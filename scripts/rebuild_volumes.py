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

DATA_ROOT = os.environ.get("LMD_DATA_ROOT", "/groups/miaai/miaai/lmd-v0.0.1/data")

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

    # Preserve normalization windows if already cataloged
    if existing_by_name and name in existing_by_name:
        prev = existing_by_name[name]
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
            existing_by_name = {v["name"]: v for v in json.load(f).get("volumes", [])}

    volumes = [build_volume(p, existing_by_name) for p in find_zarr_dirs(DATA_ROOT)]
    volumes.sort(key=lambda v: v["name"])
    print(json.dumps({"volumes": volumes}, indent=2))


if __name__ == "__main__":
    main()
