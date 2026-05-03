# Subagent report: terminus-2 / gpt-5.4 (3 runs)

## Per-run findings

### `299da343` — 2/8
- `Validate` returns single `error`. Renames + `SnapshotFromFS`/`SnapshotFromPaths` exported. Validation wired in via full `validator.Validate` per file (which can break legitimate fixtures).
- Format string uses `%q` and 0-based `i` for rule index (off-by-one vs gold's `rule 1`).
- `addDoc` untouched. Errors use `Error{Message, Location}`.
- **No fixture YAMLs.**
- Ran `go test ./internal/cue ./internal/storage/fs` repeatedly; all `[build failed]` or `FAIL`. Dismissed as "stale visible tests". Final repro used legacy field names → didn't trigger ref branch. Marked complete.

### `b553ccdd` — 1/8
- Refactor done. `storeSnapshot` aliased back as `type storeSnapshot = StoreSnapshot` for back-compat. Added a NEW exported `cue.ValidateReferences(file, b)` and wired snapshot to call THAT instead of the standard `validator.Validate` (deviation from gold).
- Format string `fmt.Sprintf("flag %s/%s rule %d references unknown segment %q", ns, flag.Key, ruleIdx+1, key)` — 1-based, correct format.
- `addDoc` untouched. Wraps errors as plain `Error{}`; `.Error()` includes ` (file L:C)` suffix → `require.EqualError` will mismatch.
- **No fixture YAMLs.**
- Got `internal/storage/fs` test to print `ok ... 0.045s` — declared done. Never read the FS_Invalid assertion text.

### `f1261115` — 2/8
- Closest-to-gold structure of the three. `SnapshotFromPaths` calls `validator.Validate` per file (matches gold). Removed a duplicate `String()` method.
- Format string `fmt.Sprintf("flag %s/%s rule %d references unknown segment %q", namespace, flag.Key, j+1, key)` — 1-based, correct format.
- `addDoc` untouched; ref checks live elsewhere. Errors are still `newNodeError` returning `Error{}`, so `.Error()` adds ` (file L:C)` suffix.
- **No fixture YAMLs.**
- Ran a `.tmp/repro_validate.go` that printed exactly: `flag default/test rule 1 references unknown segment "missing-segment" (.tmp/repro.yaml 8:14)`. The trailing ` (.tmp/repro.yaml 8:14)` is the suffix that breaks the gold tests' `require.EqualError`.

## Cross-run summary
None of 3 created fixture YAMLs. All 3 left `addDoc` untouched and used `Error{}` whose `.Error()` appends `(file L:C)` — even with fixtures, `require.EqualError` with the bare `flag fruit/apple rule 1 references unknown segment "unknown"` would fail because of the suffix. `b553ccdd` invented `ValidateReferences` (gold doesn't have it) — divergent design. `299da343` had a 0-based off-by-one. Every run's "self-test" used a custom repro script in `/tmp` or `.tmp` rather than reading `snapshot_test.go`'s assertions. None of these 3 reached 5/8.
