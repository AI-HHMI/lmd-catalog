"""Rebuild lmd_volumes.json from the real /groups/miaai/miaai/lmd-v0.0.1/data
directory tree -- the mechanical source of truth for #Volume identity, so a
volume's entry is never hand-typed (and never goes stale the way
FlyLICONN_FlyID49_40XW005/006's annotation source_paths did).

Run on a machine with /groups mounted. This script reads the existing
lmd_volumes.json (to preserve hand-set normalize_min/normalize_max), so don't
redirect stdout directly onto it -- the shell truncates the file before
Python opens it to read, so it always reads back empty. Write to a temp file
and move it into place instead:

    python3 scripts/rebuild_volumes.py > /tmp/lmd_volumes.json.new && mv /tmp/lmd_volumes.json.new lmd_volumes.json
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from data_root import DATA_ROOT

# The one volume with no "raw" wrapper group -- levels are stored directly at
# the store root instead. Not detectable by walking the filesystem alone.
IMAGE_KEY_OVERRIDES = {
    "lm-zebrafish-Betzig-mosaic-example_annotations_Thayer/crop-002_example_annotations_Thayer_2channels": "",
}


def find_zarr_dirs(root):
    """Every .zarr directory under root, without descending into one once found
    -- their chunk trees are enormous and irrelevant here."""
    found = []
    for dirpath, dirnames, _filenames in os.walk(root):
        keep = []
        for d in dirnames:
            if d.endswith(".zarr"):
                found.append(os.path.join(dirpath, d))
            else:
                keep.append(d)
        dirnames[:] = keep
    return found


def find_label_keys(path):
    """Sub-keys under a volume's own labels/ group, if any -- marks volumes
    that ship ingested ground truth directly (e.g. public EM benchmarks),
    not just ones tracked by an annotation issue."""
    labels_dir = os.path.join(path, "labels")
    if not os.path.isdir(labels_dir):
        return []
    return sorted(
        d for d in os.listdir(labels_dir)
        if not d.startswith(".") and os.path.isdir(os.path.join(labels_dir, d))
    )


def zarr_version(path):
    if os.path.exists(os.path.join(path, "zarr.json")):
        return "zarr3"
    assert os.path.exists(os.path.join(path, ".zgroup")), f"neither zarr.json nor .zgroup found: {path}"
    return "zarr2"


def extract_zarr_metadata(path, img_key, z_ver):
    shape, voxelsize, axes = None, None, None
    if z_ver == "zarr3":
        candidate_jsons = [os.path.join(path, "zarr.json")]
        if img_key:
            candidate_jsons.append(os.path.join(path, img_key, "zarr.json"))
        for cj in candidate_jsons:
            if os.path.exists(cj):
                with open(cj) as f:
                    d = json.load(f)
                ms = d.get("attributes", {}).get("ome", {}).get("multiscales") or d.get("attributes", {}).get("multiscales", [])
                if ms:
                    axes = [a["name"] if isinstance(a, dict) else a for a in ms[0].get("axes", [])]
                    for ct in ms[0].get("datasets", [{}])[0].get("coordinateTransformations", []):
                        if ct.get("type") == "scale":
                            voxelsize = ct.get("scale")
                            break
                    break

        s0_candidates = [
            os.path.join(path, img_key, "s0", "zarr.json") if img_key else "",
            os.path.join(path, "s0", "zarr.json"),
        ]
        for sc in s0_candidates:
            if sc and os.path.exists(sc):
                with open(sc) as f:
                    sdata = json.load(f)
                shape = sdata.get("shape")
                break
    else:  # zarr2
        candidate_attrs = [os.path.join(path, ".zattrs")]
        if img_key:
            candidate_attrs.append(os.path.join(path, img_key, ".zattrs"))
        for ca in candidate_attrs:
            if os.path.exists(ca):
                with open(ca) as f:
                    d = json.load(f)
                ms = d.get("multiscales", [])
                if ms:
                    axes = [a["name"] if isinstance(a, dict) else a for a in ms[0].get("axes", [])]
                    for ct in ms[0].get("datasets", [{}])[0].get("coordinateTransformations", []):
                        if ct.get("type") == "scale":
                            voxelsize = ct.get("scale")
                            break
                    break

        s0_candidates = [
            os.path.join(path, img_key, "s0", ".zarray") if img_key else "",
            os.path.join(path, "s0", ".zarray"),
        ]
        for sc in s0_candidates:
            if sc and os.path.exists(sc):
                with open(sc) as f:
                    sdata = json.load(f)
                shape = sdata.get("shape")
                break

    return shape, voxelsize, axes


def build_volume(path, existing_by_name=None):
    assert path.startswith(DATA_ROOT + "/") and path.endswith(".zarr"), path
    name = path[len(DATA_ROOT) + 1 : -len(".zarr")]
    volume = {"name": name}
    version = zarr_version(path)
    if version != "zarr3":
        volume["zarr_version"] = version
    if name in IMAGE_KEY_OVERRIDES:
        volume["image_key"] = IMAGE_KEY_OVERRIDES[name]
    img_key = volume.get("image_key", "raw")

    shape, voxelsize, axes = extract_zarr_metadata(path, img_key, version)
    if shape is not None:
        volume["shape"] = shape
    if voxelsize is not None:
        volume["voxelsize"] = voxelsize
    if axes is not None:
        volume["axes"] = axes

    label_keys = find_label_keys(path)
    if label_keys:
        volume["label_keys"] = label_keys

    # `added` is the store dir's mtime the first time a volume is cataloged (the filesystem exposes no
    # birth time); once recorded it is kept, so later edits to the store don't move it.
    prev = (existing_by_name or {}).get(name, {})
    volume["added"] = prev.get("added") or datetime.fromtimestamp(os.stat(path).st_mtime, timezone.utc).date().isoformat()

    # Preserve normalization windows if already cataloged
    if prev:
        if "normalize_min" in prev:
            volume["normalize_min"] = prev["normalize_min"]
        if "normalize_max" in prev:
            volume["normalize_max"] = prev["normalize_max"]

    return volume


def main():
    existing_by_name = {}
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "lmd_volumes.json")
    if os.path.exists(catalog_path):
        with open(catalog_path) as f:
            text = f.read()
        assert text.strip(), "lmd_volumes.json is empty -- did you redirect output onto it? `git checkout lmd_volumes.json`, then write to a temp file and mv it into place (see the module docstring)"
        existing_by_name = {v["name"]: v for v in json.loads(text).get("volumes", [])}

    volumes = [build_volume(p, existing_by_name) for p in find_zarr_dirs(DATA_ROOT)]
    volumes.sort(key=lambda v: v["name"])
    print(json.dumps({"volumes": volumes}, indent=2))


if __name__ == "__main__":
    main()
