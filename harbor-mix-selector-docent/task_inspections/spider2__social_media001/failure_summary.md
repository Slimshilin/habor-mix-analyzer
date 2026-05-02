# Failure Summary: All 18 Runs

## Failure Pattern Matrix

| Run ID | Model | Agent | First Failing Table | Failure Detail |
|---|---|---|---|---|
| 655dbf55 | claude-opus-4-6 | claude-code | twitter_posts_reporting | 199 rows vs 100 gold |
| 93ee02ec | claude-opus-4-6 | claude-code | twitter_posts_reporting | 199 rows vs 100 gold |
| 14ef67cb | claude-opus-4-6 | claude-code | twitter_posts_reporting | 199 rows vs 100 gold |
| 5fed6814 | claude-opus-4-6 | terminus-2 | rollup_report | 13 cols vs 14 gold (180 rows ok) |
| df7fc083 | claude-opus-4-6 | terminus-2 | twitter_posts_reporting | 199 rows vs 100 gold |
| 2d4505d3 | claude-opus-4-6 | terminus-2 | rollup_report | 13 cols vs 14 gold (180 rows ok) |
| a1eb8e36 | gemini-3.1-pro-preview | gemini-cli | instagram_posts_reporting | 3x11 shape correct but DATA mismatch |
| 7a638e46 | gemini-3.1-pro-preview | gemini-cli | rollup_report | 13 cols vs 14 gold |
| 387fc8d0 | gemini-3.1-pro-preview | gemini-cli | instagram_posts_reporting | 3x11 shape correct but DATA mismatch |
| bf690492 | gemini-3.1-pro-preview | terminus-2 | instagram_posts_reporting | 12 cols vs 11 gold (extra col) |
| b54d6fff | gemini-3.1-pro-preview | terminus-2 | instagram_posts_reporting | 10 cols vs 11 gold (missing col) |
| f531e9e5 | gemini-3.1-pro-preview | terminus-2 | instagram_posts_reporting | 13 cols vs 11 gold (2 extra cols) |
| f8521297 | gpt-5.4 | codex | instagram_posts_reporting | 13 cols vs 11 gold (2 extra cols) |
| c36d91b4 | gpt-5.4 | codex | instagram_posts_reporting | 13 cols vs 11 gold (2 extra cols) |
| 99898ba2 | gpt-5.4 | codex | instagram_posts_reporting | 13 cols vs 11 gold (2 extra cols) |
| dd2ff0ab | gpt-5.4 | terminus-2 | instagram_posts_reporting | 13 cols vs 11 gold (2 extra cols) |
| c5a1052c | gpt-5.4 | terminus-2 | instagram_posts_reporting | 10 cols vs 11 gold (missing col) |
| 4dcb284a | gpt-5.4 | terminus-2 | instagram_posts_reporting | 13 cols vs 11 gold (2 extra cols) |

## Failure Pattern Summary

### Pattern A: rollup_report missing column (4 runs)
- Runs: 5fed6814, 2d4505d3, 7a638e46, and implicitly others if they got past previous tables
- All produced instagram+twitter PASS but rollup has 13 cols instead of 14
- **This is the "closest" failure to success**

### Pattern B: twitter_posts_reporting row count (4 runs)
- Runs: 655dbf55, 93ee02ec, 14ef67cb, df7fc083
- All 3 claude-code runs + 1 terminus claude run
- Got 199 rows vs 100 gold — likely failed to deduplicate "most recent record"

### Pattern C: instagram_posts_reporting data mismatch (2 runs)
- Runs: a1eb8e36, 387fc8d0 (gemini-cli)
- Correct shape (3x11) but wrong VALUES — aggregation logic error

### Pattern D: instagram_posts_reporting column count wrong (8 runs)
- Various: too many (13 cols) or too few (10 cols)
- Most consistent failure for gpt-5.4 (all 6 runs) and gemini terminus (2/3 runs)

## Key Observation: Sequential Verifier
The verifier stops at the first failing table. All 18 runs fail on instagram OR twitter OR rollup.
Only 4 runs reached rollup (the final table) — these were the "best" attempts.
