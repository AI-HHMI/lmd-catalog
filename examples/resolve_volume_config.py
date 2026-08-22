"""Example consumer: resolve a stable catalog `name` directly into miao's own
VolumeConfig field names (miao.config.VolumeConfig, miao>=0.4), so any
consumer can do `VolumeConfig(**resolve_volume_config(name, volumes,
annotations))` instead of inventing a bespoke field-name dialect the way
lsd_neuron_segmentation's `_miao_config()` hand-maps its own schemaless YAML
(`segmentation_key` -> `label_key`, etc). See resolve_training_config.py for
that older, one-consumer-specific pattern; this supersedes it for any
consumer willing to target miao's real schema directly.

CONTRACT: this never sets `exp_factor`. Every zarr in this catalog already
bakes any expansion-microscopy voxel-size correction into its own OME
multiscale coordinateTransformations; miao >=0.3 applies that automatically,
and setting exp_factor on top double-applies it (miao 0.4.0 warns, does not
raise). A name resolved through this catalog must always use miao's default
exp_factor=1.0.

CONTRACT: a volume tracked by more than one annotation item (e.g. the
lm-zebrafish-Betzig-mosaic timelapse corpus, annotated per-timepoint) is
ambiguous by name alone -- resolve() raises rather than guessing. This
resolver only serves the common case (0 or 1 tracker per volume).

    scripts/export_catalog.sh
    python3 examples/resolve_volume_config.py "exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001"
"""

from __future__ import annotations

import json
import sys

# miao's VolumeConfig.bounding_box is documented as "output_axes spatial
# order" -- there's no single right answer catalog-wide, so callers whose
# MiaoConfig.output_axes spatial order isn't zyx should pass their own.
DEFAULT_SPATIAL_AXES = "zyx"


def load(path):
    with open(path) as f:
        return json.load(f)


def resolve_volume_config(name, volumes, annotations, spatial_axes=DEFAULT_SPATIAL_AXES):
    assert len(spatial_axes) == 3 and set(spatial_axes) == set("xyz"), (
        f"spatial_axes must be a permutation of 'x','y','z', got {spatial_axes!r}"
    )

    matches = [v for v in volumes if v["name"] == name]
    assert matches, f"unknown volume name: {name}"
    volume = matches[0]

    config = {
        "name": name,
        "path": volume["path"],
        "image_key": volume["image_key"],
        "zarr_version": volume["zarr_version"],
    }

    tracked = [a for a in annotations if volume["path"] in a["source_paths"]]
    assert len(tracked) <= 1, (
        f"{name} is tracked by {len(tracked)} annotation items -- ambiguous which one "
        "to resolve label_key/bounding_box from (known case: multi-round LM timelapse "
        "annotations). Pick one by issue number yourself instead of calling this resolver."
    )
    if not tracked:
        return config
    annotation = tracked[0]

    gt_path = annotation.get("gt_ingested_path")
    if gt_path is not None:
        assert gt_path.startswith(volume["path"] + "/"), f"gt_ingested_path not under volume path: {gt_path}"
        config["label_key"] = gt_path[len(volume["path"]) + 1:]

    roi = annotation.get("roi")
    if roi is not None:
        config["bounding_box"] = [roi[axis] for axis in spatial_axes]

    return config


def main():
    name = sys.argv[1]
    volumes = load("volumes.json")
    annotations = load("annotations.json")
    print(json.dumps(resolve_volume_config(name, volumes, annotations), indent=2))


if __name__ == "__main__":
    main()
