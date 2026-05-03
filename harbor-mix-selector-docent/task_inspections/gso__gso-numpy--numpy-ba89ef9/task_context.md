# Task Context — `gso/gso-numpy--numpy-ba89ef9`

## What the agent must do
- Optimize the runtime of a `<test_script>` whose hot inner loop is `np.add.at(res_copy, indices, vals)` — the unbuffered ufunc `at` method, called with 1M random indices into a length-1000 destination of float64.
- Constraints from the prompt (`task.instruction`):
  - Edit non-test files in `/workspace/numpy__numpy` to make the test_script faster.
  - Preserve functional equivalence with the original implementation.
  - "Do not overoptimize for just the specific inputs in <test_script>. Make general performance improvements for the usage scenario shown."
  - Build the repo with the snippet provided (`uv pip install . --reinstall` ladder of fallbacks) before measuring.

## Reference (oracle) solution (`task.solve_sh`)
- Adds an `At` benchmark in `benchmarks/benchmarks/bench_ufunc.py` (cosmetic, not strictly needed).
- Tweaks `numpy/core/src/umath/loops_arithm_fp.dispatch.c.src` to add an explicit small-`dimensions[0]` cutoff before falling into the SIMD path: `dimensions[0] < @count@ || !run_binary_simd_…` (count = 4 for FLOAT, 2 for DOUBLE).
- The big change is in `numpy/core/src/umath/ufunc_object.c`: it splits `ufunc_at` into a slow path and a new fast path `ufunc_at__fast_iter`, which avoids the per-element `NpyIter` buffered loop when the operands are simple/contiguous and use a strided loop instead. This is what produces the ~8× speedup on Test 0 referenced in the audit (~0.08s → ~0.01s).

The reward signal is **relative**: GSO rebuilds with the agent's patch, runs 20 hidden timing tests, then rebuilds with the *oracle commit* and runs the same tests. A helper (`/tests/gso_evaluate.py --instance-id numpy__numpy-ba89ef9`) decides `opt_commit: True/False` based on whether the agent matches the oracle's speedup pattern across the 20 tests, and writes `reward: 0` or `reward: 1`.

## Verifier flow (`task.test_sh`)
1. Save the agent's working tree as `/tmp/patch.diff` (binary blobs stripped).
2. `git reset --hard HEAD` — discards the agent's edits in the live tree.
3. `/tests/eval.sh` re-applies the patch, rebuilds, runs 20 functional tests (`>>>>> Tests Passed`) plus per-test timing blocks (`>>>>> Test K \n Execution time: …`). Then it rebuilds at the oracle commit and times again. The two timing sections appear as `>>>>> End Patch Output` (agent) and `>>>>> End Commit Output` (oracle).
4. `gso_evaluate.py` reads the combined log, writes `reward.txt` and `result.json` containing `{"opt_commit": bool, "reward": 0/1}`.

## Distribution of provided runs
- 18 runs total: 6 success / 12 failure (33% pass rate at face value).
- Per (agent, model):
  - claude-code / claude-opus-4-6: 1/3
  - codex / gpt-5.4: 1/3
  - terminus-2 / gpt-5.4: 3/3
  - terminus-2 / claude-opus-4-6: 0/3
  - gemini-cli / gemini-3.1-pro-preview: 1/3
  - terminus-2 / gemini-3.1-pro-preview: 0/3

## Key files in this directory
- `run_ids.json` — manifest of the 18 trajectories.
- `task_context.md` — this file.
- `01_query.py` — DQL helpers (kept for reference, all queries actually run via `mcp__plugin_docent_docent__execute_dql`).
- `02_analyze_runs.py` — `client.read` script that fans out per-trajectory structured analysis.
- `03_synthesize.py` — local script that aggregates the JSON results into the verdict tables.
- `all_results.json` — raw structured analyses for all 18 runs.
- `task_inspection.md` — final write-up.
