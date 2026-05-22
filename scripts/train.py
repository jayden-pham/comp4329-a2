"""End-to-end training + evaluation orchestrator for a single experiment run.

Reads configs/{name}.yaml, trains a ResNet-18 on CIFAR-10/CIFAR-100 with the
specified optimizer (sgd | sam | swa), then evaluates ID, OOD, sharpness, and
paired-image CKA, and appends one row to the per-runner results JSONL.

SAM is implemented inline (Foret et al. 2021 Eq. 2): two forward+backward
passes per batch, one optimizer.step() at the perturbed parameters.
SWA uses torch.optim.swa_utils. AMP via bf16 autocast (no GradScaler needed).

Checkpoints every 25 epochs to checkpoints/{run_id}_ep{N}.pt; the last two
periodic checkpoints are retained. Resume is automatic when periodic
checkpoints are present (unless --no-resume).

CLI:
  python scripts/train.py --config configs/spike.yaml
  python scripts/train.py --config configs/sgd_cifar10_s1.yaml --runner-id khanh_3070
  python scripts/train.py --config configs/sam_smoke.yaml --epochs 10
"""
import argparse
import contextlib
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (build_resnet18_cifar, get_dataset, get_device,
                     get_test_transform, get_train_transform, set_seed)
from sharpness import (hutchinson_trace, sam_neighborhood_loss,
                       top_eigenvalue_avg)
from cka import paired_cka_cifar_c
from eval_ood import (evaluate_id, evaluate_on_corrupted, load_cifar_c)


CHECKPOINT_INTERVAL = 25                # save every N epochs
CHECKPOINT_RETAIN = 2                   # keep this many periodic checkpoints per run_id
PRIMARY_METRICS = (                     # required for production rows
    "ood_accuracy_avg", "paired_cka_penultimate", "sharpness_top_eig",
)


# ----------------------------- AMP helper ---------------------------------

def _autocast_ctx(device, use_amp, amp_dtype):
    """Fresh autocast context manager (or null context if disabled).

    bfloat16 has fp32's dynamic range, so no GradScaler is needed and SAM's
    dual backward stays simple. fp16 path is kept available via config.
    """
    if not use_amp or device.type != "cuda":
        return contextlib.nullcontext()
    dtype = torch.bfloat16 if amp_dtype == "bfloat16" else torch.float16
    return torch.amp.autocast(device_type="cuda", dtype=dtype)


# ----------------------------- SAM step -----------------------------------

def sam_step(model, criterion, x, y, optimizer, rho, device, use_amp, amp_dtype):
    """Foret et al. 2021 SAM update: two-step, single optimizer.step() per batch."""
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer.zero_grad(set_to_none=True)
    with _autocast_ctx(device, use_amp, amp_dtype):
        loss = criterion(model(x), y)
    loss.backward()

    with torch.no_grad():
        gn = torch.sqrt(sum((p.grad ** 2).sum() for p in params if p.grad is not None))
        scale = rho / (gn + 1e-12)
        eps_per_p = []
        for p in params:
            if p.grad is None:
                eps_per_p.append(None)
                continue
            eps = p.grad * scale
            p.add_(eps)
            eps_per_p.append(eps)

    optimizer.zero_grad(set_to_none=True)
    with _autocast_ctx(device, use_amp, amp_dtype):
        loss2 = criterion(model(x), y)
    loss2.backward()

    with torch.no_grad():
        for p, e in zip(params, eps_per_p):
            if e is not None:
                p.sub_(e)
    optimizer.step()
    return loss.item()


def train_epoch(model, loader, criterion, optimizer, device, opt_type,
                rho=None, use_amp=False, amp_dtype="bfloat16"):
    model.train()
    total_loss = 0.0
    n = 0
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        if opt_type == "sam":
            lv = sam_step(model, criterion, x, y, optimizer, rho, device, use_amp, amp_dtype)
        else:
            optimizer.zero_grad(set_to_none=True)
            with _autocast_ctx(device, use_amp, amp_dtype):
                loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            lv = loss.item()
        total_loss += lv * x.size(0)
        n += x.size(0)
    return total_loss / n


# ------------------------- Checkpoint utilities --------------------------

def _periodic_paths(out_dir, run_id):
    """Sorted [(epoch, path)] for run_id's periodic checkpoints."""
    out = []
    prefix = f"{run_id}_ep"
    for p in out_dir.glob(f"{prefix}*.pt"):
        try:
            ep = int(p.stem[len(prefix):])
            out.append((ep, p))
        except ValueError:
            continue
    out.sort()
    return out


def find_latest_periodic(out_dir, run_id):
    paths = _periodic_paths(out_dir, run_id)
    return paths[-1] if paths else (None, None)


def save_periodic(out_dir, run_id, epoch, payload):
    path = out_dir / f"{run_id}_ep{epoch}.pt"
    torch.save(payload, path)
    paths = _periodic_paths(out_dir, run_id)
    for _, old in paths[:-CHECKPOINT_RETAIN]:
        try:
            old.unlink()
        except OSError:
            pass
    return path


def _git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


# ------------------------------- main -------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-dir", default=str(ROOT / "checkpoints"))
    ap.add_argument("--results-path", default=None,
                    help="Override results JSONL path. Default: "
                         "results/runs_{runner_id}.jsonl if --runner-id else results/runs.jsonl.")
    ap.add_argument("--cifar-c-dir", default=None)
    ap.add_argument("--runner-id", default=None,
                    help="Environment label (e.g. khanh_3070). Determines default "
                         "results path; included in the row.")
    ap.add_argument("--epochs", type=int, default=None,
                    help="Override config epochs (smoke testing).")
    ap.add_argument("--skip-eval", action="store_true",
                    help="Train only; do not run ID/OOD/sharpness/CKA.")
    ap.add_argument("--allow-cpu", action="store_true",
                    help="Permit CPU training; default errors out if no GPU.")
    ap.add_argument("--allow-missing-metrics", action="store_true",
                    help="With --runner-id, normally missing OOD/CKA exits non-zero. "
                         "This flag downgrades to a warning and still writes the row.")
    ap.add_argument("--no-resume", action="store_true",
                    help="Ignore existing periodic checkpoints; train from scratch.")
    args = ap.parse_args()

    overall_start = time.time()

    cfg = yaml.safe_load(Path(args.config).read_text())
    if args.epochs is not None:
        print(f"[override] epochs {cfg['epochs']} -> {args.epochs}")
        cfg["epochs"] = args.epochs
    set_seed(cfg["seed"])
    device = get_device()
    if device.type == "cpu" and not args.allow_cpu:
        print("\n[error] No GPU detected and --allow-cpu was not set.", file=sys.stderr)
        print("[error] Diagnose the GPU setup first (see docs/SETUP.md).", file=sys.stderr)
        sys.exit(2)
    print(f"[run] device={device} config={args.config} runner_id={args.runner_id}")

    # Resolve results path
    if args.results_path is not None:
        results_path = Path(args.results_path)
    elif args.runner_id:
        results_path = ROOT / "results" / f"runs_{args.runner_id}.jsonl"
    else:
        results_path = ROOT / "results" / "runs.jsonl"

    # Production mode: --runner-id implies require_production unless overridden.
    require_production = bool(args.runner_id) and not args.allow_missing_metrics

    run_id = cfg.get("run_id") or f"{Path(args.config).stem}_s{cfg['seed']}"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    final_ckpt_path = out_dir / f"{run_id}.pt"

    num_classes = 100 if cfg["dataset"] == "cifar100" else 10
    model = build_resnet18_cifar(num_classes).to(device)

    # Data
    train_t = get_train_transform(cfg["dataset"], cfg.get("augmentation", "standard"))
    test_t = get_test_transform(cfg["dataset"])
    train_ds = get_dataset(cfg["dataset"], train=True, transform=train_t)
    test_ds = get_dataset(cfg["dataset"], train=False, transform=test_t)
    pin = device.type == "cuda"
    num_workers = cfg.get("num_workers", 4)
    persistent = num_workers > 0
    train_loader = torch.utils.data.DataLoader(
        train_ds, batch_size=cfg["batch_size"], shuffle=True,
        num_workers=num_workers, pin_memory=pin, drop_last=False,
        persistent_workers=persistent,
    )
    test_loader = torch.utils.data.DataLoader(
        test_ds, batch_size=256, shuffle=False,
        num_workers=max(2, num_workers // 2), pin_memory=pin,
        persistent_workers=persistent,
    )

    # Optimizer + LR schedule
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(
        model.parameters(), lr=cfg["lr"],
        momentum=cfg.get("momentum", 0.9),
        weight_decay=cfg.get("weight_decay", 5e-4),
    )
    use_cosine = cfg.get("lr_schedule", "cosine") == "cosine"
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg["epochs"]) if use_cosine else None

    # SWA setup
    opt_type = cfg["optimizer"]
    swa_model, swa_scheduler = None, None
    swa_start = cfg.get("swa_start_epoch")
    swa_lr = None
    if opt_type == "swa":
        from torch.optim.swa_utils import AveragedModel, SWALR
        swa_model = AveragedModel(model)
        if swa_start is None:
            swa_start = int(cfg["epochs"] * 0.75)
        swa_lr = cfg.get("swa_lr", cfg["lr"] * 0.5)
        swa_scheduler = SWALR(optimizer, swa_lr=swa_lr)

    rho = cfg.get("rho", 0.05) if opt_type == "sam" else None
    use_amp = cfg.get("use_amp", True) and device.type == "cuda"
    amp_dtype = cfg.get("amp_dtype", "bfloat16")

    # ---- Resume from latest periodic checkpoint, if present ----
    start_epoch = 1
    resumed_train_secs = 0.0
    if not args.no_resume:
        last_ep, ckpt_path = find_latest_periodic(out_dir, run_id)
        if ckpt_path is not None:
            print(f"[resume] loading {ckpt_path.name} (last completed epoch {last_ep})")
            ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
            model.load_state_dict(ckpt["model_state"])
            optimizer.load_state_dict(ckpt["optimizer_state"])
            if scheduler is not None and ckpt.get("scheduler_state") is not None:
                scheduler.load_state_dict(ckpt["scheduler_state"])
            if swa_model is not None and ckpt.get("swa_state") is not None:
                swa_model.load_state_dict(ckpt["swa_state"])
            if swa_scheduler is not None and ckpt.get("swa_scheduler_state") is not None:
                swa_scheduler.load_state_dict(ckpt["swa_scheduler_state"])
            rng = ckpt.get("rng_state") or {}
            if rng.get("cpu") is not None:
                torch.set_rng_state(rng["cpu"])
            if torch.cuda.is_available() and rng.get("cuda") is not None:
                torch.cuda.set_rng_state(rng["cuda"])
            start_epoch = last_ep + 1
            resumed_train_secs = float(ckpt.get("train_wall_clock_sec_so_far", 0.0))
            print(f"[resume] resuming at epoch {start_epoch} "
                  f"(prior training wall-clock: {resumed_train_secs:.1f}s)")

    print(f"[train] optimizer={opt_type} dataset={cfg['dataset']} "
          f"epochs={cfg['epochs']} batch={cfg['batch_size']} seed={cfg['seed']}")
    print(f"[train] num_workers={num_workers} use_amp={use_amp} amp_dtype={amp_dtype}")
    if opt_type == "sam":
        print(f"[train] rho={rho}")
    if opt_type == "swa":
        print(f"[train] swa_start={swa_start} swa_lr={swa_lr}")

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()

    loop_start = time.time()
    if start_epoch <= cfg["epochs"]:
        for epoch in range(start_epoch, cfg["epochs"] + 1):
            epoch_start = time.time()
            train_loss = train_epoch(model, train_loader, criterion, optimizer, device,
                                     opt_type, rho, use_amp=use_amp, amp_dtype=amp_dtype)
            if opt_type == "swa" and epoch >= swa_start:
                swa_model.update_parameters(model)
                swa_scheduler.step()
            elif scheduler is not None:
                scheduler.step()
            if epoch == start_epoch or epoch % 10 == 0 or epoch == cfg["epochs"]:
                print(f"  epoch {epoch:3d}/{cfg['epochs']}: "
                      f"train_loss={train_loss:.4f} ({time.time() - epoch_start:.1f}s)")

            # Periodic checkpoint
            if epoch % CHECKPOINT_INTERVAL == 0 and epoch < cfg["epochs"]:
                elapsed_train = resumed_train_secs + (time.time() - loop_start)
                payload = {
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "swa_state": swa_model.state_dict() if swa_model is not None else None,
                    "optimizer_state": optimizer.state_dict(),
                    "scheduler_state": scheduler.state_dict() if scheduler is not None else None,
                    "swa_scheduler_state": swa_scheduler.state_dict() if swa_scheduler is not None else None,
                    "config": cfg,
                    "train_wall_clock_sec_so_far": elapsed_train,
                    "rng_state": {
                        "cpu": torch.get_rng_state(),
                        "cuda": torch.cuda.get_rng_state() if torch.cuda.is_available() else None,
                    },
                }
                save_periodic(out_dir, run_id, epoch, payload)
                print(f"  [ckpt] saved {run_id}_ep{epoch}.pt")
    else:
        print(f"[train] start_epoch={start_epoch} > target epochs={cfg['epochs']}; nothing to train.")

    train_wall = resumed_train_secs + (time.time() - loop_start)

    # Finalize SWA: fix BN statistics
    if opt_type == "swa":
        from torch.optim.swa_utils import update_bn
        print("[train] updating BN statistics for SWA model...")
        update_bn(train_loader, swa_model, device=device)

    max_mem_mb = (torch.cuda.max_memory_allocated() / 1024 ** 2) if device.type == "cuda" else None

    # Eval target: AveragedModel.module if SWA, else model
    eval_target = swa_model.module if opt_type == "swa" else model
    torch.save({"state_dict": eval_target.state_dict(), "config": cfg,
                "train_wall_clock_sec": train_wall}, final_ckpt_path)
    print(f"[ckpt] saved final {final_ckpt_path.name} (train wall-clock {train_wall:.1f}s)")

    metrics = {}
    ood_loaded = False
    if not args.skip_eval:
        # ID
        print("[eval] ID...")
        id_acc, id_ece, id_loss = evaluate_id(eval_target, test_loader, device)
        print(f"  ID  acc={id_acc:.4f} ECE={id_ece:.4f} loss={id_loss:.4f}")

        cifar_c_dir = args.cifar_c_dir or str(
            ROOT / f"data/CIFAR-{'10' if cfg['dataset'] == 'cifar10' else '100'}-C"
        )

        # OOD
        ood_acc_per = ood_ece_per = ood_loss_per = {}
        ood_acc_avg = ood_ece_avg = ood_loss_avg = None
        try:
            print(f"[eval] OOD from {cifar_c_dir}...")
            corr = load_cifar_c(cifar_c_dir, cfg["dataset"])
            ood_acc_per, ood_ece_per, ood_loss_per = {}, {}, {}
            for ct, (data, labels) in corr.items():
                sevs = evaluate_on_corrupted(eval_target, data, labels, cfg["dataset"], device, 256)
                ood_acc_per[ct] = [s[0] for s in sevs]
                ood_ece_per[ct] = [s[1] for s in sevs]
                ood_loss_per[ct] = [s[2] for s in sevs]
            import numpy as np
            ood_acc_avg = float(np.mean([np.mean(v) for v in ood_acc_per.values()]))
            ood_ece_avg = float(np.mean([np.mean(v) for v in ood_ece_per.values()]))
            ood_loss_avg = float(np.mean([np.mean(v) for v in ood_loss_per.values()]))
            ood_loaded = True
            print(f"  OOD acc={ood_acc_avg:.4f} ECE={ood_ece_avg:.4f} loss={ood_loss_avg:.4f}")
        except FileNotFoundError as e:
            print(f"[eval] CIFAR-C unavailable: {e}", file=sys.stderr)

        # Sharpness
        print("[eval] sharpness...")
        sharp_loader = torch.utils.data.DataLoader(
            train_ds, batch_size=cfg.get("sharpness_batch_size", 512),
            shuffle=True, num_workers=2,
        )
        eig_m, eig_s = top_eigenvalue_avg(eval_target, criterion, sharp_loader,
                                          n_batches=3, n_iter=10, device=device)
        trace_est = hutchinson_trace(eval_target, criterion, sharp_loader,
                                     n_samples=20, n_batches=2, device=device)
        nbhd = sam_neighborhood_loss(eval_target, criterion, sharp_loader,
                                     rho=0.05, n_batches=3, device=device)
        print(f"  lambda_max={eig_m:.2f}+/-{eig_s:.2f}  trace={trace_est:.2f}  nbhd_loss={nbhd:.4f}")

        # CKA (only if CIFAR-C was loaded)
        cka_res = {"paired_cka_penultimate": None, "paired_cka_per_corruption": {},
                   "paired_cka_per_layer": {}}
        if ood_loaded:
            print("[eval] paired-image CKA...")
            try:
                cka_res = paired_cka_cifar_c(eval_target, cfg["dataset"], cifar_c_dir,
                                              device, n_samples=512)
                print(f"  paired CKA (penultimate, overall) = {cka_res['paired_cka_penultimate']:.4f}")
            except Exception as e:
                print(f"[eval] CKA failed: {e}", file=sys.stderr)

        metrics = {
            "id_accuracy": id_acc, "id_loss": id_loss, "id_ece": id_ece,
            "ood_accuracy_avg": ood_acc_avg, "ood_loss_avg": ood_loss_avg,
            "ood_ece_avg": ood_ece_avg,
            "ood_accuracy_per_corruption": ood_acc_per,
            "ood_ece_per_corruption": ood_ece_per,
            "sharpness_top_eig": eig_m,
            "sharpness_top_eig_std": eig_s,
            "sharpness_trace_estimate": trace_est,
            "sharpness_sam_neighborhood_loss": nbhd,
            "paired_cka_penultimate": cka_res.get("paired_cka_penultimate"),
            "paired_cka_per_corruption": cka_res.get("paired_cka_per_corruption", {}),
            "paired_cka_per_layer": cka_res.get("paired_cka_per_layer", {}),
        }

    row = {
        "run_id": run_id,
        "runner_id": args.runner_id,
        "timestamp_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": _git_commit(),
        "config": {
            "optimizer": opt_type,
            "rho": rho,
            "swa_start_epoch": swa_start if opt_type == "swa" else None,
            "swa_lr": swa_lr if opt_type == "swa" else None,
            "dataset": cfg["dataset"],
            "model": cfg["model"],
            "epochs": cfg["epochs"],
            "batch_size": cfg["batch_size"],
            "lr": cfg["lr"],
            "weight_decay": cfg.get("weight_decay", 5e-4),
            "momentum": cfg.get("momentum", 0.9),
            "augmentation": cfg.get("augmentation", "standard"),
            "seed": cfg["seed"],
            "use_amp": use_amp,
            "amp_dtype": amp_dtype if use_amp else None,
            "num_workers": num_workers,
        },
        "wall_clock_sec": time.time() - overall_start,
        "train_wall_clock_sec": train_wall,
        "max_gpu_memory_mb": max_mem_mb,
        "metrics": metrics,
        "artifacts": {"checkpoint_path": str(final_ckpt_path.relative_to(ROOT))},
        "notes": None,
    }

    # Production validation: fail loudly if primary metrics are missing.
    if require_production and not args.skip_eval:
        missing = [m for m in PRIMARY_METRICS if metrics.get(m) is None]
        if missing:
            print(f"\n[error] Production run {run_id} missing primary metric(s): {missing}",
                  file=sys.stderr)
            print(f"[error] OOD loaded: {ood_loaded}", file=sys.stderr)
            print(f"[error] Pass --allow-missing-metrics to write a partial row anyway.",
                  file=sys.stderr)
            sys.exit(3)

    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "a") as f:
        f.write(json.dumps(row) + "\n")
    print(f"[done] appended {run_id} to {results_path}")


if __name__ == "__main__":
    main()
