# Manual downloads

Files in this folder are inputs that the pipeline cannot fetch automatically. Each new file should be sanity-checked before committing — see the per-dataset notes below.

> **Filename rules.** The pipeline mirrors files matching certain prefixes into the DemandCast clone (see `DEMANDCAST_MANUAL_FILE_PREFIXES` in `energy_timeslice_pipeline.py`). Only `.csv` files are mirrored, but **DemandCast itself reads any file** in its `manual_downloads/` folder whose name starts with the configured prefix and tries to parse it as a CSV. Keep documentation, notes, and other non-CSV artifacts (like this README) named so they do **not** start with `KRO`, `EPIAS`, `eskom`, `NITI`, or `NTDC`. The safest convention is the existing one: a single shared `README.md` for all metadata.

## Sources

### KRO_demand_*.csv — South Korea hourly electricity demand

- **Publisher:** Korea Power Exchange (한국전력거래소 / KPX)
- **Portal:** Korean Open Government Data — https://www.data.go.kr/
- **Dataset page:** https://www.data.go.kr/data/15065266/fileData.do#layer_data_infomation
- **Dataset name (Korean):** 시간별 전력수요량 ("Hourly Electricity Demand")
- **License:** Korean Open Government Data terms — verify at https://www.data.go.kr/ugs/selectPublicDataUseGuideView.do
- **Format:** EUC-KR-encoded CSV. Header is `날짜,1시,2시,…,24시` (Date, Hour 1, …, Hour 24). One row per day; columns hold demand in MW.
- **Filename convention:** `KRO_demand_<YYYY>.csv` — one file per calendar year. The `KRO` prefix is required because DemandCast's `krogd.py` retriever scans for it.
- **Sanity-checks before committing a new year:**
  - First data row's date matches the filename year.
  - No trailing all-comma blank row (data.go.kr exports have been observed to include one).
  - If you strip blank rows manually, do it in **byte mode** to preserve the EUC-KR encoding of the Korean column headers.

### CN_hourly_demand_2015_2024.csv — China national hourly electricity demand

- **Citation:** Yi, B., Luo, Q., Zhang, S., Ji, Y., Yu, S. & Fan, Y. (2026). *Hourly electricity load curve dataset for Chinese provinces derived from meteorological variables.* **Scientific Data 13, 978.** https://doi.org/10.1038/s41597-026-07327-8
- **Data repository:** figshare — https://doi.org/10.6084/m9.figshare.29832701
- **License:** **CC BY-NC-ND 4.0** (Attribution–NonCommercial–NoDerivatives). Stricter than every other source in this folder: non-commercial use only, and no distribution of derivatives. Confirm with the publisher that the intended use is permitted **before** publishing anything derived from it, and cite it in any output that uses it.
- **Coverage:** 31 provincial-level regions (excludes Hong Kong, Macao, Taiwan), hourly, 2015–2024. Published units are **GWh per hour**; local time (CST, UTC+8).
- **Method (upstream):** 2018 load data from China's National Development and Reform Commission regressed on hourly meteorology (temperature, wind speed, solar radiation, relative humidity) via building-adjusted internal temperature (BAIT) heating/cooling degree-days, with province-specific power coefficients and regional threshold temperatures; extended to other years using annual electricity demand and air-conditioner ownership. **A reconstruction, not a metered series.**
- **How this file is produced:** the published workbook (`Data output.xlsx`, ~42 MB) is **not committed** — it is too large and its license restricts redistribution. Convert your own copy:
  ```
  python scripts/build_china_hourly_demand.py --source "<path>/Data output.xlsx"
  ```
  which sums the 31 provinces to a national series, converts GWh/h → MW, and writes this CSV plus `CN_hourly_demand_2015_2024_coverage.csv` (per-year hours, missing cells, annual TWh, mean/peak GW).
- **Filename note:** the `CN_` prefix is deliberately *not* one of the `DEMANDCAST_MANUAL_FILE_PREFIXES`, so this file is read directly by the pipeline (`load_local_demand_series`) rather than mirrored into the DemandCast clone.
- **When it is used:** only for China runs whose year/window is anything other than `year=2018, last_n_years=1` — see `CLAUDE.md` §1 "China observed-demand source".
- **Sanity-checks before committing a refresh:**
  - The coverage report shows `hours == expected_hours` for every year (8,784 in leap years) and `n_missing_cells == 0`.
  - Annual totals track CEC/NBS published national consumption (2018 ≈ 6,900 TWh, 2024 ≈ 9,854 TWh at the time of writing).
  - Annual load factors land in a plausible 0.70–0.78 band.

### EDGAR_*.xlsx, EDGAR_*.zip — EDGAR / IEA emissions reference data

- **Publisher:** European Commission Joint Research Centre, EDGAR project; with IEA energy combustion CO₂.
- **Citation source:** https://edgar.jrc.ec.europa.eu/
- **License:** Verify on the EDGAR site before redistribution.
- **Use:** Reference data carried alongside the project; not currently consumed by the pipeline directly.

### 1.A.3.e.i Pipeline transport 2023 FINAL.pdf

- **Publisher:** EDGAR documentation booklet (sector 1.A.3.e.i — pipeline transport).
- **Use:** Reference document only.

---

**Treat all citations and license claims as starting points for review** — verify against the publishers' own pages before relying on derived results in any work product. Contact **IT & Systems (itsystems@energyinnovation.org)** before automating any new external data fetches.
