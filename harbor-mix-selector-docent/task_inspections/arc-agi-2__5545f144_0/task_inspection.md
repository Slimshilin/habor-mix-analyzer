# Task Inspection: arc-agi-2 / 5545f144_0

**Benchmark:** arc-agi-2
**Task ID:** 5545f144_0
**Score:** 6/18 (33% pass rate)
**Checksum:** c8e15700585f0ad5fc5178e6a7b22a1287bb3f17d7b9c6e5373514e498ba22c8
**Gemini Audit Decision:** accept (with note about benchmark-saturation)
**Our Verdict:** **ACCEPT** — well-specified high-tier ARC task; failures are agent capability bottlenecks, not task defects.

---

## 0. Task Summary

A standard ARC-AGI-2 abstract-reasoning puzzle delivered through the standard Terminal-Bench/ARC harness:

> "You are participating in a puzzle solving competition. Below is a list of input and output pairs with a pattern. Identify the pattern in the training examples that maps the input to the output, then apply that pattern to the test input. Write your answer as a JSON 2D array to `/testbed/output.json`."

Three training examples + one test input.

- **Training Example 0:** input 10×26 (separator color = `3` at cols 8 and 17 → three 8-wide panels), output 10×8.
- **Training Example 1:** input 8×27 (separator color = `2` at cols 6, 13, 20 → four 6-wide panels), output 8×6.
- **Training Example 2:** input 12×25 (separator color = `4` at col 12 → two 12-wide panels), output 12×12.
- **Test input:** 15×15, no separators, background = 6, foreground = 8, 18 cells of value 8.

**The rule (per the 6 successful Gemini runs, all of which agreed exactly):**

The grid contains a small multi-cell "spaceship/arrow" shape (the connected component of 6 cells in the test) plus a set of scattered single-cell "dots." Each panel of a training input is a *time snapshot* of the spaceship moving along orthogonal lines, eating dots as it goes; the panel's shape is rotated to face the direction of its last move. The output is the *final* state — only the spaceship at its terminal position, rotated to face the final heading; all dots are gone.

For the test input (single panel = single snapshot = initial state), the agent must:
1. Identify the initial spaceship: an UP-pointing V/T arrow at cells `(5,7), (6,6), (6,7), (6,8), (7,6), (7,8)` (anchor = `(6,7)`).
2. Identify the 12 remaining 8-cells as "dots" to be visited.
3. Trace the orthogonal path (the unique path that visits every dot, turning 90° each time the line of dots ends): `UP→(1,7) → RIGHT→(1,12) → DOWN→(3,12) → LEFT→(3,9)→(3,3) → DOWN→(8,3) → LEFT→(8,1) → DOWN→(13,1) → RIGHT→(13,6)→(13,10) → UP→(6,10) → LEFT→(6,4)`.
4. Rotate the UP arrow 90° CCW to a LEFT arrow and anchor it at `(6,4)`.

**The expected output** (verified by reward=1.0 on six independent runs):

```json
[[6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,8,8,6,6,6,6,6,6,6,6],
 [6,6,6,6,8,8,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,8,8,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6],
 [6,6,6,6,6,6,6,6,6,6,6,6,6,6,6]]
```

Six 8s arranged as a left-pointing V (tip at col 4) anchored at `(6,4)`. The verifier (`/tests/verify.py`) does an exact JSON 2D-array match against `expected.json`.

---

## 1. Run Roster — All 18 Trials

| Agent-Run ID | Model | Agent | Reward | Exception | Outcome |
|---|---|---|---|---|---|
| 230b1e14 | claude-opus-4-6 | claude-code | 0.0 | AgentTimeoutError | First-token timeout (no msg) |
| 3c07c17e | claude-opus-4-6 | claude-code | 0.0 | AgentTimeoutError | First-token timeout (no msg) |
| b7d73761 | claude-opus-4-6 | claude-code | 0.0 | AgentTimeoutError | First-token timeout (no msg) |
| 22df4db5 | claude-opus-4-6 | terminus-2 | 0.0 | AgentTimeoutError | 10 turns; fallback heuristic written |
| 56f033eb | claude-opus-4-6 | terminus-2 | 0.0 | AgentTimeoutError | 12 turns; never wrote output |
| b50a2e85 | claude-opus-4-6 | terminus-2 | 0.0 | AgentTimeoutError | 11 turns; never wrote output |
| 01e2535c | gemini-3.1-pro-preview | gemini-cli | **1.0** | none | ✅ correct on first attempt |
| a914144e | gemini-3.1-pro-preview | gemini-cli | **1.0** | none | ✅ correct on first attempt |
| eb288e60 | gemini-3.1-pro-preview | gemini-cli | **1.0** | none | ✅ correct on first attempt |
| 05069b44 | gemini-3.1-pro-preview | terminus-2 | **1.0** | none | ✅ correct on first attempt |
| 057beffc | gemini-3.1-pro-preview | terminus-2 | **1.0** | none | ✅ wrong rotation, self-corrected |
| 86927234 | gemini-3.1-pro-preview | terminus-2 | **1.0** | AgentTimeoutError | ✅ correct on B1, then over-explored to timeout (reward still 1.0) |
| 7304dc4e | gpt-5.4 | codex | 0.0 | none | 19 turns, 15×15 with 4 cells in wrong corner |
| b5bea8dc | gpt-5.4 | codex | 0.0 | none | 19 turns, 15×15 with 4 cells (kept only training-shape #2) |
| c7661bc0 | gpt-5.4 | codex | 0.0 | AgentTimeoutError | 13 msgs; never wrote output (still hypothesizing panels) |
| 260eaee2 | gpt-5.4 | terminus-2 | 0.0 | none | Output 15×5 (cropped middle vertical strip) |
| 4906d8b0 | gpt-5.4 | terminus-2 | 0.0 | none | Output 15×5 (identical bytes to 260eaee2) |
| 4a697fa4 | gpt-5.4 | terminus-2 | 0.0 | none | Output 5×5 (cropped middle-left tile) |

**Score breakdown:**
- 6 ✅ correct (all gemini-3.1-pro-preview, both gemini-cli and terminus-2)
- 6 ❌ substantive failures (all gpt-5.4, codex + terminus-2)
- 6 ❌ timeouts: 3 first-token (claude-code) + 3 mid-reasoning (claude/terminus-2)

---

## 2. How Close Are Agents to Solving?

### 2.1 The 6 successful runs

All six gemini runs produced **byte-identical** correct outputs. Path tracing was identical, final orientation was identical, anchor was identical. Three observations:

1. **None wrote any Python code.** All six solved the puzzle via natural-language internal reasoning ("chain-of-thought") and wrote the answer with a single shell or `write_file` call.
2. **The convergence is striking.** Independent runs of the same model (gemini-3.1-pro-preview) under two different harnesses (gemini-cli and terminus-2) all picked the same start anchor, the same sequence of 12 turns, and the same final rotation. This is a strong signal that the puzzle has a *unique* solution — the spaceship-and-dots interpretation is forced by the data.
3. **86927234 timed out but still scored 1.0.** It wrote the correct answer at message B1 (first turn), then second-guessed itself for 5 more turns, produced two empty/parse-error responses, and ran out of time. The harness scores from `/testbed/output.json` on disk, which was correct from B1.

### 2.2 The 6 substantive (gpt-5.4) failures — distance to correct

For each substantive failure, "distance to correct" measured against the 15×15 expected grid:

| Run | Output dims | # 8s in output | # 8s correctly placed | # 8s missing from correct positions | # 8s misplaced |
|---|---|---|---|---|---|
| 7304dc4e (gpt/codex) | 15×15 | 4 | 0 | 6 | 4 |
| b5bea8dc (gpt/codex) | 15×15 | 4 | 0 | 6 | 4 |
| c7661bc0 (gpt/codex) | — | — | 0 | 6 | — (timeout, no output) |
| 260eaee2 (gpt/terminus-2) | 15×5 | 9 | 0 | 6 | 9 (but cropped — see below) |
| 4906d8b0 (gpt/terminus-2) | 15×5 | 9 | 0 | 6 | 9 (identical to 260eaee2) |
| 4a697fa4 (gpt/terminus-2) | **5×5** | 4 | 0 | 6 | 4 |

**Zero of the failing runs got a single 8 in the right place.** Even when the dimensions were right (codex), the cells written had no overlap with the correct answer's 6 cells. In other words: **every failing run is far from correct**, despite some looking superficially close (right shape, right size).

### 2.3 The 6 timeout runs — closeness

Three claude-code runs produced no output at all (transcript ends with the user prompt; there is no assistant block). The first-token never fired.

Three claude/terminus-2 runs got 10–12 turns of analysis. The closest:
- **22df4db5:** Identified the spaceship as "the multi-cell cross shape" and wrote a fallback hypothesis ("test has no separators → keep the cross, drop singletons") to `/testbed/output.json`. This produced a 15×15 grid with 6 cells of 8 — but the 6 cells are the **initial** spaceship position `(5,7), (6,6), (6,7), (6,8), (7,6), (7,8)` rather than the **final** position `(5,5), (5,6), (6,4), (6,5), (7,5), (7,6)`. Distance: 6/6 cells wrong (no overlap with the correct cells), but at least the shape is the right kind of thing.

This makes 22df4db5 the closest of the failing runs in spirit, but still not close in cell-level overlap.

---

## 3. Concrete Failure Behaviors

### 3.1 What the verifier checks

```bash
# /tests/test_sh:
python3 /tests/verify.py /testbed/output.json /tests/expected.json
exit_code=$?
if [ "$exit_code" -eq 0 ]; then echo 1 > /logs/verifier/reward.txt
else echo 0 > /logs/verifier/reward.txt; fi
```

`verify.py` does an exact JSON-array comparison. Any mismatch in dimensions or cell values → reward 0. There is no partial credit.

### 3.2 Failure pattern A: gpt-5.4 / terminus-2 — hallucinated subgrid extraction

**Concrete behavior** (260eaee2 and 4906d8b0 are byte-identical):
- Verbalized rule: *"the input grids are partitioned by full separator columns of a distinct color. The output keeps only the subgrid corresponding to the single partition that contains a non-background connected pattern of the target color."*
- Recognized that the test "has no explicit separator columns" — and then immediately rationalized: *"width 15 suggests three equal 5-column panels … cols 6-10 contain a connected 8 component … So the correct output should be the middle 15×5 panel."*
- Wrote a 15×5 grid (the middle vertical strip of the test input, exactly).

For 4a697fa4: same surface rule, but assumed a **3×3 tiling of 5×5 blocks** and extracted the middle-left 5×5 tile.

**Surface reason:** Wrong dimensions (15×5 or 5×5 instead of 15×15).
**Root cause:** Pattern-matching to the *training* rule without questioning whether it applies. The absence of separator columns in the test should have been a strong negative signal — instead all three rationalized implicit separators. None used Python; none re-examined the rule when their hypothesis broke. Total turn count: 5 messages each (one shot, no exploration).

### 3.3 Failure pattern B: gpt-5.4 / codex — correct dimensions, invented wrong rule

Both 7304dc4e and b5bea8dc spent ~10 assistant turns (19 messages each) running 5–6 Python scripts. They:
- Successfully identified the panel structure of the training inputs.
- Successfully isolated the central 6-cell connected component in the test (`(5,7), (6,6), (6,7), (6,8), (7,6), (7,8)` — the initial spaceship!).
- Listed and characterized the canonical "shape pool" across training panels (V, T, diagonal-Y).
- Misinterpreted the rule:
  - 7304dc4e invented "anchor + core + orient inward" — wrote a 4-cell shape in the bottom-left corner around the farthest singleton at `(13,1)`. Final cells: `(11,1), (11,2), (12,2), (13,1)`.
  - b5bea8dc decided the rule was "extract a canonical small shape from noise" — kept only the 4 cells matching `shape2={(0,1),(1,1),(2,0),(2,2)}` (a diagonal-Y) and rendered them at the central component position. Final cells: `(5,7), (6,7), (7,6), (7,8)`. The 14 satellite 8s were treated as noise and discarded.

**Surface reason:** Wrong cells (zero overlap with correct answer).
**Root cause:** Failed to make the *temporal* leap — never hypothesized that the panels are time-snapshots of a moving object, never tried to interpret the test 8s as a path. Instead pattern-matched on static shape templates from training, which is a plausible-but-wrong abstraction.

c7661bc0 (the gpt/codex timeout) was on the same investigation path as 7304dc4e and b5bea8dc, having run 6 scripts when it ran out of time. Last activity: brute-forcing dihedral D4 transforms of canonical shapes against the test components. It would likely have produced a similarly wrong answer if given more time — same flawed abstraction.

### 3.4 Failure pattern C: claude/terminus-2 — got partway, never made the leap

22df4db5, 56f033eb, b50a2e85 all did 10–12 turns of careful component analysis:
- Detected separator columns in training. ✓
- Extracted panels and connected components per panel. ✓
- Noticed that *across panels of the same example, the single-cell singletons differ but one always coincides with the shape's anchor*. Close to a productive lead.
- Computed pairwise XOR of panels. ✓
- Never reached: "panels are time-snapshots of an object moving along the singletons-as-waypoints."

22df4db5 gave up at message ~B19 and wrote a fallback (`output = test_grid with singletons removed`). 56f033eb and b50a2e85 were still iterating on the singleton/shape relationship when the timeout fired — neither wrote output.

**Root cause:** Same as gpt/codex — failure to make the temporal/dynamic abstraction. Claude went deeper into static analysis (pairwise diffs, canonical shape pool) but didn't pivot to a motion model.

### 3.5 Failure pattern D: claude-code first-token timeouts

230b1e14, 3c07c17e, b7d73761 each have **a single message in the transcript — the user prompt**. There is no assistant block at all. The transcripts are byte-identical in structure. The agent timed out before producing a single token.

**Cause:** Harness-level. Likely the prompt is large enough (3 training examples × 10–12-row × 25–27-col grids + 15×15 test grid as JSON in the prompt) that claude-code's first-token latency exceeds the per-step or total timeout. The same model (claude-opus-4-6) under terminus-2 produces 10–12 turns of substantive work, so the model is fine — the harness is mis-configured for claude-code on prompts this large.

This is not a task defect: it's a harness/timeout mismatch that affects exactly 3/18 runs of this task and is shared across many ARC-AGI tasks (the de809cff_0 task in this folder showed the same pattern — 6/6 claude runs first-token-timed out).

---

## 4. Surface vs. Root Cause Summary

| Surface failure | Affected runs | Root cause |
|---|---|---|
| Wrong output dimensions (15×5, 5×5) | 3 (gpt/terminus-2) | Pattern-matching to training rule without questioning; absence of test separators not used as a falsifying signal. |
| Right dimensions, wrong cells | 2 (gpt/codex completed) | Failed to make temporal/motion abstraction; treated panels as static-shape pool instead of time series. |
| Right dimensions, wrong cells (initial-state stand-in) | 1 (claude/terminus-2 fallback) | Failed to make temporal abstraction; gave up and wrote a heuristic. |
| No output (mid-reasoning timeout) | 2 (claude/terminus-2) | Same temporal-abstraction failure + ran out of budget while exploring. |
| No output (first-token timeout) | 3 (claude-code) | Harness/timeout mis-configuration on large ARC prompts. |
| No output (analyzing-when-cutoff) | 1 (gpt/codex) | Started right investigation but ran out of budget. |

**The single unifying root cause for the substantive failures:** failure to make the abductive leap that *the panels show a moving object across time*. Once that leap is made, the puzzle becomes a path-tracing problem with a unique solution (which Gemini found six independent times). Before the leap, the puzzle looks like a "panel-extraction-with-noise" problem and admits multiple plausible-but-wrong rules.

This is a meaningful capability bottleneck:

- **Gpt-5.4 (codex):** Strong tool use (ran 5–6 Python scripts, characterized data thoroughly) but stopped at a static abstraction.
- **Gpt-5.4 (terminus-2):** Did not even use Python; one-shot guess with a wrong rule.
- **Claude-opus-4-6 (terminus-2):** Strongest static-analysis depth among the failures; got close to the productive lead (singletons coinciding with shape anchors) but didn't pivot to motion.
- **Gemini-3.1-pro-preview:** Made the leap purely in natural-language reasoning, on the first try, six times in a row. Never used Python.

The Gemini auditor's note that "weaker agents hallucinated subgrids" is precisely the gpt/terminus-2 failure mode (3/3 of those runs). The "frontier models like Gemini 3.1 Pro Preview successfully made the leap" claim is fully verified by the data.

---

## 5. Task Quality Evaluation

### 5.1 Is the answer inferrable from the environment?

**Yes, completely.** The expected output is logically forced by the training examples:
- Each training input has separator columns of a non-background color → output has the dimensions of one panel.
- Test input has no separator → output dimensions = test input dimensions = 15×15. (Gemini stated this explicitly in all 6 runs.)
- The 6 successful Gemini runs converged on byte-identical answers despite running independently, which would not happen if the answer were ambiguous.

### 5.2 Can a sufficiently capable agent solve this?

**Yes — and demonstrably so.** Six runs (3 gemini-cli + 3 gemini/terminus-2) solved it correctly. The task is theoretically self-contained: the rule and the answer are fully determined by the prompt content. The only required capability is multi-step abductive spatial reasoning over time-series snapshots, plus a 90° rotation operation and a path-tracing computation.

### 5.3 What would the gpt-5.4 / claude-opus-4-6 agents need?

To pass this task, those models would need to:
1. **Notice** that across panels of a single training example, the *non-singleton* shape is one connected component that *changes shape and position* between panels — not that each panel has a separate canonical shape.
2. **Hypothesize** a motion model — i.e., treat the panels as time samples and look for a consistent "what changed" rule.
3. **Trace** a unique path that visits all singletons in test input, executing right-angle turns whenever the line of dots ends.
4. **Apply** a rotation rule to the spaceship shape based on final heading.

Steps 1 and 2 are the hard parts and the differentiator. Steps 3 and 4 are mechanical once 1–2 are committed.

### 5.4 Harness contributions

Two harness-level concerns affect this task:

1. **claude-code first-token timeouts (3/18 runs).** Same as the de809cff_0 task: claude-code on large ARC prompts cannot produce a first token within the per-step timeout. This artificially inflates the failure rate by 3 runs. **Not a task defect** — it's a harness/timeout configuration. (Mitigation: claude/terminus-2 with the same model gets 10–12 turns of work, so the model itself is capable of engaging with the task, just not enough to solve it.)

2. **AgentTimeoutError can still earn reward 1.0** (run 86927234). The harness scores from `/testbed/output.json` on disk regardless of timeout — which is correct behavior. Worth noting because it implies the timeout doesn't blanket-disqualify a run.

Neither of these is a task defect. The task instruction, environment, and expected output are all correct.

---

## 6. Proposed Fixes

### 6.1 Are any fixes needed for task correctness?

**No.** The task is correct as authored. The instruction is the standard ARC prompt, the training examples are well-formed, the expected.json is verified by 6 independent successful agents, and the verifier is appropriate (exact match on a JSON 2D array).

### 6.2 Are any fixes recommended for evaluation fairness?

**Optional Fix A — claude-code timeout budget.** As with de809cff_0, the 600s timeout (or whatever per-step limit applies to claude-code) is too tight for claude on these large ARC prompts. Increasing to ~1200s would let claude-code at least attempt the task. This would not lower the bar — claude/terminus-2 already gets 10+ turns and still doesn't solve, so the capability gap would persist.

**Optional Fix B — tighten test-input framing.** The instruction provides only the puzzle and a write target; the agent must independently figure out that the absence of separators in the test means a single-panel output. Adding a sentence like "Note: the test input may or may not include the same separator structure as the training examples" would slightly reduce the abductive ambiguity. **However**, this would weaken the task's discrimination value — Gemini's leap is precisely the "absence of separators ⇒ output is full-width" inference, and removing that step would convert a hard task into a medium one. **Not recommended.**

**Optional Fix C — release a partial-credit verifier.** Currently the verifier is binary exact-match. A graded verifier (per-cell accuracy) would distinguish the 22df4db5 fallback (got the shape but at the initial position) from the 260eaee2 cropped-strip output (got the wrong dimensions). For ARC-AGI specifically, exact-match is the canonical scoring method, so this would deviate from the upstream benchmark norm. **Not recommended for ARC.**

**Net recommendation:** No fixes required. The task is high quality as-is.

### 6.3 The user's separate question — "too many ARC tasks?"

The user's audit comment was *"the quality of arc is good, but we need to ensure there are not too many arc tasks."* This is a benchmark-composition concern (i.e., is the corpus over-weighted toward ARC?) and not a per-task quality concern. This task on its own is well-constructed. The composition question should be addressed at the corpus level by counting the ARC tasks and adjusting the mix if the proportion is too high.

---

## 7. Final Verdict

**ACCEPT — Task is high-quality and well-specified; failures are an agent capability bottleneck, not a task defect.**

Concrete evidence supporting this verdict:

1. **Six independent successful runs converged on byte-identical correct outputs** (3 gemini-cli + 3 gemini/terminus-2). This is the strongest possible signal that the answer is logically forced by the prompt content.
2. **Gemini's reasoning is explicit and falsifiable**: it identified the separator structure, recognized that test has no separator, traced a unique path through 12 dots, and applied a 90° rotation. The path-trace can be independently verified to account for all 12 satellite 8-cells in the test input.
3. **All 6 substantive failures share one root cause**: failure to make the temporal abstraction (panels as time snapshots of motion). The surface symptoms differ — wrong dimensions for terminus-2, wrong cells for codex, fallback heuristic for claude/terminus-2 — but the underlying gap is the same.
4. **The task is theoretically self-contained**: a sufficiently capable reasoner can solve it from the prompt alone, as Gemini's six runs demonstrate. There are no hidden requirements, no environment quirks, and no unverifiable expected-output cells.
5. **The verifier is appropriate** for the ARC-AGI domain: exact JSON 2D-array match is the canonical scoring method for this benchmark family.

**Capability signal extracted:**

- gpt-5.4: **does not solve.** Stops at a static-shape abstraction; doesn't hypothesize motion.
- claude-opus-4-6 (terminus-2): **does not solve, but gets closer to a productive lead** (notices singleton/anchor coincidence). Doesn't make the temporal pivot.
- claude-opus-4-6 (claude-code): cannot even start (harness timeout).
- gemini-3.1-pro-preview: **solves cleanly, on first try, with no Python.**

This is a meaningful and clean capability discrimination — exactly what a hard-tier ARC-AGI-2 task should produce. Together with the de809cff_0 task (which has 0/18 pass rate), this 5545f144_0 task (6/18) provides a different signal: where 5545f144 separates Gemini-3.1 from gpt-5.4/claude-opus-4-6, de809cff_0 separates "all frontier models" from "no model" (everyone fails on de809cff_0 within ~99% cell accuracy). Both are valuable difficulty calibrators in different regions of the capability space.

**One harness-level concern worth flagging (not a rejection reason, and same as de809cff_0):** 3/18 runs are claude-code first-token timeouts. This is a recurring harness-budget issue across long ARC prompts and should be addressed at the harness level, not by changing this task.

---

## 8. Key Files

- `task_inspection.md` — this file
- Collection: `640e920a-aef3-4b7c-9487-69899ef19e9d`
- Dashboard: https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d

**Successful runs (verified expected output):**
- https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/01e2535c-3b93-431a-9efc-bf8ed60ef62e (gemini-cli)
- https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/05069b44-9bfd-4eb0-97c0-f22f1c67e573 (terminus-2)
- https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/86927234-f856-4f09-a475-de4931a54209 (terminus-2 with timeout, still scored 1.0)

**Substantive failures most worth reading:**
- https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/b5bea8dc-dabd-4d1f-a44e-d93f55578419 (gpt/codex — best instrumented "wrong-rule" attempt)
- https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/260eaee2-c16d-4cb0-a4a0-71cf8c75e93e (gpt/terminus-2 — canonical "hallucinate-subgrid-separator" failure)
- https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/22df4db5-5af6-4d83-8f30-4483be301167 (claude/terminus-2 — closest reasoning to the right answer that still failed)

**First-token timeouts (harness issue, not capability):**
- https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/230b1e14-f7cc-4803-9498-5b026cb98b57 (claude-code, no msgs)
