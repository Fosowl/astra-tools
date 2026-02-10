---
name: asp-migrate
description: Migrate an existing codebase to ASP - analyze code, extract decisions, draft specification
allowed-tools: Read, Write(asp.yaml), Write(universes/*), Write(MIGRATION.md), Edit(asp.yaml), Edit(MIGRATION.md), Glob, Grep, Bash(asp validate:*), Bash(asp info:*), Bash(asp universe:*), Task, AskUserQuestion
---

# /asp-migrate

Migrate an existing codebase to ASP by analyzing the code and drafting the specification.

## Prerequisites

Run `asp migrate <directory>` first to create the scaffolding (asp.yaml placeholder, MIGRATION.md, .claude/ settings).

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read the decisions reference: fetch from `https://raw.githubusercontent.com/LightconeResearch/ASP/main/docs/decisions-reference.md`
3. Read `asp.yaml` to see current state
4. Read `MIGRATION.md` to see the checklist

## Step 1: Understand the Project

Print: `## Step 1: Understand the Project`

Ask ONE high-level question to understand the project:

"Before I analyze the codebase, describe in a few sentences: **What does this analysis do, and what question is it trying to answer?**"

Wait for the user's response. This gives you context for interpreting the code.

## Step 2: Explore the Codebase

Print: `## Step 2: Exploring the Codebase`

Use the `Task` tool with `subagent_type=Explore` to understand the codebase structure:
- Entry points and main scripts
- Configuration files
- Model/algorithm implementations
- Data processing pipelines
- Output generation

Look for decision candidates (see decisions-reference.md):
- **Method choices**: Algorithm selection, model architecture, statistical tests
- **Parameter choices**: Hyperparameters with scientific meaning (priors, thresholds)
- **Data choices**: Preprocessing approaches, feature selection, data splits

**Ignore** implementation details that aren't scientifically meaningful:
- Library versions, logging levels, file paths
- Performance optimizations without scientific impact
- Code organization choices

## Step 3: Draft the Specification

Print: `## Step 3: Drafting the Specification`

Based on your analysis, draft `asp.yaml`:

### Analysis Section
- **name**: Project name
- **problem**: Research question (from user's description + code analysis)
- **success_criteria**: What would constitute a successful result?
- **inputs**: Data sources found in the code
- **outputs**: Results, figures, tables the code produces

### Chunks
- Use a single `main` chunk unless the codebase has clear pipeline stages
- If there are distinct stages (data prep → training → evaluation), create separate chunks

### Decisions
For each decision candidate found:

```yaml
chunks:
  main:
    decisions:
      decision_id:
        label: "Human-readable name"
        type: method | parameter | data
        importance: 1-5  # 1=critical, 5=minor
        rationale: "Why this choice matters scientifically"
        default: current_choice  # What the code currently does
        options:
          current_choice:
            label: "Current Implementation"
            description: "What the code does now"
          alternative:
            label: "Alternative Approach"
            description: "Reasonable alternative (if identifiable)"
```

**Decision filtering rules**:
- Include: Choices that affect scientific conclusions
- Include: Choices a reviewer might question
- Include: Choices with reasonable alternatives
- Exclude: Pure implementation details
- Exclude: Choices with only one reasonable option

## Step 4: Update MIGRATION.md

Update `MIGRATION.md` with:
- Check off completed items
- Fill in the "Decision Candidates" table
- List files reviewed under "Files to Review"
- Add any notes about uncertainties or areas needing user input

## Step 5: Validate and Present

Print: `## Step 4: Validation`

1. Run `asp validate asp.yaml`
2. If validation fails, fix issues
3. Generate baseline universe: `asp universe generate -n baseline`
4. Validate universe: `asp validate universes/baseline.yaml`

Then present a summary:
- Problem statement (1-2 sentences)
- Number of inputs/outputs
- Number of decisions extracted
- Chunk structure
- Any decisions that need user review (mark as `reviewed: false`)

Ask: "Review the specification in `asp.yaml`. What should I change?"

## Step 6: Done

When the user confirms they're satisfied, print:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ASP ► MIGRATION COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

"Codebase migrated to ASP with [N] decision(s) in [M] chunk(s)."

Suggest next steps:
- "Run `/asp-build` to create/update the CWL workflow"

## Restrictions

**You are a specification agent, not an implementation agent.**

You MUST NOT modify any existing code files (.py, .r, .jl, etc.).

You MUST ONLY create/modify:
- `asp.yaml`
- `universes/*.yaml`
- `MIGRATION.md`

## Tips

- When uncertain whether something is a decision, err on the side of including it — the user can remove it
- Current implementation should always be an option (usually the default)
- Don't invent alternatives you're not confident about — just note "alternatives TBD"
- If the codebase is complex, focus on the highest-importance decisions first
