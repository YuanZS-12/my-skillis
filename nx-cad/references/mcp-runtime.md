# Designcenter/NXOpen MCP Runtime

Read this before using `dc_mcp_server`. The server is a local stdio MCP server
on the NX machine. It exposes Designcenter/NXOpen lookup and execution tools to
the coding agent; it is not a standalone GUI.

The user prepares NX, Designcenter, VS Code Copilot, and the MCP server. The
agent may query APIs and, only after an explicit request to execute, run a
snippet or Journal through MCP. The agent must not launch or close NX through
shell, batch files, GUI automation, COM, or any other mechanism.

## Runtime Modes

| Mode | Lookup tools | `dc_run_snippet` | `dc_run_journal` |
| --- | --- | --- | --- |
| `static_only` | unavailable | forbidden | forbidden |
| `mcp_review` | allowed | only when separately authorized for a minimal probe | forbidden |
| `mcp_execute` | allowed | bounded minimal probe | allowed after static checks |

Select the mode before coding:

1. Discover which `dc_*` tools are exposed.
2. Use `static_only` when lookup tools are absent and say so immediately.
3. Use `mcp_review` when lookup tools are present but the user did not request
   execution.
4. Use `mcp_execute` only when `dc_run_journal` is present, the user explicitly
   requested execution/automatic testing/repair, and the NX environment is
   prepared.
5. Downgrade to `mcp_review` immediately if execution authorization is
   withdrawn.

Generation mode is independent from runtime mode. Wrapper and raw NXOpen
journals can both use `mcp_execute` when their runtime requirements are met.

## Seven-Tool Contract

All seven tools return Markdown, not structured JSON. Use only the documented
parameters.

### `dc_lookup_pattern`

Use first for known Designcenter Journal practices, pitfalls, color facts, or
the authoritative `ugcolor.cdf` palette.

```text
query: string, required
limit: integer, optional, default 3, maximum 5
```

Returns matching titles, scores, Solution text, and Python examples. Treat an
example as a candidate pattern; confirm exact API shape separately.

### `dc_search`

Use when a likely class, method, or enum name is known.

```text
query: string, required
search_type: classes | methods | all, optional, default all
limit: integer, optional, default 15
category: string, optional
class_filter: string, optional
return_type_filter: string, optional
```

Returns class and method matches with full names, modules, signatures,
categories, descriptions, and usage.

### `dc_semantic_search`

Use when modeling intent is known but the API name is not.

```text
query: string, required
limit: integer, optional, default 15
use_vector_embeddings: boolean, optional, default true
```

Returns relevant classes with full names, relevance scores, descriptions, and
usage. It falls back to keyword matching when embeddings are unavailable.

### `dc_get_api_info`

Use before writing or revising raw NXOpen classes, methods, properties,
builders, creators, or nested enums.

```text
info_type: class | method, optional, default class
class_name: string, required; use the full class name
method_name: string, required when info_type=method
method_filter: string prefix, optional
property_filter: string prefix, optional
```

Returns inheritance, properties, methods, signatures, descriptions, nested
types, and enum members.

### `dc_list_namespace`

Use only when exact/semantic results are too broad and browsing an API family
will narrow the choice.

```text
namespace: string, optional; omitted means namespace overview
limit: integer, optional, default 50
include_submodules: boolean, optional, default false
category: string, optional
```

Returns namespace counts or classes grouped by category.

### `dc_run_snippet`

Use only when lookup cannot prove a small runtime behavior.

```text
code: string, required
mode: auto_wrap | raw, optional, default auto_wrap
timeout: integer seconds, optional, default 90
```

`auto_wrap` binds `theSession` and `workPart`; it is stateful and can modify the
current part. Prefer a read-only query or a self-contained scratch-part probe.
Do not split a full model into a long snippet to bypass the Journal gate.

Returns exit code, duration, stdout, and stderr as Markdown. Exit code 0 proves
only that the snippet process completed.

### `dc_run_journal`

Use only in `mcp_execute` for a complete, on-disk Journal that has passed
static checks.

```text
journal_path: absolute .py/.vb/.cs path, required
args: string array, optional
managed_mode: boolean, optional, default false
timeout: integer seconds, optional, default 300
working_dir: string, optional, default Journal directory
```

Returns Journal path, exit code, duration, working directory, output files,
stdout, and stderr as Markdown. Exit code 0 is transport evidence, not geometry
success.

For the first implementation:

- require `managed_mode=false` unless the user explicitly authorizes a
  Teamcenter workflow;
- keep Journal and working directory inside the approved model workspace;
- require a unique run ID and `allow_overwrite=false`;
- require static checks before every execution or repaired re-execution;
- use at most three repair attempts;
- never embed a `dc_run_journal` call in the generated Journal.

## API Research Flow

Do not call all lookup tools mechanically.

1. Check the versioned API recipe registry first.
2. Use `dc_lookup_pattern` for a known Journal operation or pitfall.
3. Use `dc_semantic_search` when the API name is unknown, or `dc_search` when
   it is known.
4. Use `dc_list_namespace` only if search remains too broad.
5. Use `dc_get_api_info` for the exact classes, methods, properties, creators,
   builders, and nested enums written into the Journal.
6. Record only tools actually called and facts actually learned in
   `MCP_API_REVIEW`.
7. If lookup proves API existence but not a complete builder configuration,
   run a minimal probe before using it in the full model.

Minimum evidence for a new raw NXOpen API family is one discovery call plus
the applicable `dc_get_api_info` calls. Search evidence never proves that a
Section + Guide + Orientation + Law + Solid combination can commit.

If the agent cannot see the `dc_*` tools, stop the MCP preparation flow and
report `static_only`. Do not manufacture a review JSON from probe source,
reference documents, memory, or simulated lookup results. The `tools` list
must contain only calls that actually completed in the current task; for
example, never list `dc_run_snippet` when no snippet result exists.

## Execution Policy

An executable generated Journal should contain a literal policy:

```python
EXECUTION_POLICY = {
    "mode": "mcp_execute",
    "user_authorized": True,
    "requires_prepared_nx_environment": True,
    "allow_launch_or_close_nx": False,
    "allow_existing_work_part": False,
    "allow_overwrite": False,
    "managed_mode": False,
    "max_repair_attempts": 3,
}
```

This marker supports static auditing; it does not create authorization. The
Agent must still infer execution permission from the current user request.

Do not call `dc_run_journal` when:

- the user requested only generation, explanation, or review;
- the tool is absent;
- static checks failed;
- the path is outside the approved workspace;
- output would overwrite an existing artifact;
- the target is an existing production part without explicit authorization;
- managed mode is required but was not explicitly authorized;
- three repair attempts are exhausted;
- the same root cause has occurred twice with no new API evidence.

## Controlled Execution Flow

1. Create the CAD-NX design ledger and expected body/feature/artifact targets.
2. Complete API research and generate the Journal.
3. Assign a unique `run_001`, `run_002`, ... context.
4. Run `check-journal`; add `--strict-geometry` when applicable.
5. If the API recipe is experimental, run the smallest probe first.
6. Call `dc_run_journal` with absolute path, approved working directory,
   `managed_mode=false`, and a bounded timeout.
7. Preserve the raw Markdown response.
8. Parse it with `scripts/parse-dc-mcp-result` when a saved response is
   available. Require a listed `.nxreport.json` for full Journal acceptance.
9. Validate the report with `scripts/check-runtime-report`.
10. Independently validate the actual STEP when requested. Reject missing,
    empty, and metadata-only files.
11. Inspect body count and critical features. Perform snapshot/visual review
    for complex aerospace geometry.
12. Report success only when all required gates pass.

Before a repaired rerun, save parsed results and enforce the stop conditions:

```bash
skills/nx-cad/scripts/check-mcp-repair-state \
  run-001.dc-result.json run-002.dc-result.json
```

The command rejects a fourth attempt and rejects two identical root causes
unless `--new-api-evidence` truthfully records that the repair direction is
based on new API evidence.

Example parser use:

```bash
skills/nx-cad/scripts/parse-dc-mcp-result journal dc-result.md \
  --require-runtime-report --output dc-result.json
```

The parser preserves raw Markdown. Its `execution_status=completed` means only
that the MCP-reported process completed without a detected critical stderr; it
does not validate geometry.

## Runtime Evidence

Use runtime report schema v2 for MCP execution:

```json
{
  "schema_version": 2,
  "result": "success",
  "execution": {
    "actor": "agent",
    "transport": "dc_mcp",
    "tool": "dc_run_journal",
    "user_authorized": true
  },
  "model": {
    "body_count": 1,
    "expected_body_count": 1,
    "critical_features": {"main_solid": true}
  }
}
```

Schema v1 manual reports remain valid. Schema v2 also accepts a user-run report
with `actor=user` and `transport=nx_ui`.

Full-model success requires:

- MCP exit code 0 or a successful user execution;
- no traceback/NXException/critical failure in stderr;
- report `result=success`;
- expected body count;
- all reported critical features true;
- non-empty PRT when required;
- non-empty, independently inspected non-metadata STEP when requested;
- snapshot/visual review before complex aerospace regression promotion.

## Bounded Repair Loop

On failure:

1. Preserve full stdout, stderr, runtime report, Journal path, and run ID.
2. Classify path, API signature, builder configuration, geometry intent,
   boolean, selection, save, or export failure.
3. Query only the missing API evidence.
4. Patch the smallest responsible code section.
5. Run static checks again.
6. Use a new run ID and re-execute only in authorized `mcp_execute`.
7. Stop after three attempts or two identical root causes without new API
   evidence.

Stop immediately for a requested geometry change, production-part mutation,
overwrite, managed-mode expansion, infrastructure failure, or a visual/
engineering decision requiring the user.

## Final Evidence Report

When MCP was used, report:

- runtime mode;
- exact `dc_*` tools called and their relevant facts;
- whether a snippet or full Journal executed;
- Journal path, working directory, timeout, and run ID;
- MCP exit code and preserved stderr/traceback;
- runtime report validation;
- PRT/STEP/snapshot checks actually performed;
- repair attempt count and remaining risks.

Never imply MCP, NX execution, artifact creation, or geometry validation unless
the corresponding call or check actually occurred.

## Integration Prompts

Review only:

```text
Use nx-cad and dc_mcp_server in raw NXOpen high-fidelity mode. Query patterns
and exact API signatures before coding. This task authorizes mcp_review only;
do not call dc_run_snippet or dc_run_journal.
```

Controlled execution:

```text
Use nx-cad and dc_mcp_server for this NX 2606 part. The NX/Designcenter
environment is prepared. You may call dc_run_snippet for a minimal probe and
dc_run_journal after static checks. Do not launch or close NX, reuse an existing
work part, or overwrite artifacts. Use unique run IDs and at most three repair
attempts, then validate body count, critical features, PRT, STEP, and report.
```

For the first NX-machine integration, sync and follow
`assets/runtime-probes/dc-mcp-integration-manifest.json`. It deliberately starts
with verified probes 01 and 06 and defers unstable probes 07 and 10. Modify only
the workspace probe copy. Prefer the deterministic preparation command recorded
in the manifest; it refuses canonical-skill outputs and existing files, replaces
the review marker with supplied real evidence, and sets the authorized policy.
Then rerun `check-journal` before calling MCP.

The bundled preparation and checking entry points support the Python 3.7
launcher commonly available on NX machines. Invoke them with `py -3` or
`python`. Do not patch the installed canonical skill to work around a local
failure; preserve the error and update the maintained source instead.
