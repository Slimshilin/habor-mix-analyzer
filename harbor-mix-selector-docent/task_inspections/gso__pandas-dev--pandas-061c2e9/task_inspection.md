# Task Inspection: gso/gso-pandas-dev--pandas-061c2e9

**Benchmark:** GSO (Global Software Optimization)
**Task ID:** `pandas-dev__pandas-061c2e9`
**Goal:** Optimize `pandas.merge_ordered` (and the broader merge path it relies on) for sorted (monotonic-increasing) keys, while preserving functional equivalence across heterogeneous scenarios.
**Reviewer label:** Accept (gemini)
**Sample success rate observed:** 0 / 18
**Docent collection:** `640e920a-aef3-4b7c-9487-69899ef19e9d`
**Verifier setup:** the verifier runs 20 hidden test scripts (`/tests/gso_test_0.py` ... `gso_test_19.py`), each 5 iterations pre-patch + 5 iterations post-patch. Reward = 1 only if (a) every post-patch run passes equivalence, AND (b) the aggregated wall-clock improvement clears the GSO threshold (vs. the original code on the same machine).

---

## 1. Task spec, environment, verifier

### 1.1 Instruction (verbatim, abridged)

The agent gets a self-contained instruction (`_task_instruction.md`) embedding a single example test script:

```python
def setup():
    np.random.seed(42)
    left  = pd.DataFrame({'key': np.arange(0, 1000000, 2), 'val1': np.ones(500000)})
    right = pd.DataFrame({'key': np.arange(500000, 700000, 1), 'val2': np.full(200000, 2)})
    left  = left.sort_values('key').reset_index(drop=True)
    right = right.sort_values('key').reset_index(drop=True)
    return left, right

def experiment(left, right):
    return pd.merge_ordered(left, right, on='key', how='inner')
```

…with guidelines: "Make general performance improvements for the usage scenario shown… ensure functional equivalence… do not overoptimize for just the specific inputs."

The visible scenario is **inner join, single integer key, both sides unique, monotonically increasing**. The verifier's hidden suite is much wider — it covers outer/left/right joins, datetime keys (incl. tz-aware), duplicate-key sorted joins (the `dup_monotonic` scenario), and mixed dtypes.

### 1.2 Reference solution (extracted from docent metadata)

The committed fix touches **three** files (key insight: the optimization is not localized to `merge_ordered`):

1. **`pandas/core/reshape/merge.py`** — In `_MergeOperation`, allow `left_indexer is None` or `right_indexer is None` to mean "identity indexer" (a fast-path encoding for sorted-keys joins). Previously the code did `(left_indexer == -1).any()`, which crashes on `None`.
2. **`pandas/core/indexes/base.py`** — `_join_non_unique` now calls a new `get_join_indexers_non_unique(self._values, other._values, how, sort)` helper, splitting the sorted/duplicate path off into its own routine (the original called `get_join_indexers` with a list-of-arrays, which is the hash-join entry point).
3. **`pandas/core/groupby/generic.py`** — guard `if idx is not None` before `np.where(idx != -1, out[idx], 0)`, since the new fast path can return `None` for the identity case.

The PR is upstream pandas issue #56115 ("Performance improvement in `merge` and `merge_ordered` when joining on sorted ascending keys"). The patch is conceptually small (~70 net lines) but **architecturally non-local**: a fast path needs to coordinate three modules to avoid breaking duplicate-key semantics.

### 1.3 Verifier mechanics

`/tests/test.sh`:
1. Snapshots the agent's working tree as `/tmp/patch.diff`.
2. `git reset --hard HEAD`, then runs `eval.sh` which:
   - Runs all 20 `gso_test_*.py` 5× each on the **base** commit.
   - Applies the agent's patch.
   - Runs all 20 again 5× each.
3. `gso_evaluate.py` compares pre/post timings + correctness (each test calls `check_equivalence` against a stored reference). Reward = `1` iff `opt_commit: True`.

Each `gso_test_*.py` carries a `check_equivalence` that asserts shape, column list, and per-column sums (rel_tol=1e-6, abs_tol=1e-8). The visible example shows shape + sums; the hidden tests share that pattern but with diverse `setup()` data including duplicates, datetimes, and tz-awareness.

Critically: the hidden test files are present in the container at `/tests/gso_test_*.py` and are readable by the agent — they are *hidden* in the sense that the instruction doesn't mention them, not in the sense that the filesystem hides them.

---

## 2. The 18 agent runs at a glance

| Run (short id) | Agent | Model | Failure mode | Files patched |
|---|---|---|---|---|
| 4bee449c | claude-code | claude-opus-4-6 | AssertionError gso_test_12 `dup_monotonic` shape (200k vs 300k) | merge.py |
| 931a51ff | claude-code | claude-opus-4-6 | AssertionError gso_test_10 outer-merge sum mismatch | merge.py |
| e4e7fc03 | claude-code | claude-opus-4-6 | AssertionError gso_test_10 outer-merge sum mismatch | merge.py |
| 5d592888 | codex | gpt-5.4 | Tests pass, **insufficient speedup** | merge.py |
| d9514fe8 | codex | gpt-5.4 | Tests pass, **insufficient speedup + slowdown on test 12** | merge.py |
| d34ce991 | codex | gpt-5.4 | Tests pass, **slowdown on tests 10/12/18** | merge.py |
| 7823a247 | gemini-cli | gemini-3.1-pro-preview | AssertionError gso_test_12 `dup_monotonic` | merge.py |
| 15ff80f2 | gemini-cli | gemini-3.1-pro-preview | Tests pass, **insufficient speedup** | merge.py |
| 4bb79f8e | gemini-cli | gemini-3.1-pro-preview | Tests pass, **insufficient speedup** | merge.py |
| 09b70675 | terminus-2 | claude-opus-4-6 | AssertionError gso_test_12 `dup_monotonic` | merge.py |
| 5c2824c8 | terminus-2 | claude-opus-4-6 | AssertionError gso_test_12 `dup_monotonic` | merge.py |
| 1b530e64 | terminus-2 | claude-opus-4-6 | Equivalence likely failed silently for tests 12/13/18 (post-patch timings absent); verifier opt_commit=False | merge.py |
| bfb1f876 | terminus-2 | gemini-3.1-pro-preview | Tests pass, **insufficient speedup** (test 12 unimproved) | merge.py |
| c0d84c3a | terminus-2 | gemini-3.1-pro-preview | **Runtime AttributeError**: `'numpy.ndarray' object has no attribute 'is_monotonic_increasing'` on test 14 | merge.py |
| d6cbbc54 | terminus-2 | gemini-3.1-pro-preview | Tests pass, **insufficient speedup** | merge.py |
| 44e332f9 | terminus-2 | gpt-5.4 | AssertionError gso_test_12 `dup_monotonic` | merge.py |
| 25a6522b | terminus-2 | gpt-5.4 | Tests pass, **insufficient speedup (only ~4×)** | merge.py |
| 9546af5b | terminus-2 | gpt-5.4 | AssertionError gso_test_9 `monotonic` shape (74109 vs 75315) | merge.py |

**Headline observations** (these patterns hold across **18/18** runs):

1. **Every single agent edited only `pandas/core/reshape/merge.py`.** Zero touched `indexes/base.py` or `groupby/generic.py`. The reference fix is architecturally non-local; agents converged on a localized fix.
2. **Zero agents inspected `/tests/gso_test_*.py`.** Despite the files being readable on the filesystem, none of the 18 agents thought to look there. (Several inspected the in-repo `pandas/tests/reshape/merge/test_merge_ordered.py`, but that public unit suite doesn't include the dup-monotonic stress case.)
3. **Most agents reached for the same wrong primitive.** `libjoin.inner_join_indexer` / `outer_join_indexer` / `left_join_indexer` is the *Index-level* monotonic merge primitive (used by `Index.join`), and is correct only when at least one side is unique. Eight of eighteen agents called it under a `is_monotonic_increasing` guard *without* an `is_unique` check — exact match of the trap the reference solution explicitly avoids by adding `get_join_indexers_non_unique`.
4. **All commits are single-iteration.** Agents typically wrote one patch, ran their own toy benchmark + (sometimes) the in-repo pytest suite, declared a 70–250× speedup, and stopped. There is essentially no "verify against varied inputs and iterate" loop.

---

## 3. Per-question deep dive

### 3.1 How close are agents to successfully completing the task?

Closeness depends on the failure mode:

- **The 9 "AssertionError / runtime crash" runs** are *not* close. They have a fundamentally wrong understanding of the join contract: they invoke a unique-keys-only primitive on inputs that may contain duplicates, and the failure surfaces as a shape mismatch on dup_monotonic. Adding an `is_unique` guard would make the patch correct **but** then the fast path would not fire on the dup_monotonic test, pushing them into the "insufficient speedup" bucket.
- **The 8 "tests pass but insufficient speedup" runs** are closer. They wrote correct fast paths, but those paths only handle the easy single-key, monotonic-and-unique-on-at-least-one-side case. The reference solution requires handling the duplicate-key sorted case too — which sits in `_join_non_unique` (`indexes/base.py`). None of these agents touched that file. So they are roughly "halfway" to the reference solution: correct for the simple case, missing the duplicate-key fast path that the dup_monotonic and similar hidden tests require for their speedup vote.
- **No agent is in the "1 typo away from success"** zone. The shortest patch (terminus-2/gpt-5.4 run 25a6522b at 1009 bytes) is a wrapper-level delegation that bypasses `_OrderedMerge`'s sort flag and simply re-uses `pd.merge`. It's the cleanest reasoning, but only delivers ~4× speedup because it never reaches the actual factorization hot path.

In short: the failure surface ranges from "structurally wrong primitive" to "right idea, missing the duplicate-key half of the fast path." Even the best agent runs are missing 2 out of 3 reference-solution files.

### 3.2 Variance across agent-model pairs (surface vs. root)

**Convergence is the dominant pattern, not divergence.** All 18 runs (across 4 agents × 3 models) reached the same family of partial fixes:

- **Approach 1 (8 runs, mostly "Override `_OrderedMerge._get_join_indexers`")**: claude-code/opus, gemini-cli/gemini, terminus-2/opus, terminus-2/gpt-5.4. Pattern: bypass factorize and dispatch to `libjoin.*_join_indexer` for sorted single numeric/datetime keys. Failure: `libjoin.*_join_indexer` is the unique-keys primitive.
- **Approach 2 (3 codex/gpt-5.4 runs)**: same `libjoin` dispatch but inside the *generic* `get_join_indexers` (not the `_OrderedMerge` override). They added a `(left_key.is_unique or right_key.is_unique)` guard, which **dodges** the dup_monotonic correctness bug — but then the fast path doesn't fire on dup_monotonic, leaving the speedup vote insufficient. (Run d34c also introduced slowdowns on tests 10/12/18 from extra branching overhead.)
- **Approach 3 (3 terminus-2/gemini runs + 1 terminus-2/gpt-5.4 run 25a6522b)**: patch only `_OrderedMerge.__init__` to avoid `sort=True` when keys are already monotonic. Functionally minimal change, ~4× speedup, never reaches the verifier's bar.

**Surface causes (per run):**
- "Wrong shape on dup_monotonic" → using libjoin's unique-only primitive on duplicate keys
- "Insufficient speedup" → fast path's guard excludes the duplicate case (which is a major term in the test suite's wall time)
- "AttributeError on test 14" → bare attribute access on numpy array (run c0d84c3a dropped a `pd.Index()` wrap that earlier drafts had)
- "Outer-merge sum mismatch" → libjoin's outer_join_indexer dedup behavior

**Root causes (shared across the cohort):**

1. **Hidden-test discoverability blind spot.** None of 18 agents listed `/tests/` to discover `gso_test_*.py`. Even agents that inspected the in-repo unit tests did not realize the verifier had a separate, broader battery. This is the single biggest leverage point.
2. **Insufficient codebase comprehension before editing.** Agents assumed `libjoin.{inner,left,outer}_join_indexer` was the right primitive based on its name. None traced its callers (it's only called from `Index._join_monotonic`, which the cython source comment marks as "Both left and right are monotonic increasing but not necessarily unique" — but the implementation depends on the caller having already deduplicated). The reference solution author *also* didn't use it as a generic substitute; instead they added `get_join_indexers_non_unique`.
3. **Self-validation that is systematically duplicate-blind.** Agents wrote "edge case" scripts, but in 18/18 cases their duplicate-key probes either (a) used symmetric duplicates `[1,1,3,3]` vs `[1,1,3,3]` where libjoin's output coincidentally matches the cross-product, or (b) used asymmetric one-sided duplicates `[1,1,3,3]` vs `[1,3,5]` where the count is also 4 either way. Run e4e7fc03 went so far as to print *identical 5-row results for inner / outer / left / right joins* and not flag it as a correctness smell. This is a meta-failure of test design, not of optimization.
4. **Single-iteration commits.** No agent ran their patch against arbitrary inputs of varying duplicate density and dtype; every agent declared victory after one or two passes of self-built tests.
5. **Anchoring on the visible example.** The instruction's example uses `np.arange(...)` keys (perfectly unique). Agents took the example as the target distribution; the verifier intentionally tests a wider population.

**Conclusion on variance:** Surface symptoms differ across runs because there are several subtly-broken-or-insufficient choices the agent can make, but **the root failure is the same in 18/18 cases**: the agents do not realize the relevant validation surface is wider than the visible example, and they do not have enough humility about the join semantics they are altering.

### 3.3 Concrete agent behaviors that failed the tests

Two failure-class examples illustrate the pattern.

**Example A — `gso_test_12.py` (dup_monotonic shape mismatch).** Failed by 5 runs.

The hidden test sets up two sorted DataFrames with overlapping duplicate keys (e.g. left has key=5 once, right has key=5 a hundred times → the inner-join cartesian must emit 100 rows for that key) and asserts:
```python
assert tuple(ref_result['shape']) == curr_shape, \
    f'Expected shape {ref_result["shape"]}, got {curr_shape}'
```
Pre-patch result: `(300000, 3)`. Post-patch agent result: `(200000, 3)`. The `inner_join_indexer` cython routine deduplicates one side per matching key (Index-merge semantics), so the cartesian expansion is lost. Five runs (4bee449c, 7823a247, 09b70675, 5c2824c8, 44e332f9) hit this exact failure with the exact same numbers, because they all converged on the same misuse of `libjoin.inner_join_indexer`.

**Example B — "Tests pass, but `opt_commit: False, reward: 0`".** This is the per-test-timing failure mode (run 5d592888 is representative).

The verifier's stdout shows pre-patch and post-patch timings interleaved, e.g.:
```
Test 0:  pre 0.0045s → post 0.0040s  (1.11×)
Test 12: pre 0.1333s → post 0.1014s  (1.31×)   ← dup_monotonic; barely improved
Test 14: pre 0.84s   → post 1.21s    (0.69×)   ← slowdown
Test 17: pre N s     → post N/12 s   (~12×)    ← unique-key cases
```
The verifier requires meaningful speedup across the suite. With dup_monotonic stuck at the slow path (fast path guarded out by `is_unique`) and a slowdown on test 14, the aggregate doesn't clear `opt_commit`. The agent's local benchmark on the toy example showed 70–250× speedup, which created false confidence.

**Example C — runtime AttributeError (run c0d84c3a).** The patch did:
```python
if self.how in ("inner","left","right"):
    if all(s.is_monotonic_increasing for s in self.left_join_keys):
        self.sort = False
```
`self.left_join_keys` is a list whose elements may be `Series`, `numpy.ndarray`, or `ExtensionArray`. For test 14 the keys arrived as bare `numpy.ndarray`, which has no `is_monotonic_increasing` attribute. An earlier draft had `pd.Index(s).is_monotonic_increasing` (correct), but the agent removed the `pd.Index(...)` wrap and only validated against their own toy script, where keys were always Series.

### 3.4 Is the failure attributable to the task?

I will be strict here, since the user specifically asked. The questions to answer:

**(a) Can the agent infer from the environment what's being tested?**

The verifier's `test.sh` is *not* shown to the agent (it lives in `/tests/`). However:
- The container has `/tests/test.sh`, `/tests/eval.sh`, and `/tests/gso_test_*.py` all readable. A capable agent can `ls /tests/` and read the files.
- The instruction does not mention `/tests/` exists. It only describes the visible example test_script and asks for "general performance improvements."

So discoverability is "possible but undirected." I'd argue this is **part of the task's design intent** — GSO is benchmarking whether agents can produce robust, generalizable optimizations from a single representative example, not whether they can pass a known test bank. The very phrase "Do not overoptimize for just the specific inputs in <test_script>" signals that the agent must reason about other plausible inputs.

The fact that 18/18 agents failed to even `ls /tests/` is itself a strong agent-capability signal. A skilled engineer in this scenario would (i) read the harness scripts to know exactly what's measured, or (ii) reason about pandas merge semantics broadly enough to notice duplicates matter.

**(b) Can a super-capable being resolve this task given the current instructions and environment?**

Yes, unambiguously. The reference solution is real, it lives in the upstream pandas history, and:
- The instruction is clear about the goal (speedup) and the constraints (functional equivalence, no over-fitting).
- The codebase is fully present at `/workspace/pandas-dev__pandas`.
- The build/test loop works (`uv pip install . --reinstall` is documented in the instruction).
- The verifier's correctness assertions use sensible tolerances (rel_tol=1e-6, abs_tol=1e-8).
- The hidden tests are accessible if the agent investigates.

The required reasoning chain is: "merge_ordered uses the regular merge join machinery → that machinery factorizes keys → for sorted keys, factorization is wasteful → I can short-circuit with a sorted-keys path → but the sorted path must handle duplicate keys (because pandas merge has cartesian semantics on duplicates) → I need to plumb that through `_MergeOperation`, `_join_non_unique`, and the `groupby` consumer of `get_join_indexers`."

That chain is non-trivial but tractable. The reference solution PR is ~70 lines across 3 files.

**(c) Is the verifier reasonable?**

Yes. Reasonable tolerances. Compares against the same machine's pre-patch baseline (no flakiness across machines). Requires correctness AND speedup, which is the actual definition of a "performance optimization." 20 hidden tests covering datetime/tz/dup/outer/multi-dtype is a reasonable sample of pandas merge usage.

One mild concern: the `opt_commit` boundary (the speedup threshold for an "accepted" optimization) is opaque to the agent. If the threshold is set so that *only* the reference solution's specific 3-file fix would pass, then partial fixes are systematically excluded. But this seems intentional — GSO measures whether agents match expert developer commits, not whether they make any improvement.

### 3.5 Could the task be fixed?

Three possible "fixes," each evaluated critically:

**Fix A — Mention `/tests/` in the instruction.** Add a single line: "The verifier validates correctness on a hidden battery of test scripts in `/tests/gso_test_*.py`. You may inspect them to understand the equivalence surface." Pros: removes the discoverability gap; some agents would clearly use the hint. Cons: this fundamentally changes GSO's benchmark intent (testing generalizable reasoning under partial spec, not test-driven coding). Not really a "fix" — it's a different task.

**Fix B — Provide a richer example test_script.** Include 2–3 example scenarios (unique sorted, duplicate sorted, datetime sorted) with explicit equivalence checks. Pros: nudges the agent toward the right edge cases without giving away the test set. Cons: arguably already implicit in "general performance improvements." Reasonable improvement, but doesn't address the deeper exploration deficit.

**Fix C — No task change; this is a hard task and 0/18 reflects current model capability.** GSO explicitly aims at "frontier model" tasks. The reference solution author is a pandas core developer with full repo intuition. Expecting current agents to (i) read the join code thoroughly enough to know `libjoin.*_join_indexer` is unique-keys-only, (ii) realize that fast-pathing a sorted unique inner join requires also fast-pathing the non-unique sorted case via `_join_non_unique`, and (iii) realize this triggers a `None`-handling change in the groupby consumer, is a *very* high bar. Capable agents will solve this with more inference-time compute, broader exploration, or better test-discovery prompting strategies — but the task itself isn't broken.

**Recommended verdict on fixes:** No mandatory fix. **Optional improvement (Fix B)**: append one sentence to the instruction that explicitly alludes to common edge cases, e.g. "Consider that `merge_ordered` must remain correct for joins with duplicate keys, varied dtypes (datetime, datetime+tz, integer, float), and all four `how` values (inner/left/right/outer)." This is a fair hint that doesn't reveal the test set, but it does close the most common blind spot. With this hint, I'd predict 2–4 of the 18 runs would have passed (the ones that already produced correct partial fixes might have iterated to add the duplicate-key path).

If we consider the reviewer comment: gemini said "agent failures are attributed to the genuine complexity of the pandas merge implementation and the precision required to avoid regressions." That matches my analysis. The reviewer's "Accept" is correct.

---

## 4. Verdict

### 4.1 Is the task itself the cause of failure?

**No.** The task is well-designed:
- Goal is unambiguous (optimize `merge_ordered` for sorted keys).
- Environment is real, builds, and runs.
- Verifier is fair (correctness + speedup, sensible tolerances, 20 tests covering a realistic distribution).
- A real expert-developer fix exists, is small, and was the intended target.
- The hidden tests *are* discoverable (`/tests/gso_test_*.py` is a normal directory). The instruction's "do not overoptimize for the specific inputs" is an explicit warning that the test surface is wider than the example.

The only mild fragility is that the discoverability of `/tests/` is implicit. A single-sentence hint would help, but the absence of the hint is consistent with GSO's design philosophy of testing under-specified, expert-developer-style problems.

### 4.2 Is it the agent capability bottleneck?

**Yes — overwhelmingly.** The 18 trajectories show a remarkably consistent set of capability gaps:

1. **Insufficient environment exploration.** 0/18 agents listed `/tests/` to discover the hidden test suite. The information was available; agents didn't go looking.
2. **Insufficient codebase comprehension before editing.** Agents reached for `libjoin.{inner,left,outer}_join_indexer` based on its name, without reading its semantics or callers. The cython source even contains a comment hinting at the duplicate-keys constraint, but agents didn't trace the call graph.
3. **Architecturally local thinking.** 18/18 agents edited only `pandas/core/reshape/merge.py`. The reference solution requires coordinated edits across `merge.py`, `indexes/base.py`, and `groupby/generic.py`. Agents didn't realize that an indexer-shape contract change ripples to consumers.
4. **Self-validation that systematically misses duplicates.** When agents wrote their own duplicate-key tests, they used symmetric or one-sided patterns where libjoin's output coincidentally matched the cross-product. Run e4e7fc03 even returned identical results for all four join types and didn't flag it as a smell.
5. **One-shot commits.** No agent iterated more than 1–2 times after a passing self-test. The "wrote patch → ran toy benchmark → declared 70–250× speedup → done" loop is the modal trajectory.
6. **Confirmation bias.** Agents who ran the in-repo `test_merge_ordered.py` (20 small tests, all passed) used the green result as license to commit, ignoring that those tests don't probe the dup_monotonic stress case.

### 4.3 Final answer

**The task is high quality.** Failures are 95% agent capability bottlenecks, with one minor task-side issue (implicit `/tests/` discoverability) that is consistent with GSO's design intent of evaluating agents on under-specified expert-engineer tasks.

The single most diagnostic finding from this inspection is:

> **18/18 agents wrote one patch in one file based on the visible example, declared 70–250× speedup, and shipped. None of them inspected the hidden test files (which were on the filesystem), and none of them edited beyond `pandas/core/reshape/merge.py` even though the reference solution requires three coordinated file changes.**

This task should remain in the benchmark. It cleanly separates frontier agents from expert pandas developers, and the failure mode — insufficient exploration + over-confidence in toy validation + architecturally-local thinking — is the correct thing to be measuring.

**Recommendation:** Keep the task as Accept. Optionally add one-line instruction enrichment (Fix B above) if the benchmark wants to slightly soften the discoverability gap. Do not modify the verifier or hidden test suite.

---

## 5. Files in this directory

- `_task_instruction.md` — verbatim instruction shown to the agent
- `_task_test.sh` — verifier's test harness (the script that compares pre/post patch)
- `_task_solve.sh` — reference solution wrapped as the oracle apply-patch script (contains the upstream pandas #56115 patch)
- `_task_task.toml` — task config (timeouts, resource limits)
- `_task_Dockerfile` — image construction
- `task_inspection.md` — this file
