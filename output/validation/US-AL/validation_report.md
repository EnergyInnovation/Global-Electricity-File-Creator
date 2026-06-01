# Validation report - US-AL

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **88.0 TWh**
- Peak hour: **2018-06-22 13:00:00** at **14.6 GW**
- Cluster NRMSE: **0.360**

## Days per timeslice

- Winter: 27
- Spring: 85
- Summer: 127
- Fall: 92
- Summer Peak: 25
- Winter Peak: 9

## Top-5 peak days

- Summer Peak: [166, 172, 173, 179, 184, 185, 192, 193, 194, 200, 201, 205, 206, 207, 208, 214, 220, 228, 229, 233, 234, 235, 236, 240, 241]
- Winter Peak: [9, 10, 11, 12, 23, 33, 34, 37, 361]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 3539733.29 | 3539733.29 | 0.0 | 0.0 |
| residential-cooling | 5607672.92 | 5607672.92 | 0.0 | 0.0 |
| residential-lighting | 1214554.51 | 1214554.51 | 0.0 | 0.0 |
| residential-appliances | 8695339.98 | 8695339.98 | 0.0 | 0.0 |
| residential-other | 13948007.03 | 13948007.03 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 397098.48 | 397098.48 | 0.0 | 0.0 |
| commercial-cooling | 5247245.02 | 5247245.02 | 0.0 | 0.0 |
| commercial-lighting | 2358177.02 | 2358177.02 | 0.0 | 0.0 |
| commercial-appliances | 3973651.82 | 3973651.82 | 0.0 | 0.0 |
| commercial-other | 10575762.02 | 10575762.02 | -0.0 | -0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 160827.14 | 160827.14 | -0.0 | -0.0 |
| HDVs | 3088.98 | 3088.98 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 32310795.13 | 32310795.13 | -0.0 | -0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.07 | 455.56 | 8760 |
| Winter | 0.090209 | 364.25 | 648 |
| Spring | 0.129572 | 565.71 | 2040 |
| Summer | 0.088281 | 459.58 | 3048 |
| Fall | 0.090692 | 467.27 | 2208 |
| Summer Peak | 0.029047 | 156.75 | 600 |
| Winter Peak | 0.084378 | 342.95 | 216 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.101783 | 304.03 | 3539733.29 |
| residential-cooling | 0.154407 | 345.51 | 5607672.92 |
| residential-lighting | 0.061163 | 15.65 | 1214554.51 |
| residential-appliances | 0.086608 | 91.99 | 8695339.98 |
| residential-other | 0.11313 | 75.84 | 13948007.03 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.080892 | 33.0 | 397098.48 |
| commercial-cooling | 0.112631 | 141.98 | 5247245.02 |
| commercial-lighting | 0.142747 | 31.5 | 2358177.02 |
| commercial-appliances | 0.09605 | 48.56 | 3973651.82 |
| commercial-other | 0.181413 | 111.2 | 10575762.02 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.042277 | 1.56 | 160827.14 |
| HDVs | 0.081849 | 0.02 | 3088.98 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.0 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.13509 | 285.41 | 32310795.13 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 14072.57 | 14461.7 | 0.9731 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 14072.57 | 14103.12 | 0.9978 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 13437.15 | 13551.17 | 0.9916 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 2606.98 | 3022.91 | 0.8624 |  |
| category_peak_commercial-cooling | 1955.32 | 2158.53 | 0.9059 |  |
| category_peak_residential-heating | 2864.76 | 3743.13 | 0.7653 |  |
| category_peak_commercial-heating | 436.16 | 532.59 | 0.8189 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 1.0 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 13874.79 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 13785.33 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 14091.86 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 13779.0 | 13953.3 | 0.9875 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 13779.0 | 13598.76 | 1.0133 |  |
| winter_peak_net_load | 13387.85 | 13406.14 | 0.9986 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 168.31 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 359.65 | 438 | top 5% of LDC = top ~438 hours |
| overall | 157.08 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | 0.0466 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 35 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 14180.41 | shifted gen by -14d; peak hour 2018-06-22 13:00:00 |
| net_load_peak_shift_-7d | 14072.82 | shifted gen by -7d; peak hour 2018-07-20 13:00:00 |
| net_load_peak_shift_0d | 14053.02 | shifted gen by 0d; peak hour 2018-07-20 13:00:00 |
| net_load_peak_shift_7d | 14232.25 | shifted gen by 7d; peak hour 2018-07-20 15:00:00 |
| net_load_peak_shift_14d | 14042.15 | shifted gen by 14d; peak hour 2018-07-20 15:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| AL_total_annual_TWh | 88.03 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| AL_solar_pv_annual_TWh | 1.7733 | 1.7733 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| AL_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 753.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 63.3 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2543 | 0.2543 | 0.5044 | 0.5044 |
| solar-pv-dist | 0.1701 | 0.1701 | 0.3397 | 0.3397 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** 0.047

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 14180 | 2018-06-22 13:00:00 | 9847 |
| -7 | 14073 | 2018-07-20 13:00:00 | 9847 |
| 0 | 14053 | 2018-07-20 13:00:00 | 9847 |
| 7 | 14232 | 2018-07-20 15:00:00 | 9847 |
| 14 | 14042 | 2018-07-20 15:00:00 | 9847 |

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
| efs | 32310.8 | 5101 | 3688 | 837 | 1.38 |
| flat | 32310.8 | 3688 | 3688 | 0 | 1.00 |
| cambium_residual | 32310.8 | 6490 | 3688 | 910 | 1.76 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
