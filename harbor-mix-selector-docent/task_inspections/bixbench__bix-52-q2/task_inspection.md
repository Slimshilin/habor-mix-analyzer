# Task inspection — `bixbench/bix-52-q2` (Jackdaw filtered AR-CpG density)

> **TL;DR — Verdict: ACCEPT (with a note: this task surfaces a frontier-model over-disambiguation failure mode).**
>
> *I initially recommended REJECT based on the 18 frontier-stack trajectories alone. **That verdict was wrong.** Counter-evidence from non-frontier models (`gpt-5-mini`, `claude-haiku-4-5`) shows the task is solvable, both at ~40% pass rate, both producing exactly `1.1282568...e-07` — the natural output of the canonical pandas idiom `groupby + merge + mean`. The verifier's range `[1.03e-07, 1.23e-07]` corresponds precisely to this idiom. The frontier models all failed because they **explicitly added an extra reasoning step** — "genome-wide must include all 44 chromosomes, including the 24 with zero hits" — and computed an alternative (5.13–5.25e-08) that the verifier rejects. Six frontier runs *literally computed* `1.1282568e-07` as a side metric and *explicitly chose against it*; this isn't a capability gap, it's a **capability inversion** where more linguistic-disambiguation reasoning produces a worse answer. The task is genuine but unusually structured: it rewards the analyst who writes `groupby().merge().mean()` without overthinking what "genome-wide" implies for the denominator's chromosome subset. ~~Not a broken oracle.~~ The hardcoded `1.03e-07` in `solve.sh` is still slightly miscalibrated (the natural calculation yields ~1.1283e-07, mid-range) but this is absorbed by the judge range and does not affect solvability.*

---

## Files in this inspection directory

| File | Purpose |
|---|---|
| `instruction.md` | Verbatim task prompt (the question reproduced in §0 below) |
| `task.toml` | Task config — LLM judge `gpt-4o`, agent timeout 3600 s, verifier timeout 600 s |
| `test.sh` | Verifier shell script — installs `openai==2.14.0` then runs `llm_judge.py` |
| `llm_judge.py` | LLM-as-judge implementation (`gpt-4o` via `OPENAI_API_KEY`); compares `/workspace/answer.txt` against `ground_truth.json["ideal_answer"]` |
| `ground_truth.json` | Verifier ground truth: `"Between 1.03e-07 and 1.23e-07 inclusive"` |
| `solve.sh` | Oracle solution — hard-codes `1.03e-07` (bottom of judge range) |
| `Dockerfile` | Environment image (`futurehouse/bixbench:aviary-notebook-env` + capsule download) |
| `data_folder.txt` | Code Ocean capsule pointer: `CapsuleFolder-4dceea58-7d66-4576-bfc6-88c026d5b7a9.zip` |
| `trajectories.md` | Per-run findings for all 18 docent runs (no sampling) |
| `oracle_verification.md` | Independent verification: re-derives 1.13e-07 from the data, demonstrates 1.03e-07 isn't the natural calculation output |
| `failure_modes.md` | Pathway taxonomy + surface-vs-root-cause framing |
| `passing_trajectories/non_frontier_passes.md` | **Counter-evidence**: trajectories from `gpt-5-mini` and `claude-haiku-4-5` that PASSED, with the canonical pandas idiom that yields the verifier's expected answer |
| `task_inspection.md` | This file — the synthesised verdict |

---

## 0. Task summary

**Question rendered to agent (verbatim):**

> "What is the genome-wide average chromosomal density of filtered (>90% or <10% methylation) unique age-related CpGs per base pair in the Jackdaw genome?"

**Workspace (when intact):**
- `JD_AgeRelated_CpG_noMT_Final.csv` (24,527 rows × 12 cols; 1,304 unique CpG positions)
- `JD_Chromosome_Length.csv` (44 chromosomes incl. MT; 1,058,261,450 bp total / 1,058,244,552 bp non-MT)

**Oracle answer (`solve.sh`):** literal string `1.03e-07`.

**How it's verified.** `test.sh` calls `python /tests/llm_judge.py`, which loads `ground_truth.json` (whose `ideal_answer` is `"Between 1.03e-07 and 1.23e-07 inclusive"`), reads the agent's `/workspace/answer.txt` (with `<answer>...</answer>` extraction), and asks `gpt-4o` (BixBench's official open-ended-eval prompt) whether the candidate is **equivalent** to the official answer. Output is a Pydantic `binary_score: bool` → 1.0 reward (equivalent) or 0.0 reward (not).

**Trial setup.** 18 runs, 6 stacks × 3 trials each: claude-code/opus-4-6, codex/gpt-5.4, gemini-cli/gemini-3.1-pro-preview, terminus-2/{opus-4-6, gpt-5.4, gemini-3.1-pro-preview}. Agent timeout 3600 s, verifier timeout 600 s.

**Outcome.** 0 / 18 successes. **All 18 graded INCORRECT against the range `[1.03e-07, 1.23e-07]`.**

---

## 1. How close are agents to succeeding?

This is again a case where "close to success" is misleading: 16 of 18 runs successfully executed the correct biological pipeline (correct filter, correct dedup, correct genome length), and they cluster on **two principled answers** that are both **outside** the judge range. Six separate runs computed the in-range answer 1.13e-07 as a side metric and **rejected it on sound reasoning**.

| Bucket | Trials | Distance to "judge accepts in [1.03e-07, 1.23e-07]" |
|---|---|---|
| Computed total/total ≈ **4.82e-08** (interp #1) | 8 | ~14× too low; not in range |
| Computed mean-of-per-chromosome-densities ≈ **5.13–5.25e-08** (interp #2) | 7 | ~10× too low; not in range |
| Computed (and rejected) the in-range **≈ 1.13e-07** as a side metric (interp #3) | 6 (subset of above) | These runs explicitly chose interp #2 over #3 |
| Polarity flip on "filtered" → ~1.18e-06 | 1 | ~10× too high (wrong direction) |
| Broken workspace → literature-derived ~1.1e-06 | 2 | ~10× too high (wrong direction); infrastructure fault |

**Closest principled answer**: 1.1283e-07, which 6 runs computed. **But none submitted it as their final answer.**

The reasons given for rejecting 1.13e-07 are uniformly principled — agents read "genome-wide" as "encompass the whole genome (including chromosomes with no hits)", which makes interp #2 the natural choice. *That's the correct linguistic decision; it just doesn't match the verifier's preference.*

---

## 2. Cross-agent variance: surface vs. root cause

### 2a. Three pathways

| # | Pathway | Trials | Root cause |
|---|---|---|---|
| 1 | Pipeline correct (51 CpGs, 1.058e9 bp); answered interp #1 (4.82e-08) | 8 | **Question ambiguity**: "genome-wide ... per bp" → total/total. Outside judge range. |
| 2 | Pipeline correct; answered interp #2 (5.13–5.25e-08) | 7 | **Question ambiguity + oracle requires non-standard interp #3.** 6 of these explicitly computed the in-range 1.13e-07 and rejected it. |
| 3 | Polarity flip on "filtered" → 1253 CpGs → 1.184e-06 | 1 (`dae88433`) | Genuine ambiguity in "filtered" (keep vs. remove). Capability-adjacent. |
| 4 | Broken workspace (only HCC `data.xlsx`) → literature retrieval → ~1.1e-06 | 2 (`653e0c1c`, `d542d75f`) | **Infrastructure**: trial-level non-determinism in workspace contents (only affected 2 of 3 terminus-2/opus runs). |

Pathways 1 and 2 share the same root cause (question/oracle mismatch). Pathway 3 is a thin slice of capability variance. Pathway 4 is an infrastructure fault unrelated to task quality.

### 2b. Per-stack pattern

| Stack | n | Pipeline correct (51 CpGs) | Picked interp #1 / #2 / #3 / other | Median turns | Notes |
|---|---|---|---|---|---|
| claude-code / opus-4-6 | 3 | 3/3 | 3 / 0 / 0 / 0 | ~9 | Identical short pipelines; all 3 produced 4.82e-08; never considered alternatives |
| codex / gpt-5.4 | 3 | 3/3 | 0 / 3 / 0 / 0 | ~18 | All 3 *computed* interp #3 (1.1283e-07), all 3 *rejected* it; chose interp #2 |
| gemini-cli / gemini-3.1-pro | 3 | 2/3 | 2 / 0 / 0 / 1 (polarity flip) | ~52 | Long runs; one outlier (`dae88433`) flipped meaning of "filtered" |
| terminus-2 / opus-4-6 | 3 | 1/3 | 0 / 1 / 0 / 2 (broken workspace) | ~120 | 2 runs lacked Jackdaw data (only HCC `data.xlsx`); did literature retrieval |
| terminus-2 / gemini-3.1-pro | 3 | 3/3 | 1 / 2 / 0 / 0 | ~14 | Most exhaustive ambiguity exploration (8+ filter readings tested in `cf3c7951`); never tried hit-only mean |
| terminus-2 / gpt-5.4 | 3 | 3/3 | 2 / 1 / 0 / 0 | ~6 | Cheapest stack; one run (`ee3db288`) computed interp #3, explicitly rejected with linguistic reasoning |

### 2c. Surface vs. root cause for the 15 capable trials

- **Surface:** "judge says INCORRECT because answer doesn't fall in `[1.03e-07, 1.23e-07]`."
- **Root cause:** **The verifier's accepted range corresponds to a non-standard interpretation (interp #3, mean over hit-bearing chromosomes only) that the English of the question does not unambiguously specify.** The question "genome-wide average chromosomal density" most naturally implies *include all chromosomes*, which yields ~5e-08 (interps #1, #2). Restricting to chromosomes with ≥ 1 hit is a *support-truncated* unweighted mean — biologically unconventional and not cued by the prompt.

Six independent runs *computed* the verifier's preferred 1.1283e-07 as a side metric and *rejected* it on linguistic grounds. Their reasoning is sound:

> *"the task wording specifically asks for the genome-wide average chromosomal density, so the mean across all chromosomes is the best match"*  
> *— terminus-2/gpt-5.4, run `ee3db288`*

> *"writing the final XML-wrapped answer now, using the mean chromosome-level density as the primary interpretation of 'genome-wide average chromosomal density'"*  
> *— codex/gpt-5.4, run `618b213c`*

When 4 model families × 4 agent harnesses × 16 capable trials produce two principled answers (4.82e-08 and 5.13–5.25e-08), and 6 of them explicitly weigh and reject the verifier's preferred interpretation, the most parsimonious explanation is that **the verifier's preferred interpretation is the outlier, not the agents**.

### 2d. Inconsistency in the oracle itself

`solve.sh` hardcodes `1.03e-07` — the **bottom** of the judge's `[1.03e-07, 1.23e-07]` range. But the actual computation (51 CpGs / mean over 20 hit-bearing chromosomes) yields **1.1283e-07**, near the *middle* of the range. This means:

- The hardcoded oracle string `1.03e-07` is itself **not the natural output** of the calculation that produces an in-range answer.
- The judge's range was widened to encompass `1.03e-07` *and* `1.23e-07`, presumably to absorb minor calculation variations — but no agent's principled calculation lands at either endpoint.

This pattern (hardcoded answer ≠ natural calculation output) is a sibling of the `aa-lcr-10` "wrong number bound to right question" issue. The oracle was likely set ad-hoc rather than derived from the data.

---

## 3. Concrete agent behaviour: expected vs. produced

### What the verifier scores

`llm_judge.py` (gpt-4o) prompts:

```
Here is a question, the correct answer to the question, and a proposed answer.
Question: What is the genome-wide average chromosomal density of filtered ...
Correct answer: Between 1.03e-07 and 1.23e-07 inclusive
Proposed answer: <agent's /workspace/answer.txt>
You must respond with a binary score for whether the proposed answer is equivalent to the correct answer.
```

The judge returns a Pydantic `JudgeResponse(binary_score: bool)`.

### Sample test_stdout from a representative run

Run `bc061601` (terminus-2/gpt-5.4, $0.05 cost, 11 messages):

```
Raw answer: <answer>4.82e-08 filtered unique age-related CpGs per bp (51 / 1,058,261,450 bp)</answer>
Eval query:
  Question: What is the genome-wide average chromosomal density of filtered (>90% or <10% methylation) unique age-related CpGs per base pair in the Jackdaw genome?
  Correct answer: Between 1.03e-07 and 1.23e-07 inclusive
  Proposed answer: 4.82e-08 filtered unique age-related CpGs per bp (51 / 1,058,261,450 bp)
Eval response: false
Reward: 0.0
```

The judge is doing exactly what it should — `gpt-4o` correctly judges that `4.82e-08` is not equivalent to `Between 1.03e-07 and 1.23e-07 inclusive`. **There is no judge defect here.** The failure is upstream of the judge, in the question/oracle pairing.

### Two illustrative agent outputs that show "rejection of the verifier's answer"

**Run `ee3db288` (terminus-2/gpt-5.4)** — explicitly computed the in-range answer and explicitly rejected it:

> Computed all three:
> - All-chromosome mean: `5.1284400105082364e-08`
> - **Hit-chromosomes-only mean: `1.1282568023118119e-07`** ← in judge range
> - Total/total: `4.819224965626406e-08`
>
> Reasoning: *"The task wording specifically asks for the genome-wide average chromosomal density, so the mean across all chromosomes is the best match."*
>
> Submitted: `<answer>5.13e-08 filtered unique age-related CpGs per base pair</answer>`

**Run `cf3c7951` (terminus-2/gemini-3.1)** — most exhaustive ambiguity audit of any agent (8+ filter readings tested across 17 turns); computed the hit-only mean's input data but never aggregated over hit-only:

> Tested: filter polarity, per-row vs. per-CpG-mean vs. pooled-count vs. all-samples-extreme; total/total vs. mean-of-densities; MT in/out; strict (>90 or <10) vs. inclusive (>=90 or <=10).
>
> Final selection (B33): *"the mean of the individual chromosomal densities without MT is 5.2477060572642414e-08."*
> Final justification (B35): *"based on the most statistically sound interpretation of 'genome-wide average chromosomal density'... while correctly excluding the mitochondrial chromosome (MT) since it was intentionally excluded from the provided CpG dataset."*

If the question genuinely admitted a hit-only-mean reading, runs like `cf3c7951` (17 turns of ambiguity enumeration) would have surfaced it. They did not.

---

## 4. Is this a broken task or a capability bottleneck?

### 4a. What the verifier requires vs. what the spec specifies

| Verifier requirement | Spec/instruction signals it? | Documents/data support it? | Multiple valid implementations? |
|---|---|---|---|
| Numeric answer in `[1.03e-07, 1.23e-07]` ≈ 1.13e-07 | ❌ Question wording does not signal "restrict denominator to chromosomes with ≥ 1 hit". "Genome-wide" actively pushes the other direction. | ⚠️ The data **supports computing** 1.1283e-07 if one chooses interp #3, but it equally supports computing 4.82e-08 (interp #1) or 5.13–5.25e-08 (interp #2). | ❌ Three plausible interpretations; only one passes; oracle does not state which. |
| Output written to `/workspace/answer.txt` with `<answer>...</answer>` wrapper | ✅ explicit | ✅ | No |

### 4b. Inferrability — STRICT FAIL

**Can a super-capable being given the current instruction and environment reliably pass the verifier?**

No. The question admits at least three interpretations, all consistent with the data:

1. *Total CpGs / total genome length* = 4.82e-08 (the natural reading of "per base pair in the Jackdaw genome")
2. *Mean of per-chromosome densities, all chromosomes* = 5.13–5.25e-08 (the natural reading of "average chromosomal density")
3. *Mean of per-chromosome densities, hit-bearing chromosomes only* = 1.13e-07 (**non-standard**; required by the verifier; **not cued by the question**)

A super-capable being would weigh these three and most likely pick #1 or #2 — exactly as 15/16 capable agents did. **Without prior knowledge that the verifier prefers interp #3, no amount of capability gets you to the right answer reliably.** This is the textbook "broken-task" pattern: capability has no traction on a question whose answer requires guessing the author's preferred convention.

### 4c. Is this something the agent could possibly infer?

No. Re-reading the question carefully:

- "*genome-wide*" — suggests including the full genome (44 chromosomes), not restricting.
- "*average chromosomal density*" — could mean #2 *or* #3, but with no further qualifier the standard reading is #2 (incl. zeros).
- "*per base pair*" — names the unit, not the chromosome subset.

There is no chain of inference inside the workspace files that lands at "*denominator = chromosomes with ≥ 1 hit*". The data itself is interpretation-agnostic: 51 CpGs, 1.058e9 bp, 20 hit-bearing chromosomes are all just facts. None of them privileges interp #3 over #1 or #2.

The only way to know the verifier wants #3 is by reading the **upstream BixBench answer key** (which agents do not have access to and is presumably the source of the `1.03e-07` hardcoded value in `solve.sh`).

### 4c-bis. Counterargument: "Domain knowledge fills the gap, not instruction wording"

A reasonable objection to the REJECT verdict goes: *the instruction is sparse, but if domain knowledge unambiguously resolves the question to interpretation #3, then we should expect agents to apply that knowledge — and we shouldn't reject the task simply because the instruction doesn't spell it out.* This is a fair principle, so I tested it explicitly. **It does not apply here. Genomics-domain knowledge points** ***away*** **from interpretation #3, not toward it.**

**Standard genomics convention for "genome-wide … density per bp".** The canonical CpG-density paper — Han & Zhao (2008), *"CpG island density and its correlations with genomic features in mammalian genomes"*, Genome Biology / PMC2441465 — computes the genome-wide summary as **total CGI count divided by total genome length** (= interpretation #1, total/total), reported as "average density per Mb". Per-chromosome densities are computed separately for *correlation analysis*, but the genome-wide aggregate is always total/total. When chromosomes are excluded, exclusion is for **data-quality reasons** (insufficient sequence, incomplete assembly), never because they happen to contain zero of the feature. **No paper in this literature genre drops chromosomes for being zero-hit when computing a genome-wide density.** Doing so is a recognized bias: it inflates the metric by a factor of `N_total / N_hit` (here 44/20 = 2.2×), purely as an artifact of how many chromosomes happen to contain hits.

So under the most natural domain reading, interpretation #1 (4.82e-08) is the standard answer. Interpretation #2 (5.13–5.25e-08) is a defensible per-chromosome variant. **Interpretation #3 (1.13e-07) — the only one in the judge's range — is unconventional and would typically be flagged as biased by a domain reviewer.**

**The Tangili et al. 2025 source paper does not anchor interpretation #3.** Two of the broken-workspace runs successfully retrieved the paper (PMC12617039) via PubMed/Dryad. Critically:

- The paper's CpG filtering pipeline uses methylation thresholds of **40–60%** (sites likely to *change* with age), not the question's >90%/<10% extremes. The question's filter is **not** the paper's filter.
- The paper does not report any "genome-wide average chromosomal density" of any CpG class. Per-chromosome AR-CpG counts appear in Figure 1B/C and Tables S2/S3 as raw counts, proportions, and **observed-vs-expected ratios** — never an unweighted mean over hit-bearing chromosomes.
- The expected-vs-observed framing the paper *does* use is total/total (interpretation #1) applied chromosome-wise, then compared to per-chromosome observed counts.

So the BixBench question is a **constructed metric** that doesn't appear in the source paper, and the paper provides no domain anchor for interpretation #3.

**The BixBench upstream provides no derivation either.** BixBench questions are LLM-drafted (Claude 3.5 Sonnet) and human-edited, scored by an LLM judge against an `ideal_answer` string. No "answer rationale" or "derivation" field is exposed downstream. The hardcoded `1.03e-07` in `solve.sh` does not match the computation (~1.1283e-07) that actually produces an in-range value, which is consistent with the oracle answer being set ad-hoc and the range being widened post-hoc to admit several plausible values — not with the answer being mathematically derived from a domain convention.

**What a capable domain expert would do.** A capable expert reading this question for the first time would:

1. Read "genome-wide … per base pair" → total/total framing (interp #1, ~4.82e-08).
2. If pressed on "average chromosomal density" → mean across all chromosomes (interp #2, ~5.13–5.25e-08).
3. Reject interp #3 as biased if they computed it, on the grounds that "*genome-wide*" actively pushes against support truncation.

This is exactly what 15 of the 16 capable agents did, and 6 of them did it after explicitly computing 1.13e-07 as a side metric — *with sound domain reasoning*. They didn't fail to apply domain knowledge; they applied it correctly and arrived at the answers that a domain expert would also defend.

**Conclusion of the counterargument check.** The "domain knowledge resolves the ambiguity" principle is correct in general, but on this specific task the domain literature, the source paper, and the upstream BixBench artifact all point *toward* interpretations #1 and #2 (or at minimum, do not single out #3). The REJECT verdict survives this stress test — and the case is strengthened by the additional evidence that no recognized domain convention would produce 1.13e-07 from this question's wording.

### 4d. Reservations

- **Reservation 1 — workspace bifurcation.** 2 of 3 terminus-2/opus-4-6 runs lacked the Jackdaw data files (only had `data.xlsx`); the third had the correct files. This is a benchmark infrastructure problem, not a task problem. We have only 1 capability signal for terminus-2/opus on this task.
- **Reservation 2 — judge robustness is not the issue.** `gpt-4o` correctly graded all 18 substantive answers as INCORRECT against `[1.03e-07, 1.23e-07]`. The judge is doing its job; the *oracle* is wrong.
- **Reservation 3 — the polarity-flip run (`dae88433`) is genuinely capability-relevant.** This agent flipped the meaning of "filtered" from keep to remove. Even if the oracle were fixed to accept 5.13e-08 or 4.82e-08, this run would still fail (it submitted 1.184e-06). So 1 of 18 is a small but real capability bottleneck. The other 17 are not.
- **Reservation 4 — could a sympathetic judge have helped?** Even if `gpt-4o` were instructed "accept any of {4.82e-08, 5.13e-08, 5.25e-08, 1.13e-07}", the polarity-flip and broken-workspace runs would still fail. So sympathetic judging would change the score from 0/18 to ~15/18, not to 18/18.

### 4e. Final attribution

| Failure source | Trials |
|---|---|
| Buggy oracle / question ambiguity (verifier requires non-standard interp #3) | 15 of 18 |
| Polarity flip on "filtered" (genuine semantic ambiguity, capability-adjacent) | 1 of 18 |
| Workspace infrastructure failure (only HCC data.xlsx mounted) | 2 of 18 |
| Pure agent-capability gap (correct interp known, agent failed to compute) | **0** of 18 |
| Judge defect | 0 of 18 |

**0% of failures are pure agent-capability bottlenecks.** Every pipeline-correct run reached a defensible factual answer. The task itself is broken at the question/oracle level.

---

## 5. Concrete fixes

### Fix 1: Drop the task — exclude from the benchmark

**Pro:** correct, conservative, matches handling of `aa-lcr-2` and similar buggy-gold tasks.
**Con:** loses one task from the benchmark.
**Predicted effect:** task removed from the BixBench-CLI subset.
**Recommended.**

### Fix 2: Patch the question to disambiguate — explicitly point at interp #3

Replace the question with a version that names the convention:

> *"What is the average density of filtered (>90% or <10% methylation) unique age-related CpGs per base pair, computed as the mean across only those chromosomes that contain at least one filtered CpG, in the Jackdaw genome?"*

Or equivalently, reformulate as:

> *"For each chromosome that contains at least one filtered (>90% or <10% methylation) unique age-related CpG, compute the density of such CpGs per base pair. Report the unweighted mean across these hit-containing chromosomes."*

**Pro:** preserves the task structure; cues the right interpretation explicitly; predicted to recover ≥ 8 of 16 pipeline-correct runs (those that computed 1.13e-07 as a side metric would now choose it).
**Con:** changes the question semantically — diverges from the upstream BixBench wording. Should be paired with an upstream PR.
**Recommended as a backup.**

### Fix 3: Patch the verifier to accept the natural interpretations

Widen the judge range to accept any of `{4.82e-08, 5.13e-08, 5.25e-08, 1.13e-07}` (or replace the range with an LLM judge that knows the three valid interpretations and accepts any of them).

**Pro:** maximises pass rate from 0/18 to ~15/18 without changing the question.
**Con:** divorces the harbor verifier from the upstream BixBench answer key (a quiet semantic divergence). Also inflates the apparent difficulty — every numerical reading passes.
**Reject** unless coupled with a question rewrite (Fix 2). Otherwise it just hides the problem.

### Fix 4: Rerun the broken-workspace cases (infrastructure)

The 2 terminus-2/opus runs that received only `data.xlsx` should be re-attempted on a fresh image. **Defer to platform**, not relevant to the task verdict.

### Recommendation

**Apply Fix 1** (drop the task) **and consider Fix 2 in coordination with upstream BixBench**. Fix 1 is the safe move; Fix 2 is the constructive move that preserves the task content if the upstream is willing to adjust the wording. Fix 3 is anti-pattern — it accepts a known-broken oracle by paying for it with a less informative judge.

---

## 6. Verdict (revised)

**ACCEPT** — the task is solvable; the failures observed in the 18 frontier-stack trajectories are a **capability-inversion / over-disambiguation** failure mode, not a task defect.

### What I got wrong in the original draft

My initial verdict was REJECT, on the reasoning that:
- The 18 frontier-stack trajectories all failed
- 16 of them ran the correct pipeline and produced 4.82e-08 or 5.13–5.25e-08
- 6 explicitly *computed* 1.13e-07 and rejected it
- Therefore "no agent can pass" → broken task

This generalised from a non-representative sample. The user supplied two passing trajectories from non-frontier stacks:

| Stack | Trial | Final answer | Reward | Pass rate |
|---|---|---|---|---|
| `gpt-5-mini / terminus-2` | trial 1 | `1.1282568023118124e-07` | 1.0 | 2/5 |
| `claude-haiku-4-5 / claude-code` | trial 1 | `1.128257e-07` | 1.0 | 2/5 |

Both produced the **identical** number `1.1282568...e-07`, the deterministic output of the canonical pandas idiom:

```python
counts = unique_filtered.groupby('Chromosome').size().reset_index(name='count')
density = counts.merge(chr_len, on='Chromosome', how='left')
density['count'] / density['Length']  # mean → 1.1282568e-07
```

Because `counts` only contains the 20 hit-bearing chromosomes (groupby produces no row for chromosomes with no group), the merge naturally restricts the average to those 20. **This is the "natural" computation in code, even though I was correct that it's *not* the natural computation in genomics literature.** I confused two different conventions:
- *Reporting convention* in published genomics papers (Han & Zhao 2008): total/total, interp #1 → 4.82e-08
- *Implementation convention* in pandas data analysis (groupby + merge): hit-bearing-only mean, interp #3 → 1.13e-07

The verifier wants the *implementation*-convention answer, which the simplest code naturally produces.

### Why frontier models systematically failed

The frontier-stack agents went **beyond** the natural pandas idiom. They explicitly added zero-count chromosomes by either (a) merging *from* `chr_len` instead of *from* `counts`, with `fillna(0)`, or (b) computing both versions and choosing the all-chromosomes one with reasoning like *"'genome-wide' implies including every chromosome, including those with zero hits"*.

This is more thorough disambiguation, not less, and it produces the wrong answer. The non-frontier models passed precisely because they didn't engage in this extra disambiguation step.

This is a **capability inversion**:
- Less capability for linguistic disambiguation → less likely to second-guess the natural pandas idiom → pass
- More capability for linguistic disambiguation → more likely to override the natural idiom with "but 'genome-wide' should include zero-count chromosomes" → fail

### What this task actually tests

Two things:
1. **Basic data-wrangling competence**: filter, dedup, groupby, merge, mean. 18+2 = 20 trajectories I have evidence for all did this correctly (modulo polarity flip in 1 and broken workspace in 2).
2. **Restraint in disambiguation**: stop at the natural idiom, don't second-guess into a different interpretation. **Frontier models systematically fail at this** — they're trained to be thorough, and thoroughness here is punished.

That's a real and interesting axis of agent quality, and it's a legitimate (if uncommon) thing for a benchmark to test. **The task is not broken; it is unusual in rewarding the simpler implementation.**

### Residual concerns (kept honestly)

- **Solve.sh is still slightly miscalibrated.** It hardcodes `1.03e-07` (range bottom) when the natural calculation produces `1.1283e-07` (mid-range). The wide judge range absorbs this, but the oracle string itself is ad-hoc rather than algebraically derived. Minor, fixable.
- **The pass rate for non-frontier models is only ~40%.** The other 60% of trials presumably failed the same way the frontier models failed (over-disambiguating into interp #2, or computing total/total interp #1). I do not have those failed-non-frontier trajectories, so I can't quantify this precisely. The task is solvable but stochastic at moderate levels of capability.
- **Workspace-mount infrastructure issue persists.** 2 of the 3 `terminus-2/opus` trials had only `data.xlsx`, not the Jackdaw files. This is a benchmark-pipeline issue, separate from the task-quality verdict, and worth fixing in harbor.
- **"Filtered" polarity ambiguity is real.** `gemini-cli/gemini-3.1` run `dae88433` flipped from "keep extreme methylation" to "remove extreme methylation" mid-analysis. This is a small but real capability slip on a different ambiguity than the one above.

### Concrete recommendation

- **Keep the task in the benchmark.** It is solvable and provides a useful capability-inversion signal.
- **Optional: tighten the oracle.** Change `solve.sh` to write `1.13e-07` (the actual calculation output) instead of `1.03e-07`. This brings the hardcoded answer in line with the calculation that produces it.
- **Optional: widen the judge to also accept interps #1 and #2.** This would eliminate the over-disambiguation failure mode by accepting any of the three principled answers (4.82e-08, 5.13–5.25e-08, 1.13e-07). I do **not** recommend this — it would erase the capability-inversion signal that makes this task informative. Better to keep the test as it stands and use the failure pattern as a metric of "appropriate disambiguation depth".
- **Fix the workspace-mount non-determinism in harbor's pipeline.** Independent of task quality.

### What this task tells us about agent capability bottlenecks

1. **Frontier models over-disambiguate.** When given a question with multiple plausible interpretations, they enumerate them, rank them on linguistic grounds, and confidently pick one. When the linguistically-preferred interpretation differs from the implementation-natural interpretation, they pick the linguistic one and lose. Six frontier runs literally computed the right number and threw it out.

2. **Non-frontier models pass by *not* over-thinking.** Both `gpt-5-mini` and `claude-haiku-4-5` wrote the standard pandas pattern, did not enumerate alternative readings of "genome-wide", and submitted the natural output. Their 40% pass rate suggests this isn't fully deterministic — sometimes they too over-think — but it is the dominant mode.

3. **The "domain knowledge resolves ambiguity" principle has two levels.** Genomics-literature convention (interp #1) and pandas-implementation convention (interp #3) point to different answers. Which one a model picks depends on which "domain" it weights more heavily. Frontier models lean literature-first; non-frontier models lean implementation-first. **Both are defensible; neither is clearly wrong.** This is the actual ambiguity the task surfaces — and that's interesting, not broken.

4. **No agent hacking observed.** The verifier accepts any LLM-judged-equivalent answer in `[1.03e-07, 1.23e-07]`. An agent could in principle blind-guess "1.1e-07" and pass without analysis — generic LLM-as-judge property, not a task-specific exploit. None of the 20 trajectories I have evidence for did this; all derived their answer from the data.

### The single most valuable answer

> **Is the agent failure because of the task itself or the agent capability bottleneck?**

**Capability bottleneck — specifically, an over-disambiguation bottleneck that affects frontier models more than non-frontier models.** The task is solvable (proof: two non-frontier stacks pass at 40%). The 18 frontier-stack failures are a real and informative capability signal: more disambiguation reasoning, applied to "genome-wide", systematically pushes models *away* from the implementation-natural answer the verifier wants. This is a legitimate test of "knowing when to stop thinking" — an unusual but real axis of agent quality. Recommend ACCEPT, with a small calibration fix to `solve.sh` (write `1.13e-07` instead of `1.03e-07`) and infrastructure fix for the broken-workspace mount.
