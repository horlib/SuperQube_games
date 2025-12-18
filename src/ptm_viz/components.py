# -*- coding: utf-8 -*-
"""Reusable Streamlit components for PTM dashboard."""

from typing import Any

import streamlit as st


def render_verdict_panel(data: dict[str, Any]) -> None:
    """Render verdict status panel with confidence and breakdown.
    
    Args:
        data: Parsed report JSON
    """
    verdict = data.get("verdict", {})
    status = verdict.get("status", "UNDETERMINABLE")
    confidence = verdict.get("confidence", 0.0)
    key_reasons = verdict.get("key_reasons", [])
    evidence_bundle = verdict.get("evidence_bundle", {})
    
    # Status badges with emojis and CSS classes
    status_config = {
        "UNDERPRICED": {"emoji": "🟢", "color": "green", "label": "UNDERPRICED", "css_class": "underpriced"},
        "FAIR": {"emoji": "⚖️", "color": "blue", "label": "FAIR", "css_class": "fair"},
        "OVERPRICED": {"emoji": "🔴", "color": "red", "label": "OVERPRICED", "css_class": "overpriced"},
        "UNDETERMINABLE": {"emoji": "⚪", "color": "gray", "label": "UNDETERMINABLE", "css_class": "undeterminable"},
    }
    
    config = status_config.get(status, status_config["UNDETERMINABLE"])
    
    # Modern verdict badge with gradient and glow
    st.markdown(f"""
    <div class="verdict-badge {config['css_class']}" style="position: relative; z-index: 1;">
        <span style="font-size: 2rem; display: inline-block; margin-right: 0.5rem; animation: pulse 2s infinite;">{config['emoji']}</span>
        <span style="position: relative; z-index: 2;">{config['label']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Confidence metrics in cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        confidence_color = "#10b981" if confidence >= 0.8 else "#f59e0b" if confidence >= 0.5 else "#ef4444"
        st.markdown(f"""
        <div class="metric-card info" style="animation-delay: 0.1s;">
            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Confidence Level</div>
            <div style="font-size: 2.5rem; font-weight: 800; color: {confidence_color}; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{confidence:.1%}</div>
            <div style="font-size: 0.75rem; color: #9ca3af; margin-top: 0.3rem;">{'High' if confidence >= 0.8 else 'Medium' if confidence >= 0.5 else 'Low'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        sources_count = len(evidence_bundle.get("tavily_sources", []))
        st.markdown(f"""
        <div class="metric-card primary" style="animation-delay: 0.2s;">
            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Sources Analyzed</div>
            <div style="font-size: 2.5rem; font-weight: 800; color: #667eea; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{sources_count}</div>
            <div style="font-size: 0.75rem; color: #9ca3af; margin-top: 0.3rem;">{'Excellent' if sources_count >= 15 else 'Good' if sources_count >= 10 else 'Fair'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        competitor_count = verdict.get("competitor_count", 0)
        st.markdown(f"""
        <div class="metric-card success" style="animation-delay: 0.3s;">
            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Comparable Competitors</div>
            <div style="font-size: 2.5rem; font-weight: 800; color: #10b981; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{competitor_count}</div>
            <div style="font-size: 0.75rem; color: #9ca3af; margin-top: 0.3rem;">{'Strong' if competitor_count >= 5 else 'Moderate' if competitor_count >= 3 else 'Limited'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Confidence bar with custom styling
    st.markdown(f"<div style='margin-top: 1rem; margin-bottom: 0.5rem; font-weight: 500;'>Confidence: {confidence:.1%}</div>", unsafe_allow_html=True)
    st.progress(confidence, text="")
    
    # Confidence breakdown (expandable)
    with st.expander("📊 Confidence Breakdown"):
        sources_count = len(evidence_bundle.get("tavily_sources", []))
        competitor_count = verdict.get("competitor_count", 0)
        total_competitors = len(evidence_bundle.get("competitor_pricing", []))
        gaps_count = len(verdict.get("gaps", []))
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sources", sources_count)
        with col2:
            st.metric("Comparable Competitors", competitor_count)
        with col3:
            st.metric("Total Competitors", total_competitors)
        with col4:
            st.metric("Data Gaps", gaps_count)
        
        # Confidence factors
        st.markdown("**Confidence Factors:**")
        if competitor_count >= 3:
            st.success(f"✅ Sufficient comparable competitors ({competitor_count})")
        elif competitor_count == 2:
            st.warning(f"⚠️ Minimum comparable competitors ({competitor_count})")
        else:
            st.error(f"❌ Insufficient comparable competitors ({competitor_count})")
        
        if sources_count >= 10:
            st.success(f"✅ Good source coverage ({sources_count} sources)")
        elif sources_count >= 5:
            st.warning(f"⚠️ Moderate source coverage ({sources_count} sources)")
        else:
            st.error(f"❌ Limited source coverage ({sources_count} sources)")
        
        if gaps_count == 0:
            st.success("✅ No data gaps detected")
        elif gaps_count < 5:
            st.warning(f"⚠️ Some data gaps ({gaps_count})")
        else:
            st.error(f"❌ Many data gaps ({gaps_count})")
    
    # Key reasons
    if key_reasons:
        st.markdown("**Key Reasons:**")
        # Use st.text() for each reason to avoid LaTeX interpretation of $ signs
        # This displays plain text without markdown processing
        for reason in key_reasons:
            st.text(f"  • {reason}")
    
    # Special message for UNDETERMINABLE
    if status == "UNDETERMINABLE":
        gaps = verdict.get("gaps", [])
        if gaps:
            unique_gaps = list(set(gaps))[:3]  # Show first 3 unique gaps
            st.warning(f"**Why undeterminable:** {', '.join(unique_gaps)}")


def render_gaps_panel(data: dict[str, Any]) -> None:
    """Render gaps and limitations panel.
    
    Args:
        data: Parsed report JSON
    """
    verdict = data.get("verdict", {})
    gaps = verdict.get("gaps", [])
    
    if not gaps:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    padding: 2rem; border-radius: 16px; color: white; margin: 1.5rem 0;
                    box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
                    position: relative; overflow: hidden;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem; animation: pulse 2s infinite;">✅</div>
            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">No Major Gaps Detected</div>
            <div style="opacity: 0.95; font-size: 1rem;">The analysis has sufficient data quality.</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Deduplicate and limit gaps
    unique_gaps = list(set(gaps))
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                padding: 2rem; border-radius: 16px; color: white; margin: 1.5rem 0;
                box-shadow: 0 10px 30px rgba(245, 158, 11, 0.3);
                position: relative; overflow: hidden;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
        <div style="font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">Gaps & Limitations</div>
        <div style="opacity: 0.95; font-size: 1rem;">The following data gaps limit the confidence of this analysis:</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show gaps in expander if many
    if len(unique_gaps) > 10:
        with st.expander(f"📋 View all {len(unique_gaps)} gaps", expanded=False):
            for gap in unique_gaps:
                st.markdown(f"• {gap}")
        st.markdown(f"<div style='color: #6b7280; margin: 1rem 0;'>Showing first 10 of {len(unique_gaps)} unique gaps</div>", unsafe_allow_html=True)
        for gap in unique_gaps[:10]:
            st.markdown(f"""
            <div style='padding: 1rem; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                        border-left: 5px solid #f59e0b; border-radius: 8px; margin: 0.5rem 0;
                        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.15);
                        transition: all 0.2s;'>
                <span style='color: #92400e; font-weight: 500;'>•</span> 
                <span style='color: #78350f;'>{gap}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        for gap in unique_gaps:
            st.markdown(f"""
            <div style='padding: 1rem; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                        border-left: 5px solid #f59e0b; border-radius: 8px; margin: 0.5rem 0;
                        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.15);
                        transition: all 0.2s;'>
                <span style='color: #92400e; font-weight: 500;'>•</span> 
                <span style='color: #78350f;'>{gap}</span>
            </div>
            """, unsafe_allow_html=True)


def generate_recommendation(data: dict[str, Any]) -> str:
    """Generate recommendation text from report data.
    
    Args:
        data: Parsed report JSON
        
    Returns:
        Recommendation text or empty string
    """
    verdict = data.get("verdict", {})
    status = verdict.get("status", "UNDETERMINABLE")
    confidence = verdict.get("confidence", 0.0)
    evidence_bundle = verdict.get("evidence_bundle", {})
    product_input = evidence_bundle.get("product_input", {})
    competitor_pricing = evidence_bundle.get("competitor_pricing", [])
    
    # Get comparable competitors
    comparable = [
        cp for cp in competitor_pricing
        if cp.get("normalized_monthly_usd") is not None
    ]
    
    if status == "UNDETERMINABLE":
        competitor_count = verdict.get("competitor_count", 0)
        product_name = product_input.get("name", "produkt")
        return (
            f"### ❓ **Nedoporučuje se** provádět změny ceny\n\n"
            f"Analýza nenašla dostatek srovnatelných konkurentů (nalezeno: **{competitor_count}**, "
            f"potřeba: minimálně **2**).\n\n"
            f"**📋 Doporučené kroky:**\n\n"
            f"- 🔍 Získat více dat o cenách konkurentů\n"
            f"- ✅ Ověřit, zda jsou konkurenti skutečně srovnatelní s produktem `{product_name}`\n"
            f"- 📊 Zvážit manuální průzkum trhu před rozhodnutím o ceně"
        )
    
    if not comparable:
        return ""
    
    # Calculate statistics
    competitor_prices = [cp.get("normalized_monthly_usd") for cp in comparable]
    if not competitor_prices:
        return ""
    
    avg_competitor_price = sum(competitor_prices) / len(competitor_prices)
    min_price = min(competitor_prices)
    max_price = max(competitor_prices)
    
    # Parse current price
    current_price_str = product_input.get("current_price", "")
    if not current_price_str:
        return ""
    
    # Try to extract current price
    import re
    current_price = None
    match = re.search(r'\$([\d.]+)/month', current_price_str)
    if match:
        try:
            current_price = float(match.group(1))
        except ValueError:
            pass
    
    if current_price is None:
        return ""
    
    price_diff = avg_competitor_price - current_price
    price_diff_percent = (price_diff / current_price) * 100 if current_price > 0 else 0
    price_unit = "/měsíc"
    
    if status == "UNDERPRICED":
        recommended_price = avg_competitor_price * 0.9
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
            f"a obchodní strategii. Důvěra v tuto analýzu: **{confidence:.1%}**."
        )
    
    elif status == "OVERPRICED":
        recommended_price = avg_competitor_price * 1.1
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
            f"Zvažte komunikaci hodnoty zákazníkům. Důvěra v tuto analýzu: **{confidence:.1%}**."
        )
    
    elif status == "FAIR":
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
            f"**💡 Poznámka:** Důvěra v tuto analýzu: **{confidence:.1%}**. "
            f"Pokud má produkt unikátní vlastnosti nebo vyšší hodnotu, může být oprávněná i mírně vyšší cena."
        )
    
    return ""


def render_recommendation_panel(data: dict[str, Any]) -> None:
    """Render recommendation panel with enhanced styling.
    
    Args:
        data: Parsed report JSON
    """
    recommendation = generate_recommendation(data)
    
    if not recommendation:
        return
    
    # Determine color based on status
    verdict = data.get("verdict", {})
    status = verdict.get("status", "UNDETERMINABLE")
    
    if status == "UNDERPRICED":
        bg_gradient = "linear-gradient(135deg, #10b981 0%, #059669 100%)"
        border_color = "#10b981"
    elif status == "OVERPRICED":
        bg_gradient = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
        border_color = "#f59e0b"
    elif status == "FAIR":
        bg_gradient = "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
        border_color = "#3b82f6"
    else:
        bg_gradient = "linear-gradient(135deg, #6b7280 0%, #4b5563 100%)"
        border_color = "#6b7280"
    
    # Convert markdown to HTML with proper styling
    import re
    
    def markdown_to_html(text: str) -> str:
        """Convert markdown to HTML with white text styling."""
        # Handle headers
        text = re.sub(r'### (.+?)$', r'<h3 style="font-size: 1.5rem; font-weight: 700; margin: 1.5rem 0 1rem 0; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">\1</h3>', text, flags=re.MULTILINE)
        # Handle bold **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Handle code `text`
        text = re.sub(r'`(.+?)`', r'<code style="background: rgba(255,255,255,0.25); padding: 0.2rem 0.5rem; border-radius: 4px; font-family: monospace; font-weight: 600;">\1</code>', text)
        # Handle list items
        text = re.sub(r'^- (.+?)$', r'<div style="margin: 0.75rem 0; padding-left: 1rem; line-height: 1.6;">• \1</div>', text, flags=re.MULTILINE)
        # Handle empty lines
        text = re.sub(r'\n\n', '<br><br>', text)
        # Handle regular paragraphs (lines that don't start with #, -, or **)
        lines = text.split('\n')
        result = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('<') and not line.startswith('**📋') and not line.startswith('**📊') and not line.startswith('**🎯') and not line.startswith('**⚠️') and not line.startswith('**💡'):
                if not line.startswith('**') or (line.startswith('**') and line.count('**') == 2):
                    result.append(f'<div style="margin: 0.5rem 0; line-height: 1.6; opacity: 0.95;">{line}</div>')
            elif line.startswith('**📋') or line.startswith('**📊') or line.startswith('**🎯') or line.startswith('**⚠️') or line.startswith('**💡'):
                result.append(f'<div style="font-size: 1.1rem; font-weight: 700; margin: 1.5rem 0 0.75rem 0; opacity: 0.95;">{line}</div>')
            elif not line:
                result.append('<br>')
        return ''.join(result) if result else text
    
    html_content = markdown_to_html(recommendation)
    
    st.markdown(f"""
    <div style="background: {bg_gradient}; 
                padding: 2.5rem; border-radius: 16px; color: white; margin: 1.5rem 0;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                border-left: 6px solid {border_color};
                position: relative; overflow: hidden;
                animation: fadeInUp 0.8s ease-out;">
        <div style="position: relative; z-index: 2; color: white;">
            {html_content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_citations_list(data: dict[str, Any]) -> None:
    """Render citations list with clickable links.
    
    Args:
        data: Parsed report JSON
    """
    verdict = data.get("verdict", {})
    citations = verdict.get("citations", [])
    
    if not citations:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                    padding: 2rem; border-radius: 16px; color: white; margin: 1.5rem 0;
                    box-shadow: 0 10px 30px rgba(245, 158, 11, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
            <div style="font-size: 1.2rem; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">No Citations Available</div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("### 📚 Citations")
    st.markdown("<div style='color: #6b7280; margin-bottom: 1rem;'>Sources used in this analysis:</div>", unsafe_allow_html=True)
    
    # Limit to 20 citations for readability
    display_citations = citations[:20]
    
    # Create a styled list with enhanced effects
    citations_html = "<div style='background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);'>"
    for i, citation in enumerate(display_citations, 1):
        citation_str = str(citation)
        citations_html += f"""
        <div style='padding: 1rem; margin: 0.75rem 0; border-left: 5px solid #667eea; border-radius: 8px; 
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                    animation: fadeInUp 0.4s ease-out;
                    animation-delay: {i * 0.05}s;
                    animation-fill-mode: both;'>
            <span style='color: #667eea; font-weight: 700; font-size: 1.1rem; margin-right: 0.75rem;'>{i}.</span>
            <a href='{citation_str}' target='_blank' 
               style='color: #3b82f6; text-decoration: none; font-weight: 500;
                      transition: all 0.2s; display: inline-block;'
               onmouseover="this.style.color='#667eea'; this.style.transform='translateX(4px)'"
               onmouseout="this.style.color='#3b82f6'; this.style.transform='translateX(0)'">
               {citation_str}
            </a>
        </div>
        """
    citations_html += "</div>"
    
    st.markdown(citations_html, unsafe_allow_html=True)
    
    if len(citations) > 20:
        st.markdown(f"<div style='color: #6b7280; margin-top: 1rem;'>Showing first 20 of {len(citations)} citations</div>", unsafe_allow_html=True)


def render_evidence_table(competitor_df: Any) -> None:
    """Render evidence table with expandable details, filtering, and export.
    
    Args:
        competitor_df: DataFrame from build_competitor_table
    """
    if competitor_df.empty:
        st.info("No competitor data available.")
        return
    
    st.markdown("### 🔍 Evidence Table")
    st.markdown("<div style='margin-bottom: 1rem; color: #6b7280;'>Detailed evidence with source URLs and verbatim quotes</div>", unsafe_allow_html=True)
    
    # Filtering options with modern styling
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # Filter by normalized price availability
        show_only_comparable = st.checkbox("Show only comparable prices", value=False)
    
    with col2:
        # Search filter
        search_term = st.text_input("🔍 Search competitors", placeholder="Filter by name...")
    
    with col3:
        # Export button
        csv = competitor_df[["Competitor", "Source URL", "Price Evidence (verbatim)", "Normalized Monthly USD", "Notes"]].to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            csv,
            "competitor_pricing.csv",
            "text/csv",
            key="download-csv",
        )
    
    # Apply filters
    filtered_df = competitor_df.copy()
    
    if show_only_comparable:
        filtered_df = filtered_df[filtered_df["Normalized Value"].notna()]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df["Competitor"].str.contains(search_term, case=False, na=False)
        ]
    
    # Sort options
    sort_option = st.selectbox(
        "Sort by:",
        ["Competitor (A-Z)", "Competitor (Z-A)", "Price (Low to High)", "Price (High to Low)"],
    )
    
    if sort_option == "Price (Low to High)":
        filtered_df = filtered_df.sort_values("Normalized Value", ascending=True, na_last=True)
    elif sort_option == "Price (High to Low)":
        filtered_df = filtered_df.sort_values("Normalized Value", ascending=False, na_last=True)
    elif sort_option == "Competitor (A-Z)":
        filtered_df = filtered_df.sort_values("Competitor", ascending=True)
    else:  # Z-A
        filtered_df = filtered_df.sort_values("Competitor", ascending=False)
    
    st.markdown(f"*Showing {len(filtered_df)} of {len(competitor_df)} competitors*")
    
    # Display main table (without internal columns)
    display_cols = ["Competitor", "Source URL", "Price Evidence (verbatim)", "Normalized Monthly USD", "Notes"]
    display_df = filtered_df[display_cols].copy()
    
    # Make URLs clickable in display
    def make_url_clickable(url: str) -> str:
        if url and url != "":
            return f"[Link]({url})"
        return "N/A"
    
    display_df["Source URL"] = display_df["Source URL"].apply(make_url_clickable)
    
    # Show table with custom styling
    st.markdown("""
    <style>
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400,
    )
    
    # Add expanders for each competitor with full evidence
    for idx, row in filtered_df.iterrows():
        with st.expander(f"🔍 {row['Competitor']} - Full Evidence"):
            st.markdown(f"**Source URL:** [{row['Source URL']}]({row['Source URL']})" if row['Source URL'] else "**Source URL:** N/A")
            
            st.markdown("**All Extracted Price Texts:**")
            price_texts = row.get("All Price Texts", [])
            if price_texts:
                for text in price_texts:
                    st.code(text)
            else:
                st.markdown("*No price texts extracted*")
            
            st.markdown("**Evidence Snippets:**")
            snippets = row.get("Evidence Snippets", [])
            if snippets:
                for snippet in snippets[:5]:  # Limit to 5 snippets
                    st.markdown(f"> {snippet}")
                if len(snippets) > 5:
                    st.caption(f"*Showing first 5 of {len(snippets)} snippets*")
            else:
                st.markdown("*No evidence snippets*")
            
            if row["Notes"]:
                st.markdown(f"**Notes:** {row['Notes']}")
