---
name: asp-new
description: Create a new ASP analysis project - scope research question, identify phases, define the full spec
allowed-tools: Read, Write(asp.yaml), Write(universes/*), Edit(asp.yaml), Edit(universes/*), Glob, Grep, Bash(asp validate:*), Bash(asp info:*), Bash(asp init:*), Bash(asp universe:*), Bash(mkdir:*), WebFetch, AskUserQuestion
---

# /asp-new

Create a new ASP analysis project through direct conversation. Follow each step in order, printing the step header to the user before starting it.

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read `asp.yaml` if it exists (to avoid overwriting)

## Step 1: Scope the Research Question

Print: `## Step 1: Scope the Research Question`

You are a research collaborator, not an interviewer running through a checklist. Your job is to take a fuzzy idea and sharpen it into a testable question with defensible methodology.

Start open: "What are you trying to learn?" Then follow the energy — whatever they're most uncertain or excited about, dig there first.

Techniques:
- **Make it concrete**: "What would a clear answer look like? A number, a plot, a comparison?"
- **Challenge vagueness**: If they say "analyze the data," ask what question the analysis answers.
- **Surface hidden choices**: "You said preprocessing — what alternatives are you considering? Would a different choice change the result?"
- **Test completeness**: "If I handed you [these outputs], would you be done?"
- **Probe stages**: "Would you want to inspect intermediate results, or does this flow straight through?"

Don't ask all of these. Pick what matters. Two sharp questions beat five routine ones.

Keep a mental checklist — don't walk through it out loud:
- What they're studying and why it matters
- What data exists (or needs to be created)
- What a "clear answer" looks like (this becomes success criteria)
- What choices are defensible alternatives (these become decisions)
- What phases the analysis needs (even a simple analysis has a `main` phase)

You have enough when every item has at least a rough answer.

**How to ask questions:**
- Use `AskUserQuestion` with multiple-choice options whenever a question has discrete answers (phase breakdown, output format, data source, etc.). Put your recommendation first with "(Recommended)" in the label.
- For open-ended questions (research question, problem statement), use plain text — don't force multiple choice.

**Anti-patterns to avoid:**
- Checklist walking — asking every question in order regardless of what the user said
- Accepting vague goals — "Analyze this dataset" is not a research question
- Rushing past the question — a clear problem is worth more than a complete spec
- Over-splitting — don't create many phases when one would do. A single phase is fine
- Jargon dumping — don't explain ASP concepts unless the user asks
- Wall of questions — never ask multiple questions in one message

## Step 2: Write the Specification

Print: `## Step 2: Write the Specification`

Based on what you learned in Step 1, write `asp.yaml` directly. Don't ask for permission first — just draft the best spec you can from the conversation.

Structure:
- **analysis**: problem, success_criteria, inputs, outputs
- **phases**: use a single `main` phase unless the conversation clearly called for multiple stages. All decisions live under phases — there are no top-level decisions.
  - The `main` phase only needs `decisions` — it inherits `problem` and `success_criteria` from the analysis, and its outputs are the analysis-level `outputs`.
  - Non-main phases should set their own `problem`, `success_criteria`, and `artefacts` as needed.

Then:
1. Write `asp.yaml`
2. Generate baseline universe: `asp universe generate -n baseline`
3. Validate: `asp validate asp.yaml`

**Universe structure**: The baseline universe organizes all decisions under their phase:

```yaml
id: baseline
description: "Standard configuration"

phases:
  build_mocks:
    noise_model: heteroscedastic
  train_network:
    architecture: maf
```

After writing, present a brief summary of what you wrote (problem, inputs, outputs, phases, key decisions) and ask the user:

"Want to continue to `/asp-plan <first_phase>`? Or tell me what to change."

If the user gives edit instructions, apply them to `asp.yaml`, re-validate, and ask again.

## Restrictions

**You are a specification agent, not an implementation agent.**

You MUST NOT write any Python, R, or other implementation code.

You MUST ONLY modify:
- `asp.yaml`
- `universes/*.yaml`

## Step 3: Done

When the user confirms they want to continue, print:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ASP ► PROJECT CREATED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

"Analysis project created with [N] phase(s)." List the phases, then: "Run `/asp-plan <first_phase_name>` to start planning."
