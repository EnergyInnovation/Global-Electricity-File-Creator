"""eps_provenance.py — Capture where an EPS prior came from.

Every prior CSV in this folder is a snapshot of a regional EPS model at one
moment. Without provenance there is no way to tell, from the file alone,
which model copy it came from or how stale it is — which is exactly how the
2026-06-02 snapshot silently drove calibration for two months (see
DECISIONS.md, "EPS priors re-extracted with provenance").

The header is emitted as ``#``-prefixed lines above the CSV header row, so it
is visible the moment anyone opens the file and is skipped by
``pd.read_csv(..., comment='#')``.

Fields are read from the model checkout itself, never passed in by hand:
  version      InputData/version.txt
  base year    InputData/plcy-schd/IT/IT.csv
  final year   InputData/plcy-schd/FT/FT.csv
  git          branch / commit / commit date / remote / dirty count
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
from typing import Dict, List, Optional

# Home directories differ per machine, so an absolute path baked into a
# checked-in CSV is noise at best and a leak at worst. Elide the user segment
# the same way scripts/fetch_eps_wind_capacity_split.py does.
_USER_ROOT_MARKERS = ('users', 'home')


def elide_user(path: str) -> str:
    """Replace the username segment of a path with ``<user>``."""
    norm = os.path.abspath(path).replace('\\', '/')
    parts = norm.split('/')
    for i, part in enumerate(parts):
        if part.lower() in _USER_ROOT_MARKERS and i + 1 < len(parts):
            parts[i + 1] = '<user>'
            break
    return '/'.join(parts)


def _git(model_dir: str, *args: str) -> str:
    """Run a git command in the model checkout; '' if it fails or isn't a repo."""
    try:
        out = subprocess.run(
            ['git', *args],
            cwd=model_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ''
    return out.stdout.strip() if out.returncode == 0 else ''


def _first_line(path: str) -> str:
    try:
        with open(path, encoding='utf-8-sig') as fh:
            return fh.readline().strip()
    except OSError:
        return ''


def _schedule_year(model_dir: str, folder: str, label: str) -> str:
    """Read INITIAL/FINAL TIME out of plcy-schd/<folder>/<folder>.csv.

    These are ``GET DIRECT CONSTANTS`` inputs, not literals in the .mdl — the
    CSV is the only place the value actually lives. Format is two lines:
    ``,Year`` then ``Initial,2025``.
    """
    path = os.path.join(model_dir, 'InputData', 'plcy-schd', folder, f'{folder}.csv')
    try:
        with open(path, encoding='utf-8-sig') as fh:
            for line in fh:
                cells = [c.strip() for c in line.split(',')]
                if len(cells) >= 2 and cells[0].lower() == label.lower():
                    return cells[1]
    except OSError:
        pass
    return ''


def collect(model_dir: str, vensim_exe: Optional[str] = None) -> Dict[str, str]:
    """Gather provenance fields for an EPS model checkout."""
    model_dir = os.path.abspath(model_dir)
    dirty = _git(model_dir, 'status', '--porcelain')
    dirty_count = len([ln for ln in dirty.splitlines() if ln.strip()])

    fields: Dict[str, str] = {
        'source_model': os.path.basename(model_dir),
        'source_model_path': elide_user(model_dir),
        'model_version': _first_line(
            os.path.join(model_dir, 'InputData', 'version.txt')) or 'unknown',
        'base_year': _schedule_year(model_dir, 'IT', 'Initial') or 'unknown',
        'final_year': _schedule_year(model_dir, 'FT', 'Final') or 'unknown',
        'git_branch': _git(model_dir, 'rev-parse', '--abbrev-ref', 'HEAD') or 'unknown',
        'git_commit': _git(model_dir, 'rev-parse', '--short', 'HEAD') or 'unknown',
        'git_commit_date': _git(model_dir, 'log', '-1', '--format=%ad', '--date=short') or 'unknown',
        'git_remote': _git(model_dir, 'config', '--get', 'remote.origin.url') or 'unknown',
        'working_tree': 'clean' if dirty_count == 0 else f'DIRTY — {dirty_count} uncommitted',
        'extracted': dt.date.today().isoformat(),
        'extracted_by': 'data/eps_priors/parse_eps_extract.py',
    }
    if vensim_exe:
        fields['vensim'] = elide_user(vensim_exe)
    return fields


def header_lines(
    title: str,
    region: str,
    fields: Dict[str, str],
    notes: Optional[List[str]] = None,
) -> List[str]:
    """Render provenance as ``#`` comment lines to sit above the CSV header."""
    lines = [f'# {title}', f'# region:            {region}']
    width = max(len(k) for k in fields) + 2
    for key, value in fields.items():
        lines.append(f'# {key + ":":<{width}} {value}')
    for note in notes or []:
        lines.append(f'# note:              {note}')
    return lines


def write_csv_with_provenance(
    path: str,
    df,
    title: str,
    region: str,
    fields: Dict[str, str],
    notes: Optional[List[str]] = None,
) -> None:
    """Write ``df`` to ``path`` beneath a provenance comment block."""
    body = df.to_csv(index=False, lineterminator='\n')
    header = '\n'.join(header_lines(title, region, fields, notes))
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(header + '\n' + body)
