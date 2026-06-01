# Validation report - US-CT

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **28.8 TWh**
- Peak hour: **2018-01-23 10:00:00** at **5.2 GW**
- Cluster NRMSE: **0.450**

## Days per timeslice

- Winter: 63
- Spring: 60
- Summer: 68
- Fall: 161
- Summer Peak: 6
- Winter Peak: 7

## Top-5 peak days

- Summer Peak: [172, 198, 214, 215, 228, 229]
- Winter Peak: [18, 22, 23, 24, 26, 27, 45]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 2077939.33 | 2077939.33 | 0.0 | 0.0 |
| residential-cooling | 659943.14 | 659943.14 | 0.0 | 0.0 |
| residential-lighting | 1032350.53 | 1032350.53 | 0.0 | 0.0 |
| residential-appliances | 4654613.13 | 4654613.13 | -0.0 | -0.0 |
| residential-other | 5398771.98 | 5398771.98 | -0.0 | -0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 238065.06 | 238065.06 | 0.0 | 0.0 |
| commercial-cooling | 1594378.66 | 1594378.66 | 0.0 | 0.0 |
| commercial-lighting | 958786.64 | 958786.64 | 0.0 | 0.0 |
| commercial-appliances | 2243528.72 | 2243528.72 | 0.0 | 0.0 |
| commercial-other | 7025967.17 | 7025967.17 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 68431.29 | 68431.29 | 0.0 | 0.0 |
| HDVs | 990.31 | 990.31 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 2863662.81 | 2863662.81 | -0.0 | -0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.066842 | 169.14 | 8760 |
| Winter | 0.087017 | 186.15 | 1512 |
| Spring | 0.098807 | 206.69 | 1440 |
| Summer | 0.102816 | 178.74 | 1632 |
| Fall | 0.088919 | 150.45 | 3864 |
| Summer Peak | 0.028824 | 50.27 | 144 |
| Winter Peak | 0.066897 | 132.74 | 168 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.099651 | 98.86 | 2077939.33 |
| residential-cooling | 0.137914 | 38.96 | 659943.14 |
| residential-lighting | 0.060032 | 12.17 | 1032350.53 |
| residential-appliances | 0.064536 | 34.4 | 4654613.13 |
| residential-other | 0.08343 | 24.36 | 5398771.98 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.078228 | 11.39 | 238065.06 |
| commercial-cooling | 0.087713 | 35.5 | 1594378.66 |
| commercial-lighting | 0.153681 | 13.36 | 958786.64 |
| commercial-appliances | 0.076605 | 22.49 | 2243528.72 |
| commercial-other | 0.184926 | 60.26 | 7025967.17 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.061819 | 1.27 | 68431.29 |
| HDVs | 0.112391 | 0.01 | 990.31 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.214412 | 69.64 | 2863662.81 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 5011.96 | 5106.95 | 0.9814 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 4250.47 | 4250.47 | 1.0 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 5011.96 | 5053.02 | 0.9919 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 360.9 | 395.59 | 0.9123 |  |
| category_peak_commercial-cooling | 659.79 | 705.14 | 0.9357 |  |
| category_peak_residential-heating | 1066.2 | 1248.02 | 0.8543 |  |
| category_peak_commercial-heating | 168.7 | 192.16 | 0.8779 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.96 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 4794.87 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 4707.8 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 4916.28 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 5000.16 | 5054.49 | 0.9893 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 4021.42 | 3886.87 | 1.0346 |  |
| winter_peak_net_load | 5000.16 | 4988.91 | 1.0023 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 132.84 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 120.44 | 438 | top 5% of LDC = top ~438 hours |
| overall | 57.11 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0409 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 22 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 5166.7 | shifted gen by -14d; peak hour 2018-01-23 18:00:00 |
| net_load_peak_shift_-7d | 5155.21 | shifted gen by -7d; peak hour 2018-01-18 18:00:00 |
| net_load_peak_shift_0d | 5162.4 | shifted gen by 0d; peak hour 2018-01-23 18:00:00 |
| net_load_peak_shift_7d | 5152.71 | shifted gen by 7d; peak hour 2018-01-18 18:00:00 |
| net_load_peak_shift_14d | 5153.9 | shifted gen by 14d; peak hour 2018-01-23 18:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| CT_total_annual_TWh | 28.82 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| CT_solar_pv_annual_TWh | 3.0779 | 3.0779 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| CT_wind_annual_TWh | 0.1238 | 0.1238 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 1029.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 805.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 35.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2212 | 0.2212 | 0.5289 | 0.5289 |
| solar-pv-dist | 0.1534 | 0.1534 | 0.3532 | 0.3532 |
| onshore-wind | 0.3946 | 0.3946 | 0.2133 | 0.2133 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.041

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 5167 | 2018-01-23 18:00:00 | 2924 |
| -7 | 5155 | 2018-01-18 18:00:00 | 2924 |
| 0 | 5162 | 2018-01-23 18:00:00 | 2924 |
| 7 | 5153 | 2018-01-18 18:00:00 | 2924 |
| 14 | 5154 | 2018-01-23 18:00:00 | 2924 |

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
| efs | 2863.7 | 544 | 327 | 92 | 1.66 |
| flat | 2863.7 | 327 | 327 | 0 | 1.00 |
| cambium_residual | 2863.7 | 327 | 327 | 0 | 1.00 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
