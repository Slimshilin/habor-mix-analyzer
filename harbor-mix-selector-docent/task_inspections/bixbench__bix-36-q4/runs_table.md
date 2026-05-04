# All 18 docent runs at a glance

Collection: `640e920a-aef3-4b7c-9487-69899ef19e9d` · task_checksum `0959f3f3...1dffb61`
All 18 trials returned reward 0.0. None hit the band `[0.55, 0.59]`.

Sorted by extracted final answer (parsed from `<answer>...</answer>`).

| # | Agent run id (docent) | Harness | Model | Final answer | Reward |
|---|---|---|---|---|---|
| 1 | `e3ea324d-2cb4-47bf-a8f3-1ef58df524c3` | claude-code | claude-opus-4-6 | **0.18** | 0 |
| 2 | `11ca6990-36d4-4804-a687-d67cfa21fd87` | terminus-2 | gemini/gemini-3.1-pro-preview | 4.892e-07 | 0 |
| 3 | `4cdb1013-df1b-4b7a-9d83-83ef7ca143ad` | terminus-2 | gemini/gemini-3.1-pro-preview | 2.687e-08 | 0 |
| 4 | `7c06ccf3-ca02-45c5-b694-872b1c56d5ac` | terminus-2 | anthropic/claude-opus-4-6 | 1.12e-10 | 0 |
| 5 | `c0774023-f11e-4e82-88ca-21b5ed411276` | terminus-2 | anthropic/claude-opus-4-6 | 1.12e-10 | 0 |
| 6 | `1160aec6-9849-4af5-9983-1366d3169029` | claude-code | claude-opus-4-6 | 1.43e-21 | 0 |
| 7 | `72aa8ff9-b8a3-467f-a0da-792f1369a284` | codex | gpt-5.4 | 2.999698e-32 | 0 |
| 8 | `1ce7a046-0ce2-435d-9aa3-e0726cf407de` | codex | gpt-5.4 | 2.72e-41 (prose) | 0 |
| 9 | `b6ac03c0-b923-42ab-8ae7-11c4bfbefa26` | codex | gpt-5.4 | 2.72338e-41 (prose) | 0 |
| 10 | `115a98a5-9a74-4c83-ae28-64202c4c81f3` | terminus-2 | openai/gpt-5.4 | 2.7233761722814507e-41 | 0 |
| 11 | `d1724994-4c6a-4ff2-bfcd-e574f9e0c752` | terminus-2 | openai/gpt-5.4 | 2.7233761722814507e-41 | 0 |
| 12 | `d7071018-ee53-4e88-9ca0-c07318ca81fc` | terminus-2 | openai/gpt-5.4 | 2.7233761722814507e-41 | 0 |
| 13 | `59745ef4-1a84-40c1-b730-f7b19560ce86` | claude-code | claude-opus-4-6 | 6.57e-52 | 0 |
| 14 | `e4d3bfb7-0739-4d34-9701-d1950c0bb497` | terminus-2 | anthropic/claude-opus-4-6 | 4.56e-64 | 0 |
| 15 | `a626b1d6-b184-4261-836d-f16d0990b199` | terminus-2 | gemini/gemini-3.1-pro-preview | 6.085e-134 | 0 |
| 16 | `4f5cf7a9-df26-4900-834c-81a8fe2d34a5` | gemini-cli | gemini-3.1-pro-preview | 8.396166823294354e-154 | 0 |
| 17 | `51524c3f-d0f3-4588-98b1-d24c29091777` | gemini-cli | gemini-3.1-pro-preview | 8.396166823292924e-154 | 0 |
| 18 | `d94fcf06-a5a1-4cd3-9b85-436684f64c5e` | gemini-cli | gemini-3.1-pro-preview | 8.396166823291491e-154 | 0 |

## Observations at-a-glance
- **Zero answers hit `[0.55, 0.59]`.** No "near-miss". The closest single answer is **0.18** (still ~3× below 0.55), and is the only answer above 1e-6.
- **17 / 18 runs returned an extremely small p-value** (1e-7 to 1e-154). All of these come from one statistical decision: pooling individual miRNA observations into a single ANOVA across cell types. With ~10⁵ miRNAs × samples, ANOVA on cell-type means buried in observation-level variance becomes massively significant.
- **Answers cluster within harness/model**:
  - codex/gpt-5.4 + terminus-2/gpt-5.4 (6 runs): 5 / 6 produced **`2.72e-41`** identically — they're computing the same thing with the same library, on the same data, deterministically.
  - terminus-2/claude-opus-4-6 (3 runs): 2 / 3 produced **`1.12e-10`** identically.
  - gemini-cli (3 runs): all produced **~8.396e-154** to 13 sig-figs. Floating-point noise only.
  - claude-code/opus (3 runs): three different answers (1.43e-21, 6.57e-52, 0.18) — opus *does* explore alternative aggregations, but only one of the three lands on 0.18.
- **The one "right-shaped" answer (0.18) was the agent that took PBMC log2 fold change as the question literally says** — see trajectory `e3ea324d`. Its number disagrees with the oracle (0.18 ≠ 0.55–0.59), and the verifier rejects it.
