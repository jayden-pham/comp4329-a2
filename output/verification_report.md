# Verification Report — `output/sec/02_related_work.tex` (revision pass)

Section audited: Related Work (single section, 24 `\cite{}` invocations including new `schneider2020_improving_robustness`, 0 `%%VERIFY%%` markers).
Reference inputs: `notes/*.json`, `papers/cite_keys.json`, `output/traceability_report.json`.
Auditor: fact-checker subagent (second pass — re-verifying revised draft).

This pass confirms resolution of the four prior WARNs (5, 6, 7, 8), audits the three remaining traceability definitive-verb flags (lines 31, 63, 65), and looks for new issues introduced by the revisions (new Schneider cite at line 49; rewritten Schapiro/Wen passage at lines 33/39; rewritten Zhuang/GSAM line 9).

---

## FAILs

*None.* Every `\cite{}` resolves to a `paper_id` in `papers/cite_keys.json` with a present `notes/{paper_id}.json` file, and every cited claim has direct support in the named notes field.

---

## WARNs — Causal-Overclaim

*None.* All correlational citations (`keskar2016`, `jiang2019`, `ovadia2019`, `walter2025`) continue to use appropriately hedged language ("co-occurring", "associated", "does not transfer", "complementary limit"). The Jiang sentence still explicitly notes "the correlation is not causal" (line 21).

---

## WARNs — Status-Language Mismatch

The four traceability definitive-verb flags from `traceability_report.json` are audited below.

### Prior WARN 5 (line 33, wen2022_how_does) — RESOLVED → PASS-with-note

- **File**: `output/sec/02_related_work.tex:33`
- **Revised sentence**: "In a recent arXiv preprint, Wen et al.\ prove that full-batch SAM tracks Riemannian gradient flow on $\lambda_{\max}$ of the Hessian, while batch-size-1 SAM minimises an average-direction sharpness proportional to the Hessian trace, leaving practical mini-batch SAM characterised by neither limit."
- **Cited**: `\cite{wen2022_how_does}` (paper_id `07dbbb95…`, venue: arXiv.org, preprint v2)
- **Notes field**: `key_results[0]` (Theorem 4.5) and `key_results[1]` (Theorem 5.4)
- **Reason**: The revision explicitly prefixes the sentence with "In a recent arXiv preprint", satisfying the calibration rule's "make the preprint status explicit OR hedge the inner verbs" requirement. The definitive verb "prove" is now factually defensible because (a) the cited results are formal theorems with proofs in the paper, and (b) the preprint status is foregrounded for the reader. The traceability heuristic still flags this line, but the status disclaimer resolves the calibration concern.
- **Classification**: **PASS** (resolution of prior WARN 5 confirmed).

### Prior WARN 6 (line 9, zhuang2022_surrogate_gap) — RESOLVED → PASS

- **File**: `output/sec/02_related_work.tex:9`
- **Revised sentence**: "GSAM augments the objective with a surrogate gap that, for small $\rho$ near a local minimum, is approximately proportional to the dominant Hessian eigenvalue ($\sigma_{\max}\!\approx\!2h(w^*)/\rho^2$, Lemma~3.3), since low perturbed loss can coexist with sharp curvature."
- **Cited**: `\cite{zhuang2022_surrogate_gap}` (paper_id `58ab7d67…`, ICLR 2022, `evidence_strength: mixed`)
- **Notes field**: `key_results[1]` ("Lemma 3.3 proves sigma_max ≈ 2h(w*)/rho^2") and `key_quotes[1]` ("σmax ≈ 2h(w∗)/ρ2")
- **Reason**: The prior overstatement "shown to equal" has been replaced with "approximately proportional", the small-$\rho$ regime is now made explicit, the exact formula is shown, and Lemma 3.3 is cited. This matches the notes verbatim.
- **Classification**: **PASS** (resolution of prior WARN 6 confirmed).

### Line 31 (andriushchenko2022_towards_understanding) — PASS

- **File**: `output/sec/02_related_work.tex:31`
- **Sentence**: "Andriushchenko and Flammarion show the PAC-Bayes flat-minima account is incomplete: only m-SAM with small batch ($m=128$) substantially improves test error on ResNet-18/CIFAR-10, whereas n-SAM and random perturbations do not, and for diagonal linear networks SAM provably selects sparser solutions than GD."
- **Cited**: `\cite{andriushchenko2022_towards_understanding}` (paper_id `b698dbfa…`, **ICML 2022**)
- **Notes field**: `main_claims[0]`, `key_results[0]`, `key_results[1]`
- **Reason**: ICML 2022 is peer-reviewed top. "Provably selects sparser solutions" is supported by `key_results[1]`: "For diagonal linear networks, SAM provably selects solutions with smaller L1 norm (sparser) than gradient descent". Definitive verb is appropriate.
- **Classification**: **PASS** (traceability heuristic flag resolved).

### Line 63 (kornblith2019_similarity_neural) — PASS

- **File**: `output/sec/02_related_work.tex:63`
- **Sentence**: "Kornblith et al.\ establish linear Centred Kernel Alignment as the standard representation-similarity tool, identifying corresponding layers across networks at $99.3\%$ accuracy versus $10.6\%$ for CCA and $15.1\%$ for SVCCA."
- **Cited**: `\cite{kornblith2019_similarity_neural}` (paper_id `726320cd…`, **ICML 2019**)
- **Notes field**: `key_results[0]` (99.3% / 10.6% / 9.9–15.1%)
- **Reason**: ICML 2019 is peer-reviewed top. Numbers match exactly. CKA is widely adopted as a standard tool (also used by `zhang2023`). Definitive verb is appropriate.
- **Classification**: **PASS** (traceability heuristic flag resolved).

### Line 65 (izmailov2018_averaging_weights) — PASS

- **File**: `output/sec/02_related_work.tex:65`
- **Sentence**: "Izmailov et al.\ establish the SWA baseline used here as a non-perturbation flat-minima control: averaging late SGD iterates with cyclical learning rates centres the trajectory in a wider basin of the same landscape, improving WRN-28-10/CIFAR-100 from $80.82\%$ to $82.15\%$."
- **Cited**: `\cite{izmailov2018_averaging_weights}` (paper_id `b8989aff…`, **UAI 2018**)
- **Notes field**: `key_results[0]` (80.82% → 81.46–82.15%) and `key_quotes[2]` ("SWA is not finding a different minima than SGD, but rather a flatter region in the same basin of attraction")
- **Reason**: UAI is peer-reviewed top. Numerical claim 80.82 → 82.15 matches. "Same basin" / "wider basin of the same landscape" matches `key_quotes[2]`. Definitive verb is appropriate.
- **Classification**: **PASS** (traceability heuristic flag resolved).

---

## WARNs — Argument Load-Borne by Unreviewed Sources

The "SAM's Mechanism Is Not Just Flatness" subsection (lines 29–41) still cites two arXiv preprints (`wen2022_how_does`, `schapiro2024_towards_understanding`), but the central argument is anchored by three peer-reviewed top-venue works (`andriushchenko2022` ICML, `mueller2023` NeurIPS, `baek2024` ICLR). The peer-reviewed anchor remains in place, and the revision improved the preprint framing (status flag for Wen; credit redirection for Schapiro).

*No paragraph violates this calibration check.*

---

## WARNs — Quantitative Claim Mismatch

Numerical citations re-checked against notes after revision:

| Line | Numbers in prose | Notes field | Match? |
|------|-----------------|-------------|--------|
| 7 | 0.174, 0.636 (Kendall τ) | kwon2021 `key_results[0]` | exact |
| 9 | $\sigma_{\max}\!\approx\!2h(w^*)/\rho^2$, Lemma 3.3 | zhuang2022 `key_results[1]` | exact |
| 17 | "up to a five-point gap", "six configurations" | keskar2016 | exact |
| 21 | "40 alternative", "$10^4$ networks" | jiang2019 | exact |
| 31 | $m=128$ | andriushchenko2022 | exact |
| 35 | 84.19%, 83.11%, 0.090, 0.048 | mueller2023 | exact |
| 37 | 69.17%, 69.47%, 54.13%, 30% noise | baek2024 | exact (now both SAM 69.47% and J-SAM 69.17% shown) |
| 39 | 4.76%, 8.01% | schapiro2024 | exact |
| 45 | "15 corruption types at 5 severity levels" | hendrycks2019 | exact |
| 49 | 76.7%, 62.2% mCE | schneider2020 `key_results[0]` | exact |
| 51 | 63.3% → 66.9% | cha2021 | exact |
| 55 | 66.1% | wang2023 | exact |
| 57 | $\lambda_{\max}=237$ (SAM), $265$ (SWA) | kaddour2022 | exact |
| 63 | 99.3%, 10.6%, 15.1% | kornblith2019 | exact |
| 65 | 80.82% → 82.15% | izmailov2018 | exact |
| 67 | 0.7882, 0.9822 (CKA) | zhang2023 | exact |

Prior WARN 7 (J-SAM/SAM number ambiguity, line 37) and prior WARN 8 (Schapiro quote misattribution, line 39) are now resolved (see notes below). No new quantitative mismatches were introduced.

### Prior WARN 7 (line 37, baek2024_why_is) — RESOLVED → PASS

- **Revised sentence**: "Baek et al.\ attribute SAM's label-noise robustness to perturbation of the network Jacobian, not flatness at convergence: J-SAM reaches $69.17\%$ under 30\% label noise, matching SAM's $69.47\%$, while logit-only perturbation degrades to $54.13\%$."
- **Reason**: Both SAM's 69.47% and J-SAM's 69.17% are now explicitly reported, and J-SAM is clearly attributed as the holder of 69.17%. The numerical ambiguity is gone. Matches `key_results[0]` exactly.
- **Classification**: **PASS** (resolution of prior WARN 7 confirmed).

### Prior WARN 8 (line 39, schapiro2024_towards_understanding) — RESOLVED → PASS

- **Revised sentence**: "An arXiv preprint by Schapiro and Zhao reports SAM and FriendlySAM gains of $4.76\%$ and $8.01\%$ over Adam on four small-scale zero-shot OOD benchmarks (rotated/coloured MNIST, Cover Type, Portraits), not CIFAR-C, echoing Wen et al.'s observation that low sharpness alone does not fully account for SAM's gains."
- **Reason**: The prior misattribution ("Schapiro and Zhao explicitly noting") is replaced with the correct attribution ("echoing Wen et al.'s observation"), directly matching `schapiro2024.key_quotes[1]` ("as noted in Wen et al. (2023), which found that low sharpness alone does not account for all of SAM's generalization benefits"). The preprint status is also flagged in-line ("An arXiv preprint by"), and the benchmark calibration ("four small-scale … not CIFAR-C") matches `limitations[0]` ("not evaluated on CIFAR-C or ImageNet-C"). The 4.76%/8.01% figures match `key_results[0,1]` exactly.
- **Classification**: **PASS** (resolution of prior WARN 8 confirmed).

---

## WARNs — Newly Introduced by the Revision

### WARN 1 (NEW): Line 49 — minor writer-inferred causal extension on Schneider cite

- **File**: `output/sec/02_related_work.tex:49`
- **Sentence**: "Schneider et al.\ show that re-estimating BatchNorm statistics on corrupted test images lifts vanilla ResNet-50 from $76.7\%$ to $62.2\%$ mCE on ImageNet-C, a confound for any optimiser-level CIFAR-C comparison since SAM and SWA touch BN behaviour differently."
- **Cited**: `\cite{schneider2020_improving_robustness}` (paper_id `aa12f44…`, **NeurIPS 2020**, `evidence_strength: demonstrative`)
- **Notes field**: `key_results[0]` ("Vanilla ResNet-50 improves from 76.7% mCE to 62.2% mCE with full adaptation (n=50,000) on ImageNet-C")
- **Reason**: The Schneider portion of the sentence ("re-estimating BatchNorm statistics … lifts vanilla ResNet-50 from 76.7% to 62.2% mCE on ImageNet-C") matches the notes verbatim and uses an appropriate definitive verb for a peer-reviewed demonstrative result. However, two minor concerns:
  1. **Stylistic**: "lifts … from 76.7% to 62.2% mCE" is mildly awkward because mCE is an *error* metric — a reduction from 76.7 to 62.2 is an improvement, but "lifts" connotes increase. The numbers are correct; the verb is borderline. Not WARN-worthy on its own.
  2. **Writer-inferred extension**: The trailing clause "a confound for any optimiser-level CIFAR-C comparison since SAM and SWA touch BN behaviour differently" is the writer's analytical extension, not asserted by Schneider et al. The Schneider notes establish that BN-statistic adaptation matters for OOD; they do *not* say SAM and SWA differ in BN handling. The SAM/SWA-BN-difference claim is widely understood (SWA typically recomputes BN running stats after weight averaging), but no cite is provided to back the "SAM and SWA touch BN behaviour differently" assertion.
- **Classification**: **WARN — uncited inference attached to a cited result** (borderline; would PASS with a follow-up cite for the SAM/SWA BN-handling claim, e.g., Izmailov's BN-update procedure for SWA).
- **Suggested fix**: Add a cite for the SAM/SWA BN-handling asymmetry (the Izmailov 2018 paper already cited at line 65 discusses SWA's BN recomputation in §3.3) — e.g., `... since SAM and SWA interact with BN statistics differently \cite{izmailov2018_averaging_weights}`. Optionally change "lifts" → "reduces" or "improves" for metric-direction clarity.

---

## WARNs — Unresolved `%%VERIFY%%` Markers

`grep` confirms **0** `%%VERIFY%%` markers in `output/sec/02_related_work.tex`.

---

## Uncited Core Works

Re-checked the `depth_recommendation: core` set against the 24 cites in the revised section. All distinct core works remain cited; the new `schneider2020_improving_robustness` citation (`supporting` depth) adds anchoring for the OOD-benchmarks subsection. No newly-uncited core works.

---

## Summary

| Category | Count |
|---|---|
| FAILs | **0** |
| WARNs — Causal-Overclaim | **0** |
| WARNs — Status-Language Mismatch | **0** (4 traceability flags audited — all resolved to PASS) |
| WARNs — Argument Load-Borne by Unreviewed Sources | **0** |
| WARNs — Quantitative Claim Mismatch | **0** |
| WARNs — Newly Introduced by the Revision | **1** (line 49 Schneider — uncited SAM/SWA-BN inference) |
| WARNs — Unresolved `%%VERIFY%%` | **0** |
| Uncited Core Works | **0** |
| **Total actionable WARNs** | **1** |

### Resolution status of the four prior WARNs

| Prior WARN | Line | Topic | Status this pass |
|---|---|---|---|
| WARN 5 | 33 | wen2022 — definitive verbs on preprint | **RESOLVED** (explicit "In a recent arXiv preprint" status disclosure) |
| WARN 6 | 9 | zhuang2022 — "shown to equal" overstated Lemma 3.3 | **RESOLVED** ("approximately proportional", small-$\rho$ scope, exact formula and Lemma cited) |
| WARN 7 | 37 | baek2024 — 69.17%/69.47% number attribution | **RESOLVED** (both numbers now shown, J-SAM correctly holds 69.17%) |
| WARN 8 | 39 | schapiro2024 — quote misattribution | **RESOLVED** (credit redirected to Wen et al., preprint status flagged) |

### Calibration heuristic WARNs from traceability — disposition

| Line | Cite | Definitive verb | Venue | Disposition |
|---|---|---|---|---|
| 31 | andriushchenko2022 | "show … provably" | ICML 2022 | **PASS** — peer-reviewed top; "provably" backed by formal proof for diagonal linear networks |
| 33 | wen2022 | "prove" | arXiv preprint | **PASS** — preprint status now explicit in the sentence; results are formal theorems |
| 63 | kornblith2019 | "establish" | ICML 2019 | **PASS** — peer-reviewed top; CKA is the de-facto standard |
| 65 | izmailov2018 | "establish" | UAI 2018 | **PASS** — peer-reviewed top per fact-checker.md venue list |

### Top concern carried forward

**WARN 1 (line 49)** — the Schneider citation itself is well-supported, but the trailing clause "SAM and SWA touch BN behaviour differently" is an uncited writer assertion bolted onto the Schneider result. Adding a back-cite to Izmailov 2018 (already in the bibliography) for SWA's BN recomputation procedure would close this gap with a one-token edit.
