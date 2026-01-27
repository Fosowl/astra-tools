---
name: asp-verify
description: Verify analysis results meet research goals. Usage: /asp:verify [phase] — verify a specific phase, or the whole analysis.
allowed-tools: Read, Glob, Grep, Bash, Task
---

# /asp:verify

Verify that analysis results meet the original research goals and success criteria.

**Usage:**
- `/asp:verify` — verify the whole analysis (all phases + parent criteria if applicable)
- `/asp:verify <phase>` — verify a specific phase by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read `asp.yaml` for problem statement and success criteria
3. Inventory results (`results/` or phase-specific results)

## Process

### Determine scope

- No argument + no `phases`: verify root results against root success criteria
- No argument + `phases` exist: verify each phase against its own criteria, then parent-level criteria
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

- **Complete**: "Verification complete. The analysis successfully addresses the research question."
- **Gaps found**: "Gaps identified. Consider running `/asp:plan <phase>` to refine the approach."
