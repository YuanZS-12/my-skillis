---
name: nx-cad
description: Generate Siemens NXOpen Python journals from natural-language CAD specs. Use for NX-targeted parametric mechanical parts, assemblies, holes, ribs, bosses, fillets, chamfers, boolean operations, native .prt creation, and STEP export. This skill emits NXOpen Python only, never build123d/CadQuery/OCC.
---

> **Runtime**: Generated `.py` files are not executed locally.
> Copy the generated journal plus its sibling `cadnx/` folder to a machine with
> Siemens NX installed, then run via NX: File -> Execute -> NX Open. NX builds
> the model, saves a native `.prt`, and exports a `.step`.

# NX CAD Generation

## Purpose

Create NXOpen Python journals from natural-language CAD requirements. This skill
follows the text-to-cad CAD workflow style: natural-language brief, parametric
source, explicit assumptions, generated artifacts, and repair-loop discipline.
The implementation target is Siemens NXOpen Python, not build123d.

Generated files should be portable NX journals plus a small local wrapper
package:

```text
models/
    <model_name>.py
    cadnx/
        __init__.py
        builder.py
```

The generated `.py` imports `cadnx.NXBuilder`; `cadnx` is a local wrapper around
official Siemens `NXOpen` APIs.

## Use This Skill When

Use this skill when the user asks for Siemens NX, NXOpen, UG NX, NX journal
code, NX-compatible Python CAD, NX `.prt` creation, STEP export through NX, or
mechanical CAD features such as holes, counterbores, countersinks, slots,
pockets, bosses, standoffs, ribs, gussets, fillets, chamfers, and boolean
operations.

Do not use this skill for local build123d generation, local STEP validation,
render-only concept art, CAM toolpaths, engineering certification, FEA
conclusions, architectural BIM, or freehand illustration.

## Default Assumptions

Use these defaults unless the user specifies otherwise:

- Units: millimeters.
- Origin: center of the main part footprint unless a mating interface suggests
  a clearer datum.
- Base plane: XY.
- Up/extrusion axis: positive Z.
- Output geometry: closed, positive-volume solids.
- Native output: `.prt` saved by NX during execution.
- Exchange output: `.step` exported next to the generated journal.
- Small plastic enclosure wall: 2.0-3.0 mm when unspecified.
- Cosmetic fillet: 1.0-3.0 mm when safe for local geometry.
- M3/M4/M5 normal clearance holes: 3.4/4.5/5.5 mm unless another standard is
  requested.

Ask one focused clarification question only when missing information makes the
model impossible, fit-critical, safety-critical, or compliance-bound. Otherwise
proceed with explicit assumptions.

## Natural-Language Specs Only

Do not ask the user to provide JSON. Convert prose into an internal CAD brief
with dimensions, units, coordinate convention, features, output paths,
assumptions, and validation targets. Use `assets/design-brief-template.md` and
`references/natural-language-specs.md` for brief-writing patterns.

## Root Model

Keep these roots separate:

- **Skill source root**: `<repo>/skills/nx-cad`
- **Generated output root**: `<repo>/models`
- **NX runtime root**: the copied model folder on the Windows NX machine

Generated journals must not depend on absolute paths from this Mac workspace.
They should resolve outputs from `__file__` and export `.step` next to the
journal on the NX machine.

## Required Workflow

1. Classify the request: new part, assembly, modification, NX repair, or export
   issue.
2. Load only the needed references:
   - official Siemens API source mapping:
     `references/official-nxopen-sources.md`
   - natural-language brief: `references/natural-language-specs.md`
   - parameter and feature planning: `references/parameters.md`
   - NXOpen modeling calls: `references/nxopen-modeling.md`
   - validation reporting: `references/validation.md`
   - STEP export issues: `references/nxopen-export-step.md`
   - repair loop: `references/repair-loop.md`
   - repeated API failures: `references/nxopen-common-errors.md`
   - benchmark regression work: `references/benchmark-workflow.md`
3. Create a concise internal CAD-NX brief: independent parameters, derived
   parameters, coordinate convention, feature order, output name, assumptions,
   local static validation, and NX runtime validation targets.
4. Plan before coding:
   - primary solids before holes/cutouts;
   - booleans before cosmetic detail;
   - fillets/chamfers last and conservative;
   - wrapper extension needed before raw NXOpen calls.
5. Generate a single NXOpen Python journal using
   `templates/nxopen_part_template.py`.
6. Save the journal under `<repo>/models/<task_name>.py`.
7. Sync the runtime wrapper:
   `skills/nx-cad/scripts/sync-runtime --models-dir models`.
8. Run local static checks only:
   `skills/nx-cad/scripts/check-journal models/<task_name>.py`.
   Do not claim NX execution unless the user runs it in NX and reports success.
9. If the user reports an NX traceback, repair the smallest responsible section
   of either the generated journal or `cadnx/builder.py`, sync `models/cadnx/`,
   and ask them to rerun in NX.

## NXOpen Code Rules

- Use `from cadnx import NXBuilder` and `b = NXBuilder()` for all modeled
  geometry.
- Do not import build123d, CadQuery, OCC, FreeCAD, OpenSCAD, or local CAD
  kernels.
- Every generated file must define `build(output_path: str = None)`.
- End `build()` with `b.export_step(output_path)`.
- If `output_path is None`, set it to the generated journal basename with
  `.step`.
- Put all named dimensions near the top of `build()`.
- Separate independent prompt parameters from derived dimensions.
- Derive centers, pitches, cut depths, and repeated feature positions from
  named parameters instead of duplicating numeric constants.
- Use floats or numbers only for dimensions; `NXBuilder` normalizes types for
  NXOpen.
- Prefer simple robust primitives and booleans over fragile low-level NXOpen
  builder sequences in generated journals.
- Avoid generated calls to raw NXOpen APIs unless `NXBuilder` lacks the needed
  operation and the reference confirms the pattern.
- Keep `models/cadnx/` synchronized with `skills/nx-cad/cadnx/` after
  generating or changing an output script.

## Supported Wrapper Operations

Prefer these `NXBuilder` calls:

- `b.box(length, width, height, origin=(x, y, z))`
- `b.rounded_box(length, width, height, radius, origin=(x, y, z))`
- `b.cylinder(diameter, height, origin=(x, y, z), axis=(0, 0, 1))`
- `b.hole(diameter, depth, position=(x, y, z), direction=(0, 0, -1))`
- `b.counterbore_hole(target, hole_diameter, hole_depth, counterbore_diameter, counterbore_depth, position, direction)`
- `b.slot_cut(target, length, width, depth, center, axis=(1, 0, 0), direction=(0, 0, -1))`
- `b.boolean_subtract(target, tool)`
- `b.boolean_unite(target, tool)`
- `b.fillet(edges, radius)`
- `b.chamfer(edges, offset)`
- `b.get_all_edges(feature)`
- `b.get_top_edges(feature)`
- `b.get_bottom_edges(feature)`
- `b.get_edges_by_axis(feature, axis=(0, 0, 1))`
- `b.get_edges_near(feature, point=(x, y, z), tolerance=...)`
- `b.get_edges_in_box(feature, min_xyz=(...), max_xyz=(...))`
- `b.export_step(output_path)`

If a model needs an unsupported feature, either compose it from supported
solids/booleans or extend `cadnx.NXBuilder` first, then sync the runtime.

## Repair Loop

When NX reports an error:

1. Identify whether the failure is import/path, work part creation, geometry
   builder, boolean, edge selection, fillet/chamfer, save, or STEP export.
2. Patch the shared wrapper when the failure is an NXOpen compatibility issue.
3. Patch the generated journal when the feature plan is fragile or invalid.
4. Run `skills/nx-cad/scripts/sync-runtime --models-dir models`.
5. Run `skills/nx-cad/scripts/check-journal models/<task_name>.py` locally.
6. Tell the user exactly which files to copy to the NX machine.

## Non-Negotiables

- Output source must be NXOpen-compatible Python, not build123d.
- Generated journals must run inside Siemens NX, not normal Python.
- Keep `.py` journal and `cadnx/` wrapper together when moving to NX.
- Never claim a journal has run in NX unless it actually did.
- Never hardcode Mac workspace paths into generated journals.
- Report only checks that actually ran.

## Progressive References

Load these files only when their trigger applies:

- `assets/design-brief-template.md` - internal brief scaffold.
- `references/official-nxopen-sources.md` - Siemens NXOpen Python Reference
  Guide pages used as the source for journal structure, builder calls, and STEP
  export APIs.
- `references/natural-language-specs.md` - prose-to-CAD brief conversion.
- `references/parameters.md` - parameter naming, derived dimensions, feature
  grouping, and common parameter failures.
- `references/nxopen-modeling.md` - journal structure, wrapper operations,
  coordinate conventions, and robust modeling rules.
- `references/validation.md` - local static gates, NX runtime validation
  boundaries, and final report contents.
- `references/repair-loop.md` - failure classification and source-vs-wrapper
  repair policy.
- `references/nxopen-export-step.md` - `.prt` save and STEP export behavior.
- `references/nxopen-common-errors.md` - known NXOpen Python compatibility
  errors from this user's NX environment.
- `references/benchmark-workflow.md` - repo benchmark prompts, local static
  gates, NX runtime reporting, and repair policy.

Final responses should include generated `.py` path, `models/cadnx/` sync
status, syntax checks actually run, assumptions, and exactly what to copy to the
NX machine.
