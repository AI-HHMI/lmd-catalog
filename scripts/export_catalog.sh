#!/usr/bin/env bash
# Export volumes/annotations from lmd-catalog to JSON (volumes.json/annotations.json).
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON_BIN="python3"
if [ -f ".venv/bin/python3" ]; then
    PYTHON_BIN=".venv/bin/python3"
fi

export PYTHONPATH="src:${PYTHONPATH:-}"
"$PYTHON_BIN" -c '
import json
import lmd_catalog as lmd

vols = [v.model_dump() for v in lmd.all()]
anns = [a.model_dump() for a in lmd.annotations()]

with open("volumes.json", "w") as f:
    json.dump(vols, f, indent=2)
with open("annotations.json", "w") as f:
    json.dump(anns, f, indent=2)
print(f"wrote volumes.json ({len(vols)} volumes) and annotations.json ({len(anns)} annotations)")
'


