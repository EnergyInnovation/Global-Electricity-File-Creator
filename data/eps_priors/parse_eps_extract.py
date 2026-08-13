"""parse_eps_extract.py — Parse an EPS BAU TSV export (Vensim DSS vdf2tab)
into tidy prior CSVs for the Zapata ridge NNLS calibration.

Writes two files per region, both stamped with a provenance header
(see eps_provenance.py) recording the source model path, version, base/final
year, git branch + commit, working-tree state, and extraction date:

  eps_prior_<ISO2>.csv     end_use,year,eps_mwh_per_year   BAU electricity demand by sector
  eps_capacity_<ISO2>.csv  tech,year,eps_mw                BAU generation capacity by technology

End-use names match the Mendeley/Zapata convention used by
build_zapata_hybrid_basis. EPS Building Component dimension maps as:
  heating              -> residential_heating / service_heating
  cooling and ventilation -> residential_cooling / service_cooling
  envelope             -> dropped (zero electricity in EPS)
  lighting             -> residential_lighting / service_lighting
  appliances           -> residential_appliances / service_appliances
  other component      -> residential_other / service_other

Capacity technology names are the raw EPS `Electricity Source` subscripts
(e.g. `onshore wind es`), NOT remapped — the SYSHECF side of the pipeline
already speaks EPS tech names, and remapping here would only lose information.

Run from repo root:
  python data/eps_priors/parse_eps_extract.py <tsv_path> <iso2> <initial_year> <final_year> \
      --model-dir <path to EPS checkout> [--vensim <vendss64.exe>] [--note "..."]

The TSV is produced by the eps-run recipe; see run_extractions.py for the
orchestrator that runs every region end to end.
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eps_provenance  # noqa: E402

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

# Variables the export must contain. Demand drives eps_prior_<ISO2>.csv;
# capacity drives eps_capacity_<ISO2>.csv.
DEMAND_VARS = [
    'BAU Buildings Sector Electricity Demand',
    'BAU Industrial Sector Electricity Demand',
    'BAU Transportation Sector Electricity Demand',
    'BAU District Heat Electricity Demand',
    'BAU Hydrogen Sector Grid Electricity Demand',
    'BAU Data Center Load',
    'BAU Total Electricity Demand',
]
CAPACITY_VAR = 'BAU Electricity Generation Capacity'
DISTRIBUTED_CAPACITY_VAR = 'BAU Distributed Electricity Source Capacity'


def parse_subscript(var_name: str) -> tuple[str, list[str]]:
    """Split 'Foo[a,b,c]' into ('Foo', ['a','b','c'])."""
    if '[' not in var_name:
        return var_name.strip(), []
    base, rest = var_name.split('[', 1)
    subs = rest.rstrip(']').split(',')
    return base.strip(), [s.strip() for s in subs]


def parse_tsv(tsv_path: str, initial_year: int, final_year: int) -> pd.DataFrame:
    """Parse vdf2tab TSV into long-format DataFrame with columns
    [variable, subscripts, year, value].

    Column positions are taken from the ``Time`` header row rather than assumed.
    VDF2TAB's layout varies with the flags it was invoked under — some exports
    carry a run-name column between the variable name and the first year, some
    don't — and a hardcoded offset silently yields zero rows (or, worse,
    off-by-one values) when it guesses wrong. Reading the header is the only
    layout-independent way to find the years.
    """
    with open(tsv_path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline().rstrip('\n').split('\t')
    year_cols = [(i, int(c)) for i, c in enumerate(header)
                 if c.strip().isdigit() and len(c.strip()) == 4]
    if not year_cols:
        raise ValueError(
            f"{tsv_path}: no 4-digit year columns in the header row. "
            f"First cells: {header[:5]}. Was the export written by VDF2TAB?"
        )

    span = (year_cols[0][1], year_cols[-1][1])
    if span != (initial_year, final_year):
        print(f"[warn] TSV covers {span[0]}-{span[1]} but {initial_year}-{final_year} "
              f"was requested; using the TSV's own span")

    rows = []
    with open(tsv_path, 'r', encoding='utf-8', errors='replace') as f:
        next(f)  # header
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) <= year_cols[-1][0]:
                continue
            base, subs = parse_subscript(parts[0])
            for idx, year in year_cols:
                try:
                    value = float(parts[idx])
                except ValueError:
                    continue
                rows.append((base, tuple(subs), year, value))
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


def to_capacity_prior(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate parsed TSV into per-technology × year generation capacity (MW).

    Grid-connected capacity comes from ``BAU Electricity Generation Capacity``
    (subscript: Electricity Source). Distributed capacity is reported
    separately by EPS, subscripted by (Building Type, Electricity Source); it
    is summed across building types and emitted as ``<tech> (distributed)``
    rather than folded in, because the SYSHECF side treats distributed solar
    as its own technology with its own derate.
    """
    out_rows = []

    grid = df[df['variable'] == CAPACITY_VAR]
    for (subs, year), grp in grid.groupby(['subscripts', 'year']):
        if len(subs) != 1:
            continue
        out_rows.append((subs[0], int(year), float(grp['value'].sum())))

    dist = df[df['variable'] == DISTRIBUTED_CAPACITY_VAR]
    for (subs, year), grp in dist.groupby(['subscripts', 'year']):
        if len(subs) != 2:
            continue
        # (Building Type, Electricity Source) — sum over building types
        out_rows.append((f'{subs[1]} (distributed)', int(year), float(grp['value'].sum())))

    cap = pd.DataFrame(out_rows, columns=['tech', 'year', 'eps_mw'])
    if cap.empty:
        return cap
    return cap.groupby(['tech', 'year'], as_index=False)['eps_mw'].sum()


def report_missing(raw: pd.DataFrame) -> list[str]:
    """Names from DEMAND_VARS / capacity vars absent from the export."""
    present = set(raw['variable'].unique())
    wanted = DEMAND_VARS + [CAPACITY_VAR, DISTRIBUTED_CAPACITY_VAR]
    return [v for v in wanted if v not in present]


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument('tsv_path')
    ap.add_argument('iso2')
    ap.add_argument('initial_year', type=int)
    ap.add_argument('final_year', type=int)
    ap.add_argument('--model-dir', required=True,
                    help='EPS model checkout the TSV was exported from. Version, '
                         'base/final year, and git branch/commit are read from it.')
    ap.add_argument('--vensim', default=None,
                    help='Path to the vendss64.exe used for the run (provenance only).')
    ap.add_argument('--note', action='append', default=[],
                    help='Extra provenance note line (repeatable).')
    ap.add_argument('--working-tree', default=None,
                    help="Override the recorded working-tree state. Parsing usually happens "
                         "after the tree has been restored (e.g. a git stash popped once the "
                         "run finished), so the state at parse time can misdescribe the state "
                         "the model actually ran under. Pass the run-time state here.")
    ap.add_argument('--out-dir', default=None,
                    help='Where to write the CSVs (default: this script\'s folder).')
    args = ap.parse_args()

    iso2 = args.iso2.upper()
    out_dir = args.out_dir or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)

    print(f"[parse] reading {args.tsv_path}")
    raw = parse_tsv(args.tsv_path, args.initial_year, args.final_year)
    print(f"[parse] {len(raw):,} (variable, year) rows, {raw['variable'].nunique()} variables")

    missing = report_missing(raw)
    if missing:
        print(f"[warn] variables absent from the export: {missing}")

    prov = eps_provenance.collect(args.model_dir, vensim_exe=args.vensim)
    if args.working_tree:
        prov['working_tree'] = args.working_tree
    print(f"[prov] {prov['source_model']} v{prov['model_version']} "
          f"{prov['base_year']}-{prov['final_year']} "
          f"@ {prov['git_branch']}/{prov['git_commit']} ({prov['working_tree']})")

    notes = list(args.note)
    if missing:
        notes.append(f"variables absent from this model version: {', '.join(missing)}")

    # ---- Demand prior -------------------------------------------------
    prior = to_enduse_prior(raw)
    print(f"[map ] demand: {len(prior):,} rows, {prior['end_use'].nunique()} end-uses")

    # Coverage check against BAU Total
    total = raw[raw['variable'] == 'BAU Total Electricity Demand'].set_index('year')['value']
    coverage_note = 'coverage vs BAU Total Electricity Demand: not checked (variable absent)'
    if not total.empty:
        mapped = prior.groupby('year')['eps_mwh_per_year'].sum()
        coverage = (mapped / total).dropna()
        print(f"[chk ] coverage vs BAU Total: min={coverage.min():.4f} max={coverage.max():.4f}")
        coverage_note = (f'coverage vs BAU Total Electricity Demand: '
                         f'{coverage.min():.4f}-{coverage.max():.4f}')
        if (coverage < 0.99).any() or (coverage > 1.01).any():
            print("[warn] coverage outside [0.99, 1.01] for some years — check mapping")
            coverage_note += '  ** OUTSIDE [0.99, 1.01] — mapping needs review **'

    demand_path = os.path.join(out_dir, f"eps_prior_{iso2}.csv")
    eps_provenance.write_csv_with_provenance(
        demand_path, prior,
        title='EPS prior — BAU electricity demand by sector (MWh/year)',
        region=iso2, fields=prov, notes=notes + [coverage_note],
    )
    print(f"[save] {demand_path}")

    # ---- Capacity prior -----------------------------------------------
    cap = to_capacity_prior(raw)
    if cap.empty:
        print("[warn] no capacity rows found — skipping eps_capacity CSV")
    else:
        print(f"[map ] capacity: {len(cap):,} rows, {cap['tech'].nunique()} technologies")
        cap_path = os.path.join(out_dir, f"eps_capacity_{iso2}.csv")
        eps_provenance.write_csv_with_provenance(
            cap_path, cap,
            title='EPS prior — BAU electricity generation capacity by technology (MW)',
            region=iso2, fields=prov, notes=notes,
        )
        print(f"[save] {cap_path}")

    # ---- Sample year ---------------------------------------------------
    sample_year = int(prior['year'].min()) if not prior.empty else args.initial_year
    if sample_year in set(prior['year']):
        print()
        print(f"=== EPS-{iso2} {sample_year} BAU sectoral electricity demand (MWh/yr) ===")
        s = prior[prior['year'] == sample_year].sort_values('eps_mwh_per_year', ascending=False)
        for _, r in s.iterrows():
            print(f"  {r['end_use']:<26} {r['eps_mwh_per_year']:>20,.0f}")
    if not cap.empty and sample_year in set(cap['year']):
        print()
        print(f"=== EPS-{iso2} {sample_year} BAU generation capacity (MW) ===")
        s = cap[(cap['year'] == sample_year) & (cap['eps_mw'] > 0)].sort_values(
            'eps_mw', ascending=False)
        for _, r in s.iterrows():
            print(f"  {r['tech']:<40} {r['eps_mw']:>16,.0f}")


if __name__ == '__main__':
    main()
