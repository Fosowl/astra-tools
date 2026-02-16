# ASP - Agentic Science Protocol

## Overview

**ASP (Agentic Science Protocol)** is a declarative specification format for scientific analyses. It describes:

- What we want to learn (description)
- What we have to work with (inputs)
- What we want to produce (outputs)
- What choices need to be made (decisions)
- How to produce the outputs (recipes)

An ASP analysis can be executed by AI agents or human researchers. The specification says WHAT; the agent or researcher writes the code and registers recipes that produce the declared outputs.

### Architecture

ASP is the core specification layer in a three-tier architecture:

```
asp-core (this repo)
  Schema + validation (asp.yaml)
  Recipe format (containerized build rules)
  Insights + evidence verification
  Minimal CLI

asp-agent (Prism - separate repo)
  AI agent skills for writing scripts + recipes
  Claude Code / Navigator integration
  Project scaffolding

asp-ui (Spectrum - future)
  Visual editors, dashboards
```

```
┌─────────────────┐      ┌─────────────┐      ┌──────────────┐      ┌─────────┐
│ ASP Analysis    │ ───> │ Agent       │ ───> │ Scripts +    │ ───> │ Outputs │
│ (what we want)  │      │ (writes     │      │ Recipes      │      │         │
│                 │      │  code)      │      │ (how to      │      │ metrics │
│ - description   │      │             │      │  produce it) │      │ figures │
│ - inputs        │      │             │      │              │      │ tables  │
│ - outputs       │      │             │      │              │      │ data    │
│ - decisions     │      │             │      │              │      │ reports │
└─────────────────┘      └─────────────┘      └──────────────┘      └─────────┘
        ^                                                                  │
        │                                                                  │
        └──────────────── previous analyses (as inputs) ───────────────────┘

Universe (decision selections) ───> Execution Parameters
```

## The Multiverse Concept

A **universe** is one complete set of decisions -- a single path through the decision space that fully specifies an analysis. Running one universe produces outputs that address the analysis description.

The **multiverse** is the space of all valid decision combinations. Its purpose is **transparency and traceability**, not exhaustive search:

1. **Document the path taken**: Which decisions were made and why
2. **Document paths not taken**: What alternatives existed
3. **Enable exploration**: User can ask "what if we chose differently?"
4. **Check robustness**: Optionally run alternative universes to see if conclusions hold

| Approach | Purpose | Runs |
|----------|---------|------|
| **Single analysis** | Answer the research question | 1 universe |
| **Multiverse documentation** | Show all possible paths | 0 (just documentation) |
| **Robustness check** | Verify conclusions are stable | Selected universes |
| **Full enumeration** | Exhaustive comparison (rare) | All universes |

A well-specified analysis should address its research question with a **single universe**. The multiverse exists to show the researcher's choices transparently.

## Core Components

### 1. Description

A clear description of what the analysis aims to achieve. This is the research question being investigated.

The description:
- Should be specific enough to evaluate whether outputs address it
- Does not need to be machine-parseable (it's guidance for the agent and humans)
- Helps ensure the analysis stays focused

### 2. Inputs

What the analysis has to work with:

| Input Type | Description | Example |
|------------|-------------|---------|
| `data` | Raw data files | CSV, FITS, Parquet files |
| `analysis` | Results from previous analyses | Reference to another ASP analysis |

Inputs have optional fields for provenance:
- `source`: URI or path to the data source (for `data` inputs)
- `checksum`: Hash for data integrity verification (algorithm + value)
- `ref`: Reference to another ASP analysis (for `analysis` inputs)
- `ref_version`: Version of the referenced analysis
- `use_outputs`: Specific outputs to use from the referenced analysis
- `from`: Reference to a parent input or sibling output in sub-analyses

### 3. Outputs

What the analysis should produce. All outputs are declared upfront so we know what to expect.

| Output Type | Description | Example |
|-------------|-------------|---------|
| `metric` | A numeric or categorical value | Accuracy, p-value, AUC |
| `figure` | A visualization | Confusion matrix, ROC curve |
| `table` | Structured tabular data | Feature importances, comparison table |
| `data` | Processed data files | Predictions, transformed features, trained models |
| `report` | Text/document output | Summary, conclusion |

A `report` type output is special: it should address the analysis description and synthesize findings.

Outputs can declare their provenance via `from` to trace which sub-analysis produces them (e.g., `from: inference.posterior`).

### 4. Decisions

Each decision has:

- **id**: Unique identifier (unique within its analysis node)
- **label**: Human-readable name
- **type**: Category (`data`, `method`, `parameter`)
- **rationale**: Why this decision exists
- **options**: The possible choices
- **default**: (optional) The default option for baseline universes

Decision types:
- `data`: Choices about data (which dataset, how to split, what to include/exclude)
- `method`: Choices about methodology (which algorithm, which technique)
- `parameter`: Choices about parameters (hyperparameters, thresholds, settings)

Options can have:
- **constraints**: `incompatible_with`, `requires` (scoped to the same analysis node)
- **insights**: References to insight IDs that support this choice

### 5. Constraints

Options can declare constraints on other options within the same analysis node:

```yaml
decisions:
  scaling:
    options:
      minmax:
        label: "MinMaxScaler"
        incompatible_with: ["model.svm"]  # Can't use with SVM

  feature_selection:
    options:
      pca:
        label: "PCA"
        requires: ["scaling.standard"]  # PCA needs standardized data
```

**Constraint types:**
- `incompatible_with`: List of `decision.option` pairs that cannot be selected together
- `requires`: List of `decision.option` pairs that must also be selected

Constraints are scoped within an analysis node and validated when creating universes. Invalid combinations are rejected.

### 6. Recipes

Recipes are build rules that produce outputs. Each recipe declares:
- **command**: What to run (e.g., `python src/train.py`)
- **outputs**: Which output IDs this recipe produces
- **depends_on**: Recipe IDs that must complete first (forms a DAG)
- **container**: Container image override (defaults to node-level container)
- **resources**: Compute requirements (CPUs, memory, GPUs, time limit)

```yaml
container: ghcr.io/project/env@sha256:abc123   # default for all recipes

recipes:
  preprocess:
    command: python src/preprocess.py
    outputs: [cleaned_data]

  train:
    command: python src/train.py
    outputs: [trained_model]
    depends_on: [preprocess]
    container: nvidia/cuda:12.0-python3.11      # override for GPU work
    resources:
      gpus: 1
      memory: "32GB"

  evaluate:
    command: python src/evaluate.py
    outputs: [accuracy, confusion_matrix, conclusion]
    depends_on: [train]
```

**Validation rules:**
- Every declared output must be claimed by exactly one recipe
- `depends_on` references must point to valid recipe IDs within the same node
- No dependency cycles
- Recipes are optional -- an analysis without recipes is a pure specification

**Progressive complexity:**

| Stage | What you add | What you get |
|-------|-------------|--------------|
| Declaring | `asp.yaml` with outputs | "Here's what I need to produce" |
| Scripting | `src/` + `recipes:` | "Here's how to produce it" |
| Containerizing | `container:` + image | Reproducible anywhere |
| Scaling | `resources:` | Runs on HPC/cloud |

### Universe

A **universe** is a complete set of decisions across the entire analysis tree: one option selected for each decision point. The universe mirrors the analysis tree structure.

```yaml
# universes/baseline.yaml
id: baseline
description: "Default configuration using standard practices"

decisions:
  scaling: standard
  model: random_forest
  test_size: split_20
  random_seed: seed_42
```

For analyses with sub-analyses, the universe includes nested selections:

```yaml
id: baseline
description: "Standard pipeline configuration"

decisions:
  cosmology_model: flat_lcdm

analyses:
  build_mocks:
    decisions:
      noise_model: heteroscedastic
  train_network:
    decisions:
      architecture: maf
```

## Self-Similar Sub-Analyses

Analyses can decompose into sub-analyses, each with the same structure as the root. This is the key structural property: **every analysis node has the same shape**.

A node has: description, inputs, outputs, decisions, recipes, and optionally sub-analyses.

### Design Principles

1. **Self-similar**: Every level has the same structure. A sub-analysis is a valid analysis on its own.
2. **Required contract**: Sub-analyses must declare `inputs` and `outputs` — they define the node's interface.
3. **Inline or split**: Small sub-analyses live inline in the parent's `asp.yaml`. Complex sub-analyses get their own directory with their own `asp.yaml`.
4. **Scoped decisions**: Each node has its own decisions. Constraints are scoped within a node unless `parent_decisions` is used.
5. **Cross-level dependencies via `parent_decisions`**: Sub-analyses can declare which parent decisions they depend on, making those available for constraints and enabling standalone packaging.
6. **Wiring via `from`**: Sub-analysis inputs reference parent inputs or sibling outputs using the `from` field.
7. **Universe is global**: One universe covers all decisions across the entire tree.
8. **No depth limit**: Analyses can nest arbitrarily.

### Multi-Stage Analysis

```yaml
version: "1.0"
name: "SBI Cosmological Parameter Estimation"
description: |
  Use simulation-based inference to constrain cosmological
  parameters from Type Ia supernova survey data.

inputs:
  - id: survey_catalog
    type: data
    source: "sn_survey_union2.1"

outputs:
  - id: posterior_contours
    type: figure
  - id: parameter_constraints
    type: table

decisions:
  cosmology_model:
    label: "Cosmological Model"
    type: method
    default: flat_lcdm
    options:
      flat_lcdm:
        label: "Flat LCDM"
      wcdm:
        label: "wCDM"

analyses:
  build_mocks:
    description: "Generate realistic mock catalogs matching survey properties."
    parent_decisions: [cosmology_model]   # depends on parent decision
    success_criteria:
      - "Mock catalog matches observed magnitude distribution"
    inputs:
      - id: survey_data
        type: data
        from: survey_catalog          # references parent input
    outputs:
      - id: mock_catalog
        type: data
    decisions:
      noise_model:
        label: "Noise Model"
        type: method
        default: heteroscedastic
        options:
          homoscedastic:
            label: "Homoscedastic"
          heteroscedastic:
            label: "Heteroscedastic"
    recipes:
      generate:
        command: python src/generate_mocks.py
        outputs: [mock_catalog]

  train_network:
    description: "Train SBI neural network on mock catalog."
    inputs:
      - id: training_data
        type: data
        from: build_mocks.mock_catalog  # references sibling output
    outputs:
      - id: trained_model
        type: data
    decisions:
      architecture:
        label: "Network Architecture"
        type: method
        default: maf
        options:
          maf:
            label: "Masked Autoregressive Flow"
          npe:
            label: "Neural Posterior Estimation"
    recipes:
      train:
        command: python src/train.py
        outputs: [trained_model]
        resources:
          gpus: 1
          memory: "32GB"
```

## Directory Structure

The directory structure mirrors the self-similar nature of analyses. Every analysis directory has the same shape:

```
<analysis>/
  asp.yaml              # this node's specification
  insights.yaml         # this node's insights (optional)
  Containerfile         # environment definition (optional)
  src/                  # source code (any language)
  universes/            # universe definitions (root only)
    baseline.yaml
  outputs/              # materialized outputs, namespaced by universe
    <universe_id>/
      <output_id>.<ext>
  analyses/             # sub-analyses (same shape, recursive)
    <sub>/
      asp.yaml
      insights.yaml
      src/
      outputs/
        <universe_id>/
      analyses/         # can nest further
```

### Simple Analysis

```
iris-classification/
  asp.yaml
  insights.yaml
  src/
    train.py
    evaluate.py
  universes/
    baseline.yaml
    svm_focused.yaml
  outputs/
    baseline/
      accuracy.json
      confusion_matrix.png
      model_comparison.csv
    svm_focused/
      accuracy.json
      confusion_matrix.png
      model_comparison.csv
```

### Multi-Stage Analysis

```
sbi-pipeline/
  asp.yaml
  insights.yaml
  Containerfile
  universes/
    baseline.yaml
  outputs/
    baseline/
      posterior_contours.png
      parameter_constraints.csv
  analyses/
    build_mocks/
      asp.yaml                      # or inline in parent
      src/
        generate_mocks.py
      outputs/
        baseline/
          mock_catalog.parquet
    train_network/
      asp.yaml
      src/
        train.py
      outputs/
        baseline/
          trained_model.pkl
```

### Key Conventions

- **Output files are named by their output ID** from the spec, with an appropriate extension
- **Outputs are namespaced by universe ID** (`outputs/<universe_id>/`)
- **`outputs/` is gitignored** by default (generated artifacts)
- **Sub-analyses are directories** under `analyses/`, the directory name matches the analysis ID
- **Insights are scoped per node** -- each node has its own `insights.yaml`
- **`src/` is convention, not enforced** -- the recipe `command` is the authority

## Insights

Insights represent scientific knowledge extracted from literature with full traceability to source material. They use W3C Web Annotation-compliant selectors for precise evidence references.

Insights are stored in `insights.yaml` at each analysis node, scoped to that node.

### Insight Structure

```yaml
# insights.yaml
insights:
  layer_norm_stability:
    id: layer_norm_stability
    claim: "Layer normalization improves training stability compared to batch normalization."
    created_at: "2024-01-15T10:30:00Z"
    evidence:
      - id: ev1
        doi: "10.48550/arXiv.1706.03762"
        version: 7
        quote:
          type: TextQuoteSelector
          exact: "We found that layer normalization leads to faster convergence."
          prefix: "In our ablation studies, "
          suffix: " This effect was..."
        location:
          type: FragmentSelector
          page: 5
    scope: "Transformer architectures"
    confidence: 0.9
```

### Evidence Types

Evidence references papers by DOI and must include at least one content selector:

| Selector | Purpose | Required Fields |
|----------|---------|-----------------|
| `quote` (TextQuoteSelector) | Exact text from paper | `exact` (the quote) |
| `figure` (FigureSelector) | Reference to a figure | `label` (e.g., "Figure 3a") |
| `table` (TableSelector) | Reference to a table | `label` (e.g., "Table 1") |

**Quote evidence (W3C TextQuoteSelector):**
```yaml
quote:
  type: TextQuoteSelector
  exact: "The exact quoted text from the paper"
  prefix: "Context before..."    # Optional
  suffix: "Context after..."     # Optional
```

**Figure evidence (FigureSelector):**
```yaml
figure:
  type: FigureSelector
  label: "Figure 3a"
  caption: "Optional caption text for verification"
```

**Table evidence (TableSelector):**
```yaml
table:
  type: TableSelector
  label: "Table 1"
  caption: "Optional header text"
  region: "row 3, accuracy column"  # Optional: specific region
```

### Location Hints

The `location` field (W3C FragmentSelector) provides PDF location hints:

```yaml
location:
  type: FragmentSelector
  page: 5                        # 1-indexed page number
```

### arXiv Papers

For arXiv papers, use the DOI format `10.48550/arXiv.{id}` and specify the version:

```yaml
evidence:
  - id: ev1
    doi: "10.48550/arXiv.1706.03762"
    version: 7                    # Important: arXiv papers are updated
    quote:
      type: TextQuoteSelector
      exact: "Attention is all you need."
```

### Evidence Verification

The CLI can verify that quotes exist in source PDFs:

```bash
asp validate asp.yaml --verify-evidence
```

This:
1. Checks that each paper is in the local cache (`asp paper add <doi>`)
2. Searches for exact quotes in the PDF text
3. Verifies page numbers if provided
4. Caches verification results for efficiency

**Key principle**: The agent writes evidence, but validation is the gatekeeper. Fabricated quotes will fail verification.

### Evidence Lifecycle

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        PHASE 1: LITERATURE RESEARCH                      │
│                           (Agent + Web Search)                           │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Identify decisions needing justification                             │
│  2. Web search for relevant papers                                       │
│  3. Collect DOIs                                                         │
└──────────────────────────────────────────────────────────────────────────┘
                                    |
                                    v
┌──────────────────────────────────────────────────────────────────────────┐
│                        PHASE 2: PAPER ACQUISITION                        │
│                              (CLI)                                       │
├──────────────────────────────────────────────────────────────────────────┤
│  asp paper add 10.48550/arXiv.1706.03762 --version 7                     │
│  Cache: ~/.cache/asp/papers/                                             │
└──────────────────────────────────────────────────────────────────────────┘
                                    |
                                    v
┌──────────────────────────────────────────────────────────────────────────┐
│                       PHASE 3: INSIGHT EXTRACTION                        │
│                        (Agent reads PDF directly)                        │
├──────────────────────────────────────────────────────────────────────────┤
│  Agent writes insights to insights.yaml with exact quotes                │
└──────────────────────────────────────────────────────────────────────────┘
                                    |
                                    v
┌──────────────────────────────────────────────────────────────────────────┐
│                       PHASE 4: DECISION LINKING                          │
├──────────────────────────────────────────────────────────────────────────┤
│  decisions:                                                              │
│    normalization:                                                        │
│      options:                                                            │
│        layer_norm:                                                       │
│          insights:                                                       │
│            - layer_norm_insight                                           │
└──────────────────────────────────────────────────────────────────────────┘
                                    |
                                    v
┌──────────────────────────────────────────────────────────────────────────┐
│                       PHASE 5: VALIDATION                                │
│                         (CLI - Gatekeeper)                               │
├──────────────────────────────────────────────────────────────────────────┤
│  asp validate asp.yaml --verify-evidence                                 │
│  Stage 1: Schema validation                                              │
│  Stage 2: Semantic validation (references, constraints, recipes)         │
│  Stage 3: Evidence verification (quotes exist in PDFs)                   │
└──────────────────────────────────────────────────────────────────────────┘
```

## Evidence-Based Decisions

Decisions reference insights (not papers directly) to create a traceable chain:

```yaml
# insights.yaml
insights:
  minmax_study:
    id: minmax_study
    claim: "MinMax scaling improves accuracy for tree-based models by 3%."
    created_at: "2024-01-15T10:00:00Z"
    evidence:
      - id: ev1
        doi: "10.1234/scaling-study"
        quote:
          type: TextQuoteSelector
          exact: "MinMax normalization yielded a 3% improvement in accuracy for Random Forest."
        location:
          type: FragmentSelector
          page: 12
```

```yaml
# asp.yaml
decisions:
  scaling:
    options:
      minmax:
        label: "Min-Max Scaling"
        insights:
          - minmax_study            # Reference to insight ID
```

This creates a traceable chain: **decision option -> insight -> evidence -> paper (DOI)**.

## Composability

Analyses can use other analyses as inputs, enabling:

1. **Analysis pipelines**: Output of analysis A feeds into analysis B
2. **Evidence chains**: Conclusions from one study inform decisions in another
3. **Incremental research**: Build on previous work formally

```yaml
inputs:
  - id: preprocessing_study
    type: analysis
    ref: "analyses/preprocessing_comparison"
    ref_version: "v1.2"
    use_outputs: [best_method, performance_table]
```

## Versioning and Lifecycle

An analysis evolves over time. Git provides the foundation for tracking this evolution.

### The Analysis Lifecycle

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Draft  │ --> │ Evolve  │ --> │ Execute │ --> │ Iterate │ --> │Finalize │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
     |               |               |               |               |
     v               v               v               v               v
   commit         commits          run            commits          tag
   (initial)    (add decisions)  universes       (refine)        (v1.0)
```

**Key principle**: The analysis definition evolves through Git commits. Discovering a new decision point during execution is normal -- just add it and commit.

### What Git Mechanisms Map To

| Concept | Git Mechanism | When to Use |
|---------|---------------|-------------|
| **Analysis evolution** | Commits on branch | Adding/modifying decisions as you work |
| **Universe** | File (`universes/baseline.yaml`) | Different decision selections within same analysis |
| **Alternative approach** | Branch | Fundamentally different methodology |
| **Completed analysis** | Tag | Marking a milestone (submission, publication) |

### Universes vs Branches

**Universes** handle different decision selections within the same analysis. Each universe produces outputs in `outputs/<universe_id>/`, making comparison trivial:

```bash
# Different decisions, same analysis
diff outputs/baseline/ outputs/svm_focused/
```

**Branches** are for fundamentally different approaches that change the decision space itself:

```
main (classical ML)
  |
  |-- scaling, model (svm/rf), cv_strategy...
  |
  |   ── git branch deep-learning ──>
  |                                    |
  |                                    |-- adds: architecture, optimizer,
  |                                    |         learning_rate, epochs...
  |                                    |
  |                                    └── different decision space
  |
  └── continues with classical approach
```

Branches are NOT for choosing different options within the same analysis -- that's what universes are for.

### Tags: Marking Complete Analyses

```bash
git tag -a v1.0-submitted -m "Analysis as submitted to Nature Methods"
git tag -a v1.1-revision -m "Addressed reviewer comments"
git tag -a v1.1-published -m "Final published version"
```

## Example Analysis Specification

```yaml
$schema: "https://asp-spec.org/v1/schema.json"
version: "1.0"
name: "Iris Classification Study"

description: |
  Build a robust classifier for the Iris dataset that accurately
  predicts species from flower measurements, suitable for use in
  a botanical identification application.

inputs:
  - id: iris_data
    type: data
    source: "sklearn.datasets.load_iris"
    description: "Fisher's classic 150-sample, 3-class dataset"

  - id: preprocessing_study
    type: analysis
    ref: "analyses/scaling_comparison_2024"
    description: "Our previous study on scaling methods"

outputs:
  - id: accuracy
    type: metric
    description: "Classification accuracy on held-out test set"

  - id: f1_score
    type: metric
    description: "Macro-averaged F1 score"

  - id: confusion_matrix
    type: figure
    description: "Confusion matrix heatmap"

  - id: model_comparison
    type: table
    description: "Accuracy by model and preprocessing combination"

  - id: trained_output
    type: data
    description: "Best performing classifier"

  - id: conclusion
    type: report
    description: "Summary of classifier performance"

decisions:
  scaling:
    label: "Feature Scaling"
    type: method
    rationale: "Scaling affects distance-based algorithms like SVM"
    default: standard
    options:
      none:
        label: "No Scaling"
        description: "Use raw feature values"
      standard:
        label: "StandardScaler"
        description: "Z-score normalization (mean=0, std=1)"
      minmax:
        label: "MinMaxScaler"
        description: "Scale to [0, 1] range"
        incompatible_with: ["model.svm"]

  model:
    label: "Classification Model"
    type: method
    rationale: "Core algorithmic choice"
    default: random_forest
    options:
      svm:
        label: "Support Vector Machine"
        requires: ["scaling.standard"]
      random_forest:
        label: "Random Forest"
      logistic:
        label: "Logistic Regression"

  test_size:
    label: "Test Set Proportion"
    type: parameter
    rationale: "Trade-off between training data and evaluation reliability"
    default: small
    options:
      small:
        label: "20%"
      medium:
        label: "30%"

  random_seed:
    label: "Random Seed"
    type: parameter
    rationale: "For reproducibility"
    default: seed_42
    options:
      seed_42:
        label: "42"
      seed_123:
        label: "123"

recipes:
  train:
    command: python src/train.py
    outputs: [trained_output]
  evaluate:
    command: python src/evaluate.py
    outputs: [accuracy, f1_score, confusion_matrix, model_comparison, conclusion]
    depends_on: [train]
```

## CLI Commands

```bash
# Project setup
asp init my-analysis               # Create analysis scaffold
asp init my-analysis --no-git      # Skip git initialization

# Validation
asp validate asp.yaml              # Validate analysis specification
asp validate universes/baseline.yaml  # Validate universe against spec
asp validate asp.yaml --verify-evidence  # Verify evidence quotes

# Exploration
asp info                           # Show analysis summary
asp info --decisions               # Show decision details
asp viz                            # Visualize decision space (ASCII)
asp viz --format mermaid           # Mermaid diagram

# Universe management
asp universe generate --name baseline  # Generate universe from defaults
asp universe check universes/foo.yaml  # Check universe constraints

# Schema utilities
asp schema export                  # Export JSON schemas
asp schema show analysis           # Print schema to stdout

# Paper management
asp paper add <doi>                # Cache a paper
asp paper list                     # List cached papers
asp paper verify-quotes <doi>      # Verify evidence quotes
```

For full agentic scaffolding (Claude Code config, skills, HPC targets), use Prism: `prism init`.

## Schema Reference

### Analysis Schema (asp.yaml)

```yaml
$schema: "https://asp-spec.org/v1/schema.json"
version: "1.0"                      # Required: ASP spec version

name: string                        # Required: Human-readable name
description: string                 # Optional: What this analysis aims to achieve
authors: [string]                   # Optional: List of authors
tags: [string]                      # Optional: Tags for categorization

inputs:                             # Required: List of inputs
  - id: string                      # Unique identifier (^[a-z][a-z0-9_]*$)
    type: data|analysis             # Input type
    description: string             # Optional
    source: string                  # For data: URI or path
    checksum:                       # Optional: data integrity
      algorithm: sha256|sha512|md5
      value: string
    ref: string                     # For analysis: reference path
    ref_version: string             # For analysis: version
    use_outputs: [string]           # For analysis: specific outputs
    from: string                    # For sub-analyses: parent input or sibling output

outputs:                            # Required: List of outputs
  - id: string                      # Unique identifier (^[a-z][a-z0-9_]*$)
    type: metric|figure|table|data|report
    description: string             # Optional
    from: string                    # Optional: provenance from sub-analysis

decisions:                          # Map of decision IDs
  decision_id:
    label: string                   # Human-readable name
    type: data|method|parameter     # Decision category
    rationale: string               # Optional: why this decision exists
    default: option_id              # Optional: default for baseline
    options:
      option_id:
        label: string               # Human-readable name
        description: string         # Optional
        insights: [string]          # Optional: insight IDs
        incompatible_with: [string] # Optional: "decision.option" pairs
        requires: [string]          # Optional: "decision.option" pairs

insights:                           # Optional: Map of insight IDs
  insight_id:
    id: string
    claim: string
    created_at: datetime
    evidence:
      - id: string
        doi: string
        version: int                # Optional: for arXiv
        quote: TextQuoteSelector    # At least one of: quote, figure, table
        figure: FigureSelector
        table: TableSelector
        location: FragmentSelector  # Optional: PDF location hint
    confidence: float               # Optional: 0-1
    derived: bool                   # Optional: true if synthesized
    scope: string                   # Optional: applicability
    tags: [string]                  # Optional
    notes: string                   # Optional

container: string                   # Optional: default container image

recipes:                            # Optional: Map of recipe IDs
  recipe_id:
    command: string                 # Required: command to execute
    outputs: [string]               # Required: output IDs this produces
    container: string               # Optional: container override
    depends_on: [string]            # Optional: recipe IDs (forms DAG)
    resources:                      # Optional: compute requirements
      cpus: int
      memory: string               # e.g., "8GB"
      gpus: int
      time_limit: string           # e.g., "2h"

analyses:                           # Optional: Map of sub-analysis IDs
  analysis_id:                      # Same structure as root (recursive)
    description: string
    parent_decisions: [string]      # Optional: parent decision IDs this node depends on
    inputs: [...]                   # Required for sub-analyses
    outputs: [...]                  # Required for sub-analyses
    decisions: {...}
    recipes: {...}
    analyses: {...}                 # Can nest further
```

### Universe Schema (universes/*.yaml)

```yaml
$schema: "https://asp-spec.org/v1/universe.schema.json"

id: string                          # Unique identifier (^[a-z][a-z0-9_-]*$)
description: string                 # What this universe represents

decisions:                          # Root-level decision selections
  scaling: standard
  model: random_forest

analyses:                           # Sub-analysis selections (mirrors tree)
  build_mocks:
    decisions:
      noise_model: heteroscedastic
  train_network:
    decisions:
      architecture: maf
```

## What This Model Does NOT Include

### No Execution Framework

ASP defines the specification and recipes. Execution orchestration (scheduling, monitoring, event tracking, UI) is handled by external tools:
- **asp-core**: Minimal runner (podman, dependency order)
- **Prism**: AI agent that writes code and registers recipes
- **External runners**: Dagster, Snakemake, or any tool that can read recipes

### No Execution Order Between Decisions

Decisions don't have causal relationships. Constraints (`requires`, `incompatible_with`) handle validity. Execution order is determined by recipe dependencies.

## Benefits of This Model

1. **Declarative**: Spec says WHAT, recipes say HOW
2. **Self-similar**: Every level has the same structure
3. **Transparent**: All decisions and alternatives are documented
4. **Composable**: Analyses can build on each other
5. **Evidence-linked**: Decisions cite verified evidence from literature
6. **Reproducible**: Recipes + containers = reproducible outputs
7. **Progressive**: Start with just a spec, add recipes and containers incrementally
8. **Agent-friendly**: Clear structure for AI agents to understand and implement
9. **Goal-oriented**: Problem statement keeps analysis focused
10. **Single-analysis first**: One universe answers the question; multiverse is for exploration
