# AOSDF Rules
# v2.3 — Quick Reference
# Non-negotiable. Every agent and human must follow these.

---

## The 23 Principles (Condensed)

| # | Rule | Version |
|---|------|---------|
| 1 | **Security-first** — security doc must exist and be reviewed before any coding | v1.0 |
| 2 | **Contract-first** — API contracts and schemas before implementation tasks | v1.0 |
| 3 | **AI-agent compatible** — every task = executable prompt with deterministic output | v1.0 |
| 4 | **Iterative milestones** — each milestone = working, testable system slice | v1.0 |
| 5 | **Traceability** — every task → output → validation → status | v1.0 |
| 6 | **Research-before-design** — research pass on comparable systems before architecture locks | v1.1 |
| 7 | **Gap-tracking is first-class** — every gap logged in `identified_gaps.md` immediately | v1.1 |
| 8 | **Manual action tracking** — every human step logged in `12_Manual_Actions/actions.md` immediately, never deferred | v1.1 / v1.7 |
| 9 | **Minimum human intervention after 05** — agents execute with human approval gates only | v1.1 |
| 10 | **Execution-ready gate** — `project_status.md` must be `READY` before any implementation begins | v1.2 |
| 11 | **Implementation prompts are tracked artifacts** — every prompt saved to `implementation_prompts/` before execution | v1.2 |
| 12 | **AI documentation is never committed** — all AOSDF docs live in gitignored folders | v1.2 |
| 13 | **M0 is always first** — repo and stack setup before any infrastructure or feature work | v1.2 |
| 14 | **Execution plan is agent-generated** — captain_agent generates it; manual writing is not permitted | v1.3 |
| 15 | **FRD → task coverage validated** — every FRD service spec maps to ≥1 task or it's a Critical gap | v1.3 |
| 16 | **project_status.md transitions have defined owners** — see agent_index.md | v1.3 |
| 17 | **Manual actions tracked with per-env status** — `actions.md` rows include Dev/Staging/Prod columns | v1.7 |
| 18 | **LLM Wiki is read-only for agents** — agents read wiki; only humans write to `llm-wiki/` | v1.6 |
| 19 | **Legal requirements are binding constraints** — `13_Legal_Requirements/` files must map to execution plan tasks | v1.9 |
| 20 | **Every infrastructure client behind an abstraction** — provider SDK never imported in business logic | v2.0 |
| 21 | **Post-baseline changes via Addendums only** — no ad-hoc edits to tracking_board or milestones after plan is locked | v2.1 |
| 22 | **execution_plan.md is the only task-status record — no separate tracking board** — the Status column is the canonical Planned/In Progress/Done record; `08_Tracking_System/` holds only `decisions_log.md` (a lightweight decisions log, not a task board) | v2.2 |
| 23 | **System design is per-module** — `03_System_Design/` splits into cross-cutting root docs + one `NNN_<name>_module/` folder (seven-document set, cloned from `_template/`) per core module; module numbers are permanent | v2.3 |

---

## Absolute Hard Rules (Zero Exceptions)

```
git push is NEVER done by an agent — human only, every time
WRITE_INFRA requires explicit human approval before apply
No code without API contract + schema + security review complete
No agent starts implementation if project_status ≠ READY
No agent skips the implementation_prompts/ save step
No partial-done task — declare Done only when all criteria pass
identified_gaps.md: log immediately, never defer
12_Manual_Actions/actions.md: log immediately, never defer
```

---

## What Each Key File Is For

| File | Owner | Purpose |
| ---- | ----- | ------- |
| `CLAUDE.md` | Human (fills) | Authoritative context for every agent session — read first |
| `project_status.md` | `captain_agent`, `commander_agent` | Single source of truth for execution readiness |
| `identified_gaps.md` | Any agent (append) | Every gap, immediately logged |
| `12_Manual_Actions/actions.md` | Any agent (append) | Every human step, immediately logged |
| `12_Manual_Actions/guides.md` | Any agent (append) | Step-by-step instructions per action ID |
| `execution_plan.md` | `captain_agent` (creates); `execution_agent` / `validator_agent` (Status column) | **[v2.2] The only task-status record.** Flat table: Phase → Milestone → Task → Subtask → Status. Commander reads this to find the next `Planned` row — no other file is ever consulted for status |
| `08_Tracking_System/decisions_log.md` | `captain_agent` (creates if absent) | **[v2.2]** Lightweight decisions log only — **not** a task board, never holds Status. There is no `tracking_board.md` in AOSDF v2.2+ |
| `implementation_prompts/<TASK-ID>_*.md` | `execution_agent` / `architect_agent` | Every prompt saved before execution |
| `research_results.md` | `research_and_refine_agent` | Research output — human decides what to act on |
| `15_Addendums/tracking_addendums.md` | `addendum_agent` (initial), then execution/human | Post-baseline task tracking |

---

## Session Management Rules (v1.8)

```
compact → invoke commander → task runs to completion → compact → repeat
```

- Never exceed 60% context before starting a task
- Commander must NOT start a task it cannot complete (including validation + board update)
- Agents read ONLY files needed for the current task — no speculative loading
- A task left half-done is worse than a task not started

---

## wiki/ — The Four Rules

1. Agents READ from `llm-wiki/` only
2. Agents WRITE to `{ProjectName}-Documents/` and source code only
3. Wiki updates: human-only via `Wiki:` commands
4. If wiki and source document contradict: trust source document; flag to human
