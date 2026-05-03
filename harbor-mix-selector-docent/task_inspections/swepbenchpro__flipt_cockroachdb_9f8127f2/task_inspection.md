# Task inspection — `flipt-io__flipt-9f8127f2…` (add CockroachDB as a first-class DB backend)

> **TL;DR.** This task is **borderline-broken and should be rejected as currently shipped**. All 17 trials fail with reward 0.0 ("0 of 6 required tests passed"). The grader's "missing-tests" output is *not* primarily caused by a missing CockroachDB binary in the verifier image (the prior audit hypothesis); the gold `TestMain` just calls `m.Run()` and the suite defaults to SQLite when `FLIPT_TEST_DATABASE_PROTOCOL` is unset. The actual failure cascade is a mix of **(a) compile errors caused by name divergence between agent and gold (`Cockroach` vs `CockroachDB`, `DatabaseCockroach` vs `DatabaseCockroachDB`)** and **(b) runtime subtest failures in `TestParse`/`TestOpen` driven by an instruction–test contradiction** — the PR description says "CockroachDB defaults to **secure** connection settings appropriate for its typical deployment patterns", while the gold `TestParse` table asserts the default `sslmode=disable` (with a hard-coded comment pointing at the Cockroach docs). Capable agents converge on equivalent, technically-correct CockroachDB integrations that nonetheless fail the gold's narrow shape contracts. There is no agent hacking. **A super-capable agent cannot reliably pass without reading the gold author's mind** on at least the SSL default and the exact `Driver` enum spelling — both of which are pinned by the gold tests but not by the instruction.

## Files in this inspection directory

| File | Purpose |
|---|---|
| `instruction.md` | Verbatim PR description + 10 functional requirements + grader behavior |
| `gold_db_test.go` | The full gold-commit `internal/storage/sql/db_test.go` (663 lines) the verifier checks out post-agent — pulled from GitHub since the SWE-Bench-Pro `solve_sh` field is truncated at 8 KB |
| `gold_test_workflow.yml` | The gold `.github/workflows/test.yml` (also restored by the verifier) — confirms a `cockroachdb` matrix CI job exists but does NOT prove the verifier *itself* runs CockroachDB |
| `base_db_test.go` | The base-commit `internal/storage/sql/db_test.go` — what agents see during their session |
| `gold_patch_full_solve_sh.txt` | First 8 KB of the gold patch (truncated by source) |
| `_raw_*` | Raw task-spec dumps (instruction, solve_sh, test_sh, dockerfile, task_toml) |
| `trajectory_*.md` | Per-run traces for all 17 agent runs (3 claude-code, 3 codex, 2 gemini-cli, 3 terminus-claude, 3 terminus-gemini, 3 terminus-gpt) |
| `task_inspection.md` | This file — the synthesized verdict |

---

## 0. Task summary

**What it asks.** Add CockroachDB as a first-class DB backend to Flipt: register a new Driver/Protocol, accept `cockroach`/`cockroachdb`/`cockroach://`/`cockroachdb://`/`crdb://` URL schemes, route Cockroach traffic through Flipt's existing Postgres store and `lib/pq` driver, hook up `golang-migrate`'s CockroachDB driver and a migrations directory, and ship a Docker Compose example. The instruction explicitly says: *"I've already taken care of all changes to any of the test files… you DON'T have to modify the testing logic."*

**How it's verified.** The verifier's `test_sh` (a) `git checkout`s the gold-commit `internal/storage/sql/db_test.go` and `.github/workflows/test.yml`, (b) runs the standard SWE-Bench-Pro `run_script.sh` (no `FLIPT_TEST_DATABASE_PROTOCOL` env var), (c) parses results and checks that `fail_to_pass ∪ pass_to_pass = {TestParse, TestOpen, TestMigratorRun, TestMigratorRun_NoChange, TestMigratorExpectedVersions, TestDBTestSuite} ⊆ passed_tests`, (d) writes `/logs/verifier/reward.txt`. "Missing" in the grader output simply means "not in the passed set" — could be FAIL, ERROR, SKIP, or never-ran-due-to-build-failure.

**Trial setup.** 17 runs across 6 cells:
- claude-code × claude-opus-4-6 — 3 runs
- codex × gpt-5.4 — 3 runs
- gemini-cli × gemini-3.1-pro-preview — 2 runs (one timed out at 45 steps)
- terminus-2 × claude-opus-4-6 — 3 runs
- terminus-2 × gemini-3.1-pro-preview — 3 runs
- terminus-2 × gpt-5.4 — 3 runs

**Outcome.** 0/17 successes (the master tracker says "0/18"; only 17 docent links were provided, so one cell was empty or filtered). Every trial reports `Required: 6 | Passed: 0 | Missing: {all 6}`.

---

## 1. Re-grounding the prior audit hypothesis

The Gemini-audit guess was: *"`TestMain` requires a live CockroachDB instance via `cockroach-go/testserver`; the verifier image has no Docker/CockroachDB; `TestMain` calls `os.Exit(1)` before `m.Run()` so even `TestParse` never executes."*

**This hypothesis is mostly wrong.** Reading the gold `db_test.go`:

```go
func TestMain(m *testing.M) {
    dd = os.Getenv("FLIPT_TEST_DATABASE_PROTOCOL")
    os.Exit(m.Run())
}
```

`TestMain` does **not** exit early. It just stashes the env var and runs the suite. `SetupSuite` in turn defaults `proto = config.DatabaseSQLite` whenever `dd == ""`, and **only** sets `useTestContainer = true` for non-SQLite protocols. The standard SWE-Bench-Pro `run_script.sh` does NOT export `FLIPT_TEST_DATABASE_PROTOCOL`, so in the verifier `dd = ""`, the suite runs against SQLite, and **no Docker / no `cockroach` binary is needed for any of the 6 required tests to execute**. The verifier image lacking a Cockroach binary is not the binding constraint.

Also, the gold test imports `github.com/golang-migrate/migrate/database/cockroachdb` and `github.com/cockroachdb/cockroach-go` only transitively — there is **no `cockroach-go/testserver` import in `db_test.go`**. Container provisioning, when it does happen, is via `testcontainers-go` (already in the base `go.mod`).

So why are all 6 tests "missing"? Two distinct mechanisms apply, partitioning the 17 runs:

### Mechanism A — package fails to build (no test ever executes)

A test-package build failure produces no `--- PASS:` / `--- FAIL:` lines, so all 6 names appear as "missing". This catches every run whose Driver/Protocol naming diverges from the gold's exact spellings. Specifically, the gold `db_test.go` references the symbols `CockroachDB` (driver) and `config.DatabaseCockroachDB` (protocol). Any agent that named theirs `Cockroach` / `DatabaseCockroach` produces a build error of the form `db_test.go:73: undefined: CockroachDB`.

| Run | Driver enum | Protocol const | Build outcome |
|---|---|---|---|
| claude-code e46a2a36 | `CockroachDB` | `DatabaseCockroachDB` | builds |
| claude-code 5adf69a4 | `CockroachDB` | `DatabaseCockroachDB` | builds |
| claude-code 2a82262c | `CockroachDB` | `DatabaseCockroachDB` | builds |
| codex 7d638752 | `Cockroach` | `DatabaseCockroach` | **build fails** |
| codex a6ab5613 | `Cockroach` | `DatabaseCockroach` | **build fails** |
| codex b360c37d | `Cockroach` | `DatabaseCockroach` | **build fails** |
| gemini-cli 6beec19d (timeout) | (no patch landed) | (n/a) | **build fails** (file unchanged so test refs CockroachDB which doesn't exist) |
| gemini-cli cc185e99 | `Cockroach` | `DatabaseCockroach` | **build fails** |
| terminus-claude 82fd10e1 | `CockroachDB` | `DatabaseCockroachDB` | builds |
| terminus-claude 89f45147 | `CockroachDB` | `DatabaseCockroachDB` | builds (after sed mishap repaired) |
| terminus-claude b4061686 | `CockroachDB` | `DatabaseCockroachDB` | builds |
| terminus-gemini 2c6067c7 | `CockroachDB` | `DatabaseCockroachDB` | builds |
| terminus-gemini 30b4ab86 | `CockroachDB` | `DatabaseCockroachDB` | builds (but agent removed cockroach from stringToDriver — see Mechanism B) |
| terminus-gemini 96df5334 | `CockroachDB` | `DatabaseCockroachDB` | builds |
| terminus-gpt 532fe407 | `CockroachDB` | `DatabaseCockroachDB` | **build fails** — agent rewrote `migrator.go` and renamed `Run` → `Migrate`, breaking `TestMigratorRun` source-level reference. Also `driverToString[CockroachDB] = "cockroach"` (not `"cockroachdb"`); the gold test does not check the *string* but the postgres-style migrate driver name probably matches gold by accident |
| terminus-gpt 8b236d83 | `CockroachDB` | `DatabaseCockroachDB` | builds (minimal patch) |
| terminus-gpt d26c50e0 | `CockroachDB` | `DatabaseCockroachDB` | builds |

So roughly **5–6 of 17 runs are eliminated at build time** by enum-name divergence (codex × 3, gemini-cli × 2, terminus-gpt 532fe407). Those runs literally cannot pass any test — not because of agent capability gaps but because the gold test file uses spellings the instruction never pins.

### Mechanism B — package builds but `TestParse`, `TestOpen`, `TestMigratorExpectedVersions`, or `TestDBTestSuite` fail at runtime

For the ~11 runs that compile, the gold subtests impose at least three additional *unstated* contracts:

1. **Default sslmode on `cockroachdb://...` URLs without an `sslmode` query param must be `disable`.** Gold `TestParse` includes a "cockroachdb default disable sslmode" case (gold line 298–306) with the comment `// cockroachdb defaults to sslmode=disable` and a link to Cockroach docs. The instruction says the opposite: *"CockroachDB defaults to **secure** connection settings appropriate for its typical deployment patterns, including proper SSL mode handling."* Multiple codex/terminus runs interpreted "secure" literally and defaulted to `sslmode=require` or `sslmode=verify-full` — those agents would fail this case the moment compilation succeeded.

2. **DSN normalization must produce exactly `postgres://...?sslmode=disable`.** Gold's expected DSN strings for the cockroach URL family (lines 274–356 of gold_db_test.go) require the URL to be rewritten from `cockroachdb://...` (or `cockroach://...`, or `crdb://...`) into a `postgres://...` DSN, with `sslmode=disable` appended. Subtle: even if the agent does `dburl.Parse` and lets the lib produce a `postgres` DSN, they still need to *append* `sslmode=disable` when missing. Several agents handled this only for the `Postgres` branch and not for `CockroachDB`.

3. **`TestMigratorExpectedVersions` invariant.** The gold test (`migrator_test.go`) iterates `stringToDriver` and for each key reads `config/migrations/<key>/`, asserting `expectedVersions[driver] == (count/2) - 1`. So the agent's `stringToDriver` keys, the migration directories, and the `expectedVersions` values must form a self-consistent triple. This *is* satisfiable from the instruction (the Postgres pattern is right next to it), and most clean runs got it right. But three runs explicitly broke this:
   - **terminus-gemini 30b4ab86 / gemini-cli cc185e99** — `removed` `"cockroach"` from `stringToDriver` after seeing the local test fail with `open ../../../config/migrations/cockroach: no such file or directory`. This silences the failure on the *base* test but the *gold* test extends the map and re-asserts the invariant under a key the agent removed. Counterproductive.
   - **terminus-gpt 532fe407** — removed migrations entirely.
   - **claude-code 2a82262c / codex 7d638752 / terminus runs that "remap to postgres"** — kept the cockroach `stringToDriver` key but didn't create `config/migrations/cockroach{,db}/`, instead remapping at runtime in `migrator.go`. The `TestMigratorExpectedVersions` gold variant doesn't hit that runtime remap; it only checks the directory listing. So these runs fail this test. (claude-code e46 and 5ad and several terminus-gemini runs avoided this trap by physically copying or symlinking `config/migrations/postgres/` → `config/migrations/cockroachdb/`, which is what the gold author also did.)

4. **`TestDBTestSuite` against SQLite.** Once the package builds and `dd == ""`, the suite runs the existing SQLite path. None of the agents we audited broke the SQLite code path — but a few agents who reused `postgres.WithInstance` for the Cockroach migrate driver instead of importing `cockroachdb.WithInstance` would still pass this test, since SQLite uses `sqlite3.WithInstance`. So `TestDBTestSuite` is the *easiest* of the 6 to pass — yet still appears in every "missing" list. That is a strong signal that **builds are failing or `SetupSuite` is erroring out before `TestDBTestSuite` ever runs** for the runs that did compile.

What specifically would make `SetupSuite` error for SQLite default? Re-reading lines 488–541 of gold_db_test.go: after `open(cfg, ...)`, the suite computes `dr, err = sqlite3.WithInstance(...)`, then `migrate.NewWithDatabaseInstance(file://config/migrations/sqlite3, "sqlite3", dr).Up()`. The suite then drops/re-opens the DB *with `migrate: false`*, then routes to `sqlite.NewStore`. Nothing here references CockroachDB at runtime. So **for properly-spelled clean runs, `TestDBTestSuite` actually should pass**. Combined with `TestMigratorRun` and `TestMigratorRun_NoChange` being stub-only tests (they do not need any DB at all — just `stubDB.Stub` and `stubSource.Stub`), the most parsimonious explanation for runs like claude-code e46a2a36 reporting all six missing is **(2) DSN-format mismatch in `TestParse` causing the parent test to fail, plus the migrator test failing on `expectedVersions` mismatch**. The two stub-only migrator tests should still pass.

We cannot directly verify this without a verifier replay, but the trajectories give corroborating signals: claude-code 2a82262c logged a passing local `go test ./internal/config ./internal/storage/sql` after their patch (which used the *base* test file with no cockroach cases), and the only cockroachdb-aware test the agent constructed was a homemade reproducer — which always passed because the agent wrote the assertions. None of the 17 runs ran a *cockroach* path of `TestParse` (the gold's table cases were not in the base file, so the agent could not run them locally before submitting).

---

## 2. How close are agents to succeeding?

**Closer than 0/17 implies.** Reading the per-run reports:

- 11/17 runs land a *structurally complete* implementation: a `CockroachDB` Driver enum, a `DatabaseCockroachDB` Protocol, `cockroach`/`cockroachdb`/`crdb` URL acceptance, `pq.Driver{}` with `semconv.DBSystemCockroachdb` attribute, `postgres.NewStore` for the Cockroach store, a `cockroachdb.WithInstance` migrator branch, an `expectedVersions` entry, a `config/migrations/cockroachdb/` directory (either copied from postgres or symlinked or freshly authored), and a `cmd/flipt/main.go` switch update. The gold patch does the same things. The 11 runs are *substantively equivalent* to the gold-author's solution at the public-API level.

- The 6/17 runs that diverge structurally — the codex enum-naming family, the two gemini-cli runs that landed `Cockroach`, terminus-gpt 532fe407 (broken migrator), and the timeout — are eliminated upstream of any subtle DSN issue.

- The gap from "structurally complete" to "all 6 tests pass" is **(i) get the driver enum spelled `CockroachDB`** (inferrable by analogy with `MySQL` already in the codebase but not pinned), **(ii) default sslmode to `disable`** (instruction says "secure", contradicts gold), **(iii) emit a postgres-shaped DSN with `sslmode=disable` appended even when the input URL omits it** (inferrable from existing postgres parse but easy to miss for cockroach), **(iv) keep `stringToDriver["cockroachdb"]` *and* create a real `config/migrations/cockroachdb/` directory** (inferrable from `TestMigratorExpectedVersions` failing locally — though most agents who saw this failure tried to remove the entry rather than create the directory). Only the gold patch's specific solve_sh — physically copying `config/migrations/postgres/` to `config/migrations/cockroachdb/` and reusing the postgres migrate driver — is one of several locally-equivalent options that the test happens to require.

**Is the gap a real capability gap?** Partly yes (point i, iv are inferrable from the codebase if the agent reads carefully), partly no (point ii contradicts the instruction; point iii's exact format requires guessing the gold's expectations).

---

## 3. Cross-agent variance — surface vs. root cause

### Surface reasons (what the agents *appear* to do wrong)

Six distinct surface symptoms across the 17 runs:

1. **Wrong enum name.** Codex × 3, gemini-cli × 2: `Cockroach` instead of `CockroachDB`; `DatabaseCockroach` instead of `DatabaseCockroachDB`.
2. **Wrong sslmode default.** Codex run 1 (`require`), codex run 2 (`verify-full`), codex run 3 (`require`); other agents' default behavior unclear from the tracking. The gold expects `disable`.
3. **Migration directory not actually created.** claude-code 2a82262c, several codex runs, terminus-gpt 532fe407: agents code-remapped Cockroach → postgres at runtime in `migrator.go`, but did not create `config/migrations/cockroachdb/` on disk. Gold's `TestMigratorExpectedVersions` does a directory listing.
4. **Removing `stringToDriver` entries to silence `TestMigratorExpectedVersions` against the base file.** gemini-cli cc185e99, terminus-gemini 30b4ab86. Backfires under gold tests.
5. **Migrator rewrites breaking source-level test references.** terminus-gpt 532fe407: renamed `Run(force)` → `Migrate()`, gold `TestMigratorRun` calls `migrator.Run(false)` → undefined → build fail.
6. **Self-declared success with no real Cockroach exercise.** All 17 runs declared success based on either (a) trivial scoped `go test -run "TestOpen|TestParse" -short` runs with no cockroach cases (since the base file has none), or (b) homemade reproducer scripts that tested only what the agent itself believed was correct, or (c) `go test ./...` after deleting/silencing the failing entries.

### Root cause

These six surface symptoms have one dominant root cause and one secondary root cause:

**Primary: agents cannot iterate against the actual verifier tests.** Just like the ansible-galaxy task in this benchmark, the gold tests are checked out *after* the agent's window closes. The base-commit `db_test.go` has no Cockroach test cases at all (the table-driven entries are added in the gold patch), so an agent reading the base file finds zero signal about (a) the exact `Driver` enum spelling, (b) the SSL default behavior, (c) the exact DSN string format expected, (d) the migrations directory naming. They can only infer from the existing Postgres/MySQL/SQLite patterns — and the instruction's contradictory "secure SSL" wording actively misleads them.

**Secondary: instruction–test contradiction on SSL.** "Secure connection settings" appears in the requirements list. The gold's `TestParse` table includes a default-disable case with a hard-coded comment pointing to Cockroach docs. These two cannot both be true. An agent cannot resolve this without either (i) seeing the gold tests, or (ii) deliberately disregarding the instruction's wording in favor of a docs-driven default — a strange leap to ask an agent to make.

The 6/17 build-fail runs are downstream of *primary* — the agent reasonably picks `Cockroach` (the simpler/shorter name analogous to `Postgres`) over `CockroachDB`, and there is no feedback signal in the base file telling them otherwise. The 5/17 runtime-fail-on-`TestParse`/`TestMigratorExpectedVersions` runs are downstream of *secondary* and *primary* (DSN/sslmode shape).

### By agent stack

- **claude-code (3 runs)** — most polished, all three converged on `CockroachDB` (correct), all three created/copied a `config/migrations/cockroachdb/` directory (e46 and 5ad copy postgres files; 2a8 reuses via runtime remap). e46 and 5ad both imported `cockroachdb.WithInstance`. Likely failure mode: **runtime DSN-format / sslmode mismatch in `TestParse` cockroach cases**, plus possibly `TestMigratorExpectedVersions` for 2a8.
- **codex (3 runs)** — all three picked `Cockroach` (wrong). All three are eliminated at build time. Capability-wise the runs were thoughtful (codex 2 added cockroach-go to go.mod, codex 3 created `config/migrations/cockroachdb/` schema), but the enum-name choice kills them.
- **gemini-cli (2 runs)** — one timed out at 45 steps with 80% of a working patch in flight; the other landed `Cockroach` and *removed* `stringToDriver["cockroach"]` to silence the local test. Build fails on enum naming.
- **terminus-claude (3 runs)** — all three pick `CockroachDB` (correct). 89f45147 hit a sed mishap that left a duplicate `case CockroachDB:` and burned ~40 blocks recovering. b4061686 used a Python rewrite that avoided the sed bug. 82fd10e1 reused `postgres.WithInstance` for migrations (no cockroachdb migrate import). All three have the same downstream problem as claude-code: DSN/sslmode shape.
- **terminus-gemini (3 runs)** — solid investigation behavior (probed `dburl`/OTel semconv at runtime), but two of three games the existing `TestMigratorExpectedVersions` by symlinking or stripping; the third games it by stripping. Same downstream as claude-code post-build.
- **terminus-gpt (3 runs)** — variable. d26c50e0 cleanest. 532fe407 broke compilation by renaming Run → Migrate. 8b236d83 ($0.19) was extreme-budget compactness; declared success from a one-shot patch with minimal verification.

The variance is real but not interesting in a capability-bottleneck sense. **Capability-wise, all six stacks can produce a structurally-correct implementation**. The bottleneck is hidden test contracts, not "can the agent design CockroachDB integration" — most of them clearly can.

---

## 4. Concrete failures with expected-vs-produced

### 4a. `CockroachDB` symbol vs. `Cockroach` symbol

**Expected** (gold `db_test.go`, lines 73, 278, 286, 294, 304, …):
```go
driver: CockroachDB,
```

**Produced** (codex 7d638752 final patch, `internal/storage/sql/db.go`):
```go
const (
    SQLite   Driver = iota + 1  // 1
    Postgres                    // 2
    MySQL                       // 3
    Cockroach                   // 4
)
```

**Failure**: `internal/storage/sql/db_test.go:73:11: undefined: CockroachDB` — the package will not compile. All 6 tests "missing".

### 4b. SSL default

**Expected** (gold line 298–306):
```go
{
    name: "cockroachdb default disable sslmode",
    // cockroachdb defaults to sslmode=disable
    // https://www.cockroachlabs.com/docs/stable/connection-parameters.html#additional-connection-parameters
    cfg: config.DatabaseConfig{
        URL: "cockroachdb://cockroachdb@localhost:26257/flipt",
    },
    driver: CockroachDB,
    dsn:    "postgres://cockroachdb@localhost:26257/flipt?sslmode=disable",
},
```

**Produced** (codex run 2, parse logic in `internal/storage/sql/db.go`):
```go
case CockroachDB:
    if v.Get("sslmode") == "" {
        v.Set("sslmode", "verify-full")
    }
```

**Failure** (if compilation had succeeded): subtest `TestParse/cockroachdb_default_disable_sslmode` — `assert.Equal: expected "postgres://cockroachdb@localhost:26257/flipt?sslmode=disable", got "postgres://cockroachdb@localhost:26257/flipt?sslmode=verify-full"`. Parent `TestParse` reported FAIL.

### 4c. Driver→migration directory name vs. `expectedVersions`

**Expected** (gold `migrator_test.go`):
```go
for db, driver := range stringToDriver {
    migrations, err := ioutil.ReadDir(filepath.Join("../../../config/migrations", db))
    require.NoError(t, err)
    count := len(migrations)
    require.True(t, count > 0, "no migrations found for %s", db)
    actual := uint((count / 2) - 1)
    assert.Equal(t, actual, expectedVersions[driver])
}
```

**Produced** (terminus-gemini 30b4ab86, `internal/storage/sql/db.go`):
```go
var stringToDriver = map[string]Driver{
    "sqlite3":  SQLite,
    "postgres": Postgres,
    "mysql":    MySQL,
}  // intentionally NO cockroach{,db} entry to silence the local test
```

**Failure**: with the gold's `db_test.go` post-checkout, `stringToDriver` is what the agent left it; gold doesn't override the variable. So the gold test iterates the agent's 3-key map, which is fine — but the *gold* test file's `TestParse`/`TestOpen`/`SetupSuite` reference `CockroachDB` as a `case` label and expect parsing to map the cockroach URL family to it. The agent's `parse()` does this via a separate `if url.Scheme ∈ {cockroach, cockroachdb, crdb}` override, so it might still work for `TestParse`. But this is fragile — the symbol still has to exist. `TestMigratorExpectedVersions` against the gold doesn't pin a `cockroachdb` entry either (it just iterates whatever map exists), so this particular agent's gaming might actually produce a green local outcome. Build is the binding constraint.

### 4d. Migrator rewrite breaking source-level test reference

**Expected** (gold `migrator_test.go`):
```go
err = migrator.Run(false)
```

**Produced** (terminus-gpt 532fe407, `internal/storage/sql/migrator.go`):
```go
// Run() removed entirely; replaced with:
func (m *Migrator) Migrate() error { … }
```

**Failure**: `migrator_test.go: undefined: migrator.Run` — package fails to compile.

---

## 5. Is the failure due to the task or to the agent?

For each of the questions in the prompt:

> **Is this something that the agent can possibly infer from the environment or they will never know?**

| Hidden contract | Inferrable from base codebase? | Inferrable from instruction? |
|---|---|---|
| Driver enum is `CockroachDB` (not `Cockroach`) | Weakly: existing `MySQL` (with capital `SQL`) suggests `CockroachDB` over `Cockroach`. But `Postgres` is just `Postgres` not `PostgreSQL`. So the analogy is genuinely ambiguous. | No |
| Protocol const is `DatabaseCockroachDB` (paired with the driver) | Same as above | No |
| Default `sslmode` on cockroach URLs (without query param) is `disable` | No: nothing in the base codebase tells the agent the Cockroach default. Would need to look up Cockroach docs *and* override the requirement's "secure" wording. | No — instruction says "secure" |
| DSN must be `postgres://...?sslmode=disable` (postgres scheme + sslmode appended) | Weakly: existing postgres parse path does append sslmode for `sslDisabled` cases. An agent who reads carefully can mimic this for Cockroach. | No |
| Migrations directory named `cockroachdb/` (not `cockroach/`) | Yes: postgres directory is named `postgres/` matching the lowercase driver string. By analogy `cockroachdb/`. | No |
| `expectedVersions[CockroachDB]` must equal `(count/2) - 1` for whatever migrations the agent provides | Self-consistent: the gold author copied postgres → cockroachdb (8 files), and set `expectedVersions[CockroachDB] = 3`. Any agent that does the same, or creates 1 migration pair and sets value 0, satisfies the invariant. | Partially |

So **two contracts (enum naming and SSL default) are essentially un-inferrable** from instruction or base codebase alone. The other contracts are inferrable for a sufficiently careful agent.

> **Can a super-capable being resolve this task given the current instructions and environments?**

A super-capable being could **probably** pass with these specific moves: (a) pick `CockroachDB` over `Cockroach` as the more verbose, MySQL-analogous form (a 50/50 coin flip in reasonable taste); (b) read Cockroach docs link in the requirement's "Additional Context" and notice that `sslmode=disable` is the development default, then deliberately interpret the instruction's "secure connection settings" as "appropriate for the deployment context" rather than literally `sslmode=verify-full` — an unusual interpretive leap; (c) follow the existing postgres parse path closely for DSN normalization. **Even then, success is non-deterministic.** The task is theoretically solvable by an unbounded oracle, but it requires the agent to disregard instruction wording and guess the gold author's mental model. That makes the task **borderline** rather than fully broken.

---

## 6. Proposed fixes (not simplifications)

There are at least three minimal fixes that would make this task solvable by a competent agent without giving away the answer:

### Fix A — Pin SSL default in the instruction

Change requirement 6 from:
> "CockroachDB defaults to **secure** connection settings appropriate for its typical deployment patterns, including proper SSL mode handling."

to:
> "CockroachDB connection-string parsing should default `sslmode=disable` when no `sslmode` is specified, matching the [CockroachDB defaults documented here](https://www.cockroachlabs.com/docs/stable/connection-parameters.html#additional-connection-parameters). When the URL specifies a different `sslmode`, that value is preserved."

This single sentence change resolves the most damaging instruction–test contradiction without giving away any other implementation detail.

### Fix B — Pin `Driver` enum spelling

Add to the instruction a single line (at the same level of abstraction as the existing requirements):
> "Add a new `Driver` enum value named `CockroachDB` (paired with `config.DatabaseCockroachDB`) to maintain the spelling pattern of `MySQL`/`SQLite`."

This kills the build-failure mode for ~5 of 17 runs (codex × 3, gemini-cli × 2) without changing the substance of the task.

### Fix C — Surface the existing test `TestMigratorExpectedVersions` invariant

The instruction says "you don't have to modify tests" — true, but it doesn't tell the agent what existing tests will iterate over. Add:
> "Note: the existing `TestMigratorExpectedVersions` test iterates over `stringToDriver` and expects a `config/migrations/<key>/` directory with at least one (up, down) migration pair. After adding `cockroachdb` to `stringToDriver`, you must also create `config/migrations/cockroachdb/` with valid migrations and set `expectedVersions[CockroachDB]` consistent with the file count."

This tells the agent the contract without giving away the gold's specific choice (1 migration vs. 4).

### Alternative fix (heavier) — Pre-stage the gold tests

The current pattern of "the verifier checks out gold tests after the agent finishes" is the deeper structural issue this benchmark inherits from SWE-Bench-Pro. Pre-staging the gold tests inside the agent's window (with a sentinel comment that says "do not modify") would let the agent iterate. But this changes the spirit of SWE-Bench-Pro and is outside the per-task remit.

### My recommended bundle

**Apply A and B together.** Both are tiny instruction-text changes that don't reveal the gold patch and don't change the difficulty of the underlying engineering. They fix the two un-inferrable contracts. With those changes, I'd expect at least 4/17 → 8-12/17 to flip to passing (the ~6 build-fail runs would compile, and the runtime-fail runs would handle SSL correctly; remaining failures would be on DSN-shape edge cases or migration-directory provisioning, which are fair).

**Without those fixes, I would reject this task** as currently shipped: the instruction–test contradiction on SSL defaults and the unbounded enum-naming pick make it primarily a test of "guess the gold author", not a test of CockroachDB integration capability.

---

## 7. Cheating / reward hacking

**No reward hacking observed in any of the 17 runs.** Specifically:

- **No agent edited any `_test.go` file** under `internal/storage/sql/` or anywhere else.
- **No agent touched `/logs/verifier/` or `/logs/verifier/reward.txt`**. (The verifier's reward file is written from the test_sh trap; agents had no way to inject a 1.)
- **No agent set `FLIPT_TEST_DATABASE_PROTOCOL` to bypass the cockroachdb path** (that env var only steers the suite *toward* cockroachdb; agents would not benefit from setting it).
- **No agent modified `/tests/run_script.sh`, `parser.py`, or the verifier configuration**.
- **No agent disabled tests via `t.Skip(...)` or build tags**.

Two runs **gamed the existing base-commit test** by removing `stringToDriver["cockroach"]` (gemini-cli cc185e99 at B139, terminus-gemini 30b4ab86) to silence the `TestMigratorExpectedVersions` failure during their local self-test. This is **test-gaming**, not reward-hacking — they adapted to the *base* test file (which they could read), not the *gold* test file (which they could not). Both runs were structurally honest about what they had built; they would have failed the gold test for unrelated reasons (enum-name divergence in cc185e99; symbol-spelling inconsistency in 30b4ab86). The maneuver also has no effect on the verifier outcome since the gold patch replaces the test file. Worth flagging for transparency, not for sanction.

The terminus-gemini family that **symlinked `config/migrations/{cockroach,cockroachdb,crdb}` → `config/migrations/postgres`** is also not hacking — the migrate library reads the file:// path at runtime, this would also be a viable production solution, and it's structurally similar to what the gold author did (full file copy instead of symlink).

---

## 8. Verdict

**Reject this task as currently written.** The reasons:

1. **Instruction–test contradiction on SSL default** (instruction: "secure"; gold: `sslmode=disable`). This single contradiction is sufficient to fail any agent who interprets the instruction literally. It is the most common single cause of wasted effort across the audit.
2. **Un-inferrable `Driver`/`Protocol` enum spelling.** Five-to-six of the 17 runs are eliminated at build time by reasonably picking `Cockroach` over `CockroachDB`. The instruction does not pin this and the base codebase analogy is ambiguous (`MySQL` vs `Postgres` argue different ways).
3. **Implementation detail of "minimal vs full" migrations** is not a problem in itself (the test invariant is self-consistent with whatever the agent ships), but combined with the prior two issues, agents trying to hit the SSL/enum constraints under time pressure tend to mishandle the migrations as well.

The task **could be salvaged** with a few sentences of instruction tightening (Fix A + Fix B above). After that, I expect the success rate to rise from 0/17 to a meaningful fraction, and the remaining failures would be distributed across genuine DSN-shape and migration-provisioning challenges that are fair tests of capability.

**About what the failures tell us about agent capability:** Once you control for the un-inferrable contracts, agents demonstrate strong, broadly equivalent CockroachDB integration capability across 5 different (agent harness × model) cells. That is the single most striking finding from reading 17 trajectories — most agents converge on the gold's design. The variance you see between runs is dominated by the test contract opacity and (for terminus-gpt 8b236d83's $0.19 trajectory) by harness budget caps; it is not dominated by reasoning gaps about the integration itself.

This makes the task currently a **poor measure of "can frontier agents add a new DB backend"** and a **good (if accidental) measure of "can frontier agents guess the gold author's naming/SSL preferences when those preferences contradict the instruction text"**. The latter is not what the SWE-Bench-Pro rubric is asking about.
