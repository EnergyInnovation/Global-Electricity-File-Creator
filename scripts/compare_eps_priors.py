"""compare_eps_priors.py — Diff freshly extracted EPS priors against a previous snapshot.

Re-extracting a prior silently changes what the ridge-NNLS calibration is
anchored to, so every re-extraction should be reviewed end-use by end-use
before the new numbers are trusted. This prints that review.

  python scripts/compare_eps_priors.py --before <dir of old eps_prior_*.csv>

Also cross-checks the new capacity priors against data/eps_wind_capacity_split.csv,
which reads start-year wind capacity out of the same models by an entirely
different route (the BHRaSYC input CSV rather than a model run). The two should
reconcile at the model's base year; a mismatch means one of them is stale.

Values are for staff review — verify against the models' own documentation
before use in any work product.
"""
from __future__ import annotations

import argparse
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIOR_DIR = os.path.join(ROOT, 'data', 'eps_priors')
WIND_SPLIT_CSV = os.path.join(ROOT, 'data', 'eps_wind_capacity_split.csv')

# EPS Electricity Source subscripts for wind, used for the cross-check.
WIND_TECHS = {'onshore wind es': 'onshore', 'offshore wind es': 'offshore'}


def load_prior(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, comment='#')


def provenance_of(path: str) -> list[str]:
    """Echo the provenance header so the diff report is self-documenting."""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            if not line.startswith('#'):
                break
            out.append(line.rstrip('\n'))
    return out


def diff_demand(iso2: str, before_dir: str) -> None:
    new_path = os.path.join(PRIOR_DIR, f'eps_prior_{iso2}.csv')
    old_path = os.path.join(before_dir, f'eps_prior_{iso2}.csv')
    new = load_prior(new_path)
    old = load_prior(old_path)
    print(f"\n{'=' * 78}\n{iso2} — BAU electricity demand by sector\n{'=' * 78}")
    for line in provenance_of(new_path):
        print(line)
    if new is None:
        print("  NEW PRIOR MISSING")
        return
    if old is None:
        print("  (no previous snapshot to compare against)")
        return

    old_years = set(old['year'])
    new_years = set(new['year'])
    print(f"\n  year span: {min(old_years)}-{max(old_years)}  ->  "
          f"{min(new_years)}-{max(new_years)}")
    dropped = sorted(old_years - new_years)
    added = sorted(new_years - old_years)
    if dropped:
        print(f"  years dropped: {dropped[0]}-{dropped[-1]} ({len(dropped)})")
    if added:
        print(f"  years added:   {added[0]}-{added[-1]} ({len(added)})")

    shared = sorted(old_years & new_years)
    if not shared:
        print("  no overlapping years — comparing at each file's earliest year instead")
        cmp_old, cmp_new = min(old_years), min(new_years)
    else:
        cmp_old = cmp_new = shared[0]
    o = old[old['year'] == cmp_old].set_index('end_use')['eps_mwh_per_year']
    n = new[new['year'] == cmp_new].set_index('end_use')['eps_mwh_per_year']

    print(f"\n  end-use comparison  (old {cmp_old} vs new {cmp_new}, MWh/yr)")
    print(f"    {'end_use':<26} {'old':>18} {'new':>18} {'change':>10}")
    for eu in sorted(set(o.index) | set(n.index)):
        ov = float(o.get(eu, float('nan')))
        nv = float(n.get(eu, float('nan')))
        if pd.isna(ov):
            chg = 'NEW'
        elif pd.isna(nv):
            chg = 'REMOVED'
        elif ov == 0 and nv == 0:
            chg = 'both 0'
        elif ov == 0:
            chg = 'was 0'
        else:
            chg = f'{(nv / ov - 1) * 100:+.1f}%'
        flag = '  <-- ZERO' if nv == 0 else ''
        print(f"    {eu:<26} {ov:>18,.0f} {nv:>18,.0f} {chg:>10}{flag}")

    zeros = sorted(n[n == 0].index)
    if zeros:
        print(f"\n  ** zero-valued end-uses in the new prior: {', '.join(zeros)}")
        print("     align_basis_to_prior scales these basis columns to zero, so the")
        print("     matching SHELF category will export blank. See DECISIONS.md.")


def report_capacity(iso2: str) -> None:
    path = os.path.join(PRIOR_DIR, f'eps_capacity_{iso2}.csv')
    cap = load_prior(path)
    print(f"\n{'-' * 78}\n{iso2} — BAU generation capacity by technology (MW)\n{'-' * 78}")
    if cap is None:
        print("  NO CAPACITY PRIOR WRITTEN")
        return
    base = int(cap['year'].min())
    at_base = cap[(cap['year'] == base) & (cap['eps_mw'] > 0)].sort_values(
        'eps_mw', ascending=False)
    print(f"  {len(cap['tech'].unique())} technologies, years "
          f"{base}-{int(cap['year'].max())}; base-year non-zero:")
    for _, r in at_base.iterrows():
        print(f"    {r['tech']:<44} {r['eps_mw']:>14,.0f}")

    # Cross-check wind against the independently-sourced start-year split.
    if not os.path.exists(WIND_SPLIT_CSV):
        return
    split = pd.read_csv(WIND_SPLIT_CSV)
    row = split[split['iso2'] == iso2]
    if row.empty:
        return
    row = row.iloc[0]
    print(f"\n  wind cross-check vs data/eps_wind_capacity_split.csv "
          f"(source: {row['source_model']})")
    for tech, kind in WIND_TECHS.items():
        model_mw = cap[(cap['tech'] == tech) & (cap['year'] == base)]['eps_mw']
        model_mw = float(model_mw.iloc[0]) if not model_mw.empty else float('nan')
        split_mw = float(row[f'{kind}_mw'])
        if pd.isna(model_mw):
            verdict = 'tech absent from run'
        elif split_mw == 0:
            verdict = 'split file has 0'
        else:
            delta = model_mw / split_mw - 1
            verdict = f'{delta * 100:+.1f}% vs split file'
            if abs(delta) > 0.02:
                verdict += '  ** RECONCILE **'
        print(f"    {kind:<10} run {model_mw:>12,.0f} MW   "
              f"split-file {split_mw:>12,.0f} MW   {verdict}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--before', required=True,
                    help='Directory holding the previous eps_prior_*.csv snapshot.')
    ap.add_argument('--regions', default='US,CN,KR',
                    help='Comma-separated ISO2 list (default US,CN,KR).')
    args = ap.parse_args()

    for iso2 in [r.strip().upper() for r in args.regions.split(',') if r.strip()]:
        diff_demand(iso2, args.before)
        report_capacity(iso2)

    print(f"\n{'=' * 78}")
    print("All values are extracted model output for staff review. Verify against the")
    print("models' own documentation and primary sources before use in a work product.")


if __name__ == '__main__':
    main()
