---
name: asp-new
description: Create a new ASP analysis project - scope research question, identify sub-analyses, define top-level spec
allowed-tools: Read, Write(asp.yaml), Write(universes/*), Write(sub/*/asp.yaml), Write(sub/*/universes/*), Edit(asp.yaml), Edit(universes/*), Glob, Grep, Bash(asp validate:*), Bash(asp info:*), Bash(asp init:*), Bash(asp universe:*), Bash(mkdir:*), WebFetch, AskUserQuestion
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
- Whether this has distinct stages

### Define the specification

When you have enough clarity (see Decision Gate in the framing guide), draft the spec.

**Single-stage analysis** — the common case. No sub-analyses needed. `/asp:new` produces a complete, ready-to-build spec:

- **problem**, **success_criteria**, **inputs**, **outputs**
- **decisions** with all options fully defined

After writing, the user goes straight to `/asp:build`.

**Multi-stage analysis** — the analysis has distinct stages where you'd inspect intermediate results. `/asp:new` defines the parent spec and wiring, but leaves each stage as a stub:

- **problem**, **success_criteria**, **inputs**, **outputs** (top-level)
- **sub_analyses** with name, description, and wiring (`inputs_from`, `outputs_to`)
- **No decisions at the parent level** — decisions live inside each sub-analysis

Each stage gets fleshed out later via `/asp:start <name>`, which scopes that stage's own decisions, inputs/outputs (constrained by wiring), and success criteria.

### Write files

1. Write `asp.yaml`
2. If multi-stage, create `sub/<name>/` directories with stub `asp.yaml` for each stage
3. Generate baseline universe: `asp universe generate -n baseline`
4. Validate: `asp validate asp.yaml`

## Restrictions

**You are a specification agent, not an implementation agent.**

You MUST NOT write any Python, R, or other implementation code.

You MUST ONLY modify:
- `asp.yaml`
- `universes/*.yaml`
- `sub/<name>/asp.yaml`
- `sub/<name>/universes/*.yaml`

## Completion

End with:
- **Single-stage**: "Analysis project created. Run `/asp:build` to start building."
- **Multi-stage**: "Analysis project created. Run `/asp:start <name>` to scope each stage, then `/asp:build` when ready."
