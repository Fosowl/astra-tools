---
name: asp-verify
description: Verify analysis results meet the original research goals
allowed-tools: Read, Glob, Grep, Bash, Task
---

# /asp:verify

Verify that analysis results meet research goals by spawning a dedicated sub-agent.

## Instructions

1. Read the agent instructions from `.claude/agents/asp-verify.md`

2. Read the current `asp.yaml` to understand the goals and success criteria

3. Check what results exist:
   ```bash
   ls -la results/ 2>/dev/null
   ```

4. Spawn a sub-agent using the Task tool:

```
Task(
  description: "ASP verify - check results against goals",
  prompt: "<agent-instructions>
{paste the full contents of .claude/agents/asp-verify.md here}
</agent-instructions>

<current-directory>
{current working directory}
</current-directory>

<asp-specification>
{contents of asp.yaml}
</asp-specification>

<results-inventory>
{directory listing of results/}
</results-inventory>

<user-request>
The user invoked /asp:verify. Check if the analysis results meet the success criteria defined in asp.yaml.
Provide a verification report with the success criteria checklist.
</user-request>",
  subagent_type: "general-purpose"
)
```

## After the Sub-Agent Completes

The sub-agent will provide either:
- **"Verification complete. The analysis successfully addresses the research question."**
- **"Gaps identified in the analysis. Consider running `/asp:start` to refine the specification."**

Report this back to the user along with the verification summary.
