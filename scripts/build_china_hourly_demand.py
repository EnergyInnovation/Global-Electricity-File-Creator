"""Convert the provincial China hourly-load workbook into a pipeline demand CSV.

Source workbook: one ``<YYYY> load curve`` sheet per year, first column a local
(CST / Asia-Shanghai) hourly timestamp, remaining columns the 31 mainland
provinces in **GWh per hour**. A ``Power coefficients`` sheet documents the
heating/cooling degree-day coefficients behind the reconstruction; it is not
used here.

Output: ``data/manual_downloads/CN_hourly_demand_<first>_<last>.csv`` with
columns ``timestamp`` (naive local CST) and ``demand_mw`` (national sum,
GWh/h x 1000). That file is what the pipeline's ``demand_series_csv`` preset
key reads.

Usage::

    python scripts/build_china_hourly_demand.py --source "<path to xlsx>"

The source workbook lives outside the repo (it is ~40 MB), so the path is a
required argument rather than a hard-coded location.

Staff note: the national series here is a derived aggregate of a third-party
provincial reconstruction. Verify province coverage and annual totals against
CEC / NBS published national consumption before using downstream.
"""

from __future__ import annotations

import argparse
import os
import re
from typing import Dict, List

import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(REPO_ROOT, 'data', 'manual_downloads')

SHEET_RE = re.compile(r'^(\d{4})\s+load\s+curve$', re.IGNORECASE)


def read_year_sheet(xlsx: pd.ExcelFile, sheet: str) -> pd.DataFrame:
    """Return a province-wide hourly frame (GWh) indexed by local timestamp."""
    df = xlsx.parse(sheet, header=0)
    # First column holds the timestamp; its header is the unit string.
    ts_col = df.columns[0]
    stamps = pd.to_datetime(df[ts_col], errors='coerce')
    df = df.drop(columns=[ts_col])
    # Drop fully-empty trailing columns (the 2024 sheet carries two).
    df = df.dropna(axis=1, how='all')
    df = df.apply(pd.to_numeric, errors='coerce')
    df.index = pd.DatetimeIndex(stamps, name='timestamp')
    df = df[df.index.notna()]
    # Drop rows that are entirely blank, then collapse any duplicate stamps.
    df = df.dropna(how='all')
    if df.index.has_duplicates:
        df = df.groupby(level=0).mean()
    return df.sort_index()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True, help='Path to the provincial load-curve xlsx.')
    ap.add_argument('--out-dir', default=DEFAULT_OUT_DIR)
    args = ap.parse_args()

    xlsx = pd.ExcelFile(args.source)
    year_sheets = {
        int(m.group(1)): name
        for name in xlsx.sheet_names
        if (m := SHEET_RE.match(str(name).strip()))
    }
    if not year_sheets:
        raise SystemExit(f'No "<YYYY> load curve" sheets found in {args.source!r}.')

    frames: Dict[int, pd.DataFrame] = {}
    report_rows: List[dict] = []
    for year in sorted(year_sheets):
        prov = read_year_sheet(xlsx, year_sheets[year])
        national = prov.sum(axis=1, min_count=1)
        off_year = int((national.index.year != year).sum())
        expected = 8784 if pd.Timestamp(year=year, month=12, day=31).dayofyear == 366 else 8760
        report_rows.append({
            'year': year,
            'provinces': prov.shape[1],
            'hours': len(national),
            'expected_hours': expected,
            'n_missing_cells': int(prov.isna().sum().sum()),
            'rows_outside_year': off_year,
            'annual_TWh': float(national.sum()) / 1000.0,
            'mean_GW': float(national.mean()),
            'peak_GW': float(national.max()),
        })
        frames[year] = national

    report = pd.DataFrame(report_rows)
    print(report.to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

    combined = pd.concat(frames.values()).sort_index()
    combined = combined[~combined.index.duplicated(keep='first')]
    out = pd.DataFrame({
        'timestamp': combined.index.strftime('%Y-%m-%d %H:%M:%S'),
        # GWh per hour -> MW (average power over the hour)
        'demand_mw': combined.to_numpy() * 1000.0,
    })

    os.makedirs(args.out_dir, exist_ok=True)
    first, last = min(frames), max(frames)
    out_path = os.path.join(args.out_dir, f'CN_hourly_demand_{first}_{last}.csv')
    out.to_csv(out_path, index=False)
    print(f'\nwrote {len(out):,} hourly rows ({first}-{last}) -> {out_path}')

    report_path = os.path.join(args.out_dir, f'CN_hourly_demand_{first}_{last}_coverage.csv')
    report.to_csv(report_path, index=False)
    print(f'wrote coverage report -> {report_path}')


if __name__ == '__main__':
    main()
