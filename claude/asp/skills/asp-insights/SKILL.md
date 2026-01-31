---
name: asp-insights
description: Extract and verify insights from scientific papers to justify analysis decisions. Use when working with papers, PDFs, DOIs, or adding evidence to an ASP analysis. Triggers on "paper", "insight", "evidence", "literature", "DOI", "quote".
allowed-tools: Read, Edit(asp.yaml), Glob, Grep, Bash(asp:*), WebSearch, WebFetch, AskUserQuestion
---

# /asp-insights

Extract insights from scientific literature and link them to analysis decisions. This skill guides you through a robust workflow where evidence is verified against source PDFs — no fabricated quotes can pass validation.

**Key principle**: The agent writes evidence, but `asp validate --verify-evidence` is the gatekeeper. Quotes that don't exist in the PDF will fail validation.

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: Find Papers (Web Search)                                  │
│  → Identify relevant literature, collect DOIs                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: Download Papers (CLI)                                     │
│  → asp paper add <doi> — caches PDF locally                         │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: Extract Insights (Read PDF)                               │
│  → Read PDF directly, identify relevant quotes/figures              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 4: Write & Verify (Edit + Validate)                          │
│  → Write insights to asp.yaml, run asp validate --verify-evidence   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 5: Link to Decisions                                         │
│  → Add insight references to decision options                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Setup

1. Read the ASP reference guide: `.claude/skills/asp/SKILL.md`
2. Read `asp.yaml` to understand:
   - What problem is being solved?
   - What decisions exist that need justification?
   - What insights already exist?

## Step 1: Identify Papers

Print: `## Step 1: Identify Papers`

Find relevant literature for the analysis decisions.

**If the user provides a paper:**
- Extract the DOI from URL, PDF metadata, or citation
- DOI format: `10.XXXX/...` (e.g., `10.1038/s41586-023-06221-2`)
- arXiv DOI format: `10.48550/arXiv.{id}` (e.g., `10.48550/arXiv.1706.03762`)

**If searching for papers:**
- Use `WebSearch` to find relevant papers on arXiv, Semantic Scholar, Google Scholar
- Search for papers related to specific decisions that need evidence
- Note which decisions each paper might inform

Ask the user if needed: "Which decisions need literature support?" Present options from the analysis.

## Step 2: Download Papers

Print: `## Step 2: Download Papers`

Use the CLI to cache papers locally:

```bash
# Standard paper
asp paper add 10.1038/s41586-023-06221-2

# arXiv paper with specific version
asp paper add 10.48550/arXiv.1706.03762 --version 7

# If you have a PDF locally
asp paper add 10.48550/arXiv.1706.03762 --pdf /path/to/paper.pdf
```

Useful commands:
```bash
asp paper list              # List cached papers
asp paper show <doi>        # Show paper metadata
asp paper path <doi>        # Get path to cached PDF
```

**Important**: Papers must be cached before evidence can be verified. The validation step will fail if the paper isn't in the cache.

## Step 3: Read and Extract

Print: `## Step 3: Read and Extract`

Read the PDF directly to extract insights:

```bash
# Get the PDF path
asp paper path 10.48550/arXiv.1706.03762
```

Then use the Read tool to view the PDF. Claude can read PDFs natively.

For each relevant finding:
1. **Identify the exact quote** — copy text precisely as it appears
2. **Note the page number** — for the location hint
3. **Optionally add prefix/suffix** — ~20-100 chars for disambiguation if the quote is common

**Evidence types:**

| Type | When to use | Required fields |
|------|-------------|-----------------|
| `quote` | Direct text from paper | `exact` (the quote) |
| `figure` | Reference to a figure | `label` (e.g., "Figure 3a") |
| `table` | Reference to a table | `label` (e.g., "Table 1") |

**Quote extraction tips:**
- Keep quotes to 1-3 sentences
- Copy exactly — the validator does fuzzy matching but exact is better
- Include page number in `location` for faster verification
- Add `prefix`/`suffix` if the same text appears multiple times

## Step 4: Write Insights

Print: `## Step 4: Write Insights`

Add insights to `asp.yaml` in the `insights` section:

```yaml
insights:
  layer_norm_stability:
    id: layer_norm_stability
    claim: "Layer normalization improves training stability compared to batch normalization for transformer architectures."
    created_at: "2024-01-15T10:30:00Z"
    evidence:
      - id: ev1
        doi: "10.48550/arXiv.1706.03762"
        version: 7
        quote:
          type: TextQuoteSelector
          exact: "We found that layer normalization leads to faster convergence and more stable training dynamics."
          prefix: "In our ablation studies, "
        location:
          type: FragmentSelector
          page: 5

  attention_scaling:
    id: attention_scaling
    claim: "Scaling attention by 1/sqrt(d_k) prevents dot products from growing too large."
    created_at: "2024-01-15T10:35:00Z"
    evidence:
      - id: ev1
        doi: "10.48550/arXiv.1706.03762"
        version: 7
        quote:
          type: TextQuoteSelector
          exact: "We suspect that for large values of d_k, the dot products grow large in magnitude, pushing the softmax function into regions where it has extremely small gradients."
        location:
          type: FragmentSelector
          page: 4
```

**Evidence format details:**

```yaml
evidence:
  - id: ev1                           # Unique within this insight
    doi: "10.48550/arXiv.1706.03762"  # Required: paper DOI
    version: 7                         # Optional: arXiv version (important for reproducibility)

    # At least one of: quote, figure, or table
    quote:
      type: TextQuoteSelector          # W3C Web Annotation type
      exact: "The exact quoted text"   # Required: verbatim from paper
      prefix: "Context before..."      # Optional: ~20-100 chars
      suffix: "Context after..."       # Optional: ~20-100 chars

    # OR for figures
    figure:
      type: FigureSelector
      label: "Figure 3a"               # Required: figure label
      caption: "Caption text..."       # Optional: for verification

    # OR for tables
    table:
      type: TableSelector
      label: "Table 1"                 # Required: table label
      caption: "Header text..."        # Optional: for verification
      region: "row 3, accuracy column" # Optional: specific region

    # Location hint (optional but recommended)
    location:
      type: FragmentSelector
      page: 5                          # 1-indexed page number
```

## Step 5: Verify Evidence

Print: `## Step 5: Verify Evidence`

Run verification to ensure all quotes exist in source PDFs:

```bash
asp validate asp.yaml --verify-evidence
```

**What happens:**
- Schema validation (structure, types)
- Semantic validation (references resolve)
- Evidence verification (quotes found in PDFs)

**If verification fails:**
- `Quote not found` — re-read the PDF, correct the quote text
- `Paper not in cache` — run `asp paper add <doi>` first
- `Wrong page` — quote found but on different page (update location)

Keep iterating until all evidence verifies. This is the gatekeeper — fabricated quotes cannot pass.

## Step 6: Link to Decisions

Print: `## Step 6: Link to Decisions`

Reference insights in decision options to justify why that option is preferred:

```yaml
chunks:
  main:
    decisions:
      normalization:
        label: "Normalization Method"
        type: method
        default: layer_norm
        options:
          layer_norm:
            label: "Layer Normalization"
            insights:
              - layer_norm_stability    # Reference to insight ID
          batch_norm:
            label: "Batch Normalization"
```

This creates traceability: decisions link to insights, insights link to evidence, evidence links to papers.

## Step 7: Final Validation

Print: `## Step 7: Final Validation`

Run full validation one more time:

```bash
asp validate asp.yaml --verify-evidence
```

If all passes:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ASP ► INSIGHTS VERIFIED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Report: "[N] insights added with [M] verified evidence items. Linked to [K] decision options."

## CLI Reference

```bash
# Paper management
asp paper add <doi> [--version N] [--pdf path]   # Download/cache paper
asp paper list                                    # List cached papers
asp paper show <doi>                              # Show paper metadata
asp paper path <doi>                              # Get path to PDF
asp paper remove <doi>                            # Remove from cache

# Validation
asp validate asp.yaml                             # Schema + semantic validation
asp validate asp.yaml --verify-evidence           # + evidence verification
```

## Common Patterns

### Adding evidence from a new paper

```bash
# 1. Add paper to cache
asp paper add 10.1234/example.paper

# 2. Get PDF path and read it
asp paper path 10.1234/example.paper
# → Read the PDF with Read tool

# 3. Add insight to asp.yaml (Edit tool)
# 4. Verify: asp validate asp.yaml --verify-evidence
# 5. Link to decisions (Edit tool)
```

### Multiple evidence items per insight

```yaml
insights:
  robust_finding:
    id: robust_finding
    claim: "Finding X is robust across multiple studies."
    created_at: "2024-01-15T10:30:00Z"
    evidence:
      - id: ev1
        doi: "10.1234/paper1"
        quote:
          type: TextQuoteSelector
          exact: "We observed X in all conditions."
        location:
          type: FragmentSelector
          page: 7
      - id: ev2
        doi: "10.5678/paper2"
        quote:
          type: TextQuoteSelector
          exact: "Our results confirm X."
        location:
          type: FragmentSelector
          page: 12
```

### arXiv papers (version matters)

```yaml
evidence:
  - id: ev1
    doi: "10.48550/arXiv.2303.08774"
    version: 4                        # Important: arXiv papers are updated
    quote:
      type: TextQuoteSelector
      exact: "GPT-4 is a large multimodal model..."
```

## Restrictions

**You are an insights agent, not an implementation agent.**

- ONLY modify `asp.yaml` (insights section and decision option references)
- NEVER fabricate quotes — all evidence must be verified against source PDFs
- ALWAYS run `asp validate --verify-evidence` after adding evidence
- If a quote doesn't verify, fix it — don't skip verification

## Tips

1. **Start with decisions** — identify which decisions need literature support
2. **One claim per insight** — don't combine multiple findings
3. **Precise quotes** — exact text from the paper, not paraphrases
4. **Include context** — prefix/suffix helps disambiguation
5. **Page numbers** — speed up verification with location hints
6. **arXiv versions** — always specify version for reproducibility
7. **Iterate on failures** — if verification fails, re-read the PDF and correct
