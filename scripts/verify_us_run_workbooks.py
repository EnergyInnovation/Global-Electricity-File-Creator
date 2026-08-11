"""Verify the US-run SHELF + SYSHECF workbooks (build_us_run_workbooks.py).

Reproduces the workbook formula math in Python from the same source CSVs
(workbook_sources/) and compares every cell against the pipeline's exported
CSV ground truth in output/UnitedStates_timeslice_results_EPS/. Max abs diff
should be float noise (~1e-12).

Run:
    python scripts/verify_us_run_workbooks.py
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.build_us_run_workbooks import (  # noqa: E402
    DEMAND_COLS, EPS_DIR, HOUR_COLS, SHELF_SPECS, SLICES, SPLIT_GROUPS,
    SRC_DIR, SYSHECF_ORDER, TEMPLATE_SHELF_DIR, read_eps_table,
)


def load_sources():
    demand = pd.read_csv(SRC_DIR / 'demand_hourly_source.csv')
    cf = pd.read_csv(SRC_DIR / 'cf_hourly_source.csv')
    clus = pd.read_csv(SRC_DIR / 'clustering.csv')
    rep_doy = dict(zip(clus['slice_name'].dropna(),
                       clus['rep_doy'].dropna().astype(int)))
    return demand, cf, rep_doy


def repday_pick(df: pd.DataFrame, col: str, rep: int) -> np.ndarray:
    """24 hourly values of `col` on day-of-year `rep` (the SUMIFS pick)."""
    day = df[df['day_of_year'] == rep].sort_values('hour_of_day')
    return day[col].to_numpy(dtype=float)


def expected_shelf_table(cat: str, kind: str, arg, demand, rep_doy) -> pd.DataFrame:
    out = pd.DataFrame(0.0, index=SLICES, columns=HOUR_COLS)
    if kind == 'zeros':
        return out
    if kind == 'flat':
        return out + 1.0 / 8760.0
    templates = {}
    if kind == 'split':
        agg_cols, peers = SPLIT_GROUPS[cat]
        for p in peers:
            t = read_eps_table(TEMPLATE_SHELF_DIR / f'SHELF-{p}.csv')
            templates[p] = t.reindex(index=SLICES, columns=HOUR_COLS).fillna(0.0).astype(float)
    for sl in SLICES:
        rep = rep_doy[sl]
        if kind == 'direct':
            vals = repday_pick(demand, arg, rep) / demand[arg].sum()
        elif kind == 'sum':
            c1, c2 = arg
            vals = ((repday_pick(demand, c1, rep) + repday_pick(demand, c2, rep))
                    / (demand[c1].sum() + demand[c2].sum()))
        elif kind == 'split':
            # Sum of each column's own load factor (matches the pipeline's
            # sum over *_load_factor columns).
            agg_cols, peers = SPLIT_GROUPS[cat]
            agg_lf = sum(repday_pick(demand, c, rep) / demand[c].sum()
                         for c in agg_cols)
            peer_sum = sum(templates[p].loc[sl].to_numpy() for p in peers)
            me = templates[cat].loc[sl].to_numpy()
            with np.errstate(divide='ignore', invalid='ignore'):
                weight = np.where(peer_sum == 0, 0.0, me / peer_sum)
            vals = agg_lf * weight
        out.loc[sl] = vals
    return out


def compare(name: str, expected: pd.DataFrame, csv_path: Path) -> float:
    actual = read_eps_table(csv_path)
    actual = actual.reindex(index=SLICES, columns=HOUR_COLS).astype(float)
    # All-zero categories: the pipeline writes blank cells (0/0 = NaN) where
    # the workbook's IFERROR yields 0 — treat both as 0 (equivalent to EPS).
    exp = np.nan_to_num(expected.to_numpy(), nan=0.0)
    act = np.nan_to_num(actual.to_numpy(), nan=0.0)
    return float(np.max(np.abs(exp - act)))


def main():
    demand, cf, rep_doy = load_sources()
    worst = 0.0
    worst_name = ''
    print('--- SHELF ---')
    for cat, kind, arg in SHELF_SPECS:
        if kind == 'days':
            continue
        exp = expected_shelf_table(cat, kind, arg, demand, rep_doy)
        d = compare(cat, exp, EPS_DIR / 'SHELF' / f'SHELF-{cat}.csv')
        flag = '' if d < 1e-9 else '  <-- CHECK'
        print(f'  SHELF-{cat:26s} max abs diff {d:.3e}{flag}')
        if d > worst:
            worst, worst_name = d, f'SHELF-{cat}'

    print('--- SYSHECF (derived techs) ---')
    for tech, kind, arg in SYSHECF_ORDER:
        if kind != 'cf_formula':
            continue
        src_col, mult = arg
        exp = pd.DataFrame(0.0, index=SLICES, columns=HOUR_COLS)
        for sl in SLICES:
            exp.loc[sl] = repday_pick(cf, src_col, rep_doy[sl]) * mult
        d = compare(tech, exp, EPS_DIR / 'SYSHECF' / f'SYSHECF-{tech}.csv')
        flag = '' if d < 1e-9 else '  <-- CHECK'
        print(f'  SYSHECF-{tech:24s} max abs diff {d:.3e}{flag}')
        if d > worst:
            worst, worst_name = d, f'SYSHECF-{tech}'

    print(f'--- worst: {worst_name} at {worst:.3e} ---')
    if worst > 1e-9:
        print('FAIL: differences exceed float noise — investigate before delivering.')
        sys.exit(1)
    print('PASS: workbook math reproduces the pipeline CSVs to float noise.')


if __name__ == '__main__':
    main()
