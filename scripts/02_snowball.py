"""
02_snowball.py — one round of backward + forward citation chaining from seeds.

For each resolved seed, fetch its references (backward) and citations (forward)
from Semantic Scholar. Filter by year, citation count (with a recent-papers
bypass), then dedupe against existing metadata.

Refuses to run if any seed has semantic_scholar_id: null.

Inputs:  seed_papers.json (resolved), papers/metadata.json
Outputs: papers/metadata.json (augmented), logs/snowball_log.json
"""
import datetime
import json
import os
import sys
import time
from pathlib import Path

import requests

from env_loader import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SEEDS_PATH = ROOT / "seed_papers.json"
META_PATH = ROOT / "papers" / "metadata.json"
LOG_PATH = ROOT / "logs" / "snowball_log.json"
S2_BASE = "https://api.semanticscholar.org/graph/v1/paper"
S2_API_KEY = os.environ.get("S2_API_KEY", "")

YEAR_MIN = 2010
SNOWBALL_CAP = 25         # max NEW additions across all seeds
PER_SEED_REFS = 6
PER_SEED_CITES = 6
MIN_CITATIONS_OLD = 20
RECENT_YEARS = 2          # within this many years, bypass min_citations

PAPER_FIELDS = ["paperId", "title", "authors", "year", "venue", "abstract",
                "externalIds", "citationCount", "publicationTypes", "openAccessPdf"]


def session():
    s = requests.Session()
    if S2_API_KEY:
        s.headers.update({"x-api-key": S2_API_KEY})
    return s


def fetch_related(s, paper_id, direction, limit=100):
    key = "citedPaper" if direction == "references" else "citingPaper"
    fields = ",".join(f"{key}.{f}" for f in PAPER_FIELDS)
    url = f"{S2_BASE}/{paper_id}/{direction}"
    params = {"fields": fields, "limit": limit}
    for retry in range(3):
        try:
            r = s.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r.json().get("data") or [], key
            if r.status_code == 429:
                time.sleep(2 ** retry)
                continue
            if r.status_code == 404:
                return [], key
        except requests.RequestException:
            pass
        time.sleep(1)
    return [], key


def filter_and_rank(entries, key, current_year):
    out = []
    for entry in entries:
        p = entry.get(key) if isinstance(entry, dict) else None
        if not p or not p.get("paperId") or not p.get("title"):
            continue
        year = p.get("year") or 0
        if year < YEAR_MIN:
            continue
        cc = p.get("citationCount") or 0
        if (current_year - year) > RECENT_YEARS and cc < MIN_CITATIONS_OLD:
            continue
        out.append((cc, p))
    out.sort(reverse=True, key=lambda x: x[0])
    return [p for _, p in out]


def main():
    current_year = datetime.datetime.now().year
    if not SEEDS_PATH.exists():
        print(f"ERROR: {SEEDS_PATH} not found", file=sys.stderr)
        sys.exit(2)
    seeds = json.loads(SEEDS_PATH.read_text(encoding="utf-8"))
    unresolved = [s for s in seeds if not s.get("semantic_scholar_id")]
    if unresolved:
        print(f"ERROR: {len(unresolved)} seed(s) unresolved. Run 00_seed_resolve.py first.", file=sys.stderr)
        sys.exit(2)

    META_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.parent.mkdir(exist_ok=True)
    existing = {}
    if META_PATH.exists():
        for p in json.loads(META_PATH.read_text(encoding="utf-8")):
            existing[p["paperId"]] = p

    s = session()
    log = []
    added = 0

    for seed in seeds:
        if added >= SNOWBALL_CAP:
            break
        pid = seed["semantic_scholar_id"]
        refs, refs_key = fetch_related(s, pid, "references")
        time.sleep(0.4 if S2_API_KEY else 1.0)
        cites, cites_key = fetch_related(s, pid, "citations")
        time.sleep(0.4 if S2_API_KEY else 1.0)

        ranked_refs = filter_and_rank(refs, refs_key, current_year)[:PER_SEED_REFS]
        ranked_cites = filter_and_rank(cites, cites_key, current_year)[:PER_SEED_CITES]

        seed_added = 0
        for p in ranked_refs + ranked_cites:
            if added >= SNOWBALL_CAP:
                break
            ppid = p["paperId"]
            if ppid not in existing:
                p["discovery_source"] = "snowball"
                p["discovery_seed"] = pid
                existing[ppid] = p
                added += 1
                seed_added += 1

        log.append({
            "seed": f"{seed['first_author_last']} {seed['year']}",
            "seed_id": pid,
            "refs_returned": len(refs),
            "cites_returned": len(cites),
            "added": seed_added,
        })
        print(f"[+{seed_added:>2}] {seed['first_author_last']} {seed['year']} "
              f"({len(refs)} refs, {len(cites)} cites)")

    META_PATH.write_text(json.dumps(list(existing.values()), indent=2))
    LOG_PATH.write_text(json.dumps(log, indent=2))
    print(f"\nSnowball added {added} papers. Total metadata: {len(existing)}")


if __name__ == "__main__":
    main()
