"""
06_traceability_check.py — verify every \\cite{} in section files.

For each \\cite{cite_key} found in output/sec/*.tex:
  1. cite_key resolves to a paper_id via papers/cite_keys.json
  2. A '% src: <paper_id> pp.<page> (<notes_field>) — "<...>"' comment exists
     on the same line or within 3 lines after the \\cite
  3. The paper_id referenced in the % src: line matches an existing notes file
  4. The notes_field name is in the allowed set

Calibration WARN (heuristic — full check is in the fact-checker agent):
  - Lines containing definitive verbs near a cite are flagged for review;
    the fact-checker will resolve against venue/peer-review status.

Inputs:  output/sec/*.tex, papers/cite_keys.json, notes/*.json
Outputs: output/traceability_report.json
         output/traceability_report.md
Exit:    0 if zero FAILs (WARNs allowed); 2 if any FAIL
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEC_DIR = ROOT / "output" / "sec"
CITE_KEYS_PATH = ROOT / "papers" / "cite_keys.json"
NOTES_DIR = ROOT / "notes"
REPORT_JSON = ROOT / "output" / "traceability_report.json"
REPORT_MD = ROOT / "output" / "traceability_report.md"

NOTE_FIELDS = {
    "main_claims", "methodology", "key_results", "limitations",
    "relevance_to_rq", "key_quotes",
}
DEFINITIVE_VERBS = ["establish", "prove", "demonstrate", "confirm", "verify"]

CITE_RE = re.compile(r"\\cite\{([^}]+)\}")
SRC_RE = re.compile(
    r"%\s*src:\s*([A-Za-z0-9_\-]+)\s+pp\.([0-9?]+)\s*\(([A-Za-z_]+(?:\[\d+\])?)\)"
)


def find_src_comments(lines, idx, lookahead=3):
    found = []
    for j in range(idx, min(idx + lookahead + 1, len(lines))):
        for m in SRC_RE.finditer(lines[j]):
            found.append((j, m))
    return found


def main():
    if not CITE_KEYS_PATH.exists():
        print("No cite_keys.json yet; run scripts/05_build_bib.py first. Skipping.")
        return 0
    cite_keys = json.loads(CITE_KEYS_PATH.read_text(encoding="utf-8"))
    cite_to_pid = cite_keys.get("cite_key_to_paper_id", {})

    if not SEC_DIR.exists():
        print(f"No {SEC_DIR}; nothing to check.")
        return 0

    fails, warns, n_cites = [], [], 0

    for tex in sorted(SEC_DIR.glob("*.tex")):
        lines = tex.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines):
            for m in CITE_RE.finditer(line):
                keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
                src_comments = find_src_comments(lines, idx)
                src_by_pid = {sm.group(1): (j, sm) for j, sm in src_comments}

                for ckey in keys:
                    n_cites += 1
                    loc = {"file": tex.name, "line": idx + 1, "cite_key": ckey}
                    if ckey not in cite_to_pid:
                        fails.append({**loc, "reason": "cite_key not in cite_keys.json"})
                        continue
                    pid = cite_to_pid[ckey]
                    if pid not in src_by_pid:
                        if src_comments:
                            fails.append({**loc, "reason": f"no % src: comment for paper_id {pid}"})
                        else:
                            fails.append({**loc, "reason": "no % src: comment within 3 lines"})
                        continue
                    _, sm = src_by_pid[pid]
                    notes_field = sm.group(3).split("[")[0]
                    if notes_field not in NOTE_FIELDS:
                        fails.append({**loc, "reason": f"unknown notes_field {notes_field!r}"})
                        continue
                    if not (NOTES_DIR / f"{pid}.json").exists():
                        fails.append({**loc, "reason": f"notes file missing for {pid}"})

                lower = line.lower()
                for verb in DEFINITIVE_VERBS:
                    if verb in lower:
                        warns.append({
                            "file": tex.name, "line": idx + 1,
                            "reason": f"definitive verb '{verb}' near cite — fact-checker should verify peer-review status",
                        })
                        break

    REPORT_JSON.write_text(json.dumps(
        {"n_cites": n_cites, "fails": fails, "warns": warns}, indent=2))
    md = [
        "# Traceability Report",
        "",
        f"Total cites: {n_cites}",
        f"Fails: {len(fails)}",
        f"Warns: {len(warns)}",
        "",
    ]
    if fails:
        md.append("## FAILS")
        md.append("")
        for f in fails:
            md.append(f"- `{f['file']}:{f['line']}` `\\cite{{{f['cite_key']}}}` — {f['reason']}")
        md.append("")
    if warns:
        md.append("## WARNS (calibration heuristic — verify with fact-checker)")
        md.append("")
        for w in warns:
            md.append(f"- `{w['file']}:{w['line']}` — {w['reason']}")
        md.append("")
    REPORT_MD.write_text("\n".join(md))

    print(f"Traceability: {n_cites} cites, {len(fails)} FAILs, {len(warns)} WARNs")
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
