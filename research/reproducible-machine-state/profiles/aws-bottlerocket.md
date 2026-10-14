# AWS Bottlerocket: platform profile

Tracked as ,
the research epic, Reproducible
Machine State.

Bottlerocket is a Linux-based operating system for hosting containers, built by AWS, released
under Apache-2.0 or MIT at the user's option, and developed in public on GitHub. It has no package
manager. The unit it ships is a whole disk image, built for a named *variant* that fixes the
platform, the orchestrator and the orchestrator's minor version at build time. It belongs in this
investigation as the representative case of the hyperscaler container-host appliance model: an
operating system produced by the same company that operates the platform it mainly runs on, and
optimised for a fleet of interchangeable nodes rather than for a machine an operator keeps. What
makes it worth a deeper pass than a sibling in the same family is that the hyperscaler framing and
the open-source framing are both true at once. The update state machine, the rollout controls, the
partition-flip mechanics and the repository publishing tooling are all in the open-source tree.
That makes the framework's independence question answerable from primary sources rather than
guessable, which is exactly what this epic wants from at least one system in the hyperscaler tier.

**Depth tier: representative. This pass is the architecture study only.** The epic's stratification
puts Bottlerocket at "architecture study plus representative lifecycle experiments." No lifecycle
experiment was run here, and that is a scope decision recorded on the ticket before the work
started, not an omission: no experiment protocol, report template or infrastructure decision exists
yet for this tier. The methodology issue that was to produce them,
the methodology plan, was superseded by
the Pulse brief before it did, and the Pulse brief only
covers the lighter documentation-only Pulse profile. Section "What a lifecycle experiment pass
needs" below scopes the missing half precisely, so that the gap is a costed decision rather than a
silence.

**What that means for evidence labels.** Bottlerocket documents its update and rollback machinery
in unusual detail, and where it does, this profile describes it fully and labels it DOCUMENTED.
"What does the rollback mechanism do, according to the project" is a documentation question and is
answered here. "Does the rollback actually work when we force it, and how long does it take" is an
experiment question and is marked NOT TESTED / OUT OF TIER SCOPE. Nothing in this profile is
REPRODUCED. A small number of claims are labelled OBSERVED, and in every case that means a
measurement taken against the GitHub or the documentation site's HTTP API on 2026-09-16, with the
query stated. No Bottlerocket instance was booted.

**A note on source depth.** Bottlerocket's implementation source is public and permissively
licensed. Reading it is a primary source, not reverse engineering, and this profile does read it
where prose documentation stops short: the update state machine's transitions, the GPT attribute
manipulation, and the systemd unit that decides a boot was successful all come from the source
repositories. Every such claim says so and links the file. This is a real difference from the
sibling profile for Google Container-Optimized OS, where the equivalent internals are not
published and the profile correctly left them UNKNOWN.

---

## Version and data provenance

| Field | Value |
|---|---|
| Version observed | `v1.65.0` |
| Release date | 2026-09-09 (`published_at` 2026-09-09T19:16:57Z) |
| Channel | latest non-prerelease GitHub release |
| Repository | [bottlerocket-os/bottlerocket](https://github.com/bottlerocket-os/bottlerocket), default branch `develop` |
| Licence | Apache-2.0 OR MIT, contributors retain copyright ([COPYRIGHT](https://github.com/bottlerocket-os/bottlerocket/blob/develop/COPYRIGHT)) |
| Documentation version cited | `1.64.x` on bottlerocket.dev |
| Data collected | 2026-09-16 (Pulse baseline collected 2026-09-15) |
| Primary source | [Bottlerocket v1.65.0 release notes](https://github.com/bottlerocket-os/bottlerocket/releases/tag/v1.65.0) |

Re-verified on 2026-09-16 against the GitHub releases API. `v1.65.0` is still the newest
non-prerelease. The five preceding releases are `v1.64.0` (2026-07-29), `v1.63.0` (2026-07-17),
`v1.62.1` (2026-06-22), `v1.62.0` (2026-06-01) and `v1.61.0` (2026-05-18). The main repository was
last pushed 2026-09-15. OBSERVED, via `gh api repos/bottlerocket-os/bottlerocket/releases`.

**The documentation site lags the release by one minor version, and this profile cites the
published version rather than inventing a URL.** `https://bottlerocket.dev/en/os/1.65.x/...`
returns HTTP 404 as of 2026-09-16; `1.64.x` returns HTTP 200. There is no `latest` alias path on
the OS documentation tree either. Concept and update pages are therefore cited at `1.64.x`, and
repository documents are cited on `develop`, which tracks ahead of both. OBSERVED, via HTTP status
checks on 2026-09-16. Where a `1.64.x` page and the `develop` tree disagree, this profile says so.

**GitHub releases carry no binary artifacts.** The five most recent releases each have zero
assets. The release notes are the artifact; images reach users as AMIs, as OVAs, or through the
TUF repository with `tuftool`. OBSERVED, via
`gh api repos/bottlerocket-os/bottlerocket/releases --jq '.[].assets | length'` on 2026-09-16.

**Relationship to the Pulse baseline.** A sibling ticket,
the Pulse brief, produced a 14-dimension Pulse
entry for Bottlerocket on 2026-09-15 (`data/projects/bottlerocket.yaml`).
This profile treats that entry as a sourced factual baseline, reuses its citations where they
overlap, and does not contradict any of its cited facts. Three places where this profile goes
further from new primary evidence are flagged inline: the update state machine's exact states and
transitions, the criterion that marks a boot successful, and the Secure Boot signing profiles
available to an operator. All three are extensions, not corrections.

---

## 2. Unit of OS deployment

**The unit is a complete disk image, identified by variant, architecture and version.** There is no
package manager and no runtime package installation, which the project states as a design position
rather than a limitation: "Bottlerocket is not a general purpose Linux distribution and
intentionally doesn't have a package manager. Instead Bottlerocket has variants." A variant is a
pre-defined set of drivers, tools and applications tailored to an architecture, a platform and an
orchestrator, plus an optional flavour. The documented artifact naming convention makes the
identity explicit:

```
[platform]-[orchestrator]-[orchestrator version](-[flavour])-[architecture]-[version]-[commit]
bottlerocket-aws-k8s-1.25-nvidia-aarch64-1.13.0-<commit>.img
```

The distinction the documentation draws is worth keeping: "you do not directly install a variant on
a machine or instance, you install an image that is a build of the components contained in the
variant at a specific Bottlerocket version." Variant and version are two orthogonal coordinates,
and the Bottlerocket version moves freely across many variants.

**What the artifact contains.** The OS disk carries two partition *sets*, each with three
partitions: a boot partition holding `vmlinuz` and the GRUB configuration, a root partition holding
the read-only `/` filesystem, and a hash partition holding the full dm-verity hash tree for that
root. Kernel and userspace therefore ship together inside one partition set, and the boot assets
are not versioned or distributed separately from the root filesystem: the set is the unit. The
GRUB configuration in each boot partition references its own set's root and hash partitions by
offset, which is what makes a single GPT priority flip select all three at once. Outside the two
sets the root device also holds the bootloader, and a private partition that carries the
Bottlerocket API data store. A second device, the data device, is mounted at `/local` and holds
container images, orchestrator state, host containers and bootstrap containers.

**Distribution is a TUF repository, not an OCI registry.** Four metadata roles establish trust:
`root`, `timestamp`, `snapshot` and `targets`, each individually signed. `root.json` ships inside
the image and begins the chain; it can be rotated from the repository if the new root is signed by
enough keys from the old, and Bottlerocket uses multiple root keys with a threshold so that losing
some keys below the threshold does not prevent rotation. `targets.json` lists every available
target file and its hash, including `manifest.json` and every update image and migration file. The
consequence the updater documentation draws is the load-bearing one for this dimension: "Any file
listed in the manifest is also a TUF 'target' listed in targets.json and can only be downloaded via
the TUF repository, preventing the client from downloading untrusted data."

**Content-addressability comes from TUF, not from a container digest.** Targets are hash-pinned in
signed metadata, and on disk the targets directory is shared across variants and architectures
"since target files are prefixed with a checksum." That is content-addressable storage with a
signed index on top, reached over plain HTTP(S) rather than through a registry protocol.

**OCI registries are used, but for build inputs and for host containers, not for the OS.** A *kit*
is "a container image with RPM packages in it", published to Amazon ECR Public and consumed by the
build system; the core kit and kernel kit are the two that every build pulls. The admin and control
host containers are ordinary OCI images, also on ECR Public by default. The operating system itself
never travels as an OCI image. An operator who wants "the OS in my registry" does not get that
shape here.

**Mirroring and self-hosting are documented from the publisher's side.** A built repository is
synced wherever the operator wants: "One good place to store repos is S3 ... You can also store
your repo behind any HTTP server; the key part is that the repo is accessible from your host." A
`file://` URL is supported for a locally held repository. Hosts are pointed at it either at build
time, by changing the `settings.updates.targets-base-url` and `metadata-base-url` defaults for the
variant, or at run time through user data. The two settings are first-class and documented in the
settings reference, with the default `targets-base-url` given as
`https://updates.bottlerocket.aws/targets/`.

**Signing is operator-controllable.** Running `cargo make repo` with no configuration generates a
root role and a single signing key with a threshold of 1, which the guide calls "functional, but a
bit basic" and advises against for production. Real deployments are expected to use multiple root
keys with a higher threshold, a separate publication key covering the `snapshot`, `targets` and
`timestamp` roles, and keys held in a local file, an AWS SSM SecureString parameter, or AWS KMS.
Each metadata role also expires on a policy; the default is a short timestamp expiry with longer
snapshot and targets expiries, and the guide warns that a repository which is not re-signed before
expiry will stop serving its hosts.

**Independent building is documented in full, bit-for-bit reproducibility is not.** `cargo make`
builds every package from source inside the Bottlerocket SDK container. The stated cost is
concrete: over 80GB in the local directory, and a first build of roughly 12 minutes on the fastest
machines to 3-4 hours on a couple of cores. Nothing in the repository claims that a third-party
build of a given tag is byte-identical to the AWS-published image, and no such verification tooling
was found.

**Air-gapped operation is partial, and the gap is on the registry side rather than the update
side.** The TUF half is fully self-hostable as described above. The other half is not documented
end to end: host containers pull from ECR Public by default, and the build pulls SDK and kit images
from the same place. Twoliter's design document lists "Maintainers must be able to host their own
copies of any required container images or source archives" as a requirement, which states the
intent clearly but is not a runbook. No end-to-end air-gapped deployment guide was found.

**What this unit of deployment buys and what it costs.** It buys a machine whose state is
determined by two coordinates plus a settings store: there is no package database, no partially
applied transaction, and no local file edit that can make the next update behave differently. The
project makes that claim itself, in the security document's framing of why `/etc` is a tmpfs. It
costs three things. First, the orchestrator's minor version is part of the artifact's identity, so
a Kubernetes minor upgrade is a different artifact and therefore a node replacement (dimension 7).
Second, the artifact is a disk image, so the ecosystem of registry tooling that image-based systems
built on OCI can reuse does not apply. Third, there is no smaller unit than the whole image: a
one-package security fix and a kernel change arrive the same way, at the same size, through the same
reboot.

**Evidence**

- DOCUMENTED: no package manager, variants as the substitute, artifact naming, variant-versus-version orthogonality, the update-versus-migration table. Source: [Variants concept page](https://bottlerocket.dev/en/os/1.64.x/concepts/variants/)
- DOCUMENTED: two partition sets of three partitions each; boot holds `vmlinuz` and `grub.cfg`; hash holds the dm-verity tree; `grub.cfg` references root and hash by offset. Source: [signpost README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/signpost/README.md)
- DOCUMENTED: root device holds the partition sets, bootloader, verity hash tree and API data store; data device at `/local` holds container images and orchestration state. Source: [Bottlerocket README, Default Volumes](https://github.com/bottlerocket-os/bottlerocket/blob/develop/README.md)
- DOCUMENTED: four TUF roles, root rotation with a signing threshold, targets-only download path. Source: [updater README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/README.md)
- DOCUMENTED: repository hosting on S3 or any HTTP server, `file://` support, checksum-prefixed target filenames, root and publication key separation, key storage in file/SSM/KMS, expiration policy. Source: [PUBLISHING.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/PUBLISHING.md)
- DOCUMENTED: `settings.updates.metadata-base-url` and `targets-base-url` as settable settings, and the default targets URL. Source: [settings.updates reference](https://bottlerocket.dev/en/os/1.64.x/api/settings/updates/)
- DOCUMENTED: a kit is "a container image with RPM packages in it"; out-of-tree maintainers must be able to host their own copies of required images. Source: [Twoliter design document](https://github.com/bottlerocket-os/twoliter/blob/develop/docs/design/README.md)
- DOCUMENTED: build from source with `cargo make`, 80GB and 12 minutes to 4 hours, AMI registration with `cargo make ami`. Source: [BUILDING.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/BUILDING.md)
- OBSERVED: GitHub releases carry zero assets, on the five most recent releases, queried 2026-09-16.
- UNKNOWN: whether a third-party build of a given tag reproduces the AWS-published image bit for bit. No reproducibility claim or verification tool was found in the repositories read.
- UNKNOWN: an end-to-end air-gapped procedure covering both a mirrored TUF repository and mirrored host-container and kit images. Carried forward from the Pulse baseline and not closed by anything read here. Per the framework, absence of documentation is not evidence that it does not work.

---

## 4. Upgrade mechanism

This is the dimension where Bottlerocket's documentation is strongest, and the state machine can be
described end to end without inference. Two components split the work: `thar-be-updates` owns the
logical update state, and `signpost` owns the on-disk partition priority bits. `updog` sits between
them and talks to the TUF repository. `apiclient` is the operator-facing front end and drives all
of it over a local Unix socket.

### Before the upgrade

**Where the new OS comes from.** A TUF repository, at whatever URL the two `settings.updates.*`
base-URL settings point to. The default is the project's own repository; an operator can change it
at build time in the variant's defaults or at run time through user data or an `apiclient set`
call. Nothing about the update path requires the project's repository specifically.

**Who initiates.** An operator or an automation, never the OS on a fixed schedule of its own
choosing. At its core, the documentation says, "an in-place update is a call to the Bottlerocket API
server using apiclient." Four documented automations wrap that call: the Bottlerocket update
operator (brupop) on Kubernetes, the Bottlerocket ECS updater on ECS, SSM Command Documents on
either, and direct `apiclient` from the control container. The documentation is explicit that the
EKS Console and `eksctl` paths are *node replacement*, not in-place updates, and tabulates the two
categories separately. That distinction matters for this epic, because two very different machine
lifecycles hide behind the single word "update."

**How the artifact is verified.** Through the TUF chain described in dimension 2. `updog` parses
`manifest.json` from the repository, and every file it then downloads is a hash-pinned target.

**Whether Kubernetes is required.** No. `apiclient` talks to an HTTP server on a local Unix-domain
socket. Kubernetes is one of several ways to reach that socket, not a dependency of the update
itself. DOCUMENTED and load-bearing for dimension 7.

**Whether the project's hosted infrastructure is required.** No, for the same reason: the client is
local and the repository location is a setting. See dimension 22.

**Guard rails `updog` applies before it will write anything.** Four, all documented: it considers
only version increases by default, with downgrades reachable by forcing a specific image; it
respects the `max_version` field in the manifest and refuses to go beyond it; it refuses updates
built for a different variant; and it "will ensure that appropriate migration files are available to
safely transition to the new version *and back*." That last one is the interesting one, because it
makes a working downgrade path a precondition of the upgrade rather than an afterthought.

**Rollout control lives in the OS.** Waves are defined by the publisher in `manifest.json` and
enforced by the client. Each node generates a seed, a number between 0 and 2048, which fixes its
position in the update order. A wave entry carries `start_after`, an offset from the moment the
operator updated the manifest, and `fleet_percentage`, an integer from 1 to 100 that maps directly
onto a fraction of the maximum seed. Until a node's computed time has passed, `updog` will not even
report an update as available. Waves are cumulative: "All waves include the seeds of the prior wave,
so if a node misses its wave for whatever reason, it still updates at a later time." The default
published policy is one hour of lead time, then 1% within 4 hours, 5% within 1 day, 15% within 2
days, 40% within 4 days, 60% within 5 days, 90% within 6 days, and 100% after 6 days; an accelerated
policy and an emergency policy ship alongside it. Two settings let an operator opt out per node:
`updates.ignore-waves` updates immediately, and `updates.version-lock` pins the node to a chosen
version. No management plane is involved in any of this. For a framework that asks which systems
need a commercial fleet product to stage a rollout, this is a notable answer.

### The update state machine

`thar-be-updates` "models the Bottlerocket update process after a state machine" and keeps its state
in `/run/update-status`, guarded by a lockfile that also controls disk access. A command that the
current state does not allow causes it to exit immediately with a status saying so; an allowed
command forks a child and returns 0 straight away, so the caller never blocks and reads the outcome
from the status file.

The four states and the transitions between them, read from the source:

| From | Command | To | Note |
|---|---|---|---|
| `Idle` or `Available` | `refresh` | `Available` if an update was found, else `Idle` | Re-reads the repository |
| beyond `Available` | `refresh` | unchanged | Refresh is allowed but does not move the state back |
| `Available` or `Staged` | `prepare` | `Staged` | Downloads and writes the image to the inactive set |
| `Staged` | `activate` | `Ready` | Flips the GPT priority so the new set boots next |
| `Ready` | `deactivate` | `Staged` | Reverses `activate` without discarding the written image |

`apiclient update check`, `apiclient update apply` and `apiclient reboot` are the operator-facing
shorthands; `apiclient update apply --check --reboot` collapses the whole sequence into one command.
The low-level equivalents are `POST /actions/refresh-updates`, `POST /actions/prepare-update`,
`POST /actions/activate-update` and `POST /actions/reboot`, with `GET /updates/status` returning the
current `update_state`, the `available_updates` list, the `chosen_update`, the `active_partition`
and the `staging_partition`.

The presence of `deactivate` is a small but real design detail: an operator can stage an update,
arm it, change their mind, and disarm it without re-downloading, all before any reboot.

### During the upgrade

**What gets written.** The full filesystem image, to the inactive partition set. The running
filesystem is not touched. The README states the model plainly: "Rather than a package manager that
updates individual pieces of software, Bottlerocket downloads a full filesystem image and reboots
into it."

**The exact GPT sequence.** `signpost` manipulates Chrome OS-style GPT attribute flags: bit 57
"have successfully booted before", bit 56 "successful boot flag", bits 55-52 "tries remaining", bits
51-48 "priority". The documented upgrade procedure is three steps, and the source shows what each
one sets:

1. `signpost clear-inactive` sets the inactive set's priority to 0, tries-left to 0 and successful
   to false, before anything is written.
2. The downloaded images are copied to the inactive partitions and validated.
3. `signpost mark-inactive-valid` sets tries-left to 1, then `signpost upgrade-to-inactive` sets the
   inactive set's priority to 2 and successful to false, and drops the active set's priority to 1.
   `upgrade-to-inactive` refuses to run unless the inactive set has already been marked valid, and
   refuses if it has already been marked for upgrade.

The signpost README compresses that to: "Run `signpost upgrade-to-inactive` to prioritize the
inactive partitions and allow it one boot attempt before automatically rolling back."

**Kernel, initrd and bootloader.** The kernel and the GRUB configuration live inside the boot
partition of the set being written, so they move with the set. The `grub.cfg` also carries the
dm-verity root hash for that set's root filesystem, which is what ties the three partitions
together. What an OS update does to the shim and GRUB binaries on the EFI system partition, which
sits outside both sets, is not described in any document read for this profile. That is left
UNKNOWN below rather than inferred, because it is precisely the sort of detail that decides whether
an update can break Secure Boot.

**Migrations are fetched before the update is allowed to start.** Settings migrations are targets in
the TUF repository, listed in the manifest for the version pair being crossed. "During this update
preparation process, all necessary migrations are downloaded and an update will refuse to start
otherwise." The reason given is that migrations run at boot, when the network may not be available,
so nothing can be fetched then. Skipping versions is supported and the migrations run in sequence:
updating 1.10.1 to 1.12.0 runs the 1.11.0 and 1.11.1 migrations as part of it.

**Power loss halfway through is not documented, and this profile does not pretend otherwise.** What
can be said from the documented mechanics is that `clear-inactive` zeroes the inactive set's
priority, tries and successful flags *before* any image bytes are written, so a set that is in the
middle of being written is not a set the bootloader will select, and the active set retains priority
2 throughout. That reasoning is INFERRED from the documented sequence, not stated by the project,
and the actual behaviour is NOT TESTED.

### At reboot

**How the new system is selected.** GRUB reads the GPT attribute flags and selects the boot
partition with the higher priority; that boot partition's `grub.cfg` then pulls in the matching root
and hash partitions by offset. There is no bootloader menu entry per version to manage, and no
separate boot configuration file for an operator to edit.

**How many attempts are allowed: one.** `mark_inactive_valid` sets tries-left to exactly 1. The
source comment is unambiguous: "Sets 'tries left' to 1 on the inactive partition to represent a
potentially valid image."

**How a successful boot is determined, and what is and is not checked.** A systemd unit,
`mark-successful-boot.service`, runs `/bin/signpost mark-successful-boot`. Its install section is
`RequiredBy=preconfigured.target`, and `preconfigured.target` is described as "Bottlerocket initial
configuration complete" and requires `basic.target`. The unit sets `RefuseManualStart=true` and
`RefuseManualStop=true`, with a comment that manually running it "could leave the system in an
unexpected state". `signpost mark-successful-boot` sets bit 56 on the active set and also sets the
"boot has succeeded" bit on the private partition.

The consequence is the single most important fact in this dimension, and it is a *narrow* health
check by design: **the boot-success criterion is that the OS reached its own initial-configuration
systemd target. Kubernetes health, kubelet registration, and workload health are not part of it.**
The project says the same thing from the other direction in the README: "It can automatically roll
back if boot failures occur, and workload failures can trigger *manual* rollbacks." An OS that comes
up cleanly and then fails to run any pods will mark itself successful and will not roll back on its
own. This is the extension over the Pulse baseline referred to in the provenance block: the baseline
recorded "boot not marked successful" as the rollback trigger, which is correct; this profile can
now say what marks it.

A second unit, `send-boot-success.service`, runs `metricdog send-boot-success` after
`configured.target` and `network-online.target`. It is a telemetry emission, not a gate: its
`ExecStart` is prefixed with `-`, so a failure does not fail the unit, and nothing in the rollback
path depends on it.

### After failure

**Rollback is automatic when the boot attempt is consumed without success.** "The system will
automatically roll back if it's unable to boot." Since the new set gets exactly one try and
`upgrade-to-inactive` left its successful bit false, a boot that never reaches
`preconfigured.target` leaves tries at zero and the old set, still at priority 1 with its successful
bit set, becomes the bootable choice.

**What persistent state survives.** The data device at `/local` is not part of either partition set,
and the README states that "the operating system does not typically make changes to this volume
during regular updates, though changes to upstream software such as containerd or kubelet could
result in changes to their stored data." Container images and orchestrator state therefore survive
the flip in both directions, with that upstream-software caveat attached. API settings live in the
data store on the root device's private partition, are migrated forward on upgrade, and have
migrations available in both directions as a precondition of the update.

**Where a failed update actually shows up.** Migrations run at boot, when the on-disk data store
version does not match the booting image, and the design document names the cost of that choice:
"One downside of this approach is that migration failure requires another reboot to flip back to a
matching version." So a migration failure is not caught at prepare time; it costs a boot.

**One documented failure mode worth planning around.** Updating between versions that are "too far
apart" is a known issue that produces a "no space left on device" error *at boot*. The documented
example is 1.7.2 to 1.11.0, and the documented workaround is to move a couple of releases at a time
using version locking. Two properties make this operationally awkward and both are documented:
the failure surfaces after the reboot rather than during prepare, and the threshold is expressed as
"too many intermediate releases" rather than as a number.

**Two movements that are not updates at all.** Major-version changes are breaking changes and
require node replacement. Variant changes, including every Kubernetes minor-version change and every
flavour change such as adding `nvidia`, are migrations and require node replacement. See dimension 7.

### Comparison to the other upgrade architectures in this study

Bottlerocket is A/B, not A/B/recovery: there are two sets and no third, no dedicated recovery slot,
and no rescue image. It is not OSTree-style, because there is no shared filesystem tree with
hardlinked commits and no per-file deduplication; each set is a complete independent image, which is
why the two-partition-set disk is large but has no state that can become inconsistent. It is not a
transactional package layer, because there are no packages at run time at all. The trade this makes
against an OSTree-style system is symmetrical and worth stating without a verdict: Bottlerocket
gives up cheap storage and cheap incremental deltas and gets, in exchange, a disk on which no
partial state exists to reconcile.

**Evidence**

- DOCUMENTED: image-based update model, A/B partition-table flip, tracking of successful boots, automatic revert. Source: [Bottlerocket README, Updates](https://github.com/bottlerocket-os/bottlerocket/blob/develop/README.md)
- DOCUMENTED: `updog` guard rails, wave computation from the seed, TUF roles, the `apiclient` walkthrough and the `/updates/status` payload. Source: [updater README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/README.md)
- DOCUMENTED: the state machine's existence, the status file at `/run/update-status`, the lockfile, and the refusal of commands not allowed by the state. Source: [thar-be-updates README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/api/thar-be-updates/README.md)
- DOCUMENTED (source): the four states `Idle`, `Available`, `Staged`, `Ready` and every transition. Source: [thar-be-updates status.rs](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/api/thar-be-updates/src/status.rs) and [main.rs](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/api/thar-be-updates/src/main.rs)
- DOCUMENTED: the GPT attribute bit layout and the three-step upgrade procedure. Source: [signpost README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/signpost/README.md)
- DOCUMENTED (source): priority 2/1 assignment, tries-left set to exactly 1, the validity preconditions on `upgrade-to-inactive`. Source: [signpost state.rs](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/signpost/src/state.rs)
- DOCUMENTED (source): boot success is marked by `mark-successful-boot.service`, which is `RequiredBy=preconfigured.target`, "Bottlerocket initial configuration complete". Sources: [mark-successful-boot.service](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/packages/os/mark-successful-boot.service), [preconfigured.target](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/packages/release/preconfigured.target)
- DOCUMENTED: in-place versus node-replacement classification of every update method, and the `apiclient` / ECS updater / brupop / SSM options. Sources: [Updates overview](https://bottlerocket.dev/en/os/1.64.x/concepts/updating-bottlerocket/), [In-place updates](https://bottlerocket.dev/en/os/1.64.x/update/methods/in-place/), [Node replacement](https://bottlerocket.dev/en/os/1.64.x/update/methods/node-replacement/)
- DOCUMENTED: version skipping with sequenced migrations, the "no space left on device" caveat and its workaround, no in-place major-version change, no in-place variant change. Source: [Guidelines for updating in-place](https://bottlerocket.dev/en/os/1.64.x/update/guidelines/)
- DOCUMENTED: migrations run at boot, are downloaded during prepare, and an update refuses to start without them; migration failure costs another reboot. Source: [migration README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/api/migration/README.md)
- DOCUMENTED: default wave policy percentages, accelerated and emergency policies, publisher-side wave files. Sources: [PUBLISHING.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/PUBLISHING.md), [waves README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/waves/README.md)
- DOCUMENTED: `updates.ignore-waves`, `updates.version-lock`, `updates.seed` semantics and defaults. Sources: [settings.updates reference](https://bottlerocket.dev/en/os/1.64.x/api/settings/updates/), [Locking to a specific release](https://bottlerocket.dev/en/os/1.64.x/update/locking-to-a-specific-release/)
- INFERRED: a power cut during `prepare` leaves an unbootable inactive set and an unchanged active set, because `clear-inactive` zeroes the inactive priority and tries before any bytes are written. Not stated by the project.
- NOT TESTED / OUT OF TIER SCOPE: every behavioural claim above. Nothing was booted, no update was applied, no rollback was triggered, no power was cut.
- UNKNOWN: what an OS update does to the shim and GRUB binaries on the EFI system partition, which lies outside both partition sets. No document read here describes it.
- UNKNOWN: the numeric threshold at which "too many intermediate releases" triggers the no-space failure. The guidance is qualitative.

---

## 5. Rollback and recovery

The framework insists these are different concepts, and Bottlerocket is a good illustration of why:
its rollback story is strong and its recovery story is deliberately thin, because the project's
answer to recovery is to replace the host.

**Rollback to the previous OS is a local, network-free operation.** The documented procedure is two
commands:

```
signpost rollback-to-inactive
reboot
```

and the README's justification is the operationally important part: "This doesn't require any
external communication, so it's quicker than `apiclient`, and it's made to be as reliable as
possible." The source shows a safety check behind it: `rollback_to_inactive` refuses if the inactive
set "doesn't have a prior successful boot and doesn't have the priority/tries_left that would make
it safe to try," returning an error that names the priority, tries-left and successful values it
saw. Otherwise it raises the inactive set to priority 2 and drops the active set to 1, without
touching whether the active set was successful. That asymmetry is deliberate: a manual rollback
because a workload broke does not have to lie about whether the OS booted.

**Rollback to an arbitrary earlier version is a network operation, and it is a first-class one.**
`apiclient update check` reports `available_updates` including older versions, and the README
explains why: "including older versions, because Bottlerocket supports safely rolling back."
`updog`'s `--image` option forces a specific version. This is a different capability from the
partition flip and has a different dependency profile: it needs the repository.

**Retained prior versions: one** (two partition sets total). Exactly one previous OS is reachable
without the network. Reaching two versions back in place is not possible; that is INFERRED from the
two-set design rather than stated as a limit.

**Rollback of complete machine state: no, and the boundary is drawn precisely.** The settings data
store does roll back, because the update system requires migrations that "safely transition to the
new version and back" before it will start. The data device at `/local` does not roll back: it is
outside both sets and the OS "does not typically make changes to this volume during regular
updates." So an operator who rolls back gets the old OS and the old settings, with the container
image cache, orchestrator state and any application data on `/local` exactly as the new version left
them. Whether that combination is always safe is not addressed in the documentation and is not
inferred here.

**Recovery environment: none is documented.** There is no recovery partition, no rescue shell, no
netboot rescue image and no factory reset. That is not an oversight; the project's security guidance
has a section titled "Design for host replacement," and the whole variant model assumes
interchangeable nodes. For a fleet of EC2 instances behind an autoscaling group, that is a coherent
and arguably correct answer. For a single machine that must be recovered in place, it is a real gap,
and this profile records it as one without treating it as a defect.

**Recovery when Kubernetes is unavailable.** The update and settings APIs are local, so anything
reachable from a shell on the box works: the admin container, the control container, or a serial
console on a development variant. None of those require a control plane.

**Recovery when both host containers are disabled.** There is a published runbook, and it goes
*through* the orchestrator. The documented solution is to create a pod that mounts `/usr/bin/apiclient`
and `/run/api.sock` from the host, with `seLinuxOptions` type `control_t` and level `s0` so that it
can reach the socket's `api_socket_t` label, exec into it, and run
`apiclient set host-containers.admin.enabled=true`. The page's own warning is that this "involves
mounting critical resources into containers with elevated privileges. Use carefully, only run as long
as necessary, and clean up afterwards." The path works, and it is an honest piece of documentation,
but it means the published answer to "I locked myself out of the host" is "use Kubernetes."

**Recovery with no host containers, no orchestrator and no network, on a production variant.**
UNKNOWN. Development variants (`aws-dev`, `vmware-dev`, `metal-dev`) provide a serial console login,
and the local-VM quickstart says any username will do at the prompt. Production variants do not ship
that, by design, and no offline path is documented for one. This is the same gap the Pulse baseline
recorded, re-checked and unchanged.

**Persistent-data corruption.** No recovery mechanism is documented for a corrupted `/local`. Where
encrypted storage is enabled, the project's own documentation is blunt about the consequence of a
TPM PCR change: no built-in recovery mechanism, and the outcome is restore from backup or data loss.
Carried from the Pulse baseline and re-cited rather than re-derived.

**What the project treats as a "known-good state."** Operationally, the definition is written into
the GPT bits: a partition set whose successful-boot flag is set, plus a private-partition flag
recording that boot has ever succeeded at all. That is a boot-level definition, not a workload-level
one, and it follows directly from the boot-success criterion in dimension 4. INFERRED from the
documented bit semantics and the `mark_successful_boot` implementation; the project does not use the
phrase.

**Evidence**

- DOCUMENTED: `signpost rollback-to-inactive` plus reboot, and its independence from external communication. Source: [Bottlerocket README, Update rollback](https://github.com/bottlerocket-os/bottlerocket/blob/develop/README.md)
- DOCUMENTED (source): the `will_boot` precondition on rollback and the priority changes it makes. Source: [signpost state.rs](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/signpost/src/state.rs)
- DOCUMENTED: older versions appear in `available_updates` because rolling back is supported; `--image` forces a version; migrations must exist in both directions. Sources: [Bottlerocket README](https://github.com/bottlerocket-os/bottlerocket/blob/develop/README.md), [updater README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/README.md)
- DOCUMENTED: the privileged-pod procedure for regaining access, including the SELinux options. Source: [Regaining access to a Bottlerocket node](https://bottlerocket.dev/en/os/1.64.x/login/regaining-access/)
- DOCUMENTED: "Design for host replacement" as the stated operational model. Source: [SECURITY_GUIDANCE.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/SECURITY_GUIDANCE.md)
- DOCUMENTED: serial console access on development variants. Source: [QUICKSTART-LOCAL.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/QUICKSTART-LOCAL.md)
- DOCUMENTED: no built-in recovery if TPM PCR values change unexpectedly, where encrypted storage is enabled. Source: [core kit ENCRYPTED_STORAGE.md](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/docs/ENCRYPTED_STORAGE.md). Carried from the Pulse baseline.
- INFERRED: exactly one previous version is reachable without the network; the project's "known-good state" is a boot-level rather than workload-level definition.
- UNKNOWN: any offline recovery path for a production variant with both host containers disabled, no orchestrator and no network.
- UNKNOWN: whether rolling back the OS while leaving `/local` at the newer version is considered safe, and under what conditions. Not addressed in the documentation read.
- NOT TESTED / OUT OF TIER SCOPE: whether the automatic rollback fires as described, how long it takes, and what the machine looks like afterwards.

---

## 7. Kubernetes coupling

**Bottlerocket can run without Kubernetes, and the evidence is stronger than "an ECS variant
exists."** Four families in the current tree run no Kubernetes at all. The `aws-ecs-2`, `aws-ecs-3`
and `aws-ecs-4` variants run the Amazon ECS agent. The `aws-mantle-1` family runs *no orchestrator
agent whatsoever*: "Unlike other AWS variants, it does not run a container orchestrator agent." The
three development variants, `aws-dev`, `vmware-dev` and `metal-dev`, also run no orchestrator and
include Docker plus troubleshooting tools for OS development. And the local-VM quickstart states the
plainest version of it: "The VM will not join an ECS or Kubernetes cluster."

Two qualifications belong with that, and both are the project's own words. The `aws-mantle-1`
variants are labelled "limited support", are "intended for use by AWS Bedrock's Mantle API and may
make breaking changes without warning," and the documentation redirects anyone wanting a supported
variant to the Kubernetes or ECS families. And they are not in the published variant list for
`1.64.x`, which covers `aws-dev`, the ECS families, the `aws-k8s-1.31` through `aws-k8s-1.36`
families, `metal-dev`, `vmware-dev` and the `vmware-k8s-*` families, but not `aws-mantle-1`. So an
orchestrator-free Bottlerocket exists in the tree today, and is not a supported product today.
OBSERVED for the published-list omission, via the variants-and-kernels page on 2026-09-16;
DOCUMENTED for the support status.

**Is Kubernetes built into the architecture? Partly, and in a specific place: the artifact's
identity.** The orchestrator and its minor version are two of the components encoded in the variant
name, so `aws-k8s-1.33` and `aws-k8s-1.34` are different artifacts in the same sense that two
different operating systems are. The kubelet is not a workload scheduled onto a generic host; it is
a package chosen at build time and baked into the image.

**Can Kubernetes be removed? Not from a running node, and that is the same answer as for any other
component.** There is no package manager, so nothing is removed from a running Bottlerocket. It is
removed by running a different image. Out of tree, Twoliter exists to let a maintainer define their
own variant without forking the repository, with stated requirements that include replacing core
packages, mixing core and own packages, and opting out of subsystems entirely. So "Bottlerocket
without Kubernetes" is a build-time question with a documented answer, not a runtime one.

**Which Kubernetes distributions.** The `aws-k8s-*` variants "support self-hosted clusters and
clusters managed by EKS." The `vmware-k8s-*` variants "support self-hosted clusters." AWS documents
Bottlerocket as an EKS-optimised AMI family, with managed node groups and Karpenter as the AWS-side
consumption paths. EKS Anywhere is not mentioned anywhere in Bottlerocket's own sources; that
absence was recorded in the Pulse baseline and is unchanged here, and per the framework it is not
read as unsupported.

**Can the OS and Kubernetes be upgraded independently? Half of it, and the split is exact.** The
Bottlerocket version moves freely within a variant: "The version of Bottlerocket is independent of
the variant: a variant will be available across many different Bottlerocket versions." The
Kubernetes minor version does not move at all in place: "you cannot update to a different variant:
that is a migration (which involves replacing a node in the orchestrated cluster)." The update
guidelines put the same rule in operator language: "In order to move between Kubernetes versions (or
any variant), you must replace the nodes in your cluster with new nodes running the desired
variant."

What softens this in practice is the documented compatibility window. Each Kubernetes variant states
the cluster versions it works with, and the window is four minors wide: `aws-k8s-1.31` is
"compatible with Kubernetes 1.31, 1.32, 1.33, and 1.34 clusters", `aws-k8s-1.33` with 1.33 through
1.36, `aws-k8s-1.34` with 1.34 through 1.37. So a control plane can move forward several minors
before the node image has to be replaced; the node just cannot follow it in place, ever.

**Does the OS manage Kubernetes? No.** Bottlerocket starts the orchestrator agent its variant
contains and exposes `settings.kubernetes.*` to configure it. It does not install, bootstrap or
upgrade a control plane, and it is not a Kubernetes distribution in the sense that word carries
elsewhere in this comparison set.

**Does Kubernetes manage the OS? Only if the operator installs brupop, and it is genuinely
optional.** The Bottlerocket update operator is a separate repository with its own release cadence.
It installs a controller deployment, an agent daemonset on every Bottlerocket node, and its own API
server; the agent queries for updates, drains the node and performs the update when the controller
tells it to, and all cluster mutations go through the operator's API server, which re-authorises
them with the Kubernetes TokenReview API so that a request attributed to a node really came from
that node's agent. `cert-manager` is a hard prerequisite. Participation is opt-in per node through
the label `bottlerocket.aws/updater-interface-version=2.0.0`: "Only bottlerocket nodes with this
label will be updated." Its support policy is narrower than the OS's: security patches for the
latest minor version only.

Two details are worth carrying into the epic's comparison. First, brupop's node draining is the
*only* place in the documented stack where workload health enters the update decision, and it is an
optional add-on rather than part of the OS. Second, brupop rolls updates out in waves of its own,
pointing at the wave definitions embedded in Twoliter, so a cluster running brupop has two staggering
mechanisms in play.

**Which system owns machine lifecycle?** In the base case, the operating system owns the mechanism
and the operator owns the trigger, through a local API that works identically with no cluster
present. With brupop installed, Kubernetes owns the *scheduling* of updates and the draining around
them, but the OS still owns the mechanism: brupop's agent ultimately makes the same API calls an
operator would. With EKS managed node groups or Karpenter, neither owns the update, because that
path is node replacement and the machine lifecycle belongs to the AWS control plane.

**Placement on the framework's spectrum.** Kubernetes-oriented container host, between the
Kubernetes-appliance pole and the general immutable substrate pole, with the evidence for each side
recorded rather than scored. Toward the appliance pole: every fully supported variant runs an
orchestrator agent, the Kubernetes minor is part of the artifact identity, and the documented
recovery runbook for a locked-out node assumes a cluster. Toward the substrate pole: the update,
rollback and settings APIs are entirely orchestrator-independent, an orchestrator-free variant
family exists in tree, development variants run standalone on bare metal and under QEMU, and
Twoliter exists to let someone build a variant with a different package set. The project's own
charter states a position on this: "It is not a Kubernetes distro, nor an Amazon distro." That is a
values statement, recorded as such, and it sits alongside, not instead of, the fact that every
currently supported variant runs an orchestrator agent.

**Non-Kubernetes workloads other than ECS.** Not documented. There is no published guidance for
running Bottlerocket as a database host, a storage node, a hypervisor, an edge gateway or an ordinary
Linux service host, and the hardware document rules out the extensions that several of those would
need: "There is no plan to add out-of-tree drivers to Bottlerocket images. There is no plan to add
additional CPU architectures." Per the framework, that absence is recorded as absence of
documentation, not as proof that it cannot be done, especially given that Twoliter's whole purpose is
to support builds the core project does not ship.

**Evidence**

- DOCUMENTED: variants encode platform, orchestrator, orchestrator version, flavour and architecture; variant change is a migration requiring node replacement; Bottlerocket version is independent of variant. Source: [Variants concept page](https://bottlerocket.dev/en/os/1.64.x/concepts/variants/)
- DOCUMENTED: per-variant Kubernetes compatibility windows, EKS and self-hosted support, the `aws-mantle-1` family's orchestrator-free and limited-support status, development variants. Source: [variants/README.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/variants/README.md)
- DOCUMENTED: "In order to move between Kubernetes versions (or any variant), you must replace the nodes in your cluster." Source: [Guidelines for updating in-place](https://bottlerocket.dev/en/os/1.64.x/update/guidelines/)
- DOCUMENTED: brupop's architecture, cert-manager prerequisite, per-node opt-in label, draining, and latest-minor-only support policy. Source: [bottlerocket-update-operator README](https://github.com/bottlerocket-os/bottlerocket-update-operator)
- DOCUMENTED: the local VM "will not join an ECS or Kubernetes cluster". Source: [QUICKSTART-LOCAL.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/QUICKSTART-LOCAL.md)
- DOCUMENTED: "It is not a Kubernetes distro, nor an Amazon distro." Source: [CHARTER.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/CHARTER.md)
- DOCUMENTED: Twoliter's requirements to replace core packages, mix sources and opt out of subsystems. Source: [Twoliter design document](https://github.com/bottlerocket-os/twoliter/blob/develop/docs/design/README.md)
- DOCUMENTED: no out-of-tree drivers and no additional architectures planned. Source: [SUPPORTED-HARDWARE.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/SUPPORTED-HARDWARE.md)
- DOCUMENTED: Bottlerocket as an EKS-optimised AMI family. Source: [Bottlerocket AMIs for EKS](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami-bottlerocket.html)
- OBSERVED: the published variant list for `1.64.x` contains `aws-dev`, `aws-ecs-2/3/4`, `aws-k8s-1.31` through `aws-k8s-1.36`, `metal-dev`, `vmware-dev` and `vmware-k8s-1.31` through `1.36`, with their FIPS and NVIDIA flavours, and does not contain `aws-mantle-1`. Source: [Variants & kernels](https://bottlerocket.dev/en/os/1.64.x/version-information/variants/), retrieved 2026-09-16.
- OBSERVED: the top-level README's variant list is narrower than both the tree and the published list. It omits `aws-ecs-4`, the FIPS Kubernetes variants and the NVIDIA-FIPS flavours. Retrieved from `develop` on 2026-09-16; consistent with the staleness the Pulse baseline recorded.
- UNKNOWN: whether EKS Anywhere is a supported target. Never mentioned in Bottlerocket's own sources.
- UNKNOWN: whether `aws-mantle-1` is intended to become a generally supported orchestrator-free variant.
- NOT TESTED / OUT OF TIER SCOPE: whether a node actually functions across the full four-minor compatibility window, and whether brupop's drain-and-update cycle behaves as documented.

---

## 15 and 22. Supply-chain ownership and operational independence

The framework's question is "could an organization independently recreate and operate what it is
running," and its §22 protocol is to attempt every stage of the lifecycle on operator-controlled
infrastructure and record where the primary commercial sponsor's infrastructure is required.
Bottlerocket is the interesting case in the hyperscaler tier because it is an open-source project
rather than a component of a single cloud service, so the answer is a genuinely mixed map instead of
a short one.

**The experiment was not performed.** What follows is what the project's own documentation says
about each stage, with a label. Nothing here is REPRODUCED.

| Stage | Finding | Label |
|---|---|---|
| BUILD | Public source, Apache-2.0 or MIT, built locally with `cargo make` inside the Bottlerocket SDK container. Documented cost: over 80GB and 12 minutes to 4 hours for a first build. Twoliter supports defining a variant entirely out of tree, without forking, with stated requirements covering replacing core packages, mixing sources, opting out of subsystems including the update system, and defining your own partition layouts. The SDK, core kit and kernel kit are container images published to ECR Public; Twoliter states that maintainers must be able to host their own copies of required images, which is a requirement rather than a runbook. | DOCUMENTED (buildable, customisable), UNKNOWN (bit-for-bit reproducible; mirrored-input build verified end to end) |
| SIGN | Two independent signing surfaces, and they differ. **Update repository:** fully operator-controlled. `cargo make repo` generates a root role and key, or an operator supplies their own via `Infra.toml` with keys in a local file, an SSM SecureString, or KMS, with multi-key roots, thresholds and a separate publication key. **Secure Boot:** two profile types exist. The local profile is generated automatically but is "**strongly discouraged** for any kind of production use" because it exposes private key material directly. The AWS profile uses four AWS Private CAs and three KMS asymmetric keys, with a documented warning that the cost, "**especially the private CAs**", is nontrivial. No third profile type is documented, and the README invites one as a contribution. | DOCUMENTED (TUF signing fully independent; both Secure Boot profiles and the discouragement), UNKNOWN (a production-grade Secure Boot signing profile outside AWS) |
| HOST | The TUF repository is hosted wherever the operator wants: S3, "any HTTP server", or a `file://` URL. Metadata expiry becomes the operator's operational responsibility, and a repository left unre-signed stops serving its hosts. The project's own endpoints, `updates.bottlerocket.aws` and `cache.bottlerocket.aws` for `root.json`, are AWS-hosted and are the default, not a requirement. | DOCUMENTED |
| INSTALL | Four documented paths. AMI registration on EC2 via `cargo make ami`; VMware via the VMware publishing and quickstart guides; direct disk write on bare metal, where the image is written and configuration is placed into the private partition afterwards because the boot and root partitions are verity-checked; and a local QEMU/KVM path via `tools/start-local-vm`. Three of the four need no AWS service. No PXE, netboot or ISO installer is documented. | DOCUMENTED (four paths), UNKNOWN (PXE/netboot/ISO) |
| BOOT | Entirely local, with no AWS service in the path. The chain is firmware → shim → GRUB → `grub.cfg` (carrying the dm-verity root hash) → kernel → verity-checked root, and "any verification failure will immediately prevent any further progress." Bottlerocket deliberately does not use the Microsoft 3rd Party UEFI CA; it uses a self-signed certificate "intended to allow you to focus your machine's trust only to your specified OS." On metal, the machine's NVRAM must contain Bottlerocket's `db` certificate, which ships in the EFI partition in PEM and DER. An operator who built with their own sbkeys profile boots their own chain. | DOCUMENTED |
| CONFIGURE | The settings API is an HTTP server on a local Unix socket, fed at boot by `early-boot-config`. Every variant reads `/var/lib/bottlerocket/user-data.toml` first; AWS variants then read IMDS, VMware variants read a CD-ROM then guestinfo, with later sources overriding earlier ones. So a file-based configuration path with no metadata service exists and is the documented one for metal and local VMs. Remote configuration of a running node needs an authenticated transport, and the one that ships enabled by default on AWS variants is the control container, which depends on AWS Systems Manager. | DOCUMENTED (local and file-based configuration are independent; the shipped remote transport is AWS SSM) |
| UPGRADE | Fully replaceable, and this is the sharpest contrast with the other hyperscaler profile in this epic. The client is local, the repository URL is a setting changeable at build time or run time, the wave schedule is a file the publishing operator writes, and the manifest is something the operator generates. Nothing in the update path requires the project's servers once the URLs are changed. | DOCUMENTED |
| ROLLBACK | Fully local and explicitly network-free: `signpost rollback-to-inactive` and a reboot, which "doesn't require any external communication". | DOCUMENTED |
| RECOVER | Mixed and the weakest stage. No recovery environment, no rescue shell, no factory reset. The published runbook for a locked-out production node goes through Kubernetes, by mounting the API socket into a privileged pod. Development variants offer a serial console. The stated model is host replacement. | DOCUMENTED (the available paths and the stated model), UNKNOWN (offline recovery on a production variant) |

**Reading the map.** Seven of the nine stages can be run on operator-controlled infrastructure with
documented procedures: BUILD, SIGN (for updates), HOST, INSTALL, BOOT, CONFIGURE (locally) and
UPGRADE and ROLLBACK. Two have a genuine AWS dependency in the documented production path: Secure
Boot key management, where the only profile not strongly discouraged for production is built on AWS
Private CA and KMS, and remote day-2 access, where the shipped transport is SSM. RECOVER has no
independent answer at all for a production variant without an orchestrator.

**If AWS and all of its hosted services were unavailable, what would remain?** This is a dependency
map read from documentation on 2026-09-16. It is not a prediction about AWS, and the framework's bias
controls forbid making one.

What would remain: the source and the build system, both permissively licensed; the ability to build
an image locally, provided the SDK, core kit and kernel kit images had been mirrored beforehand; the
whole TUF publishing toolchain including `tuftool` and the `cargo make repo` flow; the entire local
update state machine, `signpost`, the partition flip, the automatic and manual rollback paths, the
settings API and migrations; the VMware, bare-metal and QEMU install paths; and file-based
configuration. In other words, the machine-state machinery itself is intact, which is a materially
different answer from a system whose update service is a black box.

What would have to be replaced: the default TUF repository at `updates.bottlerocket.aws` and the
`root.json` distribution point at `cache.bottlerocket.aws`; the ECR Public images for the SDK, the
kits, and the admin, control and bootstrap containers; AMI distribution and the SSM public
parameters used to look AMIs up; SSM as the remote transport for the control container and for the
SSM Command Document update path; EKS and ECS as orchestrators for every fully supported variant; the
AWS Private CA and KMS-based Secure Boot signing profile; Amazon Inspector as the SBOM consumer; and
the security advisory feed at `advisories.bottlerocket.aws`.

**Supply-chain artefacts specifically (§15).** Source availability, build tooling and public CI are
all present, and contributions are accepted and merged in public: `CONTRIBUTING.md` documents the
fork-and-pull-request flow and asks contributors to open an issue first, `COPYRIGHT` states that
"Copyrights in Bottlerocket are retained by their contributors. No copyright assignment is required
to contribute to Bottlerocket", and the v1.65.0 release notes credit an outside contributor by handle
("Thanks @anirbag"). That last point answers the check this ticket asked for: Bottlerocket is open
source *and* takes public contributions, verified against current reality rather than assumed.
Dependency pinning and signing are strong through TUF. Where it thins out is attestation: SBOM
tooling exists in the SDK and the control container uploads a CycloneDX SBOM to Amazon Inspector by
default, and each host carries a build-time package inventory at
`/var/lib/bottlerocket/inventory/applications.json`, but no per-release SBOM artifact and no build
provenance attestation were found, and GitHub releases carry no assets at all. Security advisories
are published on the repository's GitHub Security tab and as a gzipped `updateinfo.xml` at
`advisories.bottlerocket.aws`, and they key to the same package inventory.

**A fairness note the framework requires.** This same chain must be applied to every project in the
study, Kairos included. Having vendor dependencies is not unusual and is not, by itself, a finding.
What is worth recording about Bottlerocket is the shape: the dependencies cluster at the *edges* of
the lifecycle, in distribution, remote access, key custody and orchestration, and they are absent
from the *middle*, in the update and rollback mechanics that this epic is actually about. A study
that scored "number of AWS dependencies" would miss that, which is why this profile maps them by
stage instead.

**Evidence**

- DOCUMENTED: build requirements, cost and flow; `cargo make ami`; the kmod kit fetched from the TUF repository with `tuftool` and a pinned `root.json` SHA-512. Source: [BUILDING.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/BUILDING.md)
- DOCUMENTED: TUF key generation and custody options, repository hosting anywhere, wave policy selection, expiration policy, build-time and run-time repository URL changes. Source: [PUBLISHING.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/PUBLISHING.md)
- DOCUMENTED: local and AWS Secure Boot key profiles, the discouragement of the local profile for production, the four Private CAs and three KMS keys, the nontrivial cost warning, and the invitation to contribute another profile type. Source: [sbkeys README](https://github.com/bottlerocket-os/bottlerocket/blob/develop/sbkeys/README.md)
- DOCUMENTED: the boot chain, the deliberate non-use of the Microsoft 3rd Party UEFI CA, the NVRAM `db` certificate requirement on metal, and the legacy-BIOS exclusion. Source: [Chain of trust](https://bottlerocket.dev/en/os/1.64.x/concepts/chain-of-trust/)
- DOCUMENTED: user-data source order per variant, including the file-first path on every variant. Source: [variants/README.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/variants/README.md)
- DOCUMENTED: bare-metal provisioning writes configuration into the private partition because boot and root are verity-checked. Source: [PROVISIONING-METAL.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/PROVISIONING-METAL.md)
- DOCUMENTED: the local QEMU/KVM path, `tools/start-local-vm`, `--inject-file`, and serial console access. Source: [QUICKSTART-LOCAL.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/QUICKSTART-LOCAL.md)
- DOCUMENTED: contribution process, no copyright assignment, dual licence. Sources: [CONTRIBUTING.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/CONTRIBUTING.md), [COPYRIGHT](https://github.com/bottlerocket-os/bottlerocket/blob/develop/COPYRIGHT)
- DOCUMENTED: an outside contributor credited in the current release notes. Source: [v1.65.0 release notes](https://github.com/bottlerocket-os/bottlerocket/releases/tag/v1.65.0)
- DOCUMENTED: the on-host software inventory and the advisory feed at `advisories.bottlerocket.aws`. Source: [Variants concept page](https://bottlerocket.dev/en/os/1.64.x/concepts/variants/)
- DOCUMENTED: AMI IDs are retrieved through AWS SSM public parameters. Source: [Retrieve recommended Bottlerocket AMI IDs](https://docs.aws.amazon.com/eks/latest/userguide/retrieve-ami-id-bottlerocket.html)
- DOCUMENTED, carried from the Pulse baseline without independent re-derivation: SBOM tooling in the SDK (SPDX 2.3 and CycloneDX 1.6), and the control container's opt-out upload of a CycloneDX SBOM to Amazon Inspector. Re-checking that claim at source was out of scope for this pass, which focused on the four named dimensions.
- OBSERVED: 38 pull requests merged into `bottlerocket-os/bottlerocket` between 2026-06-16 and 2026-09-16, from 12 distinct authors; repository last pushed 2026-09-15. Queried via `gh api repos/bottlerocket-os/bottlerocket/pulls` on 2026-09-16. This measures activity and author spread; it does not establish employer affiliation, which the project does not publish.
- INFERRED: that a fully mirrored build is possible, from Twoliter's stated requirement that maintainers must be able to host their own copies of required container images and source archives. Stated as a requirement, not as a verified capability.
- UNKNOWN: bit-for-bit reproducibility; per-release SBOM artifacts; SLSA or equivalent build provenance; a production Secure Boot signing profile that does not use AWS Private CA and KMS; an end-to-end air-gapped runbook.
- NOT TESTED / OUT OF TIER SCOPE: the §22 experiment itself. No build was run, no repository was published, no key was generated, no image was installed.

---

## What a lifecycle experiment pass needs

This section exists because the ticket's tier calls for "representative lifecycle experiments" and
this pass deliberately did not run them. Its purpose is to make the missing half a costed decision.
The framework's §21 field list (INITIAL STATE, FAILURE INJECTED, EXPECTED BEHAVIOR, OBSERVED
BEHAVIOR, FINAL MACHINE STATE, MANUAL INTERVENTION REQUIRED, DATA LOST, RECOVERY PROCEDURE, TIME TO
RECOVERY) is the right report shape; nothing has ratified it as the template for this tier yet.

### Experiments, in rough order of value per unit of effort

1. **Happy-path in-place upgrade.** Boot a known version, `apiclient update check`, `prepare`,
   `activate`, `reboot`. Capture `/run/update-status` at each step to confirm the
   `Idle → Available → Staged → Ready` transitions empirically, and `signpost status` before and
   after to confirm the priority, tries-left and successful bits move as the source says. Confirm
   `mark-successful-boot` fires and sets bit 56. This one experiment converts most of dimension 4
   from DOCUMENTED to REPRODUCED.
2. **Forced manual rollback.** `signpost rollback-to-inactive` and reboot. Measure wall-clock time,
   confirm no network traffic is required, and confirm settings migrate backward correctly. Checks
   the strongest claim in dimension 5.
3. **Failed-boot automatic rollback.** Break the staged set after `activate` so that it cannot
   complete boot, and confirm the single boot attempt is consumed and the machine returns to the old
   set unattended. Needs a chosen breakage that fails at the intended stage; a corrupted root hash
   and a deliberately broken systemd dependency that prevents `preconfigured.target` are two
   different tests, and the second one directly probes the boot-success criterion found in
   dimension 4.
4. **Power cut during `prepare`.** Kill the VM mid-write and confirm the inactive set is unbootable
   and the active set unchanged. This is the one place in dimension 4 where this profile had to
   label a claim INFERRED; the experiment closes it.
5. **Version-skip and disk-full.** Reproduce the documented "no space left on device" failure by
   updating across many intermediate releases, and separately fill `/local` and attempt an update.
   Worth doing because the documented failure appears at boot rather than at prepare time and the
   threshold is qualitative.
6. **Repository failure modes.** Point a node at a self-hosted TUF repository, then take it offline
   mid-`prepare`; separately, let the metadata expire and observe what the client does. The
   publishing guide warns about expiry, and the client-side behaviour is not described.
7. **The §22 independence run, end to end.** Build a variant from source, sign a repository with
   keys the operator generated, host it locally, install, configure from a file, upgrade to a second
   locally built version, roll back, and recover. This is the experiment that would let the epic
   state, with evidence, what survives without the sponsor's infrastructure.
8. **Air-gap.** Mirror the TUF repository and the kit and host-container images, then run the whole
   cycle on a host with no route to `public.ecr.aws` or `*.bottlerocket.aws`. Closes the largest
   UNKNOWN in dimension 2.

Experiments 1 through 8 are all OS-level. Two further ones are orchestrator-level and need a cluster:
brupop's drain-update-uncordon cycle, and the behaviour of a node that boots cleanly but never
becomes `Ready` in Kubernetes, which is the scenario the boot-success criterion explicitly does not
cover.

### Infrastructure, and the honest cost of each option

**Option A: local QEMU/KVM, no AWS account.** This is viable and documented, which is not true of
every system in this study. Build the `metal-dev` variant with
`cargo make -e BUILDSYS_VARIANT=metal-dev`, then run
`./tools/start-local-vm --variant metal-dev --arch $(uname -m) --inject-file net.toml --inject-file user-data.toml`.
The wrapper injects configuration into the image's private partition, attaches a virtual NIC that
QEMU serves DHCP for, and connects the terminal to the serial console, where a development variant
gives an interactive login. The documented prerequisites are a Fedora host, `qemu`, hardware
virtualisation, plus the build host requirements: Docker with BuildKit, Rust, `cargo-make`, and over
80GB free. The first build is 12 minutes to 3-4 hours depending on cores. An AWS account is needed
only for the optional control container's SSM activation, which the serial console makes unnecessary.

Two caveats that would need checking before committing to this route, both currently UNKNOWN. First,
`metal-dev` is a development variant, so results from it are not automatically results about
`aws-k8s-*`; the epic would have to decide whether a `metal-dev` observation counts as REPRODUCED for
a platform whose supported target is EC2, or only as evidence about the shared mechanism. Second, the
admin and control containers pull from ECR Public even locally, so a genuinely offline run needs them
mirrored first.

**Option B: an AWS account with EC2, plus EKS or ECS.** Required for anything about the supported
variants, IMDS-delivered user data, AMI-based install, the official TUF repository and its real wave
schedules, brupop, the ECS updater, SSM Command Documents, and node replacement. Costs real money;
NVIDIA and FIPS variants cost more. Needed for experiments 9 and 10 and for any claim about the
configuration Bottlerocket is actually deployed in.

**Option C: VMware.** Documented and supported, and would give a supported (non-dev) variant on
operator-controlled hardware. Only worth it if VMware is already available on the test host or nearby;
otherwise Option A covers the same ground more cheaply.

### The decisions that block the experiment pass

1. Ratify an experiment-report template for this tier. The framework's §21 field list is the obvious
   basis; nothing has adopted it.
2. Decide whether a `metal-dev` local-QEMU result counts as REPRODUCED, as OBSERVED, or as evidence
   about the mechanism only. This decision affects every system in the study, not just Bottlerocket,
   so it belongs to the epic rather than to this ticket.
3. Decide whether an AWS account is in scope for the epic at all, and if so, with what budget cap.
   Without it, roughly a third of Bottlerocket's documented surface stays untestable and should be
   labelled as such rather than approximated from the local variant.
4. Decide the build-host allocation. An 80GB, multi-hour build is not a thing to run casually in a
   shared worktree, and the Go-cache-style sandbox constraints on the test host apply to `cargo` and
   Docker here too.

### Open questions a maintainer-correction pass should carry

Distinct from the Pulse baseline's list, and specific to this profile's four dimensions:

1. What does an OS update do to the shim and GRUB binaries on the EFI system partition, which sits
   outside both partition sets? Can an update change the Secure Boot chain, and if so, what protects
   that step?
2. Is the boot-success criterion intended to be exactly "reached `preconfigured.target`", and has a
   workload-aware criterion ever been considered for the OS itself rather than for brupop?
3. At roughly how many intermediate releases does the "no space left on device" update failure
   appear, and is there a way to detect the condition before rebooting into it?
4. Is there a supported path to a production-grade Secure Boot signing profile that does not depend
   on AWS Private CA and KMS?
5. Is rolling the OS back while `/local` stays at the newer version considered safe, and are there
   known cases where an upstream component's on-disk data makes it unsafe?
6. What happens to a `prepare` that is interrupted by power loss, and is the `clear-inactive`-first
   ordering intended to guarantee the result this profile inferred?
7. Are per-release SBOMs or build provenance attestations published anywhere, given that GitHub
   releases carry no assets?

---

## Bias and scope note

**Tier and method.** Documentation-based architecture study. No Bottlerocket instance was booted, no
image was built, no update was applied, no rollback was forced, and nothing was broken on purpose.
Claims here are DOCUMENTED, OBSERVED, INFERRED, UNKNOWN or NOT TESTED / OUT OF TIER SCOPE. Nothing is
REPRODUCED. The OBSERVED label is used narrowly and only for measurements against the GitHub API or
the documentation site's HTTP responses on 2026-09-16, with the query named each time.

**Why no experiments.** The scope call was made and posted on the ticket before the research started:
this tier has no experiment protocol, no report template and no infrastructure decision. The
methodology ticket that was to produce them was superseded before it did. Rather than invent a
protocol inside a profile, this pass does the architecture study in full and scopes the experiment
half above, so the gap is an explicit decision with a cost attached. This is the same posture the
sibling COS profile took toward framework dimension 21.

**Reading published source is in scope; guessing at unpublished internals is not.** Bottlerocket's
implementation is public and permissively licensed, so `status.rs`, `state.rs` and the systemd unit
files are primary sources and are cited as such, marked "DOCUMENTED (source)" where the prose
documentation does not cover the same ground. What was *not* done is inferring behaviour from the
Chrome OS lineage that the GPT attribute scheme comes from. Bottlerocket borrows the bit layout and
says so; it does not follow that any other Chrome OS update behaviour applies, and none was assumed.

**Places where UNKNOWN was chosen over inference, deliberately:**

- What an OS update does to the shim and GRUB binaries on the EFI system partition. The partition
  sets are documented; this is outside them and is not described.
- Whether a third-party build reproduces an official image bit for bit. No reproducibility claim was
  found in either direction.
- Whether a production-grade Secure Boot signing profile exists outside AWS Private CA and KMS. The
  sbkeys README documents two profiles and invites a third as a contribution; it does not say one
  cannot be built.
- Whether rolling back the OS while `/local` stays forward is safe.
- The numeric threshold behind the documented "too far apart" update failure.
- Any offline recovery path for a production variant with no host containers, no orchestrator and no
  network.
- Whether `aws-mantle-1` is headed for general support. It is in tree, labelled limited support, and
  absent from the published variant list. Recording all three facts is the honest answer; predicting
  the fourth is not allowed here.

**One claim is INFERRED and is flagged in place rather than buried:** that a power cut during
`prepare` leaves an unbootable inactive set and an unchanged active set. The reasoning is sound and
sits on documented mechanics, but the project does not state it and nobody has tested it. It is
labelled INFERRED in dimension 4 and listed as experiment 4 above.

**Relationship to the Pulse baseline.** Nothing here contradicts a cited fact in
`data/projects/bottlerocket.yaml`. Three extensions were added from new
primary evidence, all named in the provenance block: the exact update states and transitions, the
systemd criterion that marks a boot successful, and the two Secure Boot signing profiles with the
project's own warnings attached. Facts carried from the baseline without independent re-derivation
are the encrypted-storage recovery gap, the EKS Anywhere silence, and the SBOM tooling and Amazon
Inspector upload; the first two are re-cited to their original sources and the third is flagged as
carried in place. The baseline's release-cadence figures were checked against the releases API and
are consistent, so they are not restated here.

**No speculation about corporate behaviour.** Dimension 22 draws a dependency map and says so. It
makes no claim about what AWS will do, no inference from AWS's commercial interests, and no reading
of the charter's "not an Amazon distro" line beyond recording it as a values statement alongside the
ownership facts. The framework forbids all three, and the ticket restated the rule.

**Kairos bias control.** Mauro maintains Kairos. Nothing in this profile compares Bottlerocket to
Kairos, and no Bottlerocket limitation is framed as anyone's advantage. Four places where
Bottlerocket is clearly strong relative to the comparison set are recorded plainly rather than
hedged: the update state machine is explicit, small and published, including the transitions that
are refused; staged rollout with waves lives in the open-source OS rather than in a fleet product;
the manual rollback path is designed to need no network and says so; and the guard rail that an
upgrade will not start unless migrations exist to move *back* is an unusually disciplined piece of
design. Two places where Bottlerocket's constraints buy a real guarantee are recorded as guarantees,
not costs: the absence of a package manager, which removes the class of update failures that come
from divergent local state, and the ephemeral `/etc`, which makes system-configuration drift
structurally unable to survive a reboot. The most significant weaknesses found, the absent recovery
environment and the node-replacement requirement for a Kubernetes minor change, are recorded as
consequences of a coherent fleet-oriented design rather than as defects, because that is what the
documentation shows them to be.
