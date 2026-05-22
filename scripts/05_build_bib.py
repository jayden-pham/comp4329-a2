"""
05_build_bib.py — generate cite_keys.json and output/main.bib.

For each paper in metadata.json that has a corresponding notes/{paperId}.json:
  - Generate cite_key as {lastname}{year}_{title_stub_2_words}
  - Resolve collisions with _a, _b, _c suffixes
  - Emit a BibTeX entry to output/main.bib

Entry type heuristic:
  @inproceedings — venue suggests conference (NeurIPS/ICML/ICLR/CVPR/...)
  @article — venue suggests journal (transactions, journal, JMLR, ...)
  @misc — everything else (arXiv preprints etc.)

Inputs:  papers/metadata.json, notes/*.json
Outputs: papers/cite_keys.json, output/main.bib
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_PATH = ROOT / "papers" / "metadata.json"
NOTES_DIR = ROOT / "notes"
CITE_KEYS_PATH = ROOT / "papers" / "cite_keys.json"
BIB_PATH = ROOT / "output" / "main.bib"

CONFERENCE_HINTS = [
    "neurips", "icml", "iclr", "acl", "emnlp", "naacl", "aaai",
    "cvpr", "iccv", "eccv", "ijcai", "colm", "blackboxnlp",
    "conference on", "international conference",
]
JOURNAL_HINTS = [
    "jmlr", "tmlr", "transactions", "journal of",
    "tpami", "nature", "science", "pnas",
]
STOPWORDS = {"a", "an", "the", "of", "for", "on", "in", "to", "and", "with", "via", "by"}


def stub(title):
    words = re.findall(r"[A-Za-z]+", title or "")
    kept = [w.lower() for w in words if w.lower() not in STOPWORDS][:2]
    return "_".join(kept) if kept else "untitled"


def lastname(authors):
    if not authors:
        return "anon"
    name = authors[0].get("name") or ""
    parts = re.findall(r"[A-Za-z]+", name)
    return parts[-1].lower() if parts else "anon"


def make_cite_key(p, existing_keys):
    base = f"{lastname(p.get('authors'))}{p.get('year') or 0}_{stub(p.get('title'))}"
    key = base
    suffix = ord("a")
    while key in existing_keys:
        key = f"{base}_{chr(suffix)}"
        suffix += 1
    return key


def venue_type(venue):
    v = (venue or "").lower()
    for h in JOURNAL_HINTS:
        if h in v:
            return "article"
    for h in CONFERENCE_HINTS:
        if h in v:
            return "inproceedings"
    return "misc"


def escape_bib(s):
    return (s or "").replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")


def format_authors(authors):
    out = []
    for a in (authors or []):
        name = (a.get("name") or "").strip()
        if not name:
            continue
        parts = name.rsplit(" ", 1)
        if len(parts) == 2:
            out.append(f"{parts[1]}, {parts[0]}")
        else:
            out.append(name)
    return " and ".join(out)


def bib_entry(cite_key, p):
    typ = venue_type(p.get("venue"))
    fields = {
        "author": format_authors(p.get("authors")),
        "title": "{" + escape_bib(p.get("title", "")) + "}",
        "year": str(p.get("year") or ""),
    }
    if typ == "inproceedings":
        fields["booktitle"] = escape_bib(p.get("venue", ""))
    elif typ == "article":
        fields["journal"] = escape_bib(p.get("venue", ""))
    else:
        if p.get("venue"):
            fields["howpublished"] = escape_bib(p["venue"])
        arxiv = (p.get("externalIds") or {}).get("ArXiv")
        if arxiv:
            fields["note"] = f"arXiv:{arxiv}"
    body = ",\n  ".join(f"{k} = {{{v}}}" for k, v in fields.items() if v)
    return f"@{typ}{{{cite_key},\n  {body}\n}}\n"


def main():
    metadata = {p["paperId"]: p for p in json.loads(META_PATH.read_text(encoding="utf-8"))}
    note_ids = {nf.stem for nf in NOTES_DIR.glob("*.json")}
    eligible = sorted(
        (pid for pid in note_ids if pid in metadata),
        key=lambda pid: (metadata[pid].get("year") or 0, metadata[pid].get("title") or ""),
    )

    cite_keys = {"paper_id_to_cite_key": {}, "cite_key_to_paper_id": {}}
    bib_entries = []
    for pid in eligible:
        p = metadata[pid]
        key = make_cite_key(p, cite_keys["cite_key_to_paper_id"])
        cite_keys["paper_id_to_cite_key"][pid] = key
        cite_keys["cite_key_to_paper_id"][key] = pid
        bib_entries.append(bib_entry(key, p))

    CITE_KEYS_PATH.write_text(json.dumps(cite_keys, indent=2))
    BIB_PATH.parent.mkdir(exist_ok=True)
    BIB_PATH.write_text("\n".join(bib_entries))
    print(f"Wrote {len(eligible)} entries to {BIB_PATH}")
    missing = [pid for pid in metadata if pid not in note_ids]
    print(f"  ({len(missing)} papers in metadata have no notes -> not cited)")


if __name__ == "__main__":
    main()
