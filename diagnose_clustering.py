"""Diagnose clustering — fast vs slow + multiple cap settings.

Goal: verify the fast vectorized version agrees with the original at cap=10,
then explore how cap value affects peak slice size and SHELF aggregate peak.
"""
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from state_pipeline.builders.clustering import cluster_days as slow_cluster
from state_pipeline.builders.clustering_fast import cluster_days_fast as fast_cluster

CAMBIUM = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"


def load_cambium():
    import datetime as dt
    with open(CAMBIUM) as f:
        lines = f.readlines()
    headers = lines[5].strip().split(',')
    rows = []
    for line in lines[6:]:
        parts = line.strip().split(',')
        if len(parts) < 5:
            continue
        try:
            ts = dt.datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
        row = {'_ts': ts}
        for i, h in enumerate(headers):
            try:
                row[h] = float(parts[i])
            except (ValueError, IndexError):
                row[h] = np.nan
        rows.append(row)
    df = pd.DataFrame(rows).set_index('_ts')
    df.index.name = None
    return df


def main():
    df = load_cambium()
    total_demand = df['busbar_load']
    solar_gen = df['upv_MWh'] + df['distpv_MWh']
    wind_gen = df['wind-ons_MWh'] + df['wind-ofs_MWh']

    print("="*72)
    print("Diagnostic: fast_cluster vs slow_cluster, multiple cap values")
    print("="*72)

    # Comparison at cap=10 (where we already have a slow-cluster result)
    print("\n[1] FAST cluster_days_fast(peak_top_n=5, max_peak_days=10)")
    t0 = time.time()
    cr_fast_10 = fast_cluster(total_demand, solar_gen, wind_gen,
                               peak_top_n=5, max_peak_days=10)
    t_fast = time.time() - t0
    print(f"    elapsed: {t_fast:.1f}s; NRMSE={cr_fast_10.nrmse:.6f}; "
          f"days={cr_fast_10.days_per_timeslice}")

    print("\n[2] SLOW cluster_days(peak_top_n=5, max_peak_days=10)")
    t0 = time.time()
    cr_slow_10 = slow_cluster(total_demand, solar_gen, wind_gen,
                               peak_top_n=5, max_peak_days=10)
    t_slow = time.time() - t0
    print(f"    elapsed: {t_slow:.1f}s; NRMSE={cr_slow_10.nrmse:.6f}; "
          f"days={cr_slow_10.days_per_timeslice}")

    print(f"\n  SPEEDUP (fast vs slow at cap=10): {t_slow/t_fast:.1f}x")
    fast_sp = set(cr_fast_10.sp_top_days); slow_sp = set(cr_slow_10.sp_top_days)
    fast_wp = set(cr_fast_10.wp_top_days); slow_wp = set(cr_slow_10.wp_top_days)
    print(f"  Summer Peak agreement: {len(fast_sp & slow_sp)}/{len(fast_sp | slow_sp)} "
          f"(fast-only={sorted(fast_sp-slow_sp)}, slow-only={sorted(slow_sp-fast_sp)})")
    print(f"  Winter Peak agreement: {len(fast_wp & slow_wp)}/{len(fast_wp | slow_wp)} "
          f"(fast-only={sorted(fast_wp-slow_wp)}, slow-only={sorted(slow_wp-fast_wp)})")

    # Explore cap values
    print("\n[3] FAST clustering at different cap values:")
    print(f"{'cap':>6}{'NRMSE':>12}{'SP days':>10}{'WP days':>10}{'Winter':>10}{'Spring':>10}{'Summer':>10}{'Fall':>10}")
    print('-'*78)
    for cap in [10, 15, 20, 27, 30, 40, 60, 100, 365]:
        t0 = time.time()
        cr = fast_cluster(total_demand, solar_gen, wind_gen,
                           peak_top_n=5, max_peak_days=cap)
        elapsed = time.time() - t0
        d = cr.days_per_timeslice
        print(f"{cap:>6}{cr.nrmse:>12.6f}{d['Summer Peak']:>10}{d['Winter Peak']:>10}"
              f"{d['Winter']:>10}{d['Spring']:>10}{d['Summer']:>10}{d['Fall']:>10}  ({elapsed:.1f}s)")

    # Aggregate Summer Peak gross peak from busbar at each cap level
    print(f"\n[4] Summer Peak slice gross peak (busbar) at different cap values:")
    print(f"{'cap':>6}{'SP days':>10}{'SP gross peak GW':>20}{'SP peak hour':>15}")
    print('-'*55)
    for cap in [10, 15, 20, 27, 30, 40, 60, 100, 365]:
        cr = fast_cluster(total_demand, solar_gen, wind_gen,
                           peak_top_n=5, max_peak_days=cap)
        # Compute gross peak in SP slice
        sp_set = set(cr.sp_top_days)
        is_sp = pd.Series([d.dayofyear in sp_set for d in df.index], index=df.index)
        sp_subset = df['busbar_load'][is_sp]
        sp_by_hour = sp_subset.groupby(sp_subset.index.hour).mean()
        print(f"{cap:>6}{len(cr.sp_top_days):>10}{sp_by_hour.max()/1e3:>20.1f}{int(sp_by_hour.idxmax()):>15}")


if __name__ == '__main__':
    main()
