"""ctrl-settings/ICwIwLF: the list of industries that use a whole-industry load shape.

Written from the same table as the SHELF-indstcat tabs (industry.ASSIGN), so the two cannot drift apart: the
model needs the rows of the SHELF-indstcat files in the same order as this list.
"""
from __future__ import annotations
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

from .industry import ASSIGN, label

WORKBOOK_NAME = 'Indst Cat w Indst wide Load Factor.xlsx'
CSV_NAME = 'ICwIwLF.csv'
ABOUT = {
    1: 'ICwIwLF Industry Categories with Industry-wide Load Factor',
    3: 'Sources: ',
    6: 'Notes:',
    7: 'One can define hourly load profiles in EPS by industrial process (end uses like boilers vs.',
    8: 'facility lighting, for example) or by industry category (coal mining vs. wood product mfg, ',
    9: 'for example). ',
    11: 'In the U.S. EPS, we define an industry-wide profile for every industry. The profiles are built',
    12: 'in elec/SHELF from hourly load data by industry, which show that industries differ mainly in',
    13: 'how much of their load falls at night rather than in which end uses they run.',
    15: 'To re-define the load factor industry selection in other regions, list on the next page only the',
    16: "industries you'd like to have non-process definitions for (second column), with the same name",
    17: 'minus the ISIC definition (e.g., 01T03) in the first column. The rows of the SHELF-indstcat',
    18: 'files in elec/SHELF must list the same industries in the same order.',
}


def rows() -> list[tuple[str, str]]:
    return [('Indst Cat w Load Factor', 'Industry Category')] + [(label(cat), cat) for cat, *_ in ASSIGN]


def write(out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    ab = wb.active
    ab.title = 'About'
    for r, t in ABOUT.items():
        ab.cell(r, 1, t)
    ab['A1'].font = Font(bold=True); ab['A6'].font = Font(bold=True)
    ab['B3'] = '(none needed).'
    for i, (cat, *_) in enumerate(ASSIGN):
        ab.cell(20 + i, 1, cat)
    ws = wb.create_sheet('ICwIwLF')
    for i, (a, b) in enumerate(rows(), start=1):
        ws.cell(i, 1, a); ws.cell(i, 2, b)
    ws['A1'].font = Font(bold=True); ws['B1'].font = Font(bold=True)
    ws.column_dimensions['A'].width = 30.4
    xlsx, csv_path = out_dir / WORKBOOK_NAME, out_dir / CSV_NAME
    wb.save(xlsx)
    with open(csv_path, 'w', newline='\n') as f:
        for a, b in rows():
            f.write(f'{a},{b}\n')
    return xlsx, csv_path
