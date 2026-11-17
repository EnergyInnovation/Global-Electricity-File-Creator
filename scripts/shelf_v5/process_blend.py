"""Per-process industry shapes: the 'Industry slice weights' and 'Industry blend' tabs, the six
SHELF-indstproc-<timeslice> output tabs and SHELF-indstCCS. Everything is written as Excel formulas.

The EPRI and NREL sources on the hand-built tabs give shapes by calendar season (Dec-Feb, Mar-May, Jun-Aug,
Sep-Nov). The EPS timeslices are clusters of days, not seasons, so:

  * 'Industry slice weights' counts, from the Clustering tab, what share of each timeslice's days falls in each
    calendar season;
  * 'Industry blend' builds each timeslice's shape as that weighted blend (the two peak timeslices use the EPRI
    peak-day shapes for the process rows), then scales every row group so that its hourly values, summed over
    all timeslices and hours and weighted by days per timeslice, add to exactly 1.

The US model reads a whole-industry shape for every industry (see industry.py), so these per-process tabs are
not used in the US; they are kept so that a region can switch an industry over to them.
"""
from __future__ import annotations
from openpyxl.utils import get_column_letter as L

from . import names

SEASONS = ['winter', 'spring', 'summer', 'fall']
PROCS = ['heat below 100 C', 'heat 100 to 200 C', 'heat 200 to 500 C', 'heat 500 to 1000 C', 'heat above 1000 C',
         'Cooling', 'Machine Drive', 'Other process', 'Facility HVAC', 'Facility Lighting', 'Other Nonprocess']
CATS = ['agriculture and forestry', 'refined petroleum and coke']     # built here for reference; not exported
CCS = ['CCS']
ALL = PROCS + CATS + CCS

HDR = 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)'
EP, OD = "'EPRI load shapes'", "'Other Data & Calcs'"
ENDUSE = f"INDEX({OD}!$C$658:$C$668,MATCH($A{{r}},{OD}!$B$658:$B$668,0))"
NOT_EXPORTED = "not exported: see the 'Industry day shapes' tab"


def add_clustering_helpers(wb) -> int:
    """Month and calendar-season helper columns on the Clustering tab. Returns the last day row."""
    cl = wb['Clustering']
    cl['F1'] = 'Helper columns for the industry blend (weather year 2012, same as the clustering)'
    cl['F2'] = 'Month'; cl['G2'] = 'EPRI season'
    cl['I1'] = 'Month -> EPRI season (used to blend the industry shapes)'
    cl['I2'] = 'Month'; cl['J2'] = 'EPRI season'
    for i, m in enumerate(range(1, 13), start=3):
        cl.cell(i, 9, m)
        cl.cell(i, 10, 'winter' if m in (12, 1, 2) else 'spring' if m in (3, 4, 5)
                else 'summer' if m in (6, 7, 8) else 'fall')
    last = 2
    for r in range(3, 3 + 366):
        if cl.cell(r, 4).value is None:
            continue
        cl.cell(r, 6, f'=MONTH(DATE(2012,1,1)+D{r}-1)')
        cl.cell(r, 7, f'=INDEX($J$3:$J$14,MATCH(F{r},$I$3:$I$14,0))')
        last = r
    return last


def add_slice_weights_tab(wb, labels: list[str]) -> dict[str, int]:
    w = wb.create_sheet('Industry slice weights')
    # the ranges run one row past day 365, as in the workbook on eps-us develop; the extra row is blank
    rng, grng = '$E$3:$E$368', '$G$3:$G$368'
    w['A1'] = ("Share of each timeslice's days that fall in each calendar season (Dec-Feb winter, Mar-May spring, "
               'Jun-Aug summer, Sep-Nov fall), from the Clustering tab. The industry shapes below are built from '
               'EPRI shapes by calendar season, so each timeslice gets the day-weighted blend of those seasons.')
    w['A3'] = 'Timeslice'
    for j, s in enumerate(SEASONS):
        w.cell(3, 2 + j, s)
    w.cell(3, 6, 'days in slice'); w.cell(3, 7, 'check (sums to 1)')
    for i, sl in enumerate(labels):
        r = 4 + i
        w.cell(r, 1, sl)
        for j in range(4):
            w.cell(r, 2 + j, f'=COUNTIFS(Clustering!{rng},$A{r},Clustering!{grng},{L(2 + j)}$3)'
                             f'/COUNTIF(Clustering!{rng},$A{r})')
        w.cell(r, 6, f'=COUNTIF(Clustering!{rng},$A{r})')
        w.cell(r, 7, f'=SUM(B{r}:E{r})')
        for j in range(2, 8):
            w.cell(r, j).number_format = '0.000'
    w.column_dimensions['A'].width = 14
    return {sl: 4 + i for i, sl in enumerate(labels)}


def _season_term(cat: str, season_cell: str, hcol: int) -> str:
    """Excel expression for one calendar-season hourly value of a row group (hcol = hour 0..23)."""
    e = L(7 + hcol)     # hour columns G..AD on the EPRI and Other Data & Calcs tabs
    a = L(3 + hcol)     # hour columns C..Z on the Ag tab
    if cat in PROCS:
        return f"SUMIFS({EP}!{e}$436:{e}$455,{EP}!$C$436:$C$455,{ENDUSE},{EP}!$D$436:$D$455,{season_cell})"
    if cat == 'agriculture and forestry':
        return f"SUMIFS(Ag!{a}$6:{a}$9,Ag!$B$6:$B$9,{season_cell})"
    if cat == 'refined petroleum and coke':
        return f"SUMIFS({OD}!{e}$652:{e}$655,{OD}!$F$652:$F$655,{season_cell})/8760"
    if cat == 'CCS':
        return (f"SUMIFS({EP}!{e}$418:{e}$433,{EP}!$C$418:$C$433,\"indProcessHeating\","
                f"{EP}!$D$418:$D$433,{season_cell})")
    raise ValueError(cat)


def _peak_term(cat: str, summer: bool, hcol: int) -> str:
    e = L(7 + hcol)
    if cat in PROCS:
        return f"SUMIFS({EP}!{e}$509:{e}$513,{EP}!$C$509:$C$513,{ENDUSE})"
    if cat == 'CCS':
        return '1/8760'
    return _season_term(cat, '"summer"' if summer else '"winter"', hcol)


def add_blend_and_outputs(wb, labels: list[str], tags: list[str], tab_color: str) -> None:
    """'Industry blend', SHELF-indstproc-<tag> x 6 and SHELF-indstCCS. labels[4], labels[5] are the peak slices."""
    wrow = add_slice_weights_tab(wb, labels)
    b = wb.create_sheet('Industry blend')
    b['A1'] = ('Raw hourly shape for every industry category and timeslice, before normalisation. Non-peak '
               'timeslices blend the four calendar-season shapes with the weights on "Industry slice weights". '
               'Peak timeslices use the EPRI peak-day shapes (processes) or the summer / winter season shape '
               '(agriculture, refining) or a flat profile (CCS). The normalisation block at the right scales each '
               'category so that sum over (timeslice, hour) x days per timeslice = 1.0, which is what the EPS '
               'expects. The agriculture and refining rows are not exported; the whole-industry shapes the model '
               "reads are built on the 'Industry day shapes' tab.")
    b['A3'] = 'Category'; b['B3'] = 'Timeslice'
    for h in range(24):
        b.cell(3, 3 + h, f'Hour{h}')
    b.cell(3, 27, 'row sum'); b.cell(3, 28, 'days'); b.cell(3, 29, 'row sum x days')

    r = 4
    for cat in ALL:
        for k, sl in enumerate(labels):
            b.cell(r, 1, cat); b.cell(r, 2, sl)
            wr = wrow[sl]
            for h in range(24):
                if k >= 4:
                    f = _peak_term(cat, summer=(k == 4), hcol=h)
                else:
                    f = '+'.join(f"'Industry slice weights'!${L(2 + j)}${wr}*"
                                 + _season_term(cat, f"'Industry slice weights'!{L(2 + j)}$3", h) for j in range(4))
                b.cell(r, 3 + h, '=' + f.replace('{r}', str(r))).number_format = '0.000E+00'
            b.cell(r, 27, f'=SUM(C{r}:Z{r})').number_format = '0.00000'
            b.cell(r, 28, f"=INDEX('SHELF-days-per-timeslice'!$B$2:$B$7,MATCH(B{r},'SHELF-days-per-timeslice'!$A$2:$A$7,0))")
            b.cell(r, 29, f'=AA{r}*AB{r}').number_format = '0.00000'
            r += 1
        r += 1
    last = r

    # normalisation block
    b['AE3'] = 'Category'; b['AF3'] = 'annual sum before normalisation'; b['AG3'] = 'check after normalisation'
    n0, n1 = 4, 4 + len(ALL) - 1
    for i, cat in enumerate(ALL):
        rr = n0 + i
        b.cell(rr, 31, cat)
        b.cell(rr, 32, f'=SUMIFS($AC$4:$AC${last},$A$4:$A${last},AE{rr})').number_format = '0.00000'
        if cat in CATS:
            b.cell(rr, 33, NOT_EXPORTED)
            continue
        if cat == 'CCS':
            f = "=SUMPRODUCT(('SHELF-indstCCS'!$B$2:$Y$7)*('SHELF-days-per-timeslice'!$B$2:$B$7))"
        else:
            f = '=' + '+'.join(
                f"SUMPRODUCT(('SHELF-indstproc-{t}'!$A$2:$A$13=AE{rr})*('SHELF-indstproc-{t}'!$B$2:$Y$13))"
                f"*'SHELF-days-per-timeslice'!$B${2 + n}" for n, t in enumerate(tags))
        b.cell(rr, 33, f).number_format = '0.00000'
    b.column_dimensions['A'].width = 24; b.column_dimensions['B'].width = 12

    def out_cell(cat_ref: str, sl_ref: str, h: int) -> str:
        col = L(3 + h)
        return (f"=SUMIFS('Industry blend'!${col}$4:${col}${last},'Industry blend'!$A$4:$A${last},{cat_ref},"
                f"'Industry blend'!$B$4:$B${last},{sl_ref})"
                f"/INDEX('Industry blend'!$AF${n0}:$AF${n1},MATCH({cat_ref},'Industry blend'!$AE${n0}:$AE${n1},0))")

    def make_tab(name: str, rows: list[str], refs) -> None:
        ws = wb.create_sheet(name)
        ws.sheet_properties.tabColor = tab_color
        ws['A1'] = HDR
        for h in range(24):
            ws.cell(1, 2 + h, f'Hour{h}')
        for i, lab in enumerate(rows):
            rr = 2 + i
            ws.cell(rr, 1, lab)
            cat_ref, sl_ref = refs(rr)
            for h in range(24):
                ws.cell(rr, 2 + h, out_cell(cat_ref, sl_ref, h)).number_format = '0.0000E+00'
        ws.column_dimensions['A'].width = 26

    for sl, tag in zip(labels, tags):
        make_tab(f'SHELF-indstproc-{tag}', PROCS, lambda rr, sl=sl: (f'$A{rr}', f'"{sl}"'))
    make_tab('SHELF-indstCCS', labels, lambda rr: ('"CCS"', f'$A{rr}'))


def set_system_load_shape(wb, category: str) -> None:
    """District heat / hydrogen and geoengineering: the shape of total national end-use load (Cambium tab,
    column G), averaged per timeslice like every other tab, instead of zeros."""
    cam = "'Cambium hourly source'"
    ws = wb[f'SHELF-{category}']
    for rr in range(2, 8):
        for h in range(24):
            ws.cell(rr, 2 + h, f"=IFERROR(AVERAGEIFS({cam}!$G$7:$G$8766,{cam}!$BZ$7:$BZ$8766,$A{rr},"
                               f"{cam}!$BY$7:$BY$8766,{h})/SUM({cam}!$G$7:$G$8766),0)")
