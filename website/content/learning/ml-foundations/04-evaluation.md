# Evaluation and decision thresholds

Evaluation asks whether a candidate improves the decision that people actually care about. A single score rarely answers that question. This lesson uses a held-out set, a confusion matrix, and an explicit action policy.

## Compare with the baseline on the same cases

Take the test set reserved in the data lesson. Run the existing keyword rule and the candidate model on exactly those tickets. Record the data version, model version, label policy, and threshold before looking at results. The comparison should include the work created by mistakes, not just the number of correct labels.

For a simple binary decision, consider “send to access support” as the positive class. On 100 held-out tickets, suppose the model produces this table:

| | Actually access | Actually another queue |
| --- | ---: | ---: |
| Predicted access | 18 true positives | 2 false positives |
| Predicted other | 7 false negatives | 73 true negatives |

**Precision** is `18 / (18 + 2) = 0.90`: of tickets sent to access, 90% belonged there. **Recall** is `18 / (18 + 7) = 0.72`: the model found 72% of access tickets. **Accuracy** is `(18 + 73) / 100 = 0.91`. Accuracy sounds high while 7 of 25 access tickets are missed. Which metric matters depends on the cost of a wrong destination. Repeat the analysis for each class in a three-queue classifier.

## A score needs a decision rule

A classifier can return a score or probability-like output. A **threshold** turns that output into an action. Raising the threshold for automatic routing generally reduces uncertain automatic decisions; it can improve precision while reducing recall. The exact tradeoff must be measured on validation data. If scores are interpreted as probabilities, check calibration before making claims such as “90% confidence means 90% chance.”

An example policy is: route automatically only when the highest class score clears a tested threshold and exceeds the second highest by a tested margin; otherwise place the ticket in a review queue. Evaluate the full policy, including review volume and delay, against the baseline. Do not tune the threshold on the final test set.

## Diagram: from held-out cases to action policy

```aosdf-diagram
Held-out cases ──▶ baseline + candidate predictions ──▶ error table
                                                       │
                       error cost + review capacity ◀──┘
                                  │
                       threshold + human review policy
                                  │
                        final untouched test check
```

[Explore the full ML lifecycle diagram](/ml-foundations-lifecycle.archify.html) to place the threshold and review policy within the release path.

## Inspect the mistakes

Break results down by queue, language, input channel, and recent time period when sample sizes allow. Read actual false positives and false negatives. A model might perform well overall because one common queue dominates while failing on a less common queue. Report group sizes alongside rates; tiny slices have high uncertainty. For numeric predictions, compare mean absolute error against a simple constant or rule baseline, then inspect the tail of large errors.

## Try it

1. Compute precision, recall, and accuracy from the table without looking at the formulas above.
2. Write the cost of one false positive and one false negative for a routing workflow. Which would you try to reduce first?
3. Specify an automatic-route rule and a review path. State which set you would use to choose its threshold and which set you would use once for the release estimate.

## Check your understanding

- Why can 91% accuracy hide a weak experience for access tickets?
- What happens to the final test estimate if you repeatedly tune a threshold against it?
- Why must a “high confidence” score be checked for calibration?

**Answer guide:** the access class has 7 misses among 25 true cases; repeated test tuning makes the test part of model selection; raw scores may not match observed frequencies. Choose the policy on validation data, then evaluate once on test data.

## Read further

- [Google ML Crash Course: Accuracy, precision, and recall](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)
- [Google ML Crash Course: Thresholds and the confusion matrix](https://developers.google.com/machine-learning/crash-course/classification/thresholding)
