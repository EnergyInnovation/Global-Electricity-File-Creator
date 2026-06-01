# Validation report - US-NC

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **141.3 TWh**
- Peak hour: **2018-01-09 09:00:00** at **24.6 GW**
- Cluster NRMSE: **0.476**

## Days per timeslice

- Winter: 54
- Spring: 71
- Summer: 155
- Fall: 53
- Summer Peak: 19
- Winter Peak: 13

## Top-5 peak days

- Summer Peak: [184, 192, 193, 194, 195, 199, 200, 201, 205, 207, 213, 214, 221, 222, 229, 233, 236, 242, 243]
- Winter Peak: [9, 10, 11, 12, 19, 23, 25, 26, 28, 33, 36, 37, 352]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 9208059.79 | 9208059.79 | 0.0 | 0.0 |
| residential-cooling | 7582016.41 | 7582016.41 | 0.0 | 0.0 |
| residential-lighting | 2898247.36 | 2898247.36 | 0.0 | 0.0 |
| residential-appliances | 18303839.39 | 18303839.39 | -0.0 | -0.0 |
| residential-other | 25644314.19 | 25644314.19 | -0.0 | -0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 941002.34 | 941002.34 | -0.0 | -0.0 |
| commercial-cooling | 11229689.33 | 11229689.33 | 0.0 | 0.0 |
| commercial-lighting | 5401905.04 | 5401905.04 | 0.0 | 0.0 |
| commercial-appliances | 10004337.63 | 10004337.63 | 0.0 | 0.0 |
| commercial-other | 22213862.84 | 22213862.84 | -0.0 | -0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 237202.1 | 237202.1 | 0.0 | 0.0 |
| HDVs | 4137.8 | 4137.8 | -0.0 | -0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 28635.39 | 28635.39 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 27589947.94 | 27589947.94 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.077011 | 902.48 | 8760 |
| Winter | 0.088628 | 774.65 | 1296 |
| Spring | 0.104474 | 959.13 | 1704 |
| Summer | 0.090535 | 902.34 | 3720 |
| Fall | 0.130551 | 1183.78 | 1272 |
| Summer Peak | 0.04555 | 407.48 | 456 |
| Winter Peak | 0.09664 | 702.33 | 312 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.092426 | 515.55 | 9208059.79 |
| residential-cooling | 0.150089 | 459.81 | 7582016.41 |
| residential-lighting | 0.058618 | 35.15 | 2898247.36 |
| residential-appliances | 0.0781 | 171.78 | 18303839.39 |
| residential-other | 0.089927 | 114.34 | 25644314.19 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.076213 | 50.85 | 941002.34 |
| commercial-cooling | 0.105992 | 270.16 | 11229689.33 |
| commercial-lighting | 0.155019 | 76.85 | 5401905.04 |
| commercial-appliances | 0.085078 | 117.96 | 10004337.63 |
| commercial-other | 0.186429 | 222.69 | 22213862.84 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.057401 | 3.43 | 237202.1 |
| HDVs | 0.108943 | 0.04 | 4137.8 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.057401 | 0.41 | 28635.39 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.193637 | 444.17 | 27589947.94 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 23258.98 | 24198.24 | 0.9612 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 21933.34 | 22044.37 | 0.995 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 23258.98 | 23310.04 | 0.9978 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 3732.82 | 4428.94 | 0.8428 |  |
| category_peak_commercial-cooling | 3906.68 | 4472.02 | 0.8736 |  |
| category_peak_residential-heating | 6348.52 | 7520.57 | 0.8442 |  |
| category_peak_commercial-heating | 828.52 | 921.8 | 0.8988 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.88 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 22625.99 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 21945.77 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 23202.85 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 22571.08 | 22871.06 | 0.9869 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 20689.17 | 19702.51 | 1.0501 |  |
| winter_peak_net_load | 22571.08 | 22153.48 | 1.0189 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 736.51 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 659.32 | 438 | top 5% of LDC = top ~438 hours |
| overall | 347.64 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0142 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 36 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 23363.26 | shifted gen by -14d; peak hour 2018-02-06 08:00:00 |
| net_load_peak_shift_-7d | 23444.99 | shifted gen by -7d; peak hour 2018-01-19 19:00:00 |
| net_load_peak_shift_0d | 23350.29 | shifted gen by 0d; peak hour 2018-01-19 19:00:00 |
| net_load_peak_shift_7d | 23366.19 | shifted gen by 7d; peak hour 2018-01-19 19:00:00 |
| net_load_peak_shift_14d | 23632.4 | shifted gen by 14d; peak hour 2018-01-26 09:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| NC_total_annual_TWh | 141.29 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| NC_solar_pv_annual_TWh | 15.0086 | 15.0086 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| NC_wind_annual_TWh | 0.5925 | 0.5925 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 6681.5 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 876.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 208.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2347 | 0.2347 | 0.5392 | 0.5392 |
| solar-pv-dist | 0.1659 | 0.1659 | 0.3799 | 0.3799 |
| onshore-wind | 0.3252 | 0.3252 | 0.3015 | 0.3015 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.014

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 23363 | 2018-02-06 08:00:00 | 14348 |
| -7 | 23445 | 2018-01-19 19:00:00 | 14348 |
| 0 | 23350 | 2018-01-19 19:00:00 | 14348 |
| 7 | 23366 | 2018-01-19 19:00:00 | 14348 |
| 14 | 23632 | 2018-01-26 09:00:00 | 14348 |

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
| efs | 27589.9 | 4606 | 3150 | 744 | 1.46 |
| flat | 27589.9 | 3150 | 3150 | 0 | 1.00 |
| cambium_residual | 27589.9 | 7168 | 3150 | 1253 | 2.28 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
