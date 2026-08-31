# AOSDF for VSCode

Editor integration (`E4-T1`/`E4-T2`/`E5-T1`, `aosdf_expansion_scope.md` § 4.1 Pillar A). A thin
shell over `aosdf-mcp` (`E2-T1`), direct uncached reads of `identified_gaps.md` /
`manual_actions.md` / `implementation_prompts/README.md`, and a terminal — it holds no state of
its own (Principle 26) and never writes an AOSDF file directly.

## What it does

**Read-only (`E4`):**
- **Status bar chip** — current project state (`aosdf_read_status`) and the next `Planned` task
  (`aosdf_next_planned_task`). Click it to open `project_status.md`.
- **Inbox view** (Activity Bar → AOSDF) — three sections: every open (non-`Done`/`Resolved`/
  `Cancelled`) row from `identified_gaps.md` and `manual_actions.md`, plus every row in
  `implementation_prompts/README.md`'s Log not yet `Executed`. Click a row to jump to it.
- **`AOSDF: Open Project Docs`** command — thin wrapper opening Track P's built site
  (`docs_site_agent.md`'s `Project Docs: build` output).

**Write actions (`E5-T1`):** all three route through a named integrated terminal ("AOSDF"), never
a direct file write from the extension — whatever actually changes on disk happens inside the
Claude Code session running in that terminal, through its own agents' normal Permissions, exactly
as if you'd typed the same text yourself.
- **`AOSDF: Run Agent Command...`** — QuickPick over the 7 slash commands `.claude/commands/`
  (`E3-T1`) wires, prompting for an argument where one's needed (`/aosdf-addendum`,
  `/aosdf-research`, `/aosdf-import`), then sends the text into the terminal.
- **`AOSDF: Trigger Tracker Sync`** — shortcut that sends `/aosdf-sync` directly.
- **`AOSDF: Approve & Send`** (inline button on a pending-prompt row) — opens the prompt file for
  review, then sends the literal text `Approve to execute` into the terminal.

Refreshes automatically when `project_status.md`, `identified_gaps.md`, `manual_actions.md`, or
`implementation_prompts/README.md` change, or on demand via `AOSDF: Refresh Status`.

**Multi-workspace (`E6-T2`):** with more than one folder open in the same VS Code window (a
multi-root workspace), each folder can point at a different `{project_name}-Documents/docs` via
its own resource-scoped `aosdf.*` settings. The status bar chip shows whichever folder currently
has focus (prefixed `[folderName]`), the Inbox lists every folder's rows in one list (also
`[folderName]`-prefixed), and every write action gets its own per-folder terminal (`AOSDF:
<folderName>`), prompting with a QuickPick to pick the target folder first. With exactly one
folder open (the common case), none of this changes anything — no prefix, one plain `AOSDF`
terminal, no folder prompt.

## Setup

Requires this project's IDE tooling to be adopted (`workflow_initiator` Step 1 Q9 = yes). Unlike
`.claude/`/`.mcp.json`, this extension itself is **not** copied into `{project_name}/` — see
Distribution below. `workflow_initiator` Step 8 writes `{project_name}/.vscode/settings.json` for
you; the three settings it sets are:

| Setting | Default | Points at |
| --- | --- | --- |
| `aosdf.documentsRoot` | `../{project_name}-Documents/docs` | This product's docs root |
| `aosdf.mcpServerPath` | `../AOSDF/aosdf-mcp/src/index.js` | The same server registered in `.mcp.json` |
| `aosdf.projectDocsSitePath` | `../{project_name}-Documents/{project_name}-Documents-site/index.html` | Track P's built site |

All three defaults use the literal placeholder `{project_name}` and must be pointed at the real
folder name (Step 8 does this substitution automatically). All three are resource-scoped, so a
multi-root workspace can set different values per folder (VS Code Settings UI → Workspace tab →
pick the folder).

## Distribution

**Internal-only (`OD-1`, resolved 2026-08-29) — never published to the VS Code Marketplace.**
Two ways to run it:

- **From source** (no build step): open this folder in VS Code and press F5 to launch an
  Extension Development Host, then open `{project_name}/` inside that host window — its
  `.vscode/settings.json` takes effect automatically.
- **As a `.vsix`** (`E6-T3`): run `npm run package` in this folder (wraps `@vscode/vsce package`,
  fetched on demand via `npx` — never installed as a project dependency, consistent with the
  zero-runtime-dependency discipline this extension otherwise holds to). Produces
  `aosdf-vscode.vsix` (gitignored — a regenerable build artifact, not source), installable via
  VS Code's "Install from VSIX..." command on any machine, with no Marketplace account or
  publish step involved. `--allow-missing-repository` is passed because this package isn't a
  standalone repo (`OD-3`: bundled inside `AOSDF/`).
