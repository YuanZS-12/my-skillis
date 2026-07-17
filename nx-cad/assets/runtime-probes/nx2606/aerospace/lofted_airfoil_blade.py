import json
import math
import os

import NXOpen
import NXOpen.Features
from _nx_aerospace_probe_support import write_schema_v2_report


MCP_API_REVIEW = {
    "tools": ["dc_search", "dc_get_api_info"],
    "apis": [
        "NXOpen.Features.FeatureCollection.CreateThroughCurvesBuilder",
        "NXOpen.Features.ThroughCurvesBuilder",
        "NXOpen.Section",
    ],
    "note": "Static fixture for raw NXOpen loft journal checks; local tests do not execute NX.",
}
RAW_NXOPEN_HIGH_FIDELITY = True
USER_MANUAL_NX_EXECUTION_REQUIRED = True
DESIGN_LEDGER = {
    "task": "lofted NACA 0012 aerospace blade regression fixture",
    "capability_level": "experimental_raw",
    "target_nx_version": "NX 2606",
    "expected_body_count": 1,
    "expected_bounding_dimensions": [40.0, 4.8, 90.0],
    "feature_budget": {
        "boolean_operations": 0,
        "micro_holes": 0,
        "patterned_features": 3,
    },
    "critical_features": [
        "three_periodic_spline_airfoil_sections",
        "twisted_tapered_through_curves_blade",
    ],
    "optional_features": [],
    "outputs": ["native_prt", "step"],
}


def safe_dispose(value):
    if value is not None and hasattr(value, "Dispose"):
        value.Dispose()


def runtime_report_path():
    return os.path.splitext(os.path.abspath(__file__))[0] + ".nxreport.json"


def write_runtime_report(report):
    write_schema_v2_report(__file__, runtime_report_path(), report, DESIGN_LEDGER)


def naca0012_points(chord, samples=12):
    x_values = [0.5 * (1.0 - math.cos(math.pi * i / samples)) for i in range(samples + 1)]
    upper = []
    lower = []
    for x in x_values:
        yt = 5.0 * 0.12 * (
            0.2969 * math.sqrt(max(x, 0.0))
            - 0.1260 * x
            - 0.3516 * x**2
            + 0.2843 * x**3
            - 0.1015 * x**4
        )
        upper.append(((x - 0.25) * chord, yt * chord))
        lower.append(((x - 0.25) * chord, -yt * chord))
    return list(reversed(lower)) + upper[1:]


def transform_contour(contour, z_value, twist_degrees=0.0):
    angle = math.radians(twist_degrees)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    points = []
    for x_value, y_value in contour:
        points.append(
            NXOpen.Point3d(
                x_value * cosine - y_value * sine,
                x_value * sine + y_value * cosine,
                z_value,
            )
        )
    return points


def create_work_part_if_needed(the_session):
    base_path = os.path.splitext(os.path.abspath(__file__))[0]
    part_path = base_path
    suffix = 1
    while os.path.exists(part_path) or os.path.exists(part_path + ".prt"):
        part_path = "%s_run_%03d" % (base_path, suffix)
        suffix += 1
    result = the_session.Parts.NewDisplay(
        part_path,
        NXOpen.Part.Units.Millimeters,
    )
    load_status = None
    if isinstance(result, tuple):
        work_part = result[0]
        if len(result) > 1:
            load_status = result[1]
    else:
        work_part = result
    safe_dispose(load_status)
    return the_session.Parts.Work or work_part


def create_section_from_points(work_part, points_3d):
    spline_builder = work_part.Features.CreateStudioSplineBuilderEx(NXOpen.NXObject.Null)
    try:
        spline_builder.Type = NXOpen.Features.StudioSplineBuilderEx.Types.ThroughPoints
        spline_builder.IsPeriodic = True
        spline_builder.Degree = 3
        manager = spline_builder.ConstraintManager
        for coordinates in points_3d:
            point = work_part.Points.CreatePoint(coordinates)
            data = manager.CreateGeometricConstraintData()
            data.Point = point
            manager.Append(data)
        spline_feature = spline_builder.CommitFeature()
        entities = list(spline_feature.GetEntities())
        if len(entities) != 1:
            raise RuntimeError("Airfoil spline returned %d entities" % len(entities))
        curve = entities[0]
    finally:
        spline_builder.Destroy()

    section = work_part.Sections.CreateSection(0.01, 0.0095, 0.5)
    section.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves)
    rules_options = work_part.ScRuleFactory.CreateRuleOptions()
    try:
        rules_options.SetSelectedFromInactive(True)
        rule = work_part.ScRuleFactory.CreateRuleBaseCurveDumb([curve], rules_options)
        section.AddToSection(
            [rule],
            curve,
            NXOpen.NXObject.Null,
            NXOpen.NXObject.Null,
            points_3d[0],
            NXOpen.Section.Mode.Create,
            False,
        )
    finally:
        rules_options.Dispose()
    return section


def export_step(session, work_part, output_path):
    status = work_part.Save(
        NXOpen.BasePart.SaveComponents.TrueValue,
        NXOpen.BasePart.CloseAfterSave.FalseValue,
    )
    safe_dispose(status)
    creator = session.DexManager.CreateStepCreator()
    try:
        creator.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242
        creator.ExportFrom = NXOpen.StepCreator.ExportFromOption.DisplayPart
        creator.FileSaveFlag = False
        creator.ProcessHoldFlag = True
        creator.OutputFile = output_path
        creator.Commit()
    finally:
        creator.Destroy()
    if not os.path.isfile(output_path) or os.path.getsize(output_path) <= 0:
        raise RuntimeError("STEP export did not create a non-empty file: " + output_path)


def main():
    report = {
        "schema_version": 1,
        "nx_version": "NX 2606",
        "manual_user_run": True,
        "agent_execution": False,
        "probe": "lofted_airfoil_blade",
        "result": "running",
        "body_count": None,
        "features": {},
        "warnings": [],
    }
    try:
        the_session = NXOpen.Session.GetSession()
        work_part = create_work_part_if_needed(the_session)
        print("NXCAD_WORK_PART:", getattr(work_part, "FullPath", ""))

        root = create_section_from_points(work_part, transform_contour(naca0012_points(40.0), 0.0, 0.0))
        mid = create_section_from_points(work_part, transform_contour(naca0012_points(32.0), 45.0, -8.0))
        tip = create_section_from_points(work_part, transform_contour(naca0012_points(24.0), 90.0, -16.0))

        loft_builder = work_part.Features.CreateThroughCurvesBuilder(NXOpen.Features.Feature.Null)
        try:
            loft_builder.BodyPreference = NXOpen.Features.ThroughCurvesBuilder.BodyPreferenceTypes.Solid
            loft_builder.SectionsList.Append([root, mid, tip])
            blade_feature = loft_builder.CommitFeature()
            if not blade_feature.GetBodies():
                raise RuntimeError("ThroughCurves blade returned no body")
            print("NXCAD_BLADE_FEATURE:", blade_feature)
        finally:
            loft_builder.Destroy()
        report["features"]["three_periodic_spline_airfoil_sections"] = "success"
        report["features"]["twisted_tapered_through_curves_blade"] = "success"

        body_count = len(list(work_part.Bodies))
        report["body_count"] = body_count
        if body_count != DESIGN_LEDGER["expected_body_count"]:
            raise RuntimeError("Expected one final blade body, found %d" % body_count)

        native_path = getattr(work_part, "FullPath", "")
        step_path = os.path.splitext(native_path)[0] + ".step"
        export_step(the_session, work_part, step_path)
        report["native_part"] = {
            "path": native_path,
            "exists": bool(native_path) and os.path.isfile(native_path),
        }
        report["step"] = {
            "path": step_path,
            "exists": os.path.isfile(step_path),
            "size": os.path.getsize(step_path),
        }
        report["result"] = "success"
        print("NXCAD_RESULT: success")
    except Exception as exc:
        report["result"] = "failure"
        report["error"] = str(exc)
        print("NXCAD_RESULT: failure")
        raise
    finally:
        write_runtime_report(report)


if __name__ == "__main__":
    main()
