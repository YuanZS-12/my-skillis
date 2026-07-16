# NX CAD Parameters

Read this when designing or reviewing generated NXOpen journal parameters.

## Principle

Parameters are the model contract. Generated NX journals should make design
intent explicit through named dimensions near the top of `build()`, then derive
dependent dimensions from those inputs instead of repeating hard-coded values.

NXOpen API parameter names, object families, enums, and structs are checked
against the Siemens NXOpen Python Reference Guide 2512 namespace index:

`https://docs.sw.siemens.com/documentation/external/PL20250429951538534/en-US/custom_api/nxopen_python_ref/a00006.html`

That official page is the `NXOpen` namespace reference. It is the source for
which NXOpen classes/enums/structs exist, not for the user's part dimensions.
Part dimensions come from the prompt, safe skill defaults, and derived CAD
relationships documented below.

## Parameter Brief

Before writing source, identify:

- independent dimensions from the prompt;
- derived dimensions, centers, pitches, clearances, and offsets;
- units and coordinate axes;
- valid value ranges when a feature can become impossible;
- which parameters affect each feature group;
- which functional surfaces, datums, axes, or mating interfaces each parameter
  controls;
- which dimensional guard protects each tight feature;
- what NX runtime check or user-observed geometry proves the parameter worked.

## Naming

Use lower_snake_case names that describe intent:

- Good: `base_length`, `wall_thickness`, `lug_gap`, `bolt_circle_diameter`,
  `chamfer_offset`, `keyway_depth`.
- Avoid: `d1`, `offset2`, `magic`, `fix`, `tmp_width`.

Use `*_diameter` and `*_radius` precisely. Do not pass a radius where
`NXBuilder.cylinder()` expects a diameter.

## Derive, Do Not Drift

Compute dependent values from the real constraints:

- centers from count, pitch, and symmetry;
- hole depth from target thickness plus overcut;
- mating offsets from part heights and interface planes;
- repeated features from arrays or loops with named pitch/count values.

Avoid copying the same dimension into multiple unrelated constants. If a wall,
gap, or pitch changes, all dependent placements should update from one source.

## Feature Grouping

Group parameters in the same order as the model:

1. overall layout;
2. primary solids;
3. holes/cutouts;
4. ribs/bosses/detail features;
5. cosmetic fillets/chamfers;
6. export.

Complex journals should use small local helper functions only for repeated
math. Keep NXBuilder calls inside `build()` unless the helper is pure geometry
calculation and does not touch NXOpen.

## Bounds

Generated journals do not need a full UI-style parameter system, but they should
guard obvious invalid derived values:

- wall thickness must be less than half the containing width/depth;
- hole diameter must be positive and smaller than the boss or plate region;
- counterbore diameter must be smaller than the local lug, boss, or pad width
  with positive side wall remaining;
- hole edge distance should normally be at least one hole diameter when space
  allows, and never exactly tangent to a slot, pocket, or external wall;
- fillet radius and chamfer offset should be conservative;
- through-cut tools should be slightly longer than the target thickness.
- boolean union features must have positive body overlap, not just a shared
  face;
- subtractive cutters that open into another cutout must overlap that cutout,
  not just start tangent to it.

Use the runtime guards when the generated model has tight geometry:

```python
b.require_positive(base_length=base_length, plate_thickness=plate_thickness)
b.require_min_wall(lug_width, counterbore_diameter, min_wall=1.5, label="M5 counterbore")
b.require_edge_distance(edge_distance, clearance_diameter, min_ratio=1.0, label="mounting hole")
```

These guards are intentionally simple and NX-independent. They catch common
zero-wall/tangent mistakes before the wrapper submits a fragile boolean to NX.

## Standard Mechanical Feature Parameters

Prefer named screw-size parameters and standard helper calls:

- `mount_screw_size = "M5"` instead of repeating `5.5` clearance diameters;
- `b.screw_clearance_hole(...)` for normal clearance holes;
- `b.tapped_hole(...)` for tap-drill geometry;
- `b.socket_head_counterbore_hole(...)` for socket-head screw seats;
- `b.countersink_hole(...)` only when a flat-head relief is requested.

For repeated features, define the pattern once:

- `bolt_count`, `bolt_circle_diameter`, `start_angle_degrees`;
- `hole_pitch`, `hole_count`, `first_hole_position`;
- use `circular_pattern_points()` or `linear_pattern_points()` to derive
  centers instead of hand-copying each coordinate.

For conceptual models, prefer safe assumptions and report them. For fit-critical
or safety-critical dimensions, ask one focused clarification question.

## Industrial Detail Parameters

Industrial refinement must be parameterized, not scattered as literal values.
Choose the parameter set from the inferred manufacturing style:

- **Machined**: `chamfer_offset`, `edge_break`, `pocket_depth`,
  `counterbore_depth`, `relief_slot_width`, `datum_pad_height`,
  `minimum_edge_distance`, `feature_overlap`, `cutter_overlap`.
- **Molded/enclosure**: `wall_thickness`, `outer_radius`, `inner_radius`,
  `boss_outer_diameter`, `boss_hole_size`, `rib_thickness`, `rib_height`,
  `lid_lip_depth`.
- **Structural bracket**: `mount_pad_width`, `mount_pad_height`,
  `rib_thickness`, `gusset_height`, `slot_length`, `slot_width`,
  `bolt_edge_distance`.
- **Rotary/shaft-like**: `shaft_diameter`, `bore_diameter`,
  `shoulder_diameter`, `shoulder_length`, `end_chamfer`, `set_screw_size`
  when explicitly requested.

Use conservative defaults only when they fit the available envelope:

- edge breaks/chamfers: normally 0.5-2.0 mm for small/medium parts;
- cosmetic fillets: normally 1.0-3.0 mm and smaller than nearby wall or rib
  thickness;
- molded ribs: normally no thicker than the wall thickness unless specified;
- bosses and counterbores: require positive remaining side wall;
- pockets, slots, and lightening cuts: keep them clear of holes and external
  walls by named edge-distance parameters.
- raised details and united pads: start with a named `feature_overlap` below
  the mating face so NX sees real volume intersection;
- bore-connected keyways and reliefs: start with a named `cutter_overlap` into
  the bore or neighboring cutout to avoid tangent zero-wall booleans.

Every inferred detail should have a named parameter, a guard when geometry is
tight, and a brief assumption line in the final report.

For circular slot and hole patterns, compute a slot-to-hole budget before
modeling:

- radial clearance from the slot's nearest extent to the hole or counterbore
  radius;
- tangential/angular clearance when the patterns are offset;
- outer and inner edge distance from the slot extents;
- minimum accepted material between the slot and any fastener feature.

If the budget is negative, revise the slot radius, length, count, or start angle
before emitting NXBuilder calls.

## Industrial Parameter Checklist

For each generated journal, keep this brief near the top of `build()` as code
structure, even if not all headings are written as comments:

- independent parameters: prompt dimensions, screw sizes, counts, pitches;
- derived parameters: radii, centers, top faces, cut depths, edge distances;
- standards: metric screw helper tables, default units in millimeters;
- industrial style: machined, molded/enclosure, structural, rotary, or generic;
- detail parameters: chamfers, radii, ribs, bosses, pockets, pads, slots, or
  shoulders selected for that style;
- validation guards: positive dimensions, min wall, edge distance, overcut;
- boolean robustness: `feature_overlap`, `cutter_overlap`, and
  `through_overcut` for every feature that is united or subtracted;
- affected features: the named body, pad, lug, boss, bore, pocket, blade
  station, or datum each parameter changes;
- dimensional guard mapping: the specific `require_min_wall()` or
  `require_edge_distance()` call that protects each close hole, pocket,
  counterbore, lug, or pad;
- feature order: primary solids, pockets/slots, holes/counterbores, booleans,
  fillets/chamfers, STEP export.

Prefer named values such as `mount_screw_size`, `clearance_diameter`,
`counterbore_diameter`, `edge_distance`, and `minimum_wall` over anonymous
numeric literals inside boolean features.

## Common Failure Patterns

- Mixing X/Y/Z axes between the prompt and NXBuilder calls.
- Treating `origin` of `box()` as a center instead of lower-left-lower corner.
- Forgetting cylinder `axis` when modeling shafts along X or Y.
- Applying global `get_all_edges()` chamfers to complex bodies.
- Using large cosmetic radii that NX cannot blend after booleans.
- Hardcoding Mac paths into generated journals.
- Repeating manual cutter sequences for slots or counterbores instead of using
  `slot_cut()` and `counterbore_hole()`.
