# Per-run trajectory findings — `bixbench/bix-52-q2`

Sourced from full Docent trajectories (collection `640e920a-aef3-4b7c-9487-69899ef19e9d`). All 18 runs read end-to-end via subagents on `mcp__plugin_docent_docent__get_agent_run_messages`. No sampling.

## Final answers at a glance

| # | Run ID | Stack | Final answer | Interp. | In judge range [1.03–1.23]e-07? |
|---|---|---|---|---|---|
| 1 | 16f8fab4 | claude-code / opus-4-6 | **4.82e-08** | #1 (total/total, with MT) | ❌ |
| 2 | 76a1c40a | claude-code / opus-4-6 | **4.82e-08** | #1 | ❌ |
| 3 | b2f07594 | claude-code / opus-4-6 | **4.82e-08** | #1 | ❌ |
| 4 | 391989fb | codex / gpt-5.4 | **5.247706e-08** | #2 (mean per-chr, 43 non-MT) | ❌ |
| 5 | 50c55ea4 | codex / gpt-5.4 | **5.25e-08** | #2 | ❌ |
| 6 | 618b213c | codex / gpt-5.4 | **5.13e-08** | #2 (mean per-chr, 44 incl MT) | ❌ |
| 7 | 48df2112 | gemini-cli / gemini-3.1 | **4.819e-08** | #1 (no-MT) | ❌ |
| 8 | dae88433 | gemini-cli / gemini-3.1 | **1.184e-06** *(or 2.340e-06)* | **polarity flip** (kept 1253, not 51) | ❌ (≈25× too high) |
| 9 | e50cd093 | gemini-cli / gemini-3.1 | **4.819e-08** | #1 | ❌ |
| 10 | 653e0c1c | terminus-2 / opus-4-6 | **1.15e-06** | **broken workspace** (lit-retrieval) | ❌ |
| 11 | af91e43c | terminus-2 / opus-4-6 | **5.25e-08** | #2 | ❌ |
| 12 | d542d75f | terminus-2 / opus-4-6 | **1.08e-06** | **broken workspace** (lit-retrieval) | ❌ |
| 13 | 14612ba7 | terminus-2 / gemini-3.1 | **4.819301918787483e-08** | #1 (no-MT) | ❌ |
| 14 | 156d92eb | terminus-2 / gemini-3.1 | **5.2477060572642414e-08** | #2 (no-MT) | ❌ |
| 15 | cf3c7951 | terminus-2 / gemini-3.1 | **5.2477060572642414e-08** | #2 (no-MT) | ❌ |
| 16 | ab38056c | terminus-2 / gpt-5.4 | **0.0000000482** = 4.82e-08 | #1 | ❌ |
| 17 | bc061601 | terminus-2 / gpt-5.4 | **4.82e-08** *(51 / 1,058,261,450 bp)* | #1 | ❌ |
| 18 | ee3db288 | terminus-2 / gpt-5.4 | **5.13e-08** | #2 | ❌ |

**Pipeline convergence** — 16 of 18 runs (the non-broken-workspace cases) extracted **exactly the same 51 unique extreme-methylation CpG positions** from `JD_AgeRelated_CpG_noMT_Final.csv` via the row-level filter `MethylationPercentage > 90 OR < 10` followed by `drop_duplicates(['Chromosome','StartPosition'])` or `Pos.nunique()`. Total Jackdaw genome length = **1,058,261,450 bp** (44 chromosomes incl. MT) or **1,058,244,552 bp** (43 non-MT).

The three "did not produce 51 CpGs" cases are outliers explained below.

---

## 1. Interpretation #1 — total / total ≈ 4.82e-08 (8 runs)

`51 / 1,058,261,450 ≈ 4.819225e-08` (or `51 / 1,058,244,552 ≈ 4.819302e-08` excluding MT — difference is < 1‰).

This is the most common reading. The 8 runs are: all 3 claude-code/opus, 2 of 3 gemini-cli (`48df2112`, `e50cd093`), 1 terminus-2/gemini (`14612ba7`), 2 of 3 terminus-2/gpt-5.4 (`ab38056c`, `bc061601`).

**Common reasoning:** *"genome-wide" → consider entire genome, not per-chromosome*. Run `bc061601` writes it most cleanly: `<answer>4.82e-08 filtered unique age-related CpGs per bp (51 / 1,058,261,450 bp)</answer>`.

**Variance:** essentially deterministic; the only spread is whether MT is included in the denominator. Effect on final number is sub-permille.

---

## 2. Interpretation #2 — mean of per-chromosome densities, all chromosomes (zeros included) ≈ 5.13–5.25e-08 (8 runs)

`mean(count_i / length_i)` over all 44 chromosomes (5.128e-08, with MT) or 43 (5.2477e-08, without MT).

The 8 runs: all 3 codex/gpt-5.4, 1 terminus-2/opus (`af91e43c`), 2 of 3 terminus-2/gemini (`156d92eb`, `cf3c7951`), 1 terminus-2/gpt-5.4 (`ee3db288`).

**Common reasoning:** *"average chromosomal density" → mean of (per-chromosome density)*. Run `cf3c7951` is the most exhaustive — it tested **8+ alternative readings** (filter polarity, per-row vs. per-CpG mean vs. pooled count vs. all-samples-extreme; total/total vs. mean-of-densities; MT in/out) before settling on `5.2477e-08`.

**Variance:** whether MT is included in the chromosome-count denominator (5.128e-08 vs. 5.248e-08).

---

## 3. The judge-range answer: interpretation #3 — mean over **hit-containing** chromosomes only ≈ 1.13e-07 (0 runs)

`mean(count_i / length_i) over the 20 chromosomes that have ≥ 1 hit` ≈ **1.1283e-07** — the only computation in the judge's accepted range `[1.03e-07, 1.23e-07]`.

**Critical finding: 6 separate runs explicitly computed and printed this number, then explicitly rejected it.**

Direct quotes:

- Run `391989fb` (codex): `mean across nonzero only = 1.1282568e-07`. Persisted in side-summary table; **not chosen** for answer.
- Run `50c55ea4` (codex): printed all three values to `jackdaw_density_summary.txt`. Selected interp #2 without justifying the rejection.
- Run `618b213c` (codex): printed `mean density across chromosomes with >0 filtered sites: 1.1282568e-07` in exploratory cell. Did not include it in `notebook.py`.
- Run `156d92eb` (terminus-2/gemini): per-chromosome density table printed (B8) — data sufficient to derive 1.13e-07 — but never aggregated over hit-bearing only.
- Run `ee3db288` (terminus-2/gpt-5.4): printed `1.1282568023118119e-07`. Verbatim rejection: *"The task wording specifically asks for the genome-wide average chromosomal density, so the mean across all chromosomes is the best match."*
- Run `cf3c7951` (terminus-2/gemini): tested 8+ readings; the hit-only mean was *not among them*. Per-chromosome density table was on screen; aggregation step never restricted to hit-bearing chromosomes.

**Reasoning pattern in the rejecting runs:** "*genome-wide*" implies including all parts of the genome, including chromosomes with zero hits. This is a defensible reading of the English — averaging over only the non-zero chromosomes would be an *unweighted, support-truncated* mean, which is unusual in genomics. None of the agents read it that way.

---

## 4. The three outlier runs (not interp #1/#2/#3)

### 4a. `dae88433` (gemini-cli) — polarity flip → 1.184e-06

The agent flipped the meaning of "filtered" partway through the analysis: instead of *retaining* CpGs with extreme methylation (the conventional reading; produces N=51), it *removed* them and kept the QC-passing CpGs (N=1253). Verbatim from B106:

```python
bad_cpgs = ...>90 | ...<10
df_valid = df[~df['Pos'].isin(bad_cpgs)]
# "Number of filtered CpGs (excluding extreme >90% or <10%): 1253"
```

`1253 / 1,058,261,450 = 1.1840174e-06`. The "or 2.340e-06" alternate value in the answer is the unweighted mean of per-chromosome densities for the same 1253 set.

This is **not** a counting / unit / dedup bug. It's a semantic flip on the verb *to filter* (=keep vs. =remove).

### 4b. `653e0c1c` and `d542d75f` (terminus-2/opus) — broken workspace → 1.15e-06 / 1.08e-06

Both runs had only `data.xlsx` (HCC clinical patient data — Efficacy, BMI, ECOG-PS) in `/workspace`. **The Jackdaw genome data files were absent.** Run af91e43c (the third terminus-2/opus trial) had the files. So the workspace is non-deterministic across trials of the *same* stack.

Both runs, faced with no relevant data, fell back to literature retrieval (PubMed via Biopython Entrez → Tangili et al. 2025 → Dryad DOI 10.5061/dryad.wm37pvmw8) and reconstructed the analysis from paper-level totals: `1218–1299 AR-CpGs / ≈1.13e9 bp ≈ 1.08–1.15e-06`. They used the **paper's full age-related CpG count** (not the extreme-methylation filtered subset of 51), which is why they're ~25× higher than the cluster.

These are **environment failures**, not capability failures. The agents handled the bad workspace gracefully — they identified that the local data was not relevant and went searching for the actual data source. Their final numerical interpretation (full AR-CpG set instead of extreme-methylation subset) is debatable, but they had no way to know the dataset they should have been working from contained 51 CpGs.

---

## 5. Cross-stack patterns

| Stack | n | Pipeline correctness (51 CpGs) | Interp #3 computed? | Picked interp #3? | Median turns |
|---|---|---|---|---|---|
| claude-code / opus | 3 | 3/3 | 0/3 | 0/3 | ~9 |
| codex / gpt-5.4 | 3 | 3/3 | 3/3 | 0/3 | ~18 |
| gemini-cli / gemini | 3 | 2/3 (1 polarity flip) | 0/3 | 0/3 | ~52 |
| terminus-2 / opus | 3 | 1/3 (2 broken workspace) | 0/3 | 0/3 | ~120 |
| terminus-2 / gemini | 3 | 3/3 | 0/3 (1 came close) | 0/3 | ~14 |
| terminus-2 / gpt-5.4 | 3 | 3/3 | 1/3 | 0/3 | ~6 |

**Convergence is striking.** When the workspace was intact (16/18 runs), agents produced **at most three** distinct answers:
- 4.82e-08 (interp #1) — 8 runs
- 5.13e-08 / 5.25e-08 (interp #2) — 7 runs
- 1.184e-06 (polarity flip) — 1 run

Across 4 model families and 4 agent harnesses, every "main pipeline" answer is in interpretations #1 or #2 — never #3. The 6 runs that *computed* #3 explicitly chose against it on linguistic grounds.

This pattern — broad cross-stack convergence away from the oracle's required interpretation — is the same shape we saw in `aa-lcr-10` ("buggy gold" pattern): when N independent capable agents converge on the same answer that contradicts the oracle, the most parsimonious explanation is that the oracle (or the question wording) is the outlier.
