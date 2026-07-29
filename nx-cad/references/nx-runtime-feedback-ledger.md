# NX Runtime Feedback Ledger

Record user- or automation-reported NX results here. Local static checks are
not enough to mark a helper production-ready.

## Entry Format

```markdown
## YYYY-MM-DD - <journal path> - <NX version if known>

- Result: success|failure
- Operation class: boolean|fillet|chamfer|revolve|sweep|loft|export|save
- Traceback or warning:
- Root cause:
- Patch made:
- Follow-up checks:
```
```

## 2026-07-06 - `models/high_precision_three_axis_drone_gimbal.py` - NX version unknown

- Result: failure, then locally repaired.
- Operation class: boolean.
- Traceback or warning: `rectangular_pocket currently supports Z-axis directions only`.
- Root cause: generated journal used `rectangular_pocket()` for side-facing Y
  pockets even though the wrapper only supported Z-axis pocket directions.
- Patch made: replaced side pockets with explicit `box()` cutters plus
  `boolean_subtract()`.
- Follow-up checks: strict journal check and nx-cad Python tests passed locally;
  user NX rerun still required for runtime success.

## 2026-07-06 - `models/high_precision_hydraulic_manifold_block.py` - NX version unknown

- Result: failure, then locally repaired.
- Operation class: boolean.
- Traceback or warning: NX reported the tool and target did not form a complete
  intersection or had a touch condition that would create zero wall thickness.
- Root cause: valve mounting counterbore was tangent to the pad boundary.
- Patch made: moved `valve_mount_y` inward and added a counterbore edge guard.
- Follow-up checks: strict journal check and nx-cad Python tests passed locally;
  user NX rerun still required for runtime success.

## 2026-07-06 - `/Users/albert/models/S2.py` - NX version unknown

- Result: failure, then locally repaired.
- Operation class: feature budget guard.
- Traceback or warning: `boolean_operations=210 exceeds budget 120`.
- Root cause: intentional impeller stress test exceeded the default budget
  without declaring a higher model-specific max.
- Patch made: added explicit `max_boolean_operations=240` and
  `max_patterned_features=160`.
- Follow-up checks: strict journal check, nx-cad Python tests, and runtime sync
  check passed locally; user NX rerun still required for runtime success.

## 2026-07-06 - `/Users/albert/models/S5.py` - NX version unknown

- Result: failure, then locally repaired.
- Operation class: parameter guard.
- Traceback or warning: `fork pin lug leaves -1.000 mm side wall; minimum is 1.500 mm`.
- Root cause: generated journal compared pin-hole diameter against the
  through-thickness direction instead of checking vertical wall and end edge
  distance.
- Patch made: replaced wrong-direction wall guard with vertical wall and
  end-distance guards.
- Follow-up checks: strict journal check, nx-cad Python tests, and runtime sync
  check passed locally; user NX rerun still required for runtime success.

## 2026-07-15 - `models/S3.py` conversation / `models/S4.py` journal - NX 2606

- Result: repeated user-run failures; final ThroughCurves repair remains
  pending until the user reports complete runtime and artifact evidence.
- Operation class: sweep orientation, sweep section, through-curves repair.
- Traceback or warning: `Invalid orientation method specified.` followed by
  repeated `Invalid section string definition.` failures.
- Root cause: MCP lookup established that individual API objects existed but
  did not validate the complete Section + Sweep + Orientation + Law recipe for
  NX 2606. The repair changed the final API family to `ThroughCurvesBuilder`
  without updating embedded evidence or satisfying the raw journal contract.
- Patch made: the static checker now rejects missing raw evidence, unsafe
  builder lifecycle, swallowed critical booleans, missing raw linkage design
  ledger, and unused guide/spline helpers. S4 remains an expected-failure
  regression fixture rather than a verified model.
- Structured evidence: `runtime-results/nx2606/`.
- Follow-up checks: user must manually run any repaired probe/journal in NX;
  the agent must not start NX. Verification requires one final body, native PRT
  save, and a non-empty returned STEP before promoting the recipe.

## 2026-07-15 - NX 2606 probe suite 01-04 and 08-10 - NX 2606

- Result: probes 01, 02, 03, 04, 08, and 09 succeeded in a manual user-run NX
  session; probe 10 failed during STEP creator construction.
- Verified operations: work-part creation, closed polyline Section, periodic
  StudioSplineBuilderEx curve, two-section ThroughCurves solid, overlapping
  cylinder boolean unite, and single-edge AddChainset blend.
- STEP failure: `NXOpen.DexManager` has no `CreateStep214Creator` attribute and
  suggests `CreateStepCreator`.
- Root cause: the STEP probe used the version-specific AP214 creator exposed
  by some bindings instead of preferring the generic creator available in NX
  2606.
- Patch made: probe support now prefers `CreateStepCreator`, configures AP242
  and DisplayPart export, and retains `CreateStep214Creator` only as a fallback
  for other bindings. The old NX 2606 recipe is recorded as rejected and the
  generic creator recipe remains experimental pending a user rerun of probe 10.
- Source evidence: `models/S2.py`; structured records under
  `runtime-results/nx2606/`.
- Manual boundary: all results were produced by the user's manual NX run; the
  agent did not start or operate NX.

## 2026-07-15 - NX 2606 probe 10 rerun - NX 2606

- Result: failure before STEP creator construction.
- Operation class: work-part creation.
- Traceback or warning: `NXOpen.NXException: File already exists` from
  `session.Parts.NewDisplay(path, ...)`.
- Root cause: the first probe run left `10_step_ap242.prt`; the rerun attempted
  to create the same native part path.
- Patch made: shared probe support and the raw journal template now choose the
  first available `_run_001`, `_run_002`, and subsequent suffix without
  deleting or overwriting prior PRT evidence.
- Follow-up: user manually reruns probe 10 with the updated
  `_probe_support.py`; STEP creator validation remains pending.

## 2026-07-15 - NX 2606 probe 10 repaired rerun and artifact review - NX 2606

- Runtime result: the manual user-run NX session reported success, one body,
  and a 2221-byte STEP file.
- Artifact result: failed deterministic review after the returned STEP was
  copied to `models/nx_runtime_probes/nx2606/10_step_ap242.step`.
- Operation class: native save and STEP export.
- Finding: the AP242 file contains product metadata and an origin placement but
  no solid, face, edge, or tessellated geometry. Its generated CAD sidecar has
  zero mesh primitives. File existence and byte size were therefore a false
  positive, and this recipe is not verified.
- Root cause hypothesis: the probe combined
  `ExportFromOption.DisplayPart` with `InputFile`, allowing NX to translate a
  saved-file envelope instead of the live display-part solid.
- Patch made: the generic `CreateStepCreator` probe now uses DisplayPart export
  without assigning `InputFile`. `post-nx-review` now rejects metadata-only
  STEP files before sidecar inspection.
- Runtime evidence: body count 1; STEP path reported as
  `C:\apps\devop_tools\UDU\test11\models-main\nx2606\10_step_ap242.step`;
  reported size 2221 bytes.
- Compatibility conclusion: NX 2606 uses `CreateStepCreator`; the absent
  `CreateStep214Creator` remains a rejected recipe for this binding.
- Remaining validation: manually rerun the repaired probe 10, return the new
  report and STEP, then require deterministic inspection and snapshot review
  before promoting the recipe.

## 2026-07-15 - NX 2606 probe 10 stale STEP rerun evidence - NX 2606

- Runtime report: success, one body, and a reported 2149-byte STEP.
- Returned evidence: `models/S5.py`, containing the runtime JSON followed by
  the STEP payload.
- Artifact result: rejected. The STEP has the same 14:29:21 timestamp and the
  same metadata-only AP242 payload as the earlier returned artifact; it has no
  supported solid, face, edge, shell, or tessellated-solid representation.
- Root cause: probe work-part creation had become repeat-run-safe, but probe 10
  still exported to the fixed journal basename `10_step_ap242.step`. The old
  file satisfied the existence/size check even though the current run did not
  replace it with valid geometry.
- Patch made: probe 10 now derives the STEP path from the current work part's
  unique `FullPath`, so a rerun produces matching names such as
  `10_step_ap242_run_001.prt` and `10_step_ap242_run_001.step`.
- Recipe status remains experimental until the uniquely named returned STEP
  passes deterministic inspection and snapshot review.

## 2026-07-15 - NX 2606 probe 10 DisplayPart-only export - NX 2606

- User observation: NX successfully created and displayed the solid and saved
  `10_step_ap242_run_001.prt` and `_run_002.prt`, but no matching STEP file
  exists.
- Configuration: generic `CreateStepCreator`, AP242, DisplayPart,
  `ProcessHoldFlag=True`, and no `InputFile`.
- Result: rejected for NX 2606; native modeling/save succeeds but STEP output
  is absent.
- Next minimal test: restore `InputFile=work_part.FullPath` while retaining the
  unique per-run STEP name. Poll for up to 60 seconds and fail explicitly if
  the current run's STEP is absent. This isolates the original configuration
  without allowing an old fixed-name STEP to create another false positive.

## 2026-07-15 - NX 2606 probe 10 unique run 003 - NX 2606

- Returned evidence: `models/S5.py` contains the matching
  `10_step_ap242_run_003.step`, translator log, and structured runtime JSON.
- Runtime result: user-run NX created and displayed one body, saved the unique
  native PRT, and reported success with a 2273-byte STEP.
- Artifact result: rejected. The translator explicitly read
  `10_step_ap242_run_003.prt`, but its summary contains only 22 metadata
  entities. The STEP contains no solid, face, edge, shell, or tessellated-solid
  representation. This eliminates stale output and an unread `InputFile` as
  explanations.
- Official API review: Siemens `NXOpen.StepCreator` page `a07507.html` exposes
  `ObjectTypes`; `NXOpen.ObjectTypeSelector` page `a05707.html` documents
  writable boolean property `Solids`, which must be true when solids are
  desired in the output.
- Patch made: enable `creator.ObjectTypes.Solids = True` in the runtime probe,
  raw template, and wrapper exporter. The 004 probe keeps the remaining 003
  export configuration unchanged, so the solid filter is the only variable.
- Recipe status remains experimental until the user manually returns the 004
  JSON, STEP, and translator log and deterministic review confirms geometry.

## 2026-07-15 - NX 2606 probe 10 solids-filter rerun - NX 2606

- Returned evidence: the current `models/S5.py` contains a newly timestamped
  STEP payload (`2026-07-15T15:54:43+08:00`) and its structured runtime JSON.
- Runtime result: user-run NX reported success and one body; the native PRT
  exists and the STEP is 2221 bytes.
- Artifact result: rejected. Even with `ObjectTypes.Solids=True`, the AP242
  payload contains only product metadata and the origin placement. It contains
  no solid, face, edge, shell, or tessellated-solid geometry.
- Decision: reject and freeze this exact `CreateStepCreator` configuration.
  Per user direction, defer further STEP-export variants and continue the
  remaining roadmap work. Any future attempt must use a separately reviewed
  selection-block or export-mode recipe rather than another untracked tweak.

## 2026-07-17 - bearing support qualification run 002 STEP input failure - NX 2606

- Returned evidence: `YuanZS-12/models/aerospace_bearing_002` from a user-run
  NX UI session, source SHA256
  `80f4f0bcf35a5a1418a11d4f0e2c0d0bd43abfa688a1ab0b9c735e24542fb436`.
- Native result: `_cadnx_work/bearing_support_housing.prt` exists and is
  199345 bytes, so work-part creation, modeling, and native save reached the
  STEP stage.
- Translator result: no STEP was created; the log says
  `UG to STEP` followed by `No parts in current input file`.
- Failed configuration: generic `CreateStepCreator`, AP242,
  `ExportFrom=DisplayPart`, `ObjectTypes.Solids=True`, and no `InputFile`.
- Classification: STEP export failure, not a geometry failure. The run remains
  failed and cannot be promoted from `static_only`.
- Minimal repair: for a non-empty current-run saved PRT, use the separately
  reviewed `ExportFromOption.ExistingPart` and set `InputFile` to that PRT;
  retain AP242, solids selection, unique output paths, and no-overwrite rules.
- This is a materially different export-mode recipe. It remains experimental
  until a new manual NX UI run returns a STEP containing real geometry.

## 2026-07-17 - bearing support qualification run 004 real STEP, report path failure - NX 2606

- Returned evidence: `YuanZS-12/models/aerospace_bearing_004`, user-run NX UI,
  source SHA256
  `80f4f0bcf35a5a1418a11d4f0e2c0d0bd43abfa688a1ab0b9c735e24542fb436`.
- STEP result: 45229-byte AP242 file with real geometry. Translator evidence
  reports one input body, 41 `advanced_face`, 86 `edge_curve`, five
  `closed_shell`, and one `brep_with_voids`.
- Export configuration: generic `CreateStepCreator`, AP242,
  `ExportFrom=ExistingPart`, current-run saved PRT as `InputFile`, and
  `ObjectTypes.Solids=True`. This materially different configuration passed
  the geometry-content gate.
- Fixture result: failure after successful export. `NXBuilder.export_step()`
  resolved the placeholder `.step` to the correct absolute Journal-side path
  but returned no path; the fixture then called `getsize()` on its stale
  placeholder and wrote a failure report.
- Minimal repair: return the resolved path from `NXBuilder.export_step()`, have
  wrapper fixtures capture it, and calculate report artifact sizes from the
  actual files. Recipe/fixture promotion remains blocked until a new manual
  run returns a successful structured report linked to the real STEP.

## 2026-07-17 - bearing support frozen runs 005-006 passed - NX 2606

- Returned evidence: `YuanZS-12/models/aerospace_bearing_005` and
  `YuanZS-12/models/aerospace_bearing_006`, both executed by the user through
  the NX UI with consecutive `run_005` and `run_006` report IDs.
- Both reports passed with one body and all critical features true. The frozen
  Journal SHA256 is
  `d0e04f746814afde865ff00243a093152268e1e6ec41fd7554ebb56273ec4675`.
- Both STEP files contain 1,156 entities, 41 advanced faces, 86 edge curves,
  and one `brep_with_voids`. Independent CAD inspection returned identical
  topology, bounds, planes, areas, and positioning facts.
- The raw STEP hashes differ only because the `FILE_NAME.time_stamp` header
  value records each export time; a complete line diff found no other change.
  Native PRT hashes and sizes also vary between NX saves and remain recorded
  per evidence item rather than treated as cross-run source hashes.
- Independent post-NX report, geometry, snapshot, Journal, PRT, and STEP gates
  passed for runs 005-007. The durable evidence records under
  `models/nx_runtime_evidence/nx2606/bearing-support-housing/` passed
  `check-runtime-series` as three consecutive controlled NX runs. The fixture
  is promoted to `verified`; raw STEP hashes remain distinct because each NX
  export records its own `FILE_NAME.time_stamp`.

## 2026-07-15 - NX 2606 SweptBuilder1 probes 05-07 - NX 2606

- All results came from the user's manual Siemens NX execution; agent
  execution remained false.
- Probe 06 succeeded with one body using `SweptBuilder1`, two differently sized
  closed rectangular sections, and one straight guide connecting corresponding
  corners. The `nx2606.sweep.two-sections` recipe is promoted to verified for
  that exact configuration.
- Probes 05 and 07 both failed at `CommitFeature()` with `Unable to approximate
  guide string.` Both used one closed section, while their builder factory,
  solid-body option, section/guide objects, and guide intersection pattern were
  otherwise shared with probe 06.
- Repair: preserve each probe's orientation intent but adopt the two-section
  contract proven by 06. Probe 05 now uses identical root/tip rectangles;
  probe 07 uses a terminal rectangle rotated 20 degrees around its guide corner
  to match the linear angular-law endpoint.
- The repaired 05 and 07 configurations remain experimental pending new manual
  NX 2606 results.

## 2026-07-15 - NX 2606 repaired probes 05 and 07 - NX 2606

- Probe 05 succeeded in the user's manual NX run with one body, two identical
  sections, one straight guide, and Fixed orientation. Promote
  `nx2606.sweep.fixed-orientation` to verified for this exact configuration.
- Probe 07 progressed past guide approximation after adopting two sections but
  failed at commit with `Invalid orientation method specified.` The missing
  distinction from Fixed orientation is an explicit angular-law spine.
- Patch: populate the builder-owned `SweptBuilder1.Spine` section with the
  straight path and call `AngularLaw.SetSpineIntoBuilder(builder.Spine)` before
  selecting `ByAngularLaw`. This is grounded in Siemens pages `a47559.html` and
  `a56867.html` and awaits another manual NX 2606 result.

## 2026-07-16 - dc_mcp_server controlled execution integration - local

- Source contract: recorded the real parameter and Markdown return shapes for
  all seven `dc_mcp_server` tools.
- Runtime routing: uses `static_only`, `mcp_review`, and `manual_nx`. The user
  prepares NX and manually runs every Journal; the agent may not execute it.
- Evidence: runtime schema v2 accepts only `user:nx_ui` provenance while
  retaining legacy schema v1 manual reports.
- Safety: templates and probes allocate unique run IDs, create new work parts,
  refuse overwrite, require static checks, and cap repair attempts at three.
- Historical transport diagnostics: the parser is retained to audit old MCP
  attempts, but those results are not accepted as NX runtime evidence.

## 2026-07-16 - dc_run_journal boundary confirmed on NX 2606

- Probe 01 lookup calls completed and produced real API-review Markdown.
- `dc_run_journal` resolved `run_journal.exe`, timed out after 90 seconds, and
  produced no PRT or `.nxreport.json` despite the NX UI already being open.
- Decision: MCP is query-only. All runtime evidence must come from a manual
  user run in the NX UI; launcher timeout/license output is infrastructure
  evidence and does not consume a geometry repair attempt.

## 2026-07-16 - MCP-reviewed probe 01 manual NX UI run passed

- Review: real `dc_lookup_pattern` and `dc_get_api_info` calls confirmed
  `PartCollection.NewDisplay`, `Part.Units`, and `BasePart.Save` API facts.
- Execution: the user manually ran the `integration_003` workspace Journal in
  NX 2606; the Agent did not execute NX.
- Report: schema v2 `user:nx_ui`, `result=success`, body count `0`, expected
  body count `0`, and critical feature `work_part=true`.
- Artifact: unique `01_create_part_run_001.prt`, reported size 53,880 bytes.
- Follow-up: prepare probe 06 with fresh query-only review evidence and repeat
  the same manual NX UI flow.

## 2026-07-16 - Probe 06 geometry passed, stale provenance rejected

- The user manually ran an older workspace copy under
  `.agents\\nx_runtime_probes\\nx2606`, not the prepared `integration_003`
  Journal.
- NX 2606 committed the two-section `SweptBuilder1` solid successfully: body
  count `1`, expected `1`, critical feature true, two sections, and a reported
  77,226-byte PRT.
- The old Journal embedded `mode=mcp_execute`, listed `dc_run_snippet` in review
  evidence, and wrote `agent:dc_mcp` provenance even though the user ran it.
- Decision: retain this as geometry/compatibility evidence only. Reject it as
  schema v2 workflow evidence and rerun the unchanged geometry from a fresh
  `manual_nx` workspace copy with `user:nx_ui` provenance.
- Repair control: `check-mcp-repair-state` stops at three attempts or after two
  identical root causes without new API evidence.
- Local evidence: 86 nx-cad tests passed during implementation. No `dc_*` tools
  are exposed in the Mac development session, so NX-machine MCP execution and
  artifact gates remain pending.

## 2026-07-16 - MCP-reviewed probe 06 manual NX UI run passed

- Review: the prepared Journal records query-only `dc_lookup_pattern` and
  `dc_get_api_info` evidence for `CreateSweptBuilder1`, `SweptBuilder1`, its
  section/guide lists, solid body preference, fixed orientation, commit, and
  builder destruction. No MCP execution tool appears in the review.
- Execution: the user manually ran
  `.agents\\nx_mcp_runs\\integration_003\\06_sweep_two_sections.py` in the NX
  2606 UI; the Journal policy is `manual_nx` with `agent_execution=false`.
- Report: schema v2 `user:nx_ui`, `result=success`, body count `1`, expected
  body count `1`, critical feature
  `swept_builder1_two_section_tapered_solid=true`, and section count `2`.
- Artifact: unique `06_sweep_two_sections_run_001.prt`, reported size 77,252
  bytes. The PRT remains on the NX machine, so this record validates the
  returned report and reported artifact metadata, not local PRT inspection.
- Decision: accept this result as clean manual runtime provenance for
  `nx2606.sweep.two-sections`. Retain the prior stale-provenance entry as a
  historical rejection of that report format, not as a geometry failure.
- Follow-up: proceed to the two remaining advanced recipe gates: angular-law
  sweep and STEP creator, then the five aerospace regression fixtures.

## 2026-07-17 - Probe 07 rotated-section twist passed; ByAngularLaw rejected

- Execution: the user manually ran the final prepared Journal in the NX 2606
  UI. The schema v2 report records `user:nx_ui`, `result=success`, body count
  `1`, expected body count `1`, and critical feature
  `swept_builder1_two_section_twisted_solid=true`.
- Artifact: the report identifies unique
  `07_sweep_angular_law_run_006.prt` at 89,203 bytes. The PRT remains on the NX
  machine, so local binary geometry inspection was not performed.
- Modeling result: the successful Journal sets `by_angular_law=false`. It uses
  two rectangular sections, rotates the terminal section 20 degrees around the
  corresponding guide corner, and commits a `SweptBuilder1` solid.
- API result: the user-returned traceback and Copilot conversation report
  `Invalid orientation method specified` for tested `ByAngularLaw` variants
  using explicit Spine/`SetSpineIntoBuilder`, without that binding, without an
  explicit Spine, and with the deprecated `SweptBuilder`.
- Decision: mark `nx2606.sweep.angular-law` rejected for those tested NX 2606
  configurations. Add and verify the separate
  `nx2606.sweep.rotated-section-twist` fallback. Do not claim the successful
  body as angular-law runtime evidence.
- Workflow finding: the NX-machine Agent edited the installed canonical probe,
  deleted/replaced the existing `integration_003` workspace Journal, and
  reported four repair attempts. Those actions violate the no-overwrite,
  workspace-copy-only, and maximum-three-attempt policies. The repair guidance
  now states these boundaries explicitly.
- Completion impact: the strict roadmap still lacks a verified angular-law
  recipe; the verified fallback does not weaken or satisfy that gate.

## 2026-07-27 - Frame preparation strict-check false positive - local/NX machine

- The NX-machine Agent completed query-only API review and prepared the fresh
  `aerospace_frame_001` workspace without running NX.
- The canonical frame, report helper, and wrapper hashes matched the frozen
  Mac sources. The prepared Journal failed `check-journal --strict-geometry`
  before any NX execution.
- Root cause: MCP review evidence embedded the identifier
  `ScRuleFactory.CreateRuleCurveDumb`. The checker searched for the bare
  substring `curved`, so the `CurveDumb` identifier accidentally activated the
  smooth/freeform quality heuristic when the frame also used multiple wrapper
  primitives.
- Patch: smooth-geometry signals now use alphabetic word boundaries, retaining
  real `curved` model-name detection while excluding `CreateRuleCurveDumb`.
  A regression test covers an MCP-reviewed frame-like Journal.
- Validation: 98 nx-cad unit tests, the canonical frame strict check,
  `check-roadmap-implementation`, and `git diff --check` passed. The standalone
  fix was published at commit `ca4e829`.
- Classification: static-check infrastructure failure, not geometry or NX
  runtime failure. No Journal ran, so `_001` does not consume a manual repair
  attempt. Preserve `_001`; use a new `_002` workspace after correcting the
  review tool list and retaining raw query Markdown.

## 2026-07-27 - Frame run 003 radial borescope passage failed - NX 2606

- Execution: the user manually ran the frozen MCP-reviewed
  `aerospace_frame_003` Journal through the NX UI. The schema v2 report records
  `user:nx_ui`, `run_003`, matching source SHA256, and no PRT/STEP artifacts.
- Failure: the third `radial_boss_with_hole` boolean subtract, for the
  borescope boss at 270 degrees, raised the NX zero-wall/touch-condition
  exception. This is the first actual frame manual-run repair attempt.
- Root cause: the radial passage cutter used `casing_od` as its length. At the
  270-degree borescope position it continued beyond the local boss and casing
  wall along a primary strut, through the hub region, and toward the opposite
  frame wall. The preceding off-strut passage locations did not expose this
  overlong-cutter defect.
- Patch: derive `casing_wall = casing_or - casing_ir` and limit each radial
  passage to `boss_height + casing_wall + 2 * through_overcut`. The cutter now
  crosses only the boss and local casing wall, ending one overcut inside the
  casing cavity. API family and MCP-reviewed calls are unchanged.
- Validation: the repaired canonical frame passes strict geometry; 101 unit
  tests, `check-roadmap-implementation`, and `git diff --check` pass. A
  regression assertion forbids restoring `casing_od` as radial passage depth.
- Follow-up: publish the new canonical source, prepare a no-overwrite `_004`
  workspace using the existing query-only API review, and require another
  single user NX UI run.

## 2026-07-27 - Frame run 004 borescope/strut topology still failed - NX 2606

- Execution: the user manually ran the repaired, frozen
  `aerospace_frame_004` Journal in the NX UI. The schema v2 report records
  `user:nx_ui`, `run_004`, matching prepared-source SHA256, and no artifacts.
- Failure: NX raised the same zero-wall/touch-condition exception at the same
  borescope passage boolean subtract. This is the second actual frame
  manual-run attempt and the same failing feature as run 003.
- Finding: limiting cutter depth removed the unintended full-frame cut but did
  not resolve the local topology. At 270 degrees the passage is aligned with a
  primary strut, while `borescope_x=-12` places the 12 mm hole partly across
  the strut's axial edge instead of clearly inside or clear of it. That partial
  intersection remains a zero-wall/touch-condition candidate.
- Stop condition: do not continue tuning cutter overlap. The same root feature
  failed twice, and the next repair requires a deliberate borescope placement
  choice: move its axial station to center the passage within the strut, or
  move its angle into a clear bay between struts. Preserve `_003` and `_004`;
  await user selection before using the third and final repair run.
- User decision: retain the 270-degree circumferential location and change
  `borescope_x` from -12 mm to 0 mm. This centers the 12 mm passage within the
  primary strut's approximately -11 mm to +11 mm axial range instead of
  partially crossing its edge. Add a regression assertion for this placement
  and use it for the third and final repair workspace.

## 2026-07-27 - Frame run 005 passed borescope, failed accessory holes - NX 2606

- Execution: the user manually ran frozen `aerospace_frame_005` once through
  the NX UI. The schema v2 failure report records `user:nx_ui`, `run_005`, and
  matching prepared-source SHA256. No PRT or STEP was produced.
- Progress: the Journal passed the previously failing borescope passage,
  confirming that centering `borescope_x=0` resolved that local topology.
- New failure: the run stopped at the later accessory-pad mounting-hole
  `boolean_subtract`. Those four radial cutters still use `casing_od` as their
  length, repeating the full-diameter cutter pattern in a separate feature.
- Disposition: the current fixture has consumed three failed manual repair
  runs (`run_003`, `run_004`, `run_005`). Mark it `known_failure`, preserve all
  workspaces, and do not prepare `_006`. Any future frame work must be a
  materially redesigned fixture and a new qualification sequence, with all
  local radial passages audited before another NX run.

## 2026-07-27 - Linkage run 002 geometry passed, STEP was metadata-only - NX 2606

- Execution: the user manually ran the frozen, MCP-reviewed
  `aerospace_linkage_002` Journal through the NX UI. The schema v2 report
  records `user:nx_ui`, matching source SHA256, one expected body, all six
  critical linkage features true, and a 236,753-byte native PRT.
- Artifact failure: the 2,241-byte AP242 file contains product/context metadata
  only and no B-rep, face, edge, surface, or tessellated geometry entities.
  The qualification run therefore fails the STEP artifact gate despite
  successful NX modeling.
- Root cause candidate: the raw aerospace exporters used ExistingPart,
  InputFile, and `ObjectTypes.Solids=True`, but did not reproduce three settings
  present in the bearing-verified wrapper path: NativeFileSystem export
  destination, `.step` output extension, and `LayerMask="1-256"`. An empty or
  unsuitable layer mask is consistent with a metadata-only export.
- Patch: align linkage, duct, and blade raw exporters with the complete
  verified wrapper configuration by adding all three settings. Geometry and API
  families are unchanged. Prepare a fresh linkage workspace and require real
  STEP geometry inspection before accepting success.

## 2026-07-27 - Linkage runs 003-005 passed standalone qualification - NX 2606

- Execution: three consecutive, distinct workspaces were run exactly once by
  the user through the NX UI. All reports record `user:nx_ui`, body count 1,
  all six critical linkage features, and the same Journal SHA256
  `93e4aabaa6fdc4599df18b1a161c92acc2e7e4a64a37acac6b72eb2bd8f263a8`.
- Artifacts: every run returned a native PRT and a 41,161-byte AP242 STEP.
  Independent text inspection found `ADVANCED_BREP_SHAPE_REPRESENTATION`,
  `MANIFOLD_SOLID_BREP`, `CLOSED_SHELL`, B-spline surfaces, faces, and edges;
  the repaired exporter no longer emits the metadata-only payload from run 002.
- Final run: run 005 PRT SHA256 is
  `ce6cb981d6252d5b20f2651c1aed2710ffc6842dfd7815a7f42708624dddd14b`;
  STEP SHA256 is
  `29e32b8011d2ec39358aadb211157f45205cb7e0ebb4043dc129cab65804e74b`.
- Scope: snapshot and CAD Viewer review belong to the broader text-to-cad
  workbench and are not required by the standalone nx-cad skill. The linkage
  fixture has completed its standalone three-run qualification.

## 2026-07-29 - Duct run 002 rejected a two-loop ThroughCurves section - NX 2606

- Execution: the user ran the frozen MCP-reviewed Journal exactly once through
  the NX UI. The schema v2 report records `user:nx_ui`, `run_002`, source
  SHA256 `f6e894b4500fee9464063bcc50a3daf10746bb71f1f66f1c033fdaacf047645a`,
  and no PRT or STEP artifacts.
- Failure: `ThroughCurvesBuilder.CommitFeature()` raised `Gaps in string or
  multiple loops.` Each station Section contained both the outer and inner
  periodic spline, which NX 2606 does not accept as one solid loft string.
- Repair: create five single-loop outer sections and loft the outside solid;
  create five single-loop inner sections with positive angular through-overcut,
  loft the passage tool, then use the raw BooleanBuilder subtract path already
  verified by linkage runs 003-005.
- Classification: geometry/loft topology, first failed duct repair run. The
  original `_002` workspace remains immutable and must not be rerun.
