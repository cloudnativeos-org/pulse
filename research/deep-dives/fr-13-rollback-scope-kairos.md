# FR-13 deep dive: what does a Kairos rollback actually revert?

Tracks [FR-13](../../docs/follow-up-research.md).
Kairos leg of the experiment. The other systems in scope (Flatcar, Bottlerocket,
Fedora CoreOS, bootc, NixOS) each need a different install path and have their own legs,
not a re-run of this one.

## Method

Two images built with `kairos-init v0.17.3` on Ubuntu 24.04 base, tagged
`1.0.0` and `1.0.1`, differing only in tag. `1.0.0` installed to a qcow2 disk via
an AuroraBoot ISO, booted in QEMU. `1.0.1` served from a throwaway local OCI
registry for the upgrade step. Every check below is a live SSH command against
the running VM, not a documentation read.

The test artifacts (`Dockerfile`, `install.yaml`, `install2.log`, `boot1.log`) are not published
with this dataset.

## Partition layout observed

Confirmed by `lsblk`/`mount` on the installed disk, matching the profile:

- `COS_OEM` (`/oem`) — persistent.
- `COS_STATE` — holds the active and passive root images.
- `COS_RECOVERY` — the fallback recovery environment.
- `COS_PERSISTENT` — bind-mounted onto `/usr/local`, `/home`, `/opt`,
  `/var/lib/*`, and the explicit `/etc` subpaths (`/etc/ssh`, `/etc/systemd`,
  `/etc/rancher`, others) listed in `kairos-init`'s `00_rootfs.yaml`.
- `/etc` itself is an `overlay` mount, upper layer on tmpfs
  (`upperdir=/run/overlay/etc/.overlay/upper`) — confirmed by `mount`, not
  inferred from the shipped cloud-config.

## Four marked changes, made before the upgrade

| Path | Value | On the persisted-bind list? |
|---|---|---|
| `/oem/rollback-marker.txt` | `MARKER_OEM_v1.0.0` | yes (COS_OEM) |
| `/usr/local/rollback-marker.txt` | `MARKER_USRLOCAL_v1.0.0` | yes (COS_PERSISTENT) |
| `/etc/ssh/sshd_config` | appended marker line | yes |
| `/etc/hostname` | changed | no |

## Results

**1. Bare reboot, no upgrade.** `/etc/hostname` reverted to the image default
(`rollback-test`) immediately — lost on the very next boot, independent of any
upgrade or rollback. This is the tmpfs-overlay behaviour, not a rollback
property. The other three markers were untouched, as expected — nothing had
happened to them yet.

**2. Upgrade.** `kairos-agent upgrade --source oci:10.0.2.2:5000/kairos-rollback-test:1.0.1 --allow-insecure-registries`.
The upgrade log showed the active/passive image swap: the running image became
`COS_PASSIVE`, the new `1.0.1` image became `COS_ACTIVE`. After reboot,
`KAIROS_RELEASE=v1.0.1`. All three persisted markers survived. `/etc/hostname`
came back to the image default again — a fresh tmpfs overlay from the new
image, same mechanism as step 1, not a separate finding.

**3. Rollback.** `kairos-agent bootentry --select fallback` wrote
`next_entry=fallback` into `/oem/grubenv`. After reboot: `KAIROS_RELEASE` back
to `v1.0.0`, all three persisted markers intact, and `next_entry` had been
cleared back to empty by GRUB on consumption.

**4. One-shot confirmation.** A further plain reboot, with no `next_entry` set,
went back to `v1.0.1` — the active slot, not the rolled-back one. This
confirms `bootentry --select fallback` is a one-shot GRUB override, exactly as
an earlier reading of the code argued: it does not durably swap which
slot is "current." A durable pin needs `saved_entry`, not exercised in this
run.

## What this settles for Kairos

- A rollback reverts the whole root image (kernel, `/usr`, and the
  image-shipped `/etc` defaults). It does not touch `/oem`, `/usr/local`, or
  any of the explicitly bind-mounted `/etc` subpaths — those live outside the
  image entirely, on `COS_PERSISTENT`/`COS_OEM`, and were never in scope for
  either the upgrade or the rollback to touch.
- An `/etc` edit outside the persisted-bind list survives exactly until the
  next reboot, upgrade or rollback — all three recreate the tmpfs overlay from
  the image's shipped `/etc`. This is a property of the overlay, not of
  rollback specifically.
- Manual rollback via `bootentry --select fallback` is one-shot. It answers
  "what does the next boot do," not "what is the machine's state going
  forward" — the two are the same question only until the next reboot with no
  explicit selection.

## Scope note for the remaining systems

Flatcar and Bottlerocket ship pre-built disk images rather than an installer
ISO — no AuroraBoot-equivalent step, different VM setup. NixOS's rollback is
generation-based, not image-based, so "what survives a rollback" is a
different kind of question there (a generation is a Nix store closure plus a
boot entry, not an A/B image pair). bootc/Fedora CoreOS are the closest to
this recipe (OSTree deployment swap, comparable to the AuroraBoot/QEMU flow
here) but still need their own install path. Each is realistically its own
~20-30 minute VM lifecycle, not a copy-paste of this one.
