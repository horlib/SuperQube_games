# -*- coding: utf-8 -*-
"""Money parsing and cadence detection (NO silent normalization)."""

import re
from dataclasses import dataclass

# Currency symbols mapping
CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
}

# FX rates (can be configured, defaults to 1.0 if not provided)
# In production, these should come from a real-time source or config
DEFAULT_FX_RATES = {
    "USD": 1.0,
    "EUR": 1.1,  # Example: 1 EUR = 1.1 USD
    "GBP": 1.25,  # Example: 1 GBP = 1.25 USD
    "JPY": 0.0067,  # Example: 1 JPY = 0.0067 USD
    "INR": 0.012,  # Example: 1 INR = 0.012 USD
}


@dataclass
class ParsedPrice:
    """Parsed price information."""

    amount: float
    currency: str
    cadence: str | None = None  # "month", "year", "day", "week", None
    per_seat: bool = False
    raw_text: str = ""

    def __post_init__(self) -> None:
        """Validate parsed price."""
        if self.amount <= 0:
            raise ValueError("Price amount must be positive")


@dataclass
class NormalizedPrice:
    """Normalized price in monthly USD."""

    monthly_usd: float
    original_price: ParsedPrice
    normalization_method: str
    gaps: list[str]


def parse_price(text: str) -> ParsedPrice | None:
    """Parse price from text string.

    Only parses if explicitly stated. Does not guess or infer.

    Args:
        text: Price text (e.g., "$99/month", "€50 per month", "£30/year")

    Returns:
        ParsedPrice if parsing successful, None otherwise
    """
    if not text:
        return None

    text = text.strip()

    # Try to extract amount
    # Handle both formats: $1,234.56 (US) and €1.234,56 (EU)
    # First try US format (comma as thousands, dot as decimal)
    us_format_match = re.search(r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)", text)
    if us_format_match:
        try:
            amount_str = us_format_match.group(1).replace(",", "")
            amount = float(amount_str)
        except ValueError:
            pass
        else:
            if amount > 0:
                # Successfully parsed US format
                pass
            else:
                us_format_match = None

    # If US format didn't work, try EU format (dot as thousands, comma as decimal)
    if not us_format_match:
        eu_format_match = re.search(r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?)", text)
        if eu_format_match:
            try:
                amount_str = eu_format_match.group(1).replace(".", "").replace(",", ".")
                amount = float(amount_str)
            except ValueError:
                return None
        else:
            # Fallback to simple number
            simple_match = re.search(r"(\d+(?:[.,]\d+)?)", text)
            if not simple_match:
                return None
            try:
                amount_str = simple_match.group(1).replace(",", ".")
                amount = float(amount_str)
            except ValueError:
                return None

    # Extract currency
    currency = "USD"  # Default
    for symbol, curr in CURRENCY_SYMBOLS.items():
        if symbol in text:
            currency = curr
            break

    # Check for currency codes (USD, EUR, etc.)
    currency_code_match = re.search(r"\b(USD|EUR|GBP|JPY|INR)\b", text, re.IGNORECASE)
    if currency_code_match:
        currency = currency_code_match.group(1).upper()

    # Extract cadence
    cadence = None
    text_lower = text.lower()

    if any(term in text_lower for term in ["/month", "per month", "/mo", "monthly"]):
        cadence = "month"
    elif any(term in text_lower for term in ["/year", "per year", "/yr", "yearly", "annually"]):
        cadence = "year"
    elif any(term in text_lower for term in ["/day", "per day", "daily"]):
        cadence = "day"
    elif any(term in text_lower for term in ["/week", "per week", "weekly"]):
        cadence = "week"

    # Check for per-seat pricing
    per_seat = any(
        term in text_lower for term in ["per seat", "/seat", "per user", "/user", "per license"]
    )

    try:
        return ParsedPrice(
            amount=amount,
            currency=currency,
            cadence=cadence,
            per_seat=per_seat,
            raw_text=text,
        )
    except ValueError:
        return None


def normalize_to_monthly_usd(
    parsed_price: ParsedPrice,
    fx_rates: dict[str, float] | None = None,
    seat_count: int | None = None,
) -> NormalizedPrice:
    """Normalize price to monthly USD.

    Only normalizes if ALL required data is available:
    - Cadence must be known
    - FX rate must be available (or currency is USD)
    - If per-seat, seat count must be provided

    Args:
        parsed_price: Parsed price
        fx_rates: Optional FX rates dict (defaults to DEFAULT_FX_RATES)
        seat_count: Optional seat count for per-seat pricing

    Returns:
        NormalizedPrice with monthly_usd if normalization possible,
        otherwise with gaps explaining why normalization failed
    """
    gaps = []
    fx_rates = fx_rates or DEFAULT_FX_RATES

    # Check cadence
    if not parsed_price.cadence:
        gaps.append("Missing cadence (month/year unknown)")
        return NormalizedPrice(
            monthly_usd=0.0,
            original_price=parsed_price,
            normalization_method="failed",
            gaps=gaps,
        )

    # Check FX rate
    if parsed_price.currency not in fx_rates:
        gaps.append(f"Missing FX rate for {parsed_price.currency}")
        return NormalizedPrice(
            monthly_usd=0.0,
            original_price=parsed_price,
            normalization_method="failed",
            gaps=gaps,
        )

    # Check per-seat
    if parsed_price.per_seat and seat_count is None:
        gaps.append("Per-seat pricing but seat count not provided")
        return NormalizedPrice(
            monthly_usd=0.0,
            original_price=parsed_price,
            normalization_method="failed",
            gaps=gaps,
        )

    # Normalize step by step
    amount = parsed_price.amount

    # Step 1: Convert to USD
    fx_rate = fx_rates[parsed_price.currency]
    amount_usd = amount * fx_rate

    # Step 2: Convert to monthly
    if parsed_price.cadence == "year":
        amount_monthly = amount_usd / 12
    elif parsed_price.cadence == "day":
        amount_monthly = amount_usd * 30  # Approximate
    elif parsed_price.cadence == "week":
        amount_monthly = amount_usd * 4.33  # Approximate
    else:  # month
        amount_monthly = amount_usd

    # Step 3: Multiply by seat count if per-seat
    if parsed_price.per_seat and seat_count:
        amount_monthly = amount_monthly * seat_count

    return NormalizedPrice(
        monthly_usd=round(amount_monthly, 2),
        original_price=parsed_price,
        normalization_method="full_normalization",
        gaps=[],
    )


def detect_cadence(text: str) -> str | None:
    """Detect cadence from text.

    Args:
        text: Text to analyze

    Returns:
        Cadence string or None if not detected
    """
    text_lower = text.lower()

    if any(term in text_lower for term in ["/month", "per month", "/mo", "monthly"]):
        return "month"
    elif any(term in text_lower for term in ["/year", "per year", "/yr", "yearly", "annually"]):
        return "year"
    elif any(term in text_lower for term in ["/day", "per day", "daily"]):
        return "day"
    elif any(term in text_lower for term in ["/week", "per week", "weekly"]):
        return "week"

    return None
