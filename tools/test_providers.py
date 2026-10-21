#!/usr/bin/env python3
"""Seam test for d08.normalized.providers (the validator contract).

Usage:
    python3 tools/test_providers.py

Copies one real profile into a scratch directory, adds provider items, and runs the validator on it. A good item must pass.
Each bad item must fail with the message that names the rule. Exit code 0 means every case behaved as expected.
"""

from __future__ import annotations

import copy
import pathlib
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "tools" / "validate_profiles.py"
BASE = ROOT / "data" / "projects" / "flatcar.yaml"

SOURCE = {
    "url": "https://www.flatcar.org/docs/latest/installing/cloud/openstack/",
    "type": "official-docs",
    "retrieved": "2026-10-21",
    "quote": "Flatcar is supported on OpenStack.",
}


def good(**over):
    item = {"provider": "openstack", "level": "project-image", "tier": "project",
            "config": {"tool": "Ignition", "channel": "userdata"},
            "how": "Import the published image.", "evidence": "DOCUMENTED", "sources": [copy.deepcopy(SOURCE)]}
    item.update(over)
    return item


def run(providers):
    profile = yaml.safe_load(BASE.read_text())
    profile["dimensions"]["d08_hardware_platform"].setdefault("normalized", {})["providers"] = providers
    with tempfile.TemporaryDirectory() as tmp:
        (pathlib.Path(tmp) / "flatcar.yaml").write_text(yaml.safe_dump(profile, sort_keys=False))
        proc = subprocess.run([sys.executable, str(VALIDATOR), tmp], capture_output=True, text=True)
    return proc.returncode, proc.stdout


def without(item, key):
    item = copy.deepcopy(item)
    item.pop(key)
    return item


CASES = [
    # name, providers, expected exit code, text that must appear in the output
    ("good item passes", [good()], 0, "0 error(s)"),
    ("unknown needs no source", [{"provider": "hetzner", "level": "unknown", "evidence": "UNKNOWN", "searched": "docs"}], 0, "0 error(s)"),
    ("project-image without a source fails", [without(good(), "sources")], 1, "has no sources"),
    ("source without a quote fails", [good(sources=[without(SOURCE, "quote")])], 1, "needs a verbatim quote"),
    ("tool not in d09 fails", [good(config={"tool": "NoSuchTool", "channel": "userdata"})], 1, "is not a name in d09 config_tools"),
    ("provider outside the list fails", [good(provider="equinix")], 1, "provider must be one of"),
    ("none without DOCUMENTED fails", [good(level="none", evidence="INFERRED", inferred_from="x")], 1, "needs evidence DOCUMENTED"),
    ("duplicate provider fails", [good(), good()], 1, "appears twice"),
    ("other without a name fails", [good(provider="other")], 1, "needs a 'name'"),
    ("level outside the list fails", [good(level="works")], 1, "level must be one of"),
    ("channel outside the list fails", [good(config={"tool": "Ignition", "channel": "magic"})], 1, "config.channel must be one of"),
]


def main() -> int:
    failed = 0
    for name, providers, code, text in CASES:
        got, out = run(providers)
        ok = got == code and text in out
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failed += 1
            print(f"      expected exit {code} and {text!r}, got exit {got}")
            print("      " + "\n      ".join(out.strip().splitlines()[-6:]))
    print(f"\n{len(CASES) - failed}/{len(CASES)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
