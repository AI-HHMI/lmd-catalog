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
