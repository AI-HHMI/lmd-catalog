"""Summarize the LMD catalog (sizes, modalities, organisms, regions, ground truth) into one self-contained HTML report.

Usage: uv sync --extra analysis && python scripts/analysis/report.py   ->  docs/index.html
"""

import math
import re
import statistics
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
# Annotation statuses of the bulk-ingested issues, which don't record tool/task/structure/priority.
BULK_STATUSES = {"manual_gt_ingested", "public_gt_ingested", "proofread_ingested", "auto_pred_ingested"}
# Pipeline order for the mia_pretraining status funnel.
STATUS_ORDER = ["Pending Ingestion", "Training Bbox TBD", "Waiting", "Consider for Training", "Approved for Training", "In Training", "Model Development Only", "On Hold", "Discarded"]
SIZE_RE = re.compile(r"([\d.,]+)\s*(PB|TB|GB|MB|KB|P|T|G|M)\b", re.I)
UNIT_GB = {"KB": 1e-6, "MB": 1e-3, "GB": 1.0, "TB": 1e3, "PB": 1e6, "M": 1e-3, "G": 1.0, "T": 1e3, "P": 1e6}
CSS = """
body{font:15px system-ui,sans-serif;max-width:1200px;margin:0 auto;padding:16px;color:#222;background:#fff}
h1{margin-bottom:4px} h2{margin-top:36px;border-bottom:1px solid #ddd;padding-bottom:4px}
.tiles{display:flex;flex-wrap:wrap;gap:12px} .tile{border:1px solid #ddd;border-radius:6px;padding:10px 16px}
.tile b{display:block;font-size:24px} .grid{display:flex;flex-wrap:wrap;gap:20px}
.card{flex:1 1 460px;min-width:0} .card.wide{flex-basis:100%} .card svg{max-width:100%;height:auto} h3{margin:8px 0 4px;font-size:15px}
table{border-collapse:collapse;font-size:13px} th,td{padding:3px 10px;border-bottom:1px solid #eee;text-align:left}
td.n,th{text-align:right} th:first-child{text-align:left}
h1,h2{scroll-margin-top:16px} nav.toc{display:none}
@media (min-width:1100px){
  body{max-width:none}
  .layout{display:grid;grid-template-columns:230px minmax(0,1200px);gap:32px;max-width:1500px;margin:0 auto}
  nav.toc{display:block;position:sticky;top:16px;align-self:start;max-height:calc(100vh - 32px);overflow:auto;font-size:14px}
  nav.toc b{display:block;margin:0 0 8px 12px;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#888}
  nav.toc a{display:block;padding:5px 10px 5px 12px;color:#555;text-decoration:none;border-left:2px solid #eee}
  nav.toc a:hover{color:#222;border-left-color:#bbb} nav.toc a.on{color:#0072B2;border-left-color:#0072B2;font-weight:600}
}
"""
# Highlights the section being read in the side panel (only visible on wide screens).
TOC_JS = """
const links = [...document.querySelectorAll('nav.toc a')];
const targets = links.map(a => document.querySelector(a.getAttribute('href')));
function mark() {
  let cur = 0;
  targets.forEach((t, i) => { if (t.getBoundingClientRect().top <= 120) cur = i; });
  links.forEach((a, i) => a.classList.toggle('on', i === cur));
}
addEventListener('scroll', mark, {passive: true});
mark();
"""


def region_of(dataset: str) -> str:
    for pattern, label in REGIONS:
        if re.search(pattern, dataset.lower()):
            return label
    return "Whole organism / unspecified"


# Label arrays (a volume's labels/ group) by what they are, from the key's prefix; anything else is a pipeline output.
KIND_NAMES = {"manual_gt": "Manual ground truth", "proofread": "Proofread", "public_gt": "Public ground truth", "auto_pred": "Auto-prediction", "other": "Other (pipeline outputs)"}


def label_kind(key: str) -> str:
    return next((k for k in KIND_NAMES if k != "other" and key.startswith(k)), "other")


def subtype_of(v) -> str:
    """The project's finer microscopy label for a volume: from the records naming its store, else from those naming
    its dataset; the most common label if they disagree; 'unspecified' if there is none."""
    labels = [p.data_modality for p in v.pretraining if p.data_modality] or [p.data_modality for p in v.dataset_pretraining if p.data_modality]
    return Counter(labels).most_common(1)[0][0] if labels else "unspecified"


def record(v) -> dict:
    assert v.shape and v.axes, f"{v.name}: catalog entry is missing shape/axes"
    assert v.added, f"{v.name}: catalog entry has no `added` date -- rebuild lmd_volumes.json (scripts/rebuild_volumes.py)"
    sd, vd = v.shape_dict, v.voxelsize_dict
    prefix, organism = v.name.split("-")[:2]
    spatial = [a for a in "xyz" if a in sd]
    return dict(
        name=v.name, dataset=v.dataset, modality=MODALITY[prefix], organism=organism.capitalize(),
        region=region_of(v.dataset), subtype=subtype_of(v), labels=Counter(label_kind(k) for k in v.label_keys), voxels=math.prod(v.shape),
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
    wide = " wide" if content.startswith("<table") else ""  # tables get a row of their own
    return f"<div class='card{wide}'><h3>{title}</h3>{content}</div>"


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


def size_gb(text) -> float | None:
    """The first size quoted in a free-text disk_size ("118 GB", "~435 GB (22 volumes)", "132M"), in GB; None if none."""
    m = SIZE_RE.search(text or "")
    return float(m.group(1).replace(",", "")) * UNIT_GB[m.group(2).upper()] if m else None


def project_datasets(cat) -> list:
    """The dataset-level mia_pretraining records (the ones that are not also a tracked annotation issue)."""
    annotated = {(a.issue.repository, a.issue.number) for a in cat.annotations() if a.pretraining}
    return [p for p in cat.pretraining() if (p.issue.repository, p.issue.number) not in annotated]


def project_section(cat) -> tuple:
    """Charts of the mia_pretraining dataset records. Sizes are approximate: the first size quoted per record."""
    recs = project_datasets(cat)
    sized = [(p, size_gb(p.disk_size)) for p in recs if size_gb(p.disk_size)]
    totals = lambda key: {k: sum(g for p, g in sized if key(p) == k) / 1e3 for k in {key(p) for p, _ in sized}}
    count = lambda f: Counter(getattr(p, f) or "unset" for p in recs)
    labs = defaultdict(lambda: [0, 0.0])
    for p, g in sized:
        lab = p.source_lab or "unset"
        labs[lab][0] += 1
        labs[lab][1] += g / 1e3
    lab_rows = [[lab, n, tb] for lab, (n, tb) in sorted(labs.items(), key=lambda kv: -kv[1][1])[:12]]
    top = {p.title[:42]: g / 1e3 for p, g in sorted(sized, key=lambda pg: -pg[1])[:15]}
    status = {s: n for s, n in sorted(count("status").items(), key=lambda kv: STATUS_ORDER.index(kv[0]) if kv[0] in STATUS_ORDER else 99)}
    note = f"approx. TB, first size quoted in {len(sized)} of {len(recs)} records"
    return f"Project datasets ({len(recs)} mia_pretraining records)", [
        ("Pipeline status", plots.bar(status, "datasets")),
        ("Source type", plots.pie(count("source_type"))),
        ("Microscopy type (project labels)", plots.pie(count("data_modality"))),
        (f"Data on disk by organism ({note})", plots.bar(totals(lambda p: p.organism or "unset"), "TB")),
        (f"Data on disk by microscopy type ({note})", plots.bar(totals(lambda p: p.data_modality or "unset"), "TB")),
        ("Largest datasets (approx. TB)", plots.bar(top, "TB")),
        ("Source labs by data on disk", plots.table(["Source lab", "Datasets", "Approx. TB"], lab_rows)),
        ("Array dtype", plots.pie(count("dtype"))),
        ("Zarr format", plots.pie(count("zarr_format"))),
        ("Compression", plots.pie(count("compression"))),
    ]


def subtype_rows(recs) -> list:
    """One row per (category, subtype), categories in MODALITY order and subtypes by volume count."""
    groups = defaultdict(list)
    for r in recs:
        groups[(r["modality"], r["subtype"])].append(r)
    order = list(MODALITY.values())
    return sorted(groups.items(), key=lambda kv: (order.index(kv[0][0]), -len(kv[1])))


def detail_table(rows) -> str:
    def organisms(g):
        counts = Counter(r["organism"] for r in g).most_common(3)
        return ", ".join(f"{o} {100 * n / len(g):.0f}%" for o, n in counts)

    return plots.table(
        ["Subtype", "Volumes", "Datasets", "Tera-voxels", "Median voxel (nm)", "With GT", "Main organisms"],
        [[sub, len(g), len({r["dataset"] for r in g}), sum(r["voxels"] for r in g) / 1e12, statistics.median(r["vox_fine"] for r in g), sum(r["gt"] for r in g), organisms(g)]
         for (_, sub), g in rows],
    )


def detail_section(recs) -> tuple:
    """Each of the four categories broken into the project's finer microscopy labels."""
    rows = subtype_rows(recs)
    vol = [(sub, len(g), cat) for (cat, sub), g in rows]
    tvox = [(sub, sum(r["voxels"] for r in g) / 1e12, cat) for (cat, sub), g in rows]
    wide = {sub: [r["vox_fine"] for r in g] for (cat, sub), g in rows if len(g) >= 3}
    cards = [
        ("Volumes by microscopy subtype", plots.group_bar(vol, "volumes")),
        ("Tera-voxels by microscopy subtype", plots.group_bar(tvox, "tera-voxels")),
        ("Finest voxel size by subtype (nm, subtypes with 3+ volumes)", plots.box(wide, "nm")),
    ]
    for cat in MODALITY.values():
        cards.append((f"{cat}: subtypes in detail", detail_table([row for row in rows if row[0][0] == cat])))
    return "Microscopy types in detail (project labels)", cards


def label_section(recs) -> tuple:
    """The label arrays stored in the volumes, by what they are and by microscopy subtype."""
    rows = subtype_rows(recs)
    stacks = [(sub, cat, {KIND_NAMES[k]: n for k, n in sum((r["labels"] for r in g), Counter()).items()}) for (cat, sub), g in rows]
    coverage = [(f"{sub} ({sum(1 for r in g if r['labels'])}/{len(g)})", 100 * sum(1 for r in g if r["labels"]) / len(g), cat) for (cat, sub), g in rows]
    total = sum(sum(r["labels"].values()) for r in recs)
    return "Label annotations by microscopy type", [
        (f"Label arrays by kind and microscopy subtype ({total:,} arrays)", plots.stacked_bar(stacks, list(KIND_NAMES.values()), "label arrays")),
        ("Volumes with at least one label array (labelled/total)", plots.group_bar(coverage, "% of volumes")),
    ]


def annotation_section(cat) -> tuple:
    anns = cat.annotations()
    hand = [a for a in anns if a.status not in BULK_STATUSES]
    count = lambda rows, f: Counter(getattr(a, f) or "unset" for a in rows)
    note = f"{len(hand)} hand-tracked issues; the {len(anns) - len(hand)} bulk-ingested ones don't record this"
    return f"Annotation tracking ({len(anns)} issues)", [
        ("Status (all issues)", plots.bar(count(anns, "status"), "issues")),
        ("Organism (all issues)", plots.pie(count(anns, "model_organism"))),
        (f"Tool ({note})", plots.pie(count(hand, "tool"))),
        (f"Task ({note})", plots.pie(count(hand, "task"))),
        (f"Structure of interest ({note})", plots.pie(count(hand, "structure_of_interest"))),
        (f"Priority ({note})", plots.pie(count(hand, "priority"))),
    ]


def build() -> tuple:
    """Return (tiles, sections): tiles are (number, label); sections are (title, [(card title, svg or table html)])."""
    cat = lmd.default_catalog()
    recs = [record(v) for v in cat]
    tiles = [
        (f"{len(recs):,}", "volumes"), (f"{len(cat.list_datasets()):,}", "datasets"),
        (f"{sum(r['voxels'] for r in recs) / 1e12:,.1f}", "tera-voxels"), (f"{sum(r['extent_mm3'] for r in recs):,.1f}", "mm³ imaged"),
        (f"{sum(r['gt'] for r in recs):,}", "volumes with ground truth"), (f"{sum(r['annotated'] for r in recs):,}", "volumes tracked by an issue"),
        (f"{len(project_datasets(cat)):,}", "project datasets"),
        (f"{sum(size_gb(p.disk_size) or 0 for p in project_datasets(cat)) / 1e3:,.0f}", "TB on disk (project estimate)"),
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
        detail_section(recs),
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
        label_section(recs),
        project_section(cat),
        annotation_section(cat),
    ]
    return tiles, sections


def short_title(title: str) -> str:
    """The title without its parenthetical, which holds live counts ("Annotation tracking (1124 issues)")."""
    return title.split(" (")[0]


def anchor(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", short_title(title).lower()).strip("-")


def main():
    tiles, sections = build()
    toc = [("overview", "Overview")] + [(anchor(title), short_title(title)) for title, _ in sections]
    nav = "<nav class='toc'><b>Contents</b>" + "".join(f"<a href='#{a}'>{t}</a>" for a, t in toc) + "</nav>"
    main_html = (
        "<main><h1 id='overview'>LMD catalog report</h1><p><a href='slides.html'>View as slides &rarr;</a></p><div class='tiles'>"
        + "".join(f"<div class='tile'><b>{n}</b>{label}</div>" for n, label in tiles) + "</div>"
        + "".join(f"<h2 id='{anchor(title)}'>{title}</h2><div class='grid'>" + "".join(card(t, c) for t, c in cards) + "</div>" for title, cards in sections)
        + "</main>"
    )
    body = f"<div class='layout'>{nav}{main_html}</div><script>{TOC_JS}</script>"
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>LMD catalog report</title><style>{CSS}</style></head><body>{body}</body></html>"
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
