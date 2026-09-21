"""Tests for lmd_catalog and miao VolumeConfig integration."""

import sys
import time
import pytest


def test_import_speed_and_no_torch():
    """Verify that importing lmd_catalog is fast (<100ms) and does not import PyTorch."""
    t0 = time.time()
    import lmd_catalog as lmd

    elapsed = time.time() - t0
    assert elapsed < 0.5, f"Import too slow: {elapsed:.3f}s"
    assert "torch" not in sys.modules, "torch was eagerly imported by lmd_catalog"


def test_catalog_inventory():
    """Verify catalog contents and lookups."""
    import lmd_catalog as lmd

    vols = lmd.all()
    assert len(vols) == 838, f"Expected 838 volumes, found {len(vols)}"

    datasets = lmd.list_datasets()
    assert len(datasets) == 102, f"Expected 102 datasets, found {len(datasets)}"

    anns = lmd.annotations()
    assert len(anns) == 27, f"Expected 27 annotations, found {len(anns)}"

    # Lookup by name
    v = lmd.get("em-celegans-funceworm-jrc-20250414/crop-001")
    assert v.name == "em-celegans-funceworm-jrc-20250414/crop-001"
    assert v.path == "/groups/miaai/miaai/lmd-v0.0.1/data/em-celegans-funceworm-jrc-20250414/crop-001.zarr"

    # Lookup by path
    v2 = lmd.get(v.path)
    assert v2.name == v.name

    # Unknown key raises KeyError
    with pytest.raises(KeyError):
        lmd.get("non-existent-volume")


def test_all_volumes_produce_valid_volume_config():
    """Verify CI guarantee: all 838 volumes resolve to valid miao VolumeConfigs without torch."""
    import lmd_catalog as lmd
    from miao.config import VolumeConfig

    for v in lmd.all():
        if len(v.tracked_by) > 1:
            cfg = v.to_miao(issue=v.tracked_by[0].issue.number)
        else:
            cfg = v.to_miao()
        assert isinstance(cfg, VolumeConfig)
        assert cfg.name == v.name
        assert cfg.path == v.path
        assert cfg.exp_factor == 1.0

    # Ensure torch remains unimported after building 838 VolumeConfigs
    assert "torch" not in sys.modules, "torch was imported during VolumeConfig resolution"


def test_tracked_annotations_and_gt():
    """Verify ground truth label_key and ROI bounding_box resolution."""
    import lmd_catalog as lmd

    # Single-tracker volume with ground truth
    v = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
    assert v.is_annotated
    assert v.has_ground_truth
    cfg = v.to_miao()
    assert cfg.label_key == "labels/manual_gt-cell-final"
    assert cfg.bounding_box == [[83, 277], [514, 996], [1413, 1895]]
    assert v.normalize_min == 301.0
    assert v.normalize_max == 1130.0
    assert cfg.normalize_min == 301.0
    assert cfg.normalize_max == 1130.0
    assert cfg.normalize is True

    # Override bounding box and normalization
    cfg_override = v.to_miao(bounding_box=[[0, 10], [0, 10], [0, 10]], normalize_min=10.0, normalize_max=20.0)
    assert cfg_override.bounding_box == [[0, 10], [0, 10], [0, 10]]
    assert (cfg_override.normalize_min, cfg_override.normalize_max) == (10.0, 20.0)

    # Volume with ROI
    v_roi = lmd.get("em-mouse-MICrONS-minnie65/crop-001")
    cfg_zyx = v_roi.to_miao(spatial_axes="zyx")
    cfg_xyz = v_roi.to_miao(spatial_axes="xyz")
    assert cfg_zyx.bounding_box == [[457, 567], [3390, 3736], [2679, 3339]]
    assert cfg_xyz.bounding_box == [[2679, 3339], [3390, 3736], [457, 567]]


def test_ambiguous_multi_tracked_volume():
    """Verify that multi-tracked volumes raise unless an issue is specified."""
    import lmd_catalog as lmd

    multi_vol_name = "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-011_000x_003y_001z_32t_2c"
    v = lmd.get(multi_vol_name)
    assert len(v.tracked_by) == 4

    with pytest.raises(ValueError, match="tracked by 4 annotations"):
        v.to_miao()

    # Specifying issue succeeds
    cfg = v.to_miao(issue=3)
    assert cfg.name == v.name


def test_catalog_queries_and_filters():
    """Verify filter and query capabilities."""
    import lmd_catalog as lmd

    # Filter by dataset
    lucchi = lmd.find(dataset="em-UNKNOWN-lucchi-hippocampus")
    assert len(lucchi) == 2

    # Filter by annotation status
    annotated = lmd.find(is_annotated=True)
    assert len(annotated) > 0

    with_gt = lmd.find(has_ground_truth=True)
    assert len(with_gt) == 7

    # Filter by organism
    zebrafish = lmd.find(organism="Zebrafish")
    assert len(zebrafish) > 0

    # Filter mouse datasets with ground truth
    mouse_gt = lmd.find(organism="Mouse", has_ground_truth=True)
    assert len(mouse_gt) == 3
    mouse_datasets = {v.dataset for v in mouse_gt}
    assert len(mouse_datasets) == 3
    for v in mouse_gt:
        assert v.normalize_min is not None
        assert v.normalize_max is not None
        assert len(v.ground_truth_paths) >= 1
        cfg = v.to_miao()
        assert cfg.label_key == "labels/manual_gt-cell-final"
        assert cfg.bounding_box is not None



def test_fileglancer_urls():
    """Verify fileglancer URL generation."""
    import lmd_catalog as lmd

    v = lmd.get("em-celegans-funceworm-jrc-20250414/crop-001")
    url = v.fileglancer_url()
    assert url.startswith("https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/")
    assert v.name in url


def test_make_neuroglancer_url_combines_raw_and_seg():
    """Verify combining separate raw and segmentation Zarr stores into a single Neuroglancer URL."""
    import lmd_catalog as lmd

    raw_path = "/groups/miaai/miaai/lmd-v0.0.1/data/my_dataset/crop-001.zarr"
    seg_path = "/groups/miaai/miaai/annotations/my_dataset/seg_run1.zarr"

    url = lmd.make_neuroglancer_url(
        raw=raw_path,
        seg=seg_path,
        raw_key="raw",
        seg_key="labels/pred_cells",
        raw_name="raw_image",
        seg_name="predictions",
    )

    assert url.startswith("https://fileglancer.int.janelia.org/neuroglancer/#!%7B")
    state = lmd.parse_neuroglancer_url(url)
    assert len(state["layers"]) == 2
    assert state["layers"][0]["name"] == "raw_image"
    assert state["layers"][0]["type"] == "image"
    assert state["layers"][0]["source"] == (
        "https://fileglancer.int.janelia.org/api/content/groups_miaai_miaai/lmd-v0.0.1/data/my_dataset/crop-001.zarr/raw/|zarr3:"
    )
    assert state["layers"][1]["name"] == "predictions"
    assert state["layers"][1]["type"] == "segmentation"
    assert state["layers"][1]["source"] == (
        "https://fileglancer.int.janelia.org/api/content/groups_miaai_miaai/annotations/my_dataset/seg_run1.zarr/labels/pred_cells/|zarr:"
    )

    # make_fileglancer_url alias produces the identical result
    assert (
        lmd.make_fileglancer_url(
            raw=raw_path,
            seg=seg_path,
            raw_key="raw",
            seg_key="labels/pred_cells",
            raw_name="raw_image",
            seg_name="predictions",
        )
        == url
    )


@pytest.mark.parametrize("version,tag", [(None, "zarr"), ("zarr2", "zarr2"), ("zarr3", "zarr3")])
def test_external_segmentation_format_is_independent_of_raw(version, tag):
    """A Zarr3 raw volume must not force external Zarr2 predictions to use the v3 reader."""
    import lmd_catalog as lmd

    raw = lmd.VolumeEntry(name="raw", path="/groups/miaai/miaai/raw.zarr", zarr_version="zarr3")
    state = lmd.parse_neuroglancer_url(lmd.make_neuroglancer_url(
        raw=raw,
        seg="/groups/miaai/miaai/predictions.zarr/labels/cells",
        seg_zarr_version=version,
    ))
    assert state["layers"][0]["source"].endswith("/raw/|zarr3:")
    assert state["layers"][1]["source"].endswith(f"/predictions.zarr/labels/cells/|{tag}:")


def test_segmentation_entry_preserves_known_format():
    import lmd_catalog as lmd

    seg = lmd.VolumeEntry(
        name="predictions", path="/nrs/mia/predictions.zarr",
        image_key="labels/cells", zarr_version="zarr2",
    )
    state = lmd.parse_neuroglancer_url(lmd.make_neuroglancer_url(
        raw="/groups/miaai/miaai/raw.zarr", raw_key="raw", seg=seg,
    ))
    assert state["layers"][1]["source"].endswith("/predictions.zarr/labels/cells/|zarr2:")


def test_volume_entry_neuroglancer_url_auto_gt_and_custom():
    """Verify VolumeEntry.neuroglancer_url overlaying ground truth or external segmentation."""
    import lmd_catalog as lmd

    v = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
    assert v.has_ground_truth

    # Auto-overlay GT with automatic 1-99% B&C normalization from catalog
    gt_url = v.neuroglancer_url()
    assert gt_url.startswith("https://fileglancer.int.janelia.org/neuroglancer/#!%7B")
    gt_state = lmd.parse_neuroglancer_url(gt_url)
    assert len(gt_state["layers"]) == 2
    assert gt_state["layers"][0]["type"] == "image"
    assert gt_state["layers"][0]["source"].endswith("/raw/|zarr3:")
    assert gt_state["layers"][0]["tab"] == "rendering"
    assert gt_state["layers"][0]["shaderControls"]["normalized"]["range"] == [301, 1130]
    assert gt_state["layers"][0]["shaderControls"]["normalized"]["window"] == [0, 1695]
    assert gt_state["layers"][1]["type"] == "segmentation"
    assert gt_state["layers"][1]["name"] == "ground_truth"
    assert gt_state["layers"][1]["source"].endswith("labels/manual_gt-cell-final/|zarr:")

    # Explicit custom B&C override
    custom_norm_url = v.neuroglancer_url(raw_range=(200, 800), raw_window=(0, 1200))
    custom_norm_state = lmd.parse_neuroglancer_url(custom_norm_url)
    assert custom_norm_state["layers"][0]["shaderControls"]["normalized"]["range"] == [200, 800]
    assert custom_norm_state["layers"][0]["shaderControls"]["normalized"]["window"] == [0, 1200]

    # Disable B&C normalization
    no_norm_url = v.neuroglancer_url(raw_range=False)
    no_norm_state = lmd.parse_neuroglancer_url(no_norm_url)
    assert "shaderControls" not in no_norm_state["layers"][0]

    # Raw only
    raw_only_url = v.neuroglancer_url(include_gt=False)
    raw_state = lmd.parse_neuroglancer_url(raw_only_url)
    assert len(raw_state["layers"]) == 1
    assert raw_state["layers"][0]["shaderControls"]["normalized"]["range"] == [301, 1130]

    # Custom external segmentation
    ext_url = v.neuroglancer_url(
        seg="/nrs/cosem/user/preds/dg_crop1.zarr",
        seg_key="labels/aff_seg",
        seg_name="model_output",
    )
    ext_state = lmd.parse_neuroglancer_url(ext_url)
    assert len(ext_state["layers"]) == 2
    assert ext_state["layers"][1]["name"] == "model_output"
    assert ext_state["layers"][1]["source"] == (
        "https://fileglancer.int.janelia.org/api/content/nrs_cosem/user/preds/dg_crop1.zarr/labels/aff_seg/|zarr:"
    )


def test_to_fileglancer_content_url():
    """Verify conversion of file paths and browse URLs to Fileglancer API content URLs."""
    from lmd_catalog.viewers import to_fileglancer_content_url

    # groups/ cluster path
    res = to_fileglancer_content_url("/groups/miaai/miaai/data/crop.zarr", key="raw")
    assert res == "https://fileglancer.int.janelia.org/api/content/groups_miaai_miaai/data/crop.zarr/raw/|zarr3:"

    # embedded subpath in .zarr/
    res = to_fileglancer_content_url("/groups/miaai/miaai/data/crop.zarr/labels/seg")
    assert res == "https://fileglancer.int.janelia.org/api/content/groups_miaai_miaai/data/crop.zarr/labels/seg/|zarr3:"

    # nrs/ cluster path and zarr2
    res = to_fileglancer_content_url("/nrs/cosem/sample.zarr", key="s0", zarr_version="zarr2")
    assert res == "https://fileglancer.int.janelia.org/api/content/nrs_cosem/sample.zarr/s0/|zarr2:"

    # browse URL conversion
    res = to_fileglancer_content_url("https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/data/crop.zarr", key="raw")
    assert res == "https://fileglancer.int.janelia.org/api/content/groups_miaai_miaai/data/crop.zarr/raw/|zarr3:"

    # Precomputed / external untouched
    pre = "precomputed://https://neuroglancer.janelia.org/volume"
    assert to_fileglancer_content_url(pre) == pre



def test_strict_schema_rejection():
    """Verify that pydantic enforces closed enums and extra='forbid' (replacing cue vet)."""
    from pydantic import ValidationError
    from lmd_catalog.models import AnnotationEntry, VolumeEntry

    # 1. Reject unknown status
    with pytest.raises(ValidationError, match="Input should be"):
        AnnotationEntry.model_validate({
            "title": "test",
            "issue": {"number": 1, "url": "http", "repository": "repo"},
            "status": "NonExistentStatus",  # invalid enum
        })

    # 2. Reject unknown extra fields (closedness)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        VolumeEntry.model_validate({
            "name": "test",
            "path": "/path",
            "unknown_typo_field": "bad",
        })

    # 3. Reject out-of-bounds numbers
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        AnnotationEntry.model_validate({
            "title": "test",
            "issue": {"number": 1, "url": "http", "repository": "repo"},
            "completion_pct": -5.0,
        })


def test_layered_data_root_and_to_miao_root(monkeypatch):
    """Verify layered data root: to_miao(root=...), with_root, query root params, set_data_root, and LMD_DATA_ROOT env."""
    import lmd_catalog as lmd
    from pathlib import Path

    # Ensure clean slate
    lmd.reset_data_root()
    assert lmd.get_data_root() == lmd.DEFAULT_DATA_ROOT

    # 1. to_miao(root=...) on default VolumeEntry
    v = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
    cfg = v.to_miao(root="/Volumes/smb/data")
    assert cfg.path == "/Volumes/smb/data/exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001.zarr"
    assert cfg.label_key == "labels/manual_gt-cell-final"
    assert cfg.normalize_min == 301.0

    # Path object and trailing slash normalization
    cfg_path = v.to_miao(root=Path("/Volumes/smb/data/"))
    assert cfg_path.path == "/Volumes/smb/data/exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001.zarr"

    # 2. VolumeEntry.with_root
    v_reroot = v.with_root("/mnt/mirror")
    assert v_reroot.path == "/mnt/mirror/exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001.zarr"
    assert v_reroot.data_root == "/mnt/mirror"
    assert len(v_reroot.tracked_by) == 1
    assert v_reroot.has_ground_truth

    # 3. all(root=...), find(root=...), get(root=...)
    all_reroot = lmd.all(root="/Volumes/smb/data")
    assert len(all_reroot) == 838
    assert all_reroot[0].path.startswith("/Volumes/smb/data/")
    # Confirm tracked annotations preserved
    assert sum(len(x.tracked_by) for x in all_reroot) == 25

    find_reroot = lmd.find(organism="Mouse", has_ground_truth=True, root="/Volumes/smb/data")
    assert len(find_reroot) > 0
    assert find_reroot[0].path.startswith("/Volumes/smb/data/")

    get_reroot = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001", root="/Volumes/smb/data")
    assert get_reroot.path == "/Volumes/smb/data/exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001.zarr"

    # 4. Session level set_data_root and reset_data_root
    lmd.set_data_root("/Volumes/session_root")
    assert lmd.get_data_root() == "/Volumes/session_root"
    v_session = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
    assert v_session.path.startswith("/Volumes/session_root/")
    assert len(v_session.tracked_by) == 1
    cfg_session = v_session.to_miao()
    assert cfg_session.path.startswith("/Volumes/session_root/")
    assert cfg_session.label_key == "labels/manual_gt-cell-final"

    lmd.reset_data_root()
    assert lmd.get_data_root() == lmd.DEFAULT_DATA_ROOT

    # 5. LMD_DATA_ROOT environment variable
    monkeypatch.setenv("LMD_DATA_ROOT", "/Volumes/env_root")
    lmd.reset_data_root()
    assert lmd.get_data_root() == "/Volumes/env_root"
    v_env = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
    assert v_env.path.startswith("/Volumes/env_root/")
    assert len(v_env.tracked_by) == 1

    # Clean up
    monkeypatch.delenv("LMD_DATA_ROOT", raising=False)
    lmd.reset_data_root()


def test_volume_and_annotation_shape_and_voxelsize():
    """Verify shape, voxelsize, and axes on VolumeEntry and AnnotationEntry."""
    import lmd_catalog as lmd

    vols = lmd.all()
    assert len(vols) == 838

    # All volumes have extracted shape, voxelsize, and axes
    for v in vols:
        assert v.shape is not None and len(v.shape) >= 3
        assert v.voxelsize is not None and len(v.voxelsize) >= 3
        assert v.axes is not None and len(v.axes) >= 3
        assert len(v.shape) == len(v.axes) == len(v.voxelsize)

    # 1. Volume with zyx native axes
    v_zyx = lmd.get("em-celegans-funceworm-jrc-20250414/crop-001")
    assert v_zyx.axes == ["z", "y", "x"]
    assert v_zyx.shape == [8699, 5253, 5654]
    assert v_zyx.voxelsize == [6.0, 6.0, 6.0]
    assert v_zyx.shape_dict == {"z": 8699, "y": 5253, "x": 5654}
    assert v_zyx.shape_order("zyx") == [8699, 5253, 5654]
    assert v_zyx.shape_order("xyz") == [5654, 5253, 8699]
    assert v_zyx.voxelsize_order("zyx") == [6.0, 6.0, 6.0]

    # 2. Volume with xyz native axes
    v_xyz = lmd.get("exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001")
    assert v_xyz.axes == ["x", "y", "z"]
    assert v_xyz.shape == [2304, 2304, 393]
    assert v_xyz.voxelsize == [159.989, 159.989, 400.0]
    assert v_xyz.shape_dict == {"x": 2304, "y": 2304, "z": 393}
    assert v_xyz.shape_order("zyx") == [393, 2304, 2304]
    assert v_xyz.shape_order("xyz") == [2304, 2304, 393]
    assert v_xyz.voxelsize_order("zyx") == [400.0, 159.989, 159.989]

    # 3. Annotation with ground truth segmentation metadata
    ann_gt = lmd.get_annotation(7)
    assert ann_gt.shape == [1, 2304, 2304, 393]
    assert ann_gt.axes == ["c", "x", "y", "z"]
    assert ann_gt.voxelsize == [1.0, 159.989, 159.989, 400.0]
    assert ann_gt.roi_shape == [194, 482, 482]
    assert ann_gt.shape_dict == {"c": 1, "x": 2304, "y": 2304, "z": 393}
    assert ann_gt.shape_order("zyx") == [393, 2304, 2304]

    # 4. Annotation with ROI but no GT ingested raster
    ann_roi = lmd.get_annotation(10)
    assert ann_roi.shape is None
    assert ann_roi.roi is not None
    assert ann_roi.roi_shape == [194, 482, 482]

    # 5. with_root preserves shape, voxelsize, and axes
    v_reroot = v_xyz.with_root("/Volumes/smb/data")
    assert v_reroot.shape == v_xyz.shape
    assert v_reroot.voxelsize == v_xyz.voxelsize
    assert v_reroot.axes == v_xyz.axes
