"""Merge per-runner results/runs_*.jsonl into canonical results/runs.jsonl.

Deduplicates by run_id. Fails loudly if two sources have the same run_id with
different content (metrics or config). Validates that all production rows
(those with a runner_id set) have non-null primary metrics:
  - ood_accuracy_avg
  - paired_cka_penultimate
  - sharpness_top_eig

CLI:
  python scripts/merge_runs.py
  python scripts/merge_runs.py --allow-null-metrics      # downgrade to warning
  python scripts/merge_runs.py --output results/runs.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
PRIMARY_METRICS = ("ood_accuracy_avg", "paired_cka_penultimate", "sharpness_top_eig")


def _canonical_key(row):
    """Comparable representation for duplicate detection."""
    return json.dumps({"metrics": row.get("metrics"), "config": row.get("config")},
                      sort_keys=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-glob", default="runs_*.jsonl",
                    help="Glob (under results/) for per-runner files. Default: runs_*.jsonl")
    ap.add_argument("--output", default=str(RESULTS_DIR / "runs.jsonl"))
    ap.add_argument("--allow-null-metrics", action="store_true",
                    help="Downgrade missing-primary-metric to warning instead of failing.")
    args = ap.parse_args()

    out_path = Path(args.output)
    rows_by_id = {}
    sources_by_id = {}
    n_files = 0
    n_lines = 0

    for fp in sorted(RESULTS_DIR.glob(args.input_glob)):
        if fp.resolve() == out_path.resolve():
            continue  # don't read the merged output if it's in the same dir
        n_files += 1
        for line in fp.read_text().splitlines():
            if not line.strip():
                continue
            n_lines += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[error] {fp.name}: invalid JSON: {e}", file=sys.stderr)
                sys.exit(2)
            rid = row.get("run_id")
            if not rid:
                print(f"[error] {fp.name}: row missing run_id", file=sys.stderr)
                sys.exit(2)
            if rid in rows_by_id:
                if _canonical_key(rows_by_id[rid]) != _canonical_key(row):
                    print(f"[error] duplicate run_id {rid!r} with disagreeing content",
                          file=sys.stderr)
                    print(f"  first source : {sources_by_id[rid]}", file=sys.stderr)
                    print(f"  second source: {fp.name}", file=sys.stderr)
                    sys.exit(2)
            rows_by_id[rid] = row
            sources_by_id[rid] = fp.name

    if not rows_by_id:
        print(f"[error] no rows found under {RESULTS_DIR}/{args.input_glob}", file=sys.stderr)
        sys.exit(2)

    # Validate production rows (those with runner_id set; smoke/spike rows are
    # exempt because runner_id is null for them).
    issues = []
    for rid, row in rows_by_id.items():
        if not row.get("runner_id"):
            continue
        metrics = row.get("metrics") or {}
        for field in PRIMARY_METRICS:
            if metrics.get(field) is None:
                issues.append((rid, field))

    if issues:
        msg_head = "[error]" if not args.allow_null_metrics else "[warn]"
        for rid, field in issues:
            print(f"{msg_head} {rid}: missing primary metric {field}", file=sys.stderr)
        if not args.allow_null_metrics:
            print(f"\n[error] {len(issues)} production row(s) have missing primary metrics.",
                  file=sys.stderr)
            print("Pass --allow-null-metrics to write the merged file anyway.",
                  file=sys.stderr)
            sys.exit(3)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for rid in sorted(rows_by_id.keys()):
            f.write(json.dumps(rows_by_id[rid]) + "\n")
    print(f"[merge] read {n_lines} row(s) from {n_files} file(s)")
    print(f"[merge] wrote {len(rows_by_id)} unique row(s) -> {out_path}")


if __name__ == "__main__":
    main()
