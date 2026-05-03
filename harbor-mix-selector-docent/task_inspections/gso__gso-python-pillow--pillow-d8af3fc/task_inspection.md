# Task Inspection: `gso/gso-python-pillow--pillow-d8af3fc`

## Verdict

**Task quality:** **Reject unless fixed.** The underlying benchmark idea is good and the observed failures mostly reveal real agent capability bottlenecks, but the task has two serious quality defects: the reproduction script in the prompt is syntactically broken, and the equivalence check appears to validate only channel metadata, not pixel contents. That means the task is solvable and discriminative in practice, but not robust enough to accept unchanged.

**Primary observed bottleneck:** **Agent capability bottleneck.**

The single most valuable answer: **most agents failed because they found the right subsystem and implemented a plausible C-level split shortcut, but did not reach the upstream-quality optimization: a bulk C split path with enough allocation/data-movement reduction to match the target commit.** Two runs pass. Most non-crashing failures are not confused about what `split()` does; they are about 15-45% slower than the oracle on the hidden timing suite. That is capability. The task-quality problem is separate: the current verifier/prompt would allow fragile or semantically incomplete solutions, so I would not accept the task as high quality until those fixes are made.

## Methodology

No sampling. I exported all 18 linked Docent runs into `trajectories/`, all verifier outputs into `test_stdout/`, and run metadata into `run_summaries.json`. I also parsed timing sections into `timing_summary.json`.

I split the 18 trajectories across three subagents:

- Runs 01-06: claude-code/opus and terminus-2/opus.
- Runs 07-12: codex/gpt-5.4 and terminus-2/gpt-5.4.
- Runs 13-18: gemini-cli/gemini and terminus-2/gemini.

I then reconciled their per-run findings against the verifier stdout and the upstream oracle commit. The public upstream target commit is `python-pillow/Pillow@d8af3fc23a730dd5e9a6e556263e7be7d8de1c7e`; a local copy of the patch was fetched to `/tmp/pillow_d8af3fc.patch`.

## What The Task Asks

The prompt asks agents to optimize the runtime of a script that calls:

```python
channels = img.split()
modes = [ch.mode for ch in channels]
sizes = [ch.size for ch in channels]
```

The images include `RGB`, `RGBA`, `LA`, palette `P`, binary `1`, skinny/tall/tiny images, and two downloaded sample images. The baseline old Pillow implementation routes `Image.split()` through repeated `self.im.getband(i)` calls. The intended fast direction is inferable from the environment: a C-level split path that extracts all bands in one pass and returns all channel images at once.

The verifier does this:

1. Captures the submitted patch.
2. Resets the repo to the base parent of `d8af3fc`.
3. Runs 11 hidden tests on base, patch, and the upstream target commit.
4. Compares patch timings to the target commit and emits `opt_commit`.

Important: the reward is not just "faster than base." Many failing patches have `patch_vs_base_geomean_speedup` around `1.44x-1.46x`, but get reward 0 because the upstream commit is still faster.

## Oracle Shape

The upstream target is not a tiny Python tweak. The relevant pieces are:

- `PIL/Image.py`: route multi-band `split()` through `self.im.split()` rather than a Python loop over `getband`.
- `_imaging.c`: expose a new core `_split` method that returns all band images.
- `libImaging/Bands.c`: add `ImagingSplit`, with 2/3/4-band extraction loops and word-packed deinterleaving.
- `libImaging/Imaging.h`: declare the split helper.
- Successful agent runs often also add `ImagingNewDirty` / allocation avoidance or SIMD-style deinterleaving.

This distinction matters because most failures implemented only the first half: they removed some Python overhead but not enough allocation/data-copy overhead to match the target.

## Question 1: How Close Were Agents?

| Band | Count | Runs | What It Means |
| --- | ---: | --- | --- |
| Success | 2 | 01, 04 | `opt_commit: True`, reward 1. |
| Close performance miss | 10 | 02, 03, 05, 06, 07, 08, 09, 13, 14, 17 | Functional tests pass; real speedup; still slower than oracle. |
| Partial/wrong optimization target | 4 | 10, 11, 12, 18 | Caching or modest C-loop wrappers; small/misaligned speedups. |
| Correctness failure | 2 | 15, 16 | Hidden `gso_test_3.py` crashes with `ValueError: image has wrong mode`. |

Parsed verifier timing summary:

| Run | Agent/model | Reward | Patch/base geomean speedup | Oracle/patch geomean ratio | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| 01 | claude-code / opus | 1 | 2.40x | 1.37 | Beats oracle aggregate. |
| 04 | terminus-2 / opus | 1 | 1.94x | 1.13 | Beats oracle aggregate. |
| 02,03,05,06,07,08,09,13,14,17 | mixed | 0 | ~1.43-1.46x mostly | ~0.82-0.85 | Real speedup, but oracle still ~15-20% faster. |
| 10,12 | terminus-2 / gpt-5.4 | 0 | ~1.02x | ~0.58-0.60 | Cache helps local repeated-call tests, not verifier. |
| 15,16 | gemini-related | 0 | n/a | n/a | Hidden correctness crash. |

So the agents are often close in *direction*, but only two cross the performance bar. This is a sharp task: it separates "found the C hook" from "implemented the mature split optimization."

## Question 2: Cross-Agent Variation, Surface And Root Causes

| Agent/model | Pass | Fail | Pattern |
| --- | ---: | ---: | --- |
| claude-code / claude-opus-4-6 | 1 | 2 | One complete SIMD/allocation-heavy pass; two scalar C split near misses. |
| terminus-2 / claude-opus-4-6 | 1 | 2 | One allocation-aware pass; two scalar C split near misses. |
| codex / gpt-5.4 | 0 | 3 | All find right C area; all produce ~1.44-1.46x, below oracle. |
| terminus-2 / gpt-5.4 | 0 | 3 | Two cache/wrong-target attempts; one small C wrapper. |
| gemini-cli / gemini-3.1-pro-preview | 0 | 3 | Two performance misses, one hidden correctness crash. |
| terminus-2 / gemini-3.1-pro-preview | 0 | 3 | One hidden correctness crash; two modest/noisy C attempts with patch artifacts. |

### Surface Reasons

**Performance threshold miss.** Runs 02, 03, 05-09, 13, 14, 17 all pass visible hidden functional checks and improve over base, but final stdout says `opt_commit: False, reward: 0`. Their common patch shape is scalar bulk split or C-loop wrapper, usually touching `PIL/Image.py`, `_imaging.c`, `libImaging/Bands.c`, and `libImaging/Imaging.h`.

**Wrong optimization target.** Runs 10 and 12 add Python-level split-result caching. Their local repeated-call benchmark drops to microseconds, but the verifier's measured path creates images in `setup()` and splits each image once. The cache does not address first-call split cost.

**Hidden correctness crash.** Runs 15 and 16 unconditionally call the new core `self.im.split()` path and crash on `gso_test_3.py`:

```text
ValueError: image has wrong mode
File "/testbed/.venv/lib/python3.9/site-packages/PIL/Image.py", line 1955, in split
return tuple(self._new(x) for x in self.im.split())
```

**Patch hygiene noise.** Runs 17 and 18 leave helper patch scripts in the submitted diff. This does not appear to be the direct reason for failure, but it is a sign of weaker finalization.

### Root Cause

The root cause for the dominant failure cluster is **incomplete performance reasoning inside Pillow's C image core**. Agents correctly infer that `split()` is slow because it calls `getband()` per band, but many stop after making a scalar C method that still uses normal allocation and relatively simple copies. The upstream-quality solution also cares about allocation cost and packed deinterleaving. Passing runs do that; near misses usually do not.

For the correctness-crash cluster, the root cause is **failure to preserve all old `Image.split()` semantics**, especially single-band or special-mode cases. Original `Image.split()` had a single-band copy path; naive `self.im.split()` replacement does not automatically preserve that unless the C helper handles it.

For the caching cluster, the root cause is **benchmark misunderstanding**. The agents optimized repeated `split()` calls on unchanged image objects, but the task's usage scenario is first-call splitting across many images.

## Question 3: Concrete Expected Vs Produced Behavior

### Expected Optimized Behavior

A robust patch should preserve the old `Image.split()` API for all modes while making multi-band split cheaper:

```python
if self.im.bands == 1:
    ims = [self.copy()]
else:
    ims = map(self._new, self.im.split())
return tuple(ims)
```

That Python-level shape only works if the C method is complete. The C side must allocate output band images and extract all bands in a single pass, including 2/3/4-band cases, and it must handle errors/modes correctly.

### Near-Miss Output

Scalar C split runs typically produced a shape like:

```c
for each band:
    allocate L image
for each pixel:
    copy channel bytes into band images
return tuple of PyImagingNew(bands[i])
```

This is conceptually right but not enough. Examples:

- Run 02: local `New split: 3.507 ms`, `Old split: 5.197 ms`, but verifier `patch_vs_base_geomean_speedup = 1.46x`, `oracle/patch = 0.84`, reward 0.
- Run 07: local benchmark around `3.61 ms -> 1.84 ms`, verifier `patch_vs_base_geomean_speedup = 1.44x`, `oracle/patch = 0.84`, reward 0.
- Run 09: local `3.57 ms -> 1.85 ms`, verifier `patch_vs_base_geomean_speedup = 1.44x`, `oracle/patch = 0.82`, reward 0.

### Wrong-Target Output

Runs 10 and 12 cache split results in `PIL/Image.py`. The local repeated benchmark improves from about `3.6 ms` to about `9 us`, but verifier speedup is only about `1.02x`. Expected behavior is improving first-call split cost; produced behavior improves repeated calls on the same object.

### Hidden Correctness Failure

Runs 15 and 16 fail in `gso_test_3.py` with `ValueError: image has wrong mode`. This is exactly the kind of hidden case agents should guard against: `Image.split()` is a general library API, not only `RGB/RGBA` random arrays from the prompt.

## Question 4: Is Failure Because Of The Task Or Agent Capability?

For the observed 16 non-passing runs, **mostly agent capability**:

- 18/18 identify `Image.split()` as the hot operation.
- Most inspect `PIL/Image.py`, `_imaging.c`, and `libImaging/Bands.c`.
- Most rebuild and measure.
- The strongest failures are real optimizations, not random broken patches.
- Two agents pass, proving the task is theoretically achievable in the given environment.

What sufficient capability means here:

- Understand the old split path across Python and C.
- Preserve `Image.split()` semantics for single-band and non-plain modes.
- Recognize that avoiding repeated `getband` calls is necessary but not sufficient.
- Optimize allocation/data movement enough to match an upstream performance commit.
- Avoid local benchmark traps such as repeated-call caching.

That said, **the task itself has quality problems**. These did not cause most observed failures, but they make the task unacceptable unchanged.

### Task Problem 1: Prompt Script Is Syntactically Broken

The provided reproduction script contains invalid nested f-strings such as:

```python
f'{label}: channel count mismatch (ref={ritem['num_channels']} vs curr={citem['num_channels']})'
```

Agents can infer the intended fix by changing quote styles, and many did. But the task explicitly tells agents to create and run the script; the supplied script should run as written. This is a real prompt defect.

### Task Problem 2: Equivalence Is Too Weak

The prompt's `check_equivalence()` validates only:

- labels,
- number of channels,
- channel modes,
- channel sizes.

It does not check channel pixel data. The hidden verifier appears to use the same style: failures are either performance misses or mode errors; there is no evidence of pixel-content checking. This means a shortcut that returns blank `L` images of the right size/mode could plausibly pass correctness and be very fast. That directly undermines the "functionally equivalent" requirement.

A super-capable being can solve the intended task, but a shortcut-capable agent might also pass a weak verifier. That is the main reason I would reject unchanged.

### Task Problem 3: Prompt/Scoring Contract Mismatch

The prompt asks to "improve the performance" and "confirm that the performance has improved." The verifier requires closeness to a strong upstream commit. Runs with ~1.45x real geomean speedup get reward 0. That can be acceptable for a hard optimization benchmark, but the prompt should tell agents that the score is based on *degree* of speedup across hidden variants, not just any improvement.

## Question 5: Fixes That Would Make The Task Complete

**Required fix 1: repair the reproduction script.** Change the broken f-strings to use double-quoted outer strings or temporary variables. This is a pure quality fix and does not simplify the task.

**Required fix 2: strengthen functional equivalence.** At minimum, for every split channel, compare `mode`, `size`, and `tobytes()` or a stable hash of the bytes. For huge images, hashing full bytes is fine for 11 tests; for speed, hash sampled plus full small cases. The verifier should catch blank-channel hacks and wrong channel order.

**Required fix 3: state performance scoring more honestly.** Add a line like: "The evaluator uses several hidden split workloads and rewards patches by how close their speed is to a strong reference optimization, so a small local speedup may not be sufficient." This does not reveal the oracle implementation.

**Recommended fix 4: package a targeted oracle/solve script.** The exported `solve_sh` metadata is truncated and begins with unrelated upstream hunks, while the verifier actually compares against `d8af3fc`. For auditability, the task should include a targeted split-only reference patch or at least a clean full commit reference.

**Recommended fix 5: add explicit special-mode coverage.** Hidden tests already include a mode that catches naive `self.im.split()` replacements. Keep that, but also make pixel correctness visible in the test design so this is about preserving API semantics, not guessing hidden traps.

## Final Decision

**Observed failures:** primarily agent capability bottleneck.

**Task quality:** reject unchanged. The benchmark idea is solid and the failure pattern is meaningful, but a high-quality accepted task cannot ship with a syntactically invalid reproduction script and metadata-only equivalence for an image-channel operation. After the script and verifier fixes above, I would accept it as a strong hard optimization task: it clearly distinguishes shallow C wrappers/caches from agents that can implement a mature Pillow core optimization.

