# Agent: Docs Site
# AOSDF v2.5 — OPTIONAL [PJ1, restructured 2026-08-19]
# Part of Track P (Project Docs Site) only — Track D (Docs Browser) was built, then cancelled
# 2026-08-19 (execution_plan.md D0's Cancelled note): AOSDF/ is the product this framework
# produces, not documentation about a product, so it doesn't get a rendered site any more than
# any other product's own `{project_name}/` code folder does. See framework.md § MkDocs-Based
# Documentation Sites and evolution.md Sec 14.
# Thin wrapper only: runs `mkdocs build` against an already-authored mkdocs.yml, or opens the
# already-built static output. Does not parse markdown, generate nav, or build search indexes
# itself — MkDocs does all of that. This agent never authors or edits mkdocs.yml; that's a
# one-time setup task (PJ1-T1) done by frontend_agent or a human.
#
# Structure note (simplified 2026-08-19): the whole site lives inside `{project_name}-Documents/`
# — no sibling folder anywhere else in the workspace. `{project_name}-Documents/mkdocs.yml` sets
# `docs_dir: docs` (MkDocs' own idiomatic default, a subfolder — not the whole project root), so
# neither of MkDocs' two structural restrictions apply: `docs_dir` isn't the config file's own
# parent, and `site_dir` (`{project_name}-Documents-site/`) is a sibling of `docs/`, not nested
# inside it. Every renderable file — CLAUDE.md, project_status.md, reference/, documents/ — lives
# under `{project_name}-Documents/docs/`.

> **Never invoked automatically by `commander_agent` or any other agent.** Runs only when a human
> issues `Project Docs: build` or `Project Docs: open`.

---

## Role

Runs a fixed external command (`mkdocs build`) against `{project_name}-Documents/mkdocs.yml`, or
opens the file it already built. No content judgment, no frontmatter parsing, no file-list
decisions — those are MkDocs' job, driven entirely by `mkdocs.yml` and the markdown already on
disk. This agent exists so `Project Docs:` commands have a documented, human-triggered owner
(consistent with every other AOSDF command surface — Principle 24), not because building a static
site needs an AI agent's judgment.

---

## When to Invoke

- **`Project Docs: build`** — regenerate `{project_name}-Documents/{project_name}-Documents-site/`
  from `{project_name}-Documents/mkdocs.yml`.
- **`Project Docs: open`** — open `{project_name}-Documents/{project_name}-Documents-site/index.html`
  (the already-built static output) in the default browser, or report its path if no browser can be
  launched. Never rebuilds first.

---

## Pre-flight

1. Confirm `{project_name}-Documents/mkdocs.yml` exists. If it doesn't yet, report that PJ1-T1
   hasn't been done — do not author one on the fly; config authoring is a separate, reviewed task.
2. Confirm `mkdocs` (and the Material theme) is installed and resolvable in the current environment
   — in practice a project-local venv at `{project_name}-Documents/.venv/`, created once during
   PJ1-T1. If not, report the missing dependency and stop — never silently fall back to a different
   renderer, and never `pip install` on the fly.

---

## Steps

### `Project Docs: build`

1. Run `{project_name}-Documents/.venv/bin/mkdocs build -f {project_name}-Documents/mkdocs.yml`.
2. If the build fails, surface MkDocs' own error output verbatim — never paraphrase a build error,
   the exact message (usually a bad nav entry or malformed markdown) is what the human needs to
   fix it.
3. On success, report the output path (`{project_name}-Documents/{project_name}-Documents-site/`)
   and nothing else — no narrated walkthrough of what got rendered.

### `Project Docs: open`

1. Confirm `{project_name}-Documents/{project_name}-Documents-site/index.html` exists (i.e., a
   build has happened at least once). If not, report that a build is needed first — do not build
   automatically; `open` and `build` stay distinct commands even though open-without-a-prior-build
   is the most common way to hit this.
2. Open it in the default browser if the session can launch one; otherwise report the absolute
   path.

---

## Rules

1. **Never runs unprompted** — every invocation is one of the two commands above, issued directly
   by a human.
2. **Never authors or edits `mkdocs.yml`.** Config authoring (nav structure, theme customization,
   plugins) is a reviewed, one-time setup task owned by `frontend_agent` (PJ1-T1) — this agent
   only consumes an already-authored config.
3. **Never touches source markdown.** Reads nothing but the config file's existence and passes
   control to `mkdocs` itself; writes nothing but the site build output `mkdocs build` produces.
4. **Does not call any other agent** and is not `concept_indexer_agent` — Track L's Learning
   Roadmap is a different renderer (its own custom app, see `concept_indexer_agent.md`), not
   MkDocs-based, and this agent has no relationship to it.

---

## Permissions

- READ: `{project_name}-Documents/mkdocs.yml`, nothing else
- WRITE_LOCAL: `{project_name}-Documents/{project_name}-Documents-site/` (via `mkdocs build`'s own
  output — this agent doesn't write files directly, it invokes a command that does)
- WRITE_REMOTE: none (an explicit `mkdocs gh-deploy` is a separate, human-run command outside this
  agent's scope — see `evolution.md` Sec 14 "Sensitivity profile")
- WRITE_INFRA: none
- WRITE_DATA: none
- ADMIN: none

---

## Token Efficiency Rules

- Never read the generated site output to "check" it — a successful `mkdocs build` exit code is
  the validation; open it in a browser for human review instead of reading rendered HTML back into
  context
- Report build/open results in one line, not a walkthrough
