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

COLS, ROWS = 53, 7       # mesma grade do grafico de contribuicoes do GitHub
STEP, SIZE = 15, 11       # distancia entre quadradinhos e tamanho de cada um
PAD = 14
SPEED = 120               # pixels por segundo
PAUSE = 2.0               # segundos parada no fim antes de recomecar
SNAKE = [11, 10, 9, 8]    # tamanho de cada gomo da cobrinha

THEMES = {
    "projects-snake.svg": {
        "greens": ["#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "empty": "#ebedf0",
        "snake": "#800080",
    },
    "projects-snake-dark.svg": {
        "greens": ["#0e4429", "#006d32", "#26a641", "#39d353"],
        "empty": "#161b22",
        "snake": "#800080",
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


def seed(name):
    return sum((i + 1) * ord(ch) for i, ch in enumerate(name))


def build(names, theme):
    width = PAD * 2 + COLS * STEP
    height = PAD * 2 + ROWS * STEP
    n = len(names)

    def center(col, row):
        return PAD + col * STEP + STEP / 2, PAD + row * STEP + STEP / 2

    # um quadradinho verde por projeto, espalhados pela grade
    targets = []
    for i, name in enumerate(names):
        col = min(COLS - 1, int((i + 0.5) * COLS / max(n, 1)))
        row = seed(name) % ROWS
        targets.append((col, row, 1 + seed(name[::-1]) % 3, name))

    # caminho da cobrinha: anda pela grade ate cada quadradinho verde
    pts = [center(-2, targets[0][1] if targets else 3)]
    for col, row, _, _ in targets:
        x, y = center(col, row)
        px, py = pts[-1]
        if abs(py - y) > 0.1:
            pts.append((px, y))
        pts.append((x, y))
    pts.append((center(COLS + 2, 0)[0], pts[-1][1]))

    total = sum(math.dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))
    # distancia ao longo do caminho ate cada quadradinho verde
    target_pts = [center(c, r) for c, r, _, _ in targets]
    dist_of = {}
    acc = 0.0
    for i in range(1, len(pts)):
        acc += math.dist(pts[i - 1], pts[i])
        dist_of.setdefault(pts[i], acc)

    gap = STEP
    travel = total / SPEED
    T = travel + gap * len(SNAKE) / SPEED + PAUSE
    move_end = travel / T

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<path id="p" d="M ' + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + '" fill="none"/>',
    ]
    for col in range(COLS):
        for row in range(ROWS):
            x, y = PAD + col * STEP + (STEP - SIZE) / 2, PAD + row * STEP + (STEP - SIZE) / 2
            out.append(f'<rect x="{x}" y="{y}" width="{SIZE}" height="{SIZE}" rx="2" fill="{theme["empty"]}"/>')

    for (col, row, lvl, name), tp in zip(targets, target_pts):
        x, y = PAD + col * STEP + (STEP - SIZE) / 2, PAD + row * STEP + (STEP - SIZE) / 2
        t = dist_of.get(tp, total) / SPEED / T
        t0, t1 = max(t - 0.002, 0), min(t + 0.004, 0.999)
        out.append(f'<rect x="{x}" y="{y}" width="{SIZE}" height="{SIZE}" rx="2" fill="{theme["greens"][lvl]}">'
                   f'<title>{escape(name)}</title>'
                   f'<animate attributeName="opacity" dur="{T:.2f}s" repeatCount="indefinite" '
                   f'keyTimes="0;{t0:.4f};{t1:.4f};1" values="1;1;0;0"/></rect>')

    for k, size in enumerate(SNAKE):
        delay = gap * k / SPEED / T * 0.8
        kt = f"0;{delay:.4f};{move_end + delay:.4f};1"
        out.append(f'<rect x="{-size / 2}" y="{-size / 2}" width="{size}" height="{size}" rx="{size / 2.5:.1f}" '
                   f'fill="{theme["snake"]}">'
                   f'<animateMotion dur="{T:.2f}s" repeatCount="indefinite" calcMode="linear" '
                   f'keyPoints="0;0;1;1" keyTimes="{kt}"><mpath href="#p"/></animateMotion></rect>')

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
