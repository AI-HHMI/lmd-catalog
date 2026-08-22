#!/usr/bin/env bash
# Export volumes/annotations from the CUE catalog to JSON, for the pure-Python
# checkers in this directory to consume on a machine that has /groups mounted
# but not necessarily `cue` (e.g. a Janelia cluster node).
set -euo pipefail
cd "$(dirname "$0")/.."

CATALOG_FILES="lmd_volumes.cue lmd_annotations.cue lmd_volumes.json lmd_annotations.json"
cue export $CATALOG_FILES -e volumes > volumes.json
cue export $CATALOG_FILES -e annotations > annotations.json
echo "wrote volumes.json annotations.json"
