"""CLI entry: build SHELF + SYSHECF + workbook for one state.

  python -m state_pipeline.run --state US-VA
"""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any

import yaml
import numpy as np
import pandas as pd

from .paths import resolve_input, resolve_output, CWD
from .categories import SHELF_CATEGORIES, SYSHECF_CATEGORIES
from .readers.bceu_reader import read_bceu_annual
from .readers.industry_reader import read_industry_annual
from .readers.transport_calculator import compute_transport_electricity
from .readers.resstock_reader import read_resstock_hourly
from .readers.comstock_reader import read_comstock_hourly
from .readers.efs_reader import read_efs_state, apply_industry_shape_mode
from .fetchers.cambium import fetch_cambium
from .builders.demand_assembler import assemble_hourly_demand
# Use rep-day clustering (matches national methodology per CLAUDE.md §2).
# Legacy slice-mean cluster_days is broken when uncapped (lumps "hot half" into peak slices).
from .builders.clustering_repday import cluster_days_repday as cluster_days
from .builders.clustering import compute_validation_metrics, SLICE_NAMES
from .builders.shelf_builder import build_all_shelf
from .builders.syshecf_builder import build_all_syshecf
from .exports.csv_writer import (
    write_shelf_csv, write_syshecf_csv, write_days_per_timeslice_csv
)
from .exports.excel_writer import (
    write_demand_shelf_workbook, write_syshecf_workbook,
)


def _read_cambium_busbar(hourly_csv: str, common_idx: pd.DatetimeIndex) -> pd.Series:
    """Read busbar_load column from a Cambium hourly state file, day-shifted to 2018."""
    import numpy as np
    p = resolve_input(hourly_csv)
    h = pd.read_csv(p, skiprows=5, low_memory=False, usecols=['busbar_load'])
    h = h.iloc[:8760].reset_index(drop=True)
    vals = np.roll(h['busbar_load'].fillna(0).values.astype(float), 24)
    return pd.Series(vals, index=common_idx, name='cambium_busbar_load')


def _load_preset(state: str) -> dict[str, Any]:
    p = Path(__file__).parent / 'presets' / f'{state}.yml'
    if not p.exists():
        raise FileNotFoundError(p)
    with open(p) as f:
        return yaml.safe_load(f)


def run(state: str) -> None:
    print(f"[run] Loading preset for {state}")
    cfg = _load_preset(state)
    sources = cfg['sources']
    outputs = cfg['outputs']
    year = int(cfg.get('calendar_year', 2018))
    start_year = int(sources.get('cambium_year', 2024))  # use 2024 for annual demand reads
    state_iso2 = cfg['state_iso2']

    # ---- 1) Annual demand inputs ----
    print(f"[run] Reading BCEU annual at year {start_year}")
    bceu_annual = read_bceu_annual(sources['bcue_dir'], start_year)
    print(f"  building total: {sum(bceu_annual.values())/1e3:.1f} GWh")

    print(f"[run] Reading industry annual")
    ind_annual = read_industry_annual(sources['industry_csv'], start_year)
    print(f"  industry total: {ind_annual['industry']/1e3:.1f} GWh")

    print(f"[run] Computing transport electricity")
    tr_annual = compute_transport_electricity(sources['transport_dir'], start_year)
    print(f"  transport total: {sum(tr_annual.values())/1e3:.1f} GWh "
          f"(LDV={tr_annual.get('LDVs',0)/1e3:.1f} HDV={tr_annual.get('HDVs',0)/1e3:.1f})")

    annual_mwh: dict[str, float] = {}
    annual_mwh.update(bceu_annual)
    annual_mwh.update(ind_annual)
    annual_mwh.update(tr_annual)

    # ---- 2) Hourly shapes ----
    print(f"[run] Reading ResStock hourly")
    rs_hr = read_resstock_hourly(sources['resstock_dir'])
    print(f"  ResStock 8760 rows: {len(rs_hr)}")

    print(f"[run] Reading ComStock hourly")
    cs_hr = read_comstock_hourly(sources['comstock_dir'])
    print(f"  ComStock 8760 rows: {len(cs_hr)}")

    print(f"[run] Reading EFS hourly for {state_iso2}")
    efs_hr = read_efs_state(sources['efs_zip'], state_iso2, year)
    print(f"  EFS rows: {len(efs_hr)}")

    # Align indices: build_all expects same DatetimeIndex; force common 2018 hourly idx
    common_idx = pd.date_range('2018-01-01', periods=8760, freq='h')
    rs_hr = rs_hr.reindex(common_idx).fillna(0)
    rs_hr.index.name = 'ts'
    cs_hr = cs_hr.reindex(common_idx).fillna(0)
    cs_hr.index.name = 'ts'
    efs_hr = efs_hr.reindex(common_idx).fillna(0)
    efs_hr.index.name = 'ts'

    # ---- 3) Cambium fetch ----
    print(f"[run] Fetching Cambium hourly+annual")
    curtailment_addback = cfg.get('curtailment_addback', {}) or {}
    if curtailment_addback:
        print(f"  curtailment add-back factors: {curtailment_addback}")
    cambium_cfs, cambium_caps = fetch_cambium(
        sources['cambium_hourly_csv'],
        sources['cambium_annual_csv'],
        state_iso2, int(sources.get('cambium_year', 2024)),
        curtailment_addback=curtailment_addback,
    )
    cambium_cfs = cambium_cfs.reindex(common_idx).fillna(0)
    cambium_cfs.index.name = 'ts'

    # Also fetch UNADJUSTED CFs for diagnostic comparison (curtailment add-back delta)
    cambium_cfs_raw, _ = fetch_cambium(
        sources['cambium_hourly_csv'],
        sources['cambium_annual_csv'],
        state_iso2, int(sources.get('cambium_year', 2024)),
        curtailment_addback={},
    )
    cambium_cfs_raw = cambium_cfs_raw.reindex(common_idx).fillna(0)

    # Cambium busbar_load (for industry residual + weather-year diagnostics)
    cambium_busbar = _read_cambium_busbar(sources['cambium_hourly_csv'], common_idx)

    # ---- 3b) Industry shape mode ----
    industry_shape_mode = str(cfg.get('industry_shape_mode', 'flat'))
    print(f"[run] Industry shape mode: {industry_shape_mode}")
    rs_total = rs_hr.sum(axis=1)
    cs_total = cs_hr.sum(axis=1)
    efs_hr = apply_industry_shape_mode(
        efs_hr,
        mode=industry_shape_mode,
        cambium_busbar_load=cambium_busbar,
        resstock_total=rs_total,
        comstock_total=cs_total,
    )
    efs_hr.index.name = 'ts'

    # ---- 3c) Diagnostics: compare three industry shape options ----
    print(f"[run] Computing industry shape diagnostics (efs vs flat vs cambium_residual)")
    industry_diag = _compute_industry_shape_diagnostics(
        efs_zip=sources['efs_zip'],
        state_iso2=state_iso2,
        year=year,
        rs_total=rs_total, cs_total=cs_total,
        cambium_busbar=cambium_busbar,
        annual_industry_mwh=float(ind_annual.get('industry', 0.0)),
    )
    print(f"  diagnostics: {industry_diag}")

    # ---- 4) Assemble hourly demand ----
    print(f"[run] Assembling hourly demand")
    hourly_demand = assemble_hourly_demand(annual_mwh, rs_hr, cs_hr, efs_hr)
    total_demand = hourly_demand.sum(axis=1)
    print(f"  state total annual: {total_demand.sum()/1e6:.1f} TWh; "
          f"peak: {total_demand.max()/1e3:.1f} GW")

    # ---- 4b) Weather-year alignment diagnostics ----
    print(f"[run] Computing weather-year alignment diagnostics")
    weather_diag = _compute_weather_year_diagnostics(
        total_demand=total_demand,
        rs_total=rs_total, cs_total=cs_total,
        cambium_cfs=cambium_cfs_raw,
        cambium_caps=cambium_caps,
        cambium_busbar=cambium_busbar,
    )
    print(f"  diagnostics: {weather_diag}")

    # ---- 5) Clustering on net load ----
    print(f"[run] Clustering days")
    solar_total_mw = (cambium_cfs.get('solar-pv', pd.Series(0, index=common_idx)).values
                      * cambium_caps.get('solar-pv', 0.0)
                      + cambium_cfs.get('solar-pv-dist', pd.Series(0, index=common_idx)).values
                      * cambium_caps.get('solar-pv-dist', 0.0))
    wind_total_mw = (cambium_cfs.get('onshore-wind', pd.Series(0, index=common_idx)).values
                     * cambium_caps.get('onshore-wind', 0.0)
                     + cambium_cfs.get('offshore-wind', pd.Series(0, index=common_idx)).values
                     * cambium_caps.get('offshore-wind', 0.0))
    solar_gen = pd.Series(solar_total_mw, index=common_idx)
    wind_gen = pd.Series(wind_total_mw, index=common_idx)
    # Rep-day clustering: peak_top_n=1 (single extreme day per season), no cap (365)
    # See CLAUDE.md §2 / DECISIONS.md 2026-05-15
    cr = cluster_days(total_demand, solar_gen, wind_gen,
                      peak_top_n=int(cfg.get('peak_top_n_days', 1)),
                      max_peak_days=int(cfg.get('max_peak_days', 365)))
    print(f"  Summer Peak top days: {cr.sp_top_days}")
    print(f"  Winter Peak top days: {cr.wp_top_days}")
    print(f"  NRMSE: {cr.nrmse:.3f}")
    print(f"  days_per_timeslice: {cr.days_per_timeslice}")

    # ---- 6) Build SHELF + SYSHECF tables ----
    print(f"[run] Building SHELF tables")
    shelf_tables = build_all_shelf(hourly_demand, cr)
    # Populate flat 24/7 datacenters SHELF (LF = 1/8760 per cell, balance = 1.0).
    # Data centers run continuously; this lets BCEU/AEO datacenter annual energy
    # contribute to every hour including peak. See CLAUDE.md §1 / DECISIONS.md 2026-05-15.
    flat_dc = pd.DataFrame(1.0 / 8760.0, index=SLICE_NAMES,
                            columns=[f'Hour{h}' for h in range(24)])
    shelf_tables['datacenters'] = flat_dc

    # Load state-specific EIA capacity-factor targets if a shared lookup exists.
    # File: data/eia_state_cfs.csv (state_iso2, tech, cf_target_2024, capacity_mw_2024)
    # Generated by scripts/fetch_eia_state_cfs.py. See CLAUDE.md §1.
    state_cf_targets: dict[str, float] = {}
    eia_cf_path = (Path(__file__).parent.parent / 'data' / 'eia_state_cfs.csv')
    if eia_cf_path.exists():
        try:
            df_state_cfs = pd.read_csv(eia_cf_path)
            mask = df_state_cfs['state_iso2'].astype(str).str.upper() == str(state_iso2).upper()
            for _, row in df_state_cfs[mask].iterrows():
                state_cf_targets[str(row['tech'])] = float(row['cf_target_2024'])
            print(f"[run] State EIA CF targets loaded for {state_iso2}: {len(state_cf_targets)} techs")
        except Exception as e:
            print(f"[run] WARN: failed to load state EIA CFs from {eia_cf_path}: {e}")
    else:
        print(f"[run] No state EIA CF lookup found at {eia_cf_path} — state SYSHECFs will use Cambium raw CFs")

    print(f"[run] Building SYSHECF tables")
    syshecf_tables = build_all_syshecf(cambium_cfs, cr,
                                       legacy_syshecf_dir=sources.get('legacy_syshecf_dir'),
                                       state_cf_targets=state_cf_targets)

    # ---- 7) Export CSVs ----
    print(f"[run] Writing CSV outputs")
    shelf_dir = resolve_output(outputs['shelf_dir'])
    syshecf_dir = resolve_output(outputs['syshecf_dir'])
    for cat in [c.name for c in SHELF_CATEGORIES]:
        write_shelf_csv(shelf_dir, cat, shelf_tables.get(cat,
                        pd.DataFrame(0.0, index=cr.days_per_timeslice.keys(),
                                     columns=[f'Hour{h}' for h in range(24)])))
    write_days_per_timeslice_csv(shelf_dir, cr.days_per_timeslice)
    for tech in [c.name for c in SYSHECF_CATEGORIES]:
        write_syshecf_csv(syshecf_dir, tech, syshecf_tables.get(tech,
                          pd.DataFrame(0.0, index=cr.days_per_timeslice.keys(),
                                       columns=[f'Hour{h}' for h in range(24)])))

    # ---- 8) Validation suite (literature-standard, 10 sections) ----
    print(f"[run] Computing validation metrics (10 sections)")
    external_refs = cfg.get('external_refs') or {}
    validation_sections = compute_validation_metrics(
        hourly_demand=hourly_demand,
        shelf_tables=shelf_tables,
        cr=cr,
        cambium_caps=cambium_caps,
        cambium_cfs=cambium_cfs,
        annual_mwh=annual_mwh,
        weather_diag=weather_diag,
        external_refs=external_refs,
        state_iso2=state_iso2,
    )

    # Curtailment add-back diagnostic (kept for markdown report)
    curt_diag = _curtailment_diag(cambium_cfs, cambium_cfs_raw,
                                  techs=['solar-pv', 'solar-pv-dist',
                                         'onshore-wind', 'offshore-wind'])

    print(f"[run] Building validation report (markdown)")
    val_dir = resolve_output(outputs.get('validation_dir', 'output/validation/' + state))
    val_md = val_dir / 'validation_report.md'
    _write_validation_md(val_md, state, hourly_demand, total_demand, cr,
                         shelf_tables, validation_sections,
                         industry_shape_mode=industry_shape_mode,
                         industry_diag=industry_diag,
                         weather_diag=weather_diag,
                         curt_diag=curt_diag,
                         curtailment_addback=curtailment_addback)
    print(f"  validation: {val_md}")

    # ---- 9) Excel workbooks (two files) ----
    state_label = cfg.get('display_name', state)
    state_label_short = state_iso2  # short label used in default filenames

    # Resolve File 1 path
    f1_key = outputs.get('excel_workbook_demand_shelf')
    if f1_key:
        f1_path = resolve_output(f1_key)
    else:
        # Default location based on shelf_dir
        f1_dir = resolve_output(outputs['shelf_dir'])
        f1_path = f1_dir / f'{state_label_short} - Hourly Demand and SHELF.xlsx'

    # Resolve File 2 path
    f2_key = outputs.get('excel_workbook_syshecf')
    if f2_key:
        f2_path = resolve_output(f2_key)
    else:
        f2_dir = resolve_output(outputs['syshecf_dir'])
        f2_path = f2_dir / f'{state_label_short} - SYSHECF.xlsx'

    print(f"[run] Writing demand+SHELF workbook")
    write_demand_shelf_workbook(
        f1_path,
        state_label=state_label,
        sources=sources,
        hourly_demand=hourly_demand,
        cr=cr,
        shelf_tables=shelf_tables,
        validation_sections=validation_sections,
        industry_shape_mode=industry_shape_mode,
        curtailment_addback=curtailment_addback,
    )
    print(f"  File 1: {f1_path}")

    print(f"[run] Writing SYSHECF workbook")
    write_syshecf_workbook(
        f2_path,
        state_label=state_label,
        sources=sources,
        cambium_cfs=cambium_cfs,
        cambium_caps=cambium_caps,
        cr=cr,
        syshecf_tables=syshecf_tables,
        curtailment_addback=curtailment_addback,
    )
    print(f"  File 2: {f2_path}")

    print(f"[run] Done.")


def _compute_industry_shape_diagnostics(
    *, efs_zip: str, state_iso2: str, year: int,
    rs_total: pd.Series, cs_total: pd.Series,
    cambium_busbar: pd.Series, annual_industry_mwh: float,
) -> dict[str, Any]:
    """Return per-mode industry hourly stats: peak_MWh, std_MWh, mean_MWh."""
    # Re-read raw EFS to avoid mutation
    raw_efs = read_efs_state(efs_zip, state_iso2, year)
    common_idx = pd.date_range('2018-01-01', periods=8760, freq='h')
    raw_efs = raw_efs.reindex(common_idx).fillna(0.0)
    diags: dict[str, Any] = {}
    for mode in ['efs', 'flat', 'cambium_residual']:
        e = apply_industry_shape_mode(
            raw_efs, mode=mode,
            cambium_busbar_load=cambium_busbar,
            resstock_total=rs_total, comstock_total=cs_total,
        )
        shape = e['industry'].values.astype(float)
        s = float(shape.sum())
        if s <= 0 or annual_industry_mwh <= 0:
            scaled = np.zeros_like(shape)
        else:
            scaled = shape * (annual_industry_mwh / s)
        diags[mode] = {
            'annual_MWh': float(scaled.sum()),
            'peak_MWh': float(scaled.max()),
            'mean_MWh': float(scaled.mean()),
            'std_MWh': float(scaled.std()),
            'min_MWh': float(scaled.min()),
            'peak_to_mean': float(scaled.max() / max(scaled.mean(), 1e-9)),
        }
    return diags


def _compute_weather_year_diagnostics(
    *, total_demand: pd.Series,
    rs_total: pd.Series, cs_total: pd.Series,
    cambium_cfs: pd.DataFrame, cambium_caps: dict[str, float],
    cambium_busbar: pd.Series,
) -> dict[str, Any]:
    """Compute weather-year coupling diagnostics:
      - correlation between daily peak cooling demand and same-day mean solar CF
      - net-load peak under 0-day shift vs +/- 7-day shifts
    """
    rs = rs_total.copy()
    cs = cs_total.copy()
    bldg_total = (rs + cs)
    daily = bldg_total.groupby(bldg_total.index.dayofyear).sum()
    # Peak day from buildings (mostly summer cooling in VA)
    peak_day = int(daily.idxmax())
    # Solar CF
    sp_col = 'solar-pv'
    if sp_col in cambium_cfs.columns:
        solar = cambium_cfs[sp_col]
    else:
        solar = pd.Series(0.0, index=cambium_cfs.index)
    daily_solar = solar.groupby(solar.index.dayofyear).mean()
    # Pearson correlation: daily building demand vs daily solar CF (summer months 6-8)
    summer_mask = (bldg_total.index.month.isin([6, 7, 8]))
    daily_bldg_sum = bldg_total[summer_mask].groupby(bldg_total[summer_mask].index.dayofyear).sum()
    daily_solar_sum = solar[summer_mask].groupby(solar[summer_mask].index.dayofyear).mean()
    common = daily_bldg_sum.index.intersection(daily_solar_sum.index)
    if len(common) > 5:
        corr = float(daily_bldg_sum.loc[common].corr(daily_solar_sum.loc[common]))
    else:
        corr = float('nan')

    # Net load peak under day shifts: shift Cambium solar+wind generation
    solar_pv = (cambium_cfs.get('solar-pv', pd.Series(0.0, index=cambium_cfs.index)).values
                * cambium_caps.get('solar-pv', 0.0))
    solar_d = (cambium_cfs.get('solar-pv-dist', pd.Series(0.0, index=cambium_cfs.index)).values
               * cambium_caps.get('solar-pv-dist', 0.0))
    wind_on = (cambium_cfs.get('onshore-wind', pd.Series(0.0, index=cambium_cfs.index)).values
               * cambium_caps.get('onshore-wind', 0.0))
    wind_off = (cambium_cfs.get('offshore-wind', pd.Series(0.0, index=cambium_cfs.index)).values
                * cambium_caps.get('offshore-wind', 0.0))
    re_gen = solar_pv + solar_d + wind_on + wind_off
    demand_arr = total_demand.reindex(cambium_cfs.index).fillna(0).values.astype(float)
    shifts = {}
    for s in [-14, -7, 0, 7, 14]:
        re_shift = np.roll(re_gen, s * 24)
        nl = demand_arr - re_shift
        shifts[s] = {
            'peak_MWh': float(nl.max()),
            'mean_MWh': float(nl.mean()),
            'peak_hour': str(cambium_cfs.index[int(nl.argmax())]),
        }
    return {
        'summer_daily_corr_buildings_vs_solar_cf': corr,
        'peak_day_buildings_doy': peak_day,
        'net_load_under_day_shifts': shifts,
    }


def _build_validation(
    hourly_demand: pd.DataFrame,
    shelf_tables: dict[str, pd.DataFrame],
    syshecf_tables: dict[str, pd.DataFrame],
    cr,
    cambium_caps: dict[str, float],
    annual_mwh: dict[str, float],
    legacy_syshecf_dir: str | None,
) -> list[list[Any]]:
    """Return rows: first row is header, rest are data rows."""
    rows = [['check', 'category', 'value', 'note']]

    # Annual energy by category
    for col in hourly_demand.columns:
        annual_gwh = hourly_demand[col].sum() / 1000.0
        rows.append(['annual_GWh', col, round(float(annual_gwh), 2), ''])

    # SHELF balance check
    days = cr.days_per_timeslice
    for cat, tbl in shelf_tables.items():
        s = 0.0
        for sl in ['Winter', 'Spring', 'Summer', 'Fall']:
            s += float(tbl.loc[sl].sum()) * float(days.get(sl, 0))
        rows.append(['shelf_balance', cat, round(s, 4),
                     'expected ~1.0 (sum LF*days across non-peak slices)'])

    # NRMSE
    rows.append(['cluster_nrmse', '_all', round(cr.nrmse, 4), 'lower is better'])

    # Coverage
    rows.append(['coverage_shelf', '_all', len(shelf_tables),
                 f'expected 22 (have {len(shelf_tables)})'])
    rows.append(['coverage_syshecf', '_all', len(syshecf_tables),
                 f'expected 26 (have {len(syshecf_tables)})'])

    # Cambium capacities
    for tech, cap in sorted(cambium_caps.items()):
        rows.append(['cambium_capacity_MW', tech, round(float(cap), 1), ''])

    return rows


def _curtailment_diag(
    cfs_with: pd.DataFrame, cfs_raw: pd.DataFrame, techs: list[str],
) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for t in techs:
        if t not in cfs_with.columns:
            continue
        a = cfs_with[t]
        b = cfs_raw[t]
        # Summer peak hours: Jun-Aug, hours 12-17
        sp_mask = (a.index.month.isin([6, 7, 8])) & (a.index.hour.isin([12, 13, 14, 15, 16, 17]))
        out[t] = {
            'annual_CF_raw': float(b.mean()),
            'annual_CF_addback': float(a.mean()),
            'summer_peak_CF_raw': float(b[sp_mask].mean()),
            'summer_peak_CF_addback': float(a[sp_mask].mean()),
        }
    return out


def _write_validation_md(
    path: Path,
    state: str,
    hourly_demand: pd.DataFrame,
    total_demand: pd.Series,
    cr,
    shelf_tables: dict[str, pd.DataFrame],
    validation_sections: dict[str, Any],
    *,
    industry_shape_mode: str = 'flat',
    industry_diag: dict[str, Any] | None = None,
    weather_diag: dict[str, Any] | None = None,
    curt_diag: dict[str, dict[str, float]] | None = None,
    curtailment_addback: dict[str, float] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    days = cr.days_per_timeslice

    annual_gwh = total_demand.sum() / 1000.0
    peak_mw = total_demand.max()
    peak_hour = total_demand.idxmax()

    section_titles = [
        ('section_1_energy_reconstruction',
         'Section 1: Energy Reconstruction (Annual)',
         'Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.'),
        ('section_2_hourly_nrmse',
         'Section 2: Hourly NRMSE - Total and Per-Slice',
         'Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.'),
        ('section_3_per_enduse_nrmse',
         'Section 3: Per-end-use NRMSE',
         'Identifies categories that are poorly fit.'),
        ('section_4_peak_preservation',
         'Section 4: Peak Hour Preservation',
         'Capacity adequacy critical. Target ratio 0.95-1.05.'),
        ('section_5_top100_capture',
         'Section 5: Top-100 Hour Capture',
         'Fraction of top-100 actual hours where reconstructed >= 90% of actual.'),
        ('section_6_net_load_peak',
         'Section 6: Net Load Peak Preservation',
         'Critical for VRE-heavy systems where investment depends on net load.'),
        ('section_7_ldc_fit',
         'Section 7: Load Duration Curve Fit',
         'RMSE on top 1% (87 hours), top 5% (438 hours), and overall.'),
        ('section_8_shelf_balance',
         'Section 8: SHELF Balance Check',
         'Sum LF*days across non-peak slices = 1.0 +/- tolerance.'),
        ('section_9_weather_alignment',
         'Section 9: Weather-Year Alignment Diagnostics',
         'Daily summer correlation; net-load peak under +/-7d, +/-14d shifts.'),
        ('section_10_external_crosschecks',
         'Section 10: External Cross-Checks',
         'Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.'),
    ]

    with open(path, 'w', newline='', encoding='utf-8') as f:
        f.write(f"# Validation report - {state}\n\n")
        f.write(f"**Generated:** state_pipeline v1.2 "
                f"(consolidated workbooks + literature-standard validation suite)\n\n")
        f.write(f"## Headlines\n\n")
        f.write(f"- Total annual demand: **{annual_gwh/1000:.1f} TWh**\n")
        f.write(f"- Peak hour: **{peak_hour}** at **{peak_mw/1000:.1f} GW**\n")
        f.write(f"- Cluster NRMSE: **{cr.nrmse:.3f}**\n\n")
        f.write(f"## Days per timeslice\n\n")
        for k, v in days.items():
            f.write(f"- {k}: {v}\n")
        f.write(f"\n## Top-5 peak days\n\n")
        f.write(f"- Summer Peak: {cr.sp_top_days}\n")
        f.write(f"- Winter Peak: {cr.wp_top_days}\n\n")

        # Render each of the 10 sections
        for key, title, desc in section_titles:
            f.write(f"## {title}\n\n")
            f.write(f"{desc}\n\n")
            tbl = validation_sections.get(key)
            if not tbl:
                f.write("(no data)\n\n")
                continue
            header = tbl[0]
            f.write('| ' + ' | '.join(str(h) for h in header) + ' |\n')
            f.write('|' + '|'.join(['---'] * len(header)) + '|\n')
            for row in tbl[1:]:
                f.write('| ' + ' | '.join(str(v) for v in row) + ' |\n')
            f.write('\n')
        # ---- Cambium curtailment add-back (v1.1) ----
        f.write(f"\n## Cambium curtailment add-back\n\n")
        f.write(f"**Finding:** Cambium 2022 state-level files (hourly + annual) contain "
                f"NO explicit curtailment columns. Per-tech generation is reported "
                f"after curtailment.\n\n")
        f.write(f"**v1.1 implementation:** optional per-state, per-tech CF scaling factor "
                f"in preset YAML key `curtailment_addback`. Effective CF = "
                f"`cf_observed / (1 - f_t)`, clipped to [0,1].\n\n")
        if curtailment_addback:
            f.write(f"**Active addback factors:** {curtailment_addback}\n\n")
        else:
            f.write(f"**Active addback factors:** (empty / no scaling) — "
                    f"VA has low VRE share; impact is negligible. "
                    f"For high-VRE states (CA, TX, etc.) operators should set non-zero values.\n\n")
        if curt_diag:
            f.write(f"**Per-tech CF before/after (informational):**\n\n")
            f.write("| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |\n")
            f.write("|---|---|---|---|---|\n")
            for t, d in curt_diag.items():
                f.write(f"| {t} | {d['annual_CF_raw']:.4f} | {d['annual_CF_addback']:.4f} | "
                        f"{d['summer_peak_CF_raw']:.4f} | {d['summer_peak_CF_addback']:.4f} |\n")
            f.write("\n")

        # ---- Weather year alignment ----
        f.write(f"## Weather year alignment\n\n")
        f.write(f"**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). "
                f"Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. "
                f"Pipeline runs them on a common 2018 calendar, but the underlying weather "
                f"realizations differ. For clustering on net load, the per-hour correlation "
                f"between demand and renewable generation is therefore artificial.\n\n")
        if weather_diag:
            wd = weather_diag
            f.write(f"**Diagnostic - summer daily correlation (buildings demand vs solar CF):** "
                    f"{wd.get('summer_daily_corr_buildings_vs_solar_cf', float('nan')):.3f}\n\n")
            f.write(f"On hot summer days both should be high (sunny, hot). Weak/negative "
                    f"correlation flags weather-year decoupling.\n\n")
            f.write(f"**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**\n\n")
            f.write("| shift_days | peak_MWh | peak_hour | mean_MWh |\n|---|---|---|---|\n")
            for s, sd in sorted(wd.get('net_load_under_day_shifts', {}).items()):
                f.write(f"| {s} | {sd['peak_MWh']:.0f} | {sd.get('peak_hour','')} | {sd['mean_MWh']:.0f} |\n")
            f.write(f"\nLowest peak indicates best alignment. Pipeline retains shift=0 for v1; "
                    f"this table is informational. Fundamental fix (NSRDB TMY3 / ReEDS multi-year-mean) "
                    f"is deferred to v2 per the plan.\n\n")

        # ---- Industry shape mode ----
        f.write(f"## Industry shape mode\n\n")
        f.write(f"**Active mode:** `{industry_shape_mode}` "
                f"(set in preset YAML via `industry_shape_mode`).\n\n")
        f.write(f"**Options:**\n")
        f.write(f"- `efs`: original EFS Industrial subsector hourly shape (weather-driven regression).\n")
        f.write(f"- `flat`: constant per hour. Simplest, most defensible for bulk industry "
                f"(~24/7 manufacturing/mining).\n")
        f.write(f"- `cambium_residual`: industry shape = busbar_load - resstock - comstock; "
                f"falls back to flat if residual produces > 5% negative hours.\n\n")
        if industry_diag:
            f.write(f"**Comparison (industry annual = same; hourly stats differ):**\n\n")
            f.write("| mode | annual_GWh | peak_MWh | mean_MWh | std_MWh | peak_to_mean |\n|---|---|---|---|---|---|\n")
            for mode, d in industry_diag.items():
                f.write(f"| {mode} | {d['annual_MWh']/1000.0:.1f} | {d['peak_MWh']:.0f} | "
                        f"{d['mean_MWh']:.0f} | {d['std_MWh']:.0f} | {d['peak_to_mean']:.2f} |\n")
            f.write("\nDefault is `flat`: lowest peak, lowest std, no spurious weather-driven variation.\n\n")

        f.write(f"## Notes & caveats\n\n")
        f.write(f"- Weather year mismatch: see Weather year alignment section above.\n")
        f.write(f"- Datacenters annual = 0 (no per-state DC source integrated v1).\n")
        f.write(f"- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).\n")
        f.write(f"- SYSHECF non-variable techs use legacy template values where present;\n")
        f.write(f"  fallback to flat default CFs otherwise.\n")
        f.write(f"- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923\n")
        f.write(f"  before any work product use.\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--state', required=True, help='e.g., US-VA')
    args = p.parse_args()
    run(args.state)


if __name__ == '__main__':
    main()
