import lmd_catalog as lmd

for x in lmd.all():
    print(x.name)
import sys
sys.exit(0)

vol = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")

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
