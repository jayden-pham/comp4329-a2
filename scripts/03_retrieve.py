"""
03_retrieve.py — download PDFs for each paper in metadata.json.

Source attempt order:
  1. arXiv (if externalIds.ArXiv present)
  2. S2 openAccessPdf

Validation per attempt:
  - HTTP 200
  - Starts with %PDF- magic bytes
  - >= 10 KB
  - Content-Type not html/json/xml

Identity check: parse first 2 pages with PyMuPDF; require title fuzzy-match
and first-author last-name appearance in the first 3000 chars.

Inputs:  papers/metadata.json
Outputs: papers/pdfs/{paperId}.pdf
         logs/retrieval_failures.json
         logs/retrieval_sources.json
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
META_PATH = ROOT / "papers" / "metadata.json"
PDF_DIR = ROOT / "papers" / "pdfs"
FAIL_LOG = ROOT / "logs" / "retrieval_failures.json"
SRC_LOG = ROOT / "logs" / "retrieval_sources.json"

MIN_PDF_SIZE = 10_000
TIMEOUT = 60
HEADERS = {"User-Agent": "Mozilla/5.0 (literature-pipeline)"}


def normalize(t):
    return re.sub(r"[^a-z0-9 ]", " ", (t or "").lower()).split()


def title_match(expected, actual):
    """Recall: fraction of expected-title tokens that appear in actual text.

    Jaccard is wrong here because the actual text (first 3000 chars of the
    PDF) has hundreds of unique tokens while the title has ~7, so even a
    perfect title hit scores ~0.02 via |A intersect B| / |A union B|.
    """
    expected_tokens = set(normalize(expected))
    actual_tokens = set(normalize(actual))
    if not expected_tokens:
        return 0.0
    return len(expected_tokens & actual_tokens) / len(expected_tokens)


def fetch(url, retries=2):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code != 200:
                return None, f"http {r.status_code}"
            ct = r.headers.get("Content-Type", "").lower()
            if any(x in ct for x in ("html", "json", "xml")):
                return None, f"content-type {ct!r}"
            content = r.content
            if not content.startswith(b"%PDF-"):
                return None, "no %PDF- magic"
            if len(content) < MIN_PDF_SIZE:
                return None, f"size {len(content)}"
            return content, "ok"
        except Exception as e:
            if i == retries - 1:
                return None, f"exc {type(e).__name__}"
            time.sleep(1)
    return None, "exhausted retries"


def first_author_last(paper):
    auths = paper.get("authors") or []
    if not auths:
        return ""
    name = auths[0].get("name", "")
    parts = re.findall(r"[A-Za-z]+", name)
    return parts[-1] if parts else ""


def identity_check(pdf_bytes, expected_title, expected_first_author_last):
    try:
        import fitz
    except ImportError:
        return True, "pymupdf-missing-skipped"
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for i in range(min(2, doc.page_count)):
            text += doc[i].get_text()
        doc.close()
    except Exception as e:
        return False, f"parse exc: {e}"
    head = text[:3000]
    recall = title_match(expected_title, head)
    if recall < 0.5:
        return False, f"title recall {recall:.2f}"
    if expected_first_author_last:
        if expected_first_author_last.lower() not in head.lower():
            return False, f"first-author {expected_first_author_last!r} not in head"
    return True, f"recall={recall:.2f}"


def try_sources(paper):
    out = []
    ext = paper.get("externalIds") or {}
    arxiv = ext.get("ArXiv")
    if arxiv:
        out.append(("arxiv", f"https://arxiv.org/pdf/{arxiv}.pdf"))
    oap = paper.get("openAccessPdf") or {}
    if oap.get("url"):
        out.append(("s2_oa", oap["url"]))
    return out


def main():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    FAIL_LOG.parent.mkdir(exist_ok=True)
    metadata = json.loads(META_PATH.read_text(encoding="utf-8"))
    failures, sources_used = [], {}
    n_ok = 0
    n_cached = 0

    for p in metadata:
        pid = p["paperId"]
        target = PDF_DIR / f"{pid}.pdf"
        if target.exists() and target.stat().st_size >= MIN_PDF_SIZE:
            sources_used[pid] = {"label": "cached"}
            n_cached += 1
            continue

        title = p.get("title", "")
        fln = first_author_last(p)
        sources = try_sources(p)
        if not sources:
            failures.append({"paperId": pid, "title": title, "reason": "no source URL available"})
            print(f"[NONE  ] {title[:70]}")
            continue

        attempts = []
        ok = False
        for label, url in sources:
            content, reason = fetch(url)
            if content is None:
                attempts.append({"src": label, "url": url, "reason": reason})
                continue
            id_ok, why = identity_check(content, title, fln)
            if not id_ok:
                attempts.append({"src": label, "url": url, "reason": f"identity: {why}"})
                continue
            target.write_bytes(content)
            sources_used[pid] = {"label": label, "url": url, "id_check": why}
            n_ok += 1
            ok = True
            print(f"[{label:6}] {title[:70]}")
            break

        if not ok:
            failures.append({"paperId": pid, "title": title, "attempts": attempts})
            print(f"[FAIL  ] {title[:70]}")
        time.sleep(0.3)

    FAIL_LOG.write_text(json.dumps(failures, indent=2))
    SRC_LOG.write_text(json.dumps(sources_used, indent=2))
    print(f"\nRetrieved: {n_ok} new, {n_cached} cached, {len(failures)} failed")


if __name__ == "__main__":
    main()
