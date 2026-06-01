# scripts/ — One-off utility scripts

These are working scripts from past calibration sessions, kept for reference and reproducibility. They are **not** part of the main pipeline (see project root `state_pipeline/`, `rebuild_us_national_v2.py`, `energy_timeslice_pipeline.py`).

Outputs from these scripts (CSVs etc.) go to `scripts/data_outputs/`.

## Files

### Diagnostics / utilities (kept for re-use)

- **`verify_shelf_balance.py`** — verify that each `SHELF-*.csv` in `eps-us/InputData/elec/SHELF/` satisfies `sum(LF × hours_per_slice) = 1.0` for non-zero categories. Useful sanity check after any SHELF rebuild.
- **`populate_datacenters_shelf.py`** — populate `SHELF-datacenters.csv` with a flat 24/7 profile. Superseded by the in-line flat-table block in `state_pipeline/run.py` and `rebuild_us_national_v2.py`, but kept here in case you want to overwrite just the datacenters file without re-running the full pipeline.

### Calibration scripts (one-off, from past sessions)

- **`calibrate_syshecf_to_eia.py`** — original standalone EIA CF calibration script (scaled VRE SYSHECF to match Table 4.8.B targets). Now integrated into `rebuild_us_national_v2.py` and `state_pipeline/builders/syshecf_builder.py`.
- **`verify_and_reexport.py`** — verify SHELF + SYSHECF + days-per-timeslice consistency after a repo reset. Predates the current rebuild scripts.
- **`parse_eia_cf.py`** — small utility to extract EIA Table 4.8.B annual CFs from the downloaded xlsx file.

### Hybrid ELCCAfR (capacity-credit) computation

- **`fetch_renewables_ninja.py`** — fetch multi-year hourly VRE data from renewables.ninja API. Caches to `Downloads/ninja_cache/` (external cross-session cache, not in repo).
- **`compute_hybrid_elccafr.py`** — single-year hybrid (solar/wind + battery) ELCC-for-reliability computation.
- **`compute_hybrid_elccafr_multiyear.py`** — multi-year version using local MERRA-2 weather data.
- **`analyze_multi_year_hybrid_elccafr.py`** — analysis on multi-year renewables.ninja cached data.

### Cambium 2024 K6 exploration

- **`cluster_cambium24_k6.py`** — early exploration script for K6 clustering on Cambium 2024 national hourly. Superseded by `rebuild_us_national_v2.py`. Kept for reference.

## Workflow rule

**All project files belong in the project folder.** Output data files go to `scripts/data_outputs/` (or to the appropriate destination dir in the main pipeline). External caches (e.g., `Downloads/ninja_cache/`) for shared cross-session data are OK to leave outside the project.
