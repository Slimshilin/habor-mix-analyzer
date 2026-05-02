# Run Matrix: gso-numpy--numpy-ef5e545

| Run ID (short) | Model | Agent | Reward | Approach | Bytes? | Build OK | Self-meas. speedup | Failure mode |
|---|---|---|---|---|---|---|---|---|
| a5256238 | claude-opus-4-6 | terminus-2 | **1.0** | Generic predicate dispatcher in `_vec_string` (multiarraymodule.c), forward-scan with embedded-null bail | No (Unicode-only) | ✓ | ~7.5x | — |
| 25b3f5be | claude-opus-4-6 | terminus-2 | **1.0** | `isalpha`-specific helper in `_vec_string`, ASCII bit-twiddle fast path `((c\|0x20)-'a')<26`, backward null strip | No (Unicode-only) | ✓ | ~6.7x | — |
| 3744d256 | claude-opus-4-6 | terminus-2 | 0.0 | New `_fast_unicode_isalpha` symbol exposed via `multiarray.py`, `defchararray.py` dtype-branched on `kind=='U'` | No | ✓ | ~9.5x | Just below 0.95×gold threshold (or harness regression on edited Python wrapper) |
| b06ce298 | claude-opus-4-6 | claude-code | 0.0 | `_unicode_isalpha_fast` in `_vec_string`, contiguous-only, NPY_UNICODE-only | No | ✓ (1 build) | ~5.5x | Below 0.95× threshold; gated on contiguous-only |
| 925d9a5e | claude-opus-4-6 | claude-code | 0.0 | `_vec_string_isalpha_unicode` in `_vec_string`, both contiguous + iterator, NPY_UNICODE-only | No | ✓ (after segfault fix) | ~5x | Below 0.95× threshold |
| 086d698e | claude-opus-4-6 | claude-code | 0.0 | 9-predicate dispatcher in `_vec_string` (incl. `istitle`, `islower`, `isupper`), function-pointer + cased helpers, NPY_UNICODE-only | No | ✓ (4 builds, fixed 1 correctness regression) | ~9x | Below 0.95× threshold |
| 82959539 | gpt-5.4 | codex | 0.0 | Generic predicate (9 methods) inside `_vec_string`, `_unicode_bool_method_id` enum, NPY_UNICODE-only | No | ✓ | ~5x | Below 0.95× threshold |
| c274fd2e | gpt-5.4 | codex | 0.0 | Specialized `_vec_string_unicode_isalpha`, NPY_UNICODE-only | No | ✓ | ~4-5x | Below 0.95× threshold |
| 2613d2fa | gpt-5.4 | codex | 0.0 | Function-pointer table for 6 predicates, gated on `ISALIGNED && !ISBYTESWAPPED`, NPY_UNICODE-only | No | ✓ | ~5.3x | Below 0.95× threshold |
| ab68d1c9 | gpt-5.4 | terminus-2 | 0.0 | `PyObject_CallFunctionObjArgs` → `PyObject_CallOneArg` micro-fix only | (shared) | ✓ | ~0% (within noise) | Fails MIN_PROB_SPEEDUP=1.2× geometric mean; agent shipped despite no measurable improvement |
| 8ad260a7 | gpt-5.4 | terminus-2 | 0.0 | First wrote UCS-4 unicode fast path, **regressed** in own benchmark, REVERTED to `PyObject_CallOneArg` | (shared) | ✓ | ~2% | Same as ab68d1c9; reverted real fast path after regression |
| 5b8a9cbf | gpt-5.4 | terminus-2 | 0.0 | None — clean tree, 0-byte patch | — | n/a | — | **AgentTimeoutError**: 3265+ idle messages, "conservative-revert spiral" |
| 1789a37c | gemini-3.1-pro-preview | terminus-2 | 0.0 | `_vec_string_fast_isalpha` in `_vec_string`, NPY_UNICODE-only, uses `PyArray_SETITEM` per element (no buffer write) | No | ✓ | ~5x | Below 0.95× threshold |
| 4f45be6a | gemini-3.1-pro-preview | terminus-2 | 0.0 | Contiguous fast path before iterator, raw buffer writes | **Yes** (NPY_STRING via `isalpha((unsigned char)c)`) | ✓ | ~50% (~2x) | Below 0.95× threshold; agent rejected ufunc as "too invasive" |
| a20ec2f7 | gemini-3.1-pro-preview | terminus-2 | 0.0 | `_vec_string_fast_isalpha`, both NPY_STRING + NPY_UNICODE, uses `Py_ISALPHA` (after sed-fixing `NumPyOS_ascii_isalpha` undefined symbol) | **Yes** | ✓ (2nd build) | ~2.3x | Below 0.95× threshold |
| 357b3ac1 | gemini-3.1-pro-preview | gemini-cli | 0.0 | `_vec_string_fast_bool_method` for 6 predicates, both NPY_UNICODE + NPY_STRING, falls back on byteswapped | **Yes** | ✓ | ~6x | Below 0.95× threshold |
| 3e6b3d2b | gemini-3.1-pro-preview | gemini-cli | 0.0 | Inline ASCII fast path inside `_vec_string_no_args`, `c≥128` falls back, both unicode + bytes | **Yes** | ✓ | ~5x | Below 0.95× threshold |
| 0abd8670 | gemini-3.1-pro-preview | gemini-cli | 0.0 | 8-predicate fast path with full `Py_UNICODE_IS*` macros incl. `ISTITLE`, both unicode + bytes (via inline ASCII) | **Yes** | ✓ (after first build link error) | ~5x | Below 0.95× threshold |

## By Model

- claude-opus-4-6: 2/6 pass (33%)
- gpt-5.4: 0/6 pass (0%)
- gemini-3.1-pro-preview: 0/6 pass (0%)

## By Agent

- claude-code (claude-opus): 0/3 pass — all 3 attempted serious C-level fast paths in `_vec_string`, fell short on threshold
- terminus-2 (mixed models): 2/9 pass — both successes were claude-opus/terminus-2; gpt-5.4/terminus-2 were 3/3 fail (one timed out, two settled for `PyObject_CallOneArg` micro-fix); gemini/terminus-2 were 3/3 fail despite real C work
- codex (gpt-5.4): 0/3 pass — all 3 wrote competent C fast paths in `_vec_string`, all fell short
- gemini-cli (gemini): 0/3 pass — all 3 reached for C fast paths, even covered bytes, still fell short

## Architecture Taxonomy

| Architecture | Count | Pass rate |
|---|---|---|
| Real ufunc registration in `string_ufuncs.cpp` (gold approach) | **0** | n/a — no agent tried this |
| Fast path inside `_vec_string` in `multiarraymodule.c` | 13 | 2/13 (15%) |
| New symbol exposed via `multiarray.py` + dtype branch in `defchararray.py` | 1 | 0/1 |
| `PyObject_CallOneArg` micro-fix only | 2 | 0/2 |
| Empty patch (timeout) | 1 | 0/1 |
| Truly Python-only (no C touched) | **0** | n/a — every agent reached for C |

## Bytes (NPY_STRING) coverage

- Covered: 5 runs (4f45be6a, a20ec2f7, 357b3ac1, 3e6b3d2b, 0abd8670) — all FAILED
- Not covered: 13 runs (incl. both successes)

→ Bytes coverage is **not** the discriminator (the user-visible test_script uses only `<U60` Unicode and the hidden tests appear to be Unicode too, since both successes lack bytes coverage)

## Verifier-observed timings (from `test_stdout`)

Verifier echoes only the `>>>>> Start Commit Output` block; `Base Output` and `Patch Output` aren't surfaced, and the upstream `gm_speedup_patch_base` / `hm_speedup_patch_commit` aggregation dict is not echoed. Visible info:

- Every sampled run (a5256238, 25b3f5be, 3744d256, 82959539, b06ce298) shows `>>>>> Tests Passed` for all of `gso_test_0/1/2.py` — **all five passed correctness**.
- The reward line is `opt_commit: True, reward: 1` for the two successes and `opt_commit: False, reward: 0` for the three sampled failures.
- 3 hidden test scripts (gso_test_0, 1, 2), 5 iterations each.
