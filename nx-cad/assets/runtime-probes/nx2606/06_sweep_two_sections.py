"""User-run NX 2606 probe: SweptBuilder1 two-section tapered solid."""

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

from _probe_support import closed_rectangle_section, line_section, run_probe


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "manual_user_run_required": True, "agent_execution": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {
    "recipe": "nx2606.sweep.two-sections",
    "official_pages": ["a47559.html", "a44599.html", "a06455.html"],
    "runtime": "manual user run required",
}
DESIGN_LEDGER = {
    "target_nx_version": "NX 2606",
    "expected_body_count": 1,
    "critical_features": ["swept_builder1_two_section_tapered_solid"],
}


def operation(session, work_part, report):
    root = closed_rectangle_section(work_part, 0.0, 10.0, 5.0)
    tip = closed_rectangle_section(work_part, 40.0, 6.0, 3.0)
    # A single diagonal guide intersects corresponding upper-right corners of
    # both sections, making section-to-guide correspondence explicit.
    guide = line_section(
        work_part,
        NXOpen.Point3d(10.0, 5.0, 0.0),
        NXOpen.Point3d(6.0, 3.0, 40.0),
    )

    builder = work_part.Features.FreeformSurfaceCollection.CreateSweptBuilder1(
        NXOpen.Features.Swept.Null
    )
    try:
        builder.BodyPreference.BodyType = NXOpen.GeometricUtilities.FeatureOptions.BodyStyle.Solid
        builder.SectionList.Append([root, tip])
        builder.GuideList.Append(guide)
        builder.OrientationMethod.OrientationOption = (
            NXOpen.GeometricUtilities.OrientationMethodBuilder.OrientationOptions.Fixed
        )
        feature = builder.CommitFeature()
        print("NXCAD_FEATURE_COMMITTED:", feature)
    finally:
        builder.Destroy()
    report["api_generation"] = "SweptBuilder1"
    report["section_count"] = 2


def main():
    run_probe(__file__, "NX 2606", "06_sweep_two_sections", 1, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
