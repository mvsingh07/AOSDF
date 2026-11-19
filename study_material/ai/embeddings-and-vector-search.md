---
concepts: [embeddings, vector-similarity, approximate-nearest-neighbor, metadata-filtering]
concept_category: AI Engineering
difficulty: intermediate
prerequisites: [training-vs-inference]
interview_angle: >
  Explain why vector proximity retrieves candidates but does not establish truth or access,
  and how to evaluate approximate index recall against exact search.
built_at: framework-learning-roadmap
diagram: true
---

# Embeddings and Vector Search

## Definition

An embedding model converts text into a vector. A distance measure ranks vectors by
similarity; the ranking is model-dependent and may be wrong for a task. Exact search returns
the nearest rows under that measure. Approximate indexes such as HNSW trade some recall for
speed at scale. Metadata filters constrain the eligible corpus, but approximate index
behavior under selective filters must be measured.

## Example

"Reset my password" and "I forgot my login credentials" may rank close. A similar
document from another tenant must never reach the prompt. In pgvector, compare an exact
top-k result with the HNSW result for queries from both large and small tenants; record
recall and p95 latency rather than assuming the index is always better.

## Diagram

```aosdf-diagram
Document ──▶ embedding + source ID + access label ──▶ vector index
Question + caller ──▶ allowed-source filter ──▶ nearest candidates ──▶ source check
```

## Use It While Building

Store embedding-model version and source lineage. Test access filtering, exact-versus-ANN
recall, and what happens when a source document is updated or deleted.

## Sources

- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [pgvector documentation](https://github.com/pgvector/pgvector)
