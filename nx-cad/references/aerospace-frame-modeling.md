# Aerospace Frame Modeling

Use this reference for aerospace casings, turbine/compressor rear frames,
diffuser frames, strut rings, bearing support frames, and other circular
patterned high-detail parts.

All raw NXOpen API code must be grounded in the Siemens NXOpen Python Reference
Guide 2512:

`https://docs.sw.siemens.com/en-US/doc/209349590/PL20250429951538534.custom_api.nxopen_python_ref`

The helpers named here intentionally reuse existing `NXBuilder` wrapper paths
already mapped in `official-nxopen-sources.md`. Do not add new raw NXOpen
objects for swept or lofted geometry unless the official guide page has been
recorded there first.

## Required Strategy

1. Build primary rings first: outer case, hub, bearing bores, and large datum
   shoulders.
2. Add structural struts and diffuser windows before small holes and cosmetic
   details.
3. Use local radial/tangential/axial coordinate frames for circular-patterned
   pads, bosses, cavities, and arms:

   ```python
   radial = (math.cos(angle), math.sin(angle), 0.0)
   tangent = (-math.sin(angle), math.cos(angle), 0.0)
   axial = (0.0, 0.0, 1.0)
   pad = b.oriented_box(
       length=pad_tangential_length,
       width=pad_radial_width,
       height=pad_axial_height,
       center=(radius * radial[0], radius * radial[1], z_center),
       u_axis=tangent,
       v_axis=radial,
       w_axis=axial,
   )
   b.boolean_unite(frame, pad)
   ```

4. Use explicit ring-section helpers for grooves and shoulders:

   ```python
   b.annular_groove(
       frame,
       outer_diameter=c_seal_groove_od,
       inner_diameter=c_seal_groove_id,
       depth=c_seal_groove_depth,
       position=(0.0, 0.0, rear_face_z + cutter_overlap),
       direction=(0.0, 0.0, -1.0),
       cutter_overlap=cutter_overlap,
   )
   ```

5. Add complexity budgets near the other parameter guards:

   ```python
   b.require_feature_budget(
       boolean_operations=estimated_boolean_operations,
       micro_holes=estimated_micro_holes,
       patterned_features=strut_count + boss_count + cavity_count,
       max_boolean_operations=160,
       max_micro_holes=180,
       max_patterned_features=120,
   )
   ```

## Struts

Current stable generation should use simple polygon-prism struts or
`oriented_box()`-based local-frame approximations. Label them as approximations
when the prompt implies airfoil, swept, or lofted struts.

Do not claim true aerodynamic strut surfaces unless `NXBuilder` has a
documented swept or lofted helper whose raw NXOpen APIs have been sourced from
the Siemens NXOpen Python Reference Guide 2512 and validated in NX.

## Fillet And Chamfer Policy

High-pattern aerospace frames create dense boolean topology. Avoid final global
fillets such as:

```python
b.fillet(b.get_all_edges(frame), cosmetic_fillet)
b.fillet(b.get_edges_by_axis(frame, axis=(0, 0, 1)), cosmetic_fillet)
```

Prefer local edge treatment:

```python
b.chamfer(
    b.get_edges_in_box(
        frame,
        min_xyz=(-outer_radius, -outer_radius, rear_z - 1.0),
        max_xyz=(outer_radius, outer_radius, rear_z + 1.0),
    ),
    edge_break,
)
```

If the main geometry is complex, omit cosmetic blends until NX runtime confirms
that all structural booleans and STEP export succeed.

## Generation Quality Bar

A generated aerospace frame should include:

- named ring, hub, strut, boss, groove, and fastener parameters;
- local coordinate frames for circular-patterned non-round features;
- `oriented_box()` for radial/tangential pads and cavities;
- `annular_groove()` for C-seal, bearing-retainer, and datum ring grooves;
- `require_feature_budget()` for high-pattern feature plans;
- explicit assumptions for approximated strut airfoil or casting detail;
- a validation plan asking the NX user to report geometry appearance, warnings,
  `.prt` save, and STEP export.
