"""Rule-based pricing snippet extraction (NO LLM hallucination)."""

import re

from ptm.schemas import TavilySource

# Maximum snippet length to keep prompts safe
MAX_SNIPPET_LENGTH = 500


class ExtractionError(Exception):
    """Exception raised during extraction."""


def extract_pricing_snippets(sources: list[TavilySource]) -> list[str]:
    """Extract pricing-related snippets from sources using rule-based heuristics.

    This function ONLY extracts verbatim text from sources. It does NOT generate
    or invent any text. All snippets are direct substrings from source content.

    Args:
        sources: List of TavilySource objects

    Returns:
        List of verbatim pricing snippets (truncated to safe length)
    """
    snippets = []

    for source in sources:
        content = source.content
        if not content:
            continue

        # Extract snippets using heuristics
        extracted = _extract_with_heuristics(content)
        snippets.extend(extracted)

    # Truncate snippets to safe length
    truncated = [_truncate_snippet(s) for s in snippets]

    # Remove duplicates while preserving order
    seen = set()
    unique_snippets = []
    for snippet in truncated:
        if snippet not in seen:
            seen.add(snippet)
            unique_snippets.append(snippet)

    return unique_snippets


def _extract_with_heuristics(content: str) -> list[str]:
    """Extract pricing snippets using rule-based heuristics.

    Heuristics:
    - Look for currency symbols ($, €, £, ¥, etc.)
    - Look for "starts at" patterns
    - Look for "per month" / "per year" patterns
    - Look for price ranges

    Args:
        content: Source content text

    Returns:
        List of extracted snippets
    """
    snippets = []

    # Pattern 1: Currency symbol followed by numbers
    # Matches: $99, €50, £30, ¥1000, etc.
    currency_pattern = r"[€$£¥₹]\s*\d+(?:[.,]\d+)?(?:\s*/\s*(?:month|year|mo|yr|day|wk))?"

    # Pattern 2: "starts at" or "from" with price
    starts_at_pattern = r"(?:starts?\s+at|from|beginning\s+at)\s+[€$£¥₹]\s*\d+(?:[.,]\d+)?"

    # Pattern 3: "per month" / "per year" patterns
    per_period_pattern = (
        r"\d+(?:[.,]\d+)?\s*(?:USD|EUR|GBP|JPY|INR)?\s*(?:per|/)\s*(?:month|year|mo|yr|day|wk)"
    )

    # Pattern 4: Price ranges (e.g., "$99-$199")
    price_range_pattern = r"[€$£¥₹]\s*\d+(?:[.,]\d+)?\s*[-–—]\s*[€$£¥₹]?\s*\d+(?:[.,]\d+)?"

    # Combine all patterns
    all_patterns = [
        currency_pattern,
        starts_at_pattern,
        per_period_pattern,
        price_range_pattern,
    ]

    for pattern in all_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Extract context around the match (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            snippet = content[start:end].strip()

            if snippet and len(snippet) > 10:  # Minimum snippet length
                snippets.append(snippet)

    # Also look for lines containing pricing keywords
    lines = content.split("\n")
    pricing_keywords = ["price", "pricing", "cost", "plan", "tier", "subscription"]

    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in pricing_keywords):
            # Check if line contains currency or numbers
            if re.search(r"[€$£¥₹]\s*\d+|\d+\s*(?:USD|EUR|GBP|JPY|INR)", line):
                if line.strip() and len(line.strip()) > 10:
                    snippets.append(line.strip())

    return snippets


def _truncate_snippet(snippet: str) -> str:
    """Truncate snippet to safe prompt length.

    Args:
        snippet: Snippet text

    Returns:
        Truncated snippet
    """
    if len(snippet) <= MAX_SNIPPET_LENGTH:
        return snippet

    # Truncate and add ellipsis
    return snippet[: MAX_SNIPPET_LENGTH - 3] + "..."


def extract_price_texts(snippets: list[str]) -> list[str]:
    """Extract just the price text portions from snippets.

    This extracts only the price portions (e.g., "$99/month") from snippets,
    not the full context.

    Args:
        snippets: List of pricing snippets

    Returns:
        List of extracted price texts
    """
    price_texts = []

    # Pattern to match price expressions
    price_pattern = r"[€$£¥₹]\s*\d+(?:[.,]\d+)?(?:\s*(?:USD|EUR|GBP|JPY|INR)?\s*(?:per|/)\s*(?:month|year|mo|yr|day|wk))?"

    for snippet in snippets:
        matches = re.findall(price_pattern, snippet, re.IGNORECASE)
        for match in matches:
            price_text = match.strip()
            if price_text and price_text not in price_texts:
                price_texts.append(price_text)

    return price_texts
