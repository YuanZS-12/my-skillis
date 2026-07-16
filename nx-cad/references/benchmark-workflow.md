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

Local checks cannot prove NXOpen execution. The user runs each benchmark
manually via File -> Execute -> NX Open. MCP tools review APIs only; the agent
never calls `dc_run_journal`, launches, or closes NX.

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
- After every repair, sync `cadnx/`, run `check-journal`, allocate a new run ID,
  and ask the user to rerun manually. Stop within three attempts.

## Benchmark Priorities

Start with these because they exercise common mechanical CAD features:

- `04-stepped-shaft-keyway.md`: X-axis cylinders, keyway cut, end chamfers.
- `06-clevis-bracket-lightening-cutouts.md`: holes, ribs, cutouts, fillets.
- `08-centrifugal-impeller.md`: radial repeated features and blade unions.
- `10-planetary-gear-stage.md`: multi-body assembly-like layout.

Treat successful NX execution of these cases as the first stability milestone.

## NX Journal Quality Fixtures

| Fixture | Purpose | Must show | Forbidden |
| --- | --- | --- | --- |
| `nx_benchmark_hydraulic_manifold.py` | machined block workflow | pads, ports, counterbores, dowels, guarded wall/edge distances | tangent counterbores |
| `nx_benchmark_bearing_housing.py` | rotary seat workflow | bore, bearing shoulder, flange bolt pattern, cover interface | plain cylinder-only seat |
| `nx_benchmark_quick_release_connector.py` | lug/clevis workflow | pin-hole edge guards, ribs, side pockets, localized fillets | wrong-direction wall guard |
| `nx_benchmark_revolved_impeller_hub.py` | rotating-blade workflow foundation | revolved hub/backplate and named blade station ledger | primitive-only high-precision claim |
