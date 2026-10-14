# Talos Linux: what the API-only management contract actually buys

Platform profile, "representative" tier.
Tracked as , sub-issue of the research epic.
Research date: 2026-09-16.
Versions: `talosctl` v1.14.1 (client), node image `ghcr.io/siderolabs/talos:v1.14.1`, source read at tag `v1.14.1` of `siderolabs/talos`, documentation read at `docs.siderolabs.com/talos/v1.14`.
Seeds public series post #5 ("Talos: what changes when Kubernetes becomes part of the machine-management contract").

---

## Why this document has the structure it has

No project-profile template exists.  was meant to produce one and was closed, superseded by the Pulse brief, before it did. the platform-profile task (NixOS), the platform-profile task (Unikraft), the platform-profile task (Azure Linux) and the Secure Boot key-ownership task (Secure Boot key ownership) each designed a structure for their own question and recorded that choice in-document. This follows the same precedent rather than inventing a shared template nobody asked for.

The structure here is driven by one thing that makes this profile different from its siblings: **the evidence comes from two sources with different strengths, and they do not overlap.**

A live two-node Talos cluster was created, configured, poked at and destroyed on the research host today. That produced REPRODUCED and OBSERVED evidence about bootstrap, the configuration model and the boundaries of container-mode Talos. It produced nothing at all about upgrade and rollback, because the provisioner used — Docker — architecturally cannot perform an upgrade, and Talos refuses to try.

So the upgrade and rollback sections below are DOCUMENTED only, from Talos's own source and documentation, and they say so in every paragraph. The live mechanic — what actually happens on reboot, whether rollback actually restores a working node, what actually survives in `/var` — is NOT TESTED here and would need a QEMU-based pass with root on the host. That gap is stated plainly rather than smoothed over, which is the honest shape for a representative-tier profile: the ticket asked for representative lifecycle experiments, not the full break/recover cycle the deep-core three get.

Where a claim comes from reading Talos's Go source rather than its prose documentation, the file and line are given. Source is a primary source, and for several questions here it is a better one than the docs, because two of the most load-bearing findings below contradict what the documentation still implies.

Evidence labels are the ones defined in `research-framework.md`: DOCUMENTED, REPRODUCED, OBSERVED, INFERRED, UNKNOWN, NOT TESTED.

The sibling Pulse survey profile (`data/projects/talos.yaml`, collected 2026-09-15) already covers Talos across fourteen dimensions with sources. Nothing here duplicates it; everything load-bearing was verified independently against source or primary docs.

---

## The experiment that was run

`talosctl cluster create --provisioner docker`, one control plane and one worker, image `ghcr.io/siderolabs/talos:v1.14.1`, on the shared Docker daemon of the research host. Destroyed afterwards with `talosctl cluster destroy`. Two unrelated long-running containers on the same daemon (a riscv64 AuroraBoot build fleet and a buildkit builder) were confirmed untouched before and after.

**Bootstrap worked end to end on the first attempt.** PKI generation, etcd bootstrap, kubelet, control plane static pods, kube-proxy and coredns all reached healthy with no manual intervention. REPRODUCED.

**A configuration change applied to a running node without a reboot.** `talosctl patch machineconfig` adding `machine.sysctls."net.core.somaxconn": "4096"` returned `Applied configuration without a reboot`, and the value was present in `talosctl get machineconfig -o yaml` afterwards. REPRODUCED.

That string is not marketing copy, it is the server's own response text for the `NO_REBOOT` apply mode, emitted at [`internal/app/machined/internal/server/v1alpha1/v1alpha1_server.go:246`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/internal/server/v1alpha1/v1alpha1_server.go#L246). DOCUMENTED.

**`talosctl upgrade` was refused**, with `rpc error: code = FailedPrecondition desc = method is not supported in container mode`. REPRODUCED. The rest of this section is about why that refusal is the interesting result rather than a failed experiment.

### Why container-mode Talos cannot upgrade

The error text comes from a capability check, not from anything failing part way through. `checkSupported` formats exactly that message ([`internal/app/lifecycle/lifecycle.go:248-256`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/lifecycle/lifecycle.go#L248-L256)), and the capability table it consults strips five capabilities from container mode and nothing else:

```go
// container
all ^ uint64(Reboot|Shutdown|Upgrade|Rollback|MetaKV),
```

([`internal/app/machined/pkg/runtime/mode.go:88-102`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/pkg/runtime/mode.go#L88-L102); DOCUMENTED.) Reboot, shutdown, upgrade, rollback and META writes are the five things a container-mode node is declared unable to do. Cloud, metal and metal-agent modes get all capabilities.

The reason is visible in what the Docker provisioner actually creates. Each node is a privileged container with `ReadonlyRootfs: true`, tmpfs at `/run`, `/system` and `/tmp`, and **Docker volumes** — not partitions — mounted at `/var` (the EPHEMERAL mount point) and `/system/state` (the STATE mount point) ([`pkg/provision/providers/docker/node.go:93-155`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/provision/providers/docker/node.go#L93-L155); DOCUMENTED). The container is started with `PLATFORM=container` in its environment, which is what puts the runtime into `ModeContainer`.

There is no EFI partition, no BOOT partition, no META partition, no GPT, no bootloader and no system disk. Past the capability check, the upgrade path looks up the system disk with `blockres.GetSystemDisk` and errors out if there is none ([`internal/app/lifecycle/lifecycle.go:188-198`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/lifecycle/lifecycle.go#L188-L198); DOCUMENTED). An upgrade in Talos means writing a new kernel and image into the inactive half of an A/B pair and flipping the boot target. In a container there is no pair and no boot target.

So the refusal is a design decision surfaced early and cleanly, not a limitation of the sandbox this ran in, and not a bug. INFERRED from the source above, and consistent with the REPRODUCED error.

### What testing the real mechanic would have required

`talosctl cluster create` without a provisioner defaults to QEMU, which fails immediately with `error: please run as root user (CNI, qemu hvf requirement), we recommend running with 'sudo -E'` ([`pkg/provision/providers/qemu/preflight.go:44`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/provision/providers/qemu/preflight.go#L44); REPRODUCED, and the exact string is in the source). Root plus hardware virtualisation plus CNI bridge setup on a shared host is a larger action than this ticket's tier justifies taking opportunistically, so it was not taken.

Everything in the next section is therefore documentation and source reading. NOT TESTED.

---

## Disk layout, upgrade and rollback (DOCUMENTED, NOT TESTED)

### What is on the disk

Talos's partition set is defined in one place, [`internal/pkg/partition/partition.go`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/pkg/partition/partition.go), with sizes in [`pkg/machinery/imager/quirks/partitions.go`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/machinery/imager/quirks/partitions.go). All DOCUMENTED:

| Label | Mount | Size | Purpose |
|---|---|---|---|
| `EFI` | `/boot/EFI` | 100 MiB with GRUB; 100 MiB + 1 MiB + BOOT size with UKI | ESP; under UKI it carries all boot assets |
| `BIOS` | — | 1 MiB | GRUB stage 2, BIOS layout only, rejected with UKI |
| `BOOT` | `/boot` | quirk-dependent | Kernel and initramfs for the A and B slots, GRUB layout only |
| `META` | — | 1 MiB | Small key/value store outside the config |
| `STATE` | `/system/state` | 100 MiB | Machine configuration and node identity |
| `EPHEMERAL` | `/var` | rest of disk, 2 GiB minimum | Everything writable: etcd, containerd, kubelet, logs |

The root filesystem itself is not on this list. Talos "always runs from a SquashFS image, meaning that even if a directory is mounted to be writable, the image itself is never modified" ([philosophy](https://docs.siderolabs.com/talos/v1.14/learn-more/philosophy); DOCUMENTED), with tmpfs for runtime state and an overlayfs on XFS at `/var` for the paths that must persist ([architecture](https://docs.siderolabs.com/talos/v1.14/learn-more/architecture); DOCUMENTED).

The naming is a deliberate argument, not a description. "We call the writable partition the 'ephemeral' partition precisely because we want to make sure none of us ever uses it for unique, non-replicated, non-recreatable data. Thus, if all else fails, we can always wipe the disk and get back up and running" (philosophy; DOCUMENTED). That is a statement about what operators are permitted to assume, and it is the premise the whole recovery story rests on.

v1.14 partially complicates it. `ETCD`, `CRI`, `KUBELET` and `LOG` can now be moved from directories under EPHEMERAL onto dedicated partitions via a `VolumeConfig` document, and the changelog is explicit about the consequence: "with `ETCD` on a dedicated partition, etcd data no longer lives under `EPHEMERAL`. Resetting a control plane node with only the `EPHEMERAL` partition wiped will not clear etcd data; wipe the `ETCD` volume to reset etcd" (CHANGELOG.md, "Dedicated System Volumes"; DOCUMENTED). The backing choice is fixed at cluster creation and cannot be switched later on a provisioned node.

### Two bootloaders, two rollback mechanisms

Talos ships a GRUB path and an sd-boot/UKI path, and they implement A/B differently.

Under GRUB the `BOOT` partition holds two directories, `A` and `B`, each with a kernel and initramfs, and `grub.cfg` carries `set default=` and `set fallback=` pointing at menu entries ([`bootloader/grub/encode.go`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/pkg/runtime/v1alpha1/bootloader/grub/encode.go), [`grub/grub.go:191-197`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/pkg/runtime/v1alpha1/bootloader/grub/grub.go#L191-L197); DOCUMENTED). Rollback swaps the two: `flip()` sets default to the other label and fallback to the current one, then checks the target directory exists before writing the config ([`grub/boot_label.go:27-43`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/pkg/runtime/v1alpha1/bootloader/grub/boot_label.go#L27-L43), [`grub/revert.go`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/pkg/runtime/v1alpha1/bootloader/grub/revert.go); DOCUMENTED). Validation rejects a configuration where default and fallback are the same entry.

Under sd-boot there are no A and B labels. UKIs are files on the ESP named `Talos-<version>.efi`, with `Talos-<version>~<n>.efi` when the same version is installed more than once. Rollback globs that directory, skips the entry that is currently set to boot next, and writes the first other one it finds into the `LoaderEntryDefault` EFI variable ([`bootloader/sdboot/sdboot.go:627-670`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/pkg/runtime/v1alpha1/bootloader/sdboot/sdboot.go#L627-L670); DOCUMENTED). If no other UKI is present it returns `previous UKI not found`.

That is a real behavioural difference worth carrying into the comparison: under GRUB, "the previous version" is a fixed slot; under sd-boot it is whichever other UKI file happens to still be on the ESP. the Secure Boot key-ownership task already established that Talos ships a Sidero-signed UKI with no separate shim, so the sd-boot path is the one Secure Boot users are on. How many UKIs the ESP retains in practice, and therefore how many versions back a Secure Boot node can actually roll, is UNKNOWN from source reading alone and is a good target for the QEMU pass.

`talosctl rollback` requires the `os:admin` role, probes the bootloader on the system disk, calls `Revert`, then triggers a reboot ([`v1alpha1_server.go:367-400`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/internal/server/v1alpha1/v1alpha1_server.go#L367-L400); DOCUMENTED).

### The upgrade sequence

From the [upgrade documentation](https://docs.siderolabs.com/talos/v1.14/configure-your-talos-cluster/lifecycle-management/upgrading-talos) (DOCUMENTED): the node cordons itself and drains its pods; Talos shuts down its internal processes; filesystems are unmounted; the disk is verified and the image upgrade performed; the bootloader is set to boot *once* with the new kernel and image, and the node reboots; after the node verifies itself it makes the bootloader change permanent, rejoins the cluster and uncordons. "If an upgrade fails to boot, Talos will roll back to the previous version." Talos reboots via `kexec`, so the extra reboot is cheap.

The upgrade itself is performed by a containerised installer: Talos pulls the installer image and runs `/bin/installer install --disk=... --upgrade=true ...` in a container with host network and PID namespaces, all grantable capabilities and no masked paths ([`internal/pkg/install/install.go:165-220`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/pkg/install/install.go#L165-L220); DOCUMENTED). The new OS arrives as an OCI artifact, and the thing that installs it also arrives as an OCI artifact.

Two findings here matter more than the sequence.

**The upgrade no longer wipes anything, and `--preserve` is a dead flag.** The installer prints `system disk wipe on upgrade is not supported anymore, option ignored` when `Force` is set in upgrade mode, and in upgrade mode `diskOperations` does not touch partitions at all beyond verifying the table is GPT ([`cmd/installer/pkg/install/install.go:217-219` and `:271-279`](https://github.com/siderolabs/talos/blob/v1.14.1/cmd/installer/pkg/install/install.go#L217-L219); DOCUMENTED). On the CLI side, `--preserve`, `--force` and `--stage` are marked deprecated and described as "legacy flag for MachineService.Upgrade fallback, to be removed in Talos 1.18" ([`cmd/talosctl/cmd/talos/upgrade.go:382-389`](https://github.com/siderolabs/talos/blob/v1.14.1/cmd/talosctl/cmd/talos/upgrade.go#L382-L389); DOCUMENTED). The current flags are `--reboot-mode`, `--no-reboot`, `--drain` and `--drain-timeout`.

Anyone carrying forward the older mental model — that a Talos upgrade wipes EPHEMERAL unless you pass `--preserve` — is working from a version of Talos that no longer exists.

**The default upgrade path now depends on a Sidero-hosted service.** As of 1.14, `ghcr.io/siderolabs/installer` is no longer published; installer images are served by the Image Factory as `factory.talos.dev/metal-installer/<schematic-id>:<version>` (CHANGELOG.md, "Default Installer Image"; upgrade docs; DOCUMENTED). The empty "vanilla" schematic is `376567988ad370138ad8b2698212367b8edcb69b5fd68c80be1f2ec7d603b4ba`.

That is a direct answer to research-framework §4's "can upgrades occur without the project's hosted infrastructure?", and the answer has two halves. By default, no: the standard upgrade command resolves an image from `factory.talos.dev`. But the Image Factory is open source and documented for on-premises deployment, needing three OCI registries and an ECDSA P-256 signing key ([Image Factory docs](https://docs.siderolabs.com/talos/v1.14/learn-more/image-factory); DOCUMENTED). The dependency is on a service, not on a vendor, and the service is self-hostable. Whether a self-hosted Factory is operationally equivalent for airgapped upgrades is NOT TESTED and belongs in the operational-independence experiment (§22) rather than here.

### Reset and recovery

`talosctl reset` wipes the machine back to a clean state, with `--graceful` (default true) cordoning, draining and leaving etcd first, and `--system-labels-to-wipe` narrowing the blast radius to named partitions — the docs specifically recommend `--system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL` on cloud VMs, because a full reset wipes the entire disk and can leave the VM unbootable ([resetting a machine](https://docs.siderolabs.com/talos/v1.14/configure-your-talos-cluster/lifecycle-management/resetting-a-machine); DOCUMENTED).

There is also an offline path that does not need the API at all. The GRUB configuration Talos writes includes a menu entry, `Reset Talos installation and return to maintenance mode`, whose command line is the running entry's plus `talos.experimental.wipe=system:EPHEMERAL,STATE` ([`grub/encode.go:66-74`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/pkg/runtime/v1alpha1/bootloader/grub/encode.go#L66-L74); DOCUMENTED). A node stuck in a boot loop can be reset from the console with no network and no working Talos API. Whether an equivalent exists on the sd-boot path — where there is no GRUB menu to select from — is UNKNOWN and worth checking, because Secure Boot users are the ones who get sd-boot.

---

## Configuration model (§6)

One YAML configuration, applied over the API, held on the STATE partition. "Everything which can be configured in Talos is done through a single YAML manifest. There is no scripting and no procedural steps" (philosophy; DOCUMENTED).

`talosctl apply-config` has four modes, and the server code for them is short enough to read in full at [`v1alpha1_server.go:200-315`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/internal/server/v1alpha1/v1alpha1_server.go#L200-L315) (all DOCUMENTED):

- `no-reboot` persists the config and sets it live.
- `staged` persists it without applying, for the next boot.
- `auto` is now an alias for `no-reboot`.
- `try` sets the config live *without* persisting it and arms a revert timer, default one minute (`ConfigTryTimeout`, [`constants.go:511-512`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/machinery/constants/constants.go#L511-L512)). If nothing re-applies before the timer fires, the node returns to its persisted configuration by itself.

`--mode=reboot` was removed in 1.14: "by default, configuration is applied without a reboot. Most configuration changes don't require a reboot; the documentation lists the changes that do" (CHANGELOG.md, "Apply Configuration Modes"; DOCUMENTED). *Most*, not all — the reproduced sysctl change says nothing about fields that still need a reboot, and that boundary was not mapped here. NOT TESTED.

`try` mode is the part worth carrying into the comparison. It is a rollback primitive at the configuration layer, separate from the bootloader-level rollback, with a dead-man timer so that a change which costs you API access to the node undoes itself. Research-framework §5 asks the projects to distinguish rollback of the OS from rollback of machine state; Talos has separate mechanisms for those two things and they are not variations on each other.

A caveat on the reproduced result: the patch used `machine.sysctls`, which 1.14 deprecates in favour of a dedicated `SysctlConfig` document, alongside a long list of other v1alpha1 fields being split into focused documents (upgrade docs, "Machine configuration changes"; DOCUMENTED). The deprecated field still works — that is what was reproduced — but the single-manifest description above is becoming a multi-document one, and a profile written against 1.16 will describe a different configuration surface.

---

## No SSH, no shell: what it buys and what it costs (§12, §20)

This is the section the ticket specifically asked not to prejudge, so here is the mechanism first and the assessment after.

### What is actually absent

"Unlike traditional Linux distributions, Talos does not have: an interactive shell (SSH); a package manager; a mutable user space; common Linux utilities by default" ([Talos for Linux admins](https://docs.siderolabs.com/talos/v1.14/learn-more/talos-for-linux-admins); DOCUMENTED). "We have no shell. We have no SSH. We have none of the GNU utilities, not even a rollup tool such as busybox... There are no passwords in Talos. All networked communication is encrypted and key-authenticated" (philosophy; DOCUMENTED). There is no systemd; PID 1 is `machined` and the service model is Talos's own.

### What is actually present

The management surface is a gRPC API with a client certificate carrying a role in its Organization field. The roles are `os:admin`, `os:operator`, `os:reader`, `os:etcd:backup`, `os:image:verifier`, `os:meta:writer` and `os:impersonator` ([`pkg/machinery/role/role.go`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/machinery/role/role.go); DOCUMENTED). API methods are mapped to role sets in a single table at [`internal/app/machined/pkg/system/services/machined.go:39-152`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/pkg/system/services/machined.go#L39) — 80 entries, each naming the roles that may call it, with `FallbackRoles` set to `os:admin` for anything not listed. `Dmesg`, `Logs`, `Processes` and `Netstat` are readable by `os:reader`; `Read`, `Copy`, `Reset`, `Rollback`, `Kubeconfig` and `DebugService/ContainerRun` are `os:admin` only. DOCUMENTED.

The docs publish a direct mapping from Linux habits to API calls (Talos for Linux admins; DOCUMENTED). Abbreviated:

| Linux | Talos |
|---|---|
| `ls` / `cat` | `talosctl list` / `talosctl read` (read-only) |
| `ps` / `top` | `talosctl processes` / `talosctl dashboard` |
| `systemctl status` / `restart` | `talosctl services` / `talosctl service restart` |
| `journalctl -u` / `-f` | `talosctl logs [-f] <service>` |
| `dmesg` | `talosctl dmesg`, or `talosctl logs kernel` |
| `ip addr` / `ip route` / `ss` | `talosctl get addresses \| links` / `get routes` / `netstat` |
| `tcpdump` | `talosctl pcap` |
| `lsblk` / `lspci` / `dmidecode` / `lsmod` | `talosctl get disks` / `get pcidevices` / `get systeminformation` / `get loadedkernelmodules` |
| `scp` | `talosctl copy` (from the node) |

`talosctl support` produces a bundle containing, per node, kernel logs, all Talos service logs, all kube-system pod logs, COSI resources with secrets removed, the COSI runtime state graph, a processes snapshot, IO pressure, mounts, PCI devices and the Talos version, plus cluster-level node and pod manifests ([`cmd/talosctl/cmd/talos/support.go:40-76`](https://github.com/siderolabs/talos/blob/v1.14.1/cmd/talosctl/cmd/talos/support.go#L40-L76); DOCUMENTED). By default it is age-encrypted to the Sidero Labs GitHub organisation members, which `--no-encryption` or `--encryption-recipients` overrides.

### There is a shell, and its shape is the actual answer

`talosctl debug <image>` starts a privileged container from an image you supply and drops you into it. "The debug container runs privileged with host PID and network namespaces... The host filesystem is mounted at `/host`... When you exit, the container is removed and the cluster continues operating normally" ([Debug Shell](https://docs.siderolabs.com/talos/v1.14/troubleshooting/talosctl-debug); DOCUMENTED). The image can be pulled by the node, or pushed to it over the API as a tarball when you are debugging the network and pulling is not an option. The backing API method, `/machine.DebugService/ContainerRun`, is `os:admin` only.

The documented worked example is running Cilium's `pwru` to trace packets through the kernel network stack, including the machine configuration patch needed to relax `kernel.kptr_restrict` first because Talos restricts it by default (Debug Shell; DOCUMENTED). NOT TESTED here — Docker-mode nodes were available but this was not exercised.

So the accurate description of the Talos model is not "you can never get a shell on the node". It is: **a shell is an explicitly requested, authenticated, admin-only, ephemeral event that brings its own tools and leaves nothing behind.** The escape hatch does not weaken the state guarantees: the container is removed on exit, and the host filesystem it browsed is a read-only SquashFS. An earlier, different debug shell was removed (`chore: drop debug shell`, commit `919d8c365`, in CHANGELOG.md), and what exists in 1.14 is the container-based replacement.

### What the constraint buys

1. **The management surface is enumerable.** Eighty methods, each with a declared role set, in one table in one file, and an admin-only default for anything absent from it. The equivalent question on an SSH host — "what can the holder of this key do?" — has no bounded answer, because the answer is "run any binary present, plus any binary they can fetch". The Talos version can be audited by reading a file. DOCUMENTED, and a material difference in kind rather than degree.

2. **Ad-hoc drift has nowhere to live.** There is no package manager, no mutable userspace and no persistent shell, so the classic failure — a node fixed by hand at 3am, working, undocumented, and different from its siblings until it is replaced — has no mechanism. The root filesystem is a signed SquashFS that is never modified. A debug container's changes die with the container. That is the strongest operational argument for the model and it is structural, not procedural: it does not depend on operators being disciplined. INFERRED from the DOCUMENTED mechanisms; not measured in a fleet.

3. **Least privilege is expressible.** `os:reader` can read every log, every resource, every process list and the kernel ring buffer, and cannot read files, copy anything off the node, reboot it or fetch a kubeconfig. Granting "look at this node and tell me what's wrong" without granting "and you can also change it" is a certificate role, not a sudoers file. DOCUMENTED.

4. **Credential handling is different in kind.** No passwords; client certificates are short-lived and automatically rotating (philosophy; DOCUMENTED). Nothing to rotate on the node, nothing to distribute, no authorized_keys drift.

### What it costs

1. **Unanticipated debugging needs a plan in advance.** An SSH host lets you install what you need at the moment you discover you need it. On Talos you need an image containing the tool, and either network access from the node to a registry or a tarball you can push. The `pwru` example is the documentation's own illustration: the tool is not in any public registry, so the documented procedure starts with `git clone` and `docker build`. That is not an unreasonable workflow, but it is a slower one, and it is worse specifically in the case where you least want friction — an unfamiliar failure on a node you have never had to look inside before.

2. **You can only see what the API exposes.** `talosctl list` "lists exposed filesystem paths only" (Talos for Linux admins; DOCUMENTED). There is no writable path and no general file access outside the debug container. The debug container widens this a lot — `/host` is the whole host filesystem — but only for `os:admin`, and only deliberately.

3. **Every operator skill is Talos-specific.** The mapping table above exists because none of the Linux knowledge transfers directly. An organisation adopting Talos adopts Talos's operational vocabulary; the framework's §20 question "can existing enterprise standards be incorporated, or must the organization adopt the project's standards?" has a clear answer here, and it is the second one.

4. **The API is a dependency.** All the debugging capability above assumes the Talos API is reachable and the node is up enough to serve it. Serial console plus the GRUB reset entry is the documented floor below that, and on the sd-boot path even that is UNKNOWN (above). What debugging is possible on a node whose API is down is NOT TESTED and is the single most valuable thing a QEMU-based pass could add.

Weighing these: the constraint is a good trade for fleets that are large, homogeneous and replaceable, where drift is the dominant cost and any individual node is disposable. It is a worse trade the more a machine is special — one-off hardware, a workload with unusual debugging needs, an environment where a node cannot simply be reset and rebuilt. That is a judgment about fit, not a ranking, and it is the shape the framework's decision-scenario section asks for.

---

## Kubernetes coupling (§7)

**Kubernetes is not optional.** A machine configuration with no `cluster` section fails validation with `cluster instructions are required`, and `ClusterConfig.Validate` is called unconditionally for every configuration ([`pkg/machinery/config/types/v1alpha1/v1alpha1_validation.go:103` and `:381-386`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/machinery/config/types/v1alpha1/v1alpha1_validation.go#L103); DOCUMENTED). The three machine types are `init`, `controlplane` and `worker` ([`pkg/machinery/config/machine/machine.go`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/machinery/config/machine/machine.go)) — all three are Kubernetes node roles. There is no fourth type that means "a Talos machine that is not part of a cluster". Applying a configuration outside maintenance mode also requires a v1alpha1 document to be present, enforced at [`v1alpha1_server.go:211-212`](https://github.com/siderolabs/talos/blob/v1.14.1/internal/app/machined/internal/server/v1alpha1/v1alpha1_server.go#L211-L212).

Talos says the same thing about itself: "This is achievable because Talos is tightly focused to do one thing: run Kubernetes, in the easiest, most secure, most reliable way it can" (philosophy; DOCUMENTED).

v1.14 moved a little, though, and it is worth recording precisely because it moves along the axis this whole investigation is organised around. The new `ContainerConfig` document "declares a container to be run by Talos directly, without Kubernetes. The container is started as soon as the configuration is applied, with no image rebuild and no reboot. It runs against the CRI containerd instance in the dedicated `taloscontainers` namespace, and is restarted automatically 5 seconds after it stops" ([`pkg/machinery/config/types/container/container_config.go:50-63`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/machinery/config/types/container/container_config.go#L50-L63); DOCUMENTED).

So a Talos node can now run host-level containers outside Kubernetes, declaratively, with the same no-reboot apply semantics. It still cannot run *without* Kubernetes. On the framework's spectrum — Kubernetes appliance ↔ Kubernetes-oriented OS ↔ general immutable infrastructure substrate — Talos remains at the appliance end, with the qualification that the appliance now has a documented slot for workloads that are not Kubernetes pods. INFERRED from the source and changelog; the feature is new and was not exercised.

OS and Kubernetes upgrades are independent: "an upgrade of the Talos Linux OS will not (since v1.0) apply an upgrade to the Kubernetes version by default" (upgrade docs; DOCUMENTED), with `talosctl upgrade-k8s` as the separate command. The OS owns the machine lifecycle; Kubernetes does not manage the OS. That is the opposite arrangement from a node-lifecycle-via-CRD model, and it means a broken Kubernetes does not cost you the ability to manage the machine — the Talos API is independent of it. That last clause is INFERRED from the architecture rather than tested; deliberately breaking Kubernetes and then managing the node is one of §21's failure experiments and is NOT TESTED here.

---

## Construction, customisation and the extensibility envelope (§2, §3, §20)

The unit of deployment is one image. "The entirety of Talos is distributed as a single, self-contained image, which is versioned, signed, and immutable", and the system is "atomic in *deployment* and *modular* in *composition*" (architecture; DOCUMENTED). The SquashFS is under 80 MB (philosophy; DOCUMENTED, not independently measured here).

Customisation happens at image build time through the Image Factory. A **schematic** is a YAML document listing extra kernel arguments, initial META values, system extensions and an optional hardware overlay; it is content-addressed, so uploading the same schematic twice returns the same ID. A **model** is a schematic plus a Talos version plus an asset type — ISO, kernel/initramfs, UKI, a disk image for a given cloud, or an installer container image (Image Factory docs; DOCUMENTED). The Factory verifies signatures on every source image it pulls, signs its own cached and generated assets, verifies those signatures before serving, and deliberately provides no way to list schematics, since a schematic can contain private kernel arguments and its ID is unguessable without its content.

A running node reports its own schematic: the Factory injects a virtual `schematic` extension whose version is the schematic ID, so `talosctl get extensions` answers "what image is this machine running, exactly" with a content hash (Image Factory docs; DOCUMENTED). That is a genuinely good property for the reproducibility question this funnel is about, and it is worth comparing against how other projects answer the same question.

The extensibility envelope is an allowlist. An extension's rootfs may only contain paths under a fixed list in [`pkg/machinery/extensions/extensions.go:10-34`](https://github.com/siderolabs/talos/blob/v1.14.1/pkg/machinery/extensions/extensions.go#L10-L34), and anything else is rejected at build time with `path %q is not allowed in extensions`. The list is 17 entries: `/etc/cri/conf.d`, `/usr/lib/firmware`, `/usr/lib/modules`, the glibc loaders for x86-64 and aarch64, `ldconfig` and the `ld.so` config and cache, `/usr/lib/udev/rules.d`, `/usr/local`, `/usr/share/glvnd`, `/usr/share/egl`, `/etc/vulkan`, and six specific nvidia binaries by name. World-writable and special files are rejected outright. DOCUMENTED.

The six hardcoded nvidia paths show what the allowlist costs: widening the envelope for a new vendor requires an upstream change to that list. Talos carries that maintenance burden in exchange for knowing exactly what an extension can touch. Whether it scales is a question about the project's throughput rather than its architecture, and is outside this ticket.

On the framework's APPLIANCE ↔ CONSTRUCTION KIT axis, Talos sits close to the appliance end by construction: the set of decisions an operator can override is a finite list, and it is enumerated in source.

---

## CNCF status, verified

The ticket's claim checks out, with one addition worth getting into the record.

**Talos is not a CNCF-hosted project.** Verified directly against `landscape.yml` in `cncf/landscape` (retrieved 2026-09-16). CNCF-hosted entries carry a `project:` key with the maturity level and an `accepted:` date — Kairos, for example, has `project: sandbox` and `accepted: '2024-04-13'` (landscape.yml, line ~238). The Talos Linux entry (line ~9344) has no `project:` key at all. It is a landscape listing, which is open to any relevant project regardless of affiliation. DOCUMENTED, machine-verifiable by grepping that file.

**Talos is referenced by CNCF TAG Runtime's Special Purpose OS working group.** The [WG charter](https://tag-runtime.cncf.io/wgs/spos/charter/) names six "popular open-source projects that are in the container OS space": Bottlerocket, Flatcar, Talos, Kairos, openSUSE MicroOS and Google's Container-Optimized OS. The charter does not assert anything about the hosting status of any of them. DOCUMENTED.

**Talos does hold a CNCF mark, and it is a different one.** Its landscape entry sits under Platform / Certified Kubernetes - Distribution, with a second path under Certified Kubernetes - AI Platform (landscape.yml; DOCUMENTED). CNCF Certified Kubernetes is a conformance certification for the Kubernetes distribution Talos ships, granted per release against the conformance test suite. It is not project hosting and does not imply CNCF governance.

For the TAG paper: Talos belongs in the SPOS working group's scope discussion and in any conformance-related statement, and must not appear in a "CNCF projects" list. The distinction is easy to get wrong in one sentence, because Talos is simultaneously in the CNCF landscape, named in a CNCF TAG working group charter, and CNCF-certified — and hosted by none of it.

---

## What this profile does not establish

Stated plainly so it is not mistaken for coverage:

- **The upgrade was never run.** No reboot behaviour, no A/B flip, no `kexec` path, no boot-once-then-make-permanent, no automatic rollback on failed boot. All of that is DOCUMENTED and NOT TESTED.
- **The rollback was never run.** `talosctl rollback` was not invoked against any node.
- **Nothing is known first-hand about what survives an upgrade.** `/var`, etcd data, container images, machine identity on STATE — the mechanisms are read, the outcome is not observed.
- **None of §21's failure experiments were performed.** No power cut mid-upgrade, no corrupted image, no unbootable kernel, no broken Kubernetes after upgrade, no full disk.
- **The debug container was not used.** The §12 argument above rests on documentation, not on having debugged anything.
- **How many versions an sd-boot node can roll back through is unknown**, and so is whether an offline console reset exists on that path.
- **Which configuration fields still require a reboot was not mapped.**

A single QEMU-mode pass with root on a dedicated host would close most of this: `talosctl cluster create qemu`, upgrade, observe, roll back, observe, then the failure injections. That is a well-defined follow-up and it does not need to be opportunistic.

---

## Notes for the epic

**Two facts here contradict widely repeated descriptions of Talos** and should be checked wherever they appear in draft comparisons: upgrades no longer wipe EPHEMERAL and `--preserve` is a deprecated no-op; and the default installer image now comes from `factory.talos.dev` rather than `ghcr.io`.

**One Kairos comparison is implied and needs maintainer review before publication.** This document argues that the operational value of Talos's constraint is structural rather than procedural — that drift has no mechanism, as opposed to being discouraged. Any general-purpose immutable OS that ships a shell and package tooling reaches the same guarantee by policy instead, which is a different kind of guarantee. That framing invites a direct Kairos comparison, and Mauro maintains Kairos, so it should not be published in comparative form without a maintainer factual-review pass. I have deliberately not made the comparison here.

**One methodological note for the framework.** §12 says "do not assume SSH is inherently good or 'no SSH' inherently good", and the dimension is currently phrased as a presence/absence question. Talos 1.14 does not fit that shape: the useful distinction is not whether a shell exists but what its lifetime, authentication and persistence are. If §12 stays binary, Talos will be scored wrong in either direction depending on which sentence of its own marketing is quoted. Suggesting the dimension be restated as "what is the lifetime and authorisation model of interactive access", which the other projects can also answer.
