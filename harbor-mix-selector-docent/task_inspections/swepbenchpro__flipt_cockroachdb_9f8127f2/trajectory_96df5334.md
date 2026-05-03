# Run 96df5334 — Flipt CockroachDB (terminus-2 × gemini-3.1-pro-preview, $0.62, reward 0.0)

59 transcript blocks, the cheapest of the gemini-pro runs but the most thorough on the documentation requirement. Mirror image of run 2c6067c7: same code-side decisions, plus the requested `examples/cockroachdb` directory.

## 1. What the agent built

Final `git status` (B50): `go.mod`, `go.sum`, `internal/config/database.go`, `internal/storage/sql/db.go`, `internal/storage/sql/migrator.go`. Untracked: `config/migrations/{cockroach,cockroachdb,crdb}` (symlinks to `postgres`), `examples/cockroachdb/` (Dockerfile, README.md, docker-compose.yml). The agent also created and later deleted scratch `patch.py`, `test_dburl*.go`, `test_semconv.go`, `update_compose.py`, `update_readme.py` files.

Specifically:
- `internal/config/database.go` — added `DatabaseCockroach`, `databaseProtocolToString[DatabaseCockroach] = "cockroachdb"` (or `"cockroach"`), with `stringToDatabaseProtocol` accepting `"cockroach"`, `"cockroachdb"`, `"crdb"`.
- `internal/storage/sql/db.go` — `Cockroach` enum, accepted aliases in `stringToDriver`. In `parse()`, after `dburl.Parse`, the agent overrides `driver = Cockroach` based on `url.URL.Scheme` matching `cockroach`/`cockroachdb`/`crdb`. In `open()`: `case Cockroach: dr = &pq.Driver{}; attrs = []attribute.KeyValue{semconv.DBSystemCockroachdb}` (verified the OTel semconv constant exists in v1.4.0).
- `internal/storage/sql/migrator.go` — imported `cockroachdb` driver, `Cockroach: 3` in `expectedVersions`, `case Cockroach: dr, err = cockroachdb.WithInstance(sql, &cockroachdb.Config{})`. Likely also rerouted the migrations path to `postgres` for Cockroach (consistent with the symlink approach).
- `cmd/flipt/{main,import,export}.go` — `case sql.Cockroach:` → `postgres.NewStore`.
- `go.mod`/`go.sum` — `go get github.com/cockroachdb/cockroach-go/crdb` plus `go mod tidy` pulled in `cockroach-go v2.0.1+incompatible`.
- `config/migrations/{cockroach,cockroachdb,crdb}` — three symlinks to `postgres/`, added to make the existing `TestMigratorExpectedVersions` pass when its loop covers all three aliases.
- `examples/cockroachdb/{Dockerfile,docker-compose.yml,README.md}` — new directory copied from `examples/postgres` and rewritten for CockroachDB (`cockroachdb/cockroach:latest`, `start-single-node --insecure`, `FLIPT_DB_URL=cockroach://root@cockroachdb:26257/defaultdb?sslmode=disable`).

## 2. Did it open `internal/storage/sql/db_test.go`? Did it see CockroachDB live-server bootstrap?

No direct read. The agent only opened `migrator_test.go` while debugging `TestMigratorExpectedVersions`. It never inspected `db_test.go`, never noticed `newDBContainer` / `cockroach-go/testserver`, and never installed Cockroach or added a testcontainer/docker-compose service for the verifier.

## 3. Did it inspect `.github/workflows/test.yml`?

No. CI workflow was never opened.

## 4. Local Go tests

Yes. Found `/usr/local/go/bin/go`, ran multiple targeted `go test ./internal/config/... ./internal/storage/sql/...` passes. After hitting `TestMigratorExpectedVersions: open ../../../config/migrations/cockroachdb: no such file or directory` (and subsequently the same for `cockroach` and `crdb`), the agent created three symlinks under `config/migrations/` pointing to `postgres`. After symlinks: `go test ./internal/storage/sql` returned `ok ... 3.118s`. The transcript shows `TestParse`, `TestOpen`, `TestMigratorRun`, `TestMigratorRun_NoChange`, and `TestDBTestSuite` (subset, with two `TestDeleteSegment_ExistingRule` / `TestDeleteVariant_ExistingRule` skips) all PASS in the `-v` output (B34 — the suite ran with the existing `db_test.go`, sqlite3 only).

## 5. Surface failure in the verifier

When the verifier swaps in the gold `db_test.go`, `TestMain`/`SetupSuite`/`newDBContainer(... DatabaseCockroachDB)` triggers `cockroach-go/testserver.NewTestServer()`, which needs a `cockroach` binary in $PATH. The verifier image has no Cockroach binary, so `TestMain` exits before the test functions run, and all six required tests appear as "missing". Possible additional failure: the agent's `go.mod` pinned `cockroach-go v2.0.1+incompatible` (which provides `cockroach-go/crdb`); the gold likely uses `cockroach-go/v2/testserver`, a different module path, so the package may not even compile under the gold test file.

## 6. Root cause

(b) Gold `TestMain` requires a live CockroachDB instance via `cockroach-go/testserver`, which cannot be started without a `cockroach` binary in the verifier image. Likely compounded by (c) — `cockroach-go` module path / version mismatch between agent's go.mod and gold's imports.

## 7. Cheating / reward hacking

None. No `_test.go` edits, no `/logs/verifier/` access, no reward.txt manipulation. Symlinks under `config/migrations/` are migration assets (not test files) and are a legitimate way to satisfy a code-driven directory iteration. The agent did not delete or short-circuit any test logic.

## 8. Self-declared success?

Yes. At B55 the agent declared all requirements satisfied and called `mark_task_complete()`, citing the locally-passing `internal/config` and `internal/storage/sql` tests as evidence. It re-confirmed at B57. The agent never realized the verifier replaces `db_test.go` with a gold version that requires CockroachDB to be running.
