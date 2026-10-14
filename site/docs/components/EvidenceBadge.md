A small bordered tag that names the evidence label of a claim: one per label in the schema vocabulary.

**Provide:** the label (`DOCUMENTED`, `INFERRED`, `UNKNOWN`, `NOT_TESTED`, `REPRODUCED`, `OBSERVED`).

**Never colour alone.** Each badge is a glyph plus a word:
- Documented: filled square
- Inferred: half-filled square
- Unknown: `?`, dashed border
- Not tested: hollow circle, dotted border
- Reproduced: filled square with an inner ring
- Observed: filled circle

**Variants:** full (word) for legends and prose; compact (three letters) inside matrix cells. In the compact form, Documented drops its border and goes to `ink-muted`, because it is the default; every other label keeps its border. The compact form keeps the full word in its tooltip and accessible name.

**Don't** recolour a badge per label, or drop the word.
