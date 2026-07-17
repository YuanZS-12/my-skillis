# Official NXOpen Python Sources

Use this file when explaining or revising where `nx-cad` journal structure,
NXOpen calls, and wrapper parameters come from.

This source map is the required API grounding mechanism for `nx-cad`. New raw
`NXOpen.*` wrapper code must be traced to the Siemens reference pages listed
here and then validated in a real Siemens NX runtime before it is treated as
production-ready.

Primary source:

- Siemens **NXOpen Python Reference Guide 2512** main page:
  `https://docs.sw.siemens.com/en-US/doc/209349590/PL20250429951538534.custom_api.nxopen_python_ref`
- Static Doxygen entry used for API lookup:
  `https://docs.sw.siemens.com/documentation/external/PL20250429951538534/en-US/custom_api/nxopen_python_ref/index.html`
- NXOpen namespace index used as the official class/enum/struct lookup root:
  `https://docs.sw.siemens.com/documentation/external/PL20250429951538534/en-US/custom_api/nxopen_python_ref/a00006.html`
  - Used for: confirming that generated wrapper calls are grounded in the
    `NXOpen` namespace and that raw references should resolve to documented
    NXOpen classes, enums, or structs.
  - `nx-cad` use: this is the source-of-truth entry point for API object names
    and parameter object families. It does not provide mechanical dimensions;
    those remain prompt/default/derived CAD parameters.

## Official-Only API Rule

Any new or revised raw `NXOpen.*` reference in `skills/nx-cad/cadnx/` must be
traceable to the Siemens NXOpen Python Reference Guide main page above or one
of its generated API pages. This applies to:

- classes, enums, structs, builders, creators, and collections;
- factory methods such as `Create...Builder`;
- builder properties and enum values;
- commit, destroy, selection, collector, and export patterns.

Do not introduce raw NXOpen code from memory, forum posts, translated examples,
or non-Siemens documentation. If the official guide cannot confirm the object
or pattern, keep the generated journal within existing `NXBuilder` operations
or ask the user for a simpler supported representation.

When adding a wrapper operation, update this file with the official page used
for each new NXOpen object family and report the real Siemens NX execution
status separately.

## Raw Journal Evidence

Raw NXOpen journal code may be generated without first wrapping every API in
`NXBuilder`. In that path, the generated or repaired journal must carry either
`MCP_API_REVIEW` evidence that lists the `dc_*` tools and API facts checked, or
`STATIC_ONLY_NXOPEN_REVIEW` when MCP tools were unavailable. This file remains
the durable source map for recurring API families; MCP evidence is the
per-journal proof that specific raw calls were reviewed before handoff.

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

The higher-level helpers `NXBuilder.oriented_box(...)`,
`NXBuilder.annular_groove(...)`, `NXBuilder.bearing_seat(...)`,
`NXBuilder.bushing_boss(...)`, `NXBuilder.clevis(...)`, and
`NXBuilder.require_feature_budget(...)` do not introduce new raw NXOpen API
families. `oriented_box(...)` and `clevis(...)` delegate to
`polygon_prism_on_plane(...)`, which uses the official section/extrude APIs
listed below. `annular_groove(...)`, `bearing_seat(...)`, and
`bushing_boss(...)` compose the existing official cylinder, hole, and boolean
helper paths. `require_feature_budget(...)` is a pure Python parameter guard.

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

- `NXOpen.Features.FeatureCollection.CreateRevolveBuilder`
  - Official page:
    `.../nxopen_python_ref/a44375.html`
  - Used for: creating a `NXOpen.Features.RevolveBuilder`.
  - `nx-cad` use: `NXBuilder.revolved_profile(...)` creates a new revolve
    feature builder.

- `NXOpen.Features.RevolveBuilder`
  - Official page:
    `.../nxopen_python_ref/a46507.html`
  - Used for: `Section`, `Axis`, `Limits`, `Tolerance`, `CommitFeature()`, and
    `Destroy()`.
  - `nx-cad` use: `NXBuilder.revolved_profile(...)` revolves a closed
    radial/Z section around an axis.

- `NXOpen.AxisCollection`
  - Official page:
    `.../nxopen_python_ref/a03319.html`
  - Used for: `CreateAxis(point, direction, update)`.
  - `nx-cad` use: `NXBuilder.revolved_profile(...)` creates the revolve axis
    from `axis_point` and `axis_direction`.

- `NXOpen.GeometricUtilities.Limits`
  - Official page:
    `.../nxopen_python_ref/a56887.html`
  - Used for: `StartExtend` and `EndExtend`.
  - `nx-cad` use: `NXBuilder.revolved_profile(...)` sets angle limits.

- `NXOpen.GeometricUtilities.Extend`
  - Official page:
    `.../nxopen_python_ref/a56655.html`
  - Used for: `Value.RightHandSide` through `StartExtend` and `EndExtend`.
  - `nx-cad` use: `NXBuilder.revolved_profile(...)` sets start angle `0` and
    end angle `angle_degrees`.

## STEP Export Sources

- `NXOpen.DexManager`
  - Official page:
    `.../nxopen_python_ref/a03807.html`
  - Used for: `CreateStepCreator()` for export and
    `CreateStep214Importer()` for STEP import.
  - `nx-cad` use: `NXBuilder._create_step_exporter()` and
    `NXBuilder._create_step214_importer()`.

- `NXOpen.StepCreator`
  - Official page:
    `.../nxopen_python_ref/a07507.html`
  - Used for STEP export properties such as `InputFile`, `OutputFile`,
    `OutputFileExtension`, `ExportAs`, `ObjectTypes`, and `FileSaveFlag`.
  - `nx-cad` use: `NXBuilder.export_step(output_path)`.

- `NXOpen.ObjectTypeSelector`
  - Official page:
    `.../nxopen_python_ref/a05707.html`
  - Used for: `StepCreator.ObjectTypes.Solids = True`; Siemens documents
    `Solids` as the boolean filter that must be enabled when solid bodies are
    desired in the output file.
  - `nx-cad` use: runtime probe 10, raw journal template, and
    `NXBuilder._enable_step_solid_export(...)`.

## STEP Import Sources

- `NXOpen.Step214Importer`
  - Official page:
    `.../nxopen_python_ref/a07487.html`
  - Used for STEP214 import properties and methods including `FileOpenFlag`,
    `FlattenAssembly`, `ImportTo`, `LayerDefault`, `Optimize`, `SettingsFile`,
    `SewSurfaces`, `SimplifyGeometry`, and `SmoothBSurfaces`.
  - `nx-cad` use: `NXBuilder.import_step_part(...)` imports catalog or
    user-supplied STEP files into the current work part.

- `NXOpen.Step214Importer.ImportToOption`
  - Official page:
    `.../nxopen_python_ref/a07491.html`
  - Used for: `WorkPart`, the documented import destination for importing
    external geometry into the active work part.
  - `nx-cad` use: `NXBuilder.import_step_part(...)` sets `ImportTo` to
    `WorkPart` when the enum is available.

- `NXOpen.BaseImporter`
  - Official page:
    `.../nxopen_python_ref/a03343.html`
  - Used for inherited STEP import properties including `InputFile`,
    `OutputFile`, `PartUnit`, `GetMode`, and `SetMode`.
  - `nx-cad` use: `NXBuilder.import_step_part(...)` sets `InputFile` on the
    Step214 importer.

- `NXOpen.DexBuilder`
  - Official page:
    `.../nxopen_python_ref/a03803.html`
  - Used for inherited DEX behavior including `ProcessHoldFlag`. It inherits
    `Commit()` and `GetCommittedObjects()` from `NXOpen.Builder`.
  - `nx-cad` use: `NXBuilder.import_step_part(...)` waits for translation,
    commits the importer, and returns committed objects when NX reports them.

## Planned Advanced Geometry APIs

These are not implementation approval. They are research targets. A helper may
move to supported only after the exact class, builder, property, enum, and
method pattern are confirmed in the official Siemens guide and validated in NX.

- Revolved profile features: research target for
  `b.revolved_profile(...)`.
- Curve and spline primitives: research target for `b.polyline_curve(...)` and
  `b.spline_curve(...)`.
- Loft or through-curve bodies: research target for
  `b.loft_profiles(...)`.
- Swept profiles: research target for `b.sweep_profile(...)`.
- Semantic blade helpers: research target for `b.airfoil_section(...)`,
  `b.lofted_blade(...)`, and `b.revolved_impeller_hub(...)`.

## NX 2606 Sweep Sources

- `NXOpen.Features.SweptBuilder1`
  - Official page:
    `.../nxopen_python_ref/a47559.html`
  - Created in NX 2412. It replaces `SweptBuilder`, which Siemens marks
    deprecated from NX 2412.
  - Used for: `SectionList`, `GuideList`, `OrientationMethod`,
    `ScalingMethod`, `BodyPreference`, and `CommitFeature()` in probes 05–07.

- `NXOpen.Features.FreeformSurfaceCollection`
  - Official page:
    `.../nxopen_python_ref/a44599.html`
  - Used for: `CreateSweptBuilder1(swept)`; accessed through
    `work_part.Features.FreeformSurfaceCollection`.

- `NXOpen.SectionList`
  - Official page:
    `.../nxopen_python_ref/a06455.html`
  - Used for: `Append(section)` and `Append([section1, section2])` on sweep
    section and guide lists.

- `NXOpen.GeometricUtilities.OrientationMethodBuilder`
  - Official class and enum pages:
    `.../nxopen_python_ref/a56995.html` and `a56999.html`
  - Used for: verified `OrientationOptions.Fixed` probes and the preserved
    rejected NX 2606 `OrientationOptions.ByAngularLaw` fixture.

- `NXOpen.GeometricUtilities.ScalingMethodBuilder`
  - Official class and enum pages:
    `.../nxopen_python_ref/a57359.html` and `a57367.html`
  - Used for: `ScalingOptions.Constant` in the fixed-orientation probe.

- `NXOpen.GeometricUtilities.LawBuilder`
  - Official class and type-enum pages:
    `.../nxopen_python_ref/a56867.html` and `a56875.html`
  - Used for: `LawType = Type.Linear` plus start/end expressions in the
    preserved rejected angular-law fixture. These official API facts establish
    object shape but do not override the NX 2606 runtime rejection.

- `NXOpen.GeometricUtilities.FeatureOptions`
  - Official class and body-style enum pages:
    `.../nxopen_python_ref/a56735.html` and `a56739.html`
  - Used for: `BodyPreference.BodyType = BodyStyle.Solid`.

## What Comes From The User Prompt

The official NXOpen pages define namespaces, API objects, builder factories,
properties, object parameter types, and commit/destroy behavior. In particular,
`a00006.html` is the `NXOpen` namespace index for classes, enums, and structs.
It is used to identify official NXOpen object families, not to invent part
dimensions.

Model parameters come from the user's natural-language request and the CAD-NX
brief:

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
