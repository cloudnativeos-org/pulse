#!/usr/bin/env python3
"""Check the built site for the layout and navigation rules we decided on.

Usage: check_site.py [DIR | INDEX.html GUIDE.html]     (default: site/out/site)

The site is two pages: index.html (the matrix page) and guide.html (the guide).

Fails (exit 1) if:
- a page lacks the two tabs, Matrix and Guide, or does not mark its own tab with aria-current="page";
- the preview build lacks noindex or the preview banner on either page (a preview is detected on either page);
- the matrix page holds a guide section, or the guide holds the matrix or a data sheet;
- a link does not resolve: #id must exist on its own page, file#id must exist on the page it names;
- a link to a section that lives on the other page has no file name;
- the old-link redirect list on the matrix page names an id that guide.html does not have;
- the guide's contents repeat an entry, link to a missing anchor, miss a section, or break the page order;
- the contents toggle is not the edge tab;
- a page contains an em dash;
- a matrix header carries more than its title: a dimension code (d01 and so on), "New field", or a note;
- a matrix cell carries a sentence (a v-detail line) instead of tags; the full text belongs in the data sheet;
- a header's "?" link does not point at an entry of "What the columns mean" on the guide, or a column has no
  definition for the modal;
- the matrix still carries the old per-row Details toggle, or a separate Data sheet link;
- a matrix entry has no data sheet in index.html, or its name does not link to it;
- a data sheet lacks a row for a matrix column;
- a data sheet lacks the Mounts row, or it is not right after the Update unit row, or it lacks one of its four
  lines (read-only, writable and reset on reboot, writable and persistent, configurable), or one of them is empty;
- a "Via your base distribution" tag in a matrix row has no matching data-f<column>-via attribute on that row, or
  the old names ("From base distro", "From your base distribution", "Released architectures") are still on a page;
- a note tag in a cell links to a data sheet row that does not exist;
- the data sheets do not share one row layout: every row is id="ds-<project>-<key>" with data-col="<key>", and the
  keys are the same, in the same order, on every sheet, so the side-by-side view can align them;
- the matrix page still carries the old phone compare view (mx-cmp, mx-view);
- the matrix default columns are not five, or name a column that does not exist, or are not in matrix order;
- the Columns picker lacks "Show all columns" or "Default columns";
- a data sheet uses "buys" or "costs" as a section label;
- a source number cited on a page is missing from that page's source list;
- a matrix cell carries an evidence badge or a citation (the matrix is an overview; the evidence lives in the data sheet),
  or a data sheet row lacks its evidence badge (the Entry row and a Not collected row are the only exceptions);
- the matrix legend still lists the evidence labels instead of pointing at the data sheet;
- a "Not found in the documentation we read." is not followed by the link to the correction section (guide.html#fix-h).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def ids_of(page):
    return set(re.findall(r'\sid="([^"]+)"', page))


def hrefs_of(page):
    return re.findall(r'href=(?:"([^"]*)"|\'([^\']*)\')', page)


def main():
    args = sys.argv[1:]
    if len(args) == 2:
        ipath, gpath = args
    else:
        d = args[0] if args else os.path.join(HERE, "out", "site")
        ipath, gpath = os.path.join(d, "index.html"), os.path.join(d, "guide.html")
    raw = {"index.html": open(ipath).read(), "guide.html": open(gpath).read()}
    # Markup only: the script and style text builds links as strings, which are not links in the page.
    markup = lambda t: re.sub(r"<script(?![^>]*application/json)[^>]*>.*?</script>|<style>.*?</style>", "", t, flags=re.S)
    pages = {n: markup(t) for n, t in raw.items()}
    index, guide = pages["index.html"], pages["guide.html"]
    ids = {name: ids_of(p) for name, p in pages.items()}
    errors = []

    # ---- both pages
    preview = any("noindex" in p or "Preview, not released" in p for p in pages.values())
    for name, p in pages.items():
        tab = re.search(r'<nav class="tabs[^"]*" aria-label="Pages">(.*?)</nav>', p, re.S)
        if not tab:
            errors.append("%s has no tab bar" % name)
        else:
            links = re.findall(r'<a class="tab" href="([^"]+)"( aria-current="page")?>([^<]+)</a>', tab.group(1))
            if [(h, t) for h, _, t in links] != [("index.html", "Matrix"), ("guide.html", "Guide")]:
                errors.append("%s: the tabs are not Matrix then Guide: %s" % (name, links))
            cur = [h for h, c, _ in links if c]
            if cur != [name]:
                errors.append("%s: the current tab is %s, not %s" % (name, cur or "unmarked", name))
        if "—" in p:
            errors.append("em dash found on %s" % name)
        for old_name in ("From base distro", "From your base distribution", "Released architectures"):
            if old_name in p:
                errors.append("%s still says %r" % (name, old_name))
        if preview:
            if '<meta name="robots" content="noindex, nofollow">' not in p:
                errors.append("%s is a preview build but carries no noindex" % name)
            if "Preview, not released" not in p or 'class="banner"' not in p:
                errors.append("%s is a preview build but carries no preview banner" % name)
        if "html.toc-open .sec-matrix .mx-wrap" not in raw[name]:
            errors.append("%s: the rule that keeps the matrix clear of the open contents panel is missing" % name)

        # links: every one resolves on its page or on the page it names
        for a, b in hrefs_of(p):
            h = a or b
            if h.startswith("#"):
                base = h[1:].split("?", 1)[0]
                if not base or base == "top":
                    continue
                if base not in ids[name]:
                    other = [o for o in pages if o != name][0]
                    where = " (it is on %s: the link needs the file name)" % other if base in ids[other] else ""
                    errors.append("%s: link to #%s does not resolve%s" % (name, base, where))
            else:
                m = re.match(r"(index\.html|guide\.html)#(.*)$", h)
                if m:
                    base = m.group(2).split("?", 1)[0]
                    if base and base not in ids[m.group(1)]:
                        errors.append("%s: link to %s#%s does not resolve" % (name, m.group(1), base))
        # citations: each [n] needs its entry in this page's list
        for n in sorted({int(x) for x in re.findall(r'href="#src-(\d+)"', p)}):
            if "src-%d" % n not in ids[name]:
                errors.append("%s cites source %d but does not list it" % (name, n))
        if re.findall(r'<li id="(src-\d+)"', p) != sorted(set(re.findall(r'<li id="(src-\d+)"', p)), key=lambda s: int(s[4:])):
            errors.append("%s: the sources are repeated or out of order" % name)

    # ---- "Not found" always invites a correction
    for name, p in pages.items():
        for m in re.finditer(r"Not found in the documentation we read\.", p):
            if not re.match(r' <a class="nf-ask" href="guide\.html#fix-h">Know the answer\?</a>', p[m.end():]):
                errors.append("%s: a 'Not found in the documentation we read.' is not followed by the correction link" % name)
    if "fix-h" not in ids["guide.html"]:
        errors.append("the guide has no correction section (fix-h) for the Not found link")
    if "for the evidence label and the sources behind each one." not in index:
        errors.append("the matrix legend lacks the line that points at the data sheet for the evidence label")
    if re.search(r'<p class="mx-read-k">Evidence</p>', index):
        errors.append("the matrix legend still lists the evidence labels")

    # ---- structure of each page
    isec = re.findall(r'<section class="sec[^"]*" aria-labelledby="(h-[a-z]+)"', index)
    if isec != ["h-matrix", "h-cards", "h-src"]:
        errors.append("the matrix page holds the sections %s, not h-matrix, h-cards, h-src" % isec)
    if re.search(r'<table class="mx">', guide) or 'class="tc"' in guide or 'class="cards"' in guide:
        errors.append("the guide holds the matrix or a data sheet")
    if 'id="toc"' in index:
        errors.append("the matrix page has a contents panel; with two sections it should not")

    # ---- the guide's contents
    nav = re.search(r'<nav id="toc".*?</nav>', guide, re.S)
    if not nav:
        errors.append("no contents panel on the guide")
        nav_html = ""
    else:
        nav_html = nav.group(0)
    toc = re.findall(r'href="#([^"]+)"', nav_html)
    dupes = sorted({h for h in toc if toc.count(h) > 1})
    if dupes:
        errors.append("contents repeat an entry: %s" % ", ".join(dupes))
    dead = [h for h in toc if h not in ids["guide.html"]]
    if dead:
        errors.append("contents link to missing anchors: %s" % ", ".join(dead))
    gsec = re.findall(r'<section class="sec[^"]*" aria-labelledby="(h-[a-z]+)"', guide)
    missing = [s for s in gsec if s not in toc]
    if missing:
        errors.append("sections missing from the contents: %s" % ", ".join(missing))
    order = [h for h in toc if h in gsec]
    if order != [s for s in gsec if s in order]:
        errors.append("contents order does not follow the page order")
    if 'class="toc-toggle' not in guide or "Show contents" not in guide:
        errors.append("the contents toggle is not the edge tab")
    want = ["h-what", "h-myths", "h-start", "h-review", "h-pair", "h-origins", "h-alt", "h-worth", "h-excluded", "h-who", "h-made", "h-why", "h-wishes", "h-gloss", "h-dims", "h-src"]
    if gsec != want:
        errors.append("the guide's sections are %s, not %s" % (gsec, want))

    # ---- old links: the redirect list on the matrix page
    m = re.search(r'<script id="old-hash">.*?var g="([^"]*)"', raw["index.html"], re.S)
    if not m:
        errors.append("the matrix page has no old-link redirect script")
        moved = []
    else:
        moved = m.group(1).split()
        for i in moved:
            if i not in ids["guide.html"]:
                errors.append("the redirect list names #%s, which guide.html does not have" % i)
            if i in ids["index.html"]:
                errors.append("the redirect list names #%s, which also exists on the matrix page" % i)
        for need in ("h-pair", "h-what", "h-gloss", "h-made", "fix-h", "w-criteria", "col-update"):
            if need not in moved:
                errors.append("the redirect list lacks #%s" % need)

    # ---- the matrix page
    fgs = re.findall(r'<fieldset class="mx-fg"[^>]*>.*?</fieldset>', index, re.S)
    if not fgs:
        errors.append("no matrix filters found")
    for fg in fgs:
        title = re.search(r"<legend>(.*?)</legend>", fg, re.S)
        expl = re.search(r'<p class="mx-fd">(.*?)</p>', fg, re.S)
        name = title.group(1) if title else "(no title)"
        if not title or not title.group(1).strip():
            errors.append("a matrix filter has no title")
        if not expl or len(re.sub(r"<[^>]+>|\?", "", expl.group(1)).strip()) < 15:
            errors.append("matrix filter has no explanation: %s" % name)
        if 'class="mx-fo"' not in fg or "<input" not in fg:
            errors.append("matrix filter has no options row: %s" % name)

    entries, cols = [], []
    table = re.search(r'<table class="mx">.*?</table>', index, re.S)
    if not table:
        errors.append("no matrix table found")
    else:
        table = table.group(0)
        thead = re.search(r"<thead>.*?</thead>", table, re.S).group(0)
        for th in re.findall(r"<th[^>]*>.*?</th>", thead, re.S):
            text = re.sub(r"<[^>]+>", " ", th)
            if re.search(r"\bd\d\d\b", text) or re.search(r"\bd\d\d\b", th):
                errors.append("a matrix header carries a dimension code: %s" % " ".join(text.split()))
            if "New field" in th or "th-note" in th or "Axis B" in th:
                errors.append("a matrix header carries more than its title: %s" % " ".join(text.split()))
        cols = re.findall(r'<th scope="col" data-col="([^"]+)"', thead)
        qs = re.findall(r'class="mx-q" href="([^"]+)"', thead)
        if len(qs) != len(cols):
            errors.append("%d columns but %d ? links in the header" % (len(cols), len(qs)))
        for q in qs:
            mm = re.match(r"guide\.html#(col-[a-z0-9]+)$", q)
            if not mm or mm.group(1) not in ids["guide.html"]:
                errors.append("a header's ? link does not point at the guide's column definition: %s" % q)
        try:
            defs = json.loads(re.search(r'<script type="application/json" id="col-defs">(.*?)</script>', index, re.S).group(1).replace("<\\/", "</"))
        except Exception:
            defs = {}
            errors.append("the matrix page has no readable column definitions for the modal")
        for c in cols:
            if c not in defs or not defs[c].get("title") or not defs[c].get("html"):
                errors.append("the column %s has no definition for the modal" % c)
        if "mx-det-btn" in table or 'class="mx-details"' in table or "mx-sheet" in table:
            errors.append("the matrix still carries the old Details toggle, details rows or a separate Data sheet link")
        entries = re.findall(r'<tr data-id="([^"]+)"[^>]*>(.*?)</tr>', table, re.S)
        sheets = dict(re.findall(r'<article class="tc" aria-labelledby="tc-([a-z0-9-]+)">(.*?)</article>', index, re.S))
        for pid, row in entries:
            if re.search(r'class="ev ev-|class="cite"', row):
                errors.append("a matrix cell in the %s row carries an evidence badge or a citation; they belong in the data sheet" % pid)
            if "v-detail" in row:
                errors.append("a matrix cell in the %s row carries a sentence (v-detail); move it to the data sheet" % pid)
            mm = re.search(r'<a class="proj-open" href="#([^"]+)"', row)
            if not mm:
                errors.append("the %s row: the entry name does not link to its data sheet" % pid)
            elif mm.group(1) != "tc-" + pid or mm.group(1) not in ids["index.html"]:
                errors.append("the %s name link does not resolve: #%s" % (pid, mm.group(1)))
            for note in re.findall(r'<a class="mx-note" href="#([^"]+)"', row):
                if note not in ids["index.html"]:
                    errors.append("a note tag in the %s row links to a missing data sheet row: #%s" % (pid, note))
            sheet = sheets.get(pid)
            if sheet is None:
                errors.append("the matrix entry %s has no data sheet in index.html" % pid)
                continue
            for rid, body in re.findall(r'<div class="ds-row" id="(ds-[^"]+)" data-col="[^"]+"><dt>.*?</dt><dd>(.*?)</dd></div>', sheet, re.S):
                if 'class="ev ' not in body and "Not collected" not in body and not rid.endswith("-project"):
                    errors.append("the data sheet row %s has no evidence badge" % rid)
            missing_rows = [c for c in cols if 'id="ds-%s-%s"' % (pid, c) not in sheet]
            if missing_rows:
                errors.append("the %s data sheet has no row for: %s" % (pid, ", ".join(missing_rows)))
            # the Mounts row: right after Update unit, with its four lines
            order_ids = re.findall(r'<div class="ds-row" id="ds-%s-([a-z0-9]+)"' % re.escape(pid), sheet)
            if "mounts" not in order_ids:
                errors.append("the %s data sheet has no Mounts row" % pid)
            else:
                if "update" in order_ids and order_ids.index("mounts") != order_ids.index("update") + 1:
                    errors.append("the %s Mounts row is not right after the Update unit row" % pid)
                mrow = re.search(r'<div class="ds-row" id="ds-%s-mounts".*?</dd></div>' % re.escape(pid), sheet, re.S)
                for line in ("ro", "reset", "persist", "config"):
                    mm = re.search(r'<li class="m-line" data-line="%s"><span class="m-k">([^<]*)</span>(.*?)</li>' % line, mrow.group(0), re.S) if mrow else None
                    if not mm:
                        errors.append("the %s Mounts row has no %s line" % (pid, line))
                    elif not re.sub(r"<[^>]+>", "", mm.group(2)).strip():
                        errors.append("the %s Mounts row has an empty %s line" % (pid, line))
                if mrow and 'class="ev ' not in mrow.group(0):
                    errors.append("the %s Mounts row has no evidence badge" % pid)
            # a "via your base distribution" tag needs the filter attribute that makes the filter see it
            tagcount = row.count('class="t t-via"')
            trtag = re.search(r'<tr data-id="%s"[^>]*>' % re.escape(pid), table).group(0)
            viaattrs = re.findall(r'data-f([a-z0-9]+)-via="', trtag)
            if tagcount and not viaattrs:
                errors.append("the %s row has a Via your base distribution tag but no data-f<column>-via attribute" % pid)
        # the side-by-side view aligns rows by key, so every sheet needs the same ones, in the same order
        layouts = {}
        for pid, sheet in sheets.items():
            rows_ = re.findall(r'<div class="ds-row" id="([^"]+)" data-col="([^"]+)">', sheet)
            for rid, key in rows_:
                if rid != "ds-%s-%s" % (pid, key):
                    errors.append("the %s data sheet row %s does not follow the id pattern ds-%s-%s" % (pid, rid, pid, key))
            if sheet.count('class="ds-row"') != len(rows_):
                errors.append("the %s data sheet has a row without id and data-col" % pid)
            layouts[pid] = [k for _, k in rows_]
        if layouts:
            ref_pid = sorted(layouts)[0]
            for pid, keys in layouts.items():
                if keys != layouts[ref_pid]:
                    errors.append("the %s data sheet rows %s differ from the %s rows %s; the compare view cannot align them" % (pid, keys, ref_pid, layouts[ref_pid]))
        if "mx-cmp" in index or "mx-view" in index:
            errors.append("the matrix page still carries the old phone compare view")
        dc = re.search(r'<div class="mx-wrap" id="matrix" data-default-cols="([^"]*)"', index)
        defaults = dc.group(1).split() if dc else []
        shown = [c for c in defaults if c != "project"]
        if len(shown) != 5 or "project" not in defaults:
            errors.append("the default columns are %s: Entry plus five columns expected" % defaults)
        if [c for c in cols if c in shown] != shown or any(c not in cols for c in shown):
            errors.append("the default columns %s are not columns of the matrix, or not in matrix order" % shown)
        for lab in ("Show all columns", "Default columns"):
            if ">%s</button>" % lab not in index:
                errors.append("the Columns picker has no %r action" % lab)
        for pid, sheet in sheets.items():
            for lab in re.findall(r"<h[2-6][^>]*>(.*?)</h[2-6]>|<dt[^>]*>(.*?)</dt>", sheet, re.S):
                text = re.sub(r"<[^>]+>", " ", " ".join(lab))
                if re.search(r"\b(buys|costs)\b", text, re.I):
                    errors.append("the %s data sheet uses buys or costs as a section label: %s" % (pid, " ".join(text.split())))
        # on the guide, an entry name that opens a sheet must point at a sheet that exists
        for t in re.findall(r'href="index\.html#tc-([a-z0-9-]+)"', guide):
            if t not in sheets:
                errors.append("the guide links to a data sheet that does not exist: %s" % t)

    if errors:
        print("site check FAILED:")
        for e in dict.fromkeys(errors):
            print("  -", e)
        sys.exit(1)
    print("site check ok: matrix page %d rows each with a data sheet, %d column definitions; guide %d contents links, %d sections; "
          "%d old-link ids redirect to the guide%s" % (len(entries), len(cols), len(toc), len(gsec), len(moved), "; preview build: noindex and banner on both" if preview else ""))


if __name__ == "__main__":
    main()
