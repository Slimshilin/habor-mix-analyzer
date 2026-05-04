# bix-36-q4 — terminus-2 / gemini-3.1-pro-preview (3 runs)

Question: *"What is the p-value of ANOVA comparison across immune cell types, excluding PBMCs, for log2 fold change of miRNA expressions?"*
Graded answer: between 0.55 and 0.59 inclusive. All three runs returned reward 0.

This stack has the **widest spread** of any of the 6 model/harness pairings (4.89e-7, 2.69e-8, 6.08e-134) — it explores the most variants of "what does log2 fold change mean here?" but still systematically lands on extreme p-values. **Most importantly, run `11ca6990` actually computed a p-value of `0.0549` for one of its alternative formulations — an order of magnitude off from the oracle band `[0.55, 0.59]`. Either the agent missed by 10× or the BixBench oracle is off by 10×.**

Workspace files (same as every other run):
- `BatchCorrectedReadCounts_Zenodo.csv` (59,453 × 723; gene id × sample matrix, integer counts)
- `GeneMetaInfo_Zenodo.csv` (`Geneid`, `Chr`, `Length`, `gene_biotype`; 1,879 miRNAs)
- `Sample_annotated_Zenodo.csv` (`sample`, `samp`, `samtype` ∈ {refsamp, nonrefsamp}, `celltype` ∈ {CD4, CD8, CD14, CD19, PBMC}, `batch`, `sex`)
- `notebook.py` (empty seed)

The `samtype` column matters: 158 individuals are split into 80 `refsamp` × {5 cell types} = 400 reference samples, and 78 `nonrefsamp` individuals contribute partial cell-type panels (52–71 each, 323 total) — a 1×5 reference cohort vs. an unmatched non-reference cohort. This design does **not** give 1-to-1 ref/nonref pairing; it suggests the analysis intended in the source paper is "compare nonref to ref within each cell type, then compare those LFCs across cell types".

---

## Run `11ca6990-36d4-4804-a687-d67cfa21fd87` → `<answer>4.892177570077082e-07</answer>`

41 messages. **The most exhaustive run of any in this study** — the agent enumerated 18+ distinct formulations before settling. Reproduced p-values in source order:

| # | Formulation | p-value |
|---|---|---|
| 1 | per-patient total miRNA CPM, paired log2FC vs own PBMC, ANOVA on 4×~140 patient scalars | 2.900e-125 |
| 2 | per-patient total miRNA RAW count, paired log2FC vs own PBMC | 5.985e-23 |
| 3 | per-patient total miRNA CPM, log2FC vs MEAN PBMC | 1.617e-137 |
| 4 | per-miRNA mean-CPM log2FC vs PBMC, pseudocount 1e-3 | 0.00949 |
| 5 | per-miRNA mean-CPM log2FC vs PBMC, **filtered 0s** | **4.892e-07 ← submitted** |
| 6 | per-miRNA mean-CPM log2FC vs PBMC, pseudocount 1 | 2.761e-05 |
| 7 | per-miRNA mean log2(CPM+1) difference vs PBMC | 2.372e-05 |
| 8 | per-miRNA total miRNA expression, log2(sum+1) FC | 6.865e-154 |
| 9 | per-miRNA log2(CPM+1) per (patient, gene), pooled | 0.0 (underflow) |
| 10 | per-miRNA log2((mean_nonref+1)/(mean_ref+1)) **(CPM)**, ANOVA on 4×1879 LFCs, pseudocount 1 | **0.05486** |
| 11 | per-miRNA log2((mean_nonref+1)/(mean_ref+1)) (CPM), drop zeros | **0.06664** |
| 12 | per-miRNA log2((mean_nonref+1e-3)/(mean_ref+1e-3)) (CPM) | 0.08408 |
| 13 | per-miRNA log2((mean_nonref+1)/(mean_ref+1)) (RAW counts) | 1.119e-10 |
| 14 | per-miRNA mean-RAW log2FC vs PBMC, pseudocount 1 | 0.10854 |
| 15 | per-miRNA mean-RAW log2FC vs PBMC, drop zeros | 0.32507 |
| 16 | per-miRNA paired CPM log2FC mean across patients (per gene) | 1.825e-05 |
| 17 | per-miRNA paired CPM log2FC median across patients | 2.170e-05 |
| 18 | per-miRNA log2(mean_CPM_celltype/mean_CPM_PBMC) (CPM, drop inf) | 4.892e-07 |

**Closest p-value to the oracle band `[0.55, 0.59]`**: row 10 (`p=0.0549`), row 11 (`p=0.0666`), row 12 (`p=0.0841`) — all three computed for "compare miRNA log2FC nonref-vs-ref across the 4 immune subtypes (excluding PBMC)". These are the **only formulations consistent with both** "log2 fold change" (a true ratio between two conditions) **and** "excluding PBMCs" (PBMC dropped entirely from the analysis, not used as baseline).

The agent identified this formulation in B27 (*"The phrase 'excluding PBMCs' strongly suggests that PBMC could have been one of the groups in the ANOVA, but was excluded. This means the log2 fold change is not relative to PBMC, but rather between 'nonrefsamp' and 'refsamp' for each cell type"*) and computed `p=0.0549`. Then in B33 it reversed itself: *"The term 'excluding PBMCs' strongly implies that PBMC is the baseline reference for the log2 fold change, so its log2FC would be 0 and therefore excluded from the ANOVA"* — and went back to the vs-PBMC formulation.

**Final reasoning chain (B39):** *"the most standard interpretation of this... is to normalize to CPM, calculate the mean CPM for each cell type, compute the log2 fold change of each miRNA relative to PBMC, drop any undefined values (where mean CPM is 0), and perform a one-way ANOVA across the CD4, CD8, CD14, and CD19 groups. The calculated p-value is 4.892177570077082e-07."*

The 0.0549 result is *exactly the right* analytical shape for the question wording — but its magnitude is **10× off from the oracle**. If the BixBench oracle were `(0.05, 0.07)` instead of `(0.55, 0.59)`, this agent would have passed. This is the single strongest piece of evidence that the oracle range may be a transcription error.

---

## Run `4cdb1013-df1b-4b7a-9d83-83ef7ca143ad` → `<answer>2.6868089736878954e-08</answer>`

41 messages. Slightly less exhaustive than 11ca6990, but the only run to attempt **PyDESeq2** (the canonical tool for log2FC in bulk RNA-seq).

P-values produced:

| Formulation | p-value |
|---|---|
| per-miRNA mean log2(counts+1) diff vs PBMC (no pairing) | 0.1270 |
| per-miRNA paired log2(counts+1) FC mean across patients vs own PBMC | 0.1259 |
| per-miRNA log2((mean_nonref+1)/(mean_ref+1)) (CPM) | (not printed for raw, see below) |
| per-miRNA log2((mean_nonref+1)/(mean_ref+1)) (RAW counts), pseudocount 1 | 1.119e-10 |
| per-miRNA mean log2(counts+1) **diff between nonref and ref** | **2.687e-08 ← submitted** |
| per-miRNA log2(mean_nonref/mean_ref) without pseudocount | 2.579e-05 |
| **PyDESeq2 LFC: nonrefsamp vs refsamp per cell type, ANOVA on 4×LFC vectors** | 2.988e-23 |
| PyDESeq2 LFC: same, common genes only | 4.694e-13 |
| **PyDESeq2 LFC: celltype vs PBMC, ANOVA on 4×LFC vectors** | 6.079e-134 |

The agent never tried the per-miRNA `nonref/ref` CPM ANOVA that produced 0.0549 in run 11ca6990, and so never even came within 1 order of magnitude of the oracle band.

**Final reasoning (B35):** *"Usually, log2(mean(group A)/mean(group B)) is the standard definition of log2 fold change for RNA-seq when not using a package like DESeq2... let's check `np.log2(mean(nonref+1)/mean(ref+1))` which gave 1.1189991007360684e-10... [or] `mean(log2(counts+1))` which is the log-average. ... Let's re-evaluate the most standard pipeline for a python script without DESeq2... The p-value for this was 2.6868089736878954e-08."*

The agent saw PyDESeq2 LFC with the right comparison (vs PBMC) gives `6.08e-134` and dismissed it; saw same-cell-type nonref-vs-ref gives `2.99e-23` and submitted a simpler log2(counts+1)-diff version of nearly the same formulation (`2.69e-08`). **None of the three values it printed are in 0.55–0.59 or 0.05–0.07.**

---

## Run `a626b1d6-b184-4261-836d-f16d0990b199` → `<answer>6.084514842911341e-134</answer>`

61 messages. Same exploration pattern as 4cdb1013; it ultimately submitted the **PyDESeq2 LFC vs PBMC** value (the most rigorous/canonical one, but still 130 orders of magnitude off the oracle).

P-values produced (subset):

| Formulation | p-value |
|---|---|
| per-patient miRNA-fraction CPM log2FC vs own PBMC, ANOVA on 4×~140 scalars | 2.900e-125 |
| per-patient miRNA-fraction RAW count log2FC | 5.985e-23 |
| per-miRNA mean log2(CPM+1) paired diff per patient | 1.825e-05 |
| per-miRNA mean log2(CPM+1) diff (no pairing) | 2.372e-05 |
| per-miRNA log2((mean_CPM+1)/(mean_PBMC+1)) | 2.761e-05 |
| **PyDESeq2 LFC: celltype vs PBMC, ANOVA** | **6.085e-134 ← submitted** |
| PyDESeq2 LFC: nonrefsamp vs refsamp, ANOVA | 2.99e-23 |

**Submission rationale:** *"PyDESeq2 is the standard tool for calculating log2 fold change in bulk RNA-seq data... The 'log2 fold change of miRNA expressions' between each immune cell type and PBMC is calculated using DESeq2's framework. The ANOVA p-value across the 4 cell types' LFC arrays is 6.084514842911341e-134."*

This run **never tried** the `nonref/ref` per-cell-type ANOVA, so never came near the 0.05 region. The single closest p-value it produced is 2.76e-05 (still 4 orders of magnitude off from 0.55).

---

## Cross-run takeaways for terminus-2/gemini

1. **Even the most exhaustive trajectory missed the oracle band by an order of magnitude.** Run 11ca6990 produced 18+ p-values; the closest plausible shape (0.0549) is for "log2FC of nonref vs ref per cell type, ANOVA across 4 cell types" — exactly the analysis that "excluding PBMCs" + "log2 fold change" most literally invites (because here PBMC is *dropped*, and the LFC is between two real conditions, not a baseline).
2. **No agent ever computed a value in `[0.55, 0.59]`.** Across 18+ formulations × 3 runs in this stack alone, the ranges were `1e-154 ≤ p ≤ 0.32507`. The oracle's tolerance band is not in this distribution.
3. **The agents disagree wildly with each other**: 4.89e-7 vs 2.69e-8 vs 6.08e-134 are 26 to 134 orders of magnitude apart. Two different gemini runs on the same data with the same prompt and the same model produce p-values that differ by 10^126 — purely from picking a different "log2 fold change" interpretation. This is the strongest possible signal that the question is **underspecified** for the level of precision the oracle requires.
4. The 0.0549 result in run 11ca6990 strongly suggests either (a) the BixBench oracle range is `(0.055, 0.059)` and was transcribed as `(0.55, 0.59)`, or (b) the BixBench reference workflow uses a different normalization or a different aggregation that none of these agents tried (e.g. without CPM normalization at the within-cell-type nonref/ref ratio level — but the agents did try the raw-count version and got `1.12e-10`, nowhere near 0.55).
