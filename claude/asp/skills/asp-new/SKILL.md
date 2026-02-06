---
name: asp-new
description: Create a new ASP analysis project - scope research question, structure chunks, identify decisions with literature support
allowed-tools: Read, Write(asp.yaml), Write(universes/*), Edit(asp.yaml), Edit(universes/*), Glob, Grep, Bash(asp:*), Bash(mkdir:*), WebSearch, WebFetch, AskUserQuestion
---

# /asp-new

Create a new ASP analysis project through conversation. Build the spec iteratively so the user can watch it take shape in the navigator.

## References

- [ASP Reference](./../asp/SKILL.md) — core concepts, CLI, validation
- [Decision Guide](./decision-guide.md) — how to identify and structure decisions

## Setup

1. Read `asp.yaml` if it exists (to understand context or avoid overwriting)
2. Note the analysis directory for later

---

## Phase 1: Research Question

Print: `## Phase 1: Research Question`

Start with an open question:

> "What are you trying to learn? Describe the question in your own words."

Then sharpen:
- "What would a clear answer look like?" (becomes success criteria)
- "Why does this matter?" (context for decisions)

Don't checklist-walk. Follow what the user is uncertain or excited about.

**Write to asp.yaml:**
```yaml
version: "1.0"
analysis:
  name: "<analysis name>"
  problem: |
    <problem statement from conversation>
  success_criteria:
    - "<concrete criterion>"
```

This gives the user something to see in the navigator immediately.

---

## Phase 2: Analysis Structure

Print: `## Phase 2: Analysis Structure`

Understand the pipeline:

> "Walk me through how you'd do this step by step. What happens first? What would you want to check before moving on?"

From this, identify **chunks**:
- Single `main` chunk if it's a straightforward analysis
- Multiple chunks if there are clear stages with inspectable outputs

For multi-chunk analyses, map:
- What does each chunk produce? (artefacts)
- What does the next chunk consume?
- What decisions belong where?

Then ask:

> "Want to fully scope all chunks now, or start with [first chunk]?"

**Update asp.yaml** with chunk structure:
```yaml
analysis:
  inputs:
    - id: <input_id>
      type: data
      source: "<path or URL>"
  outputs:
    - id: <output_id>
      type: <figure|table|data|report>

chunks:
  first_chunk:
    problem: "What this chunk accomplishes"
    artefacts:
      - id: intermediate_output
        type: data

  second_chunk:
    problem: "What this chunk accomplishes"
    # decisions TBD
```

---

## Phase 3: Deep Dive

Print: `## Phase 3: Deep Dive — [chunk name]`

For each chunk being scoped, explore:

1. **Decisions** — What choices matter? See [decision-guide.md](./decision-guide.md)
2. **Data** — What does the input look like? (characteristics that affect decisions)
3. **Assumptions** — What could go wrong? What's load-bearing?

This is one exploratory conversation, not a rigid sequence. Cover what's relevant.

**Update asp.yaml incrementally** as decisions are identified. Don't wait until the end.

### Literature Notes

As methods are mentioned, note papers for Phase 4:
- Ask: "Are there specific papers that should inform this?"
- Note any papers/methods the user mentions
- Don't extract insights yet — that happens in Phase 4

### Tracking Reviewed Decisions

When the user explicitly weighs in on a decision, mark it `reviewed: true` in the spec. Decisions you infer or fill with defaults stay unreviewed — `/asp-build` will surface those.

---

## Phase 4: Literature

Print: `## Phase 4: Literature`

Ensure key decisions have literature support.

1. **Survey** — List decisions without insight links
2. **Ask** — "These decisions don't have literature support yet: [list]. Want me to search, or do you have papers in mind?"
3. **Search** — `WebSearch` for "[method] [domain]" per decision
4. **Download** — `asp paper add <doi>` for each paper
5. **Extract** — For each paper:
   - Read the PDF
   - Extract 1-2 insights relevant to decisions
   - Add to asp.yaml with quote evidence (see [Insight Extraction](#insight-extraction))
6. **Link** — Add insight refs to decision options

Target: 1-2 papers per major decision. Skip if user explicitly declines.

---

## Checkpoint

> "Anything else that should inform this analysis?"

Review the spec with the user. Update asp.yaml with any additions.

---

## Finalize

Print: `## Finalizing`

1. Validate: `asp validate asp.yaml`
2. Fix any validation errors
3. Generate baseline universe: `asp universe generate -n baseline`

Present a brief summary:
- Problem statement
- Chunks and their purposes
- Key decisions (noting which are reviewed)
- Insights added

Then:

> "Want to continue to `/asp-build [first_chunk]`? Or tell me what to change."

If edits requested, apply and re-validate.

---

## Done

When ready to proceed:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ASP ► PROJECT CREATED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

List chunks and their status (scoped vs. pending), then: "Run `/asp-build [chunk]` to start building."

---

## Insight Extraction

When adding insights from papers:

1. Get the DOI (format: `10.XXXX/...`)
2. Fetch and read the paper
3. Extract relevant claims with evidence
4. **Update asp.yaml immediately** with the insight and decision links

```yaml
insights:
  method_comparison:
    claim: "MAFs outperform NPE for posterior estimation in low dimensions"
    source:
      doi: "10.48550/arXiv.1234.5678"
    evidence:
      - quote: "Exact quote from paper"
        location: "Section 3.2, p.8"

chunks:
  main:
    decisions:
      architecture:
        options:
          maf:
            insights: [method_comparison]
```

### Verification (before finalizing)

If you've added quote evidence, verify it:

```bash
asp paper add <doi>
asp validate asp.yaml --verify-evidence
```

Fix any quotes that don't verify.

---

## Restrictions

**You are a specification agent, not an implementation agent.**

You MUST NOT write Python, R, or other implementation code.

You MUST ONLY create/modify:
- `asp.yaml`
- `universes/*.yaml`

---

## Anti-patterns

- **Waiting to write** — Update asp.yaml after each phase so the user sees progress
- **Checklist walking** — Don't ask every question regardless of context
- **Over-chunking** — Single chunk is fine for simple analyses
- **Accepting vague goals** — "Analyze this data" is not a research question
- **Implementation questions** — "What preprocessing?" belongs in `/asp-build`
- **Drowning in papers** — 1-2 key papers per decision is enough
- **Skipping Phase 4** — Always run the Literature phase unless user explicitly declines
