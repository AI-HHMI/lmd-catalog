"""Programmatic catalog for the Large Microscopy Dataset (LMD)."""

from pathlib import Path
from typing import Optional, Union

from lmd_catalog.catalog import Catalog
from lmd_catalog.models import (
    DEFAULT_DATA_ROOT,
    AnnotationEntry,
    AnnotationIssue,
    ROI,
    VolumeEntry,
)
from lmd_catalog.viewers import (
    DEFAULT_VIEWER_BASE_URL,
    make_fileglancer_url,
    make_neuroglancer_url,
    parse_neuroglancer_url,
    to_fileglancer_content_url,
)

__version__ = "0.1.0"
__all__ = [
    "Catalog",
    "VolumeEntry",
    "AnnotationEntry",
    "AnnotationIssue",
    "ROI",
    "DEFAULT_DATA_ROOT",
    "DEFAULT_VIEWER_BASE_URL",
    "get",
    "all",
    "list_names",
    "list_datasets",
    "find",
    "annotations",
    "get_annotation",
    "default_catalog",
    "set_data_root",
    "get_data_root",
    "reset_data_root",
    "make_neuroglancer_url",
    "make_fileglancer_url",
    "to_fileglancer_content_url",
    "parse_neuroglancer_url",
]

_DEFAULT_CATALOG: Optional[Catalog] = None


def default_catalog() -> Catalog:
    """Return the singleton default Catalog instance."""
    global _DEFAULT_CATALOG
    if _DEFAULT_CATALOG is None:
        _DEFAULT_CATALOG = Catalog()
    return _DEFAULT_CATALOG


def set_data_root(data_root: Union[str, Path]) -> None:
    """Set the data root path for the default catalog in this session."""
    global _DEFAULT_CATALOG
    _DEFAULT_CATALOG = Catalog(data_root=data_root)


def get_data_root() -> str:
    """Return the current data root path for the default catalog."""
    return default_catalog().data_root


def reset_data_root() -> None:
    """Reset the default catalog to default data root (or LMD_DATA_ROOT env var)."""
    global _DEFAULT_CATALOG
    _DEFAULT_CATALOG = None


def get(name_or_path: str, root: Optional[Union[str, Path]] = None) -> VolumeEntry:
    """Lookup a volume by name or path in the default catalog."""
    return default_catalog().get(name_or_path, root=root)


def all(root: Optional[Union[str, Path]] = None) -> list[VolumeEntry]:
    """Return all volumes in the default catalog."""
    return default_catalog().all(root=root)


def list_names() -> list[str]:
    """Return all volume names in the default catalog."""
    return default_catalog().list_names()


def list_datasets() -> list[str]:
    """Return all distinct dataset names in the default catalog."""
    return default_catalog().list_datasets()


def find(
    dataset: Optional[str] = None,
    status: Optional[str] = None,
    modality: Optional[str] = None,
    organism: Optional[str] = None,
    is_annotated: Optional[bool] = None,
    has_ground_truth: Optional[bool] = None,
    root: Optional[Union[str, Path]] = None,
) -> list[VolumeEntry]:
    """Filter volumes in the default catalog."""
    return default_catalog().find(
        dataset=dataset,
        status=status,
        modality=modality,
        organism=organism,
        is_annotated=is_annotated,
        has_ground_truth=has_ground_truth,
        root=root,
    )


def annotations() -> list[AnnotationEntry]:
    """Return all annotations in the default catalog."""
    return default_catalog().annotations()


def get_annotation(issue_number: int) -> AnnotationEntry:
    """Lookup an annotation by GitHub issue number in the default catalog."""
    return default_catalog().get_annotation(issue_number)
