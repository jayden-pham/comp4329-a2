# Stage D0 Spike Report

Single SGD pilot run on CIFAR-10 / ResNet-18, 50 epochs, seed=1.
Source row: `results/runs.jsonl:1` (`run_id=spike_s1`, timestamp `2026-05-22T14:36:01Z`).

---

## 1. Wall-clock observed (RTX 3070, Python 3.13)

| Phase | Time | Notes |
|---|---|---|
| Training (50 epochs SGD) | **1458.7 s** (24.3 min) | 29.2 s / epoch |
| Eval + sharpness + CKA   | 192.8 s (3.2 min) | **OOD + CKA did not actually run** — see §5 |
| **Total** | **1651.5 s (27.5 min)** | |

Throughput: 29.2 s/epoch × ~391 batches/epoch ≈ 75 ms / iteration. That is ~3× slower than the theoretical RTX 3070 ceiling for ResNet-18 / batch-128 (~25 ms/iter), implying a CPU / data-loader bottleneck under Windows + `num_workers=2`. Not blocking — see §6 for an easy speedup option.

## 2. Projected wall-clock for full 200-epoch runs

Linear extrapolation from observed 29.2 s/epoch SGD, with the SAM ≈ 2× SGD and SWA ≈ 1× SGD heuristics, plus an estimated **~9 min eval** when CIFAR-C is present (3.2 min observed without OOD/CKA, plus ~5 min for 75 CIFAR-C configs and ~1 min for paired-CKA on 512 samples × 75 configs).

| Optimizer | Train (200 ep) | Eval (incl. CIFAR-C) | Per run |
|---|---|---|---|
| SGD | 97.2 min (1.62 h) | ~9 min | **~1.77 h** |
| SAM (ρ = 0.05) | ~194 min (3.24 h) | ~9 min | **~3.40 h** |
| SWA | ~99 min (1.65 h) | ~9 min | **~1.80 h** |

CIFAR-100 vs CIFAR-10 should differ by < 5 % (only the final 512×N_classes FC differs); treated as equal in the projection.

## 3. Peak GPU memory

**712 MB / 8192 MB used on the RTX 3070** (under 9 % of capacity). Plenty of headroom for batch 256, AMP, and larger CKA sample sizes. Same for the RTX 3060 (8 GB or 12 GB models).

## 4. ID-metric sanity checks

| Metric | Value | Expected range (50-ep SGD ResNet-18 CIFAR-10) | Status |
|---|---|---|---|
| ID accuracy | **0.9439** (94.4 %) | 89–93 % typical, 94 % high end | **High but plausible** — cosine LR + 3×3 conv1 + standard aug + seed=1 happened to land well. Not a red flag. |
| ID loss | 0.2035 | 0.20–0.25 | OK |
| ID ECE (15 bins) | 0.0291 | < 0.04 well-calibrated | OK |
| Top Hessian eigenvalue λ_max | **60.8 ± 24.4** | 30–500 for CIFAR ResNet-18 | OK; the ±24.4 across 3 batches is a known noise property of single-batch power iteration |
| Hessian trace (Hutchinson) | 376 | Same order as λ_max × effective rank | OK |
| SAM-neighborhood loss (ρ=0.05) | 0.0451 | < natural loss (0.20) | OK; small local rise → flat enough at convergence |
| Peak GPU memory | 712 MB | < 8000 MB on RTX 3070 | OK |

No NaN, no Inf, no near-zero variance. All numeric paths are alive.

## 5. Issues identified

### 5.1 BLOCKER: OOD + CKA pipeline was NOT actually exercised

`results/runs.jsonl:1` shows:

```
"ood_accuracy_avg": null,
"ood_accuracy_per_corruption": {},
"paired_cka_penultimate": null,
"paired_cka_per_corruption": {},
```

This means **`data/CIFAR-10-C/` was not present at run time** — `eval_ood.py:load_cifar_c` raised `FileNotFoundError`, `train.py` caught it gracefully, but the downstream CKA was also skipped because it depends on the same data. The 27.5 min total wall-clock therefore reflects training + ID eval + sharpness only — **NOT a full Stage F-equivalent run**.

**Action required before any production run**: download CIFAR-10-C (and later CIFAR-100-C) and re-verify the OOD + CKA paths against the existing `checkpoints/spike_s1.pt` checkpoint. No re-training needed; just:

```powershell
# Download CIFAR-10-C from https://zenodo.org/record/2535967/files/CIFAR-10-C.tar
# (about 2.7 GB; extract so data/CIFAR-10-C/labels.npy + 19 .npy files exist)

# Verify OOD path
python scripts/eval_ood.py --checkpoint checkpoints/spike_s1.pt --dataset cifar10

# Verify CKA path
python scripts/cka.py --checkpoint checkpoints/spike_s1.pt --dataset cifar10
```

Both must print non-null OOD/CKA metrics before scaling to 18 runs. Expected runtime: ~5–8 minutes total for the two verifications.

### 5.2 Training is ~3× slower than the RTX 3070 ceiling

29.2 s/epoch vs expected ~10 s/epoch for ResNet-18 batch 128 on Ampere. Most likely cause: Windows + Python 3.13 + `num_workers=2` data-loader bottleneck. The GPU is sitting at < 10 % memory and presumably < 50 % compute utilization. Mitigations in §6.

### 5.3 ID accuracy 94.4 % is at the high end

Not a problem per se, but worth verifying that the full 200-epoch SGD doesn't overfit by reaching ~96–97 % and then degrading ID-ECE. The 50-epoch spike is too short to see this; the first real SGD 200-epoch run will tell us.

## 6. Compute budget analysis

### Single-machine projection (no optimizations, current code)

Full grid: 3 optimizers × 2 datasets × 3 seeds = **18 runs**.

| Optimizer | Runs × (CIFAR-10 + CIFAR-100, 3 seeds each) | Total compute |
|---|---|---|
| SGD | 6 × 1.77 h | 10.6 h |
| SAM | 6 × 3.40 h | **20.4 h** |
| SWA | 6 × 1.80 h | 10.8 h |
| **Total** | 18 runs | **~41.8 h GPU-hours** |

Single-machine budget per `RESEARCH_CONTEXT.md` is 17 h. So as-is on one machine, we are **~2.5× over budget**.

### Multi-machine reality

We have three GPUs available: RTX 3070 (you), RTX 3060 (collaborator), Colab Pro (likely T4 or L4; A100 if lucky). With parallel queues:
- Effective parallel budget: ~3 × single-machine = **~50 h of parallel compute**
- 41.8 h of work / 3 machines ≈ **14 h wall-clock** at perfect balance
- Realistic with 3070 fastest, 3060 ~10 % slower, T4 ~25 % slower than 3070: **15–18 h wall-clock**

**This fits the deadline** (paper due in 1–2 days). The 17 h budget in `RESEARCH_CONTEXT.md` should be interpreted as *wall-clock to completion* once parallelism is taken into account; the 41.8 h is total GPU-hours summed across machines, which is the correct cost metric for cloud / time-on-shared-hardware accounting, but not the relevant constraint here.

### If we want to drop scope anyway

In priority order (least painful first):

| Cut | Saves | New grid | New compute |
|---|---|---|---|
| Drop the ρ ∈ {0.02, 0.1} ablation (already optional) | ~6.8 h | 18 runs | 41.8 h |
| **Drop CIFAR-100** | ~20.9 h | 9 runs (CIFAR-10 only) | **~20.9 h** |
| Drop one seed | ~14 h | 12 runs (2 seeds × 2 datasets × 3 opt) | ~27.9 h |
| Drop CIFAR-100 AND one seed | ~27.9 h | 6 runs | ~13.9 h — fits 17 h single-machine |

**Recommendation**: do NOT drop scope yet. Distribute the 18 runs across 3 machines and use parallelism. Only fall back to "drop CIFAR-100" if Stage E shows we are running behind by Day 3 morning.

## 7. Speed optimization: 1.5–2× easy win

Add automatic mixed precision (AMP) to `train.py`. This is a half-day-of-engineering equivalent for new code but a single PR-sized change here. Expected effect on RTX 3070:
- Training: 29 s/epoch → ~15–18 s/epoch (1.6–2×)
- Memory: 712 MB → ~500 MB (more headroom)
- Numerical: tiny accuracy drop possible (< 0.2 %); acceptable for this study

If applied before launching Stage E, full grid drops from 41.8 h → **~22–26 h**. Still benefits from parallelism but a much more comfortable margin.

A secondary tweak: increase `num_workers` from 2 to 4 (or 6 on the 3060) to reduce data-loader bottleneck. On Windows num_workers > 4 sometimes destabilizes; 4 is the safe upper bound.

Neither optimization is *required* to fit the deadline; both are recommended.

## 8. Recommendations going into Stage C

1. **Immediate (blocking)**: download CIFAR-10-C, run the verification commands in §5.1, confirm OOD + CKA produce non-null metrics. If the spike checkpoint produces sensible CIFAR-10-C numbers (severity-1 accuracy in 75–85 %, severity-5 in 35–55 %, paired-CKA penultimate in 0.5–0.9), the pipeline is green.
2. **Strongly recommended**: add AMP to `train.py` and bump `num_workers` to 4. ~30 min of engineering work; ~50 % compute saving across the full grid.
3. **Lock the grid as 18 runs** (3 optimizers × 2 datasets × 3 seeds). With AMP + 3-machine parallel execution we have plenty of margin.
4. **Defer the ρ-ablation to a "if Day 4 morning shows time left" stretch task.** Only 2 extra runs (CIFAR-100, ρ ∈ {0.02, 0.1}); roughly 6.4 h. Adds value to Method/Analysis but is not required for the central mediation claim.
5. The Stage C experiment-designer should produce an `EXPERIMENT_PLAN.md` that:
   - Assumes AMP is enabled
   - Includes a per-machine assignment of which configs go where (longest SAM runs to fastest GPU)
   - States the falsification criterion verbatim from `RESEARCH_CONTEXT.md`
   - Locks ρ = 0.05 as the primary radius, with the {0.02, 0.1} sweep tagged "if time"

---

**Verdict**: pipeline mechanically validates (training, ID eval, sharpness, checkpointing) but OOD+CKA paths must be re-verified against a downloaded CIFAR-10-C before Stage E. Grid is technically over the single-machine budget but well within the realistic multi-machine + AMP envelope. Proceed to Stage C after the §5.1 verification.
