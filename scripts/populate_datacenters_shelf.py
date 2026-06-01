"""Populate SHELF-datacenters.csv with a flat 24/7 profile.

Data centers run continuously with minimal intra-day variation. A flat shape
is the most defensible default — they're designed to operate near constant
utilization. (For workload-driven daytime peaks, a slight modulation could
be added later, but ~5-10% diurnal variation is typical and a flat profile
captures the bulk of the peak contribution.)

LF[slice, hour] = 1 / 8760 for every (slice, hour) cell.
Balance: sum(LF * days_per_slice * 24 hours-per-day) = 8760/8760 = 1.0
"""
import csv
from pathlib import Path

SHELF_FILE = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SHELF\SHELF-datacenters.csv")

HEADER_LABEL = 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)'
HOUR_COLS = [f'Hour{h}' for h in range(24)]
SLICES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']

FLAT_LF = 1.0 / 8760.0   # ~1.1416e-4

print(f"Flat LF value: {FLAT_LF:.6e}")
print(f"Sum check: sum_24_hours = {24 * FLAT_LF:.6e}")
print(f"  per non-peak slice row × 24 hours = {24 * FLAT_LF:.6f}")

with open(SHELF_FILE, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow([HEADER_LABEL] + HOUR_COLS)
    for sl in SLICES:
        w.writerow([sl] + [f"{FLAT_LF:.10g}"] * 24)

print(f"Wrote: {SHELF_FILE}")

# Verify balance with current days-per-timeslice
days_file = SHELF_FILE.parent / 'SHELF-days-per-timeslice.csv'
days = {}
with open(days_file) as f:
    for row in csv.reader(f):
        if row and row[0] in SLICES:
            days[row[0]] = int(row[1])

balance = sum(FLAT_LF * 24 * days[sl] for sl in SLICES)
print(f"\nDays per timeslice: {days}")
print(f"SHELF-datacenters balance = {balance:.6f} (expected 1.0)")
