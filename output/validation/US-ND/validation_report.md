# Validation report - US-ND

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **25.4 TWh**
- Peak hour: **2018-07-18 13:00:00** at **4.2 GW**
- Cluster NRMSE: **0.728**

## Days per timeslice

- Winter: 93
- Spring: 43
- Summer: 113
- Fall: 65
- Summer Peak: 30
- Winter Peak: 21

## Top-5 peak days

- Summer Peak: [152, 153, 155, 156, 157, 184, 186, 188, 190, 191, 192, 193, 196, 199, 200, 201, 205, 206, 210, 213, 216, 219, 220, 222, 226, 227, 233, 234, 237, 241]
- Winter Peak: [13, 17, 18, 24, 34, 35, 39, 42, 45, 59, 305, 310, 335, 349, 352, 353, 359, 360, 362, 363, 365]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 1020108.44 | 1020108.44 | 0.0 | 0.0 |
| residential-cooling | 196244.14 | 196244.14 | 0.0 | 0.0 |
| residential-lighting | 285773.45 | 285773.45 | 0.0 | 0.0 |
| residential-appliances | 1470152.4 | 1470152.4 | 0.0 | 0.0 |
| residential-other | 2380697.54 | 2380697.54 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 381301.29 | 381301.29 | 0.0 | 0.0 |
| commercial-cooling | 1099425.56 | 1099425.56 | 0.0 | 0.0 |
| commercial-lighting | 827866.35 | 827866.35 | 0.0 | 0.0 |
| commercial-appliances | 1206286.64 | 1206286.64 | 0.0 | 0.0 |
| commercial-other | 4991617.82 | 4991617.82 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 18679.26 | 18679.26 | 0.0 | 0.0 |
| HDVs | 883.81 | 883.81 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 11534827.26 | 11534827.26 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.124064 | 225.68 | 8760 |
| Winter | 0.169097 | 252.45 | 2232 |
| Spring | 0.105939 | 160.6 | 1032 |
| Summer | 0.132904 | 228.18 | 2712 |
| Fall | 0.151282 | 275.32 | 1560 |
| Summer Peak | 0.11794 | 165.0 | 720 |
| Winter Peak | 0.146716 | 159.99 | 504 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.250482 | 90.3 | 1020108.44 |
| residential-cooling | 0.128088 | 9.66 | 196244.14 |
| residential-lighting | 0.075499 | 4.68 | 285773.45 |
| residential-appliances | 0.087137 | 16.84 | 1470152.4 |
| residential-other | 0.107647 | 13.51 | 2380697.54 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.204325 | 34.6 | 381301.29 |
| commercial-cooling | 0.095638 | 26.41 | 1099425.56 |
| commercial-lighting | 0.157596 | 13.97 | 827866.35 |
| commercial-appliances | 0.107614 | 18.03 | 1206286.64 |
| commercial-other | 0.187307 | 49.35 | 4991617.82 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.058924 | 0.31 | 18679.26 |
| HDVs | 0.169156 | 0.01 | 883.81 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.163098 | 228.08 | 11534827.26 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 3746.68 | 4162.31 | 0.9001 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 3746.68 | 3767.33 | 0.9945 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 3279.66 | 3334.32 | 0.9836 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 73.98 | 103.86 | 0.7123 |  |
| category_peak_commercial-cooling | 356.48 | 490.48 | 0.7268 |  |
| category_peak_residential-heating | 339.48 | 443.57 | 0.7653 |  |
| category_peak_commercial-heating | 147.04 | 205.14 | 0.7168 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.32 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 3927.99 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 3443.07 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 4020.57 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 3689.88 | 3849.94 | 0.9584 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 3689.88 | 3393.29 | 1.0874 |  |
| winter_peak_net_load | 3181.11 | 2895.9 | 1.0985 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 301.88 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 261.49 | 438 | top 5% of LDC = top ~438 hours |
| overall | 131.48 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | nan | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 30 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 4027.6 | shifted gen by -14d; peak hour 2018-07-18 14:00:00 |
| net_load_peak_shift_-7d | 4008.28 | shifted gen by -7d; peak hour 2018-07-03 12:00:00 |
| net_load_peak_shift_0d | 3906.75 | shifted gen by 0d; peak hour 2018-07-10 12:00:00 |
| net_load_peak_shift_7d | 4153.89 | shifted gen by 7d; peak hour 2018-07-18 13:00:00 |
| net_load_peak_shift_14d | 4092.64 | shifted gen by 14d; peak hour 2018-07-24 13:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| ND_total_annual_TWh | 25.41 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| ND_solar_pv_annual_TWh | 0.1115 | 0.1115 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| ND_wind_annual_TWh | 16.3631 | 16.3631 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 82.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 4727.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| solar-pv-dist | 0.1548 | 0.1548 | 0.4565 | 0.4565 |
| onshore-wind | 0.3951 | 0.3951 | 0.2504 | 0.2504 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** nan

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 4028 | 2018-07-18 14:00:00 | 1020 |
| -7 | 4008 | 2018-07-03 12:00:00 | 1020 |
| 0 | 3907 | 2018-07-10 12:00:00 | 1020 |
| 7 | 4154 | 2018-07-18 13:00:00 | 1020 |
| 14 | 4093 | 2018-07-24 13:00:00 | 1020 |

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
| efs | 11534.8 | 2388 | 1317 | 353 | 1.81 |
| flat | 11534.8 | 1317 | 1317 | 0 | 1.00 |
| cambium_residual | 11534.8 | 2785 | 1317 | 508 | 2.12 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
