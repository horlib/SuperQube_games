# REAL-DATA-ONLY Policy

## Objective

This document defines the strict contract that ensures the Pricing Truth Machine agent **never hallucinates** prices, benchmarks, FX rates, or recommendations without evidence.

## Allowed Behaviors

The agent is permitted to:

- ✅ **Verbatim extraction**: Extract exact text snippets from source content
- ✅ **Citation**: Reference specific URLs and sources for all claims
- ✅ **Best-effort parsing**: Parse structured data (prices, currencies, cadence) from extracted text using rule-based methods
- ✅ **Gap identification**: Explicitly flag when data is missing or insufficient

## Forbidden Behaviors

The agent must **never**:

- ❌ **Estimate prices**: Guess or infer prices that are not explicitly stated in sources
- ❌ **Guess market averages**: Invent benchmark values or industry standards
- ❌ **Infer FX rates**: Assume exchange rates without explicit source data
- ❌ **Infer seat counts**: Assume per-seat pricing multipliers without explicit data
- ❌ **Normalize without data**: Convert currencies or cadences without explicit rates or stated periods
- ❌ **Fill gaps with assumptions**: Create competitor data or pricing tiers that don't exist in sources

## Verdict States

The agent must return one of four verdict states:

### `UNDERPRICED`
- Current product price is lower than comparable competitor prices
- Requires: At least 2 comparable competitor prices with sufficient evidence

### `FAIR`
- Current product price is within reasonable range of competitor prices
- Requires: At least 2 comparable competitor prices with sufficient evidence

### `OVERPRICED`
- Current product price is higher than comparable competitor prices
- Requires: At least 2 comparable competitor prices with sufficient evidence

### `UNDETERMINABLE`
- Insufficient evidence to make a determination
- Must be returned when:
  - Fewer than 2 comparable competitor prices are available
  - Missing competitor prices
  - Ambiguous cadence (month/year unknown)
  - Per-seat pricing without seat count
  - Missing currency or FX rate for normalization
  - Any other condition where evidence is insufficient

## Mandatory Downgrade Rules

The agent must apply these rules to prevent false confidence:

1. **Missing competitor prices** → `UNDETERMINABLE`
   - Cannot compare without at least 2 competitor data points

2. **Ambiguous cadence** → No normalization
   - If month/year is unknown, prices remain in original format
   - Cannot normalize to monthly USD without cadence

3. **Per-seat pricing without seat count** → No normalization
   - Cannot calculate total cost without seat count
   - Cannot normalize to per-seat monthly USD without both price and seat count

4. **Missing FX rate** → No normalization
   - Cannot convert currencies without explicit exchange rate
   - Must flag as gap if normalization is attempted

5. **Insufficient evidence** → `UNDETERMINABLE`
   - Any condition where comparison is not possible with high confidence

## Citation Requirements

Every numeric claim in output must have:

- **Source URL**: Direct link to the page containing the data
- **Extracted snippet**: Verbatim text from the source showing the claim
- **Timestamp**: When the data was retrieved (if available)

If a claim cannot be cited, it must be:
- Flagged as a gap
- Not used in verdict determination
- Explicitly noted in the "Gaps & Limitations" section

## Output Requirements

All outputs must:

1. **Cite every number**: Every price, rate, or benchmark must reference a source
2. **Flag gaps explicitly**: Missing data must be documented, not silently ignored
3. **Return `UNDETERMINABLE` when appropriate**: Never force a verdict with insufficient evidence
4. **Preserve original data**: Store prices as strings unless explicitly normalized with full context
5. **Document normalization**: If normalization occurs, document the method and assumptions

## Compliance

This policy is enforced through:

- Schema validation (Pydantic models)
- Rule-based extraction (no LLM text generation for prices)
- Explicit gap tracking
- Deterministic verdict logic
- Comprehensive test coverage

Violations of this policy are considered critical bugs and must be fixed immediately.
