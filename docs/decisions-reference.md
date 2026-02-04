# Decisions Reference

This guide helps identify what counts as a "decision" in ASP. The goal is to capture **scientifically meaningful choices** — things that could affect your conclusions or that a reviewer might question.

## The Core Question

Ask: **"If I made a different choice here, could it change my scientific conclusions?"**

If yes → it's probably a decision.
If no → it's probably an implementation detail.

## What IS a Decision

### Method Choices
Choices between different algorithms, statistical approaches, or analytical techniques.

| Example | Why it's a decision |
|---------|-------------------|
| Linear regression vs. random forest | Different model families make different assumptions |
| Frequentist vs. Bayesian inference | Fundamentally different statistical frameworks |
| K-means vs. hierarchical clustering | Different clustering assumptions |
| FFT vs. wavelet transform | Different signal representations |
| Cross-validation vs. holdout | Different validation strategies |

### Parameter Choices (with scientific meaning)
Hyperparameters that encode assumptions about the data or problem.

| Example | Why it's a decision |
|---------|-------------------|
| Prior distribution choice | Encodes scientific beliefs |
| Significance threshold (α = 0.05 vs 0.01) | Affects what counts as "significant" |
| Number of clusters (k) | Assumes structure in data |
| Regularization strength | Trades off bias vs. variance |
| Kernel bandwidth | Affects smoothness assumptions |

### Data Choices
Choices about how to handle, transform, or subset data.

| Example | Why it's a decision |
|---------|-------------------|
| Normalization method (z-score vs. min-max) | Affects relative feature importance |
| Missing data strategy (impute vs. drop) | Can bias results |
| Outlier handling (winsorize vs. remove) | Affects robustness |
| Feature selection method | Determines what information is used |
| Train/test split strategy | Affects generalization estimates |

### Model Architecture
Structural choices in models or pipelines.

| Example | Why it's a decision |
|---------|-------------------|
| Network depth/width | Capacity vs. overfitting tradeoff |
| Attention mechanism type | Different inductive biases |
| Loss function choice | What the model optimizes for |
| Ensemble method | How predictions are combined |

## What is NOT a Decision

### Implementation Details
Choices that don't affect scientific conclusions.

| Example | Why it's not a decision |
|---------|------------------------|
| Python vs. R | Same algorithm, same results |
| NumPy vs. JAX | Performance difference, not scientific |
| Logging verbosity | Doesn't affect analysis |
| File format (CSV vs. Parquet) | Data representation, not content |
| Variable naming | Code style |

### Fixed Requirements
Things that aren't actually choices.

| Example | Why it's not a decision |
|---------|------------------------|
| Using the provided dataset | Not a choice — it's the input |
| Required output format | Specified by stakeholder |
| Compliance requirements | Externally mandated |

### Performance Optimizations
Speed/memory tradeoffs that don't change results.

| Example | Why it's not a decision |
|---------|------------------------|
| Batch size (usually) | Affects training speed, not final model |
| GPU vs. CPU | Same computation |
| Caching strategy | Performance only |
| Parallelization | Same results, faster |

**Exception**: Batch size CAN be a decision if it affects convergence or generalization in your specific case.

### Obvious Choices
When there's only one reasonable option.

| Example | Why it's not a decision |
|---------|------------------------|
| Using log scale for data spanning 6 orders of magnitude | Only sensible choice |
| Removing duplicate rows | Standard data hygiene |
| Using established constants | Not a choice |

## Gray Areas

Some choices are context-dependent:

### Random Seeds
- **Not a decision** if you're averaging over multiple seeds
- **Is a decision** if results are seed-dependent and you're reporting one run

### Learning Rate
- **Not a decision** if using standard adaptive optimizers (Adam, etc.)
- **Is a decision** if it significantly affects convergence or final performance

### Data Augmentation
- **Is a decision** if it encodes domain assumptions (rotation invariance, etc.)
- **Not a decision** if it's standard practice with no alternatives

### Threshold Choices
- **Is a decision** if the threshold has scientific meaning (p-value cutoff)
- **Not a decision** if it's arbitrary and results are robust to changes

## Decision Importance Scale

ASP uses a 1-5 importance scale:

| Level | Meaning | Example |
|-------|---------|---------|
| 1 | Critical — changes conclusions | Statistical framework choice |
| 2 | High — affects key results | Model family selection |
| 3 | Medium — affects some results | Preprocessing method |
| 4 | Low — minor effects | Specific hyperparameters |
| 5 | Minimal — robustness check | Numerical precision |

## When in Doubt

1. **Include it** — it's easier to remove decisions than to add them later
2. **Ask**: "Would a reviewer question this choice?"
3. **Ask**: "Are there papers comparing these alternatives?"
4. **Ask**: "Would I want to try different options in a multiverse analysis?"

If any answer is "yes," it's probably a decision.

## Examples by Domain

### Machine Learning
- Model architecture ✓
- Optimizer choice ✓ (if non-standard)
- Learning rate schedule ✓
- Batch size ✗ (usually)
- Random seed ✗ (usually)
- Early stopping patience ~

### Statistics
- Test choice (t-test vs. Mann-Whitney) ✓
- Multiple comparison correction ✓
- Confidence level ✓
- Sample size calculation method ✓
- Rounding precision ✗

### Signal Processing
- Filter type ✓
- Window function ✓
- Sampling rate ✗ (if fixed by hardware)
- FFT size ~ (depends on context)

### Simulation
- Physics model ✓
- Numerical integrator ✓
- Time step size ✓ (if affects accuracy)
- Random number generator ✗
- Output frequency ✗
