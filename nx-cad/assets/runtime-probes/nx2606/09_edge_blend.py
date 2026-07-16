"""User-run NX 2606 probe: constant-radius blend on a cylinder edge chain."""

import NXOpen
import NXOpen.Features

from _probe_support import body_of, cylinder, run_probe


RAW_NXOPEN_HIGH_FIDELITY = True
EXECUTION_POLICY = {"mode": "mcp_review", "manual_user_run_required": True, "agent_execution": False, "requires_prepared_nx_environment": True, "allow_launch_or_close_nx": False, "allow_existing_work_part": False, "allow_overwrite": False, "managed_mode": False, "max_repair_attempts": 3}
STATIC_ONLY_NXOPEN_REVIEW = {"recipe": "nx2606.edge-blend.chainset", "runtime": "manual user run required"}
DESIGN_LEDGER = {"target_nx_version": "NX 2606", "expected_body_count": 1, "critical_features": ["edge_blend"]}


def operation(session, work_part, report):
    solid = cylinder(work_part, 30.0, 20.0)
    edges = list(body_of(solid).GetEdges())
    if not edges:
        raise RuntimeError("Cylinder returned no selectable edges")
    builder = work_part.Features.CreateEdgeBlendBuilder(None)
    try:
        collector = work_part.ScCollectors.CreateCollector()
        rule = work_part.ScRuleFactory.CreateRuleEdgeDumb([edges[0]])
        collector.ReplaceRules([rule], False)
        builder.AddChainset(collector, "2.0")
        feature = builder.CommitFeature()
        report["selected_edge_count"] = 1
        print("NXCAD_EDGE_BLEND_COMMITTED:", feature)
    finally:
        builder.Destroy()


def main():
    run_probe(__file__, "NX 2606", "09_edge_blend", 1, operation, EXECUTION_POLICY, DESIGN_LEDGER["critical_features"])


if __name__ == "__main__":
    main()
