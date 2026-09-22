# Concept Vocabulary Schema
# AOSDF v3.0 — Track L (Learning), resolves OD-8
# Read this before `concept_indexer_agent` runs its collision-check step, or before hand-authoring
# a project's own `documents/16_Learning_Roadmap/concept_vocabulary.md`.

---

## Why This Exists

Nothing stops two agents (or two humans, on two different days) from tagging the same idea under two
different concept IDs — `cache-invalidation` on one ADR, `cache-invalidation-strategy` on another.
Left alone, `roadmap_index.md`/`roadmap_graph.json` end up with two rows for one real concept, and
Track L's Learn Order view treats them as unrelated. This was flagged from the start (`evolution.md`
Sec 12.3, `OD-8`) as a real but non-urgent problem — "worth a lightweight canonical concept list...
once a project has enough concepts for near-duplicates to become a real problem," explicitly not a
launch blocker.

It stayed open and unbuilt until Pillar C (`aosdf_expansion_scope_2.md` §6 — blending a project's own
concepts with a second, independently-authored corpus: the framework's `study_material/` baseline or a
per-project upload) turned it from "eventually worth doing" into a hard prerequisite: merging concept
IDs from a *second, independently-named* source **will** produce near-duplicates on day one, not
eventually. `L5` resolves `OD-8` and builds this now, ahead of `L6`/`L7` needing it.

**Deliberately not solved by this document:** automatic semantic deduplication. Deciding whether
`cache-invalidation` and `cache-invalidation-strategy` are the same concept is a human judgment call —
`concept_indexer_agent` flags a *suspected* collision (see §3), it never merges two IDs on its own
(Principle 29 — the agent never invents or decides content on a human's behalf).

---

## 1. Where It Lives

`documents/16_Learning_Roadmap/concept_vocabulary.md` — one per project, **human-maintained**, sibling
to `roadmap_index.md`. Unlike `roadmap_index.md`, `concept_indexer_agent` never writes this file —
only reads it, if present. A project with no near-duplicate problem yet simply has no such file; nothing
creates one automatically (not scaffolding — this is curated content, and an empty vocabulary file
would carry zero information).

---

## 2. Format

A flat table, one row per canonical concept ID:

| Canonical ID | Label | Category | Aliases | Notes |
| --- | --- | --- | --- | --- |
| `cache-invalidation` | Cache Invalidation | Architecture | `cache-invalidation-strategy`, `cache-invalidation-approach` | Merged 2026-09-05 — both aliases were the same idea tagged from two different ADRs |

| Field | Purpose | Must Never |
| --- | --- | --- |
| `Canonical ID` | The concept ID every source (frontmatter, `study_material/`, uploaded reference material) should converge on | Change once referenced — same stability rule as any other concept ID already in `roadmap_graph.json` |
| `Label` | Human-readable name, for the vocabulary file's own readability only | Appear anywhere in generated output — `roadmap_index.md`/`roadmap_graph.json` always show the concept's own frontmatter-authored label, never this one |
| `Category` | For the human maintaining this file to group related entries — informational only | Be parsed or relied on by `concept_indexer_agent` |
| `Aliases` | Every other ID string that has actually appeared in a document's frontmatter and means the same thing as the canonical ID | Include an ID that hasn't actually been seen in the wild — this file only records real collisions found, never speculative ones |
| `Notes` | Free text — when/why the alias was added | — |

---

## 3. How `concept_indexer_agent` Uses This (the collision-check step)

During `Learn: rebuild`, after step 2's exact-ID dedupe and before step 3's prerequisite resolution:

1. If `concept_vocabulary.md` doesn't exist, skip this step entirely — same as any other optional file,
   not a gap, nothing to report.
2. If it exists, for every concept ID found in this scan:
   - **Exact alias match** (normalized: lowercase, hyphens/underscores collapsed to one separator) —
     silently resolve to the canonical ID before building `roadmap_index.md`/`roadmap_graph.json`. This
     is an explicit human instruction already recorded in the file, not a guess.
   - **No match, but a mechanical near-duplicate signal** — the new ID's hyphen-separated word set is a
     strict subset or superset of an existing canonical ID's word set (the exact `cache-invalidation` /
     `cache-invalidation-strategy` shape). Flag it — never auto-resolve: add `Notes`:
     `possible duplicate of <canonical-id> — see concept_vocabulary.md`, and log to
     `identified_gaps.md` (`Category: Learning`, `Severity: Low`, only if not already logged for this
     pair). A human decides whether to add it as a real alias.
   - **No match, no near-duplicate signal** — nothing to do. Most IDs never touch this file at all; it
     only exists to catch the cases actually worth a human's attention.
3. This check is deliberately mechanical (normalized string/word-set comparison), not a semantic or
   LLM-based similarity check — cheap, deterministic, explainable in the flagged Note, and consistent
   with this agent's existing Token Efficiency Rules. It will miss real near-duplicates that don't share
   words (`ratelimit` vs `throttling`) — that's an accepted gap, not a bug: this document's whole
   purpose is catching the mechanical case (the same words, reordered or extended), not solving general
   concept deduplication.

---

## 4. `study_material`/Uploaded-Material Merge Mode (`L6`/`L7`, forward reference)

When `concept_indexer_agent` gains its merge mode (`aosdf_expansion_scope_2.md` §6), every ID sourced
from `AOSDF/study_material/` or a project's own `documents/16_Learning_Roadmap/reference_material/`
upload goes through the exact same check in §3 above — merge mode is not a second code path, it's the
same collision check running over a larger combined ID set (project frontmatter + baseline + uploads).
This is why `L5` (this document) is a hard prerequisite of `L6`/`L7`, not a nice-to-have done in
parallel: without it, blending a second corpus's ID vocabulary in has no collision detection at all.
