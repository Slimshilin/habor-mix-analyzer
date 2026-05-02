# Per-trajectory observations (all 18 runs)

This file is the underlying evidence for `task_inspection.md`. Each trajectory was
read end-to-end (via `mcp__plugin_docent_docent__get_agent_run_messages`); short
verbatim quotes are kept here so claims can be checked.

Reward-score legend: per-cell `item_f1` over a 5-column / 75-row gold answer.
"matched=N/75" is rows the verifier matched (rows where 国家 + 项目名称 are close
enough to align — partial cell credit comes after that alignment).

## Quick scoreboard

| Run ID | Harness | Model | Reward | Matched | Notes |
| --- | --- | --- | --- | --- | --- |
| `a3accc0f` | claude-code | claude-opus-4-6 | **0.5485** | 45/75 | 57 rows; 47 启动时间 set to "未详" |
| `b6577605` | claude-code | claude-opus-4-6 | 0.2816 | 16/75 | 23 rows; agent self-restricted to confidently-dated projects |
| `87a37e16` | claude-code | claude-opus-4-6 | 0.2255 | 12/75 | 19 rows; same self-restriction + 2-3 likely-wrong dates |
| `7a50bd11` | codex | gpt-5.4 | **0.6059** | 52/75 | **best in collection**; 61 rows from 15 weekly reports |
| `f6d027a4` | codex | gpt-5.4 | 0.6016 | 44/75 | 47 rows; cells polluted with `(交工)` `(投运)` parentheticals |
| `79701745` | codex | gpt-5.4 | 0.4257 | 28/75 | 34 rows; over-confident 启动时间 guesses |
| `5fe051c5` | gemini-cli | gemini-3.1-pro-preview | 0.2044 | 11/75 | 15 rows from a single grounded-search summary |
| `5f2e1a93` | gemini-cli | gemini-3.1-pro-preview | 0.0195 | 1/75 | search API returned empty → fell back to memory → 7 hallucinated rows |
| `173715c4` | gemini-cli | gemini-3.1-pro-preview | 0.0190 | 1/75 | search API empty → 9 hallucinated rows |
| `dff14e3d` | terminus-2 | claude-opus-4-6 | 0.0 | 0/75 | **AgentTimeoutError** — extracted 64 events from yidaiyilu.gov.cn but never wrote `output.md` |
| `708974b2` | terminus-2 | claude-opus-4-6 | 0.0 | 0/75 | `curl` missing in image; failed silently; fabricated 14 rows from memory |
| `0751299c` | terminus-2 | claude-opus-4-6 | 0.0 | 0/75 | **AgentTimeoutError** — pivoted to `urllib`, found 135 events, ran out of time on start-date enrichment |
| `96ed4d96` | terminus-2 | gemini-3.1-pro-preview | 0.0253 | 1/75 | 4 row table written; verifier picked `readable_results.txt` (intermediate dump) |
| `d010e049` | terminus-2 | gemini-3.1-pro-preview | 0.0203 | 1/75 | 4 rows; same DDGS package-rename pitfall ate most of budget |
| `2011afcb` | terminus-2 | gemini-3.1-pro-preview | 0.0 | 0/75 | **zero tool calls**; 8 hallucinated rows in one turn |
| `b3348dd8` | terminus-2 | gpt-5.4 | 0.0416 | 2/75 | 2 rows correctly mined from CRBC site (mid-run shell wedge wasted ~6 turns) |
| `489493bd` | terminus-2 | gpt-5.4 | 0.0 | 0/75 | header-only output; refused to fabricate after Bing RSS poisoning + WAF/SSL/DNS errors |
| `9a983bb1` | terminus-2 | gpt-5.4 | 0.0 | 0/75 | **AgentTimeoutError** — solved PowerChina API, but Jan-May 2025 articles had rolled off; idled 400 turns |

---

## A. claude-code × claude-opus-4-6

All three runs use the same loop: `WebSearch` → `WebFetch` → final `Write`. None
use shell. All three stop on a self-judged "I have enough data" message —
**no run hits a tool/context/timeout limit**.

- `a3accc0f` (best, 0.5485): 25 WebSearch + 6 WebFetch calls. Visited
  `yidaiyilu.gov.cn/p/0NDE4SRS.html`, `cehome.com/news/20250328/331113.shtml`,
  `cehome.com/news/20250411/333427.shtml`, `wap.imsilkroad.com/p/536545.html`.
  Filled 47 of 57 启动时间 cells with `未详` (defensible — sources don't always
  state it). Stop signal at message B105: *"Now I have enough data. Let me
  compile the final table."*
- `b6577605` (0.2816): 30+ WebSearch, **0 WebFetch** — only ever read snippets,
  never raw HTML. Self-imposed quality bar — only kept rows with a confident
  start date — collapsed coverage from ~57 candidates to 23 rows. Stop signal:
  *"Now I have enough information to compile the table."*
- `87a37e16` (0.2255): same pattern as b6577605. 19 rows, several with
  invented start years (e.g. 巴西布济乌斯 starting `2013年10月` is the field
  discovery date, not construction start). Stop signal: *"既然这些项目出现在
  一带一路周报中，我就将它们纳入 … 现在我有足够的数据了"*.

**Three trials' divergence in row count (57 / 23 / 19) is driven by an
unprompted ambiguity-policy choice**, not by capability. Per-cell F1 punishes
the conservative ones.

## B. codex × gpt-5.4

All three runs use the codex-CLI native browser stack
(`web_search_call` with action types `search`, `open_page`, `find_in_page`)
plus `exec_command` for shell. All three stop on self-judged "good enough."

- `7a50bd11` (best, 0.6059): 8 searches + **32 `open_page` calls** + 4
  `find_in_page` + 13 shell calls. Walked the weekly-report series on
  `yidaiyilu.gov.cn` directly — opened ~15 distinct issue URLs (`0G49KN1G`,
  `02B12EH9`, `0NDE4SRS`, `0NGNG757`, `0DML6SP7`, `0M6HJ806`, `0K1ICBV0`,
  `0LAN3I2R`, `0HR8OVA7`, `0DS8487N`, `0L020TBM`, `0JPF78JN`, `00V8KD8F`,
  `0MOFVH7J`, `03FPAILE`). Wrote 61 rows via `apply_patch` once, end of run.
- `f6d027a4` (0.6016): 30 searches but only 3 `open_page` — over-relied on
  Bing/DuckDuckGo via `urllib` (most returned empty). Cells polluted with
  parentheticals like `2025年2月（交工）、2025年5月（投运）` and
  `2025年2月（交付；2024年12月完工）`, hurting cell F1.
- `79701745` (0.4257): burned turns recovering from `requests`/`urllib`
  `ModuleNotFoundError`, ended at 34 rows. Misattributed contractor for
  Mariana lithium project (assigned `赣锋锂业` — the lithium owner — vs run 1's
  correct `中铁十局集团`).

**Best-of-collection insight**: 7a50bd11 won by trusting one source
(yidaiyilu.gov.cn weekly reports), paging it widely with the harness's
native `open_page`, and accepting `未检索到公开披露` for unknown start dates
rather than guessing.

## C. gemini-cli × gemini-3.1-pro-preview

- `5fe051c5` (0.2044): five `google_web_search` calls + one `write_file`.
  First search returned a Vertex-AI-grounded summary already enumerating ~16
  projects with sources. Agent treated the digest as the answer set, never
  opened a URL or paged anything. Writes 15 rows.
- `5f2e1a93` (0.0195): two `google_web_search` calls returned empty bodies
  (apparent quota / API failure). Internal monologue verbatim: *"Addressing
  the Quota Issue: I've hit a web search quota limit … Relying on Internal
  Knowledge: I'm encountering a quota error with the Google Web Search API.
  Consequently, I will now depend on my internal knowledge base."* Wrote 7
  hallucinated rows.
- `173715c4` (0.0190): five parallel `google_web_search` calls all returned
  empty. Same fall-back-to-memory pattern. 9 hallucinated rows.

**No refusal language anywhere** — the "Chinese government content refusal"
hypothesis can be ruled out for these traces.

**Search-tool degradation invalidates 2 of 3 trials.** Only run 5fe051c5 is
a meaningful measurement of gemini-3.1-pro on this task.

## D. terminus-2 × claude-opus-4-6

`terminus-2` is shell-only — no native browser tool. The Docker image
(`python:3.13-slim`) ships **without `curl`, `wget`, `lynx`, or `w3m`**, and
without `requests`/`bs4`/`lxml`. This is the dominant constraint.

- `708974b2` (0.0): first command was
  `curl -s 'https://www.google.com/search?q=...' 2>/dev/null | head -200`.
  Output empty — `curl` is missing, but `2>/dev/null` swallowed the
  `bash: curl: command not found` error. Agent silently piped nothing for 9
  turns. After diagnosing (`bash: ping: command not found` too), concluded
  "no network access, must rely on training" and **fabricated 14 rows from
  memory**, including obviously-wrong entries like
  `Karot Hydropower 2022完工` mislabelled as 2025. Self-stopped with
  `task_complete=true`.
- `dff14e3d` (0.0, AgentTimeoutError): first command's `apt-get install -y
  curl wget` succeeded. Then debugged that `yidaiyilu.gov.cn` is a Nuxt SPA
  whose article body lives in a minified `window.__NUXT__=(function(){return
  {…,content:"…"}})(...)` IIFE. Around B83 the agent extracted the
  `content:"..."` field correctly, mass-fetched ~18 weekly bulletins, and
  parsed **64 unique completion events** to `/workspace/all_completions.txt`.
  **Never converted to `output.md`** — last block (B114) is mid-`cat` of the
  parsed events file. Wall clock killed it.
- `0751299c` (0.0, AgentTimeoutError): pivoted from missing-curl to Python
  `urllib` with custom SSL context. Pulled 135 events claimed across all
  Jan-May 2025 weekly bulletins. Started running per-project DuckDuckGo
  enrichment for start dates with `time.sleep(2)` between queries, was
  rate-limited, **ran out of time before writing `output.md`**.

## E. terminus-2 × gemini-3.1-pro-preview

- `96ed4d96` (0.0253): Hit the `duckduckgo-search` package-rename pitfall —
  `RuntimeWarning: This package has been renamed to ddgs!` — got empty results.
  Eventually `pip install ddgs` and re-ran — that worked. Wrote
  `/workspace/output.md` with 4 rows (all defensible). The verifier message
  "found table in /workspace/readable_results.txt" refers to a **secondary
  fallback scan** of an intermediate snippet dump file the agent had created
  earlier — the agent **did** write the correct file.
- `d010e049` (0.0203): same DDGS-rename pitfall, eventually worked via
  `html.duckduckgo.com/html/?q=…`. 4 rows.
- `2011afcb` (0.0): **zero tool calls**. First (and only) action: write 8
  rows from memory. Self-stopped at the very first turn.

## F. terminus-2 × openai/gpt-5.4

- `b3348dd8` (0.0416): same `urllib`-only constraints. Mid-run a here-doc
  wedged the terminal for ~6 turns (`bash: C-c: command not found`).
  Reverse-engineered CRBC index page pattern
  `/site/crbc/274/info/2025/<id>.html`, scraped 48 articles, found 5
  candidates, kept the 2 that fell in Jan-May 2025. **Both rows are
  correct** but only 2 of 75 gold rows are reachable from CRBC alone.
- `489493bd` (0.0): Bing RSS returned wildly off-topic English results
  (`how_much - Wiktionary`, copyright text). Direct site fetches failed
  with: `cmec.com SSL CERTIFICATE_VERIFY_FAILED`, `chmc.cc 404`, `cwe.com.cn
  Name or service not known`, `geb.com.cn timed out`, `ccccltd.cn 403`,
  `crcc.cn` returned a slider-CAPTCHA WAF page. CEEC 2025 links were all
  HR notices and ESG videos. PowerChina's only 2025 link was a fraud
  warning. Agent wrote header-only and self-stopped: *"基于现有可验证
  信息，继续检索大概率收益有限且存在杜撰风险，因此应提交当前最稳妥结果。"*
- `9a983bb1` (0.0, AgentTimeoutError): solved PowerChina's
  `/api-gateway/jpaas-publish-server/front/page/build/unit` API by
  reverse-engineering `paramJson`/`pageNo`/`pageSize`. Pulled `pageId=7449`
  (国际项目, 92 records) — **dates ranged Nov 2025 – Apr 2026, with NO
  Jan-May 2025 entries**. The category page does not retain articles older
  than ~6 months. Agent then froze for 400 turns
  emitting `Plan: 不执行命令，保持未完成` until the wall clock killed it.
