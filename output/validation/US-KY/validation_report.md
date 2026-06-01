# Validation report - US-KY

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **77.0 TWh**
- Peak hour: **2018-01-09 09:00:00** at **13.2 GW**
- Cluster NRMSE: **0.347**

## Days per timeslice

- Winter: 44
- Spring: 98
- Summer: 109
- Fall: 83
- Summer Peak: 22
- Winter Peak: 9

## Top-5 peak days

- Summer Peak: [164, 165, 172, 173, 180, 187, 192, 193, 194, 198, 199, 200, 201, 205, 213, 214, 221, 227, 228, 229, 240, 243]
- Winter Peak: [5, 9, 10, 17, 18, 19, 23, 31, 354]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 4250509.96 | 4250509.96 | 0.0 | 0.0 |
| residential-cooling | 3023903.87 | 3023903.87 | 0.0 | 0.0 |
| residential-lighting | 978086.17 | 978086.17 | 0.0 | 0.0 |
| residential-appliances | 7205275.5 | 7205275.5 | 0.0 | 0.0 |
| residential-other | 11547713.95 | 11547713.95 | -0.0 | -0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 586808.32 | 586808.32 | 0.0 | 0.0 |
| commercial-cooling | 3851465.42 | 3851465.42 | 0.0 | 0.0 |
| commercial-lighting | 2143906.8 | 2143906.8 | 0.0 | 0.0 |
| commercial-appliances | 3613071.51 | 3613071.51 | 0.0 | 0.0 |
| commercial-other | 9616207.5 | 9616207.5 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 107447.0 | 107447.0 | 0.0 | 0.0 |
| HDVs | 2928.03 | 2928.03 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 30071791.03 | 30071791.03 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.063006 | 389.94 | 8760 |
| Winter | 0.072259 | 304.81 | 1056 |
| Spring | 0.078999 | 420.49 | 2352 |
| Summer | 0.102197 | 403.14 | 2616 |
| Fall | 0.133934 | 468.8 | 1992 |
| Summer Peak | 0.030846 | 132.91 | 528 |
| Winter Peak | 0.053574 | 214.55 | 216 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.141239 | 302.04 | 4250509.96 |
| residential-cooling | 0.169212 | 199.36 | 3023903.87 |
| residential-lighting | 0.066324 | 13.71 | 978086.17 |
| residential-appliances | 0.085593 | 74.93 | 7205275.5 |
| residential-other | 0.104924 | 56.9 | 11547713.95 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.111217 | 40.9 | 586808.32 |
| commercial-cooling | 0.120481 | 104.36 | 3851465.42 |
| commercial-lighting | 0.177965 | 33.13 | 2143906.8 |
| commercial-appliances | 0.096552 | 48.59 | 3613071.51 |
| commercial-other | 0.184054 | 102.15 | 9616207.5 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.045242 | 1.05 | 107447.0 |
| HDVs | 0.099057 | 0.02 | 2928.03 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.150223 | 294.74 | 30071791.03 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 12816.04 | 13006.44 | 0.9854 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 11895.11 | 11905.01 | 0.9992 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 12816.04 | 12847.03 | 0.9976 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 1552.67 | 1678.09 | 0.9253 |  |
| category_peak_commercial-cooling | 1420.82 | 1500.8 | 0.9467 |  |
| category_peak_residential-heating | 2642.47 | 2805.16 | 0.942 |  |
| category_peak_commercial-heating | 470.03 | 506.73 | 0.9276 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 1.0 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 12088.56 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 12151.97 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 12428.17 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 12797.34 | 12875.69 | 0.9939 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 11712.81 | 11585.85 | 1.011 |  |
| winter_peak_net_load | 12797.34 | 12717.3 | 1.0063 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 228.63 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 136.47 | 438 | top 5% of LDC = top ~438 hours |
| overall | 131.66 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0153 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 9 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 13079.59 | shifted gen by -14d; peak hour 2018-01-09 10:00:00 |
| net_load_peak_shift_-7d | 13024.67 | shifted gen by -7d; peak hour 2018-01-19 09:00:00 |
| net_load_peak_shift_0d | 13003.62 | shifted gen by 0d; peak hour 2018-01-10 09:00:00 |
| net_load_peak_shift_7d | 13081.07 | shifted gen by 7d; peak hour 2018-01-19 09:00:00 |
| net_load_peak_shift_14d | 13201.61 | shifted gen by 14d; peak hour 2018-01-09 09:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| KY_total_annual_TWh | 77.0 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| KY_solar_pv_annual_TWh | 0.9374 | 0.9374 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| KY_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 398.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 52.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2462 | 0.2462 | 0.6711 | 0.6711 |
| solar-pv-dist | 0.1696 | 0.1696 | 0.4113 | 0.4113 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.015

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 13080 | 2018-01-09 10:00:00 | 8683 |
| -7 | 13025 | 2018-01-19 09:00:00 | 8683 |
| 0 | 13004 | 2018-01-10 09:00:00 | 8683 |
| 7 | 13081 | 2018-01-19 09:00:00 | 8683 |
| 14 | 13202 | 2018-01-09 09:00:00 | 8683 |

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
| efs | 30071.8 | 4873 | 3433 | 783 | 1.42 |
| flat | 30071.8 | 3433 | 3433 | 0 | 1.00 |
| cambium_residual | 30071.8 | 6904 | 3433 | 942 | 2.01 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
