# Positioning Brief

This brief locks how the paper positions itself relative to prior work. It feeds the writer subagent (Related Work and later Introduction) and the experiment-designer.

## Claimed contribution

This work provides the first controlled empirical comparison of SAM and SWA as two distinct flat-minima-oriented optimizers on the canonical common-corruption robustness benchmarks (CIFAR-10-C, CIFAR-100-C), jointly measuring (i) loss-landscape sharpness via top Hessian eigenvalue and SAM-style neighbourhood loss, (ii) paired-image representation stability via CKA, and (iii) OOD accuracy and calibration. The novel contribution is **not** demonstrating that SAM improves OOD generalization — that is already established — but **decomposing** whether SAM's OOD gain over SGD is fully accounted for by sharpness reduction, or whether residual gains require an additional explanation grounded in representation stability. SWA serves as a non-perturbation flat-minima-oriented control that no prior CIFAR-C-focused study has included alongside SAM.

The contribution holds even if the hypothesis is falsified: if SWA matches SAM on OOD accuracy and on representation stability, this is a publishable negative result with concrete implications for the SAM-for-OOD literature (flat-minima ≈ SAM in the corruption setting; representation stability is not a distinguishing mechanism).

## Most directly comparable prior works

**Kaddour et al. (2022) — "When Do Flat Minima Optimizers Work?"** [pid: 0265144c696bf9371a0a63ece590dd2403ee71be]. The only systematic head-to-head SAM-vs-SWA comparison with Hessian-eigenvalue measurements across 42 tasks. They find SAM achieves lower λ_max than SWA on WRN-28-10/CIFAR-100 (237 vs 265), and that WASAM (an average of SAM iterates) dominates both. Differences from our work: (a) evaluation is i.i.d., not corruption-OOD; (b) no representation-stability measurement; (c) no per-corruption disaggregation; (d) WASAM is the headline contribution, not the SAM-vs-SWA decomposition.

**Mueller et al. (2023) — "Normalization Layers Are All That SAM Needs" (SAM-ON)** [pid: fba30c42c0920bd9590ddc274658c409938b2fb2]. Provides the direct empirical evidence that SAM can improve generalization while *increasing* measured sharpness — SAM-ON achieves 84.19 % on WRN-28-10/CIFAR-100 vs SAM-all's 83.11 % while being sharper (ℓ∞ m-sharpness 0.090 vs 0.048). Differences from our work: (a) no SWA control; (b) ImageNet-variant OOD (ImageNet-R, ImageNet-A, ObjectNet), not CIFAR-C; (c) no CKA representation analysis. Our experiment tests whether SAM-ON's "better-and-sharper" decoupling generalizes to the corruption setting and whether the residual generalization gain is captured by representation stability.

## Specific gaps addressed

1. **No controlled SAM-vs-SWA comparison on CIFAR-C.** Every flat-minima-for-OOD study uses DomainBed multi-domain benchmarks or ImageNet variants. SWA is consistently absent as an explicit non-perturbation control. (synthesis/gaps.md Gap 1)

2. **No joint sharpness + CKA stability + OOD measurement.** Each quantity has been measured separately in different papers, but never triangulated in a single optimizer-comparison experiment. (Gap 2)

3. **The sharpness-mechanism decoupling has not been tested on corruption OOD.** Andriushchenko & Flammarion (2022), Mueller et al. (2023), and Baek et al. (2024) all argue flatness is causally insufficient for SAM's gains, but only in i.i.d. settings. Our study extends this decoupling test to CIFAR-C. (Gap 3)

4. **SAM variants are compared without SWA as a non-perturbation baseline.** SAGM, DGSAM, and SWAD all improve over vanilla SAM in DG without including SWA as an explicit control, conflating perturbation-specific and trajectory-averaging effects. (Gap 4)

5. **No representational explanation has been tested for SAM's OOD gains.** Schapiro & Zhao (2024) explicitly note that "low sharpness alone does not account for all of SAM's generalization benefits" in OOD settings, but propose no concrete representation-stability hypothesis to fill the explanatory gap. (Gap 5)

## What SWA is and is not (calibration note)

SWA is deliberately **not** described as a "flatness-only" or "pure flatness" control. SWA averages weights across the late-training trajectory; this changes both the geometry of the converged solution *and* introduces ensemble-like averaging effects that are not captured by sharpness measures alone. The honest framing is: SAM and SWA are two distinct flatness-oriented optimizers that arrive at flat minima through different mechanisms (adversarial perturbation vs trajectory averaging), and we compare which mechanism's geometric and representational signature better tracks OOD accuracy.
