"""Example consumer: resolve a stable catalog `name` to the fields a training
config needs (data path, image key, GT segmentation key) instead of hardcoding
them. This is the pattern that would have avoided lsd_neuron_segmentation's
repeated repoint churn (see jj history: d55dd60639d3, 948cdcbfe966,
800b186d1851) -- a consumer that looks up by `name` only needs its pinned
catalog version bumped, not a grep-and-replace across its own config files.

    scripts/export_catalog.sh
    python3 examples/resolve_training_config.py "exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001"
"""

from __future__ import annotations

import json
import sys


def load(path):
    with open(path) as f:
        return json.load(f)


def resolve(name, volumes, annotations):
    matches = [v for v in volumes if v["name"] == name]
    assert matches, f"unknown volume name: {name}"
    volume = matches[0]

    tracked = [a for a in annotations if volume["path"] in a["source_paths"]]
    assert len(tracked) == 1, f"expected exactly one tracking annotation for {name}, got {len(tracked)}"
    annotation = tracked[0]

    gt_path = annotation.get("gt_ingested_path")
    assert gt_path is not None, f"{name} (status={annotation['status']}) has no gt_ingested_path yet"
    assert gt_path.startswith(volume["path"] + "/"), f"gt_ingested_path not under volume path: {gt_path}"
    segmentation_key = gt_path[len(volume["path"]) + 1:]

    return {
        "train_data_path": volume["path"],
        "image_key": volume["image_key"],
        "segmentation_key": segmentation_key,
    }


def main():
    name = sys.argv[1]
    volumes = load("volumes.json")
    annotations = load("annotations.json")
    print(json.dumps(resolve(name, volumes, annotations), indent=2))


if __name__ == "__main__":
    main()
