# Validation report - US-WI

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **70.5 TWh**
- Peak hour: **2018-01-05 12:00:00** at **12.2 GW**
- Cluster NRMSE: **0.462**

## Days per timeslice

- Winter: 80
- Spring: 60
- Summer: 58
- Fall: 130
- Summer Peak: 28
- Winter Peak: 9

## Top-5 peak days

- Summer Peak: [171, 177, 178, 179, 180, 188, 191, 192, 193, 194, 195, 198, 199, 200, 201, 205, 206, 213, 214, 215, 220, 222, 226, 228, 233, 234, 240, 242]
- Winter Peak: [4, 5, 6, 9, 10, 26, 33, 46, 355]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 4325123.09 | 4325123.09 | -0.0 | -0.0 |
| residential-cooling | 1076720.4 | 1076720.4 | 0.0 | 0.0 |
| residential-lighting | 1488484.76 | 1488484.76 | 0.0 | 0.0 |
| residential-appliances | 6272177.61 | 6272177.61 | 0.0 | 0.0 |
| residential-other | 9866881.59 | 9866881.59 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 783593.2 | 783593.2 | 0.0 | 0.0 |
| commercial-cooling | 3886342.32 | 3886342.32 | 0.0 | 0.0 |
| commercial-lighting | 2492444.31 | 2492444.31 | 0.0 | 0.0 |
| commercial-appliances | 3549296.6 | 3549296.6 | 0.0 | 0.0 |
| commercial-other | 12955363.42 | 12955363.42 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 123410.47 | 123410.47 | 0.0 | 0.0 |
| HDVs | 2913.44 | 2913.44 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 23668494.87 | 23668494.87 | -0.0 | -0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.076078 | 413.01 | 8760 |
| Winter | 0.094421 | 395.91 | 1920 |
| Spring | 0.096495 | 394.4 | 1440 |
| Summer | 0.121661 | 399.42 | 1392 |
| Fall | 0.111997 | 481.81 | 3120 |
| Summer Peak | 0.053877 | 227.67 | 672 |
| Winter Peak | 0.080722 | 359.38 | 216 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.146236 | 268.26 | 4325123.09 |
| residential-cooling | 0.120058 | 48.75 | 1076720.4 |
| residential-lighting | 0.066666 | 19.98 | 1488484.76 |
| residential-appliances | 0.073403 | 52.22 | 6272177.61 |
| residential-other | 0.096348 | 47.55 | 9866881.59 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.124477 | 50.29 | 783593.2 |
| commercial-cooling | 0.087673 | 84.04 | 3886342.32 |
| commercial-lighting | 0.155546 | 39.09 | 2492444.31 |
| commercial-appliances | 0.083698 | 37.05 | 3549296.6 |
| commercial-other | 0.179788 | 134.67 | 12955363.42 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.052174 | 1.65 | 123410.47 |
| HDVs | 0.091645 | 0.03 | 2913.44 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.164459 | 354.13 | 23668494.87 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 11431.48 | 11826.63 | 0.9666 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 10614.45 | 10617.57 | 0.9997 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 11431.48 | 11527.58 | 0.9917 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 452.43 | 562.93 | 0.8037 |  |
| category_peak_commercial-cooling | 1413.14 | 1750.59 | 0.8072 |  |
| category_peak_residential-heating | 1995.32 | 2343.55 | 0.8514 |  |
| category_peak_commercial-heating | 457.13 | 525.26 | 0.8703 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 1.0 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 11007.34 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 10846.88 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 11344.95 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 11291.7 | 11073.04 | 1.0197 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 9662.69 | 9140.15 | 1.0572 |  |
| winter_peak_net_load | 11291.7 | 10850.72 | 1.0406 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 246.72 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 286.89 | 438 | top 5% of LDC = top ~438 hours |
| overall | 166.58 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0274 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 5 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 11318.23 | shifted gen by -14d; peak hour 2018-01-05 18:00:00 |
| net_load_peak_shift_-7d | 11669.63 | shifted gen by -7d; peak hour 2018-01-05 18:00:00 |
| net_load_peak_shift_0d | 11372.93 | shifted gen by 0d; peak hour 2018-01-05 18:00:00 |
| net_load_peak_shift_7d | 11860.83 | shifted gen by 7d; peak hour 2018-01-05 18:00:00 |
| net_load_peak_shift_14d | 11817.75 | shifted gen by 14d; peak hour 2018-01-04 18:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| WI_total_annual_TWh | 70.49 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| WI_solar_pv_annual_TWh | 5.9622 | 5.9622 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| WI_wind_annual_TWh | 2.7542 | 2.7542 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 2713.4 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 138.4 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 886.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2428 | 0.2428 | 0.6383 | 0.6383 |
| solar-pv-dist | 0.1576 | 0.1576 | 0.3916 | 0.3916 |
| onshore-wind | 0.3546 | 0.3546 | 0.1958 | 0.1958 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.027

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 11318 | 2018-01-05 18:00:00 | 7052 |
| -7 | 11670 | 2018-01-05 18:00:00 | 7052 |
| 0 | 11373 | 2018-01-05 18:00:00 | 7052 |
| 7 | 11861 | 2018-01-05 18:00:00 | 7052 |
| 14 | 11818 | 2018-01-04 18:00:00 | 7052 |

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
| efs | 23668.5 | 4337 | 2702 | 669 | 1.61 |
| flat | 23668.5 | 2702 | 2702 | 0 | 1.00 |
| cambium_residual | 23668.5 | 6661 | 2702 | 1009 | 2.47 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
