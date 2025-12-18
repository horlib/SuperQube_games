# ISSUE 4.3 — Competitor pricing aggregation

**EPIC:** 4 — Evidence extraction (NO LLM hallucination)

**Objective:**  
Build structured competitor pricing records.

**Requirements:**
- For each competitor:
  - extracted_price_texts[]
  - evidence_snippets[]
  - optional normalized_monthly_usd
- Deduplicate by domain

**DoD:**
- Empty competitor evidence is explicitly flagged
- No competitor "filled in" by assumption
