# Reproducible Machine State — investigation funnel

Source documents in this directory: `persona-strategy-v3-source.txt` (the uploaded
public-persona strategy, extracted from `.docx`) and `research-framework.md` (the
22-dimension research prompt Mauro pasted directly in chat). This file is the synthesis
of the two — read the sources for full detail, this is the index.

## The question

How do modern infrastructure systems make machine state reproducible, replaceable and
recoverable, and what architectural trade-offs does each make to get there?
Immutability is one answer to that question, not the definition of it.

## Two artifacts, deliberately different in scope

1. **A ≤5-page CNCF TAG Workloads Foundation paper.** Narrow and neutral. Centers Kairos,
   bootc and Flatcar only — the "deep experimental core." Requires a maintainer
   factual-review pass before publishing. Structure per the strategy doc: problem and
   definitions, architectural models, operational comparison table, decision scenarios,
   conclusions and open questions.
2. **A CNCF blog post.** The foundation's main blog, published through Mauro's CNCF
   Ambassador channel — a distinct submission from the TAG paper above, not a rename of
   it. Scope and timing (announcing the investigation vs synthesizing its findings) is
   still open.
3. **A personal public series** (blog on mauromorales.com, companion videos) using the
   full ten-platform landscape. Content is exhaust from findings, published as they land
   — not a pre-scheduled calendar. The strategy doc's suggested sequence (a working
   outline, not a commitment):
   1. What does "immutable" actually mean for a Linux machine?
   2. The artifact boundary: Kairos vs bootc.
   3. Flatcar and the Container Linux lineage.
   4. Recovery and rollback: what counts as "known-good"?
   5. Talos: what changes when Kubernetes is part of the machine-management contract?
   6. Bottlerocket and hyperscaler operating systems.
   7. NixOS: immutability, or actually reproducibility?
   8. Unikraft: is the host OS even the right boundary?
   9. Amutable, once testable.

## Platform depth is not uniform

The strategy doc stratifies research depth deliberately — spending equal time on every
platform is itself a bias risk the framework calls out (research-framework.md, evidence
standard section):

| Tier | Platforms | Treatment |
|---|---|---|
| Deep experimental core | Kairos, bootc, Flatcar | Full build/provision/extend/update/break/recover cycle, both experiment protocols from the research framework (failure injection, operational independence) |
| Representative | Talos, Bottlerocket | Architecture study + representative lifecycle experiments, not full depth |
| Hyperscaler case study | Azure Linux, Google Container-Optimized OS | Documentation-based; explicitly avoid reverse-engineering undocumented internals; label evidence limitations |
| Challenge the premise | NixOS | Different angle — tests whether reproducibility, not immutability, is the actual objective |
| Different paradigm | Unikraft | Boundary case — asks whether the traditional host OS is the right unit of deployment at all |
| Watch / emerging | Amutable | Track only; do not score against mature systems until enough public implementation exists |

## Bias control (applies to every sub-issue, stated once here)

Mauro maintains Kairos. Treat it exactly like every other project:
- Do not accept Kairos documentation uncritically, or use Kairos terminology as the
  neutral definition of the category.
- Actively look for disadvantages in Kairos's flexibility, architecture and governance.
- Do not treat Talos's (or any opinionated project's) constraints as disadvantages by
  default — determine what guarantees or operational benefits they buy instead.
- Distinguish project capability from commercial-ecosystem capability.
- For every negative claim about any project, get a maintainer correction before
  publishing anything comparative.
- If one project appears to win almost every scenario in the final synthesis, that is a
  signal to challenge the methodology, not a finding to publish as-is.

## Evidence discipline

Every factual claim carries one label: DOCUMENTED, REPRODUCED, OBSERVED, INFERRED,
UNKNOWN, or NOT TESTED (research-framework.md, evidence standard section). Missing
documentation is never treated as proof of absence.

## Model

Opus-class for every sub-issue under this epic — hard rule 7 puts architecture/research
judgment under bias-control requirements in that tier, not Sonnet-class grunt work.

## Three artifacts, not two — resolved

Mauro clarified, 2026-09-15: the TAG paper above and "the CNCF blog" are two separate
things, not one. The CNCF blog is the foundation's main blog, where Mauro can post as a
CNCF Ambassador — distinct from the TAG Workloads Foundation submission. Tracked as its
own sub-issue.

## Deliverable 1 replaced — resolved

Mauro gave a fully-specified first deliverable directly, 2026-09-15: **Cloud Native OS
Pulse 2026**,
superseding the open-ended "methodology and research plan" sub-issue
(closed). The Pulse is deliberately narrower and more concrete than
this file's original deliverable-1 description: a compact, sourced, publishable snapshot
of the ecosystem — explicitly not the full architectural comparison, no destructive
experiments, no rankings. It reuses this funnel's ten-platform landscape and bias-control
posture, adds Fedora CoreOS as its own entry alongside bootc, and folds Amutable's
"watch, don't score" treatment in as an explicit exclusion rather than a low-priority
sub-issue. Treat the Pulse brief as authoritative on deliverable 1's actual shape; this file's
"suggested public sequence" above still holds for the personal-series artifact, unchanged.
