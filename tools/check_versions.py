#!/usr/bin/env python3
"""Check each profile's observed version against the project's latest release.

Usage: check_versions.py <projects-dir> [--out versions-check.json]

Reads version_observed.version from every profile, asks each project's own
release channel for its latest version, and writes one JSON record per entry:
observed, latest, newer (true/false/null), the method used and the check time.

It only detects. It never edits a profile. A newer release is a prompt to
re-validate that profile against the new version (see docs/REFRESH.md), not a
change to the data. The site reads the JSON to show "Newer release" badges.

Entries with no machine-readable release channel are reported as "manual".
"""
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import urllib.request

import yaml

UA = {"User-Agent": "cloud-native-os-pulse-version-check"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def gh_latest(repo):
    """Prefer the authenticated gh CLI; the anonymous API allows only 60 calls an hour."""
    try:
        tag = subprocess.run(["gh", "api", "repos/%s/releases/latest" % repo, "--jq", ".tag_name"],
                             capture_output=True, text=True, check=True, timeout=60).stdout.strip()
    except Exception:
        tag = json.loads(fetch("https://api.github.com/repos/%s/releases/latest" % repo))["tag_name"]
    return tag, "GitHub latest non-prerelease release of %s" % repo


def flatcar():
    txt = fetch("https://stable.release.flatcar-linux.net/amd64-usr/current/version.txt")
    return re.search(r"FLATCAR_VERSION=(\S+)", txt).group(1), "stable channel version.txt"


def fcos():
    data = json.loads(fetch("https://builds.coreos.fedoraproject.org/streams/stable.json"))
    return data["architectures"]["x86_64"]["artifacts"]["metal"]["release"], "stable stream metadata"


def microos():
    txt = fetch("https://download.opensuse.org/tumbleweed/appliances/")
    snaps = re.findall(r"openSUSE-MicroOS\.x86_64-[\d.]+-[^\"<]*?Snapshot(\d{8})", txt)
    if not snaps:
        raise ValueError("no MicroOS snapshot found in the appliance directory")
    return "Snapshot" + max(snaps), "newest snapshot in the published appliance directory"


CHECKS = {
    "talos": lambda: gh_latest("siderolabs/talos"),
    "bottlerocket": lambda: gh_latest("bottlerocket-os/bottlerocket"),
    "kairos": lambda: gh_latest("kairos-io/kairos"),
    "hadron": lambda: gh_latest("kairos-io/hadron"),
    "bootc": lambda: gh_latest("bootc-dev/bootc"),
    "eve-os": lambda: gh_latest("lf-edge/eve"),
    "unikraft": lambda: gh_latest("unikraft/unikraft"),
    "flatcar": flatcar,
    "fedora-coreos": fcos,
    "microos": microos,
}


def comparable(observed, latest):
    """True when the observed string already names the latest version.

    Compares the version numbers only, so tag styles like v0.21.0 and
    RELEASE-0.21.0 match.
    """
    num = re.compile(r"\d+(?:\.\d+)+|\d{8}")
    lv = num.findall(latest)
    if not lv:
        return latest.lower().lstrip("v") in observed.lower()
    return lv[0] in num.findall(observed)


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    src = args[0]
    out = args[args.index("--out") + 1] if "--out" in args else None
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    result = {}
    for f in sorted(glob.glob(os.path.join(src, "*.yaml"))):
        p = yaml.safe_load(open(f))
        pid = p["id"]
        observed = str((p.get("version_observed") or {}).get("version", ""))
        rec = {"observed": observed, "checked_at": now}
        if pid not in CHECKS:
            rec.update(latest=None, newer=None, method="manual: no machine-readable release channel")
        else:
            try:
                latest, method = CHECKS[pid]()
                rec.update(latest=latest, newer=not comparable(observed, latest), method=method)
            except Exception as e:  # report, do not guess
                rec.update(latest=None, newer=None, method="check failed: %s" % e)
        result[pid] = rec
        flag = {True: "NEWER", False: "current", None: "manual"}[rec["newer"]]
        print("%-22s %-8s observed %-40s latest %s" % (pid, flag, observed[:40], rec["latest"]))
    if out:
        json.dump(result, open(out, "w"), indent=2, sort_keys=True)
        print("wrote", out)


if __name__ == "__main__":
    main()
