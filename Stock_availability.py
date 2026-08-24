"""
Streamlit dashboard for Pilot_stcok availability.xlsx
(Unserved Prescriptions - Medicine Stock Assessment pilot)

Run with:
    streamlit run Stock_availability.py

Then open the local URL it prints (default http://localhost:8501).
"""

import pandas as pd
import streamlit as st

from theme import (CORAL, MUTED, TEAL, TEXT, dark_fig, donut_chart, inject_css,
                    kpi_card, section_header)

FILE = "Pilot_stcok availability.xlsx"

# The workbook's facility-identity sheet (Province/District/Sector/Facility name) was
# present earlier in this pilot's KoboToolbox live-sync but has since dropped out of the
# export (only 'medicine_group' remains). This mapping is carried over from that earlier
# read - reconfirm it if the sheet reappears or more visits are added.
KNOWN_FACILITIES = {
    845991489: "Kicukiro CS",
    846277248: "Masaka CS",
}

STATUS_COLOR = {
    "Stock out": "#e2585a",
    "Understock": "#ef9b62",
    "Plan stock": TEAL,
    "Overstock": "#e8c15a",
}
STATUS_ORDER = ["Stock out", "Understock", "Plan stock", "Overstock"]

st.set_page_config(page_title="Stock availability — Unserved Prescriptions Pilot", layout="wide")
inject_css()


@st.cache_data
def load_data():
    xls = pd.ExcelFile(FILE)
    med = pd.read_excel(xls, "medicine_group")

    if len(xls.sheet_names) > 1:
        facility = pd.read_excel(xls, xls.sheet_names[0])
        fac_cols = ["_index", "Province", "District", "Sector", "Facility (search & select)"]
        facility_small = facility[fac_cols].rename(columns={"Facility (search & select)": "Facility"})
        df = med.merge(facility_small, left_on="_parent_index", right_on="_index", how="left")
        sheet_note = None
    else:
        df = med.copy()
        df["Facility"] = df["_submission__id"].map(KNOWN_FACILITIES).fillna(
            "Visit " + df["_parent_index"].astype(str))
        sheet_note = (
            "The workbook's facility-identity sheet was missing at last read (only "
            "'medicine_group' remained) — facility names shown are carried over from an "
            "earlier read of this live-synced file."
        )

    empty_cols = df.columns[df.isna().all()]
    df = df.drop(columns=empty_cols)
    return df, list(empty_cols), sheet_note


df_all, empty_cols, sheet_note = load_data()
all_facilities = sorted(df_all["Facility"].unique())
all_classes = [c for c in STATUS_ORDER if c in df_all["stock_classification"].unique()]

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.title("Stock availability")
st.caption("Medicine stock assessment · Kicukiro District, Kigali City")
if sheet_note:
    st.info(sheet_note, icon="ℹ️")

# ---------------------------------------------------------------
# Filters
# ---------------------------------------------------------------
section_header("Filters", icon="🔍")
f1, f2, f3, f4, f5 = st.columns(5)
with f1:
    facility_choice = st.selectbox("Facility (HC)", ["All"] + all_facilities)
with f2:
    class_choice = st.selectbox("Stock classification", ["All"] + all_classes)

df = df_all if facility_choice == "All" else df_all[df_all["Facility"] == facility_choice]
if class_choice != "All":
    df = df[df["stock_classification"] == class_choice]

st.write("")

# ---------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------
n_fac = df["_parent_index"].nunique()
n_lines = len(df)
avail_yes = int((df["Available on visit day?"] == "Yes").sum())
avail_no = int((df["Available on visit day?"] == "No").sum())
avail_pct = (avail_yes / n_lines * 100) if n_lines else 0
stockout_n = int((df["stock_classification"] == "Stock out").sum())
loss_total = df["financial_loss"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
kpi_card(k1, "🏥", "Facilities in view", n_fac)
kpi_card(k2, "💊", "Medicine lines", n_lines)
kpi_card(k3, "✅", "Available on visit day", f"{avail_pct:.1f}%")
kpi_card(k4, "⚠️", "Stock-out lines", f"{stockout_n} / {n_lines}")
kpi_card(k5, "💰", "Est. financial loss", f"{loss_total:,.0f} RWF")

st.write("")

# ---------------------------------------------------------------
# Stock position
# ---------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    section_header("Availability on visit day")
    if n_lines:
        fig = donut_chart([avail_yes, avail_no], ["Yes", "No"], [TEAL, CORAL])
        st.pyplot(fig, width="stretch")
    else:
        st.caption("No lines match the current filters.")

with c2:
    section_header("Stock classification")
    stock_counts = df["stock_classification"].value_counts().reindex(STATUS_ORDER).dropna()
    if len(stock_counts):
        total = stock_counts.sum()
        fig, ax = dark_fig((5.2, 3.2))
        ax.barh(stock_counts.index, stock_counts.values,
                color=[STATUS_COLOR[s] for s in stock_counts.index])
        for i, v in enumerate(stock_counts.values):
            ax.text(v + total * 0.02, i, f"{int(v)} ({v / total * 100:.1f}%)",
                    va="center", fontsize=9.5, color=TEXT)
        ax.set_xlabel("Medicine lines")
        ax.invert_yaxis()
        ax.set_xlim(0, total * 1.32)
        st.pyplot(fig, width="stretch")
    else:
        st.caption("No lines match the current filters.")

st.caption("Classification is measured against each facility's understock (<1 month) / "
           "overstock (>2 months) thresholds over a 90-day window.")

na_class = df["stock_classification"].isna().sum()
if na_class:
    st.caption(
        f"⚠️ {na_class} line(s) excluded from classification: average monthly consumption "
        "recorded as 0 despite stock on hand (likely a data-entry gap, not zero demand)."
    )

section_header("Classification × facility")
ct1 = pd.crosstab(df["stock_classification"], df["Facility"], margins=True, margins_name="Total")
st.dataframe(ct1.reindex([c for c in STATUS_ORDER + ["Total"] if c in ct1.index]), width="stretch")

st.divider()

# ---------------------------------------------------------------
# Financial exposure
# ---------------------------------------------------------------
section_header("Loss by medicine")
top_loss = df[["Medicine", "Facility", "financial_loss", "total_stockout_days"]].dropna(subset=["financial_loss"])
top_loss = top_loss[top_loss["financial_loss"] > 0].sort_values("financial_loss", ascending=False)

if top_loss.empty:
    st.caption("No costed financial loss in this view.")
else:
    total_loss = top_loss["financial_loss"].sum()
    fig, ax = dark_fig((8, max(2, 0.55 * len(top_loss))))
    labels = [f"{m}  ({f})" for m, f in zip(top_loss["Medicine"], top_loss["Facility"])]
    ax.barh(labels, top_loss["financial_loss"], color=TEAL)
    for i, v in enumerate(top_loss["financial_loss"]):
        ax.text(v + total_loss * 0.015, i, f"{v:,.0f} RWF ({v / total_loss * 100:.1f}%)",
                va="center", fontsize=9.5, color=TEXT)
    ax.set_xlabel("Estimated loss (RWF)")
    ax.invert_yaxis()
    ax.set_xlim(0, total_loss * 1.4)
    st.pyplot(fig, width="stretch")
    st.caption(
        "Lines with a stock-out but zero computed loss (missing RSSB prescriptions/year or "
        "unit-tariff data) are excluded from this chart — that means 'not costed,' not 'no impact.'"
    )

st.divider()

# ---------------------------------------------------------------
# Stock-outs in detail
# ---------------------------------------------------------------
stockouts = df[df["stock_classification"] == "Stock out"]
c1, c2 = st.columns(2)
with c1:
    section_header("Recurrence by medicine")
    if stockouts.empty:
        st.caption("No stock-outs in this view.")
    else:
        recurrence = pd.crosstab(stockouts["Medicine"], stockouts["Facility"])
        st.dataframe(recurrence, width="stretch")

with c2:
    section_header("Upstream availability at stock-out")
    if stockouts.empty:
        st.caption("No stock-outs in this view.")
    else:
        detail_cols = ["Medicine", "Facility", "Available at RMS Central?", "Available at RMS Regional?",
                        "distribution_nationwide"]
        st.dataframe(stockouts[detail_cols].rename(columns={"distribution_nationwide": "Reason recorded"}),
                     width="stretch", hide_index=True)

st.divider()

# ---------------------------------------------------------------
# Requisition & fulfilment
# ---------------------------------------------------------------
section_header("Requested / delivered vs. average monthly consumption")
st.caption("100% = exactly one month's typical use. Values above 100% mean the facility "
           "requested/received more than one month's worth.")
fulfil = df.dropna(subset=["fulfilment_pct"])
if fulfil.empty:
    st.caption("No in-stock fulfilment data in this view.")
else:
    agg = fulfil.groupby("Facility")[["fulfilment_pct", "request_vs_amc_pct", "delivery_vs_amc_pct"]].mean().round(1)

    fig, ax = dark_fig((7.5, 0.9 * len(agg) + 1))
    y = range(len(agg))
    ax.barh([i + 0.18 for i in y], agg["request_vs_amc_pct"], height=0.32, label="Requested vs AMC", color=TEAL)
    ax.barh([i - 0.18 for i in y], agg["delivery_vs_amc_pct"], height=0.32, label="Delivered vs AMC", color="#e0a94c")
    ax.axvline(100, color=MUTED, linestyle="--", linewidth=1)
    ax.text(100, len(agg) - 0.3, "100%", color=MUTED, fontsize=9, ha="center")
    ax.set_yticks(list(y))
    ax.set_yticklabels(agg.index, color=TEXT)
    ax.set_xlabel("% of average monthly consumption")
    legend = ax.legend(loc="lower right", frameon=False, fontsize=9)
    for text in legend.get_texts():
        text.set_color(TEXT)
    st.pyplot(fig, width="stretch")

    section_header("Requisition fulfilment")
    m1, m2 = st.columns(2)
    for col, (fac, row) in zip([m1, m2], agg.iterrows()):
        with col:
            st.markdown(f"**{fac}**")
            st.progress(min(int(row['fulfilment_pct']), 100), text=f"{row['fulfilment_pct']:.1f}%")

st.divider()
with st.expander(f"Data notes ({len(empty_cols)} columns excluded, sample size, source)"):
    st.markdown(
        f"- **Sample size:** {len(all_facilities)} facilit{'y' if len(all_facilities) == 1 else 'ies'} "
        "— read every share/ranking here as pilot-scale, illustrative signal, not a powered estimate.\n"
        f"- **{len(empty_cols)} columns were entirely blank** in this pilot and excluded: "
        "skip-logic branches not yet triggered with only 2 submissions "
        "(facility_weakness, rms_weakness, fulfilment_status, monthly stock-out flags, "
        "re-requisition quantity fields, and related metadata).\n"
        f"- **Source:** `{FILE}`, sheet `medicine_group` (KoboToolbox export, live-synced)."
    )
