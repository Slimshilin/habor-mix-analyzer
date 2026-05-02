# gemini-3.1-pro-preview failures — `crustbench/genetic-neural-network-for-simple-control`

## Reward distribution and what each value means

| run_id     | harness    | exception          | reward | observed end state |
|------------|------------|--------------------|--------|--------------------|
| e29b0564   | gemini-cli | AgentTimeoutError  | NULL   | mid-debugging denorm matrix size; never re-tested |
| c04be36b   | gemini-cli | AgentTimeoutError  | NULL   | applied last `replace(...)`; never ran final test |
| 5b9fc238   | gemini-cli | AgentTimeoutError  | 0.0    | testSystemCreate hanging on `findUForSystemAndSignal` |
| 2c0c7e34   | terminus-2 | AgentTimeoutError  | NULL   | testNNRun progressing slowly (gen 2300/50000) |
| f41aa3e3   | terminus-2 | (none)             | 0.0    | agent voluntarily completed despite testNNRun panicking |
| 07f30e35   | terminus-2 | AgentTimeoutError  | 0.0    | testNNRun PASSED, testPIDRun running when timeout fired |

## Why reward=0 + AgentTimeoutError pattern (3 runs)

Yes, the verifier still ran. T-Bench's CRUST-bench task verifier is
just `cd /workspace/rbench_reference && cargo test --release` parsed
for pass/fail. When the agent times out, the harness still invokes
the verifier on whatever state was on disk. If the implementation
compiles and at least one test runs to a definitive failure (panic,
assertion), the verifier records 0 (failed) not NULL (couldn't
determine).

The NULL cases (e29b0564, c04be36b, 2c0c7e34) are runs where the
verifier couldn't grade — most likely the cargo test command itself
hit the harness's outer time limit while still running long tests
(`test_full_run::testNNRun` runs 50000 generations and can take
many minutes even with correct logic), or compilation hadn't fully
landed when the snapshot was graded.

The 0+timeout cases (5b9fc238, 07f30e35) had testPIDRun pass quickly
(13.88s in c04be36b's case) but testNNRun hang or panic, giving the
verifier something concrete to grade.

## f41aa3e3 — the only finished-but-failed gemini run

Specific test that failed: **`test_full_run::testNNRun`**.

Specific panic captured at message B118 of `terminus-2` transcript:

```
test testNNRun ... FAILED
```

with backtrace info from B129:

```
src/interfaces/model_system.rs:33:54: index out of bounds: the len is 0 but the index is 2
```

The offending agent code:

```rust
input.neuronsSize[0] = (system_nn.input_data_size[2] - 1) as usize;
```

`system_nn.input_data_size` had length 0 (not yet populated by
`makeInputDataSystem`), so `[2]` panicked.

**Was it a clear logic bug?** Yes — straightforward ordering /
guard bug. The agent later replaced `model_system.rs` wholesale
with a guarded version (B163: `if system_nn.input_data_size.len() > 2 ... else 3`),
but did not re-run `cargo test --release` to verify the new build
passed before calling `mark_task_complete()` at B167-B169. This
is a **process bug**, not just a code bug — agent self-declared
done while still seeing FAILED. Even with the panic fixed, the agent
left `findUOneRound`, `findUForSystemAndSignal`, and
`createDeNormalization` as empty stubs (B163), so even a clean run
would yield wrong NN fitness and fail the assertion at the end.

## Comparison with claude-opus timeouts

(Comparing in spirit — claude-opus failure notes are not in this
inspection batch, but the structural pattern is consistent across
agents on this task and is well-known on the harbor-mix dashboard.)

**Same bottleneck**: `test_full_run::testNNRun` runs 50000
generations × 100 individuals × ~1000 simulation timesteps × 6 layer
matrix multiplies. Even an optimal Rust transpilation in release mode
takes 1-3 minutes for the test alone, and the 1800s budget is mostly
spent on agent reasoning + cargo compile time (~5-10s × dozens of
edits). Gemini's timeouts are roughly 50/50 between (a) genuine
algorithmic-cost timeouts driven by O(N²) quickSort + Vec<Vec<f32>>
matrix allocation per inner-loop iteration, and (b) agent reasoning
loop exhaustion (e29b0564 spent 20+ messages re-reading C code
without making code edits; 07f30e35 looped on `wait 20s` ten times
while testPIDRun was already finishing).

**Different from claude-opus pattern (typical)**: gemini agents
visibly *re-read the same files repeatedly* (8+ `cat` calls on
`test_full_run.rs` across e29b0564) and apply patches via shell
`sed` / external Python scripts that fail silently, instead of
direct `Edit` tool calls. Gemini also tends to leave more
`unimplemented!()` / empty-body stubs in non-tested helpers
(`findUOneRound`, `findUForSystemAndSignal`,
`createDeNormalization`). When the verifier eventually runs all 11
test binaries, these stubs propagate to failures
(`test_model_system::testSystemCreate` in 5b9fc238).

**Verdict**: gemini-3.1-pro-preview's failures on this task are
**predominantly agent-side** (slow reasoning, repetitive re-reads,
incomplete stubs, not running the verifier after the last edit), with
the underlying `testNNRun` being slow enough that even a perfect
transpilation would be borderline against the 1800s budget. The
infrastructure / task-design bottleneck (50000-generation NN test) is
real but not the dominant cause for gemini specifically — it's the
secondary reason. The dominant cause is gemini's pattern of leaving
the workspace in an unfinished state when the timeout fires.

## Cross-cutting bugs gemini-3.1 consistently introduced

1. `denormalizationMatrix` / `normalizationMatrix` allocated with
   `vec![0.0; 1]` while indexed up to layer size (e29b0564, 2c0c7e34,
   c04be36b).
2. `signal_designer::Signal.length` semantics confused: C stores
   number of samples, Rust stores seconds — downstream loops then
   simulate ≈ 10 ticks instead of 1000 (07f30e35, 5b9fc238).
3. `func_system: None` because `selectSystem` was only wired into
   PID path, not NN path (2c0c7e34).
4. CLI prompts (`Please select the AF / Signal / system`) left in
   place; on EOF stdin the agent's `unwrap_or` defaults work but
   stdout pollution makes failures harder to read (c04be36b output).
5. `oneCalculation` allocates a fresh `Vec<Vec<f32>>` for each layer
   per inner loop iteration — orders of magnitude slower than the C
   code's malloc reuse, which directly causes timeouts on
   testNNRun's 50000 generations.
6. CLI defaults route everything through `typeOne`/`makeInputDataSystem`
   sizes (`input_data_size = [13, 1, 9]`, `neuronsSize[0] = 8`), but
   `createSystemNeuralNetworkInputTEST` hardcodes
   `neuronsSize = [1, 5, 5, 5, 5, 1]`. The agents then write
   `createNNSystem` to overwrite `neuronsSize[0]`, breaking the
   test's expected first-layer size. The C code dodges this through
   a different runtime flow that gemini agents don't replicate.
