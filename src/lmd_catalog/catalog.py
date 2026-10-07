"""Catalog management and lookup for the Large Microscopy Dataset."""

from __future__ import annotations

import json
import os
import re
from importlib import resources
from pathlib import Path
from typing import Optional, Union

from lmd_catalog.models import (
    DEFAULT_DATA_ROOT,
    AnnotationEntry,
    PretrainingEntry,
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


def store_paths(hhmi_path: str) -> list[str]:
    """Absolute paths in a free-text `hhmi_path` field. Several may be joined by ';', ', ', newlines or spaces;
    anything after '.zarr' (e.g. '/raw') and any trailing parenthetical remark is dropped. Prose and
    non-absolute fragments are ignored."""
    tokens = [re.sub(r"\s+\(.*$", "", t, flags=re.S) for t in re.split(r"[;,\s]+(?=/)", hhmi_path.strip())]
    return [re.sub(r"(\.zarr)/.*$", r"\1", t).rstrip("/") for t in tokens if t.startswith("/")]


class Catalog:
    """In-memory index of all LMD volumes, annotation issues, and pretraining dataset records."""

    def __init__(
        self,
        volumes_data: Optional[dict] = None,
        annotations_data: Optional[dict] = None,
        data_root: Optional[Union[str, Path]] = None,
        pretraining_data: Optional[dict] = None,
    ):
        if data_root is None:
            data_root = os.environ.get("LMD_DATA_ROOT", DEFAULT_DATA_ROOT)
        self.data_root = str(data_root).rstrip("/")

        if volumes_data is None:
            volumes_data = _load_json_data("lmd_volumes.json")
        if annotations_data is None:
            annotations_data = _load_json_data("lmd_annotations.json")
        if pretraining_data is None:
            pretraining_data = _load_json_data("lmd_pretraining.json")

        self._pretraining: list[PretrainingEntry] = [
            PretrainingEntry.model_validate(p) for p in pretraining_data.get("pretraining", [])
        ]

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
                label_keys=v.get("label_keys", []),
                added=v.get("added"),
            )
            self._volumes.append(entry)
            self._by_name[name] = entry
            self._by_path[path] = entry
            if canonical_path != path:
                self._by_path[canonical_path] = entry
            self._by_dataset.setdefault(dataset, []).append(entry)

        # 4. Join pretraining records: to the annotation tracking the same GitHub issue, else to volumes by path
        by_issue = {(a.issue.repository, a.issue.number): a for a in self._annotations}
        self._joined_pretraining: set[tuple[str, int]] = set()
        for p in self._pretraining:
            key = (p.issue.repository, p.issue.number)
            if key in by_issue:
                by_issue[key].pretraining = p
                continue
            exact: dict[str, VolumeEntry] = {}
            whole_dataset: dict[str, VolumeEntry] = {}
            for token in store_paths(p.hhmi_path or ""):
                if not token.startswith(canonical_root + "/"):
                    continue
                rel = token[len(canonical_root) + 1 :]
                if rel.endswith(".zarr") and rel[: -len(".zarr")] in self._by_name:
                    exact[rel[: -len(".zarr")]] = self._by_name[rel[: -len(".zarr")]]
                elif rel in self._by_dataset:
                    whole_dataset.update({v.name: v for v in self._by_dataset[rel]})
            for v in exact.values():
                v.pretraining.append(p)
            for v in whole_dataset.values():
                v.dataset_pretraining.append(p)
            if exact or whole_dataset:
                self._joined_pretraining.add(key)

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

    def pretraining(self) -> list[PretrainingEntry]:
        """Return all dataset records tracked in the mia_pretraining project."""
        return list(self._pretraining)

    def unjoined_pretraining(self) -> list[PretrainingEntry]:
        """Pretraining records that name a path (`hhmi_path`) but matched no volume or dataset, and aren't
        attached to an annotation either."""
        annotated = {(a.issue.repository, a.issue.number) for a in self._annotations}
        return [
            p for p in self._pretraining
            if p.hhmi_path
            and (p.issue.repository, p.issue.number) not in annotated
            and (p.issue.repository, p.issue.number) not in self._joined_pretraining
        ]

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
