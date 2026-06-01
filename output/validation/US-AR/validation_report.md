# Validation report - US-AR

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **50.0 TWh**
- Peak hour: **2018-07-31 13:00:00** at **8.0 GW**
- Cluster NRMSE: **0.375**

## Days per timeslice

- Winter: 35
- Spring: 84
- Summer: 117
- Fall: 78
- Summer Peak: 46
- Winter Peak: 5

## Top-5 peak days

- Summer Peak: [152, 157, 158, 163, 164, 165, 166, 173, 177, 178, 179, 180, 184, 185, 186, 187, 191, 192, 193, 194, 198, 199, 200, 201, 205, 206, 207, 208, 212, 213, 214, 215, 220, 221, 222, 226, 227, 228, 229, 230, 233, 234, 235, 236, 240, 241]
- Winter Peak: [10, 11, 17, 33, 34]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 2687347.6 | 2687347.6 | 0.0 | 0.0 |
| residential-cooling | 2390855.8 | 2390855.8 | -0.0 | -0.0 |
| residential-lighting | 844560.38 | 844560.38 | 0.0 | 0.0 |
| residential-appliances | 4437980.66 | 4437980.66 | 0.0 | 0.0 |
| residential-other | 9337368.11 | 9337368.11 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 320647.71 | 320647.71 | 0.0 | 0.0 |
| commercial-cooling | 2903185.81 | 2903185.81 | 0.0 | 0.0 |
| commercial-lighting | 1317168.82 | 1317168.82 | 0.0 | 0.0 |
| commercial-appliances | 2076184.06 | 2076184.06 | 0.0 | 0.0 |
| commercial-other | 5380392.73 | 5380392.73 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 72415.02 | 72415.02 | 0.0 | 0.0 |
| HDVs | 2378.09 | 2378.09 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 18279165.59 | 18279165.59 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.068294 | 243.62 | 8760 |
| Winter | 0.079274 | 212.77 | 840 |
| Spring | 0.110275 | 298.49 | 2016 |
| Summer | 0.091006 | 241.04 | 2808 |
| Fall | 0.118134 | 292.6 | 1872 |
| Summer Peak | 0.036399 | 95.65 | 1104 |
| Winter Peak | 0.083929 | 195.43 | 120 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.153133 | 217.25 | 2687347.6 |
| residential-cooling | 0.159258 | 146.55 | 2390855.8 |
| residential-lighting | 0.06249 | 10.84 | 844560.38 |
| residential-appliances | 0.086154 | 47.86 | 4437980.66 |
| residential-other | 0.10376 | 44.72 | 9337368.11 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.103933 | 25.48 | 320647.71 |
| commercial-cooling | 0.120637 | 76.33 | 2903185.81 |
| commercial-lighting | 0.142185 | 16.85 | 1317168.82 |
| commercial-appliances | 0.096016 | 26.4 | 2076184.06 |
| commercial-other | 0.169667 | 46.67 | 5380392.73 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.046075 | 0.83 | 72415.02 |
| HDVs | 0.106222 | 0.02 | 2378.09 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.134691 | 223.9 | 18279165.59 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 7719.44 | 7963.14 | 0.9694 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 7719.44 | 7739.28 | 0.9974 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 7576.06 | 7715.38 | 0.9819 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 1124.29 | 1334.2 | 0.8427 |  |
| category_peak_commercial-cooling | 1069.07 | 1165.08 | 0.9176 |  |
| category_peak_residential-heating | 1674.31 | 1927.23 | 0.8688 |  |
| category_peak_commercial-heating | 285.49 | 331.09 | 0.8623 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.97 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 7730.04 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 7628.73 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 7818.36 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 7576.06 | 7798.25 | 0.9715 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 7506.75 | 7418.85 | 1.0118 |  |
| winter_peak_net_load | 7576.06 | 7681.98 | 0.9862 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 130.57 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 106.7 | 438 | top 5% of LDC = top ~438 hours |
| overall | 88.88 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.2983 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 7 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 7965.62 | shifted gen by -14d; peak hour 2018-01-10 19:00:00 |
| net_load_peak_shift_-7d | 7965.62 | shifted gen by -7d; peak hour 2018-01-10 19:00:00 |
| net_load_peak_shift_0d | 7965.62 | shifted gen by 0d; peak hour 2018-01-10 19:00:00 |
| net_load_peak_shift_7d | 7965.62 | shifted gen by 7d; peak hour 2018-01-10 19:00:00 |
| net_load_peak_shift_14d | 7965.62 | shifted gen by 14d; peak hour 2018-01-10 19:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| AR_total_annual_TWh | 50.05 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| AR_solar_pv_annual_TWh | 1.0977 | 1.0977 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| AR_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 306.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 278.5 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2489 | 0.2489 | 0.6051 | 0.6051 |
| solar-pv-dist | 0.1758 | 0.1758 | 0.4328 | 0.4328 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.298

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 7966 | 2018-01-10 19:00:00 | 5588 |
| -7 | 7966 | 2018-01-10 19:00:00 | 5588 |
| 0 | 7966 | 2018-01-10 19:00:00 | 5588 |
| 7 | 7966 | 2018-01-10 19:00:00 | 5588 |
| 14 | 7966 | 2018-01-10 19:00:00 | 5588 |

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
| efs | 18279.2 | 3190 | 2087 | 489 | 1.53 |
| flat | 18279.2 | 2087 | 2087 | 0 | 1.00 |
| cambium_residual | 18279.2 | 4170 | 2087 | 705 | 2.00 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
