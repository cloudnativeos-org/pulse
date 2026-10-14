# FR-14 — Secure Boot key ownership across five projects

Backlog id **FR-14**, tracked as
, a follow-up
from the cloud native OS Pulse 2026 (the Pulse brief),
under the Reproducible Machine State epic (the research epic).

Research window 2026-09-16. All sources retrieved 2026-09-16 unless noted.

Scope: for Kairos, Fedora CoreOS, Bottlerocket, Flatcar and Talos, establish who holds the
signing key for the officially released artifact, whether the shim is CA-signed, what
enrolment an operator must perform on stock firmware, and what happens to out-of-tree kernel
modules under lockdown.

---

## THE FINDING THAT NEEDS MAURO'S VERIFICATION

**The Kairos architecture page at <https://kairos.io/docs/architecture/secureboot/> is
currently wrong about the only artifact Kairos ships.**

The page says:

> Any of the current supported flavors in Kairos can be used with SecureBoot out of the box in
> UEFI mode.

The only base with released OS images as of v4.3.0 is Hadron. I pulled the published
`ghcr.io/kairos-io/hadron:main` image (revision `4ffdf3c`, built 2026-09-15) and parsed the PE
headers of every file that would make up a Secure Boot chain. All of them carry an **empty
Authenticode certificate table** — they are unsigned:

| file in the image | size | certificate table |
|---|---|---|
| `usr/share/efi/x86_64/shim.efi` | 1 065 415 B | offset 0, size 0 |
| `usr/lib/grub/x86_64-efi/grubx64.efi` | 1 290 240 B | offset 0, size 0 |
| `usr/lib/systemd/boot/efi/systemd-bootx64.efi` | 124 928 B | offset 0, size 0 |
| `boot/vmlinuz-7.1.8-hadron` | 18 375 168 B | offset 0, size 0 |

Evidence label: **REPRODUCED**. Method and full chain of evidence in
[The Kairos deep-dive](#the-kairos-deep-dive) below.

On stock UEFI firmware with Secure Boot enabled, none of these will load. An official Kairos
v4.3.0 Hadron ISO does not boot with Secure Boot on, under any key, unless the operator first
builds and signs their own artifacts and enrols their own certificate.

**This is INFERRED-verified, not settled by a maintainer.** The ticket filed it as research
precisely because it was inferred. What I have added is the empirical half: the binaries are
demonstrably unsigned. What I have *not* got is a primary source from the project stating the
intent — no Kairos or Hadron document says "the GRUB-path Hadron artifacts are unsigned and
Secure Boot does not apply to them", and no issue tracks it. Before anyone acts on this, Mauro
should confirm (a) that I am reading the right published artifact, and (b) whether this is a
known gap with an unwritten plan or a genuine documentation defect. It is his project and his
call. Do not treat this section as settled on my say-so.

If it is confirmed, the operator cost is concrete and immediate: someone with Secure Boot
mandated by policy reads the architecture page, downloads the official ISO, and it does not
boot, with no documentation anywhere explaining why.

---

## Why this document is shaped the way it is

No standardized project-profile template survives from the methodology plan — that ticket was closed and
superseded by the Pulse brief before producing one. the platform-profile task (NixOS), the platform-profile task (Unikraft) and the platform-profile task (Azure Linux)
each hit the same gap, designed a structure for their own question, and recorded the choice
in-doc. Same precedent here.

This ticket's shape is not a platform profile. It is one narrow question asked identically of
five projects, where the interesting output is the *spread* of answers, plus one urgent
single-project finding. So the structure is:

1. The Kairos finding first, because the ticket says the Kairos half is the urgent half and
   burying it at the end would be the wrong call.
2. The cross-project comparison table, which is the artifact a reader actually wants.
3. Per-project findings, four questions each, in a fixed order so they are comparable.
4. The Kairos deep-dive with the full evidence chain.
5. What remains unknown, and the maintainer questions that would close each gap.

Not the 22 dimensions in order: this sits inside dimension 9 (security and chain of trust) and
touches perhaps a fifth of it. Not a mirror of the Pulse YAML profiles either — those already
answer the categorical question and I am not redoing them. Where a Pulse profile already
carries a finding I verified independently, I say so.

### Evidence labels

Per research-framework.md's evidence standard: **DOCUMENTED** (explicit in a primary source),
**REPRODUCED** (independently tested using a documented procedure), **OBSERVED** (measured in
our experiments), **INFERRED** (reasonable conclusion, not explicitly documented), **UNKNOWN**
(insufficient evidence), **NOT TESTED**. Missing documentation is never treated as proof of
absence.

### Bias control

Mauro maintains Kairos. Per the funnel README, Kairos gets the same treatment as everyone
else — and on this particular question it comes out worst of the five. That is recorded
without softening. Equally, Bottlerocket's self-signed choice and Flatcar's stalled
shim-review are recorded as what they are — a documented design decision and a stalled
process — not as failures, and Talos's constraint is examined for what it buys. No negative
claim about any project here has been put to that project's maintainers. Nothing in this
document is publication-ready for that reason.

---

## The cross-project answer

Five projects, five different answers behind one checkbox.

| | who holds the key | shim CA-signed? | enrolment on stock firmware | out-of-tree modules under lockdown |
|---|---|---|---|---|
| **Fedora CoreOS** | nobody, in effect — stock Fedora `shim-x64`, `grub2-efi`, `kernel` RPMs, so Fedora/Red Hat's keys | **Yes**, Microsoft 3rd-party UEFI CA | **None.** Firmware must trust the 3rd-party CA, which stock firmware does | Blocked. Lockdown is `integrity` whenever Secure Boot is on and cannot be lowered. Fedora signs modules with an ephemeral per-build key, so layering NVIDIA means your own key + MOK enrolment |
| **Bottlerocket** | the project (AWS): its own PK/KEK/db/vendor CAs and three signing keys | **No**, deliberately self-signed, with a written rationale | **Yes** on bare metal — import `db.crt`/`db.cer` from the ESP via the firmware setup menu. On AWS/VMware the platform pre-enrols it | Handled by turning lockdown **off**: `*-nvidia` and `*-dev` variants ship `lockdown = none` while keeping Secure Boot on. No operator-facing module-signing key |
| **Flatcar** | the project: a self-signed Flatcar CA, private key in an Azure Key Vault HSM | **No** — self-signed, described by a maintainer on 2026-07-10 as "temporary … until we get a formally signed certificate from Microsoft". No submission exists in `rhboot/shim-review` | **Yes** — enrol Flatcar's DB certificate, or sign their shim with your own DB key. No Secure Boot page in the docs at all | Lockdown `integrity` when Secure Boot is on (`CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT=y`). NVIDIA and ZFS sysexts are pre-signed with the ephemeral key so they load |
| **Talos** | Sidero Labs, for the official Image Factory assets. A self-signed root, published at a public URL | **No shim at all** — systemd-boot loads a UKI signed by the Sidero Labs key, verified directly by firmware | **Yes** — auto-enrolled under virtualization, manual from the boot menu on bare metal, or build with `enrollKeys: force` | `module.sig_enforce=1` on every image since v1.12, independent of lockdown. Lockdown `confidentiality` before v1.14.0, **`none` in v1.14.0 (a regression)**, `integrity` from v1.14.1. Sidero decided against letting operators enrol a module key |
| **Kairos** | **nobody — the released artifact is not signed at all** | **No shim signature of any kind.** Hadron builds shim 16.1 from rhboot source with no signing step, no vendor cert and no shim-review submission | **Secure Boot must be turned off.** The only signed path is Trusted Boot, which you build yourself with `auroraboot genkey` and your own PK/KEK/db | Moot today: lockdown is compiled in but forced to `none`, and nothing puts `lockdown=` on the command line, so unsigned modules load. The module signing key is ephemeral per build, as on Talos |

Four observations the table makes visible.

**Only Fedora CoreOS requires nothing of the operator.** It is also the only one that has been
through shim-review recently — Fedora's shim 16.1 submissions were accepted on 2026-05-27
(`rhboot/shim-review` #556 x64, #557 aa64). Every other project with a signed chain has made a
key-ownership decision that lands a per-machine enrolment step on somebody's desk.

**"Self-signed" covers three different things, not one.** Bottlerocket and Talos ship a signed
chain under their own key and document how to enrol it; the operator's work is a known, finite
step. Flatcar ships the same thing and does not document it — the artifacts are signed, the
docs never say so, and the only Secure Boot mention in its deploy pages tells you to turn it
off. Kairos ships no signature at all; there is nothing to enrol. The three are not
interchangeable, and one checkbox covers all of them.

**Whoever holds the key owns revocation.** Fedora inherits Microsoft's dbx and SBAT
revocation. Everyone else has to build that themselves, which is the cost a Kairos maintainer
named explicitly when the project declined to hold a key (see §6 of the deep-dive).

**Lockdown under Secure Boot is not automatic, and three of the five learned that the hard
way.** `CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT` is a distribution patch, not mainline, so a kernel
without it boots with lockdown at `none` even with Secure Boot on. Fedora and Flatcar carry it
(Flatcar since 2024-09-17). Talos assumed the kernel did it unconditionally, shipped v1.14.0
without it, and had a maintainer confirm the regression within a day. Bottlerocket sidesteps the
question by setting lockdown from its settings API instead. Hadron has neither the patch, the
config, nor a `lockdown=` command line — which is harmless while nothing is signed, and would be
exactly Talos's v1.14.0 bug the moment anything is.

---

## Per-project findings

### Fedora CoreOS

**Key holder.** FCOS holds no Secure Boot key of its own. Its package lockfile pins unmodified
Fedora RPMs — `shim-x64 16.1-5`, `grub2-efi-x64 1:2.12-64.fc44`, `kernel 7.2.5-200.fc44` — so
the keys are Fedora's and Red Hat's. The vendor certificate embedded in the shim, which is what
validates GRUB and the kernel, is `fedora-ca-20200709.cer`.
Sources: <https://github.com/coreos/fedora-coreos-config/blob/testing-devel/manifest-lock.x86_64.json>;
`rhboot/shim-review` [#556](https://github.com/rhboot/shim-review/issues/556), whose README
states "vendor_cert contains fedora-ca-20200709.cer".
Evidence: **DOCUMENTED**. Private-key custody (HSM, who may invoke it) is **UNKNOWN** — no
primary source states it.

**CA-signed?** Yes, Microsoft third-party UEFI CA. Fedora's shim 16.1 review issues were
accepted on 2026-05-27 (#556 x64, #557 aa64); acceptance is the gate for Microsoft signing. The
shim-review template notes that since 2025-10-20 submitted shims come back signed with both the
2011 and 2023 Microsoft keys. Evidence: **DOCUMENTED**.

**Enrolment.** None. The clearest proof is in FCOS's own Hyper-V documentation, because Hyper-V
Gen 2 defaults to a template that excludes the third-party CA:

> If you configure a Generation 2 virtual machine, Fedora CoreOS will not successfully boot
> until you change the Secure Boot template to *Microsoft UEFI Certificate Authority*.

Source: <https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/provisioning-hyperv.adoc>.
Evidence: **DOCUMENTED** for the requirement, **INFERRED** (high confidence) that bare metal
needs nothing — there is no enrolment procedure documented anywhere because there is no
certificate to enrol. Azure, GCP, Oracle Cloud and VMware are documented as working with Secure
Boot on. One documented exception: **official AWS AMIs do not have Secure Boot enabled** — the
registration path sets `BootMode` but never passes `UefiData`
(<https://github.com/coreos/coreos-assembler/blob/main/mantle/platform/api/aws/images.go>).
Evidence: **DOCUMENTED** for the absent field, **INFERRED** for the consequence.

**Out-of-tree modules.** Lockdown runs in `integrity` mode whenever Secure Boot is on, driven
by the kernel's own Secure Boot detection rather than a settable knob, and FCOS tests this in
CI — the kola test asserts `"none [integrity] confidentiality"` and fails with "lockdown LSM
not set to integrity on a Secure Boot system"
(<https://github.com/coreos/fedora-coreos-config/blob/testing-devel/tests/kola/security/lockdown>).
Fedora signs its own modules with an ephemeral per-build key (shim-review README: "Do you use
an ephemeral key for signing kernel modules? … Yes."), so an operator layering an out-of-tree
module must generate a key and enrol it as a MOK. `mokutil` ships in the base image;
`pesign`/`sbsigntools` do not. Evidence: **DOCUMENTED**.

The project does not document any of this. There is no kernel-modules page; the sanctioned
`rpm-ostree install` extensions page says nothing about Secure Boot or module signing, and
tracker issue #249 ("How to support installing kernel modules") has been open since 2019. The
nearest thing to an official statement is the CoreOS team's NVIDIA image experiment, whose
README says plainly:

> this introduces the downside of breaking Secure Boot as the kmods are not signed by the
> Fedora's key but a self-signed one, which is ok for a POC. For permanent deployment, we'd need
> to maintain a custom signing key, which adds the extra step of enrolling it with MOK to regain
> secure booting functionality.

Source: <https://github.com/coreos/fedora-bootc-nvidia/blob/main/README.md>. Evidence:
**DOCUMENTED** (maintainer statement in a project-adjacent repo). Whether any officially
supported path for signed out-of-tree modules exists: **UNKNOWN**.

**Bootloader updates.** Automatic by default since stable stream 43.20251024.3.0, via
`bootloader-update.service` running `bootupctl update`. This matters here: it is the only
project of the five where shim and GRUB do not drift behind the OS.
Sources: <https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/bootloader-updates.adoc>;
tracker [#1468](https://github.com/coreos/fedora-coreos-tracker/issues/1468) (closed 2025-08-25).
Evidence: **DOCUMENTED**. Note that bootupd's own README still says the opposite ("disabled by
default for e.g. Fedora CoreOS") and is out of date.

Open and unresolved: regular dbx updates
([tracker #1478](https://github.com/coreos/fedora-coreos-tracker/issues/1478), open since 2023).

### Bottlerocket

**Key holder.** The project. The build defines an "sbkeys profile" with four CAs (PK, KEK, db,
vendor) and three signing keys (shim-sign, code-sign, config-sign). shim is signed by the db
cert; GRUB and the kernel by the vendor cert embedded in shim; `grub.cfg` by a GPG key baked
into the GRUB binary. Two profile generators ship — a local one using openssl/gpg, and an
AWS one using AWS Private CA plus KMS asymmetric keys. Of the local one the README says it is
"**strongly discouraged** for any kind of production use."
Source: <https://github.com/bottlerocket-os/bottlerocket/blob/develop/sbkeys/README.md>.
Evidence: **DOCUMENTED**. Which profile AWS uses for official AMIs, and who may invoke those
keys, is stated nowhere: **UNKNOWN**.

**CA-signed?** No, and this is the clearest statement of intent any of the five projects
publishes:

> Many operating systems use a version of shim signed by the Microsoft 3rd Party UEFI CA
> certificate. Bottlerocket does not use this certificate. Instead, Bottlerocket uses a
> self-signed certificate intended to allow you to focus your machine's trust only to your
> specified OS (in this case, Bottlerocket).

It then quotes Microsoft's own argument for why: trusting the third-party CA means trusting
every Linux distribution's bootloader, not just the one you chose.
Source: <https://bottlerocket.dev/en/os/1.64.x/concepts/chain-of-trust/>. Evidence:
**DOCUMENTED**. Corroborating: no Bottlerocket submission exists in `rhboot/shim-review`
(search returns zero) — **DOCUMENTED** for the search result, **INFERRED** for "never
submitted". Secure Boot has been on by default since v1.15.0 "where supported by firmware".

**Enrolment.** On bare metal, yes — a manual certificate import through the firmware setup
menu. Verbatim from `PROVISIONING-METAL.md`:

> Although Bottlerocket also uses `shim`, its copy is not signed by Microsoft and will not be
> trusted without additional configuration. After installing Bottlerocket, the appropriate
> vendor certificate can be found on the EFI System Partition (ESP). The firmware setup menu
> should provide an option to import a new vendor certificate by selecting a file on the ESP.

The chain-of-trust page restates it as a hard requirement: "The machine's NVRAM must contain
Bottlerocket's 'db' certificate". On AWS and VMware the platform pre-enrols it at AMI/OVA
registration, so cloud operators never see this. Xen-based EC2 instance types (generation 4 and
below) boot legacy BIOS and cannot use Secure Boot at all.
Sources: <https://github.com/bottlerocket-os/bottlerocket/blob/develop/PROVISIONING-METAL.md>;
<https://bottlerocket.dev/en/os/1.64.x/concepts/chain-of-trust/>. Evidence: **DOCUMENTED**.

This is the trade the ticket points at, stated plainly by the project itself: a smaller trusted
set, paid for with a per-machine manual step on metal — and on firmware that cannot enrol
custom keys, paid for by not booting at all.

**Out-of-tree modules.** The most interesting answer of the five, because Bottlerocket resolves
the conflict by giving up the module half rather than the boot half:

> Bottlerocket enables Lockdown in "integrity" mode by default on most variants. … Certain
> variants such as `*-nvidia` need to load unsigned kernel modules at runtime. This is
> prohibited by the "integrity" mode, but required for the hardware to work as expected. On
> these variants, Lockdown is set to "none" instead.

Those NVIDIA variants still set `uefi-secure-boot = true`, so the chain through the kernel is
verified and then the kernel accepts unsigned modules. The settings reference confirms the
default is "integrity except for nvidia and dev variant flavours which use none". Lockdown is
applied at boot from the settings API rather than derived from Secure Boot state, so an
operator with API access can lower it to `none` and reboot with Secure Boot still on — a
structural difference from Fedora CoreOS, where lockdown follows Secure Boot and cannot be
lowered. No operator-facing module-signing key or MOK workflow is documented; the supported
path for custom keys is to rebuild the OS with your own sbkeys profile.
Sources: <https://github.com/bottlerocket-os/bottlerocket/blob/develop/SECURITY_FEATURES.md>;
<https://bottlerocket.dev/en/os/1.64.x/api/settings/kernel/>;
<https://github.com/bottlerocket-os/bottlerocket/blob/develop/sbkeys/README.md>.
Evidence: **DOCUMENTED**.

Also worth recording, because it bears directly on key rotation: Bottlerocket's A/B update
payload carries exactly three images (`boot`, `root`, `hash`) and the partition set it flips
contains no ESP, so shim and the GRUB binary are fixed for the life of a node's disk. New
bootloaders arrive by replacing the node.
Sources: `sources/updater/update_metadata/src/lib.rs`, `sources/updater/signpost/src/set.rs` in
<https://github.com/bottlerocket-os/bottlerocket-core-kit>. Evidence: **INFERRED** from the
code — no primary source states it in prose.

### Flatcar

**Key holder.** The project. The build script switches keys on whether the build is official:
unofficial builds use a test key baked into the SDK filesystem, official releases pull the key
from an Azure Key Vault HSM.

```sh
if [[ ${COREOS_OFFICIAL:-0} -ne 1 ]]; then
    SBSIGN_KEY="${SBSIGN_KEY:-/usr/share/sb_keys/shim.key}"
else
    SBSIGN_KEY="pkcs11:token=flatcar-secure-boot-prod-2026-04"
fi
PKCS11_MODULE_PATH="/usr/$(get_sdk_libdir)/pkcs11/azure-keyvault-pkcs11.so"
```

Source: `flatcar/scripts` `build_library/sbsign_util.sh`. The PR that introduced the split
(`flatcar/scripts` #3954, merged 2026-04-22) says it directly: the release keys are "pulled
from an Azure KMS and intended for release builds."
Evidence: **DOCUMENTED**. This is the most specific key-custody statement any of the five
projects publishes — Fedora's and Bottlerocket's custody arrangements are both UNKNOWN.

Verified against the shipped stable artifact (4757.2.0): `flatcar_production_image.shim`,
`flatcar_production_pxe_grub.efi` and `flatcar_production_image.vmlinuz` all carry an
Authenticode signature from `CN=Flatcar Container Linux Secure Boot Development Signing`,
issued by `CN=Flatcar Container Linux Secure Boot Development CA`, and the shim's embedded
`.vendor_cert` is that same self-signed CA. Its `.sbat` carries a vendor line,
`shim.flatcar,1,Flatcar Container Linux,shim,15.8-r3,security@flatcar-linux.org` — the line
Hadron's shim does not have. Evidence: **REPRODUCED** (artifact downloaded and parsed).

**CA-signed?** No. Most recent maintainer statement, chewi on 2026-07-10, in `flatcar/scripts`
PR #4140 ("Update our temporary Secure Boot CA certificate"):

> As a reminder, this is what we're using for official releases until we get a formally signed
> certificate from Microsoft.

The ticket's framing — "a maintainer stated in June 2025 that shim-review was blocked" — is
correct, and the position has been restated more recently than the ticket knew. The full
sequence, all from primary sources:

| date | statement |
|---|---|
| 2021-09-08 | `flatcar/Flatcar` [#501](https://github.com/flatcar/Flatcar/issues/501) opened |
| 2023-06-09 | jepio: "Correct, secure Boot is not supported (our EFI binaries are not signed)." |
| 2024-11-11 | jepio: "we're going to be submitting the shim … in the coming weeks" |
| 2025-01-20 | sayanchowdhury: "We are working on the shim-review questionare and getting answers for some of the questions is taking time." |
| 2025-06-23 | jepio: shim "is not signed by the official 3rdparty UEFI CA (our shim-review submission is blocked on a legal/procedural issue)" |
| 2025-06-23 | chewi: "Or they could just add our DB certificate in the short term, if that's acceptable." — the last comment on #501 |
| 2026-07-10 | chewi, in PR #4140: "temporary … until we get a formally signed certificate from Microsoft" |

Evidence: **DOCUMENTED** (all quotes read via `gh` from the issue and PR threads).

No submission exists. `rhboot/shim-review` full-text search for "flatcar" returns
`total_count: 0`. Flatcar maintains a fork, `flatcar/shim-review`, which has five pull requests
— none of them a submission, its README unmodified from the upstream template, and zero
releases, although `sys-boot/shim/README.md` says a release there is what the build consumes
once a signed shim arrives. The tracking issue `flatcar/Flatcar` #630 still carries
`- [ ] submit signed shim for review` unchecked. Evidence: **DOCUMENTED** for each of those
facts; **INFERRED** for "never submitted".

Recorded fairly: the blocker is stated as legal or procedural, not technical, and the project
does not control how long that takes. The finding here is about what an operator can do today,
not about the project's diligence — and the project has shipped a real signed chain in the
meantime, which is more than the ticket's summary implied.

**Enrolment.** Required. Two documented paths, both firmware work. Enrol Flatcar's DB
certificate alongside Microsoft's — PR #4140 gives the exact `virt-fw-vars --add-db` command
and `build_library/flatcar-sb-dev-ca.pem` is published in-repo. Or enrol your own PK/KEK/db and
re-sign Flatcar's `bootx64.efi` with your DB key, which is jepio's advice in #501. MokManager
ships on the ESP but does not help: MOK only extends trust after the shim is itself trusted by
db, and this shim is not. Evidence: **DOCUMENTED** for both paths; **INFERRED** for the MOK
point.

Which channels ship signed artifacts, corrected against the ticket's premise: **alpha since
4284.0.0 (2025-03-25), beta since 4344.1.0 (2025-06-24), stable since 4459.2.0 (2025-11-12).
LTS is not signed** — `flatcar_production_image.shim` on LTS 4081.3.10 has an empty PE security
directory. Evidence: **REPRODUCED** for LTS, **DOCUMENTED** for the three dated channel
rollouts.

There is still **no Secure Boot page anywhere in the Flatcar documentation**. A repo-wide search
of `flatcar/flatcar-website` `content/docs` for "Secure Boot" returns three files: the Hyper-V
page, which tells you to *disable* it ("Hyper-V Generation 2 virtual machines need to have
secure boot disabled, as the VHDX images are not signed" — stale relative to the signing work),
the NVIDIA page, and the supply-chain page. Neither of the latter two documents enrolment.
Evidence: **DOCUMENTED**. Cloud behaviour on AWS, Azure and GCP is **UNKNOWN** — the deploy
pages mention Secure Boot, Trusted Launch and Shielded VM zero times.

This is the sharpest documentation gap of the five, and it is a different shape from the Kairos
one: Flatcar's docs understate what the project ships, Kairos's overstate it.

**Out-of-tree modules.** The best story of the five. Flatcar carries the Debian lockdown patch
and enables it:

```
CONFIG_SECURITY_LOCKDOWN_LSM=y
CONFIG_SECURITY_LOCKDOWN_LSM_EARLY=y
CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT=y
CONFIG_MODULE_SIG=y
CONFIG_MODULE_SIG_KEY="${MODULE_SIGNING_KEY_DIR}/certs/modules.pem"
```

so the kernel enters integrity lockdown automatically when Secure Boot is detected — the exact
mechanism Hadron's configs lack. `CONFIG_MODULE_SIG_FORCE` is not set, so with Secure Boot off
unsigned modules still load. The design rationale is written down in `flatcar/scripts` #2299
(merged 2024-09-17): "The alternative is to either always force lockdown (bad - no unsigned
kernel modules) or do so through a kernel cmdline parameter in grub (frowned upon and harder to
fix later)."

The module signing key is ephemeral, and the project engineered around that rather than
shipping unsigned drivers. `flatcar/scripts` #2636 (merged 2025-04-30):

> For out of tree modules (like ZFS or NVIDIA) to work with secureboot, they need to be signed
> by the ephemeral kernel modules key. This key is shredded after the upstream-included kernel
> modules are built, therefore it can't be reused during ZFS module build. This PR moves the
> key to /tmp, so that it stays in RAM and can be reused by out of tree modules.

NVIDIA and ZFS therefore ship as pre-signed sysexts built with every release, and the NVIDIA
page states the consequence plainly: "When using secure boot, only the prebuilt sysext will
work, as the modules are signed." The legacy compile-on-first-boot path cannot work under
Secure Boot. Evidence: **DOCUMENTED**.

Whether a third party can sign their own module for a stock release: **INFERRED no** (the key
is shredded per build and `CONFIG_SECONDARY_TRUSTED_KEYRING` is not set), **UNKNOWN** whether
a path is planned.

### Talos

**Key holder.** Sidero Labs, for the official assets: "Sidero Labs provides Talos images signed
with the Sidero Labs SecureBoot key via Image Factory." The signing certificate is served
publicly at <https://factory.talos.dev/secureboot/signing-cert.pem>; its subject equals its
issuer (`C=US, O=Sidero Labs Inc., OU=Sidero Labs SecureBoot, CN=talos.dev`, valid 2023-11-21
to 2033-11-18), so it is a self-signed root with no chain to any external CA.
Evidence: **DOCUMENTED** for the statement, **REPRODUCED** for the certificate.

Two keys are involved and the docs separate them: "SecureBoot key is used to sign the boot
assets and it is enrolled into the UEFI firmware. PCR Signing Key is used to sign the TPM
policy, which is used to seal the disk encryption key." Operators can substitute their own with
`talosctl gen secureboot`, or bring an existing PKI. A self-hosted Image Factory supports file,
Azure Key Vault and AWS KMS signing backends (`IF_SECUREBOOT_*` in
`siderolabs/image-factory` `docs/configuration.md`); PKCS#11 is not supported, and a request
for Vault/OpenBao (`siderolabs/talos` #12970, 2026-03-16) is open. How Sidero custodies the
public factory's own key is **UNKNOWN**. Evidence: **DOCUMENTED** for the rest.

**CA-signed?** The question does not apply, and why is architecturally interesting. There is no
shim. systemd-boot loads a UKI containing kernel, initramfs and command line, signed as one
object; "Both `systemd-boot` and Talos `UKI` image are signed with the key, which is enrolled
into the UEFI firmware." The UEFI signature therefore covers the whole OS rather than a
first-stage loader — which is why Talos needs no shim, and also why it cannot inherit a
CA-signed one. No shim-review submission exists because there is nothing to submit.
Evidence: **DOCUMENTED**. That Sidero's key is absent from stock firmware is **INFERRED** (from
the self-signed root plus the mandatory enrolment workflow); no source states it outright.

One thing here is easy to misread and worth stating precisely. Talos embeds Microsoft's KEK and
db certificates (`MicCorKEKCA2011`, `microsoft uefi ca 2023`, `microsoft option rom uefi ca
2023` and others) in `internal/pkg/secureboot/database/database.go`, appended when
`IncludeWellKnownCertificates(true)`. Those are Microsoft certificates going *into the database
Talos asks you to enrol*, so Option ROMs still verify after enrolment. They are emphatically
not a Microsoft signature on anything of Talos's. Evidence: **DOCUMENTED**.

**Enrolment.** Required, and more automated than Bottlerocket's — but not, as the documentation's
"getting started" framing suggests, automatic on bare metal. The `loader.conf` default is
`secure-boot-enroll: if-safe`, which auto-enrols only under virtualization. On a physical
machine the operator enrols from the systemd-boot menu ("Enroll Secure Boot keys: auto"), or
builds an image with `enrollKeys: force` via the Image Factory schematic
(`customization.secureboot.enrollKeys`). The Image Factory also returns the PEM certificate for
manual enrolment. Two ISO flavours ship: `metal-<arch>.iso` for BIOS and UEFI, and
`metal-<arch>-secureboot.iso` for UEFI SecureBoot only. SecureBoot images exist from v1.5.0.
Sources: <https://docs.siderolabs.com/talos/v1.14/platform-specific-installations/bare-metal-platforms/secureboot>;
`siderolabs/talos` `pkg/imager/profile/output.go`. Evidence: **DOCUMENTED**.

The trade is worth naming: setup mode means the machine leaves factory-Microsoft trust rather
than adding Sidero alongside it, which is why Talos re-adds Microsoft's certificates to the
database it enrols. **INFERRED** from setup-mode semantics; the documentation does not spell it
out.

Which platforms have a Secure Boot path at all is answerable from the code. The imager's Secure
Boot profiles are exactly `secureboot-iso`, `-metal`, `-metal-uki`, `-installer`, `-azure`,
`-cloudstack`, `-nocloud`, `-opennebula`, `-openstack` and `-vmware`. **There is no
`secureboot-aws` and no `secureboot-gcp`.** Source: `pkg/imager/profile/default.go`. Evidence:
**DOCUMENTED**. What enrolment Azure Trusted Launch actually requires is **UNKNOWN** — Talos's
documentation mentions Trusted Launch and Shielded VM zero times.

**Out-of-tree modules.** Two mechanisms, and they are independent — which is the detail that
makes Talos's answer different from everyone else's.

Module signature enforcement does not depend on lockdown. Since v1.12.0, every Talos image
carries `module.sig_enforce=1` on the kernel command line
(`pkg/machinery/kernel/kernel.go`), Secure Boot or not. It can be set to `0` through the Image
Factory or the imager. Evidence: **DOCUMENTED**.

Lockdown has had a bumpy recent history, and the v1.14 release note the Pulse profile and my
own first pass both relied on was wrong on release:

| version | lockdown under Secure Boot |
|---|---|
| before v1.14.0 | `confidentiality`, set explicitly on the command line |
| **v1.14.0** (2026-09-03) | **`none` — a regression** |
| v1.14.1 (2026-09-15) onward | `integrity`, via an out-of-tree kernel patch |

v1.14.0 dropped the explicit `lockdown=confidentiality` flag on the assumption the kernel would
enter integrity by itself under Secure Boot. It does not. `siderolabs/talos`
[#14237](https://github.com/siderolabs/talos/issues/14237) (opened 2026-09-03, closed
2026-09-04) reports `/sys/kernel/security/lockdown` reading `[none] integrity confidentiality`
on a Secure Boot metal UKI node; smira confirmed the same day: "I can confirm this, the Linux
kernel was supposed to do this unconditionally on SecureBoot." The fix, PR #14241 (merged
2026-09-04), pulls in `siderolabs/pkgs` commit `43e6298f`, whose message names the root cause:

> For 1.14.0, we dropped the lockdown=confidentialy flag from the Linux kernel cmdline to unify
> installers. The idea was that the Linux should enter integrity on SecureBoot, but it turns out
> that it's an out-of-tree patch, so bring it in here.

Evidence: **DOCUMENTED**.

That detail matters beyond Talos, because it is the same trap Hadron is sitting in.
`CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT` is not mainline; it is a distribution patch. Talos set it
on 2026-09-04. Flatcar has carried the equivalent Debian patch since 2024-09-17. Hadron has
neither the patch nor the config, and nothing on its command line — so if Hadron's boot chain
were signed tomorrow, it would land exactly where Talos v1.14.0 did.

**Can an operator sign their own module?** No, and this is a documented product decision rather
than an accident. `siderolabs/talos`
[#11675](https://github.com/siderolabs/talos/issues/11675) ("add support for custom
user-provided module signing keys", opened 2025-08-26) was closed as completed on 2025-10-08 by
rejecting the design. frezbo:

> After doing some research this needs a lot of work to even get it working. […] After internal
> discussion the idea is to not set `CONFIG_MODULE_SIG_FORCE` and have `module.sig_enforce` set
> in talos images, providing the user to a way to disable signature verification for user
> brought modules

Evidence: **DOCUMENTED**. The escape hatch Sidero chose is "turn enforcement off", not "enrol
your key" — and that hatch is closed once lockdown is at integrity, so on a Secure Boot image
the sanctioned path for a self-built module is mutually exclusive with Secure Boot.
**INFERRED** for that last consequence; Talos does not state it.

Supporting configuration, all **DOCUMENTED**: the module signing key generation config in
`siderolabs/pkgs` literally names itself `CN = Build time throw-away kernel key`; no
`signing_key.pem` is committed anywhere in the repository; `CONFIG_SECONDARY_TRUSTED_KEYRING`
is not set, so there is no runtime keyring to extend. The documentation states the operator-
facing consequence directly: "The signing key is generated during the build process, it is
unique to each build, and it is not available to the user."

Sidero solves the driver half the way Flatcar does: NVIDIA and ZFS are built inside
`siderolabs/pkgs` against the kernel source tree, so they pick up the throw-away key, and each
build asserts that every `.ko` carries a signature. Evidence: **DOCUMENTED**.

This is the steepest customization cost of the five and the project states it plainly rather
than hiding it. Structurally it is the same constraint Hadron has — an ephemeral per-build
module key — with the difference that Talos writes it down and enforces it, while on Hadron it
is currently invisible because lockdown is off.

---

## The Kairos deep-dive

The ticket asks five things. Taken in order.

### 1. What the architecture page actually claims

`docs/architecture/secureboot.md` in `kairos-io/kairos-docs`, frontmatter `date: 2024-01-29`,
published live at <https://kairos.io/docs/architecture/secureboot/>. Verbatim, in full — it is
short:

> ## SecureBoot support implementation
>
> Currently Kairos supports SecureBoot based on the upstream artifacts.
> We piggyback on the upstream artifacts to be properly signed in order to support SecureBoot.
>
> Before this was supported, we shipped a single set of artifacts that were signed by one of
> the upstream distros. That meant that only that distro was supported under SecureBoot as we
> needed all artifacts in the chain to be signed with the same key. So that meant that
> secureboot was only supported on the same distro that we obtained the artifacts from.
>
>  - Shim (signed by X) -> grub (signed by X) -> kernel (signed by X) = SecureBoot
>  - Shim (signed by X) -> grub (signed by X) -> **kernel (signed by Y)** = No SecureBoot
>
> Now, instead of using a single set of artifacts, we use the upstream artifacts directly, so
> we can support SecureBoot on all the distros that support it directly with the upstream
> signatures. [...]
>
> Any of the current supported flavors in Kairos can be used with SecureBoot out of the box in
> UEFI mode.
>
> Currently Alpine is not supported as it does not provide signed artifacts by default and
> relies in users generating their own keys to sign those.
>
> #### Artifacts used on each distro
>
>  - shim
>  - grub
>  - kernel

Evidence: **DOCUMENTED**. Sources: `kairos-io/kairos-docs` `origin/main:docs/architecture/secureboot.md`;
live page <https://kairos.io/docs/architecture/secureboot/> (fetched 2026-09-16, text matches).

Two things about the date. The frontmatter says 2024-01-29. The rendered page says "last
updated February 24, 2026" — but the only commit touching the file on `origin/main` is
`19289fe` (2026-02-24, "Migration cleanup (#553)"), a docs-platform migration. The *content*
is unchanged from January 2024. The ticket's "dated January 2024" reading is correct, and the
2026 timestamp the site displays is misleading rather than evidence of review.
Evidence: **DOCUMENTED** (git log), **INFERRED** for "content unchanged" — history before the
migration is not in this repo's `main`, so I can only say no content commit exists after it.

The v4.3.0 versioned snapshot (`versioned_docs/version-v4.3.0/architecture/secureboot.md`) is
byte-identical to the current page. The claim ships with the current release.
Evidence: **REPRODUCED** (`diff` of the two blobs, empty).

Note also `docs/architecture/meta.md`, which lists a category "Secure Boot Only Images" whose
requirement is "Use `grub` as bootloader" — so the GRUB path is presented as the Secure Boot
path, distinct from Trusted Boot. Evidence: **DOCUMENTED**.

The claim is never qualified for Hadron anywhere. Of the 18 pages under `docs/` that mention
Hadron, exactly one also mentions Secure Boot — `docs/installation/trustedboot.mdx`, the
bring-your-own-keys page. The architecture page that makes the out-of-the-box claim does not
mention Hadron at all, and `docs/reference/image_matrix.md` states that the project now
"focus[es] official prebuilt artifacts and docs defaults on Hadron". Evidence: **DOCUMENTED**
(grep over `kairos-io/kairos-docs` `origin/main:docs/`).

### 2. The piggyback mechanism is real — for bases Kairos no longer ships

The claim is not vapour. `kairos-init` installs the upstream distro's signed packages by base:
`shim-signed` and `grub-efi-amd64-signed` / `grub-efi-arm64-signed` for Debian/Ubuntu,
`shim-x64` / `shim-aa64` for Fedora, `shim` for openSUSE, each annotated "For secure boot
support" in the source.
Source: `kairos-io/kairos` `origin/master:kairos-init/pkg/values/packagemaps.go:168, 770-855`.
Evidence: **DOCUMENTED**.

The agent then copies those binaries from the rootfs onto the ESP rather than shipping a
generic set, and the reason is written out in the code:

> The shim contains the signature from microsoft and the shim provider (i.e. upstream distro
> like fedora, suse, etc). So if we use the shim+grub from a generic package (i.e. ubuntu) it
> WILL boot with secureboot but when loading the kernel it will fail because the kernel is not
> signed by the shim provider or grub provider [...] This is why if we want to support
> secureboot we need to copy the shim+grub from the rootfs default paths instead of providing
> a generic package

Source: `kairos-io/kairos` `origin/master:agent/pkg/utils/grub.go:273-281` (`RefreshESP`).
Evidence: **DOCUMENTED**.

A maintainer closed kairos#2194 ("Secure boot not working on custom ISO created by Auroraboot")
with "we tested secureboot with debian and it worked."
Source: <https://github.com/kairos-io/kairos/issues/2194>. Evidence: **DOCUMENTED**.

So for a Kairos image *you build yourself* on Ubuntu, Debian, Fedora or openSUSE, the
piggyback story holds and the architecture page is accurate. The problem is what happens when
that assumption meets the one base that has no upstream to piggyback on.

### 3. Hadron compiles its own shim, and nothing signs it

Hadron is a from-scratch distribution. It downloads the upstream `rhboot/shim` 16.1 release
tarball and builds it:

- `origin/main:sources.yaml:879-885` — `shim: version "16.1"`, from
  `https://github.com/rhboot/shim/releases/download/${version}/shim-${version}.tar.bz2`.
- `origin/main:Dockerfile.tmpl:2967-2998` — `FROM rsync AS shim`, untar, apply
  `patches/0001-shim-gnu-efi-grouped-target.patch`, then
  `make EFIDIR=hadron ARCH=${BUILD_ARCH} DESTDIR=/tmp/shim install`, then copy
  `BOOTX64.EFI` to `/shim/usr/share/efi/x86_64/shim.efi`.
- `origin/main:Dockerfile.tmpl:4052` — `COPY --from=shim /shim/ /skeleton/`, so it lands in
  the published image.

Evidence: **DOCUMENTED**.

Three things are absent from that build, and each matters:

- **No signing step.** `git grep -i "sbsign\|pesign\|sbverify"` over the whole of
  `kairos-io/hadron` `origin/main` returns nothing. Evidence: **DOCUMENTED** (empty grep over
  a primary source).
- **No `VENDOR_CERT_FILE`.** The `make` invocation passes only `EFIDIR`, `ARCH` and `DESTDIR`.
  A shim built without a vendor certificate embeds no trust anchor of its own, so even if it
  were signed it could not validate the GRUB behind it except through MOK. Evidence:
  **DOCUMENTED** for the absent flag; **INFERRED** for the consequence (that is standard shim
  behaviour, not something Hadron documents).
- **No shim-review submission.** A full-text search of `rhboot/shim-review` for "kairos" and
  for "hadron" returns `total_count: 0` for each, across issues and pull requests.
  Evidence: **DOCUMENTED** for the search result; **INFERRED** for "no submission has ever been
  made" — a search can miss a submission filed under another name.

The only signing anywhere in the Hadron build is the Trusted Boot (UKI) path, and it signs
with keys the caller supplies. `make trusted-iso` passes `--sb-key /keys/db.key --sb-cert
/keys/db.pem` from `KEYS_DIR`, and the Makefile help says of the default: "the keys that we use
for testing, which are INSECURE and should not be used in production."
Source: `kairos-io/hadron` `origin/main:Makefile:138-145, 234-249`. Evidence: **DOCUMENTED**.

`make grub-iso` — the target that produces the released ISO shape — passes no keys at all:
`auroraboot build-iso --output /output/ docker:${INIT_IMAGE_NAME}`.
Source: `origin/main:Makefile:228-231`. Evidence: **DOCUMENTED**.

And AuroraBoot's ISO builder copies whatever shim it finds in the rootfs onto the ESP, with no
signing anywhere in the path.
Source: `kairos-io/AuroraBoot` `origin/main:pkg/ops/iso.go:620-676` (`copyShim`). Evidence:
**DOCUMENTED**.

Hadron's own Secure Boot test does not cover this. `tests/tests_suite_test.go:322-328` boots
QEMU with `assets/efivars.fd`, and `assets/efivars.md` explains that file "enables SecureBoot
with the default keys and also bundles the certs for our testing [...] what our test UKI EFI
files are signed for". It is a UKI-path test with Hadron's own test certificate pre-enrolled.
There is no test of the GRUB shim path under stock firmware keys.
Evidence: **DOCUMENTED**.

### 4. Verifying it on the published artifact

Source-reading establishes that no signing step exists. To close the gap between "no signing
step in the source" and "the shipped binary is unsigned", I checked the artifact.

Procedure (reproducible, ~154 MB of network):

1. Fetch an anonymous pull token for `ghcr.io/kairos-io/hadron` and read the OCI index at tag
   `main`. It carries `org.opencontainers.image.revision: 4ffdf3cf6866cd0e810b964d82263b91b406d9fc`
   and `org.opencontainers.image.created: 2026-09-15T16:27:16.743Z` — matching HEAD of
   `kairos-io/hadron` `origin/main` at the time of this research.
2. Resolve the `linux/amd64` manifest
   (`sha256:c03e2e05459c8c926817e81710301e2df4a87c60c430f3504a2637e539a193f2`). It has a single
   layer, `sha256:0aa70c5e…`, 154.2 MB.
3. Pull that layer, extract `usr/share/efi/x86_64/shim.efi`,
   `usr/lib/grub/x86_64-efi/grubx64.efi`, `usr/lib/systemd/boot/efi/systemd-bootx64.efi` and
   `boot/vmlinuz-7.1.8-hadron`.
4. For each, parse the PE optional header and read data directory index 4 — the Authenticode
   certificate table. An Authenticode-signed PE has a non-zero offset and size here.

Result: every one of the four reports `cert_offset=0 cert_size=0`. All are PE32+
(`magic=0x20b`), so the parse is valid; the certificate table is simply empty.

Evidence: **REPRODUCED**.

Two further details from the same extraction, both of which corroborate rather than merely
repeat the above:

- **The shim's `.sbat` section is stock upstream.** Its full contents are:

  ```
  sbat,1,SBAT Version,sbat,1,https://github.com/rhboot/shim/blob/main/SBAT.md
  shim,4,UEFI shim,shim,1,https://github.com/rhboot/shim
  ```

  Every CA-signed distribution shim carries an additional vendor line — `shim.fedora`,
  `shim.suse`, `shim.ubuntu` and so on — because SBAT revocation is per-vendor and shim-review
  requires it. There is no `shim.hadron` or `shim.kairos` line. Evidence: **REPRODUCED** for
  the section contents; **DOCUMENTED** for the shim-review requirement (rhboot/shim SBAT.md,
  linked from the section itself); **INFERRED** for the conclusion that this shim was never
  prepared for review.
- **There is no `.vendor_cert` section at all.** The section list is `/4`, `.text`, `.reloc`,
  `/14`, `/26`, `.data`, `/37`, `.dynamic`, `.rela`, `.sbat`. Evidence: **REPRODUCED**.

Note the scope limit honestly: I verified the OCI image, not the `.iso` release asset. The ISO
is built from this image by `auroraboot build-iso`, and `copyShim` copies the file rather than
transforming it, so the ISO's ESP carries the same bytes. That last step is **INFERRED**, not
reproduced — I did not download the 2+ GB ISO. If Mauro wants it airtight, mounting
`kairos-hadron-v0.5.1-core-amd64-generic-v4.3.0.iso` and running the same PE check on
`EFI/BOOT/BOOTX64.EFI` would settle it in one command.

### 5. So: does an official Kairos ISO boot with Secure Boot on?

**No, on stock firmware — and there is no key regime under which it does without operator
work.** Evidence: **REPRODUCED** for the artifact being unsigned; **INFERRED** for the boot
outcome, because I did not boot it. An unsigned EFI binary is rejected by any conforming
firmware with Secure Boot enabled; that is the specification, not a project-specific claim,
but it is still an inference from the artifact rather than an observation.

The two paths an operator actually has:

- **GRUB path (what ships).** Every v4.3.0 release ISO is `kairos-hadron-…-generic-…iso` —
  57 assets, all Hadron, all the GRUB shape, no UKI ISO among them. Unsigned. Secure Boot must
  be off. Source: `gh release view v4.3.0 --repo kairos-io/kairos`. Evidence: **DOCUMENTED**.
- **Trusted Boot path (build it yourself).** Generate your own keys with `auroraboot genkey`,
  build your own UKI ISO, enrol your own PK/KEK/db into firmware. The documentation is
  explicit and good about this: keys "are generated with the `auroraboot` tool", Microsoft's
  certificates are included by default and skipping them requires a flag literally named
  `--skip-microsoft-certs-I-KNOW-WHAT-IM-DOING`, and for HTTP boot "the machine needs to start
  in 'setup' mode, which means secure boot is disabled and there are no keys enrolled in the
  firmware." Sources: `kairos-io/kairos-docs` `origin/main:docs/installation/trustedboot.mdx:46-103`,
  `origin/main:docs/architecture/trustedboot.md`, `origin/main:docs/reference/auroraboot.md:840-856`.
  Evidence: **DOCUMENTED**.

This is an honest and coherent design — the Trusted Boot position is that the operator holds
the keys to the kingdom, and the documentation says so clearly. The defect is not the design.
The defect is that the architecture page promises a third thing, "SecureBoot out of the box",
that no released artifact delivers.

### 6. Is a Kairos-held signing key being considered?

Yes, and the reasoning against it is on the record. kairos#3489 ("feat: UKI images signed by
kairos", open since 2025-06-24). A maintainer:

> We discussed this already at the start of the Trusted Boot journey and felt like we didnt
> have the medium or the manpower to securely maintain this. [...] the key should be in a
> offline machine/usb and only used for releasing stuff [...] It also means that at least 2
> members of the team should have the key [...] It would also mean that we would need to start
> shipping an official dbx with revocation hashes.

and, in the same comment:

> Otherwise you can just use non Trusted Boot images which have secureboot provided by the
> distros.

That second sentence is the architecture page's claim restated by a maintainer in June 2025 —
and it is exactly the assumption Hadron breaks, since Hadron has no distro to provide it.
Source: <https://github.com/kairos-io/kairos/issues/3489>. Evidence: **DOCUMENTED**.

Nothing in that thread, or anywhere else I found, tracks the GRUB-path shim for Hadron.
`kairos-io/hadron` has issues disabled, so all tracking goes through `kairos-io/kairos`, and a
search of that repo for Secure Boot issues turns up the UKI signing question (#3489), a Hadron
UKI boot stall (#4618), key-management ergonomics (#3242, #2432) — and nothing on this.
Evidence: **DOCUMENTED** for the search results; **INFERRED** for "untracked".

### 7. Out-of-tree modules under lockdown, on Hadron

From `kairos-io/hadron` `origin/main:files/kernel/default.config` and `default-arm64.config`:

```
CONFIG_SECURITY_LOCKDOWN_LSM=y
CONFIG_SECURITY_LOCKDOWN_LSM_EARLY=y
CONFIG_LOCK_DOWN_KERNEL_FORCE_NONE=y
CONFIG_MODULE_SIG=y
# CONFIG_MODULE_SIG_FORCE is not set
CONFIG_MODULE_SIG_ALL=y
CONFIG_MODULE_SIG_KEY="certs/signing_key.pem"
CONFIG_INTEGRITY_PLATFORM_KEYRING=y
CONFIG_LOAD_UEFI_KEYS=y
```

Evidence: **DOCUMENTED**.

Reading that:

- Lockdown is compiled in but **forced to none**. Mainline does not auto-enter lockdown when
  Secure Boot is detected — that behaviour comes from the distribution patch
  `CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT`, which is absent from all six Hadron configs. No
  `lockdown=` appears on any kernel command line in the repo either (`git grep -i lockdown`
  outside `files/kernel/` returns nothing). So unsigned and out-of-tree modules load normally
  today. Evidence: **DOCUMENTED** for the configs and the grep; **INFERRED** for the runtime
  behaviour.
- `MODULE_SIG_KEY` is the kbuild default, and no step in the build supplies or preserves a
  key. The kernel therefore generates an ephemeral signing key per build and discards it — the
  same constraint Talos documents explicitly. `MODULE_SIG_ALL=y` means the in-tree modules
  ship signed by that throwaway key; an operator cannot sign anything with it. Evidence:
  **DOCUMENTED** for the config and the absent build step; **INFERRED** for "ephemeral and
  discarded" (standard kbuild behaviour, undocumented by Hadron).
- **riscv64 has none of it**: `# CONFIG_MODULE_SIG is not set`,
  `# CONFIG_SECURITY_LOCKDOWN_LSM is not set`, `# CONFIG_INTEGRITY_SIGNATURE is not set`. The
  shim build is skipped for riscv64 outright ("Skip shim build for RISC-V as it doesn't have
  Secure Boot support yet", `Dockerfile.tmpl:2989`). That one *is* stated in the source, and
  it is the only place in the Kairos tree where a Secure Boot limitation is written down.
  Evidence: **DOCUMENTED**.

The net effect is benign today and fragile tomorrow: because lockdown is off, nothing is
broken; but if Hadron ever gains a signed boot chain, out-of-tree modules would become a
problem with no operator-usable signing key to solve it, and nothing documents that.
Evidence: **INFERRED**.

---

## What this changes about "supports Secure Boot"

The ticket's premise holds. Five projects would tick the same box and mean five different
things, and the differences are the sort an operator finds out about at 2 a.m. in a datacentre.

The useful decomposition is four independent axes, not one flag:

1. **Is there a signed chain at all?** Four of five: yes. Kairos's released artifact: no.
2. **Is the root of that chain already in stock firmware?** Only Fedora CoreOS. Everyone else
   with a signed chain needs the operator to put a certificate into NVRAM.
3. **Who can revoke it?** CA-signed means Microsoft's dbx reaches you and SBAT revocation
   applies; project-held means the project must build and ship its own revocation story, which
   is exactly the objection a Kairos maintainer raised in kairos#3489 ("we would need to start
   shipping an official dbx with revocation hashes").
4. **Does the signed chain extend past the kernel?** Four different answers. Fedora and Talos
   block unsigned modules outright. Flatcar blocks them and pre-signs the drivers people
   actually need, which is the only answer here that leaves an operator with working GPUs and
   an intact chain. Bottlerocket turns lockdown off on the variants that need modules. Hadron
   does not reach the question, because nothing is signed and lockdown is off.

Axis 2 is the one "supports Secure Boot" hides, and it is a deployment-model question as much
as a security one. On cloud, enrolment is somebody else's job and the distinction nearly
vanishes. On bare metal it is a per-machine manual step, or a firmware-management product, or
it does not happen. That is why Bottlerocket — whose Secure Boot posture is the densest of the
five by default — is also the one with the sharpest bare-metal cost, and why Fedora CoreOS,
which is the least opinionated of the five about Secure Boot, is the easiest to actually turn
on.

Axis 3 is where a project-held key stops being free. The Kairos maintainer thread is the
clearest articulation of this cost written down by anyone in this comparison, and it is worth
quoting in any eventual public write-up regardless of how the Kairos finding resolves: an
offline key, multiple custodians, a manual release step, and a dbx you now own. Flatcar and
Bottlerocket have each paid some version of that bill. Kairos decided not to, which is a
defensible call — the problem is only that the documentation did not follow the decision.

## Unknowns

Recorded as UNKNOWN rather than resolved, per the evidence standard. Missing documentation is
not proof of absence.

- **Kairos**: whether the unsigned Hadron chain is a known gap with an unwritten plan, or an
  unnoticed regression from the distro-piggyback era. No primary source either way. Nothing
  tracks it in `kairos-io/kairos`, and `kairos-io/hadron` has issues disabled.
- **Kairos**: whether the released `.iso` ESP carries the same unsigned binary as the OCI
  image. Inferred from `copyShim` not transforming the file; not verified on the ISO.
- **Kairos**: whether the FIPS variants, which build separately, differ here. Not examined.
- **Flatcar**: what the legal or procedural blocker on shim-review actually is, and whether it
  is still the blocker fifteen months later. Also what happens on AWS, Azure and GCP — the
  deploy pages do not mention Secure Boot at all.
- **Talos**: what enrolment Azure Trusted Launch requires, and how Sidero custodies the public
  Image Factory's signing key.
- **Fedora CoreOS** and **Bottlerocket**: private-key custody for both. Neither documents it.
- **Bottlerocket**: whether the ESP really never updates. Read off the update code, not stated
  in prose by a maintainer.
- Per-project unknowns are recorded inline in each section above.

## Questions for maintainers

None of these have been asked. Per the funnel's bias control, no negative claim here is
publishable until the relevant project has had the chance to correct it.

- **Kairos** (to Mauro first, as maintainer): is the unsigned Hadron boot chain intended? Is
  the architecture page's "out of the box" claim meant to survive the move to Hadron as the
  only released base, and if not, what should it say?
- **Fedora CoreOS**: is there a supported path for out-of-tree modules under Secure Boot, or
  is the honest answer "layer it and turn Secure Boot off"?
- **Bottlerocket**: on bare metal, is enrolling the shipped db certificate the only supported
  path, and is there guidance for firmware that cannot enrol custom keys?
- **Flatcar**: the shim-review submission has never been filed upstream and the fork carries no
  submission PR. Is it still blocked on the same legal or procedural issue? And is the absence
  of any Secure Boot page in the docs deliberate, given that stable has shipped signed artifacts
  since 2025-11-12?
- **Talos**: what must an operator enrol on Azure Trusted Launch, and is the absence of
  `secureboot-aws` and `secureboot-gcp` profiles a platform limitation or a roadmap item?

## Method and limits

Kairos was investigated from primary sources in `kairos-io/kairos` (`origin/master`
`96ef1c9`), `kairos-io/hadron` (`origin/main` `4ffdf3c`), `kairos-io/kairos-docs`
(`origin/main`), `kairos-io/AuroraBoot` (`origin/main`), the live docs site, the GitHub
releases API, and the published `ghcr.io/kairos-io/hadron:main` OCI image. One empirical check
was run (PE certificate-table parse on four binaries from that image).

The other four projects were researched from their own documentation, repositories, kernel
configs and issue threads, read through `gh api` rather than a web fetch wherever a GitHub
thread was involved. Three artifact checks were run there too, and are labelled REPRODUCED:
Flatcar's stable and LTS shim/GRUB/kernel signatures, and Talos's published Image Factory
signing certificate. Nothing was booted. No firmware was touched. No claim about any project
has been put to its maintainers.

Two things were corrected mid-research and are worth recording, because both were wrong in a
source this investigation would otherwise have trusted. Talos's own v1.14.0 release note says
Secure Boot images get `lockdown=integrity` implicitly; they shipped with `lockdown=none`, and
a maintainer confirmed it the next day. And the Pulse profile's Flatcar entry, following the
June 2025 maintainer comment, reads as though only alpha ships signed artifacts; stable has
shipped them since 2025-11-12, while LTS still does not.

The Pulse's per-project YAML profiles on the unmerged `feat/issue-813-pulse-profiles` branch
were used as a starting index of sources, not as evidence. Where a Pulse finding is repeated
here it was re-checked against the primary source it cites. The Kairos claim in
`kairos.yaml` d10 — recorded there as INFERRED, "the official ISOs carry a self-built shim
that will not validate under stock firmware keys" — is the one this ticket exists to test, and
it is now supported by an artifact check rather than by inference from the build alone.
