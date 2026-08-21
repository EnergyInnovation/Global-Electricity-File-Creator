# scripts/ — One-off utility scripts

These are working scripts from past calibration sessions, kept for reference and reproducibility. They are **not** part of the main pipeline (see project root `state_pipeline/`, `rebuild_us_national_v2.py`, `energy_timeslice_pipeline.py`).

Outputs from these scripts (CSVs etc.) go to `scripts/data_outputs/`.

## Files

### Diagnostics / utilities (kept for re-use)

- **`verify_shelf_balance.py`** — verify that each `SHELF-*.csv` in `eps-us/InputData/elec/SHELF/` satisfies `sum(LF × hours_per_slice) = 1.0` for non-zero categories. Useful sanity check after any SHELF rebuild.
- **`populate_datacenters_shelf.py`** — populate `SHELF-datacenters.csv` with a flat 24/7 profile. Superseded by the in-line flat-table block in `state_pipeline/run.py` and `rebuild_us_national_v2.py`, but kept here in case you want to overwrite just the datacenters file without re-running the full pipeline.

### China observed-demand source (added 2026-08-20)

China has two observed hourly demand records and the preset picks between them from the
run configuration — see `CLAUDE.md` §1 "China observed-demand source" and DECISIONS.md
2026-08-20.

- **`build_china_hourly_demand.py`** — converts the Yi et al. 2026 provincial load
  workbook into the national series the pipeline reads. Sums the 31 provinces, converts
  GWh/h → MW, writes `data/manual_downloads/CN_hourly_demand_2015_2024.csv` plus a
  per-year coverage report (hours vs expected, missing cells, annual TWh, mean/peak GW).
  Run it whenever the source workbook is refreshed:
  `python scripts/build_china_hourly_demand.py --source "<path>/Data output.xlsx"`.
  Cite Yi, B. et al. (2026) *Scientific Data* **13**, 978,
  https://doi.org/10.1038/s41597-026-07327-8 (data: figshare
  https://doi.org/10.6084/m9.figshare.29832701, **CC BY-NC-ND 4.0**) in anything derived
  from it.
- **`compare_china_demand_sources.py`** — input-side diagnostic: compares the two
  observed series for 2018, the only year both cover (annual energy, peak level and
  timing, load factor, monthly energy, diurnal shape), and reports the new source's
  coverage by year. No arguments.
- **`test_china_demand_source.py`** — impact test: runs China under several
  source / year / window combinations and diffs the resulting SHELF and SYSHECF tables
  against the current production baseline. Writes
  `output/china_demand_source_test/` (per-variant EPS outputs, per-file diffs, day
  counts, a label-invariant pinned-peak report, all metrics). `--diff-only` re-diffs
  existing runs without re-running the pipeline; `--only <name>` runs one variant.
  Results write-up: `output/china_demand_source_test/RESULTS.md`.

### Calibration scripts (one-off, from past sessions)

- **`calibrate_syshecf_to_eia.py`** — original standalone EIA CF calibration script (scaled VRE SYSHECF to match Table 4.8.B targets). Now integrated into `rebuild_us_national_v2.py` and `state_pipeline/builders/syshecf_builder.py`.
- **`verify_and_reexport.py`** — verify SHELF + SYSHECF + days-per-timeslice consistency after a repo reset. Predates the current rebuild scripts.
- **`parse_eia_cf.py`** — small utility to extract EIA Table 4.8.B annual CFs from the downloaded xlsx file.

### ELCCAfR (capacity-credit) computation

**The supported path is `build_run_workbooks.py`**, which emits the 25 ELCCAfR CSVs and a
self-contained workbook for any region alongside SHELF and SYSHECF (added 2026-08-18; see
DECISIONS.md). ELCCAfR is a second statistic over the same hourly CF column and the same
per-slice day set that produces SYSHECF, so `SYSHECF × ELCCAfR` = the worst-day capacity
factor. No new data source is needed.

The scripts below predate that and are **one-off / reference only**: they hard-code
`C:\Users\RobbieOrvis\...` paths, use their own top-27/top-20 peak-day selection rather than
the pipeline's clustering, and add a paired-battery (hybrid) dispatch step that the supported
path deliberately does not model.

- **`fetch_renewables_ninja.py`** — fetch multi-year hourly VRE data from renewables.ninja API. Caches to `Downloads/ninja_cache/` (external cross-session cache, not in repo).
- **`compute_hybrid_elccafr.py`** — single-year hybrid (solar/wind + battery) ELCC-for-reliability computation.
- **`compute_hybrid_elccafr_multiyear.py`** — multi-year version using local MERRA-2 weather data.
- **`analyze_multi_year_hybrid_elccafr.py`** — analysis on multi-year renewables.ninja cached data.

### Cambium 2024 K6 exploration

- **`cluster_cambium24_k6.py`** — early exploration script for K6 clustering on Cambium 2024 national hourly. Superseded by `rebuild_us_national_v2.py`. Kept for reference.

## Workflow rule

**All project files belong in the project folder.** Output data files go to `scripts/data_outputs/` (or to the appropriate destination dir in the main pipeline). External caches (e.g., `Downloads/ninja_cache/`) for shared cross-session data are OK to leave outside the project.
