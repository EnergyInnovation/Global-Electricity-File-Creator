"""Read About + Shoulder Season + Summarized Data headers."""
import os
from openpyxl import load_workbook

WB = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\VA\elec\SHELF\Seasonal Hourly Equipment Load Factors by End Use.xlsx"

wb = load_workbook(WB, data_only=True, read_only=True)

print("=== About ===")
ws = wb["About"]
for row in ws.iter_rows(values_only=True, max_row=40):
    line = " | ".join("" if c is None else str(c) for c in row)
    if line.strip(" |"):
        print(line)

print("\n=== Shoulder Season Calculations ===")
ws = wb["Shoulder Season  Calculations"]
for row in ws.iter_rows(values_only=True, max_row=32):
    line = " | ".join("" if c is None else str(c) for c in row)
    if line.strip(" |"):
        print(line)

print("\n=== Summarized Data header (first 5 rows) ===")
ws = wb["Summarized Data"]
for i, row in enumerate(ws.iter_rows(values_only=True, max_row=5)):
    line = " | ".join("" if c is None else str(c)[:25] for c in row)
    print(f"R{i+1}: {line[:300]}")

# Get one full row of summer-peak from a SHELF tab to see whether values include formulas vs constants
print("\n=== SHELF-residential-cooling tab ===")
wb2 = load_workbook(WB, data_only=False, read_only=True)
ws = wb2["SHELF-residential-cooling"]
for i, row in enumerate(ws.iter_rows(values_only=True, max_row=19)):
    line = " | ".join("" if c is None else str(c)[:30] for c in row)
    print(f"R{i+1}: {line[:600]}")

print("\n=== Double Check tab (reveals formula trail) ===")
ws = wb2["Double Check"]
for i, row in enumerate(ws.iter_rows(values_only=True, max_row=31)):
    line = " | ".join("" if c is None else str(c)[:30] for c in row)
    if line.strip(" |"):
        print(f"R{i+1}: {line[:800]}")
