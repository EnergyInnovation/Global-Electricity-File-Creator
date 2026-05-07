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

## Weather Data Improvements

> **Treat this entire section as a starting point for review.** Citations and physical assumptions below have not been independently verified for any country. Verify against primary sources (KIER/KEPCO/KESIS for Korea, ENTSO-E for EU presets, EIA for U.S., etc.) before treating any derived capacity factor as a final modeled value. Coordinate with **IT & Systems (itsystems@energyinnovation.org)** before any external publication.

### Problem summary

The South Korea EPS run produces `SYSHECF-onshore-wind` capacity factors above 1.0 (peak winter values up to ~1.68). A capacity factor cannot exceed 1.0 by definition (would mean a turbine generating above nameplate). Same risk applies to solar and to any country whose synthetic-vs-Ember mismatch is large. This is the highest-priority weather-data issue.

The bug surfaces in the calibration step. Symptom is that the synthetic annual mean is much lower than Ember's reported annual mean for the country (Korea: ~10.2% synthetic vs ~18% Ember), so the multiplicative scaler `target_mean / synthetic_mean` ≈ 1.76 pushes the windiest hours past 1.0.

### Why the synthetic mean is too low (ranked for Korea)

Korea is ~99% onshore wind as of 2024, so the offshore-vs-onshore composition gap is **not** the dominant driver for KR. Likely contributors, ranked by impact:

1. **Site-selection bias (largest).** Renewables.ninja country files use **area weighting** — averaging wind speed across the entire national land area. Real wind farms are sited at the windiest locations (Korean southwest coast, Gangwon ridges, Jeju). Cubic power-curve sensitivity means a 25–30% wind-speed shortfall yields a 50%+ CF shortfall. Not fixable by tuning calibration constants — needs either a site-resolved aggregate or a fleet-weighted weather product.
2. **Roughness length and hub height (significant).** Both are global hardcoded defaults (see "Where the wind physics constants come from" below). Neither is tuned for Korean fleet vintage or terrain.
3. **Power-curve assumptions (moderate).** `cut_in=3, rated=12, cut_out=25 m/s` are Pfenninger/Staffell VWF generics circa 2016. Modern Korean turbines (most installed post-2018) reach rated output around 10–11 m/s.
4. **Onshore/offshore composition (small for Korea, large for UK/DE).** Negligible for Korea today (~99% onshore). Will be the dominant factor for UK, Germany, Denmark, Netherlands when those presets are verified.
5. **MERRA-2 reanalysis bias and other small effects.** Known to underpredict coastal wind speeds by ~5–10%. Also wake losses, curtailment, and mid-year-commissioning artifacts pull in mixed directions.

### Where the wind physics constants come from

All from **Staffell & Pfenninger's Virtual Wind Farm (VWF) model** (2016) — the academic foundation for renewables.ninja itself. They are textbook generic reference values, never country-tuned in this codebase.

| Parameter | Default | VWF/textbook meaning |
|---|---|---|
| `roughness_length` | 0.03 m | "open farmland" |
| `hub_height` | 100 m | utility-scale circa 2016 |
| `cut_in` | 3.0 m/s | turbine starts producing |
| `rated` | 12.0 m/s | turbine reaches nameplate |
| `cut_out` | 25.0 m/s | turbine shuts down for safety |
| `ref_height` | 2 m | renewables.ninja file is at 2 m above ground |

Source: docstring at [`compute_wind_capacity_factor_from_weather`](energy_timeslice_pipeline.py:711-722) cites Staffell & Pfenninger. Verify against the original paper before relying.

### What's currently controllable vs hardcoded

| Where | `roughness_length` | `hub_height` | Power curve |
|---|---|---|---|
| `run_pipeline.py` setting | exposed as `WIND_ROUGHNESS_LENGTH` | **not exposed** | **not exposed** |
| Country preset | not present | not present | not present |
| `generate_full_pipeline_for_country` | yes | **not threaded through** | **not threaded through** |
| Helper-level default | 0.03 | 100 | as above |

Only `roughness_length` is reachable from the runner. The others require editing the helper functions directly.

### Known bug: `ref_height` inconsistency

The renewables.ninja country wind-speed file is at **2 m** above ground (file header confirms "*wind speed at 2 metres above ground in m/s (U2M and V2M in MERRA-2)*"). The wrapper `compute_capacity_factors_from_weather` correctly defaults to `ref_height = 2.0`, but the inner helper `compute_wind_capacity_factor_from_weather` defaults to `ref_height = 10.0` and its docstring documents the data as "measured at e.g. 10 m". Library users who call the inner function directly will get a wrong answer (synthetic CF off by ~2.6× from the right value). Live pipeline path is unaffected because the wrapper overrides. Worth fixing for safety; ~15-line change with no production-output impact.

### Calibration approach options for the > 1.0 issue

1. **Cap-and-redistribute (recommended near-term fix).** Multiply by `target_mean / synthetic_mean`, clip values > 1.0, redistribute the excess to unsaturated hours, iterate until annual mean matches and no value exceeds 1.0. Drop-in change to `calibrate_capacity_factors`. Bounded by construction. Easy to test, easy to roll back. Symptom-fixing, not root-cause-fixing.
2. **Quantile (CDF) mapping.** Map the synthetic CF distribution onto a target CDF (e.g., Beta) parameterized by Ember's mean. Rank-preserving and bounded. More rigorous than #1 but requires assuming a target distribution shape; deserves its own methodology discussion.
3. **Logit-space affine calibration.** Bounded by construction via sigmoid transform. Numerically delicate near 0 and 1; non-obvious shape distortion at the extremes.
4. **Fix the underlying physics.** Tune `roughness_length`, `hub_height`, and the power curve per-preset so the synthetic mean is already close to the Ember target. Multiplier becomes ~1.0, no clipping needed. Best long-term answer; requires deeper modeling work and per-country research.

### Recommended order of operations

1. **Immediate:** implement option 1 (cap-and-redistribute) so all currently-shipped CF values are at least bounded. Add diagnostics — post-cal max CF, fraction of hours pinned to 1.0, calibration multiplier — to `*_Metrics.csv`. Emit a warning when the multiplier exceeds, say, 1.5.
2. **Short-term:** fix the `ref_height` inconsistency in the inner helper. Plumb `hub_height` and the power-curve parameters through `for_country` and `run_pipeline.py`. Add per-country preset overrides for these parameters where Korea-vintage / Korea-terrain values are meaningfully different from the VWF defaults.
3. **Medium-term:** investigate whether renewables.ninja exposes a current-fleet-weighted wind product (instead of area-weighted). If yes, switch the country files for high-stakes presets to the fleet-weighted version. Largest single improvement available short of building a site-resolved model.
4. **Long-term:** site-resolved CF aggregation for high-stakes countries. Compute hourly CF at each turbine site (using site-specific weather and turbine specs), then aggregate over the actual fleet.

### Verification needed before publishing any wind/solar SYSHECF

- **The Ember target value itself.** The Korean implied wind CF varies from 22% (2020) to 17% (2024) in Ember; the downward trend is suspicious and may be partly a denominator artifact (mid-year commissioning). Cross-check against KEPCO/KIER fleet-aggregate CFs.
- **The implicit fleet vintage and terrain assumed by the synthetic model.** VWF defaults reflect 2016 utility-scale onshore on flat farmland, which is not what Korea's fleet looks like.
- **The on/offshore split for European/coastal presets.** UK, Germany, Denmark, Netherlands, and similar will need separate onshore and offshore handling before their outputs are trustworthy.
- **The pinned-vs-unpinned NRMSE trade-off** is country-dependent. Korea's pinned NRMSE is 0.142 vs unpinned 0.763 (pinned wins decisively); the U.S. EFS run shows the opposite (pinned 0.389 vs unpinned 0.347). Document per country.
- **Treat all calibrated CF series as a starting point for review, not as EI's institutional position.** A high `fraction_at_cap` value (which option 1 will surface) is a flag that the underlying shape needs upstream work, not just a calibration tweak.

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

1. **Fix wind/solar capacity factor calibration so values stay in [0, 1]** — see the *Weather Data Improvements* section above for the problem, the ranked likely causes, the calibration-method options, and the recommended order of operations. This is currently the highest-priority correctness fix.
2. Improve `SYSHECF` for dispatchable/non-variable technologies so fewer tabs are template-based.
3. Decide whether the U.S. heating/cooling split should become census-region-specific.
4. Revisit the distributed-PV derate if a better rooftop source becomes available.
5. Tune how many days pinned peak slices are allowed to absorb.
6. Continue validating more major-country presets.

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
