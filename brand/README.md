# Brand

The mark of cloud native OS is two slashes, `//`: one in ink, one in the accent
blue. Pulse is a product of cloud native OS, so it uses the same mark and adds
its name. A later product does the same, with no new logo.

## Files

| File | Use |
|---|---|
| `mark-light.svg` | The mark on a light background |
| `mark-dark.svg` | The mark on a dark background |
| `mark-mono.svg` | One colour, follows `currentColor`. For places that allow a single ink |
| `favicon.svg` | Browser icon. Switches to the dark colours with the system theme |
| `favicon-32.png` | Browser icon for clients that do not read SVG |
| `apple-touch-icon.png` | 180 px home-screen icon, on the light paper background |
| `lockup-parent-light.svg`, `-dark.svg` (and `.png`) | The mark with "cloud native OS" |
| `lockup-pulse-light.svg`, `-dark.svg` (and `.png`) | The mark with a small "cloud native OS" label above "Pulse" |

The lockup SVGs set their text in Public Sans and fall back to a system sans
serif. Where the font cannot be relied on (a README, a slide), use the PNGs,
which are rendered with Public Sans at twice their display size.

The site does not link these files: each page is a single file, so the build
draws the mark inline and embeds `favicon.svg` as a data URI.

## Colours

Taken from the site tokens (`site/tokens.json`).

| | Light | Dark |
|---|---|---|
| First slash (ink) | `#1f2933` | `#e6eaee` |
| Second slash (accent) | `#2b5a84` | `#93bbe0` |
| Label text (ink muted) | `#4f5b67` | `#a8b3bd` |

## Rules

- Keep the two slashes together, in this order: ink first, accent second.
- Do not recolour the mark in a project's or vendor's colours, and do not
  combine it with another organisation's mark.
- Keep clear space around the mark of at least half its height.
- The smallest size is 16 px. Below that the two slashes merge.

## Geometry

On a 24 by 24 grid:

```
first slash   M1 22H5.75L13.25 2H8.5Z
second slash  M10.75 22H15.5L23 2H18.25Z
```
