"""Build one schematic page from a JSON spec (made with specgen.Page).

Every write is pinned with --doc to the target page; after each write the active page is
switched back to spec["home"] (if set) so another agent sharing the EDA window keeps
writing to its own page.

usage: python -I build.py spec.json [place|wire|all]
  place: adopt probes / place parts, then check every expected pin coordinate
  wire : (re)check pins, then wires -> flags -> ports -> no-connects -> texts
Re-runnable: completed writes are recorded in <spec>.log.jsonl and skipped.

Spec: {"page", "home", "parts":[{des,uuid,x,y,rot,mirror}], "expect":{"DES:pin":[x,y]},
       "wires":[{pts}], "flags":[{at|pin,kind,net,dir,off}], "ports":[{kind,net,x,y,rot}],
       "nc":{"DES":[pins]}, "texts":[{content,x,y,size}]}
A wire point is [x,y] or "DES:pin".
probes.json (written by probe_pins.py, optional, in the cwd): {device_uuid: [primitiveId, ...]}
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eda  # noqa: E402

spec = json.load(open(sys.argv[1], encoding="utf-8"))
stage = sys.argv[2] if len(sys.argv) > 2 else "all"
if stage not in ("place", "wire", "all"):
    sys.exit(f"unknown stage {stage}")
PAGE, HOME = spec["page"], spec.get("home")  # home: the other agent's page in a shared window
LOG = sys.argv[1].replace(".json", ".log.jsonl")
done = set()
try:
    for line in open(LOG, encoding="utf-8"):
        done.add(json.dumps(json.loads(line)["args"]))
except FileNotFoundError:
    pass
log = open(LOG, "a", encoding="utf-8")
try:
    probes = json.load(open("probes.json", encoding="utf-8"))
except FileNotFoundError:
    probes = {}


def home():
    if HOME:
        eda.run("sch", "open", "--page", HOME, check=False)


def write(*args):
    key = json.dumps([str(a) for a in args])
    if key in done:
        return {"skipped": True}
    d = eda.run(*args, doc=PAGE)
    done.add(key)
    log.write(json.dumps({"args": [str(a) for a in args], "result": d.get("result")}, ensure_ascii=False) + "\n")
    home()
    return d["result"]


def list_page():
    comps = eda.run("sch", "list", "--page", PAGE, "--include-pins", "--include-bbox")["result"]["components"]
    home()
    return comps


def pin_table(comps):
    table = {}
    for c in comps:
        for p in c.get("pins") or []:
            table[f"{c.get('designator')}:{p['pinNumber']}"] = (p["x"], p["y"], p.get("net"))
    return table


def modify_into_place(pid, p):
    # sch modify uses the read-back rotation convention: place 90 == modify 270
    patch = {"x": p["x"], "y": p["y"], "rotation": (360 - p.get("rot", 0)) % 360,
             "mirror": bool(p.get("mirror")), "designator": p["des"]}
    eda.run("sch", "modify", "--id", pid, "--patch", json.dumps(patch), doc=PAGE)
    home()


if stage in ("place", "all"):
    comps = list_page()
    existing = {c.get("designator") for c in comps}
    present = {c["primitiveId"] for c in comps}
    for p in spec["parts"]:
        if p["des"] in existing:
            print("skip existing", p["des"])
            continue
        pool = [i for i in probes.get(p["uuid"], []) if i in present]
        if pool:  # reuse an off-sheet probe instead of placing the device again
            pid = pool[0]
            probes[p["uuid"]].remove(pid)
            modify_into_place(pid, p)
            print("adopted probe", p["des"], pid)
            continue
        args = ["sch", "place", "--lib", eda.LIB, "--uuid", p["uuid"], "--x", p["x"], "--y", p["y"],
                "--rotation", p.get("rot", 0), "--designator", p["des"]]
        if p.get("mirror"):
            args.append("--mirror")
        try:
            r = eda.run(*args, doc=PAGE, retries=1)["result"]
            print("placed", p["des"], r.get("primitiveId"))
        except RuntimeError as e:
            # a timeout does not mean nothing was placed: look before deciding
            after = [c for c in list_page() if c["primitiveId"] not in present
                     and abs(c["x"] - p["x"]) < 1 and abs(c["y"] - p["y"]) < 1]
            if after:
                c = after[0]
                if c.get("designator") != p["des"]:
                    eda.run("sch", "modify", "--id", c["primitiveId"], "--designator", p["des"], doc=PAGE)
                print("placed (after timeout)", p["des"], c["primitiveId"])
            else:
                print("PLACE FAILED", p["des"], p["uuid"], str(e)[-80:],
                      "-> swap to another LCSC entry with the same value")
        home()
    if probes:
        json.dump(probes, open("probes.json", "w", encoding="utf-8"), indent=1)

pins = pin_table(list_page())
bad = []
for ref, xy in spec.get("expect", {}).items():
    got = pins.get(ref)
    if not got or abs(got[0] - xy[0]) > 0.6 or abs(got[1] - xy[1]) > 0.6:
        bad.append((ref, xy, got))
if bad:
    print("PIN MISMATCH — fix DEV offsets / rotation in the spec before wiring:")
    for b in bad:
        print("  ", b)
    sys.exit(2)
print("all", len(spec.get("expect", {})), "expected pins match")
if stage == "place":
    sys.exit(0)


def pt(p):
    if isinstance(p, str):
        x, y, _ = pins[p]
        # keep the pin's exact float: rounding can leave the wire end a hair off the pin
        return [round(x) if abs(x - round(x)) < 1e-9 else x, round(y) if abs(y - round(y)) < 1e-9 else y]
    return p


for w in spec.get("wires", []):
    pts = [pt(p) for p in w["pts"]]
    write("sch", "wire", "--points", json.dumps(pts), *(["--net", w["net"]] if w.get("net") else []))
print("wires", len(spec.get("wires", [])))

for f in spec.get("flags", []):
    args = ["sch", "connect", "--kind", f["kind"], "--net", f["net"]]
    if "pin" in f:
        args += ["--pin", f["pin"]]
    else:
        args += ["--x", f["at"][0], "--y", f["at"][1]]
    if f.get("dir"):
        args += ["--direction", f["dir"]]
    if f.get("off"):
        args += ["--offset", f["off"]]
    write(*args)
print("flags", len(spec.get("flags", [])))

for pt_ in spec.get("ports", []):
    write("sch", "netflag", "--kind", pt_["kind"], "--net", pt_["net"], "--x", pt_["x"], "--y", pt_["y"],
          "--rotation", pt_["rot"])
print("ports", len(spec.get("ports", [])))

for des, nums in spec.get("nc", {}).items():
    write("sch", "no-connect", "--designator", des, "--pin", ",".join(str(n) for n in nums))
print("nc done")

for t in spec.get("texts", []):
    write("sch", "text", "create", "--content", t["content"], "--x", t["x"], "--y", t["y"],
          "--font-size", t.get("size", 7))
print("texts", len(spec.get("texts", [])))
