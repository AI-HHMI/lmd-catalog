"""Validate the lmd catalog against reality: the JSON exported by
export_catalog.sh must be internally consistent AND every path it claims
must exist. Run on a machine with /groups mounted:

    scripts/export_catalog.sh   # on a machine with `cue`, produces volumes.json/annotations.json
    python3 scripts/check_integrity.py volumes.json annotations.json
"""

from __future__ import annotations

import json
import os
import sys

DATA_ROOT = "/groups/miaai/miaai/lmd-v0.0.1/data"

# Annotation status -> the path field that must exist once that status is reached.
TERMINAL_PATH_FIELDS = {
    "GT_Ingested": "gt_ingested_path",
    "Proofread_ingested": "proofread_ingested_path",
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def iter_paths(value):
    """A path field may hold one path, or several joined by ', '. Yield only
    absolute POSIX paths -- skip UNC (\\\\server\\share) paths, which aren't
    checkable from Linux."""
    if value is None:
        return
    for part in value.split(", "):
        part = part.strip()
        if part.startswith("/"):
            yield part


def check_duplicate_names(volumes):
    seen = {}
    violations = []
    for v in volumes:
        if v["name"] in seen:
            violations.append(f"duplicate volume name: {v['name']}")
        seen[v["name"]] = True
    return violations


def check_duplicate_issues(annotations):
    seen = {}
    violations = []
    for a in annotations:
        key = (a["issue"]["repository"], a["issue"]["number"])
        if key in seen:
            violations.append(f"duplicate issue tracked twice: {key[0]}#{key[1]} ({a['title']})")
        seen[key] = True
    return violations


def check_source_paths_resolve(annotations, volumes):
    """Every source_paths entry under DATA_ROOT must equal some volume's path
    exactly -- catches renamed/reorganized volumes an annotation wasn't
    repointed to."""
    volume_paths = {v["path"] for v in volumes}
    violations = []
    for a in annotations:
        for p in a["source_paths"]:
            if p.startswith(DATA_ROOT) and p not in volume_paths:
                violations.append(f"{a['title']}: source_path under DATA_ROOT has no matching volume: {p}")
    return violations


def check_volume_filesystem(volumes):
    violations = []
    for v in volumes:
        path = v["path"]
        if not os.path.exists(path):
            violations.append(f"volume path missing on disk: {path}")
            continue
        marker = ".zgroup" if v["zarr_version"] == "zarr2" else "zarr.json"
        if not os.path.exists(os.path.join(path, marker)):
            violations.append(f"zarr_version {v['zarr_version']} declared but {marker} not found: {path}")
        if not os.path.exists(os.path.join(path, v["image_key"])):
            violations.append(f"image_key '{v['image_key']}' not found under: {path}")
    return violations


def check_annotation_source_paths_exist(annotations):
    """Annotated source data must already exist -- unlike GT/proofread export
    paths, there's no "not yet produced" excuse for source_paths."""
    violations = []
    for a in annotations:
        for p in a["source_paths"]:
            if not os.path.exists(p):
                violations.append(f"{a['title']}: source_path missing on disk: {p}")
    return violations


def check_terminal_paths_exist(annotations):
    violations = []
    for a in annotations:
        field = TERMINAL_PATH_FIELDS.get(a.get("status"))
        if field is None:
            continue
        value = a.get(field)
        if value is None:
            violations.append(f"{a['title']}: status is {a['status']} but {field} is unset")
            continue
        for p in iter_paths(value):
            if not os.path.exists(p):
                violations.append(f"{a['title']}: {field} missing on disk: {p}")
    return violations


def main():
    volumes_path, annotations_path = sys.argv[1], sys.argv[2]
    volumes = load_json(volumes_path)
    annotations = load_json(annotations_path)

    violations = [
        *check_duplicate_names(volumes),
        *check_duplicate_issues(annotations),
        *check_source_paths_resolve(annotations, volumes),
        *check_volume_filesystem(volumes),
        *check_annotation_source_paths_exist(annotations),
        *check_terminal_paths_exist(annotations),
    ]

    for v in violations:
        print(f"FAIL: {v}")
    print(f"\n{len(violations)} violation(s) across {len(volumes)} volumes, {len(annotations)} annotations")
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
