"""
00_seed_resolve.py — verify each seed paper's Semantic Scholar paperId.

For seeds where semantic_scholar_id is null, look up by arXiv ID, DOI, or
title search, then verify title cosine + first-author match + year +/- 1
before trusting the result.

Pre-existing IDs are re-verified unless --trust-preexisting is passed.

Exits 2 if any seed remains unresolved or fails verification.

Inputs:  seed_papers.json
Outputs: seed_papers.json (in-place), logs/seed_resolution.json
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

from env_loader import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SEEDS_PATH = ROOT / "seed_papers.json"
META_PATH = ROOT / "papers" / "metadata.json"
LOG_PATH = ROOT / "logs" / "seed_resolution.json"
S2_BASE = "https://api.semanticscholar.org/graph/v1/paper"
FIELDS = "paperId,title,authors,year,venue,abstract,externalIds,citationCount,publicationTypes,openAccessPdf"
S2_API_KEY = os.environ.get("S2_API_KEY", "")


def session():
    s = requests.Session()
    if S2_API_KEY:
        s.headers.update({"x-api-key": S2_API_KEY})
    return s


def normalize_title(t):
    return re.sub(r"[^a-z0-9 ]", " ", (t or "").lower()).split()


def title_cosine(a, b):
    a_toks = set(normalize_title(a))
    b_toks = set(normalize_title(b))
    if not a_toks or not b_toks:
        return 0.0
    return len(a_toks & b_toks) / len(a_toks | b_toks)


def verify(seed, result):
    if not result or not result.get("title"):
        return False, "no result"
    cos = title_cosine(seed["title"], result["title"])
    if cos < 0.6:
        return False, f"title cosine {cos:.2f}"
    authors = result.get("authors") or []
    first = (authors[0].get("name") if authors else "") or ""
    if seed.get("first_author_last"):
        if seed["first_author_last"].lower() not in first.lower():
            return False, f"first-author mismatch ({first!r})"
    if seed.get("year") and result.get("year"):
        if abs(seed["year"] - result["year"]) > 1:
            return False, f"year {result['year']} vs seed {seed['year']}"
    return True, f"cos={cos:.2f}"


def fetch(s, path):
    for retry in range(3):
        try:
            r = s.get(f"{S2_BASE}{path}", params={"fields": FIELDS}, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(2 ** retry)
                continue
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(1)
    return None


def search_by_title(s, title, limit=5):
    for retry in range(3):
        try:
            r = s.get(f"{S2_BASE}/search",
                      params={"query": title, "limit": limit, "fields": FIELDS},
                      timeout=30)
            if r.status_code == 200:
                return r.json().get("data") or []
            if r.status_code == 429:
                time.sleep(2 ** retry)
                continue
        except requests.RequestException:
            pass
        time.sleep(1)
    return []


def resolve(seed, s, trust_preexisting):
    log = {
        "title": seed["title"],
        "first_author_last": seed.get("first_author_last"),
        "year": seed.get("year"),
        "resolved": False,
        "basis": None,
        "reason": None,
        "result_id": None,
    }
    if seed.get("semantic_scholar_id") and trust_preexisting:
        paper = fetch(s, f"/{seed['semantic_scholar_id']}")
        log.update(resolved=True, basis="preexisting", result_id=seed["semantic_scholar_id"])
        return seed["semantic_scholar_id"], paper, log

    if seed.get("arxiv_id"):
        r = fetch(s, f"/arXiv:{seed['arxiv_id']}")
        ok, why = verify(seed, r)
        if ok:
            log.update(resolved=True, basis="arxiv", reason=why, result_id=r["paperId"])
            return r["paperId"], r, log
        if r:
            log["reason"] = f"arxiv id {seed['arxiv_id']} failed verify: {why}"

    if seed.get("doi"):
        r = fetch(s, f"/DOI:{seed['doi']}")
        ok, why = verify(seed, r)
        if ok:
            log.update(resolved=True, basis="doi", reason=why, result_id=r["paperId"])
            return r["paperId"], r, log

    for r in search_by_title(s, seed["title"]):
        ok, why = verify(seed, r)
        if ok:
            log.update(resolved=True, basis="title_search", reason=why, result_id=r["paperId"])
            return r["paperId"], r, log
        time.sleep(0.2)

    log["reason"] = log.get("reason") or "no matching paper found"
    return None, None, log


def add_seeds_to_metadata(seed_metadata):
    META_PATH.parent.mkdir(exist_ok=True)
    existing = {}
    if META_PATH.exists():
        for p in json.loads(META_PATH.read_text(encoding="utf-8")):
            if p.get("paperId"):
                existing[p["paperId"]] = p

    for seed, paper in seed_metadata:
        if not paper:
            continue
        pid = paper["paperId"]
        merged = existing.get(pid, paper)
        merged.update({
            "discovery_source": "seed",
            "seed_subtopics": seed.get("subtopics", []),
            "seed_reason": seed.get("why"),
        })
        existing[pid] = merged

    META_PATH.write_text(json.dumps(list(existing.values()), indent=2))
    return len(seed_metadata), len(existing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trust-preexisting", action="store_true",
                    help="Skip re-verification of seeds that already have semantic_scholar_id.")
    args = ap.parse_args()

    if not SEEDS_PATH.exists():
        print(f"ERROR: {SEEDS_PATH} not found", file=sys.stderr)
        sys.exit(2)
    seeds = json.loads(SEEDS_PATH.read_text(encoding="utf-8"))
    s = session()
    logs = []
    seed_metadata = []
    failures = 0

    for seed in seeds:
        pid, paper, log = resolve(seed, s, args.trust_preexisting)
        logs.append(log)
        if pid:
            seed["semantic_scholar_id"] = pid
            seed_metadata.append((seed, paper))
            print(f"[OK]   {seed['first_author_last']} {seed['year']} -> {pid} ({log['basis']})")
        else:
            failures += 1
            print(f"[FAIL] {seed['first_author_last']} {seed['year']}: {log['reason']}", file=sys.stderr)
        time.sleep(0.3 if S2_API_KEY else 1.0)

    LOG_PATH.parent.mkdir(exist_ok=True)
    LOG_PATH.write_text(json.dumps(logs, indent=2))
    SEEDS_PATH.write_text(json.dumps(seeds, indent=2))
    _, total_metadata = add_seeds_to_metadata(seed_metadata)

    if failures:
        print(f"\n{failures} seed(s) unresolved. Edit seed_papers.json and re-run.", file=sys.stderr)
        sys.exit(2)
    print(f"\nAll {len(seeds)} seeds resolved. Metadata now contains {total_metadata} papers.")


if __name__ == "__main__":
    main()
