#!/usr/bin/env python3
"""Gera o cartão de estatísticas do GitHub (assets/light/stats.svg e assets/dark/stats.svg).

    python3 scripts/gen_stats.py --user J0NGS          # lê a API (usa GITHUB_TOKEN se existir)
    python3 scripts/gen_stats.py --placeholder         # cartão com "—", sem rede
    python3 scripts/gen_stats.py --mock                # números de exemplo, só para ver o layout

Só usa dados públicos. Sem dependência de nenhuma action de terceiros.
"""
import argparse
import json
import os
import urllib.parse
import urllib.request
from collections import Counter

from jongs_svg import ASSETS, THEMES, mono, mono_width, svg

API = "https://api.github.com"


def api(path, token):
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "jongs-readme-stats"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch(user, token):
    u = api(f"/users/{user}", token)
    repos, page = [], 1
    while True:
        chunk = api(f"/users/{user}/repos?per_page=100&type=owner&page={page}", token)
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    langs = Counter()
    for r in own:
        langs.update(api(f"/repos/{user}/{r['name']}/languages", token))
    q = lambda s: urllib.parse.quote(s, safe=":+")
    return {
        "repos": u["public_repos"],
        "stars": sum(r["stargazers_count"] for r in own),
        "followers": u["followers"],
        "commits": api(f"/search/commits?q={q(f'author:{user}')}&per_page=1", token)["total_count"],
        "prs": api(f"/search/issues?q={q(f'author:{user} type:pr')}&per_page=1", token)["total_count"],
        "issues": api(f"/search/issues?q={q(f'author:{user} type:issue')}&per_page=1", token)["total_count"],
        "langs": langs.most_common(6),
    }


MOCK = {"repos": 24, "stars": 12, "followers": 18, "commits": 1342, "prs": 41, "issues": 9,
        "langs": [("Java", 540000), ("TypeScript", 310000), ("Python", 260000), ("Dart", 120000), ("Swift", 70000), ("C++", 40000)]}
PLACEHOLDER = {k: None for k in ("repos", "stars", "followers", "commits", "prs", "issues")} | {"langs": []}


def fmt(v):
    return "—" if v is None else f"{v:,}".replace(",", ".")


def card(t, d):
    W, CELL_H, ROW_H, LABEL_W = 1280, 120, 46, 250
    ink, paper = t.ink, t.paper
    stats = [("repositórios", d["repos"]), ("estrelas", d["stars"]), ("seguidores", d["followers"]),
             ("commits", d["commits"]), ("pull requests", d["prs"]), ("issues", d["issues"])]
    cw = W / 3
    b = [f'<path d="M0 1H{W}" stroke="{ink}" stroke-width="2"/>']
    for i, (name, v) in enumerate(stats):
        col, row = i % 3, i // 3
        x, y = col * cw, row * CELL_H
        inverse = (col + row) % 2 == 0
        if inverse:
            b.append(f'<rect x="{x:.0f}" y="{y}" width="{cw:.0f}" height="{CELL_H}" fill="{ink}"/>')
        fg = paper if inverse else ink
        b.append(mono(x + 24, y + 36, "// " + name, 16, fg))
        b.append(mono(x + 24, y + 98, fmt(v), 56, fg, bold=True))
        if col:
            b.append(f'<path d="M{x:.0f} {y}V{y + CELL_H}" stroke="{ink}" stroke-width="1"/>')
    y0 = 2 * CELL_H
    b.append(f'<path d="M0 {y0}H{W}" stroke="{ink}" stroke-width="2"/>')
    langs = d["langs"]
    total = sum(v for _, v in langs) or 1
    rows = max(len(langs), 1)
    h = rows * ROW_H
    b.append(f'<rect x="0" y="{y0}" width="{LABEL_W}" height="{h}" fill="{ink}"/>')
    b.append(mono(24, y0 + 36, "LINGUAGENS", 17, paper, bold=True, ls=0.08))
    b.append(mono(24, y0 + 62, "// por bytes", 14, paper))
    bar_x, bar_max = LABEL_W + 200, W - (LABEL_W + 200) - 130
    top = langs[0][1] if langs else 1
    for i, (name, v) in enumerate(langs):
        y = y0 + i * ROW_H
        b.append(mono(LABEL_W + 24, y + 30, name, 20, ink))
        b.append(f'<rect x="{bar_x}" y="{y + 12}" width="{bar_max * v / top:.0f}" height="20" fill="{ink}"/>')
        b.append(mono(W - 16, y + 30, f"{100 * v / total:.1f}%".replace(".", ","), 20, ink, "end"))
        if i:
            b.append(f'<path d="M{LABEL_W} {y}H{W}" stroke="{ink}" stroke-width="1"/>')
    if not langs:
        b.append(mono(LABEL_W + 24, y0 + 30, "—", 20, ink))
    b.append(f'<path d="M0 {y0 + h}H{W}" stroke="{ink}" stroke-width="2"/>')
    return svg(W, y0 + h + 2, "\n".join(b), "Estatísticas do GitHub", bg=paper)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="J0NGS")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--placeholder", action="store_true")
    a = ap.parse_args()
    data = MOCK if a.mock else PLACEHOLDER if a.placeholder else fetch(a.user, os.environ.get("GITHUB_TOKEN"))
    for t in THEMES:
        d = ASSETS / t.name
        d.mkdir(parents=True, exist_ok=True)
        (d / "stats.svg").write_text(card(t, data))
        print("ok", t.name)


if __name__ == "__main__":
    main()
