---
concepts: [rag, document-chunking, grounded-answer, source-citation]
concept_category: AI Engineering
difficulty: intermediate
prerequisites: [embeddings, metadata-filtering, object-level-authorization]
interview_angle: >
  Walk through ingestion and serving separately, then explain when to abstain and how
  a citation is checked against the original source.
built_at: framework-learning-roadmap
diagram: true
---

# RAG Architecture and Grounded Answers

## Definition

Retrieval-augmented generation (RAG) provides relevant source passages to a model at
request time. Ingestion parses, chunks, versions, embeds, and indexes documents; serving
filters by permission, retrieves passages, assembles limited context, and generates an
answer. A grounded answer makes claims supported by those passages and links readers to
the original source. If evidence is absent or conflicting, it should say so.

## Example

For a private health-policy handbook, split by sections and retain document version,
page anchor, and access label. A user's question retrieves only authorized current chunks.
The answer cites exact sections; if no current policy supports a claim, it abstains and
offers a human-review path rather than inventing a policy.

## Diagram

```aosdf-diagram
Ingest: source ──▶ parse ──▶ chunk + version ──▶ embed ──▶ index
Serve:  user + question ──▶ permission filter ──▶ retrieve ──▶ model
                                                     └────────▶ citation check / abstain
```

## Use It While Building

Create a small evaluation set with answerable, no-evidence, stale, and forbidden-source
questions. Evaluate retrieval recall and citation support separately.

## Sources

- [OpenAI Retrieval Guide](https://platform.openai.com/docs/guides/retrieval)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
