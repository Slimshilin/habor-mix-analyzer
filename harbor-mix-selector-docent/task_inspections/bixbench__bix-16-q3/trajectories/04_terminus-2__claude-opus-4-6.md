# terminus-2 + claude-opus-4-6 — 0/3 PASS

Run IDs: `e22942e8`, `faf8ce28`, `f63e63fc`. All FAILED reward=0.

## Per-trajectory analysis

### Run 1 — `e22942e8-eaf0-4725-a9dc-387c572bdab3`
- **Approach.** Listed `/workspace/`, peeked at headers of `CRISPRGeneEffect.csv` and expression. Wrote `notebook.py`, ran once. Per-gene `spearmanr(c[mask], e[mask])` on raw values.
- **Numeric:** CRISPR `(1178, 17916)`, Expression `(1673, 19138)`, Common cell lines **1103**, Common genes 17676. Distribution: mean -0.013, std 0.071, min -0.628825, max 0.523398. Top: CDKN1A 0.523398, KIRREL1 0.401674, EPHA2 0.341020, USE1 0.327256. Reports `Genes >= 0.6: 0`.
- **Final answer:** `<answer>0</answer>`. Reasoning: *"The maximum correlation observed is 0.523398 (CDKN1A), which is below the 0.6 threshold."*
- **Sign-convention awareness:** None. Saw min -0.628 (one gene over the threshold on the wrong side) but didn't flag it.

### Run 2 — `faf8ce28-1564-4540-8d68-e9812040e66b`
- **Approach.** Identical pipeline. Code-level difference: `spearmanr(e[mask], c[mask])` (Spearman is symmetric so result identical).
- **Numeric:** Bit-identical to Run 1. Common cells 1103, common genes 17676, mean -0.013, min -0.628, max 0.523, top CDKN1A 0.523398.
- **Final answer:** `<answer>0</answer>`. Same reasoning.
- **Sign-convention awareness:** None.

### Run 3 — `f63e63fc-6710-46ed-b461-5a4f9a2586db`
- **Approach.** Same recipe. Added a progress print every 2000 genes.
- **Numeric:** Bit-identical numbers (1103/17676/min -0.628/max 0.523).
- **Final answer:** `<answer>0</answer>`.
- **Sign-convention awareness:** None.

## Cross-trajectory pattern

All three runs are essentially the same trajectory replayed three times: same explore-then-script pattern, same `pd.read_csv(..., index_col=0)` + intersection, same naive per-gene `spearmanr` on raw `CRISPRGeneEffect` against raw expression, same one-shot answer submission. They produce **bit-identical** intermediate numbers (1103 cells, 17676 genes, min -0.628825, max 0.523398, top gene CDKN1A 0.523398) and the same `<answer>0</answer>`.

**None inspect Model.csv, none read DepMap documentation, none verbalize the sign convention**, and none treat the visible left-tail (`min=-0.628`, beyond magnitude threshold) as a signal worth interrogating.

**Note:** The terminus-2 + claude-opus group used a 1103-cell intersection (same as gemini-cli successes). So if claude-opus had recognized the convention, it would have likely submitted 3 and passed. The harness was capable; the model lacks the DepMap prior.

**Compared to claude-code+claude-opus (different harness, same model):** terminus-2's "write one big script, run once" workflow is more brittle than claude-code's iterative pattern, but in this task the failure is at the model/domain-knowledge layer — both harnesses converge to `0`.
