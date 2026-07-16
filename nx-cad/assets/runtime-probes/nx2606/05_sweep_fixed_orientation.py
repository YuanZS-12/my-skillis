"""User-run NX 2606 probe: SweptBuilder1 fixed-orientation solid."""

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

from _probe_support import closed_rectangle_section, line_section, run_probe


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "user_authorized": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {
    "recipe": "nx2606.sweep.fixed-orientation",
    "official_pages": ["a47559.html", "a44599.html", "a56995.html", "a56735.html"],
    "runtime": "manual user run required",
}
DESIGN_LEDGER = {
    "target_nx_version": "NX 2606",
    "expected_body_count": 1,
    "critical_features": ["swept_builder1_fixed_orientation_solid"],
}


def operation(session, work_part, report):
    root = closed_rectangle_section(work_part, 0.0, 10.0, 5.0)
    tip = closed_rectangle_section(work_part, 40.0, 10.0, 5.0)
    # The first manual run showed that a one-section guide could not be
    # approximated in NX 2606. Keep the same fixed orientation and add only an
    # identical terminal section, matching the two-section contract proved by
    # probe 06.
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
        builder.OrientationMethod.OrientationOption = (
            NXOpen.GeometricUtilities.OrientationMethodBuilder.OrientationOptions.Fixed
        )
        builder.ScalingMethod.ScalingOption = (
            NXOpen.GeometricUtilities.ScalingMethodBuilder.ScalingOptions.Constant
        )
        feature = builder.CommitFeature()
        print("NXCAD_FEATURE_COMMITTED:", feature)
    finally:
        builder.Destroy()
    report["api_generation"] = "SweptBuilder1"
    report["orientation"] = "Fixed"
    report["section_count"] = 2


def main():
    run_probe(__file__, "NX 2606", "05_sweep_fixed_orientation", 1, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
