# ISSUE 0.1 — Define "REAL-DATA-ONLY" contract

**EPIC:** 0 — Product guardrails & truth constraints

**Objective:**  
Ensure the agent never hallucinates prices, benchmarks, FX rates, or recommendations without evidence.

**Requirements:**
- Define allowed vs forbidden behaviors:
  - ✅ Allowed: verbatim extraction, citation, best-effort parsing
  - ❌ Forbidden: estimating prices, guessing market averages, inferring FX/seat counts
- Define verdict states:
  - `UNDERPRICED`
  - `FAIR`
  - `OVERPRICED`
  - `UNDETERMINABLE`
- Define mandatory downgrade rules:
  - Missing competitor prices → `UNDETERMINABLE`
  - Ambiguous cadence (month/year unknown) → no normalization
  - Per-seat pricing without seat count → no normalization

**Acceptance criteria (DoD):**
- A document `docs/real_data_policy.md` exists
- Every numeric claim in output has a citation OR is flagged as a gap
- Agent returns `UNDETERMINABLE` when evidence is insufficient
