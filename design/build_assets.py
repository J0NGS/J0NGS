#!/usr/bin/env python3
"""Gera os SVGs do README em dois estilos construtivistas.

    python3 design/build_assets.py

Estilos:
  poster     -> cartaz soviético (vermelho / preto / papel, diagonais, cunha e círculo)
  brutalista -> brutalismo soviético (concreto, massas, grelha de janelas, treliça)

O nome do banner é desenhado com um alfabeto geométrico próprio (linhas grossas),
então renderiza igual em qualquer máquina. Os textos pequenos usam Arial/Courier
(com fallback para Liberation), cujas métricas são usadas para dimensionar os blocos.
"""
import math
import re
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).parent

SANS = "Arial, Helvetica, 'Liberation Sans', sans-serif"
MONO = "'Courier New', Courier, 'Liberation Mono', monospace"
_FONT_SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
_FONT_MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"


def text_width(s, size, mono=False, spacing=0.0):
    """Largura aproximada (px) de um texto em negrito, com letter-spacing em em."""
    font = ImageFont.truetype(_FONT_MONO if mono else _FONT_SANS, 100)
    return font.getlength(s) * size / 100 + spacing * size * len(s)


_LOGO = (ROOT / "logo" / "jongs.svg").read_text()
_LOGO_MARCA = re.search(r'<g[^>]*id="marca">(.*?)</g>', _LOGO, re.S).group(1)
_LOGO_TEXTO = re.search(r'<g[^>]*id="texto">(.*?)</g>', _LOGO, re.S).group(1)
LOGO_W, LOGO_H = 322.83, 129.13


def logo(x, y, w, color, text_color=None):
    """Logo JONGS (xícara + letras + {software developer}) com largura `w`, em `color`."""
    k = w / LOGO_W
    return (
        f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.4f})">'
        f'<g fill="{color}" fill-rule="nonzero">{_LOGO_MARCA}</g>'
        f'<g fill="{text_color or color}">{_LOGO_TEXTO}</g></g>'
    )


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------
# Alfabeto geométrico (cada glifo: lista de polilinhas em caixa 0..w x 0..1)
# --------------------------------------------------------------------------
def _arc(cx, cy, rx, ry, a0, a1, n=40):
    return [
        (
            cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)),
        )
        for i in range(n + 1)
    ]


def glyph(ch, square):
    """Retorna (largura, [(pontos, fechado, espessura_rel), ...])."""
    if ch == " ":
        return 0.38, []
    if ch == "J":
        w = 0.62
        if square:
            return w, [([(w, 0), (w, 1), (0, 1), (0, 0.72)], False, 1)]
        return w, [([(w, 0)] + _arc(w / 2, 0.72, w / 2, 0.28, 0, 180), False, 1)]
    if ch == "O":
        w = 0.74
        if square:
            return w, [([(0, 0), (w, 0), (w, 1), (0, 1)], True, 1)]
        return w, [(_arc(w / 2, 0.5, w / 2, 0.5, 0, 360, 56), True, 1)]
    if ch in ("A", "Ã"):
        w = 0.74
        if square:
            body = [([(0, 1), (0, 0), (w, 0), (w, 1)], False, 1), ([(0, 0.56), (w, 0.56)], False, 1)]
        else:
            body = [([(0, 1), (w / 2, 0), (w, 1)], False, 1), ([(w * 0.2, 0.68), (w * 0.8, 0.68)], False, 1)]
        if ch == "Ã":
            tilde = [(w * 0.08 + w * 0.84 * i / 20, -0.3 - 0.07 * math.sin(i / 20 * 2 * math.pi)) for i in range(21)]
            body.append((tilde, False, 0.55))
        return w, body
    if ch == "N":
        w = 0.74
        return w, [([(0, 1), (0, 0), (w, 1), (w, 0)], False, 1)]
    if ch in ("G",):
        w = 0.74
        if square:
            return w, [([(w, 0), (0, 0), (0, 1), (w, 1), (w, 0.5), (w * 0.5, 0.5)], False, 1)]
        return w, [(_arc(w / 2, 0.5, w / 2, 0.5, -35, -360, 52) + [(w * 0.5, 0.5)], False, 1)]
    if ch in ("C", "Ç"):
        w = 0.74
        if square:
            parts = [([(w, 0), (0, 0), (0, 1), (w, 1)], False, 1)]
        else:
            parts = [(_arc(w / 2, 0.5, w / 2, 0.5, -40, -320, 48), False, 1)]
        if ch == "Ç":
            parts.append(([(w / 2, 1), (w / 2, 1.2)], False, 0.7))
        return w, parts
    if ch == "L":
        w = 0.6
        return w, [([(0, 0), (0, 1), (w, 1)], False, 1)]
    raise ValueError(f"glifo sem desenho: {ch!r}")


def block_text(x, y, height, s, stroke, color, square=False, gap=0.12):
    """Desenha `s` com o alfabeto geométrico. (x, y) = canto superior esquerdo.

    `gap` é o espaço entre letras além da espessura do traço (ambos em fração da altura).
    """
    out = []
    tracking = gap + stroke / height
    cx = 0.0
    for ch in s:
        w, lines = glyph(ch, square)
        for pts, closed, k in lines:
            d = " ".join(f"{'M' if i == 0 else 'L'}{x + (cx + px) * height:.1f},{y + py * height:.1f}" for i, (px, py) in enumerate(pts))
            if closed:
                d += " Z"
            out.append(
                f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{stroke * k:.1f}" '
                f'stroke-linejoin="miter" stroke-miterlimit="2" stroke-linecap="butt"/>'
            )
        cx += w + tracking
    return "\n".join(out), (cx - tracking) * height


def svg(w, h, body, title, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}">\n'
        f"<title>{esc(title)}</title>\n<defs>{defs}</defs>\n{body}\n</svg>\n"
    )


def fit_size(s, max_w, start=22, spacing=0.05):
    size = start
    while size > 11 and text_width(s, size, spacing=spacing) > max_w:
        size -= 1
    return size


def label(x, y, s, size, fill, mono=False, anchor="start", spacing=0.04, weight=700):
    fam = MONO if mono else SANS
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing * size:.2f}">{esc(s)}</text>'
    )


# ==========================================================================
# ESTILO 1 — POSTER
# ==========================================================================
P_RED, P_BLACK, P_PAPER, P_PAPER2 = "#D8261D", "#141414", "#E9DFC8", "#D9CDB0"

P_GRAIN = (
    '<filter id="grain" x="0" y="0" width="100%" height="100%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="4" result="n"/>'
    '<feColorMatrix type="matrix" values="0 0 0 0 0.1  0 0 0 0 0.08  0 0 0 0 0.05  0 0 0 0.16 0"/>'
    "</filter>"
)


def p_paper(w, h):
    return (
        f'<rect width="{w}" height="{h}" fill="{P_PAPER}"/>'
        f'<rect width="{w}" height="{h}" filter="url(#grain)"/>'
    )


def poster_banner():
    W, H = 1280, 480
    b = [p_paper(W, H)]
    # círculo vermelho + círculo preto menor
    b.append(f'<circle cx="985" cy="250" r="205" fill="{P_RED}"/>')
    b.append(f'<circle cx="1220" cy="70" r="44" fill="{P_BLACK}"/>')
    b.append(f'<circle cx="1220" cy="70" r="16" fill="{P_PAPER}"/>')
    b.append(logo(836, 104, 300, P_BLACK))
    # cunhas: preta atravessando o círculo, vermelha fina por cima
    b.append(f'<polygon points="0,430 1085,226 1085,272 0,480" fill="{P_BLACK}"/>')
    b.append(f'<polygon points="0,396 640,276 0,424" fill="{P_RED}"/>')
    # régua superior
    b.append(f'<rect x="0" y="0" width="{W}" height="14" fill="{P_BLACK}"/>')
    b.append(f'<rect x="0" y="0" width="150" height="14" fill="{P_RED}"/>')
    b.append(label(48, 50, "DESENVOLVIMENTO  ·  OTIMIZAÇÃO  ·  MANDACARU ENERGIA", 15, P_BLACK, spacing=0.18))
    # nome (levemente inclinado), com sombra vermelha deslocada
    H0, SW = 96, 18
    n1, _ = block_text(0, 0, H0, "JOÃO", SW, P_BLACK)
    n2, _ = block_text(0, 0, H0, "GONÇALO", SW, P_BLACK)
    s1, _ = block_text(0, 0, H0, "JOÃO", SW, P_RED)
    s2, _ = block_text(0, 0, H0, "GONÇALO", SW, P_RED)
    b.append(
        '<g transform="translate(64 112) rotate(-5)">'
        f'<g transform="translate(9 9)">{s1}</g>{n1}'
        f'<g transform="translate(9 143)">{s2}</g><g transform="translate(0 134)">{n2}</g>'
        "</g>"
    )
    # faixas de cargo
    bars = ["DESENVOLVEDOR FULL-STACK", "MESTRANDO EM CIÊNCIA DA COMPUTAÇÃO", "PESQUISADOR EM PESQUISA OPERACIONAL"]
    g = ['<g transform="translate(560 372) rotate(-5)">']
    for i, t in enumerate(bars):
        size = 21
        tw = text_width(t, size, spacing=0.06)
        y = i * 38
        fill = P_PAPER if i != 1 else P_BLACK
        bg = P_BLACK if i != 1 else P_PAPER
        x0 = -14 + i * 22
        g.append(f'<rect x="{x0}" y="{y}" width="{tw + 36:.0f}" height="32" fill="{bg}"/>')
        g.append(label(x0 + 18, y + 22, t, size, fill, spacing=0.06))
    g.append("</g>")
    b.append("".join(g))
    return svg(W, H, "\n".join(b), "João Gonçalo — Desenvolvedor Full-Stack, Mestrando em Ciência da Computação, Pesquisador em Pesquisa Operacional", P_GRAIN)


def poster_header(num, title, sub=""):
    W, H = 1280, 96
    tw = text_width(title.upper(), 44, spacing=0.05)
    bar_end = max(520, 150 + tw + 90)
    b = [p_paper(W, H)]
    b.append(f'<rect x="0" y="0" width="96" height="{H}" fill="{P_RED}"/>')
    b.append(label(48, 64, num, 46, P_PAPER, anchor="middle", weight=900))
    b.append(f'<polygon points="96,0 {bar_end:.0f},0 {bar_end - 34:.0f},{H} 96,{H}" fill="{P_BLACK}"/>')
    b.append(label(130, 64, title.upper(), 44, P_PAPER, spacing=0.05, weight=900))
    # traço fino + triângulo
    b.append(f'<rect x="{bar_end + 14:.0f}" y="{H - 18}" width="{W - bar_end - 14 - 60:.0f}" height="6" fill="{P_BLACK}"/>')
    b.append(f'<polygon points="{W - 52},{H - 8} {W - 8},{H - 8} {W - 8},{H - 52}" fill="{P_RED}"/>')
    if sub:
        b.append(label(bar_end + 18, 40, sub.upper(), 15, P_BLACK, spacing=0.16))
    return svg(W, H, "\n".join(b), title, P_GRAIN)


def poster_tech(groups):
    W = 1280
    LABEL_W, ROW_H, GAP, PAD = 250, 58, 12, 14
    y = 0
    b = []
    palette = [(P_RED, P_PAPER), (P_BLACK, P_PAPER), (P_PAPER2, P_BLACK)]
    for gi, (cat, items) in enumerate(groups):
        # quebra tiles em linhas
        rows, cur, cw = [], [], LABEL_W + 22
        tiles = []
        for it in items:
            tw = text_width(it, 22, spacing=0.03) + 52
            tiles.append((it, tw))
        for it, tw in tiles:
            if cur and cw + tw + GAP > W - 30:
                rows.append(cur)
                cur, cw = [], LABEL_W + 22
            cur.append((it, tw))
            cw += tw + GAP
        rows.append(cur)
        block_h = len(rows) * ROW_H + (len(rows) - 1) * GAP
        # etiqueta da categoria (paralelogramo)
        b.append(f'<polygon points="0,{y} {LABEL_W},{y} {LABEL_W - 28},{y + block_h} 0,{y + block_h}" fill="{P_BLACK}"/>')
        b.append(f'<rect x="0" y="{y}" width="14" height="{block_h}" fill="{P_RED}"/>')
        b.append(label(34, y + block_h / 2 + 8, cat.upper(), fit_size(cat.upper(), LABEL_W - 34 - 44), P_PAPER, spacing=0.05, weight=900))
        t = 0
        for ri, row in enumerate(rows):
            x = LABEL_W + 22
            ry = y + ri * (ROW_H + GAP)
            for it, tw in row:
                fill, txt = palette[t % 3]
                t += 1
                sl = 16
                b.append(
                    f'<polygon points="{x + sl},{ry} {x + tw},{ry} {x + tw - sl},{ry + ROW_H} {x},{ry + ROW_H}" fill="{fill}"'
                    + (f' stroke="{P_BLACK}" stroke-width="3"' if fill == P_PAPER2 else "")
                    + "/>"
                )
                b.append(label(x + tw / 2, ry + 37, it, 22, txt, anchor="middle", spacing=0.03, weight=900))
                x += tw + GAP
        y += block_h + 30
    H = y - 30
    body = f'<rect width="{W}" height="{H}" fill="{P_PAPER}"/><rect width="{W}" height="{H}" filter="url(#grain)"/>' + "\n".join(b)
    return svg(W, H, body, "Tecnologias e ferramentas", P_GRAIN)


def poster_contact(kind, big, small):
    W, H = 620, 130
    b = [p_paper(W, H)]
    red = kind == "linkedin"
    main = P_RED if red else P_BLACK
    b.append(f'<polygon points="0,0 {W - 40},0 {W},{H} 0,{H}" fill="{main}"/>')
    b.append(f'<circle cx="{W - 86}" cy="{H / 2}" r="34" fill="{P_PAPER}"/>')
    b.append(f'<polygon points="{W - 100},{H / 2 - 16} {W - 66},{H / 2} {W - 100},{H / 2 + 16}" fill="{main}"/>')
    b.append(label(34, 52, small.upper(), 16, P_PAPER, spacing=0.2))
    b.append(label(34, 100, big.upper(), 44 if len(big) < 11 else 31, P_PAPER, spacing=0.03, weight=900))
    return svg(W, H, "\n".join(b), f"{big} — {small}", P_GRAIN)


def poster_footer():
    W, H = 1280, 120
    b = [p_paper(W, H)]
    b.append(f'<polygon points="0,{H} 0,40 1000,{H}" fill="{P_BLACK}"/>')
    b.append(f'<polygon points="0,{H} 0,80 420,{H}" fill="{P_RED}"/>')
    b.append(f'<circle cx="1210" cy="44" r="26" fill="{P_RED}"/>')
    b.append(label(W - 40, 104, "OTIMIZAR  ·  CONSTRUIR  ·  ENTREGAR", 16, P_BLACK, anchor="end", spacing=0.2))
    return svg(W, H, "\n".join(b), "Rodapé", P_GRAIN)


# ==========================================================================
# ESTILO 2 — BRUTALISTA (linha fina, formas em excesso, "fantasias arquitetônicas")
# ==========================================================================
B_CONC, B_CONC_D, B_CONC_L, B_BLACK, B_RED = "#A9A79F", "#6F6D68", "#D6D3C9", "#161616", "#D4281C"

B_DEFS = (
    '<filter id="conc" x="0" y="0" width="100%" height="100%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="3" seed="9" result="n"/>'
    '<feColorMatrix type="matrix" values="0 0 0 0 0.05  0 0 0 0 0.05  0 0 0 0 0.04  0 0 0 0.30 0"/>'
    "</filter>"
    '<filter id="concl" x="0" y="0" width="100%" height="100%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.4" numOctaves="2" seed="3" result="n"/>'
    '<feColorMatrix type="matrix" values="0 0 0 0 0.05  0 0 0 0 0.05  0 0 0 0 0.04  0 0 0 0.20 0"/>'
    "</filter>"
    '<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
    f'<line x1="0" y1="0" x2="0" y2="7" stroke="{B_BLACK}" stroke-width="0.9"/></pattern>'
    '<pattern id="hatchr" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">'
    f'<line x1="0" y1="0" x2="0" y2="6" stroke="{B_RED}" stroke-width="0.9"/></pattern>'
)


def b_concrete(w, h, fill=B_CONC_L, grid=80):
    """Concreto claro com textura e grelha de projeto muito fina."""
    g = "".join(f'<path d="M{x} 0V{h}" stroke="{B_BLACK}" stroke-width="1" opacity="0.06"/>' for x in range(grid, w, grid))
    g += "".join(f'<path d="M0 {y}H{w}" stroke="{B_BLACK}" stroke-width="1" opacity="0.06"/>' for y in range(grid // 2, h, grid // 2))
    return f'<rect width="{w}" height="{h}" fill="{fill}"/><rect width="{w}" height="{h}" filter="url(#concl)"/>{g}'


def ruler(x0, x1, y, step=16, major=5, h=6, color=B_BLACK):
    """Régua fina com marcações."""
    out = [f'<path d="M{x0} {y}H{x1}" stroke="{color}" stroke-width="1.5"/>']
    n = int((x1 - x0) // step)
    for i in range(n + 1):
        x = x0 + i * step
        hh = h * 2 if i % major == 0 else h
        out.append(f'<path d="M{x} {y}v-{hh}" stroke="{color}" stroke-width="1"/>')
    return "".join(out)


def brutal_banner():
    W, H = 1280, 480
    ink = B_BLACK
    b = [b_concrete(W, H)]
    # ---------- composição à direita: círculos, triângulo, diagonais, espiral ----------
    cx, cy = 930, 250
    b.append(f'<polygon points="{cx},44 {cx},456 640,456" fill="url(#hatch)" opacity="0.55"/>')
    b.append(f'<polygon points="{cx},44 1220,456 640,456" fill="none" stroke="{ink}" stroke-width="1.6"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="200" fill="none" stroke="{B_RED}" stroke-width="2.6"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="150" fill="none" stroke="{ink}" stroke-width="1"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="100" fill="none" stroke="{ink}" stroke-width="1" stroke-dasharray="7 6"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="52" fill="url(#hatchr)" stroke="{B_RED}" stroke-width="1.2"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="{B_RED}"/>')
    # eixos e diagonais
    for x1, y1, x2, y2, w in [(600, 478, 1250, 22, 1.2), (640, 478, 1250, 70, 0.8), (600, 40, 1250, 450, 0.8), (cx, 20, cx, 470, 0.8), (600, cy, 1260, cy, 0.8)]:
        b.append(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{ink}" stroke-width="{w}"/>')
    # espiral de Tatlin: elipses inclinadas ao longo de um eixo
    b.append(f'<g transform="rotate(-16 {cx} {cy})" fill="none" stroke="{ink}" stroke-width="1">')
    for i in range(9):
        y = 70 + i * 48
        rx = 28 + i * 20
        b.append(f'<ellipse cx="{cx}" cy="{y}" rx="{rx}" ry="{6 + i * 2.2:.1f}"/>')
    b.append("</g>")
    # bloco com janelas (concreto) — formas finas, sem massa
    bx, by, bw, bh = 1046, 330, 190, 96
    b.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{B_CONC}" fill-opacity="0.55" stroke="{ink}" stroke-width="1.6"/>')
    for r in range(3):
        for c in range(7):
            b.append(f'<rect x="{bx + 10 + c * 25}" y="{by + 12 + r * 27}" width="16" height="17" fill="none" stroke="{ink}" stroke-width="1"/>')
    # quadrado e círculo menores, vermelho como acento
    b.append(f'<rect x="676" y="58" width="52" height="52" fill="none" stroke="{ink}" stroke-width="1.6"/>')
    b.append(f'<path d="M676 58L728 110M728 58L676 110" stroke="{ink}" stroke-width="0.9"/>')
    b.append(f'<circle cx="1196" cy="86" r="34" fill="none" stroke="{ink}" stroke-width="1.6"/>')
    b.append(f'<path d="M1162 86H1230M1196 52V120" stroke="{ink}" stroke-width="0.9"/>')
    b.append(f'<rect x="1188" y="78" width="16" height="16" fill="{B_RED}"/>')
    # cotas
    b.append(ruler(640, 1220, 466, step=20, major=5, h=5))
    b.append(label(660, 450, "ESC. 1:100", 11, ink, mono=True, spacing=0.1, weight=400))
    b.append(f'<path d="M{cx + 141} {cy - 141}L{cx + 190} {cy - 190}H1010" fill="none" stroke="{ink}" stroke-width="0.8"/>')
    b.append(label(1016, 58, "Ø 400", 11, ink, mono=True, spacing=0.1, weight=400))
    # ---------- composição à esquerda: logo, nome e legendas ----------
    b.append(label(48, 38, "PROJETO Nº 001  ·  MANDACARU ENERGIA", 12, ink, mono=True, spacing=0.12, weight=400))
    b.append(f'<rect x="48" y="52" width="10" height="10" fill="{B_RED}"/>')
    b.append(logo(48, 78, 500, ink))
    b.append(ruler(48, 560, 296, step=16, major=5, h=5))
    nm, _ = block_text(48, 326, 36, "JOÃO GONÇALO", 4.6, ink, square=True, gap=0.1)
    b.append(nm)
    for i, t in enumerate(["DESENVOLVEDOR FULL-STACK", "MESTRANDO EM CIÊNCIA DA COMPUTAÇÃO", "PESQUISADOR EM PESQUISA OPERACIONAL"]):
        b.append(label(48, 404 + i * 22, t, 13, ink, mono=True, spacing=0.08, weight=400))
        b.append(f'<path d="M30 {399 + i * 22}h8" stroke="{B_RED if i == 0 else ink}" stroke-width="2"/>')
    # marcas de corte nos cantos
    for x, y, dx, dy in [(12, 12, 1, 1), (W - 12, 12, -1, 1), (12, H - 12, 1, -1), (W - 12, H - 12, -1, -1)]:
        b.append(f'<path d="M{x} {y + 14 * dy}V{y}H{x + 14 * dx}" fill="none" stroke="{ink}" stroke-width="1.2"/>')
    return svg(W, H, "\n".join(b), "João Gonçalo — Desenvolvedor Full-Stack, Mestrando em Ciência da Computação, Pesquisador em Pesquisa Operacional", B_DEFS)


def brutal_header(num, title, sub=""):
    W, H = 1280, 96
    ink = B_BLACK
    b = [b_concrete(W, H, grid=160)]
    b.append(f'<rect x="12" y="14" width="68" height="68" fill="none" stroke="{ink}" stroke-width="2"/>')
    b.append(f'<path d="M12 14L80 82" stroke="{ink}" stroke-width="0.8" opacity="0.5"/>')
    b.append(f'<rect x="12" y="14" width="68" height="68" fill="url(#hatch)" opacity="0.18"/>')
    b.append(f'<rect x="12" y="14" width="12" height="12" fill="{B_RED}"/>')
    b.append(label(46, 62, num, 32, ink, mono=True, anchor="middle", spacing=0, weight=700))
    b.append(label(108, 62, title.upper(), 38, ink, spacing=0.2, weight=400))
    if sub:
        b.append(label(108, 22, sub.upper(), 11, ink, mono=True, spacing=0.14, weight=400))
    tw = text_width(title.upper(), 38, spacing=0.2)
    b.append(ruler(108, W - 12, 82, step=16, major=5, h=5))
    b.append(f'<rect x="{W - 60}" y="76" width="48" height="6" fill="{B_RED}"/>')
    # formas ao fim do título
    x0 = 108 + tw + 28
    if x0 < W - 200:
        b.append(f'<circle cx="{x0 + 14:.0f}" cy="46" r="13" fill="none" stroke="{ink}" stroke-width="1.4"/>')
        b.append(f'<polygon points="{x0 + 48:.0f},60 {x0 + 74:.0f},32 {x0 + 100:.0f},60" fill="none" stroke="{ink}" stroke-width="1.4"/>')
        b.append(f'<rect x="{x0 + 118:.0f}" y="33" width="26" height="26" fill="none" stroke="{ink}" stroke-width="1.4"/>')
        b.append(f'<path d="M{x0 + 160:.0f} 60L{x0 + 190:.0f} 30" stroke="{ink}" stroke-width="1.4"/>')
    return svg(W, H, "\n".join(b), title, B_DEFS)


def _bullet(kind, x, y, color):
    """Pequenas formas geométricas usadas como marcador."""
    if kind == 0:
        return f'<circle cx="{x}" cy="{y}" r="6" fill="none" stroke="{color}" stroke-width="1.6"/>'
    if kind == 1:
        return f'<polygon points="{x - 7},{y + 6} {x},{y - 7} {x + 7},{y + 6}" fill="none" stroke="{color}" stroke-width="1.6"/>'
    if kind == 2:
        return f'<rect x="{x - 6}" y="{y - 6}" width="12" height="12" fill="none" stroke="{color}" stroke-width="1.6"/>'
    return f'<path d="M{x - 7} {y}H{x + 7}M{x} {y - 7}V{y + 7}" stroke="{color}" stroke-width="1.6"/>'


def brutal_tech(groups):
    W = 1280
    LABEL_W, ROW_H, GAP = 250, 52, 12
    ink = B_BLACK
    y = 0
    b = []
    for gi, (cat, items) in enumerate(groups):
        rows, cur, cw = [], [], LABEL_W + 24
        for it in items:
            tw = text_width(it, 20, mono=True, spacing=0.02) + 64
            if cur and cw + tw + GAP > W - 30:
                rows.append(cur)
                cur, cw = [], LABEL_W + 24
            cur.append((it, tw))
            cw += tw + GAP
        rows.append(cur)
        block_h = len(rows) * ROW_H + (len(rows) - 1) * GAP
        b.append(f'<path d="M0 {y}H{LABEL_W - 20}M0 {y + block_h}H{LABEL_W - 20}" stroke="{ink}" stroke-width="1.5"/>')
        b.append(f'<rect x="0" y="{y}" width="6" height="{block_h}" fill="{B_RED}"/>')
        b.append(label(24, y + block_h / 2 + 7, cat.upper(), fit_size(cat.upper(), LABEL_W - 24 - 30, start=20, spacing=0.1), ink, spacing=0.1, weight=400))
        b.append(label(LABEL_W - 24, y + 14, f"0{gi + 1}", 11, ink, mono=True, anchor="end", weight=400))
        t = 0
        for ri, row in enumerate(rows):
            x = LABEL_W + 24
            ry = y + ri * (ROW_H + GAP)
            for it, tw in row:
                b.append(f'<rect x="{x}" y="{ry}" width="{tw:.0f}" height="{ROW_H}" fill="{B_CONC}" fill-opacity="0.35" stroke="{ink}" stroke-width="1.5"/>')
                if t % 3 == 1:
                    b.append(f'<rect x="{x}" y="{ry}" width="{tw:.0f}" height="{ROW_H}" fill="url(#hatch)" opacity="0.22"/>')
                b.append(_bullet(t % 4, x + 24, ry + ROW_H / 2, B_RED if t == 0 else ink))
                b.append(label(x + 44, ry + ROW_H / 2 + 6, it, 20, ink, mono=True, spacing=0.02, weight=400))
                x += tw + GAP
                t += 1
        y += block_h + 28
    H = y - 28
    body = b_concrete(W, H, grid=160) + "\n".join(b)
    return svg(W, H, body, "Tecnologias e ferramentas", B_DEFS)


def brutal_contact(kind, big, small):
    W, H = 620, 130
    ink = B_BLACK
    red = kind == "linkedin"
    b = [b_concrete(W, H, grid=160)]
    b.append(f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" fill="none" stroke="{ink}" stroke-width="2"/>')
    b.append(f'<rect x="{W - 190}" y="2" width="188" height="{H - 4}" fill="url(#{"hatchr" if red else "hatch"})" opacity="0.6"/>')
    b.append(f'<path d="M{W - 190} 2V{H - 2}" stroke="{ink}" stroke-width="1.5"/>')
    b.append(f'<circle cx="{W - 96}" cy="{H / 2}" r="30" fill="{B_CONC_L}" stroke="{ink}" stroke-width="1.6"/>')
    b.append(f'<polygon points="{W - 108},{H / 2 - 14} {W - 82},{H / 2} {W - 108},{H / 2 + 14}" fill="{B_RED if red else ink}"/>')
    b.append(f'<rect x="2" y="2" width="12" height="12" fill="{B_RED}"/>')
    b.append(label(34, 44, small.upper(), 13, ink, mono=True, spacing=0.12, weight=400))
    b.append(label(34, 94, big.upper(), 40 if len(big) < 11 else 30, ink, spacing=0.12, weight=400))
    return svg(W, H, "\n".join(b), f"{big} — {small}", B_DEFS)


def brutal_footer():
    W, H = 1280, 120
    ink = B_BLACK
    b = [b_concrete(W, H, grid=160)]
    for i, r in enumerate((90, 66, 42, 18)):
        b.append(f'<path d="M{20} {H - 8}m{-r} 0a{r} {r} 0 0 1 {2 * r} 0" transform="translate({r + 40 - r} 0)" fill="none" stroke="{B_RED if i == 0 else ink}" stroke-width="{1.6 if i == 0 else 1}"/>')
    b.append(ruler(260, 1000, H - 24, step=20, major=5, h=6))
    b.append(f'<polygon points="1010,{H - 24} 1050,{H - 24} 1030,{H - 62}" fill="none" stroke="{ink}" stroke-width="1.4"/>')
    b.append(f'<circle cx="1090" cy="{H - 43}" r="19" fill="none" stroke="{ink}" stroke-width="1.4"/>')
    b.append(f'<rect x="1130" y="{H - 62}" width="38" height="38" fill="none" stroke="{ink}" stroke-width="1.4"/>')
    b.append(f'<path d="M1130 {H - 24}L1168 {H - 62}" stroke="{B_RED}" stroke-width="1.4"/>')
    b.append(label(W - 12, 24, "OTIMIZAR  ·  CONSTRUIR  ·  ENTREGAR", 12, ink, mono=True, anchor="end", spacing=0.14, weight=400))
    return svg(W, H, "\n".join(b), "Rodapé", B_DEFS)


# ==========================================================================
TECH = [
    ("Back-End", ["Java", "Spring", "PostgreSQL", "MySQL"]),
    ("Front-End", ["React", "TypeScript", "Vite", "Mantine"]),
    ("Mobile", ["Flutter", "Swift"]),
    ("DevOps & Infra", ["Docker", "GitHub Actions", "Linux", "Git", "Nginx", "Grafana"]),
    ("Pesquisa Operacional", ["Python", "Jupyter", "C++"]),
]

SECTIONS = [
    ("01", "Sobre mim", "manifesto", "sobre"),
    ("02", "Tecnologias", "ferramentas de trabalho", "tecnologias"),
    ("03", "Projetos", "obras e contribuições", "projetos"),
    ("04", "Atividade", "produção diária", "atividade"),
    ("05", "Estatísticas", "números do GitHub", "estatisticas"),
    ("06", "Contato", "convoque-me", "contato"),
]


def build(style):
    d = ROOT / style
    d.mkdir(exist_ok=True)
    if style == "poster":
        banner, header, tech, contact, footer = poster_banner, poster_header, poster_tech, poster_contact, poster_footer
    else:
        banner, header, tech, contact, footer = brutal_banner, brutal_header, brutal_tech, brutal_contact, brutal_footer
    (d / "banner.svg").write_text(banner())
    for num, title, sub, slug in SECTIONS:
        (d / f"h-{slug}.svg").write_text(header(num, title, sub))
    (d / "tecnologias.svg").write_text(tech(TECH))
    (d / "contato-linkedin.svg").write_text(contact("linkedin", "LinkedIn", "/in/jngoncalo"))
    (d / "contato-email.svg").write_text(contact("email", "E-mail", "jnetogoncalo@gmail.com"))
    (d / "footer.svg").write_text(footer())


if __name__ == "__main__":
    for s in ("poster", "brutalista"):
        build(s)
        print("ok", s)
