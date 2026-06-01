"""Verify that legacy cluster_timeslices (used by non-US country pipelines)
produces the same slice assignment as the canonical cluster_days_repday
(used by the US national + per-state pipelines).

Both are claimed to implement representative-day clustering on net load with
fixed rep profiles. If they match exactly (or within float noise on the
NRMSE), they can be considered equivalent — the legacy is just unvectorized.

If they diverge, identify why and consolidate.
"""
from __future__ import annotations
import sys
from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from state_pipeline.builders.clustering_repday import cluster_days_repday
from energy_timeslice_pipeline import cluster_timeslices

CAMBIUM = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"


def load_cambium_series():
    """Load Cambium 2024 hourly load + VRE for clustering."""
    with open(CAMBIUM) as f:
        lines = f.readlines()
    headers = lines[5].strip().split(',')
    idx = {h: i for i, h in enumerate(headers)}
    timestamps = []
    busbar, upv, distpv, won, woff = [], [], [], [], []
    for r in lines[6:]:
        parts = r.strip().split(',')
        try:
            timestamps.append(dt.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S'))
        except (ValueError, IndexError):
            continue
        busbar.append(float(parts[idx['busbar_load']]))
        upv.append(float(parts[idx['upv_MWh']]))
        distpv.append(float(parts[idx['distpv_MWh']]))
        won.append(float(parts[idx['wind-ons_MWh']]))
        woff.append(float(parts[idx['wind-ofs_MWh']]))
    di = pd.DatetimeIndex(timestamps)
    return (
        pd.Series(busbar, index=di, name='busbar_load'),
        pd.Series(np.array(upv) + np.array(distpv), index=di, name='solar'),
        pd.Series(np.array(won) + np.array(woff), index=di, name='wind'),
    )


def run_new():
    print("=== cluster_days_repday (canonical) ===")
    busbar, solar, wind = load_cambium_series()
    cr = cluster_days_repday(busbar, solar, wind,
                              peak_top_n=1, max_peak_days=365)
    print(f"  NRMSE={cr.nrmse:.6f}")
    print(f"  days_per_timeslice={cr.days_per_timeslice}")
    print(f"  SP days: {cr.sp_top_days}")
    print(f"  WP days: {cr.wp_top_days}")
    # DOY -> slice name
    return {int(d): cr.slice_assignment[d] for d in cr.slice_assignment.index}


def run_legacy():
    print("=== cluster_timeslices (legacy non-US pipeline) ===")
    busbar, solar, wind = load_cambium_series()
    # cluster_timeslices takes net_load directly. Compute net = busbar - solar - wind.
    net = busbar - solar - wind
    hourly_labels, model, mapping, rep_dates = cluster_timeslices(net)
    # hourly_labels is a Series indexed by hourly timestamps with integer cluster IDs.
    # Convert to DOY -> int -> slice name (legacy uses 0-5 ints).
    # Per legacy convention: pinned peaks get the highest IDs.
    # Inspect rep_dates to figure out which int is which slice.
    print(f"  rep_dates: {sorted(rep_dates.items())}")
    print(f"  hourly_labels distribution: {hourly_labels.value_counts().to_dict()}")

    # Identify peak labels: those whose rep date has the highest net peak in their season pool
    months_per_rep = {lbl: ts.month for lbl, ts in rep_dates.items()}
    # Heuristic: in legacy, peak labels are remaining_clusters + offset = 4 and 5 (n_clusters=6, non-peak=4)
    sp_int = 4
    wp_int = 5
    # For non-peak labels, name them by mean DOY
    nonpeak_labels = sorted([l for l in rep_dates if l not in (sp_int, wp_int)])
    doy_array = hourly_labels.index.dayofyear
    daily_labels = pd.Series([hourly_labels.iloc[i*24] for i in range(365)],
                              index=range(1, 366))
    cluster_mean_doy = {l: daily_labels[daily_labels == l].index.to_series().mean()
                        for l in nonpeak_labels if (daily_labels == l).any()}
    ranked = sorted(cluster_mean_doy.items(), key=lambda kv: kv[1])
    season_names = ['Winter', 'Spring', 'Summer', 'Fall']
    int_to_slice = {int_id: name for (int_id, _), name in zip(ranked, season_names)}
    int_to_slice[sp_int] = 'Summer Peak'
    int_to_slice[wp_int] = 'Winter Peak'

    doy_to_slice = {}
    for doy in range(1, 366):
        try:
            lbl = int(daily_labels[doy])
            doy_to_slice[doy] = int_to_slice.get(lbl, f'Unk{lbl}')
        except KeyError:
            pass

    # Count days per slice
    counts = {}
    for sl in doy_to_slice.values():
        counts[sl] = counts.get(sl, 0) + 1
    print(f"  days_per_timeslice={counts}")
    return doy_to_slice


def main():
    new_assignment = run_new()
    print()
    legacy_assignment = run_legacy()
    print()
    # Compare per-DOY
    n_agree = 0
    n_diff = 0
    diffs = []
    for doy in sorted(new_assignment):
        n = new_assignment[doy]
        l = legacy_assignment.get(doy)
        if n == l:
            n_agree += 1
        else:
            n_diff += 1
            diffs.append((doy, n, l))
    print(f"Comparison:")
    print(f"  DOYs matching:  {n_agree} / {len(new_assignment)}")
    print(f"  DOYs differing: {n_diff}")
    if diffs[:10]:
        print(f"  First 10 disagreements (DOY, new, legacy):")
        for d, n, l in diffs[:10]:
            print(f"    DOY {d}: new={n!r}, legacy={l!r}")


if __name__ == '__main__':
    main()
