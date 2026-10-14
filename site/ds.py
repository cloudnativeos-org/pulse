"""Write the design-system files (project/...) from the same data and renderers as the site."""
import datetime as dt
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def preview(group, height, body, script="", subtitle=""):
    sub = ' subtitle="%s"' % subtitle if subtitle else ""
    return ('<!-- @dsCard group="%s" height=%d%s -->\n'
            '<div class="pl" style="padding:16px;min-height:100%%">%s</div>\n%s'
            % (group, height, sub, body, "<script>%s</script>\n" % script if script else ""))


def write(P, tok, css, js, out, b):
    root = os.path.join(out, "project")
    if os.path.exists(root):
        shutil.rmtree(root)
    comp = os.path.join(root, "components")
    os.makedirs(comp)

    def put(path, text):
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        assert "—" not in text, "em dash in " + path
        open(full, "w").write(text)

    put("tokens.json", json.dumps(tok, indent=2))
    put("components/bundle.css", css)
    put("README.md", open(os.path.join(HERE, "docs", "README.md")).read())

    S = b.Sources()
    pair_html = b.pair(P, S)
    S2 = b.Sources()
    mx_html = b.matrix(P, S2)
    S3 = b.Sources()
    ctx_html = b.context_box(P, S3)

    def mini_table(rows_html, head_cols):
        return ('<div class="mx-scroll"><table class="mx" style="min-width:0">'
                '<thead><tr>%s</tr></thead>%s</table></div>' % (head_cols, rows_html))

    # Evidence badges
    ev_rows = "".join(
        '<tr><td>%s</td><td>%s</td><td class="muted">%s</td></tr>' % (b.badge(k), b.badge(k, compact=True), b.EVIDENCE_MEANING[k])
        for k in b.EVIDENCE)
    ev_body = ('<table class="mx" style="min-width:0;width:auto"><thead><tr><th>Badge</th><th>Compact, in cells</th><th>Meaning (schema vocabularies, section 2)</th></tr></thead>'
               '<tbody>%s</tbody></table>' % ev_rows)

    # Cell values
    vals = [("value", b.value("value", "Whole OS image", "A/B partition switch"), "A normalized value, with a detail line."),
            ("none", b.value("none", "No"), "Documented absence. Needs a source."),
            ("unknown", b.value("unknown", "Unknown"), "Could not be determined. The profile says where we looked."),
            ("n/a", b.value("na", "Not applicable"), "The concept does not exist for this entry."),
            ("not collected", b.value("notcollected", "Not collected"), "A new field with no data yet. Never read as no.")]
    val_body = ('<table class="mx" style="min-width:0;width:auto"><thead><tr><th>State</th><th>Renders as</th><th>Use when</th></tr></thead><tbody>%s</tbody></table>'
                % "".join('<tr><th scope="row">%s</th><td>%s</td><td class="muted">%s</td></tr>' % (k, h, u) for k, h, u in vals))

    flag_body = ('<p style="margin:0 0 8px">%s %s</p><div style="max-width:260px">%s</div>'
                 % (b.flag("talos", "project", False), b.flag("microos", "rollback", False), b.flag("microos", "rollback")))

    # Citation and stamp
    S4 = b.Sources()
    c1 = S4.cite(P["flatcar"], "d04")
    c2 = S4.cite(P["bottlerocket"], "d02", 2)
    cite_body = ('<p class="prose" style="margin:0 0 12px">Flatcar writes each update to the passive <code>/usr</code> partition.%s '
                 'Bottlerocket replaces the whole root filesystem image.%s</p><p style="margin:0 0 12px">%s</p>%s'
                 % (c1, c2, b.stamp(P), S4.render()))

    # Pending rows
    gh = ('<table class="mx" style="min-width:0"><tbody>'
          '<tr><th scope="row"><span class="proj">Talos Linux</span></th><td>Value</td><td>Value</td></tr>'
          '<tr class="gh gh-pending"><th colspan="3"><div class="gh-inner"><span class="gh-name">Profile pending</span><span class="gh-count">1 entry</span></div></th></tr>'
          '<tr class="pending"><th scope="row"><span class="proj">EVE-OS</span><span class="proj-meta">Profile not collected yet.</span></th><td colspan="2">Nothing is claimed.</td></tr>'
          '</tbody></table>')

    # BYOD column
    S5 = b.Sources()
    byod_rows = ""
    for pid in ("kairos", "bootc", "flatcar"):
        p = P[pid]
        c = b.col_byod(p, S5)
        byod_rows += '<tr><th scope="row"><span class="proj">%s</span></th><td class="byod">%s</td><td>%s</td></tr>' % (p["name"], c.html, b.col_update(p, S5).html)
    byod_body = mini_table("<tbody>%s</tbody>" % byod_rows,
                           '<th>Entry</th><th class="byod proposed">Bring your own distro<span class="th-note">Runs on a base you choose?</span></th><th>Update unit</th>')

    S6 = b.Sources()
    cards = b.data_sheet(P["bootc"], S6)
    cards_b = b.data_sheet(P["flatcar"], S6)

    comps = [
        ("ComparisonMatrix", "Comparison", 980, mx_html + '<details style="margin-top:12px"><summary>Sources</summary>%s</details>' % S2.render(), js,
         "Sortable, filterable, one list"),
        ("PendingRows", "Comparison", 200, gh, "", "Approved entries without a profile"),
        ("ByodColumn", "Comparison", 330, byod_body, "", "Bring your own distro"),
        ("EvidenceBadge", "Evidence", 330, ev_body, "", "One per label"),
        ("CellValue", "Evidence", 300, val_body, "", "The three kinds of no"),
        ("FactFixFlag", "Evidence", 170, flag_body, "", "Review state"),
        ("SourceCitation", "Evidence", 420, cite_body, "", "Citation and data as of stamp"),
        ("DataSheet", "Entries", 720, '<div class="two">%s%s</div>' % (cards, cards_b), "", "Project data sheet"),
        ("LooksAlikePair", "Entries", 520, pair_html + '<details style="margin-top:12px"><summary>Sources</summary>%s</details>' % S.render(), "", ""),
        ("ContextBox", "Entries", 470, ctx_html, "", "Entries outside the comparison matrix"),
        ("StartHere", "Reader routes", 560, b.start_here(), "", "Questions, never a project"),
        ("DisclosureBox", "Method", 300, b.coi(), "", "Conflict of interest"),
        ("FixCallout", "Method", 230, b.fix_callout(), "", "Found a mistake?"),
        ("MethodSection", "Method", 900, b.made(P), "", "How this was made"),
        ("IllustrativeBanner", "Review", 110, '<div class="banner" role="note"><b>Illustrative</b><span>Data under fact-fix. These pages show a proposed structure built from the current profiles.</span></div>', "", ""),
        ("ReviewControls", "Review", 220, b.review_bar() + b.review("1", "data sheets", "Internal note. Dropped from print and from the public build."), "", "Internal, never published"),
    ]
    for name, group, h, body, script, sub in comps:
        put("components/%s/preview.html" % name, preview(group, h, body, script, sub))
        put("components/%s/README.md" % name, open(os.path.join(HERE, "docs", "components", name + ".md")).read())

    put("components/Cover/preview.html", open(os.path.join(HERE, "docs", "cover.html")).read())

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    index = {
        "v": 3, "layout": "files", "createdOnFiles": {"v": 1, "at": now},
        "title": "cloud native OS Pulse", "namespace": "Pulse", "libraries": [],
        "sections": {}, "groups": [], "assetGroups": {}, "blobs": {}, "docs": {"sections": []},
        "lastChange": {"by": "Mauro Morales", "at": now, "via": "Claude Code", "note": "First version: tokens, components, sample previews from the 2026 profiles."},
    }
    keep = os.path.join(out, "createdOnFiles.json")
    if os.path.exists(keep):
        index["createdOnFiles"] = json.load(open(keep))
    else:
        json.dump(index["createdOnFiles"], open(keep, "w"))
    put("design-system.json", json.dumps(index, indent=2))
