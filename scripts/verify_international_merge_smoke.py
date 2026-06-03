"""Smoke test for the develop->master international merge.

Verifies, on synthetic net-load data (no external data / network needed):
  1. The merged `cluster_timeslices` wrapper runs and returns the legacy 4-tuple.
  2. days_per_timeslice sums to 365.
  3. Northern-Hemisphere country (United States) -> Summer Peak rep day in Jun-Aug.
  4. Southern-Hemisphere country (Brazil) -> Summer Peak rep day in Dec-Feb.
     (Confirms the country= argument flips the season-month pools.)

This is a structural/behavioral check of the integration, NOT a validation of any
country's actual modeled output. Validate real runs against primary sources.
"""
import os
import sys

import numpy as np
import pandas as pd

# Make the repo-root modules importable when run as scripts/...
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import energy_timeslice_pipeline as p

YEAR = 2018  # non-leap, 8760 hours
idx = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h")
doy = idx.dayofyear.to_numpy()
hour = idx.hour.to_numpy()

# Synthetic bimodal net load: a strong NH-summer (July, ~DOY 196) cooling peak
# AND a strong NH-winter (January, ~DOY 15) heating peak, plus a daily cycle.
# This makes the hemisphere flip unambiguous: NH summer pool (JJA) finds July,
# SH summer pool (DJF) finds January.
summer_bump = 4000.0 * np.exp(-0.5 * ((doy - 196) / 18.0) ** 2)   # July peak
winter_bump = 3500.0 * np.exp(-0.5 * ((doy - 15) / 18.0) ** 2)    # January peak
daily = 1500.0 * np.maximum(0, np.sin((hour - 6) / 24.0 * 2 * np.pi))
base = 10000.0
rng = np.random.default_rng(0)
net = base + summer_bump + winter_bump + daily + rng.normal(0, 120, size=8760)
net = pd.Series(net, index=idx)

SP_ID, WP_ID = 4, 5  # wrapper convention for n_clusters=6, pin_extremes=True


def run(country):
    labels, model, mapping, rep_dates = p.cluster_timeslices(
        net, timestamps=pd.Series(idx, index=idx), n_clusters=6, country=country
    )
    # days per slice = unique calendar days assigned to each integer label
    df = pd.DataFrame({"label": labels.to_numpy(), "date": idx.normalize()})
    days_per = df.groupby("label")["date"].nunique()
    sp_month = pd.Timestamp(rep_dates[SP_ID]).month
    wp_month = pd.Timestamp(rep_dates[WP_ID]).month
    return int(days_per.sum()), dict(days_per), sp_month, wp_month


def main():
    ok = True
    for country, sp_expect in [("UnitedStates", {6, 7, 8}), ("Brazil", {12, 1, 2})]:
        total, days_per, sp_month, wp_month = run(country)
        sp_ok = sp_month in sp_expect
        total_ok = total == 365
        ok = ok and sp_ok and total_ok
        print(f"[{country}]")
        print(f"  days_per_timeslice sums to 365 : {total_ok}  (sum={total})")
        print(f"  days per slice (0..5)          : {days_per}")
        print(f"  Summer Peak rep month          : {sp_month}  expected in {sorted(sp_expect)} -> {'OK' if sp_ok else 'FAIL'}")
        print(f"  Winter Peak rep month          : {wp_month}")
        print()
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
