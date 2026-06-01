# Validation report - US-IA

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **54.8 TWh**
- Peak hour: **2018-09-07 13:00:00** at **8.7 GW**
- Cluster NRMSE: **0.756**

## Days per timeslice

- Winter: 98
- Spring: 87
- Summer: 59
- Fall: 81
- Summer Peak: 33
- Winter Peak: 7

## Top-5 peak days

- Summer Peak: [152, 158, 160, 164, 165, 170, 174, 175, 182, 184, 192, 194, 195, 198, 201, 202, 204, 207, 209, 211, 213, 214, 215, 216, 217, 218, 219, 220, 221, 223, 228, 235, 242]
- Winter Peak: [26, 33, 46, 334, 338, 353, 355]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 2415395.66 | 2415395.66 | -0.0 | -0.0 |
| residential-cooling | 1080369.28 | 1080369.28 | -0.0 | -0.0 |
| residential-lighting | 790103.17 | 790103.17 | 0.0 | 0.0 |
| residential-appliances | 4195213.95 | 4195213.95 | 0.0 | 0.0 |
| residential-other | 6811058.03 | 6811058.03 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 418751.47 | 418751.47 | 0.0 | 0.0 |
| commercial-cooling | 1974044.55 | 1974044.55 | -0.0 | -0.0 |
| commercial-lighting | 1209437.28 | 1209437.28 | 0.0 | 0.0 |
| commercial-appliances | 1762028.14 | 1762028.14 | -0.0 | -0.0 |
| commercial-other | 7291002.34 | 7291002.34 | -0.0 | -0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 74645.37 | 74645.37 | 0.0 | 0.0 |
| HDVs | 2738.86 | 2738.86 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 26741068.29 | 26741068.29 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.156186 | 621.57 | 8760 |
| Winter | 0.174779 | 698.69 | 2352 |
| Spring | 0.158882 | 575.72 | 2088 |
| Summer | 0.177574 | 673.6 | 1416 |
| Fall | 0.16184 | 632.27 | 1944 |
| Summer Peak | 0.141818 | 474.5 | 792 |
| Winter Peak | 0.091099 | 242.75 | 168 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.248309 | 248.01 | 2415395.66 |
| residential-cooling | 0.156992 | 63.53 | 1080369.28 |
| residential-lighting | 0.074791 | 13.05 | 790103.17 |
| residential-appliances | 0.085561 | 43.94 | 4195213.95 |
| residential-other | 0.119005 | 43.3 | 6811058.03 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.193094 | 43.59 | 418751.47 |
| commercial-cooling | 0.125927 | 57.52 | 1974044.55 |
| commercial-lighting | 0.174973 | 20.42 | 1209437.28 |
| commercial-appliances | 0.098196 | 22.88 | 1762028.14 |
| commercial-other | 0.200462 | 84.34 | 7291002.34 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.063975 | 1.5 | 74645.37 |
| HDVs | 0.091595 | 0.02 | 2738.86 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.194776 | 546.47 | 26741068.29 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 8028.95 | 8617.46 | 0.9317 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 7728.17 | 7767.9 | 0.9949 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 8028.95 | 8039.82 | 0.9986 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 467.95 | 569.86 | 0.8212 |  |
| category_peak_commercial-cooling | 624.19 | 782.36 | 0.7978 |  |
| category_peak_residential-heating | 934.53 | 1156.93 | 0.8078 |  |
| category_peak_commercial-heating | 219.84 | 273.25 | 0.8046 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.48 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 8286.43 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 7361.47 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 8411.58 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 7965.35 | 8091.78 | 0.9844 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 7437.07 | 6529.17 | 1.1391 |  |
| winter_peak_net_load | 7965.35 | 7440.96 | 1.0705 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 591.52 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 625.97 | 438 | top 5% of LDC = top ~438 hours |
| overall | 404.32 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0833 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 353 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 8191.66 | shifted gen by -14d; peak hour 2018-08-08 13:00:00 |
| net_load_peak_shift_-7d | 8177.81 | shifted gen by -7d; peak hour 2018-01-26 12:00:00 |
| net_load_peak_shift_0d | 8228.03 | shifted gen by 0d; peak hour 2018-12-19 11:00:00 |
| net_load_peak_shift_7d | 8156.42 | shifted gen by 7d; peak hour 2018-08-09 12:00:00 |
| net_load_peak_shift_14d | 8024.31 | shifted gen by 14d; peak hour 2018-01-23 11:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| IA_total_annual_TWh | 54.77 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| IA_solar_pv_annual_TWh | 0.6831 | 0.6831 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| IA_wind_annual_TWh | 42.557 | 42.557 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 239.4 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 112.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 12131.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2478 | 0.2478 | 0.6707 | 0.6707 |
| solar-pv-dist | 0.1666 | 0.1666 | 0.4183 | 0.4183 |
| onshore-wind | 0.4004 | 0.4004 | 0.2398 | 0.2398 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.083

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 8192 | 2018-08-08 13:00:00 | 1316 |
| -7 | 8178 | 2018-01-26 12:00:00 | 1316 |
| 0 | 8228 | 2018-12-19 11:00:00 | 1316 |
| 7 | 8156 | 2018-08-09 12:00:00 | 1316 |
| 14 | 8024 | 2018-01-23 11:00:00 | 1316 |

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
| efs | 26741.1 | 4910 | 3053 | 723 | 1.61 |
| flat | 26741.1 | 3053 | 3053 | 0 | 1.00 |
| cambium_residual | 26741.1 | 6648 | 3053 | 943 | 2.18 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
