#!/usr/bin/env bash
# Export volumes/annotations from the CUE catalog to JSON, for the pure-Python
# checkers in this directory to consume on a machine that has /groups mounted
# but not necessarily `cue` (e.g. a Janelia cluster node).
set -euo pipefail
cd "$(dirname "$0")/.."

cue export . -e volumes > volumes.json
cue export . -e annotations > annotations.json
echo "wrote volumes.json annotations.json"
