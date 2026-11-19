"""Recalculate a built SHELF workbook in Excel and export its output tabs to the CSV files EPS reads.

The build script saves formulas without values (openpyxl cannot calculate). This script opens the workbook
in Excel (Windows, needs Excel and pywin32), recalculates everything, counts cells whose formula returns an
error, saves, and then writes one CSV per SHELF-<name> tab next to the workbook. Nothing is exported if any
formula returns an error.

Numbers are written to 10 significant figures, in the style each file already has in eps-us (plain for the
buildings, transport and data-center files, exponent for the industry and system-load files), so that a
rebuild with unchanged inputs leaves `git diff` empty.

Usage:
    python scripts/shelf_v5/recalc_export.py <out folder> --version 5.0        # recalculate, then export
    python scripts/shelf_v5/recalc_export.py <out folder> --version 5.0 --no-recalc
<out folder> is the --out of build_shelf_workbook.py (default output/us_shelf_<version>/).
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import openpyxl

WORKBOOK_NAME = 'Seasonal Hourly Equipment Load Factors by End Use.xlsx'
# tabs kept in the 5.0 workbook for reference but not read by the 5.0 model, so no CSV is written
NOT_EXPORTED_V5 = {'SHELF-industry'}
LOCK_PREFIX = '~' + chr(36)          # Excel's lock-file prefix


def exponent_style(tab: str) -> bool:
    return tab.startswith('SHELF-indst') or tab in ('SHELF-district-heat-hydrogen', 'SHELF-geoeng')


def recalc(path: Path) -> dict[str, int]:
    """Full recalculation in Excel. Returns {tab: number of formula cells returning an error}."""
    import win32com.client
    import win32process
    path = Path(path).resolve()
    if (path.parent / (LOCK_PREFIX + path.name)).exists():
        raise RuntimeError(f'{path.name} is open in Excel: close it first')
    xl = win32com.client.DispatchEx('Excel.Application')
    pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
    try:
        xl.Visible = False
        xl.DisplayAlerts = False
        xl.AutomationSecurity = 3
        wb = xl.Workbooks.Open(str(path), 0, False)
        xl.CalculateFullRebuild()
        errors = {}
        for ws in wb.Worksheets:
            try:
                errors[ws.Name] = ws.UsedRange.SpecialCells(-4123, 16).Count     # formulas returning errors
            except Exception:
                pass                                                            # none on this sheet
        wb.Save()
        wb.Close(False)
        return errors
    finally:
        try:
            xl.Quit()
        except Exception:
            pass
        os.system(f'taskkill /PID {pid} /F >NUL 2>&1')       # only the Excel this script started


def fmt(v, exponent: bool) -> str:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(f'not a number: {v!r}')
    if isinstance(v, int) or v == 0:
        return str(int(v))
    return f'{v:.9e}' if exponent else f'{v:.10g}'


def export(workbook: Path, folder: Path, version: str) -> list[str]:
    wb = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    written = []
    for ws in wb.worksheets:
        tab = ws.title
        if not tab.startswith('SHELF-') or (version == '5.0' and tab in NOT_EXPORTED_V5):
            continue
        rows = [r for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
        width = len([x for x in rows[0] if x is not None])
        if any(x is None for r in rows for x in r[:width]):
            raise ValueError(f'{tab}: empty cell inside the table (was the workbook recalculated?)')
        ex = exponent_style(tab)
        with open(folder / f'{tab}.csv', 'w', newline='\n') as f:
            f.write(','.join(str(x) for x in rows[0][:width]) + '\n')
            for r in rows[1:]:
                f.write(str(r[0]) + ',' + ','.join(fmt(v, ex) for v in r[1:width]) + '\n')
        written.append(tab)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('out')
    ap.add_argument('--version', choices=['4.0', '5.0'], required=True)
    ap.add_argument('--no-recalc', action='store_true', help='export the values already saved in the workbook')
    a = ap.parse_args()
    folder = Path(a.out) / 'elec' / 'SHELF'
    workbook = folder / WORKBOOK_NAME
    if not a.no_recalc:
        print('recalculating in Excel:', workbook)
        errs = recalc(workbook)
        n = sum(errs.values())
        print('formula cells returning an error:', n, errs if errs else '')
        if n:
            print('nothing exported')
            return 1
    written = export(workbook, folder, a.version)
    print(f'exported {len(written)} CSV files to {folder}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
