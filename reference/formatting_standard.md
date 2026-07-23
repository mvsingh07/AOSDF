# Document Formatting Standard
# AOSDF v1.4 — Quick Reference
# Applies to every file with a table created or updated by any agent. Non-negotiable.

---

## The 5 Rules

### Rule 1 — Separator dashes match column width

Count the maximum character width of each column (header or longest data value, whichever is greater). Fill the separator row with exactly that many dashes.

```
✅ Correct
| Task ID | Task Name                | Owner        | Status    |
| ------- | ------------------------ | ------------ | --------- |

❌ Wrong
| Task ID | Task Name | Owner | Status |
|---------|-----------|-------|--------|
```

### Rule 2 — Data cells padded to fill column width

Every value in a column is padded with trailing spaces to match the column width.

```
✅ Correct
| M1-T1   | Infra Provisioning       | Infra        | Planned   |
| M1-T2   | DB Schema                | Backend      | Planned   |

❌ Wrong
| M1-T1 | Infra Provisioning | Infra | Planned |
| M1-T2 | DB Schema | Backend | Planned |
```

### Rule 3 — Column widths are consistent across all files in the same project

When a table schema appears in multiple files (e.g., the task table in every milestone file), determine column widths once from the widest values across all files, then use those same widths everywhere.

### Rule 4 — Blank separator rows between logical groups

In tables that span multiple milestones or phases, add a blank row between groups:

```
| M0-T1   | Repo init                | Infra        | Done      |
| M0-T2   | Folder structure         | Backend      | Done      |
|         |                          |              |           |
| M1-T1   | DB schema                | Backend      | Planned   |
```

### Rule 5 — No exceptions

Every agent that writes a file with a table must follow Rules 1–4. This includes:
- `captain_agent` → `execution_plan.md`, `milestone.md`, `08_Tracking_System/decisions_log.md`
- `execution_agent` / `validator_agent` → `execution_plan.md` Status column updates
- `research_and_refine_agent` → `research_results.md`
- `addendum_agent` → `<slug>_plan.md`, `tracking_addendums.md`
- Any agent writing `identified_gaps.md` or `12_Manual_Actions/actions.md`

A two-row table follows the same rules as a fifty-row table.

---

## Common Column Width Reference

These are typical minimum widths — always extend to the actual longest value in your data:

| Column | Typical Min Width | Notes |
| ------ | ----------------- | ----- |
| Task ID | 7 (`M1-T1  `) | Grows with milestone depth (e.g., `M2.2-T3`) |
| Gap ID | 8 (`GAP-001`) | |
| Action ID | 9 (`MA-001  `) | |
| Status | 10 (`In Progress`) | Longest value drives width |
| Owner | 7 (`Backend`) | |
| Priority | 8 (`P1     `) | |
| Severity | 8 (`Critical`) | |

---

## Quick Check Before Submitting Any File

- [ ] Separator row dashes match the widest cell in each column
- [ ] Every data cell padded to column width with trailing spaces
- [ ] Blank row between milestone groups in execution_plan.md
- [ ] Column widths match other files in this project with the same schema
