# Validation report - US-OK

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **69.5 TWh**
- Peak hour: **2018-07-19 13:00:00** at **11.9 GW**
- Cluster NRMSE: **0.793**

## Days per timeslice

- Winter: 83
- Spring: 108
- Summer: 61
- Fall: 89
- Summer Peak: 8
- Winter Peak: 16

## Top-5 peak days

- Summer Peak: [157, 191, 193, 209, 219, 227, 240, 242]
- Winter Peak: [3, 5, 10, 11, 27, 32, 40, 41, 53, 318, 325, 331, 343, 346, 352, 354]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 3710741.5 | 3710741.5 | 0.0 | 0.0 |
| residential-cooling | 3324856.39 | 3324856.39 | 0.0 | 0.0 |
| residential-lighting | 1078138.92 | 1078138.92 | 0.0 | 0.0 |
| residential-appliances | 5704021.1 | 5704021.1 | 0.0 | 0.0 |
| residential-other | 12067878.08 | 12067878.08 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 630571.51 | 630571.51 | 0.0 | 0.0 |
| commercial-cooling | 5516822.98 | 5516822.98 | 0.0 | 0.0 |
| commercial-lighting | 2432793.08 | 2432793.08 | 0.0 | 0.0 |
| commercial-appliances | 3837719.81 | 3837719.81 | 0.0 | 0.0 |
| commercial-other | 9946160.61 | 9946160.61 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 91695.01 | 91695.01 | 0.0 | 0.0 |
| HDVs | 3520.85 | 3520.85 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 21161349.3 | 21161349.3 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.130452 | 756.07 | 8760 |
| Winter | 0.140528 | 787.34 | 1992 |
| Spring | 0.137052 | 772.46 | 2592 |
| Summer | 0.135459 | 714.52 | 1464 |
| Fall | 0.146135 | 817.96 | 2136 |
| Summer Peak | 0.068985 | 301.48 | 192 |
| Winter Peak | 0.110454 | 524.66 | 384 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.171505 | 416.99 | 3710741.5 |
| residential-cooling | 0.195119 | 316.54 | 3324856.39 |
| residential-lighting | 0.073856 | 18.02 | 1078138.92 |
| residential-appliances | 0.092696 | 66.23 | 5704021.1 |
| residential-other | 0.124744 | 79.89 | 12067878.08 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.144505 | 70.45 | 630571.51 |
| commercial-cooling | 0.153006 | 218.22 | 5516822.98 |
| commercial-lighting | 0.198255 | 43.89 | 2432793.08 |
| commercial-appliances | 0.108354 | 57.18 | 3837719.81 |
| commercial-other | 0.196322 | 122.39 | 9946160.61 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.067363 | 1.87 | 91695.01 |
| HDVs | 0.113676 | 0.04 | 3520.85 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.195883 | 452.22 | 21161349.3 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 11004.16 | 11750.82 | 0.9365 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 11004.16 | 11074.75 | 0.9936 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 9946.61 | 10029.32 | 0.9918 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 1690.01 | 2082.85 | 0.8114 |  |
| category_peak_commercial-cooling | 1893.15 | 2251.62 | 0.8408 |  |
| category_peak_residential-heating | 1634.94 | 2841.43 | 0.5754 |  |
| category_peak_commercial-heating | 376.76 | 636.82 | 0.5916 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.15 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 11348.07 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 9527.77 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 11506.29 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 8983.47 | 8941.17 | 1.0047 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 8270.35 | 6812.06 | 1.2141 |  |
| winter_peak_net_load | 8983.47 | 7557.5 | 1.1887 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 1006.88 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 1328.85 | 438 | top 5% of LDC = top ~438 hours |
| overall | 495.15 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.1839 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 6 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 9800.26 | shifted gen by -14d; peak hour 2018-09-04 17:00:00 |
| net_load_peak_shift_-7d | 9100.97 | shifted gen by -7d; peak hour 2018-08-31 17:00:00 |
| net_load_peak_shift_0d | 9159.49 | shifted gen by 0d; peak hour 2018-10-04 17:00:00 |
| net_load_peak_shift_7d | 9876.66 | shifted gen by 7d; peak hour 2018-02-24 18:00:00 |
| net_load_peak_shift_14d | 10052.44 | shifted gen by 14d; peak hour 2018-02-24 19:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| OK_total_annual_TWh | 69.51 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| OK_solar_pv_annual_TWh | 16.784 | 16.784 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| OK_wind_annual_TWh | 68.1738 | 68.1738 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 6787.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 110.5 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 18336.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2795 | 0.2795 | 0.7432 | 0.7432 |
| solar-pv-dist | 0.1681 | 0.1681 | 0.4658 | 0.4658 |
| onshore-wind | 0.4244 | 0.4244 | 0.2670 | 0.2670 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.184

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 9800 | 2018-09-04 17:00:00 | -1764 |
| -7 | 9101 | 2018-08-31 17:00:00 | -1764 |
| 0 | 9159 | 2018-10-04 17:00:00 | -1764 |
| 7 | 9877 | 2018-02-24 18:00:00 | -1764 |
| 14 | 10052 | 2018-02-24 19:00:00 | -1764 |

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
| efs | 21161.3 | 3731 | 2416 | 565 | 1.54 |
| flat | 21161.3 | 2416 | 2416 | 0 | 1.00 |
| cambium_residual | 21161.3 | 6015 | 2416 | 970 | 2.49 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
