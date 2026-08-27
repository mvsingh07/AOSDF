# Agent: Concept Indexer
# AOSDF v2.5 — OPTIONAL
# Part of Track L (Learning). See framework.md § Learning Roadmap, § Track L Renderer Core,
# and evolution.md Sec 3-6, Sec 13.
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
> rebuild), or `Learn: open` (open `render/index.html`, or report its path if no browser can be
> launched).

---

## Role

Read-only over the whole `{project_name}-Documents/documents/` tree; write-only to
`documents/16_Learning_Roadmap/`. Parses Concept Frontmatter (framework.md § Concept Frontmatter
Standard) off every document that carries it, dedupes concept IDs across source documents, and produces
`roadmap_index.md` — a flat, human-readable table. Contains no original content of its own (Principle
28): every fact in its output traces to a `concepts:`/`interview_angle:`/etc. field already written by
the agent or human who made that document's underlying decision, at the moment they made it (Principle
29).

If regenerating the index would produce different content than what's currently on disk, the source
documents are authoritative — the index is stale, never wrong, and re-running `Learn: rebuild` fixes it.

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

---

## Pre-flight

1. Confirm `documents/16_Learning_Roadmap/` exists; create it if absent (this is scaffolding, not a
   gap — same rule `identify_missing_documents` uses for `reference/`).
2. Confirm the project has at least one document type from framework.md's required-frontmatter list. If
   none exist yet (e.g., a project still at Phase 0 with no ADRs or module docs), report "nothing to
   index yet" and stop — do not create an empty `roadmap_index.md`.

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
3. **Resolve `prerequisites`.** For each ID listed as a prerequisite, confirm it also appears as a
   `concepts:` entry somewhere in the scan. If it doesn't resolve to anything found, flag that row's
   `Notes` column: `orphaned prerequisite: <id>`. If a prerequisite chain forms a cycle, flag every node
   in the cycle: `cycle: <id> → <id> → …`. Do not drop the node — still include it in the table,
   annotated. **[L3]** Each orphan or cycle found here also gets appended to `identified_gaps.md` —
   `Category: Learning, Severity: Low` — one row per distinct orphan/cycle, only if not already logged
   (check first; never duplicate). This is the authoritative logged record; the renderer (step 6) does
   its own independent orphan/cycle check purely for display, as a second, renderer-native guarantee
   that a concept is never silently dropped — the two are allowed to be redundant with each other, never
   allowed to disagree in substance.
4. **Build `roadmap_index.md`** — one row per unique concept ID, columns: Concept, Category, Difficulty,
   Source Document(s), Built At, Notes. Sort by `built_at` (Build Order — the only ordering available
   until Learn Order's topological sort ships in L3).
   Apply the Document Formatting Standard (framework.md § Document Formatting Standard) to the table.
5. **Build `roadmap_graph.json`.** One JSON object per unique concept ID (same dedupe/orphan/cycle
   results as step 3, carried over — never re-derive them differently across the two outputs): `id`,
   `category`, `difficulty`, `prerequisites` (array of IDs, possibly empty), `built_at`, `source`
   (array of document paths), `interview_angle`, and `diagram` — the exact text of that source document's
   `aosdf-diagram` fenced block (evolution.md Sec 5) if its frontmatter has `diagram: true`, else `null`.
   Never paraphrase or reformat the diagram text — copy it verbatim, whitespace included, so it still
   matches the source file exactly.
6. **Generate `render/index.html`.** A single self-contained file, built by inlining four things
   verbatim, in this order: `AOSDF/renderer_core/core.css`, this page's own small layout CSS layered on
   top (only what's genuinely page-specific — never re-declare a rule the core already defines),
   `AOSDF/renderer_core/core.js`, and this page's own glue script (calls `AOSDFRendererCore.escapeHtml`
   / `.renderDiagramPanel`, never re-implements them). The `roadmap_graph.json` object from step 5 is
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
   - **Cycle/orphan handling, independent of step 3's log.** Any node whose prerequisites never fully
     resolve during the topological sort (a cycle) — or that lists a `prerequisites` ID absent from the
     node set entirely (an orphan) — falls back to its Build Order position within the Learn Order view,
     with a visible badge on its card. This is computed fresh from the graph by the renderer itself, not
     read from a flag this agent set — the renderer never silently drops a concept even if this agent's
     own detection in step 3 were somehow wrong or stale.
   - **`localStorage` "mark reviewed."** A checkbox on each card, persisted under a page-scoped
     `localStorage` key, purely for the developer's own tracking of what they've re-studied — never
     synced anywhere (Principle 30's "local-only by default"). A "Reviewed: N / total" count in the
     header reads the same store.
   - Category/difficulty filters and Prev/Next navigation apply to whichever view (Build or Learn Order)
     is active, unchanged from L2.
7. **Log coverage gaps.** Any document in the required-frontmatter list (§ Inputs above) that has none:
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

## Rules

1. **Never runs unprompted** — every invocation is `Learn: rebuild` or `Learn: check coverage`, issued
   directly by a human.
2. **Writes only to `documents/16_Learning_Roadmap/roadmap_index.md`, `roadmap_graph.json`, and
   `render/index.html`** (L2/D0/L3 scope) **and appends to `identified_gaps.md`**. Never edits any source
   document — frontmatter belongs to the document it's on, and this agent only reads it.
3. **Never invents concept content.** If a document has no frontmatter, it is absent from the index and
   logged as a coverage gap — this agent never guesses a concept ID or interview angle on a human's or
   another agent's behalf.
4. **A missing frontmatter block is always Low severity** (Principle 29) — never escalated, never
   treated as blocking execution the way an unmapped FRD requirement is.
5. **Does not call any other agent** — reads files, writes `roadmap_index.md` and `identified_gaps.md`
   rows, nothing else.

---

## Permissions

- READ: every document in the required-frontmatter list, plus any other project document for the
  optional-tier scan, plus `AOSDF/renderer_core/core.js` and `core.css` (inlined verbatim into
  `render/index.html` — never modified)
- WRITE_LOCAL: `documents/16_Learning_Roadmap/roadmap_index.md`, `roadmap_graph.json`, `render/index.html`,
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
- On `Learn: check coverage`, check file existence + frontmatter-block presence only — do not parse field
  contents
- Report results as the table itself, not a narrated walkthrough of each document scanned
