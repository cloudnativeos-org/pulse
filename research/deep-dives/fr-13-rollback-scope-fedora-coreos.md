# FR-13 deep dive: what does a Fedora CoreOS rollback actually revert?

Tracks [FR-13](../../docs/follow-up-research.md). Fedora CoreOS leg,
following the bootc leg
([fr-13-rollback-scope-bootc.md](fr-13-rollback-scope-bootc.md)) — expected to share bootc's
architecture, and confirmed to below. Flatcar, Bottlerocket and NixOS each need a different
install path and are separate follow-up work.

## Method

Official `stable` stream qcow2 (release `44.20260829.3.1`) booted directly in QEMU with an
Ignition config for SSH access — no custom build for the base install, unlike the Kairos and
bootc legs, because Fedora CoreOS ships ready-made disk images. `Zincati` (automatic-update
agent) stopped and disabled first, so it could not upgrade the machine out from under the
experiment. A derived image (`quay.io/fedora/fedora-coreos:stable` plus one marker file, tagged
`v2`) built on the host with `podman`, transferred into the guest's own container storage as an
OCI archive over SSH (no registry), and applied with `bootc switch`. Every check below is a live
SSH command against the running VM.

The test artifacts (`ignition.json`, `build/Containerfile.v2`) are not published with this
dataset.

**A blocker worth recording:** the Ignition config must use spec version `3.x` (`3.4.0` used
here). Fedora CoreOS's Container Linux Config-era `1.x` version numbering is a different,
unsupported scheme on current releases and fails with a plain "unsupported config version",
dropping the boot to emergency mode with no useful hint at the version number itself.

## The real finding: Fedora CoreOS 44 is already a bootc system

This is worth stating plainly because it changes what "Fedora CoreOS's architecture" means going
forward: the booted 44.20260829.3.1 deployment reports as
`ostree-image-signed:docker://quay.io/fedora/fedora-coreos:stable`, `bootc`/`podman`/`skopeo` are
present in the base image, and `bootc switch`/`bootc rollback` work directly, with no
Fedora-CoreOS-specific tooling needed. FR-13's original framing (bootc and Fedora CoreOS as two
separate but comparable systems) undersells how close they now are: at this release, they are the
same deployment mechanism end to end, not just a comparable one.

## Partition layout observed

Identical shape to the bootc leg: `/` is a read-only composefs overlay; `/etc` and `/var` are
both bind-mounted from the same partition (`/dev/vda4`, xfs), with `/var` shared across every
deployment and `/etc` a separate copy per deployment.

## Three marked changes, and when each was made

Same structure as the bootc leg (see that file for the full table). In short: an image-baked
`/etc` marker per version, a live `/etc`+`/var` marker made while on v1 (the original
`quay.io/fedora/fedora-coreos:stable` deployment), and a second live `/etc`+`/var` marker made
while on v2, immediately before rolling back.

## Results

**1. Switch to v2, reboot.** `/etc`'s image-baked marker updated to v2's value. The v1-era live
`/etc` marker survived into v2 — carried forward by the same three-way merge behavior found in
bootc.

**2. Rollback, reboot.** Landed back on the *original* `quay.io/fedora/fedora-coreos:stable`
deployment (not the locally-tagged v2 — expected, since v1 was never re-tagged, just the
deployment that already existed). The v1-era live marker was present again. **The v2-era live
marker, made immediately before rolling back, was gone.** Exactly the bootc result: a rollback
reselects an already-existing `/etc` snapshot, frozen when that deployment was built, and does not
carry forward anything written after that point.

**3. `/var` markers.** All three (image-baked v1, v1-era live, v2-era live) present at every
step, before and after both the switch and the rollback — `/var` is shared, unconditionally.

**4. One-shot vs. durable.** A further plain reboot with no explicit command stayed on the rolled
back deployment. Durable, same as bootc, and the opposite of Kairos's one-shot `next_entry`.

## What this settles for Fedora CoreOS

Everything the bootc leg settled applies here without modification, because as of release
44.20260829.3.1 they are the same mechanism: `/etc` changes are merged forward exactly once, at
the next switch/upgrade, and are lost across a rollback that reselects a deployment built before
that change existed. `/var` is unconditionally shared. Rollback is a durable deployment-order
change, not a one-shot boot override.

The one genuinely new finding specific to this leg is architectural, not behavioral: Fedora
CoreOS and bootc are not two systems that happen to behave alike, they are the same system at
this point in Fedora's release cycle. Any future FR-13-style comparison table should reflect
that, rather than listing them as independently-verified peers.

## Scope note for the remaining systems

Flatcar and Bottlerocket ship pre-built disk images without a bootc-style container/OSTree
delivery mechanism, and NixOS's rollback is generation-based rather than image-based; each still
needs its own VM setup.
