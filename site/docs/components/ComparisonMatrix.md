The lead comparison table: one alphabetical list with one row per core entry, sortable and filterable on screen, static and paged in print.

**Provide:** the profiles. `build.py` renders every cell from normalized fields. Each cell gets a `CellValue`, a compact `EvidenceBadge` and a `SourceCitation`.

**Structure**
- `.mx-wrap` (with an `id`, used for URL state) holds the filter bar `.mx-bar`, the scroll frame `.mx-scroll` and the legend.
- `thead`: one `th` per column with a sort button and a `.th-note` naming the dimension. A column whose field is new or derived gets `class="proposed"`; its note starts "New field".
- One `tbody` with every profiled entry, alphabetical by name, then a hidden empty-state row. A second block (`PendingRows`) holds approved entries without a profile.
- No group headers. The `ByodColumn` carries the distinction between entries that adapt to a base you bring and entries that ship their own.
- Rows carry `data-f<key>` values for filters.

**States**
- Default: alphabetical by name; the entry column shows `aria-sort="ascending"`.
- Sorted: click a header; again to reverse. Reload returns to alphabetical.
- Filtered: chips are OR inside a fieldset and AND across fieldsets. The status line reads "n of m entries match"; if nothing matches, the empty row shows. Pending rows hide while any filter is on.
- URL state: `#matrix?rollback=yes&arch=arm64` presets filters; `#matrix?col=update` scrolls to a column. Start-here links use this.
- Print: filters hidden, every row printed, header repeated per page, landscape page.

**Do**
- Keep cells short: one normalized value, at most one detail line.
- Keep the first column pinned on screen.

**Don't**
- No ticks or crosses unless the property is binary and precisely defined.
- No highlighted row, no default sort by any value column, no totals or scores.
