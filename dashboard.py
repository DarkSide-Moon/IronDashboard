# -*- coding: utf-8 -*-
import io
from datetime import datetime, timezone, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from config import EVENTS

GITHUB_CSV = "https://raw.githubusercontent.com/DarkSide-Moon/IronDashboard-data/main/polymarket_data"
CST = timezone(timedelta(hours=8))
CARD_HEIGHT = 420

COLORS = [
    "#2563EB", "#E11D48", "#059669", "#D97706", "#7C3AED",
    "#0891B2", "#EA580C", "#4F46E5", "#BE185D", "#0D9488",
    "#B45309", "#6D28D9", "#DC2626", "#0284C7", "#9333EA",
]

# ── 页面配置 ──────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="伊朗情报看板",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
        max-width: 1800px;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    header[data-testid="stHeader"] {
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
    }
    .stAppViewBlockContainer {
        padding-top: 1rem;
    }

    /* ─── 标题区 ─── */
    .header-area {
        padding-bottom: 0.8rem;
        border-bottom: 2px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    .header-zh {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: 0.02em;
    }
    .header-en {
        font-size: 0.78rem;
        color: #94A3B8;
        font-weight: 500;
        margin-top: 2px;
        letter-spacing: 0.01em;
    }

    /* ─── 卡片容器 ─── */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        background: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02) !important;
        transition: box-shadow 0.3s, border-color 0.3s;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04) !important;
    }

    /* ─── 刷新按钮 ─── */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 100%);
        border: 1.5px solid #BFDBFE;
        border-radius: 10px;
        color: #2563EB;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 8px 18px;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
        letter-spacing: 0.03em;
        box-shadow: 0 1px 3px rgba(37,99,235,0.08);
    }
    div[data-testid="stButton"] > button:hover {
        background: linear-gradient(135deg, #DBEAFE 0%, #EFF6FF 100%);
        border-color: #93C5FD;
        color: #1D4ED8;
        box-shadow: 0 4px 12px rgba(37,99,235,0.15);
        transform: translateY(-1px);
    }
    div[data-testid="stButton"] > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 3px rgba(37,99,235,0.08);
    }

    /* ─── 卡片内文字 ─── */
    .card-title {
        font-size: 0.88rem;
        font-weight: 700;
        color: #1E293B;
        line-height: 1.3;
    }
    .card-metric-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin: 2px 0 0 0;
    }
    .card-delta-row {
        display: flex;
        gap: 4px;
        margin: 4px 0 0 0;
        flex-wrap: wrap;
    }
    .card-val {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
    }
    .card-delta {
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        white-space: nowrap;
    }
    .card-delta.up {
        color: #DC2626;
        background: #FEF2F2;
    }
    .card-delta.down {
        color: #16A34A;
        background: #F0FDF4;
    }
    .card-delta.flat {
        color: #64748B;
        background: #F1F5F9;
    }
    .card-label {
        font-size: 0.68rem;
        color: #2563EB;
        font-weight: 600;
    }
    .card-label-inline {
        font-size: 0.72rem;
        color: #2563EB;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 180px;
    }
    .card-updated {
        font-size: 0.7rem;
        font-weight: 500;
        color: #94A3B8;
        margin-top: 4px;
    }

    /* ─── 变动榜 ─── */
    .movers-wrap {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 14px 18px 12px;
        margin-bottom: 1.2rem;
    }
    .movers-header {
        font-size: 0.82rem;
        font-weight: 700;
        color: #475569;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .movers-col-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #64748B;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
        padding-bottom: 4px;
        border-bottom: 1px solid #E2E8F0;
    }
    .mover-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 0;
        border-bottom: 1px solid #F1F5F9;
    }
    .mover-item:last-child { border-bottom: none; }
    .mover-rank {
        font-size: 0.65rem;
        font-weight: 700;
        color: #CBD5E1;
        width: 14px;
        flex-shrink: 0;
    }
    .mover-info { flex: 1; min-width: 0; }
    .mover-name {
        font-size: 0.82rem;
        font-weight: 600;
        color: #1E293B;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .mover-label {
        font-size: 0.74rem;
        color: #94A3B8;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .mover-delta {
        font-size: 0.8rem;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 4px;
        white-space: nowrap;
        flex-shrink: 0;
    }
    .mover-delta.up { color: #DC2626; background: #FEF2F2; }
    .mover-delta.down { color: #16A34A; background: #F0FDF4; }
    .mover-delta.flat { color: #64748B; background: #F1F5F9; }

    /* ─── 底部 ─── */
    .footer-line {
        text-align: center;
        padding: 10px 0 0;
        margin-top: 0.8rem;
        border-top: 1px solid #F1F5F9;
    }
    .footer-line span {
        font-size: 0.7rem;
        color: #94A3B8;
    }

    /* ─── 隐藏默认元素 ─── */
    #MainMenu {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ── 数据加载 ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=590)
def load_event_data(slug: str) -> pd.DataFrame:
    url = f"{GITHUB_CSV}/{slug}.csv"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return pd.read_csv(io.StringIO(resp.text), parse_dates=["datetime"])
    except Exception:
        return pd.DataFrame()

# ── 工具函数 ──────────────────────────────────────────────────────────────────

def calc_delta(df, col, minutes=60):
    if len(df) < 2:
        return 0.0
    now_val = df[col].iloc[-1]
    cutoff = df["datetime"].iloc[-1] - pd.Timedelta(minutes=minutes)
    older = df[df["datetime"] <= cutoff]
    old_val = older[col].iloc[-1] if not older.empty else df[col].iloc[0]
    return (now_val - old_val) * 100


def single_delta(val, tag):
    if abs(val) < 0.05:
        return f'<span class="card-delta flat">{tag} —</span>'
    if val > 0:
        return f'<span class="card-delta up">{tag} ▲+{val:.1f}%</span>'
    return f'<span class="card-delta down">{tag} ▼{val:.1f}%</span>'


def delta_html(df, col):
    d15 = calc_delta(df, col, minutes=15)
    d1h = calc_delta(df, col, minutes=60)
    d6h = calc_delta(df, col, minutes=360)
    d24h = calc_delta(df, col, minutes=1440)
    return f'{single_delta(d15, "15m")} {single_delta(d1h, "1h")} {single_delta(d6h, "6h")} {single_delta(d24h, "24h")}'


def data_freshness(df):
    last = df["datetime"].iloc[-1]
    return last.strftime("%m-%d %H:%M")


def get_top_movers(minutes, top_n=3):
    results = []
    for event in EVENTS:
        df = load_event_data(event["slug"])
        if df.empty:
            continue
        labels = event["labels"]
        value_cols = [c for c in df.columns if c != "datetime"]
        for col in value_cols:
            delta = calc_delta(df, col, minutes=minutes)
            results.append({
                "title": event["title"],
                "label": labels.get(col, col),
                "delta": delta,
            })
    results.sort(key=lambda x: abs(x["delta"]), reverse=True)
    return results[:top_n]


def mover_item_html(rank, item):
    d = item["delta"]
    if abs(d) < 0.05:
        badge = '<span class="mover-delta flat">—</span>'
    elif d > 0:
        badge = f'<span class="mover-delta up">▲+{d:.1f}%</span>'
    else:
        badge = f'<span class="mover-delta down">▼{d:.1f}%</span>'
    return f"""
    <div class="mover-item">
        <span class="mover-rank">{rank}</span>
        <div class="mover-info">
            <div class="mover-name">{item["title"]}</div>
            <div class="mover-label">{item["label"]}</div>
        </div>
        {badge}
    </div>"""

# ── 图表 ─────────────────────────────────────────────────────────────────────

def build_chart(df, selected_cols, labels, slug=""):
    fig = go.Figure()
    for i, col in enumerate(selected_cols):
        label = labels.get(col, col)
        fig.add_trace(go.Scatter(
            x=df["datetime"], y=df[col] * 100,
            name=label, mode="lines",
            line=dict(width=2.5, color=COLORS[i % len(COLORS)]),
            hovertemplate="%{y:.1f}%<extra>" + label + "</extra>",
        ))

    vals = df[selected_cols].dropna(how="all") * 100
    y_min = max(vals.min().min() - 5, 0)
    y_max = min(vals.max().max() + 5, 105)

    x_end = df["datetime"].iloc[-1]
    x_start = x_end - pd.Timedelta(days=3)

    fig.update_layout(
        height=270,
        margin=dict(l=0, r=0, t=26, b=0),
        yaxis=dict(
            range=[y_min, y_max], tickformat=".0f", ticksuffix="%",
            title=None, gridcolor="#E2E8F0", zeroline=False,
            tickfont=dict(size=11, color="#475569"),
            linecolor="#CBD5E1", linewidth=1,
        ),
        xaxis=dict(
            title=None, gridcolor="#EFF2F7",
            range=[x_start, x_end],
            rangeslider=dict(visible=True, thickness=0.05),
            tickfont=dict(size=11, color="#475569"),
            linecolor="#CBD5E1", linewidth=1,
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1E293B", bordercolor="#334155",
                        font=dict(size=12, color="#F1F5F9")),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    font=dict(size=11, color="#64748B"), bgcolor="rgba(0,0,0,0)"),
        uirevision=slug,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#64748B"),
    )
    return fig

# ── 头部 ─────────────────────────────────────────────────────────────────────

hdr_left, hdr_right = st.columns([0.9, 0.1])
with hdr_left:
    st.markdown("""
    <div class="header-area">
        <div class="header-zh">🛰️ 伊朗情报看板</div>
        <div class="header-en">Iran Intelligence Dashboard · Polymarket real-time probability tracking</div>
    </div>
    """, unsafe_allow_html=True)
with hdr_right:
    if st.button("刷新数据", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── 主渲染 ───────────────────────────────────────────────────────────────────

@st.fragment(run_every="10m")
def render() -> None:
    # ── 变动榜 ────────────────────────────────────────────────────────────────
    windows = [("15m", 15), ("1h", 60), ("6h", 360), ("24h", 1440)]
    window_labels = {"15m": "15 分钟", "1h": "1 小时", "6h": "6 小时", "24h": "24 小时"}
    movers_cols = st.columns(4, gap="medium")
    col_htmls = []
    for tag, mins in windows:
        top = get_top_movers(mins)
        items_html = "".join(mover_item_html(i + 1, item) for i, item in enumerate(top))
        col_htmls.append(f'<div class="movers-col-title">{window_labels[tag]} 变动最大</div>{items_html}')

    st.markdown(f"""
    <div class="movers-wrap">
        <div class="movers-header">概率变动榜 · Top 3</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
            {''.join(f'<div>{h}</div>' for h in col_htmls)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 事件卡片 ──────────────────────────────────────────────────────────────
    rows = [EVENTS[i:i + 3] for i in range(0, len(EVENTS), 3)]

    for row_events in rows:
        cols = st.columns(3, gap="medium")
        for col, event in zip(cols, row_events):
            with col:
                with st.container(border=True, height=CARD_HEIGHT):
                    df = load_event_data(event["slug"])
                    labels = event["labels"]

                    if df.empty:
                        st.markdown(f'<div class="card-title">{event["title"]}</div>',
                                    unsafe_allow_html=True)
                        st.warning("暂无数据", icon="⚠️")
                        continue

                    value_cols = [c for c in df.columns if c != "datetime"]
                    is_single = len(value_cols) == 1

                    if is_single:
                        selected = value_cols
                    else:
                        latest_val = df[value_cols].iloc[-1]
                        top_col = latest_val.idxmax()
                        save_key = f"pref_{event['slug']}"
                        if save_key not in st.session_state:
                            st.session_state[save_key] = [top_col]

                    selected = st.session_state.get(f"pref_{event['slug']}", value_cols[:1]) if not is_single else value_cols
                    disp_col = selected[0] if selected else value_cols[0]
                    disp_val = df[disp_col].iloc[-1] * 100
                    disp_label = labels.get(disp_col, disp_col)
                    delta_str = delta_html(df, disp_col)
                    freshness = data_freshness(df)

                    card_html = f"""
                        <div class="card-title">{event["title"]}</div>
                        <div class="card-metric-row">
                            <span class="card-val">{disp_val:.1f}%</span>
                            <span class="card-label-inline">{disp_label}</span>
                        </div>
                        <div class="card-delta-row">{delta_str}</div>
                        <div class="card-updated">最后更新 {freshness}</div>
                    """
                    if is_single:
                        st.markdown(card_html, unsafe_allow_html=True)
                    else:
                        tc, pc = st.columns([0.88, 0.12])
                        with tc:
                            st.markdown(card_html, unsafe_allow_html=True)
                        with pc:
                            with st.popover("⚙️", use_container_width=True):
                                st.caption("选择展示的结果：")
                                selected = st.multiselect(
                                    "选择展示的结果", options=value_cols,
                                    default=st.session_state[save_key],
                                    format_func=lambda x, lb=labels: lb.get(x, x),
                                    label_visibility="collapsed",
                                )
                                st.session_state[save_key] = selected if selected else st.session_state[save_key]

                    if not selected:
                        st.info("请至少选择一个选项")
                        continue

                    fig = build_chart(df, selected, labels, slug=event["slug"])
                    st.plotly_chart(fig, use_container_width=True)

    now_cst = datetime.now(CST)
    st.markdown(f"""
    <div class="footer-line">
        <span>上次更新：{now_cst.strftime('%Y-%m-%d %H:%M:%S')} 北京时间</span>
    </div>
    """, unsafe_allow_html=True)


render()
