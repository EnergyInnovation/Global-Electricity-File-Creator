"""Build self-contained SHELF + SYSHECF + ELCCAfR Excel workbooks for ANY
region's run of the international pipeline (run_pipeline.py), directly from the
run's workbook_sources CSVs — following the build-input-xlsx skill. This builder
is the AUTHORITATIVE mapping from the Demand/CF hourly source (Zapata end-use
classifications) to the EPS output tabs; it does NOT read the pipeline's
per-category SHELF-*.csv / SYSHECF-*.csv exports.

SHELF: every category maps 1:1 to a Demand hourly source column via SLICE-MEAN
load factors (see SHELF_MAP below) — no template splits.
  LF[slice, hour] = AVERAGEIFS(col, slice, <slice>, hour_of_day, <hour>) / SUM(col)

SYSHECF: the VRE techs (solar-pv, solar-pv-dist, onshore-wind, offshore-wind)
are derived from the CF hourly source; every other ("non-VRE") tech table is
borrowed verbatim from the country's own EPS model files (--borrow-dir).
  CF[slice, hour] = AVERAGEIFS(cf col, slice, <slice>, hour_of_day, <hour>)
                    x multiplier, clamped to [0, 1]

ELCCAfR: a capacity-adequacy derate EPS applies in the RELIABILITY calculation
only. It is a second statistic over the same CF column and the same per-slice
day set that produced SYSHECF, so the two multiply back to the worst day:
  ELCCAfR[slice, hour] = MINIFS(cf col, slice, <slice>, hour_of_day, <hour>)
                         / AVERAGEIFS(same)          on the two peak slices
                       = 1.0                          on the four non-peak slices
  ==> SYSHECF x ELCCAfR = the worst-day CF at that hour
This builder also writes the 25 ELCCAfR CSVs, so a run made before ELCCAfR was
added to the pipeline gets them without re-running run_pipeline.py.

Slice means (not representative-day picks) are what CLAUDE.md §6 specifies and
what the canonical eps-us workbooks use. They are also the only form for which
the Checker tab's balance, Σ_slices days × Σ_hours LF, equals 1 for every
category — see DECISIONS.md 2026-08-12.

--borrow-dir is REQUIRED: it supplies the non-VRE SYSHECF tables.

Run:
    python scripts/build_run_workbooks.py "South Korea" \\
        --borrow-dir "C:/Users/Claire Trevisan/GitHub/eps-southkorea/InputData/elec"
Then verify (formula wiring + borrowed-value equality):
    python scripts/verify_run_workbooks.py "South Korea" \\
        --borrow-dir "C:/Users/Claire Trevisan/GitHub/eps-southkorea/InputData/elec"
"""
from __future__ import annotations
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from energy_timeslice_pipeline import (  # noqa: E402
    ELCCAfR_DEGENERATE_MEAN, ELCCAfR_DEMAND_ALTERING_DEFAULT,
    ELCCAfR_DEMAND_ALTERING_FILE, ELCCAfR_DEMAND_ALTERING_UNIT,
    ELCCAfR_STATISTIC_DEFAULT, EPS_ELCCAfR_FILE_MAP, EPS_ELCCAfR_HEADERS,
    EPS_ELCCAfR_MIRRORS, EPS_PEAK_TIMESLICES, EPS_SYSHECF_FILE_MAP,
    build_elccafr_constant_table,
    build_elccafr_demand_altering_table, build_elccafr_table,
    get_country_preset, resolve_direct_cf_spec,
)
from scripts.build_us_run_workbooks import (  # noqa: E402
    HEADER_FILL, HEADER_FONT, HOUR_COLS, OUTPUT_TAB_COLOR, SECTION_FILL,
    SECTION_FONT, SHELF_UNIT, SLICES,
    _cf_cell, _out_tab_shell, _slice_mean_cf, _slice_mean_lf,
    add_about_tab, add_clustering_tab, add_hourly_source_tab, read_eps_table,
)

SHELF_NAME = 'Seasonal Hourly Equipment Load Factors by End Use.xlsx'
SYSHECF_NAME = 'Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx'
SYSHECF_UNIT = 'Unit: dimensionless (capacity factor)'
ELCCAfR_NAME = 'ELCCAfR ELCC Adjustment for Reliability.xlsx'
ELCCAfR_STATS_TAB = 'Peak CF statistics'
ELCCAfR_RELATION_TAB = 'SHELF & SYSHECF relationship'

# ---------------------------------------------------------------------------
# SHELF mapping — Zapata (Demand hourly source) column -> EPS SHELF tab.
# Reclassified 2026-07-14 per staff direction: every category is a direct 1:1
# slice-mean load factor of one Demand hourly source column (NO template splits,
# no dependence on the untraceable "EPS Structure Testing" templates). Edit
# here to change how end uses map to EPS categories.
#   ('direct', <demand col>) : LF = slice-hour mean / annual sum of that column
#   ('zeros',  None)         : all-zero table (EPS envelope convention)
#   ('flat',   None)         : uniform 1/8760 in every cell (datacenters)
# ---------------------------------------------------------------------------
SHELF_MAP: list = [
    ('residential-heating',    ('direct', 'residential_heating')),
    ('residential-cooling',    ('direct', 'residential_cooling')),
    ('residential-envelope',   ('zeros',  None)),
    ('residential-lighting',   ('direct', 'residential_lighting')),
    ('residential-appliances', ('direct', 'residential_waterheating')),
    ('residential-other',      ('direct', 'residential_other')),
    ('commercial-heating',     ('direct', 'service_heating')),
    ('commercial-cooling',     ('direct', 'service_cooling')),
    ('commercial-envelope',    ('zeros',  None)),
    ('commercial-lighting',    ('direct', 'residential_lighting')),  # follows residential lighting
    ('commercial-appliances',  ('direct', 'service_waterheating')),
    ('commercial-other',       ('direct', 'service_other')),
    ('LDVs',                   ('direct', 'transport')),
    ('HDVs',                   ('direct', 'transport')),
    ('aircraft',               ('direct', 'transport')),
    ('rail',                   ('direct', 'transport')),
    ('ships',                  ('direct', 'transport')),
    ('motorbikes',             ('direct', 'transport')),
    ('industry',               ('direct', 'industry')),
    ('district-heat-hydrogen', ('direct', 'industry')),   # mirrors industry shape
    ('geoeng',                 ('direct', 'industry')),   # mirrors industry shape
    ('datacenters',            ('flat',   None)),
]


# ---------------------------------------------------------------------------
# Per-country About-tab metadata (fallback 'generic' for unmapped countries)
# ---------------------------------------------------------------------------

def observed_demand_sources_for(preset: dict | None, demand_year: int | None) -> list:
    """About-tab block(s) for the observed hourly demand calibration target.

    Most presets calibrate against DemandCast. A preset that also defines
    ``demand_series_csv`` has a second, staged record and selects between the
    two from the run configuration (``demandcast_pin``) — China, whose DemandCast
    source covers 2018 only while the staged CSV covers 2015-2024. Both are
    documented, because which one a run used is a methodology choice, and the
    staged source's citation has to travel with the workbook.
    """
    demandcast = {
        'purpose': 'Observed Hourly Demand (calibration target)',
        'source': 'Open Energy Transition',
        'publication': 'DemandCast',
        'year': 2025,
        'url': 'https://github.com/open-energy-transition/demandcast',
        'info': 'Observed hourly national demand over the preset calibration window; the '
                'calibrated hourly series is pasted into the "Demand hourly source" tab.',
    }
    csv_path = (preset or {}).get('demand_series_csv')
    if not csv_path:
        return [demandcast]

    pin = (preset or {}).get('demandcast_pin') or {}
    pin_txt = ' and '.join(f'{k} = {v}' for k, v in pin.items()) or '(none)'
    # last_n_years is not recoverable from workbook_sources, so only a target
    # year that cannot match the pin lets us name the source unambiguously.
    if demand_year is not None and pin.get('year') not in (None, demand_year):
        applies = (f'THIS RUN (target year {demand_year}) used the staged multi-year source '
                   f'below — the pin requires {pin_txt}.')
    elif demand_year is not None:
        applies = (f'THIS RUN has target year {demand_year}, which matches the pin on year; '
                   f'the source therefore depends on the run\'s calibration window '
                   f'(DemandCast when the full pin {pin_txt} is met, otherwise the staged '
                   f'source below). Check the run log or the pipeline metrics CSV.')
    else:
        applies = 'Target year could not be read from the run sources; check the run log.'
    demandcast['info'] = (
        'Used ONLY when the run matches the preset\'s DemandCast pin (' + pin_txt + '); '
        'this source\'s coverage is narrower than the staged record below, which is why '
        'the pin exists. ' + applies
    )

    staged = {
        'purpose': 'Observed Hourly Demand (calibration target) — staged multi-year source',
        'source': (preset or {}).get('demand_series_source', 'Yi, B. et al. (2026), Scientific Data'),
        'publication': (preset or {}).get('demand_series_citation', csv_path),
        'year': 2026,
        'url': 'https://doi.org/10.1038/s41597-026-07327-8',
        'info': ('Staged at ' + str(csv_path) + ', built by '
                 'scripts/build_china_hourly_demand.py from the published provincial '
                 'workbook (31 provincial-level regions, hourly, GWh per hour, summed to a '
                 'national MW series). Selected automatically whenever the run does not '
                 'match the DemandCast pin above. LICENSE: CC BY-NC-ND 4.0 — '
                 'non-commercial, no derivatives; confirm this permits the intended use '
                 'before publishing anything derived from it, and cite the publication '
                 'above. A meteorological reconstruction anchored to 2018 NDRC load data, '
                 'not a metered series — see CLAUDE.md section 1 and '
                 'output/china_demand_source_test/RESULTS.md.'),
    }
    return [demandcast, staged]


def demand_sources_for(country_key: str, preset: dict | None = None,
                       demand_year: int | None = None) -> list:
    if country_key == 'UnitedStates':
        return [
            {'purpose': 'U.S. Hourly End-Use Demand Shapes',
             'source': 'NREL',
             'publication': 'NREL Electrification Futures Study (EFS) Load Profiles',
             'year': 2018,
             'url': 'https://data.nrel.gov/submissions/126',
             'info': 'Reference electrification / Moderate technology advancement. Space '
                     'conditioning split via EIA RECS CE8.2.M / CE8.3.M; sub-splits via '
                     'Mendeley template shares. Level + seasonal calibration to DemandCast '
                     'observed demand (master-parity pin).'},
        ]
    return [
        {'purpose': 'Hourly End-Use Demand Shapes (synthetic)',
         'source': 'Mendeley Data (Zapata et al.)',
         'publication': 'Global hourly electricity demand dataset (SSP2) + Zapata 2022 '
                        'stylized end-use regeneration',
         'year': 2022,
         'url': 'https://data.mendeley.com/datasets/pmd2dchk44',
         'info': 'Country-specific end-use shapes. Climate-sensitive end-uses regenerated '
                 'from local weather + occupancy + daylength (Zapata 2022), then calibrated '
                 'to observed totals via ridge-regularized monthly NNLS anchored to the '
                 'country EPS per-end-use magnitudes (calibration_method per preset; see '
                 'run metadata note).'},
        *observed_demand_sources_for(preset, demand_year),
    ]


def cf_sources_for(country_key: str, preset: dict | None = None,
                   borrow_dir: Path | None = None,
                   demand_year: int | None = None) -> list:
    wind_from_sites = (preset or {}).get('wind_cf_source') == 'ninja_sites'
    if wind_from_sites:
        vre_entry = {
            'purpose': 'Hourly Solar (weather-derived) and Wind (per-site simulation) Capacity Factors',
            'source': 'Renewables.ninja / MERRA-2',
            'publication': 'Renewables.ninja country weather (solar) + per-site wind simulation (wind)',
            'year': 2025,
            'url': 'https://www.renewables.ninja/',
            'info': 'SOLAR PV (orientation x1.1) from the ninja country-aggregated weather '
                    '(irradiance / temperature) over the preset calibration window. WIND from '
                    'the ninja per-site SIMULATION output (hub-height, power-curve, '
                    'bias-corrected) — the electricity column (capacity=1) IS the hourly CF — '
                    'averaged across the sites in data/weather/ninja_sim/<ISO2>/, UTC then '
                    'converted to the preset timezone. This REPLACES the 2 m wind-speed → '
                    'power-curve estimate, whose diurnal cycle is inverted vs hub height '
                    '(see DECISIONS.md 2026-07-10). Sites are classified onshore vs offshore '
                    '(their type in scripts/fetch_ninja_sites.py), so onshore-wind and '
                    'offshore-wind derive from separate site-type CF series, each scaled by '
                    'the factor the blended series needed to hit the Ember fleet-wide wind CF '
                    '(see DECISIONS.md 2026-08-11). Both are pasted into the "CF hourly '
                    'source" tab, with derived CF_<tech> columns for every SYSHECF technology.',
        }
    else:
        vre_entry = {
            'purpose': 'Hourly Solar and Wind Capacity Factors (synthetic, weather-derived)',
            'source': 'Renewables.ninja / MERRA-2',
            'publication': 'Renewables.ninja country-aggregated weather (area-weighted)',
            'year': 2025,
            'url': 'https://www.renewables.ninja/',
            'info': 'Irradiance / temperature / wind speed over the preset calibration window. '
                    'Solar PV (orientation x1.1) and wind (hub 100 m, z0=0.03) capacity factors '
                    'computed by the pipeline and pasted into the "CF hourly source" tab, with '
                    'derived CF_<tech> columns for every SYSHECF technology.',
        }
    common = [
        vre_entry,
        {'purpose': 'Annual Capacity Factor Targets and Installed Capacity (calibration)',
         'source': 'Ember',
         'publication': 'Ember Yearly Electricity Data (full release, long format)',
         'year': 2025,
         'url': 'https://ember-energy.org/data/yearly-electricity-data/',
         'info': 'Country solar/wind annual CF targets and installed capacity. Calibration '
                 'mode per preset: cap_redistribute (bounded [0,1]) for international '
                 'presets; multiplicative for the U.S. master-parity pin.'},
        # The CF values themselves do not come from the demand series, but the
        # day-to-timeslice assignment does — so every slice mean in this workbook
        # depends on which observed demand record calibrated the run.
        *[dict(s, purpose=s['purpose'] + ' — drives the clustering, hence these slice means')
          for s in observed_demand_sources_for(preset, demand_year)],
        _nonvre_source_entry(borrow_dir),
    ]
    return common


def _nonvre_source_entry(borrow_dir: Path | None) -> dict:
    """About-tab source block for the non-derived (non-VRE) SYSHECF techs.

    When a --borrow-dir is supplied, those tabs are copied verbatim from that
    country's own EPS model input files instead of the generic EPS Structure
    Testing templates; document the provenance so staff can trace it.
    """
    if borrow_dir is not None:
        model_repo = borrow_dir.parent.parent.name  # <repo>/InputData/elec -> <repo>
        return {
            'purpose': 'Non-VRE Technology Tables (borrowed from country EPS model)',
            'source': 'Energy Innovation',
            'publication': f'EPS model input files ({model_repo})',
            'year': 2025,
            'url': 'https://energyinnovation.org/',
            'info': 'Non-derived techs (all SYSHECF technologies except the pipeline-'
                    'derived solar-pv, solar-pv-dist, onshore-wind, offshore-wind) are '
                    f'copied verbatim from {borrow_dir}\\SYSHECF\\ — the country-specific '
                    'EPS model capacity-factor tables — rather than the generic EPS '
                    'Structure Testing templates. Their tabs hold static values; edit '
                    'directly. Verify against the model source before use.',
        }
    return {
        'purpose': 'Non-VRE Technology Tables',
        'source': 'Energy Innovation',
        'publication': 'EPS Structure Testing SYSHECF templates',
        'year': 2025,
        'url': 'https://energyinnovation.org/',
        'info': 'Non-derived techs copied unchanged from the EPS template (see '
                'EPS_export_coverage.csv). Their tabs hold static values — edit directly.',
    }


def run_notes(family: str, country_key: str, preset: dict, days_txt: str) -> list:
    today = dt.date.today().isoformat()
    cal = preset.get('calibration_method', 'level_seasonal')
    cf_mode = preset.get('cf_calibration_mode', 'cap_redistribute')
    tz = preset.get('timezone') or 'UTC (no localization)'
    notes = [
        ('Methodology overview',
         f'{family} tables for the EPS Vensim model from the international pipeline '
         f'(run_pipeline.py) {country_key} run. Representative-day profiles: each output '
         'cell is the hourly value on the slice\'s representative day'
         + (' divided by the category\'s annual demand.' if family == 'SHELF'
            else ' (capacity factor, no re-normalization).')
         + ' Edit the source tab or the Clustering tab (slice assignment / representative '
           'days) and all outputs recompute.'),
        ('Clustering',
         'K6/H24 representative-day clustering (cluster_days_repday via cluster_timeslices) '
         f'on net load = calibrated demand − Ember-calibrated solar/wind generation. Days '
         f'per timeslice: {days_txt}. Representative days are editable on the Clustering '
         'tab (columns G/H).'),
        ('Run configuration',
         f'country: {country_key}; demand calibration: {cal}; CF calibration: {cf_mode}; '
         f'timezone: {tz}; built: {today}; build script: scripts/build_run_workbooks.py; '
         'source-of-record CSVs: workbook_sources/ next to this file. This workbook is '
         'self-contained: outputs derive from the source tabs via formulas, not from the '
         'pipeline\'s per-category CSV exports.'),
        ('Relationship to canonical eps-us files',
         'For the U.S., canonical EPS inputs come from the Cambium-based national pipeline; '
         'this workbook documents the international-workflow baseline. For other countries '
         'this workflow is the primary source — still subject to staff review.'),
        ('Caveats',
         'All values are inputs for staff review. Verify against the primary sources above '
         'and the project methodology (CLAUDE.md, DECISIONS.md) before use in any work '
         'product. Where the CF calibration multiplier is large, the synthetic wind/solar '
         'shape needs upstream tuning — see the calibration diagnostics in the run metrics.'),
    ]
    if family == 'SHELF':
        notes.insert(2, (
            'Category resolution',
            'Every category maps 1:1 to one Demand hourly source (Zapata) column via '
            'representative-day load factors — no template splits. Heating/cooling/lighting '
            'map to their like-named end uses; residential- and commercial-appliances take '
            'water-heating; -other takes other; commercial-lighting follows residential '
            'lighting; the six transport modes (LDVs, HDVs, aircraft, rail, ships, '
            'motorbikes) all take the single transport shape; industry — and its '
            'district-heat-hydrogen / geoeng mirrors — takes industry; envelopes are zero; '
            'datacenters are a flat 1/8760. The full map is SHELF_MAP in '
            'scripts/build_run_workbooks.py. (district-heat-hydrogen / geoeng mirroring '
            'industry differs from the eps-us zero convention — review before use.)'))
    return notes


# ---------------------------------------------------------------------------
# SHELF
# ---------------------------------------------------------------------------

def add_checker_tab(wb, categories: list[str]):
    """Energy-balance check: one column per SHELF category, one row per slice.

    Each cell sums a category tab's 24 hourly load factors for that slice; the
    'Check' row is SUMPRODUCT(days, slice sums) — the share of annual demand the
    six timeslices actually reproduce. **This must equal 1.0** for every non-zero
    category, or EPS will allocate more or less than the category's annual
    demand across the year.

    Reads the category tabs through INDIRECT on the header row, so adding a
    category means adding a column header and nothing else.
    """
    ws = wb.create_sheet('Checker', 0)
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 26
    ws.cell(1, 2, 'Days per Electricity Timeslice').font = Font(bold=True)
    for j, cat in enumerate(categories):
        col = 3 + j
        ws.column_dimensions[get_column_letter(col)].width = 30
        ws.cell(1, col, f'SHELF-{cat}').font = Font(bold=True)
    for i, sl in enumerate(SLICES):
        row = 2 + i
        ws.cell(row, 1, sl)
        ws.cell(row, 2, f"='SHELF-days-per-timeslice'!B{row}")
        for j in range(len(categories)):
            letter = get_column_letter(3 + j)
            ws.cell(row, 3 + j,
                    f'=SUM(INDIRECT("\'"&{letter}$1&"\'!B"&ROW($A{row})&":Y"&ROW($A{row})))')
    check_row = 2 + len(SLICES) + 1  # blank spacer row between slices and Check
    ws.cell(check_row, 1, 'Check').font = Font(bold=True)
    for j in range(len(categories)):
        letter = get_column_letter(3 + j)
        cell = ws.cell(check_row, 3 + j,
                       f'=ROUND(SUMPRODUCT($B2:$B7,{letter}2:{letter}7),10)')
        cell.font = Font(bold=True)
    ws.cell(check_row + 2, 1, 'Each Check must equal 1.0 for every non-zero category — '
                              'it is the fraction of annual demand the six timeslices '
                              'reproduce. Zero categories (envelopes) read 0.')
    ws.freeze_panes = 'C2'
    return ws


def _run_target_year(frame: pd.DataFrame) -> int | None:
    """Target year of the run, read off an hourly source tab's timestamps."""
    for col in ('timestamp', 'time', 'datetime'):
        if col in frame.columns:
            stamps = pd.to_datetime(frame[col], errors='coerce').dropna()
            if not stamps.empty:
                return int(stamps.dt.year.mode().iloc[0])
    return None


def build_shelf(eps_dir: Path, country_key: str, preset: dict,
                demand: pd.DataFrame, clus: pd.DataFrame):
    out_path = eps_dir / SHELF_NAME
    n = len(demand)
    days_txt = '  '.join(
        f'{s}={int(d)}' for s, d in
        zip(clus['slice_name'].dropna(), clus['days'].dropna()))

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    add_about_tab(wb, 'SHELF', out_path.stem,
                  demand_sources_for(country_key, preset, _run_target_year(demand)),
                  run_notes('SHELF', country_key, preset, days_txt))
    add_clustering_tab(wb, clus)
    col_letters = add_hourly_source_tab(wb, 'Demand hourly source', demand)
    hour_l = col_letters['hour_of_day']
    slice_l = col_letters['slice']
    SRC = 'Demand hourly source'

    # days-per-timeslice
    ws = wb.create_sheet('SHELF-days-per-timeslice')
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['B'].width = 22
    ws.cell(1, 1, 'Unit: days')
    ws.cell(1, 2, 'Days per Timeslice')
    for i, sl in enumerate(SLICES):
        ws.cell(2 + i, 1, sl)
        ws.cell(2 + i, 2, f'=Clustering!$B${3 + i}')

    missing: list = []
    for cat, (kind, payload) in SHELF_MAP:
        ws = _out_tab_shell(wb, f'SHELF-{cat}', SHELF_UNIT)
        if kind == 'direct' and payload not in col_letters:
            missing.append((cat, payload))
            kind = 'zeros'  # degrade gracefully: zero the tab
        for r_off, sl in enumerate(SLICES):
            slice_cell = f'$A{2 + r_off}'
            for h in range(24):
                if kind == 'zeros':
                    ws.cell(2 + r_off, 2 + h, 0.0)
                elif kind == 'flat':
                    ws.cell(2 + r_off, 2 + h, 1.0 / 8760.0)
                elif kind == 'direct':
                    pick, tot = _slice_mean_lf(SRC, col_letters[payload], slice_l,
                                               hour_l, n, slice_cell, h)
                    ws.cell(2 + r_off, 2 + h, f'=IFERROR({pick}/{tot},0)')

    add_checker_tab(wb, [cat for cat, _ in SHELF_MAP])

    try:
        wb.save(out_path)
    except PermissionError:
        print(f'  ERROR: cannot write {out_path} — close it in Excel first.')
        return
    print(f'[shelf] wrote {out_path}  ({len(wb.sheetnames)} tabs)')
    if missing:
        print('[shelf] WARN: demand column absent — tab(s) zeroed: '
              + ', '.join(f'{c}<-{col}' for c, col in missing))


# ---------------------------------------------------------------------------
# SYSHECF
# ---------------------------------------------------------------------------

def build_syshecf(eps_dir: Path, country_key: str, preset: dict,
                  cf: pd.DataFrame, clus: pd.DataFrame,
                  borrow_dir: Path):
    out_path = eps_dir / SYSHECF_NAME
    n = len(cf)
    days_txt = '  '.join(
        f'{s}={int(d)}' for s, d in
        zip(clus['slice_name'].dropna(), clus['days'].dropna()))

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    add_about_tab(wb, 'SYSHECF', out_path.stem,
                  cf_sources_for(country_key, preset, borrow_dir, _run_target_year(cf)),
                  run_notes('SYSHECF', country_key, preset, days_txt))
    add_clustering_tab(wb, clus)
    col_letters = add_hourly_source_tab(wb, 'CF hourly source', cf)
    hour_l = col_letters['hour_of_day']
    slice_l = col_letters['slice']
    SRC = 'CF hourly source'

    derived_techs: list[str] = []
    borrowed: list[str] = []
    missing_borrow: list[str] = []
    for file_name, spec in EPS_SYSHECF_FILE_MAP.items():
        tech = file_name[len('SYSHECF-'):]
        borrow_csv = borrow_dir / 'SYSHECF' / f'{file_name}.csv'
        borrow_tbl = read_eps_table(borrow_csv) if borrow_csv.exists() else None
        header = borrow_tbl.index.name if borrow_tbl is not None else SYSHECF_UNIT
        # Onshore/offshore wind resolve through a 'first_available' spec (their
        # own site-type CF column when the run has one, else the blended
        # wind_cf), so ask the pipeline which column the spec lands on rather
        # than pattern-matching 'direct' here.
        resolved = resolve_direct_cf_spec(spec, cf.columns)
        if resolved is not None:
            # VRE tech — derived from the CF hourly source (never borrowed).
            column, mult = resolved
            ws = _out_tab_shell(wb, file_name, header)
            for r_off, sl in enumerate(SLICES):
                slice_cell = f'$A{2 + r_off}'
                for h in range(24):
                    avg = _slice_mean_cf(SRC, col_letters[column], slice_l, hour_l,
                                         n, slice_cell, h)
                    ws.cell(2 + r_off, 2 + h, _cf_cell(avg, mult))
            derived_techs.append(tech)
        else:
            # Non-VRE ("other") tech — borrowed verbatim from the country EPS model.
            if borrow_tbl is None:
                missing_borrow.append(tech)
                continue
            ws = _out_tab_shell(wb, file_name, header)
            tbl6 = borrow_tbl.reindex(index=SLICES, columns=HOUR_COLS)
            for r_off, sl in enumerate(SLICES):
                for h in range(24):
                    v = tbl6.loc[sl, HOUR_COLS[h]]
                    ws.cell(2 + r_off, 2 + h, 0.0 if pd.isna(v) else float(v))
            borrowed.append(tech)

    try:
        wb.save(out_path)
    except PermissionError:
        print(f'  ERROR: cannot write {out_path} — close it in Excel first.')
        return
    print(f'[syshecf] wrote {out_path}  ({len(wb.sheetnames)} tabs)')
    print(f'[syshecf] derived {len(derived_techs)} VRE tech(s) from CF source: '
          f'{", ".join(sorted(derived_techs))}')
    print(f'[syshecf] borrowed {len(borrowed)} non-VRE tech table(s) from '
          f'{borrow_dir}\\SYSHECF: {", ".join(sorted(borrowed))}')
    if missing_borrow:
        print(f'[syshecf] WARN: {len(missing_borrow)} tech(s) not found in borrow '
              f'dir, tab(s) omitted: {", ".join(sorted(missing_borrow))}')


# ---------------------------------------------------------------------------
# ELCCAfR — ELCC Adjustment for Reliability
#
# Same 6x24 grid as SHELF/SYSHECF. Each cell is a capacity-adequacy derate that
# EPS multiplies into the RELIABILITY branch only, never into dispatch. It is a
# second statistic over the very same hourly CF column and the very same
# per-slice day set that produced SYSHECF, so:
#
#     SYSHECF[slice, hour]  =  mean CF over the slice's days at that hour
#     ELCCAfR[slice, hour]  =  <low statistic> CF / that same mean
#     ==> SYSHECF x ELCCAfR =  the worst day the slice contains
#
# The workbook is laid out to make that visible: the 'Peak CF statistics' tab
# holds the mean block (which reproduces SYSHECF) and the worst-day block side
# by side, and each output tab's cells are a plain guarded ratio of the two.
# ---------------------------------------------------------------------------

def _stats_ranges(src: str, col_letter: str, slice_l: str, hour_l: str,
                  n: int) -> tuple[str, str, str]:
    """(data, slice-criteria, hour-criteria) ranges on the hourly source tab."""
    return (f"'{src}'!${col_letter}$2:${col_letter}${n + 1}",
            f"'{src}'!${slice_l}$2:${slice_l}${n + 1}",
            f"'{src}'!${hour_l}$2:${hour_l}${n + 1}")


def _slice_mean_cf_ref(src: str, col_letter: str, slice_l: str, hour_l: str, n: int,
                       slice_cell: str, hour_cell: str) -> str:
    """Slice-mean CF, with the hour taken from a cell rather than a literal.

    Same statistic as _slice_mean_cf (which SYSHECF uses with a literal hour) —
    pointing at the stats tab's numeric hour row instead makes the block fillable
    across and keeps the criterion visible on the sheet.
    """
    rng, slc, hr = _stats_ranges(src, col_letter, slice_l, hour_l, n)
    return f'AVERAGEIFS({rng},{slc},{slice_cell},{hr},{hour_cell})'


def _slice_low_cf(src: str, col_letter: str, slice_l: str, hour_l: str, n: int,
                  slice_cell: str, hour_cell: str, statistic: str) -> str:
    """Low-statistic CF over the days in one (slice, hour) cell.

    'min' -> MINIFS (Excel 2019+/365, LibreOffice 7+). Written with the `_xlfn.`
             prefix, which is how the OOXML file must store functions added after
             the original spec; a bare 'MINIFS' in the XML opens as #NAME? in
             Excel. (Excel itself rewrites it to this form on save.)
    'pNN' -> PERCENTILE(IF(...)) which needs dynamic-array Excel (365/2021+);
             in older Excel the cell must be re-entered with Ctrl+Shift+Enter.
    """
    rng, slc, hr = _stats_ranges(src, col_letter, slice_l, hour_l, n)
    if statistic == 'min':
        return f'_xlfn.MINIFS({rng},{slc},{slice_cell},{hr},{hour_cell})'
    q = float(statistic[1:]) / 100.0
    return f'PERCENTILE(IF(({slc}={slice_cell})*({hr}={hour_cell}),{rng}),{q})'


def _statistic_label(statistic: str) -> str:
    if statistic == 'min':
        return 'worst day (minimum)'
    return f'{float(statistic[1:]):g}th-percentile day'


def elccafr_sources_for(country_key: str, preset: dict,
                        demand_year: int | None = None) -> list:
    """ELCCAfR draws on exactly the same VRE CF sources as SYSHECF, plus the
    judgment values that are not derived from data.

    Deliberately drops the "non-VRE tables borrowed from the country EPS model"
    block that cf_sources_for adds: ELCCAfR borrows nothing — techs with no CF
    series of their own are 1.0 by construction, or mirror a tech that has one.
    """
    sources = [s for s in cf_sources_for(country_key, preset, None, demand_year)
               if 'Non-VRE Technology Tables' not in s['purpose']]
    sources.append({
        'purpose': 'Non-Derived ELCCAfR Values (judgment parameters)',
        'source': 'Energy Innovation',
        'publication': 'eps-us InputData/elec/ELCCAfR (US reference values)',
        'year': 2026,
        'url': 'https://energyinnovation.org/',
        'info': 'Three ELCCAfR inputs are not derived from capacity-factor data. (1) The '
                'demand-altering-technologies derate on peak slices, carried over from the '
                'eps-us value pending a regional view on demand-response reliability. '
                '(2) Technologies whose SYSHECF table is a borrowed constant have no '
                'within-slice CF variation, so their derate is exactly 1.0 by construction '
                'rather than by measurement — including HYDRO, whose real capacity credit '
                'does vary between wet and dry years. (3) Solar thermal has no independent '
                'CF series here, so it mirrors solar PV rather than sitting at 1.0: it '
                'shares the solar resource, and crediting CSP as fully firm at the peak '
                'hour would overstate its capacity value. All three are flagged for staff '
                'review.',
    })
    return sources


def elccafr_run_notes(country_key: str, preset: dict, days_txt: str,
                      statistic: str, demand_altering: float,
                      derived: list[str], constant: list[str],
                      mirrors: dict[str, str] | None = None) -> list:
    today = dt.date.today().isoformat()
    tz = preset.get('timezone') or 'UTC (no localization)'
    stat_label = _statistic_label(statistic)
    return [
        ('What this file is',
         'ELCCAfR — ELCC Adjustment for Reliability — is a per-(technology, timeslice, hour) '
         'capacity-adequacy derate between 0 and 1. EPS multiplies it into the RELIABILITY '
         'calculation only, never into dispatch: "Last Year Hourly Bid Electricity Capacity '
         'Factors for Reliability by Plant Type" = the bid capacity factors x ELCCAfR, and '
         'the demand-altering file scales the peak-load-reduction term in "Total Electricity '
         'Demand by Hour Plus Reserve Margin After Demand Altering Technologies". A cell of '
         '1.0 means no derate.'),
        ('How each cell is computed',
         f'For each peak slice and hour-of-day, over the days the clustering assigned to that '
         f'slice: ELCCAfR = {stat_label} capacity factor / mean capacity factor. Both '
         'statistics are taken over the identical day set. See the '
         f'"{ELCCAfR_STATS_TAB}" tab, which shows the two blocks the ratio is built from, '
         f'and the "{ELCCAfR_RELATION_TAB}" tab for how this ties back to SHELF and SYSHECF.'),
        ('Why the four non-peak rows are 1.0',
         'Both reliability variables are summed over "Binding Peak Hour for Reliability '
         'Additions[peak day electricity timeslice!, Hour!]", so only Summer Peak and Winter '
         'Peak can ever bind. Leaving Winter/Spring/Summer/Fall at 1.0 also prevents the '
         'derate from being read as a midday dispatch penalty on solar. Non-peak rows are '
         '1.0 by definition — they can never bind in the EPS reliability calculation.'),
        ('Degenerate cells',
         f'Where the mean capacity factor over a slice\'s days is below {ELCCAfR_DEGENERATE_MEAN} '
         '— solar overnight, for example — the ratio would be 0/0, so the cell is set to 1.0. '
         'SYSHECF is ~0 in those cells anyway, so the product is unchanged.'),
        ('Which technologies are derived',
         f'Derived from the run\'s hourly CF series ({len(derived)}): '
         f'{", ".join(derived) if derived else "none"}. '
         + (f'Mirrored ({len(mirrors)}): '
            + '; '.join(f'{k[len("ELCCAfR-"):]} follows {v[len("ELCCAfR-"):]}'
                        for k, v in mirrors.items())
            + ' — no independent CF series, but a shared resource, so the derate tracks '
              'the technology it mirrors instead of sitting at 1.0. '
            if mirrors else '')
         + f'Constant 1.0 ({len(constant)}): these '
         'technologies\' SYSHECF tables are borrowed constants per (slice, hour), so their '
         'minimum and mean over a slice\'s days coincide and the derate is 1.0 by '
         'construction, not by measurement. Distributed solar PV and pumped hydro have NO '
         'ELCCAfR file — neither is a member of the EPS "Electricity Source" subscript.'),
        ('Sample-size caveat on the statistic',
         f'Days per timeslice in this run: {days_txt}. A straight minimum takes the worst of '
         'however many days a slice happens to hold, so slices with more days get a deeper '
         'derate for reasons that are an artifact of clustering rather than of the resource. '
         'The eps-us peak slices hold 11 and 10 days. Set the preset key '
         '"elccafr_statistic" to "p05" for a sample-size-stable alternative; "min" '
         'reproduces the documented eps-us methodology.'),
        ('Caveat on the underlying wind capacity factors',
         'Where the preset takes wind from Renewables.ninja per-site simulations, the hourly '
         'CF is a day-of-year x hour climatology averaged across sites and years. That '
         'averaging removes interannual and cross-site variability, so the day-to-day spread '
         'this derate measures is narrower than a single-weather-year fleet series would '
         'show, and the derate is likely too generous. Verify against unaveraged site-year '
         'data before relying on the wind values.'),
        ('Run configuration',
         f'country: {country_key}; statistic: {statistic}; demand-altering peak value: '
         f'{demand_altering}; timezone: {tz}; built: {today}; build script: '
         'scripts/build_run_workbooks.py; source-of-record CSVs: workbook_sources/ next to '
         'this file. Requires MINIFS (Excel 2019+/365 or LibreOffice 7+).'),
        ('Caveats',
         'All values are inputs for staff review. The US ELCCAfR files that regional EPS '
         'models currently carry are byte-identical copies of the eps-us tables; replacing '
         'them changes reliability-driven capacity build, so diff and review before '
         'deploying. Verify against the primary sources above and against CLAUDE.md / '
         'DECISIONS.md before use in any work product.'),
    ]


def add_elccafr_relationship_tab(wb, statistic: str, derived: list[str]):
    """Documentation tab: how ELCCAfR relates to the SHELF and SYSHECF files."""
    ws = wb.create_sheet(ELCCAfR_RELATION_TAB, 1)
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 44
    ws.column_dimensions['C'].width = 44
    ws.column_dimensions['D'].width = 44
    wrap = openpyxl.styles.Alignment(horizontal='left', vertical='top', wrap_text=True)
    stat_label = _statistic_label(statistic)

    r = 1
    ws.cell(r, 1, 'How ELCCAfR relates to the SHELF and SYSHECF files').font = Font(bold=True, size=12)
    r += 2
    ws.cell(r, 1, 'All three families share one grid').font = SECTION_FONT
    ws.cell(r, 1).fill = SECTION_FILL
    r += 1
    for c, name in ((1, ''), (2, 'SHELF'), (3, 'SYSHECF'), (4, 'ELCCAfR (this file)')):
        cell = ws.cell(r, c, name)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
    r += 1
    rows = [
        ('Grid',
         '6 timeslices x 24 hours', '6 timeslices x 24 hours', '6 timeslices x 24 hours'),
        ('One file per',
         'demand category (22)',
         'generation technology (25)',
         'Electricity Source technology (24) + demand-altering technologies (1)'),
        ('What a cell means',
         "share of the category's ANNUAL demand falling in that slice-hour",
         'expected capacity factor in that slice-hour',
         'fraction of the SYSHECF capacity factor that can be counted on for capacity adequacy'),
        ('How the cell is computed',
         'AVERAGEIFS(demand col, slice, hour) / SUM(demand col)',
         'AVERAGEIFS(CF col, slice, hour) — the MEAN over the slice\'s days',
         f'{stat_label} CF over the SAME days / that SAME mean'),
        ('EPS reads it into',
         'SHELF Seasonal Hourly Equipment Load Factors by End Use',
         'SYSHECF Start Year Seasonal Expected Hourly Electricity Capacity Factors',
         'ELCCAfR ELCC Adjustment for Reliability for Generation Sources / '
         'for Demand Altering Technologies'),
        ('Used in',
         'hourly demand allocation', 'DISPATCH and reliability',
         'RELIABILITY ONLY — never dispatch'),
        ('Built from',
         'workbook_sources/demand_hourly_source.csv',
         'workbook_sources/cf_hourly_source.csv',
         'workbook_sources/cf_hourly_source.csv (the same columns as SYSHECF)'),
    ]
    for label, a, b, c in rows:
        ws.cell(r, 1, label).font = Font(bold=True)
        for col, val in ((2, a), (3, b), (4, c)):
            ws.cell(r, col, val).alignment = wrap
        ws.row_dimensions[r].height = 46
        r += 1

    r += 1
    ws.cell(r, 1, 'The identity that ties ELCCAfR to SYSHECF').font = SECTION_FONT
    ws.cell(r, 1).fill = SECTION_FILL
    r += 1
    for text in [
        'A SYSHECF cell is the MEAN capacity factor over the days the clustering assigned to '
        'that slice, at that hour (CLAUDE.md section 6). ELCCAfR divides a LOW statistic over '
        'those same days by that same mean. So the two multiply back to the low statistic:',
        '',
        f'        SYSHECF[slice, hour]  x  ELCCAfR[slice, hour]  =  {stat_label} capacity '
        'factor at that hour',
        '',
        'That is exactly the quantity EPS wants when it evaluates whether firm capacity is '
        'adequate in the binding peak hour: not what a technology produces on an average peak '
        'day, but what it can be counted on to produce on a bad one.',
        '',
        f'The "{ELCCAfR_STATS_TAB}" tab computes both blocks from the CF hourly source and '
        'checks the identity live — the Check rows there must be 0. Keeping both statistics '
        'over the identical day set is what makes it hold; computing ELCCAfR over a '
        'separately pinned set of peak days would break it.',
        '',
        'Two places where the identity deliberately does not hold: (1) degenerate cells, '
        f'where the mean is below {ELCCAfR_DEGENERATE_MEAN} and the derate is forced to 1.0; '
        '(2) the four non-peak rows, which are forced to 1.0 because they can never bind.',
    ]:
        c = ws.cell(r, 1, text)
        c.alignment = wrap
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        ws.row_dimensions[r].height = 30 if text else 8
        r += 1

    r += 1
    ws.cell(r, 1, 'What changes if you edit something').font = SECTION_FONT
    ws.cell(r, 1).fill = SECTION_FILL
    r += 1
    for text in [
        'Edit the Clustering tab (DOY to slice assignment) and every ELCCAfR cell recomputes, '
        'because the slice column on the CF hourly source tab is a VLOOKUP into it. The same '
        'edit changes SYSHECF and SHELF in their workbooks, so re-run all three builders '
        'together rather than editing one in isolation. Clusters are defined around net peak '
        'load shapes so both SYSHECF and SHELF impact clusters.',
        'Edit a CF hourly source value and the derate for that technology recomputes. Note '
        'that a calibration multiplier applied uniformly to a CF series does NOT change '
        'ELCCAfR — it cancels in the ratio. Only the day-to-day SHAPE matters here.',
        f'Derived technologies in this run: {", ".join(derived) if derived else "none"}. '
        'Every other technology tab holds literal 1.0 values and can be edited directly if a '
        'region has evidence for a non-unity derate (hydro is the likely candidate).',
    ]:
        c = ws.cell(r, 1, text)
        c.alignment = wrap
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        ws.row_dimensions[r].height = 44
        r += 1
    return ws


def add_peak_cf_stats_tab(wb, cf: pd.DataFrame, col_letters: dict, src: str,
                          derived: list[tuple[str, str, str]], statistic: str
                          ) -> dict[str, dict[str, int]]:
    """Mean and low-statistic CF blocks per derived technology, plus a live
    check of the SYSHECF x ELCCAfR identity.

    ``derived`` is a list of (elccafr file name, tech slug, CF source column).
    Returns {tech: {'mean_row0': r, 'low_row0': r}} — the Excel row of the
    'Winter' row in each block, so output tabs can point at slice i as row0 + i.
    """
    ws = wb.create_sheet(ELCCAfR_STATS_TAB)
    ws.column_dimensions['A'].width = 26
    for c in range(2, 26):
        ws.column_dimensions[get_column_letter(c)].width = 11
    wrap = openpyxl.styles.Alignment(horizontal='left', vertical='top', wrap_text=True)
    n = len(cf)
    hour_l = col_letters['hour_of_day']
    slice_l = col_letters['slice']
    stat_label = _statistic_label(statistic)

    ws.cell(1, 1, 'Peak capacity-factor statistics — the two blocks every ELCCAfR cell '
                  'is built from').font = Font(bold=True, size=12)
    ws.cell(2, 1, 'Step 1 is the mean over each slice\'s days: it reproduces the SYSHECF '
                  f'table. Step 2 is the {stat_label} over the same days. ELCCAfR = Step 2 / '
                  'Step 1, so Step 1 x ELCCAfR = Step 2 — the Check rows verify that.')
    ws.cell(2, 1).alignment = wrap
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=25)
    ws.row_dimensions[2].height = 30

    # Numeric hour row. Every AVERAGEIFS/MINIFS below takes its hour criterion
    # from B$3:Y$3 rather than a hardcoded literal, so a block can be filled
    # across and the criterion is visible on the sheet instead of buried in 24
    # separate formulas.
    HOUR_ROW = 3
    ws.cell(HOUR_ROW, 1, 'Hour (Numeric)').font = Font(italic=True)
    ws.cell(HOUR_ROW, 2, 0)
    for h in range(1, 24):
        prev = get_column_letter(1 + h)
        ws.cell(HOUR_ROW, 2 + h, f'={prev}{HOUR_ROW}+1')

    def _header_row(row: int):
        cell = ws.cell(row, 1, 'Slice')
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        for h, name in enumerate(HOUR_COLS):
            c = ws.cell(row, 2 + h, name)
            c.font = HEADER_FONT
            c.fill = HEADER_FILL

    rows_map: dict[str, dict[str, int]] = {}
    r = 4
    for file_name, tech, column in derived:
        title = ws.cell(r, 1, f'{tech}   (CF hourly source column: {column})')
        title.font = SECTION_FONT
        title.fill = SECTION_FILL
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=25)
        r += 1

        ws.cell(r, 1, f'Step 1 — mean CF over the days in each slice   '
                      f'(reproduces SYSHECF-{tech})').font = Font(italic=True)
        r += 1
        _header_row(r)
        r += 1
        mean_row0 = r
        for i, sl in enumerate(SLICES):
            ws.cell(r + i, 1, sl)
            for h in range(24):
                hour_cell = f'{get_column_letter(2 + h)}${HOUR_ROW}'
                ws.cell(r + i, 2 + h,
                        '=' + _slice_mean_cf_ref(src, col_letters[column], slice_l, hour_l,
                                                 n, f'$A{r + i}', hour_cell))
        r += len(SLICES)

        ws.cell(r, 1, f'Step 2 — {stat_label} CF over exactly the same days'
                ).font = Font(italic=True)
        r += 1
        _header_row(r)
        r += 1
        low_row0 = r
        for i, sl in enumerate(SLICES):
            ws.cell(r + i, 1, sl)
            for h in range(24):
                hour_cell = f'{get_column_letter(2 + h)}${HOUR_ROW}'
                ws.cell(r + i, 2 + h,
                        '=' + _slice_low_cf(src, col_letters[column], slice_l, hour_l,
                                            n, f'$A{r + i}', hour_cell, statistic))
        r += len(SLICES)

        ws.cell(r, 1, 'Check — Step 1 x ELCCAfR - Step 2 must be 0 on the peak rows'
                ).font = Font(italic=True)
        r += 1
        _header_row(r)
        r += 1
        for sl in EPS_PEAK_TIMESLICES:
            i = SLICES.index(sl)
            ws.cell(r, 1, sl)
            for h in range(24):
                letter = get_column_letter(2 + h)
                ws.cell(r, 2 + h,
                        f"=ROUND({letter}{mean_row0 + i}*'{file_name}'!{letter}{2 + i}"
                        f'-{letter}{low_row0 + i},12)')
            r += 1

        rows_map[tech] = {'mean_row0': mean_row0, 'low_row0': low_row0}
        r += 2

    ws.cell(r, 1, f'Check rows read 0 except where the Step 1 mean is below '
                  f'{ELCCAfR_DEGENERATE_MEAN} and the derate is forced to 1.0 '
                  '(solar overnight).')
    ws.cell(r, 1).alignment = wrap
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=25)
    ws.freeze_panes = 'B1'
    return rows_map


def build_elccafr(eps_dir: Path, country_key: str, preset: dict,
                  cf: pd.DataFrame, clus: pd.DataFrame):
    """Write the ELCCAfR CSVs and the self-contained ELCCAfR workbook."""
    out_path = eps_dir / ELCCAfR_NAME
    csv_dir = eps_dir / 'ELCCAfR'
    csv_dir.mkdir(exist_ok=True)
    n = len(cf)
    statistic = str(preset.get('elccafr_statistic', ELCCAfR_STATISTIC_DEFAULT))
    demand_altering = float(
        preset.get('elccafr_demand_altering', ELCCAfR_DEMAND_ALTERING_DEFAULT))
    days_txt = '  '.join(
        f'{s}={int(d)}' for s, d in
        zip(clus['slice_name'].dropna(), clus['days'].dropna()))

    # Resolve each ELCCAfR file against the SYSHECF spec that drives it, using
    # the same resolver the SYSHECF builder uses so 'first_available' wind specs
    # land on the same column in both families.
    derived: list[tuple[str, str, str]] = []
    constant: list[str] = []
    tables: dict[str, pd.DataFrame] = {}
    for file_name, syshecf_file in EPS_ELCCAfR_FILE_MAP.items():
        tech = file_name[len('ELCCAfR-'):]
        resolved = resolve_direct_cf_spec(EPS_SYSHECF_FILE_MAP.get(syshecf_file), cf.columns)
        if resolved is None:
            constant.append(tech)
            tables[file_name] = build_elccafr_constant_table(1.0)
        else:
            column, _multiplier = resolved  # the multiplier cancels in the ratio
            derived.append((file_name, tech, column))
            tables[file_name] = build_elccafr_table(
                cf[column], cf['slice'], cf['hour_of_day'], statistic=statistic)

    # Mirrors (EPS_ELCCAfR_MIRRORS): a tech with no CF series of its own tracks a
    # related tech that has one, rather than the 1.0 its borrowed SYSHECF implies.
    derived_files = {f for f, _, _ in derived}
    mirrors: dict[str, str] = {}
    for file_name, source_file in EPS_ELCCAfR_MIRRORS.items():
        if (file_name in derived_files or file_name not in tables
                or source_file not in derived_files):
            continue
        tables[file_name] = tables[source_file].copy()
        mirrors[file_name] = source_file
        constant.remove(file_name[len('ELCCAfR-'):])

    tables[ELCCAfR_DEMAND_ALTERING_FILE] = build_elccafr_demand_altering_table(demand_altering)

    for file_name, table in tables.items():
        header = (ELCCAfR_DEMAND_ALTERING_UNIT if file_name == ELCCAfR_DEMAND_ALTERING_FILE
                  else EPS_ELCCAfR_HEADERS[file_name])
        out = table.copy()
        out.index.name = header
        out.to_csv(csv_dir / f'{file_name}.csv', float_format='%.4f')

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    add_about_tab(wb, 'ELCCAfR', out_path.stem,
                  elccafr_sources_for(country_key, preset, _run_target_year(cf)),
                  elccafr_run_notes(country_key, preset, days_txt, statistic,
                                    demand_altering, [t for _, t, _ in derived], constant,
                                    mirrors))
    wb['About'].column_dimensions['A'].width = 18  # note labels are longer here
    add_elccafr_relationship_tab(wb, statistic, [t for _, t, _ in derived])
    add_clustering_tab(wb, clus)
    col_letters = add_hourly_source_tab(wb, 'CF hourly source', cf)
    SRC = 'CF hourly source'
    rows_map = add_peak_cf_stats_tab(wb, cf, col_letters, SRC, derived, statistic)

    for file_name, syshecf_file in EPS_ELCCAfR_FILE_MAP.items():
        tech = file_name[len('ELCCAfR-'):]
        ws = _out_tab_shell(wb, file_name, EPS_ELCCAfR_HEADERS[file_name])

        if file_name in mirrors:
            # Peak rows point straight at the mirrored tech's tab, so the two stay
            # in step if its CF source or the clustering changes. Non-peak rows are
            # literal 1.0, same as everywhere else.
            source_tab = mirrors[file_name]
            for r_off, sl in enumerate(SLICES):
                for h in range(24):
                    if sl not in EPS_PEAK_TIMESLICES:
                        ws.cell(2 + r_off, 2 + h, 1.0)
                    else:
                        letter = get_column_letter(2 + h)
                        ws.cell(2 + r_off, 2 + h, f"='{source_tab}'!{letter}{2 + r_off}")
            ws.cell(len(SLICES) + 3, 1,
                    f'{syshecf_file} mirrors {source_tab[len("ELCCAfR-"):]}')
            continue

        if tech not in rows_map:
            for r_off in range(len(SLICES)):
                for h in range(24):
                    ws.cell(2 + r_off, 2 + h, 1.0)
            ws.cell(len(SLICES) + 3, 1,
                    f'Constant 1.0: {syshecf_file} is a borrowed constant per (slice, hour), '
                    'so its minimum and mean over a slice\'s days coincide. Edit directly if '
                    'this region has evidence for a real derate.')
            continue

        # Derived tech. No footnote here — how the cell is built is documented on
        # the "Peak CF statistics" and relationship tabs, and repeating it on every
        # derived tab just crowds the grid.
        mean_row0 = rows_map[tech]['mean_row0']
        low_row0 = rows_map[tech]['low_row0']
        for r_off, sl in enumerate(SLICES):
            for h in range(24):
                if sl not in EPS_PEAK_TIMESLICES:
                    ws.cell(2 + r_off, 2 + h, 1.0)
                    continue
                letter = get_column_letter(2 + h)
                mean_ref = f"'{ELCCAfR_STATS_TAB}'!{letter}{mean_row0 + r_off}"
                low_ref = f"'{ELCCAfR_STATS_TAB}'!{letter}{low_row0 + r_off}"
                # IFERROR -> 1.0 matches the pipeline's behaviour for a
                # (slice, hour) with no rows: AVERAGEIFS would be #DIV/0! there.
                ws.cell(2 + r_off, 2 + h,
                        f'=IFERROR(IF({mean_ref}<{ELCCAfR_DEGENERATE_MEAN},1,'
                        f'MIN(1,MAX(0,{low_ref}/{mean_ref}))),1)')

    ws = _out_tab_shell(wb, ELCCAfR_DEMAND_ALTERING_FILE, ELCCAfR_DEMAND_ALTERING_UNIT)
    for r_off, sl in enumerate(SLICES):
        value = demand_altering if sl in EPS_PEAK_TIMESLICES else 1.0
        for h in range(24):
            ws.cell(2 + r_off, 2 + h, float(value))
    ws.cell(len(SLICES) + 3, 1,
            f'Judgment parameter, not derived: {demand_altering} on the peak slices, 1.0 '
            'elsewhere. Carried over from the eps-us value pending a regional view on how '
            'much demand-response peak reduction can be counted on for capacity adequacy.')

    try:
        wb.save(out_path)
    except PermissionError:
        print(f'  ERROR: cannot write {out_path} — close it in Excel first.')
        return
    print(f'[elccafr] wrote {out_path}  ({len(wb.sheetnames)} tabs)')
    print(f'[elccafr] wrote {len(tables)} CSVs to {csv_dir}')
    print(f'[elccafr] statistic={statistic}; derived {len(derived)} tech(s) from CF source: '
          f'{", ".join(t for _, t, _ in derived)}')
    if mirrors:
        print('[elccafr] mirrored: ' + '; '.join(
            f'{k[len("ELCCAfR-"):]} <- {v[len("ELCCAfR-"):]}' for k, v in mirrors.items()))
    print(f'[elccafr] constant 1.0 for {len(constant)} tech(s) whose SYSHECF is borrowed; '
          f'demand-altering peak value {demand_altering}')


def main():
    import argparse
    p = argparse.ArgumentParser(
        description='Build self-contained SHELF + SYSHECF + ELCCAfR workbooks for a '
                    'pipeline run from its workbook_sources CSVs.')
    p.add_argument('country', nargs='?', default='China',
                   help="Country name or alias (e.g. 'China', 'South Korea').")
    p.add_argument('--borrow-dir', default=None, metavar='PATH', required=True,
                   help="REQUIRED. Directory of the country EPS model's InputData/elec "
                        '(with a SYSHECF/ subfolder). Supplies the non-VRE SYSHECF tech '
                        'tables verbatim; the pipeline-derived VRE techs (solar-pv, '
                        'solar-pv-dist, onshore/offshore-wind) and all SHELF tabs are '
                        'derived from the run\'s hourly source tabs.')
    args = p.parse_args()
    country = args.country
    borrow_dir = Path(args.borrow_dir)
    if not (borrow_dir / 'SYSHECF').is_dir():
        raise SystemExit(
            f'--borrow-dir {borrow_dir} has no SYSHECF/ subfolder — expected a '
            "country EPS model's InputData/elec directory.")

    preset = get_country_preset(country)
    country_key = preset['output_country']
    eps_dir = ROOT / 'output' / f'{country_key}_timeslice_results_EPS'
    src = eps_dir / 'workbook_sources'
    if not src.is_dir():
        raise SystemExit(
            f'{src} not found — run the pipeline for {country_key} first '
            '(python run_pipeline.py) so the workbook-source CSVs exist.')
    demand = pd.read_csv(src / 'demand_hourly_source.csv')
    cf = pd.read_csv(src / 'cf_hourly_source.csv')
    clus = pd.read_csv(src / 'clustering.csv')
    print(f'[build] {country_key}: demand {demand.shape}, cf {cf.shape}; '
          f'borrowing non-VRE SYSHECF from {borrow_dir}')
    build_shelf(eps_dir, country_key, preset, demand, clus)
    build_syshecf(eps_dir, country_key, preset, cf, clus, borrow_dir=borrow_dir)
    build_elccafr(eps_dir, country_key, preset, cf, clus)
    print('[done] verify with: python scripts/verify_run_workbooks.py '
          f'"{country}" --borrow-dir "{borrow_dir}"')


if __name__ == '__main__':
    main()
