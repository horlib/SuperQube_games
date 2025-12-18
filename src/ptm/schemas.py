# -*- coding: utf-8 -*-
"""Pydantic schemas for Pricing Truth Machine."""

from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, field_validator


class VerdictStatus(str, Enum):
    """Pricing verdict status."""

    UNDERPRICED = "UNDERPRICED"
    FAIR = "FAIR"
    OVERPRICED = "OVERPRICED"
    UNDETERMINABLE = "UNDETERMINABLE"


class ProductInput(BaseModel):
    """Input schema for product information."""

    name: str = Field(..., description="Product name")
    url: HttpUrl = Field(..., description="Product URL")
    current_price: str = Field(..., description="Current price as string (e.g., '$99/month')")
    competitor_urls: list[HttpUrl] = Field(
        default_factory=list,
        description="Optional list of competitor URLs to check",
    )
    category: str | None = Field(
        None,
        description="Product category (e.g., 'SaaS', 'Project Management', 'Design Tool')",
    )
    target_customer: str | None = Field(
        None,
        description="Target customer segment (e.g., 'Small Business', 'Enterprise', 'Individual')",
    )
    key_features: list[str] = Field(
        default_factory=list,
        description="Key features or capabilities of the product",
    )
    problem_statement: str | None = Field(
        None,
        description="Specific problem that the product solves (e.g., 'Manage team tasks and collaboration')",
    )
    decision_context: str | None = Field(
        None,
        description="Decision context: who decides, when, why (e.g., 'Marketing teams choosing tools for content creation')",
    )
    payment_model: str | None = Field(
        None,
        description="Payment model (e.g., 'subscription', 'one-time', 'per-seat', 'usage-based', 'freemium')",
    )


class TavilySource(BaseModel):
    """Schema for Tavily search result source."""

    url: HttpUrl = Field(..., description="Source URL")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content")
    score: float | None = Field(None, description="Relevance score")
    published_date: str | None = Field(None, description="Publication date if available")


class CompetitorPricing(BaseModel):
    """Schema for competitor pricing information."""

    domain: str = Field(..., description="Competitor domain")
    extracted_price_texts: list[str] = Field(
        default_factory=list,
        description="Raw price text extracted from sources",
    )
    evidence_snippets: list[str] = Field(
        default_factory=list,
        description="Verbatim snippets containing pricing evidence",
    )
    normalized_monthly_usd: float | None = Field(
        None,
        description="Normalized price in monthly USD (only if all data available)",
    )
    cadence: str | None = Field(
        None,
        description="Price cadence (month, year, day, week, one-time) if known",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="List of gaps preventing normalization (e.g., 'missing cadence', 'missing FX rate')",
    )
    # Product attributes for better competitor matching
    category: str | None = Field(
        None,
        description="Product category extracted from sources",
    )
    target_customer: str | None = Field(
        None,
        description="Target customer segment extracted from sources",
    )
    key_features: list[str] = Field(
        default_factory=list,
        description="Key features extracted from sources",
    )
    product_description: str | None = Field(
        None,
        description="Brief product description extracted from sources",
    )
    problem_statement: str | None = Field(
        None,
        description="Specific problem that the competitor product solves",
    )
    decision_context: str | None = Field(
        None,
        description="Decision context: who decides, when, why",
    )
    payment_model: str | None = Field(
        None,
        description="Payment model (e.g., 'subscription', 'one-time', 'per-seat', 'usage-based')",
    )

    @field_validator("normalized_monthly_usd")
    @classmethod
    def validate_normalized_price(cls, v: float | None) -> float | None:
        """Validate that normalized price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Normalized price must be positive")
        return v


class EvidenceBundle(BaseModel):
    """Schema for collected evidence bundle."""

    product_input: ProductInput = Field(..., description="Original product input")
    tavily_sources: list[TavilySource] = Field(
        default_factory=list,
        description="Sources retrieved from Tavily",
    )
    competitor_pricing: list[CompetitorPricing] = Field(
        default_factory=list,
        description="Competitor pricing data",
    )
    extraction_gaps: list[str] = Field(
        default_factory=list,
        description="Gaps in evidence extraction",
    )


class PricingVerdict(BaseModel):
    """Schema for final pricing verdict."""

    status: VerdictStatus = Field(..., description="Verdict status")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)",
    )
    key_reasons: list[str] = Field(
        default_factory=list,
        description="Key reasons for the verdict",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Data gaps that limit confidence",
    )
    citations: list[HttpUrl] = Field(
        default_factory=list,
        description="URLs cited as evidence",
    )
    competitor_count: int = Field(
        ...,
        ge=0,
        description="Number of competitors with comparable pricing data",
    )
    evidence_bundle: EvidenceBundle = Field(..., description="Full evidence bundle")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v
