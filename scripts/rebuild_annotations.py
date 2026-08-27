"""Rebuild lmd_annotations.json from the "mia_annotation" GitHub Project --
the source of truth for every #AnnotationItem field except `roi`, which this
script derives from bbox/bbox_size (itself a GitHub Project field), not a
GitHub field of its own.

FIELD_MAP keys are gh's own JSON-ified project column names, confirmed
against a live `gh project item-list --limit 1` response: gh takes the
column's display name, joins its words with "_" preserving each word's own
capitalization, then lowercases just the first character of the whole
string ("Data Modality" -> "data_Modality", "WK Ann Link" -> "wK_Ann_Link",
single-word names just get their first letter lowercased). The one
oddity is `structure_of_Interest_1` (a trailing "_1", presumably from a
renamed/duplicated project column) -- if a future rebuild fails on a
missing `structure_of_interest`, check whether gh renumbered this.

    gh auth status   # needs the read:project scope
    python3 scripts/rebuild_annotations.py > lmd_annotations.json
"""

from __future__ import annotations

import json
import subprocess

from roi_parse import parse_roi

PROJECT_OWNER = "AI-HHMI"
PROJECT_NUMBER = "1"

# TEMPORARY, pending a human fixing these upstream in the GitHub Project UI:
# issues #18/#19's Source Image Path/Fileglancer Path fields still have the
# stale pre-reorg liconn_data/ path (the same one fixed locally in
# lmd_annotations.cue on 2026-08-20). Per the human-in-the-loop principle --
# hand-correcting a shared system of record is a Human.Edit action, not
# something a rebuild script does on a human's behalf -- this pins the
# known-good values locally rather than silently regressing them on every
# rebuild. Remove this once GH issue #18/#19's fields are corrected upstream.
PENDING_UPSTREAM_FIXES = {
    18: {
        "source_paths": ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW005-20260625/crop-001.zarr"],
        "fileglancer_path": "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW005-20260625/crop-001.zarr",
    },
    19: {
        "source_paths": ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW006-20260625/crop-001.zarr"],
        "fileglancer_path": "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW006-20260625/crop-001.zarr",
    },
}

FIELD_MAP = {
    "status": "status",
    "dataset": "dataset",
    "tool": "tool",
    "task": "task",
    "model_Organism": "model_organism",
    "data_Modality": "data_modality",
    "structure_of_Interest_1": "structure_of_interest",
    "priority": "priority",
    "annotator": "annotator",
    "completion_Pct": "completion_pct",
    "label_Count": "label_count",
    "timepoint": "timepoint",
    "last_Updated": "last_updated",
    "bbox": "bbox",
    "bbox_size": "bbox_size",
    "fileglancer_Path": "fileglancer_path",
    "gT_Export_Path": "gt_export_path",
    "gT_Ingested_Path": "gt_ingested_path",
    "proofread_Needed_Path": "proofread_needed_path",
    "proofread_Export_Path": "proofread_export_path",
    "proofread_Ingested_Path": "proofread_ingested_path",
    "wK_Link": "wk_link",
    "wK_Ann_Link": "wk_ann_link",
}


def fetch_items():
    result = subprocess.run(
        ["gh", "project", "item-list", PROJECT_NUMBER, "--owner", PROJECT_OWNER,
         "--format", "json", "--limit", "200"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"gh project item-list failed: {result.stderr}"
    return json.loads(result.stdout)["items"]


def build_annotation(item):
    content = item["content"]
    assert content["type"] == "Issue", f"non-issue project item: {item}"

    # source_Image_Path is a single string; multiple paths are "; "-joined
    # (confirmed against issue #12, a paired fullvol+sub crop).
    source_paths = [p.strip() for p in item["source_Image_Path"].split(";") if p.strip()]

    annotation = {
        "title": content["title"],
        "issue": {
            "number": content["number"],
            "url": content["url"],
            "repository": content["repository"],
        },
        "source_paths": source_paths,
    }
    for project_field, our_field in FIELD_MAP.items():
        if item.get(project_field) not in (None, ""):
            annotation[our_field] = item[project_field]
    if item.get("assignees"):
        annotation["assignees"] = item["assignees"]
    if item.get("labels"):
        annotation["labels"] = item["labels"]

    if annotation.get("bbox") and annotation.get("bbox_size"):
        annotation["roi"] = parse_roi(annotation["bbox"], annotation["bbox_size"])

    annotation.update(PENDING_UPSTREAM_FIXES.get(content["number"], {}))

    return annotation


def main():
    items = fetch_items()
    annotations = [build_annotation(i) for i in items]
    annotations.sort(key=lambda a: a["issue"]["number"])
    print(json.dumps({"annotations": annotations}, indent=2))


if __name__ == "__main__":
    main()
