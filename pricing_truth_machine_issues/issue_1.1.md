# ISSUE 1.1 — Initialize professional Python repo (src layout)

**EPIC:** 1 — Repository skeleton & engineering standards

**Objective:**  
Create a production-ready Python package with CLI.

**Requirements:**
- Use `pyproject.toml` (setuptools)
- Structure:
  ```
  src/ptm/
  tests/
  README.md
  issues.md
  ```
- CLI entrypoint: `ptm`
- Linting with `ruff`
- Tests with `pytest`

**DoD:**
- `pip install -e .` works
- `ptm --help` works
- `pytest` passes
