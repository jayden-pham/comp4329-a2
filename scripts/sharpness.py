"""Sharpness measurements at a trained checkpoint.

Provides three measures used in the experiment plan:
  * top Hessian eigenvalue via power iteration (Rayleigh quotient)
  * Hutchinson trace estimator
  * SAM-style neighborhood loss: max_{||eps||<=rho} L(theta+eps),
    approximated by first-order ascent (Foret et al. 2021 Eq. 2)

CLI:
  python scripts/sharpness.py --checkpoint <path> --dataset cifar10
"""
import argparse
import json
import math
import sys
from pathlib import Path

import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (build_resnet18_cifar, get_dataset, get_device,
                     get_test_transform)


def _hvp(loss, params, vec):
    """Hessian-vector product Hv at the current model state."""
    grads = torch.autograd.grad(loss, params, create_graph=True)
    gv = sum((g * v).sum() for g, v in zip(grads, vec))
    Hv = torch.autograd.grad(gv, params, retain_graph=False)
    return list(Hv)


def _norm(tensors):
    return math.sqrt(sum((t.float() ** 2).sum().item() for t in tensors))


def top_eigenvalue(model, criterion, batch, n_iter=10):
    """Top Hessian eigenvalue via power iteration on a single batch.

    Returns the Rayleigh quotient v^T H v at the final iterate (||v||=1).
    """
    model.eval()
    x, y = batch
    params = [p for p in model.parameters() if p.requires_grad]

    v = [torch.randn_like(p) for p in params]
    nv = _norm(v)
    v = [vi / nv for vi in v]

    eigval = 0.0
    for _ in range(n_iter):
        loss = criterion(model(x), y)
        Hv = _hvp(loss, params, v)
        eigval = sum((vi * Hvi).sum().item() for vi, Hvi in zip(v, Hv))
        nh = _norm(Hv)
        if nh < 1e-12:
            break
        v = [Hvi / nh for Hvi in Hv]
    return eigval


def top_eigenvalue_avg(model, criterion, loader, n_batches=3, n_iter=10, device="cuda"):
    """Average top eigenvalue across n_batches held-out batches; report mean+std."""
    eigvals = []
    it = iter(loader)
    for _ in range(n_batches):
        try:
            x, y = next(it)
        except StopIteration:
            break
        x, y = x.to(device), y.to(device)
        eigvals.append(top_eigenvalue(model, criterion, (x, y), n_iter=n_iter))
        model.zero_grad(set_to_none=True)
    if not eigvals:
        return None, None
    mean = sum(eigvals) / len(eigvals)
    if len(eigvals) > 1:
        var = sum((e - mean) ** 2 for e in eigvals) / (len(eigvals) - 1)
        std = math.sqrt(var)
    else:
        std = 0.0
    return mean, std


def hutchinson_trace(model, criterion, loader, n_samples=20, n_batches=2, device="cuda"):
    """Hutchinson estimator: tr(H) ≈ E[v^T H v] for Rademacher v."""
    params = [p for p in model.parameters() if p.requires_grad]
    traces = []
    it = iter(loader)
    for _ in range(n_batches):
        try:
            x, y = next(it)
        except StopIteration:
            break
        x, y = x.to(device), y.to(device)
        loss = criterion(model(x), y)
        grads = torch.autograd.grad(loss, params, create_graph=True)
        for _ in range(n_samples):
            v = [(torch.randint_like(p, 0, 2).float() * 2 - 1) for p in params]
            gv = sum((g * vi).sum() for g, vi in zip(grads, v))
            Hv = torch.autograd.grad(gv, params, retain_graph=True)
            traces.append(sum((vi * Hvi).sum().item() for vi, Hvi in zip(v, Hv)))
        model.zero_grad(set_to_none=True)
    if not traces:
        return None
    return sum(traces) / len(traces)


def sam_neighborhood_loss(model, criterion, loader, rho=0.05, n_batches=3, device="cuda"):
    """Foret first-order approximation: L(theta + rho * grad / ||grad||).

    Averaged over n_batches held-out batches. Model parameters are restored.
    """
    model.eval()
    params = [p for p in model.parameters() if p.requires_grad]
    losses = []
    it = iter(loader)
    for _ in range(n_batches):
        try:
            x, y = next(it)
        except StopIteration:
            break
        x, y = x.to(device), y.to(device)

        loss = criterion(model(x), y)
        grads = torch.autograd.grad(loss, params)
        gn = math.sqrt(sum((g ** 2).sum().item() for g in grads))
        scale = rho / (gn + 1e-12)

        with torch.no_grad():
            for p, g in zip(params, grads):
                p.add_(g * scale)
        with torch.no_grad():
            perturbed = criterion(model(x), y).item()
        with torch.no_grad():
            for p, g in zip(params, grads):
                p.sub_(g * scale)

        losses.append(perturbed)
        model.zero_grad(set_to_none=True)
    if not losses:
        return None
    return sum(losses) / len(losses)


def _load_checkpoint(path, num_classes, device):
    model = build_resnet18_cifar(num_classes).to(device)
    state = torch.load(path, map_location=device, weights_only=False)
    sd = state.get("state_dict", state) if isinstance(state, dict) else state
    # Strip torch.optim.swa_utils.AveragedModel's "module." prefix if present
    if any(k.startswith("module.") for k in sd.keys()):
        sd = {k.replace("module.", "", 1): v for k, v in sd.items() if k.startswith("module.") or "n_averaged" not in k}
        sd = {k: v for k, v in sd.items() if "n_averaged" not in k}
    model.load_state_dict(sd, strict=False)
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--dataset", required=True, choices=["cifar10", "cifar100"])
    ap.add_argument("--batch-size", type=int, default=512)
    ap.add_argument("--n-batches", type=int, default=3)
    ap.add_argument("--n-iter", type=int, default=10)
    ap.add_argument("--rho", type=float, default=0.05)
    ap.add_argument("--skip-trace", action="store_true")
    args = ap.parse_args()

    device = get_device()
    num_classes = 100 if args.dataset == "cifar100" else 10
    model = _load_checkpoint(args.checkpoint, num_classes, device)

    transform = get_test_transform(args.dataset)
    ds = get_dataset(args.dataset, train=True, transform=transform)
    loader = torch.utils.data.DataLoader(ds, batch_size=args.batch_size, shuffle=True, num_workers=2)

    criterion = nn.CrossEntropyLoss()
    eig_m, eig_s = top_eigenvalue_avg(model, criterion, loader, args.n_batches, args.n_iter, device)
    trace = None if args.skip_trace else hutchinson_trace(model, criterion, loader, device=device)
    nbhd = sam_neighborhood_loss(model, criterion, loader, args.rho, args.n_batches, device)

    print(json.dumps({
        "sharpness_top_eig": eig_m,
        "sharpness_top_eig_std": eig_s,
        "sharpness_trace_estimate": trace,
        "sharpness_sam_neighborhood_loss": nbhd,
    }, indent=2))


if __name__ == "__main__":
    main()
