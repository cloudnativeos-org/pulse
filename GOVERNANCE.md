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

**Profile reviewers** look after the factual profile of one covered project,
`data/projects/<id>.yaml`, and are asked to review every change to it. A
profile reviewer checks facts only. Reviewing a profile does not mean the
project endorses the Pulse or agrees with its analysis. Profile reviewers are
listed in [CODEOWNERS](.github/CODEOWNERS), one slot per project. They come in
two kinds:

- A **representative** works on that project. They are a maintainer or a
  contributor named in the project's own docs.
- An **external steward** has no tie to that project. They look after the
  profile when no representative is interested.

Both kinds can exist for the same project at once. A profile with neither has
the maintainers as its reviewers. No project is forced to have a
representative. Neither kind becomes a maintainer by this role.

**Contributors** are everybody else. Anyone can open a pull request or an issue.

The **owner** and the **administrators** hold the organization and the repository
settings. They are described under Ownership and Administrators below. They do
not decide what goes into the data.

## Affiliations

Every maintainer and every profile reviewer, of either kind, states in
MAINTAINERS.md the projects they work on and the organization that employs them.
An external steward also states any affiliation with a competing or related
project.
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

The rule is symmetric. For every covered project, a conflicted change to its
profile needs approval from a maintainer with no affiliation to that project. A
maintainer who is affiliated with the project cannot give that approval,
however many of them there are. Kairos and Hadron are the worked example
because the only maintainer today is affiliated with both: until a maintainer
without that affiliation exists, the bootstrap section says what applies. A
maintainer who works on Talos does not approve a conflicted change to the Talos
profile either.

A change to `.github/CODEOWNERS` or `MAINTAINERS.md` is always conflicted,
before the bootstrap ends and after it, so that nobody can put themselves back
on the conflicted lines alone. It follows the four rules above, and for the
first 24 months after the bootstrap ends the founder clause also applies.

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
majority of the votes counted decides.

**The vote cap.** Votes from one employer count for at most half of the votes
cast. The excess is not counted. In practice, the votes of one employer are
reduced to the number that everyone else casts together. If all maintainers
work for one employer, no vote can be held, and the bootstrap section says who
decides. The cap applies to every vote in this document.

Removing a maintainer, appointing an administrator or an external steward, and
changing the ownership have their own rules below. The majority rule does not
apply to them.

## Becoming a maintainer

A contributor becomes a maintainer when an existing maintainer proposes them in
a public issue and no maintainer objects within 14 days. A maintainer steps
down by opening a pull request against MAINTAINERS.md.

## Profile reviewers

### Representatives

A person who works on a covered project can become its representative on
request. They open a pull request against CODEOWNERS and MAINTAINERS.md. The
pull request links the project's own docs that name them, for example its
maintainers file or its contributor list. A representative fact-checks the
profile in public, in comments or reviews on the pull request. That is welcome
at any time and does not need a slot.

A representative's fact check is not an approval under the conflict-of-interest
rules. Those rules ask for a maintainer with no affiliation with the project. A
representative is affiliated with it by definition.

### External stewards

An external steward is a person with no tie to the project: they do not work on
it, and no organization that employs them develops, sells or supports it. They
look after the profile when no representative is interested. A steward has
these duties:

1. Every value they change carries a primary source, as for any other project's
   profile.
2. They declare in MAINTAINERS.md any affiliation with a competing or related
   project.
3. They answer a representative's correction in the pull request, before its
   objection window closes. The window is the same as for any other change.
4. They step aside for a representative who appears. The representative takes
   the lead on the profile. The steward leaves the CODEOWNERS line when the
   representative asks, and may stay on it otherwise.

The maintainers appoint an external steward through a public issue that stays
open for 14 days. Any maintainer can object there. A steward never needs a
representative's consent. A steward steps down by opening a pull request
against MAINTAINERS.md, and the maintainers replace one who stops meeting these
duties through the same public issue process.

Both kinds can exist for one project at once. A person can be a representative
of one project and an external steward of another, if they state both
affiliations.

### Who may do what

| Role | Propose a correction | Fact-check | Approve a change to a profile | Vote on governance |
|---|---|---|---|---|
| Representative | Yes | Yes, their project | No | No |
| External steward | Yes | Yes, the profiles they look after | Yes for those profiles, unless the change is conflicted | No |
| Maintainer | Yes | Yes | Yes. A conflicted change needs a maintainer with no affiliation | Yes |
| Administrator | Yes | Yes | As a maintainer | As a maintainer. Admin rights add no vote |
| Owner | Yes | Yes | As a maintainer | As a maintainer, plus the founder clause |

Anyone else can propose a correction in a pull request or an issue.

## Removing a maintainer

An **active** maintainer has reviewed, merged or contributed something in the
last 12 months. A maintainer who is not active is **inactive**. Inactive
maintainers are not counted in any vote.

A maintainer leaves only for a stated cause. There are two.

**Inactivity.** This is not a vote. When a maintainer has been inactive for 12
months, any maintainer opens a public issue that names them and tries to reach
them. If they have not answered and have done nothing 30 days after that issue,
they move to the emeritus list. An emeritus maintainer who asks to come back
becomes a maintainer again if no maintainer objects within 14 days.

**A breach of the code of conduct.** The code of conduct is the Contributor
Covenant, version 2.1, named by its version. The Pulse does not write its own.
This cause cannot be used until the repository has a `CODE_OF_CONDUCT.md` file
that names that version. Changing the version is a change to the protected text
(see the founder clause).

A removal for a breach goes through a public issue that names the cause and the
evidence. The issue stays open for at least **30 days**, and the person
concerned can answer in it. A removal needs the votes of at least **two
thirds** of the active maintainers other than the person concerned, rounded up.
The vote cap applies.

A vote that says only that the others no longer want a person removes nobody.
A cause has to be stated and shown.

With fewer than two active maintainers besides the person concerned, no vote is
held. Then the owner and one other maintainer together can remove a maintainer,
for a breach of the code of conduct only, after the same 30-day public issue.
The owner cannot be removed this way. With fewer than two other active
maintainers, nobody can remove the owner from a role.

## Ownership

Mauro Morales is the owner of the GitHub organization `cloudnativeos-org` and
of this repository, and he stays the owner. Maintainers get write access to the
repository. They never get the owner role.

The owner may name one second owner whom he trusts, so that a lost account does
not lock the organization. This document calls that person a second owner
chosen by the owner. The second owner is an owner with full access. That they
do not remove the owner, and do not change this section, is a rule and not a
technical limit. When a second owner is named, MAINTAINERS.md lists their name
and handle.

Maintainers and administrators cannot remove the owner from the ownership of
the organization or the repository. Only the owner gives up that role.

**Only the owner changes this section, by a pull request that he opens or
approves. This does not lapse.** The rules in "Changes to this document" do not
apply to it.

## Administrators

An administrator has admin rights on the repository. An administrator is never
an owner of the organization. These facts about GitHub are taken from GitHub's
documentation. They were not tested on this organization:

- The admin role is full access to the repository. It includes sensitive and
  destructive actions, such as managing security settings or deleting the
  repository.
- An administrator can merge a pull request into a protected branch even
  without the approving reviews that the branch rules ask for, unless the rules
  cannot be bypassed.
- Whether members can delete or transfer repositories is an organization
  setting.

So the owner keeps three things set. The organization setting "Allow members to
delete or transfer repositories" is off. The rules for `main` cannot be
bypassed by administrators. Nobody relies on a CODEOWNERS line alone to stop an
administrator, because it does not bind one.

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
same public process, with one exception.

- Admin rights end on the same day a person stops being a maintainer or moves to
  the emeritus list.
- In an emergency, such as abuse or a compromised account, the owner removes an
  administrator's rights at once. He records the reason in a public issue
  afterwards.
- Administrators cannot remove the owner, and they cannot change the Ownership
  section.

## Founder clause

The **protected text** is:

- the Ownership, Administrators, Removing a maintainer and Founder clause
  sections;
- the section "Changes to this document";
- the vote rules in "Decisions", including the vote cap;
- the choice of code of conduct.

For the first 24 months after the bootstrap ends, two things need the owner's
agreement: any change to the protected text, and removing the owner from any
role. "Needs the owner's agreement" means an approving review from the owner on
the pull request.

The clause is not in force during the bootstrap. The owner merges then, so
nothing changes without him. The clause lapses on its own 24 months after the
day recorded in the Bootstrap section. It needs no vote and no change to this
document. The Ownership section is not part of the clause and does not lapse:
only the owner changes it.

GitHub cannot enforce this clause. CODEOWNERS accepts any one owner on a line,
and after the hand-over the line names the maintainer with no affiliation. So
the clause rests on one thing: the owner's power as organization owner to
revert a change that was made without his review. The same holds for
MAINTAINERS.md.

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
allowed to approve a change to the Kairos and Hadron profiles.

The bootstrap does not end by itself, and nobody else can end it. It ends on the
day a pull request that records that day in this section, approved by the
owner, is merged. From then on, the decision rules above apply in full, and
this section is reduced to a record of when the bootstrap ended.

Bootstrap ended on: not yet.

## Changes to this document

A change to this document is treated like a change to the methodology: it
follows the conflict-of-interest rules above, whoever writes it. A change to the
protected text also follows the founder clause. A change to the Ownership
section follows only that section: the owner opens or approves it.
