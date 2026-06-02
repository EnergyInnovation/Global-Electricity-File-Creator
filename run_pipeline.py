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

import sys
# Force UTF-8 on stdout/stderr so status messages containing → ° etc. don't
# crash on Windows cp1252 consoles. No-op on Python <3.7 or on non-TextIO
# streams (covered by the try/except).
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass


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
COUNTRY = 'China'

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
# annual-level scaling. Only used when CALIBRATION_METHOD = 'level_seasonal'.
# Ignored when CALIBRATION_METHOD = 'zapata_nnls'.
SEASONAL_CALIBRATION = True

# Calibration method for matching the Mendeley/Zapata synthetic shapes to
# DemandCast observed totals.
#
#   'level_seasonal' (default, legacy) — multiplicative annual scaling
#       then per-month and per-peak adjustments. Matches the production
#       behavior pre-Zapata-integration. Annual mean matches exactly by
#       construction; hourly NRMSE typically ~1.7–2.0 (worse than naive
#       mean, since shape is unchanged).
#
#   'zapata_nnls' — regenerate the four climate-sensitive end-uses
#       (residential cooling/heating/lighting + service cooling) from
#       country-specific weather + HETUS occupancy + Forsythe daylength
#       using Zapata 2022 stylized functions, then solve monthly NNLS for
#       end-use weights against observed totals. Hourly NRMSE was 0.67
#       (Korea 2024) and 1.06 (China 2018) in standalone tests — the
#       first calibration to beat the naive-mean baseline. Suffers from
#       basis-collinearity zero-flips that produce NaN/0 cells in SHELF
#       outputs (e.g. industry going to zero in some timeslices).
#
#   'zapata_ridge_nnls' — Path B. Same shape regeneration as zapata_nnls,
#       but first aligns all 11 basis columns to EPS-extracted per-end-use
#       MWh/year magnitudes, then solves a ridge-regularized NNLS that
#       anchors weights to w=1 (= EPS prior). Eliminates the zero-flip
#       pathology while preserving the climate-sensitive shape signal.
#       Self-consistent with how EPS consumes SHELF output (EPS provides
#       magnitudes, our SHELF provides shape). REQUIRES the country preset
#       to include an 'eps_prior_path' field pointing to a CSV produced by
#       data/eps_priors/parse_eps_extract.py from the country's EPS run.
#
# Requires the country preset to include a 'latitude_deg' field. All 12
# verified/mapped presets in energy_timeslice_pipeline.py already have it.
# See zapata_implementation_readme.md for methodology, assumptions, and
# the full standalone-test result comparison.
CALIBRATION_METHOD = 'zapata_ridge_nnls'  # 'zapata_nnls'  'level_seasonal'

# Ridge regularization strength for zapata_ridge_nnls. Ignored otherwise.
#   0.0   — pure NNLS, equivalent to zapata_nnls (no EPS-prior anchoring)
#   1.0   — equal weight to fit residual and prior deviation (recommended start)
#   >>1.0 — strong anchoring to EPS prior, suppresses NNLS adjustment
#   <<1.0 — weak anchoring, NNLS dominates (zero-flip risk returns)
LAMBDA_RIDGE = 1.0

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

# Capacity factor calibration mode for scaling synthetic solar/wind
# capacity factors so their annual mean matches the value reported by
# Ember.
#
#   'cap_redistribute' (recommended, default) — multiply, clip values >1
#       to 1.0, then redistribute the clipped energy across unsaturated
#       hours so the annual mean still hits the target. Bounded by
#       construction (every output is in [0, 1]).
#
#   'multiplicative' — legacy method. Pure scalar multiplication. Can
#       produce capacity factor values >1.0 when the implied multiplier
#       is large (e.g., when the synthetic profile underestimates real
#       wind speeds). Retained only for backward-compat / diff comparison
#       against pre-fix runs. Do not use for any output you intend to
#       hand off downstream.
#
# When the implied multiplier (Ember-target ÷ synthetic-mean) exceeds 1.5
# the pipeline emits a UserWarning regardless of mode — that's a sign the
# synthetic shape itself needs upstream tuning (hub height, roughness
# length, power-curve assumptions). See HANDOFF.md → "Weather Data
# Improvements" for the full discussion.
CF_CALIBRATION_MODE = 'cap_redistribute'


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
# 7. STATUS REPORTING  (controls how much progress info the run prints)
# ============================================================================

# How chatty the pipeline should be while running.
#
#   'quiet'   = only Python warnings/errors and the final [Metrics] summary.
#               Use when piping output to a file you don't plan to watch.
#
#   'normal'  = recommended default. One status line per pipeline milestone:
#               loading data, calibrating demand, weather, capacity factors
#               (with calibration diagnostics), clustering, metrics, outputs.
#               About 25–30 lines total per run.
#
#   'verbose' = adds per-seed k-means scoring details inside the clustering
#               loop (~9 extra lines). Mostly useful for debugging or
#               investigating clustering quality across seeds.
VERBOSITY = 'normal'


# ============================================================================
# 8. DIAGNOSTIC PLOTS  (visual cluster inspection — optional)
# ============================================================================

# When True, the pipeline writes 24 PNG plots per run (6 timeslices × 4
# variables: net_load, solar_cf, wind_cf, normalized hourly load) under
# ``output/<country>_timeslice_results_plots/``. Each plot shows every day
# in that cluster as a thin grey line, plus a 25–75th percentile band and
# the cluster-mean profile. On the ``net_load`` plot only, the cluster's
# representative day is overlaid in red.
#
# Useful for spot-checking how tight (or loose) each cluster is and how
# well the representative day stands in for the rest of the cluster. Adds
# ~3–5 seconds to a run.
#
# Requires `matplotlib` (already in requirements.txt). If matplotlib is
# unavailable the pipeline skips the plots with a warning and continues.
MAKE_DIAGNOSTIC_PLOTS = True


# ============================================================================
# 9. PINNED-VS-UNPINNED COMPARISON  (diagnostic — off by default)
# ============================================================================

# When True, the pipeline re-runs the clustering step twice (once with
# pinned summer/winter peak days, once without) and writes both NRMSE
# values to the metrics CSV. The pair quantifies how much the pinning
# constraint costs (or saves) on annual net-load reconstruction — useful
# for methodology disclosure when bringing a new country online.
#
# Cost: roughly doubles the clustering wall time (~10–30 seconds extra
# for South Korea, more for the U.S. EFS run). The "pinned" answer here
# is redundant with the production clustering that already ran above;
# enabling this gets you the "unpinned" baseline at the cost of also
# repeating the pinned work for symmetry.
#
# Default is False so routine runs are fast. Flip to True when validating
# a new preset, when reviewing the methodology, or when generating the
# pinned-vs-unpinned NRMSE pair for a publication or report.
COMPARE_PINNED_UNPINNED = False


# ============================================================================
# 10. CALIBRATION-ONLY MODE  (fast iteration on calibration choices)
# ============================================================================

# When True, the pipeline runs the demand-shape load and calibration steps,
# writes the calibration_overview.png plot, and then exits — no weather
# loading, no capacity factor computation, no clustering, no EPS export.
#
# Useful when you're iterating on calibration parameters (level scaling,
# seasonal calibration, calibration window) and only want to see the
# resulting overview plot without paying for the full pipeline.
#
# Default False = full pipeline.
CALIBRATION_ONLY = False #True


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
    import time as _time
    pipeline.set_verbosity(VERBOSITY)

    print("Available country presets:")
    print(pipeline.list_country_presets().to_string(index=False))
    print()

    pipeline._status(
        'setup',
        f"country={COUNTRY!r}  year={YEAR if YEAR is not None else 'preset default'}  "
        f"n_clusters={N_CLUSTERS}  last_n_years={LAST_N_YEARS if LAST_N_YEARS is not None else 'preset default'}  "
        f"use_cache={USE_CACHE}  verbosity={VERBOSITY!r}",
    )

    _run_start = _time.perf_counter()

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
        'cf_calibration_mode': CF_CALIBRATION_MODE,
        'make_plots': MAKE_DIAGNOSTIC_PLOTS,
        'compare_pinned_unpinned': COMPARE_PINNED_UNPINNED,
        'calibration_only': CALIBRATION_ONLY,
        'calibration_method': CALIBRATION_METHOD,
        'lambda_ridge': LAMBDA_RIDGE,
    }
    if DATA_DIR is not None:
        kwargs['data_dir'] = DATA_DIR

    pipeline.generate_full_pipeline_for_preset(**kwargs)

    pipeline._status('done', "run complete", t=_run_start)


if __name__ == '__main__':
    main()
