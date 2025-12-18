# -*- coding: utf-8 -*-
"""Streamlit dashboard for Pricing Truth Machine visualizations."""

from pathlib import Path

import pandas as pd
import streamlit as st

from ptm_viz.charts import create_price_comparison_chart
from ptm_viz.components import (
    render_citations_list,
    render_evidence_table,
    render_gaps_panel,
    render_recommendation_panel,
    render_verdict_panel,
)
from ptm_viz.loader import load_report_json, validate_report_structure
from ptm_viz.transforms import (
    build_competitor_table,
    build_price_comparison_data,
    calculate_price_statistics,
    get_product_info,
)

# Page config
st.set_page_config(
    page_title="Pricing Truth Machine - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for modern, sexy design
st.markdown("""
<style>
    /* Modern color palette */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --success-gradient: linear-gradient(135deg, #10b981 0%, #059669 100%);
        --warning-gradient: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        --danger-gradient: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        --info-gradient: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        --neutral-gradient: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
    
    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }
    
    @keyframes glow {
        0%, 100% {
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
        }
        50% {
            box-shadow: 0 0 30px rgba(102, 126, 234, 0.8);
        }
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Hero section with enhanced effects */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1);
        color: white;
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.8s ease-out;
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shimmer 3s infinite;
    }
    
    .hero-section h1 {
        color: white !important;
        font-size: 3rem !important;
        font-weight: 800 !important;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        position: relative;
        z-index: 1;
        letter-spacing: -0.5px;
    }
    
    .hero-section p {
        color: rgba(255, 255, 255, 0.95) !important;
        font-size: 1.2rem;
        font-weight: 300;
        position: relative;
        z-index: 1;
        letter-spacing: 0.3px;
    }
    
    /* Modern cards with enhanced effects */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.8rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border-left: 5px solid;
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transition: left 0.5s;
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
    }
    
    .metric-card.primary { 
        border-left-color: #667eea;
        background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
    }
    .metric-card.primary:hover {
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.25);
    }
    
    .metric-card.success { 
        border-left-color: #10b981;
        background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
    }
    .metric-card.success:hover {
        box-shadow: 0 12px 30px rgba(16, 185, 129, 0.25);
    }
    
    .metric-card.warning { 
        border-left-color: #f59e0b;
        background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
    }
    .metric-card.warning:hover {
        box-shadow: 0 12px 30px rgba(245, 158, 11, 0.25);
    }
    
    .metric-card.danger { 
        border-left-color: #ef4444;
        background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
    }
    .metric-card.danger:hover {
        box-shadow: 0 12px 30px rgba(239, 68, 68, 0.25);
    }
    
    .metric-card.info { 
        border-left-color: #3b82f6;
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
    }
    .metric-card.info:hover {
        box-shadow: 0 12px 30px rgba(59, 130, 246, 0.25);
    }
    
    /* Verdict badge styling with glow effects */
    .verdict-badge {
        display: inline-block;
        padding: 1.5rem 3rem;
        border-radius: 20px;
        font-size: 1.8rem;
        font-weight: 800;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.2);
        color: white;
        margin: 1.5rem 0;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.8s ease-out, pulse 2s infinite;
        letter-spacing: 1px;
    }
    
    .verdict-badge::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
        animation: shimmer 2s infinite;
    }
    
    .verdict-badge.fair {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
        box-shadow: 0 10px 40px rgba(59, 130, 246, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.2);
    }
    
    .verdict-badge.underpriced {
        background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.2);
    }
    
    .verdict-badge.overpriced {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #b91c1c 100%);
        box-shadow: 0 10px 40px rgba(239, 68, 68, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.2);
    }
    
    .verdict-badge.undeterminable {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 50%, #374151 100%);
        box-shadow: 0 10px 40px rgba(107, 114, 128, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.2);
    }
    
    /* Progress bar styling with animation */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        background-size: 200% 100%;
        border-radius: 12px;
        animation: shimmer 2s infinite;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
    }
    
    /* Table styling with enhanced effects */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    .dataframe thead {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
    }
    
    .dataframe thead th {
        padding: 1rem;
        border: none;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .dataframe tbody tr {
        transition: all 0.2s ease;
    }
    
    .dataframe tbody tr:hover {
        background-color: #e9ecef;
        transform: scale(1.01);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .dataframe tbody td {
        padding: 0.75rem 1rem;
        border-color: rgba(0, 0, 0, 0.05);
    }
    
    /* Section headers with gradient text */
    h2, h3 {
        color: #1f2937 !important;
        font-weight: 700 !important;
        margin-top: 2.5rem !important;
        margin-bottom: 1.5rem !important;
        position: relative;
        padding-bottom: 0.5rem;
        animation: fadeInUp 0.6s ease-out;
    }
    
    h2::after, h3::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 2px;
    }
    
    /* Custom divider with animation */
    hr {
        border: none;
        height: 3px;
        background: linear-gradient(90deg, transparent, #667eea, #764ba2, #667eea, transparent);
        background-size: 200% 100%;
        margin: 3rem 0;
        border-radius: 2px;
        animation: shimmer 3s infinite;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    [data-testid="stSidebar"] .sidebar-content {
        padding-top: 1rem;
    }
    
    /* File uploader styling with enhanced effects */
    .stFileUploader > div {
        border-radius: 12px;
        border: 3px dashed #667eea;
        padding: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%);
    }
    
    .stFileUploader > div:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
    }
    
    /* Checkbox styling */
    .stCheckbox {
        font-weight: 500;
    }
    
    /* Button styling with enhanced effects */
    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0) scale(0.98);
    }
    
    /* Expander styling with enhanced effects */
    .streamlit-expanderHeader {
        font-weight: 600;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        transition: all 0.2s;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #f8f9fa 100%);
        transform: translateX(4px);
    }
    
    /* Smooth scroll */
    html {
        scroll-behavior: smooth;
    }
    
    /* Additional polish */
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Info boxes */
    .stInfo {
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
    }
    
    .stSuccess {
        border-left: 4px solid #10b981;
        border-radius: 8px;
    }
    
    .stWarning {
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
    }
    
    .stError {
        border-left: 4px solid #ef4444;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section with enhanced design
st.markdown("""
<div class="hero-section">
    <div style="position: relative; z-index: 2;">
        <h1>📊 Pricing Truth Machine</h1>
        <p style="font-size: 1.3rem; font-weight: 300; letter-spacing: 0.5px;">Evidence-based pricing analysis visualization</p>
        <div style="margin-top: 1.5rem; display: flex; gap: 1rem; flex-wrap: wrap;">
            <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; backdrop-filter: blur(10px);">✨ Modern Design</span>
            <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; backdrop-filter: blur(10px);">📊 Interactive Charts</span>
            <span style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem; backdrop-filter: blur(10px);">🔍 Evidence-Based</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar - File selection
st.sidebar.header("📁 Load Report")
st.sidebar.markdown("Upload a `report.json` file or select from local directory.")

uploaded_file = st.sidebar.file_uploader(
    "Upload report.json",
    type=["json"],
    help="Upload a report.json file generated by PTM",
)

# Also allow selecting from output directory
output_dir = Path("output")
report_path = None

# Find all available reports
available_reports = []
if output_dir.exists():
    available_reports = list(output_dir.glob("report*.json"))

if uploaded_file is not None:
    # Save uploaded file temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as tmp:
        import json
        data = json.load(uploaded_file)
        json.dump(data, tmp)
        report_path = Path(tmp.name)
else:
    # Show available reports
    if available_reports:
        st.sidebar.markdown("**Available Reports:**")
        selected_report = st.sidebar.selectbox(
            "Select report:",
            options=[str(p) for p in available_reports],
            format_func=lambda x: Path(x).name,
        )
        if selected_report:
            report_path = Path(selected_report)
    else:
        st.sidebar.info("No reports found. Upload a report.json file.")

# Manual path input
manual_path = st.sidebar.text_input(
    "Or enter file path:",
    value="output/report.json",
    help="Enter path to report.json file",
)

if manual_path and Path(manual_path).exists():
    if st.sidebar.button("📂 Load from Path", use_container_width=True):
        report_path = Path(manual_path)

# Load and validate report
if report_path and report_path.exists():
    data = load_report_json(report_path)
    
    if data:
        is_valid, warnings = validate_report_structure(data)
        
        if warnings:
            for warning in warnings:
                st.sidebar.warning(warning)
        
        if is_valid or data:  # Proceed even with warnings
            # Get product info
            product_info = get_product_info(data)
            
            # Modern product header with cards
            st.markdown("### 🎯 Product Analysis")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card primary" style="animation-delay: 0.1s;">
                    <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Product Name</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937; line-height: 1.3;">{product_info['name']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                url_display = product_info['url'] if product_info['url'] else "N/A"
                st.markdown(f"""
                <div class="metric-card info" style="animation-delay: 0.2s;">
                    <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Product URL</div>
                    <div style="font-size: 1rem; font-weight: 500; color: #3b82f6; word-break: break-all;">
                        <a href="{product_info['url']}" target="_blank" 
                           style="color: #3b82f6; text-decoration: none; transition: all 0.2s;"
                           onmouseover="this.style.color='#667eea'; this.style.textDecoration='underline'"
                           onmouseout="this.style.color='#3b82f6'; this.style.textDecoration='none'">
                           {url_display[:40]}{'...' if len(url_display) > 40 else ''}
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card success" style="animation-delay: 0.3s;">
                    <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Current Price</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #10b981; text-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);">{product_info['current_price']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Verdict panel
            st.markdown("### ⚖️ Verdict")
            render_verdict_panel(data)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Recommendation panel
            st.markdown("### 💡 Recommendation")
            render_recommendation_panel(data)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Price comparison chart
            st.markdown("### 📈 Price Comparison")
            comparison_df, current_price = build_price_comparison_data(data)
            
            if not comparison_df.empty:
                # Build competitor details for interactive chart
                competitor_df = build_competitor_table(data)
                competitor_details = {}
                for _, row in competitor_df.iterrows():
                    if pd.notna(row.get("Normalized Value")):
                        competitor_details[row["Competitor"]] = {
                            "price_evidence": row.get("Price Evidence (verbatim)", "N/A"),
                            "source_url": row.get("Source URL", ""),
                        }
                
                chart = create_price_comparison_chart(
                    comparison_df,
                    product_name=product_info["name"],
                    competitor_details=competitor_details if competitor_details else None,
                )
                st.plotly_chart(chart, use_container_width=True)
                
                # Calculate and show detailed statistics
                stats = calculate_price_statistics(comparison_df, current_price)
                
                if stats:
                    st.markdown("### 📊 Price Statistics")
                    
                    # Main metrics row with modern cards
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        price_display = f"${current_price:.2f}" if current_price is not None else "N/A"
                        st.markdown(f"""
                        <div class="metric-card danger">
                            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.3rem;">Your Price</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #ef4444;">{price_display}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card primary">
                            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.3rem;">Mean</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #667eea;">${stats['mean']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card info">
                            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.3rem;">Median</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #3b82f6;">${stats['median']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class="metric-card success">
                            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.3rem;">Minimum</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #10b981;">${stats['min']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col5:
                        st.markdown(f"""
                        <div class="metric-card warning">
                            <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.3rem;">Maximum</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #f59e0b;">${stats['max']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Additional statistics in expander
                    with st.expander("📈 Detailed Statistics"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Distribution:**")
                            st.metric("Standard Deviation", f"${stats['std']:.2f}")
                            st.metric("Q25 (25th percentile)", f"${stats['q25']:.2f}")
                            st.metric("Q75 (75th percentile)", f"${stats['q75']:.2f}")
                            st.metric("Range", f"${stats['max'] - stats['min']:.2f}")
                        
                        with col2:
                            if current_price is not None and "current_vs_mean" in stats:
                                st.markdown("**Your Price vs Market:**")
                                diff = stats["current_vs_mean"]
                                diff_pct = stats["current_vs_mean_pct"]
                                if diff < 0:
                                    st.metric("Below Average", f"${abs(diff):.2f} ({abs(diff_pct):.1f}%)", delta=f"{diff_pct:.1f}%")
                                else:
                                    st.metric("Above Average", f"${diff:.2f} ({diff_pct:.1f}%)", delta=f"{diff_pct:.1f}%")
                                
                                percentile = stats.get("current_percentile", 0)
                                st.metric("Price Percentile", f"{percentile:.1f}%")
                                
                                # Interpretation
                                if percentile < 25:
                                    st.info("💡 Your price is in the **bottom quartile** - significantly below market average")
                                elif percentile < 50:
                                    st.info("💡 Your price is **below median** - competitive pricing")
                                elif percentile < 75:
                                    st.info("💡 Your price is **above median** - premium positioning")
                                else:
                                    st.info("💡 Your price is in the **top quartile** - premium pricing")
            else:
                st.markdown("""
                <div style="background: #fef3c7; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #f59e0b; margin: 1rem 0;">
                    <div style="font-weight: 600; color: #92400e; margin-bottom: 0.5rem;">ℹ️ No Comparable Prices Available</div>
                    <div style="color: #78350f;">This may be due to missing cadence information or normalization issues.</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Evidence table
            competitor_df = build_competitor_table(data)
            render_evidence_table(competitor_df)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Gaps panel
            st.markdown("### ⚠️ Gaps & Limitations")
            render_gaps_panel(data)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Citations
            render_citations_list(data)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Optional: Dataflow diagram (Mermaid)
            with st.expander("🔧 Dataflow Diagram (Technical)"):
                st.markdown("""
                ```mermaid
                flowchart LR
                    A[User Inputs] --> B[Validator]
                    B --> C[Tavily Search]
                    C --> D[Evidence Extractor]
                    D --> E[Price Parser]
                    E --> F[Verdict Engine]
                    F --> G[Report JSON/MD]
                ```
                """)
            
            # Optional: Run metadata
            with st.expander("📋 Run Metadata"):
                metadata = data.get("metadata", {})
                verdict = data.get("verdict", {})
                evidence_bundle = verdict.get("evidence_bundle", {})
                
                st.json({
                    "schema_version": metadata.get("schema_version", "unknown"),
                    "sources_retrieved": len(evidence_bundle.get("tavily_sources", [])),
                    "competitors_analyzed": len(evidence_bundle.get("competitor_pricing", [])),
                    "comparable_competitors": verdict.get("competitor_count", 0),
                })
        else:
            st.error("Report structure is invalid. Please check the file format.")
    else:
        st.error("Failed to load report. Please check the file.")
else:
    # Welcome screen with enhanced modern design
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 4rem 3rem; border-radius: 20px; color: white; margin: 2rem 0; 
                text-align: center; position: relative; overflow: hidden;
                box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);">
        <div style="position: relative; z-index: 2;">
            <div style="font-size: 4rem; margin-bottom: 1rem; animation: pulse 2s infinite;">👈</div>
            <h1 style="color: white; font-size: 3rem; margin-bottom: 1rem; font-weight: 800; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">Get Started</h1>
            <p style="font-size: 1.3rem; opacity: 0.95; font-weight: 300; letter-spacing: 0.5px;">Please load a report.json file using the sidebar</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="metric-card primary" style="height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 1rem;">📋</div>
            <h3 style="color: #1f2937; margin-bottom: 1.5rem; font-weight: 700; font-size: 1.3rem;">How to use:</h3>
            <ol style="color: #4b5563; line-height: 2.5; padding-left: 1.5rem; font-size: 1rem;">
                <li style="margin-bottom: 0.75rem;">Run PTM analysis to generate a <code style="background: #f0f4ff; padding: 0.2rem 0.5rem; border-radius: 4px; color: #667eea; font-weight: 600;">report.json</code> file</li>
                <li style="margin-bottom: 0.75rem;">Upload the file using the sidebar, or</li>
                <li>Place it in the <code style="background: #f0f4ff; padding: 0.2rem 0.5rem; border-radius: 4px; color: #667eea; font-weight: 600;">output/</code> directory and click "Load Default Report"</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card info" style="height: 100%;">
            <div style="font-size: 2rem; margin-bottom: 1rem;">✨</div>
            <h3 style="color: #1f2937; margin-bottom: 1.5rem; font-weight: 700; font-size: 1.3rem;">What you'll see:</h3>
            <ul style="color: #4b5563; line-height: 2.5; padding-left: 1.5rem; font-size: 1rem;">
                <li style="margin-bottom: 0.75rem;"><strong style="color: #1f2937;">Verdict Panel</strong>: Status and confidence of the pricing analysis</li>
                <li style="margin-bottom: 0.75rem;"><strong style="color: #1f2937;">Price Comparison Chart</strong>: Visual comparison of your product vs competitors</li>
                <li style="margin-bottom: 0.75rem;"><strong style="color: #1f2937;">Evidence Table</strong>: Detailed evidence with source URLs and verbatim quotes</li>
                <li style="margin-bottom: 0.75rem;"><strong style="color: #1f2937;">Gaps & Limitations</strong>: Data gaps that affect confidence</li>
                <li><strong style="color: #1f2937;">Citations</strong>: All sources used in the analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
