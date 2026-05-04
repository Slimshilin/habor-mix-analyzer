# Task Instruction (verbatim, as rendered to the agent)

```
Here is the question you need to address:

<question>
What is the p-value of ANOVA comparison across immune cell types, excluding PBMCs, for log2 fold change of miRNA expressions?
</question>


Perform data analysis in /workspace/notebook.py to analyze data files in /workspace/

Submit your final answer as a single string with your short answer in /workspace/answer.txt
IMPORTANT: Wrap your answer in XML tags <answer> </answer>
Example output:
```
echo "<answer>Your concise answer to the question</answer>" > /workspace/answer.txt
```
Remember, the final file should contain all necessary artifacts (plots, tables, print outputs) to solve the task provided.


General Guidelines:
- Write small to medium-sized chunks for easier debugging.
- Check dataframe shapes before printing. Use head() for large dataframes.

AVOID USING PLOTS/IMAGES. USE TABLES AND PRINT OUTPUTS INSTEAD AS MUCH AS POSSIBLE.
```

## Key facts

- **Variant:** This is the BixBench **CLI** variant (`instruction-cli.md`), where the agent gets a shell with python and writes `/workspace/answer.txt`. (The BixBench notebook variant uses Jupyter, but the harbor adapter uses CLI here.)
- **Source benchmark:** `bixbench` — a BixBench computational-biology QA benchmark from FutureHouse. Each task corresponds to a question over a public BioRxiv "capsule" (data + supplementary files). `bix-36-q4` = the 4th question of capsule #36.
- **Ground-truth (graded):** `"Between 0.55 and 0.59 inclusive"` — see `ground_truth.md`.
- **Workspace contents:** A capsule downloaded into `/workspace/` (data files for the BioRxiv paper). The Dockerfile uses `download_capsule.py --cli` against a BixBench HuggingFace asset to populate it. The exact data files are paper-specific (bix-36 corresponds to a specific paper's miRNA dataset over PBMC + isolated immune-cell subtypes).
