# PNG panels for the mia-evals leaderboard datasets

Status: **plan + feasibility prototype** (2026-10-07). Nothing here is implemented in either repo.

`mia-evals` (`~/proj/mia-evals`, AI-HHMI/mia-evals) will be a consumer of a visual overview of the data. It wants **one
PNG panel per leaderboard dataset** (= per task). The same tooling would later produce an overview of the whole catalog,
which would be multi-GB, so PNG outputs must not be committed to a repo.

## What mia-evals needs

The units are its 7 leaderboard tasks, defined in `configs/<task>/data/{fit,test}.yaml`: **21 volume entries over 14
distinct stores**.

| task | fit | test | resolves to catalog? |
| --- | --- | --- | --- |
| `gary_comparison_neuron_instance` | 1 | 1 | yes (hemibrain EB crop) |
| `hemibrain_eb_neurite_tracing` | – | 3 | no (`mia-evals-data/hemibrain_eb_lsd/roi_*.zarr`) |
| `lmd_ssl_v1_neuron_instance` | 4 | 4 | yes |
| `lmd_ssl_v1_zebrafish_instance` | 1 | 1 | yes |
| `nisb_base_neurite_tracing` | 1 | 1 | no (`lmd-v0.0.1/dev/nisb/...`) |
| `zebrafinch_neurite_tracing` | 1 | 1 | no (`mia-evals-data/zebrafinch_j0126`) |
| `zebrafinch_neurite_tracing_11um` | 1 | 1 | no (same store, smaller ROI) |

Each entry gives `path`, `image_key`, optional `label_key`, `zarr_version`, `bounding_box`, and optional
`normalize_min`/`normalize_max`; the file also gives `resolutions` and `patch_size`. Things that make this non-trivial:

- **`bounding_box` is in level-0 voxels, in the file's `output_axes` spatial order**: `lcxyz` means XYZ, `lczyx` means ZYX.
  The panel generator must honor this per file.
- **`resolutions` is a list of per-scale triples** (use the first).
- **Only 12 of 21 entries resolve to catalog volumes.** Panels must be driven by the config's `path`; the catalog is only
  used to decorate them (subtype, organism, catalog name where there is one).
- **The tracing tasks have no `label_key`** (they are scored against skeletons held elsewhere).
- mia-evals does not import `lmd_catalog` today.

## The panel

One PNG per volume, 3 rows by 4 columns (xy / xz / yz / z-projection):

1. **Context**: the whole store at a coarse level, with the scored ROI outlined.
2. **Scored ROI**: the finest level at which it fits in about 600 px, with ground-truth labels overlaid when `label_key` is set.
3. **Model-input patch**: a `patch_size` crop at the evaluation resolution, i.e. what the model actually sees.

The header gives task / split / name, the store path, axes, dtype, shape, the ROI in level-0 voxels, and the label key.
A **task panel** is a grid of its volume panels (fit and test side by side), written as `<task>.png`.

Scale rules that worked in the prototype:

- context level: the coarsest level whose longest side is at least 256 voxels
- ROI level: the finest level whose ROI longest side is at most 600 voxels
- evaluation level: the level whose x/y voxel size is nearest `resolutions`
- contrast: `normalize_min`/`normalize_max` when given, else a 1–99.5 percentile stretch per panel
- aspect ratios come from the voxel sizes, so anisotropic data is drawn true to shape

## What the prototype showed

Four representative volumes were extracted and rendered (Kasthuri15 AC4, zebrafish fish2 doublecube1, the zebrafinch
benchmark ROI, hemibrain ROI 1). Approach confirmed on both zarr formats, three axis layouts and anisotropic voxels.

- **Cost is small.** Extracting all 4 took about 3 s in total on the login node; 0.8–15 MB of intermediate data and about
  1 MB per PNG. All 21 entries should take under a minute and about 25 MB.
- **Every store is a multiscale pyramid** (4–7 levels, sharded zarr3 for lmd data, gzip zarr2 for `mia-evals-data`),
  except the three `hemibrain_eb_lsd/roi_*.zarr` stores: a single full-resolution level of 1,875³ to 3,125³.
- **Label arrays have their own pyramid.** At the same level index the zebrafish labels were half the z-size of the image.
  Labels must be matched to an image level by voxel size, not by index, and resampled with nearest-neighbour.
- **Panels surface real data problems**: black bands (blank sections) in the zebrafish xz/yz views, and z-misalignment
  streaks in the Kasthuri slab. They are only visible in the orthogonal views.
- **Issues to handle**
  - Max projection of dense EM is mush; it only reads well for stained structures (the zebrafinch vessels). Choose the
    projection type per modality, or make it optional.
  - When the ROI covers the whole store at the same level (the lmd tasks, zebrafinch) the context and ROI rows duplicate;
    drop one.
  - Stores with no pyramid (hemibrain ROIs) need strided reads to about 512 px, and projections must be skipped
    (3–6 G voxels at full resolution).
  - Guard projections by size: only when the ROI is at most about 400 M voxels at the chosen level.

## Architecture

Two stages, because the cluster `.venv` has `numpy`, `tensorstore` and `miao` but **no** `zarr`, `PIL` or `matplotlib`:

1. **extract** (cluster): read slices and projections with `tensorstore`, write one small `.npz` per volume.
2. **render** (anywhere): compose the PNG panels with matplotlib.

Alternative: add an `overview` extra to `pyproject.toml` and `uv sync --extra overview` on the cluster to collapse this
into one stage. That is simpler, if installing matplotlib on the cluster is acceptable.

## Storage and incremental runs

- Outputs go to a directory on the cluster **outside** `data/` (so the catalog's disk walk ignores it), e.g.
  `/groups/miaai/miaai/lmd-v0.0.1/overview/` with `volumes/`, `tasks/` and a `manifest.json`.
- Commit at most a small manifest keyed on store path, zarr metadata, config hash and renderer version, so reruns are
  incremental.
- The full-catalog overview (about 1,077 volumes at 1 MB or more each) is what makes this multi-GB. The 7 task panels are small.

## Open questions

1. **Where does the code live?** In `lmd-catalog` (`scripts/overview/`) reading mia-evals' YAMLs by path, or in `mia-evals`?
2. **How do the 7 task PNGs reach mia-evals?** Committed there (about 25 MB), published to its GitHub Pages, or served
   from the cluster?
3. **Tracing tasks (no `label_key`)**: keep the panel plain, or overlay the skeleton ground truth? Where is it stored?
4. **Fit and test, or test only?**
5. Later, for the full catalog: pick channel 0 / first timepoint for stores with `c` or `t` axes.

## Next steps

1. Answer the open questions above.
2. Generalize the prototype into `scripts/overview/` and run it over all 21 entries.
3. Build the per-task grids.
4. Agree the integration with mia-evals (manifest plus how the PNGs are embedded or fetched).

## Prototype artifacts (not in the repo)

The throwaway prototype lives only in the session scratchpad: `extract.py` (cluster stage, about 140 lines), `render.py`
(local stage, about 90 lines), the four extracted `.npz` files and the four sample PNGs. The cluster scratch files were
removed. Ask to have the prototype scripts copied into the repo as a starting point.
