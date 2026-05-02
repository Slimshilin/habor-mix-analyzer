#!/usr/bin/env python3
"""Fetch and summarize transcript for a single agent run."""

import sys
import json
from docent.sdk.client import Docent

COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"

def fetch_transcript(run_id):
    client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COLLECTION_ID}/agent_run/{run_id}")

    rows = client.execute_dql(
        COLLECTION_ID,
        f"SELECT t.id FROM transcripts t WHERE t.agent_run_id = '{run_id}' LIMIT 1"
    )
    dicts = client.dql_result_to_dicts(rows)
    if not dicts:
        print(f"No transcript found for {run_id}")
        return

    transcript_id = dicts[0]["id"]

    # Fetch the transcript messages
    transcript = client.get_transcript(COLLECTION_ID, transcript_id)
    return transcript

if __name__ == "__main__":
    run_id = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else run_id

    client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COLLECTION_ID}/agent_run/{run_id}")

    rows = client.execute_dql(
        COLLECTION_ID,
        f"SELECT t.id FROM transcripts t WHERE t.agent_run_id = '{run_id}' LIMIT 1"
    )
    dicts = client.dql_result_to_dicts(rows)
    if not dicts:
        print(f"No transcript found for {run_id}")
        sys.exit(1)

    transcript_id = dicts[0]["id"]
    print(f"Transcript ID: {transcript_id}")
    print(f"Run ID: {run_id}")
    print(f"Label: {label}")

    transcript = client.get_transcript(COLLECTION_ID, transcript_id)
    messages = transcript.messages
    print(f"Total messages: {len(messages)}")
    print("="*80)

    for i, msg in enumerate(messages):
        role = getattr(msg, 'role', 'unknown')
        content = getattr(msg, 'content', '')
        if isinstance(content, list):
            text_parts = []
            for c in content:
                if hasattr(c, 'text'):
                    text_parts.append(c.text)
                elif isinstance(c, dict) and 'text' in c:
                    text_parts.append(c['text'])
                elif hasattr(c, 'type') and c.type == 'tool_use':
                    text_parts.append(f"[TOOL: {c.name}({str(getattr(c, 'input', {}))[:200]})]")
                elif isinstance(c, dict) and c.get('type') == 'tool_use':
                    text_parts.append(f"[TOOL: {c.get('name')}({str(c.get('input', {}))[:200]})]")
                elif hasattr(c, 'type') and c.type == 'tool_result':
                    text_parts.append(f"[TOOL_RESULT: {str(getattr(c, 'content', ''))[:300]}]")
                else:
                    text_parts.append(str(c)[:300])
            content_str = '\n'.join(text_parts)
        else:
            content_str = str(content)

        # Truncate very long messages
        if len(content_str) > 2000:
            content_str = content_str[:2000] + f"\n... [truncated, {len(content_str)} total chars]"

        print(f"\n--- Message {i+1} [{role}] ---")
        print(content_str)
