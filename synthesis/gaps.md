# Research Gaps

These gaps are identified from the 53-paper corpus in `notes/`. Each `[pid: ...]` tag gives the canonical `paper_id` for the cited work; the writer will translate these to `cite_keys` from `papers/cite_keys.json`.

---

## Gap 1: No Controlled SAM vs. SWA Comparison on Corruption-Robustness Benchmarks

**What the gap is:** The literature contains no experiment that places SAM and SWA side-by-side under matched training protocols and evaluates both on CIFAR-C or ImageNet-C corruption benchmarks. Every flat-minima-for-OOD study either uses DomainBed multi-domain benchmarks (SWAD [pid: 4d87a9f6], SAGM [pid: beb8c384], DGSAM [pid: 0da44af3], Kaddour et al. [pid: 0265144c]) or ImageNet variants (SAM-ON [pid: fba30c42]), and no study uses SWA as an explicit control alongside SAM.

**Why it matters for the RQ:** The RQ asks whether SAM's OOD gains stem from sharpness reduction or from some other mechanism (representation stability). The only way to decompose these effects is to include SWA—a flatness-oriented optimizer that achieves comparable or lower sharpness via a different trajectory mechanism—as a control. Without this control, any correlation between SAM's flatness and its OOD accuracy is confounded by other SAM-specific properties (adversarial perturbation direction, Jacobian regularization, stochastic noise bias). The closest existing work, Kaddour et al. (2022), compares SWA and SAM on WRN/CIFAR-100 and finds SAM achieves lower λ_max (237 vs. 265), but does not use OOD corruption benchmarks.

**Closest existing work:** Kaddour et al. [pid: 0265144c] compare SWA and SAM geometrically across 42 tasks but use i.i.d. evaluation metrics, not CIFAR-C. SWAD [pid: 4d87a9f6] uses both SWA-type averaging and SAM but in DomainBed settings, not corruption benchmarks. Schapiro & Zhao [pid: a4002b51] use zero-shot OOD on synthetic rotation/color shifts, not the 15-corruption-type CIFAR-C protocol.

**How our proposed work addresses it:** The RQ's minimum viable experiment places SGD, SAM (ρ=0.05), and SWA under identical training budgets on CIFAR-10 and CIFAR-100, evaluated on CIFAR-10-C and CIFAR-100-C with severity-averaged accuracy as the primary metric. This is the first controlled head-to-head of the two dominant flat-minima-oriented optimizers on the standard corruption robustness benchmark.

---

## Gap 2: Flatness and OOD Accuracy Are Compared Without Simultaneous Representation Stability Measurement

**What the gap is:** No existing paper jointly measures (a) sharpness (Hessian eigenvalue or SAM-style neighbourhood loss), (b) paired-image representation stability (CKA(ϕ(x), ϕ(corrupt(x)))), and (c) OOD accuracy under corruption in the same experiment for any combination of SAM, SWA, and SGD. The relevant pieces exist separately: Kornblith et al. [pid: 726320cd] established paired-image CKA; SAM-ON [pid: fba30c42] measured sharpness alongside OOD accuracy; Zhang et al. [pid: cff1cdb0] used CKA to measure feature diversity in a DG context; but none triangulate all three.

**Why it matters for the RQ:** The RQ's core hypothesis is that CKA stability tracks OOD accuracy more closely than sharpness does after partialling out flatness. This requires measuring all three quantities jointly. Without joint measurement, it is impossible to evaluate whether (i) sharpness and CKA stability are correlated across optimizers, (ii) CKA stability provides additional OOD-predictive information beyond sharpness, or (iii) SAM and SWA differ in CKA stability while being similarly flat.

**Closest existing work:** Kornblith et al. [pid: 726320cd] define and validate CKA but apply it to compare networks trained from different initializations, not clean-vs-corrupted images. Zhang et al. [pid: cff1cdb0] use CKA to quantify feature diversity under different learning rates (0.7882 vs. 0.9822 CKA similarity) in a DG context, but do not pair clean and corrupted images and do not compare SAM to SWA. Mueller et al. [pid: fba30c42] demonstrate that higher sharpness co-occurs with higher OOD accuracy in SAM-ON but do not measure representation stability.

**How our proposed work addresses it:** We compute CKA(ϕ(x), ϕ(corrupt(x))) at the ResNet-18 penultimate layer for all 15 corruption types × 5 severities, averaged across 3 seeds, for SGD, SAM, and SWA. Scatter plots of (sharpness, OOD gain) and (CKA stability, OOD gain) and a partial correlation analysis provide the first joint assessment.

---

## Gap 3: The Causal Status of Sharpness in SAM's OOD Gains Is Unresolved—and One Direct Counter-Example Exists

**What the gap is:** Andriushchenko & Flammarion (ICML 2022) [pid: b698dbfa] demonstrate that convergence to flat minima does not explain SAM's generalization improvement—m-sharpness with small batch size is the key ingredient, not flatness per se. Baek et al. (ICLR 2024) [pid: ad6a428c] show SAM's label-noise gains are driven by Jacobian regularization, not flatness at convergence. Mueller et al. [pid: fba30c42] provide the most direct evidence: SAM-ON achieves better generalization while being sharper (ℓ∞ m-sharpness 0.090 vs. 0.048). Yet no prior work examines whether this sharpness-generalization decoupling holds specifically in the OOD/corruption robustness setting.

**Why it matters for the RQ:** The RQ is motivated precisely by this decoupling. If sharpness reduction alone explains SAM's OOD gains, then SWA (which achieves comparable or lower sharpness by a different mechanism) should match SAM on CIFAR-C. If sharpness is not sufficient—as the above papers suggest—then the excess OOD gain of SAM over SWA (if observed) must be attributed to something else, with representation stability as the proposed candidate.

**Closest existing work:** Andriushchenko & Flammarion [pid: b698dbfa], Mueller et al. [pid: fba30c42], and Baek et al. [pid: ad6a428c] all establish the causal insufficiency of flatness, but each is restricted to i.i.d. generalization settings. Schapiro & Zhao [pid: a4002b51] note the disconnect between theory and OOD empirics and are the most direct predecessor, but use synthetic OOD shifts (rotated/colored MNIST) rather than CIFAR-C. The RQ's study will be the first to probe whether the sharpness-mechanism decoupling holds on the canonical CIFAR corruption benchmark.

**How our proposed work addresses it:** By comparing SAM's OOD accuracy gain over SGD against SWA's gain, under matched sharpness measurement (power-iteration λ_max and SAM-style neighbourhood loss), we test whether residual SAM-vs-SWA OOD differences persist after accounting for their realized sharpness values. The falsification criterion is stated explicitly: if SWA matches SAM on OOD accuracy while both are similarly flatter than SGD, the representation-specific hypothesis is not supported—and that is a valid publishable negative result.

---

## Gap 4: SAM Variants Are Compared on OOD Benchmarks Without SWA as a Non-Perturbation Baseline

**What the gap is:** The flat-minima-for-DG literature compares SAM variants (SAGM, GSAM, DGSAM, SWAD, Lookahead) against each other and against ERM, but never against vanilla SWA as an explicit non-perturbation flat-minima baseline. This conflates two distinct sources of flatness-associated OOD improvement: (a) adversarial perturbation-based sharpness seeking (SAM family) and (b) weight-trajectory-based flat-basin centering (SWA/SWAD). Without SWA as a distinct control, all OOD gains are attributed to the SAM perturbation mechanism.

**Why it matters for the RQ:** SWAD [pid: 4d87a9f6] reports that SWA finds flatter minima than SAM on PACS (local flatness Fγ), yet SAGM [pid: beb8c384] and DGSAM [pid: 0da44af3] both improve over vanilla SAM in DG without including SWA as a control. Kaddour et al. [pid: 0265144c] include SWA in a multi-task study but do not focus on OOD corruption benchmarks. The consequence is that the literature cannot answer whether the SAM perturbation mechanism adds anything to DG/OOD performance beyond what simple weight averaging achieves.

**Closest existing work:** Kaddour et al. [pid: 0265144c] is the closest: they compare SWA, SAM, and WASAM across 42 tasks and find WASAM dominates, suggesting they are complementary. However, their OOD evaluation uses standard CV benchmarks (in-distribution test sets) rather than CIFAR-C corruption benchmarks. SWAD [pid: 4d87a9f6] compares SWAD against both SWA and SAM on DomainBed but finds SWAD (an enhanced SWA variant) beats vanilla SWA, and does not include CIFAR-C evaluation. Zhang et al. [pid: cff1cdb0] compare Lookahead to SWA and SAM on DomainBed but also without CIFAR-C.

**How our proposed work addresses it:** The RQ's three-optimizer design (SGD, SAM, SWA) on CIFAR-C directly fills this gap by providing the first controlled corruption-robustness comparison that includes both a SAM variant and vanilla SWA as a non-perturbation flatness baseline, enabling attribution of OOD gains to perturbation-specific vs. trajectory-averaging effects.

---

## Gap 5: Prior SAM-for-OOD Studies Lack a Representational Explanation, Leaving the Mechanism Unexplained

**What the gap is:** Existing papers that demonstrate SAM's OOD benefits (Schapiro & Zhao [pid: a4002b51], SAM-ON [pid: fba30c42], SWAD/SAGM flatness-for-DG literature) consistently acknowledge that flatness theory does not fully account for the observed gains, but none proposes or tests a representational explanation. Schapiro & Zhao explicitly note that "low sharpness alone does not account for all of SAM's generalization benefits" (citing Wen et al. [pid: 07dbbb95]) and list several SAM implicit biases (lower-rank features, Jacobian regularization, feature balance), but do not examine representation stability under input corruptions.

**Why it matters for the RQ:** If SAM's OOD gains are partly representational—i.e., SAM-trained networks produce more stable feature representations under input corruptions, independent of their loss-landscape flatness—then sharpness measurement alone is a systematically incomplete predictor of OOD accuracy. This framing motivates CKA stability as a complementary diagnostic. The SAM-on-adversarial-robustness paper (Wei et al. [pid: eb9eec79]) proposes that SAM shifts weight toward robust features, providing a feature-level mechanism hypothesis consistent with the RQ; but that paper uses adversarial perturbations rather than corruption robustness. Mueller et al.'s normalization-layer result [pid: fba30c42] is consistent with a representational explanation (normalization layers control feature statistics), but no representation stability measurement is reported.

**Closest existing work:** Wei et al. [pid: eb9eec79] propose the closest mechanistic explanation: SAM improves feature robustness by biasing toward robust (corruption-stable) features via feature-space perturbations. Mueller et al. [pid: fba30c42] provide indirect evidence via normalization-layer perturbation. Neither study measures CKA(ϕ(x), ϕ(corrupt(x))) or correlates representation stability with OOD accuracy across a controlled optimizer comparison. The paired-image CKA approach proposed in Kornblith et al. [pid: 726320cd] has not been applied to the SAM/SWA/SGD comparison on CIFAR-C.

**How our proposed work addresses it:** By computing paired-image CKA stability as a secondary metric alongside sharpness and OOD accuracy for all three optimizers, and by testing whether CKA stability predicts OOD accuracy after controlling for sharpness (partial correlation), this study will be the first to empirically evaluate whether representation stability is a mediating variable in SAM's OOD generalization on corruption benchmarks.
