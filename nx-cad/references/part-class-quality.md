# NX CAD Part-Class Quality

Read this when generating or repairing a complex NX journal, and whenever the
requested part class has recognizable industrial conventions.

## Principle

Choose operations and feature order from the part class. A model that merely
contains the named primitives is not acceptable when the requested object has
well-known geometry, datums, interfaces, or manufacturing cues.

## Common Classes

### Hydraulic manifold block

Expected: machined rectangular body, valve pads, port bosses, intersecting oil
passages, counterbores, dowel holes, edge breaks, named wall and edge guards.

Forbidden shortcuts: decorative cylinders that do not intersect passages,
tangent counterbores, unguarded crossed holes, arbitrary side pockets.

### Structural bracket or connector

Expected: mounting pads, lug or clevis geometry, pin-hole edge distance, ribs,
localized fillets, realistic relief pockets, stable local axes.

Forbidden shortcuts: checking hole diameter against through-thickness when the
actual wall is vertical height or end distance; unsupported angled slots.

### Bearing housing

Expected: coaxial bore, bearing seat shoulder, bolt pattern, flange or pad,
cover interface, lubrication or drain detail when appropriate.

Forbidden shortcuts: plain cylinder plus hole with no seat, no shoulder, or no
bolt interface.

### Impeller, propeller, turbine, or blisk

Expected: revolved hub or backplate, tapered or curved hub surfaces, named
blade stations, airfoil-like sections, sweep or twist intent, root or platform
detail.

Forbidden shortcuts: high-precision blade rows made primarily from rectangular
boxes, uniform vertical plates, or dozens of unannotated polygon-prism chunks.
If sweep or loft is unavailable, downgrade the claim from high precision and
report the approximation.

### Enclosure or casing

Expected: shell or wall intent, ribs, bosses, gasket or lip features, mounting
interfaces, conservative fillets, explicit clearances.

Forbidden shortcuts: solid block with surface-only decoration, unsupported
shell assumptions, missing screw boss wall checks.

## Brief Checklist

- Name the part class and manufacturing style.
- List expected datum axes and primary mating interfaces.
- List features that are functional versus cosmetic.
- State approximation level for unsupported geometry.
- Define local static checks and NX runtime checks before coding.

## Misleading Primitive Approximation

Do not claim high-fidelity smooth, aerodynamic, ergonomic, organic, or freeform
geometry when the journal is mainly boxes, cylinders, polygon prisms, and
booleans. If the user explicitly asks for a rough or printable blockout, set and
report a low-fidelity fallback. Otherwise use raw NXOpen advanced geometry with
MCP API-review evidence.
