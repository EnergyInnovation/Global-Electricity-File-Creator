# Validation report - US-KS

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **42.2 TWh**
- Peak hour: **2018-07-18 13:00:00** at **7.4 GW**
- Cluster NRMSE: **0.682**

## Days per timeslice

- Winter: 82
- Spring: 78
- Summer: 124
- Fall: 63
- Summer Peak: 9
- Winter Peak: 9

## Top-5 peak days

- Summer Peak: [158, 193, 194, 210, 215, 219, 234, 240, 241]
- Winter Peak: [9, 10, 11, 33, 40, 306, 334, 338, 352]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 1907737.4 | 1907737.4 | 0.0 | 0.0 |
| residential-cooling | 1836597.3 | 1836597.3 | 0.0 | 0.0 |
| residential-lighting | 731273.15 | 731273.15 | 0.0 | 0.0 |
| residential-appliances | 3830635.99 | 3830635.99 | 0.0 | 0.0 |
| residential-other | 6221928.49 | 6221928.49 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 392124.85 | 392124.85 | 0.0 | 0.0 |
| commercial-cooling | 3128517.0 | 3128517.0 | 0.0 | 0.0 |
| commercial-lighting | 1461052.17 | 1461052.17 | 0.0 | 0.0 |
| commercial-appliances | 2129402.11 | 2129402.11 | 0.0 | 0.0 |
| commercial-other | 8811664.71 | 8811664.71 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 61108.63 | 61108.63 | 0.0 | 0.0 |
| HDVs | 2045.45 | 2045.45 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 11661649.3 | 11661649.3 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.12448 | 435.81 | 8760 |
| Winter | 0.147377 | 480.11 | 1968 |
| Spring | 0.128834 | 433.54 | 1872 |
| Summer | 0.122633 | 420.5 | 2976 |
| Fall | 0.139974 | 468.08 | 1512 |
| Summer Peak | 0.124991 | 287.71 | 216 |
| Winter Peak | 0.084973 | 185.07 | 216 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.207767 | 210.54 | 1907737.4 |
| residential-cooling | 0.177548 | 163.49 | 1836597.3 |
| residential-lighting | 0.075756 | 12.55 | 731273.15 |
| residential-appliances | 0.08411 | 39.23 | 3830635.99 |
| residential-other | 0.126554 | 43.26 | 6221928.49 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.15558 | 43.82 | 392124.85 |
| commercial-cooling | 0.137446 | 116.7 | 3128517.0 |
| commercial-lighting | 0.173804 | 25.84 | 1461052.17 |
| commercial-appliances | 0.1151 | 34.87 | 2129402.11 |
| commercial-other | 0.208493 | 115.39 | 8811664.71 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.06363 | 1.2 | 61108.63 |
| HDVs | 0.118925 | 0.02 | 2045.45 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.163128 | 242.92 | 11661649.3 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 6754.99 | 7370.16 | 0.9165 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 6754.99 | 6809.73 | 0.992 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 6164.85 | 6180.97 | 0.9974 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 965.3 | 1196.89 | 0.8065 |  |
| category_peak_commercial-cooling | 1118.45 | 1375.75 | 0.813 |  |
| category_peak_residential-heating | 784.56 | 1154.85 | 0.6794 |  |
| category_peak_commercial-heating | 243.56 | 349.06 | 0.6978 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.29 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 6930.19 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 5975.99 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 7101.93 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 5694.89 | 5775.0 | 0.9861 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 5541.87 | 5316.95 | 1.0423 |  |
| winter_peak_net_load | 5694.89 | 5365.64 | 1.0614 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 627.22 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 807.77 | 438 | top 5% of LDC = top ~438 hours |
| overall | 281.96 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0032 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 6 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 6103.1 | shifted gen by -14d; peak hour 2018-07-19 13:00:00 |
| net_load_peak_shift_-7d | 6131.63 | shifted gen by -7d; peak hour 2018-01-04 18:00:00 |
| net_load_peak_shift_0d | 5832.43 | shifted gen by 0d; peak hour 2018-09-06 11:00:00 |
| net_load_peak_shift_7d | 5986.95 | shifted gen by 7d; peak hour 2018-08-09 14:00:00 |
| net_load_peak_shift_14d | 5815.32 | shifted gen by 14d; peak hour 2018-08-29 17:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| KS_total_annual_TWh | 42.18 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| KS_solar_pv_annual_TWh | 3.6683 | 3.6683 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| KS_wind_annual_TWh | 29.6193 | 29.6193 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 1340.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 92.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 8040.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.3002 | 0.3002 | 0.8156 | 0.8156 |
| solar-pv-dist | 0.1753 | 0.1753 | 0.4769 | 0.4769 |
| onshore-wind | 0.4205 | 0.4205 | 0.2935 | 0.2935 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.003

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 6103 | 2018-07-19 13:00:00 | 1015 |
| -7 | 6132 | 2018-01-04 18:00:00 | 1015 |
| 0 | 5832 | 2018-09-06 11:00:00 | 1015 |
| 7 | 5987 | 2018-08-09 14:00:00 | 1015 |
| 14 | 5815 | 2018-08-29 17:00:00 | 1015 |

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
| efs | 11661.6 | 2354 | 1331 | 312 | 1.77 |
| flat | 11661.6 | 1331 | 1331 | 0 | 1.00 |
| cambium_residual | 11661.6 | 3007 | 1331 | 469 | 2.26 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
