# bootc and Fedora CoreOS: platform profile

Tracked as ,
the research epic, Reproducible
Machine State.

**bootc** is a mechanism, not an operating system: a Rust command-line tool and library that deploys
and updates a machine from an OCI container image — "transactional, in-place operating system updates
using OCI/Docker container images". It ships no kernel, no userspace, no hardware enablement and no
release of its own beyond the tool. **Fedora CoreOS** is an operating system: a Fedora Edition with
three continuously updating streams, four architectures, Ignition-based first-boot provisioning, and
an update agent that polls a graph server. They are profiled together because they share OSTree as an
on-disk substrate and are routinely discussed as one thing; they are kept distinct because they are
not the same kind of object, and because — as §2 and §4 establish from primary sources — **Fedora
CoreOS does not currently use bootc as its update mechanism.** It fetches an OCI image and applies it
with `rpm-ostree`. Every claim below is attributed: *mechanism* claims travel to any bootc-based image
including RHEL and CentOS Stream ones, *vehicle* claims do not.

**There are three distinct entities here, not two:**

| | What it is | Where it lives |
|---|---|---|
| **bootc** | The update/install mechanism. A tool. CNCF Sandbox. Distribution-independent by stated goal. | [bootc-dev/bootc](https://github.com/bootc-dev/bootc), [bootc.dev](https://bootc.dev/bootc/) |
| **Fedora/CentOS bootc** ("Fedora bootc") | A *base-image project* publishing bootable container base images intended to be **derived from**. Not an OS release in the stream sense. | [docs.fedoraproject.org/en-US/bootc](https://docs.fedoraproject.org/en-US/bootc/), [gitlab.com/fedora/bootc](https://gitlab.com/fedora/bootc) |
| **Fedora CoreOS** | A finished, pre-built OS with streams, disk images and an update agent, intended to be **configured**, not derived from. | [docs.fedoraproject.org/en-US/fedora-coreos](https://docs.fedoraproject.org/en-US/fedora-coreos/), [coreos/*](https://github.com/coreos) |

The dividing line is stated by the projects, not inferred: Fedora/CentOS bootc "emphasizes users
**deriving** from our container base image, making arbitrary, potentially large changes", while
"Fedora CoreOS (much like Fedora Atomic Desktops) generally emphasizes users **configuring** an image
pre-built by Fedora." DOCUMENTED,
[fedora-coreos.adoc](https://gitlab.com/fedora/bootc/docs/-/blob/main/modules/ROOT/pages/fedora-coreos.adoc)
(rendered at [docs.fedoraproject.org/en-US/bootc/fedora-coreos/](https://docs.fedoraproject.org/en-US/bootc/fedora-coreos/)).

**Depth tier: deep experimental core. This pass is the architecture study only.** The epic puts bootc
at "full build / provision / extend / update / break / recover cycle plus both standardized experiment
protocols". None of that was run — a scope decision recorded on
the platform-profile task before the research started: no
experiment-report template is ratified for this tier, and the four infrastructure decisions gating a
real pass are open on the research epic. "What a full
experimental pass needs" scopes and prices the missing half. Same posture as the sibling Bottlerocket
and Flatcar profiles.

**Evidence labels.** Documented behaviour is described and labelled DOCUMENTED with a link. "What does
`bootc rollback` do, per the project and its source" is answered here; "does the machine come back when
we cut power mid-stage" is marked NOT TESTED / OUT OF TIER SCOPE. **Nothing is REPRODUCED.** OBSERVED
means a measurement taken on 2026-09-16 against the GitHub API, the GitLab API, the Quay.io registry
API, the Fedora CoreOS stream and build metadata endpoints, CLOMonitor or the OpenSSF Best Practices
API, with the query named.

**Source depth.** `docs.fedoraproject.org` was behind an Anubis proof-of-work challenge on 2026-09-16
and returned a bot-check page to every automated fetch. Both documentation sets build from public git,
so this profile read the AsciiDoc sources directly —
[coreos/fedora-coreos-docs](https://github.com/coreos/fedora-coreos-docs) and
[gitlab.com/fedora/bootc/docs](https://gitlab.com/fedora/bootc/docs) — citing both source file and
rendered URL. That is reading the primary source, not reverse engineering. The same applies to bootc's
`docs/src/*.md`, which is what `bootc.dev` renders.

**Relationship to the Pulse baseline.** Sibling ticket
the Pulse brief produced 14-dimension Pulse entries
for both on 2026-09-15. This profile treats them as sourced factual baselines, reuses their citations
where they overlap, and contradicts no cited fact. Four extensions are flagged inline and listed in
the bias note.

---

## Version and data provenance

| Field | Value |
|---|---|
| bootc version observed | `v1.16.13`, published 2026-09-15 |
| bootc previous release | `v1.16.12`, 2026-09-10 (the Pulse baseline's figure, superseded by one day) |
| bootc licence | `MIT OR Apache-2.0` |
| bootc foundation status | CNCF **Sandbox**, accepted 2025-01-21 |
| bootc repository | [github.com/bootc-dev/bootc](https://github.com/bootc-dev/bootc) (moved from the `containers` org; old path redirects) |
| Fedora CoreOS stable / testing / next | `44.20260829.3.1` (2026-09-14) / `44.20260913.2.1` / `45.20260913.1.1` |
| Fedora CoreOS architectures | `x86_64`, `aarch64`, `ppc64le`, `s390x` |
| Fedora CoreOS platform artifact sets | 21 on x86_64, 10 on aarch64, 5 on s390x, 4 on ppc64le |
| Fedora CoreOS stable release count | 184, first `31.20200108.3.0` (2020-01-08) |
| Fedora bootc base images | `quay.io/fedora/fedora-bootc` tags 41–46 plus `rawhide`; `latest` resolves to `44` |
| CentOS Stream bootc base images | `quay.io/centos-bootc/centos-bootc:stream9`, `:stream10` |
| Data collected | 2026-09-16 (Pulse baseline collected 2026-09-15) |

All figures were re-verified rather than carried over: the three stream JSON documents at
`builds.coreos.fedoraproject.org/streams/{stable,testing,next}.json` returned the same versions as the
baseline a day earlier; `gh api repos/bootc-dev/bootc/releases` returned `v1.16.13` published
2026-09-15T21:04:07Z, one release newer; `.../prod/streams/stable/releases.json` lists 184 stable
releases. OBSERVED.

**Base image sizes, measured.** `quay.io/fedora/fedora-bootc:44`: 1,103,762,802 bytes (x86_64),
972,032,611 (aarch64), 951,966,588 (ppc64le), 836,705,906 (s390x); `46`, built 2026-09-15:
1,037,493,924 (x86_64), 980,898,436 (aarch64). OBSERVED, `GET
https://quay.io/api/v1/repository/fedora/fedora-bootc/tag/`. Registry-reported sizes for the full base
image, not an installed footprint (§19).

**Documentation-currency note.** The Fedora bootc docs pin `container-fedora-full:
quay.io/fedora/fedora-bootc:42` in Antora attributes while `latest` resolves to `44` and `46` exists;
the same site's Fedora CoreOS page describes Fedora CoreOS as using "legacy ostree" although composefs
has been default since Fedora 41; and its base-images page calls the RHEL image-mode product "Tech
Preview status". Staleness observations about specific pages, not contradictions of facts elsewhere
here. OBSERVED, [antora.yml](https://gitlab.com/fedora/bootc/docs/-/blob/main/antora.yml) and
`fedora-coreos.adoc`.

---

## 1. Definition and implementation of immutability

### The mechanism (bootc)

**bootc's immutability is a deployment-directory boundary, not a partition boundary, and its strength
is configurable from "nothing is verified" to "the root filesystem is cryptographically bound to a
signed UKI".** That range is why a flat yes/no is useless here.

When booted, "the 'physical' host root filesystem will be mounted at `/sysroot`" and the running `/`
is a bind mount onto a deployment directory beneath it, selected by the `ostree=` kernel argument.
DOCUMENTED, [filesystem.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/filesystem.md),
[filesystem-sysroot.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/filesystem-sysroot.md).

**Read-only.** With composefs — which the project calls strongly recommended — "the entire `/` is a
read-only filesystem", and "with composefs enabled `/usr` is not different from `/`; they are part of
the same immutable image." That is a stronger claim than read-only-`/usr`: `/opt` "will be read-only,
alongside other toplevels such as `/usr`", and user-created top-levels "will be lifecycled with the
container image state, and appear immutable by default". DOCUMENTED, `filesystem.md`.

**Writable and persistent: `/etc` and `/var`, only.** `/etc` "contains mutable persistent state by
default" and gets a three-way merge on upgrade: "The *new default* `/etc` is used as a base; the diff
between current and previous `/etc` is applied to the new `/etc`; locally modified files in `/etc`
different from the default `/usr/etc` (of the same deployment) will be retained", executed by
`ostree-finalize-staged.service` at shutdown, before the new bootloader entry is written. `/var`
persists untouched: "There is exactly one `/var`. If it is not a distinct partition, then it is
automatically made a bind from `/ostree/deploy/$stateroot/var` and shared across 'deployments'."
DOCUMENTED, `filesystem.md`.

**A consequential `/var` rule.** Content shipped in `/var` inside the image "acts like a Docker
`VOLUME /var`… its contents are unpacked *only from the initial image* — subsequent changes to `/var`
in a container image are not automatically applied." Seed a file, change it later, and the change
silently never reaches existing machines. The documented remedy is `tmpfiles.d` or systemd
`StateDirectory=`, and `bootc container lint` warns about missing `tmpfiles.d` entries as of bootc
1.1.6. DOCUMENTED, `filesystem.md`.

**Four configurable strictness levels, all documented:**

1. **Default** (ostree backend, composefs mount, no fsverity): `/` read-only, `/etc` and `/var`
   persistent. "The default backend is ostree (with a composefs mount), but fsverity is not enabled by
   default." DOCUMENTED, [security.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/security.md).
2. **`etc.transient = true`**: `/etc` becomes a transient overlay discarded at reboot, removing the
   largest drift surface. "it's recommended to enable `etc.transient` if possible." DOCUMENTED.
3. **`root.transient` / `root.transient-ro`**: the whole root becomes a transient overlay (writable, or
   privileged-writable in a namespace), discarded at reboot — *reducing* immutability to let software
   write to `/usr` and `/opt` for one boot. DOCUMENTED.
4. **`composefs.enabled = verity`, or the composefs backend with a sealed UKI**: fsverity hard
   required, and with a sealed UKI the composefs digest is in the signed kernel command line and
   "*required* to match at boot". DOCUMENTED,
   [experimental-composefs.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/experimental-composefs.md).

**Where verification stops, in the project's words:** "The composefs backend enables fsverity by
default if available, but does not verify the composefs image (because there's nothing to verify it
against by default). The composefs backend with sealed UKIs does verify the composefs mount."
DOCUMENTED, `security.md`. And: "At the current time, there is no default recommended mechanism to
check the integrity of the upper composefs", tracked at
[bootc#1190](https://github.com/bootc-dev/bootc/issues/1190). So tamper-*detection* on individual
objects is present by default where the filesystem supports fsverity; tamper-*prevention* bound to a
signature needs the experimental sealed-UKI path.

**Two documented gaps.** fsverity is install-time only: "there is not yet support for automatically
ensuring that fsverity is enabled when upgrading from a state with `composefs.enabled = yes` to
`composefs.enabled = verity`. Because older objects may not have fsverity enabled, the new system will
likely fail at runtime to access these older files across the upgrade." And it "has no effect" on the
logically bound image store. DOCUMENTED, `filesystem.md`.

**Can the running OS be modified?** Yes, transiently. `bootc usr-overlay` "adds a transient overlayfs
on `/usr` that will be discarded on reboot", tmpfs-backed: "By default the kernel sizes this `tmpfs` at
50% of physical RAM… There is currently no pre-flight space check and no early warning before the
`tmpfs` is full." It "has no effect on `/etc` and `/var` — changes written there will persist", which
is exactly the drift a debugging session leaves behind. DOCUMENTED,
[bootc-usr-overlay(8)](https://github.com/bootc-dev/bootc/blob/main/docs/src/man/bootc-usr-overlay.8.md).

**Can drift occur?** Yes, in `/etc` and `/var` by default. Measure it with `ostree admin config-diff`,
with the caveat that "the 'diff' here includes metadata (uid, gid, extended attributes), so changing
any of those will also mean that updated files from the image are not applied". A `bootc config-diff`
verb exists ("Diff current /etc configuration versus default") but its man page's examples section
reads literally "TODO: Add practical examples", and in `crates/lib/src/cli.rs` it is `#[clap(hide =
true)]` and errors with "ConfigDiff is only supported for composefs backend" — DOCUMENTED (man page)
plus DOCUMENTED (source) for a limitation absent from prose, so on the default backend `ostree admin
config-diff` is the only option. Eliminate drift with `etc.transient` or `root.transient`. INFERRED
that these are the complete set of default drift channels; each is documented individually, never
enumerated. **No documented command answers "is this machine's `/usr` byte-identical to its declared
image digest". UNKNOWN.**

**Does a version uniquely identify machine state?** For the base image yes — OCI manifest digest, plus
a 128-character SHA-512 composefs digest that "uniquely identifies the filesystem contents" on the
composefs backend (DOCUMENTED, `experimental-composefs.md`). For the *machine*, no: `/etc` and `/var`
are outside it by design. Image digest plus `/etc` config-diff plus `/var` contents is the honest
description.

**How does an operator determine actual state?** `bootc status`, with `--format=json` for machines and
`--verbose` for `Download-only: yes|no` on a staged deployment, reporting booted, staged and rollback
deployments. The documented third-party probe is "`test $(bootc status --format=json | jq .spec.image)
= null`", which succeeds if an image is *not* tracked. DOCUMENTED,
[package-managers.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/package-managers.md).
`bootc internals fsck`, experimental, "expects a booted system, and performs consistency checks in a
read-only fashion" — the whole page is ten lines and lists no checks. DOCUMENTED but thin,
[experimental-fsck.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/experimental-fsck.md).

**The status surface is a stable, schemad API.** "The current API `org.containers.bootc/v1` is
stable… please change your code now to explicitly request `--format-version=1`." A JSON Schema ships
in-tree: `HostStatus` carries `booted`, `staged`, `rollback`, `rollbackQueued`, `otherDeployments`
("Other deployments (i.e. pinned)"), `readOnly`, `usrOverlay`, `type`; each `BootEntry` carries
`image`, `cachedUpdate`, `incompatible` ("has origin changes bootc does not understand"), `pinned`,
`downloadOnly`, `softRebootCapable` and a backend block; `ImageStatus` carries a required
`imageDigest`. DOCUMENTED,
[bootc-via-api.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/bootc-via-api.md),
[host-v1.schema.json](https://github.com/bootc-dev/bootc/blob/main/docs/src/host-v1.schema.json). A
`bootc-status-updated.path` unit triggers `bootc-status-updated.target` when status output would
change (DOCUMENTED, man page). And `.bootc-aleph.json`, written at install time at the root of the
physical filesystem, records the source image reference and digest, the OCI labels, a timestamp, the
bootc version, the kernel version and the SELinux state, surviving at `/sysroot/.bootc-aleph.json`.
DOCUMENTED, [bootc-install.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/bootc-install.md).

**A caveat about identification itself:** "There is no 'bootc runtime'. When used with the default
ostree backend, bootc and tools like rpm-ostree end up sharing the same code and doing effectively the
same thing. Hence, there isn't a mechanism to detect if a system 'is bootc' or 'is rpm-ostree'.
However, if the `incompatible` flag is set on a deployment, then there are layered packages and
`rpm-ostree` must be used for mutation." DOCUMENTED,
[bootc-status(8)](https://github.com/bootc-dev/bootc/blob/main/docs/src/man/bootc-status.8.md). That is
also the cleanest statement of why this profile keeps mechanism and vehicle apart: on disk, at the
ostree layer, they are the same thing.

### The vehicle (Fedora CoreOS)

**The same `/etc` + `/var` line, with a partition layout underneath and a tighter, less configurable
posture.** "The only supported writable locations are `/etc` and `/var`. `/etc` should contain only
configuration files and is not expected to store data. All data must be kept under `/var` and will not
be touched by system upgrades. Traditional places that might hold state (e.g. `/home`, or `/srv`) are
symlinks to directories in `/var`." The same page: `/` and `/usr` "are not writable"; "`/boot`
mountpoint is not writable, and the EFI System Partition is not mounted by default"; those "are
managed by `rpm-ostree` and `bootupd`, and must not be directly modified by an administrator"; and
"adding top level directories (i.e. `/foo`) is currently unsupported and disallowed by the immutable
attribute." The documented `findmnt` output shows `/sysroot`, `/usr` and `/boot` `ro`, and `/`, `/etc`,
`/var` `rw`. DOCUMENTED,
[storage.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/storage.adoc)
(rendered at [docs.fedoraproject.org/en-US/fedora-coreos/storage/](https://docs.fedoraproject.org/en-US/fedora-coreos/storage/)).

**Composefs and its documented limit.** "Fedora CoreOS introduced composefs enabled by default starting
in Fedora 41… The result is a truly read-only root (`/`) filesystem… This is a first step towards a
full verification of filesystem integrity, even at runtime." The visible consequence: "the root
filesystem (`/`) is now small and full (a few MB, 100% used)". And a real cost: "it is now impossible
to create top-level directories in `/`. A common use case for those top level directories is to use
them as mount points. We recommend using sub directories in `/var` instead. Currently, the only way
around that is to disable composefs", via `ostree.prepare-root.composefs=0`. DOCUMENTED,
[composefs.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/composefs.adoc),
[Fedora Change](https://fedoraproject.org/wiki/Changes/ComposefsAtomicCoreOSIoT).

**This is the sharpest mechanism-vs-vehicle contrast in §1.** Fedora CoreOS ships composefs *without*
fsverity enforcement, documents no `verity` or sealed-UKI option, and offers an on/off kernel argument
rather than a dial. Whether signature-backed runtime integrity lands is an open design question in its
tracker since 2022,
[fedora-coreos-tracker#1252](https://github.com/coreos/fedora-coreos-tracker/issues/1252). DOCUMENTED
as an open question; outcome UNKNOWN.

**Drift and inspection.** Same three-way `/etc` merge (same OSTree machinery), same `ostree admin
config-diff`. State is reported by `rpm-ostree status`, and `rpm-ostree kargs` creates a *new
deployment*, so kernel arguments are versioned machine state rather than free-floating configuration.
DOCUMENTED,
[kernel-args.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/kernel-args.adoc)
and `storage.adoc` ("Each update or change to the system… creates a new deployment").

**Consequences.** bootc buys a system where "what is running" is, at its strictest setting, a signed
digest the firmware enforces, and at its loosest a read-only-`/usr` system with an overlay for
debugging — the operator picks, and four strictness levels means four configurations to test, the
strictest experimental. Fedora CoreOS buys one well-tested, defaults-good configuration nobody has to
design, at the cost of a lower ceiling.

**UNKNOWN here:** whether the four bootc strictness levels are equally tested in CI (no coverage
statement is published); whether Fedora CoreOS intends to adopt any of them.

---

## 2. Unit of OS deployment

### The mechanism (bootc)

**The unit is an ordinary OCI container image that happens to contain a kernel.** "The container image
includes a Linux kernel (in e.g. `/usr/lib/modules`), which is used to boot." DOCUMENTED,
[bootc.dev/bootc](https://bootc.dev/bootc/). Deliberately not an OCI *artifact*: bootc-compatible
images "do not rely on the OCI artifact specification or the OCI referrers API". DOCUMENTED,
[relationship-oci-artifacts.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/relationship-oci-artifacts.md).

**Compatibility requirements**, short and checkable: a `/sysroot` directory with permissions like
`/usr`; `LABEL containers.bootc=1`, required so "higher level tools… can present only compatible
images"; the kernel at `/usr/lib/modules/$kver/vmlinuz` with `initramfs.img` alongside, and "You
should *not* include any content in `/boot` in your container image. Bootc will take care of copying
the kernel/initramfs as needed"; a `prepare-root.conf` enabling composefs for the ostree backend; the
UKI at `/boot/EFI/Linux/$kver.efi` for a sealed image. DOCUMENTED,
[bootc-images.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/bootc-images.md). Exactly one
kernel is an invariant: "A bootc image must contain exactly one kernel, so `ls /usr/lib/modules` must
resolve to a single directory; `bootc container lint` checks this image invariant." DOCUMENTED,
[initramfs.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/initramfs.md).

**`bootc container lint` makes validity a build-time CI gate**: "intended to be invoked via e.g. `RUN
bootc container lint` as part of a build process; it will error if any problems are detected."
DOCUMENTED,
[bootc-container-lint(8)](https://github.com/bootc-dev/bootc/blob/main/docs/src/man/bootc-container-lint.8.md).
The checks live in `crates/lib/src/lints.rs`, not in prose: fatal checks for `/var/run` as a physical
directory, `/etc` and `/usr/etc` both existing, `kargs.d` syntax, multiple kernels, required base
directories, root-of-filesystem expectations and non-UTF-8 filenames; warnings for build-system-injected
`/etc/hostname` and `/etc/resolv.conf`, missing composefs configuration, `/var` content without
`tmpfiles.d` entries, a non-empty `/boot`, and runtime dependencies. DOCUMENTED (source).

**What bootc reads and ignores from the OCI config.** `org.opencontainers.image.version` is "stored and
rendered by bootc"; `ENTRYPOINT`, `CMD`, `ENV`, `EXPOSE` and `USER` are ignored; `HEALTHCHECK` has no
consumer, because "there is no 'outer container runtime' when a bootc container is deployed on a host.
The system must perform health checking on itself (or have an external system do it)". Runtime
footprint is stated too: "bootc itself does not act as any kind of 'container runtime'… `bootc` is not
a persistent daemon by default; it does not impose any runtime overhead." DOCUMENTED,
[building/bootc-runtime.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/building/bootc-runtime.md).
The health-check sentence is load-bearing for §4, §5 and §21 scenario 4.

**On-image configuration surface**: `/usr/lib/bootc/kargs.d/*.toml` (image-managed kernel arguments),
`/usr/lib/bootc/install/*.toml` (install-config drop-ins merged alphanumerically),
`/usr/lib/bootc/install/secureboot-keys` (signed EFI signature lists),
`/usr/lib/bootc/bound-images.d/` (logically bound images), `/usr/lib/bootc/storage` (the bootc-owned
container store), `/usr/lib/ostree/prepare-root.conf` (composefs and transient-root settings).
DOCUMENTED, the respective man pages and `filesystem.md`.

**Against the framework's checklist.** Content-addressable by OCI manifest digest, plus a SHA-512
composefs digest on the composefs backend (DOCUMENTED). Standard registries with no extension: bootc
"uses the containers/image library to fetch container images (the same used by `podman`) which means it
honors almost all the same configuration options in `/etc/containers`" (DOCUMENTED,
[registries-and-offline.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/registries-and-offline.md)).
Mirrorable — "Everything in the section remapping and mirroring images applies to bootc as well"
(DOCUMENTED). Signable through the same containers/image policy machinery but **not required by
default**; §9 is the canonical treatment of that default and its consequences. Independently buildable,
which is the point of the mechanism (§15). Kernel, initrd and userspace in one image, with the
initramfs generated at build time
([initramfs.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/initramfs.md)). Air-gapped end to
end (§13, §22).

**Boot assets are versioned separately in one direction only, and it is the sharp edge.** Kernel and
initramfs travel inside the image; **the bootloader does not.** `bootc install` invokes `bootupctl
backend install` and bootc never runs `bootupctl update` afterwards; the mechanics and the contrast
with Fedora CoreOS's automatic bootloader updates are canonical in §4. What belongs here: the one
component whose failure is unrecoverable-in-band sits outside the A/B unit. DOCUMENTED,
[bootloaders.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/bootloaders.md).

**Bootloader selection is a documented decision tree**: bootupd (GRUB+shim) if `bootupd` is in the
image; systemd-boot by default if not, except on s390x; `zipl` on s390x; `--bootloader=none` to opt
out, "only supported for the Ostree backend and not for Composefs" and not on s390x. DOCUMENTED,
`bootloaders.md`.

**What the unit enables and constrains.** Enables: every registry primitive an organization already
owns — mirroring, retention, replication, pull-through caches, RBAC, promotion pipelines, `skopeo
copy` — applies to the OS with no new infrastructure. Constrains: the whole OS moves as one image, so a
one-byte fix and a kernel rebase are the same operation with the same blast radius.

### The vehicle (Fedora CoreOS)

**The update payload is an OCI image on Quay.io, but what lands on disk is an OSTree deployment applied
by rpm-ostree, not a bootc deployment.** The Fedora Change says both halves: "the hosts will pull
updates from the Quay.io container registry instead… We will notably keep using rpm-ostree for updates
(and not yet bootc)." DOCUMENTED,
[Changes/CoreOSOstree2OCIUpdates](https://fedoraproject.org/wiki/Changes/CoreOSOstree2OCIUpdates).
Rollout completed per stream: `next` at `42.20250316.1.0` (2025-03-18), `testing` at `42.20250705.2.0`
(2025-07-06), `stable` at `42.20250803.3.0` (2025-08-19). DOCUMENTED,
[major-changes.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/major-changes.adoc).

**This is the fact most likely to be got wrong: Fedora CoreOS consumes the same artifact format as
bootc and applies it with different software.** The relationship is closer than the prose suggests, and
the build system is the evidence. `coreos/fedora-coreos-config` carries a `build-args.conf` per branch
naming a **Fedora bootc base image as the builder** — `stable` from
`quay.io/bootc-devel/fedora-bootc-44-standard@sha256:d690cd06…`, `testing-devel` from
`fedora-bootc-44-standard@sha256:86ed9ccc…`, `next-devel` from `fedora-bootc-45-standard@sha256:43ac7d4b…`,
`rawhide` from `fedora-bootc-rawhide-standard@sha256:052cef99…`. The rootfs is composed by the bootc
base-image tooling (`bootc-base-imagectl build-rootfs --manifest minimal-plus`), the delta manifest
opens with "Here we override some key settings from bootc minimal-plus", the final image is assembled
with `rpm-ostree experimental compose build-chunked-oci --bootc`, and it carries `LABEL
containers.bootc=1 ostree.bootable=1`. The shipped package set includes `bootc` at `1.16.10`.
DOCUMENTED (source), [fedora-coreos-config](https://github.com/coreos/fedora-coreos-config); the stable
build's `meta.json` carries `"containers.bootc": "1"` and `"ostree.bootable": "1"` in
`coreos-assembler.oci-imported-labels`. OBSERVED. **So a current Fedora CoreOS image is a
bootc-compatible container image, built from a Fedora bootc base image, containing the bootc binary —
and it still updates itself with Zincati and rpm-ostree.** Both halves matter.

Two documented divergences from the Fedora bootc base are recorded in the delta manifest: Fedora CoreOS
keeps `/opt` and `/usr/local` as symlinks — "This is the historical default and what FCOS currently
ships. fedora-bootc uses the new `root` value, but migrating FCOS is not that simple" — and removes
`/etc/machine-id`, "Required by Ignition, and makes the system not compatible with Anaconda. Note this
deviates from fedora-bootc and means `systemctl enable` doesn't work in a container build." DOCUMENTED
(source), `manifests/coreos-bootc-delta.yaml`. Those two lines summarize why the products are not yet
one; the working group considering merging them is canonical in §18, its governance scoping in §16.

**Fedora CoreOS also ships pre-built disk images, which bootc does not.** Per platform the stable stream
publishes `raw.xz` and `4k.raw.xz` metal images, a live ISO, a PXE triple (kernel, initramfs, rootfs)
and a `qcow2.xz`, plus per-region AWS AMIs and GCP and KubeVirt references. OBSERVED,
`builds.coreos.fedoraproject.org/streams/stable.json`. The disk image is the unit for *installation*;
the OCI image is the unit for *updates*. Both are versioned as `X.Y.Z.A` — Fedora major version,
package-set datestamp, stream code (1 next, 2 testing, 3 stable), build revision. DOCUMENTED,
[faq.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/faq.adoc).
`quay.io/fedora/fedora-coreos` carries 108 tags including `stable`, `testing`, `next`, `rawhide`,
`branched`, `testing-devel` and `next-devel`. OBSERVED, Quay.io API.

**Signing.** "All binary artifacts, ostree commits, and OS images belonging to Fedora and Fedora CoreOS
(FCOS) are signed via GPG." DOCUMENTED,
[update-barrier-signing-keys.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/update-barrier-signing-keys.adoc).
The shipped container policy is stricter than upstream bootc's default and is canonical in §9; note
here only that ostree *commit* signatures no longer exist and verification moved to the container
payload (§15).

**Air gap.** No Fedora CoreOS-specific procedure was found; the generic OCI-directory procedure is
documented on the bootc and Fedora bootc sides (§22 HOST). Whether it transfers cleanly to an
`rpm-ostree`-driven machine is **UNKNOWN** — plausible from the pieces, not written down.

---

## 3. OS construction and customization

### The mechanism (bootc)

**Customization is a Containerfile: "Every tool and technique for creating application base images
should apply to the host Linux OS as much as possible."** During a build the image is fully mutable —
"all parts of the filesystem (e.g. `/usr` in particular) as fully mutable state, and writing there is
encouraged" — and package installation works unchanged: "it is very much expected that the pattern of
`RUN $pkgsystem install somepackage && $pkgsystem clean all` type flow Just Works here." DOCUMENTED,
[building/guidance.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/building/guidance.md).

**Available bases.** Anything meeting the §2 requirements. Published today: Fedora
(`quay.io/fedora/fedora-bootc`, tags 41–46 plus rawhide, four architectures each — amd64, arm64,
ppc64le, s390x, **no riscv64**), CentOS Stream 9 and 10 (`quay.io/centos-bootc/centos-bootc`), and
RHEL through the commercial image-mode product. DOCUMENTED,
[base-images.adoc](https://gitlab.com/fedora/bootc/docs/-/blob/main/modules/ROOT/pages/base-images.adoc);
tag and manifest-platform inventory OBSERVED via the Quay API. **Arbitrary non-Fedora-family bases are
a stated goal and a current limitation**: "bootc itself is not tied to Fedora derivatives; [this
issue](https://github.com/coreos/bootupd/issues/468) tracks the main blocker for other distributions."
DOCUMENTED,
[installation.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/installation.md). The adopters
file shows real multi-distribution use — HeliumOS, AlmaLinux Atomic SIG, Universal Blue, CIQ/Rocky
Linux, ALT Atomic, Caligra, Fyra Labs — all Fedora/RHEL-family. OBSERVED,
[ADOPTERS.md](https://github.com/bootc-dev/bootc/blob/main/ADOPTERS.md).

**The "full" Fedora/CentOS base image**, per its own philosophy statement: `bootc`, a kernel, systemd
"configured to run by default when executed as a container too", NetworkManager with "Full support for
many complex networking types", podman, "Filesystem tools, support for LUKS, LVM, RAID etc.", and
"Lots of other supporting tools, such as `sos`, `jq`". It excludes hypervisor agents: "the image does
*not* include hypervisor specific agents. You may install them in derived builds. For example, on
Amazon Web Services, you may want to install `cloud-init`; but this is also not required." A "minimal"
image — "just `kernel systemd bootc`; everything else (including e.g. networking) you need to add" — is
published only to the GitLab container registry. DOCUMENTED, `base-images.adoc`.

**Where customization occurs.** Build time is primary — "The bootc project currently takes a relatively
hard stance that system state should come from a container image" — but not exclusive. The documented
points: **build time** via Containerfile, where a driver, module, firmware, agent, CA certificate or
system service is a package install or a `COPY`; **kernel arguments**, baked at
`/usr/lib/bootc/kargs.d/` or machine-local at `/etc/bootc/kargs.d/`; **`/etc` at install or runtime**,
which Fedora bootc treats as first-class (§6); **a transient overlay at runtime**, for debugging; and
**logically bound images**.

**Logically bound images are the most architecturally novel primitive here.** A symlink in
`/usr/lib/bootc/bound-images.d` pointing at a Podman Quadlet `.image` or `.container` file binds an
application container's lifecycle to the OS image: "during a `bootc upgrade` or `bootc switch` the
bound images defined in the new bootc image will be automatically pulled into the bootc image storage",
reachable via `podman --storage-opt=additionalimagestore=/usr/lib/bootc/storage`. Stated use cases are
logging forwarders, monitoring, configuration-management and security agents, because "if the remote
registry is unavailable temporarily, the host system may run for a longer period of time without log
forwarding or monitoring, which can be very undesirable"; the comparison drawn is that they "allow you
to reference container images with the same confidence you can with `ExecStart=` in a systemd unit."
DOCUMENTED,
[logically-bound-images.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/logically-bound-images.md).

The same page is clear about limits: the *only* field parsed is `Image`; `PullSecret=` and `Arch=` are
unsupported; rootless containers from the system-owned store are "not supported… and none is planned";
the store must not be enabled globally in `storage.conf`, because layer garbage collection can break
floating images; "at the current time, logically bound images are [not supported by Anaconda]", which
matters for ISO installs; images must be in `/var/lib/containers` at `bootc install` time to reach the
target; and images bound to a rollback deployment are retained, so a rollback takes the agents with it.

**What does not work, documented rather than discovered.** `RUN podman pull …` inside a build "will
create problems, as the `podman` runtime will create whiteout files inside the container image
filesystem itself" ([bootc#128](https://github.com/bootc-dev/bootc/issues/128)). `chcon` at build time
fails because "the container runtime state will deny the attempt to 'physically' set the
`security.selinux` extended attribute"; `semanage fcontext` is the supported path. systemd `sysext` and
`confext` "are not currently supported on bootc-managed systems", for two stated reasons — overlayfs
stacking depth (`FILESYSTEM_MAX_STACK_DEPTH = 2`) and OS-specific labeling. DOCUMENTED,
`bootc-images.md`, `guidance.md`, `filesystem.md`.

**The `/opt` problem, with three documented answers and named trade-offs:** symlink the writable parts
to `/var` at build time (the maximum-immutability recommendation, worked example `RUN dnf install
examplepkg && mv /opt/examplepkg/logs /var/log/examplepkg && ln -sr /var/log/examplepkg
/opt/examplepkg/logs`, or `BindPaths=` in the unit); a state overlay per top-level via
`ostree-state-overlay@opt.service` (persistent, but "during updates, new files from the container image
override any locally modified version", and "there is no equivalent to this feature in the
Docker/Podman ecosystem"); or transient root. DOCUMENTED, `filesystem.md`, `guidance.md`.

**Configuration placement rules**, the general form: "Put read-only data and executables in `/usr`; Put
configuration files in `/usr` (if they're static), or `/etc` if they need to be machine-local; Put
'data' (log files, databases, etc.) underneath `/var`", because "These 'locally modified' files can be a
source of state drift. The best pattern to use is 'drop-in' directories." DOCUMENTED, `guidance.md`.

**Users and groups carry a documented drift trap.** "bootc has nothing to do directly with configuring
users or groups" beyond `bootc install --root-ssh-authorized-keys`; use `systemd-sysusers` or
`DynamicUser=yes` rather than allocating at build time, because "Any invocation of `useradd` or
`groupadd` that does not allocate a *fixed* UID/GID may be subject to 'drift' in subsequent rebuilds by
default." And injecting `/var/home/someuser/.ssh/authorized_keys` into a build means "existing systems
will *not* get the updated authorized keys file" — the `/var` rule from §1 in its most surprising form.
DOCUMENTED,
[building/users-and-groups.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/building/users-and-groups.md).

**Secrets at build time.** "**The bootc project does not currently include one single opinionated
mechanism for secrets.**" The pull secret goes at `/etc/ostree/auth.json`, `/run/ostree/auth.json` or
`/usr/lib/ostree/auth.json` — deliberately not podman's default, "as some of the file paths used there
are not appropriate for system services (e.g. reading the `/root` home directory)". A credential helper
needs a no-op `{}` authfile. Listed alternatives: cloud metadata, embedding in disk images ("Rotating
them would require an additional management tool, or refreshing disk images"), bare-metal installers,
systemd credentials. DOCUMENTED,
[building/secrets.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/building/secrets.md). No
mechanism for *workload* secrets at the OS layer; the ecosystem answer is a secrets agent shipped as a
logically bound image.

**Kernel arguments at build time** live in `/usr/lib/bootc/kargs.d/*.toml` as `kargs = [...]` with an
optional `match-architectures`; "Changes to `kargs.d` files included in a container build are honored
post-install; the difference between the set of kernel arguments is applied to the current bootloader
configuration. This will preserve any machine-local kernel arguments." Two documented traps: "**At the
current time, `bootc` does not itself offer an API to manipulate kernel arguments maintained
per-machine**", and "It is currently undefined behavior to remove kernel arguments locally that are
included in the base image via `/usr/lib/bootc/kargs.d`." `match-architectures` uses Rust's names — "A
common discrepancy is that Debian derivatives use `amd64`, whereas Rust (and Fedora derivatives) use
`x86_64`." DOCUMENTED,
[building/kernel-arguments.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/building/kernel-arguments.md).
**Guidance for replacing the kernel package in a derived image was not found. UNKNOWN.**

**FIPS.** Fedora bootc carries a dedicated `fips-crypto-policies` page that Fedora CoreOS does not; its
existence is DOCUMENTED
([nav.adoc](https://gitlab.com/fedora/bootc/docs/-/blob/main/modules/ROOT/nav.adoc)), its substance
**UNKNOWN** and on the follow-up list. A `fips/` example also exists in
[gitlab.com/fedora/bootc/examples](https://gitlab.com/fedora/bootc/examples), alongside `nvidia/`,
`kernel-module/`, `kernel-rt-rpm-ostree/`, `wifi/` and `logically-bound-images/`. DOCUMENTED.

**Producing a bootable disk is a separate tool whose home moved recently.** `bootc-image-builder`
produced `ami`, `anaconda-iso`, `bootc-installer`, `gce`, `iso`, `qcow2`, `raw`, `vhd`, `vmdk` (and
`pxe-tar-xz` per its image-types table, which disagrees with its own `--type` help string). Its
repository is **archived**: "The `bootc-image-builder` repository has been merged into the
`image-builder` repository. All issues have been migrated and this repository has been archived."
DOCUMENTED, [osbuild/bootc-image-builder](https://github.com/osbuild/bootc-image-builder).
`osbuild/image-builder` is active, last pushed 2026-09-16, most recent release `v82.0.0` (2026-09-04);
the migration guide at the destination is currently an empty heading. OBSERVED. The Fedora bootc docs
still point at the archived repository and at `quay.io/centos-bootc/bootc-image-builder:latest`.
Invocation and host requirements are in "What a full experimental pass needs". **This extends the Pulse
baseline rather than contradicting it.**

### The vehicle (Fedora CoreOS)

**The answer is "run a container", stated directly.** "On Fedora CoreOS, containers are the way to
install and configure any software not provided by the base operating system." Where containers cannot
reach, package layering exists and is discouraged in the project's own words: "The package layering
mechanism provided by rpm-ostree will continue to exist for use in debugging a Fedora CoreOS machine,
but we strongly discourage its use." DOCUMENTED, `faq.adoc`. The OS-extensions page names the real
exceptions: "drivers or VPN software are potential candidates because they are harder to containerize."

**Layering has documented friction beyond the discouragement.** No native Ignition directive exists;
the documented pattern is a hand-written systemd unit invoking `rpm-ostree install`, ordered
`Before=zincati.service` "to avoid conflicting rpm-ostree transactions", guarded by a stamp file, ending
in a reboot. The docs flag it as provisional: "In the future, we will have a more Ignition-friendly
method of doing this with stronger guarantees", pointing at
[butane#81](https://github.com/coreos/butane/issues/81) and
[fedora-coreos-tracker#681](https://github.com/coreos/fedora-coreos-tracker/issues/681). DOCUMENTED,
[os-extensions.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/os-extensions.adoc).

**And the documentation tells heavy customizers to leave**: "If you're making nontrivial changes to the
base operating system, you may instead consider using Fedora Bootc, which is oriented around custom OS
builds derived from a starting base image", echoed in the FAQ: "If you find yourself needing to heavily
customize Fedora CoreOS beyond what OS extensions provide, it might make more sense to instead build on
top of Fedora Bootc directly." DOCUMENTED. Few projects route users to a different project this
explicitly, and it is the cleanest evidence the two entries here are different products.

**Can Fedora CoreOS itself be a bootc base image?** Yes, per upstream bootc: "any Fedora derivative
already using `ostree` can be seamlessly converted into using bootc; for example, Fedora CoreOS can be
used as a base image; you will want to also `rpm-ostree install bootc` in your image builds currently.
There are some overlaps between `bootc` and `ignition` and `zincati` however." DOCUMENTED,
`installation.md`.

**Custom builds of Fedora CoreOS itself** go through `coreos-assembler`, with a custom-stream concept at
[stream-metadata.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/stream-metadata.adoc);
requirements and the now-redirected guidance on *derivatives* are in §15. `coreos-assembler` took 375
commits from 26 distinct authors in the 12 months to 2026-09-16 despite a 2024 last tag, because it is
consumed as a container image. OBSERVED.

**Kernel modules and GPU drivers have no documentation page**; `modules/ROOT/pages` contains none.
OBSERVED. A documented *absence of documentation*, not evidence it cannot be done, recorded as
**UNKNOWN** for supported-path purposes. The decision trail and the maintained Fedora bootc NVIDIA
example it points at are in §8.

### The extensibility/controlled-state trade-off

**bootc moves the entire cost of the image to the adopter and gives them the entire benefit.** Build,
test matrix, signing, CVE patching and support of the resulting image are theirs. What they get is that
"customization" and "the artifact" are the same object: no second configuration language, no drift
between built and deployed, and the digest CI tested is the digest the machine boots. The constraint is
not "cannot install packages at runtime" but that *every* change is a rebuild, and a rebuild is a
reboot.

**Fedora CoreOS keeps the image and hands the operator a configuration surface.** Nobody runs a build
pipeline, and the image is the one 184 releases of public testing have been applied to. What is given
up is the ceiling: layering discouraged, drivers undocumented, and the documented answer to "I need
more" is a different project.
---

## 4. Upgrade mechanism

The two systems run different upgrade state machines on top of the same on-disk model, so each is
documented in full.

### The mechanism (bootc)

**Before upgrade.** *Where does the new OS come from?* A container registry, or any containers/image
transport: `registry`, `oci`, `oci-archive`, `docker-daemon`, `containers-storage`. DOCUMENTED,
[bootc-switch(8)](https://github.com/bootc-dev/bootc/blob/main/docs/src/man/bootc-switch.8.md). **There
is no project-operated update service anywhere in the path** — the strongest single fact in bootc's
§22 answer, and a design consequence rather than a policy.

*Who initiates?* An operator running `bootc upgrade`, or the shipped
`bootc-fetch-apply-updates.timer`, whose service "causes `bootc` to perform the following steps: Check
the source registry for an updated container image; If one is found, download it; Reboot", with the
three steps decoupled as `bootc upgrade --check`, `bootc upgrade`, `bootc upgrade --apply`.
DOCUMENTED,
[bootc-fetch-apply-updates.service(5)](https://github.com/bootc-dev/bootc/blob/main/docs/src/man/bootc-fetch-apply-updates.service.5.md).
Disabling it in a derived image is a documented one-liner, `RUN systemctl disable
bootc-fetch-apply-updates.timer`. DOCUMENTED,
[building/management-services.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/building/management-services.md).
The unit's actual intervals, and the man page's disagreement with them, are in §11.

*How is the artifact verified?* By the containers/image signature policy at
`/etc/containers/policy.json`, **which upstream does not require by default**; bootc's one control is
`--enforce-container-sigpolicy`. §9 is the canonical treatment, including the three signature states
`bootc status` reports and what the default means for an unconfigured machine.

*Without Kubernetes?* Yes; bootc has no Kubernetes dependency. *Without hosted infrastructure?* Yes;
there is none.

**During upgrade.** The running system is untouched: "Changes to the base image are staged, and the
running system is not changed by default… A queued update is visible as `staged` in `bootc status`."
DOCUMENTED, [upgrades.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/upgrades.md),
[bootc-upgrade(8)](https://github.com/bootc-dev/bootc/blob/main/docs/src/man/bootc-upgrade.8.md).
Writes go to `/sysroot/ostree/repo` (ostree backend) or `/composefs` plus
`/state/deploy/<deployment-id>/` (composefs backend), where "transient, not-yet-finalized deployment
state… lives under `/run/composefs/staged-deployment` and is never persisted to disk". DOCUMENTED,
`experimental-composefs.md`.

**The staging controls are finer-grained than most systems offer, and are the mechanism's best
fleet-adjacent feature.** Four states, all documented in `upgrades.md`:

- `--check` — "only downloads the updated manifest and image configuration (typically kilobyte-sized
  metadata)". A fleet-wide "is there anything new" probe costing kilobytes per node.
- `--download-only` — fetches layers into a staged deployment that "will not be applied on shutdown or
  reboot until you explicitly apply it", shown as `Download-only: yes` under `--verbose`.
- `--from-downloaded` — "unlocks the staged deployment for automatic application on the next shutdown
  or reboot, without fetching updates from the container image source". The maintenance-window
  primitive: download Monday, apply Saturday, get exactly the bits you tested.
- `--apply` — apply now, with a reboot.

Two documented consequences operators get wrong: "If you reboot before applying a download-only
update, the system will boot into the current deployment and the staged deployment will be discarded.
However, the downloaded image data remains cached"; and a `bootc switch` to a different image replaces
a download-only staged deployment.

**Two forward-looking statements change operational assumptions and are worth recording**: "The
`--apply` option currently always reboots the system. In the future, this command may detect cases
where no kernel changes are queued and perform a userspace-only restart instead", and "in the future
this is likely to change such that reboots outside of a `bootc upgrade --apply` do *not* automatically
apply the update in addition." Today an ordinary `reboot` applies a staged, non-download-only update.
DOCUMENTED, `bootc-upgrade(8)`.

**Soft reboot is supported and exposed**: `--soft-reboot={required,auto}` on `upgrade` and `rollback`,
with `required` failing if unavailable, and `bootc status` reporting `softRebootCapable` per boot
entry. DOCUMENTED, man pages and `host-v1.schema.json`. A real reduction in update cost for workloads
that tolerate a userspace restart, and absent from most A/B systems.

*Kernel, initrd and bootloader?* Kernel and initramfs travel inside the image and are copied to
`/boot`; "Editing the copy in `/boot` is not supported because `bootc` replaces it from the container
image during an update." DOCUMENTED, `initramfs.md`.

**The bootloader does not move, and this is the canonical statement of the divergence that recurs in
§2, §9 and §21.** bootc runs `bootupctl backend install` at install time only: "Currently, `bootc` only
runs `bootupd` during the installation process. It does **not** automatically run `bootupctl update` to
update the bootloader after installation. This means that bootloader updates must be handled
separately, typically by the user or an automated system update process." DOCUMENTED,
[bootloaders.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/bootloaders.md). **Fedora CoreOS
does the opposite**: "The bootloader update is now performed automatically by default. The bootupd
project is included in Fedora CoreOS and supports both manual and automatic updates… Both the EFI
system partition and BIOS MBR can be updated by bootupd. Bootloader updates are performed
automatically by `bootloader-update.service`", motivated by BootHole-class vulnerabilities, with
`bootupctl status`, `bootupctl update` and `bootupctl adopt-and-update` for images predating bootupd.
DOCUMENTED,
[bootloader-updates.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/bootloader-updates.adoc).
Same component, same upstream project, opposite operational default — and an operator building their
own bootc image inherits the bootc default unless they arrange otherwise. For anyone tracking
boot-chain CVEs on bootc, that is a separate, operator-owned lifecycle sitting under the transactional
one.

*Power loss halfway?* **bootc's own documentation does not address it.** The nearest primary statement
is upstream OSTree's: "If the system crashes or you pull the power, you will have either the old
system, or the new one."
[ostree atomic upgrades](https://ostreedev.github.io/ostree/atomic-upgrades/). DOCUMENTED (upstream),
INFERRED for bootc on the ostree backend. **For the composefs backend there is no equivalent statement
at all. UNKNOWN**, and the top §21 experiment for that reason.

**At reboot.** The new system is selected by the bootloader entry finalization wrote —
`ostree-finalize-staged.service` on the ostree backend, `bootc-finalize-staged.service` on composefs.
DOCUMENTED, `boot-failure-detection.md`, `filesystem.md`.

**How is successful boot determined? Largely it is not, and this is the most consequential gap.** What
bootc documents is detection of a *failed finalization*, not a failed boot: when
`ostree-finalize-staged.service` fails at shutdown it writes a stamp file in `/boot`, and on the next
boot `ostree-boot-complete.service` finds it and itself fails, surfacing in the journal. The composefs
backend has no `-boot-complete` equivalent; the documented advice is "check the journal for failures
from the previous boot: `journalctl -u bootc-finalize-staged.service -b -1`". DOCUMENTED,
[boot-failure-detection.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/boot-failure-detection.md).

**Boot-entry counting — the systemd Automatic Boot Assessment mechanism that would give unattended
rollback — is explicitly not configured on the composefs backend**: "At the current time, the composefs
backend does not configure boot entry counting, this is likely to be added in the future." DOCUMENTED.
Whether the *ostree* backend enables it by default is stated nowhere. **UNKNOWN**, deliberately left as
UNKNOWN rather than inferred from ostree having gained the capability; having a capability and enabling
it by default are different claims.

*Is OS, Kubernetes or application health checked?* No, and the project is unambiguous about whose job
it is: "The system must perform health checking on itself (or have an external system do it)."
**greenboot, the obvious candidate, does not integrate**: the sole mention in the entire documentation
tree is the parenthetical "(note that as of right now, greenboot does not yet integrate with bootc)".
DOCUMENTED, `building/bootc-runtime.md`. A documented negative is much better evidence than silence.

**After failure.** Rollback is not automatic in anything bootc ships; see §5.

### The vehicle (Fedora CoreOS)

**A genuinely different, and in fleet terms more capable, upgrade machine — and none of it is bootc.**
"By default, the OS performs continual auto-updates via two components: rpm-ostree handles multiple
on-disk OSTree deployments and can switch between them at boot-time; Zincati continually checks for OS
updates and applies them via rpm-ostree." DOCUMENTED,
[auto-updates.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/auto-updates.adoc).

The payload is the OCI image on Quay.io since the transport change completed on stable at
`42.20250803.3.0`; Zincati polls a Cincinnati update graph to decide when; verification is GPG
signatures plus the shipped reject-by-default container policy (§9).

**Three features ship in the open-source node agent that most projects put in a commercial fleet
product**, and they are why Fedora CoreOS is fleet-capable rather than single-node:

1. **Phased rollout with per-node wariness.** "A custom 'rollout wariness' value… can be provided to
   let the server know how eager, or how risk-averse, the node is to receiving updates" — a float from
   `0.0` (most eager) to `1.0` (most conservative), set at provisioning time by a Butane snippet
   writing `/etc/zincati/config.d/51-rollout-wariness.toml`. A canary tier is a first-boot config file,
   not a control plane.
2. **Finalization strategies**: `immediate` (the default), lock-based, or `periodic` weekly maintenance
   windows on a UTC schedule, with worked examples.
3. **Cluster-wide reboot coordination** via the FleetLock HTTP protocol — **client side only**; see
   §11 for the backends and their maintenance state.

DOCUMENTED, `auto-updates.adoc` and [Zincati](https://coreos.github.io/zincati/usage/updates-strategy/).

*Without Kubernetes?* Entirely — the lock protocol is generic HTTP and a Kubernetes-backed lock manager
is one third-party option. *Without project infrastructure?* Mostly. The Cincinnati graph server is
Fedora-hosted by default, open source and self-hostable
([coreos/fedora-coreos-cincinnati](https://github.com/coreos/fedora-coreos-cincinnati)), and can be
bypassed entirely by stopping Zincati and driving `rpm-ostree rebase` by hand — the documented
stream-switching procedure. DOCUMENTED,
[update-streams.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/update-streams.adoc).
The graph server is lightly maintained: 14 commits from 6 authors in the 12 months to 2026-09-16, no
tagged release. OBSERVED, `gh api repos/coreos/fedora-coreos-cincinnati`.

**Update barriers are a real and under-appreciated feature.** "In order to make automatic updates of
Fedora CoreOS work across major Fedora releases, the above set of embedded signing keys is refreshed at
least once per Fedora release cycle. When that happens, an update barrier is put in place in the FCOS
update graph. The primary reason… is to make sure that older (and possibly stale) instances
automatically receive and trust newly generated keys. This is achieved by forcing such machines to
progressively catch up on intermediate updates (signed by an already trusted key) before jumping to the
latest published release." DOCUMENTED, `update-barrier-signing-keys.adoc`. A machine off for a year
walks forward through barrier releases rather than jumping — so the graph does real safety work, and
**skipping upgrades is not unconditionally allowed** (§18 has the measured barrier list).

*What gets written?* A new OSTree deployment in the shared root partition; the running filesystem is
unchanged, `/var` shared and untouched, `/etc` three-way merged at finalization, with a GRUB menu entry
per deployment carrying the `ostree=` argument. DOCUMENTED, `storage.adoc`. *Power loss?* Same OSTree
guarantee, same absence of a project-specific statement. *Boot success?* No automatic assessment ships;
see §5.

### Comparing the two upgrade architectures

Both are **transactional-image, deployment-directory** systems rather than A/B partition systems, with
concrete consequences:

- **No fixed-size slot.** Deployments share one root filesystem and one object store, so there is no
  "passive slot too small" failure and no doubling of the OS partition — but a deployment consumes
  space in the *same* filesystem as `/var`, coupling disk pressure to OS updates. This is why §21
  scenario 8 is a high-value experiment here.
- **`/etc` is versioned; `/var` is not.** The three-way merge gives `/etc` per-deployment content that
  travels with a rollback; `/var` is shared and does not. Most A/B systems version neither.
- **Deduplication is real.** Two deployments differing by one package share every unchanged object, so
  upgrade download is layer-delta-shaped rather than whole-image-shaped — though no figures are
  published (§19).
- **Neither ships automatic rollback.** The shared weakness, documented on both sides (§5).
- **bootc's staging controls are finer; Fedora CoreOS's rollout controls are richer.** `--check` /
  `--download-only` / `--from-downloaded` give per-node timing precision Zincati does not expose;
  phased rollout, wariness and maintenance windows give fleet shaping bootc explicitly defers: "The
  upstream bootc project provides a low-level generic tool that can be driven by multiple higher level
  management tooling." DOCUMENTED,
  [management-generic.adoc](https://gitlab.com/fedora/bootc/docs/-/blob/main/modules/ROOT/pages/management-generic.adoc).

---

## 5. Rollback and recovery

The framework asks these be treated as different concepts, which is productive here: the two systems
have near-identical rollback and very different recovery.

### Rollback to the previous OS

**bootc.** `bootc rollback` "change[s] the bootloader entry ordering; the deployment under `rollback`
will be queued for the next boot, and the current will become rollback. If there is a `staged` entry
(an unapplied, queued upgrade) then it will be discarded." `--apply` reboots immediately;
`--soft-reboot` is available; and a journal message with
`MESSAGE_ID=26f3b1eb24464d12aa5e7b544a6b5468` is logged "in order to detect a rollback invocation" — a
small but genuinely useful fleet affordance. The page also carries the warning that matters most in
practice: "if there is an active agent doing automated upgrades (such as the default
`bootc-fetch-apply-updates.timer`…) the change here may be reverted. It's recommended to only use this
in concert with an agent that is in active control." DOCUMENTED,
[bootc-rollback(8)](https://github.com/bootc-dev/bootc/blob/main/docs/src/man/bootc-rollback.8.md).
Rollback is also declarative: `bootc edit`'s `HostSpec` has exactly two fields, `image` and `bootOrder`
(`default` or `rollback`). DOCUMENTED, `bootc-edit(8)`.

**Fedora CoreOS.** `rpm-ostree rollback -r`, preceded by `systemctl stop zincati.service`, with the
cost stated plainly: "This is a manual operation that requires human intervention and console access."
A temporary rollback is available by holding Shift at boot and picking a GRUB entry. The same agent
warning appears: "Zincati will keep looking for updates and upgrade to any new available OS deployment,
other than the one you just reverted", with `systemctl disable --now zincati.service` as the documented
fix. DOCUMENTED,
[manual-rollbacks.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/manual-rollbacks.adoc).

**The `/etc` asymmetry applies to both and surprises people**, verbatim from bootc: "When you perform a
rollback (e.g., with `bootc rollback`), any changes made to files in the `/etc` directory won't carry
over to the rolled-back deployment. The `/etc` files will revert to their state from that previous
deployment instead. This is because `bootc rollback` just reorders the existing deployments. It doesn't
create new deployments. The `/etc` merges happen when new deployments are created." DOCUMENTED,
`bootc-rollback(8)`. `/var` is shared and therefore *does* carry over. So a rollback reverts
configuration and keeps data — defensible, and exactly the combination that produces config/data skew
if an upgrade migrated a schema.

### Automatic rollback: absent on both, documented on both

**bootc.** Nothing ships. Boot-entry counting is not configured on the composefs backend, greenboot
does not integrate, and health checking is stated to be the system's or an external system's job (§4).
DOCUMENTED as a set of individual statements; the *conclusion* that no automatic rollback ships is
INFERRED from them, since no page says so in those words.

**Fedora CoreOS.** Same outcome, better-evidenced. greenboot is not part of Fedora CoreOS — its own
upstream documents installing it as a layered add-on — and the automatic-rollback design question
[#47](https://github.com/coreos/fedora-coreos-tracker/issues/47) has been open since 2018. Carried from
the Pulse baseline and recorded there as documented absence rather than unknown, which is the right
call: the docs describe rollback as manual and the tracker issue names the gap.

**This is the most important architectural finding in §5.** Two systems whose whole premise is safe,
frequent, automatic updates both ship without an unattended path back from a bad boot. Both provide the
raw material — a retained deployment, a bootloader entry, a documented one-command revert — and neither
wires it to a trigger. The operator, or a fleet agent above them, owns that wiring.

### Retained versions, pinning, and multi-version rollback

**Fedora CoreOS: one retained prior version by default** (two deployments total: booted +
rollback). Carried from the Pulse baseline. Pinning against garbage collection is possible
via `ostree admin pin` but is documented only upstream in OSTree, not in the Fedora CoreOS
documentation at all. DOCUMENTED (upstream) / UNKNOWN as a supported procedure.

**bootc: UNKNOWN.** No bootc page states a retention count. The status schema models `booted` + `staged`
+ `rollback` + `otherDeployments` ("i.e. pinned"), implying a two-deployment working set plus pinned
extras — INFERRED, and left as an inference. `pinned` is *reported* per boot entry ("Whether this entry
will be subject to garbage collection") but **bootc provides no verb to set it**, and `ostree admin
pin` is never mentioned in bootc's documentation, so an operator wanting a known-good deployment held
indefinitely drops to the backend tool bootc calls an implementation detail. DOCUMENTED (the
reporting), UNKNOWN (the bootc-side procedure). `bootc install reset` documents `ostree admin undeploy
<index>` for removal and notes "You cannot remove the stateroot directory while deployments still exist
in it. OSTree protects deployment directories with filesystem-level mechanisms."

**Multi-version rollback. bootc:** `bootc switch <image>@sha256:…` to any digest, with the documented
consequence "When you do this, `bootc upgrade` will always be a no-op. In this model, upgrades are then
always triggered by further `switch` operations", plus `bootc upgrade --tag`. DOCUMENTED,
`bootc-switch(8)`. **This is materially better than "one step back": any historical version still in a
registry is reachable in one command.** The on-disk set stays small; the *network* copy is the version
archive. **Fedora CoreOS:** `rpm-ostree rebase` to a specific stream or version, downgrades blocked by
default (§18), with a documented caution against moving backwards across streams — "Upstream software
components are generally tested for upgrading, not downgrading… it is typically safer to rebase from
`stable` -> `testing`… but less safe to go the other direction", and "switching between streams may
introduce regressions or bugs due to skipping update barriers." DOCUMENTED, `update-streams.adoc`.

### Recovery environment, factory reset, and unavailability

**Recovery environment. bootc: none of its own**, which is a correct not-applicable rather than a gap —
a bootc system has whatever its distribution provides. **Fedora CoreOS: a live ISO that is a full
recovery environment**, able to bring up a functioning system entirely from memory, with
`coreos-installer` reinstalling to disk from it; published as a first-class release artifact alongside
a PXE triple. DOCUMENTED,
[live-booting.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/live-booting.adoc);
artifacts OBSERVED in the stream metadata.

**Factory reset: the mechanism now leads the vehicle, and this updates the Pulse baseline**, which
recorded factory reset as not-applicable for a mechanism. `bootc install reset` "allows you to perform
a non-destructive factory reset of an existing bootc system. This creates a fresh installation state in
a new stateroot while preserving the existing system's files on disk. After rebooting into the new
deployment, you can still access the old system's data by examining files in
`/sysroot/ostree/deploy/<old-stateroot>/`." After the reboot "`/etc` contains only the configuration
from the container image" and "`/var` is empty". Root-filesystem kernel arguments (`root=`,
`rootflags=`, `rd.*`, and anything from `kargs.d`) are inherited unless `--no-root-kargs` is passed;
`--target-imgref` resets onto a different image; `--apply` reboots. Documented limitations: it requires
`--experimental`, "Only works on systems already running bootc (not for initial installations)", and
"the old stateroot is not automatically removed and will consume disk space until manually deleted" —
a real trap on a disk-constrained edge device. DOCUMENTED,
[experimental-install-reset.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/experimental-install-reset.md).
Resetting into a parallel stateroot rather than wiping makes "reset" and "keep the evidence" the same
operation, which for a fleet where a failed device is also a support case is the difference between a
recoverable diagnosis and a lost one.

**Fedora CoreOS has no factory reset.** The open request
[#399](https://github.com/coreos/fedora-coreos-tracker/issues/399), open since 2020, names the gap
precisely: reprovisioning is the intended answer, but on single-node bare metal without external
infrastructure a manual reinstall is impractical. Carried from the Pulse baseline.

**When things are unavailable.** *Kubernetes:* no effect on either; neither has it in the recovery path.
*Management infrastructure:* no effect on bootc, since there is no management plane in the required
path; for Fedora CoreOS an unreachable graph means no updates and nothing else, with `rpm-ostree
rollback` and GRUB entry selection local. *Networking:* rollback works on both, because both retained
deployments are on disk; Fedora CoreOS's live-ISO recovery is local media, and bootc's offline `oci:`
transport means even *forward* recovery works from a USB stick. *Corrupt persistent data:* neither
helps, and both are honest about it — `/var` is shared and not rolled back, by design, "a bootc update
or rollback should not affect this application data", and `bootc install reset` is the only documented
path back to a known `/var` state on either side. DOCUMENTED, `filesystem.md`.

**What is a "known-good state"?** Neither project defines the term. bootc *implements* it as an image
digest, with `/etc` and `/var` explicitly outside unless `etc.transient` is enabled — and with
`etc.transient` plus a sealed UKI it becomes something firmware enforces. Fedora CoreOS implements it
as a release on a stream. Both INFERRED from the documented designs; neither states a definition.
**UNKNOWN:** whether either has a documented position on recovering from a corrupted object store, as
opposed to a corrupted image or a bad boot; `bootc internals fsck` exists but documents no check list
and no repair path.

---

## 6. Configuration model

**This is where mechanism and vehicle diverge most, because Fedora CoreOS's configuration model is
Ignition and bootc has no configuration model at all.** Saying that plainly is more useful than
constructing a false symmetry.

### The mechanism (bootc)

**Configuration belongs in the image, and where it cannot, in `/etc` written by somebody else's tool.**
The placement rules and the drop-in-directory recommendation are in §3. The framework's four layers map
as:

- *Image configuration* — the Containerfile, `/usr/lib/bootc/kargs.d/`, `/usr/lib/bootc/install/*.toml`,
  `/usr/lib/ostree/prepare-root.conf`. Declarative, versioned, content-addressed, signed if you sign
  the image. This is where bootc wants everything.
- *Machine configuration* — `bootc install --karg` ("These become machine-local state"), `/etc`, and
  whatever installer wrote it. The guidance is to minimize it: "minimal machine-specific configuration
  should be injected at install time. Instead, most configuration should happen at runtime — either at
  first boot or on every boot — using standard Linux mechanisms." DOCUMENTED, `bootc-install.md`.
- *Runtime configuration* — systemd, drop-in directories, `/etc`. Not bootc's concern.
- *Cluster configuration* — not applicable; bootc has no cluster concept.

**The declarative interface is deliberately tiny.** `bootc edit` "operates very similarly to `kubectl
apply`", and "Only changes to the `spec` section are honored" — where the spec has exactly two fields,
`image` and `bootOrder`. DOCUMENTED, `bootc-edit(8)` and `host-v1.schema.json`. So the declarative
surface is "which image, and forward or back" — a defensible scope for a mechanism, and the reason a
bootc fleet needs something above it.

**Kernel arguments are the one genuinely awkward area** and the docs say so; the `kargs.d` mechanics,
the missing per-machine API and the architecture-naming trap are in §3.

*Idempotency and drift.* Image configuration is idempotent by construction — the same digest produces
the same `/usr`. `/etc` is not, and its drift is measurable and eliminable (§1). *Remote inspection:*
`bootc status --format=json` against the stable `org.containers.bootc/v1` schema. *Version control:*
the Containerfile, which is the point. *Signing:* the image signature covers image configuration
completely; nothing covers `/etc`. *Secrets:* no single opinionated mechanism (§3). *Change without
reboot:* anything in `/etc` or a running service, yes; anything in the image needs a rebuild and a
reboot, though `--soft-reboot` may make that cheaper. *Source of truth:* the registry, for everything
the image covers.

**The Fedora bootc project takes a notably softer line than upstream bootc**, and preserving that
distinction is the point of this profile. Its "generic vs building" page treats `/etc` injection as
legitimate design rather than fallback: "many operations that one might include in a container build
are also viable to inject as machine-local state into that directory (via kickstart, cloud-init,
Ignition, etc.)… for one specific site want to enable or disable one or more systemd units, or inject
an extra container image… Or, the organization may want to produce a 'final' image but allow their own
users to decide more dynamically whether or not to enable FIPS mode." And it commits: "It is supported
today to use this project to produce 'generic' images, and will continue to be into the future.
However, the primary focus is on providing tools to build custom derived images." DOCUMENTED,
[generic-vs-build.adoc](https://gitlab.com/fedora/bootc/docs/-/blob/main/modules/ROOT/pages/generic-vs-build.adoc).
It also carries a `dynamic-reconfiguration` page on using Ansible against bootc systems, and names the
`community.general.bootc_manage` module. DOCUMENTED, `management-generic.adoc`, `nav.adoc`.

### The vehicle (Fedora CoreOS)

**Ignition runs exactly once, in the initramfs, before userspace, and is a provisioning tool by explicit
design.** "Ignition runs only once during the first boot of the system (while in the initramfs).
Because Ignition runs so early in the boot process, it can re-partition disks, format filesystems,
create users, and write files before the userspace begins to boot." DOCUMENTED,
[producing-ign.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/producing-ign.adoc).
Upstream is blunter: "Ignition is designed to be used as a provisioning tool, not as a configuration
management tool. Ignition encourages immutable infrastructure, in which machine modification requires
that users discard the old node and re-provision the machine." And on why it is not a scripting
language: "Ignition configs do not allow users to provide arbitrary logic (including scripts for
Ignition to run)… Any further customization must use systemd services, created by Ignition." And,
memorably: "Ignition configs were designed to be human readable, but difficult to write, to discourage
users from attempting to write configs by hand." DOCUMENTED,
[Ignition rationale](https://coreos.github.io/ignition/rationale/).

**It fails closed**, which is the right property for unattended provisioning: "Ignition produces the
machine specified or no machine at all… If for any reason Ignition cannot deliver the exact machine
that the config asked for, Ignition prevents the machine from booting successfully." DOCUMENTED.

**The documented remedy for a forgotten setting is to redeploy, not to reapply**: "Try to plan your
configuration with the full set of customization details before provisioning a Fedora CoreOS instance.
But don't worry if you forgot something as you can fix the configuration and re-deploy the instance
from a fresh image." DOCUMENTED, `producing-ign.adoc`. There is no reconciliation loop, no drift
correction and no second run.

**What the language covers**, from the Butane `fcos` 1.7.0 spec: `ignition` (config merge/replace,
timeouts, `security.tls.certificate_authorities`, proxy), `storage` (disks→partitions, `raid`,
`filesystems`, `files`, `directories`, `links`, `luks`, and `trees` for embedding local directory
trees), `systemd.units` with dropins/mask/enabled, `passwd` users and groups (`should_exist: false`
deletes), `kernel_arguments` (`should_exist` / `should_not_exist`), `boot_device` (`layout`, `luks`
with tang/tpm2/threshold/cex, `mirror.devices`), and `grub.users`. Filesystem formats accepted: `ext4,
btrfs, xfs, vfat, swap, or none`. **There is no `containers` section in any stable Butane variant** —
containers are configured via `systemd.units` running podman or by writing Quadlet files into
`/etc/containers/systemd` with `storage.files`; a `systemd.quadlets` section exists only in
`1.8.0-experimental`. DOCUMENTED, [Butane specs](https://coreos.github.io/butane/specs/),
[running-containers.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/running-containers.adoc).

**Config layering is documented at two levels.** Operator-side: `ignition.config.merge[]` and
`ignition.config.replace`, with merge rules — "child overrides parent", most lists deduplicated by a
unique-identifying field, "Files, Directories, and Links are deduplicated across each other", "Configs
are merged in a depth first traversal". Distributor-side: Ignition searches `/run/ignition` →
`/etc/ignition` → `/usr/lib/ignition` for `user.ign` and `base.d/` fragments, first-directory-wins for
the former, all-directories-merged for the latter. DOCUMENTED,
[remote-ign.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/remote-ign.adoc),
[Ignition operator notes](https://coreos.github.io/ignition/operator-notes/).

**Two structural changes landed recently and matter.** Butane merged into Ignition — "Butane 0.29.0 is
the last release from this standalone repository" — and, as of Ignition 2.27.0 (2026-08-26), Ignition
"Accept[s] Butane YAML configs in addition to Ignition JSON, with automatic transpilation at boot".
DOCUMENTED, [Butane release notes](https://coreos.github.io/butane/release-notes/),
[Ignition release notes](https://coreos.github.io/ignition/release-notes/). That makes the FAQ's
statement that Butane YAML "is never directly processed by FCOS instances" **stale upstream** —
recorded as an observation about that sentence, not a contradiction of anything else. 2.27.0 also adds
config loading from a labelled device via `ignition.config.device` + `ignition.config.path`.

*Declarative vs imperative:* declarative for one execution and never reconciled — declarative
*provisioning* rather than declarative *management*. *Idempotency:* idempotent within its single run,
which is never repeated, so the property does not do its usual work. *Drift:* unbounded in `/etc` and
`/var` after first boot; an exhaustive grep of the documentation for `idempot|drift` returns **zero
hits**, so there is no drift or reconciliation story at all. OBSERVED (absence). *Remote inspection:*
`rpm-ostree status`, journald, and Zincati's Prometheus-format metrics. *Version control:* the Butane
file, a real reviewable artifact. *Signing:* **there is none** — verification is a content hash plus
TLS (§10). *Secrets:* the documented advice is not to (§10). *Change without reboot:* `/etc` edits and
service restarts yes; kernel arguments and layered packages no. *Source of truth:* the Butane config at
provisioning time, and then nothing — the honest answer and the main cost of the model.

**Post-first-boot configuration management is undocumented.** A grep across all Fedora CoreOS
documentation pages for `ansible` returns **zero hits**; there is no page on Ansible, Puppet, Chef or
Salt. The idiom the docs actually teach is a systemd oneshot unit written by Ignition, guarded by
`ConditionPathExists=!/var/lib/%N.stamp`. The gap is acknowledged upstream: the bootc-integration
roadmap lists "Using Ansible. Make sure we have good docs for this" as an open item. OBSERVED
(absence) / DOCUMENTED (the acknowledgement),
[fedora-coreos-tracker#1726](https://github.com/coreos/fedora-coreos-tracker/issues/1726).

**Platform identity is a first-class configuration input**, and is how one image serves 21 platforms:
every image boots with `ignition.platform.id` on the kernel command line, consumed by Ignition and
Afterburn and usable in systemd units via `ConditionKernelCommandLine=`. DOCUMENTED,
[platforms.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/platforms.adoc).

### The honest comparison

Each is right for its own premise. If the image is fixed, a rich first-boot language is the only place
machine-specific decisions can go, and Ignition's initramfs execution makes it powerful enough to
repartition and encrypt. If the image is yours, most of that language is unnecessary, because the
decisions moved to build time where they are versioned and testable. The cost on the Fedora CoreOS side
is a one-shot model with no reconciliation and no second chance. The cost on the bootc side is that
every organization must choose and operate its own first-boot and day-2 tooling, with almost no
guidance upstream — Fedora bootc supplies more (kickstart, Ignition, cloud-init and Ansible are all
named as viable) but standardizes on none.

---

## 7. Kubernetes coupling

### The mechanism (bootc)

**bootc is unrelated to Kubernetes.** It does not require it, ship it, manage it, or depend on it. The
only Kubernetes-shaped thing is a design borrowing: `bootc status` outputs "a YAML-formatted object
using a schema intended to match a Kubernetes resource", and `bootc edit` "operates very similarly to
`kubectl apply`". DOCUMENTED, man pages. That is API ergonomics, not coupling.

**The project states the boundary it will not cross**, which settles the question: "Just as `podman`
does not depend on a Kubernetes API server, `bootc` will also not depend on one. However, there are
also plans for `bootc` to also understand Kubernetes API types. See configmap/secret support for
example. Perhaps in the future we may actually support some kind of `Pod` analogue for representing the
host state. Or we may define a CRD which can be used inside and outside of Kubernetes." DOCUMENTED,
[relationships.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/relationships.md). The roadmap
adds direction: "**Kubernetes Integration** — Develop native Kubernetes integrations to enable
cluster-wide OS updates, node lifecycle management, and fleet-wide rollout and rollback strategies."
DOCUMENTED, [ROADMAP.md](https://github.com/bootc-dev/bootc/blob/main/ROADMAP.md).

**An upstream Kubernetes operator now exists, in early development.**
[bootc-dev/bootc-operator](https://github.com/bootc-dev/bootc-operator), Apache-2.0, created
2026-03-18, last pushed 2026-09-15, **zero releases cut**, carrying its own warning: "This project is
in early development and not yet fully functional. APIs may change." Design: a controller Deployment
that "watches `BootcNodePool` resources, resolves image digests, manages pool membership, and drives
the rollout state machine (cordon, drain, reboot slot management)" plus a **privileged DaemonSet** that
"executes bootc commands on the host", communicating only through `BootcNode` resources. API
`node.bootc.dev/v1alpha1`, `BootcNodePool` with `spec.nodeSelector`, `spec.image.ref` (a digest today;
"Tags will also be supported"), `spec.rollout.paused` and status counters. It claims distribution
independence: "Works with any bootc-based OS image, not tied to any Kubernetes distribution."
DOCUMENTED / OBSERVED, `gh api repos/bootc-dev/bootc-operator`. The organization also carries
`bootc-dev/bink`, "Bootc in Kubernetes, tool for creating bootc kubernetes clusters".

**This extends the Pulse baseline**, which recorded Kubernetes management as "none; stated as a roadmap
goal". The accurate position is: no dependency, no shipped integration in bootc itself, and an
early-development operator in the same organization with no release. Its README positions it against
the alternatives: "Flightctl … shares similar functionality around rollouts but operates outside the
Kubernetes operator pattern" and "The MCO manages bootc hosts (such as RHEL CoreOS) on OpenShift. It is
powerful but tied to OpenShift." **UNKNOWN**: production use and release timeline.

*Which system owns machine lifecycle?* Whatever the operator puts above bootc — "a low-level generic
tool that can be driven by multiple higher level management tooling". DOCUMENTED,
`management-generic.adoc`.

**Non-Kubernetes workloads are fully in scope**, evidenced by the base image's content set (§3) and by
the `generic-vs-build` page's own examples of a "specific" image: "Run a Postgres instance in a specific
cloud", "Control software for a drone", "Be a graphical kiosk at a shopping mall". DOCUMENTED. A
hypervisor host, storage appliance, GPU node or ordinary Linux service are equally natural targets,
because nothing in the mechanism assumes a workload model.

### The vehicle (Fedora CoreOS)

**Kubernetes is optional, not included, and not life-cycled with the OS.** "Yes. However, Fedora CoreOS
does not include a specific container orchestrator (or version of Kubernetes) by default." What ships
is "Docker and podman by default", with "Based on community engagement and support this list could
change over time" — and a warning: "Running containers via `docker` and `podman` at the same time can
cause issues and unexpected behavior. We highly recommend against trying to use them both at the same
time." DOCUMENTED,
[faq.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/faq.adoc).

Its self-description places it deliberately: "designed for clusters but also operable standalone,
optimized for Kubernetes but also great without it". "Optimized for" means the update agent has
cluster-shaped affordances — FleetLock exists so a cluster can serialize reboots — not that Kubernetes
is assumed.

**The downstream relationships need stating precisely.** "Fedora CoreOS is a freely available,
community distribution that is the upstream basis for RHEL CoreOS. While Fedora CoreOS embraces a
variety of containerized use cases, RHEL CoreOS provides a focused OS for OpenShift, released and
life-cycled in tandem with the platform." DOCUMENTED, `faq.adoc`. So the *Kubernetes-coupled* member of
this family is a different, downstream product. The Machine Config Operator belongs to OpenShift and
OKD — it "extends [the operator-focused platform] to the operating system itself, managing updates and
configuration changes to essentially everything between the kernel and kubelet", uses Ignition as its
configuration format and rpm-ostree for updates, and **replaces Zincati on those nodes**. DOCUMENTED,
[machine-config-operator docs](https://github.com/openshift/machine-config-operator/blob/master/docs/README.md).
And OKD itself moved off Fedora CoreOS ([OKD SCOS migration FAQ](https://okd.io/docs/project/scos-migration-faq/)):
"OKD 4.20 marks a significant platform update, transitioning the
underlying operating system from Fedora CoreOS (FCOS) to CentOS Stream 10", corroborated by all 100
most recent OKD releases back to 2025-08 being tagged `*-okd-scos.*`. DOCUMENTED / OBSERVED. **Two
primary sources conflict**: OKD's own architecture pages and README still say Fedora CoreOS. Recorded as
a conflict rather than resolved; "OKD uses FCOS" is no longer safe to assert without qualification.

*Can OS and Kubernetes upgrade independently?* Yes, completely — nothing binds them and there is no
Kubernetes version matrix to satisfy. *Can Kubernetes manage the OS?* Not in Fedora CoreOS itself; a
Kubernetes-backed FleetLock lock manager can gate *reboots*, a narrow and useful form of awareness, but
there is no desired-state controller. DOCUMENTED.

### Position on the spectrum

The framework asks for a placement on *Kubernetes appliance ↔ Kubernetes-oriented OS ↔ general
immutable infrastructure substrate*, treating no position as superior.

**bootc sits off the scale, past the substrate end**, because it is not an OS but a mechanism for making
*any* Linux system image-based — its adopters include atomic desktops, about as far from a Kubernetes
appliance as the category goes. **Fedora CoreOS sits at "general immutable infrastructure substrate
with Kubernetes-aware update affordances"**, nearer the Kubernetes-oriented end than a plain server
distribution because of FleetLock and its cluster framing, but unambiguously not an appliance.

Neither position is a verdict. The cost of bootc's is that a Kubernetes operator gets no node-lifecycle
integration out of the box. The cost of Fedora CoreOS's is the same one layer up: reboot coordination
and phased rollout, but no drain-before-reboot and no Ready-gate, so a node that boots cleanly and
never joins the cluster is not a case the OS knows about.
---

## 8. Hardware and platform support

### The mechanism (bootc)

**bootc has no hardware support of its own** — no kernel, firmware, drivers or platform images. What a
bootc system supports is what its base image's kernel and firmware packages support. This is the same
reasoning by which the Pulse baseline marked hardware not-applicable for the mechanism.

**What the mechanism determines is how you add support: rebuild the image.** A driver, firmware blob,
out-of-tree module or replacement kernel is a package install or a `COPY`, and the result is a new
digest the fleet moves to through the ordinary upgrade path. The one-kernel invariant applies, and the
initramfs must be regenerated at build time with dracut told the kernel version explicitly, "because
its default targets the *running* kernel, which is not what a build should use". DOCUMENTED,
`initramfs.md`. **Guidance for replacing the kernel package is undocumented (§3). UNKNOWN**, and a
notable gap for hardware needing a vendor kernel.

**Architecture support follows the base image**: the Fedora bootc base images publish x86_64, aarch64,
ppc64le and s390x for every tag 41–46 plus rawhide; **no riscv64**, and a grep of the bootc repository
for `riscv` returns only rows from an imported copy of the Discoverable Partitions Spec. OBSERVED,
Quay.io API and repository search, 2026-09-16. bootc itself carries architecture-specific behaviour in
a few documented places: `zipl` on s390x, `--bootloader=none` unsupported there, architecture-specific
boot partitions in `install to-disk` ("BIOS boot for x86_64, PReP for ppc64le"), and Rust-style
architecture names in `kargs.d` (§3). DOCUMENTED, `bootloaders.md`, `bootc-install-to-disk(8)`.

**Platform support follows the disk-image builder, not bootc**, which produces no AMI, qcow2 or OVA and
states that as a non-goal: "it is not a goal to use `bootc` to produce these 'traditional' disk
images." The osbuild image types are listed in §3. DOCUMENTED. **There is no PXE or netboot story in
bootc's own documentation — the strings do not appear — and it is recorded as UNKNOWN rather than as a
stated non-goal, because the docs say neither.**

**TPM support is narrow and de-emphasized.** TPM appears only in the LUKS context, and the project
steers away from owning it: `--block-setup tpm2-luks` exists but "We don't recommend this for new
deployments", and the encryption page's heading is "Recommendation: handle root filesystem encryption
independently of bootc — If you want an encrypted root, set that up independently of bootc, and then
point `bootc install to-filesystem` at the resulting mounted filesystem… that setup is owned by whoever
builds and maintains the image or installer, not by bootc." DOCUMENTED, `bootc-install.md`,
[filesystem-encryption.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/filesystem-encryption.md).
**Measured boot, PCR policy and remote attestation are absent from bootc's documentation entirely.
UNKNOWN.**

### The vehicle (Fedora CoreOS)

**The widest platform matrix in this study, verifiable rather than claimed.** From the stable stream
metadata on 2026-09-16:

- **x86_64, 21 platform artifact sets**: `aliyun`, `applehv`, `aws`, `azure`, `azurestack`,
  `digitalocean`, `exoscale`, `gcp`, `hetzner`, `hyperv`, `ibmcloud`, `kubevirt`, `metal`, `nutanix`,
  `openstack`, `oraclecloud`, `proxmoxve`, `qemu`, `virtualbox`, `vmware`, `vultr`
- **aarch64, 10**: `applehv`, `aws`, `azure`, `gcp`, `hetzner`, `hyperv`, `metal`, `openstack`,
  `oraclecloud`, `qemu`
- **s390x, 5**: `ibmcloud`, `kubevirt`, `metal`, `openstack`, `qemu`
- **ppc64le, 4**: `metal`, `openstack`, `powervs`, `qemu`

OBSERVED, `builds.coreos.fedoraproject.org/streams/stable.json`. The `metal` entry carries `raw.xz`,
`4k.raw.xz`, `iso` (the live ISO) and `pxe` (kernel, initramfs, rootfs), so **live ISO and PXE are
first-class published release artifacts**. The `images` block carries per-region AWS AMIs plus GCP and
KubeVirt references.

**A documentation-currency gap, confirmed independently.** The Supported Platforms page omits `ppc64le`
entirely — it has shipped stable artifacts since 2021 — lists `libvirt`, which is not a stream artifact
key, omits six of aarch64's ten and s390x's `kubevirt`, and cross-references a non-existent page. The
live stream metadata is authoritative. OBSERVED, `platforms.adoc` versus the stream JSON.

**riscv64 is not released**, and the tracker explains why: even when the technical gaps close, an
official stream needs official builds in the distribution's build system first — "we won't be able to
offer an official stream until there are official builds in koji." DOCUMENTED,
[fedora-coreos-tracker#1931](https://github.com/coreos/fedora-coreos-tracker/issues/1931).

**Specialized hardware, per item:**

- **NVIDIA GPUs, Jetson, NPUs.** **No supported path is documented in Fedora CoreOS, and the project
  debated this and landed on "use Fedora bootc" deliberately.** The OS-extensions page names drivers as
  the legitimate layering case then redirects to Fedora bootc; a maintained Fedora bootc NVIDIA example
  exists at [gitlab.com/fedora/bootc/examples/nvidia](https://gitlab.com/fedora/bootc/examples/-/tree/main/nvidia),
  four lines of `dnf -y module install nvidia-driver` on a CentOS bootc base; and a proposal to adopt a
  community NVIDIA image into the CoreOS organization
  ([tracker#2047](https://github.com/coreos/fedora-coreos-tracker/issues/2047), closed 2025-10-27) drew
  "Why not directly derive from {fedora,centos} bootc where this type of thing is explicitly supported
  and encouraged?" and resolved with "We updated the project to rebase on fedora-bootc by default."
  **The Secure Boot consequence is the substantive constraint, stated by a maintainer**: "The main issue
  is that those kernel modules are not built in Fedora infra so they are not signed by Fedora. Thus to
  load them you have to either disable Secure Boot or sign them. If we sign them then we need to manage
  a signing key (as it can most probably not be the Fedora one) and document how to enroll the key in
  MOK." DOCUMENTED. So GPU support is achievable via the bootc-derivation path with a maintained
  example, at the cost of either Secure Boot or a MOK-enrolment programme. **UNKNOWN**: where that
  community image landed after the move — `github.com/coreos/coreos-nvidia` returns 404.
- **Wi-Fi.** Documented, and candidly a layering story: "The primary use for Fedora CoreOS has been
  driving server hardware… adding Wi-Fi enablement to Fedora CoreOS by default would require many large
  firmware binaries to be installed for a non-standard use, which isn't ideal", with a table of 14
  candidate firmware packages plus `NetworkManager-wifi`, installed by a stamped systemd unit, then a
  reboot. DOCUMENTED,
  [sysconfig-enabling-wifi.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/sysconfig-enabling-wifi.adoc).
- **Cellular / WWAN.** A grep across all documentation pages for `wwan|modemmanager|cellular|lte|5g`
  returns zero relevant hits. **UNKNOWN.** (Fedora bootc's `wifi/` example does install
  `NetworkManager-wwan`. DOCUMENTED, bootc side only.)
- **Unusual NICs, RAID controllers.** No enablement story and **no hardware compatibility list of any
  kind**; hardware enablement is whatever `linux-firmware` and the stock Fedora kernel carry, and
  firmware coverage regressions are handled as bugs rather than against a support matrix. OBSERVED
  (absence). **UNKNOWN** for hardware RAID HBAs.
- **Software RAID.** Documented with Butane examples, including boot-device mirroring where "you need
  to mirror all the default partitions (root, boot, EFI System Partition, and bootloader code)" and
  "On systems configured with boot device mirroring, there are independent EFI partitions on each
  constituent disk." DOCUMENTED, `storage.adoc`. LVM has no page, though the base image ships an
  `lvmdevices` allowlist and a migration unit (§13).
- **TPM.** Clevis-pinned LUKS with TPM2, and **PCR 7 only** — "Binding for PCR 8 (UEFI Boot Component
  used to track commands and kernel command line) is not supported as the kernel command line changes
  with every OS update." Platform gaps are tracked and open: TPM on AWS
  ([#1193](https://github.com/coreos/fedora-coreos-tracker/issues/1193)), Secure Boot on GCP
  ([#346](https://github.com/coreos/fedora-coreos-tracker/issues/346), open since 2020). DOCUMENTED /
  OBSERVED.
- **Raspberry Pi and SBCs.** The Pi 4 is documented using the generic aarch64 bare-metal artifact
  rather than a dedicated image, with two firmware paths and a required firmware update step. No
  dedicated SBC platform identifier, no Pi 5 page. DOCUMENTED, `provisioning-raspberry-pi4.adoc`.
- **Industrial PCs, edge appliances.** Nothing documented. **UNKNOWN.**
- **iSCSI boot.** Documented, including iBFT (`rd.iscsi.firmware=1`, `ip=ibft`), manual
  (`rd.iscsi.initiator=`, `netroot=iscsi:…`) and a fully diskless iPXE `sanboot` path — a genuinely
  capable answer for diskless datacenter hardware. DOCUMENTED, `bare-metal.adoc`.
- **4k-native disks.** Two metal images ship, 512b and 4k native, with the caveat that the `metal4k`
  image "does not have a BIOS boot partition because 4k native disks are only supported with UEFI."
  DOCUMENTED, `faq.adoc`.

### "If unsupported hardware appears tomorrow, can an organization add support itself?"

**bootc: yes, by the path you already use.** Add the package, rebuild, push, upgrade. The organization
owns the result — including its testing and the CVE lifecycle of any vendor blob added — with no
gatekeeper and no upstream request. The cost: a kernel change is a full rebuild, the initramfs
regeneration is a documented non-deterministic build step (§15), and replacing the kernel package is
undocumented.

**Fedora CoreOS: yes, but the supported path is narrow and the documentation points elsewhere.**
Layering the driver works mechanically and is discouraged in the project's own words; there is no
kernel-module or GPU documentation; the FAQ's answer to nontrivial base-OS changes is Fedora bootc. So
the honest answer is "yes, by leaving" — not a criticism of the design, since a fixed, heavily tested
image cannot also be an arbitrary hardware platform, but an organization with unusual hardware should
read that FAQ answer as the design telling them which product they want.

---

## 9. Security and chain of trust

Tracing *firmware → bootloader → kernel → initrd → root filesystem → extensions → configuration →
workload*, distinguishing tamper prevention, tamper detection and attestation.

### The mechanism (bootc)

**Firmware → bootloader.** bootc installs a bootloader at install time via bootupd or systemd-boot, and
for systemd-boot supports key enrolment: "bootc can let `systemd-boot` handle enrollment of Secure Boot
keys by putting signed EFI signature lists in `/usr/lib/bootc/install/secureboot-keys` which will copy
over into `ESP/loader/keys` after bootloader installation." DOCUMENTED, `bootc-install(8)`. Whether the
shipped shim chains to a CA already in firmware depends entirely on the base image. **The bootloader is
not updated after install** (canonical in §4), which is a standing tamper-surface and CVE-lifecycle
question the operator owns.

**Bootloader → kernel → initrd.** Two modes: traditional, where `vmlinuz` and `initramfs.img` come from
the image with a BLS entry per deployment and nothing verifies them beyond firmware Secure Boot; and
sealed UKI, where kernel, initramfs and command line are one signed EFI binary. DOCUMENTED,
`bootc-images.md`, `experimental-composefs.md`.

**Kernel → root filesystem: the sealed-UKI chain is the strongest integrity story bootc documents, and
it is experimental.** "A sealed image includes: 1. composefs digest: A SHA-512 hash of the entire root
filesystem, computed at build time; 2. Unified Kernel Image (UKI): a single EFI binary containing the
kernel, initramfs, and kernel command line with the composefs digest embedded; 3. Secure Boot
signature: The UKI is signed with your private key… At boot time, the composefs digest in the kernel
command line (e.g., `composefs=<sha512-hash>`) is verified against the mounted root filesystem. This
creates a chain of trust from firmware to userspace, ensuring the system will only boot if the root
filesystem matches exactly what was signed." DOCUMENTED, `experimental-composefs.md`.

The prerequisites are strict and are why this is not the default: a kernel and initramfs in
`/usr/lib/modules/<kver>/`, systemd-boot present and **bootupd absent**, no pre-built UKI, Secure Boot
in firmware, and **a filesystem with fsverity support (ext4 or btrfs) — excluding XFS**, the default
root filesystem type of the Fedora base images. `--allow-missing-verity` exists "for filesystems that
don't support it (e.g. XFS)" and makes the image unsealed. The build is a three-stage Containerfile
using `bootc container split-kernel-and-rootfs` and `bootc container ukify`, which wraps systemd's
`ukify` and forwards everything after `--` to it; `bootc container compute-composefs-digest` is the
lower-level primitive, "currently hidden from `--help` output". An external-signing workflow (build
unsigned, sign offline, inject) is documented but "planned for streamlining in future releases"
([bootc#1498](https://github.com/bootc-dev/bootc/issues/1498)). DOCUMENTED.

Two clarifications the page makes that are easy to get wrong: "packaging as a UKI is a boot convenience
here, not by itself a security boundary"; and on running sealed with Secure Boot disabled, "nothing
validates that root digest itself, meaning any locally running code can replace the UKI (e.g. after a
container breakout) and fully control the next boot."

**dm-verity is not used, and the choice is explained.** "One can think of composefs as effectively a way
to manage something like dm-verity, but using files… supporting multiple ones stored inside a standard
Linux filesystem. One thing this helps significantly with is dealing with the 'space management'
problems that dm-verity introduces (need for a partition to have unused empty space to grow, and also a
fixed-size ultimate capacity limit)." The signing side is unfinished: "At the current time, there is not
one single standardized approach for signing composefs images… bootc itself will not mandate one
mechanism currently. However, it is very likely that we will ship an optionally-enabled opinionated
mechanism that uses basic ed25519 signatures for example." DOCUMENTED,
[relationship-particles.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/relationship-particles.md).

**Artifact signatures: the canonical treatment of the most consequential default in this profile.**
bootc defers to `/etc/containers/policy.json`, and "bootc honors the default `/etc/containers/policy.json`
when fetching images. The upstream default at the time of this writing does not require signatures for
generic images. **It is not a vulnerability in bootc that signatures are not required by default.** It
is however a very good idea for bootc users to enable signatures for their images." DOCUMENTED,
`security.md`. **An unconfigured bootc system will deploy an unsigned image.** bootc's own control is a
meta-check, `--enforce-container-sigpolicy`, which "enforces that `containers-policy.json`… includes a
default policy which requires signatures", with an install-config equivalent defaulting to `false`; and
`bootc status` reports exactly three signature states per image — `ostreeRemote`, `containerPolicy`
("defer to the `containers-policy.json`, but we make a best effort to reject `default:
insecureAcceptAnything` policy") and `insecure` ("No signature verification will be performed").
DOCUMENTED, `bootc-switch(8)`, `host-v1.schema.json`. bootc also deliberately has no
`--tls-verify=false`: "`bootc` has no such option. Instead, you can globally configure the option… via
the `/etc/containers/registries.conf.d` configuration mechanism." DOCUMENTED,
`registries-and-offline.md`.

**Sigstore and cosign work but are inherited, not documented by bootc.** The words do not appear in
bootc's documentation; the capability is containers/image's `sigstoreSigned` policy requirement, which
supports key material, Fulcio-issued certificates and PKI, and needs `use-sigstore-attachments` enabled
per registry in `containers-registries.d`. DOCUMENTED (containers/image), INFERRED that bootc honours it
on the strength of "bootc honors the default `/etc/containers/policy.json`". **No bootc-specific
`policy.json` example exists anywhere in the tree — a real documentation gap for the single
highest-leverage security control the mechanism has.**

**SELinux.** Supported, with a documented labeling model: "bootc will load the file contexts from the
image (e.g. `/etc/selinux/policy`) and apply labels dynamically. This is the only mechanism that will
work today with a generic bootc-unaware build tooling." The build-time consequences (`chcon` vs
`semanage fcontext`) are in §3. `--disable-selinux` exists on all three install verbs. DOCUMENTED,
`bootc-images.md`, `bootc-install(8)`.

**bootc's own threat model, stated**: "bootc is a binary that is intended to be run with full
privileges. It does not expose a service (socket, HTTP endpoint) by default; that's the role of higher
level tooling. All inputs (CLI arguments, etc) are hence considered fully trusted by default."
DOCUMENTED, `security.md`. The whole security chapter is 42 lines, which is thin for a project at this
maturity — an observation, not a judgement. A separate
[SECURITY.md](https://github.com/bootc-dev/bootc/blob/main/SECURITY.md) defines private reporting via
GitHub Security Advisories; §17 covers what that process does and does not specify.

**Secret provisioning, key rotation and revocation.** No opinionated mechanism (§3, §6); rotation and
revocation for an operator-signed fleet are **UNKNOWN**. SBOM and provenance for the image are the
adopter's; for the tool, §15.

### The vehicle (Fedora CoreOS)

**Firmware → bootloader: the most operator-friendly Secure Boot position in this study, and it comes
from being Fedora.** The x86_64 disk image is GPT with a protective MBR and "supports booting via both
BIOS and UEFI (including Secure Boot)"; the EFI-SYSTEM partition "Contains EFI GRUB image and Secure
Boot shim"; `shim-x64` ships. Because Fedora's shim is signed through a certificate authority already
in firmware, **no key enrolment is required on stock hardware**. DOCUMENTED, `storage.adoc`,
[Fedora Secure Boot](https://fedoraproject.org/wiki/Features/SecureBoot). There is **no dedicated
Secure Boot documentation page**, only incidental mentions — a gap on arguably its strongest security
property. Hyper-V Gen2 needs the Microsoft UEFI CA template selected manually; VMware images set
`vmware-secure-boot: true`. DOCUMENTED.

**Bootloader updates are automatic** (canonical in §4) — the clearest operational divergence from the
mechanism.

**A GRUB password is supported** via `grub.users[].password_hash` from `grub2-mkpasswd-pbkdf2`, "to
prevent unauthorized users from accessing the GRUB command line, modifying kernel command-line
arguments, or booting non-default OSTree deployments". DOCUMENTED, `grub-password.adoc`. That closes a
real local-attack path the documented rollback procedure (hold Shift, pick an entry) otherwise leaves
open — a trade-off to make deliberately.

**Root filesystem integrity.** Composefs by default since Fedora 41, giving a genuinely read-only root,
with the project's own framing that it is "a first step towards a full verification of filesystem
integrity, even at runtime". No fsverity enforcement, no dm-verity, no sealed UKI; signature-backed
runtime integrity open since 2022
([#1252](https://github.com/coreos/fedora-coreos-tracker/issues/1252)). So: tamper prevention against a
running attacker with root, no; tamper detection at runtime, no; tamper prevention against offline
modification of the OS tree, partial via composefs and the read-only mount. DOCUMENTED.

**Artifact verification is stricter by default than upstream bootc's, and the shipped policy is
specific.** Fedora CoreOS bind-mounts its own `policy.json` over `/etc/containers/policy.json` **for
`rpm-ostreed` only**: `{"default": [{"type": "reject"}]}`, with `insecureAcceptAnything` for
`docker-daemon`, `containers-storage`, `oci` and `oci-archive`, and for the `docker` transport's
**empty-prefix scope**, plus a `signedBy` GPGKeys rule scoped to `quay.io/fedora/fedora-coreos` naming
the Fedora 44, 45 and 46 primary keys. The signature lookaside is
`https://builds.coreos.fedoraproject.org/prod/signatures/oci`. DOCUMENTED (source),
`overlay.d/17fcos-container-signing/` in
[fedora-coreos-config](https://github.com/coreos/fedora-coreos-config). **Two precision points a summary
would lose:** the strictness applies to the OS update pull, not to a user's `podman pull`, whose
`docker`-transport default here is `insecureAcceptAnything`; and the bind mount has a documented opt-out
(`ln -s /dev/null` over the `rpm-ostreed.service` drop-in). An in-flight migration unit
([#2029](https://github.com/coreos/fedora-coreos-tracker/issues/2029)) moves existing nodes onto the
signed OCI reference, with a failure MOTD warning "The system will likely fail to continue updating in
the near future"; nodes with Zincati disabled or a non-default ostree remote are not migrated.
DOCUMENTED (source). The disappearance of ostree commit signatures that made this necessary is in §15.

**Key rotation is a solved and documented problem here**, through update barriers (§4, §18) — more than
most systems in this study can say: a machine cannot skip past a signing-key change, because the graph
will not let it.

**Disk encryption.** LUKS2, opt-in, with Clevis pins for TPM2, Tang, Shamir threshold combinations, and
an IBM CEX pin on s390x; root reprovisioning to LUKS needs at least 4 GiB of RAM. The docs carry an
explicit threat-model caution: "TPM2 pinning just binds encryption to the physical machine in use. Make
sure to understand its threat model before choosing between TPM2 and Tang pinning." PCR 7 supported,
PCR 8 documented as unsupported (§8). Ignition generates a key-file at `/etc/luks/<deviceName>` if none
is specified and writes `/etc/crypttab`. DOCUMENTED, `storage.adoc`,
[Ignition operator notes](https://coreos.github.io/ignition/operator-notes/#luks).

**Mandatory access control.** "Fedora CoreOS comes with SELinux enabled in enforcing mode" and "**We do
not support disabling SELinux in Fedora CoreOS.**" Policy booleans and SELinux modules are supported,
but "we do not include `semanage` and there is no sugar in Butane or direct support in Ignition for
doing those operations"
([#701](https://github.com/coreos/fedora-coreos-tracker/issues/701)). The docs recommend
per-application permissive CIL modules over global permissive mode, and document drift detection and
repair for the policy itself: `ostree admin config-diff | grep -E 'selinux/.*/policy'`, then `rsync
--archive --links --delete /usr/etc/selinux/ /etc/selinux/` and `semodule -R` — the only documented
`/etc` repair procedure found on either side. DOCUMENTED,
[selinux.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/selinux.adoc).

**Audit.** auditd ships and has since the first Fedora 39-based release, and "it cannot be stopped or
restarted via `systemctl stop auditd` or `systemctl restart auditd` for compliance reasons" —
`auditctl --signal` is the supported control. DOCUMENTED,
[audit.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/audit.adoc).

**SSH posture.** "By default, a privileged user named `core` is created… but it is not configured with a
default password or SSH key", "Fedora CoreOS ships with no default passwords", and "By default, Fedora
CoreOS does not allow password authentication via SSH", enforced by a shipped
`/etc/ssh/sshd_config.d/40-disable-passwords.conf` that must sort before Fedora's password-enabling
drop-in. Keys resolve through an `AuthorizedKeysCommand` calling `/usr/libexec/ssh-key-dir`, reading
`~/.ssh/authorized_keys.d/` alphabetically — Ignition writes `ignition`, Afterburn writes `afterburn` —
so the two sources never collide. Default groups are `root, adm, wheel, sudo, systemd-journal, docker`.
DOCUMENTED,
[authentication.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/authentication.adoc).

**Measured boot and attestation: absent.** No documentation, and the package set contains no keylime, no
IMA tooling, no systemd-pcrlock, no fapolicyd, no AIDE and no OpenSCAP. `tpm2-tools`, `tpm2-tss` and
`clevis-pin-tpm2` ship; the only documented TPM use is Clevis LUKS unlock pinned to PCR 7. DOCUMENTED
(absence, from the shipped package manifest and an exhaustive documentation grep). **UNKNOWN** whether
any is planned.

**FIPS: not supported and not documented.**
[#302](https://github.com/coreos/fedora-coreos-tracker/issues/302) has been open since 2019-10-28,
last updated 2026-04-28; its opening states "When booting with `fips=1` as a karg, boot will fail",
and a maintainer is candid about the value: "adding FIPS support to FCOS does not make FCOS (or more
precisely the openssl build inside) FIPS certified. So this is mostly useless (from the conformance
point of view) as it's unlikely that Fedora's openssl build will ever be FIPS certified." A grep for
`fips` across all documentation pages returns zero hits. DOCUMENTED / OBSERVED (absence). **By
contrast, Fedora bootc ships a dedicated `fips-crypto-policies` page and a `fips/` example** (§3) — a
mechanism-versus-vehicle divergence on a requirement that decides procurement in regulated
environments.

**Corporate CA certificates: undocumented on both sides for the host trust store.** Fedora CoreOS
documents `--ignition-ca` and `ignition.security.tls.certificate_authorities`, and is explicit that the
latter is Ignition-scoped: "The certificate authorities listed here are not automatically added to the
host filesystem. They are solely used by Ignition itself when fetching over `https`. If you'd like to
also install them on the host filesystem, include them as usual under the `storage.files` array." A grep
for `ca-trust|update-ca-trust|pki/ca-trust` across all documentation pages returns zero hits.
DOCUMENTED (the Ignition scope), **UNKNOWN** (the host trust store as a supported workflow). For bootc a
corporate CA is an ordinary `COPY` plus `update-ca-trust` at build time — mechanically obvious and also
undocumented.

### Tamper prevention, tamper detection, attestation — summarized

- **bootc, default:** prevention limited to a read-only mount; detection via fsverity on individual
  objects where the filesystem supports it, with nothing to verify the composefs image against; no
  attestation. Artifact signature verification is *off* unless configured.
- **bootc, sealed UKI:** prevention enforced by firmware through a signed UKI carrying the root digest;
  detection via fsverity `EIO`; still no attestation. Experimental, XFS-incompatible, external signing
  unstreamlined.
- **Fedora CoreOS:** prevention via read-only composefs root, enforcing SELinux, automatic bootloader
  updates and Secure Boot on stock firmware; detection essentially absent at runtime; no attestation.
  Artifact signature verification is *on* by default, scoped to Fedora's keys, with documented rotation.

---

## 10. Provisioning and zero-touch deployment

### The mechanism (bootc)

**bootc provides install primitives, not a provisioning story, and the model is unusual.** "The `bootc
install` command bridges the two worlds of a standard, runnable OCI image and a bootable system by
running tooling logic embedded in the container image to create the filesystem and bootloader setup
dynamically. This requires running the container via `--privileged`; it uses the running Linux kernel
on the host to write the file content from the running container image; not the kernel inside the
container." And: "The installation commands **MUST** be run **from** the container image that will be
installed… This means you are (currently) not able to install `bootc` to an existing system and install
your container image." The canonical invocation is `podman run --rm --privileged --pid=host --ipc=host
-v /var/lib/containers:/var/lib/containers -v /dev:/dev --security-opt label=type:unconfined_t <image>
bootc install to-disk /path/to/disk`, where `-v /var/lib/containers` "is required in order for the
container to access its own underlying image". DOCUMENTED,
[bootc-install.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/bootc-install.md).

**The self-sufficiency claim is the interesting part**: "nothing *else* (external) is required to
perform a basic installation to disk — the container image itself comes with a baseline self-sufficient
installer that sets things up ready to boot." The image is the installer; there is no separate
installer artifact to version, mirror or match.

Three verbs with documented roles:

- **`bootc install to-disk`** — writes a whole disk, using the Discoverable Partitions Specification
  since bootc 1.11: an architecture-appropriate boot partition, an ESP of at least 512 MiB on UEFI
  architectures, a separate `/boot` only under LUKS, root filling the rest, with `--filesystem
  xfs|ext4|btrfs` and the default taken from the image's `/usr/lib/bootc/install/*.toml`. The
  documentation demotes it: "**In general, the `to-disk` flow should be considered mainly a 'demo' for
  the `bootc install to-filesystem` flow, which can be used by 'external' installers today.**"
  DOCUMENTED, `bootc-install-to-disk(8)`, `bootc-install.md`.
- **`bootc install to-filesystem`** — the real integration point, used by Anaconda and osbuild, with a
  `--source-imgref` escape hatch so the caller need not be podman: "this allows users to use a different
  sandboxing tool (e.g. bubblewrap). This argument is mainly useful for 3rd-party tooling for building
  disk images from bootable containers." DOCUMENTED.
- **`bootc install to-existing-root`** — converts a running Linux system, and is honest about the
  damage: "`/boot` (and `/boot/efi`) partitions *will be reinitialized*… **Any data from `/etc` that you
  want to use in the new system must be manually copied from `/sysroot/etc` to `/etc` after rebooting…
  There is currently no automated mechanism for migrating this configuration data.**" A wrapper,
  `system-reinstall-bootc`, makes it interactive and adds a first-boot cleanup unit; its stated purpose
  is "a way to 'take over' cloud virtual machine images, effectively using them as an installer
  environment." DOCUMENTED.

**`--via-loopback` is the local-image path**: `truncate` a file, run the install container with
`--generic-image --via-loopback`, get a raw disk image. Root required, raw only, no qcow2 conversion.
DOCUMENTED.

**Install-time machine state is bounded**: `--karg` and `--karg-delete` ("These become machine-local
state"), `--root-ssh-authorized-keys` (described as "one small exception" to bootc having nothing to do
with users), `--stateroot`, `--disable-selinux`, `--block-setup tpm2-luks`. The guidance is to use as
little as possible: "minimal machine-specific configuration should be injected at install time."
DOCUMENTED. Provenance is recorded in `.bootc-aleph.json` (§1); Fedora CoreOS has an analogous
`.coreos-aleph-version.json`, and
[tracker#2187](https://github.com/coreos/fedora-coreos-tracker/issues/2187) proposes replacing it with
`.bootc-aleph.json` — another convergence datapoint.

**What bootc does not provide, verified by absence:** no ISO, no PXE or netboot (the words do not appear
in `docs/src/`), no cloud images, no first-boot configuration language, no device-identity or enrolment
mechanism, and no `bootc upgrade` inside a container ("There are only two supported operations in a
container environment today: `bootc status`… and `bootc container lint`"). DOCUMENTED for the container
limitation and the disk-image non-goal; **UNKNOWN** for PXE, neither offered nor declared out of scope.

### The vehicle (Fedora CoreOS)

**The philosophy is one sentence:** "Fedora CoreOS does not have a separate install disk. Instead, every
instance starts from a generic disk image which is customized on first boot via Ignition… By design,
there are no hard-coded default credentials." And for bare metal: "the installer only copies the raw
image to the target disk and injects the specified config into `/boot` for use on first boot."
DOCUMENTED,
[getting-started.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/getting-started.adoc),
`storage.adoc`.

**Three bare-metal paths, documented end to end:** the **live ISO** ("capable of bringing up a fully
functioning FCOS system purely from memory", bootable in BIOS or UEFI regardless of the installed
mode), then `coreos-installer install /dev/sda --ignition-url …`; **PXE/iPXE** with kernel, initramfs
and rootfs all mandatory and documented RAM requirements ("at least 2 GiB of RAM with the
`coreos.live.rootfs_url` kernel argument, and 4 GiB otherwise"); and **from a container on an existing
host** via `podman run --privileged … quay.io/coreos/coreos-installer:release install /dev/vdb -i
config.ign`. DOCUMENTED, `bare-metal.adoc`, `live-booting.adoc`.

**`coreos-installer iso customize` and `pxe customize` are the documented zero-touch mechanism**, and
their options answer most factory questions: `--dest-ignition`, `--live-ignition`, `--dest-device`
("booting that image will automatically install to the specified disk and reboot the system"),
`--network-keyfile` ("applied before Ignition runs, so this option is useful for specifying network
settings that are needed for Ignition to fetch remote resources"), `--ignition-ca`, `--dest-console`,
`--dest-karg-append/delete`, `--live-karg-append/replace/delete` ("useful if the machine will not boot
at all without certain kernel arguments, preventing use of the Ignition `kernel_arguments` directives"),
and `--pre-install` / `--post-install` scripts. Also `pxe ignition wrap`, `iso extract pxe`, `iso
extract minimal-iso --rootfs-url` for size-limited LOM virtual CDs, and `coreos.liveiso.fromram`.
DOCUMENTED,
[coreos-installer customizing-install](https://coreos.github.io/coreos-installer/customizing-install/).

**Heterogeneous hardware is addressed directly**, which few projects do: "If you have servers with
different types and/or number of hard drives, you must create a separate customized Ignition config for
each machine (or machine class). A good model is to have the common parts of the configuration factored
out into a separate Ignition configuration which can be merged into (via HTTP or inline) the per-machine
custom config." And the alternative: "instead of generating per-machine ISOs, you can have a
`--pre-install` script run a privileged container which inspects the target system and writes an
appropriate installer config to `/etc/coreos/installer.d`" — files there make the installer run
automatically on boot, evaluated alphabetically, with `coreos.inst` kernel arguments applied afterwards.
DOCUMENTED, `bare-metal.adoc`.

**Where the Ignition config comes from, per platform**, is a documented table rather than folklore: the
`ignition.config.url` kernel argument on bare metal (accepting `http`, `https`, `tftp`, `s3`, `arn:`
and `gs` schemes), or `ignition.config.device` plus `ignition.config.path` from a labelled disk;
instance user-data on every cloud; `opt/com.coreos/config` via fw_cfg on QEMU; guestinfo on VMware; a
guest property on VirtualBox; a KVP pool entry on Hyper-V with a ~1 KiB limit worked around by
concatenating `ignition.config.0`, `.1` and so on; HTTP over vsock port 1024 on applehv; the reader
device on z/VM; a bootfifo sysfs entry on NVIDIA BlueField. DOCUMENTED,
[Ignition supported platforms](https://coreos.github.io/ignition/supported-platforms/).

**The first-boot flag is a real mechanism.** GRUB checks for an `/ignition.firstboot` stamp file on the
boot filesystem and appends `ignition.firstboot` to the kernel command line; without it "Ignition
services do not run. Boot continues normally." With it the machine runs fetch-offline, fetch, kargs
(which **reboots and restarts from the top if kernel arguments changed**), disks, mount, files, then
`ignition-complete.target`, pivot, and `ignition-delete-config.service`. For live PXE and ISO the flag
must be passed manually: "the kernel command line must include the arguments `ignition.firstboot
ignition.platform.id=metal`." DOCUMENTED, Ignition boot-flow documentation, `live-reference.adoc`.

**Config integrity is hash-based and TLS-based, not signature-based.** `verification.hash` accepts
`sha256-` or `sha512-` prefixed digests on merged and replaced configs, file contents, CA bundles and
LUKS key files, "in the form `<type>-<value>`". The documentation warns: "Retrieving a remote Ignition
config via HTTP exposes the contents of the config to anyone monitoring network traffic. When using
HTTP, it is advisable to use the verification option." `coreos-installer install` enforces HTTPS-or-hash
by default, with `--insecure-ignition` documented as "Allow Ignition URL without HTTPS or hash".
Fetching has documented retry behaviour: exponential backoff from 100 ms doubling to 5 s, a 10 s
response-header timeout, and "Any HTTP response code less than 500 results in the request being
completed" — a 404 is final, a 503 is retried. DOCUMENTED, Ignition operator notes. **There is no
Ignition config signing.** UNKNOWN whether any is planned.

**Secrets in the provisioning path: the documented advice is not to.** "We do not recommend storing
secrets in Ignition configs. Many platforms allow unprivileged software in a VM (including software
running in a container) to retrieve the Ignition config from a networked metadata service or local
API." Documented mitigations: a firewalled child config pulled via `ignition.config.merge`, firewalling
the metadata service, and — on VirtualBox and VMware only — Ignition 2.14.0+ deleting the config from VM
metadata after provisioning. A grep for `sops` or `vault` across all documentation pages returns zero
hits. DOCUMENTED,
[Ignition operator notes](https://coreos.github.io/ignition/operator-notes/#secrets) / OBSERVED
(absence).

### "Can 5,000 identical devices leave a factory and independently establish secure identity and desired state on first boot?"

**Fedora CoreOS: yes for desired state, with a documented caveat for identity.** The `iso customize` /
`pxe customize` path plus `/etc/coreos/installer.d` plus a `--pre-install` inspection script is a
complete, documented zero-touch flow that handles heterogeneous hardware, with desired state as a
hash-verified Ignition config fetched over HTTPS. **What is not documented is per-device identity**:
no enrolment protocol, no TPM-bound identity, no attestation. The documented identity primitives are
the Ignition config itself, the per-machine ISO, and the `--pre-install` inspection script. For 5,000
devices needing *individually distinguishable* secure identity, the OS does not supply it. DOCUMENTED
for the flow, **UNKNOWN** for device identity.

**bootc: the question does not apply to the mechanism.** For a bootc-based *system* the answer is
whatever the base-image project and installer provide — Anaconda plus kickstart, osbuild output
consumed by ordinary provisioning, or `bcvk`/libvirt locally. The fleet-management answer, Flight
Control, does have a device enrolment concept (§11). Air-gapped provisioning is where the mechanism is
unusually strong (§22).

---

## 11. Fleet lifecycle

The framework requires separating the open-source OS, open-source companion projects and commercial
products — especially important here, because the commercially supported systems in this family are
separate products.

### In the open-source project — bootc

**Deliberately minimal, and stated as such.** "The upstream bootc project provides a low-level generic
tool that can be driven by multiple higher level management tooling", and of the shipped default: "By
default, there is a simplistic automatic update timer enabled. At any nontrivial scale, it is intended
that this is replaced with something more sophisticated that has knowledge of things like rollouts,
checking for application status, etc." DOCUMENTED, `management-generic.adoc`.

**The shipped timer, read from the unit rather than the prose, because they disagree.**
`bootc-fetch-apply-updates.timer` is `OnBootSec=1h`, `OnUnitInactiveSec=8h`, `RandomizedDelaySec=2h`,
gated on `ConditionPathExists=/run/ostree-booted`, with no `OnCalendar=`; the service is a single
`ExecStart=/usr/bin/bootc upgrade --apply --quiet`. In-file comments name the intent: the interval is
"relatively arbitrary and obviously expected to be overridden/changed", and the randomized delay exists
because "When deploying a large number of systems, it may be beneficial to increase this value to help
with load on the registry." OBSERVED,
[systemd/bootc-fetch-apply-updates.timer](https://github.com/bootc-dev/bootc/blob/main/systemd/bootc-fetch-apply-updates.timer).
**The man page's claim that the timer is "enabled for daily updates" does not match the unit** — a
documentation-currency observation that matters, because eight hours plus up to two of jitter is a
different fleet-load profile from daily. Upstream ships the unit without enabling it ("available in
upstream for operating systems and distributions to enable"); Fedora/CentOS bootc images enable it.
DOCUMENTED. `RandomizedDelaySec` is registry-load jitter, not a rollout strategy.

What bootc contributes to a fleet: staged upgrade with separate check, download and apply steps (§4); a
stable, schemad status API plus a change-notification path unit (§1); a declarative two-field spec
drivable by `bootc edit --filename`; rollback by bootloader reordering with a journal `MESSAGE_ID` for
detection (§5); offline update from an OCI directory (§22); install provenance in `.bootc-aleph.json`;
and `bootc switch` to a pinned digest, framed by the man page as a blue/green primitive: "use a
management agent to invoke `bootc switch` (or declaratively via `bootc edit`) to implement e.g.
blue/green deployments, where some hosts are rolled onto a new image independently of others."

**Absent:** inventory, grouping, topology-aware rollout, health gates, automatic rollback, concurrency
limits, drain integration, audit trail, remote reset. None exists and none is claimed; phased rollout
appears in the roadmap as direction, not feature. DOCUMENTED, `ROADMAP.md`.

### In the open-source project — Fedora CoreOS

**Unusually capable for a community project, and the clearest case where the vehicle is far ahead of the
mechanism.** Shipped in the node agent, not a product:

- **Automatic updates on by default**, with `immediate` as the shipped strategy: "By default, the
  `immediate` strategy is used in order to proactively keep machines up-to-date."
- **Phased rollout** orchestrated server-side by the Cincinnati graph, with **per-node wariness** as a
  first-boot config file; the documented default is notable: "The default and recommended configuration
  does not set any static wariness value on Zincati side, leaving rollout decisions to Cincinnati
  backend."
- **Weekly maintenance windows** via the `periodic` strategy.
- **Cluster-wide reboot coordination** via FleetLock — **client side only**. Zincati describes it as "a
  simple HTTP-based protocol modeling a distributed counting semaphore with recursive locking" and is
  explicit that it "does not mandate any specific lock-manager or database", naming three backends.
  Checked on 2026-09-16: **[poseidon/fleetlock](https://github.com/poseidon/fleetlock)** (MIT, part of
  Typhoon) is the only actively maintained Kubernetes-native one — last push 2026-09-12, implemented as
  a Kubernetes `Lease`, deployed as a Deployment plus ClusterIP Service;
  **[coreos/airlock](https://github.com/coreos/airlock)** (Apache-2.0, etcd3-backed, x86_64 image only)
  has not been pushed since 2024-01-03 though it is not archived; and a DynamoDB/API Gateway Terraform
  implementation exists. OBSERVED. **So the most cluster-aware feature Fedora CoreOS has depends on a
  third-party project for its most common shape, and the CoreOS-org implementation is dormant.**
- **Downgrade protection** via an age index, blocked by default, because allowing it "may allow rogue
  Cincinnati servers to induce downgrades to old releases with known security vulnerabilities" (§18).
- **Prometheus-format metrics** from the update agent, and **automatic bootloader updates** (§4).
- **Layered agent configuration**, merging `/usr/lib/zincati/config.d/` → `/etc/zincati/config.d/` →
  `/run/zincati/config.d/` lexicographically, with a `/dev/null` symlink to null out a shipped file.
- **Privacy-preserving node counting** via `rpm-ostree-countme`, on by default and maskable — the
  closest thing to inventory and deliberately not inventory: it tells Fedora infrastructure "how old
  your system is (with a very large approximation)" and nothing else. DOCUMENTED,
  [counting.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/counting.adoc).

DOCUMENTED, `auto-updates.adoc`, [Zincati](https://coreos.github.io/zincati/).

**Absent:** inventory, dashboard, desired-state controller, grouping, remote reset, remote recovery, and
a lock manager for the protocol it ships a client for. Live environments also do not auto-update:
"Since the traditional FCOS upgrade process requires a disk, the live environment is not able to
auto-update in place. For this reason, Zincati is not running there." DOCUMENTED.

**One project-health caveat.** Zincati's last tagged release is `v0.0.32` (2026-02-02), with 37 commits
from 7 distinct authors in the 12 months to 2026-09-16; the Cincinnati graph server saw 14 commits from
6 authors and has no tagged release. OBSERVED. Small, stable components rather than abandoned ones —
but the OCI-native-graph proposal that would replace the server has been dormant since March 2025
(§15), and the fleet layer is the least actively developed part of the stack.

### Open-source companion projects

- **Cincinnati update graph server** —
  [coreos/fedora-coreos-cincinnati](https://github.com/coreos/fedora-coreos-cincinnati), Apache-2.0,
  self-hostable; the server half of phased rollout.
- **coreos-assembler**, **coreos-installer**, **Ignition**, **bootupd**, **rpm-ostree**, **ostree** —
  Apache-2.0 or compatible, under `coreos/` or `ostreedev/`, all actively developed (§17).
- **greenboot** — [fedora-iot/greenboot](https://github.com/fedora-iot/greenboot), LGPL-2.1. A
  health-check and automatic-rollback framework, **not shipped in Fedora CoreOS** (its own upstream
  documents layering it on) and **not integrated with bootc** (§4). The missing piece on both sides, and
  it belongs to neither.
- **Flight Control** — [flightctl/flightctl](https://github.com/flightctl/flightctl), Apache-2.0, its
  own GitHub organization, documented by the *Fedora bootc* project
  ([flight-control.adoc](https://gitlab.com/fedora/bootc/docs/-/blob/main/modules/ROOT/pages/flight-control.adoc))
  rather than upstream bootc. Current
  release line `v1.3.0` (2026-08-26), with `v1.2.1` and `v1.1.4` backports published 2026-09-10 — so
  GitHub's "latest release" ordering is misleading — last push 2026-09-15, 77 open issues. Earlier:
  v1.0.0 2025-12-22, v1.1.0 2026-04-13, v1.2.0 2026-06-18. OBSERVED.

  **This is the project that would close bootc's fleet gap, and on documentation it has the four things
  bootc lacks.** Scope, in its own words: "It works best on image-based Linux operating systems running
  **bootc** or **ostree**… APIs are Kubernetes-like"; "Flight Control initially focuses on image-based
  Linux OSes running bootable container images (bootc), with support for ostree and rpm-ostree images
  planned for later. **It does not update package-based OSes**"; and it "updates the OS image by
  delegating to bootc (or rpm-ostree)". The four capabilities:
  - *Device identity and enrolment* — "The first time the Flight Control Agent runs, it generates a
    cryptographic key pair that serves as the device's unique cryptographic identity. The pair's private
    key never leaves the device, so that the device cannot be duplicated or impersonated", and the
    device "remains quarantined in a 'device lobby' until its Enrollment Request has been approved or
    denied by an authorized user." **This is the answer to the §10 device-identity question neither the
    mechanism nor the vehicle supplies.**
  - *Rollout policies* — groups, ordering, ratios ("first 1%, then 10%, then the rest") and per-site
    concurrency, currently via a single `BatchSequence` strategy, where "Batches are updated
    sequentially. After each batch completes, the rollout proceeds to the next batch, but only if the
    success ratio of the previous batch meets or exceeds the specified success threshold." That is a
    health gate — the thing §4 and §5 found missing.
  - *Disruption budgets* — `groupBy`, `minAvailable`, `maxUnavailable`.
  - *Per-device maintenance windows* — cron-style `downloadSchedule` and `updateSchedule`, separately.

  **Self-hostable, and Kubernetes is not required**: documented deployment options are Kind, Podman
  **Quadlets** on any Linux/systemd host (`flightctl-services` RPM plus `systemctl start
  flightctl.target`), Kubernetes or OpenShift via a Helm chart (needing Gateway API and cert-manager),
  MicroShift, and a disconnected/air-gapped OpenShift path; the server needs PostgreSQL, Redis and
  Alertmanager. DOCUMENTED, flightctl README and `docs/user/`. Its downstream product is **Red Hat Edge
  Manager**: the upstream repository's `docs/developer/downstream.md` names the registry path
  `registry.redhat.io/rhem/…`, and Red Hat's vendor documentation for Edge Manager describes the same
  capability set and installs `flightctl-services`. The correspondence is DOCUMENTED; the phrase
  "upstream of" is INFERRED, since no vendor sentence read here states it. Related upstream repositories:
  `flightctl/flightctl-ansible`, `flightctl/flightctl-ui`.

  **This profile did not evaluate Flight Control's own architecture, governance, health or independence.**
  It is a separate project deserving its own assessment. UNKNOWN, and on the follow-up list.
- **Ansible** — there is no dedicated upstream bootc collection; what exists is
  `community.general.bootc_manage` (`version_added: 9.3.0`, GPL-3.0-or-later, "Bootc Switch and
  Upgrade", options `state: ['switch','latest']` plus `image`), with the explicit caveat "This does not
  reflect a reboot. Please use `ansible.builtin.reboot`". DOCUMENTED, `management-generic.adoc` and the
  module source. **UNKNOWN**: whether a dedicated collection is planned.

### Commercial products

Named because the framework requires the separation, described only as their own documentation does:

- **Image mode for RHEL** — a Red Hat product delivered as a container image, "available by using the
  `registry.redhat.io/rhel9/rhel-bootc` bootc image", whose documentation states that bootc "is intended
  to supersede rpm-ostree" and that using rpm-ostree under image mode is unsupported. **That is a product
  policy statement, not an upstream one** — upstream rpm-ostree's README says development focus has
  shifted but that it "continues to be supported" (§16). DOCUMENTED (vendor documentation).
- **Red Hat Insights / Lightspeed tasks for image mode** — a task, "Initiate Update for image mode for
  RHEL host", positioned for fleets that want to avoid automatic upgrades; commercial, not
  self-hostable. DOCUMENTED (vendor documentation); read via search-result summaries after a direct
  fetch returned 404, so treat the phrasing as close paraphrase.
- **Red Hat CoreOS** — "supported only as a component of OpenShift Container Platform for all OpenShift
  Container Platform machines", with "Controlled immutability… you can modify only a few system
  settings", "`/usr`… is read-only. **Red Hat does not support altering this**", and "Limited direct
  access to RHCOS machines cluster is available for debugging purposes. **However, do not directly
  configure RHCOS systems.**" DOCUMENTED (vendor documentation),
  [openshift-docs architecture-rhcos](https://github.com/openshift/openshift-docs/blob/main/architecture/architecture-rhcos.adoc).
- **Red Hat Edge Manager** — the downstream of Flight Control, above.

**No commercial support offering for Fedora CoreOS itself was found** (§17), and none for upstream bootc
as a standalone product. Support in this family is bought as RHEL or OpenShift.

---

## 12. Debugging and day-2 operations

### The mechanism (bootc)

**bootc contributes debugging primitives rather than a debugging environment**, which is the correct
scope for a mechanism:

- **`bootc usr-overlay`** — a transient writable overlay on `/usr` so `dnf install strace` works and is
  gone at reboot, with the tmpfs and persistence caveats in §1.
- **`bootc status`**, with the stable JSON schema and `--verbose` for download-only state (§1).
- **`bootc internals fsck`**, experimental, read-only, no documented check list.
- **`journalctl -u bootc-finalize-staged.service -b -1`** as the documented way to find a failed
  finalization on the composefs backend (§4).
- **`.bootc-aleph.json`** for "what was this built from", and **`bootc container lint`** for "is this
  image valid" before it reaches a machine.

bootc also documents a thoughtful integration ask of the wider ecosystem: package managers should
"detect if `/usr` is read-only, and provide a useful error message referring users to documentation
guidance", observing that the naive check fails because "both of these fail on `/var` being read-only;
in a default bootc model, it won't be." DOCUMENTED, `package-managers.md`.

**What bootc does not provide:** SSH (a base-image concern), a support bundle, a rescue environment, an
IPC or D-Bus interface ("it doesn't have an IPC mechanism today",
[bootc#4](https://github.com/bootc-dev/bootc/issues/4)), and any operation other than `status` and
`container lint` inside a container. It is also **root-only**, which the Fedora CoreOS roadmap names as
a blocker for its own integration: "Bootc is currently root only: no unprivileged interface, no DBus
interface." DOCUMENTED,
[fedora-coreos-tracker#1726](https://github.com/coreos/fedora-coreos-tracker/issues/1726).

**Local rebuild as a debugging technique** is documented and is a distinctive answer to "apply a hotfix
to one server": pull the booted image, derive from it with the fix, and `bootc switch --transport
containers-storage`. The friction is stated: "At the current time the bootc host container storage is
distinct from that of the `podman` container runtime storage… It [is] not currently streamlined to
export the booted host container storage into the podman storage." DOCUMENTED,
[booting-local-builds.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/booting-local-builds.md).
The experimental `bootc image copy-to-storage` closes that gap, publishing the booted image into podman
storage as `localhost/bootc`. DOCUMENTED (experimental),
[experimental-bootc-image.md](https://github.com/bootc-dev/bootc/blob/main/docs/src/experimental-bootc-image.md).

### The vehicle (Fedora CoreOS)

**A conventional systemd userspace with a deliberately minimal package set and a documented substitute.**
"The FCOS image is kept minimal by design to reduce the image size and the attack surface. This means
that it does not include every troubleshooting tool that a normal OS may include. Instead, the
recommended approach is to leverage containers with the `toolbox` utility included in the image… It is a
wrapper around podman which starts long running containers with default mounts and namespaces to
facilitate debugging the host system." Inside the toolbox `dnf install` works and the host is at
`/run/host`. DOCUMENTED,
[debugging-with-toolbox.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/debugging-with-toolbox.adoc).

**The base image ships 477 packages**, answering several dimensions at once: podman 5.8.4, moby-engine
29.7.2, toolbox, rpm-ostree 2026.2, ostree 2026.4, **bootc 1.16.10**, bootupd 0.3.2, zincati 0.0.32,
coreos-installer 0.26.0, afterburn 5.10.0, composefs 1.0.8, nmstate 2.2.57, clevis and its pins,
tpm2-tools 5.7, cryptsetup, audit 4.2.1, selinux-policy 44.6, shim-x64 16.1, grub2-efi-x64 2.12, fwupd,
sssd, kexec-tools, mdadm, lsof, pciutils, nvme-cli, git-core, gnupg2, rsync, curl, chrony, cifs-utils
and iscsi-initiator-utils. Kernel 7.2.5-200.fc44, systemd 259.8. OBSERVED,
`manifest-lock.x86_64.json` in `fedora-coreos-config`.

**`sos` is not shipped and there is no support-bundle mechanism** — absent from the package lock and from
the documentation entirely. DOCUMENTED (absence). For an enterprise used to attaching an `sosreport` to
a support case that is a real workflow gap, and note that the Fedora/CentOS bootc base image *does* list
`sos` in its content set (§3).

**The journal is persistent by default but the fact is undocumented.** The shipped
`journald.conf.d/10-coreos-persistent.conf` sets `Storage=persistent`, with an in-file comment
explaining that the `auto` default would fail because `/var/log/journal` will not exist on first boot.
The user-facing documentation never mentions it. DOCUMENTED (source), UNDOCUMENTED (user-facing) —
recorded this way because an operator planning disk usage cannot learn it from the docs.

**Access recovery is documented and console-bound.** With a lost SSH key and no password, "you can gain
access back to the machine by booting into single user mode with the `single` kernel command-line
argument": intercept GRUB, append `single`, `passwd`, `reboot -f`. DOCUMENTED,
[access-recovery.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/access-recovery.adoc).
Note the interaction with the GRUB password feature (§9): enabling one closes the other.

**Console configuration is per-platform and settable at three points.** "Older FCOS releases enabled both
serial and graphical consoles by default. Newer releases use different defaults for each cloud and
virtualization platform, and use the kernel's defaults (typically a graphical console) on bare metal",
dated per stream (next 2022-10-03, testing 2022-11-28, stable 2022-12-12). Set it at install
(`coreos-installer install --console …`, which "will configure both the GRUB bootloader and the
kernel"), via Ignition `kernel_arguments` (kernel only, GRUB unchanged), or afterwards with `rpm-ostree
kargs` (kernel only). "You can specify multiple consoles; kernel messages will appear on all of them,
but only the last-specified device will be used as the foreground interactive console." DOCUMENTED,
[emergency-shell.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/emergency-shell.adoc).
That GRUB-versus-kernel distinction decides whether a remote machine is recoverable over serial after a
bad change.

**kdump is documented** with a concrete tuning note: "`crashkernel=auto` generally doesn't reserve enough
memory on Fedora CoreOS, so it is recommended to specify `crashkernel=300M`"; vmcore lands in
`/var/crash`. DOCUMENTED, `debugging-kernel-crashes.adoc`.

**Ignition debugging** has documented tooling — `journalctl --identifier=ignition --all`,
`systemd.journald.max_level_console=debug`, `ignition-validate` — plus one gotcha with real operational
teeth: "When Ignition enables systemd services, it doesn't directly create the symlinks necessary for
systemd; it leverages systemd presets. Presets are only evaluated on first boot, which can result in
confusion if Ignition is forced to run more than once… `systemctl preset-all` will need to be manually
invoked." DOCUMENTED, Ignition operator notes.

**`rpm-ostree status` is the state view**, with documented output including `AutomaticUpdatesDriver:
Zincati`, a `DriverState` line that can read "update staged: …; reboot delayed due to active user
sessions", per-deployment `Version`, `Commit` and `GPGSignature: Valid signature by …`, and the booted
deployment marked by `●`; `rpm-ostree db diff` shows package deltas. DOCUMENTED,
`tutorial-updates.adoc`.

### Operational and security consequences

**SSH is present on both and is not treated as a flaw by either.** Fedora CoreOS's posture — key-only, no
default credential, keys from two non-colliding sources, password auth off by a shipped drop-in — is a
well-designed version of "SSH is fine if nothing ships with a way in". The security cost is the obvious
one: a stolen key is a shell on the node, and the OS supplies no attestation that would make that
detectable.

**The more interesting consequence is what the minimal base image does to debugging.** Both systems push
tooling into containers — toolbox on Fedora CoreOS, a transient overlay or a derived image on bootc — so
both make debugging depend on something not on the machine. Toolbox needs to pull an image; `bootc
usr-overlay` plus `dnf` needs repositories. **In an air-gapped or network-broken failure, the documented
debugging path on both systems requires a network that is by hypothesis unavailable**, unless the
operator pre-mirrored a toolbox image or baked the tools into their own image. bootc's answer is better,
because baking `strace` into your own image is trivial when the image is yours; Fedora CoreOS's is to
pre-pull toolbox. Neither documents this as an air-gap caveat. INFERRED from how each mechanism works,
and an experiment candidate.

---

## 13. Persistent state and storage

### Shared model

The boundary is the same on both sides, drawn by OSTree: **`/etc` is versioned per deployment and
three-way merged; `/var` is shared across all deployments and never touched by an upgrade or a
rollback.** DOCUMENTED on both sides (`filesystem.md`, `storage.adoc`, `faq.adoc`).

bootc's stated rationale explains the asymmetry: "`/etc` is relatively small configuration files, and the
expected configuration files are often bound to the operating system binaries in `/usr`. But `/var` has
arbitrarily large data (system logs, databases, etc.). It would also not be expected to be rolled back if
the operating system state is rolled back. A simple example is that an `apt|dnf downgrade postgresql`
should not affect the physical database in general in `/var/lib/postgres`", with the operational payoff:
"Having `/var` separate also makes it work cleanly to 'stage' new operating system updates before
applying them." DOCUMENTED, `filesystem.md`.

Persistence across reboot: `/etc` and `/var`. Across upgrade: `/var` untouched, `/etc` merged. Across
rollback: `/var` carries over, `/etc` reverts (§5). Across reinstall or reset: below, and the two systems
differ.

### The mechanism (bootc)

**Customizable persistent paths** use the three mechanisms in §3 — symlink into `/var` at build time, a
state overlay per top-level, or transient root. Arbitrary top-level directories can be created at build
time and become mount points via `/etc/fstab` or systemd `.mount` units. DOCUMENTED, `filesystem.md`.

**`/var` is bind-mounted from `/ostree/deploy/$stateroot/var` unless it is a distinct partition, and
there is exactly one**; making it or its subdirectories separate mount points, network or tmpfs, is
supported. DOCUMENTED.

**Container runtime state has a bootc-specific wrinkle: there are *two* container stores.** The ordinary
podman store at `/var/lib/containers`, and a bootc-owned `containers/storage` instance reached through
`/usr/lib/bootc/storage` for logically bound images. They are deliberately separate, unification is
tracked at [bootc#20](https://github.com/bootc-dev/bootc/issues/20), and the documentation warns against
enabling the bootc store globally because layer garbage collection can break floating images.
DOCUMENTED, `filesystem-sysroot.md`, `logically-bound-images.md`. So "where do my container images live"
has two answers with different lifecycles: floating images are yours and persist through OS updates;
logically bound images are bootc's and are garbage-collected with them.

**Disk encryption: bootc recommends not owning it** (§8) — "that setup is owned by whoever builds and
maintains the image or installer, not by bootc". The same page carries a sharp secrets observation: "This
only protects data written after the per-device encryption boundary exists; don't provision
machine-specific secrets into the image before that boundary is in place." DOCUMENTED,
`filesystem-encryption.md`.

**Root growth is documented and non-obvious**, because `/` is not the physical root: `cloud-init`'s
`growpart` operates on the block device, and `systemd-growfs /sysroot` needs a temporary writable
remount, for which the docs recommend a `MountFlags=slave` drop-in on `systemd-growfs@sysroot.service`
with `ExecStartPre=mount -o remount,rw /sysroot`. The general problem is flagged: "Some higher level
tools such as e.g. `cloud-init` may (reasonably) expect the `/` mount point to be the physical root.
Tools like this will need to be adjusted." DOCUMENTED, `filesystem-sysroot.md`. A concrete cost of the
deployment-root model: existing cloud tooling that assumes a conventional root needs adjusting.

**RAID, LVM, ZFS, Btrfs, network storage, CSI:** bootc is agnostic — "Fundamentally bootc is agnostic to
the underlying block device setup" — and provides no guidance beyond that and the filesystem-type choices
at install (`xfs`, `ext4`, `btrfs`). ZFS is not mentioned. **UNKNOWN** as documented capability; whatever
the base image and installer support is what works.

### The vehicle (Fedora CoreOS)

**A documented, opinionated default layout with a hard minimum.** "Fedora CoreOS ships with a simple
default storage layout: the root partition is the last one and expands to take the full size of the
disk. Apart from the boot partition, all data is stored on the root partition." And the constraint that
catches people: "**Fedora CoreOS requires the root filesystem to be at least 8 GiB.**… Currently, if the
root filesystem is smaller than 8 GiB, a warning is emitted on login. Starting from June 2021, if the
root filesystem is smaller than 8 GiB and is followed by another partition, Fedora CoreOS will refuse to
boot." DOCUMENTED, `storage.adoc`.

The x86_64 partition table: BIOS-BOOT (raw), EFI-SYSTEM (FAT32, "Contains EFI GRUB image and Secure Boot
shim"), boot (ext4, "Contains GRUB configuration, kernel/initramfs images"), root (**xfs**). Reserved
labels that may not be reused: `boot`, `boot-<n>`, `root`, `root-<n>`, `BIOS-BOOT`, `bios-<n>`,
`EFI-SYSTEM`, `esp-<n>`, and the RAID device names `md-boot` and `md-root`. Default target disk size in
the build configuration is 10 GB, with `mitigations=auto,nosmt` as shipped kernel arguments; exact
partition sizes are in §19. DOCUMENTED, `storage.adoc` and `image-base.yaml`.

**What is customizable, all with worked Butane examples in one page:** a separate `/var` partition on the
boot disk (with `resize: true` on root to keep it above 8 GiB), a dedicated `/var/lib/containers`
partition, `/var/log` on a second disk, a fully separate encrypted mirrored `/var`, root reformatting in
place, root moved to RAID0/RAID1/LUKS, swap on a second disk, and NFS or CIFS mounts via Ignition-written
`.mount` and `.automount` units. The boot disk is addressable device-agnostically during provisioning as
`/dev/disk/by-id/coreos-boot-disk`. DOCUMENTED, `storage.adoc`.

**Root reprovisioning constraints, quoted:** the root filesystem "must keep label `root`"; "FCOS knows
that the root partition is special and will figure out how to find it and mount it"; "You must have at
least 4 GiB of RAM for root reprovisioning to work"; and "If you use Ignition to reconfigure or move the
root partition, that partition is not automatically grown on first boot." DOCUMENTED.

**mdadm RAID** is a first-class `storage.raid[]` section with boot-device mirroring sugar (§8). **LVM has
no documentation page** but the base image ships an empty `/etc/lvm/devices/system.devices` allowlist —
"The existence of the file prevents LVM from auto-activating any LVM devices that aren't explicitly
allowlisted" — plus a one-shot migration unit ordered `Before=kubelet.service`. DOCUMENTED (source,
[tracker#1517](https://github.com/coreos/fedora-coreos-tracker/issues/1517)), UNKNOWN (user-facing).
**Btrfs** is a valid Butane filesystem format and appears in upstream Ignition examples, but there is no
Fedora CoreOS guidance and it is not the default anywhere. **UNKNOWN. ZFS** is not mentioned. **CSI** is
not mentioned; no orchestrator ships, so CSI assumptions belong to whatever Kubernetes is layered on.

**What survives a reinstall is documented, and it is more than one would expect:** "The installer does
not completely scrub the target disk. Thanks to Ignition's filesystem-reuse semantics, if you apply a
config with the exact same partition and filesystem settings as the first install, all previously stored
data in additional partitions will still be available. This can be useful for persisting e.g.
`/var/lib/containers` or `/var/home` between reinstalls." With a fail-safe: "Fedora CoreOS requires that
only a single filesystem labeled `boot` exists. If multiple such filesystems are found on the first boot,
provisioning will error out as a fail-safe." `coreos-installer install` also offers `--save-partlabel
<glob>` and `--save-partindex`. DOCUMENTED, `bare-metal.adoc`.

**Ignition's filesystem-reuse rules are strict and fail closed:** with `wipeFilesystem: false`, reuse
happens only if type *and* label *and* UUID match, with unset label or UUID acting as wildcards, and a
wrong type makes Ignition fail and the machine fail to boot. Partition reuse is governed by an explicit
eight-row truth table over `{present, shouldExist, wipePartitionEntry}`. DOCUMENTED, Ignition operator
notes. Right for unattended provisioning, and a foot-gun in a reinstall workflow.

**One important live-environment caveat**, the single case where the config runs repeatedly: "When
booting a live environment, the Ignition config runs on every boot, so it should avoid wiping LUKS
volumes and filesystems that you want to reuse… When reusing LUKS volumes, you must configure a
`key_file`. **Ignition cannot reuse Clevis-backed LUKS volumes.**… Avoid writing persistent data to RAID
volumes, since **Ignition cannot reuse those**… Avoid using the `append` directive for persistent files,
since the append operation will occur on every boot." DOCUMENTED, `live-booting.adoc`.

### Where each architecture draws the line

Both draw it at `/var`, treating the machine as *replaceable infrastructure plus one data directory*. The
difference is what happens to that directory when things go wrong. **Fedora CoreOS** has no factory
reset, so the documented answer to "return this machine to a known state" is reinstall — and reinstall
deliberately *preserves* additional partitions, so the answer is partly "reinstall, and your data is
probably still there", which is convenient and is also why a corrupted `/var` is not recoverable by any
documented OS mechanism. **bootc** now has `bootc install reset` (§5), experimental, giving an empty
`/var` in a fresh stateroot while leaving the old one readable — a better answer to the same question,
costing disk space until someone cleans up.

---

## 14. Networking

### The mechanism (bootc)

**bootc has no networking model.** It consumes network configuration as image content or machine-local
state, with three narrow documented touchpoints: `bootc install --karg` for initramfs networking, with a
worked example ("`--karg ip=192.168.1.100::192.168.1.1:255.255.255.0:host1::none` for static IP
configuration", DOCUMENTED, `bootc-install.md`); registry access configuration via `registries.conf.d`
for mirrors and `insecure=true`, and `/etc/ostree/auth.json` for credentials (§9, §22); and a
`building/dns.md` page whose contents were not read here — DOCUMENTED (existence), **UNKNOWN**
(substance). Fedora bootc carries `sysconfig-network-configuration` and `proxy` pages of its own —
DOCUMENTED (existence), contents **UNKNOWN**.

**What the base image supplies is the real answer**, and the Fedora/CentOS bootc base image supplies
NetworkManager with "Full support for many complex networking types" (§3). Bonding, VLANs, bridges,
WireGuard, SR-IOV and RDMA are therefore NetworkManager-and-kernel questions, configured by files that go
into the image or into `/etc`. **Whether any of that is documented or tested for bootc specifically is
UNKNOWN**, and "the underlying component supports it" is not the same claim as "the project supports it".

### The vehicle (Fedora CoreOS)

**One of Fedora CoreOS's strongest documented areas: the network page is the largest in the documentation
set and covers the topologies edge, telco and industrial deployments actually need, each with paired
kernel-argument and Butane examples.**

The model: "Unless otherwise configured, Fedora CoreOS (FCOS) will attempt DHCP on every interface with a
cable plugged in… Regardless of the way you choose to configure networking it all ends up as
configuration for NetworkManager, which takes the form of NetworkManager keyfiles." Initramfs networking
is conditional: "Networking will only be started in the initramfs if determined to be required, or if
explicitly requested by the user with `rd.neednet=1`." DOCUMENTED,
[sysconfig-network-configuration.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/sysconfig-network-configuration.adoc).

**Five configuration channels**, in the documentation's own order: dracut kernel arguments; live-image
customization (`coreos-installer iso/pxe customize --network-keyfile`); `coreos-installer install
--copy-network`; Afterburn injection (currently VMware only); and Ignition-written keyfiles at
`/etc/NetworkManager/system-connections/*.nmconnection`, mode `0600`.

**Two warnings that are the operational heart of the page:**

> "If you provide networking configuration in multiple ways (i.e. via kernel arguments and via Ignition)
> then the configuration supplied via Ignition will win… **It is not supported to provide half
> configuration via kernel arguments and half via Ignition.**"

> "If you need networking to grab your Ignition config and your environment requires more complex
> networking than the default of DHCP to grab the Ignition config, then you'll need to use another method
> other than Ignition to configure the network."

The second is the bootstrap circularity every image-based system has, stated rather than left to be
discovered, with `--network-keyfile` as the documented way out.

**Coverage, all with worked examples:** static IP, **bond** (active-backup with miimon), **bridge**,
**team**, **VLAN**, and **VLAN on a bond**. The canonical dracut form is
`ip=${ip}::${gateway}:${netmask}:${hostname}:${interface}:none:${nameserver}`, with `bond=`, `bridge=`,
`team=` and `vlan=` for the rest. A conversion helper is documented: "NetworkManager ships a tool,
`nm-initrd-generator`, that can generate keyfiles from dracut kernel argument syntax", with worked output
for a bond. Disabling autoconfiguration is a documented `/etc/NetworkManager/conf.d/noauto.conf` with
`[main] no-auto-default=*`, carrying its own warning that a machine with neither will boot with no
network. Predictable interface names are the default, with NIC renaming on its own page via systemd
`.link` files, udev rules or the `ifname=` kernel argument. DOCUMENTED.

**Proxies are documented properly**, and notably not via `/etc/profile.d`: one environment file written
by Butane, referenced by explicit systemd drop-ins on each service that needs it — `rpm-ostreed.service`,
`zincati.service`, `rpm-ostree-countme.service`, and `docker`/`containerd`. Podman has no daemon, so each
unit carries its own `EnvironmentFile=`. Ignition has a separate `ignition.proxy` section for fetch-time
proxying. DOCUMENTED,
[proxy.adoc](https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/proxy.adoc). A
related operational note appears in the OCI-updates change: "proxied environments require attention as
the nodes will reach to a different address for updates."

**WireGuard** has its own page; **hostname** is a documented `/etc/hostname` write with `overwrite:
true`, "to make sure that we overwrite the hostname that is set up by Afterburn on some platforms".
DOCUMENTED.

**What is not covered, recorded as UNKNOWN rather than absence:**

- **IPv6** appears only as `[ipv6]` stanzas inside larger examples (`addr-gen-mode=eui64`,
  `method=auto`, `method=disabled`). No IPv6 section, no dual-stack or IPv6-only guidance.
  Documented-by-example only.
- **SR-IOV and RDMA** are not mentioned anywhere. For telco and GPU-fabric scenarios this is the
  material gap, and "NetworkManager and the kernel can do it" is not the same claim.
- **Corporate CA certificates** in the host trust store: no page (§9).
- **Remote network reconfiguration**: no page. `nmstate` **ships in the base image** (2.2.57, added per
  [tracker#1175](https://github.com/coreos/fedora-coreos-tracker/issues/1175), "Declarative network
  configuration") and is **undocumented** — a shipped declarative networking capability nothing tells
  you about.
- **Pre-Kubernetes / cluster networking**: no CNI or kubelet networking page, consistent with shipping no
  orchestrator. Networking packages present include `NetworkManager-tui`, `NetworkManager-cloud-setup`,
  `nftables`, `iproute-tc`, `nmstate`, `socat`, `bind-utils` and `passt`; `firewalld` is **not** present,
  and the alternatives page marks `iptables-legacy` as "removed in Fedora CoreOS 43 and later".
- **Wi-Fi** is a layering story and **cellular** is undocumented (§8).

**Assessment for the framework's named scenarios.** For *edge and industrial*, the bond/bridge/VLAN
coverage plus iSCSI boot plus per-machine installer configs is a strong documented story, with Wi-Fi and
cellular as the gaps. For *telco*, the absence of any SR-IOV or RDMA documentation is the blocker — an
absence of documentation rather than established incapability. For *GPU*, the same absence compounds with
the GPU-driver gap in §8. For bootc, all of these are the base image's problem and therefore the
adopter's: more freedom and more work.
---

## 15. Supply-chain ownership and reproducibility

"Could an organization independently recreate and operate what it is running?" Two different answers,
because two different things are being run — and in both cases the *architecture* of the supply chain
is strong while the *attestation* of it is weak.

### The mechanism (bootc)

**Source, licence, build.** Rust, dual-licensed `MIT OR Apache-2.0` ("SPDX-License-Identifier: MIT OR
Apache-2.0", both licence files present), one public repository created 2022-11-30. DOCUMENTED,
[LICENSE](https://github.com/bootc-dev/bootc/blob/main/LICENSE). A metadata discrepancy that will
mislead an automated scan: GitHub's licence detector reports `NOASSERTION`, and CLOMonitor and the
OpenSSF badge both record plain `Apache-2.0`; the SPDX expression is authoritative. OBSERVED.

**Releases are fully automated and documented well enough to audit.** A scheduled workflow opens a
version-bump PR every Monday at 08:00 UTC with a GPG-signed commit; merging a PR labelled `release`
creates a **GPG-signed git tag**, packages the source via `cargo xtask package`, and uploads two assets
to a draft release a maintainer publishes. `release.yml` runs on `ubuntu-latest` inside
`quay.io/coreos-assembler/fcos-buildroot:testing-devel`, using a GitHub App token and an imported GPG
key. `build-and-publish.yml` builds a matrix of `fedora-43/44/45/46` and `centos-9/10` against `ostree`
and `composefs-sealeduki-sdboot` variants on every push to `main`, pushing dev images to
`ghcr.io/bootc-dev/dev-bootc`. `.packit.yaml` drives Fedora Copr RPM builds from
`contrib/packaging/bootc.spec`. DOCUMENTED,
[RELEASES.md](https://github.com/bootc-dev/bootc/blob/main/RELEASES.md) and `.github/workflows/`.

**The vendored-dependency tarball is the best supply-chain artifact bootc publishes.** Every release
carries `bootc-<version>.tar.zstd` (source) and `bootc-<version>-vendor.tar.zstd`, documented as
"Pre-downloaded Cargo dependencies for offline builds. **Required for air-gapped or restricted network
environments.** Ensures reproducible builds with exact dependency versions." DOCUMENTED, RELEASES.md.
A concrete answer to "can I build this without crates.io" — but note the wording is a dependency-pinning
claim, not a bit-for-bit one.

**No reproducible-build statement exists.** The OpenSSF `build_reproducible` criterion is left
**unanswered** (`"?"`, `build_reproducible_justification: null`). OBSERVED,
[bestpractices.dev/projects/10113](https://www.bestpractices.dev/projects/10113.json). **UNKNOWN**,
recorded as unanswered rather than failed.

**There are no signed release artifacts, no SBOM and no build provenance — a DOCUMENTED absence, not an
UNKNOWN, confirmed four ways on 2026-09-16:** every release carries exactly two `.tar.zstd` assets with
no `.sig`, `.sigstore`, `.intoto.jsonl`, `.spdx.json` or `.att`; all nine workflow files contain no
`attest`, `sbom`, `cosign`, `sigstore`, `provenance`, `syft` or `slsa` step, and `release.yml` uses
`actions/create-release@v1` with no `actions/attest-build-provenance`; CNCF's own CLOMonitor records
`security/sbom: passed=false` and `security/signed_releases: passed=false` with the detail "**Score**: 0
(check passes with score >= 1) — **Reason**: 0 out of 5 artifacts are signed or have provenance" and
per-release warnings for v1.16.9 through v1.16.13; and
`gh api repos/bootc-dev/bootc/attestations/sha256:<digest>` returns 404. OBSERVED,
[clomonitor.io/api/projects/cncf/bootc](https://clomonitor.io/api/projects/cncf/bootc).

**The only cryptographic assurance on a bootc release is the GPG signature on the git tag** (verifiable
with `git verify-tag v1.16.3`); the tarballs are unsigned and carry no provenance. That is a real gap
for a CNCF project whose premise is supply-chain-shaped delivery, and it sits oddly beside the rest of
the report card: CLOMonitor scores bootc **71.9 / rating b** (Legal 100, Documentation 97.5, Security
68.2, Best Practices 68.4, Licence 42.9), passing on governance, maintainers, contributing, code of
conduct, DCO, code review, security policy, roadmap, adopters, changelog and community meeting, and
failing on sbom, signed_releases, security_insights, token_permissions, dependencies_policy,
license_scanning and openssf_scorecard_badge; the OpenSSF Best Practices badge is **"passing"**,
achieved 2026-07-16, with `vulnerability_report_process_status` and `release_notes_status` both "Met".
OBSERVED. The project is doing the process work and not the artifact-signing work.

**A third party can build bootc, and the path is documented**: `cargo build` or `make` for the bare
binary; `just build` — "Running `just` defaults to `just build` which will build a container from the
current source code; the result will be named `localhost/bootc`"; a root `Dockerfile` taking `ARG
base=quay.io/centos-bootc/centos-bootc:stream10`, so the base is swappable; and a local test matrix via
`just test-container`, `just test-tmt <plan>` (needing `bcvk`, `tmt` and libvirt) and `just
test-composefs <bootloader> <fs> <boot_type> <seal_state>`. DOCUMENTED, CONTRIBUTING.md and the
`Justfile`.

**But bootc's own supply chain is not the interesting one**, because what a bootc-based organization runs
is its own image, from its own pipeline, on its own base. Build tooling is any OCI builder — nothing
bootc-specific is required; `bootc container lint` is validation, not a builder. SBOM, provenance and
signing for the image are entirely the adopter's, and the capability exists in the ecosystem: the CentOS
bootc base images carry `.sig`, `.att` and `.sbom` cosign tags and a populated OCI referrers index
(OBSERVED, Quay API). Reproducibility is the adopter's problem, and the documentation raises it in an
unexpected place: "a step whose result is not deterministic (regenerating an initramfs is a common
example) can produce a different image on a cache-busted rebuild even when nothing meaningful changed",
advising "Prefer reproducible build steps for anything driven on a timer"; it also notes OSTree
"currently squashes all timestamps to zero", now called "an implementation bug" that will change.
DOCUMENTED, `booting-local-builds.md`, `filesystem.md`. Dependency pinning is `bootc switch
<image>@sha256:…`, as strong a pin as exists (§18). Private registries, mirroring and self-hosted
distribution are all standard and documented (§2, §22).

**The Fedora bootc base images are independently rebuildable and the build definition is public — on
GitLab, which is not where most people will look.**
[gitlab.com/fedora/bootc/base-images](https://gitlab.com/fedora/bootc/base-images) is MIT-licensed,
public, created 2024-04-25. It defines three content sets with documented layering: "**standard**: This
image is the default, what is published as quay.io/repository/fedora/fedora-bootc"; "**minimal**: a
convenient centralization point for CI and curation around a package set that is intended as a starting
point for a container base image"; "**minimal-plus**: This content set is intended to be the shared base
used by all image-based Fedora variants (IoT, Atomic Desktops, and CoreOS)", with "standard inherits
from minimal-plus and minimal-plus in turn inherit from minimal." It states a cross-variant
change-control rule — "All non-trivial changes to minimal and minimal-plus should be ACKed by at least
one stakeholder of each Fedora variant WGs" — names the fork-free path — "If you want total control over
the image, you don't need to fork this repository. Instead, you can use the existing container as a
'builder' to make new images" — and carries a stability caveat: "**NOTE:** The location and naming of
these images is subject to change." DOCUMENTED.

**One licensing fact that decides procurement, with no Fedora-side equivalent.** Red Hat's image-mode
documentation: "The `rhel-bootc` and user-created containers based on `rhel-bootc` container image are
subject to the Red Hat Enterprise Linux end user license agreement (EULA). **You are not allowed to
publicly redistribute these images.**" DOCUMENTED (vendor documentation),
[Using image mode for RHEL](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/using_image_mode_for_rhel_to_build_deploy_and_manage_operating_systems/introducing-image-mode-for-rhel_using-image-mode-for-rhel-to-build-deploy-and-manage-operating-systems).
Fedora CoreOS and Fedora bootc images are public with only Fedora's trademark conditions attached. An
organization intending to publish derived images, or ship them to customers, needs to know which base it
built from.

### The vehicle (Fedora CoreOS)

**The build system changed structurally during 2025–2026, and several of its own documents have not
caught up. This is the most important fact in this dimension.** Fedora CoreOS is no longer built by
`rpm-ostree compose` inside coreos-assembler; it is built by `podman build` from a `Containerfile`, on
top of a Fedora bootc base image, in **Konflux**, **hermetically**. The [`Containerfile`](https://github.com/coreos/fedora-coreos-config/blob/testing-devel/Containerfile)
header names the
invocation: `podman build --security-opt=label=disable --cap-add=all --device /dev/fuse
--build-arg-file build-args.conf -v $PWD:/run/src . -t localhost/fedora-coreos`. It runs `build-rootfs
make-rootfs`, chunks via `rpm-ostree experimental compose build-chunked-oci --bootc --format-version=1`,
labels `com.coreos.inputhash`, and emits `LABEL containers.bootc=1 ostree.bootable=1` with `CMD
["/sbin/init"]`. The Tekton pipeline sets `hermetic: true` and `prefetch-input: '[{"type": "rpm",
"path": "."}]'` per stream, with `branched` explicitly `hermetic: false`. DOCUMENTED (source),
[fedora-coreos-config](https://github.com/coreos/fedora-coreos-config) and its `.tekton/` definitions;
tracked at [fedora-coreos-tracker#1969](https://github.com/coreos/fedora-coreos-tracker/issues/1969),
closed 2025-09-29.

**Two documented rebuild paths, with different costs:**

1. **coreos-assembler**: `cosa init https://github.com/coreos/fedora-coreos-config` then `cosa build`,
   with `cosa buildextend-metal` and `buildextend-live` for artifacts and an `overrides/rpm` directory
   for local packages. **The hard requirement is virtualization**: "the most important prerequisite to
   understand is that coreos-assembler generates disk images, and creating those in a maintainable way
   requires **access to virtualization - specifically `/dev/kvm`**." The documented container invocation
   is privileged *but rootless*, and the docs explain why that is acceptable: "*You should run this
   command as non-root*… `--privileged`: Note we're running as non root, so this is still safe (from the
   host's perspective)". It is also documented as runnable in Kubernetes: "the Fedora CoreOS pipeline
   runs it inside OpenShift as an **unprivileged pod** on a bare metal cluster, with `/dev/kvm` mounted
   in." The only published resource figure in the whole documentation set is an OpenShift pod requesting
   `memory: "3Gi"` with the comment "Today COSA hardcodes 2048 for launching VMs". **Disk space is
   undocumented. UNKNOWN.** DOCUMENTED,
   [building-fcos.md](https://github.com/coreos/coreos-assembler/blob/main/docs/building-fcos.md),
   `docs/working.md`.
2. **Plain `podman build`** from the `Containerfile`, needing `--security-opt=label=disable
   --cap-add=all --device /dev/fuse` and **no KVM**, supporting `overrides/rpm` (a yum repo taking
   precedence) and `overrides/rootfs` (files copied over the final rootfs). DOCUMENTED.

**Building a *derivative* is now explicitly redirected to bootc**, a meaningful change of position:
coreos-assembler's page on custom operating systems has been emptied to three sentences — "Creating
custom immutable container-native operating systems is now supported by the Fedora bootc project, and
**Fedora CoreOS derives from that project.** Please see the bootc documentation for guidance on building
custom operating systems; **Fedora CoreOS is focused on a 'direct consume' model**." DOCUMENTED,
[coreos-assembler docs/custom.md](https://github.com/coreos/coreos-assembler/blob/main/docs/custom.md).
What remains for derivation is a git-submodule pattern in `fedora-coreos-config`'s README.

**Reproducibility: no bit-for-bit claim, and the project's own words are precise about what it does
claim.** Koji-tag reproducibility is bounded: "The Koji tag ensures that… (2) stream builds are
reproducible (**up to the GC retention policy we agree upon**)… Packages in `coreos-release` have a
longer TTL than `coreos-pool`, increasing the time that official builds can be reproduced by others."
DOCUMENTED, `stream-tooling.md`. Input pinning is by EVRA, not digest (`"NetworkManager": {"evra":
"1:1.56.1-2.fc44.x86_64"}`). OBSERVED. And the most explicit admission, from the issue that fixed it:
"Right now, in the buildah path, we're just building `FROM` a moving tag. **That makes our builds not
semantically reproducible.** We should fix this by pinning on specific digests" — now fixed, with
`build-args.conf` pinning a `sha256:` builder digest. DOCUMENTED,
[tracker#2037](https://github.com/coreos/fedora-coreos-tracker/issues/2037), closed 2025-10-26. Note
"semantically reproducible", not bit-for-bit.

**Fedora as a whole is moving on reproducibility.** The Change "Package builds are expected to be
reproducible" targets **Fedora Linux 46**, is Announced and Accepted, and defines the bar: "A completely
independent rebuild of a koji package produces rpms that are identical except for the build timestamps,
signatures, and some associated metadata. **The _payload_ (i.e. packaged files) and important metadata
are bit-for-bit identical.**", with a goal of "no fewer than **99%** of package builds reproducible" and
a public rebuilderd instance. DOCUMENTED,
[Changes/Package_builds_are_expected_to_be_reproducible](https://fedoraproject.org/wiki/Changes/Package_builds_are_expected_to_be_reproducible),
last updated 2026-09-10; its predecessor shipped for Fedora 41. **There is no Fedora Change proposal for
SBOMs** — four candidate wiki titles return 404 and a full-text search returns two results. The adjacent
Fedora 46 "Adopt PURL Metadata" Change mentions only that "this metadata might be interesting for
generating SBOMs for content included in (container) images." DOCUMENTED / OBSERVED (absence).

**SBOMs for Fedora CoreOS: a split answer, and the asymmetry is the finding.** On the published release
channel there is none — the stable build's `meta.json` has no SBOM key among its twenty-one, eight
plausible filenames return 404, the Quay referrers API on the stable manifest-list digest returns an
empty `manifests` array, and cosign fallback tags return 404 on both the index and the amd64 digest; the
same holds for `quay.io/fedora/fedora-bootc:44`. On the intermediate Konflux channel there is plenty:
`quay.io/konflux-fedora/coreos-tenant/fedora-coreos-stable` carries `.sig`, `.att` and `.sbom` at two
levels — an index-level SPDX-2.3 SBOM (4,537 bytes, creators "Organization: Red Hat", "Tool: Konflux
CI", "Tool: Mobster-0.6.0") and a per-architecture SBOM of 2,443,181 bytes listing 1,214 packages, 679
of them `pkg:rpm` with full EVR, generated by syft. And `quay.io/centos-bootc/centos-bootc:stream10`
carries its SBOM and attestations **on the published image**, with a populated referrers index.
OBSERVED, 2026-09-16.

**So the attestations are produced and then not published on the artifact users consume**, and the
Konflux tenant repositories use commit-SHA tags with `pipelinesascode.tekton.dev/max-keep-runs: "3"`,
i.e. they are pruned. DOCUMENTED (source). The reason is visible in the migration plan:
[tracker#2031](https://github.com/coreos/fedora-coreos-tracker/issues/2031), "Migration to Konflux for a
Secure FCOS Release Supply Chain", closed Phase 1 on 2026-04-01 with phases 2 ("build **all artifacts**
(i.e container image **and diskimages**) with Konflux"), 3 (tests) and 4 (release) still open. The issue
states the intent: "This build system adheres to the **SLSA framework**… a **verifiable, signed build
provenance record** is generated for the container image." **Disk images are still built by Jenkins and
coreos-assembler and therefore sit outside the Konflux provenance envelope, which is why
`builds.coreos.fedoraproject.org` has no SBOM.** DOCUMENTED / INFERRED for the causal link.

**What Fedora CoreOS does publish as provenance** is a set of `meta.json` fields naming exact inputs:
`coreos-assembler.container-config-git` (repository and commit), `coreos-assembler.container-image-git`
(repository, commit and a `dirty` flag), `base-oscontainer` (image, digest and manifest-list digest),
and `coreos-assembler.oci-imported-labels` carrying `com.coreos.inputhash` and
`org.opencontainers.image.revision`. OBSERVED. Genuine, checkable provenance in a non-standard format:
enough to identify every input, not enough for a tool expecting in-toto or SPDX.

**Signing changed materially in the last twelve months.** OSTree commit GPG signatures **no longer
exist**: "we need to change our client systems to not check the OSTree commit signature (**because there
is no longer an OSTree commit signature**) and switch them to verifying a signature of the container
payload instead", migrating systems "prior to the Fedora 43 rebase". The migration ships as an overlay
rewriting the image reference from `ostree-remote-image:fedora:docker://…` to
`ostree-image-signed:docker://quay.io/fedora/fedora-coreos:${version}`, hooked into Zincati via an
`ExecStartPre=` (§9). DOCUMENTED (source),
[tracker#2029](https://github.com/coreos/fedora-coreos-tracker/issues/2029). **The replacement is
containers/image "atomic simple signing" with detached GPG signatures from an S3 lookaside — not
sigstore, not cosign, no Rekor**; the shipped policy is reproduced in §9. Key rotation is documented,
scheduled and mechanically enforced through update barriers (§4, §18), the strongest part of this supply
chain. The Fedora primary keys themselves are published at
[fedoraproject.org/security](https://fedoraproject.org/security/), in the `fedora-gpg-keys` RPM and via
DNS OPENPGPKEY records; Fedora 44's is `rsa4096/DBFCF71C6D9F90A6`. OBSERVED.

**Mirroring.** Release artifacts and update payloads mirror by ordinary means — `coreos-installer
install --image-url <LOCAL_MIRROR>` or `--image-file <PATH>`, `--offline`, `--stream-base-url`, iPXE
`BASEURL`, and standard registry mirroring. **What is not documented anywhere is mirroring the Cincinnati
update graph**: the server is open source and `cincinnati.base_url` is a shipped knob, but no
operator-facing guide for standing one up was found. DOCUMENTED (the knob), **UNKNOWN** (the procedure).
The structural fix is proposed and dormant — the OCI-transport Change lists "Moving away from maintaining
a Cincinnati server towards having the graph live in an OCI registry alongside the update payload. **This
also allows users to maintain their own update graphs**" as a future benefit, and the tracking issue
[#1872](https://github.com/coreos/fedora-coreos-tracker/issues/1872), whose framing is "the requirement
to host a Cincinnati server is an huge impediment", has one comment and was last updated 2025-03-06.
DOCUMENTED / OBSERVED. One caveat for anyone building mirroring tooling: "The stream metadata format
(under `/streams`) is intended to be stable… *Everything else about the bucket layout… is subject to
change without notice. Third-party tooling should not rely on this structure.*" DOCUMENTED, `Design.md`.

### The independence question

**"If the primary commercial sponsor and all of its hosted services disappeared tomorrow, what
functionality would remain?"** Checkable facts only; §22 answers stage by stage.

- **bootc the tool** is dual-licensed, foundation-held at CNCF, built and released from public GitHub
  Actions with signed tags, vendored dependencies and a documented local build and test path. Source,
  build and release process would remain and are reconstitutable by anyone. What would need
  reconstituting is the maintainer group (§16, §17).
- **The bootc *model*** has no hosted component at all. A fleet running operator-built images from an
  operator-run registry would not notice. The strongest structural claim in this profile, following from
  the architecture rather than a policy.
- **Fedora CoreOS** depends on Fedora infrastructure at every stage: a Jenkins pipeline "running in an
  OpenShift cluster in Fedora's infrastructure", Konflux for the container build, Koji tags for content,
  `quay.io` for the update payload, `builds.coreos.fedoraproject.org` for artifacts and signature
  lookasides, the Fedora GPG keys, and the Cincinnati graph. That is Fedora Project infrastructure
  rather than a vendor's — a distinction the framework asks to be preserved — but hosted infrastructure
  nonetheless. An operator wanting independence must mirror the artifacts, self-host the graph without a
  guide, and accept that new releases would stop. The build tooling and configuration are public and a
  rebuild path exists, so what would be lost is the *release stream*, not the *ability to build*.

This is an assessment of documented structure, not a prediction about anybody's behaviour.

---

## 16. Governance and ownership

Recording OPEN SOURCE, OPEN GOVERNANCE, VENDOR-NEUTRAL OWNERSHIP and DIVERSE CONTRIBUTION separately, as
the framework requires. The two entries come out very differently on the last two.

### The mechanism (bootc)

| Property | Finding |
|---|---|
| Licence | `MIT OR Apache-2.0` (dual, SPDX-declared) |
| Foundation | **CNCF, Sandbox level, accepted 2025-01-21** |
| Repository | `bootc-dev` organization, created 2022-11-30; 22 repositories, one archived (`podman-bootc`) |
| Governance document | `GOVERNANCE.md`, a full CNCF-style charter |
| Maintainers file | `MAINTAINERS.md`, **with an employer column** |
| Contribution agreement | **DCO**, CLA exempt per CLOMonitor |
| Security policy | `SECURITY.md`, private reporting via GitHub Security Advisories |
| Meetings | Weekly, Friday 15:30 UTC, CNCF Zoom; notes on HackMD |

DOCUMENTED, the respective files and [cncf.io/projects/bootc](https://www.cncf.io/projects/bootc/):
"bootc was accepted to CNCF on January 21, 2025 at the **Sandbox** maturity level."

**Open source: yes.** Dual-licensed permissively, DCO rather than CLA, so no relicensing lever exists.

**Open governance: documented in unusual detail, with specific thresholds.** `GOVERNANCE.md` establishes
a Maintainer Council as "the governing body for the project", states that "Direct pushes to the code is
never allowed. All pull requests require review by a maintainer *other* than the one submitting it", and
sets criteria for becoming a maintainer: "participate in discussions, contributions, code and
documentation reviews for 6 months or more, perform reviews for 20 non-trivial pull requests, contribute
10 non-trivial pull requests and have them merged". Nomination is a PR against `MAINTAINERS.md`
triggering a CNCF `gitvote`, passing on a simple majority, and "**Maintainers nominations will be
evaluated without prejudice to employer or demographics.**" Removal takes a 2/3 vote; inactivity is "a
period of very low or no activity in the project for a year or more"; emeritus status exists and return
requires two votes. Most business runs by lazy consensus, "Any Maintainer may demand a vote be taken",
and charter changes need 2/3. A Security Response Team is provided for — "The Maintainers will appoint a
Security Response Team… The Maintainers will review who is assigned to this at least once a year" — but
**no named roster exists in-repo**. The code of conduct is delegated to CNCF's. DOCUMENTED,
[GOVERNANCE.md](https://github.com/bootc-dev/bootc/blob/main/GOVERNANCE.md).

**One governance-hygiene gap.** The weekly developer meeting is mandated — "Maintainers are expected to
participate in the public developer meeting, which occurs at 15:30 UTC on Fridays" — but its record is a
live HackMD pad plus emailed Zoom AI summaries. **There are no durable, publicly archived minutes in
git.** OBSERVED, `meetings/README.md`. Decisions this profile cites as from "the August 2026 community
meeting" — the no-release-branches confirmation, the deferred support-duration policy — have no public
record to check beyond the sentence in `RELEASES.md`.

**Vendor-neutral ownership: foundation-held, at the lowest maturity tier, with no move in progress.**
Sandbox since 2025-01-21, corroborated by CLOMonitor (`"maturity": "sandbox"`) and two CNCF onboarding
issues. **No Incubation application exists** — searches of `cncf/toc` issues and pull requests return
nothing. Incubation remains a roadmap goal: "Establish formal project governance and achieve CNCF
Incubation status. **Expand maintainer diversity and grow the contributor base across organizations.**"
OBSERVED / DOCUMENTED. The statistics block on the CNCF landing page does not match the repository (1,061
stars and a 2019 first commit, against GitHub's 2,277 stars and a 2022-11-30 creation date); CLOMonitor
and the GitHub API agree with each other and the landing-page counters should not be cited.

**Diverse contribution: concentrated, measurable, and published by the project itself.** All six
approvers list **Red Hat** as their employer, as do all four community managers — ten of ten named
people, with one maintainer role ("Approver") and no separate reviewer tier. DOCUMENTED,
`MAINTAINERS.md`. Measured: **873 commits from 55 distinct authors** in the 12 months to 2026-09-16, two
of them bots; ten authors with ten or more commits, twenty-one with exactly one; top of the distribution
`cgwalters` 284, `Johan-Liebert1` 201, `jeckersb` 86, a release bot 66, `henrywang` 32, `ckyrouac` 32.
By self-declared GitHub company, **17 authors declaring Red Hat account for 697 of 873 commits
(79.8%)**, bots 81 (9.3%), everyone else and undeclared 95 (10.9%) — **a floor rather than a ceiling**,
since at least two known Red Hat contributors declare no company. Non-Red-Hat employers appearing, each
with single-digit counts, include GitLab, Heroku, Chainguard, Docker, Microsoft, Debian/Ubuntu, Kong,
CERN/AlmaLinux, foundries.io and Kheeper. OBSERVED; method: `gh api
repos/bootc-dev/bootc/commits?since=2025-09-16` and `gh api users/<login> --jq .company`, cross-multiplied
by commit count. **The method's limitation is stated rather than hidden: the GitHub company field is
self-declared and often blank, so this measures declaration, not employment.**

**Adoption breadth is the counterweight, and it is qualified.** `ADOPTERS.md` lists eight direct adopters
— Red Hat, HeliumOS, AlmaLinux Atomic SIG, Caligra, CIQ, Universal Blue, Kheeper, ALT Atomic — plus an
indirect list via OSTree including Endless, Apertis, the Fedora Project, Playtron GameOS and Fyra Labs,
introduced as "a toplevel goal of bootc is to be the successor to ostree, and it is our aim to seamlessly
carry forward these users." **Every direct entry is typed Vendor or Integration; there are no End-user
entries at all**, despite the file defining that category as "The organization runs bootc in production in
some way." OBSERVED. Adopter files are self-declared and absence proves nothing, but "eight vendors and
no named end users" is what the primary source says.

**Two documentation defects in the governance set**, recorded because this dimension is about
checkability. `CONTRIBUTING.md` contradicts itself on the DCO — "a 'Developer Certificate of Origin' is
required… you just add a line to every git commit message: `Signed-off-by:`" and, three paragraphs later,
"You may use `Signed-off-by`, but we're not requiring it" (CLOMonitor records `dco: passed=true`, so it
is enforced in CI regardless). And `RELEASES.md` dates the weekly cadence to "**v1.16.0** (June 2024)"
when v1.16.0 was published 2026-06-10. OBSERVED.

**Ability of another organization to continue development.** The licence permits it, the build is public
and automated, the release process is documented end to end, the governance document defines an explicit
path for outside maintainers with numeric thresholds and an employer-blind clause, and the
vendored-dependency tarball means a fork can be built offline. The obstacle is not legal or
infrastructural but that the people who know the codebase are concentrated — a fact, not a verdict, and
the framework forbids inferring technical weakness from corporate ownership.

### The vehicle (Fedora CoreOS)

| Property | Finding |
|---|---|
| Licence | Component-dependent; Apache-2.0 for most tooling, MIT for the OS configuration, mixed for rpm-ostree and ostree |
| Foundation | **Fedora Project; an official Fedora Edition since Fedora 37** |
| Governance | A Fedora working group with a published PRD, documented voting rules, weekly public meetings with archived minutes |
| Trademark | Held by **Red Hat, Inc.**, "protected on behalf of the entire Fedora community", with Fedora Council oversight |
| Maintainers file | **None.** No member list, no roles, no affiliations |
| Contribution agreement | Fedora Project Contributor Agreement (FPCA) |

**Open source: yes**, across components under different licences.

**Open governance: documented, with a layer above it most projects lack, and a materially better public
record than bootc's.** The working group meets weekly at 15:30 UTC on Wednesdays in Matrix, with agenda
items driven by a `meeting` label and checklists generated by `coreos/fcos-meeting-action` (running to
issue #267 as of 2026-09-09). **Minutes are durable, public and machine-readable**:
`meetbot-raw.fedoraproject.org` carries dated directories with `.html`, `.log.txt` and `.summary.md`
files going back years, current through 2026-09-15. OBSERVED. Voting rules are specific: scheduled
meetings need "a quorum… of 5 people, or 51% of the members of the WG listed below, which ever is lower";
ad-hoc votes run on tracker issues, "must be announced on the current primary mailing list" and "open for
at least three working days", need at least 5 voters or 51%, and pass by simple majority; urgent ad-hoc
votes need three hours and a **2/3 majority**; and "Working days: non-holiday weekdays. Relevant holidays
are the national holidays of the USA, Western Europe, and India." DOCUMENTED,
[fedora-coreos-tracker README](https://github.com/coreos/fedora-coreos-tracker/blob/main/README.md).

**The PRD is a real charter and includes anti-goals**, which is rarer and more useful than a goals list:
primary use cases are "Clustered server node for running Kubernetes and/OpenShift OKD" and "Single server
node for running containerized applications"; the anti-goals are "Host for running non-containerized
applications" and "User desktop", with "the working group explicitly asks users to not explore these use
cases as part of Fedora CoreOS." DOCUMENTED, [PRD](https://fedoraproject.org/wiki/CoreOS/PRD).

**Above the working group sits Fedora's own governance**, documented rather than characterized. The
Fedora Council "is our top-level community leadership and governance body", "composed of a mix of
representatives from different areas of the project, **named roles appointed by Red Hat**, and a variable
number of seats connected to medium-term project goals", deciding by lazy approval for routine matters
and full consensus (+3 and no -1) for significant ones, with "only Fedora Council members' votes are
binding in the final tally", and "**The Fedora Project Leader is hired by Red Hat with the advice and
consent of the Fedora Council.**" DOCUMENTED,
[Fedora Council documentation](https://docs.fedoraproject.org/en-US/council/). FESCo is the elected
engineering body, and the Edition decision went through it with a recorded vote — "Closed: Accepted Jul
19, 2022 … the vote is APPROVED (+5,0,-0)" — with separate Council trademark approval. DOCUMENTED,
[FESCo #2823](https://pagure.io/fesco/issue/2823). Elected bodies with recorded votes are a stronger
governance property than a project-level charter alone; the Red-Hat-appointed seats and the FPL hiring
arrangement are part of the same documented picture and belong beside it.

**Vendor-neutral ownership: foundation-held through the Fedora Project**, trademark held by Red Hat on
the community's behalf under Council oversight. "Red Hat holds the trademark" and "Red Hat controls the
project" are different claims, and only the first is documented.

**Diverse contribution: unknown, and the reason is structural rather than a reporting gap.** The tracker
repository contains 29 files; `MAINTAINERS`, `OWNERS`, `CODEOWNERS`, `GOVERNANCE.md` and
`CONTRIBUTING.md` all return 404. The README's entire membership section reads "Please see
meeting-people.txt", and that file is 24 Matrix handles headed "List of people to ping before the Fedora
CoreOS community meetings" — no names, no employers, no roles. **So the quorum rules depend on "the
members of the WG listed below" and "51% of the WG membership", and the only list that exists is a ping
list; nothing anywhere defines who is a member or how one becomes one.** OBSERVED, exhaustive tree
listing and targeted 404 probes. The one named-role list is a duty roster in a different repository —
`fedora-coreos-streams/RELEASE.md` names two release managers, three release executors and four standby
executors — and carries no affiliations either. **UNKNOWN**, deliberately.

**The contrast is the cleanest governance finding in this profile**: bootc publishes a six-person
maintainer table with an employer column and no durable meeting minutes; Fedora CoreOS publishes years of
durable minutes and no member list at all, while operating quorum rules that presuppose one.

**Measured component activity, since affiliation cannot be measured.** In the 12 months to 2026-09-16:
`fedora-coreos-config` 634 commits / 23 authors, `ignition` 354 / 28, `coreos-assembler` 375 / 26,
`bootupd` 208 / 16, `ostree` 182 / 30, `rpm-ostree` 139 / 19, `butane` 124 / 12 (now archived),
`afterburn` 104 / 18, `coreos-installer` 51 / 10, `zincati` 37 / 7, `fedora-coreos-cincinnati` 14 / 6.
Top committers: `fedora-coreos-config` → `coreosbot` 277, `dustymabe` 151; `coreos-assembler` →
`dustymabe` 179, `nikita-dubrovskii` 54; `ignition` → `prestist` 210; `rpm-ostree` → `jmarrero` 61,
`cgwalters` 43; `ostree` → `cgwalters` 77, `jmarrero` 37; `bootupd` → `Johan-Liebert1` 64, `HuijingHei`
46; `zincati` → `Roshan-R` 15. OBSERVED, `gh api repos/<repo>/commits?since=2025-09-16`. Several
individuals appear in both this set and the bootc set, consistent with the ecosystem overlap the projects
describe; no employer attribution is attempted.

### The relationship between the three, governed separately

bootc is a CNCF project with its own charter and maintainer council. Fedora bootc is a Fedora project
with its sources on GitLab. Fedora CoreOS is a Fedora Edition with a Fedora working group. **The
2026-08-26 unification proposal is scoped to the last two, and the clarification was made on the thread
by the people who would know**: "We should clarify I think this *mostly* means Fedora bootc, as distinct
from the upstream bootc project itself which continues to have a goal of being generic OS/distribution
independent infrastructure (like podman, systemd, ignition etc.)", answered with "100%. The upstream
bootc project (i.e. CNCF incubation) is distro agnostic. The 'unification' we're referring to here is
strictly within the Fedora space." DOCUMENTED,
[fedora-coreos-tracker#2214](https://github.com/coreos/fedora-coreos-tracker/issues/2214). **That
exchange is the single best primary source for the mechanism-versus-vehicle distinction this profile is
built on.** The proposal's substance and status are in §18.

**The projects' statements about each other's futures are documented rather than speculative.**
rpm-ostree's README: "Currently, **development focus has shifted to bootc, dnf, and the ecosystem around
those tools.** However, rpm-ostree is widely in use today in many upstream projects and downstream
products and **continues to be supported.** In general, new major features related to bootable containers
should land in those projects instead." bootc's relationships page: "when using a container source,
`rpm-ostree upgrade` and `bootc upgrade` are effectively equivalent"; "**Overall, rpm-ostree is used in
several important projects and will continue to be maintained for many years to come.**"; "*It will be
supported to use both bootc and rpm-ostree together*; they are not exclusive." On ostree: "With bootc,
the OSTree transport layer is not used… **The role of OSTree may further shrink in the future**…but it
will remain an important part of the bootc stack." And a documented forward-looking compatibility break:
"it is likely that at some point bootc will switch to hard binding with podman. This will reduce the role
of ostree, and hence **break compatibility with rpm-ostree.** When such work lands, we will still support
at least a 'one way' transition from an ostree backend. But once this happens there are no plans to teach
rpm-ostree to use podman too." DOCUMENTED, `relationships.md`. **These are upstream statements**; Red
Hat's product documentation says something stronger (§11), and this profile keeps them apart.

---

## 17. Project health and sustainability

No GitHub stars as a quality score, and no speculation about corporate behaviour.

### The mechanism (bootc)

**Release cadence: weekly, automated, and observed to hold exactly.** 60 releases all time (v0.1 on
2023-09-07 through v1.16.13 on 2026-09-15); **25 in the 12 months to 2026-09-16**, against 18 in the
preceding twelve; **fourteen releases from v1.16.0 (2026-06-10) to v1.16.13 (2026-09-15), fourteen
releases in fourteen weeks**; one pre-release ever. OBSERVED, `gh api repos/bootc-dev/bootc/releases
--paginate`.

**Pull-request throughput and review discipline, measured.** 1,688 pull requests all time, 1,493 merged;
**483 merged in the last 12 months, about 9.3 per week**; 57 open. Creation to merge across those 483:
p25 9.4 hours, **median 40.7 hours**, p75 121.7, p90 333.4, mean 130.5. OBSERVED. OpenSSF Scorecard via
CLOMonitor records Code-Review at 10/10 ("all changesets reviewed") and Maintained at 10/10. A median
under two days with a long tail is a healthy profile at this size.

**Issue backlog is growing.** 676 issues ever, 402 closed, **274 open**; 244 created and 149 closed in
the last 12 months, a **net gain of 95 over the year**. OBSERVED. Not a crisis at this scale, and a
number to re-measure rather than extrapolate.

**Versioning and stability policy are unusually well specified for a Sandbox project.** Semantic
versioning since v1.2.0; "The bootc CLI and API are considered **stable**. We ensure that every existing
system can be upgraded in place seamlessly across any future changes", expanded into commitments on CLI
compatibility, API compatibility and upgrade path; deprecations announced in minor releases and removed
only in a major one; and **experimental features explicitly exempt** — "New functionality is typically
introduced as experimental, indicated by an `experimental` marker on the relevant CLI command or flag,
until it is deemed stable." DOCUMENTED, RELEASES.md. The exemption matters because several features here
are experimental: the composefs backend, `install reset`, `bootc image`, progress-fd.

**Two open policy questions the project flags itself**, quoted rather than inferred: no formal
support-duration policy ("raised in the August 2026 community meeting and deferred for broader maintainer
input. CNCF does not mandate a specific support duration but expects the project to document its own
terms"), and no finalized deprecation-notice window.

**No release branches and no backporting**: "All releases are tagged directly from the `main` branch, and
there are no `release/X.Y` branches for per-version maintenance", and "there is no backporting process.
Fixes, including security and critical bug fixes, are delivered in the next scheduled weekly release, or
in an off-cycle release from `main` when they cannot wait." DOCUMENTED. **A fix reaches you by moving to
the newest release.**

**Security response: process documented, substance untested in public.** `SECURITY.md` is about twenty
lines and specifies two things — use the GitHub Security tab, and do not discuss publicly. `RELEASES.md`
adds "Critical vulnerabilities are fast-tracked and released immediately" with "Coordinated disclosure
after fix is available". **After exhaustive search, not found: any embargo period, coordinated-disclosure
window, CVE-assignment process, distribution-notification list, named Security Response Team roster, or
severity/SLA matrix.** And there is no public track record:
`gh api repos/bootc-dev/bootc/security-advisories` returns an empty array and a GitHub advisory query for
the `bootc` Rust package returns nothing — **zero published advisories, zero CVEs.** OBSERVED. For a
project that installs operating systems with full privileges, an untested disclosure process is a risk to
price, recorded as an absence of evidence rather than a judgement about competence.

**Bus factor.** 55 distinct commit authors in 12 months; two people account for 485 of 873 commits; six
approvers, all at one employer; roughly 80% of commits from self-declared Red Hat employees. OBSERVED.

**Maturity trajectory.** CNCF Sandbox since 2025-01-21; no Incubation application; Incubation and
"expand maintainer diversity" both roadmap goals. **Commercial backing:** Red Hat employs every listed
maintainer and is an adopter; downstream commercial products exist; no funding figures are public.
**UNKNOWN** beyond that.

### The vehicle (Fedora CoreOS)

**Release history is long and the documented cadence is measurably accurate.** 184 stable releases as of
2026-09-16, first `31.20200108.3.0`, current `44.20260829.3.1`; the build index lists 219 stable builds
back to `31.20191210.3.0`, 263 testing and 260 next. In the 12 months to 2026-09-16: **26 stable releases
(median gap 14 days, mean 14.5, min 6, max 24), 30 testing (median 14), 37 next (median 13, mean 11.6)**.
The 24-day maxima on all three streams are the 2025-11-20 → 2025-12-14 holiday interval; `next` shows
documented weekly bursts around Fedora milestones. OBSERVED,
`builds.coreos.fedoraproject.org/prod/streams/*/releases.json`. **The documented "every 2 weeks" holds
precisely.** General availability was 2020-01-17.

**But the cadence is explicitly not a commitment**, and the wording is load-bearing for any
support-horizon claim: "**The stream cadences are not contractual**, but will initially have two weeks
between releases. **The stream maintenance policies are also not contractual** and may evolve from those
described above, but changes will preserve the use cases and intended stability of each stream."
DOCUMENTED, `Design.md`. The same document notes a CVE-exposure consequence of the promotion structure:
"Due to the promotion structure described above, `stable` can contain packages that are as much as four
weeks out of date."

**Fedora major-version transitions are scheduled, documented and observable.** `Design.md` specifies the
sequence around a Fedora GA: `next` switches at Beta, goes weekly at Final Freeze, and at GA there is a
triple release, with `stable` "now fully rebased to Fedora N" two weeks later. Measured history matches
exactly: stable moved F42 → F43 on 2025-10-24 and F43 → F44 on 2026-04-19, each about two weeks after
the corresponding Fedora GA. Per-release rebase trackers exist back to Fedora 38, with **#2127 "Rebase
onto Fedora 45" open since 2026-03-31**. DOCUMENTED / OBSERVED.

**How a release is decided, stated precisely because it is easy to assume wrongly.** Fedora CoreOS
composes from a **Koji tag** (`coreos-pool`), not a Bodhi update; Bodhi is the upstream source of content
("`testing`: Periodic snapshot of the current Fedora release plus Bodhi `updates`"). The release
checklists contain no Bodhi step; the sequence is a config-promotion PR, per-architecture Jenkins builds,
`kola` upgrade and cloud tests, then a manual "⚠️ Release ⚠️ … IMPORTANT: this is the point of no return
here." Go/NoGo is the working group's own: "If each steps and validation were successful the release is
considered GO… A stream release can become a NOGO during these meeting." DOCUMENTED / OBSERVED. **So:
Fedora CoreOS consumes Bodhi-stable content, but the release decision is its own CI plus working-group
Go/NoGo, not a Bodhi gate.** The production pipeline is Jenkins-based, "running in an OpenShift cluster
in Fedora's infrastructure", with operator access requiring a PR to Fedora infra ansible plus a project
admin as sponsor. DOCUMENTED,
[fedora-coreos-pipeline](https://github.com/coreos/fedora-coreos-pipeline).

**Component health, with two flags.** The figures are in §16. **Zincati** (37 commits, 7 authors, last
tagged release 2026-02-02) drives every Fedora CoreOS machine's auto-updates and is **the
thinnest-staffed critical path in the set**; `coreos-installer` (51 commits, 10 authors) is second.
Neither is archived and both are small, mature components, so this is a staffing observation rather than
an abandonment claim. `coreos-assembler`'s 2024 last tag looks alarming and is not — it ships as a
container image. `afterburn` has 104 commits and no release in about 11.5 months. **Butane is archived by
design**, merged into Ignition, which "natively accepts Butane YAML configs at boot" from 2.27.0.
OBSERVED / DOCUMENTED.

**Compatibility and breaking-change policy: a curated public list rather than a formal contract.** The
Major Changes page "only includes major changes that may require manual actions", announced on the
`coreos-status` mailing list, with per-stream rollout dates and remediation commands — the cgroups v1
entry is representative, a change that makes a machine fail to boot with the exact `rpm-ostree kargs
--delete` command and the release it lands in. A deprecation commitment exists in the design document:
"Because production refs are unversioned, users will seamlessly upgrade between Fedora major releases, so
compatibility must be maintained. **Removal of functionality will require explicitly announced
deprecations, potentially with long deprecation windows.**" DOCUMENTED.

**The stability posture is stated honestly and is a fit question, not a defect.** The one relevant
statement in the entire documentation set is in the migration guide: "FCOS provides **best-effort
stability**, and may occasionally include regressions or breaking changes for some use cases or
workloads." And the streams page places a real obligation on adopters: "it is strongly encouraged for
users to devote a percentage of their FCOS deployment to running the `testing` and `next` streams."
DOCUMENTED. That is part of the cost of the model, not advice.

**Security response** follows Fedora's, with asynchronous releases for CVEs and per-release notes citing
CVE identifiers directly. Measured per-CVE latency: **NOT MEASURED, UNKNOWN.**

**Adoption.** Verifiable data is thin; node counting exists and is privacy-preserving by design, and
whether aggregate counts are published was not established. **UNKNOWN.** Downstream, Red Hat's own
documentation describes Fedora CoreOS as "**one** upstream for RHEL CoreOS" — note the qualifier, since
RHEL CoreOS uses RHEL content. DOCUMENTED (vendor documentation), `openshift/os` FAQ.

**Commercial support for Fedora CoreOS itself: no statement exists offering or denying it.** An
exhaustive search of all documentation pages for `commercial`, `paid support`, `LTS`, `enterprise
support` and related terms returned a single on-topic hit, the best-effort-stability sentence above.
Support routing is community-only in practice: Matrix, the Fedora discussion board, two mailing lists and
the GitHub tracker. Two adjacent documented facts bear on it: the trademark guidelines require anyone
shipping modified Fedora materials to state that "the software provided is not provided or supported by
the Fedora Project", and Fedora's lifecycle documentation points longer-lifecycle users downstream — "**If
you want a distribution that moves slower, but has a longer lifecycle, CentOS Stream or Red Hat
Enterprise Linux, which are downstream of Fedora might be more suitable for you.**" DOCUMENTED / OBSERVED
(absence).

---

## 18. Operational lifecycle and support horizon

### The mechanism (bootc)

**Required upgrade frequency: as often as you rebuild your image, plus bootc itself.** For the tool the
effective policy is "run the latest", because there are no release branches and no backports; for the OS
image the adopter sets the cadence, and the shipped default is the timer in §11. **Supported releases:
latest only, pending a decision** (§17).

**Skipped upgrades: supported by design, and a genuine strength.** "Upgrade path: Systems can always
upgrade from any version to any later version without manual intervention", reinforced by the composefs
backend's "We are committed to in-place upgrades from all systems deployed since bootc 1.16.0."
DOCUMENTED. A machine off for a year moves in one step.

**Downgrade support: `bootc switch` to any digest the registry still holds.** No age index, no downgrade
block — more freedom and less protection: nothing stops an operator, or a compromised management agent,
from moving a fleet to a vulnerable old image. The available mitigation is the signature policy, and it
is off by default (§9).

**Indefinite version pinning: fully supported and documented as a mode.** `bootc switch <image>@sha256:…`
pins to a digest and makes `bootc upgrade` a no-op; the only lifecycle requirement is that the registry
keeps the manifest and layers — the operator's registry, therefore the operator's retention policy.
**This is the cleanest "pin forever" answer in this study, following from the artifact being an ordinary
OCI image rather than a project-managed release.**

**Kernel and CVE cadence: the base image's, and therefore the adopter's.** Fedora bootc tracks Fedora;
CentOS Stream bootc tracks CentOS Stream; RHEL bootc is a commercial product whose EULA forbids public
redistribution of derived images (§15). A derived image inherits whichever, plus whatever the adopter
adds — and the adopter owns the CVE lifecycle of everything they added. That is the framework cost of the
construction-kit model and it should be priced, not glossed. **Kubernetes compatibility: not applicable.
LTS, EOL policy, enterprise support: none for the tool; the base distribution's for the image; commercial
products downstream.**

**Operational burden over several years.** Recurring costs: operating a build pipeline; tracking a base
image's lifecycle and its "subject to change" caveats; re-testing on every rebuild; owning CVE response
for everything layered; choosing and implementing a rollout mechanism, because the shipped one is a
timer; and building the health-check and automatic-rollback layer nothing ships. Recurring savings: no
separate configuration-management system for the OS, no drift, no per-machine state to reconcile, a
rollback that is a bootloader reorder, and free version pinning. The trade turns almost entirely on
whether the organization already runs a container build pipeline it trusts.

### The vehicle (Fedora CoreOS)

**Required upgrade frequency: continuous, by default and by design.** Automatic updates are on, and the
default strategy is `immediate` — "an aggressive finalization method which is biased towards finalizing
updates as soon as possible, and it is only aware of node-local state. Such an approach is only
recommended for environments where temporary service interruption are not problematic." An operator can
slow it (maintenance windows, fleet lock, wariness) or stop it (disable Zincati), but the design assumes
motion. DOCUMENTED, [Zincati](https://coreos.github.io/zincati/usage/updates-strategy/).

**Supported releases: the stream tip. There is no LTS, verified exhaustively rather than assumed.** A grep
for `commercial|paid support|long.term support|LTS|enterprise support` across every documentation page
returns one hit, the best-effort-stability sentence; a grep across the tracker returns only unrelated
references to upstream *kernel* LTS tags. OBSERVED (absence). **Fedora Linux's own lifecycle, for
context**: "a new version… approximately every six months and… updated packages (maintenance) to these
releases for **approximately 13 months**… 'Release N' is supported until four weeks after the release of
'Release N+2'." DOCUMENTED,
[Fedora release lifecycle](https://docs.fedoraproject.org/en-US/releases/lifecycle/). **Fedora CoreOS
does not expose that clock**, because production refs are unversioned: "Because production refs are
unversioned, users will seamlessly upgrade between Fedora major releases, so compatibility must be
maintained." So there is nothing to renew, nothing to expire — and nothing to name to an auditor.

**Skipped upgrades: allowed freely, except across a barrier — and the barrier list is measurable.** The
normative definitions: a **barrier** is "a release which is a forced chokepoint for auto-updates.
Releases older than a certain barrier must first update to it before proceding to more recent updates"; a
**dead-end** is "a release which cannot further auto-update. Manual intervention is required to update
out of it"; a **rollout** is a valid auto-update target. Each barrier carries a mandatory `reason` field
pointing at a public explanation. DOCUMENTED,
[metadata/updates/specifications.md](https://github.com/coreos/fedora-coreos-tracker/blob/main/metadata/updates/specifications.md).

**Measured, the stable graph carries 21 entries: 19 barriers and 2 in-progress rollouts. Nine of the 19
are signing-key rotations** — roughly one per Fedora cycle, as documented — and the other ten have named
technical reasons including a systemd-resolved change, an aarch64 bootloader issue, a full `/boot` on
aarch64, a bootupd ordering requirement before the 6.9 kernel, the container-signature migration, and a
Zincati stream-annotation regression. OBSERVED,
`builds.coreos.fedoraproject.org/updates/stable.json`. **A machine powered off since 2024 must walk every
newer barrier in order, one reboot at a time.** The original design issue records the trade-offs in the
project's own words: "negative: requires multiple upgrades to get to latest version in the stream /
positive: forces upgrades through a known tested upgrade path / **negative: multiple updates means we
could lose rollback targets.**" DOCUMENTED. That last is easy to miss and is the sharpest operational
consequence: catching up past several barriers can consume the deployment that was your rollback.

**Downgrade policy: three distinct layers, and conflating them produces a wrong answer.**

1. **Zincati blocks downgrades by default**: "OS updates have a strict ascending ordering called 'age
   index'… **By default, this ordering is also used to prevent automatic downgrades.**" Enabling
   `allow_downgrade = true` carries its own warning: it "removes an additional safety check, and **may
   allow rogue Cincinnati servers to induce downgrades to old releases with known security
   vulnerabilities.**" DOCUMENTED,
   [Zincati auto-updates](https://coreos.github.io/zincati/usage/auto-updates/), confirmed in source.
2. **Zincati passes `--disallow-downgrade` to rpm-ostree on every staged update**, visible in the
   `systemctl status zincati.service` output in the project's own tutorial. DOCUMENTED.
3. **rpm-ostree itself does not block downgrades by default.** Its source comment reads "default to
   allowing downgrades for rebases & deploys (without --disallow-downgrade)", and `--disallow-downgrade`
   is an opt-in flag "Forbid deployment of chronologically older trees". DOCUMENTED (source). **The block
   is a policy of the update agent, not of the OS update engine**, and `rpm-ostree deploy
   <older-version>` by hand is permitted. That is the right level for the policy to sit at, and it is not
   what the common one-sentence summary conveys.

**Documented cases where rollback is knowingly broken**, the counter-example to "rollback is always
available": "Rollbacks to a version with Podman v3.x will require manual action: Podman v4.0 will perform
several schema migrations in the Podman database when it is first run… it will not be possible to roll
back to a release with Podman v3.x without losing some functionality in existing containers", and
"Rollbacks to a previous version with Podman v4.x will likely require manual action." DOCUMENTED,
`major-changes.adoc`. A transactional OS rollback does not undo an application-level schema migration in
`/var`, and the project says so.

**Indefinite version pinning: not a documented feature.** No Zincati "pin to version N" mechanism was
found — only enable/disable, `allow_downgrade`, and manual rollback. Stopping Zincati is pinning by
omission: no updates at all, rather than "this version, patched". **UNKNOWN** whether pinning is planned.

**Kernel cadence: Fedora's** — kernel 7.2.5-200.fc44 and systemd 259.8 on stable at 2026-09-16 (OBSERVED).
Current hardware enablement without a distribution migration is the point of the model; a kernel that does
not move is its opposite.

**Operational burden over several years.** Recurring costs: running some fleet fraction on `testing` and
`next` as the project asks; reading the Major Changes page and the `coreos-status` list, the only warning
channel for a machine-breaking change; owning the automatic-rollback gap; owning recovery, because every
documented path needs console access; managing the barrier-walk cost for machines that go dark; and having
no version number to report. Recurring savings, substantial: no build pipeline, no image to test, no CVE
triage for the base OS, automatic bootloader updates, documented key rotation, and a phased rollout
somebody else operates.

### The elephant: Fedora CoreOS's own lifecycle is under active review

**An evaluator making a multi-year commitment needs this on the record, stated as fact and no further.**
On 2026-08-26 a Fedora CoreOS maintainer opened
[fedora-coreos-tracker#2214](https://github.com/coreos/fedora-coreos-tracker/issues/2214), "CoreOS and
Image Mode/Bootc Unification", proposing to bring the Fedora bootc and Fedora CoreOS "communities and
outputs together **for Fedora 46**. This means not only sharing meetings, trackers, tests, pipelines, but
also (most importantly) outputs." The reasoning: "We produce similar things; We build differently
(unintentional legacy, konflux didn't exist when CoreOS started); We each have strong suits that could
help the other out — Bootc focusing more on 'build your own', CoreOS focusing more on 'direct
consumption'." Details were deliberately omitted — "This is socialization of a high level shift in
strategy for our community" — and a precedent named: "it will be similar to the Atomic Host and Container
Linux upstream efforts coming together."

**Status as of 2026-09-16, from the thread and verified against the Fedora wiki:** received with support
in the working group meeting on 2026-08-26, with one recorded concern "around ensuring a smooth transition
for existing Fedora CoreOS instances without requiring manual intervention from users"; a working group
formed on 2026-09-01 "to enumerate some items related to the technical direction of this effort"; a first
video working session held 2026-09-10 with recording, slides and notes published; a further call scheduled
for the following week. **There is no Fedora Change proposal, no FESCo issue and no committed Fedora 46
deliverable** — verified by enumerating every F46 change category on the wiki. DOCUMENTED / OBSERVED. The
scope clarification (Fedora-space only, not upstream bootc) is quoted in §16.

**What this means for the framework's question, without prediction.** Fedora CoreOS's stream model,
Ignition-based provisioning, Zincati update agent and Cincinnati graph are all in scope for a design
discussion happening now that has published no design. The FAQ already states the direction as a goal —
"The goal is to eventually have Fedora CoreOS build on top of Fedora Bootc both literally and in the
broader sense of being part of the same ecosystem", adding "It will eventually be possible to layer
Ignition and e.g. Zincati on top if desired. These tools are intended to be used generically and are not
strictly tied to Fedora CoreOS" — and the build system already does the "literally" half (§2, §15). The
roadmap issue [#1726](https://github.com/coreos/fedora-coreos-tracker/issues/1726), open since 2024-05-13
and last updated 2026-06-23, still has most of its checklist unticked — the update graph, the
Zincati/bootc integration, configuration management ("Using Ansible. Make sure we have good docs for
this"), UKI support and local package layering — and names a blocker in bootc itself: "**Bootc is
currently root only: no unprivileged interface, no DBus interface.**" A maintainer adds a concrete
migration concern: "one thing we'll want to make sure of as part of moving to `bootc` is that the
`rpm-ostree initramfs enable` functionality is handled somehow." DOCUMENTED. **No prediction is offered
about outcome or timeline; the record is that the question is open and being worked in public.**
---

## 19. Resource footprint and performance

The framework asks for measurement "where experimentally useful" and warns against ranking trivial
differences. Almost nothing here is measured, because measuring it is the experiment pass this tier
scoped out. What follows is the published and registry-observable data, separated from what needs a
running machine.

### Published minimums and layout

**Fedora CoreOS publishes no "minimum system requirements" page**; the figures are scattered across four
pages, which is itself worth recording:

| Figure | Value | Source |
|---|---|---|
| Root filesystem minimum | **8 GiB** | `storage.adoc`: "Fedora CoreOS requires the root filesystem to be at least 8 GiB… if the root filesystem is smaller than 8 GiB and is followed by another partition, Fedora CoreOS will refuse to boot." |
| RAM for root reprovisioning (LUKS or RAID) | **4 GiB** | `storage.adoc`, stated twice |
| RAM for live PXE with `coreos.live.rootfs_url` | **2 GiB** | `live-reference.adoc`: "the recommended option unless you have special requirements" |
| RAM for live PXE with rootfs as initrd | **4 GiB** | `live-reference.adoc`: "This method is slower… and requires 4 GiB of RAM" |
| Default cloud/virt disk size | **10 GB** | `image-base.yaml`: "Make it at least 10G because we want the rootfs to be at least 8G" |

DOCUMENTED. **No minimum RAM is published for a running node at all, and no minimum disk size for
`coreos-installer` beyond the 8 GiB rootfs rule. UNKNOWN.**

**Partition sizes are not in the documentation but are in the build source.** The documented x86_64 table
gives labels and types without sizes; `coreos-assembler`'s osbuild manifests give `bios_boot_size_mb: 1`,
`efi_system_size_mb: 127`, `boot_size_mb: 384`, `ppc_prep_size_mb: 4`, `reserved_part_size_mb: 1`, with
root taking the remainder, and s390x Secure Execution images adding `se_size_mb: 200`,
`boot_verity_size_mb: 128` and `root_verity_size_mb: 256`. Per-architecture order: x86_64 BIOS-BOOT →
EFI-SYSTEM → boot → root; aarch64 reserved → EFI-SYSTEM → boot → root; ppc64le PReP → reserved → boot →
root, with no ESP; s390x boot → root. The metal image is sized as an estimated rootfs plus 513 MB of
non-root partitions; the cloud image is fixed at 10 GB. Every architecture is built twice, for 512-byte
and 4096-byte sectors. OBSERVED, `coreos-assembler/src/osbuild-manifests/` and `src/cmd-osbuild`.
**The documentation publishes only the x86_64 partition table; there is no aarch64, s390x or ppc64le
table.** OBSERVED (gap).

**bootc publishes no minimums at all**, and neither does Fedora bootc; its own QEMU examples use `-m
4096`. `bootc install to-disk` creates an ESP of "at least 512 MiB" on UEFI architectures. DOCUMENTED,
`bootc-install-to-disk(8)`. Everything else is the base image's and the adopter's.

### Measured artifact and image sizes

**Fedora CoreOS x86_64 stable `44.20260829.3.1`**, compressed download sizes from the build metadata,
confirmed by HTTP `Content-Length`. OBSERVED, 2026-09-16:

| Artifact | Compressed | Uncompressed |
|---|---|---|
| `metal.x86_64.raw.xz` | 978 MiB | 2.90 GiB |
| `metal4k.x86_64.raw.xz` | 976 MiB | 2.90 GiB |
| `qemu.x86_64.qcow2.xz` | 976 MiB | 1.96 GiB (10 GiB virtual disk) |
| `live-iso.x86_64.iso` | 1027 MiB | — |
| live PXE triple (kernel + initramfs + rootfs) | **1018 MiB** total | — |
| `azure.x86_64.vhd.xz` | 979 MiB | **10 GiB** raw VHD |
| `aws.x86_64.vmdk.xz` | 1136 MiB | 1.13 GiB |

The live rootfs uses **erofs with lzma** (`live-rootfs-fstype: "erofs"`, `-zlzma,level=6`). DOCUMENTED,
`image-base.yaml`.

**Container image sizes, sum of compressed layers as reported by the registry.** OBSERVED, Quay.io API,
2026-09-16:

| Image | Architecture | Size |
|---|---|---|
| `quay.io/fedora/fedora-coreos:stable` (44.20260829.3.1) | amd64 | **975.8 MiB** across 66 layers |
| `quay.io/fedora/fedora-bootc:46` | x86_64 / aarch64 / ppc64le / s390x | **989.4 / 935.5 / 919.8 / 803.5 MiB** |
| `quay.io/fedora/fedora-bootc:44` | x86_64 | 1052.6 MiB |
| `quay.io/centos-bootc/centos-bootc:stream9` / `:stream10` | largest arch | 1174.4 / 855.4 MiB |

**One counter-intuitive finding.** Fedora CoreOS describes itself as "minimal, monolithic"; the
Fedora/CentOS bootc base image describes its content set as "intentionally quite large". **Measured, they
are within a few percent of each other** — 975.8 MiB versus 989.4 MiB for the current tags. OBSERVED.
That the two adjectives are doing rhetorical rather than descriptive work is INFERRED, and a good example
of why the framework asks for measurement rather than self-description. The one *uncompressed* figure
published in documentation is a `podman images` listing in Fedora bootc's getting-started page showing
`quay.io/fedora/fedora-bootc 41` at **1.66 GB**, with a derived example image at 2.05 GB. DOCUMENTED.

### What is not measured, and is not measurable from documentation

**Boot time, idle memory, idle CPU, upgrade download size, upgrade duration and reboot duration are
UNKNOWN for both systems.** Exhaustive searching of Fedora CoreOS's documentation, Fedora bootc's
documentation and bootc's `docs/src/` found no published figure for any of them; every apparent hit is
incidental — a `--memory 4096` flag in a VM example, a pull-latency caveat in a Quadlet note. OBSERVED
(absence).

**Upgrade download size is the most interesting and the hardest to reason about from documentation**,
because the deployment unit is a layered OCI image with content-addressed deduplication. A minor update
between adjacent releases should transfer only changed layers, and Fedora CoreOS's 66-layer amd64 image
suggests deliberate chunking for exactly that purpose — the roadmap lists update-delta work including
`chunkah`, zstd and `zstd:chunked`. That the effective delta is much smaller than the full image is
**INFERRED**, not documented, and a prime experiment candidate because it determines real fleet
bandwidth cost. One documented caveat bears on it: the composefs backend currently fails on
`zstd:chunked` images — "Images pushed with `--compression-format zstd:chunked` currently fail to pull on
the composefs backend ('unexpected EOF reading tar entry')… until then publishers should use plain zstd
(or gzip)." DOCUMENTED, `experimental-composefs.md`. So the compression format that would most improve
delta efficiency is currently incompatible with the newer backend.

**One architectural footprint property is documented rather than measured**: because deployments share
one filesystem and one content-addressed object store, two deployments differing by one package share
every unchanged object — no doubling of the OS partition, no fixed-size passive slot. The cost is the
mirror image: a staged deployment consumes space in the same filesystem as `/var`, coupling disk pressure
to OS updates. INFERRED from the documented storage model, and the reason §21 scenario 8 is a
high-value experiment here specifically.

---

## 20. Extensibility versus constraint

The framework asks for a placement on *APPLIANCE ↔ CONSTRUCTION KIT* and insists both flexibility and
constraint can be beneficial. These two sit at opposite ends while sharing almost all of their
implementation, which makes them an unusually clean illustration.

```
APPLIANCE  <───────────────────────────────────────────────────>  CONSTRUCTION KIT
                          Fedora CoreOS                bootc
                     (configure a fixed image)   (build your own image)
```

**Fedora CoreOS is near the appliance end without being an appliance.** It decides packages, kernel,
container runtimes, filesystem, enforcing SELinux, automatic and immediate updates, self-updating
bootloader, required signatures scoped to Fedora's keys, composefs on, and `/etc` and `/var` as the only
writable places. What it leaves open is genuinely wide — Ignition can repartition, encrypt, mirror,
create users, write arbitrary files and install arbitrary systemd units on first boot — but it is all
*configuration of a fixed image*.

**bootc is near the construction-kit end without being a kit.** It decides almost nothing: not the
distribution, kernel, packages, init system, whether `/etc` persists, whether signatures are required,
when updates happen, or what a health check is. What it does decide is the *shape*: the OS is an OCI
image, the update is transactional, `/var` persists, `/etc` merges, and rollback is a bootloader reorder.

**bootc's overridable set is unusually large, and each override is a documented configuration file rather
than a fork:**

| Decision | Default | Override |
|---|---|---|
| Root read-only | Yes, via composefs | `root.transient`, `root.transient-ro` |
| `/etc` persistent | Yes | `etc.transient = true` |
| Integrity enforcement | fsverity not required | `composefs.enabled = verity`, or sealed UKI |
| Signature verification | Not required | `policy.json`, `--enforce-container-sigpolicy` |
| Storage backend | ostree | `--composefs-backend` |
| Bootloader | bootupd (GRUB) or systemd-boot | `--bootloader=none` |
| Automatic updates | Timer shipped, distribution enables | `systemctl disable bootc-fetch-apply-updates.timer` |
| Update timing | 8 h + jitter | `--check` / `--download-only` / `--from-downloaded` |
| Writable `/opt` | No | state overlay per top-level, or symlink to `/var` |
| Filesystem type | Base image's default | `--filesystem xfs\|ext4\|btrfs` |

DOCUMENTED, per the pages cited throughout this profile.

**Fedora CoreOS's overridable set is smaller and several entries carry an explicit "we do not support
this"**: SELinux cannot be disabled, auditd cannot be stopped, top-level directories cannot be created,
`/boot` and the ESP must not be touched, and layering is "strongly discourage[d]". What *can* be
overridden: composefs (a kernel argument), the update strategy, rollout wariness, the stream, the
partition layout and filesystems via Ignition, kernel arguments, the console, and the container signature
policy bind-mount (via a `/dev/null` symlink).

**Can unsupported states be created? Does customization weaken guarantees? Both answer yes, and both say
so.** On bootc, a derived image can trivially break its own guarantees: enable `root.transient` and the
immutability claim is gone for that boot; use XFS and the sealed-UKI path is unavailable; layer packages
with rpm-ostree and the deployment is marked `incompatible` and "`bootc upgrade` refuses to update it
with an error such as 'Deployment contains local rpm-ostree modifications'" — good design, because the
tool detects the unsupported state and refuses rather than silently degrading. DOCUMENTED,
`initramfs.md`. On Fedora CoreOS, layering is supported-but-discouraged and exists "for use in debugging a
Fedora CoreOS machine"; the GPU case in §8 is the sharpest illustration of customization weakening a
guarantee, since unsigned out-of-tree modules require "either disable Secure Boot or sign them".

**Does flexibility increase testing responsibility? Does constraint reduce operational complexity? Yes
and yes, and both effects are large here.** bootc's flexibility moves the entire test matrix to the
adopter: every image is a new artifact nobody else has booted. The mitigations are real — `bootc container
lint` as a build-time gate, `bcvk ephemeral` as a zero-privilege local VM, the stable status API for
automation — but they are tools for testing your own thing, not a substitute for someone having tested
it. And the matrix multiplies: four immutability strictness levels, two storage backends, three
bootloader modes, and the sealed/unsealed distinction are all supported configurations with different
behaviour, and §5 already found boot-failure detection differs between backends. Fedora CoreOS's
constraint eliminates that for the base OS at the price of a hard ceiling: 184 stable releases and three
continuously tested streams mean the image an operator boots has been exercised, and when the ceiling is
reached — a driver, kernel module, FIPS, a GPU — the documented answer is not "configure it" but "use the
other project".

**Can existing enterprise standards be incorporated, or must the organization adopt the project's?**
**bootc: existing standards fit unusually well, with two named exceptions.** The build is a Containerfile,
so an organization's existing image pipeline, scanner, signing infrastructure, registry RBAC and
promotion process apply unchanged; corporate CA certificates, monitoring agents, security agents and
compliance tooling are package installs. The exceptions are that **systemd `sysext` and `confext` are
explicitly unsupported**, ruling out one common enterprise extension pattern, and that **there is no
secrets mechanism**, so the organization brings its own. DOCUMENTED, `filesystem.md`,
`building/secrets.md`. **Fedora CoreOS: the organization adopts the project's standards.** Ignition is the
configuration language and is deliberately hostile to hand-authoring; there is no documented Ansible,
Puppet, Chef or Salt story — a grep of all documentation pages for `ansible` returns zero hits, and the
roadmap lists "Using Ansible. Make sure we have good docs for this" as an open item — and the idiom the
documentation teaches for anything post-first-boot is a stamped systemd oneshot unit written by Ignition.
DOCUMENTED / OBSERVED (absence). An enterprise with an existing configuration-management standard will
find no documented bridge to it.

**The honest summary of the trade.** bootc's flexibility costs an image pipeline to build and secure, a
test matrix nobody else runs, CVE ownership for everything layered, a fleet layer to choose or build, a
health-check and automatic-rollback layer that does not exist, a secrets mechanism to pick, and four
strictness dials to decide and test — plus a documentation set excellent on mechanism and sparse on
worked configuration, where the highest-leverage security control has no example anywhere. Fedora
CoreOS's constraint costs a ceiling low enough to hit in ordinary circumstances (drivers, GPUs, FIPS,
kernel modules, Wi-Fi), a one-shot configuration model with no reconciliation, no factory reset, no
automatic rollback, no support bundle, no version number for an auditor, and an obligation to run part of
the fleet on pre-release streams.

**What each buys is the mirror image**, and neither is better. The choice turns on one question with
nothing to do with either project's quality: does the organization already operate a container build and
signing pipeline it trusts enough to put its operating system through? If yes, bootc's costs are mostly
already paid and its flexibility is close to free. If no, those costs are a new programme, and Fedora
CoreOS's ceiling is probably higher than the organization needs.
---

## 21. Failure experiments

**Tier scope, stated first.** The ten destructive experiments were **NOT RUN** — the scope decision
recorded on the platform-profile task before the work started.
Every scenario below is **NOT TESTED / OUT OF TIER SCOPE** for observed behaviour. What is recorded is
what documentation and source say the *expected* behaviour is, DOCUMENTED where a primary source states
it explicitly and INFERRED where this profile reasons from documented mechanics. Each scenario is
answered separately for bootc and Fedora CoreOS wherever they differ.

**1. Cut power during OS update.** *bootc:* the running deployment is untouched, because staging writes
only to the object store and a new deployment directory and finalization is last. On the ostree backend
this follows from upstream OSTree's guarantee — "**If the system crashes or you pull the power, you will
have either the old system, or the new one**" (DOCUMENTED,
[ostree atomic upgrades](https://ostreedev.github.io/ostree/atomic-upgrades/)) — INFERRED for bootc,
whose own documentation is silent. **On the composefs backend there is no equivalent statement anywhere.
UNKNOWN**, with one partial mitigation: composefs staging state "lives under
`/run/composefs/staged-deployment` and is **never persisted to disk**", suggesting an interrupted stage
simply vanishes (INFERRED). A second failure point is documented and more interesting than the download:
the `/etc` merge runs inside `ostree-finalize-staged.service` **at shutdown**, and if it fails it writes
a stamp file that `ostree-boot-complete.service` surfaces on the next boot — so a power cut during
*shutdown* is a different scenario from one during *download*, and only the first has a detection
mechanism (DOCUMENTED, `boot-failure-detection.md`). *Fedora CoreOS:* same OSTree guarantee, same absence
of a project-specific statement. **The single most valuable experiment on the list.**

**2. Supply a corrupted new OS image.** *bootc:* depends entirely on configuration, and the default is
permissive (§9). With signatures required the pull fails and the machine stays put; without them — the
upstream default — a corrupted-but-well-formed image would be deployed. Corruption breaking the OCI
manifest or layer digests is caught by containers/image's ordinary digest verification regardless of
policy — INFERRED from bootc using containers/image, not stated by bootc. What bootc does *next* after a
failed pull is not documented. **UNKNOWN.** With `composefs.enabled = verity` or a sealed UKI, corruption
of the deployed tree is detected at read time as `EIO`, and a sealed UKI with a mismatching root digest
prevents boot entirely (DOCUMENTED, `experimental-composefs.md`). *Fedora CoreOS:* rejected — the shipped
policy rejects by default and requires a Fedora GPG signature against three named keys (§9). What Zincati
does next is **UNKNOWN**; the signing-migration MOTD suggests failures surface as "the system will likely
fail to continue updating", a warning rather than a documented retry policy.

**3. Introduce a kernel that cannot boot.** **The scenario where both are weakest, and both document the
gap.** *bootc:* **the machine does not recover on its own.** No automatic rollback ships; boot-entry
counting is explicitly not configured on the composefs backend and is undocumented for the ostree backend
(**UNKNOWN**, deliberately not inferred); greenboot "does not yet integrate with bootc". Documented
recovery is a human at a console selecting the previous entry, or `bootc rollback` if the system boots far
enough for a shell. DOCUMENTED, `boot-failure-detection.md`, `building/bootc-runtime.md`. *Fedora CoreOS:*
same outcome, better-evidenced — rollback "is a manual operation that requires human intervention and
console access", greenboot is not shipped, and the design question
[#47](https://github.com/coreos/fedora-coreos-tracker/issues/47) has been open since 2018. A temporary
rollback via holding Shift is available — and is closed off if the operator enabled a GRUB password (§9).
**Two sub-cases an experiment must separate and the documentation does not:** a kernel that panics
immediately, and a system that boots far enough for userspace but fails a critical unit. Only the second
produces the journal evidence the documentation tells you to look for.

**4. Break Kubernetes after OS upgrade.** **Both: nothing happens, and the OS is not aware.** The
boot-success criterion on both is at most "finalization did not fail"; there is no application-health gate
anywhere in either update path. bootc states whose job it is: "there is no 'outer container runtime' when
a bootc container is deployed on a host. **The system must perform health checking on itself (or have an
external system do it).**" DOCUMENTED, `building/bootc-runtime.md`. Fedora CoreOS's FleetLock gates *when*
a node may reboot, not whether it came back healthy; the lock is released after reboot by the node itself.
DOCUMENTED, [FleetLock protocol](https://coreos.github.io/zincati/development/fleetlock/protocol/). **A
node that boots cleanly and never becomes Ready is invisible to both.** The documented answers are
external: OpenShift's Machine Config Operator for the RHEL CoreOS product, Flight Control's batch success
thresholds, or the early-development `bootc-operator`'s cordon/drain rollout state machine (§11). None is
part of the OS or the mechanism.

**5. Corrupt persistent configuration.** **Both: no OS mechanism helps for `/var`; `/etc` is partly
recoverable.** `/var` is shared and not rolled back, by design — "a bootc update or rollback should not
affect this application data" — so corrupting it leaves neither system with a path back. `/etc` is
versioned per deployment, so a rollback reverts it, which is a real recovery path for a bad `/etc` change
and equally why a rollback loses a *good* `/etc` change made since the upgrade (§5). Two mitigations exist
and neither is on a default path: bootc's `etc.transient` makes the problem structurally impossible, and
`bootc install reset` gives a fresh `/etc` and empty `/var` in a new stateroot while preserving the old
one. Fedora CoreOS has neither; its documented answer is reinstall, which by Ignition's filesystem-reuse
semantics *preserves* additional partitions and so may not clear the corruption either (§13). For SELinux
policy specifically, Fedora CoreOS documents both detection and repair (§9) — the only documented `/etc`
repair procedure found on either side. DOCUMENTED.

**6. Remove network during upgrade.** *bootc:* the pull fails, the machine is unaffected, and the timer
retries on its next interval (8 h plus up to 2 h of jitter, §11). Retry and back-off within a single
invocation, and partial-download resumption, are **UNKNOWN**, though containers/image's layer caching
means a re-run should not re-fetch completed layers — INFERRED from the documented statement that "the
downloaded image data remains cached" after a discarded download-only stage. *Fedora CoreOS:* Zincati's
poll fails and retries; its interval and back-off are in its own documentation and were not read here.
**UNKNOWN** in this profile. **Ignition is the more interesting case, because it fails closed** (§10):
losing the network during *first boot* with a remote config means the machine does not come up, by
design, with documented retry behaviour — exponential backoff from 100 ms doubling to 5 s, a 10 s
response-header timeout, and "Any HTTP response code less than 500 results in the request being
completed", so a 404 is final and a 503 is retried. DOCUMENTED.

**7. Make the image registry unavailable.** *bootc:* two distinct cases. The *OS registry* being
unavailable means no updates and nothing else; the machine continues on its current digest indefinitely,
there is no management plane to lose, and for an air-gapped fleet this is the *intended* steady state
with an `oci:` directory on removable media as the documented alternative (§22). The *application
registry* is a container-runtime matter with one OS-level consequence: **logically bound images exist
precisely to eliminate it** — "if the remote registry is unavailable temporarily, the host system may run
for a longer period of time without log forwarding or monitoring, which can be very undesirable", and
bound images "are ensured to be available when the (bootc based) server starts". DOCUMENTED,
`logically-bound-images.md`. So a bootc system that bound its monitoring agent survives a registry outage
with monitoring; one that did not, does not. *Fedora CoreOS:* registry or graph-server outage means no
updates and nothing else — plus a third case bootc does not have: **`toolbox` needs to pull an image**, so
a registry outage removes the documented debugging path unless it was pre-pulled. DOCUMENTED by
implication of how toolbox works; not documented as a caveat anywhere.

**8. Fill the disk.** **UNKNOWN on both, and the largest genuinely open question a local VM could
settle.** No documentation page on either side addresses a full root filesystem. What makes it
architecturally specific here: **deployments, the object store and `/var` all share one filesystem**, so
there is no fixed-size passive partition to stage into and `/var` growth competes with OS updates. A
staged deployment on a nearly-full disk has no documented behaviour, and neither does a failed garbage
collection. INFERRED that the two are coupled; the *consequence* is genuinely unknown. Three adjacent
documented facts bear on it: Fedora CoreOS refuses to boot if the root filesystem is under 8 GiB and is
followed by another partition (§13); `bootc install reset` leaves the old stateroot on disk until manually
removed, so a factory reset on a constrained device can itself fill the disk (§5); and `bootc usr-overlay`
is tmpfs-backed at 50% of RAM with "no pre-flight space check and no early warning before the `tmpfs` is
full", producing `ENOSPC` (§1). DOCUMENTED.

**9. Damage boot configuration.** **The structural weak point on both, for the same reason: the bootloader
sits outside the transactional unit** (§4). On bootc it is installed once and never updated, so a damaged
ESP has no A/B counterpart and no documented in-band repair. **UNKNOWN.** On Fedora CoreOS the ESP *is*
maintained automatically by `bootloader-update.service`, which is better; but there is still one ESP per
disk and no documented repair path for a damaged one, other than boot-device mirroring, which creates
"independent EFI partitions on each constituent disk" and is therefore a genuine mitigation. DOCUMENTED,
`bootloader-updates.adoc`, `storage.adoc`. Damage to the *bootloader entries* rather than the bootloader
is more recoverable — both write a menu entry per deployment and the documented recovery is to pick
another at the console, a path a GRUB password closes. Recovery from outside is documented on the vehicle
and absent on the mechanism: Fedora CoreOS's live ISO can reinstall and `coreos-installer` can preserve
partitions with `--save-partlabel`; bootc has no recovery media of its own.

**10. Remove the management plane.** *bootc:* **no effect, because there is no management plane in the
required path.** Boot, run, local rollback and local debugging are all independent of any central service;
if Flight Control or `bootc-operator` is in use, its absence stops orchestration and nothing else.
DOCUMENTED by absence and by the architecture. *Fedora CoreOS:* no effect on the machine — an unreachable
Cincinnati graph means Zincati finds no updates and the machine continues indefinitely, and disabling
Zincati entirely is the documented way to make that the intended permanent state and is the first step in
the documented rollback procedure. DOCUMENTED, `manual-rollbacks.adoc`.

**What each project already provides toward running these properly.** bootc has a test harness and local
VM story an experiment pass would build on rather than replace: `just test-container`, `just test-tmt
<plan>` (Fedora's Test Management Tool, needing `bcvk` and libvirt) and `just test-composefs <bootloader>
<fs> <boot_type> <seal_state>` are documented in CONTRIBUTING.md, with a `tmt/` directory and an `.fmf`
metadata tree in-repo, and the CI matrix already exercises six base images across two backend variants on
every push. DOCUMENTED / OBSERVED. Fedora CoreOS has **`kola`**, the test framework inside
`coreos-assembler`, which the release process uses for upgrade and per-cloud tests — the stable release
checklist runs "kola upgrade/AWS/OpenStack/Azure/GCP" before the point of no return. DOCUMENTED (source).

---

## 22. Operational independence experiment

**Tier scope**: the end-to-end run was **NOT RUN**. What follows is the documented and source-supported
answer for each of the nine stages, with the dependency on project-controlled infrastructure named at
each. **This is where mechanism and vehicle diverge most.** bootc's design point — any OCI registry, any
base image, no hosted service — means most stages have no project dependency to remove. Fedora CoreOS's
answer is the opposite shape: every stage has a Fedora-hosted default, most have a documented local
alternative, and one does not.

**BUILD.** *bootc: fully operator-controlled, and the tool itself is buildable offline* — any OCI builder
for the image, `cargo build` or `just build` for the tool, and a vendored-dependency tarball published per
release specifically for "air-gapped or restricted network environments". The base image is the one
dependency: Fedora's and CentOS Stream's are public with public build definitions; **RHEL's is behind a
subscription and its derived images may not be publicly redistributed** (§15). DOCUMENTED. **Whether a
third-party rebuild reproduces the published base image: NOT TESTED, and no reproducibility claim exists
to test against. UNKNOWN.** *Fedora CoreOS: operator-controllable, with a real hardware requirement* —
`cosa build`, which "requires access to virtualization - specifically `/dev/kvm`", or plain `podman build`
from the `Containerfile`, which does not. Both consume Fedora content that an offline operator must
mirror, and the production pipeline itself runs in Fedora's infrastructure; the *inputs and tooling* are
public and a local build is documented (§15).

**SIGN.** *bootc: fully operator-controlled, and unusually clean because the mechanism has no opinion.*
An operator signs with their own key through whatever their registry supports — containers/image's policy
language accepts GPG keyrings (`signedBy`) and sigstore signatures (`sigstoreSigned`, including
Fulcio-issued certificates and PKI). Nothing requires a project key, and nothing requires any signature at
all — the same fact read two ways: maximum independence, minimum default safety (§9). **UNKNOWN**: whether
bootc documents key rotation or revocation for an operator-signed fleet anywhere; no such page was found.
*Fedora CoreOS: not operator-controlled for the official stream.* The shipped policy trusts exactly three
named Fedora primary keys for `quay.io/fedora/fedora-coreos`. An operator running official images is
trusting Fedora's keys by design and cannot substitute their own without replacing the policy — possible
via the documented `/dev/null` opt-out, but then nothing is verified, since the `docker` transport's
default scope is `insecureAcceptAnything`. An operator building their *own* Fedora CoreOS would sign it
themselves; no documentation for that path was found. **UNKNOWN.**

**HOST.** *bootc: fully operator-controlled, with three documented transports* — a private registry with
`/etc/ostree/auth.json` credentials and `registries.conf.d` for mirroring and remapping ("Everything in
the section remapping and mirroring images applies to bootc as well"); an `oci:` directory produced by
`skopeo copy docker://… oci:/path/myos.oci` and carried on removable media; or `containers-storage:` from
the local podman store. The USB workflow is documented end to end, is idempotent after the first `bootc
switch --transport oci`, and "can all be automated by creating systemd units that look for a USB device
with a specific label, mount (optionally with LUKS for example), and then trigger the bootc upgrade."
DOCUMENTED, `registries-and-offline.md`; Fedora bootc adds `skopeo sync` for whole-namespace mirroring.
**The strongest air-gap story in this profile, and it required no project infrastructure to begin with.**
*Fedora CoreOS: mostly operator-controllable, with one documented gap.* Install artifacts mirror trivially
(`--image-url`, `--image-file`, `--offline`, `--stream-base-url`, iPXE `BASEURL`) and the update payload is
an ordinary OCI image. **The Cincinnati update graph is the piece with no operator-facing procedure** —
open-source server, shipped `cincinnati.base_url` knob, no standing-it-up guide, and the structural fix
dormant since March 2025 (§15). DOCUMENTED / **UNKNOWN** (the procedure).

**INSTALL.** *bootc: fully operator-controlled and self-contained* — "the container image itself comes
with a baseline self-sufficient installer that sets things up ready to boot", so there is no separate
installer artifact to version or mirror; `to-disk`, `to-filesystem` or `to-existing-root` run from the
image under privileged podman, and `--via-loopback` produces a raw disk image locally. What bootc does
*not* provide is ISO or PXE, so a bare-metal fleet needs a distribution installer (Anaconda plus kickstart
per Fedora bootc) or a disk image from the osbuild tooling (§10). *Fedora CoreOS: fully
operator-controlled* — live ISO, PXE triple, cloud images, or `coreos-installer` from a container on an
existing host, all with a local image file and local Ignition config, and `iso customize` / `pxe
customize` baking everything into operator-held media. DOCUMENTED.

**BOOT.** **No external dependency on either system, at any point.** The bootloader reads local entries,
the deployment is selected by a local kernel argument, and composefs mounts a local object store. The one
caveat runs opposite ways: **Fedora CoreOS is *more* independence-friendly here**, because its shim chains
to a certificate authority already in firmware and needs no enrolment, while **bootc's sealed-UKI path
requires the operator to own a signing key and enrol it** — more independent in principle, more work in
practice (§9).

**CONFIGURE.** *bootc: fully operator-controlled* — image content, `/usr/lib/bootc/kargs.d`, install-time
`--karg`, or `/etc` written by whatever the operator chooses, with nothing routing through any service.
The cost is that bootc supplies no configuration tooling, so the independence is also an obligation (§6).
*Fedora CoreOS: fully operator-controlled* — Ignition fetches from `http`, `https`, `tftp`, `s3`, `arn:`
or `gs`, from a labelled local device, or from platform user-data; integrity is a content hash plus TLS
with operator-supplied CAs; no project service in the path and no signing (§10). DOCUMENTED.

**UPGRADE.** *bootc: fully operator-controlled, and the strongest stage.* `bootc switch` to any transport,
`bootc upgrade` against the operator's registry or a mounted `oci:` directory, with staging controls that
need nothing external either. **There is no update service to replace because there never was one.**
DOCUMENTED. *Fedora CoreOS: operator-controllable in two grades.* The supported, feature-complete path
needs a Cincinnati graph — Fedora-hosted by default, self-hostable in principle without a guide. The
always-available fallback is to stop Zincati and drive `rpm-ostree rebase
ostree-image-signed:docker://<your-mirror>/fedora-coreos:<stream>` by hand, which is exactly the documented
stream-switching procedure, so the mechanics are published even though the use case is not framed that
way. **Taking that fallback gives up phased rollout, wariness, maintenance windows, downgrade protection
and barrier enforcement** — most of what makes Fedora CoreOS's fleet story good. DOCUMENTED.

**ROLLBACK.** **No external dependency on either for the one-step case**: both retained deployments are on
disk, `bootc rollback` or `rpm-ostree rollback -r` is local and offline, and the bootloader menu is local.
**bootc additionally supports arbitrary-version rollback with no network beyond the registry holding the
digest** — and that registry can be an `oci:` directory on a USB stick. Fedora CoreOS's arbitrary-version
case needs a reachable image source and, for anything the graph would normally mediate, an explicit
`allow_downgrade`. One caveat applies to both and is documented on both sides: an active update agent will
undo a rollback unless it is stopped first. DOCUMENTED.

**RECOVER.** *bootc: mostly operator-controlled, with one experimental addition and one structural
absence.* `bootc install reset` gives a factory reset in a fresh stateroot with no network, preserving the
old state for inspection — experimental, and it leaves the old stateroot consuming disk. `bootc
usr-overlay` plus a package manager needs repositories, so an air-gapped operator must bake debugging
tools into the image — trivial when the image is theirs, and not documented as an air-gap caveat. **bootc
ships no recovery media**, so recovery from an unbootable system depends on the distribution. DOCUMENTED /
INFERRED for the air-gap point. *Fedora CoreOS: mostly operator-controlled, with one documented external
dependency.* The live ISO is an ordinary file an operator can mirror and is a complete in-memory recovery
environment; `coreos-installer` reinstalls from local media; single-user mode recovers lost access from
the console. **`toolbox` needs to pull a container image**, so an air-gapped operator must pre-mirror it or
lose the documented debugging path — and every documented recovery path requires console access, which for
a remote machine means lights-out management. DOCUMENTED / INFERRED for the toolbox caveat.

### "If the primary commercial sponsor and all of its hosted services disappeared tomorrow?"

**For bootc, almost everything remains, and the reason is architectural rather than contractual**: the
licence, the source, the build system, the vendored dependencies, the CNCF trademark and project assets,
the published documentation, and — critically — **every running fleet**, because nothing in the required
path touches project infrastructure. What would need reconstituting is the maintainer group (§16,
concentrated) and the release automation (public and rebuildable). The material loss would be the base
images: Fedora's would follow Fedora, CentOS Stream's CentOS Stream, and RHEL's is a commercial product.

**For Fedora CoreOS the picture differs, because the project *is* infrastructure.** Remaining: the
licences, the source for every component, `coreos-assembler`, the image configuration, the Cincinnati
server code, the documentation, and every running machine, continuing on its current deployment
indefinitely. Stopping: new releases, the update graph, the signature lookaside, and artifact hosting —
unless mirrored in advance. **The distinction the framework asks to be preserved applies and matters**:
that infrastructure is the Fedora Project's, governed by elected bodies with public proceedings, not a
vendor's; Fedora's own trademark and governance documents establish that, and the Red-Hat-appointed
Council seats and Red-Hat-hired Project Leader are part of the same documented picture (§16). This is an
assessment of documented structure, not a prediction about anybody's behaviour.

**Applied equally.** The same nine stages must be run against every system in this study on identical
terms. This profile makes no claim about how any other system scores; the stages are recorded here so the
test is symmetrical, per the framework's bias controls.

---

## What a full experimental pass needs

The tier calls for the full build / provision / extend / update / break / recover cycle and both
standardized experiment protocols, and this pass ran none of it. This section makes the missing half a
costed decision. The framework's §21 field list (INITIAL STATE, FAILURE INJECTED, EXPECTED BEHAVIOR,
OBSERVED BEHAVIOR, FINAL MACHINE STATE, MANUAL INTERVENTION REQUIRED, DATA LOST, RECOVERY PROCEDURE, TIME
TO RECOVERY) is the right report shape; nothing has ratified it as the template for this tier.

**A structural note first: this profile needs *two* experiment tracks, not one.** bootc and Fedora CoreOS
are different kinds of object and one test plan cannot cover both. The bootc track is build-centric and
starts with a Containerfile; the Fedora CoreOS track is configure-centric and starts with a published
qcow2 and a Butane file. Several of the most valuable experiments exist on only one track.

### Experiments, in rough order of value per unit of effort

1. **Power cut during staging, both backends, on QEMU.** The largest documented gap: bootc's own
   documentation is silent on power loss, upstream OSTree covers the ostree backend, nothing covers
   composefs. Kill the VM mid-download and mid-finalization separately and confirm the machine boots the
   old deployment. Cheap, high value, closes §21 scenario 1 and the one INFERRED claim in §4.
2. **Failed-boot behaviour, to settle the boot-entry-counting UNKNOWN.** Stage an update, break the new
   deployment, and observe whether the ostree backend returns the machine unattended. The documentation
   says the composefs backend does not do this and is silent on ostree; an experiment produces the primary
   source that does not exist. Two variants: immediate panic, and a boot that fails a critical unit.
3. **The `/etc`-does-not-carry-over demonstration.** Change `/etc`, upgrade, roll back, show the change
   disappear; pair it with the mirror case in `/var`. Minutes of work, makes §5's most surprising
   documented behaviour concrete.
4. **Disk full.** Fill the root filesystem and attempt an upgrade. §21 scenario 8 is the largest open
   UNKNOWN and is architecturally specific to these systems. Also worth testing: `bootc usr-overlay` until
   the tmpfs exhausts.
5. **Upgrade download size, measured.** Two adjacent Fedora CoreOS stable releases, actual bytes
   transferred against the 976 MiB full image; repeat for a derived bootc image with a one-package change.
   Converts §19's central INFERRED claim into a number. Also test whether `zstd:chunked` still breaks the
   composefs backend.
6. **The signature-policy default, demonstrated.** Boot a stock bootc system, point it at an unsigned
   image, show it deploy; then apply a `policy.json` requiring signatures and show it refuse. The
   highest-leverage security fact in the profile, with no worked example anywhere in the documentation —
   the experiment would produce the missing one.
7. **The §22 independence run, bootc track, end to end.** Build a derived image with operator keys, sign
   it, push to a local registry, `skopeo copy` to an `oci:` directory, install with `bootc install to-disk
   --via-loopback`, configure via `/etc`, upgrade from the USB path, roll back, reset. **bootc is the best
   candidate in the whole study for a zero-external-dependency run**, because every stage is documented
   and none requires project infrastructure.
8. **The §22 independence run, Fedora CoreOS track**, to settle the one open question: can an operator
   stand up a Cincinnati graph from the published code without a guide, and does a mirrored payload plus a
   local graph give a fully self-hosted update path? The most valuable Fedora-CoreOS-specific experiment,
   because it is the only stage where the documentation stops.
9. **`bootc install reset`, exercised.** Confirm the fresh `/etc` and empty `/var`, confirm the old
   stateroot is readable, measure the disk cost. Experimental, the only factory reset either system has,
   and apparently unwritten-up outside the project.
10. **Sealed UKI end to end.** Build with `bootc container split-kernel-and-rootfs` and `bootc container
    ukify`, enrol keys, boot under Secure Boot, tamper with the root, confirm the failure. The strongest
    integrity claim in the profile and the one most in need of verification — and the hardest, needing ext4
    or btrfs (not the default XFS), systemd-boot without bootupd, and firmware that models Secure Boot
    properly.
11. **Kubernetes-aware rollout.** Flight Control's batch success thresholds and disruption budgets, or
    `bootc-operator`'s cordon/drain state machine, against the §21 scenario 4 case. Needs a cluster, so it
    is expensive and last — but it is the only way to test the layer that closes both systems'
    automatic-rollback gap.

### Infrastructure, and the honest cost of each option

**Option A: Fedora CoreOS on local QEMU/KVM. Viable, cheap, and the project ships a production image for
it.** Every release publishes `qemu.x86_64.qcow2.xz` (976 MiB compressed, 1.96 GiB expanded, a 10 GiB
virtual disk) plus a live ISO (1027 MiB) and a PXE triple (1018 MiB); Ignition reaches QEMU through the
`opt/com.coreos/config` fw_cfg key, with a documented `provisioning-libvirt` page. OBSERVED, stream
metadata. **This is a materially comparable story to a project shipping a ready-to-run QEMU image**: no
build required, a supported production artifact rather than a development variant, about 1 GB of download.
Experiments 1–5 and 8 on the Fedora CoreOS track fit here. Cost: a host with KVM and roughly 2 GB of disk
per VM.

**Option B: bootc on local VMs via `bcvk`. The equivalent story for the mechanism, and better than expected
on privileges.** [bootc-dev/bcvk](https://github.com/bootc-dev/bcvk), Apache-2.0, latest release v0.19.0
(2026-08-24), is the actively maintained successor to `podman-bootc` — **which is archived, and any plan
naming it should be corrected.** Its README states the key property: "This doesn't require any privileges,
it's just a wrapper for `podman`. It does require a virt stack (qemu, virtiofsd) in the host environment."
`bcvk ephemeral run-ssh quay.io/fedora/fedora-bootc:44` boots a VM and drops you in a shell. Documented
host requirements: QEMU/KVM, `qemu-img`, `virtiofsd`, podman, `openssh-clients`, optionally libvirt for
persistent VMs; target images must contain systemd, `binutils`, `bubblewrap` and `openssh-clients`;
packaged in Fedora 42+ and EPEL 9/10 (`dnf install bcvk`); Linux only. DOCUMENTED / OBSERVED.

**One `bcvk` caveat is decisive for experiment design and is documented by the project itself.** It
distinguishes four ways to run a bootc container, and `bcvk ephemeral` is not an install: "`bcvk
ephemeral` - Run as a virtual machine, but *not* a true 'bootc install'. Uses the kernel in the
container." **So `bcvk ephemeral` cannot exercise the install, upgrade, rollback or boot-failure paths,
which is most of §21.** For those, `bcvk to-disk` or `bcvk libvirt run` is needed — both wrap `bootc
install to-disk` inside an ephemeral VM, which is how bcvk keeps the unprivileged property. `bcvk libvirt
run` defaults to 2 GB RAM, 2 CPUs and a 20 GB disk. DOCUMENTED.

**Option C: disk-image building via osbuild.** Needed for ISO, AMI, vmdk and anaconda-iso outputs. **The
repository moved**: `osbuild/bootc-image-builder` is archived and merged into `osbuild/image-builder`, and
the migration guide at the destination is currently an empty heading. OBSERVED. The documented invocation
is **privileged podman** with `/var/lib/containers/storage` bind-mounted and `--security-opt
label=type:unconfined_t`, plus `osbuild-selinux` installed on the host under enforcing SELinux; Fedora
images need `--rootfs <type>` because "some images (like fedora) do not have a default root filesystem
type"; macOS needs a rootful podman machine. An **experimental rootless path exists and uses KVM**, via
`--in-vm` and the user's own container storage. Cross-architecture builds are experimental and require the
builder image and target image architectures to match. **Host RAM and disk requirements are not published.
UNKNOWN** — budget at least 1 GiB of registry pull per base image plus roughly 1.7–2 GiB expanded in
container storage plus the output artifact, which is arithmetic from the measured figures in §19 rather
than a published requirement.

**Option D: rebuilding Fedora CoreOS with `coreos-assembler`.** Needed only for experiments requiring a
modified Fedora CoreOS. **Requires `/dev/kvm`**, with `--privileged` but explicitly rootless,
`--device=/dev/kvm --device=/dev/fuse` and `--security-opt=label=disable`; the only published resource
figure is an OpenShift pod requesting 3 GiB with "Today COSA hardcodes 2048 for launching VMs". **Disk
requirement undocumented. UNKNOWN.** The `podman build` path from the `Containerfile` avoids KVM entirely
and needs `--cap-add=all --device /dev/fuse --security-opt=label=disable` (§15).

**Option E: a cloud account.** Needed only for provider-specific provisioning behaviour — IMDS-delivered
Ignition, per-cloud Afterburn behaviour, AMI launches, cloud serial-console recovery. **The core lifecycle
of both systems is fully exercisable without one**, making the epic's cloud-budget decision much less
load-bearing here than for the hyperscaler profiles.

**Option F: a Kubernetes cluster.** Needed only for experiment 11. Flight Control is self-hostable
*without* Kubernetes via Podman Quadlets, which lowers the bar considerably for testing rollout policies
and disruption budgets; `bootc-operator` and `poseidon/fleetlock` both need a cluster.

### The decisions that block the experiment pass

All four are recorded on the research epic, raised from
the platform-profile task and extended from
the platform-profile task, and are not re-derived: (1) ratify an
experiment-report template for this tier; (2) decide whether a local-QEMU or dev-variant result counts as
REPRODUCED or only as evidence about the mechanism; (3) decide whether real cloud infrastructure is in
scope and with what budget cap; (4) decide build-host allocation for multi-hour, tens-of-GB builds — to
which Flatcar added the constraint that its SDK needs privileged Docker with `/dev` bind-mounted.

**What bootc and Fedora CoreOS add to each:**

- **To (1), one genuine addition: this profile needs two report templates, or one with a
  mechanism/vehicle axis.** Every other platform in the study is a single object. Here, "what happens when
  power is cut" has two answers depending on the storage backend, and "how do I build this" has two
  answers depending on whether you are configuring an image or deriving one. A template assuming one
  system under test will silently collapse the distinction this profile exists to preserve.
- **To (2), a softening and a sharpening.** *Softening*: Fedora CoreOS publishes a **supported production
  `qcow2`** with every release, so the dev-variant objection does not apply — it is the same artifact a
  user would run in production. *Sharpening, specific to bootc*: `bcvk ephemeral` is documented as "**not
  a true 'bootc install'**", so a result obtained that way is evidence about the *image*, not the
  install/upgrade/rollback machinery. The decision needs a third category beyond "QEMU" and "bare metal":
  **"ran in a VM that was properly installed" versus "ran in a VM that booted the container's kernel
  directly."** Conflating them produces results that look like §21 answers and are not.
- **To (3), much less urgent than for the hyperscaler profiles.** Both core lifecycles run locally with no
  account. If the epic wants one platform to prove the §22 protocol end to end on zero budget, bootc is
  the strongest candidate in the study, because its architecture has no hosted dependency to begin with.
- **To (4), three distinct new constraints rather than a bigger number**, to settle before anything is
  scheduled on the test host: **`bcvk` needs no root but does need a working virt stack** (qemu, virtiofsd) and
  KVM — a sandbox and device-access question, not a disk question; **`coreos-assembler` hard-requires
  `/dev/kvm`** and runs privileged-but-rootless, with nested virtualization named as the fallback inside a
  VM and an undocumented disk requirement, making it the largest unpriced item in the plan; and **the
  osbuild image builder needs privileged podman with `/var/lib/containers/storage` bind-mounted** plus
  `osbuild-selinux` under enforcing SELinux, with a KVM-based rootless path. The last is the same *class*
  of constraint Flatcar raised and should be answered once for both.

---

## Follow-up research

The Pulse baselines' open questions stand and are not repeated; these are additional or sharpened, and
several are good candidates for a maintainer factual-correction pass.

**bootc, the mechanism**

1. **What happens on power loss during staging and finalization on the composefs backend?** (§4, §21.1)
2. **Does the ostree backend enable systemd boot-entry counting by default?** This determines whether a
   bootc system has *any* unattended recovery from a bad boot. (§4, §5, §21.3)
3. **How many deployments are retained by default, and is there a bootc-side way to pin one?** (§5)
4. **Is there a plan to publish signed release artifacts, an SBOM, or build provenance?** CLOMonitor
   scores signed releases 0 of 5 and SBOM false; the OpenSSF reproducibility criterion is unanswered.
   (§15, §17)
5. **What is the security disclosure process in practice — embargo window, CVE assignment, distributor
   notification, SRT roster?** None is documented and there are zero published advisories. (§17)
6. **Is a bootc-specific `containers-policy.json` example planned?** (§9)
7. **What is the supported way to replace the kernel package in a derived image?** (§3, §8)
8. **Is PXE or netboot in scope?** The words appear as neither feature nor non-goal. (§10)
9. **Will `bootc config-diff` become generally available?** It is hidden, ostree-backend-broken, and has a
   `TODO` in its man page. (§1)
10. **What is the timeline for the composefs backend to leave experimental**, given it is "close to
    stabilization" with an in-place-upgrade commitment since 1.16.0 but named stability blockers? (§1, §9)
11. **When does the podman hard-binding land, and what exactly breaks?** The largest documented
    forward-looking change in the family. (§16)
12. **What is the state and roadmap of `bootc-operator`?** (§7, §11)
13. **Does the man page's "daily updates" claim or the shipped 8-hour timer govern?** (§11)

**Fedora CoreOS, the vehicle**

14. **Can an operator actually stand up a Cincinnati graph server from the published code?** The only stage
    of §22 where the documentation stops. (§15, §22)
15. **Is the OCI-native update graph still planned?** Dormant since March 2025, and the change that would
    remove the graph-server dependency entirely. (§15, §18)
16. **Will SBOMs and sigstore attestations reach the published artifacts?** They exist today only on pruned
    Konflux tenant repositories, while `centos-bootc` publishes them on the consumed image. Does closing
    the gap depend on Konflux phases 2–4? (§15)
17. **Is there a documented path to a host trust store for corporate CA certificates?** (§9, §14)
18. **Is `nmstate` supported?** It ships and has no documentation at all. (§14)
19. **Is any SR-IOV, RDMA, cellular or IPv6-specific guidance planned?** These decide telco, GPU-fabric and
    mobile-edge suitability. (§14)
20. **Is a version-pinning mechanism planned for Zincati?** (§18)
21. **What is the intended device-identity story?** Neither project supplies one; Flight Control does. Is
    that the intended answer for Fedora CoreOS fleets too? (§10)
22. **Will the supported-platforms page be reconciled with the stream metadata?** (§8)
23. **Is a working-group membership list with affiliations planned?** The quorum rules reference a
    membership defined nowhere. (§16)
24. **Is journald persistence intentional and permanent?** Set in shipped configuration, documented
    nowhere, and it matters for disk planning. (§12)
25. **Is `sos` deliberately excluded?** Absent from the package set and the documentation, while the Fedora
    bootc base image includes it. (§12)

**Both, and the relationship**

26. **What is the technical shape and timeline of the Fedora CoreOS ↔ Fedora bootc unification?** (§18)
27. **What does Fedora CoreOS's build-system change mean for anyone who thought they were not using
    bootc?** (§2)
28. **Is Flight Control's own architecture, governance and independence worth a profile of its own?** (§11)
29. **What is the FIPS position for Fedora bootc?** It ships a page Fedora CoreOS does not, unread here.
    (§3, §9)
30. **Where did the community NVIDIA image land after moving to the CoreOS organization?** (§8)

---

## Bias and scope note

**Tier and method.** Documentation-based architecture study covering all 22 framework dimensions for two
distinct objects — bootc the mechanism and Fedora CoreOS the vehicle — plus the Fedora/CentOS bootc
base-image project where it is the relevant third party. **No machine was booted, no image was built, no
update was applied, no rollback was forced, and nothing was broken on purpose.** Claims are DOCUMENTED,
OBSERVED, INFERRED, UNKNOWN or NOT TESTED / OUT OF TIER SCOPE. **Nothing is REPRODUCED.** OBSERVED is used
narrowly and only for measurements taken on 2026-09-16 against the GitHub API, the GitLab API, the Quay.io
registry API, the Fedora CoreOS stream and build metadata endpoints, CLOMonitor, or the OpenSSF Best
Practices API, with the query named each time.

**Why no experiments.** The scope call was made and posted on the ticket before the research started: this
tier has no ratified experiment-report template, and the four infrastructure decisions gating a real pass
are open on the epic. Rather than invent a protocol inside a profile, this pass does the architecture
study in full and prices the experiment half above, so the gap is an explicit decision with a cost
attached. Same posture as the sibling Bottlerocket and Flatcar profiles.

**Reading published source is in scope; guessing at unpublished internals is not.**
`docs.fedoraproject.org` was behind an Anubis proof-of-work challenge on 2026-09-16, so both Fedora
documentation sets were read from their own public git — `coreos/fedora-coreos-docs` on GitHub and
`fedora/bootc/docs` on GitLab — cited with both source file and rendered URL. Several findings come from
shipped configuration and build source rather than prose: the Fedora CoreOS `policy.json`, the journald
persistence drop-in, the SSH password-disabling drop-in, the `build-args.conf` builder digests, the
`coreos-bootc-delta.yaml` overrides, the partition sizes in the osbuild manifests, the
`bootc-fetch-apply-updates.timer` intervals, the `bootc container lint` check list, and the `bootc
config-diff` backend restriction. Each is labelled DOCUMENTED (source) and linked. **What was not done is
inferring behaviour from lineage.** Both systems sit on OSTree, and OSTree's documented guarantees are
cited as OSTree's, with the transfer to bootc or Fedora CoreOS marked INFERRED where the project itself is
silent.

**No Kairos comparison appears anywhere in this document.** That is deliberate and was checked. The
ticket's own instruction, and the posture of the sibling Bottlerocket and Flatcar profiles, is that a
platform profile documents its subject on its own terms; the comparison across platforms is a later
synthesis step. The framework's independence and governance tests are recorded here in a form that can be
applied symmetrically to every other platform, and §22 says so explicitly, but this profile makes no claim
about how any other system would score.

**No speculation about corporate behaviour.** Red Hat's employment of every listed bootc maintainer, its
ownership of the Fedora trademark, the Red-Hat-appointed Fedora Council seats, the Red-Hat-hired Fedora
Project Leader, the existence of image mode for RHEL and Red Hat Edge Manager, and the RHEL bootc EULA's
redistribution restriction are all recorded as dated, sourced facts. Nothing is inferred from them about
any project's future, and no claim is made about intent.

**Places where UNKNOWN was chosen over inference, deliberately.** Each had a plausible inference available
that was not taken: whether the ostree backend enables boot-entry counting by default (OSTree gained the
capability in a named commit; having a capability and enabling it by default are different claims); what a
full disk does to an update (the shared-filesystem layout makes a confident guess easy and a wrong guess
plausible); power-loss behaviour on the composefs backend (the `/run` staging path suggests an answer, the
project states none); whether the generic OCI-directory air-gap procedure works on an
`rpm-ostree`-driven Fedora CoreOS machine; whether SR-IOV, RDMA, cellular or IPv6-only work on Fedora
CoreOS (NetworkManager and the kernel can do all of these, and that is not the same claim — bonding,
bridging, teaming and VLANs *are* documented with worked examples and are recorded as DOCUMENTED, the rest
are not); whether a third-party rebuild reproduces either published artifact (neither project makes a
bit-for-bit claim, and Fedora CoreOS's own wording is "semantically reproducible"); maintainer and
contributor affiliation for Fedora CoreOS (no affiliation data is published, and guessing employers from
names or commit patterns would be unreliable and inappropriate — for bootc the employer column and
self-declared company fields were used, with the method's limitation stated at the point of use); boot
time, idle memory, idle CPU, upgrade duration and per-CVE response latency for both; the contents of the
Fedora bootc FIPS, network and proxy pages and bootc's `building/dns.md`, whose existence is recorded and
whose substance is not, because they were not read; and Flight Control's architecture, governance and
independence properties.

**Claims that are INFERRED and flagged in place rather than buried:** that a power cut during staging
leaves the running deployment intact on the ostree backend; that disk pressure and OS updates are coupled
because they share a filesystem; that an upgrade's real download is layer-delta-sized rather than
whole-image-sized; that the documented debugging paths on both systems require a network an air-gapped or
network-broken failure has by hypothesis removed; that bootc honours sigstore policy through
containers/image; and that the absence of Konflux provenance on `builds.coreos.fedoraproject.org` is
caused by disk images still being built outside Konflux. Each rests on documented mechanics, none is
stated by the projects, and several are near the top of the experiment list for exactly that reason.

**Four extensions or updates to the Pulse baselines**, stated rather than silently applied. The Pulse
entries were collected 2026-09-15 and are accurate as of that date; each of these is a change or addition
found on 2026-09-16, not a contradiction. (1) **bootc's current release is `v1.16.13`**, one newer than the
baseline's `v1.16.12`. (2) **`bootc-image-builder`'s repository is archived** and merged into
`osbuild/image-builder`, and **`podman-bootc` is archived** in favour of `bcvk`; both matter for costing an
experiment pass, and documentation on both sides still points at the archived repositories. (3) **bootc has
an experimental factory reset**, `bootc install reset`, recorded in the Pulse entry as not-applicable for a
mechanism, and more interesting than a wipe because it resets into a new stateroot and preserves the old.
(4) **An early-development Kubernetes operator, `bootc-dev/bootc-operator`, now exists** in the same
organization with no releases cut, against the Pulse entry's "none; stated as a roadmap goal".

**One finding that sharpens rather than contradicts both baselines, and is the most important single fact
in this profile.** The two entries are separate because a mechanism and a distribution are not peers, and
that reasoning holds. But the relationship is closer than either baseline's prose suggests: **Fedora CoreOS
is now built from a Fedora bootc base image, assembled with `podman build` in Konflux, ships the `bootc`
binary, and carries `LABEL containers.bootc=1` — while still applying its updates with Zincati and
rpm-ostree.** Both halves of that sentence are load-bearing, and a summary dropping either will mislead.
