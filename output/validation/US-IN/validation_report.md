# Validation report - US-IN

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **102.3 TWh**
- Peak hour: **2018-01-05 10:00:00** at **16.7 GW**
- Cluster NRMSE: **0.467**

## Days per timeslice

- Winter: 32
- Spring: 103
- Summer: 86
- Fall: 113
- Summer Peak: 19
- Winter Peak: 12

## Top-5 peak days

- Summer Peak: [177, 179, 194, 198, 199, 207, 212, 213, 214, 215, 216, 220, 221, 226, 227, 228, 229, 233, 234]
- Winter Peak: [9, 25, 26, 27, 33, 34, 37, 38, 39, 40, 46, 353]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 5672801.88 | 5672801.88 | 0.0 | 0.0 |
| residential-cooling | 2907854.63 | 2907854.63 | -0.0 | -0.0 |
| residential-lighting | 2103859.91 | 2103859.91 | 0.0 | 0.0 |
| residential-appliances | 9134249.71 | 9134249.71 | 0.0 | 0.0 |
| residential-other | 14373798.36 | 14373798.36 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 557837.05 | 557837.05 | 0.0 | 0.0 |
| commercial-cooling | 4705568.58 | 4705568.58 | 0.0 | 0.0 |
| commercial-lighting | 2437543.96 | 2437543.96 | 0.0 | 0.0 |
| commercial-appliances | 3469841.74 | 3469841.74 | -0.0 | -0.0 |
| commercial-other | 12664097.3 | 12664097.3 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 150177.46 | 150177.46 | 0.0 | 0.0 |
| HDVs | 4522.19 | 4522.19 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 47417.35 | 47417.35 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 44047844.72 | 44047844.72 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.093254 | 668.1 | 8760 |
| Winter | 0.098107 | 557.49 | 768 |
| Spring | 0.096732 | 579.94 | 2472 |
| Summer | 0.109043 | 666.93 | 2064 |
| Fall | 0.166547 | 889.67 | 2712 |
| Summer Peak | 0.03875 | 196.61 | 456 |
| Winter Peak | 0.073467 | 388.37 | 288 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.171874 | 461.07 | 5672801.88 |
| residential-cooling | 0.153808 | 187.53 | 2907854.63 |
| residential-lighting | 0.071693 | 32.4 | 2103859.91 |
| residential-appliances | 0.081283 | 87.38 | 9134249.71 |
| residential-other | 0.112416 | 80.21 | 14373798.36 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.138809 | 45.75 | 557837.05 |
| commercial-cooling | 0.110417 | 133.43 | 4705568.58 |
| commercial-lighting | 0.182592 | 38.52 | 2437543.96 |
| commercial-appliances | 0.099315 | 48.2 | 3469841.74 |
| commercial-other | 0.198706 | 140.64 | 12664097.3 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.051526 | 1.7 | 150177.46 |
| HDVs | 0.100277 | 0.04 | 4522.19 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.051526 | 0.54 | 47417.35 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.175447 | 483.79 | 44047844.72 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 16004.13 | 16601.11 | 0.964 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 14911.71 | 14954.39 | 0.9971 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 16004.13 | 16056.93 | 0.9967 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 1484.32 | 1683.4 | 0.8817 |  |
| category_peak_commercial-cooling | 1826.37 | 2098.96 | 0.8701 |  |
| category_peak_residential-heating | 2757.8 | 3286.51 | 0.8391 |  |
| category_peak_commercial-heating | 364.78 | 431.9 | 0.8446 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.87 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 15815.98 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 15229.51 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 16108.85 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 15884.63 | 15882.63 | 1.0001 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 14392.69 | 13969.64 | 1.0303 |  |
| winter_peak_net_load | 15884.63 | 15509.47 | 1.0242 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 464.07 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 340.98 | 438 | top 5% of LDC = top ~438 hours |
| overall | 299.66 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0463 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 8 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 16023.92 | shifted gen by -14d; peak hour 2018-01-05 10:00:00 |
| net_load_peak_shift_-7d | 16168.52 | shifted gen by -7d; peak hour 2018-02-01 10:00:00 |
| net_load_peak_shift_0d | 16122.17 | shifted gen by 0d; peak hour 2018-02-08 09:00:00 |
| net_load_peak_shift_7d | 16413.82 | shifted gen by 7d; peak hour 2018-01-05 10:00:00 |
| net_load_peak_shift_14d | 16448.49 | shifted gen by 14d; peak hour 2018-01-09 10:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| IN_total_annual_TWh | 102.28 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| IN_solar_pv_annual_TWh | 2.6214 | 2.6214 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| IN_wind_annual_TWh | 10.5073 | 10.5073 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 1048.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 255.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 3591.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2456 | 0.2456 | 0.6858 | 0.6858 |
| solar-pv-dist | 0.1633 | 0.1633 | 0.4291 | 0.4291 |
| onshore-wind | 0.3339 | 0.3339 | 0.1635 | 0.1635 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.046

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 16024 | 2018-01-05 10:00:00 | 10177 |
| -7 | 16169 | 2018-02-01 10:00:00 | 10177 |
| 0 | 16122 | 2018-02-08 09:00:00 | 10177 |
| 7 | 16414 | 2018-01-05 10:00:00 | 10177 |
| 14 | 16448 | 2018-01-09 10:00:00 | 10177 |

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
| efs | 44047.8 | 6714 | 5028 | 1049 | 1.34 |
| flat | 44047.8 | 5028 | 5028 | 0 | 1.00 |
| cambium_residual | 44047.8 | 9222 | 5028 | 1362 | 1.83 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
