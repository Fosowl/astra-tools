---
name: asp-plan
description: Plan how to implement an ASP analysis chunk. Usage: /asp-plan [chunk] — plan a specific chunk, or all chunks.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(asp:*), WebFetch, AskUserQuestion, Task
---

# /asp-plan

Plan how to implement an analysis chunk.

`/asp-new` defines WHAT we want. `/asp-plan` figures out HOW to do it.

**Usage:**
- `/asp-plan` — plan all chunks (asks which to start with, or goes in order)
- `/asp-plan <chunk>` — plan a specific chunk by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read `asp.yaml` to understand the specification
3. If `<chunk>` was given, confirm it exists in `chunks`

## Process

### Determine scope

- No argument: if there are multiple chunks, use `AskUserQuestion` to ask which chunk to plan (list chunk names as options). Plan ONE chunk at a time.
- `<chunk>` argument: plan that specific chunk

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

### Write the plan

Present the plan to the user for review. Once agreed, write it to `plans/<chunk_name>.md`.

The plan file should include:
- **Steps**: Ordered list of workflow steps from inputs to outputs
- **Decision mapping**: How each decision maps to step parameters
- **Tools/libraries**: What to use for each step
- **Dependencies**: Execution order between steps

Create the `plans/` directory if it doesn't exist.

## Restrictions

**You are a planning agent, not an implementation agent.**

You MUST NOT write implementation code (Python, R, CWL, etc.).

## Completion

- "Plan for `<name>` ready. Run `/asp-build <name>` to build it." Use the actual chunk name.
- **Do NOT suggest planning the next chunk.** The workflow is plan → build → verify for each chunk. Only `/asp-verify` advances to the next chunk.
