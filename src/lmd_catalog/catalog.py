"""Catalog management and lookup for the Large Microscopy Dataset."""

from __future__ import annotations

import json
import os
from importlib import resources
from pathlib import Path
from typing import Optional, Union

from lmd_catalog.models import (
    DEFAULT_DATA_ROOT,
    AnnotationEntry,
    VolumeEntry,
)


def _load_json_data(filename: str) -> dict:
    """Load JSON data file from package resources or local project root."""
    try:
        # Python 3.9+ resources API
        data_file = resources.files("lmd_catalog").joinpath("data", filename)
        if data_file.is_file():
            return json.loads(data_file.read_text(encoding="utf-8"))
    except Exception:
        pass

    # Fallback paths for local development / testing
    fallbacks = [
        Path(__file__).parent / "data" / filename,
        Path(__file__).parent.parent.parent / filename,
    ]
    for p in fallbacks:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)

    raise FileNotFoundError(f"Could not locate catalog data file: {filename}")


class Catalog:
    """In-memory index of all LMD volumes and annotation issues."""

    def __init__(
        self,
        volumes_data: Optional[dict] = None,
        annotations_data: Optional[dict] = None,
        data_root: Optional[Union[str, Path]] = None,
    ):
        if data_root is None:
            data_root = os.environ.get("LMD_DATA_ROOT", DEFAULT_DATA_ROOT)
        self.data_root = str(data_root).rstrip("/")

        if volumes_data is None:
            volumes_data = _load_json_data("lmd_volumes.json")
        if annotations_data is None:
            annotations_data = _load_json_data("lmd_annotations.json")

        # 1. Parse annotations
        raw_annotations = annotations_data.get("annotations", [])
        self._annotations: list[AnnotationEntry] = [
            AnnotationEntry.model_validate(a) for a in raw_annotations
        ]
        self._annotations_by_issue: dict[int, AnnotationEntry] = {
            a.issue.number: a for a in self._annotations
        }

        # 2. Build index from volume path to matching annotations
        path_to_annotations: dict[str, list[AnnotationEntry]] = {}
        for ann in self._annotations:
            for sp in ann.source_paths:
                path_to_annotations.setdefault(sp, []).append(ann)

        # 3. Parse volumes and attach tracked_by join
        raw_volumes = volumes_data.get("volumes", [])
        self._volumes: list[VolumeEntry] = []
        self._by_name: dict[str, VolumeEntry] = {}
        self._by_path: dict[str, VolumeEntry] = {}
        self._by_dataset: dict[str, list[VolumeEntry]] = {}

        canonical_root = DEFAULT_DATA_ROOT.rstrip("/")

        for v in raw_volumes:
            name = v["name"]
            path = self.data_root + "/" + name + ".zarr"
            canonical_path = canonical_root + "/" + name + ".zarr"
            image_key = v.get("image_key", "raw")
            zarr_version = v.get("zarr_version", "zarr3")
            dataset = name.split("/")[0]

            tracked = path_to_annotations.get(canonical_path) or path_to_annotations.get(path, [])
            entry = VolumeEntry(
                name=name,
                path=path,
                image_key=image_key,
                zarr_version=zarr_version,
                dataset=dataset,
                tracked_by=tracked,
                normalize_min=v.get("normalize_min"),
                normalize_max=v.get("normalize_max"),
                data_root=self.data_root,
                shape=v.get("shape"),
                voxelsize=v.get("voxelsize"),
                axes=v.get("axes"),
            )
            self._volumes.append(entry)
            self._by_name[name] = entry
            self._by_path[path] = entry
            if canonical_path != path:
                self._by_path[canonical_path] = entry
            self._by_dataset.setdefault(dataset, []).append(entry)

    def get(self, name_or_path: str, root: Optional[Union[str, Path]] = None) -> VolumeEntry:
        """Lookup a volume by its stable catalog name or absolute store path."""
        if name_or_path in self._by_name:
            v = self._by_name[name_or_path]
        elif name_or_path in self._by_path:
            v = self._by_path[name_or_path]
        else:
            raise KeyError(f"Volume not found in catalog: {name_or_path!r}")
        return v.with_root(root) if root is not None else v

    def __getitem__(self, name_or_path: str) -> VolumeEntry:
        return self.get(name_or_path)

    def __contains__(self, name_or_path: str) -> bool:
        return name_or_path in self._by_name or name_or_path in self._by_path

    def __len__(self) -> int:
        return len(self._volumes)

    def __iter__(self):
        return iter(self._volumes)

    def all(self, root: Optional[Union[str, Path]] = None) -> list[VolumeEntry]:
        """Return all volumes in the catalog."""
        if root is None:
            return list(self._volumes)
        return [v.with_root(root) for v in self._volumes]

    def list_names(self) -> list[str]:
        """Return all volume names in the catalog."""
        return list(self._by_name.keys())

    def list_datasets(self) -> list[str]:
        """Return all distinct dataset names in the catalog."""
        return list(self._by_dataset.keys())

    def annotations(self) -> list[AnnotationEntry]:
        """Return all tracked annotation items."""
        return list(self._annotations)

    def get_annotation(self, issue_number: int) -> AnnotationEntry:
        """Lookup an annotation item by its GitHub issue number."""
        if issue_number in self._annotations_by_issue:
            return self._annotations_by_issue[issue_number]
        raise KeyError(f"Annotation issue #{issue_number} not found in catalog")

    def find(
        self,
        dataset: Optional[str] = None,
        status: Optional[str] = None,
        modality: Optional[str] = None,
        organism: Optional[str] = None,
        is_annotated: Optional[bool] = None,
        has_ground_truth: Optional[bool] = None,
        root: Optional[Union[str, Path]] = None,
    ) -> list[VolumeEntry]:
        """Filter volumes by dataset or associated annotation metadata."""
        results = self._volumes
        if dataset is not None:
            results = [v for v in results if v.dataset == dataset]
        if is_annotated is not None:
            results = [v for v in results if v.is_annotated == is_annotated]
        if has_ground_truth is not None:
            results = [v for v in results if v.has_ground_truth == has_ground_truth]
        if status is not None:
            results = [
                v
                for v in results
                if any(a.status == status for a in v.tracked_by)
            ]
        if modality is not None:
            results = [
                v
                for v in results
                if any(a.data_modality == modality for a in v.tracked_by)
            ]
        if organism is not None:
            results = [
                v
                for v in results
                if any(a.model_organism == organism for a in v.tracked_by)
            ]
        if root is not None:
            return [v.with_root(root) for v in results]
        return results
