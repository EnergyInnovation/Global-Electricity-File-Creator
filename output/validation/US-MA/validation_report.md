# Validation report - US-MA

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **54.2 TWh**
- Peak hour: **2018-01-23 10:00:00** at **9.9 GW**
- Cluster NRMSE: **0.591**

## Days per timeslice

- Winter: 71
- Spring: 101
- Summer: 57
- Fall: 104
- Summer Peak: 18
- Winter Peak: 14

## Top-5 peak days

- Summer Peak: [152, 158, 159, 166, 172, 178, 184, 185, 187, 190, 201, 212, 214, 215, 228, 229, 232, 233]
- Winter Peak: [5, 9, 10, 11, 12, 18, 22, 23, 24, 39, 40, 46, 47, 340]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 3311040.45 | 3311040.45 | 0.0 | 0.0 |
| residential-cooling | 914745.02 | 914745.02 | -0.0 | -0.0 |
| residential-lighting | 1628141.85 | 1628141.85 | 0.0 | 0.0 |
| residential-appliances | 6686216.3 | 6686216.3 | 0.0 | 0.0 |
| residential-other | 8386949.0 | 8386949.0 | -0.0 | -0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 550498.24 | 550498.24 | -0.0 | -0.0 |
| commercial-cooling | 3395164.13 | 3395164.13 | 0.0 | 0.0 |
| commercial-lighting | 2148279.6 | 2148279.6 | 0.0 | 0.0 |
| commercial-appliances | 4604718.64 | 4604718.64 | 0.0 | 0.0 |
| commercial-other | 15677344.67 | 15677344.67 | -0.0 | -0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 123592.6 | 123592.6 | 0.0 | 0.0 |
| HDVs | 1466.39 | 1466.39 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 261580.78 | 261580.78 | -0.0 | -0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 6503768.57 | 6503768.57 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.071062 | 340.69 | 8760 |
| Winter | 0.080637 | 327.29 | 1704 |
| Spring | 0.099961 | 392.39 | 2424 |
| Summer | 0.117641 | 375.31 | 1368 |
| Fall | 0.098419 | 326.21 | 2496 |
| Summer Peak | 0.048503 | 167.3 | 432 |
| Winter Peak | 0.060609 | 225.21 | 336 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.116183 | 184.58 | 3311040.45 |
| residential-cooling | 0.15106 | 53.55 | 914745.02 |
| residential-lighting | 0.064317 | 20.61 | 1628141.85 |
| residential-appliances | 0.072562 | 52.6 | 6686216.3 |
| residential-other | 0.097506 | 41.51 | 8386949.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.082421 | 31.82 | 550498.24 |
| commercial-cooling | 0.10237 | 78.82 | 3395164.13 |
| commercial-lighting | 0.147565 | 29.69 | 2148279.6 |
| commercial-appliances | 0.079734 | 46.28 | 4604718.64 |
| commercial-other | 0.171009 | 132.84 | 15677344.67 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.058794 | 1.98 | 123592.6 |
| HDVs | 0.086141 | 0.01 | 1466.39 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.058794 | 4.2 | 261580.78 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.221676 | 138.55 | 6503768.57 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 9245.65 | 9537.09 | 0.9694 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 7915.03 | 7915.31 | 1.0 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 9245.65 | 9262.73 | 0.9982 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 361.43 | 526.27 | 0.6868 |  |
| category_peak_commercial-cooling | 1103.19 | 1412.49 | 0.781 |  |
| category_peak_residential-heating | 1536.67 | 1854.69 | 0.8285 |  |
| category_peak_commercial-heating | 393.75 | 452.99 | 0.8692 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.95 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 8896.23 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 8750.46 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 9147.41 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 8872.25 | 8790.69 | 1.0093 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 7238.89 | 6830.52 | 1.0598 |  |
| winter_peak_net_load | 8872.25 | 8491.54 | 1.0448 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 194.31 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 217.69 | 438 | top 5% of LDC = top ~438 hours |
| overall | 119.26 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0376 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 23 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 9158.73 | shifted gen by -14d; peak hour 2018-01-23 18:00:00 |
| net_load_peak_shift_-7d | 8660.61 | shifted gen by -7d; peak hour 2018-02-02 18:00:00 |
| net_load_peak_shift_0d | 8967.53 | shifted gen by 0d; peak hour 2018-01-23 18:00:00 |
| net_load_peak_shift_7d | 8975.53 | shifted gen by 7d; peak hour 2018-01-17 18:00:00 |
| net_load_peak_shift_14d | 8957.5 | shifted gen by 14d; peak hour 2018-01-23 17:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| MA_total_annual_TWh | 54.19 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| MA_solar_pv_annual_TWh | 5.5397 | 5.5397 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| MA_wind_annual_TWh | 3.4499 | 3.4499 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 941.3 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 2860.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 122.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 800.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2136 | 0.2136 | 0.4899 | 0.4899 |
| solar-pv-dist | 0.1508 | 0.1508 | 0.3396 | 0.3396 |
| onshore-wind | 0.3519 | 0.3519 | 0.2226 | 0.2226 |
| offshore-wind | 0.4386 | 0.4386 | 0.3250 | 0.3250 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.038

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 9159 | 2018-01-23 18:00:00 | 5160 |
| -7 | 8661 | 2018-02-02 18:00:00 | 5160 |
| 0 | 8968 | 2018-01-23 18:00:00 | 5160 |
| 7 | 8976 | 2018-01-17 18:00:00 | 5160 |
| 14 | 8958 | 2018-01-23 17:00:00 | 5160 |

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
| efs | 6503.8 | 1153 | 742 | 208 | 1.55 |
| flat | 6503.8 | 742 | 742 | 0 | 1.00 |
| cambium_residual | 6503.8 | 2633 | 742 | 481 | 3.55 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
