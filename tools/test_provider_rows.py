#!/usr/bin/env python3
"""Seam test for the built matrix rows (site/build.py, column "Where it runs").

Usage:
    python3 tools/test_provider_rows.py

Builds the site from data/projects into a scratch directory. For each matrix row it reads data-fprov, data-fprovlvl,
data-fprovpair and data-fprov-via from the built HTML and compares them with d08.normalized.providers in the profile.
Only the levels at which an entry runs (catalogue, project image, bring your image) may appear in the pairs. Then it runs the
real matches() from pulse.js on the real rows. For every profile with provider data it also reads the data sheet lines and checks
that each provider's line shows the label of its level. The labels are written out here on purpose: a test that read them from
build.py would pass when two of them are swapped. Exit code 0 means every check passed.
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
LEVEL_LABELS = {"provider-catalogue": "Official image in the provider's catalogue",
                "project-image": "Project image for this provider",
                "bring-your-image": "Bring your own image",
                "config-source-only": "Config source only",
                "none": "Documented as not supported",
                "unknown": "Not documented",
                "not-applicable": "Does not apply"}
NAMES = {"aws": "AWS", "azure": "Azure", "gcp": "GCP", "openstack": "OpenStack", "vsphere": "VMware vSphere",
         "proxmox": "Proxmox VE", "kvm-libvirt": "KVM/libvirt", "hyper-v": "Hyper-V", "nutanix": "Nutanix",
         "hetzner": "Hetzner", "digitalocean": "DigitalOcean", "vultr": "Vultr", "akamai": "Akamai (Linode)",
         "ovhcloud": "OVHcloud", "scaleway": "Scaleway", "bare-metal": "Bare metal", "other": "Other cloud"}


def expected(profile):
    items = (profile["dimensions"]["d08_hardware_platform"].get("normalized") or {}).get("providers") or []
    runs = [x for x in items if x["level"] in REACHES]
    return {
        "fprov": sorted(x["provider"] for x in runs),
        "fprovpair": sorted("%s:%s" % (x["provider"], x["level"]) for x in runs),
        "fprovlvl": sorted({x["level"] for x in runs}),
        "fprov-via": sorted(x["provider"] for x in items if x["level"] == "config-source-only"),
    }


def providers_of(profile):
    return (profile["dimensions"]["d08_hardware_platform"].get("normalized") or {}).get("providers") or []


def sheet_lines(index, pid):
    """(provider name, level label) for each line of the entry's Where it runs data sheet row."""
    row = re.search(r'<div class="ds-row" id="ds-%s-prov".*?</dd></div>' % re.escape(pid), index, re.S)
    if not row:
        return []
    found = re.findall(r'<li><span class="v-tag">([^<]*)</span> <span class="v[^"]*">([^<]*)</span>', row.group(0))
    return sorted((html.unescape(n), html.unescape(label)) for n, label in found)


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
    sheets = 0
    for pid, profile in profiles.items():
        items = providers_of(profile)
        if not items:
            continue
        sheets += 1
        want = sorted((x["name"] if x["provider"] == "other" and x.get("name") else NAMES[x["provider"]],
                       LEVEL_LABELS[x["level"]]) for x in items)
        have = sheet_lines(index, pid)
        check(have == want, "%s: the data sheet lines differ from the profile: only on the sheet %s, only in the profile %s"
              % (pid, sorted(set(have) - set(want)), sorted(set(want) - set(have))))
    check(sheets >= 5, "only %d data sheets have provider data" % sheets)

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
    print("%d rows checked against their profiles, %d data sheets, 2 filter cases on the real rows" % (checked, sheets))
    print("%s" % ("all passed" if not failed else "%d check(s) failed" % failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
