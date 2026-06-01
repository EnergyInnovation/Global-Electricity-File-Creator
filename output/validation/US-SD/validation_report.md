# Validation report - US-SD

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **13.7 TWh**
- Peak hour: **2018-01-11 19:00:00** at **2.2 GW**
- Cluster NRMSE: **0.705**

## Days per timeslice

- Winter: 50
- Spring: 98
- Summer: 109
- Fall: 61
- Summer Peak: 32
- Winter Peak: 15

## Top-5 peak days

- Summer Peak: [152, 153, 154, 155, 157, 165, 171, 181, 182, 184, 186, 190, 191, 192, 193, 197, 201, 202, 205, 210, 213, 219, 226, 227, 228, 232, 233, 234, 237, 239, 240, 241]
- Winter Peak: [1, 9, 20, 21, 25, 34, 50, 310, 343, 353, 361, 362, 363, 364, 365]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 911333.53 | 911333.53 | 0.0 | 0.0 |
| residential-cooling | 354332.65 | 354332.65 | 0.0 | 0.0 |
| residential-lighting | 287524.62 | 287524.62 | 0.0 | 0.0 |
| residential-appliances | 1481043.38 | 1481043.38 | 0.0 | 0.0 |
| residential-other | 2390041.03 | 2390041.03 | -0.0 | -0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 188995.31 | 188995.31 | 0.0 | 0.0 |
| commercial-cooling | 752942.56 | 752942.56 | 0.0 | 0.0 |
| commercial-lighting | 478534.58 | 478534.58 | 0.0 | 0.0 |
| commercial-appliances | 697259.67 | 697259.67 | 0.0 | 0.0 |
| commercial-other | 2885205.16 | 2885205.16 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 23485.72 | 23485.72 | 0.0 | 0.0 |
| HDVs | 1039.89 | 1039.89 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 3286420.24 | 3286420.24 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.132375 | 130.77 | 8760 |
| Winter | 0.143865 | 134.47 | 1200 |
| Spring | 0.149767 | 148.89 | 2352 |
| Summer | 0.131797 | 125.56 | 2616 |
| Fall | 0.150487 | 135.77 | 1464 |
| Summer Peak | 0.107915 | 78.92 | 768 |
| Winter Peak | 0.150026 | 128.29 | 360 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.230662 | 82.32 | 911333.53 |
| residential-cooling | 0.140611 | 21.21 | 354332.65 |
| residential-lighting | 0.072313 | 4.54 | 287524.62 |
| residential-appliances | 0.079206 | 15.45 | 1481043.38 |
| residential-other | 0.111037 | 13.84 | 2390041.03 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.183036 | 17.41 | 188995.31 |
| commercial-cooling | 0.111659 | 22.19 | 752942.56 |
| commercial-lighting | 0.152424 | 7.4 | 478534.58 |
| commercial-appliances | 0.099866 | 9.55 | 697259.67 |
| commercial-other | 0.189928 | 23.68 | 2885205.16 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.066001 | 0.41 | 23485.72 |
| HDVs | 0.086285 | 0.01 | 1039.89 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.183439 | 58.9 | 3286420.24 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 2013.12 | 2205.96 | 0.9126 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 1835.34 | 1844.34 | 0.9951 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 2013.12 | 2015.56 | 0.9988 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 141.35 | 218.38 | 0.6473 |  |
| category_peak_commercial-cooling | 238.55 | 353.31 | 0.6752 |  |
| category_peak_residential-heating | 312.95 | 417.18 | 0.7501 |  |
| category_peak_commercial-heating | 84.49 | 114.75 | 0.7363 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.18 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 2098.36 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 1807.16 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 2141.5 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 1958.08 | 1984.92 | 0.9865 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 1782.04 | 1661.82 | 1.0723 |  |
| winter_peak_net_load | 1958.08 | 1753.34 | 1.1168 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 198.49 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 211.64 | 438 | top 5% of LDC = top ~438 hours |
| overall | 80.77 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.1584 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 11 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 2004.25 | shifted gen by -14d; peak hour 2018-01-09 11:00:00 |
| net_load_peak_shift_-7d | 1987.62 | shifted gen by -7d; peak hour 2018-12-20 20:00:00 |
| net_load_peak_shift_0d | 2055.05 | shifted gen by 0d; peak hour 2018-12-19 11:00:00 |
| net_load_peak_shift_7d | 1993.82 | shifted gen by 7d; peak hour 2018-01-03 19:00:00 |
| net_load_peak_shift_14d | 2142.29 | shifted gen by 14d; peak hour 2018-01-10 19:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| SD_total_annual_TWh | 13.74 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| SD_solar_pv_annual_TWh | 0.1355 | 0.1355 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| SD_wind_annual_TWh | 10.5781 | 10.5781 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 1.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 87.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 2767.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2438 | 0.2438 | 0.6558 | 0.6558 |
| solar-pv-dist | 0.1731 | 0.1731 | 0.4657 | 0.4657 |
| onshore-wind | 0.4364 | 0.4364 | 0.2579 | 0.2579 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.158

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 2004 | 2018-01-09 11:00:00 | 345 |
| -7 | 1988 | 2018-12-20 20:00:00 | 345 |
| 0 | 2055 | 2018-12-19 11:00:00 | 345 |
| 7 | 1994 | 2018-01-03 19:00:00 | 345 |
| 14 | 2142 | 2018-01-10 19:00:00 | 345 |

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
| efs | 3286.4 | 568 | 375 | 82 | 1.51 |
| flat | 3286.4 | 375 | 375 | 0 | 1.00 |
| cambium_residual | 3286.4 | 850 | 375 | 155 | 2.27 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
