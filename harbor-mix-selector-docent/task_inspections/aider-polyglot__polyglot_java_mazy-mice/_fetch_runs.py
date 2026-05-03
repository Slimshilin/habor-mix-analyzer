"""Fetch full transcripts of all 18 mazy-mice runs and save as plain text per run."""
from pathlib import Path
import json, sys
from docent.sdk.client import Docent

COLLECTION = "640e920a-aef3-4b7c-9487-69899ef19e9d"
OUT = Path(__file__).parent / "trajectories"
OUT.mkdir(exist_ok=True)

RUNS = {
    # passes
    "f9ef9cc8-664a-4321-a64f-cb96c553b6d3": ("claude-code", "claude-opus-4-6", "PASS"),
    "7f97e4b5-6b1b-45f5-b8bb-37b0c4a9bd47": ("claude-code", "claude-opus-4-6", "PASS"),
    "5b1fb9f6-3124-4d1e-b2f5-18c10169d93a": ("claude-code", "claude-opus-4-6", "PASS"),
    "c45636bf-4088-424d-bcff-bc29711a9361": ("terminus-2", "claude-opus-4-6", "PASS"),
    "83ae6e4b-3bc6-4a39-8c68-54f674a718c4": ("terminus-2", "claude-opus-4-6", "PASS"),
    "8bdd8715-5737-4c33-af7f-55a4cd9752f3": ("terminus-2", "claude-opus-4-6", "PASS"),
    # codex / gpt-5.4
    "1fa6ed45-8c82-4e0c-9376-bd4dbaa1a205": ("codex", "gpt-5.4", "FAIL_DIM"),
    "399965ff-56e1-4fd3-a56c-c2b62cc8c081": ("codex", "gpt-5.4", "FAIL_DIM"),
    "3a65d34f-f581-4627-b22f-a7b964be40cf": ("codex", "gpt-5.4", "FAIL_JAVA_HOME"),
    # terminus-2 / gpt-5.4
    "06139fa9-4d0b-4542-a6a2-a1e3efca499c": ("terminus-2", "gpt-5.4", "FAIL_DIM"),
    "b93135dc-c9da-4b9e-87cd-ef66736dc6ae": ("terminus-2", "gpt-5.4", "FAIL_DIM"),
    "5db0a790-c779-4aa1-8a85-378b9e4ceac9": ("terminus-2", "gpt-5.4", "FAIL_JAVA_HOME"),
    # gemini-cli / gemini
    "09cdc8c0-c84e-4fcf-8d6c-7bcf2bfa7a08": ("gemini-cli", "gemini-3.1-pro-preview", "FAIL_DIM"),
    "b52ff7ac-013c-4db4-b6d7-334857cfe4a3": ("gemini-cli", "gemini-3.1-pro-preview", "FAIL_DIM"),
    "dc0eafbd-f677-4c7c-8f1e-2940b14f2e53": ("gemini-cli", "gemini-3.1-pro-preview", "FAIL_JAVA_HOME"),
    # terminus-2 / gemini
    "d47117a6-f576-4f03-95fd-677925dc6726": ("terminus-2", "gemini-3.1-pro-preview", "FAIL_DIM"),
    "1f801e11-33aa-49ac-9b8c-28e36ce6ce49": ("terminus-2", "gemini-3.1-pro-preview", "FAIL_DIM"),
    "62f7b717-4b07-4fb1-b893-5f07c2843d4a": ("terminus-2", "gemini-3.1-pro-preview", "FAIL_JAVA_HOME"),
}

c = Docent()


def render_block(b):
    role = b.get("role", "")
    parts = []
    parts.append(f"\n=== B{b.get('idx', '?')} role={role} ===")
    blocks = b.get("blocks") or [b]
    for blk in blocks if isinstance(blocks, list) else [blocks]:
        if isinstance(blk, dict):
            t = blk.get("type", "")
            if t == "text":
                parts.append(blk.get("text", ""))
            elif t == "reasoning":
                parts.append(f"[reasoning] {blk.get('text', '')}")
            elif t == "tool_call":
                tn = blk.get("tool_name", "")
                args = blk.get("input", {}) or blk.get("arguments", {})
                parts.append(f"[tool_call {tn}] {json.dumps(args)[:4000]}")
            elif t == "tool_result":
                content = blk.get("content", blk.get("text", ""))
                parts.append(f"[tool_result] {str(content)[:6000]}")
            else:
                parts.append(json.dumps(blk)[:3000])
    return "\n".join(parts)


def fetch_one(run_id, agent_name, model_name, status):
    print(f"Fetching {run_id} ({agent_name}/{model_name}) [{status}] ...", flush=True)
    try:
        run = c.get_agent_run(COLLECTION, run_id)
    except Exception as e:
        print(f"  FAILED: {e}")
        return
    out_path = OUT / f"{status}__{agent_name}__{model_name}__{run_id}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Agent run {run_id}\n# agent={agent_name} model={model_name} bucket={status}\n\n")
        # Try to walk transcripts. The structure can be a list of transcripts or a Pydantic model.
        try:
            transcripts = run.transcripts
        except AttributeError:
            transcripts = getattr(run, "transcripts", None) or run.get("transcripts", [])
        if isinstance(transcripts, dict):
            transcripts = list(transcripts.values())
        for t in transcripts or []:
            tname = getattr(t, "name", None) or t.get("name") if isinstance(t, dict) else None
            f.write(f"\n\n========== transcript: {tname} ==========\n")
            blocks = getattr(t, "messages", None)
            if blocks is None and isinstance(t, dict):
                blocks = t.get("messages", [])
            for i, m in enumerate(blocks or []):
                role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else "?")
                f.write(f"\n--- msg {i} role={role} ---\n")
                content = getattr(m, "content", None)
                if content is None and isinstance(m, dict):
                    content = m.get("content", "")
                if isinstance(content, list):
                    for blk in content:
                        if isinstance(blk, dict):
                            t_ = blk.get("type", "")
                            if t_ == "text":
                                f.write(blk.get("text", ""))
                            elif t_ == "reasoning":
                                f.write(f"\n[reasoning] {blk.get('text', '')}\n")
                            elif t_ == "tool_use":
                                f.write(f"\n[tool_use {blk.get('name','?')}] {json.dumps(blk.get('input', {}))[:6000]}\n")
                            elif t_ == "tool_result":
                                f.write(f"\n[tool_result] {str(blk.get('content',''))[:8000]}\n")
                            else:
                                f.write(f"\n[{t_}] {json.dumps(blk)[:3000]}\n")
                        else:
                            # blk is a Pydantic model
                            tt = getattr(blk, "type", "")
                            if tt == "text":
                                f.write(getattr(blk, "text", ""))
                            elif tt == "reasoning":
                                f.write(f"\n[reasoning] {getattr(blk, 'text', '')}\n")
                            elif tt == "tool_use":
                                f.write(f"\n[tool_use {getattr(blk,'name','?')}] {json.dumps(getattr(blk,'input',{}))[:6000]}\n")
                            elif tt == "tool_result":
                                cc = getattr(blk, "content", "")
                                f.write(f"\n[tool_result] {str(cc)[:8000]}\n")
                            else:
                                f.write(f"\n[{tt}] {str(blk)[:3000]}\n")
                else:
                    f.write(str(content)[:8000])
    print(f"  wrote {out_path.name} ({out_path.stat().st_size} bytes)")


for rid, (agent, model, status) in RUNS.items():
    fetch_one(rid, agent, model, status)

print("done")
