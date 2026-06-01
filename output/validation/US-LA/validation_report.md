# Validation report - US-LA

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **95.1 TWh**
- Peak hour: **2018-07-31 13:00:00** at **15.8 GW**
- Cluster NRMSE: **0.367**

## Days per timeslice

- Winter: 71
- Spring: 95
- Summer: 92
- Fall: 73
- Summer Peak: 10
- Winter Peak: 24

## Top-5 peak days

- Summer Peak: [192, 205, 206, 212, 215, 228, 229, 233, 235, 236]
- Winter Peak: [2, 9, 10, 11, 12, 13, 16, 17, 18, 19, 23, 24, 32, 33, 37, 38, 39, 340, 352, 353, 354, 355, 356, 359]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 2873716.3 | 2873716.3 | 0.0 | 0.0 |
| residential-cooling | 5759079.72 | 5759079.72 | 0.0 | 0.0 |
| residential-lighting | 1395773.74 | 1395773.74 | 0.0 | 0.0 |
| residential-appliances | 7405131.89 | 7405131.89 | -0.0 | -0.0 |
| residential-other | 15495281.36 | 15495281.36 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 310999.41 | 310999.41 | 0.0 | 0.0 |
| commercial-cooling | 6743347.01 | 6743347.01 | -0.0 | -0.0 |
| commercial-lighting | 2501635.4 | 2501635.4 | 0.0 | 0.0 |
| commercial-appliances | 3945603.75 | 3945603.75 | 0.0 | 0.0 |
| commercial-other | 10225586.17 | 10225586.17 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 105944.1 | 105944.1 | 0.0 | 0.0 |
| HDVs | 2520.95 | 2520.95 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 38382597.71 | 38382597.71 | -0.0 | -0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.062072 | 445.51 | 8760 |
| Winter | 0.07403 | 470.93 | 1704 |
| Spring | 0.086257 | 480.28 | 2280 |
| Summer | 0.119175 | 566.86 | 2208 |
| Fall | 0.067229 | 301.46 | 1752 |
| Summer Peak | 0.033127 | 175.75 | 240 |
| Winter Peak | 0.067989 | 318.09 | 576 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.126282 | 272.33 | 2873716.3 |
| residential-cooling | 0.158893 | 320.68 | 5759079.72 |
| residential-lighting | 0.061624 | 18.26 | 1395773.74 |
| residential-appliances | 0.080208 | 70.56 | 7405131.89 |
| residential-other | 0.112195 | 85.16 | 15495281.36 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.086883 | 26.63 | 310999.41 |
| commercial-cooling | 0.117823 | 164.24 | 6743347.01 |
| commercial-lighting | 0.140937 | 31.99 | 2501635.4 |
| commercial-appliances | 0.087125 | 47.53 | 3945603.75 |
| commercial-other | 0.169148 | 79.72 | 10225586.17 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.039184 | 0.94 | 105944.1 |
| HDVs | 0.110505 | 0.02 | 2520.95 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.103429 | 285.69 | 38382597.71 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 15374.55 | 15623.9 | 0.984 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 15374.55 | 15391.7 | 0.9989 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 13509.56 | 13751.94 | 0.9824 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2578.77 | 2779.38 | 0.9278 |  |
| category_peak_commercial-cooling | 2332.55 | 2405.43 | 0.9697 |  |
| category_peak_residential-heating | 2096.52 | 2739.7 | 0.7652 |  |
| category_peak_commercial-heating | 317.92 | 423.51 | 0.7507 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 1.0 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 14982.73 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 14798.17 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 15218.57 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 14887.85 | 14793.61 | 1.0064 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 14887.85 | 14587.26 | 1.0206 |  |
| winter_peak_net_load | 13509.56 | 13550.02 | 0.997 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 316.43 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 233.17 | 438 | top 5% of LDC = top ~438 hours |
| overall | 159.43 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.1846 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 18 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 15043.12 | shifted gen by -14d; peak hour 2018-08-07 12:00:00 |
| net_load_peak_shift_-7d | 15281.69 | shifted gen by -7d; peak hour 2018-08-24 15:00:00 |
| net_load_peak_shift_0d | 14928.89 | shifted gen by 0d; peak hour 2018-08-24 15:00:00 |
| net_load_peak_shift_7d | 14843.17 | shifted gen by 7d; peak hour 2018-08-17 14:00:00 |
| net_load_peak_shift_14d | 15156.39 | shifted gen by 14d; peak hour 2018-07-25 13:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| LA_total_annual_TWh | 95.15 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| LA_solar_pv_annual_TWh | 3.1479 | 3.1479 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| LA_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 710.3 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 1018.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2666 | 0.2666 | 0.5747 | 0.5747 |
| solar-pv-dist | 0.1670 | 0.1670 | 0.3453 | 0.3453 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.185

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 15043 | 2018-08-07 12:00:00 | 10502 |
| -7 | 15282 | 2018-08-24 15:00:00 | 10502 |
| 0 | 14929 | 2018-08-24 15:00:00 | 10502 |
| 7 | 14843 | 2018-08-17 14:00:00 | 10502 |
| 14 | 15156 | 2018-07-25 13:00:00 | 10502 |

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
| efs | 38382.6 | 6028 | 4382 | 988 | 1.38 |
| flat | 38382.6 | 4382 | 4382 | 0 | 1.00 |
| cambium_residual | 38382.6 | 7862 | 4382 | 983 | 1.79 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
