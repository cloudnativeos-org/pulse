# Google Container-Optimized OS: platform profile

Tracked as ,
the research epic, Reproducible
Machine State.

Container-Optimized OS (COS) is Google's own minimal container host. It is a fork of the
Chromium OS open-source project, it ships Docker and containerd, and it is the default and
recommended node image for Google Kubernetes Engine. It belongs in this investigation for one
reason: it is an image-based operating system with a read-only root and an A/B root partition
scheme, built and operated by the same company that owns the platform it runs on. That makes it
a control case. Every other system in this comparison must answer "how do you get this onto a
machine you control." COS answers a narrower question, because Google controls the machine, the
image, the update path, the registry and the support contract at the same time. The value of
studying it is not to score it against portable systems. It is to see what a platform-controlled
surrounding environment actually changes about the machine-state problem, and what it stops
being able to answer.

**Depth tier: hyperscaler case study, documentation-based.** The epic's stratification puts COS
and Azure Linux in the same tier: study the architecture from primary documentation, explicitly
avoid reverse-engineering undocumented internals, and label evidence limits rather than filling
them. No experiments were run for this profile. No COS instance was booted. Nothing here is
REPRODUCED or OBSERVED, and that is by design, not by omission.

**Two facts bound what this profile can say, and both are published by Google.** COS "is not
supported outside of the Google Cloud Platform environment," and "Container-Optimized OS does not
accept direct contributions from the public." Several framework dimensions ask about portability
and community participation. For COS those questions have answers that describe a product
boundary, not a technical limit. Where that happens, this profile says so instead of forcing a
comparison that does not mean anything.

---

## Version and data provenance

| Field | Value |
|---|---|
| Version observed | `cos-129-19506-448-20` |
| Release date | 2026-09-08 |
| Channel | milestone 129 LTS |
| Kernel | COS-6.12.105 |
| Container runtimes | Docker v27.5.1, containerd v2.2.7 |
| Data collected | 2026-09-16 (baseline collected 2026-09-15) |
| Primary source | [COS milestone 129 release notes](https://docs.cloud.google.com/container-optimized-os/docs/release-notes/m129) |

Re-verified on 2026-09-16. `cos-129-19506-448-20` is still the newest build on the current LTS
milestone. The four preceding builds landed on 2026-08-31, 2026-08-24 and 2026-08-17, which is a
cadence of roughly one build per week.

Active LTS milestones and their published end-of-support dates, from the
[release notes index](https://docs.cloud.google.com/container-optimized-os/docs/release-notes):

| Milestone | End of support |
|---|---|
| COS 129 LTS | July 2028 |
| COS 125 LTS | February 2028 |
| COS 121 LTS | March 2027 |
| COS 117 LTS | September 2026 |

**A note on URLs.** Google's `cloud.google.com` documentation URLs now redirect to
`docs.cloud.google.com`. Both forms appear in older material. This profile cites the
`docs.cloud.google.com` form throughout.

**Relationship to the lighter profile.** A sibling ticket,
the Pulse brief, produced a 14-dimension Pulse
entry for COS on 2026-09-15 (`data/projects/cos.yaml`). This profile treats
that entry as a sourced factual baseline and reuses its citations where they overlap. Two places
where this profile refines the baseline are flagged inline, in dimension 1 and dimension 7. Both
are refinements from new primary evidence, not contradictions.

---

## 1. Definition and implementation of immutability

COS splits the boot disk into three partition classes: a root partition mounted read-only, a
stateful class that is writable and survives reboot, and a stateless class that is writable and
does not. The root filesystem "is always mounted as read-only. Additionally, its checksum is
computed at build time and verified by the kernel on each boot."

The published mount layout is specific enough to reason about:

| Path | Mode | Persistence | Executable |
|---|---|---|---|
| `/` | read-only | image | yes |
| `/home`, `/var` | writable | stateful | no |
| `/var/lib/google`, `/var/lib/docker`, `/var/lib/toolbox` | writable | stateful | yes |
| `/var/lib/cloud` | writable | stateless | yes |
| `/etc` | writable | stateless | yes |
| `/tmp` | writable | stateless | no |
| `/mnt/disks` | writable | stateless | yes |

The operationally interesting property is not the read-only root. It is the stateless `/etc`.
`/etc` is writable at runtime, so a process can change system configuration, but nothing written
there survives a reboot. Google draws the consequences out directly. `systemctl enable` in a
cloud-init `runcmd` block "will not work as intended." `/etc/fstab` cannot be used to mount disks
at boot, because "`/etc/` is stateless on Container-Optimized OS." `iptables` rules "will not
persist across reboots." OS Config `recipes`, which run once per instance on other
distributions, "are run on every boot" here. So do cloud-init's `write_files` and `runcmd`.

This inverts the usual drift model. On a conventional Linux host, system configuration
accumulates and drifts away from its declared source. On COS, system configuration is destroyed
at every reboot and rebuilt from the instance metadata. Drift in `/etc` cannot survive a restart.
The cost is the mirror image of the benefit: anything an operator has not expressed in cloud-init
is lost the moment the machine reboots, and a machine that has been up for 200 days may have a
running configuration that no longer matches what a reboot would produce. Reboot becomes the
reconciliation event.

Two things sit outside that model and are worth naming. `/var/lib/docker` is stateful, so pulled
container images persist across reboot. `/var/lib/toolbox` is stateful, so a debugging
environment persists. Both are machine-local state that the image version does not describe.

**Does a version uniquely identify machine state?** Partially. The image version fixes the root
filesystem exactly. It says nothing about the stateful partition, the container image cache, the
installed GPU driver, or any attached persistent disk. An operator reads the actual OS version
from `/etc/os-release`, where `VERSION_ID` is the milestone and `BUILD_ID` is the build number.

**Whether the integrity mechanism is dm-verity is UNKNOWN for the stock image, and the
distinction matters.** The COS security page describes a checksum computed at build time and
verified by the kernel at boot. It does not say dm-verity. Google does name dm-verity in two
adjacent places: the Confidential Space image, which "builds on the existing security
enhancements of Container-Optimized OS," states that "Root-fs in the Confidential Space image is
integrity protected by `dm-verity`" with the root hash passed on the kernel command line; and
cos-customizer's `seal-oem` build step "utilizes dm-verity to verify the data in the OEM partition
when the system boots." Neither statement is about the stock COS root filesystem. This profile
records what each source supports and does not merge them.

**Evidence**

- DOCUMENTED: read-only root, build-time checksum, kernel verification at boot. Source: [COS security overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/security)
- DOCUMENTED: partition classes and full mount table. Source: [Disks and filesystem overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/disks-and-filesystem)
- DOCUMENTED: `systemctl enable` and `/etc/fstab` limitations, cloud-init on every boot. Source: [Creating and configuring instances](https://docs.cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance)
- DOCUMENTED: iptables rules do not persist. Source: [Configuring the host firewall](https://docs.cloud.google.com/container-optimized-os/docs/how-to/firewall)
- DOCUMENTED: OS Config recipes run on every boot. Source: [OS Config guest policies](https://docs.cloud.google.com/container-optimized-os/docs/how-to/osconfig)
- DOCUMENTED: `VERSION_ID` and `BUILD_ID` in `/etc/os-release`. Source: [Versioning scheme](https://docs.cloud.google.com/container-optimized-os/docs/concepts/versioning)
- DOCUMENTED: dm-verity on Confidential Space root-fs. Source: [Confidential Space security overview](https://docs.cloud.google.com/docs/security/confidential-space)
- DOCUMENTED: dm-verity on a sealed OEM partition. Source: [cos-customizer README](https://cos.googlesource.com/cos/tools/+/refs/heads/master/src/cmd/cos_customizer/README.md)
- INFERRED: the kernel refuses to boot when the root checksum fails. The security page states that the checksum is verified. It does not state the failure behaviour. The Pulse baseline stated the refusal directly; this profile treats the refusal as the reasonable reading of "verified" rather than as a quoted claim.

**UNKNOWN, and expected**

- Whether the stock COS root filesystem uses dm-verity. The concept pages describe the property, not the mechanism. Google has no reason to document an internal mechanism for an image the customer cannot rebuild in place.
- What the kernel does on a checksum mismatch.
- Whether the stateful partition is guaranteed to survive an A/B upgrade. Nothing states it as a guarantee.

---

## 2. Unit of OS deployment

The unit is a Compute Engine disk image, published in the public `cos-cloud` project and selected
by image family. It is not published as a downloadable file, and no torrent, tarball or OCI
artifact of the OS exists in the documentation.

Four families exist per architecture. `cos-[MILESTONE]-lts` is the production track with 26
months of support. `cos-stable` carries the latest production-ready milestone and is "updated
every 4 months." `cos-beta` is the next major release in stabilization. `cos-dev` is the
in-development track. Arm variants use `cos-arm64-*`. Google's own guidance is to avoid the
family API for production: "You should always refer to a specific image you have qualified for
use in production."

The artifact is whole-system. Updates replace "the OS image in its entirety, including the
kernel, as opposed to package-by-package updates like on traditional Linux distributions." Kernel,
initramfs and userspace move together. Boot assets are not versioned separately.

Google publishes real per-build supporting artifacts, which is more than the "vendor image only"
summary would suggest. Archived kernel sources and kernel headers for every build live in a public
bucket at `gs://cos-tools/<build-number>/`, with Arm variants under a `lakitu-arm64` subdirectory.
A per-milestone OVAL vulnerability feed lives at `gs://cos-oval-vulnerability-feed`. Every image
carries `/opt/google/chrome/resources/about_os_credits.html`, which "contains version and license
information for all the packages used to build that image." A `cos-package-info.json` file on the
running VM feeds the OVAL scanning workflow. This is a package inventory that an operator can
read. It is not an SBOM in a standard interchange format, and Google does not call it one.

OCI involvement exists, but only for the companion tooling, not for the operating system. Toolbox
ships as `gcr.io/cos-cloud/toolbox`, cos-customizer as `gcr.io/cos-cloud/cos-customizer`, and the
GPU installer is pulled from a Google registry as well.

**Evidence**

- DOCUMENTED: image families, milestone and build numbering, pinning guidance. Source: [Versioning scheme](https://docs.cloud.google.com/container-optimized-os/docs/concepts/versioning)
- DOCUMENTED: whole-image update including the kernel. Source: [Automatic updates](https://docs.cloud.google.com/container-optimized-os/docs/concepts/auto-update)
- DOCUMENTED: `gs://cos-tools/<build>/` kernel sources and headers, `about_os_credits.html`. Source: [COS sources](https://docs.cloud.google.com/container-optimized-os/docs/resources/sources)
- DOCUMENTED: OVAL feed at `gs://cos-oval-vulnerability-feed` and the `cos-package-info.json` workflow. Source: [Scanning for vulnerabilities with the OVAL feed](https://docs.cloud.google.com/container-optimized-os/docs/how-to/scanning-with-oval-vulnerability-feed)
- DOCUMENTED: a third party can build the image from public source, see dimension 15

**UNKNOWN, and expected**

- Whether the published image is content-addressable, and whether a digest is exposed. No digest appears in the documentation.
- Whether the image is signed, and with what. The auto-update page implies signing keys exist, because it says images released before a key rotation cannot update past it, but it never describes the scheme.
- Whether the image can be mirrored, and whether any air-gapped installation path exists. Neither is documented, and for a product that is cloud-only by definition, neither would be.

---

## 3. OS construction and customization

There is no package manager on a running COS instance, and Google closes that door explicitly:
the "`packages` and `packageRepositories` features of guest policies are not supported on
Container-Optimized OS." So the whole customization story lives elsewhere, and it is richer than
the absence of a package manager suggests.

**Build time, using cos-customizer.** cos-customizer is a documented tool that produces a
customized COS image. It "uses Daisy to create a COS VM instance, load data onto the instance, and
create a disk image from the modified instance," and it runs "as part of a Google Cloud Build
workflow as a sequence of Google Cloud Build build steps." The subcommands map directly onto the
customization questions this framework asks: `run-script` executes arbitrary scripts on the
builder VM, `install-gpu` preloads NVIDIA drivers, `seal-oem` applies dm-verity to the OEM
partition, `disable-auto-update` turns off the updater and reclaims its disk space,
`anthos-installer-install` installs application binaries, and `sed-grub-config` edits the GRUB
config and the kernel command line. That last one is notable. An operator can change kernel
command-line arguments in a built image.

Two caveats attach to cos-customizer and both are published. It runs on Google Cloud Build against
a builder VM in Compute Engine, so image construction itself depends on Google's platform. And its
README carries the line "This is not an official Google product."

**Full source build.** The whole distribution can be rebuilt. Google documents the procedure:
install `depot_tools`, `repo init https://cos.googlesource.com/cos/manifest.git`, `repo sync`,
`cros_sdk --enter`, then `build_packages --board=lakitu` and `build_image --board=lakitu test`.
The Arm board is `lakitu-arm64`. The result can be booted locally under KVM or QEMU, and imported
into Compute Engine as a custom image. This is a genuine construction-kit escape hatch, and it is
a Portage and board-overlay workflow inherited from Chromium OS, not a container build.

**First boot and every boot.** cloud-init through instance metadata, plus startup scripts, plus OS
Config recipes. All of them re-run on every boot because `/etc` is stateless.

**Runtime.** Containers are the intended answer. Toolbox is the escape hatch for the operator, a
Debian environment stored under `/var/lib/toolbox` with the host root visible at `/media/root`,
persistent across reboots, and documented as "a debugging utility and not intended for production
use."

**GPU drivers.** This is the strongest first-party extension path in the product.
`sudo cos-extensions install gpu` installs NVIDIA drivers into `/var/lib/nvidia`. Versions can be
pinned four ways: `default`, `latest`, an exact version such as `535.183.01`, or an NVIDIA branch
such as `R535`. The constraints are stated: the milestone must be LTS and at least 85, Arm images
do not support the feature, and the tool needs the
`https://www.googleapis.com/auth/devstorage.read_only` scope to reach the Google registry, without
which "downloading of the driver and its dependencies will fail." Google also documents that "you
need to run the preceding command on every VM reboot to configure GPU drivers."

**Out-of-tree kernel modules are where the constraint is hardest, and it is worth stating
precisely.** Without the GKE secure kernel module loading feature, CPU and TPU nodes run COS with
the LoadPin LSM enabled, which "restricts any OOT kernel module loading," while GPU nodes run with
LoadPin disabled, which "allows loading OOT modules" and which Google itself describes as "less
secure by default." With the feature enabled, there are two policies:
`ENFORCE_SIGNED_MODULES` "enforces that any out-of-tree kernel modules are signed by Google," and
`DO_NOT_ENFORCE_SIGNED_MODULES` "allows any kernel module, signed or unsigned, to be loaded."
Google states the supported set plainly: "only Google-signed OOT modules are allowed." A third
party cannot sign its own module with its own key and have it accepted under the enforced policy.
The feature requires GKE 1.34.1-gke.2364000 or later for CPU and TPU nodes, and 1.36.0-gke.1585000
or later for GPU nodes.

**The extensibility and controlled-state tradeoff, stated as COS makes it.** Google decides the
base distribution, the kernel, the kernel configuration, the package set, the init system, the
container runtimes, the filesystem layout and the module trust anchor. An operator can change the
image at build time and the machine at boot time, but cannot change the running system's package
set at all, and cannot introduce a kernel module on its own authority under the enforced policy.
The guarantee this buys is that the running root filesystem is exactly what Google built and can
be verified as such. The price is that a driver the operator needs and Google has not signed is a
blocked requirement, not a hard one.

**Evidence**

- DOCUMENTED: no package or repository management. Source: [OS Config guest policies](https://docs.cloud.google.com/container-optimized-os/docs/how-to/osconfig)
- DOCUMENTED: cos-customizer subcommands, Daisy, Cloud Build, the non-official-product disclaimer. Source: [cos-customizer README](https://cos.googlesource.com/cos/tools/+/refs/heads/master/src/cmd/cos_customizer/README.md)
- DOCUMENTED: full source build procedure and board names. Source: [Building from open source](https://docs.cloud.google.com/container-optimized-os/docs/how-to/building-from-open-source)
- DOCUMENTED: GPU driver install, version pinning, milestone floor, Arm exclusion, required scope, per-reboot requirement. Source: [Running instances with GPU accelerators](https://docs.cloud.google.com/container-optimized-os/docs/how-to/run-gpus)
- DOCUMENTED: LoadPin default behaviour, the two module policies, Google-signed-only, version floors. Source: [GKE secure kernel module loading](https://docs.cloud.google.com/kubernetes-engine/security/secure-modules-cos)
- DOCUMENTED: toolbox behaviour and the production disclaimer. Source: [Debugging node issues using toolbox](https://docs.cloud.google.com/container-optimized-os/docs/how-to/toolbox)

**UNKNOWN, and expected**

- Whether an operator can install a corporate CA certificate into the trust store in a supported way. Not documented.
- Whether a FIPS-validated cryptographic module or FIPS mode exists. Not documented.
- Whether third-party security or monitoring agents that need kernel modules have any supported path outside the Google-signed set.
- Whether the LoadPin restriction applies to standalone Compute Engine VMs or only to GKE node pools. The documentation is written from the GKE side.

---

## 4. Upgrade mechanism

**Before the upgrade.** The new OS comes from a Google-operated update service. The instance
itself initiates the update, not an external controller. Automatic updates are controlled by the
`cos-update-strategy` instance metadata key, set to `update_enabled` or `update_disabled`, and
"metadata flags defined at instance level takes precedence over metadata flags defined at project
level." No Kubernetes is involved, and no Kubernetes is required.

**A default changed and the documentation still contradicts itself about it.** "In milestone 117
and later, the automatic updates feature is disabled by default on all Container-Optimized OS
images. In milestones earlier than 117, the feature is enabled by default." The features and
benefits page still says COS instances "are configured to automatically download weekly updates in
the background." Both pages are current Google documentation. This is recorded as a documentation
conflict, not resolved.

**During the upgrade.** COS "uses an active-passive root partition scheme." The new image is
written to the passive partition. The running root filesystem is not modified. "The update does not
take effect until the instance is rebooted, and the auto-updater does not force reboot when an
update is installed." Once an update is staged, "the instance must be rebooted before it can
update to a newer version," so a machine that never reboots stops accumulating updates after one.

**Two documented limits matter for planning.** In-place updates "are not supported on
Container-Optimized OS VMs with UEFI Secure Boot enabled," and they "are not supported on
Container-Optimized OS Arm-based images." The first is the awkward one. Secure Boot and automatic
patching are two things a security-minded operator would want at the same time, and on COS they
are mutually exclusive.

**Verification of the payload is not documented.** The only adjacent evidence is the key rotation
note: images released before a key rotation cannot update to versions released after it, and the
affected instances must be recreated. That implies signing keys exist and are rotated. It does not
describe the verification scheme, the algorithm, or the rotation policy. The update server is never
named in Google's documentation.

**Reboot and boot selection.** GRUB is the bootloader. Google's `cos/cobble` repository is a
GRUB fork ("grub-lakitu") carrying commits for TPM support, secure boot handling, and making the
GRUB config read-only under Secure Boot. cos-customizer's `sed-grub-config` step edits the GRUB
config. So the bootloader is known. How the bootloader chooses between the two root partitions,
whether boot attempts are counted, and whether a boot is marked successful are all UNKNOWN. This
profile deliberately does not infer that behaviour from the Chromium OS lineage. That inference
would be reverse-engineering, which this tier excludes.

**The GKE path is a different mechanism entirely.** Node pool upgrades do not use the in-place
A/B updater. They provision new nodes, cordon and drain the old ones, and delete them. That is
image replacement. Google publishes a JSON mapping of GKE patch versions to COS node image
versions, updated roughly weekly with a `creation_time` field, so an operator who needs a specific
COS build can reach it by choosing a GKE patch version.

**Evidence**

- DOCUMENTED: active-passive scheme, whole-image update, no forced reboot, reboot-before-next-update, `cos-update-strategy`, the M117 default change, Secure Boot and Arm exclusions, key rotation. Source: [Automatic updates](https://docs.cloud.google.com/container-optimized-os/docs/concepts/auto-update)
- DOCUMENTED: the conflicting weekly-automatic-update statement. Source: [COS overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/features-and-benefits)
- DOCUMENTED: Arm images do not support automatic updates. Source: [Using Arm-based images](https://docs.cloud.google.com/container-optimized-os/docs/how-to/arm)
- DOCUMENTED: GRUB fork with Secure Boot and TPM work. Source: [cos/cobble repository](https://cos.googlesource.com/cos/cobble/)
- DOCUMENTED: GKE node upgrades recreate nodes; GKE-to-COS version JSON mapping. Source: [GKE node images](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/node-images)
- INFERRED: losing power mid-update leaves the running system intact, because the update is written to the passive partition and the active root is not modified. Google does not state this.

**UNKNOWN, and expected**

- How the update payload is authenticated.
- Which server the updater contacts, and whether it can be mirrored or self-hosted.
- What happens to a half-written passive partition after an interrupted update.
- How the bootloader selects a partition, and whether boot attempts are tracked.
- Whether the updater can cross milestone boundaries or only moves within a family.

---

## 5. Rollback and recovery

**This is the largest documentation gap in the profile, and it is the one that matters most to
this epic's central question.**

COS has an active-passive root partition scheme. That is documented. What is not documented,
anywhere this research could find, is how to use it. There is no published procedure to boot the
previous root partition. There is no statement about boot attempt tracking or automatic fallback
after a failed boot. There is no COS recovery or rescue environment. There is no factory reset.
There is no statement of how many previous versions are retained. The sibling Pulse profile
reached the same conclusion on 2026-09-15 after searching the concept pages, the full
documentation index, the how-to pages, Google's own COS source host, and site-scoped searches for
recovery, rescue, factory reset, bootloader, partition priority and boot-success terminology. A
fresh search on 2026-09-16 returned the same result: no COS-specific rollback or recovery
documentation.

Every field here is UNKNOWN, not absent, and that distinction is the whole point. The mechanism
almost certainly exists, because the partition scheme is documented and GRUB is present. What is
missing is any published contract an operator could rely on.

**What does exist is replacement, not rollback, and Google is consistent about which one it
offers.** GKE node auto-repair drains and recreates a node the control plane detects as unhealthy:
"If GKE detects that a node requires repair, the node is drained and re-created." For plain VMs,
managed instance groups provide rolling updates against a previous instance template. In both
cases the machine does not recover itself. The platform throws it away and makes a new one. That
is a real guarantee, and it is a different guarantee from rollback. A rollback returns a machine to
a known-good version. A replacement returns a *fleet* to a known-good version and discards the
machine. For a cloud fleet those are close to equivalent. For a machine with irreplaceable local
state they are not equivalent at all, and COS is designed for the first case.

**Generic platform recovery paths exist but are not COS features.** Compute Engine offers an
interactive serial console for troubleshooting an instance that cannot be reached over the network
or is not fully booted, and "by default, interactive serial port access is disabled." Enabling it
is a decision an operator must make before the failure, not during it.

**What is COS's definition of a known-good state?** The documentation never gives one. Read from
the surrounding design, the answer is INFERRED: a known-good state is a specific qualified image
name, applied to a fresh instance, with configuration reapplied from metadata. Google's own
guidance supports this reading, since it tells operators to pin an exact image they have qualified
rather than track a family. The known-good unit is the image plus the metadata, not the machine.

**Evidence**

- DOCUMENTED: active-passive partition scheme exists. Source: [Automatic updates](https://docs.cloud.google.com/container-optimized-os/docs/concepts/auto-update)
- DOCUMENTED: node auto-repair drains and recreates. Source: [Node auto-repair](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/node-auto-repair)
- DOCUMENTED: interactive serial console, disabled by default. Source: [Troubleshooting using the serial console](https://docs.cloud.google.com/compute/docs/troubleshooting/troubleshooting-using-serial-console)
- DOCUMENTED: pin a qualified exact image for production. Source: [Versioning scheme](https://docs.cloud.google.com/container-optimized-os/docs/concepts/versioning)
- UNKNOWN: rollback to previous OS, automatic rollback on boot failure, retained version count, recovery environment, factory reset, network-independent recovery.

**Why the UNKNOWN is expected rather than a research gap.** COS is a cloud-only product whose
fleet model is node replacement. An operator who cannot reach a machine deletes it and creates
another from the same image. Google has little product reason to document a single-machine rollback
procedure, because the supported answer to a broken machine is a new machine. That explains the
silence. It does not remove the gap for anyone trying to compare COS against systems that treat
in-place recovery as a first-class guarantee.

---

## 6. Configuration model

COS uses cloud-init, supplied through Compute Engine instance metadata. An operator passes
`--metadata-from-file user-data=<file>` at instance creation, in `cloud-config` YAML format.
Startup scripts are available through the `startup-script` metadata key. OS Config guest policies
add a third channel, limited to `assignment` and `recipes`.

The separation of configuration layers is clean and maps onto the framework's split:

- **Image configuration**: cos-customizer build steps, or a full source build.
- **Machine configuration**: instance metadata, read by cloud-init on every boot.
- **Runtime configuration**: whatever containers do, plus anything written to `/etc` that will not
  survive the next reboot.
- **Cluster configuration**: the GKE API, if GKE is in use.

**The model is declarative in form and continuously reasserted in practice, and this is COS's most
distinctive configuration property.** Because `/etc` is stateless, cloud-init is not a first-boot
provisioner here. It is a boot-time reconciler. Google says so directly: "It's a good idea to
capture the desired state of your instances in cloud-init, as cloud-init is applied when an
instance is newly created as well as when an instance is restarted." The practical consequence
falls on the operator: every cloud-init module must be idempotent, because it will run again on
every boot, and Google warns that modules which "are typically run once-per-instance on other
distros, are run on every boot on Container-Optimized OS."

**The source of truth is the Compute Engine metadata store.** That has real properties. It is
readable and writable through the Compute Engine API, so remote inspection of a machine's declared
configuration does not require reaching the machine. It can be set on an instance template, so a
managed instance group has one declared configuration for many machines. Instance-level metadata
overrides project-level metadata, which gives a two-level override model.

It also has real limits. Metadata is a key-value store, not a versioned document. Version control,
signing and review of machine configuration are not COS or Compute Engine features. An operator
who wants them supplies them from outside, in whatever system generates the instance template.
Nothing in the documentation describes signing or verifying cloud-init content.

**Configuration changes without a reboot** are possible in the sense that a process can write to
`/etc` and restart a service. They do not persist. The supported way to change machine
configuration is to change the metadata and reboot, or to replace the instance. Both are
documented paths. Neither is a live-apply mechanism.

**Evidence**

- DOCUMENTED: cloud-init via `user-data` metadata, `cloud-config` format, startup scripts, per-boot module execution, the `systemctl enable` caveat. Source: [Creating and configuring instances](https://docs.cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance)
- DOCUMENTED: capture desired state in cloud-init because it reapplies on restart. Source: [Disks and filesystem overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/disks-and-filesystem)
- DOCUMENTED: OS Config supports `assignment` and `recipes`, not `packages` or `packageRepositories`; recipes run on every boot. Source: [OS Config guest policies](https://docs.cloud.google.com/container-optimized-os/docs/how-to/osconfig)
- DOCUMENTED: instance metadata overrides project metadata. Source: [Automatic updates](https://docs.cloud.google.com/container-optimized-os/docs/concepts/auto-update) and [Using Cloud Logging](https://docs.cloud.google.com/container-optimized-os/docs/how-to/logging)

**UNKNOWN, and expected**

- Whether any signing or integrity check is applied to cloud-init content. Not documented.
- How secrets should be delivered to a COS instance in a supported way. Google Cloud has Secret
  Manager and service-account scopes, but those are platform features, and the COS documentation
  does not cover secret provisioning.
- Whether there is an Ignition-style or machine-config-API alternative. There is not one in the
  documentation, and for a cloud-only OS there is no obvious reason there would be.

---

## 7. Kubernetes coupling

COS sits toward the middle of the spectrum, and it moved there from an unusual direction. It is
not a Kubernetes appliance. It is a general container host that Google also happens to use as its
managed Kubernetes node image.

**Kubernetes is optional.** Google documents running containers on a plain Compute Engine COS VM
with `docker run`, with no Kubernetes anywhere. Logging, monitoring, the host firewall, AppArmor,
sosreport, toolbox and the auto-updater all work on a standalone VM. The COS logging page says so
explicitly: "These instructions are for when you are using Container-Optimized OS outside of GKE,
such as in Compute Engine."

**A refinement of the baseline.** The Pulse entry recorded `ships_kubernetes: false`. The COS
release notes state that the "Kubernetes version provided in the changelog corresponds to the
Kubelet and the Kubectl version that are shipped in that Container-Optimized OS image," with the
caveat that "these component version may not be used when running a GKE cluster using a
Container-Optimized OS image." So kubelet and kubectl binaries are present in the image. COS still
does not configure, bootstrap or run a Kubernetes cluster by itself, and GKE supplies its own
component versions at node creation. The refinement is that the binaries ship, not that the
operating system is a Kubernetes distribution. This is new primary evidence, and the substance of
the baseline's claim stands.

**On GKE the coupling is real but sits in the control plane, not in the OS.** GKE Autopilot
clusters always use COS with containerd. Google describes COS images as "backed by a team at
Google" and providing "better support, security, and stability than other images." Node
auto-upgrade, release channels, maintenance windows and node auto-repair are all GKE features
acting on nodes. The OS does not manage Kubernetes and Kubernetes does not use the OS's own
updater. Node upgrades replace nodes.

**Lifecycle independence is now partially answerable.** The Pulse entry recorded it as UNKNOWN
because no published mapping between GKE node versions and COS milestones was found. Google does
publish that mapping, as a JSON file of GKE patch versions to COS node image versions, refreshed
roughly weekly, so an operator can choose a GKE patch version to obtain a specific COS image
version. That is version *selection through* GKE, not version *independence from* GKE. The OS
milestone still travels with the node version. So: coupled, with a published lookup table.

**Self-managed Kubernetes on COS is undocumented.** Nothing in the COS documentation describes
bootstrapping kubeadm or any other distribution on it. The binaries being present does not make it
a documented path.

**Non-Kubernetes workloads.** COS is documented as a container host for Compute Engine, and it is
used as a substrate by other Google services. Google Cloud Batch uses it as its default VM image
for container-only jobs: "If the job only has container runnables, the job uses the latest version
of the Batch Container-Optimized OS (COS) image." Confidential Space is a COS-derived image. The
"when not to use it" list rules out non-containerized applications directly. So it is a container
host, an AI and GPU host, and a platform substrate. It is not a general Linux appliance base, and
Google does not present it as one.

**Evidence**

- DOCUMENTED: running containers on a plain VM. Source: [Running containers on instances](https://docs.cloud.google.com/container-optimized-os/docs/how-to/run-container-instance)
- DOCUMENTED: COS features work outside GKE. Source: [Using Cloud Logging](https://docs.cloud.google.com/container-optimized-os/docs/how-to/logging)
- DOCUMENTED: kubelet and kubectl ship in the image, with the GKE caveat. Source: [COS release notes](https://docs.cloud.google.com/container-optimized-os/docs/release-notes)
- DOCUMENTED: Autopilot always uses COS with containerd; the GKE-to-COS version JSON mapping. Source: [GKE node images](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/node-images)
- DOCUMENTED: Batch uses a COS image by default for container-only jobs. Source: [Batch VM OS environment overview](https://docs.cloud.google.com/batch/docs/vm-os-environment-overview)
- DOCUMENTED: Confidential Space builds on COS. Source: [Confidential Space security overview](https://docs.cloud.google.com/docs/security/confidential-space)

**UNKNOWN, and expected**

- Whether a self-managed Kubernetes distribution on COS is workable. Undocumented, not denied.
- Whether the COS milestone can be pinned independently of the GKE node version, beyond selecting a
  GKE patch version from the published mapping.

---

## 8. Hardware and platform support

**Architectures.** Two boards exist in the build system: `lakitu` for x86_64 and `lakitu-arm64`
for Arm. riscv64 appears nowhere, in the boards, the image families or the documentation. That is
a clean documented absence rather than an unknown.

**Platforms.** Compute Engine and GKE. Google states that COS "is not supported outside of the
Google Cloud Platform environment," and lists "you need full support of the OS outside of Google
Cloud Platform" among the reasons not to use it. There is no bare metal path, no on-premises path,
no other-cloud path and no edge path. Worth recording because it would be a natural assumption
otherwise: Google's own on-premises Kubernetes distribution does not use COS, and lists other
distributions as its node operating systems.

**Arm is a materially different product, not the same product on another architecture.** Google
publishes the limitations: automatic updates are not supported, GPU accelerators are not supported,
Container Threat Detection does not work, `gcloud compute instances create-with-container` is not
supported, and the logging agent is fluent-bit rather than fluentd, which "may cause breakage when
migrating workloads" that carry custom fluentd configurations. Arm images use NVMe storage and
gVNIC networking where x86 uses SCSI and virtio-net, and they carry a separate kernel
configuration. Of the four commonly used COS container images, only `gcr.io/cos-cloud/toolbox` is
listed as Arm-compatible. Arm machine types are Tau T2A.

**Accelerators and specialized hardware are a real strength on x86.** NVIDIA GPU support covers
B200, H200 141GB, H100 80GB, A100 40GB and 80GB, and L4 on accelerator-optimized machines, plus
T4, V100, P100 and P4 on N1 machines. TPU node pools appear in the secure kernel module
documentation, so COS is the OS under GKE TPU nodes. Recent milestones add high-end networking:
ConnectX-8 RDMA support, A4X-Max NICs, deterministic CX-8 NIC naming, IPv6 for IDPF-driver
machines, and a Lustre client driver landed in an M129 build in August 2026. A vTPM is available
through Shielded VM, and Confidential VM support spans multiple processor technologies.

**The framework's key question: if unsupported hardware appears tomorrow, can an organization add
support itself?** For COS the honest answer is mostly no, and the reason is instructive. Under
`ENFORCE_SIGNED_MODULES`, only Google-signed out-of-tree modules load. On CPU and TPU nodes without
the feature, LoadPin restricts out-of-tree module loading entirely. An operator can rebuild the
whole distribution from source with its own kernel configuration, which is a genuine capability,
but the result is a custom image outside the supported product, on a platform where the vendor
controls the hardware anyway. In practice new hardware support arrives when Google adds it, and
the Lustre driver landing in a routine M129 build is what that looks like. This is not a defect.
It is the direct consequence of being a first-party OS on a first-party platform, where the set of
hardware that can appear is also chosen by the vendor.

**Evidence**

- DOCUMENTED: board names for the two architectures. Source: [Building from open source](https://docs.cloud.google.com/container-optimized-os/docs/how-to/building-from-open-source)
- DOCUMENTED: not supported outside Google Cloud; the "when not to use" list. Source: [COS overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/features-and-benefits)
- DOCUMENTED: the full Arm limitation list, machine types, storage and NIC differences. Source: [Using Arm-based images](https://docs.cloud.google.com/container-optimized-os/docs/how-to/arm)
- DOCUMENTED: supported GPU models and milestone floor. Source: [Running instances with GPU accelerators](https://docs.cloud.google.com/container-optimized-os/docs/how-to/run-gpus)
- DOCUMENTED: RDMA, IPv6, NIC and Lustre additions with dates. Source: [M125 release notes](https://docs.cloud.google.com/container-optimized-os/docs/release-notes/m125) and [M129 release notes](https://docs.cloud.google.com/container-optimized-os/docs/release-notes/m129)
- DOCUMENTED: Google Distributed Cloud node OS requirements do not include COS. Source: [GDC bare metal OS requirements](https://docs.cloud.google.com/kubernetes-engine/distributed-cloud/bare-metal/docs/installing/os-reqs)

---

## 9. Security and chain of trust

Tracing the chain firmware to workload, and separating what COS provides from what the platform
provides:

**Firmware to bootloader.** Compute Engine's Shielded VM feature provides UEFI Secure Boot,
measured boot and a vTPM. Secure Boot is opt-in: "Compute Engine does not enable Secure Boot by
default." Google maintains a GRUB fork, `grub-lakitu`, with commits covering core TPM support,
command verification during boot, and making the GRUB config read-only when Secure Boot is
enabled. Custom Secure Boot keys are not documented as a COS feature.

**Bootloader to kernel to root.** The root filesystem checksum is computed at build time and
verified by the kernel at each boot. The kernel enables "Integrity Measurement Architecture (IMA),
Audit, Kernel Page Table Isolation (KPTI), and some Linux Security Modules (LSMs)." M125 added the
ability to override the IMA policy from the OEM partition, and to autoload an IMA policy at boot on
confidential-compute boards. LoadPin restricts out-of-tree module loading on CPU and TPU nodes.

**Root to workload.** The userspace is minimal by design: "Container-Optimized OS is optimized to
run containers and containers package their own dependencies, we can trim unnecessary packages and
thus minimize the OS attack surface." There are no accessible user accounts by default. The SSH
daemon "is configured to disallow password-based authentication and to disallow root logins." The
host firewall drops "all incoming TCP/UDP connections except SSH on port 22." AppArmor and seccomp
are supported, with a default AppArmor profile applied automatically when a container starts. COS
ships AppArmor, not SELinux, and the two are not interchangeable.

**Tamper prevention, tamper detection and attestation are three different things here, and COS
lands differently on each.**

- *Prevention*: read-only root, no package manager, no accessible accounts, deny-inbound firewall,
  LoadPin, stateless `/etc`. Strong, and on by default.
- *Detection*: boot-time root checksum verification, IMA, Shielded VM integrity monitoring, the
  built-in CIS compliance scanner. Present, mostly on by default.
- *Attestation*: for stock COS, Shielded VM integrity monitoring is the extent of it. Full remote
  attestation is a Confidential Space capability, where measurements of "early boot components, the
  loaded kernel, and the container image" go into vTPM registers and Google Cloud Attestation
  verifies the quote and issues an OIDC token. That is a derived product, not stock COS.

**Compliance is unusually concrete for this category.** "Starting with Milestone 97,
Container-Optimized OS images comply with CIS Level 1 by default." A scanner ships in the image,
with `cis-level1.service` enabled and `cis-level2.service` disabled, plus a
`cis-compliance-scanner.timer` that defaults to a daily run. Results land in
`/var/lib/google/cis_scanner_scan_result.textproto` with per-check failure reasons. Google also
maintains a public `cos/compliance` source repository of CIS Distribution Independent Linux
Benchmark scripts, marked experimental.

**Vulnerability handling is documented as a cadence, not as an SLA.** COS images are "actively
patched for any critical bugs." High-priority fixes are "released on-demand." Medium and low
priority fixes ship "every 3 months." Individual CVEs are named in the release notes, and the
machine-readable OVAL feed lets an operator scan an instance's package inventory with OpenSCAP or
another SCAP tool. On the GKE side, Google states it follows FedRAMP remediation timeframes by
severity, and records a dated policy change: from 7 May 2026, most Linux kernel container-breakout
vulnerabilities are classified as Medium rather than High, on the reasoning that "an application
vulnerability must typically be exploited before an attacker can gain execution access."

**Three absences are documented rather than unknown, after targeted searching**: no SBOM in a
standard format, no build provenance or in-toto style attestation for the OS image, and no FIPS
validation. The package inventory in `about_os_credits.html` and `cos-package-info.json` is real
and useful, and it is not the same thing.

**Evidence**

- DOCUMENTED: read-only root and checksum, minimal footprint, firewall default, no accessible accounts, sshd policy, IMA and Audit and KPTI and LSMs, seccomp and AppArmor. Source: [COS security overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/security)
- DOCUMENTED: default AppArmor profile for containers. Source: [Securing containers with AppArmor](https://docs.cloud.google.com/container-optimized-os/docs/how-to/secure-apparmor)
- DOCUMENTED: Secure Boot off by default, vTPM, measured boot. Source: [Shielded VM](https://docs.cloud.google.com/compute/shielded-vm/docs/shielded-vm)
- DOCUMENTED: firewall default rules and non-persistence. Source: [Configuring the host firewall](https://docs.cloud.google.com/container-optimized-os/docs/how-to/firewall)
- DOCUMENTED: CIS Level 1 by default from M97, scanner services, timer, result file. Source: [Configuring and checking CIS compliance](https://docs.cloud.google.com/container-optimized-os/docs/how-to/cis-compliance)
- DOCUMENTED: OVAL feed and SCAP workflow. Source: [Scanning with the OVAL vulnerability feed](https://docs.cloud.google.com/container-optimized-os/docs/how-to/scanning-with-oval-vulnerability-feed)
- DOCUMENTED: patching cadence by severity. Source: [Support policy](https://docs.cloud.google.com/container-optimized-os/docs/resources/support-policy)
- DOCUMENTED: FedRAMP-aligned timeframes and the May 2026 severity reclassification. Source: [GKE security patching](https://docs.cloud.google.com/kubernetes-engine/docs/resources/security-patching)
- DOCUMENTED: attestation architecture of the COS-derived Confidential Space image. Source: [Confidential Space security overview](https://docs.cloud.google.com/docs/security/confidential-space)
- DOCUMENTED: grub-lakitu secure boot and TPM work. Source: [cos/cobble repository](https://cos.googlesource.com/cos/cobble/)
- INFERRED: the kernel and bootloader are signed with Google-controlled keys, because Shielded VM Secure Boot is supported on stock COS images. No COS page states the signing arrangement.

**UNKNOWN, and expected**

- Whether dm-verity protects the stock root filesystem.
- Whether the published image is signed, and how an operator would verify it.
- Whether custom Secure Boot keys can be used with a customized COS image.
- Whether a UKI is used. Nothing suggests one, and nothing denies one.
- Whether LUKS or any OS-level disk encryption is supported. Platform encryption at rest with
  Google-managed keys is a Compute Engine property and is kept separate here.
- Key rotation and revocation policy for whatever signs updates.

---

## 10. Provisioning and zero-touch deployment

There is one provisioning path, and it starts inside Google Cloud. An operator creates a Compute
Engine instance from an image in the public `cos-cloud` project, and supplies cloud-init or a
startup script through instance metadata at creation time. There is no ISO, no USB image, no PXE
or iPXE path, no network installer, and no bare-metal install. These are recorded as documented
absences rather than unknowns, because the product is documented as cloud-only.

A self-built image adds a second path, which is worth separating from the first: the build guide
documents importing a locally built image into Compute Engine as a custom image. That still lands
in Compute Engine.

**First-boot configuration is unusually strong and unusually literal.** Because `/etc` is
stateless, first boot and every subsequent boot run the same configuration. There is no divergence
between the provisioning path and the steady-state path, which removes a whole class of "it only
works on a fresh machine" problems.

**Device identity and bootstrap trust are platform properties.** A Compute Engine instance has a
service account and an instance identity token, and GKE nodes join the cluster through the control
plane. None of that is a COS mechanism, and the COS documentation does not describe device
identity at all.

**The framework's factory scenario does not translate.** "Can 5,000 identical devices leave a
factory and independently establish secure identity and desired state on first boot?" For COS the
question is not answerable as asked, because there are no devices and there is no factory. The
nearest equivalent is 5,000 instances created from one instance template in a managed instance
group, which Compute Engine does routinely, with identity supplied by the platform. That is a
genuine capability and it is a different problem. Recording it as "equivalent" would be a category
error, so this profile records it as not applicable and says why.

**Air-gapped provisioning has no documented path.** For a product that only runs in one cloud,
this is coherent rather than an oversight.

**Evidence**

- DOCUMENTED: instance creation, metadata-supplied cloud-init, startup scripts. Source: [Creating and configuring instances](https://docs.cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance)
- DOCUMENTED: importing a self-built image into Compute Engine. Source: [Building from open source](https://docs.cloud.google.com/container-optimized-os/docs/how-to/building-from-open-source)
- DOCUMENTED: konlet, the container startup agent that deployed containers during VM creation, is deprecated; the current guidance is a startup script or cloud-init. Source: [Deploying containers on instances and MIGs](https://docs.cloud.google.com/compute/docs/containers/deploying-containers)
- Absence, DOCUMENTED by the cloud-only statement: no ISO, PXE or bare-metal install path.

---

## 11. Fleet lifecycle

The framework asks for a clear split between what the OS provides, what an open-source companion
provides, and what a commercial product provides. For COS that split is stark, and almost
everything lands in the third bucket.

**The operating system itself contributes four things.** An A/B auto-updater, controlled per
instance or per project by the `cos-update-strategy` metadata key, and off by default from
milestone 117. Boot-time configuration reassertion through cloud-init, which is a fleet property
even though it does not look like one, because it means a reboot returns any machine to its
declared configuration. A Node Problem Detector agent that "monitors the instance health and
reports health-related metrics to Cloud Monitoring," present since M77, disabled by default on
plain VMs, enabled by default on GKE nodes, and enabled through the `google-monitoring-enabled`
metadata key. A logging agent gated on `google-logging-enabled`, fluent-bit from M109 on x86 and
on all Arm images. And the CIS compliance scanner from M97.

**Open-source companions, all Google-authored.** cos-customizer and cos-gpu-installer in
`cos/tools`, cos-extensions in its own repository, all Apache-2.0. The former public GitHub mirror
of cos-customizer is archived, and the tool carries a "not an official Google product" disclaimer.

**Commercial and managed, which is where every real fleet capability lives.** GKE node
auto-upgrade, release channels, maintenance windows and surge upgrade strategies. GKE node
auto-repair, which drains and recreates an unhealthy node while preserving the node name. Managed
instance groups, which provide the rolling-update path for plain VMs. Cloud Monitoring, Cloud
Logging and Cloud Audit Logs for telemetry and audit trail. None of these are self-hostable and
none of them are part of the operating system.

**What does not exist at all is an OS-native fleet layer.** There is no COS inventory service, no
rollout campaign mechanism, no canary or staged-rollout primitive in the OS, no health gate that
the machine itself evaluates before committing an update, and no desired-state controller. The
auto-updater is per-machine and uncoordinated: it stages an update and waits, and it does not
reboot. Coordinating reboots across a fleet is left entirely to the operator or to GKE. Third-party
projects exist to fill that gap outside Google's product surface, for example
[pantheon-systems/cos-update-operator](https://github.com/pantheon-systems/cos-update-operator),
a Kubernetes operator for managing COS updates. Its existence is recorded as evidence that the
coordination gap is real. It was not evaluated for this profile and it is not a Google product.

**Disconnected fleets** are outside the product. There is no documented model for a COS fleet that
cannot reach Google.

**Evidence**

- DOCUMENTED: auto-updater metadata control and the M117 default. Source: [Automatic updates](https://docs.cloud.google.com/container-optimized-os/docs/concepts/auto-update)
- DOCUMENTED: Node Problem Detector, M77, default state, enablement methods, and that it monitors the VM and not the containers. Source: [Monitoring system health with Node Problem Detector](https://docs.cloud.google.com/container-optimized-os/docs/how-to/monitoring)
- DOCUMENTED: logging agent selection by milestone and architecture, `google-logging-enabled`. Source: [Using Cloud Logging](https://docs.cloud.google.com/container-optimized-os/docs/how-to/logging)
- DOCUMENTED: node auto-repair. Source: [Node auto-repair](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/node-auto-repair)
- DOCUMENTED: node auto-upgrade. Source: [Node auto-upgrades](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/node-auto-upgrades)
- DOCUMENTED: node pool upgrade strategies cordon, drain and replace nodes. Source: [Node pool upgrade strategies](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/node-pool-upgrade-strategies)

---

## 12. Debugging and day-2 operations

COS is conventional here in a way that several peers are not, and it adds two things many of them
lack.

**Access.** SSH is available, with key-based authentication only, no password authentication and
no root login. A local shell exists. The Compute Engine interactive serial console is available
for a machine that is unreachable over the network or not fully booted, and it is disabled by
default.

**The no-package-manager problem has a first-party answer.** Toolbox runs a Debian environment
with the host root visible at `/media/root`, persists under `/var/lib/toolbox` across reboots, and
after the first run "does not require a working Docker daemon, nor does it incur any network or
disk overhead." The first run does pull `gcr.io/cos-cloud/toolbox`. Google is careful to say it is
"a debugging utility and not intended for production use."

**Support bundles ship in the image.** "Container-Optimized OS includes the `sosreport` utility,
which collects information on demand to help you debug problems" on a COS VM. The invocation is
version-dependent: `sudo sosreport --all-logs --batch --tmp-dir=/var` on M85 and earlier, and
`sudo sos report --all-logs --batch --tmp-dir=/var` on M105 and later. The output is a `.tar.xz`
written locally, and Google warns it "may contain personally identifiable information (PII),
because it collects data from many critical system components (e.g. journald)." If a support case
is opened, "you may be asked to provide the `sosreport` data as part of the investigation." Several
projects in this comparison have nothing equivalent.

**Other tooling.** `perf` is installed by default, and kernel crash dump collection is documented.
Node Problem Detector reports host health with no Kubernetes required, which means the host
telemetry path survives a Kubernetes outage.

**Two operational consequences of this model are worth stating plainly, because they are the
tradeoff.**

First, everything listed above is host-level and works when Kubernetes is unavailable. That is a
real advantage over designs that put all debugging behind a cluster API.

Second, the escape hatches need the network and a Google registry. Toolbox needs a registry pull
the first time it runs on a machine. cos-extensions needs the `devstorage.read_only` scope to
reach `gcr.io`. An operator debugging a machine with broken networking, on which toolbox has never
been run, has the shipped tools and nothing more. The serial console is the documented answer for
that case, and it must be enabled before the failure, not during it. A COS fleet that has not
enabled the serial console in advance has a thinner recovery story than its component list
suggests.

**Evidence**

- DOCUMENTED: sshd policy and no default accounts. Source: [COS security overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/security)
- DOCUMENTED: toolbox behaviour, persistence, host access, production disclaimer. Source: [Debugging node issues using toolbox](https://docs.cloud.google.com/container-optimized-os/docs/how-to/toolbox)
- DOCUMENTED: sosreport inclusion, invocation by milestone, PII warning, support-case use. Source: [Collect debugging information using sosreport](https://docs.cloud.google.com/container-optimized-os/docs/how-to/sosreport)
- DOCUMENTED: `perf` installed by default and crash dump collection. Source: [Using debugging tools](https://docs.cloud.google.com/container-optimized-os/docs/how-to/using-debugging-tools)
- DOCUMENTED: serial console disabled by default. Source: [Troubleshooting using the serial console](https://docs.cloud.google.com/compute/docs/troubleshooting/troubleshooting-using-serial-console)
- DOCUMENTED: `cos-extensions` requires a Google API scope to fetch payloads. Source: [Running instances with GPU accelerators](https://docs.cloud.google.com/container-optimized-os/docs/how-to/run-gpus)

**UNKNOWN, and expected**

- Whether `ctr`, `crictl`, `strace` or `tcpdump` are present in the image. The debugging page names
  only `perf`. Absence from one page is not absence from the image.
- Whether journald persists logs across reboot. `/var` is stateful, which makes it possible, and no
  page states the configuration.

---

## 13. Persistent state and storage

COS draws the boundary between replaceable infrastructure and stateful machine at the partition
table, and it draws it clearly.

**Persistence across reboot** follows the three partition classes exactly. `/home`, `/var`,
`/var/lib/google`, `/var/lib/docker` and `/var/lib/toolbox` survive. `/etc`, `/tmp`,
`/var/lib/cloud` and `/mnt/disks` do not. The practical result is that container images and
container runtime state survive a reboot, while every piece of system configuration does not.

**Persistence across upgrade is not stated as a guarantee anywhere.** The separate stateful
partition implies it. Google never says it. This profile records it as UNKNOWN, following the
baseline, because a guarantee that is only implied is not a guarantee an operator can plan a data
migration around.

**Persistence across reset** has no meaning here, because no factory reset exists.

**Additional disks.** Persistent disks are formatted and mounted through cloud-init's `bootcmd`
section, not `/etc/fstab`, because "`/etc/` is stateless on Container-Optimized OS, you cannot use
`/etc/fstab` to automatically fsck and mount the disks on boot." Mount points live under
`/mnt/disks`. The mount is reasserted on every boot along with the rest of the configuration.

**Filesystems.** ext4 is the recommendation for production, with POSIX ACL and security attributes
enabled in the kernel and `e2fsprogs` present. XFS is available from M105 and is "primarily
targeted for users who have some existing dependency on XFS that cannot be migrated," with
`xfsprogs` present. Google's guidance is unambiguous: "The recommended filesystem for production
workloads on Container-Optimized OS is still EXT4." Btrfs, ZFS, NFS, overlayfs and CIFS are not
mentioned on the supported-filesystems page. Following the framework's rule, that is recorded as
not documented, not as unsupported.

**Network storage.** A Lustre client driver was added in an M129 build in August 2026. Beyond
that, network storage on GKE is the CSI driver story, which is a Kubernetes-layer concern rather
than an OS one.

**Where the boundary sits.** COS treats the machine as replaceable and the boot disk's stateful
partition as a cache, not as a system of record. Google's own fleet mechanisms reinforce this:
GKE upgrades recreate nodes, node auto-repair recreates nodes, and managed instance groups
recreate instances. An operator who puts irreplaceable data on a COS boot disk is working against
the grain of every lifecycle mechanism the platform provides. Data belongs on an attached
persistent disk, in a managed service, or in an object store.

**Evidence**

- DOCUMENTED: partition classes, per-path persistence, `bootcmd` mounting, `/etc/fstab` unusable. Source: [Disks and filesystem overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/disks-and-filesystem)
- DOCUMENTED: ext4 recommended, XFS from M105 and its intended use. Source: [Supported filesystems](https://docs.cloud.google.com/container-optimized-os/docs/concepts/supported-filesystems)
- DOCUMENTED: Lustre client driver addition. Source: [M129 release notes](https://docs.cloud.google.com/container-optimized-os/docs/release-notes/m129)

**UNKNOWN, and expected**

- Whether the stateful partition survives an A/B upgrade as a stated guarantee.
- Whether LVM, software RAID, dm-crypt or LUKS are usable. Not documented either way.
- What happens when the stateful partition is corrupted, and whether any repair path exists.

---

## 14. Networking

Networking on COS is mostly the Compute Engine network, and the COS documentation reflects that by
saying very little about it. The product has no networking concept page. What exists is a stream of
release-note entries, and those turn out to be the most informative primary source available.

**Baseline.** DHCP from the platform. Instances get their address and their NTP server from the
DHCP response on `eth0`, "which is usually the Compute Engine's metadata server." Networking is up
before anything else, which means the metadata-driven configuration model always has a network to
work with. There is no pre-network configuration problem of the kind bare-metal systems have.

**Recent, dated changes in M125 are worth recording exactly, because one of them reversed
itself.** On 2025-08-25 Google "enabled the google-guest-agent's network management functionality."
On 2025-09-08 Google "disabled network management by the google-guest-agent." On 2025-09-02 Google
"enabled dynamic vlan configuration for non-primary NICs." Also in that milestone: IPv6 support for
machines using the IDPF driver, ConnectX-8 RDMA support, support for A4X-Max NICs, and deterministic
CX-8 NIC naming. The enable-then-disable sequence on guest-agent network management is the kind of
fact that matters to anyone pinning a build, and it is only visible in the release notes.

**Multiple NICs and VLANs** are Compute Engine VPC features. Dynamic NICs use IEEE 802.1Q with VLAN
IDs from 2 to 255. COS's contribution is kernel and agent support for them.

**What is not documented for COS**: static IP configuration on the guest, bonding, bridges, Wi-Fi,
WireGuard, cellular, SR-IOV configuration by the operator, HTTP proxy configuration, and corporate
CA certificate installation. For a cloud-only VM OS most of these are not meaningful, since the
platform owns the network. Proxies and corporate CA certificates are the two that would matter to
an enterprise operator, and they are genuinely absent from the documentation.

**Edge, telco and industrial scenarios do not apply.** COS does not run outside Google Cloud, so
the framework's edge and telco emphasis has no target here. Saying so is more useful than scoring
a zero.

**Evidence**

- DOCUMENTED: NTP from the `eth0` DHCP response. Source: [Creating and configuring instances](https://docs.cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance)
- DOCUMENTED: guest-agent network management enabled then disabled, dynamic VLAN for non-primary NICs, IPv6 for IDPF, ConnectX-8 RDMA, A4X-Max NICs, CX-8 naming. Source: [M125 release notes](https://docs.cloud.google.com/container-optimized-os/docs/release-notes/m125)
- DOCUMENTED: Arm images use gVNIC rather than virtio-net. Source: [Using Arm-based images](https://docs.cloud.google.com/container-optimized-os/docs/how-to/arm)
- DOCUMENTED: Dynamic NIC and VLAN semantics are a VPC feature. Source: [Multiple network interfaces](https://docs.cloud.google.com/vpc/docs/multiple-interfaces-concepts)

**UNKNOWN, and expected**

- Supported guest-side configuration of proxies and corporate CA certificates.
- Whether bonding or bridging is usable on a COS guest.

---

## 15. Supply-chain ownership and reproducibility

The framework's question is: could an organization independently recreate and operate what it is
running? COS gives a genuinely split answer, and both halves are documented.

**What an organization can recreate.** The source is public at `cos.googlesource.com`. The build
tooling is public: `depot_tools`, `repo`, `cros_sdk`. The manifest is public, at
`cos/manifest`. The board overlays are public, at `cos/overlays/board-overlays/project-lakitu`,
laid out as a Portage overlay with the standard category structure. The kernel tree and the kernel
configurations for both architectures are public. A `cos/manifest-snapshots` repository exists,
with numbered tags created by an automated "COS Source Manager Bot" at a cadence of roughly one
every one to two days, which is the right shape for per-build source pinning. Archived kernel
sources and headers are published per build in `gs://cos-tools/<build-number>/`. The GRUB fork is
public, the compliance scripts are public, and the tooling is Apache-2.0.

That is a substantial amount of real supply-chain material, more than a "vendor-only image" summary
would predict.

**What an organization cannot verify.** Google's own statement about source availability is
hedged, and the hedge is Google's, not a paraphrase: "You can find the majority of the source code
for Container-Optimized OS in the COS repositories." No document names what the remainder is. No
reproducibility claim is made in either direction, so whether a third-party build of a given
manifest snapshot produces the official image bit for bit is UNKNOWN. There is no published SBOM
in a standard format, no build provenance or attestation, no public CI for the OS build, and no
documented signature on the published image.

**There is no single license statement for the operating system.** Components carry their own.
The tooling is Apache-2.0, the kernel is GPL-2.0, and the Chromium OS lineage brings BSD-3-Clause.
The COS-specific board overlay directory carries no license file. Per-package license and version
data ships inside every image in `about_os_credits.html`, which is the practical answer for a
compliance team.

**Self-hosted update infrastructure has no documented path.** The update service is never named.
Mirroring the image is not documented. This is the single hardest external dependency in the chain,
and it is examined stage by stage in dimension 22.

**Evidence**

- DOCUMENTED: source location, the "majority of the source code" hedge, kernel sources and headers per build, `about_os_credits.html`. Source: [COS sources](https://docs.cloud.google.com/container-optimized-os/docs/resources/sources)
- DOCUMENTED: public build tooling and procedure. Source: [Building from open source](https://docs.cloud.google.com/container-optimized-os/docs/how-to/building-from-open-source)
- DOCUMENTED: the repository set, including `cos/manifest`, `cos/manifest-snapshots`, `cos/overlays/board-overlays`, `cos/cobble`, `cos/compliance`, `cos/policymanager`, `cos/tools`, `cos/cos-extensions`. Source: [cos.googlesource.com](https://cos.googlesource.com/)
- DOCUMENTED: Portage overlay layout of `project-lakitu`. Source: [project-lakitu](https://cos.googlesource.com/cos/overlays/board-overlays/+/refs/heads/master/project-lakitu/)
- DOCUMENTED: tooling license. Source: [cos/tools LICENSE](https://cos.googlesource.com/cos/tools/+/refs/heads/master/LICENSE)

**UNKNOWN, and expected**

- Which parts of a shipped image are not in the public repositories.
- Whether a manifest snapshot pins the complete source tree for a given build, and whether the
  build is reproducible. `cos/manifest-snapshots` has no README, so its contract is not published.
- Whether public CI runs the OS build.

---

## 16. Governance and ownership

The framework asks for facts, not scores, and insists that open source, open governance,
vendor-neutral ownership and diverse contribution are four separate properties. For COS all four
answers are short.

- **Open source**: partial, with an unnamed remainder. Google publishes "the majority" of the
  source and names no exclusions.
- **Open governance**: none. There is no governance document, no maintainer list, no published
  roadmap process, and no public issue tracker for the operating system.
- **Vendor-neutral ownership**: none. Google owns the trademark, the repositories, the review
  system, the signing keys, the image project, the update service and the support contract. There
  is no foundation involvement.
- **Diverse contribution**: not established. The Pulse baseline sampled author email domains across
  one page of the tooling repository's commit log and found every author on Google's own domain. It
  is a sample from one page of one repository, and it is the tooling repository rather than the OS
  build. No external contributor evidence was found, and none is claimed as proven absent.

**The defining governance fact is a published two-tier contribution split.** "Container-Optimized
OS does not accept direct contributions from the public." The companion tooling does accept them,
through a Gerrit review system and a contributor license agreement: "Contributions to this project
must be accompanied by a Contributor License Agreement (CLA)."

**The practical consequence for an operator is concrete.** A third party who finds a defect in the
operating system has no public tracker to file it in and no path to fix it themselves. The
supported route is a paid support case. The unsupported route is to fork the public source and
maintain a private build, which puts them outside the product and on a platform where they are the
only tester.

**Could another organization continue development if Google stopped?** They could clone the public
repositories and build the `lakitu` board. They could not use the name, the update service, the
registries the extensions pull from, or the only platform the OS is supported on. This is INFERRED
from the documented dependencies. It is a dependency map, not a prediction, and this profile makes
no statement about what Google will do.

**A scoping note.** Several framework governance sub-questions, about foundation hosting,
maintainer structure, relicensing ability and organizational diversity, assume a community project.
COS is a vendor product with a published source tree. Answering those questions as if the project
were competing on governance would be a category error. The right finding is that the governance
dimension is largely not applicable, and the reason it is not applicable is itself the finding.

**Evidence**

- DOCUMENTED: the no-public-contributions statement and the source hedge. Source: [COS sources](https://docs.cloud.google.com/container-optimized-os/docs/resources/sources)
- DOCUMENTED: the tooling CLA and contribution guide. Source: [cos/tools CONTRIBUTING.md](https://cos.googlesource.com/cos/tools/+/refs/heads/master/CONTRIBUTING.md)
- DOCUMENTED: tooling license. Source: [cos/tools LICENSE](https://cos.googlesource.com/cos/tools/+/refs/heads/master/LICENSE)
- DOCUMENTED: the review system and repository set. Source: [cos.googlesource.com](https://cos.googlesource.com/)

---

## 17. Project health and sustainability

**Age and continuity.** COS has been generally available since 5 April 2017, which is nine years.
It is the default node image for Google's managed Kubernetes and the image Autopilot clusters
always use, the default VM image for container-only Google Cloud Batch jobs, and the base for
Confidential Space. That is verifiable adoption inside Google's own product line, and it is a
stronger sustainability signal than any contributor count would be.

**Release cadence is high and consistent.** A new LTS milestone arrives roughly three times a year,
matching the versioning page's statement that `cos-stable` is "updated every 4 months." Builds
within a supported milestone land weekly or faster. On M129 the four most recent builds are dated
2026-09-08, 2026-08-31, 2026-08-24 and 2026-08-17.

**Security response is documented as a cadence with no numeric commitment.** Critical bugs are
actively patched, high-priority fixes ship on demand, and medium and low priority fixes ship every
three months. Individual CVEs are named in the release notes and, on the GKE side, in security
bulletins for High and Critical issues. No response-time SLA is published for COS itself.

**Contributor concentration and bus factor cannot be measured from public data.** There is no
public issue tracker, no public CI for the OS build, and no contribution statistics for the OS. The
only sample available is the tooling repository, which is all Google. Recording a bus factor here
would be invention. The relevant risk is not a bus factor in the usual sense: it is single-vendor
concentration, which is documented rather than estimated.

**Two data-quality problems with the published lifecycle dates are worth recording, because the
lifecycle table is the one thing a planning reader most needs to be correct.** First, the Pulse
baseline found two Google pages giving different end-of-support dates for the same milestones: the
release notes page and the Compute Engine operating system details page, differing by four and five
months for M125. That discrepancy was inherited from the baseline and could not be re-verified on
2026-09-16, because the Compute Engine OS details page could not be retrieved in full. Second, the
published intervals between LTS end-of-support dates are uneven: M117 to M121 is six months, M121 to
M125 is eleven months, and M125 to M129 is five months. A steady three-milestones-a-year cadence with
a fixed 26-month window would produce even spacing. This is recorded as an observation about the
published table, not as a conclusion about Google's plans.

**Evidence**

- DOCUMENTED: general availability date. Source: [COS GA announcement](https://cloud.google.com/blog/products/gcp/container-optimized-os-from-google-is-generally-available/)
- DOCUMENTED: build dates and cadence on the current milestone. Source: [M129 release notes](https://docs.cloud.google.com/container-optimized-os/docs/release-notes/m129)
- DOCUMENTED: milestone and end-of-support table. Source: [COS release notes](https://docs.cloud.google.com/container-optimized-os/docs/release-notes)
- DOCUMENTED: `cos-stable` updated every four months. Source: [Versioning scheme](https://docs.cloud.google.com/container-optimized-os/docs/concepts/versioning)
- DOCUMENTED: patching cadence. Source: [Support policy](https://docs.cloud.google.com/container-optimized-os/docs/resources/support-policy)
- DOCUMENTED: Autopilot always uses COS. Source: [GKE node images](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/node-images)
- DOCUMENTED: Batch default image. Source: [Batch VM OS environment overview](https://docs.cloud.google.com/batch/docs/vm-os-environment-overview)

---

## 18. Operational lifecycle and support horizon

**The support contract is specific.** "Once a milestone is introduced on the LTS families, it is
supported for 26 months." Only the LTS families are supported. `cos-stable`, `cos-beta` and
`cos-dev` receive no support.

**What happens at end of support is documented in operational detail, and the detail has teeth.**
The family is deprecated, the deprecated flag is set, and the images "stop appearing in the active
list." Critically: "Any Image Family API references to the deprecated image family will return
errors and break any workflows depending on it." Deprecated images remain usable by exact name,
but "any issues with those images might not be fixed." So indefinite version pinning is possible
and explicitly unsupported, and the failure mode for anyone using the family API is a hard break
rather than a silent drift.

**A second pinning hazard sits in the update path.** Images released before a signing key rotation
cannot update to versions released after it, and affected instances must be recreated. A
long-pinned fleet can therefore reach a state where the in-place updater cannot move it forward at
all, and the only path is instance replacement.

**Required upgrade frequency depends on which lifecycle the operator is inside.** For a standalone
COS fleet, the floor is one milestone move every 26 months. For a GKE fleet, the node image
follows the GKE node version, and Google recommends upgrading clusters at least monthly for
security patching, so the practical cadence is far higher and is driven by Kubernetes, not by the
OS.

**Kubernetes compatibility** is handled through the published JSON mapping of GKE patch versions to
COS node image versions, refreshed roughly weekly with a `creation_time` field.

**Downgrade support is undocumented.** So is whether the in-place updater can cross a milestone
boundary or only moves within a family. Both are UNKNOWN.

**Operational burden over several years, read from the documented facts.** The routine burden is
low: builds land weekly, the updater is per-machine, and on GKE the whole thing is a managed
control-plane concern. The burden concentrates at three points. The milestone move every two years.
The moment a deprecated family breaks an Image Family API reference. And the reboot, which no
automatic mechanism performs, so every staged update sits inert until the operator or GKE reboots
the machine. That last one is the quiet one: with automatic updates off by default from M117, a
standalone COS fleet does nothing at all unless the operator opts in and also solves reboot
coordination.

**Commercial support** runs through Google Cloud's standard support channels with no separate
license fee. Google names the absence of third-party Linux vendor support as a reason COS may not
fit: it tells operators not to use it if "you need professional support from a Linux vendor."

**Evidence**

- DOCUMENTED: 26-month window, LTS-only support, deprecation behaviour, Image Family API breakage. Source: [Support policy](https://docs.cloud.google.com/container-optimized-os/docs/resources/support-policy)
- DOCUMENTED: key rotation blocks updates for older images. Source: [Automatic updates](https://docs.cloud.google.com/container-optimized-os/docs/concepts/auto-update)
- DOCUMENTED: monthly cluster upgrade recommendation and patch delivery through upgrades. Source: [GKE security patching](https://docs.cloud.google.com/kubernetes-engine/docs/resources/security-patching)
- DOCUMENTED: GKE-to-COS version mapping. Source: [GKE node images](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/node-images)
- DOCUMENTED: the "when not to use" list including the Linux vendor support point. Source: [COS overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/features-and-benefits)

---

## 19. Resource footprint and performance

**This dimension is mostly NOT TESTED and UNKNOWN, and the tier is the reason.** The framework
asks for measurement where experimentally useful. This is the documentation-only tier, so no image
was downloaded, no instance was booted, and nothing was timed. Presenting numbers here would mean
either reproducing third-party benchmarks, which the evidence discipline for this ticket excludes,
or inventing them.

**What Google does document is design intent, not measurement.** COS "is optimized to run
containers and containers package their own dependencies, we can trim unnecessary packages and
thus minimize the OS attack surface." No image size, disk footprint, idle memory, idle CPU, boot
time, upgrade download size or reboot duration figure appears in the COS documentation.

**Three footprint-adjacent facts are documented and worth keeping.** The A/B scheme means the boot
disk carries two root partitions, and cos-customizer's `disable-auto-update` step "disables the
auto-update service and reclaims associated disk space," which confirms that the passive partition
occupies reclaimable space. The update transfers a whole OS image rather than packages, so the
update payload is image-scale; whether delta payloads are used is not documented and is not
inferred here. GPU drivers land in `/var/lib/nvidia` and the install command must run on every
reboot.

**Evidence**

- DOCUMENTED: minimal-footprint design intent. Source: [COS security overview](https://docs.cloud.google.com/container-optimized-os/docs/concepts/security)
- DOCUMENTED: whole-image update. Source: [Automatic updates](https://docs.cloud.google.com/container-optimized-os/docs/concepts/auto-update)
- DOCUMENTED: disabling auto-update reclaims disk space. Source: [cos-customizer README](https://cos.googlesource.com/cos/tools/+/refs/heads/master/src/cmd/cos_customizer/README.md)
- NOT TESTED: every measurement in this dimension.

---

## 20. Extensibility versus constraint

**Placement: firmly toward APPLIANCE, with a full source-build escape hatch that leads outside the
supported product.**

```
APPLIANCE <--[COS]--------------------------------------> CONSTRUCTION KIT
              ^                                ^
              stock image, the product     lakitu source build,
              and the supported surface    outside the product
```

**Decisions Google makes for the operator**, none of which are overridable inside the supported
product: the base distribution (a Chromium OS fork), the kernel and its configuration, the init
system, the package set, the container runtimes, the filesystem layout and its persistence classes,
the security posture and defaults, the module trust anchor, the update mechanism, and the platform
it runs on.

**Decisions the operator can override**: the image contents at build time through cos-customizer,
including arbitrary scripts, preloaded GPU drivers, a sealed OEM partition, GRUB configuration and
kernel command-line arguments. Whether the auto-updater runs. Which driver version is installed.
The firewall rules and AppArmor profiles, reasserted on every boot. The module signing policy, on
GKE only, and only between "Google-signed" and "anything." What containers run, which is the
intended extension point.

**Decisions the operator cannot override at all**: the running system's package set, the module
signing key under the enforced policy, and portability off Google Cloud.

**Can unsupported states be created?** Yes, and the boundary is unusually visible. cos-customizer
carries "This is not an official Google product." A full source build produces an image Google has
not tested. Using `DO_NOT_ENFORCE_SIGNED_MODULES` is a documented option that Google frames as the
less safe one, and it describes GPU nodes without the feature as "less secure by default." COS is
honest about where the supported surface ends, which is more than many products manage.

**Does customization weaken guarantees?** Yes, and specifically. The core guarantee is that the
root filesystem is exactly the image Google built and is verified at boot. A cos-customizer image
is still verified, because the customizer produces a new image with its own checksum, but the thing
being verified is now the operator's artifact. The operator has moved from "Google tested this" to
"I tested this," with no supported testing infrastructure and no ability to run the result anywhere
except Compute Engine.

**Does constraint reduce operational complexity?** Yes, measurably, and this is COS's real
argument. An operator gets a hardened, CIS Level 1 compliant, read-only, AppArmor-enforcing,
deny-inbound container host without configuring any of it. The configuration surface that would
normally need policy, review and drift detection does not exist, because `/etc` is destroyed on
every boot. For an organization whose requirement is "run containers safely on Google Cloud and
think about the OS as little as possible," the constraint is the product.

**Can existing enterprise standards be incorporated, or must the organization adopt Google's?**
Mostly the latter, and the specifics matter more than the generalization. Standards expressible as
containers, cloud-init, AppArmor profiles or firewall rules fit. Standards that need a kernel
module, a specific FIPS-validated crypto module, a corporate CA in the system trust store, or an
agent installed as a package do not have a documented path. An organization with an existing Linux
standard is, by Google's own "when not to use it" list, being told to look elsewhere.

**Evidence**: as cited in dimensions 1, 3, 4, 9 and 15. No new sources are introduced here; this
dimension is a synthesis of documented facts, and the synthesis itself is INFERRED.

---

## 21. Failure experiments

**OUT OF TIER SCOPE.** This ticket's tier is documentation-based, and destructive testing of a
hyperscaler platform OS would require provisioning and deliberately breaking billable Google Cloud
infrastructure, which the epic's stratification explicitly excludes for COS and Azure Linux.

Where Google's documentation makes a direct claim about one of the framework's ten scenarios, it is
recorded below as DOCUMENTED evidence rather than omitted. Where it does not, the scenario is
UNKNOWN, not "fails."

| # | Scenario | What the documentation says |
|---|---|---|
| 1 | Cut power during OS update | Partially DOCUMENTED. The update installs to the passive partition and "does not take effect until the instance is rebooted." The running root is not modified. What happens to a half-written passive partition is UNKNOWN. |
| 2 | Corrupted new OS image | UNKNOWN. Adjacent DOCUMENTED fact: the root checksum "is computed at build time and verified by the kernel on each boot." The behaviour on mismatch is not stated. |
| 3 | Kernel that cannot boot | UNKNOWN. GRUB is the bootloader and Google maintains the `grub-lakitu` fork, but no boot-attempt tracking or fallback behaviour is documented. |
| 4 | Break Kubernetes after OS upgrade | DOCUMENTED, at the fleet level. "If GKE detects that a node requires repair, the node is drained and re-created." This is replacement, not machine recovery. |
| 5 | Corrupt persistent configuration | Partially DOCUMENTED. System configuration in `/etc` is stateless, so a reboot rebuilds it from cloud-init. Corruption of the stateful partition is UNKNOWN. |
| 6 | Remove network during upgrade | UNKNOWN. |
| 7 | Make the image registry unavailable | DOCUMENTED for the extension path. Without the `devstorage.read_only` scope, "downloading of the driver and its dependencies will fail." Toolbox needs a registry pull on first use. |
| 8 | Fill the disk | UNKNOWN. Adjacent DOCUMENTED fact: Node Problem Detector reports capacity metrics to Cloud Monitoring. |
| 9 | Damage boot configuration | UNKNOWN. Adjacent DOCUMENTED fact: the `grub-lakitu` fork makes the GRUB config read-only when Secure Boot is enabled. |
| 10 | Remove the management plane | INFERRED. A standalone COS VM has no management plane to remove and keeps running. A GKE node loses auto-upgrade, auto-repair and release-channel behaviour, and the OS-level updater is off by default from M117. |

The central question the framework poses, "what does the machine do next," is the question COS
documentation answers least. That is the most important single finding in this profile.

---

## 22. Operational independence

**Documentation-only treatment.** The experiment was not performed. Each stage below records what
Google's own documentation says about dependence on Google-hosted infrastructure, with a label.

| Stage | Finding | Label |
|---|---|---|
| BUILD | A third party can build the OS from public source, on its own machine, with `depot_tools`, `repo`, `cros_sdk` and the two board names. The source is fetched from Google-hosted Git, but the build itself runs locally. Whether the result matches an official image is unstated. | DOCUMENTED (buildable), UNKNOWN (reproducible) |
| SIGN | No signing of the OS image is documented, and no operator-controlled signing path exists in the documentation. For out-of-tree kernel modules the trust anchor is explicitly Google's key: "only Google-signed OOT modules are allowed." | UNKNOWN (image), DOCUMENTED (module key is Google's) |
| HOST | The official image is published only as a Compute Engine image in the `cos-cloud` project, not as a downloadable file. A self-built image can be imported into Compute Engine as a custom image. Mirroring the official image is not documented. | DOCUMENTED (import path), UNKNOWN (mirroring) |
| INSTALL | One documented path: create a Compute Engine instance from the image. No ISO, PXE, network installer or bare-metal install. | DOCUMENTED |
| BOOT | This is the strongest counterweight to "cloud-only," and it is easy to miss. The build guide documents booting a self-built image locally under KVM or QEMU, and gives the exact command line and the SSH key path for the test image. So booting COS outside Google Cloud is documented, as a development workflow. Running it outside Google Cloud in production is documented as not supported. | DOCUMENTED (both halves) |
| CONFIGURE | The configuration model is cloud-init driven by the Compute Engine metadata server, and NTP comes from the same place via DHCP. Outside Compute Engine there is no metadata server. Whether cloud-init works from another datasource on COS is not documented. The build guide's local-QEMU workflow uses an SSH key on a test image instead of cloud-init. | DOCUMENTED (dependency), UNKNOWN (alternative datasource) |
| UPGRADE | The hardest dependency in the chain. The updater contacts a server Google never names, and no mirroring or self-hosting path is documented or denied. Two escapes are documented and both change the problem rather than solving it: automatic updates can be disabled entirely with `cos-update-strategy=update_disabled`, or removed at build time with cos-customizer's `disable-auto-update`, which moves the operator to instance replacement, which depends on Google-hosted images. | UNKNOWN (replaceable), DOCUMENTED (can be disabled) |
| ROLLBACK | Nothing documented. See dimension 5. | UNKNOWN |
| RECOVER | No COS-specific recovery environment is documented. The available paths are Compute Engine's serial console, disabled by default, and node or instance replacement. All are Google-hosted. | UNKNOWN (COS-specific), DOCUMENTED (platform paths) |

**Reading the map.** Five of the nine stages run on infrastructure only Google controls, in the
supported product: HOST, INSTALL, CONFIGURE, UPGRADE and RECOVER. One stage, BUILD, is genuinely
independent and documented in detail. One stage, BOOT, is documented as working outside Google
Cloud but only as a development workflow. Two stages, SIGN and ROLLBACK, have no published contract
at all.

**If Google's hosted services were unavailable, what would remain?** The public source tree, the
public build tooling, and a locally bootable image under QEMU. That is not nothing, and it is more
than a closed product would leave. It is also not an operable fleet, because the images, the update
service, the registries the extensions fetch from, the metadata server the configuration model
depends on, and the only supported runtime platform are all Google's. This is a dependency map read
from current documentation. It is not a prediction about Google, and the framework's bias controls
forbid making one.

**A fairness note that this framework requires.** The same chain must be applied to every project,
including Kairos. COS is not unusual for having vendor dependencies. It is unusual for the
dependencies and the product boundary being stated so plainly by the vendor, which makes the map
easier to draw here than it will be for several projects that present themselves as fully portable.
Ease of drawing the map is not the same as a worse result, and this profile does not treat it as
one.

---

## Follow-up research

Open questions this case study surfaced. Each would need deeper documentary work, a maintainer
correction pass, or experimental work outside this tier.

**Needs an experiment, or a Google answer**

1. What happens when an instance fails to boot a newly updated root partition? Is there boot-attempt
   tracking and automatic fallback, or is recovery entirely manual?
2. Is there a supported procedure to boot the previous root partition, and how many previous versions
   are retained?
3. What happens to a half-written passive partition when power is lost mid-update?
4. Does the stateful partition survive an A/B upgrade as a guarantee, and what happens to
   `/var/lib/docker` across a milestone change?
5. Is there any recovery path for an instance with no network and a corrupted stateful partition?
6. Can the in-place updater cross a milestone boundary, or does it only move within a family? Is
   downgrade possible at all?

**Needs a documentary answer from Google**

7. Which parts of a shipped image are not in the public repositories, and why is the statement
   hedged as "the majority"?
8. Can a third party reproduce an official image bit for bit from a `cos/manifest-snapshots` tag?
   What is that repository's contract?
9. How is an update payload authenticated? Which keys, which scheme, what rotation policy?
10. Which server does the updater contact, and is there any supported way to mirror it or run it
    privately, for example for a VPC Service Controls perimeter?
11. Does the stock image use dm-verity for the root filesystem? If so, why do the concept pages
    describe only a kernel-verified checksum?
12. Can a third party sign its own out-of-tree kernel modules with its own key, in any supported
    configuration? Do the LoadPin restrictions apply to standalone Compute Engine VMs or only to GKE
    node pools?
13. Is an SBOM in a standard format, build provenance, or FIPS validation published or planned?
14. Is there any supported way to install a corporate CA certificate or configure an HTTP proxy on a
    COS guest?
15. Which page is authoritative for end-of-support dates, the COS release notes table or the Compute
    Engine operating system details table? The two disagreed as of 2026-09-15.
16. Why did automatic updates become disabled by default at milestone 117, and what is the intended
    update mechanism for a standalone COS fleet now? How should reboot coordination be handled?
17. Why does the COS overview page still describe automatic weekly background updates when the
    auto-update page states the opposite default?

**Needs cross-profile comparison work in the epic**

18. Compare COS's "replace the node" model against in-place rollback models in Flatcar, bootc and
    Kairos, and determine what each buys for a fleet with local state versus a stateless fleet. The
    interesting question is not which is better. It is which workloads make the difference visible.
19. Compare the stateless-`/etc` reconciliation model against Ignition-style first-boot-only
    provisioning and against Talos's machine-config API. All three attack drift; they place the
    reconciliation point differently.
20. Compare the Secure Boot and in-place-update mutual exclusion in COS against how other image-based
    systems handle signed boot plus atomic update. This looks like a genuinely hard problem rather
    than a COS-specific defect, and it deserves the same question asked of every project.

---

## Bias and scope note

**Tier.** Documentation-only. No COS instance was created, no image was built, no update was run,
and nothing was broken on purpose. Every claim here is DOCUMENTED, INFERRED, UNKNOWN, NOT TESTED or
OUT OF TIER SCOPE. Nothing is REPRODUCED or OBSERVED, and the absence of those two labels is a
property of the tier, not a shortfall in the research.

**No reverse-engineering was performed.** COS descends from Chromium OS, which has a well-known
A/B update and verified-boot design. It would have been easy to fill dimension 5 by describing that
lineage's partition priority and boot-attempt counters and presenting it as COS behaviour. That was
deliberately not done. Google does not document it for COS, the internals may differ, and the
epic's tier definition excludes exactly this move. Dimension 5 is left mostly UNKNOWN as a result,
and the gap is the finding.

**Places where UNKNOWN was chosen over inference, deliberately:**

- Whether the stock root filesystem uses dm-verity. Google names dm-verity for Confidential Space
  and for a sealed OEM partition, not for the stock root.
- What the kernel does when the root checksum fails. "Verified" is quoted; "refuses to boot" is
  labelled INFERRED rather than stated as Google's claim.
- How the bootloader chooses between root partitions.
- Whether the stateful partition survives an upgrade.
- Whether ctr, crictl, strace or tcpdump ship in the image.
- Whether btrfs, ZFS, NFS or overlayfs work. The supported-filesystems page does not mention them,
  and the framework forbids reading missing documentation as proof of absence.

**Places where this profile refines the Pulse baseline, both from new primary evidence:**

- Dimension 7: kubelet and kubectl binaries do ship in the COS image, per the release notes, with a
  caveat that GKE may use different component versions. COS still does not run or configure a
  Kubernetes cluster by itself.
- Dimension 7: Google does publish a JSON mapping of GKE patch versions to COS node image versions,
  which partially answers a question the baseline recorded as having no published mapping.

**Where this profile inherits rather than re-verifies:** the end-of-support date discrepancy between
the COS release notes table and the Compute Engine operating system details table. The release notes
side was re-read on 2026-09-16. The Compute Engine page could not be retrieved in full, so the
discrepancy is carried forward from the 2026-09-15 baseline and flagged as not re-verified.

**Kairos bias control.** Mauro maintains Kairos. Nothing in this profile compares COS to Kairos,
and no COS limitation is framed as a Kairos advantage. Two places where COS is clearly stronger
than most of the comparison set are recorded plainly: the preinstalled support-bundle collector and
debugging container, and the CIS Level 1 default with a shipped scanner. Two places where COS's
constraints buy a real guarantee are recorded as guarantees, not as limitations: the stateless
`/etc` that makes system-configuration drift structurally impossible across a reboot, and the
module signing policy that keeps the verified root meaningful. The largest documented weakness,
the rollback and recovery gap, is recorded as UNKNOWN rather than as absent, because that is what
the evidence supports.

**No speculation about corporate behaviour.** This profile makes no statement about what Google
will do with COS, about strategy, or about the product's future. Dimension 22's dependency map
reads current documentation. It is not a forecast.

**Maintainer review.** The epic requires a factual-correction pass with maintainers before anything
comparative is published. COS does not accept public contributions and has no public issue tracker,
so there is no community channel for that pass. Any correction round would have to go through
Google Cloud support or a direct contact. That constraint should be resolved before any material
derived from this profile is published.
