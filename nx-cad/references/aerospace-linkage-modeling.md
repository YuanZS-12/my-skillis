# Aerospace Linkage Modeling

Use this reference for flight-control bellcranks, control arms, torque links,
pushrod links, clevis brackets, lugged levers, and similar aerospace linkage
parts.

All raw NXOpen API code must be grounded in the Siemens NXOpen Python
Reference Guide 2512. In short: use the Siemens NXOpen Python Reference Guide 2512
for every new raw API shape:

`https://docs.sw.siemens.com/en-US/doc/209349590/PL20250429951538534.custom_api.nxopen_python_ref`

The helpers named here reuse existing `NXBuilder` cylinder, extrusion,
boolean, local-frame, and ring-groove operations already mapped in
`official-nxopen-sources.md`. Do not add new raw NXOpen object families for
threads, drafting, embossing, lofting, or PMI unless the official guide page is
recorded there first.

## Required Strategy

1. Define datums and load paths: pivot center, arm axes, lug centers, clevis
   axis, and side-face direction.
2. Build primary solids first: hub/bushing boss, tapered arms, lug bosses, and
   clevis ears.
3. Use semantic helpers for critical interfaces:

   ```python
   b.bushing_boss(
       body,
       boss_diameter=pivot_boss_diameter,
       boss_height=hub_thickness,
       bore_diameter=pivot_bore_diameter,
       center=(0.0, 0.0, 0.0),
       axis=(0.0, 1.0, 0.0),
       feature_overlap=feature_overlap,
       through_overcut=through_overcut,
   )
   b.bearing_seat(
       body,
       bore_diameter=pivot_bore_diameter,
       seat_diameter=bearing_seat_diameter,
       through_depth=hub_thickness,
       seat_depth=bearing_seat_depth,
       position=(0.0, -hub_thickness / 2.0 - cutter_overlap, 0.0),
       direction=(0.0, 1.0, 0.0),
       cutter_overlap=cutter_overlap,
   )
   b.clevis(
       body,
       length=clevis_length,
       width=clevis_width,
       ear_thickness=clevis_ear_thickness,
       gap=clevis_gap,
       pin_hole_diameter=clevis_pin_diameter,
       center=clevis_center,
       u_axis=clevis_axis,
       v_axis=clevis_width_axis,
       w_axis=clevis_gap_axis,
       feature_overlap=feature_overlap,
       through_overcut=through_overcut,
   )
   ```

4. Add side pockets after primary solids and before holes. Keep pockets shallow
   and use `through_overcut` or `cutter_overlap`.
5. Add pin, pivot, and fastener holes after all bosses and lugs have real
   overlap.
6. Add local fillets/chamfers last. Prefer `get_edges_near(...)` and
   `get_edges_in_box(...)`; avoid global edge selection on complex linkage
   bodies.

## Manufacturing Detail

When the prompt does not specify materials or processes, make conservative
metadata comments rather than claiming certification:

- candidate material, such as 7075-T73 aluminum or Ti-6Al-4V, if appropriate;
- bushing/bearing interface assumptions;
- surface finish or coating intent, such as hard anodize, dry-film lube, or
  passivation;
- shot-peen, NDT, serialization, or part-number pads only as represented
  geometry or source comments.

Do not claim flightworthiness, stress margin, fatigue life, or compliance from
generated geometry alone.

## Static Validation Expectations

For bellcrank/control-linkage journals, strict validation expects at least one
semantic linkage helper:

- `bearing_seat(...)` for pivot or bearing interfaces;
- `bushing_boss(...)` for reinforced lug or hub bosses;
- `clevis(...)` for forked pin interfaces.

Use `require_feature_budget(...)` when patterned holes, repeated ribs, many
booleans, or dense inspection details are present.
