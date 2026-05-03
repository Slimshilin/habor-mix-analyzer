# Gold patch — flipt-io/flipt @ c8d71ad7ea98d97546f01cce4ccb451dbcf37d3b

Source: https://github.com/flipt-io/flipt/commit/c8d71ad7ea98d97546f01cce4ccb451dbcf37d3b

## Files changed (12)

| File | Status | Lines | Notes |
| --- | --- | --- | --- |
| `cmd/flipt/validate.go` | modified | 60 | rewrites CLI to use `fs.SnapshotFromFS`/`SnapshotFromPaths` + `cue.Unwrap` |
| `internal/cue/flipt.cue` | modified | 8 | makes `name`, `value`, `percentage` optional in cue schema |
| `internal/cue/validate.go` | modified | 59 | **core refactor** — removes `Result`, returns `error`, adds `Unwrap`, `Error.Error()`, `Error.Format` |
| `internal/cue/validate_fuzz_test.go` | modified | 2 | drops `_,` from `Validate` return |
| `internal/cue/validate_test.go` | modified | 31 | tests target the new error shape |
| `internal/storage/fs/fixtures/invalid_boolean_flag_segment/features.yml` | added | 12 | new fixture |
| `internal/storage/fs/fixtures/invalid_variant_flag_distribution/features.yml` | added | 16 | new fixture |
| `internal/storage/fs/fixtures/invalid_variant_flag_segment/features.yml` | added | 13 | new fixture |
| `internal/storage/fs/snapshot.go` | modified | 143 | `storeSnapshot` -> `StoreSnapshot`, `snapshotFromFS` -> `SnapshotFromFS` (now exported, validates), adds `SnapshotFromPaths` (validates per-path), changes 3 `addDoc` errors to `ErrInvalidf("flag X/Y rule N references unknown ...")` |
| `internal/storage/fs/snapshot_test.go` | modified | 19 | **adds 3 new tests at the end of file** (after line 1643): `TestFS_Invalid_VariantFlag_Segment`, `TestFS_Invalid_VariantFlag_Distribution`, `TestFS_Invalid_BooleanFlag_Segment` |
| `internal/storage/fs/store.go` | modified | 4 | renames `storeSnapshot` -> `StoreSnapshot` field |
| `internal/storage/fs/sync.go` | modified | 36 | renames embedded `*storeSnapshot` -> `*StoreSnapshot` |

## The 8 required tests (per Gemini auditor)

| Test | File | Tests for |
| --- | --- | --- |
| `FuzzValidate` | `internal/cue/validate_fuzz_test.go` | new `Validate` signature compiles cleanly |
| `TestValidate_V1_Success` | `internal/cue/validate_test.go` | `Validate("testdata/valid_v1.yaml", b)` returns `nil` |
| `TestValidate_Latest_Success` | `internal/cue/validate_test.go` | `Validate("testdata/valid.yaml", b)` returns `nil` |
| `TestValidate_Latest_Segments_V2` | `internal/cue/validate_test.go` | `Validate("testdata/valid_segments_v2.yaml", b)` returns `nil` |
| `TestValidate_Failure` | `internal/cue/validate_test.go` | `cue.Unwrap(err)` returns `[]error`, first elem is a `cue.Error` with `.Message`, `.Location.{File,Line,Column}` matching gold values |
| `TestFS_Invalid_VariantFlag_Segment` | `internal/storage/fs/snapshot_test.go` | `SnapshotFromFS(zaptest.NewLogger(t), fs)` returns error with **EXACT** text `flag fruit/apple rule 1 references unknown segment "unknown"` |
| `TestFS_Invalid_VariantFlag_Distribution` | `internal/storage/fs/snapshot_test.go` | `SnapshotFromFS(...)` returns error with **EXACT** text `flag fruit/apple rule 1 references unknown variant "braeburn"` |
| `TestFS_Invalid_BooleanFlag_Segment` | `internal/storage/fs/snapshot_test.go` | `SnapshotFromFS(...)` returns error with **EXACT** text `flag fruit/apple rule 1 references unknown segment "unknown"` |

## Key facts that disprove the auditor's "missing tests live in another file" hypothesis

1. **All 3 `TestFS_Invalid_*` tests live inside `internal/storage/fs/snapshot_test.go` itself**, appended to the end of the existing file at line 1643+. They are NOT in a separate `invalid_test.go`.
2. The `before_repo_set_cmd` (per the auditor) restores `internal/storage/fs/snapshot_test.go` -> the 3 tests will be present in the restored test file.
3. **However** these tests rely on **fixture files** that the agent must create:
   - `internal/storage/fs/fixtures/invalid_variant_flag_segment/features.yml`
   - `internal/storage/fs/fixtures/invalid_variant_flag_distribution/features.yml`
   - `internal/storage/fs/fixtures/invalid_boolean_flag_segment/features.yml`
4. Tests use `//go:embed all:fixtures` to load fixtures at compile time. The fixture files must:
   - Exist at compile time (otherwise `fs.Sub` returns an empty FS and the test fails because `SnapshotFromFS` won't return the expected error).
   - Match the EXACT structure expected by the gold tests' assertions on error string `"flag fruit/apple rule 1 references unknown ..."`.
5. The **error message format must match the gold-patch implementation EXACTLY**: `errs.ErrInvalidf("flag %s/%s rule %d references unknown segment %q", doc.Namespace, flag.Key, rank, segmentKey)`. Any drift (e.g. quoting style, %s vs %q, stuttered "rule %d", different package, missing namespace prefix) will fail the `require.EqualError` check.

## Implications for fairness

- The instruction states the EXACT error text templates (lines 38-41 of `_task_instruction.txt`):
  - `flag <namespace>/<flagKey> rule <ruleIndex> references unknown variant "<variantKey>"`
  - `flag <namespace>/<flagKey> rule <ruleIndex> references unknown segment "<segmentKey>"`
- The instruction also states the new public interfaces (`StoreSnapshot`, `SnapshotFromFS`, `SnapshotFromPaths`, `Unwrap`) — including their inputs/outputs — verbatim.
- The instruction tells the agent to make `Validate` return a single `error` value supporting multi-error unwrap, and the FS snapshot constructors must call this validator. So an agent reading the prompt carefully has every ingredient to write code that produces the expected error strings.
- The agent must INFER the need to create the 3 fixture files. The instruction says "I've already taken care of all changes to any of the test files" — the fixture YAMLs are NOT test files per se (they're under `fixtures/`), so the agent could reasonably interpret either way.
- The 3 fixture files are NOT restored by the grader's `before_repo_set_cmd`. So if the agent creates them and writes the right error messages, the tests should pass.
