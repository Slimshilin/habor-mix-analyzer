# Summary: claude-opus-4-6 failures on crustbench/genetic-neural-network-for-simple-control

All 6 runs ended in `AgentTimeoutError` after the 1800s budget. Across all 6, the implementation was *nearly* correct — typically 10/11 test binaries passing — and the agent timed out trying to verify the 11th test (`test_full_run` containing `testNNRun`, a 50,000-generation genetic-NN simulation).

## Where time was lost (consistent pattern across all 6 runs)

| Phase | Cost (claude-code) | Cost (terminus-2) |
|---|---|---|
| Read C source + interfaces (13 files each side) | ~50% of messages | ~60% of messages (more thorough surveys) |
| First build + fix borrow-checker errors | 5-10% | 5-10% |
| Per-binary test verification + fixes | 15-25% | 15-25% |
| Waiting on test_full_run testNNRun | 10-20% (truncated by timeout) | 20%+ (4+ minutes of polling) |

## Common bottlenecks (all 6 runs)

1. **Same three compile errors every run**:
   - `quickSort(fit, &mut array_more, array_more.len() as i32)` — E0502 (borrow `len()` on already-mut-borrowed vec).
   - `quickSort(fit, &mut array_less, array_less.len() as i32)` — same.
   - `selectInputNNFunction(&mut system_nn.input_sys, system_nn)` — E0499 (double mut borrow).

2. **Same two runtime bugs every run**:
   - `population.rs::createInputPop`: `max[..cols].to_vec()` panics when test passes `min`/`max` of length 3 with `size=[2,9]`. Real fix is to pad with zeros (every run eventually figures this out).
   - `neural_network.rs::deNormalizationProcess`: index out of bounds because the test uses `layerNumber=5` with `neuronsSize=[1,5,5,5,5,1]` (6 elements), causing the last layer to be sized 5 instead of 1, but `denormalizationMatrix` only has 1 element. Two valid fixes: (a) treat `layerNumber = max(declared, neuronsSize.len())` (run c7f27a2f) or (b) allocate normalization/denormalization with neuronsSize[0]/[layerNumber-1] sizes and pad (runs 98fd3d05, 09a6112d).

3. **`tanh(5*x)` vs `tanh(x)*5`** — only 2/6 runs hit this (the C source says `tanh(5*x)` but tests expect `tanh(x)*5`).

4. **Long testNNRun**: 50,000-generation NN simulation. testPIDRun (the easier sibling) was observed at ~85s in run 10693755 and ~85s in run c9458e1e. testNNRun was NEVER observed to complete in any of the 6 runs. terminus-2 runs waited 3-4 minutes; claude-code runs hit timeout while submitting the test_full_run command at the very end.

## Is this a claude-opus-4-6-specific weakness?

Not specifically — opus-4-6 actually does the transpilation reasonably well (all 6 runs converge to ~10/11 passing). The weakness is more methodological:

- Both agents (claude-code and terminus-2) **read all 13 C source files thoroughly before writing**. This burns most of the 1800s budget.
- They write all 13 interfaces before first build, then debug after. This is sensible but leaves no margin if the long `test_full_run` is needed for validation.
- All claude-code runs end with the agent **mid-final-test-invocation** (cargo test --release --bin test_full_run is the last command).
- All terminus-2 runs end **without ever calling `mark_task_complete`** — even when 10/11 tests pass, the agent keeps trying to observe testNNRun. terminus-2 cannot succeed without explicit completion.

## IMPORTANT: agent overhead vs cargo runtime

**The timeouts are ~70% agent reasoning + ~30% legitimately slow test_full_run.**

- Cold `cargo build --release` (with rand + getrandom + libc downloads + compile): ~1-2 min observed once per run. Not the bottleneck.
- Incremental rebuilds: 0.02s-6.11s. Not the bottleneck.
- All non-`test_full_run` test binaries: <1s each, total ~5s.
- `test_full_run::testPIDRun`: ~85s consistently.
- `test_full_run::testNNRun`: never observed to finish in 6 runs. Likely 5-15+ minutes given testPIDRun is ~85s and NN does 10x more generations + more compute per generation.

The agent strategy that fails: implement everything → build → fix → run all binaries one-at-a-time → finally test_full_run. By the time the agent gets to test_full_run, only 200-400s remain. testNNRun needs more.

A better strategy would be: implement minimally → test_full_run early → use it as the diagnostic loop. But neither agent did this. Both wanted to verify each interface incrementally before facing the long test.

## Key file paths
- Per-run notes: `/home/shilin/T-Bench/habor-mix-analyzer/harbor-mix-selector-docent/task_inspections/crustbench__genetic-neural-network-for-simple-control/trajectory_notes/{10693755,c9458e1e,98fd3d05,c7f27a2f,8743bf39,09a6112d}.md`
