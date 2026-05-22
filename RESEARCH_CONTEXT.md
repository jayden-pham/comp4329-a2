# Research Context (Stage 0 — Research Contract)

This document is the locked target for the project. Subsequent stages refine *how* we test the hypothesis; they do not redirect the question.

## Research Question

Does Sharpness-Aware Minimization (SAM) improve out-of-distribution (OOD) generalization mainly by reducing loss sharpness, or by producing representations that remain more stable under input corruptions?

## Hypothesis (directional, hedged)

SAM's OOD gains are only partly explained by lower sharpness. Compared with SGD and a flat-minima-oriented control (SWA), SAM produces greater clean-to-corrupted representation stability, and this stability tracks OOD accuracy more closely than sharpness alone.

The hypothesis is falsifiable: if SWA matches SAM on OOD accuracy **and** on representation stability while both are similarly flatter than SGD, the representation-specific hypothesis is not supported. This is a publishable negative result (assignment §2.2).

## Contribution

A controlled empirical study separating sharpness-associated and representation-stability-associated explanations of SAM's OOD generalization, using SGD, SAM, and SWA under matched training protocols on CIFAR-C benchmarks. The novel comparison is including SWA as a **flat-minima-oriented control** alongside SAM in the OOD setting — this lets us decompose flatness from optimization-trajectory effects rather than treating SAM in isolation.

SWA is deliberately not called "flatness-only" — it changes the optimization trajectory via late-epoch weight averaging and may carry ensemble-like effects beyond flatness. The cleaner framing is: SAM and SWA are two distinct flatness-oriented optimizers, and we compare which one's geometric and representational signature better tracks OOD accuracy.

## Minimum Viable Experiment

- **Model**: ResNet-18 (single capacity)
- **Optimizers**: SGD (baseline), SAM (ρ=0.05, Foret et al. default for ResNet+CIFAR), SWA (flat-minima-oriented control)
- **Datasets**: CIFAR-10, CIFAR-100 (ID); CIFAR-10-C, CIFAR-100-C (OOD)
- **Seeds**: 3 per cell → **18 runs total**
- **Training budget**: equal epochs across optimizers. SAM consumes ~2× gradient compute per step; this is disclosed in Method.
- **Primary metric**: severity-averaged CIFAR-C accuracy (15 corruption types × 5 severities)
- **Secondary metrics**:
  - ID accuracy on clean test set
  - Expected Calibration Error (ECE) on ID and OOD
  - Sharpness: top eigenvalue of Hessian via power iteration **and** SAM-style neighborhood loss
  - Paired-image CKA stability at penultimate layer: CKA(ϕ(x), ϕ(corrupt(x))), averaged across corruption types and severities

## Analysis Plan

- Optimizer-level comparison of OOD gain, sharpness, and paired-CKA stability with error bars across seeds.
- Scatter plots: (sharpness, OOD gain) and (CKA stability, OOD gain) across all runs.
- Partial correlation: does CKA stability track OOD gain after accounting for sharpness?
- Framed as **exploratory associational evidence**, not confirmatory causal mediation. The N is too small for formal mediation inference; we are honest about that.

## Ablation (if compute permits, single seed)

ρ ∈ {0.02, 0.1} on CIFAR-100 only → 2 additional runs. Skipped if main grid runs over budget.

## Compute Budget

~15 h GPU for main grid + ~2 h ablation = **~17 h** across RTX 3070 (overnight) and Colab Pro (parallel). Deadline: 4 days from project start (target submission ~2026-05-24).

## Sub-topics for Literature Review

1. **sam_origin** — SAM formulation, theory, and variants
2. **sam_mechanism** — critical analyses of *why* SAM works; counter-evidence for the flatness explanation
3. **flatness_theory** — link between flatness and generalisation, including Dinh's counter-argument
4. **ood_benchmarks** — CIFAR-C / ImageNet-C / DomainBed; calibration under shift
5. **flat_minima_for_dg** — flatness-seeking optimisers (SWA, SWAD, SAM variants) applied to domain generalisation
6. **representation_analysis** — CKA, SVCCA, paired-image representation comparison
7. **weight_averaging** — SWA and related methods as flat-minima-oriented baselines

## Sub-topic ↔ Section Mapping

| Sub-topic                | Primary section file               |
|--------------------------|------------------------------------|
| sam_origin               | `sec/02_related_work.tex`          |
| sam_mechanism            | `sec/02_related_work.tex`          |
| flatness_theory          | `sec/02_related_work.tex`          |
| ood_benchmarks           | `sec/02_related_work.tex`          |
| flat_minima_for_dg       | `sec/02_related_work.tex`          |
| representation_analysis  | `sec/03_method.tex` + `sec/02_related_work.tex` |
| weight_averaging         | `sec/02_related_work.tex` + `sec/03_method.tex` |

All literature content lands in Related Work (sec/02). Method (sec/03) re-cites methodological prior work (CKA, sharpness measures, SWA) inline.

## Assignment Constraints (extracted from assignment_2.md)

- **Length**: main body ≤ 8 pages in DLCC two-column format. Appendix permitted (does not count) but reviewers may not read it. Recommended 6–8 pages.
- **Format**: DLCC LaTeX template (already in `output/`). IEEE bibliography style.
- **Submission**: OpenReview, PDF, double-blind. **No author info anywhere** in the submission PDF.
- **Required sections**: abstract, introduction, related work, method, experiments+results, conclusion, references.
- **Grading axes (90 pts)**: novelty, soundness, clarity, positioning, formatting compliance.

## Zero-Hallucination Constraints

1. Every `\cite{}` references a `cite_key` from `papers/cite_keys.json`; raw paper_ids never appear in citations.
2. Every `\cite{}` is followed within 3 lines by a `% src:` comment naming the notes file and field that supports the surrounding claim.
3. Every quantitative claim in Method / Experiments / Analysis references a row in `results/runs.jsonl` or a figure/table file under `results/`.
4. Agents write `null` for fields they cannot determine; they never invent.
5. Calibration: definitive verbs ("establishes", "demonstrates", "proves") are reserved for peer-reviewed sources. Preprint claims are attributed ("X et al. report").

## Status of this document

Locked unless the user explicitly requests an update. Agents may **read** but never silently overwrite this file.
