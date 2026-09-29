"""Shared DATA_ROOT resolution for scripts/ -- honors LMD_DATA_ROOT (e.g. an
SMB-mounted mirror of /groups) so these scripts work without /groups itself
mounted. Falls back to a repo-root .env file (gitignored) so the override
doesn't have to be exported by hand every session; .env only fills in unset
vars, so an already-exported LMD_DATA_ROOT always wins.
"""

from __future__ import annotations

import os

DEFAULT_DATA_ROOT = "/groups/miaai/miaai/lmd-v0.0.1/data"
_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")

if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))

DATA_ROOT = os.environ.get("LMD_DATA_ROOT", DEFAULT_DATA_ROOT)
