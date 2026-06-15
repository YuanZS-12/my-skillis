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

## Generated File Structure

Every generated file must follow this shape:

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
    # 2. Modeling: NXBuilder calls
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

Structure source:

- `NXOpen.Session.GetSession()` comes from the official `NXOpen.Session`
  reference.
- Work/display part behavior comes from `NXOpen.PartCollection`.
- The `build(output_path: str = None)` and `main()` wrapper are `nx-cad`
  conventions around the official API so generated journals are portable,
  testable, and callable from NX.
- The sibling `cadnx/` import is a local runtime wrapper convention; raw NXOpen
  calls remain inside `cadnx.NXBuilder`.

## Wrapper Operations

| Intent | NXBuilder call |
|--------|----------------|
| Rectangular block | `b.box(length, width, height, origin=(x, y, z))` |
| Rounded rectangular block | `b.rounded_box(length, width, height, radius, origin=(x, y, z))` |
| Cylinder / boss / pin | `b.cylinder(diameter, height, origin=(x, y, z), axis=(0, 0, 1))` |
| Through-hole | `hole = b.hole(dia, depth, position=(x, y, z), direction=(0, 0, -1))`; then `b.boolean_subtract(body, hole)` |
| Counterbore | `b.counterbore_hole(target, hole_dia, hole_depth, cbore_dia, cbore_depth, position=(x, y, z), direction=(0, 0, -1))` |
| Rounded slot cut | `b.slot_cut(target, length, width, depth, center=(x, y, z), axis=(1, 0, 0), direction=(0, 0, -1))` |
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

## Modeling Strategy

- Use named parameter variables near the top of `build()`.
- Compose robust solids from boxes and cylinders first.
- Use boolean subtract for holes, slots, lightening cutouts, and trimming.
- Use boolean unite for bosses, ribs, gussets, mounting pads, and multi-block
  parts.
- Prefer wrapper compound operations such as `slot_cut()` and
  `counterbore_hole()` over repeating raw cutter booleans in generated journals.
- Make subtractive tools slightly oversized so through-cuts fully pass the
  target body.
- Keep generated fillets/chamfers conservative; NX will fail if radius/offset
  exceeds local edge conditions.
- Avoid topology-sensitive selectors unless the model has already been kept
  very simple.

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
