"""User-run NX 2606 probe: periodic StudioSplineBuilderEx curve."""

import math

import NXOpen
import NXOpen.Features

from _probe_support import run_probe


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "manual_user_run_required": True, "agent_execution": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {"recipe": "nx2606.section.periodic-spline", "runtime": "manual user run required"}
DESIGN_LEDGER = {"target_nx_version": "NX 2606", "expected_body_count": 0, "critical_features": ["periodic_spline"]}


def operation(session, work_part, report):
    builder = work_part.Features.CreateStudioSplineBuilderEx(NXOpen.NXObject.Null)
    try:
        builder.Type = NXOpen.Features.StudioSplineBuilderEx.Types.ThroughPoints
        builder.IsPeriodic = True
        builder.Degree = 3
        manager = builder.ConstraintManager
        for index in range(8):
            angle = 2.0 * math.pi * index / 8.0
            point = work_part.Points.CreatePoint(
                NXOpen.Point3d(20.0 * math.cos(angle), 12.0 * math.sin(angle), 0.0)
            )
            data = manager.CreateGeometricConstraintData()
            data.Point = point
            manager.Append(data)
        feature = builder.CommitFeature()
        entities = feature.GetEntities()
        if not entities:
            raise RuntimeError("Periodic spline feature returned no curve entity")
        report["curve_entity_count"] = len(entities)
        print("NXCAD_PERIODIC_SPLINE_CREATED:", len(entities))
    finally:
        builder.Destroy()


def main():
    run_probe(__file__, "NX 2606", "03_closed_spline_section", 0, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
