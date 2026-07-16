"""User-run NX 2606 probe: construct one closed four-curve Section."""

import NXOpen
import NXOpen.Features

from _probe_support import run_probe


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "manual_user_run_required": True, "agent_execution": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {"recipe": "nx2606.section.closed-polyline", "runtime": "manual user run required"}
DESIGN_LEDGER = {"target_nx_version": "NX 2606", "expected_body_count": 0, "critical_features": ["closed_section"]}


def operation(session, work_part, report):
    points = [
        NXOpen.Point3d(-10.0, -5.0, 0.0),
        NXOpen.Point3d(10.0, -5.0, 0.0),
        NXOpen.Point3d(10.0, 5.0, 0.0),
        NXOpen.Point3d(-10.0, 5.0, 0.0),
    ]
    section = work_part.Sections.CreateSection(0.01, 0.0095, 0.5)
    section.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves)
    options = work_part.ScRuleFactory.CreateRuleOptions()
    try:
        for index, start in enumerate(points):
            curve = work_part.Curves.CreateLine(start, points[(index + 1) % len(points)])
            rule = work_part.ScRuleFactory.CreateRuleBaseCurveDumb([curve], options)
            section.AddToSection([rule], curve, NXOpen.NXObject.Null, NXOpen.NXObject.Null,
                                 start, NXOpen.Section.Mode.Create, False)
    finally:
        options.Dispose()
    report["section_curve_count"] = 4
    print("NXCAD_SECTION_CREATED: 4 curves")


def main():
    run_probe(__file__, "NX 2606", "02_closed_polyline_section", 0, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
