import lmd_catalog as lmd
from miao.config import MiaoConfig

def build_mouse_config() -> MiaoConfig:
    # 1. Catalog provides typed VolumeConfigs (data on disk)
    mouse_vols = lmd.find(organism="Mouse", has_ground_truth=True)
    volume_configs = [v.to_miao() for v in mouse_vols]

    # 2. Consumer provides the experiment execution configuration
    return MiaoConfig(
        volumes=volume_configs,
        patch_size=[104, 232, 232],
        resolutions=[[25.0, 10.0, 10.0]],
        samples_per_epoch=1000,
        sampling="random",
        output_axes="lzyx",
    )

if __name__ == "__main__":
    miao_cfg = build_mouse_config()
    miao_cfg.to_yaml("mice_with_gt.yaml")

