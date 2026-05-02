# Task Inspection: terminal-bench / dna-insert

**Task**: Design Q5 site-directed-mutagenesis primers that insert a 39-bp fragment into a plasmid
**Benchmark**: terminal-bench
**Checksum**: `162cd54836ca70b3a4c62f7fab0e369007f76488213865efdf563b20dceebb15`
**Collection**: `640e920a-aef3-4b7c-9487-69899ef19e9d`
**Pass rate observed**: **4/18 (22%)**
**Gemini verdict**: accept ("well-defined molecular biology engineering task with clear constraints and a robust verifier")
**My verdict**: **MARGINAL — lean REJECT unless fixed.** See Section 7. The 4 successes are real, but **12 of the 14 failures are not the "tight Tm misses" Gemini described — they are caused by a 2-bp boundary ambiguity in the verifier's hard-coded insert spelling.** The verifier enforces a stricter condition than biological correctness; agents that produce a perfectly valid wet-lab design (correct mutant plasmid, satisfying every stated rule under their own algorithmic frame) are graded as failures because the verifier's literal substring search picks the *other* of two equally valid 39-bp windows.

---

## 1. What the task asks

Agents start with `/app/sequences.fasta` containing two sequences: an `input` plasmid and an `output` plasmid where `output = input[:N] + insert + input[N:]` (the output is the input with one contiguous 39-bp insertion). They must produce `/app/primers.fasta` with **one** primer pair (4 lines, fwd then rev), suitable for NEB Q5 site-directed mutagenesis (back-to-back primers, insertion encoded as 5' overhang(s)). Constraints from the prompt:

- annealing length: 15–45 bp
- Tm: 58–72 °C
- |Tm_fwd − Tm_rev| ≤ 5 °C
- Tm computed with `oligotm -tp 1 -sc 1 -mv 50 -dv 2 -n 0.8 -d 500 <annealing_seq>`
- minimum number of primer pairs (i.e. exactly one)

Tools: agent has `apt`, can install `primer3` (provides `oligotm`) and `emboss` (provides `needle`). Wall budget: 1800 s.

## 2. What the verifier *actually* enforces (hidden from the agent)

`tests/test_outputs.py` (verbatim copy at `key_files/test_outputs.py`) hard-codes three strings:

```python
vector1 = "tctagaaataattttgtttaactttaagaaggagatatacatatg"   # 45-bp left flank,  AT-rich
vector2 = "agcaagggcgaggagctgttcaccggggtggtgcccatcctggtc"   # 45-bp right flank, GC-rich
insert  = "agtagattagaagaagaattaagaagaagattaacagaa"          # 39-bp insert (starts "ag", ends "aa")
```

It then:
1. Reads `primers.fasta`, requires exactly 4 lines.
2. Computes `primers_concat = rc(rev_primer) + fwd_primer`.
3. **Searches for the literal `insert` string** in `primers_concat`. This is the choke point.
4. Defines `annealed_rev = primers_concat[:insert_start]` and `annealed_fwd = primers_concat[insert_end:]`.
5. Asserts `vector1[-len(annealed_rev):] == annealed_rev` (line 83) and `vector2[:len(annealed_fwd)] == annealed_fwd` (line 86) — **exact string equality** with the hard-coded flanks.
6. Asserts each annealing length ∈ [15, 45], each Tm ∈ [58, 72], |ΔTm| ≤ 5.

Two structural facts about this locus that matter enormously:

- **Sequence repeats at the insertion boundary**: input reads `...catatg | agcaagggc...`; output reads `...catatg | agtagattag...aacagaaag | caagggc...`. Because the insert starts `ag`, ends `ag`, AND the post-insertion vector starts `agcaagggc`, the same 39-base string can be aligned **2 bp earlier or 2 bp later** and still produce an identical output plasmid. There are TWO equally valid 39-bp insert windows.
- **Asymmetric Tm landscape**: vector1 is AT-rich (Tm ≈ 58 °C only at length 28); vector2 is GC-rich (Tm > 65 °C even at length 17). Any 2-bp shift across the boundary swaps GC-rich bases into one primer and AT-rich bases out of the other → ΔTm swings ~6 °C.

The combination is a **trap**: a 2-bp ambiguity that, in this specific locus, blows past every Tm tolerance.

## 3. Run inventory (18 trials)

| ID | Agent | Model | Reward | Failed at line |
|---|---|---|---|---|
| `17f6766f` | claude-code | claude-opus-4-6 | **1.0** | — |
| `29b3114f` | claude-code | claude-opus-4-6 | **1.0** | — |
| `0f688714` | claude-code | claude-opus-4-6 | 0.0 | 100 (\|ΔTm\|) |
| `9ddfd9f3` | codex | gpt-5.4 | 0.0 | 100 (\|ΔTm\|) |
| `e8c6fd29` | codex | gpt-5.4 | 0.0 | 100 (\|ΔTm\|) |
| `eb610659` | codex | gpt-5.4 | 0.0 | 97 (rev Tm < 58) |
| `c4f1f788` | gemini-cli | gemini-3.1-pro-preview | 0.0 | 100 (\|ΔTm\|) |
| `e8706f0b` | gemini-cli | gemini-3.1-pro-preview | 0.0 | 100 (\|ΔTm\|) |
| `c27626a5` | gemini-cli | gemini-3.1-pro-preview | 0.0 | 97 (rev Tm < 58) |
| `16ebb768` | terminus-2 | claude-opus-4-6 | **1.0** | — |
| `00bbc598` | terminus-2 | claude-opus-4-6 | 0.0 | 100 (\|ΔTm\|) |
| `a2c46411` | terminus-2 | claude-opus-4-6 | 0.0 | 100 (\|ΔTm\|) |
| `35be0719` | terminus-2 | gemini-3.1-pro-preview | **1.0** | — |
| `b26cfbf2` | terminus-2 | gemini-3.1-pro-preview | 0.0 | 100 (\|ΔTm\|) |
| `da5d33ac` | terminus-2 | gemini-3.1-pro-preview | 0.0 | 97 (rev Tm < 58) |
| `885c69d7` | terminus-2 | gpt-5.4 | 0.0 | 100 (\|ΔTm\|) |
| `e611911a` | terminus-2 | gpt-5.4 | 0.0 | 74 (fwd anneal length > 45) |
| `78dd56d6` | terminus-2 | gpt-5.4 | 0.0 | 68 (insert not found in concat) |

Per-model success rate: claude-opus-4-6 3/9 (33%), gemini-3.1-pro 1/6 (17%), gpt-5.4 0/6 (0%). No exceptions / timeouts — every run finished cleanly.

Failure clustering by assertion:
- 9 runs at line 100 (|ΔTm| > 5 °C)
- 3 runs at line 97 (rev Tm < 58 °C)
- 1 run at line 74 (fwd annealing length > 45)
- 1 run at line 68 (insert not present in `rc(rev) + fwd`)

## 4. How agents (mostly) failed: surface vs root cause

### 4a. The dominant failure mode (12/14 runs)

All 9 of the line-100 failures and all 3 of the line-97 failures share **one root cause**: the agents' diff algorithm extracted the **shifted** 39-bp insert window `tagattagaagaagaattaagaagaagattaacagaaag` (starts with `t`, ends with `ag`), while the verifier hard-codes the **leftmost-canonical** window `agtagattagaagaagaattaagaagaagattaacagaa` (starts with `ag`, ends with `aa`). Both are mathematically valid representations of the same insertion (because of the `ag…ag` repeat at the boundary).

Almost every failed agent used a longest-common-prefix-then-longest-common-suffix walk to localise the diff. This deterministic walk extends 2 bp past the leftmost canonical breakpoint (because input `...catatgag-caagggc` and output `...catatgag-tagattag...` share `catatgag` as a 214-base common prefix) and consequently identifies the shifted window. The agents then design a primer pair around their shifted breakpoint, validate **against their own representation**, and report success.

When the verifier reconstructs `rc(rev) + fwd`, it can usually still find the canonical insert as a substring, but slices the annealing regions on either side of that canonical hit — which **steals 2 GC-rich bases (`ag` of `agcaaggg…`) from the start of vector2** and **gives them to the forward primer's annealing region**, while **stripping 2 AT-rich bases from the end of the reverse primer's annealing region**. The asymmetry (GC bases moved to the GC-rich primer, AT bases removed from the AT-rich primer) opens a ~6 °C Tm gap that the agent never sees.

Concrete example — runs `00bbc598`, `a2c46411`, `b26cfbf2` all submit the **identical primer pair**:
```
>forward_primer
TAGATTAGAAGAAGAATTAAGAAGAAGATTAACAGAAAGCAAGGGCGAGGAGCTGTT       # 57 nt = 39 tail + 18 anneal
>reverse_primer
CTCATATGTATATCTCCTTCTTAAAGTTAAACAAAATTATTTCTA                  # 45 nt all annealing
```
- **Agent's view** (using their shifted insert): annealed_fwd = `CAAGGGCGAGGAGCTGTT` (18 nt) Tm 63.81 °C; annealed_rev_sense = `…catatgag` matching first 45 of vector1; their oligotm reports both Tms = **63.81 °C**, |ΔTm| = **0.00 °C**. They confidently `mark_task_complete()`.
- **Verifier's view** (using canonical insert): finds `agtag…acagaa` inside `rc(rev)+fwd`. Strips 2 bp (`ag`) from end of agent's rev annealing → 43 nt `CTCATATGTATATCTCCTTCTTAAAGTTAAACAAAATTATTTC`; adds 2 bp (`AG`) to start of agent's fwd annealing → 20 nt `AGCAAGGGCGAGGAGCTGTT`. Verifier-computed Tm: fwd ≈ 67 °C, rev ≈ 60.5 °C, **|ΔTm| ≈ 6.5 °C → fail line 100**.

The same dynamic explains all line-97 failures: those 3 agents picked the shortest legal rev annealing (28 bp at Tm 58.04 °C, zero margin), and the 2-bp truncation by the verifier dropped Tm to ~56.5 °C, below the 58 °C floor.

### 4b. The two outlier failures

- **`78dd56d6`** (line 68, "insert not found"): used the shifted insert spelling AND placed only the 39-bp shifted insert sequence in the primer overhangs. When `rc(rev)+fwd` is searched for the canonical `agtag…acagaa`, no exact match exists (the agents' overhangs literally do not contain that 39-mer, only a 2-bp-shifted version of it). Same root cause as 4a; just caught at the substring search step instead of the slicing step.
- **`e611911a`** (line 74, "fwd anneal too long"): this one is genuinely a different bug. The agent put the *full canonical* 39-bp insert on **both** primer 5' tails, so `rc(rev)+fwd` contains the canonical insert TWICE. The verifier's `find()` returns the first match; everything after that match (the second insert + the fwd annealing region) gets classified as `annealed_fwd`, length = 15 + 39 + 32 = 86 nt > 45. This is a Q5-SDM concept failure: the insert should appear in the primer pair AT MOST ONCE.

### 4c. What the 4 successes did differently

- **`17f6766f` (claude-code/opus)** & **`29b3114f` (claude-code/opus)** anchored at the **unambiguous breakpoint** (insert position 213, `tail_overlap = 0`) and chose the canonical insert spelling. Both put the entire 39-bp insert as the forward primer's 5' tail; reverse primer is pure annealing. Final pairs are nearly identical (fwd annealing = 15 nt, rev annealing = 30–31 nt; |ΔTm| < 1.5 °C). Single-shot designs with one round of self-validation that included reconstructing the would-be PCR product. Neither needed a second iteration — they happened to pick the right anchor on the first try.
- **`16ebb768` (terminus-2/opus)**: explicitly noticed the boundary-overlap trap. Wrote code that uses `circ_input.find(primer[-i:])` to compute the **true** maximal annealing length (not the intended length) and re-derived Tm from that. Caught a wrong 37-bp design at position 215, then a 16-bp-actual-vs-15-bp-intended overlap at position 214, and finally landed on position 213 with the canonical breakpoint. The longest run (46 turns) but the most analytically thorough.
- **`35be0719` (terminus-2/gemini)**: same explicit recovery as 16ebb768. First `solve.py` produced a primer pair its own `verify.py` rejected; wrote `solve2.py` that explicitly searches for the maximal template match, converged on the canonical breakpoint.

The successes share two features: (1) they ended up with the verifier's canonical insert spelling — claude-code by lucky algorithmic convention, terminus-2 by self-debugging — and (2) they explicitly verified their primer pair by simulating the assembled PCR product before submitting.

## 5. Inferring vs hidden information

- **Can the agent infer the verifier's canonical insert spelling from the environment?** Partially. The instruction does not specify which of the two valid 39-mer windows is canonical. The successful agents either picked it by convention (longest-common-prefix-from-the-LEFT happened to give them the canonical window because of how they wrote their diff) or arrived at it by self-correcting via PCR-product simulation. So it IS inferable, but only by an agent that is suspicious enough about boundary ambiguity to either (a) explicitly check both candidate windows or (b) simulate the verifier's reconstruction and grep for its expected insert string.
- **Hidden tests**: the test logic is fully consistent with the prompt's stated rules (length, Tm range, ΔTm, oligotm flags). What is **not** stated in the prompt is the exact byte-level identity of `vector1`, `vector2`, and `insert` — these are derivable from the input file but only up to the 2-bp ambiguity discussed.
- **Could a maximally capable agent solve this with current instructions + env?** Yes, by adopting any of: (i) reconstruct the PCR product after ligation and string-compare to `output`; (ii) test BOTH candidate insert windows and pick the pair satisfying both; (iii) anchor at the unambiguous breakpoint where `tail_overlap = 0`. So the task is theoretically achievable. The 4 successes prove this empirically. The task is NOT under-specified to the point of being unsolvable.

## 6. Surface vs root cause — the table

| Failure surface | # runs | Root cause |
|---|---|---|
| line 100, \|ΔTm\| > 5 °C | 9 | 2-bp insert-window shift; verifier's slicing moves GC-rich bases between primers |
| line 97, rev Tm < 58 °C | 3 | Same 2-bp shift, but the agent left zero Tm headroom by picking minimum-length rev annealing |
| line 74, fwd anneal > 45 | 1 | Conceptual error: full insert placed on BOTH primer tails → duplicated insert in concatenation |
| line 68, insert not found | 1 | Same 2-bp shift; agents' primers carry the shifted insert; canonical insert is absent |

So **at the root, 13/14 failures are about either the boundary ambiguity (12) or a Q5-SDM concept error (1)**. The "engineering rigor in Tm optimization" framing in the original Gemini review is misleading — agents are NOT failing because they couldn't find a Tm-balanced primer pair. They are failing because the Tm constraint is *evaluated against a different annealing region than the one they optimised for*.

## 7. Verdict — task vs. agent bottleneck

This is the question the user asked me to answer:

> **Is the agent failure because of the task itself or the agent capability bottleneck?**

**Mostly the agent — but with a real, fragile task issue that amplifies the cost of one specific reasoning miss.**

Two arguments:

**Pro-agent-bottleneck (the failure is fair):**
- 4 agents passed, including across two different harnesses (claude-code, terminus-2) and two different model families (Opus, Gemini). Pass is reachable.
- The successful path requires a recoverable mode of reasoning ("simulate the verifier / test both alignments"), not occult knowledge.
- All 14 failed agents made the SAME analytical mistake (greedy diff + self-validation in their own coordinate frame). They did not interrogate boundary ambiguity, did not reconstruct the assembled PCR product, did not test their primers against the verifier-style invariants. These are well-known failure modes of LLM agents and are exactly what this kind of rigorous test SHOULD expose.
- The task tests genuine engineering reasoning: choosing breakpoints, optimising Tm, understanding back-to-back primer geometry. The 12 line-100/97 failures are not random; they're a predictable consequence of careless boundary handling.

**Pro-task-issue (the failure is fragile):**
- The 2-bp ambiguity is NOT mentioned in the prompt and is a property of *this specific locus*. Both insert windows produce the same output plasmid; both would work in a real PCR with a real ligase. The verifier enforces a stricter condition (literal substring equality with one specific window) than biological correctness requires.
- The asymmetric Tm landscape (vector1 AT-rich, vector2 GC-rich) AMPLIFIES a 2-bp slip into a guaranteed >5 °C ΔTm failure. In a less extreme locus, the same algorithmic mistake would produce primers that accidentally satisfy the constraints. So the task is essentially set up to punish agents that don't notice the ambiguity — which is a different test than "engineering rigor".
- The original Gemini review described failures as "near misses on Tm". That is **wrong**: the agents' own oligotm logs show |ΔTm| values of 0.00–1.45 °C (well inside the 5 °C tolerance). The failure is at the verifier–agent representation interface, not at the optimisation step. The Gemini review essentially mis-characterised the failure mode.
- The ratio of surface-correct designs (12/14 agents converge on essentially the same primer pair, all of which would actually work in a wet lab) to verifier-pass (4/14) is troubling. This is a reproducibility concern: a strong agent gets penalised for adopting a slightly different (but biologically equivalent) parsing.

**Net call**: I lean **REJECT** unless the verifier is fixed. The current task is a stress test of "do you suspect that your boundary representation might disagree with the grader's", which is not the same as the "PCR primer design with constrained Tm optimisation" task that the prompt advertises. The 22% pass rate is real, but it under-rewards correct biology and over-rewards lucky alignment convention.

## 8. Proposed fixes (concrete, not dilutions)

### Fix A (preferred — biologically correct verifier)
Replace the literal substring check with a **PCR-product reconstruction check**. Instead of:
```python
primers_concat = rc(rev_primer) + fwd_primer
insert_start = primers_concat.find(insert)
annealed_rev = primers_concat[:insert_start]
annealed_fwd = primers_concat[insert_end:]
assert vector1[-len(annealed_rev):] == annealed_rev
assert vector2[:len(annealed_fwd)] == annealed_fwd
```
do:
```python
# Find the longest 3' suffix of fwd_primer that matches the input plasmid (= annealed_fwd).
# Find the longest 3' suffix of rev_primer that matches rc(input) (= annealed_rev_rc).
# Reconstruct the linear PCR product and check that ligation yields `output`.
```
This rewards any biologically valid primer pair, regardless of which 2-bp boundary the agent picks.

### Fix B (cheap — disambiguate in the prompt)
Add to the instruction:
> The 39-bp inserted sequence begins with `agt` and ends with `gaa`. The annealing region of the reverse primer must end immediately before the inserted sequence; the annealing region of the forward primer must begin immediately after the inserted sequence.

This eliminates the ambiguity by fiat. Less elegant than Fix A — it gives away part of the bioinformatics reasoning — but it makes the verifier's contract unambiguous.

### Fix C (also cheap — accept either window)
Modify the verifier to try BOTH valid 39-bp windows and accept if either passes. Concretely, enumerate all `k` such that `output[k:k+39]` is a 39-bp insert window consistent with `output = input[:k] + output[k:k+39] + input[k:]`, and accept if any `k` produces a primer pair that satisfies all constraints.

### Why NOT just lower the Tm tolerance to e.g. ±10 °C
Tempting, but wrong. The agents would still produce primers that mostly pass; the test would no longer be sensitive to genuinely bad designs (e.g. the e611911a duplicate-insert error would still fail, and so would Tm <50 °C designs, but the *correctness* of the primer pair would no longer be tested). Better to fix the verifier semantics and keep the tight Tm window.

### Recommended path
**Apply Fix A.** It restores the test to what the prompt advertises ("the generated primers will successfully amplify the input DNA and contain the required overhangs that will result in the output sequence" — verbatim from the test docstring). Predicted pass rate after fix: 12/14 of the current failures would pass (because their primers ARE biologically valid), bringing pass rate to ~16/18. The remaining 2 failures (`78dd56d6` shifted insert + `e611911a` duplicated insert) would still fail — and those are *real* bugs that deserve to fail.

After Fix A, the residual failures genuinely do reflect agent capability bottlenecks: failure to validate via PCR-product reconstruction, and failure to understand back-to-back primer geometry. Those are the right things to test.

## 9. Files in this inspection

- `key_files/task.yaml` — task instruction (verbatim from `/home/shilin/T-Bench/t-bench/tasks/dna-insert/task.yaml`)
- `key_files/sequences.fasta` — input/output plasmid sequences shown to the agent
- `key_files/test_outputs.py` — hidden verifier (annotated)
- `key_files/solution.sh` — author's reference solution (uses the unambiguous breakpoint at position 213)
- `key_files/Dockerfile` — minimal Ubuntu container; agent must self-install primer3
- `task_inspection.md` — this file
