# NX 2606 Manual Runtime Probes

These probes are generated and statically checked by `nx-cad`, but only the
user may execute them manually inside Siemens NX through:

```text
File -> Execute -> NX Open
```

Do not ask an agent, MCP server, shell command, batch file, or GUI automation
to start NX or execute these journals.

Copy this entire directory to the NX machine because the numbered probes use
the sibling `_probe_support.py` module. Run one probe at a time in numeric
order and return the generated `.nxreport.json` after each run.

Current probes:

| Probe | Purpose | Recipe status |
| --- | --- | --- |
| `01_create_part.py` | work-part creation/load-status handling | verified by manual NX 2606 run |
| `02_closed_polyline_section.py` | closed Section and curve rules | verified by manual NX 2606 run |
| `03_closed_spline_section.py` | periodic StudioSplineBuilderEx curve | verified by manual NX 2606 run |
| `04_through_curves_solid.py` | two-section solid loft | verified by manual NX 2606 run |
| `05_sweep_fixed_orientation.py` | SweptBuilder1 two identical sections + fixed-orientation solid | verified by manual NX 2606 run |
| `06_sweep_two_sections.py` | SweptBuilder1 two-section tapered solid | verified by manual NX 2606 run |
| `07_sweep_angular_law.py` | SweptBuilder1 two corresponding sections + explicit spine + linear angular-law solid | experimental; repaired after invalid-orientation failure and requires manual rerun |
| `08_boolean_unite.py` | overlapping-body boolean unite | verified by manual NX 2606 run |
| `09_edge_blend.py` | collector + AddChainset edge blend | verified by manual NX 2606 run |
| `10_step_ap242.py` | generic StepCreator native save and solid STEP export | rejected configuration; current output remains metadata-only with `ObjectTypes.Solids=True` |

Probes `05` through `07` use `SweptBuilder1`, introduced in NX 2412 through
`work_part.Features.FreeformSurfaceCollection.CreateSweptBuilder1(...)`.
Siemens marks the older `SweptBuilder` API used by the failed S3 configuration
deprecated from NX 2412. The new probes remain experimental until the user runs
them manually and returns their reports.

Validate a returned result locally without starting NX:

```bash
skills/nx-cad/scripts/check-runtime-report \
  models/nx_runtime_probes/nx2606/04_through_curves_solid.nxreport.json \
  --expected-bodies 1
```

Successful manual runtime evidence may promote the matching recipe from
`experimental` to `verified`. Static checks alone cannot do so.
