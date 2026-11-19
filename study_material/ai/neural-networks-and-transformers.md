---
concepts: [neural-network, backpropagation, tokenization, self-attention, transformer]
concept_category: AI Engineering
difficulty: intermediate
prerequisites: [supervised-learning, training-vs-inference]
interview_angle: >
  Describe a forward pass, loss, and gradient update, then explain how self-attention
  uses context across tokens without claiming the model verifies facts.
built_at: framework-learning-roadmap
diagram: true
---

# Neural Networks and Transformers

## Definition

A neural layer combines inputs using learned weights and biases, then applies a nonlinear
activation. A forward pass makes a prediction; loss measures its error; backpropagation
computes gradients used to update weights. A tokenizer first maps text to token IDs. In a
Transformer, self-attention allows a token representation to incorporate information from
other positions through query, key, and value projections. The original Transformer paper
introduced this architecture; deployed language models differ in their implementation.

## Example

A ticket model sees the text "The worker sent the email because it was ready." Context can
help represent what "it" refers to. This contextual representation improves prediction, but
it does not certify that a generated answer is correct or supported by evidence.

## Diagram

```aosdf-diagram
Training:  features ──▶ layers ──▶ prediction ──▶ loss ──▶ gradients ──▶ update
Inference: text ──▶ tokens ──▶ attention layers ──▶ next-token distribution
```

## Use It While Building

Explain the training loop in plain language. For an LLM request, record token limits,
model version, output validation, and the policy gate before any side effect.

## Sources

- [Google ML Crash Course: Neural Networks](https://developers.google.com/machine-learning/crash-course/neural-networks)
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
