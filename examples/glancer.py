import lmd_catalog as lmd
from rich import print as pprint

vol = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
pprint(vol)

# Automatically normalized to [301, 1130]. Attaches GT if present.
# print(vol.neuroglancer_url())  

# Explicit B&C range and slider window
print(vol.neuroglancer_url(raw_range=(200, 1000), raw_window=(0, 1200)))

# Overlay a separate segmentation Zarr onto a raw volume:
url = lmd.make_neuroglancer_url(
    raw=vol,
    seg="/groups/miaai/miaai/annotations/my_run/predictions.zarr",
    seg_key="labels/pred_cells",
    seg_name="predictions",
)
print("Separate Zarrs link:\n", url)
