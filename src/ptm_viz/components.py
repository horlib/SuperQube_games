# -*- coding: utf-8 -*-
"""Reusable Streamlit components for PTM dashboard."""

from typing import Any

import streamlit as st


def render_verdict_panel(data: dict[str, Any]) -> None:
    """Render verdict status panel with confidence.
    
    Args:
        data: Parsed report JSON
    """
    verdict = data.get("verdict", {})
    status = verdict.get("status", "UNDETERMINABLE")
    confidence = verdict.get("confidence", 0.0)
    key_reasons = verdict.get("key_reasons", [])
    
    # Status badges with emojis
    status_config = {
        "UNDERPRICED": {"emoji": "🟢", "color": "green", "label": "UNDERPRICED"},
        "FAIR": {"emoji": "⚖️", "color": "blue", "label": "FAIR"},
        "OVERPRICED": {"emoji": "🔴", "color": "red", "label": "OVERPRICED"},
        "UNDETERMINABLE": {"emoji": "⚪", "color": "gray", "label": "UNDETERMINABLE"},
    }
    
    config = status_config.get(status, status_config["UNDETERMINABLE"])
    
    # Create columns for status and confidence
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### {config['emoji']} **{config['label']}**")
    
    with col2:
        st.metric("Confidence", f"{confidence:.1%}")
    
    # Confidence bar
    st.progress(confidence, text=f"Confidence: {confidence:.1%}")
    
    # Key reasons
    if key_reasons:
        st.markdown("**Key Reasons:**")
        for reason in key_reasons:
            st.markdown(f"- {reason}")
    
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
        st.info("✅ No major gaps detected.")
        return
    
    # Deduplicate and limit gaps
    unique_gaps = list(set(gaps))
    
    st.warning("**⚠️ Gaps & Limitations**")
    st.markdown("The following data gaps limit the confidence of this analysis:")
    
    # Show gaps in expander if many
    if len(unique_gaps) > 10:
        with st.expander(f"View all {len(unique_gaps)} gaps"):
            for gap in unique_gaps:
                st.markdown(f"- {gap}")
        st.markdown(f"*Showing first 10 of {len(unique_gaps)} unique gaps*")
        for gap in unique_gaps[:10]:
            st.markdown(f"- {gap}")
    else:
        for gap in unique_gaps:
            st.markdown(f"- {gap}")


def render_citations_list(data: dict[str, Any]) -> None:
    """Render citations list with clickable links.
    
    Args:
        data: Parsed report JSON
    """
    verdict = data.get("verdict", {})
    citations = verdict.get("citations", [])
    
    if not citations:
        st.warning("⚠️ No citations were produced.")
        return
    
    st.markdown("**Citations:**")
    st.markdown("Sources used in this analysis:")
    
    # Limit to 20 citations for readability
    display_citations = citations[:20]
    
    for i, citation in enumerate(display_citations, 1):
        citation_str = str(citation)
        st.markdown(f"{i}. [{citation_str}]({citation_str})")
    
    if len(citations) > 20:
        st.caption(f"*Showing first 20 of {len(citations)} citations*")


def render_evidence_table(competitor_df: Any) -> None:
    """Render evidence table with expandable details.
    
    Args:
        competitor_df: DataFrame from build_competitor_table
    """
    if competitor_df.empty:
        st.info("No competitor data available.")
        return
    
    st.markdown("### Evidence Table")
    st.markdown("Click on a competitor to see detailed evidence.")
    
    # Display main table (without internal columns)
    display_cols = ["Competitor", "Source URL", "Price Evidence (verbatim)", "Normalized Monthly USD", "Notes"]
    display_df = competitor_df[display_cols].copy()
    
    # Make URLs clickable in display
    def make_url_clickable(url: str) -> str:
        if url and url != "":
            return f"[Link]({url})"
        return "N/A"
    
    display_df["Source URL"] = display_df["Source URL"].apply(make_url_clickable)
    
    # Show table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
    
    # Add expanders for each competitor with full evidence
    for idx, row in competitor_df.iterrows():
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
