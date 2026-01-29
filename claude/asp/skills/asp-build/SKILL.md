---
name: asp-build
description: Plan and build an ASP analysis chunk. Usage: /asp-build [chunk] — plan, build, and run a specific chunk or all chunks.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, WebFetch, AskUserQuestion
---

# /asp-build

Plan how to implement an analysis chunk, then build and run it.

`/asp-new` defines WHAT we want. `/asp-build` figures out HOW to do it and executes.

**Usage:**
- `/asp-build` — plan and build all chunks in order
- `/asp-build <chunk>` — plan and build a specific chunk by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read the workflow guide: `.claude/skills/asp/workflow-guide.md`
3. Read `asp.yaml` to understand the specification
4. If `<chunk>` was given, confirm it exists in `chunks`

## Process

### Determine scope

- No argument: if there are multiple chunks, use `AskUserQuestion` to ask which chunk to work on (list chunk names as options). Work on ONE chunk at a time.
- `<chunk>` argument: work on that specific chunk

### Surface important decisions

Read the decisions in scope — `chunks.<name>.decisions` for the target chunk. Skip any decision that already has `reviewed: true` — a human has already weighed in. For unreviewed decisions, based on importance:

- **1-2 (critical/high)**: Must ask the user. Use `AskUserQuestion` with the decision options as multiple-choice answers. Put the default/recommended option first with "(Recommended)". Ask one decision at a time.
- **3 (medium)**: Mention the decision and offer to discuss. Use `AskUserQuestion` to let the user confirm the default or pick an alternative.
- **4-5 (low/detail)**: Handle with defaults. No need to ask.

After discussing a decision with the user, set `reviewed: true` on that decision in `asp.yaml`.

### Plan the implementation

For the target scope, work out:
- What workflow steps are needed to go from inputs to outputs
- How decisions map to parameters in those steps
- What tools/libraries to use
- Execution order and dependencies between steps

Present the plan to the user briefly. Once agreed, write it to `plans/<chunk_name>.md`. Create the `plans/` directory if it doesn't exist.

### Build

1. Generate universes if missing (`asp universe generate -n baseline`)
2. Build CWL workflows mapping inputs, decisions, and outputs
3. Implement workflow steps in `steps/` (single chunk) or `steps/<chunk_name>/` (multiple chunks)
4. Validate (`asp workflow validate --cwl workflows/main.cwl`)
5. Run (`asp workflow run universes/baseline.yaml --cwl workflows/main.cwl -o results/baseline/`)

### Chunk builds

When building a specific chunk, scope all work to that chunk's decisions. Chunk decisions appear under `chunks.<name>.decisions` in the spec and `chunks.<name>` in universe files.

## Completion

- "Chunk `<name>` built and results ready." Use the actual chunk name.
- If there are remaining chunks, suggest: "Run `/asp-build <next_chunk>` to continue."
- If all chunks are done: "All chunks built. The analysis is complete."
