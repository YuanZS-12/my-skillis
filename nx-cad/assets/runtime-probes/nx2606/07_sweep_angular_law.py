"""User-run NX 2606 probe: SweptBuilder1 linear angular-law solid."""

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

from _probe_support import (
    add_line_to_section,
    closed_rectangle_section,
    closed_rotated_rectangle_section,
    line_section,
    run_probe,
)


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "manual_user_run_required": True, "agent_execution": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {
    "recipe": "nx2606.sweep.angular-law",
    "official_pages": ["a47559.html", "a56995.html", "a56867.html", "a56875.html"],
    "runtime": "manual user run required",
}
DESIGN_LEDGER = {
    "target_nx_version": "NX 2606",
    "expected_body_count": 1,
    "critical_features": ["swept_builder1_linear_angular_law_solid"],
}


def operation(session, work_part, report):
    root = closed_rectangle_section(work_part, 0.0, 10.0, 5.0)
    # The upper-right corner remains on the guide while the terminal section is
    # rotated 20 degrees around that guide, matching the angular-law endpoint.
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
        # ByAngularLaw requires an explicit spine in addition to the guide.
        # Populate the builder-owned Spine section and bind the law to it using
        # the official LawBuilder.SetSpineIntoBuilder contract.
        add_line_to_section(
            work_part,
            builder.Spine,
            NXOpen.Point3d(10.0, 5.0, 0.0),
            NXOpen.Point3d(10.0, 5.0, 40.0),
        )
        angular_law = builder.OrientationMethod.AngularLaw
        angular_law.SetSpineIntoBuilder(builder.Spine)
        angular_law.LawType = NXOpen.GeometricUtilities.LawBuilder.Type.Linear
        angular_law.StartValue.RightHandSide = "0"
        angular_law.EndValue.RightHandSide = "20"
        builder.OrientationMethod.OrientationOption = (
            NXOpen.GeometricUtilities.OrientationMethodBuilder.OrientationOptions.ByAngularLaw
        )
        feature = builder.CommitFeature()
        print("NXCAD_FEATURE_COMMITTED:", feature)
    finally:
        builder.Destroy()
    report["api_generation"] = "SweptBuilder1"
    report["angular_law_degrees"] = [0.0, 20.0]
    report["section_count"] = 2
    report["angular_law_spine"] = True


def main():
    run_probe(__file__, "NX 2606", "07_sweep_angular_law", 1, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
