# ISSUE 5.1 — Evidence-only verdict logic (no LLM)

**EPIC:** 5 — Analysis & verdict engine

**Objective:**  
Agent must work **without OpenAI**.

**Rules:**
- Compare current price vs competitor prices ONLY IF comparable
- If fewer than 2 comparable competitors → `UNDETERMINABLE`
- Confidence scoring based on evidence count & consistency

**DoD:**
- Agent runs fully offline (except Tavily)
- Verdict logic is deterministic and testable
