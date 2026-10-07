"""Rebuild lmd_pretraining.json from the mia_pretraining GitHub Project (AI-HHMI/projects/4), the source
of truth for every #PretrainingEntry field except `created_at`, which comes from `gh issue list`
(the project items don't carry it).

Needs `gh` authenticated with `read:project`; no /groups mount. Project columns arrive as gh's JSON-ified
names ("HHMI_Path" -> "hHMI_Path", "Paper_DOI" -> "paper_DOI": first letter lowercased, the rest kept).
A column missing from FIELD_MAP fails the rebuild rather than being silently dropped.

    python3 scripts/rebuild_pretraining.py > /tmp/lmd_pretraining.json.new && mv /tmp/lmd_pretraining.json.new lmd_pretraining.json
"""

from __future__ import annotations

import json
import subprocess

PROJECT_OWNER = "AI-HHMI"
PROJECT_NUMBER = "4"

FIELD_MAP = {
    "status": "status",
    "organism": "organism",
    "data_Modality": "data_modality",
    "source_Type": "source_type",
    "dtype": "dtype",
    "has_Seg": "has_seg",
    "zarr_Format": "zarr_format",
    "compression": "compression",
    "memory_Order": "memory_order",
    "source_Lab": "source_lab",
    "dev_Stage": "dev_stage",
    "structure": "structure",
    "source_Format": "source_format",
    "paper_DOI": "paper_doi",
    "raw_Source_Path": "raw_source_path",
    "hHMI_Path": "hhmi_path",
    "fileglancer_Path": "fileglancer_path",
    "label_Path": "label_path",
    "label_Description": "label_description",
    "last_Updated": "last_updated",
    "voxel_Size_ZYX_nm": "voxel_size_zyx_nm",
    "volume_Shape_ZYX": "volume_shape_zyx",
    "physical_Volume": "physical_volume",
    "disk_Size": "disk_size",
    "num_Voxels": "num_voxels",
    "pct_Nonzero": "pct_nonzero",
    "expansion_Factor": "expansion_factor",
    "array_Dims": "array_dims",
    "axis_Order": "axis_order",
    "chunk_Shape": "chunk_shape",
    "shard_Shape": "shard_shape",
    "num_Scales": "num_scales",
    "preprocess": "preprocess",
    "training_BBox_s0_zyx": "training_bbox_s0_zyx",
    "discard_Reason": "discard_reason",
}
# Present on items but not stored (title/issue/assignees/labels are handled explicitly in build_entry).
NOT_STORED = {"content", "id", "title", "repository", "assignees", "labels", "milestone", "linked pull requests", "reviewers", "parent issue", "sub-issues progress"}


def gh_json(*cmd):
    result = subprocess.run(["gh", *cmd], capture_output=True, text=True)
    assert result.returncode == 0, f"gh {' '.join(cmd)} failed: {result.stderr}"
    return json.loads(result.stdout)


def fetch_items():
    return gh_json("project", "item-list", PROJECT_NUMBER, "--owner", PROJECT_OWNER, "--format", "json", "--limit", "5000")["items"]


def fetch_created_dates(repos):
    """(repository, issue number) -> ISO creation date."""
    created = {}
    for repo in repos:
        for i in gh_json("issue", "list", "--repo", repo, "--state", "all", "--limit", "5000", "--json", "number,createdAt"):
            created[(repo, i["number"])] = i["createdAt"][:10]
    return created


def build_entry(item, created):
    content = item["content"]
    assert content["type"] == "Issue", f"non-issue project item: {item}"
    unknown = set(item) - set(FIELD_MAP) - NOT_STORED
    assert not unknown, f"project column(s) not in FIELD_MAP (add them, and to PretrainingEntry): {sorted(unknown)} on {content['url']}"
    key = (content["repository"], content["number"])
    entry = {
        "title": content["title"],
        "issue": {"number": content["number"], "url": content["url"], "repository": content["repository"]},
        "created_at": created[key],
    }
    for project_field, our_field in FIELD_MAP.items():
        if item.get(project_field) not in (None, ""):
            entry[our_field] = item[project_field]
    if item.get("assignees"):
        entry["assignees"] = item["assignees"]
    if item.get("labels"):
        entry["labels"] = item["labels"]
    return entry


def main():
    items = fetch_items()
    created = fetch_created_dates({i["content"]["repository"] for i in items})
    entries = [build_entry(i, created) for i in items]
    entries.sort(key=lambda e: (e["issue"]["repository"], e["issue"]["number"]))
    print(json.dumps({"pretraining": entries}, indent=2))


if __name__ == "__main__":
    main()
