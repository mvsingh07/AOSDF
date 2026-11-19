# What machine learning solves

Machine learning starts with examples. During **training**, software finds a pattern in those examples and stores it in a **model**. During **inference**, that model uses the pattern to predict an answer for a new example. This lesson defines the basic parts, then asks whether a learned model is useful for a particular decision.

## The four pieces of a first model

Imagine a ticket that says, “I cannot sign in.” We want to suggest **access** as its support queue.

| Piece | Plain meaning | Ticket example |
| --- | --- | --- |
| Example | One case used to learn or test | One past support ticket |
| Feature | Information available when predicting | Ticket text and product area |
| Label | The answer attached to a past example | Final reviewed queue: access |
| Model | A learned mapping from features to predictions | Software that suggests a queue for a new ticket |

The model is not the same as the training data, and its prediction is not automatically correct. A professional review asks whether the examples represent future tickets, whether the label is trustworthy, and what happens when a prediction is wrong. Later lessons test those questions explicitly.

## Start with the decision

Imagine an inbox of support tickets. A person currently reads each ticket and assigns it to **billing**, **access**, or **technical** support. The desired behavior is not “use AI.” It is “route routine tickets accurately enough to reduce waiting time while preserving a correction path.” That statement gives us a target, a user benefit, and a failure to watch for.

The input available **at routing time** may include the subject, message text, selected product area, and language. The final human-assigned queue is a possible label. A model predicts the label from the inputs. A rule-based alternative might route messages containing “refund” to billing and everything else to a general queue. That simple rule is the **baseline**: a comparison point that may be cheap, understandable, and already good enough.

Use a model when the pattern is too varied for maintainable rules, representative examples exist, the outcome can be checked, and the expected benefit justifies the cost of training and operating it. Prefer explicit code when the decision is a policy or invariant, such as “only an account owner may download this invoice.” Learning from examples must not replace authorization.

## The three common learning shapes

| Shape | What the examples provide | Ticket example | Output |
| --- | --- | --- | --- |
| Supervised classification | A category label for each example | Historical tickets with final queues | Billing, access, or technical |
| Supervised regression | A numeric target | Historical tickets with resolution time | Estimated hours to resolve |
| Unsupervised learning | No target label | Unlabeled ticket text | Groups of similar tickets |

“Supervised” does not mean a human watches every training step. It means the training examples carry target answers. “Unsupervised” does not mean the result needs no review. A cluster may reflect language or writing style instead of the business issue you wanted to discover.

## Training and inference are different operations

During **training**, software compares predictions with known labels and adjusts model parameters. During **inference**, a deployed model uses its current parameters to predict on a new ticket. Training can happen offline; inference is usually on the product's request or job path. The inputs available in these two environments must match. A field added after a ticket is resolved cannot be used to predict where the ticket should go when it first arrives.

## Diagram: training and inference paths

```aosdf-diagram
Historical tickets + final queues ──▶ train ──▶ versioned classifier
                                                    │
New ticket at arrival ──────────────────────────────┴──▶ predict queue
                                                          │
                                               rule / human review / correction
```

The diagram has two paths because a working application has both a way to produce a model and a way to use it. The correction path provides feedback; it does not mean that every correction should be fed back into training without review.

[Explore the full ML lifecycle diagram](/ml-foundations-lifecycle.archify.html) to see where this distinction fits in the complete workflow.

## Worked decision

Suppose 1,000 tickets are routed each day. The keyword baseline routes 700 automatically and sends 300 to a person. A proposed classifier might route 900 automatically, but the extra 200 are useful only if misrouted tickets do not create more delay or expose private data. Before collecting data, decide what error rate and review policy would make the change worthwhile.

This is why “the model is 95% accurate” is not yet an engineering answer. You still need to know the class balance, which tickets were wrong, what the baseline achieved, and what happens to a wrong prediction.

## Try it

Write a five-line feature brief for a task you know:

1. **User decision:** what will the prediction help someone do?
2. **Inputs:** what exists at the moment of prediction?
3. **Target:** what answer can past examples supply?
4. **Baseline:** what simple rule or existing process will you compare against?
5. **Failure handling:** who can correct or override an error?

If line 2 uses information only known later, the proposed feature has a data-leakage problem. If line 3 cannot be observed reliably, the model may not be measurable.

## Check your understanding

- Why is a rule for account ownership a poor candidate for machine learning?
- What changes during training that does not normally change during inference?
- Why might grouping unlabeled tickets produce a useless business result?

**Answer guide:** authorization is a deterministic policy; training adjusts parameters; unsupervised groups need to be interpreted against the actual business question.

## Read further

- [Google ML Crash Course: Introduction to ML](https://developers.google.com/machine-learning/intro-to-ml)
- [Google ML Crash Course: Classification](https://developers.google.com/machine-learning/crash-course/classification)
