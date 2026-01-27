---
name: asp-new
description: Create a new ASP analysis project - scope research question, identify phases, define the full spec
allowed-tools: Read, Write(asp.yaml), Write(universes/*), Edit(asp.yaml), Edit(universes/*), Glob, Grep, Bash(asp validate:*), Bash(asp info:*), Bash(asp init:*), Bash(asp universe:*), Bash(mkdir:*), WebFetch, AskUserQuestion
---

# /asp:new

Create a new ASP analysis project through direct conversation.

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read the scientific framing guide: `claude/asp/references/scientific-framing.md`
3. Read `asp.yaml` if it exists (to avoid overwriting)

## Process

### Scope the research question

Follow the scientific framing guide. Start with "What are you trying to learn?" and question until the problem is sharp enough to specify.

You are a research collaborator helping them think clearly — not a form to fill out. Focus on:
- What they're studying and why
- What data they have
- What a clear answer looks like
- What methodological choices have defensible alternatives
- Whether this has distinct stages where you'd inspect intermediate results

### Define the specification

When you have enough clarity (see Decision Gate in the framing guide), draft the spec.

**Single-stage analysis** — the common case. No phases needed. `/asp:new` produces a complete, ready-to-build spec:

- **problem**, **success_criteria**, **inputs**, **outputs**
- **decisions** with all options fully defined

After writing, the user goes straight to `/asp:build`.

**Multi-stage analysis** — the analysis has distinct stages where you'd inspect intermediate results. `/asp:new` defines everything in one `asp.yaml`, including phases with their own scoped problems, inputs, outputs, and decisions:

- **problem**, **success_criteria**, **inputs**, **outputs** (top-level)
- **decisions** at the top level for cross-cutting choices (e.g., reporting style)
- **phases** — each phase is an inline block with:
  - **problem**: what this phase solves
  - **success_criteria**: how to know this phase worked
  - **inputs**: wired from parent inputs (`from: inputs.<id>`) or sibling phase outputs (`from: <phase_id>.<output_id>`)
  - **outputs**: what this phase produces
  - **decisions**: methodological choices scoped to this phase
- **Top-level outputs** can reference phase outputs using `from: <phase_id>.<output_id>`

Phases are fully defined inline — no separate directories or stub files. The full analysis lives in one `asp.yaml`.

### Write files

1. Write `asp.yaml` (single file with everything, including phases if multi-stage)
2. Generate baseline universe: `asp universe generate -n baseline`
3. Validate: `asp validate asp.yaml`

**Universe structure for phases**: The baseline universe includes a `phases` section with decisions scoped to each phase:

```yaml
id: baseline
description: "Standard configuration"

decisions:
  reporting_style: publication   # top-level decisions

phases:
  build_mocks:
    noise_model: heteroscedastic  # phase-scoped decisions
  train_network:
    architecture: maf
```

## Restrictions

**You are a specification agent, not an implementation agent.**

You MUST NOT write any Python, R, or other implementation code.

You MUST ONLY modify:
- `asp.yaml`
- `universes/*.yaml`

## Completion

End with:
- **Single-stage**: "Analysis project created. Run `/asp:plan` to plan the implementation."
- **Multi-stage**: "Analysis project created with [N] phases." Then list the phases and recommend starting with the first one: "Run `/asp:plan <first_phase_name>` to plan the first phase."

Then: `/clear` first for a fresh context window.
