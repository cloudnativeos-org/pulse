# Pulse vocabularies

Schema version **1.0.0**.

Every normalized field in a project profile draws from a closed vocabulary
defined here. Free prose belongs in `summary`, `notes`, and `tradeoffs`, never in
a normalized field.

**Rule for future editions:** never change the meaning of a value that already
exists. Add a new value and deprecate the old one in this file. An edition
comparison is only meaningful if the values mean the same thing in both.

---

## 1. The three absence values

These are different facts and the schema keeps them apart. Collapsing them is the
single most common way a comparison like this becomes misleading.

| Value | Meaning | Required evidence |
|---|---|---|
| `none` | The concept applies to this architecture, and the project documents that it has no such capability. | `evidence: DOCUMENTED` and at least one source. A value of `none` asserts a documented absence. |
| `unknown` | The concept applies, and we could not determine the answer from primary sources. | `evidence: UNKNOWN`, plus a `searched` note saying where we looked. |
| `not-applicable` | The concept does not exist in this architecture. Asking the question is a category error. | A `notes` entry explaining why the concept does not apply. |

Missing documentation is never evidence of absence. If in doubt, the value is
`unknown`, not `none`.

## 2. Evidence labels

Applied per dimension, not per profile.

| Label | Meaning |
|---|---|
| `DOCUMENTED` | Explicitly stated by a primary source. Requires at least one source URL. |
| `REPRODUCED` | We independently built or ran it and got the documented result. |
| `OBSERVED` | We measured the behaviour directly. |
| `INFERRED` | A reasonable conclusion from evidence that does not state it outright. Requires an `inferred_from` note naming the evidence. |
| `UNKNOWN` | Insufficient evidence. Requires a `searched` note. |
| `NOT_TESTED` | Answering it requires experiment, and this edition does not run experiments. |

The 2026 edition is a documentation survey. Expect `DOCUMENTED`, `INFERRED`,
`UNKNOWN`, and `NOT_TESTED`. `REPRODUCED` and `OBSERVED` are reserved for later
editions that run the experiment protocols.

## 3. Source types

| Value | Meaning |
|---|---|
| `official-docs` | The project's own documentation site or in-repo docs. |
| `source-repo` | Source code, build files, or configuration in an official repository. |
| `design-doc` | An architecture document, enhancement proposal, RFC, or design record. |
| `governance-doc` | GOVERNANCE, MAINTAINERS, OWNERS, CHARTER, LICENSE, trademark policy. |
| `release-notes` | Release notes, changelog, or a release listing. |
| `announcement` | An official project or vendor announcement. |
| `maintainer-statement` | A named maintainer speaking in an official channel. |
| `foundation-page` | A foundation's own page about the project (CNCF, Linux Foundation). |
| `vendor-docs` | Vendor product documentation for a commercial product built on or around the project. Acceptable for product facts. Never used as evidence about a competing project. |
| `paper` | A peer-reviewed or preprint paper by the project team, used as a design document. |

Marketing comparison pages published by any project about any other project are
not an acceptable source for any claim in this dataset, including claims about
the publishing project itself.

---

## 4. Entry kind

What sort of thing the entry is. Multi-valued. This exists because the survey
covers things that are not all the same kind of object, and comparing a
mechanism's release cadence against a distribution's is a category error.

| Value | Meaning |
|---|---|
| `distribution` | Ships released OS artifacts with versions and a release process. |
| `framework` | Primarily a toolchain for producing an OS, where the adopter owns the resulting artifact. |
| `mechanism` | A component or tool that implements part of the lifecycle, consumed by distributions. Not an OS on its own. |
| `base-images` | Publishes base images intended to be derived from, rather than run unmodified. |
| `platform-os` | An OS produced primarily to run a specific vendor platform, made public as a side effect. |
| `build-system` | Builds an operating system image from source recipes. The project releases the build tooling and metadata, not an image to run. The adopter owns the built image, and each capability comes from the layers and configuration the adopter selects. |

A project may carry several. Kairos and NixOS are both `distribution` and
`framework`. `build-system` and `framework` both move the build, test, signing,
CVE response and support duty to the adopter. Applying this field only to some
entries and not others would itself be a bias, so it is required on every entry.

---

## 5. Category fit

How comparable the entry is to the rest of the survey.

| Value | Meaning |
|---|---|
| `full` | Comparable on all fourteen dimensions without distortion. |
| `partial` | Comparable on most dimensions, with named exceptions in `notes`. |
| `adjacent` | Belongs to a neighbouring category. Included because the contrast is informative, not because it is a peer. |

An `adjacent` entry is never scored against a `full` entry on a dimension it does
not share.

---

## 6. Taxonomy axis A: workload scope

**What the machine is for.** This axis uses the spectrum language the survey
brief itself proposes. It is descriptive. No position on it is better than
another, and the profile's `tradeoffs` field records what each position buys and
costs.

| Value | Meaning |
|---|---|
| `kubernetes-appliance` | The machine's contract is "a Kubernetes node". There is no general-purpose user space, by design. |
| `kubernetes-oriented-host` | A Linux host optimized and defaulted for container or Kubernetes workloads, but a host underneath. |
| `general-purpose-host` | A general Linux host. Kubernetes is one workload among many, or absent. |
| `single-application-image` | The unit of deployment is one application. There is no multi-tenant OS. |

## 7. Taxonomy axis B: construction model

**Who assembles the artifact you run.** Multi-valued.

| Value | Meaning |
|---|---|
| `vendor-fixed-image` | You consume published images. Customization happens through defined extension points, not by rebuilding. |
| `vendor-base-plus-derivation` | The project publishes a base intended to be derived or rebuilt by the adopter with standard tooling. |
| `framework` | The project is primarily a toolchain. The adopter produces, and therefore owns, the artifact. |
| `package-repository-assembly` | The system is assembled from packages at install and update time, in the conventional distribution manner. |

`framework` is not a compliment. It moves the build, test, signing, CVE response,
and support burden for the resulting artifact to the adopter. A profile that
claims `framework` must record that cost in `tradeoffs.costs`.

## 8. Taxonomy axis C: root state substrate

**What holds the OS state.** Multi-valued, because some projects offer more than
one.

| Value | Meaning |
|---|---|
| `ab-partition-image` | Two or more whole filesystem images in alternating partitions. Boot selects one. |
| `ostree-deployment` | An OSTree commit checked out as a deployment, with hardlinked shared objects. |
| `bootc-container-deployment` | An OCI container image deployed as the bootable root, via bootc. |
| `nix-store-generation` | A hash-addressed store plus a generation symlink tree. |
| `unikernel-binary` | Application and kernel compiled into a single bootable binary. |
| `package-repository` | A conventional package database, updated in place. |
| `transactional-snapshot` | A filesystem snapshot taken per transaction, with the new snapshot becoming the next boot target. |
| `snap-image-set` | A set of independently versioned, independently refreshable read-only squashfs images, one of which serves as the root filesystem, on a fixed partition layout. |

`snap-image-set` was added while the 2026 edition was still being assembled, for
`ubuntu-core.yaml`. Adding a value is backward compatible, because it changes the
meaning of no existing value and every existing profile still validates, so
`schema_version` stays at 1.0.0. The value exists because no other one described
the arrangement without destroying a fact: the kernel and the root filesystem are
separate images that update independently, which `ab-partition-image` and
`package-repository` would both have hidden. Forcing one label onto it is the
failure this survey's taxonomy exists to avoid.

---

## 9. Integrity mechanism (dimension 2)

| Value | Meaning |
|---|---|
| `dm-verity` | Block-level integrity verified against a signed or trusted root hash. |
| `read-only-mount` | The filesystem is mounted read-only. Integrity is not cryptographically verified at runtime. |
| `ostree-immutable-checkout` | OSTree's own checkout model, where the deployment root is made immutable. |
| `read-only-store` | A content-addressed store that is read-only at runtime. |
| `image-by-construction` | The artifact cannot be modified at runtime because there is no mechanism to do so. |
| `composefs` | A composefs-mounted image tree whose objects carry fsverity digests where the backend enables them. Digests alone do not bind the tree to a signature; that needs a sealed unified kernel image. |
| `none` | Nothing enforces immutability of the running system. |
| `unknown` | |

Multi-valued. `read-only-mount` and `dm-verity` are not equivalent and are never
reported as one value.

`composefs` was added on 2026-09-22 because `bootc.yaml` had used it since the
first draft without the value being defined here. Adding it changes the meaning
of no existing value, so `schema_version` stays at 1.0.0. It is kept separate
from `dm-verity` because the two verify different things: dm-verity checks a
block device against a root hash, composefs checks file objects against
per-file digests, and only the second can be present without a signature to
verify against.

### Mounts (dimension 2, added 2026-10-12)

The Mounts row of the data sheet reads these `d02` fields. Every entry has all
four lines.

- `read_only`, with `read_only_mechanism`: what is read-only, and how.
- `ephemeral`, with `ephemeral_mechanism`: paths the documentation says are
  discarded on reboot. Absent means none documented.
- `writable_and_persistent`: paths that persist. A persistent overlay carries
  "(overlay)" after the path.
- `configurable_paths`: `value`, `how` (one line), `evidence` and `sources`.
  `value` is `yes` (the documentation shows how to change which paths are
  writable or persistent, or to add more), `no`, `unknown`, or
  `via-lifecycle-manager` (a base distribution whose layout the framework sets).
- `immutability_can_be_disabled`, with `immutability_disable_where`.
- `mount_layout`: for a base distribution that documents no layout of its own,
  the sentence pointing to its lifecycle manager.
- `mounts_sources`: the sources behind the first three lines.

## 10. Upgrade mechanism (dimension 4)

| Value | Meaning |
|---|---|
| `ab-partition-switch` | Write the new image to the inactive slot, then switch the boot target. |
| `ostree-deployment` | Stage a new OSTree deployment and add a boot entry for it. |
| `bootc-container-deployment` | Fetch an OCI image and stage it as the next bootable root. |
| `generation-switch` | Build a new generation and switch the active profile and boot entry. |
| `package-update` | Update packages in place in the running filesystem. |
| `image-replacement-redeploy` | The instance is not upgraded. A new instance is created from a new image and the old one is destroyed. |
| `transactional-snapshot` | Apply changes in a snapshot and boot into it. |
| `snap-revision-refresh` | Each composing image is fetched and swapped to a new revision on its own, so the kernel, the root filesystem and applications update independently rather than as one artifact. |

`image-replacement-redeploy` is a real and common answer, particularly for
managed node pools. It is recorded as an upgrade mechanism rather than as an
absence, because for those platforms it is the intended path.

### Adding software to the OS (dimension 6, added 2026-10-12)

`d06.normalized.add_software` is a list. Each entry is one way an adopter adds
software to the OS itself, meaning host-level software, not workloads. An entry
has `kind`, `how` (one or two short sentences), `evidence` and `sources`. Each
`kind` appears once per profile. The values are closed:

- `systemd-sysext`: system extension images, merged over /usr.
- `vendor-extensions`: a project-specific extension format, such as Talos system extensions.
- `derive-image`: build a new OS image from the project's image, for example a Containerfile FROM it.
- `package-layering`: install packages onto the image-based system, for example rpm-ostree install.
- `transactional-packages`: install packages into a new snapshot, for example transactional-update pkg install.
- `snaps`: snap packages.
- `build-time-only`: the image is composed at build and nothing is added after.
- `not-supported`: the project states you cannot add software to the host.
- `unknown`: nothing was found. It stands alone, with evidence UNKNOWN and `searched`.

An entry that builds from a base distribution gets `derive-image` as its own
documented path. It does not get the base distribution's package manager after
install unless its own documentation says so (methodology rule 21).

## 11. Rollback and recovery (dimension 5)

Recorded as separate fields, never as one "rollback" answer.

- `rollback_to_previous`: `available` | `none` | `unknown` | `not-applicable`
- `automatic_rollback_on_boot_failure`: `available` | `none` | `unknown` | `not-applicable`, plus `trigger` and `attempts` free-text fields when available
- `retained_versions`: integer, `configurable`, or `unknown`
- `recovery_environment`: `dedicated-partition` | `live-media` | `vendor-hosted` | `host-container` | `none` | `unknown`
- `factory_reset`: `available` | `none` | `unknown`
- `network_independent_recovery`: `yes` | `partial` | `no` | `unknown`

"Automatic rollback" means the machine itself reverts without an operator or a
management plane deciding to. A fleet manager that notices a broken node and
reimages it is a different capability, and it is recorded under dimension 12.

## 12. Kubernetes relationship (dimension 7)

- `requirement`: `required` | `optional` | `unrelated`
- `bundled`: `bundled` | `separately-installed` | `none` | `not-applicable`
- `independent_lifecycle`: `yes` | `partial` | `no` | `unknown` (can the OS and Kubernetes be upgraded independently?)
- `os_manages_kubernetes`: `yes` | `no` | `unknown`
- `kubernetes_manages_os`: free text naming the mechanism, or `none` / `unknown`
- `distributions`: list of Kubernetes distributions documented as supported

## 13. Fleet management (dimension 12)

Three buckets, always kept apart:

- `core_project`: capability inside the OS project itself
- `oss_companion`: open-source tooling, with `name`, `repo`, `license`, `org`
- `commercial`: commercial products, with `name`, `vendor`, `license`, `self_hostable`

A capability in the `commercial` bucket is never described as a capability of the
open-source OS.

## 14. Governance (dimension 13)

Four properties, deliberately separate, because they are independent:

| Field | Values | Question it answers |
|---|---|---|
| `open_source` | `true` / `false` / `partial` | Is the source available under an OSI-approved licence? |
| `open_governance` | `documented` / `partial` / `undocumented` / `none` | Is there a published decision-making process that a non-employee can participate in? |
| `vendor_neutral_ownership` | `foundation-held` / `single-vendor` / `mixed` / `unknown` | Who holds the trademark and project assets? |
| `contribution_diversity` | object with `method` and `value` | How many distinct organizations actually contribute? Always records how it was measured. |

A project can be open source with single-vendor ownership and undocumented
governance. Another can be foundation-held with a single dominant contributor.
These are four readings, not one score, and they are never summed.

`contribution_diversity` always states its method, because the method changes the
answer. Commit-author email domains, for example, undercount contributors who use
personal addresses, and that caveat is recorded with the value.

## 15. Maturity (dimension 14)

- `first_release`: date or `unknown`
- `current_version` / `current_version_date` / `channel`
- `release_cadence`: free text, backed by observed intervals, with `observed_intervals` listing the actual gaps used
- `support_model`: `rolling-no-lts` | `lts-stream` | `versioned-with-eol` | `vendor-lifecycle` | `unknown`
- `support_window`: free text with concrete dates where published
- `commercial_support`: `available` | `none` | `unknown`, with the vendor named

GitHub stars, download counts, and contributor counts are not recorded as quality
signals anywhere in this dataset.

### Configuration tools (dimension 9, added 2026-10-15)

`d09.normalized.config_tools` is a list. Each entry is one config-driven
provisioning tool. It has four fields, each from a closed vocabulary. `repeat`
and `scope` are lists. Every other field is one value. The old `runs` and
`reruns` fields are retired.

- `earliest`: `initramfs` (one value, whether the root is mounted yet or not), `before-services` (before kubelet), `installer`, `userspace-boot`, `none-of-its-own`, `depends-on-tool`, `unknown`.
- `latest`: `first-boot`, `every-boot`, `running-node`, `depends-on-tool`, `unknown`.
- `repeat`: every documented way the config is applied. `once` is the first boot or install. `every-boot`, `on-demand` (API or CLI), `reconcile` (the node applies it again on its own), `depends-on-tool`, `unknown`.
- `scope`: `settings-only`, `files-and-units`, `any-command`, `depends-on-tool`, `unknown`.

Each value other than `unknown` needs a `field_sources` entry whose `fields`
list names it, with a `url`, `retrieved` and a `quote` or a `note`. `unknown`
stands alone in its field. A cell without a source is `unknown`. `cell_notes`
holds caveats that the cell cannot show.
