# Azure Linux — hyperscaler case study

Depth tier: hyperscaler case study, documentation-based
(part of the research epic).
Research window: 2026-09-15 to 2026-09-16. All sources retrieved 2026-09-16 unless noted.
Seeds public series post #6, paired with Bottlerocket and Google Container-Optimized OS.

No experiments were run. The funnel README assigns this tier "documentation-based; explicitly
avoid reverse-engineering undocumented internals; label evidence limitations", and that is
what this is. Every claim below carries one of the labels from research-framework.md's
evidence standard: DOCUMENTED, INFERRED, UNKNOWN, NOT TESTED. Nothing here is REPRODUCED or
OBSERVED.

## The short answer

When AKS owns the node image, the operator stops choosing what the machine contains and starts
choosing a policy about when it changes. Known state survives, in a narrow form: Microsoft
publishes a per-version content manifest and the running node carries its version as a label, so
an operator can say precisely what is on a node. They cannot rebuild it, cannot return to a
version the node pool has already left, and cannot hold a version longer than 90 days without
leaving support. Node pool snapshots pin a version forward, which covers repeatable
environments but not rollback. Meanwhile one AKS release train applies itself when it reaches
your region, and node auto-repair reimages an unhealthy node after five minutes without asking.

Immutability is a separate axis from all of that. Base Azure Linux is not immutable; Microsoft's
immutable container host is a distinct Flatcar-derived product, ACL. On ACL the guarantees this
investigation cares about do hold — verity-protected `/usr`, signed UKI, measured boot — and the
usual costs of immutability are mostly already paid, because the platform was replacing nodes
weekly regardless.

## Why this document is shaped the way it is

No standardized project-profile template survives from the methodology plan — that ticket was closed and
superseded by the cloud native OS Pulse (the Pulse brief) before it produced one. The NixOS and Unikraft profiles each hit the same gap and each designed a structure fitting their own question,
recording that choice in-doc. Same precedent here.

The structure I chose is not the 22 dimensions in order, and not a mirror of the Pulse
profile. Both of those would produce a worse document for this tier, for different reasons.

The Pulse's `azure-linux.yaml` (1007 lines, unmerged on `feat/issue-813-pulse-profiles`)
already answers the categorical question thoroughly and I am not redoing it: base Azure Linux
is a conventional RPM distribution with a mutable root and a package manager at runtime, not
an image-based or immutable OS; Microsoft's immutable container host is a separate product,
Azure Container Linux (ACL), derived from Flatcar; a third variant, Azure Linux with OS Guard,
is being retired in ACL's favour. I verified the load-bearing pieces of that against primary
sources and found no corrections to make.

What the Pulse does not attempt, and what the ticket asks for, is the operator-facing
question: what changes about reproducibility, known state, rollback and recovery when the
platform provider — not the operator — owns the artifact and the schedule. So the document is
organized around the four things an operator actually loses or gains control of:

1. what "the surrounding environment" is, concretely
2. the node image as an artifact somebody else builds
3. who decides when a machine changes
4. what recovery means when the machine isn't yours to investigate

followed by where ACL changes the answers, and what this tier suggests the 22-dimension
framework is missing.

## Scope note: three products, one name

Stated once, because every claim below depends on which product it applies to. This is the
Pulse's finding, verified:

| Name | What it is | Where it runs |
|---|---|---|
| Azure Linux | Conventional RPM distribution, mutable root, `dnf` at runtime | AKS nodes, Azure VMs/VMSS, container base images, WSL |
| Azure Linux with OS Guard | `/usr` read-only under dm-verity, plus IPE | AKS only, preview, retiring |
| Azure Container Linux (ACL) | Flatcar-derived, immutable `/usr`, A/B USR slots, Ignition | AKS only, GA from v1.34 |

Microsoft's own deployment-options page describes ACL as "an immutable, container-optimized OS
for AKS derived from Flatcar Container Linux with Azure Linux packages and servicing"
(DOCUMENTED, [deployment-options](https://learn.microsoft.com/en-us/azure/azure-linux/deployment-options)).
For this investigation's normal dimensions — the artifact boundary, A/B rollback, verified
boot, extension model — **base Azure Linux is out of category and ACL is in it**. Where the
answer differs by product below, I say which one.

## 1. What "the surrounding environment" actually means

The ticket asks me to distinguish self-managed Azure Linux from AKS-managed nodes. The
documentation makes that distinction shorter than expected.

**There is no supported self-managed path outside Azure at all.** The deployment-options page
states it flatly:

> Azure Linux is open source, but Microsoft support and lifecycle commitments apply only to
> **Azure scenarios**. Specifically: Azure Linux Virtual Machines (VM) / Virtual Machine Scale
> Sets (VMSS), AKS container host, and container images are supported. Bare metal, ISO images,
> on-premises, and other clouds aren't supported.

(DOCUMENTED, [deployment-options](https://learn.microsoft.com/en-us/azure/azure-linux/deployment-options).)

The same page draws a second boundary inside Azure: customized images "are supported only when
built on top of a prebuilt Azure Linux image", and "images built from scratch from the Azure
Linux sources on GitHub aren't covered" (DOCUMENTED, same source). The MIT-licensed source is
public and buildable; the resulting artifact is outside the support contract. So "run it
yourself" is legally available and operationally unsupported, and the Pulse records the same
scoping in the contribution policy.

Self-managed Kubernetes on Azure Linux is not documented anywhere I looked (UNKNOWN — absence
of documentation, not evidence of impossibility). ACL is documented only as an AKS OS option
(DOCUMENTED, [ACL overview](https://learn.microsoft.com/en-us/azure/aks/azure-container-linux-overview)).

That collapses the comparison the ticket set up. For the immutable variant there is no
self-managed arm to compare against. The surrounding environment is AKS, and for ACL the
surrounding environment is the only environment. Everything below is therefore about what AKS
controls.

Concretely, AKS controls: which node image version exists, what is in it, when it reaches your
region, whether it is applied automatically, whether a node gets reimaged or redeployed when it
looks unhealthy, and how long any given image stays supported. The operator controls: which OS
SKU, which auto-upgrade channel, the maintenance window, surge settings, and whether to pin
(temporarily) with a snapshot.

## 2. The node image as an artifact somebody else builds

### What is published

AKS node images are built by AgentBaker, which is public and MIT-licensed
(DOCUMENTED, [Azure/AgentBaker](https://github.com/Azure/AgentBaker) — "AgentBaker provides
components that build VM images and provision Kubernetes nodes in Azure ... The primary
consumer of AgentBaker is Azure Kubernetes Service (AKS)"). The Packer templates are in the
repo (`vhdbuilder/packer/vhd-image-builder-acl.json` and siblings), as are the install scripts.

Each released node image gets a release-note file. For the Azure Linux 3 gen2 image
`202608.26.0` that file is 608 lines and contains, in order: every component downloaded during
the build with its version; every container image pre-pulled into the VHD; the complete
installed RPM list between `=== Installed Packages Begin` and `=== Installed Packages End`
(394 lines, one NEVRA each, including `kernel-6.6.150.1-1.azl3.x86_64`); disk usage per mount;
`/etc/os-release`; the full kernel version banner; and the build's provenance line —
`VSTS Build ID: 178227308`, `Commit: 1fcb7f57754214d0950340abe1f78a59e94ceb65`
(DOCUMENTED, [AzureLinuxv3/202608.26.0.txt](https://github.com/Azure/AKS/blob/master/vhd-notes/AzureLinuxv3/202608.26.0.txt)).

For enumerating what is on a node, this is better than most self-managed fleets produce for
themselves. The running node also carries its version as a Kubernetes label,
`kubernetes.azure.com/node-image-version`, so the manifest joins to the machine
(DOCUMENTED, [upgrade-node-image](https://learn.microsoft.com/en-us/azure/aks/upgrade-node-image)).

### What is not published

The manifest is a description, not a recipe. The Packer build takes a private package feed URL
(`PRIVATE_PACKAGES_URL`) from the environment, runs inside an Azure subscription against an
internal build pipeline, and publishes into a Shared Image Gallery
(DOCUMENTED, [vhd-image-builder-acl.json](https://github.com/Azure/AgentBaker/blob/master/vhdbuilder/packer/vhd-image-builder-acl.json)).
No documented procedure exists for an operator to rebuild a given node image version and
compare it to the published one (UNKNOWN — I found no such procedure; I did not attempt a
build, and the absence is in the documentation, not necessarily in the capability).

I also found no published SBOM or SLSA-style provenance attestation for AKS node images
themselves. Microsoft's SBOM and image-signing documentation
([attach-sbom](https://learn.microsoft.com/en-us/azure/security/container-secure-supply-chain/articles/attach-sbom),
[image-integrity](https://learn.microsoft.com/en-us/azure/aks/image-integrity)) is about
container images the customer builds and deploys, not about the VHD underneath. The Pulse
records the same gap for Azure Linux generally (UNKNOWN). Trusted Launch with Secure Boot and
vTPM gives a measured-boot attestation of what booted, which is a different guarantee than an
attestation of how the image was produced (DOCUMENTED,
[ACL overview](https://learn.microsoft.com/en-us/azure/aks/azure-container-linux-overview)).

So "known state" on AKS means: a precise, vendor-published inventory of a version you did not
choose the contents of and cannot independently reconstruct. Verification is by manifest, not
by rebuild.

### The immutable variant publishes less, not more

This is the one finding I did not expect and it is worth stating exactly.

For ACL node images, the same release-note file has this where the package list would be:

```
=== Installed Packages Begin
listInstalledPackages stub
=== Installed Packages End
```

I checked four ACL releases — `202607.20.0`, `202608.14.0`, `202608.26.0`, and the current
`latest.txt` (`202609.09.0`) — and all four carry the stub (DOCUMENTED,
[AgentBaker release-notes/AKSAzureContainerLinux/gen2tl/latest.txt](https://github.com/Azure/AgentBaker/blob/master/vhdbuilder/release-notes/AKSAzureContainerLinux/gen2tl/latest.txt)).
The ACL note is 187 lines against the Azure Linux note's 608. It does carry the pre-pulled
container image list, disk layout showing `sysext` mounted at `/usr`, `os-release` with
`ID_LIKE="flatcar"` and a CPE name, and the same kernel and build-provenance lines.

The immutable, verity-protected variant currently ships a less complete content manifest
through the AKS release-notes channel than the mutable one does. My guess is that this is a
tooling artifact rather than a policy choice — `listInstalledPackages` presumably shells out to
`rpm`/`dnf`, which is exactly what ACL does not have — but I did not verify that and the
function body is not something I went looking for (INFERRED, low confidence; the stub itself is
DOCUMENTED). Either way, the operator-visible consequence is real: on ACL, the node-image
version string plus the verity root hash is closer to the whole of what you get, and
package-level inventory has to come from somewhere else.

Worth flagging as a maintainer question rather than a finding: whether ACL package inventory is
published elsewhere, or is intended to be derived from the Azure Linux 3.0 build the image is
composed from.

### A smaller publishing wrinkle

The [node-images](https://learn.microsoft.com/en-us/azure/aks/node-images) doc points operators
at `github.com/Azure/AKS/tree/master/vhd-notes` for "detailed summaries of each node image
version". On 2026-09-16 the newest file there for Azure Linux 3 was `202608.26.0`, while
AgentBaker's own `vhdbuilder/release-notes` tree carried `202609.03.1` and `202609.09.0`
(DOCUMENTED, both trees inspected via the GitHub contents API). Images ship weekly; the
mirror the docs send you to was about three weeks behind the source of truth on the day I
looked. Not a large thing, but if the manifest is the substitute for a reproducible build, the
freshness of the manifest is load-bearing.

## 3. Who decides when the machine changes

### Three release trains, one of which is not opt-in

The release tracker documentation splits AKS releases into three independent trains, and the
first one is the interesting one:

> **AKS releases** ships updates, bug fixes, and security patches for features and add-ons ...
> These releases are automatically applied to the clusters when the release reaches the region
> where the cluster is located.

(DOCUMENTED, [release-tracker](https://learn.microsoft.com/en-us/azure/aks/release-tracker).)

The other two — Kubernetes versions and node images — are described as things the operator
upgrades "either manually or automatically". Planned maintenance can schedule "AKS-initiated
maintenance (AKS release train)", so the operator can move when it happens
(DOCUMENTED, same source). I found no documented way to decline it — a category of change to
the running system that arrives on Azure's schedule, where the operator's control is the
window rather than the decision.

### Node image upgrades: the operator picks a policy, not a version

Linux node images are released weekly and take up to two weeks to roll out across all regions,
under what Microsoft calls safe deployment practices (DOCUMENTED,
[upgrade-node-image](https://learn.microsoft.com/en-us/azure/aks/upgrade-node-image)). The
choice an operator makes is a channel:

| Channel | Who owns the update | Cadence |
|---|---|---|
| `None` | "you're solely responsible for your security updates" | never |
| `Unmanaged` | "OS driven security updates. AKS has no control over these updates." | nightly ~06:00 UTC via `dnf-automatic` |
| `SecurityPatch` | "AKS-tested, fully managed, and applied with safe deployment practices" | "Typically faster than weekly, AKS determined cadence" |
| `NodeImage` | "AKS-tested, fully managed, and applied with safe deployment practices" | weekly |

(DOCUMENTED, all quotes from
[auto-upgrade-node-os-image](https://learn.microsoft.com/en-us/azure/aks/auto-upgrade-node-os-image).)

`NodeImage` is the default for any new AKS Standard cluster from API version 2023-06-01, and
AKS Automatic clusters "always use the `NodeImage` channel by default" and cannot change it —
"you can adjust maintenance windows to control when upgrades occur", but "the channel choice is
fixed" (DOCUMENTED, same source). The `SecurityPatch` channel is the one place where AKS may
change a running node without replacing it: "If AKS decides that reimaging nodes isn't
necessary, it patches nodes live without draining pods and performs no VHD update" (DOCUMENTED,
same source).

None of these let the operator name a version. `az aks nodepool upgrade --node-image-only`
moves to the latest available; the CLI reference for `az aks nodepool add`/`upgrade` has no
node-image-version parameter (DOCUMENTED for the upgrade-to-latest behaviour;
INFERRED for the absence, since I read the CLI reference rather than running `--help`).

### Currency is mandatory, not optional

Two statements make staying current a support condition rather than a preference:

> Microsoft doesn't support node images that are older than 90 days.

> Older node images ... could also place the cluster outside of the support scope until you
> perform a node image upgrade.

(DOCUMENTED, [support-policies](https://learn.microsoft.com/en-us/azure/aks/support-policies)
and [node-images](https://learn.microsoft.com/en-us/azure/aks/node-images).)

And support explicitly excludes "vulnerabilities and CVEs with a vendor fix less than 30 days
old", with the customer expected to "update the VHD, then filter the CVE report and provide
Microsoft Support a list of only the CVEs with a vendor fix over 30 days old" (DOCUMENTED,
support-policies). The CVE support boundary is defined relative to a node image you are
presumed to be replacing continuously.

For an operator whose requirement is "this machine's state does not change until I change it",
that requirement is not expressible on AKS beyond 90 days. It is not forbidden — `None` is a
channel — it just ends support.

## 4. Rollback and pinning

### There is no node image downgrade

> You can't downgrade a node image version (for example, *AKSUbuntu-2404* to *AKSUbuntu-2204*,
> or *AKSUbuntu-2404-202601.27.0* to *AKSUbuntu-2404-202601.13.0*).

(DOCUMENTED, [upgrade-node-image](https://learn.microsoft.com/en-us/azure/aks/upgrade-node-image).)

This is stated as a capability that does not exist, so the Pulse records it as `none` rather
than unknown, and I agree with that reading. The rollback affordance this investigation treats
as fundamental for image-based systems — boot the previous known-good slot — is not exposed at
the AKS API even for ACL, which has A/B USR slots underneath. Whether ACL falls back
automatically to the inactive slot on a failed boot is still UNKNOWN; the Pulse flagged it as a
maintainer question and I did not find an answer either.

### Node pool snapshots, and what Microsoft says they are for

The snapshot documentation opens by naming exactly the problem this investigation is about:

> AKS releases a new node image weekly. Every new cluster, new node pool, or upgrade cluster
> always receives the latest image, which can make it hard to maintain consistency and have
> repeatable environments.

(DOCUMENTED, [node-pool-snapshot](https://learn.microsoft.com/en-us/azure/aks/node-pool-snapshot).)

A snapshot is an Azure resource capturing "the node image version, kubernetes version, OS type,
and OS SKU" from a source node pool, which can then create new node pools or new clusters
(DOCUMENTED, same source). Its documented properties matter more than its existence:

- It pins forward only. Upgrading a node pool to a snapshot works only "if the snapshot
  Kubernetes version and node image version are more recent than the current node pool versions.
  And the snapshot node image version is within 90 days of the node image publish date."
- Scaling preserves the pinned image — "Your node pool image version is the same contained in
  the snapshot and remains the same throughout every scale operation" — but any upgrade without
  `--snapshot-id` jumps to latest.
- New node pools must use the same VM family as the source.
- Snapshots must be created in the source region, though they can be used in other regions.

(DOCUMENTED, all from node-pool-snapshot.)

So the reproducibility primitive exists, and it is the most interesting single artifact in this
profile. It gives an operator a named, reusable configuration that survives scale-out, which is
most of what "repeatable environment" means in practice. What it does not give is a way back:
you can freeze and you can replicate, within a 90-day window and a VM family, but you cannot
return a node pool to a version it has already left.

### What rollback does exist

Two coarser mechanisms, both node-pool-granularity and both replace-rather-than-revert:

- **OS SKU change.** The ACL migration guide documents a revert: "change the OS SKU field back
  to your previous value and resubmit the deployment, which triggers another upgrade operation
  and reimages the node pool to its previous OS SKU" (DOCUMENTED,
  [migrate-nodes-azure-container-linux](https://learn.microsoft.com/en-us/azure/aks/migrate-nodes-azure-container-linux)).
  That returns you to a different OS, at whatever its current node image version is — not to a
  prior state.
- **Node pool replacement.** Add a new pool, move workloads, delete the old one (DOCUMENTED,
  same source).

### The platform also reverts things on its own

Node auto-repair is preconfigured on both AKS Automatic and AKS Standard, and runs whether or
not the operator wants it. If a node is `NotReady` for five minutes, AKS reboots it; if it stays
unhealthy, AKS reimages it; if it is still unhealthy and it is a Linux node, AKS redeploys it.
The sequence retries up to three times and "can take up to one hour to complete". Repairs are
initiated by an account named `aks-remediator` and emit `NodeReimageStart` /
`NodeRedeployStart` Kubernetes events (DOCUMENTED,
[node-auto-repair](https://learn.microsoft.com/en-us/azure/aks/node-auto-repair)). I found no
documented opt-out; the documented exclusions are conditions under which repair *doesn't* fire
(certain taints, upgrade annotations), not a setting.

For a self-managed fleet, the first action after a node goes bad is usually to look at it. Here
the platform's first three actions are reboot, reimage, redeploy, and reimage destroys the
evidence. An operator who wants a post-mortem off a failed node has five minutes and no
documented way to extend them.

## 5. Recovery, and the support boundary

The support-policies page is the most useful document in this corpus for the ticket's question,
because it states the boundary as a matrix rather than as prose. Node OS image and patching is
marked **Shared**: "Microsoft provides: Updated node images. Customer provides: Choose an
auto-upgrade channel, or apply manually." Node auto-repair is marked **Microsoft**. Node pool
configuration (VM size, count, labels, taints) is marked **Customer**. Cluster backup and
disaster recovery is **Customer** (DOCUMENTED,
[support-policies](https://learn.microsoft.com/en-us/azure/aks/support-policies)).

Three statements from that page change what investigation even looks like:

> **Microsoft Support has limited access.** Because your agent nodes run private code and store
> sensitive data, Microsoft Support can't sign in to, run commands on, or view logs for these
> nodes without your express permission or assistance.

> Any modification made directly to the agent nodes through the IaaS APIs renders the cluster
> unsupportable.

> You can't change the base OS image or make any direct customizations to these nodes using the
> IaaS APIs or resources. Any custom changes that aren't performed from the AKS API don't
> persist through an upgrade, scale, update, or reboot.

(DOCUMENTED, all from support-policies.)

Microsoft's own access to the cluster runs through a built-in Kubernetes role `aks-service`
bound to an `aks-support` identity, "only enabled under active support tickets with
just-in-time (JIT) access" (DOCUMENTED, same source).

So when something goes wrong on a hyperscaler-managed node, the operator is still the one who
has to go look, and the vendor needs their help to look at all. The recourse is the documented
access paths: `kubectl debug node` with a privileged container, which needs a working Kubernetes
API; or SSH to the node's private IP from inside the cluster VNet, obtained through the AKS ARM
API with `az aks machine list`, which does not need the Kubernetes API; or Azure Bastion if the
proxy node is unreachable. "For security reasons, AKS nodes aren't exposed to the internet"
(DOCUMENTED, [node-access](https://learn.microsoft.com/en-us/azure/aks/node-access)).

That second path is worth noting: a control-plane-independent route to the machine, via the
cloud's own API rather than the cluster's. A self-managed fleet has to build the equivalent —
out-of-band management, a console server, something — and here the surrounding environment
supplies it.

The losses are on the modification side. Node customization has exactly one supported shape —
a privileged `DaemonSet` — and even that is listed as unsupported in the responsibility matrix:
"Microsoft Support can't troubleshoot issues arising from the custom scripts due to their custom
nature" (DOCUMENTED, same source). The recommended way to change a machine is to run a container
on it that changes it, and if that goes wrong you are alone.

## 6. Where ACL changes the answers

ACL is where this investigation's normal dimensions apply. Summarizing what the primary docs
give, deliberately briefly, since Flatcar is a deep-core platform in its own right and ACL
inherits its architecture:

- `/usr` read-only under dm-verity, kernel validating a signed root hash at boot and runtime
  (DOCUMENTED, ACL overview).
- Trusted Launch with Secure Boot and vTPM is required, not optional. Kernel, initramfs and
  cmdline ship as a signed UKI measured into the vTPM (DOCUMENTED, ACL overview).
- SELinux enforcing by default, with the caveat printed in the docs: "SELinux policies might
  evolve over time" (DOCUMENTED, ACL overview).
- Only `NodeImage` and `None` are supported upgrade channels. "`Unmanaged` and `SecurityPatch`
  are incompatible with ACL due to the immutable `/usr` directory" (DOCUMENTED, ACL overview
  and auto-upgrade-node-os-image).
- Weekly full node image replacement is the only update path (DOCUMENTED, ACL overview).
- GA from AKS v1.34. OS Guard's IPE code-integrity features are explicitly not yet supported on
  ACL (DOCUMENTED, ACL overview).

The interesting part for this tier is what immutability costs *here* compared to what it costs
on a self-managed fleet. On ACL an operator loses live patching, in-place package installation,
`SecurityPatch`, and any update granularity smaller than a whole node image. On a self-managed
fleet, giving those up means building replacement machinery: image builds, rollout control,
drain coordination, a rollback story. On AKS that machinery already exists and the operator was
already using it, because `NodeImage` was the default channel and node replacement was already
how updates happened. The marginal cost of immutability is close to zero, and what is left is
the marginal benefit.

That is a real asymmetry and it belongs in the comparison: the same architectural constraint
prices very differently depending on who owns node replacement. I would not extend it further
than the evidence — this is an argument from the documented channel restrictions and defaults
(INFERRED), not something measured.

What does not improve under ACL: the node image still cannot be downgraded, the snapshot still
only pins forward, node auto-repair still reimages after five minutes, and the content manifest
is the one with the stub in it.

## 7. What the framework's 22 dimensions don't ask

The framework handles this tier competently but folds the hyperscaler-specific questions into
dimensions built for a different relationship. Four gaps, offered as proposals rather than
conclusions:

**Who owns the update decision, as a first-class question.** Dimension 4 (Upgrade mechanism)
asks how upgrades work. It does not ask who initiates them, whether the operator can decline,
or whether declining is supported. On AKS those have three different answers for three
different release trains, and the answer for one of them is "you cannot decline". A `SecurityPatch`
node and a `None` node run the same distribution and offer completely different guarantees.

**Reproducibility as attestation versus reproducibility as reconstruction.** Dimension 15
(Supply-chain ownership and reproducibility) implicitly assumes the operator can rebuild. On AKS
the answer is a published manifest of a build you cannot repeat. That is not zero
reproducibility and it is not the same thing as a reproducible build, and the dimension has no
vocabulary for the middle. A useful sub-question: *can the operator obtain the same machine
twice?* — to which AKS's answer is yes, via snapshot, for 90 days, within a VM family.

**Support-scope as an architectural constraint.** Dimension 18 covers lifecycle and support
horizon. It does not capture that support scope forbids otherwise-possible operations: running
a 120-day-old node image, modifying a node through IaaS APIs, building the OS from source. The
capability exists and using it ends the contract. For a regulated operator that is a harder
constraint than a missing feature.

**Forensic availability versus automated recovery.** Dimension 12 (Debugging and day-2) and
dimension 5 (Rollback and recovery) both exist, and the tension between them has no home. AKS
reimages an unhealthy node after five minutes by default. Whether an operator can get a
post-mortem off a node before the platform replaces it is a real operational property and
nothing in the framework asks for it.

I would not add all four as dimensions. The first and the fourth look like genuine missing
questions. The second and third look more like missing sub-questions inside 15 and 18.

## 8. For the GCOS sibling

Things this profile had to discover the hard way, which the Google Container-Optimized OS
profile will likely want to ask in the same shape. I did no GCOS research; these are questions,
not expectations.

- Is there a supported path off the provider's own platform, and does support scope differ from
  license scope?
- What is published per node image version — a content manifest, an SBOM, a provenance
  attestation, or only a version string? And does the immutable variant publish more or less
  than the mutable one?
- Is there a release train that applies automatically, distinct from the ones the operator
  triggers?
- Can a node image version be downgraded? If not, what is the coarsest available revert?
- Is there a pinning primitive equivalent to a node pool snapshot, and does it have an expiry?
- Does the platform reimage or replace unhealthy nodes automatically, on what timer, and can it
  be turned off?
- What is the maximum supported age of a node image?

A cross-provider table of those seven answers would be the useful artifact of post #6, and it is
the part neither profile can produce alone.

## Evidence ledger

Primary sources cited: 17 distinct documents and repository paths, all Microsoft-published —
learn.microsoft.com Azure Linux and AKS documentation, the `Azure/AKS` and `Azure/AgentBaker`
repositories. No secondary or blog sources were used. Two sources are the Pulse profile
(the Pulse brief/PR the profiles change) and this funnel's own README and research framework, both internal and both
labelled as such where cited.

Claim labels, counted by distinct factual assertion rather than by sentence:

- DOCUMENTED: 41
- INFERRED: 4 (the `listInstalledPackages` stub's cause; the absence of a node-image-version CLI
  parameter; the marginal-cost-of-immutability argument in §6; the framework-gap proposals in §7
  are argument rather than fact and are marked as proposals)
- UNKNOWN: 5 (no documented rebuild-and-compare procedure; no published node-image SBOM or
  provenance; self-managed Kubernetes on Azure Linux; whether ACL auto-falls-back to the
  inactive USR slot; whether ACL package inventory is published anywhere)
- NOT TESTED: everything. No cluster was created, no image was built, no failure was injected.

As the ticket predicted, this tier carries more unlabelled-as-fact material than the deep-core
platforms will. The five UNKNOWNs above are all cases where Microsoft's documentation is silent
on a mechanism, and I have left them silent rather than reasoning about what is probably
happening internally.

## Claims needing maintainer review

Nothing here is a comparative claim about Kairos, and Kairos is not mentioned in the analysis.
The bias-control requirement that applies to this document is the general one — don't let a
vendor's own framing become the category definition — and the place it bites is §6, where I
accept Microsoft's characterization of ACL's immutability without independent verification,
because verifying it would mean the reverse-engineering this tier is told not to do.

Three items I would put to a Microsoft maintainer before anything derived from this is published:

1. Is the `listInstalledPackages stub` in ACL release notes a known gap, and is ACL package
   inventory published elsewhere?
2. Does ACL fall back automatically to the inactive USR slot on a failed boot? (Inherited from
   the Pulse's open questions; still unanswered.)
3. Is there a supported way to pin a node image version beyond the snapshot's 90-day window, for
   operators with change-freeze requirements?

## Open questions carried forward

- Whether the `Azure/AKS` `vhd-notes` lag behind AgentBaker's `release-notes` is transient or
  structural, and which Microsoft considers canonical.
- Whether `SecurityPatch` live-patching without draining pods has a documented boundary — which
  package classes can be applied live versus which force a reimage. The docs say "certain kernel
  security packages" and stop there.
- What happens to a pinned node pool when its snapshot's 90-day window expires. The docs
  describe the constraint on *creating* from a snapshot; they do not describe the state of a
  pool already running one.
