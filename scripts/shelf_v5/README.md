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
| ResStock and ComStock, actual 2012 weather (`--buildings amy2012`) | `data/national_aggregated/{resstock,comstock}_amy2012_national_hourly*.csv`, one file per clock (and per `--television` setting); created on the first build | ResStock 2025 R1 `resstock_amy2012_release_1` and ComStock 2025 R2 `comstock_amy2012_release_2`, baseline (upgrade 0) by-state files from NREL's OEDI data lake; folders `state=XX` and `XX` | set `resstock_amy2012_root` / `comstock_amy2012_root` (`local_paths.yml`, `SHELF_RESSTOCK_AMY2012_ROOT`, `SHELF_COMSTOCK_AMY2012_ROOT`), then `--buildings amy2012 --refresh resstock --refresh comstock` |
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

## Options that change the numbers

The defaults reproduce eps-us `develop`. Since 2026-11-18 (eps-us 8c4a3701) that means home and business shapes
from NREL's actual-2012-weather runs, on the Eastern clock, with television counted; the first three options
below are those defaults for `--version 5.0` (with `--version 4.0` they fall back to the typical-year source and
the old clock, which reproduces the 4.0.x files). `--efs-clock eastern` is also a 5.0 default (see below).

- `--align-weekdays` moves the ResStock and ComStock days one day later when they are matched to
  timeslices. Those two sources follow a 2018 calendar (the year starts on a Monday); the clustering
  follows weather year 2012 (starts on a Sunday). Matching day number to day number, as the default does,
  puts the buildings' weekends one day early. The state pipeline already makes this correction
  (`state_pipeline/fetchers/cambium.py`). It changes the ten residential and commercial files only.
- `--buildings amy2012` (5.0 default) builds the home and business shapes from NREL's runs with the actual weather
  of 2012 (ResStock 2025 R1, ComStock 2025 R2). `--buildings typical` uses the typical-year runs (ResStock 2024 R2,
  ComStock 2021 R1) that the files before 2026-11-18 were built from. 2012 is the weather year of the
  Cambium file the clustering uses, so the clustering's hottest, coldest and highest net-load days are days when
  these buildings were simulated under the same weather. The files run 1 January to 30 December 2012 (8,760
  hours, 29 February kept), so day number n is day number n of the Cambium file and `--align-weekdays` does not
  apply (it is an error with this source). End uses are matched by name pattern, so the `.kwh` / `..kwh` column
  suffixes of the two releases both work; the build prints end uses the category maps do not cover. Of these,
  television (new as its own line in ResStock 2025 R1, formerly inside plug loads) is the only one of size
  (about 87 TWh, 5.6% of home electricity, mostly evening). It is added to `residential-other` by default with
  this source; `--television omit` leaves it out (the first reference sets did). ComStock's Hawaii weather
  files are flagged by NREL as incorrect; Hawaii is kept (about 0.5% of national commercial load).
- `--building-clock eastern` (5.0 default) adds the ResStock and ComStock states without moving each by its
  time-zone offset. NREL's state files are stamped in Eastern Standard Time already (checked against the sun,
  NOAA 2012 temperatures and NREL's documentation), so `--building-clock pipeline`, what the pipeline did before,
  shifts every state outside the Eastern zone a second time (by 0.8 h for home load and 1.0 h for business load,
  on a load-weighted average). It does not touch the SIELS industry shapes, whose local-time stamps the pipeline
  moves to Eastern correctly.
- `--building-delay-hours H` (default 0, off) delays every ResStock and ComStock hourly series by H hours after
  the states are added, as a blend of the series moved later by the whole hours and by one more (for 0.5 h, half of
  each hour's load plus half of the previous hour's; the year wraps). Annual energy is unchanged exactly. It is a
  calibration to measured demand, not a clock correction: the SHELF clock analysis (2026-11-17) found NREL's
  modelled day runs about half an hour early once television is counted. It is off in the files on `develop`:
  the shapes fix conversion errors only and keep NREL's modelled timing as published. It is applied to whichever
  source and clock are chosen.
- `--efs-clock eastern` (5.0 default) moves the EFS series (vehicle charging, rail) onto Eastern Standard Time.
  The EFS file gives each state by `LocalHourID`, its own local hour, and the reader adds the states hour by
  hour, so `--efs-clock local` (what the pipeline did before) puts western charging up to 3 hours early against
  every other source. The correction needs no raw data: the national series is moved later by 0, 1, 2 and 3
  hours with weights equal to the contiguous-US population share in the Eastern, Central, Mountain and Pacific
  zones (0.476, 0.294, 0.068, 0.163; `shelf_v5/efs_clock.py`). That is exact if every state's profile has the
  same shape in local time and an approximation otherwise. The saved EFS series shows no step at the 2012
  daylight-saving changes, so no daylight-saving correction is made. It changes `SHELF-LDVs`, `SHELF-HDVs` and
  `SHELF-rail` only.
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
| `names.py`, `paths.py`, `buildings.py` | timeslice names; where inputs are looked up; which buildings release and clock |
| `process_blend.py`, `industry.py`, `siels.py`, `icwiwlf.py`, `about_text.py` | the 5.0 additions |
| `recalc_export.py` | Excel recalculation and CSV export |
| `verify_v5.py` | independent check of an exported folder |
| `compare_csvs.py`, `compare_workbooks.py` | comparison with a reference copy |
| `extract_seed.py` | one-time: take the hand-built tabs, EFS series and clustering list from an existing workbook |
