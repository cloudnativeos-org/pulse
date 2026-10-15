# NixOS: reproducibility and immutability are different axes, and the framework currently measures one of them

Platform profile, "challenge the premise" tier.
Part of the research epic.
Research date: 2026-09-16.
Versions read: nixpkgs `release-26.05` and `master`, Nix reference manual 2.34.9, NixOS manual (stable). Where a claim rests on a file that exists only on `master`, this document says so.
Seeds public series post #7 ("NixOS: do we need immutability, or do we actually need reproducibility?").

---

## Why this document has the structure it has

No project-profile template exists for this tier. The methodology plan was supposed to produce one and was closed, superseded by the Pulse brief before it did. The Pulse's 14-dimension YAML schema is a survey instrument and the wrong shape for an argument, and this ticket's own brief says not to force NixOS through the same template as the deep experimental core. So I designed the structure below myself: question, mechanism, one section per operator guarantee, verdict, implications.

Recording that here rather than in an issue comment, because the Unikraft profile (also a "different paradigm" tier) may want to reuse or deliberately diverge from this shape, and the next author will read the document before they read the ticket thread.

The per-guarantee structure is the load-bearing choice. A dimension-per-section layout would have reproduced the framework's existing categories, and the point of this ticket is to test whether one of those categories is well formed.

## Scope and method

Everything here comes from the NixOS manual, the Nix reference manual, nixpkgs source, NixOS RFCs and NixOS release notes. I read module source directly wherever the manual was thin, which for this subject it often is.

**I did not run NixOS.** No Nix installation exists on the research host and installing one would mean changing the host, which is out of scope for this lane. Nothing in this document is labelled REPRODUCED or OBSERVED. Claims derived from reading code that I did not execute are labelled INFERRED and NOT TESTED together, so they are visibly weaker than the manual quotes.

The sibling deliverable `data/projects/nixos.yaml` already covers NixOS at survey depth across 14 dimensions, with sources. I have not duplicated it. Where I cite it I say so, and everything load-bearing to the argument below I verified against primary sources myself. One finding contradicts a detail in it, and I flag that explicitly in the "known state" section.

Evidence labels are the ones defined in `research-framework.md`: DOCUMENTED, REPRODUCED, OBSERVED, INFERRED, UNKNOWN, NOT TESTED.

## The question, restated so it can be answered

The ticket asks whether NixOS reaches the same operator guarantees that the image-based systems get from immutability, through a different mechanism.

"Immutability" cannot be compared directly, because it is not one property. The Pulse already demonstrated this with data: Flatcar makes only `/usr` read-only, Bottlerocket makes the whole root read-only and puts `/etc` on a tmpfs that does not survive reboot, Google COS has a read-only root with a writable but stateless `/etc`, and Azure Linux has none of it (the Pulse brief closing comment; DOCUMENTED in the sibling profiles, not independently re-verified here). Four systems, one checkbox, four architectures.

So this document compares four guarantees instead, and asks about each one separately:

1. **Known state.** Can an operator determine what the machine is running, and is that answer trustworthy?
2. **Atomic transition.** Can the machine move from one known state to another without passing through a state that is neither?
3. **Rollback.** Can the machine return to a previous known state, and what surface does that cover?
4. **Integrity.** Can an operator tell whether the machine has been altered, and can alteration be prevented?

These are the properties a Kubernetes node operator actually buys when they buy an immutable OS. Each is reachable by more than one mechanism.

## How NixOS names a system and how it changes one

Three things carry state in NixOS, and conflating them is where most commentary on this subject goes wrong.

**The store object.** A directory under `/nix/store` whose name begins with a hash. "Store objects are immutable: Once created, they do not change nor can any store object they reference be changed" (Nix reference manual, store objects; DOCUMENTED). The default hash is *input*-addressed, computed from the build dependency graph rather than from the output bytes: a store path name is "a cryptographic hash of the package's build dependency graph" (Nix reference manual, introduction; DOCUMENTED). Content-addressing exists as a separate mode and is not the default (Nix reference manual, content-addressing store objects; DOCUMENTED). This distinction matters later and is routinely stated wrong.

**The closure and the system derivation.** A NixOS configuration evaluates to one top-level store path, `config.system.build.toplevel`, whose transitive references are the entire operating system. One hash names the complete system: kernel, initrd, every binary, every generated file in `/etc`, the activation script and the systemd unit set. That is a single identifier for a whole machine's software, and it is the closest thing NixOS has to an image digest.

**The generation and the profile.** Each built system is linked as `/nix/var/nix/profiles/system-N-link`, and `/nix/var/nix/profiles/system` points at the current one (NixOS manual, rolling back configuration changes; DOCUMENTED). Generations are numbered, retained until garbage collection, and each gets a bootloader entry.

`nixos-rebuild switch` then does the following, in this order (NixOS manual, "What happens during a system switch"; DOCUMENTED):

1. Build the new system closure.
2. For `switch` and `boot`, install the bootloader first, "so the configuration will be the next one to boot". Unless `NIXOS_NO_SYNC=1`, sync `/nix/store` to disk.
3. For `switch` and `test`, read `/etc/fstab` and the live systemd state, and compute the difference against the desired configuration.
4. Carry out a fixed action sequence: stop units, run the activation script, re-exec systemd if needed, `reset-failed`, `daemon-reload`, reload user instances, restart `sysinit-reactivation.target`, reload units, restart units, start units.
5. "Inspect what changed during these actions and print units that failed and that were newly started."

Step 5 matters for what comes later. The command's terminal state includes a list of units that failed, so the operation is defined to be able to partially fail and continue.

Four verbs separate the three things a transition can do (`nixos-rebuild(8)`; DOCUMENTED):

| Verb | Builds | Activates the running system | Becomes the boot default |
|---|---|---|---|
| `build` | yes | no | no |
| `test` | yes | yes | no |
| `boot` | yes | no | yes |
| `switch` | yes | yes | yes |

That separation is unusually fine-grained, and the `boot` row is the one that matters most for the comparison below.

---

## Guarantee 1: known state

### What NixOS actually guarantees

A configuration, evaluated against pinned inputs, produces a specific system closure identified by one hash. That is a strong and checkable claim, and it is the claim NixOS makes on its own front page: reproducible, declarative, reliable. The word "immutable" is absent from it (nixos.org; DOCUMENTED via the sibling profile).

An operator has real state-inspection primitives:

- `readlink /run/current-system` names the closure the system last activated.
- `readlink /run/booted-system` names the closure that booted. Stage 2 writes it: `ln -sfn "$systemConfig" /run/booted-system` (nixpkgs `nixos/modules/system/boot/stage-2-init.sh`; DOCUMENTED). Comparing the two tells you whether an activation has happened since boot, which is a fact no image-based system exposes in one command, because in an image-based system the question cannot arise. That reading of the comparison is INFERRED from the source; the symlinks themselves are DOCUMENTED.
- `nixos-rebuild list-generations --json` prints generation number, build date, NixOS version, kernel version and configuration revision (`nixos-rebuild(8)`; DOCUMENTED).
- `nix-store --verify --check-contents` recomputes a SHA-256 over every valid store path and compares it against the hash recorded at build time (Nix reference manual, `nix-store --verify`; DOCUMENTED).

### What it does not guarantee

None of the above tells you that the machine matches its configuration. It tells you which configuration was last applied.

The gaps are defaults, not obscure options:

- `users.mutableUsers` defaults to `true`. Accounts created with `useradd` are merged into the generated configuration on activation rather than replaced (nixpkgs `nixos/modules/config/users-groups.nix`; DOCUMENTED).
- `nix-env -iA` installs into a profile that sits outside the declarative configuration entirely. The manual is direct about the consequence: other packages in the profile "are *not* affected" by a channel update, and "this is the crucial difference with the declarative style of package management" (NixOS manual, ad-hoc package management; DOCUMENTED).
- The root filesystem is an ordinary writable filesystem. `/var`, `/home` and anything a service writes are outside the model.
- `system.stateVersion` records the first NixOS version installed on that particular machine and is deliberately never changed afterwards: "Most users should **never** change this value after the initial install, for any reason" (nixpkgs `nixos/modules/misc/version.nix`; DOCUMENTED). Two machines with byte-identical configurations and different install histories therefore evaluate to different closures.

That last one deserves more than a bullet. `stateVersion` exists because NixOS takes the mutable-state surface seriously: it pins the *defaults* of packages whose on-disk data formats cannot migrate automatically, so an upgrade does not silently rewrite a database into a format the previous generation cannot read. No other system in this investigation has a mechanism that treats the undescribed part of the machine as a versioned thing at all. It is simultaneously the best state-handling idea I found and a direct admission that the configuration does not fully determine the machine.

### One correction to the sibling profile

The sibling profile records `/etc` as "generated at activation but writable" and says there is "no drift detection and no reconciliation loop". The first half is right. The second half is too strong for `/etc` specifically, and the difference is operationally relevant.

Reading `nixos/modules/system/etc/setup-etc.pl` (DOCUMENTED as source; the behavioural conclusion INFERRED, NOT TESTED):

- `/etc/static` is atomically re-pointed at the new generation's etc tree.
- Every managed entry is then recreated by `atomicSymlink` or by a copy plus `rename`, which replaces whatever is currently at that path. A hand-edited managed file is therefore clobbered.
- Dangling symlinks into `/etc/static` from a previous configuration are removed, and files that were copied in a previous generation but are not in the current one are deleted, tracked through `/etc/.clean`.
- Anything else in `/etc` that a human created is never touched.

And the activation script "is executed on every boot and system switch" (NixOS manual, activation script; DOCUMENTED). So managed `/etc` entries are reconciled at every single boot, without an agent and without a control plane. Unmanaged entries persist forever.

This puts NixOS's `/etc` closer to Google COS's "writable but stateless" model than the survey framing suggests, for the subset of files the configuration names. It is still not drift *detection*, because nothing reports that a file was clobbered, and it covers none of `/var`, `/opt`, user profiles or the store. It is worth a REPRODUCED test before anyone publishes it.

### Is "declarative configuration" the same claim as "known machine state"?

No. They are related by an implication that only runs one way. A known machine state implies some description exists that produced it. A declarative description does not imply the machine still matches it, because nothing in the architecture prevents divergence and nothing reports it.

For a Kubernetes-node-style guarantee the gap is load-bearing, and the reason is about incident response rather than purity. When a node misbehaves, the operator's first question is whether this node differs from its 200 siblings. On a verity-enforced root the answer is structurally "no, except in the named writable paths", and the investigation can start somewhere else. On a default NixOS node the answer requires checking the store, the root profile, every user profile, `/etc` for unmanaged files, and `/var`. That is not impossible. It is a different kind of work, and it does not get cheaper at 200 nodes.

**Verdict on guarantee 1: weaker, by default, and the weakness is deliberate.** NixOS gives a stronger *description* of the intended state than any image-based system here, and weaker *evidence* that the machine conforms to it.

---

## Guarantee 2: atomic transition

"Atomic updates" is the phrase most often attached to NixOS, and it is true of a smaller object than people assume.

### What is actually atomic

- Store object creation. A store object exists completely or not at all, and never changes afterwards (Nix reference manual; DOCUMENTED).
- The profile symlink swap from `system-N-link` to `system-(N+1)-link`.
- The `/etc/static` symlink swap, and each individual `/etc` entry's `rename` (setup-etc.pl; DOCUMENTED as source).

### What is not

The transition of the running system. The action list in the previous section is a sequence of `systemctl` calls around an arbitrary bash activation script, and it terminates by printing which units failed. There is no transaction and no rollback of a partial activation. If a unit fails to start, the machine is running generation N+1's `/etc`, N+1's unit files, and a service that is down.

The activation script itself is arbitrary code, runs as root on every boot, and the project is trying to get rid of it: reloading or restarting systemd units from the activation script is deprecated and will be removed in NixOS 26.11, "part of a bigger effort to deprecate activation scripts altogether, which will take place over several releases" (NixOS 26.05 release notes; DOCUMENTED).

### The project's own admission, shipped as a feature

NixOS 26.05 introduced switch inhibitors: a pre-switch check that compares a list of strings between the old and new generation and "refuses to switch into the new generation when there is a difference between the two lists" (NixOS 26.05 release notes; DOCUMENTED). The suggested use in the release note is `config.systemd.package.version`, so that a systemd upgrade cannot be applied live. There is at least one in-tree consumer already: changing `services.dbus.implementation` "is a **switch inhibitor**: switching between implementations requires a reboot rather than just `nixos-rebuild switch`, because restarting D-Bus mid-session is unsafe" (same source; DOCUMENTED).

The check's own message says what to do instead: "There are changes to critical components of the system... Switching into this system is not recommended. You probably want to run 'nixos-rebuild boot' and reboot your system instead" (nixpkgs `nixos/modules/system/activation/switchable-system.nix`; DOCUMENTED). `NIXOS_NO_CHECK=1` overrides it.

### What "atomic" is scoped to, on each side

In NixOS, atomicity is a property of *naming*. The new system is named atomically. Becoming it is not atomic.

In an A/B image system, atomicity is a property of the *boot pointer*. Becoming the new system is also not instantaneous, but the machine passes through a reboot, so userspace is never a mixture of two generations. You get the old system or the new one.

NixOS can have the second property. `nixos-rebuild boot` builds the closure, installs the bootloader entry and makes it the default without touching the running system (`nixos-rebuild(8)`; DOCUMENTED). Reboot, and the transition has the same shape as an A/B flip: a pointer swap, then a clean boot into a complete generation. The `image-based-appliance` profile takes this to its conclusion by removing `switch-to-configuration` from the system entirely (`nixos/modules/profiles/image-based-appliance.nix`; DOCUMENTED).

So the honest statement is: NixOS's transition model is a superset. It contains an A/B-equivalent path and, in addition, a live path that is not atomic and that the project is currently adding guardrails to. The live path is the feature NixOS has and the image systems do not, and it is also the only part of the transition model that is weaker.

**Verdict on guarantee 2: equal if the operator chooses `boot` and reboots, weaker if they choose `switch`.** The choice is per-invocation and is not enforced. Nothing in the architecture stops an operator from switching a production node live; a pre-switch check on a handful of named values is not the same as an architecture that has no live path.

One thing I could not establish: what happens on power loss between the bootloader install and the profile swap, or during the ESP write with GRUB's `copyKernels` enabled. The store paths already exist at that point, so my expectation is that the machine boots either the old or the new generation cleanly, but I did not test it and there is no documented statement. INFERRED, NOT TESTED. It is a good candidate for the failure-experiment protocol if this tier ever gets one.

---

## Guarantee 3: rollback

### The mechanism

Every previous generation stays bootable until garbage-collected, and they are listed in the boot menu under "NixOS - All configurations". The manual recommends exactly this when a new configuration fails to boot, and tells the operator to run `switch-to-configuration boot` from the recovered generation to make the selection stick (NixOS manual, rolling back configuration changes; DOCUMENTED). From a running system, `nixos-rebuild switch --rollback` is equivalent to invoking the previous generation's own `switch-to-configuration` (same source; DOCUMENTED).

Ordinary garbage collection does not remove this. The manual states that `nix-collect-garbage` "do[es] not remove garbage collector roots... Thus they do not remove the ability to roll back to previous configurations" (NixOS manual, cleaning the store; DOCUMENTED via the sibling profile's citation, and consistent with the retention behaviour described in the rollback chapter).

### Same guarantee, weaker, or different in kind?

Different in three specific ways, two favouring NixOS.

**Depth.** An A/B system's rollback budget is architecturally one, because there are two slots. NixOS's is a disk-space policy. GRUB's `configurationLimit` defaults to 100 and systemd-boot's defaults to `null`, meaning "no limit i.e. all generations that have not been garbage collected yet" (nixpkgs grub.nix and systemd-boot.nix; DOCUMENTED). This is a consequence of the store model rather than a feature: an old generation costs only the store paths it does not share with newer ones, so keeping fifty is cheap in a way that keeping fifty partition images is not.

The unbounded default is also a real hazard. The boot partition fills up, and the failure mode arrives during an upgrade, which is the worst time.

**Automation.** There is none by default. Boot counting exists on systemd-boot as an opt-in option with `tries` defaulting to 3: new entries are written with a counter in the filename, systemd-boot decrements it on each boot, `systemd-bless-boot.service` clears it once `boot-complete.target` is reached, and an entry whose counter hits zero "is considered bad and will be skipped in favour of an older generation" (nixpkgs `nixos/modules/system/boot/loader/systemd-boot/systemd-boot.nix`; DOCUMENTED). I found no equivalent on the GRUB path, where the documented recovery is a human at the boot menu. Whether one exists: UNKNOWN.

This is the sharpest operational difference in the whole comparison. An unattended fleet needs the machine to decide. NixOS gives an operator more options to choose from and, by default, nothing that chooses on their behalf.

**Surface.** Rollback reverts the system closure. It does not revert `/var`, `/home`, a database schema, or an unmanaged file in `/etc`. Managed `/etc` entries do come back, because activating generation N re-runs N's etc setup.

The same hole exists on the other side. The Pulse brief recorded that a Flatcar OS rollback does not revert `/etc`, `/opt` or `/var` (DOCUMENTED in the sibling profile, not re-verified here), and filed the question as FR-13, "what does an OS rollback actually revert". Arriving at the same boundary from the NixOS side is a useful independent confirmation that FR-13 is the right question rather than a Flatcar quirk.

NixOS is the only system I have looked at that has a named mechanism aimed at this hole. `stateVersion` does not roll state back; it reduces how often state formats change under a machine in the first place. That is a different and arguably better answer to the same problem, and it is the strongest candidate in this document for "exceeds".

One documented limit on going backwards: a newer NixOS may carry a newer Nix with a database schema upgrade, and "this cannot be undone easily, so in that case you will not be able to go back to your original channel" (NixOS manual, upgrading; DOCUMENTED). Generation rollback is not the same as downgrade, and the tool that owns the store is itself state.

**Verdict on guarantee 3: deeper and more local than A/B, and less automatic.** For an attended machine, better. For an unattended fleet node, worse out of the box, and fixable with one option on one of the two bootloaders.

---

## Guarantee 4: integrity and tamper resistance

This is where the mechanisms are least comparable, and where the word "immutable" does the most damage to the discussion.

### What the store gives

`/nix/store` is bind-mounted with `ro,nodev,nosuid` by default. The option's own description says `ro` "enforces immutability of the Nix store", and then says the thing that matters: "This affects the whole system except the nix store daemon, which will undo the bind mount" (nixpkgs `nixos/modules/system/boot/stage-2.nix`, `boot.nixStoreMountOpts`; DOCUMENTED).

So the read-only mount is a hygiene boundary against accidental writes and against processes that are not the daemon. It is not an integrity boundary against root, and it was not built to be one. Reading that as equivalent to a dm-verity root is a category error, and it is a common one.

### What content addressing does and does not give

Nix's default store paths are input-addressed. The hash is over the build dependency graph, not the output. That gives you a strong, checkable statement about *provenance*: this path is what this exact set of inputs produces. It does not by itself give you a statement about *the bytes currently on disk*, because the name was never derived from them.

What covers that is a separate, explicit operation. `nix-store --verify --check-contents` "checks that the contents of every valid store path has not been altered by computing a SHA-256 hash of the contents and comparing it with the hash stored in the Nix database at build time", and `--repair` will "try to repair the path by redownloading it" (Nix reference manual; DOCUMENTED).

That combination is genuinely something dm-verity does not have. Verity detects corruption at read time and fails closed; it cannot heal, and its granularity is the whole protected filesystem. Nix can identify exactly which store paths are wrong and fetch replacements for those paths, leaving everything else alone. On a machine with a network and a corrupted package, that is a better outcome than a failed boot.

It is also much weaker as a security property, for three reasons:

1. It is on-demand. Nothing checks anything at read time.
2. The trust anchor is the Nix SQLite database, which lives on the writable root filesystem. An attacker with root who alters a store path and its database entry defeats the check. INFERRED from the documented mechanism, NOT TESTED.
3. It is not chained to firmware. Secure Boot is not configured by either bootloader module by default; the implementation lives in a community project outside the NixOS organisation (DOCUMENTED in the sibling profile, not independently re-verified here).

### Build reproducibility is a fourth, separate claim

Reproducible builds are a stated project goal, with a dedicated site: the objective is that "compiling from the same source on independent infrastructure yields bit-by-bit identical results" (reproducible.nixos.org; DOCUMENTED). The page carries no percentage figure (DOCUMENTED that the page has none; the actual current rate is UNKNOWN, and the sibling profile records that the linked dashboard's newest evaluation was months old at its snapshot).

Substitution is signature-gated by default: `require-sigs` defaults to `true`, so "any non-content-addressed path added or copied to the Nix store... must have a signature by a trusted key", with `cache.nixos.org-1` as the default trusted key, and `sandbox` defaults to `true` (Nix reference manual, configuration file; all DOCUMENTED). Those two defaults are better than several peers in this investigation.

But build reproducibility and runtime immutability are answers to different questions. The first says a third party can independently produce the artifact and check it matches. The second says the machine cannot depart from the artifact. Neither implies the other. NixOS demonstrates the independence directly: by default it holds one of the strongest positions in this investigation on the first (complete declarative description, pinned inputs, signature-gated substitution, sandboxed builds, documented offline closure transport) and one of the weakest on the second (writable root, mutable users, imperative profiles, no Secure Boot). The comparative ranking is INFERRED from the sibling profiles rather than measured; the individual properties on both sides are DOCUMENTED.

**Verdict on guarantee 4: different in kind, not weaker or stronger as a unit.** NixOS has verifiable provenance and per-path detect-and-repair, with no enforcement and no chain of trust by default. A verity-based system has enforcement and a chain of trust, with no ability to say where the bytes came from or to fix one of them.

---

## What NixOS does when it needs the appliance guarantees

Everything above describes the default generation model. NixOS also ships, in the stable release, a complete second model, and reading it is the single most useful thing I did for this ticket.

The manual states the position plainly, in the chapter on building images:

> The generation based update mechanism of NixOS is not suited for appliances. Updates of appliances are usually either performed by replacing the entire image with a new one or by updating partitions via an A/B scheme.

(NixOS manual, building images via `systemd-repart`; DOCUMENTED. The chapter then links the Chrome OS update process as the example to follow.)

Three modules implement the alternative, all present on `release-26.05` as of 2026-09-16 (verified by fetching each from the `release-26.05` branch; DOCUMENTED):

**`nixos/modules/profiles/image-based-appliance.nix`.** Its header comment: "An appliance is installed as an image, cannot be re-built, has no Nix available, and is generally not meant for interactive use. Updates to such an appliance are handled by updating whole partition images via a tool like systemd-sysupdate." It sets `nix.enable = false`, `system.switch.enable = false`, `users.mutableUsers = false`, and defaults systemd in the initrd and `networkd` on. Three of the four escape hatches from the "known state" section are closed by those four lines.

**`nixos/modules/image/repart-verity-store.nix`.** "An opinionated module that can be used to build nixos images with a dm-verity protected nix store." It builds the store as an erofs `usr` partition with a paired verity hash partition, embeds the resulting root hash into the UKI's kernel command line as `usrhash`, and adds a build-time assertion comparing the UKI's cmdline against the repart output so that a mismatched pair cannot be produced. The `/nix/store` is then a bind mount from `/usr/nix/store`.

**`nixos/modules/system/boot/systemd/sysupdate.nix`.** A module for `systemd-sysupdate`, described in its own option text as "Atomically update the host OS, container images, portable service images or other sources", with a timer and an optional automatic reboot after a new version is installed.

Put together, these produce a machine with a verity-protected read-only store measured into a UKI, immutable users, no package manager, no `switch-to-configuration`, and A/B partition updates. That is an image-based immutable OS. It is built by Nix, from a declarative description, deterministically, but the running model is the one the deep experimental core uses.

The interpretation is mine and is INFERRED, though the modules and the manual sentence are DOCUMENTED: **when NixOS needs the operator guarantees this investigation is about, it does not extend the generation model to reach them. It abandons the generation model and adopts image-based immutability, keeping Nix as the build system.**

I found no evidence that this is a marginal or experimental path. `repart-verity-store.nix` has two named maintainers, `image-based-appliance.nix` is a first-class profile, and the manual has a chapter on it. Whether the project considers the verity module supported, and whether its root hash is signed anywhere, I could not determine (UNKNOWN; also raised as an open question by the sibling profile).

---

## The structural verdict

The comparison does not show that reproducibility substitutes for immutability, and it does not show that NixOS falls short of immutability. It shows that the two words name properties on different axes, and that the framework's dimension 1 currently collapses them.

**Axis R, derivability.** Can the operator recreate the artifact they are running, from a description they control, and check that the result matches? Sub-questions: is the description complete, is it versioned, is the build deterministic, can a third party verify.

**Axis E, enforcement.** Does the running machine provably correspond to that artifact, and what happens when it does not? Sub-questions: prevented, detected, or neither; what is the trust anchor; what is the blast radius of an escape hatch.

All four quadrants are populated, which is the test of whether the axes are real:

- **High R, low E.** Default NixOS. The strongest description of intended state in the investigation, no enforcement.
- **Low R, high E.** A vendor-fixed image under dm-verity, where the operator can verify what they received and cannot regenerate it. The Pulse's hyperscaler entries sit near here.
- **Low R, low E.** A conventional distribution, which is where most infrastructure still is.
- **High R, high E.** NixOS's own appliance profile plus the verity store module. Also where an image-based system with a genuinely reproducible build would sit.

Naming both axes makes two claims visible that the single word hides.

The first is the one the ticket expects: an OCI digest or a partition hash is an identifier, not a recipe. It says the artifact you received is the artifact that was built. It says nothing about whether you could build it again. For most image-based OS pipelines the honest answer to "rebuild this exact artifact from its source description" is no, because the build resolved package versions from a repository at build time and that repository has moved. The digest was pinned after the fact. Nix pins before the fact, which is a different and stronger property, and it is the property the epic's title already names.

The second cuts the other way and matters more for this investigation's own bias controls: the image-based systems are not getting credit for reproducibility by accident, they are getting credit for *enforcement* and the word "immutable" is doing both jobs. Separating the axes takes something away from NixOS's claim too. Reproducing a closure is not the same as constraining a machine, and no amount of declarative rigour becomes enforcement on its own.

So: **reproducibility is not a sufficient substitute for immutability for the operator guarantees this investigation cares about. It is a complementary property on an orthogonal axis, and the strongest available evidence for that is that NixOS, the system with the most reproducibility, ships a separate image-based immutable mode for exactly the cases where enforcement is required.**

The category was underspecified from the start. "Immutable OS" is not wrong, it is a compression of at least three independent things: what is enforced read-only, how the artifact is derived, and how a transition is committed. The Pulse already proved the first one varies wildly across systems that all use the same word. This document adds that the second varies just as much and is not correlated with the first.

---

## What this implies for the investigation

**Replace dimension 1 with the two axes.** The framework's dimension 1 ("Definition and implementation of immutability") asks ten good questions, but it asks them under one heading, so a profile answers them as one verdict. Split it: an enforcement dimension (what is read-only, what enforces it, what is the trust anchor, can drift occur, is it detected) and a derivability dimension (what is the description, what pins it, can the operator rebuild the artifact, can a third party verify the rebuild). Dimension 15 already asks half of the second one under "supply-chain ownership", so the material exists and is in the wrong place. Every project then gets a position on both, and "immutable: yes" stops being writable.

**The epic's title was already right and its first question was not.** "Reproducible Machine State" names the axis the investigation is actually about, and then dimension 1 asks about enforcement. That is not a small mismatch. If the two-axis model holds, the TAG paper's page 2 ("architectural models") should show each system's position on both, which is a more useful diagram than a per-project pipeline drawing and takes less space.

**FR-13 gets stronger, and gets a second angle.** "What does an OS rollback actually revert" arrived independently from the Flatcar side in the Pulse brief and from the NixOS side here. Both systems revert the OS and leave `/var`. NixOS has a partial answer (`stateVersion`) that nothing else in the set has. That makes FR-13 a comparison with a real finding available rather than a survey of four "no"s, and it is the strongest candidate for the fourth public post ("Recovery and rollback: what counts as known-good?").

**A NixOS appliance node is unprofiled territory.** Nothing I found profiles NixOS's verity-appliance path as a Kubernetes node OS. It is the configuration that would actually compete with the deep experimental core, and it is not what anyone means when they say "NixOS in production". If the series makes the argument above, someone will ask, and there is currently no evidence either way. UNKNOWN, and worth its own ticket.

**A precision the public post needs to keep.** The thing that competes with an image-based OS here is Nix as a build system, not NixOS as a running model. Nix is a better answer than a Containerfile to "derive this artifact reproducibly, under my own control, and let a third party check it". It is not an answer to "stop this machine from drifting", and NixOS does not claim it is. Collapsing those two into "NixOS vs Kairos" is the mistake the post exists to prevent, and it is an easy one to make in a headline.

---

## Where NixOS is a different sufficient answer, and where it is strictly weaker

For a Kubernetes-appliance use case specifically, meaning an unattended fleet node whose job is to run kubelet and be replaceable.

**Genuinely different and sufficient:**

- Rollback depth. Selecting generation 43 from a boot menu with no network, no second partition and no management plane is a capability, not a workaround, and it is not reachable in an A/B architecture at any price.
- Specialisations. A configuration can build additional named variants alongside itself, each with its own boot entry, switchable at runtime via `/run/current-system/specialisation/<name>/bin/switch-to-configuration test` (nixpkgs `nixos/modules/system/activation/specialisation.nix`; DOCUMENTED). "The same node, with the other kernel, one reboot away" has no A/B equivalent, because both slots are already spoken for by previous and next. For a GPU fleet or a driver bisect, that is directly useful.
- `stateVersion`, as discussed. The only mechanism in the investigation so far that versions the undescribed part of the machine.
- Per-path verify and repair. Fixing one corrupted store path beats failing closed, when the machine has a network.

**Strictly weaker, by default, for this use case:**

- No enforcement. A root process can write anywhere outside the store, and inside it through the daemon.
- No drift detection or reporting.
- No automatic rollback unless boot counting is enabled, and it exists on only one of the two bootloaders.
- No Secure Boot by default (DOCUMENTED in the sibling profile).
- Live `switch` is available on a production node and nothing prevents its use.
- No in-tree fleet orchestration, inventory, staged rollout or health gating; the companion tooling is spread across four organisations with differing maturity (DOCUMENTED in the sibling profile).
- No official published network-boot artifacts (DOCUMENTED in the sibling profile).

The appliance profile closes the first, third (partially, via sysupdate's reboot handling), fourth (via the UKI) and fifth of those. It does not close drift reporting, fleet orchestration or provisioning, and it gives up `nixos-rebuild`, the ability to roll back to generation 43, and specialisations, because it removes Nix from the machine. The two models do not compose. An operator picks one.

---

## Claims that need review before publication

Flagging these per the epic's bias control. I am not publishing, and these needed the named review before publication.

**Needs a Kairos maintainer (Mauro or another):** this document contains no Kairos-specific claim. That is deliberate. Every comparison above is against an archetype ("an A/B image system", "a verity-enforced root"), because I did not research Kairos for this ticket and had no basis for a specific claim. The two-axis verdict does imply something about Kairos, and it should be stated by whoever does profile it in the platform-profile task rather than asserted here: an OCI-native artifact model scores well on axis R only to the extent that rebuilding the Containerfile reproduces the same image, and that is an empirical question about the base and the package repositories, not a property of using OCI. Someone should check it on Kairos before the TAG paper claims reproducibility for anything in the deep core, including Kairos. **This is a methodological warning, not a finding about Kairos.**

**Needs a NixOS maintainer, if the series post makes these claims:**

- The `/etc` reconciliation reading from `setup-etc.pl`. It contradicts the common framing and my own sibling deliverable, and I have not run it.
- The characterisation of the appliance profile and verity store module as the project's answer for appliance-grade guarantees. The modules and the manual sentence are documented; calling it "the project's position" is my inference.
- Whether the verity module's root hash is signed, and whether the module is supported.

**Needs no review, already the project's own words:** "The generation based update mechanism of NixOS is not suited for appliances", and the switch-inhibitor release note.

---

## Open questions and what would settle them

Ordered by how much they would change the argument.

1. **Does managed `/etc` actually get clobbered on every activation and every boot?** Settles the single strongest anti-drift claim in this document. A ten-minute test on a VM: edit a managed file, run `nixos-rebuild switch` with no configuration change, check. Would move the claim from INFERRED to REPRODUCED. Currently NOT TESTED.
2. **What happens on power loss between the bootloader install and the profile swap?** The framework's failure-experiment 1. Currently INFERRED and NOT TESTED, and I would not publish a claim about it.
3. **Has anyone run the verity-appliance configuration as a Kubernetes node?** UNKNOWN. Determines whether NixOS belongs in the deep-core conversation at all or only as a build system.
4. **Is there boot counting or any automatic rollback on the GRUB path?** UNKNOWN. Materially changes the guarantee-3 verdict for anyone not using systemd-boot.
5. **What is the current reproducible-build percentage?** UNKNOWN. Axis R's headline claim currently has a stated goal and no published current measurement, which is a weaker position than the ecosystem generally assumes.
6. **Is the dm-verity store module supported, and is its root hash signed?** UNKNOWN. Without a signature the verity root hash is integrity without authenticity, and the UKI would have to carry the trust.
7. **Does an image-based-appliance NixOS still get `stateVersion`'s benefit?** It has no Nix and no rebuild, so the mechanism's purpose is unclear in that mode. Not investigated.

---

## Sources

Primary, read directly for this document:

- NixOS manual, "What happens during a system switch", `nixos/doc/manual/development/what-happens-during-a-system-switch.chapter.md`
- NixOS manual, "Unit handling", "Activation script", "Non Switchable Systems", "/etc via overlay filesystem", same directory
- NixOS manual, "Rolling Back Configuration Changes", `nixos/doc/manual/administration/rollback.section.md`
- NixOS manual, "Boot Problems", `nixos/doc/manual/administration/boot-problems.section.md`
- NixOS manual, "Ad-Hoc Package Management", `nixos/doc/manual/configuration/ad-hoc-packages.section.md`
- NixOS manual, "Upgrading NixOS", `nixos/doc/manual/installation/upgrading.chapter.md`
- NixOS manual, "Building Images via systemd-repart", `nixos/doc/manual/installation/building-images-via-systemd-repart.chapter.md`
- NixOS 26.05 release notes, `nixos/doc/manual/release-notes/rl-2605.section.md`
- nixpkgs source: `nixos/modules/system/boot/stage-2.nix`, `nixos/modules/system/boot/stage-2-init.sh`, `nixos/modules/system/etc/setup-etc.pl`, `nixos/modules/config/users-groups.nix`, `nixos/modules/misc/version.nix`, `nixos/modules/system/activation/switchable-system.nix`, `nixos/modules/system/activation/specialisation.nix`, `nixos/modules/system/boot/loader/systemd-boot/systemd-boot.nix`, `nixos/modules/system/boot/loader/grub/grub.nix`, `nixos/modules/profiles/image-based-appliance.nix`, `nixos/modules/image/repart-verity-store.nix`, `nixos/modules/system/boot/systemd/sysupdate.nix`
- `nixos-rebuild(8)`, `pkgs/by-name/ni/nixos-rebuild-ng/nixos-rebuild.8.scd`
- Nix reference manual 2.34.9: store objects, content-addressing store objects, introduction, `nix-store --verify`, configuration file
- https://reproducible.nixos.org/

Secondary, cited as such:

- `data/projects/nixos.yaml`, 
-  closing comments, for the Flatcar, Bottlerocket, COS and Azure Linux immutability facts and for FR-13
