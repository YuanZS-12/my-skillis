"""User-run NX 2606 probe: native save and non-empty STEP export."""

import os

import NXOpen
import NXOpen.Features

from _probe_support import cylinder, export_step, run_probe


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "user_authorized": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {"recipe": "nx2606.export.step", "runtime": "manual user run required"}
DESIGN_LEDGER = {"target_nx_version": "NX 2606", "expected_body_count": 1, "critical_features": ["native_save", "step_export"]}


def operation(session, work_part, report):
    cylinder(work_part, 20.0, 10.0)
    native_path = getattr(work_part, "FullPath", "")
    if not native_path:
        raise RuntimeError("Work part has no FullPath after native save preparation")
    # Bind STEP evidence to this run's unique native part name. A fixed journal
    # basename can leave an older STEP in place and turn mere file existence
    # into a false-positive export result.
    output_path = os.path.splitext(native_path)[0] + ".step"
    export_step(session, work_part, output_path)
    report["native_part"] = {
        "path": native_path,
        "exists": os.path.isfile(native_path),
    }
    report["step"] = {"path": output_path, "exists": True, "size": os.path.getsize(output_path)}
    print("NXCAD_STEP_EXPORTED:", output_path)


def main():
    run_probe(__file__, "NX 2606", "10_step_ap242", 1, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
