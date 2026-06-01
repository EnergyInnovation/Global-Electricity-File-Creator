# Validation report - US-GA

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **145.1 TWh**
- Peak hour: **2018-08-17 13:00:00** at **25.2 GW**
- Cluster NRMSE: **0.408**

## Days per timeslice

- Winter: 47
- Spring: 83
- Summer: 123
- Fall: 91
- Summer Peak: 14
- Winter Peak: 7

## Top-5 peak days

- Summer Peak: [177, 178, 194, 200, 205, 214, 219, 226, 227, 228, 229, 234, 241, 243]
- Winter Peak: [9, 11, 16, 19, 36, 37, 354]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 7889194.02 | 7889194.02 | 0.0 | 0.0 |
| residential-cooling | 8815152.4 | 8815152.4 | -0.0 | -0.0 |
| residential-lighting | 2725929.07 | 2725929.07 | 0.0 | 0.0 |
| residential-appliances | 17442028.14 | 17442028.14 | 0.0 | 0.0 |
| residential-other | 24585638.92 | 24585638.92 | -0.0 | -0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 781116.65 | 781116.65 | 0.0 | 0.0 |
| commercial-cooling | 11851905.04 | 11851905.04 | 0.0 | 0.0 |
| commercial-lighting | 5351201.64 | 5351201.64 | -0.0 | -0.0 |
| commercial-appliances | 9912866.35 | 9912866.35 | 0.0 | 0.0 |
| commercial-other | 22011371.63 | 22011371.63 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 235716.19 | 235716.19 | 0.0 | 0.0 |
| HDVs | 4508.48 | 4508.48 | -0.0 | -0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 125682.52 | 125682.52 | -0.0 | -0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 33319889.21 | 33319889.21 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.073466 | 874.36 | 8760 |
| Winter | 0.081072 | 746.71 | 1128 |
| Spring | 0.086066 | 738.34 | 1992 |
| Summer | 0.090284 | 943.33 | 2952 |
| Fall | 0.116848 | 1077.36 | 2184 |
| Summer Peak | 0.037363 | 409.36 | 336 |
| Winter Peak | 0.057708 | 423.56 | 168 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.098317 | 583.61 | 7889194.02 |
| residential-cooling | 0.152726 | 546.66 | 8815152.4 |
| residential-lighting | 0.064722 | 36.49 | 2725929.07 |
| residential-appliances | 0.083802 | 172.27 | 17442028.14 |
| residential-other | 0.107121 | 120.92 | 24585638.92 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.070029 | 57.34 | 781116.65 |
| commercial-cooling | 0.109267 | 297.62 | 11851905.04 |
| commercial-lighting | 0.159828 | 64.79 | 5351201.64 |
| commercial-appliances | 0.07893 | 105.06 | 9912866.35 |
| commercial-other | 0.174643 | 195.02 | 22011371.63 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.056603 | 3.22 | 235716.19 |
| HDVs | 0.096537 | 0.03 | 4508.48 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.056603 | 1.72 | 125682.52 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.183347 | 499.4 | 33319889.21 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 24011.21 | 24703.15 | 0.972 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 23742.05 | 23871.5 | 0.9946 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 24011.21 | 24082.25 | 0.9971 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 4409.43 | 4923.08 | 0.8957 |  |
| category_peak_commercial-cooling | 4405.23 | 4750.14 | 0.9274 |  |
| category_peak_residential-heating | 6472.99 | 7314.53 | 0.8849 |  |
| category_peak_commercial-heating | 912.4 | 1021.12 | 0.8935 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.67 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 23585.06 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 22739.29 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 24057.62 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 23534.05 | 23689.91 | 0.9934 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 23283.54 | 22528.53 | 1.0335 |  |
| winter_peak_net_load | 23534.05 | 23114.51 | 1.0182 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 479.14 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 1000.9 | 438 | top 5% of LDC = top ~438 hours |
| overall | 349.44 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.0299 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 35 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 24511.77 | shifted gen by -14d; peak hour 2018-08-17 15:00:00 |
| net_load_peak_shift_-7d | 24087.94 | shifted gen by -7d; peak hour 2018-01-09 07:00:00 |
| net_load_peak_shift_0d | 24147.94 | shifted gen by 0d; peak hour 2018-01-09 07:00:00 |
| net_load_peak_shift_7d | 24260.8 | shifted gen by 7d; peak hour 2018-01-09 08:00:00 |
| net_load_peak_shift_14d | 24565.7 | shifted gen by 14d; peak hour 2018-01-09 08:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| GA_total_annual_TWh | 145.05 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| GA_solar_pv_annual_TWh | 7.5876 | 7.5876 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| GA_wind_annual_TWh | 0.0 | 0.0 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 3396.7 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 84.6 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.2509 | 0.2509 | 0.5669 | 0.5669 |
| solar-pv-dist | 0.1666 | 0.1666 | 0.3985 | 0.3985 |
| onshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.030

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 24512 | 2018-08-17 15:00:00 | 15692 |
| -7 | 24088 | 2018-01-09 07:00:00 | 15692 |
| 0 | 24148 | 2018-01-09 07:00:00 | 15692 |
| 7 | 24261 | 2018-01-09 08:00:00 | 15692 |
| 14 | 24566 | 2018-01-09 08:00:00 | 15692 |

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
| efs | 33319.9 | 5503 | 3804 | 896 | 1.45 |
| flat | 33319.9 | 3804 | 3804 | 0 | 1.00 |
| cambium_residual | 33319.9 | 7984 | 3804 | 1160 | 2.10 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
