# FR-13 deep dive: what does a Flatcar rollback actually revert?

Tracks [FR-13](../../docs/follow-up-research.md). Flatcar leg of the experiment, one of six legs
(Kairos, bootc, Fedora CoreOS, Flatcar, Bottlerocket, NixOS).

## Method, and why it differs from the Kairos/bootc/FCOS recipe

Flatcar ships pre-built disk images per release, not an installer ISO — there is no
AuroraBoot-equivalent step. Two stable releases were downloaded as qcow2 images,
`4593.2.5` (2026-08-13) and `4757.2.0` (2026-09-14, then-current), and converted to raw.

A real Flatcar update runs through `update_engine` talking an Omaha-protocol handshake
to an update server (Nebraska, in local testing), which is a substantial separate
service to stand up. Rather than block this leg on that, the actual mechanism `update_engine`
exercises — a byte-for-byte write of the new release's `USR` partition into the currently
inactive `USR` slot, followed by a GPT-priority flip — was reproduced directly:

1. Booted `4593.2.5` (throwaway ignition config, ssh key only) in QEMU on a local host, with
   `/dev/kvm` confirmed working.
2. Confirmed the partition layout live (`lsblk`, `parted`, `cgpt show`, all run against the
   actual disk, not read from docs): `EFI-SYSTEM`, `BIOS-BOOT`, `USR-A`/`USR-B` (the A/B pair,
   2 GiB each, `dm-verity`-backed btrfs, alias `coreos-rootfs`), `OEM`, `OEM-CONFIG`, `ROOT`
   (ext4, alias `coreos-auto-resize` — this is the persistent, always-mutable partition).
3. Marked three paths before touching anything: `/etc/rollback-marker.txt`,
   `/var/lib/rollback-marker.txt`, `/home/core/rollback-marker.txt`. A fourth attempt at
   `/usr/rollback-marker.txt` failed immediately with "Read-only file system" — confirmed
   live, not assumed.
4. Powered the VM off cleanly and, on the host, `dd`'d `4757.2.0`'s `USR-A` partition
   bytes (verified byte-identical afterward with `cmp`) into the running disk's `USR-B`
   slot. Copied `4757.2.0`'s ESP kernel (`/flatcar/vmlinuz-a`) in as `/flatcar/vmlinuz-b`,
   since Flatcar's `postinst` script (read directly from the shipped image, `/usr/bin/flatcar-postinst`)
   turned out to do no kernel-copying at all — the kernel is a separate, larger artifact
   than anything shipped inside `/usr`, so a real update payload must deliver it through a
   channel this experiment did not reproduce. Sourcing it from the full release image
   instead is a reasonable substitute for what's under test here (persistence across a slot
   swap), not a claim about how `update_engine`'s payload format actually carries it.
5. GRUB's fixed `Flatcar USR-B` menu entry (a manual-override entry, separate from the
   `gptprio`-driven `Flatcar default` entry) was used to boot the new slot directly, since
   this avoids needing the GPT priority bits set up exactly right.

**Labeled per the repo's evidence convention:** everything above through step 5 is
REPRODUCED — live commands against a running VM, not documentation. The exact
`update_engine`/Nebraska delivery path itself is NOT TESTED.

## Results

**Booted `4757.2.0` (the "upgrade").** `VERSION_ID` confirmed via `/etc/os-release`.
All three markers (`/etc`, `/var/lib`, `/home/core`) survived, unchanged, byte for byte.

**Partition-level explanation, confirmed via live `mount` output on both sides of the
swap:**
- `/usr` is mounted from `/dev/mapper/usr` (the verity-mapped device), `ro`, on both
  versions — the read-only enforcement is real, not conventional.
- `/etc` is an **overlay whose upperdir is `/sysroot/etc`** — a literal path on the
  `ROOT` partition. This is the key structural difference from Kairos: Kairos's `/etc`
  overlay upper sits on **tmpfs** (lost every reboot, regardless of upgrade or rollback —
  see the Kairos leg's finding #1). Flatcar's overlay upper is **on disk, on the partition
  that is never touched by a `USR` slot swap.** An `/etc` edit in Flatcar survives a plain
  reboot, an upgrade, and (structurally, see below) a rollback — none of those three events
  touch `ROOT`.
- The overlay's **lowerdir** did change between versions (`/sysroot/usr/share/flatcar/etc`
  on `4593.2.5`, folded into a `systemd-sysext`/`confext` mechanism on `4757.2.0` —
  `/run/systemd/sysext/confexts/00-flatcar-default/etc`). This is a genuine implementation
  change between these two releases (confext replacing a plain path), not a rollback
  artifact — noted for completeness, not a finding this experiment set out to test.
- `/var` and `/home` are plain paths on `ROOT` (`/dev/vda9` mounted at `/`), with no overlay
  involved at all — the simplest possible "unaffected by any USR-side event" case.

**Rollback step: not directly reproduced.** After the upgrade boot, a `cgpt add` edit
(raising `USR-B`'s priority above `USR-A`'s to make the *automatic* `gptprio`-driven
entry pick the new slot on a plain `reboot`, so the "rollback" step could be a plain
`sudo reboot` rather than another manual menu pick) miscounted the ChromeOS
priority/tries protocol and left **both** slots ineligible for `gptprio`'s automatic
selection (`no such partition`, `grub-core/commands/gptprio.c:120`). Recovering from
that needs either a correct `cgpt` fix from a booted shell, or a manual GRUB menu
selection at the boot prompt — and scripting that selection via QEMU's HMP `sendkey`
against a `-display none` headless instance did not reach the guest's input queue in
repeated attempts (menu countdown ran to completion regardless of keys sent; `-vnc`
as an alternative input backend made no difference either). Time-boxed rather than
pursued further, in keeping with the rule not to chase any leg past its scope.

**What this leaves INFERRED, not REPRODUCED, for the rollback specifically:** that
booting back into `USR-A` would show the same three markers intact. This is a low-risk
inference, not a guess: the mechanism already directly observed — `ROOT` is a fixed
partition (`/dev/vda9`) never referenced by anything that decides which `USR` slot is
active — was exercised identically in both directions across the *forward* swap
(A→B), where it held. A rollback (B→A) exercises the exact same mechanism with the
slots reversed; nothing observed suggests slot direction matters to `ROOT`'s mount.
Flagged explicitly as INFERRED rather than folded into the confirmed results, per the
evidence standard in methodology.md section 6.

## What this settles for Flatcar

- Flatcar's split-`usr` design means only `/usr` (kernel + OS proper) is ever part of an
  update or rollback. `/etc`, `/var`, `/home` — anything on `ROOT` — is structurally
  outside the update mechanism's reach in either direction, not merely preserved by
  policy. This is a sharper guarantee than Kairos's (where `/etc` itself is lost every
  reboot regardless of upgrade/rollback, since its overlay upper is tmpfs) and a
  different guarantee than bootc/Fedora CoreOS's (where `/etc` **does** move with the
  deployment on upgrade, and rollback reselects an already-built `/etc` snapshot rather
  than reverting to the pre-upgrade state — see the bootc leg).
- `/usr` read-only enforcement is real and immediate (a write attempt fails at the
  filesystem level, not just "shouldn't be done").
- **Operational finding, not a Flatcar defect:** a naive `cgpt` priority edit that doesn't
  respect the tries/priority/successful protocol correctly can strand both slots as
  ineligible for automatic selection simultaneously. Real `update_engine` never does
  this because it manages the full protocol; a partition-level experiment that only
  moves priority without matching tries/successful bookkeeping can.
- **Operational finding for future VM work on a similar setup:** QEMU's HMP `sendkey`, sent to
  a `-monitor unix:...` socket against a `-display none` (or `-vnc`-only) headless
  instance, did not register as guest keyboard input against a GRUB text menu in this
  setup, across several timing and reconnection variants. Anything that needs an
  interactive GRUB menu choice on a similar setup should raise the timeout and find another
  input path (or use a fixed menu entry / direct `-kernel` boot instead of relying on
  the default/timed entry), rather than assuming `sendkey` reaches the guest.

## Scope note for the remaining systems

Bottlerocket and NixOS remain. Bottlerocket is architecturally close to Flatcar
(A/B partitions, read-only root, `/etc`/`/var` persistence model) — its own update
mechanism (`updog`) is a different implementation of the same idea and would need its
own investigation, not a copy of this recipe. NixOS's rollback is generation-based, a
different kind of question entirely (a Nix store closure plus a boot entry, not an A/B
image pair).
