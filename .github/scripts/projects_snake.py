"""Gera uma cobrinha animada (SVG) que come um quadrado para cada repositório público.

Uso: python projects_snake.py <usuario> <pasta_saida>
Cria <pasta_saida>/projects-snake.svg (tema claro) e projects-snake-dark.svg (tema escuro).
"""
import json
import math
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

COLS = 3
CELL_W, CELL_H = 210, 54
GAP_X, GAP_Y = 24, 40
PAD_X, PAD_Y = 44, 34
SNAKE_LEN = 9
SPEED = 260          # pixels por segundo
PAUSE = 2.5          # segundos parada no fim antes de recomecar

THEMES = {
    "projects-snake.svg": {
        "cells": ["#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "text": ["#0d1117", "#0d1117", "#ffffff", "#ffffff"],
        "snake": "#8250df",
        "empty": "#ebedf0",
    },
    "projects-snake-dark.svg": {
        "cells": ["#0e4429", "#006d32", "#26a641", "#39d353"],
        "text": ["#ffffff", "#ffffff", "#0d1117", "#0d1117"],
        "snake": "#a371f7",
        "empty": "#161b22",
    },
}


def fetch_repos(user):
    url = f"https://api.github.com/users/{user}/repos?per_page=100&type=owner&sort=created&direction=asc"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        repos = json.load(r)
    return [
        r["name"] for r in repos
        if not r["fork"] and not r["private"] and r["name"].lower() != user.lower()
    ]


def label(name):
    for prefix in ("PROJETO-", "PROJETO_", "projeto-"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    name = name.replace("_", " ").replace("-", " ")
    return name if len(name) <= 22 else name[:21] + "…"


def build(names, theme):
    n = max(len(names), 1)
    rows = math.ceil(n / COLS)
    width = PAD_X * 2 + COLS * CELL_W + (COLS - 1) * GAP_X
    height = PAD_Y * 2 + rows * CELL_H + (rows - 1) * GAP_Y

    # posicoes em zigue-zague (linha 1 esquerda->direita, linha 2 direita->esquerda...)
    cells = []
    for i, name in enumerate(names):
        r, c = divmod(i, COLS)
        if r % 2 == 1:
            c = COLS - 1 - c
        x = PAD_X + c * (CELL_W + GAP_X)
        y = PAD_Y + r * (CELL_H + GAP_Y)
        cells.append((name, x, y))

    # caminho da cobrinha: passa pelo meio de cada quadrado, contornando pelas laterais entre linhas
    pts = []
    first_y = PAD_Y + CELL_H / 2
    pts.append((PAD_X / 2 - 40, first_y))
    for r in range(rows):
        cy = PAD_Y + r * (CELL_H + GAP_Y) + CELL_H / 2
        left, right = PAD_X / 2, width - PAD_X / 2
        if r % 2 == 0:
            pts += [(left, cy), (right, cy)]
        else:
            pts += [(right, cy), (left, cy)]
    last = pts[-1]
    pts.append((last[0] + (40 if rows % 2 == 1 else -40), last[1]))

    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg)

    def dist_to(px, py):
        # distancia ao longo do caminho ate o ponto (px, py) que esta sobre ele
        acc = 0.0
        for i, s in enumerate(seg):
            (x1, y1), (x2, y2) = pts[i], pts[i + 1]
            if abs(y1 - py) < 0.5 and abs(y2 - py) < 0.5 and min(x1, x2) - 0.5 <= px <= max(x1, x2) + 0.5:
                return acc + abs(px - x1)
            acc += s
        return total

    seg_gap = 16  # distancia entre os gomos da cobrinha
    travel = total / SPEED
    body_delay = seg_gap * (SNAKE_LEN - 1) / SPEED
    T = travel + body_delay + PAUSE
    move_end = travel / T

    path_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<path id="p" d="{path_d}" fill="none" stroke="none"/>',
    ]

    for i, (name, x, y) in enumerate(cells):
        lvl = i % 4
        cx = x + CELL_W / 2
        t_eat = dist_to(cx, y + CELL_H / 2) / SPEED / T
        t0, t1 = max(t_eat - 0.004, 0), min(t_eat + 0.012, 0.999)
        anim = (f'<animate attributeName="opacity" dur="{T:.2f}s" repeatCount="indefinite" '
                f'keyTimes="0;{t0:.4f};{t1:.4f};1" values="1;1;0;0"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="10" fill="{theme["empty"]}"/>')
        out.append(f'<g>{anim}'
                   f'<rect x="{x}" y="{y}" width="{CELL_W}" height="{CELL_H}" rx="10" fill="{theme["cells"][lvl]}"/>'
                   f'<text x="{cx}" y="{y + CELL_H / 2 + 5}" text-anchor="middle" '
                   f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="15" font-weight="600" '
                   f'fill="{theme["text"][lvl]}">{escape(label(name))}</text></g>')

    for k in range(SNAKE_LEN):
        delay = seg_gap * k / SPEED / T
        r = 11 - k * 0.6
        kt = f"0;{delay:.4f};{move_end + delay:.4f};1"
        out.append(f'<circle r="{r:.1f}" fill="{theme["snake"]}" opacity="{1 - k * 0.06:.2f}">'
                   f'<animateMotion dur="{T:.2f}s" repeatCount="indefinite" calcMode="linear" '
                   f'keyPoints="0;0;1;1" keyTimes="{kt}"><mpath href="#p"/></animateMotion></circle>')

    out.append("</svg>")
    return "\n".join(out)


def main():
    user, out_dir = sys.argv[1], sys.argv[2]
    names = fetch_repos(user) if len(sys.argv) < 4 else sys.argv[3].split(",")
    os.makedirs(out_dir, exist_ok=True)
    for fname, theme in THEMES.items():
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
            f.write(build(names, theme))
    print(f"{len(names)} projetos: {', '.join(names)}")


if __name__ == "__main__":
    main()
