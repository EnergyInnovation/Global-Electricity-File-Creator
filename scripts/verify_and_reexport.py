"""Verify SYSHECF + SHELF state in eps-us repo. Re-apply EIA calibration if needed."""
import csv
from pathlib import Path

EPS = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec")

# K6 canonical days per timeslice
K6_DAYS = {
    'Winter': 65, 'Spring': 82, 'Summer': 119, 'Fall': 52,
    'Summer Peak': 27, 'Winter Peak': 20,
}

EIA_TARGET = {
    'SYSHECF-onshore-wind.csv':    0.343,
    'SYSHECF-solar-pv.csv':        0.232,
    'SYSHECF-solar-pv-dist.csv':   0.170,
    'SYSHECF-solar-thermal.csv':   0.250,
    'SYSHECF-offshore-wind.csv':   0.420,
}

SLICE_ORDER = ['Winter','Spring','Summer','Fall','Summer Peak','Winter Peak']
HOUR_COLS = [f'Hour{h}' for h in range(24)]


def read_grid(path):
    with open(path, newline='') as f:
        rows = list(csv.reader(f))
    first_cell = rows[0][0]
    grid = {}
    for r in rows[1:]:
        if not r or not r[0]: continue
        sl = r[0].strip()
        try:
            vals = [float(x) for x in r[1:25]]
        except (ValueError, IndexError):
            continue
        if len(vals) == 24:
            grid[sl] = vals
    return first_cell, grid


def annual_cf(grid, days=K6_DAYS):
    total = 0.0
    for sl in SLICE_ORDER:
        if sl not in grid: continue
        total += sum(grid[sl]) * days[sl]
    return total / 8760.0


def write_grid(path, first_cell, grid):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([first_cell] + HOUR_COLS)
        for sl in SLICE_ORDER:
            if sl in grid:
                w.writerow([sl] + [f"{v:.10g}" for v in grid[sl]])


# 1. Check SHELF days-per-timeslice
shelf_days_path = EPS / "SHELF" / "SHELF-days-per-timeslice.csv"
print("="*70)
print("SHELF days-per-timeslice check")
print("="*70)
shelf_days_actual = {}
with open(shelf_days_path) as f:
    for row in csv.reader(f):
        if row and row[0] in K6_DAYS:
            shelf_days_actual[row[0]] = float(row[1])

ok = True
for sl, expected in K6_DAYS.items():
    actual = shelf_days_actual.get(sl)
    mark = "OK" if actual == expected else "BAD"
    if actual != expected: ok = False
    print(f"  {sl}: expected {expected}, actual {actual}  {mark}")
if not ok:
    print("  ! Re-writing days-per-timeslice...")
    with open(shelf_days_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["Unit: days", "Days per Timeslice"])
        for sl in SLICE_ORDER:
            w.writerow([sl, K6_DAYS[sl]])
    print("  Fixed.")

# 2. Check SYSHECF annual CFs and re-calibrate if needed
print()
print("="*70)
print("SYSHECF EIA calibration check")
print("="*70)
print(f"{'File':<28}{'Target':>10}{'Actual':>10}{'Diff':>10}{'Action':>15}")
print("-"*72)
for fname, target in EIA_TARGET.items():
    path = EPS / "SYSHECF" / fname
    if not path.exists():
        print(f"  {fname}: MISSING")
        continue
    first_cell, grid = read_grid(path)
    actual = annual_cf(grid)
    diff = actual - target
    if abs(diff) < 0.001:
        action = "OK"
    else:
        # Re-calibrate
        scale = target / actual if actual > 1e-6 else 1.0
        new_grid = {sl: [min(1.0, v * scale) for v in vals] for sl, vals in grid.items()}
        write_grid(path, first_cell, new_grid)
        new_cf = annual_cf(new_grid)
        action = f"scaled x{scale:.4f}"
    print(f"  {fname:<28}{target:>10.4f}{actual:>10.4f}{diff:>+10.4f}{action:>15}")


# 3. Check other key SHELF files exist
print()
print("="*70)
print("SHELF files presence check")
print("="*70)
expected_shelf = [
    "SHELF-LDVs", "SHELF-HDVs", "SHELF-aircraft", "SHELF-rail", "SHELF-motorbikes", "SHELF-ships",
    "SHELF-commercial-appliances", "SHELF-commercial-cooling", "SHELF-commercial-envelope",
    "SHELF-commercial-heating", "SHELF-commercial-lighting", "SHELF-commercial-other",
    "SHELF-residential-appliances", "SHELF-residential-cooling", "SHELF-residential-envelope",
    "SHELF-residential-heating", "SHELF-residential-lighting", "SHELF-residential-other",
    "SHELF-industry", "SHELF-datacenters", "SHELF-district-heat-hydrogen", "SHELF-geoeng",
    "SHELF-days-per-timeslice",
]
shelf_dir = EPS / "SHELF"
missing = []
for f in expected_shelf:
    p = shelf_dir / (f + ".csv")
    if not p.exists():
        missing.append(f)
print(f"  Expected: {len(expected_shelf)}, Missing: {len(missing)}")
if missing:
    for m in missing: print(f"    Missing: {m}")
else:
    print("  All SHELF files present.")

print()
print("Done.")
