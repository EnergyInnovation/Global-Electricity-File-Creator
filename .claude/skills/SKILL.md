---
name: build-input-xlsx
description: Build a self-contained Excel workbook (.xlsx) that serves as a model input file — raw source data pasted in, all derived values computed via Excel formulas referencing the source tabs, plus an "About" tab documenting sources and methodology. Use whenever the user asks to "build an input data xlsx", "create a self-documenting Excel workbook for model inputs", "wire up an .xlsx so calculations flow from source data", "make an input xlsx with computed formulas", or similar. Especially useful for EPS Vensim model inputs (SHELF, SYSHECF) where the workbook needs to be inspectable in Excel and recompute when source data or assumptions change.
---

# Build a self-contained input data .xlsx

End-to-end pattern for creating an Excel workbook that is itself a derivation: raw source data lives in dedicated tabs, all output values are computed by Excel formulas referencing the source tabs, and the workbook documents itself via an "About" tab. Edit any source value or assumption cell → all outputs recompute.

This skill exists because building these workbooks well has several non-obvious gotchas (XLOOKUP vs VLOOKUP, openpyxl quirks, tab-color encoding, source-data layout) that have repeatedly tripped up sessions.

## When to use vs. when not to use

Use this skill when:
- The user wants an Excel workbook that derives outputs from source data via formulas (not static values)
- The user wants the workbook to be inspectable / editable in Excel (change a source value, watch outputs recompute)
- The user mentions "EPS input files" (SHELF, SYSHECF) or similar model input workbooks
- The user wants to update model inputs annually as source data refreshes

Don't use this skill when:
- The user just wants to convert a CSV to xlsx as-is (use openpyxl directly, simpler)
- The user wants a static report / dashboard (different pattern)
- The output is consumed only by another script that already reads the CSV (the formula derivation is wasted)

## Workbook design pattern

The canonical structure (in order from left to right):

1. **About** — methodology, sources, version. First tab.
2. **Editable parameter tabs** — small lookup tables the user might want to tweak (e.g., calibration targets, year selectors, scenario toggles).
3. **Source data tabs** — RAW source files pasted verbatim. One per source file.
4. **Output tabs** — formulas reference source data + parameter tabs. **Color these dark blue** to visually separate from inputs.

### About tab — exact format

The user has a specific convention for the About tab that recurs:

| Row | Col A | Col B |
|---|---|---|
| 1 | `<ABBREVIATION> <Full File Name Without Extension>` **(bold, default size 11)** | (blank) |
| 2 | (blank) | (blank) |
| 3 | `Sources:` **(bold)** | First source's *purpose* (e.g., "Hourly Generation by Electricity Type") **(bold, gray fill #D9D9D9)** |
| 4 | (blank) | Source name (e.g., "NREL") |
| 5 | (blank) | Publication name (e.g., "NREL Cambium Scenarios 2024") |
| 6 | (blank) | Year of publication (number, e.g., 2024) |
| 7 | (blank) | URL — as a clickable hyperlink (blue underlined) |
| 8 | (blank) | Important info / notes about this source (wrap text) |
| 9 | (blank) | (blank — separator between sources) |
| 10 | (blank) | Next source's *purpose* (bold, gray fill) |
| 11–15 | (blank) | …repeat 6-cell pattern… |
| ... | ... | ...all sources... |
| N | (blank) | (blank) |
| N+1 | (blank) | (blank — blank row before Notes) |
| N+2 | `Notes:` **(bold)** | (blank) |
| N+3 | Methodology section label **(bold)** | Methodology section text (wrap, left-aligned) |
| N+4+ | More section labels | More section text |

**Formatting rules that matter:**
- A1: bold, **default size** (do NOT enlarge). Format: `<ABBR> <File Name Without Extension>`
- All column B text cells: `Alignment(horizontal='left', vertical='top', wrap_text=True)`
- Column A width ~14; column B width ~110
- Purpose cells (source headers in B): bold + gray fill (`PatternFill(start_color='D9D9D9', fill_type='solid')`)
- URL cells: `cell.hyperlink = url`, font `Font(color='0563C1', underline='single')`
- Section headers like "Sources:" and "Notes:" in column A: just bold, no fill, no extra size

### Source data tabs

For each source file, create one tab that **pastes the raw source verbatim** — every row, every column, including metadata header rows.

- Don't skip "useless" columns. The user wants the full source visible.
- If the source is an xlsx, load it with openpyxl and write each cell as-is.
- If the source is a CSV, read with `csv.reader`, write each cell; cast to float for data rows where possible (skip metadata rows).
- After the source columns, **add derived columns at the right** for things the output tabs need:
  - For hourly time-series sources: `day_of_year`, `hour_of_day`, `slice` (or `season` etc.)
  - For per-tech sources: derived `CF_<tech>` columns (= MWh / capacity_MW lookup)
- Freeze the top header row(s) so the user can scroll the data while keeping headers visible.

### Output tabs

Compute everything via Excel formulas referencing source-data tab columns and parameter cells. Examples of useful patterns:

- **Slice-mean over hourly data**:
  `=AVERAGEIFS('Source'!$<cf_col>$<start>:$<cf_col>$<end>, 'Source'!$<slice_col>$<start>:$<slice_col>$<end>, "Summer Peak", 'Source'!$<hour_col>$<start>:$<hour_col>$<end>, 17)`

- **EIA-style calibration scaling** (preserve hourly shape, hit annual target):
  `=AVERAGEIFS(...) * 'Parameters'!$B$3 / AVERAGE('Source'!$<cf_col>$<start>:$<cf_col>$<end>)`

- **Year-selectable lookup from a multi-year source**:
  `=INDEX('EIA Source'!M:M, MATCH($F$1, 'EIA Source'!$A:$A, 0))` where `$F$1` is an editable year cell

- **Mirror / template references** (for technologies that should match another tab):
  `='SYSHECF-natural-gas-peaker'!B6` cell-by-cell

- Wrap formulas in `IFERROR(..., 0)` and `MAX(0, MIN(1, ...))` for CFs to handle missing data + clamp to physical range

**Tab order** must match the consuming model's subscript order if the consumer is a Vensim model. Always ask the user for the canonical order; never invent it.

**Tab color** for output tabs: `ws.sheet_properties.tabColor = '1F3864'` (Excel "Dark Blue, Accent 1, Darker 25%"). Source/About/parameter tabs stay uncolored so outputs visually pop.

## Gotchas / non-obvious rules

1. **Use VLOOKUP, not XLOOKUP.** XLOOKUP requires Excel 2021 / Microsoft 365. Many users still run Excel 2019 or earlier — XLOOKUP returns `#NAME?` and every downstream formula cascades to `#DIV/0!`. Always use `VLOOKUP(<key>, <range>, <col_index>, FALSE)` for cross-tab lookups, or `INDEX(<col>, MATCH(<key>, <key_col>, 0))` if you need column-range flexibility.

2. **File-name convention.** When the workbook replaces an existing model input file, **use the existing file name exactly** — Vensim reads files by name. Don't add prefixes like "US -" unless the user's existing convention does. Common canonical names:
   - `Start Year Seasonal Expected Hourly Electricity Capacity Factors.xlsx` (SYSHECF / capacity factors)
   - `Seasonal Hourly Equipment Load Factors by End Use.xlsx` (SHELF / load factors)

3. **A1 formatting.** Bold but **default size 11** — the user explicitly does not want the title row enlarged. Format: `<ABBREVIATION> <File Name Without Extension>`. Example: `SYSHECF Start Year Seasonal Expected Hourly Electricity Capacity Factors`.

4. **Left-align everything in column B.** `Alignment(horizontal='left', vertical='top', wrap_text=True)` — default vertical centering looks bad with long wrapped text.

5. **Hyperlinks as real hyperlinks.** Set `cell.hyperlink = url` AND style `Font(color='0563C1', underline='single')`. Just setting font isn't enough.

6. **File-open conflict.** If the user has the target file open in Excel, `wb.save()` raises `PermissionError`. Catch it cleanly and tell the user to close the file. Don't crash mid-build.

7. **Performance for large sources.** Cambium hourly is 8,760 rows × 75 cols. Use the regular openpyxl Workbook (not write_only mode — write_only doesn't support formulas well). Batch your `ws.cell(...)` calls; don't call `ws.append()` after writing individual cells (it conflicts).

8. **Formula cell references.** When derived columns are added after source data, the cell reference for a CF column might be at e.g. `CA` (col 79). Use `openpyxl.utils.get_column_letter()` to compute letters from indices — don't hardcode.

9. **Verify against ground truth.** After building, write a Python verification that reproduces the formula math (e.g., `AVERAGEIFS(...)` → equivalent groupby in pandas) and compares to the canonical CSV or independently-computed values. Max abs diff should be ~1e-11 (float noise). If it's larger, something is wrong (column letters off, scaling factor in wrong place, etc.).

10. **Tab-color encoding.** openpyxl stores `tabColor` as `'001F3864'` (with FF/00 alpha prefix) when read back, but you set it as `'1F3864'`. When verifying, substring-match `'1F3864'` rather than equality.

## Implementation skeleton

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import csv
import datetime as dt
from pathlib import Path

OUT_PATH = Path("path/to/Canonical File Name.xlsx")
OUTPUT_TAB_COLOR = '1F3864'
PURPOSE_FILL = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
HEADER_FILL = PatternFill(start_color='305496', end_color='305496', fill_type='solid')
HEADER_FONT = Font(bold=True, color='FFFFFF')
LEFT_TOP_WRAP = Alignment(horizontal='left', vertical='top', wrap_text=True)


def add_about_tab(wb, abbreviation, file_name_no_ext, sources, notes):
    ws = wb.create_sheet('About', 0)
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 110

    # A1: <ABBR> <File Name>
    ws.cell(1, 1, f'{abbreviation} {file_name_no_ext}').font = Font(bold=True)
    # A3: Sources:
    ws.cell(3, 1, 'Sources:').font = Font(bold=True)
    cur = 3
    for src in sources:
        c = ws.cell(cur, 2, src['purpose'])
        c.font = Font(bold=True); c.fill = PURPOSE_FILL; c.alignment = LEFT_TOP_WRAP
        for off, val in enumerate([src['source'], src['publication'], src['year']], start=1):
            ws.cell(cur + off, 2, val).alignment = LEFT_TOP_WRAP
        u = ws.cell(cur + 4, 2, src['url'])
        u.hyperlink = src['url']; u.font = Font(color='0563C1', underline='single'); u.alignment = LEFT_TOP_WRAP
        ws.cell(cur + 5, 2, src['info']).alignment = LEFT_TOP_WRAP
        cur += 7
    # Blank row, then Notes:
    notes_row = cur + 1
    ws.cell(notes_row, 1, 'Notes:').font = Font(bold=True)
    for i, (label, text) in enumerate(notes):
        r = notes_row + 1 + i
        ws.cell(r, 1, label).font = Font(bold=True)
        ws.cell(r, 2, text).alignment = LEFT_TOP_WRAP


def add_source_tab(wb, name, csv_rows, derived_columns=None):
    """Paste CSV rows verbatim, optionally add derived columns at the right."""
    ws = wb.create_sheet(name)
    for r_idx, row in enumerate(csv_rows, start=1):
        for c_idx, val in enumerate(row, start=1):
            ws.cell(r_idx, c_idx, _try_float(val) if r_idx > <header_row> else val)
    # Add derived columns at the right
    if derived_columns:
        for offset, (header, fill_func) in enumerate(derived_columns, start=1):
            col = len(csv_rows[0]) + offset
            ws.cell(<header_row>, col, header).font = Font(bold=True, italic=True)
            for r in range(<data_start_row>, <data_end_row> + 1):
                ws.cell(r, col, fill_func(r))
    ws.freeze_panes = 'A2'


def add_output_tab(wb, name, formula_func):
    ws = wb.create_sheet(name)
    ws.sheet_properties.tabColor = OUTPUT_TAB_COLOR
    # ... headers + formula cells via formula_func(row, col) ...


def main():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    add_about_tab(wb, ABBR, FILE_NAME_NO_EXT, sources, notes)
    # ... parameter tabs ...
    # ... source data tabs ...
    # ... output tabs in subscript order (each gets dark blue tabColor) ...
    try:
        wb.save(OUT_PATH)
    except PermissionError:
        print(f"  ERROR: cannot write {OUT_PATH} — close it in Excel first.")
        return
```

## Verification step (always do this)

After building, write a small Python script that reproduces what the formulas SHOULD evaluate to:

```python
# Reproduce AVERAGEIFS math in Python with the same source data
for tech in techs:
    cf_hourly = source_mwh[tech] / annual_capacity_mw[tech]
    annual_mean = cf_hourly.mean()
    scale = (eia_target[tech] / annual_mean) if eia_target.get(tech) else 1.0
    for slice_name in SLICES:
        for h in range(24):
            mask = (slice_arr == slice_name) & (hour_arr == h)
            expected = max(0, min(1, cf_hourly[mask].mean() * scale))
            actual = read_csv_value(tech, slice_name, h)
            assert abs(expected - actual) < 1e-9
```

Report max abs diff across all techs. If anything is > 1e-9, debug before delivering. Typical noise: ~5e-11.

## How to talk to the user about this

When proposing the workbook structure, walk through:
- "About tab will document sources + methodology"
- "Source data tabs paste the raw files verbatim — every column, every row"
- "Derived columns added at the right of source tabs"
- "Output tabs use AVERAGEIFS / VLOOKUP / INDEX-MATCH to compute values from sources"
- "Output tabs will be dark blue, source tabs uncolored"
- "I'll verify all computed values match an independent ground truth"

When the user changes a requirement mid-build (tab order, color, A1 prefix), update the build script and rerun — don't try to patch the .xlsx in place.

## Project context this skill emerged from

Built originally for the EPS (Energy Policy Simulator) Vensim model's SYSHECF and SHELF input workbooks. Methodology canonical reference: `CLAUDE.md` and `DECISIONS.md` at the root of the "Global Electricity File Creator" project. The build scripts that exercise this pattern most fully:
- `scripts/build_syshecf_workbook.py`
- `scripts/build_xlsx_per_csv.py`

If working in that project, read those scripts before writing new builds — they encode all the lessons above.
