"""Render each design-system preview with the tokens and bundle CSS, in light and dark, for local checks."""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build
tok = json.load(open("tokens.json"))
tcss = build.tokens_css(tok)
css = open("src/pulse.css").read()
os.makedirs("out/harness", exist_ok=True)
idx = []
for p in sorted(glob.glob("out/ds/project/components/*/preview.html")):
    n = p.split("/")[-2]
    body = open(p).read()
    for theme in ("light", "dark"):
        open(f"out/harness/{n}-{theme}.html", "w").write(
            f'<!doctype html><html data-theme="{theme}"><head><meta charset=utf-8><style>{tcss}</style><style>{css}</style></head><body>{body}</body></html>')
        idx.append(f'<li><a href="{n}-{theme}.html">{n} {theme}</a></li>')
open("out/harness/index.html", "w").write("<ul>%s</ul>" % "".join(idx))
