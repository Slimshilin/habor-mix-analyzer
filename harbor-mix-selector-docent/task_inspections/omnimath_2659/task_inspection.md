# omnimath_2659 — Task Inspection

> Final analysis. **Verdict: borderline-accept**, with one task-quality issue to flag (sandbox isolation anomaly) and one structural issue (no partial credit) that is by-design but worth understanding.

---

## 1. Task identity

- **Task ID**: `omnimath_2659` (under `harbor/datasets/omnimath/omnimath_2659`)
- **Source dataset**: HuggingFace `KbsdJames/Omni-MATH`, test split, index 2659
- **Origin problem**: EGMO 2024 Problem 3 (functional equation)
- **Difficulty**: hard
- **Verifier**: LLM-as-judge — `gpt-5-mini-2025-08-07`
- **Agent timeout**: 600 s; verifier timeout 60 s

## 2. Problem statement

Verbatim from `instruction.md` rendered to the agent:

> Determine all functions f: ℤ → ℤ such that **f(f(a) − b) + b·f(2a)** is a perfect square for all integers a and b.

The instruction body further says:
- Solve the problem and write the final answer to `/workspace/answer.txt`
- Plain text, no special formatting
- The example given in the instruction is "If problem asks 'What is 2+2?', answer file should contain `4`"

## 3. Ground truth (oracle `solve.sh`)

Two function families:

1. **f(n) = 0 if n is even**; **f(n) = any perfect square if n is odd** (this includes `f ≡ 0` as the special case where every odd value is `0²`).
2. **f(n) = n² for every integer n**.

Mathematically these are the only solutions to EGMO 2024 P3.

## 4. Verifier

`tests/llm_judge.py` ships the predicted text in `/workspace/answer.txt` and the target string from `ground_truths.json` to the LLM judge with this prompt:

```
You are given a question, target answer and a predicted answer. Your task is to compare the
target answer with the predicted and assess if the predicted answer is correct or incorrect.
Question: {question}
Target Answer: {answer}
Predicted Answer: {output}
Respond only with valid JSON with the key binary_score
```

Judge: `gpt-5-mini-2025-08-07`, structured output `{binary_score: bool}`. **Single-shot binary verdict — no per-family partial credit.**

## 5. Run inventory (18 runs)

| run_id (short) | agent | model | reward | role | exception |
|---|---|---|---|---|---|
| 44f3076b | codex | gpt-5.4 | 1.0 | success | — |
| 460f9dab | codex | gpt-5.4 | 1.0 | success | AgentTimeoutError (answer written before) |
| 89c6ae3c | codex | gpt-5.4 | 1.0 | success | AgentTimeoutError (**answer not visible in transcript** — see §10) |
| 3e7de1d4 | gemini-cli | gemini-3.1-pro | 1.0 | success | — |
| 4d848939 | gemini-cli | gemini-3.1-pro | 1.0 | success | — |
| bfa15a13 | gemini-cli | gemini-3.1-pro | 1.0 | success | — |
| a2ba26b9 | claude-code | claude-opus-4-6 | 0.0 | failure | — |
| a01bafb3 | claude-code | claude-opus-4-6 | 0.0 | failure | — |
| 9e291d52 | claude-code | claude-opus-4-6 | 0.0 | failure | — |
| 270f49a0 | terminus-2 | claude-opus-4-6 | 0.0 | failure | — |
| 6c726546 | terminus-2 | claude-opus-4-6 | 0.0 | failure | — |
| d09a73ad | terminus-2 | claude-opus-4-6 | 0.0 | failure | — |
| 7cf66012 | terminus-2 | gpt-5.4 | 0.0 | failure | — |
| b6bc4dcd | terminus-2 | gpt-5.4 | 0.0 | failure | — |
| c124a7e9 | terminus-2 | gpt-5.4 | 0.0 | failure | — |
| 35778523 | terminus-2 | gemini-3.1-pro | 0.0 | failure | AgentTimeoutError, **no answer.txt** |
| 4527b9e6 | terminus-2 | gemini-3.1-pro | NULL | failure | AgentTimeoutError |
| c61f9db9 | terminus-2 | gemini-3.1-pro | 0.0 | failure | AgentTimeoutError, **no answer.txt** |

**Pass rate: 6 / 18 = 33%.**

| agent × model | pass rate |
|---|---|
| codex / gpt-5.4 | 3/3 (100%) |
| gemini-cli / gemini-3.1-pro | 3/3 (100%) |
| claude-code / claude-opus-4-6 | 0/3 |
| terminus-2 / claude-opus-4-6 | 0/3 |
| terminus-2 / gpt-5.4 | 0/3 |
| terminus-2 / gemini-3.1-pro | 0/3 (all timeouts) |

## 6. Per-trajectory observations

### 6.1 codex / gpt-5.4 — 3/3 success

**Approach**: brute-force Python verification. All three runs reformulated the equation around the linearity in `b` (coefficient `f(2a)`, constant `f(f(a))`), then enumerated polynomial families and small function tables to discover both solution families.
- `44f3076b` (clean): pruned `kx²` and `x²+ux+v` over a, b ∈ [-15, 15]; confirmed only `0` and `x²` survive among polynomials, identified the even-zero/odd-square family by exhaustion.
- `460f9dab` (timeout, but answer written first): cleanest derivation. Showed `f(0) ∈ {0, -1}`, brute-searched 5-point function tables, ruled out the `f(0) = -1` branch numerically, verified the alternative family.
- `89c6ae3c` (timeout, **no visible answer.txt write** — see §10).

**Verbatim winning answer (`44f3076b`)**:
```
The functions are exactly:

1. f(n) = n^2 for every integer n;
or
2. f(n) = 0 for every even integer n, while for each odd integer n,
   f(n) may be any perfect square integer (chosen arbitrarily and independently).
```

### 6.2 gemini-cli / gemini-3.1-pro — 3/3 success

**Approach**: pure symbolic reasoning, no Python. All three runs followed the same skeleton — `P(a,b)` substitutions (`b=0`, `a=0`, `b=f(a)`), eliminate `kx²` and quadratic ansätze, derive that `f(y) − f(2a)·y + C_a` is a perfect square in y for every fixed a, bifurcate on whether `f(2a) ≡ 0` (yielding the parity family) or `f(2a) ≢ 0` (forcing `f = n²`).

- One run (`3e7de1d4`) explicitly cited the problem as "EGMO 2024" mid-derivation. The other two derived the same characterisation without naming the source — though the suspiciously identical phrasing of the final answer string suggests memorised scaffolding shapes the format.
- All three hit a reproducible gemini-cli heredoc bug (`cat << 'EOF' > /workspace/answer.txt` errored out as "here-document delimited by end-of-file") and recovered with a one-line `echo`. This is a CLI quoting bug, unrelated to the math.

**Verbatim winning answer (`3e7de1d4`)**:
```
f(x) = x^2 and any function f such that f(x) = 0 for even x and f(x) is a perfect square for odd x
```

### 6.3 claude-code / claude-opus-4-6 — 0/3 failure

**Approach**: extended symbolic reasoning, found `f ≡ 0` and `f(n) = n²`, missed the broader family. All three runs converge on the **same wrong answer**:

> "f(x) = 0 for all x, or f(x) = x² for all x."

- They derive `f(0) ∈ {0, -1}`, eliminate `f(0) = -1`, then assume the answer is a polynomial because their factorisation argument forces `h(t) = αt`. This step ignores the degenerate case where `f(2a) ≡ 0` for all a — the precise loophole that admits the missing family.
- **Damning near-miss (`a01bafb3`)**: the agent literally wrote out the candidate `f(1)=4, f(3)=9, f(5)=1, f(even)=0` and remarked "this confirms the pattern works" — then dropped the thread and reverted to claiming only `0` and `x²`. The correct family is *findable* by this model under different sampling.

### 6.4 terminus-2 / claude-opus-4-6 — 0/3 failure

**Same wrong answer in all three**: "f(a) = 0 and f(a) = a²".

- Run `270f49a0` shows real symbolic work but stops at the same place claude-code stopped.
- Runs `6c726546` and `d09a73ad` are extreme short-circuits — **2 substantive turns, no derivation visible**. The agent claims in the first message "I've solved the problem analytically" with no evidence and writes the answer + marks complete. No bash brute-force search is attempted (despite the harness offering a shell).

### 6.5 terminus-2 / gpt-5.4 — 0/3 failure (most striking)

This is the most instructive cell. Same model that **succeeds 3/3 in codex** **fails 3/3 in terminus-2**. All three runs are 5 messages long with no derivation:
- `7cf66012`: writes "the only functions are f(x)=0 and the constant **f(x)=1**". `f ≡ 1` is **not even a valid solution** (`f(f(a)−b) + b·f(2a) = 1 + b`).
- `b6bc4dcd`: writes "the only function is f(n)=0". Misses `f = n²` entirely.
- `c124a7e9`: identical to b6bc4dcd verbatim.

The model's `analysis`/`plan` field literally says "I will primarily reason directly" — and then it doesn't reason. It guesses and submits.

### 6.6 terminus-2 / gemini-3.1-pro — 0/3 timeouts

The most pathological group:
- All three hit `AgentTimeoutError`.
- Two have **no `/workspace/answer.txt` at all** (verifier reports "file not found"), one has NULL test stdout.
- Long stretches of empty assistant messages that terminus-2's parser rejects as "No valid JSON found in response". When the model does produce content, it uses gemini-cli's native `<tool call> bash_command(...)` syntax — not the JSON-encoded keystroke schema terminus-2 expects.
- Pathological detail: in run `c61f9db9`, the agent verbally states "if f(x) = 0 for all even x, and f(x) = k² for odd x, then f(f(a) − b) + b·f(2a) = f(f(a) − b), which is always a perfect square. This implies there's an infinite family of solutions." — i.e. it correctly identifies the missing family — but **never serializes it to disk** before timing out. The math was solved internally; the harness adapter ate the deliverable.

## 7. Pattern synthesis: surface vs. root cause

| group | surface failure | root cause |
|---|---|---|
| claude-code / claude-opus | answers "f=0 or f=x²" | premature closing of proof: applies "factorisation linear in u forces h linear" unconditionally, ignoring the degenerate `f(2a) ≡ 0` branch. **Genuine reasoning gap** specific to this problem — model has the competence but stops too early at the textbook olympiad answer. |
| terminus-2 / claude-opus | same answer "f=0 and f=x²" | same reasoning gap as 6.3, made worse by terminus-2's `analysis/plan/commands` JSON schema, which compresses thinking into ~2 sentences. Some runs short-circuit to declaration in 2 turns, never doing bash verification. **Capability gap + harness pressure**. |
| terminus-2 / gpt-5.4 | non-solutions ("f≡1") or trivial "f≡0" | the harness frames the task as "write a file" rather than "solve a problem". The model substitutes writing the answer file *for* thinking. Same model in codex's chat-first frame solves cleanly. **Pure harness-induced regression, not capability** — gpt-5.4 *can* solve this; the terminus-2 surface prevents it. |
| terminus-2 / gemini-3.1-pro | no answer file, timeout | format mismatch: model's native tool-call shape (`<tool call> bash_command(...)`) collides with terminus-2's `{commands:[...]}` JSON-encoded keystroke schema. Repeatedly emits empty assistant messages, burning the budget. **Pure scaffolding/adapter issue** — the math was internally solved in run c61f9db9 but never written. |
| codex / gpt-5.4 | (success) | brute-force-friendly harness that lets gpt-5.4 iterate Python verifications. Found both families empirically. |
| gemini-cli / gemini-3.1-pro | (success) | gemini's native chain-of-thought has space to do the symbolic case analysis. One run literally cites EGMO 2024. |

**The discriminating factors are two-axis, not one-axis.** It is not "stronger model = pass". It is `(harness gives space to think) × (model can complete the case-analysis or has memorised EGMO 2024)`. Both must be true. claude-opus-4-6 fails in *both* its harnesses on the math itself; gpt-5.4 succeeds in codex but fails in terminus-2 due to harness; gemini-3.1-pro succeeds in gemini-cli but times out in terminus-2 due to format mismatch.

## 8. Verdict on task quality

### 8.1 Is the task self-contained?

✅ **Yes.** The instruction is the full EGMO 2024 problem statement. No hidden information, no environment dependencies, no implicit conventions. A capable solver with no external context can derive both families.

### 8.2 Can a super-capable being solve this?

✅ **Yes.** Six of eighteen runs (across two distinct harnesses and two distinct model families) produced the correct two-family answer. This is sufficient evidence that the task is achievable — and not "lottery-success" given that *every single* run in two cells succeeded.

### 8.3 Does the verifier work correctly?

⚠️ **Mostly.** I checked the LLM judge's behaviour empirically through the agent answers:
- Successful answers were phrased in plain English ("`f(x)=x²` and any f such that f is 0 on evens and an arbitrary square on odds") — judge accepted these as equivalent to the LaTeX oracle. ✅
- Partial answers ("only `f≡0` and `f=x²`") were rejected as wrong. ✅
- Outright wrong answers ("f≡1") were rejected. ✅
- The judge appears to enforce that **both** families be present and correctly characterised — no false positives on partial answers. ✅

The judge is doing what a binary judge should do. There is no per-family partial credit — that's by design.

### 8.4 Is the failure due to task or capability/harness?

The failures decompose roughly as follows (12 failing runs):

| failures | category | weight |
|---|---|---|
| 6 (claude-opus, both harnesses) | **genuine model reasoning gap** — drops the parity branch | 50% |
| 3 (terminus-2/gpt-5.4) | **harness × model interaction** — same model solves elsewhere | 25% |
| 3 (terminus-2/gemini timeouts) | **harness × model interaction** — JSON format mismatch | 25% |

So **the task is not the cause of any of the 12 failures.** The task discriminates correctly: it is hard enough that 50% of failures are genuine math gaps, and the other 50% expose harness/model fit problems that are *also* what a benchmark like this is designed to surface.

This is exactly Gemini's audit framing ("the distribution of success/failure among trials suggests the task effectively discriminates between models that can perform deep mathematical analysis…") — and on closer inspection it actually does *more* than that: it also discriminates between harnesses for the same model.

### 8.5 Issues that DO sit with the task

1. **Sandbox isolation anomaly (`89c6ae3c`)**: Inspected the full 57-message transcript of this codex/gpt-5.4 run. **There is no `cat > /workspace/answer.txt` or any other write to that file** anywhere in the trajectory. Yet the verifier reports `Reward: 1.0` — meaning the judge saw, and accepted, *some* answer. The most plausible explanation is that the per-trial sandbox container was reused between codex/gpt-5.4 trials and a previous run's `/workspace/answer.txt` was still present. This is a benchmark-infrastructure issue (not specific to this task), but it inflates this task's pass count by 1 (and possibly inflates other tasks' pass counts in the same run set). Worth flagging to the harness authors.

2. **Oracle answer string is unusual** — bracketed list `[ $$ ... $$; $$ ... $$ ]` mixed with single-backslashed LaTeX (`\text`, `\quad`). Because the judge is an LLM, this still works (it understands the math). But it's not the cleanest form, and a stricter judge (or a future migration to a string verifier) would brittle on it. This is upstream Omni-MATH formatting, not introduced by the adapter.

3. **No partial-credit signal**: half of failures are "correct on `f=n²`, missed the parity family". The single-bit reward loses that information. This is a benchmark design choice — not a defect — but for `omnimath_2659` specifically it means the dataset can't tell apart "solver knows nothing" from "solver got 50% of the answer". For a discriminator task this is fine; for diagnostic information it is information loss.

## 9. Proposed fixes (if we wanted to make the task more robust)

I propose these in increasing order of intervention:

**Fix A — Harden sandbox isolation (no task change).** Verify that codex trials launch in fresh containers per run; if reuse is happening, add a pre-run cleanup step that wipes `/workspace/answer.txt`. This addresses the §8.5(1) anomaly without touching the task. *Best fix for the only real issue.*

**Fix B — Tighten the oracle answer string (cosmetic).** Replace the bracketed `[ $$...$$ ]` form with a single-paragraph natural-English oracle that mirrors the answer style successful agents produced. This makes the task slightly less dependent on the LLM judge's tolerance and is a small upstream-fairness improvement. Risk: too much downstream effort relative to the gain — the judge already handles the current form correctly.

**Fix C — Add a "completeness" hint to the instruction (would change difficulty).** The instruction could say: "There may be more than one family of functions — find *all* of them." This nudges agents toward the parity case. **I recommend NOT applying this**: it would mask the genuine reasoning gap that makes this task discriminating. The whole point of the failure mode is that the agent stops at the textbook answer; warning them defeats the discrimination signal.

**Fix D — Add a partial-credit verifier (instrumentation only, not for grading).** Two-step judge: first ask "did the predicted answer include `f(n)=n²`?" then ask "did it include the even-zero/odd-square family?" Take the AND for the binary reward (preserving current behaviour) but log the two booleans separately. This gives diagnostic information without changing pass rates. Requires touching `tests/llm_judge.py`. Worth doing only if downstream consumers want partial-credit signal.

**Fix E — Force a "write before timeout" rescue (harness change).** For the terminus-2/gemini timeouts where the math was solved internally but never serialised: add a harness rule that at 80% of budget, the agent is prompted to commit a partial answer. This would convert several `no-file` timeouts into possible `partial-answer` runs. Strictly a harness change, not a task change.

**My recommendation**: apply **Fix A** (sandbox isolation) and **Fix D** (partial-credit instrumentation, if downstream consumers want it). Reject **Fix B** (low value), **Fix C** (would damage the discriminator signal), and **Fix E** (out of scope for this task, harness-side issue).

## 10. The two `AgentTimeoutError + reward=1.0` codex runs — re-verified

These two runs deserved a closer look because the combination is suspicious. After re-querying the metadata and re-reading the **full** transcripts, here is what each run actually does:

### `460f9dab` — *normal pattern*

- Metadata: 16 steps, AgentTimeoutError, reward=1.0.
- Transcript: 18 messages.
- At **B15–B16** (well before the timeout) the agent runs `cat > /workspace/answer.txt <<'EOF'` and writes the correct two-family answer:
  > "All such functions are exactly the following two families: 1. f(n)=0 for every even integer n, and for each odd integer n the value f(n) can be any perfect square… 2. f(n)=n^2 for every integer n."
- B17 (assistant): "Written to /workspace/answer.txt."
- The remaining steps before the timeout were the agent continuing to explore. The verifier graded the file that was already on disk.

This pattern is **completely normal**: the codex harness lets the agent keep iterating after a deliverable is committed; if the agent runs out of budget while polishing, the timeout fires, but the deliverable is still graded. So `AgentTimeoutError + reward=1.0` here is an honest pass.

### `89c6ae3c` — *the genuine anomaly*

- Metadata: 33 steps, AgentTimeoutError, reward=1.0.
- Transcript: **57 messages, fully read** (verified: querying with `start_idx=56, end_idx=300` returns only B56 and `messages 100..200 of 57`, confirming there is no further content).
- I grep-read every `exec_command(...)` and every assistant text block. **There is no `cat > /workspace/answer.txt`, no `tee`, no `apply_patch`, no `>` redirect, no `echo > answer.txt` anywhere in the transcript.** The agent spent all 33 steps running Python brute-force searches.
- The codex `test.sh` is the standard one — it just runs the LLM judge. There is no auto-population step in the task.

Yet `test_stdout` reports `Reward: 1.0`, meaning the LLM judge read *something* it considered correct. The most plausible explanation remains cross-trial sandbox contamination — a prior codex/gpt-5.4 trial in the same container or a re-used `/workspace` left a correct `answer.txt` behind.

This **is** a real benchmark-infrastructure anomaly; it is **not** a problem with the task itself. It artificially counts one passing run that should have been a no-file timeout. With this run discounted, codex/gpt-5.4 is honestly 2/3 instead of 3/3, and the overall pass rate is 5/18 instead of 6/18 — but none of the qualitative conclusions change.

> **Were full trajectories read?** Yes. I directly verified two ways: (a) querying with `end_idx` past the visible last message returned no further content; (b) the metadata `total_steps` (33 for 89c6ae3c, 16 for 460f9dab, 16 for 44f3076b) is consistent with the 57/18/14 message counts at ~1.7 messages per step. The terminus-2/gpt-5.4 runs really are 5 messages each — re-fetched 7cf66012 in full and confirmed B0–B4 is the entire transcript.

## 10b. Why does terminus-2 consistently fail (0/9 across all three models)?

terminus-2 fails for **three distinct reasons**, one per model — but they share a common root cause in the harness design.

**Common root cause** — terminus-2's harness is shaped for *sysadmin tasks*, not reasoning tasks:
- The system prompt frames the deliverable as a JSON object with `analysis` (1–2 sentences), `plan` (1–2 sentences), `commands` (an array of `keystrokes` strings), and `task_complete` boolean.
- There is no scratchpad and no explicit reasoning channel. The model is implicitly told "do work, then mark complete".
- The `commands` field is a *tmux keystroke stream* encoded as JSON — the model has to escape multi-line bash heredocs as JSON strings, which is a brittle indirection.
- `mark_task_complete()` can be called in the same turn as the file write, so there is no harness-enforced "verify before submit" pause.

For a math problem whose deliverable is a *proof*, this scaffolding actively penalises good behaviour.

**Per-model symptom on top of that root cause:**

1. **terminus-2 / claude-opus-4-6 (0/3)** — same `f=0 + f=x²` answer that claude-code/claude-opus also produces. The bottleneck is **the model's reasoning**, not the harness. Claude-opus closes the proof prematurely on this functional equation in any harness; terminus-2's tiny analysis field doesn't help, but the failure mode here is genuinely a math gap. Two of three runs short-circuit to 2 turns ("I've solved it analytically", no work shown), but even the run that does symbolic work stops at the same place claude-code stops.

2. **terminus-2 / gpt-5.4 (0/3)** — **harness-induced regression**. Same gpt-5.4 in the codex harness runs 16–33 Python verification steps and gets 3/3. In terminus-2 all three runs are 5 messages — agent writes a guess in turn 1 and marks complete. Run 7cf66012 wrote `f(x)=0 and f(x)=1` (the constant-1 function isn't even a solution). The model's `plan` literally says "I will primarily reason directly" and then produces no reasoning. The harness's "write file → mark complete" framing convinces gpt-5.4 it has already done the work.

3. **terminus-2 / gemini-3.1-pro (0/3, all timeouts, 2 with no answer file)** — **format mismatch**. Same gemini in gemini-cli gets 3/3 with pure symbolic reasoning. In terminus-2, gemini-3.1-pro can't reliably emit the JSON-encoded keystroke schema. It produces long stretches of empty assistant messages (parser rejects with "No valid JSON found"), or hallucinates `<tool call> bash_command(keystrokes=…)` text — the format gemini-cli uses natively. Budget gets eaten by these no-op turns. In one run (c61f9db9) the agent textually states the *correct* parity family in its analysis, but never writes it to disk.

**Net**: out of 9 terminus-2 failures, ~3 are genuine model bottlenecks (claude-opus's premature closure) that would have failed in any harness, and ~6 are harness-induced regressions (the same models pass elsewhere). The terminus-2 harness is the wrong tool for math tasks where the deliverable is a characterisation, not a file. This is not specific to `omnimath_2659` — it would predict a systematic terminus-2 underperformance on any descriptive-answer math problem.

## 11. Final verdict

> **The single most valuable answer**: agent failure on `omnimath_2659` is **mostly** a capability bottleneck (claude-opus's premature proof closure, ~50% of failures), with a substantial slice (~50%) being **harness × model fit** (terminus-2 + non-claude-opus models). **None** of the 12 failures are caused by the task itself. The task is correctly specified, has a correct ground truth, has a working LLM judge, and is theoretically and practically solvable — six runs prove that.
>
> Recommendation: **accept the task**, fix the sandbox-isolation anomaly (§10) at the harness level, and consider Fix D for diagnostic instrumentation. Do **not** weaken the instruction by warning agents about multiple families — the resulting failure mode is exactly the kind of "stops at the textbook answer" pattern this task is designed to discriminate.
>
> Caveat for the dataset author: the genuinely interesting capability-bottleneck signal here is "models can find `f(n)=n²` but don't think to test the degenerate `f(2a) ≡ 0` branch". The instructive failure is *not* "model is bad at math" — it is "model assumes the answer is unique because that's what most olympiad answers look like". This is a real and useful signal that the task surfaces well.
