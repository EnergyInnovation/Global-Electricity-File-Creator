"""Where the build looks for its inputs. No user folder is written into the code.

Each location is resolved in this order:
  1. the command-line option, if given
  2. an environment variable, SHELF_<KEY> in capitals (for example SHELF_RESSTOCK_ROOT)
  3. a line `key: path` in local_paths.yml at the repository root (not committed; see local_paths.example.yml)
  4. the default below, which is inside or beside the repository
"""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DEFAULTS = {
    # raw downloads (large; none are in the repository)
    'resstock_root': ROOT.parent / 'ResStock SHELF' / 'ResStock_Upgrade0',
    'comstock_root': ROOT.parent / 'ResStock SHELF' / 'ComStock_tmy_release1',
    'efs_zip': ROOT / 'data' / 'efs' / 'EFSLoadProfile_Reference_Moderate.zip',
    'siels_zip': ROOT / 'data' / 'siels' / 'industrial_load_shapes_2018.zip',
    # inside the repository
    'handbuilt_seed': ROOT / 'data' / 'us_industry_handbuilt' / 'handbuilt_tabs.xlsx',
    'cache_dir': ROOT / 'data' / 'national_aggregated',
    'cambium_hourly': ROOT / 'data' / 'cambium24_midcase_national' / 'Cambium24_MidCase_hourly_usa_2025.csv',
    'clustering_list': ROOT / 'data' / 'cambium24_midcase_national' / 'k6_slice_assignment_repday.csv',
}


def _local_file() -> dict[str, str]:
    p = ROOT / 'local_paths.yml'
    out: dict[str, str] = {}
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            line = line.split('#', 1)[0].strip()
            if ':' in line:
                k, v = line.split(':', 1)
                if v.strip():
                    out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def lookup(key: str, cli_value: str | None = None) -> Path:
    """Resolve one input location (see the module docstring for the order)."""
    if cli_value:
        return Path(cli_value).expanduser()
    env = os.environ.get('SHELF_' + key.upper())
    if env:
        return Path(env).expanduser()
    local = _local_file().get(key)
    if local:
        return Path(local).expanduser()
    return DEFAULTS[key]
