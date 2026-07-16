# NX CAD Design Ledger

Read this before writing or repairing a nontrivial NX journal, and always read
it for raw NXOpen high-fidelity mode, assemblies, external STEP parts, PMI,
named datums, or user-reported NX runtime failures.

The ledger is an internal working checklist. Do not ask the user to provide it
as JSON. Build it from the prompt, local files, MCP evidence, and explicit
assumptions before coding.

## Required Ledger Fields

### Task And Mode

- Task type: new part, assembly, modification, repair, export issue, or
  post-NX STEP review.
- Selected generation mode: wrapper, raw NXOpen high-fidelity, or raw
  static-only.
- Mode trigger: default wrapper, MCP request, `dc_server`, Designcenter,
  raw/bare `NXOpen`, `NXOpen lib`, high-fidelity request, or explicit user
  override.
- Output journal path under `models/`.
- Whether sibling `cadnx/` is required.

### Coordinates And Units

- Units.
- Origin and datum frame.
- Base plane and up axis.
- Work-part behavior: existing active part, create display part if missing, or
  require an open part.
- Expected native `.prt` path behavior.
- Expected `.step` output path behavior.

### Parameters

- Independent prompt parameters.
- Derived parameters such as centers, pitches, radii, depths, offsets,
  overcuts, and local frames.
- Standard dimensions such as screw sizes, clearance diameters, counterbore
  sizes, or bearing fits.
- Guards needed for positive dimensions, minimum walls, edge distances, and
  boolean overlap.

### Features

- Primary solids or base features.
- Functional cuts, holes, pockets, bosses, ribs, slots, seats, pads, and
  interfaces.
- Cosmetic fillets, chamfers, colors, PMI, and annotations.
- Feature order and dependencies.
- Features allowed to fail noncritically after the primary model exists.

### Raw NXOpen API Evidence

For raw NXOpen high-fidelity mode:

- Required NXOpen submodules, such as `NXOpen.Features`,
  `NXOpen.Annotations`, `NXOpen.UF`, or `NXOpen.Assemblies`.
- Builders, collections, creators, enums, properties, and methods to review.
- MCP tools used, or the reason for `STATIC_ONLY_NXOPEN_REVIEW`.
- API facts that must be reflected in the journal source.
- Builder lifecycle/disposal requirements.

### External Components

When named purchased parts or external STEP files are involved:

- Part name or id.
- Source URL or local path.
- Checksum when known.
- Units assumption.
- Placement datum and transform.
- Whether the journal imports the real STEP or uses a simplified envelope.

### Validation Targets

- Local static checks to run.
- Manual Siemens NX runtime checks the user should report.
- Expected body or component count.
- Expected bounding dimensions and main axes.
- Critical feature dimensions and positions.
- Expected `.prt` and `.step` paths.
- Post-NX STEP inspection, snapshot, and CAD Viewer handoff if a STEP exists.

## Mode-Specific Notes

### Wrapper Mode

Use wrapper mode unless the prompt asks for MCP-backed raw NXOpen or explicitly
forbids `NXBuilder`. The ledger should identify the `NXBuilder` calls that
carry each feature and the guards that protect tight geometry. Sync `cadnx/`
before handoff.

### Raw NXOpen High-Fidelity Mode

Use raw NXOpen high-fidelity mode when the prompt asks for MCP, `dc_server`,
Designcenter, raw/bare `NXOpen`, `NXOpen lib`, or high-fidelity NXOpen code.
The ledger must include API evidence and the journal must not depend on
`cadnx/`.

### Static-Only Raw NXOpen

If MCP tools were expected but unavailable, record the missing tools and use
`STATIC_ONLY_NXOPEN_REVIEW`. Keep the journal conservative, include runtime
diagnostics, and tell the user that Siemens NX runtime validation is required.

