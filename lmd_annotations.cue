// Annotation-tracking metadata schema, from the "mia_annotation" GitHub Project
// (https://github.com/orgs/AI-HHMI/projects/1), which tracks the crop-proposal ->
// annotation -> ingestion -> proofreading workflow for a subset of the volumes in
// lmd_volumes.cue.
//
// Data lives in the sibling lmd_annotations.json (26 annotation-tracking issues
// as of the last sync), not here -- this file is schema only. Regenerate the
// data with scripts/rebuild_annotations.py, never hand-edit lmd_annotations.json,
// except for `roi`, which is derived from bbox/bbox_size by that same script and
// not itself a GitHub Project field.
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

annotations: [...#AnnotationItem]
