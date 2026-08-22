"""Rebuild lmd_volumes.json from the real /groups/miaai/miaai/lmd-v0.0.1/data
directory tree -- the mechanical source of truth for #Volume identity, so a
volume's entry is never hand-typed (and never goes stale the way
FlyLICONN_FlyID49_40XW005/006's annotation source_paths did).

Run on a machine with /groups mounted:

    python3 scripts/rebuild_volumes.py > lmd_volumes.json
"""

from __future__ import annotations

import json
import os

DATA_ROOT = "/groups/miaai/miaai/lmd-v0.0.1/data"

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


def zarr_version(path):
    if os.path.exists(os.path.join(path, "zarr.json")):
        return "zarr3"
    assert os.path.exists(os.path.join(path, ".zgroup")), f"neither zarr.json nor .zgroup found: {path}"
    return "zarr2"


def build_volume(path):
    assert path.startswith(DATA_ROOT + "/") and path.endswith(".zarr"), path
    name = path[len(DATA_ROOT) + 1 : -len(".zarr")]
    volume = {"name": name}
    version = zarr_version(path)
    if version != "zarr3":
        volume["zarr_version"] = version
    if name in IMAGE_KEY_OVERRIDES:
        volume["image_key"] = IMAGE_KEY_OVERRIDES[name]
    return volume


def main():
    volumes = [build_volume(p) for p in find_zarr_dirs(DATA_ROOT)]
    volumes.sort(key=lambda v: v["name"])
    print(json.dumps({"volumes": volumes}, indent=2))


if __name__ == "__main__":
    main()
