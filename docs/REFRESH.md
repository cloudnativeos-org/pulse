# Refreshing a profile to a new release

The Pulse is a rolling release. A project ships a new version, and the profile
should follow. But a version number is not data on its own: every claim in the
profile was checked against the old version. So a profile moves to a new
version only together with a re-validation of its claims against that version.

## 1. Detect

```sh
python3 tools/check_versions.py data/projects --out data/versions-check.json
```

The script asks each project's own release channel for its latest version and
writes one record per entry: observed, latest, `newer`, method, check time. It
never edits a profile. Entries with no machine-readable channel show `manual`:
check those by hand, using the `method` text in the profile's
`version_observed`.

The site reads `versions-check.json` and shows a "Newer release ... Not yet
re-validated" badge on every entry with `newer: true`. Commit the file, so the
badge is visible until the refresh lands.

## 2. Re-validate

One profile at a time, on its own branch and pull request. Give the agent (or
do by hand) this brief:

> Re-validate `<id>.yaml` against `<project> <new version>`. Read the release
> notes between the observed version and the new one. For every dimension,
> check whether a claim changed: re-open each cited source, compare it to the
> claim and to the new version, and update the value, evidence label and
> source where it changed. Do not change a claim the release did not touch.
> Record every change as a dated entry in `corrections`, with its source. Then
> update `version_observed` (version, released date, method) and the dimension
> `retrieved` dates you re-checked. Run `validate_profiles.py`. List what
> changed and what you could not re-check.

Then run an independent check: a second pass, given the changed profile and
the sources but not the first pass's reasoning, re-reads every changed claim.

## 3. Land

- `validate_profiles.py` passes with 0 errors.
- The pull request lists every changed claim with its source.
- Re-run the version check, so the badge for that entry clears.
- Rebuild the site. The header shows the new commit and date.

A version bump without step 2 does not land.
