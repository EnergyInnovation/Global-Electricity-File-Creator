# Validation report - US-IL

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **137.5 TWh**
- Peak hour: **2018-02-02 11:00:00** at **24.0 GW**
- Cluster NRMSE: **0.551**

## Days per timeslice

- Winter: 95
- Spring: 91
- Summer: 106
- Fall: 61
- Summer Peak: 6
- Winter Peak: 6

## Top-5 peak days

- Summer Peak: [187, 194, 198, 200, 213, 240]
- Winter Peak: [9, 25, 26, 33, 34, 353]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 8013660.61 | 8013660.61 | -0.0 | -0.0 |
| residential-cooling | 3854290.74 | 3854290.74 | 0.0 | 0.0 |
| residential-lighting | 2818027.55 | 2818027.55 | 0.0 | 0.0 |
| residential-appliances | 12482834.11 | 12482834.11 | -0.0 | -0.0 |
| residential-other | 19650993.55 | 19650993.55 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 1196568.0 | 1196568.0 | -0.0 | -0.0 |
| commercial-cooling | 9235257.91 | 9235257.91 | 0.0 | 0.0 |
| commercial-lighting | 4883792.5 | 4883792.5 | 0.0 | 0.0 |
| commercial-appliances | 6953575.62 | 6953575.62 | -0.0 | -0.0 |
| commercial-other | 25380363.42 | 25380363.42 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 206684.48 | 206684.48 | 0.0 | 0.0 |
| HDVs | 4732.8 | 4732.8 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 565038.6 | 565038.6 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 42297195.19 | 42297195.19 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.103714 | 1173.12 | 8760 |
| Winter | 0.107542 | 1076.34 | 2280 |
| Spring | 0.155231 | 1424.48 | 2184 |
| Summer | 0.125978 | 1252.42 | 2544 |
| Fall | 0.101248 | 922.38 | 1464 |
| Summer Peak | 0.05023 | 415.54 | 144 |
| Winter Peak | 0.093569 | 798.83 | 144 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.183506 | 789.97 | 8013660.61 |
| residential-cooling | 0.177376 | 290.11 | 3854290.74 |
| residential-lighting | 0.075295 | 45.31 | 2818027.55 |
| residential-appliances | 0.081234 | 115.33 | 12482834.11 |
| residential-other | 0.124074 | 129.15 | 19650993.55 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.125066 | 119.8 | 1196568.0 |
| commercial-cooling | 0.126219 | 319.82 | 9235257.91 |
| commercial-lighting | 0.176543 | 85.89 | 4883792.5 |
| commercial-appliances | 0.099258 | 99.17 | 6953575.62 |
| commercial-other | 0.200756 | 263.95 | 25380363.42 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.064156 | 3.68 | 206684.48 |
| HDVs | 0.113844 | 0.05 | 4732.8 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.064156 | 10.07 | 565038.6 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.179029 | 742.34 | 42297195.19 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 22404.3 | 23018.55 | 0.9733 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 21949.44 | 21949.44 | 1.0 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 22404.3 | 22568.45 | 0.9927 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2009.01 | 2218.05 | 0.9058 |  |
| category_peak_commercial-cooling | 3489.12 | 3996.19 | 0.8731 |  |
| category_peak_residential-heating | 4302.55 | 5020.22 | 0.857 |  |
| category_peak_commercial-heating | 1010.73 | 1199.22 | 0.8428 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.54 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 21773.28 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 20345.85 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 22315.57 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 21904.7 | 22082.45 | 0.992 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 19769.41 | 18925.73 | 1.0446 |  |
| winter_peak_net_load | 21904.7 | 21822.19 | 1.0038 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 657.59 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 957.55 | 438 | top 5% of LDC = top ~438 hours |
| overall | 471.82 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0445 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 33 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 21418.92 | shifted gen by -14d; peak hour 2018-02-01 09:00:00 |
| net_load_peak_shift_-7d | 21764.93 | shifted gen by -7d; peak hour 2018-02-02 11:00:00 |
| net_load_peak_shift_0d | 23048.97 | shifted gen by 0d; peak hour 2018-02-02 19:00:00 |
| net_load_peak_shift_7d | 22957.13 | shifted gen by 7d; peak hour 2018-02-02 11:00:00 |
| net_load_peak_shift_14d | 21909.98 | shifted gen by 14d; peak hour 2018-02-03 20:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| IL_total_annual_TWh | 137.54 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| IL_solar_pv_annual_TWh | 9.1562 | 9.1562 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| IL_wind_annual_TWh | 24.0175 | 24.0175 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 3811.3 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 426.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 7638.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2560 | 0.2560 | 0.6602 | 0.6602 |
| solar-pv-dist | 0.1632 | 0.1632 | 0.3898 | 0.3898 |
| onshore-wind | 0.3589 | 0.3589 | 0.1805 | 0.1805 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.044

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 21419 | 2018-02-01 09:00:00 | 11914 |
| -7 | 21765 | 2018-02-02 11:00:00 | 11914 |
| 0 | 23049 | 2018-02-02 19:00:00 | 11914 |
| 7 | 22957 | 2018-02-02 11:00:00 | 11914 |
| 14 | 21910 | 2018-02-03 20:00:00 | 11914 |

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
| efs | 42297.2 | 7605 | 4828 | 1123 | 1.57 |
| flat | 42297.2 | 4828 | 4828 | 0 | 1.00 |
| cambium_residual | 42297.2 | 12441 | 4828 | 1663 | 2.58 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
