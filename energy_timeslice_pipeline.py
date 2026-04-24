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
from typing import Iterable, Tuple, Dict, Optional, Any

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
    'SYSHECF-onshore-wind': {'mode': 'direct', 'column': 'wind_cf'},
    'SYSHECF-solar-pv': {'mode': 'direct', 'column': 'solar_cf'},
    'SYSHECF-solar-thermal': None,
    'SYSHECF-biomass': None,
    'SYSHECF-geothermal': None,
    'SYSHECF-petroleum': None,
    'SYSHECF-natural-gas-peaker': None,
    'SYSHECF-offshore-wind': {'mode': 'direct', 'column': 'wind_cf'},
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

COUNTRY_PRESETS: Dict[str, Dict[str, Any]] = {
    'south korea': {
        'aliases': ['korea', 'republic of korea', 'kr', 'kor', 'southkorea'],
        'output_country': 'SouthKorea',
        'country_iso2': 'KR',
        'demand_country_code': 'KOR',
        'mendeley_region_name': 'Korea',
        'ember_country_name': 'South Korea',
        'demand_shape_source': 'mendeley',
        'default_year': 2025,
        'last_n_years': 4,
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
        'default_year': 2018,
        'last_n_years': 1,
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
        'default_year': 2025,
        'last_n_years': 3,
        'status': 'mapped',
    },
}

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
) -> pd.DataFrame:
    """Load U.S. hourly end-use demand using NREL's Electrification Futures Study."""
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


def generate_full_pipeline_for_preset(
    country: str,
    year: Optional[int] = None,
    n_clusters: int = 6,
    output_path: Optional[str] = None,
    last_n_years: Optional[int] = None,
    data_dir: str = DEFAULT_DATA_DIR,
    seasonal_calibration: bool = True,
    scenario: str = 'SSP2',
    **kwargs,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Run the full pipeline using a built-in country preset."""
    preset = get_country_preset(country)
    selected_year = year or preset['default_year']
    selected_last_n_years = last_n_years or preset.get('last_n_years', 3)
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
        efs_electrification=preset.get('efs_electrification', 'Reference'),
        efs_technology_advancement=preset.get('efs_technology_advancement', 'Moderate'),
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


def calibrate_capacity_factors(
    cf_df: pd.DataFrame,
    observed_cf: Dict[str, float],
    rename_map: Dict[str, str] = None,
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
        names in ``cf_df``.  For example, ``{'Solar': 'solar_cf', 'Wind':
        'wind_cf'}``.  If ``None``, the keys of ``observed_cf`` must
        directly match the column names in ``cf_df``.

    Returns
    -------
    pandas.DataFrame
        Scaled capacity factor time series.  Each column in ``cf_df`` is
        multiplied by a constant factor so that its mean equals the
        corresponding observed value.  Columns without a matching entry in
        ``observed_cf`` are returned unchanged.

    Notes
    -----
    * If the mean of a simulated capacity factor column is zero, the
      corresponding scaling factor is set to 0 to avoid division by zero.
    * This function does not impose any upper or lower bounds on the
      resulting capacity factors; clipping (0–1) should be applied after
      scaling if necessary.
    """
    df_scaled = cf_df.copy()
    mapping = rename_map or {k: k for k in observed_cf}
    for obs_key, obs_value in observed_cf.items():
        col = mapping.get(obs_key)
        if col not in df_scaled.columns:
            continue
        sim_mean = df_scaled[col].mean()
        if sim_mean <= 0 or np.isnan(sim_mean):
            factor = 0.0
        else:
            factor = obs_value / sim_mean
        df_scaled[col] = df_scaled[col] * factor
    return df_scaled


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
    # Step 1: Load synthetic end‑use demand for the selected year
    if demand_shape_source == 'efs':
        if not efs_dir:
            raise ValueError("efs_dir is required when demand_shape_source='efs'.")
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
        )
    elif demand_shape_source == 'mendeley':
        df_synthetic = load_enduse_data_mendeley(mendeley_root, mendeley_region_name, year, scenario)
    else:
        raise ValueError(
            f"Unsupported demand_shape_source '{demand_shape_source}'. Expected 'mendeley' or 'efs'."
        )
    # Step 2: Fetch real demand over the most recent N years and compute average
    calibration_start_year = year - last_n_years + 1
    calibration_end_year = year
    real_demand = fetch_demand_data_demandcast(
        demand_country_code,
        start_year=calibration_start_year,
        end_year=calibration_end_year,
    )
    # Determine calibration years (last_n_years ending at 'year')
    cal_start_year = year - last_n_years + 1
    cal_end_year = year
    real_demand_filtered = real_demand[(real_demand.index.year >= cal_start_year) & (real_demand.index.year <= cal_end_year)]
    # Calibrate synthetic load to match average real demand over the selected years
    df_scaled = calibrate_synthetic_load(df_synthetic, real_demand_filtered, load_col='load')
    df_calibrated = df_scaled
    if seasonal_calibration:
        df_calibrated = calibrate_seasonal_enduse_load(
            df_scaled,
            real_demand_filtered,
            load_col='load',
        )
    # Step 3: Load weather data and compute capacity factors
    weather_df = load_weather_data(weather_dir, country_iso2, ['irradiance_surface', 'temperature', 'wind_speed'], weight, dataset)
    # Filter weather to the selected year
    weather_year = weather_df[(weather_df.index.year >= cal_start_year) & (weather_df.index.year <= cal_end_year)]
    # Compute capacity factors
    cf_df = compute_capacity_factors_from_weather(
        weather_year,
        pv_irradiance_col='irradiance_surface',
        temp_col='temperature',
        wind_col='wind_speed',
        orientation_factor=orientation_factor,
        roughness_length=roughness_length,
    )
    # Step 4: Calibrate capacity factors using Ember statistics
    capacities, observed_cf = load_ember_annual_capacity_factors(
        ember_csv_path, country=ember_country_name, variables=['Solar', 'Wind'], last_n_years=last_n_years
    )
    cf_scaled = calibrate_capacity_factors(cf_df, observed_cf, rename_map={'Solar': 'solar_cf', 'Wind': 'wind_cf'})
    # Step 5: Compute generation (MW) from capacity factors using average installed capacity
    # Convert installed capacity from GW to MW
    solar_cap = capacities.get('Solar', 0.0) * 1000.0
    wind_cap = capacities.get('Wind', 0.0) * 1000.0
    gen_df = pd.DataFrame(index=cf_scaled.index)
    gen_df['solar_cf'] = cf_scaled['solar_cf']
    gen_df['wind_cf'] = cf_scaled['wind_cf']
    gen_df['solar_gen'] = cf_scaled['solar_cf'] * solar_cap
    gen_df['wind_gen'] = cf_scaled['wind_cf'] * wind_cap
    # Align generation with synthetic demand index (synthetic year).  We align by time of year.
    # Create a mapping from day of year and hour to mean generation across the calibration years.
    gen_df['doy'] = gen_df.index.dayofyear
    gen_df['hour'] = gen_df.index.hour
    # Average generation for each DOY and hour
    gen_avg = gen_df.groupby(['doy', 'hour']).mean()[['solar_cf', 'wind_cf', 'solar_gen', 'wind_gen']]
    # Construct generation series for the synthetic year
    synthetic_year_dates = df_calibrated.index
    doy = synthetic_year_dates.dayofyear
    hour = synthetic_year_dates.hour
    gen_interp = gen_avg.loc[list(zip(doy, hour))].reset_index(drop=True)
    gen_interp.index = synthetic_year_dates
    # Add generation columns to the calibrated demand DataFrame
    df_with_gen = df_calibrated.copy()
    df_with_gen['solar_cf'] = gen_interp['solar_cf'].values
    df_with_gen['wind_cf'] = gen_interp['wind_cf'].values
    df_with_gen['solar_gen'] = gen_interp['solar_gen'].values
    df_with_gen['wind_gen'] = gen_interp['wind_gen'].values
    # Step 6: Compute net load by subtracting generation
    df_with_gen['net_load'] = df_with_gen['load'] - df_with_gen['solar_gen'] - df_with_gen['wind_gen']
    # Use net load for clustering; pass generation columns for subtraction in run_pipeline
    gen_cols = ['solar_gen', 'wind_gen']
    cf_cols = ['solar_cf', 'wind_cf']
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
        'demand_shape_source': df_synthetic.attrs.get('demand_shape_source', demand_shape_source),
        'demand_shape_source_year': df_synthetic.attrs.get('demand_shape_source_year', year),
        'demand_shape_source_scenario': df_synthetic.attrs.get('demand_shape_source_scenario', scenario),
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
    metrics_df = pd.concat([metrics_df, clustering_metrics, comparison_metrics], ignore_index=True)
    write_metrics_reports(metrics_df, resolved_output_path)
    print_metrics_summary(region_name, metrics_df)
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


def fetch_demand_data_demandcast(
    country_code: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
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
) -> Tuple[pd.Series, KMeans, Dict[int, int], Dict[int, pd.Timestamp]]:
    """Cluster daily net-load profiles into representative-day timeslices."""
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
            pinned_dates.append(summer_candidates.idxmax())
        if not winter_candidates.empty:
            winter_peak_date = winter_candidates.idxmax()
            if winter_peak_date not in pinned_dates:
                pinned_dates.append(winter_peak_date)

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

    for seed in seen_seeds:
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
        if score < best_score:
            best_score = score
            best_labels = daily_labels
            best_model = model
            best_mapping = mapping
            best_representative_dates = representative_dates

    if best_labels is None or best_model is None or best_mapping is None or best_representative_dates is None:
        raise RuntimeError("Failed to identify a valid timeslice clustering solution.")

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
    """Compute 24 hourly mean capacity factors for each timeslice."""
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
    """Compute 24 hourly representative-day load shares for each timeslice."""
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
            '6. Onshore and offshore wind currently use the calibrated wind profile; other non-variable technologies remain template-based unless a specific derivation is added.',
            '7. Coverage and file provenance are documented on the Coverage sheet.',
        ]
    if run_metadata:
        lines.append('Run Metadata')
        for key in ('country', 'demand_shape_source', 'demand_shape_source_year', 'demand_shape_source_scenario'):
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
) -> pd.DataFrame:
    """Export EPS-ready SHELF and SYSHECF files plus a coverage report."""
    if timeslice_metadata is None or timeslice_metadata.empty:
        return pd.DataFrame()
    if hourly_capacity_factors is None or hourly_capacity_factors.empty:
        return pd.DataFrame()
    if hourly_load_factors is None or hourly_load_factors.empty:
        return pd.DataFrame()

    os.makedirs(root_output_dir, exist_ok=True)
    shelf_dir = os.path.join(root_output_dir, 'SHELF')
    syshecf_dir = os.path.join(root_output_dir, 'SYSHECF')
    os.makedirs(shelf_dir, exist_ok=True)
    os.makedirs(syshecf_dir, exist_ok=True)

    eps_label_map = build_eps_timeslice_label_map(timeslice_metadata)
    report_rows: list[Dict[str, Any]] = []
    workbook_inputs: Dict[str, Dict[str, pd.DataFrame]] = {'SHELF': {}, 'SYSHECF': {}}

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
        )


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
    # Cluster hours into timeslices
    labels, model, mapping, representative_dates = cluster_timeslices(
        net,
        timestamps=timestamps,
        n_clusters=n_clusters,
        feature_weight_mode=feature_weight_mode,
        search_seeds=search_seeds,
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

    hourly_cf_df = compute_hourly_capacity_profiles(
        df,
        labels,
        cf_cols,
        timestamps,
        timeslice_metadata=timeslice_metadata,
        representative_dates=representative_dates,
    )
    hourly_lf_df = compute_hourly_load_profiles(
        df,
        labels,
        load_cols,
        timestamps,
        timeslice_metadata=timeslice_metadata,
        representative_dates=representative_dates,
    )
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
        )
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
    # Set the country name here for direct script runs.
    RUN_CONFIG = {
        'country': 'South Korea',
        'year': None,
        'n_clusters': 6,
        'output_path': None,
        'last_n_years': None,
        'use_example_data': False,
    }

    if RUN_CONFIG.get('use_example_data'):
        import datetime as dt  # noqa: F401

        # Generate a year of hourly timestamps
        timestamps = pd.date_range(start='2025-01-01', end='2025-12-31 23:00', freq='h')
    else:
        print("Available country presets:")
        print(list_country_presets().to_string(index=False))
        generate_full_pipeline_for_preset(
            country=RUN_CONFIG['country'],
            year=RUN_CONFIG.get('year'),
            n_clusters=RUN_CONFIG['n_clusters'],
            output_path=RUN_CONFIG['output_path'],
            last_n_years=RUN_CONFIG.get('last_n_years'),
        )
        raise SystemExit(0)
    n = len(timestamps)
    # Create synthetic load data with seasonal patterns and random noise
    np.random.seed(42)
    base_load = 5000 + 1000 * np.sin(2 * np.pi * timestamps.dayofyear / 365)
    hourly_variation = 300 * np.sin(2 * np.pi * timestamps.hour / 24)
    noise = 500 * np.random.randn(n)
    load = base_load + hourly_variation + noise
    # Synthetic renewable generation (solar and wind) capacity factors
    solar_cf = np.clip(0.5 * np.sin(2 * np.pi * timestamps.hour / 24 - np.pi/2), 0, 1)
    wind_cf = np.clip(0.3 + 0.2 * np.sin(2 * np.pi * timestamps.hour / 24 + np.pi/4), 0, 1)
    # Assume installed capacities (MW) for solar and wind
    solar_capacity = 2000
    wind_capacity = 3000
    solar_gen = solar_cf * solar_capacity
    wind_gen = wind_cf * wind_capacity
    # End‑use loads: residential and industrial (synthetic)
    residential = 0.4 * load + 100 * np.random.randn(n)
    industrial = 0.6 * load + 200 * np.random.randn(n)
    # Assemble DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'load': load,
        'solar_gen': solar_gen,
        'wind_gen': wind_gen,
        'solar_cf': solar_cf,
        'wind_cf': wind_cf,
        'residential': residential,
        'industrial': industrial,
    })
    # Run the pipeline
    results = run_pipeline(
        df,
        load_col='load',
        gen_cols=['solar_gen', 'wind_gen'],
        cf_cols=['solar_cf', 'wind_cf'],
        load_cols=['residential', 'industrial'],
        n_clusters=RUN_CONFIG['n_clusters'],
        output_path=RUN_CONFIG['output_path'],
        country=RUN_CONFIG['country'],
        return_details=True,
    )
    cf_df = results['capacity_factors']
    lf_df = results['load_factors']
    hourly_lf_df = results['hourly_load_factors']
    timeslice_metadata = results['timeslice_metadata']
    # Display summary statistics
    print("Capacity factors by timeslice:")
    print(cf_df)
    print("\nRepresentative-day shares by timeslice:")
    print(lf_df.head())
    print("\nPinned and labeled timeslices:")
    print(timeslice_metadata[['timeslice_name', 'is_pinned_summer', 'is_pinned_winter']])
    print("\nHourly sector-service annual shares by timeslice (first 12 rows):")
    hourly_cols = [c for c in hourly_lf_df.columns if c.endswith('_load_factor')]
    print(hourly_lf_df[hourly_cols].head(12))
