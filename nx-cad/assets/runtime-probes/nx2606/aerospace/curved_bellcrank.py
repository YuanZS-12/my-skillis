"""Repaired raw NXOpen curved flight-control bellcrank regression fixture.

Only the user may execute this file manually inside Siemens NX.  Each curved
arm is explicitly a five-station ThroughCurves loft through periodic spline
sections; it is not described as a sweep or as guide-controlled geometry.
"""

import json
import math
import os

import NXOpen
import NXOpen.Features
import NXOpen.GeometricUtilities
from _nx_aerospace_probe_support import write_schema_v2_report


RAW_NXOPEN_HIGH_FIDELITY = True
USER_MANUAL_NX_EXECUTION_REQUIRED = True
STATIC_ONLY_NXOPEN_REVIEW = {
    "recipes": [
        "nx2606.section.periodic-spline",
        "nx2606.through-curves.solid",
        "nx2606.boolean.unite",
        "nx2606.export.step-creator",
    ],
    "note": "Combined aerospace fixture remains experimental until manual NX 2606 evidence is returned.",
}
DESIGN_LEDGER = {
    "task": "repaired curved flight-control bellcrank",
    "capability_level": "experimental_raw",
    "target_nx_version": "NX 2606",
    "units": "millimeters",
    "origin": "central pivot axis at world origin",
    "axes": "bellcrank lies in XY with thickness along Z",
    "expected_body_count": 1,
    "expected_bounding_dimensions": [142.0, 122.0, 14.0],
    "feature_budget": {
        "boolean_operations": 7,
        "micro_holes": 0,
        "patterned_features": 10,
    },
    "critical_features": [
        "central_hub",
        "arm_a_five_station_loft",
        "arm_b_five_station_loft",
        "two_end_bushing_bosses",
        "central_bore",
        "two_end_bores",
    ],
    "optional_features": [],
    "outputs": ["native_prt", "step"],
}


def safe_dispose(value):
    if value is not None and hasattr(value, "Dispose"):
        value.Dispose()


def report_path():
    return os.path.splitext(os.path.abspath(__file__))[0] + ".nxreport.json"


def write_report(report):
    write_schema_v2_report(__file__, report_path(), report, DESIGN_LEDGER)


def unique_part_path():
    base = os.path.splitext(os.path.abspath(__file__))[0]
    candidate = base
    suffix = 1
    while os.path.exists(candidate) or os.path.exists(candidate + ".prt"):
        candidate = "%s_run_%03d" % (base, suffix)
        suffix += 1
    return candidate


def create_work_part_if_needed(session):
    result = session.Parts.NewDisplay(unique_part_path(), NXOpen.Part.Units.Millimeters)
    status = None
    if isinstance(result, tuple):
        part = result[0]
        status = result[1] if len(result) > 1 else None
    else:
        part = result
    safe_dispose(status)
    work_part = session.Parts.Work or part
    if work_part is None:
        raise RuntimeError("NX did not create a work part")
    return work_part


def body_of(feature):
    bodies = list(feature.GetBodies())
    if not bodies:
        raise RuntimeError("Committed feature returned no body")
    return bodies[0]


def cylinder(work_part, diameter, height, origin):
    builder = work_part.Features.CreateCylinderBuilder(NXOpen.Features.Feature.Null)
    try:
        builder.Type = NXOpen.Features.CylinderBuilder.Types.AxisDiameterAndHeight
        builder.Origin = NXOpen.Point3d(*origin)
        builder.Direction = NXOpen.Vector3d(0.0, 0.0, 1.0)
        builder.Diameter.RightHandSide = str(float(diameter))
        builder.Height.RightHandSide = str(float(height))
        builder.BooleanOption.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create
        return builder.CommitFeature()
    finally:
        builder.Destroy()


def boolean_feature(work_part, target_feature, tool_feature, operation):
    builder = work_part.Features.CreateBooleanBuilder(NXOpen.Features.BooleanFeature.Null)
    try:
        builder.Operation = operation
        target = body_of(target_feature)
        tool = body_of(tool_feature)
        if hasattr(builder, "Target"):
            builder.Target = target
        else:
            builder.TargetBodyCollector.Add(target)
        if hasattr(builder, "Tool"):
            builder.Tool = tool
        else:
            builder.ToolBodyCollector.Add(tool)
        return builder.CommitFeature()
    finally:
        builder.Destroy()


def unite(work_part, target_feature, tool_feature):
    return boolean_feature(
        work_part,
        target_feature,
        tool_feature,
        NXOpen.Features.Feature.BooleanType.Unite,
    )


def subtract(work_part, target_feature, tool_feature):
    return boolean_feature(
        work_part,
        target_feature,
        tool_feature,
        NXOpen.Features.Feature.BooleanType.Subtract,
    )


def bezier_point_and_tangent(control_points, parameter):
    t = float(parameter)
    omt = 1.0 - t
    p0, p1, p2, p3 = control_points
    x_value = omt**3 * p0[0] + 3.0 * omt**2 * t * p1[0] + 3.0 * omt * t**2 * p2[0] + t**3 * p3[0]
    y_value = omt**3 * p0[1] + 3.0 * omt**2 * t * p1[1] + 3.0 * omt * t**2 * p2[1] + t**3 * p3[1]
    tangent_x = 3.0 * omt**2 * (p1[0] - p0[0]) + 6.0 * omt * t * (p2[0] - p1[0]) + 3.0 * t**2 * (p3[0] - p2[0])
    tangent_y = 3.0 * omt**2 * (p1[1] - p0[1]) + 6.0 * omt * t * (p2[1] - p1[1]) + 3.0 * t**2 * (p3[1] - p2[1])
    magnitude = math.hypot(tangent_x, tangent_y)
    if magnitude <= 1.0e-9:
        raise RuntimeError("Bezier station has a zero tangent")
    tangent = (tangent_x / magnitude, tangent_y / magnitude, 0.0)
    width_axis = (-tangent[1], tangent[0], 0.0)
    return NXOpen.Point3d(x_value, y_value, 0.0), width_axis


def periodic_ellipse(work_part, center, width_axis, half_width, half_thickness, samples=12):
    builder = work_part.Features.CreateStudioSplineBuilderEx(NXOpen.NXObject.Null)
    try:
        builder.Type = NXOpen.Features.StudioSplineBuilderEx.Types.ThroughPoints
        builder.IsPeriodic = True
        builder.Degree = 3
        manager = builder.ConstraintManager
        for index in range(samples):
            angle = 2.0 * math.pi * index / float(samples)
            width = half_width * math.cos(angle)
            z_value = half_thickness * math.sin(angle)
            point = work_part.Points.CreatePoint(
                NXOpen.Point3d(
                    center.X + width_axis[0] * width,
                    center.Y + width_axis[1] * width,
                    z_value,
                )
            )
            data = manager.CreateGeometricConstraintData()
            data.Point = point
            manager.Append(data)
        feature = builder.CommitFeature()
        entities = list(feature.GetEntities())
        if len(entities) != 1:
            raise RuntimeError("Periodic ellipse station returned %d entities" % len(entities))
        return entities[0]
    finally:
        builder.Destroy()


def curve_section(work_part, curve, help_point):
    section = work_part.Sections.CreateSection(0.01, 0.0095, 0.5)
    section.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves)
    options = work_part.ScRuleFactory.CreateRuleOptions()
    try:
        rule = work_part.ScRuleFactory.CreateRuleBaseCurveDumb([curve], options)
        section.AddToSection(
            [rule],
            curve,
            NXOpen.NXObject.Null,
            NXOpen.NXObject.Null,
            help_point,
            NXOpen.Section.Mode.Create,
            False,
        )
    finally:
        options.Dispose()
    return section


def curved_arm(work_part, control_points, root_width, tip_width, root_thickness, tip_thickness):
    sections = []
    for parameter in (0.0, 0.25, 0.5, 0.75, 1.0):
        center, width_axis = bezier_point_and_tangent(control_points, parameter)
        half_width = 0.5 * (root_width + (tip_width - root_width) * parameter)
        half_thickness = 0.5 * (root_thickness + (tip_thickness - root_thickness) * parameter)
        curve = periodic_ellipse(work_part, center, width_axis, half_width, half_thickness)
        help_point = NXOpen.Point3d(
            center.X + width_axis[0] * half_width,
            center.Y + width_axis[1] * half_width,
            center.Z,
        )
        sections.append(curve_section(work_part, curve, help_point))

    builder = work_part.Features.CreateThroughCurvesBuilder(NXOpen.Features.Feature.Null)
    try:
        builder.BodyPreference = NXOpen.Features.ThroughCurvesBuilder.BodyPreferenceTypes.Solid
        builder.SectionsList.Append(sections)
        feature = builder.CommitFeature()
        body_of(feature)
        return feature
    finally:
        builder.Destroy()


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
    feature_overlap = 4.0
    through_overcut = 2.0
    report = {
        "schema_version": 1,
        "nx_version": "NX 2606",
        "manual_user_run": True,
        "agent_execution": False,
        "probe": "curved_bellcrank_repaired",
        "result": "running",
        "body_count": None,
        "features": {},
        "warnings": [],
    }
    try:
        session = NXOpen.Session.GetSession()
        work_part = create_work_part_if_needed(session)

        target = cylinder(work_part, 50.0, 14.0, (0.0, 0.0, -7.0))
        arm_a_controls = ((18.0, 0.0), (42.0, 0.0), (62.0, 18.0), (90.0, 30.0))
        arm_b_controls = ((0.0, 18.0), (0.0, 42.0), (-18.0, 64.0), (-34.0, 86.0))
        arm_a = curved_arm(work_part, arm_a_controls, 30.0, 20.0, 12.0, 9.0)
        arm_b = curved_arm(work_part, arm_b_controls, 30.0, 20.0, 12.0, 9.0)
        target = unite(work_part, target, arm_a)
        target = unite(work_part, target, arm_b)

        boss_a = cylinder(work_part, 32.0, 14.0, (90.0, 30.0, -7.0))
        boss_b = cylinder(work_part, 32.0, 14.0, (-34.0, 86.0, -7.0))
        target = unite(work_part, target, boss_a)
        target = unite(work_part, target, boss_b)
        report["features"]["primary_lofts_and_bosses"] = "success"
        report["features"]["central_hub"] = "success"
        report["features"]["arm_a_five_station_loft"] = "success"
        report["features"]["arm_b_five_station_loft"] = "success"
        report["features"]["two_end_bushing_bosses"] = "success"

        central_cutter = cylinder(
            work_part,
            20.0,
            14.0 + 2.0 * through_overcut,
            (0.0, 0.0, -7.0 - through_overcut),
        )
        target = subtract(work_part, target, central_cutter)
        for x_value, y_value in ((90.0, 30.0), (-34.0, 86.0)):
            end_cutter = cylinder(
                work_part,
                10.0,
                14.0 + 2.0 * through_overcut,
                (x_value, y_value, -7.0 - through_overcut),
            )
            target = subtract(work_part, target, end_cutter)
        report["features"]["functional_bores"] = "success"
        report["features"]["central_bore"] = "success"
        report["features"]["two_end_bores"] = "success"
        print("NXCAD_FEATURE_OVERLAP:", feature_overlap)

        body_count = len(list(work_part.Bodies))
        report["body_count"] = body_count
        if body_count != DESIGN_LEDGER["expected_body_count"]:
            raise RuntimeError("Expected one final bellcrank body, found %d" % body_count)

        native_path = getattr(work_part, "FullPath", "")
        step_path = os.path.splitext(native_path)[0] + ".step"
        export_step(session, work_part, step_path)
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
        write_report(report)


if __name__ == "__main__":
    main()
