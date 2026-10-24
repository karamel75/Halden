"""Génère le logo Halden (emblème tour + wordmark Montserrat vectorisé) en SVG et PNG.

Usage : python tools/make_logo.py chemin/vers/montserrat-latin-600-normal.woff2
"""
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = Path(__file__).resolve().parent.parent / "docs" / "assets"
NUIT, CHAMPAGNE, BLANC = "#0B1426", "#C9A86A", "#FFFFFF"


def text_path(font_file, text, size, tracking_em):
    font = TTFont(font_file)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    upm = font["head"].unitsPerEm
    scale = size / upm
    pen = SVGPathPen(gs)
    x = 0.0
    for ch in text:
        name = cmap[ord(ch)]
        tp = TransformPen(pen, (scale, 0, 0, -scale, x, size * 0.72))
        gs[name].draw(tp)
        x += gs[name].width * scale + tracking_em * size
    return pen.getCommands(), x - tracking_em * size


def emblem(color, x0=0, y0=0, h=64):
    """Tour à façade incurvée : un arc fin et des lignes verticales qui s'infléchissent."""
    w = h * 0.56
    top = y0 + h * 0.18
    parts = [f'<path d="M{x0} {y0+h} V{top+w/2} A{w/2} {w/2} 0 0 1 {x0+w} {top+w/2} V{y0+h}" '
             f'fill="none" stroke="{color}" stroke-width="1.6"/>']
    n = 6
    for i in range(1, n):
        t = i / n
        x = x0 + w * t
        bow = (w * 0.16) * (1 - abs(2 * t - 1))
        ystart = top + w / 2 - (w / 2) * (1 - (2 * t - 1) ** 2) ** 0.5 + 4
        parts.append(f'<path d="M{x:.2f} {ystart:.2f} Q{x-bow:.2f} {(ystart+y0+h)/2:.2f} {x:.2f} {y0+h}" '
                     f'fill="none" stroke="{color}" stroke-width="0.9" opacity="0.85"/>')
    parts.append(f'<line x1="{x0-6}" y1="{y0+h}" x2="{x0+w+6}" y2="{y0+h}" stroke="{color}" stroke-width="1.6"/>')
    return "\n  ".join(parts), w


def build(font_file, word_color, mark_color, bg, name, tagline=True):
    d, tw = text_path(font_file, "HALDEN", 34, 0.42)
    em, ew = emblem(mark_color, 0, 4, 64)
    gap = 26
    width = ew + gap + tw
    tag = ""
    height = 72
    if tagline:
        td, _ = text_path(font_file, "EVERY PROMISE, CARRIED THROUGH.", 8.0, 0.25)
        tag = f'<g transform="translate({ew+gap+2},52)"><path d="{td}" fill="{mark_color}"/></g>'
    pad = 28
    W, H = width + 2 * pad, height + 2 * pad
    bgrect = f'<rect width="{W:.0f}" height="{H:.0f}" fill="{bg}"/>' if bg else ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" role="img" aria-label="Halden">
  {bgrect}
  <g transform="translate({pad},{pad})">
  {em}
  <g transform="translate({ew+gap},{10 if tagline else 18})"><path d="{d}" fill="{word_color}"/></g>
  {tag}
  </g>
</svg>'''
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(OUT / f"{name}.png"), scale=4)
    except ImportError:
        pass


def build_mark(name, color, bg):
    em, ew = emblem(color, 0, 0, 64)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-18 -12 72 88" width="72" height="88">
  <rect x="-18" y="-12" width="72" height="88" rx="14" fill="{bg}"/>
  {em}
</svg>'''
    (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    f = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    build(f, BLANC, CHAMPAGNE, NUIT, "halden-logo-nuit")
    build(f, NUIT, "#8A6A3A", None, "halden-logo-clair")
    build(f, BLANC, CHAMPAGNE, None, "halden-logo-blanc")
    build_mark("halden-embleme", CHAMPAGNE, NUIT)
    print("logos écrits dans", OUT)
