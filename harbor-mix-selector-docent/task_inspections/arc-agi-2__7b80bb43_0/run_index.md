# Run Index — arc-agi-2 / 7b80bb43_0

Collection: `640e920a-aef3-4b7c-9487-69899ef19e9d`
Task checksum: `d3b8da9d7925a8a3d4805bee7fa2e7ca4aac16802c8d1b5b86ea9e77a6e581cf`
Reported score (from header): **6 / 18** (matches `n_succ=6` in metadata).

Test grid: **29 rows × 17 cols** (background `8`, lines drawn in `9`).
Agent timeout: **600 s**. Verifier timeout: 60 s.

## All 18 runs

| Run ID (short) | Model | Agent | Reward | Exception | Steps |
|---|---|---|---|---|---|
| a44478da | anthropic/claude-opus-4-6 | claude-code | 0 | AgentTimeoutError | 1 |
| df259f25 | anthropic/claude-opus-4-6 | claude-code | 0 | AgentTimeoutError | 1 |
| 0a03062b | claude-opus-4-6 | claude-code | 0 | — | 6 |
| 00f9dac8 | anthropic/claude-opus-4-6 | terminus-2 | 0 | AgentTimeoutError | NULL |
| 22c0a4c1 | anthropic/claude-opus-4-6 | terminus-2 | 0 | AgentTimeoutError | NULL |
| 7f0e52bd | anthropic/claude-opus-4-6 | terminus-2 | 0 | AgentTimeoutError | NULL |
| 030b9c7f | gemini-3.1-pro-preview | gemini-cli | **1** | — | 3 |
| 34ad41f7 | gemini-3.1-pro-preview | gemini-cli | **1** | — | 4 |
| 93f6c088 | gemini-3.1-pro-preview | gemini-cli | **1** | — | 5 |
| 02c73ab7 | gemini/gemini-3.1-pro-preview | terminus-2 | **1** | AgentTimeoutError* | NULL |
| 0f8fafbb | gemini/gemini-3.1-pro-preview | terminus-2 | **1** | — | NULL |
| 41114a41 | gemini/gemini-3.1-pro-preview | terminus-2 | 0 | — | NULL |
| 3aeb5ac3 | gpt-5.4 | codex | 0 | — | 14 |
| 81aeb4ac | gpt-5.4 | codex | **1** | — | 18 |
| de641c5d | gpt-5.4 | codex | 0 | — | 16 |
| 6c753074 | openai/gpt-5.4 | terminus-2 | 0 | — | NULL |
| 8fa97126 | openai/gpt-5.4 | terminus-2 | 0 | — | NULL |
| fe78ab5e | openai/gpt-5.4 | terminus-2 | 0 | — | NULL |

*02c73ab7 has both reward=1 and AgentTimeoutError; suggests the file was written before the harness terminated.

## Pass distribution
- Successes: 6 (3 gemini-cli, 2 gemini/terminus-2, 1 gpt/codex)
- Failures: 12 (6 claude — all timeouts or empty output, 1 gemini/terminus-2, 2 gpt/codex, 3 gpt/terminus-2)
