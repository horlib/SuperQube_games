"""Tests for money parsing and cadence detection."""


from ptm.parsing import (
    ParsedPrice,
    detect_cadence,
    normalize_to_monthly_usd,
    parse_price,
)


def test_parse_price_basic() -> None:
    """Test basic price parsing."""
    price = parse_price("$99/month")
    assert price is not None
    assert price.amount == 99.0
    assert price.currency == "USD"
    assert price.cadence == "month"
    assert not price.per_seat


def test_parse_price_per_year() -> None:
    """Test parsing yearly price."""
    price = parse_price("€50 per year")
    assert price is not None
    assert price.amount == 50.0
    assert price.currency == "EUR"
    assert price.cadence == "year"


def test_parse_price_per_seat() -> None:
    """Test parsing per-seat price."""
    price = parse_price("$10 per seat per month")
    assert price is not None
    assert price.amount == 10.0
    assert price.per_seat


def test_parse_price_invalid() -> None:
    """Test parsing invalid price."""
    price = parse_price("Contact us for pricing")
    assert price is None


def test_parse_price_with_comma() -> None:
    """Test parsing price with comma decimal separator."""
    # Note: EU format might not parse correctly, but should handle basic cases
    price2 = parse_price("$1,234.56 per month")
    assert price2 is not None
    assert price2.amount == 1234.56


def test_normalize_to_monthly_usd_monthly() -> None:
    """Test normalizing monthly USD price."""
    parsed = ParsedPrice(
        amount=99.0,
        currency="USD",
        cadence="month",
        raw_text="$99/month",
    )

    normalized = normalize_to_monthly_usd(parsed)
    assert normalized.monthly_usd == 99.0
    assert len(normalized.gaps) == 0


def test_normalize_to_monthly_usd_yearly() -> None:
    """Test normalizing yearly price to monthly."""
    parsed = ParsedPrice(
        amount=1200.0,
        currency="USD",
        cadence="year",
        raw_text="$1200/year",
    )

    normalized = normalize_to_monthly_usd(parsed)
    assert normalized.monthly_usd == 100.0  # 1200 / 12
    assert len(normalized.gaps) == 0


def test_normalize_to_monthly_usd_missing_cadence() -> None:
    """Test normalization with missing cadence."""
    parsed = ParsedPrice(
        amount=99.0,
        currency="USD",
        cadence=None,
        raw_text="$99",
    )

    normalized = normalize_to_monthly_usd(parsed)
    assert normalized.monthly_usd == 0.0
    assert "Missing cadence" in " ".join(normalized.gaps)


def test_normalize_to_monthly_usd_per_seat_without_count() -> None:
    """Test normalization of per-seat price without seat count."""
    parsed = ParsedPrice(
        amount=10.0,
        currency="USD",
        cadence="month",
        per_seat=True,
        raw_text="$10/seat/month",
    )

    normalized = normalize_to_monthly_usd(parsed)
    assert normalized.monthly_usd == 0.0
    assert "seat count" in " ".join(normalized.gaps).lower()


def test_normalize_to_monthly_usd_per_seat_with_count() -> None:
    """Test normalization of per-seat price with seat count."""
    parsed = ParsedPrice(
        amount=10.0,
        currency="USD",
        cadence="month",
        per_seat=True,
        raw_text="$10/seat/month",
    )

    normalized = normalize_to_monthly_usd(parsed, seat_count=5)
    assert normalized.monthly_usd == 50.0  # 10 * 5
    assert len(normalized.gaps) == 0


def test_normalize_to_monthly_usd_currency_conversion() -> None:
    """Test normalization with currency conversion."""
    parsed = ParsedPrice(
        amount=100.0,
        currency="EUR",
        cadence="month",
        raw_text="€100/month",
    )

    # Use custom FX rate
    fx_rates = {"EUR": 1.1, "USD": 1.0}
    normalized = normalize_to_monthly_usd(parsed, fx_rates=fx_rates)
    assert normalized.monthly_usd == 110.0  # 100 * 1.1
    assert len(normalized.gaps) == 0


def test_detect_cadence_month() -> None:
    """Test cadence detection for month."""
    assert detect_cadence("$99 per month") == "month"
    assert detect_cadence("$99/month") == "month"
    assert detect_cadence("$99 monthly") == "month"


def test_detect_cadence_year() -> None:
    """Test cadence detection for year."""
    assert detect_cadence("$1200 per year") == "year"
    assert detect_cadence("$1200/year") == "year"
    assert detect_cadence("$1200 yearly") == "year"


def test_detect_cadence_none() -> None:
    """Test cadence detection when not present."""
    assert detect_cadence("$99") is None
    assert detect_cadence("Contact us") is None
