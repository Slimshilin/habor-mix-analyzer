> Pulled from `agent_runs.metadata_json->task->>'instruction'` for run 312fcc35 (gemini-cli, success).

You are participating in a puzzle solving competition. You are an expert at solving puzzles.

Below is a list of input and output pairs with a pattern. Your goal is to identify the pattern or transformation in the training examples that maps the input to the output, then apply that pattern to the test input to give a final output.

Write your answer as a JSON 2D array to `/testbed/output.json`.

--Training Examples--

**Example 0** — 18-row × 24-col input/output (training pair). Source pixel `7` at the bottom-right; "wires" of `1` lead from it to several `2`-bordered rectangles and one `5`-bordered rectangle, each of which gets its interior filled with `7`.

**Example 1** — 12-row × 20-col input/output. Source pixel `4` at the bottom-left; wires of `1` from the source touch a subset of the `2`-bordered rectangles, which then get filled with `4`. Other `2`-rectangles that the wire never reaches stay empty.

**Example 2** — 16-row × 20-col input/output. **Two** independent power sources: a `4` at the bottom right and a separate `4` cluster on the left-bottom. Each one's wire of `1`s (left source) and `3`s (right source) reaches a different subset of `2`-rectangles. Crucially, the colour used for the wire is *not* the colour the rectangle is filled with — the fill is always the colour of the source pixel itself (`4` here).

**Example 3** — 8-row × 8-col, the simplest example. Source `4` at (7,7), wire of `1`s climbs up-left, and the lone `2`-rectangle (rows 0–3, cols 1–4) fills with `4`.

--End of Training Examples--

--Test Input--
30×30 grid (background `5`). Notable pixels:
- Source candidates: a single `8` at (0, 29), a single `6` at (0, 0).
- Multiple wire-like shapes: `1`-paths in the right columns, `3`-paths in the middle, `0` cells at (14, 1) and (18, 2).
- Several `9`-bordered rectangles distributed across the grid.

The agent must infer which source/wire/enclosure relationships hold and fill the right rectangles with the right colour.

Write the answer as a JSON 2D array to `/testbed/output.json`.
