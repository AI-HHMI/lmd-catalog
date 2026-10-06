"""Summarize the LMD catalog (sizes, modalities, organisms, regions, ground truth) into one self-contained HTML report.

Usage: uv sync --extra analysis && python scripts/analysis/report.py   ->  docs/index.html
"""

import math
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import lmd_catalog as lmd
import plots

OUT = Path(__file__).parents[2] / "docs" / "index.html"  # served by GitHub Pages (main branch, /docs)
MODALITY = {"em": "EM", "exm": "Expansion microscopy", "lm": "Light microscopy", "uct": "microCT"}
# First matching pattern wins; matched against the lowercased dataset name.
REGIONS = [
    (r"hippocamp|-dg-", "Hippocampus"),
    (r"cortex|ac3ac4|minnie65|temporal-lobe|pinky", "Cortex"),
    (r"cerebellum", "Cerebellum"),
    (r"nacc|areax", "Striatum / basal ganglia"),
    (r"vnc", "Ventral nerve cord"),
    (r"lobe|fly-mb", "Fly lobes / mushroom body"),
    (r"drosophila", "Fly brain / CNS"),
    (r"liver|kidney|heart|cardiac|bladder|muscle|pancreas|salivary|platelet|ear$", "Non-neural tissue"),
    (r"hela|jurkat|macrophage|sum159|ut21|cos7", "Cell culture"),
    (r"liconn|brain", "Brain (unspecified region)"),
]
CSS = """
body{font:15px system-ui,sans-serif;max-width:1200px;margin:0 auto;padding:16px;color:#222;background:#fff}
h1{margin-bottom:4px} h2{margin-top:36px;border-bottom:1px solid #ddd;padding-bottom:4px}
.tiles{display:flex;flex-wrap:wrap;gap:12px} .tile{border:1px solid #ddd;border-radius:6px;padding:10px 16px}
.tile b{display:block;font-size:24px} .grid{display:flex;flex-wrap:wrap;gap:20px}
.card{flex:1 1 460px;min-width:0} .card svg{max-width:100%;height:auto} h3{margin:8px 0 4px;font-size:15px}
table{border-collapse:collapse;font-size:13px} th,td{padding:3px 10px;border-bottom:1px solid #eee;text-align:left}
td.n,th{text-align:right} th:first-child{text-align:left}
"""


def region_of(dataset: str) -> str:
    for pattern, label in REGIONS:
        if re.search(pattern, dataset.lower()):
            return label
    return "Whole organism / unspecified"


def record(v) -> dict:
    assert v.shape and v.axes, f"{v.name}: catalog entry is missing shape/axes"
    assert v.added, f"{v.name}: catalog entry has no `added` date -- rebuild lmd_volumes.json (scripts/rebuild_volumes.py)"
    sd, vd = v.shape_dict, v.voxelsize_dict
    prefix, organism = v.name.split("-")[:2]
    spatial = [a for a in "xyz" if a in sd]
    return dict(
        name=v.name, dataset=v.dataset, modality=MODALITY[prefix], organism=organism.capitalize(),
        region=region_of(v.dataset), voxels=math.prod(v.shape),
        extent_mm3=math.prod(sd[a] * vd[a] for a in spatial) / 1e18,  # nm^3 -> mm^3
        vox_fine=min(vd[a] for a in spatial), vox_z=vd["z"], channels=sd.get("c", 1), timepoints=sd.get("t", 1),
        added=date.fromisoformat(v.added), gt=v.has_ground_truth, annotated=v.is_annotated, zarr=v.zarr_version, axes="".join(v.axes).upper(),
    )


def group_sum(recs, key, field=None) -> dict:
    out = defaultdict(float)
    for r in recs:
        out[r[key]] += 1 if field is None else r[field]
    return dict(out)


def cumulative(rows, top: int = plots.MAX_SLICES) -> dict:
    """rows: (date, group, weight) -> {group: (dates, running totals)}, the `top` largest groups by final total plus 'Other'.
    Every series is extended to the last date so the lines end together."""
    totals = defaultdict(float)
    for _, g, w in rows:
        totals[g] += w
    keep = {g for g, _ in sorted(totals.items(), key=lambda kv: -kv[1])[:top]}
    end = max(d for d, _, _ in rows)
    series = defaultdict(lambda: ([], []))
    running = defaultdict(float)
    for d, g, w in sorted(rows, key=lambda r: r[0]):
        g = g if g in keep else "Other"
        running[g] += w
        xs, ys = series[g]
        xs.append(d)
        ys.append(running[g])
    for g, (xs, ys) in series.items():
        xs.append(end)
        ys.append(ys[-1])
    return dict(sorted(series.items(), key=lambda kv: -kv[1][1][-1]))


def growth_section(recs, cat) -> tuple:
    """Cumulative growth of the data (by date a volume was added) and of annotation issues (by creation date)."""
    by = lambda key, field=None, scale=1: cumulative([(r["added"], r[key], (1 if field is None else r[field]) / scale) for r in recs])
    anns = cat.annotations()
    assert all(a.created_at for a in anns), "annotation entries have no `created_at` -- rebuild lmd_annotations.json (scripts/rebuild_annotations.py)"
    ann_date = lambda a: date.fromisoformat(a.created_at)
    cards = [
        ("Volumes by organism (cumulative, by date added)", plots.lines(by("organism"), "volumes")),
        ("Volumes by microscopy type (cumulative, by date added)", plots.lines(by("modality"), "volumes")),
        ("Tera-voxels by organism (cumulative, by date added)", plots.lines(by("organism", "voxels", 1e12), "tera-voxels")),
        ("Tera-voxels by microscopy type (cumulative, by date added)", plots.lines(by("modality", "voxels", 1e12), "tera-voxels")),
        ("Volumes with ground truth (cumulative, by date added)", plots.lines(
            cumulative([(r["added"], "All volumes", 1) for r in recs] + [(r["added"], "With ground truth", 1) for r in recs if r["gt"]]), "volumes")),
        ("Annotation issues by status (cumulative, log scale, by creation date)", plots.lines(cumulative([(ann_date(a), a.status or "unset", 1) for a in anns]), "issues", log=True)),
    ]
    labeled = [(ann_date(a), "Labeled objects", a.label_count) for a in anns if a.label_count]
    if labeled:
        cards.append(("Labeled objects (cumulative, by creation date; only issues with a label count)", plots.lines(cumulative(labeled), "labels")))
    return "Growth over time", cards


def card(title: str, content: str) -> str:
    return f"<div class='card'><h3>{title}</h3>{content}</div>"


def summary_table(recs, key: str) -> str:
    groups = defaultdict(list)
    for r in recs:
        groups[r[key]].append(r)
    rows = [
        [k, len(g), len({r["dataset"] for r in g}), sum(r["voxels"] for r in g) / 1e12, sum(r["extent_mm3"] for r in g), sum(r["gt"] for r in g)]
        for k, g in groups.items()
    ]
    rows.sort(key=lambda row: -row[3])
    return plots.table([key.capitalize(), "Volumes", "Datasets", "Tera-voxels", "Extent (mm³)", "With GT"], rows)


def split_section(title: str, recs, key: str) -> tuple:
    """Pie of volume counts, pie of voxel totals, and a summary table."""
    vox = {k: v / 1e12 for k, v in group_sum(recs, key, "voxels").items()}
    return title, [("Volumes", plots.pie(group_sum(recs, key))), ("Tera-voxels", plots.pie(vox)), ("Summary", summary_table(recs, key))]


def annotation_section(cat) -> tuple:
    anns = cat.annotations()
    count = lambda f: Counter(getattr(a, f) or "unset" for a in anns)
    return f"Annotation tracking ({len(anns)} issues)", [
        ("Status", plots.bar(count("status"), "issues")),
        ("Tool", plots.pie(count("tool"))),
        ("Task", plots.pie(count("task"))),
        ("Structure of interest", plots.pie(count("structure_of_interest"))),
        ("Priority", plots.pie(count("priority"))),
        ("Organism", plots.pie(count("model_organism"))),
    ]


def build() -> tuple:
    """Return (tiles, sections): tiles are (number, label); sections are (title, [(card title, svg or table html)])."""
    cat = lmd.default_catalog()
    recs = [record(v) for v in cat]
    tiles = [
        (f"{len(recs):,}", "volumes"), (f"{len(cat.list_datasets()):,}", "datasets"),
        (f"{sum(r['voxels'] for r in recs) / 1e12:,.1f}", "tera-voxels"), (f"{sum(r['extent_mm3'] for r in recs):,.1f}", "mm³ imaged"),
        (f"{sum(r['gt'] for r in recs):,}", "volumes with ground truth"), (f"{sum(r['annotated'] for r in recs):,}", "volumes tracked by an issue"),
    ]
    by_modality = defaultdict(lambda: ([], []))
    for r in recs:
        by_modality[r["modality"]][0].append(math.log10(r["voxels"]))
        by_modality[r["modality"]][1].append(r["vox_fine"])
    ds_vox = defaultdict(float)
    for r in recs:
        ds_vox[r["dataset"]] += r["voxels"] / 1e9
    top = dict(sorted(ds_vox.items(), key=lambda kv: -kv[1])[:15])
    gt_split = Counter("Ground truth" if r["gt"] else "No ground truth" for r in recs)

    sections = [
        split_section("Microscopy type", recs, "modality"),
        split_section("Organism", recs, "organism"),
        split_section("Region / tissue", recs, "region"),
        growth_section(recs, cat),
        ("Sizes", [
            ("Voxels per volume (log10)", plots.hist([math.log10(r["voxels"]) for r in recs], "log10 voxels")),
            ("Finest voxel size (nm)", plots.hist([r["vox_fine"] for r in recs], "nm")),
            ("Voxel size vs. volume size", plots.scatter(by_modality, "log10 voxels", "finest voxel size (nm)")),
            ("Top 15 datasets (giga-voxels)", plots.bar(top, "Gvox")),
        ]),
        ("Image types", [
            ("Axis layout", plots.pie(group_sum(recs, "axes"))),
            ("Channels per volume", plots.pie(Counter(f"{r['channels']} ch" for r in recs))),
            ("Timepoints per volume", plots.pie(Counter(f"{r['timepoints']} t" for r in recs))),
            ("Zarr version", plots.pie(group_sum(recs, "zarr"))),
        ]),
        ("Ground truth", [("Volumes with ingested ground truth", plots.pie(gt_split))]),
        annotation_section(cat),
    ]
    return tiles, sections


def main():
    tiles, sections = build()
    body = (
        "<h1>LMD catalog report</h1><p><a href='slides.html'>View as slides &rarr;</a></p><div class='tiles'>"
        + "".join(f"<div class='tile'><b>{n}</b>{label}</div>" for n, label in tiles) + "</div>"
        + "".join(f"<h2>{title}</h2><div class='grid'>" + "".join(card(t, c) for t, c in cards) + "</div>" for title, cards in sections)
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>LMD catalog report</title><style>{CSS}</style></head><body>{body}</body></html>"
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
