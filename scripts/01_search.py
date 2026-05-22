"""
01_search.py — Semantic Scholar keyword search across topic queries.

Hard-coded list of targeted queries spanning sub-topics in RESEARCH_CONTEXT.md.
Paginates /paper/search; dedupes by paperId; caps results per query and total.

Inputs:  (search queries hard-coded below)
Outputs: papers/metadata.json, logs/search_log.json
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

from env_loader import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

META_PATH = ROOT / "papers" / "metadata.json"
LOG_PATH = ROOT / "logs" / "search_log.json"
S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_API_KEY = os.environ.get("S2_API_KEY", "")
FIELDS = "paperId,title,authors,year,venue,abstract,externalIds,citationCount,publicationTypes,openAccessPdf"

YEAR_MIN = 2010
PER_QUERY_CAP = 8       # top N per query
TOTAL_CAP = 260         # hard ceiling on metadata size

SEARCH_QUERIES = [
    # SAM-specific
    "sharpness-aware minimization",
    "sharpness aware minimization",
    "adaptive sharpness-aware minimization",
    "understanding sharpness-aware minimization",
    "m-sharpness sharpness-aware minimization",
    "normalization layers sharpness-aware minimization",
    "sharpness-aware minimization flat minima",
    "sharpness-aware minimization robustness",
    "sharpness-aware minimization corruption robustness",
    "SAM optimizer generalization",
    "efficient sharpness-aware minimization",
    "surrogate gap guided sharpness-aware minimization",
    "friendly sharpness-aware minimization",
    # Flatness theory
    "flat minima generalization",
    "sharp minima generalization",
    "loss landscape sharpness generalization",
    "Hessian eigenvalue generalization",
    "relative flatness neural network",
    "sharpness measures generalization",
    # OOD / distribution shift
    "out-of-distribution generalization image classification",
    "common corruptions robustness",
    "CIFAR-C robustness",
    "CIFAR-10-C CIFAR-100-C robustness",
    "ImageNet-C corruption robustness",
    "corruption robustness calibration",
    "dataset shift calibration deep learning",
    # SAM x OOD
    "sharpness-aware domain generalization",
    "flat minima domain generalization",
    "sharpness-aware gradient matching domain generalization",
    "SAM out-of-distribution generalization",
    "sharpness distribution shift",
    "domain generalization benchmark DomainBed",
    "SWAD domain generalization flat minima",
    # Weight averaging
    "stochastic weight averaging",
    "stochastic weight averaging wider optima",
    "stochastic weight averaging domain generalization",
    "weight averaging generalization",
    "weight averaging flat minima generalization",
    # Representation analysis
    "centered kernel alignment representation similarity",
    "CKA neural network representations",
    "representation similarity distribution shift",
    "feature stability distribution shift",
    "representation robustness common corruptions",
    # Calibration under shift
    "calibration under dataset shift",
    "expected calibration error dataset shift",
    "expected calibration error common corruptions",
]


def session():
    s = requests.Session()
    if S2_API_KEY:
        s.headers.update({"x-api-key": S2_API_KEY})
    return s


def search(s, query, cap):
    out = []
    offset = 0
    while len(out) < cap:
        params = {
            "query": query,
            "limit": min(100, cap - len(out)),
            "offset": offset,
            "year": f"{YEAR_MIN}-",
            "fields": FIELDS,
        }
        ok = False
        for retry in range(3):
            try:
                r = s.get(S2_SEARCH, params=params, timeout=30)
                if r.status_code == 200:
                    ok = True
                    break
                if r.status_code == 429:
                    time.sleep(2 ** retry)
                    continue
            except requests.RequestException:
                pass
            time.sleep(1)
        if not ok:
            break
        data = r.json()
        rows = data.get("data") or []
        if not rows:
            break
        out.extend(rows)
        if "next" not in data:
            break
        offset = data["next"]
        time.sleep(0.4 if S2_API_KEY else 1.0)
    return out[:cap]


def main():
    META_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.parent.mkdir(exist_ok=True)
    existing = {}
    if META_PATH.exists():
        for p in json.loads(META_PATH.read_text(encoding="utf-8")):
            existing[p["paperId"]] = p

    s = session()
    log = []
    new_count = 0

    for query in SEARCH_QUERIES:
        results = search(s, query, PER_QUERY_CAP)
        kept = 0
        for r in results:
            pid = r.get("paperId")
            if not pid or not r.get("title"):
                continue
            year = r.get("year") or 0
            if year < YEAR_MIN:
                continue
            if pid not in existing:
                r["discovery_source"] = "search"
                r["discovery_query"] = query
                existing[pid] = r
                kept += 1
                new_count += 1
            if len(existing) >= TOTAL_CAP:
                break
        log.append({"query": query, "returned": len(results), "new": kept})
        print(f"[+{kept:>2}/{len(results):>2}] {query}")
        if len(existing) >= TOTAL_CAP:
            print(f"  hit TOTAL_CAP {TOTAL_CAP}, stopping")
            break
        time.sleep(0.4 if S2_API_KEY else 1.0)

    META_PATH.write_text(json.dumps(list(existing.values()), indent=2))
    LOG_PATH.write_text(json.dumps(log, indent=2))
    print(f"\nMetadata: {len(existing)} papers ({new_count} new this run)")


if __name__ == "__main__":
    main()
