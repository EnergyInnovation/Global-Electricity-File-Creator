"""Compare Limited vs Reference Access supply curves by cost bin.

The single Limited/Reference ratio (0.45 solar, 0.53 wind, etc.) averages over
the entire supply curve. But actual deployment happens at the CHEAP end —
so the deployment-relevant ratio could be much higher (cheap sites are usually
less land-constrained than marginal high-cost sites).

This script answers: at the cost levels where actual deployment occurs, what
is the Limited/Reference supply ratio? Stats reported for solar (2035) and
land-based wind (2030/2035) using NREL Lopez et al. data.

Run:
    python scripts/analyze_supply_curve_bins.py
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np

DATA = Path(__file__).parent.parent / 'data' / 'nrel_supply_curves'

PAIRS = [
    ('Solar PV (2035)',
     DATA / 'solar_limited_access_2035_moderate_supply_curve.csv',
     DATA / 'solar_reference_access_2035_moderate_supply_curve.csv'),
    ('Onshore Wind (2035)',
     DATA / 'lbw_limited_access_2035_moderate_115hh_170rd_supply_curve.csv',
     None),  # ref 2035 wind not present locally; use 2030 pair
    ('Onshore Wind (2030)',
     DATA / 'limited_access_2030_moderate_115hh_170rd_supply-curve.csv',
     DATA / 'reference_access_2030_moderate_115hh_170rd_supply-curve.csv'),
]

def _load_and_sort(path: Path) -> pd.DataFrame:
    """Detect solar vs wind column conventions and load."""
    df = pd.read_csv(path)
    if 'capacity_ac_mw' in df.columns:
        cap_col, lcoe_col = 'capacity_ac_mw', 'lcoe_site_usd_per_mwh'
    elif 'capacity_mw' in df.columns:
        # Wind convention: prefer total_lcoe (includes transmission) when available
        cap_col = 'capacity_mw'
        lcoe_col = 'total_lcoe' if 'total_lcoe' in df.columns else 'mean_lcoe'
    else:
        raise ValueError(f"Unrecognized supply curve columns in {path.name}")
    df = df[[cap_col, lcoe_col]].rename(columns={cap_col: 'cap_mw', lcoe_col: 'lcoe'})
    df = df.dropna()
    df = df[(df['cap_mw'] > 0) & (df['lcoe'] > 0)]
    df = df.sort_values('lcoe').reset_index(drop=True)
    df['cum_cap_gw'] = df['cap_mw'].cumsum() / 1000.0
    return df


def _cumulative_cap_at_lcoe(df: pd.DataFrame, lcoe_threshold: float) -> float:
    """Total capacity (GW) where LCOE <= threshold."""
    sub = df[df['lcoe'] <= lcoe_threshold]
    if sub.empty:
        return 0.0
    return float(sub['cap_mw'].sum() / 1000.0)


def _lcoe_at_cum_cap(df: pd.DataFrame, cum_cap_gw: float) -> float:
    """LCOE at which Reference supply hits the target cumulative GW."""
    if cum_cap_gw <= 0:
        return df['lcoe'].iloc[0]
    sub = df[df['cum_cap_gw'] >= cum_cap_gw]
    if sub.empty:
        return float(df['lcoe'].max())
    return float(sub['lcoe'].iloc[0])


def analyze_pair(label: str, limited_path: Path, reference_path: Path):
    if not (limited_path.exists() and reference_path and reference_path.exists()):
        return
    print(f"\n{'='*78}")
    print(f"  {label}")
    print(f"{'='*78}")
    print(f"  Limited:   {limited_path.name}")
    print(f"  Reference: {reference_path.name}")

    lim = _load_and_sort(limited_path)
    ref = _load_and_sort(reference_path)

    lim_total = lim['cap_mw'].sum() / 1000.0
    ref_total = ref['cap_mw'].sum() / 1000.0
    print(f"\n  Totals: Limited = {lim_total:,.0f} GW, "
          f"Reference = {ref_total:,.0f} GW, "
          f"Limited/Reference = {lim_total/ref_total:.3f}")

    # 1. Ratio at fixed LCOE thresholds
    print(f"\n  [Method 1] Cumulative supply at fixed LCOE threshold:")
    print(f"  {'LCOE $/MWh':<14}{'Limited GW':>14}{'Reference GW':>14}{'Lim/Ref':>10}")
    print('  ' + '-' * 50)
    for thresh in [25, 30, 35, 40, 45, 50, 60, 75, 100]:
        lim_at = _cumulative_cap_at_lcoe(lim, thresh)
        ref_at = _cumulative_cap_at_lcoe(ref, thresh)
        ratio = lim_at / ref_at if ref_at > 0 else float('nan')
        print(f"  ${thresh:<13}{lim_at:>14,.0f}{ref_at:>14,.0f}{ratio:>10.3f}")

    # 2. Cumulative supply at Reference quantile points
    print(f"\n  [Method 2] Limited supply at the LCOE level where Reference reaches X% of its total:")
    print(f"  {'Ref pct':<10}{'LCOE @':>12}{'Ref GW':>12}{'Lim GW':>12}{'Lim/Ref':>10}")
    print('  ' + '-' * 56)
    for pct in [10, 25, 40, 50, 75]:
        target_cap_gw = ref_total * pct / 100.0
        lcoe_at = _lcoe_at_cum_cap(ref, target_cap_gw)
        ref_at = target_cap_gw  # by construction
        lim_at = _cumulative_cap_at_lcoe(lim, lcoe_at)
        ratio = lim_at / ref_at if ref_at > 0 else float('nan')
        print(f"  {pct}%{'':<7}{lcoe_at:>12.1f}{ref_at:>12,.0f}{lim_at:>12,.0f}{ratio:>10.3f}")

    # 3. Cumulative supply at fixed GW deployment milestones
    print(f"\n  [Method 3] LCOE required to reach a fixed deployment level:")
    print(f"  {'Deploy GW':<12}{'Ref LCOE':>12}{'Lim LCOE':>12}{'Delta $':>10}")
    print('  ' + '-' * 46)
    for milestone in [100, 200, 500, 1000, 2000, 3000]:
        if milestone > ref_total and milestone > lim_total:
            continue
        ref_lcoe = _lcoe_at_cum_cap(ref, milestone) if milestone <= ref_total else float('nan')
        lim_lcoe = _lcoe_at_cum_cap(lim, milestone) if milestone <= lim_total else float('nan')
        delta = lim_lcoe - ref_lcoe if not (np.isnan(ref_lcoe) or np.isnan(lim_lcoe)) else float('nan')
        ref_str = f"${ref_lcoe:.1f}" if not np.isnan(ref_lcoe) else "exceeds"
        lim_str = f"${lim_lcoe:.1f}" if not np.isnan(lim_lcoe) else "exceeds"
        delta_str = f"+${delta:.1f}" if not np.isnan(delta) else "—"
        print(f"  {milestone:,}{'':<5}{ref_str:>12}{lim_str:>12}{delta_str:>10}")


def main():
    for label, lim_path, ref_path in PAIRS:
        if ref_path is None:
            continue
        analyze_pair(label, lim_path, ref_path)


if __name__ == '__main__':
    main()
