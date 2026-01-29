---
name: asp-build
description: Build and run an ASP analysis chunk. Usage: /asp-build [chunk] — build a specific chunk, or all chunks.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
---

# /asp-build

Build universes, create CWL workflows, and run the analysis.

**Usage:**
- `/asp-build` — build all chunks in dependency order
- `/asp-build <chunk>` — build a specific chunk by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read the workflow guide: `.claude/skills/asp/workflow-guide.md`
3. Read `asp.yaml` to understand the specification
4. Read the plan: `plans/<chunk_name>.md`. If no plan exists, warn the user and suggest running `/asp-plan` first.

## Process

### Determine scope

- No argument: build all chunks in order
- `<chunk>` argument: build only that chunk

### Check decisions before building

Read the decisions in scope — `chunks.<name>.decisions` for the target chunk. Skip any decision that already has `reviewed: true` — a human has already weighed in. For unreviewed decisions:
- **Importance 1-2**: Ask the user, then set `reviewed: true` in `asp.yaml`.
- **Importance 3**: Mention and offer to discuss.
- **Importance 4-5**: Use defaults without asking.

### Build steps

1. Generate universes if missing (`asp universe generate -n baseline`)
2. Build CWL workflows mapping inputs, decisions, and outputs
3. Implement workflow steps in `steps/` (single chunk) or `steps/<chunk_name>/` (multiple chunks)
4. Validate (`asp workflow validate --cwl workflows/main.cwl`)
5. Run (`asp workflow run universes/baseline.yaml --cwl workflows/main.cwl -o results/baseline/`)

### Chunk builds

When building a specific chunk, scope all work to that chunk's decisions. Chunk decisions appear under `chunks.<name>.decisions` in the spec and `chunks.<name>` in universe files.

## Completion

- "Results for `<name>` ready. Run `/asp-verify <name>` to check them." Use the actual chunk name.
- **Do NOT suggest planning or building the next chunk.** The workflow is plan → build → verify for each chunk. Only `/asp-verify` advances to the next chunk.
