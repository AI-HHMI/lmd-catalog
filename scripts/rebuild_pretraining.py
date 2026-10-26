"""Rebuild lmd_pretraining.json from the mia_pretraining GitHub Project (AI-HHMI/projects/4), the source
of truth for every #PretrainingEntry field (`created_at` is the issue's creation date).

Needs `gh` authenticated with `read:project`; no /groups mount. scripts/gh_project.py fetches the items; FIELD_MAP
keys are the project's column names exactly as GitHub returns them. A column missing from FIELD_MAP fails the
rebuild rather than being silently dropped.

    python3 scripts/rebuild_pretraining.py > /tmp/lmd_pretraining.json.new && mv /tmp/lmd_pretraining.json.new lmd_pretraining.json
"""

from __future__ import annotations

import json

from gh_project import fetch_items, inconsistent

PROJECT_NUMBER = 4

FIELD_MAP = {
    "Status": "status",
    "Organism": "organism",
    "Data_Modality": "data_modality",
    "Source_Type": "source_type",
    "Dtype": "dtype",
    "Has_Seg": "has_seg",
    "Zarr_Format": "zarr_format",
    "Compression": "compression",
    "Memory_Order": "memory_order",
    "Source_Lab": "source_lab",
    "Dev_Stage": "dev_stage",
    "Structure": "structure",
    "Source_Format": "source_format",
    "Paper_DOI": "paper_doi",
    "Raw_Source_Path": "raw_source_path",
    "HHMI_Path": "hhmi_path",
    "Fileglancer_Path": "fileglancer_path",
    "Label_Path": "label_path",
    "Label_Description": "label_description",
    "Last_Updated": "last_updated",
    "Voxel_Size_ZYX_nm": "voxel_size_zyx_nm",
    "Volume_Shape_ZYX": "volume_shape_zyx",
    "Physical_Volume": "physical_volume",
    "Disk_Size": "disk_size",
    "Num_Voxels": "num_voxels",
    "Pct_Nonzero": "pct_nonzero",
    "Expansion_Factor": "expansion_factor",
    "Array_Dims": "array_dims",
    "Axis_Order": "axis_order",
    "Chunk_Shape": "chunk_shape",
    "Shard_Shape": "shard_shape",
    "Num_Scales": "num_scales",
    "Preprocess": "preprocess",
    "Training_BBox_s0_zyx": "training_bbox_s0_zyx",
    "Discard_Reason": "discard_reason",
}
# The Title column duplicates the issue title, which build_entry takes from the issue itself.
NOT_STORED = {"Title"}


def build_entry(item):
    fields = item["fields"]
    unknown = set(fields) - set(FIELD_MAP) - NOT_STORED
    if unknown:
        inconsistent(item, f"project column(s) not in FIELD_MAP (add them, and to PretrainingEntry); dropped: {sorted(unknown)}")
    entry = {"title": item["title"], "issue": item["issue"], "created_at": item["created_at"]}
    for project_field, our_field in FIELD_MAP.items():
        if fields.get(project_field) not in (None, ""):
            entry[our_field] = fields[project_field]
    if item.get("assignees"):
        entry["assignees"] = item["assignees"]
    if item.get("labels"):
        entry["labels"] = item["labels"]
    return entry


def main():
    entries = [build_entry(i) for i in fetch_items(PROJECT_NUMBER)]
    entries.sort(key=lambda e: (e["issue"]["repository"], e["issue"]["number"]))
    print(json.dumps({"pretraining": entries}, indent=2))


if __name__ == "__main__":
    main()
