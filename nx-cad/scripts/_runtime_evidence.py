"""Shared runtime-report compatibility and provenance checks for nx-cad."""

from __future__ import annotations

from pathlib import Path


VALID_RESULTS = {"success", "partial", "failure"}
VALID_ACTORS = {"user"}


def schema_version(report: dict) -> int | None:
    value = report.get("schema_version")
    return value if isinstance(value, int) else None


def body_count(report: dict) -> object:
    model = report.get("model")
    if isinstance(model, dict) and "body_count" in model:
        return model.get("body_count")
    return report.get("body_count")


def expected_body_count(report: dict) -> object:
    model = report.get("model")
    if isinstance(model, dict):
        return model.get("expected_body_count")
    return report.get("expected_body_count")


def probe_name(report: dict) -> str:
    return str(report.get("probe") or "")


def execution_provenance(report: dict) -> tuple[str | None, list[str]]:
    """Return a stable provenance label plus validation problems.

    Both schemas accept only a user-run NX session. dc_mcp_server lookup
    results may review code, but an external journal runner cannot stand in for the
    already-open NX UI and is not accepted as runtime evidence.
    """

    version = schema_version(report)
    problems: list[str] = []
    if version == 1:
        if report.get("manual_user_run") is not True:
            problems.append("schema v1 runtime evidence must come from a manual user-run Siemens NX session")
        if report.get("agent_execution") is not False:
            problems.append("schema v1 runtime report must explicitly record agent_execution=false")
        return "user:nx_ui" if not problems else None, problems

    if version != 2:
        return None, ["schema_version must be 1 or 2"]

    execution = report.get("execution")
    if not isinstance(execution, dict):
        return None, ["schema v2 runtime report requires an execution object"]

    actor = execution.get("actor")
    transport = execution.get("transport")
    if actor not in VALID_ACTORS:
        problems.append("execution.actor must be user; agent NX execution is not supported")
    if not isinstance(transport, str) or not transport:
        problems.append("execution.transport must be a non-empty string")

    if actor == "user" and transport not in {"nx_ui", "manual"}:
        problems.append("user NX execution transport must be nx_ui or manual")

    label = f"{actor}:{transport}" if actor in VALID_ACTORS and isinstance(transport, str) else None
    return label if not problems else None, problems


def critical_feature_problems(report: dict) -> list[str]:
    model = report.get("model")
    if not isinstance(model, dict):
        return []
    features = model.get("critical_features")
    if features is None:
        return []
    if not isinstance(features, dict):
        return ["model.critical_features must be an object"]
    return [
        f"critical feature did not pass: {name}"
        for name, passed in features.items()
        if passed is not True
    ]


def validate_runtime_report(
    report: dict,
    *,
    expected_bodies: int | None,
    require_success: bool,
    path: Path | None = None,
) -> list[str]:
    prefix = f"{path}: " if path is not None else ""
    problems: list[str] = []
    _label, provenance_problems = execution_provenance(report)
    problems.extend(prefix + problem for problem in provenance_problems)

    result = report.get("result")
    if result not in VALID_RESULTS:
        problems.append(prefix + "result must be success, partial, or failure")
    if require_success and result != "success":
        problems.append(prefix + f"successful NX runtime evidence required; report result is {result!r}")

    actual_bodies = body_count(report)
    if expected_bodies is not None and actual_bodies != expected_bodies:
        problems.append(
            prefix + f"expected body_count={expected_bodies}, runtime report has {actual_bodies!r}"
        )
    reported_expected = expected_body_count(report)
    if reported_expected is not None and actual_bodies != reported_expected:
        problems.append(
            prefix
            + f"runtime report expected_body_count={reported_expected!r}, but body_count={actual_bodies!r}"
        )
    if require_success:
        problems.extend(prefix + problem for problem in critical_feature_problems(report))
    return problems
