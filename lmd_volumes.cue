// lmd-v0.0.1 data catalog schema: every .zarr volume actually present under
// /groups/miaai/miaai/lmd-v0.0.1/data, discovered by walking the directory tree
// directly. This is independent of any pretraining config's curation -- see
// /groups/miaai/miaai/lmd-v0.0.1/configs/README.md for how the generated YAML
// configs select and transform a subset of these (LM datasets, 2-channel
// funceworm, and a few others are excluded there but present here).
//
// Data lives in the sibling lmd_volumes.json (838 volumes across 102 datasets
// as of the last rebuild), not here -- this file is schema only. Regenerate
// the data with scripts/rebuild_volumes.py, never hand-edit lmd_volumes.json.
package lmd

import "list"

#DataRoot: "/groups/miaai/miaai/lmd-v0.0.1/data"

#Volume: {
	// "<dataset>/<crop>" relative to #DataRoot, without the .zarr suffix.
	name: string

	// Absolute path to the zarr store. Derived from name; every volume in this
	// corpus follows the convention, so no entry below overrides it.
	path: string | *(#DataRoot + "/" + name + ".zarr")

	// Top-level group holding the primary image array/pyramid.
	image_key: string | *"raw"

	// zarr2 stores have a top-level .zgroup; zarr3 stores have zarr.json.
	zarr_version: "zarr2" | *"zarr3"

	// Live join against annotations (lmd_annotations.cue): every GitHub Project
	// issue whose source_paths includes this volume's path. Usually empty --
	// most of the corpus has no annotation-tracking issue yet.
	tracked_by: [for a in annotations if list.Contains(a.source_paths, path) {a}]
}

volumes: [...#Volume]
