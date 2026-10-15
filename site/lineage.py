"""The "Where they came from" chart: one bar per OS, from first release to end of life,
grouped by family, with renames, forks, successors, merges and named influences.

Data: data/lineage.yaml. Every bar and every line also appears in the list under the
chart, with its evidence label and its source, so the chart meets the same evidence
standard as the matrix.
"""
import datetime as dt
import re

import yaml

# Families and lanes, top to bottom. A lane is a chain of nodes joined by renames.
LANES = [
    ("Chromium OS and CoreOS line", [
        ["chromium-os"],
        ["cos"],
        ["coreos-container-linux"],
        ["flatcar"],
        ["azure-container-linux"],
    ]),
    ("Fedora and OSTree line", [
        ["fedora-atomic-host"],
        ["fedora-coreos"],
        ["rhcos"],
        ["bootc"],
    ]),
    ("SUSE and Rancher line", [
        ["suse-microos"],
        ["opensuse-kubic"],
        ["microos"],
        ["rancheros"],
        ["rancheros-v2", "elemental"],
        ["k3os"],
        ["cos-toolkit", "elemental-toolkit"],
        ["c3os", "kairos"],
        ["hadron"],
    ]),
    ("Independent starts", [
        ["dianemo", "talos"],
        ["eve-os"],
        ["bottlerocket"],
        ["ubuntu-core"],
    ]),
]
Y0 = 2009
# Relatives that are still alive today, so their bar keeps its arrow.
ALIVE = {"chromium-os", "rhcos", "elemental-toolkit", "hadron"}
SHOWN = ("renamed-to", "forked-from", "succeeded-by", "merged-into", "influenced-by", "based-on")
LEGEND_NAME = {"forked-from": "Fork", "succeeded-by": "Named successor", "merged-into": "Merged into",
               "based-on": "Built on", "influenced-by": "Influence the project names"}
# Short labels for the chart; the list under it uses the full names.
SHORT = {"org-cncf": "CNCF", "org-kinvolk": "Kinvolk", "org-red-hat": "Red Hat", "org-microsoft": "Microsoft",
         "org-suse": "SUSE", "org-rancher-labs": "Rancher", "org-spectro-cloud": "Spectro Cloud", "org-sidero-labs": "Sidero Labs",
         "org-talos-systems": "Talos Systems", "org-lf-edge": "LF Edge", "org-google": "Google", "org-aws": "AWS",
         "org-canonical": "Canonical", "org-coreos-inc": "CoreOS Inc.", "org-fedora-project": "Fedora", "org-zededa": "ZEDEDA",
         "org-opensuse-project": "openSUSE", "org-ettore-di-giacinto": "Ettore Di Giacinto", "org-andrew-rynhard": "Andrew Rynhard",
         "org-yardi": "Yardi", "org-lf-projects": "LF Projects"}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def load(path):
    d = yaml.safe_load(open(path))
    nodes = {n["id"]: n for n in d["nodes"]}
    orgs = {o["id"]: o for o in d.get("orgs", [])}
    return d, nodes, orgs


def ym(s):
    """'2018', '2018-03' or '2018-03-06' (optionally followed by words) to a fractional year."""
    m = re.match(r"(\d{4})(?:-(\d{2}))?", str(s or ""))
    if not m:
        return None
    return int(m.group(1)) + ((int(m.group(2)) - 1) / 12 if m.group(2) else 0)


def fmt(s):
    m = re.match(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", str(s or ""))
    if not m:
        return ""
    y, mo, d = m.groups()
    if d:
        return "%d %s %s" % (int(d), MONTHS[int(mo) - 1], y)
    if mo:
        return "%s %s" % (MONTHS[int(mo) - 1], y)
    return y


def sentence(e, nodes, orgs):
    a, b = nodes[e["from"]]["name"], nodes[e["to"]]["name"]
    t = e["type"]
    if t == "forked-from":
        s = "%s is a fork of %s" % (a, b)
    elif t == "succeeded-by":
        who = e.get("claim_by")
        s = ("%s calls itself the successor of %s" % (b, a)) if who and who == e["to"] else ("%s is the named successor of %s" % (b, a))
    elif t == "merged-into":
        s = "%s merged into %s" % (a, b)
    elif t == "renamed-to":
        s = "%s was renamed %s" % (a, b)
    elif t == "based-on":
        s = "%s is built on %s" % (a, b)
    else:
        s = "%s names %s as an influence" % (a, b)
    if e.get("scope"):
        s += " (%s)" % e["scope"].rstrip(".")
    d = fmt(e.get("date"))
    return s + (", " + d if d else "") + "."


def render(path, S, E, badge, sheets=()):
    """sheets: ids of entries that have a data sheet. Their names link to it."""
    d, nodes, orgs = load(path)
    order = [lid for _, lanes in LANES for lane in lanes for lid in lane]
    lane_of = {lid: i for i, (_, lanes) in enumerate(LANES) for lane in lanes for lid in lane}
    on_chart = set(order)
    now = dt.date.today()
    y1 = now.year + 1
    W, LH = 1120, 30
    px = (W - 30) / (y1 - Y0)
    X = lambda v: 10 + (v - Y0) * px

    def start(n):
        return ym(n.get("first_public"))

    # rows
    rowy, fam_y, y = {}, [], 30
    for fam, lanes in LANES:
        y += 30
        fam_y.append((fam, y - 18))
        for lane in lanes:
            for lid in lane:
                rowy[lid] = y
            y += LH
    H = y + 6

    svg = ['<svg class="lin-svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-labelledby="lin-title lin-desc">'
           '<title id="lin-title">Where the cloud native operating systems came from, %d to %d</title>'
           '<desc id="lin-desc">A timeline with one bar per operating system. The list after the chart gives the same facts as text, with sources.</desc>'
           % (W, H, W, H, Y0, now.year)]
    for yr in range(Y0, y1 + 1):
        xx = X(yr)
        svg.append('<line x1="%.1f" x2="%.1f" y1="18" y2="%d" class="lin-grid"/>' % (xx, xx, H))
        if yr < y1:
            svg.append('<text x="%.1f" y="12" class="lin-year">%d</text>' % (xx + 3, yr))
    for fam, fy in fam_y:
        svg.append('<text x="10" y="%d" class="lin-fam">%s</text>' % (fy, E(fam)))

    # edges between lanes (renames inside a lane are drawn as ticks)
    for e in d["edges"]:
        if e["type"] not in SHOWN or e.get("evidence") == "UNKNOWN" or e.get("chart") is False:
            continue
        f, t = e["from"], e["to"]
        if f not in on_chart or t not in on_chart or rowy[f] == rowy[t]:
            continue
        when = ym(e.get("date")) or max(x for x in (start(nodes[f]), start(nodes[t])) if x is not None)
        x1, ya, yb = X(when), rowy[f] + 6, rowy[t] + 6
        mid = (ya + yb) / 2
        svg.append('<a href="#lin-%s"><path d="M%.1f %.1f C %.1f %.1f, %.1f %.1f, %.1f %.1f" class="lin-edge e-%s%s">'
                   '<title>%s</title></path></a>'
                   % (f, x1, ya, x1 + 14, mid, x1 - 14, mid, x1, yb, e["type"], " e-inferred" if e.get("evidence") == "INFERRED" else "",
                      E(sentence(e, nodes, orgs))))

    # bars
    for fam, lanes in LANES:
        for lane in lanes:
            first = nodes[lane[0]]
            kind = "entry" if any(nodes[i]["kind"] == "entry" for i in lane) else "other"
            x0 = X(start(first))
            last = nodes[lane[-1]]
            end = ym(last.get("end_of_life")) or ym(last.get("last_release"))
            # An ancestor with no recorded end fades out instead of pointing at today.
            open_end = not end and kind != "entry" and last["kind"] in ("ancestor", "relative") and lane[-1] not in ALIVE
            xe = X(end) if end else X(now.year + (now.month - 1) / 12)
            yy = rowy[lane[0]]
            names = [nodes[i]["name"] for i in lane]
            former = ", ".join("%s %s" % (nodes[i]["name"], str(nodes[i].get("first_public"))[:4]) for i in lane[:-1])
            svg.append('<a href="#lin-%s" class="lin-row k-%s"><title>%s</title>' % (lane[-1], kind, E(" then ".join(names))))
            svg.append('<rect x="%.1f" y="%d" width="%.1f" height="12" rx="2" class="lin-bar"/>' % (x0, yy, max(xe - x0, 3)))
            if open_end:
                svg.append('<rect x="%.1f" y="%d" width="%.1f" height="12" class="lin-fade"/>' % (xe - 90, yy, 92))
            elif not end:
                svg.append('<path d="M%.1f %d l6 6 l-6 6z" class="lin-bar"/>' % (xe, yy))
            for i in lane[1:]:
                xx = X(start(nodes[i]))
                svg.append('<line x1="%.1f" x2="%.1f" y1="%d" y2="%d" class="lin-tick"/>' % (xx, xx, yy - 3, yy + 15))
            near_end = x0 > W - 260
            label = ('<text x="%.1f" y="%d" class="lin-name"%s>%s%s</text>' % (
                (xe - 2) if near_end else (x0 + 3), yy - 3, ' text-anchor="end"' if near_end else "", E(names[-1]),
                ('<tspan class="lin-former"> formerly %s</tspan>' % E(former)) if former else ""))
            opens = lane[-1] in sheets
            if not opens:
                svg.append(label)
            # Owner labels inside the bar: from the owner's date (never before the bar starts),
            # dropped when the next label or the bar end leaves no room. The list keeps them all.
            labels = []
            for i in lane:
                for o in nodes[i].get("owners") or []:
                    if o.get("chart") is False or not ym(o.get("from")):
                        continue
                    labels.append((max(X(ym(o["from"])), x0), SHORT.get(o["org"], orgs.get(o["org"], {}).get("name", o["org"]))))
            labels.sort()
            for k, (lx, txt) in enumerate(labels):
                stop = labels[k + 1][0] if k + 1 < len(labels) else xe
                if lx + 3 + 5.2 * len(txt) <= stop - 2:
                    svg.append('<text x="%.1f" y="%d" class="lin-org">%s</text>' % (lx + 3, yy + 10, E(txt)))
            svg.append('</a>')
            if opens:   # the name opens the entry's data sheet; it sits outside the row link
                svg.append('<a href="#tc-%s" class="lin-open"><title>Open the data sheet for %s</title>%s</a>' % (lane[-1], E(names[-1]), label))
    svg.append('</svg>')
    svg.insert(1, '<defs><linearGradient id="lin-fade-g"><stop offset="0" class="lin-fade-0"/><stop offset="1" class="lin-fade-1"/></linearGradient></defs>')

    legend = ('<ul class="lin-legend">'
              '<li><span class="sw sw-entry"></span>In the matrix</li>'
              '<li><span class="sw sw-anc"></span>Ancestor or relative</li>'
              + "".join('<li><svg width="28" height="8" aria-hidden="true"><line x1="0" x2="28" y1="4" y2="4" class="lin-edge e-%s"/></svg>%s</li>' % (k, v)
                        for k, v in LEGEND_NAME.items())
              + '<li><span class="tick"></span>Renamed</li>'
              '<li><span class="sw sw-fade"></span>End not recorded</li>'
              '<li>Small text on a bar: who held the project from that date</li></ul>')

    # the same facts as text, with sources
    def cite(srcs, who):
        nums = [S.add(dict(s, type=s.get("publisher", ""), retrieved=d.get("retrieved", "")), who) for s in (srcs or [])[:2] if s.get("url")]
        return ('<sup class="cite">[%s]</sup>' % ",".join('<a href="#src-%d" aria-label="Source %d">%d</a>' % (k, k, k) for k in nums)) if nums else ""

    items = []
    for fam, lanes in LANES:
        items.append('<li class="lin-l-fam">%s</li>' % E(fam))
        for lane in lanes:
            for i in lane:
                n = nodes[i]
                bits = []
                fp = fmt(n.get("first_public"))
                if fp:
                    bits.append("First public %s%s%s." % (fp, (" (%s)" % n["first_public_note"].rstrip(".")) if n.get("first_public_note") else "",
                                                        cite(n.get("first_public_sources"), n["name"])))
                if n.get("last_release"):
                    bits.append("Last release %s%s%s." % (fmt(n["last_release"]), ("; " + n["last_release_note"].rstrip(".")) if n.get("last_release_note") else "",
                                                         cite(n.get("last_release_sources"), n["name"])))
                elif not n.get("end_of_life") and n["kind"] in ("ancestor", "relative") and i not in ALIVE:
                    bits.append("End not recorded.")
                if n.get("end_of_life"):
                    bits.append("Ended %s%s." % (fmt(n["end_of_life"]), cite(n.get("end_of_life_sources"), n["name"])))
                for o in n.get("owners") or []:
                    org = orgs.get(o["org"], {}).get("name", o["org"]).rstrip(".")
                    how = {"created": "Created by", "acquired": "Held by", "donated": "Contributed to", "sponsored": "Sponsored by"}.get(o.get("how"), "Held by")
                    when = fmt(o.get("from"))
                    bits.append("%s %s%s%s%s" % (how, E(org), (" from " + when) if when else "", "." , cite(o.get("sources"), n["name"])
                                                 + (" " + badge(o["evidence"], compact=True) if o.get("evidence") else "")))
                for e in d["edges"]:
                    if e["from"] == i and e["type"] in SHOWN and e.get("chart") is not False:
                        bits.append("%s%s %s" % (E(sentence(e, nodes, orgs)), cite(e.get("sources"), n["name"]), badge(e.get("evidence", "UNKNOWN"), compact=True)))
                nm = ('<a class="proj-open" href="#tc-%s">%s</a>' % (i, E(n["name"]))) if i in sheets else E(n["name"])
                items.append('<li id="lin-%s"><span class="lin-l-n">%s</span> %s</li>' % (i, nm, " ".join(bits)))
    listing = ('<details class="lin-list"><summary>Every bar and line, as text, with its source</summary><ul>%s</ul></details>' % "".join(items))
    # Below 900px the script collapses the chart behind this button and opens the text list. Without the script, both show as on wide screens.
    toggle = '<button type="button" class="lin-chart-toggle no-print" aria-expanded="true" aria-controls="lin-chart">Hide chart</button>'
    return (toggle + '<div class="lin-chart" id="lin-chart">' + legend
            + '<div class="lin-wrap"><div class="lin-frame">%s</div></div></div>' % "".join(svg) + listing)


def check(path):
    """Raise if a lane names a node that does not exist or has no first-public date."""
    d, nodes, _ = load(path)
    bad = []
    for _, lanes in LANES:
        for lane in lanes:
            for i in lane:
                if i not in nodes:
                    bad.append("%s: no such node" % i)
                elif ym(nodes[i].get("first_public")) is None:
                    bad.append("%s: no first_public date" % i)
    for e in d["edges"]:
        for k in ("from", "to"):
            if e[k] not in nodes:
                bad.append("edge %s: unknown %s %s" % (e.get("id", "?"), k, e[k]))
    return bad
