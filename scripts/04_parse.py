"""
04_parse.py — extract text from PDFs with page markers and metadata header.

For each papers/pdfs/{paperId}.pdf:
  - PyMuPDF extract text per page
  - Prepend a metadata header (TITLE/AUTHORS/YEAR/VENUE/PAPER_ID/ABSTRACT)
  - Insert --- PAGE N --- markers between pages
  - Flag quality issues (too short, encoding artefacts, very long)

Inputs:  papers/pdfs/*.pdf, papers/metadata.json
Outputs: papers/parsed/{paperId}.txt, logs/parse_quality.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "papers" / "pdfs"
PARSED_DIR = ROOT / "papers" / "parsed"
META_PATH = ROOT / "papers" / "metadata.json"
QUALITY_LOG = ROOT / "logs" / "parse_quality.json"

MIN_TEXT_CHARS = 1000
ENCODING_THRESHOLD = 0.05
LONG_THRESHOLD = 120_000


def header(p):
    authors = ", ".join(a.get("name", "") for a in (p.get("authors") or []))
    lines = [
        f"TITLE: {p.get('title', '')}",
        f"AUTHORS: {authors}",
        f"YEAR: {p.get('year', '')}",
        f"VENUE: {p.get('venue', '')}",
        f"PAPER_ID: {p.get('paperId', '')}",
        f"ABSTRACT: {p.get('abstract', '') or ''}",
        "=" * 60,
    ]
    return "\n".join(lines) + "\n\n"


def main():
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_LOG.parent.mkdir(exist_ok=True)
    metadata = {p["paperId"]: p for p in json.loads(META_PATH.read_text(encoding="utf-8"))}

    import fitz  # PyMuPDF
    flags = []
    n_ok = 0
    n_skip = 0

    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        pid = pdf.stem
        target = PARSED_DIR / f"{pid}.txt"
        if target.exists() and target.stat().st_size > 0:
            n_skip += 1
            continue
        meta = metadata.get(pid, {"paperId": pid})
        try:
            doc = fitz.open(pdf)
            parts = [header(meta)]
            for i in range(doc.page_count):
                parts.append(f"\n--- PAGE {i + 1} ---\n")
                parts.append(doc[i].get_text())
            text = "".join(parts)
            doc.close()
        except Exception as e:
            flags.append({"paperId": pid, "flag": "parse_exception", "reason": str(e)})
            continue

        issues = []
        if len(text) < MIN_TEXT_CHARS:
            issues.append("low_quality")
        if text.count(chr(0xFFFD)) / max(1, len(text)) > ENCODING_THRESHOLD:
            issues.append("encoding_issues")
        if len(text) > LONG_THRESHOLD:
            issues.append("very_long")
        if issues:
            flags.append({
                "paperId": pid,
                "title": meta.get("title"),
                "flags": issues,
                "chars": len(text),
            })

        target.write_text(text, encoding="utf-8")
        n_ok += 1

    QUALITY_LOG.write_text(json.dumps(flags, indent=2))
    print(f"Parsed: {n_ok} new, {n_skip} cached. Flagged: {len(flags)}.")


if __name__ == "__main__":
    main()
