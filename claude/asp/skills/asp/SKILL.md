---
name: asp
description: Work with ASP (Agentic Science Protocol) analyses. ALWAYS use this skill when working in a project with asp.yaml. Use for creating analyses, editing specifications, validating, managing universes, extracting insights from papers, or building CWL workflows. Triggers on asp.yaml, universes/, decisions, insights, or any ASP-related work.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(asp:*), Bash(python:*)
---

# ASP Analysis Skill

Help users work with the Agentic Science Protocol (ASP) - a declarative specification format for scientific analyses.

## Agent Commands

| Command | Purpose |
|---------|---------|
| `/asp:new` | Create a new analysis project — scope research question, identify sub-analyses, write top-level `asp.yaml` |
| `/asp:start <name>` | Define or refine a specific sub-analysis (or refine root spec for single-stage analyses) |
| `/asp:build [name]` | Build universes, CWL workflows, and run the analysis (optionally target a sub-analysis) |
| `/asp:verify [name]` | Verify results meet success criteria (optionally target a sub-analysis) |

### Workflow

**Single-stage analysis:**
```
/asp:new  →  /asp:build  →  /asp:verify
```

**Multi-stage analysis with sub-analyses:**
```
/asp:new  →  /asp:start <stage1>  →  /asp:start <stage2>  →  /asp:build  →  /asp:verify
```

You can also build/verify individual stages:
```
/asp:build <name>  →  /asp:verify <name>
```

## Sub-Analyses

A multi-stage analysis uses `sub_analyses` in the parent `asp.yaml` to define the pipeline:

```yaml
sub_analyses:
  - name: build_mocks
    description: "Generate synthetic training data"
    inputs_from: parent
    outputs_to: train_network

  - name: train_network
    description: "Train neural network on mock data"
    inputs_from: build_mocks
    outputs_to: validate

  - name: validate
    description: "Validate trained model"
    inputs_from: [train_network, parent]
    outputs_to: parent
```

Each sub-analysis gets its own directory under `sub/`:
```
project/
├── asp.yaml                    # Parent spec with sub_analyses wiring
├── universes/baseline.yaml
├── sub/
│   ├── build_mocks/
│   │   ├── asp.yaml
│   │   ├── universes/baseline.yaml
│   │   ├── workflows/main.cwl
│   │   ├── steps/...
│   │   └── results/
│   ├── train_network/
│   │   └── ...
│   └── validate/
│       └── ...
├── results/                    # Final parent-level results
└── .claude/
```

Sub-analyses are optional. Single-stage analyses work identically to before — no `sub_analyses` section, everything at the root level.

## Quick Reference

### CLI Commands
```bash
asp init <directory>              # Create new analysis project
asp validate asp.yaml             # Validate analysis specification
asp validate universes/foo.yaml   # Validate universe
asp info                          # Show analysis summary
asp info --decisions              # Show decision details
asp universe generate -n baseline # Generate universe from defaults
asp universe check universes/x.yaml  # Check universe constraints
asp viz                           # Visualize decision space
asp schema show analysis          # Show JSON schema

# Workflow Integration
asp workflow run universes/baseline.yaml --cwl main.cwl  # Run workflow
asp workflow run universes/x.yaml --cwl main.cwl -o out/ # Run with output dir
asp workflow validate --cwl main.cwl         # Validate CWL mapping
asp workflow show --cwl main.cwl             # Show parameter mapping table
asp params universes/baseline.yaml           # Output CWL parameters to stdout
```

**Sub-analysis note:** When operating inside `sub/<name>/`, agents should `cd` into the sub-analysis directory so that `asp validate`, `asp info`, etc. resolve the local `asp.yaml` naturally.

## Core Concepts

### Analysis Structure
An ASP analysis (`asp.yaml`) contains:
- **analysis**: name, problem statement, success criteria, inputs, outputs
- **decisions**: choices that define the analysis methodology
- **insights**: scientific knowledge from papers or prior analyses
- **sub_analyses** (optional): pipeline stages with wiring

### Success Criteria
Define concrete, verifiable conditions for success:
```yaml
analysis:
  problem: |
    Build a classifier for the Iris dataset...
  success_criteria:
    - "Achieve >95% classification accuracy on held-out test set"
    - "Model size under 10MB for mobile deployment"
    - "Prediction time under 100ms per sample"
```
These criteria are used by `/asp:verify` to determine if the analysis succeeded.

### Universes
A universe is a complete set of decisions - one option per decision point.

### Inputs
Inputs define the data sources for an analysis:
- **id**: Unique identifier (used as CWL parameter name)
- **type**: `data`, `analysis`, or `literature`
- **source**: Where to get the data (file path or URL)

```yaml
inputs:
  - id: training_data
    type: data
    source: "data/train.csv"           # Local file path

  - id: remote_data
    type: data
    source:
      type: url
      url: "https://example.com/data.csv"  # Remote URL
```

## Creating a New Analysis

Use `/asp:new` to interactively scope your project:
1. Define the research question
2. Identify whether this is multi-stage
3. Define top-level inputs, outputs, success criteria
4. Name and wire sub-analyses (if multi-stage)

Then use `/asp:start <name>` to flesh out individual sub-analyses.

Alternatively, scaffold manually:
```bash
asp init my-analysis -n "Analysis Name" -p "Problem statement"
```

## Extracting Insights from Papers

When the user provides a paper (PDF, DOI, or description) to extract insights:

### Step 1: Identify the Paper
Get the DOI. Format: `10.XXXX/...` (e.g., `10.1038/s41586-023-06221-2`)

### Step 2: Read the Current Analysis
Check `asp.yaml` to understand:
- What problem is being solved?
- What decisions need evidence?
- What inputs/outputs are defined?

### Step 3: Extract Relevant Insights
For each insight relevant to the analysis:

```yaml
insights:
  insight_id:  # lowercase_with_underscores
    claim: "One sentence stating what we learned"
    source:
      doi: "10.1234/paper-doi"
    evidence:
      # For figures:
      - figure: "Figure 3a"
        caption: "Description of what it shows"
      # For quotes:
      - quote: "Exact text from the paper"
        location: "Section 2.1, p.5"
      # For tables:
      - table: "Table 1"
        location: "row 3, accuracy column"
        value: "0.92"
      # For equations:
      - equation: "Equation 7"
        expression: "L = (C/C_0)^α"
      # For numerical results:
      - result: "accuracy improvement"
        location: "Section 4.2"
        value: "15%"
    scope: "Context where this applies (optional)"
```

### Step 4: Link to Decisions
Reference insights in decision options:

```yaml
decisions:
  method_choice:
    options:
      method_a:
        label: "Method A"
        evidence:
          - insight: insight_id  # Reference the insight
```

### Step 5: Validate
```bash
asp validate asp.yaml
```

## Insight Types by Source

### From Papers (doi)
Use these evidence types:
- `figure`: Reference to a figure
- `quote`: Direct quote with location
- `table`: Table reference with specific value
- `equation`: Mathematical expression
- `result`: Numerical finding

### From Prior Analyses (analysis)
Use these evidence types:
- `metric`: Named metric with value
- `output`: Reference to output artifact

```yaml
insights:
  prior_finding:
    claim: "StandardScaler outperforms MinMaxScaler on this dataset"
    source:
      analysis: "our-org/preprocessing-study"
      version: "1.2.0"
      universe: "baseline"
    evidence:
      - metric:
          name: "accuracy"
          value: { standard: 0.94, minmax: 0.89 }
      - output: "figures/scaler_comparison.png"
```

## Validation Checklist

Before finalizing an analysis, verify:

1. **Schema compliance**: `asp validate asp.yaml`
2. **All decisions have defaults**: Required for universe generation
3. **Insights have valid DOIs**: Pattern `10.XXXX/...`
4. **Evidence references exist**: Insights referenced in evidence must be defined
5. **Constraint references valid**: `incompatible_with` and `requires` point to real options

## Common Patterns

### Adding a New Decision
```yaml
decisions:
  new_decision:
    label: "Human-readable Label"
    type: method  # or: data, parameter
    importance: 3  # 1=critical, 5=minor
    rationale: "Why this decision matters"
    default: option_a
    options:
      option_a:
        label: "Option A"
        description: "What this option does"
      option_b:
        label: "Option B"
        description: "Alternative approach"
        incompatible_with: ["other_decision.some_option"]
```

### Adding Literature Input
```yaml
analysis:
  inputs:
    - id: smith2023
      type: literature
      description: "Smith et al. 2023 - Methodology paper"
```

### Creating a New Universe
```bash
asp universe generate -n experiment1 -d "Testing hypothesis X"
```

Then edit `universes/experiment1.yaml` to customize decisions.

## File Locations

### Single-Stage Analysis
```
my-analysis/
├── asp.yaml              # Main analysis specification
├── universes/            # Decision selections
│   ├── baseline.yaml
│   └── experiment1.yaml
├── workflows/            # CWL workflow definitions
│   └── main.cwl
├── steps/                # ALL workflow implementation goes here
│   ├── io/
│   ├── preprocessing/
│   ├── models/
│   └── evaluation/
├── insights/             # Optional: separate insight files
└── results/              # Execution outputs (gitignored)
```

### Multi-Stage Analysis
```
my-analysis/
├── asp.yaml              # Parent spec with sub_analyses
├── universes/baseline.yaml
├── sub/
│   ├── stage_one/
│   │   ├── asp.yaml
│   │   ├── universes/baseline.yaml
│   │   ├── workflows/main.cwl
│   │   ├── steps/...
│   │   └── results/
│   └── stage_two/
│       └── ...
├── results/              # Final parent-level results
└── .claude/
```

**Important**:
- All implementation code (Python, R, shell scripts) must be placed in the `steps/` folder alongside their CWL definitions. Do not create a separate `scripts/` folder.
- Universes are the source of truth for CWL parameters. Use `asp workflow run` to execute workflows directly from universes, or `asp params` to inspect the generated parameters.

## Building CWL Workflows

For detailed guidance on building CWL workflows from ASP analyses, see [workflow-guide.md](workflow-guide.md).

Key points:
- ASP inputs map to CWL `File` inputs using the same ID
- ASP decisions map to CWL parameters (naming depends on `value` structure)
- Use `asp workflow validate` to check CWL matches ASP spec
- Use `asp workflow run` to execute with a universe

## Tips

1. **Start with the problem**: Write a clear problem statement before defining decisions
2. **One insight per finding**: Don't combine multiple findings in one insight
3. **Precise evidence**: Include page numbers, figure labels, exact quotes
4. **Link insights to decisions**: Every decision option should ideally have supporting evidence
5. **Use scope**: Clarify when an insight applies (dataset, model type, conditions)
6. **Add value fields**: When integrating with CWL, add explicit `value` fields to options
