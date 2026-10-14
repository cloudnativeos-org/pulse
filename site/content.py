"""Reader-route content for the Cloud Native OS Pulse: "Looks alike, differs on" pairs and
"Start here" blocks. Data only, plus two render functions that produce the same markup as
build.py's sample pair() and start_here().

Drop-in:
    from content import PAIRS, START_HERE_BLOCKS, render_pairs, render_start_here
    pr = render_pairs(P, S, E, badge, dim_of, flag, BASE_CHOICE)      # replaces pair(P, S)
    {render_start_here(E)}                                             # replaces start_here()

Field keys (every sentence lists the profile fields it rests on; cites come from them):
    "flatcar:d04.scope"          dimensions.d04_*.normalized.scope (or a top-level dimension
                                 key such as summary, notes, unknowns, evidence)
    "flatcar:taxonomy.notes"     top-level profile key; no source list, so no citation link
    "base_choice:kairos"         drafts/base_choice.yaml (proposed field, not in the dataset)
A sentence is (text, [field keys]) or (text, [field keys], (pid, column)) to attach a
Fact-fix flag. Text is plain; `backticks` become <code>. No em dashes.
"""
import re

PAIRS = [
    # ------------------------------------------------------------------ Flatcar / ACL
    dict(
        id="pair-flatcar-acl", a="flatcar", b="azure-container-linux",
        headline="Same design lineage and the same A/B /usr layout. They differ on where they are documented to run, so on how an update reaches a node.",
        shared=[
            ("Microsoft documents ACL as derived from Flatcar Container Linux, and the shipped os-release carries ID_LIKE=\"flatcar\".",
             ["azure-container-linux:d01.notes"]),
            ("Both mount `/usr` read-only under dm-verity and keep `/etc` and `/var` writable.",
             ["flatcar:d02.read_only", "flatcar:d02.integrity_mechanism", "flatcar:d02.writable_and_persistent",
              "azure-container-linux:d02.read_only", "azure-container-linux:d02.integrity_mechanism", "azure-container-linux:d02.writable"]),
            ("Neither image bundles Kubernetes. Both release amd64 and arm64 images.",
             ["flatcar:d07.bundled", "azure-container-linux:d07.bundled",
              "flatcar:d08.architectures_released", "azure-container-linux:d08.architectures_released"]),
        ],
        rows=[
            ("diff", "Differs on: where it is documented to run",
             [("Bare metal, virtual machines and public clouds. Single-board computers are experimental.",
               ["flatcar:d08.platforms"])],
             [("AKS, an Azure Marketplace VM image, and QEMU/KVM for development and CI. Bare metal, on-premises and other clouds are not documented. The profile records that as a gap, not as a prohibition.",
               ["azure-container-linux:d08.platforms_supported", "azure-container-linux:d08.platforms_not_documented", "azure-container-linux:d08.notes"])]),
            ("side", "So an update reaches a node",
             [("The node polls for it and switches its A/B `/usr` partitions. The update server is self-hostable.",
               ["flatcar:d04.initiator", "flatcar:d04.mechanism", "flatcar:d04.self_hostable_update_server"]),
              ("On AKS, Microsoft disabled this A/B update in favour of node image replacement, and AKS no longer supports Flatcar for AKS (preview) from 2026-06-08.",
               ["flatcar:d12.notes"])],
             [("On AKS, as a full node image replacement on a weekly cadence, through the NodeImage or None channels only.",
               ["azure-container-linux:d04.mechanism_in_use_on_aks", "azure-container-linux:d04.supported_upgrade_channels", "azure-container-linux:d14.release_cadence"]),
              ("An A/B slot design exists in the repository, and A/B update for UKI images was enabled there on 2026-10-02. No source says that AKS uses it.",
               ["azure-container-linux:d04.summary", "azure-container-linux:d04.notes", "azure-container-linux:d04.unknowns"])]),
            ("side", "And a bad update is undone by",
             [("The bootloader, by itself, when the new version is not marked successful.",
               ["flatcar:d05.summary", "flatcar:d05.automatic_rollback_on_boot_failure", "flatcar:d05.automatic_rollback_trigger"])],
             [("Not determined for a node. The documented reversal is a node-pool reimage to the previous OS SKU. AKS documents that a node image version cannot be downgraded.",
               ["azure-container-linux:d05.automatic_rollback_on_boot_failure", "azure-container-linux:d05.aks_os_sku_rollback", "azure-container-linux:d05.aks_node_image_downgrade"])]),
        ],
        foot="Neither design is ranked. A node that updates itself keeps the update path with the operator; a node image that the managed service replaces moves the update path, and its timing, to the service.",
        foot_col=("update", "Update unit"),
    ),
    # ------------------------------------------------------------------ Kairos / bootc
    dict(
        id="pair-kairos-bootc", a="kairos", b="bootc",
        headline="Both run on a base you choose and update from an OCI image. They differ on what the project ships on top of that base.",
        shared=[
            ("Both document running on, or converting, a base distribution that the adopter picks.",
             ["base_choice:kairos", "base_choice:bootc"]),
            ("The primary artifact is an OCI image, distributed through a standard registry.",
             ["kairos:d03.primary_artifact", "kairos:d03.oci_registry_distribution",
              "bootc:d03.primary_artifact", "bootc:d03.oci_registry_distribution"]),
            ("Neither update path requires Kubernetes.",
             ["kairos:d04.requires_kubernetes", "bootc:d04.requires_kubernetes"]),
        ],
        rows=[
            ("diff", "Differs on: what the project ships",
             [("A framework and a distribution. It releases OS images, for the Hadron base only as of v4.3.0. Standard images bundle Kubernetes; core images ship none.",
               ["kairos:entry_kind", "kairos:d01.summary", "kairos:d01.bases_with_released_os_images", "kairos:d07.bundled"])],
             [("A mechanism. It ships no OS image. Kubernetes comes with images built on it, such as MicroShift on RHEL image mode.",
               ["base_choice:bootc", "bootc:d01.ships_an_os", "bootc:d07.requirement", "bootc:d07.bundled"])]),
            ("side", "So rollback and recovery are",
             [("Part of the project: automatic rollback after a failed boot (one attempt on the GRUB path, three on Trusted Boot), a recovery partition and a factory reset.",
               ["kairos:d05.automatic_rollback_on_boot_failure", "kairos:d05.automatic_rollback_attempts",
                "kairos:d05.recovery_environment", "kairos:d05.factory_reset"])],
             [("Shared with the adopting distribution. A manual rollback reorders the existing deployments. Automatic reversion depends on the backend: boot entry counting can be configured on OSTree and is not configured on composefs. The docs state no trigger or attempt count. Recovery media and factory reset belong to the distribution.",
               ["bootc:d05.rollback_mechanism", "bootc:d05.automatic_rollback_on_boot_failure",
                "bootc:d05.recovery_environment", "bootc:d05.factory_reset", "bootc:d05.notes"], ("bootc", "rollback"))]),
        ],
        foot="Neither design is ranked. A project that ships the OS also ships its recovery path and its Kubernetes choice; a mechanism leaves those choices, and their upkeep, to whoever builds the image.",
        foot_col=("byod", "Bring your own distro"),
    ),
    # ------------------------------------------------------------------ Fedora CoreOS / bootc
    dict(
        id="pair-fcos-bootc", a="fedora-coreos", b="bootc",
        headline="Both stage OSTree-backed deployments from an OCI image. They differ on who builds the image, so on who runs the update path.",
        shared=[
            ("An update stages a new deployment and leaves the running system unchanged until it is applied.",
             ["fedora-coreos:d04.summary", "bootc:d04.summary"]),
            ("The update payload is an OCI image.",
             ["fedora-coreos:d03.primary_artifact", "bootc:d03.primary_artifact"]),
            ("`/etc` and `/var` are writable, and `/etc` changes carry forward through a three-way merge.",
             ["fedora-coreos:d02.writable_and_persistent", "fedora-coreos:d02.etc_merge",
              "bootc:d02.writable_and_persistent", "bootc:d02.etc_merge"]),
            ("Two versions stay on disk. A manual rollback reorders them.",
             ["fedora-coreos:d05.retained_versions", "fedora-coreos:d05.summary",
              "bootc:d05.retained_versions", "bootc:d05.rollback_mechanism"]),
        ],
        rows=[
            ("diff", "Differs on: who builds the image",
             [("Fedora does. You configure the prebuilt image at first boot with Ignition. The project discourages package layering and points heavier customization to Fedora bootc.",
               ["fedora-coreos:taxonomy.construction_model", "fedora-coreos:d06.mechanisms",
                "fedora-coreos:d06.runtime_package_install", "fedora-coreos:d06.notes"])],
             [("You do. Customization is a Containerfile that derives from a base image. The adopter owns the build, test, signing and patching of the result.",
               ["bootc:d06.model", "bootc:d06.notes"])]),
            ("side", "So the update path is",
             [("Shipped and on by default. An agent polls an update graph with phased rollout, and the graph server is self-hostable. Rollback is manual and needs console access.",
               ["fedora-coreos:d04.auto_update_default", "fedora-coreos:d04.initiator", "fedora-coreos:d04.phased_rollout",
                "fedora-coreos:d04.self_hostable_update_server", "fedora-coreos:d05.rollback_requires_console",
                "fedora-coreos:d05.automatic_rollback_on_boot_failure"])],
             [("The adopter's to assemble: an operator command or a systemd timer, with no phased rollout. Signature checks are policy-based and permissive by default. Automatic reversion depends on the backend, and no trigger is stated.",
               ["bootc:d04.initiator", "bootc:d04.phased_rollout", "bootc:d04.artifact_verification",
                "bootc:d05.automatic_rollback_on_boot_failure", "bootc:d05.notes"], ("bootc", "rollback"))]),
        ],
        foot="Neither design is ranked. A prebuilt image comes with the project's update pipeline; a derived image puts its content, and the update pipeline, with the adopter.",
        foot_col=("constr", "Who owns the artifact"),
    ),
    # ------------------------------------------------------------------ Fedora CoreOS / openSUSE MicroOS
    dict(
        id="pair-fcos-microos", a="fedora-coreos", b="microos",
        headline="Both update atomically and ship no Kubernetes in the image. They differ on what one update is, so on what a rollback can reach.",
        shared=[
            ("Both are general-purpose hosts. Neither ships Kubernetes.",
             ["fedora-coreos:d01.workload_scope", "fedora-coreos:d01.ships_kubernetes",
              "microos:d01.workload_scope", "microos:d01.ships_kubernetes"]),
            ("The root is read-only, and `/var` sits outside what an update or a rollback replaces.",
             ["fedora-coreos:d02.read_only", "fedora-coreos:d02.survives_upgrade",
              "microos:d02.read_only", "microos:d02.var_mechanism"]),
            ("An update is prepared beside the running system and takes effect on reboot.",
             ["fedora-coreos:d04.summary", "microos:d04.summary"]),
            ("Both record a rolling support model with no LTS stream.",
             ["fedora-coreos:d14.support_model", "microos:d14.support_model"]),
        ],
        rows=[
            ("diff", "Differs on: what one update is",
             [("A new OSTree deployment, fetched as a GPG-signed OCI image.",
               ["fedora-coreos:d04.mechanism", "fedora-coreos:d03.primary_artifact", "fedora-coreos:d03.signed"])],
             [("A new btrfs snapshot of the root, with package changes applied inside it. `/etc` is an overlay with a work directory per snapshot.",
               ["microos:d04.mechanism", "microos:d04.steps", "microos:d04.scope", "microos:d02.etc_mechanism"])]),
            ("side", "So a rollback reaches",
             [("The one previous deployment, by hand, with console access. No automatic rollback ships.",
               ["fedora-coreos:d05.retained_versions", "fedora-coreos:d05.rollback_requires_console",
                "fedora-coreos:d05.automatic_rollback_on_boot_failure"])],
             [("Any retained snapshot, by command or from the boot menu. health-checker rolls back by itself when boot checks fail. Retention is a snapper policy; its default on MicroOS is not determined.",
               ["microos:d05.rollback_mechanism", "microos:d05.automatic_rollback_on_boot_failure",
                "microos:d05.automatic_rollback_trigger", "microos:d05.retained_versions", "microos:d05.retained_versions_microos"],
               ("microos", "rollback"))]),
        ],
        foot="Neither design is ranked. A fixed pair of deployments keeps one known restore point; a snapshot history keeps as many as its retention policy allows, and each update is assembled from packages on the node.",
        foot_col=("rollback", "Automatic rollback"),
    ),
    # ------------------------------------------------------------------ Talos / Bottlerocket
    dict(
        id="pair-talos-bottlerocket", a="talos", b="bottlerocket",
        headline="Both are minimal, API-managed images with whole-image A/B updates. They differ on how Kubernetes is tied to the image.",
        shared=[
            ("Neither OS has its own SSH server or shell, and neither installs packages at run time. Operations go through an API. Bottlerocket offers SSH and a shell through an optional admin container.",
             ["talos:d11.ssh", "talos:d11.local_shell", "talos:d11.api", "talos:d06.runtime_package_install",
              "bottlerocket:d11.ssh", "bottlerocket:d11.local_shell", "bottlerocket:d11.api", "bottlerocket:d06.runtime_package_install"]),
            ("An update writes a whole image to the inactive partition set. If the new image fails its one boot attempt, the machine reverts by itself.",
             ["talos:d04.mechanism", "talos:d04.scope", "talos:d05.automatic_rollback_on_boot_failure", "talos:d05.automatic_rollback_attempts",
              "bottlerocket:d04.mechanism", "bottlerocket:d04.scope", "bottlerocket:d05.automatic_rollback_on_boot_failure", "bottlerocket:d05.automatic_rollback_attempts"]),
        ],
        rows=[
            ("diff", "Differs on: how Kubernetes is tied to the image",
             [("Kubernetes is required and bundled, and the OS manages it. Kubernetes and the OS upgrade separately.",
               ["talos:d07.requirement", "talos:d07.bundled", "talos:d07.os_manages_kubernetes",
                "talos:d07.independent_lifecycle", "talos:d04.kubernetes_upgrade_separate"])],
             [("Each orchestrator variant bundles one agent: a Kubernetes minor version, or ECS. A non-orchestrator variant family also exists, so Kubernetes is optional across the project. The Kubernetes minor is part of the variant name.",
               ["bottlerocket:d07.requirement", "bottlerocket:d07.bundled", "bottlerocket:d07.distributions", "bottlerocket:d07.summary"])]),
            ("side", "So a move to a new Kubernetes minor is",
             [("An upgrade on the same node, independent of the OS version. Talos v1.14 supports five Kubernetes minors.",
               ["talos:d07.independent_lifecycle", "talos:d07.kubernetes_versions_supported"])],
             [("A variant change, which the docs describe as a node replacement. The updater refuses updates for a different variant.",
               ["bottlerocket:d04.cross_variant_upgrade", "bottlerocket:d04.notes", "bottlerocket:d07.independent_lifecycle"])]),
        ],
        foot="Neither design is ranked. A Kubernetes version fixed per image keeps the image one unit and makes a Kubernetes upgrade a node replacement; a separate Kubernetes lifecycle keeps the node in place and makes the OS responsible for Kubernetes.",
        foot_col=("k8s", "Kubernetes"),
    ),
    # ------------------------------------------------------------------ COS / Bottlerocket
    dict(
        id="pair-cos-bottlerocket", a="cos", b="bottlerocket",
        headline="Both are hyperscaler-owned images with a read-only root and whole-image A/B updates. They differ on where they run, and on how much of the update source and rollback the OS documentation describes.",
        shared=[
            ("A single vendor holds the trademark and is the main sponsor.",
             ["cos:d13.vendor_neutral_ownership", "cos:d13.trademark_holder", "cos:d13.primary_commercial_sponsor",
              "bottlerocket:d13.vendor_neutral_ownership", "bottlerocket:d13.trademark_holder", "bottlerocket:d13.primary_commercial_sponsor"]),
            ("The root filesystem is read-only, and `/etc` does not survive a reboot. An update writes the whole root to the passive partition set. COS is also updated by replacing the image.",
             ["cos:d02.read_only", "cos:d02.ephemeral", "cos:d04.mechanism", "cos:d04.scope_by_mode",
              "bottlerocket:d02.read_only", "bottlerocket:d02.ephemeral", "bottlerocket:d04.mechanism", "bottlerocket:d04.scope"]),
            ("Each is the only node image in one mode of its vendor's managed Kubernetes.",
             ["cos:d07.managed_kubernetes_sole_node_image", "bottlerocket:d07.managed_kubernetes_sole_node_image"]),
        ],
        rows=[
            ("diff", "Differs on: where it runs",
             [("Only on the vendor's cloud: its compute service and its managed Kubernetes. Other clouds, bare metal, on-premises and edge are not supported.",
               ["cos:d01.runs_outside_vendor_cloud", "cos:d08.platforms", "cos:d08.platforms_not_supported"])],
             [("EC2, VMware and local QEMU/KVM. The bare-metal Kubernetes variants are discontinued.",
               ["bottlerocket:d08.platforms", "bottlerocket:d08.platforms_discontinued"])]),
            ("side", "And the OS documentation on updates and rollback",
             [("Names no update server, does not describe payload verification, and publishes no rollback procedure. The A/B scheme exists, so rollback reads Unknown, not No.",
               ["cos:d04.unknowns", "cos:d04.artifact_verification", "cos:d04.requires_vendor_infrastructure",
                "cos:d05.summary", "cos:d05.notes", "cos:d05.evidence", "cos:d05.automatic_rollback_on_boot_failure"])],
             [("Describes both. The update repository is self-hostable and checked against TUF metadata. Automatic rollback after a failed boot is documented.",
               ["bottlerocket:d04.self_hostable_update_server", "bottlerocket:d04.artifact_verification",
                "bottlerocket:d05.automatic_rollback_on_boot_failure"])]),
        ],
        foot="Neither design is ranked. A single-cloud scope ties updates and repair to that cloud's managed services; a wider scope needs an update source that works without them. An Unknown in a profile is not a No.",
        foot_col=("selfhost", "Self-hostable update source"),
    ),
]


START_HERE_BLOCKS = [
    ("sh-managed", "If you use the node OS your cloud provider gives you", [
        ("Is the OS the default node image on your managed Kubernetes, an opt-in, or the only choice in some cluster modes?",
         []),
        ("Who starts an update: the node, you, or the managed service?",
         [("Matrix", "#matrix?col=fleet", "column: Fleet upgrade paths")]),
        ("Does the image run anywhere outside that one cloud?",
         []),
        ("If a new node image fails, does the node revert, or does the service replace it?",
         [("Matrix", "#matrix?rollback=yes", "filter: Automatic rollback, Yes")]),
        ("Who holds the project assets, and who sells support?",
         [("Matrix", "#matrix?col=own", "column: Who holds the assets")]),
    ]),
    ("sh-capi", "If you run Kubernetes on your own hardware with Cluster API", [
        ("Is there a Cluster API provider for the OS, of which type, and who maintains it?",
         [("Matrix", "#matrix?col=capi", "column: Cluster API")]),
        ("Is Kubernetes in the image, or does your bootstrap install it?",
         [("Matrix", "#matrix?col=k8s", "column: Kubernetes")]),
        ("Can the OS and Kubernetes upgrade separately?",
         []),
        ("How does a new machine get installed with no one at the keyboard?",
         [("Matrix", "#matrix?day0=pxe", "filter: Day-0 path, PXE")]),
        ("Can the update source live on your own network?",
         [("Matrix", "#matrix?selfhost=yes", "filter: Self-hostable update source")]),
    ]),
    ("sh-regulated", "If you run in a regulated or air-gapped environment", [
        ("Can a node check that an update is signed before it applies it?",
         [("Matrix", "#matrix?verified=yes", "filter: Update signature check, Possible")]),
        ("Can updates come from a mirror on your own network, with no call to the project or vendor?",
         [("Matrix", "#matrix?selfhost=yes", "filter: Self-hostable update source")]),
        ("What does the project publish about what is in the image and how it was built?",
         []),
        ("Are FIPS builds available, and from whom?",
         []),
        ("Can a machine be recovered with no network?",
         []),
        ("How long is a release supported, and is there a published end date?",
         [("Matrix", "#matrix?col=support", "column: Support model")]),
    ]),
    ("sh-gpu", "If you run GPU or AI workloads", [
        ("Are GPU drivers published for your accelerator and your architecture?",
         [("Matrix", "#matrix?col=ai", "column: AI accelerators")]),
        ("How does a kernel module reach an image the node cannot change at run time?",
         [("Matrix", "#matrix?col=ai", "column: AI accelerators")]),
        ("Do the driver and the kernel update together, as one unit?",
         [("Matrix", "#matrix?col=ai", "column: AI accelerators")]),
        ("With Secure Boot on, how do out-of-tree modules get signed?",
         []),
        ("If a driver update stops the node from booting, does it revert by itself?",
         [("Matrix", "#matrix?rollback=yes", "filter: Automatic rollback, Yes")]),
    ]),
    ("sh-device", "If you build a device that ships with the OS inside", [
        ("Who builds and patches the image you ship: the project, or you?",
         [("Matrix", "#matrix?col=constr", "column: Who owns the artifact")]),
        ("Can you start from a base distribution you choose?",
         [("Matrix", "#matrix?byod=yes", "filter: Bring your own distro, Yes")]),
        ("Which of your board architectures have released images, not only build tooling?",
         [("Matrix", "#matrix?arch=arm64", "filter: Architecture, arm64")]),
        ("How is the image written at the factory, and how does it get its first configuration?",
         [("Matrix", "#matrix?day0=disk", "filter: Day-0 path, Disk image")]),
        ("After a bad update in the field, does the device undo it alone, and can it be reset?",
         [("Matrix", "#matrix?rollback=yes", "filter: Automatic rollback, Yes")]),
        ("How long is a release supported, and who sells support beyond that?",
         [("Matrix", "#matrix?col=support", "column: Support model")]),
    ]),
    ("sh-learn", "If you run a homelab or want to learn how these systems work", [
        ("Does it install on the hardware you have: a mini PC, a single-board computer, a VM?",
         [("Matrix", "#matrix?day0=iso", "filter: Day-0 path, ISO")]),
        ("Do you want Kubernetes in the image, or to add it yourself?",
         [("Matrix", "#matrix?col=k8s", "column: Kubernetes")]),
        ("What does an update replace, and what survives it?",
         [("Matrix", "#matrix?col=update", "column: Update unit")]),
        ("If an update breaks the boot, does it undo itself?",
         [("Matrix", "#matrix?rollback=yes", "filter: Automatic rollback, Yes")]),
        ("When something goes wrong, can you get a shell, or only an API?",
         []),
        ("Who holds the project assets, and how open is its governance?",
         [("Matrix", "#matrix?col=own", "column: Who holds the assets")]),
    ]),
]


# ---------------------------------------------------------------- rendering
def _text(E, s):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", E(s))


def _dims(keys):
    """Ordered unique (pid, dim) pairs that carry a source list."""
    out = []
    for k in keys:
        pid, rest = k.split(":", 1)
        if pid == "base_choice":
            item = ("base_choice", rest)
        elif re.match(r"d\d\d\.", rest):
            item = (pid, rest[:3])
        else:
            continue  # taxonomy.*, entry_kind: profile fields without their own sources
        if item not in out:
            out.append(item)
    return out


def _sentence(sent, P, S, E, badge, dim_of, flag, BASE_CHOICE):
    text, keys = sent[0], sent[1]
    marks = []
    for pid, dim in _dims(keys):
        if pid == "base_choice":
            d = BASE_CHOICE.get(dim, {})
            srcs = d.get("sources") or []
            if srcs:
                n = S.add(dict(srcs[0], title=srcs[0].get("title") or srcs[0]["url"].split("//")[1], retrieved="2026-09-22"), P[dim]["name"])
                marks.append('<sup class="cite">[<a href="#src-%d" aria-label="Source %d">%d</a>]</sup>' % (n, n, n))
            if d.get("evidence") and d["evidence"] != "DOCUMENTED":
                marks.append(badge(d["evidence"], compact=True))
            continue
        p = P[pid]
        marks.append(S.cite(p, dim))
        ev = dim_of(p, dim).get("evidence")
        if ev and ev != "DOCUMENTED":
            marks.append(badge(ev, compact=True))
    if len(sent) > 2:
        marks.append(flag(*sent[2], inline_note=False))
    return _text(E, text) + ("".join(marks) and " " + "".join(marks))


def render_pairs(P, S, E, badge, dim_of, flag, BASE_CHOICE, pairs=None):
    out = []
    for pr in pairs or PAIRS:
        a, b = P[pr["a"]], P[pr["b"]]
        say = lambda sents: " ".join(_sentence(s, P, S, E, badge, dim_of, flag, BASE_CHOICE) for s in sents)
        link = lambda p: '<a class="proj-open" href="#tc-%s">%s</a>' % (p["id"], E(p["name"]))   # opens the entry's data sheet on the matrix page
        grid = ['<div class="rl colh empty"></div><div class="colh">%s</div><div class="colh">%s</div>' % (link(a), link(b)),
                '<div class="rl">Shared</div><div class="same">%s</div>' % say(pr["shared"])]
        for kind, label, left, right in pr["rows"]:
            if kind == "diff":
                grid.append('<div class="rl diff-row diff-label">%s</div><div class="side diff-row" data-p="%s">%s</div><div class="side diff-row" data-p="%s">%s</div>'
                            % (E(label), E(a["name"]), say(left), E(b["name"]), say(right)))
            else:
                grid.append('<div class="rl">%s</div><div class="side" data-p="%s">%s</div><div class="side" data-p="%s">%s</div>'
                            % (E(label), E(a["name"]), say(left), E(b["name"]), say(right)))
        col, col_name = pr["foot_col"]
        out.append(
            '<article class="pair" aria-labelledby="%s"><div class="pair-head"><span class="eyebrow">Looks alike, differs on</span>'
            '<h3 id="%s">%s</h3></div><div class="pair-grid">%s</div>'
            '<div class="pair-foot">%s Read the matrix column <a href="#matrix?col=%s">%s</a> for every entry.</div></article>'
            % (pr["id"], pr["id"], _text(E, pr["headline"]), "".join(grid), E(pr["foot"]), col, E(col_name)))
    return "".join(out)


def render_start_here(E, blocks=None):
    out = []
    for sid, heading, qs in blocks or START_HERE_BLOCKS:
        lis = []
        for q, links in qs:
            to = "".join('<span><span class="kind">%s</span> <a href="%s">%s</a></span>' % (k, h, E(t)) for k, h, t in links)
            if not links:
                to = '<span class="to-none">Not in the matrix yet</span>'  # kept on purpose: the question still matters
            lis.append('<li><span class="q">%s</span><span class="to">%s</span></li>' % (E(q), to))
        out.append('<section class="sh" aria-labelledby="%s"><div class="sh-head"><span class="eyebrow">Use case</span>'
                   '<h3 id="%s">%s</h3></div><ol>%s</ol></section>'
                   % (sid, sid, E(heading), "".join(lis)))
    return "".join(out)
