"""Genererar AMT Byggs mönsterbibliotek (materialmönster i loggans färger).

Kör: python3 src/patterns.py  -> assets/patterns/*.svg + assets/css/patterns.css
"""
import math, random, base64, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAVY, BLUE, GOLD = '#1b2b55', '#149eda', '#e8bd5a'


def wood(width=1200, height=1600, spacing=16, seed=7, stroke=BLUE, sw=1.1):
    """Träådring: vertikala linjer som viker undan för kvistar, som i AMT:s eget mönster."""
    rnd = random.Random(seed)
    knots = [(rnd.uniform(.1, .9) * width, rnd.uniform(.08, .92) * height, rnd.uniform(28, 70)) for _ in range(7)]
    paths = []
    n = int(width / spacing) + 6
    for i in range(-3, n):
        x0 = i * spacing
        ph = rnd.uniform(0, 6.28)
        pts = []
        for y in range(-20, height + 21, 12):
            x = x0 + 9 * math.sin(y / 260 + ph * .2) + 4 * math.sin(y / 90 + i * .35)
            for kx, ky, r in knots:
                dx, dy = x - kx, (y - ky) * .38
                d2 = dx * dx + dy * dy
                x += 1.9 * r * r * dx / (d2 + r * r * .35)
            pts.append((x, y))
        d = 'M' + ' L'.join(f'{x:.0f} {y}' for x, y in pts)
        paths.append(f'<path d="{d}"/>')
    for kx, ky, r in knots:
        for k in range(1, 5):
            rx, ry = r * .18 * k, r * .62 * k
            paths.append(f'<ellipse cx="{kx:.1f}" cy="{ky:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid slice">'
            f'<g fill="none" stroke="{stroke}" stroke-width="{sw}" vector-effect="non-scaling-stroke">' + ''.join(paths) + '</g></svg>')


def tile(w, h, body, stroke, sw=1):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<g fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="square">{body}</g></svg>')


def herringbone(stroke, u=9):
    """Fiskbensparkett 1:4. Gitter (1,1)/(4,-4) ger en kvadratisk period på 8x8 enheter."""
    L, P = 4, 8
    rects = []
    for a in range(-12, 13):
        for b in range(-4, 5):
            ox, oy = a + 4 * b, a - 4 * b
            rects.append((ox, oy, L, 1))          # liggande bräda
            rects.append((ox + L, oy - 3, 1, L))  # stående bräda
    body = ''.join(f'<rect x="{x*u}" y="{y*u}" width="{w*u}" height="{h*u}"/>'
                   for x, y, w, h in rects if -L <= x <= P and -L <= y <= P)
    return tile(P * u, P * u, body, stroke)


def studs(stroke):
    """Regelverk i fasad: reglar c/c med förskjutna kortlingar."""
    w, h, t = 96, 180, 5
    body = (f'<path d="M.5 0V{h} M{t+.5} 0V{h} M{w/2+.5} 0V{h} M{w/2+t+.5} 0V{h}"/>'
            f'<path d="M{t} 70.5H{w/2} M{t} {70.5+t}H{w/2} M{w/2+t} 125.5H{w} M{w/2+t} {125.5+t}H{w}"/>')
    return tile(w, h, body, stroke)


def brick(stroke):
    # Löpförband
    w, h = 64, 32
    body = (f'<path d="M0 .5H{w} M0 {h/2+.5}H{w}"/>'
            f'<path d="M.5 0V{h/2} M{w/2+.5} {h/2}V{h}"/>')
    return tile(w, h, body, stroke)


def hatch(stroke, gap=10):
    # Snittmarkering i A:ets vinkel (~67°)
    a = math.radians(67)
    w = gap / math.sin(a) if False else 24
    h = w * math.tan(a)
    body = f'<path d="M0 {h:.2f} L{w} 0 M{-w} {h:.2f} L0 0 M{w} {h:.2f} L{2*w} 0"/>'
    return tile(round(w, 2), round(h, 2), body, stroke)


def grid(stroke):
    w = 120
    minor = ''.join(f'M{x} 0V{w} M0 {x}H{w} ' for x in range(24, w, 24))
    body = f'<path d="{minor}" opacity=".45"/><path d="M.5 0V{w} M0 .5H{w}"/>'
    return tile(w, w, body, stroke)


def uri(svg):
    return 'url("data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode() + '")'


def main():
    pdir = os.path.join(ROOT, 'assets', 'patterns')
    os.makedirs(pdir, exist_ok=True)
    open(os.path.join(pdir, 'wood-blue.svg'), 'w').write(wood())
    open(os.path.join(pdir, 'wood-navy.svg'), 'w').write(wood(stroke=NAVY, seed=11))
    open(os.path.join(pdir, 'wood-gold.svg'), 'w').write(wood(stroke=GOLD, seed=3))
    tones = {'blue': BLUE, 'navy': NAVY, 'gold': GOLD, 'white': '#ffffff'}
    gens = {'parquet': herringbone, 'studs': studs, 'brick': brick, 'hatch': hatch, 'grid': grid}
    css = ['/* Genererad av src/patterns.py – redigera inte för hand */']
    for name, fn in gens.items():
        for tname, col in tones.items():
            css.append(f'.pat-{name}.pat--{tname}{{--pat:{uri(fn(col))}}}')
    css.append('.pat-wood.pat--blue{--pat:url("../patterns/wood-blue.svg")}')
    css.append('.pat-wood.pat--navy{--pat:url("../patterns/wood-navy.svg")}')
    css.append('.pat-wood.pat--gold{--pat:url("../patterns/wood-gold.svg")}')
    open(os.path.join(ROOT, 'assets', 'css', 'patterns.css'), 'w').write('\n'.join(css) + '\n')


if __name__ == '__main__':
    main()
