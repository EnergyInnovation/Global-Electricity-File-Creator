"""Proper K6/H24 rebuild on Cambium 2024 MidCase national 2025 hourly data.

Uses state_pipeline.builders.clustering.cluster_days (k-means + pinned-peak
NRMSE optimization, multi-seed search, netload_focus feature weighting) on
the full national busbar load + VRE generation.

Produces:
  - data/cambium24_midcase_national/clustering_diagnostics.txt
  - data/cambium24_midcase_national/k6_slice_assignment.csv
  - data/cambium24_midcase_national/k6_slice_profiles.csv  (gross/net/VRE/solar/wind per slice, 24-hr)
  - data/cambium24_midcase_national/k6_days_per_timeslice.csv

Run:  python rebuild_national_k6h24.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Make state_pipeline importable from project root
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from state_pipeline.builders.clustering import cluster_days, SLICE_NAMES

INPUT = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"
OUTDIR = ROOT / "data" / "cambium24_midcase_national"


def load_cambium_hourly(path: Path):
    """Return DataFrame with cols busbar_load, enduse_load, net_load_busbar,
    solar (upv+distpv), wind (ons+ofs), all in GW. Indexed by hourly timestamp.

    Cambium 2024 hourly file: rows 1-5 metadata, row 6 machine headers, 8760 data rows.
    """
    with open(path) as f:
        lines = f.readlines()
    headers = lines[5].strip().split(',')
    rows = []
    import datetime as dt
    for line in lines[6:]:
        parts = line.strip().split(',')
        if len(parts) < 5: continue
        try:
            ts = dt.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
        row = {'ts': ts}
        for i, h in enumerate(headers):
            try:
                row[h] = float(parts[i])
            except (ValueError, IndexError):
                row[h] = np.nan
        rows.append(row)
    df = pd.DataFrame(rows).set_index('ts')
    # Convert MWh -> MW (1 hour timestep), report in same units the pipeline expects (MWh per hour ~ MW)
    out = pd.DataFrame({
        'busbar_load': df['busbar_load'],            # MWh per hour (= MW)
        'enduse_load': df['enduse_load'],
        'net_load_busbar': df['net_load_busbar'],
        'solar': df['upv_MWh'] + df['distpv_MWh'],
        'wind':  df['wind-ons_MWh'] + df['wind-ofs_MWh'],
        'var_gen': df['variable_generation'],
    })
    return out


def slice_profile(df_hourly: pd.DataFrame, slice_assignment, sp_top, wp_top):
    """For each slice, mean 24-hour profile of busbar, net, solar, wind, var_gen.
    Uses sp_top / wp_top for peak slices (overrides slice_assignment for those days)."""
    df = df_hourly.copy()
    df['day'] = df.index.dayofyear
    df['hour'] = df.index.hour
    slice_map = slice_assignment.to_dict()
    sp_set = set(sp_top); wp_set = set(wp_top)
    def assign(d):
        if d in sp_set: return 'Summer Peak'
        if d in wp_set: return 'Winter Peak'
        return slice_map.get(d, 'Winter')
    df['slice'] = df['day'].apply(assign)
    cols = ['busbar_load', 'net_load_busbar', 'var_gen', 'solar', 'wind']
    profiles = {}
    for sl in SLICE_NAMES:
        sub = df[df['slice'] == sl]
        if sub.empty:
            profiles[sl] = {c: [0.0]*24 for c in cols}
            continue
        prof = {}
        for c in cols:
            prof[c] = sub.groupby('hour')[c].mean().reindex(range(24)).fillna(0).values.tolist()
        prof['n_days'] = int(sub['day'].nunique())
        profiles[sl] = prof
    return profiles


def main(peak_top_n: int = 5, max_peak_days: int = 10):
    print(f"[load] reading {INPUT}")
    df = load_cambium_hourly(INPUT)
    print(f"[load] {len(df)} rows; "
          f"annual busbar = {df['busbar_load'].sum()/1e6:.1f} TWh; "
          f"annual var_gen = {df['var_gen'].sum()/1e6:.1f} TWh; "
          f"annual peak busbar = {df['busbar_load'].max()/1e3:.1f} GW; "
          f"annual peak net = {df['net_load_busbar'].max()/1e3:.1f} GW")

    total_demand = df['busbar_load']
    solar_gen   = df['solar']
    wind_gen    = df['wind']

    print(f"[cluster] running cluster_days (peak_top_n={peak_top_n}, max_peak_days={max_peak_days})")
    cr = cluster_days(
        total_demand, solar_gen, wind_gen,
        peak_top_n=peak_top_n, max_peak_days=max_peak_days,
        feature_weight_mode='netload_focus',
        summer_months=(6, 7, 8),     # state_pipeline default
        winter_months=(11, 12, 1, 2),
    )
    print(f"[cluster] NRMSE = {cr.nrmse:.4f}  best_seed = {cr.best_seed}")
    print(f"[cluster] score_by_seed = {cr.score_by_seed}")
    print(f"[cluster] days_per_timeslice = {cr.days_per_timeslice}")
    print(f"[cluster] Summer Peak days (DOY): {cr.sp_top_days}")
    print(f"[cluster] Winter Peak days (DOY): {cr.wp_top_days}")

    # Re-attach actual dates for the peak days
    import datetime as dt
    yr = df.index[0].year
    def doy2date(d): return dt.date(yr, 1, 1) + dt.timedelta(days=d-1)
    print(f"[cluster] Summer Peak dates: {[doy2date(d).isoformat() for d in cr.sp_top_days]}")
    print(f"[cluster] Winter Peak dates: {[doy2date(d).isoformat() for d in cr.wp_top_days]}")

    profiles = slice_profile(df, cr.slice_assignment, cr.sp_top_days, cr.wp_top_days)

    # Summary table
    print()
    print(f"{'Slice':<14}{'Days':>6}{'GrossPk':>10}{'GrossHr':>10}{'NetPk':>10}{'NetHr':>10}{'VRE@NetPk':>12}")
    print('-'*72)
    for sl in SLICE_NAMES:
        p = profiles[sl]
        gross_pk = max(p['busbar_load']) / 1e3
        gross_hr = p['busbar_load'].index(max(p['busbar_load']))
        net_pk = max(p['net_load_busbar']) / 1e3
        net_hr = p['net_load_busbar'].index(max(p['net_load_busbar']))
        vre_at_net = p['var_gen'][net_hr] / 1e3
        print(f"{sl:<14}{p['n_days']:>6}{gross_pk:>10.1f}{gross_hr:>10d}{net_pk:>10.1f}{net_hr:>10d}{vre_at_net:>12.1f}")

    print()
    print("Summer Peak 24-hour profile (GW):")
    print(f"{'Hr':>4}{'Gross':>10}{'Net':>10}{'VRE':>10}{'Solar':>10}{'Wind':>10}")
    sp = profiles['Summer Peak']
    for h in range(24):
        print(f"{h:>4}{sp['busbar_load'][h]/1e3:>10.1f}{sp['net_load_busbar'][h]/1e3:>10.1f}"
              f"{sp['var_gen'][h]/1e3:>10.1f}{sp['solar'][h]/1e3:>10.1f}{sp['wind'][h]/1e3:>10.1f}")

    print()
    print("Winter Peak 24-hour profile (GW):")
    print(f"{'Hr':>4}{'Gross':>10}{'Net':>10}{'VRE':>10}{'Solar':>10}{'Wind':>10}")
    wp = profiles['Winter Peak']
    for h in range(24):
        print(f"{h:>4}{wp['busbar_load'][h]/1e3:>10.1f}{wp['net_load_busbar'][h]/1e3:>10.1f}"
              f"{wp['var_gen'][h]/1e3:>10.1f}{wp['solar'][h]/1e3:>10.1f}{wp['wind'][h]/1e3:>10.1f}")

    # Write artifacts
    OUTDIR.mkdir(exist_ok=True, parents=True)

    # 1) slice assignment
    cr.slice_assignment.rename('slice').to_csv(OUTDIR / 'k6_slice_assignment.csv', header=True)

    # 2) slice profiles
    rows = []
    for sl in SLICE_NAMES:
        p = profiles[sl]
        for series_name in ['busbar_load', 'net_load_busbar', 'var_gen', 'solar', 'wind']:
            row = {'slice': sl, 'series_GW': series_name, 'n_days': p['n_days']}
            for h in range(24):
                row[f'Hour{h}'] = p[series_name][h] / 1e3
            rows.append(row)
    pd.DataFrame(rows).to_csv(OUTDIR / 'k6_slice_profiles.csv', index=False)

    # 3) days per timeslice
    pd.DataFrame([{'slice': sl, 'days': cr.days_per_timeslice[sl]} for sl in SLICE_NAMES]) \
      .to_csv(OUTDIR / 'k6_days_per_timeslice.csv', index=False)

    # 4) diagnostics text
    with open(OUTDIR / 'clustering_diagnostics.txt', 'w') as f:
        f.write(f"Cambium 2024 MidCase US National 2025 - K6/H24 proper rebuild\n")
        f.write(f"Input: {INPUT}\n\n")
        f.write(f"peak_top_n = {peak_top_n}\n")
        f.write(f"max_peak_days = {max_peak_days}\n")
        f.write(f"feature_weight_mode = netload_focus\n")
        f.write(f"summer_months = (6,7,8); winter_months = (11,12,1,2)\n\n")
        f.write(f"NRMSE = {cr.nrmse:.6f}\n")
        f.write(f"best_seed = {cr.best_seed}\n")
        f.write(f"score_by_seed = {cr.score_by_seed}\n\n")
        f.write(f"days_per_timeslice = {cr.days_per_timeslice}\n")
        f.write(f"Summer Peak DOYs = {cr.sp_top_days}\n")
        f.write(f"Summer Peak dates = {[doy2date(d).isoformat() for d in cr.sp_top_days]}\n")
        f.write(f"Winter Peak DOYs = {cr.wp_top_days}\n")
        f.write(f"Winter Peak dates = {[doy2date(d).isoformat() for d in cr.wp_top_days]}\n\n")

    print(f"\n[done] artifacts in {OUTDIR}")


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--peak-top-n', type=int, default=5)
    ap.add_argument('--max-peak-days', type=int, default=10)
    args = ap.parse_args()
    main(peak_top_n=args.peak_top_n, max_peak_days=args.max_peak_days)
