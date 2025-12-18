# -*- coding: utf-8 -*-
"""Chart generation functions for PTM visualizations."""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_price_comparison_chart(
    comparison_df: pd.DataFrame,
    product_name: str = "Your Product",
    competitor_details: dict[str, dict[str, Any]] | None = None,
) -> go.Figure:
    """Create horizontal bar chart comparing product price vs competitors.
    
    Args:
        comparison_df: DataFrame with columns: Competitor, Price (USD/month), Is Product
        product_name: Name of the product being analyzed
        competitor_details: Optional dict mapping competitor names to details (for hover)
        
    Returns:
        Plotly figure
    """
    if comparison_df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No comparable competitor prices available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        return fig
    
    # Separate product and competitors
    product_row = comparison_df[comparison_df["Is Product"] == True]
    competitor_rows = comparison_df[comparison_df["Is Product"] == False]
    
    fig = go.Figure()
    
    # Calculate statistics for reference lines
    competitor_prices = competitor_rows["Price (USD/month)"] if not competitor_rows.empty else []
    mean_price = competitor_prices.mean() if len(competitor_prices) > 0 else None
    median_price = competitor_prices.median() if len(competitor_prices) > 0 else None
    
    # Add competitor bars with gradient colors
    if not competitor_rows.empty:
        hover_texts = []
        # Create gradient colors based on price position
        max_price = competitor_prices.max()
        min_price = competitor_prices.min()
        price_range = max_price - min_price if max_price != min_price else 1
        
        colors = []
        for _, row in competitor_rows.iterrows():
            comp_name = row["Competitor"]
            price = row["Price (USD/month)"]
            
            # Create gradient from blue to purple based on price position
            normalized_pos = (price - min_price) / price_range
            # Interpolate between #636EFA (blue) and #8B5CF6 (purple)
            r1, g1, b1 = 99, 110, 250  # #636EFA
            r2, g2, b2 = 139, 92, 246  # #8B5CF6
            r = int(r1 + (r2 - r1) * normalized_pos)
            g = int(g1 + (g2 - g1) * normalized_pos)
            b = int(b1 + (b2 - b1) * normalized_pos)
            colors.append(f"rgb({r}, {g}, {b})")
            
            if competitor_details and comp_name in competitor_details:
                details = competitor_details[comp_name]
                price_evidence = details.get("price_evidence", "N/A")
                hover_text = f"<b>{comp_name}</b><br>Price: <b>${price:.2f}/month</b><br><br>Evidence: {price_evidence[:150]}..."
            else:
                hover_text = f"<b>{comp_name}</b><br>Price: <b>${price:.2f}/month</b>"
            hover_texts.append(hover_text)
        
        fig.add_trace(
            go.Bar(
                y=competitor_rows["Competitor"],
                x=competitor_rows["Price (USD/month)"],
                orientation="h",
                name="Competitors",
                marker=dict(
                    color=colors,
                    line=dict(color="rgba(255,255,255,0.8)", width=1),
                    opacity=0.9,
                ),
                text=[f"${x:.2f}" for x in competitor_rows["Price (USD/month)"]],
                textposition="outside",
                textfont=dict(size=12, color="#1f2937"),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover_texts,
            )
        )
    
    # Add product bar (highlighted with glow effect)
    if not product_row.empty:
        product_price = product_row["Price (USD/month)"].iloc[0]
        fig.add_trace(
            go.Bar(
                y=product_row["Competitor"],
                x=product_row["Price (USD/month)"],
                orientation="h",
                name=product_name,
                marker=dict(
                    color="#EF4444",
                    line=dict(color="#DC2626", width=3),
                    opacity=0.95,
                ),
                text=[f"${x:.2f} ⭐" for x in product_row["Price (USD/month)"]],
                textposition="outside",
                textfont=dict(size=13, color="#DC2626", family="Arial Black"),
                hovertemplate=f"<b>{product_name}</b><br>Price: <b>${product_price:.2f}/month</b><br><br>Your Product<extra></extra>",
            )
        )
    
    # Add reference lines for mean and median
    shapes = []
    annotations = []
    
    if mean_price is not None:
        shapes.append(
            dict(
                type="line",
                x0=mean_price,
                x1=mean_price,
                y0=-0.5,
                y1=len(comparison_df) - 0.5,
                line=dict(color="#10B981", width=2, dash="dash"),
            )
        )
        annotations.append(
            dict(
                x=mean_price,
                y=len(comparison_df) - 0.3,
                text=f"Mean: ${mean_price:.2f}",
                showarrow=False,
                xref="x",
                yref="y",
                bgcolor="rgba(16, 185, 129, 0.1)",
                bordercolor="#10B981",
                borderwidth=1,
                font=dict(size=10, color="#059669"),
            )
        )
    
    if median_price is not None and abs(median_price - mean_price) > 0.01:
        shapes.append(
            dict(
                type="line",
                x0=median_price,
                x1=median_price,
                y0=-0.5,
                y1=len(comparison_df) - 0.5,
                line=dict(color="#3B82F6", width=2, dash="dot"),
            )
        )
        annotations.append(
            dict(
                x=median_price,
                y=len(comparison_df) - 0.5,
                text=f"Median: ${median_price:.2f}",
                showarrow=False,
                xref="x",
                yref="y",
                bgcolor="rgba(59, 130, 246, 0.1)",
                bordercolor="#3B82F6",
                borderwidth=1,
                font=dict(size=10, color="#2563EB"),
            )
        )
    
    fig.update_layout(
        title=dict(
            text="<b>📊 Price Comparison: Your Product vs Competitors</b>",
            font=dict(size=22, color="#1f2937", family="Arial"),
            x=0.5,
            xanchor="center",
            pad=dict(b=20),
        ),
        xaxis_title=dict(
            text="<b>Price (USD/month)</b>", 
            font=dict(size=13, color="#6b7280", family="Arial")
        ),
        yaxis_title="",
        height=max(450, len(comparison_df) * 55),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, family="Arial"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
        hovermode="closest",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(102, 126, 234, 0.1)",
            gridwidth=1,
            zeroline=False,
            tickfont=dict(size=11, color="#6b7280"),
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(size=12, color="#1f2937", family="Arial"),
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        shapes=shapes,
        annotations=annotations,
        margin=dict(l=15, r=15, t=80, b=50),
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#667eea",
            borderwidth=2,
            font_size=12,
            font_family="Arial",
        ),
    )
    
    return fig
