"""One-time helper: save the inputs the 5.0 build cannot regenerate from raw files on every machine.

Reads an existing EPS 5.0 SHELF workbook (the one committed to eps-us) and writes, inside this repository:

  data/us_industry_handbuilt/handbuilt_tabs.xlsx
        the four hand-built tabs (Ag, Other Data & Calcs, EPRI load shapes, NREL load shapes), unchanged:
        pasted source data and hand-written formulas that no script produces
  data/us_industry_handbuilt/SOURCE.txt
        where the copy was taken from
  data/national_aggregated/efs_national_hourly.csv
        the EFS national series (industry, LDVs, HDVs, rail), so the build runs without the 100+ MB EFS zip
  data/cambium24_midcase_national/k6_slice_assignment_repday.csv
        the day-to-timeslice list, so the build runs without scikit-learn

Usage:
    python scripts/shelf_v5/extract_seed.py "<path>/Seasonal Hourly Equipment Load Factors by End Use.xlsx" \
        --source-note "eps-us develop d2d418df"
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shelf_v5 import names, paths          # noqa: E402

HANDBUILT = ['Other Data & Calcs', 'NREL load shapes', 'EPRI load shapes', 'Ag']


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('workbook')
    ap.add_argument('--source-note', default='', help='where the workbook came from, e.g. "eps-us develop d2d418df"')
    a = ap.parse_args()

    print('loading', a.workbook)
    wb = openpyxl.load_workbook(a.workbook)
    missing = [n for n in HANDBUILT + ['EFS source', 'Clustering'] if n not in wb.sheetnames]
    if missing:
        sys.exit(f'workbook has no tab(s) {missing}')

    # EFS national series
    ws = wb['EFS source']
    hdr = [c.value for c in ws[1]][:5]
    assert hdr == ['timestamp', 'industry', 'LDVs', 'HDVs', 'rail'], hdr
    cache = paths.lookup('cache_dir') / 'efs_national_hourly.csv'
    with open(cache, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['ts'] + hdr[1:])
        n = 0
        for r in ws.iter_rows(min_row=2, max_row=8761, max_col=5, values_only=True):
            w.writerow([r[0] + ':00'] + [repr(float(x)) for x in r[1:]])
            n += 1
    assert n == 8760
    print('wrote', cache)

    # day -> timeslice list, in the clustering code's own timeslice names
    back = dict(zip(names.V5_LABELS, names.CANONICAL))
    ws = wb['Clustering']
    out = paths.lookup('clustering_list')
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['day_of_year', 'slice'])
        for doy, sl in ws.iter_rows(min_row=3, max_row=367, min_col=4, max_col=5, values_only=True):
            w.writerow([int(doy), back.get(sl, sl)])
    print('wrote', out)

    # hand-built tabs: drop every other sheet and save what is left
    for n in list(wb.sheetnames):
        if n not in HANDBUILT:
            del wb[n]
    wb._sheets = [wb[n] for n in HANDBUILT]
    seed = paths.lookup('handbuilt_seed')
    seed.parent.mkdir(parents=True, exist_ok=True)
    wb.save(seed)
    (seed.parent / 'SOURCE.txt').write_text(
        f'handbuilt_tabs.xlsx holds the tabs {", ".join(HANDBUILT)} copied unchanged from\n'
        f'{Path(a.workbook).name}\n{a.source_note}\nextracted {dt.date.today().isoformat()} by scripts/shelf_v5/extract_seed.py\n',
        encoding='utf-8')
    print('wrote', seed)


if __name__ == '__main__':
    main()
