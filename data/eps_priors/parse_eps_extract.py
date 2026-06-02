"""
parse_eps_extract.py — Parse an EPS BAU sectoral electricity demand TSV
(produced by Vensim DSS vdf2tab) into a tidy CSV usable as a magnitude prior
for the Zapata ridge NNLS calibration.

Output schema:
  end_use,year,eps_mwh_per_year

End-use names match the Mendeley/Zapata convention used by
build_zapata_hybrid_basis. EPS Building Component dimension maps as:
  heating              -> residential_heating / service_heating
  cooling and ventilation -> residential_cooling / service_cooling
  envelope             -> dropped (zero electricity in EPS)
  lighting             -> residential_lighting / service_lighting
  appliances           -> residential_appliances / service_appliances
  other component      -> residential_other / service_other

Run from repo root:
  python data/eps_priors/parse_eps_extract.py <tsv_path> <country_iso2> <initial_year> <final_year>
"""
from __future__ import annotations

import os
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import pandas as pd

# EPS Building Component → Zapata/Mendeley end-use suffix
EPS_COMPONENT_TO_ENDUSE_SUFFIX = {
    'heating':                  'heating',
    'cooling and ventilation':  'cooling',
    'envelope':                 None,        # always zero in EPS
    'lighting':                 'lighting',
    'appliances':               'appliances',
    'other component':          'other',
}

# EPS Building Type → Mendeley sector prefix
EPS_TYPE_TO_PREFIX = {
    'urban residential': 'residential',
    'rural residential': 'residential',  # summed with urban
    'commercial':        'service',
}


def parse_subscript(var_name: str) -> tuple[str, list[str]]:
    """Split 'Foo[a,b,c]' into ('Foo', ['a','b','c'])."""
    if '[' not in var_name:
        return var_name.strip(), []
    base, rest = var_name.split('[', 1)
    subs = rest.rstrip(']').split(',')
    return base.strip(), [s.strip() for s in subs]


def parse_tsv(tsv_path: str, initial_year: int, final_year: int) -> pd.DataFrame:
    """Parse vdf2tab TSV into long-format DataFrame with columns
    [variable, subscripts, year, value]."""
    years = list(range(initial_year, final_year + 1))
    rows = []
    with open(tsv_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < len(years) + 2:
                continue
            name = parts[0]
            # parts[1] = run name, parts[2:2+len(years)] = yearly values
            try:
                vals = [float(v) for v in parts[2:2 + len(years)]]
            except ValueError:
                continue
            base, subs = parse_subscript(name)
            for y, v in zip(years, vals):
                rows.append((base, tuple(subs), y, v))
    return pd.DataFrame(rows, columns=['variable', 'subscripts', 'year', 'value'])


def to_enduse_prior(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate parsed TSV into per-end-use × year magnitudes.

    Returns long-form DataFrame with columns [end_use, year, eps_mwh_per_year].
    """
    out_rows = []

    # Buildings: subscripts = (BuildingType, BuildingComponent)
    bld = df[df['variable'] == 'BAU Buildings Sector Electricity Demand']
    for (subs, year), grp in bld.groupby(['subscripts', 'year']):
        if len(subs) != 2:
            continue
        btype, bcomp = subs
        bcomp_norm = bcomp.lower().strip()
        suffix = EPS_COMPONENT_TO_ENDUSE_SUFFIX.get(bcomp_norm)
        prefix = EPS_TYPE_TO_PREFIX.get(btype.lower().strip())
        if suffix is None or prefix is None:
            continue
        end_use = f"{prefix}_{suffix}"
        out_rows.append((end_use, year, float(grp['value'].sum())))

    # Industry
    ind = df[df['variable'] == 'BAU Industrial Sector Electricity Demand']
    for _, r in ind.iterrows():
        out_rows.append(('industry', int(r['year']), float(r['value'])))

    # Transport — sum across vehicle/cargo combos
    trans = df[df['variable'] == 'BAU Transportation Sector Electricity Demand']
    for year, grp in trans.groupby('year'):
        out_rows.append(('transport', int(year), float(grp['value'].sum())))

    # District heat + hydrogen + data centers — combine into a single
    # 'other_sectors' bucket since Mendeley doesn't separate them
    misc_vars = [
        'BAU District Heat Electricity Demand',
        'BAU Hydrogen Sector Grid Electricity Demand',
        'BAU Data Center Load',
    ]
    misc = df[df['variable'].isin(misc_vars)]
    for year, grp in misc.groupby('year'):
        v = float(grp['value'].sum())
        if v > 0:
            out_rows.append(('other_sectors', int(year), v))

    prior = pd.DataFrame(out_rows, columns=['end_use', 'year', 'eps_mwh_per_year'])
    # Aggregate (residential_* and service_* are already aggregated by groupby above
    # but urban/rural residential map to the same prefix; aggregate by sum)
    prior = prior.groupby(['end_use', 'year'], as_index=False)['eps_mwh_per_year'].sum()
    return prior


def main() -> None:
    if len(sys.argv) < 5:
        print(__doc__)
        sys.exit(1)
    tsv_path = sys.argv[1]
    iso2 = sys.argv[2].upper()
    initial_year = int(sys.argv[3])
    final_year = int(sys.argv[4])

    print(f"[parse] reading {tsv_path}")
    raw = parse_tsv(tsv_path, initial_year, final_year)
    print(f"[parse] {len(raw):,} (variable, year) rows, {raw['variable'].nunique()} variables")

    prior = to_enduse_prior(raw)
    print(f"[map ] {len(prior):,} (end_use, year) rows, {prior['end_use'].nunique()} end-uses")

    # Coverage check against BAU Total
    total = raw[raw['variable'] == 'BAU Total Electricity Demand'].set_index('year')['value']
    mapped = prior.groupby('year')['eps_mwh_per_year'].sum()
    coverage = (mapped / total).dropna()
    print(f"[chk ] coverage vs BAU Total: min={coverage.min():.4f} max={coverage.max():.4f}")
    if (coverage < 0.99).any() or (coverage > 1.01).any():
        print(f"[warn] coverage outside [0.99, 1.01] for some years — check mapping")

    # Save output
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, f"eps_prior_{iso2}.csv")
    prior.to_csv(out_path, index=False)
    print(f"[save] {out_path}")

    # Show a sample year
    sample_year = (initial_year + final_year) // 2
    if sample_year in prior['year'].values:
        print()
        print(f"=== EPS-{iso2} {sample_year} BAU sectoral electricity demand (MWh/yr) ===")
        s = prior[prior['year'] == sample_year].sort_values(
            'eps_mwh_per_year', ascending=False,
        )
        for _, r in s.iterrows():
            print(f"  {r['end_use']:<26} {r['eps_mwh_per_year']:>20,.0f}")


if __name__ == '__main__':
    main()
