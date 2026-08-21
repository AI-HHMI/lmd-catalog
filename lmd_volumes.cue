// lmd-v0.0.1 data catalog: every .zarr volume actually present under
// /groups/miaai/miaai/lmd-v0.0.1/data, discovered by walking the directory tree
// directly. This is independent of any pretraining config's curation -- see
// /groups/miaai/miaai/lmd-v0.0.1/configs/README.md for how the generated YAML
// configs select and transform a subset of these (LM datasets, 2-channel
// funceworm, and a few others are excluded there but present here).
//
// 417 volumes across 69 datasets.
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

volumes: [...#Volume] & [
	// em-celegans-funceworm-jrc-20250414
	{name: "em-celegans-funceworm-jrc-20250414/crop-001"},
	// em-celegans-funceworm-jrc-20250908
	{name: "em-celegans-funceworm-jrc-20250908/crop-001"},
	// em-celegans-funceworm-jrc-3fold-2
	{name: "em-celegans-funceworm-jrc-3fold-2/crop-001"},
	// em-celegans-funceworm-jrc-P3-E5-D1-N2
	{name: "em-celegans-funceworm-jrc-P3-E5-D1-N2/crop-001_ch0-jrc_P3_E5_D1_N2_trimmed_align_v2"},
	// em-celegans-funceworm-jrc-comma-1
	{name: "em-celegans-funceworm-jrc-comma-1/crop-001_ch0-jrc_c-elegans-comma-1-two-channel_c0"},
	// em-celegans-funceworm-jrc_HPF-TAOTO-ME-S2_6x6nm_RegAffine-flattened
	{name: "em-celegans-funceworm-jrc_HPF-TAOTO-ME-S2_6x6nm_RegAffine-flattened/crop-001"},
	// em-drosophila-FANC-vnc
	{name: "em-drosophila-FANC-vnc/crop-001"},
	{name: "em-drosophila-FANC-vnc/crop-002"},
	// em-drosophila-banc
	{name: "em-drosophila-banc/crop-001_centralbrain"},
	{name: "em-drosophila-banc/crop-002_centralbrain"},
	{name: "em-drosophila-banc/crop-003_vnc"},
	{name: "em-drosophila-banc/crop-004_vnc"},
	// em-drosophila-flyem-cns-mito-gt-v6
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-001_box000"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-002_box001"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-003_box002"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-004_box003"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-005_box004"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-006_box005"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-007_box006"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-008_box007"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-009_box008"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-010_box009"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-011_box010"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-012_box011"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-013_box012"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-014_box013"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-015_box014"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-016_box015"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-017_box016"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-018_box017"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-019_box018"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-020_box019"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-021_box020"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-022_box021"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-023_box022"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-024_box023"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-025_box024"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-026_box025"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-027_box026"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-028_box027"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-029_box028"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-030_box029"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-031_box030"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-032_box031"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-033_box032"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-034_box033"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-035_box034"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-036_box035"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-037_box036"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-038_box037"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-039_box038"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-040_box039"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-041_box040"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-042_box041"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-043_box042"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-044_box043"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-045_box044"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-046_box045"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-047_box046"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-048_box047"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-049_box048"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-050_box049"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-051_box050"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-052_box051"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-053_box052"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-054_box053"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-055_box054"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-056_box055"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-057_box056"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-058_box057"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-059_box058"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-060_box059"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-061_box060"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-062_box061"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-063_box062"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-064_box063"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-065_box064"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-066_box065"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-067_box066"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-068_box067"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-069_box068"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-070_box069"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-071_box070"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-072_box071"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-073_box072"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-074_box073"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-075_box074"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-076_box075"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-077_box076"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-078_box077"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-079_box078"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-080_box079"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-081_box080"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-082_box081"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-083_box082"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-084_box083"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-085_box084"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-086_box085"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-087_box086"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-088_box087"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-089_box088"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-090_box089"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-091_box090"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-092_box091"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-093_box092"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-094_box093"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-095_box094"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-096_box095"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-097_box096"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-098_box097"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-099_box098"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-100_box099"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-101_box100"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-102_box101"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-103_box102"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-104_box103"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-105_box104"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-106_box105"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-107_box106"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-108_box107"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-109_box108"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-110_box109"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-111_box110"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-112_box111"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-113_box112"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-114_box113"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-115_box114"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-116_box115"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-117_box116"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-118_box117"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-119_box118"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-120_box119"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-121_box120"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-122_box121"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-123_box122"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-124_box123"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-125_box124"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-126_box125"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-127_box126"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-128_box127"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-129_box128"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-130_box129"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-131_box130"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-132_box131"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-133_box132"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-134_box133"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-135_box134"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-136_box135"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-137_box136"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-138_box137"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-139_box138"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-140_box139"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-141_box140"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-142_box141"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-143_box142"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-144_box143"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-145_box144"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-146_box145"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-147_box146"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-148_box147"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-149_box148"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-150_box149"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-151_box150"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-152_box151"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-153_box152"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-154_box153"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-155_box154"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-156_box155"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-157_box156"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-158_box157"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-159_box158"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-160_box159"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-161_box160"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-162_box161"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-163_box162"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-164_box163"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-165_box164"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-166_box165"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-167_box166"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-168_box167"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-169_box168"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-170_box169"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-171_box170"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-172_box171"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-173_box172"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-174_box173"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-175_box174"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-176_box175"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-177_box176"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-178_box177"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-179_box178"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-180_box179"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-181_box180"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-182_box181"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-183_box182"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-184_box183"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-185_box184"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-186_box185"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-187_box186"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-188_box187"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-189_box188"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-190_box189"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-191_box190"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-192_box191"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-193_box192"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-194_box193"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-195_box194"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-196_box195"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-197_box196"},
	{name: "em-drosophila-flyem-cns-mito-gt-v6/crop-198_box197"},
	// em-drosophila-flyem-hemibrain
	{name: "em-drosophila-flyem-hemibrain/crop-001_EllipsoidBody_x24000_y23000_z17000"},
	{name: "em-drosophila-flyem-hemibrain/crop-002_11k_x18000_y17000_z11000"},
	{name: "em-drosophila-flyem-hemibrain/crop-003_10k_x8000_y17000_z11000"},
	// em-human-H01-cortex
	{name: "em-human-H01-cortex/crop-001"},
	// em-hydra-zhang2025
	{name: "em-hydra-zhang2025/crop-001_x106212_y65861_z226"},
	{name: "em-hydra-zhang2025/crop-002_x33815_y86408_z95"},
	{name: "em-hydra-zhang2025/crop-003_x114198_y54198_z0"},
	// em-mosquito-bao2025-antennallobe
	{name: "em-mosquito-bao2025-antennallobe/crop-001_x114369_y44359_z3105"},
	{name: "em-mosquito-bao2025-antennallobe/crop-002_x38748_y49136_z3426"},
	// em-mouse-Jiefu-cerebellum
	{name: "em-mouse-Jiefu-cerebellum/crop-001"},
	// em-mouse-Kasthuri15-ac3ac4-cortex
	{name: "em-mouse-Kasthuri15-ac3ac4-cortex/crop-001_ac3_100slices"},
	{name: "em-mouse-Kasthuri15-ac3ac4-cortex/crop-002_ac4_100slices"},
	{name: "em-mouse-Kasthuri15-ac3ac4-cortex/crop-003_ac4train_80slices"},
	{name: "em-mouse-Kasthuri15-ac3ac4-cortex/crop-004_ac4val_20slices"},
	// em-mouse-MICrONS-minnie65
	{name: "em-mouse-MICrONS-minnie65/crop-001"},
	// em-salamander-jrc-amphiuma-liver
	{name: "em-salamander-jrc-amphiuma-liver/crop-001"},
	// em-salamander-jrc-axolotl-heart
	{name: "em-salamander-jrc-axolotl-heart/crop-001"},
	// em-salamander-jrc-axolotl-liver
	{name: "em-salamander-jrc-axolotl-liver/crop-001"},
	// em-zebrafish-fish1
	{name: "em-zebrafish-fish1/crop-001_x27648_y32963_z3143"},
	{name: "em-zebrafish-fish1/crop-002_x58228_y25201_z3904"},
	{name: "em-zebrafish-fish1/crop-003_x98895_y29905_z4127"},
	{name: "em-zebrafish-fish1/crop-004_gt-box-8nm_x59517_y30379_z2000"},
	{name: "em-zebrafish-fish1/crop-005_gt-em-8nm_x74367_y33700_z2000"},
	{name: "em-zebrafish-fish1/crop-006_gt-em-roi14_x71500_y45000_z2000"},
	{name: "em-zebrafish-fish1/crop-007_gt-em-roi16_x88500_y45000_z2000"},
	{name: "em-zebrafish-fish1/crop-008_gt-em_x61364_y37130_z2000"},
	{name: "em-zebrafish-fish1/crop-009_gt-roi1_x80000_y35000_z1350"},
	{name: "em-zebrafish-fish1/crop-010_gt-roi12_x89000_y60000_z2000"},
	{name: "em-zebrafish-fish1/crop-011_gt-roi2_x80000_y60000_z1350"},
	{name: "em-zebrafish-fish1/crop-012_gt-roi3_x68000_y37500_z1350"},
	{name: "em-zebrafish-fish1/crop-013_gt-roi4_x66500_y53500_z1350"},
	{name: "em-zebrafish-fish1/crop-014_gt-roi5_x55000_y29000_z1350"},
	{name: "em-zebrafish-fish1/crop-015_gt-roi6_x55000_y63000_z1350"},
	// em-zebrafish-fish2
	{name: "em-zebrafish-fish2/crop-001_doublecube1_x52000_y42500_z0"},
	{name: "em-zebrafish-fish2/crop-002_doublecube2_x120000_y45500_z0"},
	{name: "em-zebrafish-fish2/crop-003_quadcube1_x23908_y18314_z0"},
	{name: "em-zebrafish-fish2/crop-004_quadcube2_x15114_y10046_z0"},
	{name: "em-zebrafish-fish2/crop-005_quadcube3_x9638_y10314_z0"},
	{name: "em-zebrafish-fish2/crop-006_quadcube4_x48294_y6026_z0"},
	// exm-drosophila-flyliconn-ExPID06B-Brain2-PFA-AA-epox
	{name: "exm-drosophila-flyliconn-ExPID06B-Brain2-PFA-AA-epox/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID10-20250923_2ndGel_PBS_MES_B1_Atto488_40XW_002
	{name: "exm-drosophila-flyliconn-FlyID10-20250923_2ndGel_PBS_MES_B1_Atto488_40XW_002/crop-001_normalized", zarr_version: "zarr2"},
	{name: "exm-drosophila-flyliconn-FlyID10-20250923_2ndGel_PBS_MES_B1_Atto488_40XW_002/crop-001_raw", zarr_version: "zarr2"},
	// exm-drosophila-flyliconn-FlyID10-20250923_2ndGel_PBS_MES_B2_Atto488_40XW_002
	{name: "exm-drosophila-flyliconn-FlyID10-20250923_2ndGel_PBS_MES_B2_Atto488_40XW_002/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID10-20250923_2ndGel_PBS_PIPES_B2_Atto488_40XW_002
	{name: "exm-drosophila-flyliconn-FlyID10-20250923_2ndGel_PBS_PIPES_B2_Atto488_40XW_002/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID22-20260203_2ndGel_0.0655BIS_40XW004
	{name: "exm-drosophila-flyliconn-FlyID22-20260203_2ndGel_0.0655BIS_40XW004/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID25-20260216_MESFix_2ndGel_B1_40XW
	{name: "exm-drosophila-flyliconn-FlyID25-20260216_MESFix_2ndGel_B1_40XW/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID25-20260216_MESFix_2ndGel_B1_40XW003
	{name: "exm-drosophila-flyliconn-FlyID25-20260216_MESFix_2ndGel_B1_40XW003/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID25-20260216_MOPS_2ndGel_B1_40XW
	{name: "exm-drosophila-flyliconn-FlyID25-20260216_MOPS_2ndGel_B1_40XW/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID25-mitochondria-20260216_MOPS_2ndGel_B1_40XW003
	{name: "exm-drosophila-flyliconn-FlyID25-mitochondria-20260216_MOPS_2ndGel_B1_40XW003/crop-001"},
	// exm-drosophila-flyliconn-FlyID26-20260221_2ndgel_S4_B1_40XW
	{name: "exm-drosophila-flyliconn-FlyID26-20260221_2ndgel_S4_B1_40XW/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID26-20260221_2ndgel_S4_B1_40XW003
	{name: "exm-drosophila-flyliconn-FlyID26-20260221_2ndgel_S4_B1_40XW003/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID26-20260221_2ndgel_S4_B1_40XW004
	{name: "exm-drosophila-flyliconn-FlyID26-20260221_2ndgel_S4_B1_40XW004/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID47-2ndgel-DUP-S7-40XW003-20260619
	{name: "exm-drosophila-flyliconn-FlyID47-2ndgel-DUP-S7-40XW003-20260619/crop-001_clahe"},
	{name: "exm-drosophila-flyliconn-FlyID47-2ndgel-DUP-S7-40XW003-20260619/crop-001_raw"},
	// exm-drosophila-flyliconn-FlyID47-2ndgel-DUP-S7-B2-40XW-20260620
	{name: "exm-drosophila-flyliconn-FlyID47-2ndgel-DUP-S7-B2-40XW-20260620/crop-001_clahe"},
	{name: "exm-drosophila-flyliconn-FlyID47-2ndgel-DUP-S7-B2-40XW-20260620/crop-001_raw"},
	// exm-drosophila-flyliconn-FlyID47-2ndgel-S2-40XW007-20260619
	{name: "exm-drosophila-flyliconn-FlyID47-2ndgel-S2-40XW007-20260619/crop-001_clahe"},
	{name: "exm-drosophila-flyliconn-FlyID47-2ndgel-S2-40XW007-20260619/crop-001_raw"},
	// exm-drosophila-flyliconn-FlyID47-2ndgel-S2-40XW009-20260619
	{name: "exm-drosophila-flyliconn-FlyID47-2ndgel-S2-40XW009-20260619/crop-001_clahe"},
	{name: "exm-drosophila-flyliconn-FlyID47-2ndgel-S2-40XW009-20260619/crop-001_raw"},
	// exm-drosophila-flyliconn-FlyID49-2ndgel-BIS-40XW002-20260625
	{name: "exm-drosophila-flyliconn-FlyID49-2ndgel-BIS-40XW002-20260625/crop-001_fullvol"},
	// exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW005-20260625
	{name: "exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW005-20260625/crop-001"},
	// exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW006-20260625
	{name: "exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW006-20260625/crop-001"},
	// exm-drosophila-flyliconn-FlyID49-mirrorscope-central-20260702
	{name: "exm-drosophila-flyliconn-FlyID49-mirrorscope-central-20260702/crop-001_central"},
	// exm-drosophila-flyliconn-FlyID49-mirrorscope-lobe-20260702
	{name: "exm-drosophila-flyliconn-FlyID49-mirrorscope-lobe-20260702/crop-001_lobe"},
	// exm-drosophila-flyliconn-matt-260601-60X-B2-1-027
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B2-1-027/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B2-1-028
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B2-1-028/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B2-1-029
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B2-1-029/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B2-2-030
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B2-2-030/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B2-2-031
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B2-2-031/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B2-2-032
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B2-2-032/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B4-1-040
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B4-1-040/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B4-1-041
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B4-1-041/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B4-1-042
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B4-1-042/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B4-2-043
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B4-2-043/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B4-2-044
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B4-2-044/crop-001"},
	// exm-drosophila-flyliconn-matt-260601-60X-B4-2-045
	{name: "exm-drosophila-flyliconn-matt-260601-60X-B4-2-045/crop-001"},
	// exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002
	{name: "exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001"},
	// exm-mouse-liconn-ExPID124
	{name: "exm-mouse-liconn-ExPID124/crop-001"},
	// exm-mouse-liconn-ExPID146
	{name: "exm-mouse-liconn-ExPID146/crop-001"},
	// exm-mouse-liconn-ExPID150
	{name: "exm-mouse-liconn-ExPID150/crop-001"},
	// exm-mouse-liconn-ExPID71-synapse-20260407_GFAP_CnX43_Pan
	{name: "exm-mouse-liconn-ExPID71-synapse-20260407_GFAP_CnX43_Pan/crop-001_40XW001"},
	{name: "exm-mouse-liconn-ExPID71-synapse-20260407_GFAP_CnX43_Pan/crop-002_40XW002"},
	// exm-mouse-liconn-ExPID72-synapse-20260407_RIM12_Homer1_Pan
	{name: "exm-mouse-liconn-ExPID72-synapse-20260407_RIM12_Homer1_Pan/crop-001_40XW008"},
	{name: "exm-mouse-liconn-ExPID72-synapse-20260407_RIM12_Homer1_Pan/crop-002_40XW009"},
	{name: "exm-mouse-liconn-ExPID72-synapse-20260407_RIM12_Homer1_Pan/crop-003_40XW010"},
	// exm-mouse-liconn-ExPID82-1
	{name: "exm-mouse-liconn-ExPID82-1/crop-001_fullvol"},
	{name: "exm-mouse-liconn-ExPID82-1/crop-002_sub"},
	// exm-mouse-liconn-cortex-20250822_ExPID09_2ndGel_30percentSucrose-Glycerol_40XW_003
	{name: "exm-mouse-liconn-cortex-20250822_ExPID09_2ndGel_30percentSucrose-Glycerol_40XW_003/crop-001"},
	// exm-mouse-liconn-hippocampus-202507013_ExPID10-02_2percentAA_S2_Atto488_40XW_004
	{name: "exm-mouse-liconn-hippocampus-202507013_ExPID10-02_2percentAA_S2_Atto488_40XW_004/crop-001"},
	// lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-001_000x_000y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-002_000x_000y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-003_000x_000y_002z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-004_000x_001y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-005_000x_001y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-006_000x_001y_002z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-007_000x_002y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-008_000x_002y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-009_000x_002y_002z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-010_000x_003y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-011_000x_003y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-012_000x_003y_002z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-013_000x_004y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-014_000x_004y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish1_72hpf_roi1/crop-015_000x_004y_002z_96t_2c", zarr_version: "zarr2"},
	// lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-001_000x_000y_000z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-002_000x_000y_001z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-003_000x_000y_002z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-004_000x_001y_000z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-005_000x_001y_001z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-006_000x_001y_002z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-007_000x_002y_000z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-008_000x_002y_001z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-009_000x_002y_002z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-010_000x_003y_000z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-011_000x_003y_001z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-012_000x_003y_002z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-013_000x_004y_000z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-014_000x_004y_001z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-015_000x_004y_002z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-016_000x_005y_000z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-017_000x_005y_001z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-018_000x_005y_002z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-019_000x_006y_000z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-020_000x_006y_001z_288t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20251001_20250324_mem-histone_fish3_24hpf_roi1/crop-021_000x_006y_002z_288t_2c", zarr_version: "zarr2"},
	// lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-001_000x_000y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-002_000x_000y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-003_000x_000y_002z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-004_000x_001y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-005_000x_001y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-006_000x_001y_002z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-007_000x_002y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-008_000x_002y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-009_000x_002y_002z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-010_000x_003y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-011_000x_003y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-012_000x_003y_002z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-013_000x_004y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-014_000x_004y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-015_000x_004y_002z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-016_000x_005y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-017_000x_005y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-018_000x_005y_002z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-019_000x_006y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-020_000x_006y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-021_000x_006y_002z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-022_000x_007y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-023_000x_007y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-024_000x_007y_002z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-025_000x_008y_000z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-026_000x_008y_001z_32t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-027_000x_008y_002z_32t_2c", zarr_version: "zarr2"},
	// lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-001_000x_000y_000z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-002_000x_000y_001z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-003_000x_001y_000z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-004_000x_001y_001z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-005_000x_002y_000z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-006_000x_002y_001z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-007_000x_003y_000z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-008_000x_003y_001z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-009_000x_004y_000z_48t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_ear/crop-010_000x_004y_001z_48t_2c", zarr_version: "zarr2"},
	// lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-001_000x_000y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-002_000x_000y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-003_000x_001y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-004_000x_001y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-005_000x_002y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-006_000x_002y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-007_000x_003y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-008_000x_003y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-009_000x_004y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-010_000x_004y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-011_000x_005y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-012_000x_005y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-013_000x_006y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-014_000x_006y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-015_000x_007y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-016_000x_007y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-017_000x_008y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-018_000x_008y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-019_000x_009y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-020_000x_009y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-021_000x_010y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-022_000x_010y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-023_000x_011y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-024_000x_011y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-025_000x_012y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-026_000x_012y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-027_000x_013y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-028_000x_013y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-029_000x_014y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-030_000x_014y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-031_000x_015y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-032_000x_015y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-033_000x_016y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-034_000x_016y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-035_000x_017y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-036_000x_017y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-037_000x_018y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-038_000x_018y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-039_000x_019y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-040_000x_019y_001z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-041_000x_020y_000z_96t_2c", zarr_version: "zarr2"},
	{name: "lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_72hpf_muscle/crop-042_000x_020y_001z_96t_2c", zarr_version: "zarr2"},
	// lm-zebrafish-Betzig-mosaic-example_annotations_Thayer
	{name: "lm-zebrafish-Betzig-mosaic-example_annotations_Thayer/crop-001_dsr_timeseries_48t_1c"},
	// no "raw" wrapper group -- levels stored directly at the store root
	{name: "lm-zebrafish-Betzig-mosaic-example_annotations_Thayer/crop-002_example_annotations_Thayer_2channels", image_key: ""},
]
