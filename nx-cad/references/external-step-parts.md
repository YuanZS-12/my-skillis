# External STEP Parts

Read this file when a Siemens NX task includes purchasable components, catalog
hardware, user-supplied STEP files, or assembly references that should not be
redrawn as simple cylinders or boxes.

## Principle

Use real STEP parts for named off-the-shelf components when a reliable catalog
match exists. Use simplified envelope geometry only after `step.parts` was
reachable and returned no exact or near-exact match, or when the user explicitly
requests simplified geometry for speed, clearance planning, or IP reduction.

## Search Workflow

1. Identify named catalog components in the prompt: bearings, screws, motors,
   servos, actuators, connectors, electronics boards, standoffs, rails, and
   other purchasable parts.
2. Use `$step-parts` before generating placeholder geometry. Search exact model
   numbers first, then vendor and alias spellings.
3. For common standard parts, include useful standards and dimensions in the
   query, such as `ISO 4762 M3 12`, `608ZZ bearing`, or `M3 heat-set insert`.
4. If a result is exact or near-exact, download its STEP file with checksum
   verification when available.
5. Store durable downloaded parts under `models/parts/step-parts/<part-id>.step`
   unless the user asks for another location. Temporary exploratory downloads
   may stay in `/tmp`, but final generated NX journals must not depend on them.
6. If the API was reachable and no suitable result exists, record the miss and
   create a simplified envelope with named dimensions and an explicit source
   note.

## External Component Ledger

Every generated NX brief that uses external parts must include an external
component ledger. Keep it concise but complete:

- component name and role;
- selected step.parts id, page URL, API URL, and local STEP path;
- checksum and whether it was verified;
- expected units, normally millimeters unless the source says otherwise;
- chosen insertion datum, origin, axes, and transform;
- whether the journal imports the real STEP part or uses a simplified envelope;
- search misses and aliases tried when no exact or near-exact match exists.

Generated journals that mention named off-the-shelf components should preserve
that ledger as comments near the top of the file:

```python
# External component ledger:
# - 608 bearing: source=<step.parts URL or local path>, mode=imported STEP|simplified envelope, checksum=<sha256 or unknown>, datum=<placement datum>
# - NEMA 17 motor: source=<step.parts URL or local path>, mode=imported STEP|simplified envelope, checksum=<sha256 or unknown>, datum=<placement datum>
```

Use `mode=simplified envelope` only after a catalog miss or when the user
requests clearance-envelope geometry. The envelope still needs named dimensions
and a datum so a later pass can replace it with imported STEP geometry.

## NX Journal Policy

Generated journals should not contain raw `NXOpen.*` import or component-load
code. They should call `NXBuilder` for any external part operation.
`b.import_step_part(...)` is implemented through the official
`NXOpen.Step214Importer` path and imports external STEP geometry into the
current work part. Assembly-level component loading and placement remain
guarded until their official NXOpen APIs are researched and validated.

```python
imported_objects = b.import_step_part("parts/step-parts/608zz.step", name="bearing_608zz")
b.add_component("parts/step-parts/servo.step", name="servo")
b.place_component(component, origin=(0, 0, 12), x_axis=(1, 0, 0), z_axis=(0, 0, 1))
```

Generate `b.import_step_part(...)` only when the intended behavior is to import
the external STEP into the current work part. Do not generate
`b.add_component(...)` or `b.place_component(...)` for production output until
those wrapper methods have official NXOpen source mapping and a real NX runtime
pass. Until then, use documented envelope geometry for assembly component
placement and keep the downloaded STEP path in the ledger for the next
implementation pass.

## Validation

When NX successfully exports the final STEP, validate the NX-exported STEP with
the regular CAD inspection and viewer workflow:

```bash
skills/cad/scripts/inspect refs models/<nx_output>.step --facts --planes --positioning
skills/cad/scripts/snapshot models/<nx_output>.step
```

Then hand the explicit STEP path to `$cad-viewer`. Report catalog parts,
checksum status, envelope substitutions, and any skipped NX runtime or CAD
inspection checks.
