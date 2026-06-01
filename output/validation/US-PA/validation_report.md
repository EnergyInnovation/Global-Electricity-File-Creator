# Validation report - US-PA

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **146.3 TWh**
- Peak hour: **2018-01-23 10:00:00** at **24.4 GW**
- Cluster NRMSE: **0.363**

## Days per timeslice

- Winter: 53
- Spring: 111
- Summer: 78
- Fall: 90
- Summer Peak: 16
- Winter Peak: 17

## Top-5 peak days

- Summer Peak: [158, 159, 193, 194, 198, 199, 201, 202, 208, 212, 215, 216, 220, 221, 222, 228]
- Winter Peak: [5, 9, 10, 11, 16, 18, 19, 23, 26, 31, 37, 39, 40, 46, 47, 348, 361]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 8777904.45 | 8777904.45 | 0.0 | 0.0 |
| residential-cooling | 5769053.34 | 5769053.34 | 0.0 | 0.0 |
| residential-lighting | 4138007.03 | 4138007.03 | 0.0 | 0.0 |
| residential-appliances | 17333909.73 | 17333909.73 | 0.0 | 0.0 |
| residential-other | 21317086.75 | 21317086.75 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 894240.91 | 894240.91 | 0.0 | 0.0 |
| commercial-cooling | 7559847.6 | 7559847.6 | 0.0 | 0.0 |
| commercial-lighting | 4271746.78 | 4271746.78 | 0.0 | 0.0 |
| commercial-appliances | 6301055.1 | 6301055.1 | 0.0 | 0.0 |
| commercial-other | 19006271.98 | 19006271.98 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 224162.42 | 224162.42 | 0.0 | 0.0 |
| HDVs | 4695.24 | 4695.24 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 221670.3 | 221670.3 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 50458899.47 | 50458899.47 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.068098 | 768.66 | 8760 |
| Winter | 0.09479 | 888.76 | 1272 |
| Spring | 0.089164 | 731.22 | 2664 |
| Summer | 0.11756 | 889.61 | 1872 |
| Fall | 0.092649 | 776.79 | 2160 |
| Summer Peak | 0.038141 | 298.35 | 384 |
| Winter Peak | 0.060206 | 483.29 | 408 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.169562 | 636.79 | 8777904.45 |
| residential-cooling | 0.153929 | 345.71 | 5769053.34 |
| residential-lighting | 0.068394 | 58.55 | 4138007.03 |
| residential-appliances | 0.077106 | 151.67 | 17333909.73 |
| residential-other | 0.1096 | 113.44 | 21317086.75 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.130276 | 65.4 | 894240.91 |
| commercial-cooling | 0.109945 | 180.77 | 7559847.6 |
| commercial-lighting | 0.155888 | 61.19 | 4271746.78 |
| commercial-appliances | 0.077093 | 65.02 | 6301055.1 |
| commercial-other | 0.181164 | 176.18 | 19006271.98 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.042359 | 2.09 | 224162.42 |
| HDVs | 0.082623 | 0.02 | 4695.24 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.042359 | 2.07 | 221670.3 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.163317 | 511.43 | 50458899.47 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 23671.49 | 24308.3 | 0.9738 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 21197.99 | 21293.85 | 0.9955 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 23671.49 | 23721.33 | 0.9979 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2732.23 | 3247.45 | 0.8413 |  |
| category_peak_commercial-cooling | 2542.84 | 2891.77 | 0.8793 |  |
| category_peak_residential-heating | 4081.62 | 4712.28 | 0.8662 |  |
| category_peak_commercial-heating | 576.29 | 667.67 | 0.8631 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 1.0 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 23317.38 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 22795.33 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 23753.38 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 23117.59 | 23058.85 | 1.0025 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 20595.89 | 20288.53 | 1.0151 |  |
| winter_peak_net_load | 23117.59 | 22473.74 | 1.0286 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 425.58 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 492.7 | 438 | top 5% of LDC = top ~438 hours |
| overall | 253.32 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0306 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 18 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 23438.26 | shifted gen by -14d; peak hour 2018-01-23 09:00:00 |
| net_load_peak_shift_-7d | 23572.99 | shifted gen by -7d; peak hour 2018-01-09 18:00:00 |
| net_load_peak_shift_0d | 23323.56 | shifted gen by 0d; peak hour 2018-01-09 09:00:00 |
| net_load_peak_shift_7d | 23603.73 | shifted gen by 7d; peak hour 2018-01-23 18:00:00 |
| net_load_peak_shift_14d | 23612.32 | shifted gen by 14d; peak hour 2018-01-10 09:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| PA_total_annual_TWh | 146.28 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| PA_solar_pv_annual_TWh | 2.9967 | 2.9967 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| PA_wind_annual_TWh | 9.5532 | 9.5532 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 439.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 1580.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 2771.1 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2229 | 0.2229 | 0.5592 | 0.5592 |
| solar-pv-dist | 0.1545 | 0.1545 | 0.3647 | 0.3647 |
| onshore-wind | 0.3935 | 0.3935 | 0.2520 | 0.2520 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.031

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 23438 | 2018-01-23 09:00:00 | 15266 |
| -7 | 23573 | 2018-01-09 18:00:00 | 15266 |
| 0 | 23324 | 2018-01-09 09:00:00 | 15266 |
| 7 | 23604 | 2018-01-23 18:00:00 | 15266 |
| 14 | 23612 | 2018-01-10 09:00:00 | 15266 |

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
| efs | 50458.9 | 8080 | 5760 | 1443 | 1.40 |
| flat | 50458.9 | 5760 | 5760 | 0 | 1.00 |
| cambium_residual | 50458.9 | 12438 | 5760 | 1890 | 2.16 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
