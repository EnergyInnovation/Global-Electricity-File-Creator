# Validation report - US-NM

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **27.1 TWh**
- Peak hour: **2018-06-29 13:00:00** at **4.3 GW**
- Cluster NRMSE: **0.892**

## Days per timeslice

- Winter: 37
- Spring: 88
- Summer: 126
- Fall: 72
- Summer Peak: 23
- Winter Peak: 19

## Top-5 peak days

- Summer Peak: [158, 166, 177, 178, 179, 180, 191, 192, 193, 194, 195, 205, 206, 212, 213, 221, 222, 228, 230, 233, 241, 242, 243]
- Winter Peak: [2, 3, 5, 10, 26, 30, 32, 37, 47, 305, 309, 311, 312, 318, 325, 340, 342, 349, 361]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 1014128.96 | 1014128.96 | 0.0 | 0.0 |
| residential-cooling | 753044.84 | 753044.84 | 0.0 | 0.0 |
| residential-lighting | 514910.9 | 514910.9 | 0.0 | 0.0 |
| residential-appliances | 2248174.09 | 2248174.09 | 0.0 | 0.0 |
| residential-other | 3192646.54 | 3192646.54 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 189228.6 | 189228.6 | 0.0 | 0.0 |
| commercial-cooling | 1497013.48 | 1497013.48 | 0.0 | 0.0 |
| commercial-lighting | 797356.39 | 797356.39 | 0.0 | 0.0 |
| commercial-appliances | 1380293.08 | 1380293.08 | 0.0 | 0.0 |
| commercial-other | 5524237.98 | 5524237.98 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 50368.79 | 50368.79 | 0.0 | 0.0 |
| HDVs | 2225.49 | 2225.49 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 9924673.77 | 9924673.77 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.139452 | 261.55 | 8760 |
| Winter | 0.169583 | 312.97 | 888 |
| Spring | 0.172101 | 319.82 | 2112 |
| Summer | 0.154174 | 285.19 | 3024 |
| Fall | 0.131293 | 218.42 | 1728 |
| Summer Peak | 0.048301 | 62.19 | 552 |
| Winter Peak | 0.105292 | 139.49 | 456 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.173833 | 97.57 | 1014128.96 |
| residential-cooling | 0.156693 | 51.09 | 753044.84 |
| residential-lighting | 0.067092 | 7.54 | 514910.9 |
| residential-appliances | 0.075841 | 19.8 | 2248174.09 |
| residential-other | 0.116381 | 20.1 | 3192646.54 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.11491 | 16.86 | 189228.6 |
| commercial-cooling | 0.112768 | 35.59 | 1497013.48 |
| commercial-lighting | 0.159472 | 11.81 | 797356.39 |
| commercial-appliances | 0.111489 | 20.36 | 1380293.08 |
| commercial-other | 0.194645 | 52.25 | 5524237.98 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.069884 | 0.95 | 50368.79 |
| HDVs | 0.131231 | 0.03 | 2225.49 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.208907 | 215.22 | 9924673.77 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 4125.41 | 4276.75 | 0.9646 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 4125.41 | 4129.92 | 0.9989 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 3803.2 | 3832.21 | 0.9924 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 406.71 | 479.59 | 0.848 |  |
| category_peak_commercial-cooling | 496.34 | 565.46 | 0.8778 |  |
| category_peak_residential-heating | 475.88 | 726.24 | 0.6553 |  |
| category_peak_commercial-heating | 147.9 | 200.92 | 0.7362 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.46 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 4122.69 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 3808.76 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 4181.03 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 3599.18 | 3545.91 | 1.015 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 3599.18 | 2979.42 | 1.208 |  |
| winter_peak_net_load | 3583.11 | 2951.73 | 1.2139 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 103.35 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 202.56 | 438 | top 5% of LDC = top ~438 hours |
| overall | 160.5 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0852 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 201 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 3712.33 | shifted gen by -14d; peak hour 2018-12-19 20:00:00 |
| net_load_peak_shift_-7d | 3631.19 | shifted gen by -7d; peak hour 2018-12-26 20:00:00 |
| net_load_peak_shift_0d | 3676.4 | shifted gen by 0d; peak hour 2018-01-02 20:00:00 |
| net_load_peak_shift_7d | 3680.78 | shifted gen by 7d; peak hour 2018-07-31 16:00:00 |
| net_load_peak_shift_14d | 3977.27 | shifted gen by 14d; peak hour 2018-01-16 20:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| NM_total_annual_TWh | 27.09 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| NM_solar_pv_annual_TWh | 4.2183 | 4.2183 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| NM_wind_annual_TWh | 15.3403 | 15.3403 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 1338.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 378.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 4409.4 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.3016 | 0.3016 | 0.6376 | 0.6376 |
| solar-pv-dist | 0.2059 | 0.2059 | 0.4219 | 0.4219 |
| onshore-wind | 0.3971 | 0.3971 | 0.2350 | 0.2350 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.085

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 3712 | 2018-12-19 20:00:00 | 860 |
| -7 | 3631 | 2018-12-26 20:00:00 | 860 |
| 0 | 3676 | 2018-01-02 20:00:00 | 860 |
| 7 | 3681 | 2018-07-31 16:00:00 | 860 |
| 14 | 3977 | 2018-01-16 20:00:00 | 860 |

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
| efs | 9924.7 | 1726 | 1133 | 294 | 1.52 |
| flat | 9924.7 | 1133 | 1133 | 0 | 1.00 |
| cambium_residual | 9924.7 | 2102 | 1133 | 229 | 1.86 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
