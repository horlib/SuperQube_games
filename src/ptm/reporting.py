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
    - Citations

    Args:
        verdict: Pricing verdict
        output_path: Path to write report.md
    """
    product = verdict.evidence_bundle.product_input

    report_lines = [
        "# 💰 Pricing Analysis Report",
        "",
        f"<div align='right'>📅 **Generated:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`</div>",
        "",
        "---",
        "",
        "## 📋 Inputs",
        "",
        f"| **Field** | **Value** |",
        "|-----------|-----------|",
        f"| 🏷️ **Product Name** | `{product.name}` |",
        f"| 🔗 **Product URL** | [{product.url}]({product.url}) |",
        f"| 💵 **Current Price** | **`{product.current_price}`** |",
        "",
    ]

    if product.competitor_urls:
        report_lines.extend(
            [
                "### 🎯 Competitor URLs Provided",
                "",
            ]
        )
        for url in product.competitor_urls:
            report_lines.append(f"- 🔗 [{url}]({url})")
        report_lines.append("")

    # Evidence summary with visual KPI cards
    sources_count = len(verdict.evidence_bundle.tavily_sources)
    competitors_analyzed = len(verdict.evidence_bundle.competitor_pricing)
    comparable_count = verdict.competitor_count
    
    report_lines.extend(
        [
            "## 📊 Evidence Summary",
            "",
            "| **Metric** | **Value** | **Status** |",
            "|------------|-----------|------------|",
            f"| 🔍 **Sources Retrieved** | `{sources_count}` | {'✅' if sources_count >= 10 else '⚠️' if sources_count >= 5 else '❌'} |",
            f"| 🏢 **Competitors Analyzed** | `{competitors_analyzed}` | {'✅' if competitors_analyzed >= 5 else '⚠️' if competitors_analyzed >= 2 else '❌'} |",
            f"| ⚖️ **Comparable Competitors** | `{comparable_count}` | {'✅' if comparable_count >= 2 else '⚠️'} |",
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
        # Determine if prices are one-time or recurring
        # Check if ALL comparable prices are one-time, or if any are recurring
        cadences = [cp.cadence for cp in comparable if cp.cadence]
        is_one_time = len(cadences) > 0 and all(c == "one-time" for c in cadences)
        price_label = "Price (One-time USD)" if is_one_time else "Normalized (Monthly USD)"
        
        # Calculate price range for context
        prices = [cp.normalized_monthly_usd for cp in comparable if cp.normalized_monthly_usd is not None]
        min_price_val = min(prices) if prices else 0
        max_price_val = max(prices) if prices else 0
        
        report_lines.extend(
            [
                "## 💼 Competitor Comparison",
                "",
                f"**Price Range:** ${min_price_val:.2f} - ${max_price_val:.2f}",
                "",
                f"| 🏢 **Competitor** | 💵 **Price** | 📈 **{price_label}** | 📄 **Evidence** |",
                "|------------------|---------------|------------------------|----------------|",
            ]
        )

        for cp in comparable[:10]:  # Limit to 10 for readability
            price_text = cp.extracted_price_texts[0] if cp.extracted_price_texts else "N/A"
            normalized = f"${cp.normalized_monthly_usd:.2f}" if cp.normalized_monthly_usd else "N/A"
            evidence_count = len(cp.evidence_snippets)
            evidence_indicator = "📊" * min(evidence_count, 3)  # Visual indicator for evidence strength
            report_lines.append(
                f"| `{cp.domain}` | `{price_text}` | **{normalized}** | {evidence_count} snippet(s) {evidence_indicator} |"
            )

        report_lines.append("")

    # Verdict with enhanced visual display
    status_emoji = {
        "UNDERPRICED": "✅",
        "FAIR": "⚖️",
        "OVERPRICED": "⚠️",
        "UNDETERMINABLE": "❓",
    }
    
    status_badge = {
        "UNDERPRICED": "🟢",
        "FAIR": "🟡",
        "OVERPRICED": "🔴",
        "UNDETERMINABLE": "⚪",
    }
    
    # Create visual confidence bar
    confidence_percent = int(verdict.confidence * 100)
    confidence_bar_length = 20
    filled_bars = int(confidence_percent / 100 * confidence_bar_length)
    confidence_bar = "█" * filled_bars + "░" * (confidence_bar_length - filled_bars)
    
    confidence_color = "🟢" if verdict.confidence >= 0.8 else "🟡" if verdict.confidence >= 0.5 else "🔴"

    report_lines.extend(
        [
            "## ⚖️ Verdict",
            "",
            f"### {status_badge.get(verdict.status.value, '')} **{verdict.status.value}** {status_emoji.get(verdict.status.value, '')}",
            "",
            f"**Confidence:** {confidence_color} `{verdict.confidence:.1%}`",
            "",
            f"`{confidence_bar}` {confidence_percent}%",
            "",
            "### 🔑 Key Reasons",
            "",
        ]
    )

    for i, reason in enumerate(verdict.key_reasons, 1):
        report_lines.append(f"{i}. {reason}")

    report_lines.append("")

    # Recommendation with enhanced formatting
    recommendation = _generate_recommendation(verdict)
    if recommendation:
        report_lines.extend(
            [
                "## 💡 Recommendation",
                "",
                "<div style='background-color: #f0f8ff; padding: 15px; border-left: 4px solid #0066cc; border-radius: 5px;'>",
                "",
                recommendation,
                "",
                "</div>",
                "",
            ]
        )

    # Citations with enhanced formatting
    if verdict.citations:
        report_lines.extend(
            [
                "## 📚 Citations",
                "",
                "**Sources used in this analysis:**",
                "",
            ]
        )

        for i, citation in enumerate(verdict.citations[:20], 1):  # Limit to 20
            # Try to make citation clickable if it's a URL
            citation_str = str(citation)  # Convert URL object to string if needed
            if citation_str.startswith("http"):
                report_lines.append(f"{i}. 🔗 [{citation_str}]({citation_str})")
            else:
                report_lines.append(f"{i}. 📄 {citation_str}")

        if len(verdict.citations) > 20:
            report_lines.append(f"\n*... and {len(verdict.citations) - 20} more sources*")

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
            f"### ❓ **Nedoporučuje se** provádět změny ceny\n\n"
            f"Analýza nenašla dostatek srovnatelných konkurentů (nalezeno: **{verdict.competitor_count}**, "
            f"potřeba: minimálně **2**).\n\n"
            f"**📋 Doporučené kroky:**\n\n"
            f"- 🔍 Získat více dat o cenách konkurentů\n"
            f"- ✅ Ověřit, zda jsou konkurenti skutečně srovnatelní s produktem `{product.name}`\n"
            f"- 📊 Zvážit manuální průzkum trhu před rozhodnutím o ceně"
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
    
    # Check if prices are one-time purchases
    is_one_time = any(cp.cadence == "one-time" for cp in comparable if cp.cadence)
    price_unit = "" if is_one_time else "/měsíc"
    
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
            f"### ✅ **Doporučení: Zvážit zvýšení ceny**\n\n"
            f"**📊 Současná situace:**\n\n"
            f"- 💵 Vaše cena: **`${current_price:.2f}{price_unit}`**\n"
            f"- 📈 Průměr konkurentů: **`${avg_competitor_price:.2f}{price_unit}`**\n"
            f"- 📉 Rozdíl: **`{abs(price_diff_percent):.1f}%`** nižší než průměr\n\n"
            f"**🎯 Doporučená akce:**\n\n"
            f"- 💰 Zvážit zvýšení ceny na přibližně **`${recommended_price:.2f}{price_unit}`** (90% průměru konkurentů)\n"
            f"- ✅ Toto by stále ponechalo produkt konkurenceschopný, ale lépe reflektovalo tržní hodnotu\n"
            f"- 📊 Rozsah cen konkurentů: **`${min_price:.2f} - ${max_price:.2f}{price_unit}`**\n\n"
            f"**⚠️ Poznámka:** Před změnou ceny zvažte další faktory jako hodnotu produktu, cílovou skupinu, "
            f"a obchodní strategii. Důvěra v tuto analýzu: **{verdict.confidence:.1%}**."
        )
    
    elif verdict.status == VerdictStatus.OVERPRICED:
        recommended_price = avg_competitor_price * 1.1  # 110% of average (slightly above)
        return (
            f"### ⚠️ **Doporučení: Zvážit snížení ceny**\n\n"
            f"**📊 Současná situace:**\n\n"
            f"- 💵 Vaše cena: **`${current_price:.2f}{price_unit}`**\n"
            f"- 📈 Průměr konkurentů: **`${avg_competitor_price:.2f}{price_unit}`**\n"
            f"- 📉 Rozdíl: **`{price_diff_percent:.1f}%`** vyšší než průměr\n\n"
            f"**🎯 Doporučená akce:**\n\n"
            f"- 💰 Zvážit snížení ceny na přibližně **`${recommended_price:.2f}{price_unit}`** (110% průměru konkurentů)\n"
            f"- ✅ Toto by produkt přiblížilo k tržnímu průměru, ale zachovalo by prémiovou pozici\n"
            f"- 📊 Rozsah cen konkurentů: **`${min_price:.2f} - ${max_price:.2f}{price_unit}`**\n\n"
            f"**💡 Poznámka:** Pokud produkt nabízí výrazně lepší hodnotu než konkurenti, může být vyšší cena oprávněná. "
            f"Zvažte komunikaci hodnoty zákazníkům. Důvěra v tuto analýzu: **{verdict.confidence:.1%}**."
        )
    
    elif verdict.status == VerdictStatus.FAIR:
        return (
            f"### ✅ **Doporučení: Ponechat současnou cenu**\n\n"
            f"**📊 Současná situace:**\n\n"
            f"- 💵 Vaše cena: **`${current_price:.2f}{price_unit}`**\n"
            f"- 📈 Průměr konkurentů: **`${avg_competitor_price:.2f}{price_unit}`**\n"
            f"- 📊 Rozsah cen: **`${min_price:.2f} - ${max_price:.2f}{price_unit}`**\n\n"
            f"**🎯 Doporučená akce:**\n\n"
            f"- ✅ **Ponechat současnou cenu** - je konkurenceschopná a odpovídá tržnímu průměru\n"
            f"- 👀 Monitorovat změny cen konkurentů v budoucnu\n"
            f"- 🚀 Zaměřit se na zlepšení hodnoty produktu spíše než na změnu ceny\n\n"
            f"**💡 Poznámka:** Důvěra v tuto analýzu: **{verdict.confidence:.1%}**. "
            f"Pokud má produkt unikátní vlastnosti nebo vyšší hodnotu, může být oprávněná i mírně vyšší cena."
        )
    
    return ""
