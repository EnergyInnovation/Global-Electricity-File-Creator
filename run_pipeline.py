"""
run_pipeline.py — User-facing runner for the energy timeslice pipeline.

This is the ONLY file you should normally need to edit. All execution code
lives in ``energy_timeslice_pipeline.py``. Edit the CONFIG sections below,
then run:

    python run_pipeline.py

Sections are ordered from "most often changed" at the top to "rarely changed"
at the bottom. Every setting documents what it does and what values are valid.

Outputs land under ``output/`` by default; see the OUTPUT_PATH setting for
how to override.

Note for staff:
    Treat any results from this pipeline as a draft input for review, not a
    finished EI position. Verify country presets, calibration data, and
    derived capacity factors against primary sources before publishing.
"""

# ============================================================================
# 1. COUNTRY AND YEAR  (change these almost every run)
# ============================================================================

# Which country preset to run.
#
# Verified countries (have been validated end-to-end):
#     'South Korea', 'China', 'United States'
#
# Mapped but not yet revalidated (the preset exists but the run hasn't been
# checked recently — expect to debug if you pick one of these):
#     'Australia', 'Brazil', 'Canada', 'France', 'Germany',
#     'India', 'Japan', 'Mexico', 'United Kingdom'
#
# Run the pipeline once to see the full preset table printed to the console.
# Aliases work too (e.g. 'KR', 'kor', 'southkorea' all resolve to South Korea).
COUNTRY = 'South Korea'

# Target year for the synthetic representative-day output.
#
# - Set to None to use the preset's ``default_year`` (recommended for most users).
# - Set to an integer to override (e.g. 2030, 2050).
# - For United States runs: the EFS dataset only contains the years
#   2018, 2020, 2024, 2030, 2040, 2050. If you pick something else, the
#   pipeline maps to the nearest available year (e.g. 2025 → 2024).
# - For non-US (Mendeley) runs: years 1971–2100 are valid.
YEAR = None


# ============================================================================
# 2. CLUSTERING AND CALIBRATION  (occasional changes)
# ============================================================================

# Number of representative timeslices (days) to cluster the year into.
#
# The EPS workbook format expects 6, with two of them pinned to summer and
# winter peak days. Changing this will produce non-EPS-compatible output.
# Don't change unless you know what you're doing.
N_CLUSTERS = 6

# How many recent years of observed demand to use for calibration.
#
# - None = use the preset's default (varies by country, typically 1–4 years).
# - Larger windows smooth weather variability but blur recent demand changes.
# - Calibration data sources: DemandCast (most countries), EIA (United States),
#   KROGD (South Korea — files in data/manual_downloads/).
LAST_N_YEARS = None

# Whether to apply the seasonal-mean calibration step in addition to the
# annual-level scaling. Almost always desirable — disable only when
# debugging or comparing a "raw scaled" baseline.
SEASONAL_CALIBRATION = True

# Custom path for the main Excel workbook. None = auto-name in output/
# based on country (e.g. ``output/SouthKorea_timeslice_results.xlsx``).
# Set to a string to override (e.g. ``'output/MyRun.xlsx'``).
# Note: the EPS CSV/workbook files are always written to a folder named
# after the workbook; renaming here renames the EPS folder too.
OUTPUT_PATH = None


# ============================================================================
# 3. DEMAND-SHAPE PARAMETERS  (advanced — rarely change)
# ============================================================================

# Mendeley dataset SSP scenario for non-U.S. demand shapes.
# The dataset distributes only 'SSP2'; other SSPs would require a different
# upstream source.
SCENARIO = 'SSP2'

# NREL Electrification Futures Study (EFS) settings — UNITED STATES ONLY.
#
# These are pulled from the United States preset by default (Reference /
# Moderate). To change them, edit the 'united states' preset dict inside
# energy_timeslice_pipeline.py rather than overriding here — the preset
# function ignores overrides for these.
#
# Documented for reference:
#     EFS_ELECTRIFICATION choices: 'Reference', 'Moderate', 'High'
#     EFS_TECHNOLOGY_ADVANCEMENT choices: 'Slow', 'Moderate', 'Rapid'


# ============================================================================
# 4. WEATHER AND PHYSICS  (advanced — rarely change)
# ============================================================================

# Renewables.ninja weighting scheme used to fetch country-aggregated weather.
#
#   'area' = area-weighted (the only scheme actually present in the data/
#            weather/ files; matches the file naming convention)
#   'pop'  = population-weighted (would require differently-named files)
WEATHER_WEIGHT = 'area'

# Renewables.ninja meteorological dataset.
#   'merra2' = MERRA-2 reanalysis (the only dataset present locally)
WEATHER_DATASET = 'merra2'

# Solar PV orientation/tilt factor passed to the capacity-factor calculator.
# 1.0 = horizontal panels; 1.1 ≈ moderate tilt for typical mid-latitudes.
SOLAR_ORIENTATION_FACTOR = 1.1

# Surface roughness length (meters) used to scale wind speed from 10 m
# (renewables.ninja default) to hub height. 0.03 ≈ open countryside.
# Higher values → more wind shear → lower hub-height speeds.
WIND_ROUGHNESS_LENGTH = 0.03


# ============================================================================
# 5. PATHS  (only change if you've moved or renamed data directories)
# ============================================================================

# Base directory for input data.
#   None = use pipeline default (``<repo>/data/``)
#   Otherwise: an absolute or relative path to a folder containing the
#   ``mendeley/``, ``efs/``, ``weather/``, ``ember/``, ``manual_downloads/``
#   subfolders.
DATA_DIR = None


# ============================================================================
# 6. CACHE  (performance — recommended ON)
# ============================================================================

# Cache parsed-and-filtered intermediates to ``data/cache/*.parquet`` so
# subsequent runs skip the slow CSV parsing in the demand-shape and weather
# loaders.
#
# Effect on pipeline correctness: NONE. The cache only stores the result of
# parsing and filtering source files; modeling, calibration, and clustering
# are unchanged. Output is bit-for-bit identical to a non-cached run.
#
# When the cache is rebuilt:
#   * first run after cloning the repo (no cache yet)
#   * any source file (Mendeley CSV, EFS zip, weather CSV, or — for U.S. runs
#     — the RECS workbook) is newer than its cache file
#
# What gets cached:
#   * data/cache/mendeley_<region>_<year>_<scenario>.parquet
#   * data/cache/efs_<elec>_<tech>_<year>_<region>_<scenario>.parquet  (U.S.)
#   * data/cache/weather_<ISO2>_<dataset>_<weight>_<vars>.parquet
#
# To force a clean rebuild: just delete data/cache/ — it's never required.
#
# Set False if you want to verify a fresh run end-to-end, or if you
# suspect the cache has been corrupted.
USE_CACHE = True

# Override where parquet caches are written. None = ``<DATA_DIR>/cache/``
# (recommended). Set to a path string to put caches on a faster disk or a
# shared drive.
CACHE_DIR = None


# ============================================================================
# Execution  (DO NOT EDIT BELOW THIS LINE)
# ============================================================================

import os
import energy_timeslice_pipeline as pipeline


def _effective_cache_dir() -> "str | None":
    """
    Resolve the cache directory to pass into the pipeline.

    Order of precedence:
      1. CACHE_DIR (if set explicitly above)
      2. <DATA_DIR>/cache  (if DATA_DIR is set)
      3. <pipeline default data dir>/cache  (the normal project layout)

    Always returns an explicit path when USE_CACHE is True, so the loaders
    don't fall back to per-subdir cache locations like data/weather/cache.
    """
    if not USE_CACHE:
        return None
    if CACHE_DIR is not None:
        return CACHE_DIR
    base = DATA_DIR if DATA_DIR is not None else pipeline.DEFAULT_DATA_DIR
    return os.path.join(base, 'cache')


def main() -> None:
    print("Available country presets:")
    print(pipeline.list_country_presets().to_string(index=False))
    print()
    print(f"Running pipeline: country={COUNTRY!r}, year={YEAR}, "
          f"n_clusters={N_CLUSTERS}, last_n_years={LAST_N_YEARS}, "
          f"use_cache={USE_CACHE}")
    print()

    kwargs = {
        'country': COUNTRY,
        'year': YEAR,
        'n_clusters': N_CLUSTERS,
        'output_path': OUTPUT_PATH,
        'last_n_years': LAST_N_YEARS,
        'seasonal_calibration': SEASONAL_CALIBRATION,
        'scenario': SCENARIO,
        # Forwarded via **kwargs to generate_full_pipeline_for_country:
        'weight': WEATHER_WEIGHT,
        'dataset': WEATHER_DATASET,
        'orientation_factor': SOLAR_ORIENTATION_FACTOR,
        'roughness_length': WIND_ROUGHNESS_LENGTH,
        'use_cache': USE_CACHE,
        'cache_dir': _effective_cache_dir(),
    }
    if DATA_DIR is not None:
        kwargs['data_dir'] = DATA_DIR

    pipeline.generate_full_pipeline_for_preset(**kwargs)


if __name__ == '__main__':
    main()
