# Task Inspection: `gso/gso-huggingface--transformers-d51b589`

## Verdict

**Task quality:** **Reject unless fixed.** The task is solvable and the one successful trajectory proves that a capable agent can infer a high-performance XLNet attention optimization. But as an evaluation item, it is too fragile as written: the prompt silently uses old XLNet `input_mask` semantics in a misleading way, the verifier sometimes times out before patch evaluation, and the correctness check enforces near bitwise equality through an absolute `1e-05` checksum on huge float32 logits.

**Primary observed bottleneck:** **Mixed, but leaning agent capability under a flawed task.** Most agents found the right file and hotspots, then failed because they treated "mathematically close" PyTorch rewrites as functionally equivalent or misunderstood the old `input_mask=1` semantics. That is an agent capability/verification bottleneck. The task itself, however, makes that bottleneck less meaningful because it rewards a strange diagonal-attention edge case while the prompt calls the mask `attention_mask`.

The single most valuable answer: **the 17 failures are not mostly because agents cannot find XLNet attention; they can. They fail because the task requires exact preservation of old XLNet mask semantics and float32 operation order, and most agents optimize by replacing GELU/einsum/masking with faster but numerically non-identical operations.** I would not accept this task unchanged.

## Methodology

No sampling. I exported all 18 runs, including the missing `d7d0c912` run discovered from the collection query. Raw evidence is in `trajectories/`, `test_stdout/`, `metadata_*.json`, and `run_summaries.json`.

I used three subagents for disjoint run groups:

- Runs 01-06: claude-code/opus and terminus-2/opus.
- Runs 07-12: codex/gpt-5.4 and terminus-2/gpt-5.4.
- Runs 13-18: gemini-cli/gemini and terminus-2/gemini.

I reconciled their findings against `task_files/solve.sh` and verifier stdout.

## What The Task Actually Tests

The prompt appears to ask for general XLNet inference speedup, but the actual workload is unusual:

```python
attention_mask = torch.ones_like(input_ids)
inputs = {"input_ids": input_ids, "input_mask": attention_mask}
```

In this XLNet version, `input_mask=1` means "masked", not "valid". So all tokens are masked and the old code leaves only the self/diagonal path effectively usable. The successful solution recognizes this and optimizes the corresponding attention layout/diagonal computation without changing outputs.

The oracle patch keeps arithmetic semantics close to the original but changes attention score layout:

```python
ac = torch.einsum("ibnd,jbnd->bnij", q_head + self.r_w_bias, k_head_h)
bd = torch.einsum("ibnd,jbnd->bnij", q_head + self.r_r_bias, k_head_r)
attn_prob = F.softmax(attn_score, dim=3)
attn_vec = torch.einsum("bnij,jbnd->ibnd", attn_prob, v_head_h)
```

The verifier checks shape and a strict `logits_sum` checksum. Hidden tests use the same style, e.g. failures show:

```text
AssertionError: logits_sum differs: -3512301384.484338 vs -3512301896.811724 with tolerance 1e-05
```

## Question 1: How Close Were Agents?

| Band | Count | Runs | Notes |
| --- | ---: | --- | --- |
| Success | 1 | 07 | Exact diagonal/self-only XLNet fast path; reward 1. |
| Very close but numerically rejected | 11 | 02, 04, 05, 06, 08, 13, 14, 16, 17, 18 plus parts of 03 | Faster, shape-correct, but hidden checksum differs. |
| Semantic mask break | 2 | 11, 12 | Changed mask meaning; huge output drift. |
| Timeout / incomplete verifier | 3 | 01, 09, 15 | Verifier did not produce a clean post-patch verdict. |
| Empty patch | 1 | 10 | Reverted after local regressions; patch size 0. |

The agents were usually close in search space. Nearly all inspected `transformers/modeling_xlnet.py` and identified `gelu`, `rel_shift`, `rel_attn_core`, softmax, `einsum`, and masking as bottlenecks. But only run 07 converted that insight into a patch that was both fast and verifier-equivalent.

## Question 2: Performance Variation And Failure Roots

| Agent / model | Pass | Fail | Pattern |
| --- | ---: | ---: | --- |
| claude-code / claude-opus-4-6 | 0 | 3 | Found XLNet hotspots; one timeout, two numeric failures. |
| terminus-2 / claude-opus-4-6 | 0 | 3 | Aggressive local speedups, strict-checksum failures, artifact pollution. |
| codex / gpt-5.4 | 1 | 2 | One exact diagonal fast path; one numeric near miss; one incomplete dirty verifier run. |
| terminus-2 / gpt-5.4 | 0 | 3 | Empty patch or wrong mask semantics. |
| gemini-cli / gemini-3.1-pro-preview | 0 | 3 | Correct hotspots, numeric failures or timeout. |
| terminus-2 / gemini-3.1-pro-preview | 0 | 3 | Correct hotspots, numeric failures, messy finalization. |

### Surface Reasons

**Numerical equivalence failures dominate.** Typical examples:

- Run 02: `-3512301384.484338` expected vs `-3512301640.648031` produced.
- Run 04 and 08: hidden `gso_test_1.py` expected `-795188.75` vs produced `-795188.1875`.
- Runs 05, 06, 13, 14, 16, 18: expected `-3512301384.484338` vs produced `-3512301896.811724`.
- Run 17: expected `-3512301384.484338` vs produced `-3512301640.648031`.

**Semantic mask failures** are clearer:

- Run 11 produced `-2514655486.605321`.
- Run 12 produced `-5372994016.928238`.

Both changed how the all-ones `input_mask` affects attention.

**Verifier/operational failures**:

- Run 01 timed out during `/tests/gso_test_3.py` before patch evaluation.
- Run 15 timed out during baseline `/tests/gso_test_0.py` before patch evaluation.
- Run 09's visible log ends during reinstall with no final `opt_commit` line; the submitted diff was contaminated by generated artifacts.
- Run 10 submitted `Patch size: 0 bytes`.

### Root Causes

The dominant root cause is **insufficient exactness discipline for ML performance work**. Agents repeatedly replaced manual GELU with `F.gelu(approximate="tanh")`, replaced `einsum` with `matmul`/`bmm`, changed in-place accumulation, or adjusted thread/mask handling. Those are plausible optimizations, but they change float32 operation order or semantics enough to fail the task's strict absolute checksum.

The second root cause is **misunderstanding old XLNet mask semantics**. Run 12 is the clearest: it skipped mask construction because `input_mask` was all ones, assuming that meant all tokens valid. In this code, it means all tokens masked.

The third root cause is **local validation mismatch**. Several agents generated references under patched code, accepted relative closeness, or dismissed checksum changes as randomness. The prompt's `random.random()` multiplier likely encouraged that mistake, although the verifier seeds/reset flow makes it deterministic.

## Question 3: Concrete Expected Vs Produced Behavior

Expected behavior is not merely faster output with the same shape. The verifier expects the original checksum under controlled seeds:

```python
ref_sum = float(ref_result["logits_sum"])
curr_sum = float(current_result["logits_sum"])
tol = 1e-05
assert abs(ref_sum - curr_sum) < tol
```

Successful run 07 did this by recognizing the diagonal/self-only case and preserving the checksum:

```text
Before: 75.203577s
After: 13.521942s
Output sum unchanged: -3510056960.0
Verifier: opt_commit: True, reward: 1
```

Failing agents often produced locally faster but non-equivalent outputs:

```text
Run 08, hidden test 1:
expected -795188.75
produced -795188.1875
```

That looks tiny by ML relative-error standards, but it fails the verifier.

Wrong-mask examples are not tiny:

```text
Run 12:
expected -3512301384.484338
produced -5372994016.928238
```

That is a real semantic break caused by interpreting `input_mask` like a modern attention mask.

## Question 4: Task Self-Containment

Can a super-capable agent solve it? **Yes.** Run 07 proves it. The target file is discoverable, the prompt provides the timing/equivalence script, and `modeling_xlnet.py` exposes the old `input_mask` behavior.

Can agents infer the hidden expectations? **Partly.** They can infer:

- the task is XLNet-specific,
- `rel_attn_core` and `softmax` are the hot path,
- the checksum tolerance is strict,
- preserving old mask semantics matters.

But the prompt makes the core semantic clue unnecessarily confusing by naming the all-ones mask `attention_mask` and then passing it as `input_mask`. In modern Transformers usage, all-ones attention masks usually mean all tokens are valid. Here, all ones means all tokens are masked. That is discoverable from source, but the task is testing an API-semantic trap as much as performance reasoning.

Hidden tests appear aligned with the prompt's XLNet workload, but the equivalence criterion is harsher than normal ML functional equivalence and the occasional pre-patch timeout is a real infrastructure problem.

## Question 5: Fixes

**Required fix 1: clarify the mask semantics.** Add a sentence such as:

```text
In this old XLNet implementation, `input_mask` uses 1 for masked/padding positions. Preserve that behavior exactly; do not reinterpret it as modern all-valid `attention_mask` semantics.
```

This does not reveal the oracle layout trick. It makes the task self-contained rather than reliant on noticing a naming trap.

**Required fix 2: make the benchmark reflect a meaningful usage scenario, or explicitly embrace the edge case.** If the intended workload is normal all-valid inference, pass `attention_mask` correctly or use `input_mask=torch.zeros_like(input_ids)`. If the intended workload is diagonal/all-masked XLNet attention, say so. Right now it straddles both and rewards optimizing a suspicious corner.

**Required fix 3: strengthen and modernize equivalence.** Instead of a single absolute `logits_sum` tolerance of `1e-05`, compare the full output tensor with an ML-appropriate `torch.testing.assert_close` tolerance, plus shape and maybe top-k stability. If exact arithmetic is truly required, state that explicitly: "The evaluator requires near bit-for-bit output preservation; kernel substitutions that alter floating-point order may fail."

**Required fix 4: improve verifier robustness.** Baseline/pre-patch timeouts in runs 01 and 15 mean some failures did not evaluate the submitted patch at all. Increase verifier budget, reduce repetitions, or avoid timing the unoptimized baseline in a way that can consume the whole evaluation.

**Recommended fix 5: exclude common workspace artifacts.** Several patches included `.bak` files, helper scripts, generated `gso_*.json`, or environment debris. The prompt asks agents to create `/workspace/test_opt.py`; the harness should either exclude these reliably or direct agents to create them outside the repo.

## Final Decision

**Observed failures:** mostly agent capability and validation failures once the task is accepted on its own terms.

**Task quality:** reject unchanged. A good hard optimization task should expose capability bottlenecks cleanly. This one does expose them, but it also mixes a misleading mask setup, overly strict checksum semantics, and occasional verifier instability. With the fixes above, it could become a strong hard XLNet optimization benchmark. As-is, I would not accept it.
