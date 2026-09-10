"""Example consumer: resolve a stable catalog `name` directly into miao's own
VolumeConfig (miao.config.VolumeConfig, miao>=0.4) using lmd_catalog.

CONTRACT: this never sets `exp_factor`. Every zarr in this catalog already
bakes any expansion-microscopy voxel-size correction into its own OME
multiscale coordinateTransformations; miao >=0.3 applies that automatically,
and setting exp_factor on top double-applies it (miao 0.4.0 warns, does not
raise). A name resolved through this catalog must always use miao's default
exp_factor=1.0.

CONTRACT: a volume tracked by more than one annotation item (e.g. the
lm-zebrafish-Betzig-mosaic timelapse corpus, annotated per-timepoint) is
ambiguous by name alone -- resolve() raises unless an issue number is provided.

    python3 examples/resolve_volume_config.py "exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001"
"""

from __future__ import annotations

import json
import sys

import lmd_catalog as lmd


def main():
    if len(sys.argv) < 2:
        print("Usage: resolve_volume_config.py <volume_name> [spatial_axes] [issue_number]")
        sys.exit(1)

    name = sys.argv[1]
    spatial_axes = sys.argv[2] if len(sys.argv) > 2 else "zyx"
    issue = int(sys.argv[3]) if len(sys.argv) > 3 else None

    vol = lmd.get(name)
    config = vol.to_miao(spatial_axes=spatial_axes, issue=issue)
    print(json.dumps(config.model_dump(), indent=2))


if __name__ == "__main__":
    main()

