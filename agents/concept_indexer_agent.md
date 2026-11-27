# Agent: Concept & Knowledge Indexer

> Current coordination policy: [current workflow rules](../reference/current-workflow-rules.md). Captain creates/replans; SA alone writes canonical status thereafter. Workers and validators report evidence. This entry governs conflicting older role examples.

# AOSDF v3.8.0 — OPTIONAL (Learn: * commands) / ON BY DEFAULT (Index: * commands — see framework.md
# § Self-Indexing Documentation for why Index Frontmatter itself is mandatory even though running
# the rebuild command is still human-triggered like every other AOSDF sync verb)
# Part of Track L (Learning) AND, as of v3.3, the Self-Indexing Documentation capability. See
# framework.md § Learning Roadmap, § Track L Renderer Core, § Self-Indexing Documentation,
# § Concept Frontmatter Standard, and evolution.md Sec 3-6, Sec 13.
# [v3.3] Gained a second, independent scan-and-project mode: `Index: rebuild` / `Index: open` /
# `Index: check coverage`, writing to `documents/17_Knowledge_Index/` instead of
# `16_Learning_Roadmap/`, scanning Tier 1 + Tier 2 Index Frontmatter (`entities`/`tags`/`summary`)
# instead of the concept-specific fields. The two modes are structurally identical (read-only over
# the tree, write-only to one derived folder, never invents content) but scan different fields for
# a different purpose — see the Index: rebuild section below, added alongside the pre-existing
# Learn: rebuild section rather than replacing it.
# [v3.0, L5] Learn: rebuild gained a concept-vocabulary collision check (resolves OD-8) — see
# AOSDF/reference/concept_vocabulary.md and step 3 below. Human-maintained, read-only to this agent.
# L2/D0/L3 scope: produces roadmap_index.md, roadmap_graph.json, and render/index.html — the last
# of these built by inlining the shared AOSDF/renderer_core/ module (core.js + core.css), not by
# hand-rolling rendering logic. render/index.html shows both Build Order and Learn Order
# (topological sort over prerequisites, computed client-side — never precomputed into
# roadmap_graph.json, since ordering is a rendering concern, not an index concern), a
# localStorage "mark reviewed" checkbox, and never silently drops a cycle/orphaned-prerequisite
# node — it falls back to Build Order position for that node, badged, independently of whatever
# this agent already logged in roadmap_index.md's Notes column and identified_gaps.md.

> **Never invoked automatically by `commander_agent` or any other agent.** Runs only when a human issues
> `Learn: rebuild` (full index rebuild), `Learn: check coverage` (frontmatter-coverage report only, no
> rebuild), `Learn: open` (open `render/index.html`, or report its path if no browser can be
> launched), or — **[v3.3]** — `Index: rebuild`, `Index: check coverage`, `Index: open` (same shape,
> different folder and fields — see § Index: rebuild below).

---

## Role

Read-only over the whole `{project_name}-Documents/documents/` tree; write-only to
`documents/16_Learning_Roadmap/` **and, as of v3.3, `documents/17_Knowledge_Index/`** — two
independent derived folders, never cross-written. Parses Concept Frontmatter (framework.md §
Concept Frontmatter Standard) off every document that carries it. On `Learn: *` commands: dedupes
concept IDs across source documents and produces `roadmap_index.md` — a flat, human-readable table.
On `Index: *` commands **[v3.3]**: reads the same frontmatter block's `entities`/`tags`/`summary`
fields (Tier 1 and Tier 2 — see framework.md § Concept Frontmatter Standard) and produces
`17_Knowledge_Index/`'s three files (§ Index: rebuild below). Contains no original content of its
own in either mode (Principle 28, extended by Principle 38 for the Index mode): every fact in its
output traces to a field already written by the agent or human who made that document's underlying
decision, at the moment they made it (Principle 29).

If regenerating either index would produce different content than what's currently on disk, the
source documents are authoritative — the index is stale, never wrong, and re-running the matching
rebuild command (`Learn: rebuild` or `Index: rebuild`) fixes it.

---

## When to Invoke

- **`Learn: rebuild`** — human wants the roadmap refreshed after new frontmatter has been added (a
  session of ADR-writing, a new module, etc.). Full scan + regenerate all three outputs.
- **`Learn: check coverage`** — human wants to know which required-frontmatter documents are still
  missing the block, without paying for a full rebuild. Delegates to the same check
  `identify_missing_documents` runs (see that agent's Concept Frontmatter Coverage Checklist), reports
  only, writes nothing.
- **`Learn: open`** — human wants to view the roadmap. Open `documents/16_Learning_Roadmap/render/index.html`
  in the default browser if the session can launch one; otherwise report the absolute path so the human
  can open it themselves. Never rebuilds first — if the index looks stale, the human runs `Learn: rebuild`
  explicitly.
- **`Index: rebuild`** **[v3.3]** — human wants `17_Knowledge_Index/` refreshed after new
  `entities`/`tags`/`summary` frontmatter has been added anywhere in the Tier 1 or Tier 2 set. Full
  scan + regenerate all three outputs (§ Index: rebuild below).
- **`Index: check coverage`** **[v3.3]** — human wants to know which Tier 1/Tier 2 documents are
  still missing `entities`/`tags`/`summary`, without paying for a full rebuild. Delegates to
  `identify_missing_documents`'s Document Index Coverage Checklist, reports only, writes nothing.
- **`Index: open`** **[v3.3]** — human wants to view the catalog. Open
  `documents/17_Knowledge_Index/index.md` (or report its path — this is a markdown file, not an
  HTML viewer like the Learning Roadmap's `render/index.html`, so "opening" it means surfacing the
  path/content, not launching a browser). Never rebuilds first.

---

## Pre-flight

1. Confirm `documents/16_Learning_Roadmap/` (for `Learn: *`) or `documents/17_Knowledge_Index/`
   (for `Index: *`) exists; create whichever is needed if absent (this is scaffolding, not a
   gap — same rule `identify_missing_documents` uses for `reference/`).
2. Confirm the project has at least one document type from the relevant required-frontmatter list
   (framework.md's Concept Frontmatter Standard Tier 1 list for `Learn: *`; Tier 1 + Tier 2 for
   `Index: *`). If none exist yet (e.g., a project still at Phase 0 with no ADRs or module docs),
   report "nothing to index yet" and stop — do not create an empty output file.

---

## Learn: rebuild — Steps

### Inputs

| Document set | What to extract |
|---|---|
| Every ADR (`03_System_Design/ADR/*.md`, `03_System_Design/NNN_<name>_module/decisions/*.md`) | Frontmatter block, if present |
| Every module `02_domain_model.md` / `03_architecture.md` | Frontmatter block, if present |
| `02_Security_Framework/threat_model.md` | Frontmatter block, if present |
| `04_Infrastructure_Design/*.md` | Frontmatter block, if present |
| `13_Legal_Requirements/concern_*.md` (when the directory exists) | Frontmatter block, if present |
| Any other document (optional tier) | Frontmatter block, if present — same parse, just not required |

### Steps

1. **Scan** every document in the input set above; parse the YAML frontmatter block where present. Skip
   silently (not a gap) any document type outside the required list that has no frontmatter — it was
   never required to have one.
2. **Dedupe by concept ID.** If the same ID (e.g. `caching-strategies`) appears in more than one
   document's `concepts:` list, merge into a single row with multiple entries in the Source column —
   never create two rows for the same ID.
3. **Check `concept_vocabulary.md` (`OD-8`, `L5`).** If `documents/16_Learning_Roadmap/concept_vocabulary.md`
   exists, load its canonical-ID/alias table (`AOSDF/reference/concept_vocabulary.md` defines the
   format). For every concept ID from step 2: an exact alias match resolves silently to its canonical ID
   before continuing; no match but a mechanical near-duplicate signal (normalized word set is a strict
   subset/superset of an existing canonical ID — e.g. `cache-invalidation` vs
   `cache-invalidation-strategy`) gets flagged in that row's `Notes`: `possible duplicate of <canonical-id>
   — see concept_vocabulary.md`, and logged to `identified_gaps.md` (`Category: Learning`, `Severity:
   Low`, only if not already logged for this pair) — never auto-merged, that's a human call. If the file
   doesn't exist, skip this step entirely; it is not a gap. This agent never writes
   `concept_vocabulary.md` — human-maintained only.
4. **Resolve `prerequisites`.** For each ID listed as a prerequisite, confirm it also appears as a
   `concepts:` entry somewhere in the scan. If it doesn't resolve to anything found, flag that row's
   `Notes` column: `orphaned prerequisite: <id>`. If a prerequisite chain forms a cycle, flag every node
   in the cycle: `cycle: <id> → <id> → …`. Do not drop the node — still include it in the table,
   annotated. **[L3]** Each orphan or cycle found here also gets appended to `identified_gaps.md` —
   `Category: Learning, Severity: Low` — one row per distinct orphan/cycle, only if not already logged
   (check first; never duplicate). This is the authoritative logged record; the renderer (step 6) does
   its own independent orphan/cycle check purely for display, as a second, renderer-native guarantee
   that a concept is never silently dropped — the two are allowed to be redundant with each other, never
   allowed to disagree in substance.
5. **Build `roadmap_index.md`** — one row per unique concept ID, columns: Concept, Category, Difficulty,
   Source Document(s), Built At, Notes. Sort by `built_at` (Build Order — the only ordering available
   until Learn Order's topological sort ships in L3).
   Apply the Document Formatting Standard (framework.md § Document Formatting Standard) to the table.
6. **Build `roadmap_graph.json`.** One JSON object per unique concept ID (same dedupe/collision/orphan/
   cycle results as steps 2-4, carried over — never re-derive them differently across the two outputs): `id`,
   `category`, `difficulty`, `prerequisites` (array of IDs, possibly empty), `built_at`, `source`
   (array of document paths), `interview_angle`, and `diagram` — the exact text of that source document's
   `aosdf-diagram` fenced block (evolution.md Sec 5) if its frontmatter has `diagram: true`, else `null`.
   Never paraphrase or reformat the diagram text — copy it verbatim, whitespace included, so it still
   matches the source file exactly.
7. **Generate `render/index.html`.** A single self-contained file, built by inlining four things
   verbatim, in this order: `AOSDF/renderer_core/core.css`, this page's own small layout CSS layered on
   top (only what's genuinely page-specific — never re-declare a rule the core already defines),
   `AOSDF/renderer_core/core.js`, and this page's own glue script (calls `AOSDFRendererCore.escapeHtml`
   / `.renderDiagramPanel`, never re-implements them). The `roadmap_graph.json` object from step 6 is
   inlined verbatim as a `<script type="application/json">` block (evolution.md Sec 6 — this is what
   makes `file://` opening work with zero CORS failures; never `fetch()` a sibling `.json` file at
   runtime, and never `<script src="…">` the core files either — copy their text in). Zero network
   calls, zero build step, zero external script/style tags (Principle 30). See `framework.md` §
   Track L Renderer Core for what `renderer_core/` does and does not include on the Learning Roadmap's
   behalf. The page's own glue script (Learning-Roadmap-specific, not part of the shared core — see
   that section's "not every consumer uses every piece") implements:
   - **Two views, one dataset**: a Build Order tab (sorted by `built_at`, unchanged from L2) and a
     Learn Order tab — a topological sort computed **client-side, at render time**, over the
     `prerequisites` edges already in the inlined JSON (Kahn's algorithm: repeatedly take a node with no
     unsatisfied prerequisite, stable-tie-broken by Build Order position). This sort is never
     precomputed into `roadmap_graph.json` — ordering is a rendering concern, this agent's index-building
     job is only to hand over the raw edges correctly.
   - **Cycle/orphan handling, independent of step 4's log.** Any node whose prerequisites never fully
     resolve during the topological sort (a cycle) — or that lists a `prerequisites` ID absent from the
     node set entirely (an orphan) — falls back to its Build Order position within the Learn Order view,
     with a visible badge on its card. This is computed fresh from the graph by the renderer itself, not
     read from a flag this agent set — the renderer never silently drops a concept even if this agent's
     own detection in step 4 were somehow wrong or stale.
   - **`localStorage` "mark reviewed."** A checkbox on each card, persisted under a page-scoped
     `localStorage` key, purely for the developer's own tracking of what they've re-studied — never
     synced anywhere (Principle 30's "local-only by default"). A "Reviewed: N / total" count in the
     header reads the same store.
   - Category/difficulty filters and Prev/Next navigation apply to whichever view (Build or Learn Order)
     is active, unchanged from L2.
8. **Log coverage gaps.** Any document in the required-frontmatter list (§ Inputs above) that has none:
   append to `identified_gaps.md` — `Category: Learning, Severity: Low` — one row per missing document,
   only if not already logged (check first; never duplicate a gap row).

---

## Learn: check coverage — Steps

1. Walk the same required-frontmatter document list as step 1 above, but only check for the frontmatter
   block's presence — do not parse its contents, do not touch `roadmap_index.md`.
2. Report a table: document path → Present / Missing.
3. For every Missing row not already in `identified_gaps.md` under `Category: Learning`, append it
   (`Severity: Low`).
4. Do not rebuild the index. Report only.

---

## Index: rebuild — Steps **[v3.3]**

### Inputs

| Document tier | Files | What to extract |
|---|---|---|
| Tier 1 | Every ADR, every module `02_domain_model.md`/`03_architecture.md`, `threat_model.md`, `04_Infrastructure_Design/*.md`, `13_Legal_Requirements/concern_*.md` (when present) | `entities:` / `tags:` / `summary:` fields from the same block `Learn: rebuild` already reads `concepts:`/etc. from |
| Tier 2 | `project_context.md`; `PRD.md`/`FRD.md`/`BRD.md`; every module's `README.md`/`00_overview.md`; `security_requirements.md`/`compliance_checklist.md`; `alternatives.md` (when present) | `entities:` / `tags:` / `summary:` — the only fields these documents carry |

### Steps

1. **Scan** every document in both tiers above; parse the YAML frontmatter block where present, reading
   only `entities`/`tags`/`summary` (ignore `concepts`/etc. even if a Tier 1 document also has them —
   that's `Learn: rebuild`'s job, not this one's). Skip silently (not a gap) any document outside both
   tiers that happens to carry the block anyway.
2. **Dedupe by entity ID**, same rule as `Learn: rebuild`'s concept dedupe: the same `entities` ID
   appearing on multiple documents merges into one `entity_index.md` row listing every referencing
   document, never one row per document.
3. **Build `documents/17_Knowledge_Index/index.md`** — one table per top-level documentation section
   (00 through the highest number present in this project), columns: Document, Summary, Tags. One row
   per document that carries the block. Apply the Document Formatting Standard.
4. **Build `documents/17_Knowledge_Index/entity_index.md`** — one row per unique `entities` ID:
   columns Entity, Referenced In (every document path carrying that ID), First Introduced (the
   earliest `built_at` among Tier 1 sources for that ID, or the first Tier 2 document by path order
   if the ID never appears on a Tier 1 document).
5. **Build `documents/17_Knowledge_Index/overview.md`** — every scanned document's own `summary:`
   field, copied verbatim (never reworded, never summarized-of-the-summary), grouped by section in
   numeric order, then by path within a section.
6. **Log coverage gaps.** Any document in either tier's list that has none of `entities`/`tags`/`summary`:
   append to `identified_gaps.md` — `Category: Indexing, Severity: Low` — one row per missing document,
   only if not already logged (check first; never duplicate a gap row). This is a distinct category
   from `Learn: rebuild`'s `Category: Learning` gaps — a document can be missing one without the other.

---

## Index: check coverage — Steps **[v3.3]**

1. Walk the same Tier 1 + Tier 2 document list as `Index: rebuild`'s Inputs table, but only check
   whether `entities`/`tags`/`summary` are present — do not parse their contents, do not touch
   `17_Knowledge_Index/`.
2. Report a table: document path → Present / Missing.
3. For every Missing row not already in `identified_gaps.md` under `Category: Indexing`, append it
   (`Severity: Low`).
4. Do not rebuild the index. Report only.

---

## Rules

1. **Never runs unprompted** — every invocation is `Learn: *` or `Index: *`, issued directly by a
   human.
2. **Writes only to its two derived folders, never cross-writing.**
   `documents/16_Learning_Roadmap/roadmap_index.md`, `roadmap_graph.json`, and `render/index.html`
   (L2/D0/L3 scope, `Learn: *` only); `documents/17_Knowledge_Index/index.md`, `entity_index.md`,
   and `overview.md` (`Index: *` only, **[v3.3]**); and appends to `identified_gaps.md` from either
   mode. Never edits any source document — frontmatter belongs to the document it's on, and this
   agent only reads it.
3. **Never invents content.** If a document has no frontmatter (or lacks the specific fields a given
   mode reads), it is absent from that mode's index and logged as a coverage gap — this agent never
   guesses a concept ID, an entity, a tag, or a summary on a human's or another agent's behalf.
4. **A missing frontmatter block or field is always Low severity** (Principle 29, extended by
   Principle 38) — never escalated, never treated as blocking execution the way an unmapped FRD
   requirement is.
5. **Does not call any other agent** — reads files, writes its derived-folder outputs and
   `identified_gaps.md` rows, nothing else.

---

## Permissions

- READ: every document in the Tier 1 + Tier 2 required-frontmatter lists, plus any other project
  document for the optional-tier scan, plus `AOSDF/renderer_core/core.js` and `core.css` (inlined
  verbatim into `render/index.html` — never modified), plus `documents/16_Learning_Roadmap/concept_vocabulary.md`
  if present (`OD-8`, `AOSDF/reference/concept_vocabulary.md` — read-only, never written by this agent)
- WRITE_LOCAL: `documents/16_Learning_Roadmap/roadmap_index.md`, `roadmap_graph.json`, `render/index.html`;
  `documents/17_Knowledge_Index/index.md`, `entity_index.md`, `overview.md` **[v3.3]**;
  `identified_gaps.md` (append only)
- WRITE_REMOTE: none
- WRITE_INFRA: none
- WRITE_DATA: none
- ADMIN: none

---

## Token Efficiency Rules

- Parse only the YAML frontmatter block of each document (the fenced region between the first two `---`
  lines) — never read a document's full body unless resolving an ambiguous prerequisite reference, or
  extracting an `aosdf-diagram` fence when that document's frontmatter has `diagram: true`
- On a `Learn: check coverage` or `Index: check coverage` **[v3.3]** run, check file existence +
  frontmatter-block presence only — do not parse field contents
- Report results as the table itself, not a narrated walkthrough of each document scanned
