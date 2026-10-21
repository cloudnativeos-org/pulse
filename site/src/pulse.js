/* cloud native OS Pulse: matrix sort and filter, group-rule and placement switches.
   No dependencies. Works on any table built by build.py (class "mx"). */
(function () {
  "use strict";

  function initMatrix(root) {
    var table = root.querySelector("table.mx");
    if (!table) return;
    var bar = root.querySelector(".mx-bar");
    var status = root.querySelector(".mx-count");
    var clear = root.querySelector(".mx-clear");
    var activeBox = root.querySelector(".mx-active");
    var filtersBox = root.querySelector(".mx-filters");
    var colsBox = root.querySelector(".mx-cols");
    var scroller = root.querySelector(".mx-scroll");
    var groups = Array.prototype.slice.call(table.tBodies).filter(function (tb) { return tb.dataset.group; });
    var sortState = { col: null, dir: "ascending" };
    var WIDE = window.matchMedia("(min-width: 1200px)");
    var marked = null;           /* the column a link or the reader marked */

    function rows(tb) { return Array.prototype.slice.call(tb.rows).filter(function (r) { return r.dataset.id; }); }
    function allRows() { return groups.reduce(function (a, tb) { return a.concat(rows(tb)); }, []); }

    /* ---------- Columns shown ---------- */
    var allCols = Array.prototype.map.call(table.querySelectorAll("thead th[data-col]"), function (th) { return th.dataset.col; });
    var defaults = (root.dataset.defaultCols || "").split(" ");
    var chosen = defaults.slice();
    try { var sv = JSON.parse(localStorage.getItem("pulse-cols") || "null"); if (sv && sv.length) chosen = sv; } catch (e) {}
    var forced = {};             /* shown for a link or an active filter, not saved */
    var style = document.createElement("style");
    document.head.appendChild(style);
    function colTitle(k) { var b = table.querySelector('thead th[data-col="' + k + '"] .mx-col'); return b ? b.textContent : k; }
    function visibleCols() { return allCols.filter(function (k) { return k === "project" || chosen.indexOf(k) !== -1 || forced[k]; }); }
    function applyCols() {
      var vis = visibleCols();
      var hide = allCols.filter(function (k) { return vis.indexOf(k) === -1; });
      style.textContent = hide.length ? "@media screen{" + hide.map(function (k) { return ".mx .c-" + k; }).join(",") + "{display:none}}" : "";
      table.querySelectorAll("tr.empty > td").forEach(function (td) { td.colSpan = vis.length; });
      if (colsBox) {
        colsBox.querySelectorAll('input[name="col"]').forEach(function (i) { i.checked = vis.indexOf(i.value) !== -1; });
        colsBox.querySelector(".mx-cols-n").textContent = "(" + (vis.length - 1) + " of " + (allCols.length - 1) + ")";   /* the Entry column is always shown and not counted */
      }
    }
    function saveCols() { try { localStorage.setItem("pulse-cols", JSON.stringify(chosen)); } catch (e) {} }
    if (colsBox) {
      colsBox.addEventListener("change", function (e) {
        var i = e.target;
        if (i.name !== "col") return;
        chosen = chosen.filter(function (k) { return k !== i.value; });
        if (i.checked) chosen.push(i.value); else delete forced[i.value];
        saveCols(); applyCols();
      });
      colsBox.querySelector(".mx-cols-all").addEventListener("click", function () { chosen = allCols.slice(); saveCols(); applyCols(); });
      colsBox.querySelector(".mx-cols-reset").addEventListener("click", function () { chosen = defaults.slice(); forced = {}; saveCols(); syncForced(); applyCols(); });
      colsBox.addEventListener("keydown", function (e) { if (e.key === "Escape" && colsBox.open) { colsBox.open = false; colsBox.querySelector("summary").focus(); } });
      document.addEventListener("click", function (e) { if (colsBox.open && !colsBox.contains(e.target)) colsBox.open = false; });
    }

    /* ---------- Filters ---------- */
    function activeFilters() {
      var f = {};
      if (!bar) return f;
      bar.querySelectorAll("input[type=checkbox]:checked").forEach(function (i) {
        (f[i.name] = f[i.name] || []).push(i.value);
      });
      return f;
    }
    /* A filter on a hidden column shows that column. */
    function syncForced() {
      if (!bar) return;
      Object.keys(forced).forEach(function (k) { if (forced[k] === "filter") delete forced[k]; });
      bar.querySelectorAll("input:checked").forEach(function (i) {
        var k = i.closest("fieldset").dataset.col;
        if (k && chosen.indexOf(k) === -1 && !forced[k]) forced[k] = "filter";
      });
    }
    function chips() {
      if (!activeBox || !bar) return;
      activeBox.innerHTML = "";
      bar.querySelectorAll("input:checked").forEach(function (i) {
        var b = document.createElement("button");
        var lab = i.closest("fieldset").querySelector("legend").textContent + ": " + i.nextElementSibling.textContent;
        b.type = "button"; b.className = "mx-chip"; b.textContent = lab;
        b.setAttribute("aria-label", "Remove filter " + lab);
        b.addEventListener("click", function () {
          i.checked = false; filtersChanged();
          var next = activeBox.querySelector(".mx-chip"); (next || clear).focus();
        });
        activeBox.appendChild(b);
      });
      var n = bar.querySelectorAll("input:checked").length;
      var fn = root.querySelector(".mx-fn");
      if (fn) fn.textContent = "(" + n + " active)";
    }

    /* A row matches a filter when its own value matches, or when it credits the value "via your base distribution":
       data-f<k>-via lists the values its base distribution can supply (an accelerator, an architecture). */
    function viaOf(row, k) { return (row.dataset["f" + k + "Via"] || "").split(" ").filter(Boolean); }
    /* A provider filter and a level filter together are one question: runs on this provider at this level. The row lists
       its pairs as provider:level in data-fprovpair, so a level on one provider never answers for another. */
    function matches(row, f) {
      var pairs = f.prov && f.provlvl ? (row.dataset.fprovpair || "").split(" ") : null;
      if (pairs && !f.prov.some(function (p) { return f.provlvl.some(function (l) { return pairs.indexOf(p + ":" + l) !== -1; }); })) return false;
      return Object.keys(f).every(function (k) {
        if (pairs && (k === "prov" || k === "provlvl")) return true;
        var have = (row.dataset["f" + k] || "").split(" "), via = viaOf(row, k);
        return f[k].some(function (v) { return have.indexOf(v) !== -1 || via.indexOf(v) !== -1; });
      });
    }
    /* A row kept only through its base distribution shows why: the "Via your base distribution" tag is highlighted. */
    function markVia(row, f, ok) {
      row.querySelectorAll(".t-via.via-hit").forEach(function (t) { t.classList.remove("via-hit"); });
      if (!ok) return;
      Object.keys(f).forEach(function (k) {
        var via = viaOf(row, k);
        if (!via.length) return;
        var have = (row.dataset["f" + k] || "").split(" ");
        f[k].forEach(function (v) {
          if (have.indexOf(v) !== -1 || via.indexOf(v) === -1) return;
          row.querySelectorAll(".t-via").forEach(function (t) {
            if ((t.dataset.via || "").split(" ").indexOf(v) !== -1) t.classList.add("via-hit");
          });
        });
      });
    }

    function sortKey(row, col) {
      if (col === null) return row.dataset.name;
      var cell = row.cells[col];
      return cell ? (cell.dataset.sort || cell.textContent.trim()).toLowerCase() : "";
    }

    function render() {
      var f = activeFilters();
      var shown = 0, total = 0;
      groups.forEach(function (tb) {
        var rs = rows(tb).filter(function (r) { return !r.classList.contains("placed-out"); });
        var pending = tb.dataset.group === "pending";
        rs.sort(function (a, b) {
          var ka = sortKey(a, sortState.col), kb = sortKey(b, sortState.col);
          var c = ka < kb ? -1 : ka > kb ? 1 : 0;
          if (c === 0) c = a.dataset.name < b.dataset.name ? -1 : 1;
          return sortState.dir === "descending" ? -c : c;
        });
        var n = 0;
        rs.forEach(function (r) {
          tb.appendChild(r);
          var ok = r.classList.contains("pending") ? Object.keys(f).length === 0 : matches(r, f);
          r.hidden = !ok;
          markVia(r, f, ok);
          if (ok) n++;
          r.classList.toggle("alt", ok && n % 2 === 0);
        });
        rows(tb).forEach(function (r) { if (r.classList.contains("placed-out")) r.hidden = true; });
        var empty = tb.querySelector("tr.empty");
        if (empty) { tb.appendChild(empty); empty.hidden = n > 0 || rs.length === 0; }
        var cnt = tb.querySelector(".gh-count");
        if (cnt) cnt.textContent = Object.keys(f).length ? n + " of " + rs.length + " shown" : rs.length + (rs.length === 1 ? " entry" : " entries");
        if (!pending) { shown += n; total += rs.length; }
      });
      if (status) status.textContent = Object.keys(f).length ? shown + " of " + total + " entries match" : total + " profiled entries, alphabetical by name";
      if (clear) clear.disabled = Object.keys(f).length === 0;
      chips();
    }

    function filtersChanged() { syncForced(); applyCols(); writeHash(); render(); }

    /* Tint one column so the reader keeps their place: the one they sorted, or the one a link pointed to. */
    function highlight(col) {
      table.querySelectorAll("th.hl,td.hl").forEach(function (c) { c.classList.remove("hl"); });
      marked = null;
      if (col === null || col === undefined) return;
      table.querySelectorAll("tr").forEach(function (r) { if (r.cells[col]) r.cells[col].classList.add("hl"); });
      var th = table.tHead.rows[0].cells[col];
      marked = th ? th.dataset.col : null;
    }

    /* The column title only marks the column. Sorting happens on the arrow only. */
    table.querySelectorAll("thead .mx-col").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var th = btn.closest("th");
        var on = th.classList.contains("hl");
        table.querySelectorAll("thead .mx-col").forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
        highlight(on ? null : th.cellIndex);
        btn.setAttribute("aria-pressed", on ? "false" : "true");
      });
    });

    table.querySelectorAll("thead .mx-sort").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var th = btn.closest("th");
        var col = th.cellIndex;
        /* The arrow cycles: ascending, descending, then no sort (the default alphabetical order). */
        var cleared = false;
        if (sortState.col !== col) { sortState.col = col; sortState.dir = "ascending"; }
        else if (sortState.dir === "ascending") { sortState.dir = "descending"; }
        else { sortState.col = null; sortState.dir = "ascending"; cleared = true; }
        table.querySelectorAll("thead th").forEach(function (h) { h.removeAttribute("aria-sort"); });
        if (!cleared) th.setAttribute("aria-sort", sortState.dir);
        else table.querySelector("thead th").setAttribute("aria-sort", "ascending");  /* back to the load state: alphabetical by name */
        if (!cleared && col !== 0) highlight(col);
        render();
      });
    });

    /* A "?" next to a column title, and a project name, are links. The modal at the end of this file opens them without leaving the page. */

    if (bar) bar.addEventListener("change", filtersChanged);
    if (clear) clear.addEventListener("click", function () {
      bar.querySelectorAll("input:checked").forEach(function (i) { i.checked = false; });
      filtersChanged();
    });

    /* The filters fold into "Filters (n active)" at every width, closed by default, so the table is in view. */
    if (filtersBox) filtersBox.open = false;

    function writeHash() {
      if (!root.id) return;
      var f = activeFilters();
      var q = Object.keys(f).map(function (k) { return k + "=" + f[k].join(","); }).join("&");
      history.replaceState(null, "", "#" + root.id + (q ? "?" + q : ""));
    }

    function readHash() {
      /* Closing the modal with Back returns to the filter state the reader left. Nothing changed, so do not scroll. */
      if (window.pulseModalClosed) { window.pulseModalClosed = false; return; }
      var h = decodeURIComponent(location.hash.slice(1));
      if (!root.id || h.indexOf(root.id) !== 0 || !bar) return;
      var q = h.split("?")[1] || "";
      bar.querySelectorAll("input").forEach(function (i) { i.checked = false; });
      q.split("&").forEach(function (pair) {
        var kv = pair.split("=");
        if (!kv[1]) return;
        kv[1].split(",").forEach(function (v) {
          var i = bar.querySelector('input[name="' + kv[0] + '"][value="' + v + '"]');
          if (i) i.checked = true;
        });
      });
      var focusCol = h.match(/col=([a-z0-9-]+)/);
      Object.keys(forced).forEach(function (k) { if (forced[k] === "link") delete forced[k]; });
      if (focusCol && allCols.indexOf(focusCol[1]) !== -1 && chosen.indexOf(focusCol[1]) === -1) forced[focusCol[1]] = "link";
      syncForced(); applyCols();
      table.querySelectorAll("th.hl,td.hl").forEach(function (c) { c.classList.remove("hl"); });
      marked = null;
      render();
      if (focusCol) {
        var th = table.querySelector('thead th[data-col="' + focusCol[1] + '"]');
        if (th) { highlight(th.cellIndex); revealColumn(th); }
      }
      /* A link to the matrix lands on it, with the filter applied: on the results line, just above the table. */
      var line = root.querySelector(".mx-status");
      if (q && line) line.scrollIntoView({ block: "start" });
      else root.scrollIntoView({ block: "start" });
    }

    /* Scroll the matrix sideways so a column sits just right of the sticky Entry column, not under it. */
    function revealColumn(th) {
      var first = table.querySelector("thead th");
      if (!scroller || !first || th === first) return;
      var delta = th.getBoundingClientRect().left - scroller.getBoundingClientRect().left - first.getBoundingClientRect().width - 8;
      scroller.scrollLeft += delta;
    }

    /* Review switch: which rule assigns rows to the two groups. */
    root.setGroupRule = function (rule) {
      var by = {};
      groups.forEach(function (tb) { by[tb.dataset.group] = tb; });
      allRows().forEach(function (r) {
        if (r.classList.contains("pending")) return;
        var g = r.dataset["rule" + rule];
        if (g && by[g] && r.parentNode !== by[g]) by[g].appendChild(r);
      });
      groups.forEach(function (tb) {
        var d = tb.querySelector(".gh-rule");
        if (d && d.dataset["rule" + rule]) d.textContent = d.dataset["rule" + rule];
      });
      render();
    };
    /* Review switch: a row can be moved to the context box. */
    root.setPlacement = function (id, inMatrix) {
      allRows().forEach(function (r) { if (r.dataset.id === id) r.classList.toggle("placed-out", !inMatrix); });
      render();
    };

    window.addEventListener("hashchange", readHash);
    applyCols();
    readHash();
    render();
  }

  function initReview(page) {
    var bar = page.querySelector(".review-bar");
    if (!bar) return;
    var mx = page.querySelector(".mx-wrap");
    bar.addEventListener("change", function (e) {
      var t = e.target;
      if (t.name === "rule" && mx && mx.setGroupRule) mx.setGroupRule(t.value);
      if (t.name === "placement") {
        var inMatrix = t.value === "matrix";
        if (mx && mx.setPlacement) mx.setPlacement(t.dataset.id, inMatrix);
        page.querySelectorAll('[data-ctx="' + t.dataset.id + '"]').forEach(function (el) { el.hidden = inMatrix; });
      }
      if (t.name === "notes") page.classList.toggle("hide-review", !t.checked);
    });
  }

  /* Theme switch: System follows the OS; Light and Dark set data-theme. Remembered per reader. */
  function initTheme() {
    var box = document.querySelector(".theme");
    if (!box) return;
    var root = document.documentElement, saved = "system";
    try { saved = localStorage.getItem("pulse-theme") || "system"; } catch (e) {}
    function apply(v) {
      if (v === "system") root.removeAttribute("data-theme"); else root.setAttribute("data-theme", v);
      box.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.value === v)); });
      try { localStorage.setItem("pulse-theme", v); } catch (e) {}
    }
    box.addEventListener("click", function (e) { var b = e.target.closest("button"); if (b) apply(b.value); });
    apply(saved);
  }

  function boot() {
    initTheme();
    document.querySelectorAll(".mx-wrap").forEach(initMatrix);
    document.querySelectorAll(".pl").forEach(initReview);
    var rule = document.querySelector('.review-bar input[name="rule"]:checked');
    var mx = document.querySelector(".mx-wrap");
    if (rule && mx && mx.setGroupRule) mx.setGroupRule(rule.value);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();

/* Side table of contents: toggle, remember the choice, mark the current section. */
(function () {
  var html = document.documentElement, btn = document.querySelector(".toc-toggle"), toc = document.getElementById("toc");
  if (!btn || !toc) return;
  var WIDE = "(min-width: 1200px)";  /* from this width the open panel pushes the page aside */
  function wide() { return window.matchMedia(WIDE).matches; }
  var saved = null;
  try { saved = localStorage.getItem("pulse-toc"); } catch (e) {}
  var open = saved ? saved === "open" : wide();
  function set(v) {
    open = v; html.classList.toggle("toc-open", v); btn.setAttribute("aria-expanded", v ? "true" : "false");
    var label = v ? "Hide contents" : "Show contents";
    btn.setAttribute("aria-label", label); btn.setAttribute("title", label);
    btn.firstElementChild.innerHTML = v ? "&laquo;" : "&raquo;";
  }
  set(open);
  btn.addEventListener("click", function () { set(!open); try { localStorage.setItem("pulse-toc", open ? "open" : "closed"); } catch (e) {} });
  toc.addEventListener("click", function (ev) { if (ev.target.tagName === "A" && !wide()) set(false); });
  /* Below the wide layout the panel covers the text: Escape or a click outside closes it. */
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && open && !wide()) { set(false); btn.focus(); }
  });
  document.addEventListener("click", function (ev) {
    if (open && !wide() && !toc.contains(ev.target) && !btn.contains(ev.target)) set(false);
  });

  /* Mark the current place: the last target whose top is above 20% of the viewport, and its section's group link. */
  var links = {};
  toc.querySelectorAll("li a, a.toc-group-link").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
  var targets = [];
  Object.keys(links).forEach(function (id) {
    var el = document.getElementById(id);
    if (!el) return;
    var box = el.closest("section, article") || el;
    if (/^w-/.test(id)) box = el;
    targets.push({ id: id, el: box, sec: el.closest("section[aria-labelledby]") });
  });
  /* Contents groups: collapsed by default. The toggle opens or closes a group by hand; that choice holds until the reader
     toggles it again. Otherwise the group follows the reader's place. */
  var groups = [], lastBox = null;
  toc.querySelectorAll(".toc-g").forEach(function (box) {
    var btn = box.querySelector(".toc-gt"), sub = box.querySelector(".toc-sub");
    if (!btn || !sub) return;
    var title = (box.querySelector(".toc-group-link, .toc-group-name") || {}).textContent || "";
    var g = { box: box, manual: null, show: function (v) {
      sub.hidden = !v;
      btn.setAttribute("aria-expanded", v ? "true" : "false");
      btn.setAttribute("aria-label", (v ? "Hide the entries under " : "Show the entries under ") + title);
    } };
    btn.addEventListener("click", function () { g.manual = sub.hidden; g.show(g.manual); });
    groups.push(g);
  });
  var ticking = false;
  function mark() {
    ticking = false;
    var line = window.innerHeight * 0.2, cur = null;
    targets.forEach(function (t) { if (t.el.getBoundingClientRect().top <= line && (!cur || t.el.getBoundingClientRect().top >= cur.el.getBoundingClientRect().top)) cur = t; });
    var on = {};
    if (cur) {
      on[cur.id] = true;
      if (cur.sec) on[cur.sec.getAttribute("aria-labelledby")] = true;
    }
    Object.keys(links).forEach(function (k) { links[k].classList.toggle("on", !!on[k]); });
    /* Open the group that holds the current place, and close the others, unless the reader set one by hand. */
    var curBox = null;
    groups.forEach(function (g) { if (g.box.querySelector("a.on")) curBox = g.box; });
    if (curBox !== lastBox) { groups.forEach(function (g) { g.manual = null; }); lastBox = curBox; }  /* a hand choice lasts until the reader moves to another group */
    groups.forEach(function (g) { g.show(g.manual !== null ? g.manual : g.box === curBox); });
  }
  function queue() { if (!ticking) { ticking = true; window.requestAnimationFrame(mark); } }
  window.addEventListener("scroll", queue, { passive: true });
  window.addEventListener("resize", queue);
  window.addEventListener("hashchange", queue);
  mark();
})();

/* Back from a citation: shown while the address points at a source. */
(function () {
  var back = document.querySelector(".src-back");
  if (!back) return;
  function sync() { back.hidden = location.hash.indexOf("#src-") !== 0; }
  back.addEventListener("click", function (ev) {
    ev.preventDefault();
    if (history.length > 1) history.back(); else { location.hash = ""; window.scrollTo(0, 0); }
  });
  window.addEventListener("hashchange", sync);
  sync();
})();

/* Timeline: start at the recent years, and fade the side that has more to scroll to. */
(function () {
  document.querySelectorAll(".lin-wrap").forEach(function (wrap) {
    var f = wrap.querySelector(".lin-frame");
    if (!f) return;
    function sync() {
      var max = f.scrollWidth - f.clientWidth;
      wrap.classList.toggle("more-left", f.scrollLeft > 1);
      wrap.classList.toggle("more-right", f.scrollLeft < max - 1);
    }
    f.scrollLeft = f.scrollWidth;
    f.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    sync();
  });

  /* Below 900px: the text list is open and the chart is collapsed behind "Show chart". At 900px and wider: the chart shows and the list is collapsed. */
  var mq = window.matchMedia("(max-width: 899.98px)");
  document.querySelectorAll(".lin-chart-toggle").forEach(function (btn) {
    var chart = document.getElementById(btn.getAttribute("aria-controls"));
    var list = chart && chart.parentNode.querySelector(".lin-list");
    if (!chart) return;
    chart.parentNode.classList.add("lin-collapsible");
    function set(open) {
      chart.hidden = !open;
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.textContent = open ? "Hide chart" : "Show chart";
      if (open) {
        var f = chart.querySelector(".lin-frame");
        if (f) { f.scrollLeft = f.scrollWidth; f.dispatchEvent(new Event("scroll")); }
      }
    }
    function apply() {
      set(!mq.matches);
      if (list) list.open = mq.matches;
    }
    btn.addEventListener("click", function () { set(chart.hidden); });
    if (mq.addEventListener) mq.addEventListener("change", apply); else mq.addListener(apply);
    apply();
  });
})();

/* Modal: a project's data sheet, a column definition, or a side-by-side comparison of 2 or 3 projects opens over the matrix page.
   The address changes with it, so a sheet can be linked (#tc-<id>, or #ds-<id>-<column> for one row), a comparison too
   (#compare=<id>,<id>[,<id>]), and Back closes it.
   Without this script the links are plain: #tc-<id> scrolls to the sheet in the page, guide.html#col-<key> opens the guide. */
(function () {
  "use strict";
  var cards = document.querySelector(".cards");
  if (!cards || !window.HTMLDialogElement) return;
  var defs = {};
  try { defs = JSON.parse((document.getElementById("col-defs") || {}).textContent || "{}"); } catch (e) {}

  var sheets = {}, order = [];
  cards.querySelectorAll("article.tc").forEach(function (a) {
    var id = a.getAttribute("aria-labelledby").replace(/^tc-/, "");
    sheets[id] = a; order.push(id);
  });

  var dlg = document.createElement("dialog");
  dlg.className = "pl pm";
  dlg.innerHTML = '<div class="pm-bar"><span class="eyebrow pm-kind"></span><button type="button" class="pm-close">Close</button></div>' +
                  '<div class="pm-body" tabindex="-1"></div>';
  document.body.appendChild(dlg);
  var kind = dlg.querySelector(".pm-kind"), body = dlg.querySelector(".pm-body"), closeBtn = dlg.querySelector(".pm-close");

  var MAXCMP = 3;
  var current = null;      /* { type: "tc" | "ds" | "def" | "cmp", pid, col } while open; a "cmp" spec also has ids */
  var inDialog = null;     /* the sheet article now inside the dialog */
  var opener = null;       /* the link that opened it, to give focus back to */
  var depth = 0;           /* history entries this modal session pushed */
  var deep = false;        /* the page was loaded with the sheet's address: Back leaves the page */

  /* The first 3 valid, distinct ids of a comma list. */
  function cmpIds(list) {
    var ids = [];
    list.split(",").forEach(function (id) { if (sheets[id] && ids.indexOf(id) === -1 && ids.length < MAXCMP) ids.push(id); });
    return ids;
  }
  function cmpSpec(ids) { return { type: "cmp", pid: ids.join(","), ids: ids }; }
  function parse(hash) {
    var h = hash.replace(/^#/, ""), m;
    try { h = decodeURIComponent(h); } catch (e) {}
    if ((m = /^compare=(.*)$/.exec(h))) { var ids = cmpIds(m[1]); return ids.length ? cmpSpec(ids) : null; }
    if ((m = /^tc-(.+)$/.exec(h)) && sheets[m[1]]) return { type: "tc", pid: m[1] };
    if ((m = /^ds-(.+)-([a-z0-9]+)$/.exec(h)) && sheets[m[1]]) return { type: "ds", pid: m[1], col: m[2] };
    if ((m = /^def-([a-z0-9]+)$/.exec(h)) && defs[m[1]]) return { type: "def", col: m[1] };
    return null;
  }
  function hashOf(s) { return s.type === "tc" ? "#tc-" + s.pid : s.type === "ds" ? "#ds-" + s.pid + "-" + s.col : s.type === "cmp" ? "#compare=" + s.pid : "#def-" + s.col; }
  /* The address a link would go to, as a spec: a sheet link, a note tag, or a "?" in a column title. */
  function fromHref(href) {
    var m;
    if (!href) return null;
    if (href.charAt(0) === "#") return parse(href);
    if ((m = /^guide\.html#col-([a-z0-9]+)$/.exec(href)) && defs[m[1]]) return { type: "def", col: m[1] };
    return null;
  }
  function same(a, b) { return !!a && !!b && a.type === b.type && a.pid === b.pid && a.col === b.col; }

  function putBack() {
    if (!inDialog) return;
    var pid = inDialog.getAttribute("aria-labelledby").replace(/^tc-/, ""), ref = null;
    for (var j = order.indexOf(pid) + 1; j < order.length; j++) { if (sheets[order[j]].parentNode === cards) { ref = sheets[order[j]]; break; } }
    inDialog.querySelectorAll(".ds-hit").forEach(function (r) { r.classList.remove("ds-hit"); });
    cards.insertBefore(inDialog, ref);
    inDialog = null;
  }

  function show(spec) {
    putBack();
    body.textContent = "";
    if (spec.type === "cmp") {
      kind.textContent = "Comparison";
      body.appendChild(buildCompare(spec.ids));
      dlg.setAttribute("aria-labelledby", "pm-cmp-title");
      picks = spec.ids.slice(); syncPicks();
    } else if (spec.type === "def") {
      var d = defs[spec.col];
      kind.textContent = "Column definition";
      body.innerHTML = '<div class="pm-def"><h3 id="pm-def-title"></h3>' + d.html + '<p class="pm-all"><a href="guide.html#h-dims">All column definitions</a></p></div>';
      body.querySelector("h3").textContent = d.title;
      dlg.setAttribute("aria-labelledby", "pm-def-title");
    } else {
      kind.textContent = "Data sheet";
      inDialog = sheets[spec.pid];
      body.appendChild(inDialog);
      dlg.setAttribute("aria-labelledby", "tc-" + spec.pid);
    }
    current = spec;
    if (!dlg.open) { dlg.showModal(); document.documentElement.classList.add("pm-open"); }
    place();
  }

  /* Scroll inside the modal only: to the row an address names, or to the top. The browser's own scroll to an address
     can move the dialog itself, so put that back. */
  function place() {
    dlg.scrollTop = 0;
    var row = current && current.type === "ds" ? document.getElementById("ds-" + current.pid + "-" + current.col) : null;
    if (row && inDialog && inDialog.contains(row)) {
      row.classList.add("ds-hit");
      var r = row.getBoundingClientRect(), b = body.getBoundingClientRect();
      body.scrollTop += r.top - b.top - Math.max(0, (body.clientHeight - r.height) / 2);
    } else body.scrollTop = 0;
  }

  /* Whatever closes the dialog, the Close button, Esc, the backdrop, Back or the browser itself, ends here. */
  function afterClose() {
    var wasDeep = deep, n = depth;
    putBack();
    document.documentElement.classList.remove("pm-open");
    current = null; depth = 0; deep = false;
    /* The address still names a sheet when the dialog closed by itself, or by Esc or Close. Put it back. */
    if (parse(location.hash)) {
      window.pulseModalClosed = true;
      setTimeout(function () { window.pulseModalClosed = false; }, 300);
      if (n > 0 && !wasDeep) history.go(-n);
      else history.replaceState(null, "", location.pathname + location.search);
    }
    var o = opener; opener = null;
    if (o && document.contains(o)) {
      o.focus({ preventScroll: true });
      /* Going back in history makes the browser drop focus once it has moved to the old address. Give it back after. */
      if (refocus === undefined && parse(location.hash)) { refocus = o; setTimeout(giveFocusBack, 250); }
    }
  }
  var refocus;
  function giveFocusBack() { var o = refocus; refocus = undefined; if (o && !dlg.open && document.contains(o)) o.focus({ preventScroll: true }); }
  dlg.addEventListener("close", afterClose);

  /* The reader closes it: Close, Esc or a click outside. */
  function closeByUser() { if (dlg.open) dlg.close(); }

  /* The address says what should be open. Used for load, Back, Forward and a hand-edited address. */
  function sync(fromLoad) {
    var spec = parse(location.hash);
    if (spec) {
      if (same(spec, current)) return;
      if (fromLoad && !dlg.open) { deep = true; opener = null; }
      var st = history.state;
      depth = st && st.pm ? st.pm : 0;
      show(spec);
    } else if (dlg.open) {
      window.pulseModalClosed = true;
      setTimeout(function () { window.pulseModalClosed = false; }, 300);
      dlg.close();   /* the address is already clean, so afterClose changes nothing in it */
    }
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var spec = fromHref(a.getAttribute("href"));
    if (!spec) return;
    e.preventDefault();
    openSpec(spec, a);
  });
  /* Open a sheet, a definition or a comparison, and add one history entry so that Back closes it. */
  function openSpec(spec, from) {
    if (!dlg.open) { opener = from; depth = 0; deep = false; }
    if (same(spec, current)) return;
    depth += 1;
    history.pushState({ pm: depth }, "", hashOf(spec));
    show(spec);
  }
  closeBtn.addEventListener("click", closeByUser);
  dlg.addEventListener("click", function (e) { if (e.target === dlg) closeByUser(); });
  window.addEventListener("popstate", function () { sync(false); });
  window.addEventListener("hashchange", function () { sync(false); if (refocus) setTimeout(giveFocusBack, 0); });

  /* ---------- Compare 2 or 3 projects ---------- */
  var picks = [];          /* the ids the reader picked, in the order picked */
  var bar = null, barN = null, barOpen = null, boxes = [];

  function nameOfSheet(id) { return sheets[id].querySelector("h3").textContent; }

  /* One table: a column per project, a row per data sheet row, in data sheet order. Each cell is the sheet's own row content,
     copied, so the content is made once. Under 640px the table stacks and each cell carries its project's name. */
  function buildCompare(ids) {
    var wrap = document.createElement("div");
    var names = ids.map(nameOfSheet);
    var h = '<h3 class="visually-hidden" id="pm-cmp-title">Comparing ' + names.join(", ") + '</h3>' +
      '<table class="cmp"><caption class="visually-hidden">Data sheet rows, one column per project.</caption><thead><tr><th scope="col"><span class="visually-hidden">Row</span></th>';
    ids.forEach(function (id, i) {
      h += '<th scope="col"><div class="cmp-h"><a class="proj-open" href="#tc-' + id + '"></a>' +
        '<button type="button" class="cmp-rm" data-id="' + id + '" title="Remove">\u00d7</button></div></th>';
    });
    h += '</tr></thead><tbody></tbody></table>';
    wrap.innerHTML = h;
    wrap.querySelectorAll("thead a.proj-open").forEach(function (a, i) { a.textContent = names[i]; });
    wrap.querySelectorAll(".cmp-rm").forEach(function (b, i) { b.setAttribute("aria-label", "Remove " + names[i] + " from the comparison"); });
    var tbody = wrap.querySelector("tbody");
    sheets[ids[0]].querySelectorAll(".ds-row").forEach(function (row) {
      var key = row.getAttribute("data-col");
      var tr = document.createElement("tr");
      tr.setAttribute("data-col", key);
      var th = document.createElement("th");
      th.scope = "row";
      var dt = row.querySelector("dt").cloneNode(true);
      dt.querySelectorAll(".mx-q").forEach(function (q) { q.remove(); });
      th.textContent = dt.textContent.trim();
      tr.appendChild(th);
      ids.forEach(function (id, i) {
        var td = document.createElement("td");
        var src = document.getElementById("ds-" + id + "-" + key);
        var n = document.createElement("span");
        n.className = "cmp-n"; n.textContent = names[i];
        td.appendChild(n);
        if (src) {
          var dd = src.querySelector("dd").cloneNode(true);
          dd.querySelectorAll("[id]").forEach(function (el) { el.removeAttribute("id"); });
          while (dd.firstChild) td.appendChild(dd.firstChild);
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    return wrap;
  }

  /* Take one project out of the open comparison. Under two projects there is nothing to compare, so it closes. */
  function removeFromCompare(id) {
    if (!current || current.type !== "cmp") return;
    var ids = current.ids.filter(function (x) { return x !== id; });
    picks = picks.filter(function (x) { return x !== id; }); syncPicks();
    if (ids.length < 2) { closeByUser(); return; }
    var spec = cmpSpec(ids);
    history.replaceState(history.state, "", hashOf(spec));
    show(spec);
    body.focus({ preventScroll: true });
  }
  body.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest(".cmp-rm") : null;
    if (b) removeFromCompare(b.getAttribute("data-id"));
  });

  function syncPicks() {
    if (!bar) return;
    var n = picks.length, full = n >= MAXCMP;
    boxes.forEach(function (i) {
      i.checked = picks.indexOf(i.value) !== -1;
      i.disabled = !i.checked && full;
      i.parentNode.title = i.disabled ? "Up to " + MAXCMP + " projects" : "";
    });
    bar.hidden = n === 0;
    bar.classList.toggle("full", full);
    document.documentElement.classList.toggle("cmp-on", n > 0);
    barN.textContent = "Compare " + n + (n === 1 ? " project" : " projects");
    barOpen.disabled = n < 2;
  }

  function initPicks() {
    var rows = document.querySelectorAll("table.mx tbody tr[data-id]");
    if (!rows.length) return;
    rows.forEach(function (tr) {
      var id = tr.getAttribute("data-id"), th = tr.querySelector("th");
      if (!sheets[id] || !th) return;
      var lab = document.createElement("label");
      lab.className = "cmp-pick no-print";
      var inp = document.createElement("input");
      inp.type = "checkbox"; inp.value = id; inp.name = "compare";
      inp.setAttribute("aria-label", "Compare " + nameOfSheet(id));
      var t = document.createElement("span"); t.textContent = "Compare";
      lab.appendChild(inp); lab.appendChild(t);
      th.appendChild(lab);
      boxes.push(inp);
      inp.addEventListener("change", function () {
        picks = picks.filter(function (x) { return x !== id; });
        if (inp.checked && picks.length < MAXCMP) picks.push(id);
        syncPicks();
      });
    });
    bar = document.createElement("div");
    bar.className = "cmp-bar no-print";
    bar.setAttribute("role", "region");
    bar.setAttribute("aria-label", "Compare projects");
    bar.hidden = true;
    bar.innerHTML = '<span class="cmp-bar-n" role="status"></span><span class="cmp-bar-note">Up to ' + MAXCMP + ' projects</span>' +
      '<button type="button" class="btn cmp-open">Open</button><button type="button" class="btn cmp-clear">Clear</button>';
    document.body.appendChild(bar);
    barN = bar.querySelector(".cmp-bar-n"); barOpen = bar.querySelector(".cmp-open");
    barOpen.addEventListener("click", function () { if (picks.length >= 2) openSpec(cmpSpec(picks.slice()), barOpen); });
    bar.querySelector(".cmp-clear").addEventListener("click", function () { picks = []; syncPicks(); });
    syncPicks();
  }

  window.addEventListener("load", function () { if (dlg.open) setTimeout(place, 0); });
  function init() { initPicks(); sync(true); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
