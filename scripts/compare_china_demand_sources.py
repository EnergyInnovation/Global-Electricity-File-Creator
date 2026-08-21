"""Source-level diagnostic: old (DemandCast/Wu et al.) vs new provincial China demand.

Compares the two observed hourly national demand series for 2018 -- the only
year both cover -- and reports the new source's multi-year coverage. This is
the input-side companion to ``scripts/test_china_demand_source.py``, which
measures what the swap does to SHELF/SYSHECF.

Writes ``output/china_demand_source_test/source_comparison_2018.csv`` and
prints a summary.

Staff note: annual totals below should be checked against CEC / NBS published
national electricity consumption before either source is treated as
authoritative.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import energy_timeslice_pipeline as pipeline  # noqa: E402

OUT_DIR = os.path.join(REPO_ROOT, 'output', 'china_demand_source_test')
NEW_CSV = os.path.join(REPO_ROOT, 'data', 'manual_downloads', 'CN_hourly_demand_2015_2024.csv')


def describe(series: pd.Series, label: str) -> dict:
    s = series.astype(float)
    daily_peak = s.groupby(s.index.dayofyear).max()
    return {
        'source': label,
        'hours': len(s),
        'annual_TWh': s.sum() / 1e6,
        'mean_GW': s.mean() / 1e3,
        'peak_GW': s.max() / 1e3,
        'min_GW': s.min() / 1e3,
        'load_factor': s.mean() / s.max(),
        'peak_timestamp': str(s.idxmax()),
        'peak_hour_of_day': int(s.idxmax().hour),
        'summer_peak_GW': s[s.index.month.isin([6, 7, 8])].max() / 1e3,
        'winter_peak_GW': s[s.index.month.isin([11, 12, 1, 2])].max() / 1e3,
        'top10_daily_peak_mean_GW': daily_peak.nlargest(10).mean() / 1e3,
        'diurnal_range_pct_of_mean': (
            (s.groupby(s.index.hour).mean().max() - s.groupby(s.index.hour).mean().min())
            / s.mean() * 100
        ),
    }


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    old = pipeline.fetch_demand_data_demandcast('CHN', start_year=2018, end_year=2018)
    old.index = old.index.tz_localize(None)
    new_all = pipeline.load_local_demand_series(NEW_CSV)
    new = new_all[new_all.index.year == 2018]

    rows = [describe(old, 'DemandCast / Wu et al. (current)'),
            describe(new, 'Provincial workbook (new)')]
    summary = pd.DataFrame(rows)

    # Hourly agreement. The two series label the same underlying hours one
    # apart (the DemandCast wrapper stamps the first row 01:00; the new file
    # carries explicit 00:00-based timestamps), so compare both by label and
    # positionally.
    o, n = old.to_numpy(float), new.to_numpy(float)
    m = min(len(o), len(n))
    pos_corr = float(np.corrcoef(o[:m], n[:m])[0, 1])
    joined = pd.concat([old.rename('old'), new.rename('new')], axis=1).dropna()
    label_corr = float(joined['old'].corr(joined['new']))
    nrmse_pos = float(np.sqrt(np.mean((n[:m] - o[:m]) ** 2)) / o[:m].mean())

    monthly = pd.DataFrame({
        'old_TWh': old.groupby(old.index.month).sum() / 1e6,
        'new_TWh': new.groupby(new.index.month).sum() / 1e6,
    })
    monthly['diff_pct'] = (monthly['new_TWh'] / monthly['old_TWh'] - 1) * 100

    diurnal = pd.DataFrame({
        'old_norm': old.groupby(old.index.hour).mean() / old.mean(),
        'new_norm': new.groupby(new.index.hour).mean() / new.mean(),
    })
    diurnal['diff_pct'] = (diurnal['new_norm'] / diurnal['old_norm'] - 1) * 100

    pd.set_option('display.width', 200)
    print('=' * 78)
    print('2018 NATIONAL SERIES -- the only year both sources cover')
    print('=' * 78)
    print(summary.to_string(index=False, float_format=lambda v: f'{v:,.3f}'))
    print(f'\nhourly correlation (positional / same underlying hour): {pos_corr:.4f}')
    print(f'hourly correlation (by timestamp label as each source stamps it): {label_corr:.4f}')
    print(f'hourly NRMSE of new vs old (positional, / mean): {nrmse_pos:.4f}')
    print('\nMONTHLY ENERGY')
    print(monthly.to_string(float_format=lambda v: f'{v:,.2f}'))
    print('\nDIURNAL SHAPE (hour-of-day mean / annual mean, each on its own labels)')
    print(diurnal.to_string(float_format=lambda v: f'{v:,.4f}'))

    print('\nNEW SOURCE COVERAGE BY YEAR')
    cov = pd.DataFrame({
        'annual_TWh': new_all.groupby(new_all.index.year).sum() / 1e6,
        'mean_GW': new_all.groupby(new_all.index.year).mean() / 1e3,
        'peak_GW': new_all.groupby(new_all.index.year).max() / 1e3,
    })
    cov['load_factor'] = cov['mean_GW'] / cov['peak_GW']
    print(cov.to_string(float_format=lambda v: f'{v:,.3f}'))

    summary.to_csv(os.path.join(OUT_DIR, 'source_comparison_2018.csv'), index=False)
    monthly.to_csv(os.path.join(OUT_DIR, 'source_comparison_2018_monthly.csv'))
    diurnal.to_csv(os.path.join(OUT_DIR, 'source_comparison_2018_diurnal.csv'))
    cov.to_csv(os.path.join(OUT_DIR, 'new_source_coverage_by_year.csv'))
    print(f'\nwrote CSVs -> {OUT_DIR}')


if __name__ == '__main__':
    main()
