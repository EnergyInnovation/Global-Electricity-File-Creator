# Validation report - US-DE

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **12.0 TWh**
- Peak hour: **2018-01-20 18:00:00** at **2.4 GW**
- Cluster NRMSE: **0.516**

## Days per timeslice

- Winter: 50
- Spring: 66
- Summer: 89
- Fall: 132
- Summer Peak: 25
- Winter Peak: 3

## Top-5 peak days

- Summer Peak: [152, 172, 178, 180, 192, 194, 197, 198, 199, 200, 201, 202, 206, 207, 215, 220, 221, 222, 228, 229, 234, 239, 240, 241, 242]
- Winter Peak: [20, 21, 359]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 991912.95 | 991912.95 | 0.0 | 0.0 |
| residential-cooling | 524257.91 | 524257.91 | 0.0 | 0.0 |
| residential-lighting | 247650.06 | 247650.06 | -0.0 | -0.0 |
| residential-appliances | 1524376.91 | 1524376.91 | 0.0 | 0.0 |
| residential-other | 2133584.41 | 2133584.41 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 112421.16 | 112421.16 | 0.0 | 0.0 |
| commercial-cooling | 907757.91 | 907757.91 | 0.0 | 0.0 |
| commercial-lighting | 484443.14 | 484443.14 | 0.0 | 0.0 |
| commercial-appliances | 896626.61 | 896626.61 | 0.0 | 0.0 |
| commercial-other | 1990756.15 | 1990756.15 | -0.0 | -0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 24583.49 | 24583.49 | -0.0 | -0.0 |
| HDVs | 235.08 | 235.08 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 2153698.32 | 2153698.32 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.069439 | 88.45 | 8760 |
| Winter | 0.099772 | 99.9 | 1200 |
| Spring | 0.110261 | 98.78 | 1584 |
| Summer | 0.116857 | 89.89 | 2136 |
| Fall | 0.096282 | 85.57 | 3168 |
| Summer Peak | 0.05275 | 46.56 | 600 |
| Winter Peak | 0.111553 | 102.96 | 72 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.080859 | 51.43 | 991912.95 |
| residential-cooling | 0.13069 | 31.45 | 524257.91 |
| residential-lighting | 0.05869 | 2.87 | 247650.06 |
| residential-appliances | 0.08078 | 16.0 | 1524376.91 |
| residential-other | 0.089277 | 9.85 | 2133584.41 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.067722 | 5.87 | 112421.16 |
| commercial-cooling | 0.093512 | 19.52 | 907757.91 |
| commercial-lighting | 0.163104 | 7.37 | 484443.14 |
| commercial-appliances | 0.081196 | 10.18 | 896626.61 |
| commercial-other | 0.201335 | 18.28 | 1990756.15 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.065943 | 0.47 | 24583.49 |
| HDVs | 0.053878 | 0.0 | 235.08 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.193366 | 43.54 | 2153698.32 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 2206.51 | 2243.45 | 0.9835 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 1852.81 | 1867.5 | 0.9921 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 2206.51 | 2267.34 | 0.9732 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 293.02 | 367.12 | 0.7982 |  |
| category_peak_commercial-cooling | 335.49 | 377.56 | 0.8886 |  |
| category_peak_residential-heating | 742.09 | 777.25 | 0.9548 |  |
| category_peak_commercial-heating | 108.04 | 111.31 | 0.9706 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.76 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 2026.19 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 1977.99 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 2107.19 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 2206.51 | 2163.27 | 1.02 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 1802.21 | 1656.02 | 1.0883 |  |
| winter_peak_net_load | 2206.51 | 2206.51 | 1.0 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 105.39 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 66.94 | 438 | top 5% of LDC = top ~438 hours |
| overall | 33.64 | 8760 | full 8760 LDC |

## Section 8: SHELF Balance Check

Sum LF*days across non-peak slices = 1.0 +/- tolerance.

| category | shelf_balance_sum | deviation_from_1 | note |
|---|---|---|---|
| residential-heating | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-cooling | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-lighting | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-appliances | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-other | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| residential-envelope | 0.0 | 0.0 | category has zero annual energy |
| commercial-heating | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-cooling | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-lighting | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-appliances | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-other | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| commercial-envelope | 0.0 | 0.0 | category has zero annual energy |
| LDVs | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| HDVs | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| aircraft | 0.0 | 0.0 | category has zero annual energy |
| rail | 0.0 | 0.0 | category has zero annual energy |
| ships | 0.0 | 0.0 | category has zero annual energy |
| motorbikes | 0.0 | 0.0 | category has zero annual energy |
| industry | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
| district-heat-hydrogen | 0.0 | 0.0 | category has zero annual energy |
| geoeng | 0.0 | 0.0 | category has zero annual energy |
| datacenters | 0.0 | 0.0 | category has zero annual energy |

## Section 9: Weather-Year Alignment Diagnostics

Daily summer correlation; net-load peak under +/-7d, +/-14d shifts.

| metric | value | note |
|---|---|---|
| summer_daily_corr_buildings_vs_solar_cf | -0.0483 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 21 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 2386.31 | shifted gen by -14d; peak hour 2018-01-20 18:00:00 |
| net_load_peak_shift_-7d | 2386.31 | shifted gen by -7d; peak hour 2018-01-20 18:00:00 |
| net_load_peak_shift_0d | 2386.31 | shifted gen by 0d; peak hour 2018-01-20 18:00:00 |
| net_load_peak_shift_7d | 2386.31 | shifted gen by 7d; peak hour 2018-01-20 18:00:00 |
| net_load_peak_shift_14d | 2386.31 | shifted gen by 14d; peak hour 2018-01-20 18:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| DE_total_annual_TWh | 11.99 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| DE_solar_pv_annual_TWh | 1.3557 | 1.3557 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| DE_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 521.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 181.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2401 | 0.2401 | 0.5669 | 0.5669 |
| solar-pv-dist | 0.1636 | 0.1636 | 0.3640 | 0.3640 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.048

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 2386 | 2018-01-20 18:00:00 | 1214 |
| -7 | 2386 | 2018-01-20 18:00:00 | 1214 |
| 0 | 2386 | 2018-01-20 18:00:00 | 1214 |
| 7 | 2386 | 2018-01-20 18:00:00 | 1214 |
| 14 | 2386 | 2018-01-20 18:00:00 | 1214 |

Lowest peak indicates best alignment. Pipeline retains shift=0 for v1; this table is informational. Fundamental fix (NSRDB TMY3 / ReEDS multi-year-mean) is deferred to v2 per the plan.

## Industry shape mode

**Active mode:** `efs` (set in preset YAML via `industry_shape_mode`).

**Options:**
- `efs`: original EFS Industrial subsector hourly shape (weather-driven regression).
- `flat`: constant per hour. Simplest, most defensible for bulk industry (~24/7 manufacturing/mining).
- `cambium_residual`: industry shape = busbar_load - resstock - comstock; falls back to flat if residual produces > 5% negative hours.

**Comparison (industry annual = same; hourly stats differ):**

| mode | annual_GWh | peak_MWh | mean_MWh | std_MWh | peak_to_mean |
|---|---|---|---|---|---|
| efs | 2153.7 | 398 | 246 | 62 | 1.62 |
| flat | 2153.7 | 246 | 246 | 0 | 1.00 |
| cambium_residual | 2153.7 | 708 | 246 | 112 | 2.88 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
