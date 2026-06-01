"""Build 6x24 SYSHECF CF tables for each generation tech.

Variable techs: derive from Cambium hourly CFs (DataFrame: 8760 x N_techs).
  - For each slice, average the CF profile across days in the slice.
  - For peak slices, average across the top-N peak days.

Non-variable techs: read existing legacy SYSHECF CSV and pass through.
  - If legacy template missing, produce a flat constant profile with reasonable CF.
"""
from __future__ import annotations
from pathlib import Path
import csv
import numpy as np
import pandas as pd

from ..categories import SYSHECF_CATEGORIES
from ..paths import resolve_input
from .clustering import ClusteringResult, SLICE_NAMES


# Sane fallback CFs for non-variable techs lacking legacy templates
DEFAULT_CF = {
    'lignite': 0.7,
    'lignite-CCS': 0.7,
    'heavy-or-residual-oil': 0.1,
    'crude-oil': 0.1,
    'hydrogen-CC': 0.5,
    'hydrogen-CT': 0.1,
    'SMR': 0.85,
    'MSW': 0.6,
    'steam-turbine': 0.5,
}


def _build_variable_table(
    cf_series: pd.Series,
    cr: ClusteringResult,
) -> pd.DataFrame:
    out = pd.DataFrame(0.0, index=SLICE_NAMES, columns=[f'Hour{h}' for h in range(24)])
    df = pd.DataFrame({'cf': cf_series.values}, index=cf_series.index)
    df['day'] = df.index.dayofyear
    df['hour'] = df.index.hour
    df['slice'] = df['day'].map(cr.slice_assignment.to_dict())
    for sl in ['Winter', 'Spring', 'Summer', 'Fall']:
        mask = df['slice'] == sl
        if mask.sum() == 0:
            continue
        prof = df[mask].groupby('hour')['cf'].mean().reindex(range(24)).fillna(0).values
        out.loc[sl] = prof
    if cr.sp_top_days:
        sp = df[df['day'].isin(cr.sp_top_days)].groupby('hour')['cf'].mean().reindex(range(24)).fillna(0).values
        out.loc['Summer Peak'] = sp
    if cr.wp_top_days:
        wp = df[df['day'].isin(cr.wp_top_days)].groupby('hour')['cf'].mean().reindex(range(24)).fillna(0).values
        out.loc['Winter Peak'] = wp
    return out


def _read_legacy_template(legacy_dir: Path, tech: str) -> pd.DataFrame | None:
    p = legacy_dir / f'SYSHECF-{tech}.csv'
    if not p.exists():
        return None
    with open(p, newline='') as f:
        rows = list(csv.reader(f))
    if len(rows) < 7:
        return None
    df = pd.DataFrame(0.0, index=SLICE_NAMES, columns=[f'Hour{h}' for h in range(24)])
    label_to_slice = {
        'Winter': 'Winter', 'Spring': 'Spring', 'Summer': 'Summer', 'Fall': 'Fall',
        'Summer Peak': 'Summer Peak', 'Winter Peak': 'Winter Peak'
    }
    for r in rows[1:]:
        if not r:
            continue
        sl = label_to_slice.get(r[0].strip())
        if sl is None:
            continue
        try:
            vals = [float(x) for x in r[1:25]]
        except (ValueError, IndexError):
            continue
        if len(vals) == 24:
            df.loc[sl] = vals
    return df


def _flat_table(cf_value: float) -> pd.DataFrame:
    df = pd.DataFrame(cf_value, index=SLICE_NAMES, columns=[f'Hour{h}' for h in range(24)])
    return df


def _calibrate_to_target_cf(table: pd.DataFrame, days_per_slice: dict[str, int],
                              target_cf: float) -> pd.DataFrame:
    """Scale all (slice, hour) values uniformly so annual capacity-weighted CF = target.
    Preserves hourly shape; clips to [0, 1]."""
    hour_cols = [f'Hour{h}' for h in range(24)]
    annual = 0.0
    for sl in SLICE_NAMES:
        if sl in table.index:
            annual += float(table.loc[sl, hour_cols].sum()) * days_per_slice[sl]
    annual /= 8760.0
    if annual <= 0 or target_cf <= 0:
        return table
    scale = target_cf / annual
    out = table.copy()
    for sl in SLICE_NAMES:
        if sl in out.index:
            out.loc[sl] = out.loc[sl] * scale
    return out.clip(lower=0.0, upper=1.0)


def build_all_syshecf(
    cambium_cfs: pd.DataFrame,
    cr: ClusteringResult,
    legacy_syshecf_dir: str | None = None,
    state_cf_targets: dict[str, float] | None = None,
) -> dict[str, pd.DataFrame]:
    """Return {tech: 6x24 DataFrame}.

    Parameters
    ----------
    cambium_cfs : DataFrame of hourly CFs per tech (from Cambium hourly file).
    cr : ClusteringResult.
    legacy_syshecf_dir : optional dir of legacy SYSHECF templates (for non-variable techs).
    state_cf_targets : optional dict mapping tech name → target annual CF.
        For each tech in this dict, the resulting SYSHECF table is scaled
        so that the annual capacity-weighted CF matches the target.
        Used for state-level EIA calibration (state-specific CFs from EIA
        State Electricity Profiles).
    """
    out: dict[str, pd.DataFrame] = {}
    legacy_dir: Path | None = None
    if legacy_syshecf_dir:
        try:
            legacy_dir = resolve_input(legacy_syshecf_dir)
        except FileNotFoundError:
            legacy_dir = None

    state_cf_targets = state_cf_targets or {}

    for cat in SYSHECF_CATEGORIES:
        tbl: pd.DataFrame | None = None
        if cat.is_variable and cat.name in cambium_cfs.columns:
            cf_series = cambium_cfs[cat.name]
            if cf_series.sum() <= 0:
                # zero capacity in this state -> try legacy template, then fallback
                if legacy_dir is not None:
                    tbl = _read_legacy_template(legacy_dir, cat.name)
                if tbl is None:
                    tbl = _flat_table(0.0)
            else:
                tbl = _build_variable_table(cf_series, cr)
        else:
            if legacy_dir is not None:
                tbl = _read_legacy_template(legacy_dir, cat.name)
            if tbl is None:
                tbl = _flat_table(DEFAULT_CF.get(cat.name, 0.5))

        # Apply state-specific EIA calibration if a target is supplied for this tech
        if cat.name in state_cf_targets and tbl is not None:
            tbl = _calibrate_to_target_cf(tbl, cr.days_per_timeslice,
                                          float(state_cf_targets[cat.name]))

        out[cat.name] = tbl
    return out


# Human-readable first-cell label per tech (matches existing legacy convention).
# Used by csv writer when writing SYSHECF files.
SYSHECF_DISPLAY_NAME = {
    'solar-pv': 'solar pv',
    'solar-pv-dist': 'solar pv dist',
    'solar-thermal': 'solar thermal',
    'onshore-wind': 'onshore wind',
    'offshore-wind': 'offshore wind',
    'hydro': 'hydro',
    'pumped-hydro': 'pumped hydro',
    'nuclear': 'nuclear',
    'combined-cycle': 'natural gas combined cycle',
    'combined-cycle-CCS': 'natural gas combined cycle ccs',
    'natural-gas-peaker': 'natural gas peaker',
    'hard-coal': 'hard coal',
    'hard-coal-CCS': 'hard coal ccs',
    'lignite': 'lignite',
    'lignite-CCS': 'lignite ccs',
    'biomass': 'biomass',
    'biomass-CCS': 'biomass ccs',
    'geothermal': 'geothermal',
    'petroleum': 'petroleum',
    'heavy-or-residual-oil': 'heavy or residual fuel oil',
    'crude-oil': 'crude oil',
    'hydrogen-CC': 'hydrogen combined cycle',
    'hydrogen-CT': 'hydrogen CT',
    'SMR': 'SMR',
    'MSW': 'MSW',
    'steam-turbine': 'natural gas steam turbine',
}
