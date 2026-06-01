# Validation report - US-AZ

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **87.1 TWh**
- Peak hour: **2018-07-24 18:00:00** at **16.4 GW**
- Cluster NRMSE: **0.291**

## Days per timeslice

- Winter: 97
- Spring: 80
- Summer: 102
- Fall: 44
- Summer Peak: 16
- Winter Peak: 26

## Top-5 peak days

- Summer Peak: [186, 194, 196, 197, 202, 205, 215, 219, 220, 221, 223, 229, 231, 235, 236, 243]
- Winter Peak: [14, 35, 42, 49, 50, 51, 53, 54, 55, 56, 57, 58, 59, 305, 306, 307, 308, 309, 310, 311, 312, 316, 317, 318, 319, 329]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 3289114.89 | 3289114.89 | 0.0 | 0.0 |
| residential-cooling | 11039645.37 | 11039645.37 | 0.0 | 0.0 |
| residential-lighting | 2310336.17 | 2310336.17 | 0.0 | 0.0 |
| residential-appliances | 9615222.74 | 9615222.74 | 0.0 | 0.0 |
| residential-other | 13813933.18 | 13813933.18 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 256318.58 | 256318.58 | 0.0 | 0.0 |
| commercial-cooling | 8131858.15 | 8131858.15 | 0.0 | 0.0 |
| commercial-lighting | 2494498.83 | 2494498.83 | 0.0 | 0.0 |
| commercial-appliances | 4317848.77 | 4317848.77 | 0.0 | 0.0 |
| commercial-other | 17280920.28 | 17280920.28 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 145803.72 | 145803.72 | -0.0 | -0.0 |
| HDVs | 3366.19 | 3366.19 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 40835.78 | 40835.78 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 14410105.95 | 14410105.95 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.09054 | 773.07 | 8760 |
| Winter | 0.119768 | 779.47 | 2328 |
| Spring | 0.102445 | 751.24 | 1920 |
| Summer | 0.085261 | 717.25 | 2448 |
| Fall | 0.123643 | 993.94 | 1056 |
| Summer Peak | 0.095696 | 700.95 | 384 |
| Winter Peak | 0.124174 | 705.89 | 624 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.091707 | 245.28 | 3289114.89 |
| residential-cooling | 0.125277 | 531.04 | 11039645.37 |
| residential-lighting | 0.05022 | 24.05 | 2310336.17 |
| residential-appliances | 0.074031 | 88.56 | 9615222.74 |
| residential-other | 0.070221 | 63.0 | 13813933.18 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.068201 | 17.3 | 256318.58 |
| commercial-cooling | 0.101265 | 195.55 | 8131858.15 |
| commercial-lighting | 0.18218 | 40.09 | 2494498.83 |
| commercial-appliances | 0.091008 | 56.12 | 4317848.77 |
| commercial-other | 0.199556 | 190.93 | 17280920.28 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.065461 | 2.51 | 145803.72 |
| HDVs | 0.090321 | 0.03 | 3366.19 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.065461 | 0.7 | 40835.78 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.23974 | 344.67 | 14410105.95 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 14942.03 | 16152.72 | 0.925 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 14942.03 | 15095.56 | 0.9898 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 10558.84 | 10897.76 | 0.9689 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 5028.91 | 5859.36 | 0.8583 |  |
| category_peak_commercial-cooling | 2697.21 | 3121.6 | 0.864 |  |
| category_peak_residential-heating | 2202.05 | 4761.56 | 0.4625 |  |
| category_peak_commercial-heating | 240.67 | 452.37 | 0.532 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.64 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 15319.24 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 14001.07 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 15663.45 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 14873.63 | 15461.84 | 0.962 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 14873.63 | 14430.68 | 1.0307 |  |
| winter_peak_net_load | 10469.09 | 10396.71 | 1.007 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 981.33 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 806.26 | 438 | top 5% of LDC = top ~438 hours |
| overall | 331.94 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.1136 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 205 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 16031.78 | shifted gen by -14d; peak hour 2018-08-08 18:00:00 |
| net_load_peak_shift_-7d | 16158.34 | shifted gen by -7d; peak hour 2018-07-24 18:00:00 |
| net_load_peak_shift_0d | 15633.09 | shifted gen by 0d; peak hour 2018-07-24 19:00:00 |
| net_load_peak_shift_7d | 15890.18 | shifted gen by 7d; peak hour 2018-08-08 18:00:00 |
| net_load_peak_shift_14d | 15741.89 | shifted gen by 14d; peak hour 2018-07-24 19:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| AZ_total_annual_TWh | 87.15 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| AZ_solar_pv_annual_TWh | 52.7369 | 52.7369 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| AZ_wind_annual_TWh | 1.6502 | 1.6502 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 18155.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 1611.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 617.3 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.3142 | 0.3142 | 0.7441 | 0.7441 |
| solar-pv-dist | 0.1959 | 0.1959 | 0.4392 | 0.4392 |
| onshore-wind | 0.3052 | 0.3052 | 0.2304 | 0.2304 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.114

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 16032 | 2018-08-08 18:00:00 | 3740 |
| -7 | 16158 | 2018-07-24 18:00:00 | 3740 |
| 0 | 15633 | 2018-07-24 19:00:00 | 3740 |
| 7 | 15890 | 2018-08-08 18:00:00 | 3740 |
| 14 | 15742 | 2018-07-24 19:00:00 | 3740 |

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
| efs | 14410.1 | 2354 | 1645 | 427 | 1.43 |
| flat | 14410.1 | 1645 | 1645 | 0 | 1.00 |
| cambium_residual | 14410.1 | 3639 | 1645 | 545 | 2.21 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
