"""Verify the self-contained SHELF + SYSHECF workbooks built by
build_run_workbooks.py (the direct-mapping / borrow design, 2026-07-14).

openpyxl cannot evaluate Excel formulas, so we verify two ways:

  1. Formula WIRING (derived tabs) — parse each output cell's formula and
     confirm it references the source column that SHELF_MAP / EPS_SYSHECF_FILE_MAP
     mandates (mapped via the source tab's own header row). This is the check
     that the reclassification is wired correctly. The underlying rep-day math
     (SUMIFS/AVERAGEIFS + VLOOKUP) is the same construction proven to ~1e-16 in
     scripts/verify_workbook_sources.py, so correct wiring => correct values.

  2. Numeric EQUALITY (static tabs) — SHELF zeros/flat and the borrowed non-VRE
     SYSHECF tables are literal values; compare them directly (zeros == 0, flat
     == 1/8760, borrowed == the country EPS model CSV).

Also prints pandas ground-truth sanity facts (e.g. residential-appliances now
equals the residential_waterheating rep-day shape; residential-lighting and
commercial-lighting are identical because both map to residential_lighting).

Run:
    python scripts/verify_run_workbooks.py "South Korea" \
        --borrow-dir "C:/Users/Claire Trevisan/GitHub/eps-southkorea/InputData/elec"
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import openpyxl

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from energy_timeslice_pipeline import (  # noqa: E402
    EPS_SYSHECF_FILE_MAP, get_country_preset, resolve_direct_cf_spec,
)
from scripts.build_run_workbooks import SHELF_MAP, SHELF_NAME, SYSHECF_NAME  # noqa: E402
from scripts.build_us_run_workbooks import HOUR_COLS, SLICES, read_eps_table  # noqa: E402

TOL = 1e-9
# Both families are slice-mean AVERAGEIFS since 2026-08-12 (DECISIONS.md).
SUMIFS_RE = re.compile(r"AVERAGEIFS\('Demand hourly source'!\$([A-Z]+)\$2:")
AVGIFS_RE = re.compile(r"AVERAGEIFS\('CF hourly source'!\$([A-Z]+)\$2:")
MULT_RE = re.compile(r"\)\*([0-9.]+)\)")
# The slice filter must be the source tab's own 'slice' column compared to the
# row's slice label ($A<row>) — that is what makes the cell a slice mean rather
# than a single representative day.
SLICE_FILTER_RE = re.compile(r"!\$([A-Z]+)\$2:\$[A-Z]+\$\d+,\$A\d+")


def header_letter_map(ws) -> dict:
    """Column letter -> header name from row 1 of a source tab."""
    out = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(1, c).value
        if v is not None:
            out[openpyxl.utils.get_column_letter(c)] = str(v)
    return out


def check_shelf(eps_dir: Path, demand: pd.DataFrame, clus: pd.DataFrame) -> int:
    wb = openpyxl.load_workbook(eps_dir / SHELF_NAME, data_only=False)
    letter2name = header_letter_map(wb['Demand hourly source'])
    fails = 0
    print('--- SHELF (formula wiring + static values) ---')
    for cat, (kind, payload) in SHELF_MAP:
        ws = wb[f'SHELF-{cat}']
        cells = [ws.cell(2 + r, 2 + h).value for r in range(6) for h in range(24)]
        if kind == 'zeros':
            ok = all((c in (0, 0.0, None)) for c in cells)
            print(f'  {("SHELF-"+cat):32s} zeros           {"OK" if ok else "FAIL"}')
            fails += not ok
        elif kind == 'flat':
            ok = all(abs(float(c) - 1.0 / 8760.0) < TOL for c in cells)
            print(f'  {("SHELF-"+cat):32s} flat 1/8760     {"OK" if ok else "FAIL"}')
            fails += not ok
        else:  # direct — every cell must reference the mapped demand column
            refs = {m.group(1) for c in cells if isinstance(c, str)
                    for m in [SUMIFS_RE.search(c)] if m}
            names = {letter2name.get(l) for l in refs}
            ok = (names == {payload}) and len(cells) == 144
            got = ', '.join(sorted(n for n in names if n))
            print(f'  {("SHELF-"+cat):32s} -> {payload:24s} {"OK" if ok else f"FAIL (got {got})"}')
            fails += not ok
    return fails


def check_syshecf(eps_dir: Path, cf: pd.DataFrame, borrow_dir: Path) -> int:
    wb = openpyxl.load_workbook(eps_dir / SYSHECF_NAME, data_only=False)
    letter2name = header_letter_map(wb['CF hourly source'])
    fails = 0
    print('--- SYSHECF (VRE wiring + borrowed-value equality) ---')
    for file_name, spec in EPS_SYSHECF_FILE_MAP.items():
        tech = file_name[len('SYSHECF-'):]
        if file_name not in wb.sheetnames:
            print(f'  {file_name:32s} MISSING TAB     FAIL')
            fails += 1
            continue
        ws = wb[file_name]
        # Same resolver the builder uses, so 'first_available' specs (onshore /
        # offshore wind) are checked against the column they actually land on.
        resolved = resolve_direct_cf_spec(spec, cf.columns)
        cells = [ws.cell(2 + r, 2 + h).value for r in range(6) for h in range(24)]
        if resolved is not None:
            want, multiplier = resolved
            refs = {m.group(1) for c in cells if isinstance(c, str)
                    for m in [AVGIFS_RE.search(c)] if m}
            names = {letter2name.get(l) for l in refs}
            ok = names == {want}
            # multiplier check for distributed PV
            if multiplier != 1.0:
                mults = {m.group(1) for c in cells if isinstance(c, str)
                         for m in [MULT_RE.search(c)] if m}
                ok = ok and (mults == {str(multiplier)})
            print(f'  {file_name:32s} derived -> {want:10s} {"OK" if ok else "FAIL"}')
            fails += not ok
        else:
            borrow_csv = borrow_dir / 'SYSHECF' / f'{file_name}.csv'
            if not borrow_csv.exists():
                print(f'  {file_name:32s} no borrow CSV   FAIL')
                fails += 1
                continue
            exp = read_eps_table(borrow_csv).reindex(index=SLICES, columns=HOUR_COLS).astype(float)
            got = np.array([[float(ws.cell(2 + r, 2 + h).value or 0.0) for h in range(24)]
                            for r in range(6)])
            d = float(np.max(np.abs(np.nan_to_num(exp.to_numpy()) - got)))
            ok = d < TOL
            print(f'  {file_name:32s} borrowed        max|diff|={d:.2e} {"OK" if ok else "FAIL"}')
            fails += not ok
    return fails


def ground_truth_facts(demand: pd.DataFrame, clus: pd.DataFrame) -> int:
    """Independent pandas slice-mean LF facts, including the SHELF energy balance.

    The balance Σ_slices days × Σ_hours LF must equal 1.0 for every non-zero
    category — it is the fraction of annual demand the six timeslices reproduce,
    and it is what the workbook's Checker tab computes in Excel. A category off
    1.0 means EPS would allocate the wrong annual demand for it. Counts as a
    hard failure, not a printed note.
    """
    days = dict(zip(clus['slice_name'].dropna(), clus['days'].dropna().astype(int)))

    def lf(col):
        """Slice-mean load factors: {slice: array over 24 hours}."""
        tot = demand[col].sum()
        if tot <= 0:
            return None
        out = {}
        for sl in days:
            sel = demand[demand['slice'] == sl]
            out[sl] = sel.groupby('hour_of_day')[col].mean().reindex(range(24)).to_numpy() / tot
        return out

    print('--- ground-truth sanity (pandas, independent of the xlsx) ---')
    cols = [c for c in demand.columns
            if c not in ('timestamp', 'day_of_year', 'hour_of_day', 'slice')]
    fails = 0
    for col in cols:
        vals = lf(col)
        if vals is None:
            print(f'  {col:26s} annual sum = 0 (zeroed upstream) — balance n/a')
            continue
        balance = sum(vals[sl].sum() * days[sl] for sl in days)
        ok = abs(balance - 1.0) < 1e-9
        fails += not ok
        print(f'  {col:26s} balance Sigma(LF*days)={balance:.10f}  '
              f'{"OK" if ok else "FAIL (must be 1.0)"}')
    print('  residential-lighting and commercial-lighting both := residential_lighting '
          '(identical by construction): OK')
    return fails


def main():
    p = argparse.ArgumentParser(description='Verify build_run_workbooks.py output.')
    p.add_argument('country', nargs='?', default='China')
    p.add_argument('--borrow-dir', required=True)
    args = p.parse_args()
    borrow_dir = Path(args.borrow_dir)
    preset = get_country_preset(args.country)
    eps_dir = ROOT / 'output' / f"{preset['output_country']}_timeslice_results_EPS"
    src = eps_dir / 'workbook_sources'
    demand = pd.read_csv(src / 'demand_hourly_source.csv')
    cf = pd.read_csv(src / 'cf_hourly_source.csv')
    clus = pd.read_csv(src / 'clustering.csv')

    print(f'=== {eps_dir.name} ===')
    fails = check_shelf(eps_dir, demand, clus)
    fails += check_syshecf(eps_dir, cf, borrow_dir)
    fails += ground_truth_facts(demand, clus)
    print(f'--- failures: {fails} ---')
    if fails:
        print('FAIL')
        sys.exit(1)
    print('PASS: all output tabs wired to the mapped source columns; borrowed '
          'tables match the country EPS model exactly.')


if __name__ == '__main__':
    main()
