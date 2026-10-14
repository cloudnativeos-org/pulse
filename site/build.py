#!/usr/bin/env python3
"""Build the Cloud Native OS Pulse sample site and design-system files from the YAML profiles.

Usage: build.py <projects-dir> <out-dir>

Writes:
  <out>/site/index.html      the matrix page: matrix, data sheets, sources. No server; prints to PDF through its print CSS
  <out>/site/guide.html      the guide: every other section. Deploy both files; neither needs another file
  <out>/ds/project/...       the design-system files (tokens, README, components, cover)

Reads the profiles, never writes them. Cells are generated from normalized fields.
Anything this script derives rather than reads is labelled INFERRED in the output.
"""
import datetime as dt
import glob
import html
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
LINEAGE = None
E = html.escape

DIMS = [
    ("d01", "OS model"), ("d02", "Immutability"), ("d03", "OS artifact"), ("d04", "Upgrade"),
    ("d05", "Rollback and recovery"), ("d06", "Customization"), ("d07", "Kubernetes relationship"),
    ("d08", "Hardware and platform"), ("d09", "Provisioning"), ("d10", "Security"),
    ("d11", "Operations and debugging"), ("d12", "Fleet management"), ("d13", "Governance"), ("d14", "Maturity"),
]
DIM_NAME = dict(DIMS)

# Entries in the comparison matrix, and entries shown in the context box instead.
CORE = ["azure-container-linux", "bootc", "bottlerocket", "cos", "eve-os", "fedora-coreos", "flatcar", "kairos", "microos", "talos", "ubuntu-core"]
CONTEXT = ["nixos", "unikraft", "yocto"]
PROFILES = {}
FOLDED = {"hadron": "kairos"}          # Hadron is shown inside the Kairos row
PENDING = []                          # approved entries with no profile yet

# Review-only annotations. They describe open fact-check items in neutral words and are
# not part of the public build. Keyed by (profile id, column key).
FACT_FIX = {
    ("microos", "rollback"): "health-checker is installed by default (documented). Whether its unit is enabled by default in a stock image is not verified.",
    ("cos", "project"): "Newer build since collection; milestone 133 is now also LTS.",
}

EVIDENCE = {
    "DOCUMENTED": ("documented", "Documented", "Doc"),
    "INFERRED": ("inferred", "Inferred", "Inf"),
    "UNKNOWN": ("unknown", "Unknown", "Unk"),
    "NOT_TESTED": ("not-tested", "Not tested", "N/T"),
    "REPRODUCED": ("reproduced", "Reproduced", "Rep"),
    "OBSERVED": ("observed", "Observed", "Obs"),
}
EVIDENCE_MEANING = {
    "DOCUMENTED": "Explicitly stated by a primary source. At least one source URL.",
    "INFERRED": "A reasonable conclusion from evidence that does not state it outright. Names its evidence.",
    "UNKNOWN": "Not enough evidence. Says where we looked.",
    "NOT_TESTED": "Needs an experiment this edition does not run.",
    "REPRODUCED": "Built or run independently, with the documented result.",
    "OBSERVED": "Behaviour measured directly.",
}


def load(projects_dir):
    out = {}
    for f in sorted(glob.glob(os.path.join(projects_dir, "*.yaml"))):
        d = yaml.safe_load(open(f))
        out[d["id"]] = d
    return out


def fmt_date(s):
    try:
        return dt.date.fromisoformat(str(s)).strftime("%-d %b %Y")
    except ValueError:
        return str(s)


# ---------------------------------------------------------------- sources
class Sources:
    def __init__(self):
        self.items, self.index = [], {}

    def add(self, src, project):
        key = src.get("url")
        if key not in self.index:
            self.items.append(dict(src, project=project))
            self.index[key] = len(self.items)
        return self.index[key]

    def cite(self, p, dim, n=1):
        d = dim_of(p, dim)
        srcs = (d.get("sources") or [])[:n]
        if not srcs:
            return ""
        nums = [self.add(s, p["name"]) for s in srcs]
        links = ",".join('<a href="#src-%d" aria-label="Source %d">%d</a>' % (k, k, k) for k in nums)
        return '<sup class="cite">[%s]</sup>' % links

    def render(self, only=None):
        """The source list. With `only`, a set of source numbers, just those, keeping their numbers."""
        rows = []
        for i, s in enumerate(self.items, 1):
            if only is not None and i not in only:
                continue
            rows.append(
                '<li id="src-%d" data-n="%d"><span><a href="%s">%s</a> <span class="src-meta">%s. %s. Retrieved %s.</span>'
                '<span class="src-url">%s</span></span></li>'
                % (i, i, E(s["url"]), E(s.get("title") or s["url"]), E(s["project"]), E(s.get("type", "")),
                   E(fmt_date(s.get("retrieved", ""))), E(s["url"])))
        return '<ol class="sources">%s</ol>' % "".join(rows)


def dim_of(p, short):
    for k, v in p["dimensions"].items():
        if k.startswith(short + "_"):
            return v
    return {}


def norm(p, short):
    return dim_of(p, short).get("normalized") or {}


# ---------------------------------------------------------------- atoms
def badge(label, compact=False):
    cls, long, short = EVIDENCE[label]
    return ('<span class="ev ev-%s%s" title="%s"><span class="ev-g" aria-hidden="true"></span>'
            '<span class="ev-t-long">%s</span><span class="ev-t-short" aria-hidden="true">%s</span>'
            '<span class="visually-hidden">%s</span></span>'
            % (cls, " compact" if compact else "", E(long + ": " + EVIDENCE_MEANING[label]), long, short,
               "" if not compact else ", evidence"))


# Newer-release notes come from the version check (tools/check_versions.py), not from this file.
VERSIONS = {}


def load_versions(projects_dir):
    f = os.path.join(projects_dir, "..", "versions-check.json")
    if os.path.exists(f):
        for pid, r in json.load(open(f)).items():
            VERSIONS[pid] = r
            if r.get("newer"):
                FACT_FIX[(pid, "project")] = "Newer release since collection: %s (checked %s). Not yet re-validated." % (r["latest"], r["checked_at"][:10])


def version_unchecked(pid):
    """The version check has no result for this entry, and no manual note says a newer release exists."""
    r = VERSIONS.get(pid)
    if FACT_FIX.get((pid, "project")):
        return ""
    if r is None or r.get("newer") is None:
        why = (r or {}).get("method") or "no result recorded"
        return '<span class="vchk" title="%s">Version not checked</span>' % E("The version check has no result for this entry: " + why + ".")
    return ""


def flag(pid, col, inline_note=True):
    note = FACT_FIX.get((pid, col))
    if not note:
        return ""
    return '<span class="flag review-flag" title="%s">%s</span>%s' % (
        E(note), "Newer release" if note.startswith("Newer") else "Fact-fix", '<span class="flag-note review-flag">%s</span>' % E(note) if inline_note else "")


def first_clause(s):
    s = str(s)
    return re.split(r";\s", s, maxsplit=1)[0]


def value(kind, text, detail=""):
    cls = {"value": "", "none": " v-none", "unknown": " v-unknown", "na": " v-na", "notcollected": " v-notcollected"}[kind]
    out = '<span class="v%s">%s</span>' % (cls, text)
    if detail:
        out += '<span class="v-detail">%s</span>' % detail
    return out


NOT_FOUND_TEXT = "Not found in the documentation we read."


def not_found():
    """A data sheet value that says what was not found, and invites a correction. The link goes to the correction section
    of the guide; in the preview build the same anchor explains how reviewers get access."""
    return ('<span class="nf">%s <a class="nf-ask" href="guide.html#fix-h">Know the answer?</a></span>' % NOT_FOUND_TEXT)


# The dimension each matrix column reads, to ask whether its profile records a search.
COL_DIM = {"byod": "d01", "rollback": "d05", "verified": "d04", "boot": "d10", "access": "d11", "capi": "d12",
           "selfhost": "d04", "own": "d13", "support": "d14"}


def searched(p, short):
    """The profile records that a search was done for this dimension: a searched field, or evidence UNKNOWN."""
    d = dim_of(p, short)
    return bool(d.get("searched")) or d.get("evidence") == "UNKNOWN"


def invite(p, col, html_):
    """In a data sheet cell, a value of Unknown or None documented becomes the invitation, where a search is recorded."""
    if 'ev-unknown' in html_ or (col in COL_DIM and searched(p, COL_DIM[col])):
        return re.sub(r'<span class="v v-(?:unknown|none)">(?:Unknown|None documented)</span>', not_found(), html_)
    return html_


# ---------------------------------------------------------------- columns
SCOPE = {"kubernetes-appliance": "Kubernetes appliance", "kubernetes-oriented-host": "Container host",
         "general-purpose-host": "General host", "single-application-image": "Single application image"}
CONSTR = {"vendor-fixed-image": "Vendor image", "vendor-base-plus-derivation": "Vendor base, you derive",
          "framework": "You build it (framework)", "package-repository-assembly": "Assembled from packages"}
DAY0 = {  # d09 method token -> path family; None = configuration, not an install path
    "iso": "ISO", "live-iso": "ISO", "iso-live": "ISO", "self-installing-iso": "ISO", "iso-installer": "ISO",
    "iso-community-supported": "ISO",
    "pxe": "PXE", "ipxe": "PXE", "pxe-ipxe-netboot": "PXE", "pxe-netboot": "PXE",
    "cloud-image": "Cloud image", "cloud-image-launch": "Cloud image", "ami-launch-with-user-data": "Cloud image",
    "marketplace-vm-image": "Cloud image", "aks-node-provisioning": "Cloud image",
    "raw-image": "Disk image", "raw-disk-image": "Disk image", "install-to-disk": "Disk image",
    "direct-disk-write-metal": "Disk image", "image-flashing": "Disk image",
    "interactive-installer": "Installer", "web-ui": "Installer", "unattended-install": "Installer",
    "unattended-cloud-config": "Installer",
    "vmware-cdrom-or-guestinfo": "VM image", "local-qemu": "VM image", "virtual-machine": "VM image",
    "uki": "UKI", "kexec": "kexec", "maas": "MAAS", "factory-provisioning": "Factory",
    "install-from-another-distribution": "From another distro", "wsl": "WSL",
    "cloud-init": None, "waagent": None, "oem-partition-embedded-config": None,
}
# What one update replaces. A closed vocabulary: a profile sets scope, or scope_by_mode where its modes differ.
UPDATE_SCOPE = {"whole-os-image": "Whole OS image", "os-tree-etc-merged": "OS tree, /etc merged", "usr-only": "/usr only",
                "root-snapshot-etc": "Root snapshot with /etc", "per-snap": "Per snap",
                "whole-node": "Whole node (reimaged or replaced)"}
# The short marker a cell shows when the profile has a scope_note. The full note is in the entry's data sheet.
SCOPE_NOTE_TAG = {"kairos": "See note: persistent paths", "flatcar": "See note: kernel", "talos": "See note: bootloader",
                  "bootc": "See note: /etc and /var", "azure-container-linux": "See note: AKS"}
MECH = {"ab-partition-switch": "A/B partition switch", "ostree-deployment": "OSTree deployment",
        "bootc-container-deployment": "OCI image deployment", "generation-switch": "Generation switch",
        "package-update": "Package update", "image-replacement-redeploy": "Replace the instance",
        "transactional-snapshot": "Transactional snapshot", "snap-revision-refresh": "Snap revision refresh"}
# Can a node check that an update is signed? Derived from d04 artifact_verification. (verdict, label, evidence, detail)
# The column records capability, not defaults: how the check is switched on goes in the detail line.
VERIFIED = {
    "none": ("no", "Not possible", "DOCUMENTED", ""),
    "policy-based, permissive by default": ("yes", "Possible", "DOCUMENTED", "Set in the image signature policy"),
    "signature-against-update-signing-key": ("yes", "Possible", "INFERRED", "Update signing key"),
    "tuf-four-role": ("yes", "Possible", "INFERRED", "TUF metadata"),
    "gpg-signature": ("yes", "Possible", "INFERRED", "GPG signature on the OS update image"),
    "assertion chain": ("yes", "Possible", "INFERRED", "Signed assertions"),
    "RPM and repository signing, inherited from the shared Tumbleweed repositories": ("yes", "Possible", "INFERRED", "RPM and repository signing"),
    "signature required by default": ("yes", "Possible", "INFERRED", "Signature required"),
    "signed unified kernel image": ("yes", "Possible", "INFERRED", "Checked at boot: a signed unified kernel image under Secure Boot, with Trusted Launch"),
    "sha256 digest carried in the controller configuration": ("digest", "Digest only", "INFERRED", "A sha256 digest in the controller configuration; no signature documented"),
    "unknown": ("unknown", "Unknown", "UNKNOWN", ""),
}
OWN = {"foundation-held": "Foundation-held", "single-vendor": "Single vendor", "mixed": "Mixed", "unknown": "Unknown"}
SUPPORT = {"none published": "None published", "lts-stream": "LTS stream", "versioned-with-eol": "Versioned, with end of life",
           "rolling-no-lts": "Rolling, no LTS", "vendor-lifecycle": "Vendor lifecycle", "unknown": "Unknown"}
ARCH = {"x86_64": "amd64", "aarch64": "arm64", "x86_64-linux": "amd64", "aarch64-linux": "arm64"}


class Cell:
    """html_ is the full cell text, shown in the entry's data sheet. tags are the short labels the matrix cell shows:
    a list of (text, kind), kind as in value(). With no tags, the cell shows the first line of html_."""
    def __init__(self, html_, sort="", filt=None, cls="", tags=None):
        self.html, self.sort, self.filt, self.cls, self.tags = html_, sort, filt or {}, cls, tags
        self.detail = html_


def uniq(xs):
    out = []
    for x in xs:
        if x not in out:
            out.append(x)
    return out


SHORT_NAME = {"hadron": "Hadron"}


def short_name(p):
    return SHORT_NAME.get(p["id"], p["name"])


# Install modes are equal choices: a tag per mode, in the profile's order, never a "default" and never a "highest".
# Short mode names for the tags; the wording drops "default", which the projects' own mode names carry in places.
MODE_NAME = {"standard": "Standard", "trusted_boot": "Trusted Boot", "Standard install": "Standard",
             "Trusted Boot": "Trusted Boot", "SecureBoot (UKI)": "SecureBoot UKI", "GRUB": "GRUB",
             "Sealed UKI with composefs": "Sealed UKI", "Default ostree with GRUB and shim": "ostree"}
MODE_LONG = {"Default ostree with GRUB and shim": "ostree with GRUB and shim"}


def mode_tag(p, mode, val, field):
    """One mode, its value, and a sourced requirement if the profile records one (field.mode_requirements)."""
    req = ((norm(p, "d10").get(field) or {}).get("mode_requirements") or {}).get(mode) if field else None
    txt = "%s: %s" % (MODE_NAME.get(mode, mode), val)
    if req and req.get("needs") and req.get("sources"):
        txt += ", needs " + req["needs"]
    return txt


def folded_child(p):
    """The entry shown inside this row (Hadron in the Kairos row), or None."""
    for child, parent in FOLDED.items():
        if parent == p["id"] and child in PROFILES:
            return PROFILES[child]
    return None


def meta(label, cite, pid=None, col=None):
    parts = [badge(label, compact=True), cite]
    if pid:
        parts.append(flag(pid, col))
    return '<span class="cell-meta">%s</span>' % "".join(x for x in parts if x)


def col_project(p, S, folded=None):
    v = p["version_observed"]
    tags = "".join('<span class="tag">%s</span>' % E(k) for k in p["entry_kind"])
    if norm(p, "d01").get("runs_outside_vendor_cloud") == "not supported":
        tags += '<span class="tag">Google Cloud only</span>'
    extra = ""
    if folded:
        h = folded["version_observed"]
        extra = ('<span class="proj-meta">Default base: %s <span class="mono">%s</span>. Values that come from it carry the label %s, '
                 'as in the matrix row. It has <a href="#tc-%s">its own data sheet</a>.</span>'
                 % (E(folded["name"]), E(str(h["version"])), E('"%s"' % short_name(folded)), E(folded["id"])))
        # In the cell, the folded entry is a tag, so a reader sees which values are the base's.
        tags += '<span class="tag tag-fold">%s: default base, <span class="mono">%s</span></span>' % (E(short_name(folded)), E(str(h["version"])))
    tail = (('<span class="cell-meta">%s</span>' % flag(p["id"], "project", False)) if FACT_FIX.get((p["id"], "project"))
            else ('<span class="cell-meta">%s</span>' % version_unchecked(p["id"])) if version_unchecked(p["id"]) else "")
    head = '<span class="proj">%s</span><span class="proj-meta"><span class="mono">%s</span> · %s</span>' % (
        E(p["name"]), E(str(v["version"])), E(fmt_date(v.get("released", ""))))
    c = Cell(head + '<span class="proj-tags">%s</span>%s' % (tags, tail), p["id"])
    note = FACT_FIX.get((p["id"], "project"))
    c.detail = head + extra + '<span class="proj-tags">%s</span>%s%s' % (tags, tail, '<span class="flag-note review-flag">%s</span>' % E(note) if note else "")
    return c


def col_scope(p, S):
    s = p["taxonomy"]["workload_scope"]
    return Cell(value("value", E(SCOPE.get(s, s))) + meta(dim_of(p, "d01")["evidence"], S.cite(p, "d01")),
                SCOPE.get(s, s), {"scope": s})


def col_constr(p, S):
    cm = p["taxonomy"]["construction_model"]
    lis = "".join("<li>%s</li>" % E(CONSTR.get(c, c)) for c in cm)
    return Cell('<ul class="v v-list">%s</ul>' % lis + meta(dim_of(p, "d01")["evidence"], S.cite(p, "d06")),
                CONSTR.get(cm[0], cm[0]), {"constr": " ".join(cm)}, tags=[(CONSTR.get(c, c), "value") for c in cm])


BASE_CHOICE = yaml.safe_load(open(os.path.join(HERE, "drafts", "base_choice.yaml")))


def byod_of(p):
    """From the draft base_choice field (drafts/base_choice.yaml), not yet in the dataset."""
    d = BASE_CHOICE.get(p["id"], {})
    if d.get("value") == "adopter-chosen":
        rel = d.get("released_images")
        detail = d.get("note", "")
        if p["id"] == "kairos":
            detail = "%d bases advertised. Released OS images: %s only." % (len(norm(p, "d01").get("bases_advertised", [])), ", ".join(rel))
        elif p["id"] == "bootc":
            detail = "Any bootc base image; adopters span several distributions."
        return ("yes", "Yes", detail, d["evidence"], d)
    if d.get("value") == "own-base-only":
        return ("no", "No, ships its own base", "", d["evidence"], d)
    return ("unknown", "Unknown", "", "UNKNOWN", d)


def col_byod(p, S):
    k, label, detail, ev, d = byod_of(p)
    cite = ""
    srcs = d.get("sources") or []
    if srcs:
        nums = [S.add(dict(s, title=s.get("title") or s["url"].split("//")[1], retrieved=s.get("retrieved") or "2026-09-22"), p["name"]) for s in srcs[:1]]
        cite = '<sup class="cite">[%s]</sup>' % ",".join('<a href="#src-%d">%d</a>' % (n, n) for n in nums)
    cls = "byod-yes" if k == "yes" else ""
    title = d.get("inferred_from", "")
    tags = [(label, {"yes": "value", "no": "value"}.get(k, "unknown"))]
    child = folded_child(p)
    if child and d.get("released_images") == [child["name"].split()[0]]:
        tags.append(("%s: the only released base" % short_name(child), "value"))
    return Cell('<span class="v %s"%s>%s</span>%s' % (cls, ' title="%s"' % E(title) if title else "", E(label),
                                                    '<span class="v-detail">%s</span>' % E(detail) if detail else "") + meta(ev, cite),
                "0" + label if k == "yes" else "1" + label, {"byod": k}, "byod", tags)


def col_day0(p, S):
    n = norm(p, "d09")
    m = n.get("methods")
    if m == "not-applicable" or m is None:
        return Cell(value("na", "Not an OS image", E(n.get("install_capability", ""))) + meta(dim_of(p, "d09")["evidence"], S.cite(p, "d09")),
                    "zz", {"day0": "na"}, tags=[("Not an OS image", "na")])
    fams = []
    for t in m:
        f = DAY0.get(t, t)
        if f and f not in fams:
            fams.append(f)
    cfg = n.get("config_mechanism")
    detail = "Config: " + E(re.split(r",| \(", first_clause(cfg))[0]) if cfg else ""
    keys = {"ISO": "iso", "PXE": "pxe", "Cloud image": "cloud", "Disk image": "disk"}
    return Cell('<ul class="v v-list">%s</ul>' % "".join("<li>%s</li>" % E(f) for f in fams)
                + ('<span class="v-detail">%s</span>' % detail if detail else "")
                + meta(dim_of(p, "d09")["evidence"], S.cite(p, "d09")),
                ", ".join(fams), {"day0": " ".join(keys[f] for f in fams if f in keys)}, tags=[(f, "value") for f in fams])


def col_update(p, S):
    n = norm(p, "d04")
    mech = n.get("mechanism") or []
    modes = n.get("scope_by_mode")
    # Modes are equal choices: one tag per mode, in the profile's order, never a "default", as in the Boot trust chain column.
    if modes:
        keys = list(modes.values())
        tags = [("%s: %s" % (m, UPDATE_SCOPE.get(k, k)), "value") for m, k in modes.items()]
        shown = "; ".join("%s: %s" % (m, UPDATE_SCOPE.get(k, k)) for m, k in modes.items())
    elif n.get("scope"):
        keys = [n["scope"]]
        tags = [(UPDATE_SCOPE.get(n["scope"], n["scope"]), "value")]
        shown = tags[0][0]
    else:
        keys = []
        shown = MECH.get(mech[0], mech[0]) if mech else "Not collected"
        tags = [(shown, "value" if mech else "notcollected")]
    parts = []
    if n.get("scope_note"):
        parts.append("Note: " + n["scope_note"].rstrip(".") + "." + (" Evidence: %s." % n["scope_note_evidence"] if n.get("scope_note_evidence") else ""))
        tags.append((SCOPE_NOTE_TAG.get(p["id"], "See note"), "note", "ds-%s-update" % p["id"], n["scope_note"]))
    if n.get("bootloader_upgraded_by_mode"):
        names = {"standard": "Standard install", "trusted_boot": "Trusted Boot"}
        parts.append("Boot files on upgrade: " + "; ".join("%s: %s" % (names.get(m, m), v) for m, v in n["bootloader_upgraded_by_mode"].items())
                     + (" (%s, code reading)" % n["bootloader_upgraded_evidence"] if n.get("bootloader_upgraded_evidence") else "") + ".")
    if mech:
        parts.append("Mechanism: " + ", ".join(MECH.get(x, x) for x in mech) + ".")
    if n.get("maximum_deferral"):
        parts.append("Longest hold: " + first_clause(n["maximum_deferral"]).split(",")[0] + ".")
    srcs = (n.get("scope_sources") or []) + (n.get("bootloader_upgraded_sources") or [])
    nums = [S.add(x, p["name"]) for x in srcs]
    cite = ('<sup class="cite">[%s]</sup>' % ",".join('<a href="#src-%d" aria-label="Source %d">%d</a>' % (k, k, k) for k in nums)) if nums else S.cite(p, "d04")
    detail = "".join('<span class="v-detail">%s</span>' % E(x) for x in parts)
    return Cell(value("value" if keys or mech else "notcollected", E(shown)) + detail
                + meta(dim_of(p, "d04")["evidence"], cite, p["id"], "update"),
                shown, {"update": " ".join(uniq(keys))} if keys else {}, tags=tags)


def col_verified(p, S):
    n = norm(p, "d04")
    modes = n.get("artifact_verification_by_mode")
    if modes:
        names = {"standard": "Standard install", "trusted_boot": "Trusted Boot"}
        detail = "; ".join("%s: %s" % (names.get(m, m), v) for m, v in modes.items())
        possible = any(v not in ("not checked", "none", "unknown") for v in modes.values())
        k, label = ("yes", "Possible") if possible else ("no", "Not possible")
        tags = [(mode_tag(p, m, v, None), "none" if v in ("not checked", "none") else "value") for m, v in modes.items()]
        # Modes are equal choices: the details give each mode's value, not one summary.
        return Cell(value("value", E(detail), E(n.get("artifact_verification_note", ""))) + meta(dim_of(p, "d04")["evidence"], S.cite(p, "d04")),
                    ("0" if possible else "2") + label, {"verified": k}, tags=tags)
    raw = n.get("artifact_verification", "unknown")
    k, label, ev, detail = VERIFIED.get(raw, ("unknown", first_clause(raw), "INFERRED", ""))
    kind = {"no": "none", "unknown": "unknown"}.get(k, "value")
    return Cell(value(kind, E(label), E(detail)) + meta(ev, S.cite(p, "d04"), p["id"], "verified"),
                {"yes": "0", "digest": "1", "no": "2", "unknown": "3"}[k] + label, {"verified": k}, tags=[(label, kind)])


BOOT_LEVEL = {3: "Running root covered", 2: "Measured boot", 1: "Secure Boot", 0: "Nothing checked"}
BOOT_HOW = {"always-on": "Always on", "default-on": "On by default", "opt-in": "Opt-in",
            "per-install-mode": "Depends on install mode", "platform-provided": "Provided by the platform"}
BOOT_ROUTE_TAG = {"usi": "UKI, no pivot", "verity-root-hash-in-signed-artifact": "verity hash signed"}
BOOT_ROUTE = {"usi": "the whole OS is inside the signed UKI, no pivot",
              "verity-root-hash-in-signed-artifact": "dm-verity root hash inside a signed boot artifact"}


def col_boot(p, S):
    b = norm(p, "d10").get("boot_trust_chain")
    if not b:
        return Cell(value("notcollected", "Not collected"), "9", {"boot": "unknown"}, tags=[("Not collected", "notcollected")])
    lvl = b.get("level")
    if lvl not in BOOT_LEVEL:
        return Cell(value("unknown", "Unknown", E(b.get("note", ""))) + meta("UNKNOWN", ""), "9", {"boot": "unknown"}, tags=[("Unknown", "unknown")])
    # Capability, not defaults: only where the capability comes from is shown, never whether it ships switched on.
    parts = [BOOT_HOW[b["how"]]] if b.get("how") == "platform-provided" else []
    if b.get("modes"):
        tags = [(mode_tag(p, m, "level %s" % v, "boot_trust_chain"), "none" if v == 0 else "value") for m, v in b["modes"].items()]
    else:
        tags = [("Level %d" % lvl, "none" if lvl == 0 else "value")]
    if any("level 3" in t for t, _ in tags) or (lvl == 3 and not b.get("modes")):
        if b.get("route") in BOOT_ROUTE_TAG:
            tags.append((BOOT_ROUTE_TAG[b["route"]], "value"))
    if b.get("how") == "platform-provided":
        tags.append((BOOT_HOW[b["how"]], "value"))
    if lvl == 3 and b.get("route") in BOOT_ROUTE:
        parts.append("How the root is covered: " + BOOT_ROUTE[b["route"]] + (" (%s)" % b["artifact"] if b.get("artifact") else ""))
    if b.get("note"):
        parts.append(b["note"])
    nums = [S.add(s, p["name"]) for s in (b.get("sources") or [])[:2]]
    cite = ('<sup class="cite">[%s]</sup>' % ",".join('<a href="#src-%d" aria-label="Source %d">%d</a>' % (k, k, k) for k in nums)) if nums else ""
    label = "Level %d: %s" % (lvl, BOOT_LEVEL[lvl])
    shown = label
    if b.get("modes"):
        # Modes are equal choices: the details name each mode's level, never one "highest" level.
        shown = "; ".join("%s: level %s (%s)" % (MODE_LONG.get(m, m), v, BOOT_LEVEL.get(v, "")) for m, v in b["modes"].items())
    return Cell(value("none" if lvl == 0 else "value", E(shown), E(". ".join(x.rstrip(".") for x in parts if x) + "."))
                + meta(b.get("evidence", "INFERRED"), cite, p["id"], "boot"),
                str(3 - lvl) + label, {"boot": " ".join(uniq(["l%d" % lvl] + ["l%s" % v for v in (b.get("modes") or {}).values()]))}, tags=tags)


def col_rollback(p, S):
    n = norm(p, "d05")
    raw = n.get("automatic_rollback_on_boot_failure", "unknown")
    att = n.get("automatic_rollback_attempts")
    if raw == "available":
        k, cell, tag = "yes", value("value", "Yes", E("Attempts: %s" % first_clause(att)) if att and att != "unknown" else ""), ("Yes", "value")
    elif raw == "none":
        k, cell, tag = "no", value("none", "No"), ("No", "none")
    elif raw == "unknown":
        k, cell, tag = "unknown", value("unknown", "Unknown"), ("Unknown", "unknown")
    elif raw == "not-applicable":
        k, cell, tag = "na", value("na", "Not applicable"), ("Not applicable", "na")
    else:
        k, cell, tag = "partial", value("value", E(first_clause(raw).capitalize())), (first_clause(raw).capitalize(), "value")
    # A value of Unknown carries the UNKNOWN label, whatever the label of the rest of the dimension.
    ev = "UNKNOWN" if k == "unknown" else dim_of(p, "d05")["evidence"]
    return Cell(cell + meta(ev, S.cite(p, "d05"), p["id"], "rollback"),
                {"yes": "0", "partial": "1", "no": "2", "unknown": "3", "na": "4"}[k], {"rollback": k}, tags=[tag])


def col_capi(p, S):
    n = norm(p, "d12")
    c = n.get("cluster_api") or {}
    ev = dim_of(p, "d12")["evidence"]
    types = c.get("provider_types") or []
    if types:
        mat = str(c.get("maturity", "")).split(":")[0].split(";")[0].split(", which")[0].strip()
        detail = ", ".join(types) + (". " + mat[0].upper() + mat[1:] if mat else "")
        label = "Own providers"
        if "no longer actively developed" in str(c.get("maturity", "")):
            # The maintainer's own README notice; the providers still exist and still get releases.
            label, detail = "Own providers, no longer actively developed", ", ".join(types) + ". README notices point to Omni; releases still ship"
        return Cell(value("value", E(label), E(detail)) + meta(ev, S.cite(p, "d12")), "0", {"capi": "own"},
                    tags=[(first_upper(t), "value") for t in label.split(", ")])
    via_kubeadm = "kubeadm" in str(c.get("provisions", "")) or c.get("bootstrap_maturity")
    if via_kubeadm:
        detail = "Ignition path " + ("alpha, behind a feature gate" if "alpha" in str(c.get("bootstrap_maturity", "")) else "")
        label = "Through kubeadm"
        if c.get("blocking_issue"):
            label = "Through kubeadm, reported to fail"
            detail = "First boot reported to fail. " + detail
        return Cell(value("value", label, E(detail.strip())) + meta(ev, S.cite(p, "d12")), "1", {"capi": "kubeadm"},
                    tags=[(first_upper(t), "value") for t in label.split(", ")])
    if str(c.get("os_specific_provider", "")).startswith("not-applicable"):
        return Cell(value("na", "Does not apply") + meta(ev, S.cite(p, "d12")), "3", {"capi": "none"}, tags=[("Does not apply", "na")])
    return Cell(value("none", "None documented") + meta(ev, S.cite(p, "d12")), "2", {"capi": "none"}, tags=[("None documented", "none")])


def col_access(p, S):
    """Every way to reach a node, as separate filter values, so an entry with SSH and a fleet server shows under both."""
    n = norm(p, "d11")
    ssh, sh, api = str(n.get("ssh", "unknown")), str(n.get("local_shell", "unknown")), n.get("api")
    if ssh == "unknown" and sh == "unknown":
        return Cell(value("unknown", "Unknown") + meta("UNKNOWN", S.cite(p, "d11")), "9", {"access": "unknown"}, tags=[("Unknown", "unknown")])
    if ssh.startswith("not-applicable"):
        return Cell(value("na", "Depends on the image") + meta(dim_of(p, "d11")["evidence"], S.cite(p, "d11")), "8", {"access": "image"},
                    tags=[("Depends on the image", "na")])
    tags, parts, notes = [], [], []
    if p["id"] == "eve-os":
        notes.append("No SSH in production builds")
    elif ssh.startswith("none") and "admin container" in ssh:
        tags += ["api", "shell"]
        parts += ["API", "shell through an optional admin container"]
    elif ssh.startswith("none") and sh.startswith("none"):
        tags += ["api", "noshell"]
        parts += ["API only"]
        notes.append("No SSH and no local shell")
    else:
        tags.append("shell")
        parts.append("SSH and shell")
    # A remote command channel that does not need SSH, where the profile documents one (d12 companions).
    channel = {"kairos": "AuroraBoot fleet server (open source)",
               "talos": "Omni (source-available)",
               "ubuntu-core": "Landscape (proprietary)",
               "eve-os": "Adam (open source) or ZEDEDA Cloud"}.get(p["id"])
    if channel:
        tags.append("fleet")
        parts.append("fleet server or controller")
        notes.append(channel)
    if n.get("access_note"):
        notes.append(n["access_note"])
    parts = [first_upper(x) for x in parts]
    order = {"noshell": "0", "api": "1", "fleet": "2", "shell": "3"}
    html_ = ('<ul class="v v-list">%s</ul>' % "".join("<li>%s</li>" % E(x) for x in parts)
             + ('<span class="v-detail">%s</span>' % E(". ".join(notes)) if notes else ""))
    tagl = [(x, "value") for x in parts]
    if p["id"] == "eve-os":
        tagl.append(("No SSH in production", "none"))
    return Cell(html_ + meta(dim_of(p, "d11")["evidence"], S.cite(p, "d11")),
                min(order[x] for x in tags) + ", ".join(parts), {"access": " ".join(tags)}, tags=tagl)


FLEET_KIND = {"operator": "Kubernetes operator", "suc": "system-upgrade-controller", "cluster-api": "Cluster API",
              "fleet-server": "Fleet server", "managed-service": "Managed node service", "reboot-coordination": "Reboot coordination"}
FLEET_REC = {"one-shot": "one-shot run", "in-place": "reconciled in place", "replacement": "reconciled by replacement"}
FLEET_KIND_TAG = {"operator": "Operator", "suc": "system-upgrade-controller", "cluster-api": "Cluster API", "fleet-server": "Fleet server",
                  "managed-service": "Managed service", "reboot-coordination": "Reboot coordination"}
FLEET_REC_TAG = {"one-shot": "one-shot", "in-place": "in place", "replacement": "replacement"}
FLEET_CLASS = {"open-source": "open source", "source-available": "source-available", "proprietary": "proprietary", "service": "managed service"}


def col_fleet(p, S):
    """How a fleet gets its OS upgraded: every documented path, with its license class and reconciliation model."""
    fu = norm(p, "d04").get("fleet_upgrade")
    if not fu:
        return Cell(value("notcollected", "Not collected"), "9", {"fleet": "nc"}, tags=[("Not collected", "notcollected")])
    items, extra, kinds, recs, classes, srcs, tagl = [], [], set(), set(), set(), [], []
    for x in fu.get("paths") or []:
        lic = x.get("license") or ""
        cls = FLEET_CLASS.get(x.get("class"), x.get("class", "")) if x.get("class") else ""
        bits = [cls, lic if lic and lic not in ("not recorded", "service") and lic.lower() != cls.lower() else ""]
        if x.get("reconciliation"):
            bits.append(FLEET_REC.get(x["reconciliation"], x["reconciliation"]))
        if x.get("status"):
            bits.append(x["status"])
        line = "%s: %s" % (FLEET_KIND.get(x["kind"], x["kind"]), x["name"])
        tail = ", ".join(b for b in bits if b)
        if x.get("filter") is False:
            extra.append("%s (%s)" % (line, tail) if tail else line)
            continue
        items.append('<li>%s <span class="v-tag">%s</span></li>' % (E(line), E(tail)))
        tagl.append(", ".join(b for b in (FLEET_KIND_TAG.get(x["kind"], x["kind"]), FLEET_REC_TAG.get(x.get("reconciliation"), "")) if b))
        kinds.add(x["kind"])
        if x.get("reconciliation"):
            recs.add(x["reconciliation"])
        if x.get("class") and x["kind"] != "reboot-coordination":
            classes.add(x["class"])
        srcs += x.get("sources") or []
    detail = []
    if fu.get("self_update"):
        detail.append("On its own: " + fu["self_update"].rstrip("."))
    if extra:
        detail.append("Also: " + "; ".join(extra))
    nums = [S.add(s, p["name"]) for s in srcs[:2] if s.get("url")]
    cite = ('<sup class="cite">[%s]</sup>' % ",".join('<a href="#src-%d" aria-label="Source %d">%d</a>' % (k, k, k) for k in nums)) if nums else ""
    ev = "INFERRED" if any(x.get("evidence") == "INFERRED" for x in fu.get("paths") or []) and not any(x.get("evidence") == "DOCUMENTED" for x in fu.get("paths") or []) else "DOCUMENTED"
    html_ = ('<ul class="v v-list">%s</ul>' % "".join(items) if items else value("none", "None documented")) \
        + ('<span class="v-detail">%s</span>' % E(". ".join(detail) + ".") if detail else "")
    tagl = [(t, "value") for t in uniq(tagl)] or [("None documented", "none")]
    return Cell(html_ + meta(ev, cite), str(9 - len(items)), tags=tagl, filt={"fleet": " ".join(sorted(kinds)) or "none",
                                                               "fleetrec": " ".join(sorted(recs)) or "none",
                                                               "fleetlic": " ".join(sorted(classes)) or "none"})


CFG_RUN = {"initramfs-before-root": "initramfs, before the root is mounted", "initramfs-after-root": "initramfs, after the root is mounted",
           "userspace": "userspace", "api": "API or controller", "install": "installer"}
CFG_RUN_TAG = {"initramfs-before-root": "initramfs", "initramfs-after-root": "initramfs", "userspace": "userspace", "api": "API", "install": "installer"}
CFG_TAG_NAME = {"Installer grub options, bootstrap-config.pb and controller EdgeDevConfig": "Installer options and controller",
                "snapd install mode with gadget.yaml": "gadget.yaml"}
CFG_RERUN = {"first-boot": "first boot only", "every-boot": "every boot", "lifecycle": "every boot, lifecycle stages and a periodic reconcile",
             "continuous": "reconciled continuously", "any-time": "changed at any time", "depends": "depends on the tool"}


def col_config(p, S):
    """The configuration tool, when it runs, when it re-runs, and what disk work it can do early."""
    tools = norm(p, "d09").get("config_tools")
    if not tools:
        return Cell(value("notcollected", "Not collected"), "9", {"cfgrun": "nc"}, tags=[("Not collected", "notcollected")])
    items, runs, reruns, srcs = [], set(), set(), []
    for x in tools:
        r = x.get("runs") or []
        runs.update(r)
        if x.get("reruns"):
            reruns.add(x["reruns"])
        tag = "; ".join(b for b in (", then ".join(CFG_RUN.get(v, v) for v in r), CFG_RERUN.get(x.get("reruns"), "")) if b)
        items.append('<li>%s%s <span class="v-tag">%s</span></li>' % (
            E(x["name"]), (' <span class="v-tag-inline">(%s)</span>' % E(x["license"])) if x.get("license") else "", E(tag)))
        srcs += x.get("sources") or []
    first = tools[0]
    detail = [s for s in (first.get("early_disk"), ("After first boot: " + first["change_after_first_boot"]) if first.get("change_after_first_boot") else "") if s]
    nums = [S.add(s, p["name"]) for s in srcs[:2] if s.get("url")]
    cite = ('<sup class="cite">[%s]</sup>' % ",".join('<a href="#src-%d" aria-label="Source %d">%d</a>' % (k, k, k) for k in nums)) if nums else ""
    ev = "DOCUMENTED" if any(x.get("evidence") == "DOCUMENTED" for x in tools) else "INFERRED"
    html_ = '<ul class="v v-list">%s</ul>' % "".join(items) + ('<span class="v-detail">%s</span>' % E(". ".join(d.rstrip(".") for d in detail) + ".") if detail else "")
    order = ["initramfs-before-root", "initramfs-after-root", "install", "userspace", "api"]
    earliest = min((order.index(r) for r in runs if r in order), default=9)
    tagl = []
    for x in tools[:3]:
        name = CFG_TAG_NAME.get(x["name"]) or re.sub(r"\s*\(.*?\)", "", x["name"]).strip()
        run = " + ".join(uniq(CFG_RUN_TAG.get(v, v) for v in x.get("runs") or []))
        tagl.append(("%s, %s" % (name, run) if run else name, "value"))
    return Cell(html_ + meta(ev, cite), str(earliest) + first["name"], tags=tagl, filt={"cfgrun": " ".join(sorted(runs)) or "none",
                                                                      "cfgrerun": " ".join(sorted(reruns)) or "none"})


AI_VENDOR = {"nvidia-gpu": "NVIDIA GPU", "nvidia-jetson": "NVIDIA Jetson", "amd": "AMD", "intel": "Intel", "aws-neuron": "AWS Neuron",
             "google-tpu": "Google TPU", "qualcomm": "Qualcomm", "edge-npu": "Edge NPU"}
AI_TAG = {"nvidia-gpu": "NVIDIA GPU", "nvidia-jetson": "Jetson", "amd": "AMD", "intel": "Intel", "aws-neuron": "Neuron",
          "google-tpu": "Google TPU", "qualcomm": "Qualcomm", "edge-npu": "Edge NPU"}
VIA_TAG = "Via your base distribution"
AI_SPECIFIC = ["nvidia-gpu", "nvidia-jetson", "amd", "intel", "aws-neuron", "google-tpu", "qualcomm", "edge-npu"]
AI_DELIVERY = {"project-signed": "signed driver from the project", "vendor-image": "vendor image or package", "layered": "layered package",
               "build-yourself": "you build it", "platform-build": "platform build"}
AI_SB = {"supported": "works with Secure Boot (documented)", "signed": "signed modules", "inferred-signed": "signed (inferred)", "unsigned": "unsigned modules", "not-documented": "Secure Boot not documented",
         "breaks": "breaks Secure Boot"}
AI_OP = {"host-driver": "GPU Operator with the host driver", "host-driver-and-toolkit": "GPU Operator with host driver and toolkit",
         "not-documented": "GPU Operator not documented", "not-supported": "GPU Operator not supported"}


def col_ai(p, S):
    """Documented AI accelerators, how the driver arrives, Secure Boot and the GPU Operator mode. The Kairos row includes Hadron."""
    blocks = [(p["name"], norm(p, "d08").get("ai_accelerators"))]
    for child, parent in FOLDED.items():
        if parent == p["id"] and child in PROFILES:
            blocks.append((PROFILES[child]["name"], norm(PROFILES[child], "d08").get("ai_accelerators")))
    if not any(b for _, b in blocks):
        return Cell(value("notcollected", "Not collected"), "9", {"ai": "nc"}, tags=[("Not collected", "notcollected")])
    items, vendors, deliveries, ops, srcs, notes, tagl = [], set(), set(), set(), [], [], []
    child = folded_child(p)
    for owner, b in blocks:
        if not b:
            continue
        if b.get("applies_to"):
            notes.append("%s: applies to %s" % (owner, b["applies_to"]))
        for x in b.get("items") or []:
            vendors.add(x["vendor"])
            if x.get("delivery"):
                deliveries.add(x["delivery"])
            if x.get("gpu_operator") in ("host-driver", "host-driver-and-toolkit"):
                ops.add("documented")
            bits = [", ".join(x.get("arch") or []), AI_DELIVERY.get(x.get("delivery"), ""), AI_SB.get(x.get("secure_boot"), ""),
                    AI_OP.get(x.get("gpu_operator"), "") if x.get("gpu_operator") else "", "unsupported, work in progress" if x.get("status") == "unsupported-wip" else "",
                    "inferred" if x.get("evidence") == "INFERRED" else ""]
            label = AI_VENDOR.get(x["vendor"], x["vendor"]) + (": " + x["what"] if x.get("what") else "")
            t = AI_TAG.get(x["vendor"], x["vendor"]) + (" (unsupported)" if x.get("status") == "unsupported-wip" else "")
            if child and owner == child["name"]:
                t = "%s: %s" % (short_name(child), t)
            tagl.append(t)
            if child and owner == child["name"]:
                label = "%s: %s" % (short_name(child), label)
            items.append('<li>%s <span class="v-tag">%s</span></li>' % (E(label), E("; ".join(s for s in bits if s))))
            srcs += x.get("sources") or []
    fb = (blocks[0][1] or {}).get("from_base_distribution")
    if fb:
        vendors.add("via-base")
        items.append('<li>Other accelerators: via your base distribution <span class="v-tag">%s</span></li>' % E(fb["note"].replace("Other accelerators: ", "").rstrip(".") + "."))
        srcs = (fb.get("sources") or []) + srcs
    nums = [S.add(s, p["name"]) for s in srcs[:2] if s.get("url")]
    cite = ('<sup class="cite">[%s]</sup>' % ",".join('<a href="#src-%d" aria-label="Source %d">%d</a>' % (k, k, k) for k in nums)) if nums else ""
    allx = [x for _, b in blocks if b for x in b.get("items") or []]
    ev = "DOCUMENTED" if any(x.get("evidence") == "DOCUMENTED" for x in allx) else "INFERRED"
    html_ = ('<ul class="v v-list">%s</ul>' % "".join(items) if items else value("none", "None documented")) \
        + ('<span class="v-detail">%s</span>' % E(". ".join(notes) + ".") if notes else "")
    tagl = [(t, "value") for t in uniq(tagl)]
    if fb:
        tagl.append((VIA_TAG, "via", AI_SPECIFIC, "Other accelerators: the drivers your chosen base distribution provides"))
    tagl = tagl or [("None documented", "none")]
    filt = {"ai": " ".join(sorted(vendors)) or "none", "aidel": " ".join(sorted(deliveries)) or "none", "aiop": " ".join(sorted(ops)) or "none"}
    if fb:
        filt["ai-via"] = " ".join(AI_SPECIFIC)   # picking a specific accelerator also keeps this entry, marked
    return Cell(html_ + meta(ev, cite), str(9 - len(vendors)), tags=tagl, filt=filt)


def col_k8s(p, S):
    """Requirement and bundling as one phrase. The filter keeps the requirement value."""
    n = norm(p, "d07")
    req = n.get("requirement", "unknown")
    b = str(n.get("bundled", ""))
    detail = ""
    if req == "required":
        label = "Bundled and required"
    elif req == "unrelated":
        label = "Not bundled"
        if p["id"] == "bootc":
            detail = "Documented through images built with it (MicroShift on RHEL image mode)"
    elif req == "optional":
        if p["id"] == "kairos":
            label = "Optional, bundled in standard images only"
        elif b in ("bundled",):
            label = "Optional, bundled"
        elif b in ("none", ""):
            label = "Optional, not bundled"
        elif b == "separately-installed":
            label = "Optional, installed separately"
        else:
            label = "Optional, bundled in some images"
            detail = first_upper(first_clause(b))
    else:
        label = first_upper(str(req))
    # Documented ways to run Kubernetes: distributions and install tools, as the profile lists them.
    ways = n.get("distributions")
    if ways is None:
        ways = n.get("distributions_documented_microos") or []
    short = []
    for w in ways:
        s = re.split(r"[,(]", str(w))[0].strip()
        s = re.sub(r"^the vendor's ", "", s)
        if s and s not in short and "ECS" not in s:  # ECS is a container service, not Kubernetes
            short.append(s)
    if ways:
        detail = (detail + ". " if detail else "") + "Documented ways to run Kubernetes: " + "; ".join(str(w) for w in ways)
    return Cell(value("value", E(label), E(detail)) + meta(dim_of(p, "d07")["evidence"], S.cite(p, "d07")),
                label, {"k8s": req}, tags=[(label, "value")] + [(s, "value") for s in short])


def arch_key(a):
    return a if a in ("amd64", "arm64", "riscv64") else "other"


def col_arch(p, S):
    """Architectures with a released OS image, then, for an entry that builds the OS from a base distribution the adopter
    picks, the architectures its own components are built for, as "<arch> via your base distribution" (methodology rule 21)."""
    n = norm(p, "d08")
    ev = dim_of(p, "d08")["evidence"]
    vb = n.get("architectures_via_base_distribution") or []
    via = []   # (arch, components, sources)
    for e in vb:
        for a in e["archs"]:
            via.append((a, e["components"], e.get("sources") or []))
    via_srcs = [x for _, _, ss in via for x in ss]
    via_filt = " ".join(sorted({arch_key(a) for a, _, _ in via}))
    def via_tag(entries):
        """One tag for the architectures of one entry of architectures_via_base_distribution, so the cell stays short."""
        archs = [a for a, _, _ in entries]
        comps = ", ".join(entries[0][1])
        return ("%s via your base distribution" % ", ".join(archs), "via", sorted({arch_key(a) for a in archs}),
                "Built for %s by the entry's own components (%s). The base distribution you pick supplies the rest." % (", ".join(archs), comps))
    cite_srcs = (dim_of(p, "d08").get("sources") or [])[:1] + via_srcs
    cite = cite_all(p, S, cite_srcs)
    meta_html = '<span class="cell-meta">%s%s</span>' % (badge(ev, compact=True), cite)
    if n.get("architectures_released") == "not-applicable":
        via_li = "".join('<li>%s via your base distribution <span class="v-tag">own components built for it: %s</span></li>' % (E(a), E(", ".join(c))) for a, c, _ in via)
        html_ = value("na", "Ships no OS image") + ('<ul class="v v-list">%s</ul>' % via_li if via_li else "")
        filt = {"arch": "na"}
        if via:
            filt["arch-via"] = via_filt
        return Cell(html_ + meta_html, "zz", filt, tags=[("Ships no OS image", "na")] + ([via_tag(via)] if via else []))
    arch, extra = [], ""
    for k, v in n.items():
        if isinstance(v, list) and ("released" in k or "with_os_images" in k) and "suse_linux_micro" not in k:
            for a in v:
                a = ARCH.get(a.split(",")[0].strip(), a.split(",")[0].strip())
                if a not in arch:
                    arch.append(a)
    keep = [i for i, t in enumerate(via) if t[0] not in arch]
    via_li = "".join('<li>%s via your base distribution <span class="v-tag">own components built for it: %s</span></li>' % (E(via[i][0]), E(", ".join(via[i][1]))) for i in keep)
    via_tags = [via_tag([via[i] for i in keep])] if keep else []
    in_via = {a for a, _, _ in via}
    for k in ("architectures_with_tooling_only", "architectures_in_progress"):
        rest = [a for a in (n.get(k) or []) if a not in in_via]
        if rest:
            extra = "Tooling only: " + ", ".join(rest)
    keys = " ".join(arch_key(a) for a in arch)
    # Where every released OS image is built on the folded entry (Kairos v4.3.0: Hadron only), the architectures describe those images.
    child = folded_child(p)
    pre = "%s: " % short_name(child) if child and BASE_CHOICE.get(p["id"], {}).get("released_images") == [child["name"].split()[0]] else ""
    filt = {"arch": keys}
    if via:
        filt["arch-via"] = via_filt
    return Cell('<ul class="v v-list">%s%s</ul>' % ("".join("<li>%s</li>" % E(pre + a) for a in arch), via_li)
                + ('<span class="v-detail">%s</span>' % E(extra) if extra else "")
                + meta_html,
                str(10 - len(arch)), filt, tags=[(pre + a, "value") for a in arch] + via_tags)


def col_selfhost(p, S):
    n = norm(p, "d04")
    if "self_hostable_update_server" not in n:
        return Cell(value("notcollected", "Not collected"), "3", {"selfhost": "nc"}, tags=[("Not collected", "notcollected")])
    raw = n.get("self_hostable_update_server")
    ev = n.get("self_hostable_update_server_evidence") or dim_of(p, "d04")["evidence"]
    what = E(n.get("self_hostable_update_source", ""))
    if raw is True:
        return Cell(value("value", "Yes", what) + meta(ev, S.cite(p, "d04")), "0", {"selfhost": "yes"}, tags=[("Yes", "value")])
    if raw == "commercial-only":
        return Cell(value("value", "Commercial only", what) + meta(ev, S.cite(p, "d04")), "1", {"selfhost": "commercial"}, tags=[("Commercial only", "value")])
    if raw is False:
        return Cell(value("none", "No") + meta(ev, S.cite(p, "d04")), "2", {"selfhost": "no"}, tags=[("No", "none")])
    return Cell(value("unknown", "Unknown") + meta("UNKNOWN", S.cite(p, "d04")), "3", {"selfhost": "unknown"}, tags=[("Unknown", "unknown")])


def col_own(p, S):
    n = norm(p, "d13")
    o = n.get("vendor_neutral_ownership", "unknown")
    f = n.get("foundation")
    detail = ("%s, %s" % (f.get("name"), f.get("level"))) if isinstance(f, dict) else (n.get("trademark_holder") or "")
    if o == "single-vendor" and (not detail or detail == "unknown") and n.get("primary_commercial_sponsor") not in (None, "", "unknown"):
        # The trademark holder is not recorded: name the vendor from the sponsor field, and say which field it is.
        detail = "Vendor: %s" % n["primary_commercial_sponsor"]
    kind = "unknown" if o == "unknown" else "value"
    return Cell(value(kind, E(OWN.get(o, o)), E(first_clause(detail)) if detail and detail != "unknown" else "")
                + meta(dim_of(p, "d13")["evidence"], S.cite(p, "d13")), OWN.get(o, o),
                {"own": {"foundation-held": "foundation", "single-vendor": "vendor"}.get(o, "other")}, tags=[(OWN.get(o, o), kind)])


def col_support(p, S):
    n = norm(p, "d14")
    sm = n.get("support_model", "unknown")
    cs = n.get("commercial_support")
    label = SUPPORT.get(sm, first_clause(sm).capitalize())
    kind = "unknown" if sm == "unknown" else "value"
    detail = "Commercial support: %s" % first_clause(cs) if cs else ""
    return Cell(value(kind, E(label), E(detail)) + meta(dim_of(p, "d14")["evidence"], S.cite(p, "d14")), label, tags=[(label, kind)])


# The ways to add software to the OS itself (profile field d06.normalized.add_software). One closed vocabulary, shown as tags.
ADDSW = [("systemd-sysext", "systemd-sysext", "System extension images, merged over /usr."),
         ("vendor-extensions", "Vendor extensions", "A project-specific extension format, such as Talos system extensions."),
         ("derive-image", "Derive the image", "Build a new OS image from the project's image, for example a Containerfile that starts FROM it."),
         ("package-layering", "Package layering", "Install packages onto the image-based system, for example rpm-ostree install."),
         ("transactional-packages", "Transactional packages", "Install packages into a new snapshot, for example transactional-update pkg install."),
         ("snaps", "Snaps", "Snap packages."),
         ("build-time-only", "Build-time only", "The image is composed at build and nothing is added after."),
         ("not-supported", "Not supported", "The project states you cannot add software to the host."),
         ("unknown", "Unknown", "Nothing was found.")]
ADDSW_LABEL = {k: lab for k, lab, _ in ADDSW}


def col_addsw(p, S):
    """How an adopter adds software to the OS itself: one tag per way, from the closed vocabulary. The data sheet gives each
    way with how it is done, its evidence label where that differs from the cell's, and its sources."""
    items = norm(p, "d06").get("add_software")
    if not items:
        return Cell(value("notcollected", "Not collected"), "9", {"addsw": "nc"}, tags=[("Not collected", "notcollected")])
    evs = [x.get("evidence", "UNKNOWN") for x in items]
    cell_ev = "UNKNOWN" if all(e == "UNKNOWN" for e in evs) else ("INFERRED" if "DOCUMENTED" not in evs else "DOCUMENTED")
    lis, tags, kinds = [], [], []
    for x in items:
        k = x["kind"]
        lab = ADDSW_LABEL.get(k, k)
        kinds.append(k)
        tags.append((lab, {"not-supported": "none", "unknown": "unknown"}.get(k, "value")))
        own = ""
        if x.get("evidence") != cell_ev:
            own = " " + badge(x["evidence"], compact=True)
        if x.get("evidence") == "INFERRED" and x.get("inferred_from"):
            own += '<span class="v-detail">Inferred from: %s</span>' % E(x["inferred_from"])
        if x.get("evidence") == "UNKNOWN" and x.get("searched"):
            own += '<span class="v-detail">Searched: %s</span>' % E(x["searched"])
        lis.append('<li><span class="v%s">%s</span>%s%s%s</li>' % (
            " v-none" if k == "not-supported" else (" v-unknown" if k == "unknown" else ""), E(lab),
            ('<span class="v-detail">%s</span>' % E(x["how"])) if x.get("how") else "",
            own, cite_all(p, S, x.get("sources"))))
    html_ = '<ul class="v v-list addsw">%s</ul>' % "".join(lis) + meta(cell_ev, "")
    return Cell(html_, ", ".join(ADDSW_LABEL.get(k, k) for k in kinds), {"addsw": " ".join(kinds)}, tags=tags)


COLUMNS = [
    # key, header, note (shown under "What the columns mean"), fn, proposed
    ("project", "Entry", "The entry, the version observed and its release date, and the entry kind. Click the name to open the entry's data sheet, with every column in full.", col_project, False),
    ("constr", "Who owns the artifact", "Who builds and patches what you run.", col_constr, False),
    ("byod", "Bring your own distro", "Can the entry run on a base distribution you choose?", col_byod, True),
    ("day0", "Day-0 paths", "How a node gets its first install and bootstrap. The data sheet names the configuration it reads.", col_day0, False),
    ("config", "Configuration tool", "The declarative configuration tool and when it runs: in the initramfs before or after the root is mounted, in userspace, or through an API. The data sheet gives its license, when it re-runs, and what disk work it can do early.", col_config, True),
    ("update", "Update unit", "What one update replaces. The data sheet names the mechanism and the longest hold.", col_update, False),
    ("addsw", "Adding software to the OS", "How an adopter adds software to the OS itself. This means host-level software, not workloads. One tag per documented way. "
     + " ".join("%s: %s" % (lab, txt) for k, lab, txt in ADDSW if k != "unknown") + " Unknown: nothing was found. "
     "Kairos and bootc build from a base distribution. Their own documented way is Derive the image. The base distribution's package manager is not credited after install unless their own documentation says so. "
     "The data sheet gives each way with how it is done and its sources.", col_addsw, True),
    ("verified", "Update signature check", "Can a node check that an update is signed? Where the entry has install modes, one tag per mode. The data sheet says how the check is switched on.", col_verified, True),
    ("boot", "Boot trust chain", "How far trust reaches at boot: level 1 Secure Boot, level 2 measured boot, level 3 the running root is covered by the signature. Where the entry has install modes, one tag per mode, as equal choices. Writable state such as /etc and /var is outside the signature on every entry.", col_boot, True),
    ("rollback", "Automatic rollback", "The machine reverts to the previous version by itself when the new one fails to boot.", col_rollback, False),
    ("fleet", "Fleet upgrade paths", "Documented ways a fleet gets its OS upgraded beyond one command per node, each with its reconciliation model: a one-shot run, reconciled in place, or reconciled by replacement. The data sheet names each tool and its license.", col_fleet, True),
    ("k8s", "Kubernetes", "Whether Kubernetes is required, optional or not bundled, then each documented way to run it: distributions such as k3s or MicroK8s, and install tools such as kubeadm or Cluster API. Whether Kubernetes is required, and whether it is bundled.", col_k8s, False),
    ("access", "Node access", "How you reach a node. API-only access limits changes to what the API exposes and makes them easy to log; a shell is more flexible and familiar. Neither is more secure by default.", col_access, True),
    ("capi", "Cluster API", "How a node joins a cluster through Cluster API.", col_capi, True),
    ("ai", "AI accelerators", "Accelerators the project or its vendor documents. The data sheet says how the driver reaches the node, whether its modules load with Secure Boot, and the NVIDIA GPU Operator mode. NVIDIA's own validated list names none of these entries; it documents Container-Optimized OS on GKE, and lists Jetson as not supported. An entry that builds the OS from a base distribution you pick is credited with what that base distribution documents, once, as \"Via your base distribution\". Picking a specific accelerator in the filter keeps those entries too, marked.", col_ai, True),
    ("arch", "Architectures", "CPU architectures that have released images, not intentions, each tagged. An entry that builds the OS from a base distribution you pick also lists the architectures its own components are built for, as \"via your base distribution\". Picking an architecture in the filter keeps those entries too, marked.", col_arch, False),
    ("selfhost", "Self-hostable update source", "Can you host where a node downloads its OS updates from, for example for an air-gapped site? Tools that decide when a node upgrades, such as Omni or the AuroraBoot fleet server, are a different question.", col_selfhost, True),
    ("own", "Who holds the assets", "Who holds the trademark and the project assets.", col_own, False),
    ("support", "Support model", "The support model. The data sheet says whether commercial support exists.", col_support, False),
]
# Glossary terms that explain a column, linked from "What the columns mean".
COL_GLOSS = {"project": [("Entry kind", "entry-kind")], "constr": [("Framework or mechanism", "framework-or-mechanism")],
             "day0": [("Day 0", "day-0-day-2")], "config": [("Declarative provisioning", "declarative-provisioning")],
             "update": [("Image-based", "image-based"), ("A/B partitions", "a-b-partitions")],
             "boot": [("Boot trust chain", "boot-trust-chain"), ("UKI", "uki"), ("Pivot", "pivot"), ("dm-verity", "dm-verity")],
             "rollback": [("Rollback", "rollback")], "capi": [("Cluster API", "cluster-api")],
             "fleet": [("One-shot run", "one-shot-run"), ("Reconciled in place", "reconciled-in-place"), ("Reconciled by replacement", "reconciled-by-replacement")],
             "support": [("LTS", "lts")], "addsw": [("System extension (sysext)", "system-extension-sysext"), ("Image-based", "image-based")]}
# Shown by default: five columns. The Columns control shows the rest. Entry is always shown and is not counted.
DEFAULT_COLS = ["project", "byod", "update", "rollback", "k8s", "arch"]

FILTERS = [
    ("byod", "Bring your own distro", [("yes", "Yes"), ("no", "No")]),
    ("cfgrun", "Configuration runs", [("initramfs-before-root", "Initramfs, before the root is mounted"), ("initramfs-after-root", "Initramfs, after the root is mounted"), ("install", "Installer"), ("userspace", "Userspace"), ("api", "API or controller")]),
    ("cfgrerun", "Configuration re-runs", [("first-boot", "First boot only"), ("every-boot", "Every boot"), ("lifecycle", "Lifecycle stages"), ("continuous", "Continuously"), ("any-time", "At any time"), ("depends", "Depends on the tool")]),
    ("update", "Update unit", [(k, v) for k, v in UPDATE_SCOPE.items()]),
    ("addsw", "Adding software to the OS", [(k, lab) for k, lab, _ in ADDSW]),
    ("rollback", "Automatic rollback", [("yes", "Yes"), ("partial", "Partial or conditional"), ("no", "No"), ("unknown", "Unknown")]),
    ("verified", "Update signature check", [("yes", "Possible"), ("digest", "Digest only"), ("no", "Not possible"), ("unknown", "Unknown")]),
    ("boot", "Boot trust chain", [("l3", "Level 3"), ("l2", "Level 2"), ("l1", "Level 1"), ("l0", "Level 0"), ("unknown", "Unknown")]),
    ("fleet", "Fleet upgrade path", [("operator", "Kubernetes operator"), ("cluster-api", "Cluster API"), ("fleet-server", "Fleet server"), ("managed-service", "Managed node service"), ("reboot-coordination", "Reboot coordination")]),
    ("fleetrec", "Fleet upgrade reconciliation", [("in-place", "Reconciled in place"), ("replacement", "Reconciled by replacement"), ("one-shot", "One-shot run")]),
    ("fleetlic", "Fleet tool license", [("open-source", "Open source"), ("source-available", "Source-available"), ("proprietary", "Proprietary"), ("service", "Managed service")]),
    ("k8s", "Kubernetes", [("required", "Bundled and required"), ("optional", "Optional"), ("unrelated", "Not bundled")]),
    ("access", "Node access", [("shell", "SSH and shell"), ("api", "API"), ("fleet", "Fleet server or controller"), ("noshell", "No SSH or shell"), ("unknown", "Unknown")]),
    ("capi", "Cluster API", [("own", "Own providers"), ("kubeadm", "Through kubeadm"), ("none", "None")]),
    ("ai", "AI accelerator", [("nvidia-gpu", "NVIDIA GPU"), ("nvidia-jetson", "NVIDIA Jetson"), ("amd", "AMD"), ("intel", "Intel"), ("aws-neuron", "AWS Neuron"), ("google-tpu", "Google TPU"), ("qualcomm", "Qualcomm"), ("edge-npu", "Edge NPU"), ("via-base", "Via your base distribution")]),
    ("aidel", "Accelerator driver", [("project-signed", "Signed driver from the project"), ("vendor-image", "Vendor image or package"), ("layered", "Layered package"), ("build-yourself", "You build it"), ("platform-build", "Platform build")]),
    ("aiop", "NVIDIA GPU Operator", [("documented", "Documented")]),
    ("arch", "Architecture", [("amd64", "amd64"), ("arm64", "arm64"), ("riscv64", "riscv64"), ("other", "Other")]),
    ("day0", "Day-0 path", [("iso", "ISO"), ("pxe", "PXE"), ("cloud", "Cloud image"), ("disk", "Disk image")]),
    ("selfhost", "Self-hostable update source", [("yes", "Yes"), ("commercial", "Commercial only"), ("unknown", "Unknown")]),
    ("own", "Assets held by", [("foundation", "Foundation"), ("vendor", "Single vendor")]),
]

# One neutral sentence per filter, shown under its title in the Filters panel.
FILTER_DESC = {
    "byod": "Whether you can build on top of a base distribution you already use.",
    "cfgrun": "Where in the boot or install flow the configuration tool runs.",
    "cfgrerun": "How often the configuration tool applies its configuration again after the first run.",
    "update": "What one update replaces, for example the whole image or a package set.",
    "addsw": "How you add host software to the OS image or the running system.",
    "rollback": "Whether the machine reverts to the previous version by itself when a new one fails to boot.",
    "verified": "Whether a node can check that an update is signed before it applies it.",
    "boot": "How far trust reaches at boot, from Secure Boot alone to a signed running root.",
    "fleet": "The documented ways to upgrade a whole fleet beyond one command per node.",
    "fleetrec": "How the fleet tool keeps nodes at the wanted version: once, in place, or by replacing the node.",
    "fleetlic": "The license of the fleet upgrade tool.",
    "k8s": "Whether Kubernetes is required, optional or not bundled with the entry.",
    "access": "How you reach a node once it runs.",
    "capi": "How a node joins a cluster through Cluster API.",
    "ai": "Accelerators the project or its vendor documents support for. Entries that build on a base distribution you pick also match, marked.",
    "aidel": "How the accelerator driver reaches the node.",
    "aiop": "Whether the NVIDIA GPU Operator mode is documented for the entry.",
    "arch": "CPU architectures with a released image. Entries whose own components are built for an architecture, on a base distribution you pick, also match, marked.",
    "day0": "How a node gets its first install and bootstrap.",
    "selfhost": "Whether you can host the place where a node downloads its OS updates.",
    "own": "Who holds the trademark and the project assets.",
}

# The column a filter reads. A filter on a hidden column shows that column.
FILTER_COL = {"update": "update", "addsw": "addsw", "byod": "byod", "cfgrun": "config", "cfgrerun": "config", "rollback": "rollback", "verified": "verified", "boot": "boot",
              "fleet": "fleet", "fleetrec": "fleet", "fleetlic": "fleet", "k8s": "k8s", "access": "access", "capi": "capi",
              "ai": "ai", "aidel": "ai", "aiop": "ai", "arch": "arch", "day0": "day0", "selfhost": "selfhost", "own": "own"}

# The evidence labels the legend and the glossary both list, in this order.
EVIDENCE_SHOWN = ("DOCUMENTED", "INFERRED", "UNKNOWN", "NOT_TESTED")
ENTRY_KIND = [("distribution", "ships released OS artifacts with versions and a release process"),
              ("platform-os", "an OS produced mainly to run one vendor platform"),
              ("framework", "a toolchain for producing an OS; the adopter owns the result"),
              ("mechanism", "a component that implements part of the lifecycle; not an OS on its own"),
              ("build-system", "builds an OS image from source recipes; the adopter owns the image, and each capability comes from the layers the adopter selects")]


def read_matrix():
    """How to read the matrix: evidence labels, value kinds, badges and entry kinds, just above it."""
    vals = ('<li><span class="v v-none">None</span> a documented absence</li>'
            '<li><span class="v v-unknown">Unknown</span> not determined</li>'
            '<li><span class="v v-na">does not apply</span></li>'
            '<li><span class="v v-notcollected">Not collected</span> no data for this field yet</li>')
    badges = ('<li><span class="mx-sample t-inf">Inferred</span> a dashed border: inferred, not stated outright</li>'
              '<li><span class="mx-sample mx-sample-note">See note</span> opens the note in the data sheet</li>'
              '<li><span class="flag">Fact-fix</span> a cell under review; it may change</li>'
              '<li><span class="flag">Newer release</span> released after collection, not yet re-checked</li>'
              '<li><span class="vchk">Version not checked</span> the version check has no result for this entry</li>')
    kinds = "".join('<li><span class="tag">%s</span> %s</li>' % (E(k), E(t)) for k, t in ENTRY_KIND)
    return ('<div class="mx-read"><h3 id="mx-read-h">How to read the matrix</h3>'
            '<p class="mx-read-lede">Each cell shows the values. Open a project\'s data sheet (click its name) for the evidence label and the sources behind each one.</p>'
            '<div class="mx-read-grid">'
            '<div><p class="mx-read-k">Values</p><ul>%s</ul></div>'
            '<div><p class="mx-read-k">Badges</p><ul>%s</ul></div>'
            '<div><p class="mx-read-k">Entry kind</p><ul>%s</ul></div></div>'
            '<p class="mx-read-foot"><a href="#h-made">How it was made</a> explains the sources and the checks behind every cell. '
            'The <a href="#h-gloss">glossary</a> defines the terms.</p></div>' % (vals, badges, kinds))


def tags_html(tags, inferred=False):
    """A tag is (text, kind). A "note" tag is (text, "note", data sheet row id, full note): a link to that row of the entry's data sheet."""
    cls = {"value": "", "none": " v-none", "unknown": " v-unknown", "na": " v-na", "notcollected": " v-notcollected"}
    out = []
    for t in tags:
        if t[1] == "note":
            out.append('<li class="t t-note"><a class="mx-note" href="#%s" title="%s">%s</a></li>'
                       % (E(t[2]), E(t[3]), E(t[0])))
        elif t[1] == "via":
            # (text, "via", filter values it can satisfy, title). A filter that matches only through this tag highlights it.
            out.append('<li class="t t-via" data-via="%s" title="%s">%s</li>' % (E(" ".join(t[2])), E(t[3]), E(t[0])))
        elif inferred and t[1] in ("value", "none"):
            # The matrix is an overview: the evidence label lives in the data sheet. An inferred value keeps a mark on its tag.
            out.append('<li class="t t-inf%s" title="Inferred" aria-label="%s, inferred">%s</li>' % (cls[t[1]], E(t[0]), E(t[0])))
        else:
            out.append('<li class="t%s">%s</li>' % (cls[t[1]], E(t[0])))
    return '<ul class="tags">%s</ul>' % "".join(out)


def cell_meta(full):
    """The review flags from the end of a cell's full text. The matrix is an overview, so the evidence badge and the citations
    stay in the data sheet. Flag notes stay in the data sheet too."""
    i = full.rfind('<span class="cell-meta">')
    if i < 0:
        return ""
    meta_ = re.sub(r'<span class="flag-note review-flag">.*?</span>', "", full[i:], flags=re.S)
    flags = re.findall(r'<span class="flag review-flag"[^>]*>[^<]*</span>', meta_)
    return '<span class="cell-meta">%s</span>' % "".join(flags) if flags else ""


def is_inferred(full):
    """The cell's evidence label is INFERRED, read from the badge at the end of its full text."""
    i = full.rfind('<span class="cell-meta">')
    return i >= 0 and 'class="ev ev-inferred' in full[i:]


def columns_explained():
    """Every column's definition, for the guide. Each entry has the id col-<key>, which the "?" links point at."""
    items = []
    for k, h, note, _, _ in COLUMNS:
        gl = COL_GLOSS.get(k)
        more = (' <span class="mx-ex-g">Glossary: %s.</span>' % ", ".join('<a href="#g-%s">%s</a>' % (a, E(t)) for t, a in gl)) if gl else ""
        items.append('<div id="col-%s"><dt>%s</dt><dd>%s%s</dd></div>' % (k, E(h), E(note), more))
    items.append('<div id="col-mounts"><dt>Mounts</dt><dd>%s</dd></div>' % E(MOUNTS_NOTE))
    return '<dl class="mx-ex">%s</dl>' % "".join(items)


def col_defs():
    """The column definitions as data for the matrix page, so a "?" opens one in the modal without leaving the page.
    Without JavaScript the "?" is a plain link to the guide."""
    defs = {}
    for k, h, note, _, _ in COLUMNS:
        gl = COL_GLOSS.get(k)
        more = ('<p class="pm-gloss">Glossary: %s.</p>' % ", ".join('<a href="guide.html#g-%s">%s</a>' % (a, E(t)) for t, a in gl)) if gl else ""
        defs[k] = {"title": h, "html": '<p>%s</p>%s' % (E(note), more)}
    defs["mounts"] = {"title": "Mounts", "html": "<p>%s</p>" % E(MOUNTS_NOTE)}
    return '<script type="application/json" id="col-defs">%s</script>' % json.dumps(defs).replace("</", "<\\/")


def sheet_link(p, label=None):
    """A project's name as a link that opens its data sheet. On the guide it goes to the matrix page and opens there."""
    return '<a class="proj-open" href="#tc-%s">%s</a>' % (p["id"], E(label or p["name"]))


def cells_of(p, S):
    """Every matrix column for one entry, as Cell objects. The matrix and the data sheet both read these."""
    folded = folded_child(p)
    return [c[3](p, S, folded) if c[0] == "project" else c[3](p, S) for c in COLUMNS]


def matrix(P, S):
    rows = []
    ncol = len(COLUMNS)
    for pid in CORE:
        p = P[pid]
        cells = cells_of(p, S)
        filt = {}
        for c in cells:
            filt.update(c.filt)
        attrs = " ".join('data-f%s="%s"' % (k, E(v)) for k, v in filt.items())
        # The name is the link that opens the entry's data sheet.
        plain = '<span class="proj">%s</span>' % E(p["name"])
        linked = ('<span class="proj"><a class="proj-open" href="#tc-%s" title="Open the data sheet for %s"><span class="proj-n">%s</span>'
                  '<span class="visually-hidden">, data sheet</span></a></span>' % (pid, E(p["name"]), E(p["name"])))
        assert plain in cells[0].html
        tds = ['<th scope="row" class="c-project" data-col="project" data-sort="%s">%s</th>' % (E(cells[0].sort), cells[0].html.replace(plain, linked, 1))]
        for (k, h, _, _, _), c in list(zip(COLUMNS, cells))[1:]:
            inner = tags_html(c.tags, is_inferred(c.html)) + cell_meta(c.html) if c.tags else c.html
            tds.append('<td class="c-%s%s" data-col="%s" data-sort="%s">%s</td>' % (k, " " + c.cls if c.cls else "", k, E(c.sort), inner))
        key = p["name"].lower()
        rows.append((key, '<tr data-id="%s" data-name="%s" %s>%s</tr>' % (pid, E(key), attrs, "".join(tds))))
    head = "".join(
        '<th scope="col" data-col="%s" class="c-%s%s"%s><span class="mx-head"><button class="mx-col" type="button" aria-pressed="false" aria-label="Mark %s" title="Mark %s">%s</button>'
        '<a class="mx-q" href="#col-%s" aria-label="What %s means" title="What %s means">?</a>'
        '<button class="mx-sort" type="button" aria-label="Sort by %s" title="Sort by %s"></button></span></th>'
        % (k, k, " byod" if k == "byod" else "", ' aria-sort="ascending"' if k == "project" else "",
           E(h), E(h), E(h), k, E(h), E(h), E(h), E(h))
        for k, h, note, _, prop in COLUMNS)
    bodies = ['<tbody data-group="entries">%s<tr class="empty" hidden><td colspan="%d">No entry matches these filters.</td></tr></tbody>'
              % ("".join(r for _, r in sorted(rows)), ncol)]
    pend = "".join(
        '<tr class="pending" data-id="%s" data-name="%s"><th scope="row"><span class="proj">%s</span>'
        '<span class="proj-meta">Approved as an entry. Profile not collected yet.</span></th>'
        '<td colspan="%d">Nothing about this entry is claimed until its profile exists and validates.</td></tr>'
        % (pid, E(name.lower()), E(name), ncol - 1) for pid, name in PENDING)
    if PENDING:
        bodies.append('<tbody data-group="pending"><tr class="gh gh-pending"><th colspan="%d" scope="rowgroup"><div class="gh-inner">'
                      '<span class="gh-name">Profile pending</span><span class="gh-count">%d entry</span></div></th></tr>%s</tbody>'
                      % (ncol, len(PENDING), pend))
    fsets = "".join(
        '<fieldset class="mx-fg" data-col="%s"><legend>%s</legend>'
        '<p class="mx-fd">%s%s</p><div class="mx-fo">%s</div></fieldset>'
        % (FILTER_COL.get(k, ""), E(lab), E(FILTER_DESC[k]),
           (' <a class="mx-q" href="#col-%s" aria-label="What %s means" title="What %s means">?</a>' % (FILTER_COL[k], E(lab), E(lab))) if FILTER_COL.get(k) else "",
           "".join('<label class="chip"><input type="checkbox" name="%s" value="%s"><span>%s</span></label>' % (k, v, E(t)) for v, t in opts))
        for k, lab, opts in FILTERS)
    picks = "".join(
        '<label class="chip"><input type="checkbox" name="col" value="%s"%s%s><span>%s</span></label>'
        % (k, " checked" if k in DEFAULT_COLS else "", " disabled" if k == "project" else "", E(h)) for k, h, _, _, _ in COLUMNS)
    legend = read_matrix()
    return (legend + '<div class="mx-wrap" id="matrix" data-default-cols="%s">'
            '<div class="mx-tools no-print">'
            '<details class="mx-cols"><summary>Columns <span class="mx-cols-n"></span></summary><div class="mx-cols-panel">'
            '<fieldset><legend>Columns shown</legend>%s</fieldset>'
            '<div class="mx-cols-act"><button class="btn mx-cols-all" type="button">Show all columns</button><button class="btn mx-cols-reset" type="button">Default columns</button></div></div></details>'
            '<details class="mx-filters"><summary>Filters <span class="mx-fn">(0 active)</span></summary>'
            '<form class="mx-bar" onsubmit="return false" aria-label="Filter the matrix">%s</form></details></div>'
            '<div class="mx-status no-print"><span class="mx-count" role="status"></span><span class="mx-active" aria-label="Active filters"></span>'
            '<button class="btn mx-clear" type="button" disabled>Clear filters</button></div>'
            '<div class="mx-scroll"><table class="mx"><caption class="visually-hidden">Lead comparison matrix. Rows sorted alphabetically by name.</caption>'
            '<colgroup><col class="c-proj"></colgroup><thead><tr>%s</tr></thead>%s</table></div></div>'
            % (" ".join(DEFAULT_COLS), picks, fsets, head, "".join(bodies)))


# ---------------------------------------------------------------- blocks
REREAD = "2026-09-22"  # the full re-verification: every cited source re-read (see How it was made)


def _walk_dates(x, key, out):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == key and v:
                out.add(str(v))
            else:
                _walk_dates(v, key, out)
    elif isinstance(x, list):
        for v in x:
            _walk_dates(v, key, out)


def data_dates(P):
    """Dates the data supports: when profiles were collected, and the newest date a cited source was read."""
    coll = sorted({str(p["collected_at"]) for p in P.values()})
    read = set()
    _walk_dates(list(P.values()), "retrieved", read)
    read = sorted(d for d in read if re.match(r"\d{4}-\d\d-\d\d$", d))
    return coll, read[-1] if read else REREAD


def stamp(P):
    coll, newest = data_dates(P)
    span = fmt_date(coll[0]) if coll[0] == coll[-1] else "%s to %s" % (fmt_date(coll[0]), fmt_date(coll[-1]))
    return ('<span class="stamp"><b>Data as of</b> <time datetime="%s">%s</time>'
            '<span class="muted">The newest date a cited source was read. Profiles collected %s; every source re-read %s.</span></span>'
            % (newest, fmt_date(newest), span, fmt_date(REREAD)))


META = yaml.safe_load(open(os.path.join(HERE, "projects_meta.yaml")))


# Identifiers whose first word is an ordinary word, not a name, read in lower case after "named by".
LOWER_FIRST = ("Image", "Milestone", "Release")
# One identifier does not read after "named by" as recorded. Same facts, reordered. Recorded value:
# "By default none for the whole OS: the model assertion plus a revision per snap. With a pinning validation set: account-id/name/sequence"
NAMED_BY = {"ubuntu-core": "the model assertion plus a revision per snap, by default (none for the whole OS); with a pinning validation set, account-id/name/sequence"}


def version_identity(p, S):
    """Criterion 1 on a data sheet: what names the deployed OS, and under which condition. From d04 normalized.version_identity.
    Returns the row content: the value, then the evidence badge and citation."""
    n = norm(p, "d04")
    vi = n.get("version_identity")
    crit = '<span class="v-detail">Inclusion criterion 1: <a href="#w-criteria">versioned whole-system updates</a>.</span>'
    if not vi:
        prov = n.get("provided_by")
        if not prov or prov not in PROFILES:
            return value("notcollected", "Not collected")
        pin = n.get("base_version_pinning", "")
        pin = (" " + first_upper(pin.split(";")[0].strip()).rstrip(".") + ".") if pin else ""
        return (value("value", "Through %s.%s" % (E(PROFILES[prov]["name"]), E(pin))) + crit
                + meta(dim_of(p, "d04")["evidence"], S.cite(p, "d04", 2)))
    ident = NAMED_BY.get(p["id"]) or vi["identifier"]
    if ident.split(" ", 1)[0] in LOWER_FIRST:
        ident = ident[:1].lower() + ident[1:]
    cond = str(vi.get("condition") or "none").strip().rstrip(".")
    if cond.lower() == "none":
        cond = "No condition."
    elif cond.lower().startswith("none "):
        cond = "No condition " + cond[5:] + "."
    else:
        cond = "Condition: " + cond + "."
    cite = ""
    srcs = vi.get("sources") or []
    if srcs:
        num = S.add(srcs[0], p["name"])
        cite = '<sup class="cite">[<a href="#src-%d" aria-label="Source %d">%d</a>]</sup>' % (num, num, num)
    return (value("value", "Named by %s. %s" % (E(ident), E(cond))) + crit
            + '<span class="cell-meta">%s%s</span>' % (badge(vi["evidence"], compact=True), cite))


def cite_all(p, S, srcs):
    nums = uniq([S.add(s, p["name"]) for s in srcs or [] if s.get("url")])
    if not nums:
        return ""
    return '<sup class="cite">[%s]</sup>' % ",".join('<a href="#src-%d" aria-label="Source %d">%d</a>' % (k, k, k) for k in nums)


def maintainers_row(p, S):
    """Rule 16: one concentration fact, from the profile field maintainers_fact."""
    f = p.get("maintainers_fact")
    if not f:
        return value("notcollected", "Not collected")
    return value("value", E(f["text"])) + meta(f.get("evidence", "DOCUMENTED"), cite_all(p, S, f.get("sources")))


MOUNTS_NOTE = ("What is read-only, what is writable but reset on reboot, what persists, and whether the adopter can change that. "
               "Data sheet only: the matrix has no Mounts column.")
MOUNTS_LINES = (("ro", "Read-only"), ("reset", "Writable, reset on reboot"), ("persist", "Writable, persistent"), ("config", "Configurable"))


def mounts_row(p, S):
    """The Mounts row of a data sheet (methodology section 9, rule 21's companion row): four lines, then the evidence badge and
    citations. It reads d02: read_only, read_only_mechanism, ephemeral, ephemeral_mechanism, writable_and_persistent and
    configurable_paths. An entry whose layout is set by its lifecycle manager (Hadron, mount_layout) says so on each line."""
    n = norm(p, "d02")
    cp = n.get("configurable_paths") or {}

    def plain(v):
        if not v:
            return ""
        if isinstance(v, str):
            return v
        return ("; " if any("," in str(x) for x in v) else ", ").join(str(x) for x in v)

    def with_mech(paths, mech):
        return E(paths) + (' <span class="v-tag">(%s)</span>' % E(mech) if mech else "")

    def to_sheet(text):
        text = E(text)
        prov = n.get("provided_by")
        if prov in PROFILES:
            name = PROFILES[prov]["name"]
            text = text.replace("%s data sheet" % E(name), '<a class="proj-open" href="#tc-%s">%s data sheet</a>' % (prov, E(name)))
        return text

    if n.get("mount_layout"):
        ro = reset = persist = to_sheet(n["mount_layout"])
    else:
        known = searched(p, "d02")   # an Unknown line invites a correction only where the profile records a search
        ro = with_mech(plain(n.get("read_only")), n.get("read_only_mechanism")) if n.get("read_only") else (not_found() if known else "Unknown")
        reset = with_mech(plain(n.get("ephemeral")), n.get("ephemeral_mechanism")) if n.get("ephemeral") else not_found()
        persist = E(plain(n.get("writable_and_persistent"))) if n.get("writable_and_persistent") else (not_found() if known else "Unknown")
    val = cp.get("value")
    how = cp.get("how", "")
    if val == "unknown" or not cp:
        cfg = not_found() if searched(p, "d02") else "Unknown"
    elif val == "no":
        cfg = "Not configurable. " + E(how)
    elif val == "via-lifecycle-manager":
        cfg = to_sheet(how) + "."
    else:
        cfg = E(how)
    if cp.get("evidence") == "INFERRED":
        cfg += ' <span class="v-tag">(inferred)</span>'
    can_off = n.get("immutability_can_be_disabled")
    if can_off not in (None, False, "unknown") and n.get("immutability_disable_where"):
        cfg += " Immutability can be switched off at %s." % E(n["immutability_disable_where"])
    lines = "".join('<li class="m-line" data-line="%s"><span class="m-k">%s</span> %s</li>' % (k, E(lab), txt)
                    for (k, lab), txt in zip(MOUNTS_LINES, (ro, reset, persist, cfg)))
    ev = dim_of(p, "d02")["evidence"]   # a configurable line that is inferred or unknown says so in its own words
    cite = cite_all(p, S, (n.get("mounts_sources") or []) + (cp.get("sources") or []))
    return '<ul class="v v-list m-lines">%s</ul>' % lines + '<span class="cell-meta">%s%s</span>' % (badge(ev, compact=True), cite)


def data_sheet(p, S):
    """One entry's data sheet: every matrix column in full, in matrix order, then the version identity and the
    maintainers fact. Nothing here ranks or judges. tradeoffs.buys, tradeoffs.costs and known_issues are not shown."""
    group = ", ".join(p["entry_kind"])
    v = p["version_observed"]
    m = META.get(p["id"], {})
    own = ""
    if m.get("owner"):
        tag = ('<span class="otag"><span>%s</span><span>%s</span></span>' % (E(m["tag"][0]), E(m["tag"][1]))) if m.get("tag") else ""
        own = '<p class="tc-own">%s %s</p>' % (E(m["owner"]), tag)
    labels = [("website", "Website"), ("docs", "Docs"), ("source", "Source"), ("cncf", "CNCF")]
    links = " ".join('<a href="%s">%s</a>' % (E(m["links"][k]), lab) for k, lab in labels if m.get("links", {}).get(k))
    links += ' <a href="https://github.com/cloudnativeos-org/pulse/blob/main/data/projects/%s.yaml">Profile</a>' % p["id"]
    head = ('<article class="tc" aria-labelledby="tc-{id}"><div class="tc-head"><div><span class="eyebrow">{group}</span>'
            '<h3 id="tc-{id}">{name}</h3>{own}</div><div class="tc-side"><nav class="tc-links" aria-label="Project links">{links}</nav>'
            '<span class="muted tc-ver"><span class="mono">{ver}</span> · collected {date}</span></div></div>').format(
        id=p["id"], group=E(group), name=E(p["name"]), own=own, links=links, ver=E(str(v["version"])), date=fmt_date(p["collected_at"]))
    rows = []
    for (k, h, _, _, _), c in zip(COLUMNS, cells_of(p, S)):
        rows.append('<div class="ds-row" id="ds-%s-%s" data-col="%s"><dt>%s <a class="mx-q" href="#col-%s" aria-label="What %s means" title="What %s means">?</a></dt><dd>%s</dd></div>'
                    % (p["id"], k, k, E(h), k, E(h), E(h), invite(p, k, c.detail)))
        if k == "update":   # the Mounts row sits right after Update unit; it is not a matrix column
            rows.append('<div class="ds-row" id="ds-%s-mounts" data-col="mounts"><dt>Mounts <a class="mx-q" href="#col-mounts" aria-label="What Mounts means" title="What Mounts means">?</a></dt><dd>%s</dd></div>'
                        % (p["id"], mounts_row(p, S)))
    for k, h, html_ in (("version", "What names the OS version", version_identity(p, S)),
                        ("maintainers", "Maintainers", maintainers_row(p, S))):
        rows.append('<div class="ds-row" id="ds-%s-%s" data-col="%s"><dt>%s</dt><dd>%s</dd></div>' % (p["id"], k, k, E(h), html_))
    body = ('<dl class="ds-rows">%s</dl>'
            '<div class="tc-foot"><span>Every value as the matrix records it, with its evidence label and sources. '
            'For open bugs and advisories, see the project\'s own issue tracker.</span></div></article>'
            % "".join(rows))
    return head + body


def pair(P, S):
    a, b = P["flatcar"], P["bottlerocket"]
    na, nb = norm(a, "d05"), norm(b, "d05")
    ev = lambda p, d: badge(dim_of(p, d)["evidence"], compact=True)
    return (
        '<article class="pair" aria-labelledby="pair-1"><div class="pair-head"><span class="eyebrow">Looks alike, differs on</span>'
        '<h3 id="pair-1">Both switch A/B partitions. They differ on what an update replaces, so on what a rollback undoes.</h3></div>'
        '<div class="pair-grid">'
        '<div class="rl colh empty"></div><div class="colh">%s</div><div class="colh">%s</div>'
        '<div class="rl">Shared</div><div class="same">An update is written to the inactive partition set, then the boot target flips %s%s. '
        'If the new version is not marked good, the bootloader reverts by itself %s%s. Two versions are kept on disk (%s and %s). %s</div>'
        '<div class="rl diff-row diff-label">Differs on: what an update writes</div>'
        '<div class="side diff-row" data-p="%s">Only <code>/usr</code>, on its own partition under dm-verity. The root filesystem holding <code>/etc</code>, <code>/opt</code> and <code>/var</code> is writable and persists. %s %s</div>'
        '<div class="side diff-row" data-p="%s">The whole root filesystem, a read-only dm-verity device. <code>/etc</code> is a tmpfs; persistent state lives on a separate data volume at <code>/local</code>. %s %s</div>'
        '<div class="rl">So a rollback undoes</div>'
        '<div class="side" data-p="%s">The <code>/usr</code> partition. A bad configuration change on the writable root survives an OS rollback. %s</div>'
        '<div class="side" data-p="%s">The root image. Settings sit in an API datastore and are migrated through updates, so they are not part of the image that rolls back. %s</div>'
        '</div><div class="pair-foot">Neither design is ranked. A smaller unit of reversibility keeps local state; a whole-image unit keeps less drift. '
        'Read the matrix column <a href="#matrix?col=update">Update unit</a> for every entry.</div></article>'
        % (sheet_link(a), sheet_link(b),
           S.cite(a, "d04"), S.cite(b, "d04"), S.cite(a, "d05"), S.cite(b, "d05"),
           E(str(na.get("retained_versions"))), E(str(nb.get("retained_versions"))), ev(a, "d05"),
           E(a["name"]), S.cite(a, "d02", 2), ev(a, "d02"), E(b["name"]), S.cite(b, "d02", 2), ev(b, "d02"),
           E(a["name"]), S.cite(a, "d05"), E(b["name"]), S.cite(b, "d02")))


START_HERE = [
    ("When a machine boots a bad update with nobody on site, does it undo the update by itself?",
     [("Matrix", "#matrix?rollback=yes", "filter: Automatic rollback, Yes")]),
    ("What does that undo revert: the whole OS image, or only part of it?",
     [("Matrix", "#matrix?col=update", "column: Update unit")]),
    ("Can the update source live on your own network?",
     [("Matrix", "#matrix?selfhost=yes", "filter: Self-hostable update source")]),
    ("Which of your board architectures have released images, not only build tooling?",
     [("Matrix", "#matrix?arch=arm64", "filter: Architecture, arm64")]),
    ("How does a new machine get its first configuration with no one at the keyboard?",
     [("Matrix", "#matrix?day0=pxe", "filter: Day-0 path, PXE")]),
    ("Can you recover a machine that has no network?",
     []),
]


def start_here():
    lis = []
    for q, links in START_HERE:
        to = "".join('<span><span class="kind">%s</span> <a href="%s">%s</a></span>' % (k, h, E(t)) for k, h, t in links)
        if not links:
            to = '<span class="to-none">Not in the matrix yet</span>'
        lis.append('<li><span class="q">%s</span><span class="to">%s</span></li>' % (E(q), to))
    return ('<section class="sh" aria-labelledby="sh-edge"><div class="sh-head"><span class="eyebrow">Use case</span>'
            '<h3 id="sh-edge">If you run machines at many remote sites over weak links</h3></div><ol>%s</ol></section>'
            % "".join(lis))


def context_box(P, S):
    items = []
    for pid in sorted(CONTEXT, key=lambda x: P[x]["name"].lower()):
        p = P[pid]
        note = p["category_fit"]["note"].split("\n")[0]
        sents = re.split(r"(?<=\.)\s", note)
        txt = " ".join(sents[:2])
        hidden = ""
        items.append('<dt%s>%s<span class="tag">%s · fit: %s</span></dt><dd%s>%s %s</dd>'
                     % (hidden, E(p["name"]), E(", ".join(p["entry_kind"])), E(p["category_fit"]["comparable"]), hidden, E(txt), S.cite(p, "d01")))
    return ('<aside class="ctx" aria-label="Alternative paradigms"><div class="ctx-head">'
            '<p>These entries are profiled on the same fourteen dimensions. They reach for the same goals by a different route, '
            'so a matrix row would be mostly cells that do not apply. Each profile says so in its own category note.</p></div>'
            '<dl>%s</dl></aside>' % "".join(items))


# Projects with public work in this space but nothing released to profile yet. Not in the dataset.
WORTH_MENTIONING = [
    ("Amutable", "company, no released OS image found",
     "A company building verifiable integrity into Linux systems. Its blog describes the upstream work behind it. "
     "No released OS image to profile as of 5 Oct 2026.",
     [("Amutable blog", "https://amutable.com/blog")]),
]


def worth_mentioning():
    items = []
    for name, kind, txt, links in WORTH_MENTIONING:
        refs = ", ".join('<a href="%s">%s</a>' % (E(u), E(t)) for t, u in links)
        items.append('<dt>%s<span class="tag">%s</span></dt><dd>%s <span class="t-meta">%s</span></dd>' % (E(name), E(kind), E(txt), refs))
    return ('<aside class="ctx" aria-label="Worth mentioning"><div class="ctx-head">'
            '<p>Not profiled. Public work that points at the same problems, with nothing released yet that the dimensions could be checked against.</p></div>'
            '<dl>%s</dl></aside>' % "".join(items))


# Projects that were looked at and left out, with the reason. They are released, so they are not "worth mentioning".
EXCLUDED = [
    ("balenaOS", "excluded: does not meet R5",
     "balenaOS is a Yocto-built host OS for running containers on embedded devices. It has a read-only root filesystem and A/B root partitions, "
     "and a failed update boots back into the previous OS version. Its container engine is balenaEngine, based on Moby. "
     "balena documents no Kubernetes support, so it does not meet R5.",
     [("OS overview", "https://docs.balena.io/reference/OS/overview/2.x/"), ("OS updates", "https://docs.balena.io/reference/OS/updates/self-service/"),
      ("balenaEngine", "https://github.com/balena-os/balena-engine"), ("balenaOS product page, no Kubernetes mention", "https://www.balena.io/os")]),
]


def excluded():
    items = []
    for name, kind, txt, links in EXCLUDED:
        refs = ", ".join('<a href="%s">%s</a>' % (E(u), E(t)) for t, u in links)
        items.append('<dt>%s<span class="tag">%s</span></dt><dd>%s <span class="t-meta">Sources, retrieved 12 Oct 2026: %s.</span></dd>' % (E(name), E(kind), E(txt), refs))
    return ('<aside class="ctx" aria-label="Considered and excluded"><div class="ctx-head">'
            '<p>Not profiled. Released, and looked at, but it fails one of the five inclusion criteria. The reason is stated with each project.</p></div>'
            '<dl>%s</dl></aside>' % "".join(items))


def what_is():
    g = lambda term, anchor: '<a href="#g-%s">%s</a>' % (anchor, term)
    rows = [("Updates", g("In place", "in-place-upgrade"), g("Atomic", "atomic-upgrade")),
            ("What a version names", "A release, such as 24.04. Each node's real content is its own set of package versions",
             "The whole OS: one " + g("version", "version") + ", the same on every node"),
            ("The running system", "Writable", g("Immutable", "immutable") + '<a href="#cmp-note" aria-label="See note">*</a>'),
            ("Undoing an update", "Downgrade packages, boot a previous filesystem " + g("snapshot", "snapshot") + ", or rebuild the node",
             g("Roll back", "rollback") + ": boot into a previous version"),
            ("First install", "An installer, or an automated install", "A versioned " + g("image", "image-based")),
            ("Configuration", "Applied on top and changed over time, so nodes can " + g("drift", "drift") + " apart",
             g("Declared", "declarative-provisioning") + ", applied at first boot, and on some systems re-applied later"),
            ("Main job", "Anything", "Running cloud native workloads")]
    table = ('<table class="cmp"><thead><tr><th scope="col"></th><th scope="col">%s</th><th scope="col">%s</th></tr></thead><tbody>%s</tbody></table>'
             '<p class="t-meta" id="cmp-note">* Only part of the OS is read-only, and which part varies by system. See %s in the glossary.</p>'
             % (g("General-purpose OS", "general-purpose-os"), g("Cloud native OS", "cloud-native-os"),
                "".join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % r for r in rows), g("Immutable", "immutable")))
    rules = [("Versioned whole-system updates", "One version names the whole OS, and the OS updates as that one unit, never package by package on a running node. It is enough that the project documents a way to run it like this."),
             ("Immutable at runtime", "The OS part, the root or <code>/usr</code>, is read-only on a running node."),
             ("Rollback", "At least one previous OS version is kept and can be booted."),
             ("Declarative provisioning", "A node configures itself at first boot from a declarative input, with no interactive install."),
    ('Ignition', 'A provisioning tool that runs once, in the initramfs at first boot. It reads a JSON configuration and can partition disks, format filesystems, write files and create users before the root filesystem is in use.'),
             ("Runs Kubernetes", "The project, or its vendor, documents running Kubernetes on it: bundled, installed on it, or as the node OS of a Kubernetes service. "
              "A framework such as Kairos or bootc meets this rule through the images built with it. Running containers alone is not enough.")]
    return ('<div class="prose">'
            '<p class="t-meta">New to these terms? The <a href="#h-gloss">glossary</a> defines each one.</p>'
            '<h3 id="w-mismatch">The mismatch</h3>'
            '<p>A general-purpose operating system, such as Ubuntu, Debian, Fedora, Red Hat Enterprise Linux or SUSE Linux Enterprise Server, is built to do anything. You install it once and then groom it for its entire lifespan: '
            'you add packages, edit configuration files and upgrade it piece by piece on the running machine.</p>'
            '<p>Cloud native pushes applications toward the twelve-factor model: stateless, disposable, easy to scale and to replace. Yet a lot of cloud native infrastructure still runs on a general-purpose OS. Two of the three big managed Kubernetes services default to one: <a href="https://learn.microsoft.com/en-us/azure/aks/create-node-pools">AKS to Ubuntu</a>, and <a href="https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html">EKS managed node groups to Amazon Linux 2023</a>. That is a mismatch. We like to think the machines under our applications are cattle, because we configure them automatically. The truth is that they are automated pets, each one still groomed on its own.</p>'
            '<p>Configuration management tools such as Ansible, Puppet or Chef help, but automation alone cannot fix the root problem. They describe changes to apply to a machine, '
            'not the whole state of the machine. Anything they do not manage still changes it, from a package someone installed by hand to a dependency that moved upstream. '
            'So two nodes set up from the same playbook a month apart can end up different, and the difference grows with every change. That is drift. '
            'There is also no single version of the OS that you can provision again on day 0, when a node is first set up, or roll back to.</p>'
            '</div><h3 id="w-approach">A different approach</h3><div class="prose"><p>A cloud native operating system takes a different approach. It is built for one job: running cloud native workloads on machines you manage as a fleet. '
            'It treats the OS the way container images treat an application. The whole OS is one versioned artifact. Every node is provisioned from the same version, '
            'a new version replaces the old one instead of changing it in place, and the previous version is still there if the new one fails.</p></div>'
            + '<p class="cmp-lead">Side by side:</p>' + table +
            '<h3 id="w-criteria">The five inclusion criteria</h3>'
            '<div class="prose"><p>Most rows of that table are also a test. An OS is in the matrix when it meets all five inclusion criteria:</p><ol class="rules">%s</ol>'
            '<p>__MATRIX_LIST__</p>'
            '<p>A general-purpose OS can be made to work this way. With enough configuration, and tooling built around it, you can produce images, update them atomically, keep the OS read-only, roll back and provision declaratively. Many teams do. The Pulse does not say that is the wrong choice. It lists the projects built to meet the five criteria by design, so you do not have to configure the OS yourself or build that tooling to get there.</p>'
            '<p>Openness is not a criterion. A closed or single-vendor OS that meets the five criteria is in, and the matrix shows its governance next to every other entry.</p>'
            '<p>Some projects sit beside the matrix. <a href="#h-alt">Alternative paradigms</a> aim at the same goal and do not meet the first four rules as the project ships them: NixOS, Unikraft and the Yocto Project. '
            '<a href="#h-worth">Worth mentioning</a> lists public work with nothing released to profile yet. <a href="#h-excluded">Considered and excluded</a> names released projects that fail a criterion, with the reason. Conventional mutable distributions are out, '
            'even when they are a common Kubernetes node OS like the defaults on AKS and EKS, because they fail the first two rules. '
            'The <a href="https://github.com/cloudnativeos-org/pulse/blob/main/docs/methodology.md">methodology</a> gives the full reasoning, and the source for how each entry meets the Kubernetes rule.</p></div>'
            % "".join("<li><b>%s.</b> %s</li>" % r for r in rules))


GLOSSARY = [
    ("General-purpose OS", "An operating system built to run anything, such as Ubuntu, Debian or Fedora. It is installed once and then maintained by changing it in place for the rest of its life."),
    ("Cloud native OS", "In the Pulse, an OS that meets the five inclusion criteria: versioned whole-system updates, read-only OS files at runtime, rollback, declarative provisioning, and documented Kubernetes use."),
    ("In-place upgrade", "An upgrade that changes the running system piece by piece, for example package by package. The result depends on the state the machine was in before."),
    ("Atomic upgrade", "An upgrade that applies the new version as a whole or not at all. If it fails, the old version is still intact."),
    ("Image-based", "The OS is built ahead of time as one complete image, and that image is what gets installed and updated."),
    ('OCI image', 'A container image in the format the Open Container Initiative specifies. It is stored in a container registry and pulled from it. Some projects ship the OS itself as an OCI image.'),
    ('OSTree', 'A system for storing and deploying complete, versioned filesystem trees of an OS. Each deployment is one tree, and the bootloader chooses which deployment boots.'),
    ('composefs', 'A Linux mechanism that mounts a read-only filesystem image whose file contents sit in a shared, content-addressed store. With fs-verity, the kernel can check that the contents match what the image records.'),
    ("A/B partitions", "Two copies of the OS on disk. An update writes the copy that is not running, and the machine switches to it at the next boot."),
    ("Version", "One build of the OS, identical on every machine that runs it."),
    ("Snapshot", "A point-in-time copy of a filesystem on one machine, for example with btrfs. It captures that machine's state, so it is unique to that machine. A version is the same everywhere; a snapshot is not."),
    ("Rollback", "Going back to an earlier OS state after an update. An automatic rollback happens without a person, when the new version fails a check at boot."),
    ("Immutable", "Part of the OS is read-only on a running machine, and changes to that part arrive only through an update. Which part varies by system: the whole root filesystem on some, only <code>/usr</code> on others, and some keep <code>/etc</code> or a data volume writable. Writable does not always mean persistent: some paths are writable through a temporary overlay or an in-memory filesystem, and changes there are lost at the next boot. The matrix shows what each entry protects."),
    ("Drift", "Machines that should be the same become different over time, through changes that were not planned or not recorded."),
    ("Day 0, day 2", "Day 0 is when a node is first set up. Day 2 is everything after that: upgrades, fixes, changes, decommissioning."),
    ("Declarative provisioning", "You describe the state a machine should have, and the machine sets itself up to match it at first boot, with no interactive install."),
    ("Configuration management", "Tools such as Ansible, Puppet or Chef that apply changes to machines to bring them toward a described state."),
    ('Cluster API', 'A Kubernetes project that creates, upgrades and deletes Kubernetes clusters through declarative Kubernetes resources. Providers adapt it to an infrastructure, a bootstrap method or a control plane.'),
    ('One-shot run', 'A fleet upgrade that runs once when someone or something triggers it, and then stops. A node that joins later, or changes afterwards, stays where it is until the next run.'),
    ('Reconciled in place', 'A controller keeps comparing the declared OS version with each node, and upgrades the existing node whenever the two differ.'),
    ('Reconciled by replacement', 'A controller keeps comparing the declared OS version with each node, and replaces a node that differs with a new node built from the declared version.'),
    ("Pets and cattle", "Pets are machines cared for one by one. Cattle are machines that are interchangeable and replaced rather than repaired."),
    ("Twelve-factor app", "A set of practices for building applications that are stateless, disposable and easy to scale. See <a href=\"https://12factor.net/\">12factor.net</a>."),
    ("Boot trust chain", "How far trust reaches when a machine starts. With no Secure Boot, nothing is checked. With Secure Boot, the firmware checks the first boot component. With measured boot, each stage records what it loaded in the TPM. The chain reaches the running system only when the final root filesystem is covered by what was signed: either the whole OS is inside the signed image, or the root hash sits in a signed boot artifact. The matrix column numbers these steps from level 0 (nothing checked) to level 3 (running root covered)."),
    ("Secure Boot", "A UEFI firmware feature: before running the first boot component, the firmware checks its signature against keys stored in the firmware."),
    ("Measured boot", "Each boot stage records a hash of what it loads into the TPM. The record can be used to release a secret only to a known boot state, or to prove that state to someone else."),
    ("TPM", "Trusted Platform Module: a chip, or a virtual one in a cloud VM, that holds the boot measurements and can keep keys sealed to them."),
    ("Remote attestation", "A report of a machine's boot measurements, signed by its TPM and checked by another system before it trusts the machine."),
    ("UKI", "Unified Kernel Image: the kernel, its initrd and its command line in one signed boot file. See the <a href=\"https://uapi-group.org/specifications/specs/unified_kernel_image/\">UAPI Group specification</a>. After early boot, the system usually pivots to a root filesystem outside the UKI."),
    ("Pivot", "The point where early boot hands over from the initrd to the real root filesystem (switch_root). If that root filesystem is not covered by what was signed and measured, the chain of trust stops at the pivot."),
    ("USI", "Unified System Image: \"full OS images packed in a UKI\", in <a href=\"https://0pointer.net/blog/a-re-introduction-to-mkosi-a-tool-for-generating-os-images.html\">Daan De Meyer's words</a>. The whole OS is inside the signed image, so there is no separate root filesystem to pivot to."),
    ("dm-verity", "A Linux kernel feature that checks every block of a read-only filesystem against a hash tree. When the root hash is part of the signed and measured boot image, the chain of trust extends to that filesystem."),
    ('TUF', 'The Update Framework: a specification for securing software update systems. Signed metadata, split across several roles that each have their own keys, tells a client which files are current and what their hashes must be. See <a href="https://theupdateframework.io/">theupdateframework.io</a>.'),
    ('SBOM', 'Software Bill of Materials: a machine-readable list of the components, and their versions, in a piece of software. Common formats are SPDX and CycloneDX.'),
    ('FIPS', 'Federal Information Processing Standards, published by the US government. Here it means FIPS 140, which sets requirements for cryptographic modules. A FIPS build uses cryptographic modules validated against it.'),
    ('LTS', 'Long-term support: a release line that gets fixes for a longer, stated period than regular releases.'),
    ("Framework or mechanism", "A tool that builds or manages OS images rather than being one OS itself, such as <a class=\"proj-open\" href=\"#tc-kairos\">Kairos</a> or <a class=\"proj-open\" href=\"#tc-bootc\">bootc</a>. It meets the Kubernetes rule through the images built with it."),
    ('System extension (sysext)', 'A systemd feature that overlays extra files onto <code>/usr</code> and <code>/opt</code> from a separate image, without changing the base image. It adds software to an OS whose <code>/usr</code> is read-only.'),
    ("Evidence label", "How each claim in the Pulse is backed. " + " ".join("%s: %s" % (EVIDENCE[k][1], EVIDENCE_MEANING[k]) for k in EVIDENCE_SHOWN)),
    ("Entry kind", "What sort of object an entry is. An entry can carry more than one. " + " ".join("<code>%s</code>: %s." % (k, t) for k, t in ENTRY_KIND)),
]


def glossary():
    return '<dl class="gloss">%s</dl>' % "".join('<div><dt id="g-%s">%s</dt><dd>%s</dd></div>' % (
        re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-"), E(term), text) for term, text in GLOSSARY)


MISCONCEPTIONS = [
    ("Immutable means the whole system is read-only.",
     "Only part of the OS is read-only: the whole root filesystem on some systems, only <code>/usr</code> on others. "
     "Data and some configuration stay writable, and some of that is writable only until the next boot, through an overlay or an in-memory filesystem. "
     "A system that was read-only everywhere could not store data or run workloads. "
     "The <a href=\"#g-immutable\">glossary</a> has the details, and the matrix's <a href=\"#matrix?col=update\">Update unit</a> column shows what one update replaces on each entry."),
    ("API-only access means a smaller attack surface.",
     "An API is an attack surface too, just like SSH. What API-only access gives you is a bound and a record: you can only change what the API exposes, "
     "unless the API allows arbitrary execution, and API calls are easier to log than shell sessions. "
     "A shell is more flexible and works with familiar tooling. Neither is more secure by default. "
     "The matrix's <a href=\"#matrix?col=access\">Node access</a> column shows which each entry offers."),
    ("A rollback undoes everything.",
     "A rollback restores the part of the system the update replaced, and that part differs by design. "
     "Flatcar's A/B update covers <code>/usr</code>, so a bad change to <code>/etc</code> survives a rollback. "
     "Bottlerocket keeps settings in an API datastore outside the image, so they are not part of what rolls back. "
     "The <a href=\"#pair-1\">Flatcar and Bottlerocket pair</a> walks through it, and the <a href=\"#matrix?col=update\">Update unit</a> column shows it for every entry."),
    ("Atomic updates mean no downtime.",
     "Atomic means all or nothing: the new version applies as a whole, or the old one stays. It does not mean zero downtime. "
     "On most entries the new version takes effect at the next reboot, so the node goes down briefly. "
     "Keeping workloads running is a cluster-level job: draining nodes and rolling the update through the fleet."),
    ("A signed update means a trusted running system.",
     "A signature on an update protects the download. It does not stop a machine from booting a disk that was changed afterwards. "
     "That is the job of the <a href=\"#g-boot-trust-chain\">boot trust chain</a>: Secure Boot checks the first boot component, measured boot records each stage, "
     "and the chain covers the running system only when the final root filesystem is part of what was signed and measured, "
     "either because the whole OS is in the image (a <a href=\"#g-usi\">USI</a>) or because the root filesystem's <a href=\"#g-dm-verity\">dm-verity</a> hash is."),
    ("An immutable OS cannot be customized.",
     "It is customized differently: you change the image, not the running system. "
     "Some entries add software through system extensions, some let you build your own image from a base you choose, "
     "and some allow layering packages on top, which their own docs may discourage. "
     "The matrix's <a href=\"#matrix?col=addsw\">Adding software to the OS</a> and <a href=\"#matrix?col=byod\">Bring your own distro</a> columns and each project's data sheet show what each one allows."),
    ("Elemental and openSUSE MicroOS are the same thing.",
     "They are two projects with different jobs. <a href=\"https://elemental.docs.rancher.com/\">Elemental</a> is Rancher's OS management stack: a toolkit and an operator "
     "that build and maintain node operating systems from container images, and let Rancher Manager manage them. "
     "Its documentation describes the stack as &ldquo;a handful of packages on top of SLE Micro&rdquo;. "
     "<a href=\"https://microos.opensuse.org/\">openSUSE MicroOS</a> is a distribution, described as &ldquo;Micro Service OS built by the openSUSE community&rdquo;. "
     "The Pulse has a data sheet for <a class=\"proj-open\" href=\"#tc-microos\">openSUSE MicroOS</a>. Elemental is not an entry."),
    ("Fedora CoreOS and bootc are the same thing.",
     "Today they are not. Fedora CoreOS fetches its updates as an OCI image, but it applies them on disk as an OSTree deployment through rpm-ostree. "
     "The Fedora <a href=\"https://fedoraproject.org/wiki/Changes/CoreOSOstree2OCIUpdates\">change proposal</a> says it keeps using rpm-ostree &ldquo;and not yet bootc&rdquo;. "
     "Fedora bootc is a set of base images that you derive from. "
     "<a href=\"https://docs.fedoraproject.org/en-US/bootc/fedora-coreos/\">Fedora's own comparison</a> says Fedora CoreOS &ldquo;generally emphasizes users configuring an image pre-built by Fedora&rdquo;, "
     "while Fedora bootc &ldquo;emphasizes users deriving from our container base image&rdquo;. "
     "Fedora has started a <a href=\"https://github.com/coreos/fedora-coreos-tracker/issues/2214\">working group</a> to bring the two together, with Fedora 46 as the goal, and it is still working out the technical direction. "
     "The upstream bootc project is separate and stays independent of any one distribution. "
     "See the <a class=\"proj-open\" href=\"#tc-fedora-coreos\">Fedora CoreOS</a> and <a class=\"proj-open\" href=\"#tc-bootc\">bootc</a> data sheets."),
]


def misconceptions():
    return '<dl class="myths">%s</dl>' % "".join(
        '<div><dt><span class="myth-label">Misconception</span>%s</dt><dd><span class="myth-label">In fact</span>%s</dd></div>' % (E(m), f)
        for m, f in MISCONCEPTIONS)


def who():
    return ('<div class="prose">'
            '<p>I am <a href="https://mauromorales.com/">Mauro Morales</a>, the person behind the Cloud Native OS Pulse. '
            'I work as a Staff Engineer at <a href="https://www.spectrocloud.com/">Spectro Cloud</a>, and I am one of the maintainers of '
            '<a href="https://kairos.io/">Kairos</a> and <a href="https://hadron-linux.io/">Hadron</a>, two of the entries. '
            'I have also done quite a lot of <a href="https://mauromorales.com/public-speaking">public speaking</a> promoting these projects. '
            'So I cannot claim to be completely unbiased.</p>'
            '<p>I put this project together wearing my <a href="https://www.cncf.io/people/ambassadors/?p=mauro-morales">CNCF Ambassador</a> hat. '
            'To keep my bias in check, I tried to guide the agents toward a fair design by putting these sentences in the prompt:</p>'
            '<blockquote>Do not construct criteria specifically to make Kairos look good.</blockquote>'
            '<blockquote>If the comparison appears overwhelmingly favorable to Kairos, challenge the methodology before publishing it.</blockquote>'
            '<p>A prompt is not a guarantee, so the controls are in the method: a dated source and an evidence label on every claim, '
            'a separate fact-check per profile, maintainers who will be invited to check their own profile, and fixes open to anyone. '
            '<a href="#h-made">How it was made</a> describes each step. None of this removes my bias. It makes it easier for you to find.</p>'
            '</div>')


def coi():
    """Kept for the design-system harness: the stake is now the Who made the Pulse section."""
    return who()


def fix_callout():
    forms = "https://github.com/cloudnativeos-org/pulse/issues/new?template="
    return ('<aside class="fix" aria-labelledby="fix-h"><span class="fix-mark" aria-hidden="true">?</span><div><h3 id="fix-h">Found a mistake, or something missing?</h3>'
            '<p class="muted" style="margin:0">The Pulse is open to fixes and to proposals. Everything goes through the repository.</p><ol>'
            '<li><b>A claim is wrong or out of date.</b> Open a pull request against that project\'s YAML profile in <a href="https://github.com/cloudnativeos-org/pulse">the Pulse repository</a>, '
            'with the primary source for the correct value, or <a href="%scorrection.yml">open a correction</a>. Every correction goes into the profile\'s <code>corrections</code> list, with the date and the source.</li>'
            '<li><b>An OS is missing.</b> If it meets <a href="#w-criteria">the five inclusion criteria</a>, <a href="%snew-entry.yml">propose it</a>, with a source for each criterion.</li>'
            '<li><b>A rule is wrong or missing.</b> <a href="%scriteria.yml">Propose a change to the criteria</a>, and say which entries it would add or remove.</li>'
            '</ol></div></aside>' % (forms, forms, forms))


WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen".split()


def word(n, cap=False):
    w = WORDS[n] if n < len(WORDS) else str(n)
    return w.capitalize() if cap else w


def profiles_line(P):
    """How many profiles, what they are, and when each was collected, from the data."""
    side = sorted((P[i]["name"] for i in P if i not in CORE), key=str.lower)
    by_date = {}
    for p in P.values():
        by_date.setdefault(str(p["collected_at"]), []).append(p)
    parts = []
    for d in sorted(by_date):
        ps = by_date[d]
        when = dt.date.fromisoformat(d).strftime("%-d %B")
        if len(ps) > 3:
            parts.append("%s on %s" % (word(len(ps)), when))
        else:
            names = sorted((p["name"] for p in ps), key=str.lower)
            parts.append("%s on %s" % (" and ".join(names) if len(names) < 3 else ", ".join(names[:-1]) + " and " + names[-1], when))
    coll = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + ", and " + parts[-1]
    return ("%s profiles from primary sources: %s in the matrix, plus %s. Collected: %s."
            % (word(len(P), True), word(len([i for i in CORE if i in P])), ", ".join(side[:-1]) + " and " + side[-1], coll))


def made(P):
    ncorr = sum(len(p.get("corrections") or []) for p in P.values())
    nk = len(P["kairos"].get("corrections") or [])
    coll, newest = data_dates(P)
    coll_span = coll[0] if coll[0] == coll[-1] else "%s to %s" % (coll[0], coll[-1])
    steps = [
        ("Method first.", "I told the agent to challenge this project list and taxonomy before any research. It did. One label per project mixed three separate questions, so the Pulse uses three axes. Fedora CoreOS and bootc got separate profiles, because a distribution and a mechanism are not peers. The agent also found that my list left out openSUSE MicroOS and Ubuntu Core. Both compete directly with Kairos, so the gap flattered Kairos. I had them added."),
        ("Schema and validator.", "Fourteen dimensions, closed vocabularies, one evidence label per dimension, and a dated source for every documented claim. The validator rejects a profile that claims an absence without a source, infers without naming its evidence, marks something unknown without saying where it looked, lists no costs for a design, or carries a score or rank field."),
        ("Profiles.", profiles_line(P) + " Marketing comparison pages were not accepted as a source for anything."),
        ("Re-verification.", "On 22 September the agents re-read every cited source and checked every quote against the live page. Each profile got its own fact-check pass, which also asked whether it was treated more softly or more harshly than Kairos. Hadron was added. My brief called Hadron an immutable OS positioned like Flatcar. Its own documentation says otherwise, so the profile says otherwise."),
        ("Rollback deep dives.", "Six systems (Kairos, bootc, Fedora CoreOS, Flatcar, Bottlerocket, NixOS) were booted in VMs, moved to a second version and rolled back, to see what state survives. Where a step was not run as a real upgrade, the deep dive says INFERRED or NOT TESTED."),
        ("Second review.", "On 5 October three independent fact-check agents re-read the claims against the live sources, split by project, and another agent reviewed whether these are the right comparison points. Six claims about other projects were corrected (see <a href='#m-wrong'>What went wrong</a>). Base Azure Linux left the dataset, because it is not immutable, and Azure Container Linux replaced it. Corrections now total %d, %d of them on Kairos." % (ncorr, nk)),
        ("Maintainer review.", "Not done yet. Each project will get its profile and its open questions, with one ask: check the facts. It is not a request to endorse the analysis."),
    ]
    return ('<div class="made"><aside class="made-rail"><dl>'
            '<div><dt>Collected</dt><dd><span class="mono">%s</span></dd></div>'
            '<div><dt>Re-verified</dt><dd><span class="mono">%s</span></dd></div>'
            '<div><dt>Newest source read</dt><dd><span class="mono">%s</span></dd></div>'
            '<div><dt>Profiles</dt><dd>%d, schema <span class="mono">1.0.0</span></dd></div>'
            '<div><dt>Corrections</dt><dd>%d, each dated with its source</dd></div>'
            '<div><dt>Deep dives</dt><dd>6 rollback experiments</dd></div>'
            '<div><dt>Maintainer review</dt><dd>Not done yet</dd></div></dl></aside>'
            '<div><div class="prose"><p>AI agents did most of the reading, the bookkeeping and the first drafts of this Pulse. You do not have to trust them, or me. '
            'Every documented claim names its source, with the date it was read and a label that says how strong the evidence is. Check any claim against its source. '
            'If it does not hold, the Pulse is wrong, and I want to know.</p>'
            '<p>That is my case for using AI here. The Pulse is not opinion. It records what each project\'s own docs, code, release notes and announcements say. Machines read and cite well. They also get things wrong.</p></div>'
            '<h3>My role</h3><div class="prose"><p>I drove the Pulse. I did not validate every claim myself. I read each profile with my own Kairos experience and questioned what did not make sense. '
            'For the rest I relied on independent agent reviewers and fact-checkers. I do not own each project\'s results. The sources do, and so do the people who know those projects better than I do.</p></div>'
            '<h3>The process</h3><ol class="steps">%s</ol>'
            '<h3>Tools and models</h3><div class="prose"><p>The agents were Anthropic\'s Claude models, running in Claude Code. Each task had a written brief, its own agent session, '
            'its own branch and its own pull request. I merged every change. For this first version, Anthropic provided the model access, through its Claude for Open Source program. Anthropic had no say in the content.</p>'
            '<p>Claude Opus 5 wrote the method, the first ten profiles and the first article draft. Claude Sonnet 5 did the rest: the two added profiles, the re-verification, Hadron and the rollback experiments. '
            'Two of those briefs asked for a stronger model than the one that ran. The rollback experiments and the re-verification both ran on Sonnet 5. '
            'Every commit names the assisting model in a <code>Co-developed-by:</code> trailer, and the full history is public in <a href="https://github.com/cloudnativeos-org/pulse">the Pulse repository</a>. Commits from the <code>mauro-agent</code> account were made by an AI agent that I operate. I am the person behind that account and I answer for its work. '
            'The task briefs are kept. The exact prompts each session received are not, and neither is which model ran each fact-check pass.</p></div>'
            '<h3 id="m-wrong">What went wrong</h3><div class="prose"><ul>'
            '<li>An early summary overstated a Secure Boot finding about Kairos. It mixed up two boot paths. I caught it, and the source code settled it.</li>'
            '<li>An early pass rated Kairos rollback weaker than its peers. Part of that was a counting error: the same A/B design got different "retained versions" numbers in different profiles. The fix favoured Kairos, a project I help maintain. So I want it on the record that the code and the docs decided it, not me. Both are cited.</li>'
            '<li>Some absence claims about other projects rested only on missing documentation. They were downgraded to unknown. One claim was simply wrong: Unikraft does have a governance document and maintainer lists.</li>'
            '<li>The second review found six claims about other projects that were wrong in a way that made them look worse. They were fixed before publication.</li>'
            '</ul></div></div></div>'
            % (coll_span, REREAD, newest, len(P), ncorr, "".join("<li><span><b>%s</b> %s</span></li>" % (E(h), t) for h, t in steps)))


def review(n, title, text):
    return '<p class="review"><b>Proposed change %s, %s.</b> %s</p>' % (n, E(title), text)


def review_bar():
    return ('<form class="review-bar no-print" onsubmit="return false" aria-label="Review controls"><span class="eyebrow">Review controls</span>'
            '<fieldset><legend>Notes</legend><label class="chip"><input type="checkbox" name="notes" checked><span>Show review notes</span></label></fieldset></form>')


# ---------------------------------------------------------------- tokens to css
def tokens_css(tok, selector_map=None):
    th = [t["id"] for t in tok["color"]["themes"]]
    def val(t, theme):
        v = t["value"]
        v = v if isinstance(v, str) else v.get(theme, v[th[0]])
        return re.sub(r"\{([^}]+)\}", r"var(--\1)", v)
    def block(theme):
        return "".join("--%s:%s;" % (t["name"], val(t, theme)) for t in tok["color"]["tokens"])
    other = "".join("--%s:%s;" % (t["name"], t["value"]) for fam in ("spacing", "radius") for t in tok[fam]["tokens"])
    fams = "".join("--font-%s:%s;" % (k, v) for k, v in tok["type"]["families"].items())
    return (":root{%s%s%s}"
            "@media (prefers-color-scheme: dark){:root:not([data-theme=light]){%scolor-scheme:dark}}"
            ":root[data-theme=dark]{%scolor-scheme:dark}"
            "@media print{:root,:root[data-theme=dark]{%s}}"
            "html{background:var(--paper)}body{margin:0;background:var(--paper)}"
            % (block("light"), other, fams, block("dark"), block("dark"), block("print")))


# ---------------------------------------------------------------- site
# Two pages. index.html is the matrix page: the matrix, the data sheets (a modal with JavaScript) and the sources it cites.
# guide.html is the guide: every other section. The matrix page has no contents panel, because with the data sheets
# folded into the modal it would list only two items. Contents follow the page order. A group with sub-entries gets
# an Overview link plus one link per item.
GUIDE_TOC = [("What is a cloud native OS?", ["h-what", "WHATS"]),
             ("Misconceptions", ["h-myths"]),
             ("Start from your situation", ["h-start", "STARTS"]),
             ("Is your project here?", ["h-review"]),
             ("Looks alike, differs on", ["h-pair", "PAIRS"]),
             ("Where they came from", ["h-origins"]),
             ("Beyond the matrix", ["h-alt", "h-worth", "h-excluded"]),
             ("About", ["h-who", "h-made", "h-why", "h-wishes", "h-gloss", "h-dims", "h-src"])]
TOC_GROUPS = GUIDE_TOC


def first_upper(s):
    return s[:1].upper() + s[1:]


# Shorter labels for the contents panel only. The page headings keep their full text, which the link's title carries.
TOC_SHORT = {
    "sh-edge": "Remote sites, weak links", "sh-managed": "Your cloud's node OS", "sh-capi": "Own hardware, Cluster API",
    "sh-regulated": "Regulated or air-gapped", "sh-gpu": "GPU or AI workloads", "sh-device": "A device with the OS inside",
    "sh-learn": "Homelab or learning",
}
TOC_NAME = {"Flatcar Container Linux": "Flatcar", "Azure Container Linux (ACL)": "ACL", "Container-Optimized OS": "COS",
            "openSUSE MicroOS": "MicroOS", "Talos Linux": "Talos", "Hadron Linux": "Hadron"}


def toc_link(href, full, short=None):
    short = short or full
    title = ' title="%s"' % E(full) if short != full else ""
    return '<li><a href="#%s"%s>%s</a></li>' % (href, title, E(short))


def add_toc(page, groups=None):
    """A side table of contents built from the section headings. Toggleable, follows the reader.
    Each group's sub-entries are collapsed; the script opens the current group, and a toggle opens one by hand."""
    heads = dict(re.findall(r'<h2 id="(h-[a-z]+)"[^>]*>([^<]+)</h2>', page))
    out = []
    for gi, (title, ids) in enumerate(groups or GUIDE_TOC):
        items = ""
        for i in ids:
            if i == "WHATS":
                subs = re.findall(r'<h3 id="(w-[a-z-]+)">([^<]+)</h3>', page)
                items += "".join(toc_link(c, html.unescape(n)) for c, n in subs)
            elif i == "PAIRS":
                for pid, art in re.findall(r'<article class="pair" aria-labelledby="([^"]+)">(.*?)</article>', page, re.S):
                    names = [html.unescape(re.sub(r"<[^>]+>", "", n)) for n in re.findall(r'<div class="colh">(.*?)</div>', art)[:2]]
                    items += toc_link(pid, " / ".join(names), " / ".join(TOC_NAME.get(n, n) for n in names))
            elif i == "STARTS":
                for c, n in re.findall(r'<h3 id="(sh-[a-z0-9-]+)">([^<]+)</h3>', page):
                    items += toc_link(c, first_upper(re.sub(r"^If you ", "", html.unescape(n))), TOC_SHORT.get(c))
            elif i in heads and i not in ("h-start", "h-pair", "h-what"):
                items += toc_link(i, html.unescape(heads[i]))
        has_subs = any(i in ("PAIRS", "STARTS", "WHATS") for i in ids)
        linked = (len(ids) == 1 or has_subs) and ids[0] in heads
        if linked:
            # the group title links to this section, so it is not repeated as an item
            items = re.sub(r'<li><a href="#%s"[^>]*>[^<]*</a></li>' % ids[0], "", items)
        head = ('<a class="toc-group-link" href="#%s">%s</a>' % (ids[0], E(title))) if linked else '<span class="toc-group-name">%s</span>' % E(title)
        if not linked and not items:
            continue
        if items:
            sub = "toc-g-%d" % gi
            btn = ('<button class="toc-gt" type="button" aria-expanded="false" aria-controls="%s" aria-label="Show the entries under %s">'
                   '<span aria-hidden="true"></span></button>' % (sub, E(title)))
            out.append('<div class="toc-g"><p class="toc-group">%s%s</p><ul class="toc-sub" id="%s" hidden>%s</ul></div>' % (head, btn, sub, items))
        else:
            out.append('<div class="toc-g"><p class="toc-group">%s</p></div>' % head)
    nav = ('<button class="toc-toggle no-print" type="button" aria-expanded="false" aria-controls="toc" aria-label="Show contents" title="Show contents"><span aria-hidden="true">&raquo;</span></button>'
           '<nav id="toc" class="toc no-print" aria-label="Contents"><a class="toc-top" href="#top">Cloud Native OS Pulse guide</a>%s</nav>' % "".join(out))
    return page.replace('<div class="pl page" id="top">', nav + '<div class="pl page" id="top">', 1)


def matrix_list(P):
    """The sentence that names the entries that meet the five criteria. Each name opens its data sheet."""
    ids = sorted((i for i in CORE if i in P), key=lambda i: P[i]["name"].lower())
    parts = []
    for i in ids:
        s = sheet_link(P[i])
        if i == "kairos" and "hadron" in P:
            s += " (with %s)" % sheet_link(P["hadron"], "Hadron")
        if i == "microos":
            s += " (borderline on the Kubernetes rule)"
        parts.append(s)
    words = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen".split()
    count = words[len(ids)].capitalize() if len(ids) < len(words) else str(len(ids))
    return "%s entries meet them today: %s, and %s." % (count, ", ".join(parts[:-1]), parts[-1])


def tabs(current):
    def tab(href, label, key):
        return '<a class="tab" href="%s"%s>%s</a>' % (href, ' aria-current="page"' if key == current else "", label)
    return '<nav class="tabs no-print" aria-label="Pages">%s%s</nav>' % (tab("index.html", "Matrix", "matrix"), tab("guide.html", "Guide", "guide"))


def head_top(current):
    return ('<div class="head-top">%s<div class="theme no-print" role="group" aria-label="Colour theme">'
            '<button type="button" value="system">System</button><button type="button" value="light">Light</button><button type="button" value="dark">Dark</button></div></div>'
            % tabs(current))


def cited(body):
    """The source numbers a page links to."""
    return {int(n) for n in re.findall(r'href="#src-(\d+)"', body)}


def ids_of(body):
    return set(re.findall(r'\sid="([^"]+)"', body))


def link_across(body, here, other, other_file):
    """A link to a section that lives on the other page becomes <file>#id. A link to a matrix filter (#matrix?...) keeps its query."""
    def fix(m):
        frag = m.group(2)
        base = frag.split("?", 1)[0]
        if not base or base in here or base not in other:
            return m.group(0)
        return 'href=%s%s#%s%s' % (m.group(1), other_file, frag, m.group(1))
    return re.sub(r'href=(["\'])#([^"\']*)\1', fix, body)


def site(P, tok, css, js):
    """Build both pages. Returns (index html, guide html)."""
    global PROFILES
    PROFILES = P
    S = Sources()
    from content import render_pairs, render_start_here, START_HERE_BLOCKS
    # The order of these calls fixes the source numbers. Keep it.
    pr = pair(P, S) + render_pairs(P, S, E, badge, dim_of, flag, BASE_CHOICE)
    mx = matrix(P, S)
    ctx = context_box(P, S)
    order = sorted(CORE, key=lambda x: P[x]["name"].lower())
    for folded, host in FOLDED.items():   # a folded entry gets its own data sheet, directly after its host's
        if folded in P and host in order:
            order.insert(order.index(host) + 1, folded)
    cards = "".join(data_sheet(P[pid], S) for pid in order)
    dims = "".join('<li id="%s">%s</li>' % (k, E(n)) for k, n in DIMS)
    import lineage
    origins = lineage.render(LINEAGE, S, E, badge, sheets=set(order))

    index_body = f"""
<div class="pl page" id="top">
<header>
  {head_top("matrix")}
  <span class="eyebrow build-eyebrow">__BUILD__</span>
  <h1>Cloud Native OS Pulse</h1>
  <p class="tagline">A sourced comparison of cloud native operating systems. Every cell carries an evidence label and a source. Click a project name to open its data sheet.</p>
  <p class="guide-link"><a href="guide.html">Read the guide: what a cloud native OS is, how this was built, and how to read the matrix.</a></p>
  <p class="byline-coi">I am one of the maintainers of Kairos and Hadron, two of the entries, and I work for Spectro Cloud. See <a href="#h-who">Who is behind it</a>.</p>
  <div>{stamp(P)}</div>
  <div class="banner" role="note"><b>Illustrative</b><span>Data under fact-fix. These pages show a proposed structure built from the current profiles. Cells marked Fact-fix are under review and may change.</span></div>
  {review_bar()}
</header>
<main id="content" tabindex="-1">

<section class="sec sec-matrix" aria-labelledby="h-matrix">
  <h2 id="h-matrix">Comparison matrix</h2>
  <p class="lede">One row per core entry, alphabetical by name. Every cell carries its evidence label and a source. Sort by any column; filter by value. Click a project name for its data sheet.</p>
  {review("5 and 2", "filterable matrix and a shorter entry list", "Columns follow the proposed order. Hadron is folded into the Kairos row; NixOS, Unikraft and the Yocto Project have their own section, Alternative paradigms, in the guide. One alphabetical list: the Bring your own distro column is the distinction, so there are no group headers.")}
  {mx}
</section>

<section class="sec band band-warm sec-cards" aria-labelledby="h-cards">
  <h2 id="h-cards">Project data sheets</h2>
  <p class="lede">One sheet per entry. Each lists every value from the matrix in full, with its evidence and sources. It does not rank or judge.</p>
  {review("1", "data sheets", "Generated from each profile: the matrix columns in full, the version identity and maintainers_fact. One sheet per matrix entry, plus Hadron, which the matrix folds into the Kairos row. With JavaScript the sheets open in a modal from the project names, and this section is hidden.")}
  <div class="cards">{cards}</div>
</section>

<section class="sec" aria-labelledby="h-src">
  <h2 id="h-src">Sources</h2>
  <p class="lede">Primary sources only. Each was read on the date shown.</p>
  __SOURCES__
</section>
</main>
</div>
{col_defs()}
<a class="src-back no-print" href="#top" hidden>Back</a>"""

    guide_body = f"""
<div class="pl page" id="top">
<header>
  {head_top("guide")}
  <span class="eyebrow build-eyebrow">__BUILD__</span>
  <h1>Cloud Native OS Pulse guide</h1>
  <p class="tagline">What a cloud native OS is, how the Pulse was made, and how to read the matrix.</p>
  <p class="byline">by Mauro Morales, CNCF Ambassador</p>
  <p class="byline-coi">I am one of the maintainers of Kairos and Hadron, two of the entries, and I work for Spectro Cloud. See <a href="#h-who">Who is behind it</a>.</p>
  <div>{stamp(P)}</div>
  <div class="banner" role="note"><b>Illustrative</b><span>Data under fact-fix. These pages show a proposed structure built from the current profiles. Cells marked Fact-fix are under review and may change.</span></div>
  {review_bar()}
</header>
<main id="content" tabindex="-1">

<section class="sec" aria-labelledby="h-what">
  <h2 id="h-what">What is a cloud native OS?</h2>
  {what_is().replace("__MATRIX_LIST__", matrix_list(P))}
</section>

<section class="sec" aria-labelledby="h-myths">
  <h2 id="h-myths">Misconceptions</h2>
  {misconceptions()}
</section>

<section class="sec band band-cool" aria-labelledby="h-start">
  <h2 id="h-start">Start from your situation</h2>
  <p class="lede">New to immutable operating systems, with a constraint you already know? Pick the situation closest to yours. Each one lists the questions that matter for it and opens the matrix filtered to the systems that meet them. The blocks name no project. Each question opens a matrix filter or a matrix column: the values are there, and the conclusion is yours. A question the matrix does not cover yet says so.</p>
  {review("4", "question router", "Needs your ruling on methodology section 8: it bans best-for-X lines. This block routes to questions and filters only. %s blocks are shown." % word(1 + len(START_HERE_BLOCKS), True))}
  {start_here()}{render_start_here(E)}
</section>

<section class="sec" aria-labelledby="h-review">
  <h2 id="h-review">Is your project here?</h2>
  <div class="prose">{open(os.path.join(HERE, "maintainers.html")).read()}</div>
</section>

<section class="sec" aria-labelledby="h-pair">
  <h2 id="h-pair">Looks alike, differs on</h2>
  <p class="lede">Pairs of entries that share a design and part ways on one property a reader acts on.</p>
  {pr}
</section>

<section class="sec" aria-labelledby="h-origins">
  <h2 id="h-origins">Where they came from</h2>
  <p class="lede">Each bar runs from an operating system's first public release to its end, or to today. A tick marks a rename. Lines show forks, named successors, merges, what a system is built on, and influences a project names itself. Select a bar or a line for its source.</p>
  <p class="lede lin-note">Lines appear only where a project, or the project it links to, documents the link. So a project with few lines has none documented yet. <span class="lin-access"></span>Corrections and additions are welcome, with a source: <a href="https://github.com/cloudnativeos-org/pulse/issues/new">open an issue</a> or send a patch to <code><a href="https://github.com/cloudnativeos-org/pulse/blob/main/data/lineage.yaml">data/lineage.yaml</a></code>. See <a href="#fix-h">Found a mistake, or something missing?</a></p>
  {origins}
</section>

<section class="sec" aria-labelledby="h-alt">
  <h2 id="h-alt">Alternative paradigms</h2>
  {ctx}
</section>

<section class="sec" aria-labelledby="h-worth">
  <h2 id="h-worth">Worth mentioning</h2>
  {worth_mentioning()}
</section>

<section class="sec" aria-labelledby="h-excluded">
  <h2 id="h-excluded">Considered and excluded</h2>
  {excluded()}
</section>

<section class="sec" aria-labelledby="h-who">
  <h2 id="h-who">Who is behind it</h2>
  {who()}
</section>

<section class="sec band band-sunk" aria-labelledby="h-made">
  <h2 id="h-made">How it was made</h2>
  <p class="lede">Method, stake, and how to correct the record.</p>
  {made(P)}
  <div style="margin-top:var(--space-8)">{fix_callout()}</div>
  <p class="star-cta">If the Cloud Native OS Pulse helps you, please <a href="https://github.com/cloudnativeos-org/pulse">star it on GitHub</a>. It helps more people find it.</p>
</section>

<section class="sec" aria-labelledby="h-why">
  <h2 id="h-why">Why it exists</h2>
  <div class="prose">{open(os.path.join(HERE, "why.html")).read()}</div>
</section>

<section class="sec" aria-labelledby="h-wishes">
  <h2 id="h-wishes">What I'd like to see</h2>
  <div class="prose">{open(os.path.join(HERE, "wishes.html")).read()}</div>
</section>

<section class="sec" aria-labelledby="h-gloss">
  <h2 id="h-gloss">Glossary</h2>
  {glossary()}
</section>

<section class="sec" aria-labelledby="h-dims">
  <h2 id="h-dims">What the columns mean</h2>
  <p class="lede">Each column of the comparison matrix, with the question it answers. In the matrix, the ? next to a column title opens the same text.</p>
  {columns_explained()}
  <h3 id="dims-list" class="dims-h">The fourteen dimensions</h3>
  <p class="lede">The fourteen dimensions every profile records. There is no section per dimension yet; the values are in each project's profile and in the data sheets.</p>
  <ol class="dims">{dims}</ol>
</section>

<section class="sec" aria-labelledby="h-src">
  <h2 id="h-src">Sources</h2>
  <p class="lede">Primary sources only. Each was read on the date shown.</p>
  __SOURCES__
</section>
</main>
</div>
<a class="src-back no-print" href="#top" hidden>Back</a>"""

    # Each page lists the sources it cites, with the numbers they have everywhere.
    index_body = index_body.replace("__SOURCES__", S.render(cited(index_body)), 1)
    guide_body = guide_body.replace("__SOURCES__", S.render(cited(guide_body)), 1)
    guide_body = add_toc(guide_body)
    # A link to a section on the other page carries that page's file name.
    ii, gi = ids_of(index_body), ids_of(guide_body)
    index_body = link_across(index_body, ii, gi, "guide.html")
    guide_body = link_across(guide_body, gi, ii, "index.html")
    # An old link to the one-page site, such as /#h-pair, lands on the guide when the id lives there.
    moved = sorted(gi - ii)
    redirect = ('<script id="old-hash">document.documentElement.classList.add("js");(function(){var g=" %s ";'
                'function go(){var h="";try{h=decodeURIComponent(location.hash.slice(1)).split("?")[0]}catch(e){}'
                'if(h&&g.indexOf(" "+h+" ")>-1)location.replace("guide.html#"+h)}'
                'go();window.addEventListener("hashchange",go)})()</script>' % " ".join(moved))

    def document(title, desc, head_script, body):
        return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
{head_script}
<style>{tokens_css(tok)}</style>
<style>{css}</style>
</head><body><a class="skip-link" href="#content">Skip to content</a>{body}
<script>{js}</script>
</body></html>"""

    return (document("Cloud Native OS Pulse", "Sample pages for the Cloud Native OS Pulse. Illustrative, data under fact-fix.", redirect, index_body),
            document("Cloud Native OS Pulse guide", "The guide to the Cloud Native OS Pulse: what a cloud native OS is, how it was made, and how to read the matrix.",
                     '<script>document.documentElement.classList.add("js")</script>', guide_body))


def finish(page, P, gen, sha):
    """The steps that apply to both pages: the build stamp, the preview changes and the final checks."""
    # The deep dimension sections are not built yet, so a dimension reference is plain text, not a dead link.
    page = re.sub(r'<a href="#d\d\d">([^<]*)</a>', r'<span class="to-dim">\1</span>', page)
    page = page.replace('__BUILD__', 'Rolling release · commit <span class="mono">%s</span> · generated <time datetime="%s">%s</time>' % (sha, gen, gen), 1)
    if os.environ.get("PULSE_PREVIEW"):
        # A review preview: say so in the title, the heading and a banner, and keep it out of search engines.
        page = re.sub(r"<title>(.*?)</title>", r'<title>\1 (preview, not released)</title><meta name="robots" content="noindex, nofollow">', page, count=1)
        page = re.sub(r"(<h1>.*?)(</h1>)", r'\1 <span class="preview-tag">Preview</span>\2', page, count=1)
        page = re.sub(r'<div class="banner" role="note">.*?</div>',
                      '<div class="banner" role="note"><b>Preview, not released</b><span>This is a work in progress shared for review. '
                      'Facts are still being checked and may change. Please do not share it widely yet. '
                      'The repository is private during the preview: send me your GitHub username, through the contact links on '
                      '<a href="https://mauromorales.com/">mauromorales.com</a>, and I will give you access so you can open issues.</span></div>', page, count=1, flags=re.S)
        # Review notes and their switch are for the author, not for preview readers.
        page = re.sub(r'\s*<p class="review">.*?</p>', "", page, flags=re.S)
        page = re.sub(r'\s*<form class="review-bar[^"]*".*?</form>', "", page, flags=re.S)
        # The repository is private until release: its links would 404, so the preview unlinks them.
        page = re.sub(r'<p class="star-cta">.*?</p>', "", page, flags=re.S)
        page = re.sub(r'\s*<a href="https://github\.com/cloudnativeos-org/pulse/blob/[^"]*/data/projects/[^"]*">Profile</a>', "", page)
        page = page.replace('<p class="muted" style="margin:0">The Pulse is open to fixes and to proposals. Everything goes through the repository.</p>',
                            '<p class="muted" style="margin:0">The Pulse is open to fixes and to proposals. During the preview the repository is private: '
                            'send me your GitHub username through <a href="https://mauromorales.com/">mauromorales.com</a> and I will give you access. '
                            'Then use the links below.</p>', 1)
        page = page.replace("the full history is public in", "the full history will be public at release in")
        page = page.replace('<span class="lin-access"></span>', 'During the preview the repository is private: send me your GitHub username through '
                            '<a href="https://mauromorales.com/">mauromorales.com</a> and I will give you access. ', 1)
        page = re.sub(r'<a href="https://github\.com/cloudnativeos-org/pulse/blob/[^"]*">([^<]*)</a>', r"\1", page)
    page = page.replace('<span class="lin-access"></span>', "")
    assert "—" not in page, "em dash in output"
    return page


def main():
    src, out = sys.argv[1], sys.argv[2]
    P = load(src)
    load_versions(src)
    global LINEAGE
    LINEAGE = os.path.join(os.path.dirname(os.path.abspath(src.rstrip("/"))), "lineage.yaml")
    import lineage
    bad = lineage.check(LINEAGE)
    if bad:
        sys.exit("lineage data problems:\n  " + "\n  ".join(bad))
    tok = json.load(open(os.path.join(HERE, "tokens.json")))
    css = open(os.path.join(HERE, "src", "pulse.css")).read()
    js = open(os.path.join(HERE, "src", "pulse.js")).read()
    os.makedirs(os.path.join(out, "site"), exist_ok=True)
    import subprocess
    try:
        sha = subprocess.run(["git", "-C", src, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        sha = "unknown"
    gen = dt.date.today().isoformat()
    css = css.replace('content: "Cloud Native OS Pulse 2026"', 'content: "Cloud Native OS Pulse"')
    css = css.replace('content: "Data as of 22 Sep 2026"', 'content: "Data as of %s"' % fmt_date(data_dates(P)[1]))
    css = css.replace('content: "Illustrative, data under fact-fix"', 'content: "Generated %s from commit %s. Illustrative, data under fact-fix"' % (gen, sha))
    index_page, guide_page = site(P, tok, css, js)
    index_page, guide_page = finish(index_page, P, gen, sha), finish(guide_page, P, gen, sha)
    # The deploy must copy both files. Neither page needs any other file.
    open(os.path.join(out, "site", "index.html"), "w").write(index_page)
    open(os.path.join(out, "site", "guide.html"), "w").write(guide_page)
    # Artifact variant of the matrix page: the host adds the document skeleton.
    page = index_page
    head, rest = page.split("<head>", 1)
    inner_head, body = rest.split("</head>", 1)
    inner_head = inner_head.replace('<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">', "")
    inner_head = inner_head.replace("<title>Cloud Native OS Pulse</title>", "<title>OS Pulse Sample Pages</title>")
    body = body.replace("<body>", "").replace("</body></html>", "")
    open(os.path.join(out, "site", "artifact.html"), "w").write(inner_head + body)
    try:
        import ds  # design-system files
    except ImportError:
        print("no ds.py yet"); print("ok", len(index_page), len(guide_page)); return
    ds.write(P, tok, css, js, os.path.join(out, "ds"), sys.modules[__name__])
    print("ok", len(index_page), len(guide_page))


if __name__ == "__main__":
    main()
