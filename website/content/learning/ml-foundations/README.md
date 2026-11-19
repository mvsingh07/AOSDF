# ML foundations

Machine learning (ML) is a way to make predictions by learning patterns from examples. A traditional program follows rules written by a developer; an ML model uses patterns it learned from data to make a prediction about a new case. This module begins with that idea, then shows how to prepare examples, test whether predictions are useful, and operate a model safely. You do not need a deep-learning framework or advanced calculus.

## Start here: what is machine learning?

Suppose a support team has thousands of past tickets labeled **billing**, **access**, or **technical**. A model can learn from those labeled tickets and suggest a category for a new ticket. That suggestion is a **prediction**. The past tickets are **training data**; the ticket's words and available metadata are **features**; the correct category is a **label**. A person or simple rule can still review the result.

ML is useful when the pattern is too varied to express as a small set of maintainable rules and you can check the outcome. It is a poor replacement for a fixed policy such as “only the account owner may download a file.” Experienced readers should use the first lesson to check the problem definition and baseline before moving to data quality and evaluation.

## Who this is for

People new to ML and software engineers building or reviewing a model-backed feature. The first lesson defines the essential terms. Basic programming and API knowledge help with the later serving examples; you can work through the early exercises with a spreadsheet or a small script.

## What you will be able to do

- Turn a vague request into a prediction target, available inputs, and a non-ML baseline.
- Distinguish features from labels and training from inference.
- Choose a split that tests the way the model will be used, and recognize data leakage.
- Explain what loss, parameters, hyperparameters, and gradient descent do.
- Read a confusion matrix, choose a threshold from error costs, and plan a safe serving path.

## Learning approach

Use one public example throughout: **route incoming support tickets** to a billing, access, or technical queue. Each ticket has text and metadata. Historical tickets have a final queue assigned by a human. A model may predict a queue, but a person can correct it. The example is deliberately small so you can reason about the complete system before adding a complex model.

Read in order. After each lesson, complete its **Try it** section before opening the next page. Keep one short design note with your target, data contract, baseline, evaluation set, threshold, and rollout decision. The note is the module's final artifact.

## Diagram: the complete learning path

This workflow joins the five lessons: define a decision and baseline, prepare examples, reserve a future-like holdout, train, evaluate error costs, and serve a monitored decision. Use it as a map while reading; each lesson also contains a smaller diagram of its own step. Open the diagram in a separate tab to inspect its paths and export it.

<!-- ML_LIFECYCLE_DIAGRAM -->

## Lesson index

| Order | Lesson | Question it answers |
| --- | --- | --- |
| 1 | [What machine learning solves](/learn/ai-engineer-fde/ml-foundations/what-ml-solves) | When is learning from examples better than explicit rules? |
| 2 | [Data, labels, and trustworthy splits](/learn/ai-engineer-fde/ml-foundations/data-and-splits) | Will the evaluation represent future use? |
| 3 | [Loss, parameters, and gradient descent](/learn/ai-engineer-fde/ml-foundations/training-mechanics) | What changes when a model learns? |
| 4 | [Evaluation and decision thresholds](/learn/ai-engineer-fde/ml-foundations/evaluation) | Which errors are acceptable for this product? |
| 5 | [Inference, monitoring, and review](/learn/ai-engineer-fde/ml-foundations/inference-and-monitoring) | How does a tested model become a safe feature? |

## Completion check

You are ready to move on when you can explain your feature without a model name: **input at prediction time → predicted output → baseline → held-out evaluation → human or automatic action → monitoring and rollback**. If any arrow is vague, return to the relevant lesson. More model complexity will not repair a missing data or decision contract.

## Primary references

- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course/) for the core ML concepts and exercises.
- [Google's production ML systems module](https://developers.google.com/machine-learning/crash-course/production-ml-systems) for the boundary between an offline model and a running product.
