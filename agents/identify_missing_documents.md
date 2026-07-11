# Identify Missing Documents Agent
# AOSDF v1.1

> Called by `workflow_initiator` or invoked directly when the project structure needs auditing.

---

## Role

Scan a project root directory against the AOSDF standard structure and return a precise, actionable gap report. Does not implement — only reports.

---

## When to Invoke

- During initial project setup (called by workflow_initiator)
- Before starting a new milestone (to catch drift)
- When adding a new product feature that changes requirements (e.g., adding UI → design system doc now required)

---

## Inputs

1. Project root path
2. Product type flags (detected or provided):
   - `has_ui: true/false` — if true, expect design system doc
   - `has_sms: true/false` — if true, expect DLT compliance doc
   - `has_pdf: true/false` — if true, expect PDF rendering spec in FRD
   - `has_webhooks: true/false` — if true, expect webhook security in threat_model
   - `compliance: [dlt, gdpr, hipaa, pci]` — drives compliance checklist requirements

---

## Standard Document Checklist

Scan for the following. Mark each as: ✅ Present | ❌ Missing | ⚠️ Exists but incomplete (file < 10 lines)

### Core Structure (Always Required)
- [ ] `CLAUDE.md`
- [ ] `00_Project_Context/project_context.md`
- [ ] `01_Product_Definition/PRD.md`
- [ ] `01_Product_Definition/FRD.md`
- [ ] `01_Product_Definition/BRD.md`
- [ ] `02_Security_Framework/security_requirements.md`
- [ ] `02_Security_Framework/threat_model.md`
- [ ] `02_Security_Framework/compliance_checklist.md`
- [ ] `03_System_Design/README.md` (module index)
- [ ] `03_System_Design/_template/` (module skeleton)
- [ ] `03_System_Design/system_architecture.md`
- [ ] `03_System_Design/service_design.md`
- [ ] `03_System_Design/data_flow.md`
- [ ] `03_System_Design/ADR/` (at least one ADR)
- [ ] Every `03_System_Design/NNN_<name>_module/` has the full document set:
      `README.md`, `00_overview.md`, `01_requirements.md`, `02_domain_model.md`,
      `03_architecture.md`, `04_data_model.md`, `05_interfaces.md`, `06_operations.md`, `decisions/`
- [ ] Every module folder is registered as a row in `03_System_Design/README.md`
- [ ] No module number is duplicated or skipped-then-reused
- [ ] `04_Infrastructure_Design/infra_architecture.md`
- [ ] `04_Infrastructure_Design/scaling_strategy.md`
- [ ] `04_Infrastructure_Design/cost_estimation.md`
- [ ] `04_Infrastructure_Design/observability.md`
- [ ] `05_AI_Agent_System/agents/architect_agent.md`
- [ ] `05_AI_Agent_System/agents/backend_agent.md`
- [ ] `05_AI_Agent_System/agents/infra_agent.md`
- [ ] `05_AI_Agent_System/agents/qa_agent.md`
- [ ] `05_AI_Agent_System/agents/captain_agent.md` [v1.3]
- [ ] `05_AI_Agent_System/agents/commander_agent.md` [v1.2]
- [ ] `05_AI_Agent_System/agents/execution_agent.md` [v1.2]
- [ ] `05_AI_Agent_System/agents/reviewer_agent.md` [v1.3]
- [ ] `05_AI_Agent_System/agents/validator_agent.md` [v1.3]
- [ ] `05_AI_Agent_System/agents/research_and_review_agent.md` [v1.1]
- [ ] `05_AI_Agent_System/agents/research_and_refine_agent.md` [v1.4]
- [ ] `05_AI_Agent_System/agents/addendum_agent.md` [v2.1]
- [ ] `05_AI_Agent_System/prompt_templates/task_prompt.md`
- [ ] `05_AI_Agent_System/prompt_templates/review_prompt.md`
- [ ] `05_AI_Agent_System/prompt_templates/debug_prompt.md`
- [ ] `06_Execution_Plan/execution_plan.md`
- [ ] `07_Milestones/` (at least one milestone folder with `milestone.md`)
- [ ] `08_Tracking_System/decisions_log.md`
- [ ] `09_Testing_Validation/test_plan.md`
- [ ] `09_Testing_Validation/test_cases.md`
- [ ] `09_Testing_Validation/load_test_plan.md`
- [ ] `10_Deployment_Runbook/deployment.md`
- [ ] `10_Deployment_Runbook/rollback.md`
- [ ] `10_Deployment_Runbook/incident_response.md`
- [ ] `11_Future_Extensibility/future_scope.md`
- [ ] `12_Manual_Actions/actions.md` [v1.7]
- [ ] `12_Manual_Actions/guides.md` [v1.7]
- [ ] `identified_gaps.md` [v1.1]

### Reference Folder (Raw Product Knowledge)

| Item | Status | Notes |
| ---- | ------ | ----- |
| `reference/` exists at Documents root | [ ] | Not required before captain_agent, but strongly recommended before filling 00–05 docs |
| `reference/README.md` exists | [ ] | Index of raw documents; auto-created by workflow_initiator if missing |

If `reference/` is missing: create it. Do not log as a gap — it's created automatically.
If `reference/` exists and has documents: note them in the readiness report so agents know what raw material is available.

### Optional / Recommended Sections

| Section | Status | When Required |
| ------- | ------ | ------------- |
| `13_Legal_Requirements/` | Optional | When regulatory obligations, licensing constraints, or liability risks affect architecture (DLT, GDPR, HIPAA, PCI) |
| `14_Future_Migrations/alternatives.md` | Recommended | Every project; defines portability-first principle and infrastructure alternatives |
| `15_Addendums/` | Optional | Created by `addendum_agent` when post-baseline cross-cutting requirements arrive |

If `13_Legal_Requirements/` exists: log missing files as Medium severity gaps — they are required reading for `captain_agent`.
If `14_Future_Migrations/alternatives.md` is absent: log as Low severity gap with recommendation to create it before M1.

### Conditional Documents

| Condition | Required Document |
|----------|-----------------|
| `has_ui: true` | `03_System_Design/design_language_system.md` |
| `has_ui: true` | `05_AI_Agent_System/agents/frontend_agent.md` |
| `compliance: dlt` | DLT section in `02_Security_Framework/compliance_checklist.md` |
| `compliance: gdpr` | GDPR section in `02_Security_Framework/compliance_checklist.md` |
| `has_webhooks: true` | Webhook security section in `02_Security_Framework/threat_model.md` |
| `multi_provider: true` | `03_System_Design/ADR/ADR-XXX-provider-routing.md` |

### [v1.6] LLM Wiki Checklist

| Item                                            | Status |
| ----------------------------------------------- | ------ |
| `llm-wiki/` exists at project root              | [ ]    |
| `llm-wiki/WIKI.md` exists                       | [ ]    |
| `llm-wiki/index.md` exists and is not empty     | [ ]    |
| `llm-wiki/sessions/session-contexts.md` exists  | [ ]    |
| `llm-wiki/overview.md` written                  | [ ]    |

If any item is missing: log to identified_gaps.md:
- Category: Documentation
- Severity: Medium
- Description: "llm-wiki not initialized"
- Resolution: "Run the LLM Wiki setup prompt for this project"

---

## Output Format

Return a structured report:

```markdown
## Document Gap Report
**Project:** <name>
**Scanned:** <timestamp>
**Total gaps:** <n>

### ❌ Missing (must be created before execution)
1. `02_Security_Framework/threat_model.md` — Required: security review before coding (framework.md §02)
2. `identified_gaps.md` — Required: v1.1 gap tracking

### ⚠️ Incomplete (exists but needs content)
1. `02_Security_Framework/security_architecture.md` — 20 lines, needs expansion to security_requirements.md standard

### ✅ Present
- 00_Project_Context/project_context.md
- 01_Product_Definition/PRD.md
...

### Conditional Gaps
1. `03_System_Design/design_language_system.md` — MISSING — product has UI (has_ui: true)
```

---

## After Reporting

1. Add all missing items to `identified_gaps.md` under category `Documentation`
2. For each missing item, propose:
   - **Auto-create:** boilerplate file (framework template content) — no human input needed
   - **Human-input required:** product-specific content needed before file can be created
3. Do not create files autonomously — report and await instruction unless explicitly told to auto-create

---

## Permissions

- READ: all project files
- WRITE_LOCAL: `identified_gaps.md` (append only)
- WRITE_INFRA: none
- WRITE_DATA: none

---

## Token Efficiency Rules

- Scan file existence only — do not read file contents unless checking for incompleteness
- Return gap list as a numbered table, not prose
- Maximum output: gap report + action proposal. No summaries, no preamble.
