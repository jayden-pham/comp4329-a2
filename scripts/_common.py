"""Shared utilities for the experiment pipeline.

Imported by train.py / eval_ood.py / sharpness.py / cka.py.
"""
import random

import numpy as np
import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as T
from torchvision import models


CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD = (0.2470, 0.2435, 0.2616)
CIFAR100_MEAN = (0.5071, 0.4865, 0.4409)
CIFAR100_STD = (0.2673, 0.2564, 0.2762)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device(verbose=True):
    """Resolve the best available device. Verbose prints diagnostics so the
    user knows WHY CPU was chosen if CUDA was expected."""
    if torch.cuda.is_available():
        if verbose:
            print(f"[device] CUDA available: {torch.cuda.get_device_name(0)} "
                  f"(torch {torch.__version__}, cuda {torch.version.cuda})")
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        if verbose:
            print(f"[device] MPS available (torch {torch.__version__})")
        return torch.device("mps")
    if verbose:
        cuda_built = getattr(torch.version, "cuda", None)
        print(f"[device] CPU fallback. torch={torch.__version__} "
              f"cuda_built={cuda_built} cuda_available={torch.cuda.is_available()}")
        if cuda_built is None:
            print("[device] This torch wheel has no CUDA support. To install GPU torch on Windows:")
            print("[device]   pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu121")
    return torch.device("cpu")


def build_resnet18_cifar(num_classes):
    """ResNet-18 modified for CIFAR (3x3 first conv, no maxpool).

    Constructed without the `weights=` / `pretrained=` argument so the call
    works on both new (>=0.13) and old (<0.13) torchvision APIs; default in
    both is random initialization.
    """
    model = models.resnet18(num_classes=num_classes)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.maxpool = nn.Identity()
    return model


def get_cifar_norm(dataset):
    if dataset == "cifar10":
        return CIFAR10_MEAN, CIFAR10_STD
    if dataset == "cifar100":
        return CIFAR100_MEAN, CIFAR100_STD
    raise ValueError(f"unknown dataset: {dataset}")


def get_train_transform(dataset, augmentation="standard"):
    mean, std = get_cifar_norm(dataset)
    if augmentation == "standard":
        return T.Compose([
            T.RandomCrop(32, padding=4),
            T.RandomHorizontalFlip(),
            T.ToTensor(),
            T.Normalize(mean, std),
        ])
    if augmentation == "weak":
        return T.Compose([
            T.RandomHorizontalFlip(),
            T.ToTensor(),
            T.Normalize(mean, std),
        ])
    if augmentation == "strong":
        return T.Compose([
            T.RandomCrop(32, padding=4),
            T.RandomHorizontalFlip(),
            T.RandAugment(),
            T.ToTensor(),
            T.Normalize(mean, std),
        ])
    raise ValueError(f"unknown augmentation: {augmentation}")


def get_test_transform(dataset):
    mean, std = get_cifar_norm(dataset)
    return T.Compose([T.ToTensor(), T.Normalize(mean, std)])


def get_dataset(name, train, transform, data_root="data"):
    if name == "cifar10":
        return torchvision.datasets.CIFAR10(root=data_root, train=train, download=True, transform=transform)
    if name == "cifar100":
        return torchvision.datasets.CIFAR100(root=data_root, train=train, download=True, transform=transform)
    raise ValueError(f"unknown dataset: {name}")


def compute_ece(probs, labels, n_bins=15):
    """Expected Calibration Error with 15 equal-width confidence bins
    (Guo et al. 2017 convention). probs and labels can be tensors on any device.
    """
    if not isinstance(probs, torch.Tensor):
        probs = torch.as_tensor(probs)
    if not isinstance(labels, torch.Tensor):
        labels = torch.as_tensor(labels)
    confidences, predictions = probs.max(dim=1)
    accuracies = predictions.eq(labels)
    ece = torch.zeros(1, device=probs.device)
    edges = torch.linspace(0, 1, n_bins + 1, device=probs.device)
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        in_bin = (confidences > lo) & (confidences <= hi)
        prop = in_bin.float().mean()
        if prop.item() > 0:
            acc = accuracies[in_bin].float().mean()
            conf = confidences[in_bin].mean()
            ece += (conf - acc).abs() * prop
    return ece.item()
