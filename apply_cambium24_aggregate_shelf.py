"""Apply Cambium 2024 K6/H24 aggregate load shape to all eps-us SHELF categories.

Quick test approach: replaces each per-category SHELF file with the AGGREGATE
Cambium 2024 K6/H24 load shape, so that the model's total demand-by-hour
exactly matches Cambium 2024 (after multiplying by annual category energies).

Limitations / caveats:
  - All categories get the same shape; per-category shape diversity is lost.
    (Residential cooling LF in Winter Peak will be non-zero; LDV LF at noon
    will look like aggregate noon shape, etc.) The AGGREGATE total demand
    is correct, which is what the reliability mechanism uses.
  - For a more accurate test, the per-category SHELF rebuild from EFS
    national hourly is the next step (see rebuild_national_k6h24_shelf.py).

Inputs:
  - data/cambium24_midcase_national/k6_slice_profiles.csv (from rebuild_national_k6h24.py)
  - data/cambium24_midcase_national/k6_days_per_timeslice.csv

Outputs:
  - C:/Users/RobbieOrvis/Models/US/Models/eps-us/InputData/elec/SHELF/SHELF-*.csv
"""
from __future__ import annotations
import csv
from pathlib import Path
import pandas as pd

PROJ = Path(__file__).parent
PROFILES = PROJ / "data" / "cambium24_midcase_national" / "k6_slice_profiles.csv"
DAYS = PROJ / "data" / "cambium24_midcase_national" / "k6_days_per_timeslice.csv"

EPS_SHELF = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SHELF")

SLICES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
HOURS = [f'Hour{h}' for h in range(24)]


def main():
    print(f"[load] reading {PROFILES}")
    profiles = pd.read_csv(PROFILES)
    days_df = pd.read_csv(DAYS)
    days_per_slice = dict(zip(days_df['slice'], days_df['days']))
    print(f"[load] days_per_timeslice = {days_per_slice} (sum={sum(days_per_slice.values())})")

    # Build aggregate LF table: LF[slice, hour] = busbar_load_GW[slice, hour] / total_annual_GWh
    # where total_annual_GWh = sum_slices(sum_hours(busbar_GW[slice, hour]) * days[slice])
    busbar = profiles[profiles['series_GW'] == 'busbar_load'].set_index('slice')
    total_annual = 0.0
    for sl in SLICES:
        row = busbar.loc[sl]
        slice_24hr_sum = sum(row[h] for h in HOURS)  # GW summed across 24 hours (= GW-h for 1 day)
        total_annual += slice_24hr_sum * days_per_slice[sl]  # GW-h annually

    print(f"[build] reconstructed annual busbar = {total_annual/1000:.1f} TWh "
          f"(Cambium 2024 actual = 4408.1 TWh)")

    # Build LF table
    lf_table = {}
    for sl in SLICES:
        row = busbar.loc[sl]
        lf_table[sl] = [float(row[h]) / total_annual for h in HOURS]

    # Verify balance
    bal = sum(sum(lf_table[sl]) * days_per_slice[sl] for sl in SLICES)
    print(f"[verify] aggregate LF balance = {bal:.6f}  (expected 1.0)")
    assert abs(bal - 1.0) < 0.001, f"aggregate balance off: {bal}"

    # Write days-per-timeslice
    out_days = EPS_SHELF / 'SHELF-days-per-timeslice.csv'
    with open(out_days, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Unit: days', 'Days per Timeslice'])
        for sl in SLICES:
            w.writerow([sl, days_per_slice[sl]])
    print(f"[write] {out_days}")

    # Write each SHELF category file with the aggregate shape
    shelf_files = sorted(EPS_SHELF.glob('SHELF-*.csv'))
    written = 0
    skipped = []
    for fp in shelf_files:
        if 'days-per-timeslice' in fp.name:
            continue
        cat = fp.stem.replace('SHELF-', '')

        # Detect "all zero" categories — preserve them as zero (the model treats them specially)
        existing = pd.read_csv(fp)
        # The first column is "Unit: dimensionless (ratio ...)"
        first_col = existing.columns[0]
        all_zero = True
        for _, r in existing.iterrows():
            if str(r[first_col]) not in SLICES: continue
            vals = [float(r[c]) for c in HOURS if c in existing.columns]
            if any(abs(v) > 1e-12 for v in vals):
                all_zero = False
                break
        if all_zero:
            skipped.append(cat)
            continue

        header_label = first_col  # preserve the unit label exactly
        with open(fp, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow([header_label] + HOURS)
            for sl in SLICES:
                # Write LF row with sufficient precision
                w.writerow([sl] + [f"{v:.10g}" for v in lf_table[sl]])
        written += 1

    print(f"[write] wrote {written} SHELF category files with aggregate shape")
    print(f"[skip] preserved {len(skipped)} all-zero categories: {skipped}")


if __name__ == '__main__':
    main()
