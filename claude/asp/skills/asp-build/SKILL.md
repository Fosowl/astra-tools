---
name: asp-build
description: Build universes, create CWL workflows, and run the ASP analysis
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task
---

# /asp:build

Build and run an ASP analysis by spawning a dedicated sub-agent.

## Instructions

1. Read the agent instructions from `.claude/agents/asp-build.md`

2. Read the workflow guide from `.claude/skills/asp/workflow-guide.md`

3. Read the current `asp.yaml` to understand the specification

4. Check what universes and workflows already exist:
   ```bash
   ls universes/ 2>/dev/null
   ls workflows/ 2>/dev/null
   ```

5. Spawn a sub-agent using the Task tool:

```
Task(
  description: "ASP build - create workflows and run",
  prompt: "<agent-instructions>
{paste the full contents of .claude/agents/asp-build.md here}
</agent-instructions>

<workflow-guide>
{paste the full contents of .claude/skills/asp/workflow-guide.md here}
</workflow-guide>

<current-directory>
{current working directory}
</current-directory>

<asp-specification>
{contents of asp.yaml}
</asp-specification>

<existing-universes>
{list of files in universes/ or 'None'}
</existing-universes>

<existing-workflows>
{list of files in workflows/ or 'None'}
</existing-workflows>

<user-request>
The user invoked /asp:build. Build universes, create CWL workflows, and run the analysis.
</user-request>",
  subagent_type: "general-purpose"
)
```

## After the Sub-Agent Completes

The sub-agent will end with: **"Results are in `results/`. Run `/asp:verify` to check if they meet your research goals."**

Report this back to the user.
