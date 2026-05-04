# bix-36-q4 — Failed-run audit (terminus-2, anthropic/claude-opus-4-6)

Task: *"What is the p-value of ANOVA comparison across immune cell types, excluding PBMCs, for log2 fold change of miRNA expressions?"* — graded answer `[0.55, 0.59]`.

All three runs found the same files in `/workspace/` and identified the same set of 1879 miRNA genes, but they diverged on what "log2 fold change" meant. None of them found the correct interpretation (which produces a p-value ~0.55–0.59).

---

## Run `7c06ccf3-ca02-45c5-b694-872b1c56d5ac` → `<answer>1.12e-10</answer>`

**1. Files in `/workspace/`.** From `ls -la /workspace/`:
```
BatchCorrectedReadCounts_Zenodo.csv  (~106 MB, 59453 genes × 723 samples)
GeneMetaInfo_Zenodo.csv              (gene_biotype labels)
Sample_annotated_Zenodo.csv          (sample, samp, samtype, celltype, batch, sex)
notebook.py                          (empty)
```
Cell types `['CD4','CD8','CD14','CD19','PBMC']`; samtypes `refsamp`/`nonrefsamp` (400/323). 1879 miRNA biotype genes.

**2. ANOVA code (gene-level pooled, ratio of group means).** The agent interpreted "log2 fold change" as `log2(nonrefsamp_mean / refsamp_mean)` per miRNA per cell type:
```python
ref_mean = mirna_counts[ref_samples].mean(axis=1)
nonref_mean = mirna_counts[nonref_samples].mean(axis=1)
log2fc = np.log2((nonref_mean + 1) / (ref_mean + 1))
results[ct] = log2fc
...
f_stat, p_value = stats.f_oneway(
    log2fc_df['CD4'].dropna(), log2fc_df['CD8'].dropna(),
    log2fc_df['CD14'].dropna(), log2fc_df['CD19'].dropna())
```
- "log2 fold change" is interpreted as `log2(nonref / ref)` (ratio of group means with +1 pseudocount), **not** vs. PBMC baseline.
- Aggregation is **gene-level**: each cell type gets a vector of length 1879 (one log2FC per miRNA).
- PBMC was excluded from the ANOVA factor (`cell_types_no_pbmc = ['CD4','CD8','CD14','CD19']`).

**3. Final p-value printed.**
```
ANOVA F-statistic: 16.490578409045458
ANOVA p-value: 1.1189991007360684e-10
ANOVA p-value (scientific): 1.12e-10
```

**4. Sanity checks.** Yes — the agent later ran four alternative approaches:
- *Approach 2 (per-sample mean log2FC)*: `F=0.3316, p=8.03e-01`
- *Approach 4 (per-sample mean log2 expression)*: `p=1.77e-01`
- *Approach 5 (all miRNA × sample log2 expression flattened)*: `p=1.43e-21`
- *Approach 6 (celltype mean / overall mean)*: `p=1.06e-01`

It saw a per-sample p-value of 0.80 and another at 0.18 — much closer to the truth — but rejected them.

**5. Reasoning chain.** The agent reasoned that "log2 fold change" "strongly implies a comparison between two conditions — in this dataset, that would be nonrefsamp vs refsamp" and concluded: *"This is the most standard interpretation of 'log2 fold change' in genomics."* It treated the gene-level pooled p=1.12e-10 as canonical and submitted it twice without revisiting the per-sample alternative.

---

## Run `c0774023-f11e-4e82-88ca-21b5ed411276` → `<answer>1.12e-10</answer>`

**1. Files in `/workspace/`.** Identical listing: `BatchCorrectedReadCounts_Zenodo.csv`, `GeneMetaInfo_Zenodo.csv`, `Sample_annotated_Zenodo.csv`, `notebook.py`. Counts shape `(59453, 723)`, 1879 miRNAs.

**2. ANOVA code (identical strategy to run 7c06).** Same `nonref/ref` ratio aggregated by group means:
```python
for ct in ['CD4', 'CD8', 'CD14', 'CD19', 'PBMC']:
    ref_samples   = sample_meta[(sample_meta['celltype']==ct) & (sample_meta['samtype']=='refsamp')]['sample'].tolist()
    nonref_samples= sample_meta[(sample_meta['celltype']==ct) & (sample_meta['samtype']=='nonrefsamp')]['sample'].tolist()
    ref_mean    = mirna_counts[ref_samples].mean(axis=1)
    nonref_mean = mirna_counts[nonref_samples].mean(axis=1)
    log2fc = np.log2((nonref_mean + 1) / (ref_mean + 1))
    results[ct] = log2fc
...
groups = [results_df[ct].values for ct in cell_types_no_pbmc]
f_stat, p_value = stats.f_oneway(*groups)
```
- Same `log2(nonref/ref)` interpretation (not vs. PBMC).
- Gene-level pooled (1879 values per cell type).
- PBMC excluded from the ANOVA factor levels (kept only for printing).

**3. Final p-value printed.**
```
F-statistic: 16.490578409045458
p-value: 1.1189991007360684e-10
p-value (scientific): 1.12e-10
```

**4. Sanity checks.** Yes — after the first commit it computed an alternative *Approach 2* (per-sample mean across miRNAs):
```
Approach 2 (per-sample mean log2 expression):
F-statistic: 1.6499210419569283, p-value: 1.77e-01
```
It saw the per-sample p-value of `0.177` but dismissed it and re-affirmed `1.12e-10`.

**5. Reasoning chain.** The agent worked sample structure out (each `samp` is either ref or nonref, 80 ref individuals, 78 nonref-PBMC etc.), then chose: *"the most standard approach … for each cell type, compute the mean expression … then log2FC = log2((nonref+1)/(ref+1)) for each miRNA"*. The pseudoreplication concern was raised in the post-hoc check but immediately overruled with *"The most standard interpretation of 'log2 fold change' in genomics … the answer is 1.12e-10"*. Mark-complete fired three times before final acceptance.

---

## Run `e4d3bfb7-0739-4d34-9701-d1950c0bb497` → `<answer>4.56e-64</answer>`

**1. Files in `/workspace/`.** Identical: `BatchCorrectedReadCounts_Zenodo.csv`, `GeneMetaInfo_Zenodo.csv`, `Sample_annotated_Zenodo.csv`, `notebook.py`. 1879 miRNAs × 565 non-PBMC samples.

**2. ANOVA code (different fold-change definition).** This agent did **not** use the ref/nonref split. It computed log2 expression and subtracted the gene-wise mean across non-PBMC samples, then **flattened all gene × sample cells**:
```python
log2_counts = np.log2(mirna_counts_no_pbmc + 1)
mean_log2 = log2_counts.mean(axis=1)
log2fc = log2_counts.subtract(mean_log2, axis=0)
...
for ct in ['CD4','CD8','CD14','CD19']:
    ct_samples = [s for s in non_pbmc_samples_in_counts if sample_to_celltype[s] == ct]
    values = log2fc[ct_samples].values.flatten()  # n ≈ 250–280k per cell type
    groups[ct] = values
f_stat, p_value = stats.f_oneway(*[groups[ct] for ct in cell_types])
```
Group sizes printed: `CD4: 283729, CD8: 272455, CD14: 248028, CD19: 257423`.
- "log2 fold change" interpreted as **gene-mean-centered log2 expression** (`log2(x+1) − mean_gene log2(x+1)`), **not** vs. PBMC baseline and not vs. refsamp.
- Aggregation is **fully pseudoreplicated** (every miRNA × sample is one row, ~1M total points).
- PBMC samples were dropped before log2FC was computed.

**3. Final p-value printed.**
```
One-way ANOVA:
F-statistic: 98.9955
p-value: 4.559232124166209e-64
p-value (formatted): 4.56e-64
```

**4. Sanity checks.** Yes — the agent extensively explored alternatives:
- *Approach 2 (per-sample mean log2FC)*: `F=1.6499, p=1.77e-01`
- *Approach 3 / E (per-gene cell-type means)*: `F=2.7843, p=3.93e-02`
- *Approach 4 (raw log2 expression flattened)*: `F=33.39, p=1.43e-21`
- *Kruskal-Wallis on flattened*: `H=12.44, p=6.01e-03`
- *Approaches A–E* (all combinations of reference + per-sample/per-gene/flatten).

It explicitly noted *"the very large sample sizes (>250K per group) from flattening make even tiny differences significant. A more reasonable approach might be to work at the sample level."* — and then ignored it.

**5. Reasoning chain.** The agent never considered the ref/nonref design. Initial framing: *"compute log2(expression+1) for each miRNA in each sample, then for each cell type collect all log2FC values, perform one-way ANOVA"*. After reviewing alternatives it acknowledged the pseudoreplication problem twice (*"this has pseudoreplication issues"*), but in the end justified the choice as *"the most direct interpretation … the natural unit of observation is each miRNA expression value"* and submitted `4.56e-64`. Notably, *Approach D (per-sample mean, ref=non-PBMC): p=1.77e-01* and *Approach E (per-gene cell-type means): p=0.039* were both rejected; the per-sample mean across miRNAs was the closest to the correct ground truth (~0.55) but only gave 0.18 because the agent never used PBMC as the fold-change baseline.

---

## Cross-run takeaway

The two distinct wrong answers (`1.12e-10` and `4.56e-64`) reflect two different log2FC definitions, not two aggregations of the same definition:

- `1.12e-10` (runs 7c06, c0774023): gene-level **per-miRNA** vector of `log2(mean_nonrefsamp / mean_refsamp)` per cell type, ANOVA over 1879 values × 4 groups.
- `4.56e-64` (run e4d3): **flattened per-sample-per-miRNA** values of `log2(x+1) − gene_mean_log2(x+1)`, ANOVA over ~270k values × 4 groups (massive pseudoreplication).

Crucially, **none** of the three agents tried the interpretation the graded answer implies: compute log2 fold change of each cell type **relative to PBMC** (the obvious baseline given "excluding PBMCs"), then ANOVA at the sample- or per-gene-mean level. The phrase "excluding PBMCs" was uniformly read as "drop PBMC samples before grouping" rather than "use PBMC as the fold-change reference."
