"""Build the canonical SYSHECF Excel workbook as a self-contained derivation.

v2 changes (2026-05-22):
  - Raw Cambium hourly + annual source files pasted in verbatim (every column,
    every row of metadata + data).
  - Derived columns added at the end of the hourly tab: day_of_year,
    hour_of_day, slice, and per-tech CF columns (=MWh / capacity_MW).
  - VLOOKUP instead of XLOOKUP for slice resolution (compatible with Excel
    2019 and earlier).
  - SYSHECF tabs use AVERAGEIFS against the derived CF columns.

Workbook tabs:
  - About
  - Clustering            — days-per-timeslice + DOY → slice (editable)
  - EIA CF targets        — per-tech target annual CFs (editable)
  - Cambium annual source — verbatim paste of the source CSV (all 107 cols)
  - Cambium hourly source — verbatim paste (75 source cols) + derived cols
  - SYSHECF-<tech>        — 25 per-tech tables (formulas / mirrors / templates)

Target file:
  C:/Users/RobbieOrvis/Models/US/Models/eps-us/InputData/elec/SYSHECF/
    Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx

Run:
    python scripts/build_syshecf_workbook.py

Options (2026-11-17; all off by default, so the default build is unchanged):
    --out <xlsx>               where to write the workbook (default: the OUT path below)
    --labels 5.0               EPS 5.0 timeslice names (Representative Day 1-4, Net Peak Summer/Winter
                               Day, as on eps-us develop) instead of Winter/Spring/.../Winter Peak
    --csv-out <folder>         also write SYSHECF-<tech>.csv for the Cambium-derived techs, computed in
                               Python with the same arithmetic as the workbook formulas
    --solar-shift-hours <h>    move the Cambium solar series (utility PV, distributed PV, CSP) <h> hours
                               later before the timeslice averages are taken. Cambium labels its hours
                               as hour-beginning averages, but its solar values behave like the output
                               at the END of each labelled hour (sun tests 2026-11-17), which puts the
                               solar day about half an hour early; 0.5 corrects that. The shift is done
                               by formulas: a 'Solar timing' tab holds the hours, and shifted CF columns
                               are added to the hourly tab. Each hour becomes the time-weighted mean of
                               the two source hours it overlaps, wrapping within the day, so every day's
                               energy and the annual CF calibration to the EIA targets are unchanged.
                               With 0 (the default) none of this is added.
If scikit-learn is not installed, the clustering falls back to the saved day list
data/cambium24_midcase_national/k6_slice_assignment_repday.csv (the list on eps-us develop).
"""
from __future__ import annotations
import argparse
import csv
import sys
from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from shelf_v5.names import CANONICAL as SLICE_NAMES_CANONICAL, V5_LABELS as SLICE_NAMES_V5
try:
    from state_pipeline.builders.clustering import SLICE_NAMES
    from state_pipeline.builders.clustering_repday import cluster_days_repday
except ImportError:                       # scikit-learn missing: use the saved day list instead
    SLICE_NAMES = list(SLICE_NAMES_CANONICAL)
    cluster_days_repday = None

CAMBIUM_HOURLY = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"
CAMBIUM_ANNUAL = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_annual_national.csv"
SAVED_CLUSTERING = ROOT / "data" / "cambium24_midcase_national" / "k6_slice_assignment_repday.csv"
EIA_408B       = ROOT / "data" / "epa_04_08_b.xlsx"
OUT = Path(
    r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SYSHECF"
    r"\Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx"
)

EIA_CF_TARGETS = {
    'solar-pv':      0.232,
    'solar-pv-dist': 0.170,
    'solar-thermal': 0.250,
    'onshore-wind':  0.343,
    'offshore-wind': 0.420,
}

# (syshecf-tech, hourly_source_col_name, annual_source_col_name, display_name)
TECHS_CAMBIUM = [
    ('solar-pv',            'upv_MWh',       'upv_MW',       'solar pv'),
    ('solar-pv-dist',       'distpv_MWh',    'distpv_MW',    'solar pv dist'),
    ('solar-thermal',       'csp_MWh',       'csp_MW',       'solar thermal'),
    ('onshore-wind',        'wind-ons_MWh',  'wind-ons_MW',  'onshore wind'),
    ('offshore-wind',       'wind-ofs_MWh',  'wind-ofs_MW',  'offshore wind'),
    ('hydro',               'hydro_MWh',     'hydro_MW',     'hydro'),
    ('pumped-hydro',        'phs_MWh',       'phs_MW',       'pumped hydro'),
    ('nuclear',             'nuclear_MWh',   'nuclear_MW',   'nuclear'),
    ('combined-cycle',      'gas-cc_MWh',    'gas-cc_MW',    'natural gas combined cycle'),
    ('natural-gas-peaker',  'gas-ct_MWh',    'gas-ct_MW',    'natural gas peaker'),
    ('hard-coal',           'coal_MWh',      'coal_MW',      'hard coal'),
    ('biomass',             'biomass_MWh',   'biomass_MW',   'biomass'),
    ('geothermal',          'geothermal_MWh', 'geothermal_MW', 'geothermal'),
    ('petroleum',           'o-g-s_MWh',     'o-g-s_MW',     'petroleum'),
]

HYDROGEN_MIRRORS = [
    ('hydrogen-CT', 'natural-gas-peaker', 'hydrogen CT'),
    ('hydrogen-CC', 'combined-cycle',     'hydrogen combined cycle'),
]

TEMPLATE_TECHS = [
    ('lignite',                0.70, 'lignite'),
    ('lignite-CCS',            0.70, 'lignite ccs'),
    ('combined-cycle-CCS',     0.60, 'natural gas combined cycle ccs'),
    ('hard-coal-CCS',          0.55, 'hard coal ccs'),
    ('biomass-CCS',            0.55, 'biomass ccs'),
    ('heavy-or-residual-oil',  0.10, 'heavy or residual fuel oil'),
    ('crude-oil',              0.10, 'crude oil'),
    ('SMR',                    0.85, 'SMR'),
    ('MSW',                    0.60, 'MSW'),
    ('steam-turbine',          0.50, 'natural gas steam turbine'),
]

SLICES = list(SLICE_NAMES)
HOUR_COLS = [f'Hour{h}' for h in range(24)]

# Techs whose Cambium hourly series --solar-shift-hours moves later
SOLAR_SHIFT_TECHS = ('solar-pv', 'solar-pv-dist', 'solar-thermal')
SOLAR_TIMING_TAB = 'Solar timing'

# Final SYSHECF tab order — matches EPS subscript order for Electricity Source.
# Per user 2026-05-22 list. solar-pv-dist and pumped-hydro are NOT in that
# subscript list but their CSV files exist; appended at the end with a
# trailing-underscore tab-name prefix so they sort last. Tell user to confirm
# whether to keep them.
SYSHECF_TAB_ORDER = [
    'hard-coal',
    'steam-turbine',           # natural gas steam turbine
    'combined-cycle',          # natural gas combined cycle
    'nuclear',
    'hydro',
    'pumped-hydro',            # placed next to hydro
    'onshore-wind',
    'solar-pv',
    'solar-thermal',
    'biomass',
    'geothermal',
    'petroleum',
    'natural-gas-peaker',
    'lignite',
    'offshore-wind',
    'crude-oil',
    'heavy-or-residual-oil',
    'MSW',                     # municipal solid waste
    'hard-coal-CCS',
    'combined-cycle-CCS',
    'biomass-CCS',
    'lignite-CCS',
    'SMR',                     # small modular reactor
    'hydrogen-CT',             # hydrogen combustion turbine
    'hydrogen-CC',             # hydrogen combined cycle
    'solar-pv-dist',           # distributed PV — last per user 2026-05-22
]

HEADER_FILL = PatternFill(start_color='305496', end_color='305496', fill_type='solid')
HEADER_FONT = Font(bold=True, color='FFFFFF')
SECTION_FILL = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
SECTION_FONT = Font(bold=True)
OUTPUT_TAB_COLOR = '1F3864'  # Excel "Dark Blue, Accent 1, Darker 25%"


# ---------------------------------------------------------------------------
# Load source files (preserving raw structure)
# ---------------------------------------------------------------------------

def _read_csv_raw(path: Path) -> list[list[str]]:
    with open(path, newline='') as f:
        return list(csv.reader(f))


def _try_float(s: str):
    try:
        return float(s)
    except (ValueError, TypeError):
        return s


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

PURPOSE_FILL = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
PURPOSE_FONT = Font(bold=True)


def add_about_tab(wb: openpyxl.Workbook, days_per_slice: dict | None = None,
                  file_name_no_ext: str = '', solar_shift_hours: float = 0.0):
    """About tab:
      - A1 (bold): file name (without .xlsx)
      - A3: "Sources:"
      - Starting at B3, source blocks of 6 cells each:
          Purpose (bold, gray bg) → Source → Publication → Year → URL → Important info
        Each block followed by a blank cell, then the next block.
      - After all sources, blank row, then A-col "Notes:" with B-col methodology text.
    """
    ws = wb.create_sheet('About', 0)
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 110

    sp_days = days_per_slice.get(SLICES[4], 0) if days_per_slice else 0
    wp_days = days_per_slice.get(SLICES[5], 0) if days_per_slice else 0
    today = dt.date.today().isoformat()

    # A1: SYSHECF abbreviation + file name in bold (default size)
    ws.cell(row=1, column=1, value=f'SYSHECF {file_name_no_ext}').font = Font(bold=True)

    # A3: "Sources:"
    ws.cell(row=3, column=1, value='Sources:').font = Font(bold=True)

    # Source blocks in column B starting at row 3
    sources = [
        {
            'purpose': 'Hourly Generation by Electricity Type and Hourly Load',
            'source':  'NREL',
            'publication': 'NREL Cambium Scenarios 2024',
            'year':    2024,
            'url':     'https://www.nrel.gov/analysis/cambium.html',
            'info':    'MidCase scenario, weather year 2012, USA national, 2025 model year. '
                      'File: Cambium24_MidCase_hourly_usa_2025.csv pasted verbatim into '
                      'the "Cambium hourly source" tab (8,760 hourly rows × 75 columns).',
        },
        {
            'purpose': 'Installed Capacity by Electricity Type (Annual)',
            'source':  'NREL',
            'publication': 'NREL Cambium Scenarios 2024',
            'year':    2024,
            'url':     'https://www.nrel.gov/analysis/cambium.html',
            'info':    'MidCase scenario, USA national, all model years 2025–2050. '
                      'File: Cambium24_MidCase_annual_national.csv pasted verbatim into '
                      'the "Cambium annual source" tab. The 2025 row supplies the '
                      'capacity_MW denominators for the derived CF columns in the hourly tab.',
        },
        {
            'purpose': 'Observed Annual Capacity Factors by Electricity Type '
                      '(CF calibration target)',
            'source':  'EIA',
            'publication': 'EIA Electric Power Annual, Table 4.8.B '
                          '(Capacity Factors for Utility Scale Generators by Energy Source)',
            'year':    2025,
            'url':     'https://www.eia.gov/electricity/annual/html/epa_04_08_b.html',
            'info':    'Most recent data year = 2024. 2024 values used for SYSHECF VRE '
                      'calibration: solar PV = 0.232, solar thermal = 0.250, onshore wind = 0.343. '
                      'Offshore wind (0.420) and distributed PV (0.170) not reported in this '
                      'table — manual values per CLAUDE.md §1. File: epa_04_08_b.xlsx pasted '
                      'into the "EIA Table 4.8.B source" tab.',
        },
    ]

    left_top = Alignment(horizontal='left', vertical='top', wrap_text=True)
    cur_row = 3  # B3 starts first source's purpose
    for src in sources:
        # Purpose (bold, gray bg, left aligned)
        c = ws.cell(row=cur_row, column=2, value=src['purpose'])
        c.font = PURPOSE_FONT
        c.fill = PURPOSE_FILL
        c.alignment = left_top
        for off, val in enumerate([src['source'], src['publication'], src['year']], start=1):
            cell = ws.cell(row=cur_row + off, column=2, value=val)
            cell.alignment = left_top
        url_cell = ws.cell(row=cur_row + 4, column=2, value=src['url'])
        url_cell.hyperlink = src['url']
        url_cell.font = Font(color='0563C1', underline='single')
        url_cell.alignment = left_top
        info_cell = ws.cell(row=cur_row + 5, column=2, value=src['info'])
        info_cell.alignment = left_top
        cur_row += 7  # 6 cells + 1 blank

    # Blank row, then Notes block in column A + B
    notes_row_a = cur_row + 1
    ws.cell(row=notes_row_a, column=1, value='Notes:').font = Font(bold=True)

    notes_lines = [
        ('Methodology overview',
         f'This workbook produces SYSHECF (Start Year Seasonal Expected Hourly Electricity '
         f'Capacity Factors) tables for the EPS Vensim model. All values are derived '
         f'from the pasted source tabs via Excel formulas — modify the source data, '
         f'EIA targets, or clustering assignments and the per-tech SYSHECF tabs '
         f'recompute automatically.'),
        ('Source data layout',
         '"Cambium hourly source" pastes the Cambium 2024 MidCase national hourly CSV '
         'verbatim (75 source columns × 8,760 data rows preceded by 6 metadata rows). '
         'Derived columns are appended at the right: day_of_year, hour_of_day, slice '
         '(via VLOOKUP against the Clustering tab), and per-tech CF columns '
         '(= source MWh column / 2025 capacity_MW lookup from the annual tab).'),
        ('Clustering',
         f'K6/H24 representative-day clustering on Cambium net load assigns each '
         f'day-of-year to one of six timeslices (Winter / Spring / Summer / Fall / '
         f'Summer Peak / Winter Peak). Optimizer self-terminated at SP={sp_days} days '
         f'and WP={wp_days} days. Algorithm: cluster_days_repday '
         f'(state_pipeline/builders/clustering_repday.py).'),
        ('SYSHECF derivation',
         'Per-tech SYSHECF tabs aggregate the derived CF column via AVERAGEIFS '
         '(filtered by slice + hour_of_day). For VRE techs (solar PV, solar thermal, '
         'onshore wind, offshore wind, distributed PV) the result is scaled by '
         '(EIA Table 4.8.B target / Cambium annual mean) so the annual-weighted CF '
         'matches the EIA observed CF. Non-VRE Cambium techs are not scaled.'),
        ('Hydrogen techs',
         'hydrogen-CT references natural-gas-peaker cell-by-cell. hydrogen-CC references '
         'combined-cycle. Edit either source to propagate to the hydrogen mirror.'),
        ('Template techs',
         'lignite, lignite-CCS, hard-coal-CCS, combined-cycle-CCS, biomass-CCS, '
         'heavy/residual oil, crude oil, SMR, MSW, steam-turbine: flat constant CFs '
         '(placeholder values). Edit the tab directly to change.'),
        ('Tab order',
         'SYSHECF tab order matches the EPS Electricity Source subscript. Distributed '
         'PV is positioned at the end; pumped-hydro is placed next to hydro.'),
        ('Run metadata',
         f'country: UnitedStates; weather year: 2012 (per Cambium); built: {today}; '
         f'build script: scripts/build_syshecf_workbook.py.'),
        ('Caveats',
         'All values are inputs for staff review. Verify against NREL Cambium 2024, '
         'EIA Table 4.8.B, and the project methodology (CLAUDE.md at project root) '
         'before being used in any work product.'),
    ]
    if solar_shift_hours:
        notes_lines.append(SOLAR_TIMING_NOTE)

    # "Notes:" label stays on notes_row_a; methodology bullets start one row below
    for i, (label, text) in enumerate(notes_lines):
        r = notes_row_a + 1 + i
        ws.cell(row=r, column=1, value=label).font = Font(bold=True)
        text_cell = ws.cell(row=r, column=2, value=text)
        text_cell.alignment = left_top
        ws.row_dimensions[r].height = max(30, 18 * (1 + (len(text) // 110)))


def add_clustering_tab(wb: openpyxl.Workbook, days_per_slice: dict, slice_assignment: dict):
    ws = wb.create_sheet('Clustering')
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 8
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 14

    ws.cell(row=1, column=1, value='Days per timeslice (snapshot)').font = SECTION_FONT
    ws.cell(row=1, column=1).fill = SECTION_FILL
    ws.cell(row=2, column=1, value='Slice').font = HEADER_FONT
    ws.cell(row=2, column=1).fill = HEADER_FILL
    ws.cell(row=2, column=2, value='Days').font = HEADER_FONT
    ws.cell(row=2, column=2).fill = HEADER_FILL
    for i, sl in enumerate(SLICES):
        ws.cell(row=3 + i, column=1, value=sl)
        ws.cell(row=3 + i, column=2, value=int(days_per_slice.get(sl, 0)))

    ws.cell(row=1, column=4, value='DOY → slice (edit to reassign days)').font = SECTION_FONT
    ws.cell(row=1, column=4).fill = SECTION_FILL
    ws.cell(row=2, column=4, value='DOY').font = HEADER_FONT
    ws.cell(row=2, column=4).fill = HEADER_FILL
    ws.cell(row=2, column=5, value='Slice').font = HEADER_FONT
    ws.cell(row=2, column=5).fill = HEADER_FILL
    for doy in range(1, 366):
        sl = slice_assignment.get(doy, 'Winter')
        ws.cell(row=2 + doy, column=4, value=doy)
        ws.cell(row=2 + doy, column=5, value=sl)


def add_eia_408b_source_tab(wb: openpyxl.Workbook, source_xlsx: Path):
    """Paste the EIA Table 4.8.B xlsx contents verbatim as a tab in this workbook."""
    if not source_xlsx.exists():
        print(f"  WARN: {source_xlsx} not found — EIA Table 4.8.B source tab skipped")
        return
    src_wb = openpyxl.load_workbook(source_xlsx, data_only=True)
    src_ws = src_wb[src_wb.sheetnames[0]]
    ws = wb.create_sheet('EIA Table 4.8.B source')
    for row in src_ws.iter_rows(values_only=True):
        ws.append(list(row))
    # Column widths
    for c in range(1, src_ws.max_column + 1):
        ws.column_dimensions[get_column_letter(c)].width = 16
    ws.freeze_panes = 'B2'


def add_eia_targets_tab(wb: openpyxl.Workbook):
    """EIA CF targets tab — pulls CF values from the EIA Table 4.8.B source tab
    via INDEX/MATCH on the editable Data year cell (F1). Techs not in EIA 4.8.B
    (offshore wind, distributed PV) are hardcoded with a clear note.
    """
    ws = wb.create_sheet('EIA CF targets')
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 28
    ws.column_dimensions['D'].width = 60
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 10

    ws.cell(row=1, column=1, value='EIA Table 4.8.B annual CF targets (national, capacity-weighted)') \
      .font = SECTION_FONT
    ws.cell(row=1, column=1).fill = SECTION_FILL

    # Editable Data year cell — formulas reference $F$1
    ws.cell(row=1, column=5, value='Data year:').font = Font(bold=True)
    ws.cell(row=1, column=6, value=2024)
    ws.cell(row=1, column=6).font = Font(bold=True)

    # Headers
    for col, name in [(1, 'Tech'), (2, 'Target CF'), (3, 'Source'), (4, 'Notes')]:
        cell = ws.cell(row=2, column=col, value=name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    # EIA Table 4.8.B source column letters where the CF for each tech lives
    # (verified from source xlsx: row 2 has tech names, CF columns are the
    # second column of each tech's pair)
    eia_source_cf_col = {
        'solar-pv':       'M',   # "Solar" (utility-scale PV)
        'solar-thermal':  'O',   # "Solar - Thermal"
        'onshore-wind':   'Q',   # "Wind" (onshore in EIA terminology)
    }

    for i, (tech, default_cf) in enumerate(EIA_CF_TARGETS.items()):
        row = 3 + i
        ws.cell(row=row, column=1, value=tech)
        if tech in eia_source_cf_col:
            col = eia_source_cf_col[tech]
            formula = (
                f"=INDEX('EIA Table 4.8.B source'!{col}:{col},"
                f"MATCH($F$1,'EIA Table 4.8.B source'!$A:$A,0))"
            )
            ws.cell(row=row, column=2, value=formula)
            ws.cell(row=row, column=3, value=f"EIA Table 4.8.B col {col}")
            ws.cell(row=row, column=4,
                    value="Pulled via INDEX/MATCH from the EIA source tab for the year in $F$1. "
                          "Edit $F$1 to switch data year.")
        else:
            ws.cell(row=row, column=2, value=default_cf)
            ws.cell(row=row, column=3, value="Manual (not in EIA 4.8.B)")
            note = {
                'solar-pv-dist':  "Distributed PV is not reported in EIA Table 4.8.B. "
                                  "Value (0.170) is per CLAUDE.md §1; could be derived from EIA "
                                  "Form EIA-861 (distributed PV) or Table 19 of EIA State "
                                  "Electricity Profiles. Edit cell B4 directly to change.",
                'offshore-wind':  "Offshore wind is not split out in EIA Table 4.8.B "
                                  "(EIA reports 'Wind' which is onshore-dominated). Value (0.420) is "
                                  "per CLAUDE.md §1 / industry observed performance. Edit cell B7 "
                                  "directly to change.",
            }.get(tech, "Manual value. Edit directly to change.")
            ws.cell(row=row, column=4, value=note)
        # Left-align all cells
        for col in range(1, 5):
            ws.cell(row=row, column=col).alignment = Alignment(horizontal='left', vertical='top',
                                                               wrap_text=True)


def add_cambium_annual_source_tab(wb: openpyxl.Workbook, rows: list[list[str]]) -> dict:
    """Paste annual CSV verbatim. Returns a dict: source_col_name → 0-indexed column."""
    ws = wb.create_sheet('Cambium annual source')
    if not rows:
        return {}
    headers = rows[0]
    col_idx = {h: i for i, h in enumerate(headers)}

    # Write all rows
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row, start=1):
            cell_val = _try_float(val) if r_idx > 1 else val
            ws.cell(row=r_idx, column=c_idx, value=cell_val)

    # Reasonable widths
    for c in range(1, min(len(headers), 50) + 1):
        ws.column_dimensions[get_column_letter(c)].width = 16
    ws.freeze_panes = 'D2'
    return col_idx


def add_cambium_hourly_source_tab(
    wb: openpyxl.Workbook,
    rows: list[list[str]],
    annual_col_idx: dict,
    cluster_result,
) -> tuple[dict, int, int]:
    """Paste hourly source CSV verbatim. Add derived columns at the end:
    day_of_year, hour_of_day, slice (VLOOKUP), CF_<tech> (= MWh / cap_MW).

    Returns (tech_cf_col_letter_map, data_start_row, data_end_row).
    Row 6 in the source = source column names. Data starts row 7.
    """
    ws = wb.create_sheet('Cambium hourly source')
    if len(rows) < 7:
        raise RuntimeError("Cambium hourly source has fewer than 7 rows")

    # Source headers
    src_headers = rows[5]  # row 6 = column names
    src_col_idx = {h: i for i, h in enumerate(src_headers)}
    n_src_cols = len(src_headers)

    # Write metadata rows + header row + 8760 data rows verbatim
    print(f"  [hourly source] writing {len(rows)} rows × {n_src_cols} src cols...")
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row, start=1):
            # Cast data rows' MWh values to numbers; keep metadata rows as strings
            cell_val = _try_float(val) if r_idx >= 7 and c_idx >= 2 else val
            ws.cell(row=r_idx, column=c_idx, value=cell_val)

    data_start = 7
    data_end = len(rows)  # 8766 for full file

    # Derived columns: DOY, hour_of_day, slice, CF_<tech>
    derived_col_offset = n_src_cols  # 0-indexed offset
    cols = {
        'day_of_year':  n_src_cols + 1,
        'hour_of_day':  n_src_cols + 2,
        'slice':        n_src_cols + 3,
    }
    # Headers for derived columns (in row 6, alongside source col names)
    ws.cell(row=6, column=cols['day_of_year'], value='day_of_year').font = Font(bold=True, italic=True)
    ws.cell(row=6, column=cols['hour_of_day'], value='hour_of_day').font = Font(bold=True, italic=True)
    ws.cell(row=6, column=cols['slice'],       value='slice').font = Font(bold=True, italic=True)

    # Fill DOY/hour as static integers (more efficient than formulas)
    # The file is sorted chronologically: rows 7..30 → DOY 1 hours 0..23, etc.
    for i in range(data_end - data_start + 1):
        row = data_start + i
        doy = (i // 24) + 1
        hod = i % 24
        ws.cell(row=row, column=cols['day_of_year'], value=doy)
        ws.cell(row=row, column=cols['hour_of_day'], value=hod)
        # Slice via VLOOKUP from Clustering tab (DOY in col D, slice in col E rows 3..367)
        doy_col_letter = get_column_letter(cols['day_of_year'])
        ws.cell(row=row, column=cols['slice'],
                value=f"=VLOOKUP({doy_col_letter}{row},Clustering!$D$3:$E$367,2,FALSE)")

    # Per-tech CF columns. Capacity for 2025 is in row 2 of Cambium annual source.
    # Each CF column = <source MWh col>{row} / 'Cambium annual source'!<cap_col>$2
    tech_cf_col_letter = {}
    cf_col_offset = n_src_cols + 4  # starts after slice
    for k, (tech, mwh_col, mw_col, _disp) in enumerate(TECHS_CAMBIUM):
        col = cf_col_offset + k
        col_letter = get_column_letter(col)
        tech_cf_col_letter[tech] = col_letter
        # Header
        ws.cell(row=6, column=col, value=f'CF_{tech}').font = Font(bold=True, italic=True)
        # Source MWh column index (1-based)
        if mwh_col not in src_col_idx:
            continue
        mwh_col_letter = get_column_letter(src_col_idx[mwh_col] + 1)
        # Annual source MW column letter
        if mw_col not in annual_col_idx:
            continue
        cap_col_letter = get_column_letter(annual_col_idx[mw_col] + 1)
        # Formula for each data row: =IFERROR(MWh/cap, 0)
        for r in range(data_start, data_end + 1):
            ws.cell(row=r, column=col,
                    value=f"=IFERROR({mwh_col_letter}{r}/'Cambium annual source'!${cap_col_letter}$2,0)")

    # Column widths
    for c in range(1, min(n_src_cols + 4 + len(TECHS_CAMBIUM), 50) + 1):
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.freeze_panes = 'B7'

    return tech_cf_col_letter, data_start, data_end


def add_syshecf_tech_tab(
    wb: openpyxl.Workbook,
    tech: str,
    display: str,
    cf_col_letter: str,
    derived_doy_col_letter: str,  # not used (slice column is what AVERAGEIFS filters on)
    slice_col_letter: str,
    hour_col_letter: str,
    data_start_row: int,
    data_end_row: int,
    eia_target_row: int | None,
):
    """Per-tech SYSHECF tab using AVERAGEIFS over derived CF column."""
    ws = wb.create_sheet(f'SYSHECF-{tech}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 16
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12

    ws.cell(row=1, column=1, value=display)
    for h, name in enumerate(HOUR_COLS):
        ws.cell(row=1, column=2 + h, value=name)

    cf_range = f"'Cambium hourly source'!${cf_col_letter}${data_start_row}:${cf_col_letter}${data_end_row}"
    slice_range = f"'Cambium hourly source'!${slice_col_letter}${data_start_row}:${slice_col_letter}${data_end_row}"
    hour_range = f"'Cambium hourly source'!${hour_col_letter}${data_start_row}:${hour_col_letter}${data_end_row}"

    for r_off, sl in enumerate(SLICES):
        ws.cell(row=2 + r_off, column=1, value=sl)
        for h in range(24):
            avg = f"AVERAGEIFS({cf_range},{slice_range},$A{2+r_off},{hour_range},{h})"
            if eia_target_row is not None:
                # Annual mean CF for this tech = AVERAGE of the CF column
                annual_mean = f"AVERAGE({cf_range})"
                formula = (
                    f"=IFERROR(MAX(0,MIN(1,{avg}*'EIA CF targets'!$B${eia_target_row}/{annual_mean})),0)"
                )
            else:
                formula = f"=IFERROR(MAX(0,MIN(1,{avg})),0)"
            ws.cell(row=2 + r_off, column=2 + h, value=formula)


def add_syshecf_mirror_tab(wb: openpyxl.Workbook, tech: str, source_tech: str, display: str):
    ws = wb.create_sheet(f'SYSHECF-{tech}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 24
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12
    src_sheet = f"'SYSHECF-{source_tech}'"

    ws.cell(row=1, column=1, value=display)
    for h, name in enumerate(HOUR_COLS):
        ws.cell(row=1, column=2 + h, value=name)
    for r_off, sl in enumerate(SLICES):
        ws.cell(row=2 + r_off, column=1, value=sl)
        for h in range(24):
            col_letter = get_column_letter(2 + h)
            ws.cell(row=2 + r_off, column=2 + h,
                    value=f"={src_sheet}!{col_letter}{2+r_off}")


def add_syshecf_template_tab(wb: openpyxl.Workbook, tech: str, cf: float, display: str):
    ws = wb.create_sheet(f'SYSHECF-{tech}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 24
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12

    ws.cell(row=1, column=1, value=display)
    for h, name in enumerate(HOUR_COLS):
        ws.cell(row=1, column=2 + h, value=name)
    for r_off, sl in enumerate(SLICES):
        ws.cell(row=2 + r_off, column=1, value=sl)
        for h in range(24):
            ws.cell(row=2 + r_off, column=2 + h, value=cf)


# ---------------------------------------------------------------------------
# Solar timing shift (--solar-shift-hours)
# ---------------------------------------------------------------------------

SOLAR_TIMING_NOTE = (
    'Solar timing shift',
    "Cambium documents its hours as hour-beginning averages (a 1:00 value covers 1:00-2:00), but its "
    "solar values behave like the output at the END of each labelled hour: in the hour in which the sun "
    "sets, Cambium shows no solar output even when the sun is up for most of that hour, and its solar "
    "day is centred about half an hour before solar noon (tests against the sun, a clear-sky PV model and "
    "EIA-930 metered solar, 2026-11-17). The utility PV, distributed PV and CSP CF columns are therefore "
    "moved later by the hours in 'Solar timing'!B3 before the timeslice averages are taken. Each hour "
    "becomes the time-weighted mean of the two source hours it overlaps, wrapping within the day; with "
    "0.5 h this is the average of the readings at the start and at the end of the hour. Every day's "
    "energy is unchanged, so the annual CF calibration to the EIA targets is unchanged.")


def shift_within_days(cf: np.ndarray, hours: float) -> np.ndarray:
    """Python twin of the shifted CF columns: move an 8,760-hour series `hours` later, each hour taken
    as constant over its hour, wrapping within each day so every day's total is unchanged."""
    if not hours:
        return np.asarray(cf, dtype=float)
    k = int(np.floor(hours))
    f = hours - k
    x = np.asarray(cf, dtype=float).reshape(-1, 24)
    return ((1 - f) * np.roll(x, k, axis=1) + f * np.roll(x, k + 1, axis=1)).ravel()


def add_solar_timing_tab(wb: openpyxl.Workbook, hours: float) -> dict:
    """Tab holding the shift. Returns absolute references to the shift, whole hours and fraction."""
    idx = wb.sheetnames.index('EIA CF targets') + 1 if 'EIA CF targets' in wb.sheetnames else len(wb.sheetnames)
    ws = wb.create_sheet(SOLAR_TIMING_TAB, idx)
    ws.column_dimensions['A'].width = 34
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 100
    ws.cell(row=1, column=1, value='Solar timing shift applied to the Cambium solar CF columns').font = SECTION_FONT
    ws.cell(row=1, column=1).fill = SECTION_FILL
    rows = [
        ('Shift later (hours)', hours, 'Edit to change. 0 = Cambium as published. 0.5 = the correction '
                                      'supported by the 2026-11-17 tests (plausible range 0.4-0.7).'),
        ('Whole hours', '=INT(B3)', 'Whole-hour part of the shift.'),
        ('Fraction of an hour', '=B3-B4', 'Weight on the earlier of the two source hours each hour overlaps.'),
    ]
    for i, (label, val, note) in enumerate(rows):
        ws.cell(row=3 + i, column=1, value=label).font = Font(bold=True)
        ws.cell(row=3 + i, column=2, value=val)
        ws.cell(row=3 + i, column=3, value=note).alignment = Alignment(wrap_text=True, vertical='top')
    ws.cell(row=7, column=1, value='Why').font = Font(bold=True)
    c = ws.cell(row=7, column=3, value=SOLAR_TIMING_NOTE[1])
    c.alignment = Alignment(wrap_text=True, vertical='top')
    ws.row_dimensions[7].height = 120
    ws.cell(row=8, column=1, value='Formula').font = Font(bold=True)
    ws.cell(row=8, column=3, value="Shifted CF for day d, hour h = (1 - fraction) x CF(d, h - whole hours) + "
                                   "fraction x CF(d, h - whole hours - 1), hours counted modulo 24 within day d.")
    t = f"'{SOLAR_TIMING_TAB}'"
    return {'shift': f'{t}!$B$3', 'whole': f'{t}!$B$4', 'frac': f'{t}!$B$5'}


def add_shifted_cf_column(ws, src_col_letter: str, dest_col: int, header: str,
                          doy_col_letter: str, hod_col_letter: str,
                          data_start: int, data_end: int, refs: dict) -> str:
    """Add a column of shifted CFs next to the hourly data (formulas). Returns its column letter."""
    letter = get_column_letter(dest_col)
    ws.cell(row=data_start - 1, column=dest_col, value=header).font = Font(bold=True, italic=True)
    rng = f'${src_col_letter}${data_start}:${src_col_letter}${data_end}'
    for r in range(data_start, data_end + 1):
        base = f'24*({doy_col_letter}{r}-1)'
        ws.cell(row=r, column=dest_col, value=(
            f"=(1-{refs['frac']})*INDEX({rng},{base}+MOD({hod_col_letter}{r}-{refs['whole']},24)+1)"
            f"+{refs['frac']}*INDEX({rng},{base}+MOD({hod_col_letter}{r}-{refs['whole']}-1,24)+1)"))
    return letter


# ---------------------------------------------------------------------------
# Python twin of the SYSHECF formulas (for --csv-out and checks)
# ---------------------------------------------------------------------------

def syshecf_table(cf: np.ndarray, row_slice: np.ndarray, row_hour: np.ndarray,
                  slices: list[str], target: float | None) -> list[list[float]]:
    """Same arithmetic as the SYSHECF-<tech> formulas:
    IFERROR(MAX(0, MIN(1, AVERAGEIFS(cf, slice, s, hour, h) * target / AVERAGE(cf))), 0)."""
    cf = np.asarray(cf, dtype=float)
    mean = cf.mean()
    table = []
    for sl in slices:
        row = []
        for h in range(24):
            m = (row_slice == sl) & (row_hour == h)
            if not m.any():
                row.append(0.0)
                continue
            v = cf[m].mean()
            if target is not None:
                if mean == 0:
                    row.append(0.0)
                    continue
                v = v * target / mean
            row.append(float(max(0.0, min(1.0, v))))
        table.append(row)
    return table


def write_syshecf_csv(path: Path, display: str, table: list[list[float]], slices: list[str]):
    """CSV in the eps-us SYSHECF layout, numbers to 10 significant figures."""
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow([display] + HOUR_COLS)
        for sl, vals in zip(slices, table):
            w.writerow([sl] + ['0' if v == 0 else f'{v:.10g}' for v in vals])


def load_clustering(total_demand, solar_gen, wind_gen) -> tuple[dict, dict]:
    """(days per slice, DOY -> slice) with the canonical slice names."""
    if cluster_days_repday is not None:
        cr = cluster_days_repday(total_demand, solar_gen, wind_gen, peak_top_n=1, max_peak_days=365)
        return dict(cr.days_per_timeslice), cr.slice_assignment.to_dict()
    print(f"  scikit-learn not installed: using the saved day list {SAVED_CLUSTERING.name}")
    saved = pd.read_csv(SAVED_CLUSTERING)
    assignment = {int(d): s for d, s in zip(saved.day_of_year, saved.slice)}
    days = {sl: sum(1 for s in assignment.values() if s == sl) for sl in SLICE_NAMES_CANONICAL}
    return days, assignment


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--out', type=Path, default=OUT, help='workbook to write')
    p.add_argument('--labels', choices=['4.0', '5.0'], default='4.0', help='timeslice names')
    p.add_argument('--csv-out', type=Path, default=None, help='also write SYSHECF CSVs (Cambium techs) here')
    p.add_argument('--solar-shift-hours', type=float, default=0.0,
                   help='move the Cambium solar series this many hours later (default 0 = as published)')
    return p.parse_args(argv)


def main(argv=None):
    global SLICES
    args = parse_args(argv)
    out_path = args.out
    shift = float(args.solar_shift_hours)
    label_of = dict(zip(SLICE_NAMES_CANONICAL, SLICE_NAMES_V5 if args.labels == '5.0' else SLICE_NAMES_CANONICAL))
    SLICES = [label_of[s] for s in SLICE_NAMES]

    # Load source raw CSVs
    print(f"[load] {CAMBIUM_HOURLY}")
    hourly_rows = _read_csv_raw(CAMBIUM_HOURLY)
    print(f"  {len(hourly_rows)} rows × {len(hourly_rows[5])} cols")
    print(f"[load] {CAMBIUM_ANNUAL}")
    annual_rows = _read_csv_raw(CAMBIUM_ANNUAL)
    print(f"  {len(annual_rows)} rows × {len(annual_rows[0])} cols")

    # Clustering — load hourly into pandas for the clustering call
    print(f"[cluster] cluster_days_repday on Cambium 2024 net load")
    src_headers = hourly_rows[5]
    col_to_idx = {h: i for i, h in enumerate(src_headers)}
    n_data = len(hourly_rows) - 6
    timestamps = []
    for r in hourly_rows[6:]:
        try:
            timestamps.append(dt.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S'))
        except (ValueError, IndexError):
            timestamps.append(None)

    def _col_as_series(name):
        idx = col_to_idx[name]
        vals = []
        for r in hourly_rows[6:]:
            try:
                vals.append(float(r[idx]))
            except (ValueError, IndexError):
                vals.append(0.0)
        return pd.Series(vals, index=pd.DatetimeIndex(timestamps), name=name)

    total_demand = _col_as_series('busbar_load')
    solar_gen = _col_as_series('upv_MWh') + _col_as_series('distpv_MWh')
    wind_gen = _col_as_series('wind-ons_MWh') + _col_as_series('wind-ofs_MWh')
    days_canonical, assignment_canonical = load_clustering(total_demand, solar_gen, wind_gen)
    days_per_slice = {label_of[s]: n for s, n in days_canonical.items()}
    slice_assignment = {d: label_of[s] for d, s in assignment_canonical.items()}
    print(f"  days_per_timeslice = {days_per_slice}")

    # Build workbook
    print(f"[build] constructing workbook")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    add_about_tab(wb, days_per_slice,
                  file_name_no_ext=out_path.stem, solar_shift_hours=shift)
    add_clustering_tab(wb, days_per_slice, slice_assignment)
    add_eia_targets_tab(wb)
    add_eia_408b_source_tab(wb, EIA_408B)
    annual_col_idx = add_cambium_annual_source_tab(wb, annual_rows)
    tech_cf_col_letter, data_start, data_end = add_cambium_hourly_source_tab(
        wb, hourly_rows, annual_col_idx, None,
    )

    # Compute the derived helper column letters in Cambium hourly source
    n_src_cols = len(hourly_rows[5])
    doy_col_letter = get_column_letter(n_src_cols + 1)
    hour_col_letter = get_column_letter(n_src_cols + 2)
    slice_col_letter = get_column_letter(n_src_cols + 3)

    # Solar timing shift: shifted CF columns after the per-tech CF columns, used by the solar tabs
    if shift:
        refs = add_solar_timing_tab(wb, shift)
        ws_h = wb['Cambium hourly source']
        next_col = n_src_cols + 4 + len(TECHS_CAMBIUM)
        for tech in SOLAR_SHIFT_TECHS:
            if tech in tech_cf_col_letter:
                tech_cf_col_letter[tech] = add_shifted_cf_column(
                    ws_h, tech_cf_col_letter[tech], next_col, f'CF_{tech}_shifted',
                    doy_col_letter, hour_col_letter, data_start, data_end, refs)
                next_col += 1
        print(f"  solar CF columns shifted {shift:+g} h later (tab '{SOLAR_TIMING_TAB}')")

    # EIA target row lookup (rows 3+ for techs)
    eia_target_rows = {tech: 3 + i for i, tech in enumerate(EIA_CF_TARGETS)}

    # Build lookup maps by tech name
    cambium_map = {t: (mwh, mw, d) for t, mwh, mw, d in TECHS_CAMBIUM}
    mirrors_map = {t: (src, d) for t, src, d in HYDROGEN_MIRRORS}
    templates_map = {t: (cf, d) for t, cf, d in TEMPLATE_TECHS}

    # Emit SYSHECF tabs in the explicit subscript-matching order.
    # Hydrogen mirrors reference their source tab cell-by-cell; the source
    # tabs come earlier in SYSHECF_TAB_ORDER so mirror references resolve.
    for tech in SYSHECF_TAB_ORDER:
        if tech in cambium_map:
            _mwh, _mw, display = cambium_map[tech]
            if tech not in tech_cf_col_letter:
                continue
            target_row = eia_target_rows.get(tech)
            add_syshecf_tech_tab(
                wb, tech, display,
                cf_col_letter=tech_cf_col_letter[tech],
                derived_doy_col_letter=doy_col_letter,
                slice_col_letter=slice_col_letter,
                hour_col_letter=hour_col_letter,
                data_start_row=data_start,
                data_end_row=data_end,
                eia_target_row=target_row,
            )
        elif tech in mirrors_map:
            source_tech, display = mirrors_map[tech]
            add_syshecf_mirror_tab(wb, tech, source_tech, display)
        elif tech in templates_map:
            cf, display = templates_map[tech]
            add_syshecf_template_tab(wb, tech, cf, display)
        else:
            print(f"  WARN: tech '{tech}' in SYSHECF_TAB_ORDER not mapped — skipping")

    out_path.parent.mkdir(exist_ok=True, parents=True)
    try:
        wb.save(out_path)
    except PermissionError:
        print(f"  ERROR: cannot write {out_path} — close it in Excel first.")
        return
    print(f"[done] wrote {out_path}")
    print(f"       sheets: {len(wb.sheetnames)}")

    if args.csv_out:
        write_csvs(args.csv_out, hourly_rows, annual_rows, slice_assignment, shift)


def write_csvs(folder: Path, hourly_rows, annual_rows, slice_assignment: dict, shift: float):
    """SYSHECF-<tech>.csv for the Cambium techs, from the same inputs and arithmetic as the workbook."""
    folder.mkdir(parents=True, exist_ok=True)
    headers = hourly_rows[5]
    data = hourly_rows[6:]
    ann_h = annual_rows[0]
    ann_2 = annual_rows[1]                                   # row 2 of the annual tab = 2025
    n = len(data)
    row_doy = np.arange(n) // 24 + 1
    row_hour = np.arange(n) % 24
    row_slice = np.array([slice_assignment.get(int(d), SLICES[0]) for d in row_doy])
    for tech, mwh_col, mw_col, display in TECHS_CAMBIUM:
        if mwh_col not in headers or mw_col not in ann_h:
            continue
        mwh = np.array([float(r[headers.index(mwh_col)]) for r in data])
        cap = float(ann_2[ann_h.index(mw_col)])
        cf = mwh / cap if cap else np.zeros(n)
        if shift and tech in SOLAR_SHIFT_TECHS:
            cf = shift_within_days(cf, shift)
        table = syshecf_table(cf, row_slice, row_hour, SLICES, EIA_CF_TARGETS.get(tech))
        write_syshecf_csv(folder / f'SYSHECF-{tech}.csv', display, table, SLICES)
    print(f"[csv] wrote SYSHECF CSVs for the Cambium techs to {folder}")


if __name__ == '__main__':
    main()
