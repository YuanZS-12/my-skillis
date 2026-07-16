# NX CAD Repair Loop

Read this when a generated NX journal fails locally, in Siemens NX, during
runtime wrapper import, during modeling, during save, or during STEP export.

## Loop

1. Read the exact failing command output or Siemens NX traceback.
2. Classify the failure using the classes below.
3. Patch the smallest responsible section of the generated journal or
   `cadnx.NXBuilder` wrapper.
4. Use MCP API-review tools, when available, for suspect NXOpen classes,
   builders, enums, properties, methods, creators, or known Designcenter
   patterns.
5. Run local static gates:

   ```bash
   skills/nx-cad/scripts/check-journal models/<journal>.py
   ```

   For wrapper-mode changes or wrapper repairs:

   ```bash
   skills/nx-cad/scripts/sync-runtime --models-dir models
   skills/nx-cad/scripts/check-journal models/<journal>.py
   ```

   For boolean-heavy repairs:

   ```bash
   skills/nx-cad/scripts/check-journal models/<journal>.py --strict-geometry
   ```

6. In explicitly authorized `mcp_execute`, rerun through `dc_run_journal` only
   after static checks, using a new run ID and no-overwrite outputs. Otherwise
   ask the user to rerun manually. Never launch or close NX.
7. Stop after three repair attempts or after the same root cause occurs twice
   without new API evidence. Preserve the full traceback or success output.
8. Record durable compatibility lessons in
   `references/nxopen-common-errors.md` or
   `references/nx-runtime-feedback-ledger.md` when they help future repairs.

## MCP Repair Boundaries

Automatically repair only a local, evidence-backed API, builder lifecycle,
path, output-collision, section/collector, or known version-compatibility
problem. Stop for geometry-intent changes, production-part mutation,
Teamcenter managed mode, overwrite requests, infrastructure failures, or
visual/engineering decisions.

MCP exit code 0 is not a completed repair. Require a valid runtime report,
expected body count, critical-feature success, and actual required artifacts.

## Failure Classes

### Import Or Path Failure

Likely causes:

- wrapper journal copied without sibling `cadnx/`;
- raw journal accidentally imports `cadnx`;
- journal run with normal Python instead of inside NX;
- stale `cadnx/builder.py` on the NX machine;
- hardcoded local Mac or Windows path.

Fix:

- sync and copy `cadnx/` only for wrapper mode;
- remove `cadnx` imports from raw high-fidelity journals;
- keep paths relative to `__file__`;
- tell the user which exact files belong on the NX machine.

### Missing NXOpen Submodule

Likely causes:

- journal imports `NXOpen` but uses `NXOpen.Features`,
  `NXOpen.Annotations`, `NXOpen.UF`, or `NXOpen.Assemblies` without explicit
  submodule import;
- raw journal copied from a recorded journal with implicit imports.

Fix:

- add explicit submodule imports;
- use `dc_get_api_info` when MCP is available to confirm the namespace;
- rerun `check-journal`.

### Wrong Enum, Property, Or Method Name

Likely causes:

- NX version exposes different enum or property names;
- recorded journal API is version-specific;
- builder collection shape differs from examples.

Fix:

- use MCP API-review tools to inspect the exact API shape;
- patch the generated raw journal when the call is one-off;
- patch `cadnx/builder.py` when the failing API is inside a reusable wrapper
  operation;
- keep working fallbacks when adding compatibility branches.

### Work-Part Creation Failure

Likely causes:

- no active work part and journal assumes one;
- `NewDisplay` return shape differs;
- load status object was not handled or disposed;
- output directory is not writable.

Fix:

- add or repair `create_work_part_if_needed(session)`;
- handle tuple and non-tuple `NewDisplay` returns;
- dispose load/status objects when present;
- create writable output paths beside the journal.

### Builder Lifecycle Or Commit Failure

Likely causes:

- builder property missing or invalid;
- section/body/input collector incomplete;
- `Commit()` or `CommitFeature()` called before required inputs are attached;
- builder not destroyed after failure.

Fix:

- use `try/finally` with `Destroy()`;
- review builder inputs through MCP;
- print diagnostics before and after commit;
- reduce the feature to the smallest failing builder sequence.

### Curve, Section, Or Rule Construction Failure

Likely causes:

- open or self-intersecting section;
- curve rule factory method mismatch;
- section tolerance too tight;
- help point or section mode invalid.

Fix:

- verify point order and closed loops;
- use MCP API review for `Section`, `ScRuleFactory`, curve rules, and section
  append calls;
- loosen tolerances conservatively;
- separate curve creation from feature builder commit for diagnostics.

### Boolean Failure

Likely causes:

- subtractive tool misses the target;
- union touches only at a face or tangent edge;
- target or tool body is not the expected body;
- feature order created fragile topology.

Fix:

- add `feature_overlap`, `cutter_overlap`, or `through_overcut`;
- build primary solids before details;
- simplify the failing feature;
- rerun strict geometry checks.

### Edge Or Face Selection Failure

Likely causes:

- topology index assumptions;
- multiple similar faces or edges;
- fillets/chamfers changed topology before later selection.

Fix:

- select by axis, bounding box, point proximity, face normal, or stable datum;
- add runtime diagnostics for selected counts;
- defer cosmetic details until after functional features.

### Fillet, Chamfer, Or Blend Failure

Likely causes:

- radius or offset exceeds local geometry;
- selected edge group includes tiny or unintended edges;
- one global blend crosses complex boolean topology.

Fix:

- reduce radius or offset;
- split edge groups;
- use narrower selectors;
- make cosmetic failures nonblocking only when the primary geometry is valid.

### PMI, Annotation, Color, Or Cosmetic Failure

Likely causes:

- annotation builder API differs by NX version;
- modeling view not found;
- associativity target face is invalid;
- optional visual detail ran before primary solid was safely committed.

Fix:

- wrap optional PMI/color/cosmetic helpers so failures print warnings and do
  not erase primary geometry;
- add explicit `NXOpen.Annotations` import when used;
- report optional failure separately from primary model failure.

### Save Failure

Likely causes:

- work part has no valid path;
- target directory is not writable;
- display part differs from work part;
- NX save status object is unhandled.

Fix:

- save near the journal or under `_cadnx_work/`;
- dispose save/load status objects when present;
- print native part path;
- do not claim `.prt` save until NX reports it.

### STEP Export Failure

Likely causes:

- STEP creator method or property differs by NX version;
- input part path is missing because save failed;
- output path is not writable;
- exporter not destroyed after failure.

Fix:

- use MCP review for STEP creator class, properties, and commit method;
- ensure native save path exists before export when required by the exporter;
- derive output path from `__file__`;
- destroy exporter in `finally`;
- report STEP failure separately from successful part creation.

### Generated Artifact Path Mismatch

Likely causes:

- journal exported beside NX work part instead of beside journal;
- user copied only part of the required folder;
- local Mac path leaked into generated source;
- reported STEP path is outside `models/`.

Fix:

- resolve paths from `__file__`;
- print all output paths in the journal;
- ask user for the exact NX stdout path before inspecting post-NX artifacts.

## Patch Decision

| Failure | Patch first |
| --- | --- |
| Raw journal API call, enum, property, section, PMI, or STEP creator | generated journal plus MCP review |
| Wrapper API compatibility | `cadnx/builder.py` |
| Boolean tangent or no complete intersection | generated journal geometry plan |
| Wrong wall guard or impossible parameter | generated journal parameters/checker guidance |
| Route violation such as raw mode using `NXBuilder` | generated journal and skill routing |
| STEP exists but looks wrong | source journal after CAD inspect/snapshot evidence |

Patch `cadnx/builder.py` when:

- two or more models can hit the same NXOpen compatibility issue;
- the failing API is inside a wrapper operation;
- the generated source used documented wrapper calls correctly.

Patch the generated journal when:

- raw NXOpen code owns the failing API;
- the feature plan is too fragile or too ambitious;
- the selected edge or face set is wrong;
- a dimension, axis, or datum in the model brief was interpreted incorrectly.

## Report After Repair

Tell the user:

- which file changed;
- whether `cadnx/` is required or synced;
- which local checks ran;
- which `dc_*` tools were used for API review, if MCP API-review mode was
  available;
- which file or folder to copy to the NX machine;
- what the next manual or authorized MCP NX rerun should prove.
