# Oracle verification — `bix-36-q4`

## TL;DR

The oracle answer **(0.55, 0.59)** is technically reproducible — but the BixBench reference workflow that produces it is **non-obvious to the point of being un-inferrable from the question wording alone**. After verifying the BixBench upstream record, downloading the source capsule, and successfully re-running the canonical notebook, the reference p-value is **F=0.7718, p=0.5699** — which lands inside the oracle band only because the pipeline uses a very specific (and somewhat unusual) PyDESeq2 invocation pattern that no agent independently chose.

## What I did

1. Confirmed the harbor adapter at `/home/shilin/T-Bench/harbor/adapters/bixbench/adapter.py` reads the question and oracle range *verbatim* from the upstream HuggingFace dataset `futurehouse/BixBench` (split=train). The adapter does not modify wording; the harbor question text == BixBench question text.
2. Loaded the upstream record for `question_id = 'bix-36-q4'` directly:
   ```python
   from datasets import load_dataset
   ds = load_dataset('futurehouse/BixBench', split='train')
   ds.filter(lambda x: x['question_id'] == 'bix-36-q4')[0]
   ```
   Full record (verbatim):
   - **question**: *"What is the p-value of ANOVA comparison across immune cell types, excluding PBMCs, for log2 fold change of miRNA expressions?"*
   - **ideal**: `(0.55,0.59)` (range_verifier)
   - **distractors**: `['(0.001,0.01)', '(0.05,0.09)', '(0.1,0.2)']`
   - **hypothesis**: *"miRNAs exhibit a constant expression profile across immune-related cell types"*
   - **result**: *"ANOVA test across the 6 different comparison groups (4 immune cell types) shows that there are no signnificant differences in the LFC of miRNAs. a few outliers here and there but not enough to have a statistical impact"*
   - **answer**: `True`
   - **categories**: `Sequence Analysis,Differential Expression Analysis,Transcriptomics,RNA-seq`
   - **paper**: `https://zenodo.org/records/10000430`
   - **capsule_uuid**: `48181cce-3928-4491-94b4-c23504a6aaa1`
3. Downloaded `CapsuleFolder-48181cce-3928-4491-94b4-c23504a6aaa1.zip` from the BixBench HF repo (26.9 MB) and inspected the canonical notebook `CapsuleNotebook-48181cce-3928-4491-94b4-c23504a6aaa1_executed.ipynb`.
4. Reproduced the canonical analysis on the actual data and confirmed the oracle band.

## What the canonical notebook does (verbatim from the executed Capsule notebook)

```python
# loading data
corr_counts = pd.read_csv(corr_counts_link, index_col=0)
metadata    = pd.read_csv(metadata_link, index_col=0)

# (1) Filter to genes whose name matches the regex "MIR*"
#     NB: pandas .str.contains() default is regex=True, and "*" means
#     "0+ of the previous char", so this matches any gene name containing "MI"
#     (broader than gene_biotype=='miRNA'); it picks up 2,114 genes (vs. 1,879 strict miRNAs)
corr_counts_mir = corr_counts[corr_counts.index.str.contains("MIR*")]

# (2) "Excluding PBMCs" = drop PBMC samples entirely (NOT use them as a baseline)
corr_counts_mir = corr_counts_mir.T[corr_counts_mir.T.index.isin(
    metadata[~metadata.celltype.isin(["PBMC"])].index)]
metadata_mir = metadata[~metadata.celltype.isin(["PBMC"])]

# (3) Drop very low-expressed genes (sum across non-PBMC samples >= 10)
corr_counts_mir = corr_counts_mir.T[corr_counts_mir.T.sum(axis=1) >= 10].T
# After filter: 1,010 genes × 565 non-PBMC samples

# (4) Fit DESeq2 THREE TIMES with different reference levels — needed
#     in the OLD pydeseq2 to expose all pairwise LFC columns inside `varm["LFC"]`.
dds_mir_cd4  = DeseqDataSet(... ref_level=['celltype','CD4'], ...).deseq2()
dds_mir_cd8  = DeseqDataSet(... ref_level=['celltype','CD8'], ...).deseq2()
dds_mir_rest = DeseqDataSet(...   no ref_level (defaults to alphabetical → CD14)).deseq2()

# (5) Concatenate the LFC matrices and pull the 6 pairwise comparisons:
mir_lfc_allcells = pd.concat([
    dds_mir_cd4.varm["LFC"],
    dds_mir_cd8.varm["LFC"],
    dds_mir_rest.varm["LFC"]], axis=1)
cell_type_cols = ["celltype_CD8_vs_CD4",
                  "celltype_CD14_vs_CD4",
                  "celltype_CD19_vs_CD4",
                  "celltype_CD14_vs_CD8",
                  "celltype_CD19_vs_CD8",
                  "celltype_CD19_vs_CD14"]

# (6) ANOVA across the SIX pairwise LFC vectors (each n≈1,010):
groups = [mir_lfc_allcells[c] for c in cell_type_cols]
anova_stat, anova_p_value = f_oneway(*groups)
print(f"ANOVA across groups: stat={anova_stat:.2f}, p-value={anova_p_value:.2e}")
```

## My re-run (modern pydeseq2 + DeseqStats path, mathematically equivalent)

```
$ uv run --with pydeseq2,pandas,scipy python ...
  CD8_vs_CD4:  n=1010, mean=0.0553, std=0.3695
  CD14_vs_CD4: n=1010, mean=0.0898, std=1.4130
  CD19_vs_CD4: n=1010, mean=0.1332, std=1.2907
  CD14_vs_CD8: n=1010, mean=0.0345, std=1.4665
  CD19_vs_CD8: n=1010, mean=0.0779, std=1.2749
  CD19_vs_CD14: n=1010, mean=0.0434, std=1.6657
>>> ANOVA F=0.7718, p=5.699458e-01
```

**p ≈ 0.570 ∈ [0.55, 0.59]** → matches the oracle. Confirmed.

## Why no agent finds this

The reference pipeline embeds **four non-obvious choices**, and missing any one of them produces a p-value far from 0.55–0.59. Each choice is supported by the BixBench `hypothesis`/`result` metadata that **agents never see** (the harbor adapter does not pass `hypothesis` or `result` into the agent's instructions — only `question`).

| Decision | Reference does | Almost every agent does | Why missing this kills the answer |
|---|---|---|---|
| **Gene filter** | `index.str.contains("MIR*")` regex (≈2,114 genes; broader than just miRNA biotype) | `gene_biotype == 'miRNA'` (1,879 genes) | Minor; both filters give similar p-values after the `sum>=10` step |
| **Low-expression filter** | `sum(counts) >= 10` across non-PBMC → 1,010 genes | not applied (use all 1,879 miRNAs) | Important; without filtering, sparse miRNAs add noise |
| **"Excluding PBMCs" interpretation** | Drop PBMC samples entirely from the analysis | Use PBMC as fold-change baseline (donor-paired or grand-mean) | Critical. Vs-PBMC LFCs give p≈e-7 to e-134 because PBMC is a true mixture and CD-subtypes systematically differ from it |
| **"ANOVA across cell types" interpretation** | ANOVA on the **6 pairwise C(4,2) DESeq2 LFC vectors** | ANOVA on **4 cell-type groups** (each group = a vector of LFCs computed from CD4/CD8/CD14/CD19 samples) | Fundamental. The reference compares the *distributions* of pairwise LFCs to test whether any pair stands out; no agent saw "across cell types" as "across pairwise contrasts" |
| **LFC method** | PyDESeq2 (size-factor normalization + Wald MAP shrinkage) | log2(CPM+1)-difference, log2((mean+1)/(mean_PBMC+1)), or pyDESeq2 vs PBMC | DESeq2 LFCs are normally distributed and small-magnitude; CPM-based LFCs aren't and inflate the F |

The hypothesis text *"miRNAs exhibit a constant expression profile across immune-related cell types"* and the result text *"ANOVA test across the 6 different comparison groups (4 immune cell types) shows that there are no significant differences in the LFC of miRNAs"* explicitly state this is the "ANOVA across the 6 pairwise comparisons" formulation. **But neither string is in the agent's prompt.**

## Two extra sanity checks

- **The closest p-value any agent computed was `0.0549`** (run `11ca6990`, "log2((mean_nonref+1)/(mean_ref+1)) per miRNA, ANOVA across 4 cell types"). That is **exactly 10× off** from the oracle range. It is also a near-clone of the BixBench *distractor* `(0.05, 0.09)` — meaning the BixBench question authors anticipated this answer as a *plausible wrong answer*, but the harbor adapter's `range_verifier` only accepts the `ideal` band. So an agent that found 0.0549 and submitted it would be graded INCORRECT despite being inside one of the BixBench multiple-choice distractors.
- **No simpler interpretation produces 0.55–0.59.** Of the 18+ formulations the agents collectively tried (per-sample mean log2 expression, paired log2FC vs PBMC mean, paired log2FC vs PBMC pooled, paired log2FC vs PBMC sample-level, log2((mean+1)/(mean_PBMC+1)) per gene, log2(mean(CPM_nonref)/mean(CPM_ref)) per gene, mean log2(CPM+1) difference, total miRNA CPM LFC, total miRNA TPM LFC, DESeq2 vs PBMC, etc.), none produced a p-value in `[0.55, 0.59]` except the canonical 6-pairwise-LFC pipeline. The BixBench distractor `(0.05, 0.09)` is a much better fit for the question's natural reading.

## Verdict

**The oracle is reproducible — but only by inheriting a buggy gene filter.** When I held the canonical pipeline fixed (drop PBMC → DESeq2 → 6 pairwise LFCs → `f_oneway`) and *only* swapped the gene filter from `str.contains("MIR*")` (regex; matches anything containing 'MI'; 1010 genes after sum>=10) to the proper `gene_biotype == 'miRNA'` (798 genes), the resulting p-value flipped from **0.5699 to ≈ 0** (F=143.79). The 261 non-miRNA genes silently included by the regex (145 protein-coding genes like MITF/MIA3/MIB2, 91 lncRNAs like MIR181A1HG that are *host genes for* miRNAs but not miRNAs themselves, 25 pseudogenes) is what makes the canonical p-value land in `[0.55, 0.59]` instead of being effectively zero.

So the oracle is not derivable from "the question + correct domain practice"; it is derivable only from "the question + this specific notebook author's regex bug". A competent bioinformatician would (a) use the explicit `gene_biotype` column rather than a name-pattern regex, (b) compute a non-significant result via none of the 18+ formulations the agents tried, and (c) likely reject the canonical answer as biologically implausible (miRNAs are well-known to differ across these immune subtypes). The harbor adapter inherits the upstream bug verbatim. **Therefore: the oracle is broken, not just under-specified.** The task requires *script reproduction*, not domain reasoning.

## Sources

- BixBench dataset card: <https://huggingface.co/datasets/futurehouse/BixBench>
- bix-36 capsule download: `https://huggingface.co/datasets/futurehouse/BixBench/resolve/main/CapsuleFolder-48181cce-3928-4491-94b4-c23504a6aaa1.zip`
- Source data Zenodo record: <https://zenodo.org/records/10000430> ("RNAseq of PBMC and sorted subpopulations (CD4, CD8, CD14, CD19) from children", Lin et al. 2023)
- BixBench paper: <https://arxiv.org/abs/2503.00096> ("BixBench: a Comprehensive Benchmark for LLM-based Agents in Computational Biology")
- BixBench GitHub: <https://github.com/Future-House/BixBench>
- Harbor adapter source: `/home/shilin/T-Bench/harbor/adapters/bixbench/adapter.py` (load_dataset → BixBenchRecord → render_template; `cleaned_ideal_answer` for `range_verifier` formats `(low, high)` as `"Between {low} and {high} inclusive"`).
