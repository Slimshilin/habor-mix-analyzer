# Task Inspection: `bixbench/bix-16-q3`

**Initial verdict: REJECT.** **Revised verdict (after critical re-evaluation): WEAK ACCEPT with recommended fix.** See §10 (Critical Re-evaluation) for the recalibration.

> The original analysis below stays intact for traceability. The recalibration in §10 is what governs.

---

## TL;DR

- Pass rate: **4/18 (22%)**. Uneven across model families: gemini-cli+Gemini = 3/3, terminus-2+Gemini = 1/3, all other model×harness combos = 0/3.
- Question asks: count of genes with positive Spearman corr between expression and essentiality >= 0.6. Oracle = `3`.
- Data: `CRISPRGeneEffect.csv` (DepMap product). Per DepMap convention, **more negative GeneEffect = more essential**, so essentiality ≈ `-GeneEffect`. The instruction does not state this convention. Without it, the literal calculation returns 0 — what 11 of 14 failing runs submitted.
- Second issue: even *with* the correct sign flip, answer floats between **2 and 3** depending on cell-line intersection size (1003 vs 1103 cells). `KLF5` corr is `-0.598058` (just under threshold) at 1003 vs `-0.602008` (just over) at 1103. The 2 failed terminus-2/Gemini runs submitted **2** despite correct reasoning. **8 of 18 runs use the 1003-cell intersection** — these would all fail even if they applied the convention correctly.
- The original verdict cited (A) hidden DepMap convention + (B) numerical edge-case fragility as twin disqualifiers. **§10 retracts (A) as a rejection criterion** because BixBench is explicitly a comp-bio benchmark and the convention is implied by file naming. Only (B) remains as a quality concern.

---

## 1. Task description

**Question:** *"How many genes in the provided data show strong positive Spearman correlation between expression and essentiality across cell lines, with a correlation coefficient >= 0.6?"*

**Oracle answer:** `3`

**Verifier:** LLM-judge using `gpt-4o`. The agent writes `<answer>...</answer>` to `/workspace/answer.txt`; the judge compares it to the ideal answer `"3"` and returns binary equivalence. Reward = 1 if equivalent.

**Environment:** `/workspace/` contains:
- `CRISPRGeneEffect.csv` — DepMap CRISPR knockout gene-effect scores. Shape ~`(1178, 17916)`. **Negative values indicate essential genes.**
- `OmicsExpressionProteinCodingGenesTPMLogp1BatchCorrected.csv` — log1p TPM expression. Shape `(1529, 19138)` or `(1673, 19138)` depending on container (yes, this varied between runs — see §5).
- `Model.csv` — clinical metadata. Mostly unused.
- `notebook.py` — empty starter file.

The instruction text contains no domain context whatsoever beyond what is shown in `key_files/instruction.md`. Crucially, **it does not mention DepMap**, the meaning of GeneEffect's sign, or which file represents "essentiality."

**Adapter:** `bixbench-cli` (loads from `futurehouse/BixBench` HuggingFace dataset; the instruction is filled into a generic terminal-friendly template). Difficulty in `task.toml` is `"hard"`.

---

## 2. Agent run breakdown (all 18)

| Agent | Model | Pass rate | Final answers submitted |
|---|---|---|---|
| claude-code | claude-opus-4-6 | 0/3 | `0`, `0`, `0` |
| codex | gpt-5.4 | 0/3 | `0 genes`, `0`, `0` |
| **gemini-cli** | **gemini-3.1-pro-preview** | **3/3** | **`3`, `3`, `3`** |
| terminus-2 | claude-opus-4-6 | 0/3 | `0`, `0`, `0` |
| terminus-2 | gemini-3.1-pro-preview | 1/3 | `3` (pass), `2`, `2` (fails) |
| terminus-2 | gpt-5.4 | 0/3 | `0`, `0`, `0` |

**Total: 4/18 = 22.2%.**

**The model is the dominant predictor. The harness is secondary.** Every Gemini-3.1-Pro run recognized the DepMap sign convention; no GPT-5.4 run did; no Claude-Opus-4-6 run did.

See `trajectories/01..06_*.md` for full per-trajectory analyses with intermediate numbers, code snippets, and final answer strings.

---

## 3. How close are agents to a correct solution?

**Mechanically: extremely close.** Every one of the 18 runs:
- Correctly identified the two relevant data files.
- Correctly aligned them on shared `(model, gene)` keys (cell-line index intersection + gene-column intersection).
- Correctly used `scipy.stats.spearmanr` or `pandas.DataFrame.corrwith(method='spearman')` per gene across cell lines.
- Filtered to `>= 0.6` and counted.

The pipeline is identical across all 18 runs. The arithmetic is correct in every run.

**Conceptually: blocked by a single semantic step.** The only difference between passing and failing runs is whether the agent translated "essentiality" as `-GeneEffect` (DepMap convention) or as `+GeneEffect` (literal mapping to the provided file). Without that flip, the answer is `0`; with it, the answer is `3` (or `2` depending on intersection — see §5).

---

## 4. Surface vs. root cause analysis

### Surface failure
14 of 14 failing runs computed `count(spearman(expression, GeneEffect) >= 0.6) = 0` and submitted `<answer>0</answer>` (or `<answer>2</answer>` for two terminus-2/Gemini runs that did flip the sign but had a smaller intersection).

The surface answer of `0` is **mathematically correct for the literal text of the question** as written — assuming "essentiality" is the value in the file labeled `CRISPRGeneEffect.csv`. The maximum positive Spearman across all 17,676 genes is `0.5293` (CDKN1A), which is below 0.6. Zero is the right answer to the wrong (or insufficiently specified) question.

### Root cause
The instruction asks about the correlation between *expression* and *essentiality*. The DepMap convention is that **GeneEffect != essentiality**; rather, **essentiality ≈ -GeneEffect**. This convention is:

- **Not stated in the instruction.**
- **Not derivable from the file headers** (the column is just gene names; the file is just `CRISPRGeneEffect.csv`).
- **Not derivable from `Model.csv`** (clinical metadata only).
- **Not in any README inside /workspace** (no README ships with the capsule data).

The convention is part of biological domain knowledge that DepMap users acquire externally (DepMap docs, papers, cancer-genomics training). It is essentially a closed-domain prior.

The empirical distribution of correlations does provide a hint — `min = -0.628`, `max = +0.523`. The threshold of `0.6` is suspiciously close to the negative tail edge. Gemini-3.1-Pro Run 3 surfaced this (*"the 0.6 threshold seems intentionally set to capture exactly three genes"*). Claude-Opus and GPT-5.4 runs noticed the asymmetry but did not connect it to a sign-convention question. **None of the 14 failing runs explicitly questioned whether "essentiality" might be the negative of the column they were correlating against.**

The codex/gpt-5.4 Run 1 is the most interesting failure: it computed BOTH directions side-by-side (`direct count >=0.6 = 0`, `inverted count >=0.6 = 2`) — showing partial latent suspicion that essentiality might be inverted — but still submitted `0`. So even when the alternative hypothesis was numerically present in the agent's own output, the agent did not commit to it.

---

## 5. Off-by-one fragility (Problem B — independent of Problem A)

**Even agents that correctly applied the sign flip did NOT all succeed.** The terminus-2/Gemini group is the smoking gun:

| Run | Common cells | Common genes | KLF5 corr | corr<=-0.6 count | Submitted | Reward |
|---|---|---|---|---|---|---|
| 5b868579 (PASS) | **1103** | 17676 | **-0.602008** | 3 | `3` | 1 |
| 257d0750 (FAIL) | **1003** | 17676 | **-0.598058** | 2 | `2` | 0 |
| 2a292d49 (FAIL) | **1003** | 17676 | **-0.598058** | 2 | `2` | 0 |

Same model, same harness, same instruction, same conceptual reasoning ("DepMap convention -> count `<= -0.6`"). The split is purely numeric: with the 1003-cell intersection, KLF5 falls below the `|r| = 0.6` threshold; with 1103 cells, it clears.

Looking across all 18 runs, the cell-line intersection is reported as either **1003** or **1103** depending on the run — a delta of exactly 100. This is consistent with whether the expression matrix gets read as 1529 rows or 1673 rows of cell lines (yes, even the file shape varied by container). The instruction does not specify which preprocessing is canonical, so different agents naturally reach different intersections.

This means:
- The oracle answer of `3` is only correct under **a specific data-loading convention** that pulls 1103 cell lines into the intersection.
- The same conceptual answer is `2` under the (equally defensible) 1003-cell intersection.
- The threshold of `0.6` is dangerously close to KLF5's correlation magnitude. A change of `0.004` in the computed correlation flips the answer.

---

## 6. Could a "super-capable being" solve this from instruction + environment alone?

**Question A — DepMap sign convention:** *Borderline*. A human expert in cancer genomics would recognize `CRISPRGeneEffect.csv` as a DepMap product file. The Gemini-3.1-Pro runs cite the convention by name, suggesting the model has the prior. But **a literal reading of the instruction is mathematically defensible** and produces 0, and an agent without that exact biological prior has no way to know that "essentiality" should be defined as `-GeneEffect`.

The DepMap convention is *implied by file naming for someone who already knows the domain*, but not derivable from the prompt or any in-environment artifact (the workspace contains no README, no docs, no `Model.csv` column called "essentiality"). This violates the instruction-alignment rubric (the verifier should not check things not stated or implied by the env).

**Question B — Off-by-one fragility:** *No, even a perfect agent cannot reliably hit `3`*. The answer depends on the cell-line intersection size. There is no instruction guidance that says "drop NaN rows" vs. "use all rows" vs. "use Model.csv's `OncotreeLineage` filter" or whatever choice yields exactly 1103 cells with a non-NaN KLF5 correlation of -0.602. A super-capable being would correctly compute `2` or `3` depending on its preprocessing — and there is no objective ground for preferring one over the other. The verifier accepts only `3`.

**Conclusion:** the task is *not* theoretically self-contained even for an arbitrarily capable agent. It is gated on (a) external biological convention and (b) an unstated preprocessing choice. **One agent that does the math correctly cannot infer the right answer from instruction + environment.**

---

## 7. Proposed fixes

Three fix paths, each addressing a different flaw. None is a "simplification" — they all preserve the analytical content.

### Fix 1: State the DepMap convention in the instruction
Add a single sentence:
> The file `CRISPRGeneEffect.csv` contains DepMap CRISPR gene-effect scores: more negative scores indicate that knockout of the gene reduces cell viability (i.e., the gene is more essential). Treat essentiality as the negation of these scores.

**Effect:** Removes Problem A. Predicted impact: claude-opus and gpt-5.4 agents, which are mechanically capable but lack the domain prior, would now produce the correct conceptual computation. Pass rate would jump materially (predicted 12-14/18).

**Concern:** Does not fix Problem B. Predicted residual failures: 2-4 runs of those same models, which would still hit the 1003-cell intersection and submit `2` instead of `3`.

### Fix 2: Pin the data preprocessing
Either (a) pre-process the workspace so a single canonical aligned matrix is provided (e.g., a `essentiality_expression_aligned.csv` that already has `1103 cells x 17676 genes` with the sign flipped), or (b) state the preprocessing in the instruction:
> Use the intersection of cell lines present in both files; do not drop rows; align by index; do not filter further by Model.csv.

**Effect:** Removes Problem B by removing the agent's freedom to pick a different but defensible preprocessing path. Combined with Fix 1, this should give a >85% pass rate.

**Concern:** Even with prescribed preprocessing, the answer still hinges on a single gene at the threshold edge — slight changes in the underlying data version could re-break it. Probably needs Fix 3 too.

### Fix 3: Loosen the threshold OR widen the answer band
Change the question to ask for `>= 0.55` instead of `>= 0.6` (so KLF5, FERMT2, CCND1, WWTR1, ZEB2 all clear regardless of intersection variation), OR change the verifier from "exact count == 3" to "answer is between 2 and 5 inclusive" (BixBench has a `range_verifier` mode for exactly this case — see `BixBenchRecord.eval_mode == "range_verifier"`).

**Effect:** Removes the threshold-edge fragility. Combined with Fix 1, this is the most robust path.

**Concern:** This was a `binary` (LLM-judge) eval mode, not a `range_verifier`. Switching modes requires changing the BixBench dataset entry. Less feasible without upstream coordination.

### Recommended fix path
**Fix 1 + Fix 3.** Disambiguate the convention, then either lower the threshold or widen the verifier band. Without both, the task remains either underspecified (without Fix 1) or fragile (without Fix 3). **With both, this becomes a well-defined task that meaningfully tests data-analysis skill rather than uncertain biological priors.**

---

## 8. Hacking / cheating analysis

**Is there a way to cheat?** Mostly no, but with one minor concern:

1. **The verifier is an LLM judge (gpt-4o) comparing the agent's answer string to the ideal answer `"3"`.** This is a binary equivalence judge — *very* tight. There is no obvious way to pass by submitting a long, hedged answer that includes "3" inside it (the judge would have to decide equivalence, and gpt-4o is generally strict on integer counts).
2. **No oracle leakage.** The instruction does not contain the answer; the workspace does not contain the answer; the verifier is a separate process at `/tests/llm_judge.py` that the agent does not have read access to during execution (in standard BixBench Harbor docker config). The `ground_truth.json` lives at `/tests/`, which is not mounted into agent space.
3. **Minor concern — LLM-judge soft acceptance.** Could an agent submit something like "3-5 genes (FERMT2, CCND1, KLF5)" and have the judge accept it as equivalent to `3`? The judge prompt is *"You must respond with a binary score for whether the proposed answer is equivalent to the correct answer."* gpt-4o would likely return False for a range answer, but this hasn't been stress-tested. None of the 18 agents tried this.
4. **No test-discovery path.** The agent cannot grep the workspace for the answer; the test files are outside the agent's filesystem.

**Verdict on hacking:** Not a meaningful concern for this task. The failures we observed are honest computation failures, not gamed responses.

---

## 9. (Original) Final verdict: REJECT

**Concur with Gemini's audit** — but the failure mode is more severe than just "domain knowledge trap." Two independent design issues conspire to make the task fragile:

**Problem A (instruction):** The task requires an unstated biological convention (DepMap GeneEffect sign) to map "essentiality" onto the provided data. Without it, the literal answer is `0`, which is mathematically defensible. Eleven of fourteen failing runs landed exactly there.

**Problem B (environment + verifier):** Even with the correct sign convention applied, the answer depends on the cell-line intersection size due to KLF5's correlation magnitude floating around the 0.6 threshold (`-0.598` vs `-0.602`). Two of the four "correctly reasoning" Gemini runs submitted `2` instead of `3` and were marked wrong.

**Recommended action: REJECT.** Re-author per Fix 1 + Fix 3 above before re-including in the suite.

→ **This verdict is recalibrated in §10 below.**

---

## 10. Critical re-evaluation

The original verdict above conflated two arguments of unequal strength. Restating each more carefully changes the conclusion.

### 10a. Problem A is NOT a valid rejection criterion

**The mistake in the original analysis.** I cited the instruction-alignment rubric ("verifier should not check things not stated or implied") to argue that the unstated DepMap convention disqualifies the task. This conflates "not stated" with "not implied." The convention IS implied by the environment:

- **`CRISPRGeneEffect.csv` is a DepMap product file.** Its filename uniquely identifies it as DepMap CRISPR gene-effect data. The convention "more negative = more essential" is the DepMap product's defining feature, documented in every DepMap publication and tool. A computational biologist seeing this filename knows the convention immediately.
- **BixBench is explicitly a computational biology benchmark.** The `task.toml` lists `category = "computational_biology"` and `tags = ["computational_biology", "data_analysis", "bixbench"]`. Tasks in this category SHOULD test biological domain priors. Stripping that requirement would dilute what the benchmark is built to measure.
- **Empirical validation: Gemini-3.1-Pro recovered the convention from the file name alone.** All 6 Gemini-Pro runs cite the convention by name (e.g., *"DepMap Gene Effect scores are negative for essential genes"*) before applying the sign flip. This proves the convention is recoverable without instruction text — a sufficiently capable model carries it as a training prior.
- **The fact that GPT-5.4 and Claude-Opus-4-6 lacked the prior is the discriminating signal the benchmark is designed to surface.** A pass-rate spread across model families IS the point of a domain-knowledge benchmark.

**Conclusion:** The DepMap convention is implied by file naming and is part of legitimate biological domain knowledge that BixBench is designed to test. Problem A does not constitute a task defect. **Retract this argument.**

### 10b. Problem B is real but less severe than I framed

The off-by-one fragility (KLF5 sitting at `~-0.6`, intersection-size-dependent) IS a real quality concern, but I need to re-quantify it honestly.

**The empirical split across all 18 runs:**

| Cell-line intersection | Runs | Pass-able with sign flip |
|---|---|---|
| 1103 cells (KLF5 ≈ -0.602, 3 genes pass `\|r\| >= 0.6`) | 10/18 | Yes → answer 3 |
| 1003 cells (KLF5 ≈ -0.598, 2 genes pass) | 8/18 | No → answer 2 |

**Hypothetical pass rate if Fix 1 (state convention) alone were applied:** `10/18 ≈ 56%`.

This is a defensible pass rate for a "hard"-categorized task. Many BixBench tasks pass at sub-50% rates by design. The discrimination signal would still be informative (Gemini family vs. others, plus preprocessing-care among the rest).

**But: the residual 8/18 fragility-driven failures are still concerning.** Specifically:
- Codex (gpt-5.4) Run 1 already showed it can compute the inverted direction; if it commits, it submits 2 → fail. So even fixing the domain-knowledge layer leaves codex/gpt-5.4 broken on this task.
- Two terminus-2/Gemini runs already DID apply the convention and submitted 2 → fail. They are the strongest evidence that the threshold is too tight.

**Is this fragility a TASK defect, or a fair test of analytical care?** Reasonable people can disagree:
- *Pro-task:* Real biological data has edge cases. A careful agent should notice the threshold is on the edge and either probe sensitivity or report a range. None of the failing agents did this. The fragility is a legitimate test of analytical rigor.
- *Anti-task:* The instruction gives no guidance on preprocessing. Two equally-defensible recipes (with/without dropping NaN-heavy rows) yield 1003 vs 1103 cells, and neither is "wrong." Pinning the answer to 3 imposes a hidden preprocessing choice the agent cannot infer. This is closer to the original "implicit assumption" critique — but at the preprocessing layer rather than the convention layer.

I find the *anti-task* view stronger here because the off-by-one straddles a 0.004-correlation-magnitude difference on a single gene. That's not a robust test of analytical care; that's a coin flip. But the severity is far less than I implied originally — half of agents would pass with Fix 1 alone, and a single threshold tweak (`>= 0.55` or range-verifier) would yield ~16-18/18 with Fix 1.

### 10c. Revised verdict: WEAK ACCEPT, with strongly recommended Fix 3

**Accept rationale:**
- The task tests something real and informative: biological domain knowledge (DepMap convention) plus careful data analysis. This is the central purpose of BixBench's comp-bio category.
- Pass-rate variation across model families correctly identifies the model with stronger biological priors (Gemini-3.1-Pro). That's a useful eval signal — exactly what the benchmark is built to surface.
- The 4/18 raw pass rate, while low, is the "correct" measurement for the underlying capability gap. Other models genuinely lack this prior; the benchmark should reflect that.
- Problem A is implied by environment, not absent. Rejecting on "the instruction doesn't spell out DepMap" would force us to add such hand-holding to many comp-bio tasks, defeating their purpose.

**Caveat / recommended fix (not blocking):**
- The 0.6 threshold is unfortunately placed within ~0.004 of KLF5's actual correlation magnitude. Half of correctly-reasoning agents land on `2` instead of `3` solely due to preprocessing choices the instruction doesn't pin down. This is noise in the eval signal.
- **Fix 3 (loosen threshold to `>= 0.55`, or switch to BixBench's `range_verifier` mode with a 2-3 acceptance band) would clean the signal materially without making the task easier conceptually.** The biological-prior test (Problem A) remains intact; only the numerical-edge-case noise is removed.

**Hacking concern:** Unchanged from §8. Not a meaningful issue.

**Final stance:** Accept the task in current form, but **recommend the threshold/verifier-band fix in a future revision** to remove the preprocessing-noise component of the failure signal. Do NOT add explicit DepMap-convention text to the instruction — that would strip a legitimate part of the test.

### 10d. What this re-evaluation teaches about task review

The original verdict made the right local critique (the threshold is fragile) but applied the wrong global rubric (treating "instruction doesn't say it" as automatic disqualification). Domain-knowledge benchmarks are SUPPOSED to test things not stated in the instruction — the instruction-alignment rubric needs to be read as *"verifier doesn't check things that an idealized capable agent could not in principle know from the environment + reasonable domain training."* The DepMap convention easily clears that bar. The off-by-one threshold fragility does not — but it is a quality concern, not a structural defect.
