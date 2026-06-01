"""Build the canonical SHELF Excel workbook as a self-contained derivation.

Workbook tabs (in order):
  - About
  - Clustering            — days-per-timeslice + DOY → slice (editable)
  - Annual category totals — per-category 2025 annual TWh (parameter tab)
  - ResStock national source — TZ-corrected aggregation across 49 states
  - ComStock national source — TZ-corrected aggregation across 51 state folders
  - EFS source            — filtered Reference/Moderate Industrial+Transport
  - Cambium hourly source — Cambium 2024 MidCase national 2025 (clustering ref)
  - SHELF-days-per-timeslice (output)
  - SHELF-<category> × 22 (outputs, dark blue) in subscript order
  - SHELF-datacenters (output, dark blue) — flat 24/7

Target file:
  C:/Users/RobbieOrvis/Models/US/Models/eps-us/InputData/elec/SHELF/
    Seasonal Hourly Equipment Load Factors by End Use.xlsx

Run:
    python scripts/build_shelf_workbook.py
"""
from __future__ import annotations
import csv
import sys
import zipfile
import io
from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from state_pipeline.builders.clustering import SLICE_NAMES
from state_pipeline.builders.clustering_repday import cluster_days_repday
from state_pipeline.readers.resstock_reader import read_resstock_hourly
from state_pipeline.readers.comstock_reader import read_comstock_hourly

CAMBIUM_HOURLY = ROOT / "data" / "cambium24_midcase_national" / "Cambium24_MidCase_hourly_usa_2025.csv"
EFS_ZIP        = ROOT / "data" / "efs" / "EFSLoadProfile_Reference_Moderate.zip"
RESSTOCK_ROOT  = Path(r"C:\Users\RobbieOrvis\Models\ResStock SHELF\ResStock_Upgrade0")
COMSTOCK_ROOT  = Path(r"C:\Users\RobbieOrvis\Models\ResStock SHELF\ComStock_tmy_release1")

CACHE_DIR = ROOT / "data" / "national_aggregated"

OUT = Path(
    r"C:\Users\RobbieOrvis\Models\US\Models\eps-us\InputData\elec\SHELF"
    r"\Seasonal Hourly Equipment Load Factors by End Use.xlsx"
)

# State LST → ET offsets (matches rebuild_us_national_v2.py)
STATE_TZ_OFFSET_TO_ET = {
    'CT': 0, 'DE': 0, 'DC': 0, 'FL': 0, 'GA': 0, 'IN': 0, 'KY': 0, 'ME': 0,
    'MD': 0, 'MA': 0, 'MI': 0, 'NH': 0, 'NJ': 0, 'NY': 0, 'NC': 0, 'OH': 0,
    'PA': 0, 'RI': 0, 'SC': 0, 'VT': 0, 'VA': 0, 'WV': 0,
    'AL': 1, 'AR': 1, 'IA': 1, 'IL': 1, 'KS': 1, 'LA': 1, 'MN': 1, 'MS': 1,
    'MO': 1, 'NE': 1, 'ND': 1, 'OK': 1, 'SD': 1, 'TN': 1, 'TX': 1, 'WI': 1,
    'AZ': 2, 'CO': 2, 'ID': 2, 'MT': 2, 'NM': 2, 'UT': 2, 'WY': 2,
    'CA': 3, 'NV': 3, 'OR': 3, 'WA': 3,
    'AK': 4, 'HI': 5,
}

# SHELF output category order (from existing EPS-test-folder file, plus datacenters).
SHELF_OUTPUT_ORDER = [
    'days-per-timeslice',
    'residential-heating',
    'residential-cooling',
    'residential-envelope',
    'residential-lighting',
    'residential-appliances',
    'residential-other',
    'commercial-heating',
    'commercial-cooling',
    'commercial-envelope',
    'commercial-lighting',
    'commercial-appliances',
    'commercial-other',
    'LDVs',
    'HDVs',
    'aircraft',
    'rail',
    'ships',
    'motorbikes',
    'industry',
    'district-heat-hydrogen',
    'geoeng',
    'datacenters',
]

# Categories sourced from ResStock (column name in aggregated CSV)
RESSTOCK_CATS = ['residential-heating', 'residential-cooling', 'residential-lighting',
                 'residential-appliances', 'residential-other']
COMSTOCK_CATS = ['commercial-heating', 'commercial-cooling', 'commercial-lighting',
                 'commercial-appliances', 'commercial-other']
# EFS categories — mapped from EFS Industrial + Transportation subsectors
EFS_CATS = ['industry', 'LDVs', 'HDVs', 'rail']
# Always-zero categories (EPS convention)
ZERO_CATS = ['residential-envelope', 'commercial-envelope',
             'aircraft', 'ships', 'motorbikes',
             'district-heat-hydrogen', 'geoeng']
# Flat 24/7 categories
FLAT_CATS = ['datacenters']

# Approximate 2025 annual TWh per category for the AEO/BCEU "Annual category totals"
# tab. These are placeholders the user can edit. They reflect typical US national
# AEO Reference Case values; do NOT propagate into the LF math.
ANNUAL_TWH_DEFAULTS = {
    'residential-heating':    150.0,
    'residential-cooling':    270.0,
    'residential-envelope':     0.0,
    'residential-lighting':   120.0,
    'residential-appliances': 600.0,
    'residential-other':      360.0,
    'commercial-heating':      80.0,
    'commercial-cooling':     190.0,
    'commercial-envelope':      0.0,
    'commercial-lighting':    190.0,
    'commercial-appliances':  400.0,
    'commercial-other':       640.0,
    'industry':              1000.0,
    'LDVs':                    50.0,
    'HDVs':                     5.0,
    'aircraft':                 0.0,
    'rail':                     8.0,
    'ships':                    0.0,
    'motorbikes':               0.0,
    'district-heat-hydrogen':   0.0,
    'geoeng':                   0.0,
    'datacenters':            245.0,
}

ANNUAL_TWH_SOURCES = {
    'residential-heating':    'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential heating, electricity',
    'residential-cooling':    'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential cooling, electricity',
    'residential-envelope':   'EPS convention: 0 in start year',
    'residential-lighting':   'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential lighting, electricity',
    'residential-appliances': 'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential appl + water heat, electricity',
    'residential-other':      'bldgs/BCEU/BAU Components Energy Use.xlsx — urban+rural residential other, electricity',
    'commercial-heating':     'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial heating, electricity',
    'commercial-cooling':     'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial cooling, electricity',
    'commercial-envelope':    'EPS convention: 0 in start year',
    'commercial-lighting':    'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial lighting, electricity',
    'commercial-appliances':  'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial appliances, electricity',
    'commercial-other':       'bldgs/BCEU/BAU Components Energy Use.xlsx — commercial other, electricity',
    'industry':               'indst/BIFUbC/BIFUbC-electricity.csv (AEO industrial subsectors aggregated)',
    'LDVs':                   'trans calculator (AEO transport, light-duty vehicles)',
    'HDVs':                   'trans calculator (AEO transport, medium + heavy-duty trucks)',
    'aircraft':               'EPS convention: 0 in start year',
    'rail':                   'trans calculator (~40% of EFS "other transport")',
    'ships':                  'EPS convention: 0 in start year',
    'motorbikes':             'EPS convention: 0 in start year',
    'district-heat-hydrogen': 'EPS convention: 0 in start year (ramps post-2030)',
    'geoeng':                 'EPS convention: 0 in start year (ramps post-2030)',
    'datacenters':            'BCEU/AEO data-center electricity (~245 TWh in 2025 per EIA)',
}

SLICES = list(SLICE_NAMES)
HOUR_COLS = [f'Hour{h}' for h in range(24)]

HEADER_FILL = PatternFill(start_color='305496', end_color='305496', fill_type='solid')
HEADER_FONT = Font(bold=True, color='FFFFFF')
SECTION_FILL = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
SECTION_FONT = Font(bold=True)
PURPOSE_FILL = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
OUTPUT_TAB_COLOR = '1F3864'
LEFT_TOP_WRAP = Alignment(horizontal='left', vertical='top', wrap_text=True)


# ---------------------------------------------------------------------------
# Aggregation (with caching)
# ---------------------------------------------------------------------------

def _tz_correct(df: pd.DataFrame, state: str) -> pd.DataFrame:
    offset = STATE_TZ_OFFSET_TO_ET.get(state, 0)
    if offset == 0:
        return df
    out = df.copy()
    for col in out.columns:
        out[col] = np.roll(out[col].values, offset)
    return out


def aggregate_resstock_cached() -> pd.DataFrame:
    cache = CACHE_DIR / "resstock_national_hourly.csv"
    if cache.exists():
        print(f"  [resstock] using cache {cache}")
        return pd.read_csv(cache, index_col=0, parse_dates=True)
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    state_dirs = sorted([p for p in RESSTOCK_ROOT.glob('state=*') if p.is_dir()])
    print(f"  [resstock] aggregating {len(state_dirs)} states (TZ-corrected to ET)...")
    combined: pd.DataFrame | None = None
    for sd in state_dirs:
        state = sd.name.split('=')[1]
        try:
            sh = read_resstock_hourly(str(sd))
        except Exception as e:
            print(f"    SKIP {state}: {e}")
            continue
        sh = _tz_correct(sh, state)
        combined = sh.copy() if combined is None else combined.add(sh, fill_value=0)
        print(f"    + {state}", flush=True)
    combined.to_csv(cache)
    print(f"  [resstock] cached -> {cache}")
    return combined


def aggregate_comstock_cached() -> pd.DataFrame:
    cache = CACHE_DIR / "comstock_national_hourly.csv"
    if cache.exists():
        print(f"  [comstock] using cache {cache}")
        return pd.read_csv(cache, index_col=0, parse_dates=True)
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    state_dirs = sorted([p for p in COMSTOCK_ROOT.iterdir() if p.is_dir() and len(p.name) == 2])
    print(f"  [comstock] aggregating {len(state_dirs)} states (TZ-corrected to ET)...")
    combined: pd.DataFrame | None = None
    for sd in state_dirs:
        state = sd.name
        try:
            sh = read_comstock_hourly(str(sd))
        except Exception as e:
            print(f"    SKIP {state}: {e}")
            continue
        sh = _tz_correct(sh, state)
        combined = sh.copy() if combined is None else combined.add(sh, fill_value=0)
        print(f"    + {state}", flush=True)
    combined.to_csv(cache)
    print(f"  [comstock] cached -> {cache}")
    return combined


def load_efs_filtered(year: int = 2024) -> pd.DataFrame:
    """Return 8760×N DataFrame of EFS national hourly demand by subsector,
    filtered to Reference/Moderate/year. Columns: timestamp index, plus
    industry / LDVs / HDVs / rail derived from EFS subsectors.
    """
    print(f"  [efs] loading + filtering...")
    try:
        import zipfile_deflate64  # noqa: F401  (registers Deflate64 codec on import)
    except ImportError:
        raise ImportError("EFS zip uses Deflate64; install with `pip install zipfile_deflate64`")
    needed = ['Electrification', 'TechnologyAdvancement', 'Year',
              'LocalHourID', 'Sector', 'Subsector', 'LoadMW']
    frames = []
    with zipfile.ZipFile(EFS_ZIP) as zf:
        member = [n for n in zf.namelist() if n.endswith('.csv')][0]
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding='utf-8-sig', newline='')
            reader = pd.read_csv(text, usecols=needed, chunksize=500_000)
            for chunk in reader:
                m = ((chunk['Electrification'].str.lower() == 'reference')
                     & (chunk['TechnologyAdvancement'].str.lower() == 'moderate')
                     & (pd.to_numeric(chunk['Year'], errors='coerce') == year))
                f = chunk.loc[m]
                if f.empty:
                    continue
                frames.append(f.groupby(['LocalHourID', 'Sector', 'Subsector'],
                                        as_index=False)['LoadMW'].sum())
    agg = pd.concat(frames).groupby(['LocalHourID', 'Sector', 'Subsector'],
                                     as_index=False)['LoadMW'].sum()
    piv = agg.pivot_table(index='LocalHourID', columns=['Sector', 'Subsector'],
                          values='LoadMW', aggfunc='sum', fill_value=0.0).sort_index()
    ts = pd.date_range('2018-01-01', periods=8760, freq='h')
    piv.index = ts

    def col(sec, sub):
        return piv[(sec, sub)].astype(float) if (sec, sub) in piv.columns else pd.Series(0.0, index=ts)

    out = pd.DataFrame(index=ts)
    out['industry'] = (col('Industrial', 'machine drives')
                       + col('Industrial', 'process heat')
                       + col('Industrial', 'other'))
    out['LDVs'] = col('Transportation', 'light-duty vehicles')
    out['HDVs'] = (col('Transportation', 'medium-duty trucks')
                   + col('Transportation', 'heavy-duty trucks'))
    out['rail'] = col('Transportation', 'other') * 0.40
    return out


def load_cambium_raw_rows() -> list[list[str]]:
    with open(CAMBIUM_HOURLY, newline='') as f:
        return list(csv.reader(f))


def load_cambium_for_clustering() -> pd.DataFrame:
    rows = load_cambium_raw_rows()
    headers = rows[5]
    idx = {h: i for i, h in enumerate(headers)}
    timestamps, vals = [], {'busbar_load': [], 'upv_MWh': [], 'distpv_MWh': [],
                            'wind-ons_MWh': [], 'wind-ofs_MWh': []}
    for r in rows[6:]:
        try:
            ts = dt.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S')
        except (ValueError, IndexError):
            continue
        timestamps.append(ts)
        for c in vals:
            try:
                vals[c].append(float(r[idx[c]]))
            except (ValueError, IndexError):
                vals[c].append(0.0)
    return pd.DataFrame(vals, index=pd.DatetimeIndex(timestamps))


# ---------------------------------------------------------------------------
# About tab + parameter/source tabs
# ---------------------------------------------------------------------------

def add_about_tab(wb: openpyxl.Workbook, days_per_slice: dict, file_name_no_ext: str):
    ws = wb.create_sheet('About', 0)
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 110

    ws.cell(1, 1, f'SHELF {file_name_no_ext}').font = Font(bold=True)
    ws.cell(3, 1, 'Sources:').font = Font(bold=True)

    sources = [
        {
            'purpose': 'Residential Hourly End-Use Load Profiles by State',
            'source':  'NREL',
            'publication': 'NREL End-Use Load Profiles for the U.S. Building Stock (ResStock)',
            'year':    2024,
            'url':     'https://www.nrel.gov/buildings/end-use-load-profiles.html',
            'info':    '49 state files at ResStock SHELF/ResStock_Upgrade0/state=XX/. Each state '
                      'file is 15-min interval data in Local Standard Time (no DST). National '
                      'aggregation: TZ-correct each state forward to ET (np.roll by hours-LST-to-ET), '
                      'sum residential end-use columns (heating + hp_bkup, cooling + fans, etc.) into '
                      'five SHELF categories, downsample to hourly. Cached to '
                      'data/national_aggregated/resstock_national_hourly.csv.',
        },
        {
            'purpose': 'Commercial Hourly End-Use Load Profiles by State',
            'source':  'NREL',
            'publication': 'NREL End-Use Load Profiles for the U.S. Building Stock (ComStock TMY)',
            'year':    2024,
            'url':     'https://www.nrel.gov/buildings/end-use-load-profiles.html',
            'info':    '51 state folders at ResStock SHELF/ComStock_tmy_release1/XX/. Same TZ '
                      'correction as ResStock; commercial end-uses aggregated into five SHELF '
                      'categories per the AEO BCEU mapping. Cached to '
                      'data/national_aggregated/comstock_national_hourly.csv.',
        },
        {
            'purpose': 'Industrial and Transportation Hourly Load Profiles (National)',
            'source':  'NREL',
            'publication': 'NREL Electrification Futures Study (EFS) Load Profiles',
            'year':    2018,
            'url':     'https://data.nrel.gov/submissions/126',
            'info':    'Reference scenario, Moderate technology advancement, year 2024 EFS vintage. '
                      'Industrial: machine drives + process heat + other. Transportation: LDV / MDV+HDV / '
                      'rail (≈40% of other-transport). File: data/efs/EFSLoadProfile_Reference_Moderate.zip.',
        },
        {
            'purpose': 'Net-Load Clustering Reference (for K6/H24 representative-day slicing)',
            'source':  'NREL',
            'publication': 'NREL Cambium Scenarios 2024',
            'year':    2024,
            'url':     'https://www.nrel.gov/analysis/cambium.html',
            'info':    'MidCase scenario, weather year 2012, USA national, 2025 model year. Used '
                      'only for the clustering (assigning each day-of-year to one of six timeslices). '
                      'SHELF outputs are derived from ResStock/ComStock/EFS, not Cambium. File: '
                      'Cambium24_MidCase_hourly_usa_2025.csv pasted into "Cambium hourly source" tab.',
        },
    ]

    cur = 3
    for src in sources:
        c = ws.cell(cur, 2, src['purpose'])
        c.font = Font(bold=True); c.fill = PURPOSE_FILL; c.alignment = LEFT_TOP_WRAP
        for off, val in enumerate([src['source'], src['publication'], src['year']], start=1):
            ws.cell(cur + off, 2, val).alignment = LEFT_TOP_WRAP
        u = ws.cell(cur + 4, 2, src['url'])
        u.hyperlink = src['url']; u.font = Font(color='0563C1', underline='single')
        u.alignment = LEFT_TOP_WRAP
        ws.cell(cur + 5, 2, src['info']).alignment = LEFT_TOP_WRAP
        cur += 7

    notes_row = cur + 1
    ws.cell(notes_row, 1, 'Notes:').font = Font(bold=True)

    sp = days_per_slice.get('Summer Peak', 0)
    wp = days_per_slice.get('Winter Peak', 0)
    today = dt.date.today().isoformat()

    notes_lines = [
        ('Methodology overview',
         'This workbook produces SHELF (Seasonal Hourly Equipment Load Factor) tables for the '
         'EPS Vensim model. Each output tab gives a 6 (timeslice) × 24 (hour) load-factor table for one '
         'demand category — the ratio of demand in that slice/hour to total annual demand. '
         'Edit the source tabs or the Clustering tab and all SHELF outputs recompute via formulas.'),
        ('Source data layout',
         'Each hourly source tab pastes 8,760 rows of aggregated national hourly demand by category, '
         'with derived day_of_year / hour_of_day / slice columns at the right. Slice is resolved via '
         'VLOOKUP against the Clustering tab. The Cambium hourly source tab is included for '
         'traceability of the clustering (75 source columns × 8,760 rows pasted verbatim).'),
        ('Clustering',
         f'K6/H24 representative-day clustering on Cambium 2024 net load. Optimizer self-terminated '
         f'at SP={sp} days, WP={wp} days. Algorithm: cluster_days_repday in '
         f'state_pipeline/builders/clustering_repday.py. The Clustering tab has the editable per-day '
         f'slice assignment used by all source tabs.'),
        ('SHELF derivation',
         'For each non-zero category: LF[slice, hour] = AVERAGEIFS(demand, slice_col, "<slice>", '
         'hour_col, <hour>) / SUM(demand). Sum across all (slice, hour) × days_per_slice = 1.0 per '
         'category by construction.'),
        ('Zero categories',
         'residential-envelope, commercial-envelope, aircraft, ships, motorbikes, district-heat-hydrogen, '
         'geoeng — all zero in start year per EPS convention. May ramp up in later years for some '
         'scenarios; edit the tab directly to override.'),
        ('Datacenters',
         'Flat 24/7 LF = 1/8760 in every cell. Data centers run continuously; this lets BCEU/AEO '
         'datacenter annual energy contribute to every hour including peak.'),
        ('Annual category totals',
         'The "Annual category totals" tab documents the expected annual TWh per category and the '
         'BCEU/AEO source variable. These values do NOT propagate into the LF math (LFs are '
         'self-normalized within each category). They are reference inputs that help calibrate against '
         'expected model peak load.'),
        ('Tab order',
         'SHELF output tabs follow the EPS subscript order from the EPS-test-folder reference file: '
         'days-per-timeslice, residential-{heating,cooling,envelope,lighting,appliances,other}, '
         'commercial-{...}, LDVs, HDVs, aircraft, rail, ships, motorbikes, industry, '
         'district-heat-hydrogen, geoeng, datacenters.'),
        ('Run metadata',
         f'country: UnitedStates; clustering input: Cambium 2024 MidCase 2025 (weather year 2012); '
         f'EFS vintage: 2024; ResStock/ComStock: 2024 release; built: {today}; '
         f'build script: scripts/build_shelf_workbook.py.'),
        ('Caveats',
         'All values are inputs for staff review. Verify against NREL ResStock, ComStock, EFS, '
         'Cambium 2024, and the project methodology (CLAUDE.md at project root) before being used '
         'in any work product.'),
    ]
    for i, (label, text) in enumerate(notes_lines):
        r = notes_row + 1 + i
        ws.cell(r, 1, label).font = Font(bold=True)
        ws.cell(r, 2, text).alignment = LEFT_TOP_WRAP
        ws.row_dimensions[r].height = max(30, 18 * (1 + len(text) // 110))


def add_clustering_tab(wb, days_per_slice, slice_assignment):
    ws = wb.create_sheet('Clustering')
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 8
    ws.column_dimensions['D'].width = 8
    ws.column_dimensions['E'].width = 14
    ws.cell(1, 1, 'Days per timeslice (snapshot)').font = SECTION_FONT
    ws.cell(1, 1).fill = SECTION_FILL
    ws.cell(2, 1, 'Slice').font = HEADER_FONT
    ws.cell(2, 1).fill = HEADER_FILL
    ws.cell(2, 2, 'Days').font = HEADER_FONT
    ws.cell(2, 2).fill = HEADER_FILL
    for i, sl in enumerate(SLICES):
        ws.cell(3 + i, 1, sl)
        ws.cell(3 + i, 2, int(days_per_slice.get(sl, 0)))
    ws.cell(1, 4, 'DOY → slice (edit to reassign days)').font = SECTION_FONT
    ws.cell(1, 4).fill = SECTION_FILL
    ws.cell(2, 4, 'DOY').font = HEADER_FONT
    ws.cell(2, 4).fill = HEADER_FILL
    ws.cell(2, 5, 'Slice').font = HEADER_FONT
    ws.cell(2, 5).fill = HEADER_FILL
    for doy in range(1, 366):
        ws.cell(2 + doy, 4, doy)
        ws.cell(2 + doy, 5, slice_assignment.get(doy, 'Winter'))


def add_annual_totals_tab(wb):
    ws = wb.create_sheet('Annual category totals')
    ws.column_dimensions['A'].width = 26
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 90
    ws.cell(1, 1, 'Annual TWh per SHELF category (start year, reference)') \
      .font = SECTION_FONT
    ws.cell(1, 1).fill = SECTION_FILL
    ws.cell(2, 1, 'Category').font = HEADER_FONT
    ws.cell(2, 1).fill = HEADER_FILL
    ws.cell(2, 2, 'Annual TWh').font = HEADER_FONT
    ws.cell(2, 2).fill = HEADER_FILL
    ws.cell(2, 3, 'Source file / variable').font = HEADER_FONT
    ws.cell(2, 3).fill = HEADER_FILL
    for i, cat in enumerate([c for c in SHELF_OUTPUT_ORDER if c != 'days-per-timeslice']):
        ws.cell(3 + i, 1, cat)
        ws.cell(3 + i, 2, ANNUAL_TWH_DEFAULTS.get(cat, 0.0))
        ws.cell(3 + i, 3, ANNUAL_TWH_SOURCES.get(cat, '')).alignment = LEFT_TOP_WRAP


def _add_hourly_source_tab(
    wb, name: str, df: pd.DataFrame,
    timestamps: list, slice_assignment: dict,
) -> tuple[int, dict[str, str], str, str]:
    """Write a tab with timestamp + per-category cols + derived DOY/hour/slice.
    Returns (data_start_row, {category: col_letter}, slice_col_letter, hour_col_letter).
    """
    ws = wb.create_sheet(name)
    cols = list(df.columns)
    # Row 1: headers
    ws.cell(1, 1, 'timestamp').font = Font(bold=True)
    for i, c in enumerate(cols):
        ws.cell(1, 2 + i, c).font = Font(bold=True)
    n_main = 1 + len(cols)  # timestamp + categories
    doy_col = n_main + 1
    hour_col = n_main + 2
    slice_col = n_main + 3
    ws.cell(1, doy_col, 'day_of_year').font = Font(bold=True, italic=True)
    ws.cell(1, hour_col, 'hour_of_day').font = Font(bold=True, italic=True)
    ws.cell(1, slice_col, 'slice').font = Font(bold=True, italic=True)

    # Data rows
    for i in range(len(df)):
        row = 2 + i
        ts = timestamps[i]
        ws.cell(row, 1, ts.strftime('%Y-%m-%d %H:%M'))
        for j, c in enumerate(cols):
            ws.cell(row, 2 + j, float(df.iloc[i, j]))
        doy = (i // 24) + 1
        ws.cell(row, doy_col, doy)
        ws.cell(row, hour_col, i % 24)
        doy_letter = get_column_letter(doy_col)
        ws.cell(row, slice_col,
                value=f"=VLOOKUP({doy_letter}{row},Clustering!$D$3:$E$367,2,FALSE)")

    # Column widths
    ws.column_dimensions['A'].width = 18
    for c in range(2, slice_col + 1):
        ws.column_dimensions[get_column_letter(c)].width = 16
    ws.freeze_panes = 'B2'

    # Build map: category → column letter
    cat_col = {c: get_column_letter(2 + i) for i, c in enumerate(cols)}
    return 2, cat_col, get_column_letter(slice_col), get_column_letter(hour_col)


def add_cambium_source_tab(wb, slice_assignment):
    """Paste full Cambium source verbatim with derived DOY/hour/slice columns."""
    rows = load_cambium_raw_rows()
    ws = wb.create_sheet('Cambium hourly source')
    n_src_cols = len(rows[5])
    print(f"  [cambium] writing {len(rows)} rows × {n_src_cols} src cols...")
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, val in enumerate(row, start=1):
            cell_val = _try_float(val) if r_idx >= 7 and c_idx >= 2 else val
            ws.cell(r_idx, c_idx, cell_val)
    # Add derived columns at the right; data starts row 7
    data_start = 7
    data_end = len(rows)
    doy_col = n_src_cols + 1
    hour_col = n_src_cols + 2
    slice_col = n_src_cols + 3
    ws.cell(6, doy_col, 'day_of_year').font = Font(bold=True, italic=True)
    ws.cell(6, hour_col, 'hour_of_day').font = Font(bold=True, italic=True)
    ws.cell(6, slice_col, 'slice').font = Font(bold=True, italic=True)
    doy_letter = get_column_letter(doy_col)
    for i in range(data_end - data_start + 1):
        r = data_start + i
        ws.cell(r, doy_col, (i // 24) + 1)
        ws.cell(r, hour_col, i % 24)
        ws.cell(r, slice_col,
                value=f"=VLOOKUP({doy_letter}{r},Clustering!$D$3:$E$367,2,FALSE)")
    for c in range(1, min(slice_col, 50) + 1):
        ws.column_dimensions[get_column_letter(c)].width = 14
    ws.freeze_panes = 'B7'


def _try_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return s


# ---------------------------------------------------------------------------
# Output tabs
# ---------------------------------------------------------------------------

def add_days_per_timeslice_tab(wb, days_per_slice):
    """SHELF-days-per-timeslice tab. Same format as the CSV file."""
    ws = wb.create_sheet('SHELF-days-per-timeslice')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 22
    ws.cell(1, 1, 'Unit: days')
    ws.cell(1, 2, 'Days per Timeslice')
    for i, sl in enumerate(SLICES):
        ws.cell(2 + i, 1, sl)
        ws.cell(2 + i, 2, int(days_per_slice.get(sl, 0)))


def add_shelf_output_tab(
    wb, category: str, source_tab: str, cat_col_letter: str,
    slice_col_letter: str, hour_col_letter: str,
    data_start: int, data_end: int,
):
    """Build a SHELF-<category> tab using AVERAGEIFS / SUM."""
    ws = wb.create_sheet(f'SHELF-{category}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 16
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12

    # Header row
    ws.cell(1, 1, 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)')
    for h, name in enumerate(HOUR_COLS):
        ws.cell(1, 2 + h, name)

    cf_range = f"'{source_tab}'!${cat_col_letter}${data_start}:${cat_col_letter}${data_end}"
    slice_range = f"'{source_tab}'!${slice_col_letter}${data_start}:${slice_col_letter}${data_end}"
    hour_range = f"'{source_tab}'!${hour_col_letter}${data_start}:${hour_col_letter}${data_end}"

    for r_off, sl in enumerate(SLICES):
        ws.cell(2 + r_off, 1, sl)
        for h in range(24):
            avg = f"AVERAGEIFS({cf_range},{slice_range},$A{2+r_off},{hour_range},{h})"
            tot = f"SUM({cf_range})"
            formula = f"=IFERROR({avg}/{tot},0)"
            ws.cell(2 + r_off, 2 + h, formula)


def add_zero_tab(wb, category: str):
    """SHELF tab with all zeros (envelope, aircraft, etc.)."""
    ws = wb.create_sheet(f'SHELF-{category}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 16
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12
    ws.cell(1, 1, 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)')
    for h, name in enumerate(HOUR_COLS):
        ws.cell(1, 2 + h, name)
    for r_off, sl in enumerate(SLICES):
        ws.cell(2 + r_off, 1, sl)
        for h in range(24):
            ws.cell(2 + r_off, 2 + h, 0.0)


def add_flat_tab(wb, category: str):
    """SHELF tab with flat 1/8760 in every cell (datacenters)."""
    ws = wb.create_sheet(f'SHELF-{category}')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 16
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12
    ws.cell(1, 1, 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)')
    for h, name in enumerate(HOUR_COLS):
        ws.cell(1, 2 + h, name)
    flat_val = 1.0 / 8760.0
    for r_off, sl in enumerate(SLICES):
        ws.cell(2 + r_off, 1, sl)
        for h in range(24):
            ws.cell(2 + r_off, 2 + h, flat_val)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"[1/5] Aggregating ResStock + ComStock (cached)")
    res = aggregate_resstock_cached()
    com = aggregate_comstock_cached()
    print(f"  [resstock] shape {res.shape}; [comstock] shape {com.shape}")

    print(f"[2/5] Loading EFS national (filtered)")
    efs = load_efs_filtered(year=2024)
    print(f"  [efs] shape {efs.shape}")

    print(f"[3/5] Clustering on Cambium 2024 net load")
    cambium_df = load_cambium_for_clustering()
    cr = cluster_days_repday(
        cambium_df['busbar_load'],
        cambium_df['upv_MWh'] + cambium_df['distpv_MWh'],
        cambium_df['wind-ons_MWh'] + cambium_df['wind-ofs_MWh'],
        peak_top_n=1, max_peak_days=365,
    )
    print(f"  days_per_timeslice = {cr.days_per_timeslice}")
    slice_assignment = cr.slice_assignment.to_dict()

    print(f"[4/5] Building workbook")
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    add_about_tab(wb, cr.days_per_timeslice, file_name_no_ext=OUT.stem)
    add_clustering_tab(wb, cr.days_per_timeslice, slice_assignment)
    add_annual_totals_tab(wb)

    # All hourly sources use the same 2018 calendar
    ts2018 = pd.date_range('2018-01-01', periods=8760, freq='h').to_list()

    # ResStock source
    res_aligned = res.reset_index(drop=True).iloc[:8760].copy()
    _, res_cat_col, res_slice_col, res_hour_col = _add_hourly_source_tab(
        wb, 'ResStock national source', res_aligned, ts2018, slice_assignment,
    )
    # ComStock source
    com_aligned = com.reset_index(drop=True).iloc[:8760].copy()
    _, com_cat_col, com_slice_col, com_hour_col = _add_hourly_source_tab(
        wb, 'ComStock national source', com_aligned, ts2018, slice_assignment,
    )
    # EFS source
    efs_aligned = efs.reset_index(drop=True).iloc[:8760].copy()
    _, efs_cat_col, efs_slice_col, efs_hour_col = _add_hourly_source_tab(
        wb, 'EFS source', efs_aligned, ts2018, slice_assignment,
    )

    # Cambium source (full raw paste, clustering reference)
    add_cambium_source_tab(wb, slice_assignment)

    # ---- Output tabs ----
    print(f"  building {len(SHELF_OUTPUT_ORDER)} output tabs")
    for cat in SHELF_OUTPUT_ORDER:
        if cat == 'days-per-timeslice':
            add_days_per_timeslice_tab(wb, cr.days_per_timeslice)
            wb['SHELF-days-per-timeslice'].sheet_properties.tabColor = OUTPUT_TAB_COLOR
            continue
        if cat in ZERO_CATS:
            add_zero_tab(wb, cat)
            continue
        if cat in FLAT_CATS:
            add_flat_tab(wb, cat)
            continue
        if cat in RESSTOCK_CATS:
            add_shelf_output_tab(wb, cat, 'ResStock national source',
                                  res_cat_col[cat], res_slice_col, res_hour_col,
                                  data_start=2, data_end=8761)
        elif cat in COMSTOCK_CATS:
            add_shelf_output_tab(wb, cat, 'ComStock national source',
                                  com_cat_col[cat], com_slice_col, com_hour_col,
                                  data_start=2, data_end=8761)
        elif cat in EFS_CATS:
            add_shelf_output_tab(wb, cat, 'EFS source',
                                  efs_cat_col[cat], efs_slice_col, efs_hour_col,
                                  data_start=2, data_end=8761)
        else:
            print(f"  WARN: category '{cat}' not mapped; writing zeros")
            add_zero_tab(wb, cat)

    print(f"[5/5] Saving workbook")
    OUT.parent.mkdir(exist_ok=True, parents=True)
    try:
        wb.save(OUT)
    except PermissionError:
        print(f"  ERROR: cannot write {OUT} — close it in Excel first.")
        return
    print(f"[done] wrote {OUT}")
    print(f"       sheets: {len(wb.sheetnames)} total")


if __name__ == '__main__':
    main()
