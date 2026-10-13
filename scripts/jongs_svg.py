"""Helpers compartilhados para gerar os SVGs do perfil.

Tudo é preto e branco e todo texto é convertido em curvas (Liberation Mono), então
os SVGs ficam idênticos em qualquer máquina, sem depender de fontes instaladas.

Requisitos: `pip install fonttools` e a fonte Liberation Mono (pacote `fonts-liberation`).
Se ela estiver em outro lugar, aponte com a variável de ambiente MONO_FONT_DIR.
"""
import math
import os
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


class Theme:
    """`ink` é a cor do traço; `paper` só aparece como cor de texto sobre áreas `ink`."""

    def __init__(self, name, ink, paper):
        self.name, self.ink, self.paper = name, ink, paper


LIGHT = Theme("light", "#000000", "#FFFFFF")
DARK = Theme("dark", "#FFFFFF", "#0D1117")  # `paper` do tema escuro = fundo do GitHub
THEMES = (LIGHT, DARK)

# ---------------------------------------------------------------- texto em curvas
_FONT_DIRS = [
    os.environ.get("MONO_FONT_DIR", ""),
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/liberation2",
    "/usr/share/fonts/liberation-mono",
    "/usr/share/fonts/liberation",
    "/Library/Fonts",
    "C:/Windows/Fonts",
]
_cache = {}


def _font(bold):
    key = bool(bold)
    if key not in _cache:
        name = "LiberationMono-Bold.ttf" if bold else "LiberationMono-Regular.ttf"
        for d in _FONT_DIRS:
            if d and (Path(d) / name).exists():
                f = TTFont(Path(d) / name)
                adv = f["hmtx"][f.getBestCmap()[ord("0")]][0]
                _cache[key] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm, adv)
                break
        else:
            raise SystemExit(f"{name} não encontrada. Instale fonts-liberation ou defina MONO_FONT_DIR.")
    return _cache[key]


def _n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def mono_width(s, size, ls=0.0):
    _, _, _, upm, adv = _font(False)
    return len(s) * (adv / upm * size + ls * size) - ls * size


def mono(x, y, s, size, fill, anchor="start", bold=False, ls=0.0):
    """Texto monoespaçado desenhado como um único <path>. (x, y) = linha de base."""
    _, gs, cmap, upm, adv = _font(bold)
    k = size / upm
    step = adv * k + ls * size
    total = step * len(s) - ls * size
    x0 = x - (total if anchor == "end" else total / 2 if anchor == "middle" else 0)
    d = []
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        gn = cmap.get(ord(ch))
        if gn is None:
            raise SystemExit(f"glifo ausente na fonte: {ch!r}")
        pen = SVGPathPen(gs, ntos=_n)
        gs[gn].draw(TransformPen(pen, (k, 0, 0, -k, x0 + i * step, y)))
        d.append(pen.getCommands())
    return f'<path d="{"".join(d)}" fill="{fill}"/>'


# ---------------------------------------------------------------- logo
_LOGO = (ASSETS / "logo" / "jongs.svg").read_text()
_MARCA = re.search(r'<g[^>]*id="marca">(.*?)</g>', _LOGO, re.S).group(1)
_TEXTO = re.search(r'<g[^>]*id="texto">(.*?)</g>', _LOGO, re.S).group(1)
LOGO_W = 322.83


def logo(x, y, w, color):
    k = w / LOGO_W
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.4f})" fill="{color}" fill-rule="nonzero">{_MARCA}{_TEXTO}</g>'


# ---------------------------------------------------------------- letras geométricas (quadradas)
def glyph(ch):
    """(largura, [(pontos, fechado, espessura_rel)]) em caixa 0..w x 0..1."""
    if ch == " ":
        return 0.38, []
    w = 0.74
    if ch == "J":
        return 0.62, [([(0.62, 0), (0.62, 1), (0, 1), (0, 0.72)], False, 1)]
    if ch == "O":
        return w, [([(0, 0), (w, 0), (w, 1), (0, 1)], True, 1)]
    if ch in ("A", "Ã"):
        parts = [([(0, 1), (0, 0), (w, 0), (w, 1)], False, 1), ([(0, 0.56), (w, 0.56)], False, 1)]
        if ch == "Ã":
            tilde = [(w * 0.08 + w * 0.84 * i / 20, -0.3 - 0.07 * math.sin(i / 20 * 2 * math.pi)) for i in range(21)]
            parts.append((tilde, False, 0.55))
        return w, parts
    if ch == "N":
        return w, [([(0, 1), (0, 0), (w, 1), (w, 0)], False, 1)]
    if ch == "G":
        return w, [([(w, 0), (0, 0), (0, 1), (w, 1), (w, 0.5), (w * 0.5, 0.5)], False, 1)]
    if ch in ("C", "Ç"):
        parts = [([(w, 0), (0, 0), (0, 1), (w, 1)], False, 1)]
        if ch == "Ç":
            parts.append(([(w / 2, 1), (w / 2, 1.2)], False, 0.7))
        return w, parts
    if ch == "L":
        return 0.6, [([(0, 0), (0, 1), (0.6, 1)], False, 1)]
    raise ValueError(f"glifo sem desenho: {ch!r}")


def block_text(x, y, height, s, stroke, color, gap=0.1):
    """Escreve `s` com o alfabeto geométrico. (x, y) = canto superior esquerdo."""
    out, cx = [], 0.0
    tracking = gap + stroke / height
    for ch in s:
        w, lines = glyph(ch)
        for pts, closed, k in lines:
            d = " ".join(f"{'M' if i == 0 else 'L'}{x + (cx + px) * height:.1f},{y + py * height:.1f}" for i, (px, py) in enumerate(pts))
            if closed:
                d += " Z"
            out.append(
                f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{stroke * k:.1f}" '
                f'stroke-linejoin="miter" stroke-miterlimit="2" stroke-linecap="butt"/>'
            )
        cx += w + tracking
    return "".join(out)


def svg(w, h, body, title, defs="", bg=None):
    esc = title.replace("&", "&amp;").replace("<", "&lt;")
    if bg:  # fundo opaco: o SVG continua legível mesmo se o tema da página não bater com a variante
        body = f'<rect width="{w}" height="{h}" fill="{bg}"/>\n' + body
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc}">\n'
        f"<title>{esc}</title>\n<defs>{defs}</defs>\n{body}\n</svg>\n"
    )
