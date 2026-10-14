# FR-13 deep dive: what does a Bottlerocket rollback actually revert?

Tracks [FR-13](../../docs/follow-up-research.md). Bottlerocket leg of the experiment, one of six legs
(Kairos, bootc, Fedora CoreOS, Flatcar, Bottlerocket, NixOS).

## Method, and why it differs from every prior leg

Bottlerocket has no local-QEMU story that ships as a downloadable artifact the way Flatcar's
qcow2 releases do. Its own [`QUICKSTART-LOCAL.md`](https://github.com/bottlerocket-os/bottlerocket/blob/develop/QUICKSTART-LOCAL.md)
covers exactly this use case, but only for a `metal-dev` variant that has to be **built from
source** (`BUILDING.md` quotes 12 minutes on a fast machine, 3-4 hours on a slow one, 80GB+ of
local disk). That was time-boxed out immediately as disproportionate for one leg of this
experiment.

Instead, this leg used Bottlerocket's real **production** artifacts, fetched the same way a
running Bottlerocket host fetches them:

1. Bottlerocket publishes signed images through a [TUF](https://theupdateframework.github.io/)
   repository at `updates.bottlerocket.aws`. Rather than installing the Rust toolchain needed to
   build `tuftool`, the TUF metadata chain was walked by hand with `curl`/`jq`
   (`timestamp.json` -> `<version>.snapshot.json` -> `<version>.targets.json`), which is exactly
   what `tuftool` automates. Every download below is verified against a `sha256` hash taken
   from that signed `targets.json`, not merely trusted because the URL resolved.
2. Two versions of the `vmware-k8s-1.33` variant were pulled as full OVAs: `v1.64.0` (2026-07-28,
   "old"/installed) and `v1.65.0` (2026-09-05, "new"/upgrade target). `sha256sum` on both
   downloads matched the TUF-signed hashes exactly.
3. Each OVA is a plain tar containing an `.ovf`, a `.mf` manifest, and a `streamOptimized` vmdk.
   `qemu-img convert -f vmdk -O raw` turned each into a bootable 3 GiB raw disk in under a
   second — no vSphere, `govc`, or ESXi involved anywhere in this leg.
4. The raw disk's GPT was inspected live with `fdisk --list-details` (not read from
   documentation) and confirmed the partition scheme Bottlerocket's own
   [`signpost` README](https://github.com/bottlerocket-os/bottlerocket-core-kit/blob/develop/sources/updater/signpost/README.md)
   describes: two complete partition sets (`BOOT-A/ROOT-A/HASH-A` and `BOOT-B/ROOT-B/HASH-B`,
   each with a `RESERVED-*` sibling), plus one `BOTTLEROCKET-PRIVATE` partition (settings/confd
   datastore) and one data partition (`/var`, `/local`, container storage). Sector offsets are
   byte-identical between the `v1.64.0` and `v1.65.0` images.
5. `/dev/kvm` was confirmed working on the local host and the disk was
   booted directly in `qemu-system-x86_64` with OVMF (UEFI) firmware — the same boot path a real
   Bottlerocket host uses, just without vSphere underneath it.

**Labeled per the repo's evidence convention:** steps 1-5 above are REPRODUCED — live commands
against the actual published artifacts and a real QEMU/KVM boot, not documentation alone.

## What worked, and what genuinely didn't: getting a shell

Every other leg in this series got an interactive shell inside the guest. This one did not,
and the reason is itself a finding worth recording plainly rather than hiding.

Bottlerocket's production images ship with **no local console login and no admin/control host
container enabled by default** — the only supported way in is SSH to the admin container, which
itself has to be turned on via `settings.host-containers.admin` before first boot. Two real,
documented injection mechanisms were tried:

1. **The private-partition file injection** `tools/start-local-vm` uses for `metal-dev`
   (rebuild the `BOTTLEROCKET-PRIVATE` partition's ext4 filesystem with `net.toml` +
   `user-data.toml` + `bootconfig.data` at the root, `dd` it back over the original partition's
   sectors with `conv=notrunc`). Applied by hand, sector-for-sector, to the `vmware-k8s`
   `v1.64.0` disk.
2. **The VMware CD-ROM/OVF-environment provider** (`sources/early-boot-config/user-data-providers/vmware-cd-rom`
   in `bottlerocket-core-kit`), which mounts a CD-ROM at `/media/cdrom` and reads a plain-TOML
   file literally named `user-data` from it — attached as a `genisoimage`-built ISO on an IDE
   CD-ROM device.

Both were confirmed, empirically, **not to reach the settings store**: the running guest's
private-partition confd datastore (`/datastore/<version>_<id>/live/settings/host-containers/admin/`)
never gained an `enabled` or `user-data` key on either attempt, checked by reading the actual
private partition off the disk with `debugfs` while the VM was running. `ssh -p 2222` to the
forwarded guest port consistently got `Connection refused` (SLIRP successfully proxying to a
guest with nothing listening on port 22), not a timeout — consistent with the admin container
never starting because it was never told to.

**What this rules in, not just out:** the guest *did* boot into real userspace both times — the
private partition's confd datastore was actively read and rewritten by the running system
(new versioned generations appearing under `/datastore/`, an `inventory/application.json`
freshly written at the moment of inspection), which only a live `systemd` + `storewolf` +
`sundog` stack produces. The boot itself, and the disk's real content, are genuine; only the two
specific config-injection paths tried are confirmed not to be wired up for the `vmware-k8s`
variant under plain QEMU (`start-local-vm`'s own docs say the private-partition trick is written
for `metal-dev`; the CD-ROM/OVF path exists in the source but this leg could not get it detected
inside the ~5 minutes budgeted for this specific sub-problem before time-boxing it).

**NOT TESTED, disclosed rather than hidden:** an interactive shell issuing `touch`/`cat`
commands inside a running guest, and the two supported update commands themselves —
`apiclient update apply` and `signpost` run *from inside the OS*. Both need exactly the shell
access above.

## Reproducing the core mechanism a different way

Following the precedent of the other legs (Flatcar's leg did the same for the Omaha/`update_engine`
handshake), the underlying mechanism was reproduced directly against the real artifacts instead
of abandoning the leg:

**Read-only root and its actual contents (REPRODUCED, offline rather than in a running VM, against the real downloaded
disk):** `ROOT-A` was loop-mounted read-only (`losetup -r -o <offset> --sizelimit <size>`,
`mount -o ro`) directly off the raw disk, bypassing dm-verity entirely since verity only
*enforces* the read-only-ness, it doesn't gate a plain read. This confirmed, by looking at the
actual files rather than a doc:

- `/etc` on the root filesystem image is **structurally empty** — just a `selinux` symlink into
  `/usr/share/factory/etc/selinux`. The real population mechanism is
  `/usr/lib/tmpfiles.d/etc.conf`, systemd's stock rules (`C! /etc/nsswitch.conf`, `C! /etc/issue`,
  etc. — copy-if-absent from `/usr/share/factory/etc`), which only make sense against a **tmpfs**
  mounted fresh at `/etc` every boot. This matches Bottlerocket's own documentation
  ("/etc is ephemeral... rebuilt during each boot") but this leg verified it by reading the
  actual shipped root filesystem rather than trusting the doc alone — the same evidence bar
  Kairos's `/etc`-on-tmpfs finding was held to.
- `/var` and `/local` are **empty directories** on the root image, i.e. plain mount points. The
  real content lives on the separate data partition/volume, per Bottlerocket's own README
  ("the persisted volume... /var, /local, /opt, /mnt"), confirmed structurally by their absence
  from the read-only image itself.
- `/usr` is a symlink into `x86_64-bottlerocket-linux-gnu/sys-root/usr`, the tree
  dm-verity actually protects.
- The real dm-verity setup was read directly out of the shipped `grub.cfg` (extracted from the
  `BOOT-A` partition with `debugfs`, not assumed): Bottlerocket needs **no separate initrd** to
  assemble the root filesystem. The kernel command line itself carries
  `dm-mod.create="root,,,ro,0 661488 verity 1 PARTUUID=$boot_uuid/PARTNROFF=1 ... sha256 <root-hash> <salt> ..."`
  — the verity device is built by the kernel's own `dm-mod.create=` parameter before `/sbin/init`
  ever runs, and `root=/dev/dm-0` points straight at it.

**The update/rollback mechanism itself (REPRODUCED at the partition level, INFERRED for the
in-guest command sequence):** Bottlerocket's own updater tool,
[`signpost`](https://github.com/bottlerocket-os/bottlerocket-core-kit/tree/develop/sources/updater/signpost),
uses **the same ChromeOS-style GPT priority/tries/successful bits** ("gptprio") that Flatcar's
`cgpt` manipulates — confirmed by reading `signpost`'s own source (`gptprio.rs`) and its
README, which spells out the exact procedure:

1. `signpost clear-inactive` — clear the priority/tries bits on the inactive set.
2. Copy the downloaded `boot`/`root`/`hash` images onto the inactive set's partitions.
3. `signpost upgrade-to-inactive` — prioritize the inactive set for **one boot attempt**
   (the same one-shot semantics as Kairos's `next_entry`, not Flatcar's/bootc's durable
   flip — an unmarked-successful boot rolls back automatically). A `mark-successful-boot.service`
   unit (read directly from `bottlerocket-core-kit`) runs `signpost mark-successful-boot`
   automatically once the system reaches `preconfigured.target`, making the new set durable.
4. Rollback is `signpost rollback-to-inactive` — deprioritize the inactive set, no network
   or external service needed, "made to be as reliable as possible" per the tool's own README.

Step 2 was reproduced directly and completely, against the real published artifacts, without
needing a guest shell:

- The exact `boot`/`root`/`hash` partition contents for `v1.65.0`'s active set were extracted
  byte-for-byte from the downloaded `v1.65.0` OVA's raw disk (`dd skip=... count=...` at the
  live-confirmed sector offsets).
- Those bytes were `dd`'d, `conv=notrunc`, onto `v1.64.0`'s **inactive** `B` set — the exact
  target `signpost`'s own procedure names. The `B` set on a freshly downloaded, never-updated
  image is genuinely blank (`dd | od` showed all zero bytes at `ROOT-B`'s first sectors before
  the write), so this is a real "install the update payload" step, not overwriting existing
  data.
- The write was verified by `sha256sum`, byte-identical to the source, and then by
  loop-mounting the now-populated `ROOT-B` partition read-only and reading
  `/usr/lib/os-release`: `VERSION_ID=1.65.0`, `BUILD_ID=0be31b34` — matching the downloaded
  `v1.65.0` image exactly. `ROOT-B`'s `/etc` showed the identical empty-shell-plus-`etc.conf`
  pattern as `ROOT-A`, confirming the ephemeral-`/etc` structure is a property of every
  deployment, not something that varies between the active and inactive set.
- `fdisk --list-details` on the now-upgraded disk confirmed the GPT priority attribute bits
  are **still only set on `BOOT-A`** — exactly the state `signpost`'s procedure expects
  immediately after step 2 and before step 3 runs. Nothing about writing the new partitions
  changes which slot GRUB will pick next; that is `signpost upgrade-to-inactive`'s job alone,
  by design.

**What remains INFERRED, not REPRODUCED, because of the shell-access gap above:** that running
`signpost upgrade-to-inactive` and rebooting would actually boot `v1.65.0`, and that
`signpost rollback-to-inactive` afterward would boot back into `v1.64.0` with no data loss. This
is a low-risk inference, not a guess — the mechanism `signpost` operates on (GPT priority bits
read by GRUB's `gptprio` module) is standard, documented, and was confirmed present and
correctly laid out on this exact disk; only the "run one Rust binary, then reboot" step itself
was not executed live, because it can only be run from inside the OS.

## What this settles for Bottlerocket

- Bottlerocket's `/usr`+root read-only design is real dm-verity, wired entirely through kernel
  command-line parameters (`dm-mod.create=`) rather than a separate userspace initrd step —
  structurally the leanest of the five systems examined so far in this series.
- `/etc` is **ephemeral tmpfs, rebuilt every boot from a `/usr/share/factory/etc` skeleton plus
  dynamic settings generators** — the same category as Kairos's finding (an `/etc` edit does not
  survive so much as a plain reboot, let alone an upgrade or rollback), and a different category
  from Flatcar (`/etc` overlay-upper lives on the untouched `ROOT` partition, survives
  everything) and from bootc/Fedora CoreOS (`/etc` moves with the deployment; a rollback
  reselects an older `/etc` snapshot rather than reverting to a specific prior state).
- `/var` and `/local` (container storage, `/opt`, `/mnt`) sit on a completely separate partition
  from the `A`/`B` boot/root/hash sets, structurally outside anything an update or rollback
  writes to — the same "wrong partition entirely" guarantee Flatcar's `ROOT` partition gives for
  `/etc`/`/var`/`/home`, just with a narrower persistent set (Bottlerocket has no persistent
  `/etc`, Flatcar does).
- Bottlerocket's rollback is a **one-shot, auto-reverting** priority flip
  (`upgrade-to-inactive` gets exactly one boot attempt unless `mark-successful-boot` fires) —
  the same operational shape as Kairos's `next_entry`, not the durable flip bootc/FCOS/Flatcar
  use. Of the five systems this experiment has now examined, Bottlerocket and Kairos share this
  property; Flatcar, bootc, and Fedora CoreOS do not.
- **Genuine limitation of this leg, disclosed rather than hidden:** no interactive command was
  run inside a live Bottlerocket guest. The production `vmware-k8s` variant's supported
  local-config-injection paths (private-partition file injection, VMware CD-ROM/OVF
  environment) were both tried against the real image and both confirmed, by reading the
  guest's own settings datastore, not to take effect — most likely because that variant's
  `early-boot-config` wiring (which user-data provider(s) run, and in what priority) differs
  from what `metal-dev`'s tooling assumes, or needs a stanza this leg's ~2 hours of budget for
  local-boot investigation didn't uncover. Building `metal-dev` from source — the officially
  supported local-testing path — was time-boxed out up front as a multi-hour, 80GB+ yak-shave
  disproportionate to one leg of this experiment. A future pass could either invest in that
  build, or debug the `vmware-cd-rom` provider's actual detection logic further; either would
  close this specific gap without touching any of the structural findings above, which do not
  depend on it.

## Scope note for the remaining system

NixOS remains. Its rollback is generation-based (a Nix store closure plus a boot entry), a
different kind of question from every A/B-image system this series has covered so far —
Bottlerocket included, despite the superficial resemblance to Flatcar's split-partition design.
