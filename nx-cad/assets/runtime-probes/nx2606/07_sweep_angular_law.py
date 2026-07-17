"""User-run NX 2606 probe: two-section tapered twisted solid.

NX 2606 rejected every tested SweptBuilder/SweptBuilder1 ByAngularLaw
configuration with ``Invalid orientation method specified``. This verified
fallback encodes the 20-degree twist in the terminal section geometry and uses
the compatible SweptBuilder1 two-section recipe.
"""

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

from _probe_support import (
    closed_rectangle_section,
    closed_rotated_rectangle_section,
    line_section,
    run_probe,
)


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "manual_user_run_required": True, "agent_execution": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {
    "recipe": "nx2606.sweep.rotated-section-twist",
    "runtime": "manual user run verified; MCP review is injected only into a fresh workspace copy",
    "rejected_alternative": "nx2606.sweep.angular-law",
}
DESIGN_LEDGER = {
    "target_nx_version": "NX 2606",
    "expected_body_count": 1,
    "critical_features": ["swept_builder1_two_section_twisted_solid"],
    "twist_strategy": "rotated terminal section; ByAngularLaw rejected for tested NX 2606 configurations",
}


def operation(session, work_part, report):
    root = closed_rectangle_section(work_part, 0.0, 10.0, 5.0)
    # Keep the guide corner fixed while rotating the terminal section 20
    # degrees, so the twist comes from section correspondence rather than the
    # rejected ByAngularLaw orientation method.
    tip = closed_rotated_rectangle_section(
        work_part, 40.0, 10.0, 5.0, 10.0, 5.0, 20.0
    )
    guide = line_section(
        work_part,
        NXOpen.Point3d(10.0, 5.0, 0.0),
        NXOpen.Point3d(10.0, 5.0, 40.0),
    )

    builder = work_part.Features.FreeformSurfaceCollection.CreateSweptBuilder1(
        NXOpen.Features.Swept.Null
    )
    try:
        builder.BodyPreference.BodyType = NXOpen.GeometricUtilities.FeatureOptions.BodyStyle.Solid
        builder.SectionList.Append([root, tip])
        builder.GuideList.Append(guide)
        builder.G0Tolerance = 0.01
        builder.InterpolationOption = NXOpen.Features.SweptBuilder1.InterpolationOptions.Linear
        feature = builder.CommitFeature()
        print("NXCAD_FEATURE_COMMITTED:", feature)
    finally:
        builder.Destroy()
    report["api_generation"] = "SweptBuilder1"
    report["section_twist_degrees"] = [0.0, 20.0]
    report["section_count"] = 2
    report["by_angular_law"] = False


def main():
    run_probe(__file__, "NX 2606", "07_sweep_angular_law", 1, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
