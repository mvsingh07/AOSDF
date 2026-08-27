# aosdf-mcp

An MCP server exposing exactly six read/write tools over an AOSDF project's own markdown
files. See `framework.md`'s `[v2.5, E2-T1] aosdf-mcp Server` section for the full design
rationale (Principle 26, OD-3). This file is the quick-start.

## Run it

```bash
AOSDF_DOCS_ROOT=/path/to/{project_name}-Documents/docs node src/index.js
```

Speaks MCP's stdio transport (newline-delimited JSON-RPC 2.0) on stdin/stdout. Point any
MCP-capable client (Claude Code, an editor extension) at this command.

No `npm install` needed — zero runtime dependencies by design (see framework.md).

## Configuration

| Env var | Default | Purpose |
| --- | --- | --- |
| `AOSDF_DOCS_ROOT` | *(required)* | Path to `{project_name}-Documents/docs/` |
| `AOSDF_PROJECT_STATUS_PATH` | `$ROOT/project_status.md` | Override for `aosdf_read_status` |
| `AOSDF_EXECUTION_PLAN_PATH` | `$ROOT/documents/06_Execution_Plan/execution_plan.md` | Override for `aosdf_next_planned_task` / `aosdf_update_task_status` |
| `AOSDF_IDENTIFIED_GAPS_PATH` | `$ROOT/identified_gaps.md` | Override for `aosdf_log_gap` |
| `AOSDF_MANUAL_ACTIONS_PATH` | `$ROOT/documents/12_Manual_Actions/actions.md` | Override for `aosdf_log_manual_action` — use this for a project that documents a single-file deviation (e.g. a `manual_actions.md` at the docs root) |
| `AOSDF_MODULE_INDEX_PATH` | `$ROOT/documents/03_System_Design/README.md` | Override for `aosdf_read_module_index` |

## The six tools

See `framework.md`'s `aosdf-mcp Server` section for the full table. Short version:
`aosdf_read_status`, `aosdf_next_planned_task`, `aosdf_update_task_status`, `aosdf_log_gap`,
`aosdf_log_manual_action`, `aosdf_read_module_index` — nothing else, per SR-4.

## Test

```bash
npm test
```

Runs `node --test` over `test/`, using disposable copies of the fixtures in
`test/fixtures/` (never the real project docs) so no test run has side effects.

## Source layout

```
src/
  index.js             ← stdio JSON-RPC loop, tool registry, dispatch
  config.js             ← AOSDF_DOCS_ROOT + per-file path overrides
  fileio.js              ← read/write that preserves the file's trailing-newline convention
  markdown-table.js       ← Document Formatting Standard-safe table parse/render
  next-id.js              ← GAP-NNN / MA-N sequential ID generation
  tools/*.js               ← one file per tool, each exporting { schema, run(args, paths) }
```
