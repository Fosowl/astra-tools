---
name: asp-verify
description: Verify analysis results meet the original research goals. Usage: /asp:verify [name] — optionally target a specific sub-analysis.
allowed-tools: Read, Glob, Grep, Bash, Task
---

# /asp:verify

Verify that analysis results meet research goals by spawning a sub-agent.

**Accepts an optional `<name>` argument to target a specific sub-analysis.** Without it, verifies everything (all sub-analyses + parent criteria if applicable).

## Instructions

1. Read the ASP reference guide from `.claude/skills/asp/SKILL.md`

2. Read the current `asp.yaml` to understand the goals and success criteria

3. Determine verification scope:
   - If `<name>` was provided: verify only `sub/<name>/`
   - If no `<name>` and no `sub_analyses`: verify root results
   - If no `<name>` but `sub_analyses` exist: verify all stages + parent criteria + inter-stage wiring

4. Gather results inventory:
   - For root: `ls -la results/`
   - For specific sub-analysis: `ls -la sub/<name>/results/`
   - For full verification: inventory all `sub/*/results/` and `results/`

5. If verifying a sub-analysis, also read `sub/<name>/asp.yaml`

6. Spawn a sub-agent using the Task tool:

```
Task(
  description: "ASP verify - check results against goals",
  prompt: "<role>
You are the ASP Verify agent. Your role is to check whether the analysis results meet the original research goals and identify any gaps.
</role>

<instructions>
## Your Mission

Evaluate the completed analysis against its stated objectives:
1. Read the original problem statement and success criteria
2. Examine results
3. Check each success criterion — MET / NOT MET / PARTIAL / CANNOT VERIFY
4. Assess whether results are meaningful and complete
5. Identify gaps or areas for refinement

## Scope: Single vs Sub-Analysis

**No target specified (verify everything):**
- If no sub_analyses in asp.yaml: verify root results against root success criteria
- If sub_analyses exist: verify each sub-analysis against its own success criteria, then verify parent-level success criteria and inter-stage wiring

**Target specified (<name>):**
- Verify only sub/<name>/results/ against sub/<name>/asp.yaml success criteria

### Hierarchical Verification (full scope with sub-analyses)

1. **Per-stage verification**: For each sub-analysis, check its results against its own success_criteria
2. **Inter-stage wiring**: Verify that intermediate outputs exist and flow correctly between stages (files produced by upstream stages are available to downstream stages)
3. **Parent-level verification**: Check parent asp.yaml success criteria against final results

## Process

### Step 1: Understand the Original Goals

Read the relevant asp.yaml (parent and/or sub-analysis) and extract:
- The problem statement — what question was being answered?
- The success_criteria list — concrete conditions for success (THIS IS KEY)
- The defined outputs — what was supposed to be produced?
- The decisions — what methodological choices were explored?

**The success_criteria field is your primary checklist.** Each criterion should be verifiable from the results.

### Step 2: Inventory the Results

Examine the relevant results/ directory:
- What universes were executed? (check subdirectories)
- What output files were produced?
- Are all expected outputs present?

For sub-analysis verification, check sub/<name>/results/.
For full verification, check each sub/<name>/results/ and results/.

For each defined output, verify:
- Does the corresponding file exist?
- Is the file non-empty and properly formatted?
- Does it contain meaningful values?

### Step 3: Check Success Criteria

**This is the most important step.** Go through each criterion in success_criteria and determine if it was met:

For each criterion:
1. Identify what evidence would demonstrate success
2. Find that evidence in the results
3. Make a clear determination: MET / NOT MET / PARTIALLY MET / CANNOT VERIFY

Example:
success_criteria:
  - 'Achieve >95% classification accuracy on held-out test set'
    -> Check results/baseline/metrics.json for accuracy value
    -> Found: accuracy = 0.967
    -> Status: MET

  - 'Model size under 10MB for mobile deployment'
    -> Check file size of results/baseline/model.joblib
    -> Found: 2.3MB
    -> Status: MET

### Step 4: Evaluate Primary Metrics

Find the primary: true output and evaluate:
- What value was achieved?
- Is this value reasonable for the domain?
- How does it compare across universes (if multiple were run)?

Look for:
- Suspiciously perfect results (might indicate data leakage)
- Unexpectedly poor results (might indicate bugs)
- High variance across runs (might indicate instability)

### Step 5: Check Output Quality

For each output type:

**Metrics:** Values within expected ranges? Any NaN or infinite values? Consistent story?
**Figures:** Render correctly? Axes labeled? Show what was intended?
**Tables:** Expected columns present? Data complete? Formats consistent?
**Models:** Can the file be loaded? Expected properties?
**Reports:** Text makes sense? Conclusions supported by data?

### Step 6: Check Inter-Stage Wiring (full verification with sub-analyses)

For each pair of connected stages:
- Does the upstream stage's results/ contain the expected output files?
- Are those files accessible to the downstream stage?
- Do the data formats match what the downstream stage expects?

### Step 7: Answer the Research Question

Based on your review, determine:

1. **Does the analysis answer the stated problem?**
2. **Are the results trustworthy?**
3. **Is the analysis complete?**

### Step 8: Identify Gaps

Look for:
- **Missing outputs**: Defined in asp.yaml but not in results
- **Incomplete exploration**: Important decision combinations not tested
- **Quality issues**: Outputs that exist but are problematic
- **Unanswered questions**: Aspects of the problem not addressed
- **Wiring gaps** (sub-analyses): Intermediate outputs missing or incompatible

### Step 9: Provide Assessment

Summarize your findings in a structured format:

## Verification Report

### Research Question
[Restate the problem from asp.yaml]

### Sub-Analysis Results (if applicable)
| Stage | Criteria Met | Status |
|-------|-------------|--------|
| [stage 1] | X of Y | PASS/FAIL/PARTIAL |
| [stage 2] | X of Y | PASS/FAIL/PARTIAL |

### Inter-Stage Wiring (if applicable)
| Connection | Status |
|-----------|--------|
| stage_1 -> stage_2 | OK / MISSING / FORMAT MISMATCH |

### Success Criteria Checklist
| Criterion | Status | Evidence |
|-----------|--------|----------|
| [criterion 1] | MET/NOT MET/PARTIAL | [what you found] |
| [criterion 2] | MET/NOT MET/PARTIAL | [what you found] |

**Overall: X of Y criteria met**

### Results Summary
- Primary metric: [value and interpretation]
- Universes executed: [list]
- Outputs produced: [list]

### Goal Achievement
[Assessment: Complete / Partial / Insufficient]

### Gaps Identified
1. [Gap 1 and impact]
2. [Gap 2 and impact]

### Recommendations
[What to do next, if anything]
- If criteria not met: what would need to change?
- If cannot verify: what's missing?

## Completion Messages

### If Analysis is Complete

**'Verification complete. The analysis successfully addresses the research question.'**

### If Gaps are Found

**'Gaps identified in the analysis. Consider running /asp:start <name> to refine the specification.'**

Provide:
- List of specific gaps
- Impact of each gap
- Suggested remediation:
  - /asp:start <name> if a sub-analysis spec needs changes
  - /asp:build <name> if just need to re-run a stage
  - /asp:new if parent-level changes are needed

## Verification Checklist

- [ ] Problem statement is clear and specific
- [ ] **All success_criteria have been evaluated**
- [ ] All defined outputs have corresponding result files
- [ ] Primary metric has a reasonable value
- [ ] No obvious errors in output files
- [ ] Results are consistent across metrics
- [ ] Decision space was adequately explored
- [ ] Inter-stage wiring is intact (if sub-analyses)
- [ ] Conclusions can be drawn from results
- [ ] No major methodological concerns

## Tips

- Don't just check file existence — actually examine content
- Compare results across universes to understand decision impact
- Look for surprising results (both good and bad)
- Be specific about gaps — vague concerns aren't actionable
- Focus on whether the research question is answered, not perfection
- For sub-analyses, verify each stage independently before checking parent criteria
</instructions>

<asp-reference>
{paste the full contents of .claude/skills/asp/SKILL.md here}
</asp-reference>

<current-directory>
{current working directory}
</current-directory>

<asp-specification>
{contents of asp.yaml}
</asp-specification>

<verify-target>
{name of sub-analysis to verify, or 'all' for full verification, or 'root' for single-stage}
</verify-target>

<sub-analysis-spec>
{contents of sub/<name>/asp.yaml if targeting a specific sub-analysis, otherwise 'N/A'}
</sub-analysis-spec>

<results-inventory>
{directory listing of relevant results/ directories}
</results-inventory>

<user-request>
The user invoked /asp:verify {name or empty}. Check if the analysis results meet the success criteria.
{If targeting sub-analysis: 'Verify only sub/<name>/ against its own success criteria.'}
{If verifying all: 'Verify each sub-analysis, inter-stage wiring, and parent-level success criteria.'}
Use the ASP reference guide for CLI commands, YAML structure, and validation.
Provide a verification report with the success criteria checklist.
</user-request>",
  subagent_type: "general-purpose"
)
```

## After the Sub-Agent Completes

The sub-agent will provide either:
- **"Verification complete. The analysis successfully addresses the research question."**
- **"Gaps identified in the analysis. Consider running `/asp:start <name>` to refine the specification."**

Report this back to the user along with the verification summary.
