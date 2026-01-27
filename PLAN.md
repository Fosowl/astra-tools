# Plan: Sub-Analyses in the ASP Declarative Format

## Problem

The current ASP format is flat — all decisions, inputs, and outputs live at one level. Real scientific analyses have intermediate stages (e.g., build mocks → train network → validate), each with their own scoped decisions and outputs that a user wants to inspect before moving on. The flat format forces a "one-shot" approach that doesn't match how analysis actually works.

## Design Summary

A **sub-analysis** is a full ASP analysis (same schema, same file format) that represents one stage of a larger analysis. The parent analysis acts as an orchestrator: it declares which sub-analyses exist and wires outputs from one into inputs of the next. Each sub-analysis owns its own decisions and universes.

### Key Principles

1. **A sub-analysis IS an analysis.** Same `asp.yaml` schema. It has its own problem statement, inputs, outputs, decisions, and `universes/` directory.

2. **Abstract inputs, parent wiring.** Sub-analyses declare what inputs they need without specifying where they come from. The parent maps concrete sources (its own inputs, or sibling sub-analysis outputs) to those abstract inputs.

3. **Telescoping universes.** Each sub-analysis has its own universe files. The parent universe selects which sub-universe to use at each level, plus any parent-level decisions.

4. **Implicit ordering from data flow.** No explicit ordering field. The DAG is derived from how the parent wires outputs to inputs. (Revisit if explicit ordering is needed later.)

5. **Standalone or composed.** A sub-analysis can be run independently (user provides inputs directly) or as part of a parent pipeline (parent wires inputs).

## Concrete Format

### Parent analysis: `asp.yaml`

```yaml
version: "1.0"

analysis:
  name: "SBI Cosmological Parameter Estimation"
  problem: |
    Use simulation-based inference to constrain cosmological
    parameters from Type Ia supernova survey data.

  inputs:
    - id: survey_catalog
      type: data
      source: "..."
      description: "Observed Type Ia supernova catalog"

  outputs:
    - id: posterior_contours
      type: figure
      from: validate.posterior_plot       # drawn from a sub-analysis output
    - id: parameter_constraints
      type: table
      from: validate.constraints_table

  sub_analyses:
    build_mocks:
      path: ./sub/build_mocks
      inputs:
        survey_catalog: inputs.survey_catalog   # wire parent input

    train_network:
      path: ./sub/train_network
      inputs:
        mock_catalog: build_mocks.mock_catalog  # wire from sibling output
        survey_catalog: inputs.survey_catalog

    validate:
      path: ./sub/validate
      inputs:
        trained_model: train_network.trained_model
        survey_catalog: inputs.survey_catalog

# Parent-level decisions (if any — e.g., cross-cutting concerns)
decisions:
  reporting_style:
    label: "Reporting Style"
    type: parameter
    default: publication
    options:
      publication:
        label: "Publication quality"
      exploratory:
        label: "Quick exploratory"
```

### Sub-analysis: `sub/build_mocks/asp.yaml`

```yaml
version: "1.0"

analysis:
  name: "Build Realistic Mock Catalogs"
  problem: |
    Generate realistic mock supernova catalogs that match the
    survey selection function and noise properties.

  inputs:
    - id: survey_catalog
      type: data
      description: "Reference catalog for matching survey properties"
      # No source — abstract input, wired by parent (or provided directly)

  outputs:
    - id: mock_catalog
      type: data
      formats: [fits]
      description: "Simulated catalog matching survey properties"
    - id: diagnostic_plots
      type: figure
      formats: [png]
      description: "Mock vs real distribution comparisons"

decisions:
  noise_model:
    label: "Noise Model"
    type: method
    importance: 1
    default: heteroscedastic
    options:
      homoscedastic:
        label: "Homoscedastic"
        description: "Uniform noise across all observations"
      heteroscedastic:
        label: "Heteroscedastic"
        description: "Per-observation noise from survey pipeline"

  selection_function:
    label: "Selection Function"
    type: method
    importance: 2
    default: magnitude_limited
    options:
      magnitude_limited:
        label: "Magnitude Limited"
      full_selection:
        label: "Full Selection Model"
        description: "Includes spectroscopic follow-up efficiency"
```

### Sub-analysis universes: `sub/build_mocks/universes/baseline.yaml`

```yaml
id: baseline
description: "Standard mock generation with heteroscedastic noise"
decisions:
  noise_model: heteroscedastic
  selection_function: magnitude_limited
```

### Parent universe: `universes/baseline.yaml`

```yaml
id: baseline
description: "Standard pipeline configuration"

decisions:
  reporting_style: publication

sub_analyses:
  build_mocks: baseline          # use "baseline" universe for this sub
  train_network: baseline
  validate: baseline
```

## Directory Structure

```
my-sbi-analysis/
├── asp.yaml                          # Parent analysis (orchestrator)
├── universes/
│   └── baseline.yaml                 # Parent universe (selects sub-universes)
│
├── sub/
│   ├── build_mocks/
│   │   ├── asp.yaml                  # Sub-analysis spec
│   │   └── universes/
│   │       ├── baseline.yaml
│   │       └── full_selection.yaml
│   │
│   ├── train_network/
│   │   ├── asp.yaml
│   │   └── universes/
│   │       ├── baseline.yaml
│   │       └── large_architecture.yaml
│   │
│   └── validate/
│       ├── asp.yaml
│       └── universes/
│           └── baseline.yaml
│
├── results/                          # Execution outputs
└── .claude/
```

## Schema Changes Required

### 1. Analysis schema: add `sub_analyses` and `from` on outputs

**`sub_analyses`** — new optional top-level key (sibling of `analysis` and `decisions`):

```
sub_analyses:
  type: object
  additionalProperties:
    type: object
    required: [path]
    properties:
      path:
        type: string                  # relative path to sub-analysis directory
        description: Directory containing the sub-analysis asp.yaml
      inputs:
        type: object                  # map of sub-analysis input id → source reference
        additionalProperties:
          type: string                # e.g., "inputs.survey_catalog" or "build_mocks.mock_catalog"
```

**`from`** — new optional field on outputs:

```
outputs[].from:
  type: string
  description: |
    Reference to a sub-analysis output, in the form "sub_analysis_id.output_id".
    When present, this output is drawn from the referenced sub-analysis
    rather than produced directly. The output type/format should match.
```

### 2. Universe schema: add `sub_analyses`

```
sub_analyses:
  type: object
  additionalProperties:
    type: string                      # universe id to use for each sub-analysis
```

### 3. New semantic validation rules

- Every sub-analysis `path` must point to a directory containing a valid `asp.yaml`
- Every key in `sub_analyses[x].inputs` must match an input `id` in the sub-analysis
- Every value in `sub_analyses[x].inputs` must be a valid reference:
  - `inputs.<id>` — references a parent input
  - `<sub_analysis_id>.<output_id>` — references a sibling sub-analysis output
- Sibling references must not create cycles (DAG validation)
- Every `from` reference on a parent output must resolve to a valid sub-analysis output
- Parent universe `sub_analyses` keys must match declared sub-analysis ids
- Parent universe `sub_analyses` values must match valid universe ids in the referenced sub-analysis

## What This Does NOT Include (Yet)

- **Explicit ordering**: Ordering is derived from input wiring. Revisit if needed.
- **Execution/gating semantics**: How the agent actually pauses between sub-analyses for user inspection. This is a plugin/runtime concern, not a declarative format concern.
- **Recursive nesting**: A sub-analysis could theoretically have its own sub-analyses. The schema wouldn't prevent it, but we don't need to design for it explicitly now.
- **Cross-level constraints**: A parent decision constraining a sub-analysis decision (e.g., "if parent says exploratory, sub-analysis must use fast option"). Interesting but adds complexity — defer.

## Implementation Steps

1. Add `sub_analyses` to the Pydantic analysis model (`models/analysis.py`)
2. Add `from` field to the output model
3. Add `sub_analyses` to the universe model (`models/universe.py`)
4. Regenerate JSON schemas (`python tools/generate_schemas.py`)
5. Add semantic validation rules for sub-analysis wiring and DAG validation (`src/asp/validation/semantic.py`)
6. Add test fixtures: a parent + sub-analysis example
7. Update the iris example or add a new example demonstrating sub-analyses
8. Update DESIGN.md with sub-analysis documentation
