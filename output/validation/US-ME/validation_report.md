# Validation report - US-ME

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **11.9 TWh**
- Peak hour: **2018-02-06 18:00:00** at **2.0 GW**
- Cluster NRMSE: **0.627**

## Days per timeslice

- Winter: 75
- Spring: 69
- Summer: 43
- Fall: 145
- Summer Peak: 16
- Winter Peak: 17

## Top-5 peak days

- Summer Peak: [152, 159, 160, 163, 174, 177, 184, 186, 209, 212, 222, 223, 228, 233, 234, 235]
- Winter Peak: [12, 18, 22, 23, 27, 32, 33, 34, 47, 324, 333, 342, 344, 345, 352, 356, 362]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 766403.87 | 766403.87 | 0.0 | 0.0 |
| residential-cooling | 83088.22 | 83088.22 | 0.0 | 0.0 |
| residential-lighting | 450642.44 | 450642.44 | -0.0 | -0.0 |
| residential-appliances | 1703314.77 | 1703314.77 | -0.0 | -0.0 |
| residential-other | 1969264.36 | 1969264.36 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 119979.48 | 119979.48 | 0.0 | 0.0 |
| commercial-cooling | 441825.91 | 441825.91 | -0.0 | -0.0 |
| commercial-lighting | 349560.38 | 349560.38 | 0.0 | 0.0 |
| commercial-appliances | 817933.76 | 817933.76 | -0.0 | -0.0 |
| commercial-other | 2561474.21 | 2561474.21 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 31413.8 | 31413.8 | 0.0 | 0.0 |
| HDVs | 612.6 | 612.6 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 2616823.53 | 2616823.53 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.112603 | 108.85 | 8760 |
| Winter | 0.115166 | 110.36 | 1800 |
| Spring | 0.120742 | 117.61 | 1656 |
| Summer | 0.120894 | 98.5 | 1032 |
| Fall | 0.13055 | 117.41 | 3480 |
| Summer Peak | 0.063993 | 34.74 | 384 |
| Winter Peak | 0.101297 | 89.61 | 408 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.190491 | 66.9 | 766403.87 |
| residential-cooling | 0.176544 | 4.18 | 83088.22 |
| residential-lighting | 0.072866 | 7.1 | 450642.44 |
| residential-appliances | 0.086408 | 17.27 | 1703314.77 |
| residential-other | 0.11622 | 12.16 | 1969264.36 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.156133 | 10.02 | 119979.48 |
| commercial-cooling | 0.093537 | 10.37 | 441825.91 |
| commercial-lighting | 0.141488 | 5.24 | 349560.38 |
| commercial-appliances | 0.083922 | 9.19 | 817933.76 |
| commercial-other | 0.175191 | 22.6 | 2561474.21 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.068408 | 0.6 | 31413.8 |
| HDVs | 0.156479 | 0.02 | 612.6 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.227437 | 54.96 | 2616823.53 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 1890.8 | 2027.32 | 0.9327 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 1565.48 | 1586.0 | 0.9871 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 1890.8 | 1891.58 | 0.9996 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 18.55 | 30.26 | 0.6131 |  |
| category_peak_commercial-cooling | 134.28 | 189.96 | 0.7069 |  |
| category_peak_residential-heating | 249.29 | 409.67 | 0.6085 |  |
| category_peak_commercial-heating | 55.33 | 76.81 | 0.7204 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.27 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 1923.75 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 1695.67 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 1959.34 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 1881.6 | 1880.95 | 1.0003 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 1492.95 | 1396.0 | 1.0694 |  |
| winter_peak_net_load | 1881.6 | 1729.15 | 1.0882 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 126.49 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 148.31 | 438 | top 5% of LDC = top ~438 hours |
| overall | 52.96 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0012 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 44 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 1938.7 | shifted gen by -14d; peak hour 2018-02-02 18:00:00 |
| net_load_peak_shift_-7d | 1906.98 | shifted gen by -7d; peak hour 2018-01-20 18:00:00 |
| net_load_peak_shift_0d | 1980.78 | shifted gen by 0d; peak hour 2018-01-27 18:00:00 |
| net_load_peak_shift_7d | 1934.9 | shifted gen by 7d; peak hour 2018-02-03 18:00:00 |
| net_load_peak_shift_14d | 1928.84 | shifted gen by 14d; peak hour 2018-01-26 18:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| ME_total_annual_TWh | 11.91 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| ME_solar_pv_annual_TWh | 0.8785 | 0.8785 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| ME_wind_annual_TWh | 3.2755 | 3.2755 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 391.5 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 116.4 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 1009.5 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 12.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2112 | 0.2112 | 0.5224 | 0.5224 |
| solar-pv-dist | 0.1514 | 0.1514 | 0.3399 | 0.3399 |
| onshore-wind | 0.3651 | 0.3651 | 0.2411 | 0.2411 |
| offshore-wind | 0.4424 | 0.4424 | 0.3613 | 0.3613 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.001

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 1939 | 2018-02-02 18:00:00 | 886 |
| -7 | 1907 | 2018-01-20 18:00:00 | 886 |
| 0 | 1981 | 2018-01-27 18:00:00 | 886 |
| 7 | 1935 | 2018-02-03 18:00:00 | 886 |
| 14 | 1929 | 2018-01-26 18:00:00 | 886 |

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
| efs | 2616.8 | 442 | 299 | 76 | 1.48 |
| flat | 2616.8 | 299 | 299 | 0 | 1.00 |
| cambium_residual | 2616.8 | 588 | 299 | 75 | 1.97 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
