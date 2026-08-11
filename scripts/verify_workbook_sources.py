"""Verify workbook-source CSVs against a run's exported EPS CSVs (any region).

For a given <run>_EPS directory, re-applies the representative-day math to
workbook_sources/{demand,cf}_hourly_source.csv + clustering.csv and compares
every cell against the exported SHELF-*.csv / SYSHECF-*.csv ground truth:

  SHELF   LF[slice, hour] = <col at (rep-day of slice, hour)> / SUM(col)
          (sum mode: combined; template_split: sum of per-column LFs x
           EPS-template weight per cell)
  SYSHECF CF[slice, hour] = <CF_<tech> at (rep-day of slice, hour)>

Max abs diff should be float noise (~1e-12). Blank cells in all-zero
categories are treated as 0.

Run:
    python scripts/verify_workbook_sources.py [<run>_EPS dir ...]
Defaults to output/UnitedStates_timeslice_results_EPS.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from energy_timeslice_pipeline import (  # noqa: E402
    DEFAULT_EPS_TEMPLATE_ROOT, EPS_HOUR_COLUMNS, EPS_SHELF_FILE_MAP,
    EPS_TIMESLICE_ORDER, _load_existing_eps_csv,
)

TOL = 1e-9


def _strip_lf(name: str) -> str:
    return name[:-len('_load_factor')] if name.endswith('_load_factor') else name


def _resolve_spec(spec, demand_cols: set, template_dir: Path):
    """Mirror _build_eps_table_from_spec's option resolution against the
    demand-source columns. Returns a normalized (kind, payload) or None."""
    if spec is None or not isinstance(spec, (dict, str)):
        return None
    if isinstance(spec, str):
        spec = {'mode': 'direct', 'column': spec}
    mode = spec.get('mode', 'direct')
    if mode == 'first_available':
        for option in spec.get('options', []):
            resolved = _resolve_spec(option, demand_cols, template_dir)
            if resolved is not None:
                return resolved
        return None
    if mode == 'direct':
        col = _strip_lf(spec['column'])
        return ('direct', col) if col in demand_cols else None
    if mode == 'sum':
        cols = [_strip_lf(c) for c in spec.get('columns', [])]
        return ('sum', cols) if all(c in demand_cols for c in cols) else None
    if mode == 'zeros':
        return ('zeros', None)
    if mode == 'uniform_annual_share':
        return ('flat', None)
    if mode == 'template_split':
        agg = [_strip_lf(c) for c in spec.get('aggregate_columns', [])]
        peers = list(spec.get('peer_files', []))
        if not all(c in demand_cols for c in agg):
            return None
        if not all((template_dir / f'{p}.csv').exists() for p in peers):
            return None
        return ('split', (agg, peers))
    return None


def _read_table(path: Path) -> pd.DataFrame:
    tbl = _load_existing_eps_csv(str(path))
    return tbl.reindex(index=EPS_TIMESLICE_ORDER, columns=EPS_HOUR_COLUMNS).astype(float)


def _repday_pick(df: pd.DataFrame, col: str, rep: int) -> np.ndarray:
    day = df[df['day_of_year'] == rep].sort_values('hour_of_day')
    return day[col].to_numpy(dtype=float)


def verify_eps_dir(eps_dir: Path) -> int:
    src = eps_dir / 'workbook_sources'
    demand = pd.read_csv(src / 'demand_hourly_source.csv')
    cf = pd.read_csv(src / 'cf_hourly_source.csv')
    clus = pd.read_csv(src / 'clustering.csv')
    rep_doy = dict(zip(clus['slice_name'].dropna(),
                       clus['rep_doy'].dropna().astype(int)))
    days = dict(zip(clus['slice_name'].dropna(), clus['days'].dropna().astype(int)))
    template_dir = Path(DEFAULT_EPS_TEMPLATE_ROOT) / 'SHELF'
    demand_cols = set(demand.columns)
    failures = 0
    worst, worst_name = 0.0, ''

    def check(name: str, expected: pd.DataFrame, csv_path: Path):
        nonlocal failures, worst, worst_name
        actual = _read_table(csv_path)
        d = float(np.max(np.abs(
            np.nan_to_num(expected.to_numpy(), nan=0.0)
            - np.nan_to_num(actual.to_numpy(), nan=0.0))))
        flag = '' if d < TOL else '  <-- FAIL'
        print(f'  {name:34s} max abs diff {d:.3e}{flag}')
        if d >= TOL:
            failures += 1
        if d > worst:
            worst, worst_name = d, name

    # days-per-timeslice
    days_csv = eps_dir / 'SHELF' / 'SHELF-days-per-timeslice.csv'
    if days_csv.exists():
        actual_days = pd.read_csv(days_csv, index_col=0).iloc[:, 0]
        mismatch = [s for s in days if int(actual_days.get(s, -1)) != days[s]]
        print(f'  {"SHELF-days-per-timeslice":34s} '
              + ('OK' if not mismatch else f'MISMATCH {mismatch}  <-- FAIL'))
        failures += bool(mismatch)

    print('--- SHELF ---')
    for file_name, spec in EPS_SHELF_FILE_MAP.items():
        if file_name == 'SHELF-days-per-timeslice':
            continue
        csv_path = eps_dir / 'SHELF' / f'{file_name}.csv'
        if not csv_path.exists():
            continue
        resolved = _resolve_spec(spec, demand_cols, template_dir)
        if resolved is None:
            print(f'  {file_name:34s} skipped (template copy / unresolved)')
            continue
        kind, payload = resolved
        expected = pd.DataFrame(0.0, index=EPS_TIMESLICE_ORDER, columns=EPS_HOUR_COLUMNS)
        if kind == 'flat':
            expected += 1.0 / 8760.0
        elif kind in ('direct', 'sum', 'split'):
            templates = {}
            if kind == 'split':
                _agg, peers = payload
                for p in peers:
                    templates[p] = _read_table(template_dir / f'{p}.csv').fillna(0.0)
            for sl in EPS_TIMESLICE_ORDER:
                if sl not in rep_doy:
                    continue
                rep = rep_doy[sl]
                if kind == 'direct':
                    vals = _repday_pick(demand, payload, rep) / demand[payload].sum()
                elif kind == 'sum':
                    vals = (sum(_repday_pick(demand, c, rep) for c in payload)
                            / sum(demand[c].sum() for c in payload))
                else:
                    agg_cols, peers = payload
                    agg_lf = sum(_repday_pick(demand, c, rep) / demand[c].sum()
                                 for c in agg_cols)
                    peer_sum = sum(templates[p].loc[sl].to_numpy() for p in peers)
                    me = templates[file_name].loc[sl].to_numpy()
                    with np.errstate(divide='ignore', invalid='ignore'):
                        weight = np.where(peer_sum == 0, 0.0, me / peer_sum)
                    vals = agg_lf * weight
                expected.loc[sl] = vals
        check(file_name, expected, csv_path)

    print('--- SYSHECF ---')
    for csv_path in sorted((eps_dir / 'SYSHECF').glob('SYSHECF-*.csv')):
        tech = csv_path.stem[len('SYSHECF-'):]
        col = f'CF_{tech}'
        if col not in cf.columns:
            print(f'  {csv_path.stem:34s} skipped (no {col} column)')
            continue
        expected = pd.DataFrame(np.nan, index=EPS_TIMESLICE_ORDER, columns=EPS_HOUR_COLUMNS)
        for sl in EPS_TIMESLICE_ORDER:
            if sl in rep_doy:
                expected.loc[sl] = _repday_pick(cf, col, rep_doy[sl])
        check(csv_path.stem, expected, csv_path)

    print(f'--- worst: {worst_name} at {worst:.3e}; failures: {failures} ---')
    return failures


def main():
    dirs = [Path(a) for a in sys.argv[1:]] or [
        ROOT / 'output' / 'UnitedStates_timeslice_results_EPS']
    total = 0
    for d in dirs:
        print(f'=== {d} ===')
        total += verify_eps_dir(d)
    if total:
        print(f'FAIL: {total} table(s) exceed tolerance.')
        sys.exit(1)
    print('PASS: workbook-source CSVs reproduce the exported EPS CSVs.')


if __name__ == '__main__':
    main()
