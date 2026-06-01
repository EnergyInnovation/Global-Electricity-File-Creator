# Validation report - US-MI

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **100.8 TWh**
- Peak hour: **2018-01-05 11:00:00** at **16.7 GW**
- Cluster NRMSE: **0.435**

## Days per timeslice

- Winter: 120
- Spring: 64
- Summer: 99
- Fall: 65
- Summer Peak: 3
- Winter Peak: 14

## Top-5 peak days

- Summer Peak: [159, 199, 207]
- Winter Peak: [1, 4, 9, 26, 27, 34, 37, 39, 46, 47, 353, 354, 355, 360]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 6349132.47 | 6349132.47 | -0.0 | -0.0 |
| residential-cooling | 1849786.05 | 1849786.05 | -0.0 | -0.0 |
| residential-lighting | 2323385.11 | 2323385.11 | 0.0 | 0.0 |
| residential-appliances | 9629522.27 | 9629522.27 | -0.0 | -0.0 |
| residential-other | 15146453.69 | 15146453.69 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 1044290.74 | 1044290.74 | 0.0 | 0.0 |
| commercial-cooling | 6347069.17 | 6347069.17 | -0.0 | -0.0 |
| commercial-lighting | 3939683.47 | 3939683.47 | 0.0 | 0.0 |
| commercial-appliances | 5610785.46 | 5610785.46 | 0.0 | 0.0 |
| commercial-other | 20480509.96 | 20480509.96 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 209203.64 | 209203.64 | 0.0 | 0.0 |
| HDVs | 3149.96 | 3149.96 | -0.0 | -0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 27898936.52 | 27898936.52 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.091977 | 698.1 | 8760 |
| Winter | 0.09562 | 752.0 | 2880 |
| Spring | 0.12415 | 748.71 | 1536 |
| Summer | 0.100503 | 584.05 | 2376 |
| Fall | 0.137039 | 776.88 | 1560 |
| Summer Peak | 0.053087 | 359.62 | 72 |
| Winter Peak | 0.088265 | 518.06 | 336 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.220804 | 550.26 | 6349132.47 |
| residential-cooling | 0.161545 | 107.4 | 1849786.05 |
| residential-lighting | 0.077893 | 39.47 | 2323385.11 |
| residential-appliances | 0.068382 | 72.47 | 9629522.27 |
| residential-other | 0.117442 | 95.78 | 15146453.69 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.160685 | 90.05 | 1044290.74 |
| commercial-cooling | 0.121593 | 192.94 | 6347069.17 |
| commercial-lighting | 0.14425 | 51.51 | 3939683.47 |
| commercial-appliances | 0.095908 | 74.29 | 5610785.46 |
| commercial-other | 0.159055 | 167.27 | 20480509.96 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.058395 | 3.46 | 209203.64 |
| HDVs | 0.073237 | 0.02 | 3149.96 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.185905 | 496.11 | 27898936.52 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 15697.53 | 16537.97 | 0.9492 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 15288.6 | 15321.24 | 0.9979 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 15697.53 | 15823.26 | 0.9921 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 736.88 | 923.58 | 0.7979 |  |
| category_peak_commercial-cooling | 2267.49 | 2646.79 | 0.8567 |  |
| category_peak_residential-heating | 2460.34 | 3002.59 | 0.8194 |  |
| category_peak_commercial-heating | 546.67 | 681.99 | 0.8016 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.8 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 15779.59 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 14956.1 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 16115.67 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 15490.43 | 15735.63 | 0.9844 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 13923.0 | 13905.0 | 1.0013 |  |
| winter_peak_net_load | 15490.43 | 15312.98 | 1.0116 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 637.94 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 580.76 | 438 | top 5% of LDC = top ~438 hours |
| overall | 228.53 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0554 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 5 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 15964.93 | shifted gen by -14d; peak hour 2018-01-05 11:00:00 |
| net_load_peak_shift_-7d | 16030.95 | shifted gen by -7d; peak hour 2018-01-05 12:00:00 |
| net_load_peak_shift_0d | 16033.15 | shifted gen by 0d; peak hour 2018-01-26 11:00:00 |
| net_load_peak_shift_7d | 15775.25 | shifted gen by 7d; peak hour 2018-01-06 18:00:00 |
| net_load_peak_shift_14d | 16251.88 | shifted gen by 14d; peak hour 2018-01-04 18:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| MI_total_annual_TWh | 100.83 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| MI_solar_pv_annual_TWh | 2.7471 | 2.7471 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| MI_wind_annual_TWh | 10.473 | 10.473 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 1165.5 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 218.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 3240.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2399 | 0.2399 | 0.6902 | 0.6902 |
| solar-pv-dist | 0.1554 | 0.1554 | 0.4274 | 0.4274 |
| onshore-wind | 0.3689 | 0.3689 | 0.2218 | 0.2218 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.055

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 15965 | 2018-01-05 11:00:00 | 10001 |
| -7 | 16031 | 2018-01-05 12:00:00 | 10001 |
| 0 | 16033 | 2018-01-26 11:00:00 | 10001 |
| 7 | 15775 | 2018-01-06 18:00:00 | 10001 |
| 14 | 16252 | 2018-01-04 18:00:00 | 10001 |

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
| efs | 27898.9 | 4995 | 3185 | 805 | 1.57 |
| flat | 27898.9 | 3185 | 3185 | 0 | 1.00 |
| cambium_residual | 27898.9 | 7228 | 3185 | 1106 | 2.27 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
