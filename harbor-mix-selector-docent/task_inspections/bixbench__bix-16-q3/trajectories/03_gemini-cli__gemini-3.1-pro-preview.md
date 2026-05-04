# gemini-cli + gemini-3.1-pro-preview — 3/3 PASS (THE ONLY GROUP TO PASS RELIABLY)

Run IDs: `5f5b9cab`, `d28a4f3d`, `7dd05195`. All PASSED reward=1.

## Per-trajectory analysis

### Run 1 — `5f5b9cab-a49b-4df8-afd1-4641db4f8b95`
- **Approach.** Loaded CRISPR + expression, intersected to **1103 cell lines x 17676 genes**, ran `df_effect.corrwith(df_expr, method='spearman')`. First call: `Genes with corr >= 0.6: 0`. Then immediately checked the other tail: `>= 0.6: 0`, `<= -0.6: 3` (`CCND1 -0.628825`, `FERMT2 -0.612306`, `KLF5 -0.602008`; max positive only 0.523 for CDKN1A).
- **DepMap convention citation:** EXPLICIT. The chain-of-thought says: *"DepMap Gene Effect scores are negative for essential genes... Essentiality is the inverse of the Gene Effect score. A more negative Gene Effect score means the gene is MORE essential."* Verified with a sanity test: `If inverted, >= 0.6: 3 / If raw, >= 0.6: 0`.
- **Final code.** `df_essentiality = -df_effect; corrs = df_essentiality.corrwith(df_expr, method='spearman'); (corrs >= 0.6).sum()` -> **3**. Hits: CCND1, FERMT2, KLF5.
- **Final answer:** `<answer>3</answer>`. Reward = 1.

### Run 2 — `d28a4f3d-8a57-4030-ae98-81e0e7b572e0`
- **Approach.** Same intersection. First wrote a custom Spearman via column-rank Pearson; got `>= 0.6: 0`. Switched to `expr_common.corrwith(crispr_common, axis=0, method='spearman')`. Got `>= 0.6: 0, <= -0.6: 3` (same three genes). Then explicitly tested two hypotheses side-by-side: `Hypothesis 1 (Essentiality = -Effect) >= 0.6: 3` and `Hypothesis 2 (Essentiality = abs(Effect)) >= 0.6: 3`.
- **DepMap convention citation:** EXPLICIT. *"I realized the DepMap data uses a negative effect to signify essentiality... I should expect the correlation between Expression and Gene Effect to be <= -0.6, NOT >= 0.6."*
- **Final answer:** `<answer>3</answer>`. Reward = 1.

### Run 3 — `7dd05195-5635-4ce1-8c40-edbc02ff5b5e`
- **Approach.** Same intersection (1103 x 17676). Direct Spearman: `>= 0.6: 0`, `<= -0.6: 3`. Also tried Pearson (`>= 0.6: 0`, `<= -0.6: 12`). Briefly explored `corrs.abs() >= 0.6` -> 3.
- **DepMap convention citation:** EXPLICIT, plus a META argument: *"the 0.6 threshold now seems intentionally set to capture exactly three genes... it's not a generic value... it's a targeted query; suggesting the answer is 3."* Part of the decision wasn't pure domain knowledge — it was inferring intent from the suspiciously tight threshold.
- **Final answer:** `<answer>3</answer>`. Reward = 1.

## Cross-trajectory pattern

All three runs followed the same template:
1. Compute raw Spearman of expression vs. CRISPRGeneEffect.
2. Get exactly 0 at `>= 0.6` and exactly 3 at `<= -0.6` (CCND1 -0.6288, FERMT2 -0.6123, KLF5 -0.6020 — these specific magnitudes only appear with the **1103-cell intersection**).
3. Deliberate over the sign flip.
4. Submit `<answer>3</answer>`.

**None of the three got 3 by computing `corr(expr, -effect) >= 0.6` first.** Every run tried the literal direction first, got 0, then either invoked DepMap convention (Runs 1 & 2) or a mixture of convention plus "the 0.6 threshold was clearly chosen to land 3 genes" meta-reasoning (Run 3) to flip.

The differentiator is **DepMap-convention domain knowledge**, not threshold-shopping. The number 3 is uniquely retrievable only from the negated/inverted direction.

**Could a literal/mathematical agent land on 3 without the convention?** Essentially no. A purely literal reading — Spearman of the two raw matrices, `>= 0.6` — returns 0, the mathematically defensible answer. The only convention-free routes to 3 are: (a) try `|corr| >= 0.6`, (b) try `<= -0.6`, or (c) infer from the suspicious-threshold pattern. Every passing path required injecting outside knowledge that is not in the instruction.
