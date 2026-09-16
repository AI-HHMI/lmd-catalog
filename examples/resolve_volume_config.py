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
ambiguous by name alone -- to_miao() raises unless an issue number is provided.
"""

import lmd_catalog as lmd
from rich import print as pprint

vol = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
config = vol.to_miao()
pprint(config)

