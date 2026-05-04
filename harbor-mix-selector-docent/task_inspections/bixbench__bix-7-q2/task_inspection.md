# Task Inspection — `bixbench / bix-7-q2`

| Field | Value |
| --- | --- |
| Task ID | `bix-7-q2` |
| Source | BixBench (HuggingFace `futurehouse/BixBench`, capsule `a02b761a-02b6-46b5-9d5e-2964d5a74960`, paper https://doi.org/10.3324/haematol.2024.285239 — Bloom Syndrome / CHIP) |
| Question | "What is the average number of CHIP variants per sample after filtering out intronic, intergenic, and UTR variants?" |
| Eval mode | `range_verifier` → ground-truth string presented to GPT-4o judge: **"Between 40 and 60 inclusive"** |
| Distractors (raw, multiple-choice version) | (25,35), (120,150), (230,260) |
| Oracle `solve.sh` | `echo '<answer>40</answer>' > /workspace/answer.txt` |
| Verifier | LLM-as-judge (`gpt-4o`) via `tests/llm_judge.py` — binary equivalence to "Between 40 and 60 inclusive" |
| Pass rate observed | **2 / 18 (11 %)** |
| Docent collection | `640e920a-aef3-4b7c-9487-69899ef19e9d` |
| Audit submitted by | Lin Shi — recommended **reject** |
| My final verdict (this audit) | **ACCEPT (borderline)** — see §7 and §11. Initial REJECT was reversed after applying the domain-knowledge lens. The task tests legitimate genomics-aware capability that the failing agents lack. |

---

## 1. Key files (mirrored in this directory)

| File | What it is |
| --- | --- |
| `instruction.md` | Verbatim prompt the agent sees in `/workspace`. CLI variant of the BixBench template — only "intronic, intergenic, and UTR" are listed as filters. |
| `task.toml` | Standard BixBench spec — 1 h agent budget, 600 s verifier budget, 8 GB / 2 cpus, gpt-4o judge. |
| `Dockerfile` | `futurehouse/bixbench:aviary-notebook-env`; pulls capsule by data_folder.txt at build time. |
| `data_folder.txt` | `CapsuleFolder-a02b761a-02b6-46b5-9d5e-2964d5a74960.zip` (HuggingFace) |
| `ground_truth.json` | What the judge sees — has only `question` and `ideal_answer = "Between 40 and 60 inclusive"`. The judge does NOT see any rubric, dataset notes, or "must filter Reference" hint. |
| `llm_judge.py` | Calls `gpt-4o` with the BixBench template `OPEN_ENDED_EVAL_PROMPT` (question + correct + proposed → True/False). |
| `test.sh` | Just `pip install openai==2.14.0 && python /tests/llm_judge.py`. |
| `solve.sh` | The harbor-bixbench adapter generates this from the lower bound of the range tuple → `<answer>40</answer>`. |

The dataset that lands at `/workspace` (downloaded inside the container) is a folder
`CHIP_DP10_GQ20_PASS/` with **86 per-sample Excel workbooks** (one per sample-trio member),
two reference workbooks (`230214_Schenz_et_al_2022_CHIP_Genes.xlsx`,
`230215_Trio_Status.xlsx`), and metadata. Each per-sample workbook is a 2-row-header
spreadsheet with 33 columns. **All transcripts confirm the salient columns:**

- `Chr:Pos`, `Ref/Alt`, `Primary Findings`, `Incidental Findings`, **`Zygosity`** (col 4),
  ..., `Read Depths (DP)`, `Genotype Qualities (GQ)`, `Variant Allele Freq`,
  ..., **`Sequence Ontology (Combined)`** (col 13), **`Effect (Combined)`**,
  ..., **`In_CHIP`** (col 29).
- Every row in every file is `In_CHIP == True` and `Filter == PASS`.
- **`Zygosity` distribution is roughly:** Reference ≈ 504, Heterozygous ≈ 89, Homozygous Variant ≈ 49, NaN ≈ 2 (per typical sample, from codex run 1 B11 verbatim). Across 86 files: Reference ≈ 75 % of all rows.
- **`Sequence Ontology (Combined)` cohort distribution (from gemini-cli run 1 B64):** `intron_variant 26877, synonymous_variant 13835, missense_variant 8765, 3_prime_UTR_variant 3428, splice_region_variant 2664, 5_prime_UTR_variant 987, inframe_insertion 300, frameshift_variant 172, inframe_deletion 86, 5_prime_UTR_premature_start_codon_gain_variant 85, upstream_gene_variant 59`. **No literal `intergenic_variant` exists in the dataset.**

These observations are consistent across all 18 trajectories; they are facts of the data, not artifacts of any one agent's exploration.

---

## 2. The verifier and what "passing" means

The judge prompt is the BixBench `OPEN_ENDED_EVAL_PROMPT`:

```
Question: <question text>
Correct answer: Between 40 and 60 inclusive
Proposed answer: <agent's submitted text>
You must respond with a binary score for whether the proposed answer is equivalent to the correct answer.
```

So passing = GPT-4o judges the agent's number as "equivalent" to "Between 40 and 60 inclusive".
Empirically: agents that submit ~52 pass; agents that submit ~300 fail. There is no other
hidden test. There is no fuzz/tolerance beyond what GPT-4o's range reasoning provides.

---

## 3. The 18 runs at a glance

Six (agent, model) cells × 3 trials = 18 runs. Pulled from Docent metadata:

| Agent | Model | n | Reward |
| --- | --- | --- | --- |
| codex | gpt-5.4 | 3 | **2 success (52.91, 52.33)** + 1 fail (300.94) |
| claude-code | claude-opus-4-6 | 3 | 0 / 3 fail (300.94, 301.93, 300.94) |
| terminus-2 | claude-opus-4-6 | 3 | 0 / 3 fail (300.94, 300.94, 300.94) |
| terminus-2 | gpt-5.4 | 3 | 0 / 3 fail (300.94, 300.94, RewardFileNotFoundError) |
| gemini-cli | gemini-3.1-pro-preview | 3 | 0 / 3 fail (300.94, 300.26, 300.26) |
| terminus-2 | gemini-3.1-pro-preview | 3 | 0 / 3 fail (300.26, 300.26, 300.26) |

**Final-answer histogram: 300.94 (×9), 300.26 (×5), 301.93 (×1), 52.91 (×1), 52.33 (×1), no-submit (×1).**

The 300 cluster is not coincidence — it is the deterministic result of any agent that:
(a) keeps every row from the per-sample sheets, and
(b) drops only rows whose `Sequence Ontology (Combined)` matches `intron|UTR` (with
optional addition of `upstream_gene_variant` → 300.26 vs 300.94).

The 52 cluster is the deterministic result of additionally dropping `Zygosity == Reference`
(and treating NaN-zygosity rows the same way).

---

## 4. How close are the agents to passing?

| | Required step | Did the agent take it? |
| --- | --- | --- |
| Read 86 per-sample Excel files | Yes — all 18 |
| Identify the two-row header | Yes — all 18 |
| Identify the variant-annotation column | Yes — all 18 (`Sequence Ontology (Combined)`) |
| Drop intron / UTR ontologies | Yes — all 18 |
| Drop "intergenic" → recognized that the dataset uses `upstream_gene_variant` | 6 / 18 (and immaterial: changes 300.94 → 300.26) |
| **Drop `Zygosity == "Reference"` rows** | **2 / 18** |
| Submit a number in [40, 60] | 2 / 18 |

So the **single load-bearing step** the agents miss is the Reference-zygosity filter.
Every other step they execute correctly. The "intergenic" wording mismatch the audit
flagged is real but ~irrelevant to the verdict (only ≤1 unit difference).

The two passing runs (codex/gpt-5.4) are not lucky:

- `61ff3ccf` (success, 52.91) explicitly printed `Zygosity` value_counts on the first sample (B11) and saw `Reference 504 / Heterozygous 89 / Homozygous Variant 49 / NaN 2`. It then used `keep = df['Zygosity'].isin(['Heterozygous','Homozygous Variant'])` — i.e. an explicit whitelist. The reasoning chain (B17–B41) shows it deliberately treated Reference rows as non-variants.
- `658ddb1e` (success, 52.33) did the same `Zygosity` value_counts and stated verbatim: *"the right denominator is non-reference variant rows per sample after dropping any ontology containing intron/intergenic/UTR terms."* (B17). It used `df['Zygosity'].notna() & df['Zygosity'] != 'Reference'`.

The codex failure run (`9b9dc5c0`) skipped the Zygosity inspection entirely and submitted 300.94 — collapsing into the same failure mode as the other 14 fails.

---

## 5. Agent behaviors that failed the test

**Surface failure (every failure run):** the judge sees `Proposed answer: 300.94` (or 300.26) versus `Correct answer: Between 40 and 60 inclusive` and returns `False`. Verbatim from terminus-2/claude-opus-4-6 run `799ec7da` test_stdout:

```
Raw answer: <answer>300.94</answer>
…
Eval response: False
Reward: 0.0
```

**Concrete code that produced 300.94** (terminus-2/claude-opus-4-6 `799ec7da`):

```python
exclude_types = []
for v in all_so_values:
    v_lower = v.lower()
    if 'intron' in v_lower or 'intergenic' in v_lower or 'utr' in v_lower:
        exclude_types.append(v)
mask = ~df['Sequence Ontology (Combined)'].isin(exclude_types)   # NO Zygosity filter
```

**Concrete code that produced 52.91** (codex/gpt-5.4 `61ff3ccf`):

```python
EXCLUDED_TERMS = ["intron_variant", "intergenic_variant", "UTR_variant"]
PRESENT_ZYGOSITY = {"Heterozygous", "Homozygous Variant"}      # the load-bearing line
present_mask = df["Zygosity"].isin(PRESENT_ZYGOSITY)
excluded_mask = df["Sequence Ontology (Combined)"].astype(str).str.contains(
    "intron_variant|intergenic_variant|UTR_variant", case=False, na=False)
kept_mask = present_mask & ~excluded_mask
```

The single line `present_mask = df["Zygosity"].isin(PRESENT_ZYGOSITY)` is what
distinguishes pass from fail.

**The 1 RewardFileNotFoundError** (terminus-2/gpt-5.4 `f6b8c381`): the agent
issued `python /workspace/notebook.py > /workspace/run.log 2>&1` as its final command
but the terminal capture returned no completion prompt; the agent then double-called
`mark_task_complete()` (B19, B21) without verifying with `cat /workspace/answer.txt`
that anything was written. The script almost certainly didn't finish parsing 86 Excel
files in time. This is an agent-level reliability bug (fail-without-verify), not a
task issue — even had it written the file, it would have submitted ~300.94 like all
other terminus-2/gpt-5.4 runs and failed anyway.

---

## 6. Surface vs. root cause across all 18 runs

### Surface

- 14 / 18 → submitted ~300 (300.94 or 300.26 or 301.93)
- 1 / 18 → never submitted (terminal-capture confusion + no verification)
- 2 / 18 → submitted ~52 (PASS)

### Root cause (per-failure attribution)

**One single root cause dominates: the agent treated the per-sample workbooks as already
being a "list of called variants" and counted rows after annotation-only filtering, when
in fact the workbooks contain per-locus genotype output that includes a large majority of
reference-genotype calls.** Concretely:

- The agents trusted three signals that confirmed (incorrectly) that no further filtering
  was needed:
  1. The folder name `CHIP_DP10_GQ20_PASS` — implies "already filtered for CHIP, DP≥10,
     GQ≥20, PASS quality".
  2. `In_CHIP == True` for every row in every file (verified empirically by 8+ agents).
  3. `Filter == PASS` for every row (verified by ≥3 agents).
- Yet the `Zygosity` column was in the column list every single agent saw, and the literal
  string `Reference` was visible in the `head()` preview for ~12 / 18 runs (definitely for
  all claude-code, all terminus-2/claude-opus, all terminus-2/gemini, and one gemini-cli
  duplicate dump). **None of the 16 failing agents ran `df['Zygosity'].value_counts()`**
  or any equivalent inspection.
- This is the inflection point: if `Zygosity == "Reference"` had been treated as a
  meaningful column to inspect, the agent would have seen the ~75 % Reference share
  immediately and almost certainly chosen to drop it (codex/gpt-5.4 did this twice with
  no domain-specific prompting).

**Surface vs root, classified per the user's framework:**

- *Surface reason:* "the agent forgot to filter on Zygosity"
- *Root cause:* The agents performed insufficient column-level descriptive statistics.
  After identifying the file format and the headline annotation columns, they jumped to
  filter-and-aggregate. None of the 16 failing agents inventoried *all* enum-like columns
  (`Zygosity`, `In_CHIP`, `Filter`, `Effect (Combined)`, `Classification`) with
  `value_counts`. They picked the column whose name most obviously matches the
  instruction text ("Sequence Ontology" ≈ "intronic/intergenic/UTR") and stopped exploring.
- A secondary contributing factor is the **failure to do a sanity check**: not one of
  the 16 failing agents asked "does ~300 CHIP variants per sample fit the biology?"
  CHIP (clonal haematopoiesis of indeterminate potential) is by definition rare somatic
  clonal expansion — typical clinical reports list dozens, not hundreds, of CHIP variants
  per sample. The codex success runs implicitly used this prior, and even tested
  alternative filterings to defensively bracket the answer.
- For the 1 no-submission run, root cause is **weak self-verification** (no
  `cat /workspace/answer.txt` after the heavy notebook execution); orthogonal to the
  task content.

---

## 7. Is this a task problem or a capability problem? — the central question

This requires answering the user's two diagnostic sub-questions:

### 7a. "Is this something the agent can possibly infer from the environment, or will they never know?"

The agent CAN, in principle, infer the Reference-zygosity filter from the environment.
The required chain of inference is:
1. Notice the `Zygosity` column.
2. Run value_counts on it.
3. Recognize that "Reference" zygosity = no variant call at this locus → these rows
   are genotype output, not variant calls.
4. Decide that "CHIP variants" cannot include reference-genotype rows.

Empirically: codex/gpt-5.4 made this inference twice unprompted. So the inference is
*possible* from the environment alone — the data are self-explanatory for an agent that
inspects them with sufficient breadth.

But it is also *not implied* by the prompt. The prompt explicitly enumerates exactly
three filters ("intronic, intergenic, and UTR variants"). Reading the prompt literally,
the implicit pre-condition is that everything in the workbook IS a CHIP variant
(consistent with the folder name `CHIP_DP10_GQ20_PASS` and `In_CHIP == True`
everywhere). A "follow-the-prompt" agent has every reason to stop after applying the
three named filters.

### 7b. "Can a super-capable being resolve this task given the current instructions and environment?"

Yes — as demonstrated by codex/gpt-5.4 succeeding twice. The required capability is
**defensive descriptive statistics on every column that looks enum-like, plus
biological-plausibility sanity-checking**, not domain-specific prior knowledge.

So the task is theoretically self-contained. But the gap between what the prompt
*explicitly demands* and what the verifier *implicitly demands* is large enough that
even very capable models (Claude Opus 4.6, Gemini 3.1 Pro) consistently fall into the
trap. **2 / 18 is a 89 % failure rate that is concentrated in the prompt's silence about
Reference rows, not in any computational difficulty.**

### 7c. Initial verdict (later revised — see §11)

My first pass concluded REJECT on the grounds that the prompt's closed enumeration
("intronic, intergenic, and UTR") creates a misleading prompt-following prior. I
revised that verdict after applying the domain-knowledge lens — see §11 below.

---

## 8. How to FIX the task (not simplify it)

The audit asks for non-simplifying fixes. Two routes — both raise task quality without
removing the analytical challenge:

### Fix A (preferred) — make the implicit step explicit in the instruction

Change the prompt's filter list from a closed enumeration to an open description:

> "What is the average number of **non-reference** CHIP variants per sample after
> filtering out intronic, intergenic (including upstream-gene), and UTR variants?
> Treat each per-sample table as a per-locus genotype dump: drop rows whose `Zygosity`
> is not `Heterozygous` or `Homozygous Variant`."

- Pros: the instruction now matches the verifier; agents can pass by following the prompt.
- Pros: keeps the analytical work intact (still needs to identify columns, filter, average).
- Pros: the sub-task labeled "intergenic includes upstream_gene_variant" disambiguates the
  one remaining footgun in the data.
- Cons: somewhat hand-holding for what is supposed to be a "hard" computational-biology
  question. Predicted new pass rate: probably 12–15 / 18, since the agents already do
  the rest of the work correctly.

### Fix B — keep the prompt terse but make the dataset self-disclosing

Add a `README.md` next to the per-sample workbooks that says:

> "Each workbook is the per-locus genotype output for one sample on the CHIP gene
> panel. Reference-zygosity rows indicate the sample carries the reference allele
> (no variant); they are NOT CHIP variants."

- Pros: still requires the agent to *find and read* the README — the discovery step
  remains.
- Pros: doesn't reveal exactly how to filter, only the data semantics.
- Cons: still relies on the agent to add an unstated step to its filter; agents that
  power-through to filtering on `Sequence Ontology` only might still miss it. Predicted
  new pass rate: 6–10 / 18.

### Fix C — change the verifier rubric (NOT recommended)

Loosen the range to "Between 40 and 320 inclusive" or accept either interpretation.
This is a simplification (it makes the wrong answer correct) and damages the task's
scientific integrity. **Do not adopt.**

### Fix D — provide an example calculation in the instruction

Include a worked example for one sample showing column choice and the value_counts on
`Zygosity`. Effectively trivializes the task. **Do not adopt.**

**Recommended:** Fix A. It eliminates the prompt/verifier mismatch without removing
analytical difficulty, and it produces an instruction that an evaluator can defend as
"answerable from the prompt alone."

---

## 9. Hacking / cheating risk

- **Verifier hacking:** Low. The judge is an LLM, but the prompt is a 4-line equivalence
  check; the agent cannot prompt-inject through the answer text in any obvious way that
  would make GPT-4o accept "300" as equivalent to "Between 40 and 60 inclusive". (One
  could imagine `<answer>52</answer>` being submitted blindly as a guess — the four
  candidate ranges in the BixBench MCQ form are (25,35), (40,60), (120,150), (230,260),
  so 52 is one of four blind-guess buckets and gives a 25 % rate. We see 2 / 18 = 11 %
  → no agent appears to be blind-guessing.)
- **Internet leakage:** The Bloom-syndrome paper is published
  (https://doi.org/10.3324/haematol.2024.285239) and the benchmark canary GUID is in
  the Dockerfile. Future model training on the paper PDF could leak the answer.
- **Capsule pre-knowledge:** The capsule UUID `a02b761a-...` is on HuggingFace and the
  data are downloaded in-container. An agent that knows the capsule from training could
  in principle short-circuit. No evidence of this in the 18 trajectories.
- **Inspect-then-skip-work:** No agent did `cat answer.txt && exit` style hacking.
- **Marking complete without writing answer.txt:** Yes — terminus-2/gpt-5.4 `f6b8c381`
  did call `mark_task_complete()` without verifying. This is an agent harness bug, not
  a malicious hack, but it gets caught by the `RewardFileNotFoundError` path which
  filters the trial out of the summary anyway. Not a cheating route.

No meaningful hacking pathway. The task fails honestly.

---

## 10. Final verdict (after revision in §11)

**ACCEPT (borderline).** The task tests legitimate genomics-aware capability — see §11
for the revised reasoning. Summary:

- **Closeness to passing:** 14/18 are off by a multiplicative factor of ~6, one
  conceptual step away from a pass — the Reference-zygosity filter.
- **Variation across models:** Almost none on the failure side; the discriminating
  step is "did the agent treat the data as joint-genotyping output and inspect
  `Zygosity`?" Codex/gpt-5.4 does this 2 / 3 of the time; every other (agent, model)
  cell fails 3 / 3.
- **Surface vs root:** Surface is "wrong number ~300"; root is "the agent did not
  recognize that a per-locus genotype workbook contains reference-genotype rows that
  are not variants in the genomic sense." This is a genuine domain-awareness gap, not
  a prompt-completeness gotcha (revised position — see §11).
- **Theoretically solvable from the environment:** Yes — codex/gpt-5.4 demonstrated
  it twice unprompted by inspecting `Zygosity` value_counts and reasoning that
  Reference rows aren't variants ("the right denominator is non-reference variant
  rows per sample").
- **Should it be in HaborMix?** Yes, with a caveat. The 11 % pass rate is low but
  defensible for a "hard" computational-biology task. The capability gap revealed
  is real and discriminating: defensive descriptive statistics + biological-
  plausibility sanity-checking + recognition of standard joint-genotyping schema.
  The instruction's closed-list phrasing is a minor prompt-design weakness but not
  a disqualifier.

---

## Appendix A — Per-run table

| run id | agent | model | reward | submitted | mapped intergenic→upstream? | inspected `Zygosity`? | dropped Reference? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 61ff3ccf | codex | gpt-5.4 | 1.0 | 52.91 | partial (kept upstream, only 3 rows cohort-wide) | **yes** | **yes** |
| 658ddb1e | codex | gpt-5.4 | 1.0 | 52.33 | partial (kept upstream) | **yes** | **yes** |
| 9b9dc5c0 | codex | gpt-5.4 | 0.0 | 300.94 | yes (substring) | no | no |
| 9ced65a1 | claude-code | claude-opus-4-6 | 0.0 | 300.94 | no | no | no |
| 0ea2fe4c | claude-code | claude-opus-4-6 | 0.0 | 301.93 | no | no | no |
| 4912fbde | claude-code | claude-opus-4-6 | 0.0 | 300.94 | no | no | no |
| 799ec7da | terminus-2 | claude-opus-4-6 | 0.0 | 300.94 | no (kept upstream) | no | no |
| a6bb8d4e | terminus-2 | claude-opus-4-6 | 0.0 | 300.94 | considered, kept | no | no |
| ab1cc60a | terminus-2 | claude-opus-4-6 | 0.0 | 300.94 | considered, kept | no | no |
| 11d0fd7b | terminus-2 | gpt-5.4 | 0.0 | 300.94 | no | no | no |
| 9d262fd4 | terminus-2 | gpt-5.4 | 0.0 | 300.94 | no | no | no |
| f6b8c381 | terminus-2 | gpt-5.4 | NULL (no submit) | — | no | no | no |
| 20600ea5 | gemini-cli | gemini-3.1-pro-preview | 0.0 | 300.94 | considered, kept | saw "Reference" in dup dump only | no |
| 3b7b6899 | gemini-cli | gemini-3.1-pro-preview | 0.0 | 300.26 | yes | no | no |
| e4bd2fe3 | gemini-cli | gemini-3.1-pro-preview | 0.0 | 300.26 | yes | no | no |
| 596bd91b | terminus-2 | gemini-3.1-pro-preview | 0.0 | 300.26 | yes | no | no |
| 6fcc4a65 | terminus-2 | gemini-3.1-pro-preview | 0.0 | 300.26 | yes | no | no |
| 988a2b10 | terminus-2 | gemini-3.1-pro-preview | 0.0 | 300.26 | yes | no | no |

---

## 11. Revisiting the verdict — domain knowledge vs. prompt completeness

The user pushed back on my initial REJECT: *"if the task requires domain knowledge, it
shouldn't be rejected simply because the instruction doesn't mention it."* That reframe
forced me to ask whether the missing step is really "an unstated trap" or "what a
domain-literate analyst would do automatically." After re-examination I revised the
verdict to **ACCEPT (borderline)**. This section records the steelman of both sides
and the reasoning.

### 11a. The genomics-literate reading of the question

"Average number of CHIP **variants** per sample" — the operative word is **variant**.
In clinical and computational genomics, *variant* is a defined term: it means a
deviation from the reference allele at a locus. A homozygous-reference genotype call is
*not* a variant in that sample by the standard definition. So the question is
self-restricting: "count the variants" already implies "exclude reference-genotype
rows", before any of the named filters apply.

The data structure also self-discloses as joint-genotyping output rather than a
pre-filtered variant call set:

- `Zygosity` column contains `Reference / Heterozygous / Homozygous Variant / NaN` —
  the four-way classification produced by joint-calling with hom-ref retention.
- `Inherited From`, `Mendel Error`, `Primary Findings`, `Incidental Findings` columns
  are the standard schema for trio-based clinical genotyping (where you keep all loci,
  including those where the proband is hom-ref, so you can compute Mendelian error rates).
- `Read Depths (DP)`, `Genotype Qualities (GQ)`, `Variant Allele Freq` are the per-
  locus genotype-level QC metrics; their presence means each row is a genotype call,
  not a variant call.
- The folder name `CHIP_DP10_GQ20_PASS` describes *quality filters applied to the
  genotype calls* (DP ≥ 10, GQ ≥ 20, FILTER == PASS). It does **not** claim
  "everything in here is a variant".
- `In_CHIP == True` for every row means "this locus is in the CHIP gene panel" — a
  *gene-panel membership* flag, not a *carrier status* flag.

A working bioinformatician reads this dataset and knows immediately: *to count variants
per sample, drop hom-ref calls.* That's not an extra rule the prompt should have
mentioned — it's part of what "counting variants" means. The named filters
(intronic / intergenic / UTR) are at a different conceptual level: they're annotation-
class filters (clinical interpretation) on top of variant identification (genomics
fundamentals).

### 11b. What I had been weighing it against

My original REJECT relied on three claims that I now think are weaker than I gave them
credit for:

1. *"The instruction's closed list creates a misleading prior."* True, but BixBench's
   instruction template is generic across all 205 questions; it doesn't claim
   exhaustiveness. The phrase "after filtering out X, Y, Z" is naturally read as "in
   addition to the standard variant identification, also drop X, Y, Z" — not as "X, Y,
   Z are the only operations needed".
2. *"`In_CHIP == True` and the folder name reinforce a 'pre-filtered' reading."* They
   do, but only if you don't know what those columns mean. A genomics-literate agent
   knows `In_CHIP` is panel membership and the folder name describes QC filters; neither
   says anything about hom-ref vs. variant.
3. *"16/18 failure rate is too high."* This actually argues the *other* way once the
   domain-knowledge framing is applied: the failure rate measures how many models lack
   genomics literacy, which is exactly what BixBench is built to measure. A high failure
   rate on a hard domain task is the design intent, not a defect.

### 11c. What the trajectories actually reveal about capability

Re-reading the failure trajectories with this lens, the consistent capability gap is:

- **Failure to do basic exploratory analysis on every enum-like column.** Standard
  genotype-data EDA starts with `value_counts` on Zygosity, Filter, In_CHIP, Effect.
  16 / 18 agents skipped Zygosity. This is a generic data-analysis failure that
  happens to manifest as a domain-specific miss.
- **Failure to do biological-plausibility sanity checking.** None of the failing agents
  asked "is ~300 CHIP variants per sample plausible?" CHIP is rare somatic clonal
  hematopoiesis; per-sample counts of dozens are expected. Even without genomics
  expertise, the order-of-magnitude check is a generic scientific-reasoning step.
- **Anchoring on the most semantically obvious column ("Sequence Ontology" matches
  "intronic/intergenic/UTR") and stopping further exploration.** This is the
  pattern-match-and-execute mode of failure that more capable agents resist.

Codex/gpt-5.4 succeeded twice precisely by *not* anchoring: it inspected Zygosity
because it inspects every enum-like column by default, then reasoned from
domain-aware definitions ("non-reference variant rows per sample") to the answer.
That is exactly the capability HaborMix should be measuring.

### 11d. The remaining caveat

The instruction *could* be improved without changing the difficulty:

> *"What is the average number of non-reference CHIP variants per sample after
> filtering out intronic, intergenic, and UTR variants?"*

The single word "non-reference" eliminates the ambiguity for a literal prompt-follower
without giving away any analytical work — the agent still needs to identify the
`Zygosity` column, choose which Zygosity values count as "non-reference", and apply
the annotation filters. This is a wording polish, not a fix to a broken task.

I would recommend the polish to the BixBench upstream, but its absence does not
disqualify the task from HaborMix. The task as-is fairly tests whether an agent can
recognize standard joint-genotyping output and apply the standard semantic of "variant",
which is a capability worth measuring.

### 11e. Updated answer to the central question

**Is the failure due to the task or to agent capability?** **Agent capability.** The
two failing capability classes are concrete and generic:
1. Insufficient defensive descriptive statistics (16 / 18 agents skipped `Zygosity`
   value_counts entirely).
2. Insufficient biological / scientific plausibility checking (no agent flagged that
   ~300 CHIP variants per sample is implausible).

The task's instruction has a minor wording weakness (the closed enumeration), but it is
not the load-bearing cause of the failures. A capable agent succeeds; the failures are
informative about real capability gaps, which is what we want from a benchmark task.

---

## Appendix B — Iteration log

- 2026-05-03 (v1): initial pull of 18 trajectories via Docent MCP; per-(agent,model)
  cluster reports compiled by 6 parallel general-purpose subagents; document drafted
  with verdict REJECT (prompt closed-enumeration was treated as the load-bearing cause).
- 2026-05-03 (v2): user pushed back that domain-knowledge requirements should not
  count against a task. Re-examined under the genomics-literate reading: "CHIP variants"
  already excludes reference-genotype calls by definition; the data is unambiguously
  joint-genotyping output; the failing agents' miss is a generic-EDA + scientific-
  plausibility capability gap, not a prompt-completeness gotcha. Verdict revised to
  ACCEPT (borderline) with a recommended one-word prompt polish ("non-reference").
