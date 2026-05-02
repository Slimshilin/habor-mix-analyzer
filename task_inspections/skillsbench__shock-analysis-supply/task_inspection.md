# Task Inspection: `skillsbench/shock-analysis-supply`

**Benchmark:** skillsbench  
**Task:** shock-analysis-supply  
**Checksum:** `8c3ecac360dd6d2bf70f21915668c0595a38654cd039f75d02eac123541502f8`  
**Overall score:** 0/18 runs pass (0%)  
**Gemini audit verdict:** Accept (DISPUTED)  
**Our verdict:** **REJECT** — `test_value_magnitudes` is fundamentally broken due to a unit calibration bug.  

---

## Task Description

Agents must build a multi-sheet Excel macroeconomic model estimating the impact of a $6.5B USD investment shock on Georgia's economy using a Cobb-Douglas production function. The task has three steps:

1. **Data collection:** Pull capital stock from PWT database, real GDP from IMF WEO (2000–2027), and Consumption of Fixed Capital from ECB. Populate a provided template (`test-supply.xlsx`) with formulas.
2. **HP Filter (Excel Solver):** Smooth the log TFP series (LnZ) using the Hodrick-Prescott filter, implemented as an Excel Solver optimization (minimize P5 objective by adjusting L6:L27).
3. **Production function:** Extend capital using average K/Y anchor, compute `Ystar_base` and `Ystar_with` (counterfactual with investment), compute uplift and projected GDP growth.

The task requires Playwright MCP for IMF WEO data collection and Excel formula engineering (no hardcoded values allowed, no Python).

---

## Test Suite (9 tests)

| # | Test | Checks |
|---|------|--------|
| 1 | `test_required_sheets_exist` | All 5 sheets present |
| 2 | `test_data_collection` | PWT columns B and C populated |
| 3 | `test_weo_data_extended_with_formulas` | WEO rows 36–51 contain formulas (2028–2043 projection) |
| 4 | `test_production_depreciation_rate` | B3 formula present and references CFC data |
| 5 | `test_hp_filter_setup` | LN formulas in LnK/LnY columns (≥10 cells), P5 has HP objective formula |
| 6 | `test_production_function_calculations` | TREND formula present for LnZ extension |
| 7 | `test_investment_and_capital_accumulation` | ΔK accumulation formulas in column J |
| 8 | `test_ky_ratio_and_k_extension` | K/Y formulas in column D, K extension via anchor in column E |
| 9 | `test_value_magnitudes` | Depreciation rate B3 in [1%, 3%] AND Ystar_base (H60:H65) in [10,000, 500,000] |

---

## Results Summary

### Performance by Agent × Model (out of 9 tests)

| Agent Framework | Model | Scores | Avg |
|---|---|---|---|
| claude-code | claude-opus-4-6 | 8, 8, 8 | **8.0/9** |
| codex | gpt-5.4 | 8, 7, 7 | 7.3/9 |
| gemini-cli | gemini-3.1-pro-preview | 8, 8, 4 | 6.7/9 |
| terminus-2 | gemini/gemini-3.1-pro-preview | 7, 7, 6 | 6.7/9 |
| terminus-2 | openai/gpt-5.4 | 7, 6, 1 | 4.7/9 |
| terminus-2 | anthropic/claude-opus-4-6 | 3, 1, 1 | **1.7/9** |

### Failure Frequency

| Test | Failures (/ 18 runs) |
|---|---|
| `test_value_magnitudes` | **18 / 18 (100%)** |
| `test_hp_filter_setup` | 10 / 18 |
| `test_data_collection` | 7 / 18 |
| `test_investment_and_capital_accumulation` | 6 / 18 |
| `test_production_function_calculations` | 5 / 18 |
| `test_ky_ratio_and_k_extension` | 5 / 18 |
| `test_weo_data_extended_with_formulas` | 3 / 18 |
| `test_production_depreciation_rate` | 3 / 18 |
| `test_required_sheets_exist` | 0 / 18 |

---

## Critical Finding: `test_value_magnitudes` Fails in ALL 18 Runs

### What the test checks

```python
def test_value_magnitudes():
    # Depreciation rate (B3) should be between 0.01 and 0.03 (1-3%)
    b3_value = prod["B3"].value
    assert b3_value is not None, "Depreciation rate B3 should have a value"
    assert 0.01 < b3_value < 0.03, f"Depreciation rate should be 1-3%, got {b3_value:.4f}"

    # Ystar_base values (column H, rows 60-65) should be in thousands (50,000-150,000 range)
    # These represent potential GDP in millions of Georgian Lari
    for val in ystar_values:
        assert 10000 < val < 500000, f"Ystar_base should be in thousands (10k-500k), got {val:.2f}"
```

### What the 6 best runs produce

Every run using claude-code (claude-opus), or gemini-cli (gemini), or codex (gpt-5.4) with correct Excel formula execution produces:

```
Ystar_base (H60, year 2026) = 78.98
AssertionError: Ystar_base should be in thousands (10k-500k), got 78.98
assert 10000 < 78.980081724501
```

The computed value (~79) reflects **billions of Georgian Lari** for Georgia's potential GDP in 2026. The test expects values in **millions of Georgian Lari** (10,000–500,000 range, i.e., ~79,000).

### Root cause: the template file itself says "Scale: Billions"

The template `test-supply.xlsx` that agents are provided already contains WEO metadata rows:

```
Row 5: Units  → "National currency"
Row 6: Scale  → "Billions"
```

This is confirmed by the terminus-2 agent's exploration of the template file early in its trajectory (message B4 in run `518addd2`):

```python
[('B5', 'Units'), ('C5', 'National currency'), ...
[('B6', 'Scale'), ('C6', 'Billions'), ...
```

The IMF WEO database reports Georgia's real GDP at constant prices in **billions of Georgian Lari** (approximately 40–90 billion GEL for years 2000–2026). The template itself reflects this with "Scale: Billions".

When agents correctly use this data at billion-GEL scale and run the Cobb-Douglas production function:
- K from PWT (millions of 2017 USD, ~100,000–600,000 range)
- Y from WEO (billions of GEL, ~40–90 range)
- LnZ = LnY − α × LnK ≈ ln(80) − 0.35 × ln(500,000) ≈ −0.21
- Ystar_base = exp(LnZ_trend + α × LnK) ≈ 79 **billion GEL** → passes through in same unit

The test expects **million GEL** (i.e., Ystar_base ≈ 79,000), but the data source and template both state billion GEL (Ystar_base ≈ 79).

**Conclusion:** The test `test_value_magnitudes` is calibrated for a GDP unit (million GEL) that is inconsistent with both (a) the WEO database's actual reporting unit and (b) the template file's own metadata. No agent reading the template correctly can pass this test.

---

## Analysis of Other Failure Patterns

### `test_hp_filter_setup` — 10/18 fail

**What it checks:**
```python
assert lnk_formula_count >= 10, "Production sheet should have LN formulas for LnK"
assert lny_formula_count >= 10, "Production sheet should have LN formulas for LnY"
assert p5_formula is not None, "Cell P5 should contain HP filter objective formula"
```

**Pattern:** All 10 failures fail on the same assertion: `Cell P5 should contain HP filter objective formula` is None.

The HP filter requires Excel Solver to minimize a sum-of-squares objective placed in cell P5. Agents implementing this via Python (openpyxl) must explicitly create the formula-holding cell P5. The 6 best-performing runs (claude-code/claude-opus and some gemini/gemini-cli runs) correctly write an Excel `=SUMPRODUCT(...)` formula into P5. The failing runs either:
- Compute the objective value in Python and hard-code it into P5 (not a formula)
- Implement the HP filter optimization entirely in Python without writing formulas to Excel
- Leave P5 empty

**Surface reason:** P5 is not populated with an Excel formula.  
**Root cause:** Agents that don't use a proper Excel formula approach (writing formulas to cells) and instead use Python to compute the solved values, don't understand that the test verifies the *formula presence* not just the *value*. The instruction says "ONLY use excel for this task (no python, no hardcoded numbers for the cells that needs calculation)," which agents sometimes interpret as "use openpyxl to write Excel formulas" but fail to place the objective formula in P5. This is a genuine agent capability bottleneck.

**Is this a task problem?** Partly. The instruction says "calculate the objective in P5" which is explicit enough. An agent with sufficient Excel formula engineering capability can pass this. However, the Solver workflow (running the actual Solver) is impossible in a headless environment — all passing agents simulate the Solver by computing the optimal LnZ_HP values in Python and then writing them to Excel along with the objective formula. This is a legitimate but nontrivial implementation challenge.

### `test_data_collection` — 7/18 fail

**What it checks:**
```python
has_data_b = any(pwt.cell(row=row, column=2).value is not None for row in range(2, 30))
has_data_c = any(pwt.cell(row=row, column=3).value is not None for row in range(2, 30))
assert has_data_b, "PWT sheet Column B should have capital stock data"
assert has_data_c, "PWT sheet Column C should have employment/labor data"
```

**Pattern:** Failures fail on `has_data_c` — agents fill column B (capital stock, rnna) but not column C. The template provides only a "rnna" header in column B with no column C header at all. The instruction says "fill the relevant data in column B and C in sheet PWT" with a HINT to read the metadata.

The passing agents (e.g., claude-code) put `rgdpna` (real GDP at constant national prices) in column C. The test just checks that column C has *any* data, not specifically that it's a particular variable. Agents that only pull one PWT variable fail.

**Is this a task problem?** Partially. The instruction is ambiguous about what column C should contain (the template has no column C header). Agents that correctly infer "two relevant variables are needed" (K and perhaps GDP or labor) pass, while those that only grab K fail. A clearer instruction or pre-labeled column C header would help.

### Depreciation Rate Failure (within `test_value_magnitudes`)

Some terminus-2 runs fail at the depreciation rate check:
- `148f6cb4` (terminus-2/gpt-5.4): B3 = 4.22% — fails `0.01 < 0.0422 < 0.03`
- Several runs: B3 is None

The instruction mixes data sources with different currencies:
- ECB CFC data: in Georgian Lari (national currency)
- PWT capital stock (rnna): in millions of 2017 USD

Agents must handle the GEL-to-USD conversion when computing depreciation = CFC / Capital. The claude-code runs compute a ~1.52% rate that passes, while some terminus-2 runs use a naive division that yields 4.22%. This is a unit mismatch in the task's data combination that the instruction doesn't explicitly address.

---

## Agent Behavior Analysis

### The gemini-cli outlier: e7027d4c (4/9 vs 8/9 for same framework)

Two gemini-cli/gemini runs score 8/9 (`061ac2d3`, `0ddc6f1b`) while a third (`e7027d4c`) scores only 4/9. Inspecting the final messages of `e7027d4c` reveals the agent at message 149 checks column K for HP filter results — `wb['Production']['K6'].value` returns `None`. Column K contains LnZ (the *raw* TFP series), not column L which should contain LnZ_HP (the *smoothed* HP-filtered series). The agent confused the adjacent K/L columns during the HP filter implementation, leaving the optimization in the wrong cells. This cascaded: LnZ_HP was absent, so the production function lower table (columns G–P, rows 36–75) remained unpopulated, causing Ystar_base (H60:H65) to return 0 values.

The test accordingly reports: `AssertionError: Should have Ystar_base values, found 0` — not the unit-mismatch failure seen in the other runs, but complete absence of values.

**This is a pure agent execution error** — stochastic column-mapping confusion within the same framework/model that succeeds in other runs. The same gemini-cli framework correctly places everything in two other trials. This variance is a known property of stochastic LLM agents on complex multi-cell Excel tasks.

---

### Why claude-code/claude-opus (8/9) outperforms terminus-2/claude-opus (1.7/9)

The agent framework matters enormously here. claude-code has:
1. **Playwright MCP**: Enables direct browser automation for IMF WEO data
2. **Rich tool ecosystem**: Can write Python scripts and Excel manipulation simultaneously
3. **Better formula engineering**: Correctly writes Excel formulas (LN(), TREND(), SUMPRODUCT() for HP objective) to cells

terminus-2 is a shell-keystroke-based agent that:
1. Lacks Playwright MCP (confirmed by 518addd2 struggling to even download PWT data — no wget, no curl in the container)
2. Has a fundamentally different execution model (JSON keystrokes to terminal)
3. Falls back to Python-only HP filter computation, missing the P5 formula requirement

The 3 terminus-2/anthropic/claude-opus runs score 1/9, 1/9, 3/9 — barely functioning. They fail because the underlying terminal agent cannot efficiently:
- Download data from external URLs (no curl/wget)
- Execute Excel Playwright-style web scraping
- Properly populate Excel formulas programmatically

The **same model** (Claude Opus 4.6) achieves 8/9 consistently in the claude-code framework and ~1.7/9 in terminus-2. This 4.7× performance gap is entirely due to the agent framework, not model capability.

### Convergent failure on `test_value_magnitudes`

All 18 runs converge on the same unit issue regardless of how well they do on other tests. The 6 "best" runs (claude-code and some native framework runs) all produce:
- Ystar_base ≈ 78–80 for years 2026–2031
- Same ~79 billion GEL computation
- Same failure: 79 < 10,000

This uniformity across 3 different base models and 3 agent frameworks is the strongest evidence that the test is broken, not the agents. If the unit error were a capability gap, we'd expect variance across models. Instead, every agent that correctly follows the instruction and reads the WEO data at the scale stated in the template produces the same "wrong" result.

---

## Answering the Key Questions

### 1. How close are agents to successfully completing the task?

The best runs (claude-code/claude-opus) reach 8/9, failing only `test_value_magnitudes`. If that test were fixed, these runs would achieve 9/9. The task's other 8 tests are genuinely solvable by a capable agent with the right framework.

For weaker frameworks (terminus-2/claude), agents barely complete data collection, scoring 1/9 — a fundamentally different failure mode caused by agent infrastructure.

### 2. Do agents show similar approaches and fail at the same place?

Yes, with high consistency across the best-performing runs:
- All 6 best runs collect PWT (rnna) and IMF WEO data correctly
- All implement HP filter by computing optimal LnZ values in Python and writing to Excel
- All compute Ystar_base via the same production function formula
- **All produce Ystar_base ≈ 79 billion GEL and fail the unit magnitude test**

**Surface reason:** "Ystar_base value 78.98 is outside the expected range [10,000, 500,000]."  
**Root cause:** The test is calibrated for million-GEL units while the WEO data source (and the template's own metadata) reports in billion-GEL units. This is not an agent error — agents read the data exactly as the template specifies.

For `test_hp_filter_setup` failures:
- **Surface reason:** "P5 does not contain an HP filter objective formula"
- **Root cause:** Agents implement HP filter optimization in Python but don't write the objective formula back to cell P5. They understand the mathematical objective but miss the requirement to encode it as an Excel formula. This is a genuine agent bottleneck in understanding the "formulas only" constraint.

### 3. Concrete agent behaviors that failed the tests

**`test_value_magnitudes` (100% failure):**

What the test expects (from test code):
```python
assert 10000 < val < 500000, f"Ystar_base should be in thousands (10k-500k), got {val:.2f}"
```

What agents produce (all 6 best runs):
```
Ystar_base (H60, 2026) = 78.98
AssertionError: Ystar_base should be in thousands (10k-500k), got 78.98
assert 10000 < 78.980081724501
```

The template explicitly states `Scale: Billions` for WEO GDP. Agents use GDP ≈ 75 billion GEL (2026), capital K ≈ 550,000 (million USD from PWT), compute LnZ ≈ −0.21, and the resulting Ystar_base ≈ 79 is in the same billion-GEL unit as Y. The test expects ~79,000 (million GEL).

**`test_hp_filter_setup` (10/18 failure):**

What the test expects:
```python
p5_formula = get_formula_text(prod["P5"].value)
assert p5_formula is not None, "Cell P5 should contain HP filter objective formula"
```

What failing agents produce: P5 is empty or contains a plain numeric value (computed by Python), not an Excel formula like `=SUMSQ(L6:L27-K6:K27)+100*SUMPRODUCT(...)`.

Passing agents (claude-code) write the full Excel formula to P5 in the openpyxl formula string, e.g.: `=SUMSQ(L6:L27-K6:K27)+...`

**`test_data_collection` (7/18 failure):**

What the test expects: PWT sheet column C has any data.

What failing agents produce: Only column B (rnna) filled, column C left empty. The template has no column C header, making it easy to miss.

### 4. Task self-containment and inferability

**Can agents infer what's being tested?**

For `test_value_magnitudes`:
- The instruction says to use WEO data (billions of GEL as stated in the template)
- There is **no instruction** to express results in millions of GEL
- The template's own "Scale: Billions" metadata contradicts the test's expected range
- **An agent cannot infer** that it should use million-GEL units — it will naturally use whatever units the data source provides (billions)
- This makes `test_value_magnitudes` **not theoretically achievable** from the given instructions and environment

**Can a super-capable agent solve this task?**
- Yes, for 8/9 tests — given Playwright MCP, Excel formula engineering skills, and HP filter implementation
- No, for `test_value_magnitudes` — the data source and template explicitly state "Billions", and no instruction says to convert to millions. Even a perfect agent cannot pass a test that conflicts with the data provided

### 5. Proposed fixes

**Fix A (Recommended): Correct `test_value_magnitudes` to match billion-GEL scale**

Change the expected range from [10,000, 500,000] (millions) to [50, 250] (billions):
```python
# Ystar_base values in billion GEL (matching WEO "Scale: Billions" metadata)
assert 50 < val < 250, f"Ystar_base should be in billions (50-250 billion GEL), got {val:.2f}"
```

This fix is consistent with the template, the WEO data source, and the computed values from all correctly-implemented solutions.

**Fix B: Change the template and instruction to specify million-GEL units**

Add to the instruction: "Note: WEO GDP data should be in millions of Georgian Lari (divide billion-GEL values by 1000 where needed)." Also update the template's Scale row to "Millions."

This fix would require agents to perform an additional unit conversion step, but would be self-consistent. The PWT capital stock (in millions of 2017 USD) would then require a currency conversion (USD to GEL, then scale alignment) — adding another layer of complexity without clear educational value.

**Fix C: Remove `test_value_magnitudes` entirely**

The other 8 tests adequately check the formula structure, data collection, HP filter setup, and production function calculations. The magnitude test adds little diagnostic value if it's calibrated incorrectly.

**Assessment:**

Fix A is the correct approach. The task's logical and economic structure is sound; the unit calibration in the test is the only bug. With Fix A, the 6 best-performing runs (which currently score 8/9) would all score 9/9, making this a legitimate 0/18 → 6/18 success-rate scenario where failure is attributable to agent capability (not task bugs).

---

## Final Verdict

**Decision: REJECT**

**Reason:** `test_value_magnitudes` is a broken test that makes the task impossible to pass for any agent that correctly reads the provided template's own unit metadata ("Scale: Billions"). The test was calibrated for million-GEL GDP units while the actual data source and template specify billion-GEL. This is not an agent capability bottleneck — it is a task design bug confirmed by:

1. **100% failure rate** on `test_value_magnitudes` across all 18 runs
2. **Uniform failure value** (Ystar_base ≈ 79 across 3 different models × 3 agent frameworks)
3. **Template contradiction**: the provided `test-supply.xlsx` has `Scale: Billions` in the WEO metadata
4. **Theoretical impossibility**: no instruction says to convert units from billions to millions

The Gemini audit's acceptance is incorrect. While it correctly observes that agents reach 8/9 tests, it misattributes the final failing test to "execution errors in complex multi-step financial logic" rather than recognizing it as a test calibration bug. The task has a clear path to being a high-quality "hard" benchmark item with Fix A (correcting the expected range to billion-GEL scale), but in its current form it cannot produce any successful completions.

**Secondary finding:** The large performance gap between terminus-2/anthropic (1.7/9 avg) and claude-code/claude-opus (8/9 avg) for the same underlying model demonstrates that this task heavily favors agents with Playwright MCP capabilities and rich tool ecosystems. The terminus-2 framework's lack of curl/wget in the environment and absence of Playwright makes even basic data collection difficult, before even reaching the modeling steps.

---

*Analyzed: 2026-05-01 | Collection: 640e920a-aef3-4b7c-9487-69899ef19e9d | Runs: 18*
