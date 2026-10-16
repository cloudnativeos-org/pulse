# Kairos: deep-core platform profile (documentation pass)

Part of the Reproducible Machine State epic
(the research epic).

Research window: 2026-09-16. All sources retrieved on that date unless a line says otherwise.

Kairos version examined: **v4.3.0**, released 2026-09-08, the current stable release.
Where the `master` branch has moved past the release, both states are recorded and the
difference is called out, because an operator runs the release and not the branch.

Refs read (all fetched fresh on 2026-09-16):

| repository | ref | commit |
|---|---|---|
| `kairos-io/kairos` | `origin/master` | `96ef1c97d8c8bb0285abea88c03f9ec492830e65` (2026-09-15) |
| `kairos-io/kairos` | `v4.3.0` tag | the released state |
| `kairos-io/kairos-docs` | `origin/main` | `096e2c0713521a49ec2b95c1c2c9b69f500ffc1b` (2026-09-15) |
| `kairos-io/AuroraBoot` | `origin/main` | `d48afc5c1f37fbe4d8e40f7cab6e5c79b76ff2ab` (2026-09-15) |
| `kairos-io/kairos-operator` | `origin/main` | `ca0164da13c7141ad9716fdce84a55773db91137` (2026-09-10) |
| `kairos-io/cluster-api-provider-kairos` | `origin/main` | `e457bf40ac94cd6033653194786564978e13b991` (2026-09-14) |
| `kairos-io/community` | `origin/main` | governance, maintainers, adopters |
| `kairos-io/security` | `origin/main` | `5be0f6ed98e6bffc84a2c3a2b16b0d2239b5504d` (2026-09-10) |
| `kairos-io/hadron` | `origin/main` | `4ffdf3cf6866cd0e810b964d82263b91b406d9fc` (2026-09-15), plus the Secure Boot key-ownership task's artifact reading |
| `kairos-io/immucore` | `origin/main` | archived 2026-08-19, superseded by `kairos/immucore/` |
| `kairos-io/kairos-agent` | `origin/main` | archived 2026-08-19, superseded by `kairos/agent/` |

One structural fact shapes every source citation below. Kairos consolidated into a
monorepo between 2026-08-18 and 2026-09-03. `kairos-agent`, `immucore`, `kairos-init`,
`kairos-sdk` and several providers are now directories inside `kairos-io/kairos`, and
their standalone repositories are archived. Any reference in the documentation, or in
earlier research, to a path in `kairos-io/kairos-agent` now points at an archived copy.

---

## Why this document has this shape

No standardized project-profile template survives from
the methodology plan. That ticket closed
and was superseded by the Pulse brief
before it produced one. The NixOS, Unikraft and Azure Linux profiles, and the Secure Boot key-ownership profile
(FR-14), each designed a structure for their own question and recorded that choice in the
document. This one does the same.

The structure here is the research framework's own 22 dimensions, in order. The
sibling tickets had reasons to deviate. This one does not: the brief for this profile says "run all 22
dimensions", and this profile is the anchor the TAG paper pulls from most directly in
the three-way Kairos / bootc / Flatcar comparison. Dimension order also makes the
profile diffable against the other deep-core profiles when they exist.

Two sections do not belong to the framework and are here because the brief for this profile asks for them:
a list of every evaluative comparative claim that needs Mauro's own maintainer review,
and a list of corrections this pass owes to earlier findings in the epic.

## Scope of this pass

**This pass is documentation and source reading only.** The brief's full ask includes a live
build, provision, extend, update, deliberately break, roll back and recover cycle, plus
both standardized experiment protocols from the framework (failure injection, dimension
21; operational independence, dimension 22). Those are explicitly **out of scope here**
and deferred to a follow-up ticket.

The reason is operational, not methodological. The experiments need AuroraBoot and QEMU
on a host that is currently running a multi-day riscv64 build fleet. A collision would
cost both. The pattern this pass follows is the one the Secure Boot key-ownership task already established: do the
part that can be done rigorously, label everything else NOT TESTED, and say exactly what
the missing experiment would settle.

Every dimension below that needs a live machine to confirm carries an explicit
**NOT TESTED** line naming the experiment. Dimensions 21 and 22 are written up as
specifications for that follow-up pass rather than skipped.

### What a follow-up experimental pass must do

This doubles as the spec for the follow-up ticket.

**Infrastructure.** One host with QEMU/KVM and enough disk for several 20 GiB VM images.
A local OCI registry (`zot` or `registry:2`) under the operator's control. A TPM 2.0
emulator (`swtpm`) for the Trusted Boot and encryption paths. An OVMF build with a
writable NVRAM copy per VM, so Secure Boot key state is per-experiment. No network
access from the VM network for the air-gap runs.

**Baseline runs, before any failure injection.**

1. Install `kairos-hadron` v4.3.0 from the official ISO to a blank disk, unattended, with
   a known cloud-config. Record: install duration, resulting partition table and sizes,
   `kairos-agent state` output, `.kairos-state` contents, disk used.
2. Boot, measure time to a usable shell, idle memory, idle CPU.
3. Upgrade to a derived image built locally. Record download size, upgrade duration,
   reboot duration, and whether the ESP changed (this is the bootloader-refresh question
   in dimension 4; the fix is post-v4.3.0).
4. Roll back by selecting the fallback GRUB entry. Confirm the one-shot semantics: does
   the machine return to the new image on the next unforced boot?
5. Factory reset from the GRUB `state reset (auto)` entry. Confirm what is destroyed.

**Dimension 21 failure experiments**, all ten from the framework, each recorded with
INITIAL STATE, FAILURE INJECTED, EXPECTED BEHAVIOR, OBSERVED BEHAVIOR, FINAL MACHINE
STATE, MANUAL INTERVENTION REQUIRED, DATA LOST, RECOVERY PROCEDURE, TIME TO RECOVERY.
The four that matter most for Kairos specifically, because the source reading below
raises a question the source cannot answer:

- **Power cut during upgrade**, at three points: during OCI pull into `transition.img`,
  between the `active.img` to `passive.img` rename and the `transition.img` to
  `active.img` rename, and during the ESP refresh on a `master` build. The rename window
  is the one to target. The source does a `syscall.Sync()` after the passive rename and
  again after the active rename, so the interesting question is what a machine does when
  it loses power between them, with `active.img` gone and only `transition.img` present.
- **Corrupted new OS image.** Feed a truncated or tampered OCI image on the default
  (non-Trusted-Boot) path, where no signature check runs, and observe where the failure
  surfaces: at extract, at boot, or not at all.
- **Unbootable kernel.** Confirm that boot assessment fires, that it fires exactly once,
  and that the `upgrade_failure` sentinel reaches the booted system.
- **Boot succeeds, workload dead.** Upgrade to an image that boots cleanly but breaks
  k3s. The source says the success criterion is reaching the `boot.before` cloud-init
  stage. Confirm that boot assessment does not fire, and time how long the node stays in
  the cluster as NotReady.

**Dimension 22 operational independence.** Full BUILD, SIGN, HOST, INSTALL, BOOT,
CONFIGURE, UPGRADE, ROLLBACK, RECOVER on operator-controlled infrastructure only, with
`quay.io` and `ghcr.io` blocked at the network level from the second step onward. The
specific questions the documentation cannot answer: can `kairos-init` build an image with
no access to the base distribution's package repositories, and does anything in the
install or upgrade path reach a project-controlled host when the operator has supplied
every artifact.

**Trusted Boot runs, as a separate track.** Everything above again, on a UKI install with
operator-generated keys enrolled in OVMF. The two paths behave differently enough
(signature enforcement, three retries instead of one, no debug shell) that treating them
as one system would be wrong.

## Evidence labels

Per the framework's evidence standard: **DOCUMENTED** (explicit in a primary source),
**REPRODUCED** (independently tested with a documented procedure), **OBSERVED** (measured
in our own experiments), **INFERRED** (reasonable conclusion, not explicitly stated),
**UNKNOWN** (insufficient evidence), **NOT TESTED** (the test has not been performed).

Missing documentation is never treated as proof of absence. Where I grepped the source
and found nothing, I label the grep result DOCUMENTED and the consequence INFERRED, and
I say what I searched.

## Bias control, applied as method

Mauro maintains Kairos. The brief for this profile states the bias control more sharply than the other tickets
in this epic, so it is worth naming what I actually did with it.

**I did not use Kairos's vocabulary as the neutral definition.** Where a Kairos document
uses a word that carries a strong claim, I checked what the code does and recorded the
gap. Dimension 4 below carries the clearest case: the architecture page calls Kairos
upgrades "tamper-proof", and the default upgrade path performs no integrity check on the
artifact at all. "Tamper-proof" there means atomic, not verified. That is a terminology
audit, not a bug report, and the other nine projects in this comparison must not be
graded against a word Kairos uses in a narrower sense than a reader would assume.

**I looked for the cost of the flexibility, and found a specific, checkable form of it.**
The shipped configuration branches on the base distribution in at least three places:
persistent bind mounts for Ubuntu/Debian versus the Red Hat family, network management
for SUSE versus everyone else, and service-manager handling for systemd versus OpenRC.
Every advertised base carries its own special cases inside Kairos's own source. That is
what "distro agnostic" costs, and an appliance project with one userspace does not pay
it.

**I checked the Pulse brief negative findings rather than repeating them, and two of them do not
survive contact with the source.** They are corrected below, in Kairos's favour. Applying
the audit honestly means correcting an unfair finding with the same energy as recording a
fair one. The corrections are listed in their own section and repeated inline.

**Where Kairos is genuinely good, it is recorded with the same evidence standard.** The
state file, the phone-home default command set, the boot-failure console handling, and
the candour of the Trusted Boot key documentation are all real, and all cited.

**Every evaluative comparison against another project is flagged.** The framework asks
for comparison and the TAG paper needs it, but Mauro is the maintainer of one of the
projects being compared, and the brief for this profile is explicit that his own authorship does not exempt a
claim from review. Those claims are collected in their own section.

## Contents

The 22 dimensions, in the research framework's own order, then four sections that are not
part of the framework.

1. Definition and implementation of immutability
2. Unit of OS deployment
3. OS construction and customization
4. Upgrade mechanism
5. Rollback and recovery
6. Configuration model
7. Kubernetes coupling
8. Hardware and platform support
9. Security and chain of trust
10. Provisioning and zero-touch deployment
11. Fleet lifecycle
12. Debugging and day-2 operations
13. Persistent state and storage
14. Networking
15. Supply-chain ownership and reproducibility
16. Governance and ownership
17. Project health and sustainability
18. Operational lifecycle and support horizon
19. Resource footprint and performance
20. Extensibility versus constraint
21. Failure experiments (NOT TESTED, specification only)
22. Operational independence experiment (NOT TESTED, specification only)

Then: claims that need Mauro's maintainer review; open questions; where Kairos fits and
where it does not; corrections this pass owes to earlier findings in this epic; method and
limits.

**If you read only one dimension, read 4.** The upgrade mechanism is where the
documentation and the code diverge most, and where the bias-control instruction has the
most to bite on.

---

## 1. Definition and implementation of immutability

**What is immutable.** The root filesystem, and only the root filesystem. It is a
fixed-size `ext2` file named `active.img`, held inside the `COS_STATE` partition and
mounted read-only over a loopback device. It is not a partition, not a squashfs, and not
an OSTree-style hardlink farm. Source:
`kairos-io/kairos` `origin/master:sdk/constants/constants.go:47`
(`LinuxImgFs = "ext2" // Default filesystem type for Linux IMAGES. Used for
active/passive/recovery.img`) and the GRUB entry template at
`origin/master:kairos-init/pkg/bundled/bundled.go:347-359`, which does
`loopback loop0 /$img` against `/cOS/active.img`. Evidence: **DOCUMENTED**.

**What enforces it.** A read-only mount. Nothing else. There is no dm-verity on the OS
root, no IMA policy, no runtime re-verification of any kind. A grep of the whole
repository for digest handling in the OS-image path returns matches only in
`sdk/utils/image/rawextension.go`, which verifies the digest of a raw *system extension*
layer against its manifest. The OS root image itself is never digest-checked, at install
or at boot. Evidence: **DOCUMENTED** for the greps; **INFERRED** for the consequence.

The consequence is worth stating plainly, because "immutable" is the category word and
this is where Kairos's version of it differs from the verity-based systems. Read-only
mounting is a **tamper-prevention** measure against the running system's own processes.
It is not **tamper detection**. Anyone with offline access to the disk, or with the
ability to modify `/cOS/active.img` from a recovery boot, changes the OS and nothing
notices on the next boot. Talos, Bottlerocket and Flatcar all put dm-verity under the
root on at least some paths; Kairos does not, on either path.
[Evaluative comparison, flagged for review: **C-01**.]

**What is writable and discarded.** An overlayfs on tmpfs covers `/var`, `/etc` and
`/srv` in the shipped configuration, sized at 25% of RAM. Source:
`origin/master:kairos-init/pkg/bundled/cloudconfigs/00_rootfs.yaml`
(`OVERLAY: "tmpfs:25%"`, `RW_PATHS: "/var /etc /srv"`). Changes to these paths vanish on
reboot unless a sub-path is also listed as persistent. Evidence: **DOCUMENTED**.

**What is writable and persists.** `/usr/local` is the mount point for the whole
`COS_PERSISTENT` partition. On top of that, a list of 37 specific paths is
bind-mounted out of `/usr/local/.state` back into the overlay, so they survive reboot and
upgrade. The list is in the same `00_rootfs.yaml`: `/etc/ssh`, `/etc/kubernetes`,
`/etc/rancher`, `/etc/ssl/certs`, `/etc/ssl/private`, `/home`, `/opt`, `/root`,
`/var/lib/containerd`, `/var/lib/etcd`, `/var/lib/kubelet`, `/var/lib/rancher`,
`/var/log` and others. `/oem` is a separate 64 MiB partition holding the cloud
configuration. Evidence: **DOCUMENTED**.

**What persists across an upgrade.** Everything in the paragraph above. The OCI image
replaces the root image file wholesale, and nothing under `/usr/local`, `/oem` or a
bind-mounted state path is touched. Evidence: **DOCUMENTED** from
`origin/master:agent/pkg/action/upgrade.go`, which only ever writes inside `COS_STATE`,
`COS_RECOVERY` and the ESP.

**Can the running OS be modified?** Yes, in three distinct ways, and they have different
characters.

1. **System extensions.** `systemd-sysext` images layer over `/usr` and persist across
   reboot and upgrade (they live under `/var/lib/extensions`, a persistent state path).
   This is the sanctioned mechanism and it directly contradicts the architecture page's
   flat statement that "after installation it's not possible to add additional packages
   to the system". Both statements are on the same documentation site. Evidence:
   **DOCUMENTED**.
2. **Anything under a persistent path.** `/usr/local`, `/opt`, `/home`,
   `/var/lib/containerd` and the rest are ordinary read-write filesystems. A binary
   dropped in `/usr/local/bin` on one node and not another is drift, and nothing in the
   system detects it.
3. **The kernel command line.** `rd.immucore.debugrw` mounts the root image read-write,
   and the component README says of it: "Note that this completely breaks the concept of
   an immutable root." `rd.immucore.disable` turns the whole mechanism off. Source:
   `origin/master:immucore/README.md`. These flags are documented only in that README,
   not on the documentation site. Evidence: **DOCUMENTED**.

Point 3 matters more than it looks, because on the default GRUB path the boot menu has no
password. The shipped GRUB configuration
(`origin/master:kairos-init/pkg/bundled/bundled.go:337-410`) sets no `superusers` and no
`password_pbkdf2`. A grep of the whole tree for GRUB password configuration returns
nothing. So anyone with console access can press `e`, add `rd.immucore.debugrw`, and boot
a writable root. The same menu offers a `state reset (auto)` entry that appends
`kairos.reset` to the command line, which starts `kairos-agent reset --unattended
--reboot` with no confirmation and, by default, formats the persistent partition
(`origin/master:kairos-init/pkg/bundled/cloudconfigs/51_reset.yaml`;
`origin/master:agent/pkg/config/spec.go:555` sets `FormatPersistent: true`). Physical
access is therefore a one-keypress full data wipe, and a one-keypress mutable root.
Evidence: **DOCUMENTED** for the configuration; **INFERRED** for the attack, which was
not performed. **NOT TESTED**: boot a VM, press `e`, and confirm both. Under Trusted Boot
this closes, because the command line is measured into PCR 11 and a modified command line
breaks the TPM-bound unlock.

**Can configuration drift occur?** Yes, and the honest answer has a nuance that
the Pulse brief got slightly wrong.

There *is* a periodic reconciliation hook. `cos-setup-reconcile.timer` runs
`kairos-agent run-stage reconcile` at `OnBootSec=5min` and `OnUnitActiveSec=60min`, with
an OpenRC equivalent. Source:
`origin/master:kairos-init/pkg/bundled/cloudconfigs/09_systemd_services.yaml:114-127` and
`09_openrc_services.yaml:38-53`. The Pulse profile records "There is no reconciliation
loop", and that is too strong: the loop exists and is enabled by default.

What the loop does *not* do is reconcile anything by itself. No shipped cloud
configuration defines a `reconcile:` stage (grep of
`kairos-init/pkg/bundled/cloudconfigs/` returns nothing). It is a scheduled hook the
operator can hang work on. It compares nothing, detects nothing and corrects nothing on
its own. So the corrected finding is: **Kairos ships a periodic stage-execution timer and
no drift detection.** Evidence: **DOCUMENTED**. That is a meaningfully different fact
from "no reconciliation loop", because an operator can build convergence on top of the
timer without writing their own scheduler.

**Does a version uniquely identify machine state?** No, and this is the most significant
finding in this dimension.

Three things break the identity. First, the persistent partition and the 37 state paths
are outside the image entirely. Second, system extensions and cloud-config stages run
after the image is laid down, so two machines from the same image and different
configurations are different machines. Third, and least obvious: **the machine never
records the content digest of the image it is running.** A grep of `agent/pkg` and
`sdk/types/images` for `digest` or `Digest` returns no matches at all. The state file
(`origin/master:agent/pkg/state/state.go`) records `first-install-source`,
`last-active-source`, `last-recovery-source` and `last-reset-source`, and each is the
*reference string* the operator supplied. If that was a mutable tag such as
`quay.io/kairos/hadron:v4.3.0`, the machine has no record of which bits it actually
received. Evidence: **DOCUMENTED** for the grep and the struct; **INFERRED** for the
consequence.

This is a genuine reproducibility gap in a project whose main artifact claim is that the
OS is an OCI image. OCI images are content-addressable. Kairos uses that property for
distribution and does not carry it onto the machine.
[Evaluative comparison against OSTree-based and Talos-style systems, flagged: **C-02**.]

**How can an operator determine the actual state of a running machine?** Better than the
paragraph above implies, and this deserves credit. Two mechanisms exist and both are
node-local.

`kairos-agent state` returns a structured document
(`origin/master:sdk/state/state.go:45-104`) with the flavor, the Kairos version, the init
system, whether Secure Boot is on, the enrolled EFI certificates, every Kairos partition
with its size, filesystem, mount point, UUID and read-only flag, which slot the machine
booted from (active, passive, recovery, live), whether it is running in RAM, which
partitions are encrypted, and full `sysinfo` hardware data. That is a more complete
machine-state answer than most systems give from a single local command.

`.kairos-state` on the persistent partition
(`origin/master:agent/pkg/state/state.go`) is a small YAML file recording first install,
last active upgrade, last recovery upgrade and last reset, each with a timestamp and the
image source. It is human-readable and it survives reboot.

The gap is that neither reports a digest, neither enumerates installed system extensions
in the same view, and neither compares the running state against an intended state.
Evidence: **DOCUMENTED**.

**Two size constants that appear only in source, and one correction to earlier research.**
The root image constant is 3072 MiB (`sdk/constants/constants.go:58`) and the OEM
partition is 64 MiB (`OEMSize = uint(64)`). Neither appears in the documentation.

The Pulse brief records the 3072 figure as "a 3072 MiB ceiling on the root image". **It is not a
ceiling.** `agent/pkg/config/spec.go:173-182` seeds the three images at 3072 and then
overwrites all three with the measured source size, from a heuristic at `spec.go:879-942`
(compressed layer sum times 2.5 for a registry source, tar size times 2.0 for an OCI file,
plus 100 MiB). The 3072 default survives only when sizing *fails*, which logs a warning
rather than an error. On upgrade the configured value acts as a floor, not a cap
(`spec.go:431-472` takes the maximum). Evidence: **DOCUMENTED**. Corrected in the
corrections section below.

**Consequences, stated as the framework asks.** Kairos's immutability is a *layout*
guarantee, not a *cryptographic* one. It buys atomic whole-root replacement, a trivially
understandable mental model (one file, swapped), and the ability to use any base
distribution, because the mechanism is indifferent to what is inside the image. It gives
up integrity verification at rest, drift detection, and the property that a version
string pins a machine. For a fleet where the operator controls physical access and cares
most about "every node runs the same image and I can swap it", that trade is sound. For
a fleet where nodes are physically exposed, or where an auditor asks "prove this node is
running the image you say it is", it is not sufficient on the default path, and Trusted
Boot is the answer the project offers.

## 2. Unit of OS deployment

**The artifact is an OCI image, and everything else is derived from it.** That claim is
made in the documentation ("Bootable images are standard OCI artifacts that can be hosted
in any container registry",
`kairos-io/kairos-docs` `origin/main:docs/architecture/container.md:15`) and it survives
being checked against the code.

There is one unpack primitive and everything funnels through it.
`sdk/utils/image/image.go:143-183` extracts an OCI image onto a directory with
`mutate.Extract` and containerd's `archive.Apply`.
`agent/pkg/elemental/elemental.go:361-425` creates a fixed-size file, makes a filesystem
in it, mounts it, and unpacks the OCI rootfs into it: that is the OCI-to-`active.img`
step. In AuroraBoot, `deployer/steps.go:96-102` unpacks into a temporary rootfs and
**every other artifact step declares a dependency on it**: the ISO, the raw disk, the MBR
raw image, and, transitively, netboot, GCE, VHD and MAAS, which are conversions of the ISO
or the raw disk. The UKI path is the same source, a different packaging. Evidence:
**OBSERVED**.

So the claim "one artifact, many shapes" is true in a strong sense: there is no second
source of truth for what gets installed.

**The root filesystem it is unpacked into.** `ext2` for the image files
(`sdk/constants/constants.go:47`), `ext4` for the partitions (`:48`), `vfat` for the ESP.
The recovery image is conditional: squashfs if the live medium provides one, otherwise an
ext2 copy of the active image (`agent/pkg/config/spec.go:133-144`). Current AuroraBoot
ISOs do not produce a `recovery.squashfs`, so the ext2 branch is what runs today.
Evidence: **OBSERVED**; **INFERRED** for the squashfs branch being legacy.

### Registry properties, checked rather than assumed

| property | answer | evidence |
|---|---|---|
| standard registry | **yes**. go-containerregistry `remote.Image` with `authn.DefaultKeychain`, so any OCI registry and the normal credential chain | **OBSERVED**, `sdk/utils/image/image.go:282-294` |
| mirrorable | **yes**, by ordinary registry copy. `--allow-insecure-registries` covers internal and self-signed registries | **OBSERVED** |
| content-addressable | **partially, and not used on the machine** | see below |
| signable | **yes for release artifacts; off by default for node-side verification** | dimension 4 |
| independently buildable | **yes**. `images/Dockerfile` takes `BASE_IMAGE`, `MODEL`, `KUBERNETES_DISTRO`, `KUBERNETES_VERSION`, `TRUSTED_BOOT`, `FIPS` and `VERSION`; three documented pipeline paths | **DOCUMENTED**, `docs/reference/byoi.md:19-51` |
| kernel, initrd and userspace together | **yes**. `kairos-init` installs the kernel package and generates the initrd inside the image | **OBSERVED**, `kairos-init/pkg/values/values.go:136-146` |

**The content-addressability answer deserves its own paragraph, because it is the finding
that most undercuts the artifact story.** A digest reference is accepted
(`name.ParseReference`), but a bare image name has `:latest` appended
(`sdk/types/images/image.go:124-126`), and **nothing resolves a tag to a digest, stores a
digest, or compares one**. What install and upgrade record is the source *string*
(`agent/pkg/action/install.go:65`, `agent/pkg/action/upgrade.go:300-302`). This is the
same finding as in dimension 1, arrived at from the other end: the artifact is
content-addressable in the registry and is not content-addressed on the machine.
Evidence: **OBSERVED**.

### Are boot assets versioned separately?

**No, and that is a deliberate design decision with a written rationale.** Covered in
detail in dimension 4: shim, GRUB and the real `grub.cfg` are all copied out of the OCI
image's own rootfs, because a shim carries the signature of its own distribution and a
generic shim would boot but fail to load the image's kernel. The four exceptions, where an
asset comes from the AuroraBoot container instead, are listed there. Evidence:
**DOCUMENTED**.

### Air-gap

What works with no network at all, each checked in source or documentation:

| operation | offline | evidence |
|---|---|---|
| install from ISO | **yes, zero network**. If `/run/rootfsbase` exists, the install source is `dir:/run/rootfsbase`, the ISO's own squashfs, and shim and GRUB come from that same tree | `agent/pkg/config/spec.go:103,120-122` |
| build an ISO from a locally present image | **yes**. `GetImage` tries the local Docker daemon before the registry | `sdk/utils/image/image.go:270-280` |
| upgrade from a `docker save` tarball | **yes**, `--source ocifile:/path.tar` | `docs/upgrade/manual.md:54-61` |
| upgrade from an extracted directory | **yes**, `--source dir:/path` | `docs/upgrade/manual.md:63-67` |
| upgrade from an internal registry | **yes**, plus `--allow-insecure-registries` | `docs/advanced/private_registry_auth.md:63` |
| bundles from a local file | **yes**, `local_file: true` | `docs/advanced/bundles.md:122` |
| netboot | **no**, network is the transport | |
| `upgrade list-releases` | **no**, it lists registry tags | `agent/pkg/cmd/root.go:142` |
| keyless cosign verification | **no**, it needs Fulcio and Rekor | `agent/pkg/utils/common.go:250-255` |

Evidence: **OBSERVED** and **DOCUMENTED** as marked.

That is a strong offline story for the *runtime* half of the lifecycle, and it is one of
the clearest reasons to choose Kairos for a disconnected fleet. The *build* half is the
gap, and it is covered in dimension 15.

One detail worth pulling out of the table, because it is unusually good and easy to miss:
**installing from the ISO uses the ISO's own squashfs as the image source.** There is no
"boot the installer, then download the real image" step. A USB stick is a complete,
self-contained installation. Evidence: **DOCUMENTED**.

**A gap in the upgrade path, found in source and not documented anywhere.** There is no
free-space pre-check for the state or recovery partition on a GRUB-mode upgrade.
`UpgradeSpec.Sanitize` (`agent/pkg/implementations/spec/spec.go:230-247`) validates the
source and the mount point and nothing else. Install-time and UKI-mode checks do exist
(`agent/pkg/partitioner/disk.go:93-98`, `agent/pkg/uki/space.go:83`,
`agent/pkg/utils/grub_esp_space.go:36-65`). **INFERRED**: an oversized image on a machine
installed with a smaller one fails late with ENOSPC rather than with a sized error
message. **NOT TESTED**; this is experiment 8 in the follow-up spec.

## 3. OS construction and customization

### The base-distribution question, answered precisely

This is the claim the brief for this profile singles out as big and checkable: seven bases advertised, one with
released images. **It holds in substance, and the precise picture is more useful than the
slogan.**

| measure | count | names |
|---|---|---|
| advertised on the kairos.io homepage | **7** | Alpine, Debian, Fedora, Hadron, openSUSE, Rocky, Ubuntu |
| recognised in `kairos-init` code | **14**, plus `unknown` | the above, minus Hadron's absence of package maps, plus AlmaLinux, Oracle Linux, RHEL, Arch, SLES, SLE Micro, Tumbleweed |
| claimed "validated through automated testing" | **8** | by a workflow that has not run since 2026-08-18, see below |
| built per merge in a workflow that actually runs, producing a bootable ISO | **4** | Hadron (3 variants), Ubuntu 20.04, Rocky 9, openSUSE Leap 16.0 |
| with any v4.3.0 artifact in a registry | **2** | Hadron (78 tags); Ubuntu 22.04, Jetson only, 2 tags |
| **with a released ISO** | **1** | **Hadron v0.5.1** |

Evidence: **OBSERVED** for every row.

The homepage source is explicit: `kairos-docs` `origin/main:src/pages/index.tsx:84-96`
defines a variable named `supportedDistributions` with exactly those seven entries, and
the live page renders them. Evidence: **OBSERVED**.

**Three corrections to the slogan, all of which matter.**

**First, the documentation no longer advertises seven; it says the opposite.**
`docs/reference/image_matrix.md:8-10` reads: "As a small open-source team, we now focus
official prebuilt artifacts and docs defaults on Hadron. Other distributions are still
supported and validated through automated testing in `kairos-init`." And at line 43:
"Those flavor repositories are no longer actively updated by the Kairos release pipeline."
The docs-site flavor selector for v4.3.0 offers exactly one option, Hadron v0.5.1
(`docusaurus.config.ts:109-117`). The monorepo README names zero distributions. So the
divergence is specifically **between the marketing homepage and everything else**, not
across the documentation as a whole. Evidence: **OBSERVED**.

The narrowing was announced, by Mauro, in a Kairos blog post dated 2026-02-25: "Starting
with Kairos v4, the Kairos project will publish Hadron-based artifacts only. This decision
allows us to reduce maintenance costs." Evidence: **DOCUMENTED**. This is a stated
decision, not drift, and the profile should say so.

**Second, "only Hadron has released artifacts" is very nearly right and not exact.**
Ubuntu 22.04 ships two v4.3.0 container images for the NVIDIA Jetson Orin NX and AGX Orin,
dated 2026-09-08, at `quay.io/kairos/ubuntu`. They are container images, not ISOs, and not
GitHub release assets. Evidence: **OBSERVED**.

**Third, and this is the most consequential finding in the dimension: the "8 distros
validated by automated testing" claim currently has no running workflow behind it.**

The broad matrix exists, at `origin/master:kairos-init/.github/workflows/test.yml:22-43`,
covering 19 base images across 8 distributions. GitHub Actions never executes it, for two
independent and separately verifiable reasons. GitHub reads workflows only from
`.github/workflows/` at the repository root, and the monorepo README acknowledges exactly
this constraint for the reusable workflows it had to relocate (`README.md:93-95`) while
this file was not relocated. And its trigger is `push: branches: [main]`, while the
monorepo's default branch is `master`. `gh api repos/kairos-io/kairos/actions/workflows`
does not list it and no run named "Tests" appears. The last successful run was in the
now-archived standalone repository, on **2026-08-18**, three weeks before v4.3.0 shipped.
Evidence: **OBSERVED**; **INFERRED** for "no broad multi-distro validation has run since".

That is a supply-chain-of-evidence break created by the monorepo migration, not an
architectural problem, and it is the kind of thing that is invisible from the outside and
obvious from inside the repository. It is also the single most actionable finding in this
profile for the project itself.

**Test depth is asymmetric by roughly an order of magnitude.** From `pr.yaml`: Hadron core
gets 11 QEMU tests (custom partitioning, acceptance, install, install target, insecure
registry, partition validation, reset, upgrade with CLI, bundles, SSH hardening, upgrade
to latest). Hadron FIPS gets 2. Ubuntu 20.04 gets 2. Rocky 9 gets 1, SELinux only.
openSUSE Leap 16.0 gets 1, SELinux only. Alpine, Debian, Fedora, AlmaLinux, Oracle Linux,
Arch and SLES get **zero** coverage in any executing workflow. Evidence: **OBSERVED**.

**Two released artifact classes disappeared between v4.2.0 and v4.3.0.** `v4.2.0`'s
release workflow has a cell with `trusted_boot: true` producing a
`core-amd64-generic-uki` artifact; `origin/master:.github/workflows/release.yaml` has no
such cell, and no `quay.io/kairos/hadron` tag matching `uki`, `trusted` or `fips` exists
for v4.3.0 across all 914 active tags. So **as of the current release there is no prebuilt
Trusted Boot artifact and no prebuilt FIPS artifact**; both are CI-only. Evidence:
**OBSERVED**; **UNKNOWN** whether this is intentional.

That finding interacts directly with dimension 9. Trusted Boot is the only Kairos
configuration with a signed boot chain, and as of v4.3.0 there is no prebuilt artifact for
it. An operator who wants a verified boot chain must build it themselves, which is
consistent with the project's key-ownership position but is not what the architecture page
implies.

**Stale documentation references resolve, which is worse than if they broke.** Current
documentation pages still tell readers to pull
`quay.io/kairos/opensuse:leap-15.6-standard-amd64-generic-v3.5.0-k0s-...`,
`quay.io/kairos/rockylinux:9-core-amd64-generic-v3.4.1`,
`quay.io/kairos/opensuse:leap-15.6-core-amd64-generic-v3.1.2` and
`quay.io/kairos/ubuntu:24.04-standard-amd64-generic-v3.1.2-k3sv1.30.4-k3s1`. All four
return HTTP 200. They are live, seven-month-old, unpatched images recommended by current
pages. `docs/advanced/customizing.md:14` still uses an openSUSE Tumbleweed tag as *the*
worked example for how to customize Kairos. Evidence: **OBSERVED**.

### Where customization happens

| layer | mechanism | survives an A/B upgrade? |
|---|---|---|
| build time | `FROM <base>` plus package manager plus `kairos-init -s install && -s init` | yes, it is the image |
| install time | partition geometry, extra partitions, `extra-dirs-rootfs`, `no-format`, `grub_options.extra_cmdline`, `bind_mounts`, `ephemeral_mounts`, `ssh_hardening` | geometry yes; `extra-dirs-rootfs` **no**, it is recreated only at install |
| first boot | the `first-boot` yip stage, gated by `/usr/local/.kairos/sentinel_firstboot` | the sentinel is on the persistent partition, so the stage **never runs again** |
| runtime, cloud-config | `/oem`, `/usr/local/cloud-config`, `/system/oem`, re-evaluated every boot and every 60 minutes | **yes**, `/oem` is its own partition and the upgrade never writes to it |
| `systemd-sysext` | `kairos-agent sysext install/enable/disable/remove`, stored in `/var/lib/kairos/extensions/{active,passive,recovery,common}` | **yes**, because `/var/lib/kairos` is a persistent state path. **This is inferred from path constants and is undocumented: the word "upgrade" does not appear on the system extensions page at all** |
| bundles | OCI images applied once at install or first boot | **depends entirely on where they wrote**, and no page says so |

Evidence: **DOCUMENTED** except where marked.

**Cloud configuration is unrestricted root code execution, and there are three independent
channels into the boot path.** `agent/pkg/cloudinit/cloudinit.go:22-46` uses upstream yip
with its default plugin set; Kairos registers no allowlist and removes no plugin, so the
`commands` plugin runs arbitrary shell as root. The three channels are: yip files in
`/oem`; `kairos.config_url=` on the kernel command line, fetched at boot with the URL
rendered as a Go template against machine `sysinfo`; and dot-notation stage tokens parsed
straight out of `/proc/cmdline` (`agent/pkg/utils/runstage.go:65-145`). Evidence:
**OBSERVED**.

That is the construction kit's power and its exposure in the same sentence. Combined with
the unauthenticated GRUB menu from dimension 1, console access plus a
`kairos.config_url=` parameter is remote-code-execution-by-design on the default path.

### The framework's customization checklist

| need | where and how | label |
|---|---|---|
| kernel selection and customization | build time only: replace the kernel package, re-link `/boot/vmlinuz`, regenerate the initrd, `depmod -a`. There is an explicit worked example | **DOCUMENTED**, `docs/advanced/customizing.md:89-113` |
| packages | build time, or runtime via sysext | **DOCUMENTED** |
| custom binaries | build time, sysext into `/usr`, or a bundle into a persistent path | **DOCUMENTED** |
| kernel modules | build time. **UKI images deliberately ship without modules and firmware**, because "many EFI firmwares ... refus[e] to boot if the file exceeds 300-400MB", with the documented consequence that "certain hardware components may not function correctly" | **DOCUMENTED**, `docs/announcements/_index.md:46-56` |
| firmware | build time, or a sysext under Trusted Boot | **DOCUMENTED** |
| GPU and NVIDIA drivers | build time, via `--model nvidia-jetson-*`, which adds NVIDIA apt repositories and L4T packages | **DOCUMENTED** and **OBSERVED** |
| filesystem, storage and network drivers | build time. No runtime mechanism beyond sysext | **INFERRED** |
| security and monitoring agents | runtime, via cloud-config, a bundle, a sysext, or a DaemonSet. Anything outside the fixed persistent-path list needs `bind_mounts` | **DOCUMENTED** |
| proprietary software | build time from your own registry, or a bundle (`run://` executes `run.sh` as root) | **DOCUMENTED** |
| FIPS | build time only. **Ubuntu hard-fails** ("FIPS is not supported on Ubuntu without a PRO account and extra packages"), riscv64 hard-fails, and **no prebuilt FIPS artifact ships in v4.3.0** | **DOCUMENTED** and **OBSERVED** |
| corporate CA certificates | runtime. `/etc/ssl/certs` and `/var/lib/ca-certificates` are persistent by default; the Red Hat family additionally gets `/usr/share/pki/trust` | **DOCUMENTED** |
| system services | build time or runtime; `/etc/systemd` is persistent | **DOCUMENTED** |
| container runtimes | k3s or k0s at build time. Replacing containerd is documented and explicitly fragile: "After a Kairos upgrade, the above process has to be repeated" | **DOCUMENTED**, `docs/advanced/coco.md:125` |

**One base-specific constraint deserves to be pulled out, because it shows the default base
is not a neutral substrate.** `docs/advanced/coco.md:24`: "Hadron is musl-only, and the
Kata Containers host binaries ... are still dynamically linked against glibc, so they fail
to `execve` on a Hadron node and the pod sandbox never comes up." Choosing Kairos's own
default base costs glibc compatibility for third-party host binaries. Evidence:
**DOCUMENTED**.

### System extensions, checked against the claimed limits

- **The preview banner is stale.** The page says the feature "is in preview state and only
  available in Kairos v3.4.x releases and alphas", and that text is byte-identical in the
  v4.1.2, v4.2.0 and v4.3.0 versioned copies. No preview marker exists in the code.
  Evidence: **DOCUMENTED**.
- **The `/usr` restriction is real, in two places.** A build-time allowlist regex
  `^usr/*|^/usr/*|^etc/*|^/etc/*` (`sdk/sysext/sysext.go:20`), and a runtime hierarchy
  list restricting the merge to specific `/usr` and `/usr/local` subdirectories
  (`99_sysext.yaml`). `/opt` is deliberately excluded and has its own documentation page.
  Evidence: **OBSERVED**.
- **Signature enforcement is Trusted Boot only, confirmed from three independent angles.**
  The documentation says so ("For non-uki Kairos, the signature is not enforced yet"). The
  `systemd-dissect --validate` call in immucore sits inside an `IsUKI()` branch; on the
  GRUB path the `.raw` is symlinked straight into `/run/extensions`. And the systemd image
  policy differs: `root=signed+absent:usr=signed+absent` under UKI versus
  `root=verity+absent:usr=verity+absent` otherwise, and `verity+absent` accepts an
  unsigned, non-verity raw image. Kairos's own test asserts that the non-UKI policy stays
  that way, with a comment acknowledging it "contradict[s] the Trusted Boot docs".
  Evidence: **OBSERVED**.

  **Net: on the default path a system extension is neither signed nor integrity-checked.**
  Write access to `/var/lib/kairos/extensions` is sufficient to get arbitrary code merged
  into `/usr/bin` at the next boot, and it persists across upgrades.
  `kairos-agent sysext install` accepts a plain `http:` URL with no checksum on the HTTP
  and file paths; only the OCI raw-artifact path verifies size and SHA-256. Evidence:
  **OBSERVED**; **NOT TESTED**.
- **Only the last layer is converted**, per the SDK and the documentation, and whiteouts
  are an open TODO, so a file *deleted* in the last layer is not honoured. The SDK function
  has no caller inside the monorepo; the converter lives in AuroraBoot. Evidence:
  **OBSERVED**; **UNKNOWN** whether AuroraBoot's converter matches.
- **An undocumented feature exists.** `kairos-agent sysext install --catalog/--version`
  defaults to `https://kairos-io.github.io/hadron-layers/releases.json`. The word "catalog"
  appears nowhere in the documentation. Evidence: **OBSERVED**.

### Bundles

An OCI image applied over the filesystem, dispatched on URI scheme. `container:` and
`docker:` extract the **whole** image filesystem with `RootPath` defaulting to `/`, with no
verity, no signature, no allowlist and no layer restriction. `run:` extracts to a temporary
directory, `chmod 0700 run.sh` and executes it as root. `package:`, and anything
unrecognised, goes through `luet`. Evidence: **OBSERVED**,
`sdk/bundles/bundles.go:175-275`.

They run **once**. The first-boot gate is a sentinel on the persistent partition, which
survives reboots and upgrades, so a bundle never re-applies. The documentation says so:
"the installation only happens once. Changing the bundle's configuration block after Kairos
installation is complete, will not have any effect." Failures are swallowed unless
`fail_on_bundles_errors: true`. Evidence: **DOCUMENTED**.

**Whether a bundle survives an upgrade depends entirely on where it wrote, and no page says
so.** Files under a persistent state path survive; files under `/var`, `/etc` or `/srv` but
not under a persistent path are lost at the next reboot; files under `/usr` are wiped by
the A/B upgrade. The only place the consequence is spelled out is the Confidential
Containers page's operational warning. Evidence: **OBSERVED**.

### The bias question, answered

**Can two machines from the same OCI image end up in different states?** Yes, by four
independent routes: per-machine `/oem` configuration re-evaluated on every boot and every
hour; a templated `kairos.config_url=` that can legitimately fetch different configuration
on different hardware; sysexts that merge arbitrary `/usr` content, persist across
upgrades, and are unverified on the default path; and bundles that ran once, at install,
from whatever configuration that machine happened to have. Evidence: **OBSERVED**.

**Does a version tag uniquely identify machine state?** No, for the two reasons already
given: no digest is resolved or recorded, and the tag says nothing about `/oem`, sysexts or
bundle residue, all three of which persist across an upgrade.

**And the documentation asserts the opposite, in the same breath.**
`docs/architecture/immutable.md:87-89`: "**No snowflakes** - All the machines are based on
the same image, configuration settings and behavior" and "Configuration is driven via
cloud-init - There is only one source of truth for the configuration, and that happens at
bootstrap time." Both statements are true of the `/usr` tree and false of the machine as a
whole. This is the sharpest internal contradiction found in this profile, and it is
squarely the kind of vocabulary the bias control tells us not to adopt as the category's
definition. Evidence: **DOCUMENTED**.

**What obligations transfer to an adopter who builds their own image, and does any page
assign them?** Largely not, and this is the same gap the Pulse brief found, confirmed by an
independent search. What exists is framed as *control*, not duty:
`docs/reference/byoi.md:12-16` says "You keep full control over release cadence and patch
windows"; the Factory page offers Grype, Trivy and cosign as "Optional" features with no
statement that skipping them transfers risk; the February 2026 blog post frames the
transfer positively. **No page states that the adopter now owns signing, CVE monitoring and
response, testing, or versioning.** Evidence: **DOCUMENTED** for what exists; the absence
is a search result over `kairos-docs` at `096e2c07`, not proof that no such statement
exists anywhere.

**What build-time-only buys an appliance, stated fairly.** A project that ships one
userspace it builds itself can say "version X equals state X" and mean it, can test the
single shipped configuration exhaustively, and can carry CVE response for the whole
artifact because there is only one artifact. Kairos trades exactly those three properties
for the ability to take an arbitrary base and to change a running node.
[Evaluative comparison, flagged: **C-14**. The Kairos side of each trade is cited above;
the Talos, Bottlerocket and Flatcar sides were not audited in this pass.]

### Where Kairos genuinely excels here, held to the same standard

- **The boot chain is versioned with the OS image**, deliberately, with a written
  engineering rationale, because a shim carries its own distribution's signature.
- **Install from ISO uses the ISO's own squashfs**, so a USB stick is self-contained and
  needs no network.
- **Four upgrade source types, two of them fully offline**, with local-daemon-first image
  resolution.
- **A three-line contract for a candidate base distribution** (`docs/architecture/meta.md:20-31`):
  systemd 256+ and systemd-boot for Trusted Boot; systemd or OpenRC and GRUB otherwise;
  `CONFIG_EFI_STUB` if EFI. That is a genuinely small contract and it is real evidence for
  the meta-distribution claim.
- **The release vulnerability scan is a hard gate on the Go binaries** Kairos itself ships,
  built from the commit under test, with a stated rationale.


## 4. Upgrade mechanism

The whole upgrade state machine is in one file,
`kairos-io/kairos` `origin/master:agent/pkg/action/upgrade.go`. This section is read off
that file, the CLI definition in `origin/master:agent/pkg/cmd/root.go:101-260`, and the
boot-assessment configuration in
`origin/master:kairos-init/pkg/bundled/cloudconfigs/08_grub.yaml`.

### Before the upgrade

**Where the new OS comes from.** Any OCI source: a registry reference, a local OCI
tarball (`oci:`), a directory, or a file. The `--source` flag takes all of them and the
same value can come from `upgrade.system.uri` in the cloud configuration. Evidence:
**DOCUMENTED**.

**Who initiates it.** An operator running `kairos-agent upgrade`; the Kubernetes operator
through a `NodeOpUpgrade` resource; or the phone-home agent, for which `upgrade` is in
the default allowed-command set. Evidence: **DOCUMENTED**.

**Does it need Kubernetes?** No. Evidence: **DOCUMENTED**. The node-local CLI path is
complete.

**Does it need project infrastructure?** Not for the upgrade itself. One sub-command does
reach out: `kairos upgrade list-releases` defaults to `quay.io/kairos`
(`root.go:141`). Release *discovery* depends on the project's registry; release
*application* does not. Evidence: **DOCUMENTED**.

**How is the artifact verified?** On the default path, **it is not**. This is the single
most important fact in this dimension and it holds up under independent verification.

`origin/master:agent/pkg/elemental/elemental.go:432` guards the cosign call with
`if e.config.Cosign {`. `Cosign` is a plain `bool` on the config struct
(`origin/master:sdk/types/config/config.go:47`) with no default anywhere in the tree, so
its Go zero value, `false`, is the default. The `upgrade` command's flag list
(`root.go:105-113`) is `--image` (deprecated), `--source`, `--boot-entry`, `--recovery`,
`--exclude-path` and `--allow-insecure-registries`. There is no `--verify` and no
`--cosign`. An operator who wants verification must put `cosign: true` and `cosign-key:`
into the cloud configuration; the documentation for that is three lines in the
configuration reference
(`kairos-io/kairos-docs` `origin/main:docs/reference/configuration.md:279-281`).
Evidence: **DOCUMENTED**.

Two things make this sharper than "verification is opt-in".

First, the same command offers `--allow-insecure-registries`, described in its own help
text as allowing a registry "served over plain HTTP or presenting an untrusted/self-signed
TLS certificate". So the defaults are: no artifact signature check, and an available
switch to drop transport authentication too.

Second, **the architecture page calls this path "tamper-proof"**. The exact words, at
`kairos-io/kairos-docs` `origin/main:docs/architecture/container.md:14`, are
"**Tamper-proof upgrades** Upgrades are atomic, A/B swaps with fallback mechanisms and
automatic boot assessment", and again at line 22: "This ensures tamper-proof upgrades".
Read carefully, the sentence defines its own term: it means atomic, with fallback. Read
the way a reader comparing operating systems will read it, it says the upgrade resists
tampering, which on the default path it does not. Evidence: **DOCUMENTED** for the
quote; the reading is mine.

This is the clearest instance in this profile of the bias control that the brief for this profile asks for.
"Tamper-proof" is Kairos's word, used in a narrower sense than the category uses it. It
must not become the comparison's definition.
[Flagged for review: **C-03**.]

On the **Trusted Boot (UKI) path the picture reverses.**
`origin/master:agent/pkg/uki/upgrade.go:74-82` calls
`signatures.CheckArtifactSignatureIsValid` on the new `.efi` before anything rotates, and
refuses to proceed with the message that upgrading "would result in an unbootable active
system". So one project ships enforced verification on one path and none by default on
the other, and no documentation page states the difference. Evidence: **DOCUMENTED**.

### During the upgrade

The sequence, from `upgrade.go`:

1. Detect which slot the machine booted from (`state.DetectBootWithVFS`).
2. Mount `COS_STATE` and `COS_RECOVERY` read-write.
3. Run the `before-upgrade` stage.
4. `DeployImage` the source into `transition.img`, a third image file inside the same
   state partition. **The running root is never written to.**
5. Label the images, create any `extra-dirs-rootfs`, relabel SELinux inside the new image
   in a chroot, run `after-upgrade-chroot`.
6. Rebrand the GRUB default entry.
7. (`master` only, not v4.3.0) refresh the ESP.
8. Unmount the new image.
9. **If, and only if, the machine did not boot from passive**: rename `active.img` to
   `passive.img` and re-label it. `syscall.Sync()`.
10. Rename `transition.img` to `active.img`. `syscall.Sync()`.
11. Run `after-upgrade`, which sets the GRUB boot-assessment sentinel.
12. Set the one-shot next boot entry to `active`.
13. Record the event in `.kairos-state`.

Step 9's condition carries a real safety property and the source states the reasoning:
"We dont want to overwrite passive if we are booting from passive as it could mean that
active is broken and we would be overriding a working passive with a broken/unknown
active." That is good engineering and it is worth crediting. Evidence: **DOCUMENTED**.

**What happens to kernel and initrd.** They travel inside the OCI image and are swapped
with it. GRUB loads them from inside the loopback-mounted image
(`linux (loop0)$kernel`), so there is no separate kernel installation step and no
`/boot` to get out of sync. This is a genuine strength of the single-image model.
Evidence: **DOCUMENTED**.

**What happens to the bootloader.** This needs care, because the answer is more
interesting than "the ESP is not touched".

Kairos populates the ESP **from inside the OCI image**, not from a bundled generic
bootloader. `agent/pkg/utils/grub.go:438-528` copies shim and GRUB out of the deployed
rootfs, searching per-distribution paths listed in `sdk/utils/utils.go:329-433`
(`/usr/share/efi/x86_64/shim.efi`, `/usr/lib/shim/shimx64.efi.signed`,
`/boot/efi/EFI/fedora/shim.efi`, and others), and hard-fails with "could not find any
shim file to copy" if none is present. The code says why, at `grub.go:272-280`:

> The shim contains the signature from microsoft and the shim provider (i.e. upstream
> distro like fedora, suse, etc). So if we use the shim+grub from a generic package (i.e.
> ubuntu) it WILL boot with secureboot but when loading the kernel it will fail because
> the kernel is not signed by the shim provider or grub provider

That is a deliberate and correct decision, and it is a genuine strength: the boot chain is
versioned with the OS image rather than with the installer. `EFI/boot/grub.cfg` on the ESP
is a three-line generated stub that chainloads the real configuration from `COS_STATE`,
which itself came from `/etc/cos/grub.cfg` inside the image. Evidence: **DOCUMENTED**.

**The defect is when that copy happens.** At v4.3.0 it happens on install and on reset,
and **not on upgrade**. I verified this independently
rather than taking the Pulse brief word for it. `refreshESP` was introduced by commit
`beaa9cc627cf34999c0d4d2d0c7520bb768f42bf`, "fix(upgrade): refresh the shim, grub and
grub.cfg on the ESP (#4513)", dated 2026-09-11.
`git merge-base --is-ancestor beaa9cc6 v4.3.0` returns non-zero: the commit is **not** an
ancestor of the v4.3.0 tag, which was released 2026-09-08. Evidence: **REPRODUCED**.

So on every currently released Kairos, shim and GRUB on the ESP stay at their
install-time versions for the life of the machine, and the only supported way to refresh
them is a factory reset, which by default also wipes the persistent partition. A GRUB CVE
or a shim rotation does not reach an installed fleet through the normal upgrade path.
The fix is on `master`, unreleased and undocumented as of this date. The `master`
implementation is careful: it skips cleanly with a warning when there is no EFI
partition, when the ESP is too small, or when the image ships no shim, so a tight
partition cannot turn a working upgrade into a boot failure.

So the architecture is right and the lifecycle had a hole in it. The boot assets belong to
the image by design; the upgrade path simply did not carry them across, for the whole
history of the project up to and including the current release. That is a better
characterisation than "Kairos does not version its bootloader", which would be wrong.
[Evaluative comparison against bootc and Flatcar, flagged: **C-04**.]

Four documented exceptions exist where a boot asset is versioned with **AuroraBoot**
rather than with the OCI image, and they are worth naming because they are the seams in
the model: Alpine's GRUB (copied from inside the AuroraBoot container), the systemd-boot
binary and EFI stub used for UKI builds (unless `--sd-boot-in-source` is passed),
Raspberry Pi firmware, and the live ISO's BIOS GRUB configuration. Evidence:
**DOCUMENTED**.

**Power loss halfway through.** **NOT TESTED.** The source gives a partial answer:
`transition.img` is written first and only renamed at the end, so a power cut during the
pull leaves `active.img` intact and a stale transition file that the next run's cleanup
stack removes. The dangerous window is between step 9 and step 10, when `active.img` has
been renamed away and `transition.img` has not yet taken its place. There is a
`syscall.Sync()` on each side of that window but nothing that makes the pair atomic. What
GRUB does when `/cOS/active.img` does not exist is not stated anywhere I found. This is
experiment 1 in the follow-up spec above.

### At reboot

**How the new system is selected.** `SelectBootEntry(config, BootEntryActive)` writes a
one-shot GRUB `next_entry`. The source comment is explicit that it is one-shot: "if
active fails, the normal boot-assessment fallback still applies on subsequent boots."
Evidence: **DOCUMENTED**.

**How a successful boot is determined, and this is the limit of the whole mechanism.**
From `08_grub.yaml`, the `boot.before` stage clears both GRUB sentinels when it runs from
the active image. That is the definition of success: **the system reached an early
cloud-init stage inside the active image.** It means the root mounted and the first
configuration stage ran. It does not mean networking came up. It does not mean Kubernetes
started. It does not mean any workload is healthy. An upgrade that boots cleanly and
leaves the cluster dead is a *successful* boot by this criterion, and no rollback will
fire. This criterion appears only in a comment in a shipped YAML file. Evidence:
**DOCUMENTED**.

**How many attempts.** Exactly one on the GRUB path. The logic in the generated
`grub_boot_assessment` file: after an upgrade, `enable_boot_assessment=yes` is set. On
the first boot, GRUB sets `boot_assessment_tentative=yes` and boots the default. If GRUB
is reached again with both sentinels set, it sets `default="fallback"` and appends
`upgrade_failure` to the passive command line. So: one try, then fallback. Evidence:
**DOCUMENTED**.

On the Trusted Boot path, boot assessment is systemd's own. `08_efi_assessment.yaml`
enables `systemd-bless-boot` and overrides it to remount `/efi` read-write around the
blessing, then strips the `+N-M` counter suffix from `loader.conf` with a `sed` regex.
That is systemd's standard `+tries` convention, so the retry count is whatever number the
entry filename carries when it is written.

**The count is three, and it is hard-coded.**
`agent/pkg/utils/common.go:645-674`, `AddBootAssessment`, renames every loader entry that
does not already carry a counter to `<name>+3.conf`, on install, upgrade and reset. So the
Trusted Boot path allows **three** attempts where the GRUB path allows one. Evidence:
**DOCUMENTED**.

**And there is a dead configuration key next to it.** `UkiMaxEntries = 3` exists at
`agent/pkg/constants/constants.go:112`, is assigned into the config at
`agent/pkg/config/config.go:54`, and is exposed in the schema as `uki-max-entries`. A
repository-wide grep finds **no code that reads it**, and it appears nowhere in the
documentation. The schema advertises a knob that nothing consumes, and the real number is
the literal `+3` above. It is not the only such key: `verify:` is declared in the config
struct and in the schema, documented at
`kairos-io/kairos-docs` `origin/main:docs/reference/configuration.md:280`, and has **no
reader anywhere**. Evidence: **OBSERVED**.

**Is OS health checked? Is Kubernetes health checked?** No and no, on either path.
Evidence: **DOCUMENTED** for the absence of any health hook in the assessment path;
**INFERRED** for the consequence.

### After failure

**Is rollback automatic?** Yes, once, and only for a boot that fails before the
`boot.before` stage. What triggers it is GRUB seeing both sentinels.

**What survives.** The persistent partition, the OEM partition and every state path. The
passive image is the pre-upgrade root, byte for byte, so the rollback target is a real
previous OS and not a reconstruction.

**What happens to Kubernetes state.** `/var/lib/etcd`, `/var/lib/rancher`,
`/var/lib/k0s`, `/var/lib/kubelet` and `/etc/kubernetes` are all persistent state paths,
so cluster state survives a rollback. Whether it survives a *version* rollback of the
Kubernetes distribution is a different question, and it is the adopter's problem: the
Kubernetes version is baked into the image tag, so an OS rollback is also a Kubernetes
rollback, with whatever etcd schema consequences that carries. **NOT TESTED**; no
documentation addresses it. Evidence: **INFERRED**.

**Container images.** `/var/lib/containerd` is persistent, so the local image cache
survives.

### Compared to the other upgrade models

Kairos is A/B plus a dedicated recovery slot, where A and B are files inside one
partition rather than partitions. That choice has two consequences worth recording.

It costs disk, and the cost scales with the image. The state partition is sized at
`(active * 2) + passive + 1000` MiB and the recovery partition at `(recovery * 2) + 200`
MiB (`origin/master:agent/pkg/config/spec.go:220-262`). The doubling is there because the
transition image lives in the same partition as the slots, so the machine must have room
for **three** roots at the moment of an upgrade, not two.

With the measured-size path and the real Hadron core image (about 215 MiB compressed,
times 2.5 plus 100, giving roughly 638 MiB), that is a state partition of about 2,914 MiB
and a recovery partition of about 1,476 MiB: **roughly 4.5 GiB before any user data**. If
size measurement fails and the 3072 MiB default is used, the same arithmetic gives 10,216
MiB and 6,344 MiB: **about 16.3 GiB**. Evidence: **DOCUMENTED** for the formulas and the
measured image size; the arithmetic is **NOT TESTED** against a real install.

The documented minimums do not agree with each other or with that arithmetic. The
quickstart says 8 GB disk bare minimum, 16 GB practical, 32 GB recommended; the multi-disk
page says 14 GB; the Hetzner page says 30 GB; the getting-started guide says 35 GB; the
k0s cluster example says 40 GB. Five numbers, no reconciliation. Evidence: **OBSERVED**.

It buys flexibility. Because the slots are files, resizing them is a file operation and
the partition table does not change, and because the recovery image is a file in its own
partition, recovery is upgradeable independently. An OSTree-style system trades this for
deduplication between versions; Kairos stores two complete roots.
[Evaluative comparison, flagged: **C-05**.]

One more asymmetry, documented in the code but easy to miss: **recovery is upgraded
separately.** The upgrade command prints a warning saying so, and the Kubernetes
`NodeOpUpgrade` resource does not touch recovery unless asked. A fleet that upgrades
normally for two years has a two-year-old recovery image. Evidence: **DOCUMENTED**.

## 5. Rollback and recovery

The framework asks for these as different concepts, and Kairos separates them cleanly.

**Rollback to the previous OS.** Available. Boot the `fallback` GRUB entry, which loads
`/cOS/passive.img`. Evidence: **DOCUMENTED**.

**Number of retained prior versions: exactly one** (two deployments total, counting the
active slot). There is one `passive.img` and the upgrade overwrites it. There is no
version history, no pinning and no multi-version rollback. Corrected per the maintainer
review:
the retention count and the rollback mechanism ARE documented, on the boot_assessment
and architecture/immutable pages. The real gap is narrower: no documented manual-rollback
procedure (`kairos-agent bootentry --select fallback`), and the boot-once `next_entry`
selection is not written down anywhere. Evidence: **DOCUMENTED** from
`agent/pkg/constants/constants.go:62-64` (three image files: active, passive, recovery)
and `upgrade.go`, which renames active over passive on each upgrade.

**Rollback to an arbitrary known version.** Not a first-class operation. The supported
route is to upgrade *to* the old tag, which makes the current version the new passive.
That works and it is arguably cleaner than a version store, but it needs the artifact to
still exist in a registry, so it is network-dependent in a way that a local version
history would not be. Evidence: **INFERRED**.

**Rollback durability.** The boot selection is one-shot, not a durable pin. The source
comment in `upgrade.go` says so. Nothing in the documentation does. An operator who rolls
back and does not then reinstall the old image finds the machine back on the broken
version after the next reboot. Evidence: **DOCUMENTED** for the source; **NOT TESTED**
for the behaviour.

**Documentation of rollback: essentially none.** I searched the full documentation tree
on `kairos-io/kairos-docs` `origin/main` for "rollback" and "roll back". There is
**one** hit, `docs/architecture/container.md:35`, and it is a statement of position, not
a procedure:

> We believe that bringing rollbacks, or incremental patches upgrades increases the
> exposure to infrastructure drift.

Evidence: **DOCUMENTED**. That position is defensible and coherent with the single-image
model. It does not explain why the mechanism that does exist is undocumented: no page
shows the fallback entry, no page states the retention count, no page mentions the
one-shot behaviour. An operator in an outage has to read the GRUB menu and guess.

**Recovery environment.** A dedicated `COS_RECOVERY` partition holding its own bootable
image, selectable from the GRUB menu. It is on local disk, so recovery works with no
network, no media and no management plane. This is a real strength and one of the
clearest ways Kairos differs from systems that recover by re-imaging over the network.
Evidence: **DOCUMENTED**. [Evaluative comparison, flagged: **C-06**.]

**Factory reset.** Two routes: the `state reset (auto)` GRUB entry, or
`kairos-agent reset`. Three facts about it, all from
`origin/master:agent/pkg/action/reset.go` and `origin/master:agent/pkg/config/spec.go`:

1. **It formats the persistent partition by default.** `FormatPersistent: true` at
   `spec.go:555` and again at `:622`. There is no CLI flag to prevent it, and the source
   carries a comment saying so explicitly: "The persistent partition is formatted by
   default during reset ... so there's no useful CLI knob to surface here"
   (`root.go:671-673`).
2. **It is configurable in the cloud configuration**, as `reset.reset-persistent`, and
   that key *is* documented, at
   `kairos-io/kairos-docs` `origin/main:docs/reference/configuration.md:221`. This
   corrects the Pulse brief, which recorded "no flag to prevent it". No CLI flag is correct; no way
   to prevent it is not. Evidence: **DOCUMENTED**.
3. **It also destroys the rollback target, and that is undocumented.** After deploying
   the new active image, reset deploys passive *from the freshly reset active*
   (`spec.go:563-570`: `Source: sdkImages.NewFileSrc(activeFile)`). After a reset there is
   no previous version to roll back to. Evidence: **DOCUMENTED**.

The `state reset (auto)` GRUB entry runs `kairos-agent reset --unattended --reboot`
(`51_reset.yaml`), and `--unattended` is documented as skipping the 60-second wait. So the
destructive path is one unauthenticated menu selection with no confirmation and no delay.

**Local versus network-dependent recovery.** Everything above is local. Upgrade, rollback,
reset, re-key and inspection all work from the node's own command line with no network.
For a disconnected or edge fleet this is the single best thing about the architecture.
Evidence: **DOCUMENTED**.

**Recovery when Kubernetes is unavailable.** Unaffected. The agent does not depend on it.

**Recovery when networking is unavailable.** Unaffected for local recovery. The two
*remote* recovery mechanisms both need network: the peer-to-peer QR pairing path, and the
phone-home WebSocket agent.

**Persistent-data corruption.** Not handled by the OS. There is no checksumming
filesystem in the default layout (`ext4` on persistent,
`sdk/constants/constants.go:48`), no snapshotting, and no integrity check on the
persistent partition. A corrupted `/var/lib/etcd` is the operator's problem. Evidence:
**DOCUMENTED** for the filesystem choice; **INFERRED** for the consequence.

**What is Kairos's definition of a "known-good state"?** Read off the code rather than
the docs, it is: *the active image booted far enough to run the `boot.before` cloud-init
stage.* That is a low bar deliberately, because the project's position is that a
single-image swap is the unit of correctness and anything finer invites drift. The cost
is that the automatic safety net catches unbootable systems only. Every other class of
bad upgrade, a broken workload, a failed network, a Kubernetes version incompatibility,
is outside the definition and outside the mechanism.

## 6. Configuration model

**The model.** One YAML dialect, `yip`, used for everything: installation parameters,
machine configuration, and lifecycle hooks. It is described on one documentation page as
supporting "the standard cloud-init syntax" plus "its own extended syntax". It is not
cloud-init, not Ignition and not a CRD. Source:
`kairos-io/kairos-docs` `origin/main:docs/architecture/cloud-init.md`. Evidence:
**DOCUMENTED**.

**Separating the four configuration layers the framework asks about.** Kairos does not
separate them. The same file format and the same merge path carry image configuration
(baked in at build), machine configuration (`/oem`), runtime configuration
(`/usr/local/cloud-config`) and cluster configuration (the `k3s`/`k0s` blocks). That is a
real simplification and a real loss of separation: there is one blast radius.
Evidence: **DOCUMENTED**; the judgement is mine.

**Sources and merge order**, documented and specific (`cloud-init.md`):

1. `/run/initramfs/live` (live media and netboot only)
2. `/usr/local/cloud-config`
3. `/etc/kairos`
4. `/etc/elemental` (deprecated)
5. `/oem`

Later directories override earlier ones for scalar values. Stages are the exception and
are **additive**: "When the same stage is defined in more than one cloud config files, all
definitions will be respected." Within a directory, files are processed in lexicographic
order, which is why the shipped files are numbered `00_` to `99_`. Evidence:
**DOCUMENTED**.

**Datasources.** Thirteen providers are configured in the shipped
`00_datasource.yaml`: `cdrom`, `gcp`, `openstack`, `aws`, `azure`, `hetzner`, `packet`,
`vultr`, `digitalocean`, `metaldata`, `vmware`, `config-drive`, `maas`. The
documentation never enumerates them. Evidence: **DOCUMENTED**.

**Stages.** The documented stage list is long and genuinely expressive: `rootfs`,
`initramfs`, `boot`, `fs`, `network`, `reconcile`, plus `before`/`after` sub-stages on
each of those, plus lifecycle stages for install, upgrade and reset (and separate
UKI-only variants of each). A user can hook almost any point of the machine lifecycle,
including reverting something the base image itself configured, and the documentation
gives a worked example of exactly that. Evidence: **DOCUMENTED**. This is one of the
places where the construction-kit posture pays off clearly.

**Declarative or imperative.** Mixed, and in practice mostly imperative. The shipped
configurations use `commands:` blocks with shell, `if:` guards that are shell
expressions, `sed -i`, `systemctl` calls and here-documents. `yip` has declarative
primitives (`files:`, `directories:`, `systemctl:`, `layout:`) and they are used, but a
substantial part of what the system does to itself is a shell script in a YAML field.
Evidence: **DOCUMENTED** from the shipped configurations.

**Idempotency.** Not guaranteed by the model. It is the author's responsibility, and the
shipped configurations show the pattern: `test -f /etc/ssh/ssh_host_rsa_key || ssh-keygen
...` in `08_ssh.yaml`, with a comment explaining that the guard exists so later boots do
not clobber pinned fingerprints. Stages re-run at every boot, so a non-idempotent user
stage runs every boot. Evidence: **DOCUMENTED**.

**Configuration drift.** Covered in dimension 1. Ephemeral paths reset on reboot;
persistent paths do not; nothing detects drift.

**Remote inspection.** `kairos-agent config` prints the final merged configuration on a
running machine, which is the right primitive and is documented. There is no remote
configuration API in the open-source project other than the phone-home
`apply-cloud-config` command, which is off by default. Evidence: **DOCUMENTED**.

**Version control and signing.** The configuration is plain YAML, so version control is
the operator's to do. **There is no configuration signing or verification mechanism.** A
grep of the tree finds signature verification for OCI images, UKI artifacts and sysexts,
and nothing for cloud configuration. Since the merge path includes a URL on the kernel
command line and a templated URL substituting machine identifiers, an unsigned
configuration fetched over the network is a supported provisioning route. Evidence:
**DOCUMENTED** for the grep; **INFERRED** for the consequence.
[Evaluative comparison against Ignition's model, flagged: **C-07**.]

**Secrets.** No secret-management layer. Values go in the YAML in plaintext, including
`passwd:` for users, in the documented example. Partition encryption passphrases are the
exception and are handled by `kcrypt` with a TPM or a remote key server. Evidence:
**DOCUMENTED**.

**Changing configuration without a reboot or rebuild.** Yes. Drop a file in `/oem` or
`/usr/local/cloud-config` and run `kairos-agent run-stage <stage>`, or wait for the
reconcile timer if the stage is `reconcile`. Evidence: **DOCUMENTED**.

**Source of truth.** The `/oem` partition, in practice. It survives upgrades, it survives
reboots, and the documentation says "In Kairos the `/oem` directory keeps track of all the
configuration of the system". It does *not* survive a factory reset with `reset-oem: true`.
There is no external source of truth in the open-source project: no desired-state store,
no server the node reconciles against. Evidence: **DOCUMENTED**.

**The schema.** `kairos-agent validate` checks a configuration against a JSON Schema, and
`kairos-agent print-schema` emits it. The Pulse brief reports that the versioned schema URL stamped
into emitted configurations returns 404 for every version from v3.5.0 to v4.3.0. I did
not re-verify the live URL in this pass (no fetch was made), so that stays **UNKNOWN**
here and is inherited from the Pulse brief rather than confirmed. What I can confirm from source is
that `print-schema` will emit the current schema locally, so an operator is not blocked,
only a tool that follows the URL is. Evidence: **DOCUMENTED** for `print-schema`.

## 7. Kubernetes coupling

**Can it operate without Kubernetes? Yes, and this is provable from CI rather than from
marketing.**

The variant is derived, not chosen. `kairos-init/main.go:38-57` sets the variant to
`standard` if a Kubernetes provider was requested and `core` otherwise; the `--variant`
flag was removed. A core image subtracts concretely: no `/system/providers/agent-provider-kairos`,
no `/usr/bin/edgevpn`, no k3s or k0s binary. The agent tolerates the absence by design
(`cmd/kairos/provider.go`: "a core image has no /system/providers at all"). Evidence:
**OBSERVED**.

The CI evidence is the stronger half. In `master.yaml`, the Kubernetes-free image gets
**17 QEMU cells** across `test-core`, `test-core-fips`, `test-core-ubuntu-20`,
`test-core-rocky-9` and `test-core-leap`, covering custom partitioning, acceptance,
install, install target, insecure registry, partition validation, reset, upgrade with the
CLI, bundles, SSH hardening and upgrade to latest. The standard (Kubernetes-bearing) image
gets **5**. **The no-Kubernetes path receives roughly three times the end-to-end
coverage.** Evidence: **OBSERVED**. That is a much better answer to "is it really
optional" than any documentation page gives.

Even in a standard image, Kubernetes does not start unless it is configured:
`provider/internal/provider/bootstrap.go:51` returns early with "no P2P or kubernetes
configured", and a dedicated CI cell exercises that. Evidence: **OBSERVED**.

**Counter-evidence, and it is worth recording against the project's own claim.** A
Kubernetes assumption leaks into every image, core included.
`kairos-init/pkg/bundled/cloudconfigs/00_rootfs.yaml` hard-codes `/etc/cni`, `/etc/k0s`,
`/etc/kubernetes`, `/etc/rancher`, `/var/lib/cni`, `/var/lib/containerd`,
`/var/lib/calico`, `/var/lib/etcd`, `/var/lib/k0s`, `/var/lib/kubelet`,
`/var/lib/longhorn`, `/var/lib/rancher`, `/var/lib/rook` and Portworx paths into the
persistent bind list, unconditionally. A machine that never runs a container gets bind
mounts for Longhorn, Rook, Calico and etcd. It is harmless and it is a tell. Evidence:
**OBSERVED**.

**Which Kubernetes distributions are supported in released artifacts: k3s and k0s only,
and only ever those.** A grep for `rke2`, `kubeadm`, `microk8s` and `nodeadm` across the
release assets of v4.3.0, v4.2.0, v4.1.2, v4.0.0, v3.7.2, v3.5.10, v3.4.2, v3.2.4 and
v3.0.0 returns **zero hits**. Those providers ship binaries, never bootable media, and
several ship no assets at all. Evidence: **OBSERVED** for v3.0.0 onward; **INFERRED** for
v1.x and v2.x, where release pagination failed.

The version set is not pinned in the repository: the release workflow queries upstream at
tag time and keeps the latest patch of the top three minors.
`reusable-factory.yaml:462` hard-validates that the distribution is `k3s` or `k0s`. arm64
gets k3s only, and the workflow comment says that is deliberate. Evidence: **OBSERVED**.

**Can OS and Kubernetes upgrade independently? No.** The Kubernetes version is encoded in
the artifact tag (`sdk/versioneer/versioneer.go` appends the software version to the tag),
so an OS upgrade is a Kubernetes upgrade and vice versa. The binaries live inside the
immutable image on purpose: the provider explicitly moves the k0s binary out of
`/usr/local`, which is the persistent partition, into `/usr/bin`, "to avoid overwriting it
with PERSISTENT", **so that the binary follows A/B rollback**. That is a correct decision
and it is the decision that fuses the two lifecycles. Evidence: **OBSERVED**.

An operator can change the Kubernetes version while holding the OS version, but only to a
tag CI happened to build, and the move is a full image swap and reboot. The available
cross product is one OS version times three minors times two distributions.
`sdk/versioneer/tag_list.go` refuses a Kubernetes downgrade, with the reason in a comment.
Evidence: **OBSERVED**.

**A maintainer says so in public.** From a Kairos blog post dated 2026-06-11, by Dimitris
Karakasilis: "That packaging is convenient, but it ties two things together that do not
really need to be tied: the operating system and the Kubernetes distribution running on top
of it." The post demonstrates delivering the provider and k3s as a system extension onto
an unmodified core image, in a personal repository. The agent-side pieces exist upstream
(`kairos-agent sysext install`, and `/usr/local/system/providers` is already a provider
search path). **The decoupling is prototyped, not shipped.** This is the live fault line on
this dimension and the thing most likely to change the answer within a year. Evidence:
**DOCUMENTED**.

**Can Kubernetes manage the OS lifecycle?** Yes, through `kairos-operator`'s `NodeOp` and
`NodeOpUpgrade` resources. Covered in dimension 11, including the finding that the operator
does not verify that a node came back on the new version.

**Does the OS manage Kubernetes?** Yes, through the provider mechanism. Discovery is
prefix-based directory autoload: `agent/internal/bus/bus.go:32` autoloads any executable
named `agent-provider-*` from `/system/providers`, `/usr/local/system/providers` or the
working directory, and speaks a JSON-over-argv protocol. The same plugin contract covers
both image construction (build-time events fired by `kairos-init` inside the Dockerfile)
and node runtime. That is a genuinely clean extension seam. Running two providers
side by side is not supported. Evidence: **OBSERVED**.

**The provider ecosystem largely collapsed in August and September 2026.** Of eight
provider repositories, six are archived: `provider-nodeadm` (2026-08-18),
`provider-kairos` (2026-08-31, absorbed into the monorepo rather than abandoned), and
`provider-canonical`, `provider-k3s`, `provider-rke2` and `provider-kubeadm` (all
2026-09-03). Two are live: `provider-microk8s`, whose last release is an alpha, and
`provider-kubernetes`, a fresh core-team kubeadm provider created 2026-06-01 and at v0.3.0
as of 2026-09-15. **A grep of the whole documentation tree for `provider-kubernetes`
returns zero hits**, while `docs/examples/kubeadm-provider.md` still carries runnable
`curl` commands against the archived `provider-kubeadm` releases and tells readers to
"always refer to the provider-kubeadm repository which contains tested configurations
updated for the latest versions". Evidence: **OBSERVED**.

**Non-Kubernetes workloads.** A core image boots to a login prompt with an ordinary Linux
userspace, a local agent and no Kubernetes binary. Container host, appliance, database
node, storage node, edge gateway and ordinary Linux service are all straightforwardly
supported; hypervisor is untested and **UNKNOWN**. The persistent-path list already
accommodates Longhorn, Rook and Portworx, which suggests storage appliances are an expected
use.

### Placement on the spectrum

Measured rather than asserted: of 103 markdown files under `docs/`, 24 (23%) are
Kubernetes-framed in their front matter, 39 (38%) mention Kubernetes only in the body, and
40 (39%) never mention it. The marketing is visibly mid-rewrite: the repository README
still says "Kubernetes-focused, Cloud Native Linux meta-distribution" and "The immutable
Linux meta-distribution for edge Kubernetes", `getting-started/what-is-kairos.md` still
says "for running Kubernetes", while the current homepage hero says "The Immutable OS to
Operate at Scale" with no mention of Kubernetes and the site carries a "Without Kubernetes"
landing track added 2026-07-08. Evidence: **OBSERVED**.

Artifact skew and CI skew run in opposite directions. The v4.3.0 release ISOs are 2 core
and 9 standard; the QEMU matrix is 17 core cells and 5 standard.

**Placement: roughly 70/30 toward general immutable substrate, and moving that way
quickly.** The engine is OS-generic: the variant is a derived label, the provider bus takes
any conforming binary, the upgrade path needs no cluster, and the largest CI surface is
Kubernetes-free. The distribution is still Kubernetes-shaped: released ISOs skew standard,
standard fuses OS and Kubernetes into one artifact, the online encryption key server is a
Kubernetes operator, and every core image carries Kubernetes persistence paths. Evidence:
**INFERRED**.

The honest one-line summary: **Kairos is a general immutable-Linux substrate whose flagship
distribution is a Kubernetes appliance.** The substrate is real and tested; the appliance
is what most of the released bytes and half of the documentation are.
[Evaluative comparisons against Talos, Flatcar and Bottlerocket on this dimension are in
the review list as **C-16**. The closest analogue found is Bottlerocket, whose
per-orchestrator variants bake the Kubernetes minor into the variant name exactly as Kairos
bakes it into the tag; the difference is that Bottlerocket has no unbaked variant and
Kairos has `core`. That comparison was drawn from general knowledge, not from Bottlerocket
primary sources, and must be re-verified.]

## 8. Hardware and platform support

### Architectures with released OS artifacts

**amd64 and arm64. That is the complete list.** v4.3.0 ships 11 ISOs, all Hadron v0.5.1:
core amd64 and arm64; standard amd64 with k0s at three Kubernetes minors; standard amd64
with k3s at three minors; standard arm64 with k3s at three minors. Evidence: **OBSERVED**.

The registry adds board and raw variants that are not GitHub release assets: rpi3 and rpi4
core arm64, rpi4 standard arm64 with k3s, each with a matching `-img` raw tag. Evidence:
**OBSERVED**.

**riscv64 is tooling only.** The release ships riscv64 builds of every Go binary
(`kairos`, `kairos-init`, `kairos-installer`, `kcrypt-challenger`, `provider-kairos`) and
**no riscv64 ISO and no riscv64 OS container image, in any v4.x release**. Registry filters
for `riscv` return nothing. It appears nowhere in the documentation. In `kairos-io/hadron`,
riscv64 is PR-only with its `populate-sources` job gated off by `if: ${{ false }}`, and the
shim build is skipped outright with the comment "Skip shim build for RISC-V as it doesn't
have Secure Boot support yet". Evidence: **OBSERVED**.

### The collapse of the released matrix, quantified

| release | ISOs | base distributions |
|---|---|---|
| v3.7.2 (2026-02-05) | **95** | Alpine 3.21, Debian 13, Fedora 40, Hadron 0.0.1, openSUSE Leap 15.6, Rocky 9.7, Ubuntu 20.04/22.04/24.04/25.10 |
| v4.0.3 | 8 | Hadron |
| v4.1.2, v4.2.0, v4.3.0 | 11 | Hadron |

Evidence: **OBSERVED**. This is the same finding as dimension 3 seen from the artifact
side, and the magnitude is worth stating: the released matrix went from 95 ISOs across ten
bases to 11 across one, in one major version, by a stated decision.

**Two artifact classes regressed between v4.2.0 and v4.3.0.** There is a
`v0.5.1-core-amd64-generic-v4.2.0-uki` tag on quay, last modified three minutes after the
v4.2.0 release timestamp, and CI pushes to ghcr rather than quay, so it came from the
release run. **There is no `-uki` tag for v4.3.0.** UKI images exist for v4.0.0 through
v4.2.0 and then stop. No FIPS tag exists for v4.3.0 either. The release workflow's own
comment asserts "v4.2.0 released none of them", which the registry contradicts. Evidence:
**OBSERVED**; **UNKNOWN** whether the regression is intentional. This is worth raising with
the project as a possible unintentional loss.

That finding lands directly on dimension 9: Trusted Boot is the only Kairos path with a
signed boot chain, and as of the current release there is no prebuilt artifact for it at
all.

### Board and SoC support: a closed enumeration

`kairos-init/pkg/values/values.go` defines exactly seven models: `generic`, `rpi3`, `rpi4`,
`nvidia-jetson-agx-orin`, `nvidia-jetson-orin-nx`, `nvidia-jetson-thor`,
`nvidia-dgx-spark`. The `--model` flag is a closed enum and
`kairos-init/main.go:288` rejects anything else at argument parse time. **There is no
plugin, no registry and no configuration file for adding a model.** Evidence: **OBSERVED**.

What a model actually buys is concrete and non-trivial: kernel selection (rpi3 and rpi4
prefer the `*-raspi` module directory, with the reason in a comment naming
`kairos-io/kairos#4222`), repository tweaks (Debian non-free for Pi firmware), per-model
package sets (DGX Spark pulls an NVIDIA HWE kernel, open NVIDIA modules, `fwupd` and
`rdma-core`), firmware orchestration (a Jetson QSPI updater that compares the UEFI ESRT
against the image's bootloader, stages a capsule update, and **aborts the install** if the
board firmware is newer or below L4T 38.0.0), and architecture enforcement. Evidence:
**OBSERVED** and **DOCUMENTED**.

The per-board *cloud configurations* are a separate layer and they self-detect at runtime
from device-tree strings rather than from the build-time model. So the enum governs kernel,
packages and firmware; the runtime layer adapts on its own.

**Raspberry Pi: models 3 and 4, 64-bit, and not model 5.** The documentation says why:
"Model 5 is currently not supported because of how we use U-boot to boot the device", with
a link to upstream work. Released artifacts match, including an rpi3 gap for standard
images. Evidence: **DOCUMENTED**.

**Jetson and GPU: container images only, never ISOs**, and the reason is in the workflow
comment: "the L4T rootfs is large enough that materializing raw OOM-kills the runner during
auroraboot's copy-into-tempdir step". Thor and DGX Spark have `--model` support and
documentation and **no published image at all**. Evidence: **OBSERVED**.

**A security consequence of that exception, not previously recorded in this epic:** the
Jetson cells set `grype: false` and `sbom: false`. **The Jetson images ship without
vulnerability scanning and without an SBOM**, unlike every other released artifact.
Evidence: **OBSERVED**.

### Cloud platforms

**CI genuinely publishes to all three major clouds, and this is a real strength that
earlier research in this epic underweighted.** `.github/workflows/upload-cloud-images.yaml`
runs on release, nightly and on dispatch, with three jobs:

- **AWS**: S3 upload, `import-snapshot`, `register-image` with UEFI boot mode and ENA
  support, then **a boot test that gates publication** ("Image test failed! Not proceeding
  with making the image public and copying to other regions"), then make-public and
  copy-to-all-regions in parallel with tagging. The owner account is published in the
  documentation so an operator can verify provenance.
- **GCP**: a project and bucket under the project's control, via workload identity
  federation, including a `sgdisk -e` fix with the reason in a comment.
- **Azure**: a compute gallery, stable tags only.

Evidence: **OBSERVED**. A boot test before publication is better practice than most
operating-system projects of this size manage.

All three build from `quay.io/kairos/hadron:<version>-core-amd64-generic-<tag>`. So the
cloud offering is **amd64 only, core only, Hadron only**: no arm64 cloud images, no
Kubernetes-bearing cloud images. Evidence: **OBSERVED**.

**Documentation drift on this point is material.** The GCE page still says "only one Kairos
flavor is published in Google Cloud (Ubuntu 24.04)"; the workflow has used Hadron since
v4.x. The AWS page still shows a v3.3.0 Ubuntu AMI name as its example. The Azure page is
correct. The Hetzner page is honest that no official image exists and routes the reader to
the web installer instead, which interacts badly with the finding in dimension 10.
Evidence: **OBSERVED**.

### TPM and firmware requirements

Trusted Boot requires, verbatim from `docs/installation/trustedboot.mdx`: Secure Boot
available, a TPM chip or firmware TPM, fast boot disabled in the BIOS, hardware capable of
booting EFI files larger than 32 MB, and systemd 252 or newer in the base image. The same
page states the operational cost plainly: "Any change, or upgrade of the node to a new
version of the OS requires those assets to be regenerated with these keypairs, including
the installer ISO, and the EFI files used for upgrading", and "Loosing the keys will
prevent you to generate new images that can be used for upgrades." Evidence:
**DOCUMENTED**. That candour is worth crediting: the operator is told, up front, that
Trusted Boot means owning a signing pipeline for the life of the fleet.

Disk encryption requires TPM 2.0. Online mode additionally requires a Kubernetes cluster to
host the key server; offline mode, which seals the passphrase into a TPM NV index, requires
nothing. Evidence: **DOCUMENTED**.

The baseline path requires UEFI or legacy BIOS, GPT, and the fixed `COS_*` partition-label
contract. Legacy BIOS genuinely works (`agent/pkg/config/spec.go:110` selects BIOS firmware
when `/sys/firmware/efi` is absent). Evidence: **OBSERVED**.

### "If unsupported hardware appears tomorrow, can an organization add support itself?"

The framework calls this the most important question in the dimension. The answer splits
three ways, with very different costs.

**Case A, standard UEFI or SBSA x86-64 or arm64 hardware, which is the common case: easy,
with no upstream involvement.** Use `--model generic`, build with the base distribution's
kernel, done. The requirements a base must satisfy are short and published: systemd 256+
and systemd-boot for Trusted Boot, systemd or OpenRC and GRUB otherwise, `CONFIG_EFI_STUB`
for EFI. **This is genuinely better than an appliance operating system whose kernel and
kernel configuration are the vendor's.** Evidence: **DOCUMENTED**.
[Evaluative comparison, flagged: **C-17**.]

**Case B, board-specific tweaks without a new model: supported, and undocumented.**
`kairos-init/pkg/stages/extensions.go` implements a stage-extension loader: with
`--extensions`, it walks `$KAIROS_INIT_STAGE_EXTENSIONS_DIR` (default
`/etc/kairos-init/stage-extensions`) and appends any yip stages it finds into the matching
kairos-init stage. An organization can inject firmware copies, device-tree handling, module
lists and service tweaks **without forking**. It is in the source. No documentation page
describes it. Evidence: **OBSERVED**.

That is a significant finding in Kairos's favour that nobody would learn from the
documentation, and it materially changes the answer to the framework's question.

**Case C, a genuinely new board needing vendor kernel, device tree or bootloader
integration: an upstream Go change.** Add a `Model` constant, wire the architecture map,
add package-map entries, and for anything like Thor write firmware-orchestration Go. There
is no downstream extension point for this and no documented process. The cost is a pull
request to `kairos-io/kairos` reviewed by a team of roughly five human maintainers.
Evidence: **OBSERVED**.

**There is no hardware compatibility list, no certification programme and no porting
guide.** A grep of the documentation for "new board", "adding a board", "unsupported
hardware" and "porting" returns one page: a 2022-era NVIDIA development note that opens
"At the time of writing, we have tried porting Kairos to Jetson Nano eMMC without success."
`CONTRIBUTING.md` says nothing about hardware. Evidence: **OBSERVED**, and per the
framework this is an absence in the published corpus rather than proof that no process
exists.

### The inversion worth naming

Kairos's default operating system is now Hadron: built on musl libc, systemd, and vanilla
kernels, with no package manager by default, and described in its own README as "Engineered
by Spectro Cloud from the Kairos team". Evidence: **DOCUMENTED**.

**The flagship artifact of the meta-distribution is a from-scratch, musl, package-manager-less
distribution, which is architecturally much closer to an appliance operating system than to
"pick your distribution".** The construction kit is intact underneath. The thing in the box
is an appliance. Both facts are true and the profile should state them together rather than
choosing one.
[Evaluative framing, flagged: **C-18**.]

## 9. Security and chain of trust

This dimension was researched in depth for this epic already, as FR-14. That
document holds the full evidence chain for the Secure Boot half. This section cites it
rather than repeating it, and adds the parts FR-14 did not cover.

### Firmware to bootloader

**The released artifact is not signed at all.** FR-14 pulled the published
`ghcr.io/kairos-io/hadron:main` image (revision `4ffdf3c`, built 2026-09-15) and parsed
the PE headers of every file in the Secure Boot chain. `shim.efi`, `grubx64.efi`,
`systemd-bootx64.efi` and the kernel all carry an **empty Authenticode certificate
table**. There is no shim-review submission. Evidence: **REPRODUCED** (by the Secure Boot key-ownership task).

The architecture page at `kairos.io/docs/architecture/secureboot/` says "Any of the
current supported flavors in Kairos can be used with SecureBoot out of the box in UEFI
mode." That page describes a piggyback model: use an upstream distribution's already-signed
shim, GRUB and kernel. The model is real and it worked for the SUSE and Ubuntu bases. It
cannot apply to Hadron, which builds its own shim from rhboot source with no signing
step, and Hadron is the only base with released OS images at v4.3.0.

So an operator with a Secure Boot policy reads the architecture page, downloads the
official ISO, and it does not boot, with nothing in the documentation explaining why.
**This is the most serious single finding in this profile** and it is the Secure Boot key-ownership task's, not mine.
It remains flagged for Mauro's own verification: the Secure Boot key-ownership task is explicit that the artifact
reading is reproduced but the *intent* is unknown, because no primary source says either
way and `kairos-io/hadron` has issues disabled.

The Trusted Boot path is the opposite, and FR-14 credits it: the operator generates their
own keys with `auroraboot genkey`, and the documentation is clear and unsentimental about
what that costs. Losing the keys means you cannot build new images. Keys cannot be made
non-expiring. Enrolment needs firmware setup mode or per-machine work. The flag for
skipping Microsoft's certificates is literally named
`--skip-microsoft-certs-I-KNOW-WHAT-IM-DOING`.

A Kairos-held signing key was considered and declined, and the reasoning is on the record
in `kairos-io/kairos#3489`: an offline key, at least two custodians, a manual release
step, and an official dbx with revocation hashes to maintain. FR-14 calls that the
clearest written articulation of the cost of a project-held key by anyone in the
comparison. The decision is defensible. The documentation did not follow it.

### Bootloader to kernel to initrd

**UKI.** Available, as Trusted Boot. Kernel, initrd and command line in one signed PE
binary. Evidence: **DOCUMENTED**.

**Measured boot.** Under Trusted Boot only. PCR 7 (Secure Boot state) and PCR 11 (the UKI
measurement) are used, via systemd's own mechanisms. Evidence: **DOCUMENTED**.

**On the default GRUB path there is no measurement, no signature and, as recorded in
dimension 1, no boot menu password.** The three together mean the default path offers no
protection against an attacker with console or disk access. Evidence: **INFERRED** from
the three DOCUMENTED facts.

### Root filesystem and extensions

**dm-verity is not used for the OS root**, on either path. It appears only in the system
extension mechanism, and there signature enforcement is Trusted Boot only. The
documentation states this plainly: "Currently only signed+verity sysexts are supported
under Trusted Boot (UKI). For non-uki Kairos, the signature is not enforced yet."
Evidence: **DOCUMENTED**.

This is the clearest technical gap against the verity-based projects. Flatcar, Talos and
Bottlerocket all establish root integrity cryptographically at boot on their default
path. Kairos establishes it at install and trusts the disk thereafter.
[Evaluative comparison, flagged: **C-08**.]

### Disk encryption

**Opt-in, and scoped to user-data partitions.** The default install encrypts nothing. An
operator enables it by listing partition labels under `install.encrypted_partitions`.
Source: `kairos-io/kairos-docs` `origin/main:docs/advanced/partition_encryption.md`.
Evidence: **DOCUMENTED**.

The consequence on a default install is concrete, and it follows from the persistent-path
list in dimension 1: SSH host keys (`/etc/ssh`), Kubernetes credentials
(`/etc/kubernetes`, `/var/lib/kubelet`), etcd data (`/var/lib/etcd`), TLS private keys
(`/etc/ssl/private`) and every home directory sit unencrypted on `COS_PERSISTENT`.
Evidence: **INFERRED**, from two DOCUMENTED facts (the persistent path list, and
encryption being opt-in).

Under Trusted Boot, encryption is automatic and TPM-bound. Three modes exist: offline
(passphrase in TPM NV storage), online automated (TPM-wrapped passphrase held by a key
server), and online manual. Evidence: **DOCUMENTED**.

The remote key-server documentation is worth crediting for candour. Every worked example
in `partition_encryption.md` uses plain `http://`, certificate pinning is optional and
empty by default, and the page says so rather than hiding it. The pinning field itself is
the best-designed configuration key found anywhere in this audit:
`kcrypt.challenger.certificate` takes the PEM text rather than a path, and the
documentation says so.

### Remote attestation

**Kairos implements real TPM attestation, and it is wired to disk encryption rather than to
identity.** The kcrypt challenger runs a full credential-activation protocol: endorsement
key and attestation key parameters, activation-parameter generation, `ActivateCredential`,
and a PCR quote verified on the server. Re-attestation does the right things, including
logging a "potential TPM impersonation attempt" and honouring quarantine. Evidence:
**OBSERVED**.

Two limits, both material and both relevant to this dimension rather than to dimension 10:

- **No endorsement-key certificate chain is validated anywhere.** The protocol transmits
  the EK public key only, never the EK certificate. Greps for `x509.VerifyOptions`,
  `CertPool` and `Roots` across the kcrypt tree return nothing. Meanwhile
  `kairos-io/tpm-helpers`'s README claims, under a heading reading "Security Guarantees",
  that the "Endorsement Key (EK) proves requests come from a genuine TPM". **The code does
  not enforce that**: a software TPM can play the EK role. This is a documented-guarantee
  versus observed-source contradiction, and it is the second one in this profile after the
  Secure Boot page. Evidence: **OBSERVED**.
- **Trust-on-first-use by default, with no deny-unknown mode.** A previously unknown TPM is
  enrolled and given a passphrase. Operators can pre-create the sealed-volume resources,
  but no switch makes an unknown TPM fail. Evidence: **OBSERVED**.

So on the attestation axis the honest reading is: the hard cryptographic work is done and
done properly, and the trust anchor at the bottom of it is missing.

### Artifact signatures, SBOM, provenance

Release signing is Sigstore keyless cosign, verified genuine by the Pulse brief's own research
(Fulcio certificate naming the project's release workflow at the tag, with Rekor entries).
The documented verification command names the identity
`https://github.com/kairos-io/kairos/.github/workflows/reusable-factory.yaml@refs/tags/$VERSION`
and the GitHub Actions OIDC issuer
(`kairos-io/kairos-docs` `origin/main:docs/installation/check-the-signatures.md:38`).
Evidence: **DOCUMENTED**.

Verification is presented as an optional step for the user, and, per dimension 4, is off
by default in the upgrade path. The gap between "we sign everything" and "nothing checks
the signature unless you ask" is the central security finding of this profile.

### Tamper prevention, tamper detection, attestation

The framework asks these to be distinguished, and Kairos separates unusually cleanly,
because the two paths land in different places.

| | default (GRUB) path | Trusted Boot (UKI) path |
|---|---|---|
| tamper **prevention** | read-only root mount; no boot menu password; no signature at any stage | signed UKI, firmware-enforced; measured command line |
| tamper **detection** | none | signature check at upgrade; PCR mismatch breaks the TPM unlock |
| **attestation** | none | PCR 7 and 11 measurements available to a remote verifier; no attestation service in the project |

Evidence: **DOCUMENTED** for every cell except the attestation row, which is **INFERRED**
from the measurement being present and no attestation tooling existing in the
organization.

### CVE handling, FIPS, mandatory access control

`SECURITY.md` and the advisory history are covered in dimension 17. FIPS is a build flag
with no published FIPS ISO and no whole-system validation claim; the documentation page
is under 100 words. SELinux is relabelled on upgrade and on reset
(`upgrade.go`, `reset.go`, both calling `SelinuxRelabel`), and `master` added non-UKI
SELinux support in commit `1f9681ec`, after v4.3.0. No page documents the intended
SELinux posture (enforcing, permissive, which policy). Evidence: **DOCUMENTED** for the
code; **UNKNOWN** for the intended posture.

### Kernel hardening and lockdown

From the Secure Boot key-ownership task's reading of `kairos-io/hadron` `origin/main:files/kernel/default.config`:
lockdown is compiled in but forced to none
(`CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE=y`), the distribution patch that enters lockdown
automatically under Secure Boot is absent, and no `lockdown=` appears on any command
line. Module signing is on with the kbuild default ephemeral key, so in-tree modules are
signed by a key nobody keeps and an operator cannot sign anything with it. riscv64 has
none of it. Evidence: **DOCUMENTED** (by the Secure Boot key-ownership task).

The net effect today is benign, because nothing is signed, so nothing is enforced. It
becomes a problem the moment the boot chain is signed and nothing documents that.


## 10. Provisioning and zero-touch deployment

### Paths from powered-off hardware to a managed machine

Twelve or more, all real: interactive install from ISO or USB (a Bubble Tea terminal UI);
unattended install from ISO with `install.auto: true`; install with QR pairing;
`kairos-agent manual-install`; a container "takeover" install onto a rescue-booted machine
(`docker run --privileged ... kairos-agent manual-install --device $DEVICE --source dir:/`);
PXE and iPXE one-shot through AuroraBoot; PXE through AuroraBoot's fleet server; a separate
UKI PXE code path; cloud images on AWS, GCP and Azure; raw disk images; **MAAS**; **Redfish
virtual media**, marked experimental; the web installer UI; in-RAM diskless boot; and a
peer-to-peer self-coordinating cluster, documented as experimental and "only tested on local
setups". Evidence: **OBSERVED** and **DOCUMENTED**.

`kairos-io/netboot` and AuroraBoot are not redundant: `netboot` is a library fork of
Google's Pixiecore (server, booters, DHCP, TFTP, no `cmd/`), and AuroraBoot consumes it as
a Go dependency. netboot is the PXE engine; AuroraBoot is the product. Evidence:
**OBSERVED**.

### Configuration datasources

Two mechanisms that should not be conflated.

**The Kairos collector** (`sdk/collector/collector.go`) merges three families: four
directories in a fixed order (`/run/initramfs/live`, `/etc/kairos`,
`/usr/local/cloud-config`, `/oem`), with files requiring a `#cloud-config`,
`#kairos-config` or `#node-config` header and skipped above 2 MiB; the kernel command line
(`kairos.config=`, `kairos.config_url=`, legacy `cos.setup=`, and generic dot-notation
key/value pairs); and an HTTP or HTTPS `config_url` with a 15-second timeout, three
retries, and **recursion**. Two explicit TODOs in that code record a real hazard: an
exhausted retry and a body without a valid header **both return an empty configuration and
a nil error**. Silent failure. Evidence: **OBSERVED**.

**The cloud metadata datasources** are delegated to yip: thirteen providers, listed in
dimension 6, run in `rootfs.before`, `initramfs.before` and `network`. `cdrom` and
`config-drive` probe first and serially; the network providers probe **concurrently, first
to answer wins**, which is non-deterministic if two metadata services respond. Evidence:
**OBSERVED**.

One design detail worth crediting: under Trusted Boot, datasources are **not** parsed after
install unless `kairos.pull_datasources` is on the command line, and the rationale (USB
config injection on an edge device) is documented in place. Evidence: **OBSERVED**.

One hazard worth flagging: the datasource stage writes a sentinel and the installer blocks
on it for **up to five minutes** before proceeding anyway ("userdata configuration failed
to load after 5m, ignoring"). In an air-gapped install that five-minute stall is
guaranteed. Evidence: **OBSERVED**.

**The real per-device mechanism is a templated `config_url`.**
`sdk/collector/config_url_template.go` renders the URL through `text/template` with sprig
and `missingkey=error`, with context from `zcalusic/sysinfo` plus a random value and a
protected machine ID, and query-escapes every string leaf. The documentation exposes
`{{ .Values.product.uuid }}`, `.product.serial`,
`{{ (index .Values.network 0).macaddress }}` and `.node.hostname`. Evidence:
**DOCUMENTED**. This is a well-built zero-touch desired-state mechanism and several
appliance operating systems do not have an equivalent.

### Device identity and bootstrap trust: the dimension's main gap

**Kairos has no per-device bootstrap identity.** Four bootstrap-trust mechanisms exist.
Three are shared secrets and one is interactive-per-device. **TPM attestation is
implemented, and it is wired to disk-encryption key escrow, never to identity toward a
management plane.** Evidence: **OBSERVED**.

**Phone-home to the AuroraBoot fleet server**, the newest and now-default path. The
identity asserted is `/etc/machine-id`, read verbatim. It is genuinely per-device (the
build truncates it, first boot regenerates and persists it) and it is **self-asserted and
unattested**. The bootstrap credential is a **fleet-wide shared registration token**, baked
identically into every artifact AuroraBoot builds, alongside a default `kairos`/`kairos`
username and password in the default builder path. The server check is body-field equality
and, notably, **not constant-time**, unlike the `subtle.ConstantTimeCompare` used for the
admin password and node API keys in the same file. Enrolment is trust-on-first-use with no
allowlist: registration mints an API key for any unseen machine ID, and re-registration is
idempotent by machine ID and **returns the existing node's API key**. So anyone holding the
shared token can retrieve any enrolled node's API key by knowing its machine ID. The
default `--url` is plain HTTP; TLS is opt-in; credentials land in plain YAML on the
persistent partition, not TPM-sealed. Evidence: **OBSERVED**.

**Credit where it is due, and it is substantial:** the *authorization* model on that same
channel is well built. The default allowed-command set excludes `exec`, `reset` and
`apply-cloud-config`, with the threat named in a source comment ("a DNS hijack / rogue
server can reach this endpoint"); there is BOLA protection so a node cannot act on another
node's resources; artifact downloads are scoped; node API keys are never accepted from a
query token; rate limiting is on by default; and BMC credentials are AES-256-GCM encrypted
at rest. **A strong authorization model on a weak authentication root** is the accurate
summary. Evidence: **OBSERVED**.

**QR pairing** is genuinely per-device and deliberately not zero-touch: either a fresh
random token per machine displayed on a console, requiring a human with a camera, or a
shared network token for the whole fleet.

**The kcrypt challenger is the only real TPM attestation in the project, and it is not
identity.** It implements a full credential-activation protocol: endorsement key and
attestation key parameters, activation-parameter generation, `ActivateCredential`, and a
PCR quote verified server-side. Two findings:

- **No endorsement-key certificate chain is validated anywhere.** The protocol transmits
  only the EK public key, never the EK certificate. Greps for `x509.VerifyOptions`,
  `CertPool` and `Roots` across the kcrypt tree return nothing. Meanwhile
  `kairos-io/tpm-helpers`'s README claims, under "Security Guarantees", "**TPM Identity**:
  Endorsement Key (EK) proves requests come from a genuine TPM". **That claim is not
  enforced**: a software TPM can play the EK role. This is a documented-claim versus
  observed-source contradiction and it belongs in dimension 9 as well. Evidence:
  **OBSERVED**.
- **Trust-on-first-use by default, with no deny-unknown mode.** The challenger's source
  carries the comment "Skip verification for new enrollments (TOFU - Trust On First Use)"
  and then generates a passphrase and creates the sealed-volume resource for a previously
  unknown TPM. Operators can pre-create sealed volumes, but no switch makes an unknown TPM
  fail. Re-attestation does the right thing, including logging a "potential TPM
  impersonation attempt" and honouring quarantine. The **client** does not authenticate the
  server, so with mDNS discovery enabled a LAN attacker can be the key server at first
  enrolment. Evidence: **OBSERVED**.

### The factory scenario

> Can 5,000 identical devices leave a factory and independently establish secure identity
> and desired state on first boot?

**Desired state: yes, and well. Secure identity: no.**

Desired state is competitive. Bake a templated `config_url` and devices fetch per-machine
configuration unattended, recursively, URL-escaped, failing loudly on a missing key. Or use
MAAS, or cloud metadata, or per-device ISOs.

Secure identity is not there. Every image carries **the same secret**: the AuroraBoot
registration token, or the same peer-to-peer network token, plus default credentials in the
default builder path. **There is no per-device secret provisioning anywhere in the
codebase**: no per-device key injected at build, no factory enrolment manifest, no EK
allowlist import, no certificate-signing request. First contact is trust-on-first-use on
both paths. The identifiers a discovery service receives are unsigned claims in a URL, and
nothing stops device 2 from claiming device 1's UUID. Extract the token from one device,
which is a world-readable file under `/oem` or an unauthenticated HTTP fetch from the
netboot server, and an attacker can enrol an impostor **or pull an existing node's API
key**. Evidence: **OBSERVED**; **INFERRED** for the attack, which was not performed.
**NOT TESTED**.

**The precise shape of the gap matters more than the verdict.** It is not that Kairos lacks
TPM code: it has more TPM code than several projects in this comparison. It is that the
attestation it already implements is wired to disk encryption instead of enrolment, and the
endorsement key it attests is never chained to a manufacturer root. The smallest credible
fixes are all reachable from existing code: validate the EK certificate chain, which is a
one-field protocol change; add a deny-unknown-TPM mode; let node registration accept an EK
hash and a quote instead of a shared token; and stop returning an existing node's API key
on a bare machine-ID match.
[Evaluative comparison against Talos's per-node certificates and the hyperscalers' signed
instance-identity documents, flagged: **C-19**.]

### Air-gapped provisioning: better than assumed, worse documented

Self-contained: the ISO install source is the live medium, not a registry. And **k3s and
k0s binaries are baked at build time, not downloaded on first boot**: the provider runs the
upstream install scripts inside the Dockerfile with `INSTALL_K3S_SKIP_ENABLE=true`. A
standard image needs the internet **to be built**, not to boot. Evidence: **OBSERVED**.
That corrects a common assumption and is a real point in Kairos's favour for edge
deployment.

Still reaches out: `config_url` and every recursive hop; the network metadata datasources,
harmless but costing the five-minute stall; bundles with OCI or `run://` targets; the k3s
*container* images, which is what the air-gap documentation page is actually about;
phone-home artifact downloads; and everything at build time.

**There is no page stating the general air-gap contract:** which install paths work with no
egress, that the datasource probe stalls for five minutes, that standard images are
pre-baked, or how to air-gap the fleet server. "Kairos installs air-gapped" is **INFERRED**
from source, not documented.

### The web installer: the clearest documentation-versus-source divergence in this profile

Verified independently in `agent/internal/webui/webui.go` and the shipped configuration.

- **It binds `:8080`**, which in Go means **all interfaces**
  (`agent/pkg/constants/constants.go:134`, `DefaultWebUIListenAddress = ":8080"`). The
  installer advertises the URL on the console for every local IP address.
- **No authentication.** The complete listener setup is an Echo instance, a static file
  handler, `POST /validate`, `POST /install` and `GET /ws`. No middleware, no session, no
  token, no basic auth, **no CSRF protection**.
- **No TLS.** Plain `Start`, no `StartTLS`, no certificate paths anywhere in the package.
- **What it does:** `POST /install` accepts a cloud configuration, a reboot flag, a
  power-off flag and a target block device, writes the configuration to a temporary file,
  and executes `kairos-agent manual-install --device <caller's choice>` as root. The caller
  controls the target disk and the entire cloud configuration, which includes users, SSH
  keys, bundles and arbitrary yip stages. Arguments go through `exec` rather than a shell,
  so this is arbitrary install, not shell injection.
- **It is enabled on every live boot**, not only in install mode. The shipped configuration
  runs `systemctl enable --now kairos-webui` gated only on live or UKI install mode, and
  the project has a test asserting exactly that behaviour, named "enables the webui on every
  live boot, not only an install-mode one". No shipped image sets `webui.disable`.

Evidence: **OBSERVED** for all of the above.

**Stated fairly:** this is the live installer environment only. An installed node does not
expose it. But the realistic exposure is exactly the workflow Kairos advertises: a rack
PXE-booted into installer mode, every machine offering unauthenticated remote root install
to the provisioning network for as long as it sits there. And the Hetzner page routes users
to it **on a cloud server**.

**The documentation gap is the finding.** `docs/installation/webui.md` is twelve lines,
states the port, and contains **no security note of any kind**. The contrast with
AuroraBoot is instructive and is what makes this look like an oversight rather than a
philosophy: AuroraBoot's netboot server is also unauthenticated by design, and it says so
in its README **and** prints a runtime warning: "Serving over UNAUTHENTICATED HTTP: booting
machines cannot present a credential, so anyone who can reach this address can download the
served files, which may include a cloud-config with secrets. Run this only on a trusted,
isolated provisioning network." Evidence: **DOCUMENTED**.

That warning is the right pattern. The web installer needs the same sentence.

## 11. Fleet lifecycle

The framework asks that open-source project capability, open-source companion capability
and commercial product capability be labelled separately. For Kairos that separation has an
unusual result: **nothing is documented as commercial-only.** An exhaustive case-insensitive
grep of the whole documentation corpus for "spectro" and "palette" returns the homepage
enterprise-support card, the adopters list, one architectural citation, and a GCP project
name. **No feature matrix, no enterprise-only marker, no upsell.** Evidence: **OBSERVED**.
What Spectro Cloud's Palette adds on top is **UNKNOWN**: the kairos-io corpus is silent and
the vendor's own material was not fetched in this pass. Do not assert either direction.

The story therefore splits two ways, not three.

### kairos-operator: a single-cluster, one-shot batch runner

Maturity: first release candidate 2025-05-28, v0.2.2 on 2026-09-10. Pre-1.0 and young.

`NodeOp` offers a node selector, a required command run in a privileged container with the
host root mounted, an image reference (**the only version pin**), cordon, drain options,
reboot-on-success, a backoff limit, concurrency (**0 means all nodes at once**),
stop-on-failure, and a preflight command with a deadline. `NodeOpUpgrade` adds
recovery/active selection, a force flag that disables the preflight skip, and excluded
paths. The generated NodeOp hard-codes cordon and drain for upgrades. Evidence:
**OBSERVED**.

**What does not exist**, from exhaustive greps: maintenance windows, schedules or cron; a
`maxUnavailable` equivalent; **any deadline on the upgrade Job itself** (only the preflight
is bounded, so a hung upgrade holds its concurrency slot indefinitely with the node
cordoned and drained); any grouping abstraction beyond a label selector; **Kubernetes
Events** (zero `Recorder` or `Eventf` hits); and structured conditions, since status is a
bare phase string. Two declared fields, `drainOptions.deleteEmptyDirData` and
`drainOptions.timeoutSeconds`, are **never read by the controller**. Evidence: **OBSERVED**.

**Drain bypasses the Eviction API.** The controller enumerates pods and deletes them
directly; a grep for `eviction`, `policy/v1` and `PodDisruptionBudget` returns one unrelated
comment. **PodDisruptionBudgets are not honoured.** Evidence: **OBSERVED**.
[Evaluative judgement, flagged: **C-20**. This is below the bar `kubectl drain` sets.]

### The completion condition, which is the load-bearing answer

**The operator does not verify that a node came back on the new version.** It checks that
the Job reached a success condition, and that the reboot pod reached `Succeeded` carrying
an annotation **it set on itself, immediately before calling reboot**. The reboot script
patches `kairos.io/reboot-state: completed` onto its own pod, sleeps five seconds, and
calls `nsenter ... reboot`. Node completion is then "phase completed and reboot status
completed". Evidence: **OBSERVED**.

The negative evidence is equally clear: a grep for `NodeReady`, `node.Status` and
`Status.Conditions` in both controllers matches **only** the Job-conditions read. The
controller never reads a `Node`'s status. It gets nodes only to flip `Spec.Unschedulable`
and to list targets.

A version check does exist, and it is a **preflight skip, not a post-upgrade
verification**: the preflight script compares the image's version against
`/host/etc/kairos-release` and records the node as completed-and-skipped when they match.
It is disabled entirely under `force: true`. So "did the upgrade land" is only ever answered
by *the next* NodeOpUpgrade's preflight, run by a human. Evidence: **OBSERVED**.

**The data needed to answer it properly already exists and nothing consumes it.** The
operator ships a node-labeller DaemonSet that writes `kairos.io/release`,
`kairos.io/software-version` and `kairos.io/boot-state` (active, passive, recovery, livecd)
onto every node on a 60-second loop. **The NodeOp controller never reads any of them.**
Evidence: **OBSERVED**.

The documentation overstates the behaviour mildly:
`operator-docs/nodeop.md:172` says the node is uncordoned "After the reboot completes and
the node comes back online", which describes the observable behaviour fairly but no code
observes it. **A node that upgrades, reboots, and comes up broken but not crashed is
indistinguishable from success.**

That finding closes the loop with dimension 4. The per-node safety net stops at "reached an
early cloud-init stage", and the fleet-level safety net stops at "the reboot pod exited".
Neither layer asks whether the machine works.

### Health gates and rollback

**At fleet level: none.** No health check between batches, no readiness probe after the
Job, and **no rollback**: a grep for `rollback` across the operator's source returns zero
hits. A failed node is left in a failed phase and cordoned. `stopOnFailure` stops *starting*
new nodes; it never reverts and never aborts work in flight. Evidence: **OBSERVED**.

**At node level: real and automatic**, on both boot paths, as covered in dimensions 4 and
5.

**The missing wire is the highest-leverage fix visible anywhere in this profile.** The
node-labeller writes `kairos.io/boot-state=passive` for a node that fell back, and
AuroraBoot stores a node's boot state with the comment "a node that booted the passive
image signals a broken active image". **The signal exists at both ends and nothing connects
it to anything**: no automatic pause of a rollout, no alert, no retry. Evidence:
**OBSERVED**.

### Inventory

**The operator has none.** Its universe is objects that are already Kubernetes `Node`s. A
machine that was provisioned but never joined, failed to install, is powered off, or
dropped out is invisible. There is no expected-versus-actual reconciliation and no "missing
node" state. **A NodeOpUpgrade covering 40 of 50 machines reports completed.** Evidence:
**OBSERVED**.

**AuroraBoot has a real one.** Its store models managed nodes (machine ID with a unique
index, hostname, group, phase, last heartbeat, agent version, OS release map, labels,
addresses, boot state, claim and reset state), node groups with selectors, **BMC targets**
carrying model, manufacturer, serial, memory and CPU counts, so machines are known **before
they ever boot**, and deployments. Registration happens at first OS boot through the baked
phone-home stage, **independently of Kubernetes**, so AuroraBoot does see a machine that
booted but never joined a cluster. Evidence: **OBSERVED**.

**Nothing joins the two.** The operator does not read AuroraBoot; AuroraBoot does not read
the cluster. The only bridge in the organization is `cluster-api-provider-kairos-fleet`.
**So the operator has the batching, AuroraBoot has the inventory, and neither has both.**

### Audit trail

The operator's is thin: a status map entry overwritten in place, one timestamp, no start
and finish, no attempt history, no per-node record of which image was applied, no Events.
Durability is the lifetime of the custom resource, and the documentation encourages a new
resource per run.

AuroraBoot's is substantially better: per-node, per-command records with phase, result,
timestamps for delivery and completion, and captured output, in SQLite or Postgres, plus
deployment and artifact records carrying the Kairos version, base image, Dockerfile, cloud
configuration and build logs. The caveat is that it is a mutable operational table with
history-clearing calls, not an append-only log. Evidence: **OBSERVED**.

### Disconnected fleets

**The operator cannot handle them.** It is push-only and needs a live API server. A node
absent at rollout time is never in the target list and is only revisited by a fixed
five-minute re-list, with no memory that it was behind.

**AuroraBoot has genuine store-and-forward, and this is a real strength.** Commands are
persisted first and delivered later; the code explicitly declines to claim a command for an
offline node, "leaving the command Pending for the next poll or reconnect", and flushes
pending commands on reconnect. A REST pull path claims pending-to-delivered atomically "so
the same command is never handed to two deliveries". The node side is outbound-only with a
30-second heartbeat and 5-to-60-second reconnect backoff, which is what makes NAT and edge
work. Evidence: **OBSERVED**. Architecturally this is better suited to true edge than a
Kubernetes-Job model.

**One hazard:** a `CommandExpired` state is declared and **never written anywhere**, the
expiry timestamp is set on exactly one path, and no sweeper enforces it. **A queued upgrade
for a node that has been offline six months is delivered unmodified the moment it
reconnects.** Store-and-forward with no time to live. Evidence: **OBSERVED**.

### The AuroraBoot fleet server, and the documentation gap around it

There is no `fleet` subcommand; it is `auroraboot web`, whose source opens with the comment
"AuroraBoot fleet management server". Its README describes a self-hosted dashboard, REST
API, node manager, Secure Boot key store and netboot server, with a command taxonomy of
upgrade, upgrade-recovery, reset, exec, apply-cloud-config and reboot, three authentication
schemes, rate limiting on by default, and secrets generated on first run.

Dating matters: the build-only web UI landed 2025-03-17, but **the node registry, command
queue and fleet model landed 2026-04-20**, with a security-hardening commit on 2026-06-07
covering BOLA, TLS, credential logging and input validation. **Five months old and still
hardening.** Evidence: **OBSERVED**.

Its real limits: **no concurrency control, no batching, no canary, no health gate**. Bulk
and group command creation are flat loops, so an upgrade to a 500-node group queues 500
upgrades immediately. No rollback. The version *is* recorded, because heartbeats refresh
the OS-release map every 30 seconds, so convergence is visible after the fact, but nothing
gates on it. No heartbeat-age sweeper: the WebSocket teardown is the only place that marks
a node offline. Single instance, single database, one admin password, no RBAC and no
multi-tenancy. Evidence: **OBSERVED**.

**And it is close to invisible in the documentation.** `docs/reference/auroraboot.md` runs
880 lines and still scopes AuroraBoot as provisioning only; its "Scope" section is
download, prepare, provision, customize. A grep of the documentation and operator
documentation for `phonehome` or `phone-home` returns **zero hits**. A grep for "fleet"
returns one sentence. Evidence: **OBSERVED**.

**The consequence for this comparison is direct: a reader evaluating Kairos against a
commercial fleet manager from the documentation site alone would conclude that Kairos has
no fleet management at all.** It has a pull-based, store-and-forward, deny-by-default one,
with per-node API keys and BOLA protection, and it is undocumented.

### Cluster API

`cluster-api-provider-kairos` is functional, actively developed and released: 142 commits
since 2025-11-21, v0.1.2 on 2026-09-09, supporting single-node and HA k0s and k3s across
several infrastructure providers, and self-described as pre-1.0. A sibling,
`cluster-api-provider-kairos-fleet`, turns AuroraBoot's registry into Cluster API capacity.
The predecessor `kairos-capi` is archived. Evidence: **OBSERVED**.

**Cluster API is entirely absent from kairos.io.** A grep over the documentation for
`cluster-api`, `clusterctl` and "cluster api" returns exactly one hit, and it is a false
positive. Evidence: **OBSERVED**.

### Stale routing to archived repositories

Sixteen repositories were archived between 2025-09 and 2026-09, eleven of them in the
August-September 2026 consolidation. The current documentation tree has largely been
migrated, and `docs/architecture/meta.md` correctly points every runtime component at the
monorepo. What remains, ranked:

1. **Worst: `docs/examples/kubeadm-provider.md` and
   `docs/examples/bandwidth-optimized-upgrades.md`** carry runnable `curl` commands against
   `provider-kubeadm` releases and four separate freshness promises, including "always
   refer to the provider-kubeadm repository which contains tested configurations updated
   for the latest versions", against a repository archived 2026-09-03. **provider-kubeadm
   was not absorbed into the monorepo**; the live successor is `provider-kubernetes`, which
   the documentation never names.
2. Copy-paste install commands pinned to frozen `provider-kairos` release artifacts. They
   still resolve, because the monorepo kept the old tags resolvable, but they pin a frozen
   binary and the CLI is now `kairos provider <cmd>`.
3. **A cosign verification constraint** in `docs/upgrade/kubernetes.md` pinned to
   `provider-kairos/.github/workflows/release.yaml@refs/tags/*`. A supply-chain rule that
   will silently stop matching new releases.
4. Prose-level references in about eight further pages, low risk.

Evidence: **OBSERVED**. Healthy counter-example: the System Upgrade Controller page is
correctly marked deprecated.

## 12. Debugging and day-2 operations

**SSH.** Present, standard OpenSSH, with keys and users configured from cloud config.
Host keys are generated on first boot and persist because `/etc/ssh` is a persistent
state path, with a source comment explaining that the guard exists so later boots do not
break clients' pinned fingerprints (`08_ssh.yaml`). Evidence: **DOCUMENTED**.

**Local shell.** Present. This is an ordinary Linux userspace with whatever shell and
tools the base image ships. On Hadron that is musl plus systemd with no package manager,
so the toolset is fixed at build time. Evidence: **DOCUMENTED**.

**The local command surface is the strongest part of Kairos's day-2 story.** From
`origin/master:agent/pkg/cmd/root.go`, a single node-local binary offers: `upgrade`,
`reset`, `install`, `bootentry` (list and select boot entries), `grubedit` (read and
write GRUB environment variables), `state` (full machine state, with a `get` accessor for
dotted paths), `config` (the final merged configuration), `run-stage` (re-run any
lifecycle stage, with an `--analyze` mode), `sysext` and `confext` (list, enable, disable,
install, remove extensions), `kcrypt` (TPM NV inspection, unlock-all, re-key),
`pull-image`, `logs`, `phone-home`, `validate` and `print-schema`. All of it works with
no network, no Kubernetes and no management plane. Evidence: **DOCUMENTED**.

Two of those deserve specific credit because earlier research undersold them.

`kairos-agent bootentry --select fallback` **is** the rollback command, and
`kairos-agent bootentry` with no argument lists the entries interactively. It is a real,
first-class operation. It is documented only on the reset page
(`kairos-io/kairos-docs` `origin/main:docs/reference/reset.md:41,48,166`) and only as
`--select statereset`. So the command is documented; rollback as a procedure is not. That
is a narrower and fairer statement than "manual rollback is essentially undocumented".

`kairos-agent logs` **is** a support-bundle tool. It collects journal output from a
default list of eleven units (`kairos-agent`, `kairos-installer`, `kairos-webui`, the four
`cos-setup-*` units, `k3s`, `k3s-agent`, `k0scontroller`, `k0sworker`) plus
`/var/log/kairos/*.log`, `/var/log/*.log` and `/run/immucore/*.log`, into a gzipped tar,
with the list extensible from cloud config. Source:
`origin/master:agent/internal/agent/logs.go:39-60`. The Pulse brief records it as "kairos-agent
logs" without detail; it is more than that. Evidence: **DOCUMENTED**.

**Debugging a failed boot.** Two mechanisms, both real.

`rd.immucore.break=<step>` stops the boot before a named step in immucore's DAG and drops
to an interactive shell, dracut-style. `immucore --dry-run` prints the DAG so the step
names are discoverable. The README also documents the trap: systemd's
`TimeoutStartSec=` bounds how long you can sit at the breakpoint, and when it expires the
boot continues with none of immucore's mounts done and nothing printed. Source:
`origin/master:immucore/README.md`. Evidence: **DOCUMENTED**.

The in-RAM boot failure path writes a full-screen error to every console naming the exact
kernel option needed, then reboots so that boot assessment records the failure
(`origin/master:immucore/internal/utils/bootfailure.go`). That is unusually good
behaviour for a headless edge device and it should be recorded as such. Evidence:
**DOCUMENTED**.

**Rescue environment.** The `COS_RECOVERY` partition, from the GRUB menu, local, offline.

**Filesystem inspection and modification.** Full, from recovery: the state partition is an
ordinary ext4 filesystem holding ordinary files, and `active.img` is an ext2 image that
loop-mounts. An operator can inspect or repair a broken root with standard tools and no
project-specific knowledge. That is a direct benefit of the file-based slot design.
Evidence: **INFERRED** from the layout; **NOT TESTED**.

**Debugging with broken networking.** Everything above works offline.

**Debugging without Kubernetes.** Everything above works without it.

**Debugging under Trusted Boot: there is none, and the documentation says so.** Because
the kernel command line is measured, adding debug options changes the measurement, and
the Trusted Boot page states that the project "cannot advise how to proceed here to build
the UKI images with debug options yet". The mode intended for high-assurance deployment is
the one you cannot get a shell into. Evidence: **DOCUMENTED**.

**Serial console.** Mentioned in five documentation files but there is no dedicated
serial-console configuration page. For an edge and headless audience that is a gap, though
a smaller one than the Pulse brief implies, since the mentions do carry `console=` guidance in
context. Evidence: **DOCUMENTED** for the count; the judgement is mine.

**Logging, metrics and monitoring.** No documentation of any kind, beyond the `logs`
command. Evidence: **DOCUMENTED** (grep of the docs tree).

**Operational and security consequence of the model.** Kairos chooses SSH plus a full
local shell, which is the opposite of Talos's no-shell API-only model. The benefit is
that every failure mode below is debuggable with skills an operator already has, and no
part of the system is opaque. The cost is that the attack surface of a Kairos node is a
normal Linux attack surface, the blast radius of a compromised SSH key is a root shell,
and the machine can be modified by hand in ways nothing detects (dimension 1). Neither
model is better in the abstract; they trade auditability against recoverability.
[Evaluative comparison, flagged: **C-09**.]

## 13. Persistent state and storage

**Where the boundary sits.** Kairos draws it at the partition table. `COS_STATE` and
`COS_RECOVERY` hold replaceable infrastructure (the image files). `COS_OEM` holds
configuration. `COS_PERSISTENT` holds everything stateful. The root image is replaceable
by definition and the persistent partition is never touched by an upgrade. Evidence:
**DOCUMENTED**.

**Across reboot.** `COS_PERSISTENT`, `COS_OEM`, and the 37 bind-mounted state paths
persist. The tmpfs overlay over `/var`, `/etc` and `/srv` does not. Evidence:
**DOCUMENTED**.

**Across upgrade.** Same. The upgrade writes only inside `COS_STATE`, `COS_RECOVERY` and
(on `master`) the ESP. Evidence: **DOCUMENTED** from `upgrade.go`.

**Across reset.** By default, nothing: reset formats `COS_PERSISTENT`. With
`reset.reset-persistent: false` in the cloud configuration, persistent data survives.
`COS_OEM` survives unless `reset-oem` is set. Evidence: **DOCUMENTED**.

**Container runtime state.** `/var/lib/containerd` is a persistent state path, so the
image cache survives reboot and upgrade. Evidence: **DOCUMENTED**.

**Kubernetes state.** `/etc/kubernetes`, `/etc/rancher`, `/etc/k0s`, `/var/lib/etcd`,
`/var/lib/k0s`, `/var/lib/kubelet`, `/var/lib/rancher`, `/var/lib/calico`,
`/var/lib/cni` are all persistent. So is `/var/lib/longhorn`, `/var/lib/rook`,
`/var/lib/osd` and `/etc/pwx`, which is a notable detail: the shipped list already
accommodates Longhorn, Rook and Portworx. Evidence: **DOCUMENTED**.

**Customizable persistent paths.** Yes, two ways. `PERSISTENT_STATE_PATHS` can be
extended through `/run/cos/custom-layout.env`, and the documented cloud-config keys
`bind_mounts` and `ephemeral_mounts` do the same. The shipped `00_rootfs.yaml` implements
the merge. Evidence: **DOCUMENTED**.

There is a trap here that the source now documents and the documentation site does not,
and it is worth recording because it is the clearest example in the tree of persistence
and rollback interacting badly. A path under `/usr` must not be persisted: the shipped
configuration removed `/usr/libexec` from the list with the comment "A path under /usr is
owned by the image, so persisting it merges one slot's binaries into the other and breaks
rollback", referencing `kairos-io/kairos#4304`. Evidence: **DOCUMENTED**.

**The documentation page still advertises it.**
`kairos-io/kairos-docs` `origin/main:docs/architecture/immutable.md:48` lists
`/usr/libexec` in its "Default persistent paths" block. The same block **omits**
`/etc/ssl/private` and `/var/lib/confexts`, which the shipped configuration does include.
So the published list is wrong in both directions: it advertises a path that breaks
rollback, and it does not tell the reader that TLS private keys persist. The page does
close by pointing at the shipped file as "the most up-to-date list", which limits the
damage for a careful reader. Evidence: **DOCUMENTED**.

**Filesystems.** `ext4` for partitions, `ext2` for image files
(`sdk/constants/constants.go:47-48`), `vfat` for the ESP. Extra partitions created at
install default to `ext2` and accept a per-partition `fs` value. Evidence:
**DOCUMENTED**.

**LUKS.** Supported, per dimension 9, opt-in, TPM-bound.

**RAID, LVM, ZFS, Btrfs.** No first-class support in the install path. The documented
partition model is a fixed set of GPT partitions plus `extra-partitions` with a
filesystem each. `/etc/zfs` and `/var/lib/zfs`-adjacent paths appear in the persistent
list, which implies ZFS is expected to be usable on top, and there is a
`multi-disk-dynamic-partitioning` documentation page. But there is no documented way to
install the root onto a RAID array or an LVM volume. Evidence: **UNKNOWN** rather than
unsupported, per the framework's rule; what is DOCUMENTED is only that the install path
does not offer it.

**Additional disks and network storage.** `extra-partitions` at install, and the
`layout` stage for runtime partitioning. Network storage is the workload's problem; there
are no CSI assumptions in the OS, because the OS has no Kubernetes opinion when Kubernetes
is absent. Evidence: **DOCUMENTED**.

**The architectural reading.** Kairos's persistence model is a *list*. It works because
somebody enumerated 37 paths that matter, plus per-distribution extras for
Ubuntu/Debian (`/snap`, `/var/snap`, `/var/lib/snapd`) and the Red Hat and SUSE families
(`/usr/share/pki/trust`). That list is Kairos's real product in this dimension, and it is
also the maintenance burden: every new base distribution and every new storage or
networking component that writes somewhere unexpected needs an entry. A system that
persists by putting all state on a separate filesystem by construction does not have this
list and does not have this burden. A system that persists by enumeration can support
arbitrary bases. That is the trade, stated at its most concrete.
[Evaluative comparison, flagged: **C-10**.]

## 14. Networking

**This is the clearest flexibility cost in the whole profile, and it is a cost the
appliance projects do not pay.**

### There is no typed network API

`sdk/schema/root_schema.go`'s full field set is: bundles, config URL, environment,
fail-on-bundle-errors, GRUB options, install, options, users, P2P, debug, strict,
cloud-init paths, eject CD, full cloud config, cosign, verify, cosign public key, arch,
platform, squashfs compression settings, UKI max entries, and stages. **There is no
`network`, `dns`, `nameserver`, `interface`, `wifi`, `vlan`, `bond`, `bridge`, `hostname`
or `proxy` key.** The install schema likewise has none. Evidence: **OBSERVED**.

The only typed network primitives are inherited from yip: a `dns` plugin that writes
`/etc/resolv.conf`, and a `hostname` plugin with machine-ID templating. (yip's file named
`network.go` is not a network plugin; it is a hostname-regex stage guard.)

**Everything else, addresses, routes, VLANs, bonds, bridges, Wi-Fi, WireGuard, MTU and
IPv6, is raw `files:` and `commands:` writing distribution-native configuration.** And
validation does not catch mistakes: the schema is reflected without
`additionalProperties: false`, so unknown keys pass silently, and semantic validation has
exactly one cross-field rule. A wrong interface name or a malformed `.network` unit
surfaces as an unreachable node, not as a validation error. Evidence: **OBSERVED**.

[Evaluative comparison, flagged: **C-21**. Talos has a typed
`machine.network.interfaces[]` with bond, VLAN, bridge, WireGuard, DHCP, addresses and
routes; Bottlerocket has a `settings.network` API; Flatcar has typed Ignition into
systemd-networkd. Kairos has three stacks and asks the adopter to know which one their base
distribution produced. Those three comparisons were drawn from general knowledge, not from
those projects' primary sources, and must be verified before publication.]

### Three stacks, chosen by base distribution

| family | stack |
|---|---|
| Debian and Ubuntu | systemd-networkd plus systemd-resolved |
| SUSE (Leap, SLES) | networkd and resolved; **wicked is disabled and masked**, with the comment "Collides with systemd-networkd" |
| SLE Micro Rancher | networkd and resolved; NetworkManager disabled |
| **Red Hat family** (RHEL, Rocky, Alma, Oracle, CentOS, Fedora) | **NetworkManager**, plus `nmstate` installed. **No systemd-networkd package is installed** |
| Alpine | **connman** under OpenRC, plus `bonding`, `bridge`, `wpa_supplicant`, `wireguard-tools` |
| Hadron | networkd and resolved |
| Arch | **UNKNOWN**: declared as a distribution and a family, with no base-package entry and no network stage. No network manager is installed |

Evidence: **OBSERVED**.

**The DHCP default is a shipped yip stage, not a distribution default.**
`kairos-init/pkg/bundled/cloudconfigs/05_network.yaml` writes, in both `rootfs.before` and
`initramfs`, two systemd-networkd units matching `en*` and `eth*` with `DHCP=yes` and a MAC
client identifier, for every listed OS except Alpine. Two consequences follow. **Every**
`en*` and `eth*` interface takes a DHCP lease, so a multi-NIC host comes up with N leases
and N default routes. And `systemd-networkd-wait-online --any` means
`network-online.target` is satisfied by any one link. Evidence: **OBSERVED**.

### Feature by feature

| feature | verdict |
|---|---|
| DHCP | **DOCUMENTED** and shipped by default |
| static IP | **DOCUMENTED**, raw file only, with connman and networkd examples. **No NetworkManager example, so the Red Hat family flavors have no static-IP documentation at all** |
| bonding | **DOCUMENTED but wrong.** The networking page says bonding "can be configured via systemd-networkd (Ubuntu based images) and wicked (openSUSE based images)". `kairos-init` **disables and masks** wicked |
| VLAN | **ABSENT.** Zero hits in the documentation or in `kairos-init` |
| host bridges | **ABSENT.** Every `bridge` hit is EdgeVPN or a Kubernetes sysctl |
| Wi-Fi | **DOCUMENTED and narrow**: "Only Alpine (all architectures) and openSUSE (Raspberry Pi) currently have the necessary packages for WiFi support." Confirmed in the package maps. **No Wi-Fi on any generic amd64 flavor** |
| WireGuard | **UNDOCUMENTED**; tooling is Alpine-only |
| HTTP and HTTPS proxy | **ABSENT.** A grep for `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` and `ProxyFromEnvironment` returns **zero hits** across the monorepo, AuroraBoot and the documentation |
| corporate CA certificates | **partial and undocumented**, see below |
| IPv6 | **effectively UNDOCUMENTED.** The only two hits in the documentation are `IPv6 = off` inside connman examples. `DHCP=yes` gives v4 and v6 in networkd, so IPv6 works by accident rather than by design |
| multiple NICs | **INFERRED and unmanaged.** No documented way to select a primary, set route metrics, or bind Kubernetes or kcrypt to an interface |
| SR-IOV and RDMA | **ABSENT except one appliance.** `rdma-core` appears once, under the DGX Spark model, commented "Mellanox / ConnectX userspace from Ubuntu". Zero `sriov` or `infiniband` hits anywhere |
| nmstate | **installed on every Red Hat family image and never used.** A grep across the monorepo returns exactly the one package-list line. The obvious candidate for a declarative network API ships and is unwired |

Evidence: **OBSERVED** for every row.

### The proxy finding, stated precisely

There is no code, no documentation and no schema key. **INFERRED**: a proxy *would* be
honoured for image pulls, because the image extractor passes a nil round tripper and
go-containerregistry falls back to `http.DefaultTransport`, which carries
`Proxy: http.ProxyFromEnvironment`. **But nothing gets the environment variables to the
process.** yip's `environment:` module writes `/etc/environment`, which systemd units do
not read, and none of `kairos-agent.service` or the four `cos-setup-*` units carries an
`EnvironmentFile` or `Environment` directive. So an operator-scheduled or reconcile-driven
upgrade behind a corporate proxy will not pick the proxy up, while an interactive
`sudo kairos-agent upgrade` might, through PAM. The adopter must write a systemd drop-in,
and nothing tells them so. Evidence: **OBSERVED** for the source; **INFERRED** for the
runtime behaviour; **NOT TESTED**.

For a profile aimed at enterprise adopters this is one of the highest-impact gaps in the
document: a corporate proxy is not an exotic requirement.

### Corporate CA certificates

**The documented path is to turn TLS off.** `docs/advanced/private_registry_auth.md`
directs the reader to `--allow-insecure-registries`, implemented as
`InsecureSkipVerify = true`. The page is honest about the consequence. **There is no
documented "add my CA" path for registry TLS**, and no `RootCAs` or `x509.SystemCertPool`
handling exists anywhere in the agent, the SDK, `kairos-init` or immucore. Evidence:
**OBSERVED**.

**An undocumented path does work.** `/etc/ssl/certs`, `/etc/ssl/private` and
`/var/lib/ca-certificates` are persistent state paths, and the Red Hat and SUSE families
additionally get `/usr/share/pki/trust`. So a `boot`-stage yip step that drops a PEM and
runs `update-ca-certificates` survives reboot and upgrade, and because Go reads the system
pool on first use it would also fix the agent's image pulls. No documentation page, no
example, no test, no schema key. Evidence: **INFERRED** from the persistence layout; **NOT
TESTED**.

**The counter-example shows the project can do this well.** `kcrypt.challenger.certificate`
is a first-class typed CA pin with good documentation: "It is the PEM text itself, not a
path to a file. The node appends it to its system CA pool." One subsystem has exactly the
API the rest of the system lacks. Evidence: **DOCUMENTED**.

### Pre-Kubernetes networking, and the strongest property

**Network is in the initramfs of every non-Alpine image, unconditionally.** The dracut
module list always includes `network`, and a distribution-computed dracut configuration
selects the module: `systemd-networkd network-legacy` by default, with the comment
"network-legacy is needed for ipxe as it comes up very fast"; `network-manager` for the Red
Hat family; `systemd-networkd systemd-resolved` for Hadron. Evidence: **OBSERVED**.

`ip=` and `ifname=` work through dracut and are **documented nowhere**; only `rd.neednet`
appears in the configuration reference. **Alpine's initramfs is DHCP-only with no static
path**: its init picks one interface and runs `udhcpc`, with no `ip=` parsing. Evidence:
**OBSERVED**.

That combination produces a specific operational gap worth naming: online-mode disk
encryption needs `rd.neednet=1`, which gives DHCP and nothing else, so **there is no
documented way to give the initramfs a static IP on a node whose disk cannot be unlocked
without reaching a key server.** Evidence: **INFERRED**; **NOT TESTED**.

**The genuine strength on this dimension: cloud configuration is re-evaluated on every
boot, plus hourly.** Four shipped systemd units run `kairos-agent run-stage` for `fs`,
`boot`, `network` (ordered after `network-online.target`) and `reconcile`, with OpenRC
equivalents for Alpine, and immucore adds `rootfs` and `initramfs` to the boot DAG every
boot. **This is architecturally better than install-time-only configuration.** Its limit is
that what is re-evaluated is an arbitrary file-and-shell payload: the operator gets
idempotent *re-execution*, not idempotent *desired state*. A bad `.network` unit is
re-applied faithfully forever. Evidence: **OBSERVED**.
[Evaluative comparison to Talos's apply-config, flagged: **C-22**.]

**Remote reconfiguration** is a `NodeOp` running `sh -c 'cat > /host/oem/NN_net.yaml'` with
`rebootOnSuccess: true`, or AuroraBoot's `apply-cloud-config` command. No typed network
model, no dry run, and nothing that validates the unit before the reboot that applies it.
Changing a production fleet's network configuration is therefore a reboot-and-hope
operation. Evidence: **OBSERVED**.

### Documentation state

**One page.** `docs/advanced/networking.md` is roughly 160 lines: two paragraphs, a
static-IP example, a bonding example and a blog link. `docs/examples/wifi.md` is fifteen
lines. `docs/architecture/network.md`, where a reader navigating "Architecture, Network"
lands, **is the EdgeVPN peer-to-peer essay, not host networking.** Both were last touched
by a platform-migration commit in February 2026, not by a content update. Evidence:
**OBSERVED**.

**Two documentation-versus-source contradictions, both load-bearing.** The networking page
says "systemd-based flavors are all using `systemd-networkd`", which is **false for the
entire Red Hat family**; the Factory page says the opposite and matches the source. An
adopter on Rocky who follows the networking page writes a `.network` unit that nothing
reads. And the bonding claim points at wicked, which `kairos-init` masks. Evidence:
**OBSERVED**.

### One bright spot

**The MAAS path does translate a typed network model.** The curtin hook in AuroraBoot
translates MAAS-assigned network configuration, in either cloud-init v1 or netplan v2 form,
into systemd-networkd `.network` files written to `/oem/90_maas_network.yaml`. That is the
one place Kairos consumes a typed network model. It borrows someone else's. Evidence:
**DOCUMENTED**.

It is also proof that the translation layer is buildable: the code to turn a declarative
network model into Kairos's file-and-shell layer already exists for one provisioning path.

## 15. Supply-chain ownership and reproducibility

The framework's question is: could an organization independently recreate and operate what
it is running? For Kairos the answer is **yes for operation, no for bit-for-bit
recreation, and not without network access for the build.**

### What builds and what signs

The release entry point is
`kairos-io/kairos` `origin/master:.github/workflows/release.yaml`, which declares
`id-token: write` and fans out to reusable workflows. The signing step is in
`.github/workflows/reusable-factory.yaml:1214-1243`:

```yaml
- name: Sign image and artifact checksums with cosign
  if: inputs.cosign && inputs.registry_domain != ''
  env:
    COSIGN_YES: true
  run: |
    cosign sign ${{ steps.setup.outputs.image_tag }}
    for checksum in artifacts/*.sha256; do
      cosign sign-blob --yes --bundle="${checksum}.bundle" ... "$checksum"
    done
```

**Keyless signing is confirmed, not assumed.** A grep of every workflow file for
`COSIGN_PRIVATE_KEY`, `COSIGN_PASSWORD`, `--key ` and `cosign.key` returns zero hits.
With `id-token: write` and `COSIGN_YES: true`, this is Sigstore keyless with GitHub
Actions OIDC. Evidence: **DOCUMENTED**.

**There is therefore no project-held private key to lose, inherit or rotate.** That is a
real governance property and it should be recorded as one: the trust root is Fulcio,
Rekor and GitHub's OIDC issuer, none of which the project or its sponsor operates.

### SBOM and provenance: real, and documented in the wrong place

A documentation claim in `kairos-io/kairos-docs` `origin/main:docs/reference/image_matrix.md`
says SBOM lists "are regularly pushed via the CI as part of the Github releases assets"
at `https://github.com/kairos-io/kairos/releases/download/<VERSION>/<image>-sbom.spdx.json`.

Eight releases spanning four major versions were enumerated through the GitHub API
(v4.3.0, v4.2.0, v4.1.2, v4.0.0, v3.7.2, v3.5.0, v3.0.0, v2.5.0). **Zero assets match
`sbom` or `spdx` in any of them.** No Kairos release has ever shipped an SBOM as a GitHub
release asset. Evidence: **OBSERVED**.

The SBOMs do exist, in the registry. Querying quay.io anonymously for
`quay.io/kairos/hadron:v0.5.1-core-amd64-generic-v4.3.0` returns an OCI index
(`sha256:0642483e...`) carrying a BuildKit `attestation-manifest` child, and that manifest
holds two `application/vnd.in-toto+json` layers:

- `https://spdx.dev/Document`, 13,053,368 bytes
- `https://slsa.dev/provenance/v1`, 20,562 bytes

So Kairos ships both an SPDX SBOM and SLSA v1 provenance on every release image. Evidence:
**OBSERVED**. The Pulse brief recorded "provenance: unknown" and "No SLSA generator or level claim
was found". That is now resolved: provenance exists as a BuildKit in-toto attestation. The
project does not *claim* a SLSA level anywhere, which is a different and smaller gap.

The cosign signature is also present, and is attached through the **OCI 1.1 referrers
API** rather than the legacy `sha256-<digest>.sig` tag. A referrers query returns
`artifactType: application/vnd.dev.sigstore.bundle.v0.3+json`. A probe of the legacy tag
convention returns 404. Evidence: **OBSERVED**.

That combination produces a concrete operator trap. `check-the-signatures.md` tells the
reader to install "cosign v2.0.0 or later". For the `verify-blob` flow in that page, v2 is
fine, because the bundle is self-contained. For **image** verification of a current
release, a cosign v2 client looks for a `.sig` tag that is not there. The documentation
never mentions referrers or a minimum cosign v3. Evidence: **OBSERVED** for the registry
state; **INFERRED** for the client behaviour; **NOT TESTED** end to end.

There is also a **signer-identity inconsistency between two documentation pages**:
`docs/installation/check-the-signatures.md` gives
`.../.github/workflows/reusable-factory.yaml@refs/tags/$VERSION`, and
`docs/reference/image_matrix.md` gives `.../.github/workflows/release.yaml@refs/tags/<VERSION>`.
The signing step runs inside the reusable workflow, so that is the identity a certificate
SAN should carry. Both pages cannot be right, and a verification policy copied from the
wrong one would reject a genuine release. Evidence: **DOCUMENTED**; **NOT TESTED**
(no cosign run was made).

### What is signed and what is not

The v4.3.0 release has 57 assets: 10 ISOs with `.iso.sha256` and `.iso.sha256.bundle`
each, 23 Go binary tarballs across amd64, arm64, riscv64 and FIPS variants, and
`checksums.txt`.

**The ISOs are signed. The binaries are not.** `checksums.txt` has no `.sig`, `.pem` or
`.bundle` beside it. An operator who downloads `kairos-v4.3.0-linux-amd64.tar.gz`, the
agent binary that performs installs and upgrades on their fleet, has no signature to
verify, only an unsigned checksum file served from the same host as the binary. Evidence:
**OBSERVED**. This does not appear in any earlier research in this epic.

### Reproducible builds

**No claim is made and no tooling exists.** A grep of `origin/master` for
`SOURCE_DATE_EPOCH`, `reproducib`, `deterministic build` and `buildinfo` returns only
`Makefile:11: GOFLAGS ?= -trimpath`, which is necessary and far from sufficient. There is
no clamped mtime, no rebuild-and-compare job, no published build-input manifest.
Evidence: **OBSERVED**.

For the OS images this is structural rather than an oversight. `kairos-init` builds by
running the base distribution's package manager against live repositories (see below), so
bit-for-bit image reproducibility is out of reach without a snapshotted mirror.
Whether the Go binaries alone are bit-reproducible is **NOT TESTED**.

Per the framework's rule, missing documentation is not proof of absence, but here the
absence is of the mechanism, not of the documentation.

### Air-gapped build: the real limitation

This is the sharpest supply-chain finding, and it is a direct consequence of the
flexibility.

`kairos-init` converts a base image by driving that base's package manager.
`kairos-init/pkg/stages/steps_install.go` emits yip stages containing, among others,
`zypper -n --gpg-auto-import-keys refresh`,
`zypper -n install --force-resolution vim tpm2*`,
`dnf install -y epel-release || dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-%d.noarch.rpm`,
and `apt-get update`. The NVIDIA variants add third-party apt sources at
`repo.download.nvidia.com` and `developer.download.nvidia.com`. Evidence: **DOCUMENTED**.

So **the build stage requires network access to the base distribution's package
repositories and, for some targets, to a vendor's repositories.**
`kairos-io/kairos-docs` `origin/main:docs/examples/airgap.md` is about air-gapped
*install and runtime* (baking container images into a bundle); it builds by pulling from
`quay.io` and `wget`-ing from github.com. No documented air-gapped build path exists.
Evidence: **DOCUMENTED**.

An escape hatch exists but is not presented as one: `steps_install.go:30` honours
`--skip-step install-packages`, and `kairos-init --dry-run` prints "the resolved yip
stages ... the same format yip itself consumes". An operator could enumerate the package
set, mirror it, and point the base image at the mirror. That is standard practice and it
is not documented as a supported procedure. Evidence: **INFERRED**; **NOT TESTED**.

This is what "arbitrary base distributions" costs at the supply-chain layer. A project
that ships one fixed userspace it builds itself can make its build hermetic. A project
that converts anybody's userspace inherits everybody's package infrastructure.
[Evaluative comparison, flagged: **C-11**.]

### The independence test

BUILD, SIGN, HOST, INSTALL, BOOT, CONFIGURE, UPGRADE, ROLLBACK, RECOVER, evaluated stage
by stage against operator-controlled infrastructure:

| stage | self-hostable | required external dependency |
|---|---|---|
| BUILD | yes, with a caveat | base distribution package repositories, at build time |
| SIGN | yes | none forced; operator can use `cosign --key` or their own keyless identity. Trusted Boot keys are operator-generated by design |
| HOST | yes | none. Upgrade sources accept any OCI reference |
| INSTALL | yes | none. AuroraBoot builds ISO and raw images from a local OCI image |
| NETBOOT | yes | **none, and this is notable: there is no project-hosted netboot service at all.** AuroraBoot runs the whole netboot stack locally, and the docs carry a "Use your own netboot server" section |
| CONFIGURE | yes | none |
| UPGRADE | yes | none. Four documented source types including `ocifile:` from a local `docker save` tarball |
| ROLLBACK | yes | none, on-device |
| RECOVER | yes | none, on-device |

Evidence: **DOCUMENTED** for every row; **NOT TESTED** end to end, which is dimension 22.

Release *discovery* is the only convenience coupling: `kairos-agent upgrade list-releases`
defaults to `quay.io/kairos` and accepts `--registry`. A GitHub releases client exists at
`agent/pkg/github/releases.go` but is dead code in the shipped path (its only caller is
its own test). Evidence: **OBSERVED**.

### If the primary commercial sponsor's hosted services disappeared tomorrow

Stated factually, with no speculation about corporate behaviour, as the framework
requires.

**Spectro Cloud hosts no Kairos infrastructure that this audit could identify.** Every
endpoint in the release and runtime path belongs to a third party: quay.io for images,
github.com for source, releases and CI, Sigstore for the signing trust root, Netlify and
an LF-held domain for the docs site, LF Projects for the marks, LFX for the calendar,
matrix.org for chat.

**What would survive:** the Apache-2.0 source, every published image, every published
release asset, all Sigstore transparency-log entries, the SBOM and provenance
attestations, and the entire operator-side lifecycle in the table above.

**What would stop:** new development. Ninety-four percent of human commits over both the
12-month and 6-month windows come from four people employed by the sponsor (see dimension
16). A fork would be legally and technically unobstructed; the maintenance capacity would
have to be rebuilt.

**That distinction is worth carrying into the TAG paper**, because the two are usually
conflated and Kairos scores very differently on each. Kairos has a **capacity**
dependency on one company and essentially **no infrastructure dependency** on it. Several
projects in this comparison have the reverse shape. The Pulse brief recorded the infrastructure half
as a strength; this pass confirms it against the workflows and the registry rather than
against the documentation.

## 16. Governance and ownership

The framework asks for four properties to be kept separate: OPEN SOURCE, OPEN GOVERNANCE,
VENDOR-NEUTRAL OWNERSHIP, DIVERSE CONTRIBUTION. Kairos separates unusually sharply.

**Open source: yes.** Apache-2.0 on `kairos-io/kairos`. Evidence: **DOCUMENTED**.

**Vendor-neutral ownership: yes.** The kairos.io footer reads "Copyright © 2026 Kairos a
Series of LF Projects, LLC" and notes The Linux Foundation's registered trademarks. Marks
and project assets sit with LF Projects, not with the sponsor. This is the same legal
posture Flatcar has. There is no project-held signing key to own, because signing is
keyless. Evidence: **DOCUMENTED**; **UNKNOWN** for the domain registrant, which could not
be verified from here.

**Open governance: partial, and the detail matters.**

`kairos-io/community` `origin/main:GOVERNANCE.md` exists, is linked from `CONTRIBUTING.md`,
and is more complete than the Pulse brief summary implies. It describes itself as "loosely based on
the Kyverno Governance". It defines a four-rung ladder mapped to GitHub roles (Contributor
to Triage, Approver to Write, Maintainer to Maintain, Administrator to Admin), entry
requirements for each rung, a four-step onboarding process ("A new Approver, Maintainer,
or Administrator joins through nomination and a vote. Nobody self-applies for a role."), a
three-month inactivity offboarding rule, and an emeritus status with a documented path
back. Two named people have actually gone through the emeritus path. Evidence:
**DOCUMENTED**.

The voting thresholds are **not** in that document. They live in
`kairos-io/kairos` `origin/master:.gitvote.yml`, the CNCF GitVote bot's configuration:

| profile | duration | pass threshold | voters |
|---|---|---|---|
| default | 4 weeks | **100%** | maintainers |
| maintainer | 4 weeks | **100%** | maintainers |
| contributor | 4 weeks | 33% | maintainers and admins |

A maintainer vote requires **unanimity** of a six-person team, over four weeks. An adopter
reading the governance document learns none of this. Evidence: **DOCUMENTED**.
[Evaluative observation, flagged: **C-12**. A 100% threshold means any single maintainer
can indefinitely block a new one. That is a defensible choice and I found no rejected vote
to point at, so this is a structural observation and not a finding about outcomes.]

**What GOVERNANCE.md does not contain:** any conflict-resolution, escalation, appeal or
tie-break clause; any named arbiter; any statement of how the project decides on
contribution acceptance, requests to the CNCF, or changes to project goals; and any
maintainer-affiliation-update policy. A grep of the whole `community` repo returns nothing
on any of these. Evidence: **DOCUMENTED** for the grep; **UNKNOWN** for whether such
processes exist off-repo.

**Diverse contribution: low, and the project says so itself.**

Method, stated so the number is checkable: `git log origin/master --since=<date>
--no-merges --format='%an|%ae'` on the freshly fetched monorepo, split into bot/agent and
human by author name, then grouped by person and by email domain, then cross-referenced
against `community` `origin/main:MAINTAINERS.md` to attribute employer. Counts are
commits, not lines or pull requests. One caveat: the monorepo absorbed several standalone
repositories' histories in 2026, so these counts cover more surface than the pre-monorepo
`kairos` repo did.

| window | total non-merge commits | bot and agent | human |
|---|---|---|---|
| 12 months | 1688 | 995 (59.0%) | 693 |
| 6 months | 1062 | 641 (60.4%) | 421 |

Human commits, 12 months: Dimitris Karakasilis 387 (55.8%), Itxaka Serrano Garcia 161
(23.2%), Mauro Morales 77 (11.1%), Ettore Di Giacinto 29 (4.2%). **Top four: 94.4%, all
four employed by the primary sponsor.** Over 6 months the figure is 94.1%. The one
maintainer from a different company, William Rizzo of Mirantis, contributed 3 commits in
12 months. Evidence: **OBSERVED**.

Domain grouping alone would have been misleading here, and the correction is worth
recording as method: the four top contributors mostly use personal domains
(`karakasilis.me`, `kairos.io`, `mauromorales.com`, `localai.io`), so a raw domain
histogram shows about 8% `spectrocloud.com` when the real single-vendor figure is about
94%. The cross-reference against `MAINTAINERS.md` is what makes the number true.

**AI coding agents are a material and growing share of the commit history**, and that is a
fact about how this history is produced rather than a judgement about it. Over 12 months,
`mauro-agent` 45, `mudler-agent` 55 across two identities, `itxaka-agent` 30 across two
identities, `Copilot` 20: 150 commits, of which 149 fall in the last 6 months. The v4.3.0
release notes list `@mudler-agent` and `@itxaka-agent` under "New Contributors". These are
human-directed, so counting them as bots understates human involvement and counting them
as humans overstates distinct-person diversity. They are reported separately for that
reason. Evidence: **OBSERVED**.

`community` `origin/main:CONTRIBUTING_ORGANIZATIONS.md` lists exactly one organization,
and asserts: "As Kairos is a CNCF project, its development is driven by a diverse set of
contributors rather than a single vendor." The commit data does not support that sentence.
The same document is candid two paragraphs later: "we need more than one contributing
organization actively supporting the project." Evidence: **DOCUMENTED**.

**Maintainer structure:** six maintainers, five at the sponsor and one at Mirantis; four
administrators, all at the sponsor. Two emeritus maintainers, both from the sponsor.
Evidence: **DOCUMENTED**.

**A governance control worth crediting, because it is better than typical for the tier.**
`community` `origin/main:.github/workflows/repo-access-audit.yml` runs monthly and checks
that every repository in the organization grants the standard governance teams their
intended access, filing a drift issue when it does not. That is an automated enforcement
of the role ladder rather than a written promise of it. Evidence: **DOCUMENTED**.

**CLA or DCO:** DCO. **Relicensing:** would require the maintainers and, given LF Projects
holds the marks, LF involvement; not documented. **Release control:** the release workflow
runs on tag, and tagging requires write access, so release control sits with the
maintainers. Evidence: **DOCUMENTED** for DCO and the workflow; **UNKNOWN** for
relicensing process.

### CNCF status, verified directly

**Kairos is CNCF Sandbox.** From CNCF's own project page: "Kairos was accepted to CNCF on
April 13, 2024 at the Sandbox maturity level." Corroborated in `cncf/landscape`
`master:landscape.yml`, which carries `project: sandbox`, `accepted: '2024-04-13'` and
**no `incubating:` key**. Evidence: **DOCUMENTED**.

**Flatcar is CNCF Incubating**, accepted 2024-08-02, and entered **directly at
Incubating**; it never sat in Sandbox under CNCF. Its landscape entry carries both
`project: incubating` and `incubating: '2024-08-02'`. Evidence: **DOCUMENTED**.

**No incubation application has been filed for Kairos.** A search of `cncf/toc` issues for
"kairos" returns four hits, none of them an application (they are K3s and k0s incubation
issues and two TAG chair nominations). A search of `cncf/sandbox` returns only the
original 2023 sandbox application and the 2024 onboarding issue. So there is no public
General Technical Review, no Governance Review and no due-diligence record. Kairos has
been at Sandbox for about 29 months. Evidence: **OBSERVED**; **INFERRED** for "no
application filed", which is an inference from an absence and could be wrong if an
application exists somewhere not searched.

### What Sandbox versus Incubating actually implies

This is the governance gap the brief for this profile asks about, and it is worth answering with CNCF's own
criteria rather than with a vibe. From `cncf/toc`
`main:.github/ISSUE_TEMPLATE/template-incubation-application.md` (v1.6; the older
`graduation_criteria.md` now redirects to it), scored against Kairos's primary sources:

| incubation requirement | Kairos |
|---|---|
| OpenSSF Best Practices **passing** badge | **met**, at 100%, project 9100, linked from the README |
| Contributor ladder with multiple roles | **met** |
| Complete maintainer lifecycle including emeritus, with demonstrated use | **met**, two named emeriti |
| Public adopter list | **met**: 5 organizations (3 marked Production) and 3 individuals |
| At least 3 independent adopters, **TOC-verified** | listed, **not verified**, because no application exists |
| Public meetings on the CNCF calendar | **met**, LFX office hours |
| Governance documents vendor-neutrality of project direction | **not met**: asserted, not structurally guaranteed |
| Security response roles documented, including who triages | **not met**: `SECURITY.md` is an inbox, not a process |
| TAG Security self-assessment | **not found** in any kairos-io repository; **UNKNOWN** elsewhere |
| Documented release process | **not found** as prose; the pipeline exists, the document does not |
| General Technical Review, Governance Review, due diligence | **not done** |

So the honest summary of the gap is narrower and more specific than "Sandbox is less
mature than Incubating". Kairos already meets several incubation criteria that some
Incubating projects struggle with, notably the OpenSSF badge at 100%, the maintainer
lifecycle, and the adopter list. **What it does not have is the three things an operator
doing procurement actually reads: a documented security response process, a documented
release process, and a structural guarantee of vendor neutrality.** Those are also the
three the contribution data makes hardest to fix.
[Evaluative comparison against Flatcar, flagged: **C-13**.]

## 17. Project health and sustainability

**Age and volume.** First release 2021-07-30. 45 stable releases and 69 prereleases
matching `vX.Y.Z` among 215 release records. Current stable v4.3.0, 2026-09-08. Evidence:
**OBSERVED**.

**Release cadence.** Bimodal, not periodic. Over the 12.5 months from v3.6.0 to v4.3.0
there were 15 stable releases with a **median gap of about 4 days and a mean of about 20
days**: clustered patch bursts separated by 20 to 66 day feature gaps. Evidence:
**OBSERVED**.

Release candidates are used systematically. v4.3.0 had rc1 through rc7, v4.2.0 had rc1
through rc4. That is a real quality gate and it deserves crediting. Evidence:
**OBSERVED**.

**Maintenance branches exist in practice.** This corrects an impression left by earlier
research. Testing each recent tag for ancestry against `origin/master`: v3.5.10 and v3.5.9
are **not** ancestors. Their branch is `origin/release/v3.5.10`, whose merge base with
master is `b0099d7d` (2025-09-12), and v3.5.10 was cut on 2025-11-28, **ten days after
v3.6.0 shipped on master**. That is a genuine backport to an older line. Evidence:
**OBSERVED**. What does not exist is a published policy saying which lines get them.

**Issue and pull request velocity, last 90 days**, via `gh api search/issues` with explicit
page sizes (the default truncation at 30 would otherwise corrupt every count):

| metric | count |
|---|---|
| pull requests opened | 259 |
| pull requests merged | 174 |
| issues opened | 210 |
| issues closed | **295** |
| open issues now | 247 |
| open pull requests now | 37 |

Issues are closing faster than they open, and pull requests are not accumulating.
Evidence: **OBSERVED**. The caveat from dimension 16 applies: with about 60% of commits
from bots and agents, much of this throughput is dependency maintenance. It measures
pipeline health, not community momentum.

**Bus factor.** One person authored 55.8% of human commits over 12 months and 64.4% over
6 months. The top three account for about 90%, the top four for about 94%. **Bus factor is
1 for throughput and about 4 for continuity.** Real mitigations exist: five maintainers
hold Maintain rights, four administrators hold Admin, so there is no single-admin lockout,
and the monthly access audit keeps that true. Evidence: **OBSERVED**.

**Security response.** `SECURITY.md` is four sentences. Quoted in full, it supports
responsible disclosure, states there is no bug bounty, and gives two reporting channels (a
GitHub draft advisory and `security@kairos.io`). It has **no** supported-versions table,
**no** response commitment beyond "in a reasonable timeframe", **no** severity matrix,
**no** embargo policy, **no** PGP key and **no** named responders. Evidence:
**DOCUMENTED**.

Published advisories: **one**, `GHSA-fg9p-3w6c-652f`, critical, 2024-06-25. The org-wide
endpoint returned 404 to this audit, so the organization-wide count is **UNKNOWN** rather
than proven to be one.

**And yet the security engineering is substantially ahead of the security policy**, which
is the most interesting finding in this dimension. `kairos-io/security`
(`origin/main`, last commit 2026-09-10) holds `ksec`, an active Go pipeline that
discovers every tracked repository in the organization, collects image CVEs via Trivy,
source CVEs via govulncheck, GitHub alerts and Hadron component-manifest CVEs from OSV.dev
and NVD, correlates them into a graph mapping one Go CVE to the set of affected
repositories, triages, and renders a committed dashboard plus a tracking issue. It is
read-only against other repositories by design. It carries a `cve-policy.yaml` with an
explicit accepted-risk register. The release pipeline separately runs OSV-Scanner,
Scorecards, Trivy and Grype with SARIF upload, and v4.3.0's release notes carry a
generated "Security fixes" section. Evidence: **DOCUMENTED**.

None of that is linked from `SECURITY.md` or from the documentation site. An operator
doing diligence reads four sentences and concludes the project has no vulnerability
management. It has one; it just does not say so. Evidence: **DOCUMENTED** for both halves;
the reading is mine.

**Adoption.** `community` `origin/main:ADOPTERS.md` lists five organizations, three of them
marked Production, plus three individuals. Evidence: **DOCUMENTED**. GitHub stars are not
used as a quality signal here, per the framework.

**Commercial backing.** Spectro Cloud, which employs five of six maintainers and offers a
commercial support tier with CVE patch releases and long-term maintenance. That tier is
the only place a CVE patch commitment or long-term maintenance offering exists for Kairos.
Evidence: **DOCUMENTED** (from the Pulse brief vendor-page citation; not re-verified in this pass).

## 18. Operational lifecycle and support horizon

**There is no support-lifecycle page in the documentation.** The whole `kairos-docs` tree
on `origin/main` was searched for end-of-life, EOL, LTS, support window, support policy,
supported versions, maintenance branch and backport. `docs/` has no `support`,
`lifecycle`, `releases` or `eol` page at all. Evidence: **OBSERVED**.

The only substantive statement in the project's published material is in a **blog post**,
`blog/2026-08-18-kairos-v4-2-0-...md`, in a section titled "Kairos v3 reaches end of
life":

> We keep the latest patch of the three most recent major.minor lines, and v4.2.0 pushes
> v3 out of that window.

This is corroborated mechanically: `kairos-docs` `origin/main:versions.json` is exactly
`["v4.3.0","v4.2.0","v4.1.2"]`. Evidence: **DOCUMENTED**.

So a rule exists and is applied consistently. Three things make it insufficient as a
support horizon:

1. It is stated as a **documentation-publication** rule ("we keep the ... documentation"),
   not a security-support commitment. It does not promise patches or CVE fixes for those
   three lines.
2. It is **version-relative, not date-relative**. With a median 4-day inter-release gap,
   "the three most recent major.minor lines" gives an operator no date to plan against.
   v3 reached end of life on 2026-08-18 and v3.7.0 had shipped on 2026-02-02: about six
   and a half months of effective life for that line, with nothing guaranteeing the next
   one gets the same.
3. It is published in a **blog post**. Nobody doing procurement diligence on the
   documentation site will find it.

Evidence: **DOCUMENTED** for the rule and the dates; the assessment is mine.

**Not found anywhere:** an LTS designation, a channel model, a calendar-dated EOL table, a
stated minimum support duration, a deprecation-notice period, or a security-backport
commitment. Per the framework, absence of documentation is not proof that none of these
exist as informal practice; the maintenance-branch evidence in dimension 17 shows that at
least backporting does happen informally.

**Required upgrade frequency.** Effectively, keep up with the three most recent minor
lines. There is no long-term line to sit on. Evidence: **INFERRED**.

**Skipped upgrades.** No documented restriction. The single-image model makes an
N-to-N+3 jump structurally the same operation as N to N+1, because the whole root is
replaced. Whether persistent state or configuration schema survives such a jump is
**UNKNOWN** and is a good candidate for the follow-up experimental pass.

**Downgrade.** Possible by upgrading to an older tag. There is **no downgrade protection
in the agent**: nothing prevents pointing a node at an older image. `list-releases`
carries an `--all` flag whose help text says it includes "releases that would downgrade
Kubernetes", which implies the default view filters those out. Evidence: **DOCUMENTED**.

**Kubernetes compatibility.** Bound to the image tag, so an OS upgrade is a Kubernetes
upgrade on standard images. Covered in dimension 7.

**Kernel cadence and CVE cadence.** Tied to the base. On Hadron, the only base with
released images, the kernel is a vanilla kernel built by the Hadron pipeline, so cadence
is Hadron's. On a derived image it is the adopter's. There is no published kernel-update
cadence. Evidence: **UNKNOWN**.

**Enterprise support.** Exists as a commercial subscription from the sponsor. It is the
only place a CVE patch commitment and long-term maintenance appear.

**The multi-year operational burden.** Stated plainly: an operator running Kairos in
production over three years must accept that the upstream project publishes no support
window, so they either track the newest three minor lines continuously, buy the commercial
tier, or take over patching themselves. On a derived image, which is the recommended path
for every base except Hadron, the third option is already the default, and no
documentation page says so. That is the real compounding cost of this architecture, and it
is recorded again under dimension 20.

## 19. Resource footprint and performance

Measured where measurement was possible without booting anything. Everything requiring a
running machine is **NOT TESTED** and the experiment is named.

**Released ISO sizes, v4.3.0, exact bytes from the release API:**

| artifact | MiB |
|---|---|
| Hadron core arm64 | 281.7 |
| Hadron core amd64 | 290.7 |
| Hadron standard arm64, k3s | 375.6 |
| Hadron standard amd64, k3s | 395.9 |
| Hadron standard amd64, k0s | 505.1 |

The k0s standard ISOs are about 110 MiB larger than the k3s equivalents. Evidence:
**OBSERVED**.

**OCI image sizes, compressed layer sums from registry manifests:**

| image | MiB |
|---|---|
| `ghcr.io/kairos-io/hadron-trusted:v0.5.1` (base) | 134 |
| `ghcr.io/kairos-io/hadron:v0.5.1` (base) | 144 |
| `quay.io/kairos/hadron:v0.5.1-core-amd64-generic-v4.3.0` | 215 |
| `quay.io/kairos/hadron:...-standard-...-k3s-v1.36.4` | 322 |

So **Kairosifying Hadron adds about 71 MiB compressed** (kernel, initrd, the multi-call
binary, the installer, the provider and the cloud configurations), and k3s adds about 107
MiB on top. Evidence: **OBSERVED**.

**Cross-base comparison, v3.7.2 core amd64.** Directional only, because it is a different
Kairos version:

| base | MiB | relative to Hadron core v4.3.0 |
|---|---|---|
| Hadron (v4.3.0) | 215 | 1.0x |
| Rocky 9 | 369 | 1.7x |
| Debian 13 | 392 | 1.8x |
| Fedora 40 | 406 | 1.9x |
| Alpine 3.21 | 870 | 4.0x |
| openSUSE Leap 15.6 | 939 | 4.4x |
| Ubuntu 24.04 | 985 | 4.6x |

Evidence: **OBSERVED** for the figures; the cause of the Alpine result, which is
counterintuitive for a base marketed as minimal, is **NOT TESTED**.

This table is the concrete, measurable answer to "what does the choice of base cost", and
it argues *for* the Hadron decision on footprint grounds even while the same decision costs
the project its multi-base evidence (dimension 3).

**Partition arithmetic** is in dimension 4. The headline: about 4.5 GiB of fixed overhead
with the measured-size path on the Hadron core image, or about 16.3 GiB if size
measurement falls back to the 3072 MiB default.

**Documented minimums**, which do not reconcile: 8 GB disk and 2 GB RAM bare minimum in
the quickstart (16 GB and 4 GB practical, 32 GB and 8 GB recommended); 14 GB on the
multi-disk page; 30 GB on the Hetzner page; 35 GB in the getting-started guide; 40 GB in
the k0s cluster example; 16 GB SD card for Raspberry Pi. Evidence: **OBSERVED**.

**A documented size ceiling that is real and constraining:** UKI artifacts must stay under
roughly 300 to 400 MB, because "many EFI firmwares are very particular about the size of
the EFI image, often refusing to boot if the file exceeds 300-400MB". Kairos handles this
by shipping UKI images without kernel modules and firmware, with the stated consequence
that "certain hardware components may not function correctly". Evidence: **DOCUMENTED**.
That is a real and specific cost of Trusted Boot: it buys a verified chain and it costs
hardware breadth.

**NOT TESTED**, with the experiment that would settle each:

| unknown | experiment |
|---|---|
| uncompressed rootfs size per base | `skopeo copy` then `du -sh` on the unpacked rootfs; also validates the 2.5x sizing heuristic |
| boot time and steady-state idle RAM | boot each ISO in QEMU with fixed RAM, `systemd-analyze`, `free -m` at `multi-user.target`, then bisect RAM downward to find the real floor |
| real minimum disk | install against progressively smaller virtual disks until the partition-fit check errors |
| upgrade peak disk usage | instrument the state partition during an upgrade; the peak is the transition, active and passive triple |
| whether the 3072 MiB default ever takes effect | make `GetSourceSize` fail and observe the warning path |
| Hadron versus a glibc base on boot time and idle footprint | same hardware, same cloud-config, `systemd-analyze` on both |

## 20. Extensibility versus constraint

**Placement: a construction kit that ships one reference appliance, and the gap between the
two is where the risk lives.**

### Decisions the project makes, and whether an operator can override them

| decision | overridable |
|---|---|
| A/B plus recovery slot layout, GPT, `COS_*` labels | **no** |
| root image is a file, ext2, mounted read-only | **no** |
| image and partition sizes and filesystems | **yes**; a too-small state or recovery partition is silently raised with a warning |
| `/usr` read-only; `/etc`, `/var`, `/srv` on a tmpfs overlay | **partly**: `bind_mounts` adds persistent paths, `/usr` is excluded by design |
| the default persistent bind list | **additive only** |
| GRUB, or systemd-boot under Trusted Boot | **no** |
| yip as the configuration engine, with the full default plugin set and no allowlist | **no** |
| Kubernetes engine | **yes**, or none |
| base distribution | **yes**, the headline feature |
| kernel | **yes**, at build time |
| boot assets versioned with the image | **no**, and correctly so |

Evidence: **DOCUMENTED** and **OBSERVED** as cited in dimensions 2, 3 and 4.

**The contract a candidate base must satisfy is genuinely small**
(`docs/architecture/meta.md:20-31`): systemd 256 or later with systemd-boot for Trusted
Boot; systemd or OpenRC with GRUB otherwise; `CONFIG_EFI_STUB` if booting EFI. Three
requirements. That is real evidence for the meta-distribution claim and it should be
credited plainly.

### Can unsupported states be created?

**Yes, silently, at three levels.** Evidence: **OBSERVED**.

**At build time.** `kairos-init` does not fail on an unrecognised distribution. An unknown
`ID` or `ID_LIKE` produces `values.Unknown`, every package-map lookup returns an empty
value, and the build proceeds. The guardrail exists but is a **separate opt-in
subcommand**: `kairos-init validate` checks required binaries, `/boot/vmlinuz`,
`/boot/initrd`, the `/etc/kairos-release` keys, the dracut initrd contents, SSH host keys,
services and the kernel. It is **not** run by `-s install`, **not** by `-s init`, **not** by
`images/Dockerfile` and **not** by the release factory workflow. It is documented as a
manual step.

That combination is the sharpest form of the construction-kit risk in the whole profile: an
adopter can build a Kairos image from an unsupported base, get no error, and discover the
gap when a machine does not boot. The validator that would have caught it exists and is
off by default.

**At install time.** `install.no-format: true` and `install.force: true` deliberately skip
partitioning and format checks, which is correct for the cases they exist for.

**At runtime.** An unsigned, non-verity sysext is merged into `/usr` at the next boot on
the default path. A `run://` bundle executes as root with no verification. A
`kairos.config_url=` on the command line fetches and executes a remote configuration.

### Does customization weaken guarantees?

Yes, in named and citable ways, each of which is a real operational trap:

- **Rollback**: persisting anything under `/usr` "merges one slot's binaries into the other
  and breaks rollback". The default layout prevents it; a user `bind_mounts` entry under
  `/usr` is not blocked by anything found in the source.
- **Secure Boot**: swapping the kernel at build time without a matching signed shim and
  GRUB breaks the chain, which is precisely what the `grub.go` comment warns about.
- **Trusted Boot**: "Currently Alpine is not supported as it does not provide signed
  artifacts by default." Choosing Alpine costs Trusted Boot.
- **Atomicity**: a customized containerd "has to be repeated" after every upgrade. Runtime
  customization is not covered by the A/B guarantee.
- **Hardware coverage**: UKI images drop modules and firmware to fit under the EFI size
  limit. Trusted Boot costs hardware breadth.
- **glibc**: the default base is musl-only and cannot run glibc-linked host binaries.

Evidence: **DOCUMENTED** for each.

### Does flexibility increase the adopter's testing responsibility?

**Yes, and by an amount that can now be quantified.** For an adopter building on Ubuntu,
Alpine, Debian or Fedora today: zero QEMU tests run against their base in any executing
Kairos workflow (Rocky and openSUSE get one each, SELinux only; Ubuntu 20.04 gets two;
Hadron gets eleven). The broad `kairos-init` matrix that the documentation and the
announcement blog both cite as the evidence for multi-distro support has not executed since
2026-08-18 and cannot execute from its current location. The adopter owns signing,
scanning (offered as "Optional"), release cadence, and, undocumented, CVE response, testing
and versioning. Evidence: **OBSERVED**.

Even for Hadron, the release-time image scan runs in report-only mode with
`grype_sarif_fail_build: false`; only the Go-binary scan is a hard gate. So base-package
CVE posture is advisory even on the one base the project does ship. Evidence:
**OBSERVED**.

The project states the scaling problem in its own words, in the February 2026 blog post:
"the overall release matrix grew beyond what we could reliably sustain ... pushed us to
more than 500 artifacts per release cycle. At that scale, keeping pipelines, CI, and
verification checks consistently healthy became increasingly difficult, and the risk of
missing artifact signatures or specific version outputs was no longer acceptable."
Evidence: **DOCUMENTED**. That sentence is the clearest statement anywhere of what
extensibility costs an OS project, written by the project that paid it, and it belongs in
the TAG paper.

### Does constraint reduce operational complexity?

The Hadron decision is the experiment, and it is running now. Narrowing to one base bought
the project a sustainable release matrix and, measurably, an artifact 1.7 to 4.6 times
smaller than the alternatives. It cost the project its multi-base evidence and left the
homepage advertising a breadth the pipeline no longer demonstrates. Both halves are true
and both are the direct consequence of the same choice.

### Net placement

Kairos sits toward the **construction kit** end, and further toward it than any other
project in this comparison, because base-distribution choice is the one axis no other
project offers at all. The kit is real: 14 distributions recognised in code, a three-line
contract, arbitrary Dockerfile derivation, a documented kernel-swap path, and runtime
extensibility through cloud-config, system extensions and bundles.

The appliance it ships is also real, and narrow: Hadron v0.5.1, GRUB, non-FIPS, non-UKI,
amd64 and arm64 generic plus Raspberry Pi.

**The honest criticism is not that Kairos is too flexible.** It is that the advertised
breadth and the demonstrated breadth have diverged, that the evidentiary link between them
was severed by the monorepo migration on 2026-08-19 and has not been reconnected, and that
no documentation page tells the adopter standing in that gap what they have just picked up.
[Evaluative judgement, flagged: **C-15**.]

## 21. Failure experiments

**NOT TESTED.** No destructive experiment was run in this pass. The reason is recorded in
the scope section: the experiments need AuroraBoot and QEMU on a host that is currently
running a multi-day riscv64 build fleet, and a collision would cost both.

This section is therefore a specification rather than a result. The framework lists ten
experiments; for each, what the source reading above predicts, and what the experiment
would settle.

| # | experiment | predicted from source | what only the experiment settles |
|---|---|---|---|
| 1 | cut power during OS update | safe during the pull (transition image is separate); the window between the `active.img`-to-`passive.img` rename and the `transition.img`-to-`active.img` rename is not atomic | what GRUB does when `/cOS/active.img` does not exist. Whether recovery or fallback is reachable. Whether `syscall.Sync()` on each side is enough in practice |
| 2 | supply a corrupted new OS image | no signature check on the default path, so corruption is caught only when extraction or boot fails | where the failure surfaces: extract, boot, or silently. Whether boot assessment catches it. Whether a *partially valid* image (boots, broken userspace) passes assessment |
| 3 | introduce a kernel that cannot boot | boot assessment fires once and falls back to passive | that it actually fires; the time cost of the extra reboot; whether the `upgrade_failure` sentinel reaches userspace as documented |
| 4 | break Kubernetes after OS upgrade | **no rollback**, because the success criterion is reaching the `boot.before` cloud-init stage | confirmation that a healthy-boot/dead-cluster upgrade passes assessment. How long the node stays NotReady. Whether `NodeOpUpgrade` advances to the next batch anyway |
| 5 | corrupt persistent configuration | `/oem` is read at every stage; a malformed file's effect depends on `strict:` | whether a bad `/oem` file bricks the boot or is skipped. Whether `strict: false` (the default) really degrades gracefully. Whether recovery can still mount and repair `/oem` |
| 6 | remove network during upgrade | the pull fails, `transition.img` is removed by the cleanup stack, `active.img` is untouched | that the cleanup stack really runs on every failure path. Whether a half-pulled image leaves the state partition full |
| 7 | make the image registry unavailable | same as 6 for `oci:` sources; `ocifile:`, `dir:` and `file:` sources are unaffected | whether any part of the upgrade or boot path reaches the network when the source is local |
| 8 | fill the disk | the state partition is sized for two slots plus a transition image, so a full persistent partition should not block an upgrade | whether a full `COS_PERSISTENT` blocks boot (it holds `/var/log`, `/etc/ssh`, etcd). Whether a full state partition fails the upgrade cleanly or leaves no bootable slot |
| 9 | damage boot configuration | GRUB environment lives on `COS_STATE`; `grubedit` can repair it from a running system or from recovery | whether a corrupted `grubenv` is recoverable without external media. Whether the recovery entry survives damage to `grub.cfg` |
| 10 | remove the management plane | predicted to be a no-op: every lifecycle operation is node-local | confirmation that nothing degrades. This is the experiment Kairos should pass most comfortably, and it is worth running precisely because the prediction is confident |

Each run must record INITIAL STATE, FAILURE INJECTED, EXPECTED BEHAVIOR, OBSERVED
BEHAVIOR, FINAL MACHINE STATE, MANUAL INTERVENTION REQUIRED, DATA LOST, RECOVERY
PROCEDURE and TIME TO RECOVERY, per the framework. Experiments 1, 2 and 4 must be run on
both the GRUB path and the Trusted Boot path, because the two differ in signature
enforcement and retry count.

The central question the framework poses, "what does the machine do next", has a
source-level answer for most of these and an empirical answer for none.

## 22. Operational independence experiment

**NOT TESTED.** Same reason. Dimension 15 above establishes the documented and
source-level position for every stage; this dimension is the empirical confirmation of it,
and it has not been performed.

What the follow-up pass must do, stated as a runnable procedure:

1. Stand up a local OCI registry the operator controls. Mirror nothing in advance.
2. **BUILD.** Write a Dockerfile deriving from a chosen base and running `kairos-init`.
   Run it with the host's network reaching the base distribution's package repositories.
   Then run it again with all egress blocked, to establish exactly where the build breaks.
   Then run it a third time against a local package mirror and `--skip-step
   install-packages` where needed, to establish whether an air-gapped build is achievable
   at all and what it costs. This is the single most valuable experiment in the dimension,
   because the documentation does not address it.
3. **SIGN.** Sign the image with an operator-held cosign key, not keyless, and confirm
   `cosign: true` plus `cosign-key:` in the cloud configuration makes the agent enforce it
   at upgrade. This also settles whether the documented config keys actually work, which
   dimension 4 could only establish from source.
4. **HOST.** Push to the local registry. Block `quay.io` and `ghcr.io` at the network
   level from here onward.
5. **INSTALL.** Build an ISO with AuroraBoot from the local image and install a VM from
   it. Separately, run the netboot path end to end against AuroraBoot's own server.
6. **BOOT and CONFIGURE.** Confirm first boot applies a cloud configuration delivered from
   an operator-controlled URL.
7. **UPGRADE.** Build a second image, push, upgrade. Then repeat with an
   `ocifile:` tarball carried in by hand, with the registry unreachable.
8. **ROLLBACK.** Select the fallback entry and confirm the one-shot semantics.
9. **RECOVER.** Boot recovery and perform a reset with `reset-persistent: false`, then
   confirm what survived.

Record every point at which anything outside the operator's control is contacted. The
prediction from dimension 15 is that the only such point is step 2. Confirming or refuting
that is the whole value of the experiment.

Run the same nine steps on the Trusted Boot path with operator-generated keys enrolled in
an OVMF NVRAM copy. That path has a genuinely different independence profile, because the
operator necessarily holds the keys, and it is the only Kairos configuration where the
signed-chain question of dimension 9 has a positive answer.

---

## Claims that need Mauro's maintainer review before publication

The brief for this profile is explicit that Mauro's own authorship does not exempt a claim from review
discipline. This section separates the two kinds of claim in this document so the review
has a finite surface.

**Everything in this document that is a factual statement about Kairos, cited to a
repository ref, a file, a line, an API response or a registry query, is reviewable by
re-running the citation.** Those are not listed here. If a citation is wrong, it is wrong
and it should be corrected on the evidence.

**What is listed here is every claim that is evaluative rather than factual**: a comparison
against another project, or a judgement about what a fact means. None of these can be
settled by re-reading a file, and several depend on facts about other projects that this
pass did **not** verify from primary sources. **No comparative claim in this document
should be published before the corresponding project's own sources are checked, and every
negative claim about Kairos should be checked by Mauro before it is published anywhere,
including in the TAG paper.**

| id | dimension | the claim | why it needs review |
|---|---|---|---|
| **C-01** | 1 | "Talos, Bottlerocket and Flatcar all put dm-verity under the root on at least some paths; Kairos does not, on either path." | The Kairos half is verified from source. The other three are from general knowledge, not their primary sources |
| **C-02** | 1, 2 | Kairos's failure to record an image digest is a reproducibility gap relative to OSTree-based and Talos-style systems | The Kairos half is a verified grep result. The comparison and the word "gap" are a judgement |
| **C-03** | 4 | The architecture page's "tamper-proof upgrades" means atomic, not integrity-verified, and using it as the category's definition would mislead | The quote is verified. The reading of what a reader would assume is mine, and it is the central bias-control claim in the document |
| **C-04** | 4 | The v4.3.0 bootloader gap is a lifecycle hole in an otherwise correct architecture, rather than a failure to version the bootloader | The facts are REPRODUCED. The characterisation, and the implied comparison to bootc and Flatcar, is a judgement |
| **C-05** | 4 | The file-based A/B slot design trades deduplication for flexibility relative to an OSTree-style system | Not verified against OSTree's primary sources |
| **C-06** | 5 | A local recovery partition is a real strength relative to systems that recover by network re-imaging | The Kairos half is verified. Which other systems recover that way was not checked |
| **C-07** | 6 | The absence of configuration signing is a gap relative to Ignition's model | Ignition's actual signing and verification posture was not checked in this pass |
| **C-08** | 9 | No dm-verity on the root is "the clearest technical gap against the verity-based projects" | Same as C-01, plus the word "clearest" is a ranking |
| **C-09** | 12 | The SSH-plus-shell model and the no-shell API model "trade auditability against recoverability", and neither is better in the abstract | A framing judgement. Talos's model was not examined in this pass |
| **C-10** | 13 | Persistence by enumeration is the price of supporting arbitrary bases; a system that puts all state on a separate filesystem by construction does not pay it | The Kairos half is verified. The counterfactual is a judgement |
| **C-11** | 15 | Requiring the base distribution's package repositories at build time is what "arbitrary base distributions" costs at the supply-chain layer | The facts are verified. The causal claim is a judgement |
| **C-12** | 16 | A 100% maintainer-vote threshold on a six-person team means any single maintainer can indefinitely block a new one | The configuration is verified. No rejected vote was found, so this is structural, not an outcome |
| **C-13** | 16 | The specific Sandbox-versus-Incubating gap is "a documented security response process, a documented release process, and a structural guarantee of vendor neutrality", not general immaturity | Scored against CNCF's own template, which is verified. The selection of those three as the meaningful ones is a judgement. Flatcar's own posture on each was only partly checked |
| **C-14** | 3 | An appliance can say "version X equals state X", test one configuration exhaustively, and carry CVE response for the whole artifact; Kairos trades those three for base flexibility and runtime mutability | Talos, Bottlerocket and Flatcar were not audited in this pass |
| **C-15** | 20 | "The honest criticism is not that Kairos is too flexible. It is that the advertised breadth and the demonstrated breadth have diverged." | The underlying facts are OBSERVED. The framing is a judgement about the project Mauro maintains, and it is the sharpest sentence in the document |
| **C-16** | 7 | Kairos is structurally not a Kubernetes appliance, is less coupled than Flatcar in one dimension and more in another, and Bottlerocket's variant naming is the closest analogue | All three comparisons are from general knowledge, not primary sources |
| **C-17** | 8 | Adding support for standard UEFI hardware is "genuinely better than an appliance operating system whose kernel and kernel configuration are the vendor's" | The Kairos half is verified. The comparison is not |
| **C-18** | 8 | Hadron is "architecturally much closer to an appliance operating system than to pick your distribution" | A characterisation of the project's own flagship base, by the project's maintainer's own research. Needs his read specifically |
| **C-19** | 10 | The identity gap is not missing TPM code but attestation wired to the wrong subsystem, and Talos and the hyperscalers solve it differently | The Kairos half is OBSERVED in detail. The Talos and hyperscaler halves are from general knowledge |
| **C-20** | 11 | Bypassing the Eviction API is "below the bar `kubectl drain` sets" | The source behaviour is verified. The bar is a judgement, though a well-established one |
| **C-21** | 14 | The absence of a typed network API is "the clearest flexibility cost in the whole profile", and Talos, Bottlerocket and Flatcar all have typed models | The Kairos half is OBSERVED exhaustively. The three comparisons are from general knowledge and must be verified |
| **C-22** | 14 | Every-boot plus hourly re-evaluation is "architecturally better than install-time-only configuration" and comparable to Talos apply-config | The mechanism is verified. The comparison is not |

**Two further things for Mauro specifically, which are not comparisons.**

**The Secure Boot finding from the Secure Boot key-ownership task is still unconfirmed by the project.** The Secure Boot key-ownership task reproduced
that the published Hadron image ships unsigned boot binaries and flagged it for his
verification. Nothing in this pass changes that, and dimension 8 adds a fact that makes it
sharper: **there is no prebuilt Trusted Boot artifact at all in v4.3.0**, so the only path
with a signed chain currently has no released artifact. If the Secure Boot finding is
confirmed, that pair is the most consequential thing in this epic so far.

**Three findings in this document look like they may be unintentional regressions rather
than decisions**, and a maintainer can settle each in minutes where an outside researcher
cannot:

1. The `kairos-init` broad distribution test matrix cannot execute from its current
   location and has not run since 2026-08-18, while the documentation cites it as the
   evidence for multi-distribution support (dimension 3).
2. The UKI and FIPS release artifacts disappeared between v4.2.0 and v4.3.0, and the
   release workflow's own comment asserts v4.2.0 released none of them, which the registry
   contradicts (dimension 8).
3. The web installer binds all interfaces with no authentication and no TLS and is enabled
   on every live boot, with a twelve-line documentation page carrying no security note,
   while the sibling AuroraBoot netboot server carries a loud runtime warning for the same
   posture (dimension 10).

None of these has been reported anywhere. Per the constitution's read-only rule for
kairos-io, this pass filed nothing and commented nowhere.

## Open questions

Carried forward from the Pulse brief and still open, plus new ones from this pass. These are the
questions a maintainer interview would settle.

**New in this pass:**

1. Is the `kairos-init` distribution test matrix meant to run? If so, where should it live
   after the monorepo migration, and should the documentation's "validated through
   automated testing" sentence be qualified until it does?
2. Was the loss of the UKI and FIPS release artifacts between v4.2.0 and v4.3.0
   intentional?
3. Should the web installer get authentication, TLS, a loopback-only default, or at minimum
   the same security note AuroraBoot's netboot server carries?
4. Should the machine record the resolved image digest, not only the source string? This is
   a small change with a large effect on dimensions 1, 2 and 15.
5. `uki-max-entries` and `verify:` are both in the configuration schema and read by nothing.
   Are they intended, deprecated, or dead?
6. Is there a plan for a typed network model, given that `nmstate` already ships on every
   Red Hat family image and the MAAS path already translates one?
7. How should an operator behind a corporate HTTP proxy configure Kairos? Nothing in the
   source delivers proxy environment variables to the agent's systemd units.
8. Should the kcrypt challenger validate the EK certificate chain, and should there be a
   deny-unknown-TPM mode? `tpm-helpers`'s README currently claims a guarantee the code does
   not enforce.
9. Should the NodeOp controller read the node labels its own DaemonSet already writes, so a
   rollout can detect a node that fell back to passive?
10. What is the intended relationship between `kairos-operator` and AuroraBoot's fleet
    server? Today neither reads the other.
11. Should `docs/architecture/immutable.md`'s persistent-path list be generated from the
    shipped configuration rather than maintained by hand? It currently lists a path that
    breaks rollback and omits two that carry private keys.
12. Is `provider-kubernetes` the supported successor to `provider-kubeadm`, and should the
    documentation stop routing readers to the archived repository?

**Still open from the Pulse brief**, none of which this pass closed: which of the documented cosign
signer identities is correct; whether SBOMs are meant to return as release assets; what
governs which branches receive backports; what the CVE response commitment is for the
open-source project as distinct from the commercial tiers; whether Alpine, Debian and
Fedora remain supported bases; whether riscv64 is intended to become a released platform;
and whether Hadron is in scope for the CNCF project's governance, trademark and security
processes.

## Where Kairos fits, and where it does not

The framework's evaluation methodology asks for requirement profiles rather than a ranking.
This is a short, deliberately incomplete answer, because the full version belongs in the
synthesis once bootc and Flatcar have profiles of the same depth. Everything in this
section is a judgement built on the facts above, and all of it inherits the review
requirement.

**Kairos fits particularly well:**

- **A disconnected or air-gapped fleet that is already provisioned.** Upgrade, rollback,
  reset, re-key and inspection all work node-locally with no network, no management plane
  and no Kubernetes. The recovery image is on local disk. Upgrade sources include a plain
  tarball. Nothing in this comparison so far does offline day-2 operation better.
- **An organization with an existing Linux standard it must keep.** No other project here
  lets an adopter convert their own base with a Dockerfile. The contract a base must meet is
  three requirements long.
- **An organization that already has a container registry and CI.** The artifact is an
  ordinary OCI image, so mirroring, signing, content addressing and air-gapped transfer come
  from tooling the organization already runs.
- **A heterogeneous fleet on standard UEFI hardware**, where `--model generic` plus the
  adopter's own kernel is genuinely enough.

**Kairos fits badly, on the evidence in this document:**

- **A regulated environment that must prove what a machine is running.** No dm-verity, no
  runtime integrity verification, no digest recorded on the machine, no signature check on
  the default upgrade path, an unsigned released boot chain per the Secure Boot key-ownership task, and no prebuilt
  Trusted Boot artifact in the current release.
- **A factory scenario needing per-device identity.** Shared fleet-wide tokens,
  trust-on-first-use on both enrolment paths, and no per-device secret provisioning
  anywhere in the codebase.
- **An enterprise network.** No typed network model, no VLAN or bridge support, no proxy
  support, no documented corporate-CA path, and a networking page that is materially wrong
  for the Red Hat family.
- **An organization that needs a published support horizon.** No EOL policy, no LTS, and
  the only statement of a retention rule is a sentence in a blog post.
- **A large staged rollout with health gates.** The fleet layer has no canary, no health
  gate, no rollback, and a completion condition that cannot distinguish a working node from
  a broken one that rebooted.

**The pattern across those two lists is worth stating, because it is the finding that
generalises.** Kairos's architecture is strong exactly where the *machine* is the unit:
one image, one swap, one local recovery path, no dependency on anything remote. It is weak
exactly where the *fleet* or the *guarantee* is the unit: proving state, establishing
identity, gating a rollout, committing to a support window. That is a coherent shape, not a
random set of gaps, and the TAG paper's artifact-boundary comparison is the right place to
say so.

## Corrections this pass owes to earlier findings in this epic

The brief for this profile instructs that the Pulse brief's findings be verified rather than trusted. Most of them held.
These did not, or did not hold in the form they were written. Most of the corrections below
move in Kairos's favour, and that is the point: an audit that only ever confirms its own
negative priors is not an audit. One item (number 5) goes the other way and is recorded
with the same treatment.

They are listed here in one place so the TAG paper does not inherit a stale claim, and so
the Pulse brief's own profile can be amended if Mauro wants that.

**1. "There is no reconciliation loop."** There is. `cos-setup-reconcile.timer` runs
`kairos-agent run-stage reconcile` at boot plus 5 minutes and every 60 minutes after,
with an OpenRC equivalent, enabled by default
(`kairos-init/pkg/bundled/cloudconfigs/09_systemd_services.yaml:114-127`). The correct
statement is narrower: **Kairos ships a periodic stage-execution timer and no drift
detection.** No shipped configuration defines a `reconcile` stage, so the timer does
nothing until an operator hangs work on it. Evidence: **DOCUMENTED**.

**2. Factory reset "formats the persistent partition by default with no flag to prevent
it."** Half right. There is no *CLI* flag, and the source says so deliberately
(`agent/pkg/cmd/root.go:671-673`). But the cloud-config key `reset.reset-persistent`
exists and **is documented**, at
`kairos-io/kairos-docs` `origin/main:docs/reference/configuration.md:221`. Evidence:
**DOCUMENTED**.

**3. "Manual rollback works but is essentially undocumented."** Too strong on the command,
right on the procedure. `kairos-agent bootentry --select <entry>` is a first-class
command with an interactive listing mode, and it **is** documented, at
`docs/reference/reset.md:41,48,166`, though only as `--select statereset`. The accurate
statement is: **the command is documented for a different purpose; rollback as a
procedure is not documented at all, and the one-shot nature of the selection appears only
in a source comment.** Evidence: **DOCUMENTED**.

**4. Overlay size "25 percent in the shipped configuration and 20 percent in the component
README" recorded as a mismatch.** It is not a mismatch. 20% is immucore's *code* default
when no `rd.immucore.overlay` is given
(`immucore/internal/utils/mounts.go:311`), and the README documents that default
correctly. 25% is what Kairos's shipped cloud configuration passes
(`00_rootfs.yaml`). Same for the RW-path list: seven paths is immucore's code default
(`immucore/internal/constants/constants.go:9`), three is what Kairos overrides it to. Both
documents are accurate about the thing they describe. The real gap is only that **neither
figure is published on the documentation site.** Evidence: **DOCUMENTED**.

**5. "The docs still list /usr/libexec as a persistent bind mount ... The published
documentation therefore advertises a rollback-breaking configuration."** **This one holds, and it is worse than recorded.** The
shipped configuration on `origin/master` no longer lists `/usr/libexec` and carries an
explanatory comment naming `kairos-io/kairos#4304`. The documentation page still lists it:
`kairos-io/kairos-docs` `origin/main:docs/architecture/immutable.md:48`. The same page's
list also **omits** two paths the shipped configuration does have, `/etc/ssl/private` and
`/var/lib/confexts`. So the published list is wrong in both directions: it advertises a
path that breaks rollback, and it fails to mention that TLS private keys persist. The page
does point readers at the shipped file as "the most up-to-date list", which limits the
damage for a careful reader. Evidence: **DOCUMENTED**. This is not a correction to the Pulse brief;
it is a confirmation, upgraded with the second half.

**6. "provenance: unknown" and "No SLSA generator or level claim was found."** Provenance
exists. Querying quay.io directly returns a BuildKit attestation manifest carrying both an
SPDX SBOM and a `https://slsa.dev/provenance/v1` in-toto predicate for every release
image. What remains true is that **the project makes no SLSA *level* claim anywhere.**
Evidence: **OBSERVED**.

**7. "`kairos-agent logs`" recorded as the whole support-bundle story.** It is a real
support-bundle tool: eleven journal units by default plus three log-file globs, into a
gzipped tar, extensible from cloud config
(`agent/internal/agent/logs.go:39-60`). Evidence: **DOCUMENTED**.

**8. Maintenance branches recorded as inferred from "several v3.5.x releases published
after v3.6.0".** Confirmed precisely: v3.5.9 and v3.5.10 are **not** ancestors of
`origin/master`; their branch is `origin/release/v3.5.10`; v3.5.10 was cut ten days after
v3.6.0 shipped. Backporting demonstrably happens. Evidence: **OBSERVED**.

**9. "No support lifecycle, end-of-life or LTS policy is published anywhere in the
documentation."** Correct about the documentation. A rule does exist and is applied: "We
keep the latest patch of the three most recent major.minor lines", published in the
2026-08-18 release blog post and corroborated by `versions.json` holding exactly three
entries. It is a documentation-retention rule rather than a security-support commitment,
it is version-relative rather than dated, and it is in a blog post. All three are
criticisms; none of them is "no rule exists". Evidence: **DOCUMENTED**.

**10. The security-response picture.** The Pulse brief records `SECURITY.md`'s emptiness and the one
advisory, and mentions "a real, well-engineered scanning and triage program ... in a
separate repository". This pass confirms that program is substantially more developed than
that sentence conveys: `kairos-io/security`'s `ksec` does cross-repository CVE correlation
across the whole organization, with a committed dashboard, an accepted-risk register and a
tracking issue, alongside OSV-Scanner, Scorecards, Trivy and Grype in the release pipeline.
The correct framing is: **the security practice is well ahead of the security policy, and
the policy is what an evaluating operator reads.** Evidence: **DOCUMENTED**.

**11. "Two hard limits appear only in source: a 3072 MiB ceiling on the root image."** The
3072 MiB figure is a **default and an upgrade floor, not a ceiling**.
`agent/pkg/config/spec.go:173-182` overwrites all three image sizes with the measured
source size at install; the constant survives only when sizing fails. On upgrade the
configured value is a minimum, not a maximum (`spec.go:431-472`). The 64 MiB OEM figure is
correct. Evidence: **DOCUMENTED**.

**12. "ext2" applied to partitions.** `ext2` is the filesystem inside the image *files*;
the partitions are `ext4` (`sdk/constants/constants.go:47-48`). Evidence: **DOCUMENTED**.

**13. "Seven bases are advertised and one has released images."** Substantively right, with
three refinements. "Seven advertised" is the **marketing homepage only**; the documentation
site's image-matrix page and the v4.3.0 flavor selector both say Hadron, and the repository
README names no distribution at all. Ubuntu 22.04 does have two v4.3.0 **container** images,
for the NVIDIA Jetson Orin NX and AGX Orin, so two bases have a v4.3.0 artifact even though
only one has a released ISO. And the narrowing was an announced decision, in a Kairos blog
post of 2026-02-25, not drift. Evidence: **OBSERVED**.

Two things the Pulse brief recorded that this pass **confirms as written**, independently:

- **The default upgrade path verifies nothing.** Confirmed from
  `agent/pkg/elemental/elemental.go:432`, the `Cosign bool` zero value, and the absence of
  any verification flag on the `upgrade` command.
- **v4.3.0 does not refresh the bootloader.** Confirmed by
  `git merge-base --is-ancestor beaa9cc6 v4.3.0` returning non-zero.

## Method and limits

**What was done.** Every kairos-io clone used here was fetched fresh on 2026-09-16 and
read at `origin/<default-branch>` or at the `v4.3.0` tag, never at a working tree. The
default branch was checked per repository rather than assumed: `kairos-io/kairos` is
`master`, the others are `main`. Source claims cite repository, ref and path, and where
a line number is given it is from the ref named. GitHub and registry facts were obtained
with `gh api` and direct anonymous registry queries, with explicit page sizes, because
`gh` list and search commands truncate at 30 by default and a truncated count would have
corrupted several numbers in dimensions 15 and 17.

**What was not done, and why it matters for how much weight this document carries.**

- **No machine was booted.** No install, no upgrade, no rollback, no reset, no failure
  injection. Every behavioural claim is read off source or documentation and labelled
  accordingly. Where source and reality could diverge, that is said.
- **No image was pulled or built.** The registry facts in dimension 15 come from manifest
  and referrers queries, not from downloading an image. The Secure Boot artifact finding
  is the Secure Boot key-ownership task's, reproduced there and cited here.
- **No cosign verification was run.** The signer-identity inconsistency between two
  documentation pages is recorded as a contradiction that cannot both be right, not as a
  determination of which is right.
- **No maintainer was asked anything.** Per the funnel's bias control, no negative claim
  in this document has been put to the project. Nothing here is publication-ready for that
  reason, including the claims where the project is Mauro's own.

**Known weaknesses in the method.**

The commit-diversity numbers in dimension 16 are commit counts, not lines or pull
requests, and the monorepo consolidation in August 2026 pulled several repositories'
histories into the window. Both effects are stated where the numbers appear. The
classification of AI-agent accounts is a judgement call with no right answer, so those
accounts are reported as their own row rather than folded into either side.

Several findings are of the form "a grep returned nothing". The framework is explicit that
missing documentation is not proof of absence, and that rule is applied: those are labelled
DOCUMENTED for the search result and INFERRED or UNKNOWN for the conclusion. Where the
absence is of a *mechanism* in source rather than of a document, the label is stronger,
and the search terms are given so the search can be repeated.

Two dimensions, 21 and 22, are specifications rather than results, and they are the two
that would most change the conclusions of this profile. A reader should treat the
upgrade-failure and independence sections as well-founded predictions, not findings.
