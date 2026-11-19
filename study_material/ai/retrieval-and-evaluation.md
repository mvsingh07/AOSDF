---
concepts: [retrieval-augmented-generation, retrieval-authorization, ai-evaluation]
concept_category: AI Engineering
difficulty: intermediate
prerequisites: [authentication, authorization]
interview_angle: >
  Explain how to prove that an answer is grounded and why a semantic match from a forbidden
  document must be filtered before the model sees it.
built_at: framework-learning-roadmap
diagram: true
---

# Retrieval, Grounding, and Evaluation

## Definition

Retrieval-augmented generation (RAG) fetches relevant source passages and supplies them as context
to a model. Embeddings can help find semantically similar passages, but similarity is not permission
or proof. Grounding means the answer's claims can be checked against cited source passages.
Evaluation uses a repeatable set of real and adversarial questions to measure retrieval, answer
quality, citation support, and safe refusal when evidence is missing.

## Example

An employee asks about a team policy. Filter indexed chunks to documents that employee may access,
retrieve relevant passages, then show the cited document and section. Include a test where the best
semantic match is confidential and must be excluded.

## Diagram

```aosdf-diagram
Question + identity ──▶ Permission filter ──▶ Retrieve passages ──▶ Model
                                                            │
                                                            ▼
                                                Answer + source citations
```

## Use It While Building

Start with a small labeled evaluation set: answerable, no-evidence, stale, and forbidden-source
questions. Keep stable source IDs so citations can open the exact passage the model used.

## Sources

- [OpenAI Retrieval Guide](https://platform.openai.com/docs/guides/retrieval)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
