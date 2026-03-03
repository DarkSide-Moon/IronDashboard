# -*- coding: utf-8 -*-
import io
from datetime import datetime, timezone, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from config import EVENTS

# GitHub 数据仓库（公开）
GITHUB_CSV = "https://raw.githubusercontent.com/DarkSide-Moon/IronDashboard-data/main/polymarket_data"

# ── 页面配置 ──────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Iran Intelligence Dashboard",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CARD_HEIGHT = 560

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── 数据加载 ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=590)
def load_event_data(slug: str) -> pd.DataFrame:
    """从 GitHub 数据仓库拉取 CSV，缓存 ~5 分钟。"""
    url = f"{GITHUB_CSV}/{slug}.csv"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return pd.read_csv(io.StringIO(resp.text), parse_dates=["datetime"])
    except Exception:
        return pd.DataFrame()

# ── 图表构建 ──────────────────────────────────────────────────────────────────

def build_chart(df: pd.DataFrame, selected_cols: list[str],
                labels: dict[str, str], slug: str = "") -> go.Figure:
    fig = go.Figure()
    for col in selected_cols:
        label = labels.get(col, col)
        fig.add_trace(go.Scatter(
            x=df["datetime"],
            y=df[col] * 100,
            name=label,
            mode="lines",
            line=dict(width=2.2),
            hovertemplate="%{y:.1f}%<extra>" + label + "</extra>",
        ))

    vals = df[selected_cols].dropna(how="all") * 100
    y_min = max(vals.min().min() - 5, 0)
    y_max = min(vals.max().max() + 5, 105)

    fig.update_layout(
        template="plotly_dark",
        height=460,
        margin=dict(l=0, r=0, t=40, b=0),
        yaxis=dict(
            range=[y_min, y_max],
            tickformat=".0f",
            ticksuffix="%",
            title=None,
            gridcolor="rgba(255,255,255,0.07)",
        ),
        xaxis=dict(
            title=None,
            gridcolor="rgba(255,255,255,0.04)",
            rangeslider=dict(visible=True, thickness=0.05),
        ),
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.0,
            xanchor="left",
            x=0,
            font=dict(size=12),
            bgcolor="rgba(0,0,0,0)",
        ),
        uirevision=slug,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig

# ── 主标题 ────────────────────────────────────────────────────────────────────

st.markdown("# 🛰️ Iran Intelligence Dashboard")
st.caption("基于 Polymarket 的伊朗相关事件概率追踪")
st.divider()

# ── 图表渲染（Fragment，5 分钟自动刷新） ─────────────────────────────────────

@st.fragment(run_every="10m")
def render_all_charts() -> None:
    rows = [EVENTS[i:i + 3] for i in range(0, len(EVENTS), 3)]

    for row_events in rows:
        grid_cols = st.columns(3, gap="medium")
        for grid_col, event in zip(grid_cols, row_events):
            with grid_col:
                with st.container(border=True, height=CARD_HEIGHT):
                    df = load_event_data(event["slug"])
                    labels = event["labels"]

                    if df.empty:
                        st.markdown(f"**{event['title']}**")
                        st.warning("暂无数据", icon="⚠️")
                        continue

                    value_cols = [c for c in df.columns if c != "datetime"]
                    is_single = len(value_cols) == 1

                    if is_single:
                        st.markdown(f"**{event['title']}**")
                        selected = value_cols
                    else:
                        latest_val = df[value_cols].iloc[-1]
                        top_col = latest_val.idxmax()

                        title_col, pop_col = st.columns([0.85, 0.15])
                        with title_col:
                            st.markdown(f"**{event['title']}**")
                        with pop_col:
                            with st.popover("⚙️ 筛选", use_container_width=True):
                                st.caption("选择要展示的结果线：")
                                selected = st.multiselect(
                                    "选择展示的结果",
                                    options=value_cols,
                                    default=[top_col],
                                    format_func=lambda x, lb=labels: lb.get(x, x),
                                    key=f"sel_{event['slug']}",
                                    label_visibility="collapsed",
                                )

                    if not selected:
                        st.info("请至少选择一个选项")
                        continue

                    fig = build_chart(df, selected, labels, slug=event["slug"])
                    st.plotly_chart(fig, use_container_width=True)

    now_cst = datetime.now(timezone(timedelta(hours=8)))
    st.caption(f"上次刷新：{now_cst.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")


render_all_charts()
