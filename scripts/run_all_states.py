"""Run state_pipeline for all 48 lower-48 states.

Iterates over preset YAMLs at state_pipeline/presets/US-*.yml. Logs each state's
completion to scripts/data_outputs/all_states_run_log.csv.

Run:
    python scripts/run_all_states.py [--skip-existing] [--states US-VA,US-MO ...]
"""
from __future__ import annotations
import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
PRESETS_DIR = ROOT / "state_pipeline" / "presets"
LOG_PATH = ROOT / "scripts" / "data_outputs" / "all_states_run_log.csv"


def main(skip_existing: bool = False, only: list[str] | None = None):
    presets = sorted(PRESETS_DIR.glob('US-*.yml'))
    if only:
        wanted = set(s.upper() for s in only)
        presets = [p for p in presets if p.stem.upper() in wanted]

    LOG_PATH.parent.mkdir(exist_ok=True, parents=True)
    results = []
    print(f"Running state_pipeline for {len(presets)} states...\n")

    for i, preset in enumerate(presets, 1):
        state = preset.stem  # e.g. US-VA
        t0 = time.time()
        print(f"[{i:>2}/{len(presets)}] {state} ...", end=' ', flush=True)
        try:
            res = subprocess.run(
                [sys.executable, '-m', 'state_pipeline.run', '--state', state],
                cwd=ROOT, capture_output=True, text=True, timeout=600,
            )
            elapsed = time.time() - t0
            ok = res.returncode == 0
            status = "OK" if ok else f"FAIL(code={res.returncode})"
            # Pull NRMSE + days_per_timeslice from stdout if present
            nrmse = ''
            days = ''
            peak_gw = ''
            for line in (res.stdout or '').splitlines():
                if 'NRMSE:' in line and 'cluster' in line.lower():
                    pass
                if 'NRMSE =' in line or 'NRMSE:' in line:
                    parts = line.replace(';', ' ').split()
                    for j, tok in enumerate(parts):
                        if tok.startswith('NRMSE'):
                            try:
                                nrmse = parts[j+1].rstrip(';,')
                                if nrmse.startswith('='):
                                    nrmse = parts[j+2].rstrip(';,')
                            except IndexError:
                                pass
                if 'days_per_timeslice' in line:
                    days = line.split('days_per_timeslice')[-1].strip(': =').rstrip()
                if 'peak:' in line and 'GW' in line:
                    # "state total annual: X TWh; peak: Y GW"
                    try:
                        peak_gw = line.split('peak:')[1].split('GW')[0].strip()
                    except IndexError:
                        pass
            results.append({
                'state': state, 'status': status, 'elapsed_sec': f"{elapsed:.1f}",
                'nrmse': nrmse, 'peak_gw': peak_gw, 'days_per_timeslice': days,
            })
            print(f"{status} ({elapsed:.1f}s, peak={peak_gw} GW)")
            if not ok:
                # surface tail of stderr for diagnosis
                tail = (res.stderr or '').splitlines()[-3:]
                for t in tail:
                    print(f"      | {t}")
        except subprocess.TimeoutExpired:
            elapsed = time.time() - t0
            results.append({
                'state': state, 'status': 'TIMEOUT', 'elapsed_sec': f"{elapsed:.1f}",
                'nrmse': '', 'peak_gw': '', 'days_per_timeslice': '',
            })
            print(f"TIMEOUT ({elapsed:.0f}s)")
        except Exception as e:
            elapsed = time.time() - t0
            results.append({
                'state': state, 'status': f'ERROR({type(e).__name__})',
                'elapsed_sec': f"{elapsed:.1f}", 'nrmse': '', 'peak_gw': '',
                'days_per_timeslice': '',
            })
            print(f"ERROR: {e}")

    # Write log
    with open(LOG_PATH, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['state', 'status', 'elapsed_sec', 'nrmse',
                                          'peak_gw', 'days_per_timeslice'])
        w.writeheader()
        w.writerows(results)
    n_ok = sum(1 for r in results if r['status'] == 'OK')
    print(f"\nDone: {n_ok}/{len(results)} OK. Log: {LOG_PATH}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-existing', action='store_true', help='Skip states with existing _python_pipeline output')
    ap.add_argument('--states', type=str, help='Comma-separated list of state codes (e.g., US-VA,US-MO)')
    args = ap.parse_args()
    only = args.states.split(',') if args.states else None
    main(skip_existing=args.skip_existing, only=only)
