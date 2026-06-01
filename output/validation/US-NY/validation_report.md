# Validation report - US-NY

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **146.4 TWh**
- Peak hour: **2018-01-23 10:00:00** at **25.3 GW**
- Cluster NRMSE: **0.454**

## Days per timeslice

- Winter: 64
- Spring: 90
- Summer: 102
- Fall: 94
- Summer Peak: 10
- Winter Peak: 5

## Top-5 peak days

- Summer Peak: [198, 201, 202, 205, 212, 215, 222, 228, 229, 233]
- Winter Peak: [22, 23, 36, 37, 361]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 8620826.49 | 8620826.49 | 0.0 | 0.0 |
| residential-cooling | 4895111.37 | 4895111.37 | 0.0 | 0.0 |
| residential-lighting | 3748256.15 | 3748256.15 | 0.0 | 0.0 |
| residential-appliances | 15630293.08 | 15630293.08 | -0.0 | -0.0 |
| residential-other | 19708733.88 | 19708733.88 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 2017001.76 | 2017001.76 | 0.0 | 0.0 |
| commercial-cooling | 13821277.84 | 13821277.84 | 0.0 | 0.0 |
| commercial-lighting | 8384290.74 | 8384290.74 | 0.0 | 0.0 |
| commercial-appliances | 12152344.67 | 12152344.67 | 0.0 | 0.0 |
| commercial-other | 37302168.82 | 37302168.82 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 256238.08 | 256238.08 | 0.0 | 0.0 |
| HDVs | 4350.85 | 4350.85 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 2729453.58 | 2729453.58 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 17160859.85 | 17160859.85 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.089685 | 1086.42 | 8760 |
| Winter | 0.09166 | 1025.26 | 1536 |
| Spring | 0.088063 | 911.58 | 2160 |
| Summer | 0.106354 | 1177.57 | 2448 |
| Fall | 0.131029 | 1287.67 | 2256 |
| Summer Peak | 0.045723 | 437.92 | 240 |
| Winter Peak | 0.067598 | 670.49 | 120 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.173528 | 636.5 | 8620826.49 |
| residential-cooling | 0.144637 | 300.86 | 4895111.37 |
| residential-lighting | 0.071279 | 53.71 | 3748256.15 |
| residential-appliances | 0.072041 | 120.5 | 15630293.08 |
| residential-other | 0.110489 | 108.53 | 19708733.88 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.11609 | 149.67 | 2017001.76 |
| commercial-cooling | 0.115825 | 367.82 | 13821277.84 |
| commercial-lighting | 0.162426 | 128.34 | 8384290.74 |
| commercial-appliances | 0.082997 | 135.83 | 12152344.67 |
| commercial-other | 0.183173 | 298.73 | 37302168.82 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.063514 | 4.52 | 256238.08 |
| HDVs | 0.084283 | 0.03 | 4350.85 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.063514 | 48.1 | 2729453.58 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.238151 | 368.66 | 17160859.85 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 24113.67 | 24849.22 | 0.9704 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 22873.84 | 22955.42 | 0.9964 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 24113.67 | 24132.13 | 0.9992 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2451.01 | 2855.46 | 0.8584 |  |
| category_peak_commercial-cooling | 4904.64 | 5510.5 | 0.8901 |  |
| category_peak_residential-heating | 4238.35 | 4492.75 | 0.9434 |  |
| category_peak_commercial-heating | 1469.01 | 1557.22 | 0.9434 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.91 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 23436.29 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 22424.4 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 23916.21 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 23114.67 | 22127.13 | 1.0446 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 20823.37 | 20092.14 | 1.0364 |  |
| winter_peak_net_load | 23114.67 | 21911.72 | 1.0549 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 934.35 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 706.78 | 438 | top 5% of LDC = top ~438 hours |
| overall | 399.03 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0386 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 23 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 22935.13 | shifted gen by -14d; peak hour 2018-02-06 18:00:00 |
| net_load_peak_shift_-7d | 22304.56 | shifted gen by -7d; peak hour 2018-01-24 17:00:00 |
| net_load_peak_shift_0d | 22542.34 | shifted gen by 0d; peak hour 2018-01-22 10:00:00 |
| net_load_peak_shift_7d | 22653.82 | shifted gen by 7d; peak hour 2018-01-23 17:00:00 |
| net_load_peak_shift_14d | 22768.72 | shifted gen by 14d; peak hour 2018-01-23 17:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| NY_total_annual_TWh | 146.43 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| NY_solar_pv_annual_TWh | 9.68 | 9.68 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| NY_wind_annual_TWh | 17.3581 | 17.3581 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 3685.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 1928.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 5099.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 130.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2228 | 0.2228 | 0.5793 | 0.5793 |
| solar-pv-dist | 0.1473 | 0.1473 | 0.3587 | 0.3587 |
| onshore-wind | 0.3778 | 0.3778 | 0.2441 | 0.2441 |
| offshore-wind | 0.4235 | 0.4235 | 0.2965 | 0.2965 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.039

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 22935 | 2018-02-06 18:00:00 | 13629 |
| -7 | 22305 | 2018-01-24 17:00:00 | 13629 |
| 0 | 22542 | 2018-01-22 10:00:00 | 13629 |
| 7 | 22654 | 2018-01-23 17:00:00 | 13629 |
| 14 | 22769 | 2018-01-23 17:00:00 | 13629 |

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
| efs | 17160.9 | 2825 | 1959 | 509 | 1.44 |
| flat | 17160.9 | 1959 | 1959 | 0 | 1.00 |
| cambium_residual | 17160.9 | 6035 | 1959 | 1040 | 3.08 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
