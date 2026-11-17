"""Whole-industry load shapes for EPS 5.0 (eps-us issue #344): one row per industry on each of the six
SHELF-indstcat-<timeslice> tabs, built as Excel formulas from metered-based hourly data.

Tabs written here:
  Industry metered source     national hourly load for seven industries, Eastern time (see siels.py)
  Industry day shapes         which shape each industry uses; typical weekday and weekend day per shape; weekend
                              level; month-to-month level; agriculture by month and day type; shape by timeslice
  Industry hourly build       the typical days laid out over a year on the clustering calendar
  Industry weekend evidence   reference only: the metered figures behind the weekend settings
  SHELF-indstcat-<timeslice>  the outputs the model reads
It also adds day-type helper columns beside the utilities' daily profiles on the hand-built Ag tab.

How a shape is built: the median weekday and the median weekend day, hour by hour, from the source series; the
weekend day scaled to a set share of a weekday's energy; a month-to-month level from EIA industrial sales net of
agriculture; laid on the clustering calendar (weather year 2012, which starts on a Sunday); then averaged per
timeslice and divided by the annual total, exactly like the buildings and transport tabs.
"""
from __future__ import annotations
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

from .siels import NAMES as METERED

SRC, DAY, BUILD, EVID = ('Industry metered source', 'Industry day shapes', 'Industry hourly build',
                         'Industry weekend evidence')
SHAPES = METERED + ['agriculture']
SHAPE_NOTE = {
    'food and beverage': 'Oak Ridge / Berkeley Lab data: food and beverage manufacturing',
    'pulp and paper': 'Oak Ridge / Berkeley Lab data: pulp and paper',
    'petroleum and coal products': 'Oak Ridge / Berkeley Lab data: petroleum refining and coal products',
    'chemicals': 'Oak Ridge / Berkeley Lab data: chemicals',
    'ammonia': 'Oak Ridge / Berkeley Lab data: ammonia (not assigned to any industry; ammonia is part of chemicals)',
    'cement': 'Oak Ridge / Berkeley Lab data: cement',
    'iron and steel': 'Oak Ridge / Berkeley Lab data: iron, steel and ferroalloys, which the authors built from the '
                      'load shapes of other metal manufacturers',
    'agriculture': 'California utility agricultural profiles, by calendar season (Ag tab)',
}
OWN, BORROW, JUDGE = 'own data', 'borrowed from a similar industry', 'judgment'
_FACTORY = 'Factory work on shifts; the steel series is built from the shapes of other manufacturers.'
# EPS industry (with its ISIC code), shape, basis, why. The order is the row order of the SHELF-indstcat files
# and of ctrl-settings/ICwIwLF, which must match.
ASSIGN = [
    ('agriculture and forestry 01T03', 'agriculture', OWN, 'Irrigation and farm load, strongly seasonal.'),
    ('coal mining 05', 'cement', BORROW, 'Mining and mineral processing run long hours; cement is the closest covered industry.'),
    ('oil and gas extraction 06', 'petroleum and coal products', BORROW, 'Pumps and compressors run around the clock, like a refinery.'),
    ('other mining and quarrying 07T08', 'cement', BORROW, 'Quarrying and mineral processing; cement is the closest covered industry.'),
    ('food beverage and tobacco 10T12', 'food and beverage', OWN, ''),
    ('textiles apparel and leather 13T15', 'iron and steel', BORROW, _FACTORY),
    ('wood products 16', 'iron and steel', BORROW, _FACTORY),
    ('pulp paper and printing 17T18', 'pulp and paper', OWN, ''),
    ('refined petroleum and coke 19', 'petroleum and coal products', OWN, ''),
    ('chemicals 20', 'chemicals', OWN, ''),
    ('rubber and plastic products 22', 'iron and steel', BORROW, _FACTORY),
    ('glass and glass products 231', 'cement', BORROW, 'Glass furnaces, like cement kilns, run continuously.'),
    ('cement and other nonmetallic minerals 239', 'cement', OWN, ''),
    ('iron and steel 241', 'iron and steel', OWN, 'The authors had no California steel mills and used other metal manufacturers\' shapes.'),
    ('other metals 242', 'iron and steel', BORROW, 'Metal manufacturing.'),
    ('metal products except machinery and vehicles 25', 'iron and steel', BORROW, 'Metal manufacturing.'),
    ('computers and electronics 26', 'iron and steel', BORROW, _FACTORY),
    ('appliances and electrical equipment 27', 'iron and steel', BORROW, _FACTORY),
    ('other machinery 28', 'iron and steel', BORROW, _FACTORY),
    ('road vehicles 29', 'iron and steel', BORROW, _FACTORY),
    ('nonroad vehicles 30', 'iron and steel', BORROW, _FACTORY),
    ('other manufacturing 31T33', 'iron and steel', BORROW, _FACTORY),
    ('energy pipelines and gas processing 352T353', 'petroleum and coal products', BORROW, 'Compressors and gas plants run around the clock, like a refinery.'),
    ('water and waste 36T39', 'pulp and paper', JUDGE, 'No covered industry is a close match. Water and wastewater plants run all day with a mild daytime rise, which the paper shape resembles.'),
    ('construction 41T43', 'iron and steel', JUDGE, 'No covered industry is a close match. Construction is daytime work, and this shape has a clear daytime rise.'),
]
# weekend-day energy as a share of a weekday's, by shape (evidence on the 'Industry weekend evidence' tab)
WEEKEND = {'food and beverage': 0.85, 'pulp and paper': 0.95, 'petroleum and coal products': 0.95, 'chemicals': 0.95,
           'ammonia': 0.95, 'cement': 0.95, 'iron and steel': 0.85}

# fixed row positions on the day-shapes tab
ASGROW0 = 7                       # 25 industries: rows 7-31
LISTROW0 = 35                     # 8 shape names: rows 35-42
DAYROW0 = 48                      # 7 shapes x 2 day types: rows 48-61
AGSHARE_ROW = 66
SALESROW0 = 70                    # 36 months of sales: rows 70-105
MONROW0 = 110                     # 12 months: rows 110-121
AGROW0 = 127                      # agriculture, 12 months x 2 day types: rows 127-150
SLICEROW0 = 157                   # 8 shapes x 6 timeslices: rows 157-204
CHECKROW0 = 210                   # 8 shapes: rows 210-217

BOLD = Font(bold=True)
HDR_FILL = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
WRAP = Alignment(horizontal='left', vertical='top', wrap_text=True)
UNIT_HDR = 'Unit: dimensionless (ratio of electricity demand in this hour to annual demand)'


def label(cat: str) -> str:
    """EPS industry name without its trailing ISIC code, as used for row labels in the output files."""
    return ' '.join(cat.split(' ')[:-1])


def _banner(ws, row, text, desc=None):
    ws.cell(row, 1, text).font = BOLD
    if desc:
        ws.cell(row + 1, 1, desc)


def _header(ws, row, labels, col0=1):
    for j, t in enumerate(labels):
        c = ws.cell(row, col0 + j, t)
        c.font = BOLD; c.fill = HDR_FILL
        c.alignment = Alignment(wrap_text=True, vertical='top')


def add_source_tab(wb, stamps: list[str], cols: dict[str, list[float]]) -> None:
    ws = wb.create_sheet(SRC)
    hdr = ['timestamp'] + METERED + ['day_of_year', 'hour_of_day', 'day_type']
    for j, t in enumerate(hdr, 1):
        ws.cell(1, j, t)
    for i in range(8760):
        x = i + 2
        ws.cell(x, 1, stamps[i])
        for j, n in enumerate(METERED):
            ws.cell(x, j + 2, float(cols[n][i]))
        ws.cell(x, 9, i // 24 + 1)
        ws.cell(x, 10, i % 24)
        # the source year, 2018, began on a Monday: day 6 is a Saturday, day 7 a Sunday
        ws.cell(x, 11, f'=IF(OR(MOD(I{x},7)=6,MOD(I{x},7)=0),"weekend","weekday")')
    ws.column_dimensions['A'].width = 18


def add_build_tab(wb) -> None:
    ws = wb.create_sheet(BUILD)
    hdr = ['day_of_year', 'hour_of_day', 'month', 'day_type', 'calendar_season', 'slice'] + SHAPES
    for j, t in enumerate(hdr, 1):
        ws.cell(1, j, t)
    for i in range(8760):
        x = i + 2
        ws.cell(x, 1, i // 24 + 1)
        ws.cell(x, 2, i % 24)
        ws.cell(x, 3, f'=VLOOKUP($A{x},Clustering!$D$3:$F$367,3,FALSE)')
        # the clustering calendar (weather year 2012) begins on a Sunday: day 1 is a Sunday, day 7 a Saturday
        ws.cell(x, 4, f'=IF(OR(MOD($A{x},7)=1,MOD($A{x},7)=0),"weekend","weekday")')
        ws.cell(x, 5, f'=VLOOKUP($A{x},Clustering!$D$3:$G$367,4,FALSE)')
        ws.cell(x, 6, f'=VLOOKUP($A{x},Clustering!$D$3:$E$367,2,FALSE)')
        for k, _ in enumerate(METERED):
            r1 = DAYROW0 + 2 * k
            ws.cell(x, 7 + k, f"=INDEX('{DAY}'!$C${r1}:$Z${r1 + 1},IF($D{x}=\"weekday\",1,2),$B{x}+1)"
                              f"*INDEX('{DAY}'!$AE${r1}:$AE${r1 + 1},IF($D{x}=\"weekday\",1,2))"
                              f"*INDEX('{DAY}'!$H${MONROW0}:$H${MONROW0 + 11},$C{x})")
        ws.cell(x, 7 + len(METERED), f"=INDEX('{DAY}'!$C${AGROW0}:$Z${AGROW0 + 23},"
                                     f"($C{x}-1)*2+IF($D{x}=\"weekday\",1,2),$B{x}+1)")


def add_day_tab(wb, slice_labels: list[str]) -> None:
    ws = wb.create_sheet(DAY)
    hours = [f'Hour{h}' for h in range(24)]
    ws.cell(1, 1, 'Whole-industry load shapes: which shape each industry uses and how the shapes are built').font = BOLD
    ws.cell(2, 1, 'Read top to bottom: (1) the shape each industry uses, (2) the typical weekday and weekend day for each '
                  'shape, with the weekend level, (3) how the level changes from month to month, (4) agriculture\'s typical '
                  'days, (5) the resulting shape by timeslice, which the SHELF-indstcat output tabs read, and (6) checks.')

    # 1. assignments
    _banner(ws, 4, '1. Which shape each industry uses',
            'Every industry takes one of the shapes listed below this table. Change the SHAPE USED cell to reassign an industry.')
    _header(ws, 6, ['EPS industry', 'Name in the output files', 'SHAPE USED (edit to reassign)', 'Basis', 'Why this shape'])
    dv = DataValidation(type='list', formula1=f'=$A${LISTROW0}:$A${LISTROW0 + len(SHAPES) - 1}', allow_blank=False)
    ws.add_data_validation(dv)
    for i, (cat, shape, basis, why) in enumerate(ASSIGN):
        r = ASGROW0 + i
        ws.cell(r, 1, cat); ws.cell(r, 2, label(cat)); ws.cell(r, 3, shape); ws.cell(r, 4, basis); ws.cell(r, 5, why)
        dv.add(ws.cell(r, 3))
    _header(ws, LISTROW0 - 1, ['Shapes available', 'Where it comes from'])
    for i, s in enumerate(SHAPES):
        ws.cell(LISTROW0 + i, 1, s); ws.cell(LISTROW0 + i, 2, SHAPE_NOTE[s])

    # 2. typical days
    _banner(ws, DAYROW0 - 3, '2. Typical weekday and weekend day for each shape built from metered-based data',
            'The median load in each hour across all weekdays, and across all weekend days, of the national series on the '
            f"'{SRC}' tab (same units as that tab). The median is used so that occasional one-hour spikes in the "
            "simulated data do not affect the result. The source data put a weekend day's energy almost equal to a "
            "weekday's, which is higher than utilities' metered large-customer classes show, so the weekend rows are "
            "scaled to the WEEKEND ENERGY USED setting. The evidence for the settings is on the 'Industry weekend "
            "evidence' tab. The hour-by-hour shape of the weekend day is kept.")
    _header(ws, DAYROW0 - 1, ['Shape', 'Day type'] + hours + ['', 'Whole day\n(sum of 24 hours)',
                                                             'Weekend day as a share\nof a weekday\nin the source data',
                                                             'WEEKEND ENERGY USED\nshare of a weekday\n(edit to change)',
                                                             'Scaling applied\nto this row'])
    for k, s in enumerate(METERED):
        col = L(2 + k)
        for d, dt in enumerate(['weekday', 'weekend']):
            r = DAYROW0 + 2 * k + d
            ws.cell(r, 1, s); ws.cell(r, 2, dt)
            for h in range(24):
                ws.cell(r, 3 + h, f"=_xlfn.AGGREGATE(16,6,'{SRC}'!${col}$2:${col}$8761/(('{SRC}'!$K$2:$K$8761=$B{r})"
                                  f"*('{SRC}'!$J$2:$J$8761={h})),0.5)")
            ws.cell(r, 28, f'=SUM(C{r}:Z{r})')
            if d == 1:
                ws.cell(r, 29, f'=AB{r}/AB{r - 1}')
                ws.cell(r, 30, WEEKEND[s])
                ws.cell(r, 31, f'=AD{r}/AC{r}')
            else:
                ws.cell(r, 31, 1)

    # 3. month-to-month level
    _banner(ws, SALESROW0 - 7, '3. Month-to-month level for non-farm industry',
            'U.S. industrial electricity sales per day show how industrial load rises and falls through the year. '
            'Agriculture has its own seasonal pattern, so its share is taken out before the remainder is applied to '
            'the seven shapes above.')
    ws.cell(AGSHARE_ROW, 1, "Agriculture's share of industrial electricity")
    ws.cell(AGSHARE_ROW, 2, "='Other Data & Calcs'!$Y$616")
    _header(ws, SALESROW0 - 1, ['Month beginning', 'Month', 'Days in month',
                                'U.S. industrial electricity sales\n(million kWh)', 'Sales per day\n(million kWh)'])
    for i in range(36):
        r = SALESROW0 + i
        c = L(4 + i)
        ws.cell(r, 1, f"='Other Data & Calcs'!{c}597").number_format = 'mmm yyyy'
        ws.cell(r, 2, f'=MONTH(A{r})')
        ws.cell(r, 3, f'=DAY(EOMONTH(A{r},0))')
        ws.cell(r, 4, f"='Other Data & Calcs'!{c}601")
        ws.cell(r, 5, f'=D{r}/C{r}')
    _header(ws, MONROW0 - 1, ['Month', 'Average sales per day\n(million kWh)', "All industry\nrelative to the year's average day",
                              'Calendar season', "Agriculture\nrelative to its year's average day",
                              'Non-farm industry\nbefore rescaling', 'Days in month\non the clustering calendar',
                              "NON-FARM LEVEL USED\nrelative to the year's average day"])
    m0, m1 = MONROW0, MONROW0 + 11
    for i in range(12):
        r = MONROW0 + i
        ws.cell(r, 1, i + 1)
        ws.cell(r, 2, f'=AVERAGEIFS($E${SALESROW0}:$E${SALESROW0 + 35},$B${SALESROW0}:$B${SALESROW0 + 35},A{r})')
        ws.cell(r, 3, f'=B{r}/(SUMPRODUCT($B${m0}:$B${m1},$G${m0}:$G${m1})/SUM($G${m0}:$G${m1}))')
        ws.cell(r, 4, f'=INDEX(Clustering!$J$3:$J$14,MATCH(A{r},Clustering!$I$3:$I$14,0))')
        ws.cell(r, 5, f'=INDEX(Ag!$AB$6:$AB$9,MATCH(D{r},Ag!$B$6:$B$9,0))*4')
        ws.cell(r, 6, f'=(C{r}-$B${AGSHARE_ROW}*E{r})/(1-$B${AGSHARE_ROW})')
        ws.cell(r, 7, f'=COUNTIF(Clustering!$F$3:$F$367,A{r})')
        ws.cell(r, 8, f'=F{r}/(SUMPRODUCT($F${m0}:$F${m1},$G${m0}:$G${m1})/SUM($G${m0}:$G${m1}))')

    # 4. agriculture by month and day type
    _banner(ws, AGROW0 - 3, '4. Agriculture: typical weekday and weekend day in each month',
            "The average of the California utilities' daily agricultural profiles on the Ag tab for each month and day "
            'type, each utility first divided by its own annual total and then weighted by its share of agricultural '
            "electricity use (Ag tab, column L). Values are shares of annual use per hour, in the utilities' local time.")
    _header(ws, AGROW0 - 1, ['Month', 'Day type'] + hours + ['', 'Whole day\n(sum of 24 hours)',
                                                            'Weekend day as a share\nof a weekday'])
    for m in range(12):
        for d, dt in enumerate(['weekday', 'weekend']):
            r = AGROW0 + 2 * m + d
            ws.cell(r, 1, m + 1); ws.cell(r, 2, dt)
            for h in range(24):
                c = L(3 + h)
                ws.cell(r, 3 + h,
                        f'=Ag!$L$32*AVERAGEIFS(Ag!{c}$54:{c}$418,Ag!$AB$54:$AB$418,$A{r},Ag!$AD$54:$AD$418,$B{r})/SUM(Ag!$C$54:$Z$418)'
                        f'+Ag!$L$31*AVERAGEIFS(Ag!{c}$427:{c}$791,Ag!$AB$427:$AB$791,$A{r},Ag!$AD$427:$AD$791,$B{r})/SUM(Ag!$C$427:$Z$791)'
                        f'+Ag!$L$33*AVERAGEIFS(Ag!$D$798:$D$9557,Ag!$E$798:$E$9557,$A{r},Ag!$G$798:$G$9557,$B{r},Ag!$C$798:$C$9557,{h + 1})/SUM(Ag!$D$798:$D$9557)')
            ws.cell(r, 28, f'=SUM(C{r}:Z{r})')
            if d == 1:
                ws.cell(r, 29, f'=AB{r}/AB{r - 1}')

    # 5. by timeslice
    _banner(ws, SLICEROW0 - 3, '5. Load shape by timeslice for each shape',
            f"The share of annual electricity use in each hour of each timeslice: the average of the '{BUILD}' tab over "
            'the days in the timeslice, divided by the annual total. The SHELF-indstcat output tabs read these rows.')
    _header(ws, SLICEROW0 - 1, ['Shape', 'Timeslice'] + hours + ['', 'Day total'])
    for k, s in enumerate(SHAPES):
        col = L(7 + k)
        for j, sl in enumerate(slice_labels):
            r = SLICEROW0 + 6 * k + j
            ws.cell(r, 1, s); ws.cell(r, 2, sl)
            for h in range(24):
                ws.cell(r, 3 + h, f"=AVERAGEIFS('{BUILD}'!${col}$2:${col}$8761,'{BUILD}'!$F$2:$F$8761,$B{r},"
                                  f"'{BUILD}'!$B$2:$B$8761,{h})/SUM('{BUILD}'!${col}$2:${col}$8761)")
            ws.cell(r, 28, f'=SUM(C{r}:Z{r})')

    # 6. checks
    _banner(ws, CHECKROW0 - 3, '6. Checks',
            "Each shape's hourly shares, multiplied by the days in each timeslice and added up, must equal 1.")
    _header(ws, CHECKROW0 - 1, ['Shape', 'Sum over the year\n(must be 1)',
                                'CHECK: is the sum off by more than\none in a million?  1 = problem'])
    for k, s in enumerate(SHAPES):
        r = CHECKROW0 + k
        a = SLICEROW0 + 6 * k
        ws.cell(r, 1, s)
        ws.cell(r, 2, f"=SUMPRODUCT($AB${a}:$AB${a + 5},'SHELF-days-per-timeslice'!$B$2:$B$7)")
        ws.cell(r, 3, f'=IF(ABS(B{r}-1)>0.000001,1,0)')
    ws.cell(CHECKROW0 + len(SHAPES) + 1, 1, 'Industries whose SHAPE USED is not in the list of shapes (must be 0)')
    ws.cell(CHECKROW0 + len(SHAPES) + 1, 2,
            f'=SUMPRODUCT(--(COUNTIF($A${LISTROW0}:$A${LISTROW0 + len(SHAPES) - 1},$C${ASGROW0}:$C${ASGROW0 + len(ASSIGN) - 1})=0))')

    ws.column_dimensions['A'].width = 46
    ws.column_dimensions['B'].width = 34
    for c in 'CDEFGH':
        ws.column_dimensions[c].width = 22
    for r in (SALESROW0 - 1, MONROW0 - 1, DAYROW0 - 1, AGROW0 - 1, CHECKROW0 - 1):
        ws.row_dimensions[r].height = 62
    for c in ('AB', 'AC', 'AD', 'AE'):
        ws.column_dimensions[c].width = 22


def add_ag_helpers(wb) -> None:
    """Day-type helper columns beside the utilities' daily agricultural profiles on the hand-built Ag tab, and a
    note saying where they are used. Safe to run on a tab that already has them."""
    ws = wb['Ag']
    assert ws['AB54'].value == '=MONTH(TRIM(B54))', ws['AB54'].value
    assert ws['A797'].value == 'date' and ws['E797'].value == 'month', (ws['A797'].value, ws['E797'].value)
    for r0, r1 in ((54, 418), (427, 791)):
        ws.cell(r0 - 1, 30, 'day_type')
        for r in range(r0, r1 + 1):
            ws.cell(r, 30, f'=IF(WEEKDAY(TRIM(B{r})+0,2)>5,"weekend","weekday")')
    ws.cell(797, 7, 'day_type')
    for r in range(798, 9558):
        ws.cell(r, 7, f'=IF(WEEKDAY(A{r},2)>5,"weekend","weekday")')
    ws['A4'] = (f"The '{DAY}' tab averages the same daily profiles by month and by weekday or weekend (the day_type "
                'helper columns beside the data below) to build the agriculture shape the model reads. The four '
                'calendar-season rows here are still used to take agriculture out of the month-to-month pattern of '
                'industrial electricity sales.')


EVIDENCE = [
    ('Pacific Gas and Electric', 'E-20T: largest customers, served at transmission voltage. Nearly flat through the day.', '2018-2019', 0.92,
     'Class average from metered customer samples (dynamic load profiles). 0.91 to 0.94 in every year from 2016 to 2025.'),
    ('Pacific Gas and Electric', 'E-20P: large customers served at primary voltage', '2018-2019', 0.85,
     'Class average from metered customer samples. Includes large commercial customers.'),
    ('San Diego Gas & Electric', "Customers with demand over 500 kW ('industrial' class)", '2018-2019', 0.87,
     'Class total from meters (dynamic load profiles). 0.86 in 2019 and 0.88 in 2018. Includes large commercial customers.'),
    ('AEP Ohio', 'Sub-transmission and transmission voltage, over 200 kW', '2024-2025', 0.75,
     'Class load from a sample of interval-metered customers. A region with much auto and metal manufacturing.'),
    ('AEP Ohio', 'Primary voltage, over 200 kW', '2024-2025', 0.83,
     'Class load from a sample of interval-metered customers.'),
    ('U.S. Energy Information Administration', 'All industrial sales, estimated from differences between 40 grid regions', '2024', 0.97,
     "Not a direct measurement. Each region's weekend-to-weekday demand (hourly grid monitor, Form EIA-930) is "
     'explained by its residential, commercial and industrial shares of sales (Form EIA-861). Plausible range 0.92 '
     'to 1.05; 0.94 (0.91 to 1.00) if Texas is left out. The same fit gives 0.85 for commercial and 1.04 for residential.'),
    ('Oak Ridge / Berkeley Lab simulated load shapes', "The seven industries on the 'Industry metered source' tab", '2018', 1.00,
     "0.96 to 1.02 by industry. The simulation sets each day's energy from the meter readings for that day's shape "
     'family rather than from weekend readings directly, so this is an indirect figure and likely too high.'),
]


def add_evidence_tab(wb) -> None:
    ws = wb.create_sheet(EVID)
    ws.cell(1, 1, 'How much less electricity industry uses on a weekend day than on a weekday: the evidence behind the '
                  'WEEKEND ENERGY USED settings').font = BOLD
    ws.cell(2, 1, f"Reference only: nothing on this tab feeds the calculation. The settings themselves are on the '{DAY}' "
                  'tab. The figures were calculated from the public files named on the About tab: for each month, the '
                  "average weekend day's energy divided by the average weekday's (holidays left out), then averaged "
                  'over the months.')
    _header(ws, 4, ['Source', 'Customers covered', 'Years', 'Weekend day as a share\nof a weekday', 'How it was measured, and limits'])
    for i, row in enumerate(EVIDENCE):
        for j, v in enumerate(row):
            ws.cell(5 + i, 1 + j, v).alignment = WRAP
    r = 5 + len(EVIDENCE) + 1
    ws.cell(r, 1, 'How the settings were chosen').font = BOLD
    text = [
        'Every utility class measured directly from meters shows a weekend dip. The classes that run flat through the '
        'day, which are the round-the-clock plants, dip least (0.92). Classes with a daytime rise dip more (0.75 to '
        '0.87), though they also contain large commercial customers, which pulls them down.',
        'Across all industrial sales the dip has to be small: actual U.S. demand is only about 5% lower on weekends, '
        'and commercial buildings account for most of that.',
        'The settings used are 0.95 for the shapes of round-the-clock industries (refining, cement, chemicals, paper) '
        'and 0.85 for the shapes with a daytime rise (food, and the steel shape that other factory industries share). '
        'Weighted by electricity use this is about 0.90 for industry as a whole. Each setting is uncertain by roughly '
        '0.05 either way.',
        'Older load-shape libraries put the weekend figure at 0.40 to 0.70. That range is not consistent with any of '
        'the metered classes above or with actual regional demand.',
    ]
    for i, t in enumerate(text):
        ws.cell(r + 1 + i, 1, t).alignment = WRAP
        ws.merge_cells(start_row=r + 1 + i, start_column=1, end_row=r + 1 + i, end_column=5)
        ws.row_dimensions[r + 1 + i].height = 48
    for col, w in zip('ABCDE', (34, 52, 12, 22, 90)):
        ws.column_dimensions[col].width = w
    ws.row_dimensions[4].height = 34


def add_output_tabs(wb, slice_labels: list[str], tags: list[str], tab_color: str) -> None:
    """SHELF-indstcat-<tag>: one row per industry, reading its assigned shape for that timeslice."""
    a0, a1 = ASGROW0, ASGROW0 + len(ASSIGN) - 1
    s0, s1 = SLICEROW0, SLICEROW0 + 6 * len(SHAPES) - 1
    for sl, tag in zip(slice_labels, tags):
        ws = wb.create_sheet(f'SHELF-indstcat-{tag}')
        ws.sheet_properties.tabColor = tab_color
        ws.cell(1, 1, UNIT_HDR)
        for h in range(24):
            ws.cell(1, 2 + h, f'Hour{h}')
        for i, (cat, *_) in enumerate(ASSIGN):
            r = 2 + i
            ws.cell(r, 1, label(cat))
            for h in range(24):
                col = L(3 + h)
                ws.cell(r, 2 + h, f"=SUMIFS('{DAY}'!{col}${s0}:{col}${s1},'{DAY}'!$A${s0}:$A${s1},"
                                  f"INDEX('{DAY}'!$C${a0}:$C${a1},MATCH($A{r},'{DAY}'!$B${a0}:$B${a1},0)),"
                                  f"'{DAY}'!$B${s0}:$B${s1},\"{sl}\")").number_format = '0.0000E+00'
        ws.column_dimensions['A'].width = 26


def add_all(wb, stamps, cols, slice_labels: list[str], tags: list[str], tab_color: str) -> None:
    add_source_tab(wb, stamps, cols)
    add_day_tab(wb, slice_labels)
    add_build_tab(wb)
    add_evidence_tab(wb)
    add_ag_helpers(wb)
    add_output_tabs(wb, slice_labels, tags, tab_color)
