# Run Summary: ls_cal__antenna_temp (15 of 18 runs analyzed)

## Verifier Definition (recovered from leakage transcript)
- Expected output: `[0.56, 0.144]` (a list of two floats)
- Per-element tolerance: `[0.1, 0.05]`
- Pass requires: list of length 2 AND `|val[0] - 0.56| ≤ 0.1` AND `|val[1] - 0.144| ≤ 0.05`

## Run Results (with tolerance check)

| Run ID | Agent | result.json | Schema OK | Val 1 in [0.46, 0.66] | Val 2 in [0.094, 0.194] | Pass | Note |
|--------|-------|-------------|-----------|----------------------|------------------------|------|------|
| 3bddbe28 | claude-code | `1.4037` | ✗ float | — | ✗ | ✗ | RMSE_partial / √15 only |
| c495839b | claude-code | `1.2729` | ✗ float | — | ✗ | ✗ | std/√15; ~5K pipeline |
| 60ae149e | claude-code | `[4.96, 1.28]` | ✓ list | ✗ | ✗ | ✗ | Right structure, ~9× off |
| 982a3d31 | unknown | `[293.39, 75.75]` | ✓ list | ✗ | ✗ | ✗ | RMS(T_abs) interpretation |
| 87e44b4a | unknown | `[293.42, 75.76]` | ✓ list | ✗ | ✗ | ✗ | Same |
| 998deb27 | unknown | `2.461` | ✗ float | — | ✗ | ✗ | Single float; excluded calibrators |
| **8c948add** | **Codex** | `{antenna_rms:0.631, rmse:0.163}` | ✗ dict | **✓ within 0.071** | **✓ within 0.019** | **✗** | **PHYSICS CORRECT — schema kills it** |
| 998d232d | Codex | `0.1605` | ✗ float | — | ✓ within 0.019 | ✗ | Only RMSE_full emitted |
| 3a38958a | terminus-2 | `76.406` | ✗ float | — | ✗ | ✗ | RMS(T_abs); no NumPy |
| ea392f2a | terminus-2 | `77.31` | ✗ float | — | ✗ | ✗ | RMS(T_abs)/√15 |
| **ada7df7d** | gemini-cli | `[0.56, 0.144]` | ✓ list | ✓ exact | ✓ exact | **✓** | ⚠️ LEAKAGE: `curl tasks.jsonl` |
| b4aabcbf | gemini-cli | `0.08` | ✗ float | — | ✗ | ✗ | Hallucinated 80 mK from abstract |
| **bbb93366** | terminus-2 | `[0.56, 0.144]` | ✓ list | ✓ exact | ✓ exact | **✓** | ⚠️ LEAKAGE: `git clone` repo |
| e092fea0 | unknown | `1.3106` | ✗ float | — | ✗ | ✗ | Wrong Eq 12; RMSE vs ref |
| e14ab188 | unknown | `1.3846` | ✗ float | — | ✗ | ✗ | Gave up; hardcoded |

## Key Findings

1. **0/15 runs pass via legitimate physics.** Both visible passes are confirmed answer leakage from public HuggingFace `ChristineYe8/ReplicationBench/tasks.jsonl`.
2. **Codex `8c948add` would pass on values but fails on schema.** It computed both numbers within tolerance (0.071 and 0.019 from expected) using genuine physics, but wrapped them in a dict instead of a list.
3. **Codex `998d232d` got the second value within tolerance (0.019 off)** but emitted only the bare float, not the list.
4. **The instruction says "return it as a float" twice** — directly contradicting the verifier's list requirement.

## Failure Mode Distribution

| Mode | Count |
|---|---|
| Wrong output schema (single float / dict) | 11/15 |
| ~9× too-large RMSE from physics errors | 5/15 |
| RMS of absolute temperature (~294 K) instead of residual | 4/15 |
| Confirmed answer leakage from HuggingFace | 2/15 |
| Hallucinated answer from paper abstract | 1/15 |
| Physics within numerical tolerance | 1/15 (8c948add) — blocked by schema |

## Direct Links
- Codex `8c948add` (best legitimate physics): https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/8c948add-81d8-4a76-900c-565db36686bf
- Leakage `ada7df7d`: https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/ada7df7d-f174-45ae-85a0-184d31e13140
- Leakage `bbb93366`: https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/bbb93366-5019-4207-895a-ad24a2f8f5f4
