"""Thin wrapper around the easyeda CLI used by the redraw scripts."""
import json
import subprocess
import time

LIB = "0819f05c4eef4c71ace90d822a990e87"


RETRYABLE = ("--doc guard", "do not interleave", "no EasyEDA connector", "being verified", "create failed!")


def run(*args, doc=None, check=True, retries=12):
    """Run the CLI; refusals raised before any write (doc guard, busy window) are retried."""
    for attempt in range(retries):
        try:
            return _run(*args, doc=doc, check=check)
        except RuntimeError as e:
            if attempt == retries - 1 or not any(k in str(e) for k in RETRYABLE):
                raise
            time.sleep(5 + attempt * 2)


import os

# target project uuid: set EASYEDA_PROJECT so every call is routed to the right window
PROJECT = os.environ.get("EASYEDA_PROJECT", "")


def _run(*args, doc=None, check=True):
    # route by project uuid: other windows (web editors) may hold a same-named copy
    cmd = ["easyeda"] + (["--project", PROJECT] if PROJECT else [])
    if doc:
        cmd += ["--doc", doc]
    cmd += [str(a) for a in args]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = p.stdout
    # the CLI may prefix progress lines (e.g. "⏳ connector queue busy") before the JSON body
    start = out.find("\n{")
    if not out.lstrip().startswith("{") and start >= 0:
        out = out[start + 1:]
    try:
        d = json.loads(out)
    except Exception:
        raise RuntimeError(f"non-json from {' '.join(cmd)}: {p.stdout[:400]} {p.stderr[:400]}")
    if check and not d.get("ok"):
        raise RuntimeError(f"failed {' '.join(cmd)}: {json.dumps(d.get('error'), ensure_ascii=False)[:600]}")
    return d


def place(doc, uuid, x, y, designator=None, rotation=0, mirror=False):
    args = ["sch", "place", "--lib", LIB, "--uuid", uuid, "--x", x, "--y", y, "--rotation", rotation]
    if designator:
        args += ["--designator", designator]
    if mirror:
        args.append("--mirror")
    return run(*args, doc=doc)["result"]


def components(page):
    d = run("sch", "list", "--page", page, "--stay", "--include-pins", "--include-bbox")
    return d["result"]["components"]


def wire(doc, pts, net=None):
    args = ["sch", "wire", "--points", json.dumps(pts)]
    if net:
        args += ["--net", net]
    return run(*args, doc=doc)["result"]


def netflag(doc, kind, net, x, y, rotation=0):
    return run("sch", "netflag", "--kind", kind, "--net", net, "--x", x, "--y", y,
               "--rotation", rotation, doc=doc)["result"]
