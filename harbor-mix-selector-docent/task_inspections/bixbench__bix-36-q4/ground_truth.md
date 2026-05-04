# Ground truth

The verifier loads `/tests/ground_truth.json` (not visible to the agent), which has the form:

```json
{
  "question": "What is the p-value of ANOVA comparison across immune cell types, excluding PBMCs, for log2 fold change of miRNA expressions?",
  "ideal_answer": "Between 0.55 and 0.59 inclusive"
}
```

(Question pulled verbatim from the ATIF metadata; `ideal_answer` confirmed by every verifier `Eval query` block, all 18 of which contain the line `Correct answer: Between 0.55 and 0.59 inclusive`.)

## How the judge works

`/tests/llm_judge.py` calls `gpt-4o` with the BixBench `OPEN_ENDED_EVAL_PROMPT`:

```
Here is a question, the correct answer to the question, and a proposed answer.
Question: ...
Correct answer: Between 0.55 and 0.59 inclusive
Proposed answer: <agent answer>
You must respond with a binary score for whether the proposed answer is equivalent to the correct answer.

Nothing else is permitted.
```

So the judge is *lenient on prose / formatting*, but it will only return `True` if the proposed numeric value falls within `[0.55, 0.59]` (or is a paraphrase like "approximately 0.57"). Any number outside that band is `False`.

## Oracle solution
The packaged oracle simply writes `<answer>0.55</answer>` to `/workspace/answer.txt` (see `solve.sh.template`). It does **not** include the analysis pipeline that produced 0.55–0.59 — so the only evidence of *how* the ground truth was computed is the BixBench upstream Q&A specification (which we did not fetch).
