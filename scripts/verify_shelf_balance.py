"""Verify SHELF balance in eps-us after copy."""
import csv
from pathlib import Path

SHELF_DIR = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SHELF")

# Read days per timeslice
days = {}
with open(SHELF_DIR / 'SHELF-days-per-timeslice.csv') as f:
    for row in csv.reader(f):
        if row and row[0] in {'Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak'}:
            days[row[0]] = int(row[1])

print(f"days_per_timeslice: {days}  (sum={sum(days.values())})")
print()

# Check each SHELF file
SLICES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
print(f"{'category':<32}{'balance':>10}{'deviation':>12}{'mark':>6}")
print('-'*60)
shelf_files = sorted(SHELF_DIR.glob('SHELF-*.csv'))
worst = 0.0
worst_cat = ''
for fp in shelf_files:
    if 'days-per-timeslice' in fp.name:
        continue
    with open(fp) as f:
        rows = list(csv.reader(f))
    bal = 0.0
    for r in rows[1:]:
        if not r or r[0] not in SLICES: continue
        sl = r[0]
        try:
            row_sum = sum(float(x) for x in r[1:25])
        except (ValueError, IndexError):
            continue
        bal += row_sum * days[sl]
    cat = fp.stem.replace('SHELF-', '')
    dev = abs(bal - 1.0)
    mark = 'OK' if dev < 0.01 else 'BAD'
    print(f"{cat:<32}{bal:>10.4f}{dev:>+12.4f}{mark:>6}")
    if dev > worst:
        worst = dev
        worst_cat = cat

print(f"\nWorst deviation: {worst:.4f} ({worst_cat})")
