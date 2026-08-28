---
description: Answer a structured research question before updating architecture/product/security docs (research_and_refine_agent).
argument-hint: <path to your task.md>
---

Call the `research-and-refine-agent` subagent.

task.md: $ARGUMENTS
project_root_path: (this project's `{project_name}-Documents/` root)

If `$ARGUMENTS` is empty, stop and ask the human to write a `task.md` first — see
`AOSDF/manual.md` § "How to Call the Research & Refine Agent" for its exact required format
(Objective, Research Scope, Documents Likely Affected, Decision Required, Constraints).

The agent will:
1. Read task.md — extract objective, scope, context docs, constraints
2. Read CLAUDE.md + only the listed context documents
3. Research the named options against the project's constraints
4. Write findings + a recommendation to `research_results.md`

It will NOT modify any existing document, create ADRs, or update the execution plan — that's the
human's decision after reviewing the output.
