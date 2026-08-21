"""Impact test: swapping China's observed hourly demand source.

Runs the China preset under several demand-source / calibration-window
configurations and diffs the resulting SHELF and SYSHECF tables against the
current production baseline.

Variants (everything not listed is the China preset default):

    A_baseline_dc2018   DemandCast (Wu et al.), year 2018, 1-year window
                        -- the current production configuration
    B_newcsv_2018_1y    New provincial CSV, year 2018, 1-year window
                        -- isolates the demand-source swap
    C_newcsv_2018_4y    New provincial CSV, year 2018, 2015-2018 window
                        -- adds the 4-year calibration window
    D_newcsv_2024_4y    New provincial CSV, year 2024, 2021-2024 window
                        -- the configuration the new source makes possible

Outputs land in ``output/china_demand_source_test/<variant>/`` and the diff
tables in ``output/china_demand_source_test/``.

Staff note: results are a draft input for review. The SHELF/SYSHECF deltas
reported here should be checked against primary sources (CEC/NBS national
consumption, Ember capacity factors) before any of these configurations is
adopted for a published EPS-China run.

Usage::

    python scripts/test_china_demand_source.py            # run everything
    python scripts/test_china_demand_source.py --diff-only # re-diff existing runs
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import energy_timeslice_pipeline as pipeline  # noqa: E402

TEST_ROOT = os.path.join(REPO_ROOT, 'output', 'china_demand_source_test')
NEW_DEMAND_CSV = os.path.join('data', 'manual_downloads', 'CN_hourly_demand_2015_2024.csv')

SLICES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']

# ``demand_series_csv`` here is the runner-style override passed straight through
# to the pipeline: 'demandcast' forces DemandCast, a path forces that CSV, and
# None lets the China preset's rule decide (DemandCast at year 2018 + 1-year
# window, the Yi et al. CSV otherwise). A and B both sit on the pinned config,
# so each states its source explicitly; C/D/E leave it to the rule, which also
# checks the rule fires.
VARIANTS: List[Dict[str, object]] = [
    {'name': 'A_baseline_dc2018', 'year': 2018, 'last_n_years': 1, 'demand_series_csv': 'demandcast'},
    {'name': 'B_newcsv_2018_1y', 'year': 2018, 'last_n_years': 1, 'demand_series_csv': NEW_DEMAND_CSV},
    {'name': 'C_newcsv_2018_4y', 'year': 2018, 'last_n_years': 4, 'demand_series_csv': None},
    {'name': 'D_newcsv_2024_4y', 'year': 2024, 'last_n_years': 4, 'demand_series_csv': None},
    # 2024 is a leap year and the run's days-per-timeslice sums to 366, which
    # breaks the EPS convention of 365. E repeats D on the most recent non-leap
    # target year to confirm that is a leap-year artifact rather than a
    # consequence of the new source.
    {'name': 'E_newcsv_2023_4y', 'year': 2023, 'last_n_years': 4, 'demand_series_csv': None},
]

BASELINE = 'A_baseline_dc2018'


def variant_workbook(name: str) -> str:
    return os.path.join(TEST_ROOT, name, 'China_timeslice_results.xlsx')


def eps_dir(name: str) -> str:
    return os.path.splitext(variant_workbook(name))[0] + '_EPS'


def run_variant(variant: Dict[str, object]) -> None:
    name = str(variant['name'])
    out_path = variant_workbook(name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print('\n' + '=' * 78)
    override = variant['demand_series_csv']
    print(f"RUN {name}: year={variant['year']}  last_n_years={variant['last_n_years']}  "
          f"demand override={override if override else 'none (preset rule decides)'}")
    print('=' * 78, flush=True)
    t0 = time.perf_counter()
    pipeline.generate_full_pipeline_for_preset(
        country='China',
        year=variant['year'],
        last_n_years=variant['last_n_years'],
        demand_series_csv=variant['demand_series_csv'],
        n_clusters=6,
        output_path=out_path,
        use_cache=True,
        cache_dir=os.path.join(pipeline.DEFAULT_DATA_DIR, 'cache'),
        make_plots=True,
    )
    print(f"[{name}] finished in {time.perf_counter() - t0:,.0f}s", flush=True)


# ---------------------------------------------------------------------------
# Diffing
# ---------------------------------------------------------------------------

def read_table(path: str) -> Optional[pd.DataFrame]:
    """Read a 6x24 SHELF/SYSHECF CSV into a slice x hour frame."""
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, index_col=0)
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.loc[[s for s in SLICES if s in df.index]]
    return df


def days_per_slice(name: str) -> Optional[pd.Series]:
    path = os.path.join(eps_dir(name), 'SHELF', 'SHELF-days-per-timeslice.csv')
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, index_col=0)
    return pd.to_numeric(df.iloc[:, 0], errors='coerce').reindex(SLICES)


def annual_weighted_mean(table: pd.DataFrame, days: pd.Series) -> float:
    """Days-weighted annual mean of a 6x24 capacity-factor table."""
    hourly = table.mean(axis=1)
    w = days.reindex(hourly.index)
    return float((hourly * w).sum() / w.sum())


def shelf_balance(table: pd.DataFrame, days: pd.Series) -> float:
    """SHELF balance check: sum over slices of (row sum x days) should be 1."""
    w = days.reindex(table.index)
    return float((table.sum(axis=1) * w).sum())


def diff_family(family: str, variants: List[str]) -> pd.DataFrame:
    base_dir = os.path.join(eps_dir(BASELINE), family)
    if not os.path.isdir(base_dir):
        raise SystemExit(f'Baseline {family} directory missing: {base_dir}')
    files = sorted(
        f for f in os.listdir(base_dir)
        if f.endswith('.csv') and 'days-per-timeslice' not in f
    )
    base_days = days_per_slice(BASELINE)
    rows = []
    for fname in files:
        base = read_table(os.path.join(base_dir, fname))
        if base is None or base.empty:
            continue
        base_flat = base.to_numpy().ravel()
        base_is_zero = np.allclose(np.nan_to_num(base_flat), 0.0)
        for name in variants:
            comp = read_table(os.path.join(eps_dir(name), family, fname))
            if comp is None or comp.empty:
                rows.append({'family': family, 'file': fname, 'variant': name,
                             'status': 'missing'})
                continue
            comp_flat = comp.to_numpy().ravel()
            n = min(len(base_flat), len(comp_flat))
            b, c = base_flat[:n], comp_flat[:n]
            mask = np.isfinite(b) & np.isfinite(c)
            b, c = b[mask], c[mask]
            days = days_per_slice(name)
            denom = np.abs(b).mean()
            row = {
                'family': family,
                'file': fname,
                'variant': name,
                'status': 'zero-by-design' if base_is_zero and np.allclose(c, 0.0) else 'ok',
                'base_mean': float(b.mean()),
                'new_mean': float(c.mean()),
                'mean_abs_diff': float(np.abs(c - b).mean()),
                'max_abs_diff': float(np.abs(c - b).max()) if len(b) else np.nan,
                'rel_mean_abs_diff_pct': float(np.abs(c - b).mean() / denom * 100) if denom else np.nan,
                'corr': float(np.corrcoef(b, c)[0, 1]) if b.std() > 0 and c.std() > 0 else np.nan,
            }
            if family == 'SHELF':
                row['base_balance'] = shelf_balance(base, base_days)
                row['new_balance'] = shelf_balance(comp, days)
            else:
                row['base_annual_cf'] = annual_weighted_mean(base, base_days)
                row['new_annual_cf'] = annual_weighted_mean(comp, days)
            rows.append(row)
    return pd.DataFrame(rows)


def cluster_summary(variants: List[str]) -> pd.DataFrame:
    rows = []
    for name in variants:
        days = days_per_slice(name)
        if days is None:
            continue
        row = {'variant': name}
        row.update({f'days_{s}': (int(days[s]) if pd.notna(days.get(s)) else None) for s in SLICES})
        row['days_total'] = int(days.sum())
        # Peak hour + peak value of the total-residential+industry demand proxy:
        # use the Summer Peak / Winter Peak rows of a representative SHELF file.
        for cat, fname in [('res-cooling', 'SHELF-residential-cooling.csv'),
                           ('industry', 'SHELF-industry.csv')]:
            tbl = read_table(os.path.join(eps_dir(name), 'SHELF', fname))
            if tbl is None or tbl.empty:
                continue
            for slc in ['Summer Peak', 'Winter Peak']:
                if slc in tbl.index and np.isfinite(tbl.loc[slc]).any():
                    row[f'{cat}_{slc.replace(" ", "")}_peakhour'] = int(np.nanargmax(tbl.loc[slc].to_numpy()))
        rows.append(row)
    return pd.DataFrame(rows)


# EPS prior end-use -> SHELF category file. The prior supplies the annual MWh
# weights needed to turn per-category load factors back into a system shape.
PRIOR_TO_SHELF = {
    'industry': 'SHELF-industry.csv',
    'residential_appliances': 'SHELF-residential-appliances.csv',
    'residential_cooling': 'SHELF-residential-cooling.csv',
    'residential_heating': 'SHELF-residential-heating.csv',
    'residential_lighting': 'SHELF-residential-lighting.csv',
    'residential_other': 'SHELF-residential-other.csv',
    'service_appliances': 'SHELF-commercial-appliances.csv',
    'service_cooling': 'SHELF-commercial-cooling.csv',
    'service_heating': 'SHELF-commercial-heating.csv',
    'service_lighting': 'SHELF-commercial-lighting.csv',
    'service_other': 'SHELF-commercial-other.csv',
    'transport': 'SHELF-LDVs.csv',
}


def system_peak_shape(name: str, year: int) -> Optional[pd.DataFrame]:
    """Reconstruct the system-level demand shape (GW) implied by a run's SHELF.

    EPS multiplies each category's annual energy by its SHELF load factors, so
    ``system[s, h] = sum_cat E_cat * LF_cat[s, h]``. Annual energies come from
    the EPS-China prior. Each category is divided by its own SHELF balance
    first, so a category whose table does not conserve energy (see the balance
    column in the SHELF diff) still contributes its full annual total rather
    than a fraction of it -- otherwise the label-invariant peak comparison
    would inherit that separate defect.

    This is a comparison diagnostic, not an EPS result: real EPS-China annual
    energies come from the model's own BAU inputs.
    """
    prior_path = os.path.join(REPO_ROOT, 'data', 'eps_priors', 'eps_prior_CN.csv')
    if not os.path.exists(prior_path):
        return None
    prior = pd.read_csv(prior_path, comment='#')  # skip the provenance header
    years = sorted(prior['year'].unique())
    use_year = year if year in years else min(years, key=lambda y: abs(y - year))
    prior = prior[prior['year'] == use_year].set_index('end_use')['eps_mwh_per_year']

    days = days_per_slice(name)
    total = None
    for end_use, fname in PRIOR_TO_SHELF.items():
        if end_use not in prior.index:
            continue
        tbl = read_table(os.path.join(eps_dir(name), 'SHELF', fname))
        if tbl is None or tbl.empty:
            continue
        bal = shelf_balance(tbl, days)
        if not np.isfinite(bal) or bal <= 0:
            continue
        # MWh/yr * LF -> MWh in that hour == MW average power; /1e3 -> GW.
        contrib = tbl.fillna(0.0) * (float(prior[end_use]) / bal) / 1e3
        total = contrib if total is None else total.add(contrib, fill_value=0.0)
    return total


def peak_slice_report(variants: List[str], years: Dict[str, int]) -> pd.DataFrame:
    """Label-invariant view: the two pinned peak slices plus the system shape.

    The four non-peak EPS labels (Winter/Spring/Summer/Fall) are assigned by a
    dominant-month heuristic and are NOT stable across runs, so a file-by-file
    diff on those rows mixes real change with relabelling. Summer Peak and
    Winter Peak are pinned by construction and are directly comparable.
    """
    rows = []
    for name in variants:
        shape = system_peak_shape(name, years.get(name, 2018))
        days = days_per_slice(name)
        if shape is None or days is None:
            continue
        row = {'variant': name, 'days_total': int(days.sum())}
        annual_gw = float((shape.mean(axis=1) * days).sum() / days.sum())
        row['implied_annual_mean_GW'] = annual_gw
        for slc in ['Summer Peak', 'Winter Peak']:
            if slc not in shape.index:
                continue
            prof = shape.loc[slc]
            tag = slc.replace(' ', '')
            row[f'{tag}_days'] = int(days[slc])
            row[f'{tag}_peak_GW'] = float(prof.max())
            row[f'{tag}_peak_hour'] = int(np.nanargmax(prof.to_numpy()))
            row[f'{tag}_mean_GW'] = float(prof.mean())
            row[f'{tag}_peak_over_annual_mean'] = float(prof.max()) / annual_gw
        rows.append(row)
    return pd.DataFrame(rows)


def metrics_summary(variants: List[str]) -> pd.DataFrame:
    frames = []
    for name in variants:
        path = os.path.splitext(variant_workbook(name))[0] + '_Metrics.csv'
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path)
        df.insert(0, 'variant', name)
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--diff-only', action='store_true',
                    help='Skip the pipeline runs and only re-diff existing outputs.')
    ap.add_argument('--only', nargs='*', default=None,
                    help='Run only these variant names.')
    args = ap.parse_args()

    os.makedirs(TEST_ROOT, exist_ok=True)
    pipeline.set_verbosity('normal')

    selected = [v for v in VARIANTS if not args.only or v['name'] in args.only]
    if not args.diff_only:
        for variant in selected:
            run_variant(variant)

    names = [str(v['name']) for v in VARIANTS if os.path.isdir(eps_dir(str(v['name'])))]
    comparisons = [n for n in names if n != BASELINE]
    if BASELINE not in names:
        raise SystemExit(f'Baseline run {BASELINE} not found under {TEST_ROOT}.')

    shelf = diff_family('SHELF', comparisons)
    syshecf = diff_family('SYSHECF', comparisons)
    clusters = cluster_summary(names)
    metrics = metrics_summary(names)
    years = {str(v['name']): int(v['year']) for v in VARIANTS}  # type: ignore[arg-type]
    peaks = peak_slice_report(names, years)
    peaks.to_csv(os.path.join(TEST_ROOT, 'peak_slice_report.csv'), index=False)

    shelf.to_csv(os.path.join(TEST_ROOT, 'diff_SHELF.csv'), index=False)
    syshecf.to_csv(os.path.join(TEST_ROOT, 'diff_SYSHECF.csv'), index=False)
    clusters.to_csv(os.path.join(TEST_ROOT, 'cluster_summary.csv'), index=False)
    if not metrics.empty:
        metrics.to_csv(os.path.join(TEST_ROOT, 'metrics_all_variants.csv'), index=False)

    pd.set_option('display.width', 200)
    print('\n\n' + '=' * 78)
    print('DAYS PER TIMESLICE')
    print('=' * 78)
    print(clusters.to_string(index=False))

    print('\n' + '=' * 78)
    print('PINNED PEAK SLICES (label-invariant) + EPS-prior-weighted system shape')
    print('=' * 78)
    print(peaks.to_string(index=False, float_format=lambda v: f'{v:,.3f}'))

    for family, df in [('SHELF', shelf), ('SYSHECF', syshecf)]:
        print('\n' + '=' * 78)
        print(f'{family} DIFF vs {BASELINE}  (non-zero tables only)')
        print('=' * 78)
        live = df[df['status'] == 'ok'].copy() if 'status' in df else df
        for name in comparisons:
            sub = live[live['variant'] == name]
            if sub.empty:
                continue
            print(f'\n--- {name} ---')
            cols = ['file', 'base_mean', 'new_mean', 'mean_abs_diff', 'max_abs_diff',
                    'rel_mean_abs_diff_pct', 'corr']
            cols += ([c for c in ('base_balance', 'new_balance') if c in sub]
                     if family == 'SHELF'
                     else [c for c in ('base_annual_cf', 'new_annual_cf') if c in sub])
            print(sub[cols].to_string(index=False, float_format=lambda v: f'{v:,.4f}'))

    print(f'\nWrote diff tables -> {TEST_ROOT}')


if __name__ == '__main__':
    main()
