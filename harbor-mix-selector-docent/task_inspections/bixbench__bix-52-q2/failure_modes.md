# Failure-mode taxonomy — `bixbench/bix-52-q2`

## Bucket counts (n=18)

| # | Pathway | Trials | Surface cause | Root cause |
|---|---|---|---|---|
| 1 | Computed total / total ≈ 4.82e-08 (interp #1) | 8 | Answer outside judge range `[1.03e-07, 1.23e-07]` | **Question ambiguity + oracle bias to non-standard interp #3.** Agents read "genome-wide" → "across the whole genome" → total / total. |
| 2 | Computed mean-of-per-chromosome-densities ≈ 5.13–5.25e-08 (interp #2) | 7 | Answer outside judge range | **Question ambiguity.** Agents read "average chromosomal density" → mean across chromosomes (incl. zero-hit ones). 6 of these 7 explicitly *computed* the in-range answer 1.13e-07 as a side metric and **rejected it** on linguistic grounds. |
| 3 | Polarity flip on "filtered" → 1253 CpGs → 1.184e-06 | 1 | Answer ~10× too high | **Genuine semantic ambiguity in "filtered"**: kept = retain extreme-methylation CpGs (the 51) vs. removed = exclude them as QC-failures (the 1253). The agent (`dae88433`) tried both and committed to the wrong polarity. |
| 4 | Broken workspace (only HCC `data.xlsx`, no Jackdaw data) → literature-derived ~1e-06 | 2 | Answer ~10× too high | **Infrastructure failure** unrelated to task quality. Workspace bifurcation: trial-level non-determinism in which files got mounted into `/workspace`. Both affected runs are `terminus-2 / claude-opus-4-6`. The third trial of the same stack (`af91e43c`) had the data and produced interp #2. |

## Surface vs. root cause for the main cluster (15 of 18 pipeline-correct runs)

### Surface
The LLM judge sees an answer in scientific notation outside `[1.03e-07, 1.23e-07]` and returns INCORRECT.

### Root cause
**The question wording does not unambiguously specify the calculation method that the verifier requires.** Three plausible interpretations exist:

1. *Total CpGs / total genome length* — most natural reading of "genome-wide ... per base pair"
2. *Mean of per-chromosome densities, all chromosomes (zeros included)* — most natural reading of "average chromosomal density"
3. *Mean of per-chromosome densities, hit-bearing chromosomes only* — required by the verifier; **non-standard** and **not cued by the question**

The English of the prompt *favours* interpretations #1 and #2 (the 15 pipeline-correct runs split 8/7 between them). Interpretation #3 requires a support-truncated unweighted mean — a calculation that excludes 24 of 44 chromosomes from the *denominator* with no English signal in the prompt.

### Why "rejection of #3" is informed, not lazy

Six runs (3 codex/gpt-5.4 + 1 terminus-2/gemini + 1 terminus-2/gpt-5.4 + 1 implicit in code from terminus-2/gemini) explicitly **computed 1.1283e-07 and rejected it**. Their stated reasons:

- *"using the mean chromosomal density (incl. zero-count chromosomes) as the primary interpretation of 'genome-wide average chromosomal density'"* — codex `50c55ea4`
- *"the task wording specifically asks for the genome-wide average chromosomal density, so the mean across all chromosomes is the best match"* — terminus-2/gpt-5.4 `ee3db288`
- *"writing the final XML-wrapped answer now, using the mean chromosome-level density as the primary interpretation"* — codex `618b213c`

These are **good linguistic decisions** by capable agents, made on principled grounds, that happen to land outside the verifier's required interpretation.

## Pathway 3 in detail (`dae88433`, polarity flip)

The verb *to filter* is genuinely ambiguous in scientific English:
- "Filter for extreme methylation values" → keep them (the 51-CpG reading, used by 17 of 18 runs)
- "Filter out extreme methylation values" → remove them (the 1253-CpG reading)

`dae88433` started with the keep-reading at B22, then at B106 switched to the remove-reading on the rationale that ">90% or <10% methylation" sounds like a QC-fail criterion that should be excluded for downstream analysis. This is a defensible reading in a different methodological context but contradicts the task as designed. **Surface cause:** wrong polarity. **Root cause:** semantic ambiguity in "filtered" + extended literature search that surfaced QC-filter conventions.

## Pathway 4 in detail (broken workspace, `653e0c1c` and `d542d75f`)

Both runs reported `/workspace/` containing only `data.xlsx` — an unrelated HCC clinical dataset (Efficacy / BMI / ECOG-PS columns). No `JD_AgeRelated_CpG_noMT_Final.csv`, no `JD_Chromosome_Length.csv`. The agents:

1. Recognized the data was wrong domain.
2. Did extensive web/PubMed research, found the source paper (Tangili et al. 2025) and Dryad DOI.
3. Reconstructed the analysis using paper-level totals (1218–1299 AR-CpGs), **not** the dataset's extreme-methylation filter.
4. Computed `1218–1299 / ≈1.13e9 ≈ 1.08–1.15e-06`.

**The third terminus-2/opus run (`af91e43c`) had the correct workspace and produced 5.25e-08.** So the workspace problem is non-deterministic across trials — most likely a stochastic Docker image / capsule download failure. The audit cannot infer pathway 4 as a *task* problem; it is a benchmark infrastructure problem affecting only this stack.

## Comparison to other "buggy gold" inspections

This task fits the same shape as `aa-lcr-10`, `aa-lcr-30`, `aa-lcr-60`:

| Property | `aa-lcr-10` | `bix-52-q2` |
|---|---|---|
| Pass rate | 0/18 | 0/18 |
| Capable runs converging on same wrong answer | 15/15 | 15/16 (one polarity flip) |
| Oracle hard-coded value derivable from env? | No | Borderline — only via non-standard interp #3 |
| Multiple capable agents flag the issue? | Yes (3 runs surface the calculation tension explicitly) | Yes (6 runs compute interp #3 and reject it) |
| Authoring-error pattern | Number lifted from different question | Calculation method lifted from non-standard interp |

## Summary

- **15 of 18 runs** failed because the task's question is ambiguous and the verifier requires a non-standard interpretation that the question does not cue.
- **1 of 18 runs** failed by flipping the polarity of "filtered", a different semantic ambiguity.
- **2 of 18 runs** failed because of a broken workspace (infrastructure issue, not task-design).

**0 of 18 runs** can be attributed to a clean agent-capability gap. The 16 pipeline-correct runs all produced the **correct underlying biological computation** (51 unique extreme-methylation CpGs, 1.058e9 bp Jackdaw genome length, 20 hit-bearing chromosomes); they only diverge on which aggregation step the question wants — and the question does not unambiguously specify it.
