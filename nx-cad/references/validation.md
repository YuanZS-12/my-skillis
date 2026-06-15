# NX CAD Validation

Read this before reporting success for generated NXOpen journals.

## Principle

Local validation can prove source structure and runtime freshness. It cannot
prove Siemens NX execution, native `.prt` save, or STEP export unless the
journal was actually run inside NX and the user or automation reports the
result.

## Local Static Validation

Always run after generating or modifying a journal:

```bash
skills/nx-cad/scripts/sync-runtime --models-dir models
skills/nx-cad/scripts/check-journal models/<journal>.py
```

These checks prove:

- the journal is valid Python syntax;
- the journal imports `cadnx.NXBuilder`;
- the journal defines `build(output_path: str = None)`;
- prohibited local CAD kernels are absent;
- sibling `cadnx/` runtime files compile.

Use `scripts/bundle/bundle-skill.sh nx-cad --check` before handoff when the
repository `models/cadnx/` runtime should be current.

## Brief-Level Validation Plan

Before coding, list what should be checked in NX:

- expected body or assembly-like body count;
- bounding dimensions and main axes;
- critical hole diameters and axes;
- major feature positions;
- whether cosmetic fillets/chamfers are required or optional;
- expected `.prt` and `.step` paths.

## NX Runtime Validation

When the user runs the journal in Siemens NX, ask for:

- whether geometry appears;
- whether warnings were printed;
- whether `.prt` saved;
- whether `.step` exported;
- the full traceback for failures.

If `.step` exists, it can be inspected with the regular CAD skill tools and CAD
Viewer. Until then, report local checks only.

## Reporting

Final responses for NX CAD generation should include:

- generated `.py` path;
- synced `cadnx/` path;
- static checks actually run;
- assumptions and important dimensions;
- exact files to copy to the NX machine;
- a clear statement that NX execution was not verified locally.

Do not claim:

- `.prt` creation;
- STEP export;
- watertight solids;
- visual correctness;
- manufacturability;

unless those facts are supported by NX runtime output or subsequent STEP
inspection.
