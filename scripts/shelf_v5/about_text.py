"""Text of the About tab for the EPS 5.0 SHELF workbook, below the block the 4.0.x build writes.

Rows 44 onward of the tab: the sources added for the industry shapes, then the method notes. Each entry is
(text for column A or None, text for column B or None); an entry of (None, None) is a blank row. Written for
the published model: what a reader of the workbook needs, in plain language.
"""

# Replaces the 4.0.x "Zero categories" note: district heat, hydrogen and geoengineering are no longer zero.
ZERO_CATEGORIES_NOTE = ('residential-envelope, commercial-envelope, aircraft, ships, motorbikes - all zero in start year '
    'per EPS convention. May ramp up in later years for some scenarios; edit the tab directly to '
    'override. district-heat-hydrogen and geoeng carry the total end-use load shape (see below).')

FIRST_ROW = 44

ROWS = [
    ('Industrial End-Use Hourly Load Shapes',
     'EPRI'),
    (None,
     ('EPRI Load Shape Library (industrial HVAC, lighting, machine drives, process heating, cooling; by'
     ' season and day type)')),
    (None,
     'https://loadshape.epri.com/'),
    (None,
     ('Hourly shapes by industrial end use. They are used for the SHELF-indstproc tabs (the per-process'
     ' shapes), blended over calendar seasons and scaled by month with EIA industrial sales. See the '
     "'EPRI load shapes' and 'Industry blend' tabs.")),
    ('Industrial Hourly Load by Industry Category',
     'NREL'),
    (None,
     'NREL Manufacturing Thermal Energy Use dataset'),
    (None,
     'https://data.nrel.gov/submissions/118'),
    (None,
     ('Pre-aggregated outside Excel to season x hour by EPS industry category. Used only to take '
     "refining's steady load out of the monthly sales pattern applied to the per-process shapes.")),
    ('Agricultural Hourly Load Shapes',
     'California utilities (PG&E, SCE, SDG&E)'),
    (None,
     ('Agricultural rate-class load profiles for a full year, one row per day and one column per hour, '
     'from Southern California Edison (2026 static profiles), Pacific Gas and Electric (2025 static '
     'profiles) and San Diego Gas & Electric (2025), pasted on the Ag tab with their web addresses. A '
     "static profile is the utility's typical-year profile for the class, built from its meter "
     "samples. The three are weighted by each utility's agricultural electricity use. Limits: "
     'California farm load is mostly summer irrigation pumping, which may not represent farm load '
     'elsewhere, and the profiles are in Pacific time and are not shifted to Eastern time.')),
    ('Monthly Industrial Electricity Sales',
     'U.S. Energy Information Administration'),
    (None,
     ('Electricity Data Browser, retail sales of electricity, industrial sector, monthly '
     '(ELEC.SALES.US-IND.M)')),
    (None,
     'https://www.eia.gov/electricity/data/browser/'),
    ('Hourly Industrial Load by Industry',
     'Oak Ridge National Laboratory and Lawrence Berkeley National Laboratory'),
    (None,
     ('Simulation of Industrial Electrical Load Shapes (SIELS): state-level hourly electricity demand '
     'for seven manufacturing subsectors in 2018. Murthy, Smith, Okeke and Hubbard. Data on Mendeley '
     'Data, doi:10.17632/jhghzm9yk5; paper in Advances in Applied Energy 24 (2026) 100309.')),
    (None,
     2026),
    (None,
     'https://data.mendeley.com/datasets/jhghzm9yk5'),
    (None,
     ('Hourly load for food and beverage, pulp and paper, petroleum and coal products, chemicals, '
     "ammonia, cement, and iron, steel and ferroalloys, held on the 'Industry metered source' tab. The"
     ' authors built it from hourly meter readings at about 24,000 California industrial customers '
     "(2018-2019) and scaled it to each state's industrial electricity use. They had no California "
     'steel mills, so their steel series uses the shapes of other metal manufacturers. The files give '
     'each state in its own local time. Before pasting we moved each state to Eastern time (Central 1 '
     'hour later, Mountain 2, Pacific 3, Alaska 4, Hawaii 5) and added the states together, the same '
     'shift used for the NREL Electrification Futures Study profiles. Limits: these are California '
     "plants' habits applied to the whole country; the series is simulated, with occasional one-hour "
     "spikes; and it sets each day's energy from the readings for that day's shape rather than from "
     'weekend readings directly, so we take only the hour-by-hour shapes from it and set the weekend '
     'level separately. It should not be read as a measurement of any one state or plant.')),
    (None,
     None),
    ('Weekend Level of Industrial Load: California Utility Class Profiles',
     'Pacific Gas and Electric; San Diego Gas & Electric'),
    (None,
     ('PG&E dynamic load profiles by rate class (E-20T transmission voltage, E-20P primary voltage), '
     '2016-2025; SDG&E dynamic load profiles, customers with demand over 500 kW, 2016-2023')),
    (None,
     2026),
    (None,
     'https://www.pge.com/assets/rates/tariffs/energy_use_prices.shtml'),
    (None,
     ("Hourly class load measured from samples of metered customers. SDG&E's profiles are at "
     'https://dlp.extweb.sempra.com/. Used only to judge how far industrial load falls on weekends; '
     "the figures are on the 'Industry weekend evidence' tab and the files are not held in this "
     'workbook. Limits: these are classes by voltage or size, not by industry, so all but the '
     'transmission-voltage class include large commercial customers.')),
    (None,
     None),
    ('Weekend Level and Time of Day of Industrial Load: Ohio Utility Class Profiles',
     'AEP Ohio'),
    (None,
     ('Class load profiles by voltage level and size (sub-transmission and transmission voltage over '
     '200 kW; primary voltage over 200 kW), 2024-2025')),
    (None,
     2026),
    (None,
     'https://www.aepohio.com/company/about/choice/cres/load-profiles'),
    (None,
     ('Hourly class load from a sample of interval-metered customers. Used to judge the weekend level '
     'and to check the time-of-day shape of factory load outside California; the figures are on the '
     "'Industry weekend evidence' tab and the files are not held in this workbook. Limits: one utility"
     ' in one state, with a large share of auto and metal manufacturing; classes are by voltage, not '
     'by industry.')),
    (None,
     None),
    ('Weekend Level of Industrial Load: Regional Demand and Sales',
     'U.S. Energy Information Administration'),
    (None,
     ('Hourly Electric Grid Monitor (Form EIA-930), demand by balancing authority, 2024; Annual '
     'Electric Power Industry Report (Form EIA-861), sales to ultimate customers by sector, 2024')),
    (None,
     2025),
    (None,
     'https://www.eia.gov/electricity/gridmonitor/'),
    (None,
     ("Form EIA-861 is at https://www.eia.gov/electricity/data/eia861/. Each grid region's "
     'weekend-to-weekday demand was compared with its residential, commercial and industrial shares of'
     ' sales to estimate the weekend level of each sector. Used only as a bound on the industrial '
     "weekend level; the result is on the 'Industry weekend evidence' tab. Limits: an estimate from "
     'differences between 40 regions, not a measurement, and it explains only part of the variation '
     'between regions.')),
    (None,
     None),
    ('Industry tabs',
     ('The model can read industrial load shapes in two ways, and the list in ctrl-settings/ICwIwLF '
     'decides which one each industry uses. An industry on that list uses one shape for all of its '
     'electricity: the SHELF-indstcat-<timeslice> tabs, one row per industry. An industry not on the '
     'list uses a separate shape for each end use, such as machine drives or facility lighting: the '
     'SHELF-indstproc-<timeslice> tabs, one row per Industrial Process element. In the U.S. model '
     'every industry is on the list, so the per-process tabs are not used; they are kept so a region '
     'can switch an industry over. SHELF-indstCCS is the shape for electricity used by industrial '
     'carbon capture. SHELF-industry is a single all-industry shape that model versions before 5.0 '
     'read.')),
    ('How the whole-industry shapes are built',
     ("Each industry is given one of eight shapes on the 'Industry day shapes' tab: seven built from "
     'the Oak Ridge / Berkeley Lab data and one for agriculture. The steps, in the order they appear '
     'on that tab: (1) each industry is assigned a shape; (2) for each of the seven shapes we take the'
     " typical weekday and the typical weekend day, hour by hour, from the 'Industry metered source' "
     "tab, and scale the weekend day to a set share of a weekday's energy; (3) a month-to-month level "
     'comes from U.S. industrial electricity sales per day, after taking out agriculture; (4) '
     'agriculture gets a typical weekday and weekend day for each month from California utility '
     "profiles. The 'Industry hourly build' tab then lays these days out over a full year on the same "
     'calendar the clustering uses (weather year 2012, which starts on a Sunday). (5) Each shape is '
     'averaged over the days in each timeslice and divided by its annual total, the same way the '
     'buildings and transport tabs are built, and (6) checks confirm each shape adds up to 1 over the '
     'year. What differs between industries is mainly how much of the load falls at night and how far '
     'it falls on weekends.')),
    ('Weekend level',
     ("The Oak Ridge / Berkeley Lab data put a weekend day's electricity use almost equal to a "
     "weekday's. Utilities' metered profiles for their largest customers show a dip: about 8% for "
     'flat, round-the-clock loads and 13 to 25% for classes with a daytime rise, while actual demand '
     'across U.S. grid regions limits the dip for industry as a whole to roughly 0 to 9%. We therefore'
     " set a weekend day to 95% of a weekday's energy for the shapes of round-the-clock industries "
     '(refining, cement, chemicals, paper) and 85% for the shapes with a daytime rise (food, and the '
     'steel shape that other factory industries share), which is about 90% across all industrial '
     'electricity. Each setting is uncertain by about 5 percentage points. The settings are in the '
     "WEEKEND ENERGY USED column on the 'Industry day shapes' tab and can be edited there; the "
     "evidence is laid out on the 'Industry weekend evidence' tab. Holidays are treated as ordinary "
     'days.')),
    ('Agriculture',
     ('Agriculture uses daily load profiles for agricultural rate classes from three California '
     "utilities, weighted by each utility's agricultural electricity use (Ag tab). We average them by "
     'month and by weekday or weekend, so the shape keeps both its strong summer rise from irrigation '
     'and its weekend dip of about 10%. Two limits: California farm load may not represent farm load '
     'in other regions, and the profiles are left in Pacific time, so in a national model the farm '
     'peak falls up to three hours earlier in the day than it should.')),
    ('Industries that borrow a shape',
     ('The Oak Ridge / Berkeley Lab data cover food, paper, refining, chemicals, cement and steel. '
     'Every other industry borrows the shape of the most similar covered industry: other factory '
     'industries use the steel shape (which is itself built from other metal manufacturers), oil and '
     'gas extraction and pipelines use the refining shape, mining and glass use the cement shape, '
     'water and waste uses the paper shape, and construction uses the steel shape. About 45% of '
     'industrial electricity is on a borrowed shape. These are judgment calls and the least certain '
     'part of the file; construction and water and waste have no close match in any source. To change '
     "one, pick a different shape in the SHAPE USED column on the 'Industry day shapes' tab; the "
     'output tabs update on their own.')),
    ('What the shapes were checked against',
     ("Time of day: AEP Ohio's metered class for its largest customers has the same weekday pattern as "
     'the steel shape used here (lowest overnight, highest in mid-morning, back near the overnight '
     "level by evening), and PG&E's transmission-voltage class is flat through the day like the "
     'refining shape. Utility classes that include large commercial customers peak later, around 1 pm.'
     ' Weekend level: see the note above. Effect on the model: in runs without policies, replacing '
     'these shapes with completely flat ones, or giving every industry the shape with the strongest '
     'daytime rise, changed national peak demand by less than 3% and 2050 emissions by about 0.5%, so '
     'results are not sensitive to the remaining uncertainty in these shapes.')),
    ('Limits of the industry shapes',
     ('The hour-by-hour shapes come from California plants and are applied to the whole country; public'
     ' data by industry do not exist for other regions, only utility classes by voltage. The shapes do'
     " not vary by region. They describe today's plants: an industry that electrifies its process heat"
     " keeps the same shape. Older load-shape libraries (EPRI, the NEMS model, NREL's Electrification "
     'Futures Study) put weekend industrial load 30 to 60% below weekday load, which the metered '
     'classes and regional demand do not support.')),
    ('Updating the industry shapes',
     ("To use newer data, paste a national hourly series for each shape into the 'Industry metered "
     "source' tab (one year, Eastern time, with its day_of_year, hour_of_day and day_type columns), "
     'keep the column names, and the rest recalculates. To add a shape, add a column there and '
     "matching rows on the 'Industry day shapes' and 'Industry hourly build' tabs. If the clustering "
     'changes, nothing here needs editing: the build reads the day-to-timeslice list on the Clustering'
     ' tab. The rows of each SHELF-indstcat tab must stay in the same order as the industry list in '
     'ctrl-settings/ICwIwLF.')),
    ('How the per-process shapes are built',
     ('The EPRI, NREL and utility sources give shapes by calendar season (Dec-Feb, Mar-May, Jun-Aug, '
     'Sep-Nov), while the EPS timeslices are clusters of days that are not calendar seasons. The '
     "Industry slice weights tab counts, from the Clustering tab, what share of each timeslice's days "
     "falls in each calendar season, and the Industry blend tab builds each timeslice's shape as that "
     'weighted blend. The two peak timeslices use the EPRI peak-day shapes for the process elements. '
     'Every row is then scaled on the Industry blend tab so that its hourly values, summed over all '
     'timeslices and hours and weighted by days per timeslice, add to exactly 1.0.')),
    ('District heat, hydrogen and geoengineering',
     ('These sectors have little or no electricity use in the start year but can grow under policy (for'
     ' example grid electrolysis), so their tabs carry the shape of total national end-use load from '
     'the Cambium hourly source tab rather than zeros. Zeros would remove that electricity from the '
     'hourly dispatch entirely.')),
    ('Data centers',
     ('Data centers have one load shape per end use: facility load (cooling, ventilation and power '
     "distribution) and IT load ('other'). Both are flat for now - every hour of the year carries the "
     'same share of annual load. The cooling tab reads the IT tab, so a weather-driven cooling shape '
     'can be entered on its own tab later.')),
]
