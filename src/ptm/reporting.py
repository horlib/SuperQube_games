# -*- coding: utf-8 -*-
"""Markdown report generator for pricing analysis."""

from datetime import datetime
from pathlib import Path

from ptm.schemas import PricingVerdict, VerdictStatus


def generate_markdown_report(verdict: PricingVerdict, output_path: Path) -> None:
    """Generate human-readable Markdown report.

    Sections:
    - Inputs
    - Evidence summary
    - Competitor comparison table
    - Verdict
    - Recommendation (verbal recommendation based on verdict)
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

    # Recommendation
    recommendation = _generate_recommendation(verdict)
    if recommendation:
        report_lines.extend(
            [
                "## Recommendation",
                "",
                recommendation,
                "",
            ]
        )

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


def _generate_recommendation(verdict: PricingVerdict) -> str:
    """Generate verbal recommendation based on verdict status.
    
    Args:
        verdict: Pricing verdict
        
    Returns:
        Recommendation text or empty string if undeterminable
    """
    product = verdict.evidence_bundle.product_input
    
    # Get comparable competitors for price calculations
    comparable = [
        cp
        for cp in verdict.evidence_bundle.competitor_pricing
        if cp.normalized_monthly_usd is not None
    ]
    
    if verdict.status == VerdictStatus.UNDETERMINABLE:
        return (
            f"**Nedoporučuje se** provádět změny ceny na základě současných dat. "
            f"Analýza nenašla dostatek srovnatelných konkurentů (nalezeno: {verdict.competitor_count}, "
            f"potřeba: minimálně 2). Doporučujeme:\n\n"
            f"- Získat více dat o cenách konkurentů\n"
            f"- Ověřit, zda jsou konkurenti skutečně srovnatelní s produktem {product.name}\n"
            f"- Zvážit manuální průzkum trhu před rozhodnutím o ceně"
        )
    
    if not comparable:
        return ""
    
    # Calculate average competitor price
    competitor_prices = [cp.normalized_monthly_usd for cp in comparable if cp.normalized_monthly_usd is not None]
    if not competitor_prices:
        return ""
    
    avg_competitor_price = sum(competitor_prices) / len(competitor_prices)
    min_price = min(competitor_prices)
    max_price = max(competitor_prices)
    
    # Parse current price to get numeric value
    from ptm.parsing import parse_price, normalize_to_monthly_usd
    
    current_parsed = parse_price(product.current_price)
    if not current_parsed:
        return ""
    
    current_normalized = normalize_to_monthly_usd(current_parsed)
    if current_normalized.gaps or current_normalized.monthly_usd is None:
        return ""
    
    current_price = current_normalized.monthly_usd
    price_diff = avg_competitor_price - current_price
    price_diff_percent = (price_diff / current_price) * 100 if current_price > 0 else 0
    
    if verdict.status == VerdictStatus.UNDERPRICED:
        recommended_price = avg_competitor_price * 0.9  # 90% of average (conservative)
        return (
            f"**Doporučení: Zvážit zvýšení ceny**\n\n"
            f"Současná cena produktu {product.name} (${current_price:.2f}/měsíc) je výrazně nižší než průměrná cena "
            f"konkurentů (${avg_competitor_price:.2f}/měsíc). Rozdíl činí {abs(price_diff_percent):.1f}%.\n\n"
            f"**Doporučená akce:**\n"
            f"- Zvážit zvýšení ceny na přibližně **${recommended_price:.2f}/měsíc** (90% průměru konkurentů)\n"
            f"- Toto by stále ponechalo produkt konkurenceschopný, ale lépe reflektovalo tržní hodnotu\n"
            f"- Rozsah cen konkurentů: ${min_price:.2f} - ${max_price:.2f}/měsíc\n\n"
            f"**Poznámka:** Před změnou ceny zvažte další faktory jako hodnotu produktu, cílovou skupinu, "
            f"a obchodní strategii. Důvěra v tuto analýzu: {verdict.confidence:.1%}."
        )
    
    elif verdict.status == VerdictStatus.OVERPRICED:
        recommended_price = avg_competitor_price * 1.1  # 110% of average (slightly above)
        return (
            f"**Doporučení: Zvážit snížení ceny**\n\n"
            f"Současná cena produktu {product.name} (${current_price:.2f}/měsíc) je výrazně vyšší než průměrná cena "
            f"konkurentů (${avg_competitor_price:.2f}/měsíc). Rozdíl činí {price_diff_percent:.1f}%.\n\n"
            f"**Doporučená akce:**\n"
            f"- Zvážit snížení ceny na přibližně **${recommended_price:.2f}/měsíc** (110% průměru konkurentů)\n"
            f"- Toto by produkt přiblížilo k tržnímu průměru, ale zachovalo by prémiovou pozici\n"
            f"- Rozsah cen konkurentů: ${min_price:.2f} - ${max_price:.2f}/měsíc\n\n"
            f"**Poznámka:** Pokud produkt nabízí výrazně lepší hodnotu než konkurenti, může být vyšší cena oprávněná. "
            f"Zvažte komunikaci hodnoty zákazníkům. Důvěra v tuto analýzu: {verdict.confidence:.1%}."
        )
    
    elif verdict.status == VerdictStatus.FAIR:
        return (
            f"**Doporučení: Ponechat současnou cenu**\n\n"
            f"Současná cena produktu {product.name} (${current_price:.2f}/měsíc) je v rozumném rozsahu "
            f"ve srovnání s konkurenty (průměr: ${avg_competitor_price:.2f}/měsíc, "
            f"rozsah: ${min_price:.2f} - ${max_price:.2f}/měsíc).\n\n"
            f"**Doporučená akce:**\n"
            f"- **Ponechat současnou cenu** - je konkurenceschopná a odpovídá tržnímu průměru\n"
            f"- Monitorovat změny cen konkurentů v budoucnu\n"
            f"- Zaměřit se na zlepšení hodnoty produktu spíše než na změnu ceny\n\n"
            f"**Poznámka:** Důvěra v tuto analýzu: {verdict.confidence:.1%}. "
            f"Pokud má produkt unikátní vlastnosti nebo vyšší hodnotu, může být oprávněná i mírně vyšší cena."
        )
    
    return ""
