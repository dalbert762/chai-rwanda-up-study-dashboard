"""
Shared visual theme for the Unserved Prescriptions Pilot dashboard.
Dark background, teal for data, coral for accents/negative states, bordered
KPI cards, small coral-dot section headers. Import from every page.
"""

import matplotlib.pyplot as plt
import streamlit as st

TEAL = "#30d5be"
TEAL_MID = "#5fe0c8"
TEAL_LIGHT = "#8fe8da"
TEAL_DARK = "#1f9c88"
TEAL_RAMP = [TEAL_DARK, "#249e8a", TEAL_MID, TEAL_LIGHT]  # dark -> light, sequential magnitude

CORAL = "#ef6461"
MUTED = "#9aa1a8"
TEXT = "#eef0f1"
GRID = "#2a2d31"
CARD_BG = "#15181b"
CARD_BORDER = "#262a2e"


def inject_css():
    st.markdown(
        f"""
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER} !important;
            border-radius: 10px;
        }}
        .section-head {{ display:flex; align-items:center; gap:8px; margin: 4px 0 12px; }}
        .section-head .dot {{ color: {CORAL}; font-size: 1rem; }}
        .section-head .label {{ font-weight: 700; font-size: 1.05rem; color: {TEXT}; }}
        .kpi-icon-label {{ color: {MUTED}; font-size: 0.85rem; margin-bottom: 4px; }}
        .kpi-value {{ color: {TEAL}; font-size: 2rem; font-weight: 700; line-height: 1.15;
                      font-variant-numeric: tabular-nums; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(label, icon=None):
    prefix = f"{icon} " if icon else ""
    st.markdown(
        f'<div class="section-head"><span class="dot">●</span>'
        f'<span class="label">{prefix}{label}</span></div>',
        unsafe_allow_html=True,
    )


def kpi_card(col, icon, label, value):
    with col.container(border=True):
        st.markdown(f'<div class="kpi-icon-label">{icon} {label}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-value">{value}</div>', unsafe_allow_html=True)


def dark_fig(figsize):
    """Axes styled for a transparent/dark card background."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_axisbelow(True)
    return fig, ax


def donut_chart(values, labels, colors, figsize=(4.2, 4.2)):
    """Two/three-slice donut with on-ring '<label>\\n<pct>%' text, matching the reference dashboard."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_alpha(0)
    total = sum(values)
    ring_labels = [f"{lbl}\n{v / total * 100:.1f}%" for lbl, v in zip(labels, values)]
    _, texts = ax.pie(
        values, colors=colors, startangle=90,
        wedgeprops=dict(width=0.42, edgecolor=CARD_BG, linewidth=2),
        labels=ring_labels, labeldistance=0.78,
    )
    for t in texts:
        t.set_color(TEXT)
        t.set_fontsize(10)
        t.set_fontweight("bold")
        t.set_ha("center")
    return fig
