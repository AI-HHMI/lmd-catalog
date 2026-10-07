"""Unit tests for the policy checks in scripts/ (the pure functions; no /groups needed)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

# scripts/data_root.py loads the repo's .env into os.environ on import; don't let that leak into the other tests.
_env = dict(os.environ)
from check_integrity import check_pretraining_joined, check_pretraining_matches_stores  # noqa: E402

os.environ.clear()
os.environ.update(_env)


def volume(shape=(10, 100, 100), voxelsize=(40.0, 8.0, 8.0), axes=("z", "y", "x"), **record):
    return {
        "name": "vol/crop-001", "shape": list(shape), "voxelsize": list(voxelsize), "axes": list(axes),
        "pretraining": [{"issue": {"repository": "AI-HHMI/mia_pretraining", "number": 1}, **record}],
    }


def test_matching_shape_and_voxel_size_pass():
    assert check_pretraining_matches_stores([volume(volume_shape_zyx="10×100×100", voxel_size_zyx_nm="40×8×8")]) == []


def test_axis_order_of_the_store_does_not_matter():
    store = volume(shape=(100, 100, 10), voxelsize=(8.0, 8.0, 40.0), axes=("x", "y", "z"), volume_shape_zyx="10×100×100", voxel_size_zyx_nm="40×8×8")
    assert check_pretraining_matches_stores([store]) == []


def test_project_shape_larger_on_every_axis_is_the_parent_dataset():
    assert check_pretraining_matches_stores([volume(volume_shape_zyx="1830×139264×180224")]) == []


def test_shape_smaller_on_any_axis_is_flagged():
    (msg,) = check_pretraining_matches_stores([volume(volume_shape_zyx="10×100×50")])
    assert "mia_pretraining#1" in msg and "shape" in msg


def test_voxel_size_within_one_percent_passes_but_a_real_difference_is_flagged():
    assert check_pretraining_matches_stores([volume(voxel_size_zyx_nm="40.2×8.05×8.05")]) == []
    (msg,) = check_pretraining_matches_stores([volume(voxel_size_zyx_nm="30×8×8")])
    assert "voxel size" in msg


def test_pre_expansion_voxel_size_is_allowed_only_with_a_matching_expansion_factor():
    store = dict(voxelsize=(400.0, 162.5, 162.5))
    assert check_pretraining_matches_stores([volume(**store, voxel_size_zyx_nm="25×10×10", expansion_factor="~16x")]) == []
    assert len(check_pretraining_matches_stores([volume(**store, voxel_size_zyx_nm="25×10×10", expansion_factor="32x")])) == 1
    assert len(check_pretraining_matches_stores([volume(**store, voxel_size_zyx_nm="25×10×10")])) == 1


def test_blank_prose_and_non_zyx_stores_are_skipped():
    assert check_pretraining_matches_stores([volume(volume_shape_zyx="", voxel_size_zyx_nm="~40 nm")]) == []
    assert check_pretraining_matches_stores([volume(axes=("c", "y", "x"), shape=(2, 100, 100), voxelsize=(1.0, 8.0, 8.0), volume_shape_zyx="1×1×1")]) == []
    assert check_pretraining_matches_stores([{"name": "no-metadata", "pretraining": [{"issue": {"repository": "r", "number": 2}}]}]) == []


def test_unjoined_records_are_flagged_except_statuses_that_are_not_catalog_volumes():
    def record(status):
        return {"title": "t", "status": status, "hhmi_path": "/x/y", "issue": {"repository": "AI-HHMI/mia_pretraining", "number": 3}}

    assert len(check_pretraining_joined([record("Consider for Training")])) == 1
    assert check_pretraining_joined([record("Pending Ingestion"), record("Model Development Only")]) == []


def make_store(tmp_path, metadata_file, content, image_key="raw"):
    array = tmp_path / image_key / "s0"
    array.mkdir(parents=True)
    (array / metadata_file).write_text(content)
    return {"name": "vol/crop-001", "path": str(tmp_path), "image_key": image_key,
            "pretraining": [{"issue": {"repository": "AI-HHMI/mia_pretraining", "number": 4}, "dtype": "uint16"}]}


def test_dtype_matches_zarr3_and_zarr2_metadata(tmp_path):
    from check_integrity import check_pretraining_dtype

    assert check_pretraining_dtype([make_store(tmp_path / "a", "zarr.json", '{"data_type": "uint16"}')]) == []
    assert check_pretraining_dtype([make_store(tmp_path / "b", ".zarray", '{"dtype": "<u2"}')]) == []
    assert check_pretraining_dtype([make_store(tmp_path / "c", "zarr.json", '{"data_type": "uint16"}', image_key="")]) == []


def test_dtype_mismatch_is_flagged(tmp_path):
    from check_integrity import check_pretraining_dtype

    (msg,) = check_pretraining_dtype([make_store(tmp_path / "a", "zarr.json", '{"data_type": "uint8"}')])
    assert "says dtype uint16" in msg and "uint8" in msg
    (msg,) = check_pretraining_dtype([make_store(tmp_path / "b", ".zarray", '{"dtype": "|u1"}')])
    assert "uint8" in msg


def test_dtype_check_skips_missing_metadata_and_unrecorded_dtypes(tmp_path):
    from check_integrity import check_pretraining_dtype, store_dtype

    store = make_store(tmp_path / "a", "zarr.json", '{"data_type": "uint8"}')
    assert check_pretraining_dtype([{**store, "path": str(tmp_path / "nowhere")}]) == []
    store["pretraining"][0]["dtype"] = None
    assert check_pretraining_dtype([store]) == []
    assert store_dtype(make_store(tmp_path / "b", ".zarray", '{"dtype": "|b1"}')) is None


def test_known_project_errors_are_ignored_but_must_keep_failing(monkeypatch):
    import check_integrity as c

    monkeypatch.setattr(c, "KNOWN_PROJECT_ERRORS", {})
    record = {"title": "t", "status": "Consider for Training", "hhmi_path": "/x/y", "issue": {"repository": "R", "number": 7}}
    assert len(c.check_pretraining_known_errors([record], [])) == 1  # an unknown problem is a violation

    monkeypatch.setattr(c, "KNOWN_PROJECT_ERRORS", {("R", 7): "typo in the project"})
    assert c.check_pretraining_known_errors([record], []) == []  # acknowledged, so ignored

    (msg,) = c.check_pretraining_known_errors([], [])  # fixed upstream: the entry is now stale
    assert "R#7" in msg and "typo in the project" in msg and "remove it" in msg


def test_known_project_errors_also_cover_store_mismatches(monkeypatch):
    import check_integrity as c

    store = volume(voxel_size_zyx_nm="30×8×8")  # does not match the store's 40×8×8
    monkeypatch.setattr(c, "KNOWN_PROJECT_ERRORS", {})
    assert len(c.check_pretraining_known_errors([], [store])) == 1
    monkeypatch.setattr(c, "KNOWN_PROJECT_ERRORS", {("AI-HHMI/mia_pretraining", 1): "copied from another dataset"})
    assert c.check_pretraining_known_errors([], [store]) == []
