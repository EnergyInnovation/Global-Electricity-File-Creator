"""Build self-contained SHELF + SYSHECF Excel workbooks for the USA run of the
international pipeline (run_pipeline.py), following the build-input-xlsx
pattern: raw hourly source data pasted into source tabs, all output values
derived via Excel formulas, About tab documenting sources + methodology.

The math mirrors the pipeline's EPS export exactly (SLICE MEANS — the form
CLAUDE.md §6 specifies and the canonical eps-us workbooks use; see
DECISIONS.md 2026-08-12 for why representative-day picks were replaced):
  SHELF   LF[slice, hour] = AVERAGEIFS(col, slice, hour) / SUM(col)
  SYSHECF CF[slice, hour] = AVERAGEIFS(cf, slice, hour), clamped [0,1]
                            (x0.70 dist PV)
  template_split cats     = aggregate LF x peer-template weight per cell
  'sum' cats (HDVs)       = (avg1 + avg2) / (SUM(v1) + SUM(v2))

Inputs (created from the verified 2026-07-07 master-parity run captures if the
workbook_sources CSVs don't exist yet):
  output/UnitedStates_timeslice_results_EPS/workbook_sources/
    demand_hourly_source.csv   cf_hourly_source.csv   clustering.csv

Outputs (same canonical names the legacy export uses, in the run's EPS dir —
NOT eps-us; the canonical US EPS inputs come from the Cambium-based national
pipeline):
  output/UnitedStates_timeslice_results_EPS/
    Seasonal Hourly Equipment Load Factors by End Use.xlsx
    Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx

Run:
    python scripts/build_us_run_workbooks.py
Then verify:
    python scripts/verify_us_run_workbooks.py
"""
from __future__ import annotations
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

EPS_DIR = ROOT / 'output' / 'UnitedStates_timeslice_results_EPS'
SRC_DIR = EPS_DIR / 'workbook_sources'
TEMPLATE_SHELF_DIR = ROOT.parent / 'EPS Structure Testing' / 'InputData' / 'elec' / 'SHELF'

SHELF_OUT = EPS_DIR / 'Seasonal Hourly Equipment Load Factors by End Use.xlsx'
SYSHECF_OUT = EPS_DIR / 'Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx'

SLICES = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
HOUR_COLS = [f'Hour{h}' for h in range(24)]
SHELF_UNIT = 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)'
SYSHECF_UNIT = 'Unit: dimensionless (capacity factor)'

# Demand source columns pasted into the SHELF source tab (raw pipeline names).
DEMAND_COLS = [
    'residential_heating', 'residential_cooling', 'residential_lighting',
    'residential_appliances', 'residential_other',
    'service_heating', 'service_cooling', 'service_waterheating', 'service_other',
    'transport_ldv', 'transport_mdv', 'transport_hdv', 'transport_other',
    'industry_total',
]

# SHELF output spec, mirroring EPS_SHELF_FILE_MAP as resolved for this US run
# (see EPS_export_coverage.csv). kinds: direct / sum / split / zeros / flat.
SHELF_SPECS = [
    ('days-per-timeslice',      'days',   None),
    ('residential-heating',     'direct', 'residential_heating'),
    ('residential-cooling',     'direct', 'residential_cooling'),
    ('residential-envelope',    'zeros',  None),
    ('residential-lighting',    'direct', 'residential_lighting'),
    ('residential-appliances',  'direct', 'residential_appliances'),
    ('residential-other',       'direct', 'residential_other'),
    ('commercial-heating',      'direct', 'service_heating'),
    ('commercial-cooling',      'direct', 'service_cooling'),
    ('commercial-envelope',     'zeros',  None),
    ('commercial-lighting',     'split',  None),
    ('commercial-appliances',   'split',  None),
    ('commercial-other',        'split',  None),
    ('LDVs',                    'direct', 'transport_ldv'),
    ('HDVs',                    'sum',    ('transport_hdv', 'transport_mdv')),
    ('aircraft',                'split',  None),
    ('rail',                    'split',  None),
    ('ships',                   'split',  None),
    ('motorbikes',              'split',  None),
    ('industry',                'direct', 'industry_total'),
    ('district-heat-hydrogen',  'direct', 'industry_total'),
    ('geoeng',                  'direct', 'industry_total'),
    ('datacenters',             'flat',   None),
]

SPLIT_GROUPS = {
    'commercial-lighting':  (('service_waterheating', 'service_other'),
                             ['commercial-lighting', 'commercial-appliances', 'commercial-other']),
    'commercial-appliances': (('service_waterheating', 'service_other'),
                              ['commercial-lighting', 'commercial-appliances', 'commercial-other']),
    'commercial-other':     (('service_waterheating', 'service_other'),
                             ['commercial-lighting', 'commercial-appliances', 'commercial-other']),
    'aircraft':   (('transport_other',), ['aircraft', 'rail', 'ships', 'motorbikes']),
    'rail':       (('transport_other',), ['aircraft', 'rail', 'ships', 'motorbikes']),
    'ships':      (('transport_other',), ['aircraft', 'rail', 'ships', 'motorbikes']),
    'motorbikes': (('transport_other',), ['aircraft', 'rail', 'ships', 'motorbikes']),
}
SPLIT_TEMPLATE_CATS = ['commercial-lighting', 'commercial-appliances', 'commercial-other',
                       'aircraft', 'rail', 'ships', 'motorbikes']

# SYSHECF spec: (tech, kind, source). kind 'cf_formula' derives from the CF
# hourly source tab; 'static' pastes the run's exported CSV values verbatim
# (template techs, unchanged from the EPS template per the coverage report).
SYSHECF_ORDER = [
    ('hard-coal', 'static', None),
    ('steam-turbine', 'static', None),
    ('combined-cycle', 'static', None),
    ('nuclear', 'static', None),
    ('hydro', 'static', None),
    ('onshore-wind', 'cf_formula', ('wind_cf', 1.0)),
    ('solar-pv', 'cf_formula', ('solar_cf', 1.0)),
    ('solar-thermal', 'static', None),
    ('biomass', 'static', None),
    ('geothermal', 'static', None),
    ('petroleum', 'static', None),
    ('natural-gas-peaker', 'static', None),
    ('offshore-wind', 'cf_formula', ('wind_cf', 1.0)),
    ('lignite', 'static', None),
    ('MSW', 'static', None),
    ('crude-oil', 'static', None),
    ('heavy-or-residual-oil', 'static', None),
    ('hard-coal-CCS', 'static', None),
    ('combined-cycle-CCS', 'static', None),
    ('biomass-CCS', 'static', None),
    ('lignite-CCS', 'static', None),
    ('SMR', 'static', None),
    ('hydrogen-CT', 'static', None),
    ('hydrogen-CC', 'static', None),
    ('solar-pv-dist', 'cf_formula', ('solar_cf', 0.70)),
    ('pumped-hydro', 'static', None),
]

def read_eps_table(path: Path) -> pd.DataFrame:
    """Read an EPS 6x24 CSV, dropping blank/duplicate label rows (same cleanup
    as energy_timeslice_pipeline._load_existing_eps_csv)."""
    tbl = pd.read_csv(path, index_col=0)
    tbl.index = tbl.index.astype(str).str.strip()
    tbl = tbl[~tbl.index.isin(['', 'nan', 'None'])]
    tbl = tbl[~tbl.index.duplicated(keep='first')]
    return tbl


HEADER_FILL = PatternFill(start_color='305496', end_color='305496', fill_type='solid')
HEADER_FONT = Font(bold=True, color='FFFFFF')
SECTION_FILL = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
SECTION_FONT = Font(bold=True)
PURPOSE_FILL = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
OUTPUT_TAB_COLOR = '1F3864'
LEFT_TOP_WRAP = Alignment(horizontal='left', vertical='top', wrap_text=True)


# ---------------------------------------------------------------------------
# Source-of-record CSVs (created from the verified run captures if absent)
# ---------------------------------------------------------------------------

def ensure_workbook_sources() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (demand_df, cf_df, clustering_df); build the CSVs if missing."""
    demand_csv = SRC_DIR / 'demand_hourly_source.csv'
    cf_csv = SRC_DIR / 'cf_hourly_source.csv'
    clus_csv = SRC_DIR / 'clustering.csv'
    if demand_csv.exists() and cf_csv.exists() and clus_csv.exists():
        print(f'[sources] using existing CSVs in {SRC_DIR}')
        return (pd.read_csv(demand_csv), pd.read_csv(cf_csv), pd.read_csv(clus_csv))

    print('[sources] building workbook_sources CSVs from run captures...')
    parquet = ROOT / 'scratch' / 'cluster_input_branch.parquet'
    labels_csv = ROOT / 'scratch' / 'labels_branch.csv'
    tsmeta_csv = ROOT / 'scratch' / 'tsmeta_branch.csv'
    for p in (parquet, labels_csv, tsmeta_csv):
        if not p.exists():
            raise FileNotFoundError(
                f'{p} not found. Re-run the capture first:\n'
                '    python scratch/capture_cluster_input.py branch')
    df = pd.read_parquet(parquet)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    labels = pd.read_csv(labels_csv, index_col=0).iloc[:, 0].to_numpy()
    tsmeta = pd.read_csv(tsmeta_csv).set_index('timeslice')

    from energy_timeslice_pipeline import build_eps_timeslice_label_map
    label_map = build_eps_timeslice_label_map(tsmeta)

    n = len(df)
    doy = np.arange(n) // 24 + 1
    hod = np.arange(n) % 24
    slice_names = pd.Series(labels).map(label_map.to_dict()).to_numpy()
    ts_txt = df.index.strftime('%Y-%m-%d %H:%M')

    SRC_DIR.mkdir(parents=True, exist_ok=True)

    demand = pd.DataFrame({'timestamp': ts_txt})
    for c in DEMAND_COLS:
        demand[c] = df[c].to_numpy()
    demand['day_of_year'] = doy
    demand['hour_of_day'] = hod
    demand['slice'] = slice_names
    demand.to_csv(demand_csv, index=False)

    cf = pd.DataFrame({'timestamp': ts_txt})
    for c in ['load', 'net_load', 'solar_gen', 'wind_gen', 'solar_cf', 'wind_cf']:
        cf[c] = df[c].to_numpy()
    cf['day_of_year'] = doy
    cf['hour_of_day'] = hod
    cf['slice'] = slice_names
    cf['CF_solar-pv'] = df['solar_cf'].to_numpy()
    cf['CF_solar-pv-dist'] = df['solar_cf'].to_numpy() * 0.70
    cf['CF_onshore-wind'] = df['wind_cf'].to_numpy()
    cf['CF_offshore-wind'] = df['wind_cf'].to_numpy()
    cf.to_csv(cf_csv, index=False)

    rep_dates = pd.to_datetime(tsmeta['representative_date'])
    rep_doy_by_label = {}
    days_by_label = {}
    doy_to_slice = {}
    day_index = pd.to_datetime(df.index.date[::24])
    for ts_num, label in label_map.items():
        days_by_label[label] = int(tsmeta.loc[ts_num, 'days_represented'])
        rep = rep_dates.loc[ts_num]
        rep_doy_by_label[label] = int((day_index == rep).argmax()) + 1
    for d in range(1, 366):
        doy_to_slice[d] = slice_names[(d - 1) * 24]
    clus = pd.DataFrame({
        'doy': list(range(1, 366)),
        'slice': [doy_to_slice[d] for d in range(1, 366)],
    })
    # Slice-level columns occupy the first six rows (one per EPS slice).
    clus['slice_name'] = pd.Series(SLICES).reindex(clus.index)
    clus['days'] = pd.Series([days_by_label[s] for s in SLICES]).reindex(clus.index)
    clus['rep_doy'] = pd.Series([rep_doy_by_label[s] for s in SLICES]).reindex(clus.index)
    clus.to_csv(clus_csv, index=False)
    print(f'[sources] wrote {demand_csv.name}, {cf_csv.name}, {clus_csv.name}')
    return demand, cf, clus


# ---------------------------------------------------------------------------
# Shared tabs
# ---------------------------------------------------------------------------

def add_about_tab(wb, abbr: str, file_name_no_ext: str, sources: list, notes: list):
    ws = wb.create_sheet('About', 0)
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 110
    ws.cell(1, 1, f'{abbr} {file_name_no_ext}').font = Font(bold=True)
    ws.cell(3, 1, 'Sources:').font = Font(bold=True)
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
    for i, (label, text) in enumerate(notes):
        r = notes_row + 1 + i
        ws.cell(r, 1, label).font = Font(bold=True)
        ws.cell(r, 2, text).alignment = LEFT_TOP_WRAP
        ws.row_dimensions[r].height = max(30, 18 * (1 + len(text) // 110))


def add_clustering_tab(wb, clus: pd.DataFrame):
    """Days-per-slice snapshot, slice -> representative DOY (editable), and
    DOY -> slice map (editable). Output-tab formulas VLOOKUP into G/H."""
    ws = wb.create_sheet('Clustering')
    for col, w in zip('ABDEGH', (14, 8, 8, 14, 14, 10)):
        ws.column_dimensions[col].width = w
    ws.cell(1, 1, 'Days per timeslice (snapshot)').font = SECTION_FONT
    ws.cell(1, 1).fill = SECTION_FILL
    for c, name in ((1, 'Slice'), (2, 'Days')):
        ws.cell(2, c, name).font = HEADER_FONT
        ws.cell(2, c).fill = HEADER_FILL
    days = dict(zip(clus['slice_name'].dropna(), clus['days'].dropna().astype(int)))
    rep = dict(zip(clus['slice_name'].dropna(), clus['rep_doy'].dropna().astype(int)))
    for i, sl in enumerate(SLICES):
        ws.cell(3 + i, 1, sl)
        ws.cell(3 + i, 2, days[sl])
    ws.cell(1, 4, 'DOY → slice (edit to reassign days)').font = SECTION_FONT
    ws.cell(1, 4).fill = SECTION_FILL
    for c, name in ((4, 'DOY'), (5, 'Slice')):
        ws.cell(2, c, name).font = HEADER_FONT
        ws.cell(2, c).fill = HEADER_FILL
    for _, row in clus.iterrows():
        d = int(row['doy'])
        ws.cell(2 + d, 4, d)
        ws.cell(2 + d, 5, row['slice'])
    ws.cell(1, 7, 'Representative day per slice (edit to re-derive outputs)').font = SECTION_FONT
    ws.cell(1, 7).fill = SECTION_FILL
    for c, name in ((7, 'Slice'), (8, 'Rep DOY')):
        ws.cell(2, c, name).font = HEADER_FONT
        ws.cell(2, c).fill = HEADER_FILL
    for i, sl in enumerate(SLICES):
        ws.cell(3 + i, 7, sl)
        ws.cell(3 + i, 8, rep[sl])


def add_hourly_source_tab(wb, name: str, df: pd.DataFrame) -> dict[str, str]:
    """Paste an hourly source CSV; 'slice' becomes a VLOOKUP on Clustering.
    Returns {column_name: column_letter}."""
    ws = wb.create_sheet(name)
    cols = list(df.columns)
    for j, c in enumerate(cols, start=1):
        ws.cell(1, j, c).font = Font(bold=True, italic=(c in ('day_of_year', 'hour_of_day', 'slice')))
    doy_letter = get_column_letter(cols.index('day_of_year') + 1)
    slice_idx = cols.index('slice') + 1
    for i in range(len(df)):
        r = 2 + i
        for j, c in enumerate(cols, start=1):
            if c == 'slice':
                ws.cell(r, j, f'=VLOOKUP({doy_letter}{r},Clustering!$D$3:$E$367,2,FALSE)')
            elif c == 'timestamp':
                ws.cell(r, j, str(df.iloc[i, j - 1]))
            else:
                ws.cell(r, j, float(df.iloc[i, j - 1]))
    ws.column_dimensions['A'].width = 18
    for j in range(2, len(cols) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 15
    ws.freeze_panes = 'B2'
    return {c: get_column_letter(i + 1) for i, c in enumerate(cols)}


def _rep_doy_formula(slice_cell: str) -> str:
    return f'VLOOKUP({slice_cell},Clustering!$G$3:$H$8,2,FALSE)'


def _out_tab_shell(wb, title: str, first_cell: str):
    ws = wb.create_sheet(title)
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 24
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 12
    ws.cell(1, 1, first_cell)
    for h, name in enumerate(HOUR_COLS):
        ws.cell(1, 2 + h, name)
    for r_off, sl in enumerate(SLICES):
        ws.cell(2 + r_off, 1, sl)
    return ws


# ---------------------------------------------------------------------------
# SHELF workbook
# ---------------------------------------------------------------------------

def _slice_mean_lf(src: str, col_letter: str, slice_l: str, hour_l: str, n: int,
                   slice_cell: str, h: int) -> tuple[str, str]:
    """Slice-mean load factor for one column: (numerator, denominator).

    numerator   = AVERAGEIFS(col, slice, <slice>, hour_of_day, <h>)
                  — mean demand over every hour assigned to that (slice, hour)
    denominator = SUM(col) — annual demand

    This is the definition in CLAUDE.md §6 and the form used by the canonical
    eps-us workbooks. It is also the only form that satisfies the SHELF balance
    Σ_slices days × Σ_hours LF = 1 exactly: summing the slice means over 24
    hours and weighting by the slice's day count reconstructs the slice's total
    energy, and summing over slices reconstructs the annual total.

    Superseded the representative-day form (SUMIFS on the slice's one rep day),
    which broke that balance — see DECISIONS.md 2026-08-12.
    """
    rng = f"'{src}'!${col_letter}$2:${col_letter}${n + 1}"
    slc = f"'{src}'!${slice_l}$2:${slice_l}${n + 1}"
    hr = f"'{src}'!${hour_l}$2:${hour_l}${n + 1}"
    return f'AVERAGEIFS({rng},{slc},{slice_cell},{hr},{h})', f'SUM({rng})'


def _slice_mean_cf(src: str, col_letter: str, slice_l: str, hour_l: str, n: int,
                   slice_cell: str, h: int) -> str:
    """Slice-mean capacity factor: AVERAGEIFS(col, slice, <slice>, hour, <h>).

    Callers clamp to [0, 1] and wrap in IFERROR, matching the eps-us cells.
    """
    rng = f"'{src}'!${col_letter}$2:${col_letter}${n + 1}"
    slc = f"'{src}'!${slice_l}$2:${slice_l}${n + 1}"
    hr = f"'{src}'!${hour_l}$2:${hour_l}${n + 1}"
    return f'AVERAGEIFS({rng},{slc},{slice_cell},{hr},{h})'


def _cf_cell(avg: str, mult: float) -> str:
    """Wrap a CF expression the way the eps-us SYSHECF cells do."""
    mult_txt = '' if mult == 1.0 else f'*{mult}'
    return f'=IFERROR(MAX(0,MIN(1,{avg}{mult_txt})),0)'


def add_split_templates_tab(wb) -> dict[str, tuple[str, int]]:
    """Paste the EPS-template peer tables used for template_split weights.
    Returns {category: (col_letter of Hour0, header_row)} — each table is 26
    rows apart, columns B..Y hold Hour0..Hour23, col A the slice name."""
    ws = wb.create_sheet('Split templates')
    ws.column_dimensions['A'].width = 24
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 11
    anchors = {}
    row = 1
    for cat in SPLIT_TEMPLATE_CATS:
        path = TEMPLATE_SHELF_DIR / f'SHELF-{cat}.csv'
        tbl = read_eps_table(path).reindex(index=SLICES, columns=HOUR_COLS).fillna(0.0)
        ws.cell(row, 1, f'SHELF-{cat} (EPS template — split weight source)').font = SECTION_FONT
        ws.cell(row, 1).fill = SECTION_FILL
        hdr = row + 1
        ws.cell(hdr, 1, 'slice').font = Font(bold=True)
        for h, name in enumerate(HOUR_COLS):
            ws.cell(hdr, 2 + h, name).font = Font(bold=True)
        for i, sl in enumerate(SLICES):
            ws.cell(hdr + 1 + i, 1, sl)
            for h in range(24):
                ws.cell(hdr + 1 + i, 2 + h, float(tbl.loc[sl, HOUR_COLS[h]]))
        anchors[cat] = hdr  # data rows are hdr+1 .. hdr+6, cols 2..25
        row = hdr + 6 + 2
    return anchors


def build_shelf_workbook(demand: pd.DataFrame, clus: pd.DataFrame):
    n = len(demand)
    today = dt.date.today().isoformat()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    sources = [
        {'purpose': 'U.S. Hourly End-Use Demand Shapes',
         'source': 'NREL',
         'publication': 'NREL Electrification Futures Study (EFS) Load Profiles',
         'year': 2018,
         'url': 'https://data.nrel.gov/submissions/126',
         'info': 'Reference electrification / Moderate technology advancement, EFS year '
                 'nearest 2025 (2024). Residential + commercial space conditioning split into '
                 'heating/cooling via EIA RECS CE8.2.M / CE8.3.M monthly multipliers; '
                 'residential/service sub-splits via Mendeley template shares. Level + seasonal '
                 'calibration to DemandCast observed demand (2023–2025 mean 477,941 MW). The '
                 'calibrated hourly series is pasted into the "Demand hourly source" tab.'},
        {'purpose': 'Observed Hourly Demand (calibration target)',
         'source': 'Open Energy Transition',
         'publication': 'DemandCast (EIA-930 derived for the U.S.)',
         'year': 2025,
         'url': 'https://github.com/open-energy-transition/demandcast',
         'info': 'Hourly observed U.S. demand 2023–2025 used for level + seasonal calibration '
                 '(calibration_method=level_seasonal, master-parity pin).'},
        {'purpose': 'Split Weights for Commercial Lighting/Appliances/Other and '
                    'Aircraft/Rail/Ships/Motorbikes',
         'source': 'Energy Innovation',
         'publication': 'EPS Structure Testing SHELF templates',
         'year': 2025,
         'url': 'https://energyinnovation.org/',
         'info': 'EPS template SHELF tables pasted into the "Split templates" tab. The pipeline '
                 'distributes the aggregate (service water-heat + other; transport other) across '
                 'these categories in proportion to the template values, cell by cell.'},
    ]
    notes = [
        ('Methodology overview',
         'SHELF tables for the EPS Vensim model from the international pipeline '
         '(run_pipeline.py) U.S. run. Each output tab is a 6 (timeslice) x 24 (hour) load-factor '
         'table: LF[slice, hour] = demand at (representative day of slice, hour) / annual demand '
         'of that category. Representative-day profiles — NOT slice-hour means. Edit the source '
         'tab, the Clustering tab (slice assignment or representative days), or the Split '
         'templates tab and all outputs recompute.'),
        ('Clustering',
         'K6/H24 representative-day clustering (cluster_days_repday via cluster_timeslices) on '
         'net load = calibrated demand − Ember-calibrated renewables.ninja solar/wind generation. '
         'Days per timeslice: W=27 Sp=71 Su=62 F=166 SP=23 WP=16. Representative days per slice '
         'are editable on the Clustering tab (G/H columns).'),
        ('Master-parity pins',
         'This U.S. run is pinned to legacy master-branch behavior (DECISIONS.md 2026-07-07): '
         'UTC weather, multiplicative CF calibration, level_seasonal demand calibration. '
         'Verified bit-identical to the 2026-07-01 master baseline run.'),
        ('Zero and flat categories',
         'residential-envelope, commercial-envelope: zero (EPS convention). datacenters: flat '
         '1/8760. district-heat-hydrogen and geoeng mirror the industry shape in this workflow '
         '(pipeline convention; differs from the eps-us zero convention — review before use).'),
        ('Relationship to canonical eps-us files',
         'The canonical U.S. EPS SHELF inputs come from the Cambium-based national pipeline '
         '(scripts/build_shelf_workbook.py, ResStock/ComStock/EFS sources). This workbook '
         'documents the international-workflow U.S. baseline and is NOT a drop-in replacement.'),
        ('Run metadata',
         f'country: UnitedStates; year 2025; EFS 2024 Reference/Moderate; built: {today}; '
         'build script: scripts/build_us_run_workbooks.py; source-of-record CSVs: '
         'workbook_sources/ next to this file.'),
        ('Caveats',
         'All values are inputs for staff review. Verify against NREL EFS, DemandCast/EIA, '
         'Ember, and the project methodology (CLAUDE.md, DECISIONS.md) before use in any '
         'work product.'),
    ]
    add_about_tab(wb, 'SHELF', SHELF_OUT.stem, sources, notes)
    add_clustering_tab(wb, clus)
    split_anchors = add_split_templates_tab(wb)
    col_letters = add_hourly_source_tab(wb, 'Demand hourly source', demand)
    hour_l = col_letters['hour_of_day']
    slice_l = col_letters['slice']
    SRC = 'Demand hourly source'

    for cat, kind, arg in SHELF_SPECS:
        if kind == 'days':
            ws = wb.create_sheet('SHELF-days-per-timeslice')
            ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
            ws.column_dimensions['A'].width = 22
            ws.column_dimensions['B'].width = 22
            ws.cell(1, 1, 'Unit: days')
            ws.cell(1, 2, 'Days per Timeslice')
            for i, sl in enumerate(SLICES):
                ws.cell(2 + i, 1, sl)
                ws.cell(2 + i, 2, f'=Clustering!$B${3 + i}')
            continue
        ws = _out_tab_shell(wb, f'SHELF-{cat}', SHELF_UNIT)
        for r_off, sl in enumerate(SLICES):
            slice_cell = f'$A{2 + r_off}'
            for h in range(24):
                if kind == 'zeros':
                    ws.cell(2 + r_off, 2 + h, 0.0)
                elif kind == 'flat':
                    ws.cell(2 + r_off, 2 + h, 1.0 / 8760.0)
                elif kind == 'direct':
                    pick, tot = _slice_mean_lf(SRC, col_letters[arg], slice_l, hour_l, n, slice_cell, h)
                    ws.cell(2 + r_off, 2 + h, f'=IFERROR({pick}/{tot},0)')
                elif kind == 'sum':
                    c1, c2 = arg
                    p1, t1 = _slice_mean_lf(SRC, col_letters[c1], slice_l, hour_l, n, slice_cell, h)
                    p2, t2 = _slice_mean_lf(SRC, col_letters[c2], slice_l, hour_l, n, slice_cell, h)
                    ws.cell(2 + r_off, 2 + h, f'=IFERROR(({p1}+{p2})/({t1}+{t2}),0)')
                elif kind == 'split':
                    # Aggregate LF = sum of each column's OWN load factor
                    # (pick/annual-sum per column), matching the pipeline's
                    # sum over *_load_factor columns — not combined-then-
                    # normalized.
                    agg_cols, peers = SPLIT_GROUPS[cat]
                    terms = []
                    for c in agg_cols:
                        p, t = _slice_mean_lf(SRC, col_letters[c], slice_l, hour_l, n, slice_cell, h)
                        terms.append(f'{p}/{t}')
                    agg = f"({'+'.join(terms)})"
                    cell_col = get_column_letter(2 + h)
                    me = f"'Split templates'!${cell_col}${split_anchors[cat] + 1 + r_off}"
                    peer_cells = [
                        f"'Split templates'!${cell_col}${split_anchors[p] + 1 + r_off}"
                        for p in peers
                    ]
                    ws.cell(2 + r_off, 2 + h,
                            f"=IFERROR({agg}*{me}/({'+'.join(peer_cells)}),0)")

    SHELF_OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        wb.save(SHELF_OUT)
    except PermissionError:
        print(f'  ERROR: cannot write {SHELF_OUT} — close it in Excel first.')
        return
    print(f'[shelf] wrote {SHELF_OUT}  ({len(wb.sheetnames)} tabs)')


# ---------------------------------------------------------------------------
# SYSHECF workbook
# ---------------------------------------------------------------------------

def build_syshecf_workbook(cf: pd.DataFrame, clus: pd.DataFrame):
    n = len(cf)
    today = dt.date.today().isoformat()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    sources = [
        {'purpose': 'Hourly Solar and Wind Capacity Factors (synthetic, weather-derived)',
         'source': 'Renewables.ninja / NREL MERRA-2',
         'publication': 'Renewables.ninja country-aggregated weather (MERRA-2, area-weighted)',
         'year': 2025,
         'url': 'https://www.renewables.ninja/',
         'info': 'U.S. irradiance/temperature/wind speed 2023–2025, kept in UTC (master-parity '
                 'pin). Solar PV (orientation x1.1) and wind (hub 100 m, z0=0.03) capacity '
                 'factors computed by the pipeline and pasted into the "CF hourly source" tab '
                 'as solar_cf / wind_cf plus derived CF_<tech> columns.'},
        {'purpose': 'Annual Capacity Factor Targets and Installed Capacity (calibration)',
         'source': 'Ember',
         'publication': 'Ember Yearly Electricity Data (full release, long format)',
         'year': 2025,
         'url': 'https://ember-energy.org/data/yearly-electricity-data/',
         'info': 'U.S. solar target 0.198 / wind target 0.337 (3-year mean). MULTIPLICATIVE '
                 'calibration (master-parity pin): wind multiplier 29.66x, so wind_cf values '
                 'exceed 1.0 (max 12.5). Retained for baseline continuity with the 2026-07-01 '
                 'master run — do not hand these wind tables downstream without review.'},
        {'purpose': 'Non-VRE Technology Tables',
         'source': 'Energy Innovation',
         'publication': 'EPS Structure Testing SYSHECF templates',
         'year': 2025,
         'url': 'https://energyinnovation.org/',
         'info': '22 techs copied unchanged from the EPS template (see EPS_export_coverage.csv). '
                 'Their tabs hold static values — edit directly to change.'},
    ]
    notes = [
        ('Methodology overview',
         'SYSHECF tables from the international pipeline (run_pipeline.py) U.S. run. For the '
         'four derived techs (solar-pv, solar-pv-dist, onshore-wind, offshore-wind): '
         'CF[slice, hour] = CF at (representative day of slice, hour), via AVERAGEIFS against '
         'the CF hourly source tab. solar-pv-dist = 0.70 x solar-pv. Representative-day '
         'profiles — NOT slice-hour means. No EIA re-calibration and no [0,1] clamp is applied '
         '(matches the pipeline CSVs exactly).'),
        ('Clustering',
         'Same clustering as the SHELF workbook: representative-day K6/H24 on net load. Days '
         'per timeslice: W=27 Sp=71 Su=62 F=166 SP=23 WP=16. Slice assignment and '
         'representative days are editable on the Clustering tab.'),
        ('Master-parity pins',
         'UTC weather + multiplicative CF calibration + level_seasonal demand calibration '
         '(DECISIONS.md 2026-07-07). Verified bit-identical to the 2026-07-01 master baseline.'),
        ('Relationship to canonical eps-us files',
         'The canonical U.S. SYSHECF inputs come from the Cambium-based national pipeline '
         '(scripts/build_syshecf_workbook.py, EIA-calibrated). This workbook documents the '
         'international-workflow U.S. baseline and is NOT a drop-in replacement.'),
        ('Run metadata',
         f'country: UnitedStates; year 2025; built: {today}; build script: '
         'scripts/build_us_run_workbooks.py; source-of-record CSVs: workbook_sources/.'),
        ('Caveats',
         'All values are inputs for staff review. Verify against renewables.ninja, Ember, and '
         'the project methodology (CLAUDE.md, DECISIONS.md) before use in any work product. '
         'Wind CF values > 1.0 are physically invalid and flagged above.'),
    ]
    add_about_tab(wb, 'SYSHECF', SYSHECF_OUT.stem, sources, notes)
    add_clustering_tab(wb, clus)
    col_letters = add_hourly_source_tab(wb, 'CF hourly source', cf)
    hour_l = col_letters['hour_of_day']
    slice_l = col_letters['slice']
    SRC = 'CF hourly source'

    for tech, kind, arg in SYSHECF_ORDER:
        csv_path = EPS_DIR / 'SYSHECF' / f'SYSHECF-{tech}.csv'
        tbl = read_eps_table(csv_path)
        first_cell = tbl.index.name  # header first cell as exported (unit or display name)
        tbl = tbl.reindex(index=SLICES, columns=HOUR_COLS)
        ws = _out_tab_shell(wb, f'SYSHECF-{tech}', first_cell)
        if kind == 'static':
            for r_off, sl in enumerate(SLICES):
                for h in range(24):
                    ws.cell(2 + r_off, 2 + h, float(tbl.loc[sl, HOUR_COLS[h]]))
        else:
            src_col, mult = arg
            for r_off, sl in enumerate(SLICES):
                slice_cell = f'$A{2 + r_off}'
                for h in range(24):
                    avg = _slice_mean_cf(SRC, col_letters[src_col], slice_l, hour_l,
                                         n, slice_cell, h)
                    ws.cell(2 + r_off, 2 + h, _cf_cell(avg, mult))

    try:
        wb.save(SYSHECF_OUT)
    except PermissionError:
        print(f'  ERROR: cannot write {SYSHECF_OUT} — close it in Excel first.')
        return
    print(f'[syshecf] wrote {SYSHECF_OUT}  ({len(wb.sheetnames)} tabs)')


def main():
    demand, cf, clus = ensure_workbook_sources()
    print(f'[build] demand source {demand.shape}, cf source {cf.shape}')
    build_shelf_workbook(demand, clus)
    build_syshecf_workbook(cf, clus)
    print('[done] run scripts/verify_us_run_workbooks.py next')


if __name__ == '__main__':
    main()
