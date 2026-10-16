# Governance

The cloud native OS Pulse compares projects, and the person who runs it,
Mauro Morales, maintains two of them. This document says who owns the Pulse,
who decides what goes into it, how, and what stops that person from tilting the
data toward his own projects. It also says what protects a maintainer from
being removed without a cause. The owner has a stronger protection: the owner
role cannot be taken away by a vote, and the founder clause adds more for 24
months. The owner started the Pulse, and the organization and the repository
are his.

## When these rules apply

The Pulse is in preview, and Mauro is still reviewing it himself. During the
preview, changes are merged without the conflict-of-interest process below.
The rules in this document take effect when the preview ends. That day, the
`main` branch is protected so that GitHub enforces code owner approval, and the
date is recorded here. The bootstrap described below starts on the day the
preview ends.

Preview ended on: not yet.

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
listed in [MAINTAINERS.md](MAINTAINERS.md). They are not listed in CODEOWNERS:
their reviews are requested by hand. They come in two kinds:

- A **representative** works on that project. They are a maintainer or a
  contributor named in the project's own docs.
- An **external steward** has no affiliation with any covered project. They look
  after the profile when no representative is interested.

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
An affiliation is any project in the Pulse that a person maintains, contributes
to as part of their job, or is paid to promote. A person is also affiliated with
every project that their employer develops, sells or supports, whether or not
they work on it themselves. A **covered project** is a project that has a profile
in `data/projects/`.

## Conflict of interest

A change is **conflicted** when it touches the profile of a project that the
author or the merging maintainer is affiliated with, or an entry about that
project in another file that states facts about projects. Any file that states
a fact about a project counts, whether or not it is listed. Today the listed
files are `data/lineage.yaml`, `site/projects_meta.yaml`, `site/content.py` (the
written comparisons) and `site/drafts/base_choice.yaml`. Mauro decided to list
these files, although it makes his own changes harder, because readers who find
facts they can check will trust the Pulse little by little. A conflicted change:

1. Goes through a public pull request. Nobody pushes it directly to `main`.
2. Carries the `conflict-of-interest` label.
3. Stays open for at least **7 days** after the label is added, so that anyone
   can object. An objection with a primary source blocks the merge until it is
   resolved, or until the profile records the disagreement with both sources.
   That includes an objection from the project's representative.
4. Needs approval from a maintainer who has no affiliation with that project,
   once such a maintainer exists. Until then, the 7 days and the public record
   are the only safeguard. During the bootstrap, the Bootstrap section below
   says so too.

The rule is symmetric. For every covered project, a conflicted change to its
profile needs approval from a maintainer with no affiliation to that project. A
maintainer who is affiliated with the project cannot give that approval,
however many of them there are. Kairos and Hadron are the worked example
because the only maintainer today is affiliated with both: until a maintainer
without that affiliation exists, rule 4 says what applies, and during the
bootstrap the Bootstrap section adds its own rules. A maintainer who works on
Talos does not approve a conflicted change to the Talos profile either.

GitHub does not enforce the symmetric rule. GitHub enforces only that a code
owner approves. The symmetric rule rests on the maintainers and the public
record.

A change to `.github/CODEOWNERS` or `MAINTAINERS.md` is always conflicted,
before the bootstrap ends and after it, so that nobody can put themselves back
on the conflicted lines alone. It follows the four rules above, and for the
first 24 months after the bootstrap ends the founder clause also applies to
the protected text in them.

A change to a profile by an author, or with an approver, who is affiliated with
any covered project is conflicted under all four rules, even when it changes
the profile of a project they are not affiliated with. Editing a competitor is
as conflicted as editing your own project, for example a Talos maintainer who
edits the Kairos profile. Every value it changes must carry a primary source,
and the pull request states the author's affiliations. When the author is
affiliated with any covered project, rule 4 asks for approval from a maintainer
with no affiliation with any covered project. A Talos maintainer cannot approve
a Bottlerocket maintainer's edit to the Kairos profile.

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
work for one employer, no vote can be held. During the bootstrap, the Bootstrap
section says who decides. After it, no vote is held and a change that needs a
vote is not merged. The cap applies to every vote in this document, including
during the bootstrap.

Becoming a maintainer, removing a maintainer, appointing an administrator or an
external steward, and changing the ownership have their own rules below. The
majority rule does not apply to them.

## Becoming a maintainer

A contributor becomes a maintainer when an existing maintainer proposes them in
a public issue that stays open for 14 days and no maintainer objects. One
maintainer's objection is a veto. The objection and the answer stay in the
issue. A maintainer steps down by opening a pull request against
MAINTAINERS.md.

## Profile reviewers

### Representatives

A person who works on a covered project can become its representative on
request. They open a pull request against MAINTAINERS.md that adds a row. The
pull request links the project's own docs that name them, for example its
maintainers file or its contributor list.

A maintainer requests the representative's review by hand on every pull request
that changes that profile, and the request is recorded in the pull request. A
representative can also fact-check at any time, in public, in comments or
reviews. An objection from a representative that cites a primary source blocks
the change, as in rule 3 of the conflict-of-interest rules.

Representatives are not code owners. GitHub requires code owners to have write
access, and one code owner on a line is enough for GitHub. A code owner's
approval would then count as the approval of the profile.

A representative's fact check is not an approval under the conflict-of-interest
rules. Those rules ask for a maintainer with no affiliation with the project. A
representative is affiliated with it by definition.

### External stewards

An external steward has no affiliation with any covered project. They do not
work on one, and no organization that employs them develops, sells or supports
one. They look after a profile when no representative is interested. A steward
has these duties:

1. Every value they change carries a primary source, as for any other project's
   profile.
2. They declare in MAINTAINERS.md the organization that employs them and any
   tie to a project outside the Pulse that competes with or relates to the
   covered project.
3. They answer a representative's correction in the pull request, before its
   objection window closes. The window is the same as for any other change.
4. They step aside for a representative who appears. The representative takes
   the lead on the profile. The steward stays on the list in MAINTAINERS.md, or
   leaves it when the representative asks.

The maintainers appoint an external steward through a public issue that stays
open for 14 days. One maintainer's objection is a veto. A steward never needs a
representative's consent. Stewards are not code owners, for the same reason as
representatives. A steward steps down by opening a pull request against
MAINTAINERS.md. The maintainers replace one who stops meeting these duties
through the same public issue process.

Both kinds can exist for one project at once. A representative of one covered
project is affiliated with it, so they cannot be an external steward of another.

### Who may do what

| Role | Propose a correction | Fact-check | Approve a change to a profile | Vote on governance |
|---|---|---|---|---|
| Representative | Yes | Yes, their project | No | No |
| External steward | Yes | Yes, the profiles they look after | No. Their review is requested and recorded. A maintainer approves and merges | No |
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
becomes a maintainer again if no maintainer objects within 14 days. The owner is
exempt: the 12-month rule does not move the owner to the emeritus list. The
owner holds the organization, and a role that could be lost by being quiet
would let anyone take over the Pulse by waiting.

**A breach of the code of conduct.** The code of conduct is the Contributor
Covenant, version 2.1, named by its version. The Pulse does not write its own.
This cause cannot be used until the repository has a `CODE_OF_CONDUCT.md` file
that names that version. Changing the version is a change to the protected text
(see the founder clause).

A removal for a breach needs all three of these:

1. A public issue that names the cause and the evidence. It stays open for at
   least **30 days**, and the person concerned can answer in it.
2. A written finding of a breach from the enforcement contact named in
   `CODE_OF_CONDUCT.md`, or from an outside person named in MAINTAINERS.md.
   Neither of them is a maintainer, neither has an affiliation with any covered
   project, and neither votes in the removal. Naming or replacing either one
   follows the rule for becoming a maintainer: a public issue open for 14 days,
   and one maintainer's objection is a veto. Both are protected text.
3. The votes of at least **two thirds** of the active maintainers other than the
   person concerned, rounded up. The two thirds are counted against that whole
   group, not against the votes cast. The vote cap applies, so the yes votes of
   one employer are reduced as described under Decisions.

Residual risk. More than one third of them can block any removal. Two
employers acting together can reach two thirds. The written finding is the
check on that: they cannot remove anyone without it.

A vote that says only that the others no longer want a person removes nobody.
A cause has to be stated and shown.

With fewer than two active maintainers other than the person concerned, no vote
can be held and nobody is removed. That includes the case of exactly two
maintainers in all: the owner alone cannot remove the other one. The remedy is
to appoint another maintainer first.

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
apply to it. No other section limits or overrides this section.

## Administrators

An administrator has admin rights on the repository. An administrator is never
an owner of the organization. These facts about GitHub are taken from GitHub's
documentation. They were not tested on this organization:

- The admin role is full access to the repository. It includes sensitive and
  destructive actions, such as managing security settings or deleting the
  repository.
- Branch protection rules do not apply to administrators by default. A setting
  can stop them from bypassing the rules, but an administrator can switch
  repository rules off. Only an organization-level ruleset stops an
  administrator. Owners manage it, and so do users with the permission "Manage
  organization ref update rules and rulesets".
- Whether members can delete or transfer repositories is an organization
  setting.

So the owner must set two things (not yet verified). The organization setting
"Allow members to delete or transfer repositories" must be off. An
organization-level ruleset must protect `main`, and administrators must not be
able to bypass it. Whether the organization's plan has rulesets is not
verified. Nobody relies on a CODEOWNERS line alone to stop an administrator,
because it does not bind one.

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
MAINTAINERS.md. The owner adds an administrator only through, and removes one
only through, the same public process, except an emergency removal, below.
Three more rules apply:

- Admin rights end on the same day a person stops being a maintainer or moves to
  the emeritus list.
- In an emergency, such as abuse or a compromised account, the owner removes an
  administrator's rights at once. He records the reason in a public issue
  afterwards.
- Administrators cannot remove the owner, and they cannot change the Ownership
  section.

## Founder clause

The **protected text** is:

- the Ownership, Administrators, Removing a maintainer, Becoming a maintainer and
  Founder clause sections;
- the section "Changes to this document";
- the vote rules in "Decisions", including the vote cap;
- the rule in "Conflict of interest" that changes to CODEOWNERS and
  MAINTAINERS.md are always conflicted;
- the choice of code of conduct, the enforcement contact named in
  `CODE_OF_CONDUCT.md`, and the outside person named in MAINTAINERS.md;
- the date recorded in the Bootstrap section.

For the first 24 months after the bootstrap ends, two things need the owner's
agreement: any change to the protected text, and removing the owner from any
role. "Needs the owner's agreement" means a pull request opened or approved by
the owner. GitHub does not let an author approve their own pull request, so a
pull request that the owner opens counts. The recorded date follows its own rule
in the Bootstrap section, and that rule does not lapse.

The clause is not in force during the bootstrap. The owner merges then, and
nothing changes without him except under the two exceptions that the Bootstrap
section names. The clause lapses on its own 24 months after the day recorded
in the Bootstrap section. It needs no vote and no change to this document. The
Ownership section is not part of the clause and does not lapse: only the owner
changes it.

GitHub cannot enforce this clause. CODEOWNERS accepts any one owner on a line,
and after the hand-over the line names the maintainer with no affiliation. So
the clause rests on one thing: the owner's power as organization owner to
revert a change that was made without his involvement. The same holds for
MAINTAINERS.md.

## Bootstrap

Today the Pulse has one maintainer: Mauro Morales. He is one of the maintainers
of Kairos and of Hadron Linux, two projects the Pulse covers, and he is employed
by Spectro Cloud. So today, nobody without an affiliation reviews the Kairos and
Hadron profiles before they are merged. The 7-day window and the
`conflict-of-interest` label make each such change public. They do not make it
independent.

During the bootstrap:

- Mauro merges pull requests, with two exceptions: the pull request that
  records the end of the bootstrap under rule 3 below, and the pull requests
  that the second owner merges when the owner has been unreachable for 6
  months, as the last item in this list says.
- Every change to `data/projects/kairos.yaml` or `data/projects/hadron.yaml` is
  conflicted, and so is every change to an entry about Kairos, Hadron or Spectro
  Cloud in `data/lineage.yaml`, `site/projects_meta.yaml`, `site/content.py` or
  `site/drafts/base_choice.yaml`. That includes corrections that Mauro did not
  write but merges.
- The first maintainer who has no affiliation with any covered project
  replaces Mauro as the required approver of the Kairos and Hadron profiles, of
  the conflicted entries in the files above, of the methodology and the schema,
  and of `.github/CODEOWNERS`, `MAINTAINERS.md` and this document. A
  maintainer who works on another covered project, a competitor of Kairos or
  Hadron for example, does not qualify.
- Mauro proposes the new maintainers, so he picks the people who will oversee
  him. Each proposal is a public issue, open 14 days, and one maintainer's
  objection is a veto.
- If the owner has been unreachable for 6 months, the second owner may merge
  pull requests and propose maintainers under these rules. Unreachable means no
  commit, review or comment anywhere in the organization, stated in a public
  issue that stays unanswered for 30 days. The second owner never touches the
  Ownership section. If there is no second owner, nobody can act: that is a
  residual risk, and it is listed under "Known limits".

**The end condition** is that the Pulse has at least two maintainers besides
Mauro, who are affiliated with different projects, or with none, and none of
whom is employed by Spectro Cloud, and at least one of whom has no
affiliation with any covered project. Without that last part the bootstrap
could end with nobody allowed to approve a change to the Kairos and Hadron
profiles.

**How the bootstrap ends.** There is one rule, in five parts:

1. The bootstrap ends on the day a pull request that records that day in this
   section is merged.
2. Once the end condition holds, the owner can end it at any time. He opens or
   approves that pull request.
3. If the end condition has held for 90 days and the owner has not recorded the
   day, any maintainer may ask him in a public issue. If he has not acted within
   14 days of that request, the maintainer opens the recording pull request. An
   administrator or the second owner merges it. If there is neither, a
   maintainer who is not employed by Spectro Cloud, and who did not open it,
   merges it. Nobody else can.
4. The owner can delay the end only by publishing a reason in a public issue
   before the 90 days run out. Each reason delays the end by at most 90 days.
   He can do this at most twice, so the delay is at most 180 days. After that,
   rule 3 applies with no further delay.
5. The recorded date is protected text. After it is recorded, it changes only
   through a pull request opened or approved by the owner. The first recording
   under rule 3 is the one exception.

From the day it is recorded, the decision rules above apply in full, and this
section is reduced to a record of when the bootstrap ended and to the first two
sentences of rule 5, which stay in force and do not lapse.

Bootstrap ended on: not yet.

## Changes to this document

A change to this document is treated like a change to the methodology: it
follows the conflict-of-interest rules above, whoever writes it. A change to the
protected text also follows the founder clause. A change to the Ownership
section follows only that section: the owner opens or approves it.

## Known limits

A governance document cannot be perfect. These limits are known and accepted
for now:

- After the founder clause lapses, only the Ownership section and the recorded
  date stay under the owner's control. A majority of the maintainers can then
  rewrite the Removing a maintainer and Becoming a maintainer sections.
- One maintainer's veto can freeze all growth, and it can keep the end condition
  from ever holding. That is the price of the rule against packing the
  maintainers with a majority.
- While the owner is the only maintainer, every profile change that he writes or
  approves waits 7 days. This is intended.
- If the owner is unreachable and there is no second owner, nobody can act
  during the bootstrap.
- A group of more than one third of the active maintainers other than the
  person concerned can block any removal, and two employers together can reach
  two thirds. The written finding is the only check.
- GitHub can block rule 3 of "How the bootstrap ends". The recording pull
  request changes this document, and CODEOWNERS names only the owner on its
  line until he changes that line. If a code owner review is required and the
  organization ruleset stops administrators from bypassing it, nobody that rule
  3 names can merge that pull request until the CODEOWNERS line changes.
- GitHub cannot enforce the founder clause, or the rule that only the owner
  changes the Ownership section, once the code owner lines name another
  maintainer. Both rest on the owner's power as organization owner.
- The rules are only as strong as the organization settings behind them. The
  Administrators section says which settings.
