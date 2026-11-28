# Methodology, cloud native OS Pulse

Data collected: **2026-09-15**. Every source re-read and every profile
re-verified: **2026-09-22**. Schema version **1.0.0**.

The Pulse is a rolling release. There are no editions. The site states the
commit it was built from and the date it was generated. Section 7 says when a
profile moves to a new release of its project.

This document explains how the Pulse is built, what it deliberately does
not do, and how to challenge it. Read it before reading the comparison. A
comparison whose method is hidden is not a comparison, it is an assertion.

---

## 1. The question

**Where does the cloud-native operating system ecosystem stand today?**

The Pulse is a point-in-time map. Its purpose is to give platform engineers and
infrastructure teams enough factual information to understand the major
approaches and decide which ones deserve a deeper evaluation against their own
requirements.

It is explicitly not:

- an architectural analysis of what these differences mean in practice
- a benchmark or a measurement of behaviour under failure
- a recommendation, a ranking, or a verdict
- a feature checklist

Those belong to later work. Section 10 sets the inclusion criteria and the scope.
Section 11 and `follow-up-research.md` record the questions this survey raised
and did not answer.

## 2. Who wrote this, and why that matters

This survey was initiated by people who work on Kairos, one of the projects in
it. That is a methodological risk, not a disclaimer to be waved away. Section 9
lists the specific controls applied, including the ones built into the data
schema so that they cannot be skipped. Section 11 records where the method was
challenged and what changed as a result.
One link needs naming: the creator of Kairos formerly led Elemental at SUSE, and
Elemental is an entry. Section 10, "The fourteenth entry: Elemental", lists the
controls applied to that profile.

## 3. The taxonomy, and why the obvious one is wrong

The common way to classify these systems is a single label per project:
"Kubernetes OS", "immutable distro", "bootable container", "unikernel". That list
looks like a taxonomy but it is not one, because its entries do not answer the
same question.

- "Kubernetes OS" answers *what the machine is for*.
- "OS construction framework" answers *who assembles the artifact*.
- "Bootable container" answers *what holds the OS state*.

Those are three independent questions. A project can be a general-purpose host
that you assemble yourself and that stores its root state in A/B partitions.
Forcing one label onto it destroys two of the three facts, and which two survive
depends on whoever wrote the label. So the Pulse uses three axes instead.

### Axis A. Workload scope: what the machine is for

`kubernetes-appliance` to `kubernetes-oriented-host` to `general-purpose-host`,
plus `single-application-image` for systems where the unit of deployment is one
application rather than a host at all.

This is a spectrum and it is descriptive. **No position on it is better than
another**, and the profile schema requires every project to record what its
position buys and what it costs. A narrow appliance gives up general-purpose
flexibility and gets a smaller attack surface, fewer states to test, and a
machine whose configuration cannot drift. A general-purpose host gives up that
constrained state space and gets the ability to run the workload that does not
fit the appliance model. Both statements are in the dataset.

### Axis B. Construction model: who assembles the artifact you run

`vendor-fixed-image`, `vendor-base-plus-derivation`, `framework`,
`package-repository-assembly`.

This axis exists because "customizable" is close to meaningless on its own. The
useful question is where in the lifecycle customization happens and who owns the
result. A project that publishes a fixed image and a defined extension mechanism
retains responsibility for the artifact. A framework hands the adopter the
ability to build anything and, with it, the duty to build, test, sign, patch, and
support what they built. Neither is a better answer. They are different
allocations of the same work.

### Axis C. Root state substrate: what holds the OS

`ab-partition-image`, `ostree-deployment`, `bootc-container-deployment`,
`nix-store-generation`, `unikernel-binary`, `package-repository`,
`transactional-snapshot`, `snap-image-set`.

Integrity enforcement is deliberately *not* on this axis. Whether a root
filesystem is read-only, verity-protected, or merely conventional is recorded
under dimension 2 and dimension 10, because two projects can share a substrate
and differ completely in what protects it.

### Entry kind: not everything here is the same kind of object

The survey covers distributions, frameworks, base image sets, mechanisms, build
systems, and operating systems produced for a vendor platform. Comparing a mechanism's release
cadence or hardware support against a distribution's is a category error, and
doing it silently produces a table that looks rigorous and is not.

Every profile therefore carries `entry_kind`, which may hold more than one value.

**This is how the Fedora CoreOS and bootc relationship is represented.** They are
not peers. Fedora CoreOS is a distribution with streams and releases. bootc is a
mechanism for deploying and updating a system from an OCI container image, which
distributions and base images consume. They get separate profiles with different
`entry_kind` values, and the bootc profile marks as `not-applicable` every
dimension that only makes sense for a distribution.

**The same field applies to Kairos, and that is the point.** Kairos is a
framework first, by its own description, and a distribution second, because it
also releases the artifacts its framework produces. If `entry_kind` exists so
that bootc is not mismeasured, it has to be applied identically to the project
the authors work on.

**The same split is how Hadron and Kairos are represented.** Hadron is the
from-scratch base distribution that Kairos is applied to, and it publishes base
images meant to be derived from. On its own it has no install, upgrade, rollback
or recovery mechanism; its home page says it "becomes immutable" when "topped
with Kairos". So Hadron carries `distribution` and `base-images`, Kairos carries
`framework` and `distribution`, and the dimensions that Kairos supplies are
recorded in `hadron.yaml` as provided by the framework, with a cross-reference,
rather than restated. A comparison table must not count the A/B substrate or the
boot-assessment mechanism twice. The pair is the mirror of Fedora CoreOS and
bootc, with one difference that the Kairos profile keeps its `distribution` tag
for: the framework project releases the combined artifact itself, under its own
version number, which bootc does not. Section 11 records how that tag was
re-examined.

**The Yocto Project is represented as a `build-system`, not as a `framework`.**
A framework in this survey produces an artifact from a base that the project or a
vendor supplies: Kairos on Hadron, the Talos imager, the Unikraft micro-libraries.
The Yocto Project assembles the whole distribution from source recipes, with no
base to start from. The project releases the build tooling and the metadata. The
adopter owns the image that comes out. Each capability a dimension asks about comes
from a layer the adopter selects, and the profile names the layer and separates it
from the Yocto Project itself. Like a framework, a build system moves the build,
test, signing, CVE response and support duty to the adopter.

### Category fit: admitting when something is adjacent

NixOS, Unikraft and the Yocto Project are in this survey because the contrast is
informative, not because they are peers of a Kubernetes node OS. NixOS's central claim is
declarative configuration and reproducible builds, not an immutable running root.
Unikraft has no host operating system at all, so several dimensions do not merely
score low, they do not apply. The Yocto Project builds the whole operating system
from source, so what a dimension asks about depends on the layers the adopter
selects.

Each profile carries `category_fit` with a value of `full`, `partial`, or
`adjacent`, and an `adjacent` entry is never compared to a `full` entry on a
dimension it does not share.

## 4. The three kinds of "no"

The schema keeps three answers apart that a checkbox table collapses into one
empty cell:

| Value | Means | Required evidence |
|---|---|---|
| `none` | The project documents that it has no such capability. | A source that says so. |
| `unknown` | We could not determine it from primary sources. | A note saying where we looked. |
| `not-applicable` | The concept does not exist in this architecture. | A note saying why. |

**Missing documentation is never treated as proof of absence.** When in doubt the
value is `unknown`. The validator enforces this: a value of `none` fails the
check unless the dimension carries `DOCUMENTED` evidence and at least one source.

This matters most for the projects with the thinnest public documentation, which
at the 2026-09-15 collection are the hyperscaler ones. An unknown recorded
honestly is a better data point than a confident wrong one, and it tells the next
re-validation where to look.

## 5. The fourteen dimensions

Each dimension has a stable id so two versions of a profile can be diffed field
by field.

| Id | Dimension | What it records | What it must not do |
|---|---|---|---|
| d01 | OS model | Position on the three axes, plus the project's own words about itself | Assign one label |
| d02 | Immutability | What is read-only, what is writable, what is ephemeral, and the enforcing mechanism | Reduce to immutable yes/no |
| d03 | OS artifact | The primary deployable artifact, and whether standard OCI infrastructure applies | Treat every image format as equivalent |
| d04 | Upgrade | The actual mechanism and what writes where | Say "atomic updates" and stop |
| d05 | Rollback and recovery | Six separate fields, because these are different capabilities | Treat rollback and recovery as synonyms |
| d06 | Customization | Where in the lifecycle customization happens, and its documented limits | Claim customizable yes/no |
| d07 | Kubernetes relationship | Requirement, bundling, lifecycle independence, direction of control | Imply a position on the spectrum is superior |
| d08 | Hardware and platform | Architectures with released artifacts, platforms, specialized hardware, and the extension mechanism | Report intentions as support |
| d09 | Provisioning | Supported install and bootstrap paths | |
| d10 | Security | Each mechanism separately: Secure Boot, measured boot, TPM, integrity, encryption, artifact verification, SBOM, FIPS | Treat these as one bucket, or as equivalent properties |
| d11 | Operations and debugging | The operating model, including what works when Kubernetes is down | Imply SSH is good, or that its absence is good |
| d12 | Fleet management | Three separate buckets: core project, open-source companion, commercial product | Attribute a commercial product's capability to the OS |
| d13 | Governance | Four separate properties (see below) | Collapse them into "open source" |
| d14 | Maturity | Age, current version, observed cadence, support model and windows | Use GitHub stars as a quality signal |

### d13 deserves its own note

Four properties, kept separate because they vary independently:

- **Open source.** Is the source under an OSI-approved licence?
- **Open governance.** Is there a published decision process a non-employee can participate in?
- **Vendor-neutral ownership.** Who holds the trademark and the project assets?
- **Contribution diversity.** How many distinct organizations actually contribute, and measured how?

A project can be open source, single-vendor owned, and have no published
governance. Another can be foundation-held with one dominant contributor. These
are four readings. The Pulse does not add them up, and it applies all four to
Kairos on the same terms as to everyone else.

Contribution diversity always records its measurement method alongside its value,
because the method changes the answer. Counting commit-author email domains
undercuts contributors who use personal addresses, and that caveat travels with
the number.

### d08 records artifacts, not intentions

An architecture counts as supported when there is a released artifact or explicit
documentation saying so. A port in progress, an open issue, or a community build
is recorded as such and not as support. This rule is applied to every project
including Kairos.

One exception, added 2026-10-12 as rule 21 in section 9: an entry that builds the
OS from a base distribution the adopter picks lists, as "via your base
distribution", the architectures its own components are built for. It is a
separate tag. It never counts as a released image.

Where an entry runs follows the same rule. A provider counts when the project or
the provider documents a path to it, with a source, and the level says how far
that path goes (rule 22 in section 9). The old `platforms` field keeps its
coarse values and its meaning.

## 6. Evidence standard

Every dimension carries exactly one evidence label: `DOCUMENTED`, `REPRODUCED`,
`OBSERVED`, `INFERRED`, `UNKNOWN`, or `NOT_TESTED`.

The Pulse is so far a documentation survey. Almost everything in it is
`DOCUMENTED`, with some `INFERRED` and `UNKNOWN`, and `NOT_TESTED` wherever a
claim would need an experiment. In the profiles, `REPRODUCED` and `OBSERVED` are
reserved for later work that runs experiments. The one exception is the six
FR-13 rollback-scope deep dives under `research/deep-dives/`: each ran live commands in a
virtual machine, so where a deep dive labels a result it uses `REPRODUCED` for
results it ran itself and `INFERRED` for anything it did not. Not every deep dive
labels every result. **Nothing inferred is presented as
documented fact**, and an inference must name the evidence it rests on.

Acceptable sources, in order of preference:

1. official documentation
2. official source repositories
3. design and architecture documents
4. governance documents
5. release notes
6. official project announcements
7. maintainer statements in official channels

Vendor product documentation is acceptable for facts about that vendor's own
product, and is labelled `vendor-docs`. **Marketing comparison pages published by
any project about any other project are not an acceptable source for any claim in
this dataset, including claims about the publishing project itself.**

Every source carries a `retrieved` date. A Pulse without dated sources cannot be
diffed against the next one.

One caveat found on the second pass, recorded here rather than fixed, because
fixing it means re-citing several hundred URLs: several documentation sites
serve their development branch at the unversioned URL and their released
documentation under a versioned path. kairos.io is one; its unversioned
`/docs/...` pages carry a "Next" banner while the v4.3.0 tree lives under
`/docs/v4.3.0/...`. The profiles cite the unversioned URLs. On the second pass
the load-bearing Kairos claims were checked against the versioned v4.3.0 source
tree as well and hold, but a reader who follows a citation may land on a page
that has moved on. A re-validation should cite the versioned path wherever a
site offers one, and record the documentation version in the source's `version`
field, which the schema already has.

## 7. Versioning and repeatability

The dataset records, for every project:

- the date the data was collected
- the exact version observed, the channel, and its release date
- **the method used to determine that version**, so the next re-validation repeats the same lookup rather than inventing a new one
- the documentation version where the source is versioned

The Pulse is a rolling release, not a series of editions. The site states the
commit it was built from and the date it was generated. A script detects newer
releases of each project, and the site flags those entries as not yet
re-validated. A profile moves to a new release only after its claims are
re-validated against that release, with every change recorded in
`corrections`. `REFRESH.md` describes the steps. Re-validation is a manual step
today. The Pulse makes no commitment about when a flagged entry is re-validated.

Every profile still carries an `edition` field. It is kept for compatibility
with schema 1.0.0. It does not mark an edition, and no edition exists.

The schema is versioned separately from the data. A later schema version may add
fields and vocabulary values. It must never change what an existing value means,
because a diff between two versions of a profile is only meaningful if the
vocabulary is stable.

## 8. Presentation rules

- **No giant checkbox table.** Comparison tables carry short normalized
  descriptions, not ticks. Checkboxes appear only for properties that are
  genuinely binary and precisely defined.
- **No aggregate score, no ranking, no winner, and no radar chart.** A radar chart
  is excluded specifically because its area is an implicit weighted sum that the
  reader cannot see, and the weights would be chosen by the people who maintain
  one of the projects on it. The profile validator fails on any field that looks
  like a score or a rank, so this constraint survives contact with a future
  editor.
- **No persona-specific winners and no "best for X" lines.** Those belong to the
  later requirement-profile work, after experiments exist.
- **Reader guidance routes to questions, never to a project.** A "By use case"
  block may point a reader to the questions to ask, the dimensions that answer
  them, and the matrix filters that narrow the list. It must never point a reader
  to a named project. This was amended on 2026-10-05. The ban on "best for X"
  lines stays.
- Every comparison table cell traces to a dimension field in a profile, and every
  profile field traces to a source.

## 9. Bias controls

The risk is that a survey written by Kairos maintainers quietly optimizes for
Kairos. Four of these controls are structural, meaning the schema or the
validator enforces them rather than relying on the author's good intentions.

**Structural:**

1. **`tradeoffs.buys` and `tradeoffs.costs` are both required on every profile.**
   A profile does not validate until both are filled in. No project, including
   Kairos, gets to have only upsides.
2. **The validator rejects score, rank, rating, and grade fields.** The "no
   aggregate score" rule is enforced by code, not by discipline.
3. **A value of `none` requires a documented absence.** A competitor's capability
   cannot be erased by failing to find its documentation.
4. **`entry_kind` and `category_fit` apply to every entry.** The fairness
   mechanism invented for bootc, NixOS, and Unikraft is applied to Kairos on the
   same terms.

**Editorial:**

5. Kairos is treated exactly like every other project, and is researched with the
   same instruction to hunt actively for its limitations and thin documentation.
6. Kairos terminology is not used as the neutral vocabulary of the category. The
   axis names and vocabulary values are chosen to be describable without
   reference to any one project.
7. No criterion exists because Kairos scores well on it. Section 11 records the
   dimensions that were kept specifically because Kairos does *not* look good on
   them.
8. Constraints are described in terms of both cost and guarantee. Talos's absence
   of a shell is not a missing feature, it is a design decision with a stated
   rationale and a measurable consequence, and the profile records the rationale
   in the project's own words.
9. Flexibility is described in terms of both capability and responsibility. Where
   a project lets the adopter build their own artifact, the profile records that
   the adopter then owns testing, signing, CVE response, and support for it.
10. No speculation about corporate acquisitions, commercial strategy, or future
    company behaviour. Ownership facts are recorded as documented, and nothing
    beyond that is said.
11. No editorializing about maintainers or commercial organizations.
12. **If the comparison comes out overwhelmingly favourable to Kairos, the
    methodology is challenged before publication, not the finding.** Section 11 is
    where that challenge is recorded.
13. **No foundation or dashboard scores.** Not every entry belongs to a
    foundation, so a score such as a CNCF CLOMonitor rating cannot be compared
    across the matrix. (Added 2026-10-06.)
14. **A pinned component is not a cost; a closed one is.** A release that pins
    a component behind its upstream, as Kairos pins Hadron or ACL pins Flatcar,
    is how every OS ships. It is not a cost when the adopter can build an image
    with the version they want. It is a cost when the project gives no way to
    build or run your own, because the adopter is then held to its cadence.
    A gap between what a project states and what it delivers stays a cost,
    unless the project documents a supported way to get what it does not ship,
    such as building your own image. (Added 2026-10-06.) This rule governed
    the former buys and costs, which rule 19 replaced.
15. **What counts as a cost.** A line in `tradeoffs.costs` must be one of four
    kinds: (C1) a limit the adopter cannot remove; (C2) a capability that is
    absent where other entries document it; (C3) a documented risk or defect;
    (C4) a gap between what the project states and what it delivers. Six kinds
    of line are not costs: (N1) an unknown, which goes to `open_questions`;
    (N2) a documented design choice with a supported alternative path; (N3) a
    pin the adopter can rebuild (rule 14); (N4) a remark about a version number
    or a name; (N5) a cost already counted under another entry; (N6) a
    judgement or an unsourced comparison. A value that the documented design
    implies counts as documented: an A/B design documents one previous
    version. (Added 2026-10-06.) This rule governed the former buys and
    costs, which rule 19 replaced.
16. **Concentration is stated once, in one shape.** For a foundation-held
    entry, the data sheet states one measure: `N of M maintainers work for
    <company>`, from the project's own maintainers file. A commit share is
    added only when it is measured the same way for every entry. A
    single-vendor entry says single vendor once. An entry whose maintainer
    affiliations are not published says so as an open question, not a cost.
    (Added 2026-10-06.) The data sheet's Maintainers row shows this fact,
    from the profile field `maintainers_fact`.
17. **Where a capability is documented is not a cost.** A feature that exists
    and is documented anywhere the project maintains, such as a repository
    README, counts as documented. The absence of the feature, or of any
    documentation, can be a cost. (Added 2026-10-06.) This rule governed
    the former buys and costs, which rule 19 replaced.
18. **A limitation is a cost only where every entry with the capability is
    assessed on it.** A limitation of a capability is a cost only when the
    same aspect is assessed for every entry that has that capability. An
    entry is never penalised for the quality of something other entries lack
    entirely; for those entries, the absence is the cost. Four kinds of
    limitation still count wherever they appear: a documented defect, an
    unverified security path, a stated stop of maintenance, and a gap between
    what a project states and what it delivers (C4). A status goes inside the
    buy for the capability it describes, and only when the project states a
    consequence in its own words, such as "the API may still change". A
    version number alone is not a status (rule 15, N4). Statuses share a place
    on the card, not a weight. A status that is a real risk for the adopter is
    also a cost. (Added 2026-10-06.) This rule governed the former buys and
    costs, which rule 19 replaced. Its four kinds now define known issues.
19. **Each project has a data sheet, not a list of buys and costs.** The
    sheet lists every value from the matrix in full, without ranking or
    judging. Known issues are listed only when they are a documented defect,
    an unverified install or update path, a stated stop of maintenance, or a
    checked gap between what a project states and what it delivers. (Added
    2026-10-06.) Known issues are recorded in the profile field
    `known_issues`, each with its kind and its sources. Two pages of a
    project that disagree with each other are an open question, not a known
    issue. The profile fields `tradeoffs.buys` and `tradeoffs.costs` stay in
    the profiles for history and are no longer shown. (Amended 2026-10-12.)
    Right after Update unit, the sheet carries a Mounts row. It is not a
    matrix column. It has four lines for every entry: what is read-only, what
    is writable but reset on reboot, what is writable and persistent, and
    whether the adopter can change that. A path is listed as reset on reboot
    only where the documentation says it is discarded on reboot. A persistent
    overlay, such as `/etc` on some entries, is listed as persistent with
    "(overlay)" after the path. The profile fields are in `d02` (`read_only`,
    `ephemeral`, `writable_and_persistent`, `configurable_paths`).
20. **Data sheets do not list known issues.** (Added 2026-10-08.) One
    entry was read far more deeply than the others, so it collected far more
    issues. The count measured how closely each project was examined, not how
    well it works. A fair list would need the same fixed checks, at the same
    depth, for every entry, and even then a project that tracks its bugs in
    public would show more than one that does not. The sheet sends readers to
    each project's own issue tracker instead. Facts that matter to an adopter,
    such as an unverified upgrade path or a stopped provider, stay in the
    matrix columns they belong to. The profile field `known_issues` stays for
    history and is no longer shown. This replaces the known-issues part of
    rule 19.
21. **Via your base distribution.** (Added 2026-10-12.) An entry that builds
    the OS from a base distribution the adopter picks is credited with what
    that base distribution documents, once, as "via your base distribution",
    instead of the Pulse copying the upstream documentation. For
    architectures, this holds only where the entry's own components are built
    for that architecture. A base distribution entry, such as Hadron, is
    credited only with what it documents itself. Today this applies to Kairos
    and bootc. The AI accelerator column shows "Via your base distribution"
    for them, and picking a specific accelerator in the filter keeps them,
    with the tag highlighted. The Architectures column adds "<arch> via your
    base distribution" for each architecture their own components are built
    for (profile field `architectures_via_base_distribution`, with the release
    assets or package builds as sources), and the architecture filter keeps
    them in the same way.
22. **Where it runs records paths, not reputations.** (Added 2026-10-21.)
    The column "Where it runs" (profile field `d08.normalized.providers`)
    lists, for a fixed set of infrastructure providers, the highest level an
    entry reaches: an official image in the provider's catalogue, a project
    image for the provider, documented steps to bring your own image, or only
    a config source. A level other than "Not documented" or "Does not apply" cites a
    page with a verbatim quote. A general platform list from a config tool, such as the
    Ignition list, supports "config source only" and nothing higher: a tool
    that reads a provider's metadata is not an OS that runs there. "Works, but
    not documented" is not a level, because it needs a run on the provider
    (`REPRODUCED`); such questions go to `follow-up-research.md`. A provider
    with no source reads "Not documented", which is not a statement that the
    entry fails there. Equinix Metal is not a row. It ended on 2026-06-30.
    The Ignition list still names it ([Equinix end-of-life
    table](https://docs.equinix.com/releases/end-of-life/eol-products-services)).
    The first pass covers Fedora CoreOS, Flatcar, Talos, Kairos and Hadron.
    Every other entry reads "Not collected" until its pass is done.

## 10. Scope and inclusion criteria

### Inclusion criteria

An entry in the comparison matrix meets all five inclusion criteria, with one exception that is stated openly: R3 is not yet documented for Azure Container Linux and Container-Optimized OS. It is recorded as "unknown" in their profiles, and a missing document is not read as a "no" (section 4).

| Rule | Name | Meaning |
|---|---|---|
| R1 | Atomic updates (versioned OS) | The OS version is one artifact, built once, that every node in a fleet runs. A fleet updates or rolls back by pointing it at a version. Examples: an OCI image, an image file, an OSTree commit. Extensions on top of the base, such as system extensions or layering, are allowed and recorded as conditions. A node that assembles its own update from packages does not meet R1, also when the packages come from a pinned repository. The local per-node rollback is R3. The test is capability: the project documents a way to run it like this. A cloud native OS is judged across a fleet, not on a single node. |
| R2 | Immutable at runtime (read-only OS files) | The OS part (the root or `/usr`) is read-only on a running node. |
| R3 | Rollback (to a version) | Rollback goes back to the previous OS version, the artifact the whole fleet ran. Each node keeps that previous version locally, ready to boot. A snapshot of a node's own state is not this rollback: R3 is a rollback to a version, not to a snapshot of one node. |
| R4 | Config-driven provisioning | A node sets itself up from a written config when it is installed or first boots, with no interactive install. Some projects apply the config again at every boot, on demand, or by reconcile. The config can be one file or several. The old name, Declarative provisioning, stays as an alias. |
| R5 | Kubernetes ready | The project, or its vendor, documents running Kubernetes on it: bundled, installed on it, or as the node OS of a Kubernetes service. |

R5 needs two notes.

- **A framework or a mechanism meets R5 through the images built with it.**
  Kairos and bootc do not run anything on their own. They meet R5 when images
  built with them run Kubernetes, and the table below names the source.
- **Running containers alone is not enough.** Limiting the Pulse to
  Kubernetes-only systems would be too narrow for cloud native. The opposite
  statement is the strong one: if a system does not run Kubernetes, it is hard
  to consider it cloud native.

**Openness is not an inclusion criterion.** A closed or single-vendor project
that meets the five criteria is in. Governance and openness are shown as columns
instead, from d13, so a reader sees them for every entry rather than having them
decide who appears.

Three groups sit beside the matrix.

- **Alternative paradigms.** Entries that aim at a reproducible machine you can
  roll back but do not meet R1 to R4 as the project ships them: NixOS rebuilds
  the system in place from a declaration, Unikraft has no host OS at all, and the
  Yocto Project builds the whole OS from source, so R1 to R4 come from layers and
  configuration the adopter selects. They appear in their own section, not in the
  matrix. They are profiled on the same fourteen dimensions. A matrix row would be
  mostly cells that do not apply.

  *Note, 2026-10-12.* The Yocto Project was added as the third entry, and the
  definition changed with it. The earlier wording, "by a route outside R1 to R4",
  was not true of the Yocto Project: through layers it can reach R1 (meta-rauc,
  meta-swupdate, meta-mender, meta-updater), R2 (the `read-only-rootfs` image
  feature) and R3 (A/B slots or OSTree). The test in R1 is that the project
  documents a way to run it like this. The Yocto Project's own manuals do not
  document the update layers, so "as the project ships them" is the accurate test.
- **Worth mentioning.** Projects with public work but nothing released to profile
  appear in a short list, not in the dataset: Amutable. The dimensions cannot be
  checked against something that has not shipped.
- **Out of scope.** Conventional mutable distributions fail R1 and R2 as
  shipped. With enough configuration and tooling around them they can be made
  to meet all five criteria, and the Pulse does not call that the wrong choice.
  It lists the projects that meet the criteria by design, without the reader
  configuring the OS or building that tooling. See "Deliberately out of scope"
  below.

Hadron is a special case. It is profiled as the base Kairos is applied to, and on
its own it has no upgrade or rollback mechanism. It meets R1 to R5 only as
deployed through Kairos. See "The thirteenth entry" below.

### How each entry meets R5

Each row names the source the claim rests on. Where a source is already cited in
the profile, the row uses that citation. A row with no source in the profiles
says "source to add" rather than inventing one.

| Entry | How it meets R5 | Source |
|---|---|---|
| Azure Container Linux | Node OS of AKS. Its README describes it as built for AKS, and it is a named OS option on AKS from Kubernetes 1.34. | [ACL README](https://github.com/microsoft/azure-container-linux/blob/aclmain/README.md), [ACL overview](https://learn.microsoft.com/en-us/azure/azure-linux/azure-container-linux-overview) |
| Bottlerocket | Kubernetes variants. The orchestrator agent ships in the image, and the Kubernetes minor version is part of the variant name. | [Bottlerocket variants](https://bottlerocket.dev/en/os/1.64.x/concepts/variants/), [EKS Bottlerocket AMIs](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami-bottlerocket.html) |
| Container-Optimized OS | Node OS of GKE. It is the documented default node image, and the only one on Autopilot. | [GKE node images](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/node-images) |
| Fedora CoreOS | Its own self-description says "optimized for Kubernetes". Kubernetes is not shipped. | [Fedora CoreOS documentation](https://docs.fedoraproject.org/en-US/fedora-coreos/), [FAQ](https://docs.fedoraproject.org/en-US/fedora-coreos/faq/) |
| Flatcar Container Linux | Kubernetes is installed on it through Ignition or a sysext. | [Getting started with Kubernetes](https://www.flatcar.org/docs/latest/orchestrate/kubernetes/getting-started-with-kubernetes/) |
| Kairos | Standard images bundle a Kubernetes distribution, k3s or k0s. Core images ship none. | [Kairos image matrix](https://kairos.io/docs/reference/image_matrix/), [Choosing a Kubernetes distribution](https://kairos.io/docs/examples/choosing-kubernetes-distribution/) |
| Hadron | Through Kairos. No Hadron image contains Kubernetes. The Kairos standard images built from Hadron bundle k3s or k0s. | [Hadron README](https://github.com/kairos-io/hadron/blob/main/README.md), [Kairos v4.3.0 release](https://github.com/kairos-io/kairos/releases/tag/v4.3.0) |
| Talos Linux | Built for Kubernetes. Machines are control plane or worker nodes, and Kubernetes ships with the OS. | [Talos README](https://github.com/siderolabs/talos/blob/main/README.md), [Talos support matrix](https://docs.siderolabs.com/talos/v1.14/getting-started/support-matrix) |
| bootc | Through images (cited in `bootc.yaml` d07). Red Hat documents MicroShift, its Kubernetes distribution, embedded in bootc images. The bootc roadmap also plans native Kubernetes integration. That is a direction, not evidence, and R5 does not rest on it. | [MicroShift with image mode for RHEL](https://docs.redhat.com/en/documentation/red_hat_build_of_microshift/4.22/html/installing_with_image_mode_for_rhel/index), [bootc roadmap](https://github.com/bootc-dev/bootc/blob/main/ROADMAP.md) |
| Elemental | Rancher provisions RKE2 or K3s on Elemental nodes. The cluster phase creates the cluster from the registered machines. | [Elemental cluster deployment](https://elemental.docs.rancher.com/architecture-clusterdeployment) |
| Ubuntu Core | MicroK8s, installed as a snap. Canonical documents a strictly confined build, which is the only kind Ubuntu Core can install. | [MicroK8s strict install](https://canonical.com/microk8s/docs/install-strict), [MicroK8s snap](https://snapcraft.io/microk8s) |
| EVE-OS | Through its EVE-k build flavor (HV=k), which runs k3s. The default flavor (HV=kvm) ships no Kubernetes. | [EVE-K.md](https://github.com/lf-edge/eve/blob/master/docs/EVE-K.md) |

### Projects included

| Project | Entry kind | Category fit | Why it is here |
|---|---|---|---|
| Kairos | framework, distribution | full | A toolchain that converts a base into an immutable A/B host, and the released artifacts it produces from Hadron. |
| Hadron | distribution, base-images | partial | The from-scratch base Kairos is applied to. Not immutable and not upgradeable on its own; profiled so the base and the framework are not one blurred entry. |
| Talos Linux | distribution | full | The clearest example of the Kubernetes appliance position. |
| Flatcar Container Linux | distribution | full | The Container Linux lineage, and an A/B `/usr` model distinct from whole-root A/B. |
| Fedora CoreOS | distribution | full | The OSTree deployment model, with its own update infrastructure. |
| bootc | mechanism | partial | The bootable-container mechanism, profiled as a mechanism and not as a distribution. |
| Bottlerocket | distribution, platform-os | full | A minimal, API-driven host with verity-protected root and a TUF update path. |
| Azure Container Linux (ACL) | distribution, platform-os | partial | The immutable container host Microsoft ships for AKS, derived from Flatcar and built from Azure Linux RPMs. Profiled in place of base Azure Linux, which is a mutable package-based distribution and out of scope. |
| Container-Optimized OS | platform-os | partial | A hyperscaler platform OS derived from Chromium OS, with limited public source. |
| NixOS | distribution, framework | adjacent | Challenges the premise. Its claim is reproducibility, not root immutability. |
| Unikraft | framework | adjacent | Boundary case. Asks whether the host OS is the right unit at all. |
| Yocto Project | build-system | adjacent | A build system, not an image to run. It builds the whole OS from source recipes, and R1 to R4 come from layers the adopter selects. Alternative paradigms, not in the matrix. |
| Elemental | distribution, framework | full | SUSE's fleet-image path on the SL Micro base. One OCI image is rolled to every node in the selected clusters. See "The fourteenth entry: Elemental". |
| Ubuntu Core | distribution, framework | full | The snap model, where the kernel and the root filesystem are separate images that update independently. |

NixOS, Unikraft and the Yocto Project are profiled but appear under Alternative
paradigms, not in the matrix. See the inclusion criteria above.

Sixteen profiles rather than the nine originally proposed. Fedora CoreOS and
bootc are separated rather than merged, the two general-purpose-host entries
flagged as a known gap in the first draft were researched and
added rather than deferred, Hadron was added in the second pass, on
2026-09-22, for the reasons below, Elemental was added on 2026-10-14 (see "The fourteenth entry: Elemental"), and NixOS, Unikraft and the Yocto Project
are profiled as alternative paradigms.

### The thirteenth entry: Hadron

Hadron was neither included nor excluded in the first draft of the Pulse. It
was simply absent, while `kairos.yaml` referred to it in eight dimensions as the
only base Kairos publishes artifacts for. That is a gap of the kind this
methodology says must be recorded rather than left implicit, and it was closed by
researching Hadron against the same fourteen dimensions and the same evidence
rules.

**Why a separate profile.** The alternative was to fold Hadron's facts into
`kairos.yaml`, which already carried a `base-images` tag on their behalf. That
would have let one entry claim the properties of two objects: a from-scratch base
with its own kernel, hardening baseline, build toolchain and release cadence, and
a lifecycle framework with its own upgrade, rollback and recovery mechanism.
Fedora CoreOS and bootc are kept apart for exactly this reason, and the Kairos
pair is not entitled to a looser rule.

**Why partial, not full.** Hadron's own sources say what it is: a base that
"becomes immutable" when Kairos is applied, whose raw images "cannot be used to
upgrade a running Kairos node directly". The brief for this entry described
Hadron as a general-purpose immutable OS positioned like Flatcar. The evidence
does not support that framing, and the profile says so. Six dimensions (d02,
d04, d05, d09, d11, d12) are answered as provided by Kairos, with the sources that
say so and a cross-reference to `kairos.yaml`, rather than restated. A reader
comparing Hadron to Flatcar on rollback is comparing Kairos to Flatcar, and the
profile is written so that this is visible.

**Why this is not double counting.** The taxonomy axes in `hadron.yaml` describe
what a Hadron base becomes when deployed through its only documented path, in the
way `bootc.yaml`'s axes describe what bootc enables. The substrate value is the
same `ab-partition-image` as Kairos, and the profile says it is the same
mechanism. A comparison table that lists both entries must list the mechanism
once.

**What the entry adds that the Kairos profile could not.** The Secure Boot
question that `kairos.yaml` records as its largest documentation gap originates in
Hadron, which compiles its own shim with no signing step, and is recorded there
at its source. The governance question of whether Hadron is inside the CNCF
Kairos project is recorded from Hadron's side, where the announcement claims it
and no primary source establishes it. And the Trusted Boot path has a live,
dated, root-caused defect at the collection date, recorded under the same
discipline as the Talos provider deprecations.

### The fourteenth entry: Elemental

Elemental entered the matrix on 2026-10-14, when openSUSE MicroOS left it. The
reason for both moves is the same change to R1, recorded in the dated note in
section 11 (item 12): a cloud native OS is judged across a fleet, not on a
single node.

**What the entry is.** Elemental is the operator, the toolkit and the Elemental
OS images on the SUSE Linux Micro base. It is not SUSE Edge, and it is not SL
Micro alone. A `ManagedOSImage` names one OCI image, and the operator rolls it
to every node in the selected clusters. That is R1. Each upgrade unpacks the new
image into a new snapshot that records its image source, and a digest when the
source is an image. The fleet job upgrades from a directory, so a snapshot made
that way has no digest (the toolkit sets the digest only for an image source).
The toolkit keeps a set number of snapshots (default 2, or 4 on `btrfs`), and the
boot menu has one entry for each kept snapshot. That is R3. Rancher provisions
RKE2 or K3s on the nodes. That is R5. Rancher Manager v2.14 or later is a condition on R1,
because the 1.9 operator must be paired with it.

**Why it is not a second MicroOS.** `microos.yaml` covers SUSE Linux Micro as a
release vehicle, and its update tool is `transactional-update`, which builds each
snapshot on the node. Elemental uses SUSE Linux Micro only as its base. Its
update and rollback come from the toolkit's image snapshots. This is the Kairos
and Hadron shape: a lifecycle stack on a base. The base facts in `elemental.yaml`
cite SUSE's own sources and not `microos.yaml`.

**Fairness.** The creator of Kairos formerly led Elemental at SUSE
(`data/lineage.yaml`), and the people who started this survey work on Kairos.
Four controls apply to this profile, on top of section 9:

1. A researcher who had not seen `kairos.yaml` or the lineage file wrote the
   profile, with the section 9 control 5 instruction: hunt for limitations and
   for strengths in the same way.
2. Every source comes from the section 6 list: `elemental.docs.rancher.com`, the
   `rancher/elemental*` repositories, `documentation.suse.com` and `suse.com`.
   No source is on a Kairos or Spectro Cloud site.
3. A second pass, as `docs/REFRESH.md` describes, re-read every claim, given the
   profile and the sources and not the first pass's reasoning.
4. The pull request that added the entry lists, for each matrix column,
   Elemental's value next to Kairos's value, so a reader can check that a
   difference rests on a source on each side.

The maintainer invite for Elemental is produced like any other, and its sending
is a separate decision.

### The two entries added after the first draft

The first draft of the Pulse profiled ten projects and recorded openSUSE
MicroOS, SLE Micro and Ubuntu Core as a known gap, noting that all of them sit in
the same `general-purpose-host` position as Kairos and that leaving them out made
that part of the map look sparser than it is. They were subsequently researched
against the same fourteen dimensions and the same evidence rules, and the gap is
closed. The `transactional-snapshot` vocabulary value, defined but unused in the
first draft, is now used.

**MicroOS, Leap Micro and SUSE Linux Micro are one profile, not two or three.**
The reasoning belongs here because it is a judgement call and the survey's own
precedent pulls in both directions.

Against merging: they carry different names, different support models, different
subscription requirements and different certifications, and those differences are
documented and dated.

For merging, which is the decision taken:

1. **The separation of Fedora CoreOS and bootc turned on *kind*.** A mechanism and
   a distribution are not peers, so comparing their release cadence is a category
   error. All three SUSE vehicles are distributions, so that precedent does not
   reach this case.
2. **The architecture is one architecture.** Dimensions d02 through d06, which is
   the whole immutability, artifact, upgrade, rollback and customization story, are
   the same mechanism in all three. Separate entries would duplicate five
   dimensions and make `transactional-snapshot` appear two or three times in every
   comparison table, reading as that much more prevalent than it is. That is the
   mirror image of the under-representation this addition exists to fix.
3. **The Pulse already set the precedent for a community upstream and a
   commercial downstream.** Fedora CoreOS has a profile; Red Hat's image-mode
   product appears as a line item inside `bootc.yaml`. Giving SUSE's commercial
   product its own peer entry while Red Hat's stays a line item would apply a
   distinction where it is convenient rather than consistently, which is the
   failure control 4 in section 9 exists to prevent.
4. **The names do not split where the products do.** openSUSE Leap Micro is the
   community rebuild of SUSE Linux Micro, not of MicroOS, so a two-file split named
   for MicroOS and SLE Micro would have to place Leap Micro in one of them
   arbitrarily.
5. **The vendor is converging the commercial vehicle into its enterprise server.**
   SUSE published on 2026-02-23 that SUSE Linux Enterprise Server 16.1 adds an
   Immutable Mode carrying SUSE Linux Micro's characteristics, with a committed
   upgrade path from SUSE Linux Micro 6.2, and 6.2 already identifies itself as
   SLES 16.0 in `/etc/os-release`. Standing the commercial product up as a peer
   entry in a point-in-time snapshot, at the moment its vendor is folding it into
   something else, would give a reader a map that is wrong within one release.

Where the vehicles genuinely differ, each dimension records them as separate named
fields rather than averaging them. The differences are sharpest on support model,
certification, architectures, Kubernetes pairing, fleet tooling and governance, and
the profile says so in each place.

One further honesty note. No primary source found in this research states that
openSUSE MicroOS is the upstream of SUSE Linux Micro. The documented relationship
is that Leap Micro is a rebrand of SUSE Linux Micro. The lineage question is
recorded in the profile's `open_questions` rather than asserted.

**Ubuntu Core needed a new vocabulary value.** Its OS state is a set of
independently versioned read-only squashfs images, of which one serves as the root
filesystem, so the kernel and the root filesystem update independently of each
other. No existing axis C value described that without destroying the fact.
`snap-image-set` was added to the vocabulary and the schema. Adding a value changes
the meaning of no existing value and every existing profile still validates, so
`schema_version` stays at 1.0.0. Forcing the entry into `ab-partition-image` or
`package-repository` instead would have been precisely the single-label failure
section 3 rejects.

### Projects considered and excluded

Excluding a project is a methodological choice and is recorded as one.

**Amutable.** Not profiled, and listed under Worth mentioning. It has public
work, but no released OS image to check the dimensions against. Tracking only,
with no scoring against mature systems.

**openSUSE MicroOS, Leap Micro and SUSE Linux Micro.** Excluded since 2026-10-14,
because they do not meet R1. Each node builds its next snapshot from packages with
`transactional-update`, also when the repository is pinned. The profile
`microos.yaml` and its data sheet stay, so a reader can see the evidence. SUSE
still has an entry in the matrix: Elemental, its fleet-image path on the same
base. See "The fourteenth entry: Elemental" and item 12 in section 11. "The two
entries added after the first draft" explains why these three vehicles are one
profile.

**Ubuntu Core.** No longer excluded. Recorded as a known gap in the first draft
and since researched and added as `ubuntu-core.yaml`.

**Both omissions cut in the authors' favour, which is why they were flagged rather
than left implicit, and why they were closed rather than deferred.** MicroOS and
Ubuntu Core both sit in the same `general-purpose-host` position as Kairos.
Leaving them out made that part of the map look sparser than it is. That column is
no longer incomplete on the two counts the first draft knew about.

**balenaOS.** Excluded, because it does not meet R5. balenaOS is a Yocto-built
host OS for running containers on embedded devices. It has a read-only root
filesystem and A/B root partitions, and a failed update boots back into the
previous OS version. Its container engine is balenaEngine, based on Moby. balena
documents no Kubernetes support, so it does not meet R5. Sources, all retrieved
2026-10-12: the [balenaOS overview](https://docs.balena.io/reference/OS/overview/2.x/),
[OS updates](https://docs.balena.io/reference/OS/updates/self-service/) and
[balenaEngine](https://github.com/balena-os/balena-engine). On the
[balenaOS product page](https://www.balena.io/os) and on the overview page, a
search for "Kubernetes" found no match. That is a check of absence, not a quote.

**SUSE Linux Enterprise Server 16.1 in Immutable Mode.** Excluded, and tracked.
SUSE published in February 2026 that its enterprise server gains an immutable
installation mode carrying SUSE Linux Micro's characteristics, with a committed
upgrade path from SUSE Linux Micro 6.2. That is recorded inside `microos.yaml` as
a dated fact about where the commercial vehicle is going. It is not profiled
separately, because the artifact a reader would evaluate today is
SUSE Linux Micro 6.2. A later re-validation of `microos.yaml` should check
whether the converged product has become the thing to profile.

### Deliberately out of scope

Conventional mutable distributions are out of scope, even when they are a common
Kubernetes node OS. A node OS that updates in place with a package manager fails
R1 and R2, and does not answer the question this survey asks, and a field such as "immutable: no" would
only record that. Where a vendor ships an immutable product beside a mutable one,
the immutable product is the entry (Azure Container Linux, not base Azure Linux).

No destructive experiments: no power loss during upgrade, no corrupt image, no
kernel boot failure, no management-plane loss, no registry loss, no disk
corruption. No best-OS recommendations, persona winners, numeric rankings,
architecture verdicts, or long-form competitive analysis.

## 11. Where the method was challenged

Recorded so a reader can audit the reasoning rather than trust it.

1. **The single-label taxonomy was rejected** in favour of three axes. See
   section 3. The original list conflated three questions.
2. **Fedora CoreOS and bootc were separated** rather than merged into one entry,
   because a mechanism and a distribution are not peers. See section 3.
3. **Two competing projects were found missing from the scope, and both omissions
   flatter the authors' own project.** See section 10. They were recorded as known
   gaps rather than quietly left out, and then closed: openSUSE MicroOS and Ubuntu
   Core were researched against the same fourteen dimensions and added, taking the
   dataset from ten entries to twelve. Recording a gap is worth less than closing
   it, and the gap was on the axis where this survey's authors had the most to
   gain from silence.
4. **A radar chart and any aggregate score were ruled out at the schema level**,
   not at the editing stage. See section 8.
5. **A researcher who gathered the SUSE evidence recommended two profiles, and was
   overruled.** The recommendation was that SUSE Linux Micro and the community
   vehicles diverge enough on support model, subscription and certification to
   warrant separate entries. The reasoning for merging them anyway is set out in
   full in section 10, and rests on consistency with how the Pulse already
   treats Fedora CoreOS and Red Hat's commercial downstream. The disagreement is
   recorded rather than hidden, because a reader who thinks the researcher was
   right should be able to see that the question was live.
6. **The addition of Ubuntu Core forced a vocabulary change rather than a
   convenient mislabel.** Its substrate fitted no existing value on axis C, and the
   two nearest values would each have hidden the fact that its kernel and root
   filesystem update independently. A new value was added instead. See section 10.
7. **Kairos's `entry_kind` was re-examined on 2026-09-22 and tightened.** The
   first draft gave `kairos.yaml` three tags, `distribution`, `framework` and
   `base-images`, while this document's own table gave it two. The brief for the
   re-examination, from the project's own maintainer, was that Kairos should
   read as a framework, the way bootc reads as a mechanism, rather than being
   blurred across three categories.

   The `base-images` tag was removed. The base images in the Kairos-and-Hadron
   pair are Hadron's, published to be derived from, and they now have their own
   entry. Kairos's own published images are the released artifacts, which
   `distribution` already covers. Carrying `base-images` on Kairos was hedging.

   The `distribution` tag was kept, and this is where the brief was not followed
   as given. The vocabulary defines a distribution as one that "ships released
   OS artifacts with versions and a release process". Kairos does: 109 stable
   releases, bootable ISOs with Kubernetes bundled, a release cadence, a support
   statement, hardware findings that are findings about released images. bootc
   ships none of that, which is why four of its dimensions are not applicable.
   Dropping `distribution` from Kairos would have marked those same dimensions
   not applicable for the authors' own project, and the findings recorded there
   (riscv64 tooling only, cloud images that do not match their documentation, a
   bursty cadence with no support lifecycle) are among the least flattering in
   the profile. Removing the tag would have removed them. NixOS and Ubuntu Core
   carry both tags on the same reasoning. The order was changed to lead with
   `framework`, which matches the project's self-description and is the tag that
   decides how the entry is read.
8. **Cluster API was covered unevenly, and the uneven coverage flattered the
   authors' own project.** The first pass mentioned Cluster API in three profiles
   and in none of the other nine, because no dimension asked about it. Two of the
   three that mentioned it were Kairos and Talos, the two entries that happen to
   ship providers of their own. A reader comparing those three against the silent
   nine would have concluded that the other nine have nothing, which is wrong for
   at least four of them.

   It was then researched for all twelve on the same terms and recorded under
   `d12_fleet_management.normalized.cluster_api`, with the same three absence
   values as everywhere else. No new dimension was added: the question fits inside
   fleet management, and inventing a fifteenth dimension for a capability the
   authors' own project ships would be exactly the failure control 7 in section 9
   exists to prevent.

   The result does not flatter anyone consistently, which is the point. Kairos
   has the most complete provider set in the dataset and the youngest, at pre-1.0
   with four months of release history, absent from every shipped `clusterctl`,
   and still listed as coming soon on its own site. Talos owns the only providers
   the published upstream list names and has deprecated all three, the two
   Cluster API providers in August 2026 and Sidero Metal in March 2024. The
   project with the most usable integration, Flatcar, ships no provider at all.
   An earlier version of `talos.yaml` recorded that its providers were migrating
   to kubernetes-sigs; no such repository exists and the deprecation notices point
   elsewhere, so that claim was corrected.

9. **Every profile was fact-checked a second time, one week after collection,
   and the pass found errors in both directions.** On 2026-09-22 every cited
   source in every profile was re-read, every quote checked against the live
   page, and every time-sensitive fact re-verified. The corrections live in each
   profile's `corrections` list, dated, with the source. Three patterns are worth
   recording here because they are about the method, not about one project.

   Absence claims resting on missing documentation were found in competitors'
   profiles, which is the exact failure control 3 exists to prevent, and they
   were downgraded to `unknown`: an SBOM, a FIPS claim and a download path for
   Container-Optimized OS, an SBOM and a support bundle for NixOS, a commercial
   support offering for Flatcar that its own site describes in the past tense.
   One absence claim about a competitor was simply wrong: Unikraft was recorded
   as having no governance document and no maintainers file, and it has a
   governance repository with per-SIG maintainer lists.

   Facts that moved in the week between collection and re-verification were
   recorded as "moved since collection" rather than silently updated, so the
   two dates stay diffable. bootc, Container-Optimized OS and Hadron all
   released in that week.

   The fact-checkers were also asked, per profile, whether the entry was
   treated more softly or more harshly than `kairos.yaml`. The recurring
   answer was a tone note: several profiles describe a project's documentation
   as "honest", "candid" or "unusually" clear, and a few rank a capability
   against the rest of the dataset ("the deepest rollback capability in this
   edition", "the strongest governance position"). `kairos.yaml` uses the same
   register about itself ("the cleanest OCI-native artifact model", "a genuine
   strength"), so this is the dataset's voice rather than an asymmetry, and
   only one adjective was removed. The cross-entry superlatives are flagged
   here because they sit close to the no-ranking rule in section 8: they are
   backed by facts in the same dimension, but a reader cannot check "in this
   edition" from one profile. The article pass, not the data pass, is where
   that wording should be settled.
10. **Azure Linux was profiled although it is not immutable.** The first draft
    recorded base Azure Linux as `adjacent`, a mutable package-based distribution
    with a separate immutable sibling product. On 2026-10-05 the base entry was
    removed. Wide deployment does not put a mutable distribution in an
    immutable-OS survey, so the immutable product Microsoft ships, Azure
    Container Linux, is profiled instead. The scope line is in section 10.
11. **The inclusion criteria were written down on 2026-10-05** (first called inclusion rules; renamed 2026-10-06). Until then, scope
    was decided entry by entry, and the reasons lived in the notes above. R1 to
    R5 in section 10 now state the test, and each entry's case for R5 has a
    source. Two results are recorded rather than smoothed over. openSUSE MicroOS
    is borderline on R5: its Kubernetes path is a separate SUSE product, and the
    community guide is unmaintained. bootc meets R5 only through Red Hat's
    MicroShift images, not through anything bootc ships. Openness was
    deliberately not made a rule. A rule on openness would have changed who
    appears based on governance, which d13 already reports for every entry.
    On 2026-10-06, R1 became "versioned whole-system updates". Two readings
    were tested against all eleven entries, with an independent check. Under a
    strict reading (a version guarantees the same OS files on every node), four
    entries pass: Bottlerocket, Container-Optimized OS, EVE-OS and Talos Linux.
    Six entries let a node add files to the OS part while its version stays
    the same, through system extensions, package layering or per-snap refresh.
    Under the capability reading (the project documents a way to run it so
    that one version names the whole OS), all eleven pass, some with a
    condition. R1 uses the capability reading, the same rule the matrix
    columns follow: they record what is possible, not what ships switched on.
12. **On 2026-10-14, R1 and R3 changed to a fleet reading.** A cloud native OS
    is judged across a fleet, not on a single node. R1 now asks for one OS
    artifact, built once, that every node in a fleet runs. A fleet updates or
    rolls back by pointing it at a version. A node that assembles its own update
    from packages does not meet R1. R3 now asks for a rollback to the previous
    fleet version, which each node keeps locally, ready to boot. The five
    criteria carry the display names Atomic updates (versioned OS), Immutable
    (read-only OS files), Rollback, Declarative provisioning and Kubernetes
    ready. The ids R1 to R5 stay. The old names stay as aliases: Versioned whole-system updates (R1), Immutable at runtime (R2), Rollback (R3), Declarative provisioning (R4) and Runs Kubernetes (R5). R1 always shows as
    "Atomic updates (versioned OS)" and never as "Atomic updates" alone, because
    MicroOS updates are atomic and still do not meet R1.
    On 2026-10-15 the names changed to match the KCD UK talk. R2 shows as
    Immutable at runtime (read-only OS files) and R3 as Rollback (to a version).
    R3 is a rollback to the previous OS version, not to a snapshot of one node.
    R1 and R5 keep the names above, and the ids R1 to R5 stay. The new R2
    name only adds "(read-only OS files)" to Immutable at runtime, the name R2
    had before 2026-10-14. Immutable (read-only OS files) and Rollback, as the
    site showed them on 2026-10-14, are old names of R2 and R3.
    Results. openSUSE MicroOS leaves the matrix: each node builds its next
    snapshot from packages, also from a pinned repository. SUSE still has an
    entry, because Elemental enters as SUSE's fleet-image path on the same base.
    Ubuntu Core passes R1 with a condition: the fleet's OS version is the signed
    model assertion plus an enforced validation set that pins the snap
    revisions. Without one, each device refreshes its snaps on its own. The other
    nine matrix entries and Hadron consume or derive a centrally built image and
    keep their results. For R3, the entries that keep a previous artifact pass.
    Azure Container Linux and Container-Optimized OS stay in the matrix with R3
    "unknown", because the method never reads a missing document as a "no"
    (section 4). Their documented rollback happens at the node pool, and the
    profiles record that as an open question.
13. **On 2026-10-15, R4 was renamed Config-driven provisioning.** Not every
    tool is declarative. Ignition, Bottlerocket settings and Talos machine
    config describe an end state. yip and cloud-init also run commands in
    order, and the configuration management tools are mixed too: Puppet is
    declarative, Ansible and Chef run steps. What all eleven matrix entries
    share is a written config that the node applies with no hands on it. The
    old name, Declarative provisioning, stays as an alias. No entry entered or
    left the matrix. The `runs` and `reruns` fields of `d09_provisioning` became
    four fields per tool: `earliest`, `latest`, `repeat` and `scope`, each with
    a source in `field_sources`. A cell without a source is `unknown`. The
    filter no longer splits Kairos from the Ignition projects: all of them run
    before switch_root. The Elemental value `initramfs-before-root` was wrong,
    because the earliest stage runs after the root is mounted in /sysroot.
14. The remaining challenges appear in each profile's `open_questions` and in
    `follow-up-research.md`.

## 12. Correcting this

Open a pull request against the project's YAML profile, with the primary source
for the correct value. Corrections are recorded in the profile's `corrections`
list with the date and source, so the change history lives in the data.

Maintainers of any project covered here are invited to correct their own
project's factual profile. The ask is to verify **factual representation only**.
It is not a request to endorse, approve, or agree with any analysis, and a
correction does not imply the maintainer agrees with anything else in this
document. See `maintainer-review.md` for the per-project question lists.
