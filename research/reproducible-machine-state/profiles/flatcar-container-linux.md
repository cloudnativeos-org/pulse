# Flatcar Container Linux: platform profile

Tracked as ,
the research epic, Reproducible
Machine State.

Flatcar Container Linux is a minimal, container-oriented Linux distribution built from a ChromiumOS
and Gentoo base, with no package manager, an A/B pair of read-only `/usr` partitions, and an
Omaha-protocol update client inherited from Chrome OS by way of CoreOS. It began in 2018 as what its
own announcement called "a friendly fork of CoreOS' Container Linux", started by Kinvolk after the
CoreOS acquisition, and it is the surviving continuation of that codebase: `update_engine`,
`locksmith`, `mantle`, `bootengine` and the `scripts` SDK are the CoreOS repositories, still moving.
Kinvolk was acquired by Microsoft in 2021, and the project was accepted into the CNCF in 2024. It
belongs in this investigation as the anchor of the Container Linux family, the architectural lineage
that every other A/B image-based system in the study either descends from, borrows from, or defines
itself against. Bottlerocket's GPT priority/tries/successful attribute scheme is the same Chrome OS
scheme; Azure Container Linux is derived from Flatcar directly and says so; Kairos, Talos and bootc
all make different choices about the same problem Flatcar solved first in this shape.

What makes it the right place to spend deep-tier effort is not age. It is that Flatcar is the case
where the framework's two hardest questions, §15's supply-chain ownership and §22's operational
independence, are answerable from primary sources rather than guessable. The whole build system is
public and runnable. The update server is open source, self-hostable, and is provably the same code
the project runs in production. The signing is documented down to which key signs what and where it
lives. Almost nothing in the lifecycle is a black box, which is the opposite of the hyperscaler
profiles in this study and is a real, testable architectural property rather than a marketing
posture.

**Depth tier: deep experimental core. This pass is the architecture study only.** The epic's
stratification puts Flatcar at "full build / provision / extend / update / break / recover cycle plus
both standardized experiment protocols". None of that was run here. That is a scope decision recorded
on the platform-profile task and on the epic before the
research started, not an omission: no experiment-report template is ratified for this tier, and the
four infrastructure decisions that gate a real experiment pass are open on
the research epic. The section "What a full
experimental pass needs" below scopes the missing half and prices it, so the gap is a costed decision
rather than a silence.

**What that means for evidence labels.** Where Flatcar documents a behaviour, this profile describes
it fully and labels it DOCUMENTED with a link. "What does the rollback mechanism do, according to the
project and its source" is a documentation question and is answered here. "Does it actually roll back
when we cut power mid-write, and how long does that take" is an experiment question and is marked
NOT TESTED / OUT OF TIER SCOPE. Nothing in this profile is REPRODUCED. A number of claims are
labelled OBSERVED, and in every case that means a measurement taken on 2026-09-16 against the GitHub
API, the Flatcar release servers, or the public Omaha update endpoint, with the query named. No
Flatcar instance was booted and no image was built.

**A note on source depth.** Flatcar's build system is public and Apache-2.0 or BSD licensed. Reading
it is a primary source, not reverse engineering, and this profile reads it where the prose
documentation stops short: which key signs the update payload, how sysext signing certificates get
into the image, and what an official build asserts about its own keys all come from
`flatcar/scripts`. Every such claim says so and links the file. Sections 15, 21 and 22 depend on this
and would be much weaker without it.

**Relationship to the Pulse baseline.** A sibling ticket,
the Pulse brief, produced a 14-dimension Pulse
entry for Flatcar on 2026-09-15 (`data/projects/flatcar.yaml`). This profile
treats that entry as a sourced factual baseline, reuses its citations where they overlap, and does
not contradict any of its cited facts. Six places where this profile goes further from new primary
evidence are flagged inline: the update payload's signing key and the absence of a detached payload
signature, the sysext signing certificate, the presence of Secure Boot artifacts on the stable
channel today, the CNCF-operated CDN behind both release hosts, the identity of the public update
service, and SELinux's documented default mode. Five of the six are extensions. The Secure Boot one
is a partial correction of a 2025 maintainer statement by observation of today's artifact listing,
and is described as exactly that, with both facts kept.

---

## Version and data provenance

| Field | Value |
|---|---|
| Version observed | `4757.2.0` (stable) |
| Build ID | `2026-09-11-1651` |
| Release date | 2026-09-14 |
| Other channels | beta `4790.1.0` (2026-09-14), alpha `4820.0.0` (2026-09-14), lts `4081.3.10` (2026-08-13) |
| Architectures released | `amd64-usr`, `arm64-usr` |
| Issue tracker / project repo | [flatcar/Flatcar](https://github.com/flatcar/Flatcar), default branch `main` |
| Build system | [flatcar/scripts](https://github.com/flatcar/scripts) |
| Licence | Apache-2.0 on the project repo; polyglot by component (`update_engine` BSD-3-Clause, `bootengine` BSD-2-Clause) |
| Documentation | [flatcar.org/docs/latest](https://www.flatcar.org/docs/latest/) |
| Data collected | 2026-09-16 (Pulse baseline collected 2026-09-15) |
| Primary source for version | [`version.txt`, stable channel](https://stable.release.flatcar-linux.net/amd64-usr/current/version.txt) |

`version.txt` on the stable channel returned `FLATCAR_VERSION=4757.2.0`, `FLATCAR_SDK_VERSION=4757.0.0`
and `FLATCAR_BUILD_ID="2026-09-11-1651"` on 2026-09-16. The four most recent GitHub releases on
`flatcar/scripts` are `stable-4757.2.0`, `beta-4790.1.0` and `alpha-4820.0.0`, all published
2026-09-14, and `lts-4081.3.10`, published 2026-08-13. The Pulse baseline's version numbers are
unchanged one day later. OBSERVED, via HTTP GET and `gh api repos/flatcar/scripts/releases`.

**Both release hosts sit behind a CNCF-operated CDN.** `stable.release.flatcar-linux.net` and
`update.release.flatcar-linux.net` each answer with HTTP 302 to `flatcar.cdn.cncf.io`. This matters
for §22 and is recorded there rather than treated as trivia: the hosting of record is the
foundation's, not a vendor's. OBSERVED, via `curl -I` on 2026-09-16.

### CNCF status, verified rather than assumed

**Flatcar Container Linux is at CNCF Incubating maturity as of 2026-09-16.** The CNCF project page
states: "Flatcar Container Linux was accepted to CNCF on August 2, 2024 at the Incubating maturity
level." The page shows no subsequent level change, and Flatcar does not appear among CNCF's graduated
projects. DOCUMENTED, [cncf.io/projects/flatcar](https://www.cncf.io/projects/flatcar/), checked
directly on 2026-09-16 rather than carried over from the Pulse entry.

Two related governance facts, both verifiable and both distinct from the maturity level: the project
states on its own site that Flatcar is "a Series of LF Projects, LLC", and `MAINTAINERS.md` says that
"All maintainers listed here should also be present in the
[CNCF project maintainers list](https://github.com/cncf/foundation/blob/main/project-maintainers.csv)."
DOCUMENTED, [flatcar.org/license](https://www.flatcar.org/license/) and
[MAINTAINERS.md](https://github.com/flatcar/Flatcar/blob/main/MAINTAINERS.md).

---

## 1. Definition and implementation of immutability

**Flatcar's immutability is partial by design, and the boundary is a partition boundary.** All OS
binaries live in `/usr`, which is a separate partition mounted read-only and protected by dm-verity.
The learning-series page states it plainly: "`/usr` is on a separate partition, and that partition is
strictly read-only", and describes dm-verity as inserting itself "by means of a device mapper layer
between the physical `vda3` and what's mounted on `/usr`", so the contents are "guarded by
cryptographic checksums". The supply-chain page repeats the mechanism from the other end: "The OS
partition is validated on each boot using `dm-verity`. The verity hash is baked into the init-rd at
build time." DOCUMENTED,
[learning series](https://www.flatcar.org/docs/latest/getting-started/learning-series/immutability-updates-rollbacks/),
[supply chain](https://www.flatcar.org/docs/latest/security/supply-chain/).

**Everything else is writable and persistent.** The root filesystem on partition 9 holds `/etc`,
`/opt`, `/var` and `/home`, is populated at first boot, and is not touched by updates:
"The data stored on the root partition isn't manipulated by the update process." `/bin`, `/sbin`,
`/lib` and `/lib64` are symlinks into `/usr`. There is no ephemeral-root model and no tmpfs root:
a file an operator writes to `/etc` stays there across reboot and across OS upgrade. DOCUMENTED,
[disk partitions](https://www.flatcar.org/docs/latest/devguide/sdk-disk-partitions/).

**The consequence is the single most important architectural fact about Flatcar, and it cuts both
ways.** Because the A/B pair covers `/usr` only, an OS rollback reverts the binaries and nothing
else. Configuration drift is not only possible, it is the expected steady state of a long-lived
Flatcar machine: Ignition runs once at first boot and never again, and everything after that is an
operator or an agent writing to a writable root that no mechanism reconciles. A version string
therefore identifies the OS binaries exactly and identifies machine state not at all. Set against
that, the same boundary is why an upgrade is cheap and safe: nothing an operator built up in `/var`
or `/etc` is at risk from an OS update, which is a guarantee whole-root A/B systems have to work
harder for. INFERRED as a consequence, from the DOCUMENTED partition scope above and the DOCUMENTED
once-only Ignition run in §6.

**How an operator determines actual state.** `cat /etc/os-release` and `uname -a` give the running
version and kernel; `rootdev -s /usr` names the active USR partition; `cgpt show /dev/vda` prints the
priority, tries and successful attributes for both USR partitions, which is the authoritative view of
which slot is live and whether the last boot was accepted. DOCUMENTED, learning series. There is no
documented command that reports "does this machine's writable root differ from a reference", and no
documented drift-detection facility at all. UNKNOWN whether one exists undocumented; missing
documentation is not proof of absence, and `/usr/share/flatcar/etc` (where the image's `/etc`
defaults are stashed at build time, per `finish_image` in the build library) suggests the raw
material for such a comparison is present on disk even though no tool is documented to use it.

**One documentation contradiction, carried forward from the Pulse baseline and still live.** The
`flatcar/Flatcar` README describes a "read-only root filesystem", which the learning series and the
partition layout both contradict. The learning series is the accurate one. Recorded here because a
reader who starts at the README will form the wrong mental model of what rolls back.

---

## 2. Unit of OS deployment

**Flatcar has two units, not one, and they are different artifacts with different properties.**
The install-time unit is a full disk image, published per platform: `flatcar_production_image.bin.bz2`
for generic bare metal, plus roughly forty platform variants (AMI, GCE, Azure VHD, OpenStack, QEMU,
VMware OVA, Hyper-V VHDX, Vagrant boxes, and so on). The update-time unit is a separate payload,
`flatcar_production_update.gz`, served by the Omaha update service. DOCUMENTED, with the artifact set
OBSERVED: the stable `current/` directory listing contained 1618 files on 2026-09-16, via
`curl -H 'Accept: application/json' https://stable.release.flatcar-linux.net/amd64-usr/current/`.

**Sizes, measured rather than claimed.** Raw QEMU image 569.2 MiB, bzip2-compressed generic image
557.4 MiB, live ISO 477.0 MiB (500,170,752 bytes), PXE initramfs 440.3 MiB (461,650,500 bytes),
kernel 33.5 MiB, per-release SBOM 15.5 MiB. The update payload the public Omaha service currently
advertises for stable is 540,489,428 bytes. OBSERVED, from the directory listing and from an Omaha
`updatecheck` POST to `https://public.update.flatcar-linux.net/v1/update/` on 2026-09-16.

**Content-addressability: no, and this is a real gap relative to OCI-native peers.** The OS is not
distributed through an OCI registry and there is no digest-addressed identity for a release. A
`flatcar-container.tar.gz` exists (452.7 MiB, OBSERVED) but the documentation describes no
OCI-registry distribution path for the OS itself. Identity is a version string plus a signature, not
a digest. The Omaha response does carry a per-package hash: the OEM sysext packages carry both a
legacy base64 SHA-1 `hash` and a `hash_sha256`, while the main OS payload in the response observed on
2026-09-16 carried only the legacy `hash`. OBSERVED, from the Omaha response body.

**Signing: yes, and thoroughly, for images.** Every published artifact carries a detached GPG
signature. The stable `current/` listing contained 621 `.sig` files on 2026-09-16 (OBSERVED). The
signing key is a "4096 bit GPG RSA key", access "restricted to core maintainers", "always stored
encrypted", with "a lifetime of one year", and renewal requiring "split secrets of multiple
maintainers". DOCUMENTED, [supply chain](https://www.flatcar.org/docs/latest/security/supply-chain/).
The public key fingerprint is published at
[flatcar.org/security/image-signing-key](https://www.flatcar.org/security/image-signing-key/) and the
verification procedure is documented.

**The update payload is signed differently, and this profile can now say how.** There is no detached
`.sig` for `flatcar_production_update.gz`: requesting one returns HTTP 404 while the payload itself
returns HTTP 200 with `content-length: 540489428` (OBSERVED, 2026-09-16). The signature is inside the
payload. `flatcar/scripts` generates payloads with
`delta_generator -private_key "/usr/share/update_engine/update-payload-key.key.pem"`, and the client
side verifies against the matching public key shipped in the image at
`/usr/share/update_engine/update-payload-key.pub.pem`. DOCUMENTED (source),
[`build_library/prod_image_util.sh`](https://github.com/flatcar/scripts/blob/main/build_library/prod_image_util.sh)
and [`flatcar-postinst`](https://github.com/flatcar/update_engine/blob/main/flatcar-postinst). This
resolves two UNKNOWNs the Pulse baseline left open about which key signs the payload.

**Mirrorable and air-gappable: yes, on both paths.** Images are ordinary HTTP files and
`flatcar-install -b BASEURL` overrides the mirror. Nebraska can host the payloads as well as the
metadata, which is the documented air-gap route. DOCUMENTED, see §10 and §22.

**Independently buildable: yes.** This is the property that most distinguishes Flatcar's unit of
deployment from every hyperscaler peer in this study, and it is covered in §3 and §15.

**What the payload format actually is remains UNKNOWN.** `delta_generator` is the Chrome OS
update-payload tool and the source is present, but the documentation does not specify the wire format,
and this profile did not read the payload generator's implementation.

---

## 3. OS construction and customization

**There is no package manager, and the project offers four distinct construction points instead.**
Ordered from least to most invasive:

**Build time, via the SDK.** The Flatcar SDK is the whole Gentoo/Portage build system, published as a
container on `ghcr.io`. The scripts README describes three flavours: a full SDK with both
architectures at "about 8GB in size (~3 GB compressed)", and per-architecture SDKs at "about 6GB in
size". The flow is `./run_sdk_container -t`, then `./build_packages`, `./build_image`, and
`./image_to_vm.sh` to produce a platform image. Building images needs privileged Docker with `/dev`
bind-mounted "because the SDK currently employs loop devices to create and to partition OS images".
Boards are `amd64-usr` and `arm64-usr`; a native ARM64 SDK is "not ready yet". Packages live in
`portage-stable` (kept aligned with upstream Gentoo) and `coreos-overlay` (Flatcar-specific ebuilds).
DOCUMENTED, [scripts README](https://github.com/flatcar/scripts/blob/main/README.md) and
[modifying Flatcar](https://www.flatcar.org/docs/latest/devguide/sdk-modifying-flatcar/). Kernel
configuration changes, added or removed kernel modules, patched libraries and entirely new packages
are all in scope at this layer.

**Image time, before distribution.** The boot, OEM and root partitions of a published image can be
modified offline. The documentation attaches a hard warning to this: never boot a customized image
before distributing it, because first-boot initialization would make every instance identical, break
the update server registration, skip SSH host key regeneration and stop Ignition from running.
DOCUMENTED,
[customize the image](https://www.flatcar.org/docs/latest/fb-provision/customize-image/customize-the-image/).

**First boot, via Ignition.** Files, users, systemd units, disks, filesystems and RAID arrays, once.
See §6.

**Runtime, via systemd-sysext.** This is Flatcar's answer to "no package manager" and it is the layer
an adopter will live in. A sysext is a squashfs or raw image that overlays `/usr`. Official extensions
split into enabled-by-default (Docker, containerd, OEM tools) and opt-in (ZFS, Podman, Python, NVIDIA
drivers, Incus, OverlayBD), enabled "by writing one name per line to
`/etc/flatcar/enabled-sysext.conf`". Community extensions come from the Sysext Bakery. From 3510.2.0,
`systemd-sysupdate` can keep extensions current on a timer. DOCUMENTED,
[system extensions](https://www.flatcar.org/docs/latest/sys-ext/).

**The sysext constraint is specific, documented, and is the single sharpest cost in Flatcar's
extensibility model.** "If your binaries link against Flatcar's binaries under `/usr`, you must couple
your sysext image to the Flatcar version by specifying `VERSION_ID=MAJOR.MINOR.PATCH`", and then "the
sysext image won't be loaded anymore after an OS update". The escape is static linking plus
`SYSEXT_LEVEL=1.0`. An organization that ships a dynamically linked agent as a sysext therefore
inherits a rebuild-and-revalidate obligation on every single OS bump, on a project whose stable
channel moves every 14 days. That is a real, recurring operational cost, and it is the price of a
`/usr` overlay model that has no package manager to reconcile dependencies. DOCUMENTED, same page.

**Sysexts are signed, and this profile can show where the certificate comes from.** The build injects
an ephemeral sysext signing certificate into the image: `sudo cp "${SYSEXT_SIGNING_KEY_DIR}/sysexts.crt"
"${root_fs_dir}/usr/lib/verity.d"`. Sysexts fetched during the post-install step are verified against
the update payload key, via `download_sysext -p /usr/share/update_engine/update-payload-key.pub.pem`.
DOCUMENTED (source), `prod_image_util.sh` and `flatcar-postinst`. Whether a third party can obtain or
use that ephemeral key to sign its own modules for Secure Boot nodes remains UNKNOWN, which is the
same question the Pulse baseline raised and which the source does not answer.

**Specific customization targets.** Out-of-tree kernel modules are built in the developer container
against an overlay on `/usr/lib/modules`; under Secure Boot "only the prebuilt sysext will work, as
the modules are signed" with the ephemeral kernel module signing key. NVIDIA drivers ship as prebuilt
signed sysexts with every release, amd64 only, in both proprietary and open flavours and for driver
series 535, 550 and 570 (OBSERVED from the artifact listing). Corporate CA certificates go to
`/etc/ssl/certs` followed by `update-ca-certificates`; the page does not state whether this survives
an OS upgrade, though the `/etc` persistence documented in §1 implies it does (INFERRED). FIPS is a
supported configuration rather than a certification (see §9). DOCUMENTED,
[NVIDIA](https://www.flatcar.org/docs/latest/os-config/host-config/using-nvidia/),
[kernel modules](https://www.flatcar.org/docs/latest/devguide/kernel-modules/),
[adding CAs](https://www.flatcar.org/docs/latest/security/cert-auth/adding-certificate-authorities/).

**The tradeoff, stated neutrally.** Flatcar makes far fewer decisions for the operator than a
hyperscaler appliance does, and unlike an appliance it hands over the entire factory. What it does not
provide is a supported way to add something to `/usr` at runtime that survives the next update without
the operator owning a build. The flexibility is real and it is deferred work, not avoided work.

---

## 4. Upgrade mechanism

### Before the upgrade

The new OS comes from an Omaha-protocol update service. `update_engine` polls it: "Each machine
should check in about 10 minutes after boot and roughly every hour after that." The endpoint and the
channel are two variables in `/etc/flatcar/update.conf`: `SERVER`, defaulting to
`https://public.update.flatcar-linux.net/v1/update/`, and `GROUP`, with public values `stable`, `beta`
and `alpha`. An empty or absent file is fine, because the defaults ship in
`/usr/share/flatcar/update.conf`. DOCUMENTED,
[update strategies](https://www.flatcar.org/docs/latest/updates-releases/releases/update-strategies/),
[update.conf](https://www.flatcar.org/docs/latest/updates-releases/releases/update-conf/).

The node initiates. There is no push. Kubernetes is not involved at any point, and no Flatcar-hosted
infrastructure is required: pointing `SERVER` at a self-hosted Nebraska removes the project's servers
from the path entirely. Verification is against the update signing key: "Before installation, update
images are validated against the update signing key", and "An update is installed only after
successful validation". DOCUMENTED, supply chain page.

**The public update service is Nebraska.** The Omaha response observed on 2026-09-16 carried
`server="nebraska"` in its root element. The service the project runs for everyone is the same
open-source server it tells operators to self-host, which is a stronger independence property than
"a self-hosted alternative exists". OBSERVED, from the response body of an Omaha `updatecheck` POST.

### During the upgrade

"Updates are always downloaded to the passive partition when they become available." The running
`/usr` is untouched, and so is the writable root. What gets written is the inactive USR slot, and then
the GPT attributes: "after an update, Flatcar Container Linux will re-configure the GPT priority
attribute, instructing the bootloader to boot from the passive (newly updated) partition."
DOCUMENTED, update strategies and disk partitions.

The bootloader, kernel and initrd are handled differently from Bottlerocket's per-set boot partitions.
Flatcar has one EFI system partition and one BIOS-BOOT partition, shared. The kernel is inside the USR
image and the verity root hash is baked into the initramfs at build time (DOCUMENTED, supply chain).
What an OS update does to the shim and GRUB binaries on the EFI system partition, which sits outside
the A/B pair, is not described on any page found. UNKNOWN, and it is the same gap the Bottlerocket
profile flagged for the same structural reason.

**Power loss halfway through.** The mechanics documented above mean the active slot is never written
during staging and the GPT priority flip is the last step, so an interrupted download should leave a
partial inactive slot and an unchanged, bootable active slot. That is INFERRED, not DOCUMENTED. No
page states it and nobody has tested it here. NOT TESTED. It is experiment 4 in the experiment section.

### At reboot

Reboot is a separate decision from staging, which is the part of Flatcar's design that most rewards
reading carefully. `locksmithd` owns it, configured by `REBOOT_STRATEGY` in `/etc/flatcar/update.conf`:

- `etcd-lock`: "Reboot after first taking a distributed lock in etcd (reboot window applies)"
- `reboot`: "Reboot immediately after an update is applied (reboot window applies)"
- `off`: "Do not reboot after updates are applied"

"The default behavior is `reboot` and results in a reboot with a delay of 5 minutes." Reboot windows
restrict when this can happen, for example every Thursday between 04:00 and 05:00. DOCUMENTED, update
strategies.

Slot selection at boot is by GPT attributes. The active partition shows `priority=1 tries=0
successful=1`; a staged update gets a higher priority and `tries=1`. "The bootloader decrements a
tries counter before each boot attempt." DOCUMENTED, learning series.

**Boot success is an OS-level criterion with a time basis, not a health check.** "The rollback to the
previously installed version is done by GRUB and happens automatically if `update-engine` had no
chance to mark the version as successful", and marking happens after roughly two minutes of running
the new version. Neither Kubernetes health nor workload health enters into it. That is a deliberate
scope: the OS decides whether the OS came up, and anything above that is the orchestrator's problem,
which is what FLUO and kured exist for (§7, §11). DOCUMENTED,
[manual rollbacks](https://www.flatcar.org/docs/latest/diagnostics/manual-rollbacks/).

### After failure

Rollback is automatic and local. Tries reach zero, GRUB falls back to the retained slot, and no
network, no management plane and no operator are required. Persistent state survives entirely,
because the writable root was never in scope. Container images in `/var/lib/docker` survive.
Kubernetes state on the node survives, and whether the cluster is happy about a node that just changed
kernel version twice is outside what this mechanism promises. DOCUMENTED for the mechanism, NOT TESTED
for the behaviour.

### Comparison to the other upgrade architectures in this study

Flatcar is A/B with the smallest reversible unit of the A/B systems in this study. Bottlerocket flips
a set of three partitions covering boot, root and the verity hash tree, with a read-only root, so a
Bottlerocket rollback reverts more of the machine. Whole-root A/B systems revert more still.
OSTree-style systems revert a commit that covers the whole OS tree. Flatcar reverts `/usr`. The
practical reading: Flatcar's upgrade is the least likely of the group to lose operator state and the
least able of the group to undo an operator's mistake. Neither half of that is a defect; they are the
same design decision seen from two sides, and which one an organization wants depends on whether its
machines are cattle or something it has invested in.

---

## 5. Rollback and recovery

The framework asks these to be treated as different concepts, and Flatcar makes the distinction easy
because its answers are genuinely different in kind.

**Rollback to the previous OS: automatic, local, network-independent, and bounded at one step back.**
Covered in §4. Exactly two USR slots exist, so exactly one previous version is retained. "There is no
method to downgrade to an arbitrary version number." DOCUMENTED, manual rollbacks.

**Rollback to a chosen known-good version: possible, but it is a network operation.**
`sudo flatcar-update --to-version 2905.2.6 --disable-afterwards` installs a specific version to the
inactive slot and can stop further updates. It downloads a payload, so it needs a reachable update
service, which may be a self-hosted one. DOCUMENTED, manual rollbacks and
[`flatcar/init`'s `bin/flatcar-update`](https://github.com/flatcar/init/blob/flatcar-master/bin/flatcar-update)
(note that repository's default branch is `flatcar-master`, not `main`).

**Manual slot switch: entirely offline.** `cgpt find -t flatcar-usr` to list the USR partitions,
`rootdev -s /usr` to identify the active one, `cgpt prioritize /dev/sda3` to promote the other, and
`cgpt add -T 1 /dev/sda3` to restore a try if needed. This requires no network at all. The
documentation attaches a caution to both manual paths: "Neither performing a manual rollback nor
forcing a channel downgrade are recommended." DOCUMENTED, manual rollbacks.

**Rollback of complete machine state: not offered.** Nothing reverts `/etc`, `/opt` or `/var`. A bad
configuration change survives every rollback mechanism Flatcar has. This is the direct consequence of
§1's partition boundary and it is the most important thing to say about this dimension.

**Recovery environment: the live media, and it is a full one.** The ISO boots to a running Flatcar
with a shell, and `flatcar-install` runs from it. The PXE image runs "completely out of RAM" and needs
"A minimum of 3 GB of RAM". Both are ordinary Linux environments with the usual tools, so filesystem
inspection and repair of a damaged root is a normal Linux exercise rather than a special mode.
DOCUMENTED, [booting with ISO](https://www.flatcar.org/docs/latest/deploy/bare-metal/booting-with-iso/),
[booting with iPXE](https://www.flatcar.org/docs/latest/deploy/bare-metal/booting-with-ipxe/).

**Factory reset or reprovision in place: UNKNOWN.** No such command or page appears anywhere in the
documentation sitemap, which this profile enumerated in full
([sitemap.xml](https://www.flatcar.org/sitemap.xml), OBSERVED 2026-09-16, 152 `/docs/latest/` URLs).
Reinstall is the only documented answer. Recorded as UNKNOWN rather than "not supported", because a
wipe of partition 9 plus a fresh `flatcar/first_boot` marker would plausibly do it and nobody has
written that down either way.

**Remote recovery: UNKNOWN at the project level.** Nebraska can pin a version and pause a rollout, but
no documented mechanism reaches into a machine that will not boot. Anything of that shape is
platform-specific, for example a cloud serial console.

**"Known-good state", in Flatcar's own terms, is a USR partition that booted and got marked
successful.** That is a narrower definition than most systems in this study use, and it is internally
consistent: Flatcar only claims to manage the OS binaries, so that is the only thing it claims to know
is good.

---

## 6. Configuration model

**Ignition is the machine-configuration mechanism, and it runs exactly once.** "Ignition only runs
once, during the first boot of the system." It executes in the initramfs, before systemd, which is
what lets it partition disks, create filesystems and assemble RAID arrays as well as write files and
units. First-boot detection is a marker file: GRUB "checks for a file called `flatcar/first_boot` in
the EFI System Partition" and sets `flatcar.first_boot=detected`; after a successful run the system
"deletes the `flatcar/first_boot` file". DOCUMENTED,
[Ignition](https://www.flatcar.org/docs/latest/fb-provision/ignition/),
[boot process](https://www.flatcar.org/docs/latest/fb-provision/ignition/boot-process/).

**Butane is the authoring layer.** Operators write YAML; `butane` transpiles it to the Ignition JSON
the system consumes; `ignition-validate` checks it before deployment. The Flatcar Container Linux
Config (`cl-config`) format is the older equivalent and is still documented. DOCUMENTED,
[Butane](https://www.flatcar.org/docs/latest/fb-provision/butane/).

**Separating the four configuration layers the framework asks about:**

- *Image configuration* is the SDK build, plus offline edits to a published image's partitions (§3).
- *Machine configuration* is Ignition, once, at first boot.
- *Runtime configuration* is ordinary Linux: files under `/etc`, systemd drop-ins, `systemctl`,
  `update-ca-certificates`, `/etc/flatcar/update.conf`, `/etc/flatcar/enabled-sysext.conf`. Most of it
  takes effect without a reboot; for example a networkd change needs
  `sudo systemctl restart systemd-networkd` rather than a reboot. DOCUMENTED,
  [networkd](https://www.flatcar.org/docs/latest/os-config/network/network-config-with-networkd/).
- *Cluster configuration* is not Flatcar's concern at all (§7).

**Declarative at first boot, imperative forever after.** This is the honest characterization and it
has consequences the framework specifically asks about. Idempotency: Ignition is idempotent in the
trivial sense that it cannot run twice. Drift: unmanaged and undetected by the OS, so an adopter needs
an external configuration-management or GitOps layer if drift matters, which is precisely the
enterprise-standards question §20 raises. Source of truth: whatever the operator's provisioning
pipeline holds, not the machine. Version control and signing of configuration: an operator concern, on
operator-chosen tooling; Ignition configs are plain JSON files, so signing them is possible with
ordinary tools but no Flatcar-specific mechanism is documented. UNKNOWN whether the project intends
one.

**Secrets.** Ignition fetches configuration over HTTP, HTTPS, S3 or TFTP, and the remote fetch is the
documented route for anything that should not sit in a cloud user-data field. No project-specific
secret store, sealing or attestation-gated release mechanism is documented. UNKNOWN.

**Remote inspection of configuration: UNKNOWN.** Nothing reports a machine's configuration back to a
central place. Nebraska reports version and update status per instance (§11), which is not the same
thing.

**Configuration change without reboot or rebuild: mostly yes**, because this is a conventional systemd
userspace. The exceptions are anything in `/usr` (rebuild or sysext) and anything Ignition-only, for
example disk layout.

---

## 7. Kubernetes coupling

**Flatcar is a container host, not a Kubernetes appliance, and the documentation is consistent about
it.** Kubernetes is not shipped. It is one orchestrator among several, with Docker, Incus and Nomad
each getting their own documentation pages. The OS runs perfectly well with no orchestrator at all.
DOCUMENTED,
[Kubernetes](https://www.flatcar.org/docs/latest/orchestrate/kubernetes/getting-started-with-kubernetes/),
[Incus](https://www.flatcar.org/docs/latest/orchestrate/containers/incus/).

**Which distributions work: whichever the operator installs.** kubeadm, Cluster API, Kubespray and
Typhoon are documented or widely used routes; k3s and Kubernetes components are available as Sysext
Bakery extensions. Changing distribution is an operator decision with no OS-level obstacle.
DOCUMENTED.

**Lifecycles are fully independent.** The OS updates on its channel cadence; Kubernetes updates on
whatever path installed it. Neither version constrains the other at the OS level, which is a genuine
advantage over variant-based systems where the orchestrator minor version is fixed at image build
time. It is also a genuine cost: nobody has tested the specific pairing an operator ends up running,
and the responsibility for that matrix is entirely the adopter's.

**Who manages whom.** The OS does not manage Kubernetes. Kubernetes can manage the OS's reboots, and
there are three distinct, mutually confusable mechanisms:

- `locksmithd`, OS-level, not Kubernetes-aware except through an etcd lock.
- FLUO (`flatcar-linux-update-operator`), Kubernetes-native: "When a reboot is needed after updating
  the system via update_engine, the operator will drain the node before rebooting it", one node at a
  time. Mutually exclusive with `locksmithd`.
- `kured`, third party, supported since 3067.0.0.

DOCUMENTED, [FLUO](https://github.com/flatcar/flatcar-linux-update-operator),
[locksmith](https://github.com/flatcar/locksmith).

**Machine lifecycle ownership sits with the OS by default and can be delegated upward.** That is
unusual in this study: most systems either keep it (appliance) or hand it over (Kubernetes-managed
node images). Flatcar ships both and makes the operator choose, which is flexibility with a
configuration-error surface attached, since running FLUO and `locksmithd` together is a documented
mistake.

**Non-Kubernetes workloads.** A plain container host, an appliance, a database host, a storage node
(ZFS and RAID are documented, §13), a GPU node (NVIDIA sysexts, §8), an edge gateway and an ordinary
systemd service host are all ordinary uses. Flatcar as a hypervisor host is UNKNOWN: no KVM or libvirt
host documentation was found, only guest documentation.

**On the spectrum the framework proposes**, Flatcar sits clearly at the general-immutable-substrate
end of "Kubernetes appliance <-> Kubernetes-oriented OS <-> general immutable infrastructure
substrate", a little short of a full construction kit because the base image's contents are the
project's decision unless the operator takes over the SDK.

---

## 8. Hardware and platform support

**Architectures: amd64 and arm64, both on all four channels. No riscv64.** OBSERVED, from the
per-architecture artifact trees on the release servers, and DOCUMENTED on the releases page. The
riscv64 request, [flatcar/Flatcar#1420](https://github.com/flatcar/Flatcar/issues/1420), has been open
since 2024-04-09 and was last updated 2025-02-13 (OBSERVED, `gh api`). This is a documented absence,
not an unknown.

**There is riscv64 work in that thread, and it is worth stating precisely because it is easy to
over-read.** A Flatcar maintainer wrote in the issue that they had produced Flatcar RISC-V images from
a personal release page, "made to support only QEMU", and were attempting physical boards
(LicheePi4a, HiFive Unmatched, Banana Pi F3). That is a maintainer's individual experiment, not an
official release, not a supported board, and not a roadmap commitment. DOCUMENTED as a maintainer
statement in the issue thread; anything beyond that is UNKNOWN, and this profile does not speculate
about intent.

**Platforms.** Eleven clouds are documented as officially supported (Akamai Connected Cloud, AWS EC2,
Brightbox, DigitalOcean, Exoscale, Google Compute Engine, Hetzner, Azure, Oracle Cloud, STACKIT,
VMware) and three as community supported (OVHcloud, Scaleway, Vultr). Virtualization coverage is
broad: QEMU, libvirt, VirtualBox, VMware, Hyper-V, Proxmox VE, OpenStack, KubeVirt, Vagrant,
Eucalyptus. Bare metal is a first-class target with ISO, PXE, iPXE and `flatcar-install`. The
published artifact set corroborates the list: per-platform images exist for each, plus per-platform
OEM sysexts (`oem-ami.raw`, `oem-azure.raw`, `oem-gce.raw`, `oem-hetzner.raw` and so on). DOCUMENTED
and OBSERVED. See [cloud deployment](https://www.flatcar.org/docs/latest/deploy/cloud/).

**SBCs and edge.** Raspberry Pi 4 support "is still in its early stages and is not thoroughly tested"
and depends on third-party UEFI firmware the documentation labels unofficial. DOCUMENTED,
[Raspberry Pi](https://www.flatcar.org/docs/latest/deploy/bare-metal/raspberry-pi/). No Jetson, no
NPU, no industrial-PC and no cellular documentation was found. UNKNOWN rather than unsupported: the
generic arm64 image plus a sysext is a plausible route and nobody has documented it.

**GPUs.** NVIDIA is well handled and amd64 only: prebuilt, signed sysexts for driver series 535, 550
and 570, in proprietary and open-kernel-module variants, rebuilt with every release (OBSERVED from the
stable artifact listing; DOCUMENTED on the NVIDIA page). AMD and Intel GPU support is UNKNOWN.

**TPM**: see §9. **Unusual NICs, RAID controllers, SR-IOV, RDMA, Wi-Fi**: the kernel config is
published per release (`flatcar_production_image_kernel_config.txt`, OBSERVED), so an operator can
check driver availability exactly rather than guess, which is a genuinely useful property. Whether any
given device is present in the default config is answerable but was not enumerated here.

**"If unsupported hardware appears tomorrow, can an organization add support itself?"** Yes, and the
answer has two tiers with very different costs. A driver that only needs a kernel module: build it in
the developer container against the release's `/usr/lib/modules` and ship it as a sysext, modest
effort, with the Secure Boot signing caveat from §3. A change that needs a different kernel
configuration, a patched kernel, or a new board: take over the SDK, which means owning an 8 GB build
environment, a Portage tree, and from then on your own release pipeline. That second tier is
genuinely available, which is more than most of this study's hyperscaler entries offer, and it is not
cheap.

---

## 9. Security and chain of trust

Tracing the chain the framework asks for: firmware -> bootloader -> kernel -> initrd -> root
filesystem -> extensions -> configuration -> workload.

**Firmware to bootloader (Secure Boot): the incomplete link, with a correction to record.** Signed
shim and GRUB ship with every release. On 2026-09-16 the *stable* channel's `current/` directory
contained `flatcar_production_image.shim`, `flatcar_production_image.grub`,
`flatcar_production_image.vmlinuz` with detached signatures, and a Secure Boot QEMU flavour
(`flatcar_production_qemu_uefi_secure_image.img` plus its `_efi_vars.qcow2`). OBSERVED. The build
system has a `sbsign_prod_image` function that signs the image, kernel, GRUB and PCR policy
(DOCUMENTED (source), `prod_image_util.sh`). What is missing is not signing but *chain of trust from
stock firmware*: a maintainer stated in June 2025 that "images in the alpha channel have secure boot
signatures but with a shim that is not signed by the official 3rdparty UEFI CA (our shim-review
submission is blocked on a legal/procedural issue)", and another maintainer replied that operators
"could just add our DB certificate in the short term". The tracking request,
[flatcar/Flatcar#501](https://github.com/flatcar/Flatcar/issues/501), has been open since 2021-09-08
and was last updated 2025-06-23 (OBSERVED). **There is no Secure Boot page anywhere in the
documentation**, which this profile verified against the full sitemap. The accurate 2026-09-16
statement is therefore: Secure Boot artifacts are published on stable, custom-key or DB-enrolment
Secure Boot is achievable, shim-review status is UNKNOWN, and the operator-facing documentation for
any of it does not exist.

**Bootloader to kernel to initrd to root filesystem.** GRUB selects a USR slot by GPT attributes. The
verity root hash is "baked into the init-rd at build time" and `/usr` is validated on every boot by
dm-verity. A per-release verity reference is published
(`flatcar_production_image_verity.txt`, a single 64-character hash;
`a66ed27d0706be144ccec48de70ea6c746e989992f9c6e27405085cc2796ce99` for 4757.2.0, OBSERVED). Kernel
lockdown in integrity mode is enabled when Secure Boot is on. DOCUMENTED, supply chain page.

**The writable root is not in the chain.** dm-verity covers `/usr`. Partition 9 has no integrity
mechanism documented beyond whatever filesystem and encryption the operator chooses. This is the
security-side statement of §1's boundary: tamper *prevention* and *detection* cover the OS binaries;
neither covers configuration or data.

**Extensions.** Sysexts are signed with an ephemeral per-release certificate placed at
`/usr/lib/verity.d/sysexts.crt`, and post-install sysext downloads are verified against the update
payload key (DOCUMENTED (source), §3). Whether a third party can participate in that signing is
UNKNOWN. The LUKS page notes a related gap in the measurement chain: "Flatcar OEM extensions are also
read from the OEM partition without creating measurements nor with pre-checking their checksum".

**Measured boot and TPM.** PCRs 9 to 13 are recorded and a PCR policy bundle
(`flatcar_production_image_pcr_policy.zip`, 20,304 bytes, OBSERVED) ships per release. The
documentation is internally inconsistent: the trusted-computing page still says TPM 2.0 support "will
be added in a future Flatcar Container Linux release" while the LUKS page states "TPM2-backed rootfs
encryption in Flatcar is supported from version 3913.0.1 onwards". The LUKS page is the current one.
DOCUMENTED, with the contradiction recorded as a fact about the documentation.

**Disk encryption.** LUKS is opt-in, via `systemd-cryptenroll` (PCR 7 by default) or Clevis with TPM
or Tang. The documented caveats are unusually candid and should not be softened: GRUB's measurements
mean "TPM PCR values would not be predictable/universal for a given Flatcar version but would have to
be observed locally"; "binding a secret against the full TPM PCR state only works reliable when auto
updates are disabled and when the first-boot setup is not involved, i.e., on the second boot"; and the
strongest binding carries "Consider this approach experimental and understand that this protection has
holes." DOCUMENTED, [LUKS](https://www.flatcar.org/docs/latest/security/encryption/luks/).

**Remote attestation: UNKNOWN.** PCRs are measured and a policy bundle is published, but no
attestation service, protocol or verifier is documented.

**Artifact signatures, SBOM, provenance, reproducibility.** Detached GPG signatures on everything
(§2). A per-release SBOM (`flatcar_production_image_sbom.json`, 15.5 MiB, OBSERVED), licence manifest,
package list and kernel config. SLSA Level 3 claimed, with per-package provenance "shipped within the
image at `/usr/share/SLSA/`". Builds are described as reproducible with a stated caveat: output "may
differ in a bit-by-bit comparison ONLY in places where this volatile information is compiled into the
binaries" (timestamps, usernames, hostnames). Build infrastructure is "a dedicated machine (not a VM)
in a secure, access-controlled Equinix Metal data center", reachable "only via a VPN (not via public
internet)". DOCUMENTED, supply chain page.

**The project lists its own remaining gaps**, which is worth crediting and worth recording exactly:
hermetic builds are not implemented; "Flatcar currently does not support setting up a full chain of
trust via TPM"; "changes to the build system do not enforce approval by a second administrator"; and
builder ID tracking during CI builds is missing. DOCUMENTED, same page.

**SELinux: present, permissive by default.** "Flatcar Container Linux implements SELinux, but
currently does not enforce SELinux protections by default." Switching to enforcing is documented, with
two named incompatibilities: Btrfs volumes and volumes shared between containers, and Flannel 0.15+
installed via `kube-flannel.yml`. DOCUMENTED,
[SELinux](https://www.flatcar.org/docs/latest/security/encryption/selinux/) and
[hardening guide](https://www.flatcar.org/docs/latest/security/hardening/hardening-guide/). This
resolves a Pulse baseline UNKNOWN.

**Default attack surface is small and documented**: "the only service that listens by default on
Flatcar Container Linux is sshd on port 22 on all interfaces", and the `core` user has sudo via the
wheel group. The hardening guide recommends masking `sshd.socket`, restricting the `core` user,
restricting the Docker socket group, and blacklisting the USB module. It does not cover firewalling,
auditd or sysctl hardening. DOCUMENTED.

**FIPS: honestly scoped.** "Flatcar is not officially FIPS certified, it is possible to deploy it so
that it is compliant with two of these standards", from 3185.0.0, with named caveats including the
argon2id LUKS KDF and some SSH ciphers. DOCUMENTED,
[FIPS](https://www.flatcar.org/docs/latest/security/hardening/fips/). For a regulated buyer this is
the correct disclosure and also a hard stop where a certificate is required.

**CVE handling.** A seven-person security team is named in `MAINTAINERS.md`, a `SECURITY.md` exists on
the project repo, and a `flatcar/security-triage` repository is active (last pushed 2026-09-04,
OBSERVED). Per-CVE response times were not measured. NOT TESTED.

---

## 10. Provisioning and zero-touch deployment

**Every route ends at Ignition.** The routes themselves:

- **Live ISO** (477.0 MiB, OBSERVED): boots a full Flatcar, then `flatcar-install` writes to disk.
- **PXE and iPXE**: `flatcar_production_pxe.vmlinuz` plus `flatcar_production_pxe_image.cpio.gz`,
  chained from a boot script. "This will run Flatcar Container Linux completely out of RAM" and needs
  "A minimum of 3 GB of RAM". Configuration arrives via `ignition.config.url=`, which accepts HTTP,
  HTTPS, S3 and TFTP.
- **Cloud images**, per provider, with configuration through the provider's user-data channel.
- **`flatcar-install`**, the installer, which "downloads an image, verifies it with gpg, and then
  copies it bit for bit to disk", needs at least 8 GB of usable space, and runs from any Linux
  distribution. Its flags are the whole air-gap story in one line: `-d DEVICE`, `-C CHANNEL`,
  `-V VERSION`, `-i IGNITION`, `-b BASEURL` to override the mirror, `-f IMAGE` to "Install unverified
  local image file to disk instead of fetching", and `-k KEYFILE` to "Override default GPG key for
  verifying image signature".
- **OEM partition**, which can carry mandatory or fallback Ignition configuration and kernel
  arguments. This is the route closest to factory preload.

DOCUMENTED,
[installing to disk](https://www.flatcar.org/docs/latest/deploy/bare-metal/installing-to-disk/),
[iPXE](https://www.flatcar.org/docs/latest/deploy/bare-metal/booting-with-ipxe/),
[Ignition](https://www.flatcar.org/docs/latest/fb-provision/ignition/).

**`-f` plus `-k` is the important pair and deserves calling out.** Together they mean an operator can
install from a locally held image, verified against a key the operator chose, with no route to any
Flatcar server. That is an operator-owned trust root at install time, and few systems in this study
offer it as a documented flag rather than an unsupported workaround.

**The factory scenario: "can 5,000 identical devices leave a factory and independently establish
secure identity and desired state on first boot?"** Partly, and the gap is specific. Desired state:
yes, via an OEM-partition Ignition config or a network config URL. Independence: yes, given DHCP and a
reachable config source, or none at all if the config is embedded. **Secure identity: not from
anything Flatcar provides.** There is no documented device-identity bootstrap, no enrolment protocol,
no attestation-gated first contact, and no per-device key provisioning mechanism. SSH host keys are
generated on first boot, which prevents the worst failure mode but is not an identity system. An
adopter must bring its own, for example a TPM-backed enrolment in an Ignition-run unit. UNKNOWN
whether the project considers this in scope; no page addresses it.

**The customization warning matters for exactly this scenario** and is repeated here because it is the
trap: an image customized offline must never be booted before distribution, or every device gets the
same machine ID, the update-server registration breaks, SSH host keys are not regenerated, and
Ignition will not run. DOCUMENTED, customize-the-image.

---

## 11. Fleet lifecycle

Splitting by ownership, as the framework requires.

**In the open-source OS itself:** `update_engine` (the Omaha client), `locksmithd` (reboot manager
with an etcd-based distributed lock and reboot windows), and `/etc/flatcar/update.conf` as the
per-node policy surface (`GROUP`, `SERVER`, `REBOOT_STRATEGY`). Version pinning is
`flatcar-update --to-version X --disable-afterwards`, or `SERVER=disabled`, which the documentation
recommends over other methods because it avoids partially applied updates. DOCUMENTED.

**In open-source companion projects, all under the `flatcar` GitHub organization, all Apache-2.0:**

- **Nebraska**: a self-hostable Omaha update server. Groups and channels, custom groups "for greater
  control over the updates", rollout control, and per-instance statistics. It can host the payloads
  too, with `-host-flatcar-packages=true -flatcar-packages-path=...`, which is the documented route for
  "an isolated environment without internet access (e.g air-gapped environment)". DOCUMENTED,
  [managing updates](https://www.flatcar.org/docs/latest/updates-releases/nebraska/managing-updates/),
  [flatcar/nebraska](https://github.com/flatcar/nebraska).
- **FLUO**: Kubernetes-native reboot coordination with node draining, one node at a time.
- **kured**: third party, supported since 3067.0.0.

**In a commercial product:** Flatcar Container Linux Pro, a Microsoft Azure Marketplace listing
offering an Azure-optimized edition with enterprise support, alongside a free BYOL listing. Nothing in
the update or fleet path requires it.

**Mapping to the framework's checklist.** Inventory and per-instance version reporting: Nebraska.
Desired OS version and staged rollout: Nebraska groups and channels, plus pause and resume. Canaries:
achievable by group membership; no dedicated canary abstraction is documented. Maintenance windows and
concurrency: `locksmithd` reboot windows and the etcd lock; FLUO's one-node-at-a-time drain.
Kubernetes-aware draining: FLUO or kured. Health gates: only the OS-level boot-success criterion from
§4; no application health gate exists at the OS layer. Automatic rollback: §5, per node, not
fleet-coordinated. Topology-aware rollout: UNKNOWN, nothing documented. Remote reset and remote
recovery: UNKNOWN, nothing documented. Disconnected fleets: supported through a self-hosted Nebraska.
Audit trail: Nebraska's instance statistics are the closest thing documented; a general audit log is
UNKNOWN.

**One vendor-platform fact, with its scope stated carefully.** Microsoft's AKS documentation states
that from 2026-06-08 AKS no longer supports Flatcar Container Linux for AKS (preview), stops producing
node images and security patches, and will remove existing Flatcar node images on 2026-09-08. The same
page notes that on AKS, Flatcar's built-in A/B update was disabled in favour of full node image
updates. Its replacement, Azure Container Linux, is documented by Microsoft as "derived from the
Flatcar Container Linux project", retaining the update model, the USR-A/USR-B layout and the OEM
package model, with Azure Linux RPMs replacing the Portage build. Both are facts about one vendor's
managed-Kubernetes offering and about a downstream derivative. Neither is a documented fact about the
upstream CNCF project, which released on three channels two days before this profile was written. No
inference beyond what those pages state is drawn here, per the framework's rule against speculating on
corporate behaviour. DOCUMENTED,
[Flatcar for AKS](https://learn.microsoft.com/en-us/azure/aks/flatcar-container-linux-for-aks),
[Azure Container Linux overview](https://learn.microsoft.com/en-us/azure/azure-linux/azure-container-linux-overview).

---

## 12. Debugging and day-2 operations

**Flatcar's day-2 posture is "a normal Linux box with an unusual `/usr`", and that is its single
biggest operational advantage over the appliance-shaped systems in this study.**

**SSH: present, with no default credential.** `sshd` is the only listening service by default. It is
unusable until a key arrives through Ignition or `update-ssh-keys`. DOCUMENTED,
[adding users](https://www.flatcar.org/docs/latest/os-config/host-config/adding-users/), hardening
guide. The consequence cuts both ways and the framework asks for both halves. In favour: an operator
with a broken node uses `ssh`, `journalctl`, `systemctl`, `cgpt` and a text editor, and every hour of
existing Linux experience transfers. Against: a shell on the host is a lateral-movement surface that
an API-only system does not have, and there is no OS-level audit of what was done in that shell. A
regulated environment may prefer the appliance model precisely because it removes the option.

**Debugging tools: `toolbox`.** With no package manager, the documented answer is a Fedora container
under `systemd-nspawn`: "You can use common debugging tools like tcpdump or strace with Toolbox."
DOCUMENTED,
[installing debugging tools](https://www.flatcar.org/docs/latest/diagnostics/install-debugging-tools/).
This needs a container image, so it needs either a network or a pre-pulled image, which is a real
constraint in the "broken networking" scenario the framework asks about.

**Logs.** `journalctl` for the system log. Kernel crash logs go through pstore, moved into
`/var/lib/systemd/pstore` by `systemd-pstore.service`, with the serial console as the fallback where
pstore is unavailable. DOCUMENTED,
[collecting crash logs](https://www.flatcar.org/docs/latest/diagnostics/collecting-crash-logs/),
[reading the system log](https://www.flatcar.org/docs/latest/diagnostics/reading-the-system-log/).

**Serial console: supported**, and it is the documented fallback for Ignition failures too, where the
listed scenarios are an emergency shell with visible errors, stuck console output needing kernel
parameter changes, and no console access at all, which is handled by validating configs offline before
deployment. DOCUMENTED, Ignition boot process.

**Filesystem inspection and modification: unrestricted on the writable root, impossible on `/usr`**
while running. The live ISO covers the case where the root itself needs repair.

**Debugging without Kubernetes and with a broken network: everything above is host-level** and works
with Kubernetes down or absent. The network-down case degrades: the shell, journal, `systemctl` and
`cgpt` work; `toolbox` and `flatcar-update` do not.

**Support bundles: a documentation gap rather than a capability.** [flatcar/mayday](https://github.com/flatcar/mayday),
described as a "utility for gathering support information", is active (last pushed 2026-07-28,
OBSERVED) and is referenced nowhere in the documentation. Recorded exactly as the Pulse baseline did.

**API access: none.** There is no management API on the node. Whether that is a gap depends entirely
on whether an organization wants one.

---

## 13. Persistent state and storage

**The boundary is drawn at the partition table and it is unusually generous to state.** Partition 9,
`ROOT`, holds everything writable and is never touched by the update process. Persistence across
reboot: everything. Across upgrade: everything, including container images, Kubernetes state, etcd
data and application data. Across rollback: everything, which as §5 notes is a guarantee and a hazard
in the same sentence. Across reset: UNKNOWN, since no reset mechanism is documented. DOCUMENTED, disk
partitions.

**The full partition layout**, since it is the substrate for this dimension and §1, §2 and §4:

| # | Label | Filesystem | Purpose |
|---|---|---|---|
| 1 | EFI-SYSTEM | FAT32 | Bootloader, and the `flatcar/first_boot` marker |
| 2 | BIOS-BOOT | GRUB core.img | "the second stages of GRUB for use when booting from BIOS" |
| 3 | USR-A | ext2 | One half of the A/B pair, mounted read-only at `/usr` under dm-verity |
| 4 | USR-B | (empty on first boot) | The other half |
| 5 | ROOT-C | none | "reserved for future use" |
| 6 | OEM | btrfs | "Stores configuration data specific to an OEM platform" |
| 7 | OEM-CONFIG | OEM-defined | Optional OEM storage |
| 8 | (unused) | none | "reserved for future use" |
| 9 | ROOT | ext4, btrfs or xfs | Persistent data |

DOCUMENTED,
[disk partitions](https://www.flatcar.org/docs/latest/devguide/sdk-disk-partitions/). That page states
the OEM partition is "mounted at `/usr/share/oem`", while the learning series refers to `/oem`. A
minor documentation inconsistency, recorded rather than resolved.

**Growth.** "Flatcar Container Linux will fix the partition table and resize the root partition to
fill the disk on the next boot", so enlarging the underlying volume is the whole procedure on QEMU,
VMware, VirtualBox and EC2. DOCUMENTED,
[adding disk space](https://www.flatcar.org/docs/latest/os-config/storage/adding-disk-space/).

**Additional disks.** Ignition formats, systemd mount units mount. The documentation insists on stable
identifiers, "a distinct stable identifier such as `/dev/disk/by-label/X` or
`/dev/disk/by-partlabel/X`", because device names change across reboots, and it warns that "some cloud
providers treat certain disks as ephemeral and you will lose all Docker images contained on that
disk". Mounting a dedicated volume at `/var/lib/docker` is the documented pattern. NFS is documented
as a mount target. DOCUMENTED,
[mounting storage](https://www.flatcar.org/docs/latest/os-config/storage/mounting-storage/).

**RAID, LVM, iSCSI, swap** all have their own pages. RAID arrays are built by `storage.raid` in a
Butane config; root-on-RAID requires the type GUID `be9067b9-ea49-4f15-b4f6-f36f8c9e1818` and
components must be GPT partitions rather than whole disks. The stated limits are firm: "Other system
partitions, such as `USR-A`, `USR-B`, `OEM`, and `EFI-SYSTEM`, cannot be placed on a software RAID
array", and "`/etc/mdadm.conf` cannot be used to configure a RAID array containing the root
filesystem". DOCUMENTED, [RAID](https://www.flatcar.org/docs/latest/os-config/storage/raid/),
[LVM](https://www.flatcar.org/docs/latest/os-config/storage/lvm/),
[iSCSI](https://www.flatcar.org/docs/latest/os-config/storage/iscsi/).

**ZFS is available and labelled experimental for a structural reason worth quoting:** "Support for ZFS
is experimental because the ZFS kernel module lives out-of-tree which means it is not part of the
upstream Linux kernel", with the consequence that a Flatcar release may ship without ZFS until
compatibility is restored. It arrives as a sysext (7.11 MiB, OBSERVED), enabled through
`/etc/flatcar/enabled-sysext.conf`, first published in 3913.0.0. DOCUMENTED,
[ZFS](https://www.flatcar.org/docs/latest/os-config/storage/zfs/). Root-on-ZFS is UNKNOWN.

**Btrfs** is supported on the root partition and has its own troubleshooting page, but note the
interaction with §9: SELinux enforcement "is currently incompatible with Btrfs volumes". DOCUMENTED.

**Encryption**: LUKS, opt-in, §9. **CSI assumptions**: none at the OS level; a CSI driver is a
Kubernetes concern and Flatcar makes no claims about it. **Disk full**: see §21.

---

## 14. Networking

**systemd-networkd, with per-platform defaults.** Configuration is `.network` and `.link` units,
delivered either by Butane, where "Network units injected via a Butane Config will be written to the
system before networkd is started", or written manually, where "Files placed manually on the
filesystem will need to reload networkd afterwards with `sudo systemctl restart systemd-networkd`".
DOCUMENTED,
[networkd](https://www.flatcar.org/docs/latest/os-config/network/network-config-with-networkd/).

**DHCP and static addressing** are both documented, with a fallback-DHCP pattern matching `Name=en*`
and a static example using `[Match]` plus `Address=`, `Gateway=` and `DNS=`. DOCUMENTED, same page.

**Bonding, VLANs, bridges and multiple NICs are not covered on that page.** They are standard
systemd-networkd features and a `.netdev` unit delivered by Butane is the obvious route, but this
profile will not label a capability DOCUMENTED on the strength of what systemd can do in general. The
Flatcar-specific guidance is absent. UNKNOWN, meaning undocumented rather than unsupported. For an
edge, telco or industrial evaluator this is a real documentation gap, because those are exactly the
topologies that matter there.

**Pre-Kubernetes networking**: Ignition can configure the network before it fetches remote
configuration, via kernel command-line arguments and an Ignition network-configuration page.
DOCUMENTED,
[Ignition network configuration](https://www.flatcar.org/docs/latest/fb-provision/ignition/network-configuration/).

**DNS** has its own page, and `systemd-resolved` is the mechanism. DOCUMENTED,
[configuring DNS](https://www.flatcar.org/docs/latest/os-config/network/configuring-dns/).

**Corporate CAs and proxies.** CAs: `/etc/ssl/certs` plus `update-ca-certificates` (§3). Proxies:
environment variables via systemd drop-ins are documented generically on the environment-variables
page. DOCUMENTED,
[environment variables](https://www.flatcar.org/docs/latest/os-config/host-config/environment-variables/).

**WireGuard, SR-IOV, RDMA, Wi-Fi, cellular, IPv6 specifics**: no Flatcar-specific documentation found.
UNKNOWN. The published kernel config is the honest way to answer any of these precisely for a given
release, and this profile did not enumerate it.

**Remote network reconfiguration**: an ordinary systemd-networkd change over SSH, with the usual risk
of locking yourself out, and no Flatcar-specific safety net documented. INFERRED from the mechanism;
no page addresses it.

**A network-adjacent item worth noting because it is unusual**: OverlayBD artifact streaming has its
own page and ships as a sysext (39.95 MiB, OBSERVED), which is a container-image-delivery optimization
relevant to bandwidth-constrained fleets. DOCUMENTED,
[OverlayBD](https://www.flatcar.org/docs/latest/os-config/network/overlaybd-artifact-streaming/).

---

## 15. Supply-chain ownership and reproducibility

**"Could an organization independently recreate and operate what it is running?" For Flatcar the
documented answer is yes, and that is unusual enough in this study to be the headline.**

**Source availability**: complete. The OS build system (`flatcar/scripts`, including both Portage
overlays), the update client (`flatcar/update_engine`), the initramfs (`flatcar/bootengine`), the
reboot manager (`flatcar/locksmith`), the update server (`flatcar/nebraska`), the Kubernetes operator
(`flatcar/flatcar-linux-update-operator`), the test harness (`flatcar/mantle`) and the extension
builder (`flatcar/sysext-bakery`) are all public. Sixty repositories in the organization, with daily
pushes across the active ones. OBSERVED, `gh api orgs/flatcar/repos`.

**Build tooling**: published as container images on `ghcr.io` (`flatcar-sdk-all`, plus per-arch), with
documented standalone and integrated modes, and `ci-automation/` script stubs "for gluing Flatcar
Container Linux builds to a continuous integration system". An operator can also bootstrap a new SDK
from a seed tarball with `./bootstrap_sdk_container`, which means the toolchain itself is not a
permanent dependency on the project's binaries. DOCUMENTED, scripts README.

**Public CI**: builds run on the project's own infrastructure (a dedicated machine in an Equinix Metal
data center, VPN-only), with Jenkins configuration in `flatcar/jenkins-os`. So the *tooling* is public
and the *build service* is not, which is a normal and honestly described arrangement.

**Reproducible builds**: claimed, with the volatile-metadata caveat quoted in §9. Whether an
independent rebuild matches an official image modulo that caveat has not been demonstrated by anyone
here. NOT TESTED.

**Dependency pinning**: the release tag in `flatcar/scripts` pins the entire Portage tree, which is
vendored in-repo rather than fetched from a moving Gentoo. That is strong pinning by construction.
DOCUMENTED, scripts README.

**Signing**: image key (GPG 4096-bit RSA, one-year lifetime, split-secret renewal, maintainer-only
access) and update payload key (`update-payload-key.key.pem`, used by `delta_generator`). An official
build asserts its own key provenance: the build library refuses to produce an official image unless
the key package carries the right flag, via
`grep -q official "${root_fs_dir}"/var/db/pkg/coreos-base/coreos-au-key-*/USE || die_notrace`.
DOCUMENTED (source), `prod_image_util.sh`. A self-built image therefore carries a *different* update
key by default, which is the mechanism by which operator-owned updates become possible and also the
mechanism by which an operator's fleet stops trusting official payloads. That tradeoff is inherent and
is picked up in §22.

**SBOM and provenance**: per release, in the artifact listing and inside the image at
`/usr/share/SLSA/`. SLSA Level 3 claimed with four named gaps (§9). DOCUMENTED.

**Public artifacts, mirroring, private registries, self-hosted update infrastructure**: all supported,
covered in §2, §10 and §11.

**Key rotation and revocation**: the image key has a stated one-year lifetime and a split-secret
renewal procedure. Revocation, and what a node does if a key it has is revoked, is UNKNOWN. Whether an
operator can pin or replace the update payload public key on an existing fleet without rebuilding the
image is UNKNOWN; the key is a file at a fixed path inside read-only `/usr`, and `flatcar-postinst`
checks its md5 to recognise the official key, which suggests replacing it means rebuilding. INFERRED
from the mechanism, not stated.

**"If Microsoft and all its hosted services disappeared tomorrow, what would remain?"** Answered in
§22, because the answer is structural rather than a single sentence. The short version: the code, the
build system, the update server, the signing procedure and the foundation-held assets would all
remain; the project's build machine, its release servers and its signing keys would not.

---

## 16. Governance and ownership

Recording facts, and keeping the framework's four properties separate, because Flatcar is a case where
they genuinely diverge.

**Licence**: Apache-2.0 on the project repository. Polyglot by component: `update_engine` BSD-3-Clause,
`bootengine` BSD-2-Clause, inherited from CoreOS. DOCUMENTED, [flatcar.org/license](https://www.flatcar.org/license/).

**Foundation and asset ownership**: CNCF Incubating since 2024-08-02 (verified, see the provenance
block). The site states Flatcar is "a Series of LF Projects, LLC", which places the trademark and
project assets with LF Projects. No published trademark assignment document naming the transferring
party was found. UNKNOWN on that last point, as the Pulse baseline also recorded.

**GitHub organization**: `flatcar`, 60 repositories. OBSERVED.

**Governance documents**: [`governance.md`](https://github.com/flatcar/Flatcar/blob/main/governance.md),
[`MAINTAINERS.md`](https://github.com/flatcar/Flatcar/blob/main/MAINTAINERS.md),
[`SECURITY.md`](https://github.com/flatcar/Flatcar/blob/main/SECURITY.md),
[`CONTRIBUTING.md`](https://github.com/flatcar/Flatcar/blob/main/CONTRIBUTING.md) and an
`ONBOARDING.md`, all present on `main`. OBSERVED, `gh api`.

**Governance content**: a Maintainer Council is "the governing body for the project". Lazy consensus,
simple majority for most votes, two-thirds for charter changes and maintainer removal. Nomination by
an existing maintainer via pull request on consensus. Removal paths include inactivity of a year or
more. An emeritus list exists. The document states "Community over Product or Company" and that "Each
contributor participates in the project as an individual". Public developer syncs every fourth
Wednesday. DOCUMENTED.

**Maintainer structure, with a detail the Pulse baseline did not have.** Sixteen maintainers and a
seven-member security team, and additionally five named maintainer subgroups, "enforced via GitHub
teams and `CODEOWNERS` files in each repository": `nebraska-maintainers`, `flatcar-integrations`,
`flatcar-communication`, `flatcar-ci` and `flatcar-infra`, each listing its members and its
repositories. Repositories not covered get `@flatcar/flatcar-maintainers`. This is a more developed
review structure than a flat maintainer list, and it is machine-enforced. DOCUMENTED, `MAINTAINERS.md`
as of 2026-09-16.

**Infrastructure and signing-key control.** The build machine is the project's, in an access-controlled
Equinix Metal facility. Image signing key access is "restricted to core maintainers" and renewal
"requires split secrets of multiple maintainers", which is a distributed rather than a single-holder
arrangement. The release CDN is `flatcar.cdn.cncf.io`, so the distribution layer is foundation
infrastructure (OBSERVED). Domain and registry control was not investigated. UNKNOWN.

**Commercial sponsorship and history, as dated facts.** Kinvolk started Flatcar in 2018. Microsoft
acquired Kinvolk in 2021. The project was accepted to the CNCF in 2024. Flatcar Container Linux Pro is
a Microsoft Azure Marketplace listing. No speculation about future corporate behaviour is offered
here, per the framework's explicit instruction, and none should be read into the §11 AKS facts either.

**The four properties, kept apart:**

- *Open source*: yes, unambiguously, including the build system.
- *Open governance*: documented in detail, with defined voting thresholds, a council, subgroups and
  public syncs. This is among the more complete governance documents in the study.
- *Vendor-neutral ownership*: yes. Assets sit with LF Projects and distribution runs on CNCF
  infrastructure.
- *Diverse contribution*: this is the one that does not follow from the other three. The project's own
  monthly contribution report for 2026-06-22 to 2026-07-21 counted 15 contributors and 8,579
  contributions across 45 repositories, with 26.67% new contributors. All-time commit counts on
  `flatcar/scripts` are heavily concentrated: `krnowak` 4319, `marineam` 3256, `dm0-` 2349,
  `crawford` 1142, `dongsupark` 974, `tormath1` 951, `pothos` 905 (OBSERVED, `gh api
  repos/flatcar/scripts/contributors`). The second, third and fourth of those are CoreOS-era
  contributors, so the live concentration is tighter still. `MAINTAINERS.md` records no employer
  affiliation for any maintainer, so organizational spread cannot be derived from project files at
  all. UNKNOWN, and it is a meaningful unknown for anyone assessing single-employer risk.

**"Could another organization continue development?"** Structurally yes: the licence permits it, the
build system is public and runnable, the update server is open source, and the assets are
foundation-held. The practical obstacle is the small core, not the legal or technical arrangement.
That distinction is exactly what the framework asks these four properties to keep separate.

---

## 17. Project health and sustainability

All figures OBSERVED on 2026-09-16 via `gh api`, with the query named, unless marked otherwise.

**Release cadence**: "Within each channel, updates are planned on a 14-day cadence"; a new major alpha
monthly, alpha to beta every two months, beta to stable every three to four months, a new LTS yearly.
DOCUMENTED, [RELEASES.md](https://github.com/flatcar/Flatcar/blob/main/RELEASES.md). Observed
behaviour matches for three of four channels: stable, beta and alpha all published 2026-09-14, and the
previous set on 2026-08-13, which is a 32-day gap rather than 14. LTS last published 2026-08-13. The
14-day figure is a plan; the observed interval between the last two release events on `flatcar/scripts`
is a month.

**Release history**: continuous since 2018. Eight years.

**Contributors and concentration**: see §16. Fifteen active contributors in the most recent monthly
report window; commit history dominated by a handful of people, several of whom predate Flatcar.

**Bus factor**: not computed here, and the honest statement is that it looks small at the code level
and is mitigated at the governance level (16 maintainers, 5 subgroups with CODEOWNERS enforcement, a
7-person security team, documented removal and emeritus paths). Those are different mitigations for
different failure modes and neither substitutes for the other.

**Commit activity**: `flatcar/scripts` weekly commit counts for the last eight weeks were
`[11, 189, 39, 27, 150, 33, 136, 17]` (`gh api repos/flatcar/scripts/stats/participation`). Bursty,
which is what a release-train repository looks like, and never idle.

**Issue response and PR velocity**: on `flatcar/Flatcar`, 158 issues opened and 138 closed in the 90
days to 2026-09-16, against 482 open issues total. On `flatcar/scripts`, 50 open pull requests and 112
merged in the same 90 days. Closing roughly as many issues as arrive, and merging pull requests at
better than one a day, is a working project rather than a maintained-only one. (`gh api search/issues`
with explicit date bounds.)

**Security response**: a named seven-person security team with, per the Pulse baseline, fortnightly
meetings, a rotating primary and secondary, and a daily advisory runbook. An active
`flatcar/security-triage` repository. Response *times* were NOT TESTED.

**External health signal**: an OpenSSF Best Practices badge at the passing level, 100%, with all six
criteria categories full (Basics 13/13, Change Control 9/9, Reporting 8/8, Quality 13/13, Security
16/16, Analysis 8/8). DOCUMENTED, [bestpractices.dev/projects/10926](https://www.bestpractices.dev/projects/10926).
This is a self-assessment against a published rubric rather than an audit, and should be read as such,
but it is a stronger signal than stars, which per the framework are not used here at all.

**Funding**: not publicly broken out. UNKNOWN. Commercial backing exists in the form of the primary
sponsor and the Pro listing; CNCF membership dues and infrastructure credits are not itemized per
project.

**Adoption**: not verifiably measured here. The number of officially supported clouds and the
existence of a commercially supported derivative are indirect signals, not measurements. UNKNOWN.

---

## 18. Operational lifecycle and support horizon

**Required upgrade frequency is high on the non-LTS channels.** A stable node following the default
configuration updates automatically and reboots within five minutes, on a channel intended to move
every 14 days. An organization that wants a slower clock must either use LTS, pin with
`flatcar-update --disable-afterwards`, set `SERVER=disabled`, or run its own Nebraska and control the
rollout. All four are documented and supported, which is better than the alternative of fighting the
mechanism. DOCUMENTED.

**Supported releases**: four channels. Alpha, beta and stable move forward continuously; each is
supported only at its current version. The LTS stream is where the long horizon is supposed to live:
"LTS release streams will be maintained for an extended lifetime of 18 months. The yearly LTS streams
have an overlap of 6 months." DOCUMENTED, [releases page](https://www.flatcar.org/releases).

**The LTS channel does not currently reconcile with its own published policy, and this is the least
legible part of the project.** The releases page announces that "The LTS-2024 channel (major release
series 4081) will continue supporting CGroupsV1. This channel will receive regular updates until early
2026, and hit EOL in mid-2026." The lts channel served 4081.3.10 on 2026-08-13, after that stated EOL,
and no LTS-2025 or LTS-2026 stream appears as a channel. An issue titled "Is LTS channel dead?",
[flatcar/Flatcar#2040](https://github.com/flatcar/Flatcar/issues/2040), opened 2026-03-16, is still
open; a maintainer replied "LTS is not dead and seems like it got missed in the last couple releases.
We will try push LTS more often", and a later comment in June 2026 asked for "a single source of truth
of what release channels are currently available" and for the complete list of valid `GROUP` values,
noting that lts-2023 and lts-2024 appear active while lts-2025 and lts-2026 are missing. No answer is
posted. DOCUMENTED and OBSERVED (issue state checked 2026-09-16). For an organization choosing Flatcar
specifically for an 18-month support window, this is the thing to raise with maintainers before
committing.

**Skipped upgrades**: not addressed by any page found. The A/B mechanism applies a full payload rather
than a delta by default, which suggests jumping many versions is mechanically fine, but the migration
work inside `flatcar-postinst` between distant versions is exactly where a version-skip problem would
live. UNKNOWN.

**Downgrade**: one step back by slot switch; arbitrary versions by `flatcar-update --to-version`, with
the documentation recommending against it. "There is no method to downgrade to an arbitrary version
number" refers to the automatic mechanism. DOCUMENTED, §5.

**Kubernetes compatibility**: not the OS's concern, and therefore not the OS's promise (§7). An
adopter owns the compatibility matrix.

**Kernel cadence**: tracks the channel. Published per release as a kernel config artifact. The LTS-2024
note about cgroups v1 shows the project does use LTS streams to hold a compatibility line.

**CVE cadence**: releases carry security fixes on the channel cadence; a security team and a triage
repository exist. Per-CVE latency NOT TESTED.

**Old artifacts and indefinite version pinning**: old versions remain fetchable from the release
servers by version path (the Omaha response's `codebase` is a version-scoped URL, OBSERVED), and
`flatcar-update -V` plus `flatcar-install -V` both take explicit versions. Combined with a self-hosted
Nebraska and a local mirror, indefinite pinning is achievable. Whether the project guarantees old
artifacts stay available is UNKNOWN, and for an operator who cares, mirroring is the answer that does
not depend on the guarantee.

**Enterprise support**: Flatcar Container Linux Pro on Azure Marketplace. No support vendors or tiers
are named on flatcar.org itself. DOCUMENTED and UNKNOWN respectively.

**Multi-year operational burden, assessed.** The recurring costs are: track a fast channel or accept
the LTS ambiguity above; rebuild any dynamically linked sysext on every OS bump (§3); own the
Kubernetes compatibility matrix (§7); and manage drift on a writable root that nothing reconciles
(§1). The recurring savings are: upgrades never threaten machine state, rollback is local and
automatic, and every debugging skill an existing Linux team has keeps working.

---

## 19. Resource footprint and performance

The framework asks for measurement where it is useful. This pass measured what can be measured
without booting anything, and says so where it could not.

**Artifact sizes (OBSERVED, stable 4757.2.0, amd64, 2026-09-16):**

| Artifact | Size |
|---|---|
| Raw QEMU disk image | 569.2 MiB |
| Generic image, bzip2 | 557.4 MiB |
| Live ISO | 477.0 MiB (500,170,752 bytes) |
| PXE initramfs | 440.3 MiB (461,650,500 bytes) |
| Kernel (`vmlinuz`) | 33.5 MiB |
| Update payload advertised by the public Omaha service | 540,489,428 bytes |
| Per-release SBOM | 15.5 MiB |
| ZFS sysext | 7.11 MiB |
| NVIDIA 570 sysext | 483.0 MiB |
| Developer container | 574.4 MiB |

**Upgrade download size is effectively the full payload.** 540 MB per node per update, against a
14-day planned cadence, is a real number for a large or bandwidth-constrained fleet, and it is the
main argument for a local Nebraska with `-host-flatcar-packages` even where internet access exists.
Whether `delta_generator` deltas are used in production between adjacent versions is UNKNOWN; the
observed Omaha response advertised a full payload, and the client sent `delta_okay="false"` in the
probe, so this measurement does not settle it.

**Disk footprint**: the installer requires "at least 8GB of usable space", and the root partition
auto-grows to fill the disk at first boot. DOCUMENTED.

**Memory**: PXE requires "A minimum of 3 GB of RAM" because it runs entirely from RAM. The shipped
QEMU wrapper defaults to `VM_MEMORY='2048'` and `VM_NCPUS="$(getconf _NPROCESSORS_ONLN)"`, which is
the project's own idea of a reasonable development VM. DOCUMENTED and OBSERVED (from
`flatcar_production_qemu.sh`, 343 lines, downloaded 2026-09-16). **Idle memory and idle CPU of a
running node: NOT TESTED.** No documented figure was found either. UNKNOWN.

**Boot time, upgrade duration, reboot duration: NOT TESTED and UNKNOWN.** The only time constant the
documentation gives is the roughly two minutes after boot before `update_engine` marks a version
successful, which bounds how long an automatic rollback takes to trigger but is not a boot-time
measurement.

**Network consumption at idle**: an Omaha check about 10 minutes after boot and roughly hourly after
that, each a small XML POST. Negligible. DOCUMENTED.

**No ranking is offered.** These figures are useful for capacity planning and for the air-gap
argument. Comparing a 569 MiB Flatcar image against another project's image without normalizing for
what is inside it would be the kind of trivial-difference ranking the framework warns against.

---

## 20. Extensibility versus constraint

**Flatcar sits nearer the construction-kit end than any other vendor-released, channel-published
distribution in this study, and it gets there by a different route than a build-it-yourself system.**

**Decisions the project makes for the operator**: the base userspace (Gentoo-derived, no package
manager), the partition layout, the A/B scope (`/usr` only), the update protocol (Omaha), the
first-boot configuration format (Ignition), the init system, the integrity mechanism (dm-verity on
`/usr`), the release channels and their cadence, and which extensions are official.

**Which of those can be overridden, and at what cost:**

| Decision | Override | Cost |
|---|---|---|
| Base userspace contents | SDK rebuild | Own an 8 GB build environment and a release pipeline |
| Kernel and its config | SDK rebuild | Same |
| Contents of `/usr` at runtime | sysext | Low, with the `VERSION_ID` rebuild treadmill (§3) |
| Update source | `SERVER=` a self-hosted Nebraska | Low, documented |
| Update policy and timing | `update.conf`, reboot windows, FLUO, kured | Low, documented |
| Channel and version | `GROUP=`, `flatcar-update -V` | Low, documented |
| Orchestrator | Install whatever you like | Low, and you own the matrix |
| Partition layout | Ignition at first boot, within the fixed system partitions | Medium; USR, OEM and EFI are fixed |
| A/B scope | Not overridable | Architectural |
| Ignition-once semantics | Not overridable | Architectural |

**Can unsupported states be created? Easily.** Running FLUO and `locksmithd` together is a documented
conflict. A `VERSION_ID`-pinned sysext plus auto-updates silently stops loading the extension after an
upgrade. SELinux enforcing plus Btrfs is documented as incompatible. Full TPM PCR binding plus
auto-updates is documented as unreliable. Every one of these is an operator-reachable combination that
the documentation warns about rather than prevents. That is the cost of the flexibility, and it is a
fair one to name.

**Does customization weaken guarantees?** Specifically, yes, in one place worth stating: an SDK-built
image is signed with the operator's keys, not the project's, and `prod_image_util.sh` enforces that an
official build must carry the official update key. So the moment an organization builds its own
Flatcar, it becomes its own root of trust for updates. That is the point of the exercise and it is
also a transfer of responsibility that should be a deliberate decision, not a side effect.

**Does flexibility increase testing responsibility?** Yes, and measurably: every sysext, every kernel
module, every Kubernetes pairing and every SDK change is untested by the project's CI. The project
ships a test harness (`kola`) that an operator can run, which is a meaningful partial answer and is
picked up in the experiment section.

**Can existing enterprise standards be incorporated, or must the organization adopt Flatcar's?**
Mostly incorporated. Corporate CAs, SSSD, custom sshd configuration, SELinux policy, FIPS-compliant
configuration, existing monitoring and security agents (as sysexts), existing configuration management
over SSH, and existing PXE infrastructure all fit. What the organization must adopt is Ignition for
first boot, a `/usr` that cannot be modified in place, and a build pipeline if it needs anything in
that `/usr`. Compared with a Kubernetes appliance, that is a short list of impositions.

**On the spectrum**: APPLIANCE <--------[Flatcar]--> CONSTRUCTION KIT, closer to the kit, with the
qualifier that the kit is a Gentoo build system and picking it up is a commitment rather than a
weekend.

---

## 21. Failure experiments

**Tier scope, stated first.** The ten destructive experiments the framework lists were NOT RUN. That
is the scope decision recorded on the platform-profile task
before the work started: no experiment-report template is ratified, and the four infrastructure
decisions on the research epic are open. Every
scenario below is therefore **NOT TESTED / OUT OF TIER SCOPE** for observed behaviour. What is
recorded is what the documentation and the source say the *expected* behaviour is, labelled DOCUMENTED
where a primary source says it explicitly and INFERRED where this profile reasons from documented
mechanics. The framework's central question, "what does the machine do next?", is answered as far as
documentation can answer it and no further.

**1. Cut power during OS update.** Expected: the active `/usr` slot and the writable root are
untouched during staging, and the GPT priority flip is the final step, so the machine should reboot
into the unchanged active slot with a partially written inactive slot that is later overwritten by the
next download. INFERRED, from the DOCUMENTED staging mechanics in §4. No page states it. This is the
single most valuable experiment on the list because it is the one place in the upgrade path where the
profile has to infer.

**2. Supply a corrupted new OS image.** Expected: rejected before installation. "Before installation,
update images are validated against the update signing key" and "An update is installed only after
successful validation". A payload that fails signature validation should never reach the inactive
slot. DOCUMENTED, supply chain page. What the client does *next* (retry, back off, report to the
update server, log what) is not documented. UNKNOWN.

**3. Introduce a kernel that cannot boot.** Expected: GRUB decrements `tries` on the new slot, the
boot fails, and on the following attempt `tries` reaches zero and GRUB falls back to the retained
slot, without operator action or network. DOCUMENTED, learning series and manual rollbacks. Two
sub-cases the documentation does not separate and an experiment would have to: a kernel that panics
immediately, versus a kernel that boots far enough that `update_engine` runs but a critical service
fails. The learning series describes the second case explicitly, including a deliberate reboot to
trigger the rollback. The first is UNKNOWN in detail, specifically how many attempts are consumed.

**4. Break Kubernetes after OS upgrade.** Expected: nothing. The boot-success criterion is
OS-level and time-based, so a node whose kubelet never becomes ready still marks the new `/usr`
successful and keeps it. DOCUMENTED by implication of the criterion in §4; the documentation does not
address this scenario directly, so the *consequence* is INFERRED. FLUO's drain-before-reboot reduces
the blast radius but does not gate on post-reboot health either, as far as its README states. This is
a real architectural gap and it is shared with most A/B systems in the study.

**5. Corrupt persistent configuration.** Expected: no OS mechanism helps. `/etc` is on the writable
root, is not covered by dm-verity, is not reverted by rollback, and is not re-applied by Ignition,
which runs once. Recovery is manual: the live ISO, or a shell, or reinstall. DOCUMENTED, from §1, §5
and §6 together. This is the scenario where Flatcar's design is weakest and it follows directly from
the `/usr`-only A/B scope.

**6. Remove network during upgrade.** Expected: the download fails and `update_engine` retries on its
polling schedule; the machine is unaffected because the active slot was never touched. INFERRED from
the polling behaviour and the staging mechanics. Retry and back-off behaviour is not documented.
UNKNOWN.

**7. Make the image registry unavailable.** Two distinct cases for Flatcar, and conflating them would
be an error. The *update service* being unavailable means no updates and no other effect; the node
continues on its current version indefinitely, and `SERVER=disabled` is the documented way to make
this the permanent, intended state. DOCUMENTED. The *container registry* being unavailable is a
container-runtime matter with no OS-level consequence, except for `toolbox`, which needs to pull an
image and therefore stops working for debugging (§12). DOCUMENTED by implication.

**8. Fill the disk.** UNKNOWN, and deliberately so. No documentation page addresses a full root
partition. The interesting question is specific: an update stages into the inactive USR partition,
which is a fixed-size system partition rather than part of the writable root, so a full `/var` should
not block an OS update. That would be INFERRED from the partition layout, and it is exactly the kind
of plausible inference that an experiment exists to check. What a full root does to `update_engine`'s
bookkeeping, to `locksmithd`, and to the post-install step is not documented at all.

**9. Damage boot configuration.** Partly answerable. Damage to the GPT attributes is recoverable
offline with `cgpt prioritize` and `cgpt add -T`, which is precisely the documented manual-rollback
procedure (DOCUMENTED). Damage to the single EFI system partition, which is shared rather than
duplicated per slot, has no documented recovery path and no A/B protection. UNKNOWN, and it is the
structural weak point of Flatcar's layout relative to Bottlerocket's per-set boot partitions.

**10. Remove the management plane.** Expected: no effect on the machine. There is no management plane
in the required path. Nebraska's absence means no update checks succeed; `locksmithd`'s etcd lock is
only consulted if `etcd-lock` is the configured strategy, and its absence would block reboots under
that strategy specifically. Boot, run, local rollback and local debugging are all independent of any
central service. DOCUMENTED, from §4, §5 and §11.

**What Flatcar already provides toward running these properly.** `flatcar/mantle` ships `kola`, a test
framework that launches instances and runs tests, whose default platform is QEMU, and which already
has a `kola/tests/update/` suite and a `kola/tests/misc/omaha.go`. An experiment pass would not start
from zero. DOCUMENTED, [mantle README](https://github.com/flatcar/mantle) and OBSERVED, `gh api
repos/flatcar/mantle/contents/kola/tests`.

---

## 22. Operational independence experiment

**Tier scope**: the end-to-end independence run was NOT RUN. What follows is the documented and
source-supported answer for each of the nine stages, with the dependency on Flatcar-controlled
infrastructure named at each one. Flatcar is a genuinely interesting case here precisely because the
answer is not uniform, and because CNCF hosting changes what "the project's infrastructure" even means.

**BUILD.** Fully operator-controlled, documented, and the strongest stage. The SDK is a public
container image on `ghcr.io`, the build system and both Portage overlays are in `flatcar/scripts`, and
`./bootstrap_sdk_container` can produce a new SDK from a seed, so even the toolchain is not a
permanent dependency. Dependency on project infrastructure: the SDK image is hosted on GitHub Container
Registry, and a from-scratch bootstrap needs a seed tarball. Both are mirrorable. DOCUMENTED, scripts
README. Whether a third-party build reproduces an official image: NOT TESTED, and the project's own
reproducibility claim carries the volatile-metadata caveat (§15).

**SIGN.** Fully operator-controlled, with a consequence. An operator's build signs with the operator's
keys; the build library explicitly refuses to mark a build official unless the official update key
package is present. So operator-owned signing is not merely possible, it is the default for anyone who
builds. The consequence is that the operator's fleet then trusts the operator's key and, unless the
image ships both, no longer trusts official payloads. DOCUMENTED (source),
`build_library/prod_image_util.sh`. What is UNKNOWN is whether a supported path exists to trust both
keys, or to rotate a fleet from one to the other without reinstalling.

**HOST.** Fully operator-controlled and documented on two levels. Images: any HTTP server, with
`flatcar-install -b BASEURL`. Update payloads: Nebraska with `-host-flatcar-packages=true`, documented
for "an isolated environment without internet access (e.g air-gapped environment)". Worth recording
about the project's own hosting: both `stable.release.flatcar-linux.net` and
`update.release.flatcar-linux.net` redirect to `flatcar.cdn.cncf.io`, so the default hosting of record
is foundation infrastructure rather than a sponsor's. OBSERVED, 2026-09-16.

**INSTALL.** Fully operator-controlled. `flatcar-install -f IMAGE -k KEYFILE` installs a local image
verified against an operator-supplied key, with no network. Alternatively ISO, PXE or iPXE from
operator-hosted boot assets. DOCUMENTED.

**BOOT.** No external dependency at any point. GRUB reads GPT attributes from the local disk;
dm-verity validates `/usr` against a hash baked into the local initramfs. DOCUMENTED. The one caveat
is Secure Boot: booting with the project's signed shim on stock firmware would require a shim signed
by the third-party UEFI CA, which does not exist (§9), so an operator wanting Secure Boot enrols keys
itself, which is *more* independent, not less, but is undocumented.

**CONFIGURE.** Fully operator-controlled. Ignition reads from HTTP, HTTPS, S3, TFTP, a cloud user-data
channel, or an embedded OEM-partition config. Nothing routes through a project service. DOCUMENTED.

**UPGRADE.** Fully operator-controlled, and this is the stage where Flatcar's answer is unusually
strong. `SERVER=` points at any Omaha endpoint; Nebraska is the project's own server, open source, and
the public service identifies itself as Nebraska (OBSERVED, §4), so the operator runs the same code
the project runs. Payload verification uses a key inside the image, which is the operator's key on an
operator-built image. DOCUMENTED plus OBSERVED.

**ROLLBACK.** No external dependency for the one-step case: `cgpt prioritize` is local, offline and
documented. The arbitrary-version case needs a reachable update service, which may be the operator's.
DOCUMENTED.

**RECOVER.** Mostly operator-controlled. Live ISO and PXE images are ordinary files an operator can
mirror. `toolbox` needs a container image, so an air-gapped operator must pre-mirror it or lose that
debugging path. No project-hosted service is required to recover a machine. DOCUMENTED, with the
`toolbox` dependency INFERRED from how `toolbox` works rather than stated as an air-gap caveat on the
page.

**"If the primary commercial sponsor and all its hosted services disappeared tomorrow, what would
remain?"** Recording only what is checkable. The licences, the source, the build system and its
vendored Portage tree, the update server, the test harness, the published documentation, and the
trademark and project assets held by LF Projects would remain. The release and update hosting runs on
CNCF infrastructure rather than the sponsor's, per the CDN observation above. What would need
reconstituting is the build machine and its access-controlled environment, the signing keys and the
split-secret renewal procedure around them, and the release engineering capacity of the people who run
it. The first two are procedural and documented enough to rebuild; the third is the contribution
concentration recorded in §16 and is the real question. This is an assessment of documented structure,
not a prediction about anybody's behaviour.

**Applied equally.** The same nine stages should be run against Kairos, where the OCI-registry-native
distribution model makes HOST and UPGRADE look different, and where the equivalent of "the project
refuses to build official images without the official key" may or may not exist. This profile makes no
claim about how Kairos scores; it is named here only to record that the test is symmetrical, per the
framework's bias controls.

---

## What a full experimental pass needs

This section exists because the tier calls for the full build / provision / extend / update / break /
recover cycle and both standardized experiment protocols, and this pass deliberately ran none of it.
Its purpose is to make the missing half a costed decision. The framework's §21 field list (INITIAL
STATE, FAILURE INJECTED, EXPECTED BEHAVIOR, OBSERVED BEHAVIOR, FINAL MACHINE STATE, MANUAL
INTERVENTION REQUIRED, DATA LOST, RECOVERY PROCEDURE, TIME TO RECOVERY) is the right report shape;
nothing has ratified it as the template for this tier.

### Experiments, in rough order of value per unit of effort

1. **Happy-path upgrade on QEMU.** Boot stable, point `SERVER=` at a local Nebraska serving a newer
   version, watch `update_engine` stage into the passive slot, and capture `cgpt show` before and
   after to confirm priority, tries and successful move as documented. Confirm the success marking
   happens at roughly two minutes. This single experiment converts most of §4 from DOCUMENTED to
   REPRODUCED and produces the first real boot-time and upgrade-duration numbers for §19.
2. **Failed-boot automatic rollback.** Stage an update, then break the new slot so it cannot complete
   boot, and confirm the machine returns to the retained slot unattended with no network. Two
   variants worth separating, because §21 scenario 3 shows the documentation only covers one: a kernel
   that panics immediately, and a system that boots but fails a critical unit.
3. **Power cut during staging.** Kill the VM mid-download and confirm the active slot is unchanged and
   bootable. This closes the one INFERRED claim in §4 and is cheap on QEMU.
4. **The `/etc` non-rollback, demonstrated.** Change something in `/etc` that breaks the node, upgrade,
   roll back, and show the breakage survives. This is the most important *architectural* demonstration
   in the whole Flatcar profile, it takes minutes, and it makes §1's consequence concrete rather than
   argued.
5. **Sysext version-pinning treadmill.** Build a `VERSION_ID`-pinned sysext, upgrade the OS, and show
   the extension silently stops loading. Then repeat with `SYSEXT_LEVEL` and a static binary. This
   converts §3's central cost from a documentation quote into a measured operational fact.
6. **Disk full.** Fill the root partition and attempt an update. §21 scenario 8 is the largest
   genuinely open UNKNOWN that a local VM can settle.
7. **The §22 independence run, end to end.** Build an image from the SDK with operator keys, sign it,
   host it and its payload on a local Nebraska, install from local media with `-f` and `-k`, configure
   by Ignition from a local file, upgrade to a second locally built version, roll back, and recover.
   This is the experiment that would let the epic state with evidence what survives without the
   sponsor's infrastructure, and Flatcar is the best candidate in the study for it because every stage
   is documented.
8. **Air gap.** Run the whole of 7 on a host with no route to `flatcar.cdn.cncf.io`, `ghcr.io` or
   `public.update.flatcar-linux.net`, including a pre-mirrored `toolbox` image.
9. **Secure Boot with operator-enrolled keys.** Boot `flatcar_production_qemu_uefi_secure_image.img`
   with the shipped EFI vars, then with operator-enrolled keys. This is the one dimension where the
   documentation is absent entirely, so an experiment would produce the primary source that does not
   exist.
10. **Kubernetes-aware reboot coordination.** FLUO's drain-reboot-uncordon cycle, and the §21 scenario
    4 case of a node that boots cleanly and never becomes Ready. Needs a cluster, so it is the
    expensive one and it is last.

### Infrastructure, and the honest cost of each option

**Option A: local QEMU/KVM, no cloud account. Viable, cheap, and documented by the project itself.**
Flatcar publishes a QEMU wrapper script with every release, and the documented flow is three commands:
download `flatcar_production_qemu_image.img` and `flatcar_production_qemu.sh`, `gpg --verify` the
signature, then `./flatcar_production_qemu.sh -nographic`. Ignition is injected with
`./flatcar_production_qemu.sh -i config.ign -- -nographic`, the script finds SSH keys from `ssh-agent`
or `~/.ssh/`, and access is `ssh -l core -p 2222 localhost`. Defaults are 2048 MB RAM and all host
CPUs. DOCUMENTED, [QEMU](https://www.flatcar.org/docs/latest/deploy/virt-options/qemu/); defaults
OBSERVED from the script. **This is a materially better local story than Bottlerocket's**, because it
needs no build at all to start, uses the *supported production image* rather than a development
variant, and ships from the project as a release artifact. Total cost: about 600 MB of download and a
host with KVM. Experiments 1 to 6 and 9 all fit here.

There is one caveat to settle before relying on it. The QEMU image is a supported production image, so
unlike Bottlerocket's `metal-dev` there is no dev-variant asterisk on results. But a QEMU result is
still a virtual-hardware result, and the epic's decision 2 on
the research epic applies here in a softer form: does
a QEMU observation count as REPRODUCED for bare metal? For Flatcar the honest answer is that it counts
for everything except firmware, Secure Boot and TPM behaviour, which is where experiment 9 would need
real hardware or careful OVMF setup.

**Option B: a local Nebraska.** Needed for experiments 1, 7 and 8 and it is cheap: a container plus
PostgreSQL, with `-host-flatcar-packages=true` to serve payloads. This is the piece that makes the
independence run possible without any cloud account at all, and it has no equivalent in the
hyperscaler profiles.

**Option C: the SDK build host.** Needed for experiments 5, 7 and 8. Cost: an 8 GB SDK container
image (3 GB compressed), privileged Docker with `/dev` bind-mounted, and a full `build_packages` run
whose duration is UNKNOWN because the documentation states no figure. This is the largest unpriced item
in the plan, and it is the Flatcar-specific addition to the epic's decision 4: the privileged-Docker
requirement is a sandbox question on the test host, not only a disk-and-time question.

**Option D: a cloud account.** Needed only for provider-specific provisioning behaviour (IMDS-delivered
Ignition, per-provider OEM sysexts, cloud serial console recovery). Unlike Bottlerocket, Flatcar's
*core* lifecycle is fully exercisable without one, so decision 3 on the epic is much less load-bearing
for this profile than for the hyperscaler ones.

**Option E: `kola`.** Worth evaluating before writing any bespoke harness. `flatcar/mantle` already
provides instance launching, a QEMU default platform, and existing `kola/tests/update` and
`kola/tests/misc/omaha.go` suites. Using the project's own harness would make results easier for
maintainers to check during a factual-correction pass, which the framework asks for. Effort to adopt:
UNKNOWN.

### The decisions that block the experiment pass

All four are already recorded on the research epic,
raised from the platform-profile task, and are not re-derived
here: (1) ratify an experiment-report template for this tier; (2) decide whether a local-QEMU or
dev-variant result counts as REPRODUCED or only as evidence about the mechanism; (3) decide whether
real cloud infrastructure is in scope and with what budget cap; (4) decide build-host allocation for
multi-hour, tens-of-GB builds.

**What Flatcar adds to each, specifically:**

- To (1): nothing new. The §21 field list fits Flatcar's scenarios without modification.
- To (2): Flatcar softens the decision in one way and sharpens it in another. It softens it because
  the QEMU image is a *supported production image*, not a development variant, so the dev-variant
  objection does not apply. It sharpens it because Secure Boot, TPM and PCR behaviour are exactly the
  things QEMU models imperfectly, and they are exactly the things Flatcar's documentation is weakest
  on, so the one dimension most in need of an experiment is the one least served by the cheap option.
- To (3): Flatcar makes it much less urgent. A near-complete lifecycle and both §21 and §22 protocols
  are runnable with no cloud account at all. If the epic wants one system to prove the independence
  protocol end to end on a zero-budget setup, this is the one.
- To (4): Flatcar adds a new constraint rather than a bigger number. The SDK needs **privileged Docker
  with `/dev` bind-mounted** to build images, because it uses loop devices. On the test host that is a
  sandbox and permissions question before it is a disk-space question, and it should be answered
  before anyone schedules experiment 7.

---

## Follow-up research

Open questions this study surfaced. The Pulse baseline's twelve open questions stand and are not
repeated; these are additional or sharpened, and several are good candidates for a maintainer
factual-correction pass.

1. **What does an OS update do to the shim and GRUB on the single EFI system partition?** It sits
   outside the A/B pair. Can an update change the boot chain, and what protects that step? (§4, §21
   scenario 9.)
2. **Is the full payload always downloaded, or are deltas used between adjacent stable releases?** The
   observed Omaha exchange advertised a full 540 MB payload, but the probe sent `delta_okay="false"`.
   This determines the real fleet bandwidth cost. (§19.)
3. **Why does the main OS payload carry only a legacy base64 `hash` in the Omaha response while OEM
   packages carry `hash_sha256` as well?** (§2.)
4. **Can an operator trust both the official update key and a self-built one, and can the update
   payload key be rotated on an existing fleet without reinstalling?** The key is a file inside
   read-only `/usr` and `flatcar-postinst` checks its md5. (§15, §22 SIGN.)
5. **What is the current state of the shim-review submission, and what exactly must an operator enrol
   to use Secure Boot on stock firmware today?** Related: why does no Secure Boot page exist when the
   stable channel publishes signed shim, GRUB, kernel and a Secure Boot QEMU image? (§9.)
6. **Can a third party sign sysext kernel modules for Secure Boot nodes**, given the ephemeral
   per-release signing certificate at `/usr/lib/verity.d/sysexts.crt`? (§3, §9.)
7. **What is the current LTS stream, and what is the definitive list of valid `GROUP` values?** Open
   on [flatcar/Flatcar#2040](https://github.com/flatcar/Flatcar/issues/2040) since March 2026 and
   unanswered since June 2026. (§18.)
8. **Is there any documented factory-reset or reprovision-in-place path?** Nothing appears in the full
   documentation sitemap. (§5.)
9. **What happens when the root partition fills?** Specifically, does a full `/var` block an OS update
   that stages into a fixed-size system partition? (§21 scenario 8.)
10. **Is there Flatcar-specific guidance for bonding, VLANs, bridges and multi-NIC hosts?** These are
    the topologies edge, telco and industrial deployments need and the networkd page does not cover
    them. (§14.)
11. **What is a realistic wall-clock duration and disk requirement for a full `build_packages` plus
    `build_image` run?** No figure is published, and it is the largest unpriced item in the experiment
    plan. (§3, experiment section option C.)
12. **How long does a `kola` suite take to adopt for an external investigator**, and would maintainers
    prefer results expressed as `kola` tests? (§21, experiment section option E.)
13. **Is the `flatcar/mayday` support-bundle tool still supported, and why is it undocumented?**
    Carried from the Pulse baseline because it remains true and the repository is still active. (§12.)
14. **Are maintainer employer affiliations recorded anywhere?** `MAINTAINERS.md` records none, so
    single-employer concentration cannot be assessed from project files. (§16, §17.)

---

## Bias and scope note

**Tier and method.** Documentation-based architecture study covering all 22 framework dimensions. No
Flatcar instance was booted, no image was built, no update was applied, no rollback was forced, and
nothing was broken on purpose. Claims are DOCUMENTED, OBSERVED, INFERRED, UNKNOWN or NOT TESTED / OUT
OF TIER SCOPE. Nothing is REPRODUCED. The OBSERVED label is used narrowly and only for measurements
taken on 2026-09-16 against the GitHub API, the Flatcar release servers, the public Omaha update
endpoint or the documentation sitemap, with the query named each time.

**Why no experiments.** The scope call was made and posted on the ticket before the research started:
this tier has no ratified experiment-report template, and the four infrastructure decisions that gate
a real pass are open on the epic. Rather than invent a protocol inside a profile, this pass does the
architecture study in full and prices the experiment half above, so the gap is an explicit decision
with a cost attached. This is the same posture the sibling Bottlerocket and COS profiles took.

**Reading published source is in scope; guessing at unpublished internals is not.** Flatcar's build
system, update client and initramfs are public, so `build_library/prod_image_util.sh` and
`flatcar-postinst` are primary sources and are cited as such, marked DOCUMENTED (source) where prose
documentation does not cover the same ground. What was *not* done is inferring behaviour from the
Chrome OS or CoreOS lineage. Flatcar inherits the GPT attribute scheme and the Omaha protocol and says
so; it does not follow that any other Chrome OS behaviour applies, and none was assumed.

**Kairos bias control, applied.** Flatcar is treated exactly as every other system. Where its
architecture is better than Kairos's, this profile says so without hedging: the update path is
self-hostable with the project's own server code, the build system is fully public and runnable, the
governance documentation is more developed than most, and the independence story is the strongest in
the study so far. Where it is worse, it also says so: the A/B scope is the smallest of the A/B systems
here, `/etc` survives every rollback, Secure Boot has been incomplete for four years with no
documentation at all, and the sysext version-pinning treadmill is a recurring cost that a
package-manager or OCI-layer model does not have. §22 explicitly notes that the same nine-stage test
must be run against Kairos, and makes no claim about how Kairos would score.

**No speculation about corporate behaviour.** Kinvolk's acquisition (2021), the CNCF donation (2024),
the AKS deprecation (2026) and the Azure Container Linux derivative are recorded as dated facts with
their sources, and nothing is inferred from them about the project's future. The framework forbids it
and, separately, it would be bad evidence.

**Places where UNKNOWN was chosen over inference, deliberately:**

- What an OS update does to the shim and GRUB on the EFI system partition. The A/B pair is documented;
  this sits outside it and nothing describes it.
- What a full root partition does to an update. The partition layout makes a confident guess easy and
  a wrong guess plausible.
- Whether bonding, VLANs and bridges are supported. systemd-networkd can do all three, so the
  temptation to mark this DOCUMENTED is strong. The Flatcar-specific guidance does not exist, and "the
  underlying component supports it" is not the same claim.
- Whether a factory reset exists. A plausible procedure can be constructed from documented pieces,
  which is exactly why it is not recorded as a capability.
- Whether deltas are used between adjacent releases. One Omaha exchange with `delta_okay="false"` does
  not settle it.
- Whether SBC, Jetson, NPU, industrial or cellular hardware works. Nothing documents it either way,
  and generic arm64 support does not transfer automatically.
- Maintainer organizational diversity. The files record no affiliations, and guessing employers from
  names or commit patterns would be both unreliable and inappropriate.
- Per-CVE security response latency, boot time, idle memory and idle CPU. All measurable, none
  measured here.

**Two claims are INFERRED and are flagged in place rather than buried:** that a power cut during
staging leaves the active slot unchanged and bootable (§4, §21 scenario 1), and that a full root
partition would not block an OS update that stages into a fixed-size system partition (§21 scenario
8). Both rest on documented mechanics, neither is stated by the project, and both are near the top of
the experiment list above for exactly that reason.

**One partial correction to a prior source, stated rather than silently applied.** The Pulse baseline
recorded, from a June 2025 maintainer comment, that Secure Boot signatures were present in the alpha
channel. On 2026-09-16 the stable channel publishes a signed shim, signed GRUB, a signed kernel, a PCR
policy bundle and a Secure Boot QEMU image. Both facts are kept: the 2025 statement is accurate as of
its date, the 2026 observation extends it, and the part of the 2025 statement that still stands is the
one that matters most, which is that the shim is not signed by the third-party UEFI CA.
