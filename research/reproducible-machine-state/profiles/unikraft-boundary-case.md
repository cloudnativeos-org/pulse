# Unikraft: is the general-purpose host OS the right unit of deployment?

Boundary-case profile for the Reproducible Machine State investigation
(),
written for .
Seeds public series post #8.

Research date: 2026-09-16. Versions examined: Unikraft core `v0.21.0` (Ijiraq, released
2026-05-20) and the `staging` branch as of the research date; KraftKit as of the same date.

## Status and structure

This is not a survey. A compact fourteen-dimension factual profile of Unikraft already
exists as part of the cloud native OS Pulse 2026
(, file
`data/projects/unikraft.yaml`, unmerged on `feat/issue-813-pulse-profiles`),
and this document does not repeat it. Where the Pulse establishes a fact, this document
cites it and moves on. Where a fact is load-bearing for an argument here, it was re-verified
against a primary source on 2026-09-16 and is cited to that source directly.

**On document structure.**  was supposed to produce a standardised
project-profile template and was closed without producing one, superseded by the Pulse brief. There is
therefore no template to follow.  (the NixOS sub-issue under the same
epic) hit the same gap and resolved it by designing a structure appropriate to its own
question and recording that as an explicit decision. This document follows that precedent.
The structure here is organised around the research framework's twenty-two dimensions used
as an applicability checklist, which is what the platform-profile task asks for, rather than around a profile
shape that would imply Unikraft is being scored against the other nine projects. It is not.

**Evidence labels** follow `research-framework.md`, evidence standard section: DOCUMENTED,
REPRODUCED, OBSERVED, INFERRED, UNKNOWN, NOT TESTED. Nothing here is REPRODUCED — this
tier does not require the build/provision/break/recover cycle and none was run. Claims
labelled OBSERVED come from reading the project's source trees through the GitHub API on
2026-09-16, which is verification of what is and is not in the tree, not of runtime
behaviour.

**Bias control.** Mauro maintains Kairos. Comparative claims involving Kairos are collected
in a single section at the end and flagged for maintainer review before any of this is
published.

## The question

The framework asks how modern infrastructure systems make machine state reproducible,
replaceable and recoverable. Every dimension in it takes for granted that there is a
machine: a thing with persistent storage, a boot path, an identity, an upgrade history, and
a lifetime longer than the workloads it carries. Unikraft is in the study because it appears
to remove that thing.

It does not remove it. It requires a hypervisor, and the hypervisor runs on a machine that
still has all of those properties and is simply out of the project's scope. Most of what
follows is working out which of the framework's questions survive that relocation.

## What Unikraft actually is

Unikraft is a build system and a library operating system, not an operating system you
install. The project describes its output as "specialized OS images, known as unikernels,"
each being "a single-address space binary object: it does not have separation between kernel
and user address spaces which allows for much faster execution."
[DOCUMENTED — [unikraft.org/docs/concepts](https://unikraft.org/docs/concepts)]

The construction model is a port of the Linux kernel's Kconfig system applied to a catalogue
of micro-libraries. The build system "provides a Kconfig-based menu for users to select which
micro-libraries to use in an application build, for them to select which platform(s) and CPU
architectures to target," then "compiles all of the micro-libraries, links them, and produces
one binary per selected platform." Micro-libraries implement named Unikraft APIs, and "all
micro-libraries that implement the same API are interchangeable" — so the C library, the
memory allocator, the scheduler, the network stack and the filesystem are all selections
rather than givens. Schedulers are pluggable to the point that "each CPU core can run a
different scheduler."
[DOCUMENTED — [unikraft.org/docs/internals/architecture](https://unikraft.org/docs/internals/architecture)]

A production image "contains no shell, no unneeded system services, no unneeded system calls
or OS features."
[DOCUMENTED — [unikraft.org/docs/concepts/security](https://unikraft.org/docs/concepts/security)]

One correction to the common description, including the one in the platform-profile task's own ticket text.
Saying there is "no process model at all" is too strong. `lib/posix-process` exists in the
tree and its Kconfig exposes `LIBPOSIX_PROCESS_MULTITHREADING`, `LIBPOSIX_PROCESS_EXECVE`,
`LIBPOSIX_PROCESS_SIGNAL` (marked EXPERIMENTAL) and `LIBPOSIX_PROCESS_MULTIPROCESS`, the
last of which depends on a VFS and pulls in `execve` and locking.
[OBSERVED — [lib/posix-process/Config.uk on staging](https://github.com/unikraft/unikraft/blob/staging/lib/posix-process/Config.uk), read 2026-09-16]
The accurate statement is that a process model is an optional, build-time-selectable
micro-library rather than a property of the system, and a minimal image does not include
one. That distinction matters for the audit below, because it means several "there is no X"
answers are really "X is a compile-time option that a minimal image declines," which is a
different kind of absence.

Two routes exist for running existing software. Recompilation builds an application against
musl and links its object files into the unikernel through a modular syscall shim. Binary
compatibility runs unmodified Linux ELFs, with documented limits: x86_64 only with aarch64
in development, position-independent executables only, KVM as the sole supported hypervisor,
and "a slight performance hit." The shim implements "160+ syscalls."
[DOCUMENTED — [unikraft.org/docs/concepts/compatibility](https://unikraft.org/docs/concepts/compatibility)]

The deployment target is a hypervisor. The in-tree platform directories are `kvm`, `xen` and
`native`; the architecture directories are `x86`, `x86_64`, `arm` and `arm64`, with no
riscv64 tree.
[OBSERVED — [unikraft/unikraft tree, staging](https://github.com/unikraft/unikraft/tree/staging), read 2026-09-16]
Bare-metal execution, which is what `native` points toward, is described by the project's own
FAQ as "We are working towards having Unikraft run baremetal."
[DOCUMENTED — [unikraft.org/docs/faq](https://unikraft.org/docs/faq)]

Packaging is standard OCI: "It is possible to access pre-built and to distribute yourself
unikernel images using the OCI Image Specification," multi-target projects produce a
multi-platform image, and `kraft pkg push` sends it to a registry.
[DOCUMENTED — [unikraft.org/docs/cli/packaging](https://unikraft.org/docs/cli/packaging)]

The CLI's command set is worth stating precisely, because an absence in it carries a lot of
weight later. The top-level commands in the KraftKit source tree are `build`, `clean`,
`cloud`, `compose`, `events`, `fetch`, `lib`, `login`, `logs`, `menu`, `net`, `pause`, `pkg`,
`ps`, `remove`, `run`, `set`, `start`, `stop`, `system`, `unset`, `version`, `volume` and `x`.
[OBSERVED — [unikraft/kraftkit internal/cli/kraft](https://github.com/unikraft/kraftkit/tree/staging/internal/cli/kraft), read 2026-09-16]
There is no `upgrade`, no `update` of an instance, and no `rollback`. `pkg update` refreshes
the component manifest list, which is a different operation.

## The applicability audit

Verdicts are: **applies** (the framework's question works as written), **transformed** (the
question has an answer but the answer is a different kind of thing than the framework
expects), **collapsed** (the question is answered entirely by another dimension), and **not
applicable** (the question presupposes something that does not exist here).

| # | Dimension | Verdict | One-line reason |
|---|---|---|---|
| 1 | Definition/implementation of immutability | transformed | Immutable because no mutation path exists, not because a mechanism forbids one |
| 2 | Unit of OS deployment | transformed | The unit is a workload, not a machine; "OS release" has no referent |
| 3 | OS construction and customization | applies | The project's deepest dimension; entirely build-time |
| 4 | Upgrade mechanism | not applicable | No upgrade state machine exists; replacement is the only operation |
| 5 | Rollback and recovery | not applicable | No retained versions, no boot slots, no recovery environment, no device to reset |
| 6 | Configuration model | collapsed into 3 | OS configuration *is* the build; only instance parameters remain at run time |
| 7 | Kubernetes coupling | transformed | Never a node OS; a workload format Kubernetes can schedule |
| 8 | Hardware/platform support | applies, answered by the host | Guest sees virtio/Xen front-ends; real hardware is the hypervisor host's problem |
| 9 | Security and chain of trust | applies | Fewer links in the chain, and no cryptographic continuity along it |
| 10 | Provisioning and zero-touch | not applicable | Starts from powered-off hardware; there is no hardware in the model |
| 11 | Fleet lifecycle | not applicable to the project | No agent, no enrolment, no control-plane client in a built image |
| 12 | Debugging and day-2 operations | transformed | Interactive access gone; attached debugging better than a host OS |
| 13 | Persistent state and storage | transformed | The boundary is drawn at the image, with nothing on the stateful side by default |
| 14 | Networking | applies, thinly | Bridge networking and static kernel-cmdline parameters |
| 15 | Supply-chain ownership and reproducibility | applies | Strongest rebuild story in the study; no verification story at all |
| 16 | Governance and ownership | applies unchanged | Nothing about unikernels touches this |
| 17 | Project health and sustainability | applies unchanged | Same |
| 18 | Operational lifecycle and support horizon | applies, and gets harder | Patch unit moves from per-machine to per-workload-image |
| 19 | Resource footprint and performance | applies, with the largest margins in the study | Sub-2MB images, 2–6MB memory, sub-millisecond guest boot |
| 20 | Extensibility versus constraint | transformed | Past the construction-kit end of the axis, and the constraint binds the developer |
| 21 | Failure experiments | 5 of 10 do not parse | The failure space shrinks because the state space shrinks |
| 22 | Operational independence experiment | applies, 3 of 9 verbs collapse | INSTALL, ROLLBACK and RECOVER all become "redeploy" |

### 1, 2, 3 and 6: the collapse the ticket predicted

The ticket flagged "OS construction and customization" and "unit of OS deployment" as likely
to collapse into each other. They do, and configuration collapses into them as well.

For a host OS these are three separable acts at three separable times. You construct an OS,
you publish it as an artifact, and you configure a machine that runs it. Each has its own
tooling, its own failure modes and its own drift surface. In Unikraft they are one act. The
Kconfig selection and the Kraftfile produce the binary, the binary is the artifact, and the
artifact contains its own configuration. There is no point between construction and running
at which an OS exists as a separately configurable thing.

Dimension 6's four-way split of image / machine / runtime / cluster configuration reduces to
two. Image configuration is Kconfig plus the Kraftfile, at build time. Instance configuration
is what the VMM is handed at launch: kernel command-line arguments, environment variables,
volume attachments and network parameters, for example
`kraft run image netdev.ipv4_addr=172.88.0.2 -- -c /path/to/config`
[DOCUMENTED — [unikraft.org/docs/cli/running](https://unikraft.org/docs/cli/running)].
There is no cloud-init, no Ignition, no first-boot configuration pass, and no persistent
configuration store. The framework's question "can configuration drift occur" has the
answer "not for OS configuration, because there is nowhere for it to drift to" — which is
the same answer as "there is no runtime OS configuration at all," stated optimistically.

Dimension 1 deserves a precise statement, because "immutable" here means something
different from what it means anywhere else in this study. Image-based host OSes enforce
immutability with a mechanism: a read-only mount, dm-verity, an OSTree commit, an A/B
partition pair. The mechanism exists because there is a writer to defend against. Unikraft
has no mechanism and does not need one, because the image is a statically linked binary and
nothing in the running system can write to it. The default root filesystem is held in memory
via `ramfs` "and therefore it is not persistent"; the `einitrd` variant compiles the
filesystem archive into the binary itself
[DOCUMENTED — [unikraft.org/docs/cli/filesystem](https://unikraft.org/docs/cli/filesystem)].

That is immutability by absence of a mutation path rather than by policy or by cryptography,
and it has a cost the framework's dimension 9 picks up: no verity means no tamper
*detection* either. A host OS with dm-verity can tell you its root filesystem was modified.
A Unikraft image cannot tell you anything about itself, because there is nothing in it that
checks.

The framework's last sub-question under dimension 1 — "how can an operator determine the
actual state of a running machine?" — is the only one that gets harder rather than easier.
Everywhere else in this dimension the unikernel model gives degenerate answers. Here it
gives a worse one, and that is dimension 12's territory.

### 4 and 5: not applicable, and the guarantees that replaces

Dimension 4 asks for a complete upgrade state machine across four phases. None of the phases
exist. There is no inactive partition, no bootloader to update, no running filesystem to
change, and no point at which power loss can leave persistent storage in an inconsistent
state, because nothing is being written to persistent storage. The project documents no
upgrade mechanism and the CLI has no verb for one
[OBSERVED — command list above].

The two sub-questions that do survive are the ones about trust rather than mechanism. "How
is the artifact verified?" — nothing verifies it. No signing, no verification on pull, no
SBOM, no provenance attestation
[DOCUMENTED — the packaging documentation contains no digest, signing or verification
language; corroborated by the Pulse's search of the KraftKit source tree for signing,
verification and attestation terms, which returned no matches]. "Who initiates the upgrade?"
— whatever orchestrates instances, which is outside the project.

Dimension 5 is more interesting because of *why* each part fails to apply, and the reasons
are not the same reason four times.

- Rollback to a previous OS version means redeploying an earlier image. That is an
  orchestrator action, and it is exactly what it would be for any stateless OCI workload.
  The concept survives; it just leaves the project's scope entirely.
- Automatic rollback on failed boot requires a bootloader tracking boot attempts across
  reboots of a persistent system. The guest has no bootloader — the VMM loads the binary
  directly as a kernel. Nothing could count attempts because nothing survives between them.
- A recovery environment requires a shell. A production image has none, by design and by
  documentation.
- Factory reset requires persistent device identity. There is none.

The framework's summarising question is "what is the project's definition of a known-good
state?" Unikraft has no definition, and does not need one, because the question presupposes
state that accumulates. Every instance starts from the same known state, which is the image.
That is genuinely a stronger position than any host OS in the study can reach — obtained by
giving up the ability to be a machine.

### 7: inverted rather than transformed

The framework places systems on a spectrum from Kubernetes appliance to general immutable
infrastructure substrate and asks which system owns machine lifecycle. Unikraft has no
position on that spectrum. It is never the node OS. A unikernel can run *as* a Kubernetes
workload: the `runu` OCI runtime "enables container managers to run Unikraft unikernels
inside lightweight virtual machines as if they were Linux containers," registered as a
RuntimeClass and referenced from a pod spec
[DOCUMENTED — [unikraft.org/docs/getting-started/integrations/container-runtimes](https://unikraft.org/docs/getting-started/integrations/container-runtimes)].

So "can Kubernetes manage the OS lifecycle" does not parse, and "can it operate without
Kubernetes" is trivially yes, because the primary documented workflow never mentions
Kubernetes. The spectrum runs along the wrong axis: Unikraft sits one layer below both ends
of it, as an artifact producer whose output an orchestrator may schedule. The Pulse reached
the same conclusion independently and I agree with it.

Note also which side the maturity caveat falls on. The Docker path requires the containerd
image store, "currently still considered experimental." The Kubernetes path through
RuntimeClass carries no maturity label at all, which is not the same as being labelled
stable. Whether it is exercised in CI is UNKNOWN.

### 8 and 14: the dimensions where the host reappears

Dimension 8's sharpest question is "if unsupported hardware appears tomorrow, can an
organization add support itself, and how difficult is that?" For Unikraft the answer is that
the question is being asked of the wrong layer. A unikernel guest talks to virtio and Xen
front-end drivers. Real hardware — a GPU, an NPU, a RAID controller, an unusual NIC, a TPM
— is handled by the hypervisor host, and Unikraft has nothing to say about that host. The
Pulse established by source-tree search that GPU and TPM support are absent in tree, and the
architecture listing confirms the four architecture trees with no riscv64
[OBSERVED, read 2026-09-16].

Networking has the same shape. `kraft` supports bridge networking on Linux, and instance
addressing is static parameters on the kernel command line
[DOCUMENTED — [unikraft.org/docs/cli/reference/kraft/net](https://unikraft.org/docs/cli/reference/kraft/net),
[unikraft.org/docs/cli/running](https://unikraft.org/docs/cli/running)].
Bonding, VLANs, Wi-Fi, SR-IOV and RDMA do not appear in the top-level library listing
[INFERRED from the `lib/` and `plat/` listings read 2026-09-16; a full tree search was not
performed here, and the Pulse's fuller search agrees]. The framework says to pay particular
attention to edge, telco, GPU and industrial scenarios. Those are precisely the scenarios
where the guest has nothing to offer, because in all of them the interesting hardware is
attached to the host.

This is the first place the relocation shows up concretely rather than conceptually.

### 9: fewer links, no continuity

The framework traces trust through firmware → bootloader → kernel → initrd → root filesystem
→ extensions → configuration → workload. Unikraft collapses the last five of those into one
link. That is a real structural improvement to the chain: there are no joints between kernel,
initrd, rootfs, configuration and workload, so there are no joints to attack or to get out of
sync. The `einitrd` variant is explicitly argued on those grounds, removing the possibility
of injecting a different initrd at boot time
[DOCUMENTED — [unikraft.org/docs/cli/filesystem](https://unikraft.org/docs/cli/filesystem)].

The chain has no cryptographic continuity along it. There is no UEFI Secure Boot path for the
guest, no UKI, no measured boot, no TPM or PCR usage, no dm-verity, no image signature, no
remote attestation. The guest's chain of trust begins at whatever the VMM hands it, and the
VMM's own integrity is the host's problem. Separating the framework's three concepts:
tamper prevention is strong at runtime (nothing can modify a running image), tamper detection
is absent, and attestation is absent.

There is a second cost that the project's own attack-surface framing does not cover, and the
project is honest enough to gesture at it. The single address space means syscalls are
effectively function calls and there is no intra-image isolation. A memory-safety bug in the
application is a bug at kernel privilege. Cross-application isolation is the hypervisor's,
not the image's. The project states the limit of its own claim — specialization "does not
eliminate all attack vectors, it severely reduces them, especially compared to a
general-purpose OS" — and cites an external assessment critical of unikernel security rather
than ignoring it
[DOCUMENTED — [unikraft.org/docs/concepts/security](https://unikraft.org/docs/concepts/security)].
Several Linux countermeasures are marked as inapplicable by the project for the same
structural reason: KPTI, SMAP and PAN are "unnecessary because of the presence of a single
application."

The hardening status table on that page still projects "completion of most core security
features by the end of 2022," roughly four years before this snapshot, so no in-progress or
planned row on it can be treated as current
[DOCUMENTED, staleness OBSERVED 2026-09-16].

Process, not mechanism, is the larger gap. I verified the absence directly: at the root of
`unikraft/unikraft` on `staging` there is no `SECURITY.md`, no `GOVERNANCE.md`, no
`MAINTAINERS.md` and no `CODEOWNERS`
[OBSERVED — GitHub contents API, four 404s, 2026-09-16]. For a project whose headline claim
is security, there is no published vulnerability reporting address and no advisory history.

### 10 and 11: category errors, and they are different ones

Dimension 10 instructs the researcher to "start from powered-off/unprovisioned hardware."
There is no hardware. ISO, USB, PXE, network installation, OEM factory installation,
partitioning, first-boot configuration, device identity and bootstrap trust all presuppose
installing an operating system onto persistent storage, and this model never does that.
What exists instead is a VMM invocation, or `kraft run <oci-reference>`, which downloads the
image if it is not already present
[DOCUMENTED — [unikraft.org/docs/cli/running](https://unikraft.org/docs/cli/running)].

The framework's scenario question — can 5,000 identical devices leave a factory and
independently establish secure identity and desired state on first boot — has no Unikraft
answer at all, and it is worth being precise about why. It is not that Unikraft answers it
badly. It is that 5,000 devices running unikernels would be 5,000 devices each running a
hypervisor on some host OS, and that host OS is what the question is about. Unikraft would
be the thing those devices *run*, not the thing that gets provisioned.

Dimension 11 fails to apply for a different reason. It is not a category error about
hardware; it is an absence of the mechanism. A built image has no agent, no control-plane
client, and no way to phone home or be enrolled. `kraft`'s scope is a single host — listing
instances lists them on the machine the command runs on. Fleet capability at scale means
either the commercial Unikraft Cloud, whose control plane is not published, or Kubernetes
through the `runu` path — in which case the fleet lifecycle being managed is Kubernetes' and
the node OS's, and Unikraft is the payload
[DOCUMENTED, established in the Pulse's `d12_fleet_management`, which searched the
`unikraft-cloud` organisation and found clients, SDKs, an interface spec, a Terraform
provider and a Kubernetes operator published, and no server, scheduler or orchestrator].

Dimension 11's methodological instruction — label which capabilities belong to the
open-source project, an open-source companion, or a commercial product — does more work here
than anywhere else in the study, because the open-source CLI ships subcommands for
autoscaling, scale-to-zero, persistent volumes, certificates and metrics that are features of
a hosted platform reached through an open-source client. The client is open. The capability
is not.

### 12: the operator role moves

Roughly half of dimension 12's checklist does not apply: SSH, local shell, privileged
debugging containers, filesystem inspection and modification, support bundles and a rescue
environment all require a session to attach to, a process model to attach into, and a
userspace to run tools in. None of those are present in a minimal production image.

The other half is better than a host OS, not worse. Because "the application and OS are
linked into a single binary, debuggers can be used on the running unikernel to debug both
application and OS code at the same time." The build produces a `.dbg` image alongside the
stripped one, and QEMU's `-s` flag plus GDB against the debug image gives a full-system
debugger for application and kernel code in one session. Serial console output is standard
and works without networking
[DOCUMENTED — [unikraft.org/docs/internals/debugging](https://unikraft.org/docs/internals/debugging)].

So the framework's two hardest day-2 scenarios have easy answers. Debugging with broken
networking works, because the serial console never needed networking. Debugging without
Kubernetes works, because Kubernetes was never involved.

What changes is who does the debugging. A host OS day-2 problem is handled by an operator who
logs into a specific machine and looks at what that machine has accumulated. A unikernel
day-2 problem is handled by attaching a debugger from outside, or by reproducing the failure
locally against the same image, which is a developer workflow. The framework's dimension 12
is written from the operator's side. Under this model a large part of that role moves to the
developer who owns the image and to whatever schedules instances. That is an organisational
consequence of the architecture, and it is the kind of thing a "does this dimension apply"
audit surfaces that a feature comparison would not.

### 13: the boundary is drawn at the image

The framework's summarising instruction is to determine where each architecture draws the
boundary between replaceable infrastructure and stateful machine. Unikraft draws it at the
image boundary and puts nothing on the stateful side. Persistence across reboot: none by
default, the initramfs is in memory. Persistence across upgrade: the question does not parse.
Persistence across reset: no reset exists.

The documentation is direct about what this costs, which is more than most projects manage:
the initramfs approach is "unsuitable for applications which rely on persistent storage,
i.e. having made changes to a filesystem to be persisted after restarting the unikernel which
is often necessary for database applications like Postgres or MongoDB"
[DOCUMENTED — [unikraft.org/docs/cli/filesystem](https://unikraft.org/docs/cli/filesystem)].
Persistence means attaching an external volume, and volume drivers are selected at compile
time.

LUKS, RAID, LVM, ZFS and Btrfs have no in-tree equivalents; the filesystem-related libraries
in the tree are `ramfs`, `devfs`, `9pfs`, `ukfs-virtiofs` and the VFS core
[OBSERVED — `lib/` listing, staging, 2026-09-16]. CSI assumptions do not arise, because CSI
is a concept about Kubernetes nodes.

### 15 and 22: strong on rebuild, absent on verify

"Could an organization independently recreate and operate what it is running?" is the
framework's question, and in one specific sense Unikraft's answer is the strongest in the
study. There is no vendor base image to inherit. You compile the operating system from source
every time you build, from a public tree, with a configuration you hold. Nothing in the
artifact came from somewhere you cannot rebuild.

The verification half is entirely missing. No reproducible-build claim, no SBOM, no signing,
no provenance, nothing that checks a pulled component or a pulled image. Build-time
components come from a published manifest index, with a mirror flag on the build command and
no documented air-gap workflow
[DOCUMENTED / UNKNOWN as recorded in the Pulse's `d03_artifact`; I did not independently
attempt an air-gapped build, NOT TESTED].

Dimension 22's chain of BUILD → SIGN → HOST → INSTALL → BOOT → CONFIGURE → UPGRADE →
ROLLBACK → RECOVER survives partially. BUILD, HOST, BOOT and CONFIGURE work on
operator-controlled infrastructure. SIGN has no mechanism. INSTALL does not apply. UPGRADE,
ROLLBACK and RECOVER are all the same action, redeploy, and the operator already holds the
image, so no vendor infrastructure is required for any of them
[INFERRED from the model; the project documents no recovery procedure, NOT TESTED]. The one
place a vendor is structurally required is fleet operation at scale, which means the
commercial platform.

### 18: the dimension that gets harder, and the framework has no name for it

This is where I think the audit turns up something the framework does not currently ask
about.

Fusing the application and the operating system into one artifact eliminates drift between
them. No other project in this study gets that property — in every image-based host OS there
is still an OS version and a workload version and a matrix between them. It is a genuine
architectural win and the Pulse records it correctly as one.

The same fusion multiplies the patch unit. In a host-OS model, a kernel or libc CVE is fixed
once per machine, and every workload on that machine inherits the fix on reboot. In a
unikernel model, the same CVE must be fixed by rebuilding and redeploying every distinct
image that contains the affected micro-library. The patch unit moves from "machine" to
"workload image," and the number of workload images in an organisation is normally much
larger than the number of machines.

Unikraft's release process makes this sharper rather than softer. There are no release
branches, no backports and no support-window statement, so a fix reaches an adopter by moving
to the newest core release
[DOCUMENTED as established in the Pulse's `d14_maturity`]. Measured minor-release intervals
were 197, 154, 57 and 250 days for the last four, against a stated cadence of one release
every two months
[OBSERVED — [unikraft/unikraft releases via API](https://github.com/unikraft/unikraft/releases),
2026-09-16: 0.21.0 on 2026-05-20, 0.20.0 on 2025-09-12, 0.19.1 on 2025-07-17, 0.19.0 on
2025-05-23, 0.18.0 on 2024-12-20].

So the operational burden over several years, which is what dimension 18 asks about, is
different in kind rather than in degree: not "how often must I reboot machines" but "how fast
can I rebuild and redeploy N images, and do I know which of them contain the affected
component." The second half of that needs an SBOM, which does not exist.

[INFERRED. No Unikraft documentation addresses fleet-wide patching, and I found no project
statement acknowledging the trade. The mechanism follows directly from static linking and the
absence of release branches, both DOCUMENTED, but the operational consequence is my inference
and has not been tested at any scale.]

I would suggest the framework gains a dimension from this, or at least a sub-question under
18: **what is the patch unit, and how does the artifact boundary multiply or divide it?**
That question is meaningful for every project in the study, not only this one. It is the
question that the drift/coupling trade-off actually turns on, and none of the 22 dimensions
currently asks it.

### 19, 20, 21: briefly

**19.** Unikraft wins this dimension by the largest margins anywhere in the study, and the
framework almost does not care — it says not to rank trivial performance differences. These
are not trivial. The project reports images "all under 2MBs," guests running in "2-6MBs of
memory," guest boot times in the tens to hundreds of microseconds with total VM boot dominated
by the VMM at 3ms (Firecracker, Solo5) to 40ms (QEMU), and Redis "around 30%-80% faster than
running the same app in a container"
[DOCUMENTED, and these are the project's own published figures from its EuroSys'21 paper —
[unikraft.org/docs/concepts/performance](https://unikraft.org/docs/concepts/performance),
[paper](https://dl.acm.org/doi/10.1145/3447786.3456248). NOT REPRODUCED here]. The page's
figures cite Solo5, which has no platform directory in the current tree, so they are older
than the platform set observed above and should be treated as indicative. Those numbers
are what makes per-request instance lifecycles and scale-to-zero feasible, which is a
deployment pattern no host OS in this study can offer.

**20.** The APPLIANCE ↔ CONSTRUCTION KIT axis has no point for Unikraft, because it is not a
kit for building a machine; it is a kit for building a kernel. It is off the end of the scale.
The constraint it imposes is also of a different kind than the axis measures: the axis asks
how much the *operator* may change, and Unikraft's constraint binds the *developer*, whose
application must be portable to the libOS. The project quantifies that cost rather than
waving it away, which is unusual and worth crediting.

**21.** Five of the ten failure experiments do not parse. Power loss during update, network
removal during update and damaged boot configuration all require an update mechanism or a
bootloader, neither of which exists. Breaking Kubernetes after an OS upgrade requires a node
OS. Corrupting persistent configuration requires persistent configuration, which exists only
if a volume was attached. The five that do parse — corrupted image, unbootable kernel,
registry unavailable, disk full, management plane removed — have the same answer shape in
every case: the instance fails to start or dies, nothing persistent is damaged, and something
outside the model decides whether to start another. The framework's central question, "what
does the machine do next?", has a uniform answer here because the state space is small enough
that there is only one thing it can do. [NOT TESTED — no experiments were run for this tier.]

### 16 and 17: the boundary case stops being one

Governance, ownership and project health are unaffected by any of the above. BSD-3-Clause
with per-component exceptions, hosted as a sub-project of the Xen Project which is itself a
Linux Foundation project, trademark held by the commercial entity, no governance document and
no maintainers file (verified above), 0.x after nine years from the
[2017 founding announcement](https://www.linuxfoundation.org/press/press-release/xen-project-introduces-unikraft-unikernel-project).
[DOCUMENTED as established in the Pulse's `d13_governance` and `d14_maturity`; the missing
governance files OBSERVED 2026-09-16.]

A project can be a paradigm boundary case architecturally and a perfectly ordinary
open-source project organisationally. Unikraft is both, and nothing about the unikernel model
exempts it from the questions the study asks every other project.

## What replaces the host-OS guarantees

The framework's three target properties — reproducible, replaceable, recoverable — all have
unikernel-native analogues, and they are not equally strong.

**Reproducible** is the strongest. A host OS reproduces machine state by pinning an artifact
and then hoping nothing writable diverges. Unikraft reproduces it by construction: the binary
plus the boot arguments plus any attached volume *is* the state, exhaustively, and two
instances from the same binary are identical in a way that two machines from the same image
are not, because there is no writable surface for them to differ on. The Kconfig and Kraftfile
are the source of truth and they are ordinary files that go in version control.

What is missing is the verification half. Reproducibility in this sense means "I can rebuild
it"; it does not mean "I can prove this is what I built," because nothing is signed, measured
or attested. The property that image-based host OSes get from content-addressed registries
plus signatures, Unikraft gets only the first half of.

**Replaceable** is stronger than anything in the study, because there is nothing to replace.
Replacement is not a machine operation with a state machine and failure modes; it is
scheduling. Patch-and-reboot becomes rebuild-and-redeploy. The failure modes of the upgrade
path disappear along with the upgrade path.

**Recoverable** is where the analogy breaks and I do not think it should be papered over.
Recovery in the framework's sense is about restoring a *specific* machine that has something
worth restoring — identity, data, a role in a cluster. A unikernel instance has none of those,
so recovery is not a weaker version of host-OS recovery; it is a different problem that has
been moved to whatever holds the state instead. If the state lives in an attached volume, its
recovery is the volume's problem and Unikraft offers nothing. If the state lives in a
database elsewhere, the recovery story is that database's. The unikernel did not solve
recovery; it declined to participate in it.

In all three properties the guarantee comes from removing the thing that needed guaranteeing,
and in two of the three the removed thing reappears somewhere else.

## Structural verdict

**The general-purpose host OS is not the wrong unit of deployment for this investigation, but
the investigation has been treating it as an unstated assumption and should state it.**

Three claims, in order of confidence.

**First, "there is a persistent machine" is an implicit boundary of the whole framework, and
Unikraft makes it visible.** At least eight of the twenty-two dimensions — 4, 5, 10, 11 and
substantial parts of 1, 6, 12 and 13 — are not really about immutability, reproducibility or
recovery. They are about what happens to a thing that survives its workloads. Remove the
surviving thing and those dimensions do not become hard to answer; they become void. A
dimension that returns "not applicable" for a system with no persistent machine was asking
about persistent machines, whatever its heading said.

**Second, the boundary is defensible, because Unikraft does not remove the host — it requires
one.** Every currently supported deployment target is a hypervisor: KVM through QEMU or
Firecracker, or Xen
[OBSERVED — `plat/` listing, 2026-09-16; DOCUMENTED —
[unikraft.org/docs/concepts/virtualization](https://unikraft.org/docs/concepts/virtualization)].
A hypervisor runs on a machine that somebody has to provision, patch, attest, recover and
operate across years. Every question the epic asks applies to that machine, unchanged. The
`native` platform and the bare-metal work are the only path that would alter this, and the
project's own FAQ still describes bare metal as something it is working towards.

So the popular framing — unikernels make the host OS obsolete — is not supported by what the
project actually ships. What it does is make the host OS *smaller and more uniform*: a
machine whose only job is to run a hypervisor and schedule short-lived guests has a narrower
requirements profile than a machine running a container runtime and a Kubernetes kubelet. The
reproducible-machine-state question does not go away at that layer. If anything it gets
cleaner, because there is less on the machine to disagree about.

**Third, the widening Unikraft argues for is not "add unikernels to the study."** It is a
dimension the framework is missing, described under 18 above: the patch unit, and how the
artifact boundary multiplies or divides it. Unikraft is the extreme case of fusing workload
into artifact, and the extreme case makes the trade legible — no drift between application
and OS, at the cost of every image needing a rebuild for every component CVE. That trade
exists in weaker form in every project in the study, including the ones that bundle a
container runtime or a Kubernetes distribution into the OS artifact. The framework should ask
about it directly.

Recommendations for the epic:

1. State the host-OS scope boundary explicitly in the TAG paper and in the series, rather
   than leaving it implicit. One sentence, of the form "this investigation is about machines
   that outlive their workloads," would do it, and it is more honest than the current
   position of simply not mentioning that the boundary exists.
2. Keep Unikraft as a boundary case and do not score it. Eight-plus dimensions returning "not
   applicable" is not a low score; it is evidence that the scoring instrument does not apply.
   Any comparison table that puts Unikraft in a column alongside the other nine will mislead,
   and the Pulse's three-kinds-of-no schema is the right precedent to follow.
3. Add a patch-unit question, either as a twenty-third dimension or as a sub-question under
   18.
4. Do not widen the study to unikernels as a category. The layer Unikraft points at — what
   runs the hypervisor — is already in scope, and is where the study's existing dimensions
   work as written.

For public series post #8 specifically: the title question has an answer, and the answer is
neither "yes, the host OS is obsolete" nor "no, unikernels are a toy." It is that the host OS
survives as a hypervisor substrate with a narrower job, and that the interesting consequence
of unikernels for machine state is not the disappearance of the host but the multiplication
of the patch unit.

## Claims that need maintainer review before publication

**Unikraft maintainers.** The following are my characterisations rather than the project's,
and the project has never stated them:

- That the model implies no fleet-wide patch story and that a component CVE requires
  rebuilding every image containing it. The mechanism follows from static linking and the
  absence of release branches, but the project may have an intended answer that is not
  documented.
- That the absence of an upgrade verb in the CLI reflects an architectural position rather
  than a gap. The Pulse already flags this as the largest conceptual gap for operators and
  asks the project to state its position; I reached the same place independently.
- That the Kubernetes `runu` path's maturity is unstated rather than stable.

**Kairos maintainers, and Mauro specifically.** One claim in this document is comparative in a
direction that favours the category Kairos belongs to, and I am flagging it rather than
leaving it in the text unmarked:

- In the structural verdict, second claim, I argue that a hypervisor host has a narrower
  requirements profile than a Kubernetes node and that the reproducible-machine-state question
  gets *cleaner* at that layer. That reads as an argument that minimal immutable host OSes —
  Kairos among them — are well suited to the substrate role that unikernels create demand for.
  I believe the narrower-profile part is defensible on its own terms, but "cleaner" is an
  interpretation and I did not test it. It should be checked for motivated reasoning by
  someone who is not writing under an epic that Kairos's maintainer opened.
- I have made no claim anywhere in this document that Kairos or any other named project
  handles any dimension better or worse than Unikraft. That was deliberate. Unikraft is not
  being scored, and comparative claims would have required the maintainer-correction round
  that the framework mandates.

## Open questions

Distinct from the Pulse's open questions, which are factual gaps to put to the project. These
are questions about the investigation.

1. Does the framework want a twenty-third dimension for the patch unit, or a sub-question
   under 18? A new dimension would need applying retroactively to any project already
   profiled.
2. Is "the machine outlives its workloads" the right statement of the study's boundary, or is
   there a better one? The alternative framing is "state that accumulates," which would draw
   the line in a slightly different place and might include or exclude different systems.
3. Does the same audit run against Amutable and NixOS produce different void dimensions? If
   the set of dimensions that go void is distinctive per paradigm, the audit itself might be a
   more interesting comparison instrument than the dimension answers are.
4. If bare-metal Unikraft ships, which of the eleven void or transformed verdicts here flip?
   My guess is dimensions 10, 8 and parts of 5 come back immediately, and 4 and 11 do not.
   Worth re-running the audit if `native` matures, and worth not assuming this will happen —
   the FAQ has described bare metal as in progress for some time.
5. Does anyone run the open-source project in production outside the commercial platform? The
   Pulse asks this as a factual question. For this document it matters because the entire
   operational half of the audit is reasoning about a deployment model, and NOT TESTED is the
   honest label on most of it.
