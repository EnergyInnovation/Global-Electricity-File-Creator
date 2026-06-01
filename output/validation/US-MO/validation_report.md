# Validation report - US-MO

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **81.1 TWh**
- Peak hour: **2018-01-05 11:00:00** at **14.1 GW**
- Cluster NRMSE: **0.446**

## Days per timeslice

- Winter: 47
- Spring: 81
- Summer: 100
- Fall: 92
- Summer Peak: 33
- Winter Peak: 12

## Top-5 peak days

- Summer Peak: [158, 184, 185, 186, 187, 188, 191, 192, 193, 194, 197, 198, 199, 200, 201, 202, 213, 214, 216, 219, 220, 221, 222, 228, 229, 233, 234, 235, 236, 240, 241, 242, 243]
- Winter Peak: [5, 9, 10, 25, 26, 33, 34, 37, 38, 39, 40, 353]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 5293839.39 | 5293839.39 | 0.0 | 0.0 |
| residential-cooling | 4683713.36 | 4683713.36 | 0.0 | 0.0 |
| residential-lighting | 1912242.09 | 1912242.09 | -0.0 | -0.0 |
| residential-appliances | 9727432.59 | 9727432.59 | 0.0 | 0.0 |
| residential-other | 15795164.13 | 15795164.13 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 968364.6 | 968364.6 | 0.0 | 0.0 |
| commercial-cooling | 6065064.48 | 6065064.48 | 0.0 | 0.0 |
| commercial-lighting | 2716204.57 | 2716204.57 | 0.0 | 0.0 |
| commercial-appliances | 3958382.18 | 3958382.18 | 0.0 | 0.0 |
| commercial-other | 16379894.49 | 16379894.49 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 154271.07 | 154271.07 | 0.0 | 0.0 |
| HDVs | 3629.63 | 3629.63 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 47736.65 | 47736.65 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 13417065.73 | 13417065.73 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.080724 | 541.75 | 8760 |
| Winter | 0.080457 | 441.0 | 1128 |
| Spring | 0.095958 | 543.45 | 1944 |
| Summer | 0.124582 | 607.64 | 2400 |
| Fall | 0.107756 | 631.35 | 2208 |
| Summer Peak | 0.05588 | 329.12 | 792 |
| Winter Peak | 0.061242 | 273.67 | 288 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.143418 | 365.85 | 5293839.39 |
| residential-cooling | 0.143025 | 304.02 | 4683713.36 |
| residential-lighting | 0.063847 | 24.92 | 1912242.09 |
| residential-appliances | 0.078739 | 85.85 | 9727432.59 |
| residential-other | 0.100108 | 71.79 | 15795164.13 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.11501 | 65.97 | 968364.6 |
| commercial-cooling | 0.106529 | 162.68 | 6065064.48 |
| commercial-lighting | 0.159543 | 38.92 | 2716204.57 |
| commercial-appliances | 0.084311 | 43.37 | 3958382.18 |
| commercial-other | 0.174585 | 155.1 | 16379894.49 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.06303 | 2.65 | 154271.07 |
| HDVs | 0.104382 | 0.03 | 3629.63 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.06303 | 0.82 | 47736.65 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.208864 | 247.39 | 13417065.73 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 13278.45 | 13873.09 | 0.9571 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 12700.12 | 12786.69 | 0.9932 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 13278.45 | 13318.6 | 0.997 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2463.62 | 2998.67 | 0.8216 |  |
| category_peak_commercial-cooling | 2207.54 | 2595.97 | 0.8504 |  |
| category_peak_residential-heating | 2846.82 | 3333.6 | 0.854 |  |
| category_peak_commercial-heating | 681.68 | 776.41 | 0.878 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.97 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 13096.08 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 12709.07 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 13405.21 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 13197.35 | 13491.72 | 0.9782 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 12608.9 | 12433.93 | 1.0141 |  |
| winter_peak_net_load | 13197.35 | 13087.53 | 1.0084 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 486.24 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 273.6 | 438 | top 5% of LDC = top ~438 hours |
| overall | 198.53 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0893 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 6 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 13609.22 | shifted gen by -14d; peak hour 2018-02-02 10:00:00 |
| net_load_peak_shift_-7d | 13832.82 | shifted gen by -7d; peak hour 2018-02-02 10:00:00 |
| net_load_peak_shift_0d | 13824.12 | shifted gen by 0d; peak hour 2018-02-02 10:00:00 |
| net_load_peak_shift_7d | 13805.32 | shifted gen by 7d; peak hour 2018-02-02 10:00:00 |
| net_load_peak_shift_14d | 13285.63 | shifted gen by 14d; peak hour 2018-01-06 19:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| MO_total_annual_TWh | 81.12 | 80.0 | 0.014 | EIA SEDS 2022 MO total electricity consumption ~80 TWh; staff verify against current SEDS release |
| MO_solar_pv_annual_TWh | 0.4971 | 0.4971 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| MO_wind_annual_TWh | 7.8457 | 7.8457 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 78.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 217.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 2227.8 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2536 | 0.2536 | 0.6106 | 0.6106 |
| solar-pv-dist | 0.1697 | 0.1697 | 0.4077 | 0.4077 |
| onshore-wind | 0.4020 | 0.4020 | 0.2086 | 0.2086 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.089

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 13609 | 2018-02-02 10:00:00 | 8308 |
| -7 | 13833 | 2018-02-02 10:00:00 | 8308 |
| 0 | 13824 | 2018-02-02 10:00:00 | 8308 |
| 7 | 13805 | 2018-02-02 10:00:00 | 8308 |
| 14 | 13286 | 2018-01-06 19:00:00 | 8308 |

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
| efs | 13417.1 | 2242 | 1532 | 357 | 1.46 |
| flat | 13417.1 | 1532 | 1532 | 0 | 1.00 |
| cambium_residual | 13417.1 | 4117 | 1532 | 640 | 2.69 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
