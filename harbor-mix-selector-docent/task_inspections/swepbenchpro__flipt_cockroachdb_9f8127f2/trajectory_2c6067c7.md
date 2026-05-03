# Run 2c6067c7 — Flipt CockroachDB (terminus-2 × gemini-3.1-pro-preview, $0.76, reward 0.0)

79 transcript blocks, the most expensive of the three gemini runs. The agent eventually got every existing test passing (besides the unrelated Redis docker tests) but still scored 0 because the gold test file replaces the in-tree tests at verify time.

## 1. What the agent built

Final modifications:
- `internal/config/database.go` — added `DatabaseCockroachDB` enum constant; `databaseProtocolToString[DatabaseCockroachDB] = "cockroach"` (initially "cockroachdb", later changed to "cockroach" out of caution about dburl); `stringToDatabaseProtocol` accepts `"cockroach"`, `"cockroachdb"`, `"crdb"`.
- `internal/storage/sql/db.go` — added `Cockroach` to the `Driver` enum, with `driverToString[Cockroach] = "cockroach"` and `stringToDriver` accepting `"cockroach"`, `"cockroachdb"`, `"crdb"`. In `open()`: `case Cockroach: dr = &pq.Driver{}; attrs = []attribute.KeyValue{semconv.DBSystemCockroachdb}` (which it confirmed the OTel semconv package actually exposes). In `parse()`, after `dburl.Parse`, it explicitly checks `url.URL.Scheme == "cockroach" || "cockroachdb" || "crdb"` and overrides `driver = Cockroach`. SSL/sslmode handling collapsed `case Postgres, Cockroach:`.
- `internal/storage/sql/migrator.go` — imported `github.com/golang-migrate/migrate/database/cockroachdb`, added `Cockroach: 3` to `expectedVersions`, added `case Cockroach: dr, err = cockroachdb.WithInstance(sql, &cockroachdb.Config{})`. Migration directory is mapped: `migPath := driver.String(); if driver == Cockroach { migPath = "postgres" }`. `migrate.NewWithDatabaseInstance(..., driver.String(), dr)` keeps the `cockroach` name.
- `cmd/flipt/{main,import,export}.go` — added `case sql.Cockroach: store = postgres.NewStore(db, logger)`.
- `examples/cockroachdb/{docker-compose.yml,README.md,Dockerfile}` — new directory copied from `examples/postgres` and rewritten for CockroachDB (`cockroachdb/cockroach:latest-v22.2`, `start-single-node --insecure`, `FLIPT_DB_URL=cockroach://root@cockroachdb:26257/defaultdb?sslmode=disable`).
- `go.mod` / `go.sum` — modified by `go get github.com/cockroachdb/cockroach-go/crdb` plus `go mod tidy`. The agent pulled in `github.com/cockroachdb/cockroach-go v2.0.1+incompatible` to satisfy the golang-migrate cockroachdb driver dependency.
- `config/migrations/{cockroach,cockroachdb,crdb}` — three symlinks pointing at `postgres/`, added so the existing `TestMigratorExpectedVersions` (which iterates `stringToDriver` and `ioutil.ReadDir`s `config/migrations/<key>`) passes.

## 2. Did it open `internal/storage/sql/db_test.go`? Did it see CockroachDB live-server bootstrap?

No. The agent grepped the file for `postgres` references and inferred its structure from the matches it saw, but never `cat`d the file. It never noticed the `newDBContainer`/`testcontainers` plumbing, never saw that the gold version uses `cockroach-go/testserver`, and never looked at the actual `TestMain`/`SetupSuite`. It treated the package's tests as a black box that should keep passing under its existing logic.

## 3. Did it inspect `.github/workflows/test.yml`?

The early grep surfaced `./.github/workflows/test.yml:71:        database: ["mysql", "postgres"]` (block B2), but the agent did not open the file or modify it. The CI matrix hint that gold restores was missed.

## 4. Local Go tests

Yes. Found `/usr/local/go/bin/go`, exported PATH, and ran `go run` snippets to probe `xo/dburl` (got `Driver: postgres, Scheme: cockroach`) and `golang-migrate/migrate/database/cockroachdb` (initially missing the `cockroach-go/crdb` module, fixed via `go get` + `go mod tidy`). After the patches it ran `go build ./...` (failed because of leftover `test_*.go` mains, then succeeded after deletion), then `go test ./...` — `internal/config` and `internal/storage/sql` both passed; only `server/cache/redis` failed due to missing Docker daemon. It did NOT run any `TestParse`/`TestOpen`/`TestDBTestSuite` against a real Cockroach instance — those tests in the base file have no Cockroach subtests.

## 5. Surface failure in the verifier

When the verifier `git checkout`s the gold `db_test.go` and `.github/workflows/test.yml`, the new tests pull in `cockroach-go/testserver` (or similar) and the `TestMain`/`SetupSuite` calls `newDBContainer(... DatabaseCockroachDB)` — there is no `cockroach` binary in the verifier image, so the test process exits early during package init and every test in the file shows as "missing" (not "failed"). The package may also fail to compile if the gold test imports a different cockroach-go module path than the agent's `go.mod` (the agent locked `cockroach-go v2.0.1+incompatible`; gold likely uses `cockroach-go/v2/testserver`).

## 6. Root cause

(b) Gold `TestMain` requires a live CockroachDB and the verifier image lacks the binary. Possibly compounded by (c) — the agent's `go.mod` uses `github.com/cockroachdb/cockroach-go v2.0.1+incompatible` (legacy import path `cockroach-go/crdb`) whereas the gold imports `cockroach-go/v2/testserver`, which is a distinct module. When gold's test file is dropped on top, `go test` may fail to compile the package, presenting as build error → all tests missing.

## 7. Cheating / reward hacking

None. No `_test.go` edits, no `/logs/verifier/` access, no reward.txt manipulation. Symlinking `config/migrations/{cockroach,cockroachdb,crdb} -> postgres` is a plausible production fix (the migrate library reads the file:// path), not test cheating; the gold test's iteration of `stringToDriver` would need the same files anyway.

## 8. Self-declared success?

Yes. At B71 the agent listed all 10 PR requirements as satisfied and called `mark_task_complete()`. After a brief reconsideration (changed `databaseProtocolToString[DatabaseCockroachDB]` from `"cockroachdb"` to `"cockroach"` and reran tests at B73), it confirmed PASS again at B77. The local test evidence was real (`internal/storage/sql` passed) but irrelevant to the gold verifier.
