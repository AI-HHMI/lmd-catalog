import lmd_catalog as lmd
from miao.config import MiaoConfig

# 1. Catalog provides typed VolumeConfigs (data on disk)
mouse_vols = lmd.find(organism="Mouse", has_ground_truth=True)
mouse_vol_configs = [v.to_miao() for v in mouse_vols]

fish_vols = lmd.find(organism="Zebrafish", has_ground_truth=True)
fish_vol_configs = [v.to_miao(issue=v.tracked_by[0].issue.number) for v in fish_vols]

# 2. Customize per-volume weights
for i, cfg in enumerate(mouse_vol_configs):
    cfg.weight = 1/len(mouse_vol_configs)
for i, cfg in enumerate(fish_vol_configs):
    cfg.weight = 1/len(fish_vol_configs)

# 3. Combine volume lists
cfg = MiaoConfig(
    volumes=mouse_vol_configs + fish_vol_configs,
    patch_size=[104, 232, 232],
    resolutions=[[25.0, 10.0, 10.0]],
    samples_per_epoch=1000,
    sampling="random",
    output_axes="lzyx",
)

# 3. Serialize to yaml once you've found params you like!
cfg.to_yaml("mouse-fish-combo.yaml") 

for v in fish_vols + mouse_vols:
    print(v.fileglancer_url())
