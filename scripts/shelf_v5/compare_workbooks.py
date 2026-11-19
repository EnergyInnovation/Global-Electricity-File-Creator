"""Compare two SHELF workbooks cell by cell: formula text and typed-in values, every tab.

Used to show that a workbook built by scripts/build_shelf_workbook.py is the same workbook as a reference
(for example the one committed to eps-us). Numbers are compared with a relative tolerance, because Excel
rewrites pasted numbers to 15 significant figures when it saves. Formulas are compared as text.

Usage:
    python scripts/shelf_v5/compare_workbooks.py <built.xlsx> <reference.xlsx> [--tol 1e-12] [--show 5]
Exit code 0 when the only differences are in cells listed in EXPECTED.
"""
from __future__ import annotations
import argparse
import sys

import openpyxl
from openpyxl.utils import get_column_letter

# cells that are meant to differ between two builds
EXPECTED = {('About', 'B41'): 'run line: build date and where each input was read from'}


def cells(ws) -> dict:
    out = {}
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if v is None:
                continue
            if not isinstance(v, (str, int, float, bool)):
                v = getattr(v, 'text', None) or str(v)           # array formulas, dates
            out[(c.row, c.column)] = v
    return out


def same(a, b, tol: float) -> bool:
    if isinstance(a, bool) or isinstance(b, bool) or isinstance(a, str) or isinstance(b, str):
        return a == b
    if a == b:
        return True
    return abs(a - b) <= tol * max(abs(a), abs(b))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('built'); ap.add_argument('reference')
    ap.add_argument('--tol', type=float, default=1e-12, help='relative tolerance for numbers')
    ap.add_argument('--show', type=int, default=5, help='differences to print per tab')
    a = ap.parse_args()
    print('loading', a.built); wb1 = openpyxl.load_workbook(a.built)
    print('loading', a.reference); wb2 = openpyxl.load_workbook(a.reference)
    bad = 0
    if wb1.sheetnames != wb2.sheetnames:
        only1 = [n for n in wb1.sheetnames if n not in wb2.sheetnames]
        only2 = [n for n in wb2.sheetnames if n not in wb1.sheetnames]
        print(f'TAB LIST DIFFERS: only in built {only1}; only in reference {only2}; '
              f'same tabs in a different order: {not only1 and not only2}')
        bad += 1
    else:
        print(f'tab list and order: same ({len(wb1.sheetnames)} tabs)')
    total = worst = 0
    for name in wb1.sheetnames:
        if name not in wb2.sheetnames:
            continue
        c1, c2 = cells(wb1[name]), cells(wb2[name])
        diffs, mx = [], 0.0
        for k in sorted(set(c1) | set(c2)):
            x, y = c1.get(k), c2.get(k)
            coord = f'{get_column_letter(k[1])}{k[0]}'
            if x is None or y is None or not same(x, y, a.tol):
                if (name, coord) in EXPECTED:
                    print(f'  {name}!{coord}: differs as expected ({EXPECTED[(name, coord)]})')
                    continue
                diffs.append((coord, x, y))
            elif isinstance(x, (int, float)) and not isinstance(x, bool) and x != y:
                mx = max(mx, abs(x - y) / max(abs(x), abs(y)))
        total += len(c1); worst = max(worst, mx)
        flag = 'ok ' if not diffs else 'DIFF'
        print(f'{flag} {name:32} cells {len(c1):7d} vs {len(c2):7d}  differences {len(diffs):6d}'
              + (f'  (numbers equal within {mx:.1e})' if mx else ''))
        for coord, x, y in diffs[:a.show]:
            print(f'       {coord}: built={str(x)[:110]!r}  reference={str(y)[:110]!r}')
        bad += len(diffs)
    print(f'{total} cells compared; unexpected differences: {bad}; largest relative difference between numbers '
          f'counted as equal: {worst:.1e}')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
