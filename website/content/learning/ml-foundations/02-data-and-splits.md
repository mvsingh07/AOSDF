# Data, labels, and trustworthy splits

A model can look impressive in a test and fail in production because the test did not represent future use. This lesson treats the dataset as a product contract: what was known, how the answer was recorded, and how unseen examples will differ.

## Define one example precisely

For ticket routing, one **example** is the ticket as it looked when it arrived. Its **features** may be the subject, body, language, and product area. Its **label** is the final queue chosen after review. A field such as “team that solved it” is not an input feature if it is only created after routing. A feature is useful only when it exists, with the same meaning, at inference time.

Labels can be noisy. A ticket may be transferred among teams, or an agent may select a convenient category rather than the best one. Write a label policy: use the final resolving queue, the first accepted queue, or a reviewed category? These choices define different learning problems. Sample and audit labels before choosing a model.

## Split for the future you expect

Use a **training set** to fit parameters, a **validation set** to compare versions or thresholds, and a **test set** for a final check after choices are made. Repeatedly tuning against the test set turns it into another validation set. Keep it separate until the candidate and decision rule are fixed.

A random row split is not always appropriate. If many tickets from the same customer or incident have near-identical text, copies in train and test make the test easier than future unseen customers. If product vocabulary changes over time, a later time window is more realistic than a random sample from the same period. The split unit should match the expected generalization claim.

## Diagram: preparing evidence for evaluation

```aosdf-diagram
Raw tickets ──▶ deduplicate / audit labels ──▶ group or time split
                                                  ├──▶ training: fit
                                                  ├──▶ validation: choose
                                                  └──▶ test: final estimate
```

The diagram separates **data cleaning** from **model selection**. A clean split is not a substitute for representative data; the test distribution should still resemble the people and requests the feature will serve.

[Explore the full ML lifecycle diagram](/ml-foundations-lifecycle.archify.html) to follow the data from the decision through the held-out evaluation.

## Recognize leakage

**Target leakage** occurs when a feature contains the answer or information unavailable at prediction time. In our example, including “assigned team after escalation” may make accuracy look extraordinary. **Duplicate leakage** occurs when the same case, or near-identical copies, appear across splits. **Process leakage** can arise when labels and features were both influenced by a prior routing rule; the model may simply learn that rule's historical bias.

Build a small data card before training:

| Field | Question to record |
| --- | --- |
| Source and consent | Where did these records come from, and may they be used for this purpose? |
| Prediction-time availability | Is this field present before routing? |
| Missingness | Which users or channels lack it? |
| Label policy | Who assigned the answer, and can it be wrong? |
| Split unit | Customer, incident, time, or individual ticket? |
| Retention | When should raw text and derived features be deleted? |

## Worked split

Suppose the available dataset contains 20,000 tickets from January through June. A defensible first experiment might train on January–April, choose settings on May, and test once on June. If a large incident generated hundreds of nearly identical tickets across those months, group the incident so related examples cannot appear on both sides of a split. Report the size and class distribution of every set; a tiny access-support class may need separate error analysis.

## Try it

Take ten representative records and mark every candidate feature as **available at prediction**, **created later**, or **uncertain**. Draft a label policy. Choose a split strategy and write one sentence explaining the future situation it tests. List two ways the measured score could still overstate production quality.

## Check your understanding

- Why is “the team that resolved the ticket” dangerous as an input feature?
- When is a time-based or grouped split preferable to a random row split?
- What happens if you compare model versions on the test set every day?

**Answer guide:** the feature may only exist after the prediction; grouped or time splits test unseen entities or future changes; repeated test use leaks selection into the final estimate.

## Read further

- [Google ML Crash Course: Dividing datasets](https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets)
- [Google ML Crash Course: Overfitting](https://developers.google.com/machine-learning/crash-course/overfitting/overfitting)
