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
# ESTILO 2 — BRUTALISTA / CONSTRUTIVISTA, preto e branco, com cara de código
# ==========================================================================
INK, PAPER = "#000000", "#FFFFFF"


def mono(x, y, s, size=14, fill=INK, anchor="start", weight=400, ls=0.0):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls * size:.2f}" xml:space="preserve">{esc(s)}</text>'
    )


def brutal_banner():
    """Editor de código em cartaz: calha com números de linha, logo, e uma cunha diagonal com código."""
    W, H, LINE = 1280, 480, 32
    b = [f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    # calha do editor
    for i in range(15):
        b.append(mono(40, 22 + i * LINE, f"{i + 1:02d}", 10, anchor="end"))
    b.append(f'<path d="M56 0V{H}" stroke="{INK}" stroke-width="1"/>')
    # linhas paralelas à hipotenusa da cunha (construção, só no lado de fora)
    x0, y0, x1, y1 = 700, 480, 1280, 40
    ln = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / ln, (y1 - y0) / ln
    nx, ny = dy, -dx  # normal apontando para fora (cima-esquerda)
    clip = (
        f'<clipPath id="fora"><path clip-rule="evenodd" d="M0 0H{W}V{H}H0Z M{x0} {y0}L{x1} {y0}L{x1} {y1}Z"/></clipPath>'
        f'<clipPath id="dentro"><polygon points="{x0},{y0} {x1},{y0} {x1},{y1}"/></clipPath>'
        f'<clipPath id="resto"><rect x="680" y="0" width="{W - 680}" height="{H}"/></clipPath>'
    )
    par = []
    for k in (1, 2, 3, 4):
        o = k * 26
        par.append(
            f'<path d="M{x0 + nx * o - dx * 400:.1f} {y0 + ny * o - dy * 400:.1f}L{x1 + nx * o + dx * 400:.1f} {y1 + ny * o + dy * 400:.1f}" '
            f'stroke="{INK}" stroke-width="1"/>'
        )
    b.append(f'<g clip-path="url(#resto)">{"".join(par)}</g>')
    # a cunha
    b.append(f'<polygon points="{x0},{y0} {x1},{y0} {x1},{y1}" fill="{INK}"/>')
    # círculo atravessando a hipotenuse: preto fora da cunha, branco dentro
    cx, cy, r = x0 + dx * 650, y0 + dy * 650, 70
    b.append(f'<g clip-path="url(#fora)"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{INK}" stroke-width="2"/></g>')
    b.append(f'<g clip-path="url(#dentro)"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{PAPER}" stroke-width="2"/>'
             f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 24}" fill="{PAPER}"/></g>')
    # código ao longo da hipotenusa
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    px, py = x0 + dx * 236, y0 + dy * 236
    code = ["const jongs = {", '  cargo: "Desenvolvedor Full-Stack",', '  atualmente: "Mandacaru Energia",', '  mestrando: "Ciência da Computação",', "};"]
    t = [f'<g transform="translate({px:.1f} {py:.1f}) rotate({ang:.2f})">']
    for i, c in enumerate(code):
        t.append(mono(0, 34 + i * 26, c, 17, PAPER, weight=700))
    t.append("</g>")
    b.append("".join(t))
    # coluna da esquerda
    b.append(mono(96, 22 + LINE, "$ whoami", 14, weight=700))
    b.append(logo(96, 80, 560, INK))
    nm, _ = block_text(96, 334, 30, "JOÃO GONÇALO", 4.0, INK, square=True, gap=0.1)
    b.append(nm)
    for i, t_ in enumerate(["// desenvolvedor full-stack", "// mestrando em ciência da computação", "// pesquisador em pesquisa operacional"]):
        b.append(mono(96, 22 + (12 + i) * LINE, t_, 15))
    cur_x = 96 + len("// pesquisador em pesquisa operacional") * 9 + 8
    b.append(f'<rect x="{cur_x}" y="{22 + 14 * LINE - 14}" width="9" height="17" fill="{INK}"/>')
    return svg(W, H, "\n".join(b), "João Gonçalo — Desenvolvedor Full-Stack, Mestrando em Ciência da Computação, Pesquisador em Pesquisa Operacional", clip)


def brutal_header(num, title, sub=""):
    """Barra preta com corte diagonal, estilo '## título' de markdown."""
    W, H = 1280, 96
    tw = text_width(title.upper(), 32, mono=True, spacing=0.06)
    end = 124 + tw + 56
    b = [f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    b.append(f'<polygon points="0,18 {end:.0f},18 {end - 30:.0f},78 0,78" fill="{INK}"/>')
    b.append(mono(24, 60, num, 32, PAPER, weight=700))
    b.append(f'<path d="M86 30V66" stroke="{PAPER}" stroke-width="2"/>')
    b.append(mono(108, 60, title.upper(), 32, PAPER, weight=700, ls=0.06))
    b.append(f'<path d="M{end + 24:.0f} 48H{W - 150}" stroke="{INK}" stroke-width="1"/>')
    b.append(mono(W - 8, 54, f"// {num}/06", 15, anchor="end"))
    if sub:
        b.append(mono(end + 24, 38, "# " + sub.lower(), 12))
    return svg(W, H, "\n".join(b), title)


def brutal_tech(groups):
    """Tabela: rótulo preto | células brancas contíguas."""
    W, LABEL_W, ROW_H = 1280, 250, 56
    b, y = [], 0
    for cat, items in groups:
        rows, cur, cw = [], [], LABEL_W
        for it in items:
            tw = text_width(it, 19, mono=True) + 48
            if cur and cw + tw > W - 4:
                rows.append(cur)
                cur, cw = [], LABEL_W
            cur.append((it, tw))
            cw += tw
        rows.append(cur)
        h = len(rows) * ROW_H
        b.append(f'<rect x="0" y="{y}" width="{LABEL_W}" height="{h}" fill="{INK}"/>')
        b.append(mono(24, y + h / 2 + 5, cat.upper(), 15, PAPER, weight=700, ls=0.08))
        for ri, row in enumerate(rows):
            ry, x = y + ri * ROW_H, LABEL_W
            for it, tw in row:
                x += tw
                b.append(f'<path d="M{x:.0f} {ry}V{ry + ROW_H}" stroke="{INK}" stroke-width="1"/>')
                b.append(mono(x - tw / 2, ry + ROW_H / 2 + 6, it, 19, INK, anchor="middle"))
            if ri:
                b.append(f'<path d="M{LABEL_W} {ry}H{W}" stroke="{INK}" stroke-width="1"/>')
        b.append(f'<path d="M0 {y + h}H{W}" stroke="{INK}" stroke-width="2"/>')
        y += h
    H = y + 1
    body = f'<rect width="{W}" height="{H}" fill="{PAPER}"/><path d="M0 1H{W}" stroke="{INK}" stroke-width="2"/>' + "\n".join(b)
    return svg(W, H, body, "Tecnologias e ferramentas")


def brutal_contact(kind, big, small):
    """Botão cru: preto (linkedin) ou contornado (e-mail), com canto chanfrado."""
    W, H = 620, 130
    solid = kind == "linkedin"
    fg, bg = (PAPER, INK) if solid else (INK, PAPER)
    c = 34
    pts = f"0,0 {W - c},0 {W},{c} {W},{H} 0,{H}"
    b = [f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    b.append(f'<polygon points="{pts}" fill="{bg}" stroke="{INK}" stroke-width="3"/>')
    b.append(f'<path d="M{W - 150} {H - 3}V{36}" stroke="{fg}" stroke-width="1"/>')
    b.append(mono(34, 50, small, 14, fg))
    b.append(mono(34, 98, big.upper(), 40 if len(big) < 11 else 30, fg, weight=700, ls=0.04))
    ax = W - 112
    b.append(f'<path d="M{ax} {H / 2 + 8}H{ax + 70}M{ax + 54} {H / 2 - 8}L{ax + 70} {H / 2 + 8}L{ax + 54} {H / 2 + 24}" fill="none" stroke="{fg}" stroke-width="3"/>')
    return svg(W, H, "\n".join(b), f"{big} — {small}")


def brutal_footer():
    W, H = 1280, 120
    b = [f'<rect width="{W}" height="{H}" fill="{PAPER}"/>']
    b.append(mono(96, 40, "// fim do arquivo", 15))
    b.append(f'<polygon points="0,{H} 0,70 {W},24 {W},{H}" fill="{INK}"/>')
    b.append(mono(96, 106, "$ exit 0", 22, PAPER, weight=700))
    b.append(f'<rect x="{96 + 8 * 13.2 + 8:.0f}" y="88" width="12" height="22" fill="{PAPER}"/>')
    b.append(mono(W - 24, 106, "06/06", 15, PAPER, anchor="end"))
    return svg(W, H, "\n".join(b), "Rodapé")


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
