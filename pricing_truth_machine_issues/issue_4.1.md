# ISSUE 4.1 — Pricing snippet extraction (rule-based)

**EPIC:** 4 — Evidence extraction (NO LLM hallucination)

**Objective:**  
Extract pricing evidence **without generating text**.

**Requirements:**
- Only substring extraction from source content
- Heuristics:
  - currency symbols
  - "starts at"
  - "per month / per year"
- Truncate to safe prompt length

**DoD:**
- Output snippets are verbatim from source
- No invented phrasing
