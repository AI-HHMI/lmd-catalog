- cfg: pull in mia_annotation GitHub Project (AI-HHMI/projects/1) tracking metadata --
26 annotation-tracking issues (crop proposal -> annotation -> ingestion -> proofreading),
joined live against #Volume via source_paths -> path (list.Contains)

- cfg: CUE catalog of every .zarr volume in /groups/miaai/miaai/lmd-v0.0.1/data (417
volumes, 69 datasets) -- name/path/image_key/zarr_version, path derived from name,
discovered by walking data/ directly (independent of any pretraining config's curation)
