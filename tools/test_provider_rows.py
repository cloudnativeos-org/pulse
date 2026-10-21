#!/usr/bin/env python3
"""Seam test for the built matrix rows (site/build.py, column "Where it runs").

Usage:
    python3 tools/test_provider_rows.py

Builds the site from data/projects into a scratch directory. For each matrix row it reads data-fprov, data-fprovlvl,
data-fprovpair and data-fprov-via from the built HTML and compares them with d08.normalized.providers in the profile.
Only the levels at which an entry runs (catalogue, project image, bring your image) may appear in the pairs. Then it runs the
real matches() from pulse.js on the real rows. Exit code 0 means every check passed.
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
REACHES = ("provider-catalogue", "project-image", "bring-your-image")
JS = (ROOT / "site" / "src" / "pulse.js").read_text()


def expected(profile):
    items = (profile["dimensions"]["d08_hardware_platform"].get("normalized") or {}).get("providers") or []
    runs = [x for x in items if x["level"] in REACHES]
    return {
        "fprov": sorted(x["provider"] for x in runs),
        "fprovpair": sorted("%s:%s" % (x["provider"], x["level"]) for x in runs),
        "fprovlvl": sorted({x["level"] for x in runs}),
        "fprov-via": sorted(x["provider"] for x in items if x["level"] == "config-source-only"),
    }


def tokens(value):
    return [] if value in (None, "none", "nc") else sorted(value.split())


def built_rows(index):
    rows = {}
    for tag in re.findall(r"<tr data-id=\"[^\"]+\"[^>]*>", index):
        rid = re.search(r'data-id="([^"]+)"', tag).group(1)
        rows[rid] = {k: html.unescape(v) for k, v in re.findall(r'data-(fprov(?:-via|lvl|pair)?)="([^"]*)"', tag)}
    return rows


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(ROOT / "site" / "build.py"), str(ROOT / "data" / "projects"), tmp],
                           capture_output=True, text=True)
        if r.returncode:
            print("FAIL  site build\n" + r.stderr[-800:])
            return 1
        index = (pathlib.Path(tmp) / "site" / "index.html").read_text()
    rows = built_rows(index)
    profiles = {}
    for f in sorted((ROOT / "data" / "projects").glob("*.yaml")):
        d = yaml.safe_load(f.read_text())
        profiles[d["id"]] = d
    failed = 0
    checked = 0

    def check(ok, msg):
        nonlocal failed
        if not ok:
            failed += 1
            print("FAIL  " + msg)

    for rid, attrs in rows.items():
        if rid not in profiles:
            continue
        want = expected(profiles[rid])
        checked += 1
        for key in ("fprov", "fprovpair", "fprovlvl", "fprov-via"):
            have = tokens(attrs.get(key))
            check(have == want[key], "%s: data-%s is %s, the profile says %s" % (rid, key, have, want[key]))
        check(len(tokens(attrs.get("fprov"))) == len(tokens(attrs.get("fprovpair"))), "%s: data-fprov and data-fprovpair differ in length" % rid)
        for pair in tokens(attrs.get("fprovpair")):
            check(pair.split(":", 1)[1] in REACHES, "%s: pair %s is not a level at which the entry runs" % (rid, pair))
    check(checked >= 4, "only %d matrix rows matched a profile" % checked)

    m = re.search(r"function matches\(row, f\) \{.*?\n    \}\n", JS, re.S)
    v = re.search(r"function viaOf\(row, k\) \{.*?\}\n", JS)
    if not m or not v:
        print("FAIL  could not find matches() and viaOf() in site/src/pulse.js")
        return 1
    filters = [{"prov": ["openstack"], "provlvl": ["provider-catalogue"]}, {"prov": ["openstack"], "provlvl": ["project-image"]}]
    dataset = {rid: {k.replace("-via", "Via"): val for k, val in a.items()} for rid, a in rows.items()}
    script = v.group(0) + m.group(0) + """
var rows = %s, fs = %s;
console.log(JSON.stringify(fs.map(function (f) { return Object.keys(rows).filter(function (id) { return matches({dataset: rows[id]}, f); }); })));
""" % (json.dumps(dataset), json.dumps(filters))
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if r.returncode:
        print("FAIL  node error\n" + r.stderr)
        return 1
    got = json.loads(r.stdout)
    for f, have in zip(filters, got):
        want = sorted(rid for rid in rows if rid in profiles and
                      any(x["provider"] == "openstack" and x["level"] == f["provlvl"][0]
                          for x in (profiles[rid]["dimensions"]["d08_hardware_platform"].get("normalized") or {}).get("providers") or []))
        check(sorted(have) == want, "OpenStack + %s on the built rows matches %s, the profiles say %s" % (f["provlvl"][0], sorted(have), want))
    print("%d rows checked against their profiles, 2 filter cases on the real rows" % checked)
    print("%s" % ("all passed" if not failed else "%d check(s) failed" % failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
