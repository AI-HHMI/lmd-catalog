import lmd_catalog as lmd

vol = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")

# 1. Combine catalog raw volume with an external/separate segmentation Zarr
custom_url = lmd.make_neuroglancer_url(
    raw=vol,
    seg="/groups/miaai/miaai/annotations/my_run/predictions.zarr",
    seg_key="labels/pred_cells",
    seg_name="predictions",
)
print("Combined viewer link (separate Zarrs):\n", custom_url)

# 2. Overlay ground truth directly from a VolumeEntry
if vol.has_ground_truth:
    print("\nVolume + Ground Truth link:\n", vol.neuroglancer_url())
