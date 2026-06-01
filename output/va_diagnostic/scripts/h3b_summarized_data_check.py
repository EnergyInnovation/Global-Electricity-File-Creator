"""H3b: From the workbook 'Summarized Data' tab, identify which calendar day each sector's
Summer Peak hour comes from, and check whether all sectors share a single peak day.

Also: confirm the data is *VA*-state-only or NREL national-aggregate. The About says NREL EFS
is the source. With state-level VA, the data should be only VA. We'll inspect.
"""
import os
from openpyxl import load_workbook
import pandas as pd

WB = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\VA\elec\SHELF\Seasonal Hourly Equipment Load Factors by End Use.xlsx"
OUT_DIR = r"C:\Users\RobbieOrvis\Models\Global Electricity File Creator\output\va_diagnostic\tables"

wb = load_workbook(WB, data_only=True, read_only=True)

# Read first ~30 rows of Summarized Data with all columns to identify what data is in there.
ws = wb["Summarized Data"]
rows = []
for i, row in enumerate(ws.iter_rows(values_only=True)):
    rows.append(row)
    if i > 8770:
        break

# Header rows are 1-3
header3 = rows[2]  # this is the column-name row
print("Columns:", [(j, c) for j, c in enumerate(header3) if c])

# Build a DataFrame from rows[3:] using header3 as columns
hdr = [str(c) if c is not None else f"col{i}" for i, c in enumerate(header3)]
data = [r for r in rows[3:] if r and r[0] is not None]
df = pd.DataFrame(data, columns=hdr)
print(f"Rows: {len(df)}")
print("First rows:")
print(df.head(3).to_string())

# Identify the "Ratios of Demand" columns by looking at row 2
header2 = rows[1]
print("\nGroup labels (row 2):", [(j, c) for j, c in enumerate(header2) if c])

# Save first 10 rows
df.head(20).to_csv(os.path.join(OUT_DIR, "h3_summarized_data_head.csv"), index=False)

# Find peak hour by ratio columns: max of each ratio column tells us which row gives the peak,
# and from row's Day column we get the calendar day.
# Look for "Total Load" col
print("\nTotal Load max info:")
if "Total Load" in df.columns:
    df["Total Load"] = pd.to_numeric(df["Total Load"], errors="coerce")
    idx = df["Total Load"].idxmax()
    print(f"Max total at index {idx}: {df.loc[idx].to_dict()}")

# For each "Ratios of Demand" sector column (after position ~26), find its max row
peak_by_col = {}
for j, name in enumerate(hdr):
    if j < 25 or name in (None, ""):
        continue
    try:
        s = pd.to_numeric(df[name], errors="coerce")
    except Exception:
        continue
    if s.notna().sum() < 100:
        continue
    # Restrict to summer rows
    if "Season" in df.columns:
        is_summer = df["Season"].astype(str).str.lower().str.startswith("summer") | (df["Season"] == "Summer")
        s_summer = s[is_summer]
    else:
        s_summer = s
    if s_summer.empty:
        continue
    idx = s_summer.idxmax()
    peak_by_col[name + f"_col{j}"] = (df.loc[idx, "Day"] if "Day" in df.columns else None,
                                       df.loc[idx, "Hour"] if "Hour" in df.columns else None,
                                       float(s_summer.max()))

print("\nPer-sector summer peak day/hour:")
for k, v in peak_by_col.items():
    print(f"  {k}: day={v[0]} hour={v[1]} val={v[2]:.6g}")

# Save
out = pd.DataFrame([{"sector_col": k, "day": v[0], "hour": v[1], "value": v[2]} for k, v in peak_by_col.items()])
out.to_csv(os.path.join(OUT_DIR, "h3_summer_peak_day_per_sector.csv"), index=False)
