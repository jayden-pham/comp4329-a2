"""Linear CKA at the penultimate layer + paired-image CKA across CIFAR-C corruptions.

Paired-image CKA: for each (corruption type c, severity s), compute
CKA(phi(x_clean), phi(corrupt(x_clean, c, s))) on the same N test images,
where phi is the network's penultimate-layer feature map. Averages across
severities per corruption type, then across corruption types.

CLI:
  python scripts/cka.py --checkpoint <path> --dataset cifar10
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (build_resnet18_cifar, get_cifar_norm, get_dataset,
                     get_device, get_test_transform)

CORRUPTION_TYPES = [
    "gaussian_noise", "shot_noise", "impulse_noise", "defocus_blur",
    "glass_blur", "motion_blur", "zoom_blur", "snow", "frost", "fog",
    "brightness", "contrast", "elastic_transform", "pixelate", "jpeg_compression",
]


def linear_cka(A, B):
    """Linear CKA between two N x D matrices (Kornblith et al. 2019).

    CKA(X, Y) = ||X_c^T Y_c||_F^2 / (||X_c^T X_c||_F * ||Y_c^T Y_c||_F)
    where X_c and Y_c are example-centered.
    """
    A_c = A - A.mean(0, keepdim=True)
    B_c = B - B.mean(0, keepdim=True)
    num = (A_c.T @ B_c).pow(2).sum()
    den_a = (A_c.T @ A_c).pow(2).sum().sqrt()
    den_b = (B_c.T @ B_c).pow(2).sum().sqrt()
    return float(num / (den_a * den_b + 1e-12))


class _LayerFeatureExtractor:
    """Hook ResNet-18 to collect penultimate (pre-fc) features and per-layer
    global-avg-pooled features from layer1..layer4 outputs."""

    def __init__(self, model):
        self.model = model
        self.buffers = {}
        self._hooks = []

        def make_hook(name):
            def hook(_m, _inp, out):
                self.buffers[name] = out.detach()
            return hook

        for name in ("layer1", "layer2", "layer3", "layer4"):
            self._hooks.append(getattr(model, name).register_forward_hook(make_hook(name)))

        # fc takes the avgpooled penultimate as input
        def fc_in_hook(_m, inp, _out):
            self.buffers["penultimate"] = inp[0].detach()
        self._hooks.append(model.fc.register_forward_hook(fc_in_hook))

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        for h in self._hooks:
            h.remove()


def _pooled(tensor):
    """If 4D (B,C,H,W) reduce to (B,C) via global average pool; if 2D pass through."""
    if tensor.dim() == 4:
        return tensor.mean(dim=(2, 3))
    return tensor


def _gather_features(model, x_batches, device, batch_size=128):
    """Run model on a list of pre-normalized tensors; return dict of stacked features."""
    out = {k: [] for k in ("layer1", "layer2", "layer3", "layer4", "penultimate")}
    model.eval()
    with _LayerFeatureExtractor(model) as ext:
        with torch.no_grad():
            for x in x_batches:
                x = x.to(device)
                _ = model(x)
                for k, v in ext.buffers.items():
                    out[k].append(_pooled(v).cpu())
    return {k: torch.cat(v, dim=0) for k, v in out.items() if v}


def paired_cka_cifar_c(model, dataset, cifar_c_dir, device, n_samples=512, batch_size=128):
    """Paired-image CKA over Hendrycks CIFAR-C corruptions.

    Returns dict matching results/schema.md:
      - paired_cka_penultimate: overall mean
      - paired_cka_per_corruption: per-corruption-type mean (averaged over 5 severities)
      - paired_cka_per_layer: overall mean per layer
    """
    cifar_c_dir = Path(cifar_c_dir)
    mean, std = get_cifar_norm(dataset)
    mean_t = torch.tensor(mean).view(1, 3, 1, 1).to(device)
    std_t = torch.tensor(std).view(1, 3, 1, 1).to(device)

    # Clean test images (in CIFAR test order); take first n_samples
    from torchvision.datasets import CIFAR10, CIFAR100
    cls = CIFAR10 if dataset == "cifar10" else CIFAR100
    raw = cls(root="data", train=False, download=True)
    # raw.data is (10000, 32, 32, 3) uint8
    clean = torch.from_numpy(raw.data[:n_samples]).permute(0, 3, 1, 2).float() / 255.0
    clean = (clean.to(device) - mean_t) / std_t

    clean_batches = [clean[i:i + batch_size] for i in range(0, len(clean), batch_size)]
    clean_feats = _gather_features(model, clean_batches, device, batch_size)

    per_corruption = {}
    per_corruption_per_sev = {}
    per_layer_acc = {k: [] for k in clean_feats.keys()}

    for ctype in CORRUPTION_TYPES:
        cpath = cifar_c_dir / f"{ctype}.npy"
        if not cpath.exists():
            continue
        arr = np.load(str(cpath))  # (50000, 32, 32, 3) uint8
        sev_ckas_pen = []
        per_corruption_per_sev[ctype] = []
        for sev in range(5):
            start = sev * 10000
            sev_data = arr[start:start + n_samples]
            x = torch.from_numpy(sev_data).permute(0, 3, 1, 2).float() / 255.0
            x = (x.to(device) - mean_t) / std_t
            corrupt_batches = [x[i:i + batch_size] for i in range(0, len(x), batch_size)]
            corrupt_feats = _gather_features(model, corrupt_batches, device, batch_size)

            # Penultimate (the headline metric)
            cka_pen = linear_cka(clean_feats["penultimate"], corrupt_feats["penultimate"])
            sev_ckas_pen.append(cka_pen)
            per_corruption_per_sev[ctype].append(cka_pen)

            # Accumulate per-layer for overall per-layer mean
            for layer_name in per_layer_acc:
                per_layer_acc[layer_name].append(
                    linear_cka(clean_feats[layer_name], corrupt_feats[layer_name])
                )
        per_corruption[ctype] = sum(sev_ckas_pen) / len(sev_ckas_pen)

    per_layer = {k: (sum(v) / len(v) if v else None) for k, v in per_layer_acc.items()}
    overall_pen = sum(per_corruption.values()) / max(1, len(per_corruption))
    return {
        "paired_cka_penultimate": overall_pen,
        "paired_cka_per_corruption": per_corruption,
        "paired_cka_per_severity": per_corruption_per_sev,
        "paired_cka_per_layer": per_layer,
    }


def _load_checkpoint(path, num_classes, device):
    model = build_resnet18_cifar(num_classes).to(device)
    state = torch.load(path, map_location=device, weights_only=False)
    sd = state.get("state_dict", state) if isinstance(state, dict) else state
    if any(k.startswith("module.") for k in sd.keys()):
        sd = {k.replace("module.", "", 1): v for k, v in sd.items() if "n_averaged" not in k}
    model.load_state_dict(sd, strict=False)
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--dataset", required=True, choices=["cifar10", "cifar100"])
    ap.add_argument("--cifar-c-dir", default=None)
    ap.add_argument("--n-samples", type=int, default=512)
    args = ap.parse_args()

    if args.cifar_c_dir is None:
        args.cifar_c_dir = f"data/CIFAR-{'10' if args.dataset == 'cifar10' else '100'}-C"

    device = get_device()
    num_classes = 100 if args.dataset == "cifar100" else 10
    model = _load_checkpoint(args.checkpoint, num_classes, device)

    res = paired_cka_cifar_c(model, args.dataset, args.cifar_c_dir, device, args.n_samples)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
