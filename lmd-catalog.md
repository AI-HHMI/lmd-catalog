# Design Rationale: `lmd-catalog` and its Dependency on `miao-io`

## 1. Executive Summary & Context

The Larva Multimodal Dataset (LMD) at Janelia consists of 838 OME-Zarr image volumes, 26 manual annotation issues, and associated multimodal datasets stored across cluster storage (`/groups/miaai/miaai/lmd-v0.0.1/data`).

An earlier effort (`lmd-data-versioning`) attempted to formalize this catalog using CUE schemas and markdown specifications. While thorough, it had **zero downstream consumers**: training and evaluation pipelines (such as `lsd_neuron_segmentation` and `mia-muvit`) continued to copy-paste raw file paths and hand-craft custom volume configurations.

To make this dataset actionable and maintainable, the catalog is being reimagined as a first-class Python package: `lmd-catalog`. 

This document records the design discussions, architectural decisions, and trade-offs that led to the following consensus:
1. **`lmd-catalog` should be a versioned Git repository and Python package**, not a static file on cluster storage.
2. **`lmd-catalog` must remain separate from `miao` (`miao-io`)**, maintaining a clean boundary between institutional data and generic open-source tooling.
3. **`lmd-catalog` should depend directly on `miao-io`** to avoid the fragile "shadow schema" anti-pattern.
4. **`miao-io` must make PyTorch imports deferred/lazy**, ensuring that importing `miao.config` is sub-50ms, pure Pydantic, and safe for non-PyTorch / JAX environments.

---

## 2. Decision 1: Standalone Git Repo vs. Static Generated File (`catalog.json`)

A natural question was: *Why create a repository at all? Why not just generate a single `catalog.json` or `catalog.yaml` on cluster storage at `/groups/miaai/.../catalog.json`?*

While a static file on GPFS/NFS seems simple, it introduces critical failure modes in scientific computing:

### 2.1 The "Mutable Global Variable" vs. Scientific Provenance
A file sitting at a fixed path on a shared filesystem is mutable global state. If a volume's bounding box is adjusted, a voxel resolution typo is corrected, or an orientation axis is flipped:
- If edited in place, any model trained two months prior can no longer reproduce its exact input data or validation splits.
- If append-only semantics are enforced without version control, maintainers resort to namespace pollution: creating keys like `larva_v12_v2`, `larva_v12_fixed_roi`, or `larva_v12_20260901`. The catalog quickly becomes an untidy graveyard of deprecated aliases.

### 2.2 Version Pinning via Git & SemVer
By housing the catalog in a Git repository installed as a Python package, downstream pipelines can pin exact catalog releases in their `pyproject.toml` or lockfiles:
```toml
dependencies = [
    "lmd-catalog @ git+https://github.com/JaneliaSciComp/lmd-catalog.git@v0.2.1",
]
```
This decouples catalog evolution from experiment stability:
- Maintainers can fix errors, add metadata, and reorganize splits cleanly under semantic versioning.
- Past experiments remain 100% reproducible by referencing their pinned catalog commit or tag.

### 2.3 Code + Data (Client SDK vs. Fragile Parsers)
A catalog is rarely just static strings; downstream code needs convenience operations:
- Resolving relative cluster paths to absolute paths depending on cluster mount points.
- Querying volumes by stage, modality, or resolution.
- Generating Neuroglancer viewing links on the fly (`volume.neuroglancer_url()`).
- Slicing and sub-volume cropping.

If the catalog is merely a JSON file on disk, *every downstream repo* (`lsd_neuron_segmentation`, `mia-muvit`, analysis notebooks) must write its own parser, path resolver, and coordinate math. This guarantees code divergence and duplicated bugs. A Python package acts as a thin client SDK providing shared logic alongside data.

---

## 3. Decision 2: Why Not Merge `lmd-catalog` into `miao` (`miao-io`)?

Another option considered was: *Since `miao` handles volume I/O and dataset configuration, why not bundle the LMD catalog directly into `miao`?*

Merging the two is an architectural anti-pattern for several reasons:

| Property | `miao` (`miao-io`) | `lmd-catalog` |
| :--- | :--- | :--- |
| **Scope** | General-purpose OME-NGFF I/O library for PyTorch | Domain-specific biological dataset catalog |
| **Audience** | Open-source community (published to PyPI) | Janelia / HHMI internal researchers |
| **Path Coupling** | Strictly agnostic (accepts any Zarr URI or path) | Coupled to `/groups/miaai/miaai/...` cluster storage |
| **Metadata Coupling** | Generic chunks, bounds, channels, dtypes | GitHub issue trackers, biological stages, anatomical ROI labels |
| **Release Cadence** | Infrequent (driven by I/O algorithms, cache optimizations) | Frequent (driven by new volume acquisitions, annotator corrections) |

Tying `miao` to Janelia's cluster paths or specific specimen taxonomies would destroy `miao`'s viability as a reusable open-source library. Keeping them separate preserves clean separation of concerns.

---

## 4. Decision 3: Interface Design & The "Shadow Schema" Trap

Once established that `lmd-catalog` and `miao` are separate repos, the core architectural question arose:

> **How should `lmd-catalog` produce volume configurations for `miao`? Should `lmd-catalog` depend on `miao-io`, or should it emit raw dictionaries?**

### 4.1 Approach A: Duck Typing / Raw Dictionaries (No Dependency)
In this approach, `lmd-catalog` has zero dependencies on `miao`. It exposes a method like:
```python
# In lmd-catalog:
def to_miao_dict(self) -> dict:
    return {
        "source": self.zarr_path,
        "roi": {"offset": self.offset, "shape": self.shape},
        "dtype": self.dtype,
    }
```
Downstream consumers would do:
```python
import lmd_catalog as lmd
from miao.config import VolumeConfig

vol = lmd.get("larva_vNC_01")
cfg = VolumeConfig(**vol.to_miao_dict())
```

#### Why Approach A Fails: The Shadow Schema Trap
While superficially decoupled, this creates an unvalidated **shadow schema**:
1. `lmd-catalog` is implicitly writing code against `miao`'s internal data model without the type system or package manager knowing about it.
2. If `miao` renames a field (e.g., `source` $\to$ `uri`), introduces new required parameters (e.g., coordinate space definitions), or changes normalization settings, `lmd-catalog` cannot detect the breakage at CI time.
3. Errors only surface at runtime inside downstream training scripts when Pydantic throws a `ValidationError` on `VolumeConfig(**dict)`.
4. Downstream consumers are forced to write boilerplate glue code to bridge the two libraries.

### 4.2 Approach B: Direct Dependency (`lmd-catalog` depends on `miao-io`)
In this approach, `lmd-catalog` lists `miao-io` in its dependencies:
```python
# In lmd-catalog:
from miao.config import VolumeConfig

def to_miao(self) -> VolumeConfig:
    return VolumeConfig(
        source=self.zarr_path,
        roi={"offset": self.offset, "shape": self.shape},
        dtype=self.dtype,
    )
```

#### Advantages of Approach B:
1. **First-Class Schema Validation in CI**: `lmd-catalog`'s test suite can run:
   ```python
   for entry in catalog.all():
       entry.to_miao()  # Instantiates and validates real VolumeConfig objects
   ```
   If a catalog entry is malformed or if an update to `miao` changes the schema, CI fails immediately in `lmd-catalog` before any user runs a training job.
2. **Superior Developer Experience**: Users simply do:
   ```python
   import lmd_catalog as lmd
   cfg = lmd.get("larva_vNC_01").to_miao()
   ```
   Autocomplete, type hints, and editor navigation work end-to-end.

---

## 5. The Technical Hurdle: PyTorch Startup Latency & CUDA Conflicts

If Approach B is clearly better, why was there hesitation to make `lmd-catalog` depend on `miao-io`?

The hesitation stemmed from **PyTorch's import overhead**:
1. **Import Latency**: Historically, `import miao` imported `torch`.
   - On local NVMe/SSD, importing PyTorch takes ~400–600ms.
   - On cluster network filesystems (GPFS/NFS) under load, importing PyTorch can take **2.5 to 5+ seconds** due to metadata lookups across dozens of shared `.so` libraries.
   - For interactive exploration or fast CLI utilities (`lmd list`, `lmd info <volume>`), a multi-second startup delay makes the tool feel sluggish and broken.
2. **CUDA / JAX Contention**:
   - Some downstream pipelines (e.g., `lsd_neuron_segmentation` or evaluation suites) use **JAX** or non-PyTorch backends.
   - In certain environments, importing `torch` initializes the CUDA driver and can preemptively claim GPU memory (or conflict with JAX's CUDA memory allocator), leading to out-of-memory errors or device initialization failures.

If depending on `miao-io` meant that every invocation of `lmd-catalog` carried the full weight of PyTorch and CUDA, that dependency would indeed be unacceptable.

---

## 6. The Resolution: Deferred / Lazy PyTorch Imports in `miao-io`

To resolve the conflict between schema safety (Approach B) and lightweight execution, we inspected `miao/src/miao/config.py`.

### 6.1 The Root Cause in `miao.config`
`config.py` was importing `torch` solely for a simple dictionary mapping string names to PyTorch dtypes:
```python
# miao/src/miao/config.py
import torch  # <-- The sole reason PyTorch was being loaded during config parsing

IMAGE_DTYPE_MAP = {
    "uint8": torch.uint8,
    "float32": torch.float32,
    # ...
}
```
`VolumeConfig` is a **Pydantic configuration model**, not an execution kernel. It describes data paths, bounding boxes, and resolutions. It does not perform tensor arithmetic.

### 6.2 The Solution in `miao-io`
1. **Decouple `VolumeConfig` from `torch.dtype`**:
   Represent `dtype` in `VolumeConfig` as a string literal (e.g., `Literal["uint8", "float32", "uint16"]`) or defer the lookup to a property:
   ```python
   # miao/src/miao/config.py (Zero torch imports)
   from pydantic import BaseModel
   from typing import Literal

   class VolumeConfig(BaseModel):
       source: str
       dtype: Literal["uint8", "float32", "uint16"] = "float32"
       # ...
       
       def get_torch_dtype(self):
           import torch  # Lazy import only when PyTorch tensor conversion is explicitly requested
           return getattr(torch, self.dtype)
   ```
2. **Module-level Lazy Loading in `miao/__init__.py`**:
   Using Python 3.7+ PEP 562 module `__getattr__`, importing `miao` or `miao.config` does not load PyTorch dataset classes (`VolumeDataset`) until they are explicitly accessed:
   ```python
   # miao/__init__.py
   def __getattr__(name: str):
       if name == "VolumeDataset":
           from .dataset import VolumeDataset
           return VolumeDataset
       raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
   ```

### 6.3 Outcome of the Optimization
- **`from miao.config import VolumeConfig` drops from ~3,500ms to ~35ms** (a 100x speedup).
- The import depends only on `pydantic` and `pyyaml`.
- Zero CUDA initialization occurs. JAX pipelines and non-GPU tasks can import `miao.config` with complete safety.
- The objection to making `lmd-catalog` depend on `miao-io` is eliminated.

---

## 7. Target Architecture Summary

```
                       +----------------------------------+
                       |           miao-io                |
                       |  - VolumeConfig (pure Pydantic)  |  <--- Lightweight (<40ms)
                       |  - VolumeDataset (lazy PyTorch)  |
                       +-----------------+----------------+
                                         ^
                                         | imports VolumeConfig
                       +-----------------+----------------+
                       |          lmd-catalog             |
                       |  - 838 Zarr volume definitions   |
                       |  - CI validates with VolumeConfig|
                       |  - .to_miao() -> VolumeConfig    |
                       +-----------------+----------------+
                                         ^
                                         | pins via git/semver
          +------------------------------+------------------------------+
          |                                                             |
+---------+---------------------------+       +-------------------------+---------+
|     lsd_neuron_segmentation         |       |              mia-muvit            |
| - Uses lmd.get("...").to_miao()     |       | - Uses lmd.get("...").to_miao()   |
| - Safe in JAX (no torch triggered)  |       | - Directly passes to VolumeDataset|
+-------------------------------------+       +-----------------------------------+
```

### Key Takeaways
1. **Single Source of Truth**: `miao-io` defines the volume schema (`VolumeConfig`).
2. **No Shadow Schemas**: `lmd-catalog` outputs concrete `VolumeConfig` objects, allowing automated integrity verification in CI.
3. **Reproducibility**: `lmd-catalog` releases are tagged in Git and pinned in downstream projects.
4. **Zero Overhead**: Because `miao.config` avoids eager PyTorch imports, `lmd-catalog` stays fast, lightweight, and runtime-agnostic.
