from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(15, 23, 42, 0.4)",
    plot_bgcolor="rgba(15, 23, 42, 0.2)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=30, r=20, t=55, b=50),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.03,
        xanchor="right",
        x=1,
        font=dict(size=11, color="#cbd5e1")
    )
)

def filter_tickets_by_timeframe(tickets: List[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
    """Filters records based on 7 Days, 30 Days, 365 Days, or All Time."""
    if not tickets or timeframe == "All Time":
        return tickets

    days_map = {
        "Last 7 Days (Weekly)": 7,
        "Last 30 Days (Monthly)": 30,
        "Last 365 Days (Yearly)": 365
    }
    days = days_map.get(timeframe)
    if not days:
        return tickets

    cutoff = datetime.now() - timedelta(days=days)
    filtered = []

    for t in tickets:
        raw_date = t.get("created_at") or t.get("timestamp") or ""
        try:
            dt = pd.to_datetime(raw_date)
            if dt.tz_localize(None) >= cutoff:
                filtered.append(t)
        except Exception:
            filtered.append(t)

    return filtered


def create_timeline_trend_chart(tickets: List[Dict[str, Any]]):
    """
    Side-by-side grouped bar chart: Har unique date par Reported vs Resolved volume.
    """
    if not tickets:
        fig = go.Figure()
        fig.update_layout(title="No incident timeline data available", **DARK_LAYOUT)
        return fig

    df = pd.DataFrame(tickets)

    # 1. Clean Dates (Sirf YYYY-MM-DD grouping)
    df["created_date"] = pd.to_datetime(df["created_at"], errors="coerce").dt.strftime("%d %b %Y")
    reported_counts = df.groupby("created_date").size().reset_index(name="Reported")

    # 2. Resolved dates (sirf actual resolved)
    resolved_df = df[df["status"] == "RESOLVED"].copy()
    if not resolved_df.empty and "resolved_at" in resolved_df.columns:
        resolved_df["clean_res"] = resolved_df["resolved_at"].fillna(resolved_df["created_at"])
        resolved_df["res_date"] = pd.to_datetime(resolved_df["clean_res"], errors="coerce").dt.strftime("%d %b %Y")
        resolved_counts = resolved_df.groupby("res_date").size().reset_index(name="Resolved")
    else:
        resolved_counts = pd.DataFrame(columns=["res_date", "Resolved"])

    # 3. Outer merge taake date miss na ho
    timeline_df = pd.merge(
        reported_counts,
        resolved_counts,
        left_on="created_date",
        right_on="res_date",
        how="outer"
    ).fillna(0)

    timeline_df["date_label"] = timeline_df["created_date"].combine_first(timeline_df["res_date"])
    
    # Chronological sort
    timeline_df["sort_dt"] = pd.to_datetime(timeline_df["date_label"], format="%d %b %Y", errors="coerce")
    timeline_df = timeline_df.sort_values("sort_dt").drop(columns=["sort_dt"])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=timeline_df["date_label"],
        y=timeline_df["Reported"],
        name="Incoming Reports",
        marker_color="#38bdf8",
        marker_line=dict(width=0)
    ))

    fig.add_trace(go.Bar(
        x=timeline_df["date_label"],
        y=timeline_df["Resolved"],
        name="Resolved / Closed",
        marker_color="#10b981",
        marker_line=dict(width=0)
    ))

    fig.update_layout(
        barmode="group",
        bargap=0.3,
        bargroupgap=0.1,
        title=dict(
            text="<b>Daily Incident Comparison (Reported vs Resolved)</b>",
            font=dict(color="#f8fafc", size=14),
            x=0.01,
            y=0.96
        ),
        xaxis=dict(type="category", showgrid=False, title=dict(text="Date", font=dict(size=12))),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title=dict(text="Volume", font=dict(size=12))),
        **DARK_LAYOUT
    )
    return fig


def create_department_breakdown_chart(tickets: List[Dict[str, Any]]):
    """
    Departmental Workload & Backlog ka balanced stacked horizontal/vertical chart.
    """
    if not tickets:
        fig = go.Figure()
        fig.update_layout(title="No Active Tickets Reported", **DARK_LAYOUT)
        return fig

    # Standard short names for neat spacing
    dept_short_names = {
        "Bahawalpur Waste Management Company (BWMC)": "BWMC (Waste)",
        "Communication & Works (C&W) / MCB Roads": "C&W / MCB Roads",
        "MCB - Water & Sanitation Branch": "MCB (Water/Sanitation)"
    }

    # Pre-populate all departments so bars stretch across evenly
    all_depts = list(dept_short_names.values())
    raw_df = pd.DataFrame(tickets)
    raw_df["short_dept"] = raw_df["department"].map(lambda x: dept_short_names.get(x, x))

    grouped = raw_df.groupby(["short_dept", "status"]).size().unstack(fill_value=0).reindex(all_depts, fill_value=0).reset_index()

    if "PENDING" not in grouped.columns:
        grouped["PENDING"] = 0
    if "RESOLVED" not in grouped.columns:
        grouped["RESOLVED"] = 0

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=grouped["short_dept"],
        y=grouped["PENDING"],
        name="Action Pending",
        marker_color="#f59e0b",
        marker_line=dict(width=0)
    ))

    fig.add_trace(go.Bar(
        x=grouped["short_dept"],
        y=grouped["RESOLVED"],
        name="Resolved / Closed",
        marker_color="#10b981",
        marker_line=dict(width=0)
    ))

    fig.update_layout(
        barmode="stack",
        bargap=0.35,
        title=dict(
            text="<b>Departmental Workload & Backlog</b>",
            font=dict(color="#f8fafc", size=14),
            x=0.01,
            y=0.96
        ),
        xaxis=dict(
            showgrid=False,
            tickangle=0,
            tickfont=dict(size=11, color="#cbd5e1")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            title=dict(text="Total Work Orders", font=dict(size=12))
        ),
        **DARK_LAYOUT
    )
    return fig


def create_severity_pie_chart(tickets: List[Dict[str, Any]]):
    """
    Hazard severity distribution donut chart.
    """
    if not tickets:
        return go.Figure()

    df = pd.DataFrame(tickets)
    counts = df["severity"].value_counts().reset_index()
    counts.columns = ["severity", "count"]

    color_map = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MEDIUM": "#eab308",
        "LOW": "#3b82f6"
    }

    fig = go.Figure(data=[go.Pie(
        labels=counts["severity"],
        values=counts["count"],
        hole=0.6,
        marker=dict(colors=[color_map.get(s, "#64748b") for s in counts["severity"]]),
        textinfo="percent+label",
        hoverinfo="label+value+percent"
    )])

    fig.update_layout(
        title=dict(text="<b>Hazard Severity Distribution</b>", font=dict(color="#f8fafc", size=14), x=0.01, y=0.96),
        showlegend=False,
        **DARK_LAYOUT
    )
    return fig