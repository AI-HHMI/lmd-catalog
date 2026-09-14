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

# The Design Problem

OK, let's forget about CUE for a second. What are standard practices and tools
around data versioning for systems like ours. We have a few hundred large zarr
volumes and continually update them with medium sized but highly compressible
label annotations over time and frequently update the lightweight metadata like
voxel size, etc. Occasionally we may want to migrate the data e.g. zarr2 ->
zarr3 or create and store downsampled versions of raw images and labels. We need
to reference this data from many different projects for training neural nets and
making predictions, but those predictions are changing frequently as we iterate
on models.


List of things we want:

0. No change for zarr writers.
1. Consumers don't have data move out from under them.
2. Compatible with Fileglancer / Neuroglancer
3. We can add new zarrs, new keys/labels and new metadata.
4. We can specify subvolumes of zarrs specifically used for train/test.
5. We can fix and update metadata.
6. Auto verification that new versions don't break consumers except on major version bumps.
7. Auto verification that paths are valid and complete records of underlying data.


Systems:

- versioned json metadata
- miao configs next to data


# key classes

some keys live next to

---

Don't rely on claude to update data. Use python to update data/make lists.
Use claude to write scripts that generate data!

Claude writes .py and .cue
.py generates .json
.cue verifies it
but why .cue? why not specify schema in .py and verify with .py?


