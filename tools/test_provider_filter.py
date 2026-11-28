#!/usr/bin/env python3
"""Seam test for the matrix provider and level filters (site/src/pulse.js).

Usage:
    python3 tools/test_provider_filter.py

Takes the real `matches` function out of pulse.js and runs it in node on fake rows. A provider and a level selected together
must match only a row that reaches that provider at that level. Exit code 0 means every case behaved as expected.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
JS = (ROOT / "site" / "src" / "pulse.js").read_text()

# Two rows. "a" has a catalogue image on azure and a project image on openstack. "b" has a bring-your-image on openstack.
ROWS = {
    "a": {"fprov": "azure openstack", "fprovlvl": "project-image provider-catalogue", "fprovpair": "azure:provider-catalogue openstack:project-image"},
    "b": {"fprov": "openstack", "fprovlvl": "bring-your-image", "fprovpair": "openstack:bring-your-image"},
    "via": {"fprov": "none", "fprovlvl": "none", "fprovpair": "none", "fprovVia": "openstack"},
}

CASES = [
    ("provider alone", {"prov": ["openstack"]}, ["a", "b", "via"]),
    ("level alone", {"provlvl": ["provider-catalogue"]}, ["a"]),
    ("openstack with catalogue: no row has that pair", {"prov": ["openstack"], "provlvl": ["provider-catalogue"]}, []),
    ("azure with catalogue", {"prov": ["azure"], "provlvl": ["provider-catalogue"]}, ["a"]),
    ("openstack with project image", {"prov": ["openstack"], "provlvl": ["project-image"]}, ["a"]),
    ("either provider with bring your image", {"prov": ["azure", "openstack"], "provlvl": ["bring-your-image"]}, ["b"]),
]


def main() -> int:
    m = re.search(r"function matches\(row, f\) \{.*?\n    \}\n", JS, re.S)
    v = re.search(r"function viaOf\(row, k\) \{.*?\}\n", JS)
    if not m or not v:
        print("FAIL  could not find matches() and viaOf() in site/src/pulse.js")
        return 1
    script = v.group(0) + m.group(0) + """
var rows = %s, cases = %s, out = [];
cases.forEach(function (c) {
  out.push(Object.keys(rows).filter(function (id) { return matches({dataset: rows[id]}, c[1]); }));
});
console.log(JSON.stringify(out));
""" % (json.dumps(ROWS), json.dumps([[n, f] for n, f, _ in CASES]))
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if r.returncode:
        print("FAIL  node error\n" + r.stderr)
        return 1
    got = json.loads(r.stdout)
    failed = 0
    for (name, _, want), have in zip(CASES, got):
        ok = sorted(have) == sorted(want)
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failed += 1
            print(f"      expected {want}, got {have}")
    print(f"\n{len(CASES) - failed}/{len(CASES)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
