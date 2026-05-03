# Task Context: `gso/gso-huggingface--transformers-d51b589`

The task asks agents to optimize a Hugging Face Transformers XLNet inference script using `XLNetLMHeadModel.from_pretrained("xlnet-base-cased")`, sequence length 612, batch size 8, and:

```python
attention_mask = torch.ones_like(input_ids)
inputs = {"input_ids": input_ids, "input_mask": attention_mask}
```

In this old XLNet implementation, `input_mask=1` means masked/padding, not valid-token attention. Therefore the prompt's variable name is misleading: the workload is effectively a degenerate all-masked/diagonal self-attention case, not normal all-valid attention.

The prompt's equivalence check is strict:

```python
tol = 1e-05
assert abs(ref_sum - curr_sum) < tol
```

The oracle patch in `task_files/solve.sh` changes only `transformers/modeling_xlnet.py`. Its important idea is to keep the same XLNet arithmetic but lay out attention scores as `(batch, heads, query, key)` (`bnij`) rather than `(query, key, batch, heads)` (`ijbn`), then run `F.softmax(..., dim=3)` on the contiguous last dimension and adapt `rel_shift`, mask application, and attention-value einsums accordingly.

All 18 runs were exported from Docent. The user pasted 17 links; the missing run was discovered by querying the collection for this task:

```text
d7d0c912-41d0-49ac-9484-c7073c9e4a53
codex / gpt-5.4 / failure
trial_id: 9bcd4049-600b-42b3-9335-fe324a824de3
```
