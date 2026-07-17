"""Experimental raw NXOpen aerospace curved-duct regression fixture.

Only the user may run this journal manually in Siemens NX via
File -> Execute -> NX Open.  The agent never starts or operates NX.

The solid is a station-only ThroughCurves loft through five annular periodic
B-spline sections.  It deliberately does not claim guide-controlled sweep
geometry.  Runtime promotion requires a returned report and inspected STEP.
"""

import json
import math
import os

import NXOpen
import NXOpen.Features
from _nx_aerospace_probe_support import write_schema_v2_report


RAW_NXOPEN_HIGH_FIDELITY = True
USER_MANUAL_NX_EXECUTION_REQUIRED = True
EXECUTION_POLICY = {
    "mode": "mcp_review",
    "manual_user_run_required": True,
    "agent_execution": False,
    "requires_prepared_nx_environment": True,
    "allow_launch_or_close_nx": False,
    "allow_existing_work_part": False,
    "allow_overwrite": False,
    "managed_mode": False,
    "max_repair_attempts": 3,
}
STATIC_ONLY_NXOPEN_REVIEW = {
    "recipes": [
        "nx2606.section.periodic-spline",
        "nx2606.through-curves.solid",
        "nx2606.export.step-creator",
    ],
    "note": "The combined annular five-station duct recipe remains experimental until a manual NX 2606 run.",
}
DESIGN_LEDGER = {
    "task": "aerospace curved bleed-air duct regression fixture",
    "capability_level": "experimental_raw",
    "target_nx_version": "NX 2606",
    "units": "millimeters",
    "origin": "bend center at world origin",
    "axes": "duct centerline lies in XZ; section width is along Y",
    "expected_body_count": 1,
    "expected_bounding_dimensions": [66.0, 36.0, 66.0],
    "feature_budget": {
        "boolean_operations": 0,
        "micro_holes": 0,
        "patterned_features": 5,
    },
    "critical_features": [
        "five_annular_periodic_spline_sections",
        "station_only_through_curves_duct",
        "continuous_internal_passage",
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


def station_frame(angle_degrees, centerline_radius):
    angle = math.radians(angle_degrees)
    center = NXOpen.Point3d(
        centerline_radius * math.cos(angle),
        0.0,
        centerline_radius * math.sin(angle),
    )
    # Local section basis: u follows global Y; v is radial in the bend plane.
    u_axis = (0.0, 1.0, 0.0)
    v_axis = (math.cos(angle), 0.0, math.sin(angle))
    return center, u_axis, v_axis


def periodic_spline(work_part, center, u_axis, v_axis, radius, samples=12):
    builder = work_part.Features.CreateStudioSplineBuilderEx(NXOpen.NXObject.Null)
    try:
        builder.Type = NXOpen.Features.StudioSplineBuilderEx.Types.ThroughPoints
        builder.IsPeriodic = True
        builder.Degree = 3
        manager = builder.ConstraintManager
        for index in range(samples):
            angle = 2.0 * math.pi * index / float(samples)
            u_scale = radius * math.cos(angle)
            v_scale = radius * math.sin(angle)
            point = work_part.Points.CreatePoint(
                NXOpen.Point3d(
                    center.X + u_axis[0] * u_scale + v_axis[0] * v_scale,
                    center.Y + u_axis[1] * u_scale + v_axis[1] * v_scale,
                    center.Z + u_axis[2] * u_scale + v_axis[2] * v_scale,
                )
            )
            data = manager.CreateGeometricConstraintData()
            data.Point = point
            manager.Append(data)
        feature = builder.CommitFeature()
        entities = list(feature.GetEntities())
        if len(entities) != 1:
            raise RuntimeError("Periodic spline station returned %d curve entities" % len(entities))
        return entities[0]
    finally:
        builder.Destroy()


def annular_section(work_part, center, u_axis, v_axis, outer_radius, inner_radius):
    section = work_part.Sections.CreateSection(0.01, 0.0095, 0.5)
    section.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves)
    options = work_part.ScRuleFactory.CreateRuleOptions()
    try:
        for radius in (outer_radius, inner_radius):
            curve = periodic_spline(work_part, center, u_axis, v_axis, radius)
            rule = work_part.ScRuleFactory.CreateRuleBaseCurveDumb([curve], options)
            help_point = NXOpen.Point3d(
                center.X + u_axis[0] * radius,
                center.Y + u_axis[1] * radius,
                center.Z + u_axis[2] * radius,
            )
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


def create_duct(work_part):
    centerline_radius = 48.0
    outer_radius = 18.0
    wall_thickness = 2.5
    inner_radius = outer_radius - wall_thickness
    if inner_radius <= 0.0:
        raise ValueError("wall_thickness must leave a positive inner passage")

    sections = []
    for station_angle in (0.0, 22.5, 45.0, 67.5, 90.0):
        center, u_axis, v_axis = station_frame(station_angle, centerline_radius)
        sections.append(
            annular_section(work_part, center, u_axis, v_axis, outer_radius, inner_radius)
        )

    builder = work_part.Features.CreateThroughCurvesBuilder(NXOpen.Features.Feature.Null)
    try:
        builder.BodyPreference = NXOpen.Features.ThroughCurvesBuilder.BodyPreferenceTypes.Solid
        builder.SectionsList.Append(sections)
        feature = builder.CommitFeature()
        if not feature.GetBodies():
            raise RuntimeError("ThroughCurves duct returned no body")
        return feature
    finally:
        builder.Destroy()


def export_step(session, work_part, output_path):
    status = work_part.Save(
        NXOpen.BasePart.SaveComponents.TrueValue,
        NXOpen.BasePart.CloseAfterSave.FalseValue,
    )
    safe_dispose(status)
    input_path = getattr(work_part, "FullPath", "")
    if not input_path or not os.path.isfile(input_path):
        raise RuntimeError("Saved NX part was not found for STEP export: " + input_path)
    creator = session.DexManager.CreateStepCreator()
    try:
        creator.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242
        creator.ExportFrom = NXOpen.StepCreator.ExportFromOption.ExistingPart
        creator.InputFile = input_path
        creator.ObjectTypes.Solids = True
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
        "probe": "aerospace_curved_duct",
        "result": "running",
        "body_count": None,
        "features": {},
        "warnings": [],
    }
    try:
        session = NXOpen.Session.GetSession()
        work_part = create_work_part_if_needed(session)
        feature = create_duct(work_part)
        report["features"]["five_annular_periodic_spline_sections"] = "success"
        report["features"]["station_only_through_curves_duct"] = "success"
        report["features"]["continuous_internal_passage"] = "success"
        print("NXCAD_DUCT_FEATURE:", feature)

        body_count = len(list(work_part.Bodies))
        report["body_count"] = body_count
        if body_count != DESIGN_LEDGER["expected_body_count"]:
            raise RuntimeError("Expected one final duct body, found %d" % body_count)

        native_path = getattr(work_part, "FullPath", "")
        report["native_part"] = {
            "path": native_path,
            "exists": bool(native_path) and os.path.isfile(native_path),
        }
        step_path = os.path.splitext(native_path)[0] + ".step"
        export_step(session, work_part, step_path)
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
