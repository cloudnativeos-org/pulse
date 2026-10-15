# Follow-up research backlog

Questions this edition surfaced and does not answer. The Pulse is a documentation
survey. Everything here needs either deeper architectural analysis or an
experiment, and both are out of scope for a Pulse by design.

Each item has a stable id. Profiles reference these ids in their
`follow_up_research` field, so it is possible to ask which projects a given
question touches.

---

## Carried from the investigation framework

**FR-01. What does "immutable" actually mean across these architectures?**
The 2026 data already shows the word covering at least five different
arrangements: a verity-protected /usr with a writable root, a whole read-only
root, an OSTree deployment with a three-way-merged /etc, a read-only
content-addressed store under a mutable filesystem, and an image that cannot be
modified because there is no mechanism to modify it. These are not degrees of the
same property. They are different properties sharing a word.

**FR-02. A/B versus transactional versus A/B plus recovery versus OSTree: what is
the unit of reversibility?**
Not "which is better", but: when you roll back, what comes back with you, and
what does not. See FR-13, which is the sharpest version of this question.

**FR-03. What constitutes a known-good state?**
Each project has an implicit definition embedded in its automatic rollback
trigger. "The OS booted and a daemon did not crash within two minutes" and "the
kubelet registered and became Ready" are very different claims about health.
Collect each project's actual definition and compare them.

**FR-04. What happens when an update fails?**
Needs the failure-injection experiment protocol: power loss mid-write, corrupt
payload, kernel that does not boot, full disk.

**FR-05. How independently can each system be operated?**
Operation with no network, no management plane, no registry, no vendor
infrastructure. Partly answerable from documentation, but the interesting part is
what actually happens, not what is claimed.

**FR-06. How much customization is possible, and what guarantees does it weaken?**
The important half is the second. Every extension mechanism trades away some part
of the property the project sells. Which part, and how visibly is it stated?

**FR-07. Who owns the machine lifecycle: the OS, Kubernetes, or the fleet
manager?**
In several projects the answer is configurable, and the configurations are
mutually exclusive. Flatcar's locksmithd and FLUO cannot both run. That pattern is
worth mapping across projects.

**FR-08. Open source versus open governance versus vendor-neutral ownership.**
The 2026 dataset separates these four properties but does not analyse the
resulting matrix. The analysis is its own piece of work, and it must apply to
Kairos on the same terms.

**FR-09. Hardware extensibility.**
How does a new driver, a new board, or a new architecture actually reach a
released artifact in each project, and how long does that take?

**FR-10. Secure and measured boot architectures.**
See FR-14, which the 2026 research sharpened into a specific question.

**FR-11. Fleet lifecycle.**
The full loop: provision, configure, update, observe, recover, decommission.
Where does each project stop and something else start?

**FR-12. Recovery without Kubernetes, without the network, without the management
plane.**
Needs experiments. Documentation answers "is it possible", not "what does it take
and how long".

---

## Surfaced by the 2026 research

**FR-13. Rollback scope: what does an OS rollback actually revert?**
Flatcar's A/B pair covers /usr only, so /etc, /opt and /var survive a rollback
untouched. Whole-root A/B systems revert more. OSTree reverts the deployment but
keeps /var and merges /etc. The transactional snapshot model reverts the root and
/etc together while deliberately excluding /var, which is a fourth answer and the
one drawn closest to where an operator would want the line. A system that reverts
the OS but keeps the configuration change that broke it has rolled back less than
the word suggests.
Map this precisely across every project. This is probably the single most
misleading dimension in the category, and it is the first deep dive worth
writing.
Deep dives so far (live VM, not documentation alone): bootc
([research/deep-dives/fr-13-rollback-scope-bootc.md](../research/deep-dives/fr-13-rollback-scope-bootc.md)),
Fedora CoreOS
([research/deep-dives/fr-13-rollback-scope-fedora-coreos.md](../research/deep-dives/fr-13-rollback-scope-fedora-coreos.md)).
The Flatcar, Bottlerocket and NixOS legs are tracked separately.

Kairos leg run and verified against a live VM install/upgrade/rollback cycle:
[`research/deep-dives/fr-13-rollback-scope-kairos.md`](../research/deep-dives/fr-13-rollback-scope-kairos.md).
The remaining five need their own install path each; not a copy-paste of the
Kairos run.

**FR-14. Secure Boot key ownership: whose key, and what must an operator enrol?**
"Supports Secure Boot" hides a large difference. A project whose shim is signed by
the third-party UEFI CA works on stock firmware. A project that signs with its own
key requires the operator to enrol it, which on some hardware is not possible at
all. Establish, for every project: who holds the signing key, whether the shim is
CA-signed, what enrolment is required, and what happens to out-of-tree kernel
modules under lockdown.

**FR-15. Which projects have a genuinely self-hostable update path?**
An air-gapped or sovereign deployment needs the whole chain local: metadata
service, payloads, signing key trust. Some projects document this end to end,
some have the pieces on unrelated pages, some depend on vendor-hosted
infrastructure with no documented alternative. Establish which, with an actual
offline deployment as the test.

**FR-16. Documentation legibility as an operational property.**
Several projects have documentation that contradicts itself on load-bearing
facts, or has no page at all for a shipped capability. That is not a
nice-to-have: an operator choosing a system for a support window, or enrolling a
Secure Boot key, acts on what the docs say. Worth measuring consistently rather
than mentioning anecdotally, and worth applying to Kairos first.

**FR-17. What does a support window mean for a rolling OS?**
Some projects publish LTS streams with dates, some are explicitly rolling with no
LTS, and some publish a policy whose live state does not match it. For a team
that needs to answer an auditor, these are three different situations.

**FR-18. Who decides when a machine updates, and who decides what the update
contains?**
Most of this edition assumes the operator can decline an update indefinitely.
Ubuntu Core does not: a refresh can be held for at most 90 days, after which it
happens regardless, and the documented way to control what lands is to change the
store the device talks to rather than to stop the update. That inverts the usual
question. Instead of "can I defer this", it becomes "who controls the payload, and
is that party someone I can be". Map both halves across every project: the
maximum deferral a device will honour, and whether an adopter can operate the
thing that decides what an update delivers without a commercial agreement. This
overlaps FR-15 and sharpens it, because a self-hostable update path is not only
about reachability in an air gap, it is about who holds the decision.

**FR-19. How deep is reversibility, and can an operator find out?**
The A/B systems in this edition keep one or two slots, and say so. The
transactional snapshot model keeps whatever a retention policy says, so its
rollback depth is a configuration value rather than an architectural constant, and
the shipped default is published nowhere that this survey could find. Ubuntu Core
retains three revisions per snap, which means depth is per component rather than
per system. These are three different answers to "how far back can I go", and one
of them is not answerable from documentation at all. Establish the real default
for each project and whether an operator can discover it without reading shipped
configuration files.

---

## How to use this

These feed the later artifacts in the investigation: the architecture deep dives,
the reproducible experiments, and the requirement profiles. FR-13 and FR-14 are
the two that came out of the 2026 research with enough sharpness to write
immediately, and both are good candidates for the first deep dive. FR-18 is the
sharpest of the questions added with the MicroOS and Ubuntu Core entries, because
it is the one where the projects disagree about who the operator is. The Hadron
entry added no new question; it moved FR-14's Kairos half to where the shim is
actually built.
