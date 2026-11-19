# Indexable document authoring — productization contract

Status: `aosdf-doc/v1` is required for new project Markdown documents in AOSDF 3.6.0. Existing projects adopt the enforcement tools explicitly; historical legacy files use a reviewed fixed-path baseline. Comms adoption is recorded in update3, without relabeling its older framework baseline.

The Markdown document is the authoritative content. Indexes, backlinks, graph edges, embeddings and chat answers are derived views tied to a source revision. No additional `llm-wiki/` directory, copied source summaries or separate entity/concept articles are required. A chat answer becomes durable knowledge only through an explicit reviewed document change.

## Metadata contract — the first section of the file

Every adopted Markdown document starts with exactly one YAML mapping between `---` delimiters at byte zero. The reference is the six-field header in the existing Comms wiki `entities/aws.md`: `title`, `type`, `tags`, `created`, `updated`, `sources`. Reuse that predictable header format on the original documents. The wiki's AWS claims and old source slugs are not current project facts or a vocabulary to copy blindly.

The required fields are `title`, `type`, `tags`, `created`, `updated`, `sources`, `document_schema`, `id`, `summary`, `entities`. Recommended order is the wiki's six named fields followed by `document_schema`, `id`, `summary`, `entities`. Delimiters are not metadata fields. `owner` and `status` are optional and must never be guessed during formatting.

| Field | Type and exact rule |
| --- | --- |
| `title` | Nonempty string; preserve an existing value. Otherwise use the first real H1 outside code fences; filename fallback is recorded as inferred. |
| `type` | Nonempty document-kind string, independent of task status. Preferred kinds: context, requirements, design, decision, policy, plan, milestone, evidence, runbook, reference, index, prompt, template, source, entity, concept, analysis, session, overview. Preserve existing project kinds such as pitch-report/pitch-layout and record path-based classification as inferred. |
| `tags` | String list; preserve existing tags. Use `[]` if none are declared; do not invent a taxonomy during a format-only pass. |
| `created` | Existing declared ISO date/date-time, or explicit YAML `null` when unknown. Filesystem birth/mtime, Git introduction and migration date are not proof of original authorship date. |
| `updated` | Existing declared content-update date/date-time, or `null` when unknown. A metadata-only edit does not pretend the content was revised on the migration date. |
| `sources` | String list of declared supporting document IDs, resolvable document-relative paths/anchors or external URLs. Preserve legacy identifiers; report unresolved ones. `[]` means no sources declared, not no evidence exists. Ordinary navigation links are not automatically evidence. |
| `document_schema` | Exact string `aosdf-doc/v1`. Schema version is separate from framework/product/package version. |
| `id` | Nonempty stable document identity. Preserve on rename, move, retitle and content edits. Initial migration may assign UUIDv5 from stable project identity + original relative path; record that origin and keep the assigned value thereafter. No body/content hash as the document ID. |
| `summary` | Preserve an existing summary. Otherwise extract a bounded literal prose excerpt (maximum 360 characters in the pilot tool), identifying it as an excerpt; title-only fallback is explicit. This is navigation metadata, not a verified synthesis or substitute for full content. |
| `entities` | String list of declared canonical entity IDs; preserve old values. Use `[]` for unknown, not inferred architecture/provider claims. |
| `metadata_updated` | Recommended date of the metadata maintenance, separate from content dates; pilot adds it when missing. It is not a deployment/approval date. |
| `metadata_provenance` | Recommended mapping describing origins of added values (first_h1, filename, directory_classification, body_excerpt, title_only, none_declared, unknown, project_and_original_path_uuid5). Inference is explicit, never silently promoted to an accepted fact. |
| `owner`, `status` | Optional existing author/owner and document lifecycle labels. Preserve exact legacy values; absent stays absent. Document lifecycle is not execution-plan task Status. Preferred labels for newly authored documents: draft, proposed, accepted, superseded, archived. Only an actual recorded decision can mark accepted or superseded. |
| Extension fields | Retain every existing field/value, including concepts, concept_category, difficulty, prerequisites, interview_angle, built_at, diagram, channel, version, audience, product and project-specific status/type labels. The schema permits extensions. |

Example shape for an existing prompt whose authorship dates are unknown:

```yaml
---
title: Supagram Marketing Website — Emergent Build Prompt
type: prompt
tags: []
created: null
updated: null
sources: []
document_schema: aosdf-doc/v1
id: <assigned-once-project-document-id>
summary: <existing-summary-or-recorded-body-excerpt>
entities: []
metadata_updated: 2026-11-15
metadata_provenance:
  title: first_h1
  type: directory_classification
  created: unknown
  updated: unknown
  summary: body_excerpt
---
```

Use lowercase canonical entity IDs plus optional `aliases` for spelling variants. Do not merge entities only because an LLM suggests it. Optional `related` relations use `{type: depends_on|implements|evidences|contradicts|relates_to, target: <document-id>}`; `supersedes` contains stable IDs with an actual owner decision behind them. Missing evidence remains unknown. Sensitive-file rules and access policies are server-controlled; frontmatter cannot grant access.

YAML duplicate keys, unclosed delimiters, non-mapping headers, invalid dates, malformed list fields and duplicate document IDs fail validation. Do not silently “repair” them by dropping values. Preserve comments and extension fields during migration; unsupported flow/merge/anchor layouts need explicit handling, not a lossy rewrite. YAML ordering is presentation; it has no authority semantics.

Machine-readable schema: [document-metadata.schema.json](schemas/document-metadata.schema.json). The reusable [formatter/checker](../tools/document_metadata.py) validates the same required fields, preserves original metadata values and verifies exact body hashes against a migration manifest. It uses PyYAML pinned in `tools/requirements-metadata.txt`; importing or checking does not mutate documents.

## Format-only migration boundary

This metadata pass changes only the first YAML section. Everything after the closing delimiter is byte-identical to the original body; documents without frontmatter retain their entire original content as that body. It does not normalize tables, headings, prose, code fences, links, decisions, requirements or task records. The body-structure guidance below applies to future authoring or a separately authorized body-format task.

Inventory every original path and original whole-file/body hash before writes; keep recoverable originals and existing working-tree edits. Verify existing YAML values/comments, unique IDs, dates/lists and a byte-idempotent second pass. Invalid/unsupported inputs are reported and left unchanged. Record exact changed/protected/error paths and counts; “all docs migrated” is false when exceptions remain.

Frozen payloads, accepted artifacts, runtime coordination/claim/round records, archived history and generated outputs stay untouched. When a current provenance/source/diagram consumer pins source bytes, preserve the file and provide source-hash-bound proposed metadata in a migration manifest until that consumer is explicitly reconciled. Historical run/baseline snapshots remain truthful records of old bytes; never rewrite them to imply they consumed the new revision. Merely finding a hash in an old snapshot does not make a maintained source permanently immutable. Record before/after hashes and distinguish historical observations from unresolved consumers; C13 still applies to every changed byte.

Duplicates and contradictions are review findings only. Do not delete, merge, move, retitle, mark superseded or choose one conflicting document as truth without the user's specific consent. Keep exact duplicate-body groups separate from same-title candidates and explicit conflicting/supersession statements; title similarity alone proves neither duplication nor contradiction. List the actual paths and evidence, with no claim that semantic conflict detection is complete.

## Body structure by purpose

Use one H1, meaningful H2/H3 headings and stable explicit anchors for contracts cited by automation. Requirements carry stable requirement IDs, actor/trigger, expected behavior, negative/failure cases and measurable acceptance. Designs carry context, inputs/outputs, invariants, boundaries, failure behavior, alternatives, evidence and rollback. Decisions carry date/owner, decision, rationale, alternatives, consequences and source links. Task plans carry objective/owned paths, approach, risks, binary validation, rollback, initial reviewer identity/verdict/revision and factual As-built. Runbooks carry prerequisites, ordered steps, expected output, failure/rollback and environment. These are purpose-specific sections, not a mandatory giant template for every small note.

Use normal relative Markdown links so MkDocs and Git viewers resolve them. Derive backlinks rather than manually editing every incoming document. Catalog a source once by stable ID and path. Keep terms and invariants in their owning document; other documents link to them. Tables need headings and units; code fences name their language; diagrams have a text explanation; images have alt text. Distinguish requirement/proposal/accepted design/as-built and Dev/Staging/Prod evidence. Never state deployed from source-only evidence.

## Wiki practices translated into the documents

| Existing wiki practice         | Native document equivalent                                                                 |
| ------------------------------ | ------------------------------------------------------------------------------------------ |
| `WIKI.md` rules                | This authoring contract plus project workflow policy                                       |
| Source catalog/index           | `17_Knowledge_Index/index.md` generated from metadata and paths                            |
| Entity/concept pages           | Entity/tag indexes linking to owning document sections                                     |
| Bidirectional links            | Derived forward/backlink graph from Markdown and typed relations                           |
| Overview/synthesis             | Existing project-context document; any synthesis is a cited, revision-bound generated view |
| Contradiction analysis         | Findings referring to competing source sections; owner resolves in an ADR/document         |
| Append-only log/session memory | Git history, ADRs and existing task/context/accepted receipts                              |
| Saved query answer             | Optional reviewed change to an existing owning document, never automatic truth             |

## Derivation and migration

Manifest fields: schema version, project/document-root identity, source commit or local content-tree hash, parser version, document count, coverage/errors/exclusions, generation ID/time. Each entry has stable ID/path/title/type/lifecycle/owner/summary/entities/tags/relations, normalized headings/anchors and source SHA-256. Generated rows never own task status. Caches can become stale: compare source revision at read time and show mismatch/unknown; never claim always-current merely because content is derived.

Start with a read-only inventory and duplicate-ID/link/metadata report. Backfill only metadata and safe anchors, preserving decisions, task IDs, table status, accepted receipts and historical bytes. Exempt hashed/accepted evidence from rewriting; index it using immutable attachment manifests. Legacy files retain `entities/tags/summary` compatibility while the report tracks richer-schema coverage. Move no files in the first pass; retain redirect maps for later moves. Require strict new-schema checks only on new/migrated documents until coverage is approved. Roll back by restoring source changes and rebuilding disposable indexes. Per-project adoption is explicit; a framework root update does not migrate products.

Build/check indexes only through existing human-triggered commands. An opt-in hosted indexing job can be proposed separately, with revision fences, access policy and a registered implementation task; existing local commands do not silently become background synchronization.

## Required metadata for every new document — 2026-11-16

All newly created Markdown files under a project's `docs/documents/` must use `aosdf-doc/v1` from creation, including plans, evidence, generated Markdown, agent instructions and new files inside archive/run directories. Existing files with adopted metadata must retain it. There are no directory exemptions for new Markdown. Non-Markdown assets retain their native format. Existing legacy files are listed explicitly in a reviewed `docs-repo/.aosdf/document-metadata-legacy.json`; this fixed list is not a license to add new exceptions or rewrite immutable evidence. Remove an individual exemption when its migration is approved. Do not regenerate or expand the baseline to make a failed check pass.

Use the installed `tools/create_document.py` with an actual title, type, summary and body-only Markdown. It assigns a stable project/path identity, records the known new-file creation date in UTC and preserves body bytes. Never copy a template's document ID: templates have their own identities; each instantiated document needs a new one. Preserve assigned IDs on moves/edits. Manual authors and generators may emit the same required header directly, then run the gate. Unknown dates in historical sources remain null; writing a new wrapper never proves the date of copied historical content.

Before handoff, run `python tools/check_document_metadata.py --root docs/documents --legacy-baseline .aosdf/document-metadata-legacy.json` from the documentation repository. Missing/invalid metadata, copied IDs, placeholder IDs and symlink sources fail. The MkDocs pre-build hook runs this same read-only gate and aborts before rendering if it fails. Normal validation/builds never edit documents, assign IDs, enlarge exceptions or call an LLM. A direct filesystem editor can still save an invalid file; creation through the helper and the required handoff/build check enforce the authoring contract. This is not a filesystem watcher or an indexing service.

New projects install all metadata tools, `requirements-metadata.txt`, the schema/profile, a document template, the MkDocs hook and an **empty** legacy baseline before generating documents. Existing projects review an exact path list of pre-existing legacy files before activation. Keep adopted sources out of that list; validate before enabling the hook. Run the gate after any document-generating command, including index/learning/coordination generators, and update those generators to emit metadata when exercised. Do not silently exempt their future outputs.
