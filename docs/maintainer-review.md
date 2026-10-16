# Maintainer factual-review plan

Before publication, each project's factual profile goes to that project's
maintainers for correction. This document says how, and what we are and are not
asking for.

## What we are asking

**Verify the factual representation of your project.** That is the whole ask.

We are not asking anyone to endorse the survey, agree with the taxonomy, approve
the comparison, or review anything about another project. Correcting a fact in
your profile does not imply agreement with anything else in the dataset or the
article, and we will not present it that way.

## Who reviews a profile

Each profile can have a representative, a person who works on the project, and
an external steward, a person with no affiliation with any covered project who
looks after the profile when no representative is interested. No project has to
have a representative. A profile with neither is reviewed by the maintainers. A
maintainer requests each reviewer's review by hand, and the request is recorded
in the pull request. The rules are in [GOVERNANCE.md](../GOVERNANCE.md).

## What to send

One profile per project, not the whole dataset. Each YAML profile is
self-contained: fourteen dimensions, an evidence label per dimension, a source URL
behind every documented claim, and an `open_questions` list of things we could not
settle.

Send, per project:

1. A link to that project's profile file.
2. The `open_questions` list from it, which is where we most need help.
3. A short note covering the three points in "What we are asking" above.
4. The correction mechanism: a pull request against the YAML, with the primary
   source for the correct value.

Do not send a draft of the comparative article for approval. The article is our
analysis; the profile is the factual claim about their project. Those are
different things and conflating them is how a factual-review request turns into
an endorsement request.

## Priority order

Ordered by how much a wrong answer would cost a reader, not by project size.

**First, because the profile records an unresolved question that materially
affects an operator's decision:**

- **Container-Optimized OS.** Rollback and recovery are entirely
  undocumented, and the profile says so. If a procedure exists, we want to record
  it rather than leave the largest gap in the survey.
- **Kairos.** Secure Boot posture on the current default artifact could not be
  established, and the architecture page appears to describe a model that no
  longer applies. Also whether the install web UI has any authentication.
- **Hadron.** The same Secure Boot question, recorded at its source: the shim is
  compiled from upstream with no signing step found. Also whether Hadron is
  inside the CNCF Kairos project's scope, and whether the base images are
  signed. The author is one of the Kairos and Hadron maintainers, so changes to
  these two profiles follow the conflict-of-interest rules in
  [GOVERNANCE.md](../GOVERNANCE.md). The ask is the same as to everyone else.

If the maintainers like the format and the method, the Pulse is open to becoming
a group effort, kept up by people from several of the projects rather than by
one author.
- **Talos Linux.** What exactly triggers automatic rollback, and how many
  attempts. We read this from source because it is not documented, and we would
  rather be corrected than be right by accident.

**Second, where a published policy and the live state disagree:**

- **Flatcar.** The LTS channel state against the published LTS policy, and the
  current status of the shim-review submission.
- **Azure Container Linux.** Whether AKS uses the A/B slot switch on ACL nodes or
  always replaces the node, and which Flatcar version a node image is built from.
  The repository documents a stable 4459.x pin and Flatcar stable is now 4757.2.0.
- **Fedora CoreOS.** The shape and timeline of the unification working group
  opened 2026-08-26, since a reader deciding today is deciding about a moving
  target.
- **Ubuntu Core.** How many failed boots trigger an automatic kernel or base snap
  rollback, and what counts as a successful boot. The mechanism is documented and
  the two numbers that decide what it actually catches are not. Also whether a
  released riscv64 image exists for any board, since the architecture is listed and
  no artifact was found.

**Second and a half, where a profile covers more than the maintainer may expect:**

- **openSUSE MicroOS.** This profile covers three release vehicles, MicroOS, Leap
  Micro and SUSE Linux Micro, and that choice should be stated plainly when the
  profile is sent, because a maintainer of any one of them will otherwise
  reasonably read it as a profile of something they do not own. The specific
  factual asks are whether SUSE Linux Micro 6.x still ships health-checker, what
  the default snapshot retention policy is, and whether openSUSE MicroOS is
  properly described as an upstream of SUSE Linux Micro or as a sibling. The
  routing question is real here too: the community and commercial vehicles have
  different maintainers, and the profile may need to go to both.

**Third, standard factual review:**

- Bottlerocket, bootc, NixOS, Unikraft.

## Contact routes

Use each project's own documented channel rather than a maintainer's personal
address. Where a project has a public discussion forum or a regular community
meeting, that is usually better than a private message, because the correction
and its source then live somewhere other people can see.

Several projects in this edition have no published security or governance contact
at all, which is itself recorded in their profiles. For those, a public issue on
the relevant repository is the appropriate route.

## Recording corrections

Every correction goes into the profile's `corrections` list with the date, the
field, what changed, who submitted it and the primary source. The change history
then lives in the data rather than only in git history, and a reader of a single
profile can see that it was reviewed and what moved.

If a maintainer disputes a characterization we believe the sources support, record
both: keep the sourced value and add the dispute to `open_questions`. Do not
quietly change a sourced claim to match an unsourced objection, and do not leave
a maintainer's disagreement invisible.

If a maintainer declines to review, that is fine and is not recorded as a
deficiency in the profile. Nothing here depends on their participation.

## Timing

Send after the dataset is stable and before the article is published anywhere.
The profiles are the reviewable unit and they are stable now.

Corrections received after publication are still accepted through the same pull
request mechanism, and the `corrections` list is designed for exactly that.
