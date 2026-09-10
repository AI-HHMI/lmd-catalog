"""Example consumer: resolve a stable catalog `name` to the fields a training
config needs (data path, image key, GT segmentation key) instead of hardcoding
them. This is the pattern that would have avoided lsd_neuron_segmentation's
repeated repoint churn (see jj history: d55dd60639d3, 948cdcbfe966,
800b186d1851) -- a consumer that looks up by `name` only needs its pinned
catalog version bumped, not a grep-and-replace across its own config files.

    python3 examples/resolve_training_config.py "exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001"
"""

from __future__ import annotations

import json
import sys

import lmd_catalog as lmd


def resolve(name: str) -> dict:
    vol = lmd.get(name)
    assert len(vol.tracked_by) == 1, (
        f"expected exactly one tracking annotation for {name}, got {len(vol.tracked_by)}"
    )
    annotation = vol.tracked_by[0]

    gt_path = annotation.gt_ingested_path
    assert gt_path is not None, f"{name} (status={annotation.status}) has no gt_ingested_path yet"
    assert gt_path.startswith(vol.path + "/"), f"gt_ingested_path not under volume path: {gt_path}"
    segmentation_key = gt_path[len(vol.path) + 1 :]

    return {
        "train_data_path": vol.path,
        "image_key": vol.image_key,
        "segmentation_key": segmentation_key,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: resolve_training_config.py <volume_name>")
        sys.exit(1)

    name = sys.argv[1]
    print(json.dumps(resolve(name), indent=2))


if __name__ == "__main__":
    main()

