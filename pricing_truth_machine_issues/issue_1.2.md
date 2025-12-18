# ISSUE 1.2 — Environment & configuration handling

**EPIC:** 1 — Repository skeleton & engineering standards

**Objective:**  
Centralized, explicit configuration via `.env`.

**Requirements:**
- Load env vars with `python-dotenv`
- Required:
  - `TAVILY_API_KEY`
- Optional:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
- Fail fast if Tavily key missing

**DoD:**
- Clear error message if Tavily key missing
- Optional OpenAI mode does not block execution
