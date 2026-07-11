# Reference — Raw Product Knowledge
# {ProjectName}
# AOSDF v2.2 [v2.2]

This folder holds raw product knowledge documents — the source material that informs the structured 00–05 documents.

Agents READ this folder. No agent writes to it or modifies files here.

---

## What Goes Here

| Type | Examples |
| ---- | -------- |
| Product briefs | One-pagers, vision docs, pitch deck content, founder notes |
| Stakeholder requirements | Raw requirements from business owners, clients, or PMs — before they are structured into PRD/FRD |
| User research | Interview notes, survey results, persona sketches, user journey maps |
| Competitor / market research | Competitor teardowns, industry analysis, pricing comparisons |
| Vendor / API documentation | Key excerpts or summaries from third-party API docs (e.g., Twilio, Stripe, Supabase) |
| Existing system documentation | Specs or docs from systems this project integrates with |
| Design references | Brand guidelines, design language notes, UI inspiration — if has_ui is true |
| Business context | Company background, go-to-market strategy, customer contracts that constrain the build |
| Technical constraints | Existing infrastructure that must be worked around, legacy system notes |

---

## What Does NOT Go Here

- Structured product documents (PRD, FRD, BRD) → those belong in `01_Project_Definition/`
- Architecture decisions → `03_System_Design/`
- Security requirements → `02_Security_Framework/`
- Research output from agents → `research_results.md` at Documents root

---

## How Agents Use This Folder

Agents that need product context read this folder before performing tasks that involve understanding the product domain. They do not use it as a replacement for the structured 00–05 documents — it is supplementary input for when the structured docs don't have enough detail.

Specifically:
- `research_and_review_agent` — reads here before researching comparable systems
- `research_and_refine_agent` — reads relevant files listed in `task.md` context documents
- `captain_agent` — may read here if product intent is unclear from the structured docs
- `architect_agent` — reads here when designing features whose business rationale matters

Agents never modify, delete, or create files in this folder.

---

## Index

Add an entry here for each file you put in this folder:

| File | Type | Description | Date Added |
| ---- | ---- | ----------- | ---------- |
|      |      |             |            |

---

## Sync Note

If a reference document is ingested into the LLM Wiki, record it here:

| File | Wiki Page | Synced |
| ---- | --------- | ------ |
|      |           |        |
