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
