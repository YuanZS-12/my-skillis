# Official NXOpen Python Sources

Use this file when explaining or revising where `nx-cad` journal structure,
NXOpen calls, and wrapper parameters come from.

Primary source:

- Siemens **NXOpen Python Reference Guide 2512** main page:
  `https://docs.sw.siemens.com/en-US/doc/209349590/PL20250429951538534.custom_api.nxopen_python_ref`
- Static Doxygen entry used for API lookup:
  `https://docs.sw.siemens.com/documentation/external/PL20250429951538534/en-US/custom_api/nxopen_python_ref/index.html`

## Journal Session And Part Sources

- `NXOpen.Session`
  - Official page:
    `.../nxopen_python_ref/a06767.html`
  - Used for: `NXOpen.Session.GetSession()`.
  - `nx-cad` use: `NXBuilder.__init__()` starts from the singleton NX session.

- `NXOpen.PartCollection`
  - Official page:
    `.../nxopen_python_ref/a05815.html`
  - Used for: `NewDisplay(name, units)` when no work part exists.
  - `nx-cad` use: `NXBuilder._create_work_part()` creates a millimeter work
    part if the NX session has no active work part.

## Modeling Builder Sources

- `NXOpen.Features.FeatureCollection`
  - Official page:
    `.../nxopen_python_ref/a44375.html`
  - Used for factory methods:
    `CreateBlockFeatureBuilder`, `CreateCylinderBuilder`,
    `CreateBooleanBuilder`, `CreateChamferBuilder`,
    `CreateEdgeBlendBuilder`, and `CreateExtrudeBuilder`.
  - `nx-cad` use: all generated geometry goes through `NXBuilder` wrapper
    methods that call these official builder factories.

- `NXOpen.Features.BlockFeatureBuilder`
  - Official page:
    `.../nxopen_python_ref/a42987.html`
  - Used for rectangular block primitives.
  - `nx-cad` use: `NXBuilder.box(length, width, height, origin)`.

- `NXOpen.Features.CylinderBuilder`
  - Official page:
    `.../nxopen_python_ref/a43699.html`
  - Used for cylindrical primitives and cylindrical cutter tools.
  - `nx-cad` use: `NXBuilder.cylinder(...)` and `NXBuilder.hole(...)`.

- `NXOpen.Features.FeatureBuilder`
  - Referenced by builder pages as inherited behavior.
  - Used for: `CommitFeature()`.
  - `nx-cad` use: wrapper methods commit feature builders and return the
    committed feature.

- `NXOpen.Builder`
  - Referenced by builder pages as inherited behavior.
  - Used for: `Destroy()`.
  - `nx-cad` use: wrapper methods destroy builders after commit or failed
    attempts.

- `NXOpen.Features.ChamferBuilder`
  - Official page:
    `.../nxopen_python_ref/a43163.html`
  - Used for chamfer features.
  - `nx-cad` use: `NXBuilder.chamfer(...)` with compatibility fallbacks for
    NXOpen versions where `SmartCollector` is not already initialized.

- `NXOpen.Features.EdgeBlendBuilder`
  - Official page:
    `.../nxopen_python_ref/a44035.html`
  - Used for edge blends / fillets.
  - `nx-cad` use: `NXBuilder.fillet(...)` with fallback behavior for NXOpen
    versions that lack convenience methods or reject a selected edge set.

- `NXOpen.Features.ExtrudeBuilder`
  - Official page:
    `.../nxopen_python_ref/a44299.html`
  - Used for prism-like extrusions from sections.
  - `nx-cad` use: `polygon_prism(...)` and `polygon_prism_on_plane(...)`.

## STEP Export Sources

- `NXOpen.DexManager`
  - Official page:
    `.../nxopen_python_ref/a03807.html`
  - Used for: `CreateStepCreator()`.
  - `nx-cad` use: `NXBuilder._create_step_exporter()`.

- `NXOpen.StepCreator`
  - Official page:
    `.../nxopen_python_ref/a07507.html`
  - Used for STEP export properties such as `InputFile`, `OutputFile`,
    `OutputFileExtension`, `ExportAs`, and `FileSaveFlag`.
  - `nx-cad` use: `NXBuilder.export_step(output_path)`.

## What Comes From The User Prompt

The official NXOpen pages define API objects, builder factories, properties, and
commit/destroy behavior. They do not define model dimensions. Model parameters
come from the user's natural-language request and the CAD-NX brief:

- explicit dimensions: length, width, height, diameters, counts, pitches;
- defaults from `SKILL.md`: millimeters, XY base plane, +Z up, conservative
  clearances and cosmetic radii;
- derived values: radii from diameters, centers from symmetry/pitch, overcut
  depths from target thickness.

Generated journals put those named parameters at the top of `build()`, then
pass them into wrapper calls whose underlying NXOpen APIs are traced above.

## Why `NXBuilder` Wraps Official APIs

Generated journals use `from cadnx import NXBuilder` instead of directly calling
all raw NXOpen builders because:

- official NXOpen API names and collector behavior vary across NX versions;
- wrapper methods keep generated journals concise and repeatable;
- compatibility fixes from real NX runs can be made in one place;
- static checks can verify generated journals without executing Siemens NX.
