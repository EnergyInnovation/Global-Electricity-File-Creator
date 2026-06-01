# Validation report - US-WA

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **92.1 TWh**
- Peak hour: **2018-01-05 12:00:00** at **16.0 GW**
- Cluster NRMSE: **0.398**

## Days per timeslice

- Winter: 62
- Spring: 86
- Summer: 101
- Fall: 80
- Summer Peak: 25
- Winter Peak: 11

## Top-5 peak days

- Summer Peak: [156, 164, 173, 177, 180, 187, 188, 193, 194, 199, 200, 201, 202, 207, 208, 212, 219, 220, 226, 227, 230, 234, 236, 241, 243]
- Winter Peak: [4, 9, 10, 12, 16, 24, 40, 44, 332, 333, 362]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 7168502.34 | 7168502.34 | 0.0 | 0.0 |
| residential-cooling | 447664.13 | 447664.13 | 0.0 | 0.0 |
| residential-lighting | 3128558.03 | 3128558.03 | 0.0 | 0.0 |
| residential-appliances | 12468349.94 | 12468349.94 | 0.0 | 0.0 |
| residential-other | 16596916.76 | 16596916.76 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 1713434.94 | 1713434.94 | 0.0 | 0.0 |
| commercial-cooling | 3676143.02 | 3676143.02 | 0.0 | 0.0 |
| commercial-lighting | 2856984.17 | 2856984.17 | 0.0 | 0.0 |
| commercial-appliances | 5910521.69 | 5910521.69 | 0.0 | 0.0 |
| commercial-other | 16052344.67 | 16052344.67 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 126616.51 | 126616.51 | 0.0 | 0.0 |
| HDVs | 2725.16 | 2725.16 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 31505.44 | 31505.44 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 21964065.84 | 21964065.84 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.080971 | 620.54 | 8760 |
| Winter | 0.082069 | 541.04 | 1488 |
| Spring | 0.100139 | 678.79 | 2064 |
| Summer | 0.135158 | 730.3 | 2424 |
| Fall | 0.103811 | 671.44 | 1920 |
| Summer Peak | 0.054426 | 175.1 | 600 |
| Winter Peak | 0.047137 | 247.47 | 264 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.155138 | 389.16 | 7168502.34 |
| residential-cooling | 0.104453 | 20.73 | 447664.13 |
| residential-lighting | 0.068186 | 42.88 | 3128558.03 |
| residential-appliances | 0.072114 | 100.21 | 12468349.94 |
| residential-other | 0.096514 | 83.49 | 16596916.76 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.109429 | 90.79 | 1713434.94 |
| commercial-cooling | 0.086905 | 60.94 | 3676143.02 |
| commercial-lighting | 0.148439 | 39.79 | 2856984.17 |
| commercial-appliances | 0.083568 | 60.88 | 5910521.69 |
| commercial-other | 0.175414 | 148.81 | 16052344.67 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.061781 | 1.94 | 126616.51 |
| HDVs | 0.09441 | 0.02 | 2725.16 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.061781 | 0.48 | 31505.44 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.232005 | 379.27 | 21964065.84 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 15136.47 | 15729.34 | 0.9623 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 11871.13 | 11984.73 | 0.9905 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 15136.47 | 15156.75 | 0.9987 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 235.95 | 331.41 | 0.712 |  |
| category_peak_commercial-cooling | 1087.61 | 1400.93 | 0.7763 |  |
| category_peak_residential-heating | 2578.15 | 3161.21 | 0.8156 |  |
| category_peak_commercial-heating | 865.96 | 1066.07 | 0.8123 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.8 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 14815.84 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 14182.83 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 15124.53 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 14889.67 | 14874.93 | 1.001 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 11754.89 | 11357.58 | 1.035 |  |
| winter_peak_net_load | 14889.67 | 14646.37 | 1.0166 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 510.02 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 427.78 | 438 | top 5% of LDC = top ~438 hours |
| overall | 204.23 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.1399 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 5 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 15394.84 | shifted gen by -14d; peak hour 2018-12-18 12:00:00 |
| net_load_peak_shift_-7d | 15359.69 | shifted gen by -7d; peak hour 2018-01-03 13:00:00 |
| net_load_peak_shift_0d | 15126.89 | shifted gen by 0d; peak hour 2018-12-28 12:00:00 |
| net_load_peak_shift_7d | 15404.49 | shifted gen by 7d; peak hour 2018-01-04 12:00:00 |
| net_load_peak_shift_14d | 14968.3 | shifted gen by 14d; peak hour 2018-01-11 12:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| WA_total_annual_TWh | 92.14 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| WA_solar_pv_annual_TWh | 1.1337 | 1.1337 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| WA_wind_annual_TWh | 9.1093 | 9.1093 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 184.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 646.4 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 3732.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2269 | 0.2269 | 0.6796 | 0.6796 |
| solar-pv-dist | 0.1354 | 0.1354 | 0.4189 | 0.4189 |
| onshore-wind | 0.2786 | 0.2786 | 0.2152 | 0.2152 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.140

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 15395 | 2018-12-18 12:00:00 | 9349 |
| -7 | 15360 | 2018-01-03 13:00:00 | 9349 |
| 0 | 15127 | 2018-12-28 12:00:00 | 9349 |
| 7 | 15404 | 2018-01-04 12:00:00 | 9349 |
| 14 | 14968 | 2018-01-11 12:00:00 | 9349 |

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
| efs | 21964.1 | 3345 | 2507 | 559 | 1.33 |
| flat | 21964.1 | 2507 | 2507 | 0 | 1.00 |
| cambium_residual | 21964.1 | 4145 | 2507 | 539 | 1.65 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
