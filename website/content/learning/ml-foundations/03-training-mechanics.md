# Loss, parameters, and gradient descent

A model learns by changing numbers that influence its predictions. This lesson explains that loop with one small calculation. You do not need to implement an optimizer to review a model-backed feature, but you should know what was learned, what was chosen by an engineer, and why a low training error can mislead.

## A model is a function with adjustable parameters

For a simple numeric prediction, write `prediction = weight × input + bias`. The **weight** and **bias** are parameters. Training changes them. The form of the function is the model family; its capacity determines which patterns it can represent. A ticket classifier uses more features and returns scores for billing, access, and technical queues, but it follows the same idea: inputs pass through a parameterized function to produce a prediction.

The **loss** measures how wrong a prediction is on an example. For a numeric target, squared error is `(prediction − target)²`. For classification, a loss such as cross-entropy penalizes assigning low probability to the correct class. Loss is a training signal, not a complete product success metric. An average loss can hide errors on a small but important group.

## Follow one update

Suppose `input = 2`, `target = 4`, `weight = 1`, and `bias = 0`. The prediction is `2`; squared error is `4`. Holding the bias fixed, the gradient of this example's loss with respect to the weight is `2 × (prediction − target) × input = −8`. With learning rate `0.1`, one gradient step gives `new weight = 1 − 0.1 × (−8) = 1.8`. The new prediction is `3.6`; squared error is `0.16`.

This is a teaching calculation for one example, not evidence that a model generalizes. In real training, updates use many examples, and a step that improves one can hurt another. The **learning rate** is a hyperparameter chosen before or during the run. If it is too large, updates can overshoot; if too small, progress can be slow. Other hyperparameters include regularization strength and model size.

## Diagram: parameter updates and release boundary

```aosdf-diagram
Training batch ──▶ predictions ──▶ loss against labels ──▶ gradients
       ▲                                              │
       └──────────── updated parameters ◀────────────┘
                              │
                     frozen, versioned model ──▶ inference
```

The lower path matters operationally: serving should use a known model version. Retraining produces a new candidate; it does not silently alter the model used for every live request.

[Explore the full ML lifecycle diagram](/ml-foundations-lifecycle.archify.html) to see where a trained model enters evaluation and serving.

## Watch training and validation together

If training loss falls while validation loss rises, the model may be fitting details peculiar to the training set. This is **overfitting**. It can also signal a split or distribution problem, so inspect examples before changing architecture. First responses include more representative data, a simpler model, regularization, or stopping training earlier. A large model is not automatically the best baseline.

For ticket routing, begin with a keyword rule, then a simple text classifier. Track both against the same held-out tickets. A neural model is worth considering only when the simpler candidates miss a valuable pattern and the added operating cost is justified.

## Try it

1. Recalculate the worked example with learning rate `0.25`. What is the new weight and loss?
2. Draw training and validation loss curves where validation begins to rise. Mark the model version you would consider keeping.
3. List the parameters and two hyperparameters for a simple classifier. Explain which are learned from examples.

## Check your understanding

- Does a lower training loss prove that ticket routing improved for future tickets?
- What is the difference between a model parameter and a learning rate?
- Why should a retraining run create a new model version?

**Answer guide:** with learning rate `0.25`, weight becomes `3`, prediction becomes `6`, and squared error returns to `4`; the step overshot. A lower training loss proves only better fit to training examples. Parameters are updated from data; learning rate controls the update. Versioning supports comparison and rollback.

## Read further

- [Google ML Crash Course: Gradient descent](https://developers.google.com/machine-learning/crash-course/linear-regression/gradient-descent)
- [Google ML Crash Course: Overfitting](https://developers.google.com/machine-learning/crash-course/overfitting/overfitting)
