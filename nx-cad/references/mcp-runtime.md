# Designcenter/NXOpen MCP Review + Manual NX Runtime

`dc_mcp_server` is a local stdio MCP server on the NX machine. In this
environment it is an authoritative API-review service, not the Siemens NX
runtime transport.

The user starts and prepares NX, Designcenter, VS Code Copilot, and the MCP
server. The Agent may call the five lookup tools. The Agent must not call
`dc_run_snippet` or `dc_run_journal`, launch or close NX, invoke
`run_journal.exe`/`ugraf.exe`, or claim that lookup output is NX runtime
evidence. The user runs every Journal manually from the NX UI and returns the
generated report and artifacts.

## Proven Runtime Boundary

The NX 2606 `integration_002` test established the boundary:

- the lookup tools were visible and returned real Designcenter/API results;
- `dc_run_journal` resolved a separate `run_journal.exe` process;
- that process did not use the already-open NX UI, timed out after 90 seconds,
  and produced no PRT or `.nxreport.json`;
- therefore Agent execution is unsupported even when NX is already open.

Do not classify this infrastructure timeout as a Journal geometry failure and
do not spend a repair attempt changing the Journal.

## Runtime Modes

| Mode | MCP lookup | NX execution | Evidence |
| --- | --- | --- | --- |
| `static_only` | unavailable | optional manual user run | user-returned NX artifacts only |
| `mcp_review` | five lookup tools | not yet run | API review only |
| `manual_nx` | reviewed | user runs Journal in NX UI | `user:nx_ui` report and artifacts |

Generation mode remains independent: wrapper or raw NXOpen can both move from
review to a manual NX run.

## Seven-Tool Contract

All seven tools return Markdown. Only the first five are callable in this
workflow.

### `dc_lookup_pattern`

```text
query: string, required
limit: integer, optional, default 3, maximum 5
```

Use first for Designcenter Journal patterns, pitfalls, and `ugcolor.cdf`
facts. Treat returned code as a candidate and confirm signatures separately.
Never adopt a pattern that deletes an existing output file; nx-cad requires a
new run ID instead of overwrite/delete.

### `dc_search`

```text
query: string, required
search_type: classes | methods | all, optional, default all
limit: integer, optional, default 15
category: string, optional
class_filter: string, optional
return_type_filter: string, optional
```

Use when a likely class, method, or enum name is known.

### `dc_semantic_search`

```text
query: string, required
limit: integer, optional, default 15
use_vector_embeddings: boolean, optional, default true
```

Use when modeling intent is known but the NXOpen name is not.

### `dc_get_api_info`

```text
info_type: class | method, optional, default class
class_name: string, required
method_name: string, required when info_type=method
method_filter: string prefix, optional
property_filter: string prefix, optional
```

Use before writing or repairing raw NXOpen classes, methods, properties,
builders, creators, and nested enums.

### `dc_list_namespace`

```text
namespace: string, optional
limit: integer, optional, default 50
include_submodules: boolean, optional, default false
category: string, optional
```

Use only when search results are too broad.

### `dc_run_snippet` — unavailable for this workflow

```text
code: string, required
mode: auto_wrap | raw, optional, default auto_wrap
timeout: integer seconds, optional, default 90
```

Do not call it. It relies on the execution backend rather than the user's
already-open NX UI and cannot provide accepted runtime evidence here.

### `dc_run_journal` — unavailable for this workflow

```text
journal_path: absolute .py/.vb/.cs path, required
args: string array, optional
managed_mode: boolean, optional, default false
timeout: integer seconds, optional, default 300
working_dir: string, optional
```

Do not call it. It resolves `run_journal.exe`, starts a separate process, and
does not execute inside the user-prepared NX UI. A timeout, license diagnostic,
or absence of artifacts is infrastructure evidence, not a model repair signal.

## API Review Protocol

1. Inspect the versioned API recipe registry.
2. Call `dc_lookup_pattern` for known Journal operations and pitfalls.
3. Use `dc_semantic_search` when the API name is unknown, or `dc_search` when
   known.
4. Use `dc_list_namespace` only if results remain broad.
5. Call `dc_get_api_info` for every exact raw builder, creator, method,
   property, and nested enum written or changed.
6. Preserve the raw Markdown results.
7. Record only calls that actually completed and facts actually returned in
   `MCP_API_REVIEW`.

Preservation means one immutable UTF-8 Markdown file per completed lookup call,
not a prose summary or a pointer to an ephemeral editor cache. Store a manifest
with the call sequence, exact tool name, complete input arguments, Markdown
path, Markdown SHA256, and original cache path when one exists. The distinct
manifest tool set must exactly equal `MCP_API_REVIEW["tools"]`, and the number
of manifest entries must equal the number of archived Markdown files. Reused
facts require links to their original archived calls; a `[reuse]` summary by
itself is not review evidence.

Validate a completed archive without connecting to MCP or NX:

```text
py -3 scripts\check-mcp-review-evidence \
  <workspace>\api-review-raw\api-review-manifest.json \
  --review-evidence <frame-review-v3.json>
```

The checker accepts either a top-level call list or an object with a `calls`
list. Each entry requires `sequence`, `tool`, `exact_input`,
`raw_markdown_file`, and `raw_markdown_sha256`; `original_cache_path` remains
recommended provenance metadata.

If lookup tools are absent, switch to `static_only`. Never manufacture review
JSON from source code, local references, memory, or simulated results. Never
list `dc_run_snippet` or `dc_run_journal` in API review evidence.

Designcenter patterns can conflict with nx-cad policy. For example, a pattern
may recommend deleting an existing PRT before `NewDisplay`; nx-cad instead
allocates `run_001`, `run_002`, and so on and never deletes prior evidence.

## Manual-Run Journal Policy

An MCP-reviewed Journal prepared for the user should contain:

```python
EXECUTION_POLICY = {
    "mode": "manual_nx",
    "manual_user_run_required": True,
    "agent_execution": False,
    "requires_prepared_nx_environment": True,
    "allow_launch_or_close_nx": False,
    "allow_existing_work_part": False,
    "allow_overwrite": False,
    "managed_mode": False,
    "max_repair_attempts": 3,
}
```

Prepare a workspace copy, never the canonical skill asset:

```text
py -3 skills\nx-cad\scripts\prepare-dc-mcp-journal \
  <canonical-probe> <workspace-copy> \
  --review-evidence <review.json> --manual-user-run
```

The filename is retained for compatibility: it injects MCP review evidence but
does not execute MCP. It supports Python 3.7 and refuses overwrites. For an
aerospace Wrapper probe it also copies the sibling `cadnx/` package and report
support module into the fresh workspace; Raw probes receive only the sibling
support modules they actually import.

Before giving the file to the user:

```text
py -3 skills\nx-cad\scripts\check-journal <workspace-copy> --strict-geometry
```

## Manual NX Execution Handoff

1. Agent completes API review, Journal preparation, and static checks.
2. Agent reports the exact workspace Journal path and expected body/artifacts.
3. User opens/prepares NX and manually runs that Journal from the NX UI.
4. User returns console output, traceback if any, `.nxreport.json`, PRT, STEP
   when requested, and the exact Journal used.
5. Agent validates the report with `check-runtime-report`.
6. Agent independently validates the returned report and STEP geometry evidence.
7. If the Journal failed, Agent performs the smallest evidence-backed repair,
   creates a new workspace copy/run ID, and asks the user to run it again.

Accepted schema v2 provenance is:

```json
{
  "execution": {
    "actor": "user",
    "transport": "nx_ui",
    "tool": "nx_ui"
  }
}
```

Schema v1 remains accepted only with `manual_user_run=true` and
`agent_execution=false`. Reports claiming `agent:dc_mcp` are rejected.

## Bounded Manual Repair Loop

Each repair attempt requires a separate user run:

1. preserve the full traceback, report, artifacts, Journal, and run ID;
2. classify API signature, builder configuration, geometry, boolean,
   selection, save, export, or infrastructure failure;
3. do not patch geometry for `run_journal.exe` timeout/license failures;
4. query only the missing API evidence;
5. patch the smallest responsible code section;
6. rerun static checks;
7. hand a new no-overwrite Journal/run ID to the user;
8. stop after three failed user runs or two identical root causes without new
   API evidence.

Repairs must modify only a fresh workspace copy. Do not edit the canonical
probe under the installed skill on the NX machine, and do not delete or replace
an earlier workspace Journal to make room for a repair. A successful fallback
that changes API family or modeling strategy must be recorded as a separate
recipe; it does not promote the originally requested API recipe.

## Final Report Contract

Report separately:

- lookup tools actually called and raw review Markdown;
- generated/prepared Journal and static-check result;
- explicit statement that the Agent did not run NX;
- user-run console/traceback and report path;
- body, critical-feature, PRT, and STEP gates actually checked;
- repair count and next manual action.

Never imply that MCP lookup, a static check, or a `run_journal.exe` attempt is
successful NX execution.
