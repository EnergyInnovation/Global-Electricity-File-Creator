"""Build self-contained SHELF + SYSHECF Excel workbooks for ANY region's
run of the international pipeline (run_pipeline.py), directly from the run's
workbook_sources CSVs — following the build-input-xlsx skill. This builder is
the AUTHORITATIVE mapping from the Demand/CF hourly source (Zapata end-use
classifications) to the EPS output tabs; it does NOT read the pipeline's
per-category SHELF-*.csv / SYSHECF-*.csv exports.

SHELF: every category maps 1:1 to a Demand hourly source column via
representative-day load factors (see SHELF_MAP below) — no template splits.
  LF[slice, hour] = <col at (rep-day of slice, hour)> / SUM(col)

SYSHECF: the VRE techs (solar-pv, solar-pv-dist, onshore-wind, offshore-wind)
are derived from the CF hourly source; every other ("non-VRE") tech table is
borrowed verbatim from the country's own EPS model files (--borrow-dir).
  CF[slice, hour] = <cf col at (rep-day of slice, hour)> x multiplier

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

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from energy_timeslice_pipeline import (  # noqa: E402
    EPS_SYSHECF_FILE_MAP, get_country_preset,
)
from scripts.build_us_run_workbooks import (  # noqa: E402
    HOUR_COLS, OUTPUT_TAB_COLOR, SHELF_UNIT, SLICES,
    _out_tab_shell, _rep_doy_formula, _repday_lf,
    add_about_tab, add_clustering_tab, add_hourly_source_tab, read_eps_table,
)

SHELF_NAME = 'Seasonal Hourly Equipment Load Factors by End Use.xlsx'
SYSHECF_NAME = 'Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx'
SYSHECF_UNIT = 'Unit: dimensionless (capacity factor)'

# ---------------------------------------------------------------------------
# SHELF mapping — Zapata (Demand hourly source) column -> EPS SHELF tab.
# Reclassified 2026-07-14 per staff direction: every category is a direct 1:1
# rep-day load factor of one Demand hourly source column (NO template splits,
# no dependence on the untraceable "EPS Structure Testing" templates). Edit
# here to change how end uses map to EPS categories.
#   ('direct', <demand col>) : LF = rep-day value / annual sum of that column
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

def demand_sources_for(country_key: str) -> list:
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
        {'purpose': 'Observed Hourly Demand (calibration target)',
         'source': 'Open Energy Transition',
         'publication': 'DemandCast',
         'year': 2025,
         'url': 'https://github.com/open-energy-transition/demandcast',
         'info': 'Observed hourly national demand over the preset calibration window; the '
                 'calibrated hourly series is pasted into the "Demand hourly source" tab.'},
    ]


def cf_sources_for(country_key: str, preset: dict | None = None,
                   borrow_dir: Path | None = None) -> list:
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
                    '(see DECISIONS.md 2026-07-10). Both are pasted into the "CF hourly '
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

def build_shelf(eps_dir: Path, country_key: str, preset: dict,
                demand: pd.DataFrame, clus: pd.DataFrame):
    out_path = eps_dir / SHELF_NAME
    n = len(demand)
    days_txt = '  '.join(
        f'{s}={int(d)}' for s, d in
        zip(clus['slice_name'].dropna(), clus['days'].dropna()))

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    add_about_tab(wb, 'SHELF', out_path.stem, demand_sources_for(country_key),
                  run_notes('SHELF', country_key, preset, days_txt))
    add_clustering_tab(wb, clus)
    col_letters = add_hourly_source_tab(wb, 'Demand hourly source', demand)
    doy_l = col_letters['day_of_year']
    hour_l = col_letters['hour_of_day']
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
                    pick, tot = _repday_lf(SRC, col_letters[payload], doy_l, hour_l,
                                           n, slice_cell, h)
                    ws.cell(2 + r_off, 2 + h, f'=IFERROR({pick}/{tot},0)')

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
                  cf_sources_for(country_key, preset, borrow_dir),
                  run_notes('SYSHECF', country_key, preset, days_txt))
    add_clustering_tab(wb, clus)
    col_letters = add_hourly_source_tab(wb, 'CF hourly source', cf)
    doy_l = col_letters['day_of_year']
    hour_l = col_letters['hour_of_day']
    SRC = 'CF hourly source'

    derived_techs: list[str] = []
    borrowed: list[str] = []
    missing_borrow: list[str] = []
    for file_name, spec in EPS_SYSHECF_FILE_MAP.items():
        tech = file_name[len('SYSHECF-'):]
        borrow_csv = borrow_dir / 'SYSHECF' / f'{file_name}.csv'
        borrow_tbl = read_eps_table(borrow_csv) if borrow_csv.exists() else None
        header = borrow_tbl.index.name if borrow_tbl is not None else SYSHECF_UNIT
        derived = (isinstance(spec, dict) and spec.get('mode') == 'direct'
                   and spec.get('column') in cf.columns)
        if derived:
            # VRE tech — derived from the CF hourly source (never borrowed).
            ws = _out_tab_shell(wb, file_name, header)
            col_l = col_letters[spec['column']]
            mult = float(spec.get('multiplier', 1.0))
            rng = f"'{SRC}'!${col_l}$2:${col_l}${n + 1}"
            doy = f"'{SRC}'!${doy_l}$2:${doy_l}${n + 1}"
            hr = f"'{SRC}'!${hour_l}$2:${hour_l}${n + 1}"
            for r_off, sl in enumerate(SLICES):
                slice_cell = f'$A{2 + r_off}'
                for h in range(24):
                    avg = f'AVERAGEIFS({rng},{doy},{_rep_doy_formula(slice_cell)},{hr},{h})'
                    mult_txt = '' if mult == 1.0 else f'*{mult}'
                    ws.cell(2 + r_off, 2 + h, f'=IFERROR({avg}{mult_txt},0)')
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


def main():
    import argparse
    p = argparse.ArgumentParser(
        description='Build self-contained SHELF + SYSHECF workbooks for a '
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
    print('[done] verify with: python scripts/verify_run_workbooks.py '
          f'"{country}" --borrow-dir "{borrow_dir}"')


if __name__ == '__main__':
    main()
