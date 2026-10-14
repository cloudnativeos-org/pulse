# Cloud Native OS Pulse

A sourced comparison of cloud native operating systems.

By Mauro Morales, CNCF Ambassador.

If the Pulse helps you, please star this repository. It helps more people find it.

The Pulse records what each project is, how it handles the machine lifecycle,
and where the designs actually differ, with every factual claim traceable to a
primary source. It is not a benchmark and not a recommendation. Its job is to
give you a good starting point for choosing, and to explain how projects that
look alike differ.

## A rolling release

There are no editions. The site is built from this repository, and every view
says which commit it came from and when it was generated. A script detects
when a project ships a newer release, and the site flags that entry. The profile
moves to the new release only after its claims are re-validated against it,
which is a manual step today: see [docs/REFRESH.md](docs/REFRESH.md).

## Why a dataset and not only an article

The site is an output of this data, not the other way round. Keeping the data
separate buys three things:

1. **A refresh is a diff, not a rewrite.** A new release changes the fields it
   touched, and the history shows what moved.
2. **A correction is a small, reviewable change.** A maintainer who disagrees
   with one claim edits one field in one file, with its source, rather than
   arguing about a paragraph.
3. **Claims are checkable.** Every normalized value carries an evidence label
   and a source URL, and a validator enforces that pairing.

## Layout

```
data/
  projects/<id>.yaml           one profile per project
  versions-check.json          latest release per project, from tools/check_versions.py
  lineage.yaml                 where each OS came from: releases, renames, forks, owners, with sources
schema/
  profile.schema.json          the profile schema (JSON Schema, applied to YAML)
  vocabularies.md              the closed vocabularies, with the meaning of every value
tools/
  validate_profiles.py         schema and consistency validation
  check_versions.py            detects newer releases; never edits a profile
docs/
  methodology.md               inclusion criteria, taxonomy, dimensions, evidence standard, bias controls
  dataset.md                   scope, status and the list of profiles
  REFRESH.md                   how a profile moves to a new release
  maintainer-review.md         the maintainer factual-review plan and per-project questions
  follow-up-research.md        questions the data surfaced but does not answer
research/
  deep-dives/                  rollback experiments run in VMs
  reproducible-machine-state/  the research that preceded the Pulse
site/
  build.py                     builds the static site and its PDF from data/
```

## Build and check

```sh
python3 tools/validate_profiles.py data/projects
python3 tools/check_versions.py data/projects --out data/versions-check.json
python3 site/build.py data/projects site/out
python3 site/check_site.py            # contents, layout and em-dash checks
```

The build writes two pages, `site/out/site/index.html` (the matrix, the data sheets, the sources) and `site/out/site/guide.html` (the guide). A deploy must copy both files. Neither needs another file.

```sh
python3 site/serve.py                 # review server; open pages reload after each build
```

## Found something wrong?

Open a pull request against the project's YAML profile, with the primary source
for the correct value. If you cannot open a pull request, use one of the issue
forms: **Correct a claim** (wrong or out of date), **Propose an OS** (it meets the
five inclusion criteria, with a source for each), or **Propose a change to the
criteria** (say which entries it would add or remove).
Corrections are recorded in the profile's `corrections` list, with the date and
the source, so the change history is visible in the data and not only in git.

Maintainers of any project covered here are invited to correct their own
project's factual profile. The ask is to verify **factual representation** only.
It is not a request to endorse, approve, or agree with any analysis.

## Who is behind it

Mauro Morales, CNCF Ambassador. I am one of the Kairos maintainers and work as a Staff Engineer
for Spectro Cloud, so I cannot be fully unbiased. The site's "How it was made"
section says what I did about that.

AI agents did most of the reading and the first drafts. Commits from the
`mauro-agent` account were made by an AI agent that I operate. I am the person
behind that account and I answer for its work. Every commit names the assisting
model in a `Co-developed-by:` trailer.

## License

- Code (`site/`, `tools/`, `schema/`, and any other software in this repository): [Apache License 2.0](LICENSE).
- Data, documentation and site text (`data/`, `docs/`, `research/`, and the published pages): [Creative Commons Attribution 4.0 International](LICENSE-CC-BY-4.0).

Quotes from project documentation inside the profiles remain the work of their authors and are included to support each claim with its source.
