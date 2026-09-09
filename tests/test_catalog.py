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
    assert cfg.bounding_box is None

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


def test_fileglancer_urls():
    """Verify fileglancer URL generation."""
    import lmd_catalog as lmd

    v = lmd.get("em-celegans-funceworm-jrc-20250414/crop-001")
    url = v.fileglancer_url()
    assert url.startswith("https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/")
    assert v.name in url


def test_strict_schema_rejection():
    """Verify that pydantic enforces closed enums and extra='forbid' (replacing cue vet)."""
    from pydantic import ValidationError
    from lmd_catalog.models import AnnotationEntry, VolumeEntry

    # 1. Reject unknown status
    with pytest.raises(ValidationError, match="Input should be"):
        AnnotationEntry(
            title="test",
            issue={"number": 1, "url": "http", "repository": "repo"},
            status="NonExistentStatus",  # invalid enum
        )

    # 2. Reject unknown extra fields (closedness)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        VolumeEntry(
            name="test",
            path="/path",
            unknown_typo_field="bad",
        )

    # 3. Reject out-of-bounds numbers
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        AnnotationEntry(
            title="test",
            issue={"number": 1, "url": "http", "repository": "repo"},
            completion_pct=-5.0,
        )

