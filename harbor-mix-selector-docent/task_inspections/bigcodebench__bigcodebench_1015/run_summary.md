# Run Summary: bigcodebench_1015

Collection: 640e920a-aef3-4b7c-9487-69899ef19e9d
Task checksum: 1a87496faccfb2b0ac7530db63bcbec018f5ea7f7311e0cfd405f6144b61541c

## All 15 Runs

| Agent Run ID | Agent | Model | Reward | Role | response.* used | Key error |
|---|---|---|---|---|---|---|
| cbd79b0c | terminus-2 | claude-opus-4-6 | 1.0 | success | .content | — |
| 1e2cdb96 | terminus-2 | claude-opus-4-6 | 1.0 | success | .content | — |
| 5efa34e8 | codex | gpt-5.4 | 1.0 | success | .content | — |
| 2c224522 | codex | gpt-5.4 | 1.0 | success | .content (inferred) | — |
| 5ff404d4 | gemini-cli | gemini-3.1-pro-preview | 1.0 | success | .content | — |
| 648fe4f0 | terminus-2 | gemini-3.1-pro-preview | 1.0 | success | .content | — |
| a0d3a83c | terminus-2 | claude-opus-4-6 | 0.0 | failure | .text | TypeError: expected string or bytes-like object |
| a6c56191 | terminus-2 | gemini-3.1-pro-preview | 0.0 | failure | .text | TypeError: expected string or bytes-like object |
| 65bfcbc4 | terminus-2 | gemini-3.1-pro-preview | 0.0 | failure | .text | TypeError + pd.read_html(str) without io.StringIO |
| 22243362 | terminus-2 | gpt-5.4 | 0.0 | failure | .text | TypeError: initial_value must be str or None, not MagicMock |
| 79b5053b | terminus-2 | gpt-5.4 | 0.0 | failure | .text | AssertionError: 0 != 1 (exception swallowed) |
| 01a43073 | terminus-2 | gpt-5.4 | 0.0 | failure | .text | TypeError: expected string or bytes-like object |
| 66d924a8 | codex | gpt-5.4 | 0.0 | failure | .text | TypeError: expected string or bytes-like object |
| a9406701 | gemini-cli | gemini-3.1-pro-preview | 0.0 | failure | .text | OSError + TypeError |
| a4ba52ce | gemini-cli | gemini-3.1-pro-preview | 0.0 | failure | .text | AssertionError: 0 != 1 (exception swallowed) |

## Test Breakdown for Failing Runs

| Run ID | test_solution_exists | test_database_error | test_empty_table | test_invalid_url | test_local_file_url | test_valid_webpage_url |
|---|---|---|---|---|---|---|
| a0d3a83c | PASS | FAIL | FAIL | PASS | PASS | FAIL |
| a6c56191 | PASS | FAIL | FAIL | PASS | PASS | FAIL |
| 65bfcbc4 | PASS | FAIL | FAIL | PASS | FAIL | FAIL |
| 22243362 | PASS | FAIL | FAIL | PASS | PASS | FAIL |
| 79b5053b | PASS | FAIL | PASS | PASS | PASS | FAIL |
| 01a43073 | PASS | FAIL | FAIL | PASS | PASS | FAIL |
| 66d924a8 | PASS | FAIL | FAIL | PASS | PASS | FAIL |
| a9406701 | PASS | FAIL | FAIL | PASS | PASS | FAIL |
| a4ba52ce | PASS | FAIL | PASS | PASS | PASS | FAIL |

**Pattern:** test_invalid_url ALWAYS passes (the RequestException propagation works fine). 
test_local_file_url also passes in most failing cases (file:// handling is correct).
The failures concentrate on tests that involve HTTP mocking (test_valid_webpage_url, test_database_error, test_empty_table).
