# lmd-catalog

Programmatic catalog, metadata index, and Miao [`VolumeConfig`](file:///Users/broaddusc/proj/miao/src/miao/config.py#L83) resolver for the Large Microscopy Dataset (LMD) corpus at `/groups/miaai/miaai/lmd-v0.0.1/data`.

- **838 OME-Zarr volumes** across 102 datasets discovered directly from cluster storage.
- **27 annotation-tracking issues** synced from GitHub Projects (`AI-HHMI/projects/1`).
- **Direct Miao integration**: `.to_miao()` maps catalog entries directly into typed `VolumeConfig` instances without eager PyTorch imports or CUDA initialization.
- **Fast**: Sub-50ms import latency, pure Pydantic metadata.

## Quickstart

```sh
pip install git+https://github.com/JaneliaSciComp/lmd-catalog.git
```

```python
import lmd_catalog as lmd

# Get volume by name or path
vol = lmd.get("em-UNKNOWN-lucchi-hippocampus/crop-001_train")

# Resolve directly into a miao VolumeConfig for training/inference
cfg = vol.to_miao(spatial_axes="zyx")

# Find volumes with ground truth annotations
annotated = lmd.find(has_ground_truth=True)
for v in annotated:
    print(v.name, v.ground_truth_paths)

# Query all Mouse datasets with ground truth annotations
mouse_gt = lmd.find(organism="Mouse", has_ground_truth=True)
for v in mouse_gt:
    cfg = v.to_miao()
    print(v.dataset, cfg.label_key, cfg.bounding_box)
```

See [`examples/query_mouse_gt_datasets.py`](examples/query_mouse_gt_datasets.py) for a complete CLI script with JSON output and metadata formatting.


---

## Examples

The `examples/` directory contains standalone runnable scripts demonstrating common consumer patterns:

- [`examples/query_mouse_gt_datasets.py`](examples/query_mouse_gt_datasets.py): Query and group mouse volumes with ground truth annotations. Supports human-readable output and `--json`.
- [`examples/mouse_miaoconfigs.py`](examples/mouse_miaoconfigs.py): Construct a `miao.config.MiaoConfig` from catalog query results and export/save as YAML.
- [`examples/resolve_volume_config.py`](examples/resolve_volume_config.py): Resolve a catalog volume name directly into a `miao.config.VolumeConfig`.
- [`examples/resolve_training_config.py`](examples/resolve_training_config.py): Resolve volume metadata into training configuration keys (`train_data_path`, `image_key`, `segmentation_key`).
- [`examples/resolve_roi.py`](examples/resolve_roi.py): Extract and re-order bounding boxes into caller-specified spatial axes (e.g. `zyx`).
- [`examples/combined_viewer_link.py`](examples/combined_viewer_link.py): Generate multi-layer Neuroglancer/Fileglancer viewer links combining separate raw and segmentation Zarr stores.

## Development & Verification

```sh
# Run test suite (<50ms, verifies all 838 volumes resolve to valid VolumeConfigs)
pytest tests/ -v

# Type checking
pyright
mypy src tests examples
```



