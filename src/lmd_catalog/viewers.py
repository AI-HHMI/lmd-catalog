"""Neuroglancer and Fileglancer URL generation for LMD catalog volumes."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional, Union
from urllib.parse import quote, unquote

if TYPE_CHECKING:
    from lmd_catalog.models import VolumeEntry


DEFAULT_VIEWER_BASE_URL = "https://fileglancer.int.janelia.org/neuroglancer/#!"


def split_zarr_path_and_key(path: str, key: Optional[str] = None) -> tuple[str, Optional[str]]:
    """If path contains a .zarr extension with a trailing subpath, split them."""
    if key is not None:
        return path, key
    if ".zarr/" in path:
        zarr_idx = path.index(".zarr/") + 5
        return path[:zarr_idx], path[zarr_idx:].strip("/")
    return path, key


def to_fileglancer_content_url(
    path: str,
    key: Optional[str] = None,
    zarr_version: Optional[str] = "zarr3",
) -> str:
    """Convert a filesystem path or browse URL to a Fileglancer API content URL for Neuroglancer.

    Handles cluster path prefixes like /groups/miaai/miaai -> groups_miaai_miaai,
    embedded group keys (e.g. .zarr/labels/seg), and zarr format tags (|zarr3:).
    Ensures a trailing slash before |zarr to match Fileglancer and Neuroglancer URL resolution.
    """
    if path.startswith(("precomputed://", "zarr://", "zarr2://", "zarr3://", "n5://")):
        return path

    path, key = split_zarr_path_and_key(path, key)

    if path.startswith("http://") or path.startswith("https://"):
        url = path.replace("/browse/", "/api/content/")
    else:
        clean = path.lstrip("/")
        if clean.startswith("groups/"):
            parts = clean.split("/")
            if len(parts) >= 3:
                clean = f"{parts[0]}_{parts[1]}_{parts[2]}/{'/'.join(parts[3:])}"
        elif clean.startswith("nrs/"):
            parts = clean.split("/")
            if len(parts) >= 2:
                clean = f"{parts[0]}_{parts[1]}/{'/'.join(parts[2:])}"
        url = f"https://fileglancer.int.janelia.org/api/content/{clean}"

    if key:
        url = f"{url.rstrip('/')}/{key.lstrip('/')}"

    if zarr_version and not url.endswith(":") and "|zarr" not in url:
        v_str = "zarr3" if "3" in str(zarr_version) else "zarr2"
        url = f"{url.rstrip('/')}/|{v_str}:"
    elif "|zarr" in url:
        prefix, tag = url.split("|zarr", 1)
        url = f"{prefix.rstrip('/')}/|zarr{tag}"

    return url


def make_neuroglancer_url(
    raw: Union[str, VolumeEntry],
    seg: Optional[Union[str, VolumeEntry]] = None,
    *,
    raw_key: Optional[str] = None,
    seg_key: Optional[str] = None,
    raw_name: str = "raw",
    seg_name: str = "segmentation",
    raw_zarr_version: Optional[str] = None,
    seg_zarr_version: Optional[str] = None,
    layout: str = "4panel",
    additional_layers: Optional[list[dict[str, Any]]] = None,
    viewer_base_url: str = DEFAULT_VIEWER_BASE_URL,
) -> str:
    """Generate a Neuroglancer URL combining raw and segmentation layers from separate Zarr stores.

    Args:
        raw: File path, Fileglancer URL, or VolumeEntry for the raw image volume.
        seg: Optional file path, Fileglancer URL, or VolumeEntry for the segmentation volume.
        raw_key: Array or group key for raw volume (defaults to raw.image_key if VolumeEntry).
        seg_key: Array or group key for segmentation volume (e.g. 'labels/seg').
        raw_name: Display name for the raw layer in Neuroglancer (default: 'raw').
        seg_name: Display name for the segmentation layer (default: 'segmentation').
        raw_zarr_version: 'zarr2' or 'zarr3' for raw volume (defaults to raw.zarr_version if VolumeEntry).
        seg_zarr_version: 'zarr2' or 'zarr3' for seg volume (defaults to seg.zarr_version if VolumeEntry).
        layout: Neuroglancer layout name (default: '4panel', or 'xy', '4panel-alt', etc.).
        additional_layers: Optional list of additional custom Neuroglancer layer dicts.
        viewer_base_url: Base URL for Neuroglancer viewer instance.

    Returns:
        A complete, clickable Neuroglancer URL with encoded multi-layer state.
    """
    # 1. Resolve raw volume parameters
    if isinstance(raw, str):
        raw_path = raw
    else:
        raw_path = raw.path
        raw_key = raw_key or raw.image_key
        raw_zarr_version = raw_zarr_version or raw.zarr_version
        raw_name = raw_name or raw.name

    raw_source = to_fileglancer_content_url(
        raw_path,
        key=raw_key,
        zarr_version=raw_zarr_version or "zarr3",
    )

    layers: list[dict[str, Any]] = [
        {
            "type": "image",
            "name": raw_name,
            "source": raw_source,
        }
    ]

    # 2. Resolve segmentation volume parameters if provided
    if seg is not None:
        if isinstance(seg, str):
            seg_path = seg
        else:
            seg_path = seg.path
            seg_key = seg_key or getattr(seg, "label_key", None) or getattr(seg, "image_key", None)
            seg_zarr_version = seg_zarr_version or seg.zarr_version
            seg_name = seg_name or "segmentation"

        seg_source = to_fileglancer_content_url(
            seg_path,
            key=seg_key,
            zarr_version=seg_zarr_version or "zarr3",
        )
        layers.append(
            {
                "type": "segmentation",
                "name": seg_name,
                "source": seg_source,
            }
        )

    # 3. Append any additional custom layers
    if additional_layers:
        layers.extend(additional_layers)

    state = {
        "layers": layers,
        "layout": layout,
    }

    # Compact JSON encoding
    encoded_state = quote(json.dumps(state, separators=(",", ":")))
    base = viewer_base_url.rstrip("/")
    if base.endswith("#!"):
        return f"{base}{encoded_state}"
    if "#!" in base:
        return f"{base}{encoded_state}"
    return f"{base}/#!{encoded_state}"


def parse_neuroglancer_url(url: str) -> dict[str, Any]:
    """Extract and parse the JSON state dictionary from a Neuroglancer URL."""
    if "#!" not in url:
        raise ValueError(f"URL does not contain a Neuroglancer state fragment ('#!'): {url}")
    fragment = url.split("#!", 1)[1]
    decoded = unquote(fragment)
    return json.loads(decoded)


# Alias for discoverability matching user terminology
make_fileglancer_url = make_neuroglancer_url
