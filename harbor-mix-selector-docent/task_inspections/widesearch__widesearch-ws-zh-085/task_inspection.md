# Task inspection — `widesearch/widesearch-ws-zh-085`

- **Benchmark**: widesearch (Chinese-language wide-search subset)
- **Task ID**: `widesearch/widesearch-ws-zh-085`
- **Checksum**: `9da33e97cf4f4ae0838532be56210b35fb62ac61af229ec5879a0baf7d3c3ab4`
- **Difficulty**: hard / information-retrieval
- **Trials in collection**: 18 (3 each: claude-code/opus-4-6, codex/gpt-5.4,
  gemini-cli/gemini-3.1-pro, terminus-2/{opus-4-6, gemini-3.1-pro, gpt-5.4})
- **n_succ**: 12 (this is just "reward > 0", not "task solved")
- **Best reward across all 18**: **0.6059** (codex/gpt-5.4, 52/75 matched)
- **Original audit verdict**: ACCEPT (Gemini)
- **My verdict**: ⚠ **conditional reject — design is fragile in three concrete ways
  that prevent even a maximally capable agent from solving it as written.**
  The good news: every fragility has a cheap fix. See §6.

For the underlying detail behind every claim below, see the sibling files
[`instruction.md`](./instruction.md) (verbatim Chinese prompt + Dockerfile +
test.sh + task.toml), [`key_files.md`](./key_files.md) (visible-vs-hidden
inputs), and [`trajectories.md`](./trajectories.md) (per-run quotes).

---

## TL;DR

The verifier scoring is fair. The task topic is well-chosen.
But three concrete environmental defects, plus an under-specified rubric,
combine so that the **score gap between agent harnesses (0.0–0.6) is bigger
than the score gap between models within the same harness**.
That is the wrong shape for a benchmark trying to measure model capability,
and it is what makes me reject the task as currently written.

The single most valuable answer to the user's headline question:

> **Is failure due to the task or to agent capability?**
> **Both, layered.** The agentic-harness runs (claude-code / codex /
> gemini-cli) fail mostly on **agent stopping-criterion bottleneck** — they
> declare "I have enough data" after sampling 3-5 of the ~22 weekly reports.
> The terminus-2 runs fail mostly on **task-environment defects** — `curl`
> missing, source SPA hidden in `window.__NUXT__`, gold-source articles
> rolled off the live site. The task is designed for harnesses with a
> native browser tool; in a shell-only harness it is borderline-infeasible.
> The strongest single trial (codex/gpt-5.4 at 0.6059) is what we'd expect
> from a "good but not exhaustive" capable agent — confirming the
> agent-side ceiling is real, but it's only ~0.6 of gold even with a strong
> harness.

---

## 1. How close are agents to successfully completing the task?

The answer depends on what "complete" means; the verifier only reports
`item_f1` (per-cell F1 against the 75-row gold).

| Harness × model | Run rewards | Mean | Best matched/75 |
| --- | --- | --- | --- |
| codex × gpt-5.4 | 0.606, 0.602, 0.426 | 0.544 | 52 |
| claude-code × opus-4-6 | 0.548, 0.282, 0.226 | 0.352 | 45 |
| gemini-cli × gemini-3.1-pro | 0.204, 0.020, 0.019 | 0.081 | 11 |
| terminus-2 × gpt-5.4 | 0.042, 0.0, 0.0 | 0.014 | 2 |
| terminus-2 × gemini-3.1-pro | 0.025, 0.020, 0.0 | 0.015 | 1 |
| terminus-2 × opus-4-6 | 0.0, 0.0, 0.0 | 0.0 | 0 |

Reading by absolute closeness:
- **Single best trial: 0.606** = the verifier matched 52 of 75 rows; per-cell
  F1 is ~0.61. Given the gold has 5 cells/row × 75 rows = 375 cells, this
  corresponds to roughly **~210–220 correct cells out of 375** (cells in
  matched rows that exactly match the gold's strings).
- **No trial gets above 0.61.** No trial matched more than 52 rows. Even
  ignoring the 9 terminus-2 floors, the mean across the 9 agentic-harness
  runs is 0.331.
- **Gold-recall ceiling appears to be ~70 % of rows reachable**, because
  the canonical source (`yidaiyilu.gov.cn` weekly reports series) covers
  most but not all 75 projects in the gold. dff14e3d's regex parse of all
  18 weekly bulletins yielded 64 unique completion events — already 11
  short of 75 even if perfectly transcribed.

**Closeness verdict**: nobody is close to gold. The single best run is at
"just over half done." The variance across trials of the same agent is huge
(claude-code: 0.226–0.548; codex: 0.426–0.606), suggesting the task has a
high noise floor.

---

## 2. How do agent–model performances vary, and what's the surface vs. root cause?

There are two clean groups, and the gap between them is the central finding.

### 2.1 Group I — agentic-harness runs (claude-code, codex, gemini-cli)

These three harnesses ship a native web tool (WebSearch/WebFetch in
Anthropic, `web_search_call` with `open_page`/`find_in_page` in codex CLI,
`google_web_search` in gemini-cli). The model can issue queries and read
HTML without writing a scraper.

**Surface failure pattern across all 9 runs**: 19–61 rows produced (vs 75
gold), some rows wrong, several cells imprecise (especially 启动时间 and
承包公司).

**Root cause** (consistent across these 9 runs): **stopping criterion**.
Every one of these 9 runs **stopped on a self-judged "I have enough data"
message** — none hit the wall clock, none hit a tool-output cap, none
looped, none ran out of context. Concrete quotes:

> *"Now I have enough data. Let me compile the final table."* — a3accc0f
> *"现在我有足够的数据了 … 我觉得还是应该只列入那些能找到合理开工日期
> 的项目"* — 87a37e16
> *"候选项目已按"正式交付/投运"标准筛过一轮，核心字段也补齐到月度粒度，
> 现在开始写出最终单表。"* — 79701745
> *"已写入 /workspace/output.md."* — 7a50bd11

What separates 0.606 from 0.226 inside this group is **execution discipline**,
not "more searches" — the best run (`7a50bd11`) used **fewer** total turns
than the worst, but spent most of them on direct `open_page` calls into the
yidaiyilu.gov.cn weekly-report series rather than per-project enrichment
queries.

A secondary axis is the **ambiguity-policy choice** for missing 启动时间
data: a3accc0f wrote `未详`/`未检索到公开披露` and got 45/75; b6577605 and
87a37e16 dropped any project they couldn't date and got 16/75 and 12/75
respectively. Per-cell F1 punishes the conservative ones — but neither
strategy is requested by the prompt. **The agent is being asked to make a
judgment call the rubric doesn't disclose.**

### 2.2 Group II — terminus-2 runs (shell-only)

terminus-2 has only `bash` plus the standard `python:3.13-slim` toolset.
The image **does not include `curl`, `wget`, `lynx`, `w3m`, `requests`,
`bs4`, or `lxml`**. The only available primitives are `python3` + raw
`urllib.request`.

**Surface failures vary widely**: zero tool-use hallucination
(2011afcb), 14 fabricated rows (708974b2), header-only output
(489493bd, 9a983bb1), no file written (dff14e3d, 0751299c), 2-4
defensible rows (b3348dd8, 96ed4d96, d010e049).

**Root causes are environmental**, not capability:

1. **`curl` swallowed errors.** 708974b2's first 9 turns were
   `curl ... 2>/dev/null | head` — silently producing empty output because
   `curl` does not exist in the image. Agent misdiagnosed as "no network"
   and fabricated.
2. **Source SPA renders client-side.** Two opus-4-6 runs (dff14e3d,
   0751299c) and the best gpt-5.4 run (b3348dd8) all spent 30+ turns
   reverse-engineering that `yidaiyilu.gov.cn` is a Nuxt SPA whose article
   body lives in a minified `window.__NUXT__=(function(){…content:"…"})()`
   IIFE. dff14e3d only solved this around message 84 of 114.
3. **Bot-blocking on search engines.** Bing returns SSR'd HTML with
   anti-bot wrappers and Wiktionary-poisoned RSS; Baidu redirects through
   JS interstitials; only `html.duckduckgo.com` works, intermittently and
   rate-limited.
4. **WAFs / SSL / DNS errors on individual contractor sites.**
   `crcc.cn` returns a slider-CAPTCHA; `cmec.com` has a hostname-mismatch
   cert; `cwe.com.cn` has no DNS record; `ccccltd.cn` returns 403.
5. **Source retention window.** PowerChina's `pageId=7449` (国际项目)
   only retains articles from the last ~6 months. As of the run date
   (Apr 2026), the Jan-May 2025 articles that the gold answer relies
   on **had rolled off the live site**. Run 9a983bb1 confirmed this —
   "时间范围仅覆盖 2025年11月-2026年4月，没有 2025年1-5月记录."
6. **Library-rename trap.** Both terminus-2/gemini runs spent 5-8 turns
   on the `duckduckgo-search → ddgs` rename — the old package emits a
   warning and silently returns empty results. This is a Python
   ecosystem detail, not a research-skill test.

The picture: **same model in two harnesses produces 10-15× different
reward** (gpt-5.4 codex 0.42-0.61 vs terminus-2 0.0-0.04; opus-4-6
claude-code 0.23-0.55 vs terminus-2 0.00-0.00). That is the signature of
an **environment / harness affordance** dominating model capability.

### 2.3 Cross-group synthesis

| Layer | Behaviour | Verdict |
| --- | --- | --- |
| **Surface** (verifier-visible) | Missing rows, wrong cells, partial tables | Real |
| **Proximate cause** (model decisions) | Stop too early; pick wrong contractor when ambiguous; fill 启动时间 with guesses | **Real agent bottleneck** in Group I |
| **Root cause for Group I** | Lack of "enumerate-to-budget" planning; no internal "have I covered all weeks?" check | **Agent reasoning bottleneck** |
| **Root cause for Group II** | Container missing tools; SPA scrape engineering; gold sources rolled off | **Task-environment defect** |

The original Gemini audit's conclusion that *"failures appear to be genuine
retrieval misses rather than clerical errors"* is correct **for Group I**.
For Group II it is misleading — the failures there are not "retrieval
misses" but "the harness can't reach a working browser at all in 30 min."

---

## 3. Concrete agent behaviour vs. test failures

### 3.1 What the verifier expects (item_f1 over 75 rows × 5 columns)

```
test_sh:
  python3 evaluate.py \
    --output-file /workspace/output.md \
    --gold-file   /tests/gold_answer.csv \
    --eval-config /tests/eval_config.json \
    --reward-file /logs/verifier/reward.txt \
    --reward-json /logs/verifier/reward.json \
    --workspace-dir /workspace
```

The `evaluate.py` and `gold_answer.csv` are mounted in `/tests/` (verifier-only;
agent cannot read them). What they contain has to be inferred from observed
behaviour:

- **Row alignment**: `matched=N/75` is reported, so the verifier first
  attempts to align rows between agent output and gold (by 国家 + 项目名称
  fuzzy match — 96ed4d96 with 4 rows got 1 match, b3348dd8 with 2 rows
  got 2 matches, suggesting near-exact matching of country + project name
  is required to align).
- **Item F1 over cells of matched rows**: `item_f1` is then computed
  per-cell within the matched rows. Cells outside matched rows count as
  zero. This is why a3accc0f's 57 rows (45 matched) → 0.55 while
  87a37e16's 19 rows (12 matched) → 0.23.
- **Workspace fallback**: when `output.md` is not parseable, the verifier
  scans `/workspace` for any markdown-table-shaped file. dff14e3d's run
  reports *"No table found in /workspace/output.md or workspace
  /workspace"* — confirms the fallback exists and confirms the file truly
  was missing.

### 3.2 Concrete examples of expected vs. produced

**Run 7a50bd11 (best, 0.606)** — example correct row that scored full credit:

```
| 喀麦隆 | 恩图至恩乔莱公路 | 中铁二十局集团有限公司 | 2021年10月 | 2025年1月 |
```
This row appears in 96ed4d96's 4-row table verbatim too — country, project,
contractor, both dates all align with the gold.

**Run 79701745 (0.426)** — likely-wrong contractor that lost cells:

```
| 阿根廷 | Mariana 盐湖项目 | 赣锋锂业股份有限公司 | 2022 | 2025年2月 |
```
vs. run 7a50bd11's matching row:
```
| 阿根廷 | Mariana 盐湖项目 | 中铁十局集团有限公司 | … | 2025年2月 |
```
Gold likely says `中铁十局` (the EPC contractor named in the 一带一路网
weekly report) — Ganfeng is the lithium *owner*, not the EPC. The
instruction's "承包公司" is structurally ambiguous; the verifier silently
chose one interpretation.

**Run f6d027a4 (0.602)** — cell-pollution that lost cells:

```
| 喀麦隆 | 克里比深水港二期 | 中国港湾… | 2017年11月 | 2025年2月（交工）、2025年5月（投运） |
```
vs. the implied gold cell `2025年2月` or `2025年5月` (one or the other).
The agent's parenthetical annotation breaks string matching even though
the data is correct.

**Run 708974b2 (0.0)** — fabrication that aligned no rows:

```
| 印度尼西亚 | 雅万高铁延伸线 | 中铁国际 | 2023年10月 | 2025年1月 |
```
This project did not have a 2025年1月 completion — agent invented it from
training-data memory after the silent `curl: command not found` failure.
Gold has zero rows aligning with this fabrication.

**Run dff14e3d (0.0, "No table found")** — the most painful failure mode:
the agent had **64 verified completion events** in
`/workspace/all_completions.txt` when the wall clock killed it. It just
hadn't written `/workspace/output.md` yet. The verifier sees zero.

---

## 4. Is this task self-contained and theoretically achievable?

Working through the user's framework explicitly:

### 4.1 What can the agent infer from instruction + environment?

**Inferable**:
- The 5-column schema and Chinese-language requirement (stated explicitly).
- The Jan 1 – May 31, 2025 window (stated explicitly).
- Output path `/workspace/output.md` (stated explicitly).
- That the data lives on Chinese government / SOE / state-media websites
  (inferable from the topic — "Belt and Road" + "中企海外项目").

**Not inferable**:
- Source URLs. The instruction never names `yidaiyilu.gov.cn`,
  `cehome.com`, `imsilkroad.com`, `xinhuanet.com`, etc. The agent must
  discover these.
- The verifier's exact column-string conventions. E.g. for 承包公司, gold
  uses one of {EPC contractor / parent group / financing entity} per
  project, not consistently. The agent has no examples.
- That the verifier scores by item_f1 and falls back to workspace-scan.
  This isn't strictly necessary to know, but it changes the optimal
  strategy (e.g. `未详` is at parity with no row at all, so don't bother
  including unverified projects).

### 4.2 Hidden tests issue

The verifier's column conventions are effectively a **hidden specification**.
The instruction says "承包公司" but doesn't define whether for the
Argentina-Mariana project the answer is the lithium owner (`赣锋锂业`),
the parent state-owned EPC (`中国港湾`), or the actual on-site contractor
(`中铁十局`). All three are defensible Chinese-language answers and all
three appear in different press releases. The verifier picks one and
silently penalizes the other two.

Run 79701745 and run 7a50bd11 disagree on this exact field for the same
project — they cannot both be wrong, but the task gives the agent no way
to know which interpretation the gold uses. **This is a real task-design
issue.**

### 4.3 Could a "super-capable being" solve this?

Not as written, in the terminus-2 harness, in the configured container:
- **PowerChina retention window**: gold-source articles for Jan-May 2025
  are no longer at their original URLs as of run time (Apr 2026). Run
  9a983bb1 reverse-engineered the API and **proved** this. Even an
  unboundedly capable agent cannot fetch what the server doesn't serve.
  Web Archive / archive.org access is the only workaround, and the
  instruction doesn't mention it.
- **30 min × 1 CPU × shell-only**: even with archived snapshots, paging
  ~22 weekly bulletins, deduplicating completions across them, AND
  running per-project enrichment for 75 start dates, fits inside 30
  minutes only if Bing/DuckDuckGo cooperate. They don't, reliably.

In the agentic-harness configurations (codex / claude-code / gemini-cli),
the task is **theoretically achievable** — the data was reachable from
yidaiyilu.gov.cn and weekly-report mirrors at the time the task was
authored, and the gold appears to be constructed from these sources. The
combination "perfect enumeration + perfect cell-string discipline +
correct ambiguity-policy guesses" would yield ~0.85+. No agent in the 18
trials achieves that combination.

So the answer is split:
- ✅ Task is **theoretically self-contained for codex/claude-code/gemini-cli
  harnesses** at the time of authoring.
- ❌ Task is **NOT theoretically self-contained for terminus-2** under the
  given Dockerfile.
- ❌ Task is **temporally fragile** — gold sources have begun rolling off
  primary sites; in another 6 months Group I may also become infeasible.

---

## 5. Specific task-quality issues found

(Each is independently fixable. None is fatal alone; together they make
the task much weaker than the original audit suggested.)

| # | Issue | Evidence | Severity |
| --- | --- | --- | --- |
| **A** | Container lacks `curl`/`wget`/`requests`/`bs4` | All 9 terminus-2 runs blocked on this; 708974b2 hallucinated everything because `curl: command not found` was hidden by `2>/dev/null` | **High** |
| **B** | Source data has retention windows | Run 9a983bb1 confirmed PowerChina pageId=7449 only retains articles from Nov 2025 onward | **High** (gets worse with time) |
| **C** | "承包公司" structurally ambiguous | Runs 7a50bd11 and 79701745 disagree on the contractor for Mariana, both citing different defensible primary sources | **Medium** |
| **D** | "启动时间" rarely in completion announcement | Across all Group I runs, agents either left this `未详` or invented dates; per-cell F1 rewards confident guessing over honest unknowns | **Medium** |
| **E** | Per-cell `item_f1` favours invented dates over `未详` | a3accc0f's 47 `未详` cells score 0; runs that confidently guess wrong dates also score 0; only correct guesses win — but the task gives no way to verify guesses | **Medium** |
| **F** | DDGS package-rename pitfall | Both terminus-2/gemini runs lost 5-8 turns to `duckduckgo-search → ddgs` rename | **Low** (fixable by pin) |
| **G** | Tool-availability `2>/dev/null` trap | `curl: command not found` is silent; agent has no signal | **Low** (more an agent-skill issue) |
| **H** | 30-min wall × 1 CPU × 75 rows is borderline | Even Group I best (7a50bd11) reaches only 52 matched rows in 30 min | **Low** (intentional difficulty) |
| **I** | No source-URL hint | Instruction's "全量检索" implies internet research; relying on agent to find a Chinese-government site without naming it is fair, but compounds when search APIs flake | **Low** |

Issues **A** (container) and **B** (retention) together make the task
non-deterministic across time — the same gold may become unreachable
without re-running the data collection. Issue **C** (承包公司) is a
genuine rubric defect: there is no objectively correct answer, and the
gold encodes one without telling the agent.

---

## 6. Proposed fixes (not simplifications)

I'm not proposing to make this task easier — the user is right that "good
task that exposes agent bottlenecks" is the goal. The proposals below
remove fragility without lowering the bar.

### 6.1 Container fixes (cheap, high-leverage)

```diff
 FROM python:3.13-slim
 WORKDIR /workspace
 RUN apt-get update && apt-get install -y \
-    git \
+    git curl wget jq \
     && rm -rf /var/lib/apt/lists/*
-RUN pip install --no-cache-dir pandas openai dateparser tenacity
+RUN pip install --no-cache-dir pandas openai dateparser tenacity \
+    requests beautifulsoup4 lxml ddgs
```

This removes Issues **A**, **F**, **G** outright. It does **not** make the
task easier — the searching, deduplication, enumeration, and cell-string
discipline are still 100% on the agent. It just removes the
"random Python ecosystem trivia tax" that has nothing to do with the
agent's actual reasoning ability.

Estimated effect on Group II rewards: probably 0.0 → 0.1–0.3 (still poor,
because the harness lacks a native browser, but at least not a silent
floor). Group I rewards: unchanged.

### 6.2 Snapshot the gold sources (mid-leverage, fixes time-decay)

The task should ship a local cached snapshot of the relevant
yidaiyilu.gov.cn weekly bulletins (Jan-May 2025) inside `/data/` (read-only
mount). This kills Issue **B**: the agent doesn't have to gamble that the
live SPA still serves the articles.

```toml
[environment]
mounts.read_only = [
  { src = "/data/widesearch-zh-085/yidaiyilu_bulletins_2025-01-to-05/", dst = "/data/sources" },
  { src = "/data/widesearch-zh-085/news_articles_2025-01-to-05/", dst = "/data/news" },
]
```

The instruction would gain one sentence: *"Reference materials are
available under `/data/sources` and `/data/news`. You may also use the
internet."*

This converts the task from "scrape JS-rendered SPAs in 30 min" to
"reason over a corpus + enrich with web search" — same task family,
much less fragile. **This is the single most valuable fix.**

### 6.3 Define the rubric (cheap, fixes ambiguity)

The instruction should include a short rubric block clarifying the two
genuine ambiguities:

```
## Rubric guidance for ambiguous cells

- **承包公司**: use the EPC contractor (the entity that physically built
  the project), not the financing entity, the owner, or the parent group.
  Where multiple contractors are jointly named in the source, list them
  comma-separated in the order they appear.
- **启动时间** / **竣工时间**: use the construction-start month and
  commissioning/operation month respectively, both rounded to month
  precision in the form "YYYY年M月". If the source does not specify, write
  "未详" (this counts as no answer for that cell, not as wrong).
```

This fixes Issues **C** and **D**, and eliminates the "lottery" effect
where an agent's defensible-but-wrong-by-rubric contractor choice tanks
its score on rows it otherwise nailed.

### 6.4 Tighten the verifier (medium-leverage)

`item_f1` over 5 cells × 75 rows is a reasonable scoring choice, but the
current implementation (inferred from behaviour) appears to use exact
string match per cell. Two small upgrades:

1. **Date normalization**: parse `2025年2月` / `2025-02` / `2025/2` /
   `2025年2月（交工）` / `February 2025` to a canonical month and compare
   on canonical form. (The image already has `dateparser` installed —
   it's just not used.) This kills Issue **F** without making the task
   easier.
2. **Score `未详` separately**: a cell with the literal string `未详` (or
   the rubric-named placeholder) should count as "agent honestly opted
   out" — neither rewarded nor penalized — vs. wrong-cell which is
   penalized. This rebalances Issue **E** so the optimal strategy is no
   longer "guess confidently."

### 6.5 Optional: relax the wall clock

Bumping `agent.timeout_sec` from 1800 (30 min) to 2700 (45 min) for tasks
with `category="information-retrieval"` and gold size > 50 rows would
remove the "ran out of time on the final write" failure (dff14e3d,
0751299c). This is a non-trivial cost increase but cleanly maps a real
bottleneck to wall-clock budget rather than capability.

### 6.6 Combined predicted effect

If fixes 6.1–6.4 are applied, my estimate of the new reward distribution
(based on observed behaviour) is:

| Harness × model | Current best | Predicted best after fix |
| --- | --- | --- |
| codex × gpt-5.4 | 0.61 | 0.78–0.85 |
| claude-code × opus-4-6 | 0.55 | 0.70–0.80 |
| gemini-cli × gemini-3.1-pro | 0.20 | 0.40–0.55 |
| terminus-2 × gpt-5.4 | 0.04 | 0.30–0.50 |
| terminus-2 × opus-4-6 | 0.00 | 0.30–0.55 |
| terminus-2 × gemini-3.1-pro | 0.03 | 0.20–0.40 |

The point is not the absolute numbers — it is that the reward gap between
**Group I and Group II shrinks from "10-15× apart" to "comparable
order of magnitude."** That is the shape a good benchmark should have,
because the model is what's nominally being measured.

---

## 7. Final verdict

**On the original "Is failure due to the task or to agent capability?":**
- For agentic-harness runs: **agent capability** (specifically: stopping-
  criterion bottleneck and ambiguity-policy choice). These runs would
  benefit from a clearer rubric (§6.3) but the underlying gap is real.
- For shell-only (terminus-2) runs: **task environment**. The container
  shipped without `curl`, the source SPA hides content in JS, and parts
  of the gold sources have rolled off the live web. Same model in
  another harness scores 10-15× higher.

**On task-quality and review:** I recommend **rejecting this task as
written** and re-accepting after fixes 6.1–6.4. The original Gemini
audit's evaluation is partially correct ("genuine retrieval misses") for
Group I but does not see the structural environmental defects that zero
out Group II. The audit also did not catch the "承包公司" ambiguity,
which is a real rubric defect, nor the "未详 vs guess" pathology that
biases the metric.

**What this task does measure well**, even with current defects:
- **Long-horizon enumeration discipline**: codex-CLI's 7a50bd11 win
  reflects genuine "page through 15 weekly bulletins systematically"
  behaviour that the other agents lacked. This is a real, useful signal.
- **Stopping-criterion calibration**: the 0.226 vs. 0.548 spread inside
  claude-code is purely about when to stop — also a real, useful signal.
- **Honest-unknown vs. confident-guess tradeoff**: 79701745 vs. 7a50bd11
  shows that reckless filling of unknown 启动时间 is worse than honest
  placeholders. Useful — but **only** if §6.4's "score 未详 separately"
  fix is applied; otherwise the metric pushes in the opposite direction.

The task is salvageable with cheap fixes. It is not salvageable as
written.
