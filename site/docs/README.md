The Pulse is a sourced comparison of cloud native operating systems. It has no score and no winner. This system exists so that the HTML report and its PDF look like one calm technical reference, and so that no project gets a visual advantage.

## Principles

1. **Every claim shows where it came from.** A matrix cell carries an evidence badge and a citation. A data sheet or pair says which profile fields it came from. Nothing is drawn without a source or a stated derivation.
2. **No project gets a visual advantage.** No logos, no project or vendor colours, no highlighted row. Rows sort alphabetically by name, in one list. Every entry gets the same components in the same order.
3. **The three kinds of "no" never look alike.** `None` (documented absence), `Unknown` (not determined) and `not applicable` each have their own rendering. A new field with no data reads `Not collected`, never `No`.
4. **Plain, dense, calm.** Hairlines, not shadows. One tint in the whole system, and it marks review state, not a project.

## Content fundamentals

- **Voice.** Plain declarative sentences. The method and disclosure sections speak in Mauro's first person ("I maintain Kairos"). Everything else is impersonal and describes the projects, never the reader's choice.
- **Never answer with a project.** A "start here" block routes to dimensions and matrix filters. Lines such as "best for edge" or "choose X if" are not written anywhere (methodology section 8).
- **Punctuation.** No em dashes in any copy. Use a full stop, a comma, a colon or parentheses. Avoid filler: "worth stating", "plainly", "genuinely", "in this survey".
- **Case.** Sentence case for headings and buttons. Uppercase only through `t-eyebrow` (section labels, pending header).
- **Project names.** Exactly as the profile's `name` field writes them (`AWS Bottlerocket`, `openSUSE MicroOS`). Sorting uses the same string, case-insensitive.
- **Dates.** In running text and stamps: `22 Sep 2026`. In data and version cells, ISO in `t-mono`: `2026-09-22`.
- **Numbers.** Digits for counts and versions. Units with a space: `90 days`.
- **No emoji, no icons.** Meaning comes from words plus a small set of typographic glyphs (see Iconography).
- **Public output.** No link, name or path to a private repository, tracker or ticket. Placeholders such as `[PUBLIC DATASET LINK]` stay visible until replaced.

## Visual foundations

### Colour

Slate ink on near-white paper, one interface accent, section bands, and one review tint.

- Page ground is `paper`. Tables and filter bars sit on `paper-sunk`. Cards and boxes sit on `paper-raised`.
- Text is `ink`, a cool slate rather than black, so long tables stay calm. Secondary text is `ink-muted`. Both hold 5.7:1 or more on every surface in every theme.
- `accent` is for the interface only: links, citations, sort state, active filters, the Start here numbers, focus. It never colours a project, a value or a row by meaning. Text on a solid accent fill uses `on-accent`.
- `accent-soft` grounds the Bring your own distro column and the hovered row.
- **Section bands** give each part of the report its own ground, full width: `band-cool` for reader routes (Start here), `band-warm` for the project data sheets, `paper-sunk` for the method. The pair and the matrix sit on plain `paper`.
- **Zebra rows:** every second matrix row uses `row-alt`, so the eye can follow one entry across thirteen columns.
- Hairlines are `rule`. Anything that carries meaning (an exception badge, a chip, a control) uses `rule-strong`, 3:1 or more on every surface.
- `flag-bg`, `flag-ink` and `flag-rule` are the review tint: the illustrative banner and Fact-fix flags only.

**Quiet defaults, loud exceptions.** Documented is the most common evidence label, so its compact badge has no border: a small glyph in `ink-muted`. Inferred, Unknown and Not tested keep their borders, so the cells that need care are the ones that stand out.

Three themes: **Light**, **Dark** and **Print**. The page header has a System / Light / Dark switch, remembered per reader; System follows `prefers-color-scheme`. Print is black on white with grey rules and no bands.

### Type

- `sans` (Public Sans) for headings, tables, labels and controls.
- `serif` (Source Serif 4) for prose and pair text: the reading voice.
- `mono` (Source Code Pro) for versions, field paths and ISO dates.
- Styles: `t-title` once per page, `t-h2` per section, `t-h3` per card. Matrix cells use `t-cell`; citations and dates use `t-meta`. Prose uses `t-prose` at a 68ch measure.

All three faces load from Google Fonts. Fallbacks are system faces of the same class.

### Space, radius, borders

- A 4px base: `space-1` 4, `space-2` 8, `space-3` 12, `space-4` 16, `space-6` 24, `space-8` 32, `space-12` 48.
- Cell padding is `space-2`. Card padding is `space-4`. Sections are `space-12` apart.
- `radius-0` for tables and rows, `radius-1` for badges and chips, `radius-2` for cards. Nothing is rounder.
- No shadows. Separation comes from `rule` hairlines and the paper steps.
- Focus: a 2px solid `focus` outline with a 2px offset on every interactive element.

### Layout and rhythm

- The page is one column, max 1240px, with a 24px gutter (16px under 640px). The matrix breaks out to 1760px and scrolls horizontally inside its own frame, with the entry column pinned.
- **Break the "table, then a paragraph per entry" rhythm.** The report leads with pairs, then reader routes, then the matrix, then data sheets. Deep prose follows the matrix as dimension sections, not as one paragraph per project.
- Two cards or boxes may sit side by side (`.two`); below 900px they stack.

## Evidence and values

Use the `EvidenceBadge` for every label in the schema's vocabulary: Documented, Inferred, Unknown, Not tested, Reproduced, Observed. Each badge is a glyph shape plus a word, so it reads in greyscale and to a screen reader. In matrix cells use the compact form; the full word stays in the accessible name.

Use `CellValue` for every cell. `v-none` for a documented absence, `v-unknown` for undetermined, `v-na` for a concept that does not apply, `v-notcollected` for a new field without data. Do not write "No" when the profile says `unknown`.

When a value is derived by the generator rather than read from a field, label it Inferred and say what it was derived from (in the column note or the cell detail).

## Iconography

No icon set and no logos. A short list of typographic glyphs, always next to a word:

| Glyph | Meaning |
|---|---|
| filled square | Documented |
| half-filled square | Inferred |
| `?` in a dashed box | Unknown |
| hollow circle, dotted box | Not tested |
| `∅` | None, a documented absence |
| `n/a ·` | Does not apply |
| `→` | A route to a filter or dimension |
| `!` in a circle | Fact-fix flag |

CNCF marks are not used. The byline reads "CNCF Ambassador" in plain text.

## Neutrality rules

- One alphabetical list, no groups. Sorting by a column is the reader's choice and resets on reload.
- Distinctions between entries are columns with sourced values, never group headers or sections. Bring your own distro is a column for that reason.
- Entries outside the lead matrix go in the `ContextBox` with their own category note, never as a footnote.
- An entry the authors maintain is treated like every other: same components, same order, same flags.
- An approved entry with no profile appears as a pending row and claims nothing.

## Output targets

One generator (`build.py`) reads the YAML profiles and writes a single static HTML file. No server, no runtime data fetch. The PDF is the same HTML printed through its print CSS:

- A4 portrait; the matrix section switches to A4 landscape (`@page wide`).
- Running header: title on the left, "Data as of" date on the right. Footer: the illustrative note and "Page n of m".
- The matrix header row repeats on every page; rows never split; filters, sort arrows and review notes are hidden; all rows print, whatever the screen filter.
- Citations print with their full URL in the source list.

## Review-only parts

The `ReviewControls` toggle, `review` notes and Fact-fix flags exist for the review of the proposed structure. They are hidden in print, and the public build drops them.
