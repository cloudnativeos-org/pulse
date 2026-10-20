One data sheet per entry. It lists every value from the matrix in full, in matrix order, with its evidence label and sources, then two rows the matrix does not carry: what names the OS version (`d04 version_identity`) and the maintainers fact (`maintainers_fact`).

**Provide:** the profile. The header shows its entry kind, then name, owner label and tag, project links, observed version and collection date.

**Layout:** one row per value, the column title on the left and the full value on the right (stacked under 640px). Each row has the id `ds-<entry>-<column>`, so a matrix note tag can link to it. The sheet has the id `tc-<entry>`. A project name links to it (`href="#tc-<entry>"` on the matrix page, `index.html#tc-<entry>` on the guide). With JavaScript the sheet opens in a modal `<dialog>` and the address changes with it, so a sheet or a row can be linked; without JavaScript the sheets stay in the page.

**Do** list every option where a column lists options (Day-0 paths, AI accelerators, fleet paths, Kubernetes ways, configuration tools). Where install modes replace different parts in a fact column, such as Update unit, give each mode as an item.

**Do** follow the capability rule in the two capability rows, Update signature check and Boot trust chain. The matrix cell shows the highest level the entry can reach, marked Opt-in, with the mode or setting that reaches it, when the adopter has to turn it on. The data sheet says three things in the same words on every entry, each with its own sources: Optional or On by default; how far it goes, with which mode or setting; and, for an optional capability, where the default leaves you. When no source says where the default leaves you, the row says so.

**Do** cite, on each row, only the sources recorded for the fields that row shows (`<field>_sources`, or the field's own `sources`). A row whose fields have no source of their own shows no citation, and `check_site.py` lists it.

**Don't** rank, judge, or show `tradeoffs.buys` and `tradeoffs.costs`. Don't show `known_issues` (methodology section 9, rule 20).
