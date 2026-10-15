# Governance

The cloud native OS Pulse compares projects, and the person who runs it,
Mauro Morales, maintains two of them. This document says who owns the Pulse, who decides what goes into it,
how, and what stops that person from tilting the data toward his own projects.
It also says what protects every maintainer, the owner included, from being
removed without a cause.

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

The **owner** and the **administrators** hold the organization and the repository
settings. They are described under Ownership and Administrators below. They do
not decide what goes into the data.

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

The rule is symmetric. It holds for every covered project and for every
maintainer. No maintainer is the only approver of a change to the profile of a
project they are affiliated with. Kairos and Hadron are the worked example
because the only maintainer today is affiliated with both: until a maintainer
without that affiliation exists, the bootstrap section says what applies. A
maintainer who works on Talos could not alone approve a change to the Talos
profile either.

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

Removing a maintainer, appointing an administrator and changing the ownership
have their own rules below. The majority rule does not apply to them.

## Becoming a maintainer

A contributor becomes a maintainer when an existing maintainer proposes them in
a public issue and no maintainer objects within 14 days. A maintainer steps
down by opening a pull request against MAINTAINERS.md.

A person who works on a covered project becomes a profile reviewer for that
project on request, through a pull request against CODEOWNERS. They do not have
to become a maintainer.

## Removing a maintainer

A maintainer is removed only for a stated cause. There are two causes:

1. A breach of the code of conduct that this repository publishes. The code of
   conduct is a separate file. Until it exists, this cause cannot be used.
2. Twelve months without activity: no review, no merge and no other
   contribution in that time. The maintainer moves to the emeritus list.

A removal goes through a public issue that names the cause and the evidence.
The issue stays open for at least **30 days**, and the person concerned can
answer in it. A removal needs the votes of **two thirds** of the maintainers,
not counting the person concerned. The limit of half the votes for one
organization applies here too.

A vote that says only that the others no longer want a person removes nobody.
A cause has to be stated and shown.

## Ownership

Mauro Morales is the owner of the GitHub organization `cloudnativeos-org` and
of this repository, and he stays the owner. Maintainers get write access to the
repository. They never get the owner role.

The owner may name one second owner whom he trusts, so that a lost account does
not lock the organization. This document calls that person a second owner
chosen by the owner. The second owner is there to recover the organization.
They do not remove the owner, and they do not change this section.

Maintainers and administrators cannot remove the owner from the ownership of
the organization or the repository. Only the owner gives up that role. A change
to this section follows the rules in "Changes to this document" and the
founder clause below.

## Administrators

An administrator has admin rights on the repository: settings, branch
protection and access. An administrator is never an owner of the organization.

Administrators come from the maintainers who have shown skin in the game after
proven maintainership work. A maintainer can be proposed as an administrator
when all three of these are true:

1. They have been a maintainer for at least 12 months.
2. They have reviewed or merged changes to the profiles of more than one
   project.
3. They have no unresolved conflict-of-interest issue.

The owner appoints an administrator after a public issue that has stayed open
for 14 days. Anyone can object in that issue, and the owner answers each
objection there. An administrator steps down by opening a pull request against
MAINTAINERS.md. The owner adds or removes an administrator only through the
same public process.

Administrators cannot remove the owner, and they cannot change the Ownership
section.

## Founder clause

For the first 24 months after the day the bootstrap ends, two things need the
owner's agreement as well as the votes they would need otherwise:

- removing the owner from any role;
- changing the Ownership, Administrators or Removing a maintainer sections.

The clause then lapses on its own, with no vote and no change to this document.
The Bootstrap section records the day the bootstrap ended, and the 24 months
count from that day.

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
Cloud, and at least one of whom has no affiliation with Kairos, Hadron or
Spectro Cloud. Without that last condition the bootstrap could end with nobody
allowed to approve a change to the Kairos and Hadron profiles. From then on, the
decision rules above apply in full, and this section is reduced to a record of
when the bootstrap ended.

Bootstrap ended on: not yet. Whoever closes the bootstrap writes the date here.

## Changes to this document

A change to this document is treated like a change to the methodology: it
follows the conflict-of-interest rules above, whoever writes it. For the first 24
months after the bootstrap ends, a change to the Ownership, Administrators or
Removing a maintainer sections also needs the owner's agreement: see the
founder clause.
