# Validation report - US-VA

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **137.0 TWh**
- Peak hour: **2018-01-23 10:00:00** at **25.7 GW**
- Cluster NRMSE: **0.597**

## Days per timeslice

- Winter: 36
- Spring: 90
- Summer: 154
- Fall: 63
- Summer Peak: 15
- Winter Peak: 7

## Top-5 peak days

- Summer Peak: [159, 164, 165, 171, 194, 204, 205, 213, 214, 220, 222, 226, 229, 233, 240]
- Winter Peak: [18, 22, 23, 24, 36, 37, 360]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 9653021.69 | 9653021.69 | 0.0 | 0.0 |
| residential-cooling | 4806362.84 | 4806362.84 | 0.0 | 0.0 |
| residential-lighting | 1944733.29 | 1944733.29 | 0.0 | 0.0 |
| residential-appliances | 12888423.21 | 12888423.21 | -0.0 | -0.0 |
| residential-other | 18117907.39 | 18117907.39 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 2155723.92 | 2155723.92 | 0.0 | 0.0 |
| commercial-cooling | 14977608.44 | 14977608.44 | 0.0 | 0.0 |
| commercial-lighting | 7488599.06 | 7488599.06 | -0.0 | -0.0 |
| commercial-appliances | 13870369.28 | 13870369.28 | -0.0 | -0.0 |
| commercial-other | 30798358.73 | 30798358.73 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 199274.83 | 199274.83 | 0.0 | 0.0 |
| HDVs | 3482.17 | 3482.17 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 7665.86 | 7665.86 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 20057709.44 | 20057709.44 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.077493 | 978.1 | 8760 |
| Winter | 0.085151 | 892.32 | 864 |
| Spring | 0.096185 | 1002.5 | 2160 |
| Summer | 0.096124 | 962.81 | 3696 |
| Fall | 0.138903 | 1222.71 | 1512 |
| Summer Peak | 0.025638 | 248.01 | 360 |
| Winter Peak | 0.085442 | 804.7 | 168 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.094678 | 507.04 | 9653021.69 |
| residential-cooling | 0.153254 | 293.58 | 4806362.84 |
| residential-lighting | 0.057835 | 22.38 | 1944733.29 |
| residential-appliances | 0.074459 | 110.75 | 12888423.21 |
| residential-other | 0.094698 | 90.56 | 18117907.39 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.076294 | 111.09 | 2155723.92 |
| commercial-cooling | 0.104743 | 337.94 | 14977608.44 |
| commercial-lighting | 0.161735 | 105.51 | 7488599.06 |
| commercial-appliances | 0.091049 | 165.38 | 13870369.28 |
| commercial-other | 0.178676 | 267.91 | 30798358.73 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.063006 | 3.35 | 199274.83 |
| HDVs | 0.105135 | 0.03 | 3482.17 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.063006 | 0.13 | 7665.86 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.219181 | 392.47 | 20057709.44 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 24796.15 | 25355.11 | 0.978 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 21691.71 | 21691.71 | 1.0 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 24796.15 | 24840.95 | 0.9982 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2312.07 | 2784.87 | 0.8302 |  |
| category_peak_commercial-cooling | 5174.95 | 5761.03 | 0.8983 |  |
| category_peak_residential-heating | 6874.49 | 7475.63 | 0.9196 |  |
| category_peak_commercial-heating | 2037.87 | 2129.99 | 0.9568 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.9 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 22739.3 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 22647.1 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 23724.08 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 24184.01 | 23322.78 | 1.0369 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 18519.62 | 17478.86 | 1.0595 |  |
| winter_peak_net_load | 24184.01 | 22949.51 | 1.0538 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 842.52 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 592.57 | 438 | top 5% of LDC = top ~438 hours |
| overall | 363.68 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0633 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 36 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 23959.91 | shifted gen by -14d; peak hour 2018-01-23 09:00:00 |
| net_load_peak_shift_-7d | 23314.91 | shifted gen by -7d; peak hour 2018-02-05 08:00:00 |
| net_load_peak_shift_0d | 24191.69 | shifted gen by 0d; peak hour 2018-01-24 08:00:00 |
| net_load_peak_shift_7d | 23735.35 | shifted gen by 7d; peak hour 2018-01-19 09:00:00 |
| net_load_peak_shift_14d | 24454.99 | shifted gen by 14d; peak hour 2018-01-24 08:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| VA_total_annual_TWh | 136.97 | 128.0 | 0.0701 | EIA SEDS 2022/2024 VA total electricity consumption ~127-130 TWh; staff verify against current SEDS release |
| VA_solar_pv_annual_TWh | 17.1391 | 17.1391 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| VA_wind_annual_TWh | 6.6678 | 6.6678 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 8004.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 486.4 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 104.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 2500.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2344 | 0.2344 | 0.5474 | 0.5474 |
| solar-pv-dist | 0.1645 | 0.1645 | 0.3671 | 0.3671 |
| onshore-wind | 0.3550 | 0.3550 | 0.1951 | 0.1951 |
| offshore-wind | 0.2896 | 0.2896 | 0.2090 | 0.2090 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.063

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 23960 | 2018-01-23 09:00:00 | 12918 |
| -7 | 23315 | 2018-02-05 08:00:00 | 12918 |
| 0 | 24192 | 2018-01-24 08:00:00 | 12918 |
| 7 | 23735 | 2018-01-19 09:00:00 | 12918 |
| 14 | 24455 | 2018-01-24 08:00:00 | 12918 |

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
| efs | 20057.7 | 3298 | 2290 | 542 | 1.44 |
| flat | 20057.7 | 2290 | 2290 | 0 | 1.00 |
| cambium_residual | 20057.7 | 5447 | 2290 | 963 | 2.38 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
