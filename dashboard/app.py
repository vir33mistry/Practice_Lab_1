"""
Robot Predictive Maintenance Dashboard (Neon-backed)

Reads:
- linear_regression.models
- linear_regression.events

Shows:
- 4 robot panels with live-updating plots (recent residuals & predicted failure window)
- latest predicted time-to-failure window (days)
- alert/error counts
- recent events table
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from streamlit_autorefresh import st_autorefresh


# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="Robot Predictive Maintenance Dashboard",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 Robot Predictive Maintenance Dashboard (Neon-backed)")
st.caption(
    "This dashboard reads models + events from Neon and visualizes predictive maintenance alerts. "
    "The live streaming notebook writes events; this dashboard renders them cleanly."
)

# ---------------------------
# Load .env and build engine
# ---------------------------
load_dotenv()


def make_engine():
    db_url = (
        f"postgresql+psycopg2://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}"
        f"@{os.getenv('PGHOST')}:{os.getenv('PGPORT', '5432')}/{os.getenv('PGDATABASE')}"
        f"?sslmode={os.getenv('PGSSLMODE', 'require')}"
    )
    return create_engine(db_url, pool_pre_ping=True)


engine = make_engine()

# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.header("Controls ⚙️")

refresh_seconds = st.sidebar.slider("Auto-refresh (seconds)", 2, 15, 5, 1)
minutes_back = st.sidebar.slider("Lookback window (minutes)", 5, 180, 60, 5)

max_events_table = st.sidebar.slider("Recent events table rows", 20, 300, 80, 20)

# auto-refresh tick
st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh")

robots = [1, 2, 3, 4]


# ---------------------------
# Helpers
# ---------------------------
@st.cache_data(ttl=10)
def load_models() -> pd.DataFrame:
    q = "SELECT * FROM linear_regression.models ORDER BY robot_id;"
    return pd.read_sql(q, engine)


@st.cache_data(ttl=10)
def load_events(minutes_back: int) -> pd.DataFrame:
    # Use UTC now
    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=int(minutes_back))

    q = text(
        """
SELECT robot_id, axis_num, event_type, ts, residual, predicted_ttf_days, created_at
FROM linear_regression.events
WHERE created_at >= :since
ORDER BY created_at ASC;
"""
    )
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params={"since": since})
    # Ensure ts is datetime
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df.dropna(subset=["ts"]).copy()


def kpi_block(label: str, value: str, hint: str = ""):
    st.markdown(f"**{label}**")
    st.markdown(f"<div style='font-size:30px; font-weight:700'>{value}</div>", unsafe_allow_html=True)
    if hint:
        st.caption(hint)


def make_robot_plot(ev_robot: pd.DataFrame, robot_id: int) -> go.Figure:
    """
    Plot residual time series with ALERT / ERROR markers.
    Also show predicted_ttf_days as a secondary trace (scaled to plot nicely).
    """
    fig = go.Figure()

    if ev_robot.empty:
        fig.update_layout(
            title=f"🤖 Robot {robot_id} — No events in window",
            template="plotly_white",
            height=380,
        )
        return fig

    # Base line: residual over time
    fig.add_trace(
        go.Scatter(
            x=ev_robot["ts"],
            y=ev_robot["residual"],
            mode="lines",
            name="Residual (positive)",
            line=dict(color="#2563eb", width=2),
        )
    )

    # ALERT markers
    alert = ev_robot[ev_robot["event_type"] == "ALERT"]
    if not alert.empty:
        fig.add_trace(
            go.Scatter(
                x=alert["ts"],
                y=alert["residual"],
                mode="markers",
                name="ALERT",
                marker=dict(color="#f59e0b", size=11, symbol="triangle-up"),
                hovertemplate="ALERT<br>%{x}<br>resid=%{y:.3f}<br>ttf_days=%{customdata:.2f}<extra></extra>",
                customdata=alert["predicted_ttf_days"].to_numpy(),
            )
        )

    # ERROR markers
    error = ev_robot[ev_robot["event_type"] == "ERROR"]
    if not error.empty:
        fig.add_trace(
            go.Scatter(
                x=error["ts"],
                y=error["residual"],
                mode="markers",
                name="ERROR",
                marker=dict(color="#dc2626", size=12, symbol="x"),
                hovertemplate="ERROR<br>%{x}<br>resid=%{y:.3f}<br>ttf_days=%{customdata:.2f}<extra></extra>",
                customdata=error["predicted_ttf_days"].to_numpy(),
            )
        )

    # Secondary “predicted days” line (scaled) – purely visual, keeps plot readable
    # We'll map predicted_ttf_days into residual-scale band so it's visible without dual axes.
    ttf = ev_robot["predicted_ttf_days"].astype(float).to_numpy()
    resid = ev_robot["residual"].astype(float).to_numpy()

    # scale ttf to residual chart range
    r_min, r_max = float(np.nanmin(resid)), float(np.nanmax(resid))
    if np.isfinite(r_min) and np.isfinite(r_max) and r_max > r_min:
        t_min, t_max = float(np.nanmin(ttf)), float(np.nanmax(ttf))
        if np.isfinite(t_min) and np.isfinite(t_max) and t_max > t_min:
            t_scaled = (ttf - t_min) / (t_max - t_min) * (r_max - r_min) + r_min
            fig.add_trace(
                go.Scatter(
                    x=ev_robot["ts"],
                    y=t_scaled,
                    mode="lines",
                    name="Predicted TTF (scaled)",
                    line=dict(color="#111827", width=2, dash="dot"),
                    hovertemplate="TTF(days)=%{customdata:.2f}<extra></extra>",
                    customdata=ttf,
                )
            )

    fig.update_layout(
        title=f"🤖 Robot {robot_id} — Residual Stream with Predictive Alerts",
        template="plotly_white",
        height=380,
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True, title="Residual (pos)")

    return fig


# ---------------------------
# Load data
# ---------------------------
try:
    models = load_models()
except Exception as e:
    st.error(f"Could not load models table. Error: {e}")
    st.stop()

if models.empty:
    st.warning("Models table is empty. Run Notebook 1 to populate linear_regression.models.")
    st.stop()

try:
    events = load_events(minutes_back)
except Exception as e:
    st.error(f"Could not load events table. Error: {e}")
    st.stop()

# ---------------------------
# Top-level KPI row
# ---------------------------
colA, colB, colC, colD = st.columns(4)

total_alerts = int((events["event_type"] == "ALERT").sum()) if not events.empty else 0
total_errors = int((events["event_type"] == "ERROR").sum()) if not events.empty else 0
latest_ts = events["ts"].max() if not events.empty else None

with colA:
    kpi_block("Lookback window", f"{minutes_back} min", "Filter used for events table + plots")

with colB:
    kpi_block("ALERT count", str(total_alerts), "Within the lookback window")

with colC:
    kpi_block("ERROR count", str(total_errors), "Within the lookback window")

with colD:
    kpi_block("Latest event time", str(latest_ts) if latest_ts is not None else "—", "UTC time")


st.divider()

# ---------------------------
# Robot panels
# ---------------------------
for rid in robots:
    st.subheader(f"Robot {rid} panel 🤖")

    left, right = st.columns([1, 2], vertical_alignment="top")

    ev_r = events[(events["robot_id"] == rid) & (events["axis_num"] == rid)].copy()

    # KPIs per robot
    with left:
        if ev_r.empty:
            st.info("No events for this robot in the lookback window.")
        else:
            # Latest predicted TTF from latest event
            latest = ev_r.sort_values("ts").iloc[-1]
            latest_ttf = float(latest["predicted_ttf_days"])
            latest_type = str(latest["event_type"])
            latest_resid = float(latest["residual"])

            # Counts
            a_ct = int((ev_r["event_type"] == "ALERT").sum())
            e_ct = int((ev_r["event_type"] == "ERROR").sum())

            st.markdown("### Live status")
            st.metric("Latest predicted failure window (days)", f"{latest_ttf:.2f}")
            st.metric("Latest event type", latest_type)
            st.metric("Latest residual (pos)", f"{latest_resid:.3f}")

            st.markdown("### Counts (window)")
            st.metric("ALERTs", a_ct)
            st.metric("ERRORs", e_ct)

            # Minimal, executive-style message
            if latest_type == "ERROR":
                st.error(f"🚨 ERROR: failure likely soon (~{latest_ttf:.1f} days). Prioritize inspection.")
            elif latest_type == "ALERT":
                st.warning(f"⚠️ ALERT: elevated risk (~{latest_ttf:.1f} days). Plan preventive maintenance.")
            else:
                st.success("✅ Stable in the current window.")

    # Plot per robot
    with right:
        fig = make_robot_plot(ev_r, rid)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

# ---------------------------
# Recent Events Table
# ---------------------------
st.subheader("Recent events (Neon) 📜")

if events.empty:
    st.info("No events in this window. Run Notebook 2 to generate events and insert them into Neon.")
else:
    ev_view = events.sort_values("ts", ascending=False).head(int(max_events_table)).copy()
    ev_view["ts"] = ev_view["ts"].dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    st.dataframe(ev_view, use_container_width=True, hide_index=True)

st.caption("Tip: If you want fewer alerts/errors, raise residual_alert/residual_error quantiles in Notebook 1 and increase cooldown in Notebook 2.")
