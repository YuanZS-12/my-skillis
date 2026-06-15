# NX CAD Parameters

Read this when designing or reviewing generated NXOpen journal parameters.

## Principle

Parameters are the model contract. Generated NX journals should make design
intent explicit through named dimensions near the top of `build()`, then derive
dependent dimensions from those inputs instead of repeating hard-coded values.

## Parameter Brief

Before writing source, identify:

- independent dimensions from the prompt;
- derived dimensions, centers, pitches, clearances, and offsets;
- units and coordinate axes;
- valid value ranges when a feature can become impossible;
- which parameters affect each feature group;
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
- fillet radius and chamfer offset should be conservative;
- through-cut tools should be slightly longer than the target thickness.

For conceptual models, prefer safe assumptions and report them. For fit-critical
or safety-critical dimensions, ask one focused clarification question.

## Common Failure Patterns

- Mixing X/Y/Z axes between the prompt and NXBuilder calls.
- Treating `origin` of `box()` as a center instead of lower-left-lower corner.
- Forgetting cylinder `axis` when modeling shafts along X or Y.
- Applying global `get_all_edges()` chamfers to complex bodies.
- Using large cosmetic radii that NX cannot blend after booleans.
- Hardcoding Mac paths into generated journals.
- Repeating manual cutter sequences for slots or counterbores instead of using
  `slot_cut()` and `counterbore_hole()`.
