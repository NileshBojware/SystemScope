"""
SystemScope - Interactive Charts Module
Generates responsive, polished Plotly charts for CPU, RAM, and Disk telemetry.
Supports both modern Dark and crisp Light themes with threshold markers,
bounded history visualization, and empty state handling.
"""

from typing import List, Optional, Dict, Any
import plotly.graph_objects as go
from modules.system_monitor import format_bytes


def get_layout_defaults(theme: str = "dark") -> Dict[str, Any]:
    """Returns Plotly layout tokens aligned with the active UI theme."""
    if theme == "light":
        return dict(
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f8fafc",
            font=dict(family="Inter, -apple-system, sans-serif", color="#0f172a", size=12),
            margin=dict(l=45, r=30, t=45, b=45),
            hovermode="x unified",
        )
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.75)",   # Slate-900 transparent
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        font=dict(family="Inter, -apple-system, sans-serif", color="#f8fafc", size=12),
        margin=dict(l=45, r=30, t=45, b=45),
        hovermode="x unified",
    )


def create_empty_chart(
    title: str,
    message: str = "Awaiting performance data...",
    theme: str = "dark",
) -> go.Figure:
    """Renders a friendly placeholder chart when insufficient data points exist."""
    fig = go.Figure()
    title_color = "#0f172a" if theme == "light" else "#f8fafc"
    msg_color = "#334155" if theme == "light" else "#94a3b8"

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=title_color, weight="bold")),
        **get_layout_defaults(theme),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        annotations=[
            dict(
                text=message,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color=msg_color, weight="bold"),
            )
        ],
    )
    return fig


def create_metric_history_chart(
    timestamps: List[str],
    values: List[float],
    title: str,
    metric_name: str,
    line_color: Optional[str] = None,
    fill_color: Optional[str] = None,
    threshold: Optional[float] = None,
    y_max: float = 100.0,
    theme: str = "dark",
) -> go.Figure:
    """
    Renders an interactive time-series line chart with bounded history.
    Displays threshold indicator line, dynamic themes, and hover telemetry.
    """
    if not timestamps or not values:
        return create_empty_chart(title, "Gathering real-time telemetry readings...", theme=theme)

    is_light = (theme == "light")

    # High-contrast defaults tuned per theme
    if line_color is None:
        line_color = "#0284c7" if is_light else "#38bdf8"
    if fill_color is None:
        fill_color = "rgba(2, 132, 199, 0.16)" if is_light else "rgba(56, 189, 248, 0.18)"

    title_color = "#0f172a" if is_light else "#f8fafc"
    axis_title_color = "#0f172a" if is_light else "#f1f5f9"
    tick_color = "#1e293b" if is_light else "#cbd5e1"
    grid_color = "rgba(148, 163, 184, 0.35)" if is_light else "rgba(148, 163, 184, 0.18)"
    thresh_color = "#b91c1c" if is_light else "#f87171"

    fig = go.Figure()

    # Main metric trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=values,
            mode="lines+markers",
            name=metric_name,
            line=dict(color=line_color, width=2.5, shape="spline", smoothing=0.7),
            marker=dict(size=5, color=line_color),
            fill="tozeroy",
            fillcolor=fill_color,
            hovertemplate=f"<b>{metric_name}</b>: %{{y:.1f}}%<br>Time: %{{x}}<extra></extra>",
        )
    )

    # Threshold horizontal line if specified
    if threshold is not None and 0 <= threshold <= 100:
        fig.add_hline(
            y=threshold,
            line_dash="dot",
            line_color=thresh_color,
            line_width=2.0,
            annotation_text=f"Threshold ({threshold:.0f}%)",
            annotation_position="top right",
            annotation_font=dict(color=thresh_color, size=11, weight="bold"),
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=title_color, weight="bold")),
        **get_layout_defaults(theme),
        xaxis=dict(
            title=dict(text="Time (HH:MM:SS)", font=dict(size=12, color=axis_title_color, weight="bold")),
            showgrid=True,
            gridcolor=grid_color,
            tickangle=-20,
            tickfont=dict(color=tick_color, size=11),
        ),
        yaxis=dict(
            title=dict(text="Utilization (%)", font=dict(size=12, color=axis_title_color, weight="bold")),
            range=[0, max(y_max, 100.0)],
            showgrid=True,
            gridcolor=grid_color,
            ticksuffix="%",
            tickfont=dict(color=tick_color, size=11),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=title_color, size=11, weight="bold"),
        ),
    )
    return fig


def create_storage_donut_chart(
    used_bytes: int,
    free_bytes: int,
    mountpoint: str,
    used_percent: float,
    threshold: Optional[float] = None,
    theme: str = "dark",
) -> go.Figure:
    """
    Renders an interactive donut chart illustrating disk space usage.
    """
    if used_bytes == 0 and free_bytes == 0:
        return create_empty_chart(f"Disk Allocation — {mountpoint}", "Storage data not accessible.", theme=theme)

    is_light = (theme == "light")
    used_fmt = format_bytes(used_bytes)
    free_fmt = format_bytes(free_bytes)
    total_fmt = format_bytes(used_bytes + free_bytes)

    # Dynamic color based on threshold
    is_alert = threshold is not None and used_percent >= threshold
    if is_alert:
        used_color = "#dc2626" if is_light else "#ef4444"
    else:
        used_color = "#2563eb" if is_light else "#6366f1"

    free_color = "#cbd5e1" if is_light else "#1e293b"
    ring_outline = "#ffffff" if is_light else "#0f172a"
    title_color = "#0f172a" if is_light else "#f8fafc"
    center_text_color = "#0f172a" if is_light else "#f8fafc"
    sub_used_color = "#1e293b" if is_light else "#cbd5e1"
    legend_color = "#0f172a" if is_light else "#f8fafc"
    slice_text_color = "#0f172a" if is_light else "#f8fafc"

    labels = ["Used Space", "Free Space"]
    values = [used_bytes, free_bytes]
    colors = [used_color, free_color]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.68,
                marker=dict(colors=colors, line=dict(color=ring_outline, width=2)),
                textinfo="label+percent",
                textposition="outside",
                insidetextfont=dict(color=slice_text_color, size=12),
                outsidetextfont=dict(color=slice_text_color, size=12, weight="bold"),
                hoverinfo="label+text",
                hovertext=[
                    f"Used: {used_fmt} ({used_percent:.1f}%)",
                    f"Free: {free_fmt} ({100.0 - used_percent:.1f}%)",
                ],
            )
        ]
    )

    # Center label showing usage
    fig.add_annotation(
        text=f"<b>{used_percent:.1f}%</b><br><span style='font-size:12px;color:{sub_used_color};font-weight:700;'>USED</span>",
        x=0.5,
        y=0.5,
        font=dict(size=22, color=center_text_color),
        showarrow=False,
    )

    fig.update_layout(
        title=dict(
            text=f"Storage Breakdown: {mountpoint} (Total {total_fmt})",
            font=dict(size=14, color=title_color, weight="bold"),
        ),
        **get_layout_defaults(theme),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(color=legend_color, size=12, weight="bold"),
        ),
    )
    return fig


def create_cpu_per_core_chart(
    per_cpu_percent: List[float],
    threshold: Optional[float] = None,
    theme: str = "dark",
) -> go.Figure:
    """
    Renders an interactive horizontal or vertical bar chart of individual core utilization.
    """
    if not per_cpu_percent:
        return create_empty_chart("Per-Core CPU Distribution", "No logical core metrics reported.", theme=theme)

    is_light = (theme == "light")
    title_color = "#0f172a" if is_light else "#f8fafc"
    axis_title_color = "#0f172a" if is_light else "#f1f5f9"
    tick_color = "#1e293b" if is_light else "#cbd5e1"
    grid_color = "rgba(100, 116, 139, 0.25)" if is_light else "rgba(148, 163, 184, 0.15)"
    thresh_color = "#b91c1c" if is_light else "#f87171"

    cores = [f"Core {i+1}" for i in range(len(per_cpu_percent))]
    colors = []
    for val in per_cpu_percent:
        if threshold is not None and val >= threshold:
            colors.append("#dc2626" if is_light else "#ef4444")  # red
        elif val >= 70:
            colors.append("#d97706" if is_light else "#f59e0b")  # amber
        else:
            colors.append("#0284c7" if is_light else "#06b6d4")  # cyan/blue

    bar_outline = "rgba(0,0,0,0.12)" if is_light else "rgba(255,255,255,0.1)"

    fig = go.Figure(
        data=[
            go.Bar(
                x=cores,
                y=per_cpu_percent,
                marker=dict(color=colors, line=dict(color=bar_outline, width=1)),
                hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra></extra>",
            )
        ]
    )

    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dot",
            line_color=thresh_color,
            line_width=1.8,
            annotation_text=f"Limit ({threshold:.0f}%)",
            annotation_position="top right",
            annotation_font=dict(color=thresh_color, size=11, weight="bold"),
        )

    fig.update_layout(
        title=dict(text="Logical Core Utilization Breakdown", font=dict(size=14, color=title_color, weight="bold")),
        **get_layout_defaults(theme),
        xaxis=dict(
            title=dict(text="CPU Core", font=dict(size=12, color=axis_title_color, weight="bold")),
            showgrid=False,
            tickfont=dict(color=tick_color, size=11),
        ),
        yaxis=dict(
            title=dict(text="Load (%)", font=dict(size=12, color=axis_title_color, weight="bold")),
            range=[0, 100],
            showgrid=True,
            gridcolor=grid_color,
            ticksuffix="%",
            tickfont=dict(color=tick_color, size=11),
        ),
    )
    return fig
