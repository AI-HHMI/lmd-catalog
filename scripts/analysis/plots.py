"""Small matplotlib/HTML helpers: each chart returns an inline SVG string, each table an HTML string."""

import html
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Okabe-Ito colorblind-safe palette; grey is reserved for "Other".
COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
GREY = "#999999"
MAX_SLICES = 8

plt.rcParams.update({"svg.fonttype": "none", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def to_svg(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    svg = buf.getvalue()
    return svg[svg.index("<svg"):]


def top_n(counts: dict, n: int = MAX_SLICES) -> dict:
    """Keep the n largest entries and fold the rest into 'Other'."""
    items = sorted(counts.items(), key=lambda kv: -kv[1])
    out = dict(items[:n])
    rest = sum(v for _, v in items[n:])
    if rest:
        out["Other"] = rest
    return out


def pie(counts: dict) -> str:
    counts = top_n(counts)
    colors = [GREY if k == "Other" else COLORS[i] for i, k in enumerate(counts)]
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    ax.pie(list(counts.values()), colors=colors, startangle=90, counterclock=False,
           autopct=lambda p: f"{p:.0f}%" if p >= 5 else "", pctdistance=0.78, wedgeprops={"linewidth": 1, "edgecolor": "white"})
    ax.legend([f"{k} ({v:,.0f})" if float(v).is_integer() else f"{k} ({v:.3g})" for k, v in counts.items()],
              loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
    return to_svg(fig)


def bar(counts: dict, xlabel: str, log: bool = False) -> str:
    """Horizontal bars, largest on top."""
    items = sorted(counts.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(5.5, 0.3 * len(items) + 0.8))
    ax.barh([k for k, _ in items], [v for _, v in items], color=COLORS[0])
    ax.set_xlabel(xlabel)
    if log:
        ax.set_xscale("log")
    return to_svg(fig)


def hist(values, xlabel: str, bins: int = 30) -> str:
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.hist(values, bins=bins, color=COLORS[0], edgecolor="white")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("volumes")
    return to_svg(fig)


def scatter(groups: dict, xlabel: str, ylabel: str) -> str:
    """groups: label -> (xs, ys)."""
    fig, ax = plt.subplots(figsize=(5.5, 3.6))
    for (label, (xs, ys)), c in zip(groups.items(), COLORS):
        ax.scatter(xs, ys, s=14, alpha=0.6, color=c, label=label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    return to_svg(fig)


def lines(series: dict, ylabel: str, log: bool = False) -> str:
    """Step lines over time. series: label -> (dates, values)."""
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    for (label, (xs, ys)), c in zip(series.items(), COLORS):
        ax.step(xs, ys, where="post", color=GREY if label == "Other" else c, label=label, linewidth=1.8)
    ax.set_ylabel(ylabel)
    if log:
        ax.set_yscale("log")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.autofmt_xdate()
    return to_svg(fig)


def table(header: list, rows: list) -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in header)
    body = "".join(
        "<tr>" + "".join(f"<td class='{'n' if not isinstance(c, str) else ''}'>{html.escape(f'{c:,}' if isinstance(c, int) else f'{c:,.2f}' if isinstance(c, float) else c)}</td>" for c in r) + "</tr>"
        for r in rows
    )
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"
