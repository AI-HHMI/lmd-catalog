"""Data models for LMD catalog volumes, annotations, and ROIs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from miao.config import VolumeConfig


class ROI(BaseModel):
    """Axis-labeled spatial region within a volume's level-0 raster."""

    model_config = ConfigDict(extra="forbid")

    x: list[int]
    y: list[int]
    z: list[int]

    def to_order(self, axes: str = "zyx") -> list[list[int]]:
        """Return bounding box ranges in the requested spatial axis order (e.g. 'zyx')."""
        axes = axes.lower()
        if len(axes) != 3 or set(axes) != set("xyz"):
            raise ValueError(
                f"spatial_axes must be a permutation of 'x','y','z', got {axes!r}"
            )
        lookup = {"x": list(self.x), "y": list(self.y), "z": list(self.z)}
        return [lookup[a] for a in axes]


class AnnotationIssue(BaseModel):
    """GitHub Project issue tracking an annotation task."""

    model_config = ConfigDict(extra="forbid")

    number: int
    url: str
    repository: str


AnnotationStatus = Literal[
    "Crop Pending Approval",
    "Crop Approved",
    "On Hold",
    "In Annotation",
    "Screening Queue",
    "Initial Screen",
    "Fix",
    "nth Screen",
    "Done",
    "GT_Ingested",
    "pre_paintera_proofreading",
    "Proofreading",
    "Proofread Screening Queue",
    "Proofread Initial Screen",
    "Proofread Fix",
    "Proofread nth Screen",
    "post_paintera_proofreading",
    "Proofread_ingested",
    "In Training",
]

AnnotationDataset = Literal[
    "Betzig Fish",
    "MammalianLICONN",
    "MICrONS",
    "FlyLICONN",
]

AnnotationTool = Literal[
    "Amira",
    "Paintera",
    "WebKnossos",
]

ModelOrganism = Literal[
    "Zebrafish",
    "Mouse",
    "Drosophila",
    "C. elegans",
    "Human",
    "Danionella",
]

DataModality = Literal[
    "Light-sheet (LLSM)",
    "Light-sheet (diSPIM)",
    "Expansion Microscopy (Spinning Disk)",
    "Expansion Microscopy (Mirror)",
    "ATUM-mSEM",
    "FIB-SEM",
    "ssTEM (Multibeam SEM)",
    "IBEAM-mSEM",
    "Confocal (CLSM)",
]

AnnotationTask = Literal[
    "dense annotation",
    "sparse annotation",
    "dense proofreading",
    "sparse proofreading",
]

StructureOfInterest = Literal[
    "neurons",
    "cells",
    "mitochondria",
    "synapses",
    "nuclei",
]

Priority = Literal["P1", "P2", "P3"]


class AnnotationEntry(BaseModel):
    """Annotation metadata tracked via GitHub Project."""

    model_config = ConfigDict(extra="forbid")

    title: str
    issue: AnnotationIssue
    status: Optional[AnnotationStatus] = None
    dataset: Optional[AnnotationDataset] = None
    tool: Optional[AnnotationTool] = None
    task: Optional[AnnotationTask] = None
    model_organism: Optional[ModelOrganism] = None
    data_modality: Optional[DataModality] = None
    structure_of_interest: Optional[StructureOfInterest] = None
    priority: Optional[Priority] = None
    annotator: Optional[str] = None
    assignees: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    completion_pct: Optional[float] = Field(default=None, ge=0, le=100)
    label_count: Optional[int] = Field(default=None, ge=0)
    timepoint: Optional[str] = None
    last_updated: Optional[str] = None
    bbox: Optional[str] = None
    bbox_size: Optional[str] = None
    roi: Optional[ROI] = None
    source_paths: list[str] = Field(default_factory=list)
    fileglancer_path: Optional[str] = None
    gt_export_path: Optional[str] = None
    gt_ingested_path: Optional[str] = None
    proofread_needed_path: Optional[str] = None
    proofread_export_path: Optional[str] = None
    proofread_ingested_path: Optional[str] = None
    wk_link: Optional[str] = None
    wk_ann_link: Optional[str] = None


class VolumeEntry(BaseModel):
    """A single OME-Zarr volume in the LMD corpus."""

    model_config = ConfigDict(extra="forbid")

    name: str
    path: str
    image_key: str = "raw"
    zarr_version: Literal["zarr2", "zarr3"] = "zarr3"
    dataset: str = ""
    tracked_by: list[AnnotationEntry] = Field(default_factory=list)
    normalize_min: Optional[float] = None
    normalize_max: Optional[float] = None

    @property
    def is_annotated(self) -> bool:
        """True if any GitHub Project issue tracks this volume."""
        return len(self.tracked_by) > 0

    @property
    def has_ground_truth(self) -> bool:
        """True if any tracking issue has an ingested ground-truth path."""
        return any(a.gt_ingested_path is not None for a in self.tracked_by)

    @property
    def ground_truth_paths(self) -> list[str]:
        """All ingested ground-truth paths associated with this volume."""
        return [
            a.gt_ingested_path
            for a in self.tracked_by
            if a.gt_ingested_path is not None
        ]

    def fileglancer_url(self) -> str:
        """Return a Janelia Fileglancer URL for this volume."""
        for ann in self.tracked_by:
            if ann.fileglancer_path and self.name in ann.fileglancer_path:
                return ann.fileglancer_path
        clean_path = self.path.lstrip("/")
        if clean_path.startswith("groups/"):
            parts = clean_path.split("/")
            if len(parts) >= 3:
                prefix = f"{parts[0]}_{parts[1]}_{parts[2]}"
                rest = "/".join(parts[3:])
                return f"https://fileglancer.int.janelia.org/browse/{prefix}/{rest}"
        return f"https://fileglancer.int.janelia.org/browse/{clean_path}"

    def neuroglancer_url(
        self,
        seg: str | VolumeEntry | None = None,
        *,
        raw_key: Optional[str] = None,
        seg_key: Optional[str] = None,
        include_gt: bool = True,
        raw_name: Optional[str] = None,
        seg_name: str = "segmentation",
        layout: str = "4panel",
        viewer_base_url: Optional[str] = None,
    ) -> str:
        """Return a Neuroglancer URL for this volume, optionally with segmentation overlay.

        If seg is omitted and include_gt is True (default) and this volume has ground truth
        annotations, the first ground truth dataset is automatically attached as the
        segmentation layer.
        """
        from lmd_catalog.viewers import DEFAULT_VIEWER_BASE_URL, make_neuroglancer_url

        if seg is None and include_gt and self.has_ground_truth and self.ground_truth_paths:
            seg = self.ground_truth_paths[0]
            seg_name = "ground_truth"

        return make_neuroglancer_url(
            raw=self,
            seg=seg,
            raw_key=raw_key,
            seg_key=seg_key,
            raw_name=raw_name or self.name.split("/")[-1],
            seg_name=seg_name,
            layout=layout,
            viewer_base_url=viewer_base_url or DEFAULT_VIEWER_BASE_URL,
        )

    def to_miao(
        self,
        spatial_axes: str = "zyx",
        issue: Optional[int] = None,
        label_key: Optional[str] = None,
        bounding_box: Optional[list[list[int]]] = None,
        **kwargs: Any,
    ) -> VolumeConfig:
        """Resolve this volume directly into a miao.config.VolumeConfig.

        CONTRACT: Never sets exp_factor; uses miao's default exp_factor=1.0 since
        LMD zarrs already bake expansion-microscopy voxel-size corrections into
        coordinateTransformations.

        Parameters:
            spatial_axes: Order of spatial axes for bounding_box (default: "zyx").
            issue: Specific GitHub issue number if volume is tracked by multiple annotations.
            label_key: Explicit override for label_key.
            bounding_box: Explicit override for bounding_box.
            **kwargs: Additional fields forwarded to VolumeConfig (e.g. weight, resolutions).
        """
        from miao.config import VolumeConfig

        config_args: dict[str, Any] = {
            "name": self.name,
            "path": self.path,
            "image_key": self.image_key,
            "zarr_version": self.zarr_version,
        }

        chosen_annotation: Optional[AnnotationEntry] = None
        if issue is not None:
            matches = [a for a in self.tracked_by if a.issue.number == issue]
            if not matches:
                raise ValueError(
                    f"Issue #{issue} does not track volume {self.name!r}"
                )
            chosen_annotation = matches[0]
        elif len(self.tracked_by) == 1:
            chosen_annotation = self.tracked_by[0]
        elif len(self.tracked_by) > 1 and (label_key is None or bounding_box is None):
            issues = [a.issue.number for a in self.tracked_by]
            raise ValueError(
                f"Volume {self.name!r} is tracked by {len(self.tracked_by)} annotations (issues: {issues}). "
                "Specify which annotation to use via `to_miao(issue=...)` or pass explicit label_key / bounding_box."
            )

        if chosen_annotation is not None:
            if label_key is None and chosen_annotation.gt_ingested_path:
                gt = chosen_annotation.gt_ingested_path
                prefix = self.path + "/"
                if gt.startswith(prefix):
                    label_key = gt[len(prefix) :]
            if bounding_box is None and chosen_annotation.roi:
                bounding_box = chosen_annotation.roi.to_order(spatial_axes)

        if label_key is not None:
            config_args["label_key"] = label_key
        if bounding_box is not None:
            config_args["bounding_box"] = bounding_box
        if self.normalize_min is not None:
            config_args["normalize_min"] = self.normalize_min
        if self.normalize_max is not None:
            config_args["normalize_max"] = self.normalize_max
        if self.normalize_min is not None or self.normalize_max is not None:
            config_args.setdefault("normalize", True)

        config_args.update(kwargs)
        return VolumeConfig(**config_args)
