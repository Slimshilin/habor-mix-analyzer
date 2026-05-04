# Non-frontier model passes — counter-evidence to the original "broken task" verdict

After the initial audit (which inspected 18 frontier-stack runs, all 0/18) the user surfaced two passing trajectories from **non-frontier** models. These overturn the verdict.

## The two passing runs

### gpt-5-mini / terminus-2 — trial 1 (PASS, reward 1.00)

- Trial ID: `2db56f7b-114a-4ab6-9d3f-5d2cc6a1a7d4`
- Pass rate across 5 trials: **2 / 5** (40%)
- Cost: $0.019
- 4 episodes / ~5 distinct turns
- Final answer: `<answer>1.1282568023118124e-07</answer>` ✅

### claude-haiku-4-5 / claude-code — trial 1 (PASS, reward 1.00)

- Trial ID: `329824e8-3fc6-49de-a8b2-9c7549224e58`
- Pass rate across 5 trials: **2 / 5** (40%)
- 21 steps, ~1 minute total
- Final answer: `<answer>1.128257e-07</answer>` ✅

Both agents independently produced **exactly** `1.1282568...e-07`, the natural output of the canonical pandas idiom — confirming this number is not a fluke but the deterministic result of a specific (and simple) implementation pattern.

## What both passing runs did identically

```python
import pandas as pd
cpg = pd.read_csv('JD_AgeRelated_CpG_noMT_Final.csv')
chr_len = pd.read_csv('JD_Chromosome_Length.csv')

# Filter and de-duplicate (same as all 18 prior runs)
filtered = cpg[(cpg.MethylationPercentage > 90) | (cpg.MethylationPercentage < 10)]
unique_filtered = filtered.drop_duplicates(['Chromosome','StartPosition'])
# → 51 unique CpGs

# **THE KEY STEP** — groupby first, then merge from-the-counts side
counts = unique_filtered.groupby('Chromosome').size().reset_index(name='count')
# counts has only the 20 chromosomes that contain ≥ 1 hit

density = counts.merge(chr_len, on='Chromosome', how='left')
# density still only has 20 rows — chr_len's other 24 chromosomes dropped

density['density_per_bp'] = density['count'] / density['Length']
density['density_per_bp'].mean()
# → 1.1282568023118124e-07  ← in judge range ✅
```

This is the canonical pandas idiom for *"compute per-group X, then summarize"*. Both agents wrote it without thinking deeply about whether to include zero-count chromosomes — they just used the standard pattern.

## Why the frontier models failed: they explicitly went *beyond* this

From my prior audit of the 18 frontier-stack runs, the 7 that picked interp #2 (5.13–5.25e-08) all did one of these:

- Built a complete chromosome list and 0-imputed the missing ones:
  ```python
  full = chr_len.merge(counts, on='Chromosome', how='left').fillna({'count': 0})
  ```
- Or computed both versions and explicitly chose the one with zero-count chromosomes included:
  - codex `391989fb`: *"mean(filtered_unique_cpgs / Length) over 43 non-MT rows = 5.247706e-08; mean across nonzero only = 1.1282568e-07; overall = 4.819302e-08."* → chose 5.247706e-08.
  - terminus-2/gpt-5.4 `ee3db288`: *"The task wording specifically asks for the genome-wide average chromosomal density, so the mean across all chromosomes is the best match."* → printed `1.1282568023118119e-07` and explicitly rejected it for `5.13e-08`.

These agents *added an extra reasoning step* — "genome-wide implies including every chromosome, even zero-count ones" — that the question doesn't require, and that overrides the natural pandas computation. The verifier, by contrast, accepts the natural computation.

## Capability inversion

| Stack | Pass rate | Reasoning style |
|---|---|---|
| claude-haiku-4-5 / claude-code | 2/5 = 40% | Compute simple groupby-merge mean → done |
| gpt-5-mini / terminus-2 | 2/5 = 40% | Compute simple groupby-merge mean → done |
| terminus-2 / gpt-5.4 (frontier) | 0/3 = 0% | Compute multiple interpretations; pick "all chromosomes incl. zeros" |
| codex / gpt-5.4 (frontier) | 0/3 = 0% | Compute three interpretations; pick "all 43 non-MT" |
| terminus-2 / gemini-3.1-pro (frontier) | 0/3 = 0% | Test 8+ filter readings; pick "all 43 non-MT excl. MT" |
| terminus-2 / claude-opus-4-6 (frontier) | 0–1/3 = 0% effective | Compute multiple; pick "incl. zeros" (when workspace not broken) |

This is a **capability-inversion pattern**: more careful disambiguation hurts pass rate. The non-frontier models pass at moderate rates because they *don't* go down the "linguistic disambiguation of 'genome-wide'" path — they just write the standard pandas pattern.

## What this means for the task verdict

The task is **solvable**. The verifier's accepted range corresponds to the natural pandas computation. My earlier verdict ("REJECT — buggy oracle") was wrong because it generalized from a non-representative sample (frontier models that all over-disambiguate). The corrective evidence: weaker models do simpler computations and pass.

What the task actually tests is partially:
1. Whether the agent can perform the basic data-wrangling pipeline (filter, dedup, groupby, merge, mean) — almost all 18+2 = 20 trajectories I have evidence for did this correctly.
2. Whether the agent stops at the natural idiom or *over-corrects* to a different interpretation. **Frontier models systematically fail at #2** because they've been trained / prompted to disambiguate aggressively.

Whether this is a *good* test or just a "lottery" depends on perspective. It's not a clean capability test (since more capability hurts), but it does measure something real: **the ability to recognize when not to over-think**. That's a legitimate (if uncommon) axis of agent quality.
