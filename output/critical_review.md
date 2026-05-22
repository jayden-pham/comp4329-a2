# Critical Review — `output/sec/02_related_work.tex`

Adversarial PhD-examiner critique. Scope: Related Work section only (Stage B). Stage F will receive a full-paper review; experiment-rigor section (F) is intentionally skipped here.

---

## A. Overclaims and weak causal inference

**A1. Line 21 — Jiang et al. described as "partially rehabilitate the empirical claim".**
> "Jiang et al.\ partially rehabilitate the empirical claim, showing that PAC-Bayes and Keskar sharpness are associated with the generalisation gap more strongly than 40 alternative complexity measures across $10^4$ networks, while noting explicitly that the correlation is not causal"

Cited work: `jiang2019_fantastic_generalization` (ICLR 2020, peer-reviewed, canonical_status = published). The notes say the measures perform "best overall" — but the prose adds an interpretive frame ("rehabilitate") that is the writer's editorial reading, not the paper's claim. Jiang et al. never frame their result as a rehabilitation of Keskar against Dinh; they explicitly disclaim causality. The notes also state Jiang's evidence_strength is `correlational`.
**Severity:** mild. The hedge ("partially") is honest and the explicit "correlation is not causal" rider is preserved. **Proposed rewrite:** "Jiang et al.\ provide the largest correlational rebuttal, finding that PAC-Bayes and Keskar sharpness are the strongest of 40+ complexity measures predicting the generalisation gap across $10^4$ networks, while explicitly noting the result is associational, not causal."

**A2. Line 23 — Petzka described as "partially resolve Dinh's critique".**
> "Petzka et al.\ partially resolve Dinh's critique by deriving a reparametrisation-invariant relative flatness..."

Cited work: `petzka2020_relative_flatness` (NeurIPS 2021). Notes show the measure is invariant *to linear* reparameterizations only, and depends on locally constant feature labels — a strong assumption. The phrase "partially resolve" is appropriately hedged, but the prose drops both caveats. The notes also say the measure "outperforms state-of-the-art flatness measures in correlation with generalization on CIFAR-10" — observational, not a proof of resolution.
**Severity:** mild. **Proposed rewrite:** "Petzka et al.\ derive a flatness measure invariant to linear reparametrisations of ReLU networks under the assumption that feature-space labels are locally constant; this measure correlates with the generalisation gap more strongly than the Hessian trace on CIFAR-10, partially addressing Dinh's critique within its assumptions."

**A3. Line 31 — Andriushchenko stated as "show that the PAC-Bayes-and-flat-minima account is incomplete".**
> "Andriushchenko and Flammarion show that the PAC-Bayes-and-flat-minima account is incomplete: only m-SAM with small batch size ($m=128$) substantially improves test error on ResNet-18/CIFAR-10..."

Cited work: `andriushchenko2022_towards_understanding` (ICML 2022, peer-reviewed). The note's main_claims field uses exactly the phrase "incomplete", so the framing is faithful. However, the prose says "for diagonal linear networks SAM provably selects sparser solutions than GD". The notes confirm this is *theoretically* proved for diagonal linear nets only and the deep-net extension is empirical — but this is correctly bounded by the qualifier "for diagonal linear networks". **Severity:** OK. This is appropriately hedged. Note the traceability warning at line 31 about the verb "prove" — the verb is fine because the proof scope is explicitly bounded to diagonal linear networks.

**A4. Line 35 — SAM-ON described as "the most direct empirical counter-example".**
> "The most direct empirical counter-example is SAM-ON: perturbing only the $\sim 0.1\%$ of parameters in normalisation layers achieves $84.19\%$ on WRN-28-10/CIFAR-100 versus $83.11\%$ for SAM-all while measuring higher $\ell_\infty$ $m$-sharpness ($0.090$ vs.\ $0.048$)"

Cited work: `mueller2023_normalization_layers` (NeurIPS 2023, peer-reviewed). Numbers verified against notes. The framing "most direct empirical counter-example" is the writer's editorial superlative — defensible given the gaps.md treats this paper exactly as the load-bearing counter-evidence, but a sterner reviewer would prefer "the single most cited counter-example in the recent literature is SAM-ON, which..." with attribution. **Severity:** low; framing is faithful to source. **Proposed minor rewrite:** "The most direct counter-example reported in the literature is SAM-ON: ..."

**A5. Line 37 — Baek et al. described as "attribute SAM's label-noise robustness to perturbation of the network Jacobian, not flatness at convergence".**
> "Baek et al.\ attribute SAM's label-noise robustness to perturbation of the network Jacobian, not flatness at convergence, with J-SAM matching SAM at $69.17\%$ under 30\% label noise..."

Cited work: `baek2024_why_is` (ICLR 2024). Notes confirm the J-SAM = 69.17% vs L-SAM = 54.13% numbers, and the qualification "in deep networks" / "label noise setting". The prose drops the "label noise" scope of the claim until the comma — a careful reader can parse it, but it would be cleaner to scope the attribution upfront. **Severity:** low. **Proposed rewrite:** unchanged; the scope clause "label-noise robustness" already appears in the first noun phrase.

**A6. Line 39 — Schapiro & Zhao numbers presented without caveat about benchmark difficulty.**
> "Schapiro and Zhao report SAM and FriendlySAM gains of $4.76\%$ and $8.01\%$ on zero-shot OOD over Adam across four shift benchmarks"

Cited work: `schapiro2024_towards_understanding` (arXiv 2024, NOT peer-reviewed — canonical_status: preprint). Notes confirm the 4.76% / 8.01% numbers AND limit the benchmark to "Color MNIST, Rotated MNIST, Cover Type, Portraits" with modest CNN/MLP architectures, "not evaluated on CIFAR-C or ImageNet-C". The prose hides the benchmark composition — a reader will assume CIFAR/ImageNet-scale, which inflates the perceived effect size. **Severity: moderate.** Combined with the peer-review issue (see §E), this is the single most polishable line in the section. **Proposed rewrite:** "Schapiro and Zhao (arXiv preprint, 2024) report SAM and FriendlySAM gains of $4.76\%$ and $8.01\%$ over Adam in a zero-shot OOD study on four small-scale benchmarks (rotated/colored MNIST, Cover Type, Portraits), while explicitly noting that ``low sharpness alone does not account for all of SAM's generalization benefits.''"

**A7. Line 51 — SWAD numbers presented as definitive.**
> "SWAD couples dense overfit-aware stochastic weight averaging with a flatness bound and lifts the five-benchmark DomainBed average from $63.3\%$ (ERM) to $66.9\%$; on PACS it reports SWA flatter than SAM by the local flatness $F_\gamma$"

Cited work: `cha2021_swad_domain` (NeurIPS 2021). Numbers and PACS Fγ claim verified. Note that the comparison is *SWA vs SAM* (not SWAD vs SAM) — phrasing is correct ("it reports SWA flatter than SAM"). **Severity:** OK.

**A8. Line 67 — Final sentence overclaims decomposition.**
> "this controlled comparison decomposes OOD gains into flatness-attributable and representation-stability-attributable components."

This is not yet supported by experiments and steps over `briefs/positioning.md`, which insists this is *exploratory associational evidence*, not mediation/decomposition. The very next subsection in the brief warns against "mediation language". **Severity: high — directly contradicts the locked positioning brief.** **Proposed rewrite:** "this controlled comparison provides the first joint measurement of sharpness, paired-image CKA stability, and OOD accuracy across SAM, SWA, and SGD on CIFAR-C, enabling an exploratory association analysis between each mechanistic signal and OOD gain." (See also §H1.)

---

## B. Missing counterarguments and unaddressed limitations

**B1. Dinh's critique is mentioned but its bite is underplayed.**
Line 19 quotes Dinh's "observationally equivalent" result. The next sentence (line 21) introduces Jiang et al. with "partially rehabilitate the empirical claim" — but the prose does not say *which* part of Dinh's argument remains unanswered. Jiang's measures are still parametrisation-dependent; they correlate empirically but do not resolve the theoretical objection. As written, Dinh appears to be defeated by Jiang and then Petzka. The brief calls Dinh "MANDATORY" precisely because the critique is foundational. **Fix:** add one half-sentence after the Jiang citation, e.g. "though the parametrisation dependence Dinh identifies is left unresolved by these empirical results."

**B2. Andriushchenko's *null findings* are framed as a positive result.**
The note `b698dbfaf9b...` includes the null finding that "n-SAM and random perturbations do not [substantially improve generalization]" — line 31 captures this. But the null finding for `n-SAM` (full-batch SAM, the closer analogue of what Wen et al. theoretically characterise) is given equal weight as the positive m-SAM finding when it deserves more emphasis: it directly *contradicts the full-batch flat-minima narrative* the next sentence (line 33, Wen et al.) characterises mathematically. The two papers should be bridged: "Andriushchenko shows full-batch n-SAM does not generalise; Wen et al. nonetheless characterise the full-batch limit, leaving the practical mini-batch regime (which generalises) explained by *neither* analysis." The prose hints at this on line 33 ("leaving the practical mini-batch regime characterised by neither limit") but does not flag that this is the *deeper* counterargument against flatness.

**B3. The Schneider/BN-adaptation caveat is missing.**
`synthesis/themes.json:ood_corruption_benchmarks` flags Schneider et al. (paper_id `aa12f44062c06f90526cb128f10e829846145b1f`) as raising "the question of whether any optimizer-level OOD gain partly reflects incidental BN adaptation" — and notes this is "relevant to interpreting SAM-vs-SWA comparisons on CIFAR-C since both methods affect BN behavior differently." A note file exists for Schneider, and the brief lists `schneider2020_improving_robustness` in the optional pool. Given the central role of normalisation layers in Mueller et al. (cited on line 35), the BN-adaptation counterargument deserves at least one sentence in §2.4 to pre-empt the reviewer who asks "isn't this just BN statistics?" **Fix:** add one sentence to §2.4 (probably after the calibration sentence) along the lines of: "Schneider et al.\ further show that test-time BatchNorm-statistic adaptation alone substantially improves CIFAR-C accuracy, a confound any optimiser-level OOD comparison on this benchmark must acknowledge."

**B4. Kaddour vs SWAD contradiction is stated but not interpreted.**
Line 57 says "SWAD reports SWA flatter than SAM on PACS, whereas Kaddour et al.\ report SAM flatter than SWA on CIFAR-100; this contradiction has not been examined on CIFAR-C." This is sharp and good. But the prose stops one beat short: *why* might these two be inconsistent? Different flatness measures (Fγ vs λmax), different benchmarks (PACS vs CIFAR-100), different architectures (ResNet-50 pretrained vs WRN-28-10 from scratch). The current sentence reads as "isn't this odd" rather than "here is exactly which methodological axis must be held constant to resolve it" — which is the bridge to the contribution. **Fix:** "These results disagree on both the flatness measure (local Fγ vs Hessian λmax) and the benchmark (PACS vs CIFAR-100); whether the SAM-vs-SWA flatness comparison reverses again on CIFAR-C is an open question."

**B5. CKA's known limitations are not flagged.**
Line 61 introduces CKA as the "standard representation-similarity tool" with the 99.3% layer-matching number. The notes (`726320cdbd...`) explicitly list a limitation: "CKA is invariant to isotropic scaling but not non-isotropic scaling, so different parametrisations can still affect the measured similarity" — which is *exactly* Dinh's reparametrisation point applied to CKA itself. Since the gap statement (line 67) hangs on CKA as the measurement instrument, the paper owes one sentence acknowledging that CKA's robustness is not parametrisation-invariant. Otherwise a reviewer can return Dinh's objection against the proposed solution. **Fix:** add to §2.5: "CKA is invariant to orthogonal transformation and isotropic scaling but not to non-isotropic rescaling; the same parametrisation caveat that motivated Petzka's relative flatness applies, albeit attenuated when networks share architecture and initialisation distribution."

---

## C. Synthesis quality

**C1. §2.1 (Sharpness-Aware Minimization and its Variants) reads as a list.**
> "SAM formalises ... \cite{foret2020_sharpness_aware}. ASAM introduces ... \cite{kwon2021_asam_adaptive}. GSAM augments ... \cite{zhuang2022_surrogate_gap}. F-SAM decomposes ... \cite{li2024_friendly_sharpness}. All four share the assumption..."

Four sentences, four papers, one sentence per paper — this is the canonical "paper-by-paper" pattern. The closing sentence makes them cohere via a single shared assumption, but the body is a citation parade. The brief permitted "≤4 variants compactly" — the writer hit the cap but did not *synthesise*. A better organisation would group: (i) formulation [Foret], (ii) two variants addressing weaknesses in the sharpness measure [ASAM scale-invariance; GSAM surrogate-gap unreliability], (iii) one variant identifying the operative perturbation component [F-SAM], with topic sentences distinguishing the categories. **Fix:** prepend a topic sentence such as "SAM is a family rather than a single algorithm." Then group ASAM+GSAM as "two variants refine the sharpness measure itself..." and treat F-SAM as the connector to §2.3.

**C2. Missed cross-theme bridge: ASAM ↔ Dinh.**
`themes.json` cross_theme_bridges lists ASAM as bridging `sam_formulation_variants` and `flatness_generalization_theory` because it directly addresses Dinh's reparametrisation critique with scale-invariant adaptive sharpness. The current §2.1 sentence on ASAM mentions "neutralising the parameter-rescaling pathology" — which is good — but does not explicitly name Dinh, so the bridge to §2.2 is implicit. A reader who skims §2.1 then encounters Dinh fresh in §2.2 will not realise ASAM was already an answer. **Fix:** rewrite line 7 to forward-reference Dinh: "ASAM introduces a scale-invariant adaptive sharpness whose Kendall rank correlation with the generalisation gap rises from $0.174$ to $0.636$, neutralising the parameter-rescaling pathology that Dinh et al.\ (§2.2) identify as a fundamental obstacle to fixed-radius measures \cite{kwon2021_asam_adaptive}." This single edit turns §2.1 from list to argument.

**C3. Missed cross-theme bridge: GSAM as mechanistic critique.**
`themes.json` bridges GSAM to both `sam_formulation_variants` AND `sam_mechanism_critique` ("argument that SAM's perturbed loss does not reliably minimise sharpness"). Currently GSAM appears only as a variant (§2.1), and the GSAM-as-critique reading is missing. Either the §2.1 sentence should foreshadow the §2.3 line ("low perturbed loss can coexist with sharp curvature" — which is already in the §2.1 sentence! great), or §2.3 should briefly remind the reader that this critique has already appeared. **Status:** the §2.1 sentence already includes the critique observation. This is OK, just under-emphasised.

**C4. SAM-ON's variant-status is not surfaced.**
`themes.json` lists Mueller et al. as bridging variants ↔ critique. The §2.3 sentence treats it purely as a critique-side data point. This is fine — but a reviewer could ask "isn't SAM-ON also a SAM variant, and shouldn't it appear in §2.1?" The current organisation chooses one home for the paper, which is a legitimate authorial decision. **Status:** acceptable, but the writer could pre-empt by saying "SAM-ON, itself a SAM variant restricted to normalisation parameters, provides the most direct counter-example..." — adds one phrase, prevents the question.

**C5. §2.4 is closer to a list than §2.1.**
Six sentences, six papers (Hendrycks → Ovadia → DomainBed → SWAD → SAGM → Kaddour), plus the closing contradiction. Five of the six sentences begin with a noun-phrase subject "X et al." or "X" + verb. The closing contradiction sentence rescues the paragraph but each individual line stands alone. A topic sentence ("The OOD literature has converged on three benchmarks and two flat-minima families ...") would organise the cluster. **Fix:** rewrite the opening sentence of §2.4 to take ownership of the structure, e.g. "OOD evaluation for flat-minima optimisers has converged on a small set of benchmarks and a contested empirical picture."

**C6. §2.5 closing paragraph mixes contribution claim with method claim.**
Line 67 packs: (i) the joint-measurement gap, (ii) the contribution claim, (iii) the SAM-vs-SWA mechanism distinction, (iv) a decomposition promise. This is dense — four ideas in one sentence-and-a-half. Either it should be one short, sharp gap statement (and let §1 Introduction handle the contribution language), or it should be broken into two sentences with a clear "what is missing → what we do" structure. (See A8 for the decomposition issue.) **Fix:** split into two sentences; cut the "decomposes ... attributable" language; promote the gap statement to a tight thesis sentence.

---

## D. Coverage and balance

**D1. Core papers from `synthesis/themes.json` — all present.** I cross-checked against `core_papers` for each theme:

- `sam_formulation_variants` core: Foret ✓, Kwon ✓, Zhuang ✓, F-SAM (`bf109c1c`/`ce871754` — same paper, see notes) ✓.
- `sam_mechanism_critique` core: Andriushchenko ✓, Mueller ✓, Baek ✓, Wen ✓. Note: paper `11adeccf` listed in the theme is *not* cited; it's marked supporting in the brief (not mandatory) and missing is acceptable.
- `flatness_generalization_theory` core: Keskar ✓, Dinh ✓, Jiang ✓, Petzka ✓.
- `ood_corruption_benchmarks` core: Hendrycks ✓, Ovadia ✓, Gulrajani ✓.
- `flat_minima_ood_methods` core: SWAD ✓, SAGM ✓, Kaddour ✓, Schapiro & Zhao ✓.
- `weight_averaging_flat_minima` core: Izmailov (SWA) ✓.
- `representation_similarity_tools` core: Kornblith ✓.

Coverage is complete. No `depth_recommendation: core` paper is omitted.

**D2. Balance across subsections.** Word counts are roughly balanced — §2.1 (~130w), §2.2 (~190w), §2.3 (~210w), §2.4 (~200w), §2.5 (~150w). §2.3 is the load-bearing subsection and rightly the longest, matching the brief.

**D3. Single-paper dependence.** §2.5 leans heavily on Kornblith (1 of 3 cites) and Zhang (the CKA-in-DG precedent). The gap claim ultimately rests on the absence of prior work, so single-paper dependence is unavoidable. **Status:** acceptable for a "gap" subsection.

**D4. Closing gap statement specificity.** Line 67 names the gap concretely: "jointly measures sharpness, paired-image CKA stability $\mathrm{CKA}(\phi(x),\phi(\mathrm{corrupt}(x)))$, and OOD accuracy across SAM, SWA and SGD on CIFAR-C." This is specific enough that another team could replicate the contribution test. **Status:** good. (See A8 for the overclaim issue with the following sentence.)

**D5. Optional `walter2025_when_flatness` is included; `schneider2020_improving_robustness` is not.** The brief lists Schneider as optional and warns about BN-adaptation. Given the close fit to §2.4 and the moderate budget headroom (the section is well under 900w), including Schneider would strengthen B3. Status: optional but recommended.

---

## E. Peer-review calibration (HIGH-PRIORITY)

I list every load-bearing claim grounded SOLELY in preprint (canonical_status ≠ peer-reviewed) sources.

**E1. Schapiro & Zhao — preprint, load-bearing.**
> Line 39: "Schapiro and Zhao report SAM and FriendlySAM gains of $4.76\%$ and $8.01\%$ on zero-shot OOD over Adam across four shift benchmarks, while explicitly noting that ``low sharpness alone does not account for all of SAM's generalization benefits''"

Canonical status per notes: `arXiv preprint arXiv:2412.05169v1, submitted December 2024`. Not peer-reviewed. This citation closes §2.3 (the load-bearing subsection) and supplies the verbatim quotation that the paper's central thesis pivots on. The role is *load-bearing*. The brief itself flagged that "definitive verbs" should be avoided for preprints; the verb here is "report" which is appropriately hedged. **Issue:** the prose does not attribute the work as a preprint, so a reader who does not check the bibliography assumes peer-reviewed standing. **Fix:** either (a) introduce the work with the explicit attribution "the preprint of Schapiro and Zhao reports..." or "in a recent preprint, Schapiro and Zhao report...", or (b) add a parenthetical "(arXiv preprint, 2024)". The quotation should also be attributed as a direct quote with quotation marks (already done). The companion of Wen et al. (Schapiro's quote is *of* Wen et al.) — note that the section cites `wen2022_how_does` directly (line 33) which is *also* a preprint (notes: "arXiv preprint v2"), so the quote-of-a-preprint-via-a-preprint chain should be made transparent.

**E2. Wen et al. — preprint, load-bearing for the mechanism story.**
> Line 33: "Wen et al.\ report that full-batch SAM tracks Riemannian gradient flow on $\lambda_{\max}$ of the Hessian, while stochastic batch-size-1 SAM minimises an average-direction sharpness proportional to the Hessian trace..."

Canonical status per notes: `arXiv preprint v2 (arXiv:2211.05729v2, 5 Jan 2023)`. Not peer-reviewed. Verb used is "report" — properly hedged. Theoretical results are also formal mathematical theorems (evidence_strength: theoretical), so the citation is robust regardless of peer-review status. **Issue:** the central characterisation of "what SAM minimises" — which underpins §2.3's whole argument — is grounded entirely in a preprint. The prose does not flag this. **Fix:** parenthetical "(preprint, 2022)" or rephrase as "Wen et al.\ (preprint) prove..." — given the theoretical nature, "prove" is acceptable here.

**E3. Walter et al. — preprint, supporting role.**
> Line 25: "Walter et al.\ report a complementary limit: flatness implies a local but not a global robustness radius..."

Canonical status: `arXiv preprint arXiv:2510.14231v1, submitted October 2025`. Not peer-reviewed. Verb "report" is appropriately hedged. Role is supporting (one sentence). The 2025 date will also raise eyebrows for a reader in 2026 — a peer-reviewed version may exist or appear before the paper is finalised. **Fix:** attribute as preprint; consider replacement at Stage F if a peer-reviewed version surfaces, or drop if word budget tightens.

**E4. Zhang et al. — preprint, supporting role.**
> Line 65: "Zhang et al.\ provide the only prior pairing of CKA with flat-minima analysis in a DG setting..."

Canonical status: `arXiv preprint arXiv:2309.06337v1, submitted to IEEE TKDE`. Submitted but not yet accepted at the snapshot time of the notes. Role: supporting; the claim "only prior pairing of CKA with flat-minima analysis in a DG setting" is a coverage claim (negative existential), which is *less* dangerous than a positive empirical claim — but the verb "provide" is mildly definitive. The verb is OK. **Fix:** attribute as preprint or update venue if TKDE acceptance has occurred by submission time.

**E5. Definitive verb warnings from traceability_report.md.**
The verb "establish" appears twice on lines 61 and 63 with `kornblith2019_similarity_neural` (ICML 2019, peer-reviewed) and `izmailov2018_averaging_weights` (UAI 2018, peer-reviewed). Both are peer-reviewed top-tier venues — the verb is appropriate. **Status:** no action needed; these warnings are false positives.

**Summary of E:** the heaviest preprint exposure is on lines 33 (Wen) and 39 (Schapiro & Zhao), which together carry the §2.3 closing argument. Both should be explicitly attributed as preprints. The current prose treats them as ordinary citations and a reviewer who polices peer-review calibration will flag this. This is the single most impactful revision in the section.

---

## F. Experiment rigor (Stage F) — skipped.

No experiments yet. Will be revisited at Stage F.

---

## G. Academic writing defects

**G1. Filler / hedging without substance.**

- Line 13: "All four share the assumption that minimising some surrogate of neighbourhood loss locates flat minima that generalise."
  — "All four" is fine; "some surrogate of" is filler (you mean "a surrogate"). Cut "some".
- Line 27: "Even granting this association, whether flatness causally explains SAM's specific gains is contested."
  — "Even granting this association" is a load-bearing transition and is OK. But "specific gains" is filler; SAM has gains, not specific-gains. Cut "specific".
- Line 41: "These results collectively motivate a mechanism beyond flatness, but no candidate has been tested on the canonical corruption benchmarks."
  — "collectively" is filler. The five preceding sentences are already presented together; the reader knows they are collective. Cut.

**G2. Repeated sentence structures.**

- §2.4 has six consecutive sentences whose subject is a proper-noun work or a possessive citation construction: "CIFAR-10-C... define the standard...", "Ovadia et al.\ show...", "The DomainBed framework formalises...", "SWAD couples...", "SAGM extends...", "The closest comparator is Kaddour et al., who benchmark...". This is the strongest list-pattern in the section. (See C5.)
- §2.3 has five "X et al.\ \[verb\]..." constructions: "Andriushchenko and Flammarion show", "Wen et al.\ report", "Baek et al.\ attribute", "Schapiro and Zhao report". Only SAM-ON breaks the pattern ("The most direct empirical counter-example is..."). Variety is acceptable but the pattern is detectable; consider rewriting one to invert subject and object ("The Jacobian, not flatness, explains SAM's label-noise robustness in Baek et al.'s decomposition...").
- §2.5 — three out of three sentences open with "X et al.\ ...".

**G3. Paragraphs without topic sentences.**

- §2.1 (line 5): "SAM formalises generalisation as a min-max neighbourhood objective..." — this is content, not a topic sentence. A topic sentence would say *what the paragraph is about* before plunging into citations. Same critique applies to §2.2, §2.3, §2.4. Only §2.5 has an implicit topic (CKA + the gap).
- This is partly an IEEE-conference convention (start with the most informative statement) and partly a stylistic choice. A reviewer may not flag it, but the prose would be stronger if §2.3 opened with: "SAM's mechanism remains contested even when its generalisation benefit is granted." — and *then* introduces Andriushchenko.

**G4. Tense consistency.** Mostly present tense ("SAM formalises", "ASAM introduces"), which is correct IEEE convention. One slip: line 23 "Petzka et al.\ partially resolve Dinh's critique by deriving..." — "deriving" is fine but the parallel construction with §2.2's other sentences uses simple-present verbs ("counter", "rehabilitate"). **Status:** minor, no fix needed.

**G5. IEEE template compliance.**

- Citation density is high but the brief permits ~21 cites — current count is 22, fine.
- Numerical figures use IEEE-style decimal points and no thousands separator (`$10^4$`, `0.174`, `0.636`, `84.19\%`) — consistent.
- The em-dash ("Uncanny Valley" regions) and double-quotes around `"Uncanny Valley"` look correct. The two backtick quotes ``low sharpness alone does not account...'' on line 39 are LaTeX-correct.
- **Issue:** the section's penultimate-layer notation `$\mathrm{CKA}(\phi(x),\phi(\mathrm{corrupt}(x)))$` on line 67 introduces $\phi$ and $\mathrm{corrupt}(\cdot)$ without defining them. Related Work is normally not where notation is introduced; this should either be moved to Method, or one short clause should gloss "(for embedding $\phi$ and corruption function $\mathrm{corrupt}(\cdot)$)". **Fix:** rewrite as "paired-image CKA stability between embeddings of clean and corrupted inputs" — prose, no math — and reserve the formal notation for the Method section.

**G6. Discourse markers.**

- Line 41 "These results collectively motivate..." — good link to §2.4.
- Line 43 §2.4 opens with "CIFAR-10-C, CIFAR-100-C and ImageNet-C define..." — no discourse link to §2.3. This is a section-to-section gap (jump from "mechanism debate" to "benchmark infrastructure"). A one-clause bridge would help: "Adjudicating these mechanism debates on OOD benchmarks requires shared evaluation infrastructure." This problem is also visible at the §2.2→§2.3 boundary, where "Even granting this association..." does the bridging job — that bridge is *better* than the one missing at §2.3→§2.4.

---

## H. Intellectual coherence

**H1. Order of subsections.** §2.1 (variants) → §2.2 (flatness theory) → §2.3 (mechanism critique) → §2.4 (OOD benchmarks) → §2.5 (CKA + gap). This order matches the brief and builds toward the gap. The bridges are good at §2.2→§2.3 and §2.4→§2.5. The §2.3→§2.4 transition is weaker (see G6). **Status:** order is correct, transitions can be tightened.

**H2. Gap statement vs positioning brief.** The positioning brief says: "**decomposing** whether SAM's OOD gain over SGD is fully accounted for by sharpness reduction, or whether residual gains require an additional explanation grounded in representation stability." It also says SWA is "deliberately **not** described as a 'flatness-only' or 'pure flatness' control" and the framing is *exploratory*, not mediation/causal.

The current §2.5 closing sentence ("decomposes OOD gains into flatness-attributable and representation-stability-attributable components") **overclaims relative to positioning.md**. "Decomposes ... into attributable components" sounds like mediation analysis or causal decomposition. The positioning brief explicitly forbids this framing. The Method/Analysis section says "framed as exploratory associational evidence, not confirmatory causal mediation." This contradiction is a serious coherence issue. **Fix:** see A8. The repair must use words like "jointly measure", "compare", "exploratory association", not "decompose into components".

**H3. SWA framing is consistent with the brief.** The section calls SWA a "non-perturbation flat-minima control" (line 63) and "non-perturbation flat-minima baseline" (line 67), and "trajectory averaging" (line 67) — matches the brief's preferred terminology. **Status:** good.

**H4. The §2.5 contribution claim previews the experiment.** The gap statement names sharpness + CKA + OOD jointly, on SAM/SWA/SGD, on CIFAR-C — which matches `RESEARCH_CONTEXT.md` exactly. **Status:** good.

---

## I. Top 5 highest-priority revisions

1. **Line 67 — repair the decomposition overclaim.** Replace "this controlled comparison decomposes OOD gains into flatness-attributable and representation-stability-attributable components" with an exploratory-association framing. This sentence directly violates the locked positioning brief and will be the easiest reviewer hit if it stays. (See A8, H2.)

2. **Lines 33 and 39 — attribute preprints.** Wen et al. (`wen2022_how_does`) and Schapiro & Zhao (`schapiro2024_towards_understanding`) are both arXiv preprints carrying load-bearing claims in §2.3. Each needs an explicit "(preprint, YYYY)" or "in a recent preprint, X et al.\ ..." attribution. The Schapiro & Zhao numbers (4.76%/8.01%) should also gain a one-clause caveat about the benchmark composition (rotated/colored MNIST etc., not CIFAR-C). (See E1, E2, A6.)

3. **§2.1 — make it a synthesis, not a list.** Add a topic sentence ("SAM is a family rather than a single algorithm.") and forward-reference Dinh on the ASAM line ("...neutralising the parameter-rescaling pathology that Dinh et al.\ (§2.2) identify..."). This single edit turns four sentences from a roll-call into an argument and creates the cross-theme bridge the synthesis demands. (See C1, C2.)

4. **§2.4 — add the Schneider/BN-adaptation caveat (if budget permits) or at least gesture at it.** The brief lists `schneider2020_improving_robustness` as optional; given the load-bearing role of normalisation in Mueller's §2.3 sentence and the centrality of BN behaviour to SAM-vs-SWA on CIFAR-C, omitting Schneider creates a reviewer-attack surface. One sentence in §2.4 (after Ovadia/before DomainBed) would cover the BN-adaptation confound. (See B3, D5.)

5. **Line 67 — split the closing sentence into two: gap, then promise.** Currently one sentence packs the gap statement, the contribution claim, the SAM-vs-SWA mechanism distinction, and the decomposition promise. Break into two: (i) "No prior work jointly measures sharpness, paired-image CKA stability, and OOD accuracy across SAM, SWA, and SGD on CIFAR-C." (ii) "SAM and SWA reach flat regions through adversarial perturbation and trajectory averaging respectively; our study tests whether their geometric and representational signatures track OOD accuracy differently." Drop the math notation `$\mathrm{CKA}(\phi(x),\phi(\mathrm{corrupt}(x)))$` — move to Method. (See A8, C6, G5.)

---

## Summary verdict

This section is structurally sound, citation coverage matches the synthesis, mandatory inclusions (Dinh, Andriushchenko, Wen, Mueller, SWAD, Kaddour) are all present and accurately characterised, and the closing gap claim is specific enough to be testable. The most damaging issues are the line-67 decomposition overclaim (which contradicts the locked positioning brief) and the un-attributed preprint citations to Wen and Schapiro & Zhao (which together carry the §2.3 mechanism argument). With those two repairs plus a topic sentence on §2.1 and the optional Schneider sentence in §2.4, the section is ready for submission. As currently drafted, a peer reviewer would request revisions on the framing and preprint calibration but would not reject — the substance is well-founded.
