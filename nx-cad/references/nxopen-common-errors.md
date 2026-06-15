# NXOpen Common Errors

## ModuleNotFoundError: No module named 'NXOpen'

Cause:

- The journal was run with normal Python instead of Siemens NX Python or NX journal runner.

Fix:

- Run the script with `skills\nx-cad\scripts\nx-run.bat`.
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
