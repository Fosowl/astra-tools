---
name: asp-plan
description: Plan how to implement an ASP analysis. Usage: /asp:plan [phase] — plan a specific phase, or the whole analysis if single-stage.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(asp:*), WebFetch, AskUserQuestion, Task
---

# /asp:plan

Plan how to implement an analysis (or a specific phase of one).

`/asp:new` defines WHAT we want. `/asp:plan` figures out HOW to do it.

**Usage:**
- `/asp:plan` — plan the whole analysis (single-stage, no phases)
- `/asp:plan <phase>` — plan a specific phase by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read `asp.yaml` to understand the specification
3. If `<phase>` was given, confirm it exists in `phases`

## Process

### Determine scope

- No argument + no `phases`: plan the root analysis
- No argument + `phases` exist: ask the user which phase to plan (or plan all sequentially)
- `<phase>` argument: plan that specific phase

### Plan the implementation

For the target scope, work out:
- What workflow steps are needed to go from inputs to outputs
- How decisions map to parameters in those steps
- What tools/libraries to use
- Execution order and dependencies between steps

### Write the plan

Present the plan to the user for review. Once agreed, write it to a planning artifact the build agent can follow.

## Restrictions

**You are a planning agent, not an implementation agent.**

You MUST NOT write implementation code (Python, R, CWL, etc.).

## Completion

- **Single-stage**: "Plan ready. Run `/asp:build` to start building."
- **Phase**: "Plan for `<name>` ready. Run `/asp:build <name>` to build it." Use the actual phase name.
- **Phase with next**: If there are more phases to plan, also mention: "Next phase to plan: `/asp:plan <next_name>`."

Then: `/clear` first for a fresh context window.
