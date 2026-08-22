"""Rebuild lmd_annotations.json from the "mia_annotation" GitHub Project --
the source of truth for every #AnnotationItem field except `roi`, which this
script derives from bbox/bbox_size (itself a GitHub Project field), not a
GitHub field of its own.

UNVERIFIED: the gh CLI on the cluster is currently missing the read:project
scope (run `gh auth refresh -s read:project` once, interactively, to fix
this), so the exact JSON shape of `gh project item-list`'s custom-field keys
in FIELD_MAP below has never been checked against a live response -- only
guessed from the field names already visible in lmd_annotations.json. Before
trusting a full run, do a `--limit 1` dry run and diff its output against one
known-good entry in lmd_annotations.json; fix FIELD_MAP if names don't match.
Required schema fields (title/issue/source_paths) missing after mapping will
still fail loudly at `cue vet` time either way.

    gh auth refresh -s read:project   # one-time, interactive
    python3 scripts/rebuild_annotations.py > lmd_annotations.json
"""

from __future__ import annotations

import json
import subprocess

from roi_parse import parse_roi

PROJECT_OWNER = "AI-HHMI"
PROJECT_NUMBER = "1"

# GitHub Project custom field name -> #AnnotationItem field name.
FIELD_MAP = {
    "Status": "status",
    "Dataset": "dataset",
    "Tool": "tool",
    "Task": "task",
    "Model Organism": "model_organism",
    "Data Modality": "data_modality",
    "Structure of Interest": "structure_of_interest",
    "Priority": "priority",
    "Annotator": "annotator",
    "Completion %": "completion_pct",
    "Label Count": "label_count",
    "Timepoint": "timepoint",
    "Last Updated": "last_updated",
    "Bbox": "bbox",
    "Bbox Size": "bbox_size",
    "Fileglancer Path": "fileglancer_path",
    "GT Export Path": "gt_export_path",
    "GT Ingested Path": "gt_ingested_path",
    "Proofread Needed Path": "proofread_needed_path",
    "Proofread Export Path": "proofread_export_path",
    "Proofread Ingested Path": "proofread_ingested_path",
    "WK Link": "wk_link",
    "WK Annotation Link": "wk_ann_link",
}


def fetch_items():
    result = subprocess.run(
        ["gh", "project", "item-list", PROJECT_NUMBER, "--owner", PROJECT_OWNER,
         "--format", "json", "--limit", "200"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"gh project item-list failed: {result.stderr}"
    return json.loads(result.stdout)["items"]


def split_multi(value):
    """A "list of paths"-shaped field may come back as a real list, or as a
    newline-separated string, depending on the GitHub Project field type."""
    if isinstance(value, list):
        return value
    return [line.strip() for line in value.splitlines() if line.strip()]


def build_annotation(item):
    content = item["content"]
    assert content["type"] == "Issue", f"non-issue project item: {item}"

    annotation = {
        "title": content["title"],
        "issue": {
            "number": content["number"],
            "url": content["url"],
            "repository": content["repository"],
        },
        "source_paths": split_multi(item["Source Paths"]) if "Source Paths" in item else [],
    }
    for project_field, our_field in FIELD_MAP.items():
        if item.get(project_field) not in (None, ""):
            annotation[our_field] = item[project_field]
    if item.get("Assignees"):
        annotation["assignees"] = split_multi(item["Assignees"])
    if item.get("Labels"):
        annotation["labels"] = split_multi(item["Labels"])

    if annotation.get("bbox") and annotation.get("bbox_size"):
        annotation["roi"] = parse_roi(annotation["bbox"], annotation["bbox_size"])

    return annotation


def main():
    items = fetch_items()
    annotations = [build_annotation(i) for i in items]
    annotations.sort(key=lambda a: a["issue"]["number"])
    print(json.dumps({"annotations": annotations}, indent=2))


if __name__ == "__main__":
    main()
