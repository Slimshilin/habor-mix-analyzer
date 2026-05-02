# Failure modes — `aa-lcr/aa-lcr-18`

## Failure-mode taxonomy

| Failure class | # of runs | Runs |
|---|---|---|
| **A. Infrastructure (auth 401)** | 3 | All claude-code/opus runs |
| **B. Tool-usage / context overflow** | 1 | gemini-cli run 627c5b3d (parallel full reads, no pagination) |
| **C. Reasoning (over-inclusion of Port Hedland)** | 13 | All other completed reasoning attempts |
| **Success** | 1 | codex/gpt-5.4 bfa55548 |

## A. Infrastructure failures (3 runs)

All three claude-code/claude-opus-4-6 runs returned only one assistant message containing:
```
Failed to authenticate. API Error: 401 {"error":{"code":"","message":"无效的令牌
(request id: 2026042803...)","type":"new_api_error"}}
```

The Chinese error string ("无效的令牌" = "invalid token") and the `new_api_error` type are characteristic of a third-party Anthropic-compatible relay/proxy, not Anthropic's own API. The harness produced a synthetic "assistant" turn carrying the upstream 401 instead of model output, which explains the metadata `total_steps=2, prompt_tokens=0, completion_tokens=0`. **No model inference occurred** in any of these three runs. They tell us nothing about claude-code's capability on this task and should be excluded from any conclusion about model performance.

## B. Tool-usage / context overflow (1 run)

`627c5b3d` (gemini-cli) issued three full-document `read_file` tool calls in parallel with no `start_line`/`end_line`. Each Digital Realty file returned a "Showing lines 1-2000 of 2899 total lines" truncation banner, dumping ~6 500 lines into context in a single shot. The transcript ends mid-tool-output of the third file with no follow-up assistant turn and no `write_file` call — the run terminated (token/turn budget exhausted) before any reasoning step could occur. **`/workspace/answer.txt` was never created.** This is a harness/agent tool-use failure, not a reasoning or task issue.

## C. Reasoning failure — over-inclusion of Port Hedland (13 runs)

This is the single most striking finding: across **5 distinct agent×model configurations** (codex/gpt-5.4 ×2, gemini-cli/gemini-3.1-pro ×2, terminus-2/opus-4-6 ×3, terminus-2/gemini-3.1-pro ×3, terminus-2/gpt-5.4 ×3), the failure pattern is **identical**:

1. Read NEXTDC's Development activity section in full (it is small, ~6 KB).
2. Identify three CY2023 capacity events: S3 Sydney +4 MW, M2 Melbourne +3 MW, PH1 Port Hedland 0.5 MW.
3. Search the two Digital Realty supplementals (typically via `grep`/`rg`, occasionally with full reads). Confirm Sydney = 4, Melbourne = 2, Port Hedland is absent from the metro table.
4. **Write a 3-line answer that includes "Port Hedland — 0".**

### Why this is a reasoning failure, not a retrieval failure

- The Sydney = 4 and Melbourne = 2 numbers are correctly retrieved every time.
- The agents that read with very low token budgets (terminus-2 runs: 18–30 K prompt tokens) get the same answer as the agents that read with very high budgets (gemini-cli: 436 K, 643 K). Token spend is uncorrelated with correctness because the retrieval was always sufficient.
- Several agents (notably terminus-2/opus run #3, `8d601bd1`) explicitly *consider* excluding Port Hedland on the grounds that Digital Realty has no presence there, then reverse themselves to include it.

### What the agents missed

The NEXTDC source uses two distinct verb phrases for the three sites:
- *"added X MW of built capacity"* — Sydney (S3) and Melbourne (M2). These are existing facilities receiving capacity expansions.
- *"opened to customers with 0.5 MW of built capacity"* — Port Hedland (PH1). This is a brand-new site coming online.

The question's predicate, *"cities we can be confident NEXTDC **added additional** built capacity"*, is most naturally read as expansions to existing built footprint — which excludes a site whose entire 0.5 MW is its inaugural offering. The successful run `bfa55548` is the only one that picked up this asymmetry.

Secondary supporting signal: *"how many data centers does Digital Realty have **in these cities**"* implicitly presupposes Digital Realty *has* presence in the answer cities; reporting "Port Hedland: 0" is a non-sequitur to the question.

## Test code that fails the agents

Grading is via `tests/llm_judge.py`:

```python
JUDGE_PROMPT = """Assess whether the following CANDIDATE ANSWER is CORRECT or INCORRECT.
For the CANDIDATE ANSWER to be correct, it must be consistent with the OFFICIAL ANSWER.

The question, for reference only: {question}
The OFFICIAL ANSWER: {correct_answer}
CANDIDATE ANSWER TO ASSESS: {predicted_answer}

Reply only with CORRECT or INCORRECT."""
```

OFFICIAL ANSWER: `Melbourne - 2, Sydney - 4`. The judge model (`gpt-5-mini`, `reasoning.effort=low`) is reasonably forgiving of formatting (colon vs. dash, multi-line vs. comma-separated) but a candidate that adds a third city Port Hedland with a value of 0 is materially different from the official answer — gpt-5-mini reliably marks it INCORRECT (consistent with all 13 runs scoring 0). Format alone is therefore not the failure point; the city-set difference is.

## Pattern across agent×model combinations

| Combination | Real reasoning attempts | Wrong-via-Port-Hedland |
|---|---|---|
| codex / gpt-5.4 | 3 | 2 (1 success) |
| gemini-cli / gemini-3.1-pro | 2 (1 crashed) | 2 |
| terminus-2 / opus-4-6 | 3 | 3 |
| terminus-2 / gemini-3.1-pro | 3 | 3 |
| terminus-2 / gpt-5.4 | 3 | 3 |
| **Total** | **14** | **13** |

The convergence is striking: 5 distinct (agent, model) configurations, ~14 independent samples, all but one make the same interpretive mistake. This is not a sampling fluke — it is a stable, reproducible bias in how current LLMs parse this question + source pair.
