# ISSUE 4.2 — Money parsing & cadence detection

**EPIC:** 4 — Evidence extraction (NO LLM hallucination)

**Objective:**  
Parse prices **only if explicitly stated**.

**Rules:**
- Detect:
  - amount
  - currency
  - cadence (month/year)
  - per-seat
- Normalize to monthly USD ONLY IF:
  - cadence known
  - FX rate explicitly provided or configured
- Otherwise: return `None` + gap note

**DoD:**
- No silent normalization
- Every failed parse produces a gap reason
