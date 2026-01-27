---
name: asp-build
description: Build and run an ASP analysis. Usage: /asp:build [phase] — build a specific phase, or the whole analysis if single-stage.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
---

# /asp:build

Build universes, create CWL workflows, and run the analysis.

**Usage:**
- `/asp:build` — build the whole analysis (single-stage) or all phases in dependency order
- `/asp:build <phase>` — build a specific phase by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read the workflow guide: `.claude/skills/asp/workflow-guide.md`
3. Read `asp.yaml` to understand the specification
4. If a plan exists from `/asp:plan`, read it

## Process

### Determine scope

- No argument + no `phases`: build the root analysis
- No argument + `phases` exist: build all phases in dependency order (inferred from input wiring)
- `<phase>` argument: build only that phase

### Build steps

1. Generate universes if missing (`asp universe generate -n baseline`)
2. Build CWL workflows mapping inputs, decisions, and outputs
3. Implement workflow steps in `steps/`
4. Validate (`asp workflow validate --cwl workflows/main.cwl`)
5. Run (`asp workflow run universes/baseline.yaml --cwl workflows/main.cwl -o results/baseline/`)

### Phase builds

When building a specific phase, scope all work to that phase's inputs, outputs, and decisions. Phase decisions appear under `phases.<name>.decisions` in the spec and `phases.<name>` in universe files.

## Completion

- "Results are in `results/`. Run `/asp:verify` to check if they meet your research goals."
- For phase: "Results for `<phase>` ready. Run `/asp:verify <phase>` to check them."
