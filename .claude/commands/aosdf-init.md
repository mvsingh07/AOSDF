---
description: Set up a new AOSDF project or resume one after a gap (workflow_initiator).
argument-hint: [project context — name, root, description, has_ui, cloud provider, team size, strategy, compliance, stack]
---

Call the `workflow-initiator` subagent with the following project context:

$ARGUMENTS

Please:
1. Scan the project root for existing files
2. Identify missing required documents
3. Create CLAUDE.md if missing
4. Create project_status.md
5. Create identified_gaps.md and manual_action.md
6. Report what is ready and what needs human input before execution can begin

If `$ARGUMENTS` is empty, ask for the project context first (project name, project root, one-line description, has UI, cloud provider, team size, execution strategy, compliance requirements, primary language/stack, related systems) — see `AOSDF/manual.md` § "How to Call the Workflow Initiator" for the full example.
