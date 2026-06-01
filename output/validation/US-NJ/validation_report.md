# Validation report - US-NJ

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **78.0 TWh**
- Peak hour: **2018-07-18 12:00:00** at **14.7 GW**
- Cluster NRMSE: **0.542**

## Days per timeslice

- Winter: 64
- Spring: 71
- Summer: 82
- Fall: 135
- Summer Peak: 8
- Winter Peak: 5

## Top-5 peak days

- Summer Peak: [197, 198, 199, 202, 214, 215, 222, 233]
- Winter Peak: [10, 17, 18, 22, 23]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 4649166.18 | 4649166.18 | 0.0 | 0.0 |
| residential-cooling | 3974262.31 | 3974262.31 | 0.0 | 0.0 |
| residential-lighting | 2205343.79 | 2205343.79 | 0.0 | 0.0 |
| residential-appliances | 9267415.01 | 9267415.01 | 0.0 | 0.0 |
| residential-other | 11427485.35 | 11427485.35 | -0.0 | -0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 886998.83 | 886998.83 | 0.0 | 0.0 |
| commercial-cooling | 8263599.06 | 8263599.06 | 0.0 | 0.0 |
| commercial-lighting | 4395134.82 | 4395134.82 | 0.0 | 0.0 |
| commercial-appliances | 6135052.75 | 6135052.75 | -0.0 | -0.0 |
| commercial-other | 19500468.93 | 19500468.93 | -0.0 | -0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 173754.65 | 173754.65 | -0.0 | -0.0 |
| HDVs | 2386.35 | 2386.35 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 422169.85 | 422169.85 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 6680847.25 | 6680847.25 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.084117 | 626.62 | 8760 |
| Winter | 0.082846 | 552.91 | 1536 |
| Spring | 0.098496 | 640.55 | 1704 |
| Summer | 0.127653 | 662.79 | 1968 |
| Fall | 0.099238 | 644.41 | 3240 |
| Summer Peak | 0.06511 | 490.01 | 192 |
| Winter Peak | 0.08879 | 517.57 | 120 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.123005 | 322.78 | 4649166.18 |
| residential-cooling | 0.147955 | 293.25 | 3974262.31 |
| residential-lighting | 0.068712 | 30.34 | 2205343.79 |
| residential-appliances | 0.069978 | 68.8 | 9267415.01 |
| residential-other | 0.112278 | 65.96 | 11427485.35 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.09154 | 60.22 | 886998.83 |
| commercial-cooling | 0.110053 | 238.11 | 8263599.06 |
| commercial-lighting | 0.166307 | 70.0 | 4395134.82 |
| commercial-appliances | 0.090738 | 78.5 | 6135052.75 |
| commercial-other | 0.196897 | 207.74 | 19500468.93 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.067889 | 3.32 | 173754.65 |
| HDVs | 0.080199 | 0.02 | 2386.35 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.067889 | 8.07 | 422169.85 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.202487 | 158.68 | 6680847.25 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 13816.7 | 14353.76 | 0.9626 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 13522.3 | 13550.97 | 0.9979 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 13816.7 | 13820.07 | 0.9998 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2390.09 | 2641.02 | 0.905 |  |
| category_peak_commercial-cooling | 3280.28 | 3577.87 | 0.9168 |  |
| category_peak_residential-heating | 2967.95 | 3265.81 | 0.9088 |  |
| category_peak_commercial-heating | 804.23 | 861.61 | 0.9334 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.64 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 13157.35 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 12438.69 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 13662.97 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 13220.14 | 12738.09 | 1.0378 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 12440.3 | 11598.94 | 1.0725 |  |
| winter_peak_net_load | 13220.14 | 12669.2 | 1.0435 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 407.66 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 610.36 | 438 | top 5% of LDC = top ~438 hours |
| overall | 266.58 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0923 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 18 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 13818.01 | shifted gen by -14d; peak hour 2018-01-17 17:00:00 |
| net_load_peak_shift_-7d | 13569.33 | shifted gen by -7d; peak hour 2018-01-18 17:00:00 |
| net_load_peak_shift_0d | 12921.01 | shifted gen by 0d; peak hour 2018-01-18 09:00:00 |
| net_load_peak_shift_7d | 13938.11 | shifted gen by 7d; peak hour 2018-01-17 17:00:00 |
| net_load_peak_shift_14d | 12883.91 | shifted gen by 14d; peak hour 2018-01-17 17:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| NJ_total_annual_TWh | 77.98 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| NJ_solar_pv_annual_TWh | 8.8271 | 8.8271 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| NJ_wind_annual_TWh | 3.8892 | 3.8892 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 2531.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 2818.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 7.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 1100.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2272 | 0.2272 | 0.5371 | 0.5371 |
| solar-pv-dist | 0.1534 | 0.1534 | 0.3398 | 0.3398 |
| onshore-wind | 0.2447 | 0.2447 | 0.1661 | 0.1661 |
| offshore-wind | 0.4019 | 0.4019 | 0.2924 | 0.2924 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.092

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 13818 | 2018-01-17 17:00:00 | 7451 |
| -7 | 13569 | 2018-01-18 17:00:00 | 7451 |
| 0 | 12921 | 2018-01-18 09:00:00 | 7451 |
| 7 | 13938 | 2018-01-17 17:00:00 | 7451 |
| 14 | 12884 | 2018-01-17 17:00:00 | 7451 |

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
| efs | 6680.8 | 1169 | 763 | 203 | 1.53 |
| flat | 6680.8 | 763 | 763 | 0 | 1.00 |
| cambium_residual | 6680.8 | 2361 | 763 | 355 | 3.10 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
