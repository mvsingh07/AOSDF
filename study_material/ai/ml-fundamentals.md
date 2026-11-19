---
concepts: [supervised-learning, unsupervised-learning, training-vs-inference, model-evaluation]
concept_category: AI Engineering
difficulty: fundamental
prerequisites: []
interview_angle: >
  Explain what the model learns from labeled examples, why inference is different from training,
  and how a baseline and held-out set reveal whether it helps users.
built_at: framework-learning-roadmap
diagram: true
---

# ML Fundamentals for a Software Engineer

## Definition

Supervised learning fits a mapping from examples with labels to predictions. Unsupervised
learning finds structure without those labels. During **training**, parameters change to reduce
a loss; during **inference**, fixed parameters produce a prediction for a new input. Features,
labels, train/validation/test splits, and the cost of different errors matter more to an
application engineer than memorizing model names.

## Example

In a support-ticket classifier, the ticket text and metadata are features; the resolved
category is the label. Compare a model to a keyword baseline on tickets from later periods
or unseen customers. If the same customer's near-duplicate tickets appear in both training
and test, a high score may reflect leakage rather than generalization.

## Diagram

```aosdf-diagram
Historical examples ──▶ Train / tune ──▶ Versioned model
                                            │
New ticket ─────────────────────────────────┴──▶ Inference ──▶ Human review / route
Held-out examples ─────────────────────────────▶ Evaluation ──▶ Release decision
```

## Use It While Building

State the prediction target, baseline, split strategy, and one costly false positive or
false negative. Inspect mistakes by input type and user group before optimizing the model.

## Sources

- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course/)
