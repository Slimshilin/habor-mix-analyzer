# Subagent report: terminus-2 / claude-opus-4-6 (3 runs)

> Note: the subagent reports each run as 0/8 but mentions "5 cue tests pass". Per my verifier dump all 3 runs are **0/8** (`Required tests that passed: 0`), with `Passed tests: 3` (these 3 are unrelated tests in the same package the parser ran — not part of the 8 required). The cue tests do NOT pass: the agents kept the legacy `(Result, error)` method and the gold-restored `validate_test.go` won't compile.

## Per-run findings

### `512520b0` — 0/8
- Kept `FeaturesValidator.Validate(file, b) (Result, error)` unchanged.
- Added free `Unwrap(err) ([]error, bool)` and `validationError` with `Unwrap() []error`.
- Did **NOT** add a top-level `Validate(file, b) error`, NOT add `Error.Error()`, NOT use `errors.Join`.
- Renames done. SnapshotFromPaths added but does NOT call `cue.NewFeaturesValidator()` per file — instead has a self-contained `validateReferences(file, b)` re-parsing yaml.
- **No fixture YAMLs.**
- Format strings: `fmt.Errorf("flag %s/%s rule %d references unknown segment %q", ns, flag.Key, ruleIdx, sk)` joined via `errors.Join`. Format text correct.

### `aec30231` — 0/8
- Kept `(Result, error)` method. Added free `Unwrap(err)` only. Explicitly stated: "The existing Validate method on FeaturesValidator keeps its (Result, error) signature so existing tests continue to pass."
- This is the most direct evidence of the root cause: the agent reasoned about backward compatibility with the IN-TREE tests and missed that the gold-restored tests use the new signature.
- Renames done; **modified `addDoc` in-place** (the only run in this group to do so) with gold-matching format: `fmt.Errorf("flag %s/%s rule %d references unknown segment %q", doc.Namespace, f.Key, rank, segmentKey)` and the variant equivalent.
- **No fixture YAMLs.**
- This run's `addDoc` work would have produced the gold-correct error string at runtime IF the FS package compiled (it doesn't, because the cue package fails to compile and the FS package depends on it).

### `c1579e91` — 0/8
- Kept `(Result, error)` method.
- DID add `Error.Error() = "message (file line:column)"` (the only opus run to do this).
- Added free `Unwrap(err)`.
- Renames + `SnapshotFromPaths` added. Validation again wired into `addDoc` via in-place edits. Format strings gold-matching.
- **No fixture YAMLs.**

## Cross-run summary
All 3 runs converged on the same architectural choice (preserve legacy `(Result, error)` method for backward compatibility with the **in-tree** tests) and the same omissions (no fixture YAMLs, no `errs.ErrInvalidf`, no `errors.Join`). When the grader restores `validate_test.go` (which uses `err = v.Validate(...)`), the cue package fails to compile because `v.Validate(...)` resolves to the kept method which returns 2 values into a single-value assignment. This single design decision tanks all 8 required tests in this group of 3.

This is a notable model/harness signal: claude-opus-4-6 in both `claude-code` and `terminus-2` harnesses (6 runs total) **all** chose to preserve the legacy method, while gpt-5.4 and gemini-3.1-pro-preview consistently replaced the method outright. The opus prior toward "don't break the visible tests" is the dominant failure mode for this task in those runs.
