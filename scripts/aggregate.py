"""Aggregate results/runs.jsonl into LaTeX tables and figures.

Outputs:
  results/tables/main_grid.tex         (optimizer x dataset summary)
  results/tables/per_corruption.tex    (per-corruption OOD accuracy)
  results/figures/scatter_sharpness_vs_ood.pdf
  results/figures/scatter_cka_vs_ood.pdf
  results/figures/per_corruption_bars.pdf

CLI:
  python scripts/aggregate.py
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RUNS_PATH = ROOT / "results" / "runs.jsonl"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"


def load_runs(path=RUNS_PATH):
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def group_by(runs, key_fn):
    out = defaultdict(list)
    for r in runs:
        out[key_fn(r)].append(r)
    return out


def mean_std(values):
    arr = np.array([v for v in values if v is not None], dtype=float)
    if arr.size == 0:
        return None, None
    return float(arr.mean()), float(arr.std(ddof=1)) if arr.size > 1 else 0.0


def fmt_pm(mean, std, mult=100, prec=2):
    if mean is None:
        return "---"
    if std is None or std == 0:
        return f"${mean * mult:.{prec}f}$"
    return f"${mean * mult:.{prec}f} \\pm {std * mult:.{prec}f}$"


# ----------------------------- tables -------------------------------------

def make_main_grid_table(runs):
    by_cell = group_by(runs, lambda r: (r["config"]["optimizer"], r["config"]["dataset"]))
    lines = [r"\begin{tabular}{ll|cccc}", r"\toprule",
             r"Optimizer & Dataset & ID acc (\%) & OOD acc (\%) & $\lambda_{\max}$ & paired-CKA \\",
             r"\midrule"]
    for (opt, ds), rs in sorted(by_cell.items()):
        id_m, id_s = mean_std([r["metrics"].get("id_accuracy") for r in rs])
        ood_m, ood_s = mean_std([r["metrics"].get("ood_accuracy_avg") for r in rs])
        eig_m, eig_s = mean_std([r["metrics"].get("sharpness_top_eig") for r in rs])
        cka_m, cka_s = mean_std([r["metrics"].get("paired_cka_penultimate") for r in rs])
        lines.append(
            f"{opt.upper()} & {ds.replace('cifar', 'CIFAR-')} & "
            f"{fmt_pm(id_m, id_s)} & {fmt_pm(ood_m, ood_s)} & "
            f"{fmt_pm(eig_m, eig_s, mult=1, prec=2)} & "
            f"{fmt_pm(cka_m, cka_s, mult=1, prec=3)} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


def make_per_corruption_table(runs):
    by_cell = group_by(runs, lambda r: (r["config"]["optimizer"], r["config"]["dataset"]))
    ctypes = set()
    for r in runs:
        ctypes.update((r["metrics"].get("ood_accuracy_per_corruption") or {}).keys())
    ctypes = sorted(ctypes)
    if not ctypes:
        return "% no per-corruption data\n"
    lines = [r"\begin{tabular}{ll|" + "c" * len(ctypes) + "}",
             r"\toprule",
             r"Optimizer & Dataset & " + " & ".join(c.replace("_", r"\_") for c in ctypes) + r" \\",
             r"\midrule"]
    for (opt, ds), rs in sorted(by_cell.items()):
        cells = []
        for ct in ctypes:
            vals = []
            for r in rs:
                pc = (r["metrics"].get("ood_accuracy_per_corruption") or {}).get(ct)
                if pc:
                    vals.append(float(np.mean(pc)))
            m, s = mean_std(vals)
            cells.append(fmt_pm(m, s))
        lines.append(f"{opt.upper()} & {ds.replace('cifar', 'CIFAR-')} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines)


# ----------------------------- figures ------------------------------------

def _scatter(runs, x_field, y_field, x_label, y_label, out_path):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5, 4))
    by_opt = group_by(runs, lambda r: r["config"]["optimizer"])
    markers = {"sgd": "o", "sam": "s", "swa": "^"}
    for opt, rs in by_opt.items():
        pts = [(r["metrics"].get(x_field), r["metrics"].get(y_field)) for r in rs]
        pts = [(a, b) for a, b in pts if a is not None and b is not None]
        if not pts:
            continue
        xs, ys = zip(*pts)
        ax.scatter(xs, ys, marker=markers.get(opt, "x"), label=opt.upper(), s=60, alpha=0.75)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def _per_corruption_bars(runs, out_path):
    import matplotlib.pyplot as plt
    by_opt = group_by(runs, lambda r: r["config"]["optimizer"])
    ctypes = set()
    for r in runs:
        ctypes.update((r["metrics"].get("ood_accuracy_per_corruption") or {}).keys())
    ctypes = sorted(ctypes)
    if not ctypes:
        return
    width = 0.8 / max(1, len(by_opt))
    x = np.arange(len(ctypes))
    fig, ax = plt.subplots(figsize=(12, 4))
    for i, (opt, rs) in enumerate(sorted(by_opt.items())):
        means = []
        for ct in ctypes:
            vals = []
            for r in rs:
                pc = (r["metrics"].get("ood_accuracy_per_corruption") or {}).get(ct)
                if pc:
                    vals.append(float(np.mean(pc)))
            means.append(float(np.mean(vals)) if vals else 0.0)
        ax.bar(x + i * width, [v * 100 for v in means], width, label=opt.upper())
    ax.set_xticks(x + width * (len(by_opt) - 1) / 2)
    ax.set_xticklabels([c.replace("_", "\n") for c in ctypes], rotation=0, fontsize=8)
    ax.set_ylabel("Accuracy (%)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(RUNS_PATH))
    args = ap.parse_args()
    runs = load_runs(args.runs)
    if not runs:
        print(f"No runs in {args.runs}.")
        return

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    (TABLES_DIR / "main_grid.tex").write_text(make_main_grid_table(runs) + "\n")
    (TABLES_DIR / "per_corruption.tex").write_text(make_per_corruption_table(runs) + "\n")

    _scatter(runs, "sharpness_top_eig", "ood_accuracy_avg",
             r"Top Hessian eigenvalue ($\lambda_{\max}$)", "OOD accuracy (CIFAR-C)",
             FIGURES_DIR / "scatter_sharpness_vs_ood.pdf")
    _scatter(runs, "paired_cka_penultimate", "ood_accuracy_avg",
             "Paired-image CKA (penultimate)", "OOD accuracy (CIFAR-C)",
             FIGURES_DIR / "scatter_cka_vs_ood.pdf")
    _per_corruption_bars(runs, FIGURES_DIR / "per_corruption_bars.pdf")

    print(f"Aggregated {len(runs)} runs.")
    print(f"  tables -> {TABLES_DIR}")
    print(f"  figures -> {FIGURES_DIR}")


if __name__ == "__main__":
    main()
