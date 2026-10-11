"""Motor isométrico mínimo: cajas con orden de pintado, planos para dibujar sobre caras y utilidades de color."""

import math

COS = math.cos(math.radians(30))
SIN = 0.5


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c):
    return "#" + "".join(f"{max(0, min(255, round(v))):02x}" for v in c)


def shade(color, k):
    return rgb_hex(tuple(v * k for v in hex_rgb(color)))


def mix(a, b, t):
    ra, rb = hex_rgb(a), hex_rgb(b)
    return rgb_hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


class View:
    def __init__(self, s, ox, oy):
        self.s, self.ox, self.oy = s, ox, oy

    def p(self, x, y, z):
        return (self.ox + (x - y) * COS * self.s, self.oy + (x + y) * SIN * self.s - z * self.s)

    def poly(self, pts, fill, extra="", inner=""):
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.p(*q) for q in pts))
        return f'<polygon points="{d}" fill="{fill}"{extra}>{inner}</polygon>'

    # matrices para dibujar en 2D sobre un plano; u avanza a la derecha en pantalla, v hacia abajo
    def plane_y(self, y0):
        s = self.s
        return f"matrix({COS * s:.4f},{SIN * s:.4f},0,{s},{self.ox - y0 * COS * s:.2f},{self.oy + y0 * SIN * s:.2f})"

    def plane_x(self, x0):
        s = self.s
        return f"matrix({COS * s:.4f},{-SIN * s:.4f},0,{s},{self.ox + x0 * COS * s:.2f},{self.oy + x0 * SIN * s:.2f})"

    def plane_z(self, z0):
        s = self.s
        return f"matrix({COS * s:.4f},{SIN * s:.4f},{-COS * s:.4f},{SIN * s:.4f},{self.ox:.2f},{self.oy - z0 * s:.2f})"


LIGHT = {"top": 1.0, "y": 0.78, "x": 0.6}


class Box:
    """Caja alineada a los ejes. Caras visibles: top, x (en x+w) y y (en y+d)."""

    def __init__(self, x, y, z, w, d, h, color, faces=None, extra=None):
        self.x, self.y, self.z, self.w, self.d, self.h = x, y, z, w, d, h
        self.color = color
        self.faces = faces or {}
        self.extra = extra or {}
        self.after = ""

    def bounds(self):
        return (self.x, self.y, self.z, self.x + self.w, self.y + self.d, self.z + self.h)

    def render(self, v):
        x, y, z, w, d, h = self.x, self.y, self.z, self.w, self.d, self.h
        out = []
        quads = {
            "y": [(x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)],
            "x": [(x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)],
            "top": [(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)],
        }
        for face in ("y", "x", "top"):
            fill = self.faces.get(face) or shade(self.color, LIGHT[face])
            if fill == "none":
                continue
            out.append(v.poly(quads[face], fill, self.extra.get(face, "")))
        return "".join(out) + self.after


class Sprite:
    """Contenido SVG libre que se ordena como si ocupara una caja."""

    def __init__(self, bounds, svg):
        self.b, self.svg = bounds, svg

    def bounds(self):
        return self.b

    def render(self, v):
        return self.svg


def _screen_box(v, b):
    x0, y0, z0, x1, y1, z1 = b
    pts = [v.p(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _behind(a, b):
    ax0, ay0, az0, ax1, ay1, az1 = a
    bx0, by0, bz0, bx1, by1, bz1 = b
    eps = 1e-6
    if ax1 <= bx0 + eps:
        return True
    if bx1 <= ax0 + eps:
        return False
    if ay1 <= by0 + eps:
        return True
    if by1 <= ay0 + eps:
        return False
    if az1 <= bz0 + eps:
        return True
    if bz1 <= az0 + eps:
        return False
    return (ax0 + ax1 + ay0 + ay1 + az0 + az1) < (bx0 + bx1 + by0 + by1 + bz0 + bz1)


def depth_sort(v, items):
    n = len(items)
    bnds = [it.bounds() for it in items]
    scr = [_screen_box(v, b) for b in bnds]
    after = [[] for _ in range(n)]
    indeg = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            a, b = scr[i], scr[j]
            if a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]:
                continue
            if _behind(bnds[i], bnds[j]):
                after[i].append(j)
                indeg[j] += 1
            else:
                after[j].append(i)
                indeg[i] += 1
    key = lambda k: sum(bnds[k])
    ready = sorted([i for i in range(n) if indeg[i] == 0], key=key)
    order = []
    while ready:
        i = ready.pop(0)
        order.append(i)
        for j in after[i]:
            indeg[j] -= 1
            if indeg[j] == 0:
                ready.append(j)
        ready.sort(key=key)
    if len(order) < n:  # ciclo: lo que falte, por profundidad
        rest = sorted(set(range(n)) - set(order), key=key)
        order += rest
    return [items[i] for i in order]


def render_scene(v, items):
    return "".join(it.render(v) for it in depth_sort(v, items))
