# Validation report - US-WV

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **33.7 TWh**
- Peak hour: **2018-01-17 09:00:00** at **6.2 GW**
- Cluster NRMSE: **0.367**

## Days per timeslice

- Winter: 45
- Spring: 132
- Summer: 87
- Fall: 77
- Summer Peak: 17
- Winter Peak: 7

## Top-5 peak days

- Summer Peak: [159, 163, 173, 177, 186, 193, 194, 200, 201, 208, 213, 215, 221, 222, 227, 240, 241]
- Winter Peak: [10, 11, 16, 17, 26, 27, 37]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 2205679.95 | 2205679.95 | 0.0 | 0.0 |
| residential-cooling | 659536.93 | 659536.93 | 0.0 | 0.0 |
| residential-lighting | 520866.65 | 520866.65 | 0.0 | 0.0 |
| residential-appliances | 3291890.39 | 3291890.39 | 0.0 | 0.0 |
| residential-other | 4618763.19 | 4618763.19 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 214429.37 | 214429.37 | 0.0 | 0.0 |
| commercial-cooling | 1332711.02 | 1332711.02 | 0.0 | 0.0 |
| commercial-lighting | 836201.64 | 836201.64 | 0.0 | 0.0 |
| commercial-appliances | 1548631.3 | 1548631.3 | -0.0 | -0.0 |
| commercial-other | 3438628.37 | 3438628.37 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 38718.68 | 38718.68 | -0.0 | -0.0 |
| HDVs | 1226.19 | 1226.19 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 15028365.94 | 15028365.94 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.059888 | 180.79 | 8760 |
| Winter | 0.113043 | 255.34 | 1080 |
| Spring | 0.093447 | 170.98 | 3168 |
| Summer | 0.110988 | 178.66 | 2088 |
| Fall | 0.089563 | 179.96 | 1848 |
| Summer Peak | 0.040151 | 61.21 | 408 |
| Winter Peak | 0.105627 | 212.84 | 168 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.118756 | 178.31 | 2205679.95 |
| residential-cooling | 0.157974 | 44.56 | 659536.93 |
| residential-lighting | 0.069258 | 7.77 | 520866.65 |
| residential-appliances | 0.083967 | 33.17 | 3291890.39 |
| residential-other | 0.115059 | 26.2 | 4618763.19 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.110105 | 16.79 | 214429.37 |
| commercial-cooling | 0.108473 | 34.49 | 1332711.02 |
| commercial-lighting | 0.131423 | 10.29 | 836201.64 |
| commercial-appliances | 0.089581 | 18.8 | 1548631.3 |
| commercial-other | 0.167161 | 25.62 | 3438628.37 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.040256 | 0.37 | 38718.68 |
| HDVs | 0.083342 | 0.01 | 1226.19 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.12704 | 135.12 | 15028365.94 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 5865.31 | 6086.92 | 0.9636 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 4823.47 | 4837.07 | 0.9972 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 5865.31 | 5885.94 | 0.9965 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 323.31 | 389.0 | 0.8311 |  |
| category_peak_commercial-cooling | 472.98 | 528.72 | 0.8946 |  |
| category_peak_residential-heating | 1385.37 | 1621.96 | 0.8541 |  |
| category_peak_commercial-heating | 162.28 | 203.0 | 0.7994 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.66 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 5507.74 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 5350.68 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 5724.79 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 5824.41 | 5688.23 | 1.0239 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 4738.92 | 4722.14 | 1.0036 |  |
| winter_peak_net_load | 5824.41 | 5612.23 | 1.0378 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 186.82 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 146.81 | 438 | top 5% of LDC = top ~438 hours |
| overall | 63.5 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0429 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 17 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 6040.09 | shifted gen by -14d; peak hour 2018-01-26 09:00:00 |
| net_load_peak_shift_-7d | 5713.98 | shifted gen by -7d; peak hour 2018-01-24 09:00:00 |
| net_load_peak_shift_0d | 6015.39 | shifted gen by 0d; peak hour 2018-01-26 09:00:00 |
| net_load_peak_shift_7d | 6033.36 | shifted gen by 7d; peak hour 2018-01-17 11:00:00 |
| net_load_peak_shift_14d | 5958.48 | shifted gen by 14d; peak hour 2018-01-24 09:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| WV_total_annual_TWh | 33.74 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| WV_solar_pv_annual_TWh | 0.2329 | 0.2329 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| WV_wind_annual_TWh | 2.6129 | 2.6129 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 50.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 96.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 878.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2353 | 0.2353 | 0.6038 | 0.6038 |
| solar-pv-dist | 0.1530 | 0.1530 | 0.3783 | 0.3783 |
| onshore-wind | 0.3394 | 0.3394 | 0.2070 | 0.2070 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.043

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 6040 | 2018-01-26 09:00:00 | 3526 |
| -7 | 5714 | 2018-01-24 09:00:00 | 3526 |
| 0 | 6015 | 2018-01-26 09:00:00 | 3526 |
| 7 | 6033 | 2018-01-17 11:00:00 | 3526 |
| 14 | 5958 | 2018-01-24 09:00:00 | 3526 |

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
| efs | 15028.4 | 2485 | 1716 | 434 | 1.45 |
| flat | 15028.4 | 1716 | 1716 | 0 | 1.00 |
| cambium_residual | 15028.4 | 3269 | 1716 | 486 | 1.91 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
