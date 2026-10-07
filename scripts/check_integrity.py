"""Validate the lmd catalog against reality: internal consistency AND every
path it claims must exist. Run on a machine with /groups mounted:

    python3 scripts/check_integrity.py
    # or with exported JSON:
    python3 scripts/check_integrity.py volumes.json annotations.json   # skips the pretraining join check
"""

from __future__ import annotations

import json
import os
import re
import sys

from data_root import DATA_ROOT, DEFAULT_DATA_ROOT
from roi_parse import parse_roi

# Annotation status -> the path field that must exist once that status is reached.
TERMINAL_PATH_FIELDS = {
    "GT_Ingested": "gt_ingested_path",
    "Proofread_ingested": "proofread_ingested_path",
}


def rebase(p):
    """Annotation paths are stored under the canonical DEFAULT_DATA_ROOT; map them
    onto DATA_ROOT so the checks also work against a remapped mount."""
    if p.startswith(DEFAULT_DATA_ROOT + "/"):
        return DATA_ROOT + p[len(DEFAULT_DATA_ROOT):]
    return p


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


# mia_pretraining statuses whose path legitimately matches no catalog volume (not ingested yet / synthetic dev data).
PRETRAINING_NO_VOLUME_STATUSES = {"Pending Ingestion", "Model Development Only"}


# mia_pretraining records that are wrong in the GitHub Project and can't be corrected there: (repository, issue
# number) -> what is wrong. Their violations are ignored, but an entry that stops failing is itself a violation, so
# remove it once the project is fixed.
KNOWN_PROJECT_ERRORS = {
    ("AI-HHMI/mia_pretraining", 13): "hhmi_path is a range ('... 027 … 045 (12 dirs)'), not paths",
    ("AI-HHMI/mia_pretraining", 14): "hhmi_path uses the legacy betzig-fish-mosaic/ layout, which no longer exists on disk",
    ("AI-HHMI/mia_pretraining", 15): "hhmi_path uses the legacy betzig-fish-mosaic/ layout, which no longer exists on disk",
    ("AI-HHMI/mia_pretraining", 16): "hhmi_path uses the legacy betzig-fish-mosaic/ layout, which no longer exists on disk",
    ("AI-HHMI/mia_pretraining", 38): "voxel_size_zyx_nm 400×162.5×162.5 looks copied from the spinning-disk datasets; the stores are 1000×157×157",
    ("AI-HHMI/mia_pretraining", 303): "hhmi_path lists bare crop names after its first full path",
}


def record_key(p):
    return (p["issue"]["repository"], p["issue"]["number"])


def unjoined_problems(unjoined_pretraining):
    """(record key, message) for each mia_pretraining record that names a path but matches no catalog volume or
    dataset directory -- a typo, a layout the join doesn't understand, or a store that isn't in the catalog."""
    return [
        (record_key(p), f"{p['title']} ({p['issue']['repository']}#{p['issue']['number']}): hhmi_path matches no catalog volume or dataset: {p['hhmi_path']}")
        for p in unjoined_pretraining
        if p["status"] not in PRETRAINING_NO_VOLUME_STATUSES
    ]


def check_pretraining_joined(unjoined_pretraining):
    return [m for _, m in unjoined_problems(unjoined_pretraining)]


NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def numbers3(text):
    """The three numbers of a free-text 'A×B×C' field, else None (blank, prose, or a different count)."""
    nums = [float(x) for x in NUMBER_RE.findall(text or "")]
    return nums if len(nums) == 3 else None


def close(a, b, tol):
    return abs(a - b) <= tol * max(abs(a), abs(b))


def mismatch_problems(volumes):
    """For a store a mia_pretraining record names exactly, the record's shape and voxel size must agree with
    the store's own zarr metadata (the catalog's shape/voxelsize, ZYX). Two conventions are allowed: a project
    shape that is larger on every axis (it describes the crop's parent dataset), and a voxel size equal to the
    store's divided by the record's expansion factor (the pre-expansion size). Fields that are blank or aren't
    three numbers are skipped. Returns (record key, message) pairs."""
    problems = []
    for v in volumes:
        if not (v.get("shape") and v.get("axes") and v.get("voxelsize")):
            continue
        shape, vox = dict(zip(v["axes"], v["shape"])), dict(zip(v["axes"], v["voxelsize"]))
        if any(a not in shape for a in "zyx"):
            continue
        store_shape, store_vox = [float(shape[a]) for a in "zyx"], [float(vox[a]) for a in "zyx"]
        for p in v.get("pretraining", []):
            ref = f"{p['issue']['repository']}#{p['issue']['number']}"
            project_shape = numbers3(p.get("volume_shape_zyx"))
            if project_shape:
                b1 = project_shape == store_shape
                b2 = all(a >= b for a, b in zip(project_shape, store_shape))
                if not (b1 or b2):
                    problems.append((record_key(p), f"{v['name']}: {ref} says shape {p['volume_shape_zyx']} but the store is {store_shape} (ZYX)"))
            project_vox = numbers3(p.get("voxel_size_zyx_nm"))
            if project_vox:
                m = NUMBER_RE.search(p.get("expansion_factor") or "")
                factor = float(m.group()) if m else 0.0
                b1 = all(close(a, b, 0.01) for a, b in zip(project_vox, store_vox))
                b2 = factor > 0 and all(close(a * factor, b, 0.03) for a, b in zip(project_vox, store_vox))
                if not (b1 or b2):
                    problems.append((record_key(p), f"{v['name']}: {ref} says voxel size {p['voxel_size_zyx_nm']} nm (expansion {p.get('expansion_factor')}) but the store is {store_vox} (ZYX)"))
    return problems


def check_pretraining_matches_stores(volumes):
    return [m for _, m in mismatch_problems(volumes)]


def check_pretraining_known_errors(unjoined_pretraining, volumes):
    """The join and store-agreement checks with KNOWN_PROJECT_ERRORS ignored -- and a violation for every
    known error that no longer fails, so the list can't go stale."""
    problems = unjoined_problems(unjoined_pretraining) + mismatch_problems(volumes)
    fired = {key for key, _ in problems}
    violations = [m for key, m in problems if key not in KNOWN_PROJECT_ERRORS]
    violations += [
        f"KNOWN_PROJECT_ERRORS entry {key[0]}#{key[1]} ({why}) no longer fails any check -- remove it"
        for key, why in KNOWN_PROJECT_ERRORS.items()
        if key not in fired
    ]
    return violations


ZARR2_KINDS = {"i": "int", "u": "uint", "f": "float"}


def store_dtype(volume):
    """The dtype name ('uint8', 'float32', ...) of a store's s0 array, read from its zarr3 `zarr.json` or zarr2
    `.zarray`; None if the metadata isn't there or isn't a plain int/uint/float."""
    for base in (os.path.join(volume["path"], volume["image_key"], "s0"), os.path.join(volume["path"], "s0")):
        v3, v2 = os.path.join(base, "zarr.json"), os.path.join(base, ".zarray")
        if os.path.exists(v3):
            dtype = load_json(v3).get("data_type")
            return dtype if isinstance(dtype, str) else None
        if os.path.exists(v2):
            m = re.match(r"^[<>|=]?([iuf])(\d+)$", load_json(v2)["dtype"])
            return f"{ZARR2_KINDS[m.group(1)]}{int(m.group(2)) * 8}" if m else None
    return None


def check_pretraining_dtype(volumes):
    """For a store a mia_pretraining record names exactly, the record's `dtype` must match the store's s0 array.
    Reads zarr metadata, so it needs the data mounted."""
    violations = []
    for v in volumes:
        records = [p for p in v.get("pretraining", []) if p.get("dtype")]
        actual = store_dtype(v) if records else None
        for p in records if actual else []:
            if p["dtype"] != actual:
                violations.append(f"{v['name']}: {p['issue']['repository']}#{p['issue']['number']} says dtype {p['dtype']} but the store's s0 is {actual}")
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
    exactly, or be a dataset directory containing volumes (dataset-level
    issues) -- catches renamed/reorganized volumes an annotation wasn't
    repointed to."""
    volume_paths = {v["path"] for v in volumes}
    violations = []
    for a in annotations:
        for p in map(rebase, a["source_paths"]):
            if p.startswith(DATA_ROOT) and p not in volume_paths and not any(vp.startswith(p + "/") for vp in volume_paths):
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
        for key in v.get("label_keys", []):
            if not os.path.exists(os.path.join(path, "labels", key)):
                violations.append(f"label_keys entry 'labels/{key}' not found under: {path}")
    return violations


def check_annotation_source_paths_exist(annotations):
    """Annotated source data must already exist -- unlike GT/proofread export
    paths, there's no "not yet produced" excuse for source_paths."""
    violations = []
    for a in annotations:
        for p in map(rebase, a["source_paths"]):
            if not os.path.exists(p):
                violations.append(f"{a['title']}: source_path missing on disk: {p}")
    return violations


def check_roi_matches_bbox_text(annotations):
    """roi is derived from the free-text bbox/bbox_size fields by hand -- make
    sure a future edit to one can't silently drift from the other."""
    violations = []
    for a in annotations:
        roi = a.get("roi")
        if roi is None:
            continue
        if not (a.get("bbox") or a.get("bbox_size")):
            violations.append(f"{a['title']}: roi {roi} is set but bbox/bbox_size text is empty (rebuild_annotations.py would drop it)")
            continue
        expected = parse_roi(a.get("bbox"), a.get("bbox_size"))
        if expected != roi:
            violations.append(f"{a['title']}: roi {roi} doesn't match bbox/bbox_size text (expected {expected})")
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
        for p in map(rebase, iter_paths(value)):
            if not os.path.exists(p):
                violations.append(f"{a['title']}: {field} missing on disk: {p}")
    return violations


def main():
    if len(sys.argv) >= 3:
        volumes = load_json(sys.argv[1])["volumes"]
        annotations = load_json(sys.argv[2])["annotations"]
        pretraining_checks = []  # the pretraining join needs the package; use the default (no-argument) mode to check it
    else:
        try:
            import lmd_catalog as lmd
        except ImportError:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
            import lmd_catalog as lmd
        volumes = [v.model_dump() for v in lmd.all()]
        annotations = [a.model_dump() for a in lmd.annotations()]
        unjoined_pretraining = [p.model_dump() for p in lmd.default_catalog().unjoined_pretraining()]
        pretraining_checks = [*check_pretraining_known_errors(unjoined_pretraining, volumes), *check_pretraining_dtype(volumes)]


    violations = [
        *check_duplicate_names(volumes),
        *check_duplicate_issues(annotations),
        *check_source_paths_resolve(annotations, volumes),
        *check_volume_filesystem(volumes),
        *check_annotation_source_paths_exist(annotations),
        *pretraining_checks,
        *check_roi_matches_bbox_text(annotations),
        *check_terminal_paths_exist(annotations),
    ]

    for v in violations:
        print(f"FAIL: {v}")
    print(f"\n{len(violations)} violation(s) across {len(volumes)} volumes, {len(annotations)} annotations")
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
