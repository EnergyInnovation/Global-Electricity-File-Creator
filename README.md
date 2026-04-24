# Global Electricity File Creator

This project builds country-specific representative-day electricity inputs for EPS-style power-sector modeling.

The main script is:

- `energy_timeslice_pipeline.py`

## Primary Goals

The work in this thread focused on four overlapping goals:

1. Build representative-day electricity inputs for major countries.
2. Preserve investment-relevant reliability conditions, especially summer and winter peak or net-peak days.
3. Export results in the exact EPS-style `SHELF` and `SYSHECF` formats used by the downstream Vensim/EPS model.
4. Keep the workflow reproducible, automated, and country-driven.

## Current High-Level Workflow

The script now does the following:

1. Resolve a built-in country preset.
2. Choose a demand-shape source:
   - `United States` -> `EFS`
   - non-U.S. countries -> `Zapata/Mendeley`
3. Fetch real-world historical demand for calibration using DemandCast or the custom U.S. EIA path.
4. Download weather data and Ember annual data.
5. Build solar and wind hourly capacity factors and calibrate them to observed annual values.
6. Compute net load.
7. Cluster days into 6 representative timeslices.
8. Keep summer and winter peak days pinned.
9. Export generic outputs plus EPS-ready `SHELF` and `SYSHECF` files.
10. Report calibration and clustering RMSE/NRMSE metrics.

## Country Presets

The script has a built-in preset registry in `energy_timeslice_pipeline.py`.

Verified countries in this thread:

- `South Korea`
- `China`
- `United States`

Mapped but not fully revalidated in this thread:

- `Australia`
- `Brazil`
- `Canada`
- `France`
- `Germany`
- `India`
- `Japan`
- `Mexico`
- `United Kingdom`

## Demand-Shape Source Logic

### Non-U.S.

Non-U.S. countries use the Zapata/Mendeley end-use dataset:

- Mendeley dataset URL:
  - `https://data.mendeley.com/public-api/zip/pmd2dchk44/download/1`

This source is used to build hourly end-use load shapes by sector and service/end use.

### United States

The U.S. now uses NREL Electrification Futures Study load-shape data:

- OpenEI source:
  - `https://data.openei.org/submissions/8199`
- Archive used:
  - `EFSLoadProfile_Reference_Moderate.zip`

Scenario choice:

- Electrification: `Reference`
- Technology advancement: `Moderate`

Available EFS years confirmed in the archive:

- `2018`
- `2020`
- `2024`
- `2030`
- `2040`
- `2050`

Current rule:

- if the requested U.S. year is not directly available, use the nearest EFS year
- example: a `2025` request maps to `2024`

### U.S. Heating/Cooling Split

EFS combines residential and commercial space conditioning, so heating and cooling must be split before export.

The current split method is:

- use EIA RECS monthly tables `CE8.2.M` and `CE8.3.M`
- derive monthly heating vs cooling multipliers from those tables
- apply the same monthly multipliers to commercial space conditioning

The RECS tables were read from:

- `C:\Users\RobbieOrvis\Models\EPS Structure Testing\InputData\elec\SHELF\Seasonal Hourly Equipment Load Factors by End Use.xlsx`
- tabs:
  - `RECS CE8.2.M`
  - `RECS CE8.3.M`

This is a monthly split, not yet submonthly or region-specific.

## Historical Demand Calibration

The script calibrates synthetic demand to real-world demand in two stages:

1. Simple level scaling to match observed average demand.
2. Seasonal calibration to better match observed monthly means and seasonal peaks.

This is stronger than the original annual-only scaling, but it is still not a full econometric weather-demand model.

## Capacity Factors

The script computes weather-based:

- `solar_cf`
- `wind_cf`

and calibrates them to observed annual values using Ember.

These calibrated renewable capacity factors are what feed `SYSHECF`.

## Clustering and Reliability Logic

The representative-day clustering is day-based, not hour-based.

Important current choices:

- exactly `6` timeslices
- `24` hours per representative day
- `Summer Peak` and `Winter Peak` are pinned

The clustering objective is now aligned with the earlier U.S.-only script:

- reconstruct the full hourly year from representative days
- evaluate `net_load` RMSE
- use normalized RMSE based on `std(original net_load)`

### Pinned-Day Improvement

Originally, pinned peak days only represented themselves.

This thread added a statistical reassignment step:

- keep pinned summer and winter peak days fixed as representative days
- test assigning additional same-season days into those pinned slices
- only accept a reassignment if it improves full-year net-load reconstruction NRMSE

This improved the pinned U.S. EFS case.

Recent U.S. result:

- pinned `year net-load NRMSE`: `0.3891`
- unpinned `year net-load NRMSE`: `0.3473`

So pinned still performs worse than unpinned on annual reconstruction, but materially better than before, while preserving reliability-relevant peak slices.

## Metrics

Metrics are written both to the terminal and to CSV.

Key metrics include:

- demand RMSE by stage:
  - raw
  - scaled
  - seasonally calibrated
- monthly mean RMSE
- monthly peak RMSE
- clustering reconstruction RMSE/NRMSE
- pinned vs unpinned net-load NRMSE comparison

Files:

- per-run:
  - `<run>_Metrics.csv`
- global summary:
  - `output/timeslice_run_metrics_summary.csv`

## Generic Outputs

The generic output set includes:

- `*_SYSHECF.csv`
- `*_SHELF.csv`
- `*_TimesliceInfo.csv`
- `*_TimesliceMap.csv`
- `*_Metrics.csv`

These are written under:

- `output/`

## EPS Export Work

The script now exports EPS-ready inputs in the exact family/file structure expected by the downstream model.

### SHELF

It writes:

- one CSV per end-use category
- fixed rows:
  - `Winter`
  - `Spring`
  - `Summer`
  - `Fall`
  - `Summer Peak`
  - `Winter Peak`
- columns:
  - `Hour0` ... `Hour23`

It also writes:

- `SHELF-days-per-timeslice.csv`

### SYSHECF

It writes:

- one CSV per technology
- same 6 row labels
- same 24 hourly columns

### EPS Workbooks

The script also writes two `.xlsx` workbooks:

- `Seasonal Hourly Equipment Load Factors by End Use.xlsx`
- `Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx`

Each workbook now includes:

- `About`
- all target EPS tabs
- `Coverage`
- `TimesliceInfo`
- `EPS_Label_Map`

### About Sheets

The `About` tabs were updated to explain the methodology used for each workbook.

For the U.S. `SHELF` workbook, the `About` sheet now explicitly states:

- EFS is the U.S. load-shape source
- RECS monthly multipliers are used to split heating/cooling
- demand is calibrated to observed data
- peak days are pinned

## EPS Mapping Rules Added

The EPS export mapping is now tighter than it was originally.

### SHELF mappings

Generated directly or derived:

- residential heating
- residential cooling
- residential lighting
- residential appliances
- residential other
- commercial heating
- commercial cooling
- commercial lighting
- commercial appliances
- commercial other
- `LDVs`
- `HDVs`
- `aircraft`
- `rail`
- `ships`
- `motorbikes`
- `industry`
- `district-heat-hydrogen`
- `geoeng`
- `datacenters`

Special rules:

- `datacenters`:
  - uniform annual load
  - every hour = `1/8760`
- `district-heat-hydrogen`:
  - follows industry
- `geoeng`:
  - follows industry
- residential/commercial envelope:
  - explicit zero tables

### SYSHECF mappings

Generated directly:

- `onshore-wind`
- `offshore-wind`
- `solar-pv`
- `solar-pv-dist`

Current distributed solar rule:

- `solar-pv-dist = solar_cf * 0.70`

This is an inferred rooftop-vs-utility derate chosen as a practical default, not a final region-specific rooftop model.

Many non-variable technologies in `SYSHECF` are still template-based rather than fully derived.

## Coverage Status

### SHELF

At this point, all `SHELF` files are generated.

The only intentionally zero categories are:

- `SHELF-residential-envelope`
- `SHELF-commercial-envelope`

### SYSHECF

Only a subset are currently generated from modeled data:

- wind-related tabs
- solar-related tabs

Most other `SYSHECF` tabs still copy the EPS template values.

## Data/Environment Work Done

### Installed or added

- Mendeley runtime download support
- DemandCast local bootstrap
- EIA API support for U.S. demand retrieval
- `openpyxl`
- `xlsxwriter`
- `zipfile-deflate64` for reading the EFS Deflate64 archive

### Local files used

- `.env` contains the EIA API key used in this thread
- project output goes to:
  - `output/`

## Important Output Examples

Representative recent output folders/files:

- `output/SouthKorea_timeslice_results_EPS/`
- `output/UnitedStates_EFS_test_EPS/`
- `output/UnitedStates_EFS_test.xlsx`
- `output/UnitedStates_EFS_test_Metrics.csv`

## Key Modeling Assumptions to Know

1. Representative days are a compression of the full year, not a full chronological production-cost model.
2. Pinned peak days are retained because the modeling goal is investment realism, not just average-year fit.
3. Non-U.S. load shapes still rely on Zapata/Mendeley.
4. U.S. load shapes now rely on EFS, but heating/cooling are split with national RECS monthly multipliers.
5. Distributed solar is still a simplified rooftop derate, not a dedicated rooftop solar model.
6. Many dispatchable/non-variable `SYSHECF` technologies are still template-based.

## What Another Thread Should Likely Do Next

Good next tasks:

1. Improve `SYSHECF` derivations for non-variable technologies instead of relying on templates.
2. Consider a better rooftop/distributed PV treatment than the current flat `0.70` derate.
3. Decide whether U.S. heating/cooling should use more granular regional or submonthly RECS-style splits.
4. Tune or constrain how many days pinned peak slices can absorb.
5. Continue hardening country presets for more major countries.
6. If needed, connect the EPS/Vensim-side model updates in a separate repository/thread.

## Short Summary

This repository now has:

- country presets
- automated downloads
- U.S.-specific EFS demand shapes
- non-U.S. Zapata/Mendeley demand shapes
- observed-demand calibration
- observed renewable calibration
- representative-day clustering with pinned peak logic
- RMSE/NRMSE reporting
- EPS-ready CSV and workbook exports
- methodology and coverage documentation embedded in the workbooks

This README is intended as a handoff document for a follow-up thread.
