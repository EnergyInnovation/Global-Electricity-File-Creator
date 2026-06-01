# Validation report - US-RI

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **7.8 TWh**
- Peak hour: **2018-01-17 10:00:00** at **1.4 GW**
- Cluster NRMSE: **0.832**

## Days per timeslice

- Winter: 33
- Spring: 99
- Summer: 119
- Fall: 84
- Summer Peak: 14
- Winter Peak: 16

## Top-5 peak days

- Summer Peak: [152, 159, 160, 172, 185, 212, 214, 222, 226, 229, 232, 233, 234, 241]
- Winter Peak: [10, 12, 17, 23, 27, 37, 40, 46, 47, 48, 51, 316, 348, 349, 354, 360]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 471657.97 | 471657.97 | 0.0 | 0.0 |
| residential-cooling | 147825.5 | 147825.5 | 0.0 | 0.0 |
| residential-lighting | 247597.86 | 247597.86 | 0.0 | 0.0 |
| residential-appliances | 1081876.61 | 1081876.61 | 0.0 | 0.0 |
| residential-other | 1260411.49 | 1260411.49 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 77483.29 | 77483.29 | -0.0 | -0.0 |
| commercial-cooling | 527520.52 | 527520.52 | 0.0 | 0.0 |
| commercial-lighting | 319613.13 | 319613.13 | 0.0 | 0.0 |
| commercial-appliances | 702417.94 | 702417.94 | -0.0 | -0.0 |
| commercial-other | 2336559.2 | 2336559.2 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 17593.41 | 17593.41 | -0.0 | -0.0 |
| HDVs | 160.79 | 160.79 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 656969.63 | 656969.63 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.110094 | 71.81 | 8760 |
| Winter | 0.117034 | 62.68 | 792 |
| Spring | 0.124742 | 80.61 | 2376 |
| Summer | 0.125517 | 79.17 | 2856 |
| Fall | 0.112733 | 63.42 | 2016 |
| Summer Peak | 0.074651 | 37.61 | 336 |
| Winter Peak | 0.096843 | 55.46 | 384 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.170403 | 42.75 | 471657.97 |
| residential-cooling | 0.136207 | 9.73 | 147825.5 |
| residential-lighting | 0.073018 | 3.85 | 247597.86 |
| residential-appliances | 0.073973 | 10.19 | 1081876.61 |
| residential-other | 0.123682 | 8.23 | 1260411.49 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.15258 | 7.04 | 77483.29 |
| commercial-cooling | 0.097726 | 15.95 | 527520.52 |
| commercial-lighting | 0.148536 | 4.78 | 319613.13 |
| commercial-appliances | 0.080554 | 7.89 | 702417.94 |
| commercial-other | 0.179869 | 21.15 | 2336559.2 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.064211 | 0.35 | 17593.41 |
| HDVs | 0.06745 | 0.0 | 160.79 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.215914 | 16.76 | 656969.63 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 1214.64 | 1329.87 | 0.9134 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 1127.78 | 1133.07 | 0.9953 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 1214.64 | 1222.65 | 0.9935 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 59.57 | 91.37 | 0.652 |  |
| category_peak_commercial-cooling | 173.82 | 254.49 | 0.683 |  |
| category_peak_residential-heating | 172.47 | 275.1 | 0.6269 |  |
| category_peak_commercial-heating | 32.36 | 55.22 | 0.586 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.18 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 1246.83 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 1093.68 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 1283.85 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 1214.64 | 1207.75 | 1.0057 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 1018.61 | 943.9 | 1.0791 |  |
| winter_peak_net_load | 1214.64 | 1142.41 | 1.0632 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 95.84 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 102.58 | 438 | top 5% of LDC = top ~438 hours |
| overall | 41.17 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.064 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 22 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 1315.51 | shifted gen by -14d; peak hour 2018-01-26 18:00:00 |
| net_load_peak_shift_-7d | 1243.83 | shifted gen by -7d; peak hour 2018-12-19 18:00:00 |
| net_load_peak_shift_0d | 1234.52 | shifted gen by 0d; peak hour 2018-12-26 18:00:00 |
| net_load_peak_shift_7d | 1292.66 | shifted gen by 7d; peak hour 2018-01-17 18:00:00 |
| net_load_peak_shift_14d | 1266.38 | shifted gen by 14d; peak hour 2018-01-27 19:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| RI_total_annual_TWh | 7.85 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| RI_solar_pv_annual_TWh | 0.8207 | 0.8207 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| RI_wind_annual_TWh | 2.8732 | 2.8732 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 273.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 211.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 21.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 734.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2214 | 0.2214 | 0.5133 | 0.5133 |
| solar-pv-dist | 0.1570 | 0.1570 | 0.3413 | 0.3413 |
| onshore-wind | 0.3846 | 0.3846 | 0.2746 | 0.2746 |
| offshore-wind | 0.4359 | 0.4359 | 0.4298 | 0.4298 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.064

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 1316 | 2018-01-26 18:00:00 | 474 |
| -7 | 1244 | 2018-12-19 18:00:00 | 474 |
| 0 | 1235 | 2018-12-26 18:00:00 | 474 |
| 7 | 1293 | 2018-01-17 18:00:00 | 474 |
| 14 | 1266 | 2018-01-27 19:00:00 | 474 |

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
| efs | 657.0 | 126 | 75 | 22 | 1.68 |
| flat | 657.0 | 75 | 75 | 0 | 1.00 |
| cambium_residual | 657.0 | 75 | 75 | 0 | 1.00 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
