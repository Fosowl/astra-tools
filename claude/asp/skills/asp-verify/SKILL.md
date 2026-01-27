---
name: asp-verify
description: Verify analysis results meet research goals. Usage: /asp-verify [phase] — verify a specific phase, or the whole analysis.
allowed-tools: Read, Glob, Grep, Bash, Task
---

# /asp-verify

Verify that analysis results meet the original research goals and success criteria.

**Usage:**
- `/asp-verify` — verify all phases + parent-level criteria
- `/asp-verify <phase>` — verify a specific phase by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read `asp.yaml` for problem statement and success criteria
3. Inventory results (`results/` or phase-specific results)

## Process

### Determine scope

- No argument: verify all phases against their criteria, then parent-level criteria
- `<phase>` argument: verify only that phase's results against its success criteria

### Verification

For each success criterion, determine: **MET / NOT MET / PARTIAL / CANNOT VERIFY**

Check:
- All expected outputs exist and are non-empty
- Primary metrics are within reasonable ranges
- Results are consistent across universes (if multiple were run)
- No signs of data leakage or methodological issues

### Report

Produce a verification report with:
- Success criteria checklist (criterion → status → evidence)
- Overall assessment (Complete / Partial / Insufficient)
- Gaps identified and recommendations

## Completion

- **Complete**: "Phase `<name>` verified." If there are remaining phases, suggest: "Run `/clear`, then `/asp-plan <next_phase>` to start the next phase." If all phases are done: "All phases verified. The analysis successfully addresses the research question."
- **Gaps found**: "Gaps identified in `<name>`. Run `/asp-plan <name>` to refine the approach." Use the actual phase name.
