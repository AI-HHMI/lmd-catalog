import lmd_catalog as lmd
from miao.config import MiaoConfig

# 1. Catalog provides typed VolumeConfigs (data on disk)
mouse_vols = lmd.find(organism="Mouse", has_ground_truth=True)
volume_configs = [v.to_miao() for v in mouse_vols]

# 2. Consumer provides the experiment execution configuration
miao_cfg = MiaoConfig(
    volumes=volume_configs,
    patch_size=[104, 232, 232],
    resolutions=[[25.0, 10.0, 10.0]],
    samples_per_epoch=1000,
    sampling="random",
    output_axes="lzyx",
)
print(miao_cfg)
