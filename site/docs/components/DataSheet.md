One data sheet per entry. It lists every value from the matrix in full, in matrix order, with its evidence label and sources, then two rows the matrix does not carry: what names the OS version (`d04 version_identity`) and the maintainers fact (`maintainers_fact`).

**Provide:** the profile. The header shows its entry kind, then name, owner label and tag, project links, observed version and collection date.

**Layout:** one row per value, the column title on the left and the full value on the right (stacked under 640px). Each row has the id `ds-<entry>-<column>`, so a matrix note tag can link to it. The sheet has the id `tc-<entry>`. A project name links to it (`href="#tc-<entry>"` on the matrix page, `index.html#tc-<entry>` on the guide). With JavaScript the sheet opens in a modal `<dialog>` and the address changes with it, so a sheet or a row can be linked; without JavaScript the sheets stay in the page.

**Do** list every option where a column lists options (Day-0 paths, AI accelerators, fleet paths, Kubernetes ways, configuration tools), and every install mode as an equal item.

**Don't** rank, judge, or show `tradeoffs.buys` and `tradeoffs.costs`. Don't show `known_issues` (methodology section 9, rule 20).
