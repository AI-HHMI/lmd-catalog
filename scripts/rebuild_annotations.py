"""Rebuild lmd_annotations.json from the "mia_annotation" GitHub Project --
the source of truth for every #AnnotationItem field except `roi`, which this
script derives from bbox/bbox_size (itself a GitHub Project field), not a
GitHub field of its own.

FIELD_MAP keys are the project's column names exactly as GitHub returns them (scripts/gh_project.py fetches the
items, with each issue's creation date, for a few GraphQL points).

    gh auth status   # needs the read:project scope
    python3 scripts/rebuild_annotations.py > lmd_annotations.json
"""

from __future__ import annotations

import json
import os

from gh_project import fetch_items, inconsistent
from roi_parse import parse_roi

PROJECT_NUMBER = 1

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
    # #1138: Source_Image_Path is the Fileglancer URL of the store's raw/ group, not its /groups path.
    1138: {
        "source_paths": ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW005-20260625/crop-001.zarr"],
    },
    # #7/#8/#9: verified ROIs (LICONN DG/Cortex/Hippocampus); the project has no bbox text for them yet.
    7: {
        "bbox": "X:1413-1895, Y:514-996, Z:83-277",
        "bbox_size": "482, 482, 194",
        "roi": {"x": [1413, 1895], "y": [514, 996], "z": [83, 277]},
    },
    8: {
        "bbox": "X:627-1109, Y:610-1092, Z:17-211",
        "bbox_size": "482, 482, 194",
        "roi": {"x": [627, 1109], "y": [610, 1092], "z": [17, 211]},
    },
    9: {
        "bbox": "X:496-978, Y:495-977, Z:44-238",
        "bbox_size": "482, 482, 194",
        "roi": {"x": [496, 978], "y": [495, 977], "z": [44, 238]},
    },
}

# Issues whose bbox text is not one box in the source volume's level-0 voxels, so it has no #ROI. Keyed by issue
# number and pinned to the exact text: once someone rewrites it upstream the entry stops matching and the rebuild
# fails, asking for it to be removed (the new text is then parsed as usual).
UNPARSED_BBOX = {
    1138: {
        "bbox": "BBox1: Z[265:532], Y[678:946], X[572:841]; BBox2: Z[1035:1302], Y[167:436], X[844:1114] (resolution: segmentation layer 9nm iso)",
        "why": "two boxes, ZYX, in the LSD segmentation's 9 nm grid (Proofread_Needed_Path), not source level-0 voxels",
    },
}

FIELD_MAP = {
    "Status": "status",
    "Dataset": "dataset",
    "Tool": "tool",
    "Task": "task",
    "Model_Organism": "model_organism",
    "Data_Modality": "data_modality",
    "Structure_of_Interest_1": "structure_of_interest",
    "Priority": "priority",
    "Annotator": "annotator",
    "Completion_Pct": "completion_pct",
    "Label_Count": "label_count",
    "Timepoint": "timepoint",
    "Last_Updated": "last_updated",
    "Bbox": "bbox",
    "Bbox_size": "bbox_size",
    "Fileglancer_Path": "fileglancer_path",
    "GT_Export_Path": "gt_export_path",
    "GT_Ingested_Path": "gt_ingested_path",
    "Proofread_Needed_Path": "proofread_needed_path",
    "Proofread_Export_Path": "proofread_export_path",
    "Proofread_Ingested_Path": "proofread_ingested_path",
    "WK_Link": "wk_link",
    "WK_Ann_Link": "wk_ann_link",
}


def build_annotation(item):
    fields = item["fields"]
    # Source_Image_Path is a single string; multiple paths are "; "-joined
    # (confirmed against issue #12, a paired fullvol+sub crop).
    if not fields.get("Source_Image_Path"):
        inconsistent(item, "no Source_Image_Path in the project; item skipped")
        return None
    source_paths = [p.strip() for p in fields["Source_Image_Path"].split(";") if p.strip()]

    annotation = {
        "title": item["title"],
        "issue": item["issue"],
        "source_paths": source_paths,
    }
    for project_field, our_field in FIELD_MAP.items():
        if fields.get(project_field) not in (None, ""):
            annotation[our_field] = fields[project_field]
    if item.get("assignees"):
        annotation["assignees"] = item["assignees"]
    if item.get("labels"):
        annotation["labels"] = item["labels"]

    unparsed = UNPARSED_BBOX.get(item["issue"]["number"])
    if unparsed:
        if annotation.get("bbox") != unparsed["bbox"]:
            inconsistent(item, "bbox changed upstream, remove its UNPARSED_BBOX entry")
    elif annotation.get("bbox") and annotation.get("bbox_size"):
        try:
            annotation["roi"] = parse_roi(annotation["bbox"], annotation["bbox_size"])
        except AssertionError as e:
            inconsistent(item, f"{e}; roi omitted")

    annotation.update(PENDING_UPSTREAM_FIXES.get(item["issue"]["number"], {}))

    return annotation


def main():
    # shape/voxelsize/axes are hand-set (not GitHub Project fields) -- carry them over by issue number.
    with open(os.path.join(os.path.dirname(__file__), "..", "lmd_annotations.json")) as f:
        text = f.read()
    assert text.strip(), "lmd_annotations.json is empty -- did you redirect output onto it? `git checkout lmd_annotations.json`, then write to a temp file and mv it into place"
    existing = {a["issue"]["number"]: a for a in json.loads(text)["annotations"]}
    items = fetch_items(PROJECT_NUMBER)
    built = [(build_annotation(i), i) for i in items]
    built = [(a, i) for a, i in built if a is not None]
    annotations = [a for a, _ in built]
    for a, item in built:
        a["created_at"] = item["created_at"]
        old = existing.get(a["issue"]["number"], {})
        a.update({k: old[k] for k in ("shape", "voxelsize", "axes") if k in old})
    annotations.sort(key=lambda a: a["issue"]["number"])
    print(json.dumps({"annotations": annotations}, indent=2))


if __name__ == "__main__":
    main()
