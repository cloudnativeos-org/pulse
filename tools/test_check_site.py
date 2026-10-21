#!/usr/bin/env python3
"""Seam test for the provider checks in site/check_site.py.

Usage:
    python3 tools/test_check_site.py

Builds the site into a scratch directory, then runs check_site.py on the good build and on two broken copies: a
Where it runs row in the data sheet with its citations removed, and a data sheet with no Where it runs row. The good build must pass. Each broken copy must fail with the message that names the rule.
Exit code 0 means every case behaved as expected.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROW = re.compile(r'(<div class="ds-row" id="ds-flatcar-prov".*?</dd></div>)', re.S)


def run_check(site: pathlib.Path):
    r = subprocess.run([sys.executable, str(ROOT / "site" / "check_site.py"), str(site)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def strip_cites(row):
    return re.sub(r'<[^<>]*class="cite"[^<>]*>.*?</(?:a|span|sup)>', "", row, flags=re.S)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "out"
        r = subprocess.run([sys.executable, str(ROOT / "site" / "build.py"), str(ROOT / "data" / "projects"), str(out)],
                           capture_output=True, text=True)
        if r.returncode:
            print("FAIL  site build\n" + r.stderr[-800:])
            return 1
        site = out / "site"
        index = (site / "index.html").read_text()
        row = PROW.search(index)
        if not row:
            print("FAIL  no Where it runs row for flatcar in the data sheet")
            return 1
        cases = [
            ("good build passes", None, 0, "site check ok"),
            ("sheet row without citations fails", index.replace(row.group(1), strip_cites(row.group(1))), 1, "lists a provider with no source"),
            ("sheet without the row fails", index.replace(row.group(1), ""), 1, "no Where it runs row in its data sheet"),
        ]
        failed = 0
        for name, broken, code, text in cases:
            work = pathlib.Path(tmp) / ("case-" + str(abs(hash(name))))
            work.mkdir()
            for f in site.iterdir():
                if f.is_file():
                    (work / f.name).write_bytes(f.read_bytes())
            if broken is not None:
                (work / "index.html").write_text(broken)
            got, output = run_check(work)
            ok = got == code and text in output
            print(f"{'PASS' if ok else 'FAIL'}  {name}")
            if not ok:
                failed += 1
                print(f"      expected exit {code} and {text!r}, got exit {got}\n      {output.strip()[-300:]}")
    print(f"\n{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
