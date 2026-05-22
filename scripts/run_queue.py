"""Run all configs assigned to a runner in priority order.

Reads configs/_index.json to determine which configs belong to the runner,
skips configs whose run_id is already present in results/runs_{runner_id}.jsonl,
and continues past individual config failures (recording them in
results/failed_{runner_id}.jsonl).

CLI:
  python scripts/run_queue.py --runner-id khanh_3070
  python scripts/run_queue.py --runner-id khanh_3070 --dry-run
  python scripts/run_queue.py --runner-id khanh_3070 --include-optional
  python scripts/run_queue.py --runner-id khanh_3070 --configs configs/sgd_cifar10_s1.yaml
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "configs" / "_index.json"
RESULTS_DIR = ROOT / "results"


def _existing_run_ids(results_path):
    if not results_path.exists():
        return set()
    ids = set()
    for line in results_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            ids.add(json.loads(line)["run_id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return ids


def _resolve_queue(runner_id, include_optional, explicit_configs):
    if explicit_configs:
        # User-provided list: keep order, treat each as path
        return [Path(p) for p in explicit_configs]
    if not INDEX_PATH.exists():
        print(f"[error] {INDEX_PATH} not found. Run scripts/gen_configs.py first.", file=sys.stderr)
        sys.exit(2)
    index = json.loads(INDEX_PATH.read_text())
    mine = [e for e in index["configs"] if e["assigned_runner"] == runner_id]
    if not include_optional:
        mine = [e for e in mine if not e.get("optional", False)]
    mine.sort(key=lambda e: e["priority_within_runner"])
    return [ROOT / e["config_path"] for e in mine]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner-id", required=True,
                    help="One of: khanh_3070, friend_3060, khanh_colab, friend_colab "
                         "(or any label you choose; must match what --runner-id was "
                         "set to when configs were generated).")
    ap.add_argument("--include-optional", action="store_true",
                    help="Run optional ablation configs assigned to this runner.")
    ap.add_argument("--configs", nargs="*", default=None,
                    help="Explicit config paths to run, overriding the index lookup.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would run without executing.")
    ap.add_argument("--cifar-c-dir", default=None,
                    help="Forwarded to train.py.")
    args = ap.parse_args()

    queue = _resolve_queue(args.runner_id, args.include_optional, args.configs)
    if not queue:
        print(f"[warn] empty queue for runner_id={args.runner_id}")
        return

    results_path = RESULTS_DIR / f"runs_{args.runner_id}.jsonl"
    failed_path = RESULTS_DIR / f"failed_{args.runner_id}.jsonl"
    completed = _existing_run_ids(results_path)

    print(f"[queue] runner_id={args.runner_id}")
    print(f"[queue] {len(queue)} config(s) queued; {len(completed)} already completed")
    print(f"[queue] results -> {results_path}")
    print(f"[queue] failures -> {failed_path}")
    print()

    to_run = []
    for cfg_path in queue:
        if not cfg_path.exists():
            print(f"  [skip] {cfg_path.name}: file not found")
            continue
        cfg = yaml.safe_load(cfg_path.read_text())
        run_id = cfg.get("run_id") or f"{cfg_path.stem}_s{cfg.get('seed')}"
        if run_id in completed:
            print(f"  [skip] {run_id}: already in {results_path.name}")
            continue
        to_run.append((cfg_path, run_id))

    if args.dry_run:
        print(f"\n[dry-run] Would execute {len(to_run)} config(s):")
        for cfg_path, run_id in to_run:
            print(f"  {run_id:35s}  ({cfg_path.name})")
        return

    if not to_run:
        print("[queue] nothing to run; all configs already completed.")
        return

    print(f"\n[queue] executing {len(to_run)} config(s)...\n")
    n_ok = n_fail = 0
    for idx, (cfg_path, run_id) in enumerate(to_run, 1):
        print(f"\n{'=' * 70}")
        print(f"[{idx}/{len(to_run)}] {run_id}")
        print(f"{'=' * 70}")
        cmd = [
            sys.executable, str(ROOT / "scripts" / "train.py"),
            "--config", str(cfg_path),
            "--runner-id", args.runner_id,
        ]
        if args.cifar_c_dir is not None:
            cmd += ["--cifar-c-dir", args.cifar_c_dir]

        t0 = datetime.datetime.utcnow()
        try:
            result = subprocess.run(cmd, cwd=ROOT)
            rc = result.returncode
        except KeyboardInterrupt:
            print("\n[queue] interrupted by user (Ctrl-C); leaving queue partially run.")
            sys.exit(130)
        except Exception as e:
            print(f"[queue] exception running {run_id}: {e}", file=sys.stderr)
            rc = -1

        if rc == 0:
            n_ok += 1
            print(f"[queue] {run_id}: OK")
        else:
            n_fail += 1
            fail_row = {
                "run_id": run_id,
                "runner_id": args.runner_id,
                "config_path": str(cfg_path.relative_to(ROOT)),
                "exit_code": rc,
                "timestamp_utc": t0.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            failed_path.parent.mkdir(parents=True, exist_ok=True)
            with open(failed_path, "a") as f:
                f.write(json.dumps(fail_row) + "\n")
            print(f"[queue] {run_id}: FAILED (exit {rc}); recorded in {failed_path.name}")

    print(f"\n[queue] complete: {n_ok} ok, {n_fail} failed")


if __name__ == "__main__":
    main()
