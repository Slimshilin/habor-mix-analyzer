# omnimath_20 — Task Inspection

> **Verdict: ACCEPT** with two harness flags. The task is well-specified, has a unique correct integer answer (115440), and is theoretically solvable from the prompt alone — six independent runs reach 115440 internally and four commit it to disk. **None of the 14 failures are caused by the task itself.** Failures decompose into (1) genuine math gaps, (2) harness-format mismatches that block file writes, (3) bare-API/empty-trajectory infrastructure timeouts. The task discriminates well.

---

## 1. Task identity

- **Task ID**: `omnimath_20` (from `harbor-datasets/datasets/omnimath/omnimath_20`).
- **Source dataset**: HuggingFace `KbsdJames/Omni-MATH`, split `test`, index 20.
- **Origin problem**: HMMT February 2024 Team Round Problem #10 (Sean Li).
- **Difficulty tag**: `hard`. **Agent timeout**: 600 s. **Verifier timeout**: 60 s.
- **Verifier**: LLM-as-judge — `gpt-5-mini-2025-08-07`, structured `{binary_score: bool}`.
- **Ground-truth answer**: `115440` (single integer string).
- See `key_files.md` for the materialized adapter outputs (instruction.md, llm_judge.py, ground_truths.json, solve.sh, etc.).

## 2. Problem statement (verbatim, as the agent sees it)

> Consider pairs `(f, g)` of functions from the set of nonnegative integers to itself such that
> - `f(0) ≥ f(1) ≥ f(2) ≥ … ≥ f(300) ≥ 0`
> - `f(0) + f(1) + … + f(300) ≤ 300`
> - for any 20 nonnegative integers `n_1, n_2, …, n_20` (not necessarily distinct), `g(n_1 + … + n_20) ≤ f(n_1) + … + f(n_20)`
>
> Determine the maximum possible value of `g(0) + g(1) + … + g(6000)`.  *[Sean Li]*

The instruction body further says: solve the problem, write the **final answer only** to `/workspace/answer.txt` as plain text. The illustrative example given is `"What is 2+2?"` → `"4"`. So a plain integer is the expected deliverable.

## 3. Ground truth

- **Numerical answer**: `115440`.
- **Optimal construction**: `f(x) = max(0, 24-x)` (sum `f` is `24·25/2 = 300`, exactly the budget). The 20-fold infimal convolution gives `g(k) = max(0, 480-k)`, summing to `480·481/2 = 115440`.
- **Why this is the optimum**: with `f` extended to `+∞` outside `[0,300]`, `h := f^{(*20)}` is the maximal feasible `g`. Decompose `f` as `Σ c_j · B_j` where `B_j(x) = max(0, j-x)`; this yields an unbounded-knapsack with weight `j(j+1)/2` and value `400·j(j+1)/2 - 190·j` per item. Value-to-weight ratio is strictly increasing, so the unique optimum picks the largest item that fits the budget — which is exactly `j = 24`.

## 4. Run inventory (18 runs)

| run_id (short) | agent | model | reward | exception | steps | verdict |
|---|---|---|---|---|---|---|
| baca1436 | claude-code | claude-opus-4-6 | 0.0 | AgentTimeoutError | 1 | empty trajectory |
| 00c2f940 | claude-code | claude-opus-4-6 | 0.0 | AgentTimeoutError | 1 | empty trajectory |
| c9227520 | claude-code | claude-opus-4-6 | 0.0 | AgentTimeoutError | 1 | empty trajectory |
| 5dc06bee | codex | gpt-5.4 | 0.0 | — | 7 | wrote `63000` (unsupported guess) |
| 10bb6013 | codex | gpt-5.4 | 0.0 | — | 9 | wrote `63000` (only tested step f's) |
| 159d0e0a | codex | gpt-5.4 | 0.0 | AgentTimeoutError | 10 | **computed 115440 but never wrote** |
| dc1d3f49 | gemini-cli | gemini-3.1-pro | **1.0** | — | 18 | ✅ `115440` |
| 05252440 | gemini-cli | gemini-3.1-pro | **1.0** | — | 5 | ✅ `115440` (in-context derivation) |
| 7aa765fc | gemini-cli | gemini-3.1-pro | **1.0** | — | 9 | ✅ `115440` |
| bfbebe46 | terminus-2 | claude-opus-4-6 | 0.0 | AgentTimeoutError | — | best=66990, never reached triangular f |
| 022cc070 | terminus-2 | claude-opus-4-6 | 0.0 | AgentTimeoutError | — | **found 115440, doubted, pivoted, never wrote** |
| 3b036f1c | terminus-2 | claude-opus-4-6 | 0.0 | AgentTimeoutError | — | empty trajectory |
| 7f4046d3 | terminus-2 | gemini-3.1-pro | 0.0 | AgentTimeoutError | — | JSON-format mismatch, never wrote |
| a43939a1 | terminus-2 | gemini-3.1-pro | 0.0 | AgentTimeoutError | — | **computed 115440, JSON failures, never wrote** |
| cd628d78 | terminus-2 | gemini-3.1-pro | **1.0** | AgentTimeoutError | — | ✅ `115440` (written before timeout) |
| 1f922598 | terminus-2 | gpt-5.4 | 0.0 | — | — | wrote `6000` (wrong layer-cake bound) |
| d769ece5 | terminus-2 | gpt-5.4 | 0.0 | — | — | wrote `63000` (coincidence-of-3 fallacy) |
| c7dfa417 | terminus-2 | gpt-5.4 | 0.0 | — | — | wrote `63000` (same flat-step fallacy) |

**Pass rate: 4 / 18 = 22%.**

| agent × model | pass rate |
|---|---|
| **gemini-cli / gemini-3.1-pro** | **3/3 (100%)** |
| terminus-2 / gemini-3.1-pro | 1/3 (33%) |
| codex / gpt-5.4 | 0/3 |
| terminus-2 / gpt-5.4 | 0/3 |
| claude-code / claude-opus-4-6 | 0/3 |
| terminus-2 / claude-opus-4-6 | 0/3 |

The single most striking pattern: **gemini-3.1-pro is the only model that solves this problem in any harness**, and **claude-opus-4-6 produces three completely empty transcripts** (the `claude-code` rows below).

## 5. Per-trajectory observations

### 5.1 gemini-cli / gemini-3.1-pro — 3/3 ✅

All three reach the answer `115440`, with two distinct strategies appearing across the runs:

- **`dc1d3f49` (18 steps, code-heavy)** — wrote 13 successive Python scripts (`max_g.py` → `max_g13.py`) doing brute-force partition + min-convolution DP for tiny `(N, K)`. Quickly tried rectangular `f` shapes (all gave 63000), then tested triangular `f(i) = max(0, k-i)` — the very first triangular guess at `k=24` returned **115440**. Proved tightness via differences-of-`g`-equal-differences-of-`f` argument (formula `Σ g = K²·S - K(K-1)/2·f(0)`, minimized by `f(0)=k` with all unit drops). Echoed `115440 > /workspace/answer.txt`. Telling quote: *"Triangular f: [24, 23, …, 1, 0, …]  Sum: 300, Eval: 115440"*.
- **`05252440` (5 steps, pure-symbolic)** — single dense assistant turn does the entire derivation: extends `f(x>300) = ∞`, sets up `h = f^{(*20)}`, decomposes `f = Σ c_j · B_j`, computes `V_j = 400·S_j − 190·j` and `S_j = j(j+1)/2`, casts as knapsack with capacity 300, finds `V_j/S_j` strictly increasing up to `j=24`. Telling quote: *"the optimal solution is achieved by a single basis function with j=24. I am now certain the maximal h-sum is 115,440"*. No competition is cited; this looks like derivation, not retrieval (extensive false starts, self-corrections about convex minorant).
- **`7aa765fc` (9 steps, mixed)** — brute-forces `M ≤ 14, N = 20` to observe optimal `f` is always convex; reformulates as knapsack with `d_k = f(k-1) - f(k)` and second differences `e_j`, maximize `Σ (200j² + 10j) e_j` s.t. `Σ j(j+1)/2 · e_j ≤ 300`; DP gives 115440. Verifies via direct convolution simulation. Identifies `f(x) = max(0, 24-x)` and `g(k) = max(0, 480-k)`.

**Two distinct correct routes** (numerical-then-pattern in `dc1d3f49`/`7aa765fc`; pure-symbolic-knapsack in `05252440`) plus **one out-of-distribution success in terminus-2** (`cd628d78`, see §5.6) — this is sufficient evidence that the task is genuinely solvable from the prompt alone.

### 5.2 codex / gpt-5.4 — 0/3 ❌

- **`159d0e0a` (10 steps, AgentTimeoutError) — the most informative failure.** The agent ran a min-cost DP for the inf-convolution and tested four candidate `f` shapes. The last one was `f = list(range(24, 0, -1)) + [0]*277` — i.e. exactly `f(x) = max(0, 24-x)`, motivated by `24·25/2 = 300` matching the budget. The DP returned **115440**, beating the other three (which gave 63000). The transcript ends *literally on this output*: `24..1 115440`. **No subsequent assistant turn occurred**; `AgentTimeoutError` fired before `echo 115440 > /workspace/answer.txt` was sent. Reward 0.0 because the file was never created. *"I'll verify the candidate maximum computationally before writing the final value to answer.txt"* — the agent solved the problem and lost on time-management, not math.
- **`5dc06bee` (7 steps)** — wrote `63000` with **zero derivation shown**. Single load-bearing claim: *"I have the extremal value. I'm writing the final numeric answer to /workspace/answer.txt now."* No code, no symbolic algebra. Pure unsupported guess.
- **`10bb6013` (9 steps)** — explored only constant-step `f`'s (parameter `m`, width 21), saw `Σ T = 210·m` for every `m`, inferred a "ratio of 210" was universal, and concluded the optimum is `300 · 210 = 63000` with `m = 300, width = 1`. Asserted: *"I've pinned down a clean upper bound of 63000 and found a matching construction, so the optimum is exact."* Neither claim is true — the upper bound was never proved, and triangular `f` shapes (which gave 115440 in `159d0e0a`) were never tested. The failure is **insufficient candidate exploration plus premature confidence**.

### 5.3 claude-code / claude-opus-4-6 — 0/3 ❌

All three runs are **completely empty trajectories**: 1 step, 0 prompt tokens consumed, 0 completion tokens, no assistant turn, no `/workspace/answer.txt` write, just the user prompt sitting unanswered, then `AgentTimeoutError`. Identical pattern across `baca1436`, `00c2f940`, `c9227520`. This is **not a math-reasoning failure** — it is an infrastructure-level timeout in which the model never produced a single token before the wall clock hit 600 s. Most plausibly an Anthropic API hang or pre-stream abort in the recording window; possibly a harness regression specific to this combination.

### 5.4 terminus-2 / claude-opus-4-6 — 0/3 ❌

- **`022cc070` (timed out) — the most frustrating failure.** The agent ran the inf-convolution DP, tested triangular `k=24` (sum f = 300), and saw the script print **`Σ g = 115440`** — the correct answer. It then talked itself out of it: it had earlier articulated a "concave equal-split" formula `400·S - 190·(f(0)+f(300))` and noticed the formula's directionality was inverted (equal-split is the *max*, not the min). Instead of trusting the numerical DP result, it pivoted to a long convex-non-increasing search loop, ran out of time, and never wrote anything. *"Triangular k=24: sum f = 300, sum g = 115440"* immediately followed by *"For concave f, the infimal convolution formula I used was WRONG... Let me reconsider what kind of f gives the best result."* The DP was right; the agent's analytical critique was right too (the formula was wrong); but the conclusion to abandon the answer was wrong.
- **`bfbebe46` (timed out)** — set up the right DP, but lacked numpy in the container so the inf-convolution runs were slow (size-6001 pure-Python loops). Tried multi-level step shapes climbing from 63000 → 63190 → 64140 → 66990 (best). Never reached triangular `f`. Caught at ~`a=115` in a 300-iteration sweep when the timeout hit. **Slow compute + wrong candidate family** — math-side failure compounded by missing numpy.
- **`3b036f1c` (timed out)** — empty trajectory like the claude-code group. No assistant turn, 0 tokens. Pure infra timeout.

### 5.5 terminus-2 / gpt-5.4 — 0/3 ❌

This cell is the **harness × model regression**: the same gpt-5.4 that solved 0/3 in codex (above) does *worse* in terminus-2 — instead of timing out with the right answer in hand, it confidently writes nonsense and marks the task complete.

- **`1f922598`** — wrote `6000`. "Layer-cake" upper-bound argument: decomposed `f = Σ_t 1_{n<a_t}` and argued *"each layer contributes 1 to g(k) iff k<20a_t"*, i.e. `g_layer(k) = 1_{k < 20a_t}`. Summed across layers to claim `Σ g ≤ 20·Σ a_t ≤ 20·300 = 6000`. The bound is **wrong**: g is the inf-convolution of `f`, which does NOT decompose into a per-layer sum (the constraint binds across layers jointly). The agent never sanity-checked against any small `(N, K)` instance.
- **`d769ece5`** — wrote `63000`. Tested three `f`'s: `[1]*300+[0]`, `[300]+[0]*300`, `[2]*150+[0]*151`. All three returned `Σ h = 63000` in the DP. Concluded *"Since two different extremals attain 63000, the maximum is 63000"* — coincidence-of-three-guesses-as-proof. Earlier wrote a correct partial bound `S ≤ 119620`, then *rejected it* because it conflicted with the (suboptimal) brute-force result. Never tested any non-uniform `f`.
- **`c7dfa417`** — wrote `63000`. Same structural failure as `d769ece5`: rectangular `f(i) = 1` on `[0, 299]` gave `Σ = 63000`, agent declared this optimal without exploring other shapes. Hand-waved an upper-bound argument ("level-set argument"). Notably, this run *first* wrote `6000` (arithmetic error), then a Python verification script returned 63000, and the agent overwrote — but never extended its search beyond rectangles.

All three runs are short (5–13 messages) and lock onto the rectangular `f` family, missing the triangular optimum entirely.

### 5.6 terminus-2 / gemini-3.1-pro — 1/3 (one success, two harness-blocked)

This cell is the cleanest demonstration of a **harness × model fit problem**:

- **`cd628d78` (15 steps, AgentTimeoutError, ✅ reward 1.0)** — succeeded by writing `echo "115440" > /workspace/answer.txt` at step B13, well before the timeout. The agent had emitted **3 empty assistant turns** (B1, B3, B5, parser-error: "No valid JSON found") earlier, but recovered enough to run the brute-force DP, identify the unbounded-knapsack reformulation `(W_m = m(m+1)/2, V_m = 200m² + 10m)`, and compute 115440 explicitly. Final timeout was triggered by a `task_complete` confirmation prompt the model failed to answer; the file write had already landed. **A real success, written by the agent, not pre-existing.**
- **`a43939a1`** — derived 115440 internally via the same knapsack DP (`"N=300, K=20, max_sum=115440"` printed), but the assistant produced *6 empty-content turns out of ~9*, each rejected as `"No valid JSON found in response"`. The trivial `echo 115440 > /workspace/answer.txt` was never emitted. Pure harness-format failure on a fully-solved problem.
- **`7f4046d3`** — was on track (correct knapsack reformulation: *"this reduces the problem to an unbounded knapsack problem where the j-th item has weight j(j+1)/2 and value 200j² + 10j. The knapsack capacity is 300."*), but emitted bare prose plus `<tool call>bash_command(keystrokes=...)</tool call>` pseudo-syntax instead of the JSON `{analysis, plan, commands}` envelope. Later turns degenerated into entirely empty assistant blocks. The DP script `dp.py` was written but never confirmed run. Never wrote the answer.

Same model, same task — one passes, two are blocked by the JSON-emission collision between gemini-3.1-pro's native function-call shape and terminus-2's strict JSON envelope.

## 6. Surface vs. root cause

| run | surface | root cause | category |
|---|---|---|---|
| baca1436, 00c2f940, c9227520 (claude-code/opus) | empty transcript | API-level hang or pre-stream abort; agent never produced a token | **Infrastructure** |
| 3b036f1c (terminus-2/opus) | empty transcript | same as above | **Infrastructure** |
| 159d0e0a (codex/gpt-5.4) | timeout, no answer file | computed 115440 but ran out of steps before the trivial file write | **Time/budget management** |
| 022cc070 (terminus-2/opus) | timeout, no answer file | computed 115440 but pivoted away on a flawed analytical critique | **Self-doubt / analysis-over-empirical** |
| a43939a1, 7f4046d3 (terminus-2/gemini) | empty assistant turns, no file | gemini's native `<tool call>bash_command(keystrokes=…)` clashes with terminus-2's JSON envelope; parser rejects, agent stalls | **Harness × model format mismatch** |
| 5dc06bee (codex/gpt-5.4) | wrote 63000 with no work | premature closure; declared "I have the extremal value" with zero derivation | **Reasoning hygiene gap** |
| 10bb6013 (codex/gpt-5.4) | wrote 63000 | only tested constant-step f's; declared optimum without testing other shapes | **Insufficient candidate exploration** |
| bfbebe46 (terminus-2/opus) | best 66990, no file | slow pure-Python compute + only tested multi-level steps; never reached triangular f | **Insufficient candidate exploration + slow tools** |
| 1f922598 (terminus-2/gpt-5.4) | wrote 6000 | invalid layer-cake decomposition; no verification against small cases | **Wrong proof argument, no verification** |
| d769ece5 (terminus-2/gpt-5.4) | wrote 63000 | three suboptimal guesses gave same value, declared optimal | **Coincidence-as-proof fallacy** |
| c7dfa417 (terminus-2/gpt-5.4) | wrote 63000 | rectangular f hits 63000, declared optimum without exploring | **Insufficient candidate exploration** |

**Decomposition of the 14 failures**:

| Category | # | Notes |
|---|---|---|
| Infrastructure (empty trajectory) | 4 | claude-code/opus ×3 + terminus-2/opus ×1 |
| Found 115440, harness/timing blocked write | 4 | `159d0e0a`, `022cc070`, `7f4046d3`, `a43939a1` |
| Genuine math-reasoning gap (wrong answer written) | 5 | `5dc06bee`, `10bb6013`, `1f922598`, `d769ece5`, `c7dfa417` |
| Genuine math gap + slow tools | 1 | `bfbebe46` |

**The single most discriminating root-cause pattern**: among the 6 reasoning failures (rows 7–12 of the table above), every single one **never tested a triangular `f`**. They tried rectangular / constant-step / multi-step-flat-tail shapes and locked in. The optimal `f(x) = max(0, 24-x)` was simply not in the candidate set the failing models considered. By contrast, all three gemini-cli successes — and `159d0e0a`, `022cc070`, `cd628d78` (the three runs that found the answer despite failing) — explicitly tested the triangular shape and immediately got 115440. **Triangular-f candidacy is the single hardest cognitive step in this problem.**

The 4 "found-the-answer-but-blocked" runs are **diagnostic gold**: in `159d0e0a` the agent computed 115440 in step 10 but had no opportunity to commit; in `022cc070` it computed 115440 and then *talked itself out of it*; in `7f4046d3` and `a43939a1` it computed 115440 but the harness's JSON parser stripped the writing turn to empty content. The **math is achievable**; the failure modes are around it.

## 7. Assessing the task itself

### 7.1 Is the task self-contained?
**Yes.** The instruction is the full HMMT problem. No hidden tests, no implicit conventions, no environment dependencies (numpy not being pre-installed is a minor friction, not a barrier — `pip install numpy` works). The expected deliverable format (a single integer in `/workspace/answer.txt`) is unambiguous.

### 7.2 Can a super-capable being solve this?
**Yes.** Six distinct runs computed `115440` internally (3 gemini-cli successes + 1 terminus-2/gemini success + 2 unwritten internal computations in codex/gpt-5.4 and terminus-2/opus). Two distinct solution paths are in evidence (numerical brute-force + pattern recognition; pure-symbolic knapsack reformulation). The task is theoretically achievable from the prompt and the available tools. "Sufficient capability" here means: (a) test triangular `f` shapes (or do the convexity argument symbolically), (b) actually run a small-case sanity check, (c) commit the answer to disk.

### 7.3 Does the verifier work correctly?
**Yes, with one caveat.** The four passing runs all wrote the bare integer `115440` and the LLM judge correctly accepted them. The four wrong-answer runs wrote `6000`, `63000`, `63000`, `63000` — all rejected. There is no false-positive risk in evidence here (the answer is a single numeric value, so the judge prompt is essentially a string equality check that tolerates whitespace). Caveat: the judge is `gpt-5-mini-2025-08-07`, an LLM, so behavior could drift; for an integer answer this is overkill and a `str_verifier` would be more robust. Not a defect for this trial.

### 7.4 Is the failure due to task or capability/harness?
| Failure category | # | Task-quality issue? |
|---|---|---|
| Empty-trajectory infra timeouts | 4 | **No** — bench-infrastructure issue, not specific to this task |
| Math-gap failures (wrote a wrong answer) | 6 | **No** — these are genuine model reasoning bottlenecks; the task discriminates correctly |
| Found 115440 but blocked from writing | 4 | **No** — harness × model fit issues (terminus-2 / gemini JSON, codex/gpt-5.4 step-budget, terminus-2/opus self-doubt) |

**Zero of the 14 failures are caused by the task itself.** The task is correctly specified, has a correct ground truth, has a working judge, and is theoretically and practically solvable. **Accept.**

### 7.5 Is the discrimination signal good?
**Excellent.** The task discriminates on three independent axes:
1. **Whether the agent tests non-rectangular `f` shapes** (the cognitive crux). `1f922598`, `5dc06bee`, `10bb6013`, `d769ece5`, `c7dfa417`, `bfbebe46` all locked into rectangles/steps and lost.
2. **Whether the agent verifies on small cases before declaring** (`1f922598`'s layer-cake bound and `d769ece5`'s "two extremals coincide" fallacy would both have been caught instantly by a brute-force on `(N=20, K=2)`).
3. **Whether the harness×model combination supports the deliverable cycle** (terminus-2/gemini's JSON collisions, codex/gpt-5.4's "verify before commit" step blowing the budget, terminus-2/opus self-doubt loop).

For a benchmark intended to surface model and harness bottlenecks, this is exactly the discrimination one wants.

## 8. Issues that DO sit somewhere (none on the task itself)

1. **Three empty claude-code/opus transcripts** (`baca1436`, `00c2f940`, `c9227520`) plus one terminus-2/opus (`3b036f1c`). Across all four, the agent emitted zero tokens before the 600 s wall-clock fired. This is not specific to omnimath_20 — claude-opus-4-6 routinely stalls in the recording window of this collection. **Bench-infrastructure issue**, worth retrying these runs to see if they are real reasoning failures or just API hangs.
2. **terminus-2 + gemini-3.1-pro JSON-emission incompatibility**. `a43939a1` and `7f4046d3` both have the agent solve the math internally (knapsack + 115440 visible in tool output) but the assistant turns degrade into empty content rejected by the parser as `"No valid JSON found"`. The pattern is robust enough across multiple omnimath problems (also noted in `omnimath_2659`'s inspection) that it is a **harness-side bug** and not specific to this task.
3. **No "commit a partial answer at 80% budget" rule**. `159d0e0a` (codex/gpt-5.4) computed `115440` on its last allowed step and timed out before the trivial `echo` to disk. `022cc070` did the same and then talked itself out of the right answer. A single rule — "if budget is 80% spent and no answer file exists, write the current best guess" — would convert at least 2 of the 14 failures into successes.
4. **numpy not pre-installed in the container**. `bfbebe46` was crippled by pure-Python loops on size-6001 inf-convolutions. The agent could in principle `pip install numpy`, but on a 600 s budget the round-trip cost matters. Adding `numpy` to the Dockerfile would not change the math; it would remove a tooling friction that biases against models that don't think to pre-install dependencies.

## 9. Proposed fixes (none of these change the task)

**Fix A — Retry empty-trajectory runs.** The 4 empty trajectories (3 claude-code, 1 terminus-2/opus) carry zero signal. If they are API hangs (most plausible), a retry policy converts them into real attempts. *Worth doing — costs nothing structural.*

**Fix B — Fix terminus-2 ↔ gemini JSON-emission contract.** Either (a) accept gemini's native `<tool call>bash_command(keystrokes=...)</tool call>` syntax in the parser, (b) include a few-shot JSON example in the harness's system prompt for gemini specifically, or (c) translate gemini's tool-call shape to JSON server-side. *Recoups 2 runs (`a43939a1`, `7f4046d3`) on this task and many more across the dataset.*

**Fix C — "Commit before timeout" rescue rule.** Add a harness-level rule: at 80% of the agent budget, if `/workspace/answer.txt` is empty, prompt the agent to write its current best guess. *Recoups `159d0e0a` and possibly `022cc070`.* Strictly a harness change; leaves the task untouched.

**Fix D — Add numpy to the omnimath Dockerfile.** A one-line Dockerfile change. Removes a tooling friction that disproportionately punishes models that don't think to install dependencies. *Marginal; not specific to omnimath_20.*

**Fix E (REJECTED) — Modify the task instruction.** I considered nudging the agent toward "test multiple `f` shapes including triangular ones." **This would mask the genuine reasoning signal that this task is designed to surface.** The discriminating cognitive step *is* the realisation that the optimal `f` is convex/triangular; warning agents about it eliminates the discrimination. **Do not apply.**

**Recommendation**: apply A, B, and C at the harness level. Reject E. The task itself stays as-is.

## 10. Final verdict

> **The single most valuable answer**: agent failure on `omnimath_20` is **mostly a capability/harness bottleneck**, not a task defect. Of the 14 failures:
> - **6 are genuine model reasoning gaps** — the agent locked into rectangular `f` shapes and never tested triangular ones (the cognitive crux of the problem). These would have failed in any harness.
> - **4 are harness × model fit issues** — found 115440 but blocked from committing it (terminus-2/gemini JSON parser collisions, codex/gpt-5.4 step budget, terminus-2/opus self-doubt loop).
> - **4 are pure infrastructure timeouts** with empty transcripts (3 claude-code/opus + 1 terminus-2/opus).
>
> **Zero** of the 14 failures are caused by the task itself. The task is correctly specified, has a correct ground truth (`115440`), has a working LLM judge, and is theoretically + practically solvable — six runs computed the answer internally and four committed it to disk. The task discriminates well: the hardest cognitive step (testing triangular `f` shapes / discovering convexity is optimal) cleanly separates models that explore the candidate space from models that lock onto the obvious rectangle. **Accept.** Apply harness fixes A/B/C; do not weaken the instruction.
>
> **Caveat for the dataset author**: the genuinely interesting capability signal here is *"models can compute the inf-convolution numerically but don't think to test non-rectangular `f`."* The instructive failure mode is **insufficient candidate exploration plus weak verification habits** — the same surface signal across `1f922598`, `5dc06bee`, `10bb6013`, `d769ece5`, `c7dfa417`. This is a real and useful signal that this task surfaces well. The four "found-but-blocked" runs are also valuable as diagnostic markers of harness × model fit.
