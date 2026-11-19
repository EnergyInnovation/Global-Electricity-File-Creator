"""Independent check of an exported EPS 5.0 SHELF folder. Run it after recalc_export.py.

Nothing here reads the workbook's calculation cells. Each number is worked out again in Python from the raw
inputs and compared with the exported CSV:

  1. Whole-industry shapes (SHELF-indstcat-*, 25 industries x 6 timeslices x 24 hours): from the SIELS zip
     itself when it is available (otherwise the saved national series), the utilities' daily agricultural
     profiles and the EIA monthly sales pasted on the hand-built tabs, the day-to-timeslice list and the
     weekend settings.
  2. Buildings, transport, old all-industry, district heat / hydrogen, geoengineering and data-center tabs:
     from the saved national series, the Cambium file and the day-to-timeslice list.
  3. Every exported row adds up to 1 over the year (hourly shares x days per timeslice), or is all zeros.
  4. The per-process tabs (SHELF-indstproc-*, SHELF-indstCCS) are not recomputed, because they come from
     formulas on the hand-built tabs; they are covered by check 3 only.
  5. The industries are in the same order in every SHELF-indstcat file and in ICwIwLF.csv.
  6. The workbook's own check cells.

Usage:
    python scripts/shelf_v5/verify_v5.py <out folder> [--align-weekdays] [--siels-tennessee eastern|central]
        [--buildings typical|amy2012] [--building-clock pipeline|eastern] [--television omit|other]
        [--building-delay-hours H]
<out folder> is the --out of build_shelf_workbook.py (default output/us_shelf_5.0/). Pass the same
--align-weekdays / --siels-tennessee / --buildings / --building-clock / --television / --building-delay-hours
options the workbook was built with (they select which saved national series the buildings tabs are checked
against). With --buildings amy2012, television is counted unless --television omit is given, as in the build.
Exit code 0 when every check passes.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import io
import statistics
import sys
import zipfile
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
from shelf_v5 import buildings as bld, efs_clock, names, paths                 # noqa: E402
from shelf_v5.industry import ASSIGN, CHECKROW0, WEEKEND, label     # noqa: E402
from shelf_v5.siels import ALIAS, FILES, NAMES as METERED, read_cache, CACHE_NAME   # noqa: E402

TOL = 2e-9        # the CSVs are printed to 10 significant figures
LABELS, TAGS = names.V5_LABELS, names.V5_TAGS
WORKBOOK_NAME = 'Seasonal Hourly Equipment Load Factors by End Use.xlsx'


def tz_offsets() -> dict[str, int]:
    """The state time-zone table, read from the build script's text so this check does not import it."""
    import ast
    import re
    src = (HERE.parents[1] / 'build_shelf_workbook.py').read_text(encoding='utf-8')
    return ast.literal_eval(re.search(r'STATE_TZ_OFFSET_TO_ET = (\{.*?\n\})', src, re.S).group(1))


def siels_national(zip_path: Path, offsets: dict[str, int]) -> dict[str, np.ndarray]:
    """National series from the zip, written independently of siels.py (pandas, shift by np.roll)."""
    out = {}
    with zipfile.ZipFile(zip_path) as zf:
        members = {Path(n).name: n for n in zf.namelist() if not n.startswith('__MACOSX')}
        for name, fn in FILES:
            df = pd.read_csv(io.BytesIO(zf.read(members[fn])), index_col=0)
            assert len(df) == 8760, (fn, len(df))
            tot = np.zeros(8760)
            for col in df.columns:
                tot += np.roll(np.nan_to_num(df[col].to_numpy(dtype=float)), offsets[ALIAS.get(col, col)])
            out[name] = tot
    return out


def read_csv_table(p: Path) -> tuple[list[str], np.ndarray]:
    rows = list(csv.reader(open(p, newline='')))
    return [r[0] for r in rows[1:]], np.array([[float(x) for x in r[1:]] for r in rows[1:]])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('out')
    ap.add_argument('--align-weekdays', action='store_true')
    ap.add_argument('--siels-tennessee', choices=['eastern', 'central'], default='eastern')
    ap.add_argument('--siels-zip')
    ap.add_argument('--buildings', choices=list(bld.SOURCES), default='amy2012')
    ap.add_argument('--building-clock', choices=list(bld.CLOCKS), default='eastern')
    ap.add_argument('--television', choices=list(bld.TELEVISION), default=None)
    ap.add_argument('--building-delay-hours', type=float, default=0.0)
    ap.add_argument('--efs-clock', choices=list(efs_clock.CLOCKS), default='eastern')
    a = ap.parse_args()
    if a.buildings == 'amy2012' and a.align_weekdays:
        ap.error('--align-weekdays does not apply to --buildings amy2012')
    a.television = bld.resolve_television(a.buildings, a.television)
    folder = Path(a.out) / 'elec' / 'SHELF'
    ok = True

    def report(name: str, passed: bool, detail: str) -> None:
        nonlocal ok
        ok = ok and passed
        print(f"{'PASS' if passed else 'FAIL'}  {name}: {detail}")

    wb = openpyxl.load_workbook(folder / WORKBOOK_NAME, read_only=True, data_only=True)

    # ---- inputs: clustering list and days per timeslice (typed-in cells on the Clustering tab)
    slice_of = {int(r[0]): r[1] for r in wb['Clustering'].iter_rows(min_row=3, max_row=367, min_col=4, max_col=5,
                                                                   values_only=True)}
    assert sorted(slice_of) == list(range(1, 366))
    slice_arr = np.array([slice_of[d] for d in range(1, 366)])
    days = {sl: int((slice_arr == sl).sum()) for sl in LABELS}
    got_days = dict(zip(*[(lab, vals[:, 0].astype(int)) for lab, vals in
                          [read_csv_table(folder / 'SHELF-days-per-timeslice.csv')]][0]))
    report('days per timeslice', {k: int(v) for k, v in got_days.items()} == days, str(days))
    cal = [dt.date(2012, 1, 1) + dt.timedelta(days=k) for k in range(365)]      # the clustering calendar

    # ---- 1. whole-industry shapes
    zip_path = paths.lookup('siels_zip', a.siels_zip)
    if zip_path.exists():
        off = tz_offsets()
        if a.siels_tennessee == 'eastern':
            off['TN'] = 0
        ser = siels_national(zip_path, off)
        src = f'SIELS zip, Tennessee on {a.siels_tennessee} time'
    else:
        ser = {n: np.array(v) for n, v in read_cache(paths.lookup('cache_dir') / CACHE_NAME)[1].items()}
        src = 'saved national series (zip not found)'
    od = wb['Other Data & Calcs']
    dates = list(next(od.iter_rows(min_row=597, max_row=597, min_col=4, max_col=39, values_only=True)))
    sales = list(next(od.iter_rows(min_row=601, max_row=601, min_col=4, max_col=39, values_only=True)))
    ag_share = next(od.iter_rows(min_row=616, max_row=616, min_col=25, max_col=25, values_only=True))[0]
    agws = wb['Ag']
    season = {12: 'winter', 1: 'winter', 2: 'winter', 3: 'spring', 4: 'spring', 5: 'spring',
              6: 'summer', 7: 'summer', 8: 'summer', 9: 'fall', 10: 'fall', 11: 'fall'}

    def pdate(x):
        if isinstance(x, dt.datetime):
            return x.date()
        s = str(x).strip()
        for f in ('%m/%d/%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return dt.datetime.strptime(s, f).date()
            except ValueError:
                pass
        raise ValueError(s)

    # utilities' daily agricultural profiles (hour columns are hour-ending 1..24 = hours 0..23)
    util = {}
    for name, r0, r1 in (('SCE', 54, 418), ('PGE', 427, 791)):
        util[name] = {pdate(r[1]): [float(x) for x in r[2:26]]
                      for r in agws.iter_rows(min_row=r0, max_row=r1, max_col=26, values_only=True)}
    sd: dict = {}
    for r in agws.iter_rows(min_row=798, max_row=9557, max_col=4, values_only=True):
        sd.setdefault(pdate(r[0]), [0.0] * 24)[int(r[2]) - 1] = float(r[3])
    util['SDGE'] = sd
    kwh = {r[0]: float(r[1]) for r in agws.iter_rows(min_row=31, max_row=33, min_col=10, max_col=11, values_only=True)}
    tot_kwh = sum(kwh.values())
    wt = {'PGE': kwh['PG&E'] / tot_kwh, 'SCE': kwh['SCE'] / tot_kwh, 'SDGE': kwh['SDGE'] / tot_kwh}
    ag: dict = {}                             # (month, day type) -> 24 values, share of annual use per hour
    for n, dd in util.items():
        tot = sum(sum(v) for v in dd.values())
        for m in range(1, 13):
            for t in ('weekday', 'weekend'):
                sel = [v for d, v in dd.items() if d.month == m and (d.weekday() >= 5) == (t == 'weekend')]
                cur = ag.setdefault((m, t), [0.0] * 24)
                for h in range(24):
                    cur[h] += wt[n] * (sum(v[h] for v in sel) / len(sel)) / tot
    # agriculture's seasonal level as the Ag tab works it out (season mean / all-season mean)
    seas_rows = {r[1]: [float(x) for x in r[2:26]] for r in agws.iter_rows(min_row=6, max_row=9, max_col=26, values_only=True)}
    allmean = sum(sum(v) for v in seas_rows.values()) / 96
    ag_rel = {s: (sum(v) / 24) / allmean for s, v in seas_rows.items()}

    # typical weekday and weekend day on the source calendar (2018), weekend scaled to its setting
    src_weekend = [(dt.date(2018, 1, 1) + dt.timedelta(days=k)).weekday() >= 5 for k in range(365)]
    typ = {}
    for n in METERED:
        v = ser[n].reshape(365, 24)
        for dtp in ('weekday', 'weekend'):
            pick = [k for k in range(365) if src_weekend[k] == (dtp == 'weekend')]
            typ[n, dtp] = [statistics.median(float(v[k, h]) for k in pick) for h in range(24)]
        k = WEEKEND[n] * sum(typ[n, 'weekday']) / sum(typ[n, 'weekend'])
        typ[n, 'weekend'] = [x * k for x in typ[n, 'weekend']]

    # month level for non-farm industry
    def as_date(x):
        return x.date() if isinstance(x, dt.datetime) else (dt.date(1899, 12, 30) + dt.timedelta(days=int(x)))
    perday: dict = {}
    for d, s in zip(dates, sales):
        d = as_date(d)
        nd = (dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1) - d).days
        perday.setdefault(d.month, []).append(s / nd)
    perday = {m: sum(v) / len(v) for m, v in perday.items()}
    ndays = {m: sum(1 for d in cal if d.month == m) for m in range(1, 13)}
    mean = sum(perday[m] * ndays[m] for m in ndays) / 365
    raw = {m: (perday[m] / mean - ag_share * ag_rel[season[m]]) / (1 - ag_share) for m in ndays}
    rmean = sum(raw[m] * ndays[m] for m in ndays) / 365
    level = {m: raw[m] / rmean for m in ndays}

    def shelf_for(shape):
        year = np.zeros((365, 24))
        for k, d in enumerate(cal):
            t = 'weekend' if d.weekday() >= 5 else 'weekday'
            year[k] = ag[d.month, t] if shape == 'agriculture' else np.array(typ[shape, t]) * level[d.month]
        return {sl: year[slice_arr == sl].mean(0) / year.sum() for sl in LABELS}

    cache, worst, n = {}, 0.0, 0
    order_ok = True
    want_labels = [label(c[0]) for c in ASSIGN]
    for sl, tag in zip(LABELS, TAGS):
        labs, got = read_csv_table(folder / f'SHELF-indstcat-{tag}.csv')
        order_ok = order_ok and labs == want_labels
        for (cat, shape, *_), row in zip(ASSIGN, got):
            if shape not in cache:
                cache[shape] = shelf_for(shape)
            worst = max(worst, float(np.abs(row / cache[shape][sl] - 1).max()))
            n += 24
    report('whole-industry shapes recomputed', worst < TOL,
           f'{n} values from the {src}; largest relative difference {worst:.1e}')

    # ---- 2. buildings, transport, system-load and data-center tabs
    cdir = paths.lookup('cache_dir')
    res = pd.read_csv(cdir / bld.cache_name('resstock', a.buildings, a.building_clock, a.television), index_col=0)
    com = pd.read_csv(cdir / bld.cache_name('comstock', a.buildings, a.building_clock), index_col=0)
    efs = pd.read_csv(cdir / 'efs_national_hourly.csv', index_col=0)
    if a.efs_clock == 'eastern':
        efs = efs_clock.to_eastern(efs)
    crow = list(csv.reader(open(paths.lookup('cambium_hourly'), newline='')))
    j = crow[5].index('enduse_load')
    enduse = np.array([float(r[j]) for r in crow[6:8766]])

    def averaged(values, shift_days=0):
        v = np.asarray(values, dtype=float)[:8760].reshape(365, 24)
        day_slice = np.roll(slice_arr, -shift_days) if shift_days else slice_arr   # source day d -> clustering day d+shift
        return np.array([v[day_slice == sl].mean(0) / v.sum() for sl in LABELS])

    def delayed(values, tau):
        """Worked out here on its own: blend of the series moved later by floor(tau) and floor(tau)+1 hours, year wrapping."""
        v = np.asarray(values, dtype=float)[:8760]
        k = int(np.floor(tau)); f = tau - k
        return v if not tau else (1 - f) * np.roll(v, k) + f * np.roll(v, k + 1)

    bshift = 1 if a.align_weekdays else 0
    expect = {}
    for c in res.columns:
        expect[c] = averaged(delayed(res[c].values, a.building_delay_hours), bshift)
    for c in com.columns:
        expect[c] = averaged(delayed(com[c].values, a.building_delay_hours), bshift)
    for c in ('LDVs', 'HDVs', 'rail'):
        expect[c] = averaged(efs[c].values)
    expect['district-heat-hydrogen'] = expect['geoeng'] = averaged(enduse)
    expect['datacenters-other'] = expect['datacenters-cooling'] = np.full((6, 24), 1 / 8760)
    worst, n = 0.0, 0
    for c, want in expect.items():
        labs, got = read_csv_table(folder / f'SHELF-{c}.csv')
        assert labs == LABELS, (c, labs)
        worst = max(worst, float(np.abs(got / want - 1).max()))
        n += got.size
    report('buildings, transport, system-load and data-center tabs recomputed', worst < TOL,
           f'{n} values in {len(expect)} files; largest relative difference {worst:.1e}'
           + ('; buildings shifted one day (--align-weekdays)' if bshift else '')
           + (f'; buildings: {a.buildings} source, {a.building_clock} clock, television {a.television}'
              + (f', {a.building_delay_hours:g} h delay' if a.building_delay_hours else '')
              if (a.buildings, a.building_clock, a.building_delay_hours) != ('typical', 'pipeline', 0.0) else ''))

    # ---- 3. every exported row adds up to 1 over the year, or is all zeros
    dvec = np.array([days[sl] for sl in LABELS])
    worst, nrows, zeros, bad = 0.0, 0, [], []
    for p in sorted(folder.glob('SHELF-*.csv')):
        tab = p.stem
        if tab == 'SHELF-days-per-timeslice':
            continue
        labs, got = read_csv_table(p)
        if tab.startswith('SHELF-indstproc-') or tab.startswith('SHELF-indstcat-'):
            continue                                    # one file per timeslice: summed across files below
        if not got.any():
            zeros.append(tab.replace('SHELF-', ''))
            continue
        s = float((got.sum(1) * dvec).sum())
        worst = max(worst, abs(s - 1)); nrows += 1
        if abs(s - 1) > 1e-8:
            bad.append((tab, s))
    for fam in ('indstproc', 'indstcat'):
        tabs = [read_csv_table(folder / f'SHELF-{fam}-{t}.csv') for t in TAGS]
        tot = sum(tb[1].sum(1) * days[sl] for tb, sl in zip(tabs, LABELS))
        worst = max(worst, float(np.abs(tot - 1).max())); nrows += len(tot)
        bad += [(f'{fam}:{lab}', float(s)) for lab, s in zip(tabs[0][0], tot) if abs(s - 1) > 1e-8]
    report('annual sums', not bad, f'{nrows} shapes add to 1 (largest distance {worst:.1e}); all-zero by design: '
           + ', '.join(zeros) + (f'; OFF: {bad}' if bad else ''))

    # ---- 5. industry order
    ic = [r[0] for r in csv.reader(open(Path(a.out) / 'ctrl-settings' / 'ICwIwLF' / 'ICwIwLF.csv', newline=''))][1:]
    report('industry order', order_ok and ic == want_labels,
           f'{len(ic)} industries, same order in ICwIwLF.csv and the six SHELF-indstcat files')

    # ---- 6. the workbook's own check cells
    ck = wb['Industry day shapes']
    cells = [(r[0], r[1], r[2]) for r in ck.iter_rows(min_row=CHECKROW0, max_row=CHECKROW0 + 9, max_col=3, values_only=True) if r[0]]
    flagged = sum(1 for c in cells[:-1] if c[2] != 0)
    report('workbook check cells', flagged == 0 and cells[-1][1] == 0,
           f'shapes flagged {flagged} of {len(cells) - 1}; industries with an unknown shape {cells[-1][1]}')
    blend = [r for r in wb['Industry blend'].iter_rows(min_row=4, max_row=17, min_col=31, max_col=33, values_only=True)]
    offb = [r[0] for r in blend if isinstance(r[2], (int, float)) and abs(r[2] - 1) > 1e-9]
    report('per-process normalisation cells', not offb, f'{sum(isinstance(r[2], (int, float)) for r in blend)} row groups add to 1'
           + (f'; OFF: {offb}' if offb else ''))

    print('ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
