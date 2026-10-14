# FR-13 deep dive: what does a NixOS rollback actually revert?

Tracks [FR-13](../../docs/follow-up-research.md). NixOS leg of the experiment, one of six legs
(Kairos, bootc, Fedora CoreOS, Flatcar, Bottlerocket, NixOS).

## Why this leg is a different shape of question

Every other system in this FR-13 series rolls back an A/B pair or an OSTree deployment: two whole
root images (or two deployments), one active, one not. "What survives" is a question about a
partition boundary or a deployment boundary.

NixOS has no A or B. `nixos-rebuild switch` never overwrites anything — it builds a new **Nix
store closure** (the full dependency graph a configuration needs) and adds a **generation**: a
new entry in `/nix/var/nix/profiles/system` pointing at that closure, plus a new boot-loader
menu entry. Every past generation's closure stays on disk (garbage-collected only on request),
so a NixOS host can in principle roll back to any earlier point, not just one step back — the
opposite of Kairos/Bottlerocket's one-shot single-fallback design. This leg tests that unit
directly: a generation is a store closure plus a boot entry, and "rollback" means switching
which generation the running system, the `/etc` symlink farm, and the default boot entry point
at.

## Method

A real install, not documentation: NixOS 24.11 minimal ISO (`nixos-minimal-24.11.719113...`,
downloaded from `releases.nixos.org`) installed with `nixos-install` onto a 20GiB qcow2 disk in
QEMU/KVM on the local host, legacy BIOS boot (GPT + `bios_grub` partition, GRUB2, no OVMF needed).
Every step below was driven over the VM's real serial console with `pexpect`, not a documented
procedure — the NixOS live ISO auto-logs into an unprivileged `nixos` user by default, so each
session did `sudo -i` to get root, then ran the same commands a person would type by hand.

**Getting a NixOS artifact for local QEMU testing, and what was time-boxed out:** installing
Nix itself on the local host, or using `nixos-rebuild build-vm`/`nix build .#...config.system.build.vm`,
was ruled out up front as the slower path (bootstrapping a Nix installation on a non-NixOS Fedora
host is its own yak-shave). The official minimal ISO plus a real `nixos-install` — the same shape
the Kairos/Flatcar/Bottlerocket legs used for their own systems — was faster and gives a fully
real generation history to test against, not a synthetic one.

One real blocker, found and fixed rather than worked around: `nixos-install --no-channel-copy`
(used to skip copying the live ISO's channel into the target, to save time) leaves the installed
system with no `nixpkgs` entry in its Nix search path, so `nixos-rebuild` fails immediately with
`file 'nixpkgs' was not found in the Nix search path` — and because the first attempt piped that
failure through `tail`, the shell's exit code came back `0` and looked like success until the
actual command output was read. Fixed with `nix-channel --add https://nixos.org/channels/nixos-24.11
nixos && nix-channel --update` on the installed system before the first `nixos-rebuild switch`.
Noted here so the next run touching NixOS on a similar setup doesn't lose time to the same masked
failure.

**Labeled per the repo's evidence convention: every result below is REPRODUCED** — live commands
against a running VM at every stage (install, mark, upgrade, rollback, reboot), not documentation
alone — except where marked NOT TESTED.

## Results

**Generation 1 (the install).** `nixos-install` produced
`/nix/store/dyhpaaqd...-nixos-system-gen1-host-24.11...`, hostname `gen1-host`, no `cowsay`.
Three markers written before touching anything further: `/etc/rollback-marker.txt`
(`MARKER_GEN1_ETC`), `/var/lib/rollback-marker/marker.txt` (`MARKER_GEN1_VAR`), and
`/home/marker/rollback-marker.txt` (`MARKER_GEN1_HOME`, owned by an unprivileged `marker` user
created for this purpose).

**There is no partition boundary between these three paths, or between any of them and the Nix
store.** `mount` shows a single `/dev/vda2` ext4 filesystem mounted at both `/` and (read-only)
`/nix/store` — confirmed live, not assumed from the install layout. Every other system in this
ticket drew its persistence line at a partition or deployment boundary (Flatcar's `ROOT`
partition, Bottlerocket's data partition, bootc/FCOS's per-deployment `/etc`). NixOS draws no
such line at all: `/etc`, `/var`, `/home` and the Nix store all sit on the same disk, and what
"survives a rollback" is decided entirely by which files the activation script's managed list
touches, not by where those files physically live.

**The `/etc` mechanism, read directly off the running system:**

```
/etc/hostname -> /etc/static/hostname
/etc/static/hostname -> /nix/store/zhv1wq4gp1r4rx6d8lnjnm3avndbcvc4-etc-hostname
/etc/static -> /nix/store/lb67z3ca9hcnd2wv5w918jlcz7nw8gsy-etc/etc
```

A file NixOS manages (`environment.etc.*`, plus stock files like `hostname`, `hosts`,
`nsswitch.conf`) is a **two-hop symlink**: `/etc/<name>` points at `/etc/static/<name>`, and
`/etc/static` itself is one symlink that gets re-pointed, atomically, at the new generation's
`etc` derivation every time `nixos-rebuild switch` runs its "setting up /etc..." step. Roll the
generation back and that one symlink moves back too, and every managed file under it reverts in
the same instant, without walking or diffing the tree.

`/etc/rollback-marker.txt`, by contrast, is a **plain regular file** (`ls -la` confirms
`-rw-r--r--`, not `lrwxrwxrwx`) sitting directly on the ext4 filesystem. It was never part of any
`etc` derivation, so activation has no reason to ever touch it — not on upgrade, not on
rollback, not ever. This is a third `/etc` model, distinct from every other system in this
ticket: not a persistent on-disk overlay untouched by upgrades (Flatcar), not an ephemeral tmpfs
reseeded every boot (Kairos, Bottlerocket), not a whole directory that moves with the deployment
and gets reselected on rollback (bootc, Fedora CoreOS) — but a **per-file managed set,
reconciled by symlink redirection on every activation, that leaves anything outside that set
alone indefinitely.**

**The upgrade.** `configuration.nix` changed `networking.hostName` to `gen2-host` and added
`pkgs.cowsay` to `environment.systemPackages`; `nixos-rebuild switch` built and activated
generation 2 (`nixos-system-gen2-host-...`). Confirmed live: `/etc/hostname` now reads
`gen2-host`, `cowsay` is on `PATH` and runs, `/nix/var/nix/profiles/system` now points at the
generation-2 closure, and `nix-env --list-generations -p /nix/var/nix/profiles/system` lists
both generations with `2` marked `(current)`. All three markers read back unchanged
(`MARKER_GEN1_ETC`/`VAR`/`HOME`) — the upgrade only ever touches what the new generation's `etc`
derivation and package closure define.

**The boot entry, read directly from the installed GRUB config:** before the upgrade,
`grub.cfg` had one `menuentry "NixOS"` (the default) and one `"NixOS - Configuration 1"` entry.
After the upgrade it gained a second: `"NixOS - Configuration 2 (2026-09-22 - 24.11...)"`. Each
generation gets its own named menu entry, confirming the "boot entry per generation" model
directly rather than inferring it from the CLI output — this is the literal boot-entry half of
"a generation is a Nix store closure plus a boot entry."

**The rollback: `nixos-rebuild switch --rollback`.** One command, run live: output was
`switching profile from version 2 to 1 / updating GRUB 2 menu... / activating the configuration...
/ setting up /etc...`. Confirmed immediately after: `/etc/hostname` back to `gen1-host`, `cowsay`
gone from `PATH`, `/nix/var/nix/profiles/system` back to the generation-1 closure, and
`nix-env --list-generations` shows generation 1 marked `(current)` again. All three markers still
read their original `GEN1` values, untouched through the entire upgrade-then-rollback cycle.

**Durability, confirmed with a real cold reboot, not just the live profile switch:** after
`reboot` (a plain guest reboot, no manual boot-menu interaction), the system came back on
generation 1 by itself — `readlink -f /nix/var/nix/profiles/system` and `readlink
/run/current-system` both pointed at the generation-1 closure, hostname was `gen1-host`,
`cowsay` was still absent, and all three markers were still intact. **`nixos-rebuild switch
--rollback` writes a durable default**, exactly like `switch` does for a forward upgrade — this
puts NixOS in the same "durable flip" category as bootc, Fedora CoreOS, and Flatcar, and
distinct from Kairos's and Bottlerocket's one-shot `next_entry`/`upgrade-to-inactive` semantics,
which auto-revert unless a separate "mark successful" step fires.

**NOT TESTED, disclosed rather than hidden:** manually selecting an older "Configuration N"
GRUB entry at the boot menu, rather than using `nixos-rebuild switch --rollback` to update the
default. The structural evidence for that path is solid — `grub.cfg` genuinely lists one
selectable entry per generation, confirmed by reading the file — but this leg didn't drive GRUB's
interactive serial menu the way it drove the installed system's own shell, since the durable,
fully-reproduced `--rollback` path already answers the series' real question (what survives a
generation change) without that extra step. A future pass could add it; it would test the same
mechanism from the boot-menu side rather than the command-line side, not a different mechanism.

## What this settles for NixOS

- A NixOS "rollback" is a **generation switch**: a Nix store profile symlink move
  (`/nix/var/nix/profiles/system`) plus a GRUB default-entry update, both performed atomically
  by the same tool (`nixos-rebuild switch --rollback` / `switch-to-configuration`) that performs
  a forward upgrade. It is not an A/B image swap and has no partition-level analogue in the
  other five systems in this series.
- **Retention is unbounded, not one-shot.** Every past generation's closure stays addressable
  (`nix-env --list-generations`) until explicitly garbage-collected — a sharper guarantee than
  every A/B system in this series, all of which keep exactly one fallback.
- `/etc` persistence is **per-file and symlink-mediated**, not partition-based and not
  time-based. A file NixOS's configuration declares (`environment.etc.*`, `networking.hostName`,
  etc.) reverts precisely and atomically on rollback, because it's a symlink into a per-generation
  Nix store path. A file nothing declares is a plain file on disk that no activation script will
  ever touch, upgrade or rollback alike — the practical effect is closer to "permanently
  persistent" than any other system in this series, since there is no tmpfs reseed (Kairos,
  Bottlerocket) and no deployment-directory swap (bootc, FCOS) to ever threaten it.
- The rollback is **durable across a real reboot**, confirmed by actually rebooting rather than
  trusting the CLI's own report — putting NixOS alongside bootc/FCOS/Flatcar's durable-flip
  category, not Kairos/Bottlerocket's auto-reverting one-shot category.

## Cross-system comparison, now that all six legs are done

The six systems split cleanly on two independent axes, and NixOS is the one system that breaks
the pattern on both:

**What a rollback reverts:**
- **Whole root image**, one prior version only: Kairos, Bottlerocket (both auto-revert unless
  marked successful — the one-shot group).
- **`/usr` only**, writable root never touched: Flatcar.
- **OSTree deployment**, `/var` shared, `/etc` three-way-merged forward but *not* reverted by a
  rollback (which reselects, rather than recomputes, an existing deployment): bootc, Fedora
  CoreOS.
- **A Nix store closure plus one symlink**, unbounded generation history, every past generation
  addressable, not just one: **NixOS** — a different unit entirely, not a bigger or smaller
  version of the other five.

**What happens to `/etc` specifically**, the sharpest comparison point this whole ticket
produced:
- **Ephemeral, reseeded from a template every boot**, survives nothing by default: Kairos,
  Bottlerocket.
- **Persistent, on-disk, structurally outside the update mechanism's reach**: Flatcar.
- **Moves with the deployment**, merged forward on upgrade, reselected (not reverted) on
  rollback: bootc, Fedora CoreOS.
- **Individually symlinked per managed file, reconciled by redirection on every activation,
  unmanaged files never touched at all**: NixOS — neither ephemeral nor a single persistent
  blob, but a declared allow-list enforced at the file level.

A reader who only sees "has rollback: yes" for all six systems is comparing a one-shot image
flip, a durable deployment reorder, and an unbounded generation switch as if they were the same
feature. They aren't, and the six legs of this series are the concrete evidence for why not.
