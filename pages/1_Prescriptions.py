"""
Streamlit page: Prescriptions pilot
(Unserved Prescriptions - Prescription-level Assessment)

Part of the same multipage app as Stock_availability.py - launched together via:
    streamlit run Stock_availability.py
This file just needs to live in a 'pages/' folder next to it.
"""

import pandas as pd
import streamlit as st

from theme import CORAL, MUTED, TEAL, TEXT, dark_fig, donut_chart, inject_css, kpi_card, section_header

FILE = "Pilot_prescription.xlsx"

st.set_page_config(page_title="Prescriptions — Unserved Prescriptions Pilot", layout="wide")
inject_css()


@st.cache_data
def load_data():
    xls = pd.ExcelFile(FILE)
    main = pd.read_excel(xls, xls.sheet_names[0])
    pres = pd.read_excel(xls, "prescription")
    pres = pres.rename(columns=lambda c: c.strip())
    pres["Date of prescription"] = pd.to_datetime(pres["Date of prescription"])
    empty_cols = pres.columns[pres.isna().all()].tolist()
    pres = pres.drop(columns=empty_cols)
    return main, pres, empty_cols


main, pres_all, empty_cols = load_data()

st.title("Prescriptions")
st.caption("Prescription-level assessment · Kicukiro District, Kigali City")

# ---------------------------------------------------------------
# Filters
# ---------------------------------------------------------------
section_header("Filters", icon="🔍")
facilities = sorted(pres_all["Health facility"].unique())
prescribers = sorted(pres_all["Prescriber category"].dropna().unique())
min_date, max_date = pres_all["Date of prescription"].min().date(), pres_all["Date of prescription"].max().date()

f1, f2, f3, f4, f5 = st.columns(5)
with f1:
    fac_choice = st.selectbox("Health facility (HC)", ["All"] + facilities)
with f2:
    presc_choice = st.selectbox("Prescriber category", ["All"] + prescribers)
with f3:
    date_choice = st.date_input("Date of prescription", value=(min_date, max_date),
                                 min_value=min_date, max_value=max_date)

pres = pres_all.copy()
if fac_choice != "All":
    pres = pres[pres["Health facility"] == fac_choice]
if presc_choice != "All":
    pres = pres[pres["Prescriber category"] == presc_choice]
if isinstance(date_choice, tuple) and len(date_choice) == 2:
    start, end = date_choice
    pres = pres[(pres["Date of prescription"].dt.date >= start) & (pres["Date of prescription"].dt.date <= end)]

if pres.empty:
    st.warning("No prescription lines match the current filters.")
    st.stop()

st.write("")

# ---------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------
n_submissions = pres["_parent_index"].nunique()
n_lines = len(pres)
n_facilities = pres["Health facility"].nunique()
eml_yes = int((pres["On EML?"] == "Yes").sum())
eml_no = n_lines - eml_yes
avail_col = "Was the medicine available at the health facility during the date of prescription?"
avail_yes = int((pres[avail_col] == "Yes").sum())
avail_no = n_lines - avail_yes
avail_pct = (avail_yes / n_lines * 100) if n_lines else 0

k1, k2, k3, k4, k5 = st.columns(5)
kpi_card(k1, "🏥", "Facilities in view", n_facilities)
kpi_card(k2, "🧾", "Data-collection entries", n_submissions)
kpi_card(k3, "💊", "Prescription lines", n_lines)
kpi_card(k4, "📋", "On EML", f"{eml_yes / n_lines * 100:.1f}%")
kpi_card(k5, "✅", "Available at prescription", f"{avail_pct:.1f}%")

if avail_pct == 100:
    st.success(
        "Every prescription line in this view was recorded as available at the facility at the time of "
        "prescription — this pilot has not yet captured an unserved-prescription cost event, so the "
        "downstream fields it's designed to populate (RMS availability, unit price, total_cost_unserved, "
        "distribution reason) are still blank.",
        icon="✅",
    )

st.write("")

# ---------------------------------------------------------------
# Overview
# ---------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    section_header("Available at prescription")
    fig = donut_chart([avail_yes, avail_no] if avail_no else [avail_yes],
                       ["Yes", "No"] if avail_no else ["Yes"],
                       [TEAL, CORAL] if avail_no else [TEAL])
    st.pyplot(fig, width="stretch")

with c2:
    section_header("Lines by facility")
    fac_counts = pres["Health facility"].value_counts()
    total = fac_counts.sum()
    fig, ax = dark_fig((5.2, 3.2))
    order = fac_counts.sort_values().index
    ax.barh(order, fac_counts[order], color=TEAL)
    for i, v in enumerate(fac_counts[order]):
        ax.text(v + total * 0.02, i, f"{int(v)} ({v / total * 100:.1f}%)",
                va="center", fontsize=9.5, color=TEXT)
    ax.set_xlabel("Prescription lines")
    ax.set_xlim(0, total * 0.75)
    st.pyplot(fig, width="stretch")

section_header("Facility × prescriber category")
ct = pd.crosstab(pres["Health facility"], pres["Prescriber category"], margins=True, margins_name="Total")
st.dataframe(ct, width="stretch")

st.caption(
    "Note: one data-collection entry is not always one patient visit — at Busanza CS, a single "
    "submission bundled 31 prescription lines spanning multiple patients and several dates "
    "(18–20 Aug). Treat 'data-collection entries' as batches, not encounters, until confirmed "
    "with the field team."
)

st.divider()

# ---------------------------------------------------------------
# Medicines
# ---------------------------------------------------------------
c3, c4 = st.columns(2)
with c3:
    section_header("On the Essential Medicines List")
    fig = donut_chart([eml_yes, eml_no] if eml_no else [eml_yes],
                       ["Yes", "No"] if eml_no else ["Yes"],
                       [TEAL, CORAL] if eml_no else [TEAL])
    st.pyplot(fig, width="stretch")

    st.write("")
    section_header("Name type")
    name_type = pres["Name type"].value_counts()
    fig2 = donut_chart(name_type.values, name_type.index, [TEAL, CORAL][:len(name_type)])
    st.pyplot(fig2, width="stretch")

with c4:
    section_header("Top drug classes")
    drug_class = pres["Drug class"].astype(str).str.strip().str.lower()
    vc = drug_class.value_counts()
    top_n = vc.head(10)
    other_n = vc.iloc[10:].sum()
    if other_n:
        top_n = pd.concat([top_n, pd.Series({"other (long tail)": other_n})])
    top_n = top_n.sort_values()
    total_lines = vc.sum()
    fig, ax = dark_fig((6, 4.4))
    colors = [MUTED if lbl == "other (long tail)" else TEAL for lbl in top_n.index]
    ax.barh([s.title() for s in top_n.index], top_n.values, color=colors)
    for i, v in enumerate(top_n.values):
        ax.text(v + total_lines * 0.01, i, f"{int(v)} ({v / total_lines * 100:.1f}%)",
                va="center", fontsize=9, color=TEXT)
    ax.set_xlabel("Prescription lines")
    ax.set_xlim(0, top_n.values.max() * 1.5)
    st.pyplot(fig, width="stretch")
    st.caption(
        "Drug class is free text, entered inconsistently (e.g. 'anti', 'ANTI', 'anti-hypertensive', "
        "'hypertension' likely all mean the same class) — bars are lightly cleaned (trimmed, "
        "lower-cased) but not merged across spellings, so this understates the true top categories."
    )

section_header("Qty prescribed — summary")
st.dataframe(pres["Qty prescribed"].describe().round(1).to_frame("value").T, width="stretch")

st.divider()

# ---------------------------------------------------------------
# Detail
# ---------------------------------------------------------------
section_header("Prescription lines (filtered view)")
detail_cols = ["Health facility", "Date of prescription", "Prescriber category",
                "Medicine name (as prescribed)", "Drug class", "Name type", "On EML?", "Qty prescribed"]
st.dataframe(pres[detail_cols].sort_values("Date of prescription", ascending=False),
             width="stretch", hide_index=True)

st.divider()
with st.expander(f"Data notes ({len(empty_cols)} columns excluded, quality flags, source)"):
    st.markdown(
        f"- **{len(empty_cols)} columns were entirely blank** across all {len(pres_all)} lines and excluded: "
        "they only populate when a medicine is *not* available at the facility (order status, unit price, "
        "`total_cost_unserved`, RMS Regional/Central availability, distribution reason) — none of that "
        "branch has been triggered yet in this pilot.\n"
        "- **Patient / Prescription ID column removed:** the raw export had a field with values that could "
        "be real patient identifiers (and, on one row, a medicine name typed into it by mistake) — dropped "
        "before this data was shared, so patient-level counts aren't available here.\n"
        "- **Medicine names are free text** with visible typos (e.g. 'ciprofoxacin', 'Amlodipne') — fine for "
        "a pilot, but worth moving to a selectable list tied to the EML for cleaner rollup analysis.\n"
        f"- **Source:** `{FILE}`, sheets `Unserved Prescriptions - Pre...` and `prescription` "
        "(KoboToolbox export)."
    )
