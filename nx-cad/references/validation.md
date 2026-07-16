# NX CAD Validation

Read this before reporting success for generated NXOpen journals.

## Principle

Validation is layered. Local checks can prove source structure, route
consistency, and wrapper runtime freshness. They cannot prove Siemens NX
execution, native `.prt` save, STEP export, solid validity, or visual
correctness. Runtime validation may come from a user-run NX session or an
explicitly authorized `agent:dc_mcp` execution. In both cases the user prepares
NX, and the agent never launches or closes NX.

## Validation Hierarchy

### Wrapper Mode

1. Syntax/static check:

   ```bash
   skills/nx-cad/scripts/check-journal models/<journal>.py
   ```

2. Runtime wrapper sync when the journal imports `cadnx`:

   ```bash
   skills/nx-cad/scripts/sync-runtime --models-dir models
   skills/nx-cad/scripts/check-journal models/<journal>.py
   ```

3. Strict geometry static check when the journal has industrial/mechanical
   booleans, holes, ribs, bosses, slots, or patterned features:

   ```bash
   skills/nx-cad/scripts/check-journal models/<journal>.py --strict-geometry
   ```

4. Controlled Siemens NX execution: user-run, or authorized `mcp_execute`
   through `dc_run_journal` after static checks.
5. NX stdout, warnings, traceback, `.nxreport.json`, `.prt`, and `.step` paths.
6. Post-NX STEP inspection, snapshot, and CAD Viewer handoff of the actual
   NX-exported STEP.

### Raw NXOpen High-Fidelity Mode

1. Syntax/static check:

   ```bash
   skills/nx-cad/scripts/check-journal models/<journal>.py
   ```

2. MCP API-review evidence, or explicit `STATIC_ONLY_NXOPEN_REVIEW` if MCP
   tools were unavailable.
3. Check that `cadnx/` is not required by the journal.
4. Controlled user-run or authorized MCP Siemens NX execution.
5. NX stdout, warnings, traceback, body/feature diagnostics,
   `.prt` save, and `.step` export paths.
6. Post-NX STEP inspection, snapshot, and CAD Viewer handoff of the actual
   NX-exported STEP.

## What Local Checks Prove

`skills/nx-cad/scripts/check-journal` proves only the checks it implements:

- Python syntax is valid.
- Forbidden local CAD kernels are absent.
- Wrapper journals use `NXBuilder` entry points and STEP export calls.
- Raw NXOpen journals include `MCP_API_REVIEW` or
  `STATIC_ONLY_NXOPEN_REVIEW`.
- Raw high-fidelity journals do not use `cadnx.NXBuilder`.
- Raw journals include basic diagnostics and builder cleanup guardrails.
- Referenced `cadnx/` runtime files compile when the journal needs them.

It does not prove NX can commit the features or export a STEP.

For raw NXOpen evidence preflight during development, use:

```bash
skills/nx-cad/scripts/check-nxopen-api models/<journal>.py
```

This helper checks only raw NXOpen imports, evidence markers, and obvious raw
high-fidelity route violations. It does not replace `check-journal`.

## Brief-Level Validation Plan

Before coding, record in the design ledger:

- expected body or assembly-like body count;
- bounding dimensions and main axes;
- critical hole diameters, axes, and locations;
- major feature positions;
- whether cosmetic fillets, chamfers, colors, PMI, or annotations are required
  or optional;
- expected `.prt` and `.step` path behavior;
- what user-run NX output should prove.

## Raw NXOpen Evidence

Raw NXOpen evidence is required for generated or repaired raw `NXOpen.*`
journals.

When a generated or repaired journal uses raw `NXOpen.*`, the final response
must report one of:

- `MCP_API_REVIEW`: exact `dc_*` tools used and the API facts checked;
- `STATIC_ONLY_NXOPEN_REVIEW`: MCP tools were unavailable or not exposed, plus
  the local static checks that ran.

Do not imply MCP was used unless the final answer lists the actual `dc_*` calls.
Do not claim NX runtime success unless a controlled execution report and its
required artifact gates pass. Report PMI, annotation, color, or cosmetic
failures separately from primary solid-generation failures.

## Controlled NX Runtime Validation

After local checks, either hand the Journal to the user for manual execution or,
in explicitly authorized `mcp_execute`, call `dc_run_journal` according to
`references/mcp-runtime.md`. Capture:

- whether NX executed the journal;
- warnings, tracebacks, or diagnostic prints;
- committed feature/body counts when printed;
- whether native `.prt` save was reported;
- whether `.step` export was reported;
- output paths reported by the journal.

When the journal returns a structured report, validate it locally without
starting or operating NX:

```bash
skills/nx-cad/scripts/check-runtime-report \
  models/<journal>.nxreport.json \
  --expected-bodies 1 \
  --step models/<nx-exported>.step
```

Schema v1 reports must retain `manual_user_run=true` and
`agent_execution=false`. Schema v2 reports must use either `user:nx_ui` or an
explicitly authorized `agent:dc_mcp` execution provenance. Agent reports
require `tool=dc_run_journal` and `user_authorized=true`. Passing `--step`
independently rejects missing, empty, and metadata-only STEP files. Full CAD
inspection and snapshots remain required.

For the standard report + STEP + deterministic inspection workflow, use:

```bash
skills/nx-cad/scripts/post-nx-review \
  models/<journal>.nxreport.json \
  models/<nx-exported>.step \
  --expected-bodies 1 \
  --snapshot-output /tmp/<model>-iso.png
```

This local postprocessor validates returned evidence and invokes CAD inspection
and snapshot tools. It never starts or operates Siemens NX. CAD Viewer handoff
remains an explicit final agent workflow step after these gates pass.

For each aerospace regression run, also pass the returned PRT and write a
durable review record:

```bash
skills/nx-cad/scripts/post-nx-review \
  <report.nxreport.json> <returned.step> \
  --expected-bodies 1 \
  --prt <returned.prt> \
  --snapshot-output <run-dir>/iso.png \
  --evidence-output <run-dir>/post-nx-review.json
```

After three consecutive controlled NX sessions, validate their immutable review
records with:

```bash
skills/nx-cad/scripts/check-runtime-series \
  <fixture-id> \
  <run-001>/post-nx-review.json \
  <run-002>/post-nx-review.json \
  <run-003>/post-nx-review.json
```

The series checker verifies controlled execution provenance, success result, stable body
count, saved snapshot review, and unchanged PRT/STEP/snapshot hashes. It also
reopens every recorded STEP and independently rejects metadata-only payloads;
an evidence JSON flag cannot substitute for actual geometry. It never starts
NX.

After validation, a fixture may be promoted to `verified` only when its matrix
entry records the three distinct evidence paths in `run_evidence`. The strict
roadmap completion checker reruns `check-runtime-series` against those paths;
the numeric `consecutive_successes` field alone is not proof.

For wrapper mode, tell the user to copy the journal and sibling `cadnx/`.
For raw NXOpen high-fidelity mode, tell the user to copy only the journal unless
the generated source explicitly imports additional local files.

## Post-NX STEP Review

After Siemens NX reports that the native part saved and the NX-exported STEP
exists, treat that STEP as the primary review artifact. From the repository
root, run targeted CAD checks against the explicit output path:

```bash
skills/cad/scripts/inspect refs <nx-exported.step> --facts --planes --positioning
skills/cad/scripts/snapshot <nx-exported.step>
```

Then hand the same STEP to `$cad-viewer` when available. Snapshot and viewer
review are visual checks; convert visual concerns into measurements, source
changes, or explicit NX rerun requests before claiming them fixed.

## Reporting Shapes

### Wrapper Mode

```text
Mode: wrapper
Generated: models/<journal>.py
Runtime: models/cadnx/ synced or not required
Checks run: <commands and results>
Assumptions: <brief summary>
Copy to NX machine: models/<journal>.py and models/cadnx/
NX runtime: <not executed; manual run required | authorized dc_mcp result and gates>
```

### Raw NXOpen High-Fidelity Mode

```text
Mode: raw NXOpen high-fidelity
Generated: models/<journal>.py
Runtime: cadnx/ not required
Review evidence: MCP_API_REVIEW with <dc_* tools> or STATIC_ONLY_NXOPEN_REVIEW
Checks run: <commands and results>
Assumptions: <brief summary>
Copy to NX machine: models/<journal>.py
NX runtime: <not executed; manual run required | authorized dc_mcp result and gates>
```

### Post-NX STEP Review

```text
NX runtime evidence: <user:nx_ui or agent:dc_mcp stdout/paths/report>
STEP: <nx-exported.step>
Inspection: <facts/planes/measurements>
Snapshot: <path or skipped reason>
CAD Viewer: <link or unavailable reason>
Remaining risks: <unchecked claims>
```

## Claims Not Allowed Without Evidence

Do not claim:

- NX execution;
- `.prt` creation;
- STEP export;
- watertight solids;
- visual correctness;
- manufacturability;
- tolerance compliance;
- structural safety;

unless those facts are supported by controlled NX runtime evidence and the
applicable independent artifact inspection.
