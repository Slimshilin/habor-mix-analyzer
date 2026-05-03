# Task context (raw materials)

- `task_payload.json` — full agent prompt, dockerfile, oracle `solve.sh`, `test.sh`, `task.toml`.
- `run_metadata.json` — all 15 runs found in the Docent collection. `task_checksum = 788f50…2796e95a`. Reward column matches the URLs in the prompt.
- `transcripts_index.json` / `message_table_probe.json` — Docent metadata.
- `trajectories/<id>.md` and `<id>.json` — full exported transcripts (no sampling).
- `test_stdout/<id>.txt` — verifier output per run.

## Headline counts

15 runs, 1 pass, 14 fail. By bucket:

| Bucket | Runs | Outcome |
| --- | --- | --- |
| Pass | `136e3a42` (codex/gpt-5.4) | 18/18 |
| Tests run, partial pass | `92eb3056` codex/gpt-5.4 (15/18), `0241a42d` terminus-2/gemini-3.1-pro-preview (13/18), `0439140e` codex/gpt-5.4 (12/18), `647609d6` terminus-2/gemini-3.1-pro-preview (9/18), `c0feb22b` & `fcfe3b7f` gemini-cli/gemini-3.1-pro-preview (7/18 each), `26162475` & `6cefc9fa` terminus-2/claude-opus-4-6 (4/18 each), `0d33cc9e` terminus-2/gpt-5.4 (3/18) | reward 0 |
| Module-import error at test-collect time | `8b471998` terminus-2/gemini (`_convert_assessments_to_tool_types` not importable), `b3298c68` terminus-2/gpt-5.4 (`TraceLocationType` imported from wrong module), `a0d995b3` gemini-cli/gemini (IndentationError in `assessment_source.py`) | reward 0 |
| No agent code change | `394234e2` terminus-2/claude-opus-4-6 (AgentTimeoutError, no edits), `cf63bf46` terminus-2/gpt-5.4 (broken edits, ended up reverted) | reward 0 |

Pass per agent/model: codex/gpt-5.4 1/3, terminus-2/gpt-5.4 0/3, gemini-cli/gemini-3.1-pro-preview 0/3, terminus-2/gemini-3.1-pro-preview 0/3, terminus-2/claude-opus-4-6 0/3.

## Test surface

The verifier runs `pytest tests/genai/judges/test_judge_tool_search_traces.py` (FAIL_TO_PASS, 18 tests) and on success also `tests/cli/test_scorers.py tests/utils/test_doctor.py tests/store/artifact/test_models_artifact_repo.py tests/genai/judges/utils/test_parsing_utils.py tests/utils/test_credentials.py` (PASS_TO_PASS, 70 tests). Reward is 1 only if both groups pass.

## Test names that recur in failures

Across the ten substantive test-running runs:

| Test | Fail count out of 10 | Surface signal |
| --- | --- | --- |
| `test_search_traces_tool_invoke_invalid_trace_json` | 10/10 | `assert len(result) == 0` but agent returns 2 (None-filled records) |
| `test_search_traces_tool_invoke_partial_failure` | 10/10 | `assert len(result) == 1` but agent returns 2 |
| `test_search_traces_tool_invoke_success` | 6/10 | `assert result[0].request == 'request1'` but agent returns `'"request1"'` (json-wrapped) |
| `test_get_experiment_id_no_trace_location` | 7/10 | `pytest.raises(MlflowException, match='Current trace has no trace_location')` — agent raises `'The provided trace has no trace location information'` |
| `test_get_experiment_id_not_mlflow_experiment` | 7/10 | `match='Current trace is not from an MLflow experiment'` |
| `test_get_experiment_id_no_experiment_id` | 7/10 | `match='Current trace has no experiment_id'` |
| `test_search_traces_tool_get_definition` | 5/10 | shape/description mismatch on `ToolDefinition` |
| `test_convert_assessments_to_tool_types_*` (4 variants) | 5/10 | `source` field not the expected string, `valid`/`overrides` on `JudgeToolFeedback` not threaded |
| `test_search_traces_tool_invoke_search_fails` | 4/10 | inner `Exception` propagates instead of being re-raised as `MlflowException` |
