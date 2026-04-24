# Handoff

This is a short handoff for a follow-up thread.

## Main File

- `energy_timeslice_pipeline.py`

## Main Objective

Build country-specific representative-day electricity inputs for EPS-style modeling that:

- preserve investment-relevant peak conditions
- still do a reasonable job representing the annual net-load shape
- export directly into EPS-style `SHELF` and `SYSHECF` CSV/workbook formats

## Current Demand-Shape Source Rules

### United States

Use EFS:

- source: `https://data.openei.org/submissions/8199`
- scenario:
  - `Reference` electrification
  - `Moderate` technology advancement

Current behavior:

- if the requested year is not in EFS, use the nearest available EFS year
- example:
  - requested `2025`
  - uses EFS `2024`

### Non-U.S.

Use Zapata/Mendeley:

- `https://data.mendeley.com/public-api/zip/pmd2dchk44/download/1`

## U.S. Heating/Cooling Split

EFS combines residential and commercial space conditioning, so the script splits it into heating and cooling.

Current method:

- use RECS monthly tables:
  - `RECS CE8.2.M`
  - `RECS CE8.3.M`
- source workbook:
  - `C:\Users\RobbieOrvis\Models\EPS Structure Testing\InputData\elec\SHELF\Seasonal Hourly Equipment Load Factors by End Use.xlsx`
- apply the same monthly heating/cooling split to commercial

This is currently:

- national
- monthly
- not yet regional or submonthly

## Clustering Logic

The model uses:

- 6 representative days
- 24 hours per representative day
- pinned `Summer Peak`
- pinned `Winter Peak`

Important recent improvement:

- pinned peak days are fixed
- additional same-season days can be reassigned into pinned peak slices
- only if that improves full-year net-load reconstruction NRMSE

This improved the pinned U.S. case.

## Key U.S. Metric

Recent U.S. EFS run:

- pinned `year net-load NRMSE = 0.3891`
- unpinned `year net-load NRMSE = 0.3473`

Interpretation:

- pinned still costs some annual-fit quality
- but it is better than the earlier pinned version
- this is likely the right tradeoff for investment-oriented modeling

## EPS Export Status

The script now exports:

- EPS-style CSV families
- EPS-style workbooks

Outputs include:

- `About`
- `Coverage`
- `TimesliceInfo`
- `EPS_Label_Map`

## SHELF Status

All `SHELF` files are now generated.

Special rules:

- `datacenters`:
  - uniform `1/8760`
- `district-heat-hydrogen`:
  - follows industry
- `geoeng`:
  - follows industry
- residential/commercial envelope:
  - explicit zero tables

## SYSHECF Status

Directly generated:

- `onshore-wind`
- `offshore-wind`
- `solar-pv`
- `solar-pv-dist`

Current distributed solar assumption:

- `solar-pv-dist = solar_cf * 0.70`

Still template-based:

- most non-variable technologies in `SYSHECF`

## Workbook About Sheets

The workbook `About` tabs were updated to describe methodology.

For U.S. runs, the `About` sheet now explicitly says:

- EFS is the demand-shape source
- RECS monthly multipliers split heating/cooling
- demand is calibrated to observed load
- peak days are pinned

## Useful Output Paths

Examples:

- `output/UnitedStates_EFS_test.xlsx`
- `output/UnitedStates_EFS_test_EPS/`
- `output/UnitedStates_EFS_test_Metrics.csv`
- `output/SouthKorea_timeslice_results_EPS/`

## Important Packages/Environment Notes

Installed in the project environment during this work:

- `openpyxl`
- `xlsxwriter`
- `zipfile-deflate64`

These matter because:

- Excel workbooks are now written directly
- the EFS archive uses Deflate64 compression

## Good Next Steps

1. Improve `SYSHECF` for dispatchable/non-variable technologies so fewer tabs are template-based.
2. Decide whether the U.S. heating/cooling split should become census-region-specific.
3. Revisit the distributed-PV derate if a better rooftop source becomes available.
4. Tune how many days pinned peak slices are allowed to absorb.
5. Continue validating more major-country presets.

## If Starting a New Thread

Tell the new thread to read:

- `README.md`
- `HANDOFF.md`
- `energy_timeslice_pipeline.py`

and note that:

- U.S. load shapes are EFS-based
- non-U.S. load shapes are Zapata/Mendeley-based
- EPS exports are already wired
- clustering metrics are already implemented
