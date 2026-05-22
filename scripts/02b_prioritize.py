"""
02b_prioritize.py — rank and cap papers in metadata.json.

After snowball, metadata.json may contain far more papers than we can read
within the project's deadline. This script ranks non-seed papers and keeps
the top (max - n_seeds) so the total reading list is bounded.

Always-included:
  - Every seed paper (discovery_source == "seed", or paperId matching a seed
    in seed_papers.json)

Ranking score for non-seed papers (descending):
  1. Topical keyword hits in title + abstract head (multi-word phrases only)
  2. log(1 + citationCount), rescaled to [0, 1]
  3. Recency (linear decay over 10 years)
  4. Discovery source: snowball > search
  5. Has openAccessPdf or arXiv ID (retrievable)
  6. Has abstract (we know what it's about)

De-selected papers are NOT discarded — they are archived in
logs/prioritization_report.json for audit. Only the active metadata.json
is trimmed.

Inputs:  papers/metadata.json, seed_papers.json
Outputs: papers/metadata.json (overwritten with top N),
         logs/prioritization_report.json
Usage:   python scripts/02b_prioritize.py [--max-papers 60]
"""
import argparse
import datetime
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_PATH = ROOT / "papers" / "metadata.json"
SEEDS_PATH = ROOT / "seed_papers.json"
REPORT_PATH = ROOT / "logs" / "prioritization_report.json"

TOPIC_KEYWORDS = [
    # SAM family
    "sharpness-aware", "sharpness aware", "SAM", "ASAM", "GSAM", "ESAM", "FSAM",
    # Flatness / sharpness theory
    "flat minima", "sharp minima", "flatness", "sharpness",
    "Hessian eigenvalue", "loss landscape", "loss surface",
    # OOD / corruptions
    "out-of-distribution", "out of distribution",
    "distribution shift", "domain generalization", "domain generalisation",
    "common corruption", "corruption robustness",
    "CIFAR-C", "CIFAR-10-C", "CIFAR-100-C", "ImageNet-C",
    "robustness", "covariate shift", "dataset shift",
    # Calibration
    "calibration", "expected calibration", "ECE",
    # Representation analysis
    "centered kernel alignment", "CKA",
    "representation similarity", "feature stability",
    # Weight averaging
    "stochastic weight averaging", "SWA", "SWAD",
    "weight averaging",
]

# Compile word-boundary patterns once
KEYWORD_PATTERNS = [
    re.compile(r"\b" + re.escape(k.lower()) + r"\b") for k in TOPIC_KEYWORDS
]


def count_keywords(title, abstract):
    text = ((title or "") + " " + (abstract or "")[:500]).lower()
    return sum(1 for pat in KEYWORD_PATTERNS if pat.search(text))


def is_seed(paper, seed_ids):
    return paper.get("paperId") in seed_ids or paper.get("discovery_source") == "seed"


def score(p, max_citations, current_year):
    kw = count_keywords(p.get("title"), p.get("abstract"))
    cc = p.get("citationCount") or 0
    cc_score = math.log(1 + cc) / max(1.0, math.log(1 + max_citations))
    year = p.get("year") or 2000
    age = max(0, current_year - year)
    recency_score = max(0.0, 1.0 - age / 10.0)

    snowball_bonus = 0.30 if p.get("discovery_source") == "snowball" else 0.0
    ext = p.get("externalIds") or {}
    oap = p.get("openAccessPdf") or {}
    pdf_bonus = 0.10 if (oap.get("url") or ext.get("ArXiv")) else 0.0
    abstract_bonus = 0.05 if p.get("abstract") else 0.0

    composite = (
        2.0 * kw
        + 1.5 * cc_score
        + 0.8 * recency_score
        + snowball_bonus
        + pdf_bonus
        + abstract_bonus
    )
    return composite, {
        "kw_hits": kw,
        "citation_count": cc,
        "year": year,
        "discovery_source": p.get("discovery_source"),
        "has_pdf_hint": pdf_bonus > 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-papers", type=int, default=60,
                    help="Total cap on metadata.json after prioritisation (default 60)")
    args = ap.parse_args()

    if not META_PATH.exists():
        print(f"ERROR: {META_PATH} not found", file=sys.stderr)
        sys.exit(2)
    metadata = json.loads(META_PATH.read_text(encoding="utf-8"))
    seeds = json.loads(SEEDS_PATH.read_text(encoding="utf-8")) if SEEDS_PATH.exists() else []
    seed_ids = {s.get("semantic_scholar_id") for s in seeds if s.get("semantic_scholar_id")}

    current_year = datetime.datetime.now().year
    max_citations = max((p.get("citationCount") or 0) for p in metadata) if metadata else 1

    seed_papers, other_papers = [], []
    for p in metadata:
        if is_seed(p, seed_ids):
            seed_papers.append(p)
        else:
            other_papers.append(p)

    # Score and sort non-seed papers
    scored = []
    for p in other_papers:
        s, comp = score(p, max_citations, current_year)
        scored.append((s, p, comp))
    scored.sort(reverse=True, key=lambda x: x[0])

    n_non_seed_slots = max(0, args.max_papers - len(seed_papers))
    selected_non_seeds = scored[:n_non_seed_slots]
    deselected = scored[n_non_seed_slots:]

    selected_papers = seed_papers + [p for _, p, _ in selected_non_seeds]

    META_PATH.write_text(json.dumps(selected_papers, indent=2))

    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(json.dumps({
        "max_papers": args.max_papers,
        "n_seeds_kept": len(seed_papers),
        "n_others_kept": len(selected_non_seeds),
        "n_deselected": len(deselected),
        "selected_others": [
            {"paperId": p["paperId"], "title": p.get("title"),
             "year": p.get("year"), "score": round(s, 3), "components": comp}
            for s, p, comp in selected_non_seeds
        ],
        "deselected": [
            {"paperId": p["paperId"], "title": p.get("title"),
             "year": p.get("year"), "score": round(s, 3), "components": comp}
            for s, p, comp in deselected
        ],
    }, indent=2))

    print(f"Kept {len(selected_papers)} papers ({len(seed_papers)} seeds + "
          f"{len(selected_non_seeds)} others). Deselected {len(deselected)}.")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
