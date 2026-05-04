# bix-36-q4 — gemini-3.1-pro-preview / gemini-cli failures

**Task question.** "What is the p-value of ANOVA comparison across immune cell
types, excluding PBMCs, for log2 fold change of miRNA expressions?"
**Graded answer.** Between 0.55 and 0.59 inclusive.
**All three runs submit ~`8.396e-154`** (reward 0). The harness is `gemini-cli`
running `gemini-3.1-pro-preview`.

## TL;DR (shared across all 3 runs)

All three runs identify the **same three input files**, settle on the **same
formulation**, and produce the same numeric p-value (`8.396166823294354e-154`,
`8.396166823292924e-154`, `8.396166823291491e-154`) which agrees to 13 sig
figs — only float-rounding noise differs between runs.

Workspace files (`/workspace/`):
- `BatchCorrectedReadCounts_Zenodo.csv` — gene × sample integer count matrix,
  shape `(59453, 723)`, first column is gene id, the other 723 are
  `(samp)(celltype)` columns like `CHC096CD4`, `PO237_PB_PBMC`, etc.
- `GeneMetaInfo_Zenodo.csv` — `Geneid, Chr, Length, gene_biotype` for 59,453
  rows; 1,879 are `gene_biotype == 'miRNA'`.
- `Sample_annotated_Zenodo.csv` — 723 rows of `sample, samp, samtype, celltype,
  batch, sex`. `celltype` counts: PBMC 158, CD4 151, CD8 145, CD19 137, CD14 132.
  Every individual `samp` has a paired PBMC sample (158/158).

The submitted code path (essentially identical in all 3 runs):

```python
mirnas = meta[meta['gene_biotype'] == 'miRNA']['Geneid']
mirna_total = counts.loc[mirnas].sum(axis=0)            # one scalar/sample
total = counts.sum(axis=0)
cpm   = mirna_total / total * 1e6                        # total-miRNA CPM/sample
df = samples.merge(... cpm ...)
pbmc = df[df.celltype=='PBMC'].set_index('samp')['cpm']
df['pbmc_cpm'] = df['samp'].map(pbmc)
df['log2fc']   = np.log2(df['cpm'] / df['pbmc_cpm'])     # paired vs OWN PBMC
df = df[df.celltype != 'PBMC']                           # 565 rows total
groups = [g['log2fc'] for ct,g in df.groupby('celltype')]
f, p = scipy.stats.f_oneway(*groups)                     # F=476.5, p≈8.4e-154
```

This is **sample-level paired LFC of one scalar per sample** (the per-sample
total miRNA CPM, computed from the SUM of all 1,879 miRNA counts as a
fraction of the library). It is NOT a per-miRNA ANOVA. PBMCs are correctly
excluded from the ANOVA factor levels (only CD4/CD8/CD14/CD19 are passed to
`f_oneway`), but PBMC is the **denominator** of the fold change. n per group
≈ 132–151, total ≈ 565 observations, df_between=3, df_within≈561, F≈476.5.
The reason the p-value is astronomically small is the very tight per-group
distributions (e.g. CD14 mean −0.327, sd 0.291; CD19 mean +0.955, sd 0.297)
combined with a large monocyte-vs-lymphocyte separation — see
`run d94fcf06`'s printed group stats.

The ground truth (0.55–0.59) requires a **per-miRNA log2FC** ANOVA
(distributions of 1,879 LFC values per cell type, comparing means across
groups). All three agents *did compute* such a per-miRNA p-value at some
point (~2.7e-5 with `+1` pseudocount on mean-CPM, or 0.108–0.135 on raw
counts) but **rejected it in favor of the per-sample total-miRNA LFC** for
its mathematical "purity" (no pseudocount needed). None of them produced
anything in the 0.55–0.59 range — the closest p-value any of them computed
was 0.667/0.700 (TPM-LFC ANOVA in run 1) and 0.108–0.135 (raw-count per-gene
mean LFC).

The three runs are **deterministic up to float noise**: same model, same
prompt, same dataset, same code path; the trailing-digit drift
(`...294354` vs `...292924` vs `...291491`) is consistent with
non-deterministic floating-point summation order in pandas
(`counts.sum(axis=0)`, dict-iteration order) across BLAS thread schedulings,
not with substantive different methods.

---

## Run `4f5cf7a9-df26-4900-834c-81a8fe2d34a5` → `8.396166823294354e-154`

98 messages. Agent reads all three CSVs (block B2), confirms 1,879 miRNAs
(B8), and that all 158 individuals have a paired PBMC (B16). It then
spends ~25 messages oscillating between three candidate definitions of
"log2 fold change of miRNA expressions" (sum-then-LFC sample-wise
vs per-miRNA mean-LFC vs DESeq2-style), running each one. Notable computed
values along the way:

| Method                                            | Block | p-value |
| ------------------------------------------------- | ----- | ------- |
| Paired sample-level total miRNA CPM LFC            | B24, B64, B74 | 8.396e-154 |
| Sample-level total miRNA RAW count LFC (no norm)  | B24   | 1.474e-27 |
| Per-miRNA log2((mean_CT+1)/(mean_PBMC+1)) ANOVA   | B26, B48, B58, B68 | 2.761e-05 |
| Per-miRNA mean(log2(CPM+1)) diff ANOVA            | B50, B58 | 2.372e-05 |
| Per-miRNA log2(count+1) diff (no lib norm)        | B52   | 0.127 |
| Per-miRNA log2(mean count+1) ratio (no lib norm)  | B52   | 0.109 |
| `eps=1e-6` per-miRNA CPM-LFC                       | B70   | 0.210 |
| Expressed-only per-miRNA mean-CPM LFC, no eps      | B70   | 4.89e-7 |
| Per-miRNA paired CPM LFC mean (pseudocount 1)     | B78   | 1.825e-05 |
| Per-miRNA paired RAW count LFC mean               | B80   | 0.126 |
| TPM-LFC mean ANOVA (with/without pairing)         | B84   | 0.667 / 0.700 |
| Total-miRNA TPM paired LFC                        | B86   | 3.27e-132 |
| All sample-miRNA LFC pooled (huge n)              | B62   | 0.0 (underflow) |

Sanity-checking: agent did notice the per-miRNA p-value's **strong
dependence on the pseudocount** (B71): "the p-value's heavy reliance on
the pseudocount […] casts serious doubt on the initial interpretation".
It uses *that* observation as positive evidence in favor of the
sample-level total-LFC, because no pseudocount is needed there
("There were no zeros in that data!", B71). It also briefly tries DESeq2
size-factor normalization (B76) but that yields `nan` due to zero-count
genes and is abandoned.

Final reasoning chain (B87, B89, B91, B97): "The mathematical
representation of this is unambiguous; there are no arbitrary factors such
as pseudocounts […] The result remains extremely robust." The agent writes
a final notebook computing both (per-miRNA `2.76e-5` and sample-total
`8.40e-154`) and **deliberately picks the latter**, then echoes the
answer. Final assistant message acknowledges the alternative
(`2.7610981213865518e-05`) but concludes "The robust paired total miRNA LFC
is provided as the final answer".

The minor digit drift (`294354` here vs `292924`/`291491` in the others)
likely comes from a slightly different intermediate pandas pipeline:
this run uses `pbmc_cpm = ...mean(axis=1)` chains and `sample_to_celltype`
dict-iteration in B23, whereas the other two reach the same number via
`samples['sample'].map(pbmc)` + boolean filtering. The FP sums differ in
the last bit.

---

## Run `51524c3f-d0f3-4588-98b1-d24c29091777` → `8.396166823292924e-154`

106 messages, the longest of the three. Same data files, same end formula.
Distinguishing feature: this is the only run that **invokes pydeseq2**
in earnest (it found `pydeseq2 0.4.12` installed) and runs full DESeq2
size-factor + dispersion + LFC fitting. Six methods enumerated explicitly
as "Method 1..6" in B25/B37:

| Method | Description | p-value |
| ------ | ----------- | ------- |
| 1 | Paired log2FC of total miRNA CPM (sample-level) | 8.396e-154 |
| 2 | Mean log2FC of each miRNA gene across pairs | 1.825e-05 |
| 3 | Unpaired version of 2 | 2.372e-05 |
| 4 | Average per-sample of all-miRNA LFCs | 1.61e-75 |
| 5 | log2(mean(CPM_ct)/mean(CPM_PBMC)) ANOVA | 2.761e-05 |
| 6 | Paired version of 5 | 2.318e-05 |

Then DESeq2 (B66/B78): fits size factors on all 59,453 genes, refits LFCs
on the 1,879 miRNA subset, runs Wald tests for CD4 vs PBMC, CD8 vs PBMC,
CD14 vs PBMC, CD19 vs PBMC, then `f_oneway` on the four
`log2FoldChange` arrays → **6.084514842911341e-134** (B78). It also tries
DESeq2 size-factor-normalized total-miRNA LFC (B94) → `2.118e-130`, and
log2(CPM+1) sample-level LFC (B98) → `6.865e-154`. None of the per-miRNA
or DESeq2 results push it toward the 0.55–0.59 truth.

Same per-miRNA pseudocount-sensitivity observation as run 1, same
conclusion: B95 — "the same incredibly small p-value of
`8.396166823292924e-154`. Finally, I will output this to
`/workspace/answer.txt`." Final answer written B101.

This run notably arrives at the answer via a slightly different code
shape (B100): `samples['miRNA_cpm'] = samples['sample'].map(miRNA_cpm)` +
`pbmc = samples[samples.celltype=='PBMC'].set_index('samp')['miRNA_cpm']`,
which differs from run 1's `groupby('samp')` approach. Same math, FP
order differs in the last bits — `292924` vs `294354`.

---

## Run `d94fcf06-a5a1-4cd3-9b85-436684f64c5e` → `8.396166823291491e-154`

98 messages. Same data, same final formulation. Distinctive features:
this is the only run that **also tries native R DESeq2** (after
`installed.packages()` confirms DESeq2 + apeglm + ashr are installed,
B52). It writes `/workspace/notebook.R` with `library(DESeq2)`, builds a
`DESeqDataSet`, and runs the full pipeline; transcript truncated in
the middle but it eventually yields **`6.084514842911341e-134`**
through pydeseq2 with all-genes size factors (B82, B88) — same as run 2.

This run's final notebook (B91) is the cleanest: it computes mirna_fraction
= sum(miRNA counts) / sum(all counts) per sample, takes
`log2(fraction_ct / fraction_pbmc)` per `samp`, then `f_oneway` on the
four cell-type groups. Algebraically equivalent to runs 1 and 2 (since
multiplying numerator and denominator by `1e6` doesn't change the ratio
inside `log2`). Output (B92):

```
F-statistic: 476.5355608624385
p-value: 8.396166823291491e-154
```

Group means (printed in B28):
```
celltype  mean       std      count
CD14     -0.326816   0.291    132
CD19      0.955332   0.297    137
CD4      -0.060946   0.299    151
CD8      -0.019581   0.316    145
```
This is the smoking-gun for *why* the p-value is so extreme: CD19's mean
LFC of +0.955 is ~3.3 SD away from CD14's −0.327, with N≈140 per group
and within-group SD ≈0.30 — the F statistic of ~477 reflects a genuine
biological signal (B-cells preferentially package miRNA), but it is
answering the wrong statistical question. The truth (`p∈[0.55, 0.59]`)
demands per-miRNA LFC vectors (1,879 values per group), where per-miRNA
biological variability dominates and means across cell types are nearly
indistinguishable.

Final reasoning (B91, B93, B97): "the standard CPM approach is direct,
straightforward, and doesn't involve dispersion estimation". It briefly
second-guesses ("Did the task creator perhaps anticipate the output from
PyDESeq2's f_oneway on its log2FoldChange arrays, which is
`6.084514842911341e-134`?") but does not switch its answer.

---

## Why are all three nearly identical?

**Deterministic up to float noise, not coincidence.** Same model
(`gemini-3.1-pro-preview`), same harness (`gemini-cli`), same prompt, same
input data, same toolset. All three converge on the same wrong
interpretation ("log2 fold change of miRNA expressions" = log2-FC of the
*scalar* per-sample total miRNA fraction, paired against own PBMC,
ANOVA across the 4 non-PBMC cell types) for the same reason:

1. The per-miRNA mean-LFC ANOVA p-value (~2.7e-5) is **wildly sensitive
   to pseudocount choice** (range from 0.21 with eps=1e-6 to 4.9e-7 with
   no eps + expressed-only filter), which all three agents flag as a red
   flag.
2. The sample-level total-LFC has **no zeros** (min total miRNA count =
   269, B96 in run 2 / B90 in run 3) so the calculation is "mathematically
   pure" — no pseudocount choice. Each run cites this as their rationale.
3. None of the three actually checks the LFC distribution per **gene**
   (i.e. across the 1,879 miRNAs), which is what the question is really
   asking. They all pivot away from per-gene methods because of the
   pseudocount sensitivity, and they all also tried DESeq2 (which gave
   `6e-134`, also too tiny) without recognizing that DESeq2's per-gene
   `log2FoldChange` distribution being concentrated near zero with similar
   means across cell types is the relevant clue.

The three trailing-digit differences (`294354`/`292924`/`291491`) come from
running mathematically equivalent but differently-ordered pandas /
NumPy float reductions: e.g. `groupby('samp')` + iter vs
`set_index('samp')` + `map` + boolean filter. With ~565 floats summed
through pandas + numpy + BLAS, the final ULPs differ across reorderings.
This is the float-summation noise the task description anticipated; the
agents are doing the same computation. The mistake is in the
interpretation of "log2 fold change of miRNA expressions" — taking it
to mean "log2 fold change of (total) miRNA expression (per sample)"
rather than "log2 fold change of (each of the many) miRNA expressions
(per gene)".
