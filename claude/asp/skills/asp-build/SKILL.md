---
name: asp-build
description: Build and run an ASP analysis phase. Usage: /asp-build [phase] — build a specific phase, or all phases.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
---

# /asp-build

Build universes, create CWL workflows, and run the analysis.

**Usage:**
- `/asp-build` — build all phases in dependency order
- `/asp-build <phase>` — build a specific phase by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read the workflow guide: `.claude/skills/asp/workflow-guide.md`
3. Read `asp.yaml` to understand the specification
4. Read the plan: `plans/<phase_name>.md`. If no plan exists, warn the user and suggest running `/asp-plan` first.

## Process

### Determine scope

- No argument: build all phases in dependency order (inferred from input wiring)
- `<phase>` argument: build only that phase

### Check decisions before building

Read the decisions in scope — `phases.<name>.decisions` for the target phase (plus top-level `decisions` for cross-cutting choices). Skip any decision that already has `reviewed: true` — a human has already weighed in. For unreviewed decisions:
- **Importance 1-2**: Ask the user, then set `reviewed: true` in `asp.yaml`.
- **Importance 3**: Mention and offer to discuss.
- **Importance 4-5**: Use defaults without asking.

### Build steps

1. Generate universes if missing (`asp universe generate -n baseline`)
2. Build CWL workflows mapping inputs, decisions, and outputs
3. Implement workflow steps in `steps/<phase_name>/`
4. Validate (`asp workflow validate --cwl workflows/main.cwl`)
5. Run (`asp workflow run universes/baseline.yaml --cwl workflows/main.cwl -o results/baseline/`)

### Phase builds

When building a specific phase, scope all work to that phase's inputs, outputs, and decisions. Phase decisions appear under `phases.<name>.decisions` in the spec and `phases.<name>` in universe files.

## Completion

- "Results for `<name>` ready. Run `/asp-verify <name>` to check them." Use the actual phase name.
