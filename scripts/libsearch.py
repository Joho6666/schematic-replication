"""Search EasyEDA library for several queries and print compact rows.

usage: python -I libsearch.py <limit> "query1" "query2" ...
"""
import json
import os
import subprocess
import sys

limit = sys.argv[1]
for q in sys.argv[2:]:
    out = subprocess.run(
        ["easyeda"] + (["--project", os.environ["EASYEDA_PROJECT"]] if os.environ.get("EASYEDA_PROJECT") else []) + ["lib", "search", "--query", q, "--limit", limit],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout
    print(f"######## {q}")
    try:
        items = json.loads(out)["result"]["components"]
    except Exception:
        print(out[:400])
        continue
    for i in items:
        print(" ", i.get("lcsc"), "|", i.get("name"), "|", i.get("footprintName"),
              "|", i.get("libraryUuid"), i.get("uuid"), "|", (i.get("description") or "")[:50])
