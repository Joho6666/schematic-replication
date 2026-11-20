"""Place devices off-sheet once and print their pin offsets for specgen.DEV.

usage: python -I probe_pins.py <page-uuid> <device-uuid> [<device-uuid> ...]

Probes are deliberately LEFT on the page (x >= 1400): deleting the last instance of a
device can make later `sch place` of that device hang. Their ids are appended to
probes.json in the cwd; build.py then moves a probe into place instead of placing anew.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eda  # noqa: E402

page, uuids = sys.argv[1], sys.argv[2:]
try:
    probes = json.load(open("probes.json", encoding="utf-8"))
except FileNotFoundError:
    probes = {}
start = sum(len(v) for v in probes.values())
placed = {}
for i, u in enumerate(uuids, start):
    x, y = 1400 + (i % 5) * 150, 800 - (i // 5 % 5) * 150
    try:
        r = eda.run("sch", "place", "--lib", eda.LIB, "--uuid", u, "--x", x, "--y", y, doc=page, retries=1)["result"]
        placed[r["primitiveId"]] = (u, x, y)
        probes.setdefault(u, []).append(r["primitiveId"])
    except RuntimeError as e:
        print("PLACE FAILED", u, str(e)[-80:], "-> try another LCSC entry with the same value")
json.dump(probes, open("probes.json", "w", encoding="utf-8"), indent=1)

comps = eda.run("sch", "list", "--page", page, "--include-pins", "--include-bbox")["result"]["components"]
for c in comps:
    if c["primitiveId"] in placed:
        u, x, y = placed[c["primitiveId"]]
        pins = {p["pinNumber"]: (round(p["x"] - x), round(p["y"] - y)) for p in c["pins"]}
        names = {p["pinNumber"]: p["pinName"] for p in c["pins"]}
        print(f"{c['component']['name']}  uuid={u}  probe={c['primitiveId']}")
        print(f"    offsets={pins}   (rotation 0, no mirror -> paste into specgen.DEV)")
        print(f"    names={names}")
