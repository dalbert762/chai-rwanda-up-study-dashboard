"""
Quick analysis of Pilot_stcok availability.xlsx
(Unserved Prescriptions - Medicine Stock Assessment pilot)

Two sheets are expected in the workbook:
- 'Unserved Prescriptions - Med...' : one row per facility visit (submission)
- 'medicine_group'                 : one row per medicine assessed per visit (repeat group)

Supports filtering the whole analysis down to a single health center (HC):

    python analyze_pilot_stock.py                       # all facilities
    python analyze_pilot_stock.py --facility "Kicukiro CS"
    python analyze_pilot_stock.py -f masaka              # partial / case-insensitive match
"""

import argparse
import sys

import pandas as pd

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 160)

FILE = "Pilot_stcok availability.xlsx"

# Known facility names for this pilot's two submissions. The workbook's facility-level
# sheet (Province/District/Sector/Facility name) was present earlier in the KoboToolbox
# live-sync but has since dropped out of the export (only 'medicine_group' remains) -
# this mapping is carried over from that earlier read. Reconfirm if more visits are added.
KNOWN_FACILITIES = {
    845991489: "Kicukiro CS",
    846277248: "Masaka CS",
}

# ---------------------------------------------------------------
# 0. CLI
# ---------------------------------------------------------------
parser = argparse.ArgumentParser(description="Analyze the medicine stock pilot, optionally filtered to one HC.")
parser.add_argument("-f", "--facility", default="all",
                     help="Health center (HC) to filter to, e.g. 'Kicukiro CS' or 'Masaka CS'. "
                          "Case-insensitive substring match. Default: 'all' (no filter).")
args = parser.parse_args()

# ---------------------------------------------------------------
# 1. Load and merge
# ---------------------------------------------------------------
xls = pd.ExcelFile(FILE)
med = pd.read_excel(xls, "medicine_group")

if len(xls.sheet_names) > 1:
    facility = pd.read_excel(xls, xls.sheet_names[0])
    fac_cols = ["_index", "Province", "District", "Sector", "Facility (search & select)"]
    facility_small = facility[fac_cols].rename(columns={"Facility (search & select)": "Facility"})
    df = med.merge(facility_small, left_on="_parent_index", right_on="_index", how="left",
                    suffixes=("", "_fac"))
else:
    df = med.copy()
    df["Facility"] = df["_submission__id"].map(KNOWN_FACILITIES).fillna(
        "Visit " + df["_parent_index"].astype(str))

# Drop columns that are entirely empty in this pilot (skip-logic branches never triggered)
empty_cols = df.columns[df.isna().all()]
df = df.drop(columns=empty_cols)

all_facilities = df["Facility"].drop_duplicates().tolist()

# ---------------------------------------------------------------
# 1b. Apply the HC filter, if any
# ---------------------------------------------------------------
facility_filter = args.facility.strip()
if facility_filter.lower() != "all":
    matches = [f for f in all_facilities if facility_filter.lower() in f.lower()]
    if not matches:
        sys.exit(f"No facility matches '{facility_filter}'. Available: {all_facilities}")
    if len(matches) > 1:
        sys.exit(f"'{facility_filter}' matches more than one facility: {matches}. Be more specific.")
    df = df[df["Facility"] == matches[0]].copy()
    active_facility = matches[0]
else:
    active_facility = "All facilities"

# ---------------------------------------------------------------
# 2. Overview
# ---------------------------------------------------------------
n_facilities = df["_parent_index"].nunique()
print("=" * 70)
print("OVERVIEW")
print("=" * 70)
print(f"Filter applied            : {active_facility}")
print(f"Facilities in view        : {n_facilities}  ({', '.join(sorted(df['Facility'].unique()))})")
print(f"Medicine lines assessed   : {len(df)}")
print(f"Columns dropped (all-NaN) : {len(empty_cols)}  -> not yet triggered in this pilot / skip logic")

# ---------------------------------------------------------------
# 3. Key variable distributions
# ---------------------------------------------------------------
print()
print("=" * 70)
print("KEY VARIABLE: Availability on visit day")
print("=" * 70)
avail_counts = df["Available on visit day?"].value_counts(dropna=False)
avail_pct = (avail_counts / len(df) * 100).round(1)
print(pd.DataFrame({"count": avail_counts, "pct": avail_pct}))

print()
print("=" * 70)
print("KEY VARIABLE: Stock classification")
print("=" * 70)
stock_counts = df["stock_classification"].value_counts(dropna=False)
stock_pct = (stock_counts / len(df) * 100).round(1)
print(pd.DataFrame({"count": stock_counts, "pct": stock_pct}))

print()
print("=" * 70)
print("KEY VARIABLE: stock_level_months (months of stock on hand) - summary stats")
print("=" * 70)
print(df["stock_level_months"].describe().round(2))

print()
print("=" * 70)
print("KEY VARIABLE: total_stockout_days (over the 3-month window) - summary stats")
print("=" * 70)
print(df["total_stockout_days"].describe().round(1))
print("Non-zero stockout-day lines:", (df["total_stockout_days"] > 0).sum(), "/", len(df))

# ---------------------------------------------------------------
# 4. Cross-tabulations
# ---------------------------------------------------------------
print()
print("=" * 70)
print("CROSS-TAB 1: Stock classification x Facility")
print("=" * 70)
ct1 = pd.crosstab(df["stock_classification"], df["Facility"], margins=True)
print(ct1)

print()
print("=" * 70)
print("CROSS-TAB 2: Available on visit day? x Facility")
print("=" * 70)
ct2 = pd.crosstab(df["Available on visit day?"], df["Facility"], margins=True)
print(ct2)

print()
print("=" * 70)
print("CROSS-TAB 3: Stock classification x Available on visit day? (consistency check)")
print("=" * 70)
ct3 = pd.crosstab(df["stock_classification"], df["Available on visit day?"], margins=True)
print(ct3)

print()
print("=" * 70)
print("CROSS-TAB 4: Among stocked-out medicines - availability at RMS Central / Regional")
print("=" * 70)
stockouts = df[df["stock_classification"] == "Stock out"]
if not stockouts.empty:
    ct4 = pd.crosstab(stockouts["Available at RMS Central?"], stockouts["Available at RMS Regional?"], margins=True)
    print(ct4)
    print()
    print("Reason recorded (distribution_nationwide) for stock-outs:")
    print(stockouts["distribution_nationwide"].value_counts(dropna=False))
else:
    print("No stock-out lines found for this filter.")

print()
print("=" * 70)
print("CROSS-TAB 5: Which medicines stocked out, by facility")
print("=" * 70)
if not stockouts.empty:
    ct5 = pd.crosstab(stockouts["Medicine"], stockouts["Facility"])
    print(ct5)
else:
    print("No stock-out lines found for this filter.")

# ---------------------------------------------------------------
# 5. Financial loss from stock-outs
# ---------------------------------------------------------------
print()
print("=" * 70)
print("FINANCIAL LOSS (RWF) attributable to stock-outs, by facility")
print("=" * 70)
loss = df.groupby("Facility")["financial_loss"].sum(min_count=1)
print(loss)
print(f"\nTotal estimated financial loss in view: {df['financial_loss'].sum():,.0f} RWF")

print()
print("Top medicines by financial loss:")
top_loss = df[["Medicine", "Facility", "financial_loss", "total_stockout_days"]].dropna(subset=["financial_loss"])
top_loss = top_loss.sort_values("financial_loss", ascending=False)
if top_loss.empty:
    print("(none)")
else:
    print(top_loss.to_string(index=False))

# ---------------------------------------------------------------
# 6. Fulfilment / requisition indicators (only defined for in-stock lines)
# ---------------------------------------------------------------
print()
print("=" * 70)
print("Requisition fulfilment indicators (in-stock lines only)")
print("=" * 70)
fulfil = df.dropna(subset=["fulfilment_pct"])
if fulfil.empty:
    print("(none)")
else:
    print(fulfil.groupby("Facility")[["fulfilment_pct", "request_vs_amc_pct", "delivery_vs_amc_pct"]].mean().round(1))

print()
print("Note: columns", list(empty_cols), "\nwere blank for every row in this pilot dataset (skip-logic branches")
print("not yet triggered, e.g. only 2 facilities submitted and no re-requisition was recorded) - excluded above.")
