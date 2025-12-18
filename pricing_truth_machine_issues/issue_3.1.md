# ISSUE 3.1 — Tavily search client

**EPIC:** 3 — Real-time internet data retrieval (Tavily)

**Objective:**  
Fetch **current web data** reliably.

**Requirements:**
- POST `/search` with:
  - retry logic (tenacity)
  - timeout handling
- Parameters:
  - `search_depth`
  - `max_results`
  - `include_raw_content`
- Deduplicate results by URL

**DoD:**
- Transient errors retried
- Auth errors reported clearly
- Output = list of structured sources
