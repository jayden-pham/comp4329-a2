# Literature-Review Pipeline — Architecture Blueprint

A self-contained specification for rebuilding this pipeline in any other research repo. The pipeline produces a PhD-level LaTeX literature review + research proposal with **machine-checkable citation traceability** and **calibrated peer-review language** — written by Claude Code subagents but gated by deterministic Python scripts so nothing the LLM produces can silently bypass the quality bars.

The reference implementation targeted mechanistic interpretability + transformer belief updating. **Everything below is topic-agnostic**; the only files that change per topic are the four governance JSONs (`seed_papers.json`, `curated_external.json`, `must_have_papers.json`, `RESEARCH_CONTEXT.md`) and the writer-section table in `CLAUDE.md`.

---

## 1. Design Philosophy

Five principles drive every design decision. Preserve all five in any rebuild.

1. **LLMs write, scripts gate.** Every LLM-produced artefact (notes, synthesis, sections, fact-check report) is followed by a Python script that mechanically enforces a structural contract. Subagents are not trusted to police themselves.
2. **Three-level identity (cite_key → work_id → paper_id).** Citations in `\cite{}` are never raw paper IDs. A `work_id` represents one intellectual work; a `paper_id` is one *version* of it (arXiv preprint vs accepted conference paper count as two paper_ids, one work_id). One cite_key per work.
3. **Peer-review status is a first-class field.** Every cited work has a `canonical_status` in {`peer_reviewed_top`, `peer_reviewed_other`, `preprint`, `industry_report`, `informal`, `unknown`}. Writers must calibrate verb choice to status; fact-checker WARNs on mismatch; coverage audit enforces ≥ N peer-reviewed citations as a RED gate.
4. **Causal vs correlational discipline.** Each paper's notes carry an `evidence_strength` field (causal/correlational/demonstrative/theoretical/mixed). Writers may not use causal language ("the model uses X") for probing-only (correlational) evidence. This is checked structurally and semantically.
5. **Zero hallucination tolerance via traceability comments.** Every `\cite{cite_key}` must be followed within 3 lines by a LaTeX comment `% src: <paper_id> pp.<page> (<notes_field>) — "<short evidence>"`. A Python script verifies the comment resolves to an existing notes file and field. The LLM fact-checker then semantically verifies the claim against that field.

---

## 2. Pipeline Overview (7 phases)

```
Phase 0   00_seed_resolve.py        Verify seed-paper IDs against Semantic Scholar
Phase 1   01_search.py              S2 keyword search (50+ queries × topic)
Phase 1b  01b_openreview_pull.py    Scoped OpenReview pull (accepted notes only)
Phase 1c  01c_curated_pull.py       Industry/blog sources (Anthropic, Distill, …)
Phase 2   02_snowball.py            Forward/backward citation chaining from seeds
Phase 3   03_retrieve.py            Download PDFs (arXiv → S2 OA → Unpaywall → OpenReview → ACL)
Phase 3b  04_parse.py               Extract text with page markers (PyMuPDF)
─────────────── HUMAN CHECKPOINT 1: retrieval failures, parse quality ───────────────
Phase 4a  04b_status_tag.py         Tag publication_status per paper from venues.json
          04c_link_versions.py      Group paper_ids into work_ids (intellectual works)
─────────────── HUMAN CHECKPOINT 2: review version-linkage ambiguous matches ────────
Phase 4   [paper-reader subagents]  notes/{paper_id}.json per work (≥3 page-anchored quotes)
Phase 4b  05_build_bib.py           Generate cite_keys.json + references.bib (work-level)
          06_coverage_audit.py      Coverage gates (RED on fail)
─────────────── HUMAN CHECKPOINT 3: coverage audit, must-have papers ────────────────
Phase 5   [synthesizer subagent]    synthesis/themes.json + synthesis/gaps.md
          06_coverage_audit.py      Re-run for section-mapping gate
─────────────── HUMAN CHECKPOINT 4: synthesis quality + section coverage ────────────
Phase 6   [writer subagents × N]    output/sections/*.tex (with `% src:` comments)
Phase 6b  05_build_bib.py           Deterministic re-run
          07_traceability_check.py  Structural + calibration-language gates (FAIL = exit 2)
          06_coverage_audit.py      Re-run with absolute peer-reviewed gate
Phase 7   [fact-checker subagent]   output/verification_report.md
Phase 7b  [critical-reviewer agent] output/critical_review.md
─────────────── Compile LaTeX → submit ─────────────────────────────────────────────
```

Phases 0-3 + 4a + 4b + 6b are Python; phases 4, 5, 6, 7, 7b are Claude Code subagents.

---

## 3. Repository Layout

```
{repo_root}/
├── CLAUDE.md                     # Claude Code instructions for all phases (this file's spec)
├── RESEARCH_CONTEXT.md           # Research question, sub-topics, sub-topic→section map
├── README.md                     # Human-run instructions
├── requirements.txt              # requests, pymupdf
├── seed_papers.json              # Verified seed papers (Phase 0 fills in S2 IDs)
├── must_have_papers.json         # Governance: papers that MUST appear; sub-topic thresholds
├── curated_external.json         # Non-S2 sources (industry blogs, technical reports)
├── venues.json                   # Venue → publication_status mapping
├── .claude/agents/
│   ├── paper-reader.md           # Subagent: one paper → structured notes
│   ├── synthesizer.md            # Subagent: all notes → themes + gaps
│   ├── writer.md                 # Subagent: one section → LaTeX
│   ├── fact-checker.md           # Subagent: verify every \cite{} against notes
│   └── critical-reviewer.md      # Subagent: adversarial PhD examiner critique
├── scripts/
│   ├── 00_seed_resolve.py
│   ├── 01_search.py
│   ├── 01b_openreview_pull.py
│   ├── 01c_curated_pull.py
│   ├── 02_snowball.py
│   ├── 03_retrieve.py
│   ├── 04_parse.py
│   ├── 04b_status_tag.py
│   ├── 04c_link_versions.py
│   ├── 05_build_bib.py
│   ├── 06_coverage_audit.py
│   └── 07_traceability_check.py
├── papers/
│   ├── metadata.json             # All discovered papers (from search/snowball/curated/openreview)
│   ├── paper_status.json         # paper_id → {status, confidence, basis}
│   ├── works.json                # work_id → {canonical_paper_id, version_paper_ids, canonical_status, …}
│   ├── cite_keys.json            # work_id ↔ cite_key ↔ notes_paper_id maps
│   ├── pdfs/                     # Downloaded PDFs ({paper_id}.pdf)
│   └── parsed/                   # Extracted text ({paper_id}.txt with --- PAGE N --- markers)
├── notes/
│   └── {paper_id}.json           # Per-work structured notes (from paper-reader)
├── synthesis/
│   ├── themes.json               # Thematic clusters + suggested_section_mapping
│   └── gaps.md                   # Research gaps prose
├── logs/
│   ├── seed_resolution.json      # Phase 0 audit
│   ├── search_log.json           # Phase 1 query log
│   ├── openreview_pull.json      # Phase 1b log
│   ├── retrieval_failures.json   # Phase 3 fails
│   ├── retrieval_sources.json    # Phase 3 winning source per paper
│   ├── parse_quality.json        # Phase 3b flags
│   ├── version_linkage.json      # Phase 4a flagged ambiguous merges
│   └── coverage_audit.{json,md}  # Phase 4b/5b/6c audit
└── output/
    ├── {main}.tex                # Main LaTeX file (loads sections/* + bib)
    ├── references.bib            # Generated bibliography
    ├── sections/                 # One .tex per writer subagent
    ├── traceability_report.{json,md}
    ├── verification_report.md
    └── critical_review.md
```

---

## 4. Identity Model (CRITICAL — do not deviate)

Three levels of identifier. Every cross-reference in the codebase relies on this hierarchy.

```
cite_key   ←   what writers put in \cite{} (e.g. "olsson2022_induction_heads")
   │
   ▼
work_id    ←   one intellectual work; hash over canonical title + first-author + year
   │           (e.g. arXiv preprint + NeurIPS version = same work_id)
   ▼
paper_id   ←   one VERSION of a work
               - S2 hex paperId (40 chars, e.g. "c90a99e…")
               - synthetic "ext_*" id minted ONLY by 01b/01c for non-S2 sources
                 (e.g. "ext_anthropic_2022_toy_models_superposition")
```

`papers/cite_keys.json` is the single source of truth:

```json
{
  "work_id_to_cite_key":         { "<work_id>": "olsson2022_induction_heads", ... },
  "cite_key_to_work_id":         { "olsson2022_induction_heads": "<work_id>", ... },
  "paper_id_to_cite_key":        { "<any version paper_id>": "olsson2022_induction_heads", ... },
  "work_id_to_canonical_paper_id": { "<work_id>": "<canonical paper_id>", ... },
  "work_id_to_notes_paper_id":   { "<work_id>": "<paper_id of notes file>", ... }
}
```

The two paper-id maps differ: `canonical_paper_id` is the version used for the bibliography/status (highest peer-review tier); `notes_paper_id` is the version a notes file actually exists for (may be a fallback preprint when the canonical conference PDF wasn't retrievable). The traceability check resolves `% src: <paper_id>` against `paper_id_to_cite_key` so writers can comment any version paper_id and it still validates.

**Status promotion rule**: `canonical_status = max(version statuses)` under the ordering `peer_reviewed_top > peer_reviewed_other > preprint > industry_report > informal > unknown`. A work cited in any reviewed venue is reported as peer-reviewed even when the version on disk is the preprint.

**Synthetic IDs**: only `01b_openreview_pull.py` and `01c_curated_pull.py` mint `ext_*` IDs. Every other script treats them identically to S2 hex IDs. The `ext_<source>_<slug>` namespace guarantees no collision with S2 40-char hex.

---

## 5. Governance Files (the four you customise per topic)

### 5.1 `RESEARCH_CONTEXT.md`

```markdown
# Research Context
## Research Question
<One-sentence RQ.>

## Assignment Requirements
- Task 1: literature review N words, ≥ N cited peer-reviewed works, IEEE citations
- Task 2: research proposal M words with evaluation plan
- Output format: LaTeX

## Sub-topics to Cover
1. **<sub-topic 1>** — <one-line description>
...
8. **<sub-topic 8>** — <one-line description>

## Constraints
- ZERO hallucination tolerance
- Every claim traces to a retrieved paper
- Every note includes page-approximate references
- Agents write null for fields they cannot determine — never guess

## Sub-topic ↔ Section Mapping (canonical)
| Sub-topic (RC #) | Canonical ID                 | Section file                              |
|---|---|---|
| 1 <name>         | `foundations`                | `02_<sub-topic-name>`                     |
| ...              | ...                          | ...                                       |

The canonical IDs above appear identically in must_have_papers.json:subtopic_keywords,
seed_papers.json:subtopics, and curated_external.json:entries[].subtopics.
scripts/06_coverage_audit.py cross-references them.
```

The sub-topic→section mapping defines how many writer subagents there will be (one per section file). Two sub-topics MAY map to one section if they are analytically inseparable; the audit script knows about this.

### 5.2 `seed_papers.json`

A flat list of papers the human knows are foundational. Each entry:

```json
{
  "title": "...",
  "arxiv_id": "2209.11895",
  "doi": null,
  "first_author_last": "Olsson",
  "year": 2022,
  "semantic_scholar_id": null,
  "subtopics": ["foundations", "in_context_learning"],
  "why": "<1-sentence reason this is a seed>"
}
```

`scripts/00_seed_resolve.py` fills in `semantic_scholar_id` via arXiv→DOI→title-search-with-cosine-and-author-and-year verification. Manual nulls require manual fix. Snowball refuses to run while any seed has `semantic_scholar_id: null`.

### 5.3 `curated_external.json`

Non-S2 sources (industry technical reports, blog-format research like Distill / Anthropic Transformer Circuits Thread). Each entry has a `synthetic_id`, full author list, year, venue, `url`, `publication_status` ({`industry_report` | `informal`}), `status_confidence`, and optionally `also_known_as_s2: ["<paperId>"]` for explicit linkage to an S2 entry of the same work.

`scripts/01c_curated_pull.py` first attempts to resolve to a real S2 paperId (so industry papers that were later published get a real S2 ID); only if S2 lookup fails does the entry receive its `ext_*` synthetic ID. Manual PDF placement at `papers/pdfs/{paper_id}.pdf` is supported.

The top of the file specifies `max_external_share_pct: 15` — the coverage audit YELLOW-flags if `ext_*` papers exceed 15% of the corpus. Adjust per topic; for an industry-heavy field this can go to 25.

### 5.4 `must_have_papers.json`

```json
{
  "must_have": [
    {"title": "...", "first_author_last": "...", "year": ..., "rationale": "..."},
    ...
  ],
  "subtopic_min_papers": {
    "foundations": 6,
    "<sub-topic-id>": <int>,
    ...
  },
  "subtopic_min_keyword_hits": 2,
  "subtopic_keywords": {
    "foundations": [
      "circuit analysis", "attention head", "residual stream",
      "induction head", "transformer circuits", "computational graph"
    ],
    ...
  }
}
```

**Keyword design rule**: keywords must be **multi-word phrases**, not bare common words. `06_coverage_audit.py` requires ≥ `subtopic_min_keyword_hits` distinct phrases per paper before that paper counts toward a sub-topic. Single common words like "transformer" or "context" inflate coverage incorrectly. Always use 2-3-word phrases.

### 5.5 `venues.json`

Topic-agnostic. Maps venue strings to publication_status:

```json
{
  "buckets": ["peer_reviewed_top", "peer_reviewed_other", "preprint", "industry_report", "informal", "unknown"],
  "exact_top":    ["neurips", "icml", "iclr", "acl", "emnlp", "naacl", "aaai", "cvpr", "iccv", "eccv", "ijcai", "colm", "tacl", "jmlr", "tmlr", "nature", "science", "pnas", "blackboxnlp"],
  "exact_other":  ["coling", "uai", "aistats", "interspeech", "kdd", "wsdm", "sigir", "eacl", "icassp", "iclr workshop", "neurips workshop", "icml workshop"],
  "contains_top": ["advances in neural information processing", "international conference on machine learning", "ieee transactions", ...],
  "contains_other": ["workshop", "findings", "blackboxnlp", ...],
  "preprint_signals": ["arxiv", "preprint", "biorxiv", "ssrn"],
  "industry_report_venues": ["anthropic", "openai", "deepmind", "transformer circuits thread", "distill"],
  "informal_signals": ["lesswrong", "alignment forum", "medium.com", "blog post"]
}
```

Add or remove venues for the target field (e.g. for HCI/security add CHI, USENIX, S&P, CCS).

---

## 6. The 12 Python Scripts (specifications)

All scripts: standard library + `requests` + `pymupdf`. No notebooks. Run sequentially. Each has a deterministic, idempotent contract.

### `00_seed_resolve.py`
- Input: `seed_papers.json`
- Output: `seed_papers.json` (updated in place), `logs/seed_resolution.json`
- Verifies every seed against Semantic Scholar via arXiv-id → DOI → title-search (cosine ≥ 0.80, first-author match, year ± 1). Pre-existing IDs are re-verified by default; `--trust-preexisting` skips that.
- Exit 2 if any seed remains unresolved.

### `01_search.py`
- Input: `RESEARCH_CONTEXT.md` topics (hard-coded list of 40-60 search queries spanning all sub-topics)
- Output: `papers/metadata.json`, `logs/search_log.json`
- Paginates S2 `/paper/search` up to 1000 results per query. Year filter (default ≥ 2017 for transformer-era; configurable). Keeps abstract-less papers.
- Honours `S2_API_KEY` env var. Sleeps 1s between calls without key.

### `01b_openreview_pull.py`
- Input: venue list (ICLR/TMLR/COLM/workshops), `TOPIC_TERMS` keyword filter (re-uses 01's vocabulary)
- Output: augments `papers/metadata.json`, `logs/openreview_pull.json`
- **Hard rule**: EVERY OpenReview venue requires accept-decision filtering. When `directReplies` doesn't carry the decision, a fallback `/notes?forum={id}` walk is used. Notes for which no decision can be located are EXCLUDED (counted as `skipped_no_decision`), never defaulted to include. This prevents rejected workshop submissions from being mis-tagged as `peer_reviewed_other`.
- Looks up each accepted note on S2 with title+first-author+year verification. If unverified, keeps synthetic `ext_openreview_<noteid>`.

### `01c_curated_pull.py`
- Input: `curated_external.json`
- Output: augments `papers/metadata.json`, writes `papers/curated_urls.json`
- For each entry, attempts S2 resolution (same verification as seed resolver). On success uses the real S2 paperId. On failure mints `ext_<source>_<slug>`. Only place except 01b that can mint synthetic IDs.

### `02_snowball.py`
- Input: `seed_papers.json` (with resolved IDs), `papers/metadata.json`
- Output: augments `papers/metadata.json`
- Forward and backward citation chaining from seeds via S2 `/paper/{id}/citations` and `/paper/{id}/references`. Recent papers (≤ 2 years) bypass the `min_citations` gate so SOTA isn't filtered out. Backward floor at year 2010 to capture foundational pre-transformer work (adjust per topic).
- REFUSES to run on seeds with `semantic_scholar_id: null`.

### `03_retrieve.py`
- Input: `papers/metadata.json`, `papers/curated_urls.json`
- Output: `papers/pdfs/{paper_id}.pdf`, `logs/retrieval_failures.json`, `logs/retrieval_sources.json`
- Source attempt order: arXiv → S2 openAccessPdf → Unpaywall (DOI; requires `UNPAYWALL_EMAIL`) → OpenReview (title) → ACL Anthology. For `ext_*` papers, tries the curated URL first.
- **Validation**: HTTP 200 + starts with `%PDF-` magic bytes + ≥ 10 KB + content-type not html/json/xml.
- **Identity check**: after download, parses the first 2 pages with PyMuPDF, runs cosine similarity on title and first-author last-name. Rejects mismatches (logged).
- Records the winning source URL per paper in `logs/retrieval_sources.json`.

### `04_parse.py`
- Input: `papers/pdfs/*.pdf`, `papers/metadata.json`
- Output: `papers/parsed/{paper_id}.txt`, `logs/parse_quality.json`
- Uses PyMuPDF to extract text. Prepends a metadata header (TITLE/AUTHORS/YEAR/VENUE/PAPER_ID/ABSTRACT). Inserts `--- PAGE N ---` markers between pages. Detects likely section headings as `## heading`. Flags `low_quality` (< 1000 chars), `encoding_issues` (> 5% replacement chars), `very_long` (> 120k chars).

### `04b_status_tag.py`
- Input: `papers/metadata.json`, `venues.json`, `curated_external.json`
- Output: `papers/paper_status.json`
- Tagging priority: curated_external override → venue exact_top → exact_other → contains_top → contains_other → industry_report → informal → preprint_signals → heuristic (arXiv present + no venue → preprint) → unknown.
- Outputs per paper: `{status, confidence (high/medium/low), basis, venue}`.

### `04c_link_versions.py`
- Input: `papers/metadata.json`, `papers/paper_status.json`, `curated_external.json`
- Output: `papers/works.json`, `logs/version_linkage.json`
- Linking heuristics, FIRST MATCH WINS:
  1. Identical externalIds.ArXiv
  2. Identical externalIds.DOI
  3. `curated_external.json:also_known_as_s2` explicit linkage
  4. Title cosine ≥ 0.92 + first-author match + year ± 1
- Anything with title cosine 0.85-0.92 without arXiv/DOI/curated evidence is FLAGGED in `logs/version_linkage.json` and NOT auto-merged.
- Canonical version selection: highest `STATUS_RANK` wins. Ties broken by (a) prefer non-arXiv venue (b) most recent (c) lexicographic paper_id.
- Output `works.json` schema:
  ```json
  {
    "<work_id>": {
      "canonical_paper_id": "...",
      "version_paper_ids": ["...", "..."],
      "canonical_title": "...",
      "canonical_authors": [...],
      "canonical_year": ...,
      "canonical_venue": "...",
      "canonical_status": "peer_reviewed_top",
      "status_confidence": "high",
      "linkage_basis": "arxiv_id" | "doi" | "curated" | "title_author_year"
    }
  }
  ```

### `05_build_bib.py`
- Input: `papers/works.json`, `papers/metadata.json`, `notes/*.json`
- Output: `papers/cite_keys.json`, `output/references.bib`
- Eligible works = those with notes for either canonical or any fallback version (records `work_id_to_notes_paper_id` accordingly).
- Cite-key format: `{first_author_lastname_slug}{year}_{title_stub_2_words}` (e.g. `olsson2022_induction_heads`). Collision suffix `_a`, `_b`, …
- BibTeX entry types: `@inproceedings` (conferences), `@article` (journals/transactions), `@techreport` (industry_report), `@misc` (everything else). Author names formatted "Last, First". Title double-braced to preserve case.
- Deterministic: sort by year ASC, then canonical title, then work_id.

### `06_coverage_audit.py`
- Input: everything generated so far + `must_have_papers.json` + `output/sections/*.tex` (optional)
- Output: `logs/coverage_audit.json`, `logs/coverage_audit.md`
- Gates (counts at WORK level, not paper_id level):

  | Gate | Severity | Threshold |
  |---|---|---|
  | `cited_peer_reviewed_works` | RED | ≥ 25 (assignment requirement) — only fires after Phase 6 when section files exist |
  | `per_section_peer_reviewed_anchors` | RED | ≥ 2 for core sections, ≥ 1 for supporting sections |
  | `proposal_methods_anchors` | RED | Each named method/tool in proposal must have ≥ 1 peer-reviewed cite within 2 lines |
  | `subtopic_coverage_min` | RED | Per-subtopic ≥ 50% of `subtopic_min_papers` |
  | `notes_volume` | RED | ≥ 15 canonical notes |
  | `must_have_present` | RED | ≤ 5 must-have papers missing |
  | `peer_review_balance_overall` | YELLOW | ≥ 50% peer-reviewed in corpus; RED < 30% |
  | `peer_review_balance_core` | YELLOW | ≥ 50% of `depth_recommendation=core` papers are peer-reviewed |
  | `external_share` | YELLOW | ≤ `max_external_share_pct` (15% default) |
  | `recency` | YELLOW | ≥ 30% within 24 months |
  | `section_mapping` | YELLOW | Each section in themes.json has ≥ 3 papers (only after Phase 5) |

- Exit code 2 on any RED.

### `07_traceability_check.py`
- Input: `output/sections/*.tex`, `papers/cite_keys.json`, `papers/works.json`, `notes/*.json`
- Output: `output/traceability_report.json`, `output/traceability_report.md`
- For every `\cite{cite_key}`:
  1. Resolve cite_key → work_id → notes_paper_id
  2. Verify `notes/{notes_paper_id}.json` exists
  3. Verify a `% src: <paper_id> ...` LaTeX comment is within 3 lines of the cite
  4. Verify the src comment references a supported notes field name AND/OR a page reference
- Calibration-language check: if any `\cite{}` on a line is for a work whose canonical_status ∈ {`preprint`, `industry_report`, `informal`} AND the surrounding sentence contains a definitive verb (`establishes`, `proves`, `demonstrates that`, `shows that`, `confirms`, `verifies`), emit a WARN with reason `definitive_verb_on_unreviewed_source`. Sentence window: ±1 line, sliced on `[.!?]` boundaries.
- Exit 0 if all FAILs are zero (calibration is WARN, not FAIL). Exit 2 on any FAIL.

---

## 7. The Five Subagents

Each subagent lives in `.claude/agents/{name}.md` as a YAML-frontmatter markdown file. The frontmatter declares `name`, `description`, and `tools` (always just `Read, Write`).

### 7.1 `paper-reader` (Phase 4)

**Input**: one parsed `.txt` file (with `--- PAGE N ---` markers).

**Output**: `notes/{paper_id}.json` matching this schema EXACTLY:

```json
{
  "paper_id": "<filename without .txt>",
  "title": "<exact title from paper>",
  "authors": ["Last, F.", ...],
  "year": 2024,
  "venue": "<conf/journal name>",
  "publication_status_observed": "<what the PAPER says about itself — observational, NOT a judgment>",
  "main_claims": ["claim 1 in your own words", ...],
  "methodology": "<2-3 sentence description>",
  "key_results": ["concrete result 1", ...],
  "evidence_strength": "causal | correlational | demonstrative | theoretical | mixed",
  "limitations": ["limitation 1", ...],
  "relevance_to_rq": "<1-2 sentences on relevance to RQ>",
  "key_quotes": [
    {"text": "exact verbatim quote ≤30 words", "page_approx": 7, "context": "what this quote supports"},
    ...
  ],
  "related_work_mentioned": [...],
  "depth_recommendation": "core | supporting | peripheral",
  "confidence": "high | medium | low",
  "extraction_issues": "null or description"
}
```

**Hard rules**:
- ≥ 3 `key_quotes` per paper (different aspects: one for method, one for result, one for limitation). Fewer is allowed ONLY with `confidence: low` and a justification in `extraction_issues`.
- `page_approx`: nearest preceding `--- PAGE N ---` marker. Never null.
- Quotes are EXACT verbatim substrings. No paraphrasing.
- `evidence_strength` is critical for downstream calibration. Probing-only papers are `correlational` even when the prose says "the model uses X". Linear-probe accuracy alone is correlational evidence.
- `publication_status_observed` is OBSERVATIONAL ("NeurIPS 2023 main track", "arXiv preprint", "Anthropic technical report"). Do NOT make a quality judgment — that's done by `04b_status_tag.py` from venue metadata.
- Write null (never invent) for any field you cannot determine.

### 7.2 `synthesizer` (Phase 5, single agent)

**Input**: all `notes/*.json` + `RESEARCH_CONTEXT.md` + `must_have_papers.json` + `logs/coverage_audit.md`.

**Output**: `synthesis/themes.json` and `synthesis/gaps.md`.

`themes.json` schema:
```json
{
  "themes": [
    {
      "id": "snake_case_id",
      "label": "Human-readable theme name",
      "description": "2-3 sentence description",
      "subtopic_ids": ["<canonical IDs from RESEARCH_CONTEXT.md>"],
      "papers": ["<paper_id>", ...],
      "core_papers": ["<paper_ids for in-depth treatment>"],
      "consensus_findings": "<what papers agree on>",
      "open_debates": "<where they disagree>",
      "methodological_trends": "<common methods>",
      "temporal_progression": "<how the theme evolved>"
    }
  ],
  "cross_theme_bridges": [
    {"paper_id": "<id>", "themes": ["<theme_id>", "<theme_id>"], "bridge_note": "..."}
  ],
  "suggested_section_mapping": {
    "<section_filename_stem>": ["<paper_id>", ...]
  }
}
```

`gaps.md`: 3-5 research gaps, each with: what the gap is, why it matters for the RQ, which existing papers come closest but fall short, how the gap connects to the proposed research.

**Rules**: every claim references a paper_id present in `notes/`. Never introduce information not in the notes. Group by intellectual contribution, not chronologically. Mark which papers in each theme are core vs supporting.

### 7.3 `writer` (Phase 6, one invocation per section)

**Input**: `synthesis/themes.json`, `synthesis/gaps.md`, `papers/cite_keys.json`, `papers/works.json` (for canonical_status), and the `notes/*.json` files relevant to the assigned section. The orchestrator tells the writer which section to write and supplies target word count and focus description.

**Output**: `output/sections/{section_name}.tex`.

**LaTeX structural rules**:
- Open with `\subsection{...}` (NOT `\section{...}`). The main `.tex` file already opens `\section{Literature Review}` and `\section{Research Proposal}`.
- Use `\subsubsection{}` for internal divisions.
- Do not reopen `\documentclass`, `\begin{document}`, or `\bibliography`.

**Citation rules (enforced by `07_traceability_check.py`)**:
- Every factual claim has `\cite{cite_key}` where cite_key comes from `papers/cite_keys.json`. NEVER raw paper_id.
- One cite_key per intellectual work (the map enforces this).
- After every `\cite{cite_key}`, on the same line or the next line, add a comment:
  ```
  % src: <paper_id> pp.<page> (<notes_field>) — "<short evidence ≤ 20 words>"
  ```
  where `<paper_id>` is the notes_paper_id (looked up via `cite_keys.json[work_id_to_notes_paper_id]`), `<page>` is from `key_quotes[i].page_approx`, and `<notes_field>` is one of `main_claims`, `methodology`, `key_results`, `limitations`, `relevance_to_rq`, `key_quotes` (optionally indexed e.g. `key_quotes[0]`).
- For grouped citations `\cite{a, b, c}`, one `% src:` line per cite_key, separate lines.
- Mark uncertainty with `%%VERIFY%%`.

**Calibration rules (peer-review status, HARD)**:

| canonical_status | Allowed prose patterns |
|---|---|
| `peer_reviewed_top` | "X shows that…", "Y establishes…", "Z demonstrates…" (definitive) |
| `peer_reviewed_other` | Same, but prefer "X reports…" for workshop work |
| `preprint` | "X reports…", "recent work argues…", "an arXiv preprint by Y suggests…" (always attributed; NEVER "establishes/proves") |
| `industry_report` | "Anthropic researchers report…", "the Distill thread on X argues…" (always name source org; NEVER "establishes/proves") |
| `informal` | Avoid as load-bearing. If used, attribute explicitly. |

A paragraph mixing reviewed + unreviewed evidence MUST distinguish them when unreviewed evidence is load-bearing.

**Evidence-strength rule**: do NOT use causal language for correlational evidence. "The model uses X" → "information about X is linearly decodable" when the only evidence is probing.

**Style**:
- PhD-level analytical prose; no filler ("it is worth noting", "interestingly", "furthermore" as sentence starters).
- Organise around claims, not papers. Core papers get 3-6 sentences (methodology, results, limitations); supporting get 1-2; peripheral get grouped cite.
- Each content section closes with a 1-3 sentence transition to the next section.
- Present tense for established findings; past tense for specific experiments.
- IEEE citation style.

### 7.4 `fact-checker` (Phase 7, single agent)

**Input**: all `output/sections/*.tex`, all `notes/*.json`, `papers/cite_keys.json`, `papers/works.json`, `output/traceability_report.json`.

**Process** for every `\cite{cite_key}`:
1. Resolve cite_key → work_id → notes_paper_id.
2. Read `notes/{notes_paper_id}.json`.
3. Read the `% src:` comment within 3 lines.
4. Identify the factual claim in the surrounding sentence.
5. Verify the claim against the named notes field.
6. Classify: PASS (directly supported), WARN (imprecise, weakly supported, wrong field-pointer, or calibration mismatch), FAIL (not supported / notes missing / cite_key unresolvable).

**Calibration checks (WARN, not FAIL)**:
- Status-language mismatch: definitive language on `preprint`/`industry_report`/`informal` → WARN `unattributed_unreviewed_source`.
- Causal overclaim: causal prose where `notes.evidence_strength == "correlational"` → WARN `causal_language_on_correlational_evidence`.
- Industry-only load-bearing: a paragraph's main argument rests on multiple `industry_report` cites with zero `peer_reviewed_*` → WARN `argument_load_borne_by_industry_only`.

**Structural checks**: unresolved `%%VERIFY%%`, cite_keys with no notes file, sections citing fewer than 3 cite_keys (under-cited), `depth_recommendation=core` works not cited (likely missing).

**Output**: `output/verification_report.md` with sections: FAIL items, WARN items, Causal-Overclaim items, Status-Language Mismatch, Argument-Load-Borne-By-Industry-Only, Unresolved %%VERIFY%% Markers, Uncited Core Works, Summary.

### 7.5 `critical-reviewer` (Phase 7b, single agent)

**Input**: all sections, all notes, `synthesis/`, `verification_report.md`, `logs/coverage_audit.md`, `must_have_papers.json`, `RESEARCH_CONTEXT.md`, `works.json` (for canonical_status of every cited work).

**Output**: `output/critical_review.md` with these sections:
- **A. Overclaims and weak causal inference** — causal language on correlational evidence, "all/every/always" from one paper, conflation of decodable vs causally used, conflation of linear-probe accuracy with "represents X". Quote the offending sentence, name the cited work AND its canonical_status, state the strongest claim notes actually support, propose a hedged rewrite.
- **B. Missing counterarguments and unaddressed limitations** — probing critiques, "interpretability illusions", evaluation debates, feature universality debates. Identify one-sided framings; propose where to insert counterargument.
- **C. Synthesis quality** — flag any paragraph reading as paper-by-paper list. Propose thematic reorganisation. Flag missed `cross_theme_bridges` from `themes.json` absent from prose.
- **D. Coverage and balance** — must-have works present in notes/ but not cited; sub-topics with thin treatment vs centrality; sections dominated by 1-2 papers.
- **E. Peer-review calibration (HIGH-PRIORITY)** — for each section list every load-bearing claim grounded SOLELY in non-peer-reviewed sources. Per item: name the works and their canonical_status, assess whether prose attributes the claim to the source organisation or presents it as fact, propose attribution rewrite / add peer-reviewed companion / explicit acknowledgement of unrefereed evidence with proposal-validation hook.
- **F. Proposal rigor (Task 2)** — critically assess proposal section against: contributions distinct/testable/non-trivial? Each measurement has stated baseline + success threshold + defensible reason it answers the question? Stages genuinely staged? Tools justified by literature vs boilerplate? Evidence chain established? Foundational methods cite ≥ 1 peer-reviewed source?
- **G. Academic writing defects** — filler, hedging without substance, repeated sentence structures, paragraphs without topic sentences, disconnected section openings, inconsistent tense, IEEE conventions. 3-5 examples per pattern with section:line.
- **H. Intellectual coherence** — intro roadmap matches body? Gap section motivates proposal? Proposal evaluates the gap claim?
- **I. Top 10 highest-priority revisions** — ranked list.
- **Summary verdict** — 1-3 sentences.

**Rules**: cite specific lines and quote specific text — no generic critique. If a section is fine, say so. Don't propose new citations the writer doesn't have notes for. Distinguish "the cited paper doesn't support this" (fact-check territory; defer) from "the rhetorical framing overclaims" (your territory). Hold the proposal to a high bar.

---

## 8. CLAUDE.md — what the orchestrator (Claude Code) sees

`CLAUDE.md` is the master instruction document for the agent driving the pipeline. It contains:
1. Project overview (1 paragraph).
2. Assignment instructions + marking criteria, verbatim.
3. Phase definitions (Phases 0-3, 4a, 4, 4b, 5, 6, 6b, 7, 7b) with exact script commands and dependencies.
4. **Writer-section table** (the per-topic deliverable: section file → target word count → sub-topics covered → focus).
5. Subagent routing rules: "Phase 4 (paper-readers)" and "Phase 6 (writers)" are independent delegation candidates (run in parallel). Phase 5 / 7 / 7b are sequential singletons. Human checkpoints after Phase 3, 4b, 5, 7b.
6. **Critical constraints** (the 11 rules — re-iterate the identity model, synthetic-ID minting policy, status calibration, causal-vs-correlational discipline, "no agent asserts a fact without notes in context", traceability requirement, IEEE style, absolute peer-reviewed gate).

When porting to a new topic, only the writer-section table and the marking criteria text change.

---

## 9. Human Checkpoints (do not skip)

| After phase | What to review | What to fix |
|---|---|---|
| Phase 0 | `logs/seed_resolution.json` | Any seed with `semantic_scholar_id: null` — manually fix the seed entry |
| Phase 3b | `logs/retrieval_failures.json`, `retrieval_sources.json`, `parse_quality.json`, metadata sanity | Manually place PDFs that failed every source at `papers/pdfs/{paper_id}.pdf`; re-run parse |
| Phase 4a | `logs/version_linkage.json` flagged pairs | Confirm or split ambiguous title-only merges |
| Phase 4b | `logs/coverage_audit.md` | Add seeds for missing must-have papers; re-run earlier phases; manually drop in critical PDFs |
| Phase 5 | `synthesis/themes.json` + re-run coverage audit | Add papers if sub-topics are under-mapped; ask synthesizer to re-cluster |
| Phase 6b | `output/traceability_report.md` | Structural FAILs must be 0; calibration WARNs reviewed and either fixed or accepted |
| Phase 7 | `output/verification_report.md` | All semantic FAILs fixed |
| Phase 7b | `output/critical_review.md` | Top-10 priority revisions addressed; re-run fact-check on rewrites |

---

## 10. Worked example of the traceability contract

Section file `02_mech_interp_foundations.tex`:

```latex
\subsection{Mechanistic Interpretability Foundations}

Induction heads emerge during training and explain a substantial portion of in-context learning improvement \cite{olsson2022_induction_heads}.
% src: c90a99eeb57019732a6cc996bb9eaf13faedf00f pp.4 (key_results) — "induction heads form sharply during a single phase change"
Anthropic's Transformer Circuits Thread reports that toy models can recover monosemantic features via sparse autoencoders \cite{bricken2023_towards_monosemanticity}.
% src: ext_anthropic_2023_towards_monosemanticity pp.12 (main_claims) — "SAEs decompose superposed activations into monosemantic features"
```

What checks pass / fail here:

- `07_traceability_check.py` resolves `olsson2022_induction_heads` via `cite_keys.json` → work_id → notes_paper_id `c90a99e…`. The `% src:` comment is within 3 lines, references a supported field (`key_results`) and a page (`pp.4`). PASS.
- The Anthropic cite resolves to an `ext_anthropic_*` paper_id; `works.json[work_id].canonical_status == "industry_report"`. The sentence uses attributed language ("Anthropic's Transformer Circuits Thread reports") — no definitive verb. PASS calibration check.
- If the sentence read "Bricken et al.\ \emph{establish} that SAEs recover monosemantic features \cite{bricken2023_towards_monosemanticity}", the calibration check fires WARN `definitive_verb_on_unreviewed_source`.
- The LLM fact-checker then opens `notes/ext_anthropic_2023_towards_monosemanticity.json`, finds `main_claims` includes the SAE-decomposition claim, and PASSes the semantic check.

---

## 11. Porting checklist (to a new topic)

When rebuilding for a different field, replace:

1. **`RESEARCH_CONTEXT.md`** — new RQ, new 4-8 sub-topics, new sub-topic→section table.
2. **`seed_papers.json`** — 30-50 seed papers from your field. Add subtopic IDs matching `RESEARCH_CONTEXT.md`.
3. **`must_have_papers.json`** — your field's canonical works + sub-topic keyword phrases (multi-word, ≥ 2 distinct hits required).
4. **`curated_external.json`** — only if your field has important non-S2 sources (industry reports, technical blogs). For most academic fields this is empty/short.
5. **`venues.json`** — add field-specific venues to `exact_top` / `exact_other` / `contains_*`.
6. **`CLAUDE.md` writer table** — adjust the section list (1 section per content sub-topic + intro + gaps + proposal).
7. **`scripts/01_search.py:SEARCH_QUERIES`** — replace the 40-60 keyword queries with your field's vocabulary.
8. **`scripts/01b_openreview_pull.py:TOPIC_TERMS`** and venue list — narrow to your field's OpenReview venues.
9. **`scripts/02_snowball.py`** — adjust `RECENT_WINDOW_YEARS` and backward-citation floor if your field's foundational papers are older than 2010.
10. **`output/{main}.tex`** — change title, student ID, `\input{}` list to match your section files.

Everything else (the identity model, the gating scripts, the subagents, the calibration discipline) is field-agnostic and ports as-is.

---

## 12. Critical "don't break this" rules — quick reference

1. **Three-level identity**: cite_key → work_id → paper_id. Resolve via `papers/cite_keys.json`. Never put paper_id in `\cite{}`. Never invent multiple cite_keys for the same work.
2. **Synthetic IDs**: `ext_*` minted ONLY by `01b_openreview_pull.py` and `01c_curated_pull.py`. Every other script treats them as opaque IDs.
3. **Calibration discipline**: definitive verbs only on `peer_reviewed_*`; attribution on `preprint`/`industry_report`/`informal`.
4. **Causal-vs-correlational**: causal prose on `evidence_strength=correlational` notes is WARN.
5. **No agent asserts a fact about a work without that work's canonical notes in its context window.** Missing notes → flag, never fabricate.
6. **Traceability comments are mandatory**: every `\cite{}` followed within 3 lines by `% src: <paper_id> pp.<page> (<notes_field>) — "<quote>"`. Enforced by `07_traceability_check.py` (exit 2 on fail).
7. **`%%VERIFY%%`** marks any sentence the writer is unsure of. Must be resolved before fact-check.
8. **IEEE citation style** via `\bibliographystyle{IEEEtran}`.
9. **Seeds and curated entries are pre-verified** with title-cosine + first-author + year. Never resolve by top-1 title search alone.
10. **Coverage audit gates are absolute, not ratios**: ≥ 25 cited peer-reviewed works in the final draft; per-section peer-reviewed anchors; each proposal method cites ≥ 1 peer-reviewed work.
11. **Industry-heavy fields**: if `industry_report` is structurally over-represented (e.g. mech-interp, AI alignment), the writer must EXPLICITLY note this in the relevant section and pair industry citations with peer-reviewed replications wherever possible. The proposal's evaluation plan should treat "provide peer-reviewed validation of an industry result" as a contribution rather than an apology.
