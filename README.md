# ASP - Agentic Science Protocol

[![CI](https://github.com/EiffL/ASP/actions/workflows/ci.yml/badge.svg)](https://github.com/EiffL/ASP/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A declarative specification format for scientific analyses that can be executed by AI agents.

## What is ASP?

ASP is the **core specification** for describing scientific analyses. It separates **what** you want to learn from **how** to compute it:

- **Problem statement** - The research question
- **Inputs** - Data, previous analyses, literature
- **Outputs** - Metrics, figures, tables, models
- **Decisions** - The choices that define your analysis
- **Insights** - Evidence from papers and prior analyses
- **Constraints** - Relationships between decision options

ASP makes no prescription about execution frameworks. The specification defines *what* to compute; execution is handled by the agentic layer.

```
ASP (this package)  =  Schema, validation, insights, evidence verification, CLI
Prism (agent layer) =  Claude Code skills, project scaffolding, remote/HPC config
```

## Key Concepts

**Universe**: A complete set of decisions -- one option selected for each decision point. Running a universe produces results that answer your problem statement.

**Multiverse**: The space of all valid decision combinations. Its purpose is transparency and traceability, not exhaustive search.

**Chunks**: All decisions live under chunks. Single-stage analyses use a `main` chunk. Complex analyses decompose into multiple chunks with their own decisions and artefacts.

**Evidence-based decisions**: Link decisions to supporting evidence from papers or prior analyses, with quote verification.

**Composability**: Use outputs from one analysis as inputs to another.

## Installation

```bash
# Core specification package:
pip install asp

# For development:
pip install -e ".[dev]"

# Full agentic experience (includes ASP automatically):
pip install prism
```

## Quick Start

```bash
# Create a minimal analysis scaffold
asp init my-analysis
cd my-analysis

# Edit asp.yaml to define your analysis
# Then validate it
asp validate asp.yaml
```

For full agentic scaffolding with Claude Code integration, use `prism init` instead.

## Quick Example

```yaml
version: "1.0"

analysis:
  name: "Iris Classification Study"
  problem: |
    Build a robust classifier for the Iris dataset that accurately
    predicts species from flower measurements.

  inputs:
    - id: iris_data
      type: data
      source: "sklearn.datasets.load_iris"

  outputs:
    - id: accuracy
      type: metric
      dtype: float
      range: [0, 1]

    - id: confusion_matrix
      type: figure
      formats: [png]

chunks:
  main:
    decisions:
      scaling:
        label: "Feature Scaling"
        type: method
        importance: 2
        default: standard
        options:
          none:
            label: "No Scaling"
          standard:
            label: "StandardScaler"
          minmax:
            label: "MinMaxScaler"
            incompatible_with: ["model.svm"]

      model:
        label: "Classification Model"
        type: method
        importance: 1
        default: random_forest
        options:
          svm:
            label: "Support Vector Machine"
          random_forest:
            label: "Random Forest"
          logistic:
            label: "Logistic Regression"
```

See [examples/iris/](examples/iris/) for a complete working example.

## CLI Commands

```bash
# Project setup
asp init my-analysis               # Create minimal scaffold
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

## Project Structure

An ASP project created with `asp init` has this minimal structure:

```
my-analysis/
├── asp.yaml              # Analysis specification (source of truth)
├── .gitignore            # Git ignore rules
└── universes/            # Universe definitions (decision selections)
    └── baseline.yaml
```

Use `prism init` for full agentic scaffolding (Claude Code config, scripts, HPC targets).

## Design Principles

1. **Declarative** - Spec says WHAT, not HOW
2. **ASP is source of truth** - Implementations are derived from ASP
3. **Transparent** - All decisions and alternatives documented
4. **Composable** - Analyses build on each other
5. **Evidence-linked** - Decisions cite supporting evidence
6. **Reproducible** - Precise provenance and verification

## Documentation

See [DESIGN.md](DESIGN.md) for the complete specification.

## License

Apache 2.0
