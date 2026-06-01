"""
Prototype: ResStock/ComStock-based SHELF generator for VA.

Approach:
- Building categories (residential+commercial: heating/cooling/lighting/appliances/other) come from
  ResStock + ComStock (TMY-based, physics-based).
- Non-building categories (transport, industry, datacenters, etc.) keep current EFS-derived shapes.
- Peak day = single coincident system peak day from ResStock+ComStock combined.
- Non-peak slice labels match existing workbook labeling (Winter / Spring / Summer / Fall).
- Days-per-timeslice unchanged from existing.
- Output to: VA/elec/SHELF/_resstock_prototype/
"""
import pandas as pd
import numpy as np
from pathlib import Path
import openpyxl, csv, shutil

STATE = 'VA'
SHELF_DIR = Path(rf"C:\Users\RobbieOrvis\Models\state-eps-data-repository\{STATE}\elec\SHELF")
OUT_DIR = SHELF_DIR / "_resstock_prototype"
OUT_DIR.mkdir(exist_ok=True)
RS_DIR = Path(rf"C:\Users\RobbieOrvis\Models\ResStock SHELF\ResStock_Upgrade0\state={STATE}")
CS_DIR = Path(rf"C:\Users\RobbieOrvis\Models\ResStock SHELF\ComStock_tmy_release1\{STATE}")
WB = SHELF_DIR / "Seasonal Hourly Equipment Load Factors by End Use.xlsx"

# ---- 1) ResStock VA --------------------------------------------------------------
RS_RES = {
    # EPS AEO mapping: SpaceHeating only in heating bucket.
    # heating_hp_bkup is heat-pump electric resistance backup -> still SpaceHeating concept.
    'residential-heating': [
        'out.electricity.heating.energy_consumption.kwh',
        'out.electricity.heating_hp_bkup.energy_consumption.kwh',
        'out.electricity.heating_hp_bkup_fa.energy_consumption.kwh',
    ],
    # EPS AEO mapping: SpaceCooling + FurnaceFans (Furnace Fans and Boiler Circulation Pumps)
    # in cooling bucket. heating_fans_pumps from ResStock = AEO's FurnaceFans concept.
    'residential-cooling': [
        'out.electricity.cooling.energy_consumption.kwh',
        'out.electricity.cooling_fans_pumps.energy_consumption.kwh',
        'out.electricity.heating_fans_pumps.energy_consumption.kwh',
    ],
    'residential-lighting': [
        'out.electricity.lighting_interior.energy_consumption.kwh',
        'out.electricity.lighting_exterior.energy_consumption.kwh',
        'out.electricity.lighting_garage.energy_consumption.kwh',
    ],
    'residential-appliances': [
        'out.electricity.clothes_dryer.energy_consumption.kwh',
        'out.electricity.clothes_washer.energy_consumption.kwh',
        'out.electricity.dishwasher.energy_consumption.kwh',
        'out.electricity.range_oven.energy_consumption.kwh',
        'out.electricity.refrigerator.energy_consumption.kwh',
        'out.electricity.freezer.energy_consumption.kwh',
        'out.electricity.hot_water.energy_consumption.kwh',
    ],
    'residential-other': [
        'out.electricity.ceiling_fan.energy_consumption.kwh',
        'out.electricity.plug_loads.energy_consumption.kwh',
        'out.electricity.mech_vent.energy_consumption.kwh',
        'out.electricity.permanent_spa_heat.energy_consumption.kwh',
        'out.electricity.permanent_spa_pump.energy_consumption.kwh',
        'out.electricity.pool_heater.energy_consumption.kwh',
        'out.electricity.pool_pump.energy_consumption.kwh',
        'out.electricity.well_pump.energy_consumption.kwh',
    ],
}

print("Loading ResStock VA...")
all_rs_cols = sorted({c for cols in RS_RES.values() for c in cols})
rs_combined = None
for f in sorted(RS_DIR.glob('*.csv')):
    df = pd.read_csv(f, usecols=['timestamp']+all_rs_cols)
    if rs_combined is None:
        rs_combined = df.set_index('timestamp')
    else:
        rs_combined = rs_combined.add(df.set_index('timestamp'), fill_value=0)
rs_combined.index = pd.to_datetime(rs_combined.index)
print(f"  ResStock 15-min rows: {len(rs_combined)}")

rs_cat = pd.DataFrame(index=rs_combined.index)
for cat, cols in RS_RES.items():
    rs_cat[cat] = rs_combined[cols].sum(axis=1)
rs_cat['_residential_total'] = rs_cat.sum(axis=1)

# ---- 2) ComStock VA --------------------------------------------------------------
print("Loading ComStock VA...")
all_cs_cols = [
    'out.electricity.cooling.energy_consumption',
    'out.electricity.heating.energy_consumption',
    'out.electricity.heat_rejection.energy_consumption',
    'out.electricity.heat_recovery.energy_consumption',
    'out.electricity.fans.energy_consumption',
    'out.electricity.pumps.energy_consumption',
    'out.electricity.interior_lighting.energy_consumption',
    'out.electricity.exterior_lighting.energy_consumption',
    'out.electricity.interior_equipment.energy_consumption',
    'out.electricity.refrigeration.energy_consumption',
    'out.electricity.water_systems.energy_consumption',
]
cs_load = None
for f in sorted(CS_DIR.glob('*.csv')):
    df = pd.read_csv(f, usecols=['timestamp']+all_cs_cols)
    if cs_load is None:
        cs_load = df.set_index('timestamp')
    else:
        cs_load = cs_load.add(df.set_index('timestamp'), fill_value=0)
cs_load.index = pd.to_datetime(cs_load.index)
print(f"  ComStock 15-min rows: {len(cs_load)}")

# EPS AEO mapping for commercial:
#   heating  = SpaceHeating only
#   cooling  = SpaceCooling + Ventilation (= ALL fans + pumps + heat_rejection)
#   lighting = Lighting only
#   appl     = Refrigeration + Cooking + WaterHeating (= refrigeration + water_systems;
#              cooking is bundled inside ComStock's interior_equipment which we put in 'other')
#   other    = OfficeEquipment + Computing + OtherUses (= interior_equipment + heat_recovery)
cs_cat = pd.DataFrame(index=cs_load.index)
cs_cat['commercial-heating'] = cs_load['out.electricity.heating.energy_consumption']
cs_cat['commercial-cooling'] = (cs_load['out.electricity.cooling.energy_consumption']
                                + cs_load['out.electricity.heat_rejection.energy_consumption']
                                + cs_load['out.electricity.fans.energy_consumption']
                                + cs_load['out.electricity.pumps.energy_consumption'])
cs_cat['commercial-lighting'] = (cs_load['out.electricity.interior_lighting.energy_consumption']
                                 + cs_load['out.electricity.exterior_lighting.energy_consumption'])
cs_cat['commercial-appliances'] = (cs_load['out.electricity.refrigeration.energy_consumption']
                                   + cs_load['out.electricity.water_systems.energy_consumption'])
cs_cat['commercial-other'] = (cs_load['out.electricity.interior_equipment.energy_consumption']
                              + cs_load['out.electricity.heat_recovery.energy_consumption'])
cs_cat['_commercial_total'] = cs_cat.sum(axis=1)

# ---- 3) Combine + aggregate to hourly --------------------------------------------
all_cat = pd.concat([rs_cat, cs_cat], axis=1)
all_cat['_state_total'] = all_cat['_residential_total'] + all_cat['_commercial_total']
all_cat = all_cat.reset_index().rename(columns={'index':'ts','timestamp':'ts'})
all_cat['hour_start'] = (all_cat['ts'] - pd.Timedelta(minutes=15)).dt.floor('h')
hourly = all_cat.drop(columns=['ts']).groupby('hour_start').sum().reset_index().rename(columns={'hour_start':'ts'})
hourly['day'] = hourly['ts'].dt.dayofyear
hourly['hour'] = hourly['ts'].dt.hour
print(f"\nHourly rows: {len(hourly)}")
print(f"Annual residential total: {hourly['_residential_total'].sum()/1e6:,.0f} GWh")
print(f"Annual commercial total : {hourly['_commercial_total'].sum()/1e6:,.0f} GWh")
print(f"Annual state-bldg total : {hourly['_state_total'].sum()/1e6:,.0f} GWh")

# ---- 4) Identify TOP-N peak days per season (for averaging) ----------------------
N_PEAK = 5
daily_peak = hourly.groupby('day')['_state_total'].max()
summer_days_pool = [d for d in daily_peak.index if d in range(152, 244)]
winter_days_pool = [d for d in daily_peak.index if d <= 60 or d >= 335]
sp_top_days = sorted(daily_peak.loc[summer_days_pool].sort_values(ascending=False).head(N_PEAK).index.tolist())
wp_top_days = sorted(daily_peak.loc[winter_days_pool].sort_values(ascending=False).head(N_PEAK).index.tolist())
sp_day = sp_top_days[0]  # legacy single-day variable kept for any references
wp_day = wp_top_days[0]
print(f"\nSummer peak slice: top-{N_PEAK} days {sp_top_days}")
print(f"Winter peak slice: top-{N_PEAK} days {wp_top_days}")
print(f"  Summer top day peak: {daily_peak.loc[sp_top_days[0]]/1e3:,.0f} MW; top-5 mean peak: {daily_peak.loc[sp_top_days].mean()/1e3:,.0f} MW")
print(f"  Winter top day peak: {daily_peak.loc[wp_top_days[0]]/1e3:,.0f} MW; top-5 mean peak: {daily_peak.loc[wp_top_days].mean()/1e3:,.0f} MW")

# ---- 5) Apply workbook day labels ------------------------------------------------
wb = openpyxl.load_workbook(WB, read_only=True, data_only=True)
ws = wb['Summarized Data']
day_label = {}
for row in ws.iter_rows(min_row=4, max_row=ws.max_row, values_only=True):
    if row[0] is None: continue
    if row[1] is not None and row[9] is not None:
        day_label[int(row[1])] = row[9]
wb.close()
hourly['slice'] = hourly['day'].map(day_label)

# ---- 6) Build SHELFs per building category ---------------------------------------
BLDG_CATS = list(RS_RES.keys()) + ['commercial-heating','commercial-cooling','commercial-lighting','commercial-appliances','commercial-other']
shelf_template_path = SHELF_DIR / "SHELF-residential-cooling.csv"
template = list(csv.reader(open(shelf_template_path)))
header = template[0]

def compute_shelf(cat, hourly_df, sp_top_days, wp_top_days):
    """Peak slices = top-N day MEAN profile (smooths cold-snap and heat-wave idiosyncrasies)."""
    annual = hourly_df[cat].sum()
    if annual == 0:
        return {sl: [0.0]*24 for sl in ['Winter','Spring','Summer','Fall','Summer Peak','Winter Peak']}
    df = hourly_df.copy()
    df['lf'] = df[cat] / annual
    out = {}
    for season in ['Winter','Spring','Summer','Fall']:
        mask = df['slice'].str.startswith(season)
        if mask.sum() == 0:
            out[season] = [0.0]*24
        else:
            v = df.loc[mask].groupby('hour')['lf'].mean().reindex(range(24)).fillna(0).values
            out[season] = list(v)
    # Peak slices: mean across top-N days (smooths single-day extremes)
    sp = df[df['day'].isin(sp_top_days)].groupby('hour')['lf'].mean().reindex(range(24)).fillna(0).values
    wp = df[df['day'].isin(wp_top_days)].groupby('hour')['lf'].mean().reindex(range(24)).fillna(0).values
    out['Summer Peak'] = list(sp)
    out['Winter Peak'] = list(wp)
    return out

print("\nGenerating building SHELFs...")
results_summary = []
for cat in BLDG_CATS:
    shelf_path = SHELF_DIR / f"SHELF-{cat}.csv"
    out_path = OUT_DIR / f"SHELF-{cat}.csv"
    if not shelf_path.exists():
        print(f"  [skip] {cat}: no template at {shelf_path}")
        continue
    shelf = compute_shelf(cat, hourly, sp_top_days, wp_top_days)
    rows = [header]
    for sl in ['Winter','Spring','Summer','Fall','Summer Peak','Winter Peak']:
        vals = shelf[sl]
        rows.append([sl] + [repr(float(v)) if float(v) != 0.0 else '0.0' for v in vals])
    with open(out_path, 'w', newline='') as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)
    # Compare to old
    old_rows = list(csv.reader(open(shelf_path)))
    old_sp = [float(v) for v in old_rows[5][1:25]]
    old_wp = [float(v) for v in old_rows[6][1:25]]
    old_sp_max = max(old_sp); old_wp_max = max(old_wp)
    new_sp_max = max(shelf['Summer Peak']); new_wp_max = max(shelf['Winter Peak'])
    sp_chg = (new_sp_max/old_sp_max - 1)*100 if old_sp_max > 0 else 0
    wp_chg = (new_wp_max/old_wp_max - 1)*100 if old_wp_max > 0 else 0
    results_summary.append((cat, old_sp_max, new_sp_max, sp_chg, old_wp_max, new_wp_max, wp_chg))

# ---- 7) Copy non-building SHELFs verbatim ----------------------------------------
print("\nCopying non-building SHELFs from existing (post-MAXIFS-fix)...")
NON_BLDG = ['LDVs','HDVs','aircraft','rail','ships','motorbikes','industry',
            'district-heat-hydrogen','geoeng','datacenters',
            'residential-envelope','commercial-envelope','days-per-timeslice']
copied = 0
for cat in NON_BLDG:
    src = SHELF_DIR / f"SHELF-{cat}.csv"
    dst = OUT_DIR / f"SHELF-{cat}.csv"
    if src.exists():
        shutil.copy2(src, dst)
        copied += 1
print(f"  Copied {copied} non-building CSVs")

# ---- 8) Summary ------------------------------------------------------------------
print(f"\n{'='*100}")
print(f"Summary: building SHELFs - peak hour LF before (EFS+MAXIFS-fix) vs after (ResStock/ComStock)")
print(f"{'='*100}")
print(f"  {'category':30s}  {'SP old':>11s}  {'SP new':>11s}  {'%chg':>7s}   {'WP old':>11s}  {'WP new':>11s}  {'%chg':>7s}")
for cat, ospm, nspm, spc, owpm, nwpm, wpc in results_summary:
    print(f"  {cat:30s}  {ospm:11.4e}  {nspm:11.4e}  {spc:+6.1f}%   {owpm:11.4e}  {nwpm:11.4e}  {wpc:+6.1f}%")

print(f"\nOutput written to: {OUT_DIR}")
print(f"CSVs generated: {len(list(OUT_DIR.glob('SHELF-*.csv')))}")
