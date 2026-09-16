"""Example consumer: resolve a stable catalog `name` to the fields a training
config needs (data path, image key, GT segmentation key) instead of hardcoding
them.
"""

import lmd_catalog as lmd
from rich import print as pprint

vol = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
assert len(vol.tracked_by) == 1
gt_path = vol.tracked_by[0].gt_ingested_path
assert gt_path and gt_path.startswith(vol.path + "/")

pprint({
    "train_data_path": vol.path,
    "image_key": vol.image_key,
    "segmentation_key": gt_path[len(vol.path) + 1 :],
})
