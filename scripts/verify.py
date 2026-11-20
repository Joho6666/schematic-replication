"""Compare a page's live pin->net partition with the expected netlist.

usage: python -I verify.py nets.json
nets.json: {"page", "home", "designators":[...], "nets": {"NAME": ["DES:pin", ...]}, "nc": ["DES:pin"]}
A net whose NAME starts with "_" only checks grouping; otherwise the live net name must match too.
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eda  # noqa: E402

spec = json.load(open(sys.argv[1], encoding="utf-8"))
comps = eda.run("sch", "list", "--page", spec["page"], "--include-pins")["result"]["components"]
if spec.get("home"):
    eda.run("sch", "open", "--page", spec["home"], check=False)

mine = set(spec["designators"])
live = {}
nc_live = set()
for c in comps:
    if c.get("designator") not in mine:
        continue
    for p in c.get("pins") or []:
        ref = f"{c['designator']}:{p['pinNumber']}"
        live[ref] = p.get("net")
        if p.get("noConnected"):
            nc_live.add(ref)

groups = defaultdict(set)
for ref, net in live.items():
    if net:
        groups[net].add(ref)

errors = []
for name, refs in spec["nets"].items():
    nets = {live.get(r) for r in refs}
    if None in nets or "" in nets or len(nets) != 1:
        errors.append(f"{name}: pins split/unconnected -> {sorted((r, live.get(r)) for r in refs)}")
        continue
    net = nets.pop()
    extra = groups[net] - set(refs)
    if extra:
        errors.append(f"{name}: live net {net} has extra pins {sorted(extra)}")
    if not name.startswith("_") and net != name:
        errors.append(f"{name}: live net name is {net}")
expected_pins = {r for refs in spec["nets"].values() for r in refs} | set(spec.get("nc", []))
for ref in sorted(set(live) - expected_pins):
    if live[ref]:
        errors.append(f"unexpected connection {ref} -> {live[ref]}")
for ref in spec.get("nc", []):
    if ref not in nc_live:
        errors.append(f"{ref} not marked no-connect")
print(f"checked {len(spec['nets'])} nets / {len(live)} pins")
print("\n".join(errors) if errors else "ALL NETS MATCH")
