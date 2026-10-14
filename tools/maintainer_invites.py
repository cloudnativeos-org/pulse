#!/usr/bin/env python3
"""Fill docs/maintainer-invite.md for each project, ready to send.

Usage: maintainer_invites.py [--out DIR] [--name ID=NAME ...] [--max N] [project ids ...]

Writes one text file per project to DIR (default site/out/invites, which is not
committed), with the project's own open questions. Pass --name to greet a person
by name; otherwise the greeting says "Hi,". With no project ids, every profile
gets one.
"""
import argparse
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW_URL = "https://cloudnativeos.org"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--out", default=os.path.join(ROOT, "site", "out", "invites"))
    ap.add_argument("--name", action="append", default=[], help="ID=NAME, the person to greet")
    ap.add_argument("--max", type=int, default=3, help="open questions to list; the rest are referred to the profile")
    a = ap.parse_args()

    names = dict(x.split("=", 1) for x in a.name)
    template = open(os.path.join(ROOT, "docs", "maintainer-invite.md")).read()
    pdir = os.path.join(ROOT, "data", "projects")
    ids = a.ids or sorted(f[:-5] for f in os.listdir(pdir) if f.endswith(".yaml"))
    os.makedirs(a.out, exist_ok=True)

    for pid in ids:
        p = yaml.safe_load(open(os.path.join(pdir, pid + ".yaml")))
        qs = [str(q) for q in (p.get("open_questions") or [])]
        shown = qs[: a.max]
        lines = ["%d. %s" % (i, q) for i, q in enumerate(shown, 1)]
        if len(qs) > len(shown):
            lines.append("... and %d more." % (len(qs) - len(shown)))
        if not lines:
            lines = ["(None recorded. A look at the data sheet and the matrix row is still very welcome.)"]
        text = (template
                .replace("{project}", p["name"])
                .replace("{preview_url}", PREVIEW_URL)
                .replace("{open_questions}", "\n".join(lines)))
        if pid in ("kairos", "hadron"):
            # The author maintains these two, so another Kairos maintainer reviews them.
            text = text.replace(
                "Up front: I am one of the maintainers of Kairos and Hadron, two of the other entries, and I work for Spectro Cloud. "
                "That is why every project gets this same request, Kairos and Hadron included.",
                "As you know, I am one of the Kairos and Hadron maintainers too, and I work for Spectro Cloud, "
                "so I am asking you to review them instead of doing it myself. Every project gets this same request.")
        who = names.get(pid)
        text = text.replace("Hi {name},", "Hi %s," % who if who else "Hi,")
        path = os.path.join(a.out, pid + ".txt")
        open(path, "w").write(text)
        print(path)


if __name__ == "__main__":
    sys.exit(main())
