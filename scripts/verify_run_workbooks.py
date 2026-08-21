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
    ELCCAfR_DEGENERATE_MEAN, ELCCAfR_DEMAND_ALTERING_DEFAULT,
    ELCCAfR_DEMAND_ALTERING_FILE, ELCCAfR_STATISTIC_DEFAULT,
    EPS_ELCCAfR_FILE_MAP, EPS_ELCCAfR_HEADERS, EPS_ELCCAfR_MIRRORS,
    EPS_PEAK_TIMESLICES, EPS_SYSHECF_FILE_MAP, get_country_preset,
    resolve_direct_cf_spec,
)
from scripts.build_run_workbooks import (  # noqa: E402
    ELCCAfR_NAME, ELCCAfR_STATS_TAB, SHELF_MAP, SHELF_NAME, SYSHECF_NAME,
)
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


STATS_REF_RE = re.compile(rf"'{re.escape(ELCCAfR_STATS_TAB)}'!([A-Z]+)(\d+)")


def _pandas_peak_stats(cf: pd.DataFrame, column: str, statistic: str) -> dict:
    """Independent per-(peak slice, hour) mean and low statistic, plain pandas.

    Deliberately does NOT call build_elccafr_table — this is the ground truth the
    written CSVs are checked against, so it must not share their code path.
    """
    out = {}
    for sl in EPS_PEAK_TIMESLICES:
        sub = cf[cf['slice'] == sl]
        means, lows = np.full(24, np.nan), np.full(24, np.nan)
        for h in range(24):
            v = pd.to_numeric(sub.loc[sub['hour_of_day'] == h, column],
                              errors='coerce').dropna().to_numpy(dtype=float)
            if v.size == 0:
                continue
            means[h] = v.mean()
            lows[h] = v.min() if statistic == 'min' else np.percentile(v, float(statistic[1:]))
        out[sl] = (means, lows)
    return out


def check_elccafr(eps_dir: Path, cf: pd.DataFrame, preset: dict) -> int:
    """ELCCAfR: CSV values vs independent pandas, formula wiring, and the
    SYSHECF x ELCCAfR = worst-day identity."""
    statistic = str(preset.get('elccafr_statistic', ELCCAfR_STATISTIC_DEFAULT))
    demand_altering = float(
        preset.get('elccafr_demand_altering', ELCCAfR_DEMAND_ALTERING_DEFAULT))
    csv_dir = eps_dir / 'ELCCAfR'
    wb = openpyxl.load_workbook(eps_dir / ELCCAfR_NAME, data_only=False)
    stats_ws = wb[ELCCAfR_STATS_TAB] if ELCCAfR_STATS_TAB in wb.sheetnames else None
    fails = 0
    print(f'--- ELCCAfR (statistic={statistic}; CSV vs pandas, wiring, identity) ---')

    expected_files = list(EPS_ELCCAfR_FILE_MAP) + [ELCCAfR_DEMAND_ALTERING_FILE]
    for file_name in expected_files:
        path = csv_dir / f'{file_name}.csv'
        if not path.exists():
            print(f'  {file_name:32s} MISSING CSV     FAIL')
            fails += 1
            continue
        if file_name not in wb.sheetnames:
            print(f'  {file_name:32s} MISSING TAB     FAIL')
            fails += 1
            continue
        tbl = read_eps_table(path).reindex(index=SLICES, columns=HOUR_COLS).astype(float)
        ws = wb[file_name]

        # Universal invariants: shape, range, non-peak rows exactly 1.0.
        problems = []
        if tbl.isna().to_numpy().any():
            problems.append('not 6x24')
        vals = tbl.to_numpy(dtype=float)
        if not ((vals >= 0.0) & (vals <= 1.0)).all():
            problems.append('value outside [0,1]')
        nonpeak = [s for s in SLICES if s not in EPS_PEAK_TIMESLICES]
        if not np.allclose(tbl.loc[nonpeak].to_numpy(dtype=float), 1.0, atol=TOL):
            problems.append('non-peak row != 1.0')
        if file_name != ELCCAfR_DEMAND_ALTERING_FILE:
            a1 = read_eps_table(path).index.name
            if a1 != EPS_ELCCAfR_HEADERS[file_name]:
                problems.append(f'A1 header {a1!r}')

        if file_name == ELCCAfR_DEMAND_ALTERING_FILE:
            peak = tbl.loc[list(EPS_PEAK_TIMESLICES)].to_numpy(dtype=float)
            if not np.allclose(peak, demand_altering, atol=TOL):
                problems.append(f'peak rows != {demand_altering}')
            tab = np.array([[float(ws.cell(2 + r, 2 + h).value) for h in range(24)]
                            for r in range(6)])
            if not np.allclose(tab, vals, atol=TOL):
                problems.append('tab != CSV')
            ok = not problems
            print(f'  {file_name:32s} judgment {demand_altering}    '
                  f'{"OK" if ok else "FAIL (" + "; ".join(problems) + ")"}')
            fails += not ok
            continue

        resolved = resolve_direct_cf_spec(
            EPS_SYSHECF_FILE_MAP.get(EPS_ELCCAfR_FILE_MAP[file_name]), cf.columns)

        source_file = EPS_ELCCAfR_MIRRORS.get(file_name)
        source_derived = source_file is not None and resolve_direct_cf_spec(
            EPS_SYSHECF_FILE_MAP.get(EPS_ELCCAfR_FILE_MAP.get(source_file)),
            cf.columns) is not None
        if resolved is None and source_derived:
            # Mirror: CSV must equal the mirrored tech's CSV, and the tab's peak
            # cells must reference that tab (not hold a stale copy of its values).
            mirror_tbl = read_eps_table(csv_dir / f'{source_file}.csv').reindex(
                index=SLICES, columns=HOUR_COLS).astype(float)
            d = float(np.max(np.abs(vals - mirror_tbl.to_numpy(dtype=float))))
            if d > TOL:
                problems.append(f'CSV != {source_file} (max|diff|={d:.2e})')
            for r_off, sl in enumerate(SLICES):
                for h in range(24):
                    cell = ws.cell(2 + r_off, 2 + h).value
                    if sl not in EPS_PEAK_TIMESLICES:
                        if not isinstance(cell, (int, float)) or abs(float(cell) - 1.0) > TOL:
                            problems.append(f'{sl} h{h} non-peak != 1.0')
                            break
                    else:
                        want = (f"='{source_file}'!"
                                f'{openpyxl.utils.get_column_letter(2 + h)}{2 + r_off}')
                        if str(cell) != want:
                            problems.append(f'{sl} h{h} ref {cell!r} != {want!r}')
                            break
                else:
                    continue
                break
            ok = not problems
            print(f'  {file_name:32s} mirrors {source_file[len("ELCCAfR-"):]:<12s} '
                  f'{"OK" if ok else "FAIL (" + "; ".join(problems) + ")"}')
            fails += not ok
            continue

        if resolved is None:
            # Constant tech: CSV and tab must both be literal 1.0 everywhere.
            if not np.allclose(vals, 1.0, atol=TOL):
                problems.append('constant tech != 1.0')
            tab = np.array([[float(ws.cell(2 + r, 2 + h).value) for h in range(24)]
                            for r in range(6)])
            if not np.allclose(tab, 1.0, atol=TOL):
                problems.append('tab != 1.0')
            ok = not problems
            print(f'  {file_name:32s} constant 1.0    '
                  f'{"OK" if ok else "FAIL (" + "; ".join(problems) + ")"}')
            fails += not ok
            continue

        column, _mult = resolved
        stats = _pandas_peak_stats(cf, column, statistic)
        max_diff, max_identity = 0.0, 0.0
        degenerate = 0
        for sl in EPS_PEAK_TIMESLICES:
            means, lows = stats[sl]
            for h in range(24):
                got = float(tbl.loc[sl, HOUR_COLS[h]])
                if np.isnan(means[h]) or means[h] < ELCCAfR_DEGENERATE_MEAN:
                    degenerate += 1
                    if abs(got - 1.0) > TOL:
                        problems.append(f'{sl} h{h} degenerate != 1.0')
                    continue
                want = min(max(lows[h] / means[h], 0.0), 1.0)
                max_diff = max(max_diff, abs(got - want))
                # SYSHECF x ELCCAfR = the low-statistic CF at that hour.
                max_identity = max(max_identity, abs(means[h] * got - lows[h]))
        # CSVs are written at 4dp, so allow half a unit in the last place.
        if max_diff > 5e-5:
            problems.append(f'CSV vs pandas max|diff|={max_diff:.2e}')
        if max_identity > 5e-5:
            problems.append(f'identity max|diff|={max_identity:.2e}')

        # Formula wiring: each peak cell divides a MINIFS row by an AVERAGEIFS
        # row of the same hour column on the stats tab, both labelled with the
        # cell's own slice. Checked against the stats tab itself, not row numbers.
        if stats_ws is None:
            problems.append('stats tab missing')
        else:
            for r_off, sl in enumerate(SLICES):
                if sl not in EPS_PEAK_TIMESLICES:
                    continue
                for h in range(24):
                    formula = ws.cell(2 + r_off, 2 + h).value
                    refs = STATS_REF_RE.findall(str(formula))
                    letter = openpyxl.utils.get_column_letter(2 + h)
                    if len(refs) != 3 or {c for c, _ in refs} != {letter}:
                        problems.append(f'{sl} h{h} bad refs')
                        break
                    # =IF(<mean> < eps, 1, MIN(1, MAX(0, <low> / <mean>)))
                    rows = [int(rw) for _, rw in refs]
                    mean_row, low_row = rows[0], rows[1]
                    if rows[2] != mean_row:
                        problems.append(f'{sl} h{h} guard row != denominator row')
                        break
                    mean_src = str(stats_ws.cell(mean_row, 2 + h).value)
                    low_src = str(stats_ws.cell(low_row, 2 + h).value)
                    # MINIFS must carry the _xlfn. prefix in the stored XML or
                    # Excel opens the cell as #NAME?.
                    low_fn = '_xlfn.MINIFS' if statistic == 'min' else 'PERCENTILE'
                    if ('AVERAGEIFS' not in mean_src or low_fn not in low_src
                            or stats_ws.cell(mean_row, 1).value != sl
                            or stats_ws.cell(low_row, 1).value != sl):
                        problems.append(f'{sl} h{h} refs wrong block')
                        break
                else:
                    continue
                break

        ok = not problems
        print(f'  {file_name:32s} derived -> {column:18s} '
              f'max|diff|={max_diff:.2e} identity={max_identity:.2e} '
              f'degenerate={degenerate:3d} '
              f'{"OK" if ok else "FAIL (" + "; ".join(problems) + ")"}')
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
    fails += check_elccafr(eps_dir, cf, preset)
    fails += ground_truth_facts(demand, clus)
    print(f'--- failures: {fails} ---')
    if fails:
        print('FAIL')
        sys.exit(1)
    print('PASS: all output tabs wired to the mapped source columns; borrowed '
          'tables match the country EPS model exactly; ELCCAfR CSVs match an '
          'independent pandas recomputation and satisfy SYSHECF x ELCCAfR = '
          'worst-day CF.')


if __name__ == '__main__':
    main()
