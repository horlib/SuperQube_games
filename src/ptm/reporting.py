"""Markdown report generator for pricing analysis."""

from datetime import datetime
from pathlib import Path

from ptm.schemas import PricingVerdict


def generate_markdown_report(verdict: PricingVerdict, output_path: Path) -> None:
    """Generate human-readable Markdown report.

    Sections:
    - Inputs
    - Evidence summary
    - Competitor comparison table
    - Verdict
    - Gaps & limitations
    - Citations

    Args:
        verdict: Pricing verdict
        output_path: Path to write report.md
    """
    product = verdict.evidence_bundle.product_input

    report_lines = [
        "# Pricing Analysis Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Inputs",
        "",
        f"- **Product Name:** {product.name}",
        f"- **Product URL:** {product.url}",
        f"- **Current Price:** {product.current_price}",
        "",
    ]

    if product.competitor_urls:
        report_lines.extend(
            [
                "### Competitor URLs Provided",
                "",
            ]
        )
        for url in product.competitor_urls:
            report_lines.append(f"- {url}")
        report_lines.append("")

    # Evidence summary
    report_lines.extend(
        [
            "## Evidence Summary",
            "",
            f"- **Sources Retrieved:** {len(verdict.evidence_bundle.tavily_sources)}",
            f"- **Competitors Analyzed:** {len(verdict.evidence_bundle.competitor_pricing)}",
            f"- **Comparable Competitors:** {verdict.competitor_count}",
            "",
        ]
    )

    # Competitor comparison table
    comparable = [
        cp
        for cp in verdict.evidence_bundle.competitor_pricing
        if cp.normalized_monthly_usd is not None
    ]

    if comparable:
        report_lines.extend(
            [
                "## Competitor Comparison",
                "",
                "| Competitor | Price | Normalized (Monthly USD) | Evidence |",
                "|------------|-------|---------------------------|----------|",
            ]
        )

        for cp in comparable[:10]:  # Limit to 10 for readability
            price_text = cp.extracted_price_texts[0] if cp.extracted_price_texts else "N/A"
            normalized = f"${cp.normalized_monthly_usd:.2f}" if cp.normalized_monthly_usd else "N/A"
            evidence_count = len(cp.evidence_snippets)
            report_lines.append(
                f"| {cp.domain} | {price_text} | {normalized} | {evidence_count} snippet(s) |"
            )

        report_lines.append("")

    # Verdict
    status_emoji = {
        "UNDERPRICED": "✅",
        "FAIR": "⚖️",
        "OVERPRICED": "⚠️",
        "UNDETERMINABLE": "❓",
    }

    report_lines.extend(
        [
            "## Verdict",
            "",
            f"**Status:** {status_emoji.get(verdict.status.value, '')} {verdict.status.value}",
            "",
            f"**Confidence:** {verdict.confidence:.1%}",
            "",
            "### Key Reasons",
            "",
        ]
    )

    for reason in verdict.key_reasons:
        report_lines.append(f"- {reason}")

    report_lines.append("")

    # Gaps & limitations
    if verdict.gaps:
        report_lines.extend(
            [
                "## Gaps & Limitations",
                "",
                "The following data gaps limit the confidence of this analysis:",
                "",
            ]
        )

        for gap in verdict.gaps:
            report_lines.append(f"- {gap}")

        report_lines.append("")

    # Citations
    if verdict.citations:
        report_lines.extend(
            [
                "## Citations",
                "",
                "Sources used in this analysis:",
                "",
            ]
        )

        for i, citation in enumerate(verdict.citations[:20], 1):  # Limit to 20
            report_lines.append(f"{i}. {citation}")

        report_lines.append("")

    # Disclaimer
    report_lines.extend(
        [
            "---",
            "",
            "## Disclaimer",
            "",
            "This is an **evidence-based informational analysis** only. ",
            "No promises or guarantees are made. ",
            "Pricing decisions should be based on comprehensive market research ",
            "and business considerations beyond this analysis.",
            "",
        ]
    )

    # Write report
    report_content = "\n".join(report_lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding="utf-8")
