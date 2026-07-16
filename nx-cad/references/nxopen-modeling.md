# NXOpen Modeling Reference

## Objective

Generate Siemens NXOpen Python journals that build parametric BREP geometry
inside Siemens NX, save a native `.prt`, and export a `.step` file. Generated
journals are run inside NX via File -> Execute -> NX Open.

This skill borrows text-to-cad's brief/parameter/repair-loop discipline, but
the emitted source must be NXOpen-compatible Python only.

Official API source: use `references/official-nxopen-sources.md` before changing
journal structure, builder calls, or STEP export behavior. The current standard
is derived from Siemens NXOpen Python Reference Guide 2512 pages for
`NXOpen.Session`, `NXOpen.PartCollection`, `NXOpen.Features.FeatureCollection`,
feature builders, `NXOpen.DexManager`, and `NXOpen.StepCreator`.

## Coordinate System

- Units: millimeters.
- XY is the base plane.
- +Z is up.
- Prefer origin at the main part footprint center unless a functional datum is
  clearer.
- For blocks, `origin=(x, y, z)` means the lower-left-lower corner of the block.

## Supported Journal Patterns

### Wrapper-assisted journal pattern

Use this when `NXBuilder` operations directly match the requested geometry.
The generated journal may import `cadnx.NXBuilder`, call wrapper primitives,
and use `b.export_step(output_path)`.

```python
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _candidate in (
    _SCRIPT_DIR,
    os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "skills", "nx-cad")),
):
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)

from cadnx import NXBuilder


def build(output_path: str = None):
    b = NXBuilder()

    # 1. Parameters: named dimensions
    # 2. Modeling: NXBuilder calls when they directly match intent
    # 3. Export
    if output_path is None:
        output_path = os.path.splitext(os.path.abspath(__file__))[0] + ".step"
    b.export_step(output_path)


def main():
    default_output = os.path.splitext(os.path.abspath(__file__))[0] + ".step"
    output = sys.argv[1] if len(sys.argv) > 1 else default_output
    build(output)


if __name__ == "__main__":
    main()
```

Do not use plain `"output.step"` as the generated default.

### Raw NXOpen high-fidelity journal pattern

This is the Raw NXOpen journal pattern for MCP-backed high-fidelity generation.

Use this when the prompt asks to use MCP, `dc_server`, Designcenter, raw/bare
`NXOpen`, `NXOpen lib`, or high-fidelity NXOpen code. This route is available
for any part class and is not limited to smooth or advanced geometry. The
journal must not import `cadnx` or use `NXBuilder`.

Use `templates/raw_nxopen_part_template.py` as the starting point. The journal
should:

- include `RAW_NXOPEN_HIGH_FIDELITY = True`;
- include `MCP_API_REVIEW` when `dc_*` tools were used, or
  `STATIC_ONLY_NXOPEN_REVIEW` when they were unavailable;
- include required submodule imports;
- import every required NXOpen submodule explicitly, such as
  `NXOpen.Features`, `NXOpen.Annotations`, or `NXOpen.UF`;
- define `create_work_part_if_needed(session)` when the journal can run without
  an active part;
- keep named parameters near the top of `build()` or `main()`;
- create curves, sections, builders, expressions, PMI, and exports using
  MCP-reviewed NXOpen API shapes;
- destroy builders and dispose load/status objects where applicable;
- make nonessential PMI or cosmetic annotation failures nonblocking when the
  primary solid is already created;
- print diagnostics for work part, created bodies/features, and export path.
- avoid `cadnx.NXBuilder` entirely.

Structure source:

- `NXOpen.Session.GetSession()` comes from the official `NXOpen.Session`
  reference.
- Work/display part behavior comes from `NXOpen.PartCollection`.
- The `build(output_path: str = None)` and `main()` wrapper are `nx-cad`
  conventions around the official API so generated journals are portable,
  testable, and callable from NX.
- The sibling `cadnx/` import is a local runtime wrapper convention for the
  wrapper-assisted pattern. Raw NXOpen high-fidelity journals should omit it.

## Wrapper Operations

| Intent | NXBuilder call |
|--------|----------------|
| Rectangular block | `b.box(length, width, height, origin=(x, y, z))` |
| Local-frame rectangular block | `b.oriented_box(length, width, height, center=(x, y, z), u_axis=(...), v_axis=(...), w_axis=(...))` |
| Revolved radial/Z profile | `b.revolved_profile(points=[(radius, z), ...], axis_point=(x, y, z), axis_direction=(0, 0, 1), angle_degrees=360.0)` |
| Rounded rectangular block | `b.rounded_box(length, width, height, radius, origin=(x, y, z))` |
| Cylinder / boss / pin | `b.cylinder(diameter, height, origin=(x, y, z), axis=(0, 0, 1))` |
| Through-hole | `hole = b.hole(dia, depth, position=(x, y, z), direction=(0, 0, -1))`; then `b.boolean_subtract(body, hole)` |
| Ring groove / shoulder | `b.annular_groove(target, outer_diameter, inner_diameter, depth, position=(x, y, z), direction=(0, 0, -1), cutter_overlap=...)` |
| Bearing seat | `b.bearing_seat(target, bore_diameter, seat_diameter, through_depth, seat_depth, position=(x, y, z), direction=(0, 0, -1), cutter_overlap=...)` |
| Bushing boss | `b.bushing_boss(target, boss_diameter, boss_height, bore_diameter, center=(x, y, z), axis=(0, 0, 1), feature_overlap=..., through_overcut=...)` |
| Clevis interface | `b.clevis(target, length, width, ear_thickness, gap, pin_hole_diameter, center=(x, y, z), u_axis=(...), v_axis=(...), w_axis=(...))` |
| Counterbore | `b.counterbore_hole(target, hole_dia, hole_depth, cbore_dia, cbore_depth, position=(x, y, z), direction=(0, 0, -1))` |
| Metric clearance hole | `b.screw_clearance_hole(target, "M5", depth, position=(x, y, z), direction=(0, 0, -1))` |
| Metric tapped pilot hole | `b.tapped_hole(target, "M5", depth, position=(x, y, z), direction=(0, 0, -1))` |
| Socket-head screw seat | `b.socket_head_counterbore_hole(target, "M5", depth, position=(x, y, z), direction=(0, 0, -1))` |
| Flat-head screw relief | `b.countersink_hole(target, "M5", depth, position=(x, y, z), direction=(0, 0, -1))` |
| Rounded slot cut | `b.slot_cut(target, length, width, depth, center=(x, y, z), axis=(1, 0, 0), direction=(0, 0, -1))`; `axis` and `direction` must be axis-aligned |
| Rectangular pocket | `b.rectangular_pocket(target, length, width, depth, center=(x, y, z), direction=(0, 0, -1))` |
| Linear pattern points | `b.linear_pattern_points(start=(x, y, z), count=n, spacing=pitch, direction=(1, 0, 0))` |
| Circular pattern points | `b.circular_pattern_points(center=(x, y, z), radius=r, count=n, start_angle_degrees=0)` |
| Positive dimension guard | `b.require_positive(base_length=base_length, plate_thickness=plate_thickness)` |
| Feature budget guard | `b.require_feature_budget(boolean_operations=n, micro_holes=m, patterned_features=p)` |
| Local wall guard | `b.require_min_wall(lug_width, counterbore_diameter, min_wall=1.5, label="M5 counterbore")` |
| Hole edge-distance guard | `b.require_edge_distance(edge_distance, clearance_diameter, min_ratio=1.0, label="mounting hole")` |
| Union two bodies | `b.boolean_unite(target, tool)` |
| Subtract tool body | `b.boolean_subtract(target, tool)` |
| Fillet edges | `b.fillet(edges, radius)` |
| Chamfer edges | `b.chamfer(edges, offset)` |
| All body edges | `b.get_all_edges(feature)` |
| Highest-Z edges | `b.get_top_edges(feature)` |
| Lowest-Z edges | `b.get_bottom_edges(feature)` |
| Edges parallel to axis | `b.get_edges_by_axis(feature, axis=(0, 0, 1))` |
| Edges near point | `b.get_edges_near(feature, point=(x, y, z), tolerance=1.0)` |
| Edges in bounding box | `b.get_edges_in_box(feature, min_xyz=(...), max_xyz=(...))` |
| STEP export | `b.export_step(output_path)` |

The `NXBuilder` calls above map to official NXOpen objects listed in
`references/official-nxopen-sources.md`. For example, `box()` wraps
`BlockFeatureBuilder`, `cylinder()` wraps `CylinderBuilder`, boolean operations
wrap `FeatureCollection.CreateBooleanBuilder`, and `export_step()` wraps
`DexManager.CreateStepCreator` plus `StepCreator` properties.

The official namespace entry
`https://docs.sw.siemens.com/documentation/external/PL20250429951538534/en-US/custom_api/nxopen_python_ref/a00006.html`
is used as the top-level source for NXOpen class/enum/struct families. It
defines the official API object space that `NXBuilder` wraps. Generated
mechanical dimensions are still named CAD parameters from the prompt and the
skill brief, then passed into official NXOpen builder properties through the
wrapper.

Raw `NXOpen.*` calls are allowed in generated journals when direct NXOpen
builders produce better geometry than wrapper operations. Compatibility work
still requires MCP API-review evidence or explicit static-only uncertainty.

Reusable `NXBuilder` helpers for advanced geometry remain governed by
`references/advanced-geometry-roadmap.md`. Direct raw NXOpen use of loft,
sweep, through-curve, spline, PMI, and related APIs is allowed when MCP
API-review evidence supports the API shape and the journal includes the
required diagnostics and repair-loop expectations.

## Parameter Source

NXOpen official documentation defines API signatures and builder properties, not
the part dimensions. Generated journal parameters are obtained from:

- explicit user prompt dimensions and feature counts;
- defaults in `SKILL.md` when safe, such as millimeters, XY base plane, +Z up,
  and conservative cosmetic radii;
- derived calculations such as radius from diameter, symmetric centers, pattern
  pitch, and through-cut overtravel.

Put independent prompt parameters first, then derived parameters, then
NXBuilder feature calls.

When geometry is compact, add guard calls before creating subtractive features:

```python
b.require_positive(base_length=base_length, lug_width=lug_width)
b.require_min_wall(lug_width, counterbore_diameter, min_wall=1.5, label="shoulder counterbore")
b.require_edge_distance(hole_edge_distance, clearance_diameter, min_ratio=1.0, label="mounting hole")
```

These checks are not Siemens API calls; they are generation-time CAD sanity
rules that prevent known NX boolean failures such as tangent tools and zero wall
thickness before the journal reaches NX.

## Modeling Strategy

- Use named parameter variables near the top of `build()`.
- Classify the part as machined, molded/enclosure, structural bracket, rotary,
  or generic before choosing optional industrial details.
- For named purchasable components, resolve `$step-parts` candidates and record
  the external component ledger before deciding to use imported STEP geometry
  or a simplified envelope.
- Compose robust solids from boxes and cylinders first.
- Use boolean subtract for holes, slots, lightening cutouts, and trimming.
- Use boolean unite for bosses, ribs, gussets, mounting pads, and multi-block
  parts.
- Prefer wrapper compound operations such as `slot_cut()` and
  `counterbore_hole()` over repeating raw cutter booleans in generated journals.
- For circular patterned pads, cavities, arms, or inspection blocks, prefer
  `oriented_box()` with local radial/tangential/axial axes over global
  axis-aligned `box()` calls.
- For bearing shoulders, retaining grooves, C-seal grooves, and circular
  datum reliefs, prefer `annular_groove()` over opaque large-diameter `hole()`
  cutters so the section intent is explicit.
- For bellcranks, control arms, clevis brackets, and lugged linkage parts,
  prefer `bearing_seat()`, `bushing_boss()`, and `clevis()` so critical
  interfaces are explicit and can be statically checked.
- Use `slot_cut()` only for axis-aligned slots. Do not pass circular-pattern
  tangents, radial normals, or trig-derived vectors to `axis` or `direction`.
  For angled cosmetic marks, use shallow `box()` cutters or
  `rectangular_pocket()` features; for functional angled slots, extend the
  wrapper before generating the journal.
- Make subtractive tools slightly oversized so through-cuts fully pass the
  target body.
- Add explicit overlap for boolean features so tools do not merely touch target
  faces or previously cut faces.
- Keep generated fillets/chamfers conservative; NX will fail if radius/offset
  exceeds local edge conditions.
- Avoid topology-sensitive selectors unless the model has already been kept
  very simple.
- Avoid global `fillet(get_all_edges(...))` or
  `fillet(get_edges_by_axis(...))` after high-pattern boolean operations. Use
  local `get_edges_in_box(...)` selectors, small chamfers, or omit cosmetic
  blends until NX runtime confirms the main body.

## External STEP Components

External STEP import and assembly placement may use `NXBuilder` methods when
their guarded contract is sufficient. Raw `NXOpen.*` import manager, component
assembly, or transform calls are allowed when MCP API-review evidence confirms
the API shape and the journal reports runtime uncertainty honestly.

The desired generated shape is:

```python
component = b.import_step_part("parts/step-parts/<part-id>.step", name="<role>")
b.place_component(component, origin=(x, y, z), x_axis=(1, 0, 0), z_axis=(0, 0, 1))
```

These methods are a contract until their raw NXOpen implementation is grounded
in the Siemens reference guide and run in a real NX session. If that validation
has not happened, generate conservative envelope geometry and record the real
STEP part in the external component ledger for a later import-capable pass.

## Boolean Overlap Rules

NX rejects many boolean features when the tool and target only touch at a face,
edge, or tangent boundary. Generated journals must avoid exact contact:

- union features must overlap the target by a named `feature_overlap`
  parameter, normally 0.3-1.0 mm for small raised details;
- subtractive cutters must overlap the target or adjacent cutouts by a named
  `cutter_overlap` parameter instead of starting exactly on a face created by a
  previous cut;
- through-cut tools should extend past both sides of the target by
  `through_overcut`;
- raised text, arrows, pads, ribs, bosses, and standoffs should start slightly
  below the target face before `b.boolean_unite(...)`;
- keyways, slots, reliefs, and pockets that open into a bore or another cutout
  should overlap that existing opening by `cutter_overlap`;
- do not rely on exact tangent placement such as `origin_y = bore_radius` for a
  keyway cutter or `origin_z = top_z` for a raised arrow.

Prefer changing the generated journal's feature plan over patching
`NXBuilder.boolean_subtract()` or `NXBuilder.boolean_unite()` when the reported
failure is a model-specific zero-wall touch condition.

## Industrial Detail Strategy

Use detail features that communicate design intent while preserving NX
robustness:

- Machined parts: start from rectangular/round stock-like solids, add pockets
  and slots before fastener features, use metric helper calls for clearance,
  counterbore, countersink, and tapped holes, then add small chamfers or
  fillets to accessible edges.
- Molded/enclosure parts: create the exterior shell and any lid/base solids
  first, then add bosses, ribs, standoffs, and lip/step geometry with consistent
  wall parameters. Keep ribs and bosses simple when the wrapper lacks true
  shell/draft features.
- Structural brackets: build the main plate or upright, unite pads and ribs,
  then cut mounting holes and lightening slots. Keep gussets rectangular or
  simple polygon prisms only when the wrapper operation is already supported.
- Rotary parts: keep all coaxial cylinders on the same axis, add shoulders and
  bores with named diameters, then finish exposed ends with small chamfers.
- Generic concept parts: use only low-risk edge refinement and standard
  fastener helpers.

Skip a detail rather than inventing unsupported raw NXOpen code. If the detail
is important, extend `NXBuilder` first using officially documented NXOpen APIs.
Record the official source in `references/official-nxopen-sources.md`.

## Hole Pattern

Always create a hole tool cylinder, then subtract it from the target body:

```python
hole = b.hole(
    diameter,
    depth,
    position=(cx, cy, top_z + 1),
    direction=(0, 0, -1),
)
b.boolean_subtract(body, hole)
```

Make the hole depth 1-3 mm larger than the target thickness.

## Slot And Counterbore Pattern

Use `slot_cut()` for axis-aligned rounded slots. It creates two end cutter
cylinders plus a rectangular bridge cutter and subtracts them from the target.
Keep `axis` and `direction` orthogonal and axis-aligned.

Use `counterbore_hole()` for screw seats instead of manually sequencing the
smaller bore and larger counterbore in every generated journal.

## Industrial Hole And Fastener Pattern

For normal metric fasteners, prefer the standard helper wrappers over ad hoc
diameters:

```python
b.screw_clearance_hole(plate, "M5", plate_thickness + 2, position=(x, y, top_z + 1))
b.socket_head_counterbore_hole(plate, "M5", plate_thickness + 2, position=(x, y, top_z + 1))
b.tapped_hole(block, "M6", thread_depth, position=(x, y, top_z + 1))
```

Use `linear_pattern_points()` and `circular_pattern_points()` for repeated hole
layouts so pitch, bolt-circle diameter, count, and centers stay parameterized.

Maintain enough material around holes and pockets:

- hole edge distance should normally be at least one hole diameter, or at least
  2-3 mm for conceptual small parts;
- counterbore diameter must not equal the local lug or boss width;
- slots and pockets should not exactly touch other cutouts or external faces;
- leave positive wall thickness between neighboring subtractive features.

Before placing lightening slots near fasteners, calculate a slot-to-hole budget
from the actual slot extents, the fastener/counterbore radius, and the angular
relationship of the patterns. If the requested slot dimensions do not fit, move
or shrink the slot and report the change as an assumption rather than creating a
known-invalid journal.

## Ribs And Gussets

For first-pass NX robustness, prefer simple rectangular ribs or wedge-like
solids made from boxes and subtractive cutters. Avoid fragile generated
chamfers on temporary cutter bodies unless the geometry has been tested in NX.

If triangular gussets are required and a direct wedge primitive is unavailable,
use oversized subtractive blocks/cylinders and keep the feature plan simple.

## Export

Always end `build()` with:

```python
b.export_step(output_path)
```

`NXBuilder.export_step()` handles part saving, STEP creator variants, absolute
path resolution, and fallback STEP recovery.

## Common Mistakes To Avoid

- Forgetting to sync `models/cadnx/` after changing `skills/nx-cad/cadnx/`.
- Forgetting to run `skills/nx-cad/scripts/check-journal` before handoff.
- Copying only the generated `.py` to the NX machine.
- Using build123d/CadQuery/OCC imports in an NX journal.
- Calling raw NXOpen builder methods that differ by NX version when a wrapper
  operation exists.
- Using `Face.GetCentroid()` for edge selection; this user's NX binding lacks
  it.
- Using `NXOpen.Features.BooleanBuilder.BooleanOperation`; use the wrapper.
- Defaulting output to `"output.step"`; use script-basename `.step`.
