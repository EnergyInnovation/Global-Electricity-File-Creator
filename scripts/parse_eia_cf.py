"""Parse EIA Table 4.8.B and compare to SYSHECF."""
from openpyxl import load_workbook

wb = load_workbook(r"C:\Users\RobbieOrvis\Downloads\epa_04_08_b.xlsx", data_only=True)
print("Sheets:", wb.sheetnames)
ws = wb.active
print(f"Active sheet: {ws.title}, dim: {ws.dimensions}")
print()
for row in ws.iter_rows(min_row=1, max_row=30, values_only=True):
    print(" | ".join(str(c) if c is not None else "" for c in row))
