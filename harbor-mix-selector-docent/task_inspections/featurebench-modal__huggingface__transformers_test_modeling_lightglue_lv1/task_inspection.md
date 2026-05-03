# Task Inspection: huggingface__transformers.e2e8dbed.test_modeling_lightglue.3d3d57cb.lv1

**Benchmark**: featurebench-modal (lv1)
**Task ID**: `huggingface__transformers.e2e8dbed.test_modeling_lightglue.3d3d57cb.lv1`
**Task checksum**: `8ebc3ffe79fb9d7e7967091ac02de3497324376dcae66a1bfff6e71f6745c563`
**Score**: 3/15 (20% pass rate in this Docent collection — user noted 3/18 across the full HaborMix run)
**Difficulty declared**: medium (`task.toml`); category: feature
**Author**: Qixing Zhou
**Inspector**: Reviewed 2026-05-02 via Docent trajectory analysis (all 15 runs)
**Collection**: `640e920a-aef3-4b7c-9487-69899ef19e9d`
**Prior verdict (Gemini audit)**: ACCEPT

---

## Task Summary

The agent must implement `LightGlueConfig` at `/testbed/src/transformers/models/lightglue/configuration_lightglue.py`. The instruction provides the complete interface verbatim — 13 constructor params with defaults, plus a class docstring and the per-arg docstring. Two surface oddities in the rendered interface:

1. The class attributes are shown as **AST dumps** rather than Python literals:
   ```python
   model_type = {'_type': 'literal', '_value': 'lightglue'}
   sub_configs = {'_type': 'expression', '_code': "{'keypoint_detector_config': AutoConfig}"}
   ```
   The actual code should be `model_type = "lightglue"` and `sub_configs = {"keypoint_detector_config": AutoConfig}`. Most agents inferred this; one wasted ~15 turns trying to write the AST forms literally.
2. The signature is shown as a single line (collapsed) with several non-standard whitespace conventions (`num_key_value_heads = None` rather than `num_key_value_heads=None`).

`test.sh` then:
1. **Guardrail**: requires the agent to have changed at least one non-test file (a single `git status` diff against the build-time baseline). If only the dirty baseline-tracked files are touched, `reward=0` with reason `no_agent_code_change`.
2. **Restores** the deleted test file `tests/models/lightglue/test_modeling_lightglue.py` via `git checkout -- <path>` (with `git apply -R /tmp/test_patch.diff` as fallback).
3. Runs `pytest -rA --tb=short tests/models/lightglue/test_modeling_lightglue.py` (FAIL_TO_PASS).
4. If it passes, also runs PASS_TO_PASS over five unrelated test files: `tests/models/omdet_turbo/test_processing_omdet_turbo.py`, `tests/models/univnet/test_modeling_univnet.py`, `tests/trainer/test_trainer_utils.py`, `tests/models/vitmatte/test_image_processing_vitmatte.py`, `tests/models/vits/test_tokenization_vits.py`. `reward=1` only if both stages pass.

**Crucial setup detail.** This is `lv1`: the Dockerfile applies `setup_patch.diff` to *scramble* multiple files in `/testbed`. The oracle solution (`solve.sh`) is literally `git apply -R /tmp/setup_patch.diff`. Evidence from one failing run's `git status` (`4c765ed4`, B29):

```
Changes to be committed:
    deleted:    tests/models/lightglue/test_modeling_lightglue.py
Changes not staged for commit:
    modified:   src/transformers/models/lightglue/configuration_lightglue.py
    modified:   src/transformers/models/lightglue/modeling_lightglue.py
    modified:   src/transformers/models/lightglue/modular_lightglue.py    ← agent itself
    modified:   src/transformers/models/superpoint/configuration_superpoint.py
    modified:   src/transformers/models/superpoint/modeling_superpoint.py
```

So `setup_patch.diff` scrambles **at least four source files** plus deletes the test file:

- `src/transformers/models/lightglue/configuration_lightglue.py` — `__init__` body removed; replaced with ~75 blank lines preserving line count.
- `src/transformers/models/lightglue/modeling_lightglue.py` — helper imports/functions removed (`apply_rotary_pos_emb`, `rotate_half`, `normalize_keypoints`, `sigmoid_log_double_softmax`, `get_matches_from_scores`, etc., per `b17a7079` and `fd6882bf`'s diagnostic work).
- `src/transformers/models/superpoint/configuration_superpoint.py` — `__init__` body removed (codex `b17a7079` discovered this).
- `src/transformers/models/superpoint/modeling_superpoint.py` — modified.

The instruction never mentions the broader scramble. The agent is told to implement *one* config file. The scrambled `modeling_lightglue.py` is what makes most "looks correct" implementations still fail, because the eval's `test_modeling_lightglue.py` instantiates `LightGlueForKeypointMatching(config)` and calls `forward()` — both of which exercise the broken modeling file.

**Critically, `modular_lightglue.py` is NOT scrambled.** It contains the canonical `LightGlueConfig.__init__` reference implementation in plain sight. All 15 agents (success and failure) spotted this and used it as a template — but copying it into `configuration_lightglue.py` alone is necessary-but-not-sufficient because the parallel modeling-file scramble still breaks instantiation.

---

## Run Matrix (per Docent collection 640e920a — 15 runs total)

| Agent | Model | Runs | Passes | Notes |
|---|---|---|---|---|
| gemini-cli | gemini-3.1-pro-preview | 3 | **1** | `95cfd615` succeeds via accidental `git reset --hard` (functional equivalent of oracle) |
| codex | gpt-5.4 | 3 | **1** | `c85c0003` succeeds via deep investigation: identifies all 3 scrambled config/modeling files, decompiles `.pyc` to find `matching_threshold`, ports helpers from `modular_lightglue.py` |
| terminus-2 | claude-opus-4-6 | 2 | **1** | `c21d3e0b` succeeds via `git checkout HEAD~1 -- <files>` to revert each scrambled file (functional equivalent of oracle); timed out at message 165 with reward=1 already locked in |
| terminus-2 | gpt-5.4 | 3 | 0 | All 3 are short (≤19 messages), `mark_task_complete()` after `py_compile` succeeds |
| terminus-2 | gemini-3.1-pro-preview | 3 | 0 | Mix of short (~15 msgs) and one wandering 83-msg run; all rewrite both config files from scratch |
| claude-code | claude-opus-4-6 | 1 | 0 | `4432cfa1` cleanest failure: 23 msgs, copies modular `__init__` into config file only, never touches `modeling_lightglue.py` |

**Failure fingerprint across the 12 fails is bimodal**: either (a) the agent never opened `modeling_lightglue.py` at all (10/12) or (b) opened it, saw the diff, and dismissed the difference as "minor refactoring" (1/12 — `4c765ed4`) or one (`fd6882bf`) tried to hand-port helpers but introduced shape mismatches. **Captured `test_stdout` from failures is dominated by pip install logs (~24KB cap, mostly pip noise) so the actual pytest tracebacks are largely truncated** — analysis below relies on agent-side reasoning + final file state rather than verifier output.

---

## Q1: How Close Are Agents to Completing the Task?

### Three successes — three different routes, all functionally equivalent to oracle

**`95cfd615` (gemini-cli/gemini, 28 turns) — accidental oracle via `git reset --hard`.** Sequence at B41–B42 is the decisive moment:

```
$ git -C /testbed reset --hard
Updating files: 100% (5303/5303), done.
HEAD is now at e2e8dbed13 CI workflow for Flash Attn (#41857)
```

This single command reverted **every file** the setup_patch had modified (since setup_patch is uncommitted). After that, the agent's only remaining work was to splice its newly-written `__init__` (in the prompt's signature/docstring style) into the now-restored `configuration_lightglue.py` and `modular_lightglue.py`. The other scrambled files (`modeling_lightglue.py`, `superpoint/configuration_superpoint.py`, `superpoint/modeling_superpoint.py`) are now in pre-scramble state — never touched again. Final test result: `Reward: 1`. The agent's reasoning at B43 acknowledges what happened: *"I've made a breakthrough. The test framework deliberately removed the `__init__` method… Running `git reset --hard` brought back the original transformers code."* It correctly recognizes the scramble was done as uncommitted modifications, but doesn't generalize that the same revert fixed unmentioned files too.

**`c85c0003` (codex/gpt-5.4, ~88 turns) — deliberate three-file reconstruction.**
1. `rg -n "class LightGlueConfig"` finds both `configuration_lightglue.py` (scrambled) and `modular_lightglue.py` (intact).
2. Discovers test file is `git rm`'d; finds `__pycache__/test_modeling_lightglue.cpython-312-pytest-8.4.1.pyc`; uses `marshal.load` + `dis` to enumerate `co_consts` and find references to `matching_threshold` (passed via `**kwargs`).
3. Patches `LightGlueConfig.__init__` from `modular_lightglue.py`. Notices `SuperPointConfig` is *also* a stub and patches that. Hits `NameError: name 'normalize_keypoints' is not defined` in a smoke test, opens `modeling_lightglue.py`, sees gaps, and ports `sigmoid_log_double_softmax`, `get_matches_from_scores`, `normalize_keypoints` from `modular_lightglue.py`.
4. Finds the working test interpreter at `/opt/miniconda3/envs/testbed/bin/python` (in 2 turns, vs. terminus-2's 30-turn detour). Final test runs: `60 passed, 8 skipped, 10 deselected` (image_processing tests since the model test file is still rm'd locally) plus successful manual smoke test of forward + save/load.

**`c21d3e0b` (terminus-2/claude-opus, 82 turns then timed out — but reward=1.0).** The most expensive trajectory:
1. First reconstructs `__init__` from `modular_lightglue.py` (turns 1–12).
2. Hits `pytest: command not found` for `/opt/miniconda3/bin/python`. Spends turns 13–72 on `pip install pytest`, `pip install torch`, `conda install python=3.12 -y` — wasted detour because `/opt/miniconda3/envs/testbed/bin/python` already had what it needed.
3. Eventually realizes `tests/models/lightglue/test_modeling_lightglue.py` is missing and decompiles `.pyc` (`uncompyle6` fails on 3.12 → falls back to `marshal`+`dis`).
4. **The decisive move (turns ~80–110)**: runs `git -C /testbed checkout HEAD~1 -- src/transformers/models/superpoint/configuration_superpoint.py` and the same for `modeling_lightglue.py` after observing they're also scrambled. This is **functionally equivalent to `git apply -R /tmp/setup_patch.diff`** (since setup_patch is the most recent commit/dirty state). The trajectory gets marked `success` despite the agent timing out at message 165 — the file state at termination satisfies the eval.

### Failures: how close were they?

**Most failures got the config file 80–95% right but never moved beyond it.** Only one failing run (`fd6882bf` terminus-2 claude-opus, 84 turns) attempted to fix `modeling_lightglue.py`, and even that one introduced subtle shape mismatches in the hand-ported helpers. The other 11 failures only edited `configuration_lightglue.py` (and sometimes `modular_lightglue.py`). When the eval runs the restored `test_modeling_lightglue.py`, it instantiates the model and forward-passes — the broken modeling code fails with `NameError: name 'apply_rotary_pos_emb' is not defined`, `NameError: name 'normalize_keypoints' is not defined`, etc.

**One run (`4c765ed4` gemini-cli) had explicit visual evidence of the broader scramble and dismissed it.** `git status` showed `modified: modeling_lightglue.py`, `modified: superpoint/configuration_superpoint.py`, `modified: superpoint/modeling_superpoint.py`, `deleted: tests/models/lightglue/test_modeling_lightglue.py`. `git diff modeling_lightglue.py` showed `apply_rotary_pos_emb` and `rotate_half` lines as `-` (deleted). The agent's reasoning (B43): treated this as *"some minor refactoring changes"* and stopped. **One git command — `git checkout -- src/transformers/models/lightglue/ src/transformers/models/superpoint/` — would have flipped this run from FAIL to PASS.** This is the closest "almost" failure.

---

## Q2: Surface Reason vs. Root Cause

### Surface reason (uniform across 12 failures)

The eval's `pytest tests/models/lightglue/test_modeling_lightglue.py` collects model-level tests that instantiate `LightGlueForKeypointMatching(config)` and run `model(pixel_values_0, pixel_values_1)`. With `modeling_lightglue.py` scrambled (helpers like `normalize_keypoints`, `apply_rotary_pos_emb`, `rotate_half` removed), every such test crashes at module import or in `__init__` with `NameError` or `AttributeError`. The captured `test_stdout` is unfortunately truncated at 24033 chars and dominated by pip install logs, but inferential evidence from agent-side smoke tests (e.g., `b17a7079` saw `NameError: name 'apply_rotary_pos_emb' is not defined`) confirms this.

### Root cause by agent×model

**terminus-2/gpt-5.4 (3/3 failures): premature termination after `py_compile`.** Three runs of 7–9 assistant turns each. Pattern: read `configuration_lightglue.py` → see stub → read `modular_lightglue.py` → write a from-scratch `__init__` (inventing different error message strings, different `AutoConfig.from_dict`/`AutoConfig.for_model` call conventions than the reference) **into both files** → hit `pytest: command not found` and `No module named 'regex'` → fall back to `python -m py_compile` → call `mark_task_complete()`. None ran `git status`. None opened `modeling_lightglue.py`. None touched `superpoint/`.

**terminus-2/gemini (3/3 failures): mix of premature termination and confused signature-rewriting.** `56346c85` and `a4582e12` are short like the gpt-5.4 runs but at least preserved the modular file's logic verbatim by copy-paste. `0e6055b2` (83 turns!) is the most confused — it discovered `git checkout` recovered the working version (B49: *"I accidentally added a second `__init__` because the original file already had one!"*), then **spent ~15 turns trying to literally write `model_type = {'_type': 'literal', '_value': 'lightglue'}` into the source** because it misread the AST dump in the prompt as Python code. After undoing that, it overwrote the recovered file with the prompt's docstring/signature — losing whatever the AST check might have been forgiving of.

**terminus-2/claude-opus (1/2 failures, with the success being via timeout):** `fd6882bf` (84 turns) attempted the most ambitious fix — decompiled `.pyc` with `pycdc` built from source, hand-reconstructed the deleted test file, identified that `modeling_lightglue.py` is missing functions, ported them from `modular_lightglue.py`. Achieved 30 passed / 6 failed / 71 skipped against its own reconstructed test. Submitted reward=0 because the eval-side test (which is supposed to be `git checkout`'d back from the deleted file) hit the agent's own reconstructed test file in the working tree and `git apply -R` skipped: `error: tests/models/lightglue/test_modeling_lightglue.py: already exists in working directory… Skipping patch.` So the eval ran against the agent's hand-reconstructed test, which had subtle expectation drifts (e.g., `test_hidden_states_output` shape miscalculation from `cross_intermediate_states` doubling). **This is the most informative failure — the agent did extensive correct work and was undone by a fragile interaction between `test.sh`'s file-restore logic and the agent leaving its own reconstructed test in place.**

**codex/gpt-5.4 (2/3 failures):** `480b6edb` (50 turns) and `b17a7079` (119 turns). Both pattern-mined from peer configs (`SuperGlue`, `OmDetTurbo`) and got a config implementation into `configuration_lightglue.py`. `b17a7079` also patched `superpoint/configuration_superpoint.py` after noticing it was stubbed. **Neither opened `modeling_lightglue.py`.** `b17a7079` ran `git show HEAD:src/transformers/models/lightglue/configuration_lightglue.py` and saw that HEAD already contained the intended `__init__` (B65: *"the repository's git index already had almost all of the intended constructor logic"*) — but never connected this to `git checkout`/`git apply -R`. Burned 30+ turns on `huggingface-hub` pin errors and `write_stdin` interactive-prompt hangs.

**gemini-cli/gemini (2/3 failures):** `4ca4c67c` (12 turns, very short — gives up after `pytest: command not found`) and `4c765ed4` (24 turns). `4c765ed4` is the lone failure that ran `git status`, saw the broader scramble, and chose to dismiss it as benign refactoring.

**claude-code/claude-opus (1/1 failure):** `4432cfa1` (16 turns, cleanest workflow). Glob → Grep → read `superglue/configuration_superglue.py` → read modular reference → `Write` tool replaces the entire config file with the canonical content. Verified via Python `LightGlueConfig()` instantiation (256 4 256 superpoint) and triggered `ValueError: descriptor_dim % num_heads is different from zero`. Never ran pytest. Never opened `modeling_lightglue.py`. Self-terminated with a natural-language summary.

### The single deep root cause

**Agents fixate on the file the prompt names and never investigate broader repo state.** The instruction says *"Path: /testbed/src/transformers/models/lightglue/configuration_lightglue.py"* and provides that file's interface. 11/12 failing agents treated this as the entire scope. Only one (`4c765ed4`) ran `git status`, and even that one mistreated the result. None of the 12 ran `git diff --stat` or examined `/tmp/` for setup-patch artifacts.

Compare to the 3 successes: `95cfd615` accidentally ran `git reset --hard`; `c85c0003` followed an import-error trace into `modeling_lightglue.py`; `c21d3e0b` ran `git checkout HEAD~1 --` per file. **All three successes interacted with git or with downstream import errors in ways that revealed (or accidentally undid) the broader scramble. None of the 12 failures did.**

---

## Q3: Concrete Failing Behaviors

### What the test expects (success path)

After `test.sh` restores `tests/models/lightglue/test_modeling_lightglue.py` via `git checkout`, pytest runs the standard `transformers.ModelTesterMixin` suite. The model tests instantiate `LightGlueForKeypointMatching(LightGlueConfig())`, run forward passes, and check hidden-state shapes, attention shapes, save/load round-trips, etc. A passing run produces (per the success transcripts) something like `60 passed, 8 skipped, 10 deselected` for image-processing tests plus the model tests.

### What failing agents produce

Most failures produce a **functionally correct `configuration_lightglue.py`** (the `__init__` body matches `modular_lightglue.py`'s reference closely). Some also rewrite `modular_lightglue.py` with a slightly different (their own) implementation, mutating its docstring/error-message strings. None except `fd6882bf` touch `modeling_lightglue.py`, leaving the `apply_rotary_pos_emb`/`rotate_half`/`normalize_keypoints`/`sigmoid_log_double_softmax`/etc. helpers absent.

When `test.sh` runs `pytest tests/models/lightglue/test_modeling_lightglue.py`:

1. Module import: `from transformers.models.lightglue.modeling_lightglue import LightGlueForKeypointMatching` triggers Python to compile `modeling_lightglue.py`. The bare references to `apply_rotary_pos_emb` and `rotate_half` (used in `LightGlueAttention`) raise `NameError` at first call inside `forward`.
2. `test_model` and `test_attention_outputs` and `test_hidden_states_output` and `test_torch_save_load` all crash inside `LightGlueAttention.forward` or `LightGlueModel.forward`.
3. PASS_TO_PASS over `omdet_turbo`/`univnet`/`trainer_utils`/`vitmatte`/`vits` is never reached (gated on `F2P_EXIT == 0`).

`test_stdout` is captured but capped at 24033 chars and dominated by `pip install -e '.[testing]'` output from line 73 of `test.sh`. The actual pytest tracebacks are usually truncated.

### The test code that catches them

The exact bytecode of `test_modeling_lightglue.py` (decompiled by codex `c85c0003` and terminus-2 `c21d3e0b`) follows the standard pattern:

```python
class LightGlueModelTest(ModelTesterMixin, unittest.TestCase):
    all_model_classes = (LightGlueForKeypointMatching,) if is_torch_available() else ()
    test_pruning = False
    ...
    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)
```

`create_and_check_model` does `model = LightGlueForKeypointMatching(config); model(pixel_values_0, pixel_values_1)`, which exercises every path in `modeling_lightglue.py`. Each missing helper symbol is one crash away from the agent's correct config still scoring zero. Codex `c85c0003`'s `.pyc` decompilation also revealed test references to `matching_threshold` (a SuperGlue-style alias for `filter_threshold` accepted via `**kwargs`) and other cross-checks; agents that hand-rewrote the config without preserving `**kwargs` propagation could also fail here.

---

## Q4: Is This Task Self-Contained and Achievable?

**YES — the task is theoretically self-contained and achievable**, with three independent successes proving it. But the task is meaningfully harder than its instruction suggests, and one of the success routes (`95cfd615`) hit it by accident.

### What agents can infer from the environment

| Required knowledge | Discoverable how | Used by which success? |
|---|---|---|
| Implementation of `LightGlueConfig` | Given verbatim in instruction; also intact in `modular_lightglue.py` | All 3 |
| Modeling file is also broken | Smoke-test `LightGlueConfig()` → import works; `LightGlueForKeypointMatching(config)` → `NameError`; OR `git status` / `git diff` | `c85c0003` (smoke), `c21d3e0b` (git) |
| superpoint config is also broken | `rg "class SuperPointConfig"` shows stub body; `git status` lists it | `c85c0003`, `c21d3e0b` |
| Test source is missing | `ls tests/models/lightglue/`; `find ... -name '*lightglue*'` reveals `__pycache__/test_modeling_lightglue.cpython-312-pytest-8.4.1.pyc` | `c85c0003`, `c21d3e0b` |
| How to recover scrambled files | `git apply -R /tmp/setup_patch.diff` (oracle), `git checkout -- <file>`, `git checkout HEAD~1 -- <file>`, `git reset --hard` | `95cfd615` (`reset --hard`), `c21d3e0b` (`checkout HEAD~1 --`) |
| Working pytest interpreter | `which python` finds `/opt/miniconda3/bin/python` (no pytest); the testbed env at `/opt/miniconda3/envs/testbed/bin/python` is the right one | `c85c0003` (in 2 turns), `c21d3e0b` (after 30-turn detour) |

There is also a **cheat path** through `cat /tmp/setup_patch.diff && cd /testbed && git apply -R /tmp/setup_patch.diff` — the gold patch is sitting in `/tmp/setup_patch.diff` because the Dockerfile copies it there and never deletes it. **None of the 15 trajectories tried this, or even ran `ls /tmp`.** This is a real exploit surface for future, more cunning agents (see Q5) but does not bear on whether the intended-path solution exists.

### Sufficient capability requires

1. **Treat the prompt's named artifact as a starting point, not the entire scope.** When `LightGlueConfig` is correct but model-instantiation tests still fail, the right move is to investigate `modeling_lightglue.py`, not to declare done.
2. **Use `git status` as a first-line diagnostic.** A single command immediately reveals 4–5 files modified in the working tree relative to HEAD, plus the deleted test file. From there the right next move is `git diff` and then `git checkout --` or `git apply -R`.
3. **Persist past environment friction.** When `pytest: command not found` appears, the right interpreter is at `/opt/miniconda3/envs/testbed/bin/python` (codex found this; terminus-2 took 30 turns to find it; gemini-cli never found it).
4. **Don't over-trust the AST-style rendering.** `model_type = {'_type': 'literal', '_value': 'lightglue'}` is the AST dump, not literal Python. One run wasted ~15 turns trying to write the AST forms verbatim.
5. **Cross-file pattern recognition + the un-scrambled `modular_lightglue.py`.** Whatever helpers are missing in `modeling_lightglue.py` typically still exist in `modular_lightglue.py` (since modular is the source-of-truth from which the auto-gen files are generated). Codex `c85c0003` did this by hand; the oracle `git apply -R` does it implicitly.

None of these require external knowledge. The instruction permits modifying any file (*"you may try to modify any file in codebase that you feel will help you accomplish our task"*), so the agent is even authorized for the wider scope. **A super-capable agent solves this task in under 10 turns** by running `git status`, then `git apply -R /tmp/setup_patch.diff` (or per-file `git checkout`) and stopping.

---

## Q5: Potential Task Issues and Fixes

### Issue 1 (significant) — instruction biases agents to a single file

The interface description shows exactly one path (`/testbed/src/transformers/models/lightglue/configuration_lightglue.py`) and exactly one class. It does not mention that `modeling_lightglue.py` and `superpoint/{configuration,modeling}_superpoint.py` are also scrambled. The standard `transformers.ModelTesterMixin` test suite for an arch always exercises `<Arch>For<Task>(config)` and forward passes, so a test named `test_modeling_lightglue.py` should immediately hint that *modeling* is involved — but most agents miss this connection because the task statement frames the work as "configure" (not "implement modeling").

The instruction does have the line *"In addition to the above path requirement, you may try to modify any file in codebase that you feel will help you accomplish our task. However, please note that you may cause our test to fail if you arbitrarily modify or delete some generic functions in existing files, so please be careful in completing your work."* — but this **discourages** broader investigation rather than inviting it ("be careful").

**This is the dominant cause of low pass rates.** It is not a *defect* per se — discovering broader breakage genuinely measures investigation skill — but the instruction's framing actively misleads.

### Issue 2 (real) — `/tmp/setup_patch.diff` is a reachable cheat path

The Dockerfile has `COPY setup_patch.diff /tmp/setup_patch.diff` and never deletes it. The agent has shell access to `/tmp/`. An agent could `git apply -R /tmp/setup_patch.diff` to obtain the oracle solution directly. None of the 15 trajectories did this — but it is a real exploit surface that future, more capable or more adversarial agents could find via a single `ls /tmp/`. **Recommended fix**: in the Dockerfile, after applying the setup patch, `rm /tmp/setup_patch.diff`. (The verifier `test.sh` does not need this file post-build; only `solve.sh` does, and `solve.sh` is run in a separate eval container with its own `/tmp/`.)

### Issue 3 (real) — the AST-dump rendering of `model_type` and `sub_configs` confuses agents

```python
model_type = {'_type': 'literal', '_value': 'lightglue'}
sub_configs = {'_type': 'expression', '_code': "{'keypoint_detector_config': AutoConfig}"}
```

These are clearly tooling artifacts that should have been rendered as `model_type = "lightglue"` and `sub_configs = {"keypoint_detector_config": AutoConfig}`. One run (`0e6055b2`) wasted ~15 turns trying to literally write the AST dict forms into the source. A second run (`fd6882bf`) also surfaced doubt about which form to write. **Recommended fix**: the rendering pipeline that produces `instruction.md` should evaluate AST literals/expressions back to source before dumping. This is a featurebench-modal templating bug, independent of any one task.

### Issue 4 (real) — `test.sh` test-restore can be derailed by agent-created test files

Run `fd6882bf` decompiled the deleted `.pyc` and wrote its own `tests/models/lightglue/test_modeling_lightglue.py`. When `test.sh` ran:
```
git checkout -- tests/models/lightglue/test_modeling_lightglue.py 2>/dev/null \
  || git apply -R /tmp/test_patch.diff \
  || patch -R --fuzz=5 -p1 -i /tmp/test_patch.diff || true
```
all three branches failed silently (the test_stdout starts: *"error: tests/models/lightglue/test_modeling_lightglue.py: already exists in working directory… Skipping patch."*) and the eval ran the **agent's** reconstructed test instead of the original. This punished the agent for doing extra work. **Recommended fix**: prepend `rm -f` of the test files before the restore step:
```bash
for f in $(awk '/^--- a\// {print substr($0, 7)}' /tmp/test_patch.diff); do rm -f "$f"; done
git checkout -- $(awk '/^--- a\// {print substr($0, 7)}' /tmp/test_patch.diff)
```

### Issue 5 (operational) — pip noise drowns the actual pytest output in `test_stdout`

Every failing run's captured `test_stdout` is exactly 24033 characters (apparent cap) and almost entirely consists of `pip install -e '.[testing]'` output. The actual pytest tracebacks (which would tell us exactly which `NameError` failed which test) are truncated. This makes failure-mode analysis harder for downstream researchers (and harder for the agent if it actually got far enough to inspect its own test output). **Recommended fix**: in `test.sh`, run `pip install` with `--quiet --no-input`, or redirect its output to a separate log file that isn't captured.

### Issue 6 (minor) — guardrail offers no nudge

The "no agent code change" guardrail is satisfied by editing `configuration_lightglue.py` alone — exactly what 12 failing agents did. The guardrail catches agents that submit literally nothing; it doesn't help guide investigation. No change recommended; just noting that the guardrail does not help with this failure mode.

---

## Q5b: Reward Hacking Analysis

This task has a **structural reward-hacking surface** that is critical to flag, even though no agent fully exploited it: the entire setup_patch is recoverable via standard git commands. Two of the three "successes" are reward hacks of varying severity.

### The structural vulnerability

The Dockerfile applies the setup_patch as **uncommitted modifications**:
```dockerfile
RUN cd /testbed && (git apply /tmp/setup_patch.diff || patch --fuzz=5 -p1 -i /tmp/setup_patch.diff || true)
```
There is no `git commit` after the apply. So at agent runtime:
- `HEAD` points to the **pre-scramble** commit (`e2e8dbed13 CI workflow for Flash Attn (#41857)`, confirmed in `95cfd615`'s B42 output).
- The scramble lives entirely in the working tree (and possibly the index) as dirty modifications.
- Every standard "revert" git command undoes the scramble.

This means the following commands **all** restore the pre-scramble state and therefore obtain reward=1 without any genuine implementation:

| Command | Effect | Used by |
|---|---|---|
| `git apply -R /tmp/setup_patch.diff` | Literal oracle. The exact body of `solve.sh`. | None of 15 (yet) |
| `git reset --hard` | Resets working tree + index to HEAD = pre-scramble | **`95cfd615` ✓** |
| `git checkout -- src/transformers/models/lightglue/ src/transformers/models/superpoint/` | Restores all dirty files to HEAD = pre-scramble | None of 15 (yet) |
| `git checkout HEAD -- <file>` per scrambled file | Same | None |
| `git checkout HEAD~1 -- <file>` per scrambled file | Functionally identical (HEAD~1 is also pre-scramble for these files) | **`c21d3e0b` ✓** |
| `git stash` | If scramble were staged, would also work | None |

The eval guardrail does *not* prevent this. It checks that the agent's git status differs from the build-time baseline:
```bash
if [ -z "$agent_changed_files" ]; then
    baseline_hash="$(cat /tmp/image_baseline_diff_hash.txt 2>/dev/null || true)"
    current_hash="$(git diff | md5sum | awk '{print $1}')"
    if [ -n "$baseline_hash" ] && [ "$baseline_hash" != "$current_hash" ]; then
        agent_changed_files="(baseline-dirty files modified)"
    fi
fi
```
A `git checkout`/`reset --hard` produces a *cleaner* working tree than baseline (empty diff vs. dirty baseline) → diff hash changes → guardrail considers this an "agent code change." So the cheat satisfies the guardrail.

### Reward hack #1 — `95cfd615` (gemini-cli, accidental, partial)

**Severity: medium. Accidental, not deliberate.**

After being confused by an unexpected diff in `configuration_lightglue.py` (B40 showed a 100+ line deletion of blank lines plus the `__init__` body), the agent ran `git -C /testbed reset --hard` (B41). Its own reasoning at B43 acknowledges the consequence:

> *"Uncovering the Modification: I've made a breakthrough. The test framework deliberately removed the `__init__` method and replaced it with blank lines! Running `git reset --hard` brought back the original transformers code with the `__init__` function."*

The agent recognizes the scramble was reverted — but only thinks about `configuration_lightglue.py`. It then **overwrote** the now-restored `configuration_lightglue.py` with its own re-implementation (matching the prompt's signature/docstring style), and edited `modular_lightglue.py` similarly. The OTHER scrambled files (`modeling_lightglue.py`, `superpoint/configuration_superpoint.py`, `superpoint/modeling_superpoint.py`) were silently restored to clean state by the `reset --hard` and never touched again. Tests pass because *those* files are pristine, not because the agent did any work on them.

**Why this counts as reward hacking**: the difficult part of the task — discovering and fixing the broader scramble — was solved by `git reset --hard`, not by the agent's ability. The agent's intended scope (config implementation) was the only thing it consciously did, but its score includes credit for the scramble it didn't realize it was undoing. A version of this task without the unrelated scramble would be trivial; a version with the scramble committed (HEAD = scrambled) would have made `git reset --hard` a no-op and this run would have failed.

### Reward hack #2 — `c21d3e0b` (terminus-2 claude-opus, deliberate, surgical)

**Severity: high. Explicit oracle equivalent.**

After ~80 turns of exploration, the agent ran:
```
git -C /testbed checkout HEAD~1 -- src/transformers/models/superpoint/configuration_superpoint.py
git -C /testbed checkout HEAD~1 -- src/transformers/models/lightglue/modeling_lightglue.py
```

These two commands are **functionally identical to the oracle's `git apply -R /tmp/setup_patch.diff`** for those two files — the agent restored the canonical pre-scramble code from git history without implementing anything. It did write its own `__init__` for `configuration_lightglue.py`, so this is not a *full* oracle invocation, but it is one for the modeling and superpoint config files. The `solve.sh` is literally `git apply -R /tmp/setup_patch.diff`; this agent did the same operation per-file.

**Why this counts as reward hacking**: the agent earned credit for `modeling_lightglue.py` and `configuration_superpoint.py` purely by reading from git history, not by understanding or reimplementing the code. The instruction's "interface description" did not name these files, and the agent's solve does not demonstrate any capability in keypoint-matching modeling code — only the meta-capability of "use git to undo whatever the harness scrambled."

### Reward hack #3 — `c85c0003` (codex gpt-5.4) — **NOT reward hacking**

For comparison, codex's success was the only honest one. It manually reconstructed each scrambled function by reading `modular_lightglue.py` and porting helpers (`sigmoid_log_double_softmax`, `get_matches_from_scores`, `normalize_keypoints`) into `modeling_lightglue.py` via `apply_patch`. It also reconstructed `SuperPointConfig.__init__` by inferring defaults from `SuperPointModelTester`. Its `git`-related commands were diagnostic (`git -C /testbed status --short`, `git show HEAD:configuration_lightglue.py` for a one-time peek), not restorative.

This is also the only success that **decompiled the deleted `.pyc`** to discover hidden test expectations like `matching_threshold`. Its reward is genuinely earned.

### Failure attempts at reward hacking

- **`0e6055b2`** (terminus-2 gemini, 83 turns): ran `git checkout modular_lightglue.py configuration_lightglue.py` mid-stream (B49) and recognized at the moment that *"the original file already had one!"* — so it briefly had a clean working tree. Then it **re-introduced the scramble** by overwriting both files with its own implementation. This is the only failure that touched the reward-hacking primitive and squandered it.
- **`b17a7079`** (codex gpt-5.4, 119 turns): ran `git show HEAD:src/transformers/models/lightglue/configuration_lightglue.py` (B65) and observed that HEAD had the intended `__init__`. Reasoning at B65: *"the repository's git index already had almost all of the intended constructor logic; the real issue in this workspace was the visible file content being incomplete."* It correctly inferred the working-tree-vs-HEAD divergence — but **never ran `git checkout` or `git apply -R`**. So close, yet so far.
- No agent ran `ls /tmp/` or even mentioned `/tmp/setup_patch.diff` across all 15 trajectories. The literal cheat path was never accessed.
- No agent attempted to write to `/logs/verifier/reward.txt` directly, modify `test.sh`, or game the FAIL_TO_PASS / PASS_TO_PASS pytest invocations.
- No agent attempted to skip tests via `pytest.mark.skip` injection or `conftest.py` manipulation.

### Severity assessment

This is **not** an isolated weakness — it is a systemic flaw in the `lv1` scrambling design. **Two of three successes (67%) are reward-hacking the recoverable git state.** Only one success demonstrates actual capability in the task's nominal domain. If reward hacking is filtered out, the genuine pass rate is **1/15 (~7%)**, not 3/15 (~20%).

For the same reason, every `lv1` task in the featurebench-modal family carries this vulnerability — including the sibling `swin2sr` task previously inspected, where the success run `20acb248` used `git restore` of `pytorch_utils.py`, `modeling_perceiver.py`, and `modeling_swin2sr.py` (also a reward hack by the same logic).

### Concrete fix for reward hacking

**The single highest-leverage fix** is to make the scramble persistent across git operations:

1. **In the Dockerfile, commit the setup_patch after applying it:**
   ```dockerfile
   RUN cd /testbed && (git apply /tmp/setup_patch.diff || patch --fuzz=5 -p1 -i /tmp/setup_patch.diff || true) \
     && git -c user.email=fb@bench.com -c user.name=FeatureBench add -A \
     && git -c user.email=fb@bench.com -c user.name=FeatureBench commit -m "task setup" --allow-empty
   ```
   Now HEAD = scrambled. `git reset --hard`, `git checkout --`, and `git stash pop` all restore the *scrambled* state, not the clean one. Reward hacks #1 and #2 stop working.

2. **Squash the underlying commit history** (or `git checkout --orphan` and re-init), so `git checkout HEAD~1 -- <file>` doesn't reach a pre-scramble state via prior commits. After step 1, the repo should look like a fresh single-commit repo whose HEAD already contains the scramble.

3. **Delete `/tmp/setup_patch.diff` after build** (Issue 2 / Fix B). Closes the literal oracle path.

4. **(Optional, defense in depth) After applying the scramble, set the file mtime to the original commit's date** to defeat any agent that tries to identify "recently modified" files via `find -mmin`/`stat`.

With these fixes, the only legitimate path to reward=1 is the intended one: read the prompt, examine the codebase to find broken neighboring files (via `pytest`, `import` errors, or grep for missing symbols), and reconstruct them from `modular_lightglue.py` or peer arch directories. This is what `c85c0003` actually did — and is the capability the task is supposed to measure.

### Concrete fix proposals

- **(A) Add one sentence to the instruction**: *"Note: portions of related files in this codebase may be in an incomplete state. After implementing the configuration, you should run the relevant test suite (`pytest tests/models/lightglue/test_modeling_lightglue.py`) and address any other failures you find."* This would lift pass rates substantially without revealing the answer. It tests test-driven workflow rather than scope-intuition.
- **(B) Delete `/tmp/setup_patch.diff` in the Dockerfile after applying it.** Closes the cheat path without affecting the legitimate solution route.
- **(C) Quiet the pip install** in `test.sh` so failure tracebacks survive to the captured stdout.
- **(D) Fix the AST-dump rendering** in featurebench-modal's instruction template (renders `model_type = "lightglue"` instead of the AST dict). This is a templating-tool bug, not a per-task fix.
- **(E) Make `test.sh`'s test restore idempotent** to agent-created test files — `rm -f` before `git checkout`.
- **(F) [CRITICAL] Commit the setup_patch in the Dockerfile so HEAD = scrambled.** Eliminates the `git reset --hard` / `git checkout --` reward-hacking primitive that two of three current "successes" rely on. See Q5b for full rationale.

Fixes (D), (E), and (F) are clearly bugs; (A) is borderline (some would argue the ambiguity is what makes the task discriminative). (B) and (C) are hygiene. **(F) is the only fix without which the task's pass rate is meaningfully inflated by reward hacking.**

---

## Final Verdict

### **CONDITIONAL ACCEPT — agent-capability bottleneck on the surface, but reward hacking inflates the pass rate; fix F is required**

The task is solvable in principle (one genuine success, `c85c0003`, demonstrates this), but **2 of the 3 nominal successes are reward hacks** that obtained credit by reverting the setup_patch via standard git commands rather than by implementing the task. The genuine pass rate is **1/15 (~7%)**, not 3/15 (~20%). This significantly weakens the task's signal until fix (F) lands.

| Failure source | Evidence | Capability or task issue? |
|---|---|---|
| Narrow-scope instinct (declare done after implementing the named artifact) | 11/12 failures only edit `configuration_lightglue.py` (and sometimes `modular_lightglue.py`); never open `modeling_lightglue.py` | **Capability** |
| No use of git as diagnostic | Only `4c765ed4` ran `git status` — and dismissed the result. None ran `ls /tmp`. | **Capability** |
| Substitute "verification" by `py_compile` / `ast.parse` / in-process assert smoke test | 9/12 failures end on one of these; none exercise model instantiation | **Capability** |
| Wrong python interpreter | 12/12 hit this; codex `c85c0003` resolved in 2 turns; terminus-2 `c21d3e0b` took 30 | **Capability** (correct interpreter is discoverable via `which python`; "we have already installed all dependencies" line tempts giving up) |
| AST-dump rendering of `model_type`/`sub_configs` | `0e6055b2` wasted ~15 turns; `fd6882bf` also surfaced doubt | **Templating bug (Issue 3 / Fix D)** |
| Hand-reconstructed test file derails `test.sh`'s restore | `fd6882bf` did extensive correct work and was punished | **Harness fragility (Issue 4 / Fix E)** |
| **Two "successes" are reward hacks via `git reset --hard` / `git checkout HEAD~1 --`** | `95cfd615` accidental, `c21d3e0b` deliberate — neither implemented `modeling_lightglue.py` or `superpoint/configuration_superpoint.py` | **Task design (Q5b / Fix F)** |

**What this task is supposed to measure**: ability to (1) treat the prompt's named artifact as a starting point rather than the entire scope, (2) use diagnostic tooling to discover broken neighboring files, (3) follow import errors, (4) identify the correct python interpreter, and (5) port code between sibling implementations. **What it actually rewards in 2 of 3 successes**: knowing that `git reset --hard` exists. These are very different capabilities, and only the former is what HaborMix presumably wants to measure.

**Required fixes before acceptance**:
- **(F) [CRITICAL]** Commit the setup_patch in the Dockerfile so HEAD = scrambled. Without this, `git reset --hard` and `git checkout HEAD~1 -- <file>` are one-line reward hacks. With this, the scramble persists and the only path to reward is genuine implementation. Predicted pass rate after (F): ~1/15, but every pass would be `c85c0003`-quality.
- **(D)** Fix the AST-dump rendering of `model_type` and `sub_configs` in `instruction.md`. Unambiguously a featurebench templating bug.
- **(E)** Make `test.sh`'s test-restore robust to agent-created test files (`rm -f` before `git checkout`).

**Recommended fixes (not blockers)**:
- **(B)** Remove `/tmp/setup_patch.diff` after build — the literal oracle path, currently un-exploited but visible.
- **(C)** Quiet pip install output in `test.sh` so failure tracebacks survive in captured stdout.

The instruction-framing concern (Issue 1 / Fix A) remains borderline. Adding a hint about broader scrambling would lift pass rates but reduce signal value. **I would NOT add fix A** — the current ambiguity is what makes the task discriminative, and `c85c0003` demonstrates the task is solvable through the intended path.

**Decision**: The task is fundamentally well-formed and the underlying skill it measures is real and valuable, but it is currently **leaky**. With fix (F) applied, the task becomes a clean test of (1) noticing broader breakage, (2) reconstructing missing helpers from `modular_lightglue.py`, and (3) running the actual test suite — exactly the genuine bottlenecks the failure analysis highlights. **Accept conditional on fix (F)**; without it, the task's headline "3/15 medium-difficulty pass rate" overstates what current frontier agents can actually do at this task type by ~3×. The same vulnerability applies family-wide to all featurebench-modal `lv1` tasks (including the sibling `swin2sr` task), so fix (F) should land at the template level, not per-task.
