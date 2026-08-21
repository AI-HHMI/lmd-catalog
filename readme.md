- cfg: pull in mia_annotation GitHub Project (AI-HHMI/projects/1) tracking metadata --
26 annotation-tracking issues (crop proposal -> annotation -> ingestion -> proofreading),
joined live against #Volume via source_paths -> path (list.Contains)

- cfg: CUE catalog of every .zarr volume in /groups/miaai/miaai/lmd-v0.0.1/data (417
volumes, 69 datasets) -- name/path/image_key/zarr_version, path derived from name,
discovered by walking data/ directly (independent of any pretraining config's curation)

# The Design Problem

OK, let's forget about CUE for a second. What are standard practices and tools
around data versioning for systems like ours. We have a few hundred large zarr
volumes and continually update them with medium sized but highly compressible
label annotations over time and frequently update the lightweight metadata like
voxel size, etc. Occasionally we may want to migrate the data e.g. zarr2 ->
zarr3 or create and store downsampled versions of raw images and labels. We need
to reference this data from many different projects for training neural nets and
making predictions, but those predictions are changing frequently as we iterate
on models.


List of things we want:

0. No change for zarr writers.
1. Consumers don't have data move out from under them.
2. We can add new zarrs, new metadata, new keys/labels.
3. We can fix and update metadata.
4. We can fix and update labels.
5. We can specify subvolumes of zarrs specifically used for train/test.

Systems:

a. 
