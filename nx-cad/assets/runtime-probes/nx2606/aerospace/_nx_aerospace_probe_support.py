"""Schema-v2 reporting support for self-contained manual NX aerospace probes."""

import hashlib
import json
import os
import re


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_id_for(probe_file):
    configured = os.environ.get("NXCAD_RUN_ID", "")
    if re.fullmatch(r"run_\d{3,}", configured):
        return configured
    match = re.search(r"_(\d{3,})$", os.path.basename(os.path.dirname(probe_file)))
    return "run_" + match.group(1) if match else "run_001"


def _artifact(entry):
    if not isinstance(entry, dict):
        return {}
    return {
        "path": entry.get("path", ""),
        "exists": bool(entry.get("exists")),
        "size": int(entry.get("size") or 0),
    }


def write_schema_v2_report(probe_file, output_path, report, design_ledger):
    features = report.get("features") if isinstance(report.get("features"), dict) else {}
    normalized = {
        "schema_version": 2,
        "execution": {"actor": "user", "transport": "nx_ui", "tool": "nx_ui"},
        "nx_version": report.get("nx_version", "NX 2606"),
        "probe": report.get("probe", ""),
        "run_id": run_id_for(probe_file),
        "source_sha256": sha256_file(probe_file),
        "result": report.get("result", "failure"),
        "journal": {
            "path": os.path.abspath(probe_file),
            "working_dir": os.path.dirname(os.path.abspath(probe_file)),
        },
        "model": {
            "body_count": report.get("body_count"),
            "expected_body_count": design_ledger.get("expected_body_count"),
            "critical_features": {
                name: features.get(name) in {True, "success"}
                for name in design_ledger.get("critical_features", [])
            },
        },
        "artifacts": {
            "prt": _artifact(report.get("native_part")),
            "step": _artifact(report.get("step")),
        },
        "warnings": report.get("warnings", []),
    }
    if report.get("error"):
        normalized["error"] = report["error"]
    with open(output_path, "w", encoding="utf-8") as stream:
        json.dump(normalized, stream, indent=2, sort_keys=True)
    print("NXCAD_RUNTIME_REPORT:", output_path)
