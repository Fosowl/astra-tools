---
name: asp-build
description: Build an ASP analysis chunk. Usage: /asp-build [chunk] — plan, then build and run a specific chunk.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, WebFetch, AskUserQuestion, EnterPlanMode
---

# /asp-build

Build and run an analysis chunk in two phases: **Plan** then **Build**.

`/asp-new` defines WHAT we want. `/asp-build` figures out HOW to do it and executes.

**Usage:**
- `/asp-build` — build all chunks in order
- `/asp-build <chunk>` — build a specific chunk by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read the workflow guide: `.claude/skills/asp/workflow-guide.md`
3. Read `asp.yaml` to understand the specification
4. If `<chunk>` was given, confirm it exists in `chunks`

## Process

### Determine scope

- No argument: if there are multiple chunks, use `AskUserQuestion` to ask which chunk to work on (list chunk names as options). Work on ONE chunk at a time.
- `<chunk>` argument: work on that specific chunk

### Check for existing plan

If the chunk already has a `plan:` field in asp.yaml AND the plan file exists, ask:

> "A plan already exists for this chunk: `plans/<chunk>.plan.md`. Want to rebuild from this plan, or re-plan from scratch?"

If rebuilding from existing plan, skip to [Phase 2: Build](#phase-2-build).

---

## Phase 1: Plan

Print: `## Phase 1: Planning — <chunk name>`

Use the **Task tool with `subagent_type: Plan`** to spawn a planning agent. Give it:
- The full `asp.yaml` content
- The workflow guide content (`.claude/skills/asp/workflow-guide.md`)
- The chunk name to plan for
- Any existing code in `steps/` or `workflows/` (if re-planning)

The planning agent should produce a plan covering:

1. **Approach** — High-level strategy for implementing this chunk
2. **Dependencies** — Python packages needed (and why)
3. **Workflow structure** — CWL workflow design:
   - Which steps, how they connect
   - Input/output wiring between steps
4. **Decision mapping** — How each ASP decision translates to code:
   - Which decision values affect which steps
   - How option values map to implementation choices
5. **Data flow** — File formats between steps, how data moves through the pipeline
6. **Step implementations** — For each step:
   - What it does
   - Inputs and outputs (types, formats)
   - Key implementation details or library calls
7. **Edge cases** — Anything tricky: missing data handling, decision interactions, constraint implications
8. **File manifest** — Complete list of files to create:
   ```
   workflows/main.cwl          — Main workflow definition
   steps/preprocess.cwl         — Preprocessing step CWL
   steps/preprocess.py          — Preprocessing implementation
   steps/train.cwl              — Training step CWL
   steps/train.py               — Training implementation
   ...
   ```

### Write the plan

Write the plan to `plans/<chunk>.plan.md`.

Update `asp.yaml` to link the plan:
```yaml
chunks:
  <chunk>:
    plan: plans/<chunk>.plan.md
    ...
```

### User review

Present a summary of the plan to the user:
- Key approach decisions
- Libraries chosen
- Workflow structure (steps and connections)
- Files to be created

Then ask:

> "Plan written to `plans/<chunk>.plan.md`. Review it and tell me what to change, or say 'build' to proceed."

Wait for user approval before proceeding. If they request changes, update the plan file and re-summarize.

---

## Phase 2: Build

Print: `## Phase 2: Building — <chunk name>`

Start fresh — read only what's needed:

1. Read `asp.yaml` (the spec)
2. Read `plans/<chunk>.plan.md` (the plan)
3. Read the workflow guide: `.claude/skills/asp/workflow-guide.md`

Then execute the plan:

1. Generate universes if missing (`asp universe generate -n baseline`)
2. Install any dependencies the plan identified
3. Build CWL workflows following the plan's workflow structure
4. Implement each step following the plan's step specifications
5. Validate (`asp workflow validate --cwl workflows/main.cwl`)
6. Run (`asp workflow run universes/baseline.yaml --cwl workflows/main.cwl -o results/baseline/`)

### Chunk builds

When building a specific chunk, scope all work to that chunk's decisions. Chunk decisions appear under `chunks.<name>.decisions` in the spec and `chunks.<name>` in universe files.

### If something goes wrong

If the build fails (validation errors, runtime errors, etc.):
- Fix the issue based on the error
- Do NOT modify the plan unless the plan itself was wrong
- If the plan was wrong (e.g., wrong library API, missing step), update the plan file to reflect what actually worked, so it stays accurate as documentation

---

## Completion

- "Chunk `<name>` built. Results saved to `results/<universe>/`." Use the actual chunk name.
- If there are remaining chunks, suggest: "Run `/asp-build <next_chunk>` to continue."
- If all chunks are done: "All chunks built. The analysis is complete."
