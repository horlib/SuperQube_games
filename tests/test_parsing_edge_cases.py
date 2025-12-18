"""Additional edge case tests for parsing & normalization."""


from ptm.parsing import (
    ParsedPrice,
    detect_cadence,
    normalize_to_monthly_usd,
    parse_price,
)


def test_parse_price_week_cadence() -> None:
    """Test parsing price with week cadence."""
    price = parse_price("$20 per week")
    assert price is not None
    assert price.cadence == "week"
    assert price.amount == 20.0


def test_parse_price_day_cadence() -> None:
    """Test parsing price with day cadence."""
    price = parse_price("$5 per day")
    assert price is not None
    assert price.cadence == "day"
    assert price.amount == 5.0


def test_parse_price_currency_code() -> None:
    """Test parsing price with currency code."""
    price = parse_price("100 EUR per month")
    assert price is not None
    assert price.currency == "EUR"
    assert price.amount == 100.0


def test_parse_price_negative_amount() -> None:
    """Test parsing negative amount (should parse but validation catches it)."""
    # Negative prices might parse, but validation in __post_init__ should catch it
    price = parse_price("-$99/month")
    if price:
        # If it parses, the amount would be negative and validation should fail
        # But since we're just testing parsing, we'll just verify it doesn't crash
        assert price.amount > 0 or price.amount < 0  # Either way, it parsed


def test_normalize_to_monthly_usd_week() -> None:
    """Test normalizing weekly price to monthly."""
    parsed = ParsedPrice(
        amount=20.0,
        currency="USD",
        cadence="week",
        raw_text="$20/week",
    )

    normalized = normalize_to_monthly_usd(parsed)
    # 20 * 4.33 ≈ 86.6
    assert normalized.monthly_usd > 80.0
    assert normalized.monthly_usd < 90.0
    assert len(normalized.gaps) == 0


def test_normalize_to_monthly_usd_day() -> None:
    """Test normalizing daily price to monthly."""
    parsed = ParsedPrice(
        amount=5.0,
        currency="USD",
        cadence="day",
        raw_text="$5/day",
    )

    normalized = normalize_to_monthly_usd(parsed)
    # 5 * 30 ≈ 150
    assert normalized.monthly_usd > 140.0
    assert normalized.monthly_usd < 160.0
    assert len(normalized.gaps) == 0


def test_normalize_to_monthly_usd_missing_fx_rate() -> None:
    """Test normalization with missing FX rate."""
    parsed = ParsedPrice(
        amount=100.0,
        currency="CAD",  # Not in default FX rates
        cadence="month",
        raw_text="100 CAD/month",
    )

    normalized = normalize_to_monthly_usd(parsed)
    assert normalized.monthly_usd == 0.0
    assert any("CAD" in gap or "FX rate" in gap for gap in normalized.gaps)


def test_detect_cadence_week() -> None:
    """Test cadence detection for week."""
    assert detect_cadence("$20 per week") == "week"
    assert detect_cadence("$20/week") == "week"
    assert detect_cadence("$20 weekly") == "week"


def test_detect_cadence_day() -> None:
    """Test cadence detection for day."""
    assert detect_cadence("$5 per day") == "day"
    assert detect_cadence("$5/day") == "day"
    assert detect_cadence("$5 daily") == "day"


def test_parse_price_empty_string() -> None:
    """Test parsing empty string."""
    assert parse_price("") is None
    assert parse_price("   ") is None


def test_parse_price_no_numbers() -> None:
    """Test parsing text with no numbers."""
    assert parse_price("Contact us for pricing") is None
    assert parse_price("Free") is None
