"""
07_format_check.py — final format/compliance gates.

Checks:
  1. latexmk -pdf compiles output/main.tex without error (or pdflatex fallback)
  2. Page count (main body must be <= 8)
  3. Anonymization sweep: searches output/ for forbidden tokens
     (author name(s), university, email patterns)
  4. \\ref/\\autoref/\\cref resolution: every reference has a \\label somewhere
  5. Per-section word count

Outputs: output/format_report.md
Exit:    0 on all checks pass; 2 on any FAIL
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
SEC_DIR = OUTPUT_DIR / "sec"
REPORT_MD = OUTPUT_DIR / "format_report.md"

PAGE_LIMIT = 8

# Tokens that MUST NOT appear in the submission (anonymisation).
# Edit this list to include all author/affiliation strings to scrub.
ANON_FORBIDDEN = [
    "Jayden Pham",
    "jayden.pham",
    "khanhak299",
    "University of Sydney",
    "USYD",
    "Sydney University",
    "@uni.sydney.edu.au",
    "@sydney.edu.au",
]


def run(cmd, cwd):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=240)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def latex_compile():
    for cmd in (
        ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"],
        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
    ):
        rc, out, err = run(cmd, cwd=OUTPUT_DIR)
        if rc == 127:
            continue
        return cmd[0], rc, (out + "\n" + err)[-3000:]
    return None, 127, "neither latexmk nor pdflatex found"


def page_count():
    pdf = OUTPUT_DIR / "main.pdf"
    if not pdf.exists():
        return None
    try:
        import fitz
        d = fitz.open(pdf)
        n = d.page_count
        d.close()
        return n
    except Exception:
        return None


def anonymization_sweep():
    hits = []
    for tex in OUTPUT_DIR.rglob("*.tex"):
        text = tex.read_text(encoding="utf-8", errors="ignore")
        low = text.lower()
        for token in ANON_FORBIDDEN:
            if token.lower() in low:
                # Find line numbers
                for i, line in enumerate(text.splitlines(), 1):
                    if token.lower() in line.lower():
                        hits.append({
                            "file": str(tex.relative_to(ROOT)),
                            "line": i,
                            "token": token,
                        })
    return hits


def ref_label_check():
    refs, labels = set(), set()
    ref_re = re.compile(r"\\(?:ref|autoref|cref|Cref|eqref)\{([^}]+)\}")
    lbl_re = re.compile(r"\\label\{([^}]+)\}")
    for tex in OUTPUT_DIR.rglob("*.tex"):
        text = tex.read_text(encoding="utf-8", errors="ignore")
        refs.update(ref_re.findall(text))
        labels.update(lbl_re.findall(text))
    return sorted(refs - labels)


def section_words():
    counts = {}
    if not SEC_DIR.exists():
        return counts
    for tex in sorted(SEC_DIR.glob("*.tex")):
        text = tex.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(r"%.*", "", text)
        text = re.sub(r"\\[A-Za-z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", text)
        words = re.findall(r"[A-Za-z][A-Za-z'-]+", text)
        counts[tex.name] = len(words)
    return counts


def main():
    report = ["# Format Check", ""]
    fails = 0

    backend, rc, log = latex_compile()
    if rc == 0:
        report.append(f"- [OK] LaTeX compile via `{backend}`")
    elif backend is None:
        report.append("- [SKIP] LaTeX compile (neither latexmk nor pdflatex found)")
    else:
        report.append(f"- [FAIL] LaTeX compile via `{backend}` (rc={rc})")
        report.append("")
        report.append("```")
        report.append(log)
        report.append("```")
        fails += 1

    n = page_count()
    if n is None:
        report.append("- [SKIP] Page count (no main.pdf)")
    elif n > PAGE_LIMIT:
        report.append(f"- [FAIL] Page count {n} > {PAGE_LIMIT} limit")
        fails += 1
    else:
        report.append(f"- [OK] Page count {n} <= {PAGE_LIMIT}")

    hits = anonymization_sweep()
    if hits:
        report.append(f"- [FAIL] Anonymisation: {len(hits)} forbidden token(s) found")
        for h in hits:
            report.append(f"    - `{h['file']}:{h['line']}` token={h['token']!r}")
        fails += 1
    else:
        report.append("- [OK] Anonymisation sweep clean")

    dangling = ref_label_check()
    if dangling:
        report.append(f"- [FAIL] {len(dangling)} dangling references: {', '.join(dangling[:10])}")
        fails += 1
    else:
        report.append("- [OK] All `\\ref` resolve to `\\label`")

    counts = section_words()
    if counts:
        report.append("")
        report.append("## Section word counts")
        report.append("")
        for k, v in counts.items():
            report.append(f"- `{k}`: {v} words")
        report.append(f"- **Total**: {sum(counts.values())} words")

    REPORT_MD.write_text("\n".join(report) + "\n")
    print("\n".join(report))
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
