"""Gráficos em SVG gerados no servidor. Sem bibliotecas, sem CDN."""

from markupsafe import Markup, escape

from .fmt import brl, brl_curto

L, A = 720, 240           # largura e altura do viewBox
ME, MD, MT, MB = 52, 12, 16, 28   # margens: esquerda, direita, topo, base


def _escala(minimo, maximo, passos=4):
    if minimo == maximo:
        maximo = minimo + 100
    bruto = (maximo - minimo) / passos
    mag = 10 ** (len(str(int(abs(bruto)))) - 1) if bruto >= 1 else 1
    for m in (1, 2, 2.5, 5, 10):
        passo = m * mag
        if passo >= bruto:
            break
    ini = (minimo // passo) * passo
    fim = -(-maximo // passo) * passo
    ticks = []
    v = ini
    while v <= fim + 1e-9:
        ticks.append(v)
        v += passo
    return ini, fim, ticks


def _eixo_y(ticks, y, fmt):
    partes = []
    for t in ticks:
        yy = y(t)
        classe = "zero" if t == 0 else "grade"
        partes.append(f'<line class="{classe}" x1="{ME}" x2="{L - MD}" y1="{yy:.1f}" y2="{yy:.1f}"/>')
        partes.append(f'<text class="rot-y" x="{ME - 8}" y="{yy + 4:.1f}" text-anchor="end">{escape(fmt(t))}</text>')
    return partes


def barras(rotulos, series, altura=A, formatar=brl_curto, mostrar_cada=1):
    """series: [(nome, valores, classe_css)]. Valores em centavos; aceita negativos."""
    todos = [v for _, vals, _ in series for v in vals] or [0]
    ini, fim, ticks = _escala(min(0, min(todos)), max(0, max(todos)))
    h_util = altura - MT - MB
    y = lambda v: MT + (fim - v) / (fim - ini) * h_util
    n = max(len(rotulos), 1)
    largura_grupo = (L - ME - MD) / n
    k = len(series)
    gap = largura_grupo * 0.28
    lb = max(2.0, (largura_grupo - gap) / k)
    raio = min(5.0, lb / 2.5)

    partes = [f'<svg class="grafico" viewBox="0 0 {L} {altura}" role="img">']
    partes += _eixo_y(ticks, y, formatar)
    for i, rot in enumerate(rotulos):
        x0 = ME + i * largura_grupo + gap / 2
        for j, (nome, vals, classe) in enumerate(series):
            v = vals[i] if i < len(vals) else 0
            if not v:
                continue
            x = x0 + j * lb
            topo, base = (y(v), y(0)) if v > 0 else (y(0), y(v))
            hh = max(base - topo, 1.0)
            r = min(raio, hh / 2)
            if v > 0:
                d = (f"M{x:.1f},{base:.1f} V{topo + r:.1f} Q{x:.1f},{topo:.1f} {x + r:.1f},{topo:.1f} "
                     f"H{x + lb - 1 - r:.1f} Q{x + lb - 1:.1f},{topo:.1f} {x + lb - 1:.1f},{topo + r:.1f} V{base:.1f} Z")
            else:
                d = (f"M{x:.1f},{topo:.1f} V{base - r:.1f} Q{x:.1f},{base:.1f} {x + r:.1f},{base:.1f} "
                     f"H{x + lb - 1 - r:.1f} Q{x + lb - 1:.1f},{base:.1f} {x + lb - 1:.1f},{base - r:.1f} V{topo:.1f} Z")
            partes.append(f'<path class="{classe}" d="{d}"><title>{escape(rot)} · {escape(nome)}: {escape(brl(v))}</title></path>')
        if i % mostrar_cada == 0:
            cx = ME + i * largura_grupo + largura_grupo / 2
            partes.append(f'<text class="rot-x" x="{cx:.1f}" y="{altura - 8}" text-anchor="middle">{escape(rot)}</text>')
    partes.append("</svg>")
    return Markup("".join(partes))


def linhas(rotulos, series, altura=A, formatar=brl_curto, mostrar_cada=1):
    """series: [(nome, valores com None nos buracos, classe_css)]."""
    todos = [v for _, vals, _ in series for v in vals if v is not None] or [0]
    ini, fim, ticks = _escala(min(0, min(todos)), max(todos))
    h_util = altura - MT - MB
    y = lambda v: MT + (fim - v) / (fim - ini) * h_util
    n = max(len(rotulos), 1)
    passo = (L - ME - MD) / max(n - 1, 1)
    x = lambda i: ME + i * passo

    partes = [f'<svg class="grafico" viewBox="0 0 {L} {altura}" role="img">']
    partes += _eixo_y(ticks, y, formatar)
    for nome, vals, classe in series:
        pontos = [(x(i), y(v), v, rotulos[i]) for i, v in enumerate(vals) if v is not None]
        if not pontos:
            continue
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py, _, _ in pontos)
        if "area" in classe:
            area = d + f" L{pontos[-1][0]:.1f},{y(max(ini, 0)):.1f} L{pontos[0][0]:.1f},{y(max(ini, 0)):.1f} Z"
            partes.append(f'<path class="{classe} preench" d="{area}"/>')
        partes.append(f'<path class="{classe} traco" d="{d}"/>')
        for px, py, v, rot in pontos:
            partes.append(f'<circle class="{classe} ponto" cx="{px:.1f}" cy="{py:.1f}" r="7">'
                          f'<title>{escape(rot)} · {escape(nome)}: {escape(brl(v))}</title></circle>')
    for i, rot in enumerate(rotulos):
        if i % mostrar_cada == 0:
            partes.append(f'<text class="rot-x" x="{x(i):.1f}" y="{altura - 8}" text-anchor="middle">{escape(rot)}</text>')
    partes.append("</svg>")
    return Markup("".join(partes))
