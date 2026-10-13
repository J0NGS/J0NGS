#!/usr/bin/env python3
"""Gera os SVGs do README (assets/light e assets/dark).

    pip install fonttools
    python3 scripts/build_assets.py

Estilo: brutalismo web + construtivismo russo, só preto e branco, com cara de código.
O tema escuro é o mesmo desenho com as cores trocadas (fundo transparente).
"""
import math

from jongs_svg import ASSETS, THEMES, block_text, logo, mono, mono_width, svg

LINE = 32  # passo das linhas do "editor" no banner


def banner(t):
    """Um arquivo de código: calha com números de linha, logo e uma cunha diagonal com código."""
    W, H = 1280, 480
    ink, paper = t.ink, t.paper
    b = []
    for i in range(15):
        b.append(mono(40, 22 + i * LINE, f"{i + 1:02d}", 12, ink, "end"))
    b.append(f'<path d="M56 0V{H}" stroke="{ink}" stroke-width="1"/>')

    # linhas paralelas à hipotenusa da cunha (só no lado de fora)
    x0, y0, x1, y1 = 700, 480, 1280, 40
    ln = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / ln, (y1 - y0) / ln
    nx, ny = dy, -dx
    clip = (
        f'<clipPath id="fora"><path clip-rule="evenodd" d="M0 0H{W}V{H}H0Z M{x0} {y0}L{x1} {y0}L{x1} {y1}Z"/></clipPath>'
        f'<clipPath id="dentro"><polygon points="{x0},{y0} {x1},{y0} {x1},{y1}"/></clipPath>'
        f'<clipPath id="resto"><rect x="680" y="0" width="{W - 680}" height="{H}"/></clipPath>'
    )
    par = "".join(
        f'<path d="M{x0 + nx * k * 26 - dx * 400:.1f} {y0 + ny * k * 26 - dy * 400:.1f}'
        f'L{x1 + nx * k * 26 + dx * 400:.1f} {y1 + ny * k * 26 + dy * 400:.1f}" stroke="{ink}" stroke-width="1"/>'
        for k in (1, 2, 3, 4)
    )
    b.append(f'<g clip-path="url(#resto)">{par}</g>')
    b.append(f'<polygon points="{x0},{y0} {x1},{y0} {x1},{y1}" fill="{ink}"/>')

    # círculo atravessando a hipotenusa: traço `ink` fora da cunha, `paper` dentro
    cx, cy, r = x0 + dx * 650, y0 + dy * 650, 70
    b.append(f'<g clip-path="url(#fora)"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{ink}" stroke-width="2"/></g>')
    b.append(
        f'<g clip-path="url(#dentro)"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{paper}" stroke-width="2"/>'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r - 24}" fill="{paper}"/></g>'
    )

    # código ao longo da hipotenusa
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    px, py = x0 + dx * 236, y0 + dy * 236
    code = ["const jongs = {", '  cargo: "Desenvolvedor Full-Stack",', '  atualmente: "Mandacaru Energia",', '  mestrando: "Ciência da Computação",', "};"]
    b.append(
        f'<g transform="translate({px:.1f} {py:.1f}) rotate({ang:.2f})">'
        + "".join(mono(0, 34 + i * 26, c, 17, paper, bold=True) for i, c in enumerate(code))
        + "</g>"
    )

    # coluna da esquerda
    b.append(mono(96, 22 + LINE, "$ whoami", 16, ink, bold=True))
    b.append(logo(96, 80, 560, ink))
    b.append(block_text(96, 334, 30, "JOÃO GONÇALO", 4.0, ink))
    roles = ["// desenvolvedor full-stack", "// mestrando em ciência da computação", "// pesquisador em pesquisa operacional"]
    for i, s in enumerate(roles):
        b.append(mono(96, 22 + (12 + i) * LINE, s, 16, ink))
    cur_x = 96 + mono_width(roles[-1], 16) + 8
    b.append(f'<rect x="{cur_x:.1f}" y="{22 + 14 * LINE - 14}" width="10" height="18" fill="{ink}"/>')
    return svg(W, H, "\n".join(b), "João Gonçalo — Desenvolvedor Full-Stack na Mandacaru Energia, mestrando em Ciência da Computação", clip, bg=paper)


def header(t, num, title, sub):
    """Barra com corte diagonal, no estilo '## título' de markdown."""
    W, H = 1280, 96
    ink, paper = t.ink, t.paper
    end = 124 + mono_width(title.upper(), 32, 0.06) + 56
    b = [f'<polygon points="0,18 {end:.0f},18 {end - 30:.0f},78 0,78" fill="{ink}"/>']
    b.append(mono(24, 60, num, 32, paper, bold=True))
    b.append(f'<path d="M86 30V66" stroke="{paper}" stroke-width="2"/>')
    b.append(mono(108, 60, title.upper(), 32, paper, bold=True, ls=0.06))
    b.append(f'<path d="M{end + 24:.0f} 52H{W - 170}" stroke="{ink}" stroke-width="1"/>')
    b.append(mono(end + 24, 40, "# " + sub.lower(), 16, ink))
    b.append(mono(W - 8, 58, f"// {num}/06", 18, ink, "end"))
    return svg(W, H, "\n".join(b), title, bg=paper)


def tech(t, groups):
    """Tabela: rótulo em bloco `ink` | células contíguas com linhas finas."""
    W, LABEL_W, ROW_H = 1280, 250, 56
    ink, paper = t.ink, t.paper
    b, y = [f'<path d="M0 1H{W}" stroke="{ink}" stroke-width="2"/>'], 0
    for cat, items in groups:
        rows, cur, cw = [], [], LABEL_W
        for it in items:
            tw = mono_width(it, 20) + 52
            if cur and cw + tw > W - 4:
                rows.append(cur)
                cur, cw = [], LABEL_W
            cur.append((it, tw))
            cw += tw
        rows.append(cur)
        h = len(rows) * ROW_H
        b.append(f'<rect x="0" y="{y}" width="{LABEL_W}" height="{h}" fill="{ink}"/>')
        size = 17
        while mono_width(cat.upper(), size, 0.08) > LABEL_W - 40:
            size -= 1
        b.append(mono(24, y + h / 2 + size * 0.35, cat.upper(), size, paper, bold=True, ls=0.08))
        for ri, row in enumerate(rows):
            ry, x = y + ri * ROW_H, LABEL_W
            for it, tw in row:
                x += tw
                b.append(f'<path d="M{x:.0f} {ry}V{ry + ROW_H}" stroke="{ink}" stroke-width="1"/>')
                b.append(mono(x - tw / 2, ry + ROW_H / 2 + 7, it, 20, ink, "middle"))
            if ri:
                b.append(f'<path d="M{LABEL_W} {ry}H{W}" stroke="{ink}" stroke-width="1"/>')
        b.append(f'<path d="M0 {y + h}H{W}" stroke="{ink}" stroke-width="2"/>')
        y += h
    return svg(W, y + 2, "\n".join(b), "Tecnologias e ferramentas", bg=t.paper)


def contact(t, kind, big, small):
    """Botão cru: cheio (linkedin) ou só contorno (e-mail), com o canto chanfrado."""
    W, H, c = 620, 130, 34
    ink, paper = t.ink, t.paper
    solid = kind == "linkedin"
    fg = paper if solid else ink
    pts = f"2,2 {W - c},2 {W - 2},{c} {W - 2},{H - 2} 2,{H - 2}"
    b = [f'<polygon points="{pts}" fill="{ink if solid else "none"}" stroke="{ink}" stroke-width="3"/>']
    b.append(f'<path d="M{W - 150} {H - 3}V36" stroke="{fg}" stroke-width="1"/>')
    b.append(mono(34, 52, small, 16, fg))
    b.append(mono(34, 100, big.upper(), 40 if len(big) < 11 else 30, fg, bold=True, ls=0.04))
    ax = W - 112
    b.append(f'<path d="M{ax} {H / 2 + 8}H{ax + 70}M{ax + 54} {H / 2 - 8}L{ax + 70} {H / 2 + 8}L{ax + 54} {H / 2 + 24}" fill="none" stroke="{fg}" stroke-width="3"/>')
    return svg(W, H, "\n".join(b), f"{big} — {small}", bg=t.paper)


def footer(t):
    W, H = 1280, 120
    ink, paper = t.ink, t.paper
    b = [mono(96, 40, "// fim do arquivo", 16, ink)]
    b.append(f'<polygon points="0,{H} 0,70 {W},24 {W},{H}" fill="{ink}"/>')
    b.append(mono(96, 106, "$ exit 0", 22, paper, bold=True))
    b.append(f'<rect x="{96 + mono_width("$ exit 0", 22) + 8:.1f}" y="88" width="12" height="22" fill="{paper}"/>')
    b.append(mono(W - 24, 106, "06/06", 18, paper, "end"))
    return svg(W, H, "\n".join(b), "Rodapé", bg=t.paper)


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
    ("05", "Estatísticas", "números do github", "estatisticas"),
    ("06", "Contato", "convoque-me", "contato"),
]


def main():
    for t in THEMES:
        d = ASSETS / t.name
        d.mkdir(parents=True, exist_ok=True)
        (d / "banner.svg").write_text(banner(t))
        for num, title, sub, slug in SECTIONS:
            (d / f"h-{slug}.svg").write_text(header(t, num, title, sub))
        (d / "tecnologias.svg").write_text(tech(t, TECH))
        (d / "contato-linkedin.svg").write_text(contact(t, "linkedin", "LinkedIn", "/in/jngoncalo"))
        (d / "contato-email.svg").write_text(contact(t, "email", "E-mail", "jnetogoncalo@gmail.com"))
        (d / "footer.svg").write_text(footer(t))
        print("ok", t.name)


if __name__ == "__main__":
    main()
