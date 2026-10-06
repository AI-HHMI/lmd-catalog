"""Turn the LMD catalog report into a self-contained HTML slide deck (same charts as report.py).

Usage: uv sync --extra analysis && python scripts/analysis/slides.py   ->  docs/slides.html

Keys: arrows / space / PageUp+PageDown to move, Home/End to jump, f for fullscreen; click the left third to go back, anywhere else to go forward.
Print to PDF for handouts.
"""

from pathlib import Path

import report

OUT = Path(__file__).parents[2] / "docs" / "slides.html"
CHARTS_PER_SLIDE = 2
CSS = """
html,body{margin:0;height:100%;background:#fff;color:#222;font:20px system-ui,sans-serif;overflow:hidden}
.slide{display:none;height:100vh;box-sizing:border-box;padding:4vh 6vw;flex-direction:column}
.slide.on{display:flex} .kicker{color:#0072B2;font-size:.7em;text-transform:uppercase;letter-spacing:.08em}
h1{font-size:2.4em;margin:12vh 0 2vh} h2{font-size:1.6em;margin:.2em 0 .6em} h3{font-size:.85em;margin:0 0 .4em;color:#555}
.row{display:flex;gap:3vw;flex:0 1 auto;min-height:0;margin:auto 0;align-items:flex-start;justify-content:center}
.card{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center} .card h3{text-align:center}
.card svg{width:100%;height:auto;max-height:68vh}
.tiles{display:flex;flex-wrap:wrap;gap:2vw} .tile{border:1px solid #ddd;border-radius:8px;padding:1.2vh 2vw;font-size:.8em}
.tile b{display:block;font-size:2em}
table{border-collapse:collapse;font-size:1.05em} th,td{padding:.3em .9em;border-bottom:1px solid #eee;text-align:left}
td.n,th{text-align:right} th:first-child{text-align:left}
p.hint{margin-top:auto;color:#666;font-size:.75em}
#count{position:fixed;right:2vw;bottom:2vh;color:#999;font-size:.6em}
@media print{html,body{overflow:visible}.slide{display:flex;height:auto;min-height:100vh;page-break-after:always}#count{display:none}}
@page{size:landscape}
"""
JS = """
const slides = [...document.querySelectorAll('.slide')];
let i = Math.min(Math.max(parseInt(location.hash.slice(1)) || 0, 0), slides.length - 1);
function show(n) {
  i = Math.min(Math.max(n, 0), slides.length - 1);
  slides.forEach((s, k) => s.classList.toggle('on', k === i));
  document.getElementById('count').textContent = `${i + 1} / ${slides.length}`;
  history.replaceState(null, '', '#' + i);
}
document.addEventListener('keydown', e => {
  if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) show(i + 1);
  else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) show(i - 1);
  else if (e.key === 'Home') show(0);
  else if (e.key === 'End') show(slides.length - 1);
  else if (e.key === 'f') document.documentElement.requestFullscreen?.();
});
document.addEventListener('click', e => show(e.clientX < innerWidth / 3 ? i - 1 : i + 1));
show(i);
"""


def chunk(cards: list) -> list:
    """Tables get a slide to themselves; charts are grouped CHARTS_PER_SLIDE to a slide."""
    slides, charts = [], []
    for title, content in cards:
        if content.startswith("<table"):
            slides.append([(title, content)])
        else:
            charts.append((title, content))
            if len(charts) == CHARTS_PER_SLIDE:
                slides.append(charts)
                charts = []
    return slides + ([charts] if charts else [])


def slide(kicker: str, title: str, inner: str) -> str:
    return f"<section class='slide'><div class='kicker'>{kicker}</div><h2>{title}</h2>{inner}</section>"


def main():
    tiles, sections = report.build()
    title = (
        "<section class='slide'><div class='kicker'>Large Microscopy Dataset</div><h1>LMD catalog overview</h1><div class='tiles'>"
        + "".join(f"<div class='tile'><b>{n}</b>{label}</div>" for n, label in tiles)
        + "</div><p class='hint'><a href='index.html'>Full report</a> &nbsp;·&nbsp; Press → or click anywhere to start &nbsp;·&nbsp; ← goes back &nbsp;·&nbsp; f for fullscreen</p></section>"
    )
    body = title + "".join(
        slide("LMD catalog", name, "<div class='row'>" + "".join(report.card(t, c) for t, c in group) + "</div>")
        for name, cards in sections
        for group in chunk(cards)
    )
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>LMD catalog slides</title><style>{CSS}</style></head><body>{body}<div id='count'></div><script>{JS}</script></body></html>"
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
