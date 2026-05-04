# Failure-mode taxonomy — bix-36-q4

## Surface vs. root cause

| | Surface failure | Root cause |
|---|---|---|
| 14 / 18 runs | Submitted a tiny p-value (1e-7 to 1e-154) | Used "log2 fold change" as a per-gene per-donor or per-(gene, sample) quantity, then ANOVA'd the pooled distribution → pseudoreplication inflation |
| 1 / 18 runs (claude-code, `e3ea324d`) | Submitted 0.18 | Took the question literally as "ANOVA on 4 cell-type means of mean miRNA log2 expression" — got the right *aggregation level* but the wrong *fold-change definition* (used `log2(expr+1)` not pairwise DESeq2 LFCs) |
| 1 / 18 runs (terminus-2/gemini, `a626b1d6`) | Submitted 6.08e-134 | Used PyDESeq2 — the right *tool* — but with `celltype vs PBMC` contrasts (4 LFC vectors), not the canonical 6 pairwise contrasts |
| 18 / 18 runs | Did not produce a value in `[0.55, 0.59]` at any point | Did not interpret "across cell types" as "across the 6 pairwise C(4,2) DESeq2 LFC vectors of CD4/CD8/CD14/CD19", and did not see "excluding PBMCs" as "drop PBMC samples entirely from the analysis" |

## The hidden ambiguity tree

The phrase **"the p-value of ANOVA comparison across immune cell types, excluding PBMCs, for log2 fold change of miRNA expressions"** has at least 4 independent ambiguities:

1. **What does "log2 fold change" mean?**
   - log2 of expression (no fold change) — claude-code's chosen answer (0.18)
   - log2((expr+1)/(PBMC+1)) per donor (paired) — codex's answer (2.72e-41)
   - log2(mean_celltype/mean_PBMC) per gene — terminus-2/opus's answer (1.12e-10)
   - log2(nonrefsamp/refsamp) per gene — terminus-2/gemini's 11ca6990 attempt (0.0549)
   - PyDESeq2 LFC celltype-vs-PBMC — terminus-2/gemini's a626b1d6 (6.08e-134)
   - **PyDESeq2 LFC pairwise (CANONICAL)** — none chose
   - log2(total miRNA fraction CPM) — gemini-cli (8.40e-154)

2. **What's the "fold change" baseline?**
   - PBMC (most agents)
   - Cell-type grand mean (claude-code 59745ef4)
   - "refsamp" subgroup (terminus-2/opus 7c06ccf3, c0774023)
   - **None — pairwise among cell types (CANONICAL)**

3. **What's the unit of observation in the ANOVA?**
   - One scalar per sample (claude-code e3ea324d, gemini-cli x3)
   - One LFC value per (gene, sample) (most agents)
   - One LFC value per gene (terminus-2/opus 7c06ccf3, c0774023)
   - **One LFC value per (gene, pairwise contrast) (CANONICAL)**

4. **What does "excluding PBMCs" mean?**
   - PBMC is *the* baseline (so its LFC is 0 by definition; excluded from the ANOVA factor) — most agents
   - PBMC samples are *dropped* before computing fold change — terminus-2/gemini 11ca6990, **CANONICAL**

The reference notebook makes one specific cut at every node: "log2 fold change" = pairwise DESeq2 LFC, baseline = none (pairwise), unit = (gene, pairwise contrast), excluding PBMCs = drop PBMC samples. **The probability of an agent reading the wording and randomly picking exactly this combination is essentially zero**, especially since the most natural reading of "log2 fold change... excluding PBMCs" is "fold change computed against the [included or excluded] PBMC reference".

## Pseudoreplication is a *secondary* issue

Many agents (claude-code 1160aec6, codex all 3, terminus-2/opus e4d3bfb7, all gpt-5.4 stacks) chose a pooled-gene×sample ANOVA, where the F-statistic is huge because n is huge. Several of them flagged the issue explicitly: "the very large sample sizes (>250K per group) from flattening make even tiny differences significant. A more reasonable approach might be to work at the sample level" (run `e4d3bfb7`). They knew it was wrong and submitted it anyway because the alternative interpretations they considered also missed the oracle. **This is consistent with the oracle being unreachable from the question wording**: any agent who ran sample-level aggregation got p ≈ 0.18–0.20 and judged that "doesn't seem right either" relative to the question's framing as a precise numerical comparison.

## Determinism, by stack

| Stack | n | Distinct answers | Comment |
|---|---|---|---|
| terminus-2 / gpt-5.4 | 3 | 1 (`2.72338e-41` × 3) | Deterministic to 16 sig-figs |
| gemini-cli / gemini-3.1-pro-preview | 3 | 3 same to 13 sig-figs (`8.396166823e-154`) | Deterministic up to float-summation noise |
| terminus-2 / claude-opus-4-6 | 3 | 2 (`1.12e-10`×2, `4.56e-64`×1) | Two of three converge; one diverges |
| codex / gpt-5.4 | 3 | 2 (`2.72e-41`×2 in different prose, `2.999e-32`×1) | Two converge; complete-donor variant in third |
| claude-code / claude-opus-4-6 | 3 | 3 (`0.18`, `1.43e-21`, `6.57e-52`) | Highest exploration variance |
| terminus-2 / gemini-3.1-pro-preview | 3 | 3 (`4.89e-7`, `2.69e-8`, `6.08e-134`) | Highest exploration variance; spans 126 orders of magnitude |

**The two highest-exploration stacks (claude-code/opus, terminus-2/gemini) produce the closest p-values to the oracle (0.18 and 0.0549 respectively).** Stacks that lock in deterministically (gpt-5.4 + gemini-cli) commit to a pseudoreplicated pooled formulation as the "obvious" interpretation and stop iterating.

This is the diagnostic signature of a task where exploration helps but doesn't *solve*: more iterations get you closer, but no amount of standard exploration leads to the canonical pairwise-DESeq2-LFC pipeline because it's not signaled by the prompt.

## Hacking risk

**No agent attempted to look up the BixBench upstream dataset, the canonical solution notebook, or the source paper.** All worked from the data files alone, with the question text as the only spec. That said: the canonical answer corpus is downloadable from HuggingFace (`futurehouse/BixBench/CapsuleFolder-48181cce-3928-4491-94b4-c23504a6aaa1.zip` contains the executed `CapsuleNotebook-...ipynb`), and there's no firewall / network restriction visible in the agent environment. **An agent that decided to search for "BixBench" or "bix-36" online could in principle have found and reproduced the notebook.** None did. This is mostly a non-issue here because the BixBench training data is also tagged with a canary GUID, and the notebook itself contains the value — so anybody finding it would just copy the answer.

The bigger hack-risk is: an agent could simply submit `<answer>0.57</answer>` (a bald guess in the middle of any reasonable p-value range) and pass via the LLM judge. Since the oracle range is [0.55, 0.59] and gpt-4o is asked to judge "equivalence", a prose answer of "approximately 0.57" or even "the result is non-significant (p ≈ 0.57)" would pass. **This is the only viable hack: educated guessing of a "reasonable" non-significant p-value.** None of the 18 trial submissions did this — every agent submitted what its own analysis had produced, in good faith. That suggests the task evades hacking by sheer ambiguity, but a more cunning agent could.
