---
name: asp-verify
description: Verify analysis results meet research goals. Usage: /asp-verify [chunk] — verify a specific chunk, or the whole analysis.
allowed-tools: Read, Glob, Grep, Bash, Task
---

# /asp-verify

Verify that analysis results meet the original research goals and success criteria.

**Usage:**
- `/asp-verify` — verify all chunks + parent-level criteria
- `/asp-verify <chunk>` — verify a specific chunk by name

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read `asp.yaml` for problem statement and success criteria
3. Inventory results (`results/` or chunk-specific results)

## Process

### Determine scope

- No argument: verify all chunks against their criteria, then analysis-level criteria
- `<chunk>` argument: verify only that chunk's results against its success criteria
- For `main` chunk: use the analysis-level `success_criteria` (the `main` chunk doesn't define its own)

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

- **Complete**: "Chunk `<name>` verified." If there are remaining chunks, suggest: "Run `/clear`, then `/asp-plan <next_chunk>` to start the next chunk." If all chunks are done: "All chunks verified. The analysis successfully addresses the research question."
- **Gaps found**: "Gaps identified in `<name>`. Run `/asp-plan <name>` to refine the approach." Use the actual chunk name.
