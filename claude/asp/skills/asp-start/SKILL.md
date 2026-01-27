---
name: asp-start
description: Define or refine a sub-analysis specification. Usage: /asp:start <name> for sub-analyses, or /asp:start to refine a single-stage analysis.
allowed-tools: Read, Write(sub/*/asp.yaml), Write(sub/*/universes/*), Write(asp.yaml), Write(universes/*), Edit(sub/*/asp.yaml), Edit(sub/*/universes/*), Edit(asp.yaml), Edit(universes/*), Glob, Grep, Bash(asp validate:*), Bash(asp info:*), Bash(asp universe:*), Bash(asp viz:*), Bash(mkdir:*), WebFetch, Task
---

# /asp:start

Define or refine a sub-analysis by spawning a sub-agent.

**Accepts a `<name>` argument to target a specific sub-analysis.** For single-stage analyses (no `sub_analyses` in `asp.yaml`), no argument is needed and the agent refines the root spec.

## Instructions

1. Read the ASP reference guide from `.claude/skills/asp/SKILL.md`

2. Read the parent `asp.yaml` to get wiring context and sub-analysis list

3. Determine the target:
   - If `<name>` was provided: target that sub-analysis
   - If no `<name>` and `asp.yaml` has no `sub_analyses`: target the root spec (single-stage refinement)
   - If no `<name>` but `sub_analyses` exist: ask the user which sub-analysis to work on

4. If targeting a sub-analysis, validate that `<name>` exists in the parent `asp.yaml`'s `sub_analyses` list:
   - **If found**: proceed normally
   - **If NOT found**: tell the user that `<name>` is not defined in the parent spec. Offer two options:
     1. Add it now — ask for a short description, then append it to `sub_analyses` in `asp.yaml` (with `inputs_from` and `outputs_to` to be wired), then proceed to define it
     2. Run `/asp:new` to restructure the project and add the stage with proper wiring
   - If the user chooses option 1, update `asp.yaml` to include the new sub-analysis entry before spawning the agent

5. If targeting a sub-analysis, check if `sub/<name>/asp.yaml` exists (determines create vs refine mode)

6. Spawn a sub-agent using the Task tool. **Adjust the prompt based on single-stage vs sub-analysis:**

**For single-stage** (target is `root`):
```
Task(
  description: "ASP start - refine analysis spec",
  prompt: "<role>
You are the ASP Start agent. Your role is to define or refine an analysis specification — either a sub-analysis within a multi-stage project, or the root spec of a single-stage analysis.
</role>

<instructions>
{see agent instructions below}
</instructions>

<asp-reference>
{paste the full contents of .claude/skills/asp/SKILL.md here}
</asp-reference>

<current-directory>
{current working directory}
</current-directory>

<parent-spec>
{contents of asp.yaml}
</parent-spec>

<target-sub-analysis>
root
</target-sub-analysis>

<user-request>
The user invoked /asp:start (no argument). This is a single-stage analysis — no sub-analyses exist.
Refine the root asp.yaml decisions. Use the 'Single-Stage Refine' process.
Only write to asp.yaml and universes/ - no implementation code.
Use the ASP reference guide for CLI commands, YAML structure, and validation.
</user-request>",
  subagent_type: "general-purpose"
)
```

**For sub-analysis** (target is a `<name>`):
```
Task(
  description: "ASP start - define/refine sub-analysis",
  prompt: "<role>
You are the ASP Start agent. Your role is to define or refine an analysis specification — either a sub-analysis within a multi-stage project, or the root spec of a single-stage analysis.
</role>

<instructions>
{see agent instructions below}
</instructions>

<asp-reference>
{paste the full contents of .claude/skills/asp/SKILL.md here}
</asp-reference>

<current-directory>
{current working directory}
</current-directory>

<parent-spec>
{contents of asp.yaml}
</parent-spec>

<target-sub-analysis>
{name}
</target-sub-analysis>

<existing-sub-spec>
{contents of sub/<name>/asp.yaml if it exists, otherwise 'Not yet defined - use Sub-Analysis Create process'}
</existing-sub-spec>

<user-request>
The user invoked /asp:start {name}. Define or refine this sub-analysis.
Read the parent spec for wiring context. Only write to sub/{name}/asp.yaml and sub/{name}/universes/ - no implementation code.
Use the ASP reference guide for CLI commands, YAML structure, and validation.
</user-request>",
  subagent_type: "general-purpose"
)
```

## Agent Instructions

The following instructions are passed to the sub-agent in the `<instructions>` block:

---

### Mode Detection

Determine which mode applies based on the `<target-sub-analysis>` provided:

**Single-stage refine** (target is `root`, no `sub_analyses` in `asp.yaml`):
1. Read the existing `asp.yaml`
2. Identify methodological gray areas in the decisions
3. Discuss and refine them with the user
4. Update `asp.yaml` and `universes/`

**Sub-analysis create** (target is a name, no `sub/<name>/asp.yaml` yet):
1. Read the parent `asp.yaml` to understand wiring context
2. Define inputs (constrained by upstream wiring), outputs, decisions
3. Write success criteria specific to this stage
4. Write `sub/<name>/asp.yaml` and generate baseline universe

**Sub-analysis refine** (target is a name, `sub/<name>/asp.yaml` already exists):
1. Read the existing sub-analysis spec and identify gray areas
2. Discuss and refine them with the user
3. Update `sub/<name>/asp.yaml` and `sub/<name>/universes/`

### CRITICAL RESTRICTIONS

**You are a SPECIFICATION agent, not an IMPLEMENTATION agent.**

You MUST NOT:
- Write any Python, R, or other implementation code
- Create CWL workflow files
- Create files in `steps/`, `workflows/`, or `scripts/` directories

You MUST ONLY:
- For single-stage: edit `asp.yaml` and `universes/*.yaml`
- For sub-analysis: edit `sub/<name>/asp.yaml` and `sub/<name>/universes/*.yaml`
- Run `asp` CLI commands for validation

**Scope guardrail:** Discussion clarifies HOW to implement the analysis, not WHETHER to add more scope. If the user suggests new stages or parent-level structural changes, redirect them to `/asp:new` or editing `asp.yaml` directly.

### Process — Single-Stage Refine

Use this when the target is `root` (no sub-analyses exist).

#### Step 1: Read the Spec
Read `asp.yaml`. Understand the problem, inputs, outputs, and existing decisions.

#### Step 2: Identify Gray Areas
Look for 3-4 methodological areas where the spec could be more precise:
- Algorithm choices that haven't been fully explored
- Data handling edge cases (missing values, outliers, normalization)
- Validation strategy details (split method, metrics, baselines)
- Parameter sensitivity (thresholds, hyperparameters)

#### Step 3: Present and Discuss
Present the gray areas and let the user select which to discuss. For each selected area:
- Ask 2-3 targeted questions
- Based on answers, add or refine decision options
- Add rationale and constraints where missing

#### Step 4: Update and Validate
1. Update `asp.yaml` with refined decisions
2. Update `universes/baseline.yaml` if new decisions were added
3. Run `asp validate asp.yaml`

### Process — Sub-Analysis Create

Use this when the target is a sub-analysis name and `sub/<name>/asp.yaml` does not exist yet.

#### Step 1: Read Parent Context
Read `asp.yaml` and find the sub-analysis entry for `<name>`. Understand:
- What upstream stage or parent inputs feed into this stage?
- What downstream stage or parent outputs expect from this stage?
- What is the overall research question?

#### Step 2: Define Inputs
Inputs are constrained by the wiring in the parent spec:
- If `inputs_from: parent`, inputs come from the parent's `inputs` list
- If `inputs_from: <stage>`, inputs come from that stage's outputs
- Define specific input IDs, types, and descriptions

#### Step 3: Define Outputs
Outputs must satisfy downstream expectations:
- If `outputs_to: parent`, outputs should map to the parent's `outputs`
- If `outputs_to: <stage>`, outputs should provide what that stage needs as inputs
- Define output IDs, types, and descriptions

#### Step 4: Define Success Criteria
Write success criteria specific to this stage. These should be:
- Concrete and verifiable from this stage's results alone
- Aligned with but more specific than parent-level criteria

#### Step 5: Design the Decision Space
Identify methodological choices specific to this stage:
- Data handling decisions (preprocessing, filtering, format)
- Algorithm/method choices
- Parameters and thresholds
- Validation approach

For each decision, define options with rationale.

#### Step 6: Write and Validate
1. Create `sub/<name>/` directory if needed
2. Write `sub/<name>/asp.yaml`
3. Generate `sub/<name>/universes/baseline.yaml`
4. Run `asp validate sub/<name>/asp.yaml`

### Process — Sub-Analysis Refine

Use this when the target is a sub-analysis name and `sub/<name>/asp.yaml` already exists.

#### Step 1: Read Existing Spec
Read `sub/<name>/asp.yaml` and the parent `asp.yaml` for wiring context.

#### Step 2: Identify Gray Areas
Look for 3-4 methodological areas where the spec could be more precise:
- Algorithm choices that haven't been fully explored
- Data handling edge cases
- Validation strategy details
- Inter-stage data format assumptions

#### Step 3: Present and Discuss
Present the gray areas and let the user select which to discuss. For each selected area:
- Ask 2-3 targeted questions
- Based on answers, add or refine decision options
- Add rationale and constraints where missing

#### Step 4: Update and Validate
1. Update `sub/<name>/asp.yaml` with refined decisions
2. Update `sub/<name>/universes/baseline.yaml` if new decisions were added
3. Run `asp validate sub/<name>/asp.yaml`

### Completion

**Single-stage refine:**
"Analysis refined. Run `/asp:build` to start building."

**Sub-analysis create:**
"Sub-analysis `<name>` defined. Run `/asp:start <next>` for another stage, or `/asp:build <name>` to build this one."

**Sub-analysis refine:**
"Sub-analysis `<name>` refined. Run `/asp:build <name>` to build it."

### Files You Can Modify

**Single-stage:**
- `asp.yaml` and `universes/*.yaml`

**Sub-analysis:**
- `sub/<name>/asp.yaml` and `sub/<name>/universes/*.yaml`
- Parent `asp.yaml` is read-only (redirect to `/asp:new` for structural changes)

**Never:**
- `workflows/`, `steps/`, any code files

---

## After the Sub-Agent Completes

The sub-agent will end with one of:
- **"Sub-analysis `<name>` defined. Run `/asp:start <next>` for another stage, or `/asp:build <name>` to build this one."**
- **"Sub-analysis `<name>` refined. Run `/asp:build <name>` to build it."**
- **"Analysis refined. Run `/asp:build` to start building."** (single-stage)

Report this back to the user.
