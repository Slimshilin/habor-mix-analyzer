# Run Matrix: gso-numpy--numpy-83c780d

| Run ID | Model | Agent | Reward | Approach | Key failure |
|--------|-------|-------|--------|----------|-------------|
| 0bc02beb | claude-opus-4-6 | claude-code | 1.0 | C++ UFuncs (gold-style) | — |
| 08178892 | claude-opus-4-6 | terminus-2 | 1.0 | METH_FASTCALL C fast path | — |
| b5aaff45 | gpt-5.4 | codex | 1.0 | C fast path in multiarraymodule.c | — |
| 36b92e25 | gpt-5.4 | codex | 1.0 | Broader C fast path (5 methods) | — |
| 0b93d6a5 | claude-opus-4-6 | claude-code | 0.0 | C extension + Python fast path | Unicode-only, bytes unhandled |
| 98750d18 | claude-opus-4-6 | claude-code | 0.0 | C fast path in multiarraymodule.c | Unicode-only, bytes unhandled |
| 82489223 | claude-opus-4-6 | terminus-2 | 0.0 | METH_VARARGS C fast path | Just below threshold |
| 757cdee3 | claude-opus-4-6 | terminus-2 | 0.0 | METH_VARARGS C fast path | Just below threshold |
| ba0d666e | gemini-3.1-pro-preview | terminus-2 | 0.0 | frompyfunc (~1.06x) | NETWORK ERROR + weak approach |
| 8040e880 | gpt-5.4 | codex | 0.0 | C fast path (correct!) | NETWORK ERROR in eval |
| df466b90 | gemini-3.1-pro-preview | gemini-cli | 0.0 | Python _vec_string replacement | Python-level, ~1.06x |
| 3ef23267 | gemini-3.1-pro-preview | terminus-2 | 0.0 | Python list-comprehension | Python-level, ~1.04x |
| 7dc102b8 | gemini-3.1-pro-preview | terminus-2 | 0.0 | frompyfunc + uint8 sliding window | Python-level, ~1.06x |
| 96fbf376 | gemini-3.1-pro-preview | gemini-cli | 0.0 | Same as 7dc102b8, larger patch | Python-level, ~1.04x |
| b33b2725 | gemini-3.1-pro-preview | gemini-cli | 0.0 | frompyfunc | Python-level, ~1.06x |
| f9cd45fd | gpt-5.4 | terminus-2 | 0.0 | Tuple-reuse in _vec_string_with_args | Too shallow, ~1.01x |
| 8b2fb9dc | gpt-5.4 | terminus-2 | 0.0 | Attempted, then reverted | No net code change |
| d56dabb1 | gpt-5.4 | terminus-2 | 0.0 | Nothing committed | 0-byte patch |

## By Model
- claude-opus-4-6: 2/6 pass (33%)
- gpt-5.4: 2/6 pass (33%); would be 3/6 if 8040e880 network fixed
- gemini-3.1-pro-preview: 0/6 pass (0%)

## By Agent Type
- claude-code: 1/3 pass (33%)
- terminus-2: 1/7 pass (14%); 3 GPT/terminus-2 submitted no code
- codex: 2/3 pass (67%); would be 3/3 if 8040e880 network fixed
- gemini-cli: 0/3 pass (0%)
