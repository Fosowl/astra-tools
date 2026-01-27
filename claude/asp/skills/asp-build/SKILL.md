---
name: asp-build
description: Build and run an ASP analysis phase. Usage: /asp:build [phase] — build a specific phase, or all phases.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
---

# /asp:build

Build universes, create CWL workflows, and run the analysis.

**Usage:**
- `/asp:build` — build all phases in dependency order
- `/asp:build <phase>` — build a specific phase by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read the workflow guide: `.claude/skills/asp/workflow-guide.md`
3. Read `asp.yaml` to understand the specification
4. Read the plan: `plans/<phase_name>.md`. If no plan exists, warn the user and suggest running `/asp:plan` first.

## Process

### Determine scope

- No argument: build all phases in dependency order (inferred from input wiring)
- `<phase>` argument: build only that phase

### Check decisions before building

Read the decisions in scope — `phases.<name>.decisions` for the target phase (plus top-level `decisions` for cross-cutting choices). If any implementation choice maps to a decision with importance 1-2, ask the user before proceeding. For importance 3, mention it. For 4-5, use defaults.

### Build steps

1. Generate universes if missing (`asp universe generate -n baseline`)
2. Build CWL workflows mapping inputs, decisions, and outputs
3. Implement workflow steps in `steps/`
4. Validate (`asp workflow validate --cwl workflows/main.cwl`)
5. Run (`asp workflow run universes/baseline.yaml --cwl workflows/main.cwl -o results/baseline/`)

### Phase builds

When building a specific phase, scope all work to that phase's inputs, outputs, and decisions. Phase decisions appear under `phases.<name>.decisions` in the spec and `phases.<name>` in universe files.

## Completion

- "Results for `<name>` ready. Run `/clear`, then `/asp:verify <name>` to check them." Use the actual phase name.
- If there are more phases to build, also mention: "Next phase to build: `/clear`, then `/asp:build <next_name>`."
