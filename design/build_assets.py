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


def b_concrete(w, h, fill=B_CONC_L, grid=80, hgrid=None, opacity=0.06):
    """Concreto claro com textura e grelha de projeto muito fina."""
    hg = hgrid or grid // 2
    g = "".join(f'<path d="M{x} 0V{h}" stroke="{B_BLACK}" stroke-width="1" opacity="{opacity}"/>' for x in range(grid, w, grid))
    g += "".join(f'<path d="M0 {y}H{w}" stroke="{B_BLACK}" stroke-width="1" opacity="{opacity}"/>' for y in range(hg, h, hg))
    return f'<rect width="{w}" height="{h}" fill="{fill}"/><rect width="{w}" height="{h}" filter="url(#concl)"/>{g}'


def wedge(x, y, size, corner, color=B_RED):
    """Triângulo retângulo ancorado em um canto: a 'cunha vermelha' do construtivismo."""
    dx = size if corner in ("tl", "bl") else -size
    dy = size if corner in ("tl", "tr") else -size
    return f'<polygon points="{x},{y} {x + dx},{y} {x},{y + dy}" fill="{color}"/>'


def ruler(x0, x1, y, step=16, major=5, h=6, color=B_BLACK):
    """Régua fina com marcações."""
    out = [f'<path d="M{x0} {y}H{x1}" stroke="{color}" stroke-width="1.5"/>']
    n = int((x1 - x0) // step)
    for i in range(n + 1):
        x = x0 + i * step
        hh = h * 2 if i % major == 0 else h
        out.append(f'<path d="M{x} {y}v-{hh}" stroke="{color}" stroke-width="1"/>')
    return "".join(out)


def tag(x, y, s, size=11, anchor="start", opacity=1.0):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}" fill="{B_BLACK}" '
        f'text-anchor="{anchor}" letter-spacing="{0.08 * size:.2f}" opacity="{opacity}">{esc(s)}</text>'
    )


def brutal_banner():
    """Linearismo: massa (logo) + construção polar de linhas finas ancorada no canto."""
    W, H = 1280, 480
    ink, G = B_BLACK, 80
    b = [b_concrete(W, H, grid=G, hgrid=G, opacity=0.08)]
    # coordenadas da grelha (16 colunas x 6 linhas), como numa planta
    for i in range(16):
        b.append(tag(G * i + 40, 15, f"{i + 1:02d}", 10, "middle", 0.55))
    for j in range(6):
        b.append(tag(14, G * j + 44, "ABCDEF"[j], 10, "middle", 0.55))
    # ---------- construção polar: raios e arcos a partir do canto inferior direito ----------
    ox, oy = W, H
    clip = '<clipPath id="polar"><rect x="720" y="0" width="560" height="480"/></clipPath>'
    g = ['<g clip-path="url(#polar)" fill="none">']
    for r in range(160, 801, 160):
        g.append(f'<circle cx="{ox}" cy="{oy}" r="{r}" stroke="{ink}" stroke-width="1"/>')
    for k in range(7):
        if 180 + 15 * k == 225:
            continue
        th = math.radians(180 + 15 * k)
        g.append(f'<path d="M{ox} {oy}L{ox + 900 * math.cos(th):.1f} {oy + 900 * math.sin(th):.1f}" stroke="{ink}" stroke-width="1"/>')
    th = math.radians(225)
    g.append(f'<path d="M{ox} {oy}L{ox + 900 * math.cos(th):.1f} {oy + 900 * math.sin(th):.1f}" stroke="{B_RED}" stroke-width="3"/>')
    g.append("</g>")
    b.append("".join(g))
    # rótulos de raio (na base) e de ângulo (no arco r=480)
    for r in (160, 320, 480):
        b.append(f'<rect x="{ox - r - 17}" y="{oy - 22}" width="34" height="14" fill="{B_CONC_L}"/>')
        b.append(tag(ox - r, oy - 11, str(r), 10, "middle"))
    for k in range(7):
        a = 180 + 15 * k
        x, y = ox + 480 * math.cos(math.radians(a)), oy + 480 * math.sin(math.radians(a))
        if k in (0, 6):
            continue
        red = a == 225
        if red:
            x, y = x - 30, y + 20
        b.append(f'<rect x="{x - 17:.1f}" y="{y - 8:.1f}" width="34" height="15" fill="{B_CONC_L}"/>')
        b.append(
            f'<text x="{x:.1f}" y="{y + 3:.1f}" font-family="{MONO}" font-size="10" text-anchor="middle" '
            f'fill="{B_RED if red else ink}" font-weight="{700 if red else 400}">{k * 15}°</text>'
        )
    b.append(f'<circle cx="{ox + 480 * math.cos(math.radians(225)):.1f}" cy="{oy + 480 * math.sin(math.radians(225)):.1f}" r="5" fill="{B_RED}"/>')
    # lema ao longo do raio vermelho
    px, py = ox + 560 * math.cos(math.radians(225)), oy + 560 * math.sin(math.radians(225))
    b.append(
        f'<g transform="translate({px:.1f} {py:.1f}) rotate(45) translate(0 -8)">'
        f'<text font-family="{MONO}" font-size="12" fill="{ink}" letter-spacing="1.4">OTIMIZAR · CONSTRUIR · ENTREGAR</text></g>'
    )
    b.append(wedge(W, H, 56, "br"))
    # ---------- massa: o logo, alinhado à grelha ----------
    b.append(tag(G, 50, "PROJETO Nº 001  ·  MANDACARU ENERGIA", 12))
    b.append(logo(G, G, 600, ink))
    b.append(ruler(G, G + 600, 340, step=16, major=5, h=5))
    nm, _ = block_text(G, 366, 30, "JOÃO GONÇALO", 4.0, ink, square=True, gap=0.1)
    b.append(nm)
    for i, t in enumerate(["DESENVOLVEDOR FULL-STACK", "MESTRANDO EM CIÊNCIA DA COMPUTAÇÃO", "PESQUISADOR EM PESQUISA OPERACIONAL"]):
        b.append(f'<path d="M{G} {420 + i * 20 - 4}h8" stroke="{B_RED if i == 0 else ink}" stroke-width="2"/>')
        b.append(tag(G + 18, 420 + i * 20, t, 12))
    b.append(wedge(0, 0, 30, "tl"))
    return svg(W, H, "\n".join(b), "João Gonçalo — Desenvolvedor Full-Stack, Mestrando em Ciência da Computação, Pesquisador em Pesquisa Operacional", B_DEFS + clip)


def brutal_header(num, title, sub=""):
    """Cabeçalho como linha de tabela: número | título | índice de seções."""
    W, H = 1280, 96
    ink = B_BLACK
    n = int(num)
    b = [b_concrete(W, H, grid=160, hgrid=96)]
    b.append(f'<path d="M0 1H{W}" stroke="{ink}" stroke-width="1.5"/>')
    b.append(f'<path d="M0 {H - 1}H{W}" stroke="{ink}" stroke-width="3"/>')
    b.append(f'<path d="M104 1V{H - 1}M{W - 336} 1V{H - 1}" stroke="{ink}" stroke-width="1"/>')
    b.append(wedge(0, 1, 34, "tl"))
    b.append(label(52, 66, num, 40, ink, mono=True, anchor="middle", spacing=0, weight=400))
    b.append(label(132, 62, title.upper(), 38, ink, spacing=0.2, weight=400))
    if sub:
        b.append(tag(132, 26, sub.upper(), 11))
    # índice de seções: 6 segmentos, o atual em vermelho
    b.append(tag(W - 312, 34, f"SEÇÃO {n:02d}/06", 11))
    for i in range(6):
        x = W - 312 + i * 48
        fill = B_RED if i == n - 1 else "none"
        b.append(f'<rect x="{x}" y="52" width="40" height="12" fill="{fill}" stroke="{B_RED if i == n - 1 else ink}" stroke-width="1"/>')
    return svg(W, H, "\n".join(b), title, B_DEFS)


def brutal_tech(groups):
    """Tabela: categoria | células contíguas, com linhas finas."""
    W = 1280
    LABEL_W, ROW_H = 250, 54
    ink = B_BLACK
    b, y = [], 0
    tops = [0]
    for gi, (cat, items) in enumerate(groups):
        rows, cur, cw = [], [], LABEL_W
        for it in items:
            tw = text_width(it, 19, mono=True, spacing=0.02) + 48
            if cur and cw + tw > W - 8:
                rows.append(cur)
                cur, cw = [], LABEL_W
            cur.append((it, tw))
            cw += tw
        rows.append(cur)
        h = len(rows) * ROW_H
        b.append(wedge(0, y, 16, "tl"))
        b.append(label(28, y + h / 2 + 6, cat.upper(), fit_size(cat.upper(), LABEL_W - 28 - 44, start=17, spacing=0.12), ink, spacing=0.12, weight=400))
        b.append(tag(LABEL_W - 16, y + 18, f"0{gi + 1}", 10, "end"))
        b.append(f'<path d="M{LABEL_W} {y}V{y + h}" stroke="{ink}" stroke-width="1"/>')
        for ri, row in enumerate(rows):
            ry = y + ri * ROW_H
            x = LABEL_W
            for it, tw in row:
                x += tw
                b.append(f'<path d="M{x:.0f} {ry}V{ry + ROW_H}" stroke="{ink}" stroke-width="1"/>')
                b.append(label(x - tw / 2, ry + ROW_H / 2 + 6, it, 19, ink, mono=True, anchor="middle", spacing=0.02, weight=400))
            if ri:
                b.append(f'<path d="M{LABEL_W} {ry}H{W}" stroke="{ink}" stroke-width="0.6"/>')
        y += h
        tops.append(y)
    H = y + 1
    lines = "".join(f'<path d="M0 {t + 0.5}H{W}" stroke="{ink}" stroke-width="{3 if t == tops[-1] else 1.5}"/>' for t in tops)
    body = b_concrete(W, H, grid=160, hgrid=ROW_H) + lines + "\n".join(b)
    return svg(W, H, body, "Tecnologias e ferramentas", B_DEFS)


def brutal_contact(kind, big, small):
    W, H = 620, 130
    ink = B_BLACK
    b = [b_concrete(W, H, grid=160, hgrid=130)]
    b.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="{ink}" stroke-width="1.5"/>')
    b.append(f'<path d="M{W - 150} 1V{H - 1}" stroke="{ink}" stroke-width="1"/>')
    b.append(wedge(1, 1, 30, "tl"))
    b.append(tag(40, 50, small.upper(), 12))
    b.append(label(40, 98, big.upper(), 40 if len(big) < 11 else 30, ink, spacing=0.12, weight=400))
    ax = W - 112
    b.append(f'<path d="M{ax} {H / 2}H{ax + 70}M{ax + 54} {H / 2 - 16}L{ax + 70} {H / 2}L{ax + 54} {H / 2 + 16}" fill="none" stroke="{ink}" stroke-width="1.5"/>')
    return svg(W, H, "\n".join(b), f"{big} — {small}", B_DEFS)


def brutal_footer():
    W, H = 1280, 120
    ink = B_BLACK
    b = [b_concrete(W, H, grid=160, hgrid=120)]
    b.append(f'<path d="M0 1H{W}" stroke="{ink}" stroke-width="1.5"/>')
    b.append(tag(80, 48, "OTIMIZAR  ·  CONSTRUIR  ·  ENTREGAR", 12))
    b.append(tag(W - 120, 48, "FIM  06/06", 12, "end"))
    b.append(ruler(80, W - 120, 92, step=16, major=5, h=5))
    b.append(wedge(W, H, 64, "br"))
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
