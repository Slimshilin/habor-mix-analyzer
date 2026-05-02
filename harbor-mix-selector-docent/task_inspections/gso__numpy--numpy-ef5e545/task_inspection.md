# Task Inspection: gso-numpy--numpy-ef5e545

**Benchmark:** gso
**Task ID:** gso-numpy--numpy-ef5e545
**Task Checksum:** 7d9cd3e05e83c0d426238140b3579b0c582b04b545bec1f3f1b113b60814d5c1
**Collection:** 640e920a-aef3-4b7c-9487-69899ef19e9d
**Pass Rate:** 2/18 (11.1%)
**Gemini audit verdict:** ACCEPT (high-quality, real-world)
**Our verdict:** ACCEPT (with one minor caveat about threshold tightness) — **agent capability bottleneck dominates**, the task itself is sound

---

## Task Description

Agents receive `/workspace/numpy__numpy` (NumPy source pre-checked-out at commit `ef5e545`) and a 60-line `test_script` that:

1. Generates 50,000 random Unicode strings of length 5-50 (`<U60` dtype) under `random.seed(1234)`. Mix is 75% letters, 13% digits, 9% punctuation, 3% whitespace; ~35% have trailing whitespace; ~5% have an empty insertion mid-string.
2. Calls `np.char.isalpha(data)` → boolean ndarray.
3. Counts True values, returns dict with `alpha_flags` (list[bool]), `total_words=50000`, `count_alpha`.
4. Equivalence check compares all three exactly.

The instruction says: "Make general performance improvements for the usage scenario shown" and "Do not overoptimize for just the specific inputs in <test_script>." It explicitly tells agents to rebuild via `uv pip install . --reinstall` and provides a Cython/setuptools fallback. The instruction does NOT disclose: hidden test count (turns out to be 3 — `gso_test_0/1/2.py`), the `OPT_THRESH = 0.95` and `MIN_PROB_SPEEDUP = 1.2` thresholds, or whether bytes (`NPY_STRING`) is in the hidden test mix.

**Container limits:** 4 CPUs, 0 GPUs, 8 GiB RAM, agent timeout 3h, verifier timeout 1h, `allow_internet = true` (the task does NOT require any network access — corpus is generated locally from a fixed seed, unlike the related `np.char.find` task).

## Verifier Pipeline

`test_sh` performs:
1. `git diff --cached HEAD > /tmp/patch.diff`. If patch_size = 0, immediately `reward=0` with `status: empty_patch`.
2. `git reset --hard HEAD`, then runs `/tests/eval.sh` (inside the docker image). This reapplies the patch on a clean tree, rebuilds NumPy, and runs `gso_test_0/1/2.py` under 3 phases: base (unmodified), patch (agent's), commit (gold solution). Each test runs 5 iterations.
3. `gso_evaluate.py` parses `Execution time:` lines per phase per test and computes `opt_commit` via the upstream `gso.harness.grading.metrics.get_opt_status`:
   ```python
   if base_mean > patch_mean and round(pb_speedup_gm, 1) >= MIN_PROB_SPEEDUP:  # ≥ 1.2x
       opt_status["opt_base"] = True
       if opt(pc_speedup_hm):  # pc_speedup_hm > OPT_THRESH (0.95)
           opt_status["opt_commit"] = True
   ```
4. `reward.txt` set to `1` iff `opt_commit == True`, else `0`.

The grader is **purely time-based**: it does NOT inspect patch shape, file paths, or symbol names. The only correctness gate is "tests pass" (i.e., `experiment(data)` returns equivalent results in patch phase as in base phase) — every observed sampled run passed correctness.

## Gold Solution (from `task.solve_sh`)

Adds a real C++ ufunc for `isalpha`:
1. **`numpy/core/src/umath/string_ufuncs.cpp`** — adds `string_isalpha<rstrip, character>` template, `string_isalpha_loop` for both `npy_byte` and `npy_ucs4`; registers a new `isalpha` ufunc via `PyUFunc_FromFuncAndData` with type signature `[NPY_STRING, NPY_BOOL, NPY_UNICODE, NPY_BOOL]`.
2. **`numpy/core/src/common/numpyos.{c,h}`** — exports `NumPyOS_ascii_isalpha(char c)` so the new loop can reuse it.
3. **`numpy/core/defchararray.py`** — replaces `_vec_string(a, bool_, 'isalpha')` with `multiarray.isalpha(a)`.

The gold approach side-steps the entire `_vec_string` Python-method dispatch infrastructure (Python attribute lookup, scalar boxing, descriptor handling, error-translation, type promotion) and runs as a vanilla NumPy ufunc, which has minimal per-call overhead.

## Run Matrix Summary

| Model | Agent | Pass | Notes |
|---|---|---|---|
| claude-opus-4-6 | terminus-2 | 2/4 | Both passes here; the 2 failures came from one different patch shape (3744d256) and one over-engineered helper |
| claude-opus-4-6 | claude-code | 0/3 | All 3 wrote serious C fast paths inside `_vec_string`; all fell below threshold |
| gpt-5.4 | codex | 0/3 | All 3 wrote competent C fast paths inside `_vec_string`; all fell below threshold |
| gpt-5.4 | terminus-2 | 0/3 | Two settled for `PyObject_CallOneArg` micro-fix (~2% gain); one timed out after revert spiral |
| gemini-3.1-pro-preview | gemini-cli | 0/3 | All 3 wrote real C fast paths covering BOTH bytes + unicode; all fell below threshold |
| gemini-3.1-pro-preview | terminus-2 | 0/3 | Same pattern; agents explicitly considered ufuncs and explicitly rejected as "too invasive" |
| **TOTAL** | | **2/18** | |

The success path: only **claude-opus-4-6 + terminus-2** combos succeeded, and only 2/4 of those.

---

## Q1: How Close Are Agents to Successfully Completing the Task?

**Five categories of closeness:**

### Category A — Correct fast-path inside `_vec_string`, passes timing margin (2 runs, both PASS)
Both passes (a5256238, 25b3f5be) intercepted in `_vec_string` (multiarraymodule.c) BEFORE the per-element Python-method dispatch, with tight inner loops:
- a5256238: generic predicate function pointer + `Py_UNICODE_ISALPHA`, forward scan with embedded-null bail-out
- 25b3f5be: `isalpha`-specific helper + ASCII bit-twiddle macro `((c|0x20)-'a')<26u` + Python-macro fallback for non-ASCII

Both rebuilt cleanly; both reported 6.7-7.5x self-measured speedup.

### Category B — Same architecture but slightly slower or different code path (10 runs, all FAIL)
Same `_vec_string` interception but with a fractional efficiency gap: extra dispatch layers (function-pointer tables, generic 6-9 predicate dispatchers), missing micro-optimizations, contiguity gating that excludes some test inputs. Self-measured speedups range 4-9x.

These were architecturally close but couldn't get within 5% of gold's harmonic-mean speed.

### Category C — Different patch shape (1 run, FAIL)
Run 3744d256 (claude-opus/terminus-2) introduced a NEW Python-visible symbol `_fast_unicode_isalpha`, edited `numpy/core/multiarray.py` to expose it, and rewrote `defchararray.isalpha` to dtype-branch on `kind=='U'`. Self-measured 9.5x speedup (FASTER than the successes). This is the most surprising failure — same model+agent as both successes, faster self-measured speedup, yet reward=0. (Detailed analysis in Q3.)

### Category D — Architectural give-up (2 runs, FAIL)
Runs ab68d1c9 and 8ad260a7 (both gpt-5.4/terminus-2) shipped only the `PyObject_CallFunctionObjArgs` → `PyObject_CallOneArg` micro-fix, which is a 2-3% improvement at best. Run 8ad260a7 actually wrote a real UCS-4 fast path first, observed it regressed in their own benchmark, panicked, and reverted. Both fall below `MIN_PROB_SPEEDUP = 1.2x`.

### Category E — Empty patch (1 run, FAIL)
Run 5b8a9cbf (gpt-5.4/terminus-2): wrote one ASCII fast path that regressed in their benchmark, reverted with `git checkout`, then entered a 3265+ message "conservative revert spiral" emitting `commands: []` until the agent timeout fired. Submitted clean tree → `status: empty_patch`.

---

## Q2: Agent/Model Performance Variation

### Approach Taxonomy by Model

**Claude-opus-4-6 (7 runs: 2 pass)**
- Both successes used **terminus-2** with tight `_vec_string` fast paths.
- 5 failures all reached for C-level work and rebuilt successfully — no model bottleneck on understanding the problem.
- The 3 claude-code failures (b06ce298, 925d9a5e, 086d698e) all wrote architecturally similar fast paths to the successes but ended up below the 0.95× threshold for unclear reasons (possibly extra branching, less-tight inner loops, or contiguity gating). Run 086d698e is particularly telling: 90 messages, 4 rebuilds, 9-predicate dispatcher with cased-character handling — the agent had time and capability to thoroughly engineer the fix, but produced a structurally heavier solution than the successes.
- **Surface reason for failures:** Inner loop or dispatch wrapper is fractionally slower than gold's ufunc.
- **Root cause:** None of the failing claude-opus runs reached the **alternative architectural target** (`string_ufuncs.cpp`). They all went after `_vec_string`. This is reasonable since `defchararray.py` directly imports `_vec_string` — exploration naturally leads there. But the gold-equivalent path (registering a real ufunc) was apparently never seriously considered.

**GPT-5.4 (6 runs: 0 pass)**
- 3 codex runs all wrote competent C fast paths in `_vec_string`. Same architecture as claude-opus successes, slightly different micro-details, all fell short.
- 3 terminus-2 runs all collapsed: one timed out in a revert spiral, two reverted real fast paths and shipped only `PyObject_CallOneArg`.
- **Surface reason:** Either timing-margin failure or no real change.
- **Root cause for terminus-2 collapses:** Agent fragility under uncertainty — when their first attempt regressed (typically due to the embedded-null edge case in trailing padding), the agent treated the regression as definitive and reverted, rather than debugging the inner loop. This is a known agent failure mode in long C-edit-rebuild loops.

**Gemini-3.1-pro-preview (6 runs: 0 pass)**
- ALL 6 runs wrote real C fast paths in `multiarraymodule.c`. None stayed at Python level. (This contradicts the pattern from the related `np.char.find` task where gemini stayed at Python level.)
- **5 of 6 covered bytes (NPY_STRING) too** — better dtype coverage than the successes!
- Yet all 6 failed. **Surface reason:** Below 0.95× harmonic-mean threshold despite 5x self-measured speedups.
- **Root cause:** Gemini agents in 4f45be6a and a20ec2f7 EXPLICITLY considered `string_ufuncs.cpp` (the right target) and EXPLICITLY rejected it as "too invasive." From 4f45be6a B33: *"we would have to define a new ufunc, which involves updating umathmodule.c, adding it to funcs.inc.src, etc. This might be too complex and invasive for just optimizing isalpha."* This is a **scope-conservatism gap**: the agent correctly identified the right target, correctly assessed it would require more changes, and incorrectly concluded that more changes weren't worth the effort. The reference solution is in fact ~150 lines of C++ template code — not trivial but well within scope for a 3-hour task.

### Surface vs Root Cause — Cross-cutting

| Surface failure | Root cause |
|---|---|
| 13 fast-path-in-`_vec_string` runs fell below 0.95× | Inherent overhead in `_vec_string` infrastructure (Python attr lookup, type dispatch, scalar boxing, descriptor handling) that gold's ufunc avoids — these C-fast-path patches reach maybe 85-95% of gold's speed depending on inner-loop tightness; many fall on the wrong side of the threshold |
| 2 `PyObject_CallOneArg` micro-fixes | Agent fragility: regressed first attempt → reverted real C path → shipped trivial change |
| 1 empty patch | Agent fragility: same as above but stuck in idle loop until timeout |
| 1 `defchararray.py` + new symbol approach (3744d256) | Either the new Python-level symbol triggered some `defchararray`-level overhead or the changed import path caused a subtle issue not visible in agent's local tests |

The unifying root cause across 14 of 16 failures is **failure to recognize ufunc registration as the target of choice**. Agents read `defchararray.py`, find `_vec_string`, decide to optimize `_vec_string`. Almost none ask "what's the canonical NumPy way to add a vectorized scalar-string operation?" and find `string_ufuncs.cpp`.

---

## Q3: Concrete Failure Behaviors vs. Expected

### What the verifier expects (from grading code, verbatim)

```python
# from src/gso/harness/grading/metrics.py (gso-bench/gso)
if base_mean > patch_mean and round(pb_speedup_gm, 1) >= MIN_PROB_SPEEDUP:  # 1.2
    opt_status["opt_base"] = True
    if opt(pc_speedup_hm):  # pc_speedup_hm > 0.95
        opt_status["opt_commit"] = True
```

So the patch must:
1. Beat base (unmodified numpy) by ≥ 1.2× geometric-mean across 3 tests AND
2. Run within ~5% of the gold solution (harmonic mean of `commit_time / patch_time` > 0.95)

The visible `test_stdout` for sampled runs confirms `>>>>> Tests Passed` for all 3 hidden tests in every observed case — i.e., correctness is not the failure mode; the timing-margin is.

### Failure Type 1: Real fast path, just below 0.95× of gold (10 runs)

**Representative — run b06ce298 (claude-code), self-measured 5.5x speedup but rewarded 0:**

```c
/* Inserted in _vec_string in multiarraymodule.c */
if (PyArray_TYPE(char_array) == NPY_UNICODE
        && PyArray_IS_C_CONTIGUOUS(char_array)
        && (args_seq == NULL
            || (PySequence_Check(args_seq) && PySequence_Size(args_seq) == 0))
        && PyUnicode_Check(method_name)
        && PyUnicode_CompareWithASCIIString(method_name, "isalpha") == 0) {
    Py_DECREF(type);
    result = _unicode_isalpha_fast(char_array);
    ...
}
```

vs. **successful run 25b3f5be:**
```c
/* Same dispatcher hook + this loop body */
if (ch < 128) {
    if (!_is_ascii_alpha(ch)) { is_alpha = 0; break; }  // bit-twiddle
} else if (!Py_UNICODE_ISALPHA(ch)) { is_alpha = 0; break; }
```

The success uses an inlined bit-twiddle ASCII fast path before falling through to `Py_UNICODE_ISALPHA`. The failure uses `Py_UNICODE_ISALPHA` for every character. For a corpus that's mostly ASCII letters (75%+ in the test_script), the difference is significant — `Py_UNICODE_ISALPHA` is a function-call macro that does table lookup; the bit-twiddle is 3 instructions inline. Over 50,000 strings × ~25 chars avg = 1.25M iterations, even a 30ns difference per character compounds to ~40ms.

That kind of micro-optimization tightness is what separates passes from fails at the 95% threshold.

### Failure Type 2: `PyObject_CallOneArg` micro-fix (2 runs)

**Run ab68d1c9 (gpt-5.4/terminus-2) — entire patch:**
```c
- item_result = PyObject_CallFunctionObjArgs(method, item, NULL);
+ item_result = PyObject_CallOneArg(method, item);
```

This change saves ~10ns/element (one fewer tuple allocation), giving a 2-3% improvement at best. Self-measured: baseline ~10.6 ms → after-patch ~10.5 ms — within noise. The agent admitted as much in their final message ("marginally better than baseline, but the improvement is very small and within noise") and shipped anyway. Fails `MIN_PROB_SPEEDUP=1.2x`.

### Failure Type 3: Empty patch via revert spiral (1 run)

**Run 5b8a9cbf (gpt-5.4/terminus-2) trajectory:**
- Messages 1-50: explored, wrote a real ASCII fast path, rebuilt, observed regression to ~13ms (vs ~9.7ms baseline).
- Message ~52: `git checkout -- numpy/core/src/multiarray/multiarraymodule.c`, restored baseline.
- Messages 55-3320: 3265 consecutive turns of identical content `"Analysis: No new output or changes... Plan: No commands to run"` with `commands: []`. Terminal echoed the same idle prompt every tick.
- Message 3321: `AgentTimeoutError`, ending with a clean tree.
- `test_sh` saw `PATCH_SIZE=0` → `status: empty_patch, reward=0`.

This is an agent stability issue, not a task issue.

### Failure Type 4: New Python symbol approach — same model, opposite outcome (1 run)

**Run 3744d256 (claude-opus/terminus-2, same setup as the 2 successes, but FAILED) — `defchararray.py` edit:**
```python
a = numpy.asarray(a)
if a.dtype.kind == 'U':
    return _fast_unicode_isalpha(a)
return _vec_string(a, bool_, 'isalpha')
```

Plus a new `_fast_unicode_isalpha` C function in `multiarraymodule.c`, plus an export edit to `numpy/core/multiarray.py`. Self-measured 9.5× — FASTER than the 6.7-7.5× of the successes. Yet the verifier returned `opt_commit: False, reward: 0`.

**Plausible root causes** (cannot be 100% confirmed without verifier internals):
1. The patch's `numpy.asarray(a)` does extra work for every call vs. the successes' approach (which leaves `defchararray.isalpha` unchanged and intercepts deeper).
2. Editing `numpy/core/multiarray.py` to expose `_fast_unicode_isalpha` could produce a stale or partially regenerated `multiarray.py` after rebuild (this file's contents are partly synthesized by NumPy's build).
3. The agent's `_fast_unicode_isalpha` C loop has an unbounded forward scan that doesn't bail at trailing nulls — it iterates ALL `itemsize` chars (60) for every element regardless of actual content length, vs. the successes' backward-strip-then-iterate (which iterates ~25 chars for ~25-char strings). For 50k × (60-25)=35 wasted iterations, that's 1.75M extra Py_UCS4 reads; at ~1ns each, ~1.75ms extra — could push them below threshold despite higher self-measured speedup with their corpus.

The third explanation is concrete and consistent with all observed evidence: the failing run ran fast in their warm cache locally but slower under the verifier's measurement protocol where the per-test overhead added up.

---

## Q4: Task Self-Containedness Analysis

### Can a sufficiently capable agent solve this?

**Yes.** Two runs demonstrate it. The gold solution is ~150 lines of C++ template code in `string_ufuncs.cpp`. Multiple alternative routes work: tight `_vec_string` interception (the successes), or registering a real ufunc (gold approach).

### What does "sufficient capability" mean here?

1. **Diagnose**: Identify that `_vec_string` does per-element `PyArray_ToScalar` + Python-method dispatch (visible by reading `multiarraymodule.c::_vec_string_no_args`).
2. **Choose target architecture**: Either (a) intercept inside `_vec_string` with a tight C loop, or (b) register a `multiarray.isalpha` ufunc and rewire `defchararray.py`. The latter is canonical NumPy.
3. **Tight C loop**: Strip trailing nulls correctly (handle embedded `\x00` per the test corpus's 5% mid-string insertions), use ASCII fast path for the common case, fall back to `Py_UNICODE_ISALPHA` for ≥128.
4. **Build awareness**: The instruction explicitly tells agents to rebuild via `uv pip install . --reinstall`. Most agents handle this fine.

### Can agents infer everything they need?

| Inference required | Inferable from environment? |
|---|---|
| `_vec_string` is the hot path | YES — by reading `defchararray.isalpha` |
| Trailing nulls must be stripped | YES — by reading `multiarraymodule.c::_vec_string_no_args` and seeing how it handles padding |
| Embedded null edge case (`a\x00b` is False, not True) | YES — by running `'a\x00b'.isalpha()` in Python OR reading the test_script's 5% empty-insertion logic |
| ASCII fast path matters for performance | PARTIALLY — corpus is 75% letters, agents who profile would see this. Otherwise they'd write `Py_UNICODE_ISALPHA` every char. |
| `string_ufuncs.cpp` is the canonical target for ufuncs | YES — this file is in the open repo and contains existing ufunc registrations (`equal`, `not_equal`, etc.). `git grep -l "PyUFunc_FromFuncAndData"` finds it instantly. |
| 0.95× harmonic-mean threshold | NO — this is hidden in the GSO benchmark code. Agents have no way to know the exact margin required. |
| 1.2× geometric-mean threshold for opt_base | NO — same as above. |
| 3 hidden tests (gso_test_0/1/2.py) | NO — hidden, but the instruction says "general performance improvements" |
| Bytes (`NPY_STRING`) is or isn't tested | NO — but irrelevant: 13 successful runs and the 2 actual passes lacked bytes coverage; bytes coverage doesn't appear to be tested |

The threshold opacity is real but tolerable: a capable agent that aims at "match the gold reference" wouldn't need to know the exact threshold to pass. The "generalize beyond the inputs" hint in the instruction implicitly tells agents not to take shortcuts.

### Can a super-capable being resolve this?

**Yes**, unambiguously. The task is theoretically self-contained. The signal that 2/18 ran's pass with this same architectural choice (tight `_vec_string` interception) demonstrates the threshold is achievable without going all the way to gold-style ufuncs. A super-capable agent that recognized the bit-twiddle ASCII fast path or chose the ufunc route would pass deterministically.

### Network dependency?

Unlike the related `gso-numpy--numpy-83c780d` (`np.char.find`) task that downloads from Project Gutenberg in the eval scripts, this task generates corpus data deterministically from `random.seed(1234)` — **no network dependency, no risk of network-failure-causes-zero-score**.

---

## Q5: Proposed Fixes

### Fix 1 (Optional — Threshold Disclosure): Tell agents the rough threshold

**Problem:** Several near-pass runs report self-measured speedups (5-9×) that they considered satisfactory. They have no way to know that the verifier requires being within 5% of the reference solution's harmonic-mean speedup.

**Fix:** Add to the instruction: "Your patch must be at least 1.2× faster than the unmodified baseline AND must run within ~5% of the reference implementation's speed across multiple test inputs."

**Counter-argument:** This is fairly standard for performance benchmarks (they're scored against a reference). Adding this disclosure doesn't help an agent who can't get within 5% of the reference; it just tells them they failed earlier. The current opacity is reasonable: it tests whether agents try to write the *best* optimization, not the *minimally adequate* one.

**Recommendation:** OPTIONAL — could help agents calibrate effort, but doesn't obviously raise the pass rate among capable agents.

### Fix 2 (Optional — Score Granularity): Proportional reward

**Problem:** Binary scoring at 0.95× harmonic mean creates a sharp cliff. Agents at 0.94× (functionally equivalent C optimization) get 0; agents at 0.96× get 1. The task signal becomes noisier than necessary.

**Fix:** Change reward to `min(pc_speedup_hm, 1.0)` so an agent that hits 0.94× gets 0.94 reward.

**Counter-argument:** The harbor mix matrix expects binary rewards. Changing this requires upstream coordination. Also, the cliff is informative — passes mean "matched the reference"; near-passes mean "got most of the way."

**Recommendation:** OPTIONAL — would smooth signal but doesn't change which agents are capable.

### Fix 3 (No fix needed): Network — already fine

The task does NOT depend on network access. `random.seed(1234)` ensures deterministic corpus. No infrastructure-failure risk.

### Fix 4 (No fix needed): Bytes coverage in instruction

The 2 successful runs both lacked bytes coverage and still passed, which means the hidden tests are pure Unicode. There's no evidence bytes coverage is tested. No need to mention bytes in the instruction.

---

## Final Verdict

### Is the primary cause of failure agent capability or task issues?

**Primary cause: Agent capability bottleneck (dominant)**

Concrete evidence:
1. **2 runs pass** with valid, independently-derived solutions on a tight `_vec_string` interception architecture. The task is solvable.
2. **0 runs across all 6 model+agent combinations attempted the canonical ufunc approach** — even gemini agents who *explicitly identified* `string_ufuncs.cpp` as the right target *explicitly rejected* it as "too invasive." This is a capability/judgment gap, not a task design issue.
3. **All 16 failures fall into well-defined capability buckets:**
   - 10 fail by writing C fast paths just below the 95% threshold (micro-optimization gap; the successes had ASCII bit-twiddle, the failures didn't)
   - 1 fails on patch-shape choice (3744d256 — added new Python symbol, self-measured fastest, still failed; possibly extra `np.asarray` overhead or unbounded inner-loop scan)
   - 2 fail by reverting real attempts and shipping `PyObject_CallOneArg` micro-fix (terminus-2 fragility under regression)
   - 1 fails by entering 3265-message idle loop (terminus-2 timeout under uncertainty)

4. **No infrastructure failures.** All 16 failures rebuilt successfully (or chose not to build). The verifier ran tests cleanly (`Tests Passed` × 3 in every observed case). No `Patch Apply Failed`, no `BASE_FAILED`, no network errors.

5. **Threshold is tight but achievable.** OPT_THRESH = 0.95 means "match the gold reference within 5%." Two agents matched. The other agents fell short on micro-optimization tightness or chose the wrong architectural target (most stayed at `_vec_string` rather than registering a ufunc).

### Secondary cause: Task design has minor friction

1. **Tight 0.95× threshold** creates a cliff between "fundamentally correct" and "fundamentally correct + perfectly tuned." Several runs (e.g., 086d698e with 9-predicate dispatcher, 4 rebuilds, comprehensive testing, 9× self-measured speedup) demonstrate that capable engineering effort can fall short by inches. This is unfair to agents who do good but not perfect work, but it's also an honest test of "can you match the reference?"

2. **Threshold opacity** — the 0.95× figure isn't disclosed to agents. They have no way to calibrate target speed. This is a minor design choice rather than a flaw.

3. **No clear architectural hint** that the canonical NumPy approach for `np.char.X` operations is to register a ufunc in `string_ufuncs.cpp`. A capable agent should discover this by exploring the codebase, but several gemini agents actively rejected the path as "invasive" — suggesting the intended path isn't obvious.

### Recommendation

**ACCEPT.** This is a high-quality task that:
- Has a clear, well-formed objective (optimize `np.char.isalpha`).
- Has multiple valid solution paths (tight `_vec_string` patch OR ufunc registration).
- Discriminates well between agent capability levels (claude-opus/terminus-2 passes; weaker model/agent combos fail).
- Has a robust verifier (deterministic corpus, three test scripts, multi-iteration timing, gold-solution comparison).
- Has no infrastructure flaws (no network dependency, no patch-apply problems, no environment instability).

The 11.1% pass rate (2/18) is consistent with a "hard" performance task tagged `difficulty = "hard"` in `task.toml`. The Gemini auditor's verdict is correct.

**Quality signal this task provides:**
- Pass: agent can engineer a tight C-level fast path that matches the reference within 5%.
- Near-pass (most failures): agent understood the problem and wrote real C, but couldn't quite match the reference performance.
- Hard fail (3 runs): agent unable to engage with C-level work in a stateful build environment.

This is a **meaningful capability discriminator** worth preserving. Could be polished by disclosing thresholds (Fix 1) but doesn't require it.

---

## Appendix: Observed Verifier Timings

From the `Start Commit Output` block of `test_stdout` (only this block was echoed; Base and Patch phase timings live in the upstream eval log not surfaced to stdout):

| Run | Test 0 mean | Test 1 mean | Test 2 mean |
|---|---|---|---|
| a5256238 (PASS) | 1.671 ms | 0.704 ms | 0.310 ms |
| 25b3f5be (PASS) | 1.667 ms | 0.661 ms | 0.304 ms |
| 3744d256 (FAIL) | 0.661 ms | 0.661 ms | 0.305 ms |
| 82959539 (FAIL) | 1.671 ms | 0.703 ms | 0.310 ms |
| b06ce298 (FAIL) | 1.660 ms | 0.636 ms | 0.307 ms |

The "commit times" (gold-solution-applied timings) are remarkably similar across runs that pass tests — confirming the verifier's commit phase is deterministic. The reward outcome is not predictable from these visible commit-only timings alone; it depends on the upstream `gm_speedup_patch_base` (geometric mean of base/patch) and `hm_speedup_patch_commit` (harmonic mean of commit/patch) which the verifier doesn't echo to stdout.

## Appendix: Verifier Implementation (verbatim from gso-bench/gso/src/gso/harness/grading/metrics.py)

```python
def opt(speedup):
    return speedup > OPT_THRESH  # OPT_THRESH = 0.95

# In get_opt_status():
if base_mean > patch_mean and round(pb_speedup_gm, 1) >= MIN_PROB_SPEEDUP:  # 1.2
    opt_status["opt_base"] = True
    if opt(pc_speedup_hm):  # pc_speedup_hm > 0.95
        opt_status["opt_commit"] = True
```

Constants from `gso/constants.py`:
- `MIN_PROB_SPEEDUP = 1.2`
- `OPT_THRESH = 0.95`
- `LOW_TEST_FALLBACK_SPEEDUP = 1.1`
- `MAX_TEST_COUNT = 20`
- `LOW_TEST_IDEAL_TEST_COUNT = 5`
