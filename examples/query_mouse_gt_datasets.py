"""Example consumer: query all Mouse datasets that have ground truth annotations.

Demonstrates filtering by organism and ground-truth status, inspecting metadata
(ROIs, normalization ranges, issue tracking), and resolving to Miao VolumeConfigs.

Usage:
    python3 examples/query_mouse_gt_datasets.py
    python3 examples/query_mouse_gt_datasets.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Support running directly from repository root without prior pip install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import lmd_catalog as lmd


def volumesToDatasets(volumes: list[lmd.VolumeEntry]) -> dict[str, list[dict]]:
    datasets: dict[str, list[dict]] = defaultdict(list)
    for v in volumes:
        # Extract ground truth annotations
        gt_annotations = [a for a in v.tracked_by if a.gt_ingested_path]

        for ann in gt_annotations:
            if not ann.gt_ingested_path:
                continue
            gt_path = ann.gt_ingested_path
            gt_key = (
                gt_path[len(v.path) + 1 :]
                if gt_path.startswith(v.path + "/")
                else gt_path
            )
            entry = {
                "volume_name": v.name,
                "volume_path": v.path,
                "image_key": v.image_key,
                "gt_key": gt_key,
                "gt_path": gt_path,
                "roi_zyx": ann.roi.to_order("zyx") if ann.roi else None,
                "normalization": (
                    [v.normalize_min, v.normalize_max]
                    if v.normalize_min is not None
                    else None
                ),
                "issue_number": ann.issue.number,
                "issue_title": ann.title,
                "data_modality": ann.data_modality,
                "structure": ann.structure_of_interest,
            }
            datasets[v.dataset].append(entry)

    return dict(datasets)


def main():
    volumes = lmd.find(organism="Mouse", has_ground_truth=True)
    for i, v in enumerate(volumes):
        print(i, v.model_dump_json(indent=2))

    datasets = volumesToDatasets(volumes)
    for dataset_name, crops in datasets.items():
        print(f"Dataset: {dataset_name}")
        for crop in crops:
            print(f"  • Volume:        {crop['volume_name']}")
            print(f"    Issue:         #{crop['issue_number']} ({crop['issue_title']})")
            print(f"    Modality:      {crop['data_modality']}")
            print(f"    Structure:     {crop['structure']}")
            print(f"    GT Key:        {crop['gt_key']}")
            print(f"    ROI (ZYX):     {crop['roi_zyx']}")
            print(f"    Normalization: {crop['normalization']}")

            # Demonstrate direct resolution into Miao VolumeConfig
            vol = lmd.get(crop["volume_name"])
            miao_cfg = vol.to_miao(issue=crop["issue_number"])
            print(
                f"    Miao Config:   resolved label_key={miao_cfg.label_key!r}, "
                f"bbox={miao_cfg.bounding_box}, "
                f"norm=({miao_cfg.normalize_min}, {miao_cfg.normalize_max})"
            )
        print()


if __name__ == "__main__":
    main()
