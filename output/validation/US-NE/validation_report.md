# Validation report - US-NE

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **33.8 TWh**
- Peak hour: **2018-07-13 13:00:00** at **5.5 GW**
- Cluster NRMSE: **0.869**

## Days per timeslice

- Winter: 82
- Spring: 83
- Summer: 101
- Fall: 56
- Summer Peak: 19
- Winter Peak: 24

## Top-5 peak days

- Summer Peak: [152, 173, 191, 192, 193, 195, 196, 200, 201, 212, 213, 214, 216, 221, 227, 230, 232, 233, 240]
- Winter Peak: [3, 18, 19, 21, 24, 27, 32, 39, 49, 305, 308, 311, 318, 321, 325, 329, 331, 333, 337, 340, 342, 349, 354, 356]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 1682957.21 | 1682957.21 | -0.0 | -0.0 |
| residential-cooling | 965510.26 | 965510.26 | 0.0 | 0.0 |
| residential-lighting | 570564.77 | 570564.77 | 0.0 | 0.0 |
| residential-appliances | 2999601.41 | 2999601.41 | 0.0 | 0.0 |
| residential-other | 4870187.57 | 4870187.57 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 288858.73 | 288858.73 | 0.0 | 0.0 |
| commercial-cooling | 1623396.83 | 1623396.83 | 0.0 | 0.0 |
| commercial-lighting | 917901.52 | 917901.52 | 0.0 | 0.0 |
| commercial-appliances | 1337845.84 | 1337845.84 | 0.0 | 0.0 |
| commercial-other | 5536166.47 | 5536166.47 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 42765.2 | 42765.2 | 0.0 | 0.0 |
| HDVs | 2126.53 | 2126.53 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 12952469.17 | 12952469.17 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.149537 | 368.6 | 8760 |
| Winter | 0.15285 | 369.68 | 1968 |
| Spring | 0.162846 | 370.91 | 1992 |
| Summer | 0.16301 | 402.23 | 2424 |
| Fall | 0.143577 | 348.13 | 1344 |
| Summer Peak | 0.131382 | 265.64 | 456 |
| Winter Peak | 0.182149 | 344.71 | 576 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.219198 | 164.71 | 1682957.21 |
| residential-cooling | 0.171282 | 68.54 | 965510.26 |
| residential-lighting | 0.073881 | 9.34 | 570564.77 |
| residential-appliances | 0.082432 | 30.07 | 2999601.41 |
| residential-other | 0.117981 | 30.98 | 4870187.57 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.16955 | 27.87 | 288858.73 |
| commercial-cooling | 0.128641 | 50.33 | 1623396.83 |
| commercial-lighting | 0.16837 | 15.63 | 917901.52 |
| commercial-appliances | 0.108782 | 20.85 | 1337845.84 |
| commercial-other | 0.204045 | 58.36 | 5536166.47 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.066857 | 0.9 | 42765.2 |
| HDVs | 0.096359 | 0.04 | 2126.53 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.207305 | 295.01 | 12952469.17 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 5064.59 | 5492.47 | 0.9221 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 5064.59 | 5096.27 | 0.9938 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 4414.81 | 4462.18 | 0.9894 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 446.41 | 575.78 | 0.7753 |  |
| category_peak_commercial-cooling | 509.12 | 689.19 | 0.7387 |  |
| category_peak_residential-heating | 544.8 | 861.66 | 0.6323 |  |
| category_peak_commercial-heating | 129.47 | 199.93 | 0.6476 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.17 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 5297.03 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 4375.9 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 5377.06 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 4334.17 | 4265.15 | 1.0162 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 4334.17 | 3214.53 | 1.3483 |  |
| winter_peak_net_load | 4194.21 | 2894.83 | 1.4489 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 348.35 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 565.75 | 438 | top 5% of LDC = top ~438 hours |
| overall | 257.49 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0667 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 26 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 4539.03 | shifted gen by -14d; peak hour 2018-08-07 19:00:00 |
| net_load_peak_shift_-7d | 4337.05 | shifted gen by -7d; peak hour 2018-01-26 21:00:00 |
| net_load_peak_shift_0d | 4428.1 | shifted gen by 0d; peak hour 2018-05-15 19:00:00 |
| net_load_peak_shift_7d | 4537.74 | shifted gen by 7d; peak hour 2018-01-05 19:00:00 |
| net_load_peak_shift_14d | 4486.38 | shifted gen by 14d; peak hour 2018-01-12 19:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| NE_total_annual_TWh | 33.79 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| NE_solar_pv_annual_TWh | 6.6667 | 6.6667 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| NE_wind_annual_TWh | 29.9761 | 29.9761 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 2705.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 75.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 7600.5 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2766 | 0.2766 | 0.7879 | 0.7879 |
| solar-pv-dist | 0.1717 | 0.1717 | 0.4561 | 0.4561 |
| onshore-wind | 0.4502 | 0.4502 | 0.3092 | 0.3092 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.067

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 4539 | 2018-08-07 19:00:00 | -326 |
| -7 | 4337 | 2018-01-26 21:00:00 | -326 |
| 0 | 4428 | 2018-05-15 19:00:00 | -326 |
| 7 | 4538 | 2018-01-05 19:00:00 | -326 |
| 14 | 4486 | 2018-01-12 19:00:00 | -326 |

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
| efs | 12952.5 | 2553 | 1479 | 428 | 1.73 |
| flat | 12952.5 | 1479 | 1479 | 0 | 1.00 |
| cambium_residual | 12952.5 | 3765 | 1479 | 799 | 2.55 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
