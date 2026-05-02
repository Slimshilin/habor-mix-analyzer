# Task inspection — `aa-lcr/aa-lcr-18`

- **Task name:** `aa-lcr/aa-lcr-18`
- **Benchmark:** AA-LCR (Artificial Analysis Long-Context Reasoning)
- **Source dataset:** [`ArtificialAnalysis/AA-LCR`](https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR), question_id = 18
- **Difficulty (declared):** hard
- **Document category:** Company_Documents (3 documents, ~250 KB total)
- **Aggregate result:** 1 / 18 = 5.5 % pass rate
- **Verdict:** **Mostly an agent-capability bottleneck, with one fragility in the task that lowers ceiling slightly. KEEP, but flag.**

> Companion files in this directory:
> - `trajectories.md` — per-run inventory and outcomes
> - `failure_modes.md` — failure-mode taxonomy and source-text quotes
> - `instruction.md`, `task.toml`, `Dockerfile`, `test.sh`, `solve.sh`, `llm_judge.py`, `ground_truth.json` — reconstructed task assets

---

## 1. The task in one paragraph

The agent is dropped into `/workspace`, given three text documents in `/workspace/documents/`, and asked a multi-step retrieval-and-reasoning question. The documents are NEXTDC's 1H FY24 ASX half-year results announcement (covering CY2023 H2) and two Digital Realty quarterly supplementals (Q1-24 and Q2-24). The question requires the agent to (a) identify which cities NEXTDC "added additional built capacity" in CY2023, (b) look up Digital Realty's data-center count in each of those cities, and (c) emit them ordered ascending by NEXTDC's added MW. Expected answer: **`Melbourne - 2, Sydney - 4`**. Grading is an LLM-as-judge equality check (gpt-5-mini, reasoning effort low) against the official answer.

## 2. The crux

The NEXTDC document lists **three** Australian capacity events in CY2023:

| Site | NEXTDC verb in source | MW |
|---|---|---|
| S3 Sydney | "**added** 4 MW of built capacity" | 4 |
| M2 Melbourne | "**added** 3 MW of built capacity" | 3 |
| PH1 Port Hedland | "**opened to customers with** 0.5 MW of built capacity" | 0.5 |

Digital Realty has 4 data centers in Sydney, 2 in Melbourne, **0 in Port Hedland** (Port Hedland is not in either Digital Realty supplemental's metro table).

The official answer drops Port Hedland. The natural interpretation that justifies this: **PH1 is a brand-new site opening, not an "additional" expansion of existing built footprint** — and Digital Realty has no presence there to make a meaningful Digital-Realty-count comparison. The agents who failed all included `Port Hedland - 0` as the leading entry of a 3-row answer.

## 3. Closeness — how close are agents to passing?

Very close on retrieval. Across all 14 substantive runs the agent correctly extracted Sydney = 4 and Melbourne = 2, the exact two numbers in the gold answer. The gap is one extra row at the top.

If the judge were using strict normalized exact-match, even a 2-row "Melbourne — 2 / Sydney — 4" answer might fail (delimiter mismatch). But the judge is gpt-5-mini with a "consistent with the OFFICIAL ANSWER" rubric, which empirically tolerates `:` vs. `-`, comma vs. newline, and short prose around the numbers — what it consistently rejects is the addition of a third entry that materially changes the answer set. So the failure margin is exactly one bullet point, no more and no less.

## 4. Cross-agent comparison — surface vs. root cause

### Surface

13 runs (across 5 distinct agent × model combinations) wrote the same wrong 3-row answer including `Port Hedland — 0`. Token budgets ranged from 18 K to 643 K prompt tokens; the answer was the same at every budget level. The single success and the failures used essentially the same toolchain (`grep`/`rg`/`sed` on the small NEXTDC doc + targeted grep on the two large Digital Realty docs).

### Root cause

This is **not a retrieval failure, not a tool-use failure, and not a context-budget failure**. It is a **question-comprehension / source-comprehension failure** at the synthesis step:

1. **Question parse error.** The qualifier *"additional built capacity"* in the question is read by every losing run as "any non-zero MW added in 2023". The successful run reads it as "expansion of a pre-existing built footprint" and excludes new-site openings.
2. **Failure to attend to verb asymmetry in source.** The NEXTDC text uses *"added"* for Sydney/Melbourne and *"opened to customers with"* for Port Hedland. The losing runs treat these as paraphrases; the winning run reads them as a category distinction.
3. **Literal answer-shape bias.** The losing runs treat the question as "list all NEXTDC 2023 additions, then attach Digital Realty counts (0 if absent)". The right reading is "list cities in the intersection of NEXTDC additions and Digital-Realty presence".

The retrieval is robust; the reasoning is brittle. Several agents (notably terminus-2/opus run `8d601bd1` and gemini-cli `a1e2e52a`) **explicitly considered** excluding Port Hedland and then reversed themselves. So the model can *raise* the right hypothesis but cannot reliably *commit to it*.

### Why this is genuinely capability-related, not task-related

- The verb asymmetry ("added" vs. "opened to customers with") is **textually present** in the source documents the agents are given.
- The qualifier "additional" is **textually present** in the question.
- One agent (`bfa55548`) stitched these two cues together and produced the right answer, demonstrating that the cue chain is sufficient for an in-distribution model.
- A super-capable being given the same materials would solve this — it doesn't need any external knowledge or hidden test info.

So this satisfies the "theoretically self-contained and achievable" check.

### Per-configuration breakdown

| Configuration | Correctly excluded PH | Included PH-0 | Infra/tool fail |
|---|---|---|---|
| codex / gpt-5.4 | **1** | 2 | – |
| gemini-cli / gemini-3.1-pro-preview | – | 2 | 1 |
| terminus-2 / claude-opus-4-6 | – | 3 | – |
| terminus-2 / gemini-3.1-pro-preview | – | 3 | – |
| terminus-2 / gpt-5.4 | – | 3 | – |
| claude-code / claude-opus-4-6 | – | – | 3 (auth 401) |

Only one configuration produces any successes, and only 1 of 3 codex/gpt-5.4 attempts succeeds. The other two codex runs make the same Port Hedland mistake despite using essentially identical tooling — so the success vs. failure within the same configuration appears to be **a sampling-level reasoning lottery**, not a determined model-level capability difference.

## 5. Concrete agent behaviors that fail the test

### Expected behavior

```
$ cat /workspace/answer.txt
Melbourne - 2, Sydney - 4
```
LLM judge (gpt-5-mini): `CORRECT`.

### Typical failing behavior

```
$ cat /workspace/answer.txt
Port Hedland - 0
Melbourne - 2
Sydney - 4
```
LLM judge: `INCORRECT` because the candidate names three cities and assigns "0" to Port Hedland, while the official answer names two cities. The Sydney = 4 and Melbourne = 2 entries are factually consistent in isolation, but the inclusion of Port Hedland with an unverifiable "0" makes the candidate inconsistent with the official answer (consistency, in the judge prompt's framing, requires the answer set to match — a 3-element set against a 2-element set fails).

### Test-side code

`tests/llm_judge.py` (mirrored in this directory):

```python
JUDGE_PROMPT = """Assess whether the following CANDIDATE ANSWER is CORRECT or INCORRECT.
For the CANDIDATE ANSWER to be correct, it must be consistent with the OFFICIAL ANSWER.
…
Reply only with CORRECT or INCORRECT."""
…
response = client.responses.create(model="gpt-5-mini", input=prompt,
                                    max_output_tokens=1024,
                                    reasoning={"effort": "low"})
```

Reward = 1.0 iff the judge replies "CORRECT" (and not "INCORRECT"). Else 0.0.

## 6. Is this a problem with the task itself?

There are three potential task-side criticisms to examine:

### 6.1 Is the question ambiguous? (Borderline yes)

"Cities we can be confident NEXTDC added additional built capacity in calendar year 2023" admits two readings:

- **Strict (gold answer's reading):** *additional* means *added on top of pre-existing built capacity*. PH1 Port Hedland is a brand-new site, not "additional" capacity. Sydney and Melbourne qualify; Port Hedland does not.
- **Loose (13 agents' reading):** *additional* means *additional MW relative to before*. PH1 went from 0 MW to 0.5 MW, so 0.5 MW was added. All three cities qualify.

The strict reading is supported by the verb asymmetry in the source. But a careful reader could legitimately disagree: "0.5 MW more than was there yesterday" is also "additional" in standard English. The qualifier *"we can be confident"* hints at filtering, but doesn't unambiguously specify *what* to filter — at least 13 capable agents read it as a hedge against ambiguous numbers, not as an instruction to drop new-site openings.

**Can an agent infer the strict reading from the environment?** Yes, in principle — by attending to the "added" vs. "opened with" verb difference plus the natural reading of "additional". One agent did. But the cue is subtle and the alternate reading is plausible. A typical scoring of this question would put it in the genuinely-ambiguous-but-resolvable category.

### 6.2 Is the format strict? (Borderline no)

The expected answer is `Melbourne - 2, Sydney - 4` — a specific delimiter and city order. The judge is gpt-5-mini with low reasoning effort and a "consistent with the OFFICIAL ANSWER" rubric. Empirically (per the trajectories), it accepts colon-delimited and multi-line variants — what flips it is the answer set. So the format is *not* the bottleneck for any of these runs.

There is a residual concern: if a future agent produced `Sydney - 4, Melbourne - 2` (descending instead of ascending), the judge's behavior is uncertain. But none of the inspected runs fail in this way.

### 6.3 Is "Digital Realty has 0 in Port Hedland" knowable? (Yes — and that's the trap)

The agents conclude "Port Hedland: 0" by *absence* from Digital Realty's metro table. This is a defensible inference from the supplementals but it is also exactly the moment the agent should pause and ask "if Port Hedland is not in Digital Realty's footprint at all, am I sure I should include it in the answer?" — a question the agents either don't ask or wave away.

### 6.4 Verdict on task-side problems

The task is **not broken**, but it is **on the threshold of fairness**:

- One reading of "additional" is genuinely defensible and accepted by 13/14 reasoning attempts.
- The discriminating cue (verb asymmetry) is subtle and could be missed without prejudice.
- The 1/18 success rate is barely above lottery — even the single success may not replicate.

A stricter author would tighten the question to remove the loose-reading escape hatch. The task as written is hard, ambiguous in the way AA-LCR is intentionally hard, and not technically defective.

## 7. Proposed fixes (not simplifications)

Three options ranked by quality.

### Fix A — Tighten the question (RECOMMENDED)

Rewrite the question to remove the ambiguity that 13/14 reasoning attempts exploit:

> *For the cities where NEXTDC expanded the built capacity of a pre-existing data center in calendar year 2023 (excluding new-site openings), how many data centers does Digital Realty have in these cities? List the cities and the number of Digital Realty data centers in ascending order of the MW NEXTDC added to those existing facilities in CY2023.*

This makes "additional" mean "expansion of pre-existing" explicitly. Predicted effect: the Port-Hedland-inclusion failure mode disappears; agents that already retrieve Sydney = 4 and Melbourne = 2 correctly will pass. The 14 reasoning attempts would likely jump from 1/14 to a much higher fraction (≈8–12/14, since retrieval was correct for all 14).

This is a fix, not a simplification: the underlying long-context retrieval task (cross-referencing one NEXTDC doc with two Digital Realty supplementals, looking up city-level counts in nested tables) is unchanged. Only the linguistic ambiguity is removed.

### Fix B — Tighten the gold answer to discriminate against the trap

Keep the question, but make the gold answer explicitly exclusive:

> Official answer: `Melbourne - 2, Sydney - 4 (Port Hedland excluded as a new-site opening, not an addition)`.

Combined with a judge-prompt nudge ("the official answer is exhaustive — candidates that include additional cities are INCORRECT"), this would reliably fail the 13 wrong runs and reliably pass the 1 right one. But this is **less satisfying** than Fix A because it doesn't help the reasoning agent figure out *why* — it just enforces the strict reading at grading time. Models that have already "correctly" reasoned to the loose-reading answer would learn nothing.

### Fix C — Keep as-is and accept the low pass rate

The task is hard *because* the verb asymmetry and the qualifier "additional" create a subtle reasoning trap. Accepting 5.5 % pass rate as legitimate is consistent with AA-LCR's stated purpose (long-context reasoning at the frontier). The single success is informative — it says "this trap is in principle catchable, and at least one agent caught it". The 13 failures are informative — they say "current models default to literal/inclusive readings even when subtle textual cues warrant filtering".

Drawback: with only 1 success out of 18, the task has very low *discriminative* power. It cannot distinguish between models that almost-could and models that won't — both score 0. As a benchmark item, it's near the noise floor.

### Recommendation

**Apply Fix A** if this task is being used in a production benchmark mix where discriminative power matters. **Apply Fix C** (keep as-is) if it's a sample for studying reasoning brittleness — the convergence of 13/14 wrong reasoning attempts on the *same* error is itself a useful signal.

The task should NOT be rejected. It is well-specified, theoretically self-contained, has correct ground truth, has a clean tester, and one capable agent solved it — all checks pass. It just sits at a hard reasoning point where most current models fall on the wrong side of an interpretive line.

## 8. Final verdict

> **Is the agent failure because of the task itself or the agent capability bottleneck?**

**~85 % capability bottleneck, ~15 % task fragility.**

- 3 / 18 runs are pure infrastructure (auth) failure — **harness, not task or model**.
- 1 / 18 is a tool-use crash (parallel un-paginated reads) — **agent harness mishap**.
- 13 / 18 are the same reasoning failure across 5 different agent×model combinations — **a real, reproducible model capability gap** at the question-comprehension layer. The retrieval is correct in every case; the synthesis is wrong in the same way every time.
- 1 / 18 is a pass — demonstrating the task is solvable.
- The task itself has a **borderline-ambiguous qualifier** ("additional") that could be tightened, but the gold-answer reading is defensible from textual cues in the source. A super-capable model can solve this from the materials given; current frontier models can do so only intermittently.

**Recommendation:** Keep the task. Optionally apply Fix A (tighten the question's "additional" qualifier) if the goal is to maximize discriminative power. Either way, this task tells a clean story about where the capability ceiling is — careful question parsing combined with attention to subtle source-text cues at the synthesis step. That is precisely the bottleneck AA-LCR is designed to probe.
