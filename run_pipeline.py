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
YEAR = 2023#None


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
#   KROGD (South Korea — files in data/manual_downloads/), Yi et al. 2026
#   (China — see DEMAND_SERIES_CSV below).
# - CHINA: this setting, together with YEAR, selects which observed demand
#   source is used. See DEMAND_SERIES_CSV.
LAST_N_YEARS = 4#None

# Observed hourly demand source override.
#
#   None (recommended) — let the country preset decide.
#   'demandcast'       — force the DemandCast retrieval path.
#   '<path to CSV>'    — force a staged hourly demand CSV (columns: a timestamp
#                        in the country's local time, and demand in MW).
#
# CHINA has two observed records and the preset picks between them from the run
# configuration, because they cover different periods and disagree on hourly
# shape even where they overlap:
#
#   YEAR = 2018 and LAST_N_YEARS = 1  (the China preset defaults)
#       → DemandCast / Wu et al. The legacy baseline. This source covers 2018
#         only, which is the only configuration it can serve. Keeping it as the
#         default means the historical EPS-China run stays reproducible.
#
#   any other YEAR or LAST_N_YEARS
#       → Yi, B., Luo, Q., Zhang, S., Ji, Y., Yu, S. & Fan, Y. (2026). Hourly
#         electricity load curve dataset for Chinese provinces derived from
#         meteorological variables. Scientific Data 13, 978.
#         https://doi.org/10.1038/s41597-026-07327-8
#         Data: figshare https://doi.org/10.6084/m9.figshare.29832701
#         (CC BY-NC-ND 4.0). 31 provinces, hourly, 2015–2024, GWh/h; summed to
#         a national MW series by scripts/build_china_hourly_demand.py into
#         data/manual_downloads/CN_hourly_demand_2015_2024.csv.
#
#         Note: 2024 is a leap year and the run's days-per-timeslice currently
#         sums to 366 rather than the 365 EPS expects. Prefer YEAR = 2023 until
#         that is fixed. See output/china_demand_source_test/RESULTS.md.
#
# The run log prints which source was used and its citation.
DEMAND_SERIES_CSV = None

# Whether to apply the seasonal-mean calibration step in addition to the
# annual-level scaling. Only used when CALIBRATION_METHOD = 'level_seasonal'.
# Ignored when CALIBRATION_METHOD = 'zapata_nnls'.
SEASONAL_CALIBRATION = True

# Calibration method for matching the Mendeley/Zapata synthetic shapes to
# DemandCast observed totals.
#
#   None (recommended) — use the country preset's default:
#       United States       → 'level_seasonal'  (pinned to legacy master-branch
#                             behavior so US clustering outputs stay comparable
#                             with the historical baseline)
#       South Korea / China → 'zapata_ridge_nnls'
#       other presets       → 'level_seasonal' (no 'calibration_method' field)
#     A non-None value here overrides the preset for this run.
#
#   'level_seasonal' (legacy) — multiplicative annual scaling
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
CALIBRATION_METHOD = None  # None = preset default; or 'level_seasonal' / 'zapata_nnls' / 'zapata_ridge_nnls'

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
# These choices apply ONLY to the United States preset (its demand-shape source
# is EFS). They are IGNORED for every non-US country, which uses Zapata/Mendeley
# demand shapes instead.
#
# How to use:
#   * Leave either set to None to use the United States preset's default
#     (EFS_ELECTRIFICATION = 'Reference', EFS_TECHNOLOGY_ADVANCEMENT = 'Moderate').
#   * Set to one of the documented values below to override the preset for this
#     run — no need to edit the preset dict in energy_timeslice_pipeline.py.
#
#   EFS_ELECTRIFICATION choices:        'Reference', 'Moderate', 'High'
#   EFS_TECHNOLOGY_ADVANCEMENT choices: 'Slow', 'Moderate', 'Rapid'
#
# The EFS dataset only contains years 2018, 2020, 2024, 2030, 2040, 2050; any
# other YEAR (Section 1) maps to the nearest available EFS year.
#
# Note: the U.S. heating/cooling split (EIA RECS CE8.2.M / CE8.3.M monthly
# multipliers, applied to residential + commercial space conditioning) is
# applied automatically for U.S. runs. It is a methodology step, not a per-run
# toggle — see README.md -> "U.S. Heating/Cooling Split".
EFS_ELECTRIFICATION = None          # None = United States preset default ('Reference')
EFS_TECHNOLOGY_ADVANCEMENT = None   # None = United States preset default ('Moderate')


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
# Only used by the legacy 2 m-weather wind path (wind_cf_source='weather').
WIND_ROUGHNESS_LENGTH = 0.03

# Number of most-recent available site-years to average for wind CF, for
# presets whose wind_cf_source='ninja_sites' (China, South Korea). This is
# DECOUPLED from LAST_N_YEARS (which governs demand + Ember calibration): the
# ninja per-site archive is a weather climatology and benefits from more years
# regardless of the model target year. The pipeline reduces the selected
# site-years to a day-of-year × hour climatology and maps it onto the run's
# calendar.
#
#   None (recommended) — use the country preset's wind_cf_years (China/KR = 7).
#   <int>              — override for this run (e.g. 3 to use the 3 most recent
#                        available site-years). If fewer years exist on disk,
#                        all available are used and the run reports the shortfall.
#
# Ignored for presets using wind_cf_source='weather' (the 2 m path).
WIND_CF_YEARS = None

# Onshore vs offshore wind (no setting here — data-driven, documented for
# reference). For 'ninja_sites' presets each site is classified onshore or
# offshore from its `type` in scripts/fetch_ninja_sites.py::SITES, and
# SYSHECF-onshore-wind / SYSHECF-offshore-wind get separate capacity-factor
# tables. Net load and clustering use the blended wind_cf, weighted by the
# region's EPS start-year wind capacities from data/eps_wind_capacity_split.csv
# (refresh with scripts/fetch_eps_wind_capacity_split.py when a model's
# start-year capacities change). See CLAUDE.md → "Onshore vs offshore wind are
# separate SYSHECF series" and DECISIONS.md 2026-08-11 / 2026-08-12.

# Capacity factor calibration mode for scaling synthetic solar/wind
# capacity factors so their annual mean matches the value reported by
# Ember.
#
#   None (recommended) — use the country preset's default:
#       United States → 'multiplicative'  (pinned to legacy master-branch
#                       behavior for baseline comparability; note this can
#                       yield CF values > 1.0)
#       all others    → 'cap_redistribute'
#     A non-None value here overrides the preset for this run.
#
#   'speed_rescale' — calibrate WIND in wind-speed space: solve for the
#       scalar k such that mean(power_curve(k × hub-height speed)) equals
#       the Ember target, then recompute the wind CF series from the
#       rescaled speeds. Bounded by the power curve (no hours pinned at
#       1.0), and the shape distortion is physical (calm hours stay near
#       zero; the ramp region stretches through the cubic power curve)
#       rather than a linear stretch. Directly compensates the two
#       dominant low-biases of area-averaged national wind speeds
#       (site-selection bias + power-curve-of-the-mean). Solar falls back
#       to cap_redistribute under this mode. Recommended when the implied
#       wind multiplier is large; see HANDOFF.md → "Weather Data
#       Improvements".
#
#   'cap_redistribute' — multiply, clip values >1
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
#
# NOTE: presets with wind_cf_source='ninja_sites' (e.g. China) take their
# wind CF from Renewables.ninja per-site simulation outputs and calibrate
# wind to the Ember target with cap_redistribute REGARDLESS of this setting
# (speed_rescale is inapplicable — there is no wind-speed series for site
# CFs). This setting still governs SOLAR for those presets, and both solar
# and wind for all 'weather'-source presets. See DECISIONS.md 2026-07-10.
CF_CALIBRATION_MODE = None  # None = preset default; or 'speed_rescale' / 'cap_redistribute' / 'multiplicative'


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
# variables: net_load, load, solar_cf, wind_cf — all in native units; load
# is absolute MW, not normalized) under
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


def _print_nrmse_report() -> None:
    """List every NRMSE value from the run's Metrics CSV.

    Reads ``<output_root>_Metrics.csv`` (written by the pipeline) and prints a
    grouped table of all normalized-RMSE values — the demand-calibration fit,
    the solar/wind CF calibration, and the representative-day clustering
    reconstruction. NRMSE is dimensionless (RMSE ÷ the normalization basis
    shown per group: mean_observed or std_observed), so values are comparable
    across series of different magnitudes.

    Skipped quietly if no Metrics CSV exists (e.g. CALIBRATION_ONLY runs, which
    exit before metrics are written).
    """
    import os
    import pandas as pd

    try:
        preset = pipeline.get_country_preset(COUNTRY)
        region_name = preset['output_country']
    except Exception:
        region_name = None

    resolved = pipeline.resolve_output_path(OUTPUT_PATH, country=region_name)
    if not resolved:
        return
    root, _ = os.path.splitext(resolved)
    metrics_path = f'{root}_Metrics.csv'
    if not os.path.exists(metrics_path):
        print(f"[NRMSE] no metrics file at {metrics_path} — nothing to list.")
        return

    df = pd.read_csv(metrics_path)
    if 'nrmse' not in df.columns:
        return
    df = df[df['nrmse'].notna()].copy()
    if df.empty:
        print("[NRMSE] metrics file has no NRMSE values.")
        return

    country = df['country'].iloc[0] if 'country' in df.columns else region_name
    year = df['year'].iloc[0] if 'year' in df.columns else ''
    basis_labels = {
        'mean_observed': 'normalized by mean of observed series',
        'std_observed': 'normalized by std of observed series',
    }

    print()
    print('=' * 72)
    print(f"NRMSE summary — {country} {year}".rstrip())
    print("(NRMSE = RMSE ÷ normalization basis; dimensionless, lower is better)")
    print('=' * 72)

    # Longest "series / stage" label for column alignment.
    df['label'] = df['series'].astype(str) + ' / ' + df['stage'].astype(str)
    width = min(max(df['label'].str.len().max(), 12), 64)

    for group in df['metric_group'].drop_duplicates():
        sub = df[df['metric_group'] == group]
        bases = sub['normalization_basis'].dropna().unique() \
            if 'normalization_basis' in sub.columns else []
        basis_txt = ', '.join(basis_labels.get(b, str(b)) for b in bases)
        header = f"\n{group}"
        if basis_txt:
            header += f"  [{basis_txt}]"
        print(header)
        for _, r in sub.iterrows():
            print(f"  {r['label']:<{width}}  {r['nrmse']:>12.4f}")
    print('=' * 72)


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
        'demand_series_csv': DEMAND_SERIES_CSV,
        'seasonal_calibration': SEASONAL_CALIBRATION,
        'scenario': SCENARIO,
        # Forwarded via **kwargs to generate_full_pipeline_for_country:
        'weight': WEATHER_WEIGHT,
        'dataset': WEATHER_DATASET,
        'orientation_factor': SOLAR_ORIENTATION_FACTOR,
        'roughness_length': WIND_ROUGHNESS_LENGTH,
        'wind_cf_years': WIND_CF_YEARS,
        'use_cache': USE_CACHE,
        'cache_dir': _effective_cache_dir(),
        'cf_calibration_mode': CF_CALIBRATION_MODE,
        'make_plots': MAKE_DIAGNOSTIC_PLOTS,
        'compare_pinned_unpinned': COMPARE_PINNED_UNPINNED,
        'calibration_only': CALIBRATION_ONLY,
        'calibration_method': CALIBRATION_METHOD,
        'lambda_ridge': LAMBDA_RIDGE,
        # United States only (ignored for non-US presets). None = preset default.
        'efs_electrification': EFS_ELECTRIFICATION,
        'efs_technology_advancement': EFS_TECHNOLOGY_ADVANCEMENT,
    }
    if DATA_DIR is not None:
        kwargs['data_dir'] = DATA_DIR

    pipeline.generate_full_pipeline_for_preset(**kwargs)

    _print_nrmse_report()

    pipeline._status('done', "run complete", t=_run_start)


if __name__ == '__main__':
    main()
