"""Verify SHELF workbook formula values match the existing SHELF-*.csv files.

Reproduces the AVERAGEIFS / SUM math in Python using the same aggregated
ResStock + ComStock + EFS source data and the same Cambium-derived clustering,
then compares cell-by-cell to the corresponding `SHELF-*.csv` files in
`eps-us/InputData/elec/SHELF/`.
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from state_pipeline.builders.clustering_repday import cluster_days_repday

CACHE_DIR = ROOT / "data" / "national_aggregated"
CAMBIUM_HOURLY = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"
SHELF_DIR = Path(r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SHELF")

SLICES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']

RESSTOCK_CATS = ['residential-heating', 'residential-cooling', 'residential-lighting',
                 'residential-appliances', 'residential-other']
COMSTOCK_CATS = ['commercial-heating', 'commercial-cooling', 'commercial-lighting',
                 'commercial-appliances', 'commercial-other']
EFS_CATS = ['industry', 'LDVs', 'HDVs', 'rail']
ZERO_CATS = ['residential-envelope', 'commercial-envelope',
             'aircraft', 'ships', 'motorbikes',
             'district-heat-hydrogen', 'geoeng']
FLAT_CATS = ['datacenters']


def load_efs_filtered(year: int = 2024):
    import zipfile, io
    import zipfile_deflate64  # noqa: F401
    needed = ['Electrification', 'TechnologyAdvancement', 'Year',
              'LocalHourID', 'Sector', 'Subsector', 'LoadMW']
    frames = []
    with zipfile.ZipFile(ROOT / "data" / "efs" / "EFSLoadProfile_Reference_Moderate.zip") as zf:
        member = [n for n in zf.namelist() if n.endswith('.csv')][0]
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding='utf-8-sig', newline='')
            reader = pd.read_csv(text, usecols=needed, chunksize=500_000)
            for chunk in reader:
                m = ((chunk['Electrification'].str.lower() == 'reference')
                     & (chunk['TechnologyAdvancement'].str.lower() == 'moderate')
                     & (pd.to_numeric(chunk['Year'], errors='coerce') == year))
                f = chunk.loc[m]
                if not f.empty:
                    frames.append(f.groupby(['LocalHourID', 'Sector', 'Subsector'],
                                            as_index=False)['LoadMW'].sum())
    agg = pd.concat(frames).groupby(['LocalHourID', 'Sector', 'Subsector'],
                                     as_index=False)['LoadMW'].sum()
    piv = agg.pivot_table(index='LocalHourID', columns=['Sector', 'Subsector'],
                          values='LoadMW', aggfunc='sum', fill_value=0.0).sort_index()
    ts = pd.date_range('2018-01-01', periods=8760, freq='h')
    piv.index = ts

    def col(sec, sub):
        return piv[(sec, sub)].astype(float) if (sec, sub) in piv.columns else pd.Series(0.0, index=ts)

    out = pd.DataFrame(index=ts)
    out['industry'] = (col('Industrial', 'machine drives') + col('Industrial', 'process heat')
                       + col('Industrial', 'other'))
    out['LDVs'] = col('Transportation', 'light-duty vehicles')
    out['HDVs'] = (col('Transportation', 'medium-duty trucks')
                   + col('Transportation', 'heavy-duty trucks'))
    out['rail'] = col('Transportation', 'other') * 0.40
    return out


def main():
    # Load aggregated source data
    res = pd.read_csv(CACHE_DIR / 'resstock_national_hourly.csv', index_col=0, parse_dates=True)
    com = pd.read_csv(CACHE_DIR / 'comstock_national_hourly.csv', index_col=0, parse_dates=True)
    efs = load_efs_filtered(year=2024)

    # Cluster
    with open(CAMBIUM_HOURLY) as f:
        lines = f.readlines()
    headers = lines[5].strip().split(',')
    col_idx = {h: i for i, h in enumerate(headers)}
    timestamps = []
    busbar, upv, distpv, won, woff = [], [], [], [], []
    for r in lines[6:]:
        parts = r.strip().split(',')
        try:
            timestamps.append(dt.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S'))
        except (ValueError, IndexError):
            continue
        busbar.append(float(parts[col_idx['busbar_load']]))
        upv.append(float(parts[col_idx['upv_MWh']]))
        distpv.append(float(parts[col_idx['distpv_MWh']]))
        won.append(float(parts[col_idx['wind-ons_MWh']]))
        woff.append(float(parts[col_idx['wind-ofs_MWh']]))
    idx = pd.DatetimeIndex(timestamps)
    cr = cluster_days_repday(
        pd.Series(busbar, index=idx),
        pd.Series(np.array(upv) + np.array(distpv), index=idx),
        pd.Series(np.array(won) + np.array(woff), index=idx),
        peak_top_n=1, max_peak_days=365,
    )
    slice_map = cr.slice_assignment.to_dict()

    # Slice + hour arrays for the 8760 rows (matching how the workbook indexes — sequential)
    n = 8760
    doys = np.array([(i // 24) + 1 for i in range(n)])
    hours = np.array([i % 24 for i in range(n)])
    slices = np.array([slice_map.get(int(d), 'Winter') for d in doys])

    print(f"{'Category':<26}{'max abs diff':>14}{'mean abs diff':>16}{'verdict':>12}")
    print('-' * 68)

    overall_max = 0.0
    for cat in RESSTOCK_CATS + COMSTOCK_CATS + EFS_CATS:
        if cat in RESSTOCK_CATS:
            arr = res[cat].iloc[:n].values
        elif cat in COMSTOCK_CATS:
            arr = com[cat].iloc[:n].values
        elif cat in EFS_CATS:
            arr = efs[cat].iloc[:n].values
        total = arr.sum()
        if total <= 0:
            continue
        computed = {}
        for sl in SLICES:
            for h in range(24):
                mask = (slices == sl) & (hours == h)
                v = arr[mask].mean() / total if mask.sum() > 0 else 0.0
                computed[(sl, h)] = v
        # Read CSV
        csv_path = SHELF_DIR / f"SHELF-{cat}.csv"
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        csv_vals = {}
        for r in rows[1:]:
            if not r or r[0] not in SLICES:
                continue
            sl = r[0]
            for h in range(24):
                try:
                    csv_vals[(sl, h)] = float(r[1 + h])
                except (ValueError, IndexError):
                    csv_vals[(sl, h)] = 0.0
        diffs = [abs(computed[k] - csv_vals.get(k, 0.0)) for k in computed]
        max_d = max(diffs)
        mean_d = sum(diffs) / len(diffs)
        overall_max = max(overall_max, max_d)
        verdict = 'OK' if max_d < 1e-9 else ('CLOSE' if max_d < 1e-5 else 'MISMATCH')
        print(f"{cat:<26}{max_d:>14.2e}{mean_d:>16.2e}{verdict:>12}")

    # Verify zero cats
    print()
    for cat in ZERO_CATS:
        csv_path = SHELF_DIR / f"SHELF-{cat}.csv"
        if not csv_path.exists():
            print(f"{cat:<26}  CSV missing")
            continue
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        all_zero = True
        max_v = 0.0
        for r in rows[1:]:
            if not r or r[0] not in SLICES: continue
            for h in range(24):
                try:
                    v = abs(float(r[1 + h]))
                    if v > 1e-12: all_zero = False
                    max_v = max(max_v, v)
                except (ValueError, IndexError):
                    pass
        verdict = 'OK (all zero)' if all_zero else f'NON-ZERO max={max_v:.2e}'
        print(f"{cat:<26} (zero cat): {verdict}")

    # Verify datacenters (flat 1/8760)
    expected = 1.0 / 8760.0
    csv_path = SHELF_DIR / "SHELF-datacenters.csv"
    if csv_path.exists():
        with open(csv_path) as f:
            rows = list(csv.reader(f))
        max_diff = 0.0
        for r in rows[1:]:
            if not r or r[0] not in SLICES: continue
            for h in range(24):
                try:
                    max_diff = max(max_diff, abs(float(r[1 + h]) - expected))
                except (ValueError, IndexError):
                    pass
        print(f"{'datacenters':<26} (flat 1/8760): max diff from {expected:.6e} = {max_diff:.2e}")
        overall_max = max(overall_max, max_diff)

    print()
    print(f"Overall max abs diff (computed cells): {overall_max:.2e}")
    print("Verdict:", "OK" if overall_max < 1e-9 else "INSPECT")


if __name__ == '__main__':
    main()
