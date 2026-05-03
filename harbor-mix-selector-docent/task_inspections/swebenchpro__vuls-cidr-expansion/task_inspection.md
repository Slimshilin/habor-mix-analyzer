# Task Inspection — `swebenchpro / future-architect__vuls-86b60e1478e4...` (CIDR expansion)

## TL;DR — Verdict: **REJECT** (or **ACCEPT after Fix A**)

The 0/18 result is **predominantly task-side**, not capability-side. The hidden gold test `TestHosts` exercises the **iplib v1.0.3 RFC-3021 / host-only-enumeration semantics** for IPv4 (`/30 → 2 hosts`, `/31 → 2 hosts`, `/32 → 1 host`), but:
1. The PR description does **not** specify those semantics — its examples ("`/30` yields the in-range addresses for the network") read as "all addresses in the prefix" to anyone defaulting to Go stdlib.
2. The library carrying these semantics — `github.com/c-robinson/iplib` — is **not in the baseline `go.mod`**, so an agent has no breadcrumb to discover the convention by reading the codebase.
3. 17/18 agents implement `enumerateHosts` with stdlib `net.ParseCIDR` / `net/netip` and yield **4 addresses for `/30`** (the natural literal reading). The single agent that hand-rolled network/broadcast exclusion (gemini-cli run `893f17d3`) still failed, signalling additional thin-margin pitfalls (likely `nil` vs `[]string{}` for empty results, or an `isCIDRNotation` false positive on the literal `ssh/host`).
4. One run (terminus-2/gemini `b0a4652a`) **briefly produced the correct trim** then *talked itself out of it* by reading "the in-range addresses" literally — direct evidence that the spec wording, not the agent capability, is the limiter.

The grader **does** restore `TestHosts` correctly (Jiankai's claim is empirically right; the "Unsure" reviewer's environmental claim is wrong; the test runs and fails assertions).

A **capable being can resolve this task only by external knowledge** of iplib-style RFC enumeration or by asking the right "did you mean usable hosts only?" question. The task is therefore not self-contained at the brief+env level.

Recommendation: **REJECT in current form.** Make acceptable via **Fix A** (add three explicit enumeration examples to the PR description that pin the IPv4 host-only semantics for `/30` and the RFC-3021 semantics for `/31`). Optional **Fix B** preseeds `iplib` in the baseline `go.mod`; **Fix C** swaps `reflect.DeepEqual` for a set-equality assertion. Details in §6.

---

## 1. Task at a glance

- **Repo:** `future-architect/vuls` (Go vulnerability scanner).
- **Base commit:** `42fdc08933d2b60adc555972b32ae599386b0b9c`.
- **Gold commit:** `86b60e1478e44d28b1aff6b9ac7e95ceb05bc5fc` (PR #1415 — "feat(config): support CIDR").
- **Files in gold patch:** `config/config.go`, `config/tomlloader.go`, `config/tomlloader_test.go`, `go.mod`, `go.sum`, `subcmds/configtest.go`, `subcmds/discover.go`, `subcmds/scan.go`.
- **Required tests (`fail_to_pass`):** `["TestHosts"]` — a single table-driven Go test in `config/tomlloader_test.go`, 13 sub-cases (see §3).
- **Pre-existing tests (`pass_to_pass`):** 84 tests in `package config`; all 18 agents pass them, so the build is healthy in every cell.
- **Cells × runs (18 total):** claude-code/opus-4-6 (3), codex/gpt-5.4 (3), gemini-cli/gemini-3.1-pro-preview (3), terminus-2/opus-4-6 (3), terminus-2/gpt-5.4 (3), terminus-2/gemini-3.1-pro-preview (3).
- **Result:** uniformly `reward=0`, no exceptions, identical stdout summary "Required tests: 1, Passed tests: 84, Missing tests: ['TestHosts']".

## 2. Verifier mechanics — resolves the prior reviewer dispute

`/tests/test.sh` runs (excerpt):
```bash
GOLD_CHECKOUT=$(python3 ...)  # last line of before_repo_set_cmd
eval "$GOLD_CHECKOUT"          # → git checkout 86b60e14... -- config/tomlloader_test.go
bash /tests/run_script.sh "$TEST_FILES"  # then go test, parse, compare
```

I fetched `config/tomlloader_test.go` from the gold commit on GitHub. It contains `TestHosts` at lines 9–98 (137-line file, also includes `TestToCpeURI`). Conclusions:

- **Jiankai is correct:** `TestHosts` is restored to the working tree before `go test ./config` runs.
- **"Unsure" reviewer is wrong about the environment:** the test is *not* missing from the filesystem. Their reasoning ("never appears in any test run output → never restored") confused "0 of the required tests passed" with "the required test never executed". Because 84 sibling tests pass, the package builds and `TestHosts` is being *run* — the test is just *failing assertions*. The 222-byte truncated stdout hides the per-case `t.Errorf` lines, but that's a logging limitation, not an environmental break.

So the task's grader is functionally correct. The reason for 0/18 lives in the spec and in agent inference, not in a broken restore.

## 3. The actual failure mode — iplib's library-specific semantics

The hidden test asserts `reflect.DeepEqual(actual, tt.expected)` after `sort.Slice(actual)` for these cases (paraphrased from `gold__tomlloader_test.go`):

| # | `in` | `ignore` | expected | err |
|---|---|---|---|---|
| 1 | `127.0.0.1` | — | `["127.0.0.1"]` | false |
| 2 | `127.0.0.1` | `["127.0.0.1"]` | `[]` | false |
| 3 | `ssh/host` | — | `["ssh/host"]` | false |
| 4 | `192.168.1.1/30` | — | `[".1", ".2"]` | false |
| 5 | `192.168.1.1/30` | `[".1"]` | `[".2"]` | false |
| 6 | `192.168.1.1/30` | `["ignore"]` | — | **true** |
| 7 | `192.168.1.1/30` | `["192.168.1.1/30"]` | `[]` | false |
| 8 | `192.168.1.1/31` | — | `[".0", ".1"]` | false |
| 9 | `192.168.1.1/32` | — | `[".1"]` | false |
| 10 | `2001:...8888/126` | — | 4 addrs | false |
| 11 | `…/127` | — | 2 addrs | false |
| 12 | `…/128` | — | 1 addr | false |
| 13 | `…/32` | — | — | **true** |

Cases 4, 5, 7, 8, 9 are the IPv4 enumeration trap. I ran iplib v1.0.3 in a probe directory:
```
192.168.1.1/30: count=2  →  192.168.1.1, 192.168.1.2
192.168.1.1/31: count=2  →  192.168.1.0, 192.168.1.1
192.168.1.1/32: count=1  →  192.168.1.1
```
Exact match to the test's expected outputs. iplib's `NewNet4` excludes the network address and broadcast for prefixes ≤/30, applies RFC 3021 (no broadcast) for /31, and treats /32 as a single host route. **The test is a behavioural specification of iplib.**

A naive stdlib loop yields the network and broadcast as well:
- `192.168.1.1/30` → `[.0, .1, .2, .3]` (4 addrs) — fails case 4
- `192.168.1.1/30` ignore=`[.1]` → `[.0, .2, .3]` (3 addrs) — fails case 5
- `192.168.1.1/32` → `[.0]` (network address) for some impls, fails case 9 even when /30 doesn't.

Additional thin-margin pitfalls in the test, beyond /30 enumeration:
- **Case 2 expects `[]string{}` after exclusion** — `reflect.DeepEqual([]string(nil), []string{}) == false` in Go. Returning `nil` from the empty path silently fails.
- **Case 3 (`ssh/host`)** — requires `isCIDRNotation` to return false for non-IP-prefix slash-strings. An over-eager `strings.Contains(host, "/")` heuristic fails this case.
- **Case 6 (ignore=`["ignore"]`)** — requires error detection on a non-IP / non-CIDR ignore entry. Several agents detect this *only* if the `host` is a CIDR; they'd silently accept a non-IP ignore when host is a plain IP.

## 4. The instruction does not pin down the convention

Verbatim from the PR description:
> IPv4 examples: '/31' yields exactly two addresses; '/32' yields one; '/30' yields the in-range addresses for the network containing the given IP, and 'IgnoreIPAddresses' can remove specific addresses or the entire subrange.

"the in-range addresses for the network" admits two readings:
- **A (literal):** all 4 addresses in the /30 prefix.
- **B (RFC-aware host-only):** the 2 usable hosts, excluding network and broadcast.

Reading A is what `net.ParseCIDR` + iteration produces. Reading B is what iplib produces and what the test asserts. The mention that `/32` yields 1 (host-route) and `/31` yields 2 (RFC 3021) hints — *in retrospect* — at Reading B, but only because Reading B is the convention iplib encodes. A stdlib-oriented Go programmer with no iplib exposure typically reads "in-range" as Reading A.

## 5. The codebase contains no breadcrumb to iplib

I downloaded both `go.mod` and `go.sum` at base commit `42fdc089…` and at gold commit `86b60e14…`:

| File | Base | Gold |
|---|---|---|
| `go.mod` | no `iplib` | `github.com/c-robinson/iplib v1.0.3` added |
| `go.sum` | no `iplib` | `iplib v1.0.3` hashes added |

There are no other `iplib` usages in the repo at base. So `grep -r iplib /app` and `cat go.mod | grep -i ip` both return empty — agents have **zero environmental cue** that iplib is the intended dependency. Combined with §4, the iplib semantics are not reachable from instruction + env unless the agent (a) pattern-matches "Go + CIDR + RFC-aware enumeration" → iplib from training memory, *and* (b) anticipates that the test will pin those exact outputs. Both are external-knowledge moves.

## 6. Possible fixes (none simplify the task)

**Fix A — clarify the spec (preferred).** Replace the ambiguous "in-range addresses" sentence with three explicit examples that pin the boundary cases:
```
- A /30 yields the two usable host addresses, excluding the network and broadcast addresses
  (e.g. 192.168.1.1/30 → ["192.168.1.1", "192.168.1.2"]).
- A /31 yields both addresses per RFC 3021 (e.g. 192.168.1.1/31 → ["192.168.1.0", "192.168.1.1"]).
- A /32 yields the single host address (e.g. 192.168.1.1/32 → ["192.168.1.1"]).
- IPv6 masks broader than /66 must error (the address count must fit in int64).
- For inputs that consist of an empty host set after exclusions, return an empty slice (not nil).
```
This preserves test strictness, makes the spec self-contained, and lets a capable agent implement everything from stdlib alone — the agents who hand-rolled it (e.g. gemini-cli `893f17d3`) showed this is feasible.

**Fix B — discoverable dependency.** Pre-add `github.com/c-robinson/iplib v1.0.3` to baseline `go.mod`/`go.sum` plus a TODO comment in `tomlloader.go` ("`// TODO: implement using iplib for RFC-aware host enumeration`"). This puts the convention into the environment so agents can discover it via codebase exploration. More invasive but matches a more realistic SWE flow ("here's the lib, wire it up").

**Fix C — relax `reflect.DeepEqual`.** Use sorted set equality, accept either Reading A or B for `/30` (with explicit `pass_to_pass` documentation of either-or). This dilutes evaluation power and mixes two distinct semantics; not recommended.

**Recommendation:** apply **Fix A**. It's a 5-line edit to the PR description that converts the task from "guess the right library" to "implement the spec correctly." After Fix A, current 0/18 should rise toward 4–10/18 (extrapolating from the runs that already got 11+ of 13 cases right except the /30 boundary). After Fix A *and* Fix B, the task becomes a clean "use the suggested helper" workflow and most capable cells should pass.

## 7. Cheating surface

- **Read the gold test directly:** at agent-time `config/tomlloader_test.go` is the *base* version (only `TestToCpeURI`). The gold version is checked out only at verify-time, so this attack does not work. ✅ Not exploitable.
- **`git fetch origin` / `git show 86b60e14…`:** the dockerfile resets to base but does not strip the remote. If the upstream commit is reachable, an agent could in theory `git show 86b60e14:config/tomlloader_test.go`. **No agent attempted this in any of the 18 trajectories** — sub-agent reports confirm zero cheating attempts. The risk exists but isn't being exercised.
- **Hard-code outputs:** an agent could special-case all 13 test inputs in `hosts()`. **No agent did this** — implementations are general-purpose enumerations, not table lookups. Detectable in code review either way.
- **`net.LookupIP("non-IP")` quirks:** test 3 uses `ssh/host`, which contains `/`. An agent who naively checks `strings.Contains(host, "/")` to detect CIDR fails this case; the gold uses `net.ParseIP(strings.SplitN(host, "/", 2)[0]) != nil` which correctly rejects `ssh`. Not cheating, but a test-instrumented gotcha.

## 8. Per-trajectory analysis (18 runs, all six cells)

Detailed per-cell reports live alongside this file:
- `run_claude-code__claude-opus-4-6.md` (3 runs, claude-code/opus)
- `run_codex__gpt-5.4.md` (3 runs, codex/gpt-5.4)
- `run_gemini-cli__gemini-3.1-pro-preview.md` (3 runs, gemini-cli/gemini-3.1-pro)
- `run_terminus-2__claude-opus-4-6.md` (3 runs, terminus-2/opus)
- `run_terminus-2__gpt-5.4.md` (3 runs, terminus-2/gpt-5.4)
- `run_terminus-2__gemini-3.1-pro-preview.md` (3 runs, terminus-2/gemini-3.1-pro)

### 8.1 Aggregate matrix

| Cell | Run | Lib | `/30` count | `/31` | `/32` | IPv6 broad | BaseName field | TOML expand | Cheat |
|---|---|---|---|---|---|---|---|---|---|
| claude-code/opus | 884a3495 | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| claude-code/opus | 8e63cfcb | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| claude-code/opus | d3ec08e4 | stdlib `net`+`big.Int` | **4** | 2 ✓ | 1 ✓ | `<112` ✓ | ✓ | ✓ | none |
| codex/gpt-5.4 | 11a8e3ca | `net/netip` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| codex/gpt-5.4 | 6e5c4d68 | `net`+`netip` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| codex/gpt-5.4 | 935b273d | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| gemini-cli/gemini | 4bc7d10e | `net/netip` | **4** | 2 ✓ | 1 ✓ | `<112` ✓ | ✓ | ✓ | none |
| gemini-cli/gemini | **893f17d3** | stdlib `net` | **2 ✓** | 2 ✓ (cased) | 1 ✓ (cased) | `>16` ✓ | ✓ | ✓ | none |
| gemini-cli/gemini | a2590785 | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `<112` ✓ | ✓ | ✓ | none |
| terminus-2/opus | 25e11d86 | `net`+`big.Int` | **4** | 2 ✓ | 1 ✓ | `>17` ✓ | ✓ | ✓ | none |
| terminus-2/opus | 8090e1f2 | `net`+`big.Int` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| terminus-2/opus | 98cf9be8 | stdlib `net` (uint32) | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| terminus-2/gpt-5.4 | 1d292b62 | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| terminus-2/gpt-5.4 | 2bf4556d | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| terminus-2/gpt-5.4 | b2b27972 | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `>16` ✓ | ✓ | ✓ | none |
| terminus-2/gemini | 0131b9a4 | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `<112` ✓ | ✓ | ✓ | none |
| terminus-2/gemini | 8a2cc8c4 | stdlib `net` | **4** | 2 ✓ | 1 ✓ | `<126` ✓ | ✓ | ✓ | none |
| terminus-2/gemini | b0a4652a | stdlib `net` | **4** (was 2, reverted) | 2 ✓ | 1 ✓ | `<120` ✓ | ✓ | ✓ | none |

### 8.2 Surface vs root cause

- **Surface cause (17/18 runs):** `enumerateHosts(ip/30)` returns 4 addresses. Test expects 2.
- **Root cause:**
  1. The PR description's sentence "/30 yields the in-range addresses" is ambiguous; the natural reading (Reading A in §4) gives 4 addresses.
  2. Baseline `go.mod` doesn't include `iplib`, so there's no environmental nudge toward Reading B.
  3. Existing 84 tests in `config/` don't exercise `/30` cardinality, so agents who run `go test ./config/...` get a false green light.
  4. The PR text explicitly says "I've already taken care of all changes to any of the test files… You don't have to modify the testing logic" — agents reasonably take this to mean *don't probe for hidden tests* and rely solely on the spec.

The diagnostic moments:
- **gemini-cli `a2590785`** literally printed `30: [192.168.1.0 192.168.1.1 192.168.1.2 192.168.1.3]` and accepted it as correct.
- **terminus-2/gemini `b0a4652a`** **wrote the correct trim** (`if mask < 31 && len(ips) > 2 { ips = ips[1:len(ips)-1] }`), then **explicitly removed it** because it re-read the PR text "/30 yields the in-range addresses" and decided that meant "all 4". This is the cleanest evidence that the *spec wording* is the limiter, not capability.
- **gemini-cli `893f17d3`** independently rediscovered network/broadcast exclusion with hand-written bitwise broadcast detection plus a dedicated /31 branch, *without* ever naming iplib or RFC 3021. It still fails the verifier — almost certainly due to one of the thin-margin pitfalls in §3 (most likely `nil` vs `[]string{}` for case 2/7, or a small IPv6/`isCIDRNotation` discrepancy). The fact that **even the agent who got the headline /30 right still failed** is itself evidence of how brittle the test is.

### 8.3 Variance across cells

- All six cells show the same primary failure mode → the failure is **not** model-specific and **not** harness-specific. It's task-driven.
- Strongest signal of "almost passed": one of three gemini-cli runs got /30 right; one of three terminus-2/gemini runs almost got /30 right and reverted. So the gemini family was the closest, but neither got across the line.
- claude-opus, gpt-5.4, terminus-2-orchestrated runs all uniformly produce 4-for-/30; **no model used iplib** in any of the 18 trajectories.
- Cheating: zero attempts across all 18 trajectories. None tried `git show 86b60e14:…`, none tried to read hidden test fixtures, none table-look-up'd the test inputs.

## 9. Answers to the user's six questions

### Q1. How close are agents to successfully completing the task?

Quantitatively: each agent gets ~11/13 sub-cases of `TestHosts` correct (the /31, /32, /126, /127, /128, IPv6-/32, ssh/host, single-IP, and invalid-ignore cases), but fails the `/30` case and the `/30`-with-ignore case. Because the test uses `reflect.DeepEqual` on the full slice with no per-case scoring, a single mismatch sinks the run. So they're cosmetically close (~85% of asserts probably pass) but binary-failed.

### Q2. How do agent-model performances vary?

Surprisingly low variance. Across 6 (agent × model) cells × 3 trials each:
- 17/18 produce 4 addresses for /30 with stdlib enumeration.
- 1/18 hand-rolls the host-only semantics correctly (gemini-cli `893f17d3`); still fails for unrelated thin-margin reasons.
- 1/18 transiently writes the correct trim then reverts (terminus-2/gemini `b0a4652a`).
- The other 4 cells (claude-code/opus, codex/gpt-5.4, terminus-2/opus, terminus-2/gpt-5.4) show **no awareness** of network/broadcast exclusion in any of their 12 runs.

**Surface reasons** they all give: "the spec says enumerate the in-range addresses; my loop does that." They run their own private tests asserting `/30 → 4` and watch them pass.

**Root cause** is shared across all cells: a literal reading of the spec + reliance on stdlib + a baseline that contains no breadcrumb to iplib + a "tests already taken care of" instruction that discourages hidden-test inference.

### Q3. Concrete agent behaviors that failed the tests

Verbatim test code (gold `config/tomlloader_test.go:84-97`):
```go
for i, tt := range tests {
    actual, err := hosts(tt.in, tt.ignore)
    sort.Slice(actual, func(i, j int) bool { return actual[i] < actual[j] })
    if err != nil && !tt.err { t.Errorf(...) }
    else if err == nil && tt.err { t.Errorf(...) }
    if !reflect.DeepEqual(actual, tt.expected) { t.Errorf(...) }
}
```

Concrete failure (e.g., codex/gpt-5.4 `11a8e3ca`'s code):
```go
prefix = prefix.Masked()
hostBits := prefix.Addr().BitLen() - prefix.Bits()
for addr, i := prefix.Addr(), 0; i < (1 << hostBits); i++ {
    enumerated = append(enumerated, addr.String())
    addr = addr.Next()
}
```
For `192.168.1.1/30` this returns `["192.168.1.0", "192.168.1.1", "192.168.1.2", "192.168.1.3"]`. After `sort.Slice`, that's still 4 strings. The test then does `reflect.DeepEqual([4 strings], [".1", ".2"]) == false` → `t.Errorf`. → `TestHosts` fails → grader reports `Required tests that passed: 0`. Same pattern in 16 other runs.

For terminus-2/gemini `b0a4652a` *during reasoning*: the agent first wrote `if mask < 31 && len(ips) > 2 { ips = ips[1:len(ips)-1] }` which would have given `[".1", ".2"]` for /30 — this would have passed test cases 4, 5, 7. Then in a later message it wrote (paraphrased) "the PR description says '/30 yields the in-range addresses for the network containing the given IP'; let's assume it means all addresses in the CIDR block" and removed the trim.

### Q4. Are problems attributable to the task (instruction / environment / tests)? Could a "super-capable being" solve it?

**Yes, problems are attributable to the task.** Specifically:
- **Instruction**: ambiguous about /30 boundary semantics (network/broadcast exclusion) (§4).
- **Environment**: doesn't expose iplib so the convention can't be discovered (§5).
- **Test**: thin-margin assertions (`reflect.DeepEqual` for `nil` vs `[]string{}`; one pin per /30 boundary) make near-correct implementations fail completely (§3).

**Could a super-capable being solve it?** In principle yes, by either:
- Pattern-matching from training data ("Go + CIDR + RFC 3021" → iplib's `Net4.Enumerate`) and gambling that the test pins iplib semantics; or
- Writing both implementations (Reading A + Reading B) and probing the test boundaries; or
- Generating its own private test-fixture from "/31 yields 2 / /32 yields 1" hints, recognizing those numbers as RFC-3021 + host-route signatures, and inferring the host-only enumeration convention.

This is a **library-convention identification** capability, not a software-engineering capability. The fact that one of 18 agents (gemini-cli `893f17d3`) hand-rolled the right semantics shows it's not impossible; the fact that 17 of 18 didn't shows it's beyond current practice. **The task is theoretically self-contained but in a fragile, knowledge-dependent way that the spec does not signal.**

### Q5. Proposed fixes

See §6 above. Best path: **Fix A** (clarify spec with three explicit examples and the empty-slice-not-nil note). Optional **Fix B** (preseed `iplib` in baseline). Avoid **Fix C** (test relaxation) — it dilutes evaluation.

After Fix A I predict:
- Cells using strong reasoners (claude-code/opus, terminus-2/opus, gpt-5.4) → most or all 3 trials would pass.
- Gemini family → likely 2/3 trials pass per cell (gemini already half-discovered the convention).
- Estimated total: ~12–15 of 18 trials pass. The task remains "essential" difficulty (cross-file changes, subtle library semantics, validation logic) but becomes solvable from the brief.

### Q6. Cheating / agent hacking

**No cheating observed in any of the 18 trajectories.** No attempts to:
- Read `config/tomlloader_test.go` for hidden tests (would have been the gold version's test; agents who tried only saw the base version's `TestToCpeURI`).
- `git show 86b60e14:config/tomlloader_test.go` (this would work — the dockerfile doesn't strip the remote — but no agent attempted it).
- Hard-code the 13 test inputs in `hosts()` as a table.
- Manipulate `go.sum` / `go.mod` to inject test-bypass logic.

The cheating surface that exists (§7) is `git show <gold-sha>:<test-file>` — worth either disabling network access at agent-time or stripping `.git` after `reset --hard`. Not actively exploited but worth closing in a future task hardening pass.

## 10. Final answer to the central question

> **Is the failure because of the task itself or the agent capability bottleneck?**

**Predominantly the task.** The brief admits two valid readings of `/30`; the environment offers no breadcrumb toward the one the test enforces; the test is brittle to small implementation choices (`nil` vs `[]string{}`, `isCIDRNotation` heuristics). 17 of 18 agents converge on the natural-language reading and fail; 1 of 18 hand-rolls the correct semantics and still fails on adjacent thin-margin assertions; 1 of 18 *had* the correct fix and reverted it specifically because of the spec wording.

There is a real capability component too — none of 18 agents went looking for an existing library that handles RFC-aware host enumeration, and only 1 cross-checked their /30 output against the conventional "usable hosts" reading — but the capability bar required to clear this task without spec changes is "knows iplib by heart and gambles on the test pinning its semantics," which is not a reasonable evaluation target for general-purpose SWE agents.

**Verdict: REJECT in current form. ACCEPT after Fix A** (5-line spec clarification). The bones of the task — multi-file changes, validation logic, TOML loader expansion, BaseName tracking — are good SWE content; only the unstated /30 convention makes it currently unfair.
