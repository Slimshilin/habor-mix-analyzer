# Key files for `widesearch/widesearch-ws-zh-085`

The local repo does not contain the task source — these were reconstructed from the
Docent collection metadata (`agent_runs.metadata_json.task.*`).

| File | Path inside container | Notes |
| --- | --- | --- |
| Instruction (Chinese) | shown to agent at task start | See `instruction.md` |
| Verifier driver | `/tests/test.sh` | Calls `evaluate.py`; in `test_sh.txt` |
| Verifier scorer (hidden) | `/tests/evaluate.py` | Item-level F1; **not in metadata** — only inferred from stdout/behavior |
| Gold answer (hidden) | `/tests/gold_answer.csv` | 75 rows; **not visible to agent** |
| Eval config (hidden) | `/tests/eval_config.json` | Determines fuzzy-match thresholds; **not visible** |
| Reward sink | `/logs/verifier/reward.txt` | Holds final scalar reward (item-F1) |
| Agent output | `/workspace/output.md` | What the agent must produce |
| Canonical solver | `/solution/csv_to_markdown.py /solution/gold_answer.csv /workspace/output.md` | The "oracle" solution just dumps the gold table |
| Dockerfile | image build | `python:3.13-slim` + git + pandas/openai/dateparser/tenacity |
| `task.toml` | task spec | difficulty=hard, agent timeout=1800s, verifier timeout=600s, 1 cpu / 4GB / 10GB |

## Hidden-vs-visible inputs (a fair-task check)

- **Visible to agent**: only the Chinese instruction in the user message. No data files,
  no URL hints, no schema definition file, no examples.
- **Hidden from agent**: `gold_answer.csv`, `evaluate.py`, `eval_config.json`. The agent
  cannot read `/tests/` (verifier-only directory). The agent has no a-priori list of
  the 75 projects.
- The instruction does name the columns, the date window (Jan 1 – May 31, 2025),
  the fact that agents must output a single markdown table to `/workspace/output.md`,
  and the language (Chinese). It does **not** name source URLs (e.g. yidaiyilu.gov.cn);
  the agent must discover those itself.

## Agent harness × model matrix (3 trials each, 18 total)

| harness | model | comments |
| --- | --- | --- |
| `claude-code` | claude-opus-4-6 | native web fetch / search tools |
| `codex` (CLI) | gpt-5.4 | native web fetch / search tools |
| `gemini-cli` | gemini-3.1-pro-preview | native web search tool |
| `terminus-2` | claude-opus-4-6, gemini-3.1-pro-preview, gpt-5.4 | shell-only (no native browser); web access only via `curl`/`wget` |
