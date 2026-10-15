# cloud native OS Pulse dataset

**Data collected: 2026-09-15. Every source re-read and every profile
re-verified: 2026-09-22.** Schema version 1.0.0.

The Pulse is a rolling release. There are no editions. The site states the
commit it was built from and the date it was generated. A script detects newer
releases, and the site flags those entries as not yet re-validated. A profile
moves to a new release only after its claims are re-validated against that
release (see [`REFRESH.md`](REFRESH.md)). Re-validation is a manual step today,
with no timing commitment. Every profile still carries an `edition` field. It is
kept for compatibility with schema 1.0.0 and does not mark an edition.

A point-in-time view of where the cloud-native and immutable operating system
ecosystem stands. It records what each project is, how it handles the machine
lifecycle, and where the architectures actually differ. It does not rank them and
it does not pick a winner.

Read [`methodology.md`](methodology.md) first. It explains the inclusion criteria,
the taxonomy, the evidence standard, the bias controls, and the projects that were left out along
with the effect of leaving them out.

## Status

| Piece | State |
|---|---|
| Methodology and taxonomy | Complete |
| Profile schema and validator | Complete |
| Project profiles | Complete, all sixteen. The first thirteen were fact-checked a second time on 2026-09-22 |
| Follow-up research backlog | Complete |
| Normalized comparison | Complete, inside the article draft |
| Maintainer review plan | Complete |
| FR-13 rollback-scope deep dives | Complete, all six: [bootc](../research/deep-dives/fr-13-rollback-scope-bootc.md), [Bottlerocket](../research/deep-dives/fr-13-rollback-scope-bottlerocket.md), [Fedora CoreOS](../research/deep-dives/fr-13-rollback-scope-fedora-coreos.md), [Flatcar](../research/deep-dives/fr-13-rollback-scope-flatcar.md), [Kairos](../research/deep-dives/fr-13-rollback-scope-kairos.md), [NixOS](../research/deep-dives/fr-13-rollback-scope-nixos.md) |

All sixteen profiles pass `validate_profiles.py` with zero errors. Research was
conducted against primary sources on 2026-09-15 and re-verified source by source
on 2026-09-22, with every dimension carrying an evidence label and, where the
label is `DOCUMENTED`, at least one source URL. Every change the second pass made
is in the profile's `corrections` list, dated and sourced.

## Profiles

| Project | Entry kind | Category fit | Profile |
|---|---|---|---|
| Kairos | framework, distribution | full | [`data/projects/kairos.yaml`](../data/projects/kairos.yaml) |
| Hadron | distribution, base-images | partial | [`data/projects/hadron.yaml`](../data/projects/hadron.yaml) |
| Talos Linux | distribution | full | [`data/projects/talos.yaml`](../data/projects/talos.yaml) |
| Flatcar Container Linux | distribution | full | [`data/projects/flatcar.yaml`](../data/projects/flatcar.yaml) |
| Fedora CoreOS | distribution | full | [`data/projects/fedora-coreos.yaml`](../data/projects/fedora-coreos.yaml) |
| bootc | mechanism | partial | [`data/projects/bootc.yaml`](../data/projects/bootc.yaml) |
| Bottlerocket | distribution, platform-os | full | [`data/projects/bottlerocket.yaml`](../data/projects/bottlerocket.yaml) |
| Azure Container Linux (ACL) | distribution, platform-os | partial | [`data/projects/azure-container-linux.yaml`](../data/projects/azure-container-linux.yaml) |
| Container-Optimized OS | platform-os | partial | [`data/projects/cos.yaml`](../data/projects/cos.yaml) |
| NixOS | distribution, framework | adjacent | [`data/projects/nixos.yaml`](../data/projects/nixos.yaml) |
| Unikraft | framework | adjacent | [`data/projects/unikraft.yaml`](../data/projects/unikraft.yaml) |
| Yocto Project | build-system | adjacent | [`data/projects/yocto.yaml`](../data/projects/yocto.yaml) |
| openSUSE MicroOS | distribution | full | [`data/projects/microos.yaml`](../data/projects/microos.yaml) |
| Ubuntu Core | distribution, framework | full | [`data/projects/ubuntu-core.yaml`](../data/projects/ubuntu-core.yaml) |
| Elemental | distribution, framework | full | [`data/projects/elemental.yaml`](../data/projects/elemental.yaml) |

A matrix entry meets five inclusion criteria, R1 to R5, set out in `methodology.md`
section 10 with a source for how each entry meets R5. NixOS, Unikraft and the Yocto
Project do not meet R1 to R4 as the project ships them and appear under
Alternative paradigms, not in the matrix. Amutable has public work but nothing released to profile, so it appears
under Worth mentioning and has no profile. Conventional mutable distributions are
out of scope.

Sixteen profiles, not nine. Fedora CoreOS and bootc are separated because a
distribution and a mechanism are not peers, and Hadron and Kairos are separated
for the same reason: Hadron is the base, Kairos is the framework applied to it,
and Hadron on its own is neither immutable nor upgradeable. NixOS, Unikraft and
the Yocto Project are profiled too, as alternative paradigms outside the matrix. See `methodology.md`
section 3 and the "thirteenth entry" note in section 10.

`microos.yaml` covers three release vehicles over one architecture: the rolling
community build, openSUSE Leap Micro, and the commercial SUSE Linux Micro. The
reasoning for one profile rather than three is in `methodology.md` section 10,
along with the researcher recommendation that argued the other way.

## Closed gaps

The first draft of the Pulse profiled ten projects and recorded openSUSE
MicroOS, SLE Micro and Ubuntu Core as a known gap, because all of them sit in the
same general-purpose-host position as Kairos and leaving them out made that part
of the map look sparser than it is. They have since been researched against the
same fourteen dimensions and added. The `transactional-snapshot` vocabulary value
is now used, and a new value, `snap-image-set`, was added for Ubuntu Core's
substrate.

One gap is left open deliberately. SUSE Linux Enterprise Server 16.1 gains an
immutable installation mode carrying SUSE Linux Micro's characteristics, and SUSE
has committed to an upgrade path from SUSE Linux Micro 6.2 into it. That is
recorded as a dated fact inside `microos.yaml` rather than profiled separately,
because the artifact a reader evaluates today is SUSE Linux Micro 6.2. A later
re-validation of `microos.yaml` should check whether the converged product is the
thing to profile.

## Validating the dataset

```sh
python3 tools/validate_profiles.py data/projects
```

The validator enforces the rules that keep the dataset honest: a documented
absence needs a source, an inference names its evidence, an unknown says where we
looked, both sides of `tradeoffs` are filled in, and no field may look like a
score or a rank.

## Corrections

Open a pull request against a project's YAML profile with the primary source for
the correct value. Corrections land in the profile's `corrections` list with the
date and source.
