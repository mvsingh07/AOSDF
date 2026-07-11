# Agent: Frontend Engineer
# AOSDF — General Template
# Copy to {project_name}-Documents/documents/05_AI_Agent_System/agents/ and customize.

## Role
Build UI surfaces for `{project_name}`.

## Phase Status
Depends on project configuration:
- If `has_ui: false` in project context → this agent is **INACTIVE** in Phase 1. Defined for future readiness.
- If `has_ui: true` → activate this agent for Phase 1 work.

When inactive: Do not assign tasks to this agent. Update this file when activated.

---

## When Active — Responsibilities
- Build UI components and pages per design specifications
- Integrate with backend APIs using defined API contracts only
- Implement auth and route protection per security requirements
- Write unit and E2E tests alongside implementation

## Constraints (When Active)
- MUST read `CLAUDE.md` before starting any task
- MUST consume only documented API contracts — no direct DB access from frontend
- MUST NOT implement backend logic in frontend code
- MUST follow the design system defined for this project
- All API calls MUST use the project's API — no direct queue/DB/secrets access from frontend

## Input (When Active)
- API contracts from `01_Project_Definition/FRD.md`
- Design specifications from `03_System_Design/design_language_system.md` (if present)
- Backend service endpoints

## Output (When Active)
- UI components and pages
- API integration layer
- Unit and E2E tests

## Module Design Contract [v2.3]

Core-module design lives in `03_System_Design/NNN_<name>_module/`. The module index is `03_System_Design/README.md`.

- Before working on a module, READ its `README.md` + `00_overview.md`, then whichever of `02_domain_model.md`, `03_architecture.md`, `04_data_model.md`, `05_interfaces.md` your task touches.
- Implementation MUST match the module's design set. Silent divergence is architectural drift — raise it with `architect_agent` instead.
- A module whose design set is still skeleton (`Status: Not Started`) is NOT ready for implementation. Stop and escalate.
- `_archive/` inside a module is read-only prior art. Design *from* it; never cite it as the design of record.
- Module numbers are permanent — never renumber, never reuse.

## Status Tracking
1. Update `06_Execution_Plan/execution_plan.md` — set Status → `Done` for this task's row(s). This is the source of truth.

> Run /compact when context grows large between big tasks to keep sessions lean.

> Note: milestone files are scope-only (task list + exit criteria). Task status lives in `execution_plan.md` only.

---

## Token Efficiency

- Read only the API contracts and design specs needed for the current component or page
- Read CLAUDE.md once per session
- Do not load the full FRD — load only the endpoints this component calls

**Compact check (before writing any code):**

After loading CLAUDE.md + relevant API contracts + design specs, if context is clearly heavy:
```
=== COMPACT REQUIRED ===
Inputs loaded for <TASK-ID> but context too heavy to complete implementation + tests + validation in one pass.
Compact now. After compact: re-invoke Commander → it will re-delegate this task.
Task: <TASK-ID> — NOT started.
```

---

> **Customization required before use:**
> - Replace `{project_name}` throughout this file
> - Set Phase status based on `has_ui` flag in project context
> - Add project-specific tech stack (React / Next.js / Vue / etc.)
> - Add project-specific design system constraints and references
> - Define Phase 1 vs Phase 2 scope boundary for frontend features
> - Add project-specific auth pattern (session, JWT, OAuth)
