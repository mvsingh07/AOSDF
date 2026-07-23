# AOSDF — How This Works
# A Plain-Language Guide

---

## What Problem Does This Solve?

Building software with AI agents is powerful, but chaotic without a system. You end up with:
- AI that makes up its own architecture
- No record of decisions
- Security skipped because it's "just an internal tool"
- Features built before the data model is agreed on
- Agents doing the wrong thing because they don't have enough context

AOSDF (AI-Orchestrated Software Development Framework) solves this by giving AI agents a **structured playbook** — a set of documents, rules, and checkpoints that turn vague product ideas into working software, step by step, with minimal manual effort once the plan is locked.

---

## The Big Picture in One Paragraph

You describe your product. The framework breaks it into phases (think: quarters), milestones (think: sprints), tasks, and subtasks. For each subtask, a specific AI agent receives a precise prompt, does exactly one thing, and proves it worked. A human reviews at milestone boundaries — not at every step. The system tracks everything: what was built, what gaps were found, what manual actions are needed.

---

## The 12 Folders — What They Are

Think of the project folder as a filing cabinet. Each drawer has a specific purpose.

| Drawer | What Goes In It |
|--------|----------------|
| `00_Project_Context` | The "why" — what we're building and why it matters |
| `01_Product_Definition` | The "what" — what the product does, what it won't do, what rules it follows |
| `02_Security_Framework` | The "how not to get hacked" — must be filled before writing any code |
| `03_System_Design` | The "how it's built" — services, data flow, key decisions |
| `04_Infrastructure_Design` | The "where it runs" — cloud, servers, databases, costs |
| `05_AI_Agent_System` | The "who builds it" — AI agent definitions and their task templates |
| `06_Execution_Plan` | The "in what order" — every task, subtask, owner, and pass/fail condition |
| `07_Milestones` | The "checkpoints" — per-sprint deliverables and exit criteria |
| `08_Tracking_System` | [v2.2] Lightweight decisions log only (`decisions_log.md`) — **not** a task board; all task status lives in `06_Execution_Plan/execution_plan.md`'s Status column |
| `09_Testing_Validation` | The "proof it works" — test plans, test cases, load tests |
| `10_Deployment_Runbook` | The "how to ship it" — deploy steps, rollback, incident response |
| `11_Future_Extensibility` | The "what comes next" — deferred features and how the architecture enables them |
| `12_Manual_Actions` | [v1.7] The "human-only steps" — `actions.md` tracker + `guides.md` instructions |
| `13_Legal_Requirements` | [v1.9] Optional — regulatory obligations, compliance constraints binding on architecture |
| `14_Future_Migrations` | [v2.0] Recommended — infrastructure alternatives, OSS exit paths, portability design guide |
| `15_Addendums` | [v2.1] Optional — post-baseline cross-cutting changes, each with a plan + tracking file |

Plus one special file at the root:
- `identified_gaps.md` — every problem found, logged and tracked

Manual actions are tracked in `12_Manual_Actions/actions.md` (authoritative for v1.7+). `guides.md` holds step-by-step completion instructions.

---

## The Agents — Who Does What

Agents are AI workers. Each one has a defined role, specific inputs it reads, specific outputs it produces, and constraints it must follow. Think of them like team members with job descriptions.

| Agent | Job Description |
|------|----------------|
| **Workflow Initiator** | First to run on a new project. Asks setup questions, checks the filing cabinet, finds what's missing, gives the green light to start |
| **Research & Review** | Before design is finalized, researches how similar products are built. Prevents reinventing wheels badly |
| **Research & Refine** | [v1.4] Receives a `task.md` file and `project_root_path`. Reads the listed 00–04 docs as context, researches the defined scope, and writes findings + a recommendation to `research_results.md` at the project root. Never modifies any existing document. |
| **Identify Missing Docs** | Scans the project structure against the checklist. Reports gaps. Gets called by Workflow Initiator |
| **Captain** | [v1.3] After 00–05 docs are complete, reads them all and generates the execution plan, milestone files, and tracking board. Validates that every FRD service has a task. Sets project_status = READY. |
| **Commander** | Once per session, reads project_status.md + tracking board, finds the next task, delegates to the right agent. Never writes code. |
| **Execution Agent** | Strategy A worker: receives task from commander, generates the implementation prompt, saves it, executes, validates, updates the board. |
| **Reviewer** | Strategy B only: receives an implementation prompt from Architect, checks for security and scalability violations, approves or redlines. |
| **Validator** | Strategy B only: receives completed code from Implementor, runs tests, marks task Done in the tracking board if tests pass. |
| **Architect** | Designs services, writes ADRs, creates implementation prompts for the backend agent |
| **Backend** | Writes code. Only after contracts and schemas are defined. Writes tests too |
| **Infra** | Provisions cloud infrastructure. Terraform/CDK/OpenTofu. Never writes business logic |
| **QA** | Tests everything. Integration tests on real DB. Load tests. Security tests |
| **Frontend** | Builds UI. Inactive until UI phase is defined in project context |
| **Addendum** | [v2.1] Called after the plan is locked when a late cross-cutting requirement arrives. Reads the human-authored addendum doc, produces a scoped plan + tracking file entirely within `15_Addendums/`. Never touches the main tracking board or milestone files. |

---

## How Execution Actually Works

There are two modes:

### Mode A: One Agent, One Step at a Time

Best for: solo engineer, careful review of every step.

1. You call the Workflow Initiator and confirm the plan
2. It finds the next task in the execution plan
3. It hands the task to the right agent with a precise prompt
4. You approve the prompt (one click / one message)
5. Agent executes, validates, marks done
6. Repeat until milestone complete
7. You review milestone exit criteria, approve next milestone

Human effort: approve prompts, review milestone outputs. That's it.

### Mode B: Four-Agent Pipeline

Best for: larger scope, wanting to move faster with automated quality control.

```
Architect drafts the prompt
  → Reviewer checks for security + scalability issues
    → Implementor builds it
      → Validator tests it
        → Done (or loops back for fixes)
```

Humans only review at milestone boundaries. The four agents self-correct within a task.

---

## The Golden Rules (Plain Language)

**1. Nothing gets built without a contract.**
Before any agent writes code, the API shape and data schema must exist. This prevents "I assumed the field was a string" bugs.

**2. Security isn't optional.**
The `02_Security_Framework` folder must be complete before any agent touches `06_Execution_Plan`. No exceptions.

**3. Agents don't make it up.**
If an agent doesn't have enough information to complete a task, it stops and asks — it doesn't invent requirements. Gaps are logged, not papered over.

**4. Everything is tracked.**
Every task gets a status. Every gap gets a log entry. Every manual action gets a log entry. If it isn't in the tracking system, it didn't happen.

**5. Milestones are gates.**
You cannot start Milestone 2 until Milestone 1's exit criteria all pass. This prevents half-finished work piling up.

**6. Agents never push to remote branches.**
An agent may commit locally, but `git push` requires an explicit human instruction every time. No branch — feature, staging, or main — is ever pushed automatically.

---

## How to Start a New Project

1. Create the project folder structure (copy the 12-drawer template)
2. Call the **Workflow Initiator** agent
3. Answer its questions (product type, cloud provider, compliance needs, team size)
4. It scans for missing files, creates what it can, flags what you need to provide
5. Fill the flagged files (PRD, FRD, BRD — the product-specific documents)
6. Workflow Initiator confirms everything is ready
7. Choose execution strategy (A or B)
8. Start Milestone 1

From step 7 onward, human effort = approval gates only.

---

## How to Resume a Project

1. Call the **Workflow Initiator** agent again
2. It re-scans the structure, checks `execution_plan.md`'s Status column for current state [v2.2] — the only place task status lives
3. Identifies the next incomplete task
4. Resumes from there

Context is never lost because everything is in the files — not in a chat history.

---

## The Two Special Files

### `identified_gaps.md`
Every time an agent finds a problem — a missing security control, a design flaw, a doc gap — it logs it here with a severity and status. This file is reviewed at every milestone boundary. Nothing falls through the cracks.

### `manual_action.md`
Some things can't be automated: registering a sender ID on a government portal, approving a domain, getting a vendor API key. This file tracks those actions with their deadlines. If it's in here and not done, it will block execution.

---

## Document Formatting Standard [v1.4]

Every file created by any agent that contains a table must be formatted so a human can read it at a glance — not just a machine. This standard applies to milestone files, execution plans, tracking boards, research results, gap trackers, and any other tabular output.

**The two rules:**

**1. Separator dashes match column width.**
Count the widest value in each column (header or data). The separator row uses exactly that many dashes.
```
✅  | Task ID | Task Name                | Status    |
    | ------- | ------------------------ | --------- |

❌  | Task ID | Task Name | Status |
    |---------|-----------|--------|
```

**2. Data cells are padded to fill column width.**
Every cell in a column is padded with trailing spaces to match the column width. Columns visually align.
```
✅  | M1-T1   | Infra Provisioning       | Planned   |
    | M1-T2   | DB Schema                | Planned   |

❌  | M1-T1 | Infra Provisioning | Planned |
    | M1-T2 | DB Schema | Planned |
```

This is defined in `framework.md` [v1.4] § Document Formatting Standard and applies to every agent — captain, execution, research, validator, and any future agent.

---

## What Makes This Different from Just Using AI

Without AOSDF, AI agents:
- Forget context between sessions
- Make up architecture without reading your existing design
- Skip security
- Don't track what they've done
- Can't be resumed cleanly

With AOSDF:
- `CLAUDE.md` gives every agent full context in one read
- Security is a gate, not a suggestion
- Every task has a validation condition — the agent doesn't declare done until it passes
- `execution_plan.md`'s Status column is the ground truth of project state [v2.2] — there is no separate tracking board; `08_Tracking_System/decisions_log.md` holds only a lightweight decisions log
- Any agent, any session, can pick up exactly where the last one left off

---

## Agents That Require Manual Invocation

Most agents are called by other agents. But these agents **must always be called by a human**, because they need human judgment or human-authored input to proceed:

| Agent | When | Why Manual |
|------|-----|-----------|
| `workflow_initiator` | At project start; when resuming after a long gap | Needs you to answer setup questions about project type, cloud, compliance, team |
| `research_and_review` | Before architecture is finalized | You decide which reference systems to study and what aspects to focus on |
| `research_and_refine` | Any time a research question needs a structured answer | Requires a human-authored `task.md` + `project_root_path`; outputs to `research_results.md` only |
| `identify_missing_documents` | Called by workflow_initiator, or when you suspect structure drift | Needs the current project root path from you |
| `captain_agent` | After 00–05 docs are complete and locked | You confirm docs are final before it generates the binding execution plan |
| `addendum_agent` | When a post-baseline cross-cutting requirement arrives | Needs a human-authored `15_Addendums/<slug>.md` before it can plan |

**Everything else is called automatically** — the Commander Agent calls the Execution Agent, the Architect Agent calls the Reviewer, and so on.

---

## Agent Call Sequence — Full Simulation

Here is the exact order in which agents are called, from project start to first deployed feature.

```
1. HUMAN → workflow_initiator
   "Set up a new project called comms-engine..."
   ↓
   workflow_initiator asks 7 setup questions
   workflow_initiator calls → identify_missing_documents
   identify_missing_documents scans structure → returns gap list
   workflow_initiator creates/updates CLAUDE.md, project_status.md
   workflow_initiator sets project_status.md → PLANNING (docs need filling)

2. HUMAN → research_and_review (manual, before architecture is locked)
   "Research: Twilio, SendGrid, Postmark — focus on webhook and template patterns"
   ↓
   research_and_review produces research_notes.md
   research_and_review updates identified_gaps.md if new patterns found
   HUMAN reviews research_notes.md → confirms or adjusts architecture docs

   [HUMAN fills 00–05 documents: PRD, FRD, BRD, security, architecture, infra]

2c. HUMAN → research_and_refine (manual, any time — before or after captain_agent) [v1.4]
    Inputs: task.md (written by human) + project_root_path
    "Research X and tell me what the best option is given our constraints."
    ↓
    research_and_refine reads task.md → extracts objective, scope, context docs, constraints
    research_and_refine reads CLAUDE.md + only the context docs listed in task.md
    research_and_refine fetches public sources → extracts findings
    research_and_refine writes research_results.md (appends if already exists)
    research_and_refine does NOT modify any existing document
    HUMAN reads research_results.md → decides what to change, create ADRs, re-run captain_agent

2b. HUMAN → captain_agent (after 00–05 docs complete and locked) [v1.3]
    "Read all docs and generate the execution plan."
    ↓
    captain_agent reads FRD → extracts 8 services, all API endpoints, acceptance criteria
    captain_agent reads security_requirements.md → extracts all controls
    captain_agent reads infra_architecture.md → extracts all components
    captain_agent maps: services → tasks → milestones
    captain_agent writes execution_plan.md (flat table, all milestones, Status = the only status record) [v2.2]
    captain_agent writes 07_Milestones/M0/milestone.md through M3/milestone.md
    captain_agent writes 08_Tracking_System/decisions_log.md if absent (decisions log only — not a task board)
    captain_agent validates FRD coverage → every service has ≥1 task
    captain_agent sets project_status.md → READY
    HUMAN reviews milestones → confirms plan before execution begins

3. HUMAN → commander_agent (once per session, from M0 onward)
   ↓
   commander reads project_status.md → status = READY
   commander reads execution_plan.md → finds first row with Status = Planned [v2.2]
   commander reads milestone.md → checks pre-conditions

   --- Strategy A ---
   commander → execution_agent (with task context)
   execution_agent loads CLAUDE.md + FRD section
   execution_agent generates prompt → saves to implementation_prompts/
   execution_agent presents prompt to HUMAN: "Approve?"
   HUMAN approves
   execution_agent implements → validates
   execution_agent updates execution_plan.md Status: Done (the only status record)
   execution_agent reports to commander
   commander finds next Planned task in execution_plan.md → calls execution_agent again
   ... (repeats until milestone complete)

   --- Strategy B ---
   commander → architect_agent (with task context)
   architect_agent generates prompt → saves to implementation_prompts/
   architect_agent → reviewer_agent (security + scale review)
   reviewer_agent approves or sends back to architect
   reviewer_agent → implementor (approved prompt)
   implementor builds and tests
   implementor → validator_agent
   validator_agent runs tests → updates execution_plan.md Status: Done (the only status record)
   validator_agent → (back to commander for next task)

4. MILESTONE COMPLETE
   commander detects all milestone tasks = Done
   commander checks milestone exit criteria
   commander reports to HUMAN: "M0 complete. Ready for M1?"
   HUMAN reviews exit criteria → approves next milestone
   commander updates project_status.md milestone table
   session continues with M1
```

---

## How to Call the Workflow Initiator — Example

When starting a new project, paste this (or similar) as your first message:

```
Call workflow_initiator with the following project context:

Project name: comms-engine
Project root: Microservices/Comms-Engine/
One-line description: Multi-tenant, API-first, event-driven transactional communication platform
Has UI: No (Phase 1 is API-only)
Cloud provider: AWS (ap-south-1)
Team size: Solo engineer
Execution strategy: Strategy A (single-agent, sequential)
Compliance requirements: India DLT (SMS), append-only audit logs
Primary language/stack: TypeScript, Node.js, PostgreSQL, SQS
Related systems: Auction Engine (internal consumer)

Please:
1. Scan the project root for existing files
2. Identify missing required documents
3. Create CLAUDE.md if missing
4. Create project_status.md
5. Create identified_gaps.md and manual_action.md
6. Report what is ready and what needs human input before execution can begin
```

**What the initiator will do with this:**
- Detect which of the 12 sections already exist
- Create any missing boilerplate files
- Flag documents that require product-specific content (FRD, BRD) as "human input required"
- Set `project_status.md` to `PLANNING` or `READY` depending on what it finds
- Give you a numbered list of what to fill before calling the Commander

---

## How to Call the Commander Agent — Example

Once `project_status.md` = `READY`, start every execution session like this:

```
Call commander_agent.

Project: comms-engine
AOSDF docs root: Microservices/Comms-Engine/
Execution strategy: Strategy A

Please:
1. Read project_status.md and execution_plan.md
2. Identify the next Planned task (Status column — the only status record)
3. Verify no blocking manual actions for this milestone
4. Delegate to execution_agent with full context
```

**To resume after a break:**
The Commander will read `execution_plan.md`'s Status column and find exactly where you left off. No context from the previous session is needed — the state is in the files.

---

## Session Context Management — Rules for Agents and Humans

Context window space is a finite resource. Wasting it leads to higher token costs and mid-task failures. These rules are non-negotiable.

### Rule 1 — Compact proactively, not reactively

Before starting any task, the agent must assess how much context has already been consumed. If the session has had significant prior exchanges (large file reads, multi-step planning, long outputs), compact the chat before starting the next task:

- Use `/compact` (or the IDE equivalent) to compress prior turns into a summary
- Compact after every completed task, not just when context is nearly full
- Compacting early is cheap. Compacting late — or not at all — causes context overflow mid-task, which is the worst possible outcome

**Target:** Never exceed 60% context usage before starting a new task. Compact when approaching this threshold.

### Rule 2 — Do not start a task you cannot finish

Before delegating any task, the Commander Agent MUST estimate whether enough context window remains to complete it. If it is not confident the task can run to completion (including validation and the execution_plan.md Status update), it MUST NOT start the task.

**Instead, the Commander must:**
1. Say: "Insufficient context remaining to start [task name] safely. Please compact the session and re-invoke the Commander."
2. Stop. Do not begin partial execution.

A task left incomplete in the middle is worse than a task not started. Incomplete tasks can leave code, schema, or state in a broken intermediate state that is harder to recover than a clean start.

### Rule 3 — One task per compact cycle

Never chain multiple tasks across a single un-compacted session. Each task gets its own compact cycle:

```
compact → invoke Commander → Commander delegates → task runs to completion → compact → repeat
```

This keeps each task isolated, token-efficient, and recoverable.

### Rule 4 — Large file reads are expensive — scope them

When an agent needs to read documentation or code files, it must read only what is needed for the current task — not the full set of project documents. CLAUDE.md + the specific files listed in the task. Nothing else unless explicitly required.

---

## How to Call the Research & Review Agent — Example

Call this before finalizing `03_System_Design/`. Specify what you want researched:

```
Call research_and_review agent.

Project: comms-engine
Research scope:
- Twilio: focus on multi-channel routing, delivery status webhooks, idempotency
- SendGrid: template versioning, transactional vs marketing separation
- Postmark: bounce handling, DLQ equivalent patterns
- AWS SES: delivery notification structure, complaint handling

Output: produce research_notes.md in 00_Project_Context/
Flag any patterns not reflected in our current FRD or architecture docs.
```

The agent will produce `research_notes.md` and add any architectural gaps to `identified_gaps.md` for you to review.

---

## How to Call the Captain Agent — Example [v1.3]

Call this after all 00–05 documents are complete and you are ready to lock the plan:

```
Call captain_agent.

Project: comms-engine
AOSDF docs root: Microservices/Comms-Engine/

Please:
1. Read all 00–05 documents (FRD, PRD, BRD, security, architecture, infra)
2. Extract all services, security controls, and infra components
3. Map them to tasks grouped into milestones M0–M3
4. Write execution_plan.md (flat Phase→Milestone→Task→Subtask table)
5. Write each milestone.md with task table, exit criteria, and dependencies
6. Write 08_Tracking_System/decisions_log.md if absent (decisions log only — not a task board)
7. Validate FRD coverage — every service must have ≥1 task
8. Log unmapped requirements to identified_gaps.md
9. Set project_status.md → READY if coverage is complete
```

**What captain_agent will produce:**
- `06_Execution_Plan/execution_plan.md` — complete flat task table
- `07_Milestones/M0_Project_Setup/milestone.md` through `M3_Hardening/milestone.md`
- `08_Tracking_System/decisions_log.md` — created if absent (decisions log only, not a task board)
- Coverage validation report — every FRD service → task ID mapping
- `project_status.md` updated to READY

**To re-run after scope changes:**
```
Call captain_agent.

Project: comms-engine
AOSDF docs root: Microservices/Comms-Engine/
Reason for re-run: <new service added / feature removed / architecture changed>

Please:
1. Re-read FRD and architecture docs
2. Diff new requirements against current execution_plan.md (Status column is the record)
3. Append new tasks, mark removed tasks as Cancelled
4. Re-validate FRD coverage
5. Update project_status.md
```

---

## How to Call the Research & Refine Agent — Example [v1.4]

Call this any time a decision requires research before you can update the architecture, product, or security documents. Write a `task.md` first, then invoke the agent.

### Step 1 — Write your task.md

Create a file (anywhere) with this format:

```markdown
# Research & Refine Task

## Objective
Decide whether to use MJML or direct HTML templating for email rendering in the Rendering Service.

## Research Scope
- MJML: responsive email support, maintenance status, Fastify/Node.js ecosystem fit
- react-email: developer experience, output quality, bundle size
- Handlebars: flexibility, variable resolution, complexity for our block-based model

## Documents Likely Affected
- 03_System_Design/system_architecture.md: Rendering Service section
- 03_System_Design/service_design.md: Rendering Service responsibilities
- 01_Product_Definition/FRD.md: §2.5 Rendering Service, email channel spec

## Decision Required
Which library/approach to use for email rendering in the Rendering Service, and why.

## Constraints
- Block-based input model is locked (ADR-002) — do not change it
- P99 email render < 300ms is a hard target (PRD §3)
- Phase 1 only — no UI preview capability required
```

### Step 2 — Call the agent

```
Call research_and_refine_agent.

task.md: <path to your task.md>
project_root_path: Microservices/Comms-Engine/
```

**What the agent will do:**
1. Read `task.md` → extract objective, scope, context docs, constraints
2. Read `CLAUDE.md` + the listed context documents (not all 00–04 docs — only what's listed)
3. Fetch public documentation for MJML, react-email, Handlebars
4. Compare options against the project's constraints
5. Write findings + recommendation to `Microservices/Comms-Engine/research_results.md`

**What it will NOT do:**
- Modify any existing document (FRD, system_architecture.md, ADRs — nothing)
- Create ADRs (that's the human's job after reviewing the output)
- Update the execution plan or milestones

**After the agent runs:**
- Read `research_results.md` — it contains findings, comparison table, and recommendation
- Decide what to act on: update FRD §X, create a new ADR, adjust architecture docs
- If the decision affects scope: run `captain_agent` to update the execution plan

---

## How to Use the LLM Wiki [v1.6]

### What It Is
The `llm-wiki/` folder is a persistent knowledge base maintained by the LLM across
all sessions. Every document in `{project_name}-Documents/` is ingested and summarized
there. The wiki compounds over time — query answers, research results, and session
decisions all get filed and linked.

### When to Use Wiki vs. Agents vs. Direct Chat

| Situation                                         | Use                                           |
| ------------------------------------------------- | --------------------------------------------- |
| Understanding the product or architecture         | Wiki query (direct chat)                      |
| Starting or resuming a dev session                | AOSDF agent — `commander_agent`               |
| Generating or regenerating the execution plan     | AOSDF agent — `captain_agent`                 |
| Running structured research                       | AOSDF agent — `research_and_refine_agent`     |
| Capturing a decision or session summary           | Wiki — `Wiki: start session`                  |
| A source document changed                         | Wiki — `Wiki: re-ingest <file>`               |
| Multiple documents changed (e.g. captain re-run)  | Wiki — `Wiki: full-sync`                      |
| Checking project structure completeness           | AOSDF agent — `identify_missing_documents`    |
| Health-checking the wiki                          | Wiki — `Wiki: lint`                           |

The test: is this a **know** question or a **do** question?
- Know → use wiki (direct chat)
- Do → use agent (dev session)

### How Agents Use the Wiki
Agents are READ-ONLY consumers of the wiki. They never write to `llm-wiki/`.
They read `index.md`, find relevant pages, and use that context to inform their work.
The human is responsible for syncing the wiki after each agent run.

### Session Management
At the start of any session where decisions will be made:
1. Say `Wiki: start session` in your wiki session
2. Wiki records decisions, links, and changes made during the session
3. Say `Wiki: close session` at the end
4. Session indexed in `llm-wiki/sessions/session-contexts.md`

### Verifying Claude Is Using the Wiki
Ask: "What does the wiki say about [topic]?"
Claude should cite specific wiki page paths. If it doesn't, say:
"Read llm-wiki/index.md first, then answer."

### Quick Command Reference

| Command                          | Action                                      |
| -------------------------------- | ------------------------------------------- |
| `Wiki: ingest <path>`            | Ingest a new file                           |
| `Wiki: ingest all`               | Ingest all files in Documents/              |
| `Wiki: re-ingest <path>`         | Update wiki from a changed file             |
| `Wiki: full-sync`                | Re-read all sources, update stale pages     |
| `Wiki: start session`            | Begin a session record                      |
| `Wiki: close session`            | Finalize and file the current session       |
| `Wiki: lint`                     | Health-check the entire wiki                |
