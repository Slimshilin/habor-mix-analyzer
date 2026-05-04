# Per-run trajectories — bix-36-q4 (18/18 audited, no sampling)

This is the consolidated index for the per-run findings. Detailed write-ups are in:

- `_subagent_claude_code.md` — claude-code/claude-opus-4-6 (3 runs)
- `_subagent_codex.md` — codex/gpt-5.4 (3 runs)
- `_subagent_gemini_cli.md` — gemini-cli/gemini-3.1-pro-preview (3 runs)
- `_subagent_terminus2_gpt54.md` — terminus-2/openai/gpt-5.4 (3 runs)
- `_subagent_terminus2_opus.md` — terminus-2/anthropic/claude-opus-4-6 (3 runs)
- `_subagent_terminus2_gemini.md` — terminus-2/gemini/gemini-3.1-pro-preview (3 runs)

Below is the cross-run summary. The "p-value distance to oracle" is `|log10(p) − log10(0.57)|` — a pure measure of how far each agent's answer is from the oracle band on a log scale.

## Final answers + interpretations (sorted by submitted p-value, descending)

| # | Run | Harness/Model | Submitted p | Interpretation |
|---|---|---|---|---|
| 1 | `e3ea324d` | claude-code / claude-opus-4-6 | **0.18** | Per-sample mean of `log2(count+1)`, ANOVA on 4 cell-type groups (no fold change at all) |
| 2 | `11ca6990` | terminus-2 / gemini-3.1-pro-preview | 4.892e-7 | Per-miRNA `log2(mean_CPM_celltype / mean_CPM_PBMC)` (drop zeros), ANOVA on 4 cell-type LFC vectors |
| 3 | `4cdb1013` | terminus-2 / gemini-3.1-pro-preview | 2.687e-8 | Per-miRNA mean `log2(counts+1)` difference between nonref and ref, ANOVA on 4 cell-type LFC vectors |
| 4 | `7c06ccf3` | terminus-2 / claude-opus-4-6 | 1.12e-10 | Per-miRNA `log2((mean_nonref+1)/(mean_ref+1))` (raw counts), ANOVA on 4 cell-type LFC vectors |
| 5 | `c0774023` | terminus-2 / claude-opus-4-6 | 1.12e-10 | (clone of #4) |
| 6 | `1160aec6` | claude-code / claude-opus-4-6 | 1.43e-21 | Pooled gene×sample `log2(count+1)`, ANOVA on 4 huge groups (~250–284k each) |
| 7 | `72aa8ff9` | codex / gpt-5.4 | 2.999e-32 | Donor-paired `log2((cell+1)/(PBMC+1))`, gene-pooled, restricted to 116 complete donors |
| 8 | `1ce7a046` | codex / gpt-5.4 | 2.72e-41 (prose) | Same as 9, all 158 donors |
| 9 | `b6ac03c0` | codex / gpt-5.4 | 2.72338e-41 (prose) | Same as 10 |
| 10 | `115a98a5` | terminus-2 / gpt-5.4 | 2.72338e-41 | Donor-paired `log2((expr+1)/(PBMC+1))` per gene, all 158 donors, pooled, ANOVA 4 groups |
| 11 | `d1724994` | terminus-2 / gpt-5.4 | 2.72338e-41 | clone of #10 |
| 12 | `d7071018` | terminus-2 / gpt-5.4 | 2.72338e-41 | clone of #10 |
| 13 | `59745ef4` | claude-code / claude-opus-4-6 | 6.57e-52 | Per-gene mean-centering `log2((expr+1)/per-gene-non-PBMC-mean)`, gene-pooled |
| 14 | `e4d3bfb7` | terminus-2 / claude-opus-4-6 | 4.56e-64 | Gene-mean-centered `log2(expr+1)`, gene×sample pooled, ANOVA 4 huge groups |
| 15 | `a626b1d6` | terminus-2 / gemini-3.1-pro-preview | 6.085e-134 | **PyDESeq2 celltype-vs-PBMC** LFC, ANOVA on 4 LFC vectors (close in spirit but wrong contrast set) |
| 16 | `4f5cf7a9` | gemini-cli / gemini-3.1-pro-preview | 8.396e-154 | **Per-sample total miRNA CPM**, paired LFC vs own PBMC (single scalar per sample) |
| 17 | `51524c3f` | gemini-cli / gemini-3.1-pro-preview | 8.396e-154 | clone of #16 (last bit float drift) |
| 18 | `d94fcf06` | gemini-cli / gemini-3.1-pro-preview | 8.396e-154 | clone of #16 (last bit float drift) |

**Oracle**: `[0.55, 0.59]` (canonical pipeline produces F=0.7718, p=0.5699 — see `oracle_verification.md`).
**Closest agent answer**: 0.18 (claude-code/opus, run `e3ea324d`). Distance ≈ 0.5 log10 units.
**Closest p-value any agent *computed* (not necessarily submitted)**: 0.0549 (run `11ca6990`, "per-miRNA log2((mean_nonref+1)/(mean_ref+1)) (CPM), ANOVA on 4 LFC vectors"). Distance ≈ 1.0 log10 units. **This is exactly 10× smaller than 0.55, and inside the BixBench distractor `(0.05, 0.09)`.**

## What every agent got right

- **Found all three CSVs**: `BatchCorrectedReadCounts_Zenodo.csv`, `GeneMetaInfo_Zenodo.csv`, `Sample_annotated_Zenodo.csv`. ✓
- **Identified miRNA genes**: 1,879 with `gene_biotype == 'miRNA'` (the canonical workflow uses a regex `MIR*` that gives 2,114, but this is a minor difference). ✓
- **Identified the 4 immune cell types**: `CD4, CD8, CD14, CD19` and the PBMC group. ✓
- **Identified the donor pairing structure**: 158 donors, 116 with all 5 cell types. ✓
- **Most agents wrote a working `f_oneway` call** with PBMCs excluded from factor levels. ✓

## What every agent got wrong (the universal failure)

**No agent computed the canonical pairwise-DESeq2-LFC ANOVA.** All 18 agents read "ANOVA across cell types" as "an ANOVA whose factor levels are the 4 cell types" rather than as "an ANOVA over the 6 pairwise C(4,2) DESeq2 LFC vectors". This single decision point dominates outcomes — every other choice (CPM normalization, PBMC pairing, pseudocount value, pooled vs sample-level) is downstream of it.

The reference workflow is also **statistically unusual**: comparing the marginal distributions of 6 pairwise LFCs is not a standard test. It's testing whether the *pairwise effect sizes* differ across the C(4,2) comparisons — essentially a sanity check on the homogeneity of effect-size distributions across pairs of cell types, which is an oblique way of asking "do miRNAs differ across cell types?". The hypothesis stated in BixBench upstream — *"miRNAs exhibit a constant expression profile across immune-related cell types"* — frames the research question, but that hypothesis text is not given to the agent.

## Determinism analysis

- **terminus-2/gpt-5.4**: 3/3 produced 2.7233761722814507e-41 to 16 sig-figs → fully deterministic on identical code path.
- **gemini-cli**: 3/3 within 13 sig-figs of 8.396166823e-154 → fully deterministic up to float-summation noise from pandas iteration order.
- **terminus-2/claude-opus-4-6**: 2/3 produced 1.12e-10 (same code), 1/3 took a different aggregation path and got 4.56e-64.
- **codex/gpt-5.4**: 2/3 produced 2.72e-41 (full-donor pooled), 1/3 produced 2.999e-32 (complete-donor-only pooled).
- **claude-code/claude-opus-4-6**: 3/3 different answers (0.18, 1.43e-21, 6.57e-52) — opus *does* explore alternative aggregations and one of three actually picks the per-sample mean log2 expression which gives the closest answer to the oracle. Highest variance, highest exploration.
- **terminus-2/gemini-3.1-pro-preview**: 3/3 different answers (4.89e-7, 2.69e-8, 6.08e-134), spanning 126 orders of magnitude. Most exploratory; one run (11ca6990) computed 0.0549 — within 1 log10 of the oracle band — but rejected it.

## A second hidden disagreement

Even **two interpretations of "log2 fold change"** that the agents themselves both saw — log2((cell+1)/(PBMC+1)) per gene per donor (donor-paired) vs the same averaged per donor — give p-values 30+ orders of magnitude apart. This is the *statistical inflation from pseudoreplication*, which 4 of 18 agents explicitly flagged as a concern but none corrected for. Even agents that recognized the problem chose the inflated answer because the question doesn't tell them which aggregation to use.
