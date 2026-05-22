# Section Brief: sec/02_related_work.tex

This brief locks the writer's contract for the Related Work section.

## Target
- **Words**: ~800 (soft ceiling; +10% OK; do NOT exceed 900)
- **Cites**: ~21 cite_keys, all `depth_recommendation` ∈ {core, supporting}
- **Structure**: 5 subsections (`\subsection{...}`), each ~150-170 words, ordered to motivate the gap

## Open with a section command

`\section{Related Work}` — first time the section appears in `main.tex`.

## Subsection structure

### 2.1 Sharpness-Aware Minimization and its Variants (~150 words, ~4 cites)
Open with the SAM formulation [`foret2020_sharpness_aware`] — the two-step min-max neighbourhood loss with default ρ=0.05 for ResNet/CIFAR. Cover the variant family compactly:
- Scale-invariant adaptation [`kwon2021_asam_adaptive`]
- Surrogate-gap refinement [`zhuang2022_surrogate_gap`]
- Perturbation-direction analysis showing the stochastic noise component drives generalization [`li2024_friendly_sharpness`]

Close with one sentence stating that all variants share the assumption that minimizing some form of neighbourhood loss yields flat minima which generalize. This sets up §2.2.

### 2.2 Flatness and Generalization: Theory and Counter-Arguments (~170 words, ~5 cites)
- Keskar et al.'s ε-sharpness as the empirical foundation [`keskar2016_large_batch`]
- **MANDATORY**: Dinh et al.'s reparametrization counter-argument — sharp minima can generalize equivalently to flat ones under coordinate rescaling [`dinh2017_sharp_minima`]
- Jiang et al.'s large-scale validation that sharpness measures are among the strongest empirical predictors of generalization gap [`jiang2019_fantastic_generalization`]
- Petzka et al.'s reparametrization-invariant relative flatness as the partial resolution to Dinh's critique [`petzka2020_relative_flatness`]
- Walter et al. as the recent extension: flatness guarantees only local, not global, adversarial robustness [`walter2025_when_flatness`] (optional — drop if over budget)

Close with one sentence: even granting that flatness correlates with generalization, the question of whether it *causally explains* SAM's specific gains is contested — leading to §2.3.

### 2.3 SAM's Mechanism Is Not Just Flatness (~170 words, ~5 cites) — LOAD-BEARING SUBSECTION
This is the most important subsection — it sets up our gap.
- **MANDATORY**: Andriushchenko & Flammarion — m-sharpness with small batch size is the key ingredient, not flat-minima convergence [`andriushchenko2022_towards_understanding`]
- **MANDATORY**: Wen et al. — theoretical decomposition; SAM minimizes top Hessian eigenvalue only in full-batch limit, which differs from practical mini-batch SAM [`wen2022_how_does`]
- **MANDATORY**: Mueller et al. (SAM-ON) — the direct counter-example: better generalization with higher measured sharpness [`mueller2023_normalization_layers`]
- Baek et al. — SAM's label-noise gains driven by Jacobian regularization, not flatness at convergence [`baek2024_why_is`]
- Schapiro & Zhao — direct predecessor noting "low sharpness alone does not account for all of SAM's generalization benefits" in OOD settings [`schapiro2024_towards_understanding`]

Close with one sentence: these findings collectively motivate the search for a mechanism beyond flatness — but no candidate has been tested on corruption-robustness benchmarks.

### 2.4 OOD Benchmarks and Flat-Minima Optimizers for Domain Generalization (~170 words, ~6 cites)
- CIFAR-C/ImageNet-C corruption benchmarks [`hendrycks2019_benchmarking_neural`]
- Calibration under shift [`ovadia2019_can_you`] — anchors the ECE secondary metric
- DomainBed evaluation discipline [`gulrajani2020_search_lost`]
- **MANDATORY**: SWAD as direct prior; uses weight-averaging variant for DG; finds SWA flatter than SAM on PACS by local flatness Fγ [`cha2021_swad_domain`]
- SAGM extends SAM to DG with gradient matching [`wang2023_sharpness_aware`]
- **MANDATORY (closest comparator)**: Kaddour et al. — the only systematic SAM-vs-SWA comparison with sharpness measurement, but on i.i.d. evaluation [`kaddour2022_when_do`]

Close with one sentence: SWAD reports SWA flatter than SAM (PACS), Kaddour et al. report SAM flatter than SWA (WRN/CIFAR-100); this contradiction is unresolved and has not been examined on CIFAR-C.

### 2.5 Representation Similarity and Our Gap (~140 words, ~2-3 cites)
- CKA as the standard representation-similarity tool [`kornblith2019_similarity_neural`]
- Zhang et al. as the only prior use of CKA in a DG-flat-minima context, measuring feature diversity under different learning rates [`zhang2023_exploring_flat`]

Closing paragraph (~3-4 sentences) stating our specific gap and contribution: **no prior work simultaneously measures sharpness, paired-image CKA stability, and OOD accuracy across SAM, SWA, and SGD on CIFAR-C**. Our work fills this gap, providing the first controlled corruption-robustness comparison that can decompose flatness-attributable and representation-stability-attributable components of SAM's OOD generalization. SWA is included not as a "flatness-only" control — the honest framing is that SAM and SWA are two distinct flatness-oriented optimizers reaching flat minima via different mechanisms.

## Hard mandatory inclusions (do not omit)
1. `dinh2017_sharp_minima` — the reparametrization counter-argument
2. `andriushchenko2022_towards_understanding` — m-sharpness critique
3. `wen2022_how_does` — theoretical mechanism analysis
4. `mueller2023_normalization_layers` — SAM-ON, the load-bearing counter-example
5. `cha2021_swad_domain` — SWAD as direct prior
6. `kaddour2022_when_do` — closest SAM-vs-SWA comparator
7. Closing transition that explicitly states our gap

## Forbidden patterns
- Paragraphs starting with "In recent years", "Recent works have", "It is well-known", "Several papers have"
- Surveying every SAM variant individually (4 maximum)
- Calling SWA "flatness-only" / "pure flatness" / "flatness without SAM" — use "flat-minima-oriented control" or "non-perturbation flat-minima baseline"
- Causal language on correlational evidence — use "is associated with" / "co-occurs with" / "exhibits", not "X causes Y" or "the model uses X"
- Definitive verbs ("establishes", "proves", "demonstrates that") for preprints unless work is at NeurIPS/ICML/ICLR/CVPR top-tier. For the corpus: most cited works are peer-reviewed; check notes/{paper_id}.json:venue and publication_status_observed before using definitive verbs.

## Cite_keys allowed (20 primary + 3 optional)
**Primary** (use most of these — aim for ~20):
- foret2020_sharpness_aware
- kwon2021_asam_adaptive
- zhuang2022_surrogate_gap
- li2024_friendly_sharpness
- keskar2016_large_batch
- dinh2017_sharp_minima
- jiang2019_fantastic_generalization
- petzka2020_relative_flatness
- andriushchenko2022_towards_understanding
- wen2022_how_does
- mueller2023_normalization_layers
- baek2024_why_is
- schapiro2024_towards_understanding
- hendrycks2019_benchmarking_neural
- ovadia2019_can_you
- gulrajani2020_search_lost
- cha2021_swad_domain
- wang2023_sharpness_aware
- kaddour2022_when_do
- izmailov2018_averaging_weights
- kornblith2019_similarity_neural

**Optional** (use only if word budget permits):
- schneider2020_improving_robustness — BN adaptation caveat
- walter2025_when_flatness — flatness/adversarial counter-extension
- zhang2023_exploring_flat — CKA-in-DG precedent

## Notes on cite groupings
Group efficiency variants (du2021_efficient_sharpness, liu2022_towards_efficient) as a single comparative cite if mentioned, e.g. "efficiency-oriented variants [a, b]". Do **not** dedicate sentences to each.

## Style constraints (from writer.md)
- PhD-level analytical prose
- Organise around claims, not papers
- Every `\cite{key}` followed within 3 lines by `% src: <paper_id> pp.<page> (<notes_field>) — "<≤20 word evidence>"`
- Grouped citations `\cite{a, b}` need ONE `% src:` line per cite_key (separate lines)
- IEEE numerical citation style (handled by `\bibliographystyle{style/ieee}` in main.tex)
- No `%%VERIFY%%` markers in this section (lit review is fully traceable; mark with %%VERIFY%% only if you genuinely cannot verify a claim)
