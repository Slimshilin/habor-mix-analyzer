from __future__ import annotations

import json

from docent.sdk.client import Docent


COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
TRANSCRIPT_ID = "7a0fce49-6ce2-44e9-b5b0-b58c35546814"


def main() -> None:
    client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COLLECTION_ID}")
    tables = ["transcript_messages", "messages", "events", "blocks"]
    column_sets = [
        "id, transcript_id, role, content, metadata_json",
        "id, transcript_id, name, content, metadata_json",
        "id, transcript_id, message_index, role, content",
        "id, transcript_id, idx, role, content",
        "id, transcript_id, block_idx, role, content",
        "id, transcript_id, sequence_number, role, content",
    ]
    for table in tables:
        for columns in column_sets:
            query = f"SELECT {columns} FROM {table} WHERE transcript_id = '{TRANSCRIPT_ID}' LIMIT 2"
            try:
                result = client.execute_dql(COLLECTION_ID, query)
            except Exception as exc:
                print("ERR", table, columns, str(exc).splitlines()[0][:220])
                continue
            print("OK", table, columns)
            print(result["columns"])
            print(json.dumps(result["rows"][:2], indent=2)[:2000])
            break


if __name__ == "__main__":
    main()
