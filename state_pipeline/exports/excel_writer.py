"""Write the consolidated per-state workbooks (v1.2):

  File 1: {STATE_LABEL} - Hourly Demand and SHELF.xlsx
    Tabs: About / Hourly Demand / Daily Summary / SHELF / Validation

  File 2: {STATE_LABEL} - SYSHECF.xlsx
    Tabs: About / Hourly Renewable CFs / SYSHECF
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

from ..builders.clustering import ClusteringResult, SLICE_NAMES
from ..builders.syshecf_builder import SYSHECF_DISPLAY_NAME


PIPELINE_VERSION = 'state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)'


def _to_py(v):
    """Cast numpy scalars to plain Python so xlsxwriter is happy."""
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


def _about_lines_demand_shelf(state_label: str, sources: dict,
                              industry_shape_mode: str,
                              curtailment_addback: dict | None) -> list[str]:
    run_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    cb = curtailment_addback or {}
    lines: list[str] = [
        f'State-level Hourly Demand and SHELF Pipeline Output - {state_label}',
        '',
        f'Pipeline: {PIPELINE_VERSION}',
        f'Run date: {run_date}',
        '',
        'Methodology (3-bullet summary):',
        '  1. Annual electricity by SHELF category from EPS state input files '
        '(BCEU buildings + BIFUbC industry + computed transport).',
        '  2. Hourly shapes from ResStock TMY3 (residential), ComStock TMY release 1 '
        '(commercial), and EFS Reference Moderate (transport + industry depending on mode).',
        '  3. Days clustered into 6 timeslices (Winter / Spring / Summer / Fall + '
        'pinned Summer Peak (top-5 days) + pinned Winter Peak (top-5 days)). '
        'SHELF LF tables = mean fraction of annual demand by hour-of-day per slice.',
        '',
        'Time convention: Local Standard Time, hour-beginning, 8760 hours, '
        '2018 non-leap calendar (Monday start).',
        '',
        'Weather-year mismatch (key caveat):',
        '  ResStock + ComStock = TMY3 (1991-2005 synthesized typical year).',
        '  Cambium 2022 = 2012 actual weather (re-indexed to 2018 calendar via 1-day shift).',
        '  EFS = 2012 actual weather. Per-hour correlation between demand and renewable '
        'generation is therefore artificial; net-load peak hour is subject to weather-year noise. '
        'See Validation tab Section 9 for diagnostic shifts and a daily-coupled correlation metric.',
        '',
        f'Industry shape mode used: {industry_shape_mode}',
        '  Options: efs (EFS weather-driven), flat (default; bulk industry constant), '
        'cambium_residual (busbar - resstock - comstock with flat fallback).',
        '',
        'Curtailment add-back factors (SYSHECF; informational here):',
        f'  {cb if cb else "(none) - VA VRE share is low; impact is negligible. "
                          "For high-VRE states (CA, TX), set non-zero values per CAISO/ERCOT reports."}',
        '',
        '----------------------------------------------------------------',
        'Sources & References',
        '----------------------------------------------------------------',
        '',
        'Buildings - ResStock & ComStock:',
        '  ResStock TMY3 release: https://resstock.nrel.gov/dataviewer/',
        '    NREL ResStock End-Use Load Profiles (TMY3 version, residential).',
        f'    Local data path: {sources.get("resstock_dir", "")}',
        '  ComStock TMY release 1: https://comstock.nrel.gov/',
        '    NREL ComStock End-Use Load Profiles (TMY release 1, commercial).',
        f'    Local data path: {sources.get("comstock_dir", "")}',
        '',
        'Generation - Cambium 2022 Mid-case:',
        '  Cambium 2022 documentation: https://www.nrel.gov/analysis/cambium.html',
        '  Cambium Scenario Viewer: https://scenarioviewer.nrel.gov/',
        '  Citation: Gagnon, P., Cole, W., Frazier, A., et al. (2022). '
        'Cambium 2022 Scenario Data. National Renewable Energy Laboratory.',
        f'    Hourly file: {sources.get("cambium_hourly_csv", "")}',
        f'    Annual file: {sources.get("cambium_annual_csv", "")}',
        '',
        'Demand sectors - EFS:',
        '  NREL Electrification Futures Study (EFS): '
        'https://www.nrel.gov/analysis/electrification-futures.html',
        f'    Local data path: {sources.get("efs_zip", "")}',
        '',
        'External cross-check sources:',
        '  EIA State Energy Data System (SEDS): https://www.eia.gov/state/seds/',
        '  EIA Form 923: https://www.eia.gov/electricity/data/eia923/',
        '',
        'Methodology references (clustering & validation):',
        '  Poncelet, K., Hoschle, H., Delarue, E., et al. (2017). "Selecting Representative '
        'Days for Capturing the Implications of Integrating Intermittent Renewables in '
        'Generation Expansion Planning Problems." IEEE Trans. Power Systems 32(3).',
        '  Mallapragada, D.S., Papageorgiou, D.J., Venkatesh, A., et al. (2018). "Impact of '
        'model resolution on scenario outcomes for electricity sector system expansion." Energy 163.',
        '  NREL ReEDS Documentation (representative days methodology): '
        'https://www.nrel.gov/analysis/reeds/',
        '',
        '----------------------------------------------------------------',
        'All outputs are inputs for staff review. Verify against EIA SEDS / EIA-923 / '
        'Cambium Scenario Viewer before any work product use.',
    ]
    return lines


def _about_lines_syshecf(state_label: str, sources: dict,
                         curtailment_addback: dict | None) -> list[str]:
    run_date = datetime.now().strftime('%Y-%m-%d %H:%M')
    cb = curtailment_addback or {}
    lines: list[str] = [
        f'State-level SYSHECF Pipeline Output - {state_label}',
        '',
        f'Pipeline: {PIPELINE_VERSION}',
        f'Run date: {run_date}',
        '',
        'Methodology (SYSHECF-focused):',
        '  Variable techs (solar PV, distributed PV, onshore wind, offshore wind, '
        'hydro, etc.) derive hourly capacity factors from Cambium 2022 Mid-case state '
        'hourly generation divided by Cambium annual capacity (anchor year 2024).',
        '  Non-variable techs (lignite, hydrogen, SMR, MSW, steam-turbine, etc.) use '
        'legacy SYSHECF templates where present, falling back to flat constant CF '
        'profiles otherwise.',
        '  6 timeslices: Winter / Spring / Summer / Fall + Summer Peak (top-5 days) '
        '+ Winter Peak (top-5 days). Per-slice CF = mean of hourly CFs across days '
        'in that slice.',
        '',
        'Weather-year basis: Cambium 2022 underlying weather year is 2012, mapped to '
        'the 2018 calendar via a 1-day shift to align day-of-week patterns.',
        '',
        'Curtailment treatment:',
        '  Cambium 2022 state files contain NO explicit curtailment columns; per-tech '
        'generation is reported AFTER curtailment. EPS expects pre-curtailment resource '
        'availability. Optional per-tech, per-state scaling factor is supported via '
        'preset YAML key `curtailment_addback`. Effective CF = cf_observed / (1 - f_t), '
        'clipped to [0, 1].',
        f'  Active addback factors: {cb if cb else "(none)"}',
        '',
        '----------------------------------------------------------------',
        'Sources & References',
        '----------------------------------------------------------------',
        '',
        'Cambium 2022 Mid-case scenario:',
        '  Documentation: https://www.nrel.gov/analysis/cambium.html',
        '  Scenario Viewer: https://scenarioviewer.nrel.gov/',
        '  Citation: Gagnon, P., Cole, W., Frazier, A., et al. (2022). '
        'Cambium 2022 Scenario Data. National Renewable Energy Laboratory.',
        f'    Hourly file: {sources.get("cambium_hourly_csv", "")}',
        f'    Annual file: {sources.get("cambium_annual_csv", "")}',
        '',
        'Capacity validation:',
        '  EIA State Energy Data System (SEDS): https://www.eia.gov/state/seds/',
        '  EIA Form 923 (generation): https://www.eia.gov/electricity/data/eia923/',
        '  EIA Form 860 (capacity): https://www.eia.gov/electricity/data/eia860/',
        '',
        '----------------------------------------------------------------',
        'All outputs are inputs for staff review. Verify against the Cambium Scenario '
        'Viewer and EIA Form 860 before any work product use.',
    ]
    return lines


def _write_about(writer, sheet_name: str, lines: list[str]) -> None:
    """Write a single-column About sheet with rich formatting."""
    wb = writer.book
    ws = wb.add_worksheet(sheet_name[:31])
    writer.sheets[sheet_name[:31]] = ws
    header_fmt = wb.add_format({'bold': True, 'font_size': 14, 'bottom': 2})
    section_fmt = wb.add_format({'bold': True, 'font_size': 11,
                                 'bg_color': '#E8E8E8'})
    bullet_fmt = wb.add_format({'text_wrap': True})
    plain_fmt = wb.add_format({'text_wrap': True})
    ws.set_column(0, 0, 110)
    for i, line in enumerate(lines):
        if i == 0:
            ws.write(i, 0, line, header_fmt)
        elif line.startswith('-----'):
            ws.write(i, 0, '', plain_fmt)
        elif line.endswith(':') and not line.startswith(' '):
            ws.write(i, 0, line, section_fmt)
        else:
            ws.write(i, 0, line, bullet_fmt)
    ws.set_row(0, 24)


def _write_table(writer, sheet_name: str,
                 rows: list[list[Any]],
                 freeze: tuple[int, int] = (1, 0),
                 col_widths: dict[int, int] | None = None) -> None:
    """Write a 2D list (header + data) starting at row 0 col 0."""
    sn = sheet_name[:31]
    wb = writer.book
    if sn in writer.sheets:
        ws = writer.sheets[sn]
    else:
        ws = wb.add_worksheet(sn)
        writer.sheets[sn] = ws
    header_fmt = wb.add_format({'bold': True, 'bg_color': '#D9E1F2', 'bottom': 1})
    for c, h in enumerate(rows[0]):
        ws.write(0, c, _to_py(h), header_fmt)
    for r, row in enumerate(rows[1:], start=1):
        for c, v in enumerate(row):
            ws.write(r, c, _to_py(v))
    if col_widths:
        for col, w in col_widths.items():
            ws.set_column(col, col, w)
    ws.freeze_panes(*freeze)


# =============================================================================
# File 1: Hourly Demand and SHELF
# =============================================================================

def write_demand_shelf_workbook(
    output_path: str | Path,
    *,
    state_label: str,
    sources: dict,
    hourly_demand: pd.DataFrame,                 # 8760 x 22 SHELF cats
    cr: ClusteringResult,
    shelf_tables: dict[str, pd.DataFrame],       # 6x24 per cat
    validation_sections: dict[str, Any],
    industry_shape_mode: str = 'flat',
    curtailment_addback: dict | None = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        # ---- 1) About ----
        _write_about(writer, 'About',
                     _about_lines_demand_shelf(state_label, sources,
                                               industry_shape_mode,
                                               curtailment_addback))

        # ---- 2) Hourly Demand ----
        sd = hourly_demand.copy()
        # Cast to plain floats
        for c in sd.columns:
            sd[c] = sd[c].astype(float)
        sd['total_demand_MWh'] = sd.sum(axis=1)
        sd['day_of_year'] = sd.index.dayofyear.astype(int)
        sd['hour'] = sd.index.hour.astype(int)
        slice_map = cr.slice_assignment.to_dict()
        sd['EPS Timeslice Day'] = sd['day_of_year'].map(slice_map)
        sd_reset = sd.reset_index().rename(columns={'index': 'timestamp_lst',
                                                    sd.index.name or 'index': 'timestamp_lst'})
        # Ensure first column is named timestamp_lst even if rename didn't catch it
        first_col = sd_reset.columns[0]
        if first_col != 'timestamp_lst':
            sd_reset = sd_reset.rename(columns={first_col: 'timestamp_lst'})
        sd_reset.to_excel(writer, sheet_name='Hourly Demand', index=False)
        ws = writer.sheets['Hourly Demand']
        ws.freeze_panes(1, 1)
        ws.set_column(0, 0, 20)

        # ---- 3) Daily Summary ----
        ds_rows: list[list[Any]] = [['day_of_year', 'date', 'slice_assignment',
                                     'peak_slice_membership', 'system_peak_MWh',
                                     'peak_hour', 'day_total_MWh']]
        sp_set = set(cr.sp_top_days)
        wp_set = set(cr.wp_top_days)
        days = sorted(cr.slice_assignment.index.tolist())
        # Pre-compute peak hour per day
        total_by_hour = hourly_demand.sum(axis=1)
        for d in days:
            date = pd.Timestamp('2018-01-01') + pd.Timedelta(days=int(d) - 1)
            slc = cr.slice_assignment[d]
            peak_label = ''
            if int(d) in sp_set:
                peak_label = 'Summer Peak'
            elif int(d) in wp_set:
                peak_label = 'Winter Peak'
            day_mask = (total_by_hour.index.dayofyear == int(d))
            day_slice = total_by_hour[day_mask]
            if len(day_slice) > 0:
                peak_mw = float(day_slice.max())
                peak_hr = int(day_slice.idxmax().hour)
                day_tot = float(day_slice.sum())
            else:
                peak_mw = 0.0
                peak_hr = 0
                day_tot = 0.0
            ds_rows.append([int(d), date.strftime('%Y-%m-%d'), slc, peak_label,
                            round(peak_mw, 2), peak_hr, round(day_tot, 2)])
        _write_table(writer, 'Daily Summary', ds_rows, freeze=(1, 0),
                     col_widths={0: 11, 1: 12, 2: 14, 3: 18, 4: 16, 5: 10, 6: 16})

        # ---- 4) SHELF (consolidated 22 cats x 6 slices) ----
        # Top: small days-per-timeslice block
        wb = writer.book
        ws_shelf = wb.add_worksheet('SHELF')
        writer.sheets['SHELF'] = ws_shelf
        # Days-per-timeslice block at columns 0..1, rows 0..6
        bold = wb.add_format({'bold': True, 'bg_color': '#D9E1F2'})
        ws_shelf.write(0, 0, 'slice', bold)
        ws_shelf.write(0, 1, 'days_per_timeslice', bold)
        for i, sl in enumerate(SLICE_NAMES):
            ws_shelf.write(i + 1, 0, sl)
            ws_shelf.write(i + 1, 1, int(cr.days_per_timeslice.get(sl, 0)))
        # Master SHELF table starts at row 9
        master_header_row = 9
        header_fmt = wb.add_format({'bold': True, 'bg_color': '#D9E1F2', 'bottom': 1})
        master_cols = ['category', 'slice'] + [f'Hour{h}' for h in range(24)]
        for c, h in enumerate(master_cols):
            ws_shelf.write(master_header_row, c, h, header_fmt)
        # Sort by category (in column order), then by slice in SLICE_NAMES order
        r = master_header_row + 1
        for cat in hourly_demand.columns:
            tbl = shelf_tables.get(cat)
            if tbl is None:
                continue
            for sl in SLICE_NAMES:
                ws_shelf.write(r, 0, cat)
                ws_shelf.write(r, 1, sl)
                if sl in tbl.index:
                    vals = tbl.loc[sl].values.astype(float)
                else:
                    vals = np.zeros(24, dtype=float)
                for c, v in enumerate(vals):
                    ws_shelf.write(r, 2 + c, float(v))
                r += 1
        ws_shelf.set_column(0, 0, 28)
        ws_shelf.set_column(1, 1, 14)
        ws_shelf.set_column(2, 25, 11)
        ws_shelf.freeze_panes(master_header_row + 1, 2)

        # ---- 5) Validation ----
        ws_val = wb.add_worksheet('Validation')
        writer.sheets['Validation'] = ws_val
        section_title_fmt = wb.add_format({'bold': True, 'font_size': 12,
                                           'bg_color': '#FCE4D6'})
        header_row_fmt = wb.add_format({'bold': True, 'bg_color': '#D9E1F2',
                                        'bottom': 1})
        ws_val.set_column(0, 0, 36)
        ws_val.set_column(1, 8, 22)

        section_titles = [
            ('section_1_energy_reconstruction',
             'Section 1: Energy Reconstruction (Annual). '
             'Per category: annual input vs reconstructed sum-of-hourly. '
             'Should be ~100% match by construction; flag if not.'),
            ('section_2_hourly_nrmse',
             'Section 2: Hourly NRMSE - Total and Per-Slice (non-peak slices only). '
             'Lower is better.'),
            ('section_3_per_enduse_nrmse',
             'Section 3: Per-end-use NRMSE. Identifies categories that are poorly fit.'),
            ('section_4_peak_preservation',
             'Section 4: Peak Hour Preservation (capacity adequacy critical). '
             'Target ratio 0.95-1.05.'),
            ('section_5_top100_capture',
             'Section 5: Top-100 Hour Capture. Fraction of top-100 actual hours '
             'reconstructed within 10% of original.'),
            ('section_6_net_load_peak',
             'Section 6: Net Load Peak Preservation. Critical for VRE-heavy systems.'),
            ('section_7_ldc_fit',
             'Section 7: Load Duration Curve fit. RMSE on top 1%, top 5%, overall.'),
            ('section_8_shelf_balance',
             'Section 8: SHELF Balance Check. Sum LF*days across non-peak slices '
             'should equal 1.0 +/- tolerance.'),
            ('section_9_weather_alignment',
             'Section 9: Weather-Year Alignment Diagnostics. '
             'Daily summer correlation; net-load peak under +/-7d, +/-14d shifts.'),
            ('section_10_external_crosschecks',
             'Section 10: External Cross-Checks. Pipeline value vs reference '
             '(EIA SEDS, Cambium). Verify against primary sources.'),
        ]

        cur_row = 0
        for key, title in section_titles:
            ws_val.merge_range(cur_row, 0, cur_row, 7, title, section_title_fmt)
            cur_row += 1
            tbl = validation_sections.get(key, [['(no data)']])
            # write header
            for c, h in enumerate(tbl[0]):
                ws_val.write(cur_row, c, _to_py(h), header_row_fmt)
            cur_row += 1
            for row in tbl[1:]:
                for c, v in enumerate(row):
                    ws_val.write(cur_row, c, _to_py(v))
                cur_row += 1
            cur_row += 1  # blank row between sections
        ws_val.freeze_panes(1, 0)

    return output_path


# =============================================================================
# File 2: SYSHECF
# =============================================================================

def write_syshecf_workbook(
    output_path: str | Path,
    *,
    state_label: str,
    sources: dict,
    cambium_cfs: pd.DataFrame,                  # 8760 x N variable techs
    cambium_caps: dict[str, float],
    cr: ClusteringResult,
    syshecf_tables: dict[str, pd.DataFrame],    # 6x24 per tech
    curtailment_addback: dict | None = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        # ---- 1) About ----
        _write_about(writer, 'About',
                     _about_lines_syshecf(state_label, sources, curtailment_addback))

        # ---- 2) Hourly Renewable CFs ----
        # Header row at top with capacity_MW per tech, then 8760 rows of CFs.
        wb = writer.book
        ws = wb.add_worksheet('Hourly Renewable CFs')
        writer.sheets['Hourly Renewable CFs'] = ws
        bold = wb.add_format({'bold': True, 'bg_color': '#D9E1F2', 'bottom': 1})
        cap_fmt = wb.add_format({'italic': True, 'bg_color': '#FFF2CC'})
        techs = list(cambium_cfs.columns)
        # Row 0: column headers
        ws.write(0, 0, 'timestamp_lst', bold)
        for c, t in enumerate(techs):
            ws.write(0, c + 1, t, bold)
        # Row 1: capacity_MW
        ws.write(1, 0, 'capacity_MW', cap_fmt)
        for c, t in enumerate(techs):
            ws.write(1, c + 1, float(cambium_caps.get(t, 0.0)), cap_fmt)
        # Rows 2+: hourly data
        idx = cambium_cfs.index
        cf_arr = cambium_cfs.values.astype(float)
        for i in range(len(idx)):
            ws.write(i + 2, 0, str(idx[i]))
            for c in range(len(techs)):
                ws.write(i + 2, c + 1, float(cf_arr[i, c]))
        ws.freeze_panes(2, 1)
        ws.set_column(0, 0, 22)
        ws.set_column(1, len(techs), 14)

        # ---- 3) SYSHECF (consolidated 26 techs x 6 slices) ----
        ws_sy = wb.add_worksheet('SYSHECF')
        writer.sheets['SYSHECF'] = ws_sy
        header_fmt = wb.add_format({'bold': True, 'bg_color': '#D9E1F2', 'bottom': 1})
        master_cols = ['tech', 'slice'] + [f'Hour{h}' for h in range(24)]
        for c, h in enumerate(master_cols):
            ws_sy.write(0, c, h, header_fmt)
        r = 1
        # Use SYSHECF_DISPLAY_NAME ordering (from categories.py order); preserve dict order
        for tech, tbl in syshecf_tables.items():
            for sl in SLICE_NAMES:
                ws_sy.write(r, 0, tech)
                ws_sy.write(r, 1, sl)
                if sl in tbl.index:
                    vals = tbl.loc[sl].values.astype(float)
                else:
                    vals = np.zeros(24, dtype=float)
                for c, v in enumerate(vals):
                    ws_sy.write(r, 2 + c, float(v))
                r += 1
        ws_sy.set_column(0, 0, 26)
        ws_sy.set_column(1, 1, 14)
        ws_sy.set_column(2, 25, 11)
        ws_sy.freeze_panes(1, 2)

    return output_path


# Backward-compatibility shim for any caller still importing write_workbook.
# Internally just calls the demand+SHELF writer; the SYSHECF file should be
# produced via write_syshecf_workbook directly from run.py.
def write_workbook(*args, **kwargs):
    raise RuntimeError(
        "write_workbook() has been replaced in v1.2 by write_demand_shelf_workbook() "
        "and write_syshecf_workbook(). Update the caller (run.py) accordingly."
    )
