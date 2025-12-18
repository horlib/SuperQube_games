# Pricing Truth Machine

Evidence-based pricing analysis tool that **never hallucinates** prices, benchmarks, or recommendations.

## Features

- ✅ Real-time web data retrieval via Tavily
- ✅ Rule-based evidence extraction (no LLM hallucination)
- ✅ Strict data validation with Pydantic schemas
- ✅ Deterministic verdict logic
- ✅ Optional LLM reasoning mode (OpenAI)
- ✅ Human-readable Markdown reports
- ✅ Machine-readable JSON output

## Installation

```bash
pip install -e .
```

## Configuration

Create a `.env` file:

```env
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional
OPENAI_MODEL=gpt-4  # Optional
```

## Usage

```bash
ptm run --product-name "My Product" --product-url "https://example.com" --current-price "$99/month"
```

See `ptm --help` for full usage information.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src tests

# Format code
ruff format src tests
```

## Policy

This tool adheres to the **REAL-DATA-ONLY** policy. See [docs/real_data_policy.md](docs/real_data_policy.md) for details.

## Disclaimer

**This is an evidence-based informational analysis tool only.**

- No promises or guarantees are made regarding pricing recommendations
- This tool provides information based on publicly available data
- Pricing decisions should be based on comprehensive market research and business considerations beyond this analysis
- The authors and contributors are not responsible for any decisions made based on this tool's output
- Always verify pricing information from official sources before making business decisions

## License

MIT
