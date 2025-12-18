# ISSUE 2.1 — Define strict Pydantic schemas

**EPIC:** 2 — Data schemas & contracts

**Objective:**  
Guarantee input/output correctness and reproducibility.

**Schemas required:**
- `ProductInput`
- `TavilySource`
- `CompetitorPricing`
- `EvidenceBundle`
- `PricingVerdict`

**Rules:**
- URLs must validate
- Prices stored as strings unless explicitly normalized
- Verdict must include:
  - status
  - confidence
  - key reasons
  - gaps
  - citations

**DoD:**
- Invalid input fails validation
- Output JSON always conforms to schema
