# NX CAD Benchmark Workflow

Use the repository `benchmarks/` prompts as regression cases for `nx-cad`
generation quality. The benchmark files describe expected geometry in prose and
test-table form; they are not user-facing JSON specs.

## Purpose

- Keep generated NXOpen journals aligned with durable text-to-cad benchmark
  requirements.
- Capture failures reported from real Siemens NX runs as regression cases.
- Improve `cadnx.NXBuilder` when multiple generated journals hit the same
  NXOpen API or topology failure.

## Local Static Gate

After generating or updating a benchmark journal under `models/`, run:

```bash
skills/nx-cad/scripts/sync-runtime --models-dir models
skills/nx-cad/scripts/check-journal models/<journal>.py
```

For the current repository model set, run:

```bash
python3 tests/python/skills/nx-cad/test_nx_cad_scripts.py
```

This verifies:

- generated journals are valid Python source;
- journals import `cadnx.NXBuilder`;
- journals do not import build123d, CadQuery, OCC, FreeCAD, or OpenSCAD;
- `models/cadnx/` is synchronized with `skills/nx-cad/cadnx/`.

## NX Runtime Gate

Local checks cannot prove NXOpen execution. For each benchmark handoff, copy the
generated journal and sibling `cadnx/` directory to the Siemens NX machine, then
run the journal via File -> Execute -> NX Open.

Record the result:

- journal path;
- NX version if known;
- whether geometry appeared;
- whether `.prt` saved;
- whether `.step` exported;
- full traceback or warning text for failures.

## Repair Policy

- Patch `skills/nx-cad/cadnx/builder.py` when the failure is an NXOpen API
  compatibility issue shared by multiple models.
- Patch the generated journal when the model plan is fragile, over-detailed, or
  selects the wrong topology.
- Keep fillets and chamfers cosmetic by default; wrappers should warn and
  continue when NX rejects a decorative edge operation.
- After every repair, sync `cadnx/`, run `check-journal`, and ask the user to
  rerun the same journal in NX before regenerating unrelated geometry.

## Benchmark Priorities

Start with these because they exercise common mechanical CAD features:

- `04-stepped-shaft-keyway.md`: X-axis cylinders, keyway cut, end chamfers.
- `06-clevis-bracket-lightening-cutouts.md`: holes, ribs, cutouts, fillets.
- `08-centrifugal-impeller.md`: radial repeated features and blade unions.
- `10-planetary-gear-stage.md`: multi-body assembly-like layout.

Treat successful NX execution of these cases as the first stability milestone.
