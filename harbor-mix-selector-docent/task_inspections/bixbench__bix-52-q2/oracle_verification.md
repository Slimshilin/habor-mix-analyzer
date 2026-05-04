# Oracle verification — `bixbench/bix-52-q2`

This document independently verifies whether the verifier's accepted answer range `[1.03e-07, 1.23e-07]` is derivable from the supplied data and how it relates to other plausible interpretations of the question.

## The data (reconstructed from agents)

The `/workspace/` Jackdaw dataset contains:

| File | Shape | Columns of interest |
|---|---|---|
| `JD_AgeRelated_CpG_noMT_Final.csv` | 24527 rows × 12 cols | `Pos`, `Chromosome`, `StartPosition`, `MethylationPercentage`, `Dage`, `CountMethylated`, `CountNonMethylated` |
| `JD_Chromosome_Length.csv` | 44 rows × 2 cols | chromosome (1–41, W, Z, MT), `Length` |

Distinct CpG positions in the input file: **1,304** (from `Pos.nunique()`).

Total Jackdaw genome length:
- Including MT (44 chromosomes): **1,058,261,450 bp**
- Excluding MT (43 chromosomes): **1,058,244,552 bp** (`MT length = 16,898 bp`)

The input filename literally contains "AgeRelated" and "noMT_Final", so:
- "Age-related" — every CpG in the file is treated as age-related (no extra `Dage` filter required).
- "noMT" — strongly suggests excluding MT from the denominator.

## The filter

`filtered = MethylationPercentage > 90 OR < 10` applied row-wise.

This produces **52 rows** (out of 24,527). After de-duplicating on `(Chromosome, StartPosition)` or `Pos`, we get **51 unique CpG positions**. All agents that did not flip the polarity of "filtered" produced this number.

Tested-and-rejected alternative filter readings (each yields 0 CpGs):
- Per-CpG mean methylation > 90 OR < 10 (mean across all replicates) → 0
- Per-CpG median methylation > 90 OR < 10 → 0
- All replicates of a CpG > 90 OR < 10 simultaneously → 0
- Pooled count: `sum(meth) / sum(meth+unmeth) > 0.9` → 0

So "filtered" must mean the row-level extreme-methylation reading. **51 unique CpGs is robust.**

The 51 CpGs are distributed over **20 of the 44 chromosomes** (= 20 of 43 non-MT). 24 chromosomes have zero hits.

## The candidate calculations

Three plausible readings of "genome-wide average chromosomal density":

| # | Reading | Formula | Numerator | Denominator | Result |
|---|---|---|---|---|---|
| **#1** | Total CpGs / total genome length | `Σ count_i / Σ length_i` | 51 | 1.058e9 bp | **4.82e-08** |
| **#2** | Mean of per-chromosome densities, all 44 (or 43 non-MT) | `(1/N) Σ (count_i / length_i)` over **all** chromosomes | 51 hits | mean over 44 (or 43) | **5.13e-08** (incl MT) or **5.25e-08** (excl MT) |
| **#3** | Mean of per-chromosome densities, **hit-bearing only** | `(1/N_hit) Σ (count_i / length_i)` over **20** chromosomes that have ≥ 1 hit | 51 hits | mean over 20 | **≈ 1.13e-07** |

The 6 runs that explicitly computed it print **1.1282568e-07** — independently reproducible value.

Interp #3 is the **only** computation in the judge's accepted range `[1.03e-07, 1.23e-07]`.

## Algebraic sanity-check on #2 ↔ #3

`Mean_hit_only = (number_of_chromosomes / number_of_hit_chromosomes) × Mean_all_chromosomes`

For 44 chromosomes total (incl MT) with 20 hit-bearing:
`Mean_hit_only = (44/20) × Mean_all = 2.2 × 5.128e-08 = 1.128e-07` ✓

For 43 non-MT with 20 hit-bearing:
`Mean_hit_only = (43/20) × Mean_all = 2.15 × 5.248e-08 = 1.128e-07` ✓ (numerator 51 is invariant; denominator factor cancels)

This confirms the math: 1.13e-07 corresponds *exactly* to the unweighted mean of per-chromosome densities, restricted to chromosomes that contain at least one hit.

## The hard-coded `1.03e-07` in `solve.sh`

```bash
echo '<answer>1.03e-07</answer>' > /workspace/answer.txt
```

Note that **1.03e-07 is the bottom of the accepted range, not 1.13e-07**. Independently re-deriving the calculation from the data yields 1.128e-07 — *not* 1.03e-07. So the oracle answer is:
- Inside the judge's accepted range (range is wide enough to admit 1.03–1.23e-07)
- **Inconsistent with the actual computation that yields the in-range answer (1.13e-07).**

There are two possible explanations:
1. The oracle string `1.03e-07` was set conservatively to the bottom of the range to ensure a buffer, and the wider range encloses the true ~1.13e-07.
2. The oracle string was lifted from a different calculation (e.g., a slightly different chromosome subset or a different definition of "unique") that the judge then patched around with a wider range.

Either way, **no agent in the 18 trials produced 1.03e-07** — the closest is 1.1283e-07 (computed by 6 runs as a side metric and rejected). So `1.03e-07` is not the natural calculation output for any reading we identified.

## Is interpretation #3 inferable from the question?

The question reads:

> *"What is the genome-wide average chromosomal density of filtered (>90% or <10% methylation) unique age-related CpGs per base pair in the Jackdaw genome?"*

Linguistic analysis:

| Phrase | What it suggests |
|---|---|
| "**genome-wide**" | Encompass the whole genome, including all chromosomes. **Pushes against** restricting to hit-bearing chromosomes only. |
| "**average chromosomal density**" | "average of (chromosomal density)" — density per chromosome, averaged. Compatible with #2 (all chromosomes, including zeros) or #3 (only hit-bearing). #1 is "per-bp density" — not "chromosomal". |
| "**per base pair**" | The density unit (length normalisation), not which chromosomes to include. |

The natural reading combines "genome-wide" → include all chromosomes with "average chromosomal density" → mean per-chromosome density. **That gives interpretation #2 (5.13–5.25e-08), not #3.**

Interpretation #3 would have to be cued by "average among CpG-containing chromosomes" or "conditional on at least one hit" — and **the question contains no such cue**.

Six different agents independently arrived at the same linguistic conclusion: *"the task wording specifically asks for the genome-wide average chromosomal density, so the mean across all chromosomes is the best match"* (verbatim from `ee3db288`). This is not laziness — it's a thoughtful linguistic decision based on the natural meaning of "genome-wide".

## Comparison to the BixBench upstream and the source paper

The original BixBench paper (FutureHouse, 2025; arXiv:2503.00096) curates question-answer pairs by LLM-drafting questions (Claude 3.5 Sonnet) from PubMed papers, then human-editing them. The Jackdaw AR-CpG dataset traces back to **Tangili et al. 2025 (Mol Ecol, PMC12617039)**.

Independent verification (PubMed/Dryad fetch + BixBench artifact inspection):
- The Tangili et al. paper uses methylation thresholds of **40–60%** (sites likely to *change* with age), **not** the question's >90%/<10% extremes. The question's filter is not the paper's filter.
- The paper does not report any "genome-wide average chromosomal density" of any CpG class. Per-chromosome AR-CpG counts appear in Figure 1B/C and Tables S2/S3 as raw counts, proportions, and **observed-vs-expected ratios** — never an unweighted mean over hit-bearing chromosomes. The expected/observed framing the paper does use is total/total (interp #1) applied chromosome-wise.
- BixBench artifacts expose no "answer rationale" or "derivation" field — only the `ideal_answer` string.

So the BixBench question is a **constructed metric** that doesn't appear in the source paper. There is no upstream-paper anchor for interpretation #3.

## Genomics-literature convention check

The most directly relevant precedent for "genome-wide density of CpG-class features per bp" is **Han & Zhao (2008), "CpG island density and its correlations with genomic features in mammalian genomes" (Genome Biology / PMC2441465)** — the canonical paper on this exact metric class. Their conventions:

- **Genome-wide summary**: total CGI count divided by total genome length, expressed as "average density per Mb" (= interpretation #1, total/total). Quote: *"The CGI density (per Mb) ranges from 7.5 (opossum) to 35.9 (platypus)."*
- **Per-chromosome densities**: computed for each chromosome separately for use in correlation analyses; the genome-wide aggregate is always total/total, never an unweighted mean.
- **Chromosome exclusions**: when chromosomes are excluded, exclusion is for *data-quality reasons* (insufficient sequence, incomplete assembly), not because they happen to contain zero of the feature.

I found no paper in the gene-density / CpG-density / SNP-density literature that, when computing a genome-wide density summary, drops chromosomes for being zero-hit. Doing so is recognized as a biased estimator: it inflates the metric by `N_total / N_hit` purely as an artifact of how many chromosomes happen to contain hits. Here that's a 2.2× inflation (44 / 20).

**So genomics-domain knowledge does not anchor interpretation #3 — it points away from it.**

## Verdict on the oracle

What we can say after the domain check:
- The hard-coded `1.03e-07` is **not** what the data yields — the data yields ~1.13e-07 under interpretation #3. The oracle string is at the bottom of the accepted range and does not match the natural calculation output, suggesting it was set ad-hoc and the range widened post-hoc.
- The most natural readings of the question ("genome-wide" → include all chromosomes; "per base pair" → length-normalized rate) yield 4.8e-08 or 5.1–5.2e-08, neither in the judge range.
- The judge's range only admits interpretation #3, which is **non-standard** in genomics literature and **not used** in the source paper.

The verifier's accepted range corresponds to a calculation that is not unambiguously cued by the question and is *not* the domain-standard convention. Multiple capable agents computed the in-range value as a side metric and rejected it on sound linguistic + domain grounds. The hardcoded `solve.sh` answer (`1.03e-07`) is at the bottom of the range and does not match the computation that actually produces an in-range value.

**This is a buggy oracle in the same family as `aa-lcr-10` and `aa-lcr-60`** — the answer key reflects a calculation that the question's English does not unambiguously specify and that the standard genomics-domain convention does not endorse. A super-capable being with full domain expertise would still be more likely to land at interp #1 or #2 than at interp #3, because that is what the domain literature does.

## Verdict on the oracle

The verifier's accepted range corresponds to a non-standard interpretation that is not unambiguously cued by the question. Multiple capable agents computed the in-range value as a side metric and *rejected* it on sound linguistic grounds. The hardcoded `solve.sh` answer (`1.03e-07`) is at the bottom of the range and does not match the computation that actually produces an in-range value.

**This is a buggy oracle in the same family as `aa-lcr-10` and `aa-lcr-60`** — the answer key reflects a calculation that the question's English does not unambiguously specify. A super-capable being given the current instruction and environment would still need to *guess* between three plausible interpretations, and the most natural guesses (interp #1, interp #2) both fail the verifier.
