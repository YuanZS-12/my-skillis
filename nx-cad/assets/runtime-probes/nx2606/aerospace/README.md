# NX 2606 Aerospace Qualification Probes

These probes are prepared for user execution from the Siemens NX UI. They do
not authorize agent-controlled NX execution.

| Fixture | Journal | Runtime dependency |
| --- | --- | --- |
| bearing support | `bearing_support_housing.py` | sibling `cadnx/` and `_nx_aerospace_probe_support.py` |
| frame | `aerospace_hpc_rear_frame.py` | sibling `cadnx/` and `_nx_aerospace_probe_support.py` |
| linkage | `curved_bellcrank.py` | sibling `_nx_aerospace_probe_support.py` |
| duct | `curved_aerospace_duct.py` | sibling `_nx_aerospace_probe_support.py` |
| blade | `lofted_airfoil_blade.py` | sibling `_nx_aerospace_probe_support.py` |

For each attempt, copy the entire `aerospace/` directory to a new workspace
whose name ends in a unique numeric sequence, such as
`aerospace_bearing_001`. Do not reuse an earlier workspace. The directory
suffix becomes the schema-v2 `run_id`; `NXCAD_RUN_ID=run_001` may be used when
the NX UI environment supports setting it explicitly.

Before manual execution, complete the NX-machine API review described in
`references/mcp-runtime.md`, then use `prepare-dc-mcp-journal` with the saved
review JSON to create the workspace Journal. For bearing support and frame the
preparation command copies the required sibling `cadnx/` package automatically.
Run `check-journal --strict-geometry` on the workspace journal. The user must
execute the checked journal through
**File > Execute > NX Open**. Return the journal, `.nxreport.json`, `.prt`,
`.step`, translator/console log, and snapshot inputs without deleting or
overwriting any earlier artifact.

The report records `source_sha256`. Three formal runs qualify only when
`check-runtime-series` confirms the same source hash, ordered distinct run IDs,
distinct artifact paths, user/NX-UI provenance, critical features, and real
STEP geometry for all three runs.
