# Validation report - US-MN

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **69.0 TWh**
- Peak hour: **2018-01-09 11:00:00** at **11.5 GW**
- Cluster NRMSE: **0.781**

## Days per timeslice

- Winter: 101
- Spring: 80
- Summer: 65
- Fall: 87
- Summer Peak: 18
- Winter Peak: 14

## Top-5 peak days

- Summer Peak: [152, 153, 158, 191, 193, 194, 198, 201, 205, 212, 214, 226, 227, 233, 234, 235, 240, 241]
- Winter Peak: [25, 34, 37, 47, 54, 310, 352, 353, 354, 355, 359, 362, 363, 365]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 4403089.1 | 4403089.1 | 0.0 | 0.0 |
| residential-cooling | 981091.44 | 981091.44 | -0.0 | -0.0 |
| residential-lighting | 1298552.17 | 1298552.17 | 0.0 | 0.0 |
| residential-appliances | 6707514.65 | 6707514.65 | 0.0 | 0.0 |
| residential-other | 10814243.85 | 10814243.85 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 1004765.53 | 1004765.53 | -0.0 | -0.0 |
| commercial-cooling | 3048153.58 | 3048153.58 | 0.0 | 0.0 |
| commercial-lighting | 2208686.99 | 2208686.99 | 0.0 | 0.0 |
| commercial-appliances | 3271424.38 | 3271424.38 | 0.0 | 0.0 |
| commercial-other | 13535169.99 | 13535169.99 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 115754.32 | 115754.32 | 0.0 | 0.0 |
| HDVs | 2641.47 | 2641.47 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 32830.15 | 32830.15 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 21591023.45 | 21591023.45 | -0.0 | -0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.139835 | 698.81 | 8760 |
| Winter | 0.162959 | 854.1 | 2424 |
| Spring | 0.140471 | 655.01 | 1920 |
| Summer | 0.160564 | 685.99 | 1560 |
| Fall | 0.141814 | 723.99 | 2088 |
| Summer Peak | 0.066283 | 191.16 | 432 |
| Winter Peak | 0.096444 | 384.54 | 336 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.223658 | 418.7 | 4403089.1 |
| residential-cooling | 0.156295 | 53.83 | 981091.44 |
| residential-lighting | 0.079404 | 22.01 | 1298552.17 |
| residential-appliances | 0.080225 | 63.79 | 6707514.65 |
| residential-other | 0.118709 | 67.45 | 10814243.85 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.201041 | 93.56 | 1004765.53 |
| commercial-cooling | 0.116612 | 82.4 | 3048153.58 |
| commercial-lighting | 0.171858 | 37.52 | 2208686.99 |
| commercial-appliances | 0.098448 | 48.36 | 3271424.38 |
| commercial-other | 0.195761 | 137.88 | 13535169.99 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.068486 | 2.29 | 115754.32 |
| HDVs | 0.10863 | 0.03 | 2641.47 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.068486 | 0.65 | 32830.15 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.217438 | 444.74 | 21591023.45 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 10376.99 | 11347.84 | 0.9144 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 9484.93 | 9500.05 | 0.9984 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 10376.99 | 10494.75 | 0.9888 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 326.24 | 463.3 | 0.7042 |  |
| category_peak_commercial-cooling | 898.52 | 1207.29 | 0.7442 |  |
| category_peak_residential-heating | 1510.65 | 2084.57 | 0.7247 |  |
| category_peak_commercial-heating | 433.64 | 558.77 | 0.7761 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.14 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 10758.21 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 9128.97 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 10995.11 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 10096.09 | 10224.63 | 0.9874 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 8740.21 | 7720.88 | 1.132 |  |
| winter_peak_net_load | 10096.09 | 9612.41 | 1.0503 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 730.81 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 979.45 | 438 | top 5% of LDC = top ~438 hours |
| overall | 423.01 | 8760 | full 8760 LDC |

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
| rail | 1.0 | 0.0 | expected ~1.0 across all 6 slices |
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
| summer_daily_corr_buildings_vs_solar_cf | 0.0685 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 4 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 10759.81 | shifted gen by -14d; peak hour 2018-01-06 19:00:00 |
| net_load_peak_shift_-7d | 10358.74 | shifted gen by -7d; peak hour 2018-01-13 19:00:00 |
| net_load_peak_shift_0d | 10483.3 | shifted gen by 0d; peak hour 2018-12-19 18:00:00 |
| net_load_peak_shift_7d | 10548.78 | shifted gen by 7d; peak hour 2018-01-05 12:00:00 |
| net_load_peak_shift_14d | 10705.8 | shifted gen by 14d; peak hour 2018-01-03 12:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| MN_total_annual_TWh | 69.01 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| MN_solar_pv_annual_TWh | 8.0163 | 8.0163 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| MN_wind_annual_TWh | 31.4432 | 31.4432 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 3273.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 859.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 8392.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2394 | 0.2394 | 0.6682 | 0.6682 |
| solar-pv-dist | 0.1532 | 0.1532 | 0.4334 | 0.4334 |
| onshore-wind | 0.4277 | 0.4277 | 0.2427 | 0.2427 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.069

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 10760 | 2018-01-06 19:00:00 | 3374 |
| -7 | 10359 | 2018-01-13 19:00:00 | 3374 |
| 0 | 10483 | 2018-12-19 18:00:00 | 3374 |
| 7 | 10549 | 2018-01-05 12:00:00 | 3374 |
| 14 | 10706 | 2018-01-03 12:00:00 | 3374 |

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
| efs | 21591.0 | 3678 | 2465 | 585 | 1.49 |
| flat | 21591.0 | 2465 | 2465 | 0 | 1.00 |
| cambium_residual | 21591.0 | 5379 | 2465 | 755 | 2.18 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
