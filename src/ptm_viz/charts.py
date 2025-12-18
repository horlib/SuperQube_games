# -*- coding: utf-8 -*-
"""Chart generation functions for PTM visualizations."""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_price_comparison_chart(
    comparison_df: pd.DataFrame,
    product_name: str = "Your Product",
) -> go.Figure:
    """Create horizontal bar chart comparing product price vs competitors.
    
    Args:
        comparison_df: DataFrame with columns: Competitor, Price (USD/month), Is Product
        product_name: Name of the product being analyzed
        
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
    
    # Add competitor bars
    if not competitor_rows.empty:
        fig.add_trace(
            go.Bar(
                y=competitor_rows["Competitor"],
                x=competitor_rows["Price (USD/month)"],
                orientation="h",
                name="Competitors",
                marker=dict(color="#636EFA"),
                text=[f"${x:.2f}" for x in competitor_rows["Price (USD/month)"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Price: $%{x:.2f}/month<extra></extra>",
            )
        )
    
    # Add product bar (highlighted)
    if not product_row.empty:
        fig.add_trace(
            go.Bar(
                y=product_row["Competitor"],
                x=product_row["Price (USD/month)"],
                orientation="h",
                name=product_name,
                marker=dict(color="#EF553B", line=dict(color="black", width=2)),
                text=[f"${x:.2f}" for x in product_row["Price (USD/month)"]],
                textposition="outside",
                hovertemplate=f"<b>{product_name}</b><br>Price: $%{{x:.2f}}/month<extra></extra>",
            )
        )
    
    fig.update_layout(
        title="Price Comparison: Your Product vs Competitors",
        xaxis_title="Price (USD/month)",
        yaxis_title="",
        height=max(400, len(comparison_df) * 50),
        showlegend=True,
        hovermode="closest",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=False),
    )
    
    return fig
