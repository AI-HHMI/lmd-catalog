// Annotation-tracking metadata from the "mia_annotation" GitHub Project
// (https://github.com/orgs/AI-HHMI/projects/1), which tracks the crop-proposal ->
// annotation -> ingestion -> proofreading workflow for a subset of the volumes in
// lmd_volumes.cue. Synced by hand via:
//   gh project item-list 1 --owner AI-HHMI --format json --limit 100
// Re-run and regenerate when the project board changes; there is no automation here.
//
// source_paths usually matches a #Volume.path in lmd_volumes.cue 1:1, but not
// always: a few items track data staged outside data/ (e.g. /nrs scratch space or
// the legacy liconn_data/ layout) that predates or bypasses this catalog entirely.
// Volume.tracked_by (see lmd_volumes.cue) is the live join back the other way.
package lmd

#AnnotationStatus: "Crop Pending Approval" | "Crop Approved" | "On Hold" | "In Annotation" |
	"Screening Queue" | "Initial Screen" | "Fix" | "nth Screen" | "Done" | "GT_Ingested" |
	"pre_paintera_proofreading" | "Proofreading" | "Proofread Screening Queue" |
	"Proofread Initial Screen" | "Proofread Fix" | "Proofread nth Screen" |
	"post_paintera_proofreading" | "Proofread_ingested" | "In Training"

#AnnotationDataset: "Betzig Fish" | "MammalianLICONN" | "MICrONS" | "FlyLICONN"

#AnnotationTool: "Amira" | "Paintera" | "WebKnossos"

#ModelOrganism: "Zebrafish" | "Mouse" | "Drosophila" | "C. elegans" | "Human" | "Danionella"

#DataModality: "Light-sheet (LLSM)" | "Light-sheet (diSPIM)" | "Expansion Microscopy (Spinning Disk)" |
	"Expansion Microscopy (Mirror)" | "ATUM-mSEM" | "FIB-SEM" | "ssTEM (Multibeam SEM)" |
	"IBEAM-mSEM" | "Confocal (CLSM)"

#AnnotationTask: "dense annotation" | "sparse annotation" | "dense proofreading" | "sparse proofreading"

#Structure: "neurons" | "cells" | "mitochondria" | "synapses" | "nuclei"

#Priority: "P1" | "P2" | "P3"

// A region within a volume's finest-level (level-0) raster, in that array's
// own index units -- max exclusive, matching Python slice semantics. Kept
// axis-labeled and order-free rather than a positional list, since bbox (see
// below) has already shown up in more than one axis order by hand -- resolve
// into a specific consumer's expected order (e.g. miao's ZYX bounding_box) at
// read time, don't bake an order in here.
#ROI: {
	x: [int, int]
	y: [int, int]
	z: [int, int]
}

#AnnotationItem: {
	title: string
	issue: {
		number:     int
		url:        string
		repository: string
	}

	status?:                #AnnotationStatus
	dataset?:               #AnnotationDataset
	tool?:                   #AnnotationTool
	task?:                   #AnnotationTask
	model_organism?:         #ModelOrganism
	data_modality?:          #DataModality
	structure_of_interest?:  #Structure
	priority?:               #Priority

	annotator?:      string
	assignees?:      [...string]
	labels?:         [...string]
	completion_pct?: number & >=0 & <=100
	label_count?:    int & >=0
	timepoint?:      string
	last_updated?:   string

	bbox?:      string
	bbox_size?: string
	// Parsed, order-free version of bbox/bbox_size above -- resolve subvolumes
	// through this, not by parsing the free-text fields.
	roi?: #ROI

	// Absolute paths this issue tracks. Usually one; a few items cover more than
	// one crop (e.g. a paired fullvol+sub crop) or a path outside lmd_volumes.cue's
	// data/ root entirely (see file header).
	source_paths: [...string]

	fileglancer_path?:        string
	gt_export_path?:          string
	gt_ingested_path?:        string
	proofread_needed_path?:   string
	proofread_export_path?:   string
	proofread_ingested_path?: string
	wk_link?:                 string
	wk_ann_link?:             string
}

annotations: [...#AnnotationItem] & [
	{
		title: "LICONN_Matt_260601_60X_B4_1_042"
		issue: {number: 25, url: "https://github.com/AI-HHMI/mia_annotation/issues/25", repository: "AI-HHMI/mia_annotation"}
		status: "Crop Approved"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		priority: "P2"
		labels: ["LICONN"]
		timepoint: "N/A"
		last_updated: "2026-08-17"
		bbox: "X:908-1390, Y:910-1392, Z:218-412"
		bbox_size: "sizeX=482, sizeY=482, sizeZ=194 (52x52x58 um)"
		roi: {x: [908, 1390], y: [910, 1392], z: [218, 412]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-matt-260601-60X-B4-1-042/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-matt-260601-60X-B4-1-042"
		wk_link: "https://webknossos.int.janelia.org/datasets/260601_60X_B4_1_042-6a4d1256010000c900d6a042/view#1152,1152,315,0,1.3"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a691a880100006104dfba68#1106,1086,271,0,2.594"
	},
	{
		title: "LICONN_Cortex"
		issue: {number: 8, url: "https://github.com/AI-HHMI/mia_annotation/issues/8", repository: "AI-HHMI/mia_annotation"}
		status: "GT_Ingested"
		dataset: "MammalianLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Mouse"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		structure_of_interest: "neurons"
		annotator: "Tiffany Tran"
		assignees: ["dchen116"]
		labels: ["LICONN", "WebKnossos"]
		completion_pct: 100
		label_count: 303
		timepoint: "N/A"
		last_updated: "2026-08-11"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-cortex-20250822_ExPID09_2ndGel_30percentSucrose-Glycerol_40XW_003/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-mouse-liconn-cortex-20250822_ExPID09_2ndGel_30percentSucrose-Glycerol_40XW_003"
		gt_export_path: "/groups/miaai/miaai/Annotation_LICONN/LICONN_Cortex_20260730"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-cortex-20250822_ExPID09_2ndGel_30percentSucrose-Glycerol_40XW_003/crop-001.zarr/labels/manual_gt-cell-final"
		wk_link: "https://webknossos.org/datasets/69ceb9a2010000d700924908"
		wk_ann_link: "https://webknossos.org/annotations/69d40aae010000ca05940b64"
	},
	{
		title: "LICONN_DG"
		issue: {number: 7, url: "https://github.com/AI-HHMI/mia_annotation/issues/7", repository: "AI-HHMI/mia_annotation"}
		status: "GT_Ingested"
		dataset: "MammalianLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Mouse"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		structure_of_interest: "neurons"
		annotator: "Brie Yarbrough"
		assignees: ["bumblebrie18"]
		labels: ["LICONN", "WebKnossos"]
		completion_pct: 100
		label_count: 146
		timepoint: "N/A"
		last_updated: "2026-07-31"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002"
		gt_export_path: "/groups/miaai/miaai/Annotation_LICONN/LICONN_DG_20260730/DG.zarr/manual_gt_final"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001.zarr/labels/manual_gt-cell-final"
		wk_link: "https://webknossos.org/datasets/69ceb95b0100000606924829"
		wk_ann_link: "https://webknossos.org/annotations/6a1f3ca8010000f6003afe4a"
	},
	{
		title: "Betzig_000x_003y_001z_t31_cell"
		issue: {number: 4, url: "https://github.com/AI-HHMI/mia_annotation/issues/4", repository: "AI-HHMI/mia_annotation"}
		status: "GT_Ingested"
		dataset: "Betzig Fish"
		tool: "Amira"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		annotator: "Diana Ramirez"
		assignees: ["zinni-ad"]
		labels: ["Betzig Fish", "Amira"]
		completion_pct: 100
		label_count: 223
		timepoint: "t=31"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-011_000x_003y_001z_32t_2c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain"
		gt_export_path: "\\\\prfs\\miaai\\paintera_projects\\betzig-fish-mosaic\\fish1_24hpf_roi1_brain\\fish1_24hpf_roi1_brain_000x_003y_001z_t31\\fish1_24hpf_roi1_brain_000x_003y_001z_t31.zarr"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-011_000x_003y_001z_32t_2c.zarr/labels/manual_gt-cell-t31"
	},
	{
		title: "Betzig_000x_003y_001z_t0_cell"
		issue: {number: 3, url: "https://github.com/AI-HHMI/mia_annotation/issues/3", repository: "AI-HHMI/mia_annotation"}
		status: "GT_Ingested"
		dataset: "Betzig Fish"
		tool: "Paintera"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		annotator: "Alannah Post"
		assignees: ["postalannah"]
		labels: ["Betzig Fish", "Paintera"]
		completion_pct: 100
		label_count: 200
		timepoint: "t=0"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-011_000x_003y_001z_32t_2c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain"
		gt_export_path: "\\\\prfs\\miaai\\paintera_projects\\betzig-fish-mosaic\\fish1_24hpf_roi1_brain\\fish1_24hpf_roi1_brain_000x_003y_001z_t0\\fish1_24hpf_roi1_brain_000x_003y_001z_t0.zarr\\cell\\s0"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-011_000x_003y_001z_32t_2c.zarr/labels/manual_gt-cell-t0"
	},
	{
		title: "Betzig_000x_007y_002z_t9_cell"
		issue: {number: 2, url: "https://github.com/AI-HHMI/mia_annotation/issues/2", repository: "AI-HHMI/mia_annotation"}
		status: "GT_Ingested"
		dataset: "Betzig Fish"
		tool: "Paintera"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		annotator: "Alannah Post"
		assignees: ["postalannah"]
		labels: ["Betzig Fish", "Paintera"]
		completion_pct: 100
		label_count: 153
		timepoint: "t=9"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-024_000x_007y_002z_32t_2c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain"
		gt_export_path: "\\\\prfs\\miaai\\annotations\\paintera_exports\\fish1_24hpf_roi1_brain\\000x_007y_002z_t9_filtered.zarr\\s0"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-024_000x_007y_002z_32t_2c.zarr/labels/manual_gt-cell-t9"
	},
	{
		title: "Betzig_000x_007y_002z_t0_cell"
		issue: {number: 1, url: "https://github.com/AI-HHMI/mia_annotation/issues/1", repository: "AI-HHMI/mia_annotation"}
		status: "GT_Ingested"
		dataset: "Betzig Fish"
		tool: "Amira"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		annotator: "Diana Ramirez"
		assignees: ["zinni-ad"]
		labels: ["Betzig Fish", "Amira"]
		completion_pct: 100
		label_count: 236
		timepoint: "t=0"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-024_000x_007y_002z_32t_2c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain"
		gt_export_path: "\\\\prfs\\miaai\\annotations\\amira\\fish1_roi1_brain_000x_007y_002z_t0\\zarr\\cell_instances\\s0"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-024_000x_007y_002z_32t_2c.zarr/labels/manual_gt-cell-t0"
	},
	{
		title: "Betzig_dsr_timeseries_proofread_t10"
		issue: {number: 22, url: "https://github.com/AI-HHMI/mia_annotation/issues/22", repository: "AI-HHMI/mia_annotation"}
		status: "Proofreading"
		dataset: "Betzig Fish"
		tool: "Paintera"
		task: "dense proofreading"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		structure_of_interest: "cells"
		priority: "P1"
		annotator: "Diana Ramirez"
		assignees: ["zinni-ad"]
		labels: ["Betzig Fish", "Amira", "Paintera"]
		timepoint: "t=10"
		last_updated: "2026-07-21"
		bbox: "Y:151-351, X:870-1070, Z:0-152"
		bbox_size: "sizeY=200, sizeX=200, sizeZ=152"
		roi: {x: [870, 1070], y: [151, 351], z: [0, 152]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-example_annotations_Thayer/crop-001_dsr_timeseries_48t_1c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/annotations/betzig-fish-mosaic/example_annotations_Thayer/paintera_proofread"
		gt_export_path: "/groups/miaai/miaai/betzig-fish-mosaic/example_annotations/dsr_annotated.ome.zarr/labels/postprocessed_labels"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/example_annotations_Thayer/dsr_timeseries.zarr/labels/postprocessed_labels_t01"
		proofread_needed_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/example_annotations_Thayer/dsr_timeseries.zarr/labels/cellpose_t10_denseEX_pp"
		proofread_export_path: "/groups/miaai/miaai/annotations/amira/variation_project/Alannah/post_clean.zarr/ap_clean_final/s0, /groups/miaai/miaai/annotations/amira/variation_project/Diana/ramirezd_seg.zarr/dr_prdn_clean_7_15_2026/s0"
		proofread_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/example_annotations_Thayer/dsr_timeseries.zarr/labels/t10_y151x870_variability_alannah, /groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/example_annotations_Thayer/dsr_timeseries.zarr/labels/t10_y151x870_variability_diana"
	},
	{
		title: "Betzig_dsr_timeseries_proofread_t25"
		issue: {number: 23, url: "https://github.com/AI-HHMI/mia_annotation/issues/23", repository: "AI-HHMI/mia_annotation"}
		status: "Proofreading"
		dataset: "Betzig Fish"
		tool: "Paintera"
		task: "dense proofreading"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		structure_of_interest: "cells"
		priority: "P1"
		annotator: "Alannah Post"
		assignees: ["postalannah"]
		labels: ["Paintera"]
		timepoint: "t=25"
		last_updated: "2026-07-21"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-example_annotations_Thayer/crop-001_dsr_timeseries_48t_1c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/annotations/betzig-fish-mosaic/example_annotations_Thayer/paintera_proofread"
		gt_export_path: "/groups/miaai/miaai/betzig-fish-mosaic/example_annotations/dsr_annotated.ome.zarr/labels/postprocessed_labels"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/example_annotations_Thayer/dsr_timeseries.zarr/labels/postprocessed_labels_t01"
		proofread_needed_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/example_annotations_Thayer/dsr_timeseries.zarr/labels/cellpose_t25_denseEX_pp"
	},
	{
		title: "Betzig_dsr_timeseries_proofread_t40"
		issue: {number: 24, url: "https://github.com/AI-HHMI/mia_annotation/issues/24", repository: "AI-HHMI/mia_annotation"}
		status: "pre_paintera_proofreading"
		dataset: "Betzig Fish"
		tool: "Paintera"
		task: "dense proofreading"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		structure_of_interest: "cells"
		priority: "P2"
		annotator: "Diana Ramirez or Alannah Post"
		assignees: ["zinni-ad", "postalannah"]
		timepoint: "t=40"
		last_updated: "2026-07-21"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-example_annotations_Thayer/crop-001_dsr_timeseries_48t_1c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/annotations/betzig-fish-mosaic/example_annotations_Thayer/paintera_proofread"
		gt_export_path: "/groups/miaai/miaai/betzig-fish-mosaic/example_annotations/dsr_annotated.ome.zarr/labels/postprocessed_labels"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/example_annotations_Thayer/dsr_timeseries.zarr/labels/postprocessed_labels_t01"
		proofread_needed_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/example_annotations_Thayer/dsr_timeseries.zarr/labels/cellpose_t40_denseEX_pp"
	},
	{
		title: "Betzig_000x_006y_001z_t0_cell"
		issue: {number: 5, url: "https://github.com/AI-HHMI/mia_annotation/issues/5", repository: "AI-HHMI/mia_annotation"}
		status: "In Annotation"
		dataset: "Betzig Fish"
		tool: "Paintera"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		annotator: "Diana Ramirez"
		assignees: ["zinni-ad"]
		labels: ["Betzig Fish", "Amira"]
		completion_pct: 80
		label_count: 195
		timepoint: "t=0"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-020_000x_006y_001z_32t_2c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/2026/2/13/Korra_Foundation/20250616_mem-histone/fish1_24hpf_roi1_brain/000x_006y_001z.zarr/labels/cell_t0"
	},
	{
		title: "Betzig_000x_006y_001z_t16_cell"
		issue: {number: 6, url: "https://github.com/AI-HHMI/mia_annotation/issues/6", repository: "AI-HHMI/mia_annotation"}
		status: "In Annotation"
		dataset: "Betzig Fish"
		tool: "Paintera"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		annotator: "Alannah Post"
		assignees: ["postalannah"]
		labels: ["Betzig Fish", "Paintera"]
		completion_pct: 80
		label_count: 167
		timepoint: "t=16"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-020_000x_006y_001z_32t_2c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/betzig-fish-mosaic/2026/2/13/Korra_Foundation/20250616_mem-histone/fish1_24hpf_roi1_brain/000x_006y_001z.zarr/labels/cell_t16"
	},
	{
		title: "LICONN_Hippocampus"
		issue: {number: 9, url: "https://github.com/AI-HHMI/mia_annotation/issues/9", repository: "AI-HHMI/mia_annotation"}
		status: "GT_Ingested"
		dataset: "MammalianLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Mouse"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		structure_of_interest: "neurons"
		annotator: "Cat Mori"
		assignees: ["moric7"]
		labels: ["LICONN", "WebKnossos"]
		completion_pct: 100
		label_count: 285
		timepoint: "N/A"
		last_updated: "2026-07-31"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-hippocampus-202507013_ExPID10-02_2percentAA_S2_Atto488_40XW_004/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-mouse-liconn-hippocampus-202507013_ExPID10-02_2percentAA_S2_Atto488_40XW_004"
		gt_export_path: "/groups/miaai/miaai/Annotation_LICONN/LICONN_Hippocampus_20260730/"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-hippocampus-202507013_ExPID10-02_2percentAA_S2_Atto488_40XW_004/crop-001.zarr/labels/manual_gt-cell-final"
		wk_link: "https://webknossos.org/datasets/69ceb80301000041019244b3"
		wk_ann_link: "https://webknossos.org/annotations/69d42d10010000a424941998"
	},
	{
		title: "LICONN_ExPID82-1_crop"
		issue: {number: 12, url: "https://github.com/AI-HHMI/mia_annotation/issues/12", repository: "AI-HHMI/mia_annotation"}
		status: "Crop Pending Approval"
		dataset: "MammalianLICONN"
		task: "dense proofreading"
		model_organism: "Mouse"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		assignees: ["knechtc"]
		labels: ["LICONN"]
		timepoint: "N/A"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-ExPID82-1/crop-001_fullvol.zarr", "/groups/miaai/miaai/lmd-v0.0.1/data/exm-mouse-liconn-ExPID82-1/crop-002_sub.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-mouse-liconn-ExPID82-1"
		wk_link: "https://webknossos.int.janelia.org/datasets/ExPID82-1_wk.zarr-6a441916010000d100d69dd0"
	},
	{
		title: "MICrONS_minnie65_crop"
		issue: {number: 13, url: "https://github.com/AI-HHMI/mia_annotation/issues/13", repository: "AI-HHMI/mia_annotation"}
		status: "Crop Pending Approval"
		dataset: "MICrONS"
		task: "dense proofreading"
		model_organism: "Mouse"
		data_modality: "ssTEM (Multibeam SEM)"
		assignees: ["knechtc"]
		labels: ["MICrONS"]
		timepoint: "N/A"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/em-mouse-MICrONS-minnie65/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/em-mouse-MICrONS-minnie65"
		wk_link: "https://webknossos.org/datasets/microns-minnie65-6a32d0b30100008713635c75/view#5228,3993,259,0,5.43"
	},
	{
		title: "Betzig_000x_003y_001z_t0_densebox2"
		issue: {number: 15, url: "https://github.com/AI-HHMI/mia_annotation/issues/15", repository: "AI-HHMI/mia_annotation"}
		status: "In Annotation"
		dataset: "Betzig Fish"
		tool: "Amira"
		task: "dense annotation"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		structure_of_interest: "cells"
		annotator: "TBD"
		assignees: ["postalannah"]
		labels: ["Betzig Fish", "Amira"]
		timepoint: "t=0"
		last_updated: "2026-08-17"
		bbox: "X:0-128, Y:0-384, Z:1400-2000"
		bbox_size: "sizeX=128, sizeY=384, sizeZ=600 (12.5x37.6x210 um)"
		roi: {x: [0, 128], y: [0, 384], z: [1400, 2000]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-011_000x_003y_001z_32t_2c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain"
		wk_link: "https://webknossos.int.janelia.org/datasets/betzig_fish1_24hpf_roi1_brain_000x_003y_001z.zarr-6a3449f3010000cb00fee380/view#64,192,1664,0,1.3,pos-t=0"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a344b54010000c900fee383#64,192,1700,0,2,pos-t=0"
	},
	{
		title: "Betzig_000x_003y_001z_t0_densebox1"
		issue: {number: 14, url: "https://github.com/AI-HHMI/mia_annotation/issues/14", repository: "AI-HHMI/mia_annotation"}
		status: "In Annotation"
		dataset: "Betzig Fish"
		tool: "Amira"
		task: "dense annotation"
		model_organism: "Zebrafish"
		data_modality: "Light-sheet (LLSM)"
		structure_of_interest: "cells"
		annotator: "TBD"
		assignees: ["zinni-ad"]
		labels: ["Betzig Fish", "Amira"]
		timepoint: "t=0"
		last_updated: "2026-08-17"
		bbox: "X:0-128, Y:0-384, Z:700-1300"
		bbox_size: "sizeX=128, sizeY=384, sizeZ=600 (12.5x37.6x210 um)"
		roi: {x: [0, 128], y: [0, 384], z: [700, 1300]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain/crop-011_000x_003y_001z_32t_2c.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/lm-zebrafish-Betzig-mosaic-20260213_Korra_Foundation_20250616_mem-histone_fish1_24hpf_brain"
		wk_link: "https://webknossos.int.janelia.org/datasets/betzig_fish1_24hpf_roi1_brain_000x_003y_001z.zarr-6a3449f3010000cb00fee380/view#64,192,1664,0,1.3,pos-t=0"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a344b54010000c900fee383#64,192,1700,0,2,pos-t=0"
	},
	{
		title: "LICONN_Matt_260601_60X_B4_1_040"
		issue: {number: 10, url: "https://github.com/AI-HHMI/mia_annotation/issues/10", repository: "AI-HHMI/mia_annotation"}
		status: "On Hold"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		priority: "P2"
		annotator: "Brie"
		assignees: ["bumblebrie18"]
		labels: ["LICONN"]
		timepoint: "N/A"
		last_updated: "2026-08-17"
		bbox: "X:931-1413, Y:900-1382, Z:171-365"
		bbox_size: "sizeX=482, sizeY=482, sizeZ=194 (52x52x58 um)"
		roi: {x: [931, 1413], y: [900, 1382], z: [171, 365]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-matt-260601-60X-B4-1-040/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-matt-260601-60X-B4-1-040"
		wk_link: "https://webknossos.int.janelia.org/datasets/260601_60X_B4_1_040.zarr-6a2c5cdb010000cd00fee192/view"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a3007c1010000fd05fee235#1439,1148,215,0,2.303"
	},
	{
		title: "LICONN_Matt_260601_60X_B2_1_028"
		issue: {number: 11, url: "https://github.com/AI-HHMI/mia_annotation/issues/11", repository: "AI-HHMI/mia_annotation"}
		status: "On Hold"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		assignees: ["PostPreAndCleft", "CarlaRodriguez96"]
		labels: ["LICONN"]
		timepoint: "N/A"
		last_updated: "2026-08-17"
		bbox: "X:1323-1805, Y:796-1278, Z:137-331"
		bbox_size: "sizeX=482, sizeY=482, sizeZ=194 (52x52x58 um)"
		roi: {x: [1323, 1805], y: [796, 1278], z: [137, 331]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-matt-260601-60X-B2-1-028/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-matt-260601-60X-B2-1-028"
		wk_link: "https://webknossos.int.janelia.org/datasets/260601_60X_B2_1_028.zarr-6a2c5c86010000df00fee18d/view"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a3004b9010000fc05fee225#1680,1153,267,0,3.797"
	},
	{
		title: "LICONN_Matt_260601_60X_B4_1_041"
		issue: {number: 16, url: "https://github.com/AI-HHMI/mia_annotation/issues/16", repository: "AI-HHMI/mia_annotation"}
		status: "On Hold"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		annotator: "TBD"
		assignees: ["jakobtroidl", "CarlaRodriguez96"]
		labels: ["LICONN"]
		timepoint: "N/A"
		last_updated: "2026-08-17"
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-matt-260601-60X-B4-1-041/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-matt-260601-60X-B4-1-041"
		wk_link: "https://webknossos.int.janelia.org/datasets/260601_60X_B4_1_041-6a39516b010000bc00fee3ec/view"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a39648c010000c600fee3f0#1172,1134,378,0,1.1,13"
	},
	{
		title: "FlyLICONN_FlyID49_40XW005"
		issue: {number: 18, url: "https://github.com/AI-HHMI/mia_annotation/issues/18", repository: "AI-HHMI/mia_annotation"}
		status: "In Annotation"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		priority: "P1"
		annotator: "Cat Mori"
		assignees: ["moric7"]
		labels: ["LICONN"]
		last_updated: "2026-06-29"
		bbox: "X:911-1393, Y:911-1393, Z:429-623"
		bbox_size: "sizeX=482, sizeY=482, sizeZ=194 (78.6x78.6x77.6 um)"
		roi: {x: [911, 1393], y: [911, 1393], z: [429, 623]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW005-20260625/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW005-20260625/crop-001.zarr"
		wk_link: "https://webknossos.int.janelia.org/dashboard/datasets/FlyID49-6a3d5476010000ad00d69bb0"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a427ec0010000cc00d69ca5#1152,1152,526,0,1.3"
	},
	{
		title: "FlyLICONN_FlyID49_40XW006"
		issue: {number: 19, url: "https://github.com/AI-HHMI/mia_annotation/issues/19", repository: "AI-HHMI/mia_annotation"}
		status: "In Annotation"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		priority: "P1"
		annotator: "Tiffany Tran"
		assignees: ["trant16"]
		labels: ["LICONN"]
		last_updated: "2026-06-29"
		bbox: "X:900-1382, Y:900-1382, Z:462-656"
		bbox_size: "sizeX=482, sizeY=482, sizeZ=194 (78.6x78.6x77.6 um)"
		roi: {x: [900, 1382], y: [900, 1382], z: [462, 656]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW006-20260625/crop-001.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-DUP-BIS-40XW006-20260625/crop-001.zarr"
		wk_link: "https://webknossos.int.janelia.org/dashboard/datasets/FlyID49-6a3d5476010000ad00d69bb0"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a428144010000c900d69cb1#1141,1141,559,0,1.43"
	},
	{
		title: "FlyLICONN_FlyID49_MirrorScope_central"
		issue: {number: 27, url: "https://github.com/AI-HHMI/mia_annotation/issues/27", repository: "AI-HHMI/mia_annotation"}
		status: "In Annotation"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Mirror)"
		structure_of_interest: "neurons"
		priority: "P1"
		assignees: ["bumblebrie18"]
		labels: ["LICONN"]
		bbox: "13720, 16025, 3570"
		bbox_size: "482, 482, 194"
		roi: {x: [13720, 14202], y: [16025, 16507], z: [3570, 3764]}
		source_paths: ["/nrs/liconn/data_internal/20260702_flyID49_Moe/central_crop/fused.ome.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-mirrorscope-central-20260702/crop-001_central.zarr"
		wk_link: "https://webknossos.int.janelia.org/datasets/exm-drosophila-flyliconn-FlyID49-mirrorscope-central-20260702-6a83647e010000aa00dfc147/view"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a8364d60100005104dfc14a"
	},
	{
		title: "LICONN Mitochondria"
		issue: {number: 21, url: "https://github.com/AI-HHMI/mia_annotation/issues/21", repository: "AI-HHMI/mia_annotation"}
		status: "GT_Ingested"
		dataset: "FlyLICONN"
		tool: "Amira"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		structure_of_interest: "mitochondria"
		annotator: "Grace Park, Alannah Post"
		timepoint: "N/A"
		last_updated: "2026-07-22"
		source_paths: ["/nrs/tavakoli/A46-PTR202604lic-MT-MW-organelle-annotations/zarr/20260216_FlyID25_MOPS_2ndGel_B1_40XW003.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID25-mitochondria-20260216_MOPS_2ndGel_B1_40XW003"
		gt_export_path: "/nrs/tavakoli/A46-PTR202604lic-MT-MW-organelle-annotations/annotation/crop001/crop001_combined.zarr"
		gt_ingested_path: "/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID25-mitochondria-20260216_MOPS_2ndGel_B1_40XW003/crop-001.zarr/labels/manual_gt-mitochondria-crop001"
	},
	{
		title: "FlyLICONN_FlyID49_40XW002"
		issue: {number: 26, url: "https://github.com/AI-HHMI/mia_annotation/issues/26", repository: "AI-HHMI/mia_annotation"}
		status: "Crop Approved"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Spinning Disk)"
		priority: "P2"
		labels: ["LICONN"]
		bbox: "X:911-1393, Y:911-1393, Z:118-312"
		bbox_size: "sizeX=482, sizeY=482, sizeZ=194 (78.3x78.3x77.6 um)"
		roi: {x: [911, 1393], y: [911, 1393], z: [118, 312]}
		source_paths: ["/groups/miaai/miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-BIS-40XW002-20260625/crop-001_fullvol.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-2ndgel-BIS-40XW002-20260625/crop-001_fullvol.zarr"
		wk_link: "https://webknossos.int.janelia.org/datasets/exm-drosophila-flyliconn-FlyID49-2ndgel-BIS-40XW002-20260625-6a7f69630100006204dfc009/view"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a7f6980010000b200dfc00a#1170,1218,123,0,5.56"
	},
	{
		title: "FlyLICONN_FlyID49_MirrorScope_lobe"
		issue: {number: 28, url: "https://github.com/AI-HHMI/mia_annotation/issues/28", repository: "AI-HHMI/mia_annotation"}
		status: "Crop Approved"
		dataset: "FlyLICONN"
		tool: "WebKnossos"
		task: "dense annotation"
		model_organism: "Drosophila"
		data_modality: "Expansion Microscopy (Mirror)"
		priority: "P2"
		labels: ["LICONN"]
		bbox: "41567, 36040, 3865"
		bbox_size: "482, 482, 194"
		roi: {x: [41567, 42049], y: [36040, 36522], z: [3865, 4059]}
		source_paths: ["/nrs/liconn/data_internal/20260702_flyID49_Moe/lobe/fused.ome.zarr"]
		fileglancer_path: "https://fileglancer.int.janelia.org/browse/groups_miaai_miaai/lmd-v0.0.1/data/exm-drosophila-flyliconn-FlyID49-mirrorscope-lobe-20260702/crop-001_lobe.zarr"
		wk_link: "https://webknossos.int.janelia.org/datasets/exm-drosophila-flyliconn-FlyID49-mirrorscope-lobe-20260702-6a8364210100005c04dfc144/view"
		wk_ann_link: "https://webknossos.int.janelia.org/annotations/6a83658c0100005704dfc153"
	},
]
