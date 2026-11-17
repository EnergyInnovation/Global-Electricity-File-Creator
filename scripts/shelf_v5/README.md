# Building the US SHELF workbook for EPS 5.0

`scripts/build_shelf_workbook.py --version 5.0` builds the workbook that eps-us `develop` reads
(`InputData/elec/SHELF/Seasonal Hourly Equipment Load Factors by End Use.xlsx`), and
`scripts/shelf_v5/recalc_export.py` exports its CSVs. Without `--version`, the script builds the 4.0.x
workbook as before.

All values are inputs for staff review. Check them against the primary sources named on the workbook's
About tab before using them in any work product.

## Regenerate the develop workbook from a clone

Needs Windows with Excel, Python 3.11+, and `pip install numpy pandas openpyxl pywin32`.
Nothing has to be downloaded: every hourly source has a saved national series in the repository.

```bash
python scripts/build_shelf_workbook.py --version 5.0
```

```bash
python scripts/shelf_v5/recalc_export.py output/us_shelf_5.0 --version 5.0
```

```bash
python scripts/shelf_v5/verify_v5.py output/us_shelf_5.0
```

1. **Build** writes the workbook (formulas, no values yet) and the `ICwIwLF` workbook and CSV under
   `output/us_shelf_5.0/`, laid out like an eps-us `InputData` folder (`elec/SHELF/`,
   `ctrl-settings/ICwIwLF/`). It prints which inputs came from saved series and which from raw files.
2. **Recalculate and export** opens the workbook in Excel, recalculates, stops if any formula returns an
   error, and writes the 36 `SHELF-*.csv` files beside it.
3. **Check** recomputes the exported numbers in Python from the raw inputs and confirms every shape adds
   up to 1 over the year.

To compare with eps-us, or to write straight into a checkout:

```bash
python scripts/shelf_v5/compare_csvs.py output/us_shelf_5.0 <eps-us>/InputData
```

```bash
python scripts/shelf_v5/compare_workbooks.py "output/us_shelf_5.0/elec/SHELF/Seasonal Hourly Equipment Load Factors by End Use.xlsx" "<eps-us>/InputData/elec/SHELF/Seasonal Hourly Equipment Load Factors by End Use.xlsx"
```

```bash
python scripts/build_shelf_workbook.py --version 5.0 --out <eps-us>/InputData
```

## What 5.0 adds to the 4.0.x workbook

| Addition | Where it is built |
|---|---|
| Timeslices named `Representative Day 1`-`4`, `Net Peak Summer Day`, `Net Peak Winter Day` | `names.py` |
| Data centers as two tabs, `SHELF-datacenters-cooling` and `SHELF-datacenters-other` | `build5.py` |
| District heat / hydrogen and geoengineering on the Cambium total end-use load shape, not zeros | `process_blend.py` |
| Per-process industry tabs `SHELF-indstproc-<timeslice>` and `SHELF-indstCCS`, with the `Industry slice weights` and `Industry blend` tabs | `process_blend.py` |
| Whole-industry shapes for 25 industries, `SHELF-indstcat-<timeslice>`, with the `Industry metered source`, `Industry day shapes`, `Industry hourly build` and `Industry weekend evidence` tabs | `industry.py`, `siels.py` |
| `ctrl-settings/ICwIwLF` (the list of industries on a whole-industry shape) | `icwiwlf.py` |
| About tab text for all of the above | `about_text.py` |

The method for the industry shapes is described on the workbook's About tab and at the top of
`industry.py`.

## Inputs, and what is needed to refresh each one

The build reads a saved copy when there is one, and the raw download only when the saved copy is
missing or `--refresh <name>` is given. Locations of raw downloads are set with a command-line option,
an environment variable or `local_paths.yml` (copy `local_paths.example.yml`); see `paths.py`.

| Input | Saved copy in the repository | Raw download | To refresh |
|---|---|---|---|
| ResStock, by state | `data/national_aggregated/resstock_national_hourly.csv` | NREL End-Use Load Profiles, state folders `state=XX` | `--resstock-root <folder> --refresh resstock` |
| ComStock, by state | `data/national_aggregated/comstock_national_hourly.csv` | NREL End-Use Load Profiles, state folders `XX` | `--comstock-root <folder> --refresh comstock` |
| Electrification Futures Study | `data/national_aggregated/efs_national_hourly.csv` | `EFSLoadProfile_Reference_Moderate.zip` (data.nrel.gov/submissions/126); needs `pip install zipfile-deflate64` | `--efs-zip <file> --refresh efs` |
| Industry hourly load (SIELS) | `data/national_aggregated/siels_national_hourly.csv` | `industrial_load_shapes_2018.zip` (data.mendeley.com/datasets/jhghzm9yk5, 27 MB) | `--siels-zip <file> --refresh siels` |
| Clustering | `data/cambium24_midcase_national/k6_slice_assignment_repday.csv` | the Cambium file is in the repository; re-running needs `pip install scikit-learn` | `--clustering rerun` |
| Hand-built industry tabs (`Ag`, `Other Data & Calcs`, `EPRI load shapes`, `NREL load shapes`) | `data/us_industry_handbuilt/handbuilt_tabs.xlsx` | none: pasted data and hand-written formulas | edit the seed workbook, or re-extract it with `extract_seed.py` |

`--clustering auto` (the default) re-runs the clustering when scikit-learn is installed and warns if the
result differs from the saved list; otherwise it uses the saved list.

The saved EFS series, the saved clustering list and the hand-built tabs were taken from the workbook on
eps-us `develop` (commit d2d418df) with `extract_seed.py`. On a machine without the EFS zip and
scikit-learn, a rebuild therefore shows that those three were carried through correctly, not that the raw
data lead to them.

## Two options that change the numbers

Both are off by default, so that the default build reproduces eps-us `develop`.

- `--align-weekdays` moves the ResStock and ComStock days one day later when they are matched to
  timeslices. Those two sources follow a 2018 calendar (the year starts on a Monday); the clustering
  follows weather year 2012 (starts on a Sunday). Matching day number to day number, as the default does,
  puts the buildings' weekends one day early. The state pipeline already makes this correction
  (`state_pipeline/fetchers/cambium.py`). It changes the ten residential and commercial files only.
- `--siels-tennessee central` uses the pipeline's own time-zone table for Tennessee when the SIELS zip is
  aggregated. The files on eps-us `develop` were built with Tennessee on Eastern time, which is the
  default here so that they can be reproduced. The series for this option is saved under its own name
  and does not replace the default one. It changes the six `SHELF-indstcat` files only.

## The 4.0.x workbook

```bash
python scripts/build_shelf_workbook.py
```

```bash
python scripts/shelf_v5/recalc_export.py output/us_shelf_4.0 --version 4.0
```

Same tabs and timeslice names as before. The only changes to this path are where inputs are looked up
(no user folder in the code), where the workbook is written (`output/us_shelf_4.0/` unless `--out` is
given), and that the EFS series and the clustering fall back to their saved copies when the EFS zip or
scikit-learn is missing.

## Files in this folder

| File | Purpose |
|---|---|
| `build5.py` | adds the 5.0 tabs to the base workbook and orders the tabs |
| `names.py`, `paths.py` | timeslice names; where inputs are looked up |
| `process_blend.py`, `industry.py`, `siels.py`, `icwiwlf.py`, `about_text.py` | the 5.0 additions |
| `recalc_export.py` | Excel recalculation and CSV export |
| `verify_v5.py` | independent check of an exported folder |
| `compare_csvs.py`, `compare_workbooks.py` | comparison with a reference copy |
| `extract_seed.py` | one-time: take the hand-built tabs, EFS series and clustering list from an existing workbook |
