# Validation report - US-MS

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **49.2 TWh**
- Peak hour: **2018-08-16 14:00:00** at **8.3 GW**
- Cluster NRMSE: **0.355**

## Days per timeslice

- Winter: 32
- Spring: 96
- Summer: 72
- Fall: 126
- Summer Peak: 14
- Winter Peak: 25

## Top-5 peak days

- Summer Peak: [156, 191, 193, 194, 198, 199, 200, 201, 213, 227, 228, 229, 240, 241]
- Winter Peak: [2, 3, 4, 5, 9, 10, 11, 12, 19, 20, 23, 24, 25, 26, 31, 33, 34, 37, 39, 345, 352, 353, 354, 359, 360]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 1904003.52 | 1904003.52 | 0.0 | 0.0 |
| residential-cooling | 3660855.8 | 3660855.8 | -0.0 | -0.0 |
| residential-lighting | 674950.18 | 674950.18 | 0.0 | 0.0 |
| residential-appliances | 4876383.35 | 4876383.35 | 0.0 | 0.0 |
| residential-other | 7821131.3 | 7821131.3 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 220155.63 | 220155.63 | 0.0 | 0.0 |
| commercial-cooling | 3477110.2 | 3477110.2 | 0.0 | 0.0 |
| commercial-lighting | 1459879.84 | 1459879.84 | 0.0 | 0.0 |
| commercial-appliances | 2460222.74 | 2460222.74 | -0.0 | -0.0 |
| commercial-other | 6547889.8 | 6547889.8 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 85568.14 | 85568.14 | 0.0 | 0.0 |
| HDVs | 2556.67 | 2556.67 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 15973785.46 | 15973785.46 | -0.0 | -0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.064376 | 240.24 | 8760 |
| Winter | 0.125203 | 273.39 | 768 |
| Spring | 0.071002 | 216.0 | 2304 |
| Summer | 0.121643 | 300.21 | 1728 |
| Fall | 0.079413 | 252.32 | 3024 |
| Summer Peak | 0.023076 | 66.24 | 336 |
| Winter Peak | 0.063537 | 154.71 | 600 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.121361 | 157.68 | 1904003.52 |
| residential-cooling | 0.153191 | 211.58 | 3660855.8 |
| residential-lighting | 0.058944 | 8.27 | 674950.18 |
| residential-appliances | 0.075744 | 45.26 | 4876383.35 |
| residential-other | 0.109378 | 42.15 | 7821131.3 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.087562 | 17.44 | 220155.63 |
| commercial-cooling | 0.106327 | 82.38 | 3477110.2 |
| commercial-lighting | 0.156102 | 20.71 | 1459879.84 |
| commercial-appliances | 0.101541 | 34.95 | 2460222.74 |
| commercial-other | 0.175078 | 61.73 | 6547889.8 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.047475 | 0.98 | 85568.14 |
| HDVs | 0.079124 | 0.02 | 2556.67 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.156505 | 184.91 | 15973785.46 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 8137.08 | 8255.44 | 0.9857 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 8137.08 | 8158.21 | 0.9974 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 7170.26 | 7208.88 | 0.9946 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 1783.52 | 1950.47 | 0.9144 |  |
| category_peak_commercial-cooling | 1329.46 | 1388.51 | 0.9575 |  |
| category_peak_residential-heating | 1365.29 | 1771.87 | 0.7705 |  |
| category_peak_commercial-heating | 217.57 | 287.27 | 0.7574 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.98 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 7925.2 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 7860.95 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 8074.15 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 8042.81 | 8066.3 | 0.9971 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 8042.81 | 7955.5 | 1.011 |  |
| winter_peak_net_load | 7137.46 | 7087.43 | 1.0071 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 87.11 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 214.14 | 438 | top 5% of LDC = top ~438 hours |
| overall | 78.39 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.2389 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 19 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 8199.91 | shifted gen by -14d; peak hour 2018-08-17 15:00:00 |
| net_load_peak_shift_-7d | 8099.48 | shifted gen by -7d; peak hour 2018-08-16 16:00:00 |
| net_load_peak_shift_0d | 8131.83 | shifted gen by 0d; peak hour 2018-07-20 15:00:00 |
| net_load_peak_shift_7d | 8172.66 | shifted gen by 7d; peak hour 2018-07-20 14:00:00 |
| net_load_peak_shift_14d | 8113.53 | shifted gen by 14d; peak hour 2018-07-20 15:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| MS_total_annual_TWh | 49.16 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| MS_solar_pv_annual_TWh | 0.715 | 0.715 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| MS_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 318.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 22.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2444 | 0.2444 | 0.5210 | 0.5210 |
| solar-pv-dist | 0.1695 | 0.1695 | 0.3479 | 0.3479 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.239

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 8200 | 2018-08-17 15:00:00 | 5531 |
| -7 | 8099 | 2018-08-16 16:00:00 | 5531 |
| 0 | 8132 | 2018-07-20 15:00:00 | 5531 |
| 7 | 8173 | 2018-07-20 14:00:00 | 5531 |
| 14 | 8114 | 2018-07-20 15:00:00 | 5531 |

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
| efs | 15973.8 | 2555 | 1823 | 410 | 1.40 |
| flat | 15973.8 | 1823 | 1823 | 0 | 1.00 |
| cambium_residual | 15973.8 | 3061 | 1823 | 393 | 1.68 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
