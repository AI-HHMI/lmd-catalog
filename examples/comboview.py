import lmd_catalog as lmd
from miao.config import MiaoConfig

volumes = [x.to_miao() for x in lmd.all() if "flyliconn" in x.name]
cfg = MiaoConfig(
    volumes=volumes,
    patch_size=[104, 232, 232],
    resolutions=[[25.0, 10.0, 10.0]],
    samples_per_epoch=1000,
    sampling="random",
    output_axes="lzyx",
)

vol = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
print(vol.neuroglancer_url())  # automatically normalized to [301, 1130]

# Explicit B&C range and slider window
url = vol.neuroglancer_url(raw_range=(200, 800), raw_window=(0, 1200))

sys.exit(0)

# 1. Overlay a separate segmentation Zarr onto a raw volume:
url = lmd.make_neuroglancer_url(
    raw=vol,
    seg="/groups/miaai/miaai/annotations/my_run/predictions.zarr",
    seg_key="labels/pred_cells",
    seg_name="predictions",
)
print("Separate Zarrs link:\n", url)

# 2. Directly from VolumeEntry (automatically attaches ground truth if present):
print("Raw + Ground Truth link:\n", vol.neuroglancer_url())
