# Run outcomes — flipt-CockroachDB (`instance_flipt-io__flipt-9f8127f225a86245fa35dca4885c2daef824ee55`)

All 17 runs report the same grader output (token-for-token):

```
Required tests: 6
Passed tests: 0
Required tests that passed: 0
RESULT: FAILED
Missing tests: ['TestMigratorExpectedVersions', 'TestOpen', 'TestParse',
                'TestMigratorRun_NoChange', 'TestDBTestSuite', 'TestMigratorRun']
```

Note: order of "Missing" varies (Python set ordering); the set is identical.

## Trial matrix

| # | Run ID | Agent | Model | Steps | Cost | Driver enum picked | Outcome category |
|---|---|---|---|---|---|---|---|
| 1 | `e46a2a36-2752-47a7-a446-f630daecf5a3` | claude-code | claude-opus-4-6 | 87 | n/a | `CockroachDB` | builds; runtime DSN/sslmode shape |
| 2 | `2a82262c-09cf-4f66-b029-a2009d6e1d3d` | claude-code | claude-opus-4-6 | 69 | n/a | `CockroachDB` | builds; missing `config/migrations/cockroachdb/` directory |
| 3 | `5adf69a4-9d56-46fd-ba1a-09aa4a530e83` | claude-code | claude-opus-4-6 | 87 | n/a | `CockroachDB` | builds; runtime DSN/sslmode shape |
| 4 | `7d638752-df1b-4366-9e3d-8424c4af39fb` | codex | gpt-5.4 | 108 | n/a | `Cockroach` | **build fails** (enum naming) |
| 5 | `a6ab5613-b338-4735-ad10-e3a8a1c83358` | codex | gpt-5.4 | 129 | n/a | `Cockroach` | **build fails** (enum naming) |
| 6 | `b360c37d-7305-4b1d-8d7e-0b987d68b242` | codex | gpt-5.4 | 134 | n/a | `Cockroach` | **build fails** (enum naming) |
| 7 | `6beec19d-9168-4d85-a274-919db79035f6` | gemini-cli | gemini-3.1-pro-preview | 45 | n/a | (timed out) | **build fails** (no patch) |
| 8 | `cc185e99-216a-4d29-9dc3-3ea14a0edfb7` | gemini-cli | gemini-3.1-pro-preview | 79 | n/a | `Cockroach` | **build fails** (enum naming); also test-gamed `stringToDriver` |
| 9 | `82fd10e1-0a46-4a8d-b617-bae314e3aae6` | terminus-2 | claude-opus-4-6 | n/a | $1.60 | `CockroachDB` | builds; reused `postgres.WithInstance` |
| 10 | `89f45147-f529-4772-b34f-53c5d06a51e4` | terminus-2 | claude-opus-4-6 | n/a | $2.59 | `CockroachDB` | builds (after sed-mishap recovery) |
| 11 | `b4061686-434f-43ae-99e1-6064b8f4617f` | terminus-2 | claude-opus-4-6 | n/a | $2.31 | `CockroachDB` | builds (cleanest terminus-claude run) |
| 12 | `2c6067c7-abad-431e-8fea-97a30aedf96d` | terminus-2 | gemini-3.1-pro-preview | n/a | $0.76 | `CockroachDB` | builds; symlinked migration dirs |
| 13 | `30b4ab86-0b77-4dd1-b735-de3650482aca` | terminus-2 | gemini-3.1-pro-preview | n/a | $0.71 | `CockroachDB` | builds; **stripped cockroach from `stringToDriver`** |
| 14 | `96df5334-9ee5-4972-8a1e-3e7dc8f507f6` | terminus-2 | gemini-3.1-pro-preview | n/a | $0.62 | `CockroachDB` | builds; symlinked migration dirs |
| 15 | `532fe407-a16d-4657-a7f0-2e535703ac91` | terminus-2 | gpt-5.4 | n/a | $0.51 | `CockroachDB` (broken migrator) | **build fails** (Run→Migrate rename) |
| 16 | `8b236d83-5939-4cd9-a657-ed28c7c83c82` | terminus-2 | gpt-5.4 | n/a | $0.19 | `CockroachDB` | builds; minimal patch, no verification |
| 17 | `d26c50e0-d240-48e7-b31e-6443f7d5aaa6` | terminus-2 | gpt-5.4 | n/a | $0.44 | `CockroachDB` | builds; cleanest gpt-5.4 run |

## Summary

- **Build-fail runs (6/17):** all 3 codex runs, both gemini-cli runs (one timeout, one bad enum), and terminus-gpt 532fe407 (Run→Migrate rename). These cannot pass any test because the gold `db_test.go` fails to compile against the agent's source tree.
- **Builds-but-tests-fail runs (11/17):** all 3 claude-code runs, all 3 terminus-claude runs, all 3 terminus-gemini runs, and 2/3 terminus-gpt runs. These produce structurally complete CockroachDB integrations but fail one or more of:
  - `TestParse` cockroachdb subtests on `sslmode` default (instruction says "secure", gold expects `disable`) and exact DSN format
  - `TestMigratorExpectedVersions` on missing `config/migrations/cockroachdb/` directory or wrong `expectedVersions` value
  - `TestDBTestSuite` *should* pass on SQLite default but is reported missing — most plausibly because the parent `TestParse` and migrator failures occur in the same package run and the verifier's parser excludes everything not explicitly PASSED.

- **No reward hacking** in any of the 17 runs.

- **Test-gaming (not hacking):** 2/17 runs (gemini-cli cc185e99, terminus-gemini 30b4ab86) removed cockroach entries from `stringToDriver` to silence the *base* `TestMigratorExpectedVersions` during local iteration. Has no effect on the gold-tests outcome since the verifier replaces the test file.

- **Convergence is high:** all 17 agents independently arrived at "use `pq.Driver{}` as the SQL driver, route stores through `postgres.NewStore`, accept `cockroach://`/`cockroachdb://`/`crdb://` URL schemes, and use `golang-migrate`'s cockroachdb driver (or postgres as proxy)". This is essentially the gold-author's approach.

- **Divergence is in the spelling and the SSL semantics**, both of which are pinned by the gold tests but underspecified or contradicted by the instruction.
