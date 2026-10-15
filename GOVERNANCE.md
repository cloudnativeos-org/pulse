# Governance

The cloud native OS Pulse compares projects, and the person who runs it,
Mauro Morales, maintains two of them. This document says who decides what goes into the Pulse,
how, and what stops that person from tilting the data toward his own projects.

## When these rules apply

The Pulse is in preview, and Mauro is still reviewing it himself. During the
preview, changes are merged without the conflict-of-interest process below.
The rules in this document take effect when the preview ends. That day, the
`main` branch is protected so that the rules are enforced by GitHub, not only
written down, and the date is recorded here.

## Not a CNCF project

**The cloud native OS Pulse is not a CNCF project.** It is not hosted, owned or
endorsed by the Cloud Native Computing Foundation. Its author is a CNCF
Ambassador, and that role gives the Pulse no standing with the CNCF.

## Roles

**Maintainers** decide what is merged, and they own the methodology, the schema,
the tools and the site. The current list is in [MAINTAINERS.md](MAINTAINERS.md).

**Profile reviewers** are people who work on a project the Pulse covers. A
profile reviewer checks the factual profile of that project,
`data/projects/<id>.yaml`, and is asked to review every change to it. A profile
reviewer checks facts only. Reviewing a profile does not mean the project
endorses the Pulse or agrees with its analysis. Profile reviewers are listed in
[CODEOWNERS](.github/CODEOWNERS), one slot per project.

**Contributors** are everybody else. Anyone can open a pull request or an issue.

## Affiliations

Every maintainer and every profile reviewer states, in MAINTAINERS.md, the
projects they work on and the organization that employs them.
An affiliation is any project in the Pulse that a person maintains, contributes
to as part of their job, or is paid to promote. A person is also affiliated with
every project that their employer develops, sells or supports, whether or not
they work on it themselves.

## Conflict of interest

A change is **conflicted** when it touches the profile of a project that the
author or the merging maintainer is affiliated with, or an entry about that
project in another file that states facts about projects. Any file that states
a fact about a project counts, whether or not it is listed. Today the listed
files are `data/lineage.yaml`, `site/projects_meta.yaml`, `site/content.py` (the
written comparisons) and `site/drafts/base_choice.yaml`. A conflicted change:

1. Goes through a public pull request. Nobody pushes it directly to `main`.
2. Carries the `conflict-of-interest` label.
3. Stays open for at least **7 days** after the label is added, so that anyone
   can object. An objection with a primary source blocks the merge until it is
   resolved, or until the profile records the disagreement with both sources.
4. Needs approval from a maintainer who has no affiliation with that project,
   once such a maintainer exists. Until then, the 7 days and the public record
   are the only safeguard, and the bootstrap section below says so.

A change by an affiliated author to the profile of a project they are not
affiliated with, for example a Kairos maintainer who edits the Talos profile,
is not conflicted. Every value it changes must carry a primary source, and the
pull request states the author's affiliations. Without that rule, nobody could
keep the other profiles current while the Pulse has one maintainer.

A change to the methodology, the inclusion criteria, the schema or the
vocabularies affects every project at once. It carries the
`conflict-of-interest` label and is announced in the pull request description,
whoever writes it. When it changes a value that any profile shows, it also
follows rules 3 and 4.

A change that only fixes a typo or the formatting of a field, or that replaces
a broken source URL with the same document at a new address or an archived
copy, is not conflicted, as long as what the field says does not change. The
pull request says why it qualifies.

## Decisions

These rules apply once the bootstrap below has ended. Until then, the
bootstrap section says who decides.

Maintainers decide by lazy consensus. A pull request that has the approvals it
needs, and no open objection, is merged. When maintainers disagree, the
majority of maintainers decides. No organization may cast more than half of
the votes in one decision, however many of its employees are maintainers.

## Becoming a maintainer

A contributor becomes a maintainer when an existing maintainer proposes them in
a public issue and no maintainer objects within 14 days. A maintainer steps
down by opening a pull request against MAINTAINERS.md. A maintainer who has not
reviewed or merged anything for 12 months is moved to an emeritus list.

A person who works on a covered project becomes a profile reviewer for that
project on request, through a pull request against CODEOWNERS. They do not have
to become a maintainer.

## Bootstrap

Today the Pulse has one maintainer: Mauro Morales. He is one of the maintainers
of Kairos and of Hadron Linux, two projects the Pulse covers, and he is employed
by Spectro Cloud. So today, nobody without an affiliation reviews the Kairos and
Hadron profiles before they are merged. The 7-day window and the
`conflict-of-interest` label make each such change public. They do not make it
independent.

During the bootstrap:

- Mauro merges pull requests.
- Every change to `data/projects/kairos.yaml` or `data/projects/hadron.yaml` is
  conflicted, and so is every change to an entry about Kairos, Hadron or Spectro
  Cloud in `data/lineage.yaml`, `site/projects_meta.yaml`, `site/content.py` or
  `site/drafts/base_choice.yaml`. That includes corrections that Mauro did not
  write but merges.
- A change to `.github/CODEOWNERS` or `MAINTAINERS.md` is conflicted too, so
  that Mauro cannot put himself back on these lines alone after the hand-over.
- The first maintainer who has no affiliation with Kairos, Hadron or Spectro
  Cloud replaces Mauro as the required approver of the Kairos and Hadron
  profiles, of the conflicted entries in the files above, of the methodology and
  the schema, and of `.github/CODEOWNERS`, `MAINTAINERS.md` and this document.
- Mauro proposes the new maintainers, so he picks the people who will oversee
  him. Each proposal is a public issue, open 14 days, and anyone can object to
  it there.

**The bootstrap ends** when the Pulse has at least two maintainers besides Mauro,
who work on two different projects, and neither of whom is employed by Spectro
Cloud. From then on, the decision rules above apply in full, and this section is
reduced to a record of when the bootstrap ended.

## Changes to this document

A change to this document is treated like a change to the methodology: it
follows the conflict-of-interest rules above, whoever writes it.
