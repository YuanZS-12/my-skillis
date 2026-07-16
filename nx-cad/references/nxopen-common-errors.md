# NXOpen Common Errors

## ModuleNotFoundError: No module named 'NXOpen'

Cause:

- The journal was run with normal Python instead of Siemens NX Python or NX journal runner.

Fix:

- Run manually through NX File -> Execute -> NX Open. Do not call
  `dc_run_journal` or launch NX through a batch helper.
- Or run it from Siemens NX: File > Execute > NX Open.

## NoneType work part

Cause:

- No active work part exists.

Fix:

- Create a new part first.
- Or instruct the user to open an existing part.

## Builder commit failure

Cause:

- Missing required builder property.
- Invalid section, plane, direction, or expression.
- Wrong NXOpen API for the user's NX version.

Fix:

- Use a recorded NX journal from the same NX version.
- Ensure all builder inputs are assigned before `Commit()`.

## Zero-wall or touch-condition boolean failure

Cause:

- A subtractive cutter starts exactly on a face created by an earlier cut.
- A union feature sits exactly on top of a target face without volume overlap.
- A slot, keyway, pocket, or raised detail is tangent to another feature.
- The requested feature spacing leaves no positive wall thickness.

Fix:

- Add named `cutter_overlap` for subtractive tools that open into bores,
  pockets, or slots.
- Add named `feature_overlap` for raised text, arrows, pads, ribs, bosses, and
  other `boolean_unite()` features.
- Reorder cuts only when the final cutter still has real overlap with the
  existing target; reordering alone does not fix exact tangent geometry.
- Calculate slot-to-hole and edge-distance budgets before generating the
  journal. Move, shrink, or skip decorative lightening cuts when the budget is
  negative.
- Patch the generated journal rather than `NXBuilder` when the failure is caused
  by model-specific feature placement.

## Side-direction rectangular_pocket failure

Cause:

- `NXBuilder.rectangular_pocket()` currently supports Z-axis pocket directions.
- A generated journal used it for a side-facing X or Y pocket.

Fix:

- For shallow side pockets, create an explicit `box()` cutter with
  `cutter_overlap` and subtract it with `boolean_subtract()`.
- Extend `rectangular_pocket()` only after the needed side-axis behavior is
  specified and statically checked.

## Feature budget too low for intentional stress test

Cause:

- `require_feature_budget()` was called with a model complexity estimate above
  the default maximum.
- The model may be an intentional stress test, or it may be over-detailed for a
  generated journal.

Fix:

- If the complexity is intentional, set model-specific
  `max_boolean_operations`, `max_micro_holes`, or `max_patterned_features`.
- If the complexity is accidental, reduce repeated booleans, simplify cosmetic
  details, or replace primitive-only complex geometry with a better helper.

## Wrong-direction wall guard

Cause:

- A generated journal compared a hole diameter against the cutter travel
  thickness instead of the actual remaining material direction.
- Common examples: pin holes through clevis ears and side bores through lugs.

Fix:

- Identify the hole axis first.
- Check wall thickness perpendicular to the hole axis.
- Add `require_edge_distance()` for end distance from the hole center to the
  nearest free edge.

## EdgeBlendBuilder has no AddConstantRadiusEdge

Cause:

- Some NXOpen Python bindings do not expose `EdgeBlendBuilder.AddConstantRadiusEdge`.
- Recorded journals for those versions usually create a selection collector,
  add an edge dumb rule, then call `EdgeBlendBuilder.AddChainset`.

Fix:

- Use `NXBuilder.fillet()`, which tries `AddConstantRadiusEdge` first and falls
  back to `ScCollector` plus `AddChainset`.
- If both APIs are unavailable in the user's NX version, the wrapper logs a
  warning and skips the cosmetic fillet so the main model can still export.

## Unable to apply blend

Cause:

- The requested fillet radius is too large for one or more selected edges.
- The selected edge set crosses small faces, sharp transitions, boolean seams,
  or topology where NX cannot build one continuous blend.

Fix:

- Keep generated fillet radii conservative.
- Use `NXBuilder.fillet()`, which first tries the complete edge set, then tries
  each edge individually, and finally skips the cosmetic fillet if NX still
  cannot apply it.
- If the fillet is function-critical rather than cosmetic, reduce the radius or
  select a narrower edge set in the generated journal.

## ChamferBuilder SmartCollector is None

Cause:

- Some NXOpen Python bindings create `ChamferBuilder.SmartCollector` as `None`
  instead of a ready-to-use collector object.
- Calling `builder.SmartCollector.Add(edge)` then fails before NX can attempt
  the chamfer.

Fix:

- Use `NXBuilder.chamfer()`, which creates an `ScCollector`, adds an edge dumb
  rule, assigns it to the chamfer builder, and falls back to single-edge
  chamfers when the complete selected edge set fails.
- If the chamfer is cosmetic and NX still rejects it, the wrapper logs a
  warning and lets the main model continue exporting.

## Save cancelled after check failure

Cause:

- NX rejected `part.SaveAs(<output>.prt)` during save checks, often after a
  complex generated model has fragile blends, booleans, or transient topology.
- The model may still exist in the active display part even though native PRT
  save failed.

Fix:

- `NXBuilder.export_step()` tries to save next to the STEP output first, then in
  `_cadnx_work/`.
- If both `SaveAs` attempts fail, the wrapper logs a warning and asks the STEP
  exporter to export the current display part without setting an `InputFile`.
- If STEP export still fails, simplify fragile chamfers/fillets or inspect the
  active part with NX part checks.

## Invalid file path

Cause:

- Windows backslashes not escaped.
- Output directory does not exist.
- NX has no write permission.

Fix:

- Use raw strings on Windows.
- Create output directories before running the journal.
- Prefer absolute paths.
