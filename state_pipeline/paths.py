"""Path resolution helpers.

Source data paths in presets may be:
  - absolute
  - relative to current working directory
  - relative to the parent of cwd (the Models/ folder, where
    state-eps-data-repository and "ResStock SHELF" live)

resolve_input() tries each in turn.
resolve_output() resolves against cwd; creates parent dirs.
"""
from __future__ import annotations
from pathlib import Path
from typing import Iterable


CWD = Path.cwd()
SEARCH_ROOTS: tuple[Path, ...] = (CWD, CWD.parent)


def resolve_input(path_like: str, *, must_exist: bool = True) -> Path:
    """Resolve an input path searching across roots."""
    p = Path(path_like)
    if p.is_absolute():
        if must_exist and not p.exists():
            raise FileNotFoundError(p)
        return p
    candidates: list[Path] = [(root / p) for root in SEARCH_ROOTS]
    for c in candidates:
        if c.exists():
            return c
    if must_exist:
        raise FileNotFoundError(
            f"Could not resolve input path '{path_like}' under: " +
            ", ".join(str(r) for r in SEARCH_ROOTS)
        )
    return candidates[0]


def resolve_output(path_like: str) -> Path:
    """Resolve an output path. Symmetric with resolve_input: prefer the parent
    of cwd if its first path segment already exists there (typical when writing
    to state-eps-data-repository/ which lives one level up from the project).
    Falls back to cwd-relative otherwise. Creates parent dirs.
    """
    p = Path(path_like)
    if p.is_absolute():
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    # Prefer parent if first segment exists there as a directory
    first = p.parts[0] if p.parts else ''
    parent_anchor = CWD.parent / first
    if first and parent_anchor.is_dir():
        out = CWD.parent / p
    else:
        out = CWD / p
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def search_roots() -> Iterable[Path]:
    return SEARCH_ROOTS
