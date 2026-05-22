# CLAUDE.md — Orchestrator Instructions

This file is loaded into Claude Code on every session in this repo. It defines the pipeline stages, which agents to invoke, and the constraints that must hold across all work.

## Project

A research paper for COMP4329 / COMP5329 Assignment 2. The full assignment brief is in `assignment_2.md`; the locked research contract is in `RESEARCH_CONTEXT.md`. Read both before doing anything.

**Submission target**: 6–8 page DLCC-template paper on OpenReview, double-blind. Deadline ~4 days from project start.

## Pipeline stages

The pipeline runs in seven stages. Most stages have a clear "checkpoint" where the user reviews artefacts before the next stage runs.

### Stage 0 — Research Contract (DONE at repo init)
Locked in `RESEARCH_CONTEXT.md`. Never modified by agents.

### Stage A — Literature pipeline
User runs each script manually; Claude orchestrates the subagents. Scripts read `S2_API_KEY` from either the shell environment or a repo-root `.env` file:

```
S2_API_KEY=your_semantic_scholar_key_here
```

```
python scripts/00_seed_resolve.py     # verify seed S2 IDs
python scripts/01_search.py           # targeted S2 keyword queries
python scripts/02_snowball.py         # one round, capped at ~40 papers total
python scripts/03_retrieve.py         # download PDFs
python scripts/04_parse.py            # PyMuPDF text + page markers
# Checkpoint A1: review logs/retrieval_failures.json, logs/parse_quality.json
# Then Claude fans out paper-reader subagents in parallel (one per parsed paper)
python scripts/05_build_bib.py        # cite_keys.json + output/main.bib
# Checkpoint A2: spot-check 3 random notes/*.json against PDFs
# Then Claude invokes synthesizer once
# Checkpoint A3: read synthesis/themes.json and synthesis/gaps.md
```

### Stage B — Related Work + Positioning Brief
Claude invokes `writer` subagent for `sec/02_related_work.tex` with a section brief in `briefs/02_related_work.md`. Then:

```
python scripts/05_build_bib.py        # re-run after any writer pass
python scripts/06_traceability_check.py   # structural FAIL gate
```

Claude then invokes `fact-checker` → `critical-reviewer` → revision pass via `writer`. The Positioning Brief (`briefs/positioning.md`) is written by Claude after the synthesizer runs and before the writer; it states the paper's claimed contribution relative to prior work.

Intro is **NOT** written here — it is deferred to Stage F.

### Stage D0 — Feasibility spike
Claude writes minimum-viable `scripts/train.py`, `scripts/eval_ood.py`, `scripts/sharpness.py`, `scripts/cka.py`, `scripts/aggregate.py`. User runs ONE config end-to-end (SGD on CIFAR-10, ResNet-18, 1 seed) and produces one row in `results/runs.jsonl`. Outputs `logs/spike_report.md` with wall-clock, memory, and metric sanity-check info.

### Stage C — Experiment plan
Claude invokes `experiment-designer` subagent. Input: synthesis, positioning brief, spike report. Output: `EXPERIMENT_PLAN.md` with the final grid, configs, expected runtime, and pre-registered predictions. User approves before Stage D.

### Stage D — Finalise experiment infrastructure
Based on `EXPERIMENT_PLAN.md`, Claude finalises scripts and generates all `configs/*.yaml`.

### Stage E — Run experiments
User runs jobs across RTX 3070 + Colab Pro. Each job writes a row to `results/runs.jsonl`.

### Stage F — Write result-driven sections
Claude invokes `writer` for `sec/03_method.tex`, `sec/04_experiments.tex`, `sec/05_analysis.tex`, `sec/06_conclusion.tex` — each with its own `briefs/{section}.md`. Then `sec/01_introduction.tex` is written **last** (intro depends on the final contribution). The abstract is updated last.

After each `writer` pass:
```
python scripts/05_build_bib.py
python scripts/06_traceability_check.py
python scripts/07_format_check.py
```

Then `fact-checker` (extended to also verify quantitative claims against `results/runs.jsonl`) and `critical-reviewer` over the full paper.

### Stage G — Final gates
- `python scripts/07_format_check.py` — page count, anonymization, figure refs, latexmk compile
- Page-budget allocation review (compare section lengths vs target)
- Manual re-read by user

## Subagent routing

| Agent | When invoked | Parallel-safe | Input | Output |
|---|---|---|---|---|
| `paper-reader` | Stage A, after parse | Yes (one per paper) | parsed .txt | `notes/{paper_id}.json` |
| `synthesizer` | Stage A, after all notes | No (singleton) | all notes | `synthesis/themes.json`, `synthesis/gaps.md` |
| `experiment-designer` | Stage C | No (singleton) | synthesis + spike report | `EXPERIMENT_PLAN.md` |
| `writer` | Stages B, F | One section at a time | `briefs/{section}.md` + relevant notes | `output/sec/{section}.tex` |
| `fact-checker` | After every writer pass | No (singleton) | section files, notes, runs.jsonl | `output/verification_report.md` |
| `critical-reviewer` | After fact-check | No (singleton) | whole paper draft | `output/critical_review.md` |

## Critical constraints (the "don't break this" list)

1. **`RESEARCH_CONTEXT.md` is locked.** Read; do not modify unless user explicitly says so.
2. **Three-level identity**: `cite_key` (what writers put in `\cite{}`) → `paper_id` (S2 hex or `ext_*`). The map is `papers/cite_keys.json`. Never put a paper_id in `\cite{}`. Never invent cite_keys.
3. **Traceability comments are mandatory**: every `\cite{cite_key}` is followed within 3 lines by `% src: <paper_id> pp.<page> (<notes_field>) — "<≤20-word evidence>"`. Enforced by `scripts/06_traceability_check.py` (exit 2 on FAIL).
4. **Calibration**: definitive verbs reserved for peer-reviewed sources; preprints get attributed verbs ("X et al. report"). The `fact-checker` agent WARNs on mismatches.
5. **Causal vs correlational**: if a notes file says `evidence_strength: correlational`, the writer must not use causal language ("the model uses X"). Use the field-appropriate phrasing.
6. **No quantitative claim without `results/runs.jsonl`**: every numeric value in Method/Experiments/Analysis must trace to a row in `runs.jsonl` or a file under `results/`.
7. **No claim about a paper without that paper's notes file in agent context**. Missing notes → flag, never fabricate.
8. **Double-blind**: no author names, affiliations, acknowledgments, or self-citations as "we previously showed" anywhere in the submission. Enforced by `scripts/07_format_check.py`.
9. **IEEE citation style** via the DLCC template's `bibliographystyle{style/ieee}`. Already configured in `output/main.tex`.
10. **`%%VERIFY%%`** marks any line the writer is unsure of. Must be resolved by the fact-checker pass before submission.
11. **Agents write `null` for fields they cannot determine**. They never guess.

## Section files

`output/main.tex` currently inputs `sec/00_abstract.tex`, `sec/01_introduction.tex`, `sec/02_formattingyourpaper.tex`. At the start of Stage B we replace `02_formattingyourpaper` with the real section list:

```latex
\input{sec/00_abstract}
\input{sec/01_introduction}
\input{sec/02_related_work}
\input{sec/03_method}
\input{sec/04_experiments}
\input{sec/05_analysis}
\input{sec/06_conclusion}
```

The template stub `sec/02_formattingyourpaper.tex` is deleted once `sec/02_related_work.tex` exists.

## Human checkpoints (do not skip)

- **After Stage A**: read `synthesis/themes.json` and `synthesis/gaps.md` end-to-end (≈ 20 min)
- **After Stage B**: read `sec/02_related_work.tex` and `briefs/positioning.md` (≈ 20 min)
- **After Stage D0**: read `logs/spike_report.md` — confirm wall-clock fits the budget (≈ 10 min)
- **After Stage C**: read `EXPERIMENT_PLAN.md`, approve grid (≈ 20 min)
- **After Stage F**: read full paper draft (≈ 30 min)
- **After Stage G**: read compiled PDF (≈ 30 min)
