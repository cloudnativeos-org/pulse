# Research framework — Reproducible Machine State investigation

Verbatim, 2026-09-15. This is the operational research
framework; `persona-strategy-v3-source.txt` in this same directory is the strategy
document (extracted from the uploaded `.docx`) that supplies the *why*, the
two-artifact split, and the platform depth tiers. Read both — this file is more
exhaustive on the research dimensions and evidence standard; the strategy doc is
authoritative on scope, depth stratification and what gets published where.

---

I want to conduct a rigorous, technically deep comparison of modern immutable/cloud-native operating systems and OS-building approaches.

The initial projects should include:

CNCF:
- Kairos
- Flatcar
- bootc / Fedora CoreOS where relevant

Cloud-native / independent:
- Talos Linux
- Unikraft

Hyperscaler:
- AWS Bottlerocket
- Azure Linux
- Google Container-Optimized OS

Other approaches worth considering:
- NixOS
- Ammutable, once enough public information exists

The goal is NOT to determine a universal "best OS" and NOT to produce a feature-checkbox comparison.

The goal is to understand the architectural choices each project makes, the consequences of those choices, and which kinds of users, workloads, organizations, and operating environments benefit from each approach.

I work on Kairos, so bias is an explicit methodological risk. Treat Kairos exactly like every other project. Do not assume its architectural choices are superior. Identify cases where Kairos's flexibility, architecture, governance, or other choices introduce disadvantages. Likewise, do not treat Talos's constraints or opinionated design as disadvantages by default; determine what guarantees or operational benefits those constraints enable.

Where possible, distinguish between:
- documented capability
- experimentally reproduced capability
- observed/measured behavior
- inference
- unknown/not tested

Never interpret missing documentation as proof that something is unsupported.

Use current primary sources wherever possible: official documentation, source repositories, design documents, governance documents, release information, and project maintainers' statements. Flag information that may have changed between versions.

## Research framework

For every project, investigate the following areas.

### 1. Definition and implementation of immutability

Determine what "immutable" concretely means.

Investigate:
- What parts of the filesystem/system are immutable?
- What remains writable?
- What is ephemeral?
- What persists across reboot?
- What persists across upgrade?
- What technical mechanism enforces immutability?
- Can the running OS be modified?
- Can configuration drift occur?
- Does a version uniquely identify machine state?
- How can an operator determine the actual state of a running machine?

Do not reduce this to "immutable: yes/no."

Explain the consequences of each implementation.

### 2. Unit of OS deployment

Determine what artifact represents an OS release.

Examples might include:
- OCI image
- disk image
- SquashFS
- OSTree commit
- A/B filesystem image
- UKI
- package/repository snapshot
- another format

Investigate:
- Is it content-addressable?
- Can it live in a standard OCI registry?
- Can it be mirrored?
- Can it be signed?
- Can it be independently built?
- Does it contain kernel, initrd and userspace together?
- Are boot assets versioned separately?
- Can the complete artifact lifecycle work air-gapped?

Explain what the project's chosen "unit of deployment" enables and constrains.

### 3. OS construction and customization

Determine how an organization creates the OS it actually runs.

Investigate:
- Available base distributions/userspaces
- Whether arbitrary Linux bases are possible
- Kernel selection/customization
- Packages
- custom binaries
- kernel modules
- firmware
- GPU drivers
- filesystem drivers
- storage/network drivers
- security agents
- monitoring agents
- proprietary software
- FIPS requirements
- corporate CA certificates
- system services
- container runtimes

Determine WHERE customization occurs:
- build time
- extensions
- runtime
- first boot
- machine configuration
- another mechanism

Do not equate "cannot install packages at runtime" with "cannot be customized."

Explain the tradeoff between extensibility and controlled system state.

### 4. Upgrade mechanism

Document the complete upgrade state machine.

Before upgrade:
- Where does the new OS come from?
- Who initiates the upgrade?
- How is the artifact verified?
- Can upgrades occur without Kubernetes?
- Can upgrades occur without the project's hosted infrastructure?

During upgrade:
- What gets written?
- Is an inactive partition used?
- Is the running filesystem changed?
- What happens to kernel/initrd/bootloader?
- What happens if power is lost halfway through?

At reboot:
- How is the new system selected?
- How is successful boot determined?
- How many attempts are allowed?
- Is OS health checked?
- Is Kubernetes/application health checked?

After failure:
- Is rollback automatic?
- What triggers it?
- What persistent state survives?
- What happens to Kubernetes state?
- What happens to workloads/container images?

Explicitly compare A/B, A/B/recovery, transactional image, OSTree-style, and other approaches where applicable.

### 5. Rollback and recovery

Treat rollback and recovery as different concepts.

Distinguish:
- rollback to previous OS
- rollback to known OS version
- rollback of complete machine state
- recovery environment
- factory reset/reprovisioning

Investigate:
- Number of retained versions
- automatic rollback
- explicit version selection
- multi-version rollback
- local vs network-dependent recovery
- dedicated recovery systems
- persistent-data corruption
- recovery when Kubernetes is unavailable
- recovery when management infrastructure is unavailable
- recovery when networking is unavailable

Ask: what is the project's definition of a "known-good state"?

### 6. Configuration model

Determine how machines are configured.

Investigate:
- cloud-init
- Ignition/Butane
- YAML configuration
- APIs
- Kubernetes CRDs
- systemd
- image-embedded configuration
- other models

Separate:
- image configuration
- machine configuration
- runtime configuration
- cluster configuration

Investigate:
- declarative vs imperative
- idempotency
- configuration drift
- remote inspection
- version control
- signing
- secrets
- configuration changes without reboot/rebuild
- source of truth

### 7. Kubernetes coupling

Determine how strongly the OS and Kubernetes are coupled.

Investigate:
- Can it operate without Kubernetes?
- Is Kubernetes built into the OS architecture?
- Can Kubernetes be removed?
- Which Kubernetes distributions are supported?
- Can Kubernetes distributions be changed?
- Can OS and Kubernetes upgrades happen independently?
- Can Kubernetes manage the OS lifecycle?
- Does the OS manage Kubernetes?
- Which system owns machine lifecycle?

Evaluate non-Kubernetes workloads:
- container host
- appliance
- database
- storage
- AI/GPU
- edge gateway
- hypervisor
- ordinary Linux service

Place systems conceptually on a spectrum such as:

Kubernetes appliance <-> Kubernetes-oriented OS <-> general immutable infrastructure substrate

Do not assume any position is inherently superior.

### 8. Hardware and platform support

Evaluate:
- amd64
- arm64
- riscv64
- other architectures

Platforms:
- bare metal
- VMs
- AWS
- Azure
- GCP
- VMware
- OpenStack
- SBCs
- edge devices

Specialized hardware:
- NVIDIA GPUs
- NVIDIA Jetson
- NPUs
- unusual NICs
- RAID controllers
- storage controllers
- Wi-Fi
- cellular
- TPM
- industrial PCs
- Raspberry Pi-class hardware
- RISC-V

Most importantly ask:

"If unsupported hardware appears tomorrow, can an organization add support itself, and how difficult is that?"

### 9. Security and chain of trust

Trace trust through:

firmware -> bootloader -> kernel -> initrd -> root filesystem -> extensions -> configuration -> workload

Investigate:
- UEFI Secure Boot
- custom keys
- UKI
- measured boot
- TPM/PCR
- dm-verity
- disk encryption
- TPM-bound encryption
- remote attestation
- artifact signatures
- OCI signatures
- SBOM
- provenance
- reproducible builds
- CVE handling
- secret provisioning
- key rotation/revocation
- FIPS
- SELinux/AppArmor
- kernel hardening

Explicitly distinguish:
- tamper prevention
- tamper detection
- attestation

### 10. Provisioning and zero-touch deployment

Start from powered-off/unprovisioned hardware and document the path to a managed machine.

Investigate:
- ISO
- USB
- PXE/iPXE
- cloud images
- network installation
- OEM/factory installation
- first-boot configuration
- device identity
- bootstrap trust
- DHCP/network requirements
- Internet requirements
- air-gapped provisioning

Evaluate the factory/edge scenario:

"Can 5,000 identical devices leave a factory and independently establish secure identity and desired state on first boot?"

### 11. Fleet lifecycle

Separate OS functionality from optional/commercial fleet-management products.

Investigate:
- inventory
- desired OS state/version
- staged rollout
- canaries
- maintenance windows
- concurrency
- topology-aware rollout
- Kubernetes-aware draining
- health gates
- automatic rollback
- version pinning
- grouping
- remote reset
- remote recovery
- disconnected fleets
- audit trail

Clearly label which capabilities belong to:
- the open-source OS/project
- an open-source companion project
- a commercial product

### 12. Debugging and day-2 operations

Evaluate failure scenarios.

Investigate:
- SSH
- local shell
- available debugging tools
- temporary tools
- privileged debugging containers
- logs
- API access
- serial console
- rescue environment
- support bundles
- filesystem inspection/modification
- debugging without Kubernetes
- debugging with broken networking

Do not assume SSH is inherently good or "no SSH" inherently good.

Explain the operational and security consequences of each model.

### 13. Persistent state and storage

Investigate:
- persistence across reboot
- persistence across upgrade
- persistence across reset
- container runtime state
- Kubernetes state
- etcd
- application data
- customizable persistent paths
- disk encryption
- additional disks
- LUKS
- RAID
- LVM
- ZFS
- Btrfs
- network storage
- CSI assumptions

Determine where each architecture draws the boundary between replaceable infrastructure and stateful machine.

### 14. Networking

Investigate:
- DHCP
- static networking
- bonding
- VLAN
- bridges
- Wi-Fi
- WireGuard
- proxies
- corporate CAs
- IPv6
- multiple NICs
- SR-IOV
- RDMA
- pre-Kubernetes networking
- remote network reconfiguration

Pay particular attention to edge, telco, GPU and industrial scenarios.

### 15. Supply-chain ownership and reproducibility

Ask:

"Could an organization independently recreate and operate what it is running?"

Investigate:
- source availability
- build tooling
- public CI
- reproducible builds
- dependency pinning
- signing
- SBOM
- provenance
- public artifacts
- private registry support
- mirroring
- self-hosted builds
- self-hosted update infrastructure

Perform or design this independence test:

Using infrastructure controlled entirely by the operator:

BUILD -> SIGN -> HOST -> INSTALL -> CONFIGURE -> UPGRADE -> ROLLBACK -> RECOVER

Identify every point where infrastructure controlled by the project's primary commercial sponsor is required.

Then ask:

"If that company and all of its hosted services disappeared tomorrow, what functionality would remain?"

Apply this equally to every project, including Kairos.

### 16. Governance and ownership

Record facts rather than assigning simplistic scores.

Investigate:
- trademark ownership
- project asset ownership
- GitHub organization ownership
- foundation hosting
- governance documents
- maintainer structure
- organizational diversity
- CLA/DCO
- license
- relicensing ability
- release control
- infrastructure control
- signing-key control
- domain/registry control
- commercial sponsors
- dependency on one company's engineers
- ability of another organization to continue development

Explicitly distinguish:

OPEN SOURCE
OPEN GOVERNANCE
VENDOR-NEUTRAL OWNERSHIP
DIVERSE CONTRIBUTION

These are not synonymous.

### 17. Project health and sustainability

Investigate:
- release cadence
- release history
- contributors
- contributor concentration
- maintainers
- bus factor
- issue response
- PR velocity
- security response
- support windows
- compatibility policy
- breaking-change policy
- commercial backing
- funding where publicly known
- adoption where verifiable
- foundation maturity where relevant

Do not use GitHub stars as a quality score.

### 18. Operational lifecycle and support horizon

Investigate:
- required upgrade frequency
- supported releases
- skipped upgrades
- downgrade support
- Kubernetes compatibility
- kernel cadence
- CVE cadence
- LTS releases
- EOL policy
- old artifacts/extensions
- indefinite version pinning
- enterprise support

Evaluate the operational burden over several years, not merely initial installation.

### 19. Resource footprint and performance

Where experimentally useful, measure:
- image size
- disk footprint
- idle memory
- idle CPU
- boot time
- upgrade download size
- upgrade duration
- reboot duration
- network consumption

Do not rank trivial performance differences unless they have practical consequences.

### 20. Extensibility versus constraint

Treat this as a core architectural tradeoff.

Place systems conceptually on:

APPLIANCE <----------------> CONSTRUCTION KIT

Investigate:
- How many decisions does the project make for the operator?
- Which decisions can be overridden?
- How difficult is customization?
- Can unsupported states be created?
- Does customization weaken guarantees?
- Does flexibility increase testing responsibility?
- Does constraint reduce operational complexity?
- Can existing enterprise standards be incorporated?
- Must the organization instead adopt the project's standards?

Treat both flexibility and constraint as potentially beneficial.

### 21. Failure experiments

Design reproducible destructive tests.

For every feasible project:

1. Cut power during OS update.
2. Supply a corrupted new OS image.
3. Introduce a kernel that cannot boot.
4. Break Kubernetes after OS upgrade.
5. Corrupt persistent configuration.
6. Remove network during upgrade.
7. Make the image registry unavailable.
8. Fill the disk.
9. Damage boot configuration.
10. Remove the management plane.

For every experiment document:

INITIAL STATE
FAILURE INJECTED
EXPECTED BEHAVIOR
OBSERVED BEHAVIOR
FINAL MACHINE STATE
MANUAL INTERVENTION REQUIRED
DATA LOST
RECOVERY PROCEDURE
TIME TO RECOVERY

The central question is:

"What does the machine do next?"

### 22. Operational independence experiment

Attempt to operate every system without infrastructure provided by its creator or primary commercial sponsor.

Attempt:

BUILD
SIGN
HOST
INSTALL
BOOT
CONFIGURE
UPGRADE
ROLLBACK
RECOVER

Document external dependencies and whether they can be replaced with operator-controlled infrastructure.

## Evaluation methodology

Do NOT produce a universal numeric ranking.

Instead derive recommendations based on requirement profiles such as:

- Kubernetes appliance
- enterprise Kubernetes platform
- edge fleet
- AI/GPU edge
- hyperscale/cloud
- regulated environment
- enterprise with existing Linux standards
- homelab
- infrastructure vendor/OEM
- disconnected/air-gapped environment
- heterogeneous hardware fleet

For every profile:

1. Define the requirements first.
2. Identify which architectural dimensions matter.
3. Explain the tradeoffs.
4. Determine which projects fit particularly well.
5. Identify meaningful disadvantages.
6. State when multiple approaches are equally defensible.

It is desirable for different projects to win different scenarios.

If one project appears to win almost every scenario, challenge the methodology for hidden assumptions or bias.

## Evidence standard

Every factual claim should have one of these labels internally:

DOCUMENTED — explicitly supported by primary documentation/source.
REPRODUCED — independently tested using documented procedure.
OBSERVED — measured during our experiments.
INFERRED — reasonable conclusion from evidence but not explicitly documented.
UNKNOWN — insufficient evidence.
NOT TESTED — test has not been performed.

Prefer primary sources.

Record exact project/version information for experimental results.

Where feasible, create reproducible scripts/configuration and publish them.

Before final publication, prepare a factual profile for each project and invite its maintainers to correct factual errors. Maintainers may correct facts but do not need to agree with conclusions.

## Important bias controls

I work on Kairos.

Therefore:

- Do not accept Kairos documentation uncritically.
- Do not use Kairos terminology as the neutral definition of the category.
- Do not design criteria solely around features Kairos happens to have.
- Identify architectural costs introduced by Kairos's flexibility.
- Identify guarantees created by Talos's constraints.
- Identify areas where Flatcar, bootc, Bottlerocket, Talos, etc. are technically superior.
- Distinguish project capability from commercial ecosystem capability.
- Apply governance and independence tests equally to Kairos.
- Never speculate about future corporate behavior.
- Do not infer technical weakness from acquisitions, maintainer departures, funding, or corporate ownership.

The purpose is not to prove that Kairos is best.

The purpose is to create a framework rigorous enough that, after defining an organization's requirements, we can defensibly answer:

"Which architecture makes the most sense for this particular problem, and why?"

## First deliverable

Do NOT begin writing the final comparison yet.

First produce a RESEARCH PLAN containing:

1. A refined taxonomy of the systems being compared.
2. Any missing evaluation dimensions in this prompt.
3. Any dimensions that should be merged or removed.
4. The exact facts/data required from every project.
5. Experiments required for meaningful comparison.
6. Hardware/infrastructure required for those experiments.
7. A standardized project-profile template.
8. A standardized experiment-report template.
9. Proposed requirement/persona profiles.
10. Major methodological risks and sources of bias.
11. A research sequence that minimizes duplicated work.
12. Which questions can be answered through documentation and which require experiments.

Challenge the framework before accepting it. Methodological rigor matters more than a large number of criteria.
