"""Demand and generation category registry.

These category names lock the SHELF and SYSHECF CSV file naming. The pipeline
must produce one CSV per category per state, matching what the EPS model
expects to read.

For each SHELF demand category:
  - source: where the annual energy value comes from (per state)
  - shape_source: where the hourly load shape comes from
  - shape_keys: ResStock/ComStock/EFS columns that build the shape
  - bucket_role: residential / commercial / transportation / industry / other
  - eps_aeo_aggregation: how EPS BCEU / AEO aggregates this category
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DemandCategory:
    """One end-use category that produces a SHELF-{name}.csv file."""
    name: str
    bucket: str                  # 'residential', 'commercial', 'transportation', 'industry', 'other'
    source_file: str             # human-readable description of where the annual comes from
    shape_source: str            # human-readable description of where the hourly shape comes from
    notes: Optional[str] = None


@dataclass(frozen=True)
class GenerationCategory:
    """One generation tech that produces a SYSHECF-{name}.csv file."""
    name: str
    is_variable: bool            # True if hourly CF varies (solar, wind, hydro); False if mostly constant
    cambium_column: Optional[str] # column name in Cambium hourly file (e.g., 'upv_MWh', 'wind-ons_MWh')
    cambium_capacity_column: Optional[str]  # corresponding capacity column in Cambium annual file
    notes: Optional[str] = None


# =============================================================================
# SHELF demand categories — 22 total, 2 envelope categories are always-zero
# =============================================================================
SHELF_CATEGORIES = [
    # ---- Residential buildings ----
    DemandCategory(
        name='residential-heating',
        bucket='residential',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (urban+rural residential heating, electricity)',
        shape_source='ResStock heating + heating_hp_bkup + heating_hp_bkup_fa (per AEO BCEU mapping)',
        notes='Excludes heating_fans_pumps (those go to cooling per AEO Furnace Fans bucket)',
    ),
    DemandCategory(
        name='residential-cooling',
        bucket='residential',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (urban+rural residential cooling, electricity)',
        shape_source='ResStock cooling + cooling_fans_pumps + heating_fans_pumps (AEO SpaceCooling + FurnaceFans)',
    ),
    DemandCategory(
        name='residential-lighting',
        bucket='residential',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (urban+rural residential lighting, electricity)',
        shape_source='ResStock lighting_interior + lighting_exterior + lighting_garage',
    ),
    DemandCategory(
        name='residential-appliances',
        bucket='residential',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (urban+rural residential appl, electricity)',
        shape_source='ResStock clothes_dryer + clothes_washer + dishwasher + range_oven + refrigerator + freezer + hot_water',
        notes='AEO BCEU "appl" includes water heating + cooking + appliances; matched to ResStock columns',
    ),
    DemandCategory(
        name='residential-other',
        bucket='residential',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (urban+rural residential other, electricity)',
        shape_source='ResStock ceiling_fan + plug_loads + mech_vent + spa/pool/well_pump',
        notes='AEO BCEU "other" = OtherUses + TVs + Computers; ResStock plug_loads captures TVs/computers',
    ),
    DemandCategory(
        name='residential-envelope',
        bucket='residential',
        source_file='(always zero)',
        shape_source='(always zero)',
        notes='Envelope SHELFs are intentionally zero by EPS convention',
    ),
    # ---- Commercial buildings ----
    DemandCategory(
        name='commercial-heating',
        bucket='commercial',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (commercial heating, electricity)',
        shape_source='ComStock heating',
    ),
    DemandCategory(
        name='commercial-cooling',
        bucket='commercial',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (commercial cooling, electricity)',
        shape_source='ComStock cooling + heat_rejection + ALL fans + ALL pumps (AEO SpaceCooling + Ventilation)',
    ),
    DemandCategory(
        name='commercial-lighting',
        bucket='commercial',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (commercial lighting, electricity)',
        shape_source='ComStock interior_lighting + exterior_lighting',
    ),
    DemandCategory(
        name='commercial-appliances',
        bucket='commercial',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (commercial appl, electricity)',
        shape_source='ComStock refrigeration + water_systems',
        notes='Cooking partially undercounted (lumped in interior_equipment which we put in other)',
    ),
    DemandCategory(
        name='commercial-other',
        bucket='commercial',
        source_file='bldgs/BCEU/BAU Components Energy Use.xlsx (commercial other, electricity)',
        shape_source='ComStock interior_equipment + heat_recovery',
        notes='AEO BCEU "other" = Computing + OfficeEquipment + OtherUses',
    ),
    DemandCategory(
        name='commercial-envelope',
        bucket='commercial',
        source_file='(always zero)',
        shape_source='(always zero)',
    ),
    # ---- Transportation (matches existing SHELF transportation categories) ----
    DemandCategory(
        name='LDVs',
        bucket='transportation',
        source_file='Computed: stock × distance × loading / fuel_economy × electricity_share for LDV vehicle types',
        shape_source='EFS Transportation light-duty vehicles hourly',
        notes='Inputs: trans/SYVbT, AVLo, BAADTbVT, SYFAFE, BPoEFUbVT (LDV rows)',
    ),
    DemandCategory(
        name='HDVs',
        bucket='transportation',
        source_file='Computed: same formula, HDV + MDV vehicle types aggregated',
        shape_source='EFS Transportation heavy-duty + medium-duty trucks hourly',
        notes='MDVs aggregated into HDVs to match SHELF category structure',
    ),
    DemandCategory(
        name='aircraft',
        bucket='transportation',
        source_file='Computed: same formula for aircraft vehicle types',
        shape_source='EFS Transportation other (placeholder until aircraft-specific shape sourced)',
    ),
    DemandCategory(
        name='rail',
        bucket='transportation',
        source_file='Computed: same formula for rail vehicle types',
        shape_source='EFS Transportation other (placeholder)',
    ),
    DemandCategory(
        name='ships',
        bucket='transportation',
        source_file='Computed: same formula for ship vehicle types',
        shape_source='EFS Transportation other (placeholder)',
    ),
    DemandCategory(
        name='motorbikes',
        bucket='transportation',
        source_file='Computed: same formula for motorbike vehicle types',
        shape_source='EFS Transportation light-duty vehicles (proxy)',
    ),
    # ---- Industrial ----
    DemandCategory(
        name='industry',
        bucket='industry',
        source_file='indst/BIFUbC/BIFUbC-electricity.csv (sum across NAICS/ISIC categories for start year)',
        shape_source='EFS Industrial machine drives + other + process heat',
    ),
    # ---- Other (will be populated later for several of these) ----
    DemandCategory(
        name='district-heat-hydrogen',
        bucket='other',
        source_file='dist-heat/* and hydgn/* (TODO map specific files); zero in start year v1',
        shape_source='Follows industry shape (per existing pipeline convention)',
        notes='Ramps up post-2030 in EPS scenarios; zero for start year is approximately correct',
    ),
    DemandCategory(
        name='geoeng',
        bucket='other',
        source_file='geoeng/* DAC + ERW (TODO map specific files); zero in start year v1',
        shape_source='Follows industry shape',
        notes='DAC/ERW are post-2030 technologies; zero for start year is approximately correct',
    ),
    DemandCategory(
        name='datacenters',
        bucket='other',
        source_file='Per-state data center annual demand (architected to be populated from external source TBD)',
        shape_source='Flat 1/8760 (constant per hour)',
        notes='Currently zero per VA EPS convention; pipeline supports population when state-level DC data integrated',
    ),
]


# =============================================================================
# SYSHECF generation categories — 26 total
# Variable techs derive hourly CFs from Cambium; non-variable use templates.
# =============================================================================
SYSHECF_CATEGORIES = [
    # ---- Variable renewables (hourly from Cambium) ----
    GenerationCategory('solar-pv', True, 'upv_MWh', 'upv_MW',
                       'Utility-scale solar PV; CF = generation / capacity'),
    GenerationCategory('solar-pv-dist', True, 'distpv_MWh', 'distpv_MW',
                       'Distributed (rooftop) solar PV; behind-the-meter in Cambium'),
    GenerationCategory('solar-thermal', True, 'csp_MWh', 'csp_MW',
                       'Concentrating solar power'),
    GenerationCategory('onshore-wind', True, 'wind-ons_MWh', 'wind-ons_MW', None),
    GenerationCategory('offshore-wind', True, 'wind-ofs_MWh', 'wind-ofs_MW', None),
    # ---- Hydro and storage (hourly from Cambium) ----
    GenerationCategory('hydro', True, 'hydro_MWh', 'hydro_MW',
                       'Conventional hydro; can be variable due to operations + season'),
    GenerationCategory('pumped-hydro', True, 'phs_MWh', 'phs_MW',
                       'Note: phs_MWh is dispatched generation, may show negative/zero during charging'),
    # ---- Thermal (mostly constant CF, can derive from Cambium for v1) ----
    GenerationCategory('nuclear', True, 'nuclear_MWh', 'nuclear_MW',
                       'Typical CF ~0.90-0.93 from operations'),
    GenerationCategory('combined-cycle', True, 'gas-cc_MWh', 'gas-cc_MW', None),
    GenerationCategory('combined-cycle-CCS', True, 'gas-cc-ccs_MWh', 'gas-cc-ccs_MW', None),
    GenerationCategory('natural-gas-peaker', True, 'gas-ct_MWh', 'gas-ct_MW',
                       'Aka gas combustion turbine; low CF'),
    GenerationCategory('hard-coal', True, 'coal_MWh', 'coal_MW', None),
    GenerationCategory('hard-coal-CCS', True, 'coal-ccs_MWh', 'coal-ccs_MW', None),
    GenerationCategory('lignite', False, None, None,
                       'No US Cambium category; template-only'),
    GenerationCategory('lignite-CCS', False, None, None,
                       'No US Cambium category; template-only'),
    GenerationCategory('biomass', True, 'biomass_MWh', 'biomass_MW', None),
    GenerationCategory('biomass-CCS', True, 'beccs_MWh', 'beccs_MW',
                       'Cambium beccs = bioenergy with CCS'),
    GenerationCategory('geothermal', True, 'geothermal_MWh', 'geothermal_MW', None),
    GenerationCategory('petroleum', True, 'o-g-s_MWh', 'o-g-s_MW',
                       'o-g-s = oil-gas-steam (residual+kerosene-fired steam units)'),
    GenerationCategory('heavy-or-residual-oil', False, None, None,
                       'Subset of o-g-s; template-only'),
    GenerationCategory('crude-oil', False, None, None,
                       'Negligible US generation; template-only'),
    GenerationCategory('hydrogen-CC', False, None, None,
                       'Not in Cambium 2022; ramps up in scenarios; template-only for v1'),
    GenerationCategory('hydrogen-CT', False, None, None,
                       'Same as hydrogen-CC; template-only for v1'),
    GenerationCategory('SMR', False, None, None,
                       'Small modular reactor; template-only for v1'),
    GenerationCategory('MSW', False, None, None,
                       'Municipal solid waste; template-only for v1'),
    GenerationCategory('steam-turbine', False, None, None,
                       'Generic steam turbine; template-only for v1'),
]


# Convenience accessors
SHELF_BY_NAME = {c.name: c for c in SHELF_CATEGORIES}
SYSHECF_BY_NAME = {c.name: c for c in SYSHECF_CATEGORIES}


def shelf_categories_by_bucket(bucket: str) -> list:
    """Return SHELF categories whose bucket matches (e.g., 'residential')."""
    return [c for c in SHELF_CATEGORIES if c.bucket == bucket]
