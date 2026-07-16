"""Controlled NX 2606 probe for a two-section ThroughCurves solid."""

import NXOpen
import NXOpen.Features

from _probe_support import closed_rectangle_section, run_probe


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "manual_user_run_required": True, "agent_execution": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {
    "recipe": "nx2606.through-curves.solid",
    "reason": "Use manual NX or explicitly authorized dc_mcp execution for runtime validation.",
}
DESIGN_LEDGER = {
    "capability_level": "experimental_raw",
    "target_nx_version": "NX 2606",
    "expected_body_count": 1,
    "critical_features": ["two_section_through_curves_solid"],
    "optional_features": [],
}


def operation(session, work_part, report):
    root = closed_rectangle_section(work_part, 0.0, 20.0, 12.0)
    tip = closed_rectangle_section(work_part, 40.0, 12.0, 8.0)

    builder = work_part.Features.CreateThroughCurvesBuilder(NXOpen.Features.Feature.Null)
    try:
        builder.BodyPreference = NXOpen.Features.ThroughCurvesBuilder.BodyPreferenceTypes.Solid
        builder.SectionsList.Append([root, tip])
        feature = builder.CommitFeature()
        print("NXCAD_FEATURE_COMMITTED:", feature)
    finally:
        builder.Destroy()


def main():
    run_probe(__file__, "NX 2606", "through_curves_solid", 1, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
