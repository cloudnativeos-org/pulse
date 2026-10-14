#!/usr/bin/env python3
"""Validate Cloud Native OS Pulse project profiles.

Usage:
    python3 tools/validate_profiles.py [PROFILE_DIR ...]

With no arguments it validates every ``*/projects`` directory it finds under
the repository root.

Two layers of checking run:

1. **Schema.** If the ``jsonschema`` package is installed, every profile is
   validated against ``schema/profile.schema.json``. If it is not installed the
   script says so and skips this layer rather than failing, so the dataset stays
   checkable on a machine without it.

2. **Consistency rules the schema cannot express.** These are the rules that stop
   the dataset from quietly becoming misleading:

   - A normalized value of ``none`` asserts a *documented* absence, so its
     dimension must carry ``evidence: DOCUMENTED`` and at least one source.
   - A normalized value of ``not-applicable`` needs a ``notes`` entry saying why,
     and the dimension should be listed in ``category_fit.dimensions_not_applicable``.
   - ``evidence: INFERRED`` needs ``inferred_from``; ``evidence: UNKNOWN`` needs
     ``searched``.
   - A ``summary`` must not be a bare yes/no. The Pulse forbids binary answers
     for non-binary properties.
   - No profile may carry a score, rank, rating, or grade field. The survey
     produces no aggregate score by design, and this check keeps that true as the
     dataset grows.
   - Every source needs a ``retrieved`` date, because a Pulse is a point-in-time
     record and an undated source cannot be diffed against the next edition.

Exit code 0 means every profile passed. Exit code 1 means at least one error.
Warnings do not fail the run.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: python3 -m pip install pyyaml")

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCHEMA_PATH = ROOT / "schema" / "profile.schema.json"

BANNED_FIELD_PATTERN = re.compile(r"(^|_)(score|rank|rating|grade|stars|winner)(_|$)", re.I)
KNOWN_ISSUE_KINDS = ("defect", "unverified", "maintenance-stopped", "stated-vs-delivered")
BARE_BINARY = re.compile(r"^\s*(yes|no|true|false|n/?a)\s*\.?\s*$", re.I)

REQUIRED_DIMENSIONS = [
    "d01_os_model",
    "d02_immutability",
    "d03_artifact",
    "d04_upgrade",
    "d05_rollback_recovery",
    "d06_customization",
    "d07_kubernetes",
    "d08_hardware_platform",
    "d09_provisioning",
    "d10_security",
    "d11_operations_debugging",
    "d12_fleet_management",
    "d13_governance",
    "d14_maturity",
]


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"ERROR {where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"WARN  {where}: {message}")


def walk_strings(node, path=""):
    """Yield (path, value) for every string leaf in a nested structure."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk_strings(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_strings(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


def walk_keys(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else str(key)
            yield here, key
            yield from walk_keys(value, here)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_keys(value, f"{path}[{index}]")


def check_sources(where: str, dimension: dict, report: Report) -> None:
    for index, source in enumerate(dimension.get("sources") or []):
        at = f"{where}.sources[{index}]"
        if not isinstance(source, dict):
            report.error(at, "source must be a mapping")
            continue
        for field in ("url", "type", "retrieved"):
            if not source.get(field):
                report.error(at, f"missing required source field '{field}'")
        url = source.get("url", "")
        if url and not url.startswith(("http://", "https://")):
            report.error(at, f"url is not an absolute URL: {url!r}")
        if not source.get("quote"):
            report.warn(at, "no quote recorded; a quote makes the claim checkable without refetching")


def check_dimension(profile_id: str, name: str, dimension, report: Report) -> None:
    where = f"{profile_id}:{name}"
    if not isinstance(dimension, dict):
        report.error(where, "dimension must be a mapping")
        return

    evidence = dimension.get("evidence")
    summary = dimension.get("summary")

    if not summary:
        report.error(where, "missing 'summary'")
    elif BARE_BINARY.match(summary):
        report.error(
            where,
            f"summary is a bare binary answer ({summary!r}); the Pulse requires a normalized description",
        )

    if not evidence:
        report.error(where, "missing 'evidence'")
        return

    if evidence == "DOCUMENTED" and not dimension.get("sources"):
        report.error(where, "evidence is DOCUMENTED but no sources are recorded")
    if evidence == "INFERRED" and not dimension.get("inferred_from"):
        report.error(where, "evidence is INFERRED but 'inferred_from' is missing")
    if evidence == "UNKNOWN" and not dimension.get("searched"):
        report.error(where, "evidence is UNKNOWN but 'searched' is missing")

    normalized = dimension.get("normalized") or {}
    for path, value in walk_strings(normalized):
        if value == "none":
            if evidence != "DOCUMENTED":
                report.error(
                    where,
                    f"normalized.{path} is 'none' (a documented absence) but evidence is {evidence}; "
                    "use 'unknown' when the absence is not documented",
                )
            elif not dimension.get("sources"):
                report.error(where, f"normalized.{path} is 'none' but no source documents the absence")
        if value == "not-applicable" and not dimension.get("notes"):
            report.error(
                where,
                f"normalized.{path} is 'not-applicable' but no 'notes' explains why the concept does not apply",
            )

    check_sources(where, dimension, report)
    if name.startswith("d02_"):
        check_mounts(profile_id, where, normalized, report)
    if name.startswith("d08_"):
        check_via_base(where, normalized, report)
    if name.startswith("d06_"):
        check_add_software(profile_id, where, normalized, report)


MOUNTS_CONFIGURABLE = ("yes", "no", "unknown", "via-lifecycle-manager")
VIA_BASE_ARCHS = ("amd64", "arm64", "riscv64", "ppc64le", "s390x")


def check_mounts(profile_id: str, where: str, normalized: dict, report: Report) -> None:
    """The Mounts row of the data sheet reads d02. Every entry needs its four lines (rule 21's companion row):
    read-only, writable and reset on reboot, writable and persistent, configurable."""
    cp = normalized.get("configurable_paths")
    if not isinstance(cp, dict):
        report.error(where, "normalized.configurable_paths is missing; the Mounts row needs it")
        return
    if cp.get("value") not in MOUNTS_CONFIGURABLE:
        report.error(where, f"configurable_paths.value must be one of {', '.join(MOUNTS_CONFIGURABLE)}, got {cp.get('value')!r}")
    if not cp.get("how"):
        report.error(where, "configurable_paths.how is missing; say what the adopter can change, in one line")
    ev = cp.get("evidence")
    if ev not in ("DOCUMENTED", "REPRODUCED", "OBSERVED", "INFERRED", "UNKNOWN", "NOT_TESTED"):
        report.error(where, f"configurable_paths.evidence is missing or not an evidence label: {ev!r}")
    if ev == "INFERRED" and not cp.get("inferred_from"):
        report.error(where, "configurable_paths is INFERRED but 'inferred_from' is missing")
    if ev == "UNKNOWN" and not cp.get("searched"):
        report.error(where, "configurable_paths is UNKNOWN but 'searched' is missing")
    if cp.get("value") == "via-lifecycle-manager" and not normalized.get("provided_by"):
        report.error(where, "configurable_paths is via-lifecycle-manager but normalized.provided_by names no lifecycle manager")
    if ev == "DOCUMENTED" and not cp.get("sources"):
        report.error(where, "configurable_paths is DOCUMENTED but records no sources")
    for label, group in (("configurable_paths.sources", cp.get("sources")), ("mounts_sources", normalized.get("mounts_sources"))):
        for j, source in enumerate(group or []):
            for field in ("url", "type", "retrieved", "quote"):
                if not source.get(field):
                    report.error(f"{where}.{label}[{j}]", f"missing '{field}'; the Mounts row cites it, so it needs a verbatim quote")
    layout_set_elsewhere = bool(normalized.get("mount_layout"))
    if not layout_set_elsewhere:
        for key in ("read_only", "writable_and_persistent"):
            if not normalized.get(key):
                report.error(where, f"normalized.{key} is missing; the Mounts row needs it (or normalized.mount_layout, for a base distribution)")
    if normalized.get("immutability_can_be_disabled") not in (None, False, "unknown") and not normalized.get("immutability_disable_where"):
        report.error(where, "immutability_can_be_disabled is set but immutability_disable_where is missing")


def check_via_base(where: str, normalized: dict, report: Report) -> None:
    for i, entry in enumerate(normalized.get("architectures_via_base_distribution") or []):
        at = f"{where}.architectures_via_base_distribution[{i}]"
        for arch in entry.get("archs") or []:
            if arch not in VIA_BASE_ARCHS:
                report.error(at, f"unknown architecture {arch!r}; use one of {', '.join(VIA_BASE_ARCHS)}")
        if not entry.get("archs") or not entry.get("components"):
            report.error(at, "needs archs and the components that are built for them")
        if not entry.get("sources"):
            report.error(at, "needs at least one source")
        for j, source in enumerate(entry.get("sources") or []):
            for field in ("url", "type", "retrieved", "quote"):
                if not source.get(field):
                    report.error(f"{at}.sources[{j}]", f"missing '{field}'")


ADD_SOFTWARE_KINDS = ("systemd-sysext", "vendor-extensions", "derive-image", "package-layering", "transactional-packages",
                      "snaps", "build-time-only", "not-supported", "unknown")


def check_add_software(profile_id: str, where: str, normalized: dict, report: Report) -> None:
    """The matrix column 'Adding software to the OS' reads d06.normalized.add_software. Each entry is one way, with its own
    evidence label and sources. 'unknown' stands alone. A DOCUMENTED entry needs a source with a verbatim quote."""
    items = normalized.get("add_software")
    if items is None:
        report.warn(where, "normalized.add_software is missing; the 'Adding software to the OS' column shows Not collected")
        return
    if not isinstance(items, list) or not items:
        report.error(where, "normalized.add_software must be a non-empty list")
        return
    seen = set()
    for i, item in enumerate(items):
        at = f"{where}.add_software[{i}]"
        kind = item.get("kind")
        if kind not in ADD_SOFTWARE_KINDS:
            report.error(at, f"kind must be one of {', '.join(ADD_SOFTWARE_KINDS)}, got {kind!r}")
        if kind in seen:
            report.error(at, f"kind {kind!r} appears twice; record each way once, with all its sources")
        seen.add(kind)
        if not item.get("how"):
            report.error(at, "missing 'how'; say how it is done")
        ev = item.get("evidence")
        if ev not in ("DOCUMENTED", "REPRODUCED", "OBSERVED", "INFERRED", "UNKNOWN", "NOT_TESTED"):
            report.error(at, f"evidence is missing or not an evidence label: {ev!r}")
        if ev == "INFERRED" and not item.get("inferred_from"):
            report.error(at, "evidence is INFERRED but 'inferred_from' is missing")
        if ev == "UNKNOWN" and not item.get("searched"):
            report.error(at, "evidence is UNKNOWN but 'searched' is missing")
        if (kind == "unknown") != (ev == "UNKNOWN"):
            report.error(at, "kind 'unknown' and evidence UNKNOWN go together")
        if ev in ("DOCUMENTED", "REPRODUCED", "OBSERVED") and not item.get("sources"):
            report.error(at, f"evidence is {ev} but no sources are recorded")
        for j, source in enumerate(item.get("sources") or []):
            for field in ("url", "type", "retrieved", "quote"):
                if not source.get(field):
                    report.error(f"{at}.sources[{j}]", f"missing '{field}'; the data sheet cites it, so it needs a verbatim quote")
    if "unknown" in seen and len(items) > 1:
        report.error(where, "add_software: kind 'unknown' must be the only entry")


def check_profile(path: pathlib.Path, report: Report) -> dict | None:
    try:
        profile = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        report.error(path.name, f"YAML parse error: {exc}")
        return None
    if not isinstance(profile, dict):
        report.error(path.name, "profile root must be a mapping")
        return None

    profile_id = profile.get("id") or path.stem
    if profile.get("id") and path.stem != profile["id"]:
        report.error(path.name, f"filename does not match id {profile['id']!r}")

    for field in ("schema_version", "edition", "id", "name", "collected_at", "entry_kind", "tradeoffs"):
        if field not in profile:
            report.error(profile_id, f"missing required top-level field '{field}'")

    tradeoffs = profile.get("tradeoffs") or {}
    for side in ("buys", "costs"):
        if not tradeoffs.get(side):
            report.error(
                profile_id,
                f"tradeoffs.{side} is empty; every profile must record both what the design buys and what it costs",
            )

    # Known issues (methodology section 9, rule 19): one of four kinds, each with a dated source.
    for i, issue in enumerate(profile.get("known_issues") or []):
        if issue.get("kind") not in KNOWN_ISSUE_KINDS:
            report.error(profile_id, f"known_issues[{i}].kind must be one of {', '.join(KNOWN_ISSUE_KINDS)}")
        if not issue.get("text") or not issue.get("sources"):
            report.error(profile_id, f"known_issues[{i}] needs text and at least one source")
        for src in issue.get("sources") or []:
            if not src.get("url") or not src.get("retrieved"):
                report.error(profile_id, f"known_issues[{i}] has a source without a url or a retrieved date")
    fact = profile.get("maintainers_fact")
    if fact is not None and (not fact.get("text") or not fact.get("sources")):
        report.error(profile_id, "maintainers_fact needs text and at least one source")

    for key_path, key in walk_keys(profile):
        if BANNED_FIELD_PATTERN.search(key):
            report.error(
                profile_id,
                f"field {key_path!r} looks like a score or ranking; the Pulse produces no aggregate score",
            )

    dimensions = profile.get("dimensions") or {}
    for name in REQUIRED_DIMENSIONS:
        if name not in dimensions:
            report.error(profile_id, f"missing dimension '{name}'")
    for name in dimensions:
        if name not in REQUIRED_DIMENSIONS:
            report.error(profile_id, f"unexpected dimension '{name}'")
    for name, dimension in dimensions.items():
        check_dimension(profile_id, name, dimension, report)

    declared_na = set((profile.get("category_fit") or {}).get("dimensions_not_applicable") or [])
    for name, dimension in dimensions.items():
        if not isinstance(dimension, dict):
            continue
        values = {value for _, value in walk_strings(dimension.get("normalized") or {})}
        if "not-applicable" in values and name not in declared_na:
            report.warn(
                profile_id,
                f"{name} uses 'not-applicable' but is not listed in "
                "category_fit.dimensions_not_applicable. That is correct when only a single "
                "sub-field does not apply; list the dimension only if the whole question is a "
                "category error for this entry.",
            )

    return profile


def schema_check(profiles: list[tuple[pathlib.Path, dict]], report: Report) -> None:
    try:
        import jsonschema
    except ImportError:
        print("note: jsonschema not installed; structural schema validation skipped "
              "(consistency rules still ran). Install with: python3 -m pip install jsonschema")
        return
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for path, profile in profiles:
        for error in sorted(validator.iter_errors(profile), key=lambda e: list(e.path)):
            location = "/".join(str(part) for part in error.path) or "<root>"
            report.error(f"{path.stem}:{location}", error.message)


def main(argv: list[str]) -> int:
    dirs = [pathlib.Path(arg) for arg in argv[1:]]
    if not dirs:
        dirs = sorted(ROOT.glob("*/projects"))
    if not dirs:
        print("no profile directories found")
        return 1

    report = Report()
    loaded: list[tuple[pathlib.Path, dict]] = []
    count = 0
    for directory in dirs:
        if not directory.is_dir():
            report.error(str(directory), "not a directory")
            continue
        for path in sorted(directory.glob("*.yaml")):
            count += 1
            profile = check_profile(path, report)
            if profile is not None:
                loaded.append((path, profile))

    schema_check(loaded, report)

    for line in report.warnings:
        print(line)
    for line in report.errors:
        print(line)

    print(f"\n{count} profile(s) checked, {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
