# Validation report - US-SC

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **85.7 TWh**
- Peak hour: **2018-07-10 11:00:00** at **14.7 GW**
- Cluster NRMSE: **0.424**

## Days per timeslice

- Winter: 29
- Spring: 140
- Summer: 89
- Fall: 76
- Summer Peak: 15
- Winter Peak: 16

## Top-5 peak days

- Summer Peak: [152, 184, 191, 193, 194, 195, 199, 200, 201, 212, 221, 229, 241, 242, 243]
- Winter Peak: [9, 10, 11, 12, 16, 17, 19, 23, 27, 38, 341, 345, 346, 356, 361, 362]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 4011749.71 | 4011749.71 | 0.0 | 0.0 |
| residential-cooling | 4995864.6 | 4995864.6 | 0.0 | 0.0 |
| residential-lighting | 1548947.83 | 1548947.83 | 0.0 | 0.0 |
| residential-appliances | 9525527.55 | 9525527.55 | -0.0 | -0.0 |
| residential-other | 13260756.15 | 13260756.15 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 353147.71 | 353147.71 | -0.0 | -0.0 |
| commercial-cooling | 6086049.24 | 6086049.24 | -0.0 | -0.0 |
| commercial-lighting | 2589557.44 | 2589557.44 | 0.0 | 0.0 |
| commercial-appliances | 4794783.12 | 4794783.12 | 0.0 | 0.0 |
| commercial-other | 10646160.61 | 10646160.61 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 136708.21 | 136708.21 | 0.0 | 0.0 |
| HDVs | 2759.53 | 2759.53 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 27755249.64 | 27755249.64 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.072544 | 483.51 | 8760 |
| Winter | 0.089195 | 419.05 | 696 |
| Spring | 0.089289 | 475.0 | 3360 |
| Summer | 0.092469 | 527.57 | 2136 |
| Fall | 0.119604 | 547.48 | 1824 |
| Summer Peak | 0.040479 | 241.99 | 360 |
| Winter Peak | 0.083335 | 352.4 | 384 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.111201 | 312.08 | 4011749.71 |
| residential-cooling | 0.157322 | 332.96 | 4995864.6 |
| residential-lighting | 0.065731 | 22.38 | 1548947.83 |
| residential-appliances | 0.087934 | 104.5 | 9525527.55 |
| residential-other | 0.112991 | 72.8 | 13260756.15 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.084919 | 26.82 | 353147.71 |
| commercial-cooling | 0.118374 | 167.67 | 6086049.24 |
| commercial-lighting | 0.14902 | 32.77 | 2589557.44 |
| commercial-appliances | 0.078775 | 50.13 | 4794783.12 |
| commercial-other | 0.18667 | 99.51 | 10646160.61 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.046603 | 1.48 | 136708.21 |
| HDVs | 0.072417 | 0.02 | 2759.53 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.144433 | 282.18 | 27755249.64 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 13793.28 | 14381.83 | 0.9591 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 13793.28 | 13860.59 | 0.9951 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 13279.26 | 13368.33 | 0.9933 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2545.37 | 2860.39 | 0.8899 |  |
| category_peak_commercial-cooling | 2217.54 | 2372.24 | 0.9348 |  |
| category_peak_residential-heating | 3138.75 | 3745.77 | 0.8379 |  |
| category_peak_commercial-heating | 374.94 | 439.37 | 0.8534 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.82 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 13702.45 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 13131.1 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 13960.71 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 13393.66 | 13493.15 | 0.9926 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 13393.66 | 12853.3 | 1.042 |  |
| winter_peak_net_load | 13119.36 | 12998.12 | 1.0093 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 325.99 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 525.76 | 438 | top 5% of LDC = top ~438 hours |
| overall | 180.96 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0323 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 16 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 13662.14 | shifted gen by -14d; peak hour 2018-07-19 16:00:00 |
| net_load_peak_shift_-7d | 13664.18 | shifted gen by -7d; peak hour 2018-01-16 09:00:00 |
| net_load_peak_shift_0d | 13607.36 | shifted gen by 0d; peak hour 2018-12-27 08:00:00 |
| net_load_peak_shift_7d | 13806.36 | shifted gen by 7d; peak hour 2018-01-19 09:00:00 |
| net_load_peak_shift_14d | 13626.64 | shifted gen by 14d; peak hour 2018-01-16 07:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| SC_total_annual_TWh | 85.71 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| SC_solar_pv_annual_TWh | 4.7478 | 4.7478 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| SC_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 1606.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 873.9 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2444 | 0.2444 | 0.5683 | 0.5683 |
| solar-pv-dist | 0.1708 | 0.1708 | 0.3954 | 0.3954 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.032

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 13662 | 2018-07-19 16:00:00 | 9242 |
| -7 | 13664 | 2018-01-16 09:00:00 | 9242 |
| 0 | 13607 | 2018-12-27 08:00:00 | 9242 |
| 7 | 13806 | 2018-01-19 09:00:00 | 9242 |
| 14 | 13627 | 2018-01-16 07:00:00 | 9242 |

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
| efs | 27755.2 | 4643 | 3168 | 731 | 1.47 |
| flat | 27755.2 | 3168 | 3168 | 0 | 1.00 |
| cambium_residual | 27755.2 | 6644 | 3168 | 956 | 2.10 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
