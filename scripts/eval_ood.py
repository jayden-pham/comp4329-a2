"""ID + CIFAR-C evaluation for a trained ResNet-18 checkpoint.

Loads Hendrycks CIFAR-10-C or CIFAR-100-C as .npy arrays from
data/CIFAR-{10,100}-C/ in the standard layout:

  data/CIFAR-10-C/
    labels.npy
    gaussian_noise.npy
    shot_noise.npy
    ...

Each corruption .npy is shape (50000, 32, 32, 3) uint8, organized as
5 severities x 10000 test images in the same order as the clean CIFAR test set.

CLI:
  python scripts/eval_ood.py --checkpoint <path> --dataset cifar10
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (build_resnet18_cifar, compute_ece, get_cifar_norm,
                     get_dataset, get_device, get_test_transform)

CORRUPTION_TYPES = [
    "gaussian_noise", "shot_noise", "impulse_noise", "defocus_blur",
    "glass_blur", "motion_blur", "zoom_blur", "snow", "frost", "fog",
    "brightness", "contrast", "elastic_transform", "pixelate", "jpeg_compression",
]


def load_cifar_c(cifar_c_dir, dataset):
    """Load CIFAR-C corruption arrays + labels. Returns {ctype: (data, labels)}."""
    p = Path(cifar_c_dir)
    labels_p = p / "labels.npy"
    if not labels_p.exists():
        raise FileNotFoundError(
            f"labels.npy not found in {p}.\n"
            f"Download {dataset.upper()}-C:\n"
            f"  CIFAR-10-C : https://zenodo.org/record/2535967/files/CIFAR-10-C.tar\n"
            f"  CIFAR-100-C: https://zenodo.org/record/3555552/files/CIFAR-100-C.tar\n"
            f"Extract so that {p}/labels.npy exists."
        )
    labels = np.load(str(labels_p))
    out = {}
    for ct in CORRUPTION_TYPES:
        f = p / f"{ct}.npy"
        if f.exists():
            out[ct] = (np.load(str(f)), labels)
    if not out:
        raise FileNotFoundError(f"No corruption .npy files found in {p}.")
    return out


def evaluate_on_corrupted(model, data, labels, dataset, device, batch_size=256):
    """Per-severity (accuracy, ECE, loss) for one corruption type."""
    mean, std = get_cifar_norm(dataset)
    mean_t = torch.tensor(mean).view(1, 3, 1, 1).to(device)
    std_t = torch.tensor(std).view(1, 3, 1, 1).to(device)
    crit = nn.CrossEntropyLoss(reduction="sum")
    out = []
    model.eval()
    for sev in range(5):
        sl = slice(sev * 10000, (sev + 1) * 10000)
        x_t = torch.from_numpy(data[sl]).permute(0, 3, 1, 2).float() / 255.0
        # Hendrycks' labels.npy is length 50000 (severity-repeated)
        y_t = torch.from_numpy(labels[sl] if len(labels) == 50000 else labels).long()
        probs_chunks, correct_chunks, loss_sum, n = [], [], 0.0, 0
        with torch.no_grad():
            for i in range(0, len(x_t), batch_size):
                x = x_t[i:i + batch_size].to(device)
                y = y_t[i:i + batch_size].to(device)
                x = (x - mean_t) / std_t
                logits = model(x)
                loss_sum += crit(logits, y).item()
                probs_chunks.append(torch.softmax(logits, dim=1).cpu())
                correct_chunks.append(logits.argmax(dim=1).eq(y).cpu())
                n += x.size(0)
        probs = torch.cat(probs_chunks)
        correct = torch.cat(correct_chunks)
        ece = compute_ece(probs, y_t)
        out.append((float(correct.float().mean()), ece, loss_sum / n))
    return out


def evaluate_id(model, loader, device):
    """Clean-test (accuracy, ECE, loss)."""
    model.eval()
    crit = nn.CrossEntropyLoss(reduction="sum")
    probs_chunks, label_chunks, correct_chunks, loss_sum, n = [], [], [], 0.0, 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(x)
            loss_sum += crit(logits, y).item()
            probs_chunks.append(torch.softmax(logits, dim=1).cpu())
            label_chunks.append(y.cpu())
            correct_chunks.append(logits.argmax(dim=1).eq(y).cpu())
            n += x.size(0)
    probs = torch.cat(probs_chunks)
    labels = torch.cat(label_chunks)
    correct = torch.cat(correct_chunks)
    return float(correct.float().mean()), compute_ece(probs, labels), loss_sum / n


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
    ap.add_argument("--batch-size", type=int, default=256)
    args = ap.parse_args()
    if args.cifar_c_dir is None:
        args.cifar_c_dir = f"data/CIFAR-{'10' if args.dataset == 'cifar10' else '100'}-C"

    device = get_device()
    num_classes = 100 if args.dataset == "cifar100" else 10
    model = _load_checkpoint(args.checkpoint, num_classes, device)

    transform = get_test_transform(args.dataset)
    ds = get_dataset(args.dataset, train=False, transform=transform)
    loader = torch.utils.data.DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=2)

    id_acc, id_ece, id_loss = evaluate_id(model, loader, device)
    corr_data = load_cifar_c(args.cifar_c_dir, args.dataset)
    acc_per, ece_per, loss_per = {}, {}, {}
    for ct, (data, labels) in corr_data.items():
        sevs = evaluate_on_corrupted(model, data, labels, args.dataset, device, args.batch_size)
        acc_per[ct] = [s[0] for s in sevs]
        ece_per[ct] = [s[1] for s in sevs]
        loss_per[ct] = [s[2] for s in sevs]

    def avg(d):
        return float(np.mean([np.mean(v) for v in d.values()])) if d else None

    print(json.dumps({
        "id_accuracy": id_acc,
        "id_ece": id_ece,
        "id_loss": id_loss,
        "ood_accuracy_avg": avg(acc_per),
        "ood_ece_avg": avg(ece_per),
        "ood_loss_avg": avg(loss_per),
        "ood_accuracy_per_corruption": acc_per,
        "ood_ece_per_corruption": ece_per,
    }, indent=2))


if __name__ == "__main__":
    main()
