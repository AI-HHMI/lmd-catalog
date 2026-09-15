import lmd_catalog as lmd

vol = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")

# Set seg and seg_key to your prediction store and array/group key.
# None displays the catalog's ground truth.
url = vol.neuroglancer_url(
    seg="/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-cortex-20250822_ExPID09_2ndGel_30percentSucrose-Glycerol_40XW_003/crop-001.zarr",
    seg_key="labels/manual_gt-cell-final",
    seg_name="predictions",
    raw_range=(200, 1000),
    raw_window=(0, 1200),
)

print(url)
