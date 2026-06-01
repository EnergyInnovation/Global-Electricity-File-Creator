# Validation report - US-MT

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **15.6 TWh**
- Peak hour: **2018-01-05 20:00:00** at **2.4 GW**
- Cluster NRMSE: **0.617**

## Days per timeslice

- Winter: 126
- Spring: 112
- Summer: 88
- Fall: 1
- Summer Peak: 28
- Winter Peak: 10

## Top-5 peak days

- Summer Peak: [156, 181, 190, 191, 192, 193, 194, 197, 198, 199, 200, 202, 204, 208, 212, 214, 215, 218, 219, 223, 227, 229, 230, 233, 234, 236, 239, 241]
- Winter Peak: [19, 34, 38, 59, 331, 348, 359, 360, 361, 362]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 1048124.27 | 1048124.27 | 0.0 | 0.0 |
| residential-cooling | 143549.82 | 143549.82 | 0.0 | 0.0 |
| residential-lighting | 419579.13 | 419579.13 | 0.0 | 0.0 |
| residential-appliances | 1768663.54 | 1768663.54 | 0.0 | 0.0 |
| residential-other | 2548473.04 | 2548473.04 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 193421.16 | 193421.16 | -0.0 | -0.0 |
| commercial-cooling | 619657.09 | 619657.09 | 0.0 | 0.0 |
| commercial-lighting | 443689.92 | 443689.92 | 0.0 | 0.0 |
| commercial-appliances | 769097.3 | 769097.3 | 0.0 | 0.0 |
| commercial-other | 3078048.07 | 3078048.07 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 26237.81 | 26237.81 | 0.0 | 0.0 |
| HDVs | 1205.13 | 1205.13 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 4558948.63 | 4558948.63 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.106506 | 100.52 | 8760 |
| Winter | 0.123026 | 119.77 | 3024 |
| Spring | 0.116898 | 100.88 | 2688 |
| Summer | 0.109313 | 97.08 | 2112 |
| Fall | 0.0 | 0.0 | 24 |
| Summer Peak | 0.061044 | 42.51 | 672 |
| Winter Peak | 0.068259 | 56.69 | 240 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.213408 | 79.01 | 1048124.27 |
| residential-cooling | 0.121254 | 6.74 | 143549.82 |
| residential-lighting | 0.0758 | 6.8 | 419579.13 |
| residential-appliances | 0.082367 | 17.94 | 1768663.54 |
| residential-other | 0.105772 | 14.34 | 2548473.04 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.159584 | 14.79 | 193421.16 |
| commercial-cooling | 0.091673 | 10.78 | 619657.09 |
| commercial-lighting | 0.175852 | 7.19 | 443689.92 |
| commercial-appliances | 0.117407 | 10.92 | 769097.3 |
| commercial-other | 0.16897 | 26.82 | 3078048.07 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.065913 | 0.49 | 26237.81 |
| HDVs | 0.134448 | 0.01 | 1205.13 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.187902 | 89.47 | 4558948.63 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 2259.18 | 2392.59 | 0.9442 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 2163.32 | 2163.32 | 1.0 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 2259.18 | 2269.35 | 0.9955 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 60.85 | 75.79 | 0.8029 |  |
| category_peak_commercial-cooling | 188.28 | 221.41 | 0.8503 |  |
| category_peak_residential-heating | 410.99 | 465.17 | 0.8835 |  |
| category_peak_commercial-heating | 94.11 | 116.82 | 0.8056 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.13 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 2276.5 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 2027.11 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 2320.95 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 2203.08 | 2191.72 | 1.0052 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 2082.22 | 1892.07 | 1.1005 |  |
| winter_peak_net_load | 2203.08 | 2083.78 | 1.0572 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 119.21 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 131.71 | 438 | top 5% of LDC = top ~438 hours |
| overall | 59.59 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0007 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 362 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 2291.07 | shifted gen by -14d; peak hour 2018-01-05 20:00:00 |
| net_load_peak_shift_-7d | 2199.51 | shifted gen by -7d; peak hour 2018-12-21 20:00:00 |
| net_load_peak_shift_0d | 2362.74 | shifted gen by 0d; peak hour 2018-12-28 20:00:00 |
| net_load_peak_shift_7d | 2325.36 | shifted gen by 7d; peak hour 2018-01-04 20:00:00 |
| net_load_peak_shift_14d | 2311.62 | shifted gen by 14d; peak hour 2018-01-09 21:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| MT_total_annual_TWh | 15.62 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| MT_solar_pv_annual_TWh | 0.7072 | 0.7072 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| MT_wind_annual_TWh | 6.6184 | 6.6184 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 327.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 26.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 1859.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2342 | 0.2342 | 0.6338 | 0.6338 |
| solar-pv-dist | 0.1583 | 0.1583 | 0.4326 | 0.4326 |
| onshore-wind | 0.4062 | 0.4062 | 0.2809 | 0.2809 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.001

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 2291 | 2018-01-05 20:00:00 | 947 |
| -7 | 2200 | 2018-12-21 20:00:00 | 947 |
| 0 | 2363 | 2018-12-28 20:00:00 | 947 |
| 7 | 2325 | 2018-01-04 20:00:00 | 947 |
| 14 | 2312 | 2018-01-09 21:00:00 | 947 |

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
| efs | 4558.9 | 825 | 520 | 137 | 1.59 |
| flat | 4558.9 | 520 | 520 | 0 | 1.00 |
| cambium_residual | 4558.9 | 807 | 520 | 93 | 1.55 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
