# Inference, monitoring, and review

An offline result becomes a product only when a new input can receive a timely, traceable decision and people can detect and correct failures. This lesson connects the model to a serving contract, a cautious release, and a feedback loop.

## Define the serving contract

For ticket routing, the request contains a ticket ID and the fields allowed at arrival. Validate their schema and size before inference. The response contains a proposed queue, model version, decision score, and whether automatic routing is allowed. Keep a human review path for low scores or invalid inputs. The prediction service should not acquire authority to read unrelated tickets merely because the model needs context.

Training and serving transformations must agree. If training lowercases text and serving does not, the model sees a different input representation. Record the feature schema and preprocessing version with the model artifact. Keep a known fallback, such as the original keyword rule or manual triage, available during failures.

## Diagram: serving and feedback loop

```aosdf-diagram
New ticket ──▶ schema + privacy checks ──▶ feature transform ──▶ model version
                                                                   │
                                  review queue ◀── decision gate ◀──┘
                                       │                 │
                                 human correction   approved route
                                       └────────┬────────┘
                                                ▼
                                  delayed outcomes + monitoring
```

The decision gate belongs in application code. A model proposes; the product policy decides whether to act. Corrections are evidence for later analysis, not an instruction to retrain immediately on every click.

[Explore the full ML lifecycle diagram](/ml-foundations-lifecycle.archify.html) to trace how serving follows an evaluated release decision.

## Release in controlled steps

First replay historical held-out cases through the real serving code to catch feature and serialization mistakes. Next, use a **shadow** run: make predictions on live tickets without affecting routing, then compare with the eventual human decision. A limited **canary** can route a small eligible slice automatically while the rest use the existing path. Expand only if error, latency, and review-volume limits hold. Preserve a switch that returns traffic to the baseline and retain the previous model artifact.

For the ticket example, a release note might say: “Only English billing and technical tickets with a validated input schema and a score above the chosen threshold are eligible. All others go to human triage. Stop the canary if misroutes exceed the agreed rate or p95 inference latency exceeds the budget.” The actual limits must come from the service's needs and measured baseline.

## Monitor what the product can observe

Measure request volume, validation failures, serving errors, latency, fallback use, predicted-class mix, and review volume immediately. Measure routing quality when corrected labels arrive. Changes in input or prediction distribution can suggest drift, but they do not by themselves prove that accuracy changed. Investigate with labeled examples. Segment metrics by channel and language where the samples are large enough.

Log the minimum needed for debugging: request ID, timestamp, model and feature versions, decision, and outcome reference. Set access and retention rules for ticket text. A trace should help reconstruct a decision without storing sensitive content in every log.

## Produce a release-ready design note

Your final artifact for this module should fit on one or two pages:

1. **Decision and baseline:** what changes for a user, and what currently handles it?
2. **Data contract:** prediction-time fields, label policy, exclusions, and split rationale.
3. **Candidate and evaluation:** model/version, baseline comparison, confusion matrices or error distribution, and important slices.
4. **Action policy:** threshold, human review, and forbidden automatic actions.
5. **Serving and release:** schema, latency budget, shadow/canary plan, fallback, and rollback owner.
6. **Monitoring:** immediate service signals, delayed quality signals, and a correction review cadence.

If any part cannot be stated, keep the existing process while you gather evidence. A more capable model does not remove the need for a clear decision and an observable release.

## Try it

Draft the six-part note for the ticket example or another low-risk feature. Identify one signal that appears immediately and one that appears only after human review. Write the exact action an operator can take if the model begins misrouting tickets.

## Check your understanding

- Why is a shadow run useful even after offline evaluation?
- Can a shift in predicted classes prove that quality has declined?
- What must be versioned to explain a particular production prediction?

**Answer guide:** shadowing exercises the live input and serving path without changing user outcomes; distribution shift is a warning, not a quality label; retain the model, feature transformation, input schema, and decision policy versions. Roll back to the baseline if the release gate fails.

## Read further

- [Google ML Crash Course: Monitoring ML systems](https://developers.google.com/machine-learning/crash-course/production-ml-systems/monitoring)
- [Google ML Crash Course: Production ML systems](https://developers.google.com/machine-learning/crash-course/production-ml-systems)
