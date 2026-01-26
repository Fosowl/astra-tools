---
name: asp-start
description: Start a new ASP analysis - define problem, inputs, outputs, and decisions
allowed-tools: Read, Write(asp.yaml), Write(universes/*), Edit(asp.yaml), Edit(universes/*), Glob, Grep, Bash(asp validate:*), Bash(asp info:*), Bash(asp universe:*), WebFetch, Task
---

# /asp:start

Start or refine an ASP analysis specification by spawning a dedicated sub-agent.

**This agent only writes to `asp.yaml` and `universes/` - no implementation code.**

## Instructions

1. Read the agent instructions from `.claude/agents/asp-start.md`

2. Read the current `asp.yaml` if it exists (to provide context)

3. Spawn a sub-agent using the Task tool:

```
Task(
  description: "ASP start - define analysis spec",
  prompt: "<agent-instructions>
{paste the full contents of .claude/agents/asp-start.md here}
</agent-instructions>

<current-directory>
{current working directory}
</current-directory>

<existing-spec>
{contents of asp.yaml if it exists, otherwise 'No asp.yaml found - starting fresh'}
</existing-spec>

<user-request>
The user invoked /asp:start. Help them define their analysis specification.
Guide them through problem, success_criteria, inputs, outputs, and decisions.
Only write to asp.yaml and universes/ - no implementation code.
</user-request>",
  subagent_type: "general-purpose"
)
```

## After the Sub-Agent Completes

The sub-agent will end with: **"asp.yaml is ready. Run `/asp:build` when you're ready to create universes and build workflows."**

Report this back to the user.
