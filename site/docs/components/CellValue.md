How a matrix value renders, including the three kinds of "no" from the schema.

**Provide:** a kind and a short text, optionally a detail line.

| Kind | Class | Renders |
|---|---|---|
| value | `v` | the normalized value |
| none | `v-none` | `∅ No`: documented absence, has a source |
| unknown | `v-unknown` | `? Unknown`, italic |
| not-applicable | `v-na` | `n/a ·` then the reason, muted |
| not collected | `v-notcollected` | dotted underline, muted: a new field with no data |

**Do** keep the detail line to one clause. **Don't** turn `unknown` into "No", or leave a cell blank.
