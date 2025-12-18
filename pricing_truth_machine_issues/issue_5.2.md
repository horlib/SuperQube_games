# ISSUE 5.2 — Optional LLM reasoning mode (OpenAI)

**EPIC:** 5 — Analysis & verdict engine

**Objective:**  
Enhance interpretation **without violating real-data policy**.

**Rules:**
- LLM sees ONLY:
  - product facts
  - extracted evidence snippets
  - explicit gaps
- Prompt forbids estimation or invention
- Output must be structured JSON

**DoD:**
- Every conclusion references evidence
- Missing data → explicit uncertainty
