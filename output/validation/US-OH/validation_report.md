# Validation report - US-OH

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **150.9 TWh**
- Peak hour: **2018-02-06 09:00:00** at **26.1 GW**
- Cluster NRMSE: **0.369**

## Days per timeslice

- Winter: 64
- Spring: 85
- Summer: 105
- Fall: 80
- Summer Peak: 25
- Winter Peak: 6

## Top-5 peak days

- Summer Peak: [164, 170, 173, 191, 192, 194, 198, 199, 200, 201, 205, 206, 207, 208, 212, 213, 214, 215, 219, 221, 222, 226, 227, 228, 229]
- Winter Peak: [4, 9, 10, 26, 37, 38]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 9016524.03 | 9016524.03 | 0.0 | 0.0 |
| residential-cooling | 3623728.02 | 3623728.02 | 0.0 | 0.0 |
| residential-lighting | 3349490.04 | 3349490.04 | 0.0 | 0.0 |
| residential-appliances | 14586957.8 | 14586957.8 | 0.0 | 0.0 |
| residential-other | 22965738.57 | 22965738.57 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 1125571.51 | 1125571.51 | 0.0 | 0.0 |
| commercial-cooling | 8574296.6 | 8574296.6 | 0.0 | 0.0 |
| commercial-lighting | 4831682.3 | 4831682.3 | 0.0 | 0.0 |
| commercial-appliances | 6880451.35 | 6880451.35 | 0.0 | 0.0 |
| commercial-other | 25114302.46 | 25114302.46 | -0.0 | -0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 234880.61 | 234880.61 | 0.0 | 0.0 |
| HDVs | 5398.83 | 5398.83 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 43557.03 | 43557.03 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 50516521.69 | 50516521.69 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.062726 | 775.44 | 8760 |
| Winter | 0.084295 | 759.11 | 1536 |
| Spring | 0.1087 | 881.77 | 2040 |
| Summer | 0.082202 | 680.95 | 2520 |
| Fall | 0.131215 | 958.13 | 1920 |
| Summer Peak | 0.03902 | 338.21 | 600 |
| Winter Peak | 0.057231 | 483.01 | 144 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.135476 | 554.48 | 9016524.03 |
| residential-cooling | 0.130924 | 188.85 | 3623728.02 |
| residential-lighting | 0.064924 | 45.08 | 3349490.04 |
| residential-appliances | 0.069442 | 113.3 | 14586957.8 |
| residential-other | 0.096373 | 107.63 | 22965738.57 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.105788 | 71.84 | 1125571.51 |
| commercial-cooling | 0.101275 | 195.97 | 8574296.6 |
| commercial-lighting | 0.147457 | 63.39 | 4831682.3 |
| commercial-appliances | 0.076302 | 70.17 | 6880451.35 |
| commercial-other | 0.175418 | 243.08 | 25114302.46 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.047562 | 2.57 | 234880.61 |
| HDVs | 0.111948 | 0.04 | 5398.83 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.047562 | 0.48 | 43557.03 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.162347 | 576.04 | 50516521.69 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 25060.58 | 25292.43 | 0.9908 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 22519.94 | 22574.71 | 0.9976 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 25060.58 | 25120.14 | 0.9976 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 1758.43 | 2082.3 | 0.8445 |  |
| category_peak_commercial-cooling | 3159.71 | 3497.02 | 0.9035 |  |
| category_peak_residential-heating | 4502.19 | 4958.9 | 0.9079 |  |
| category_peak_commercial-heating | 775.87 | 861.97 | 0.9001 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 1.0 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 23902.89 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 23474.87 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 24406.14 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 24633.98 | 24267.11 | 1.0151 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 21576.66 | 20808.18 | 1.0369 |  |
| winter_peak_net_load | 24633.98 | 23986.23 | 1.027 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 727.79 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 542.58 | 438 | top 5% of LDC = top ~438 hours |
| overall | 318.88 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.1435 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 37 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 24381.69 | shifted gen by -14d; peak hour 2018-02-06 10:00:00 |
| net_load_peak_shift_-7d | 24557.15 | shifted gen by -7d; peak hour 2018-01-04 18:00:00 |
| net_load_peak_shift_0d | 24637.18 | shifted gen by 0d; peak hour 2018-02-06 09:00:00 |
| net_load_peak_shift_7d | 24519.4 | shifted gen by 7d; peak hour 2018-02-07 09:00:00 |
| net_load_peak_shift_14d | 25251.39 | shifted gen by 14d; peak hour 2018-02-06 10:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| OH_total_annual_TWh | 150.87 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| OH_solar_pv_annual_TWh | 5.004 | 5.004 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| OH_wind_annual_TWh | 3.1713 | 3.1713 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 2217.5 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 269.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 1063.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 21.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2389 | 0.2389 | 0.6809 | 0.6809 |
| solar-pv-dist | 0.1538 | 0.1538 | 0.4109 | 0.4109 |
| onshore-wind | 0.3329 | 0.3329 | 0.1895 | 0.1895 |
| offshore-wind | 0.3735 | 0.3735 | 0.1890 | 0.1890 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.143

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 24382 | 2018-02-06 10:00:00 | 16289 |
| -7 | 24557 | 2018-01-04 18:00:00 | 16289 |
| 0 | 24637 | 2018-02-06 09:00:00 | 16289 |
| 7 | 24519 | 2018-02-07 09:00:00 | 16289 |
| 14 | 25251 | 2018-02-06 10:00:00 | 16289 |

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
| efs | 50516.5 | 8370 | 5767 | 1343 | 1.45 |
| flat | 50516.5 | 5767 | 5767 | 0 | 1.00 |
| cambium_residual | 50516.5 | 12958 | 5767 | 1906 | 2.25 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
