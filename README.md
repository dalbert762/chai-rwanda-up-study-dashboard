# Unserved Prescriptions Pilot — Dashboard

Analysis and Streamlit dashboard for the Rwanda (Kicukiro District, Kigali City)
medicine stock and prescription pilot, run via KoboToolbox.

## Contents

- `Stock_availability.py` — main dashboard page: facility-level medicine stock
  assessment (availability, stock classification, financial loss from
  stock-outs, requisition vs. consumption). Reads `Pilot_stcok availability.xlsx`.
- `pages/1_Prescriptions.py` — second dashboard page: prescription-level
  assessment (EML compliance, drug classes, availability at time of
  prescription). Reads `Pilot_prescription.xlsx`.
- `theme.py` — shared dark theme (KPI cards, donut/bar chart helpers, section
  headers) used by both pages.
- `analyze_pilot_stock.py` — standalone command-line analysis of the stock
  pilot with cross-tabulations, filterable by health center (`--facility`).
- `.streamlit/config.toml` — Streamlit theme (dark, teal/coral accents).

## Running the dashboard

```bash
pip install -r requirements.txt
streamlit run Stock_availability.py
```

Open the local URL it prints (default `http://localhost:8501`). Use the
sidebar to switch to the Prescriptions page.

## Running the standalone script

```bash
python analyze_pilot_stock.py                        # all facilities
python analyze_pilot_stock.py --facility "Kicukiro CS"
```

## Data notes

Both source workbooks are pilot-scale KoboToolbox exports — read every
share/ranking as illustrative signal, not a powered estimate:

- **Stock assessment**: 2 facilities (Kicukiro CS, Masaka CS), 32 medicines
  each. The workbook's facility-identity sheet has dropped out of its live
  sync at various points; facility names are cross-checked against the
  submission IDs in `Stock_availability.py`.
- **Prescriptions**: 66 data-collection entries / 135 prescription lines
  across 3 facilities (Kicukiro CS, Masaka CS, Busanza CS). Several fields
  are free text with visible data-entry inconsistencies (drug class casing,
  a medicine name typed into the Patient/Prescription ID field on one row) —
  flagged in-app under each page's "Data notes" expander.
