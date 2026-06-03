"""
zipfile_deflate64 — drop-in shim that uses the prebuilt ``inflate64`` wheel.

Mimics the upstream ``zipfile-deflate64`` package's behavior: simply
importing this module patches the standard-library ``zipfile`` so that
``zipfile.ZipFile`` can transparently read Deflate64 (compress_type == 9)
entries — which is what the EFS load-profile archive uses.

Why this shim exists
--------------------
The upstream ``zipfile-deflate64`` package contains a C extension and has
no prebuilt wheel for Python 3.12 on Windows. Building it from source
requires Microsoft Visual C++ Build Tools, which are awkward to install
across a team. The ``inflate64`` package (https://pypi.org/project/inflate64/)
ships prebuilt wheels for all major platforms and provides exactly the
Deflate64 decompressor we need, so this file wires it into ``zipfile``.

Multi-user setup
----------------
This file lives next to ``energy_timeslice_pipeline.py``. When the pipeline
runs ``import zipfile_deflate64``, Python's module search looks in the
script's own directory first, so this shim is picked up automatically for
anyone who clones the repo. The only external requirement is the
``inflate64`` PyPI package — see ``requirements.txt``.

Usage
-----
::

    import zipfile_deflate64  # side-effect: patches zipfile
    import zipfile
    with zipfile.ZipFile('EFSLoadProfile_Reference_Moderate.zip') as z:
        with z.open('EFSLoadProfile_Reference_Moderate.csv') as fh:
            ...  # transparent Deflate64 decompression
"""

from __future__ import annotations

import zipfile

try:
    from inflate64 import Inflater
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The zipfile_deflate64 shim requires the 'inflate64' package. "
        "Install it with: pip install inflate64"
    ) from exc


# Standard zip compress_type value for Deflate64.
ZIP_DEFLATED64 = 9


class _Deflate64Decompressor:
    """
    Adapter wrapping ``inflate64.Inflater`` so it satisfies the small subset
    of the decompressor protocol used by ``zipfile.ZipExtFile._read1`` for
    non-DEFLATE compression types: a ``.decompress(data) -> bytes`` method
    and an ``.eof`` boolean attribute.
    """

    __slots__ = ('_inflater', 'eof')

    def __init__(self) -> None:
        self._inflater = Inflater()
        self.eof = False

    def decompress(self, data: bytes) -> bytes:
        if self.eof:
            return b''
        out = self._inflater.inflate(data if data else b'')
        if getattr(self._inflater, 'eof', False):
            self.eof = True
        return out


# ---------------------------------------------------------------------------
# Patch zipfile so it accepts compress_type=9 and can build a decompressor
# for it. We wrap the originals so all other compression types behave
# exactly as before.
# ---------------------------------------------------------------------------

# Stash the unpatched originals on the zipfile module under a unique name.
# Doing it this way (instead of capturing them into module-level locals)
# keeps the shim idempotent: a reload re-wraps the originals stored on
# zipfile, never the previous wrappers — so we don't recurse infinitely
# if this module is imported more than once.
if not hasattr(zipfile, '_orig_check_compression_d64'):
    zipfile._orig_check_compression_d64 = zipfile._check_compression
if not hasattr(zipfile, '_orig_get_decompressor_d64'):
    zipfile._orig_get_decompressor_d64 = zipfile._get_decompressor


def _patched_check_compression(compression):
    if compression == ZIP_DEFLATED64:
        return
    return zipfile._orig_check_compression_d64(compression)


def _patched_get_decompressor(compress_type):
    if compress_type == ZIP_DEFLATED64:
        return _Deflate64Decompressor()
    return zipfile._orig_get_decompressor_d64(compress_type)


zipfile._check_compression = _patched_check_compression
zipfile._get_decompressor = _patched_get_decompressor

# Friendly name in error messages and listings (zipfile.compressor_names is a
# dict mapping numeric compress_type -> human-readable string).
zipfile.compressor_names.setdefault(ZIP_DEFLATED64, 'deflate64')


__all__ = ['ZIP_DEFLATED64']
