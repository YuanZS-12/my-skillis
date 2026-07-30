"""Experimental user-run NX 2606 StyledSweep rotation-set probe.

This tests a materially different twist API from the rejected
SweptBuilder/SweptBuilder1 ByAngularLaw configurations. The user must run it
manually from the NX UI; MCP review is API evidence, not runtime evidence.
"""

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities

from _probe_support import add_curves_to_section, closed_rectangle_section, run_probe


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "manual_user_run_required": True, "agent_execution": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {
    "recipe": "nx2606.styled-sweep.rotation-sets",
    "status": "experimental",
    "runtime": "manual NX UI run required",
    "api_family": "NXOpen.Features.StyledSweepBuilder",
    "not_by_angular_law": True,
}
DESIGN_LEDGER = {
    "target_nx_version": "NX 2606",
    "expected_body_count": 1,
    "critical_features": ["styled_sweep_rotation_sets_twist"],
    "section_count": 1,
    "guide_count": 1,
    "rotation_sets": [{"path_parameter": 0.0, "degrees": 0.0}, {"path_parameter": 1.0, "degrees": 20.0}],
}


def require_attribute(value, name):
    if not hasattr(value, name):
        raise RuntimeError(
            "%s does not expose required StyledSweep attribute %s"
            % (type(value).__name__, name)
        )
    return getattr(value, name)


def operation(session, work_part, report):
    section = closed_rectangle_section(work_part, 0.0, 10.0, 5.0)
    guide_start = NXOpen.Point3d(10.0, 5.0, 0.0)
    guide_end = NXOpen.Point3d(10.0, 5.0, 40.0)
    guide_curve = work_part.Curves.CreateLine(guide_start, guide_end)

    builder = work_part.Features.CreateStyledSweepBuilder(
        NXOpen.Features.Feature.Null
    )
    commit_failed = False
    try:
        builder.Type = NXOpen.Features.StyledSweepBuilder.Types.OneGuide
        builder.SectionOrientationOption = (
            NXOpen.Features.StyledSweepBuilder.SectionOrientationOptions.UserDefined
        )
        section_list = require_attribute(builder, "SectionList")
        require_attribute(section_list, "Append")([section])
        first_guide = require_attribute(builder, "FirstGuide")
        add_curves_to_section(
            work_part, first_guide, [guide_curve], [guide_start]
        )

        rotation_set_list = require_attribute(builder, "RotationSetList")
        rotation_sets = [
            builder.CreateRotationSet(0.0, 0.0, guide_curve),
            builder.CreateRotationSet(20.0, 1.0, guide_curve),
        ]
        require_attribute(rotation_set_list, "Append")(rotation_sets)

        try:
            feature = builder.CommitFeature()
        except Exception:
            commit_failed = True
            raise
        print("NXCAD_FEATURE_COMMITTED:", feature)
    finally:
        try:
            builder.Destroy()
        except Exception as destroy_error:
            if not commit_failed:
                raise
            print("NXCAD_BUILDER_DESTROY_WARNING:", destroy_error)

    report["api_generation"] = "StyledSweepBuilder"
    report["rotation_set_count"] = 2
    report["rotation_set_degrees"] = [0.0, 20.0]
    report["by_angular_law"] = False
    report["experimental_candidate"] = True


def main():
    run_probe(
        __file__,
        "NX 2606",
        "11_styled_sweep_rotation_sets",
        1,
        operation,
        EXECUTION_POLICY,
        DESIGN_LEDGER["critical_features"],
    )


if __name__ == "__main__":
    main()
