# Raw NXOpen High-Fidelity Route

Read this when the prompt asks to use MCP, `dc_server`, Designcenter, raw/bare
`NXOpen`, `NXOpen lib`, or high-fidelity NXOpen code.

## Contract

Raw NXOpen high-fidelity mode emits direct Siemens NXOpen Python journal code.
It must not import `cadnx` or use `NXBuilder`.

Every journal in this mode must include:

- `RAW_NXOPEN_HIGH_FIDELITY = True`;
- either `MCP_API_REVIEW = {...}` when `dc_*` tools were used, or
  `STATIC_ONLY_NXOPEN_REVIEW = {...}` when they were unavailable;
- explicit `NXOpen` submodule imports for every family used, such as
  `NXOpen.Features`, `NXOpen.Annotations`, `NXOpen.UF`, or
  `NXOpen.Assemblies`;
- `create_work_part_if_needed(session)` when the journal can run without an
  active work part;
- named parameters near the top of `main()` or a dedicated parameter function;
- helper functions for repeated geometry, point generation, feature creation,
  PMI, save, and export behavior;
- runtime diagnostics with `print(...)` for work part, committed features,
  body counts, save/export paths, and skipped optional features;
- nonblocking guards for optional PMI, notes, colors, or cosmetic details after
  the primary solid has been created.

## API Review

When MCP tools are available:

1. Use `dc_search`, `dc_semantic_search`, or `dc_lookup_pattern` before coding.
2. Use `dc_get_api_info` for the exact classes, builders, enums, properties,
   methods, creators, collections, and return objects written into the journal.
3. Record the reviewed APIs in `MCP_API_REVIEW`.
4. Select `mcp_review` unless the user explicitly requested execution. In
   authorized `mcp_execute`, call `dc_run_journal` only after static checks and
   follow the bounded execution/evidence rules in `mcp-runtime.md`.

When MCP tools are not available, continue only with explicit uncertainty:

```python
STATIC_ONLY_NXOPEN_REVIEW = {
    "reason": "Designcenter/NXOpen MCP tools were not available in this agent session.",
    "checks": ["skills/nx-cad/scripts/check-journal ..."],
}
```

Do not fabricate MCP evidence.

## Code Shape

Prefer this structure:

1. imports and evidence marker;
2. pure math and parameter helpers;
3. NX object creation helpers;
4. work-part creation helper;
5. optional PMI/annotation/color helpers wrapped so failures are reported but
   do not erase the primary model;
6. save/export helpers when requested;
7. `main()` with parameters, derived values, builder calls, diagnostics, and
   output handling.

All `Create*Builder(...)` objects must be destroyed in `finally` blocks. Dispose
load-status, rule-option, and similar disposable helper objects when NXOpen
returns them.

## Quality Bar

High-fidelity means the code should express the intended NX model with the
native API family rather than reducing it to wrapper primitives. Use direct
NXOpen feature builders for extrudes, revolves, holes, blends, chamfers,
patterns, sections, through-curves, sweeps, shells, drafts, expressions, PMI,
assemblies, save, and export when those operations match the requested part.

For mechanical parts, raw NXOpen high-fidelity can still be appropriate:
feature builders, datum references, named expressions, precise edge/face
selection, pattern builders, and PMI may be better than wrapper primitives.

For smooth or station-based parts, generate analytic points or curves from
named parameters, transform them through local coordinate frames, create
sections or splines through reviewed NXOpen APIs, and commit the appropriate
loft/sweep/through-curve feature.

## Reporting

Final responses for this mode must state:

- that raw NXOpen high-fidelity mode was selected;
- whether MCP API-review or static-only review was used;
- exact `dc_*` tools called when MCP was available;
- generated journal path;
- local static checks actually run;
- that `cadnx/` is not required unless the journal imports it, which this mode
  should not do;
- selected runtime mode and whether validation remains a manual NX handoff or
  used an explicitly authorized `agent:dc_mcp` run.
