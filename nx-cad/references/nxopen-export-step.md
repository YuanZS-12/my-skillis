# NXOpen Export STEP

Use NXOpen DexManager STEP exporters when available.

NX 2606 currently has an experimental generic-creator pattern:

- `session.DexManager.CreateStepCreator()`
- Set `ExportAsOption.Ap242`
- Set `ExportFromOption.DisplayPart`
- Explicitly set `step_creator.ObjectTypes.Solids = True`; object-type filters
  are not assumed to default to enabled
- For the live-part wrapper/template route, do not also set `InputFile`
- Set output STEP filename
- Commit export
- Destroy the exporter

`CreateStep214Creator()` is absent from the user's NX 2606 Python binding. It
may remain a version-gated fallback for older bindings, where an input part path
is required, but it is rejected as an NX 2606 recipe.

Probe 10 run 003 deliberately used `DisplayPart` plus `InputFile` and a unique
output name. NX read the correct PRT but emitted only metadata because solids
were not selected. Run 004 preserves that configuration and adds only
`ObjectTypes.Solids = True`. The live DisplayPart-only template/wrapper route
also enables `Solids`, but neither route is verified until a manually returned
STEP passes deterministic geometry inspection.

General requirements:

- Export the active work part
- Use AP214 or AP242 if available
- Export solids
- Use absolute output paths
- Confirm the `.step` file exists after export

NX 2606 live-part candidate pattern:

    step_creator = session.DexManager.CreateStepCreator()
    step_creator.ExportAs = NXOpen.StepCreator.ExportAsOption.Ap242
    step_creator.ExportFrom = NXOpen.StepCreator.ExportFromOption.DisplayPart
    step_creator.ObjectTypes.Solids = True
    step_creator.FileSaveFlag = False
    step_creator.ProcessHoldFlag = True
    step_creator.OutputFile = step_path
    try:
        step_creator.Commit()
    finally:
        step_creator.Destroy()

File existence and size are not sufficient artifact validation. The returned
STEP must contain geometric representation entities and pass the post-NX CAD
inspection/snapshot workflow before export is promoted as verified.
