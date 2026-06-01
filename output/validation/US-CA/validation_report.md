# Validation report - US-CA

**Generated:** state_pipeline v1.2 (consolidated workbooks + literature-standard validation suite)

## Headlines

- Total annual demand: **274.1 TWh**
- Peak hour: **2018-01-26 13:00:00** at **45.6 GW**
- Cluster NRMSE: **0.355**

## Days per timeslice

- Winter: 69
- Spring: 76
- Summer: 144
- Fall: 38
- Summer Peak: 22
- Winter Peak: 16

## Top-5 peak days

- Summer Peak: [187, 194, 196, 201, 205, 212, 213, 214, 215, 219, 220, 222, 223, 225, 226, 227, 228, 229, 236, 241, 242, 243]
- Winter Peak: [1, 2, 3, 4, 5, 9, 10, 11, 12, 24, 26, 339, 345, 346, 347, 361]

## Section 1: Energy Reconstruction (Annual)

Per category: annual input vs reconstructed sum-of-hourly. Should be ~100% match.

| category | annual_input_MWh | annual_reconstructed_MWh | abs_diff_MWh | rel_diff |
|---|---|---|---|---|
| residential-heating | 12066060.96 | 12066060.96 | 0.0 | 0.0 |
| residential-cooling | 7548212.19 | 7548212.19 | 0.0 | 0.0 |
| residential-lighting | 8077590.86 | 8077590.86 | -0.0 | -0.0 |
| residential-appliances | 32605328.25 | 32605328.25 | 0.0 | 0.0 |
| residential-other | 43346292.5 | 43346292.5 | 0.0 | 0.0 |
| residential-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| commercial-heating | 2859964.83 | 2859964.83 | -0.0 | -0.0 |
| commercial-cooling | 21575146.54 | 21575146.54 | 0.0 | 0.0 |
| commercial-lighting | 11050263.77 | 11050263.77 | 0.0 | 0.0 |
| commercial-appliances | 22796395.08 | 22796395.08 | 0.0 | 0.0 |
| commercial-other | 61905041.03 | 61905041.03 | 0.0 | 0.0 |
| commercial-envelope | 0.0 | 0.0 | 0.0 | 0.0 |
| LDVs | 679164.54 | 679164.54 | 0.0 | 0.0 |
| HDVs | 10982.76 | 10982.76 | 0.0 | 0.0 |
| aircraft | 0.0 | 0.0 | 0.0 | 0.0 |
| rail | 790977.41 | 790977.41 | 0.0 | 0.0 |
| ships | 0.0 | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 | 0.0 |
| industry | 48789949.3 | 48789949.3 | 0.0 | 0.0 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 | 0.0 |

## Section 2: Hourly NRMSE - Total and Per-Slice

Lower is better. Non-peak slices only since peak slices have 0 days_per_timeslice.

| scope | NRMSE | MAE_MWh | n_hours |
|---|---|---|---|
| total_year | 0.073789 | 1622.92 | 8760 |
| Winter | 0.122983 | 2490.6 | 1656 |
| Spring | 0.068081 | 1387.63 | 1824 |
| Summer | 0.070734 | 1411.17 | 3456 |
| Fall | 0.110889 | 2127.39 | 912 |
| Summer Peak | 0.044636 | 747.71 | 528 |
| Winter Peak | 0.048942 | 909.84 | 384 |

## Section 3: Per-end-use NRMSE

Identifies categories that are poorly fit.

| category | NRMSE | MAE_MWh | annual_MWh |
|---|---|---|---|
| residential-heating | 0.116192 | 766.51 | 12066060.96 |
| residential-cooling | 0.128044 | 404.01 | 7548212.19 |
| residential-lighting | 0.059865 | 95.13 | 8077590.86 |
| residential-appliances | 0.061618 | 189.83 | 32605328.25 |
| residential-other | 0.099286 | 220.88 | 43346292.5 |
| residential-envelope | 0.0 | 0.0 | 0.0 |
| commercial-heating | 0.113389 | 160.73 | 2859964.83 |
| commercial-cooling | 0.102148 | 267.26 | 21575146.54 |
| commercial-lighting | 0.149919 | 164.71 | 11050263.77 |
| commercial-appliances | 0.106023 | 314.53 | 22796395.08 |
| commercial-other | 0.103475 | 693.89 | 61905041.03 |
| commercial-envelope | 0.0 | 0.0 | 0.0 |
| LDVs | 0.059238 | 9.87 | 679164.54 |
| HDVs | 0.096575 | 0.07 | 10982.76 |
| aircraft | 0.0 | 0.0 | 0.0 |
| rail | 0.059238 | 11.49 | 790977.41 |
| ships | 0.0 | 0.0 | 0.0 |
| motorbikes | 0.0 | 0.0 | 0.0 |
| industry | 0.197129 | 864.3 | 48789949.3 |
| district-heat-hydrogen | 0.0 | 0.0 | 0.0 |
| geoeng | 0.0 | 0.0 | 0.0 |
| datacenters | 0.0 | 0.0 | 0.0 |

## Section 4: Peak Hour Preservation

Capacity adequacy critical. Target ratio 0.95-1.05.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| system_peak_hour | 43726.26 | 45311.37 | 0.965 | representative max vs top-5 days actual peak average |
| summer_peak_slice | 43564.31 | 43564.31 | 1.0 | Summer Peak slice reconstructed peak vs actual top-5 average |
| winter_peak_slice | 43726.26 | 43767.7 | 0.9991 | Winter Peak slice reconstructed peak vs actual top-5 average |
| category_peak_residential-cooling | 4379.27 | 4871.5 | 0.899 |  |
| category_peak_commercial-cooling | 5174.92 | 5600.08 | 0.9241 |  |
| category_peak_residential-heating | 7418.31 | 9110.01 | 0.8143 |  |
| category_peak_commercial-heating | 1620.95 | 2041.38 | 0.794 |  |

## Section 5: Top-100 Hour Capture

Fraction of top-100 actual hours where reconstructed >= 90% of actual.

| metric | value | note |
|---|---|---|
| top_100_hours_capture_pct | 0.97 | fraction of top-100 actual hours where recon >= 90% of actual |
| top_100_actual_min_MW | 43528.2 | lowest MW threshold of top-100 actual hours |
| top_100_recon_avg_MW | 42188.92 | avg reconstructed MW at top-100 actual hour positions |
| top_100_actual_avg_MW | 44108.4 | avg actual MW at top-100 hours |

## Section 6: Net Load Peak Preservation

Critical for VRE-heavy systems where investment depends on net load.

| metric | representative_MW | actual_MW | preservation_ratio | note |
|---|---|---|---|---|
| net_load_peak_hour | 40294.86 | 40872.19 | 0.9859 | representative net-load max vs top-5 days actual peak average |
| summer_peak_net_load | 38967.75 | 38104.78 | 1.0226 |  |
| winter_peak_net_load | 40294.86 | 39629.34 | 1.0168 |  |

## Section 7: Load Duration Curve Fit

RMSE on top 1% (87 hours), top 5% (438 hours), and overall.

| scope | RMSE_MW | n_hours | note |
|---|---|---|---|
| top_1pct | 818.4 | 88 | top 1% of LDC = top ~87 hours |
| top_5pct | 1416.62 | 438 | top 5% of LDC = top ~438 hours |
| overall | 583.85 | 8760 | full 8760 LDC |

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
| summer_daily_corr_buildings_vs_solar_cf | -0.3695 | correlation of daily summer building demand vs daily solar CF |
| peak_day_buildings_doy | 229 | day-of-year of peak building demand day |
| net_load_peak_shift_-14d | 41062.65 | shifted gen by -14d; peak hour 2018-12-28 16:00:00 |
| net_load_peak_shift_-7d | 42021.49 | shifted gen by -7d; peak hour 2018-01-03 16:00:00 |
| net_load_peak_shift_0d | 41860.99 | shifted gen by 0d; peak hour 2018-01-03 16:00:00 |
| net_load_peak_shift_7d | 41854.69 | shifted gen by 7d; peak hour 2018-01-03 16:00:00 |
| net_load_peak_shift_14d | 40896.55 | shifted gen by 14d; peak hour 2018-12-12 16:00:00 |

## Section 10: External Cross-Checks

Pipeline value vs reference (EIA SEDS, Cambium). Verify against primary sources.

| name | pipeline_value | reference_value | rel_diff | note |
|---|---|---|---|---|
| CA_total_annual_TWh | 274.1 |  |  | EIA SEDS / EIA-923 cross-check; verify against primary source |
| CA_solar_pv_annual_TWh | 76.0802 | 76.0802 | 0.0 | Pipeline derived directly from Cambium hourly CFs * capacity; reference = same Cambium math (sanity self-check) |
| CA_wind_annual_TWh | 14.7521 | 14.7521 | 0.0 | Pipeline derived from Cambium hourly CFs * capacity for onshore + offshore wind; reference = same Cambium math |
| cambium_capacity_solar-pv_MW | 20194.2 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_solar-pv-dist_MW | 13052.4 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_onshore-wind_MW | 6476.0 |  |  | staff-review against Cambium Scenario Viewer |
| cambium_capacity_offshore-wind_MW | 0.0 |  |  | staff-review against Cambium Scenario Viewer |


## Cambium curtailment add-back

**Finding:** Cambium 2022 state-level files (hourly + annual) contain NO explicit curtailment columns. Per-tech generation is reported after curtailment.

**v1.1 implementation:** optional per-state, per-tech CF scaling factor in preset YAML key `curtailment_addback`. Effective CF = `cf_observed / (1 - f_t)`, clipped to [0,1].

**Active addback factors:** (empty / no scaling) — VA has low VRE share; impact is negligible. For high-VRE states (CA, TX, etc.) operators should set non-zero values.

**Per-tech CF before/after (informational):**

| tech | annual_CF_raw | annual_CF_addback | summer_peak_CF_raw | summer_peak_CF_addback |
|---|---|---|---|---|
| solar-pv | 0.3097 | 0.3097 | 0.7053 | 0.7053 |
| solar-pv-dist | 0.1862 | 0.1862 | 0.4606 | 0.4606 |
| onshore-wind | 0.2600 | 0.2600 | 0.2942 | 0.2942 |
| offshore-wind | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Weather year alignment

**Mismatch:** ResStock/ComStock use TMY3 (1991-2005 synthesized typical year). Cambium 2022 uses 2012 actual weather. EFS uses 2012 actual weather. Pipeline runs them on a common 2018 calendar, but the underlying weather realizations differ. For clustering on net load, the per-hour correlation between demand and renewable generation is therefore artificial.

**Diagnostic - summer daily correlation (buildings demand vs solar CF):** -0.369

On hot summer days both should be high (sunny, hot). Weak/negative correlation flags weather-year decoupling.

**Net-load peak under +/-7 and +/-14 day shifts of Cambium gen:**

| shift_days | peak_MWh | peak_hour | mean_MWh |
|---|---|---|---|
| -14 | 41063 | 2018-12-28 16:00:00 | 20921 |
| -7 | 42021 | 2018-01-03 16:00:00 | 20921 |
| 0 | 41861 | 2018-01-03 16:00:00 | 20921 |
| 7 | 41855 | 2018-01-03 16:00:00 | 20921 |
| 14 | 40897 | 2018-12-12 16:00:00 | 20921 |

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
| efs | 48789.9 | 8061 | 5570 | 1396 | 1.45 |
| flat | 48789.9 | 5570 | 5570 | 0 | 1.00 |
| cambium_residual | 48789.9 | 16355 | 5570 | 2860 | 2.94 |

Default is `flat`: lowest peak, lowest std, no spurious weather-driven variation.

## Notes & caveats

- Weather year mismatch: see Weather year alignment section above.
- Datacenters annual = 0 (no per-state DC source integrated v1).
- District-heat-hydrogen, geoeng = 0 in start year (ramp-up post-2030).
- SYSHECF non-variable techs use legacy template values where present;
  fallback to flat default CFs otherwise.
- All outputs are inputs for staff review; verify against EIA SEDS + EIA-923
  before any work product use.
