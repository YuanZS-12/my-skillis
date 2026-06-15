# NXOpen Export STEP

Use NXOpen DexManager STEP exporters when available.

Common NXOpen patterns include:

- `session.DexManager.CreateStep214Creator()`
- Set input part
- Set output STEP filename
- Commit export
- Destroy the exporter

General requirements:

- Export the active work part
- Use AP214 or AP242 if available
- Export solids
- Use absolute output paths
- Confirm the `.step` file exists after export

Pseudo-pattern:

    step_creator = session.DexManager.CreateStep214Creator()
    step_creator.InputFile = part_path
    step_creator.OutputFile = step_path
    step_creator.Commit()
    step_creator.Destroy()

If the exact STEP creator properties differ by NX version, use a journal recorded from the user's NX version as the authoritative template.
