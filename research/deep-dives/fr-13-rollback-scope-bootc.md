# FR-13 deep dive: what does a bootc rollback actually revert?

Tracks [FR-13](../../docs/follow-up-research.md). bootc leg. Fedora CoreOS
shares this architecture (OSTree deployment swap) and is expected to behave the same way, but is
not itself tested here. Flatcar, Bottlerocket and NixOS each need a different install path and are
separate legs, same as the Kairos leg
([fr-13-rollback-scope-kairos.md](fr-13-rollback-scope-kairos.md)) left them.

## Method

Two images built from `quay.io/fedora/fedora-bootc:41`, differing only in a marker file baked into
`/etc` at build time, tagged `v1` and `v2`. `v1` installed to a 12G raw disk via `bootc install
to-disk --via-loopback` inside a privileged `podman` container, booted in QEMU with KVM
acceleration. `v2` transferred into the guest's own container storage as an OCI archive over SSH
(no registry involved) and applied with `bootc switch --transport containers-storage`. Every check
below is a live SSH command against the running VM, not a documentation read.

The test artifacts (`Containerfile.v1`, `Containerfile.v2`, `install.sh`) are not published with
this dataset.

## A blocker worth recording: `--disable-selinux` broke the install, not fixed it

`bootc install to-disk` failed every attempt with `fsetxattr(security.selinux): Invalid argument`
while unpacking the image, regardless of container runtime (Docker or podman), SELinux container
label (`type:unconfined_t` or `disable`), or whether the host had the `osbuild-selinux` policy
package installed. The fix was removing `--disable-selinux` from the install command entirely. That
flag's own `--help` text reads "necessary to install *from* a system with SELinux disabled but
where the target does have SELinux enabled" — the opposite of the test setup (SELinux Enforcing
throughout) — and passing it anyway made bootc write an invalid label instead of skipping labeling.
Once dropped, the same command succeeded immediately. Anyone repeating this on an Enforcing host:
leave `--disable-selinux` off unless the source side is actually SELinux-disabled.

## Partition layout observed

Confirmed by `lsblk`/`mount` on the installed disk:

- `/` is a read-only composefs overlay, backed by `/sysroot/ostree/repo/objects` — the
  content-addressed image store, shared across every deployment.
- `/var` and `/etc` are both bind-mounted from the same partition (`/dev/vda3`, xfs) that holds
  `/sysroot`. `/var` is one shared instance across all deployments. `/etc`, by contrast, is a
  **separate copy per deployment** — `/sysroot/ostree/deploy/default/deploy/<checksum>/etc` — bind
  mounted in at boot for whichever deployment is active.

## Three marked changes, and when each was made

| Path | Value | When made | Shared or per-deployment |
|---|---|---|---|
| `/etc/rollback-marker-image.txt` | image-baked, differs v1 vs v2 | build time | per-deployment (part of the image) |
| `/etc/rollback-marker-live.txt` | `MARKER_ETC_LIVE_v1` | live, while booted on v1, before upgrading | per-deployment (this deployment's own `/etc`) |
| `/etc/rollback-marker-live-v2.txt` | `MARKER_ETC_LIVE_v2` | live, while booted on v2, before rolling back | per-deployment (v2's own `/etc`) |
| `/var/rollback-marker.txt` | `MARKER_VAR_v1` | build time (v1 image) | shared |
| `/var/rollback-marker-live.txt` | `MARKER_VAR_LIVE_v1` | live, while booted on v1 | shared |
| `/var/rollback-marker-live-v2.txt` | `MARKER_VAR_LIVE_v2` | live, while booted on v2 | shared |

## Results

**1. Upgrade (`bootc switch` to v2, then reboot).** `/etc/rollback-marker-image.txt` updated to
v2's image-shipped value, confirming the deployment's `/etc` is derived fresh from the new image at
switch time. `/etc/rollback-marker-live.txt` — the marker set on v1 *before* the switch, never part
of any image — **survived into v2's `/etc`**. bootc/ostree carries local `/etc` modifications
forward across an upgrade via a three-way merge at deployment-creation time; this is not a shared
`/etc`, it is a merge performed once, when the new deployment is built.

**2. Rollback (`bootc rollback`, made a new `/etc` and `/var` marker on v2 first, then rebooted).**
`/etc/rollback-marker-image.txt` reverted to v1's value and `/etc/rollback-marker-live.txt` (the
marker from step 1) was back, both expected — this is v1's own, already-existing `/etc`, untouched
since the switch away from it. **`/etc/rollback-marker-live-v2.txt` — the marker made on v2,
immediately before rolling back — was gone.** This is the sharpest finding: rollback does not carry
forward an `/etc` change made on the deployment you are rolling back *from*. It reselects an
existing, unrelated `/etc` copy that was frozen at the moment the v2 deployment was created. This
matches the concern raised earlier from reading bootc's own docs: rollback reorders existing
deployments rather than building a new one, so anything written to `/etc` after that deployment was
built travels with neither the forward path (there is none) nor the rollback.

**3. `/var` markers.** All three (`v1` image-baked, `v1`-era live, `v2`-era live) were present at
every step — before the upgrade, after the upgrade, and after the rollback. `/var` is one shared
instance across every deployment; it is simply never part of what switch or rollback touch.

**4. One-shot vs. durable.** A further plain reboot, with no explicit `bootc switch` or `bootc
rollback`, stayed on v1. Unlike Kairos's `bootentry --select fallback` (a one-shot GRUB override,
[fr-13-rollback-scope-kairos.md](fr-13-rollback-scope-kairos.md)), bootc's rollback reorders the
actual deployment list bootupd's GRUB config walks, so it is durable until the next explicit
`switch`/`rollback`/`upgrade` — not a one-time redirect that a plain reboot undoes.

## What this settles for bootc

- A rollback reverts to a specific, already-existing `/etc` (and the read-only image content it
  came from). It is not a shared `/etc` and not a live merge at rollback time — it is a fixed
  snapshot taken when that deployment was created.
- `/etc` edits are carried forward exactly once, at the next `switch`/`upgrade`, via a three-way
  merge. An edit made and then rolled back past — without an intervening switch that would merge it
  forward — does not survive. This is a real, narrower version of that concern: it is not that
  bootc "loses" `/etc` changes generally, it is that a change's survival depends on whether a new
  deployment was built *after* it was made.
- `/var` is unconditionally shared and untouched by both switch and rollback, matching Kairos's
  `/oem`/`/usr/local` persistence story even though the two projects reach it by different means
  (bind-mounted shared partition vs. explicit persistent binds).
- bootc's rollback is a durable deployment-order change, not a one-shot boot override — the
  opposite of Kairos's `next_entry` semantics for the same word.

## Scope note for the remaining systems

Fedora CoreOS shares bootc's OSTree deployment model closely enough that this result is expected to
transfer, but that is an expectation, not a result — it needs its own live run. Flatcar and
Bottlerocket ship pre-built disk images rather than an installer/container path, and NixOS's
rollback is generation-based rather than image-based; each needs its own VM setup entirely.
