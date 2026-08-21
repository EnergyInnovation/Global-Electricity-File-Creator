"""
energy_timeslice_pipeline.py
===========================

This module implements a flexible data pipeline for computing time‑slice
capacity factors and load factors for energy system models.  It is designed
to support models that use a limited number of representative time periods
(so‑called *timeslices*) to capture the variability of electricity demand
and renewable generation across the year.  The pipeline automates the
following steps:

1. **Net load calculation** – combine hourly demand data with variable
   renewable generation profiles (e.g. solar and wind) to compute the net
   load that must be met by dispatchable resources.  Net load is defined
   as the forecasted load minus the expected generation from variable
   renewable resources【202852532351279†L50-L103】.

2. **Clustering hours into timeslices using k‑means** – apply a k‑means
   clustering algorithm to the net load series to identify a user‑specified
   number of timeslices (e.g. six).  Hours with similar net load levels are
   grouped together; the resulting cluster labels can be ordered by the
   cluster centroids to distinguish low, medium and high net load periods.
   The use of k‑means for selecting representative days or periods in energy
   models is motivated by research showing that such clustering can capture
   the distribution and temporal correlation of load and renewable profiles
   better than manually defined seasons and periods【787555183402410†L900-L921】.

3. **Capacity factor aggregation** – for each variable renewable technology
   (e.g. solar PV, wind), compute an average capacity factor within each
   timeslice by averaging the hourly capacity factors across all hours
   assigned to that timeslice.  This follows the approach described in
   Mallapragada et al. (2020) where, once time slices are determined,
   renewable energy (RE) capacity factors in each slice are computed as
   the average capacity factor over all hours in that slice【787555183402410†L900-L904】.

4. **Load factor calculation** – for each end‑use sector or customer class,
   calculate the average load and peak load within each timeslice and
   compute the load factor.  In electrical engineering, the load factor is
   defined as the ratio of the average load to the peak (maximum) load over
   a period【707536377475410†L119-L124】; high load factors indicate that
   resources are used more consistently.  These load factors can be
   combined with sectoral demand shares to produce the hourly load factors
   required in timeslice‑based models.

5. **Export to model input sheets** – write the aggregated capacity
   factors and load factors to Excel files that mirror the structure of
   SYSHECF and SHELF input tables.  This makes it easy to integrate
   country‑specific results into existing energy system models.

The functions below are intentionally modular to allow users to plug in
their own data sources.  To use the pipeline you must provide a
``pandas.DataFrame`` of hourly data with at least the following columns:

* ``timestamp`` – a datetime column identifying the hour.
* ``load`` – total electricity demand for the country or region.
* ``<tech>_cf`` – one column per variable renewable technology giving
  the hourly capacity factor (0–1) of that technology.
* ``<sector>_<enduse>`` – one column per sector and end‑use combination
  representing the hourly electricity demand for that end‑use (e.g.
  residential_space_heating, industry_machinery, etc.).

The example at the bottom of the file demonstrates how to call the
functions and produce Excel files for a specific country.  Additional
instructions and assumptions are provided in the docstrings.

Note: This pipeline uses scikit‑learn for clustering.  If scikit‑learn
is not installed, you can install it via ``pip install scikit‑learn`` in
your environment.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Iterable, List, Tuple, Dict, Optional, Any

import calendar
import datetime as _datetime
import os
import requests
from requests.exceptions import HTTPError
import json
import importlib
import subprocess
import sys
import tempfile
import time
import zipfile
import shutil
import io
import yaml

MENDELEY_DATASET_URL = 'https://data.mendeley.com/public-api/zip/pmd2dchk44/download/1'
EFS_DATASET_URL = 'https://data.nlr.gov/system/files/126/EFSLoadProfile_Reference_Moderate.zip'
DEMANDCAST_REPO_URL = 'https://github.com/open-energy-transition/demandcast.git'
DEMANDCAST_LOCAL_DIR = os.path.join(os.getcwd(), '.vendor', 'demandcast')
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), 'output')
DEFAULT_DATA_DIR = os.path.join(os.getcwd(), 'data')
MENDELEY_REQUIRED_FILES = (
    'Residential_cooling_weekday.csv',
    'Residential_heating_weekday.csv',
    'Service_cooling_weekday.csv',
    'Industry_total_weekday_SSP2.csv',
    'Transport_total_weekday.csv',
)
EFS_REQUIRED_FILE = 'EFSLoadProfile_Reference_Moderate.csv'
EFS_AVAILABLE_YEARS = (2018, 2020, 2024, 2030, 2040, 2050)
EIA_SOURCE_YAML = os.path.join(
    DEMANDCAST_LOCAL_DIR,
    'demandcast',
    'retrievals',
    'electricity_demand_data_sources',
    'eia.yaml',
)
GLOBAL_METRICS_SUMMARY_CSV = os.path.join(DEFAULT_OUTPUT_DIR, 'timeslice_run_metrics_summary.csv')
DEFAULT_EPS_TEMPLATE_ROOT = os.path.join(
    os.path.dirname(os.getcwd()),
    'EPS Structure Testing',
    'InputData',
    'elec',
)
DEFAULT_EPS_SHELF_WORKBOOK_PATH = os.path.join(
    DEFAULT_EPS_TEMPLATE_ROOT,
    'SHELF',
    'Seasonal Hourly Equipment Load Factors by End Use.xlsx',
)
EPS_TIMESLICE_ORDER = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
EPS_HOUR_COLUMNS = [f'Hour{i}' for i in range(24)]
DISTRIBUTED_SOLAR_CF_DERATE = 0.70
EPS_SHELF_FILE_MAP: Dict[str, Any] = {
    'SHELF-days-per-timeslice': None,
    'SHELF-residential-heating': {'mode': 'direct', 'column': 'residential_heating_load_factor'},
    'SHELF-residential-cooling': {'mode': 'direct', 'column': 'residential_cooling_load_factor'},
    'SHELF-residential-envelope': {'mode': 'zeros'},
    'SHELF-residential-lighting': {'mode': 'direct', 'column': 'residential_lighting_load_factor'},
    'SHELF-residential-appliances': {
        'mode': 'first_available',
        'options': [
            {'mode': 'direct', 'column': 'residential_appliances_load_factor'},
            {
                'mode': 'template_split',
                'aggregate_columns': ['residential_waterheating_load_factor', 'residential_other_load_factor'],
                'peer_files': ['SHELF-residential-appliances', 'SHELF-residential-other'],
            },
        ],
    },
    'SHELF-residential-other': {
        'mode': 'first_available',
        'options': [
            {'mode': 'direct', 'column': 'residential_other_load_factor'},
            {
                'mode': 'template_split',
                'aggregate_columns': ['residential_waterheating_load_factor', 'residential_other_load_factor'],
                'peer_files': ['SHELF-residential-appliances', 'SHELF-residential-other'],
            },
        ],
    },
    'SHELF-commercial-heating': {'mode': 'direct', 'column': 'service_heating_load_factor'},
    'SHELF-commercial-cooling': {'mode': 'direct', 'column': 'service_cooling_load_factor'},
    'SHELF-commercial-envelope': {'mode': 'zeros'},
    'SHELF-commercial-lighting': {
        'mode': 'template_split',
        'aggregate_columns': ['service_waterheating_load_factor', 'service_other_load_factor'],
        'peer_files': ['SHELF-commercial-lighting', 'SHELF-commercial-appliances', 'SHELF-commercial-other'],
    },
    'SHELF-commercial-appliances': {
        'mode': 'template_split',
        'aggregate_columns': ['service_waterheating_load_factor', 'service_other_load_factor'],
        'peer_files': ['SHELF-commercial-lighting', 'SHELF-commercial-appliances', 'SHELF-commercial-other'],
    },
    'SHELF-commercial-other': {
        'mode': 'template_split',
        'aggregate_columns': ['service_waterheating_load_factor', 'service_other_load_factor'],
        'peer_files': ['SHELF-commercial-lighting', 'SHELF-commercial-appliances', 'SHELF-commercial-other'],
    },
    'SHELF-LDVs': {
        'mode': 'first_available',
        'options': [
            {'mode': 'direct', 'column': 'transport_ldv_load_factor'},
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_total_load_factor'],
                'peer_files': ['SHELF-LDVs', 'SHELF-HDVs', 'SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
        ],
    },
    'SHELF-HDVs': {
        'mode': 'first_available',
        'options': [
            {'mode': 'sum', 'columns': ['transport_hdv_load_factor', 'transport_mdv_load_factor']},
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_total_load_factor'],
                'peer_files': ['SHELF-LDVs', 'SHELF-HDVs', 'SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
        ],
    },
    'SHELF-aircraft': {
        'mode': 'first_available',
        'options': [
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_other_load_factor'],
                'peer_files': ['SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_total_load_factor'],
                'peer_files': ['SHELF-LDVs', 'SHELF-HDVs', 'SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
        ],
    },
    'SHELF-rail': {
        'mode': 'first_available',
        'options': [
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_other_load_factor'],
                'peer_files': ['SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_total_load_factor'],
                'peer_files': ['SHELF-LDVs', 'SHELF-HDVs', 'SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
        ],
    },
    'SHELF-ships': {
        'mode': 'first_available',
        'options': [
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_other_load_factor'],
                'peer_files': ['SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_total_load_factor'],
                'peer_files': ['SHELF-LDVs', 'SHELF-HDVs', 'SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
        ],
    },
    'SHELF-motorbikes': {
        'mode': 'first_available',
        'options': [
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_other_load_factor'],
                'peer_files': ['SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
            {
                'mode': 'template_split',
                'aggregate_columns': ['transport_total_load_factor'],
                'peer_files': ['SHELF-LDVs', 'SHELF-HDVs', 'SHELF-aircraft', 'SHELF-rail', 'SHELF-ships', 'SHELF-motorbikes'],
            },
        ],
    },
    'SHELF-industry': {'mode': 'direct', 'column': 'industry_total_load_factor'},
    'SHELF-district-heat-hydrogen': {'mode': 'direct', 'column': 'industry_total_load_factor'},
    'SHELF-geoeng': {'mode': 'direct', 'column': 'industry_total_load_factor'},
    'SHELF-datacenters': {'mode': 'uniform_annual_share'},
}
EPS_SYSHECF_FILE_MAP: Dict[str, Any] = {
    'SYSHECF-hard-coal': None,
    'SYSHECF-steam-turbine': None,
    'SYSHECF-combined-cycle': None,
    'SYSHECF-nuclear': None,
    'SYSHECF-hydro': None,
    # Onshore and offshore wind take their own site-type-specific CF series when
    # the wind source is the Renewables.ninja per-site simulation output
    # (wind_cf_source='ninja_sites'), which classifies every site onshore vs
    # offshore. Presets on the legacy 2 m-weather path have no site split and
    # fall back to the single blended wind_cf for both techs.
    'SYSHECF-onshore-wind': {
        'mode': 'first_available',
        'options': [
            {'mode': 'direct', 'column': 'wind_onshore_cf'},
            {'mode': 'direct', 'column': 'wind_cf'},
        ],
    },
    'SYSHECF-solar-pv': {'mode': 'direct', 'column': 'solar_cf'},
    'SYSHECF-solar-thermal': None,
    'SYSHECF-biomass': None,
    'SYSHECF-geothermal': None,
    'SYSHECF-petroleum': None,
    'SYSHECF-natural-gas-peaker': None,
    'SYSHECF-offshore-wind': {
        'mode': 'first_available',
        'options': [
            {'mode': 'direct', 'column': 'wind_offshore_cf'},
            {'mode': 'direct', 'column': 'wind_cf'},
        ],
    },
    'SYSHECF-lignite': None,
    'SYSHECF-MSW': None,
    'SYSHECF-crude-oil': None,
    'SYSHECF-heavy-or-residual-oil': None,
    'SYSHECF-hard-coal-CCS': None,
    'SYSHECF-combined-cycle-CCS': None,
    'SYSHECF-biomass-CCS': None,
    'SYSHECF-lignite-CCS': None,
    'SYSHECF-SMR': None,
    'SYSHECF-hydrogen-CT': None,
    'SYSHECF-hydrogen-CC': None,
    'SYSHECF-solar-pv-dist': {'mode': 'direct', 'column': 'solar_cf', 'multiplier': DISTRIBUTED_SOLAR_CF_DERATE},
    'SYSHECF-pumped-hydro': None,
}

# ---------------------------------------------------------------------------
# ELCCAfR — ELCC Adjustment for Reliability
# ---------------------------------------------------------------------------
# A per-(tech, slice, hour) capacity-adequacy derate on the same 6x24 grid as
# SHELF and SYSHECF. EPS multiplies it into the RELIABILITY branch only, never
# into dispatch:
#
#   Last Year Hourly Bid Electricity Capacity Factors for Reliability by Plant
#   Type = <bid CF by plant type> * ELCCAfR[Electricity Source]   (EPS.mdl)
#
#   Total Electricity Demand by Hour Plus Reserve Margin After Demand Altering
#   Technologies = ... + <peak-load reduction> * ELCCAfR[demand altering]
#
# Both feed "...in Binding Hour by Plant Type", which sums over
# Binding Peak Hour for Reliability Additions[peak day electricity timeslice!,
# Hour!] — so only the two peak slices can ever bind, which is why the four
# non-peak rows are 1.0.
#
# One file per member of the EPS 'Electricity Source' subscript (24 of them),
# plus the demand-altering-technologies file = 25 CSVs. NOTE: solar-pv-dist and
# pumped-hydro appear in EPS_SYSHECF_FILE_MAP but are NOT in 'Electricity
# Source', so they have no ELCCAfR file. Do not add them.
#
# The value maps each ELCCAfR file to the SYSHECF file whose capacity-factor
# series drives it, so a tech that is pipeline-derived here gets a derived
# derate and a tech whose SYSHECF is a borrowed constant gets 1.0 (its min and
# mean over the slice's days are equal by construction).
EPS_ELCCAfR_FILE_MAP: Dict[str, str] = {
    'ELCCAfR-hard-coal': 'SYSHECF-hard-coal',
    'ELCCAfR-steam-turbine': 'SYSHECF-steam-turbine',
    'ELCCAfR-combined-cycle': 'SYSHECF-combined-cycle',
    'ELCCAfR-nuclear': 'SYSHECF-nuclear',
    'ELCCAfR-hydro': 'SYSHECF-hydro',
    'ELCCAfR-onshore-wind': 'SYSHECF-onshore-wind',
    'ELCCAfR-solar-pv': 'SYSHECF-solar-pv',
    'ELCCAfR-solar-thermal': 'SYSHECF-solar-thermal',
    'ELCCAfR-biomass': 'SYSHECF-biomass',
    'ELCCAfR-geothermal': 'SYSHECF-geothermal',
    'ELCCAfR-petroleum': 'SYSHECF-petroleum',
    'ELCCAfR-natural-gas-peaker': 'SYSHECF-natural-gas-peaker',
    'ELCCAfR-lignite': 'SYSHECF-lignite',
    'ELCCAfR-offshore-wind': 'SYSHECF-offshore-wind',
    'ELCCAfR-crude-oil': 'SYSHECF-crude-oil',
    'ELCCAfR-heavy-or-residual-oil': 'SYSHECF-heavy-or-residual-oil',
    'ELCCAfR-MSW': 'SYSHECF-MSW',
    'ELCCAfR-hard-coal-CCS': 'SYSHECF-hard-coal-CCS',
    'ELCCAfR-combined-cycle-CCS': 'SYSHECF-combined-cycle-CCS',
    'ELCCAfR-biomass-CCS': 'SYSHECF-biomass-CCS',
    'ELCCAfR-lignite-CCS': 'SYSHECF-lignite-CCS',
    'ELCCAfR-SMR': 'SYSHECF-SMR',
    'ELCCAfR-hydrogen-CT': 'SYSHECF-hydrogen-CT',
    'ELCCAfR-hydrogen-CC': 'SYSHECF-hydrogen-CC',
}

# First-cell (A1) label per ELCCAfR CSV, matching the eps-us files exactly.
# Vensim ignores A1 for a 'B2' GET DIRECT CONSTANTS read; this is for humans.
EPS_ELCCAfR_HEADERS: Dict[str, str] = {
    'ELCCAfR-hard-coal': 'hard coal',
    'ELCCAfR-steam-turbine': 'natural gas steam turbine',
    'ELCCAfR-combined-cycle': 'natural gas combined cycle',
    'ELCCAfR-nuclear': 'nuclear',
    'ELCCAfR-hydro': 'hydro',
    'ELCCAfR-onshore-wind': 'onshore wind',
    'ELCCAfR-solar-pv': 'solar pv',
    'ELCCAfR-solar-thermal': 'solar thermal',
    'ELCCAfR-biomass': 'biomass',
    'ELCCAfR-geothermal': 'geothermal',
    'ELCCAfR-petroleum': 'petroleum',
    'ELCCAfR-natural-gas-peaker': 'natural gas peaker',
    'ELCCAfR-lignite': 'lignite',
    'ELCCAfR-offshore-wind': 'offshore wind',
    'ELCCAfR-crude-oil': 'crude oil',
    'ELCCAfR-heavy-or-residual-oil': 'heavy or residual fuel oil',
    'ELCCAfR-MSW': 'municipal solid waste',
    'ELCCAfR-hard-coal-CCS': 'hard coal w CCS',
    'ELCCAfR-combined-cycle-CCS': 'natural gas combined cycle w CCS',
    'ELCCAfR-biomass-CCS': 'biomass w CCS',
    'ELCCAfR-lignite-CCS': 'lignite w CCS',
    'ELCCAfR-SMR': 'small modular reactor',
    'ELCCAfR-hydrogen-CT': 'hydrogen combustion turbine',
    'ELCCAfR-hydrogen-CC': 'hydrogen combined cycle',
}

# Technologies with no CF series of their own that should track another
# technology's derate rather than sit at 1.0. Solar thermal shares the solar
# resource, so its capacity credit varies with the same weather that drives
# solar PV; leaving it at 1.0 would credit CSP as fully firm at the peak hour.
# Applied only when the tech is not independently derived AND its mirror target
# is — so a region that does derive solar thermal keeps its own values.
# Added 2026-08-20 per staff edit to the KR workbook.
EPS_ELCCAfR_MIRRORS: Dict[str, str] = {
    'ELCCAfR-solar-thermal': 'ELCCAfR-solar-pv',
}

ELCCAfR_DEMAND_ALTERING_FILE = 'ELCCAfR-demand-altering-techs'
ELCCAfR_DEMAND_ALTERING_UNIT = 'Unit: dimensionless (ELCC fraction at hour)'
EPS_PEAK_TIMESLICES = ('Summer Peak', 'Winter Peak')
# A cell whose mean CF over the slice's days is below this is treated as "no
# resource at this hour" (e.g. solar overnight) and set to 1.0 rather than to a
# meaningless 0/0 ratio. SYSHECF is ~0 there anyway, so the product is unchanged.
ELCCAfR_DEGENERATE_MEAN = 1e-3
# US value from the eps-us file; a judgment parameter about demand-response
# reliability at peak, NOT derivable from capacity-factor data. Override per
# region with the preset key 'elccafr_demand_altering'.
ELCCAfR_DEMAND_ALTERING_DEFAULT = 0.9
# 'min'  — worst single day in the slice (the documented eps-us methodology).
# 'pNN'  — NNth percentile across the slice's days; sample-size stable, which
#          matters because peak-slice day counts differ a lot by region
#          (eps-us 11/10 vs the South Korea run's 30/39). Override per region
#          with the preset key 'elccafr_statistic'.
ELCCAfR_STATISTIC_DEFAULT = 'min'


def _elccafr_reduce(values: np.ndarray, statistic: str) -> float:
    """Collapse one (slice, hour) cell's per-day CF values to its low statistic."""
    if statistic == 'min':
        return float(np.min(values))
    if statistic.startswith('p'):
        try:
            q = float(statistic[1:])
        except ValueError:
            raise ValueError(f"Unrecognized ELCCAfR statistic '{statistic}'.")
        return float(np.percentile(values, q))
    raise ValueError(
        f"Unrecognized ELCCAfR statistic '{statistic}'. Use 'min' or 'pNN' (e.g. 'p05').")


def build_elccafr_constant_table(value: float = 1.0) -> pd.DataFrame:
    """6x24 table of a single constant — used for techs with no derived CF."""
    return pd.DataFrame(float(value), index=EPS_TIMESLICE_ORDER, columns=EPS_HOUR_COLUMNS)


def build_elccafr_demand_altering_table(
    peak_value: float = ELCCAfR_DEMAND_ALTERING_DEFAULT,
) -> pd.DataFrame:
    """Demand-altering-technologies derate: ``peak_value`` on the two peak
    slices, 1.0 elsewhere (only peak slices bind in the reliability calc)."""
    table = build_elccafr_constant_table(1.0)
    for slice_name in EPS_PEAK_TIMESLICES:
        table.loc[slice_name, :] = float(peak_value)
    return table


def build_elccafr_table(
    values: Iterable[float],
    slice_labels: Iterable[str],
    hours: Iterable[int],
    statistic: str = ELCCAfR_STATISTIC_DEFAULT,
) -> pd.DataFrame:
    """Compute one technology's 6x24 ELCCAfR table from an hourly CF series.

    For each peak slice and hour-of-day, over the days the clustering assigned
    to that slice::

        ELCCAfR = low-statistic CF / mean CF        (clamped to [0, 1])

    The denominator is the *same* slice mean that becomes the SYSHECF cell
    (CLAUDE.md section 6), so for a derived tech::

        SYSHECF x ELCCAfR = the worst-day CF at that hour

    which is the capacity-adequacy quantity EPS wants in the binding peak hour.
    Keeping both statistics over the identical day set is what makes that
    identity hold; computing ELCCAfR over a separately pinned day set would
    break it.

    Non-peak slices are 1.0 — they can never bind (see EPS_ELCCAfR_FILE_MAP).
    Cells whose mean is below ELCCAfR_DEGENERATE_MEAN are 1.0.

    Parameters are three aligned hourly sequences so both callers can use this:
    the pipeline (timeslice ids mapped to EPS labels) and the workbook builder
    (the 'slice' column of workbook_sources/cf_hourly_source.csv).
    """
    frame = pd.DataFrame({
        'value': pd.to_numeric(pd.Series(list(values)), errors='coerce'),
        'slice': pd.Series(list(slice_labels)).astype(str).to_numpy(),
        'hour': pd.to_numeric(pd.Series(list(hours)), errors='coerce').astype('Int64').to_numpy(),
    }).dropna()

    table = build_elccafr_constant_table(1.0)
    for slice_name in EPS_PEAK_TIMESLICES:
        sub = frame[frame['slice'] == slice_name]
        if sub.empty:
            continue
        for hour in range(24):
            cell = sub.loc[sub['hour'] == hour, 'value'].to_numpy(dtype=float)
            if cell.size == 0:
                continue
            mean_cf = float(cell.mean())
            if mean_cf < ELCCAfR_DEGENERATE_MEAN:
                continue  # leave at 1.0
            ratio = _elccafr_reduce(cell, statistic) / mean_cf
            table.loc[slice_name, EPS_HOUR_COLUMNS[hour]] = float(min(max(ratio, 0.0), 1.0))
    return table


def build_all_elccafr_tables(
    hourly_cf_source: pd.DataFrame,
    eps_label_map: pd.Series,
    statistic: str = ELCCAfR_STATISTIC_DEFAULT,
    demand_altering: float = ELCCAfR_DEMAND_ALTERING_DEFAULT,
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, str]]:
    """Build all 25 ELCCAfR tables. Returns ``(tables, notes)`` keyed by file name.

    ``hourly_cf_source`` must be the FULL hourly series (one row per hour of the
    year) with 'timeslice' and 'hour_of_day' columns — NOT the collapsed 6x24
    profile that ``compute_hourly_capacity_profiles`` returns and that SYSHECF is
    built from. ELCCAfR measures spread across the days inside a slice, so a
    frame that has already been averaged over those days would yield a
    meaningless all-1.0 table.
    """
    work = hourly_cf_source.reset_index()
    if 'timeslice' not in work.columns or 'hour_of_day' not in work.columns:
        raise KeyError("Hourly capacity-factor data must include 'timeslice' and 'hour_of_day'.")
    if not work.duplicated(subset=['timeslice', 'hour_of_day']).any():
        raise ValueError(
            'ELCCAfR needs the full hourly series: every (timeslice, hour_of_day) pair in '
            f'the frame passed is unique ({len(work)} rows), so it has already been averaged '
            'over each slice\'s days and carries no spread to measure. Pass the 8760-row '
            'capacity-factor frame, not the output of compute_hourly_capacity_profiles.')
    slice_labels = work['timeslice'].map(eps_label_map.to_dict())

    tables: Dict[str, pd.DataFrame] = {}
    notes: Dict[str, str] = {}
    derived: set = set()
    for file_name, syshecf_file in EPS_ELCCAfR_FILE_MAP.items():
        resolved = resolve_direct_cf_spec(
            EPS_SYSHECF_FILE_MAP.get(syshecf_file), work.columns)
        if resolved is None:
            # SYSHECF is a borrowed/template constant per (slice, hour): its min
            # and mean over the slice's days coincide, so the derate is exactly 1.
            tables[file_name] = build_elccafr_constant_table(1.0)
            notes[file_name] = (
                f'constant 1.0 — {syshecf_file} is not pipeline-derived, so its CF has '
                'no day-to-day variation within a slice')
            continue
        column, multiplier = resolved
        # The multiplier cancels in the ratio, so it is deliberately not applied.
        tables[file_name] = build_elccafr_table(
            work[column], slice_labels, work['hour_of_day'], statistic=statistic)
        notes[file_name] = (
            f'derived from {column} as {statistic}/mean CF across each peak slice\'s days '
            f'(same day set and denominator as {syshecf_file})')
        derived.add(file_name)

    # Mirrors: a tech with no CF series of its own tracks a related tech that has
    # one, instead of the meaningless 1.0 its borrowed SYSHECF would imply.
    for file_name, source_file in EPS_ELCCAfR_MIRRORS.items():
        if file_name in derived or file_name not in tables:
            continue
        if source_file not in derived:
            continue
        tables[file_name] = tables[source_file].copy()
        notes[file_name] = (
            f'mirrors {source_file} — no independent CF series, but it shares that '
            "technology's resource, so its capacity credit varies the same way")

    tables[ELCCAfR_DEMAND_ALTERING_FILE] = build_elccafr_demand_altering_table(demand_altering)
    notes[ELCCAfR_DEMAND_ALTERING_FILE] = (
        f'constant {demand_altering} on peak slices, 1.0 elsewhere — a judgment parameter '
        'on demand-response reliability, not derived from capacity-factor data')
    return tables, notes


COUNTRY_PRESETS: Dict[str, Dict[str, Any]] = {
    'south korea': {
        'aliases': ['korea', 'republic of korea', 'kr', 'kor', 'southkorea'],
        'output_country': 'SouthKorea',
        'country_iso2': 'KR',
        'demand_country_code': 'KOR',
        'mendeley_region_name': 'Korea',
        'ember_country_name': 'South Korea',
        'demand_shape_source': 'mendeley',
        # IANA timezone used to localize hourly weather (UTC) into local time
        # before grouping by hour-of-day for SHELF/SYSHECF. EPS expects local
        # time. Verify against the country's actual operating-hour convention.
        'timezone': 'Asia/Seoul',
        # Seoul-ish; KR is small, single point OK
        'latitude_deg': 37.5,
        # Path B (zapata_ridge_nnls): per-end-use MWh/year prior extracted
        # from EPS-South Korea (eps-southkorea). See data/eps_priors/parse_eps_extract.py.
        'eps_prior_path': 'data/eps_priors/eps_prior_KR.csv',
        # Default demand calibration when the runner leaves
        # CALIBRATION_METHOD = None (runner override still wins).
        'calibration_method': 'zapata_ridge_nnls',
        'default_year': 2025,
        'last_n_years': 4,
        # Wind CF from Renewables.ninja per-site SIMULATION outputs (hub-height,
        # power-curve, bias-corrected), same as China — see DECISIONS.md
        # 2026-07-10. Sites in data/weather/ninja_sim/KR/ (fetch with
        # scripts/fetch_ninja_sites.py --country KR). Averaged across sites over
        # wind_cf_years, calibrated to the Ember annual wind CF. Solar still uses
        # the ninja weather product. Sites are classified onshore (Gangwon ridge,
        # Gyeongbuk coast, Gyeongnam mountains, Jeju) vs offshore (Buan, Sinan,
        # Ulsan) by the fetcher's SITES table, so SYSHECF-onshore-wind and
        # SYSHECF-offshore-wind get separate CF tables. The loader uses whichever
        # site files are on disk, so newly added sites take effect once fetched.
        'wind_cf_source': 'ninja_sites',
        'wind_sites_dir': None,  # None → data/weather/ninja_sim
        'wind_cf_years': 7,      # most-recent 7 available site-years (decoupled from last_n_years)
        # The onshore/offshore weights for the BLENDED wind_cf (net load,
        # clustering, Ember calibration anchor) come from eps-southkorea's
        # start-year capacities via data/eps_wind_capacity_split.csv — no preset
        # key needed. Set 'wind_capacity_split' here only to override that
        # lookup: {'onshore': …, 'offshore': …}.
        #
        # ELCCAfR (capacity-adequacy derate). 'min' reproduces the documented
        # eps-us methodology; note this run's peak slices hold 30 (Summer) and
        # 39 (Winter) days vs eps-us's 11/10, and a straight min takes the worst
        # of however many days there are — see DECISIONS.md 2026-08-17. Set
        # 'elccafr_statistic': 'p05' for a sample-size-stable alternative.
        'elccafr_statistic': 'min',
        'elccafr_demand_altering': 0.9,  # US value; needs a KR demand-response view
        'status': 'verified',
    },
    'china': {
        'aliases': ['cn', 'chn'],
        'output_country': 'China',
        'country_iso2': 'CN',
        'demand_country_code': 'CHN',
        'mendeley_region_name': 'China +',
        'ember_country_name': 'China',
        'demand_shape_source': 'mendeley',
        # China officially uses one timezone nationwide (CST = UTC+8) even
        # though it geographically spans five. 'Asia/Shanghai' is the IANA
        # name for that single national timezone.
        'timezone': 'Asia/Shanghai',
        # population-weighted central China; CN spans ~18–53°N
        'latitude_deg': 32.0,
        # Path B (zapata_ridge_nnls): per-end-use MWh/year prior extracted
        # from EPS-China (eps-china-igdp). See data/eps_priors/parse_eps_extract.py.
        'eps_prior_path': 'data/eps_priors/eps_prior_CN.csv',
        # Default demand calibration when the runner leaves
        # CALIBRATION_METHOD = None (runner override still wins).
        'calibration_method': 'zapata_ridge_nnls',
        'default_year': 2018,
        'last_n_years': 1,
        # ---- Observed-demand source: two sources, selected by run config ----
        # China is the one preset with two usable observed hourly demand
        # records, and they disagree on hourly shape even where they overlap.
        # The rule (see DECISIONS.md 2026-08-13):
        #
        #   year == 2018 AND last_n_years == 1  → DemandCast / Wu et al.
        #       The legacy baseline. Wu et al. covers 2018 only, which is why
        #       the preset defaults pin that year and window. Kept as the
        #       default so the historical China run stays reproducible.
        #
        #   any other year or window            → Yi et al. 2026 (below)
        #       Covers 2015–2024, so it is the only source that can serve a
        #       multi-year calibration window or a post-2018 target year.
        #       Asking for either is taken as asking for this source.
        #
        # Force one explicitly with the runner override DEMAND_SERIES_CSV
        # ('demandcast', or a CSV path) when you need to override the rule.
        'demand_series_csv': 'data/manual_downloads/CN_hourly_demand_2015_2024.csv',
        'demandcast_pin': {'year': 2018, 'last_n_years': 1},
        'demand_series_citation': (
            "Yi, B., Luo, Q., Zhang, S., Ji, Y., Yu, S. & Fan, Y. (2026). "
            "Hourly electricity load curve dataset for Chinese provinces derived "
            "from meteorological variables. Scientific Data 13, 978. "
            "https://doi.org/10.1038/s41597-026-07327-8 — data: figshare "
            "https://doi.org/10.6084/m9.figshare.29832701 (CC BY-NC-ND 4.0)"
        ),
        # Wind CF comes from Renewables.ninja per-site SIMULATION outputs
        # (hub-height, power-curve, bias-corrected) rather than the 2 m weather
        # variable. Site CSVs live in data/weather/ninja_sim/CN/ (fetched by
        # scripts/fetch_ninja_sites.py). They are averaged across sites over the
        # calibration window, then calibrated to the Ember annual wind CF. Solar
        # still uses the ninja weather product. See DECISIONS.md 2026-07-10.
        # Sites are classified onshore (the seven "Three North" base sites) vs
        # offshore (Rudong, Yangjiang, Putian — the *_OSW files) by the fetcher's
        # SITES table, so SYSHECF-onshore-wind and SYSHECF-offshore-wind get
        # separate CF tables.
        'wind_cf_source': 'ninja_sites',
        'wind_sites_dir': None,  # None → data/weather/ninja_sim
        # Wind averages its own multi-year window of the site archive, decoupled
        # from last_n_years (demand). 7 = all of 2018–2024 downloaded for CN.
        # Runner can override via WIND_CF_YEARS in run_pipeline.py.
        'wind_cf_years': 7,
        # The onshore/offshore weights for the BLENDED wind_cf (net load,
        # clustering, Ember calibration anchor) come from eps-china-igdp's
        # start-year capacities via data/eps_wind_capacity_split.csv — no preset
        # key needed. Set 'wind_capacity_split' here only to override that
        # lookup: {'onshore': …, 'offshore': …}.
        'status': 'verified',
    },
    'united states': {
        'aliases': ['us', 'usa', 'unitedstates', 'america', 'united states of america'],
        'output_country': 'UnitedStates',
        'country_iso2': 'US',
        'demand_country_code': 'USA',
        'mendeley_region_name': 'USA',
        'ember_country_name': 'United States of America',
        'demand_shape_source': 'efs',
        'efs_electrification': 'Reference',
        'efs_technology_advancement': 'Moderate',
        # ---- Master-parity pinning (2026-07-07) ----------------------------
        # The US run from this script is pinned to the legacy master-branch
        # behavior so its clustering outputs stay comparable with the
        # historical US baseline (see DECISIONS.md 2026-07-07). Three pins:
        #   * no 'timezone' key — weather stays in UTC, exactly as on master.
        #     CONUS spans four timezones, so any single-tz localization is an
        #     approximation anyway; allow_utc_weather suppresses the loud
        #     no-timezone warning for this deliberate opt-out.
        #   * cf_calibration_mode 'multiplicative' — master's pure scalar
        #     scaling. NOTE: yields wind CF values > 1.0 (implied multiplier
        #     ~29×); retained for baseline continuity only. The canonical US
        #     EPS inputs come from the Cambium-based national pipeline
        #     (rebuild_us_national_v2.py), not from this script.
        #   * calibration_method 'level_seasonal' — the only demand
        #     calibration that existed on master.
        # A runner override (non-None CALIBRATION_METHOD / CF_CALIBRATION_MODE
        # in run_pipeline.py) still takes precedence over these pins.
        'allow_utc_weather': True,
        'cf_calibration_mode': 'multiplicative',
        'calibration_method': 'level_seasonal',
        # CONUS centroid; spans 25–49°N
        'latitude_deg': 38.0,
        # Path B (zapata_ridge_nnls): per-end-use MWh/year prior extracted
        # from EPS-US (eps-us). See data/eps_priors/parse_eps_extract.py.
        'eps_prior_path': 'data/eps_priors/eps_prior_US.csv',
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'verified',
    },
    'canada': {
        'aliases': ['ca', 'can'],
        'output_country': 'Canada',
        'country_iso2': 'CA',
        'demand_country_code': 'CAN',
        'mendeley_region_name': 'Canada',
        'ember_country_name': 'Canada',
        'demand_shape_source': 'mendeley',
        # Most populous TZ (Eastern). Canada spans six timezones; for region-specific runs you'd want to refactor.
        'timezone': 'America/Toronto',
        # population-weighted southern CA; spans 42–82°N
        'latitude_deg': 50.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
    'japan': {
        'aliases': ['jp', 'jpn'],
        'output_country': 'Japan',
        'country_iso2': 'JP',
        'demand_country_code': 'JPN',
        'mendeley_region_name': 'Japan',
        'ember_country_name': 'Japan',
        'demand_shape_source': 'mendeley',
        # Japan is single-timezone (JST = UTC+9).
        'timezone': 'Asia/Tokyo',
        # Honshu centroid
        'latitude_deg': 36.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
    'india': {
        'aliases': ['in', 'ind'],
        'output_country': 'India',
        'country_iso2': 'IN',
        'demand_country_code': 'IND',
        'mendeley_region_name': 'India',
        'ember_country_name': 'India',
        'demand_shape_source': 'mendeley',
        # India is single-timezone (IST = UTC+5:30).
        'timezone': 'Asia/Kolkata',
        # population-weighted central IN
        'latitude_deg': 22.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
    'germany': {
        'aliases': ['de', 'deu'],
        'output_country': 'Germany',
        'country_iso2': 'DE',
        'demand_country_code': 'DEU',
        'mendeley_region_name': 'Germany',
        'ember_country_name': 'Germany',
        'demand_shape_source': 'mendeley',
        # Germany is single-timezone (CET/CEST).
        'timezone': 'Europe/Berlin',
        # DE centroid
        'latitude_deg': 51.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
    'france': {
        'aliases': ['fr', 'fra'],
        'output_country': 'France',
        'country_iso2': 'FR',
        'demand_country_code': 'FRA',
        'mendeley_region_name': 'France',
        'ember_country_name': 'France',
        'demand_shape_source': 'mendeley',
        # Metropolitan France only; overseas territories not modeled.
        'timezone': 'Europe/Paris',
        # mainland FR centroid
        'latitude_deg': 47.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
    'united kingdom': {
        'aliases': ['uk', 'gb', 'gbr', 'britain', 'great britain'],
        'output_country': 'UnitedKingdom',
        'country_iso2': 'GB',
        'demand_country_code': 'GBR',
        'mendeley_region_name': 'United Kingdom',
        'ember_country_name': 'United Kingdom',
        'demand_shape_source': 'mendeley',
        # GMT/BST.
        'timezone': 'Europe/London',
        # UK centroid
        'latitude_deg': 54.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
    'australia': {
        'aliases': ['au', 'aus'],
        'output_country': 'Australia',
        'country_iso2': 'AU',
        'demand_country_code': 'AUS',
        'mendeley_region_name': 'Australia',
        'ember_country_name': 'Australia',
        'demand_shape_source': 'mendeley',
        # Most populous TZ (AEDT/AEST). Australia spans 5+ timezones; for region-specific runs you'd want to refactor.
        'timezone': 'Australia/Sydney',
        # population-weighted south-east coast; AU is southern hemisphere
        'latitude_deg': -33.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
    'brazil': {
        'aliases': ['br', 'bra'],
        'output_country': 'Brazil',
        'country_iso2': 'BR',
        'demand_country_code': 'BRA',
        'mendeley_region_name': 'Brazil',
        'ember_country_name': 'Brazil',
        'demand_shape_source': 'mendeley',
        # Most populous TZ (BRT). Brazil spans four timezones.
        'timezone': 'America/Sao_Paulo',
        # population-weighted south-east BR
        'latitude_deg': -15.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
    'mexico': {
        'aliases': ['mx', 'mex'],
        'output_country': 'Mexico',
        'country_iso2': 'MX',
        'demand_country_code': 'MEX',
        'mendeley_region_name': 'Mexico',
        'ember_country_name': 'Mexico',
        'demand_shape_source': 'mendeley',
        # Most populous TZ. Mexico spans four timezones.
        'timezone': 'America/Mexico_City',
        # MX centroid
        'latitude_deg': 23.0,
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
}

###############################################################################
# Status / progress reporting
#
# Pipeline runs are long. Without inline status, the only sign of life is
# sklearn's KMeans memory-leak warning printed dozens of times during the
# clustering phase. Inline status lines turn that into useful progress.
#
# Format conventions:
#   - Every status line starts with `[stage]` for grep-ability. Stages are
#     'setup', 'demand', 'calibrate-load', 'weather', 'cf', 'gen',
#     'cluster', 'metrics', 'output', 'eps', 'done'.
#   - Slow steps include `[X.Xs]` or `[Xm Ys]` timing in brackets. Pass
#     ``t=time.perf_counter()`` start to ``_status`` to render this.
#   - Pipeline modules call ``_status(...)`` to emit lines; consumers
#     control the volume by calling ``set_verbosity('quiet'|'normal'|'verbose')``.
#
# `quiet`   = no status output (only Python warnings/errors)
# `normal`  = the default — one status line per pipeline milestone
# `verbose` = adds per-iteration kmeans seed details (mostly for debugging)
###############################################################################

_VERBOSITY = 'normal'


def set_verbosity(level: str) -> None:
    """Set pipeline status verbosity. Levels: 'quiet', 'normal', 'verbose'."""
    global _VERBOSITY
    if level not in ('quiet', 'normal', 'verbose'):
        raise ValueError(
            f"Unknown verbosity level {level!r}; expected one of "
            "'quiet', 'normal', 'verbose'."
        )
    _VERBOSITY = level


def _status(stage: str, msg: str, *, t: Optional[float] = None, level: str = 'normal') -> None:
    """Emit a single pipeline status line.

    Parameters
    ----------
    stage : str
        Short tag used as a `[bracket]` prefix (e.g. 'demand', 'cluster').
    msg : str
        The message body. Should fit on one line.
    t : float, optional
        ``time.perf_counter()`` start. If supplied, elapsed time is
        appended in compact form (seconds for short, m+s for long).
    level : str, default 'normal'
        Minimum verbosity level required to print this line. ``'normal'``
        always prints unless quiet; ``'verbose'`` prints only when verbose.
    """
    if _VERBOSITY == 'quiet':
        return
    if level == 'verbose' and _VERBOSITY != 'verbose':
        return
    line = f"[{stage}] {msg}"
    if t is not None:
        elapsed = time.perf_counter() - t
        if elapsed < 60:
            line += f"  [{elapsed:.1f}s]"
        else:
            line += f"  [{int(elapsed // 60)}m {int(elapsed % 60)}s]"
    print(line, flush=True)


# Suppress the repetitive sklearn KMeans MKL memory-leak warning so it
# fires once instead of on every fit. The clustering step runs k-means 9+
# times in a single country run; without this filter the legitimate status
# lines get drowned out. Setting OMP_NUM_THREADS=2 in the environment
# silences the underlying issue, but a filter here is enough for log
# readability.
import warnings as _kmeans_warnings_module
_kmeans_warnings_module.filterwarnings(
    'once',
    message='KMeans is known to have a memory leak',
    category=UserWarning,
)


###############################################################################
# Parquet cache for parsed-and-filtered intermediates
#
# These helpers let the three slow data-loading functions
# (``load_enduse_data_mendeley``, ``load_enduse_data_efs_us``, and
# ``load_weather_data``) skip re-parsing their large source CSVs on every
# run. The cache is opt-in: the loaders accept ``use_cache=False`` by
# default, so existing callers see no behavior change.
#
# Cache files live under ``<data_dir>/cache/`` and are named with the
# parameters that affect the result (region, year, scenario, etc.).
# Staleness is detected by comparing each cached file's mtime to the
# mtimes of all source files that fed it; if any source is newer, the
# cache is rebuilt.
#
# Caches are derived from upstream source CSVs/zips that already live on
# disk. Deleting ``data/cache/`` is always safe — it just forces the
# next run to recompute. Caching does not change the modeled values; it
# only avoids redoing the parse-and-filter work.
###############################################################################

CACHE_DIR_NAME = 'cache'


def _safe_filename_part(value: Any) -> str:
    """Sanitize a value so it can be embedded in a cache file name."""
    s = str(value).strip().lower()
    out = []
    for ch in s:
        if ch.isalnum() or ch in ('-', '.'):
            out.append(ch)
        elif ch in (' ', '/', '\\', ':', '+'):
            out.append('_')
    return ''.join(out) or 'na'


def _resolve_cache_dir(data_dir: Optional[str], cache_dir: Optional[str]) -> str:
    """Pick a cache directory, falling back to ``<data_dir>/cache``."""
    if cache_dir:
        return cache_dir
    base = data_dir or DEFAULT_DATA_DIR
    return os.path.join(base, CACHE_DIR_NAME)


def _cache_is_stale(cache_path: str, source_paths: Iterable[str]) -> bool:
    """
    Return True if the cache must be (re)built.

    Stale conditions:
      * cache file does not exist
      * any required source path does not exist (caller will likely error
        anyway, but we surface that by treating the cache as stale)
      * any source file's mtime is newer than the cache file's mtime
    """
    if not os.path.exists(cache_path):
        return True
    cache_mtime = os.path.getmtime(cache_path)
    for src in source_paths:
        if not os.path.exists(src):
            return True
        if os.path.getmtime(src) > cache_mtime:
            return True
    return False


def _read_or_build_cached_parquet(
    cache_path: str,
    source_paths: Iterable[str],
    build_fn,
) -> pd.DataFrame:
    """
    Return a DataFrame, reading from the parquet cache if fresh, otherwise
    calling ``build_fn()``, persisting its result, and returning it.

    The cache file is written via ``DataFrame.to_parquet`` (pyarrow engine).
    Index dtypes are preserved across the round-trip; tz-aware timestamps
    survive intact, which matters for the weather data.
    """
    sources = list(source_paths)
    if not _cache_is_stale(cache_path, sources):
        try:
            return pd.read_parquet(cache_path)
        except Exception:
            # Corrupt cache file — fall through and rebuild
            pass
    df = build_fn()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    try:
        df.to_parquet(cache_path)
    except Exception:
        # If parquet write fails (e.g. unsupported dtype), don't crash the
        # caller — just skip caching for this run.
        pass
    return df


###############################################################################
# Capacity factor computation from weather data
###############################################################################

def compute_pv_capacity_factor_from_weather(
    weather: pd.DataFrame,
    ghi_col: str = 'ghi',
    temp_col: str = 'temperature',
    tilt: float = 30.0,
    orientation_factor: float = 1.0,
    temp_coeff: float = -0.004,
    reference_temp: float = 25.0,
    ghi_reference: float = 1000.0,
    tcell_coeff: float = 0.025,
) -> pd.Series:
    """
    Estimate photovoltaic (PV) capacity factors from area‑weighted weather data.

    This helper computes an approximate hourly PV capacity factor from
    aggregated weather data.  It follows the high‑level methodology of
    Pfenninger & Staffell (2016) used in Renewables.ninja【861615956447402†L248-L254】:

    1. **Plane‑of‑array irradiance:**  The global horizontal irradiance (GHI) is
       scaled by an ``orientation_factor`` to approximate the irradiance on a
       tilted PV module.  In the full GSEE model, the plane‑of‑array
       irradiance is calculated from direct and diffuse components using the
       incidence angle formula ``a = arccos( sin(h)*cos(t) + cos(h)*sin(t)*cos(ap - as) )``
       for the angle of incidence on a panel of tilt ``t``【861615956447402†L248-L254】.
       When only area‑weighted GHI is available, we approximate the tilt
       correction via a constant ``orientation_factor`` (e.g. 1.1 for south‑facing
       panels in mid‑latitudes).  Users can adjust this parameter for
       different tilt/azimuth combinations.

    2. **Cell temperature:**  PV cell temperature is estimated from the
       ambient air temperature and irradiance.  The GSEE model uses a
       temperature rise of roughly 0.025 °C per W m⁻² of irradiance
       【861615956447402†L280-L294】.  We implement this as ``T_cell = T_air + tcell_coeff * I_poa``,
       where ``tcell_coeff`` defaults to 0.025.

    3. **Temperature‑dependent efficiency:**  Module efficiency decreases
       linearly with cell temperature.  Following typical PV performance
       curves, the relative change in efficiency per degree Celsius is
       represented by ``temp_coeff`` (negative, e.g. −0.004 / °C).  The
       efficiency ratio is ``1 + temp_coeff * (T_cell - reference_temp)``.

    4. **Capacity factor:**  Capacity factor is defined as actual power
       divided by rated power.  For a PV system rated at 1 kWₚ (under
       1000 W m⁻² irradiance), the capacity factor is approximated as

       ``CF = (I_poa / ghi_reference) * (1 + temp_coeff * (T_cell - reference_temp))``

       where ``ghi_reference`` is 1000 W m⁻².  This expression mirrors the
       approach in GSEE, which multiplies the plane‑of‑array irradiance by
       a temperature‑dependent efficiency and divides by the reference
       irradiance【861615956447402†L280-L304】.

    Parameters
    ----------
    weather : pandas.DataFrame
        DataFrame indexed by timestamps with at least two columns: a global
        horizontal irradiance column (``ghi_col``) in W m⁻² and an ambient
        temperature column (``temp_col``) in °C.  The data should be
        aggregated (e.g. area‑weighted) across the region of interest.
    ghi_col : str, default 'ghi'
        Name of the column in ``weather`` containing global horizontal
        irradiance (W m⁻²).
    temp_col : str, default 'temperature'
        Name of the column in ``weather`` containing ambient air temperature
        (°C).
    tilt : float, default 30.0
        Nominal tilt angle of the PV panels (degrees).  This parameter does not
        directly affect the calculation in the simplified model, but is
        included for completeness and potential future extensions.
    orientation_factor : float, default 1.0
        Multiplicative factor applied to the horizontal irradiance to
        approximate the plane‑of‑array irradiance.  Set to >1 for south‑facing
        tilted panels in the northern hemisphere (typical values 1.0–1.2).
    temp_coeff : float, default −0.004
        Temperature coefficient of efficiency (relative change per °C).  A
        value of −0.004 implies a 0.4 % decrease in efficiency per degree
        Celsius above the reference temperature.
    reference_temp : float, default 25.0
        Reference cell temperature (°C) at which the module’s rated power is
        specified.
    ghi_reference : float, default 1000.0
        Reference irradiance (W m⁻²) corresponding to 1 kWₚ.  Standard test
        conditions specify 1000 W m⁻².
    tcell_coeff : float, default 0.025
        Empirical coefficient relating irradiance to the increase in cell
        temperature above ambient (°C per W m⁻²).  Pfenninger & Staffell
        estimated a similar value【861615956447402†L280-L294】.

    Returns
    -------
    pandas.Series
        Hourly PV capacity factor (0–1) indexed like ``weather``.

    Notes
    -----
    * This function provides a simplified representation of the GSEE model.
      It does not account for diffuse/direct separation, incidence angle
      geometry or inverter/shading losses explicitly.  Nevertheless it
      preserves the key dependencies on irradiance and temperature and
      produces reasonable capacity factors for regional analyses when
      detailed data are unavailable.
    * Users with access to direct and diffuse irradiance and precise
      orientation information can substitute this function with more
      sophisticated models (e.g. using the ``pvlib`` library) to compute
      plane‑of‑array irradiance and module output.
    """
    if ghi_col not in weather.columns or temp_col not in weather.columns:
        raise KeyError(f"Weather DataFrame must contain columns '{ghi_col}' and '{temp_col}'.")
    ghi = weather[ghi_col].astype(float).clip(lower=0)
    temp_air = weather[temp_col].astype(float)
    # Approximate plane‑of‑array irradiance
    i_poa = ghi * orientation_factor
    # Estimate PV cell temperature
    t_cell = temp_air + tcell_coeff * i_poa
    # Temperature‑dependent efficiency ratio
    eta_ratio = 1.0 + temp_coeff * (t_cell - reference_temp)
    # Compute capacity factor; ensure non‑negative and cap at 1
    cf = (i_poa / ghi_reference) * eta_ratio
    return cf.clip(lower=0, upper=1).rename('pv_capacity_factor')


def compute_wind_capacity_factor_from_weather(
    weather: pd.DataFrame,
    wind_speed_col: str = 'wind_speed',
    ref_height: float = 10.0,
    hub_height: float = 100.0,
    roughness_length: float = 0.03,
    cut_in: float = 3.0,
    rated: float = 12.0,
    cut_out: float = 25.0,
    smoothing: bool = True,
    sigma_coef: Tuple[float, float] = (0.6, 0.2),
) -> pd.Series:
    """
    Estimate wind turbine capacity factors from area‑weighted wind speed data.

    This function implements a simplified version of the Virtual Wind Farm
    (VWF) model described by Staffell & Pfenninger (2016)【751685054143373†L406-L433】.
    The steps are:

    1. **Extrapolate wind speeds to hub height:**  Wind speeds measured at
       reference height (e.g. 10 m) are extrapolated to the turbine hub height
       using the logarithmic wind profile formula:

       ``v_hub = v_ref * (ln(hub_height / z0) / ln(ref_height / z0))``

       where ``z0`` is the surface roughness length.  This corresponds to
       Equation 2 in the VWF model【751685054143373†L406-L433】.

    2. **Convert wind speeds to turbine power:**  A piecewise cubic power
       curve is used to approximate the relationship between wind speed and
       output.  Below the cut‑in speed the output is zero; between cut‑in and
       rated speeds it scales with ``((v - cut_in)/(rated - cut_in))³``;
       above the rated speed the output is constant at full output; and above
       the cut‑out speed the turbines shut down.  This follows the general
       shape of the smoothed power curves used in the VWF model【751685054143373†L406-L433】.
       Optionally, a simple Gaussian smoothing can be applied to reflect
       intrahour variability across turbines as described by Staffell & Pfenninger.

    3. **Capacity factor:**  The normalized turbine output is the capacity
       factor (0–1) for each hour.

    Parameters
    ----------
    weather : pandas.DataFrame
        DataFrame indexed by timestamps with a column of wind speeds at the
        reference height ``wind_speed_col`` (m s⁻¹).  These speeds should be
        aggregated (area‑weighted) across the region of interest.
    wind_speed_col : str, default 'wind_speed'
        Column name containing wind speed at the reference height.
    ref_height : float, default 10.0
        Height (m) at which wind speeds in ``weather`` are measured.
    hub_height : float, default 100.0
        Turbine hub height (m) used for extrapolating wind speeds.
    roughness_length : float, default 0.03
        Surface roughness length (m) used in the logarithmic wind profile.  A
        value of 0.03 m corresponds to open farmland.
    cut_in : float, default 3.0
        Turbine cut‑in wind speed (m s⁻¹).  Below this speed the turbine does
        not generate.
    rated : float, default 12.0
        Wind speed at which the turbine reaches full power output (m s⁻¹).
    cut_out : float, default 25.0
        Wind speed above which the turbine shuts down to avoid damage (m s⁻¹).
    smoothing : bool, default True
        Whether to apply a Gaussian smoothing to the power curve to mimic the
        smoothing effect of aggregating many turbines【751685054143373†L406-L433】.
    sigma_coef : tuple(float, float), default (0.6, 0.2)
        Coefficients ``(a, b)`` used to compute the smoothing width
        ``sigma = a + b * v_hub`` if ``smoothing`` is True.  This replicates
        the smoothing parameterization in the VWF model【751685054143373†L406-L433】.

    Returns
    -------
    pandas.Series
        Hourly wind capacity factor (0–1) indexed like ``weather``.

    Notes
    -----
    * The simple power curve implemented here does not distinguish between
      onshore and offshore turbines or account for site‑specific power curves.
      For more accurate simulations, supply a custom power curve or use
      ``windpowerlib`` with specific turbine parameters.
    * Bias corrections described by Staffell & Pfenninger (comparing
      simulated and observed capacity factors) are not applied here
      【751685054143373†L549-L569】; users can calibrate the resulting capacity
      factors externally by multiplying by a bias factor if desired.
    """
    if wind_speed_col not in weather.columns:
        raise KeyError(f"Weather DataFrame must contain column '{wind_speed_col}'.")
    v_ref = weather[wind_speed_col].astype(float).clip(lower=0)
    # Extrapolate to hub height using logarithmic wind profile
    if ref_height <= roughness_length or hub_height <= roughness_length:
        raise ValueError("Heights must be greater than the roughness length for log profile extrapolation.")
    log_ratio = np.log(hub_height / roughness_length) / np.log(ref_height / roughness_length)
    v_hub = v_ref * log_ratio
    # Piecewise power curve (normalized to 1 at rated)
    def power_curve(v: np.ndarray) -> np.ndarray:
        p = np.zeros_like(v)
        # Between cut‑in and rated: cubic ramp
        mask_ramp = (v >= cut_in) & (v < rated)
        p[mask_ramp] = ((v[mask_ramp] - cut_in) / (rated - cut_in)) ** 3
        # Between rated and cut‑out: full power
        mask_full = (v >= rated) & (v < cut_out)
        p[mask_full] = 1.0
        # Elsewhere remains zero
        return p
    # Wrap raw capacity factors in a Series for consistent indexing
    cf_raw_series = pd.Series(power_curve(v_hub), index=weather.index)
    if smoothing:
        # Apply Gaussian smoothing to simulate turbine aggregation effects
        a, b = sigma_coef
        sigma = a + b * v_hub
        # Convert sigma to a numpy array to avoid pandas indexing warnings
        sigma_arr = np.asarray(sigma, dtype=float)
        window_size = 5
        values = cf_raw_series.values
        smoothed_vals = np.empty_like(values)
        # Compute smoothed values using a moving Gaussian window
        for i in range(len(values)):
            half_win = window_size // 2
            left = max(i - half_win, 0)
            right = min(i + half_win + 1, len(values))
            idx = np.arange(left, right)
            weights_win = np.exp(-0.5 * ((idx - i) ** 2) / (sigma_arr[i] ** 2))
            weights_sum = weights_win.sum()
            if weights_sum > 0:
                weights_win /= weights_sum
                smoothed_vals[i] = np.dot(values[idx], weights_win)
            else:
                smoothed_vals[i] = values[i]
        cf_smoothed = pd.Series(smoothed_vals, index=weather.index)
    else:
        cf_smoothed = cf_raw_series
    return cf_smoothed.clip(lower=0, upper=1).rename('wind_capacity_factor')

###############################################################################
# Weather data utilities
###############################################################################

def build_weather_file_name(
    country_code: str,
    variable: str,
    weight: str = 'area',
    dataset: str = 'merra2',
) -> str:
    """
    Construct the filename for a Renewables.ninja country‑aggregated weather CSV.

    Renewables.ninja exposes pre‑computed weather time series for each country
    and variable in the form

    ``ninja-weather-country-<ISO2>-<variable>_<weight>_wtd-<dataset>.csv``.

    Parameters
    ----------
    country_code : str
        ISO‑2 country code (e.g. 'KR' for South Korea).
    variable : str
        Short variable name such as ``irradiance_surface``, ``temperature`` or
        ``wind_speed``.  See the API metadata for the available variables【608637583202059†L66-L122】.
    weight : str, default 'area'
        Weighting method: ``'area'`` or ``'pop'``.  This corresponds to land
        area weighting or population weighting respectively.
    dataset : str, default 'merra2'
        Underlying meteorological dataset.  Currently only ``'merra2'`` is
        supported in the public country downloads.

    Returns
    -------
    str
        Filename of the weather CSV (without any directory prefix).
    """
    iso2 = country_code.upper()
    # Normalise variable name (replace spaces and hyphens with underscores)
    var_norm = variable.strip().replace(' ', '_').replace('-', '_')
    weight_norm = weight.strip().lower()
    return f"ninja-weather-country-{iso2}-{var_norm}_{weight_norm}_wtd-{dataset}.csv"


def load_weather_data(
    data_dir: str,
    country_code: str,
    variables: Iterable[str],
    weight: str = 'area',
    dataset: str = 'merra2',
    use_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load multiple weather variables for a given country from Renewables.ninja files.

    The Renewables.ninja country downloads include hourly weather time series
    aggregated over the country using area or population weights.  This
    function reads the specified variables from CSV files in ``data_dir`` and
    returns a DataFrame indexed by timestamps (UTC).  Comment lines
    beginning with ``#`` are skipped.  Each variable is assigned to its own
    column.

    Parameters
    ----------
    data_dir : str
        Directory containing the downloaded weather CSV files.
    country_code : str
        ISO‑2 code of the country (e.g. 'KR').  Must match the codes used
        in the filenames.
    variables : Iterable[str]
        Names of the weather variables to load (e.g. ['irradiance_surface',
        'temperature', 'wind_speed']).  These names should correspond to
        the ``variable`` argument of :func:`build_weather_file_name`.
    weight : str, default 'area'
        Weighting method ('area' or 'pop').
    dataset : str, default 'merra2'
        Underlying meteorological dataset ('merra2').

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by UTC timestamps with columns for each requested
        variable.  All timestamps are timezone‐aware and in UTC.

    Notes
    -----
    * Renewables.ninja files include several comment lines (starting with
      ``#``) containing metadata.  These are automatically skipped.
    * Each CSV contains a ``time`` column (UTC) and one or more columns
      named by ISO‑2 country code or region code.  Because these files
      contain only aggregated data for one country, the second column is
      assumed to be the desired variable.
    * If a requested file is not found, a ``FileNotFoundError`` will be
      raised.  Ensure that the user has downloaded all required weather
      files into ``data_dir`` as automatic downloads are blocked by the
      Renewables.ninja server.
    """
    iso2 = country_code.upper()
    variables_tuple = tuple(variables)

    # ------------------------------------------------------------------
    # Cache short-circuit. The cache key embeds country, dataset, weight,
    # and the (sorted) variable list so different callers stay isolated.
    # Source mtimes are checked against the cache; any newer source CSV
    # invalidates and rebuilds.
    # ------------------------------------------------------------------
    if use_cache:
        sorted_vars = '__'.join(sorted(_safe_filename_part(v) for v in variables_tuple))
        cache_name = (
            f"weather_{_safe_filename_part(iso2)}_"
            f"{_safe_filename_part(dataset)}_{_safe_filename_part(weight)}_"
            f"{sorted_vars}.parquet"
        )
        cache_path = os.path.join(_resolve_cache_dir(data_dir, cache_dir), cache_name)
        source_paths = [
            os.path.join(data_dir, build_weather_file_name(iso2, v, weight, dataset))
            for v in variables_tuple
        ]

        def _build():
            return _load_weather_data_uncached(
                data_dir, iso2, variables_tuple, weight, dataset
            )
        return _read_or_build_cached_parquet(cache_path, source_paths, _build)

    return _load_weather_data_uncached(data_dir, iso2, variables_tuple, weight, dataset)


def _load_weather_data_uncached(
    data_dir: str,
    iso2: str,
    variables: Tuple[str, ...],
    weight: str,
    dataset: str,
) -> pd.DataFrame:
    """Original (uncached) body of :func:`load_weather_data`."""
    frames = []
    for var in variables:
        fname = build_weather_file_name(iso2, var, weight, dataset)
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Weather file '{path}' not found. Please download the file "
                f"from Renewables.ninja (variable '{var}', weighting '{weight}', dataset '{dataset}') "
                f"and place it in '{data_dir}'."
            )
        # Read the CSV and skip initial comment lines. Renewables.ninja files
        # begin with several comment lines that start with the string
        # "#" (surrounded by double quotes) followed by a header row
        # containing the column names (e.g. "time","KR"). The pandas
        # ``comment`` parameter does not strip these because the double
        # quote appears before the hash. To robustly skip comment lines,
        # count how many lines in the file start with '"#' and pass
        # that value to ``skiprows``.
        skip_rows = 0
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('"#'):
                    skip_rows += 1
                    continue
                else:
                    break
        # Now read the file, skipping the detected comment lines. After
        # skipping, the first row should be the header (e.g. "time","KR").
        df_var = pd.read_csv(path, skiprows=skip_rows)
        # Validate that there are at least two columns (time and variable)
        if df_var.shape[1] < 2:
            raise ValueError(f"Unexpected format in {path}; expected at least 2 columns after skipping comments.")
        # Rename the second column to the requested variable name. The
        # column names may be quoted, so use the second column's current
        # name directly.
        var_col = df_var.columns[1]
        df_var = df_var.rename(columns={var_col: var})
        # Parse the 'time' column to timezone-aware timestamps in UTC
        df_var['time'] = pd.to_datetime(df_var['time'], utc=True)
        df_var = df_var.set_index('time')
        # Append only the column corresponding to the requested variable
        frames.append(df_var[[var]])
    # Merge on the index
    weather_df = pd.concat(frames, axis=1)
    return weather_df


def download_file(url: str, dest_path: str, headers: Optional[Dict[str, str]] = None) -> None:
    """
    Download a file from a URL and save it to ``dest_path``.

    This helper uses the requests library to stream content from the
    remote server to a local file.  If the download fails due to an
    HTTP error (e.g. 403 or 404), an exception is raised.  A custom
    ``User-Agent`` header is added by default to mimic a web browser.

    Parameters
    ----------
    url : str
        Fully qualified URL of the file to download.
    dest_path : str
        Path on the local filesystem where the file should be saved.  If
        intermediate directories do not exist they are created.
    headers : dict, optional
        Additional HTTP headers to include in the request.  By default a
        ``User-Agent`` header is added if not provided.
    """
    headers = headers or {}
    # Provide a default User-Agent to avoid potential blocking by the
    # server.  A simple Mozilla string is used here.
    headers.setdefault('User-Agent', 'Mozilla/5.0 (compatible; energy-timeslice-pipeline)')
    # Create destination directory if needed
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def download_weather_files(
    country_code: str,
    variables: Iterable[str],
    weight: str = 'area',
    dataset: str = 'merra2',
    output_dir: str = '.',
    base_url: str = 'https://www.renewables.ninja',
    headers: Optional[Dict[str, str]] = None,
) -> None:
    """
    Download Renewables.ninja country‑aggregated weather CSVs.

    Renewables.ninja hosts pre‑computed weather time series for each
    country and variable at URLs of the form::

        https://www.renewables.ninja/country_downloads/{ISO2}/ninja-weather-country-{ISO2}-{variable}_{weight}_wtd-{dataset}.csv

    This function iterates over the requested variables and attempts to
    download each file if it does not already exist in ``output_dir``.
    If a download fails with an HTTP error, the exception is propagated
    to the caller.

    Parameters
    ----------
    country_code : str
        ISO‑2 country code (e.g. 'KR').  Case‑insensitive.
    variables : Iterable[str]
        Weather variables to download (e.g. ['irradiance_surface', 'temperature', 'wind_speed']).
    weight : str, default 'area'
        Weighting method ('area' or 'pop').
    dataset : str, default 'merra2'
        Meteorological dataset ('merra2').
    output_dir : str, default '.'
        Local directory where downloaded files will be saved.  Files
        retain their original filenames.
    base_url : str, default 'https://www.renewables.ninja'
        Base URL for the Renewables.ninja downloads.  Change this
        argument only if the hosting domain changes.
    headers : dict, optional
        Additional HTTP headers to send with the request.  This can be
        used to provide API tokens or cookies required by
        Renewables.ninja.  If omitted, a default User‑Agent header is
        set automatically.

    """
    iso2 = country_code.strip().upper()
    for var in variables:
        fname = build_weather_file_name(iso2, var, weight, dataset)
        url = f"{base_url}/country_downloads/{iso2}/{fname}"
        dest_path = os.path.join(output_dir, fname)
        # Skip download if the file already exists
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            continue
        try:
            download_file(url, dest_path, headers=headers)
        except HTTPError as e:
            # Propagate the error to inform the caller that the download failed
            raise RuntimeError(
                f"Failed to download weather file '{fname}' for {iso2} from {url}: {e}"
            ) from e


def download_ember_dataset(
    dest_path: str,
    primary_url: str = 'https://files.ember-energy.org/public-downloads/yearly_full_release_long_format.csv',
    fallback_url: str = 'https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv',
) -> None:
    """
    Download the Ember yearly electricity dataset (long format).

    This helper attempts to download the official Ember dataset from the
    ``primary_url``.  If the download fails with an HTTP error, a
    fallback dataset hosted by Our World in Data (OWID) is downloaded
    instead.  The OWID energy dataset includes the Ember yearly
    electricity data and is licensed for public use.  After downloading
    either file, it is saved to ``dest_path``.  The function does not
    perform any post‑processing; callers should load and filter the
    contents as needed.

    Parameters
    ----------
    dest_path : str
        Path where the CSV file will be saved.
    primary_url : str, optional
        Primary URL for the Ember dataset.  Defaults to the official
        release hosted by Ember.
    fallback_url : str, optional
        Fallback URL for the OWID energy dataset, used if the primary
        download fails.
    """
    try:
        download_file(primary_url, dest_path)
    except Exception as primary_err:
        # Attempt fallback
        try:
            download_file(fallback_url, dest_path)
        except Exception as fallback_err:
            raise RuntimeError(
                f"Failed to download the Ember dataset from both primary and fallback locations.\n"
                f"Primary error: {primary_err}\nFallback error: {fallback_err}"
            ) from fallback_err


def _find_mendeley_data_root(search_dir: str) -> Optional[str]:
    """Find the directory containing the extracted Mendeley CSV files."""
    for root, _, files in os.walk(search_dir):
        file_set = set(files)
        if all(required in file_set for required in MENDELEY_REQUIRED_FILES):
            return root
    return None


def ensure_mendeley_dataset(
    data_dir: str,
    dataset_url: str = MENDELEY_DATASET_URL,
    headers: Optional[Dict[str, str]] = None,
) -> str:
    """Ensure the Mendeley end-use dataset is present locally and return its root."""
    existing_root = _find_mendeley_data_root(data_dir)
    if existing_root is not None:
        return existing_root

    os.makedirs(data_dir, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='mendeley_download_') as temp_dir:
        zip_path = os.path.join(temp_dir, 'mendeley_dataset.zip')
        download_file(dataset_url, zip_path, headers=headers)
        with zipfile.ZipFile(zip_path, 'r') as archive:
            archive.extractall(data_dir)

    extracted_root = _find_mendeley_data_root(data_dir)
    if extracted_root is None:
        raise FileNotFoundError(
            "Downloaded the Mendeley dataset archive, but could not locate the expected CSV files "
            f"under '{data_dir}'."
        )
    return extracted_root


def ensure_efs_dataset(
    data_dir: str,
    dataset_url: str = EFS_DATASET_URL,
    headers: Optional[Dict[str, str]] = None,
) -> str:
    """Ensure the EFS reference/moderate load-profile archive is present locally."""
    os.makedirs(data_dir, exist_ok=True)
    zip_path = os.path.join(data_dir, 'EFSLoadProfile_Reference_Moderate.zip')
    if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
        download_file(dataset_url, zip_path, headers=headers)
    return zip_path


def _nearest_efs_year(target_year: int) -> int:
    """Return the available EFS study year nearest to the requested year."""
    return min(EFS_AVAILABLE_YEARS, key=lambda y: (abs(y - int(target_year)), y))


def _load_efs_space_conditioning_split_template(
    mendeley_root: str,
    region: str,
    year: int,
    scenario: str = 'SSP2',
) -> Dict[str, pd.Series]:
    """Build heating/cooling split ratios from the Zapata/Mendeley profiles."""
    template_df = load_enduse_data_mendeley(mendeley_root, region, year, scenario=scenario)
    ratios: Dict[str, pd.Series] = {}
    for prefix in ('residential', 'service'):
        heating_col = f'{prefix}_heating'
        cooling_col = f'{prefix}_cooling'
        total = template_df[heating_col] + template_df[cooling_col]
        ratios[f'{prefix}_heating_ratio'] = (template_df[heating_col] / total.replace(0, np.nan)).fillna(0.5)
        ratios[f'{prefix}_cooling_ratio'] = (template_df[cooling_col] / total.replace(0, np.nan)).fillna(0.5)
    return ratios


def load_recs_monthly_space_conditioning_split(
    workbook_path: str = DEFAULT_EPS_SHELF_WORKBOOK_PATH,
) -> Dict[int, Dict[str, float]]:
    """Load monthly U.S. residential heating/cooling split multipliers from RECS."""
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ImportError(
            "Reading the RECS workbook requires openpyxl. Install it in the active environment."
        ) from exc

    if not os.path.exists(workbook_path):
        raise FileNotFoundError(f"RECS workbook not found at '{workbook_path}'.")

    wb = load_workbook(workbook_path, read_only=True, data_only=True)
    table_map = {
        'RECS CE8.2.M': 'heating',
        'RECS CE8.3.M': 'cooling',
    }
    monthly_values: Dict[str, Dict[int, float]] = {'heating': {}, 'cooling': {}}
    month_lookup = {calendar.month_name[i]: i for i in range(1, 13)}
    for sheet_name, key in table_map.items():
        ws = wb[sheet_name]
        header_row = next(ws.iter_rows(min_row=4, max_row=4, values_only=True))
        data_row = next(ws.iter_rows(min_row=5, max_row=5, values_only=True))
        for header, value in zip(header_row, data_row):
            if header in month_lookup:
                monthly_values[key][month_lookup[header]] = float(value or 0.0)

    ratios: Dict[int, Dict[str, float]] = {}
    for month in range(1, 13):
        heating = monthly_values['heating'].get(month, 0.0)
        cooling = monthly_values['cooling'].get(month, 0.0)
        total = heating + cooling
        if total <= 0:
            ratios[month] = {'heating': 0.5, 'cooling': 0.5}
        else:
            ratios[month] = {'heating': heating / total, 'cooling': cooling / total}
    return ratios


def load_enduse_data_efs_us(
    efs_zip_path: str,
    requested_year: int,
    electrification: str = 'Reference',
    technology_advancement: str = 'Moderate',
    recs_workbook_path: Optional[str] = DEFAULT_EPS_SHELF_WORKBOOK_PATH,
    split_template_root: Optional[str] = None,
    split_template_region: str = 'USA',
    split_template_scenario: str = 'SSP2',
    use_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> pd.DataFrame:
    """Load U.S. hourly end-use demand using NREL's Electrification Futures Study."""

    # ------------------------------------------------------------------
    # Cache short-circuit. EFS streaming through the deflate64 shim takes
    # several minutes; the cached parquet is one year × ~10 columns and
    # reads in a few seconds. The cache is keyed on the EFS scenario and
    # the resolved EFS year (which is rounded to the nearest available
    # EFS year, so a 2025 request and a 2024 request hit the same cache).
    # ------------------------------------------------------------------
    if use_cache:
        efs_year_for_key = _nearest_efs_year(requested_year)
        cache_name = (
            f"efs_{_safe_filename_part(electrification)}_"
            f"{_safe_filename_part(technology_advancement)}_"
            f"{_safe_filename_part(efs_year_for_key)}_"
            f"{_safe_filename_part(split_template_region)}_"
            f"{_safe_filename_part(split_template_scenario)}.parquet"
        )
        # Use the EFS zip's directory as the cache base when no cache_dir
        # is supplied (keeps EFS-derived files near the source).
        base_dir = cache_dir or _resolve_cache_dir(
            os.path.dirname(os.path.dirname(efs_zip_path)),
            None,
        )
        cache_path = os.path.join(base_dir, cache_name)
        # Source mtimes that matter for invalidation:
        #   - EFS zip itself (the bulk of the input)
        #   - RECS workbook (drives the monthly heating/cooling split)
        #   - Mendeley template directory's residential/service CSVs (drive
        #     the sub-monthly split ratios). Watching just one stable file
        #     in that directory is sufficient as a signal.
        source_paths = [efs_zip_path]
        if recs_workbook_path:
            source_paths.append(recs_workbook_path)
        if split_template_root:
            source_paths.append(
                os.path.join(split_template_root, 'Residential_heating_weekday.csv')
            )

        def _build():
            return load_enduse_data_efs_us(
                efs_zip_path=efs_zip_path,
                requested_year=requested_year,
                electrification=electrification,
                technology_advancement=technology_advancement,
                recs_workbook_path=recs_workbook_path,
                split_template_root=split_template_root,
                split_template_region=split_template_region,
                split_template_scenario=split_template_scenario,
                use_cache=False,
                cache_dir=None,
            )
        return _read_or_build_cached_parquet(cache_path, source_paths, _build)

    try:
        import zipfile_deflate64  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Reading the EFS archive requires the 'zipfile-deflate64' package. "
            "Install it in the active environment to enable the U.S. demand-shape path."
        ) from exc

    efs_year = _nearest_efs_year(requested_year)
    aggregate_frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(efs_zip_path) as archive:
        if EFS_REQUIRED_FILE not in archive.namelist():
            raise FileNotFoundError(
                f"Expected '{EFS_REQUIRED_FILE}' inside '{efs_zip_path}', but it was not found."
            )
        with archive.open(EFS_REQUIRED_FILE) as raw_handle:
            text_handle = io.TextIOWrapper(raw_handle, encoding='utf-8-sig', newline='')
            reader = pd.read_csv(
                text_handle,
                usecols=[
                    'Electrification',
                    'TechnologyAdvancement',
                    'Year',
                    'LocalHourID',
                    'Sector',
                    'Subsector',
                    'LoadMW',
                ],
                chunksize=500_000,
            )
            for chunk in reader:
                mask = (
                    chunk['Electrification'].astype(str).str.strip().str.lower() == electrification.lower()
                ) & (
                    chunk['TechnologyAdvancement'].astype(str).str.strip().str.lower() == technology_advancement.lower()
                ) & (
                    pd.to_numeric(chunk['Year'], errors='coerce') == efs_year
                )
                filtered = chunk.loc[mask, ['LocalHourID', 'Sector', 'Subsector', 'LoadMW']].copy()
                if filtered.empty:
                    continue
                filtered['LocalHourID'] = pd.to_numeric(filtered['LocalHourID'], errors='coerce').astype('Int64')
                filtered['LoadMW'] = pd.to_numeric(filtered['LoadMW'], errors='coerce')
                grouped = (
                    filtered
                    .dropna(subset=['LocalHourID', 'LoadMW'])
                    .groupby(['LocalHourID', 'Sector', 'Subsector'], as_index=False)['LoadMW']
                    .sum()
                )
                aggregate_frames.append(grouped)

    if not aggregate_frames:
        raise ValueError(
            f"No EFS rows were found for Electrification='{electrification}', "
            f"TechnologyAdvancement='{technology_advancement}', Year={efs_year}."
        )

    aggregated = pd.concat(aggregate_frames, ignore_index=True)
    aggregated = aggregated.groupby(['LocalHourID', 'Sector', 'Subsector'], as_index=False)['LoadMW'].sum()
    hourly = aggregated.pivot_table(
        index='LocalHourID',
        columns=['Sector', 'Subsector'],
        values='LoadMW',
        aggfunc='sum',
        fill_value=0.0,
    ).sort_index()

    expected_hours = 8760
    if len(hourly.index) != expected_hours or int(hourly.index.min()) != 1 or int(hourly.index.max()) != expected_hours:
        raise ValueError(
            f"EFS U.S. hourly profile is expected to span LocalHourID 1..{expected_hours}, "
            f"but observed range {hourly.index.min()}..{hourly.index.max()} with {len(hourly.index)} rows."
        )

    timestamps = pd.date_range(start=f'{efs_year}-01-01 00:00:00', periods=expected_hours, freq='h')
    hourly.index = timestamps
    hourly.index.name = 'timestamp'

    def _series(sector: str, subsector: str) -> pd.Series:
        if (sector, subsector) in hourly.columns:
            return hourly[(sector, subsector)].astype(float)
        return pd.Series(0.0, index=hourly.index)

    df = pd.DataFrame(index=hourly.index)
    df['residential_space_conditioning'] = _series('Residential', 'space heating and cooling')
    df['residential_waterheating'] = _series('Residential', 'water heating')
    df['residential_appliances'] = _series('Residential', 'clothes and dish washing/drying')
    df['residential_other'] = _series('Residential', 'other')

    df['service_space_conditioning'] = _series('Commercial', 'space heating and cooling')
    df['service_waterheating'] = _series('Commercial', 'water heating')
    df['service_other'] = _series('Commercial', 'other')

    df['industry_machine_drives'] = _series('Industrial', 'machine drives')
    df['industry_process_heat'] = _series('Industrial', 'process heat')
    df['industry_other'] = _series('Industrial', 'other')
    df['industry'] = df[['industry_machine_drives', 'industry_process_heat', 'industry_other']].sum(axis=1)
    df['industry_total'] = df['industry']

    df['transport_ldv'] = _series('Transportation', 'light-duty vehicles')
    df['transport_mdv'] = _series('Transportation', 'medium-duty trucks')
    df['transport_hdv'] = _series('Transportation', 'heavy-duty trucks')
    df['transport_other'] = _series('Transportation', 'other')
    df['transport'] = df[['transport_ldv', 'transport_mdv', 'transport_hdv', 'transport_other']].sum(axis=1)
    df['transport_total'] = df['transport']

    if recs_workbook_path:
        monthly_split = load_recs_monthly_space_conditioning_split(recs_workbook_path)
        heating_ratio = pd.Series(
            [monthly_split[ts.month]['heating'] for ts in df.index],
            index=df.index,
        )
        cooling_ratio = pd.Series(
            [monthly_split[ts.month]['cooling'] for ts in df.index],
            index=df.index,
        )
        split_ratios = {
            'residential_heating_ratio': heating_ratio,
            'residential_cooling_ratio': cooling_ratio,
            'service_heating_ratio': heating_ratio,
            'service_cooling_ratio': cooling_ratio,
        }
    elif split_template_root:
        split_ratios = _load_efs_space_conditioning_split_template(
            split_template_root,
            split_template_region,
            requested_year,
            scenario=split_template_scenario,
        )
    else:
        uniform_index = pd.Series(0.5, index=df.index)
        split_ratios = {
            'residential_heating_ratio': uniform_index,
            'residential_cooling_ratio': uniform_index,
            'service_heating_ratio': uniform_index,
            'service_cooling_ratio': uniform_index,
        }

    df['residential_heating'] = df['residential_space_conditioning'] * split_ratios['residential_heating_ratio'].to_numpy()
    df['residential_cooling'] = df['residential_space_conditioning'] * split_ratios['residential_cooling_ratio'].to_numpy()
    df['service_heating'] = df['service_space_conditioning'] * split_ratios['service_heating_ratio'].to_numpy()
    df['service_cooling'] = df['service_space_conditioning'] * split_ratios['service_cooling_ratio'].to_numpy()

    df['residential_waterheating'] = df['residential_waterheating']
    df['service_waterheating'] = df['service_waterheating']
    df['residential_lighting'] = 0.0
    df['residential_total'] = (
        df['residential_heating']
        + df['residential_cooling']
        + df['residential_waterheating']
        + df['residential_appliances']
        + df['residential_other']
    )
    df['service_total'] = (
        df['service_heating']
        + df['service_cooling']
        + df['service_waterheating']
        + df['service_other']
    )
    df['load'] = df[['residential_total', 'service_total', 'industry_total', 'transport_total']].sum(axis=1)
    df = df.drop(columns=['residential_space_conditioning', 'service_space_conditioning'])
    df.attrs['demand_shape_source'] = 'efs'
    df.attrs['demand_shape_source_year'] = efs_year
    df.attrs['demand_shape_source_scenario'] = f'{electrification}/{technology_advancement}'
    return df


def ensure_demandcast_source(
    repo_dir: str = DEMANDCAST_LOCAL_DIR,
    repo_url: str = DEMANDCAST_REPO_URL,
) -> str:
    """Ensure a local checkout of DemandCast exists and return its source root."""
    if not os.path.exists(repo_dir):
        os.makedirs(os.path.dirname(repo_dir), exist_ok=True)
        subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, repo_dir],
            check=True,
        )

    source_root = os.path.join(repo_dir, 'demandcast')
    if not os.path.exists(source_root):
        raise FileNotFoundError(
            f"DemandCast source root was not found at '{source_root}'."
        )
    return source_root


# DemandCast retrievers that read pre-staged "manual" files look in
# <demandcast_root>/data/electricity_demand/manual_downloads/. The canonical
# home for those files in this repo is data/manual_downloads/. The pipeline
# mirrors files matching these prefixes from the canonical folder into the
# DemandCast clone before each run, so users only need to maintain one copy.
#
# Add a prefix here when you bring a new DemandCast manual source online
# (each retriever module under
# .vendor/demandcast/demandcast/retrievals/electricity_demand_data_sources/
# documents the file prefix it expects).
DEMANDCAST_MANUAL_FILE_PREFIXES: Tuple[str, ...] = (
    'KRO',     # KROGD: South Korea hourly demand (data.go.kr → krogd.py)
    # 'EPIAS', # Turkey (epias.py)             — uncomment when populated
    # 'eskom', # South Africa (eskom.py)       — uncomment when populated
    # 'NITI',  # India (niti.py)               — uncomment when populated
    # 'NTDC',  # Pakistan (ntdc.py)            — uncomment when populated
)


def _sync_manual_downloads_to_demandcast(
    data_dir: str,
    demandcast_root: str,
    prefixes: Iterable[str] = DEMANDCAST_MANUAL_FILE_PREFIXES,
    quiet: bool = False,
) -> int:
    """
    Mirror manually-staged demand files from ``<data_dir>/manual_downloads/``
    into the DemandCast clone's ``data/electricity_demand/manual_downloads/``.

    The canonical location is the project repo's ``data/manual_downloads/``;
    this function only writes into the DemandCast clone, never the other way.
    The sync is idempotent: a file that already exists at the destination
    with a matching size and a not-older mtime is skipped.

    Parameters
    ----------
    data_dir : str
        The repo's data directory (the parent of ``manual_downloads/``).
    demandcast_root : str
        The DemandCast source root returned by :func:`ensure_demandcast_source`
        (i.e. ``<repo>/demandcast``, not the wrapper checkout above it).
    prefixes : iterable of str
        Filename prefixes to mirror. Defaults to
        :data:`DEMANDCAST_MANUAL_FILE_PREFIXES`.
    quiet : bool, default False
        When False, print a one-line summary if any files were copied.

    Returns
    -------
    int
        Number of files actually copied this call (0 means everything was
        already up to date or no matching files existed).
    """
    src_dir = os.path.join(data_dir, 'manual_downloads')
    dst_dir = os.path.join(
        demandcast_root, 'data', 'electricity_demand', 'manual_downloads',
    )
    if not os.path.isdir(src_dir):
        return 0
    os.makedirs(dst_dir, exist_ok=True)
    prefixes_t = tuple(prefixes)
    if not prefixes_t:
        return 0

    copied = 0
    for name in os.listdir(src_dir):
        # Mirror only CSV files. DemandCast retrievers parse every prefix-matched
        # file in their manual_downloads/ folder as a CSV, so any non-CSV (a
        # README, sources.txt, notes.docx, etc.) that gets mirrored would crash
        # the parser. The .csv-only filter here is defense in depth on top of
        # the per-folder README convention documented in
        # data/manual_downloads/README.md.
        if not (name.startswith(prefixes_t) and name.lower().endswith('.csv')):
            continue
        src = os.path.join(src_dir, name)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dst_dir, name)
        if os.path.exists(dst):
            src_st = os.stat(src)
            dst_st = os.stat(dst)
            if src_st.st_size == dst_st.st_size and dst_st.st_mtime >= src_st.st_mtime:
                continue
        shutil.copy2(src, dst)
        copied += 1

    if copied and not quiet:
        print(
            f"[manual-downloads] Mirrored {copied} file(s) from "
            f"{src_dir} -> {dst_dir}"
        )
    return copied


def resolve_output_path(output_path: Optional[str], country: Optional[str] = None) -> Optional[str]:
    """Resolve output paths into the default output directory unless absolute."""
    if output_path is None and country is None:
        return None

    if output_path is None:
        output_path = f"{country}_timeslice_results.xlsx" if country else "timeslice_results.xlsx"

    if not os.path.isabs(output_path):
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(DEFAULT_OUTPUT_DIR, output_path)
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    return output_path


def _read_env_file_value(key: str, env_path: Optional[str] = None) -> Optional[str]:
    """Read a simple KEY=VALUE pair from a local .env file if present."""
    env_path = env_path or os.path.join(os.getcwd(), '.env')
    if not os.path.exists(env_path):
        return None
    with open(env_path, 'r', encoding='utf-8') as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or '=' not in stripped:
                continue
            name, value = stripped.split('=', 1)
            if name.strip() == key:
                return value.strip().strip('"').strip("'")
    return None


def _normalize_country_lookup(country: str) -> str:
    """Normalize a user-provided country label for preset lookup."""
    normalized = ''.join(ch.lower() if ch.isalnum() else ' ' for ch in country)
    return ' '.join(normalized.split())


def get_country_preset(country: str) -> Dict[str, Any]:
    """Resolve a country alias to a configured preset."""
    lookup = _normalize_country_lookup(country)
    for canonical_name, preset in COUNTRY_PRESETS.items():
        aliases = [_normalize_country_lookup(canonical_name)]
        aliases.extend(_normalize_country_lookup(alias) for alias in preset.get('aliases', []))
        if lookup in aliases:
            resolved = dict(preset)
            resolved['canonical_name'] = canonical_name.title()
            return resolved
    supported = ', '.join(sorted(name.title() for name in COUNTRY_PRESETS))
    raise KeyError(f"Unsupported country '{country}'. Supported presets: {supported}.")


def elccafr_run_metadata(country: Optional[str]) -> Dict[str, Any]:
    """Preset-resolved ELCCAfR settings, for inclusion in ``run_metadata``.

    Falls back to the module defaults for an unrecognized or missing country so
    a bare-DataFrame pipeline call still exports ELCCAfR.
    """
    try:
        preset = get_country_preset(country) if country else {}
    except KeyError:
        preset = {}
    return {
        'elccafr_statistic': preset.get('elccafr_statistic', ELCCAfR_STATISTIC_DEFAULT),
        'elccafr_demand_altering': preset.get(
            'elccafr_demand_altering', ELCCAfR_DEMAND_ALTERING_DEFAULT),
    }


def list_country_presets() -> pd.DataFrame:
    """List the built-in country presets and their readiness status."""
    rows = []
    for canonical_name, preset in sorted(COUNTRY_PRESETS.items()):
        rows.append({
            'country': canonical_name.title(),
            'output_country': preset['output_country'],
            'country_iso2': preset['country_iso2'],
            'demand_country_code': preset['demand_country_code'],
            'demand_shape_source': preset.get('demand_shape_source', 'mendeley'),
            'default_year': preset['default_year'],
            'last_n_years': preset['last_n_years'],
            'status': preset.get('status', 'mapped'),
        })
    return pd.DataFrame(rows)


# Sentinel for the ``demand_series_csv`` override meaning "use DemandCast",
# distinct from ``None`` (= "no override, apply the preset rule").
DEMANDCAST_SOURCE = 'demandcast'


def resolve_demand_series_csv(
    preset: Dict[str, Any],
    year: int,
    last_n_years: int,
    override: Optional[str] = None,
) -> Optional[str]:
    """Choose the observed-demand source for a run.

    Returns the path of a staged hourly demand CSV, or ``None`` to fall back to
    DemandCast (:func:`fetch_demand_data_demandcast`).

    Resolution order:

    1. ``override`` — the runner's ``DEMAND_SERIES_CSV`` setting. A path forces
       that CSV; the literal ``'demandcast'`` forces DemandCast; ``None`` means
       "no override" and falls through.
    2. The preset's ``demand_series_csv``, unless the preset also defines
       ``demandcast_pin`` and this run matches it — in which case DemandCast is
       used instead.
    3. ``None`` (DemandCast) for presets with no ``demand_series_csv`` at all.

    ``demandcast_pin`` exists because China has two observed hourly records with
    different coverage. DemandCast's Wu et al. source covers 2018 only, so it is
    kept for the run configuration it can actually serve (``year=2018``,
    ``last_n_years=1``) and the multi-year Yi et al. CSV is used whenever the run
    asks for a different target year or a wider calibration window. A pin may
    name ``year``, ``last_n_years``, or both; every named field must match.
    """
    if override is not None:
        if str(override).strip().lower() == DEMANDCAST_SOURCE:
            return None
        return override

    csv_path = preset.get('demand_series_csv')
    if not csv_path:
        return None

    pin = preset.get('demandcast_pin')
    if isinstance(pin, dict) and pin:
        run_config = {'year': year, 'last_n_years': last_n_years}
        if all(run_config.get(key) == value for key, value in pin.items()):
            return None
    return csv_path


def generate_full_pipeline_for_preset(
    country: str,
    year: Optional[int] = None,
    n_clusters: int = 6,
    output_path: Optional[str] = None,
    last_n_years: Optional[int] = None,
    data_dir: str = DEFAULT_DATA_DIR,
    seasonal_calibration: bool = True,
    scenario: str = 'SSP2',
    efs_electrification: Optional[str] = None,
    efs_technology_advancement: Optional[str] = None,
    **kwargs,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Run the full pipeline using a built-in country preset.

    United-States-only EFS scenario choices (``efs_electrification`` /
    ``efs_technology_advancement``) may be supplied from the caller (e.g. the
    ``run_pipeline.py`` control surface). When provided they OVERRIDE the
    preset's default; when left ``None`` the preset default is used. They are
    ignored for non-US presets, which use Zapata/Mendeley demand shapes.
    """
    preset = get_country_preset(country)
    selected_year = year or preset['default_year']
    selected_last_n_years = last_n_years or preset.get('last_n_years', 3)
    # Runner override (if not None) takes precedence over the preset default.
    resolved_efs_electrification = (
        efs_electrification if efs_electrification is not None
        else preset.get('efs_electrification', 'Reference')
    )
    resolved_efs_technology_advancement = (
        efs_technology_advancement if efs_technology_advancement is not None
        else preset.get('efs_technology_advancement', 'Moderate')
    )
    # Per-preset behavior pinning (same pattern as the EFS overrides above):
    # runner override (not None) → preset value → global default. This is
    # what lets the United States preset pin master-parity choices
    # ('multiplicative' CF scaling, 'level_seasonal' demand calibration)
    # while international presets keep cap_redistribute / Zapata defaults.
    resolved_cf_calibration_mode = kwargs.pop('cf_calibration_mode', None)
    if resolved_cf_calibration_mode is None:
        resolved_cf_calibration_mode = preset.get('cf_calibration_mode', 'cap_redistribute')
    resolved_calibration_method = kwargs.pop('calibration_method', None)
    if resolved_calibration_method is None:
        resolved_calibration_method = preset.get('calibration_method', 'level_seasonal')
    # Wind-CF year window (only meaningful for wind_cf_source='ninja_sites'):
    # runner override (not None) → preset → None (country fn falls back to
    # last_n_years). Decoupled from last_n_years so wind can average more years
    # of the site-simulation archive than the demand-calibration window uses.
    resolved_wind_cf_years = kwargs.pop('wind_cf_years', None)
    if resolved_wind_cf_years is None:
        resolved_wind_cf_years = preset.get('wind_cf_years')
    # Observed-demand source. A staged local CSV takes precedence over
    # DemandCast; presets without a 'demand_series_csv' key use DemandCast as
    # before. See resolve_demand_series_csv for the run-config rule that lets a
    # preset keep DemandCast for one pinned (year, window) and switch to its CSV
    # for everything else.
    resolved_demand_series_csv = resolve_demand_series_csv(
        preset,
        year=selected_year,
        last_n_years=selected_last_n_years,
        override=kwargs.pop('demand_series_csv', None),
    )
    return generate_full_pipeline_for_country(
        mendeley_dir=os.path.join(data_dir, 'mendeley'),
        efs_dir=os.path.join(data_dir, 'efs'),
        weather_dir=os.path.join(data_dir, 'weather'),
        ember_csv_path=os.path.join(data_dir, 'ember', 'yearly_full_release_long_format.csv'),
        region_name=preset['output_country'],
        country_iso2=preset['country_iso2'],
        demand_country_code=preset['demand_country_code'],
        year=selected_year,
        mendeley_region_name=preset['mendeley_region_name'],
        ember_country_name=preset['ember_country_name'],
        last_n_years=selected_last_n_years,
        n_clusters=n_clusters,
        output_path=output_path,
        seasonal_calibration=seasonal_calibration,
        scenario=scenario,
        demand_shape_source=preset.get('demand_shape_source', 'mendeley'),
        efs_electrification=resolved_efs_electrification,
        efs_technology_advancement=resolved_efs_technology_advancement,
        country_timezone=preset.get('timezone'),
        allow_utc_weather=preset.get('allow_utc_weather', False),
        cf_calibration_mode=resolved_cf_calibration_mode,
        wind_cf_source=preset.get('wind_cf_source', 'weather'),
        wind_sites_dir=preset.get('wind_sites_dir'),
        wind_cf_years=resolved_wind_cf_years,
        wind_capacity_split=preset.get('wind_capacity_split'),
        calibration_method=resolved_calibration_method,
        latitude_deg=preset.get('latitude_deg'),
        eps_prior_path=preset.get('eps_prior_path'),
        lambda_ridge=preset.get('lambda_ridge', kwargs.pop('lambda_ridge', 1.0)),
        demand_series_csv=resolved_demand_series_csv,
        demand_series_citation=preset.get('demand_series_citation'),
        **kwargs,
    )


def _load_eia_subdivision_codes() -> list[str]:
    """Load the available EIA respondent subdivision codes for the USA."""
    if not os.path.exists(EIA_SOURCE_YAML):
        return []
    with open(EIA_SOURCE_YAML, 'r', encoding='utf-8') as handle:
        data = yaml.safe_load(handle) or {}
    entities = data.get('entities', [])
    return [
        str(entity.get('subdivision_code', '')).strip().upper()
        for entity in entities
        if str(entity.get('country_code', '')).strip().upper() == 'USA'
        and str(entity.get('subdivision_code', '')).strip()
    ]


def _fetch_eia_respondent_series(
    respondent_code: str,
    api_key: str,
    start_year: int,
    end_year: int,
) -> pd.Series:
    """Fetch an hourly EIA respondent demand series and return it in UTC."""
    respondent_code = respondent_code.strip().upper()
    intervals = pd.date_range(
        start=f'{start_year}-01-01',
        end=f'{end_year + 1}-01-01',
        freq='6MS',
    )
    intervals = list(intervals)
    series_parts: list[pd.Series] = []
    session = requests.Session()
    for start_ts, end_ts in zip(intervals[:-1], intervals[1:]):
        params = {
            'api_key': api_key,
            'frequency': 'hourly',
            'data[0]': 'value',
            'facets[type][]': 'D',
            'facets[respondent][]': respondent_code,
            'start': start_ts.strftime('%Y-%m-%dT%H'),
            'end': (end_ts - pd.Timedelta(hours=1)).strftime('%Y-%m-%dT%H'),
            'sort[0][column]': 'period',
            'sort[0][direction]': 'asc',
            'offset': 0,
            'length': 5000,
        }
        last_error: Optional[Exception] = None
        response = None
        for attempt in range(5):
            try:
                response = session.get(
                    'https://api.eia.gov/v2/electricity/rto/region-data/data/',
                    params=params,
                    timeout=60,
                )
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = exc
                time.sleep(min(2 ** attempt, 20))
        if response is None:
            raise requests.ConnectionError(
                f'Failed to retrieve EIA data for respondent {respondent_code} '
                f'between {start_ts:%Y-%m-%d} and {(end_ts - pd.Timedelta(hours=1)):%Y-%m-%d}.'
            ) from last_error
        payload = response.json()
        records = payload.get('response', {}).get('data', [])
        if not records:
            continue
        df_records = pd.DataFrame(records)
        if 'period' not in df_records or 'value' not in df_records:
            continue
        timestamps = pd.DatetimeIndex(pd.to_datetime(df_records['period'])).tz_localize('UTC')
        part = pd.Series(
            pd.to_numeric(df_records['value'], errors='coerce').to_numpy(),
            index=timestamps,
            name=respondent_code,
        ).dropna()
        if not part.empty:
            series_parts.append(part)
    if not series_parts:
        raise ValueError(f'No EIA demand data returned for respondent {respondent_code}.')
    combined = pd.concat(series_parts).sort_index()
    combined = combined.groupby(combined.index).mean()
    return combined


def _fetch_eia_us_national_series(
    start_year: int = 2020,
    end_year: Optional[int] = None,
) -> pd.Series:
    """Aggregate EIA respondent series into a reproducible national USA series."""
    end_year = end_year or _datetime.datetime.now().year
    api_key = os.getenv('EIA_API_KEY') or _read_env_file_value('EIA_API_KEY')
    if not api_key:
        raise ValueError(
            "The EIA API key is not set. Add EIA_API_KEY to the environment or local .env file."
        )
    subdivision_codes = _load_eia_subdivision_codes()
    if not subdivision_codes:
        raise FileNotFoundError(
            f"Unable to load EIA respondent codes from '{EIA_SOURCE_YAML}'."
        )
    national_series: Optional[pd.Series] = None
    for subdivision_code in subdivision_codes:
        respondent_series = _fetch_eia_respondent_series(
            subdivision_code,
            api_key=api_key,
            start_year=start_year,
            end_year=end_year,
        )
        if national_series is None:
            national_series = respondent_series
        else:
            national_series = national_series.add(respondent_series, fill_value=0.0)
    if national_series is None or national_series.empty:
        raise ValueError('No EIA respondent data could be aggregated for USA.')
    national_series = national_series.sort_index().groupby(level=0).sum()
    national_series.name = 'USA'
    return national_series


def _find_demandcast_sources_containing_code(
    source_root: str,
    code: str,
) -> list[str]:
    """Read DemandCast source YAMLs and return matching electricity-demand sources."""
    sources_dir = os.path.join(
        source_root,
        'retrievals',
        'electricity_demand_data_sources',
    )
    matches: list[str] = []
    normalized = code.replace('-', '_').upper()
    for name in os.listdir(sources_dir):
        if not name.endswith('.yaml'):
            continue
        path = os.path.join(sources_dir, name)
        with open(path, 'r', encoding='utf-8') as handle:
            data = yaml.safe_load(handle)
        entities = data.get('entities', []) if isinstance(data, dict) else []
        for entity in entities:
            country_code = str(entity.get('country_code', '')).upper()
            subdivision_code = str(entity.get('subdivision_code', '')).upper()
            combined = (
                f"{country_code}_{subdivision_code}".rstrip('_')
                if subdivision_code and subdivision_code != 'NONE'
                else country_code
            )
            if normalized in {country_code, combined}:
                matches.append(os.path.splitext(name)[0])
                break
    matches.sort()
    return matches


def _retrieve_demandcast_series_from_source(
    source_root: str,
    data_source: str,
    code: str,
) -> pd.Series:
    """Retrieve a demand series from a single DemandCast source module."""
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
    retrieval_module = importlib.import_module(
        f'retrievals.electricity_demand_data_sources.{data_source}'
    )
    if data_source == 'wu_et_al':
        # DemandCast's China parser can fail on newer pandas string dtypes.
        # Parse the source CSV directly so the CHN path remains reproducible.
        dataset = pd.read_csv(retrieval_module.get_url(), sep=';', engine='python')
        numeric_columns = dataset.columns[1:]
        dataset[numeric_columns] = dataset[numeric_columns].apply(
            pd.to_numeric, errors='coerce'
        )
        national_demand = dataset[numeric_columns].sum(axis=1)
        timestamps = pd.date_range(
            start='2018-01-01 01:00:00',
            periods=len(national_demand),
            freq='h',
            tz='Asia/Shanghai',
        )
        return pd.Series(national_demand.to_numpy(), index=timestamps, name=code)
    requests_list = retrieval_module.get_available_requests()
    if requests_list is None:
        return retrieval_module.download_and_extract_data()
    raise RuntimeError(
        f"DemandCast source '{data_source}' requires request-based retrieval that "
        "is not yet wired into this script fallback."
    )


def compute_capacity_factors_from_weather(
    weather: pd.DataFrame,
    pv_irradiance_col: str = 'irradiance_surface',
    temp_col: str = 'temperature',
    wind_col: str = 'wind_speed',
    orientation_factor: float = 1.1,
    ref_height: float = 2.0,
    hub_height: float = 100.0,
    roughness_length: float = 0.03,
    **kwargs,
) -> pd.DataFrame:
    """
    Compute solar PV and wind capacity factors from weather variables.

    Parameters
    ----------
    weather : pandas.DataFrame
        DataFrame with columns for irradiance (W m⁻²), temperature (°C) and
        wind speed (m s⁻¹).  The index must be timestamps in UTC.
    pv_irradiance_col : str
        Name of the irradiance column.  Default ``'irradiance_surface'``.
    temp_col : str
        Name of the ambient temperature column.  Default ``'temperature'``.
    wind_col : str
        Name of the wind speed column at the reference height.  Default
        ``'wind_speed'``.
    orientation_factor : float, default 1.1
        See :func:`compute_pv_capacity_factor_from_weather`.
    ref_height : float, default 2.0
        Reference height for wind speed measurements (m).  Renewables.ninja
        provides wind speed at 2 m; this is extrapolated to hub height.
    hub_height : float, default 100.0
        Hub height of the turbines for wind power calculation (m).
    roughness_length : float, default 0.03
        Surface roughness length for wind speed extrapolation (m).
    **kwargs : dict
        Additional parameters passed to the underlying PV and wind capacity
        factor functions.

    Returns
    -------
    pandas.DataFrame
        DataFrame with two columns: ``'solar_cf'`` and ``'wind_cf'``.
    """
    # Compute PV capacity factors
    pv_cf = compute_pv_capacity_factor_from_weather(
        weather, ghi_col=pv_irradiance_col, temp_col=temp_col,
        orientation_factor=orientation_factor, **kwargs
    )
    # Compute wind capacity factors; rename column appropriately
    wind_cf = compute_wind_capacity_factor_from_weather(
        weather, wind_speed_col=wind_col,
        ref_height=ref_height, hub_height=hub_height,
        roughness_length=roughness_length, **kwargs
    )
    df_cf = pd.concat([pv_cf, wind_cf], axis=1)
    df_cf.columns = ['solar_cf', 'wind_cf']
    return df_cf


DEFAULT_WIND_SITES_DIR = os.path.join(DEFAULT_DATA_DIR, 'weather', 'ninja_sim')

# Wind-site types, and the CF column each one produces. 'wind_cf' stays the
# blended (fleet-wide) series used for net load and clustering; the per-type
# columns feed SYSHECF-onshore-wind / SYSHECF-offshore-wind.
WIND_SITE_TYPES: Tuple[str, ...] = ('onshore', 'offshore')
WIND_SITE_TYPE_CF_COLUMNS: Dict[str, str] = {
    'onshore': 'wind_onshore_cf',
    'offshore': 'wind_offshore_cf',
}
# Fallback classifier: filename markers used for offshore sites. Only consulted
# for site files that are not in the fetcher's SITES table.
_OFFSHORE_SITE_NAME_MARKERS: Tuple[str, ...] = ('osw', 'offshore', 'off-shore', 'off_shore')


def _fetcher_wind_site_types() -> Dict[Tuple[str, str], str]:
    """``(ISO2, site_name) → 'onshore'|'offshore'`` from the fetcher's SITES table.

    ``scripts/fetch_ninja_sites.py`` is the single source of truth for site
    classification: its ``SITES`` entries carry the ``type`` that selected the
    turbine and hub height for each download, so the same table decides which
    SYSHECF technology a site's output belongs to. Returns ``{}`` if the fetcher
    module cannot be imported, leaving the filename fallback in charge.
    """
    cached = getattr(_fetcher_wind_site_types, '_cache', None)
    if cached is not None:
        return cached
    types: Dict[Tuple[str, str], str] = {}
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
    try:
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        sites = importlib.import_module('fetch_ninja_sites').SITES
    except Exception:  # noqa: BLE001 — classification degrades to the name fallback
        sites = []
    for site in sites:
        site_type = str(site.get('type', '')).strip().lower()
        if site_type in WIND_SITE_TYPES:
            types[(str(site.get('country', '')).upper(), str(site.get('name', '')))] = site_type
    _fetcher_wind_site_types._cache = types  # type: ignore[attr-defined]
    return types


def classify_wind_site(country_iso2: str, site_name: str) -> str:
    """Classify a Renewables.ninja wind site as ``'onshore'`` or ``'offshore'``.

    Primary source is the fetcher's ``SITES`` table (see
    :func:`_fetcher_wind_site_types`). Sites missing from it fall back to a
    filename marker (``_OSW``, ``Offshore``, …); anything unmarked is treated as
    onshore, which is the safe default because onshore dominates every fleet in
    the current preset list.
    """
    declared = _fetcher_wind_site_types().get((str(country_iso2).upper(), site_name))
    if declared:
        return declared
    lowered = site_name.lower()
    if any(marker in lowered for marker in _OFFSHORE_SITE_NAME_MARKERS):
        return 'offshore'
    return 'onshore'


DEFAULT_WIND_CAPACITY_SPLIT_CSV = os.path.join(DEFAULT_DATA_DIR, 'eps_wind_capacity_split.csv')


def load_eps_wind_capacity_split(
    country_iso2: str,
    csv_path: Optional[str] = None,
) -> Optional[Dict[str, float]]:
    """Onshore/offshore wind capacity shares for a region, or ``None`` if unknown.

    Reads ``data/eps_wind_capacity_split.csv``, produced by
    ``scripts/fetch_eps_wind_capacity_split.py`` from each regional EPS model's
    ``InputData/elec/BHRaSYC/BHRaSYC-StartYearCapacities.csv`` (the sum over
    vintage columns is that technology's start-year capacity). Using the model's
    own start-year fleet means the blended ``wind_cf`` — and therefore the Ember
    calibration anchor behind the onshore/offshore SYSHECF tables — is weighted
    by the same capacity mix the EPS run will dispatch.

    Returns ``{'onshore': share, 'offshore': share}``, or ``None`` when the
    region has no row (the caller then falls back to site-count weighting).
    Refresh the CSV after a model's start-year capacities change.
    """
    path = csv_path or DEFAULT_WIND_CAPACITY_SPLIT_CSV
    if not os.path.exists(path):
        return None
    try:
        table = pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001 — a bad lookup must not kill the run
        _status('cf', f"  wind capacity split: could not read {path} ({exc}); "
                      "falling back to site-count weighting")
        return None
    if 'iso2' not in table.columns:
        return None
    match = table[table['iso2'].astype(str).str.upper() == str(country_iso2).upper()]
    if match.empty:
        return None
    row = match.iloc[-1]
    try:
        onshore = float(row['onshore_share'])
        offshore = float(row['offshore_share'])
    except (KeyError, TypeError, ValueError):
        return None
    if not (np.isfinite(onshore) and np.isfinite(offshore)) or onshore + offshore <= 0:
        return None
    _status(
        'cf',
        f"  wind capacity split for {str(country_iso2).upper()}: "
        f"onshore={onshore:.4f}  offshore={offshore:.4f}  "
        f"({float(row.get('onshore_mw', float('nan'))):,.0f} / "
        f"{float(row.get('offshore_mw', float('nan'))):,.0f} MW start-year capacity, "
        f"{row.get('source_model', 'unknown model')} "
        f"{row.get('source_file', '')}, retrieved {row.get('retrieved', 'n/a')})",
    )
    return {'onshore': onshore, 'offshore': offshore}


def load_site_wind_capacity_factors(
    country_iso2: str,
    n_years: int,
    sites_dir: Optional[str] = None,
    country_timezone: Optional[str] = None,
    capacity_split: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """Average Renewables.ninja per-site wind SIMULATION output into hourly CF series.

    Reads ``<sites_dir>/<ISO2>/<site>_<year>.csv`` files produced by
    ``scripts/fetch_ninja_sites.py``, keeps the most recent ``n_years`` of
    calendar-year data **available on disk**, and averages the site
    ``electricity`` columns at each hour. Because the fetch uses ``capacity=1``,
    ``electricity`` IS the hourly capacity factor (0-1) at hub height — sheared
    and bias-corrected by Renewables.ninja's simulation.

    Every site is classified onshore vs offshore (:func:`classify_wind_site`),
    so the return carries **three** series where both types are present:

    * ``wind_cf``          — blended / fleet-wide, used for net load + clustering
    * ``wind_onshore_cf``  — mean over onshore sites   → SYSHECF-onshore-wind
    * ``wind_offshore_cf`` — mean over offshore sites  → SYSHECF-offshore-wind

    The blend is capacity-weighted when ``capacity_split`` is supplied and
    site-count-weighted otherwise (see that parameter). Countries whose site set
    is all one type get only ``wind_cf`` plus that type's column.

    This REPLACES the legacy 2 m-wind-speed → log-shear → power-curve estimate
    (:func:`compute_wind_capacity_factor_from_weather`). The 2 m ninja *weather*
    variable has an inverted diurnal cycle relative to hub height and is
    unusable for wind shape; the site simulation output is the correct source.
    See CLAUDE.md and DECISIONS.md (2026-07-10).

    The wind window is **decoupled from the demand/CF calibration window**
    (``last_n_years``): wind uses its own ``n_years`` of site data (preset key
    ``wind_cf_years``). The returned multi-year series is reduced to a
    day-of-year × hour climatology by the caller and mapped onto the run's
    calendar, so the number of wind years need not match the number of demand
    years. Selection is the most recent ``n_years`` years actually present, not
    a window anchored to the model year — the site archive (2018–2024) is a
    weather climatology independent of the model's target year.

    Times in the source files are UTC. When ``country_timezone`` is given the
    returned index is converted to that timezone so it aligns with the localized
    weather series used elsewhere in the pipeline (the demand/SHELF side runs on
    local time). The instant of each observation is preserved; only the labels
    change.

    Parameters
    ----------
    country_iso2 : str
        ISO2 code naming the per-country subfolder (e.g. ``'CN'``).
    n_years : int
        Number of most-recent available site-years to average (preset
        ``wind_cf_years``). If fewer years exist on disk, all are used and a
        status line reports the shortfall.
    sites_dir : str, optional
        Root directory holding ``<ISO2>/`` subfolders. Defaults to
        ``data/weather/ninja_sim``.
    country_timezone : str, optional
        IANA timezone to convert the UTC index into. ``None`` leaves it in UTC.
    capacity_split : dict, optional
        Installed-capacity weights for the blended ``wind_cf`` column, e.g.
        ``{'onshore': 0.92, 'offshore': 0.08}`` (preset key
        ``wind_capacity_split``; renormalized internally, so MW work as well as
        shares). Only used when both site types are present. When omitted the
        blend is the plain mean over all site-years — i.e. weighted by how many
        sites of each type were downloaded, which is an artifact of the fetch
        list rather than of the fleet. Supply it when the onshore/offshore
        capacity mix is known; the status line reports which weighting was used.

    Returns
    -------
    pandas.DataFrame
        Hourly wind capacity factors on a tz-aware index spanning the selected
        site-years: ``'wind_cf'`` (blended) plus ``'wind_onshore_cf'`` and/or
        ``'wind_offshore_cf'`` for the site types present.
        ``df.attrs['wind_site_types']`` maps each site name to its class and
        ``df.attrs['wind_blend_weights']`` records the weights used.
    """
    import glob as _glob

    sites_dir = sites_dir or DEFAULT_WIND_SITES_DIR
    country_dir = os.path.join(sites_dir, country_iso2)
    if not os.path.isdir(country_dir):
        raise FileNotFoundError(
            f"No site-wind directory for {country_iso2!r} at {country_dir!r}. "
            f"Run  python scripts/fetch_ninja_sites.py --country {country_iso2}  first."
        )

    # Discover (path, site, year) for every well-named CSV, then select the most
    # recent n_years years actually present on disk.
    parsed: List[tuple] = []
    for path in sorted(_glob.glob(os.path.join(country_dir, '*.csv'))):
        stem = os.path.splitext(os.path.basename(path))[0]
        # filename convention from fetch_ninja_sites.py: <site>_<year>.csv
        site, _, yr = stem.rpartition('_')
        if yr.isdigit():
            parsed.append((path, site, int(yr)))
    if not parsed:
        raise FileNotFoundError(
            f"No <site>_<year>.csv files for {country_iso2!r} under {country_dir!r}. "
            f"Fetch them with scripts/fetch_ninja_sites.py."
        )
    available_years = sorted({y for _, _, y in parsed})
    n_req = int(n_years) if n_years else len(available_years)
    sel_years = set(available_years[-n_req:])
    if len(sel_years) < n_req:
        _status(
            'cf',
            f"  wind_cf: requested {n_req} year(s) but only {len(sel_years)} "
            f"site-year(s) on disk for {country_iso2} ({sorted(sel_years)}) — using all available",
        )

    frames: List[pd.Series] = []
    frames_by_type: Dict[str, List[pd.Series]] = {t: [] for t in WIND_SITE_TYPES}
    site_types: Dict[str, str] = {}
    used_years: set = set()
    for path, site, yr in parsed:
        if yr not in sel_years:
            continue
        # Renewables.ninja CSVs carry a metadata header block; the data header
        # row starts with 'time'. Find it dynamically so the parser survives
        # header-length changes between API versions.
        with open(path, encoding='utf-8') as fh:
            skip = next((i for i, line in enumerate(fh) if line.startswith('time')), 0)
        df = pd.read_csv(path, skiprows=skip, usecols=['time', 'electricity'])
        s = pd.Series(
            pd.to_numeric(df['electricity'], errors='coerce').to_numpy(),
            index=pd.to_datetime(df['time'], utc=True),
            name='wind_cf',
        )
        site_type = classify_wind_site(country_iso2, site)
        frames.append(s)
        frames_by_type[site_type].append(s)
        site_types[site] = site_type
        used_years.add(yr)

    if not frames:
        raise FileNotFoundError(
            f"No site-wind CSVs for {country_iso2!r} in years {sorted(sel_years)} "
            f"under {country_dir!r}. Fetch them with scripts/fetch_ninja_sites.py."
        )

    def _mean_over(series_list: List[pd.Series]) -> pd.Series:
        """Mean across site-year series at each UTC timestamp.

        Concatenating then grouping by the (duplicated) timestamp index means
        each hour is the mean over whatever sites are present for that hour —
        robust to a site missing a year.
        """
        return pd.concat(series_list).groupby(level=0).mean().sort_index()

    by_type: Dict[str, pd.Series] = {
        t: _mean_over(frames_by_type[t]) for t in WIND_SITE_TYPES if frames_by_type[t]
    }
    out = pd.DataFrame({WIND_SITE_TYPE_CF_COLUMNS[t]: s for t, s in by_type.items()})

    # Blended (fleet-wide) series. With both types present the blend weights
    # decide how much each type's shape contributes; capacity shares are the
    # physically meaningful weights, and the all-site mean (site-count
    # weighting) is the fallback when the split is unknown. Weights are applied
    # NaN-aware (renormalized over the types that have data in a given hour) so
    # a type missing a year cannot blank out the blend.
    weights: Dict[str, float] = {}
    if len(by_type) == 1:
        only_type = next(iter(by_type))
        weights = {only_type: 1.0}
        wind_cf = by_type[only_type].copy()
        weight_basis = f'{only_type}-only site set'
    elif capacity_split:
        raw_w = {t: float(capacity_split.get(t, 0.0) or 0.0) for t in by_type}
        total_w = sum(raw_w.values())
        if total_w <= 0:
            raise ValueError(
                f"capacity_split {capacity_split!r} gives zero total weight for the "
                f"site types present ({sorted(by_type)})."
            )
        weights = {t: w / total_w for t, w in raw_w.items()}
        w_frame = pd.DataFrame(
            {WIND_SITE_TYPE_CF_COLUMNS[t]: w for t, w in weights.items()},
            index=out.index,
        ).where(out.notna())
        wind_cf = (out * w_frame).sum(axis=1) / w_frame.sum(axis=1)
        weight_basis = 'capacity-weighted (' + ', '.join(
            f'{t}={weights[t]:.3f}' for t in sorted(weights)
        ) + ')'
    else:
        wind_cf = _mean_over(frames)
        n_by_type = {t: len(frames_by_type[t]) for t in by_type}
        n_total = sum(n_by_type.values())
        weights = {t: n / n_total for t, n in n_by_type.items()}
        weight_basis = 'site-count-weighted (no wind_capacity_split preset key)'
    out.insert(0, 'wind_cf', wind_cf.reindex(out.index))

    # Localize UTC → country timezone so the index aligns with the localized
    # weather elsewhere in the pipeline (instant preserved, labels shift).
    if country_timezone:
        out.index = out.index.tz_convert(country_timezone)

    n_sites_by_type = {t: sum(1 for v in site_types.values() if v == t) for t in by_type}
    _status(
        'cf',
        f"wind_cf source = ninja site outputs: averaged {len(site_types)} site(s) "
        f"({', '.join(f'{n} {t}' for t, n in sorted(n_sites_by_type.items()))}) "
        f"× years {sorted(used_years)} ({len(out):,} hours)  "
        f"raw annual-mean CF={float(out['wind_cf'].mean()):.4f}",
    )
    for site_type in sorted(by_type):
        members = sorted(s for s, t in site_types.items() if t == site_type)
        _status(
            'cf',
            f"  {WIND_SITE_TYPE_CF_COLUMNS[site_type]}: raw annual-mean CF="
            f"{float(out[WIND_SITE_TYPE_CF_COLUMNS[site_type]].mean()):.4f}  "
            f"from {', '.join(members)}",
        )
    _status('cf', f"  blended wind_cf weighting: {weight_basis}")

    out.attrs['wind_site_types'] = site_types
    out.attrs['wind_blend_weights'] = weights
    return out


def load_ember_annual_capacity_factors(
    ember_csv_path: str,
    country: str,
    variables: Iterable[str] = ('Solar', 'Wind'),
    last_n_years: int = 3,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Compute average installed capacity and capacity factors from Ember data.

    This function reads the Ember yearly full release CSV and extracts
    electricity generation and capacity data for the specified country and
    technology variables.  It then computes the average installed capacity
    (GW) and average generation (TWh) over the most recent ``last_n_years``
    for which data are available.  Finally, it returns two dictionaries:
    one mapping variable names to average installed capacity (GW) and the
    other mapping variable names to average observed capacity factors
    (fraction).

    Parameters
    ----------
    ember_csv_path : str
        Path to the Ember ``yearly_full_release_long_format.csv`` file.
    country : str
        Name of the country (e.g. 'South Korea') exactly as it appears in
        the ``Area`` column of the Ember dataset.
    variables : iterable of str, default ('Solar', 'Wind')
        Technologies to extract.  These names must match the values in
        the ``Variable`` column of the Ember dataset (case‑sensitive).
    last_n_years : int, default 3
        Number of most recent years to average.  If fewer years are
        available for a variable, the function will use all available
        years but issue a warning.

    Returns
    -------
    (dict, dict)
        Tuple of two dictionaries.  The first maps each variable to the
        average installed capacity (GW) across the selected years.  The
        second maps each variable to the average observed capacity factor
        (0–1) computed from generation and capacity data.

    Notes
    -----
    * The Ember dataset contains both absolute values (units 'TWh' for
      generation and 'GW' for capacity) and percentage shares ('%').
      This function filters by units to ensure only absolute values are
      considered.
    * Capacity factor is calculated as

      ``CF = (generation_TWh * 1e3) / (capacity_GW * 8760)``

      where generation is converted to GWh.【608637583202059†L66-L122】
    """
    df = pd.read_csv(ember_csv_path)
    # Filter for the specified country and the most recent years with data
    capacity_dict: Dict[str, float] = {}
    cf_dict: Dict[str, float] = {}
    for var in variables:
        # Capacity rows: Category == 'Capacity', Subcategory == 'Fuel', Variable == var, Unit == 'GW'
        df_cap = df[
            (df['Area'] == country) &
            (df['Category'] == 'Capacity') &
            (df['Variable'] == var) &
            (df['Unit'] == 'GW')
        ]
        df_gen = df[
            (df['Area'] == country) &
            (df['Category'] == 'Electricity generation') &
            (df['Variable'] == var) &
            (df['Unit'] == 'TWh')
        ]
        # Determine available years for generation and capacity
        years_cap = df_cap['Year'].dropna().unique()
        years_gen = df_gen['Year'].dropna().unique()
        years = sorted(set(years_cap) & set(years_gen))
        if not years:
            raise ValueError(f"No overlapping capacity and generation data for variable '{var}' in {country}.")
        max_year = max(years)
        # Select the most recent N years
        selected_years = [y for y in years if y >= max_year - last_n_years + 1]
        if len(selected_years) < last_n_years:
            # Warn but proceed
            import warnings
            warnings.warn(
                f"Only {len(selected_years)} years of data available for {var} in {country}; "
                f"averaging across {len(selected_years)} years instead of {last_n_years}."
            )
        df_cap_sel = df_cap[df_cap['Year'].isin(selected_years)]
        df_gen_sel = df_gen[df_gen['Year'].isin(selected_years)]
        # Compute average capacity (GW)
        cap_avg = df_cap_sel['Value'].astype(float).mean()
        # Compute average generation (TWh)
        gen_avg_twh = df_gen_sel['Value'].astype(float).mean()
        # Convert generation to GWh
        gen_avg_gwh = gen_avg_twh * 1e3
        # Compute capacity factor
        if cap_avg <= 0:
            cf_obs = 0.0
        else:
            cf_obs = gen_avg_gwh / (cap_avg * 8760)
        capacity_dict[var] = cap_avg
        cf_dict[var] = cf_obs
    return capacity_dict, cf_dict


CF_CALIBRATION_MODES = ('cap_redistribute', 'multiplicative')
CF_CALIBRATION_MULTIPLIER_WARN_THRESHOLD = 1.5


def _cap_and_redistribute_cf(
    values: np.ndarray,
    target_mean: float,
    *,
    max_iter: int = 10,
    tol: float = 1e-9,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Scale ``values`` so that the non-NaN mean equals ``target_mean`` while
    keeping every entry in [0, 1].

    The algorithm:
      1. Apply the multiplicative scale ``s = target_mean / sample_mean``.
      2. If ``s <= 1`` (we are scaling down), no entry can exceed 1.0 from
         the multiplication alone — clip to [0, 1] and return.
      3. Otherwise some entries may exceed 1.0. Clip them to 1.0, sum the
         excess, and redistribute it across unsaturated entries with
         per-entry weights proportional to their headroom ``(1 - cf_i)``.
         The redistribution preserves the target mean exactly (single
         iteration is mathematically sufficient; we still loop a few times
         as a safety net against floating-point drift).

    Returns
    -------
    (np.ndarray, dict)
        The bounded calibrated values and a diagnostics dict containing:
            ``mode`` — always ``'cap_redistribute'`` for this helper
            ``initial_mean`` — pre-calibration sample mean
            ``target_mean`` — the requested target
            ``initial_multiplier`` — ``target_mean / initial_mean``
            ``iterations`` — how many cap-and-redistribute passes ran
            ``fraction_at_cap`` — share of non-NaN hours pinned at 1.0
            ``final_max`` — max calibrated value
            ``residual_mean_error`` — calibrated_mean − target_mean
            ``mean_unreachable`` — True if the target could not be hit
                                     because the synthetic distribution
                                     is too saturated to absorb the
                                     redistributed energy.
    """
    arr = np.asarray(values, dtype=float).copy()
    nan_mask = np.isnan(arr)
    finite = arr[~nan_mask]
    n_finite = finite.size

    diag: Dict[str, Any] = {
        'mode': 'cap_redistribute',
        'initial_mean': float(np.nanmean(arr)) if n_finite else float('nan'),
        'target_mean': float(target_mean) if target_mean is not None else float('nan'),
        'initial_multiplier': float('nan'),
        'iterations': 0,
        'fraction_at_cap': float('nan'),
        'final_max': float(np.nanmax(arr)) if n_finite else float('nan'),
        'residual_mean_error': float('nan'),
        'mean_unreachable': False,
    }

    if n_finite == 0 or target_mean is None or not np.isfinite(target_mean):
        return arr, diag

    if target_mean < 0 or target_mean > 1:
        raise ValueError(
            f"target_mean must lie in [0, 1] for capacity factor calibration; "
            f"got {target_mean!r}."
        )

    initial_mean = diag['initial_mean']
    if not np.isfinite(initial_mean) or initial_mean <= 0:
        # Cannot scale a zero-mean (or NaN-mean) sample; leave unchanged.
        return arr, diag

    multiplier = target_mean / initial_mean
    diag['initial_multiplier'] = float(multiplier)

    # Apply the initial multiplicative scale.
    out = arr * multiplier

    if multiplier <= 1.0:
        # Scaling down or by exactly 1: no cap step needed (no value can
        # exceed 1.0 if it started in [0, 1]). Clip negatives just in case.
        np.clip(out, 0.0, 1.0, out=out)
        finite_out = out[~nan_mask]
        diag['iterations'] = 1
        diag['fraction_at_cap'] = float(np.mean(finite_out >= 1.0 - 1e-9))
        diag['final_max'] = float(np.nanmax(out))
        diag['residual_mean_error'] = float(np.nanmean(out) - target_mean)
        return out, diag

    # Multiplier > 1: cap-and-redistribute loop.
    for it in range(1, max_iter + 1):
        diag['iterations'] = it
        excess_per_hour = np.where(~nan_mask, np.maximum(out - 1.0, 0.0), 0.0)
        excess = float(excess_per_hour.sum())
        # Clip excess down to 1.0
        out = np.where(nan_mask, out, np.clip(out, 0.0, 1.0))
        if excess <= tol:
            break
        # Headroom is the per-entry amount we can still absorb.
        headroom = np.where(~nan_mask & (out < 1.0), 1.0 - out, 0.0)
        headroom_total = float(headroom.sum())
        if headroom_total <= tol:
            # Cannot redistribute — every non-NaN hour is already saturated.
            # Target is unreachable from this synthetic distribution.
            diag['mean_unreachable'] = True
            break
        if excess > headroom_total + tol:
            # Even filling all unsaturated hours to 1.0 cannot absorb the
            # excess. We will fall short of the target on this pass and
            # subsequent iterations will see no further excess (everything
            # is at 1.0). Mark unreachable and let the loop exit naturally.
            diag['mean_unreachable'] = True
        # Redistribute proportionally to headroom.
        scale = excess / headroom_total
        out = np.where(nan_mask, out, out + headroom * scale)

    # Final safety clip.
    out = np.where(nan_mask, out, np.clip(out, 0.0, 1.0))
    finite_out = out[~nan_mask]
    diag['fraction_at_cap'] = float(np.mean(finite_out >= 1.0 - 1e-9))
    diag['final_max'] = float(np.nanmax(out))
    diag['residual_mean_error'] = float(np.nanmean(out) - target_mean)
    return out, diag


def calibrate_capacity_factors(
    cf_df: pd.DataFrame,
    observed_cf: Dict[str, float],
    rename_map: Dict[str, str] = None,
    mode: str = 'cap_redistribute',
    multiplier_warn_threshold: float = CF_CALIBRATION_MULTIPLIER_WARN_THRESHOLD,
) -> pd.DataFrame:
    """
    Scale simulated capacity factor time series to match observed average values.

    Parameters
    ----------
    cf_df : pandas.DataFrame
        DataFrame containing simulated capacity factor time series.  Columns
        should include technology names (e.g. 'solar_cf', 'wind_cf').
    observed_cf : dict
        Mapping from technology names (matching the keys used in
        ``rename_map`` if provided) to observed average capacity factors.
        These values are typically derived from annual generation and
        capacity statistics (e.g. Ember data).
    rename_map : dict, optional
        Optional mapping from the keys in ``observed_cf`` to the column
        names in ``cf_df``.
    mode : {'cap_redistribute', 'multiplicative'}, default 'cap_redistribute'
        Calibration method.

        * ``'cap_redistribute'`` (default): apply the multiplicative scale,
          clip values that exceed 1.0, then redistribute the clipped energy
          to unsaturated hours so the annual mean still equals the target.
          Bounded by construction (every output is in [0, 1]).
        * ``'multiplicative'``: legacy behavior — pure scalar multiplication.
          Can produce capacity factor values > 1.0 when the implied
          multiplier is large (e.g., when observed annual mean is much
          higher than the synthetic mean). Retained only for backward
          compatibility / diff comparison with prior runs.
    multiplier_warn_threshold : float, default 1.5
        When the implied multiplier ``observed_mean / synthetic_mean``
        exceeds this value, emit a ``UserWarning`` recommending an upstream
        physics check (hub height, roughness length, power-curve
        assumptions). The warning fires regardless of ``mode`` because a
        large multiplier indicates a synthetic-shape mismatch that the
        calibration step is masking.

    Returns
    -------
    pandas.DataFrame
        Scaled capacity factor time series. ``df.attrs['calibration_diagnostics']``
        holds a ``{column_name: diag_dict}`` map describing what the
        calibration did per column (initial multiplier, iterations,
        fraction at cap, residual mean error, etc.). Use ``build_run_metrics``
        to surface these into the per-run metrics CSV.

    Notes
    -----
    See ``_cap_and_redistribute_cf`` for the full algorithm in the bounded
    mode. The 'multiplicative' mode is equivalent to the original behavior
    of this function before the cap-and-redistribute fix.
    """
    if mode not in CF_CALIBRATION_MODES:
        raise ValueError(
            f"Unknown calibration mode {mode!r}; expected one of "
            f"{CF_CALIBRATION_MODES}."
        )
    df_scaled = cf_df.copy()
    mapping = rename_map or {k: k for k in observed_cf}
    diagnostics: Dict[str, Dict[str, Any]] = {}

    for obs_key, obs_value in observed_cf.items():
        col = mapping.get(obs_key)
        if col is None or col not in df_scaled.columns:
            continue
        column = pd.to_numeric(df_scaled[col], errors='coerce')
        sim_mean = float(column.mean())

        if not np.isfinite(sim_mean) or sim_mean <= 0:
            # No information to calibrate against; leave the column unchanged
            # so downstream callers see the same series as today.
            diagnostics[col] = {
                'mode': mode,
                'initial_mean': sim_mean,
                'target_mean': float(obs_value) if obs_value is not None else float('nan'),
                'initial_multiplier': float('nan'),
                'iterations': 0,
                'fraction_at_cap': float('nan'),
                'final_max': float(column.max()) if column.notna().any() else float('nan'),
                'residual_mean_error': float('nan'),
                'mean_unreachable': False,
            }
            continue

        multiplier = float(obs_value) / sim_mean
        if multiplier > multiplier_warn_threshold:
            import warnings
            warnings.warn(
                f"Capacity factor calibration for {col!r} requires a multiplier of "
                f"{multiplier:.2f}× (synthetic mean {sim_mean:.4f} vs observed "
                f"{obs_value:.4f}). This is a sign the synthetic shape needs upstream "
                "tuning (hub_height, roughness_length, power-curve parameters, or the "
                "underlying renewables.ninja weather product). The cap-and-redistribute "
                "mode will keep values in [0, 1] but cannot fix the shape mismatch. "
                "See HANDOFF.md → 'Weather Data Improvements' for context.",
                stacklevel=2,
            )

        if mode == 'cap_redistribute':
            new_values, diag = _cap_and_redistribute_cf(column.to_numpy(), float(obs_value))
            df_scaled[col] = new_values
        else:  # 'multiplicative' — legacy
            new_values = column.to_numpy() * multiplier
            df_scaled[col] = new_values
            finite = new_values[~np.isnan(new_values)]
            diag = {
                'mode': 'multiplicative',
                'initial_mean': sim_mean,
                'target_mean': float(obs_value),
                'initial_multiplier': multiplier,
                'iterations': 1,
                'fraction_at_cap': float(np.mean(finite >= 1.0 - 1e-9)) if finite.size else float('nan'),
                'final_max': float(np.nanmax(new_values)),
                'residual_mean_error': float(np.nanmean(new_values) - float(obs_value)),
                'mean_unreachable': False,
            }
        diagnostics[col] = diag

    df_scaled.attrs['calibration_diagnostics'] = diagnostics
    return df_scaled


def calibrate_wind_cf_speed_rescale(
    weather: pd.DataFrame,
    target_mean: float,
    wind_speed_col: str = 'wind_speed',
    ref_height: float = 2.0,
    hub_height: float = 100.0,
    roughness_length: float = 0.03,
    k_bounds: Tuple[float, float] = (0.25, 8.0),
    tol: float = 1e-7,
    max_iter: int = 80,
) -> Tuple[pd.Series, Dict[str, Any]]:
    """Calibrate wind CF in WIND-SPEED space instead of CF space.

    Solves for a scalar ``k`` such that
    ``mean(power_curve(k * v_hub)) == target_mean`` and returns the wind CF
    series computed from the rescaled speeds. Because the calibration acts on
    the speed distribution *before* the power curve:

      * output is bounded to [0, 1] by construction (the power curve is);
      * the shape distortion is physical — calm hours stay near zero and the
        ramp region stretches through the cubic power curve — rather than the
        linear stretch of 'multiplicative' or the hour-pinning of
        'cap_redistribute';
      * ``k`` directly compensates the two dominant low-biases of a national
        area-averaged wind-speed series (site-selection bias and
        power-curve-of-the-mean averaging), which act in speed space.

    See HANDOFF.md → "Weather Data Improvements" for the bias discussion.

    Parameters mirror ``compute_capacity_factors_from_weather`` (the live
    pipeline uses ref_height=2.0 for renewables.ninja files). ``k_bounds``
    brackets the bisection; the mean CF is monotonically increasing in ``k``
    over any realistic range.

    Returns (calibrated_series, diagnostics_dict). Diagnostics use the same
    keys the other calibration modes emit (so build_run_metrics and the
    status printer pick them up), plus ``speed_scale_k``.
    """
    v_ref = pd.to_numeric(weather[wind_speed_col], errors='coerce')

    def _cf_for_k(k: float) -> pd.Series:
        scaled = weather[[wind_speed_col]].copy()
        scaled[wind_speed_col] = v_ref * k
        return compute_wind_capacity_factor_from_weather(
            scaled,
            wind_speed_col=wind_speed_col,
            ref_height=ref_height,
            hub_height=hub_height,
            roughness_length=roughness_length,
        )

    base = _cf_for_k(1.0)
    initial_mean = float(base.mean())
    target = float(target_mean)

    def _diag(series: pd.Series, k: float, iterations: int, unreachable: bool) -> Dict[str, Any]:
        vals = pd.to_numeric(series, errors='coerce').to_numpy()
        finite = vals[~np.isnan(vals)]
        return {
            'mode': 'speed_rescale',
            'initial_mean': initial_mean,
            'target_mean': target,
            'initial_multiplier': (target / initial_mean) if initial_mean > 0 else float('nan'),
            'speed_scale_k': float(k),
            'iterations': iterations,
            'fraction_at_cap': float(np.mean(finite >= 1.0 - 1e-6)) if finite.size else float('nan'),
            'final_max': float(np.nanmax(vals)) if finite.size else float('nan'),
            'residual_mean_error': float(np.nanmean(vals) - target),
            'mean_unreachable': unreachable,
        }

    if not np.isfinite(target) or target <= 0 or not np.isfinite(initial_mean):
        return base, _diag(base, 1.0, 0, False)

    # mean CF is NOT monotone in k over the full bracket: at extreme k the
    # rescaled speeds blow past the turbine cut-out and the mean collapses
    # (empirically for China 2018 the mean peaks near k≈4 and falls after).
    # So: coarse log-spaced grid to bracket the FIRST upward crossing of the
    # target, then bisect inside that bracket. If no grid point reaches the
    # target, return the max-mean series and flag unreachable.
    lo, hi = float(k_bounds[0]), float(k_bounds[1])
    grid = np.geomspace(lo, hi, 33)
    f_grid = [float(_cf_for_k(k).mean()) for k in grid]
    iterations = len(grid)
    cross = None
    for i in range(1, len(grid)):
        if f_grid[i - 1] < target <= f_grid[i]:
            cross = (grid[i - 1], grid[i])
            break
    if f_grid[0] >= target:
        # Synthetic already above target at the lower bound; clamp there.
        return _cf_for_k(lo), _diag(_cf_for_k(lo), lo, iterations, True)
    if cross is None:
        import warnings
        k_best = float(grid[int(np.argmax(f_grid))])
        warnings.warn(
            f"speed_rescale: wind CF target {target:.4f} unreachable for any "
            f"speed scale in [{lo}, {hi}] (max mean {max(f_grid):.4f} at "
            f"k={k_best:.2f}). Returning the max-mean series — the synthetic "
            "wind-speed product needs upstream work (see HANDOFF.md → "
            "'Weather Data Improvements').",
            stacklevel=2,
        )
        series = _cf_for_k(k_best)
        return series, _diag(series, k_best, iterations, True)

    b_lo, b_hi = cross
    for _ in range(max_iter):
        iterations += 1
        mid = 0.5 * (b_lo + b_hi)
        f_mid = float(_cf_for_k(mid).mean())
        if abs(f_mid - target) < tol:
            b_lo = b_hi = mid
            break
        if f_mid < target:
            b_lo = mid
        else:
            b_hi = mid
    k = 0.5 * (b_lo + b_hi)
    series = _cf_for_k(k)
    if k > 2.0:
        import warnings
        warnings.warn(
            f"speed_rescale: wind-speed scale k={k:.2f} exceeds 2.0. The "
            "calibration is bounded and shape-preserving, but a scale this "
            "large means the underlying area-averaged wind-speed product is "
            "far from fleet conditions — consider per-preset hub height / "
            "power-curve updates or a fleet-weighted weather product "
            "(HANDOFF.md → 'Weather Data Improvements').",
            stacklevel=2,
        )
    return series, _diag(series, k, iterations, False)


def _align_modeled_and_real_series(
    modeled_series: pd.Series,
    real_series: pd.Series,
) -> pd.DataFrame:
    """Align modeled and observed series on a common timezone-aware hourly index."""
    modeled = pd.Series(modeled_series).copy()
    real = pd.Series(real_series).copy()
    if modeled.index.has_duplicates:
        modeled = modeled.groupby(modeled.index).mean()
    if real.index.has_duplicates:
        real = real.groupby(real.index).mean()
    if modeled.index.tz is None and real.index.tz is not None:
        modeled.index = modeled.index.tz_localize(real.index.tz)
    elif modeled.index.tz is not None and real.index.tz is not None and modeled.index.tz != real.index.tz:
        modeled.index = modeled.index.tz_convert(real.index.tz)
    aligned = pd.concat(
        [modeled.rename('modeled'), real.rename('observed')],
        axis=1,
        join='inner',
    ).dropna()
    return aligned


def _rmse(left: pd.Series, right: pd.Series) -> float:
    """Compute RMSE between two aligned numeric series."""
    if len(left) == 0:
        return float('nan')
    diff = pd.to_numeric(left, errors='coerce') - pd.to_numeric(right, errors='coerce')
    return float(np.sqrt(np.nanmean(np.square(diff))))


def _nrmse(rmse: float, observed: pd.Series) -> float:
    """Compute NRMSE normalized by the mean of the observed series."""
    observed_numeric = pd.to_numeric(observed, errors='coerce')
    denominator = float(np.nanmean(np.abs(observed_numeric)))
    if np.isnan(rmse) or denominator <= 0 or np.isnan(denominator):
        return float('nan')
    return float(rmse / denominator)


def _nrmse_std(rmse: float, observed: pd.Series) -> float:
    """Compute NRMSE normalized by the standard deviation of the observed series."""
    observed_numeric = pd.to_numeric(observed, errors='coerce')
    denominator = float(np.nanstd(observed_numeric))
    if np.isnan(rmse) or denominator <= 0 or np.isnan(denominator):
        return float('nan')
    return float(rmse / denominator)


def build_run_metrics(
    country: str,
    year: int,
    synthetic_df: pd.DataFrame,
    scaled_df: pd.DataFrame,
    calibrated_df: pd.DataFrame,
    real_demand: pd.Series,
    cf_raw: pd.DataFrame,
    cf_scaled: pd.DataFrame,
    observed_cf: Dict[str, float],
) -> pd.DataFrame:
    """Build a compact metrics table for a country run, including RMSE values."""
    metrics: list[Dict[str, Any]] = []

    demand_stages = {
        'raw_hourly': synthetic_df['load'],
        'scaled_hourly': scaled_df['load'],
        'seasonally_calibrated_hourly': calibrated_df['load'],
    }
    for stage, series in demand_stages.items():
        aligned = _align_modeled_and_real_series(series, real_demand)
        hourly_rmse = _rmse(aligned['modeled'], aligned['observed'])
        metrics.append({
            'country': country,
            'year': year,
            'metric_group': 'demand',
            'series': 'load',
            'stage': stage,
            'rmse': hourly_rmse,
            'nrmse': _nrmse(hourly_rmse, aligned['observed']),
            'normalization_basis': 'mean_observed',
            'n_points': len(aligned),
        })

        if not aligned.empty:
            modeled_monthly_mean = aligned['modeled'].groupby(aligned.index.month).mean()
            observed_monthly_mean = aligned['observed'].groupby(aligned.index.month).mean()
            monthly_mean = pd.concat(
                [modeled_monthly_mean.rename('modeled'), observed_monthly_mean.rename('observed')],
                axis=1,
                join='inner',
            ).dropna()
            monthly_mean_rmse = _rmse(monthly_mean['modeled'], monthly_mean['observed'])
            metrics.append({
                'country': country,
                'year': year,
                'metric_group': 'demand',
                'series': 'load',
                'stage': stage.replace('hourly', 'monthly_mean'),
                'rmse': monthly_mean_rmse,
                'nrmse': _nrmse(monthly_mean_rmse, monthly_mean['observed']),
                'normalization_basis': 'mean_observed',
                'n_points': len(monthly_mean),
            })

            modeled_monthly_peak = aligned['modeled'].groupby(aligned.index.month).max()
            observed_monthly_peak = aligned['observed'].groupby(aligned.index.month).max()
            monthly_peak = pd.concat(
                [modeled_monthly_peak.rename('modeled'), observed_monthly_peak.rename('observed')],
                axis=1,
                join='inner',
            ).dropna()
            monthly_peak_rmse = _rmse(monthly_peak['modeled'], monthly_peak['observed'])
            metrics.append({
                'country': country,
                'year': year,
                'metric_group': 'demand',
                'series': 'load',
                'stage': stage.replace('hourly', 'monthly_peak'),
                'rmse': monthly_peak_rmse,
                'nrmse': _nrmse(monthly_peak_rmse, monthly_peak['observed']),
                'normalization_basis': 'mean_observed',
                'n_points': len(monthly_peak),
            })

    for source_name, df_source in (('raw', cf_raw), ('calibrated', cf_scaled)):
        for observed_key, observed_value in observed_cf.items():
            column_name = {'Solar': 'solar_cf', 'Wind': 'wind_cf'}.get(observed_key, observed_key)
            if column_name not in df_source.columns:
                continue
            simulated_mean = float(pd.to_numeric(df_source[column_name], errors='coerce').mean())
            rmse = float(np.sqrt((simulated_mean - observed_value) ** 2))
            metrics.append({
                'country': country,
                'year': year,
                'metric_group': 'capacity_factor',
                'series': column_name,
                'stage': f'{source_name}_annual_mean',
                'rmse': rmse,
                'nrmse': float(rmse / abs(observed_value)) if observed_value not in [0, 0.0] else float('nan'),
                'normalization_basis': 'mean_observed',
                'n_points': len(df_source[column_name]),
            })

    # Calibration diagnostics — one row per (column, diagnostic_field) so they
    # land in the same CSV alongside the calibration RMSE rows above. These are
    # informational rather than error metrics; the 'rmse' / 'nrmse' columns
    # carry the diagnostic value, and 'normalization_basis' identifies what
    # the value represents.
    cal_diag = getattr(cf_scaled, 'attrs', {}).get('calibration_diagnostics', {})
    diagnostic_fields = (
        'mode',
        'initial_multiplier',
        'speed_scale_k',          # speed_rescale mode only
        'iterations',
        'fraction_at_cap',
        'final_max',
        'residual_mean_error',
        'mean_unreachable',
    )
    for column_name, diag in cal_diag.items():
        for field in diagnostic_fields:
            if field not in diag:
                continue
            value = diag[field]
            # Coerce non-numeric (mode, mean_unreachable) into a numeric-safe
            # form so the metrics CSV stays one consistent dtype.
            if isinstance(value, bool):
                numeric = float(value)
            elif isinstance(value, str):
                numeric = float('nan')
            else:
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    numeric = float('nan')
            metrics.append({
                'country': country,
                'year': year,
                'metric_group': 'capacity_factor_calibration',
                'series': column_name,
                'stage': field if not isinstance(value, str) else f'{field}={value}',
                'rmse': numeric,
                'nrmse': float('nan'),
                'normalization_basis': 'calibration_diagnostic',
                'n_points': int(len(cf_scaled[column_name])) if column_name in cf_scaled.columns else 0,
            })

    return pd.DataFrame(metrics)


def build_clustering_metrics(
    country: str,
    year: int,
    df: pd.DataFrame,
    labels: pd.Series,
    timestamps: pd.Series,
    columns: Iterable[str],
    representative_dates: Optional[Dict[int, pd.Timestamp]] = None,
) -> pd.DataFrame:
    """Measure how well representative-day clustering reconstructs hourly series."""
    metrics: list[Dict[str, Any]] = []
    if df.empty:
        return pd.DataFrame(metrics)

    hours = pd.to_datetime(timestamps).dt.hour
    work = df[list(columns)].copy()
    work['timeslice'] = labels.values
    work['date'] = pd.to_datetime(timestamps).dt.floor('D').values
    work['hour_of_day'] = hours.values

    if representative_dates:
        profiles = []
        date_keys = pd.to_datetime(work['date']).dt.strftime('%Y-%m-%d')
        for timeslice, rep_date in representative_dates.items():
            rep_key = pd.Timestamp(rep_date).strftime('%Y-%m-%d')
            rep_profile = work.loc[date_keys == rep_key, ['hour_of_day', *columns]].copy()
            if rep_profile.empty:
                continue
            rep_profile['timeslice'] = int(timeslice)
            profiles.append(rep_profile)
        if not profiles:
            raise ValueError("Representative-day clustering profiles could not be constructed.")
        profile_values = pd.concat(profiles, ignore_index=True).groupby(['timeslice', 'hour_of_day'])[list(columns)].first()
    else:
        profile_values = work.groupby(['timeslice', 'hour_of_day'])[list(columns)].mean()
    lookup_index = pd.MultiIndex.from_arrays([labels.values, hours.values], names=['timeslice', 'hour_of_day'])
    reconstructed = profile_values.loc[lookup_index].reset_index(drop=True)
    reconstructed.index = df.index

    for column in columns:
        original = pd.to_numeric(df[column], errors='coerce')
        rebuilt = pd.to_numeric(reconstructed[column], errors='coerce')
        valid = pd.DataFrame({'original': original, 'reconstructed': rebuilt}).dropna()
        rmse = _rmse(valid['reconstructed'], valid['original'])
        metrics.append({
            'country': country,
            'year': year,
            'metric_group': 'clustering',
            'series': column,
            'stage': 'representative_day_full_year_reconstruction',
            'rmse': rmse,
            'nrmse': _nrmse_std(rmse, valid['original']),
            'normalization_basis': 'std_observed',
            'n_points': len(valid),
        })

    return pd.DataFrame(metrics)


def compare_pinned_unpinned_clustering(
    country: str,
    year: int,
    df: pd.DataFrame,
    load_col: str,
    gen_cols: Iterable[str],
    n_clusters: int,
    feature_weight_mode: str = 'netload_focus',
    search_seeds: Optional[Iterable[int]] = None,
) -> pd.DataFrame:
    """Compare pinned vs unpinned day clustering on full-year net-load reconstruction."""
    timestamps = _extract_timestamps(df)
    net = compute_net_load(df, load_col=load_col, gen_cols=gen_cols)
    rows: list[Dict[str, Any]] = []
    for pin_extremes in (True, False):
        labels, _, _, representative_dates = cluster_timeslices(
            net,
            timestamps=timestamps,
            n_clusters=n_clusters,
            feature_weight_mode=feature_weight_mode,
            search_seeds=search_seeds,
            pin_extremes=pin_extremes,
        )
        metrics = build_clustering_metrics(
            country=country,
            year=year,
            df=pd.DataFrame({'net_load': net}, index=df.index),
            labels=labels,
            timestamps=timestamps,
            columns=['net_load'],
            representative_dates=representative_dates,
        )
        if metrics.empty:
            continue
        metric_row = metrics.iloc[0].to_dict()
        metric_row['metric_group'] = 'clustering_comparison'
        metric_row['stage'] = 'pinned_full_year_reconstruction' if pin_extremes else 'unpinned_full_year_reconstruction'
        rows.append(metric_row)
    return pd.DataFrame(rows)


def write_metrics_reports(metrics_df: pd.DataFrame, output_path: Optional[str]) -> None:
    """Write per-run metrics and refresh the global metrics summary CSV."""
    if output_path is None or metrics_df is None or metrics_df.empty:
        return

    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    root, _ = os.path.splitext(output_path)
    metrics_path = f'{root}_Metrics.csv'
    metrics_df.to_csv(metrics_path, index=False)

    summary = metrics_df[
        ['country', 'year', 'metric_group', 'series', 'stage', 'rmse', 'nrmse', 'normalization_basis']
    ]
    if os.path.exists(GLOBAL_METRICS_SUMMARY_CSV):
        existing = pd.read_csv(GLOBAL_METRICS_SUMMARY_CSV)
        combined = pd.concat([existing, summary], ignore_index=True)
        combined = combined.drop_duplicates(
            subset=['country', 'year', 'metric_group', 'series', 'stage'],
            keep='last',
        )
    else:
        combined = summary
    combined.to_csv(GLOBAL_METRICS_SUMMARY_CSV, index=False)


def make_cluster_diagnostic_plots(
    df: pd.DataFrame,
    labels: pd.Series,
    timeslice_metadata: pd.DataFrame,
    representative_dates: Dict[int, pd.Timestamp],
    output_dir: str,
    country: str = '',
) -> "list[str]":
    """
    Write per-cluster diagnostic PNG plots for visual inspection of how
    clustering grouped the year.

    For each of the 6 timeslices, four plots are written:

        <Label>_net_load.png        — net load (MW)
        <Label>_load.png            — total load (MW)
        <Label>_solar_cf.png        — solar capacity factor (0–1), calibrated
        <Label>_wind_cf.png         — wind capacity factor (0–1), calibrated

    Every plot shows:
        * one thin grey line per day in the cluster (low alpha)
        * a shaded band between the 25th and 75th percentiles, by hour
        * a dashed steelblue line for the cluster mean profile

    On the ``net_load`` plot only, an additional thick red line marks
    the cluster's representative day — the same date the rest of the
    pipeline uses as a stand-in for the whole timeslice when populating
    SHELF/SYSHECF. For pinned timeslices, the rep day is the literal
    summer/winter peak day rather than a centroid-nearest day, and the
    legend says so.

    The function imports matplotlib lazily so a missing install just
    skips the plotting step with a warning instead of crashing the run.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly DataFrame with columns ``net_load``, ``load``, ``solar_cf``,
        ``wind_cf``. Index must be hourly (any timezone, but typically the
        country's local TZ after the pipeline's tz_convert step).
    labels : pandas.Series
        Per-hour timeslice ID, same length and order as ``df``.
    timeslice_metadata : pandas.DataFrame
        Output of ``build_timeslice_metadata`` — must contain
        ``is_pinned_summer`` and ``is_pinned_winter`` columns indexed by
        the same timeslice IDs used in ``labels``.
    representative_dates : dict[int, pandas.Timestamp]
        Mapping from timeslice ID to the representative day's date.
    output_dir : str
        Directory to write the PNG files into. Created if missing.
    country : str, optional
        Country / region label inserted into each plot's title.

    Returns
    -------
    list of str
        Absolute paths of the PNG files written. Empty if matplotlib is
        not available or the inputs are empty.
    """
    # Lazy import so a missing install isn't a hard fail.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        import warnings
        warnings.warn(
            "matplotlib is not installed; cluster diagnostic plots will be "
            "skipped. Install with `pip install matplotlib`."
        )
        return []

    if df is None or df.empty or labels is None or len(labels) == 0:
        return []

    required_cols = ['net_load', 'load', 'solar_cf', 'wind_cf']
    if any(col not in df.columns for col in required_cols):
        return []

    os.makedirs(output_dir, exist_ok=True)

    # Build a tidy work frame: date + hour + variable values + label.
    work = df[required_cols].copy()
    work['__date'] = pd.to_datetime(work.index).floor('D')
    work['__hour'] = pd.to_datetime(work.index).hour
    work['__label'] = labels.values

    # Pretty cluster labels (e.g. 'Summer Peak') and pinned-flag lookup.
    try:
        eps_label_map = build_eps_timeslice_label_map(timeslice_metadata)
    except Exception:
        # Fall back to numeric labels if EPS labeling cannot be built.
        eps_label_map = pd.Series({i: f'Timeslice_{int(i)}' for i in pd.unique(labels)})

    def _is_pinned(ts_id: int) -> bool:
        if timeslice_metadata is None or timeslice_metadata.empty:
            return False
        if ts_id not in timeslice_metadata.index:
            return False
        return bool(
            timeslice_metadata.loc[ts_id].get('is_pinned_summer', False)
            or timeslice_metadata.loc[ts_id].get('is_pinned_winter', False)
        )

    # Variable spec: (column, y-axis label, filename suffix). These are the
    # calibrated / model-input series (one line per synthetic-year day). Total
    # load is plotted in absolute MW (not normalized) for direct readability.
    variables = [
        ('net_load',  'Net load (MW)',                        'net_load'),
        ('load',      'Total load (MW)',                      'load'),
        ('solar_cf',  'Solar capacity factor (calibrated)',   'solar_cf'),
        ('wind_cf',   'Wind capacity factor (calibrated)',    'wind_cf'),
    ]

    paths_written: "list[str]" = []

    def _render_variable(
        pivot: pd.DataFrame, ts_label: str, ts_label_safe: str, n_days: int,
        ylabel: str, suffix: str, rep_date=None, is_pinned=False, overlay_rep=False,
    ) -> None:
        """Draw one per-cluster variable plot and append its path."""
        if pivot is None or pivot.empty:
            return
        fig, ax = plt.subplots(figsize=(8.0, 4.5))

        # Per-day curves (low alpha) — every day in the cluster as a thin grey line.
        for _, day_row in pivot.iterrows():
            ax.plot(range(24), day_row.values, color='0.55', linewidth=0.6, alpha=0.35)

        # 25–75th percentile shaded band.
        p25 = pivot.quantile(0.25, axis=0)
        p75 = pivot.quantile(0.75, axis=0)
        ax.fill_between(
            range(24), p25.values, p75.values,
            color='steelblue', alpha=0.18, label='25–75th pct',
        )

        # Cluster mean (dashed).
        cluster_mean = pivot.mean(axis=0)
        ax.plot(
            range(24), cluster_mean.values,
            color='steelblue', linestyle='--', linewidth=1.5, label='cluster mean',
        )

        # Rep-day overlay (red) — only requested on net_load.
        if overlay_rep and rep_date is not None and rep_date in pivot.index:
            rep_values = pivot.loc[rep_date].values
            rep_label_parts = [f"rep day {rep_date.date()}"]
            rep_label_parts.append("(pinned)" if is_pinned else "(centroid-nearest)")
            ax.plot(
                range(24), rep_values,
                color='firebrick', linewidth=2.0, label=" ".join(rep_label_parts),
            )

        country_suffix = f" — {country}" if country else ""
        ax.set_title(f"{ts_label} ({n_days} days){country_suffix}\n{ylabel}")
        ax.set_xlabel('Hour of day (local)')
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 23)
        ax.set_xticks(range(0, 24, 2))
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize='small', framealpha=0.85)
        fig.tight_layout()

        out_path = os.path.join(output_dir, f'{ts_label_safe}_{suffix}.png')
        fig.savefig(out_path, dpi=110)
        plt.close(fig)
        paths_written.append(out_path)

    for ts_id in sorted(pd.unique(labels.dropna())):
        ts_id = int(ts_id)
        ts_rows = work[work['__label'] == ts_id]
        if ts_rows.empty:
            continue
        ts_label = str(eps_label_map.get(ts_id, f'Timeslice_{ts_id}'))
        ts_label_safe = ts_label.replace(' ', '_').replace('/', '_')
        n_days = ts_rows['__date'].nunique()
        is_pinned = _is_pinned(ts_id)
        rep_date = None
        if representative_dates and ts_id in representative_dates:
            rep_date = pd.Timestamp(representative_dates[ts_id]).floor('D')

        # Calibrated / model-input variables.
        for col, ylabel, suffix in variables:
            if col not in ts_rows.columns:
                continue
            pivot = ts_rows.pivot_table(
                index='__date', columns='__hour', values=col, aggfunc='first',
            ).reindex(columns=range(24))
            _render_variable(
                pivot, ts_label, ts_label_safe, n_days, ylabel, suffix,
                rep_date=rep_date, is_pinned=is_pinned, overlay_rep=(col == 'net_load'),
            )

    return paths_written


# Canonical Zapata end-use categories (the demand-shape basis columns).
ZAPATA_END_USE_CATEGORIES = [
    'residential_cooling', 'residential_heating', 'residential_lighting',
    'residential_waterheating', 'residential_other',
    'service_cooling', 'service_heating', 'service_waterheating', 'service_other',
    'industry', 'transport',
]


def make_enduse_lf_plots(
    df: pd.DataFrame,
    labels: pd.Series,
    timeslice_metadata: pd.DataFrame,
    output_dir: str,
    country: str = '',
) -> "list[str]":
    """Plot the SHELF load factors of each Zapata end-use category, faceted
    per timeslice.

    One PNG per timeslice (``LF_by_timeslice_<Slice>.png``) — Winter, Spring,
    Summer, Fall, Summer Peak, Winter Peak. Each figure is a grid of panels,
    one per Zapata end-use category. Within a panel, the x-axis is hour of day
    (0–23) and, in that timeslice's color:

        * thin dotted lines — every day assigned to this timeslice, as its
          own hourly load-factor profile (LF = day demand / category annual);
        * one thick solid line — the MEAN load factor over all those days
          (the average day-shape of the timeslice, not the representative day).

    The y-axis is shared across all panels in a figure so category peakiness is
    comparable. A category with zero annual demand (e.g. a calibration
    zero-flip) shows as a flat zero panel.

    matplotlib is imported lazily so a missing install just skips the plots.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
    except ImportError:
        import warnings
        warnings.warn(
            "matplotlib is not installed; end-use LF plots will be skipped."
        )
        return []

    if df is None or df.empty or labels is None or len(labels) == 0:
        return []

    cats = [c for c in ZAPATA_END_USE_CATEGORIES if c in df.columns]
    if not cats:
        return []

    os.makedirs(output_dir, exist_ok=True)

    try:
        eps_label_map = build_eps_timeslice_label_map(timeslice_metadata)
    except Exception:
        eps_label_map = pd.Series(
            {int(i): f'Timeslice_{int(i)}' for i in pd.unique(labels)}
        )

    slice_order = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']
    slice_color = {
        'Winter': '#1f77b4', 'Spring': '#2ca02c', 'Summer': '#ff7f0e',
        'Fall': '#8c564b', 'Summer Peak': '#d62728', 'Winter Peak': '#9467bd',
    }

    idx = pd.to_datetime(df.index)
    day = idx.floor('D')
    hour = idx.hour

    # Slice name per calendar day (all hours of a day share one timeslice id).
    ts_per_hour = pd.Series(labels).reset_index(drop=True).to_numpy()
    day_ts = pd.DataFrame({'day': day, 'ts': ts_per_hour}).groupby('day')['ts'].first()
    day_slice = day_ts.map(
        lambda t: str(eps_label_map.get(int(t), f'Timeslice_{int(t)}'))
    )

    # Per-category day x hour load-factor matrices (computed once, reused per figure).
    lf_wide: Dict[str, pd.DataFrame] = {}
    for cat in cats:
        tmp = pd.DataFrame({'day': day, 'hour': hour,
                            'v': pd.to_numeric(df[cat], errors='coerce').to_numpy()})
        wide = tmp.pivot_table(index='day', columns='hour', values='v',
                               aggfunc='first').reindex(columns=range(24))
        annual = float(np.nansum(tmp['v'].to_numpy()))
        lf_wide[cat] = wide / annual if annual > 0 else wide * 0.0

    ncols = 3
    nrows = -(-len(cats) // ncols)  # ceil
    paths_written: "list[str]" = []

    for sl in slice_order:
        days_s = day_slice.index[day_slice == sl]
        if len(days_s) == 0:
            continue
        color = slice_color.get(sl, '0.3')

        # Shared y-limit across this figure's panels (include per-day spread).
        ymax = 0.0
        for cat in cats:
            sub = lf_wide[cat].reindex(index=days_s)
            if sub.size:
                m = np.nanmax(sub.to_numpy())
                if np.isfinite(m):
                    ymax = max(ymax, float(m))
        if ymax <= 0:
            ymax = 1.0

        fig, axes = plt.subplots(nrows, ncols, figsize=(4.0 * ncols, 2.6 * nrows),
                                 sharex=True, sharey=True)
        axes = np.atleast_1d(axes).flatten()
        for i, cat in enumerate(cats):
            ax = axes[i]
            sub = lf_wide[cat].reindex(index=days_s)
            for _, row_vals in sub.iterrows():
                ax.plot(range(24), row_vals.to_numpy(), color=color,
                        linewidth=0.5, alpha=0.25, linestyle=':')
            ax.plot(range(24), sub.mean(axis=0).to_numpy(), color=color,
                    linewidth=2.4, solid_capstyle='round')
            ax.set_title(cat, fontsize=9)
            ax.set_xlim(0, 23)
            ax.set_xticks(range(0, 24, 6))
            ax.grid(True, alpha=0.3)
        for j in range(len(cats), len(axes)):
            axes[j].axis('off')
        axes[0].set_ylim(0, ymax * 1.05)  # sharey propagates to all panels

        country_suffix = f" — {country}" if country else ""
        fig.suptitle(f"{sl} — SHELF load factors by end use{country_suffix}"
                     f"   ({len(days_s)} days)\n"
                     "thin dotted = each assigned day; thick solid = timeslice mean",
                     fontsize=12)
        try:
            fig.supxlabel('Hour of day (local)')
            fig.supylabel('Load factor (share of annual demand)')
        except AttributeError:
            axes[0].set_ylabel('Load factor (share of annual demand)')
        legend_handles = [
            Line2D([0], [0], color=color, linewidth=2.4, label='timeslice mean'),
            Line2D([0], [0], color=color, linewidth=0.8, linestyle=':', label='individual day'),
        ]
        fig.legend(handles=legend_handles, loc='lower right', fontsize='small',
                   framealpha=0.85)
        fig.tight_layout(rect=(0, 0, 1, 0.96))

        sl_safe = sl.replace(' ', '_')
        out_path = os.path.join(output_dir, f'LF_by_timeslice_{sl_safe}.png')
        fig.savefig(out_path, dpi=110)
        plt.close(fig)
        paths_written.append(out_path)

    return paths_written


def make_calibration_overview_plot(
    df_calibrated: pd.DataFrame,
    real_demand: pd.Series,
    output_path: str,
    country: str = '',
) -> Optional[str]:
    """
    One full-year overview plot showing the calibration result at daily-mean
    resolution:

      * **Stacked area** of the four sector totals (residential, service,
        industry, transport) in the calibrated synthetic year — this is
        what the rest of the pipeline consumes.
      * **Line** for observed DemandCast demand, day-of-year-averaged
        across the calibration window so a single curve overlays cleanly
        on top of the stacked area.
      * **Line** for total calibrated load (= top of the stacked area).
        Slightly offset visually so it remains distinguishable; if it
        diverges from the stack top there's a sum bug somewhere.

    Returns the path written, or ``None`` if matplotlib is unavailable
    or the inputs are insufficient.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        import warnings
        warnings.warn(
            "matplotlib is not installed; calibration overview plot will be "
            "skipped. Install with `pip install matplotlib`."
        )
        return None

    if df_calibrated is None or df_calibrated.empty:
        return None

    sector_cols = [
        col for col in (
            'residential_total', 'service_total', 'industry_total', 'transport_total',
        ) if col in df_calibrated.columns
    ]
    if not sector_cols:
        return None

    # Daily means for the synthetic year (one point per day of year).
    syn_daily = df_calibrated[sector_cols + (['load'] if 'load' in df_calibrated.columns else [])].copy()
    syn_daily['_doy'] = pd.to_datetime(syn_daily.index).dayofyear
    syn_daily = syn_daily.groupby('_doy').mean()

    # DemandCast: day-of-year mean across calibration years (gives one curve
    # to compare against the synthetic single-year shape).
    if real_demand is None or len(real_demand) == 0:
        dc_daily = None
    else:
        real = pd.Series(real_demand).copy()
        real_doy = pd.to_datetime(real.index).dayofyear
        dc_daily = real.groupby(real_doy).mean()

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 4.8))

    # Stacked area of sector totals (calibrated).
    sector_colors = {
        'residential_total': '#4c72b0',
        'service_total':     '#dd8452',
        'industry_total':    '#55a868',
        'transport_total':   '#c44e52',
    }
    sector_labels = {
        'residential_total': 'Residential',
        'service_total':     'Service / Commercial',
        'industry_total':    'Industry',
        'transport_total':   'Transport',
    }
    stack_arrays = [syn_daily[col].values for col in sector_cols]
    stack_colors = [sector_colors.get(col, None) for col in sector_cols]
    stack_labels = [sector_labels.get(col, col) for col in sector_cols]
    ax.stackplot(
        syn_daily.index, *stack_arrays,
        labels=stack_labels, colors=stack_colors, alpha=0.75,
    )

    # Calibrated total-load line (top of stack — sanity check).
    if 'load' in syn_daily.columns:
        ax.plot(
            syn_daily.index, syn_daily['load'].values,
            color='black', linewidth=1.2, linestyle='--',
            label='Calibrated load (synth sum)',
        )

    # DemandCast observed line.
    if dc_daily is not None and not dc_daily.empty:
        ax.plot(
            dc_daily.index, dc_daily.values,
            color='crimson', linewidth=1.6, label='DemandCast observed (DOY mean)',
        )

    country_suffix = f" — {country}" if country else ""
    ax.set_title(
        f"Calibration overview{country_suffix}\n"
        "Stacked end-uses = calibrated synthetic year; lines = observed and synthetic totals"
    )
    ax.set_xlabel('Day of year')
    ax.set_ylabel('Hourly demand (MW), daily-mean')
    ax.set_xlim(1, max(syn_daily.index.max(), 365))
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize='small', framealpha=0.85, ncol=2)
    fig.tight_layout()

    fig.savefig(output_path, dpi=110)
    plt.close(fig)
    return output_path


def print_metrics_summary(country: str, metrics_df: pd.DataFrame) -> None:
    """Print a short metrics summary for the current run."""
    if metrics_df is None or metrics_df.empty:
        return

    def _lookup(metric_group: str, series: str, stage: str, value_col: str = 'rmse') -> Optional[float]:
        match = metrics_df[
            (metrics_df['metric_group'] == metric_group)
            & (metrics_df['series'] == series)
            & (metrics_df['stage'] == stage)
        ]
        if match.empty:
            return None
        return float(match.iloc[-1][value_col])

    hourly = _lookup('demand', 'load', 'seasonally_calibrated_hourly')
    monthly_mean = _lookup('demand', 'load', 'seasonally_calibrated_monthly_mean')
    monthly_peak = _lookup('demand', 'load', 'seasonally_calibrated_monthly_peak')
    solar = _lookup('capacity_factor', 'solar_cf', 'calibrated_annual_mean')
    wind = _lookup('capacity_factor', 'wind_cf', 'calibrated_annual_mean')
    cluster_load_nrmse = _lookup('clustering', 'load', 'representative_day_full_year_reconstruction', 'nrmse')
    cluster_net_load_nrmse = _lookup('clustering', 'net_load', 'representative_day_full_year_reconstruction', 'nrmse')
    cluster_net_load_rmse = _lookup('clustering', 'net_load', 'representative_day_full_year_reconstruction', 'rmse')
    pinned_cmp = _lookup('clustering_comparison', 'net_load', 'pinned_full_year_reconstruction', 'nrmse')
    unpinned_cmp = _lookup('clustering_comparison', 'net_load', 'unpinned_full_year_reconstruction', 'nrmse')

    parts = [f"[Metrics] {country}"]
    if hourly is not None:
        parts.append(f"load hourly RMSE={hourly:,.2f}")
    if monthly_mean is not None:
        parts.append(f"monthly mean RMSE={monthly_mean:,.2f}")
    if monthly_peak is not None:
        parts.append(f"monthly peak RMSE={monthly_peak:,.2f}")
    if solar is not None:
        parts.append(f"solar CF RMSE={solar:.4f}")
    if wind is not None:
        parts.append(f"wind CF RMSE={wind:.4f}")
    if cluster_load_nrmse is not None:
        parts.append(f"year-load NRMSE={cluster_load_nrmse:.4f}")
    if cluster_net_load_rmse is not None:
        parts.append(f"year net-load RMSE={cluster_net_load_rmse:,.2f}")
    if cluster_net_load_nrmse is not None:
        parts.append(f"year net-load NRMSE={cluster_net_load_nrmse:.4f}")
    if pinned_cmp is not None and unpinned_cmp is not None:
        parts.append(f"pinned vs unpinned net-load NRMSE={pinned_cmp:.4f}/{unpinned_cmp:.4f}")
    print(' | '.join(parts))


def generate_full_pipeline_for_country(
    mendeley_dir: str,
    efs_dir: Optional[str],
    weather_dir: str,
    ember_csv_path: str,
    region_name: str,
    country_iso2: str,
    demand_country_code: str,
    year: int,
    mendeley_region_name: Optional[str] = None,
    ember_country_name: Optional[str] = None,
    last_n_years: int = 3,
    demand_shape_source: str = 'mendeley',
    efs_electrification: str = 'Reference',
    efs_technology_advancement: str = 'Moderate',
    weight: str = 'area',
    dataset: str = 'merra2',
    orientation_factor: float = 1.1,
    roughness_length: float = 0.03,
    n_clusters: int = 6,
    scenario: str = 'SSP2',
    output_path: Optional[str] = None,
    seasonal_calibration: bool = True,
    mendeley_dataset_url: str = MENDELEY_DATASET_URL,
    mendeley_headers: Optional[Dict[str, str]] = None,
    weather_headers: Optional[Dict[str, str]] = None,
    use_cache: bool = False,
    cache_dir: Optional[str] = None,
    country_timezone: Optional[str] = None,
    allow_utc_weather: bool = False,
    cf_calibration_mode: str = 'cap_redistribute',
    wind_cf_source: str = 'weather',
    wind_sites_dir: Optional[str] = None,
    wind_cf_years: Optional[int] = None,
    wind_capacity_split: Optional[Dict[str, float]] = None,
    make_plots: bool = True,
    compare_pinned_unpinned: bool = False,
    calibration_only: bool = False,
    latitude_deg: Optional[float] = None,
    calibration_method: str = 'level_seasonal',
    eps_prior_path: Optional[str] = None,
    lambda_ridge: float = 1.0,
    demand_series_csv: Optional[str] = None,
    demand_series_citation: Optional[str] = None,
    **kwargs,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Run the complete timeslice pipeline for a country using multiple data sources.

    This high‑level function orchestrates the following steps:

    1. **Load synthetic end‑use demand** from the Mendeley dataset for the
       specified year.
    2. **Retrieve and average real demand** over the most recent ``last_n_years``
       using DemandCast and calibrate the synthetic load accordingly.
    3. **Load weather data** (irradiance, temperature and wind speed) from
       Renewables.ninja files and compute hourly solar and wind capacity
       factors.  These are then calibrated to match observed annual
       capacity factors derived from Ember statistics.
    4. **Convert capacity factors to generation** using average installed
       capacity (GW) from Ember and compute net load.
    5. **Cluster hours into timeslices** using k‑means on net load and
       compute average load factors and capacity factors per slice.
    6. **Export results** to an Excel workbook matching the SYSHECF and
       SHELF formats (if ``output_path`` is provided).

    Parameters
    ----------
    mendeley_dir : str
        Directory containing the extracted Mendeley end‑use CSV files.
    weather_dir : str
        Directory containing Renewables.ninja weather CSVs.  Must include
        the files for irradiance, temperature and wind speed for the given
        country and weighting.
    ember_csv_path : str
        Path to the Ember ``yearly_full_release_long_format.csv`` file.
    region_name : str
        Region name used in the Mendeley dataset (e.g. 'South Korea').
    country_iso2 : str
        ISO‑2 country code corresponding to the weather files (e.g. 'KR').
    demand_country_code : str
        ISO Alpha‑3 code (or subdivision code) used by DemandCast to fetch
        real demand data (e.g. 'KOR' for South Korea).  This may differ
        from ``country_iso2`` due to different coding schemes.
    year : int
        Year of the synthetic data to construct.  Should correspond to a
        year within the Mendeley dataset (1971–2100).  Typically set to the
        most recent year of available data.
    last_n_years : int, default 3
        Number of most recent years to use when averaging demand and
        supply statistics.  The function will attempt to use data from
        ``year``, ``year-1`` and ``year-2`` if available.
    weight : str, default 'area'
        Weighting method for weather variables ('area' or 'pop').
    dataset : str, default 'merra2'
        Meteorological dataset ('merra2').
    orientation_factor : float, default 1.1
        Tilt/orientation factor passed to the PV capacity factor calculator.
    roughness_length : float, default 0.03
        Surface roughness length used for wind speed extrapolation.
    n_clusters : int, default 6
        Number of timeslices for k‑means clustering.
    scenario : str, default 'SSP2'
        Scenario identifier for the Mendeley dataset.
    output_path : str, optional
        If provided, the results will be written to this Excel file with
        sheets named ``SYSHECF`` and ``SHELF``.
    weather_headers : dict, optional
        Additional HTTP headers to pass when downloading the
        Renewables.ninja weather files.  Use this parameter to supply
        authentication tokens or cookies if required by the service.
    **kwargs : dict
        Additional keyword arguments passed to :func:`run_pipeline`.

    Returns
    -------
    (pd.DataFrame, pd.DataFrame, pd.Series)
        Tuple containing the capacity factors DataFrame, load factors
        DataFrame and the series of cluster labels (one per hour in the
        synthetic year).

    Notes
    -----
    * This function depends on DemandCast being installed for demand
      retrieval.  If DemandCast is not available, an exception will be
      raised when attempting to fetch real demand data.
    * If the Ember or weather data are not already present in the
      specified directories, the function will attempt to download
      them automatically.  The Ember dataset is fetched from the
      official Ember site with a fallback to the OWID energy dataset
      if the primary download fails.  Weather files are retrieved
      directly from Renewables.ninja using the country code and
      weighting specified.  Ensure you have appropriate
      internet access and permissions to download these files.
    """
    # Download external data if missing.  Download the Ember dataset and
    # Renewables.ninja weather files before loading anything.  This allows
    # the pipeline to run end‑to‑end in one call.  If downloads fail,
    # informative exceptions will be raised.
    demand_shape_source = str(demand_shape_source).strip().lower()
    mendeley_root = None
    if demand_shape_source in {'mendeley', 'efs'}:
        mendeley_root = ensure_mendeley_dataset(
            mendeley_dir,
            dataset_url=mendeley_dataset_url,
            headers=mendeley_headers,
        )
    # 1. Download Ember annual dataset if it does not exist.
    if ember_csv_path and (not os.path.exists(ember_csv_path) or os.path.getsize(ember_csv_path) == 0):
        download_ember_dataset(ember_csv_path)
    # 2. Download Renewables.ninja weather files for the specified country.
    download_weather_files(
        country_code=country_iso2,
        variables=['irradiance_surface', 'temperature', 'wind_speed'],
        weight=weight,
        dataset=dataset,
        output_dir=weather_dir,
        headers=weather_headers,
    )

    mendeley_region_name = mendeley_region_name or region_name
    ember_country_name = ember_country_name or region_name
    # ---- [setup] preset details (visible at the start of the run) -------
    cal_start_year_preview = year - last_n_years + 1
    _status(
        'setup',
        f"iso2={country_iso2}  timezone={country_timezone or 'UTC (no preset tz)'}  "
        f"demand-shape source={demand_shape_source}  "
        f"calibration window={cal_start_year_preview}–{year}  "
        f"cf calibration mode={cf_calibration_mode}",
    )

    # Step 1: Load synthetic end‑use demand for the selected year
    _t = time.perf_counter()
    if demand_shape_source == 'efs':
        if not efs_dir:
            raise ValueError("efs_dir is required when demand_shape_source='efs'.")
        _status('demand', f"loading EFS shapes ({efs_electrification} / {efs_technology_advancement} / nearest-to-{year})...")
        efs_zip_path = ensure_efs_dataset(efs_dir, dataset_url=EFS_DATASET_URL, headers=mendeley_headers)
        df_synthetic = load_enduse_data_efs_us(
            efs_zip_path=efs_zip_path,
            requested_year=year,
            electrification=efs_electrification,
            technology_advancement=efs_technology_advancement,
            recs_workbook_path=DEFAULT_EPS_SHELF_WORKBOOK_PATH,
            split_template_root=mendeley_root,
            split_template_region=mendeley_region_name,
            split_template_scenario=scenario,
            use_cache=use_cache,
            cache_dir=cache_dir,
        )
    elif demand_shape_source == 'mendeley':
        _status('demand', f"loading Mendeley shapes for region {mendeley_region_name!r}, year {year}...")
        df_synthetic = load_enduse_data_mendeley(
            mendeley_root, mendeley_region_name, year, scenario,
            use_cache=use_cache, cache_dir=cache_dir,
        )
    else:
        raise ValueError(
            f"Unsupported demand_shape_source '{demand_shape_source}'. Expected 'mendeley' or 'efs'."
        )
    _status(
        'demand',
        f"loaded {len(df_synthetic):,} hours × {df_synthetic.shape[1]} end-use columns",
        t=_t,
    )

    # Step 2: Fetch real demand over the most recent N years and compute average
    calibration_start_year = year - last_n_years + 1
    calibration_end_year = year
    _t = time.perf_counter()
    if demand_series_csv:
        _status(
            'calibrate-load',
            f"reading observed {demand_country_code} demand "
            f"{calibration_start_year}–{calibration_end_year} from local CSV "
            f"{demand_series_csv}...",
        )
        if demand_series_citation:
            _status('calibrate-load', f"  source: {demand_series_citation}")
        real_demand = load_local_demand_series(
            demand_series_csv,
            start_year=calibration_start_year,
            end_year=calibration_end_year,
            timezone=country_timezone,
            name=demand_country_code,
        )
    else:
        _status(
            'calibrate-load',
            f"fetching real {demand_country_code} demand "
            f"{calibration_start_year}–{calibration_end_year} via DemandCast...",
        )
        real_demand = fetch_demand_data_demandcast(
            demand_country_code,
            start_year=calibration_start_year,
            end_year=calibration_end_year,
        )
    # Determine calibration years (last_n_years ending at 'year')
    cal_start_year = year - last_n_years + 1
    cal_end_year = year
    real_demand_filtered = real_demand[(real_demand.index.year >= cal_start_year) & (real_demand.index.year <= cal_end_year)]
    _status(
        'calibrate-load',
        f"fetched {len(real_demand_filtered):,} hours of observed demand "
        f"(mean {float(real_demand_filtered.mean()):,.0f} MW)",
        t=_t,
    )
    # Calibrate synthetic load to match observed demand. Two methods supported:
    #   'level_seasonal' (default, legacy) — multiplicative annual scaling then
    #       per-month/per-peak adjustments. Implemented in calibrate_synthetic_load
    #       + calibrate_seasonal_enduse_load.
    #   'zapata_nnls' — regenerate the 4 climate-sensitive end-uses from weather
    #       + occupancy + Forsythe daylength via Zapata 2022 stylized functions,
    #       then solve monthly NNLS for end-use weights to fit observed totals.
    #       Substantially better hourly NRMSE in standalone tests; see
    #       zapata_implementation_readme.md for methodology and result comparison.
    _synth_load_mean = float(pd.to_numeric(df_synthetic['load'], errors='coerce').mean())
    _real_load_mean = float(pd.to_numeric(real_demand_filtered, errors='coerce').mean())
    _level_multiplier = (_real_load_mean / _synth_load_mean) if _synth_load_mean else float('nan')
    _status('calibrate-load', f"method: {calibration_method}")

    if calibration_method == 'zapata_nnls':
        if latitude_deg is None:
            raise ValueError(
                "calibration_method='zapata_nnls' requires latitude_deg, but none "
                "was supplied. Add a 'latitude_deg' field to the country preset, "
                "or pass it directly to generate_full_pipeline_for_country."
            )
        # Load weather early for shape regeneration. Single target year — the
        # Zapata stylized functions need country-specific weather covering the
        # synthetic year only. The CF computation later re-uses the cache (via
        # load_weather_data) for the calibration window of years.
        _t_zw = time.perf_counter()
        _status('calibrate-load', f"loading target-year weather for Zapata shape regeneration (lat {latitude_deg}°)")
        _zapata_weather = load_weather_data(
            weather_dir,
            country_iso2,
            ['temperature', 'irradiance_surface'],
            weight,
            dataset,
            use_cache=use_cache,
            cache_dir=cache_dir,
        )
        # Localize to country TZ, strip tz, filter to the synthetic year so
        # the index aligns with df_synthetic (naive local time).
        if country_timezone:
            if _zapata_weather.index.tz is None:
                _zapata_weather.index = _zapata_weather.index.tz_localize('UTC')
            _zapata_weather.index = _zapata_weather.index.tz_convert(country_timezone)
        if _zapata_weather.index.tz is not None:
            _zapata_weather.index = _zapata_weather.index.tz_localize(None)
        _zapata_weather, _zw_src_year, _zw_relabeled = _zapata_weather_for_year(
            _zapata_weather, year, df_synthetic.index)
        if _zw_relabeled:
            _status('calibrate-load',
                    f"target year {year} is beyond the weather archive; using {_zw_src_year} "
                    f"weather relabeled to {year} for the Zapata shape")
        _status(
            'calibrate-load',
            f"building Zapata hybrid basis  ({len(_zapata_weather):,} hours × stylized funcs)",
        )
        _df_basis = build_zapata_hybrid_basis(
            df_synthetic, _zapata_weather, latitude_deg=latitude_deg,
        )
        _zapata_end_use_cols = [
            'residential_cooling', 'residential_heating', 'residential_lighting',
            'residential_waterheating', 'residential_other',
            'service_cooling', 'service_heating', 'service_waterheating',
            'service_other', 'industry', 'transport',
        ]
        _status('calibrate-load', "solving monthly NNLS against observed totals")
        df_calibrated, _zapata_weights = calibrate_via_monthly_nnls(
            _df_basis, real_demand_filtered,
            end_use_cols=[c for c in _zapata_end_use_cols if c in _df_basis.columns],
        )
        df_scaled = df_calibrated  # alias for downstream metric code referencing df_scaled
        _status(
            'calibrate-load',
            f"Zapata-NNLS calibrated load: mean {df_calibrated['load'].mean():,.0f} MW  "
            f"peak {df_calibrated['load'].max():,.0f} MW",
            t=_t_zw,
        )
    elif calibration_method == 'zapata_ridge_nnls':
        # Path B: regenerate climate-sensitive shapes, align all columns to
        # country-specific EPS BAU magnitudes, then solve ridge-regularized
        # monthly NNLS. Anchors weights to the EPS prior (w=1 ≡ EPS share
        # is correct), preventing the basis-collinearity zero-flips that
        # plague plain NNLS. See "Path B" comment block before
        # load_eps_magnitude_prior for the rationale and EPS.mdl context.
        if latitude_deg is None:
            raise ValueError(
                "calibration_method='zapata_ridge_nnls' requires latitude_deg, but none "
                "was supplied. Add a 'latitude_deg' field to the country preset, "
                "or pass it directly to generate_full_pipeline_for_country."
            )
        if eps_prior_path is None:
            raise ValueError(
                "calibration_method='zapata_ridge_nnls' requires eps_prior_path. "
                "Add an 'eps_prior_path' field to the country preset pointing to "
                "data/eps_priors/eps_prior_<ISO2>.csv (extracted via "
                "data/eps_priors/parse_eps_extract.py)."
            )
        _t_zw = time.perf_counter()
        _status('calibrate-load', f"loading target-year weather for Zapata shape regeneration (lat {latitude_deg}°)")
        _zapata_weather = load_weather_data(
            weather_dir,
            country_iso2,
            ['temperature', 'irradiance_surface'],
            weight,
            dataset,
            use_cache=use_cache,
            cache_dir=cache_dir,
        )
        if country_timezone:
            if _zapata_weather.index.tz is None:
                _zapata_weather.index = _zapata_weather.index.tz_localize('UTC')
            _zapata_weather.index = _zapata_weather.index.tz_convert(country_timezone)
        if _zapata_weather.index.tz is not None:
            _zapata_weather.index = _zapata_weather.index.tz_localize(None)
        _zapata_weather, _zw_src_year, _zw_relabeled = _zapata_weather_for_year(
            _zapata_weather, year, df_synthetic.index)
        if _zw_relabeled:
            _status('calibrate-load',
                    f"target year {year} is beyond the weather archive; using {_zw_src_year} "
                    f"weather relabeled to {year} for the Zapata shape")
        _status('calibrate-load',
                f"building Zapata hybrid basis  ({len(_zapata_weather):,} hours × stylized funcs)")
        _df_basis_raw = build_zapata_hybrid_basis(
            df_synthetic, _zapata_weather, latitude_deg=latitude_deg,
        )
        _zapata_end_use_cols = [
            'residential_cooling', 'residential_heating', 'residential_lighting',
            'residential_waterheating', 'residential_other',
            'service_cooling', 'service_heating', 'service_waterheating',
            'service_other', 'industry', 'transport',
        ]
        _zapata_cols_present = [c for c in _zapata_end_use_cols if c in _df_basis_raw.columns]

        _status('calibrate-load', f"loading EPS magnitude prior from {eps_prior_path}")
        eps_prior = load_eps_magnitude_prior(eps_prior_path, target_year=year)
        _status(
            'calibrate-load',
            f"EPS prior: {len(eps_prior)} end-uses covering "
            f"{sum(eps_prior.values()):,.0f} MWh/yr",
        )
        _df_basis, _scales = align_basis_to_prior(
            _df_basis_raw, eps_prior, end_use_cols=_zapata_cols_present, verbose=True,
        )
        _status(
            'calibrate-load',
            f"solving monthly RIDGE NNLS (lambda={lambda_ridge}) against observed totals",
        )
        df_calibrated, _ridge_weights = calibrate_via_monthly_ridge_nnls(
            _df_basis, real_demand_filtered,
            end_use_cols=_zapata_cols_present,
            lambda_ridge=lambda_ridge,
        )
        df_scaled = df_calibrated
        _status(
            'calibrate-load',
            f"Zapata-Ridge calibrated load: mean {df_calibrated['load'].mean():,.0f} MW  "
            f"peak {df_calibrated['load'].max():,.0f} MW",
            t=_t_zw,
        )
    elif calibration_method == 'level_seasonal':
        _status(
            'calibrate-load',
            f"level scaling: synthetic mean {_synth_load_mean:,.0f} MW × "
            f"{_level_multiplier:.2f} → {_real_load_mean:,.0f} MW",
        )
        df_scaled = calibrate_synthetic_load(df_synthetic, real_demand_filtered, load_col='load')
        df_calibrated = df_scaled
        if seasonal_calibration:
            df_calibrated = calibrate_seasonal_enduse_load(
                df_scaled,
                real_demand_filtered,
                load_col='load',
            )
            _status('calibrate-load', "seasonal calibration applied (monthly-mean RMSE → ~0)")
        else:
            _status('calibrate-load', "seasonal calibration skipped (using level-scaled only)")
    else:
        raise ValueError(
            f"Unknown calibration_method={calibration_method!r}; expected "
            "'level_seasonal', 'zapata_nnls', or 'zapata_ridge_nnls'."
        )

    # ---- Calibration-overview plot (optional, can also short-circuit the run) ----
    # We resolve the output path early so the calibration plot has somewhere
    # to land before the heavy clustering work begins. If CALIBRATION_ONLY=True
    # the rest of the pipeline is skipped entirely — useful for quickly
    # iterating on calibration choices without paying for clustering/EPS export.
    resolved_output_path_early = resolve_output_path(output_path, country=region_name)
    if make_plots and resolved_output_path_early:
        _plots_dir = os.path.splitext(resolved_output_path_early)[0] + '_plots'
        _cal_plot_path = make_calibration_overview_plot(
            df_calibrated=df_calibrated,
            real_demand=real_demand_filtered,
            output_path=os.path.join(_plots_dir, 'calibration_overview.png'),
            country=region_name,
        )
        if _cal_plot_path:
            _status('plots', f"wrote calibration overview → {_cal_plot_path}")
    if calibration_only:
        _status(
            'done',
            "CALIBRATION_ONLY=True — exiting before weather / clustering / EPS export",
        )
        # Return empty results in the same shape callers expect.
        return pd.DataFrame(), pd.DataFrame(), pd.Series(dtype='float64')
    # Step 3: Load weather data and compute capacity factors
    _t = time.perf_counter()
    _status(
        'weather',
        f"loading {country_iso2} weather (irradiance, temperature, wind_speed)...",
    )
    weather_df = load_weather_data(
        weather_dir,
        country_iso2,
        ['irradiance_surface', 'temperature', 'wind_speed'],
        weight,
        dataset,
        use_cache=use_cache,
        cache_dir=cache_dir,
    )
    _status(
        'weather',
        f"loaded {len(weather_df):,} hours UTC, 3 variables",
        t=_t,
    )
    # ----- Timezone localization -------------------------------------------
    # Renewables.ninja files are timestamped in UTC. EPS expects the SHELF
    # and SYSHECF outputs to be in local time so that, e.g., Hour0 means
    # midnight local. Without this conversion, weather-derived capacity
    # factors get grouped by UTC hour-of-day while the demand shapes get
    # grouped by local hour-of-day, and the two are out of sync by the
    # country's UTC offset (9 hours for KST, 8 for CST China, etc.).
    #
    # tz_convert keeps each instant the same (no data shift); it only
    # changes the index labels. Subsequent .dayofyear / .hour calls then
    # reflect the local-time view, which is what we want for clustering
    # and EPS export.
    #
    # If country_timezone is None (e.g. an unverified preset that hasn't
    # had a timezone assigned yet) we leave the index in UTC and emit a
    # warning, so the failure mode is loud rather than silently producing
    # mis-aligned outputs. Presets that deliberately opt out of
    # localization (currently only the United States, pinned to the legacy
    # master-branch UTC behavior for baseline comparability) set
    # allow_utc_weather=True to suppress the warning.
    if country_timezone:
        if weather_df.index.tz is None:
            weather_df.index = weather_df.index.tz_localize('UTC')
        weather_df.index = weather_df.index.tz_convert(country_timezone)
    elif allow_utc_weather:
        _status(
            'weather',
            "keeping weather in UTC (preset sets allow_utc_weather=True — "
            "deliberate legacy-parity opt-out of timezone localization)",
        )
    else:
        import warnings
        warnings.warn(
            f"No country_timezone provided for {region_name!r}; weather data "
            "will remain in UTC. This will mis-align the SYSHECF output "
            "(UTC hour-of-day) with the SHELF output (local hour-of-day) "
            "by the country's UTC offset. Add a 'timezone' field to the "
            "country preset to fix.",
            stacklevel=2,
        )
    # Filter weather to the selected year (now in local time, if localized)
    weather_year = weather_df[(weather_df.index.year >= cal_start_year) & (weather_df.index.year <= cal_end_year)]
    if country_timezone:
        _status(
            'weather',
            f"localized to {country_timezone}; "
            f"filtered to calibration window: {len(weather_year):,} hours",
        )
    else:
        _status('weather', f"filtered to calibration window: {len(weather_year):,} hours (UTC, no localization)")
    # Compute capacity factors
    _t = time.perf_counter()
    cf_df = compute_capacity_factors_from_weather(
        weather_year,
        pv_irradiance_col='irradiance_surface',
        temp_col='temperature',
        wind_col='wind_speed',
        orientation_factor=orientation_factor,
        roughness_length=roughness_length,
    )
    _solar_raw_mean = float(pd.to_numeric(cf_df['solar_cf'], errors='coerce').mean())
    _wind_raw_mean = float(pd.to_numeric(cf_df['wind_cf'], errors='coerce').mean())
    _status(
        'cf',
        f"computed solar PV (orient×{orientation_factor}) and wind (hub 100m, z0={roughness_length}) CFs  "
        f"raw annual means: solar={_solar_raw_mean:.4f}  wind={_wind_raw_mean:.4f}",
        t=_t,
    )

    # --- Wind CF source override: Renewables.ninja per-site simulation outputs ---
    # For presets with wind_cf_source='ninja_sites' (China + South Korea as of
    # 2026-07-10), replace the 2 m-weather-derived wind_cf with the site-averaged
    # hub-height simulation output. The 2 m weather variable has an inverted
    # diurnal cycle vs hub height and is unusable for wind shape (see
    # DECISIONS.md 2026-07-10); the site outputs are the correct wind shape.
    # Solar is unchanged.
    #
    # Wind uses its OWN multi-year window (wind_cf_years, decoupled from the
    # demand/CF last_n_years window): the site archive is a weather climatology
    # and benefits from more years regardless of the model target year. We
    # reduce the selected site-years to a (day-of-year, hour) climatology and map
    # it onto cf_df's calendar. This also removes the UTC↔local boundary gap: a
    # single site-year's tz-shifted tail wraps around to fill the year's opening
    # hours, so every (doy, hour) cell is populated.
    #
    # The loader classifies each site onshore vs offshore, so alongside the
    # blended wind_cf it returns wind_onshore_cf / wind_offshore_cf. Those feed
    # SYSHECF-onshore-wind / SYSHECF-offshore-wind (EPS_SYSHECF_FILE_MAP);
    # wind_cf stays the blended series behind net load and clustering.
    _wind_type_cf_cols: List[str] = []
    if wind_cf_source == 'ninja_sites':
        _wind_years = wind_cf_years if wind_cf_years is not None else last_n_years
        # Blend weights: explicit preset key wins; otherwise fall back to the
        # region's EPS start-year wind capacities (data/eps_wind_capacity_split.csv,
        # built by scripts/fetch_eps_wind_capacity_split.py) and, failing that, to
        # site-count weighting inside the loader.
        _capacity_split = wind_capacity_split
        if _capacity_split is None:
            _capacity_split = load_eps_wind_capacity_split(country_iso2)
        site_wind = load_site_wind_capacity_factors(
            country_iso2, _wind_years,
            sites_dir=wind_sites_dir, country_timezone=country_timezone,
            capacity_split=_capacity_split,
        )
        _sidx = site_wind.index
        _keys = list(zip(cf_df.index.dayofyear, cf_df.index.hour))
        for _col in site_wind.columns:
            clim = site_wind[_col].groupby([_sidx.dayofyear, _sidx.hour]).mean()
            aligned = pd.Series(clim.reindex(_keys).to_numpy(), index=cf_df.index)
            n_missing = int(aligned.isna().sum())
            if n_missing:
                # Only possible if a (doy, hour) cell is entirely absent across all
                # selected site-years (e.g. cf_df includes leap-day Feb 29 but no
                # site-year is a leap year). Fill by time-interpolation.
                aligned = aligned.interpolate(method='time', limit_direction='both').ffill().bfill()
                _status(
                    'cf',
                    f"  {_col}: filled {n_missing} (doy,hour) cell(s) "
                    f"({100 * n_missing / len(aligned):.2f}%) absent from the site-year climatology",
                )
            cf_df[_col] = aligned.to_numpy()
        _wind_type_cf_cols = [c for c in site_wind.columns if c != 'wind_cf']
        _wind_raw_mean = float(pd.to_numeric(cf_df['wind_cf'], errors='coerce').mean())
        _status(
            'cf',
            f"replaced weather-derived wind_cf with ninja site outputs "
            f"(wind_cf_years={_wind_years}, doy×hour climatology; "
            f"raw annual-mean CF={_wind_raw_mean:.4f}; "
            f"site-type series: {', '.join(_wind_type_cf_cols) or 'none'})",
        )

    # Step 4: Calibrate capacity factors using Ember statistics
    capacities, observed_cf = load_ember_annual_capacity_factors(
        ember_csv_path, country=ember_country_name, variables=['Solar', 'Wind'], last_n_years=last_n_years
    )
    _solar_target = observed_cf.get('Solar', float('nan'))
    _wind_target = observed_cf.get('Wind', float('nan'))
    _status(
        'cf',
        f"Ember targets for {country_iso2}: solar={_solar_target:.4f}  wind={_wind_target:.4f}  "
        f"(calibration mode = {cf_calibration_mode})",
    )
    if wind_cf_source == 'ninja_sites':
        # Wind CF already comes from hub-height site simulation outputs, so the
        # speed_rescale path does not apply (there is no wind-speed series to
        # rescale). Calibrate the wind annual mean to the Ember target with
        # cap_redistribute (bounded [0, 1]); solar keeps the requested mode,
        # falling back to cap_redistribute if the run selected speed_rescale.
        _solar_mode = 'cap_redistribute' if cf_calibration_mode == 'speed_rescale' else cf_calibration_mode
        cf_scaled = calibrate_capacity_factors(
            cf_df,
            {k: v for k, v in observed_cf.items() if k == 'Solar'},
            rename_map={'Solar': 'solar_cf'},
            mode=_solar_mode,
        )
        _wind_target = observed_cf.get('Wind')
        if _wind_target is not None and np.isfinite(float(_wind_target)):
            _diags = dict(cf_scaled.attrs.get('calibration_diagnostics', {}))
            # Ember publishes one fleet-wide wind CF, so the blended series is
            # the only anchorable quantity. Calibrate it to the target, then
            # scale the onshore/offshore series by the SAME factor the blend
            # needed (target ÷ raw blended mean) rather than calibrating each to
            # the fleet target — that keeps the offshore-vs-onshore CF ratio the
            # site simulations imply, while leaving the capacity-weighted blend
            # on target. Each type still goes through cap_redistribute so it
            # stays bounded in [0, 1].
            _wind_raw_blend = float(pd.to_numeric(cf_df['wind_cf'], errors='coerce').mean())
            _wind_scale = (
                float(_wind_target) / _wind_raw_blend if _wind_raw_blend > 0 else float('nan')
            )
            for _col, _tgt in [('wind_cf', float(_wind_target))] + [
                (c, float(pd.to_numeric(cf_df[c], errors='coerce').mean()) * _wind_scale)
                for c in _wind_type_cf_cols
            ]:
                if not np.isfinite(_tgt):
                    cf_scaled[_col] = cf_df[_col]
                    continue
                _cal = calibrate_capacity_factors(
                    cf_df, {_col: _tgt}, rename_map={_col: _col}, mode='cap_redistribute',
                )
                cf_scaled[_col] = _cal[_col]
                _cd = _cal.attrs.get('calibration_diagnostics', {}).get(_col)
                if _cd:
                    _diags[_col] = _cd
            cf_scaled.attrs['calibration_diagnostics'] = _diags
            _status(
                'cf',
                f"  wind_cf: site-output CF calibrated to Ember target "
                f"{float(_wind_target):.4f} (cap_redistribute)",
            )
            for _col in _wind_type_cf_cols:
                _status(
                    'cf',
                    f"  {_col}: calibrated to {float(cf_scaled[_col].mean()):.4f} "
                    f"(raw × {_wind_scale:.3f}, the blend's Ember scale — preserves the "
                    f"site-implied onshore/offshore ratio)",
                )
        else:
            for _col in ['wind_cf', *_wind_type_cf_cols]:
                cf_scaled[_col] = cf_df[_col]
            _status('cf', "  wind_cf: site-output CF used uncalibrated (no Ember wind target)")
    elif cf_calibration_mode == 'speed_rescale':
        # Wind is calibrated in wind-speed space (physical shape, bounded by
        # the power curve — see calibrate_wind_cf_speed_rescale). Solar keeps
        # cap_redistribute: its multiplier is near 1 in practice and there is
        # no equivalent "speed" to rescale for irradiance.
        cf_scaled = calibrate_capacity_factors(
            cf_df,
            {k: v for k, v in observed_cf.items() if k == 'Solar'},
            rename_map={'Solar': 'solar_cf'},
            mode='cap_redistribute',
        )
        _wind_target = observed_cf.get('Wind')
        if _wind_target is not None and np.isfinite(float(_wind_target)):
            _wind_series, _wind_diag = calibrate_wind_cf_speed_rescale(
                weather_year,
                float(_wind_target),
                wind_speed_col='wind_speed',
                roughness_length=roughness_length,
            )
            cf_scaled['wind_cf'] = _wind_series
            _diags = dict(cf_scaled.attrs.get('calibration_diagnostics', {}))
            _diags['wind_cf'] = _wind_diag
            cf_scaled.attrs['calibration_diagnostics'] = _diags
            _status(
                'cf',
                f"  wind_cf: speed_rescale k={_wind_diag['speed_scale_k']:.3f} "
                f"(replaces CF-space multiplier {_wind_diag['initial_multiplier']:.2f}×)",
            )
    else:
        cf_scaled = calibrate_capacity_factors(
            cf_df,
            observed_cf,
            rename_map={'Solar': 'solar_cf', 'Wind': 'wind_cf'},
            mode=cf_calibration_mode,
        )
    # Surface the per-column calibration diagnostics inline so the user
    # sees the multiplier and the fraction-at-cap at the moment they
    # matter, without having to open the metrics CSV.
    for _col, _diag in cf_scaled.attrs.get('calibration_diagnostics', {}).items():
        _mult = _diag.get('initial_multiplier', float('nan'))
        _frac = _diag.get('fraction_at_cap', float('nan'))
        _max = _diag.get('final_max', float('nan'))
        _resid = _diag.get('residual_mean_error', float('nan'))
        _unreach = _diag.get('mean_unreachable', False)
        _status(
            'cf',
            f"  {_col}: multiplier={_mult:.2f}×  frac_at_cap={_frac*100:.1f}%  "
            f"max={_max:.4f}  residual={_resid:+.4f}"
            + ("  (target unreachable — synthetic too saturated)" if _unreach else ""),
        )
    # Step 5: Compute generation (MW) from capacity factors using average installed capacity
    # Convert installed capacity from GW to MW
    solar_cap = capacities.get('Solar', 0.0) * 1000.0
    wind_cap = capacities.get('Wind', 0.0) * 1000.0
    _status(
        'gen',
        f"installed capacity (Ember avg over {last_n_years}y): "
        f"solar={solar_cap/1000:.1f} GW  wind={wind_cap/1000:.1f} GW",
    )
    # Wind generation (and hence net load) uses the blended wind_cf; the
    # site-type series ride along so they reach the SYSHECF export on the same
    # calendar. Both end in '_cf' so the load-column filter below skips them.
    _carry_cf_cols = ['solar_cf', 'wind_cf', *[c for c in _wind_type_cf_cols if c in cf_scaled.columns]]
    gen_df = pd.DataFrame(index=cf_scaled.index)
    for _col in _carry_cf_cols:
        gen_df[_col] = cf_scaled[_col]
    gen_df['solar_gen'] = cf_scaled['solar_cf'] * solar_cap
    gen_df['wind_gen'] = cf_scaled['wind_cf'] * wind_cap
    # Align generation with synthetic demand index (synthetic year).  We align by time of year.
    # Create a mapping from day of year and hour to mean generation across the calibration years.
    gen_df['doy'] = gen_df.index.dayofyear
    gen_df['hour'] = gen_df.index.hour
    # Average generation for each DOY and hour
    gen_avg = gen_df.groupby(['doy', 'hour']).mean()[[*_carry_cf_cols, 'solar_gen', 'wind_gen']]
    # Construct generation series for the synthetic year
    synthetic_year_dates = df_calibrated.index
    doy = synthetic_year_dates.dayofyear
    hour = synthetic_year_dates.hour
    gen_interp = gen_avg.loc[list(zip(doy, hour))].reset_index(drop=True)
    gen_interp.index = synthetic_year_dates
    # Add generation columns to the calibrated demand DataFrame
    df_with_gen = df_calibrated.copy()
    for _col in _carry_cf_cols:
        df_with_gen[_col] = gen_interp[_col].values
    df_with_gen['solar_gen'] = gen_interp['solar_gen'].values
    df_with_gen['wind_gen'] = gen_interp['wind_gen'].values
    # Step 6: Compute net load by subtracting generation
    df_with_gen['net_load'] = df_with_gen['load'] - df_with_gen['solar_gen'] - df_with_gen['wind_gen']
    _nl = pd.to_numeric(df_with_gen['net_load'], errors='coerce')
    _status(
        'gen',
        f"net load = load − solar_gen − wind_gen  → "
        f"annual mean {float(_nl.mean()):,.0f} MW  "
        f"(range {float(_nl.min()):,.0f}–{float(_nl.max()):,.0f})",
    )
    # Use net load for clustering; pass generation columns for subtraction in run_pipeline
    gen_cols = ['solar_gen', 'wind_gen']
    cf_cols = list(_carry_cf_cols)
    # Determine which load columns to include for load factor computation
    load_cols = [
        col for col in df_with_gen.columns
        if (np.issubdtype(df_with_gen[col].dtype, np.number)
            and col not in gen_cols
            and not col.endswith('_cf')
            and not col.endswith('_gen')
            and col not in {'load', 'net_load'})
    ]
    # Run the standard pipeline using the precomputed net load series directly.
    resolved_output_path = resolve_output_path(output_path, country=region_name)
    run_metadata = {
        'country': region_name,
        # Which observed hourly demand record calibrated this run, so the
        # provenance travels with the outputs rather than only the console log.
        'observed_demand_source': demand_series_csv or 'DemandCast',
        'observed_demand_citation': (
            demand_series_citation if demand_series_csv else None
        ),
        'observed_demand_window': f'{calibration_start_year}-{calibration_end_year}',
        'demand_shape_source': df_synthetic.attrs.get('demand_shape_source', demand_shape_source),
        'demand_shape_source_year': df_synthetic.attrs.get('demand_shape_source_year', year),
        'demand_shape_source_scenario': df_synthetic.attrs.get('demand_shape_source_scenario', scenario),
        **elccafr_run_metadata(region_name),
    }

    run_details = run_pipeline(
        df_with_gen,
        load_col='net_load',
        gen_cols=[],
        cf_cols=cf_cols,
        load_cols=load_cols,
        n_clusters=n_clusters,
        country=region_name,
        output_path=resolved_output_path,
        return_details=True,
        feature_weight_mode=kwargs.get('feature_weight_mode', 'netload_focus'),
        search_seeds=kwargs.get('search_seeds'),
        run_metadata=run_metadata,
    )
    cf_results = run_details['capacity_factors']
    lf_results = run_details['load_factors']
    labels = run_details['labels']

    # Days-per-timeslice summary so the user can sanity-check the cluster
    # composition at a glance.
    _ts_metadata = run_details.get('timeslice_metadata')
    if _ts_metadata is not None and 'timeslice_name' in _ts_metadata.columns and 'days_represented' in _ts_metadata.columns:
        _days_summary = '  '.join(
            f"{name}={int(days)}"
            for name, days in zip(_ts_metadata['timeslice_name'], _ts_metadata['days_represented'])
        )
        _status('cluster', f"days per timeslice: {_days_summary}")

    metrics_df = build_run_metrics(
        country=region_name,
        year=year,
        synthetic_df=df_synthetic,
        scaled_df=df_scaled,
        calibrated_df=df_calibrated,
        real_demand=real_demand_filtered,
        cf_raw=cf_df,
        cf_scaled=cf_scaled,
        observed_cf=observed_cf,
    )
    clustering_columns = ['load', 'net_load'] + [col for col in cf_cols if col in df_with_gen.columns]
    preferred_load_columns = [
        'residential_total',
        'service_total',
        'industry_total',
        'transport_total',
    ]
    clustering_columns.extend([col for col in preferred_load_columns if col in df_with_gen.columns])
    clustering_columns = list(dict.fromkeys(clustering_columns))
    clustering_metrics = build_clustering_metrics(
        country=region_name,
        year=year,
        df=df_with_gen,
        labels=labels,
        timestamps=df_with_gen.index.to_series(),
        columns=clustering_columns,
        representative_dates=run_details.get('representative_dates'),
    )
    # The pinned-vs-unpinned comparison is opt-in because it re-runs the
    # full clustering pipeline twice (~2× the clustering cost). The
    # production answer is the pinned variant, which has already been
    # computed above; the comparison only adds the unpinned baseline plus
    # a redundant pinned re-run for symmetry. Worth enabling occasionally
    # to verify the pinning trade-off on a new country; not worth the
    # time on every routine run once the trade-off is understood.
    if compare_pinned_unpinned:
        _status(
            'cluster',
            "running pinned-vs-unpinned reconstruction comparison "
            "(re-clusters once with and once without pinning)...",
        )
        _t_compare = time.perf_counter()
        comparison_metrics = compare_pinned_unpinned_clustering(
            country=region_name,
            year=year,
            df=df_with_gen,
            load_col='net_load',
            gen_cols=[],
            n_clusters=n_clusters,
            feature_weight_mode=kwargs.get('feature_weight_mode', 'netload_focus'),
            search_seeds=kwargs.get('search_seeds'),
        )
        _status('cluster', "comparison complete", t=_t_compare)
    else:
        comparison_metrics = pd.DataFrame()
        _status(
            'cluster',
            "skipping pinned-vs-unpinned comparison "
            "(set COMPARE_PINNED_UNPINNED=True in run_pipeline.py to enable)",
            level='verbose',
        )

    metrics_df = pd.concat([metrics_df, clustering_metrics, comparison_metrics], ignore_index=True)
    _status(
        'metrics',
        f"writing per-run metrics ({len(metrics_df)} rows) + appending to global summary",
    )
    write_metrics_reports(metrics_df, resolved_output_path)

    # Single-line output / eps summaries (file lists deliberately suppressed
    # so they don't clutter the log; the directory contents tell that story).
    if resolved_output_path:
        _status(
            'output',
            f"generic outputs written → {resolved_output_path} (+ companion CSVs)",
        )
        _eps_dir = os.path.splitext(resolved_output_path)[0] + '_EPS'
        if os.path.isdir(_eps_dir):
            try:
                _shelf_count = len([
                    f for f in os.listdir(os.path.join(_eps_dir, 'SHELF'))
                    if f.endswith('.csv')
                ]) if os.path.isdir(os.path.join(_eps_dir, 'SHELF')) else 0
                _syshecf_count = len([
                    f for f in os.listdir(os.path.join(_eps_dir, 'SYSHECF'))
                    if f.endswith('.csv')
                ]) if os.path.isdir(os.path.join(_eps_dir, 'SYSHECF')) else 0
            except OSError:
                _shelf_count = _syshecf_count = 0
            _status(
                'eps',
                f"EPS files written → {_eps_dir}/  "
                f"(SHELF: {_shelf_count}, SYSHECF: {_syshecf_count})",
            )

    print_metrics_summary(region_name, metrics_df)

    # ---- Diagnostic plots (per-cluster, four variables each) ----
    # Optional. Produces 24 PNG files (6 timeslices × 4 variables) under
    # <output_root>_plots/. Skipped if `make_plots=False` or if matplotlib
    # is not importable.
    if make_plots and resolved_output_path:
        _t_plots = time.perf_counter()
        plots_dir = os.path.splitext(resolved_output_path)[0] + '_plots'
        _ts_metadata_for_plots = run_details.get('timeslice_metadata')
        plot_paths = make_cluster_diagnostic_plots(
            df=df_with_gen,
            labels=labels,
            timeslice_metadata=_ts_metadata_for_plots,
            representative_dates=run_details.get('representative_dates') or {},
            output_dir=plots_dir,
            country=region_name,
        )
        if plot_paths:
            _status(
                'plots',
                f"wrote {len(plot_paths)} cluster diagnostic plots → {plots_dir}/",
                t=_t_plots,
            )
        else:
            _status(
                'plots',
                "diagnostic plots skipped (matplotlib unavailable or no data)",
                level='verbose',
            )

        # Per-timeslice SHELF load-factor plots: one faceted PNG per timeslice
        # (category panels), each day dotted + the timeslice mean solid.
        lf_plot_paths = make_enduse_lf_plots(
            df=df_with_gen,
            labels=labels,
            timeslice_metadata=_ts_metadata_for_plots,
            output_dir=plots_dir,
            country=region_name,
        )
        if lf_plot_paths:
            _status(
                'plots',
                f"wrote {len(lf_plot_paths)} end-use load-factor plots → {plots_dir}/",
            )

        # The calibration-overview plot is now generated earlier (right after
        # the calibration step). No re-emit here.

    return cf_results, lf_results, labels

###############################################################################
# Weighted aggregation utilities
###############################################################################

def compute_area_weights(latitudes: Iterable[float]) -> np.ndarray:
    """
    Compute normalized area weights for a set of grid cells.

    Many global reanalysis datasets (e.g. MERRA‑2 or ERA5) are defined on
    regular latitude–longitude grids.  The physical surface area covered by
    each grid cell decreases with latitude because lines of longitude converge
    toward the poles.  When aggregating a variable (such as capacity factors
    or weather variables) across multiple grid cells, it is often desirable to
    weight each cell by its actual land area.  For a latitude/longitude grid
    with uniform spacing in degrees, the area of a cell at latitude ``lat`` is
    proportional to ``cos(lat)``.  This function calculates area weights using
    that approximation and normalizes them to sum to one.

    Parameters
    ----------
    latitudes : Iterable[float]
        A sequence of latitude values (in degrees) for each grid cell or site.

    Returns
    -------
    np.ndarray
        Array of normalized area weights with the same length as ``latitudes``.

    Notes
    -----
    * The cosine approximation assumes a rectangular grid with constant
      longitudinal spacing.  For very fine grids or regions that span a wide
      range of longitudes (especially near the poles) a more exact area
      calculation may be required.  In such cases, consider computing the
      polygon area of each grid cell using a geospatial library (e.g.
      ``geopandas`` or ``pyproj``) and normalizing by the total area.
    """
    lats = np.asarray(list(latitudes), dtype=float)
    # Convert degrees to radians
    rad = np.radians(lats)
    # Raw weights proportional to the cosine of latitude
    raw = np.cos(rad)
    # Replace negative values (beyond the poles) with zero
    raw = np.where(raw < 0, 0, raw)
    # Normalize to sum to 1; avoid division by zero
    total = raw.sum()
    if total == 0:
        raise ValueError("Sum of raw area weights is zero; check input latitudes.")
    return raw / total


def compute_population_weights(population_values: Iterable[float]) -> np.ndarray:
    """
    Compute normalized weights based on population values.

    This helper normalizes a sequence of population counts so that the
    resulting weights sum to one.  Population weighting is useful when
    aggregating weather or generation data to represent the conditions
    experienced by the population rather than the land area.  For example,
    Renewables.ninja's country‑level weather aggregates use a population‑
    weighted mean across all MERRA‑2 grid cells within the given country
   【253340970991469†L11-L15】.

    Parameters
    ----------
    population_values : Iterable[float]
        A sequence of population counts for each grid cell or site.

    Returns
    -------
    np.ndarray
        Array of normalized weights summing to one.

    Raises
    ------
    ValueError
        If the total population is zero.
    """
    pop = np.asarray(list(population_values), dtype=float)
    total = pop.sum()
    if total == 0:
        raise ValueError("Total population for weighting is zero; cannot compute weights.")
    return pop / total


def aggregate_weighted_series(
    data: pd.DataFrame,
    weights: Dict[str, float],
) -> pd.Series:
    """
    Aggregate multiple time series into a single weighted average series.

    Given a DataFrame with one column per site or grid cell and a dictionary
    of weights for each column, this function computes a weighted sum across
    the columns for each time step.  The weights should sum to one.  If they
    do not, they will be renormalized.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame whose columns correspond to the sites or grid cells to
        aggregate and whose index represents the time dimension (e.g. hourly
        timestamps).  All values should be numeric.
    weights : dict[str, float]
        Mapping from column name in ``data`` to its corresponding weight.  Any
        columns missing from the weights mapping will be dropped.  Extra keys
        in ``weights`` that do not correspond to columns in ``data`` are
        ignored.

    Returns
    -------
    pandas.Series
        Weighted average time series across the specified columns.

    Notes
    -----
    * The weights are renormalized to sum to one before aggregation.  This
      ensures that inadvertent rounding or scaling errors in the supplied
      weights do not bias the result.
    * This function does not perform any spatial matching; it assumes that
      the caller has already aligned each column with the appropriate weight
      (e.g. via a geospatial join between grid cells and the target region).
    """
    # Filter to columns present in both data and weights
    common_cols = [c for c in data.columns if c in weights]
    if not common_cols:
        raise ValueError("No columns in data match the provided weights.")
    sub = data[common_cols].copy()
    # Extract and renormalize weights
    w = np.array([weights[c] for c in common_cols], dtype=float)
    total = w.sum()
    if total == 0:
        raise ValueError("Sum of weights is zero; cannot compute weighted average.")
    w = w / total
    # Compute weighted average along the columns axis
    # Each row in sub is multiplied by the weight vector
    weighted_values = sub.values.dot(w)
    return pd.Series(weighted_values, index=sub.index, name="weighted_average")

# Mapping from numeric region codes to region names for the Mendeley hourly end‑use
# dataset.  This mapping is derived from the ``Regions_code.docx`` file included
# in the dataset.  If new regions are added or codes change in future versions,
# update this dictionary accordingly.
REGION_CODE_MAP: Dict[int, str] = {
    1: 'Canada',
    2: 'USA',
    3: 'Mexico',
    4: 'Rest Central America',
    5: 'Brazil',
    6: 'Rest South America',
    7: 'Northern Africa',
    8: 'Western Africa',
    9: 'Eastern Africa',
    10: 'Southern Africa',
    11: 'Western Europe',
    12: 'Central Europe',
    13: 'Turkey',
    14: 'Ukraine +',
    15: 'Asia-Stan',
    16: 'Russia +',
    17: 'Middle East',
    18: 'India +',
    19: 'Korea',
    20: 'China +',
    21: 'Southeastern Asia',
    22: 'Indonesia +',
    23: 'Japan',
    24: 'Oceania',
    25: 'Rest S.Asia',
    26: 'Rest S.Africa',
}

# Invert the region mapping for quick lookup of codes by name.
NAME_TO_CODE: Dict[str, int] = {v: k for k, v in REGION_CODE_MAP.items()}
REGION_ALIASES: Dict[str, str] = {
    'South Korea': 'Korea',
    'Republic of Korea': 'Korea',
}

def _parse_regioncoded_patterns(
    file_weekday: str,
    file_weekend: str,
    region: str,
    year: int,
) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """Parse monthly hourly patterns from region‑coded CSV files.

    Some Mendeley end‑use files (e.g. ``Residential_cooling_weekday.csv``)
    provide a single row per month with columns ``Year``, ``Region``,
    ``Month`` and ``h1``–``h24``.  This helper reads the weekday and
    weekend files for a given year and region, returning two dictionaries
    mapping months to arrays of 24 hourly values.

    Parameters
    ----------
    file_weekday, file_weekend : str
        Paths to the weekday and weekend CSVs.
    region : str
        Human‑readable region name (e.g. 'USA').
    year : int
        Year to extract.

    Returns
    -------
    weekday_patterns, weekend_patterns : dict[int, np.ndarray]
        Dictionaries mapping month (1–12) to arrays of 24 floats.
    """

    region = REGION_ALIASES.get(region, region)
    if region not in NAME_TO_CODE:
        raise ValueError(f"Unknown region '{region}'. Available regions: {list(NAME_TO_CODE.keys())}")
    region_code = NAME_TO_CODE[region]

    def read_file(path: str) -> Dict[int, np.ndarray]:
        df = pd.read_csv(path, skiprows=4, dtype=str)
        # Standardise column names
        df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
        # Convert numeric columns
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Region'] = pd.to_numeric(df['Region'], errors='coerce')
        df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
        df = df[(df['Year'] == year) & (df['Region'] == region_code)]
        patterns: Dict[int, np.ndarray] = {}
        for _, row in df.iterrows():
            month = int(row['Month'])
            # Extract h1…h24 columns
            cols = [c for c in row.index if isinstance(c, str) and c.lower().startswith('h')]
            cols = sorted(cols, key=lambda s: int(s[1:]))
            arr = row[cols].astype(float).values
            patterns[month] = arr
        return patterns

    weekday_patterns = read_file(file_weekday)
    weekend_patterns = read_file(file_weekend)
    return weekday_patterns, weekend_patterns


def _parse_regionnamed_patterns(
    file_weekday: str,
    file_weekend: str,
    region: str,
    year: int,
) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """Parse monthly hourly patterns from region‑named CSV files.

    Files such as ``Industry_total_weekday_SSP2.csv`` provide one row per
    hour with columns ``Month`` and ``Hour`` alongside region names.  This
    helper extracts the hourly patterns for the specified region and year.

    Parameters
    ----------
    file_weekday, file_weekend : str
        Paths to the weekday and weekend CSV files.
    region : str
        Region name matching a column in the CSV.
    year : int
        Year to extract.

    Returns
    -------
    weekday_patterns, weekend_patterns : dict[int, np.ndarray]
        Dictionaries mapping month to arrays of length 24.
    """
    region = REGION_ALIASES.get(region, region)

    def read_file(path: str) -> Dict[int, np.ndarray]:
        df = pd.read_csv(path, skiprows=4, dtype=str, low_memory=False)
        # Determine year column name
        year_col = 'year' if 'year' in df.columns else 'Year'
        df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
        # Convert numeric columns
        df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
        df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
        df['Hour'] = pd.to_numeric(df['Hour'], errors='coerce')
        if region not in df.columns:
            raise ValueError(f"Region '{region}' not found in {os.path.basename(path)}")
        df[region] = pd.to_numeric(df[region], errors='coerce')
        df = df[df[year_col] == year]
        patterns: Dict[int, np.ndarray] = {}
        for month in sorted(df['Month'].dropna().unique()):
            m = int(month)
            sub = df[df['Month'] == month].sort_values('Hour')
            patterns[m] = sub[region].astype(float).values
        return patterns

    weekday_patterns = read_file(file_weekday)
    weekend_patterns = read_file(file_weekend)
    return weekday_patterns, weekend_patterns


def _replicate_monthly_patterns(
    weekday_patterns: Dict[int, np.ndarray],
    weekend_patterns: Dict[int, np.ndarray],
    year: int,
) -> pd.Series:
    """Replicate monthly hourly patterns into an hourly Series for a given year.

    For each date in the year, this function selects the appropriate
    weekday or weekend pattern and appends its 24 hourly values.  Weekends
    are defined as Saturday and Sunday (``weekday() >= 5``).  If a pattern
    is missing for a particular day type, the available pattern for that
    month is used as a fallback.

    Parameters
    ----------
    weekday_patterns, weekend_patterns : dict[int, np.ndarray]
        Mappings from month to 24‑element arrays for weekdays and weekends.
    year : int
        Year to construct (leap years are handled).

    Returns
    -------
    pandas.Series
        Hourly Series indexed by timestamps for the entire year.
    """
    values: list[np.ndarray] = []
    timestamps: list[_datetime.datetime] = []
    for month in range(1, 13):
        _, days_in_month = calendar.monthrange(year, month)
        for day in range(1, days_in_month + 1):
            dt = _datetime.datetime(year, month, day)
            is_weekend = dt.weekday() >= 5
            pattern = weekend_patterns.get(month) if is_weekend else weekday_patterns.get(month)
            if pattern is None:
                # Fallback: use whichever pattern exists for the month
                pattern = weekday_patterns.get(month) or weekend_patterns.get(month)
            values.append(pattern)
            for hour in range(24):
                timestamps.append(_datetime.datetime(year, month, day, hour))
    data = np.concatenate([arr.reshape(1, -1) for arr in values], axis=0).reshape(-1)
    return pd.Series(data, index=pd.DatetimeIndex(timestamps))


def load_enduse_data_mendeley(
    data_dir: str,
    region: str,
    year: int,
    scenario: str = 'SSP2',
    use_cache: bool = False,
    cache_dir: Optional[str] = None,
) -> pd.DataFrame:
    """Load hourly end‑use electricity demand from the Mendeley dataset.

    This function assembles a 365‑ or 366‑day hourly time series of
    electricity demand by end‑use and sector for a given region and year.
    It uses the ``Future global electricity demand load curves`` dataset
    (Mendeley ID ``pmd2dchk44``) and reconstructs hourly profiles by
    repeating monthly weekday and weekend patterns across the calendar.

    End‑use categories include:

    * Residential: cooling, heating, lighting, water heating, other
    * Service: cooling, heating, water heating, other
    * Industry: total
    * Transport: total

    The ``other`` categories for residential and service sectors are
    calculated as the difference between the aggregated sector total and the
    sum of the explicitly modelled end‑uses.  Negative differences (due
    perhaps to missing data) are clipped at zero.

    Parameters
    ----------
    data_dir : str
        Directory containing the extracted CSV files from the Mendeley
        dataset (e.g. ``/home/oai/share/pmd2dchk44-1``).
    region : str
        Region name (e.g. 'USA', 'Canada').  Must appear in
        ``REGION_CODE_MAP`` or as a column in the aggregated files.
    year : int
        Year to construct (between 1971 and 2100).
    scenario : str, default 'SSP2'
        Scenario identifier used for aggregated files (e.g. 'SSP2').

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by hourly timestamps with columns for each
        end‑use and sector, sector totals and a ``load`` column equal to
        the sum of sector totals.
    """
    region = region.strip()

    # ------------------------------------------------------------------
    # Cache short-circuit. Mendeley parsing reads ~22 ~9 MB CSVs; the
    # cached parquet is tiny (one year × ~15 columns) and reads in ~1 s.
    # ------------------------------------------------------------------
    if use_cache:
        cache_name = (
            f"mendeley_{_safe_filename_part(region)}_"
            f"{_safe_filename_part(year)}_{_safe_filename_part(scenario)}.parquet"
        )
        cache_path = os.path.join(_resolve_cache_dir(data_dir, cache_dir), cache_name)
        # Source paths: the broad set of Mendeley CSVs this loader touches.
        # If any of them changed, we rebuild.
        _mendeley_sources = [
            os.path.join(data_dir, name)
            for name in (
                f'Residential_total_weekday_{scenario}.csv',
                f'Residential_total_weekend_{scenario}.csv',
                f'Service_total_weekday_{scenario}.csv',
                f'Service_total_weekend_{scenario}.csv',
                f'Industry_total_weekday_{scenario}.csv',
                f'Industry_total_weekend_{scenario}.csv',
                'Transport_total_weekday.csv',
                'Transport_total_weekend.csv',
                'Residential_cooling_weekday.csv',
                'Residential_cooling_weekend.csv',
                'Residential_heating_weekday.csv',
                'Residential_heating_weekend.csv',
                'Residential_lighting_weekday.csv',
                'Residential_lighting_weekend.csv',
                'Residential_waterheating_weekday.csv',
                'Residential_waterheating_weekend.csv',
                'Service_cooling_weekday.csv',
                'Service_cooling_weekend.csv',
                'Service_heating_weekday.csv',
                'Service_heating_weekend.csv',
                'Service_waterheating_weekday.csv',
                'Service_waterheating_weekend.csv',
            )
        ]

        def _build():
            return load_enduse_data_mendeley(
                data_dir, region, year, scenario,
                use_cache=False, cache_dir=None,
            )
        return _read_or_build_cached_parquet(cache_path, _mendeley_sources, _build)

    # Helper to form file names for aggregated sector totals
    def tot_path(sector: str, day_type: str) -> str:
        if sector.lower() in {'residential', 'service', 'industry'}:
            return os.path.join(data_dir, f"{sector}_total_{day_type}_{scenario}.csv")
        else:
            # Transport files lack a scenario suffix
            return os.path.join(data_dir, f"{sector}_total_{day_type}.csv")

    # Residential end‑uses
    residential_uses = ['cooling', 'heating', 'lighting', 'waterheating']
    residential_series: Dict[str, pd.Series] = {}
    for use in residential_uses:
        f_wd = os.path.join(data_dir, f"Residential_{use}_weekday.csv")
        f_we = os.path.join(data_dir, f"Residential_{use}_weekend.csv")
        wd_pat, we_pat = _parse_regioncoded_patterns(f_wd, f_we, region, year)
        residential_series[f'residential_{use}'] = _replicate_monthly_patterns(wd_pat, we_pat, year)
    # Aggregated residential total
    wd_tot, we_tot = _parse_regionnamed_patterns(tot_path('Residential', 'weekday'), tot_path('Residential', 'weekend'), region, year)
    residential_total = _replicate_monthly_patterns(wd_tot, we_tot, year)
    res_sum = sum(residential_series.values())
    residential_other = residential_total - res_sum
    residential_other = residential_other.clip(lower=0)
    residential_series['residential_other'] = residential_other
    residential_series['residential_total'] = residential_total

    # Service end‑uses
    service_uses = ['cooling', 'heating', 'waterheating']
    service_series: Dict[str, pd.Series] = {}
    for use in service_uses:
        f_wd = os.path.join(data_dir, f"Service_{use}_weekday.csv")
        f_we = os.path.join(data_dir, f"Service_{use}_weekend.csv")
        wd_pat, we_pat = _parse_regioncoded_patterns(f_wd, f_we, region, year)
        service_series[f'service_{use}'] = _replicate_monthly_patterns(wd_pat, we_pat, year)
    # Aggregated service total
    wd_tot_svc, we_tot_svc = _parse_regionnamed_patterns(tot_path('Service', 'weekday'), tot_path('Service', 'weekend'), region, year)
    service_total = _replicate_monthly_patterns(wd_tot_svc, we_tot_svc, year)
    svc_sum = sum(service_series.values())
    service_other = service_total - svc_sum
    service_other = service_other.clip(lower=0)
    service_series['service_other'] = service_other
    service_series['service_total'] = service_total

    # Industry total
    wd_ind, we_ind = _parse_regionnamed_patterns(tot_path('Industry', 'weekday'), tot_path('Industry', 'weekend'), region, year)
    industry_series = _replicate_monthly_patterns(wd_ind, we_ind, year)

    # Transport total (no scenario suffix)
    wd_tr, we_tr = _parse_regionnamed_patterns(tot_path('Transport', 'weekday'), tot_path('Transport', 'weekend'), region, year)
    transport_series = _replicate_monthly_patterns(wd_tr, we_tr, year)

    # Construct DataFrame
    df = pd.DataFrame({
        **residential_series,
        **service_series,
        'industry': industry_series,
        'transport': transport_series,
    })
    # Sector totals for industry and transport
    df['industry_total'] = industry_series
    df['transport_total'] = transport_series
    # Compute overall load
    df['load'] = df['residential_total'] + df['service_total'] + industry_series + transport_series
    df.index.name = 'timestamp'
    return df


def load_local_demand_series(
    csv_path: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    timezone: Optional[str] = None,
    name: Optional[str] = None,
) -> pd.Series:
    """Read an observed hourly demand series from a local CSV.

    Alternative to :func:`fetch_demand_data_demandcast` for countries whose
    best available demand record is a staged file rather than a DemandCast
    source. Enabled per country with the ``demand_series_csv`` preset key.

    The CSV must have a timestamp column (``timestamp``/``time``/``datetime``,
    or the first column) holding **local** wall-clock time for the country, and
    a demand column (``demand_mw``/``demand``/``load_mw``/``value``, or the
    second column) in **MW**. Returned tz-aware in ``timezone`` so the series
    is interchangeable with the DemandCast return value; ambiguous or
    nonexistent local times (DST transitions) are resolved forward, which is a
    no-op for countries that do not observe DST.

    Parameters
    ----------
    csv_path : str
        Path to the CSV. Relative paths resolve against the repo root.
    start_year, end_year : int, optional
        Inclusive calendar-year filter, matching the DemandCast fetcher.
    timezone : str, optional
        IANA timezone of the timestamps. ``None`` leaves the index naive.
    name : str, optional
        Name for the returned Series (typically the ISO-3 country code).
    """
    path = csv_path if os.path.isabs(csv_path) else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), csv_path)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"demand_series_csv points at '{csv_path}', which does not exist "
            f"(resolved to '{path}')."
        )
    df = pd.read_csv(path)
    if df.shape[1] < 2:
        raise ValueError(f"'{path}' needs at least a timestamp and a demand column.")
    lowered = {str(c).strip().lower(): c for c in df.columns}
    ts_col = next(
        (lowered[c] for c in ('timestamp', 'time', 'datetime', 'date') if c in lowered),
        df.columns[0],
    )
    val_col = next(
        (lowered[c] for c in ('demand_mw', 'demand', 'load_mw', 'load', 'value') if c in lowered),
        df.columns[1],
    )
    stamps = pd.DatetimeIndex(pd.to_datetime(df[ts_col], errors='coerce'))
    values = pd.to_numeric(df[val_col], errors='coerce')
    series = pd.Series(values.to_numpy(), index=stamps, name=name or val_col)
    series = series[series.index.notna()].dropna().sort_index()
    series = series[~series.index.duplicated(keep='first')]
    if timezone:
        if series.index.tz is None:
            series.index = series.index.tz_localize(
                timezone, ambiguous=True, nonexistent='shift_forward')
        else:
            series.index = series.index.tz_convert(timezone)
    if start_year is not None:
        series = series[series.index.year >= start_year]
    if end_year is not None:
        series = series[series.index.year <= end_year]
    if series.empty:
        raise ValueError(
            f"'{path}' contains no hourly demand rows in {start_year}–{end_year}."
        )
    return series


def fetch_demand_data_demandcast(
    country_code: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    data_dir: Optional[str] = None,
) -> pd.Series:
    """Fetch historical hourly electricity demand using DemandCast.

    This helper wraps the DemandCast retrieval machinery to download
    high‑resolution electricity demand data from open sources defined in
    the `awesome‑electricity‑demand` repository.  DemandCast exposes
    retrieval modules for numerous countries and grid operators; this
    function automatically selects an appropriate data source based on
    the provided ISO Alpha‑3 country code.  It returns a pandas
    ``Series`` indexed by timezone‑aware timestamps (local time) with
    values in megawatts (MW).

    Parameters
    ----------
    country_code : str
        ISO Alpha‑3 code of the country (e.g. ``'USA'`` for the United
        States or ``'CAN_AB'`` for a Canadian subdivision).  Codes are
        case‑insensitive.  If a subdivision code is provided after an
        underscore, the function will retrieve data for that
        subdivision.
    start_year, end_year : int, optional
        Limit the returned series to the inclusive range of calendar
        years.  If either is ``None`` no filtering is applied.  For
        example, ``start_year=2022, end_year=2024`` will return only
        values from 1 January 2022 through 31 December 2024.

    Returns
    -------
    pandas.Series
        Time series of hourly electricity demand (MW) indexed by
        timezone‑aware timestamps.  If no data source is available for
        the specified code, or if the DemandCast package is not
        installed, an exception will be raised.

    Notes
    -----
    DemandCast is an external project developed by Open Energy
    Transition to retrieve and forecast electricity demand worldwide.
    Historical demand is sourced from public datasets curated in the
    `awesome‑electricity‑demand` repository【97645308504532†L172-L189】.
    To use this function you must install DemandCast and its
    dependencies (see https://github.com/open-energy-transition/demandcast).
    At runtime, the function imports DemandCast modules on demand;
    failure to import will result in an ``ImportError`` with guidance.
    Some data sources (such as ENTSO‑E) require API keys set via
    environment variables; if these are missing an informative
    exception will be raised by the underlying retrieval module.  In
    such cases you may need to provide credentials or choose a
    different data source.
    """
    # Normalise the country code (uppercase and strip whitespace)
    code = country_code.strip().upper()
    if code == 'USA':
        eia_start_year = start_year or 2020
        eia_end_year = end_year or _datetime.datetime.now().year
        series = _fetch_eia_us_national_series(
            start_year=eia_start_year,
            end_year=eia_end_year,
        )
        if start_year is not None:
            series = series[series.index >= pd.Timestamp(start_year, 1, 1, tz='UTC')]
        if end_year is not None:
            series = series[series.index <= pd.Timestamp(end_year, 12, 31, 23, tz='UTC')]
        return series
    try:
        demandcast_root = ensure_demandcast_source()
    except Exception as inner_e:
        raise ImportError(
            "DemandCast could not be imported or bootstrapped locally. "
            "Install its dependencies or provide a pre-downloaded demand series "
            "to enable automatic demand retrieval."
        ) from inner_e

    # Mirror manually-staged demand files from the canonical
    # data/manual_downloads/ folder into the DemandCast clone, so users only
    # need to maintain one copy. Best-effort: any failure (missing folder,
    # permission denied, etc.) is silently ignored so that DemandCast can
    # raise its own clearer "file not found" error if it actually needs them.
    try:
        _sync_manual_downloads_to_demandcast(
            data_dir or DEFAULT_DATA_DIR, demandcast_root,
        )
    except Exception:
        pass

    # Identify available data sources for the given code
    sources = _find_demandcast_sources_containing_code(demandcast_root, code)
    if not sources:
        raise ValueError(
            f"No electricity demand data sources are available for code '{code}'. "
            "Check the DemandCast documentation or specify a subdivision code if available."
        )

    last_error: Optional[Exception] = None
    # Try each data source in order until successful
    for source in sources:
        try:
            series = _retrieve_demandcast_series_from_source(demandcast_root, source, code)
            # Successful retrieval; break out of loop
            break
        except Exception as err:
            last_error = err
            series = None
            continue
    else:
        # None of the sources succeeded
        raise RuntimeError(
            f"Failed to retrieve demand data for '{code}' from any DemandCast source. "
            f"Last error: {last_error}"
        )

    # Optionally filter by year range
    if start_year is not None or end_year is not None:
        start = pd.Timestamp(start_year, 1, 1, tz=series.index.tz) if start_year else None
        end = pd.Timestamp(end_year, 12, 31, 23, tz=series.index.tz) if end_year else None
        if start is not None:
            series = series[series.index >= start]
        if end is not None:
            series = series[series.index <= end]

    return series


###############################################################################
# Zapata-based calibration  (Zapata et al., Energy 258 (2022) 124741)
#
# Implementation notes:
#   * The four "climate-sensitive" end-uses (residential cooling, residential
#     heating, residential lighting, service cooling) are REGENERATED from
#     country-specific weather + occupancy + Forsythe daylength using the
#     verbatim closed-form equations from the paper's online supplementary.
#   * The other seven Mendeley end-uses keep their empirical hourly patterns;
#     the paper says their HOURLY variation is empirical-not-stylized.
#   * Calibration to observed totals is done via monthly non-negative least
#     squares (NNLS) on the hybrid basis.
#
# See ``zapata_implementation_readme.md`` for the full methodology write-up,
# equation references, and result comparison. Treat the constants below
# (×7, /17.9, /12.43, etc.) as Zapata-fit against European/USA empirical
# data; applying them unchanged to any new country inherits that bias.
###############################################################################

# Reference temperature for cooling- and heating-degree-hours.
ZAPATA_REF_TEMP_C = 18.0

# Climate-sensitive end-uses with stylized hourly functions per Zapata.
ZAPATA_CLIMATE_SENSITIVE_COLS = (
    'residential_cooling',
    'residential_heating',
    'residential_lighting',
    'service_cooling',
)

# HETUS-style hourly occupancy profiles (hand-tuned approximations of paper
# Fig. 3). Four profiles per sector: active/total × weekday/weekend.
ZAPATA_RES_ACTIVE_WEEKDAY = np.array([
    0.03, 0.02, 0.02, 0.02, 0.03, 0.10,
    0.35, 0.55, 0.50, 0.40, 0.32, 0.30,
    0.32, 0.30, 0.28, 0.30, 0.45, 0.65,
    0.80, 0.88, 0.85, 0.65, 0.35, 0.10,
])
ZAPATA_RES_ACTIVE_WEEKEND = np.array([
    0.05, 0.03, 0.03, 0.03, 0.04, 0.07,
    0.18, 0.40, 0.60, 0.70, 0.72, 0.72,
    0.68, 0.65, 0.62, 0.65, 0.70, 0.78,
    0.85, 0.88, 0.85, 0.70, 0.45, 0.20,
])
ZAPATA_RES_TOTAL_WEEKDAY = np.array([
    0.97, 0.98, 0.99, 0.99, 0.99, 0.97,
    0.90, 0.78, 0.55, 0.40, 0.30, 0.28,
    0.32, 0.30, 0.28, 0.30, 0.45, 0.65,
    0.85, 0.93, 0.96, 0.97, 0.97, 0.97,
])
ZAPATA_RES_TOTAL_WEEKEND = np.array([
    0.97, 0.98, 0.98, 0.98, 0.98, 0.97,
    0.92, 0.85, 0.75, 0.80, 0.82, 0.82,
    0.80, 0.78, 0.78, 0.80, 0.82, 0.85,
    0.92, 0.95, 0.96, 0.97, 0.96, 0.96,
])
ZAPATA_SVC_WEEKDAY = np.array([
    0.05, 0.05, 0.05, 0.05, 0.05, 0.10,
    0.30, 0.60, 0.85, 0.95, 0.98, 0.95,
    0.85, 0.90, 0.95, 0.93, 0.85, 0.65,
    0.40, 0.20, 0.10, 0.08, 0.05, 0.05,
])
ZAPATA_SVC_WEEKEND = np.array([
    0.03, 0.03, 0.03, 0.03, 0.03, 0.05,
    0.10, 0.18, 0.25, 0.32, 0.38, 0.40,
    0.40, 0.38, 0.35, 0.30, 0.25, 0.18,
    0.12, 0.08, 0.05, 0.04, 0.03, 0.03,
])


def _zapata_forsythe_daylength_hours(latitude_deg: float, day_of_year: int) -> float:
    """Forsythe et al. (1995) daylength formula (paper ref [59])."""
    import math as _math
    lat_rad = _math.radians(latitude_deg)
    P = _math.asin(
        0.39795 * _math.cos(
            0.2163108 + 2 * _math.atan(0.9671396 * _math.tan(0.00860 * (day_of_year - 186)))
        )
    )
    arg = (
        (_math.sin(_math.radians(0.8333)) + _math.sin(lat_rad) * _math.sin(P))
        / (_math.cos(lat_rad) * _math.cos(P))
    )
    if arg > 1.0:
        return 0.0
    if arg < -1.0:
        return 24.0
    return 24.0 - (24.0 / _math.pi) * _math.acos(arg)


def _zapata_forsythe_irradiance_pattern_24h(
    latitude_deg: float, day_of_year: int,
) -> np.ndarray:
    """Synthetic 24h irradiance pattern: half-sinus from sunrise to sunset,
    centred at 12:30 local. Per paper Section 2.1.2 (p. 5), used as BP for
    residential lighting instead of measured irradiance."""
    import math as _math
    D = _zapata_forsythe_daylength_hours(latitude_deg, day_of_year)
    if D <= 0:
        return np.zeros(24)
    if D >= 24:
        return np.ones(24)
    sunrise = 12.5 - D / 2.0
    sunset = 12.5 + D / 2.0
    pattern = np.zeros(24)
    for h in range(24):
        h_mid = h + 0.5
        if sunrise < h_mid < sunset:
            pattern[h] = _math.sin(_math.pi * (h_mid - sunrise) / D)
    return pattern


# ---------- Stylized functions f_e (Zapata 2022 supplementary, verbatim) ----------

def _zapata_residential_lighting(
    occ_active: np.ndarray, irr_pattern: np.ndarray,
) -> np.ndarray:
    """Eq. 3 (supplementary):
        Lighting = (AO + 0.15) / min(1, max(0.3, I/0.4))
    """
    denom = np.minimum(1.0, np.maximum(0.3, irr_pattern / 0.4))
    return (occ_active + 0.15) / denom


def _zapata_residential_heating(
    occ_active: np.ndarray, hdh: np.ndarray,
    hours: np.ndarray, is_weekend: np.ndarray,
) -> np.ndarray:
    """Eqs. 4 (supplementary), weekday and weekend variants with morning-peak window."""
    weekday_morning = (~is_weekend) & (hours >= 5) & (hours <= 10)
    weekend_morning = is_weekend & (hours >= 5) & (hours <= 12)
    morning = weekday_morning | weekend_morning
    ao_term = np.where(
        morning,
        np.maximum(0.01, occ_active + 0.4),
        np.maximum(0.01, occ_active),
    )
    weekend_offpeak = is_weekend & ~weekend_morning
    hdh_scaled = np.where(weekend_offpeak, 1.1 * hdh / 17.9, hdh / 17.9)
    hdh_term = np.maximum(0.6, hdh_scaled)
    return ao_term + hdh_term


def _zapata_residential_cooling(
    occ_total: np.ndarray, cdh: np.ndarray,
) -> np.ndarray:
    """Residential AC (supplementary, unnumbered):  HO × max(0.01, CDH × 7)."""
    return occ_total * np.maximum(0.01, cdh * 7.0)


def _zapata_service_cooling(
    occ_svc: np.ndarray, cdh: np.ndarray, is_weekend: np.ndarray,
) -> np.ndarray:
    """Eqs. 8 & 9 (supplementary):
        Weekday: CDH/12.43 + 0.5 + 0.6 × OCC
        Weekend: CDH/12.43 + 0.5 + 0.2 × OCC
    """
    occ_scale = np.where(is_weekend, 0.2, 0.6)
    return cdh / 12.43 + 0.5 + occ_scale * occ_svc


def _zapata_broadcast_occupancy(
    profile_weekday: np.ndarray, profile_weekend: np.ndarray,
    hours: np.ndarray, is_weekend: np.ndarray,
) -> np.ndarray:
    """Pick the right HETUS profile per hour based on day-of-week."""
    return np.where(is_weekend, profile_weekend[hours], profile_weekday[hours])


def _zapata_weather_for_year(
    weather_naive: pd.DataFrame,
    target_year: int,
    mendeley_index: pd.DatetimeIndex,
) -> Tuple[pd.DataFrame, int, bool]:
    """Return weather aligned to the Mendeley target-year calendar for the
    Zapata basis, falling back to a proxy year when the target is out of range.

    The Renewables.ninja weather archive ends in a fixed year (currently 2024),
    but non-US presets can target a later year (e.g. South Korea's 2025). The
    Zapata regeneration only needs a representative weather *year* for the
    climate-sensitive shape, so when the target year is not fully covered we use
    the most recent full weather year and relabel its calendar to the target
    year (matching by month/day/hour). Years already in the archive (e.g. China
    2018) resolve to themselves and are unaffected.

    Parameters
    ----------
    weather_naive : DataFrame
        Weather on a naive (tz-stripped) local-time hourly index spanning many
        years (must include a ``temperature`` column).
    target_year : int
        The run's target year (the Mendeley demand-shape year).
    mendeley_index : DatetimeIndex
        The Mendeley target-year hourly index to align onto.

    Returns
    -------
    (DataFrame, int, bool)
        Weather reindexed to ``mendeley_index``; the source weather year used;
        and whether a proxy year was substituted (True) or the target year was
        used directly (False).
    """
    yr_counts = weather_naive.index.year.value_counts()
    full_years = sorted(y for y, n in yr_counts.items() if n >= 8760)
    if not full_years:
        raise ValueError(
            "No full weather year available to build the Zapata basis "
            f"(archive years: {sorted(int(y) for y in yr_counts.index)})."
        )
    if target_year in full_years:
        src_year, relabeled = int(target_year), False
    else:
        earlier = [y for y in full_years if y <= target_year]
        src_year, relabeled = int(earlier[-1] if earlier else full_years[-1]), True

    src = weather_naive[weather_naive.index.year == src_year]
    # Align by (month, day, hour) so the proxy year maps onto the target-year
    # calendar regardless of leap-year differences.
    src_keyed = src.set_axis(
        pd.MultiIndex.from_arrays([src.index.month, src.index.day, src.index.hour])
    )
    mkey = list(zip(mendeley_index.month, mendeley_index.day, mendeley_index.hour))
    out = src_keyed.reindex(mkey)
    out.index = mendeley_index
    if out['temperature'].isna().any():
        # Residual gap only if the target calendar has a day the proxy lacks
        # (e.g. a leap-day target against a non-leap proxy). Fill smoothly.
        out = out.interpolate(method='time', limit_direction='both').ffill().bfill()
    return out, src_year, relabeled


def build_zapata_hybrid_basis(
    mendeley_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    latitude_deg: float,
) -> pd.DataFrame:
    """Assemble the Zapata hybrid basis: 4 climate-sensitive columns
    regenerated from weather + occupancy + Forsythe daylength, plus the
    other 7 Mendeley end-uses kept as empirical patterns.

    Both inputs must be on the SAME naive (local-time) hourly index. Returns
    a DataFrame indexed identically with all 11 end-use columns plus a
    ``load`` column = sum across end-uses.

    Parameters
    ----------
    mendeley_df : DataFrame
        Output of ``load_enduse_data_mendeley`` for the target year and
        region (naive hourly index, local time).
    weather_df : DataFrame
        Hourly weather DataFrame with at least a ``temperature`` column
        (°C). Index must align with ``mendeley_df.index`` after stripping
        timezone information.
    latitude_deg : float
        Latitude used for the Forsythe daylength term (degrees, +N).
    """
    if 'temperature' not in weather_df.columns:
        raise KeyError(
            "build_zapata_hybrid_basis requires weather_df['temperature']; "
            f"got columns {list(weather_df.columns)}."
        )

    # Align weather to Mendeley index (drop tz if present). Both should be
    # the same local-time naive hourly grid by the caller's contract.
    w = weather_df.copy()
    if getattr(w.index, 'tz', None) is not None:
        w.index = w.index.tz_localize(None)
    w = w.reindex(mendeley_df.index)
    if w['temperature'].isna().any():
        raise ValueError(
            "weather_df cannot be aligned to mendeley_df index without NaN "
            "after reindex — caller must ensure both cover the same year "
            "and use matching naive local-time hour-beginning indices."
        )

    idx = mendeley_df.index
    temp_C = w['temperature'].to_numpy(dtype=float)
    hours = (idx.hour.to_numpy() if hasattr(idx.hour, 'to_numpy')
             else np.asarray(idx.hour))
    days = (idx.dayofyear.to_numpy() if hasattr(idx.dayofyear, 'to_numpy')
            else np.asarray(idx.dayofyear))
    is_weekend = idx.dayofweek.to_numpy() >= 5

    occ_res_total = _zapata_broadcast_occupancy(
        ZAPATA_RES_TOTAL_WEEKDAY, ZAPATA_RES_TOTAL_WEEKEND, hours, is_weekend,
    )
    occ_res_active = _zapata_broadcast_occupancy(
        ZAPATA_RES_ACTIVE_WEEKDAY, ZAPATA_RES_ACTIVE_WEEKEND, hours, is_weekend,
    )
    occ_svc = _zapata_broadcast_occupancy(
        ZAPATA_SVC_WEEKDAY, ZAPATA_SVC_WEEKEND, hours, is_weekend,
    )

    CDH = np.maximum(temp_C - ZAPATA_REF_TEMP_C, 0.0)
    HDH = np.maximum(ZAPATA_REF_TEMP_C - temp_C, 0.0)

    # Forsythe irradiance pattern, cached by day-of-year.
    pattern_by_doy = {
        int(d): _zapata_forsythe_irradiance_pattern_24h(latitude_deg, int(d))
        for d in np.unique(days)
    }
    irr_pattern_hourly = np.asarray([
        pattern_by_doy[int(d)][int(h)] for d, h in zip(days, hours)
    ], dtype=float)

    basis = mendeley_df.copy()
    basis['residential_cooling'] = _zapata_residential_cooling(occ_res_total, CDH)
    basis['residential_heating'] = _zapata_residential_heating(
        occ_res_active, HDH, hours, is_weekend,
    )
    basis['residential_lighting'] = _zapata_residential_lighting(
        occ_res_active, irr_pattern_hourly,
    )
    basis['service_cooling'] = _zapata_service_cooling(occ_svc, CDH, is_weekend)

    # Recompute totals and load = sum of end-use components.
    basis = _recompute_enduse_totals(basis)
    return basis


def calibrate_via_monthly_nnls(
    basis_df: pd.DataFrame,
    real_series: pd.Series,
    end_use_cols: Iterable[str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Solve monthly NNLS to find non-negative end-use weights that best
    fit observed totals. Returns:

      * a calibrated DataFrame with the same end-use columns as ``basis_df``,
        each scaled by its NNLS weight for that hour's month; plus a
        recomputed ``load`` column = sum of calibrated components.
      * a weights DataFrame with columns 'month', 'hours_in_month',
        'residual_norm_mw', and one column per end-use.

    The function expects ``basis_df.index`` to be naive local-time hourly
    and ``real_series`` to cover the same period (caller should align
    them first; the function does an inner-join on indices for safety).
    """
    from scipy.optimize import nnls as _nnls

    end_use_cols = list(end_use_cols)
    missing = [c for c in end_use_cols if c not in basis_df.columns]
    if missing:
        raise KeyError(f"basis_df missing end-use columns: {missing}")

    # Align: strip tz info on the real series if present, then inner-join
    # on index.
    rs = real_series.copy()
    if getattr(rs.index, 'tz', None) is not None:
        rs.index = rs.index.tz_localize(None)
    rs = rs.groupby(rs.index).mean().sort_index()

    common = basis_df.index.intersection(rs.index)
    if len(common) == 0:
        raise ValueError(
            "No overlapping timestamps between basis_df and real_series for NNLS."
        )

    X_full = basis_df.loc[common, end_use_cols].astype(float)
    y_full = rs.loc[common].astype(float)
    months = pd.Series(common, index=common).dt.month

    weights_rows: list[Dict[str, Any]] = []
    monthly_weights: Dict[int, np.ndarray] = {}
    for month, idx_in_month in months.groupby(months).groups.items():
        X = X_full.loc[idx_in_month].to_numpy()
        y = y_full.loc[idx_in_month].to_numpy()
        if X.size == 0 or y.size == 0:
            continue
        w, residual_norm = _nnls(X, y)
        monthly_weights[int(month)] = w
        weights_rows.append({
            'month': int(month),
            'hours_in_month': int(len(idx_in_month)),
            'residual_norm_mw': float(residual_norm),
            **{col: float(w_i) for col, w_i in zip(end_use_cols, w)},
        })
    weights_df = pd.DataFrame(weights_rows)

    # Apply weights to the FULL basis_df. For each (month, end-use) pair,
    # multiply the basis_df column by the NNLS weight for that month. Hours
    # in a month with no NNLS solve (real_series didn't cover it) get 0.0;
    # caller should warn in that case rather than fabricating values.
    #
    # IMPORTANT: do NOT fall back to the raw basis_df value when the NNLS
    # weight is zero — NNLS can legitimately produce a zero weight, and
    # falling back to the unscaled basis (which may be in Mendeley raw
    # units ~1e8) would massively inflate the output. The correct
    # interpretation of a zero weight is "this end-use contributes nothing
    # this month," and the calibrated column should reflect that.
    calibrated = basis_df.copy()
    basis_months = pd.Series(basis_df.index, index=basis_df.index).dt.month.values
    for col_idx, col in enumerate(end_use_cols):
        # Map each hour's month → weight (0.0 if month not in monthly_weights)
        weight_for_hour = np.asarray([
            monthly_weights.get(int(m), np.zeros(len(end_use_cols)))[col_idx]
            for m in basis_months
        ], dtype=float)
        calibrated[col] = basis_df[col].astype(float).to_numpy() * weight_for_hour

    calibrated = _recompute_enduse_totals(calibrated)
    return calibrated, weights_df


# ============================================================================
# Path B — EPS-anchored ridge NNLS calibration
# ----------------------------------------------------------------------------
# Background: the production zapata_nnls method (Path A) suffers from
# basis-collinearity zero-flips. NNLS picks one column as a "flat baseload"
# stand-in and zeros others in some months, producing NaN/0 cells in the
# SHELF output (e.g. industry shape goes to 0 in winter/spring for China,
# which then propagates as zero industrial hourly demand in those timeslices
# when EPS consumes the SHELF).
#
# Ridge regularization fixes this by adding a soft prior that each end-use's
# weight should stay close to 1.0 (in aligned-column units). The prior comes
# from a country-specific EPS BAU sectoral demand extract — see
# data/eps_priors/ for the extraction methodology. Because EPS itself
# provides the magnitudes that get multiplied by SHELF shapes downstream,
# anchoring our basis to EPS's own per-end-use magnitudes makes the entire
# pipeline self-consistent with how its output will be consumed.
#
# Key insight (verified by reading EPS.mdl line 12716-12749): SHELF files
# in EPS are SHAPE ONLY — header reads "Unit: dimensionless (ratio of
# electricity demand in this hour to annual demand)". EPS multiplies them
# by BAU [Sector] Electricity Demand internally. So the role of the
# magnitude alignment is purely to make NNLS well-conditioned, not to
# ensure correct magnitudes in the final output (those come from EPS).
# ============================================================================

def load_eps_magnitude_prior(
    prior_csv_path: str,
    target_year: int,
) -> Dict[str, float]:
    """Load per-end-use MWh/year magnitudes from an EPS BAU prior CSV.

    The CSV must have columns ``end_use``, ``year``, ``eps_mwh_per_year``
    (long format). Produced by ``data/eps_priors/parse_eps_extract.py``
    against the country's EPS Vensim run.

    Parameters
    ----------
    prior_csv_path : str
        Path to the EPS prior CSV (per-country, e.g.
        ``data/eps_priors/eps_prior_CN.csv``).
    target_year : int
        Calibration year. If the EPS run does not cover this year, the
        nearest available year is used (with a printed warning).

    Returns
    -------
    Dict[str, float]
        Mapping {end_use_name: MWh_per_year_for_target_year}.
    """
    if not os.path.exists(prior_csv_path):
        raise FileNotFoundError(
            f"EPS prior CSV not found: {prior_csv_path}. Run "
            "data/eps_priors/parse_eps_extract.py against the country's "
            "EPS Vensim output first."
        )
    # comment='#' skips the provenance header written by
    # data/eps_priors/parse_eps_extract.py (source model, version, git commit,
    # extraction date). Open the CSV to see which model snapshot this is.
    df = pd.read_csv(prior_csv_path, comment='#')
    required = {'end_use', 'year', 'eps_mwh_per_year'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"EPS prior CSV {prior_csv_path} missing columns: {missing}"
        )
    available_years = sorted(df['year'].unique())
    if target_year in available_years:
        used_year = target_year
    else:
        used_year = min(available_years, key=lambda y: abs(y - target_year))
        print(
            f"[eps-prior] WARNING: target year {target_year} not in EPS prior "
            f"(available {min(available_years)}-{max(available_years)}); "
            f"using nearest year {used_year}"
        )
    yr_df = df[df['year'] == used_year]
    return {row['end_use']: float(row['eps_mwh_per_year']) for _, row in yr_df.iterrows()}


def align_basis_to_prior(
    basis_df: pd.DataFrame,
    prior: Dict[str, float],
    end_use_cols: Iterable[str],
    verbose: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Per-column rescale ``basis_df`` so each end-use's annual MEAN matches
    the EPS prior MWh/year converted to MW (MWh/yr ÷ 8760).

    After alignment, every aligned column has mean ≈ target_mean_MW, so a
    ridge-prior weight of 1.0 on each column is meaningful: w=1 reproduces
    the EPS prior's relative share, w!=1 means NNLS overrode the prior.

    End-uses present in ``end_use_cols`` but not in ``prior`` are left
    unscaled (with a warning).

    Returns
    -------
    aligned_df : DataFrame
        Copy of basis_df with the end-use columns rescaled.
    scale_factors : Dict[str, float]
        The per-column multiplier applied (target_mean / current_mean).
    """
    hours_per_year = 8760.0
    end_use_cols = list(end_use_cols)
    aligned = basis_df.copy()
    scale_factors: Dict[str, float] = {}

    # Fallback magnitude for columns NOT in the EPS prior (e.g. waterheating,
    # which EPS folds into 'appliances' or 'other component' and doesn't track
    # separately). Use the median of the priored targets — keeps the column
    # at a comparable magnitude so ridge NNLS treats it on the same footing
    # as the other end-uses rather than letting its raw Mendeley magnitude
    # (which can be 10⁸×) dominate the basis.
    prior_means_mw = [v / hours_per_year for v in prior.values() if v > 0]
    fallback_target_mw = float(np.median(prior_means_mw)) if prior_means_mw else 1.0

    if verbose:
        print(f"[eps-prior] aligning {len(end_use_cols)} basis columns to EPS magnitudes:")
        print(f"[eps-prior]   fallback magnitude for no-prior columns: "
              f"{fallback_target_mw:,.4g} MW (median of priored targets)")
        print(f"  {'end_use':<26} {'current_mean':>14} {'target_mean_MW':>16} {'scale':>14}")

    for col in end_use_cols:
        if col not in basis_df.columns:
            continue
        current_mean = float(pd.to_numeric(basis_df[col], errors='coerce').mean())
        if col not in prior:
            # No EPS prior: scale to the fallback magnitude so this column
            # doesn't dominate the basis with its raw Mendeley units.
            target_mean_mw = fallback_target_mw
            label = '<fallback>'
        else:
            target_mean_mw = prior[col] / hours_per_year
            label = None
        if current_mean <= 0:
            if verbose:
                print(f"  {col:<26} {current_mean:>14.4g} {target_mean_mw:>16.4g} "
                      f"{'<degenerate>':>14}")
            scale_factors[col] = 1.0
            continue
        s = target_mean_mw / current_mean
        aligned[col] = basis_df[col].astype(float) * s
        scale_factors[col] = s
        if verbose:
            scale_str = label if label else f"{s:.4g}"
            print(f"  {col:<26} {current_mean:>14.4g} {target_mean_mw:>16.4g} {scale_str:>14}")

    aligned = _recompute_enduse_totals(aligned)
    return aligned, scale_factors


def calibrate_via_monthly_ridge_nnls(
    basis_df: pd.DataFrame,
    real_series: pd.Series,
    end_use_cols: Iterable[str],
    lambda_ridge: float = 1.0,
    prior_weights: Optional[Dict[str, float]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Solve monthly RIDGE NNLS with a per-end-use prior anchor.

    Mathematically: for each month, solve

        min  ||X·w - y||² + lambda * ||w - w_prior||²    s.t.  w >= 0

    via stacked NNLS on

        X' = [X; sqrt(lambda) * I]
        y' = [y; sqrt(lambda) * w_prior]

    where I is the identity and w_prior is the per-end-use prior weight
    vector (defaults to 1.0 for every column, which assumes basis_df has
    been pre-aligned to a magnitude prior via ``align_basis_to_prior``).

    Parameters
    ----------
    basis_df : DataFrame
        Hourly basis matrix (T × n_end_uses). Should be pre-aligned to a
        magnitude prior so that w=1 is a meaningful anchor.
    real_series : Series
        Observed total electricity demand (MW), naive local time index.
    end_use_cols : iterable of str
        Column names in basis_df to use as the end-use basis.
    lambda_ridge : float, default 1.0
        Ridge strength. 0.0 reduces to plain NNLS; larger values pull
        weights more strongly toward ``prior_weights``.
    prior_weights : Dict[str, float] or None
        Per-end-use prior weight (default 1.0 for all).

    Returns
    -------
    calibrated_df : DataFrame
        basis_df with each end-use column scaled by its (month, end-use)
        ridge-NNLS weight, plus recomputed ``load`` = sum of end-uses.
    weights_df : DataFrame
        Per-month diagnostic: monthly residual norm, prior deviation,
        and one column per end-use weight.
    """
    from scipy.optimize import nnls as _nnls

    end_use_cols = list(end_use_cols)
    missing = [c for c in end_use_cols if c not in basis_df.columns]
    if missing:
        raise KeyError(f"basis_df missing end-use columns: {missing}")

    if prior_weights is None:
        prior_weights = {col: 1.0 for col in end_use_cols}
    w_prior = np.asarray(
        [float(prior_weights.get(col, 1.0)) for col in end_use_cols], dtype=float,
    )

    # Align real series to basis index (strip tz if present)
    rs = real_series.copy()
    if getattr(rs.index, 'tz', None) is not None:
        rs.index = rs.index.tz_localize(None)
    rs = rs.groupby(rs.index).mean().sort_index()
    common = basis_df.index.intersection(rs.index)
    if len(common) == 0:
        raise ValueError(
            "No overlapping timestamps between basis_df and real_series for ridge NNLS."
        )

    X_full = basis_df.loc[common, end_use_cols].astype(float)
    y_full = rs.loc[common].astype(float)
    months = pd.Series(common, index=common).dt.month

    n_e = len(end_use_cols)

    # Per-month per-column effective lambda. ``lambda_ridge`` is dimensionless
    # ("how much do I trust the EPS prior vs the data fit?"). 1.0 means "equal
    # weight per residual entry"; >1 = trust prior more; <1 = trust data more.
    #
    # Without scaling, the data block has T_month ≈ 720 residual entries in
    # MW² while the ridge block has n_e ≈ 11 in dimensionless w-space — that's
    # an automatic 65× advantage for the data plus the magnitude mismatch
    # between MW residuals and unit-scale prior deviations. To make
    # `lambda_ridge=1` actually mean "equal weight," we scale each ridge row
    # by `sigma_y * sqrt(T_month / n_e)` so each prior-residual entry has the
    # same expected squared magnitude as a data-residual entry.

    weights_rows: list[Dict[str, Any]] = []
    monthly_weights: Dict[int, np.ndarray] = {}
    for month, idx_in_month in months.groupby(months).groups.items():
        X = X_full.loc[idx_in_month].to_numpy()
        y = y_full.loc[idx_in_month].to_numpy()
        if X.size == 0 or y.size == 0:
            continue
        if lambda_ridge > 0:
            t_month = X.shape[0]
            # Use std of y to set the natural scale of a single residual MW
            # entry. clip to avoid division by zero in pathological cases.
            sigma_y = float(np.std(y))
            sigma_y = max(sigma_y, 1e-6)
            # Effective per-entry ridge scale that makes one prior-residual
            # entry have the same expected squared magnitude as one data
            # residual entry.
            effective_scale = sigma_y * float(np.sqrt(max(1.0, t_month / max(1, n_e))))
            sqrt_lambda = float(np.sqrt(lambda_ridge)) * effective_scale
            ridge_block_X = sqrt_lambda * np.eye(n_e)
            ridge_block_y = sqrt_lambda * w_prior
            X_aug = np.vstack([X, ridge_block_X])
            y_aug = np.concatenate([y, ridge_block_y])
            w, residual_norm = _nnls(X_aug, y_aug)
        else:
            w, residual_norm = _nnls(X, y)
        # Diagnostics: how close did the solver stay to the prior?
        prior_deviation = float(np.linalg.norm(w - w_prior))
        # Data-only fit residual (excluding the ridge block)
        data_residual = float(np.linalg.norm(X @ w - y))
        monthly_weights[int(month)] = w
        weights_rows.append({
            'month': int(month),
            'hours_in_month': int(len(idx_in_month)),
            'data_residual_mw': data_residual,
            'prior_deviation': prior_deviation,
            'augmented_residual': float(residual_norm),
            **{col: float(w_i) for col, w_i in zip(end_use_cols, w)},
        })
    weights_df = pd.DataFrame(weights_rows)

    # Apply weights to the FULL basis_df (zero for months not solved).
    calibrated = basis_df.copy()
    basis_months = pd.Series(basis_df.index, index=basis_df.index).dt.month.values
    for col_idx, col in enumerate(end_use_cols):
        weight_for_hour = np.asarray([
            monthly_weights.get(int(m), np.zeros(n_e))[col_idx]
            for m in basis_months
        ], dtype=float)
        calibrated[col] = basis_df[col].astype(float).to_numpy() * weight_for_hour

    calibrated = _recompute_enduse_totals(calibrated)
    return calibrated, weights_df


def calibrate_synthetic_load(
    df: pd.DataFrame,
    real_series: pd.Series,
    load_col: str,
    load_cols_to_scale: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Scale synthetic hourly load data to match real demand.

    This function adjusts the synthetic load and sectoral demands so that
    their aggregate matches the magnitude of observed historical load.
    It computes a simple multiplicative scaling factor based on the
    ratio of average real demand to average synthetic demand over the
    overlapping period.  The scaling is applied to the specified
    columns (typically the total load and each sector/end‑use column)
    while leaving generation and capacity factor columns unchanged.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame of synthetic hourly data produced by
        ``load_enduse_data_mendeley`` or equivalent.  Must be indexed
        by timestamps and contain at least the ``load_col`` used for
        total demand.
    real_series : pandas.Series
        Historical hourly electricity demand series (e.g. output of
        ``fetch_demand_data_demandcast``) indexed by timestamps.  The
        index must be timezone‑aware.  Values should represent MW or kW.
    load_col : str
        Name of the total load column in ``df``.  The scaling factor
        will be computed as the ratio of the mean of ``real_series`` to
        the mean of ``df[load_col]`` over the overlapping period.
    load_cols_to_scale : Iterable[str], optional
        List of column names in ``df`` to which the scaling factor
        should be applied.  If ``None``, all numeric columns in ``df``
        except those ending with ``'_cf'`` (capacity factors) or
        ``'_gen'`` (generation) will be scaled.

    Returns
    -------
    pandas.DataFrame
        A new DataFrame with scaled load and end‑use columns.  Columns
        not included in ``load_cols_to_scale`` are returned unchanged.

    Notes
    -----
    Scaling the synthetic load profiles ensures that the aggregate
    demand matches historical values.  This is important when using
    synthetic end‑use patterns for capacity expansion models that are
    calibrated to actual demand levels.  More sophisticated calibration
    methods (e.g. regression by hour or by month) can be implemented
    outside this function if needed.
    """
    if df.index.tz is None:
        # Align naive timestamps to the timezone of the real series if present
        tz = real_series.index.tz
        df = df.copy()
        df.index = df.index.tz_localize(tz)

    # Find overlapping period between synthetic and real data
    common_index = df.index.intersection(real_series.index)
    if common_index.empty:
        raise ValueError("No overlap between synthetic data and real demand series. "
                         "Ensure both series cover a common time period and share the same time zone.")

    # Compute average demand over the overlapping period
    real_mean = real_series.loc[common_index].mean()
    synthetic_mean = df.loc[common_index, load_col].mean()
    if synthetic_mean == 0 or np.isnan(synthetic_mean):
        raise ZeroDivisionError("Synthetic mean load is zero or NaN; cannot compute scaling factor.")
    scaling_factor = real_mean / synthetic_mean

    # Determine which columns to scale
    if load_cols_to_scale is None:
        # Scale all numeric columns except generation and capacity factor columns
        load_cols_to_scale = [
            col for col in df.columns
            if (np.issubdtype(df[col].dtype, np.number)
                and not col.endswith('_cf')
                and not col.endswith('_gen'))
        ]

    # Apply scaling
    df_scaled = df.copy()
    for col in load_cols_to_scale:
        df_scaled[col] = df_scaled[col] * scaling_factor

    return df_scaled


def _infer_enduse_columns(
    df: pd.DataFrame,
) -> Tuple[list[str], list[str], list[str]]:
    """Infer heating, cooling, and load-like columns from naming conventions."""
    numeric_cols = [
        col for col in df.columns
        if np.issubdtype(df[col].dtype, np.number)
    ]
    load_like_cols = [
        col for col in numeric_cols
        if not col.endswith('_cf') and not col.endswith('_gen')
    ]
    heating_cols = [col for col in load_like_cols if 'heating' in col.lower()]
    cooling_cols = [col for col in load_like_cols if 'cooling' in col.lower()]
    return heating_cols, cooling_cols, load_like_cols


def _recompute_enduse_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute sector totals and total load after end-use adjustments."""
    df = df.copy()
    residential_components = [
        col for col in [
            'residential_cooling',
            'residential_heating',
            'residential_lighting',
            'residential_waterheating',
            'residential_appliances',
            'residential_other',
        ]
        if col in df.columns
    ]
    if residential_components:
        df['residential_total'] = df[residential_components].sum(axis=1)

    service_components = [
        col for col in [
            'service_cooling',
            'service_heating',
            'service_waterheating',
            'service_other',
        ]
        if col in df.columns
    ]
    if service_components:
        df['service_total'] = df[service_components].sum(axis=1)

    if 'industry' in df.columns:
        df['industry_total'] = df['industry']
    if 'transport' in df.columns:
        df['transport_total'] = df['transport']

    total_cols = [
        col for col in [
            'residential_total',
            'service_total',
            'industry_total',
            'transport_total',
        ]
        if col in df.columns
    ]
    if total_cols:
        df['load'] = df[total_cols].sum(axis=1)

    return df


def calibrate_seasonal_enduse_load(
    df: pd.DataFrame,
    real_series: pd.Series,
    load_col: str = 'load',
    heating_cols: Optional[Iterable[str]] = None,
    cooling_cols: Optional[Iterable[str]] = None,
    winter_months: Optional[Iterable[int]] = None,
    summer_months: Optional[Iterable[int]] = None,
) -> pd.DataFrame:
    """Adjust synthetic end uses to better match real monthly and seasonal peaks."""
    if real_series.index.has_duplicates:
        real_series = real_series.groupby(real_series.index).mean().sort_index()

    if winter_months is None:
        winter_months = [11, 12, 1, 2]
    if summer_months is None:
        summer_months = [6, 7, 8]

    if df.index.tz is None:
        df = df.copy()
        df.index = df.index.tz_localize(real_series.index.tz)

    common_index = df.index.intersection(real_series.index)
    if common_index.empty:
        raise ValueError(
            "No overlap between synthetic data and real demand series. "
            "Ensure both series cover a common time period and share the same time zone."
        )

    if heating_cols is None or cooling_cols is None:
        inferred_heating, inferred_cooling, load_like_cols = _infer_enduse_columns(df)
        heating_cols = inferred_heating if heating_cols is None else list(heating_cols)
        cooling_cols = inferred_cooling if cooling_cols is None else list(cooling_cols)
    else:
        _, _, load_like_cols = _infer_enduse_columns(df)
        heating_cols = list(heating_cols)
        cooling_cols = list(cooling_cols)

    df_adj = df.copy()
    month_index = df_adj.loc[common_index].index.month
    real_monthly_mean = real_series.loc[common_index].groupby(month_index).mean()
    synthetic_monthly_mean = df_adj.loc[common_index, load_col].groupby(month_index).mean()
    monthly_factors = (real_monthly_mean / synthetic_monthly_mean.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    for month, factor in monthly_factors.items():
        mask = df_adj.index.month == month
        df_adj.loc[mask, load_like_cols] = df_adj.loc[mask, load_like_cols] * factor

    seasonal_specs = [
        (list(summer_months), cooling_cols),
        (list(winter_months), heating_cols),
    ]
    for months, target_cols in seasonal_specs:
        target_cols = [col for col in target_cols if col in df_adj.columns]
        if not target_cols:
            continue
        real_mask = real_series.loc[common_index].index.month.isin(months)
        synthetic_mask = df_adj.loc[common_index].index.month.isin(months)
        if not real_mask.any() or not synthetic_mask.any():
            continue
        real_peak = real_series.loc[common_index][real_mask].max()
        synthetic_peak = df_adj.loc[common_index, load_col][synthetic_mask].max()
        if synthetic_peak and not np.isnan(synthetic_peak):
            factor = real_peak / synthetic_peak
            month_mask = df_adj.index.month.isin(months)
            df_adj.loc[month_mask, target_cols] = df_adj.loc[month_mask, target_cols] * factor

    df_adj = _recompute_enduse_totals(df_adj)

    reconciled_monthly_mean = df_adj.loc[common_index, load_col].groupby(df_adj.loc[common_index].index.month).mean()
    final_monthly_factors = (real_monthly_mean / reconciled_monthly_mean.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    for month, factor in final_monthly_factors.items():
        mask = df_adj.index.month == month
        df_adj.loc[mask, load_like_cols] = df_adj.loc[mask, load_like_cols] * factor

    return _recompute_enduse_totals(df_adj)


def generate_timeslices_for_country(
    data_dir: str,
    region_name: str,
    country_code: str,
    year: int,
    calibration_start_year: Optional[int] = None,
    calibration_end_year: Optional[int] = None,
    gen_cols: Iterable[str] = (),
    cf_cols: Iterable[str] = (),
    n_clusters: int = 6,
    output_path: Optional[str] = None,
    load_cols: Optional[Iterable[str]] = None,
    scenario: str = 'SSP2',
    scale_all_numeric: bool = True,
    seasonal_calibration: bool = True,
    demand_shape_source: str = 'mendeley',
    efs_electrification: str = 'Reference',
    efs_technology_advancement: str = 'Moderate',
    mendeley_dataset_url: str = MENDELEY_DATASET_URL,
    mendeley_headers: Optional[Dict[str, str]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """High‑level workflow to generate timeslices for a given country.

    This convenience function ties together all steps: it loads synthetic
    hourly end‑use data from the Mendeley dataset, fetches real demand
    data using DemandCast, calibrates the synthetic profiles to match
    historical demand, computes net load, clusters hours into timeslices
    using k‑means, aggregates capacity factors and load factors, and
    optionally exports the results to an Excel workbook.  It is
    particularly useful when running the pipeline across multiple
    countries because it automates the calibration step and handles
    default file naming.

    Parameters
    ----------
    data_dir : str
        Directory containing the extracted Mendeley end‑use CSV files.
    region_name : str
        Name of the region in the Mendeley dataset (e.g. 'USA', 'Canada').
    country_code : str
        ISO Alpha‑3 country code (or code with subdivision) used by
        DemandCast to fetch real demand (e.g. 'USA', 'CAN_AB').
    year : int
        Year of the synthetic data to reconstruct (1971–2100).  This
        should align with the year used in the Mendeley dataset.
    calibration_start_year, calibration_end_year : int, optional
        Inclusive range of years over which to compute the average real
        demand for calibration.  If either is ``None`` the demand data
        will be returned without filtering.  Use a two‑ or three‑year
        period to smooth out year‑to‑year fluctuations.
    gen_cols : Iterable[str], default empty tuple
        Names of columns in the DataFrame representing variable
        generation (MW).  If provided, these columns will be subtracted
        from total load to compute net load.  Leave empty if no
        generation data are available.
    cf_cols : Iterable[str], default empty tuple
        Names of capacity factor columns (0–1).  These will be averaged
        over each timeslice.  If empty, capacity factor results will be
        an empty DataFrame.
    n_clusters : int, default 6
        Number of timeslices to generate via k‑means clustering.
    output_path : str, optional
        Path to save the Excel file.  If ``None`` a default name of
        ``<country_code>_timeslice_results.xlsx`` will be used in the
        current working directory.  Passing ``False`` will disable
        writing altogether.
    load_cols : Iterable[str], optional
        Columns representing end‑use loads to compute load factors.  If
        ``None``, all numeric columns in the synthetic DataFrame except
        generation and capacity factor columns will be used.
    scenario : str, default 'SSP2'
        Scenario identifier for loading aggregated Mendeley sector totals.
    scale_all_numeric : bool, default True
        If ``True``, scale all numeric columns (except generation and
        capacity factors) when calibrating.  If ``False``, only scale
        ``load_col`` and the columns provided in ``load_cols``.

    Returns
    -------
    capacity_factors : pandas.DataFrame
        Mean capacity factors by timeslice (empty if no ``cf_cols``).
    load_factors : pandas.DataFrame
        Load statistics by timeslice.
    labels : pandas.Series
        Timeslice labels for each hour.

    Notes
    -----
    This function is a wrapper around the lower‑level functions
    ``load_enduse_data_mendeley``, ``fetch_demand_data_demandcast``,
    ``calibrate_synthetic_load`` and ``run_pipeline``.  It assumes that
    DemandCast is installed and that data sources exist for the chosen
    country code.  If retrieval fails, an exception will be raised.
    """
    # Load the synthetic end‑use data for the chosen region and year
    demand_shape_source = str(demand_shape_source).strip().lower()
    mendeley_root = None
    if demand_shape_source in {'mendeley', 'efs'}:
        mendeley_root = ensure_mendeley_dataset(
            data_dir,
            dataset_url=mendeley_dataset_url,
            headers=mendeley_headers,
        )
    if demand_shape_source == 'efs':
        efs_zip_path = ensure_efs_dataset(os.path.join(os.path.dirname(os.path.abspath(data_dir)), 'efs'))
        df_synthetic = load_enduse_data_efs_us(
            efs_zip_path=efs_zip_path,
            requested_year=year,
            electrification=efs_electrification,
            technology_advancement=efs_technology_advancement,
            recs_workbook_path=DEFAULT_EPS_SHELF_WORKBOOK_PATH,
            split_template_root=mendeley_root,
            split_template_region=region_name,
            split_template_scenario=scenario,
        )
    elif demand_shape_source == 'mendeley':
        df_synthetic = load_enduse_data_mendeley(mendeley_root, region_name, year, scenario=scenario)
    else:
        raise ValueError(
            f"Unsupported demand_shape_source '{demand_shape_source}'. Expected 'mendeley' or 'efs'."
        )

    # Fetch real demand data and restrict to the calibration years
    real_series = fetch_demand_data_demandcast(
        country_code,
        start_year=calibration_start_year,
        end_year=calibration_end_year,
    )

    # Determine which columns to scale during calibration
    if scale_all_numeric:
        cols_to_scale = None  # calibrate_synthetic_load will determine automatically
    else:
        # Scale total load and the specified load_cols only
        default_cols = [col for col in df_synthetic.columns if col == 'load']
        if load_cols is not None:
            default_cols += list(load_cols)
        cols_to_scale = default_cols

    # Calibrate the synthetic load to match real demand levels
    df_calibrated = calibrate_synthetic_load(
        df_synthetic,
        real_series,
        load_col='load',
        load_cols_to_scale=cols_to_scale,
    )
    if seasonal_calibration:
        df_calibrated = calibrate_seasonal_enduse_load(
            df_calibrated,
            real_series,
            load_col='load',
        )

    # Determine default load_cols if not provided
    if load_cols is None:
        load_cols = [
            col for col in df_calibrated.columns
            if (np.issubdtype(df_calibrated[col].dtype, np.number)
                and not col.endswith('_cf')
                and not col.endswith('_gen')
                and col != 'load')
        ]

    # Run the timeslice pipeline on the calibrated data
    cf_df, lf_df, labels = run_pipeline(
        df_calibrated,
        load_col='load',
        gen_cols=gen_cols,
        cf_cols=cf_cols,
        load_cols=load_cols,
        n_clusters=n_clusters,
        output_path=output_path if output_path not in [None, False] else None,
        country=region_name,
        run_metadata={
            'country': region_name,
            'demand_shape_source': df_synthetic.attrs.get('demand_shape_source', demand_shape_source),
            'demand_shape_source_year': df_synthetic.attrs.get('demand_shape_source_year', year),
            'demand_shape_source_scenario': df_synthetic.attrs.get('demand_shape_source_scenario', scenario),
            **elccafr_run_metadata(region_name),
        },
    )
    return cf_df, lf_df, labels


def compute_net_load(
    df: pd.DataFrame,
    load_col: str,
    gen_cols: Iterable[str],
) -> pd.Series:
    """Compute net load as total load minus variable generation.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing at least the load column and generation columns.
    load_col : str
        Name of the column containing total electricity demand (MW or kW).
    gen_cols : Iterable[str]
        Iterable of column names corresponding to variable renewable generation
        (in the same units as load).  If capacity factors are provided
        instead of generation, multiply them by installed capacity before
        calling this function.

    Returns
    -------
    pandas.Series
        A series of net load values for each row in ``df``.

    Notes
    -----
    Net load is defined as the forecasted load minus expected production
    from variable generation resources (e.g. wind and solar).  The net load
    curves illustrate the portion of the demand that must be served by
    dispatchable resources【202852532351279†L50-L103】.
    """

    # Ensure all required columns exist
    missing = [c for c in [load_col, *gen_cols] if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns required for net load calculation: {missing}")

    # Subtract the sum of generation columns from the load
    net = df[load_col] - df[list(gen_cols)].sum(axis=1)
    return net


# Countries in the Southern Hemisphere — their season-month defaults need to flip
# (December–February is summer; June–August is winter). Used by the
# `_hemisphere_season_months` helper to pick correct defaults when the caller
# does not pass explicit winter_months / summer_months.
SOUTHERN_HEMISPHERE_COUNTRIES = {
    'Australia', 'Brazil', 'Argentina', 'Chile', 'New Zealand', 'South Africa',
    'Peru', 'Uruguay', 'Paraguay', 'Bolivia',
}


def _hemisphere_season_months(country: Optional[str] = None) -> Tuple[List[int], List[int]]:
    """Return (summer_months, winter_months) lists for a country.

    Northern Hemisphere default. For SOUTHERN_HEMISPHERE_COUNTRIES the months flip:
      summer = [12, 1, 2]
      winter = [6, 7, 8]
    """
    if country and country in SOUTHERN_HEMISPHERE_COUNTRIES:
        return [12, 1, 2], [6, 7, 8]
    return [6, 7, 8], [11, 12, 1, 2]


def cluster_timeslices(
    net_load: pd.Series,
    timestamps: Optional[pd.Series] = None,
    n_clusters: int = 6,
    random_state: Optional[int] = 0,
    n_init: int = 10,
    winter_months: Optional[Iterable[int]] = None,
    summer_months: Optional[Iterable[int]] = None,
    feature_weight_mode: str = 'netload_focus',
    search_seeds: Optional[Iterable[int]] = None,
    pin_extremes: bool = True,
    country: Optional[str] = None,
) -> Tuple[pd.Series, KMeans, Dict[int, int], Dict[int, pd.Timestamp]]:
    """Cluster daily net-load profiles into representative-day timeslices.

    **As of 2026-05-22 this function delegates to
    `state_pipeline.builders.clustering_repday.cluster_days_repday` — the
    canonical clustering implementation used by the US national + per-state
    pipelines.** This wrapper preserves the legacy return signature
    (hourly labels Series, KMeans model, mapping dict, representative_dates
    dict) for backward compatibility with existing non-US country pipelines.

    The methodology — representative-day reconstruction on net load with FIXED
    rep profiles and no peak-day cap — is documented in
    CLUSTERING_METHODOLOGY.md at the project root. The optimizer self-terminates
    at ~10–15 day peak slices for typical national net-load series.

    The `country` parameter is new in this revision. If provided, season-month
    defaults are hemisphere-aware (Southern Hemisphere countries get flipped
    summer/winter months). Explicit `winter_months` / `summer_months` arguments
    still take precedence.
    """
    if winter_months is None or summer_months is None:
        default_summer, default_winter = _hemisphere_season_months(country)
        if winter_months is None:
            winter_months = default_winter
        if summer_months is None:
            summer_months = default_summer
    return _cluster_timeslices_via_repday(
        net_load, timestamps, n_clusters=n_clusters, n_init=n_init,
        winter_months=winter_months, summer_months=summer_months,
        feature_weight_mode=feature_weight_mode, search_seeds=search_seeds,
        pin_extremes=pin_extremes,
    )


def _cluster_timeslices_via_repday(
    net_load: pd.Series,
    timestamps: Optional[pd.Series],
    n_clusters: int,
    n_init: int,
    winter_months: Iterable[int],
    summer_months: Iterable[int],
    feature_weight_mode: str,
    search_seeds: Optional[Iterable[int]],
    pin_extremes: bool,
) -> Tuple[pd.Series, KMeans, Dict[int, int], Dict[int, pd.Timestamp]]:
    """Wrapper: call cluster_days_repday, repack result into legacy return tuple."""
    try:
        from state_pipeline.builders.clustering_repday import cluster_days_repday
    except ImportError:
        # Fall back to the legacy in-place implementation if state_pipeline is
        # not importable (e.g., running this module in isolation).
        return _cluster_timeslices_legacy_impl(
            net_load, timestamps, n_clusters=n_clusters, n_init=n_init,
            winter_months=winter_months, summer_months=summer_months,
            feature_weight_mode=feature_weight_mode, search_seeds=search_seeds,
            pin_extremes=pin_extremes,
        )

    # Build a DatetimeIndex-keyed net_load Series.
    if timestamps is not None:
        idx = pd.to_datetime(timestamps)
        net_series = pd.Series(net_load.values, index=idx)
    else:
        if not isinstance(net_load.index, pd.DatetimeIndex):
            net_load = pd.Series(net_load.values, index=pd.to_datetime(net_load.index))
        net_series = net_load

    # cluster_days_repday computes net = total - solar - wind internally. We
    # already have net load, so pass it as total_demand and zero VRE.
    zero = pd.Series(0.0, index=net_series.index)
    cr = cluster_days_repday(
        net_series, zero, zero,
        peak_top_n=1 if pin_extremes else 0,
        max_peak_days=365,
        feature_weight_mode=feature_weight_mode,
        search_seeds=search_seeds,
        n_init=n_init,
        summer_months=tuple(summer_months),
        winter_months=tuple(winter_months),
    )

    # Map slice names → integer cluster IDs. Convention: pinned peak slices get
    # the highest IDs (matches legacy `remaining_clusters + offset`).
    n_pinned = 2 if pin_extremes else 0
    n_nonpeak = n_clusters - n_pinned
    slice_to_int: Dict[str, int] = {
        'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3,
    }
    if pin_extremes:
        slice_to_int['Summer Peak'] = n_nonpeak
        slice_to_int['Winter Peak'] = n_nonpeak + 1

    # Hourly labels: per-hour integer cluster ID.
    doys = net_series.index.dayofyear
    hourly_labels = pd.Series(
        [int(slice_to_int[cr.slice_assignment[int(d)]]) for d in doys],
        index=net_series.index,
    )

    # mapping: legacy uses this internally for centroid ordering. Identity is fine —
    # downstream callers in this file ignore it.
    mapping: Dict[int, int] = {i: i for i in range(n_clusters)}

    # representative_dates: per slice, pick a rep day.
    representative_dates: Dict[int, pd.Timestamp] = {}
    year = int(net_series.index[0].year)
    base = pd.Timestamp(year=year, month=1, day=1)
    for slice_name, int_id in slice_to_int.items():
        days = [int(d) for d in cr.slice_assignment.index
                if cr.slice_assignment[int(d)] == slice_name]
        if not days:
            continue
        if slice_name in ('Summer Peak', 'Winter Peak'):
            rep_doy = max(days, key=lambda d: float(cr.daily_peak.loc[d]))
        else:
            rep_doy = sorted(days)[len(days) // 2]
        representative_dates[int_id] = base + pd.Timedelta(days=rep_doy - 1)

    # KMeans model: legacy callers in this file don't use the returned model
    # (verified via grep — only `mapping` and `representative_dates` are read
    # downstream). Provide a minimal valid placeholder so isinstance checks
    # pass. Suppress the ConvergenceWarning since the placeholder is
    # intentionally degenerate (no real cluster centers are needed).
    import warnings
    placeholder = KMeans(n_clusters=max(2, n_nonpeak), random_state=cr.best_seed, n_init=1)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        try:
            # Use a non-degenerate fit input so sklearn doesn't warn about
            # duplicate points; values don't matter since the model isn't used.
            placeholder.fit(np.arange(max(2, n_nonpeak)).reshape(-1, 1).astype(float))
        except Exception:  # pragma: no cover
            pass
    return hourly_labels, placeholder, mapping, representative_dates


def _cluster_timeslices_legacy_impl(
    net_load: pd.Series,
    timestamps: Optional[pd.Series] = None,
    n_clusters: int = 6,
    random_state: Optional[int] = 0,
    n_init: int = 10,
    winter_months: Optional[Iterable[int]] = None,
    summer_months: Optional[Iterable[int]] = None,
    feature_weight_mode: str = 'netload_focus',
    search_seeds: Optional[Iterable[int]] = None,
    pin_extremes: bool = True,
) -> Tuple[pd.Series, KMeans, Dict[int, int], Dict[int, pd.Timestamp]]:
    """Original cluster_timeslices implementation, kept as a fallback.

    Identical methodology to cluster_days_repday (rep-day on net load, fixed
    rep profiles, no cap) but uses pandas-heavy operations (~50x slower for
    8760-hour series). Preserved here for cases where state_pipeline is not
    importable.
    """
    if winter_months is None:
        winter_months = [11, 12, 1, 2]
    if summer_months is None:
        summer_months = [6, 7, 8]

    if timestamps is None:
        timestamps = pd.Series(net_load.index, index=net_load.index)
    timestamps = pd.to_datetime(timestamps)

    daily = pd.DataFrame({
        'timestamp': pd.Series(timestamps).reset_index(drop=True),
        'net_load': pd.Series(net_load).reset_index(drop=True),
    })
    daily['date'] = daily['timestamp'].dt.floor('D')
    daily['hour_of_day'] = daily['timestamp'].dt.hour
    X = (
        daily.pivot(index='date', columns='hour_of_day', values='net_load')
        .sort_index()
        .reindex(columns=range(24))
    )
    if X.isna().any().any():
        raise ValueError("Daily net-load profiles must contain 24 hourly values for each day.")

    def _max_abs_ramp(values: pd.Series) -> float:
        arr = pd.to_numeric(values, errors='coerce').to_numpy()
        if len(arr) < 2:
            return 0.0
        diffs = np.diff(arr)
        return float(np.nanmax(np.abs(diffs))) if len(diffs) else 0.0

    feature_matrix = pd.DataFrame({
        'net_mean': daily.groupby('date')['net_load'].mean(),
        'net_min': daily.groupby('date')['net_load'].min(),
        'net_p95': daily.groupby('date')['net_load'].quantile(0.95),
        'net_ramp_max': daily.groupby('date')['net_load'].apply(_max_abs_ramp),
    }).sort_index()

    feature_weights = {
        'uniform': {'net_mean': 1.0, 'net_min': 1.0, 'net_p95': 1.0, 'net_ramp_max': 1.0},
        'netload_focus': {'net_mean': 2.5, 'net_min': 4.0, 'net_p95': 6.0, 'net_ramp_max': 4.0},
        'netload_ramp_focus': {'net_mean': 2.0, 'net_min': 3.0, 'net_p95': 5.0, 'net_ramp_max': 6.0},
    }
    if feature_weight_mode not in feature_weights:
        raise ValueError(f"Unknown feature_weight_mode '{feature_weight_mode}'.")
    weighted_features = feature_matrix.mul(pd.Series(feature_weights[feature_weight_mode]), axis=1)

    pinned_dates: list[pd.Timestamp] = []
    if pin_extremes:
        daily_peaks = daily.groupby('date')['net_load'].max()
        day_months = daily.groupby('date')['timestamp'].first().dt.month
        summer_candidates = daily_peaks[day_months.isin(list(summer_months))]
        winter_candidates = daily_peaks[day_months.isin(list(winter_months))]
        if not summer_candidates.empty:
            _summer_pin = summer_candidates.idxmax()
            pinned_dates.append(_summer_pin)
            _status(
                'cluster',
                f"pinning summer peak day = {pd.Timestamp(_summer_pin).date()}  "
                f"(net-load peak {float(summer_candidates.loc[_summer_pin]):,.0f} MW)",
            )
        if not winter_candidates.empty:
            winter_peak_date = winter_candidates.idxmax()
            if winter_peak_date not in pinned_dates:
                pinned_dates.append(winter_peak_date)
                _status(
                    'cluster',
                    f"pinning winter peak day = {pd.Timestamp(winter_peak_date).date()}  "
                    f"(net-load peak {float(winter_candidates.loc[winter_peak_date]):,.0f} MW)",
                )

    remaining_dates = X.index.difference(pd.Index(pinned_dates))
    remaining_clusters = n_clusters - len(pinned_dates)
    if remaining_clusters < 1:
        raise ValueError("n_clusters must be larger than the number of pinned extreme days.")

    candidate_seeds = list(search_seeds) if search_seeds is not None else [int(random_state or 0), 1, 2, 3, 4, 5, 10, 20, 99]
    seen_seeds = []
    for seed in candidate_seeds:
        seed_i = int(seed)
        if seed_i not in seen_seeds:
            seen_seeds.append(seed_i)

    scaler = StandardScaler()
    scaled_features = pd.DataFrame(
        scaler.fit_transform(weighted_features),
        index=weighted_features.index,
        columns=weighted_features.columns,
    )
    pinned_label_map = {
        pd.Timestamp(pinned_date): remaining_clusters + offset
        for offset, pinned_date in enumerate(pinned_dates)
    }

    def _select_representative_dates(candidate_daily_labels: pd.Series) -> Dict[int, pd.Timestamp]:
        representative_dates: Dict[int, pd.Timestamp] = {}
        for pinned_date, pinned_label in pinned_label_map.items():
            representative_dates[int(pinned_label)] = pd.Timestamp(pinned_date)
        for timeslice, member_dates in candidate_daily_labels.groupby(candidate_daily_labels):
            if int(timeslice) in representative_dates:
                continue
            member_index = member_dates.index
            cluster_features = scaled_features.loc[member_index]
            centroid = cluster_features.mean(axis=0)
            distances = ((cluster_features - centroid) ** 2).sum(axis=1)
            representative_dates[int(timeslice)] = pd.Timestamp(distances.idxmin())
        return representative_dates

    def _score_daily_labels(
        candidate_daily_labels: pd.Series,
        representative_dates: Dict[int, pd.Timestamp],
    ) -> float:
        rep_profiles = (
            daily[daily['date'].isin(representative_dates.values())]
            .assign(timeslice=lambda d: d['date'].map({v: k for k, v in representative_dates.items()}))
            .set_index(['timeslice', 'hour_of_day'])['net_load']
        )
        lookup_index = pd.MultiIndex.from_arrays(
            [daily['date'].map(candidate_daily_labels).to_numpy(), daily['hour_of_day'].to_numpy()],
            names=['timeslice', 'hour_of_day'],
        )
        reconstructed = rep_profiles.loc[lookup_index].to_numpy()
        observed = daily['net_load'].to_numpy()
        rmse = float(np.sqrt(np.nanmean((observed - reconstructed) ** 2)))
        std = float(np.nanstd(observed))
        return rmse / std if std > 0 else float('inf')

    def _improve_pinned_assignments(
        candidate_daily_labels: pd.Series,
        representative_dates: Dict[int, pd.Timestamp],
    ) -> Tuple[pd.Series, Dict[int, pd.Timestamp], float]:
        if not pinned_label_map:
            return candidate_daily_labels, representative_dates, _score_daily_labels(candidate_daily_labels, representative_dates)

        day_peaks = daily.groupby('date')['net_load'].max().sort_index()
        day_month_map = daily.groupby('date')['timestamp'].first().dt.month.sort_index()
        working_labels = candidate_daily_labels.copy().sort_index()
        current_reps = dict(representative_dates)
        current_score = _score_daily_labels(working_labels, current_reps)
        season_to_pinned = {}
        if summer_candidates is not None and not summer_candidates.empty and len(pinned_dates) >= 1:
            season_to_pinned['summer'] = pinned_label_map.get(pd.Timestamp(summer_candidates.idxmax()))
        if winter_candidates is not None and not winter_candidates.empty:
            season_to_pinned['winter'] = pinned_label_map.get(pd.Timestamp(winter_candidates.idxmax()))

        for season_name, months, pinned_label in (
            ('summer', list(summer_months), season_to_pinned.get('summer')),
            ('winter', list(winter_months), season_to_pinned.get('winter')),
        ):
            if pinned_label is None:
                continue
            candidate_dates = [
                pd.Timestamp(day)
                for day in working_labels.index
                if pd.Timestamp(day) not in pinned_label_map
                and int(day_month_map.loc[pd.Timestamp(day)]) in months
            ]
            candidate_dates = sorted(candidate_dates, key=lambda day: float(day_peaks.loc[day]), reverse=True)
            improved = True
            while improved:
                improved = False
                best_move = None
                best_move_score = current_score
                for candidate_date in candidate_dates:
                    if int(working_labels.loc[candidate_date]) == int(pinned_label):
                        continue
                    trial_labels = working_labels.copy()
                    trial_labels.loc[candidate_date] = int(pinned_label)
                    trial_reps = _select_representative_dates(trial_labels)
                    trial_score = _score_daily_labels(trial_labels, trial_reps)
                    if trial_score + 1e-12 < best_move_score:
                        best_move = candidate_date
                        best_move_score = trial_score
                if best_move is not None:
                    working_labels.loc[best_move] = int(pinned_label)
                    current_reps = _select_representative_dates(working_labels)
                    current_score = best_move_score
                    improved = True
        return working_labels, current_reps, current_score

    best_score = float('inf')
    best_labels = None
    best_model = None
    best_mapping = None
    best_representative_dates = None
    _t_cluster = time.perf_counter()
    _status(
        'cluster',
        f"k-means search across {len(seen_seeds)} random seeds "
        f"({remaining_clusters} free clusters + {len(pinned_dates)} pinned)",
    )

    for _seed_idx, seed in enumerate(seen_seeds, start=1):
        model = KMeans(n_clusters=remaining_clusters, random_state=seed, n_init=n_init)
        raw_labels = model.fit_predict(scaled_features.loc[remaining_dates])
        centers = model.cluster_centers_[:, scaled_features.columns.get_loc('net_p95')]
        order = np.argsort(centers)
        mapping = {int(cluster): int(rank) for rank, cluster in enumerate(order)}
        daily_labels = pd.Series(raw_labels, index=remaining_dates).map(mapping)
        for offset, pinned_date in enumerate(pinned_dates):
            daily_labels.loc[pinned_date] = remaining_clusters + offset
        daily_labels = daily_labels.sort_index()
        representative_dates = _select_representative_dates(daily_labels)
        daily_labels, representative_dates, score = _improve_pinned_assignments(daily_labels, representative_dates)
        improved = score < best_score
        if improved:
            best_score = score
            best_labels = daily_labels
            best_model = model
            best_mapping = mapping
            best_representative_dates = representative_dates
        # Per-seed details only when verbose, otherwise just the summary
        # is printed after the loop completes.
        _status(
            'cluster',
            f"  seed {seed} ({_seed_idx}/{len(seen_seeds)}): score={score:.4f}"
            + ("  (new best)" if improved else ""),
            level='verbose',
        )

    if best_labels is None or best_model is None or best_mapping is None or best_representative_dates is None:
        raise RuntimeError("Failed to identify a valid timeslice clustering solution.")
    _status(
        'cluster',
        f"selected best clustering (score={best_score:.4f}) across {len(seen_seeds)} seeds",
        t=_t_cluster,
    )

    ordered_labels = daily['date'].map(best_labels)
    ordered_labels.index = net_load.index
    return ordered_labels, best_model, best_mapping, best_representative_dates



def compute_capacity_factors(
    df: pd.DataFrame,
    labels: pd.Series,
    cf_cols: Iterable[str],
) -> pd.DataFrame:
    """Aggregate hourly capacity factors into timeslice averages.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing hourly capacity factor columns for each variable
        renewable technology.  The DataFrame must have the same length as
        ``labels``.
    labels : pandas.Series
        Timeslice labels for each row in ``df``, such as those returned by
        ``cluster_timeslices``.
    cf_cols : Iterable[str]
        List of column names corresponding to variable renewable capacity
        factors (values between 0 and 1).

    Returns
    -------
    pandas.DataFrame
        A DataFrame indexed by the ordered timeslice label.  Each column
        contains the mean capacity factor of the corresponding technology
        within each timeslice.

    Notes
    -----
    According to Mallapragada et al. (2020), once time slices are determined,
    renewable energy capacity factors in each slice should be computed as the
    average capacity factor over all hours in that slice【787555183402410†L900-L904】.
    This function implements that aggregation.
    """

    # Validate column existence
    missing = [c for c in cf_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing capacity factor columns: {missing}")

    # Combine labels with the DataFrame
    df = df.copy()
    df['timeslice'] = labels.values
    # Group by timeslice and compute mean capacity factor for each technology
    grouped = df.groupby('timeslice')[list(cf_cols)].mean()
    # Ensure slices appear in order 0…n-1
    grouped = grouped.sort_index()
    return grouped


def compute_load_factors(
    df: pd.DataFrame,
    labels: pd.Series,
    load_cols: Iterable[str],
) -> pd.DataFrame:
    """Compute load factors for end‑use sectors within each timeslice.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing hourly load columns for each sector/end‑use
        combination.  Must have the same length as ``labels``.
    labels : pandas.Series
        Timeslice labels for each row in ``df``.
    load_cols : Iterable[str]
        List of column names representing hourly electricity consumption for
        different end uses and sectors.  Each column should be non‑negative.

    Returns
    -------
    pandas.DataFrame
        A DataFrame indexed by timeslice.  For each sector/end‑use column,
        two statistics are reported:

        * ``<col>_mean`` – average load within the timeslice.
        * ``<col>_max`` – peak (maximum) load within the timeslice.
        * ``<col>_load_factor`` – ratio of average to peak load in the
          timeslice【707536377475410†L119-L124】.

    Notes
    -----
    Load factor is a useful indicator of how consistently a resource is used.
    A high load factor (closer to 1) means that the load remains near its
    peak level throughout the timeslice; a low load factor indicates that
    demand is highly concentrated in a few hours.
    """

    missing = [c for c in load_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing load columns: {missing}")

    df = df.copy()
    df['timeslice'] = labels.values
    # Prepare a dictionary to hold aggregated results
    results: Dict[str, pd.Series] = {}
    for col in load_cols:
        # Compute mean and max per timeslice
        agg = df.groupby('timeslice')[col].agg(['mean', 'max'])
        # Compute load factor as mean divided by max (avoid division by zero)
        lf = agg['mean'] / agg['max'].replace(0, np.nan)
        results[f'{col}_mean'] = agg['mean']
        results[f'{col}_max'] = agg['max']
        results[f'{col}_load_factor'] = lf
    # Combine into a DataFrame and order timeslices
    out = pd.DataFrame(results)
    out.index.name = 'timeslice'
    out = out.sort_index()
    return out


def assign_seasonal_labels(
    timestamps: pd.Series,
    labels: pd.Series,
    winter_months: Optional[Iterable[int]] = None,
    summer_months: Optional[Iterable[int]] = None,
) -> pd.Series:
    """Assign descriptive labels (e.g. 'winter_peak', 'winter_offpeak') to timeslices.

    Parameters
    ----------
    timestamps : pandas.Series
        Series of datetime objects corresponding to each row of the input data.
    labels : pandas.Series
        Timeslice labels obtained from ``cluster_timeslices``.
    winter_months : Iterable[int], optional
        Months considered part of the winter season (e.g. [11, 12, 1, 2]).  If
        ``None`` a default of November–February is used.
    summer_months : Iterable[int], optional
        Months considered part of the summer season (e.g. [5, 6, 7, 8]).  If
        ``None`` a default of May–August is used.

    Returns
    -------
    pandas.Series
        A Series of string labels giving a human‑readable description for each
        hour (e.g. 'winter_offpeak', 'winter_peak', 'summer_offpeak', etc.),
        based on seasonal membership and relative net load ranking.

    Notes
    -----
    This helper function is optional but can be useful when mapping
    timeslice indices to model‑specific names.  It assumes that low
    timeslice indices correspond to low net load and high indices to high
    net load.
    """

    if winter_months is None:
        winter_months = [11, 12, 1, 2]
    if summer_months is None:
        summer_months = [5, 6, 7, 8]
    # Determine the season for each timestamp
    season = timestamps.dt.month.map(
        lambda m: 'winter' if m in winter_months else ('summer' if m in summer_months else 'shoulder')
    )
    # Determine threshold to split into off‑peak and peak categories
    max_label = int(labels.max())
    half = (max_label + 1) // 2
    peak_flag = labels >= half
    descriptive = season + '_' + peak_flag.map({False: 'offpeak', True: 'peak'})
    return descriptive


def _extract_timestamps(df: pd.DataFrame) -> pd.Series:
    """Return a timestamp series from a DataFrame column or DatetimeIndex."""
    if 'timestamp' in df.columns:
        return pd.to_datetime(df['timestamp'])
    if isinstance(df.index, pd.DatetimeIndex):
        return pd.Series(df.index, index=df.index, name='timestamp')
    raise KeyError(
        "A datetime source is required. Provide a 'timestamp' column or a DatetimeIndex."
    )


def build_timeslice_metadata(
    timestamps: pd.Series,
    labels: pd.Series,
    net_load: pd.Series,
    representative_dates: Optional[Dict[int, pd.Timestamp]] = None,
    winter_months: Optional[Iterable[int]] = None,
    summer_months: Optional[Iterable[int]] = None,
) -> pd.DataFrame:
    """Create metadata describing each timeslice and pinned labels."""
    timestamps = pd.to_datetime(timestamps)
    if winter_months is None:
        winter_months = [11, 12, 1, 2]
    if summer_months is None:
        summer_months = [6, 7, 8]

    if not isinstance(net_load, pd.Series):
        net_load = pd.Series(net_load, index=labels.index)

    meta = pd.DataFrame({
        'timestamp': pd.Series(timestamps).reset_index(drop=True),
        'timeslice': pd.Series(labels).reset_index(drop=True),
        'net_load': pd.Series(net_load).reset_index(drop=True),
    })
    meta['date'] = meta['timestamp'].dt.floor('D')
    meta['month'] = meta['timestamp'].dt.month
    meta['season'] = np.where(
        meta['month'].isin(list(winter_months)),
        'winter',
        np.where(meta['month'].isin(list(summer_months)), 'summer', 'other'),
    )

    winter_rows = meta.loc[meta['season'] == 'winter']
    if winter_rows.empty:
        winter_timeslice = int(meta.loc[meta['net_load'].idxmax(), 'timeslice'])
    else:
        winter_peak_row = winter_rows.loc[winter_rows['net_load'].idxmax()]
        winter_timeslice = int(winter_peak_row['timeslice'])

    summer_rows = meta.loc[meta['season'] == 'summer']
    if summer_rows.empty:
        summer_timeslice = int(meta.loc[meta['net_load'].idxmax(), 'timeslice'])
    else:
        summer_peak_row = summer_rows.loc[summer_rows['net_load'].idxmax()]
        summer_timeslice = int(summer_peak_row['timeslice'])

    summary = meta.groupby('timeslice').agg(
        days_represented=('date', 'nunique'),
        hours_in_timeslice=('timeslice', 'size'),
        avg_net_load=('net_load', 'mean'),
        peak_net_load=('net_load', 'max'),
        dominant_month=('month', lambda x: int(x.mode().iat[0])),
        dominant_season=('season', lambda x: x.mode().iat[0]),
    ).sort_index()

    summary['timeslice_name'] = [f'TS{int(ts):02d}' for ts in summary.index]
    for timeslice in summary.index:
        suffixes = []
        if timeslice == summer_timeslice:
            suffixes.append('PINNED_SUMMER')
        if timeslice == winter_timeslice:
            suffixes.append('PINNED_WINTER')
        if suffixes:
            summary.loc[timeslice, 'timeslice_name'] = f"TS{timeslice:02d}_{'_'.join(suffixes)}"

    summary['is_pinned_summer'] = summary.index == summer_timeslice
    summary['is_pinned_winter'] = summary.index == winter_timeslice
    if representative_dates:
        summary['representative_date'] = summary.index.map(
            lambda ts: pd.Timestamp(representative_dates.get(int(ts))).date().isoformat()
            if int(ts) in representative_dates else None
        )
    summary.index.name = 'timeslice'
    return summary


def compute_hourly_capacity_profiles(
    df: pd.DataFrame,
    labels: pd.Series,
    cf_cols: Iterable[str],
    timestamps: pd.Series,
    timeslice_metadata: Optional[pd.DataFrame] = None,
    representative_dates: Optional[Dict[int, pd.Timestamp]] = None,
) -> pd.DataFrame:
    """Compute 24 hourly mean capacity factors for each timeslice.

    Default (``representative_dates=None``) is the **slice mean**: each cell is
    the average CF over every hour assigned to that (slice, hour-of-day), which
    is what the EPS workbooks express as ``AVERAGEIFS(cf, slice, …, hour, …)``.

    Passing ``representative_dates`` switches to a single representative day's
    profile per slice. That is the clustering *objective*, not the export
    convention — a rep-day table's days-weighted annual mean does not match the
    calibrated hourly annual mean. The production path no longer passes it; see
    DECISIONS.md 2026-08-12.
    """
    missing = [c for c in cf_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing capacity factor columns: {missing}")

    if not cf_cols:
        return pd.DataFrame()

    work = df[list(cf_cols)].copy()
    work['timeslice'] = labels.values
    work['date'] = pd.to_datetime(timestamps).dt.floor('D').values
    work['hour_of_day'] = pd.to_datetime(timestamps).dt.hour.values

    if representative_dates:
        profiles = []
        date_keys = pd.to_datetime(work['date']).dt.strftime('%Y-%m-%d')
        for timeslice, rep_date in representative_dates.items():
            rep_key = pd.Timestamp(rep_date).strftime('%Y-%m-%d')
            rep_profile = work.loc[date_keys == rep_key, ['hour_of_day', *cf_cols]].copy()
            if rep_profile.empty:
                continue
            rep_profile['timeslice'] = int(timeslice)
            profiles.append(rep_profile)
        if not profiles:
            raise ValueError("Representative-day capacity profiles could not be constructed.")
        hourly = pd.concat(profiles, ignore_index=True).groupby(['timeslice', 'hour_of_day'])[list(cf_cols)].first()
    else:
        hourly = work.groupby(['timeslice', 'hour_of_day'])[list(cf_cols)].mean()
    full_index = pd.MultiIndex.from_product(
        [sorted(pd.unique(labels)), range(24)],
        names=['timeslice', 'hour_of_day'],
    )
    hourly = hourly.reindex(full_index)

    if timeslice_metadata is not None and not timeslice_metadata.empty:
        hourly = hourly.reset_index().merge(
            timeslice_metadata[['timeslice_name', 'days_represented']].reset_index(),
            on='timeslice',
            how='left',
        )
        hourly = hourly.set_index(['timeslice', 'timeslice_name', 'hour_of_day']).sort_index()

    return hourly


def compute_hourly_load_profiles(
    df: pd.DataFrame,
    labels: pd.Series,
    load_cols: Iterable[str],
    timestamps: pd.Series,
    timeslice_metadata: Optional[pd.DataFrame] = None,
    representative_dates: Optional[Dict[int, pd.Timestamp]] = None,
) -> pd.DataFrame:
    """Compute 24 hourly load shares (load factors) for each timeslice.

    Default (``representative_dates=None``) is the **slice mean**:
    ``LF[slice, hour] = mean demand over that (slice, hour-of-day) / annual
    demand``, matching CLAUDE.md §6. This is the form that satisfies the SHELF
    balance ``Σ_slices days × Σ_hours LF = 1`` exactly, so EPS allocates each
    category's annual demand across the year without gain or loss.

    Passing ``representative_dates`` switches to a single representative day per
    slice, which breaks that balance (0.84–2.24 by category on the KR run). The
    production path no longer passes it; see DECISIONS.md 2026-08-12.
    """
    missing = [c for c in load_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing load columns: {missing}")

    work = df[list(load_cols)].copy()
    work['timeslice'] = labels.values
    work['date'] = pd.to_datetime(timestamps).dt.floor('D').values
    work['hour_of_day'] = pd.to_datetime(timestamps).dt.hour.values

    if representative_dates:
        profiles = []
        date_keys = pd.to_datetime(work['date']).dt.strftime('%Y-%m-%d')
        for timeslice, rep_date in representative_dates.items():
            rep_key = pd.Timestamp(rep_date).strftime('%Y-%m-%d')
            rep_profile = work.loc[date_keys == rep_key, ['hour_of_day', *load_cols]].copy()
            if rep_profile.empty:
                continue
            rep_profile['timeslice'] = int(timeslice)
            profiles.append(rep_profile)
        if not profiles:
            raise ValueError("Representative-day load profiles could not be constructed.")
        hourly_mean = pd.concat(profiles, ignore_index=True).groupby(['timeslice', 'hour_of_day'])[list(load_cols)].first()
    else:
        hourly_mean = work.groupby(['timeslice', 'hour_of_day'])[list(load_cols)].mean()
    full_index = pd.MultiIndex.from_product(
        [sorted(pd.unique(labels)), range(24)],
        names=['timeslice', 'hour_of_day'],
    )
    hourly_mean = hourly_mean.reindex(full_index)

    out = pd.DataFrame(index=hourly_mean.index)
    annual_totals = df[list(load_cols)].sum(axis=0).replace(0, np.nan)
    for col in load_cols:
        out[f'{col}_load_factor'] = hourly_mean[col] / annual_totals[col]

    if timeslice_metadata is not None and not timeslice_metadata.empty:
        out = out.reset_index().merge(
            timeslice_metadata[['timeslice_name', 'days_represented']].reset_index(),
            on='timeslice',
            how='left',
        )
        out = out.set_index(['timeslice', 'timeslice_name', 'hour_of_day']).sort_index()

    return out


def _month_distance(month: int, target_month: int) -> int:
    """Return circular month distance on a 12-month calendar."""
    diff = abs(int(month) - int(target_month))
    return min(diff, 12 - diff)


def build_eps_timeslice_label_map(timeslice_metadata: pd.DataFrame) -> pd.Series:
    """Map numeric timeslices onto EPS-style labels."""
    if timeslice_metadata is None or timeslice_metadata.empty:
        raise ValueError("Timeslice metadata is required to build EPS labels.")

    metadata = timeslice_metadata.copy()
    label_map: Dict[int, str] = {}

    summer_rows = metadata[metadata['is_pinned_summer']]
    if not summer_rows.empty:
        label_map[int(summer_rows.index[0])] = 'Summer Peak'

    winter_rows = metadata[metadata['is_pinned_winter']]
    if not winter_rows.empty:
        label_map[int(winter_rows.index[0])] = 'Winter Peak'

    seasonal_targets = {
        'Winter': 1,
        'Spring': 4,
        'Summer': 7,
        'Fall': 10,
    }
    seasonal_aliases = {
        'Winter': {'winter'},
        'Spring': {'other'},
        'Summer': {'summer'},
        'Fall': {'other'},
    }
    remaining = metadata.loc[~metadata.index.isin(label_map.keys())].copy()
    remaining['timeslice'] = remaining.index.astype(int)

    for season_label, target_month in seasonal_targets.items():
        if remaining.empty:
            break
        scored = remaining.assign(
            season_match=remaining['dominant_season'].astype(str).str.lower().isin(seasonal_aliases[season_label]),
            month_distance=remaining['dominant_month'].apply(lambda m: _month_distance(int(m), target_month)),
        ).sort_values(
            by=['season_match', 'month_distance', 'days_represented', 'avg_net_load'],
            ascending=[False, True, False, False],
        )
        chosen = int(scored.iloc[0]['timeslice'])
        label_map[chosen] = season_label
        remaining = remaining.drop(index=chosen)

    unmapped = [int(ts) for ts in metadata.index if int(ts) not in label_map]
    unused_labels = [label for label in EPS_TIMESLICE_ORDER if label not in label_map.values()]
    for timeslice, label in zip(unmapped, unused_labels):
        label_map[timeslice] = label

    out = pd.Series(label_map, name='eps_label').sort_index()
    return out


def _build_eps_hour_table(
    hourly_df: pd.DataFrame,
    value_column: str,
    eps_label_map: pd.Series,
) -> pd.DataFrame:
    """Pivot an hourly timeslice profile into EPS CSV/table layout."""
    if value_column not in hourly_df.columns:
        raise KeyError(f"Column '{value_column}' not found in hourly profile data.")

    work = hourly_df.reset_index()
    if 'timeslice' not in work.columns or 'hour_of_day' not in work.columns:
        raise KeyError("Hourly profile data must include 'timeslice' and 'hour_of_day'.")
    work['eps_label'] = work['timeslice'].map(eps_label_map.to_dict())
    pivot = work.pivot_table(
        index='eps_label',
        columns='hour_of_day',
        values=value_column,
        aggfunc='first',
    )
    pivot = pivot.reindex(index=EPS_TIMESLICE_ORDER, columns=range(24))
    pivot.columns = EPS_HOUR_COLUMNS
    return pivot


def _build_eps_days_table(
    timeslice_metadata: pd.DataFrame,
    eps_label_map: pd.Series,
) -> pd.DataFrame:
    """Create EPS days-per-timeslice table."""
    rows = []
    for timeslice, label in eps_label_map.items():
        rows.append({
            'eps_label': label,
            'Days per Timeslice': timeslice_metadata.loc[int(timeslice), 'days_represented'],
        })
    out = pd.DataFrame(rows).drop_duplicates(subset=['eps_label']).set_index('eps_label')
    out = out.reindex(EPS_TIMESLICE_ORDER)
    return out


def _build_zero_eps_hour_table() -> pd.DataFrame:
    """Create an all-zero EPS hour table."""
    return pd.DataFrame(0.0, index=EPS_TIMESLICE_ORDER, columns=EPS_HOUR_COLUMNS)


def _build_uniform_annual_share_table() -> pd.DataFrame:
    """Create a table with equal annual share in every represented hour."""
    uniform_value = 1.0 / 8760.0
    return pd.DataFrame(uniform_value, index=EPS_TIMESLICE_ORDER, columns=EPS_HOUR_COLUMNS)


def _load_existing_eps_csv(path: str) -> pd.DataFrame:
    """Read an EPS CSV while preserving the first-column label structure."""
    df = pd.read_csv(path, index_col=0)
    df.index = df.index.astype(str).str.strip()
    df = df[~df.index.isin(['', 'nan', 'None'])]
    df = df[~df.index.duplicated(keep='first')]
    numeric_cols = [col for col in df.columns if str(col).startswith('Hour')]
    if numeric_cols:
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    return df


def _make_excel_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove timezone information so pandas can write the frame to Excel."""
    out = df.copy()
    for col in out.columns:
        if isinstance(out[col].dtype, pd.DatetimeTZDtype):
            out[col] = out[col].dt.tz_localize(None)
    if isinstance(out.index, pd.DatetimeIndex) and out.index.tz is not None:
        out.index = out.index.tz_localize(None)
    return out


def _write_eps_csv(path: str, table: pd.DataFrame, unit_label: str) -> None:
    """Write a table in the same top-left-cell format used by EPS CSVs."""
    out = table.copy()
    out.index.name = unit_label
    out.to_csv(path)


def resolve_direct_cf_spec(
    spec: Any,
    available_columns: Iterable[str],
) -> Optional[Tuple[str, float]]:
    """Reduce an export spec to ``(column, multiplier)`` if it is a direct read.

    Returns ``None`` for specs that are not a plain hourly-column read (``sum``,
    ``template_split``, ``uniform_annual_share``, ``None``) or whose column is
    absent from ``available_columns``. ``first_available`` is walked in order and
    resolves to its first usable option — which is what lets the wind techs
    prefer their site-type series (``wind_onshore_cf`` / ``wind_offshore_cf``)
    and fall back to the blended ``wind_cf``.

    The workbook builders use this to decide which SYSHECF tabs are *derived*
    from the hourly CF source tab (formula-driven) rather than pasted in, so
    they must agree with :func:`_build_eps_table_from_spec` about which column a
    spec resolves to.
    """
    columns = set(available_columns)
    if isinstance(spec, str):
        spec = {'mode': 'direct', 'column': spec}
    if not isinstance(spec, dict):
        return None
    mode = spec.get('mode', 'direct')
    if mode == 'first_available':
        for option in spec.get('options', []):
            resolved = resolve_direct_cf_spec(option, columns)
            if resolved is not None:
                return resolved
        return None
    if mode == 'direct' and spec.get('column') in columns:
        return str(spec['column']), float(spec.get('multiplier', 1.0))
    return None


def _build_eps_table_from_spec(
    file_name: str,
    spec: Any,
    hourly_df: pd.DataFrame,
    eps_label_map: pd.Series,
    template_dir: Optional[str],
) -> Tuple[Optional[pd.DataFrame], str, str]:
    """Resolve an EPS export spec to a table plus status metadata."""
    if spec is None:
        return None, 'missing', ''
    if isinstance(spec, str):
        spec = {'mode': 'direct', 'column': spec}
    if not isinstance(spec, dict):
        return None, 'missing', ''

    mode = spec.get('mode', 'direct')
    if mode == 'first_available':
        for option in spec.get('options', []):
            table, status, note = _build_eps_table_from_spec(
                file_name=file_name,
                spec=option,
                hourly_df=hourly_df,
                eps_label_map=eps_label_map,
                template_dir=template_dir,
            )
            if table is not None:
                return table, status, note
        return None, 'missing', ''
    if mode == 'direct':
        column = spec['column']
        if column not in hourly_df.columns:
            return None, 'missing', ''
        table = _build_eps_hour_table(hourly_df, column, eps_label_map)
        multiplier = float(spec.get('multiplier', 1.0))
        if multiplier != 1.0:
            table = table * multiplier
            note = f'generated from {column} with multiplier {multiplier:.3f}'
        else:
            note = f'generated from {column}'
        return table, 'generated', note

    if mode == 'zeros':
        return _build_zero_eps_hour_table(), 'generated', 'generated as explicit zero table'

    if mode == 'uniform_annual_share':
        return _build_uniform_annual_share_table(), 'generated', 'generated as a uniform 1/8760 annual-share table'

    if mode == 'sum':
        columns = list(spec.get('columns', []))
        missing = [col for col in columns if col not in hourly_df.columns]
        if missing:
            return None, 'missing', ''
        combined = hourly_df[columns].sum(axis=1)
        temp = hourly_df.copy()
        temp['_combined_value'] = combined
        table = _build_eps_hour_table(temp, '_combined_value', eps_label_map)
        return table, 'generated', f"generated from summed columns: {', '.join(columns)}"

    if mode == 'template_split':
        aggregate_columns = list(spec.get('aggregate_columns', []))
        peer_files = list(spec.get('peer_files', []))
        missing = [col for col in aggregate_columns if col not in hourly_df.columns]
        if missing or not template_dir:
            return None, 'missing', ''
        peer_tables = []
        for peer in peer_files:
            peer_path = os.path.join(template_dir, f'{peer}.csv')
            if not os.path.exists(peer_path):
                return None, 'missing', ''
            peer_table = _load_existing_eps_csv(peer_path).reindex(index=EPS_TIMESLICE_ORDER, columns=EPS_HOUR_COLUMNS).fillna(0.0)
            peer_tables.append(peer_table.astype(float))
        current_idx = peer_files.index(file_name)
        peer_sum = sum(peer_tables)
        weight = peer_tables[current_idx].divide(peer_sum.replace(0, np.nan)).fillna(0.0)
        aggregate_series = hourly_df[aggregate_columns].sum(axis=1)
        temp = hourly_df.copy()
        temp['_aggregate_value'] = aggregate_series
        aggregate_table = _build_eps_hour_table(temp, '_aggregate_value', eps_label_map)
        table = aggregate_table.multiply(weight)
        return table, 'generated', (
            f"generated from template-weighted split of {', '.join(aggregate_columns)} "
            f"across {', '.join(peer_files)}"
        )

    return None, 'missing', ''


def _build_methodology_sheet(
    family: str,
    coverage_df: pd.DataFrame,
    run_metadata: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Create a workbook About sheet describing the EPS export methodology."""
    if family == 'SHELF':
        demand_shape_source = str((run_metadata or {}).get('demand_shape_source', 'mendeley')).lower()
        if demand_shape_source == 'efs':
            source_line = '1. U.S. hourly end-use demand is built from NREL Electrification Futures Study Reference electrification / Moderate technology advancement load profiles.'
            source_line_2 = '2. EFS residential and commercial space-conditioning loads are split into heating and cooling using monthly RECS Table CE8.2.M and CE8.3.M multipliers.'
            next_number = 3
        else:
            source_line = '1. Synthetic hourly end-use demand profiles are built from the Mendeley global electricity demand dataset.'
            source_line_2 = None
            next_number = 2
        lines = [
            'About',
            'This workbook contains representative-day hourly end-use load factors formatted for EPS.',
            'Methodology',
            source_line,
        ]
        if source_line_2:
            lines.append(source_line_2)
        lines.extend([
            f'{next_number}. Hourly sector and end-use demand is calibrated to observed electricity demand, including seasonal adjustments.',
            f'{next_number + 1}. Net-load days are clustered into six representative timeslices, with pinned summer and winter peak days retained.',
            f'{next_number + 2}. Each tab reports the share of annual load that occurs in each representative-day hour.',
            f'{next_number + 3}. Datacenters are modeled as a uniform annual load with equal hourly share in every hour of the year.',
            f'{next_number + 4}. District heat hydrogen and geoengineering are currently proxied with the industry profile.',
            f'{next_number + 5}. Where the pipeline only has an aggregate category, existing EPS template tabs are used as split weights to allocate that aggregate across finer categories.',
            f'{next_number + 6}. Coverage and file provenance are documented on the Coverage sheet.',
        ])
    elif family == 'ELCCAfR':
        statistic = str((run_metadata or {}).get('elccafr_statistic', ELCCAfR_STATISTIC_DEFAULT))
        demand_altering = float(
            (run_metadata or {}).get('elccafr_demand_altering', ELCCAfR_DEMAND_ALTERING_DEFAULT))
        lines = [
            'About',
            'This workbook contains the per-(technology, timeslice, hour) ELCC Adjustment for Reliability tables formatted for EPS.',
            'Methodology',
            '1. ELCCAfR is a capacity-adequacy derate that EPS multiplies into the reliability calculation only, never into dispatch.',
            f'2. For each peak slice and hour-of-day, ELCCAfR = {statistic} capacity factor / mean capacity factor across the days the clustering assigned to that slice.',
            '3. The denominator is the same slice mean that becomes the SYSHECF cell, so SYSHECF x ELCCAfR equals the worst-day capacity factor at that hour.',
            '4. The four non-peak slices are 1.0: only peak slices can bind in the EPS reliability calculation.',
            f'5. Cells whose mean capacity factor is below {ELCCAfR_DEGENERATE_MEAN} (for example solar overnight) are set to 1.0 rather than a 0/0 ratio.',
            '6. Technologies whose SYSHECF table is a borrowed constant have no within-slice capacity-factor variation, so their ELCCAfR is exactly 1.0.',
            f'7. Demand-altering technologies use {demand_altering} on peak slices, a judgment parameter on demand-response reliability rather than a derived value.',
            '8. There is no ELCCAfR file for distributed solar PV or pumped hydro: neither is a member of the EPS Electricity Source subscript.',
            '9. Coverage and file provenance are documented on the Coverage sheet.',
        ]
    else:
        lines = [
            'About',
            'This workbook contains representative-day hourly electricity capacity factors formatted for EPS.',
            'Methodology',
            '1. Solar and wind hourly capacity factors are derived from weather-based profiles and calibrated to observed annual values where data are available.',
            '2. The same six representative timeslices used for SHELF are applied here so demand and supply remain aligned.',
            '3. Utility-scale solar PV maps directly from the calibrated solar capacity factor profile.',
            '4. Distributed solar PV uses the same hourly shape as utility-scale solar, multiplied by a rooftop derate factor.',
            f'5. The current distributed PV derate is {DISTRIBUTED_SOLAR_CF_DERATE:.2f}, based on an inference from NREL ATB utility-scale vs distributed PV average performance assumptions.',
            '6. Onshore and offshore wind use separate calibrated wind profiles where the run has per-site simulation data classified onshore vs offshore, and the same blended wind profile otherwise; other non-variable technologies remain template-based unless a specific derivation is added.',
            '7. Coverage and file provenance are documented on the Coverage sheet.',
        ]
    if run_metadata:
        lines.append('Run Metadata')
        for key in (
            'country',
            'demand_shape_source',
            'demand_shape_source_year',
            'demand_shape_source_scenario',
            'observed_demand_source',
            'observed_demand_window',
            'observed_demand_citation',
        ):
            if key in run_metadata and run_metadata[key] not in [None, '']:
                lines.append(f"{key}: {run_metadata[key]}")
    coverage_summary = []
    if not coverage_df.empty:
        grouped = coverage_df.groupby('status').size().sort_index()
        coverage_summary = [f"{status}: {count}" for status, count in grouped.items()]
    if coverage_summary:
        lines.append('Coverage Summary')
        lines.extend(coverage_summary)
    return pd.DataFrame({'Notes': lines})


def export_eps_input_tables(
    root_output_dir: str,
    hourly_capacity_factors: Optional[pd.DataFrame],
    hourly_load_factors: Optional[pd.DataFrame],
    timeslice_metadata: Optional[pd.DataFrame],
    eps_template_root: Optional[str] = None,
    run_metadata: Optional[Dict[str, Any]] = None,
    hourly_cf_source: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Export EPS-ready SHELF, SYSHECF and ELCCAfR files plus a coverage report.

    ``hourly_capacity_factors`` / ``hourly_load_factors`` are the collapsed 6x24
    profiles. ``hourly_cf_source`` is the full hourly capacity-factor frame
    (8760 rows, with 'timeslice' and 'hour_of_day' columns) that ELCCAfR needs to
    measure spread across the days inside each slice; without it the ELCCAfR
    family is skipped rather than written wrong.
    """
    if timeslice_metadata is None or timeslice_metadata.empty:
        return pd.DataFrame()
    if hourly_capacity_factors is None or hourly_capacity_factors.empty:
        return pd.DataFrame()
    if hourly_load_factors is None or hourly_load_factors.empty:
        return pd.DataFrame()

    os.makedirs(root_output_dir, exist_ok=True)
    shelf_dir = os.path.join(root_output_dir, 'SHELF')
    syshecf_dir = os.path.join(root_output_dir, 'SYSHECF')
    elccafr_dir = os.path.join(root_output_dir, 'ELCCAfR')
    os.makedirs(shelf_dir, exist_ok=True)
    os.makedirs(syshecf_dir, exist_ok=True)
    os.makedirs(elccafr_dir, exist_ok=True)

    eps_label_map = build_eps_timeslice_label_map(timeslice_metadata)
    report_rows: list[Dict[str, Any]] = []
    workbook_inputs: Dict[str, Dict[str, pd.DataFrame]] = {
        'SHELF': {}, 'SYSHECF': {}, 'ELCCAfR': {}}

    def _resolve_template_dir(family: str) -> Optional[str]:
        if not eps_template_root:
            return None
        candidate = os.path.join(eps_template_root, family)
        return candidate if os.path.isdir(candidate) else None

    def _export_family(
        family: str,
        output_dir: str,
        file_map: Dict[str, Any],
        hourly_df: pd.DataFrame,
        unit_label: str,
    ) -> None:
        template_dir = _resolve_template_dir(family)
        for file_name, source_column in file_map.items():
            output_path = os.path.join(output_dir, f'{file_name}.csv')
            template_path = os.path.join(template_dir, f'{file_name}.csv') if template_dir else None
            status = 'missing'
            note = ''
            table = None
            if file_name == 'SHELF-days-per-timeslice':
                table = _build_eps_days_table(timeslice_metadata, eps_label_map)
                _write_eps_csv(output_path, table, 'Unit: days')
                status = 'generated'
                note = 'generated from clustered timeslice day counts'
            else:
                table, status, note = _build_eps_table_from_spec(
                    file_name=file_name,
                    spec=source_column,
                    hourly_df=hourly_df,
                    eps_label_map=eps_label_map,
                    template_dir=template_dir,
                )
                if table is not None:
                    _write_eps_csv(output_path, table, unit_label)
            if table is None and template_path and os.path.exists(template_path):
                shutil.copyfile(template_path, output_path)
                table = _load_existing_eps_csv(template_path)
                status = 'template_copy'
                note = 'copied unchanged from EPS template'
            report_rows.append({
                'family': family,
                'file_name': f'{file_name}.csv',
                'status': status,
                'source_column': json.dumps(source_column) if isinstance(source_column, dict) else source_column,
                'note': note,
                'output_path': output_path,
            })
            if table is not None:
                workbook_inputs[family][file_name] = table

    _export_family(
        family='SHELF',
        output_dir=shelf_dir,
        file_map=EPS_SHELF_FILE_MAP,
        hourly_df=hourly_load_factors,
        unit_label='Unit: dimensionless (ratio of electricity demand in this hour to annual demand)',
    )
    _export_family(
        family='SYSHECF',
        output_dir=syshecf_dir,
        file_map=EPS_SYSHECF_FILE_MAP,
        hourly_df=hourly_capacity_factors,
        unit_label='Unit: dimensionless (capacity factor)',
    )

    # ELCCAfR is a second statistic over the same hourly CF series and the same
    # per-slice day set that produced SYSHECF, so it is built here rather than
    # through _export_family (which maps one output cell to one source column).
    # It needs the FULL hourly frame, not the collapsed 6x24 profile that
    # SYSHECF is built from — the spread across a slice's days is the whole
    # quantity being measured.
    if hourly_cf_source is None or hourly_cf_source.empty:
        print('WARNING: no hourly capacity-factor source supplied; skipping the ELCCAfR '
              'export. Build it from the run with scripts/build_run_workbooks.py.')
    else:
        elccafr_statistic = str(
            (run_metadata or {}).get('elccafr_statistic', ELCCAfR_STATISTIC_DEFAULT))
        elccafr_demand_altering = float(
            (run_metadata or {}).get('elccafr_demand_altering',
                                     ELCCAfR_DEMAND_ALTERING_DEFAULT))
        elccafr_tables, elccafr_notes = build_all_elccafr_tables(
            hourly_cf_source,
            eps_label_map,
            statistic=elccafr_statistic,
            demand_altering=elccafr_demand_altering,
        )
        for file_name, table in elccafr_tables.items():
            output_path = os.path.join(elccafr_dir, f'{file_name}.csv')
            header = (ELCCAfR_DEMAND_ALTERING_UNIT if file_name == ELCCAfR_DEMAND_ALTERING_FILE
                      else EPS_ELCCAfR_HEADERS[file_name])
            _write_eps_csv(output_path, table, header)
            report_rows.append({
                'family': 'ELCCAfR',
                'file_name': f'{file_name}.csv',
                'status': 'generated',
                'source_column': EPS_ELCCAfR_FILE_MAP.get(file_name, ''),
                'note': elccafr_notes[file_name],
                'output_path': output_path,
            })
            workbook_inputs['ELCCAfR'][file_name] = table

    excel_engine = None
    for candidate in ('xlsxwriter', 'openpyxl'):
        try:
            __import__(candidate)
            excel_engine = candidate
            break
        except ImportError:
            continue

    workbook_specs = {
        'SHELF': os.path.join(root_output_dir, 'Seasonal Hourly Equipment Load Factors by End Use.xlsx'),
        'SYSHECF': os.path.join(root_output_dir, 'Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx'),
        'ELCCAfR': os.path.join(root_output_dir, 'ELCCAfR ELCC Adjustment for Reliability.xlsx'),
    }
    if excel_engine is not None:
        for family, workbook_path in workbook_specs.items():
            with pd.ExcelWriter(workbook_path, engine=excel_engine) as writer:
                family_report = pd.DataFrame(report_rows)
                family_report = family_report[family_report['family'] == family].copy()
                _build_methodology_sheet(family, family_report, run_metadata=run_metadata).to_excel(writer, sheet_name='About', index=False)
                for sheet_name, table in workbook_inputs[family].items():
                    out = table.copy()
                    out.to_excel(writer, sheet_name=sheet_name)
                if not family_report.empty:
                    family_report.to_excel(writer, sheet_name='Coverage', index=False)
                metadata_out = _make_excel_safe(timeslice_metadata.copy())
                metadata_out['eps_label'] = metadata_out.index.map(eps_label_map.to_dict())
                metadata_out.to_excel(writer, sheet_name='TimesliceInfo')
                eps_label_df = pd.DataFrame({
                    'timeslice': eps_label_map.index,
                    'eps_label': eps_label_map.values,
                })
                eps_label_df.to_excel(writer, sheet_name='EPS_Label_Map', index=False)

    report_df = pd.DataFrame(report_rows)
    if not report_df.empty:
        report_df.to_csv(os.path.join(root_output_dir, 'EPS_export_coverage.csv'), index=False)
    return report_df


def export_to_excel(
    capacity_factors: pd.DataFrame,
    load_factors: pd.DataFrame,
    filepath: str,
    cf_sheet_name: str = 'SYSHECF',
    lf_sheet_name: str = 'SHELF',
    timeslice_labels: Optional[pd.Series] = None,
    descriptive_labels: Optional[pd.Series] = None,
    hourly_capacity_factors: Optional[pd.DataFrame] = None,
    hourly_load_factors: Optional[pd.DataFrame] = None,
    timeslice_metadata: Optional[pd.DataFrame] = None,
    eps_template_root: Optional[str] = DEFAULT_EPS_TEMPLATE_ROOT,
    run_metadata: Optional[Dict[str, Any]] = None,
    hourly_cf_source: Optional[pd.DataFrame] = None,
) -> None:
    """Write aggregated capacity and load factors to an Excel workbook.

    The workbook will contain two sheets: one for capacity factors and one for
    load factors.  The timeslice index will appear in the first column.  If
    provided, descriptive labels and timeslice mappings will be added as
    additional sheets.

    Parameters
    ----------
    capacity_factors : pandas.DataFrame
        DataFrame of mean capacity factors indexed by timeslice and with
        technology names as columns.
    load_factors : pandas.DataFrame
        DataFrame of load statistics (mean, max and load factor) indexed by
        timeslice.  Should be produced by ``compute_load_factors``.
    filepath : str
        Path where the Excel workbook will be saved.
    cf_sheet_name : str, default 'SYSHECF'
        Name of the sheet containing capacity factor data.  By default this
        matches the SYSHECF input sheet used in TIMES models.
    lf_sheet_name : str, default 'SHELF'
        Name of the sheet containing load factor data.  By default this
        matches the SHELF input sheet.
    timeslice_labels : pandas.Series, optional
        Original timeslice labels for each hour.  If provided, they will be
        included in an additional sheet named 'TimesliceMap' to document
        which hours belong to each slice.
    descriptive_labels : pandas.Series, optional
        Human‑readable labels for each hour (e.g. produced by
        ``assign_seasonal_labels``).  This is only used if
        ``timeslice_labels`` is also supplied.

    Returns
    -------
    None
        This function writes an Excel file to disk and returns nothing.
    """

    def _safe_write(writer_func, target_path: str) -> str:
        try:
            writer_func(target_path)
            return target_path
        except PermissionError:
            root_name, ext = os.path.splitext(target_path)
            fallback = f"{root_name}_{_datetime.datetime.now():%Y%m%d_%H%M%S}{ext}"
            writer_func(fallback)
            print(f"Target file was locked; wrote fallback output to '{fallback}'.")
            return fallback

    cf_export = hourly_capacity_factors if hourly_capacity_factors is not None and not hourly_capacity_factors.empty else capacity_factors
    lf_export = hourly_load_factors if hourly_load_factors is not None and not hourly_load_factors.empty else load_factors

    mapping_df = None
    if timeslice_labels is not None:
        mapping_df = pd.DataFrame({
            'timeslice_label': timeslice_labels
        })
        if descriptive_labels is not None:
            mapping_df['description'] = descriptive_labels.values
        mapping_df = _make_excel_safe(mapping_df)

    excel_engine = None
    for candidate in ('xlsxwriter', 'openpyxl'):
        try:
            __import__(candidate)
            excel_engine = candidate
            break
        except ImportError:
            continue

    if excel_engine is None:
        root, _ = os.path.splitext(filepath)
        _safe_write(lambda p: cf_export.to_csv(p), f'{root}_{cf_sheet_name}.csv')
        _safe_write(lambda p: lf_export.to_csv(p), f'{root}_{lf_sheet_name}.csv')
        if mapping_df is not None:
            _safe_write(lambda p: mapping_df.to_csv(p), f'{root}_TimesliceMap.csv')
        if hourly_capacity_factors is not None and not hourly_capacity_factors.empty:
            _safe_write(lambda p: capacity_factors.to_csv(p), f'{root}_{cf_sheet_name}_SUMMARY.csv')
        if hourly_load_factors is not None and not hourly_load_factors.empty:
            _safe_write(lambda p: load_factors.to_csv(p), f'{root}_{lf_sheet_name}_SUMMARY.csv')
        if timeslice_metadata is not None and not timeslice_metadata.empty:
            _safe_write(lambda p: timeslice_metadata.to_csv(p), f'{root}_TimesliceInfo.csv')
        if hourly_capacity_factors is not None and not hourly_capacity_factors.empty and hourly_load_factors is not None and not hourly_load_factors.empty:
            export_eps_input_tables(
                root_output_dir=f'{root}_EPS',
                hourly_capacity_factors=hourly_capacity_factors,
                hourly_load_factors=hourly_load_factors,
                timeslice_metadata=timeslice_metadata,
                eps_template_root=eps_template_root,
                run_metadata=run_metadata,
                hourly_cf_source=hourly_cf_source,
            )
        print(
            "No Excel writer backend is installed; wrote CSV files instead of "
            f"'{filepath}'."
        )
        return

    def _write_excel(target_path: str) -> None:
        with pd.ExcelWriter(target_path, engine=excel_engine) as writer:
            cf_export.to_excel(writer, sheet_name=cf_sheet_name)
            lf_export.to_excel(writer, sheet_name=lf_sheet_name)
            if mapping_df is not None:
                mapping_df.to_excel(writer, sheet_name='TimesliceMap')
            if hourly_capacity_factors is not None and not hourly_capacity_factors.empty:
                capacity_factors.to_excel(writer, sheet_name=f'{cf_sheet_name}_SUMMARY')
            if hourly_load_factors is not None and not hourly_load_factors.empty:
                load_factors.to_excel(writer, sheet_name=f'{lf_sheet_name}_SUMMARY')
            if timeslice_metadata is not None and not timeslice_metadata.empty:
                _make_excel_safe(timeslice_metadata.copy()).to_excel(writer, sheet_name='TimesliceInfo')

    _safe_write(_write_excel, filepath)
    if hourly_capacity_factors is not None and not hourly_capacity_factors.empty and hourly_load_factors is not None and not hourly_load_factors.empty:
        root, _ = os.path.splitext(filepath)
        export_eps_input_tables(
            root_output_dir=f'{root}_EPS',
            hourly_capacity_factors=hourly_capacity_factors,
            hourly_load_factors=hourly_load_factors,
            timeslice_metadata=timeslice_metadata,
            eps_template_root=eps_template_root,
            run_metadata=run_metadata,
            hourly_cf_source=hourly_cf_source,
        )


def export_workbook_source_csvs(
    df: pd.DataFrame,
    labels: pd.Series,
    timestamps: pd.Series,
    timeslice_metadata: pd.DataFrame,
    cf_cols: Iterable[str],
    load_cols: Iterable[str],
    root_output_dir: str,
) -> None:
    """Write workbook-source CSVs matching the eps-us xlsx source-tab format.

    These are the hourly source-of-record files a self-contained SHELF/SYSHECF
    workbook (build-input-xlsx pattern) consumes — one row per hour with
    derived day_of_year / hour_of_day / slice columns at the right, mirroring
    the "ResStock national source" and "Cambium hourly source" tab layouts in
    the eps-us workbooks. Written to <root_output_dir>/workbook_sources/:

      demand_hourly_source.csv   timestamp + raw end-use demand columns +
                                 day_of_year / hour_of_day / slice. Category
                                 resolution (direct / sum / template_split per
                                 EPS_SHELF_FILE_MAP) stays in the workbook
                                 formulas — split categories cannot be
                                 represented as single pre-resolved hourly
                                 columns under the representative-day math.
      cf_hourly_source.csv       timestamp, load, net_load, solar/wind gen +
                                 cf columns, derived columns, then one
                                 CF_<tech> column per SYSHECF tech: hourly
                                 series for pipeline-derived techs (solar-pv,
                                 solar-pv-dist, onshore/offshore-wind),
                                 template tables expanded to hourly via each
                                 hour's (slice, hour_of_day) for the rest, so
                                 every SYSHECF tab derives from this one tab.
      clustering.csv             DOY → slice map plus per-slice days and
                                 representative-day DOY (first six rows).
      annual_category_totals.csv informational annual MWh per demand column.

    The invariant (checked by scripts/verify_workbook_sources.py): the
    representative-day math applied to these CSVs reproduces the exported
    SHELF-*.csv / SYSHECF-*.csv files exactly.
    """
    src_dir = os.path.join(root_output_dir, 'workbook_sources')
    os.makedirs(src_dir, exist_ok=True)

    label_map = build_eps_timeslice_label_map(timeslice_metadata)
    n = len(df)
    ts = pd.to_datetime(pd.Series(timestamps).reset_index(drop=True))
    try:
        if ts.dt.tz is not None:
            ts = ts.dt.tz_localize(None)
    except (TypeError, AttributeError):
        pass
    ts_txt = ts.dt.strftime('%Y-%m-%d %H:%M')
    doy = np.arange(n) // 24 + 1
    hod = np.arange(n) % 24
    slice_names = pd.Series(labels).reset_index(drop=True).map(label_map.to_dict())

    load_cols = [c for c in load_cols if c in df.columns]
    cf_cols = [c for c in cf_cols if c in df.columns]

    # ---- demand_hourly_source.csv ----
    demand = pd.DataFrame({'timestamp': ts_txt})
    for c in load_cols:
        demand[c] = pd.to_numeric(df[c], errors='coerce').to_numpy()
    demand['day_of_year'] = doy
    demand['hour_of_day'] = hod
    demand['slice'] = slice_names.to_numpy()
    demand.to_csv(os.path.join(src_dir, 'demand_hourly_source.csv'), index=False)

    # ---- cf_hourly_source.csv ----
    cf = pd.DataFrame({'timestamp': ts_txt})
    for c in ['load', 'net_load', 'solar_gen', 'wind_gen', *cf_cols]:
        if c in df.columns and c not in cf.columns:
            cf[c] = pd.to_numeric(df[c], errors='coerce').to_numpy()
    cf['day_of_year'] = doy
    cf['hour_of_day'] = hod
    cf['slice'] = slice_names.to_numpy()
    slice_idx = slice_names.map(
        {s: i for i, s in enumerate(EPS_TIMESLICE_ORDER)}
    )
    for file_name, spec in EPS_SYSHECF_FILE_MAP.items():
        tech = file_name[len('SYSHECF-'):]
        resolved = resolve_direct_cf_spec(spec, df.columns)
        if resolved is not None:
            column, multiplier = resolved
            series = pd.to_numeric(df[column], errors='coerce').to_numpy()
            cf[f'CF_{tech}'] = series * multiplier
        else:
            csv_path = os.path.join(root_output_dir, 'SYSHECF', f'{file_name}.csv')
            if not os.path.exists(csv_path):
                continue
            tbl = _load_existing_eps_csv(csv_path).reindex(
                index=EPS_TIMESLICE_ORDER, columns=EPS_HOUR_COLUMNS)
            vals = tbl.to_numpy(dtype=float)
            expanded = np.full(n, np.nan)
            ok = slice_idx.notna().to_numpy()
            expanded[ok] = vals[slice_idx[ok].astype(int).to_numpy(), hod[ok]]
            cf[f'CF_{tech}'] = expanded
    cf.to_csv(os.path.join(src_dir, 'cf_hourly_source.csv'), index=False)

    # ---- clustering.csv ----
    days_by_label: Dict[str, int] = {}
    rep_doy_by_label: Dict[str, Optional[int]] = {}
    day_dates = ts.iloc[::24].dt.normalize().reset_index(drop=True)
    for ts_num, eps_label in label_map.items():
        days_by_label[eps_label] = int(
            timeslice_metadata.loc[int(ts_num), 'days_represented'])
        rep_doy_by_label[eps_label] = None
        rep_raw = timeslice_metadata.loc[int(ts_num)].get('representative_date')
        if rep_raw is not None and not pd.isna(rep_raw):
            match = day_dates[day_dates == pd.Timestamp(rep_raw).normalize()]
            if not match.empty:
                rep_doy_by_label[eps_label] = int(match.index[0]) + 1
    n_days = n // 24
    clus = pd.DataFrame({
        'doy': list(range(1, n_days + 1)),
        'slice': [slice_names.iloc[(d - 1) * 24] for d in range(1, n_days + 1)],
    })
    slice_order = [s for s in EPS_TIMESLICE_ORDER if s in days_by_label]
    clus['slice_name'] = pd.Series(slice_order).reindex(clus.index)
    clus['days'] = pd.Series([days_by_label[s] for s in slice_order]).reindex(clus.index)
    clus['rep_doy'] = pd.Series([rep_doy_by_label[s] for s in slice_order]).reindex(clus.index)
    clus.to_csv(os.path.join(src_dir, 'clustering.csv'), index=False)

    # ---- annual_category_totals.csv (informational) ----
    totals = pd.DataFrame({
        'column': load_cols,
        'annual_MWh': [float(pd.to_numeric(df[c], errors='coerce').sum())
                       for c in load_cols],
    })
    totals.to_csv(os.path.join(src_dir, 'annual_category_totals.csv'), index=False)
    print(f"Workbook-source CSVs written to '{src_dir}'.")


def run_pipeline(
    df: pd.DataFrame,
    load_col: str,
    gen_cols: Iterable[str],
    cf_cols: Iterable[str],
    load_cols: Iterable[str],
    n_clusters: int = 6,
    output_path: Optional[str] = None,
    country: Optional[str] = None,
    return_details: bool = False,
    feature_weight_mode: str = 'netload_focus',
    search_seeds: Optional[Iterable[int]] = None,
    run_metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Run the full timeslice aggregation pipeline on the input data.

    This convenience function orchestrates the entire workflow: it computes
    net load, clusters hours into timeslices, aggregates capacity factors
    and load factors, and optionally writes results to an Excel file.

    Parameters
    ----------
    df : pandas.DataFrame
        Hourly data containing load, generation, capacity factor and sectoral
        load columns.  See the module docstring for a description of the
        required columns.
    load_col : str
        Name of the column containing total load.
    gen_cols : Iterable[str]
        Columns for variable generation (kW or MW).  These are subtracted
        from total load to compute net load.
    cf_cols : Iterable[str]
        Columns containing capacity factors (0–1) for each renewable
        technology.  These columns are averaged over each timeslice.
    load_cols : Iterable[str]
        Columns containing end‑use load data for computing load factors.
    n_clusters : int, default 6
        Number of timeslices to generate.
    output_path : str, optional
        If provided, the results will be written to this Excel file.  If
        ``None``, no file is written.
    country : str, optional
        Name of the country or region being processed.  If supplied and
        ``output_path`` is ``None``, the function will choose a default
        output filename of the form ``<country>_timeslice_results.xlsx``.

    Returns
    -------
    capacity_factors : pandas.DataFrame
        Averaged capacity factors by timeslice.
    load_factors : pandas.DataFrame
        Load factor statistics by timeslice.
    labels : pandas.Series
        Timeslice labels for each hour.

    Notes
    -----
    This function is intended to be a high‑level entry point for the
    pipeline.  Users may instead call the constituent functions
    individually if more control is desired.
    """

    timestamps = _extract_timestamps(df)
    # Compute net load
    net = compute_net_load(df, load_col=load_col, gen_cols=gen_cols)
    # Cluster hours into timeslices. The `country` kwarg here drives Southern
    # Hemisphere season-month defaults (Australia, Brazil, Chile, etc.) inside
    # cluster_timeslices. Explicit winter_months / summer_months passed via
    # kwargs would still override.
    labels, model, mapping, representative_dates = cluster_timeslices(
        net,
        timestamps=timestamps,
        n_clusters=n_clusters,
        feature_weight_mode=feature_weight_mode,
        search_seeds=search_seeds,
        country=country,
    )
    # Aggregate capacity factors and load factors
    cf_df = compute_capacity_factors(df, labels, cf_cols)
    lf_df = compute_load_factors(df, labels, load_cols)
    timeslice_metadata = build_timeslice_metadata(timestamps, labels, net, representative_dates=representative_dates)
    if not cf_df.empty:
        cf_df = cf_df.merge(
            timeslice_metadata[['timeslice_name']],
            left_index=True,
            right_index=True,
            how='left',
        )
        cols = ['timeslice_name'] + [c for c in cf_df.columns if c != 'timeslice_name']
        cf_df = cf_df[cols]
    if not lf_df.empty:
        lf_df = lf_df.merge(
            timeslice_metadata[['timeslice_name', 'days_represented']],
            left_index=True,
            right_index=True,
            how='left',
        )
        cols = ['timeslice_name', 'days_represented'] + [c for c in lf_df.columns if c not in {'timeslice_name', 'days_represented'}]
        lf_df = lf_df[cols]

    # SLICE-MEAN, not representative-day (DECISIONS.md 2026-08-12, Option A).
    # `representative_dates` stays the *clustering* objective — it is what makes
    # the optimizer put only genuinely extreme days in the peak slices — but the
    # exported tables are slice means, per CLAUDE.md §6 ("mean demand in slice at
    # that hour / annual demand") and the eps-us workbooks, whose output cells are
    # AVERAGEIFS over slice + hour.
    #
    # Passing representative_dates here instead made each table a single day's
    # profile, which does not conserve annual energy: the SHELF balance
    # Σ_slices days × Σ_hours LF came out anywhere from 0.84 to 2.24 by category
    # rather than 1.0, so EPS would have allocated the wrong annual demand. Slice
    # means give exactly 1.0 by construction.
    hourly_cf_df = compute_hourly_capacity_profiles(
        df,
        labels,
        cf_cols,
        timestamps,
        timeslice_metadata=timeslice_metadata,
    )
    hourly_lf_df = compute_hourly_load_profiles(
        df,
        labels,
        load_cols,
        timestamps,
        timeslice_metadata=timeslice_metadata,
    )
    # Full hourly CF frame for ELCCAfR. hourly_cf_df above is already averaged
    # over each slice's days (that is what SYSHECF wants); ELCCAfR measures the
    # spread across those days, so it needs the un-collapsed series.
    elccafr_cf_source = df[[c for c in cf_cols if c in df.columns]].copy()
    elccafr_cf_source['timeslice'] = labels.values
    elccafr_cf_source['hour_of_day'] = pd.to_datetime(timestamps).dt.hour.values

    # Optionally write to an Excel file
    if output_path or country:
        output_path = resolve_output_path(output_path, country=country)
        export_to_excel(
            cf_df,
            lf_df,
            output_path,
            timeslice_labels=labels,
            descriptive_labels=assign_seasonal_labels(timestamps, labels),
            hourly_capacity_factors=hourly_cf_df,
            hourly_load_factors=hourly_lf_df,
            timeslice_metadata=timeslice_metadata,
            run_metadata=run_metadata,
            hourly_cf_source=elccafr_cf_source,
        )
        # Workbook-source CSVs (eps-us source-tab format) alongside the EPS
        # CSVs. Runs after export_to_excel so the SYSHECF template CSVs exist
        # for CF_<tech> expansion. Auxiliary output — a failure here should
        # not kill the run, but it should be loud.
        try:
            eps_root = f'{os.path.splitext(output_path)[0]}_EPS'
            if os.path.isdir(eps_root):
                export_workbook_source_csvs(
                    df=df,
                    labels=labels,
                    timestamps=timestamps,
                    timeslice_metadata=timeslice_metadata,
                    cf_cols=list(cf_cols),
                    load_cols=list(load_cols),
                    root_output_dir=eps_root,
                )
        except Exception as exc:  # pragma: no cover - defensive
            print(f"WARNING: workbook-source CSV export failed: {exc!r}")
    if return_details:
        return {
            'capacity_factors': cf_df,
            'load_factors': lf_df,
            'labels': labels,
            'hourly_capacity_factors': hourly_cf_df,
            'hourly_load_factors': hourly_lf_df,
            'timeslice_metadata': timeslice_metadata,
            'representative_dates': representative_dates,
            'model': model,
            'mapping': mapping,
        }
    return cf_df, lf_df, labels


if __name__ == '__main__':  # pragma: no cover
    # All run-time settings (country, year, clustering, etc.) live in
    # run_pipeline.py. This module is library code — please launch via:
    #
    #     python run_pipeline.py
    #
    # That file holds every setting you should normally need to edit, with
    # inline documentation. Calling this script directly does nothing useful.
    import sys
    sys.stderr.write(
        "energy_timeslice_pipeline.py is a library module.\n"
        "Run the pipeline via:  python run_pipeline.py\n"
        "(All editable settings live there, with inline documentation.)\n"
    )
    sys.exit(2)
