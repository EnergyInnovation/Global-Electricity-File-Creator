# Validation report - US-TN

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **102.4 TWh**
- Peak hour: **2018-02-02 10:00:00** at **17.9 GW**
- Cluster NRMSE: **0.392**

## Days per timeslice

- Winter: 45
- Spring: 121
- Summer: 131
- Fall: 52
- Summer Peak: 10
- Winter Peak: 6

## Top-5 peak days

- Summer Peak: [191, 193, 198, 200, 201, 205, 213, 215, 233, 241]
- Winter Peak: [23, 26, 27, 32, 33, 39]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 6284097.3 | 6284097.3 | -0.0 | -0.0 |
| residential-cooling | 5620694.61 | 5620694.61 | 0.0 | 0.0 |
| residential-lighting | 1592502.93 | 1592502.93 | 0.0 | 0.0 |
| residential-appliances | 11655627.2 | 11655627.2 | -0.0 | -0.0 |
| residential-other | 18690123.09 | 18690123.09 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 922174.68 | 922174.68 | 0.0 | 0.0 |
| commercial-cooling | 7331330.6 | 7331330.6 | 0.0 | 0.0 |
| commercial-lighting | 3876670.57 | 3876670.57 | -0.0 | -0.0 |
| commercial-appliances | 6531975.38 | 6531975.38 | 0.0 | 0.0 |
| commercial-other | 17384554.51 | 17384554.51 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 166338.13 | 166338.13 | 0.0 | 0.0 |
| HDVs | 3801.15 | 3801.15 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 22319367.5 | 22319367.5 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.069542 | 594.68 | 8760 |
| Winter | 0.102002 | 631.09 | 1080 |
| Spring | 0.089199 | 613.5 | 2904 |
| Summer | 0.095955 | 597.13 | 3144 |
| Fall | 0.11863 | 614.28 | 1248 |
| Summer Peak | 0.023094 | 132.97 | 240 |
| Winter Peak | 0.083853 | 487.93 | 144 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.108149 | 450.84 | 6284097.3 |
| residential-cooling | 0.163656 | 390.8 | 5620694.61 |
| residential-lighting | 0.062932 | 21.31 | 1592502.93 |
| residential-appliances | 0.086434 | 124.16 | 11655627.2 |
| residential-other | 0.106402 | 93.71 | 18690123.09 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.086202 | 64.96 | 922174.68 |
| commercial-cooling | 0.117164 | 201.43 | 7331330.6 |
| commercial-lighting | 0.165003 | 55.28 | 3876670.57 |
| commercial-appliances | 0.090367 | 79.63 | 6531975.38 |
| commercial-other | 0.186337 | 174.23 | 17384554.51 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.05292 | 2.09 | 166338.13 |
| HDVs | 0.078951 | 0.02 | 3801.15 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.193658 | 310.81 | 22319367.5 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 17321.37 | 17653.76 | 0.9812 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 16228.88 | 16233.48 | 0.9997 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 17321.37 | 17435.31 | 0.9935 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2947.73 | 3259.26 | 0.9044 |  |
| category_peak_commercial-cooling | 2768.55 | 2920.78 | 0.9479 |  |
| category_peak_residential-heating | 4704.29 | 5365.27 | 0.8768 |  |
| category_peak_commercial-heating | 845.65 | 967.16 | 0.8744 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.93 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 16433.77 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 16100.56 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 16901.96 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 17125.62 | 16994.61 | 1.0077 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 15438.65 | 15045.89 | 1.0261 |  |
| winter_peak_net_load | 17125.62 | 16831.5 | 1.0175 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 479.88 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 354.23 | 438 | top 5% of LDC = top ~438 hours |
| overall | 189.94 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0875 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 34 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 17325.14 | shifted gen by -14d; peak hour 2018-02-02 18:00:00 |
| net_load_peak_shift_-7d | 17398.21 | shifted gen by -7d; peak hour 2018-02-02 10:00:00 |
| net_load_peak_shift_0d | 17327.54 | shifted gen by 0d; peak hour 2018-02-02 18:00:00 |
| net_load_peak_shift_7d | 17506.41 | shifted gen by 7d; peak hour 2018-02-02 10:00:00 |
| net_load_peak_shift_14d | 17377.91 | shifted gen by 14d; peak hour 2018-02-01 10:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| TN_total_annual_TWh | 102.38 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| TN_solar_pv_annual_TWh | 4.6975 | 4.6975 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| TN_wind_annual_TWh | 0.054 | 0.054 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 1985.3 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 149.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 29.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2576 | 0.2576 | 0.6121 | 0.6121 |
| solar-pv-dist | 0.1664 | 0.1664 | 0.3764 | 0.3764 |
| onshore-wind | 0.2120 | 0.2120 | 0.0873 | 0.0873 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.087

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 17325 | 2018-02-02 18:00:00 | 11145 |
| -7 | 17398 | 2018-02-02 10:00:00 | 11145 |
| 0 | 17328 | 2018-02-02 18:00:00 | 11145 |
| 7 | 17506 | 2018-02-02 10:00:00 | 11145 |
| 14 | 17378 | 2018-02-01 10:00:00 | 11145 |

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
| efs | 22319.4 | 3457 | 2548 | 569 | 1.36 |
| flat | 22319.4 | 2548 | 2548 | 0 | 1.00 |
| cambium_residual | 22319.4 | 5172 | 2548 | 956 | 2.03 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
