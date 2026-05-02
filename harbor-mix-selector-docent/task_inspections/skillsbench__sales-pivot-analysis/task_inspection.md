# Task Inspection: skillsbench / sales-pivot-analysis

**Task checksum:** `7b6c12be477911c5278aea4533baf65a6cd50ce8241e9a87ea21612d9dce7308`  
**Benchmark:** skillsbench  
**Gemini audit verdict:** accept  
**Our verdict:** **REJECT** in current form (asymmetric resource provisioning); ACCEPT if the proposed Fix A is applied  
**Score:** 6/18 (33.3%) — claude-code 3/3, gemini-cli 3/3, codex 0/3 (one near-miss), terminus-2 0/6

> **Reconsidered with Opus 4.7 after initial Sonnet pass.** The verdict survived a second careful pass. The argument was sharpened around the *asymmetric resource provisioning* framing: the task declares `required_skills = ["xlsx", "pdf"]` and the Dockerfile provides them to 7 named agent frameworks but not to terminus-2. The reconsidered analysis also gives more weight to the discriminating power *among skill-equipped agents* (codex 1/3 used skills correctly; 2/3 had access but didn't use them) — which is what makes this task worth fixing rather than discarding outright.

---

## TL;DR

- **Pass-rate decomposition:** Success is fully determined by **agent framework**, not model. Same `claude-opus-4-6` model: 3/3 with claude-code (skills) → 0/3 with terminus-2 (no skills). Same `gemini-3.1-pro-preview` model: 3/3 with gemini-cli → 0/3 with terminus-2.
- **Single dominant failure mode** (11/12 failing runs): no real Excel `PivotTable` XML written; agents wrote pandas-aggregated static cells. The verifier crashes on `workbook[sheet]._pivots[0]` with `IndexError: list index out of range`.
- **Root cause** of the dominant failure: agents that did NOT activate / consult the `xlsx` skill defaulted to `pandas.pivot_table()` because openpyxl's pivot API is obscure and not in most training data.
- **Asymmetric resource provisioning:** Dockerfile copies the `xlsx` skill to `/root/.{claude,codex,opencode,agents,factory,goose,gemini}/skills/` — **no terminus-2 path, and terminus-2 has no `activate_skill()` mechanism**. All 6 terminus-2 runs are systematically denied access to a *declared-required* resource.
- **The task does discriminate well *among* skill-equipped agents** (codex used skills 1/3 of the time and that 1 nearly passed; codex 2/3 ignored available skills and failed). That part is fair.
- **Fix is small** (1 paragraph appended to instruction OR 1 file written into `/root/`) and would convert this from "rejected" to "high quality."

---

## Task Summary

Agents must:
1. Extract Australian SA2-level population data from a 74-page PDF (`/root/population.pdf`)
2. Read income data from an Excel file (`/root/income.xlsx`)
3. Merge on `SA2_CODE`, compute Q1–Q4 income quartiles from `MEDIAN_INCOME`, and `Total = EARNERS × MEDIAN_INCOME`
4. Produce `/root/demographic_analysis.xlsx` with 5 sheets: **SourceData** + four sheets containing **functional Excel PivotTable XML objects** (verifier checks `ws._pivots`, NOT just numeric content)

**Required skills (per `task_toml`):** `xlsx`, `pdf`. **Difficulty tag:** medium.

---

## Score Matrix (6/18 pass)

| Model | Agent | Reward | Tests Passed | Notes |
|---|---|---|---|---|
| claude-opus-4-6 | claude-code | 1.0 | 26/26 (3 skipped) | ✅ Used `Skill(skill=xlsx)` |
| claude-opus-4-6 | claude-code | 1.0 | 26/26 | ✅ |
| claude-opus-4-6 | claude-code | 1.0 | 26/26 | ✅ |
| claude-opus-4-6 | terminus-2 | 0.0 | 12/26 | ❌ No pivot XML; "Other Territories" |
| claude-opus-4-6 | terminus-2 | 0.0 | 12/26 | ❌ Same |
| claude-opus-4-6 | terminus-2 | 0.0 | 12/26 | ❌ Same |
| gemini-3.1-pro-preview | gemini-cli | 1.0 | 26/26 | ✅ Used `activate_skill(xlsx)` |
| gemini-3.1-pro-preview | gemini-cli | 1.0 | 26/26 | ✅ |
| gemini-3.1-pro-preview | gemini-cli | 1.0 | 26/26 | ✅ |
| gemini-3.1-pro-preview | terminus-2 | 0.0 | 11/26 | ❌ No pivot XML; SA2 join only 80% |
| gemini-3.1-pro-preview | terminus-2 | 0.0 | 11/26 | ❌ Same |
| gemini-3.1-pro-preview | terminus-2 | 0.0 | 11/26 | ❌ Same — also `AgentTimeoutError` |
| gpt-5.4 | codex | 0.0 | 13/26 | ❌ Had skill, didn't use it |
| gpt-5.4 | codex | 0.0 | 12/26 | ❌ Had skill, didn't use it; "Other Territories" |
| **gpt-5.4** | **codex** | **0.0** | **22/26** | **🟡 Used skill, real pivots, only `'nan'` in Quarter** |
| gpt-5.4 | terminus-2 | 0.0 | 13/26 | ❌ No pivot XML |
| gpt-5.4 | terminus-2 | 0.0 | 13/26 | ❌ No pivot XML |
| gpt-5.4 | terminus-2 | 0.0 | 12/26 | ❌ No pivot XML; `'nan'` quarter |

**Crucial observation:** Same model (e.g., `claude-opus-4-6`) goes from 100% success with a skill-aware framework (claude-code) to 0% with a skill-blind framework (terminus-2). The model is not the bottleneck — agent infrastructure is.

---

## 1. How close are agents to success?

| Bucket | Runs | What's missing |
|---|---|---|
| Full success | 6 | — |
| Near-success (1 test from passing) | 1 | run `8afeb161`: only `test_quarter_values_are_valid` failed because `'nan'` ended up in the Quarter column for rows where `MEDIAN_INCOME` was the `'np'` placeholder. A 1-line fix (`if pd.isna(val): return 'Q1'`) would have passed it. |
| Pivot-only failure (data logic correct) | 5 | runs `21afb32a`, `bb95013e`, `c1f053ba`: data logic fully correct, only missing real pivot XML. |
| Pivot + state contamination | 4 | 3× claude-opus/terminus-2 + run `901dca22`: also include `'Other Territories'` rows (left join, not inner join). |
| Pivot + truncated PDF parse | 3 | gemini/terminus-2: produced 1925–1961 rows instead of 2000+, missed ~500 SA2 entries. |

The "average" failure is just *one structural change* (`pandas.pivot_table()` → `openpyxl.pivot.table.TableDefinition`) away from passing. Agents almost universally got the data logic right; what they lacked was knowledge of openpyxl's pivot API.

---

## 2. Surface vs. root cause analysis (per question 2)

### Surface
For 11/12 failing runs the verifier dies on:
```
>   pivot = workbook[sheet_name]._pivots[0]
E   IndexError: list index out of range
```
The pivot worksheets exist with the right names; they just contain pre-computed values in plain cells, not pivot XML.

### Root cause: a knowledge gap, gated by a documentation gap

Openpyxl's `PivotTable` API is **not** what an LLM would produce from training-data prior. The publicly-prominent way to "make a pivot table in Python" is `pandas.pivot_table()`. The openpyxl pivot API is buried, sparsely documented, has the non-obvious `cacheId=0` constraint, and requires assembling six classes (`TableDefinition`, `CacheDefinition`, `CacheSource`, `WorksheetSource`, `SharedItems`, `CacheField`, `PivotField`, `RowColField`, `DataField`) in a specific order.

This is exactly the gap the bundled `xlsx` skill bridges. Inspecting the skill content (visible in the gemini-cli transcript) shows it:
- Loudly states "`cacheId` MUST be 0"
- Provides a complete worked example with all 9 classes
- Includes a 2D-pivot section that maps directly to "State Income Quartile"
- Lists every valid `axis`/`subtotal` value

So the chain is:

```
[skill provided to agent] → [agent tries openpyxl pivot API] → [pivot XML written] → [PASS]
                                            (or)
                                  [agent ignores skill] → [pandas fallback] → [FAIL]
                                            (or)
[skill NOT provided]      → [agent has no openpyxl knowledge] → [pandas fallback] → [FAIL]
```

### Why the model is largely irrelevant

If the model were the bottleneck, we'd expect performance to track the model. It does not:

| Model | With skill-aware agent | Without |
|---|---|---|
| claude-opus-4-6 | 3/3 (claude-code) | 0/3 (terminus-2) |
| gemini-3.1-pro-preview | 3/3 (gemini-cli) | 0/3 (terminus-2) |
| gpt-5.4 | 1/3 used skill, 2/3 didn't (codex) | 0/3 (terminus-2) |

The model's contribution is mostly visible in *whether the agent uses the skill once it has access* (gpt-5.4/codex was inconsistent: 1/3 used the skill; the other two ignored it).

### Surface vs. root cause for the four failure modes

| Failure mode | Surface | Root cause |
|---|---|---|
| No `_pivots` (11 runs) | `IndexError` on `_pivots[0]` | Either no skill access (terminus-2) OR skill ignored (codex 2/3). Both ultimately = openpyxl pivot API not invoked. |
| `'Other Territories'` (3 claude-opus/terminus-2 + 1 codex/gpt-5.4) | `assert not invalid` on `STATE` | Used left/outer join instead of inner join. Inner join would have dropped `'Other Territories'` automatically because income.xlsx has no rows with that state. **Could be inferred from data inspection** — the agent never noticed income.xlsx lacks `'Other Territories'` rows. |
| SA2 row count 1925–1961 (3 gemini/terminus-2) | row count < 2000 | gemini's pdfplumber parse missed ~500 rows. **Inferrable** by post-extraction sanity checks (compare row count to income.xlsx coverage). |
| `'nan'` in Quarter (2 runs incl. 8afeb161) | `assert` on Quarter values | `pd.qcut` / threshold comparisons left NaN as `'nan'` strings. **Inferrable** by inspecting income.xlsx — the `'np'` placeholder values in EARNERS / MEDIAN_INCOME are visible after read. |

The non-pivot failures (rows 2–4) all fall in the "should have noticed by inspecting the data" category — these *are* genuine agent capability gaps about exploring/auditing data before submitting. A super-capable agent would catch them. They do not depend on any skill or external knowledge.

---

## 3. What was expected vs. what agents produced (concrete examples)

### Expected (excerpt from oracle `solve.sh`)
```python
from openpyxl.pivot.table import TableDefinition, Location, PivotField, DataField, RowColField
from openpyxl.pivot.cache import CacheDefinition, CacheField, CacheSource, WorksheetSource, SharedItems

cache = CacheDefinition(
    cacheSource=CacheSource(type="worksheet",
        worksheetSource=WorksheetSource(ref=f"A1:I{num_rows}", sheet="SourceData")),
    cacheFields=[CacheField(name=h, sharedItems=SharedItems()) for h in HEADERS])

pivot = TableDefinition(name=name, cacheId=0,                     # cacheId MUST be 0
                        location=Location(ref="A3:F15", firstHeaderRow=1,
                                          firstDataRow=2, firstDataCol=1))
for i in range(len(HEADERS)):
    axis = "axisRow" if i == row_idx else ("axisCol" if i == col_idx else None)
    pivot.pivotFields.append(PivotField(axis=axis, dataField=(i == data_idx), showAll=False))
pivot.rowFields.append(RowColField(x=row_idx))
if col_idx: pivot.colFields.append(RowColField(x=col_idx))
pivot.dataFields.append(DataField(name=name, fld=data_idx, subtotal=subtotal))
pivot.cache = cache
pivot_ws._pivots.append(pivot)                                    # registers the pivot
```

### Actual (typical failing run, e.g. terminus-2 transcript)
```python
import pandas as pd
df_pop = pd.DataFrame(...)              # extracted from PDF
df_inc = pd.read_excel('/root/income.xlsx')
df = df_pop.merge(df_inc, on='SA2_CODE')
df['Quarter'] = pd.qcut(df['MEDIAN_INCOME'], 4, labels=['Q1','Q2','Q3','Q4'])
df['Total'] = df['EARNERS'] * df['MEDIAN_INCOME']

with pd.ExcelWriter('/root/demographic_analysis.xlsx') as w:
    df.to_excel(w, sheet_name='SourceData', index=False)
    df.groupby('STATE')['POPULATION_2023'].sum().to_excel(w, sheet_name='Population by State')
    df.groupby('STATE')['EARNERS'].sum().to_excel(w, sheet_name='Earners by State')
    df.groupby('STATE')['SA2_CODE'].count().to_excel(w, sheet_name='Regions by State')
    df.pivot_table('EARNERS', 'STATE', 'Quarter', aggfunc='sum').to_excel(w, sheet_name='State Income Quartile')
```

### Why the verifier rejects it
The verifier opens the file with `openpyxl.load_workbook(...)` and checks four orthogonal properties of `ws._pivots[0]`:

```python
# from /tests/test_outputs.py
def test_pivot_row_is_state(workbook, sheet_name, ...):
    pivot = workbook[sheet_name]._pivots[0]              # crashes here
    row_fields = [f.x for f in pivot.rowFields]
    assert STATE_FIELD_IDX in row_fields

def test_pivot_uses_correct_aggregation(workbook, sheet_name, expected_subtotal, ...):
    pivot = workbook[sheet_name]._pivots[0]
    assert pivot.dataFields[0].subtotal == expected_subtotal

def test_pivot_col_field(workbook, sheet_name='State Income Quartile', ...):
    pivot = workbook[sheet_name]._pivots[0]
    col_fields = [f.x for f in pivot.colFields]
    assert QUARTER_FIELD_IDX in col_fields

def test_pivot_cache_has_fields(workbook):
    pivot = workbook["Population by State"]._pivots[0]
    assert len(pivot.cache.cacheFields) > 0
```

Pandas-written cells have no `PivotTable` registered → `_pivots` is `[]` → `_pivots[0]` raises `IndexError` → all four tests crash. This is a robust, well-designed verifier that genuinely distinguishes "looks like a pivot summary" from "is a pivot table." The Gemini audit was right about this part.

---

## 4. Task quality questions (per the user's framing)

### 4a. Is everything inferrable from the environment, or is something hidden?

| Property checked | Stated in instruction? | Findable in env? |
|---|---|---|
| Use openpyxl PivotTable API (not pandas) | Implicitly via "four new pivot tables" + `required_skills=["xlsx"]` | Yes, **if** the agent can access the skill (claude-code, codex, gemini-cli). For terminus-2, only via `find /root -name SKILL.md` — none of the 6 terminus-2 runs tried this. |
| `cacheId=0` constraint | No | Only via the skill (or by reading openpyxl source) |
| Exclude `'Other Territories'` (test asserts `STATE ∈ VALID_STATES`) | No | Yes — income.xlsx contains zero `'Other Territories'` rows; an inner join handles it. |
| Use Q1 (or any single bucket) for NaN MEDIAN_INCOME | No | Yes — income.xlsx has `'np'` placeholders. Test rejects `'nan'` strings. |
| 90% SA2 codes preserved through join | No | Yes — implicitly, "merge data" requires preserving most rows. |
| Row count between 2000 and 3000 | No | Yes — implied by data sizes. |

**Verdict on inferrability for skill-equipped agents:** All requirements are inferrable. Some require careful data inspection (NaN handling, "Other Territories"), but a competent agent that audits its output before submitting would catch them.

**Verdict on inferrability for terminus-2:** The pivot XML requirement is *theoretically* findable (skills exist on disk under `/root/.*/skills/`) but **not signaled** in the instruction or system prompt. None of the 6 terminus-2 runs attempted to discover skills. Without the skill, openpyxl pivot API knowledge would have to come from training data — improbable but not literally impossible.

### 4b. Could a "super-capable being" solve this with the current task?

**Yes, even from terminus-2's position**, if the being:
1. Notices `required_skills` in `task.toml` (but `task.toml` may not be visible to the agent)
2. Discovers `find /root -name 'SKILL.md'` would surface 7 copies of the skill
3. OR knows openpyxl's pivot API from training data + spots the `cacheId=0` constraint via `python -c "import openpyxl.pivot.table; help(...)"` exploration
4. Audits its own output (e.g. `unzip -l demographic_analysis.xlsx` shows no `xl/pivotTables/*.xml`) before claiming complete

So the task is **theoretically self-contained**. But "what would a sufficient being do" is a high bar — the gap between that and observed terminus-2 behavior is large.

### 4c. The asymmetric provisioning argument

Here's the strongest reason to reject:

The task author **intended** skills to be available. Evidence:
1. `task_toml` declares `required_skills = ["xlsx", "pdf"]`
2. The Dockerfile contains `COPY skills /root/.X/skills` for **seven** named agent frameworks
3. The seven names cover essentially every agent framework the author could think of *except* terminus-2

But:
4. terminus-2 has **no skill-activation mechanism** in its system prompt or tool surface
5. The author also did not embed skill content in the instruction or any well-known path

So the **intent** ("provide skills to all agents") **fails to reach** terminus-2 due to a Dockerfile + instruction omission. This isn't terminus-2 being measured at "skill-discovery"; it's terminus-2 being measured at "guess that skill files exist somewhere we never told you about." That's not a fair test, even of agent capability.

A clean experimental design would be one of:
- (A) Provide skills to all agents (uniform resource provision) — tests skill-following and data handling
- (B) Provide skills to none, and don't declare `required_skills` — tests baseline knowledge of openpyxl
- (C) Provide skills only to skill-aware agents AND tell skill-blind agents to look at `/root/skills/` — tests resource discovery

The current design does (A) for 7 agents and... nothing coherent for terminus-2. It's an unintentional stratification.

---

## 5. Proposed fixes (per question 5)

### Fix A (recommended) — Embed skill content in instruction

Append the contents of `xlsx/SKILL.md` (and optionally `pdf/SKILL.md`) to the bottom of `task.instruction`, separated by a clear marker:

```
Save the final results in /root/demographic_analysis.xlsx.

---
The following reference documentation may be useful:

# XLSX Skill: Creating Pivot Tables
[full content of xlsx/SKILL.md including the cacheId=0 warning,
 worked example, and 2D pivot pattern]
```

**Why this fix:**
- Framework-agnostic: terminus-2, claude-code, codex, gemini-cli, factory, goose, opencode — all see the same instruction
- Doesn't change task difficulty for skill-aware agents (they'd already activate the skill and see the same content)
- Removes the "did you know to look in `/root/.X/skills/`" lottery
- Trivial to implement (string concatenation in task definition)

**Predicted post-fix outcomes** based on observed failure modes:
- All 3 claude-opus/terminus-2 runs (currently failing on pivots + state) → likely PASS, since the model is the same as in claude-code (3/3) and the skill content is what bridges the gap
- All 3 gpt-5.4/terminus-2 runs (currently failing on pivots only) → likely PASS, since codex run `8afeb161` proved this model can use the skill
- 3 gemini/terminus-2 runs → likely STILL FAIL on the SA2 truncation (model-specific PDF extraction issue) but the pivot test would pass
- 2 currently-failing codex runs → mostly unchanged — the skill is already accessible to them; the problem is they don't activate it. Embedding it in the instruction means they read it whether they want to or not, so they likely PASS.
- 1 codex near-pass (`8afeb161`) → unchanged unless we also do Fix C (NaN guidance)

**Post-fix expected pass rate:** roughly 12–14/18, up from 6/18 — converting agent-infrastructure noise into genuine capability signal.

### Fix B — Add `/root/SKILLS_REFERENCE.md` and reference it in the instruction

A weaker variant: instead of embedding the full skill, write skill content to `/root/SKILLS_REFERENCE.md` and add a single line to the instruction: `"See /root/SKILLS_REFERENCE.md for relevant openpyxl pivot table guidance."` This keeps the instruction shorter while still being framework-agnostic. Slightly worse than Fix A because it costs an extra `cat` step, but acceptable.

### Fix C (minor, optional) — Disambiguate NaN handling

Add to the instruction:
> Some `MEDIAN_INCOME` values may be missing in the source data; assign such rows to `Q1`.

This would convert the codex near-miss (`8afeb161`) from a failure to a success. Without this, the NaN handling is a fair (if subtle) capability test, so it's optional.

### Fix D (minor, optional) — Clarify join semantics

Add to the instruction:
> Include only SA2 regions present in both files (inner join).

This would prevent the `'Other Territories'` failures. Without it, "merge" arguably implies inner join, but stating it explicitly removes the edge case.

### What NOT to fix

- **Don't dumb down the verifier.** Checking `_pivots[0]` for actual `PivotTable` XML is the *good* part of this task — it forces real Excel pivot tables instead of pandas summaries. Removing this would convert a discriminating task into a trivial one.
- **Don't add a `terminus-2` path to the Dockerfile alone.** Terminus-2 has no `activate_skill()` call; merely copying files doesn't help unless the agent also knows where to look. Fix A (instruction embedding) is strictly better than Dockerfile-only changes.

---

## 6. Final verdict

### The single most valuable answer

> **Is agent failure due to the task itself or to agent capability bottleneck?**

**Mixed, with a clean decomposition:**

- **6/12 failures (all 6 terminus-2 runs):** *Task issue — asymmetric resource provisioning.* The task declares skills as required and the Dockerfile provisions them to seven agent frameworks but not terminus-2, while also failing to embed skill content in the instruction. This produces a confounded experiment where it's impossible to attribute terminus-2's failure to model capability versus framework gap versus missing documentation. The task intended for all agents to have skills; that intent doesn't reach terminus-2.
- **2/12 failures (codex `21afb32a`, `901dca22`):** *Agent capability bottleneck — failure to activate available skills.* Both runs had `/root/.codex/skills/` accessible but defaulted to pandas. This is a real, measurable agent deficiency: not following available technical documentation. The task design is sound for these runs.
- **1/12 failure (codex `8afeb161`):** *Agent capability bottleneck — minor data-handling oversight.* Used the skill correctly, built proper pivots, missed NaN handling on 1 column. 22/26 tests pass. A more careful agent (or one that auditied its own output) would have caught it.
- **The 3 gemini/terminus-2 runs additionally have a model-specific PDF extraction shortfall** (1925–1961 rows vs. 2000+) — this is an agent/model capability issue independent of the skill problem.

### Why REJECT (in current form) rather than ACCEPT-with-warning

The user's stated bar is strict task quality. The asymmetric provisioning isn't borderline — it eliminates 33% of runs from being meaningfully measured, and it can be fixed in 5 minutes by appending skill content to the instruction. A benchmark mix should not include tasks where a straightforward fix would dramatically reduce framework-specific noise.

### Why this is fixable rather than fundamentally broken

The task's *content* is excellent: realistic data engineering (multi-page PDF + Excel join + quartile binning), a well-supported but non-obvious technical requirement (Excel PivotTable XML), a robust verifier that distinguishes static data from real pivots, and natural data-quality edge cases (`'np'` placeholders, `'Other Territories'`). Among skill-equipped agents the discrimination is meaningful (codex 1/3 used skills and nearly passed; codex 2/3 had skills but ignored them). The Gemini audit's claim that "the verifier is robust [and] correctly distinguishes between a static representation of data and the dynamic pivot table requested" is correct — that part is genuinely well-designed.

### Concrete recommendation

- **Reject** in the current form
- **Re-accept** if Fix A (embed `xlsx` skill content in `task.instruction`) is applied
- Optionally include Fix C and Fix D for cleaner data-handling signal, but these are not blocking

Where the Gemini audit went wrong:
1. Attributed success to "Claude and Gemini models" when it actually correlates with **agent framework**
2. Did not notice the systematic terminus-2 exclusion
3. Did not audit which information is reachable from each agent's surface area

The task content itself is good. The packaging asymmetry is what makes it currently rejectable.

---

## Key files

| Path | Purpose |
|---|---|
| `task_inspection.md` | This analysis |

## Docent links

- **Collection:** https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d
- **Best failing run** (`8afeb161`, codex/gpt-5.4, 22/26 pass): https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/8afeb161-ace7-4484-a66a-bf7d034e367a
- **Representative successful run** (claude-code/claude-opus-4-6): https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/15f467ac-fb01-459c-b2d9-c93a05281075
- **Representative terminus-2 failure** (claude-opus-4-6): https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/e6eed2ea-bb34-43ea-8fcf-3dfa767d892d
