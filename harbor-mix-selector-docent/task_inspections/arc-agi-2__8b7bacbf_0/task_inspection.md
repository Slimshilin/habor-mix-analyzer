# Task Inspection: arc-agi-2 / 8b7bacbf_0

**Benchmark:** arc-agi-2
**Task ID:** 8b7bacbf_0
**Score:** 4/18 (22%)
**Checksum:** 48e1aa1d5bedc2725c5c2038738017311772a61e5e8f603dafb04695f7c332f7
**Gemini Auditor Decision:** accept ("high-quality ARC-AGI-2 reasoning task")
**User Pre-Note:** "the quality of arc is good, but we need to ensure there are not too many arc tasks?" — quality concern is dataset-mix, not task-level.

**Our Verdict: ACCEPT.** The task itself is correct, self-contained, and theoretically solvable from the prompt alone (proven by 4/4 successful Gemini-3.1-pro runs). All 14 failures are **agent-capability bottlenecks**, not task defects. No agent hacking observed. Some fragility around the agent-timeout for heavy reasoning models on big prompts, but this is a model-budget concern (which the auditor was already aware of), not a flaw in the puzzle, environment, or verifier.

---

## 0. Task Summary

An ARC-AGI-2 abstract-reasoning puzzle. The agent receives **4 training (input, output) grid pairs** of varying sizes (8×8, 12×20, 16×24, 18×24) and must apply the inferred transformation to a **30×30 test input**, writing the answer as a JSON 2D array to `/testbed/output.json`.

### The Rule (verified from training examples + 4 successful Gemini reasoning chains)

> Some cells are unique-colour "power source" pixels. "Wires" of one specific colour (e.g. `1`s, `3`s) connect each source to a subset of nearby enclosed rectangles (made of `2`s or `9`s). **Only the wire-reachable rectangles get filled** with the source colour; rectangles that the wire never touches — or that the wire reaches only through a *break* (a `0` cell) — stay empty.

The four training examples teach the rule incrementally:

- **Ex 0**: source `7`, wires of `1`, fills several `2`-rectangles + one `5`-rectangle with `7`. **Some `2`-rectangles are NOT filled**, demonstrating that local adjacency to the wire colour is insufficient.
- **Ex 1**: source `4`, wires of `1`, fills only the wire-reachable `2`-rectangles.
- **Ex 2**: **two** independent sources (left and right), each with its own wire colour (`1` left, `3` right) but both fill colour `4`. Establishes (a) wire colour ≠ fill colour, and (b) source-pixel uniquely determines fill.
- **Ex 3**: 8×8 sanity case — single source `4`, single `1`-wire, single `2`-rectangle filled.

### Test grid (30×30)

- Background `5`.
- **Two sources**: `6` at `(0,0)`, `8` at `(0,29)`.
- **Wire `1`** connects to source `6`; **wire `3`** connects to source `8`.
- **Seven 9-bordered enclosed rectangles**.
- **Two `0` pixels** at `(14,1)` and `(18,2)` interrupt the `3`-wire on the left side, isolating one rectangle from the `8` source.

**Expected fill (verified ground truth, see `key_files/expected_output.json`):**

| # | Rectangle (rows, cols) | Fill colour | Source | Notes |
|---|---|---|---|---|
| 1 | rows 3–4, cols 4–5 | **6** | top-left `6` via `1`-wire | |
| 2 | rows 3–4, cols 13–19 | **6** | same `6`/`1` chain | |
| 3 | rows 11–12, cols 4–10 | **— (stays 5)** | _disconnected_ | `3`-wire is broken by `0`s at `(14,1)`,`(18,2)` |
| 4 | rows 12–19, col 16 (vertical) | **8** | top-right `8` via `3`-wire | |
| 5 | rows 10–11, cols 22–23 | **8** | same `8`/`3` chain | |
| 6 | rows 22–26, cols 17–19 (staircase) | **6** | `6`/`1` family | |
| 7 | rows 23–24, cols 4–5 | **8** | reached by `3`-wire from row 21 | |

The single hardest sub-rule is rectangle 3: every wrong-attempt agent (codex × 3, terminus-2 × 3 on gpt-5.4) fills it; only Gemini correctly leaves it empty by tracing the broken `3`-wire.

### Verifier

- `/tests/test_sh.sh` checks that `/testbed/output.json` exists, then runs `python3 /tests/verify.py /testbed/output.json /tests/expected.json`.
- Verifier is a single exact match (per the auditor's note and consistent with the success cases). No hidden tests.
- Verifier timeout: 60 s. Agent timeout: **600 s**. Container: `python:3.11-slim`, 1 CPU, 1 GiB RAM.

### Files in this inspection

- `key_files/instruction.md` — the prompt the agent receives (verbatim from `metadata_json->task->>'instruction'`)
- `key_files/test_sh.sh` — the verifier script
- `key_files/solve_sh.sh` — the oracle (`cp /solution/expected.json /testbed/output.json`)
- `key_files/Dockerfile` — minimal `python:3.11-slim` + `uv` + `/logs`
- `key_files/task.toml` — `[verifier] 60s, [agent] 600s, 1 CPU, 1 GiB RAM`
- `key_files/expected_output.json` — the verified canonical answer (extracted via `cat /testbed/output.json` from the successful Gemini run `312fcc35`, which passed exact-match)

The verifier source `/tests/verify.py` itself isn't in the run metadata; from `solve_sh.sh` we know it's a direct exact-match (the oracle just copies `expected.json` → `output.json` and gets full reward). No agent ever read it (see §6).

---

## 1. Dataset Overview — All 18 Runs

Pulled directly from Docent collection `640e920a-aef3-4b7c-9487-69899ef19e9d`.

| Run ID (8-char) | Model | Agent | Reward | Role | Exception | Steps |
|---|---|---|---|---|---|---|
| 37a0bd73 | claude-opus-4-6 | claude-code | 0 | failure | AgentTimeoutError | 1 |
| 6979c32d | claude-opus-4-6 | claude-code | 0 | failure | AgentTimeoutError | 1 |
| d13a0f7e | claude-opus-4-6 | claude-code | 0 | failure | AgentTimeoutError | 1 |
| 2e629cea | claude-opus-4-6 | terminus-2 | 0 | failure | AgentTimeoutError | — |
| 7354c262 | claude-opus-4-6 | terminus-2 | 0 | failure | AgentTimeoutError | — |
| c6ccb222 | claude-opus-4-6 | terminus-2 | 0 | failure | AgentTimeoutError | — |
| **312fcc35** | **gemini-3.1-pro-preview** | **gemini-cli** | **1** | **success** | — | 4 |
| **729c61c9** | **gemini-3.1-pro-preview** | **gemini-cli** | **1** | **success** | — | 4 |
| **81d5528e** | **gemini-3.1-pro-preview** | **gemini-cli** | **1** | **success** | — | 5 |
| 82712cf7 | gemini-3.1-pro-preview | terminus-2 | 0 | failure | AgentTimeoutError | — |
| **c73aceca** | **gemini-3.1-pro-preview** | **terminus-2** | **1** | **success** | — | — |
| ebe2f1b4 | gemini-3.1-pro-preview | terminus-2 | 0 | failure | AgentTimeoutError | — |
| 18d7a862 | gpt-5.4 | codex | 0 | failure | none | 18 |
| d51a3b58 | gpt-5.4 | codex | 0 | failure | none | 14 |
| f9bf4cb0 | gpt-5.4 | codex | 0 | failure | none | 15 |
| 4de0244e | gpt-5.4 | terminus-2 | 0 | failure | none (early `mark_task_complete`) | — |
| dc93ecf7 | gpt-5.4 | terminus-2 | 0 | failure | none (early `mark_task_complete`) | — |
| faddebd8 | gpt-5.4 | terminus-2 | 0 | failure | none (early `mark_task_complete`) | — |

**Pass-rate by model × harness:**

| | claude-code | terminus-2 | gemini-cli | codex |
|---|---|---|---|---|
| claude-opus-4-6 | 0/3 | 0/3 | — | — |
| gemini-3.1-pro-preview | — | 1/3 | **3/3** | — |
| gpt-5.4 | — | 0/3 | — | 0/3 |

**Important metadata correction:** the gpt-5.4 / terminus-2 runs initially looked like timeouts (NULL steps in metadata) but the trajectory inspection showed they all **completed quickly with `mark_task_complete()` after 1–2 turns** with shallow guesses — not timeouts. This changes the interpretation in §4.

---

## 2. How Close Are Agents?

Distance is measured against the verified ground truth in `key_files/expected_output.json`. Out of 900 cells, the disagreement counts:

| Run | Model / Harness | Output? | Wrong cells | Notes |
|---|---|---|---|---|
| 312fcc35, 729c61c9, 81d5528e | gemini-3.1-pro / gemini-cli | ✅ | **0** | All three pass exact match. |
| c73aceca | gemini-3.1-pro / terminus-2 | ✅ | **0** | Pass after one false-start empty turn. |
| 18d7a862 | gpt-5.4 / codex | ✅ | ~14 | Off only by spurious 8-fill of Rectangle 3. |
| f9bf4cb0 | gpt-5.4 / codex | ✅ | ~14 | Same single error as 18d7a862. |
| d51a3b58 | gpt-5.4 / codex | ✅ | ~50+ | Same Shape-3 error + flawed hole-detector that leaks fill outside the staircase. |
| 4de0244e, dc93ecf7 | gpt-5.4 / terminus-2 | ✅ | ~80 | Single uniform fill of `8` for every enclosure (no 6/8 partition, plus Shape 3 wrongly filled). |
| faddebd8 | gpt-5.4 / terminus-2 | ✅ (wrong) | ~90+ | Hand-typed grid with a stray horizontal stripe of 8s; never ran flood-fill. |
| 2e629cea | claude-opus-4-6 / terminus-2 | ✅ (wrong) | ~70+ | Filled only 2 of 7 rectangles, with wrong colour `0`. |
| 7354c262, c6ccb222 | claude-opus-4-6 / terminus-2 | ❌ | n/a | Never wrote `output.json`; verifier fails with missing-file. |
| 6979c32d, 37a0bd73, d13a0f7e | claude-opus-4-6 / claude-code | ❌ | n/a | LLM never produced first response within 600 s. |
| 82712cf7, ebe2f1b4 | gemini-3.1-pro / terminus-2 | ❌ | n/a | Empty first turn → JSON parse error → timeout. |

**Key observations:**

- Two codex runs (18d7a862 and f9bf4cb0) are **14 cells away** from passing — closer than any failing run on any other arc-agi-2 task in this batch (cf. de809cff sister inspection, where the closest gpt-5.4 run was 6 cells off, but 14 cells out of 900 is still 98.4% accuracy).
- The exact-match verifier is unforgiving: 14 wrong cells = 0 reward. There is no partial credit, which is faithful to the ARC-AGI-2 contract but means any rule-bug (even one) is fatal.
- The Gemini sweep (4/6 successes including the timeouts) confirms the task is solvable in ≤5 turns by a model that gets the rule on first try.

---

## 3. Per-Run Trajectory Findings

### 3.1 Claude family (6 runs, 0 successes)

**`6979c32d`, `37a0bd73`, `d13a0f7e` (claude-opus-4-6 / claude-code, 1 step each):**
All three transcripts contain *only* the puzzle prompt and zero assistant turns. The LLM never produced a first response within the 600 s window. This is a **harness-format pathology**: the prompt is large (4 training grids + a 30×30 test grid serialised as Python literals + claude-code's system prompt), and claude-opus's "extended thinking" mode evidently uses the entire budget on hidden CoT before emitting anything visible. **Three identical failures across three runs is a strong signal of a deterministic interaction problem, not a randomly-flaky model.**

**`c6ccb222`, `7354c262` (claude-opus-4-6 / terminus-2):**
Both correctly identify the rule family ("source pixel → wire → enclosed rectangle filled with source colour") on the first turn, but neither ever writes `/testbed/output.json`. They burn all 18–19 turns iteratively re-analysing the *training* examples to refine the rule (chasing why one Example-0 ring is unfilled). **Classic ARC trap**: prioritising a fully verified rule over a committed best-guess.

**`2e629cea` (claude-opus-4-6 / terminus-2):**
The only Claude run that actually wrote `output.json`. Used a strict same-value-only path-BFS that fails because the test grid's "wires" pass through the borders of 9-rectangles (so a `1`-wire can become a `3`-wire across a rectangle ring). Output fills only 2 of 7 rectangles with `0` (wrong colour entirely) and leaves the rest as background. Crucially, the agent **self-diagnosed the bug at turn B5** (quote: *"…the BFS for paths is only following cells of exactly the same path type … the paths are made of alternating 1s and 3s that are not directly connected to each other … I need to rethink the approach."*) but spent the remaining 10 turns running diagnostics on training data instead of overwriting `output.json` with a corrected hypothesis. **Surface failure**: wrong-colour fills, missing rectangles. **Root cause**: no defensive "save best guess each iteration" pattern.

### 3.2 Gemini family (6 runs, 4 successes)

**Successes (`312fcc35`, `729c61c9`, `81d5528e` gemini-cli; `c73aceca` terminus-2):**
All four converge on the identical electric-circuit metaphor on the **first reasoning turn** and emit a one-shot Python script that hard-codes the 6 fill regions as `(rows, cols, val)` tuples. Representative quote (`312fcc35`):

> *"Power Sources: Single isolated pixels acting as endpoints — `6` at `(0,0)` and `8` at `(0,29)`. Wires: contiguous pixels of a specific color extending out from the power source (color `1` for the `6` source, color `3` for the `8` source). Shapes: outlined enclosures (made of 9s) that function as secondary conductors. When a shape physically touches a 'live' wire or another 'live' shape, power flows through its boundary, and its interior empty spaces are filled with the color of the active power source."*

Each of the four explicitly notes the broken-wire case (the `3`-wire interrupted by `0`s near rows 14 and 18) and correctly leaves Rectangle 3 empty. `c73aceca` (terminus-2 success) survived a false-start empty assistant turn that triggered a JSON-parse error, then committed in turn 2 to a complete Python solution.

**Failures (`82712cf7`, `ebe2f1b4` terminus-2 / AgentTimeoutError):**

- `82712cf7`: empty first turn → JSON parse error → never recovered → timeout.
- `ebe2f1b4`: empty first turn, then second productive turn was an "exploratory visualisation" plan that only printed Example 0 and never wrote `/testbed/output.json` → timeout.

**Surface failure**: terminus-2's strict JSON-action protocol punishes Gemini's tendency to emit free-form prose around the JSON. **Root cause**: harness-friction × heavy-reasoning model. The 600 s budget, normally ample, is consumed by hidden thinking tokens + JSON-format retries before any Python script can run. The same model passes 3/3 on gemini-cli (which has a more permissive tool-call format).

### 3.3 GPT-5.4 family (6 runs, 0 successes)

**Codex runs (`18d7a862`, `d51a3b58`, `f9bf4cb0` — 14–18 steps, no timeout):**
All three converge on the **same wrong rule**: "a 9-ring is filled with the source colour iff its ring is *locally* adjacent to a cell of the matching wire colour." This works for 6 of 7 rings but mis-classifies Rectangle 3 (rows 11–12, cols 4–10), whose 9-ring is locally adjacent to the broken `3`-wire fragment but is **globally** disconnected from the `8` source by the `0` interrupters. Quote (`18d7a862`): *"I've narrowed the rule to 'fill enclosed holes inside outlined shapes using a marker color taken from a separate cue object.'"* — captures the right intuition (source ↔ ring) but explicitly omits the wire-conduction step.

- `18d7a862` and `f9bf4cb0` are off by exactly **14 cells** (the spurious 8-fill of Rectangle 3).
- `d51a3b58` has the same Rectangle-3 error **plus** a buggy hole-detector that leaks fill outside the bottom-right staircase (~50+ wrong cells).

**Surface failures**: spurious fill of Rectangle 3 with `8`. **Root cause**: premature commitment to a local-adjacency heuristic without testing it against training Example 0 (where a `2`-ring near rows 2–5 cols 8–11 is *not* filled — exactly the falsifying case). None of the codex runs ever asked "why isn't every ring filled in the training data?"; that question would have surfaced the wire-connectivity requirement.

**Terminus-2 runs (`4de0244e`, `dc93ecf7`, `faddebd8`):**
**Premature termination**, not timeout — all three call `mark_task_complete()` after 1–2 turns with a shallow guess. Runs 4 and 5 emit a Python flood-fill that uniformly fills every 9-bordered hole with `8` (no `1`↔`6` / `3`↔`8` partition, no wire-connectivity check). Run 6 doesn't even use Python — it hand-types a heredoc with a stray horizontal stripe of `8`s at row 14. **Surface**: missing partition + Rectangle-3 error + (Run 6) wrong outline-colour identification entirely. **Root cause**: terminus-2's "produce a batch of shell commands and `mark_task_complete()`" framing biases gpt-5.4 toward a single guess; codex's iterative `exec_command` loop encourages the longer (and qualitatively closer) answers.

---

## 4. Surface vs. Root Cause Synthesis

### Surface errors per family

| Family | Symptom |
|---|---|
| claude-opus / claude-code | LLM never produces first response (1-step transcripts) |
| claude-opus / terminus-2 | Output never written, or written once with wrong fill colour |
| gemini-3.1-pro / gemini-cli | None — passes 3/3 |
| gemini-3.1-pro / terminus-2 | Empty first turn → JSON-parse error → timeout (2/3); 1/3 success |
| gpt-5.4 / codex | Spurious 8-fill of Rectangle 3 (14 cells off) |
| gpt-5.4 / terminus-2 | Single uniform fill colour for all rectangles, premature `mark_task_complete()` |

### Root causes (deeper)

1. **Reasoning depth + premature commitment (gpt-5.4 codex).** The agents detect the right *abstractions* (sources, wires, rings) but commit to "ring locally touches wire" before testing the heuristic against Example 0's unfilled rectangles. Asking "where does my rule fail in the training data?" once would have caught the wire-connectivity requirement. This is a generic reasoning skill, not a task-induced trap.
2. **Harness friction with thinking models (gemini-3.1-pro on terminus-2).** Heavy CoT + strict-JSON output protocol = empty first turns, parse errors, lost turns. Same model on gemini-cli is 3/3 — proof that the failure is harness-induced, not capability-induced.
3. **Output-budget / first-token latency (claude-opus on claude-code).** Three runs all end with zero assistant tokens after 600 s. The prompt is large but not pathological for opus; the issue is that opus's extended-thinking mode + the claude-code single-shot format means the *first* response can take longer than the agent budget. This is a configuration mismatch, not a task defect — but it is a real concern because 3/3 runs are deterministically lost.
4. **No defensive "save best guess" pattern (claude-opus on terminus-2).** Two of three terminus-2 runs never wrote `output.json` despite identifying the rule. A simple "after each hypothesis revision, re-write `/testbed/output.json` with current best" loop would have produced a non-trivial answer in every run.
5. **One-shot bias (gpt-5.4 on terminus-2).** The harness's "emit shell-command batch + `mark_task_complete()`" template collapses the iteration budget. The model has the capability to do better but never spends the turns.

### Surface vs. root mapping

| Surface | Root |
|---|---|
| Wrong fill of Rectangle 3 (14 cells) | No wire-connectivity check; agent never falsified its local-adjacency heuristic on training data |
| Empty first turn / JSON parse error | Strict-JSON harness × thinking-model incompatibility |
| 1-step transcript / no assistant output | Agent timeout < first-token latency on heavy prompts in claude-code |
| Output never written | No defensive partial-commit pattern; agent prioritises rule-derivation over guessing |
| Single uniform fill colour | One-shot harness bias; no iteration |

**None of the root causes is a task defect.** All trace back to model capability or harness configuration.

---

## 5. Theoretical solvability and self-containedness

- **Is the answer inferable from the prompt?** Yes. 4/4 successful Gemini runs converged on the same correct grid using only the prompt — no extra information needed.
- **Hidden tests?** No. The verifier is one exact match against `/tests/expected.json`. There are no adversarial cases beyond "produce this 30×30 grid". This is faithful to the ARC-AGI-2 contract.
- **Can a super-capable being solve this?** Yes. The prompt is the canonical ARC-AGI-2 prompt with no clerical traps. Identifying the electric-circuit metaphor, partitioning sources/wires, simulating conduction, and rendering 7 rectangle fills on a 30×30 grid are well-specified and tractable.
- **What "sufficient capability" means here:** (a) inferring an unusual abstraction from few-shot examples, (b) testing the inferred rule against ALL training examples (especially the negative cases — unfilled rectangles), (c) executing pixel-perfect rendering, all (d) within ~600 s on a 1-CPU container.

---

## 6. Verdict & proposed fixes

### Verdict

**ACCEPT** — agreeing with Gemini auditor. The task is well-formed, the verifier is correct, and 4 independent successes confirm both. The 14 failures break down as:

| Failure type | Count | Attribution |
|---|---|---|
| Agent reasoning bug (didn't falsify heuristic) | 5 (all gpt-5.4) | **Capability** |
| Premature task termination (mark_task_complete too soon) | 3 (gpt-5.4 / terminus-2) | **Harness × capability** |
| Heavy-CoT timeout (claude-code 1-step, gemini-3.1 terminus-2) | 5 (3 claude-code + 2 gemini terminus-2) | **Harness × capability** |
| No defensive output write | 1 (claude-opus terminus-2 c6ccb222 + 7354c262) — partial overlap | **Capability** |

All failures are explainable by agent or harness limits; none implicate the task's instruction, environment, or tests.

### Proposed fixes — only relevant if we want to reduce harness-induced false negatives

These are **not necessary** to make the task valid (it already is), but would tighten the signal it produces:

| Fix | What it addresses | Critique |
|---|---|---|
| **A. Raise agent timeout from 600 s to e.g. 900 s for ARC-AGI-2** | Claude-code 1-step and gemini-3.1 terminus-2 runs that hit timeout while still thinking. | Mild: would convert some timeout failures into substantive trajectories, but also masks "the agent is too slow" as a real signal. Recommend **no change** — the auditor's note acknowledges 600 s is fair; the data should be allowed to reflect first-token latency limits. |
| **B. Reduce prompt size by truncating training-grid JSON to one line per row** | Same first-token issue on claude-code. | Trivial improvement, but the prompt is already verbatim ARC-AGI-2 standard. Don't deviate from upstream format; the issue is on the model side. |
| **C. Add a partial-credit verifier (e.g. cell-accuracy > 99%)** | Would let the close-to-correct codex runs score. | **Reject.** ARC-AGI-2 is defined as exact-match. Partial credit would change benchmark semantics and reward "close" reasoning that misses the actual abstraction. The codex 14-cell error is the precise signal that the agent missed the wire-connectivity rule — exactly what we want to measure. |
| **D. Add a hint in the instruction about wire-connectivity** | Would unlock gpt-5.4 codex. | **Reject.** This is the puzzle. Removing it removes the test. |
| **E. Add a verifier preflight that warns if `/testbed/output.json` is wrong-shape** | Would help terminus-2 agents that produce malformed output. | **Reject.** Verifier should remain stateless and exact-match. Agents have a shell and can self-check. |

**Conclusion: the task does not need a fix.** The right answer for the harbor-mix selection is to accept it as-is and let the failures stand as honest signals of model + harness capability.

### Optional polish (low priority)

- Could add a one-line CANARY note to the instruction (a "do not memorise this puzzle" disclaimer like the test_sh canary GUID) to harden against pretraining contamination — but that is an ARC-AGI-2-level concern, not specific to this task.

---

## 7. Hacking analysis

**No hacking signals across all 18 runs.** Every trajectory was inspected in §3 specifically for attempts to read the verifier or expected outputs. Findings:

- **Zero reads** of `/tests/expected.json`, `/solution/expected.json`, `/tests/verify.py`, `/tests/`, `/solution/`, or any path outside `/testbed/`.
- **Zero `cat`, `cp`, `find`, `grep`, or `ls`** against verifier-related paths.
- **All shell calls** in successful runs are: write `solution.py` (heredoc), `python3 solution.py`, and (optionally) `cat /testbed/output.json` or `wc -c`. Failed runs do less, not more.
- **Hacking surface:** the agent has unrestricted shell as `/testbed`'s owner, and `/tests/` and `/solution/` are mounted readable in the container (since the verifier runs `python3 /tests/verify.py`). So hacking is possible — but no agent attempted it.

**The 4 Gemini successes are reasoning successes, not exfiltration successes.** The 14 failures are reasoning/harness failures, not detected hacking attempts. No agent showed any awareness that the answer is on disk somewhere accessible.

This is consistent with the auditor's "high-quality" rating: the task rewards the underlying logical solution, and the agents that succeed do so by deriving it.

---

## 8. Final answer to the original question

> **"Is the agent failure because of the task itself or the agent capability bottleneck?"**

**Capability bottleneck, every time.** Specifically:

- **4/14 failures** = agent reasoning gap (gpt-5.4 codex × 3, gpt-5.4 terminus-2 × 1 with at least *some* programmatic effort): the agent gets within 14 cells but never asks "where does my heuristic fail in the training examples?" — a task-independent meta-reasoning skill.
- **5/14 failures** = harness × thinking-model interaction (claude-code 3 + gemini-3.1 terminus-2 × 2): the agent never gets a chance to write its first answer, because hidden CoT eats the wall budget. Fixable with a different harness or longer timeout, but neither is a task defect.
- **3/14 failures** = premature task termination (gpt-5.4 terminus-2): harness's `mark_task_complete()` bias prevents iteration. Fixable with a stricter "don't complete until you've verified against training" wrapper, but again — task-side fix unnecessary.
- **2/14 failures** = no defensive output-write pattern (claude-opus terminus-2 c6ccb222 + 7354c262): pure agent-side discipline issue.

**The auditor's accept decision is correct.** The "unsure" annotation (about ARC-task density in the mix) is unrelated to this task's individual quality. We recommend keeping this task in the harbor mix.
