# bix-36-q4 — claude-code/claude-opus-4-6 trajectory audits

Three docent runs, all `claude-code` harness on `claude-opus-4-6`, all reward 0.

Ground truth band: **`[0.55, 0.59]`** (verifier rejects anything else).
Question: *"What is the p-value of ANOVA comparison across immune cell types, excluding PBMCs, for log2 fold change of miRNA expressions?"*

All three runs found the same `/workspace/` payload via `Glob /workspace/*`:

```
/workspace/GeneMetaInfo_Zenodo.csv      (59,453 rows, columns: ,Geneid,Chr,Length,gene_biotype)
/workspace/Sample_annotated_Zenodo.csv  (723 rows, columns: sample,samp,samtype,celltype,batch,sex)
/workspace/BatchCorrectedReadCounts_Zenodo.csv  (genes x 723 samples; index = gene id; columns are <donor><celltype>[_<n>])
/workspace/notebook.py                  (empty seed file)
```

`Sample_annotated_Zenodo.csv` shows `celltype ∈ {CD4, CD8, CD14, CD19, PBMC}`. The `samp` column is the donor id (so PBMC and the 4 sorted subsets are paired per donor). 1,879 genes have `gene_biotype == 'miRNA'`. After excluding PBMC, 565 non-PBMC samples remain.

---

## Run `e3ea324d-2cb4-47bf-a8f3-1ef58df524c3` — `<answer>0.18</answer>` (18 steps)

**Data discovery.** Identical Glob then `head -5 GeneMetaInfo... Sample_annotated... BatchCorrectedReadCounts...` (one batched call). Saw the 5-celltype universe and the gene metadata schema. Did not run `wc -l` on gene meta (it inferred miRNA count later).

**First attempt.** Filtered to `gene_biotype == 'miRNA'` (1879 genes), excluded PBMC (565 samples), computed `log2_data = np.log2(mirna_non_pbmc + 1)`, then took the per-sample mean across all miRNAs (`sample_mean_log2 = log2_data.mean(axis=0)`) and ran `scipy.stats.f_oneway` on the 4 cell-type groups (n = 132/137/151/145). Output:

```
Cell types in ANOVA: ['CD14', 'CD19', 'CD4', 'CD8']
Group sizes: [132, 137, 151, 145]
ANOVA F-statistic: 1.6499
ANOVA p-value: 1.7681e-01
```

**Moment of doubt.** It explicitly second-guessed itself: *"the p-value is 0.1768. But let me reconsider — 'log2 fold change' might mean something different from just log2 expression. Fold change typically implies a ratio between conditions."* It then **rewrote the script with five competing approaches** and ran them all in one pass:

```
Approach 1 (mean log2 per sample):                      F=1.6499,  p=1.7681e-01   <-- ultimately submitted
Approach 2 (log2FC vs grand mean per gene):             F=2.0140,  p=1.0969e-01
Approach 3 (pooled gene x sample log2):                 F=33.3897, p=1.4327e-21
Approach 4 (log2FC vs matched PBMC, mean across genes per sample):
            CD14 n=132 mean=-0.024,  CD19 n=137 mean=-0.013,
            CD4  n=151 mean=-0.032,  CD8  n=145 mean=-0.035
            F=1.5762,  p=1.9405e-01
Approach 5 (log2FC vs PBMC, pooled all genes):          F=63.8799, p=2.7234e-41
```

Approach 4 is *exactly* the question taken literally — paired-donor log2((celltype + 1) / (matched PBMC + 1)) per gene, averaged across genes per sample, then ANOVA across the 4 cell types — and gave **p ≈ 0.194**. The ground-truth band 0.55-0.59 was not produced by any of the five formulations.

**Final reasoning chain (verbatim).** *"In RNA-seq, 'log2 fold change' can sometimes just refer to log2-transformed counts, but 'fold change' really does imply a comparison to something. ... I'm settling on the most straightforward interpretation: calculate the mean log2-transformed expression across all miRNAs for each sample, then run a one-way ANOVA across the four cell types, which gives me p = 0.1768, or approximately 0.18 when rounded."*

So it considered both PBMC-as-baseline and grand-mean-as-baseline, computed both, **and then defaulted back to Approach 1** (no fold-change at all, just mean log2 expression per sample) because that's "most straightforward". Final write: `echo "<answer>0.18</answer>"`. Closing line: *"This is not statistically significant, indicating no significant difference in mean miRNA log2 expression across these cell types."*

This is the only run that even computed the "log2FC vs PBMC, average per sample, ANOVA across 4 cell types" formulation (Approach 4). Its number 0.194 is closer to 0.55-0.59 than anyone else got, but still well outside the band — so Approach 4 isn't what BixBench's reference workflow does either. The 0.55-0.59 answer is likely something more specific (e.g. paired-donor log2FC where each gene-celltype mean is one observation, or a different aggregation altogether).

---

## Run `1160aec6-9849-4af5-9983-1366d3169029` — `<answer>1.43e-21</answer>` (14 steps)

**Data discovery.** Same Glob, then `head -5` of all three CSVs in one batched bash call, then a follow-up `wc -l /workspace/GeneMetaInfo_Zenodo.csv && cut -d',' -f5 ... | sort | uniq -c` showing 19,942 protein_coding / 1,879 miRNA / etc. — this run was more thorough about confirming biotypes.

**Single attempt, no doubt.** It went straight for the **gene-level pooled** ANOVA (Approach 3 in `e3ea324d`'s taxonomy). Code summary:

```python
mirna_genes = gene_meta[gene_meta['gene_biotype'] == 'miRNA'].index    # 1879
samples_no_pbmc = samples[samples['celltype'] != 'PBMC']               # 565 samples
mirna_counts_no_pbmc = mirna_counts[common_samples]                    # 1879 x 565
log2_expr = np.log2(mirna_counts_no_pbmc + 1)                          # NO fold change

groups = []
for ct in ['CD14','CD19','CD4','CD8']:
    ct_samples = samples_no_pbmc[samples_no_pbmc['celltype'] == ct]['sample'].values
    ct_cols = [s for s in ct_samples if s in log2_expr.columns]
    vals = log2_expr[ct_cols].values.flatten()                         # genes x samples flattened
    groups.append(vals)
f_stat, p_value = stats.f_oneway(*groups)
```

Group sizes were enormous: CD14 = 248,028; CD19 = 257,423; CD4 = 283,729; CD8 = 272,455 (each = 1879 genes × number of samples in that celltype). Output:

```
ANOVA F-statistic: 33.3897
ANOVA p-value: 1.43e-21
ANOVA p-value (full): 1.4327277524778449e-21
```

Note F=33.39 is identical to `e3ea324d`'s Approach 3 — same data, same formulation.

**No fold change was actually computed.** It used `log2(count+1)` as the input, which is just log-transformed expression. There is no per-gene baseline subtraction, no PBMC matching, no grand-mean centering. It explicitly equates the two in code comments: *"# Compute log2 transformed expression"* and then submits saying *"log2 fold change of miRNA expressions is 1.43e-21"*.

**No alternatives explored.** It immediately wrote `<answer>1.43e-21</answer>` and a one-line summary. Zero internal debate. PBMCs were excluded from the cell-type groups but not used as a baseline reference.

---

## Run `59745ef4-1a84-40c1-b730-f7b19560ce86` — `<answer>6.57e-52</answer>` (13 steps)

**Data discovery.** Same Glob, same `head -5` batched preview. No `wc -l` follow-up. Inferred miRNA count from the data itself.

**Single attempt, no doubt.** Closest in spirit to a "fold change", but with **grand mean across non-PBMC samples** as baseline (no PBMC matching). Code:

```python
mirna_genes = gene_info[gene_info['gene_biotype'] == 'miRNA'].index    # 1879
non_pbmc_samples = sample_info[sample_info['celltype'] != 'PBMC'].index # 565
mirna_non_pbmc = mirna_counts[non_pbmc_samples]
mirna_pseudo = mirna_non_pbmc + 1
gene_means = mirna_pseudo.mean(axis=1)                                  # mean across non-PBMC samples per gene
log2fc = np.log2(mirna_pseudo.div(gene_means, axis=0))                  # log2(expr / per-gene non-PBMC mean)

celltypes_data = {}
for sample in non_pbmc_samples:
    ct = sample_info.loc[sample, 'celltype']
    celltypes_data.setdefault(ct, []).append(log2fc[sample].values)
for ct in celltypes_data:
    celltypes_data[ct] = np.concatenate(celltypes_data[ct])    # gene x sample, flattened

f_stat, p_value = stats.f_oneway(*celltypes_data.values())
```

Same massive group sizes (CD4=283,729; CD8=272,455; CD14=248,028; CD19=257,423). Output:

```
ANOVA F-statistic: 80.25737718438768
ANOVA p-value: 6.5676601707908834e-52
ANOVA p-value (scientific): 6.57e-52
```

This is `e3ea324d`'s Approach 2 except pooled at the (gene × sample) level rather than the (gene × celltype-mean) level — i.e., centering each gene by its non-PBMC mean and then ANOVAing all individual gene-sample log2FC values. Because per-gene centering removes the gene-level expression-level differences (which dominated `1160aec6`'s F=33), the residual celltype effect at the gene-sample level is *more* visible: F jumps to 80, and p drops further (6.57e-52 vs 1.43e-21).

**No alternatives explored, no doubt.** No PBMC pairing considered. Wrote `<answer>6.57e-52</answer>` immediately; final-line summary: *"The p-value of the ANOVA comparison across immune cell types (CD4, CD8, CD14, CD19), excluding PBMCs, for log2 fold change of miRNA expressions is **6.57e-52**."*

---

## Cross-run summary

| Run | Steps | Submitted | Formulation | "log2 fold change" interpreted as | PBMC role |
|---|---|---|---|---|---|
| `e3ea324d` | 18 | 0.18 | per-sample mean of log2(count+1), ANOVA on 4 sample-level groups (n≈132-151) | *just log2(count+1)*, no fold change | excluded only |
| `1160aec6` | 14 | 1.43e-21 | flattened gene×sample log2(count+1), ANOVA on 4 huge pooled groups (n≈248k-284k) | *just log2(count+1)*, no fold change | excluded only |
| `59745ef4` | 13 | 6.57e-52 | flattened gene×sample log2((count+1)/per-gene non-PBMC mean), ANOVA on 4 huge pooled groups | log2 ratio vs per-gene grand-mean baseline | excluded only |

Only `e3ea324d` even tried a PBMC-paired log2FC (its Approach 4) — F=1.58, p=0.194 — which is the most literal reading of the question, and *still* misses the 0.55-0.59 ground-truth band. None of the five formulations `e3ea324d` enumerated lands in the band, so the canonical BixBench workflow that produced 0.55-0.59 must use yet a different aggregation (likely something like per-donor matched log2((celltype+pseudo)/(PBMC+pseudo)), summarized per (donor, celltype) into one mean log2FC per sample, possibly with a different gene/sample subset, or possibly comparing celltype mean log2FC values at the gene level rather than at the sample level).
