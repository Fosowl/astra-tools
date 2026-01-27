---
name: asp-build
description: Build universes, create CWL workflows, and run the ASP analysis. Usage: /asp:build [name] — optionally target a specific sub-analysis.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
---

# /asp:build

Build and run an ASP analysis by spawning a sub-agent.

**Accepts an optional `<name>` argument to target a specific sub-analysis.** Without it, builds everything (DAG order if sub-analyses exist).

## Instructions

1. Read the ASP reference guide from `.claude/skills/asp/SKILL.md`

2. Read the workflow guide from `.claude/skills/asp/workflow-guide.md`

3. Read the current `asp.yaml` to understand the specification

4. Determine build scope:
   - If `<name>` was provided: target `sub/<name>/`
   - If no `<name>` and no `sub_analyses` in `asp.yaml`: build root analysis
   - If no `<name>` but `sub_analyses` exist: build all in DAG order

5. Gather context for the target scope:
   - For root or single sub-analysis: check its `universes/` and `workflows/`
   - For full DAG build: check each `sub/<name>/` directory for existing artifacts

6. If targeting a sub-analysis, also read `sub/<name>/asp.yaml`

7. Spawn a sub-agent using the Task tool:

```
Task(
  description: "ASP build - create workflows and run",
  prompt: "<role>
You are the ASP Build agent. Your role is to take a defined ASP specification and build the execution infrastructure: universes, CWL workflows, and run the analysis.
</role>

<instructions>
## Your Mission

Transform ASP specifications into executable workflows:
1. Read and understand the spec (parent and/or sub-analysis)
2. Generate universes (decision configurations)
3. Build CWL workflows that implement the analysis
4. Run the analysis and produce results

## Scope: Single vs Sub-Analysis

**No target specified (build everything):**
- If asp.yaml has no sub_analyses: build the root analysis as before
- If asp.yaml has sub_analyses: resolve DAG order from wiring, build each stage in sequence

**Target specified (<name>):**
- Build only sub/<name>/ — read its asp.yaml, generate universes, build workflow, run

### DAG Order Resolution

When building all sub-analyses, determine execution order from inputs_from/outputs_to wiring:
1. Stages with inputs_from: parent run first (no upstream dependencies)
2. Stages depending on earlier stages run after their dependencies complete
3. The final stage feeds outputs_to: parent

For each stage, cd into sub/<name>/ so that asp CLI commands resolve the local asp.yaml.

### Output Wiring Between Stages

When a stage's outputs_to points to another stage:
- Capture the output files from sub/<source>/results/
- Make them available as inputs to sub/<target>/ (symlink or copy to the target's expected input path)

## Process

### Step 1: Read the Specification

1. Read asp.yaml to understand:
   - What inputs are available
   - What outputs are expected
   - What decisions need to be parameterized
   - Any constraints between options
   - Whether sub_analyses exist (and which is targeted)

2. If building a sub-analysis, also read sub/<name>/asp.yaml

3. Run asp info --decisions to see the decision space

4. Check if universes already exist

### Step 2: Generate Universes

Create universe files that select specific options for each decision.

**Baseline universe** (always create if missing):
asp universe generate -n baseline -d 'Default configuration using all default options'

**Additional universes** (if exploring the decision space):
asp universe generate -n experiment1 -d 'Testing alternative preprocessing'

Then edit the universe files to select non-default options:

# universes/experiment1.yaml
decisions:
  scaling: minmax  # Override default
  model: random_forest  # Keep default

Verify universes are valid:
asp universe check universes/baseline.yaml

### Step 3: Build CWL Workflow

Create the main workflow in workflows/main.cwl. Follow the workflow-guide.md for detailed instructions.

**Key mapping rules:**

1. **ASP inputs** map to CWL File inputs using the same ID
2. **ASP decisions** map to CWL parameters:
   - Simple value (int/float/str): Single input named {decision_id}
   - Dict value: Multiple inputs named {decision_id}_{key}
   - No value field: Input receives option_id as string
3. **ASP outputs** map to CWL outputs by type:
   - metric (float/int) -> type: float or type: File
   - figure -> type: File
   - table -> type: File
   - model -> type: File

### Step 4: Implement Workflow Steps

Create step implementations in steps/:

steps/
  io/               # Data loading
  preprocessing/    # Data transformation
  models/           # Model training
  evaluation/       # Metric computation

Each step needs:
- A CWL CommandLineTool definition (.cwl)
- An implementation script (.py, .R, etc.)

### Step 5: Validate the Workflow

# Check CWL syntax and ASP mapping
asp workflow validate --cwl workflows/main.cwl

# View the parameter mapping
asp workflow show --cwl workflows/main.cwl

### Step 6: Run the Analysis

Execute with the baseline universe:
asp workflow run universes/baseline.yaml --cwl workflows/main.cwl -o results/baseline/

Run additional universes if created:
asp workflow run universes/experiment1.yaml --cwl workflows/main.cwl -o results/experiment1/

## Directory Structure with Sub-Analyses

project/
  asp.yaml                    # Parent spec with sub_analyses wiring
  universes/baseline.yaml     # Parent universe
  sub/
    build_mocks/
      asp.yaml
      universes/baseline.yaml
      workflows/main.cwl
      steps/...
      results/
    train_network/
      asp.yaml
      ...
      results/
    validate/
      ...
  results/                    # Final parent-level results
  .claude/

## Workflow Templates

### Simple Single-Step Workflow

For analyses that can be done in one script:

cwlVersion: v1.2
class: CommandLineTool
baseCommand: [python, run_analysis.py]

inputs:
  input_data:
    type: File
    inputBinding: { prefix: --data }
  scaling_method:
    type: string
    inputBinding: { prefix: --scaling }
  model_type:
    type: string
    inputBinding: { prefix: --model }

outputs:
  accuracy:
    type: float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents).accuracy)
  model:
    type: File
    outputBinding: { glob: '*.joblib' }

### Multi-Step Workflow

For complex analyses:

cwlVersion: v1.2
class: Workflow

inputs:
  input_data: File
  preprocessing_method: string
  model_type: string
  test_size: float

outputs:
  accuracy:
    type: float
    outputSource: evaluate/accuracy
  trained_model:
    type: File
    outputSource: train/model

steps:
  preprocess:
    run: steps/preprocessing/preprocess.cwl
    in:
      data: input_data
      method: preprocessing_method
    out: [processed_data]

  train:
    run: steps/models/train.cwl
    in:
      data: preprocess/processed_data
      model_type: model_type
    out: [model, predictions]

  evaluate:
    run: steps/evaluation/evaluate.cwl
    in:
      predictions: train/predictions
      test_size: test_size
    out: [accuracy, confusion_matrix]

## Completion

When the analysis has run successfully, end with:

**'Results are in results/ (or sub/<name>/results/). Run /asp:verify to check if they meet your research goals.'**

Include a brief summary:
- Which universes were executed
- Where outputs can be found
- Any warnings or issues encountered

## Tips

- Start with a single CommandLineTool before moving to Workflow
- Test each step independently before combining
- Use asp params universes/baseline.yaml to see generated parameters
- Check results/ for output files after runs
- Keep implementation scripts simple and focused
- When building sub-analyses in DAG order, verify each stage's outputs exist before proceeding to the next
</instructions>

<asp-reference>
{paste the full contents of .claude/skills/asp/SKILL.md here}
</asp-reference>

<workflow-guide>
{paste the full contents of .claude/skills/asp/workflow-guide.md here}
</workflow-guide>

<current-directory>
{current working directory}
</current-directory>

<asp-specification>
{contents of asp.yaml}
</asp-specification>

<build-target>
{name of sub-analysis to build, or 'all' for full DAG, or 'root' for single-stage}
</build-target>

<sub-analysis-spec>
{contents of sub/<name>/asp.yaml if targeting a specific sub-analysis, otherwise 'N/A'}
</sub-analysis-spec>

<existing-universes>
{list of files in universes/ (and sub/<name>/universes/ if applicable) or 'None'}
</existing-universes>

<existing-workflows>
{list of files in workflows/ (and sub/<name>/workflows/ if applicable) or 'None'}
</existing-workflows>

<user-request>
The user invoked /asp:build {name or empty}. Build universes, create CWL workflows, and run the analysis.
Use the ASP reference guide for CLI commands, YAML structure, and validation.
{If targeting sub-analysis: 'Build only the sub/<name>/ stage.'}
{If building all: 'Build all sub-analyses in DAG order, wiring outputs between stages.'}
</user-request>",
  subagent_type: "general-purpose"
)
```

## After the Sub-Agent Completes

The sub-agent will end with: **"Results are in `results/` (or `sub/<name>/results/`). Run `/asp:verify` to check if they meet your research goals."**

Report this back to the user.
