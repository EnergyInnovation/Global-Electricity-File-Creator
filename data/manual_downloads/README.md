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
