# EXPERIMENT_PLAN.md (Stage C — locked grid + configs + analysis plan)

Status: locked pending user approval. After approval, no methodological choices change in Stage D/E/F.

---

## 1. Hypothesis

Verbatim from `RESEARCH_CONTEXT.md`:

> SAM's OOD gains are only partly explained by lower sharpness. Compared with SGD and a flat-minima-oriented control (SWA), SAM produces greater clean-to-corrupted representation stability, and this stability tracks OOD accuracy more closely than sharpness alone.

**One-sentence refinement from smoke data (10-epoch CIFAR-10):** SWA's mid-training point already shows lower λ_max (65.9) and higher paired-CKA (0.864) than SAM ρ=0.05 (λ_max 130.9, CKA 0.846). This is mid-training, not converged behaviour, and is consistent with Mueller et al. [pid: fba30c42c0920bd9590ddc274658c409938b2fb2]'s finding that SAM can generalize better *with higher measured sharpness*. The directional prediction on flatness is therefore explicitly hedged (§5).

---

## 2. Independent variables

| Variable | Levels | Justification (paper_id) |
|---|---|---|
| Optimizer | SGD; SAM (ρ=0.05); SWA | SGD is the baseline; SAM ρ=0.05 is the Foret et al. default for ResNet+CIFAR [pid: a2cd073b57be744533152202989228cb4122270a]; SWA is the non-perturbation flat-minima-oriented control [pid: b8989afff14fb630ca58b6afa917fb42574228ee]. The three-way design uniquely decomposes perturbation-specific from trajectory-averaging effects (Gap 1, Gap 4 in `synthesis/gaps.md`). |
| Dataset (ID / OOD) | CIFAR-10 / CIFAR-10-C; CIFAR-100 / CIFAR-100-C | Hendrycks & Dietterich's standard 15-corruption × 5-severity benchmarks [pid: 49b64383fe36268410c430352637ed23b16820c5]. Two label-cardinalities give a coarse generality check at no extra design cost (CIFAR-100 only changes the final FC layer; <5% wall-clock difference). |
| Seed | {1, 2, 3} | Foret et al. report 5 seeds for headline numbers [pid: a2cd073b57be744533152202989228cb4122270a]; we use 3 due to the 17h compute envelope. Three seeds give nontrivial bootstrap CIs while staying inside the budget. |
| (Fixed) Model | ResNet-18 | Standard ResNet+CIFAR setting used in Foret et al. ablations [pid: a2cd073b57be744533152202989228cb4122270a] and Andriushchenko & Flammarion [pid: b698dbfaf9b961502062cbfcbe05d319047d8495]. Single capacity per `RESEARCH_CONTEXT.md` MVE. |
| (Fixed) Epochs | 200 | Foret et al. CIFAR/WRN protocol uses 200 epochs basic-aug [pid: a2cd073b57be744533152202989228cb4122270a]; Izmailov et al. budget-1 SWA also reports 200 epochs [pid: b8989afff14fb630ca58b6afa917fb42574228ee]. Identical across optimizers; the 2× SAM gradient cost is disclosed in Method, not absorbed by reducing epochs. |
| (Fixed) Batch size | 128 | Andriushchenko & Flammarion show m=128 m-SAM is where SAM's generalization gain actually appears [pid: b698dbfaf9b961502062cbfcbe05d319047d8495]; using 128 keeps us in the regime SAM is documented to work in. |
| Ablation (single seed, optional) | ρ ∈ {0.02, 0.1} on CIFAR-100 only | Foret et al. tune ρ ∈ {0.01, 0.02, 0.05, 0.1, 0.2} [pid: a2cd073b57be744533152202989228cb4122270a]; we bracket 0.05 with one lower and one higher value. Run **only if main grid completes with time to spare**. |

The grid above contains the *only* IVs in the experiment. No new IVs may be added in Stage D/E/F.

---

## 3. Dependent variables (metrics)

| Metric | Role | How computed | Justification (paper_id) |
|---|---|---|---|
| Severity-averaged CIFAR-C accuracy | **Primary** | Top-1 accuracy on the 15 corruption types × 5 severities of CIFAR-{10,100}-C (75 configs), averaged with equal weight. Report severity-disaggregated too. | Hendrycks & Dietterich CIFAR-C protocol [pid: 49b64383fe36268410c430352637ed23b16820c5]; severity-averaged accuracy is the standard summary used in SAM-ON [pid: fba30c42c0920bd9590ddc274658c409938b2fb2] and SWAD [pid: b8989afff14fb630ca58b6afa917fb42574228ee]. |
| OOD gain (Δ vs SGD) | Primary derived | Per-seed: `acc_OOD(opt) − acc_OOD(SGD same seed)` on the matched dataset. | Direct measurement of the RQ quantity. |
| Paired-image penultimate CKA stability | **Primary (mechanism)** | Linear CKA between penultimate features ϕ(x) and ϕ(corrupt(x)) on a fixed 512-image probe set, averaged across the 15 corruption types and 5 severities. Also reported per layer (layer1–4) as diagnostic. | Kornblith et al. linear CKA [pid: 726320cdbd04804ffa8f3a78c095bd1b55a2a695]; paired-image variant is the novel methodological choice motivated by Gap 2 and Gap 5. |
| Top Hessian eigenvalue λ_max | Secondary | Power iteration on the train-loss Hessian over 3 batches of 512 images; report mean and std. | Keskar et al. sharpness foundation [pid: 8ec5896b4490c6e127d1718ffc36a3439d84cb81]; Foret et al. report λ_max as their convergence-sharpness measure [pid: a2cd073b57be744533152202989228cb4122270a]. |
| SAM-style neighborhood loss (ρ=0.05) | Secondary | One inner SAM ascent step at ρ=0.05, then forward-evaluate the loss. Single fixed ρ for cross-optimizer comparability. | Foret et al. m-sharpness definition [pid: a2cd073b57be744533152202989228cb4122270a]; Andriushchenko & Flammarion m-sharpness emphasis [pid: b698dbfaf9b961502062cbfcbe05d319047d8495]. |
| Hessian trace (Hutchinson) | Diagnostic | Hutchinson trace estimator, 20 Rademacher probes, 3 batches × 512 images. | Reparametrization-robustness check against λ_max; supports Petzka-style discussion in Method. |
| ID accuracy | Secondary | Top-1 on the clean CIFAR-{10,100} test set. | Standard; needed to compute OOD gain over a meaningful ID anchor. |
| ID ECE (15-bin) | Secondary | Naeini 15-bin ECE on the clean test set. | Ovadia et al. motivates calibration tracking under shift [pid: 49b64383fe36268410c430352637ed23b16820c5]'s related-work chain. |
| OOD ECE (15-bin) | Secondary | Same as ID ECE, computed per-corruption then averaged. | Calibration degrades under shift even when ID-calibrated; motivated by `RESEARCH_CONTEXT.md` secondary-metric list. |

The smoke runs confirm every metric path produces non-null values on the production pipeline (see `results/runs.jsonl` rows `sam_smoke_s1`, `swa_smoke_s1`).

---

## 4. Full run grid

Main grid = 3 optimizers × 2 datasets × 3 seeds = **18 runs**. Optional ablation = 2 runs (single seed each). Total potential = **20 runs**.

Wall-clock estimates use the "Updated compute data" table: SGD 13.9 s/ep, SAM 28.2 s/ep, SWA 13.9 s/ep, all under AMP bf16 + num_workers=4 on RTX 3070. Eval (incl. CIFAR-C + sharpness + CKA) is ~5–6 min/run; budget 6 min. CIFAR-100 is ~5% slower; budget +5% on CIFAR-100 train time. "Per run" = train + eval.

| # | Optimizer | Dataset | Seed | Train (200ep) | Eval | Per run (3070, h) |
|---|---|---|---|---|---|---|
| 1  | SGD          | CIFAR-10  | 1 | 46.3 min | 6 min | 0.87 |
| 2  | SGD          | CIFAR-10  | 2 | 46.3 min | 6 min | 0.87 |
| 3  | SGD          | CIFAR-10  | 3 | 46.3 min | 6 min | 0.87 |
| 4  | SGD          | CIFAR-100 | 1 | 48.6 min | 6 min | 0.91 |
| 5  | SGD          | CIFAR-100 | 2 | 48.6 min | 6 min | 0.91 |
| 6  | SGD          | CIFAR-100 | 3 | 48.6 min | 6 min | 0.91 |
| 7  | SAM ρ=0.05   | CIFAR-10  | 1 | 94.0 min | 6 min | 1.67 |
| 8  | SAM ρ=0.05   | CIFAR-10  | 2 | 94.0 min | 6 min | 1.67 |
| 9  | SAM ρ=0.05   | CIFAR-10  | 3 | 94.0 min | 6 min | 1.67 |
| 10 | SAM ρ=0.05   | CIFAR-100 | 1 | 98.7 min | 6 min | 1.75 |
| 11 | SAM ρ=0.05   | CIFAR-100 | 2 | 98.7 min | 6 min | 1.75 |
| 12 | SAM ρ=0.05   | CIFAR-100 | 3 | 98.7 min | 6 min | 1.75 |
| 13 | SWA          | CIFAR-10  | 1 | 46.3 min | 6 min | 0.87 |
| 14 | SWA          | CIFAR-10  | 2 | 46.3 min | 6 min | 0.87 |
| 15 | SWA          | CIFAR-10  | 3 | 46.3 min | 6 min | 0.87 |
| 16 | SWA          | CIFAR-100 | 1 | 48.6 min | 6 min | 0.91 |
| 17 | SWA          | CIFAR-100 | 2 | 48.6 min | 6 min | 0.91 |
| 18 | SWA          | CIFAR-100 | 3 | 48.6 min | 6 min | 0.91 |
| A1 | SAM ρ=0.02   | CIFAR-100 | 1 | 98.7 min | 6 min | 1.75 |
| A2 | SAM ρ=0.10   | CIFAR-100 | 1 | 98.7 min | 6 min | 1.75 |

**Main grid total: 21.43 GPU-hours on a 3070-equivalent.** Ablation adds 3.50 h ⇒ **24.93 h** total potential. The budget in `RESEARCH_CONTEXT.md` is 17 h *wall-clock to completion* assuming parallel execution across 4 environments (see §9 and §11).

---

## 5. Pre-registered predictions

Predictions are stated as orderings over the three optimizers, applied per dataset. Confidence is hedged where smoke data warrants.

**P1 — Primary: OOD accuracy.**
Predict: `OOD_acc(SAM) ≳ OOD_acc(SWA) > OOD_acc(SGD)` on both CIFAR-10 and CIFAR-100.
- Strong directional prediction for SGD being last (Foret 2021 [pid: a2cd073b57be744533152202989228cb4122270a]; Kaddour 2022 [pid: 0265144c]; SWAD [pid: 4d87a9f6]).
- SAM-vs-SWA ordering is weakly directional ("SAM ≥ SWA, possibly tied"): smoke @ 10 ep already shows SWA leading on OOD (0.698 vs 0.643), but at 200 ep both literature and Foret's own ablations point to SAM at least matching SWA. *Falsifier:* `OOD_acc(SWA) > OOD_acc(SAM)` by ≥0.5 pp on both datasets across all 3 seeds.

**P2 — Primary mechanism: paired-image penultimate CKA.**
Predict: `CKA(SAM) > CKA(SWA) ≈ CKA(SGD)`.
- This is the core mechanism claim: SAM-trained representations are more stable under input corruption than SWA's even if both are similarly flat. No prior work measures this — strongest directional prediction in the contract.
- Smoke @ 10 ep shows SAM 0.846 vs SWA 0.864: contrary to prediction at mid-training, but at convergence SAM is expected to consolidate its representation-stability advantage.
- *Falsifier (this is THE falsifier of the hypothesis):* `CKA(SWA) ≥ CKA(SAM)` with overlapping seed CIs **and** SWA matching SAM on OOD accuracy. Per `RESEARCH_CONTEXT.md`, this is a publishable negative result.

**P3 — Secondary: top Hessian eigenvalue λ_max.**
Predict (HEDGED): `λ_max(SGD) > λ_max(SAM) ≈ λ_max(SWA)` at convergence, but **we explicitly allow that SAM may exhibit equal or higher sharpness than SWA**.
- Foret 2021 reports SAM ≈ 24× lower λ_max than non-SAM at convergence on WRN-CIFAR [pid: a2cd073b57be744533152202989228cb4122270a].
- Mueller 2023 (SAM-ON) reports SAM-variants generalizing better *with higher sharpness* [pid: fba30c42c0920bd9590ddc274658c409938b2fb2].
- Kaddour 2022 reports SAM λ_max=237 vs SWA=265 (SAM flatter); SWAD reports SWA flatter than SAM on PACS [pid: 0265144c, 4d87a9f6]. The literature itself disagrees.
- Smoke @ 10 ep: SAM 130.9, SWA 65.9 — SAM is the *sharper* one. We do not over-claim that this will invert by epoch 200.
- *No falsifier for the hypothesis is tied to P3* (the hypothesis is precisely that sharpness alone does not determine OOD).

**P4 — Secondary: ECE under shift.**
Predict: `ECE_OOD(SAM) < ECE_OOD(SWA) < ECE_OOD(SGD)`.
- Smoke shows SWA 0.0999 vs SAM 0.1040, essentially tied at 10 ep. Weak directional prediction.

**P5 — Partial correlation (exploratory).**
Predict: After partialling out λ_max, `corr(CKA, OOD_gain | λ_max)` remains positive with magnitude ≥ 0.3 across the N=18 main-grid runs. Reported as exploratory associational evidence (per `RESEARCH_CONTEXT.md`), not as a mediation test.

---

## 6. Analysis plan

**Plots (deliverables for Stage F):**
1. Bar plot: severity-averaged CIFAR-C accuracy per optimizer × dataset, ±seed-CI (bootstrap 1000 resamples over 3 seeds; show both 90% and 50% intervals because n=3).
2. Bar plot: paired-image penultimate CKA per optimizer × dataset, ±seed-CI.
3. Bar plot: λ_max per optimizer × dataset, ±seed-CI (log y-axis given Hessian eig range).
4. Severity-disaggregated line plot: x = severity {1..5}, y = OOD accuracy, one line per optimizer per dataset.
5. Scatter (one point per run, N=18): x = λ_max, y = OOD-gain over SGD. Annotate by optimizer (color) and dataset (marker).
6. Scatter (one point per run, N=18): x = paired-CKA, y = OOD-gain over SGD. Same annotation.

**Statistical tests:**
- For each metric: per-optimizer × per-dataset mean and 90% bootstrap CI across seeds. Report individual seed values in the appendix per `experiment-designer.md` rule 6.
- Pairwise comparisons (SAM vs SWA, SAM vs SGD, SWA vs SGD) via paired bootstrap differencing within seed (since seed is matched across optimizers).
- **Partial correlation analysis (exploratory):** Pearson and Spearman `corr(CKA, OOD_gain | λ_max)` over the N=18 runs. Reported with an explicit caveat: this is associational, not a formal mediation analysis, and N=18 is small. Following Schapiro & Zhao [pid: a4002b51cf357bd741882062806b9204ce6e6a33], we present this as "consistent with / inconsistent with" rather than causal evidence.

**Reporting:** Both optimizer-level summary (3 numbers × 2 datasets) and seed-level individual values (18 rows), as required by `experiment-designer.md` rule 6.

---

## 7. Falsification criteria

Verbatim from `RESEARCH_CONTEXT.md`:

> if SWA matches SAM on OOD accuracy **and** on representation stability while both are similarly flatter than SGD, the representation-specific hypothesis is not supported. This is a publishable negative result (assignment §2.2).

Operationalised: hypothesis is falsified if **all three** hold across both datasets:
1. `|OOD_acc(SAM) − OOD_acc(SWA)| < 0.5 pp` with overlapping 90% seed CIs;
2. `|paired_CKA(SAM) − paired_CKA(SWA)| < 0.01` with overlapping 90% seed CIs;
3. `λ_max(SAM) < λ_max(SGD)` and `λ_max(SWA) < λ_max(SGD)` (both flatter than SGD).

If only conditions 1–2 hold but condition 3 fails (e.g. neither SAM nor SWA is flatter than SGD), the result is *anomalous* and reported separately — it does not support or refute the hypothesis but contributes to the Mueller-style "SAM works without flatness" thread.

---

## 8. Failure-mode plan

| Failure mode | Probability | Contingency |
|---|---|---|
| Training diverges (NaN loss) | Low (smoke runs all clean) | Lower LR by 2× for that cell; re-seed; flag in results. |
| OOM on Colab T4 / A100 / friend's 3060 | Very low (smoke peak 480 MB) | Smoke runs used 480 MB at AMP bf16; we have 16× headroom on a T4 (16 GB). No mitigation expected to fire. |
| Sharpness measurement noise (high σ on power iter) | Medium (spike showed ±24 on λ=61) | Spec says 3 batches × 512 imgs; if σ/μ > 0.5, increase to 5 batches and re-run eval only (no retraining). Report std alongside mean. |
| CKA brittleness across runs of same config | Medium | Use a fixed seed-1 probe set of 512 images for *all* CKA evaluations (same images, only the model changes). Avoids cross-run probe-set variance. |
| Colab disconnects mid-training | High on Colab Pro free tier; medium on paid | All training writes checkpoint every 25 epochs. Resume-from-checkpoint exists in `train.py`. Stage D must verify resume path. |
| CIFAR-C download fails on Colab | Medium | Pre-stage CIFAR-10-C and CIFAR-100-C onto each user's Google Drive (one-time, ~3 GB total). Drive-mount in Colab cell template (§11.8). |
| Friend's machine has no cu124 wheel for py3.13 | Low-medium | Fall back to Python 3.12 install; pin requirements.txt to py3.12-compatible wheels. Setup assumptions in §11.8 acknowledge this. |
| 200-epoch SGD overfits ID-ECE | Medium (spike report §5.3 flagged 50-ep ID acc 94.4%) | This is informational, not blocking. If observed, note in Method as expected SGD overfitting behaviour — does not affect OOD comparison since SAM and SWA share the same schedule. |
| Wall-clock under-estimate on Colab T4 | Medium-high | §11.5 fallback cuts in priority order. T4-equivalent (0.5×) is our planning factor; if a Colab turns out to be L4 (0.8×) it's bonus capacity. |

---

## 9. Compute budget

**Per-run wall-clock (RTX 3070, AMP bf16, num_workers=4):**
- SGD CIFAR-10: 0.87 h; SGD CIFAR-100: 0.91 h
- SAM CIFAR-10: 1.67 h; SAM CIFAR-100: 1.75 h
- SWA CIFAR-10: 0.87 h; SWA CIFAR-100: 0.91 h

**Main grid (18 runs) total compute-hours (3070-equivalent): 21.43 h.**
**With ρ-ablation (20 runs): 24.93 h.**

Comparison against the 17-h budget in `RESEARCH_CONTEXT.md`: the 17 h is the **wall-clock-to-completion** target across 4 parallel environments, not a single-machine GPU-hours budget. Aggregate compute-hours of 21.43 h is the cost-of-goods figure (relevant for cloud billing); the wall-clock target requires parallelism. With 4 runners assigned per §11.3, projected wall-clock is **~6 h** on the longest queue (khanh_3070) — comfortably inside 17 h.

**Cuts in priority order, if needed (matches §11.5):**
1. Drop ρ-ablation (saves 3.50 h aggregate; main grid unaffected).
2. Drop CIFAR-100 seed 3 (saves ~3.57 h aggregate; weakens CIFAR-100 CI from n=3 to n=2).
3. Drop CIFAR-100 seed 2 as well (saves another ~3.57 h; CIFAR-100 becomes n=1 — usable only as point estimate).
4. Drop CIFAR-100 entirely (saves ~10.7 h; main grid reduces to 9 runs on CIFAR-10).

---

## 10. What this plan deliberately does NOT do

- **No additional optimizers** (ASAM, GSAM, F-SAM, SWAD, WASAM). Considered; rejected. The contribution is SAM vs SWA decomposition, not a SAM-variant horse race. Including variants would dilute the headline mechanism story and overrun budget.
- **No additional model capacities** (ResNet-50, WRN-28-10, ViT). Considered; rejected. `RESEARCH_CONTEXT.md` MVE specifies single capacity; cross-capacity scaling is appendix material at best.
- **No DomainBed / multi-domain OOD benchmark.** Considered; rejected. CIFAR-C is the *specific* benchmark where the SAM-vs-SWA gap is unexplored (Gap 1).
- **No formal causal mediation analysis.** Per `RESEARCH_CONTEXT.md`: N=18 is too small. Partial correlation is reported as exploratory associational evidence only.
- **No BatchNorm-adaptation comparison** (e.g. Schneider et al. test-time BN). Considered; rejected. Would confound the optimizer comparison; flagged in Method limitations.
- **No additional sharpness measures beyond λ_max + Hutchinson trace + SAM-neighborhood loss.** Considered ASAM-adaptive sharpness and Petzka relative flatness; rejected as eval-time additions because both require non-trivial reimplementation and the three measures we have already triangulate.
- **No representation analysis beyond paired-image penultimate CKA + per-layer CKA.** Considered SVCCA, RSA, probing classifiers; rejected per Kornblith et al. [pid: 726320cdbd04804ffa8f3a78c095bd1b55a2a695] showing CKA dominates the alternatives.
- **No paper writing in Stage D/E.** Stage F handles writing; Stage D/E are runs + aggregation only.

---

## 11. Distributed Execution Plan

Four execution environments are available:
- `khanh_3070`: primary author's local RTX 3070, Windows + Python 3.13. Pace factor **1.0×** (baseline).
- `friend_3060`: collaborator's local RTX 3060. Pace factor **~0.85×**.
- `khanh_colab`: primary author's Colab Pro. Plan as T4-equivalent **~0.5×**.
- `friend_colab`: collaborator's Colab Pro. Plan as T4-equivalent **~0.5×**.

Any L4 / A100 allocation in Colab is *bonus*; the plan does not depend on it.

### 11.1 Full config grid (configs/{name}.yaml — naming only; do NOT write YAMLs at this stage)

Naming convention: `{optimizer}{rho_suffix}_{dataset}_s{seed}.yaml`.

| Config name | Optimizer | ρ | Dataset | Seed |
|---|---|---|---|---|
| `sgd_cifar10_s1.yaml`        | sgd | — | cifar10  | 1 |
| `sgd_cifar10_s2.yaml`        | sgd | — | cifar10  | 2 |
| `sgd_cifar10_s3.yaml`        | sgd | — | cifar10  | 3 |
| `sgd_cifar100_s1.yaml`       | sgd | — | cifar100 | 1 |
| `sgd_cifar100_s2.yaml`       | sgd | — | cifar100 | 2 |
| `sgd_cifar100_s3.yaml`       | sgd | — | cifar100 | 3 |
| `sam005_cifar10_s1.yaml`     | sam | 0.05 | cifar10  | 1 |
| `sam005_cifar10_s2.yaml`     | sam | 0.05 | cifar10  | 2 |
| `sam005_cifar10_s3.yaml`     | sam | 0.05 | cifar10  | 3 |
| `sam005_cifar100_s1.yaml`    | sam | 0.05 | cifar100 | 1 |
| `sam005_cifar100_s2.yaml`    | sam | 0.05 | cifar100 | 2 |
| `sam005_cifar100_s3.yaml`    | sam | 0.05 | cifar100 | 3 |
| `swa_cifar10_s1.yaml`        | swa | — | cifar10  | 1 |
| `swa_cifar10_s2.yaml`        | swa | — | cifar10  | 2 |
| `swa_cifar10_s3.yaml`        | swa | — | cifar10  | 3 |
| `swa_cifar100_s1.yaml`       | swa | — | cifar100 | 1 |
| `swa_cifar100_s2.yaml`       | swa | — | cifar100 | 2 |
| `swa_cifar100_s3.yaml`       | swa | — | cifar100 | 3 |
| `sam002_cifar100_s1.yaml` *(ablation)* | sam | 0.02 | cifar100 | 1 |
| `sam010_cifar100_s1.yaml` *(ablation)* | sam | 0.10 | cifar100 | 1 |

All non-listed hyperparameters (lr=0.1, momentum=0.9, weight_decay=5e-4, epochs=200, batch_size=128, augmentation="standard", AMP bf16, num_workers=4, swa_start_epoch=160, swa_lr=0.005) are fixed and inherit from a common default. Stage D will materialise these YAMLs from a small template script — not done here.

### 11.2 Estimated runtime per config (hours, by environment)

Pace factors applied: `khanh_3070` = 1.0×, `friend_3060` = 0.85× (so 1/0.85 = 1.176× wall-clock), `khanh_colab` = `friend_colab` = 0.5× (so 2.0× wall-clock).

| Config | khanh_3070 (h) | friend_3060 (h) | khanh_colab (h) | friend_colab (h) |
|---|---|---|---|---|
| sgd_cifar10_s{1,2,3}        | 0.87 | 1.02 | 1.74 | 1.74 |
| sgd_cifar100_s{1,2,3}       | 0.91 | 1.07 | 1.82 | 1.82 |
| sam005_cifar10_s{1,2,3}     | 1.67 | 1.96 | 3.34 | 3.34 |
| sam005_cifar100_s{1,2,3}    | 1.75 | 2.06 | 3.50 | 3.50 |
| swa_cifar10_s{1,2,3}        | 0.87 | 1.02 | 1.74 | 1.74 |
| swa_cifar100_s{1,2,3}       | 0.91 | 1.07 | 1.82 | 1.82 |
| sam002_cifar100_s1 *(ablation)* | 1.75 | 2.06 | 3.50 | 3.50 |
| sam010_cifar100_s1 *(ablation)* | 1.75 | 2.06 | 3.50 | 3.50 |

### 11.3 Suggested runner assignment

Principles:
- Put SAM CIFAR-100 (longest + highest-risk; 1.75 h on 3070, 3.50 h on T4) on the fastest hardware → `khanh_3070` and `friend_3060`.
- Put SGD/SWA (short, robust, checkpoint-friendly) on Colab → tolerant of disconnects since restart cost is low and checkpointing every 25 epochs caps loss to <12 min of training per disconnect.
- Balance total queue wall-clock across the four runners.

| Runner | Assigned configs | Total wall-clock (h) |
|---|---|---|
| **khanh_3070** (1.0×) | sam005_cifar100_s1, sam005_cifar100_s2, sam005_cifar100_s3, sam005_cifar10_s1 | 1.75 + 1.75 + 1.75 + 1.67 = **6.92** |
| **friend_3060** (0.85×) | sam005_cifar10_s2, sam005_cifar10_s3, sgd_cifar100_s1, swa_cifar100_s1, swa_cifar10_s1 | 1.96 + 1.96 + 1.07 + 1.07 + 1.02 = **7.08** |
| **khanh_colab** (0.5×) | sgd_cifar10_s1, sgd_cifar10_s2, sgd_cifar10_s3, sgd_cifar100_s2, swa_cifar10_s2 | 1.74×3 + 1.82 + 1.74 = **8.78** |
| **friend_colab** (0.5×) | swa_cifar10_s3, swa_cifar100_s2, swa_cifar100_s3, sgd_cifar100_s3 | 1.74 + 1.82 + 1.82 + 1.82 = **7.20** |

Total wall-clock if all four run in parallel: max(6.92, 7.08, 8.78, 7.20) = **8.78 h** (gated by `khanh_colab`). Inside the 17 h budget with >8 h margin.

**Aggregate compute-hours summed across runners (sanity check):** 6.92 + 7.08 + 8.78 + 7.20 = 29.98 h wall-clock summed (this is 4-machine-wall-clock-hours; NOT 3070-equivalent compute-hours, which remains 21.43 h per §9).

Ablation configs (sam002_cifar100_s1, sam010_cifar100_s1, 1.75 h each on 3070) are queued **only** after the main grid completes; assigned to whichever of `khanh_3070` / `friend_3060` finishes first.

### 11.4 Priority order within each runner's queue

Rule 1: **Longest first** — fail fast and surface SAM-CIFAR-100 issues before SGD-CIFAR-10 noise.
Rule 2: **All seed-1 configs across all runners complete before any seed-2 starts.** This gives a coarse single-seed answer to the RQ by hour ~5–6 of wall-clock, providing an early go/no-go signal.
Rule 3: SAM CIFAR-100 is the highest-risk cell because (a) longest wall-clock and (b) the SAM-vs-SWA discrimination is most uncertain on the harder dataset → it leads each queue that contains one.

Per-runner queue order:
- **khanh_3070**: `sam005_cifar100_s1` → `sam005_cifar10_s1` → `sam005_cifar100_s2` → `sam005_cifar100_s3`
- **friend_3060**: `sam005_cifar10_s2` (longest available after seed-1 sweep) → `sgd_cifar100_s1` → `swa_cifar100_s1` → `swa_cifar10_s1` → `sam005_cifar10_s3`
- **khanh_colab**: `sgd_cifar100_s2` → `sgd_cifar10_s1` → `sgd_cifar10_s2` → `swa_cifar10_s2` → `sgd_cifar10_s3`
- **friend_colab**: `swa_cifar100_s2` → `swa_cifar100_s3` → `sgd_cifar100_s3` → `swa_cifar10_s3`

Synchronization point: after **all seed-1 configs complete**, take a 15-min checkpoint review (do the bar plots look sensible? are any cells clearly broken?) before continuing to seeds 2 and 3.

### 11.5 Fallback cuts if one Colab is unavailable or slower than expected

In priority order (least painful first), with quantified savings:

| Cut | Action | Saves (wall-clock on slowest runner) |
|---|---|---|
| F1 | Reroute the missing-Colab queue to whichever of khanh_3070 / friend_3060 has more headroom; no scope reduction. | 0 h (only redistributes; total still ≤ 9 h on slowest). Use this when only one Colab disappears. |
| F2 | Drop the ρ-ablation (was outside the main grid anyway). | 3.50 h aggregate (1.75 h × 2 ablation runs on 3070-equivalent). |
| F3 | Drop CIFAR-100 seed 3 (configs #6 sgd, #12 sam, #18 swa). | ~3.57 h aggregate; weakens CIFAR-100 CI from n=3 to n=2. |
| F4 | Drop CIFAR-100 seed 2 as well. | another ~3.57 h aggregate; CIFAR-100 reduces to n=1. |
| F5 | Drop CIFAR-100 entirely (9 runs). | ~10.7 h aggregate; results restricted to CIFAR-10, which still supports the RQ but weakens generality claim. |

Trigger: re-evaluate after the seed-1 sync point (§11.4 Rule 2). If projected slowest-runner wall-clock at that point exceeds 13 h, apply F2 immediately and consider F3.

### 11.6 Per-runner results file rule

Each environment writes only to its own results file:
- `results/runs_khanh_3070.jsonl`
- `results/runs_khanh_colab.jsonl`
- `results/runs_friend_3060.jsonl`
- `results/runs_friend_colab.jsonl`

No runner writes to `results/runs.jsonl` directly. This avoids merge conflicts when the four runners push concurrently. Each row carries a `run_id` of the form `{optimizer}{rho_if_sam}_{dataset}_s{seed}` (e.g. `sam005_cifar100_s1`) plus `runner_id` and `git_commit` fields for attribution.

### 11.7 Merge plan after all runs finish (Stage D deliverable)

1. Each runner commits and pushes their `runs_{runner_id}.jsonl` to a branch named `runs/{runner_id}` and opens a PR against `master`.
2. The PRs touch *only* their own results file → zero merge conflict by construction.
3. After all four are merged, run `scripts/merge_runs.py` (Stage D deliverable, not written here) which:
   - Concatenates `results/runs_*.jsonl` into `results/runs.jsonl` (the canonical aggregated file).
   - Deduplicates by `run_id` (last-writer-wins with a warning if duplicates have differing content — surfaces re-run cases for human review).
   - Validates each row's `metrics` block has no nulls in `ood_accuracy_avg`, `paired_cka_penultimate`, `sharpness_top_eig` (the three primary fields).
4. `scripts/aggregate.py` (Stage E deliverable) consumes the merged `results/runs.jsonl` and emits the Stage F bar/scatter/correlation tables in `results/`.

Deliverables to declare in Stage D: `configs/*.yaml` (20 files), `scripts/merge_runs.py`.

### 11.8 Setup assumptions

**Local Windows GPU runners (`khanh_3070`, `friend_3060`):**
- Python 3.13 (preferred) or 3.12 (fallback if cu124 wheel for py3.13 still missing on the 3060 machine).
- Install path per `requirements.txt`: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124` then `pip install -r requirements.txt`.
- Confirm AMP bf16 works on Ampere (3060 / 3070 both support it natively).
- CIFAR-10-C and CIFAR-100-C downloaded to `data/CIFAR-10-C/` and `data/CIFAR-100-C/` once per machine (3 GB total).

**Colab Pro runners (`khanh_colab`, `friend_colab`):**
- Torch is preinstalled in the Colab runtime image; do not reinstall.
- Mount Google Drive for (a) reading pre-staged CIFAR-C and (b) persisting results across runtime disconnects.
- A 5-line Colab starter cell that Stage D will pin in a `scripts/colab_setup.ipynb`:

```python
!pip -q install pyyaml pymupdf requests   # matplotlib is already in Colab
from google.colab import drive; drive.mount('/content/drive')
!ln -sfn /content/drive/MyDrive/A2/data    /content/A2/data
!ln -sfn /content/drive/MyDrive/A2/results /content/A2/results
!cd /content/A2 && python train.py --config configs/sam005_cifar100_s1.yaml --runner_id khanh_colab
```

- Results written to `/content/drive/MyDrive/A2/results/runs_{runner_id}.jsonl` survive disconnects.
- Resume-from-checkpoint must be verified in Stage D before launching long Colab runs (checkpoint cadence: every 25 epochs).

---

## Methodological decision flagged for human approval before Stage D

- **`swa_start_epoch=160, swa_lr=0.005`** are inherited from Izmailov et al.'s budget-1 protocol [pid: b8989afff14fb630ca58b6afa917fb42574228ee] (begin SWA at 75% of total epochs, hold a constant low LR). The smoke run used `swa_start_epoch=7, swa_lr=0.05` for a 10-epoch toy. The 200-epoch values are a direct scaling but **not yet smoke-tested at full length**. Stage D should verify the SWA average is meaningfully different from the underlying SGD weights before launching all 6 SWA cells — a 5-minute sanity check.
- **Probe set for CKA** is currently fixed at 512 images of seed-1 of the test split. If reviewers prefer the more conservative practice of using a held-out probe set, this is a 1-line code change but should be confirmed before Stage E.

All other methodological choices are derived directly from the cited papers and require no further approval.
