"""Genera las placas SVG del perfil y el README a partir de profile.json.

Uso:  python scripts/build.py
Requiere: fonttools y brotli (pip install fonttools brotli)
"""

import base64
import io
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scene import office, product_object  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT_DIR = ROOT / "scripts" / "fonts"

FONTS = {
    "af8": ("AF8", "archivo-expanded-800.woff2"),
    "as6": ("AS6", "archivo-semiexpanded-600.woff2"),
    "gs4": ("GS4", "geist-sans-latin-400-normal.woff2"),
    "gs5": ("GS5", "geist-sans-latin-500-normal.woff2"),
    "gm4": ("GM4", "geist-mono-latin-400-normal.woff2"),
    "gm5": ("GM5", "geist-mono-latin-500-normal.woff2"),
}

C = {
    "fondo": "#0C0F16",
    "superficie": "#121722",
    "borde": "#1F2635",
    "regla": "#232B3B",
    "texto": "#EEEAE2",
    "texto2": "#8D96A6",
    "acento": "#FFB547",
    "apoyo": "#6FE3D0",
    "verde": "#3FB950",
}

W = 880
_metrics = {}


def _font(key):
    if key not in _metrics:
        f = TTFont(FONT_DIR / FONTS[key][1])
        _metrics[key] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    return _metrics[key]


def text_width(s, key, size, spacing=0.0):
    cmap, hmtx, upm = _font(key)
    total = sum(hmtx[cmap[ord(ch)]][0] if ord(ch) in cmap else upm * 0.6 for ch in s)
    return total / upm * size + spacing * len(s)


def wrap(s, key, size, max_w):
    lines, cur = [], ""
    for w in s.split():
        test = f"{cur} {w}".strip()
        if text_width(test, key, size) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def _subset_b64(key, chars):
    f = TTFont(FONT_DIR / FONTS[key][1])
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []
    s = subset.Subsetter(opts)
    s.populate(text=chars + " ")
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.parts, self.used = [], {}

    def add(self, *s):
        self.parts.extend(s)

    def text(self, x, y, s, font, size, fill, anchor="start", spacing=0, extra=""):
        self.used.setdefault(font, set()).update(s)
        an = f' text-anchor="{anchor}"' if anchor != "start" else ""
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        return (
            f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONTS[font][0]}" font-size="{size}" '
            f'fill="{fill}"{an}{ls}{extra}>{escape(s)}</text>'
        )

    def render(self):
        faces = "".join(
            f"@font-face{{font-family:{FONTS[k][0]};src:url(data:font/woff2;base64,{_subset_b64(k, ''.join(sorted(ch)))}) format('woff2')}}"
            for k, ch in self.used.items()
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
            f'role="img" aria-label="{escape(self.title)}"><title>{escape(self.title)}</title>'
            f"<style>{faces}</style>{''.join(self.parts)}</svg>"
        )


def plate(svg, rx=22, fill=None):
    w, h = svg.w, svg.h
    svg.add(
        '<defs><filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>'
        '<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.05 0"/></filter>'
        f'<clipPath id="plate"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath></defs>',
        f'<rect width="{w}" height="{h}" rx="{rx}" fill="{fill or C["fondo"]}"/>',
    )


def plate_end(svg, rx=22):
    w, h = svg.w, svg.h
    svg.add(
        f'<rect width="{w}" height="{h}" rx="{rx}" filter="url(#grain)" opacity="0.9"/>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx - 0.5}" fill="none" stroke="{C["borde"]}"/>',
    )


def arrow(x, y, color, size=7):
    return (
        f'<path d="M{x - size} {y + size} L{x + size} {y - size} M{x - size * 0.4} {y - size} L{x + size} {y - size} L{x + size} {y + size * 0.4}" '
        f'fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
    )


# ---------------------------------------------------------------- placas

def hero(p):
    H = 600
    svg = Svg(W, H, f"{p['name']}, {p['role']}")
    plate(svg)
    svg.add(
        '<defs><radialGradient id="halo" cx="0.66" cy="0.48" r="0.6">'
        '<stop offset="0" stop-color="#1A2236"/><stop offset="1" stop-color="#0C0F16" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="vig" cx="0.5" cy="0.5" r="0.75"><stop offset="0.6" stop-color="#000" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#000" stop-opacity="0.45"/></radialGradient></defs>',
        f'<rect width="{W}" height="{H}" fill="url(#halo)" clip-path="url(#plate)"/>',
        f'<g clip-path="url(#plate)">{office(svg, s=16, ox=566, oy=238)}</g>',
        f'<rect width="{W}" height="{H}" rx="22" fill="url(#vig)"/>',
    )

    # marca
    svg.add(f'<rect x="48" y="46" width="30" height="30" rx="7" fill="{C["acento"]}"/>')
    svg.add(svg.text(63, 66.5, "IF", "af8", 13, C["fondo"], anchor="middle"))
    svg.add(svg.text(90, 66, p["company"], "gs5", 14, C["texto"]))

    # nombre y tesis
    first, last = p["name"].split(" ", 1)
    svg.add(svg.text(46, 176, first, "af8", 54, C["texto"], spacing=-1.2))
    svg.add(svg.text(46, 236, last, "af8", 54, C["texto"], spacing=-1.2))
    y = 292
    for line in p["hero_lines"]:
        svg.add(svg.text(48, y, line, "gs5", 19, C["texto"]))
        y += 27
    y += 20
    for line in wrap(p["hero_role"], "gs4", 14.5, 250):
        svg.add(svg.text(48, y, line, "gs4", 14.5, C["texto2"]))
        y += 22

    # pie de figura
    svg.add(f'<line x1="48" y1="560" x2="{W - 48}" y2="560" stroke="{C["regla"]}"/>')
    svg.add(svg.text(48, 582, "Fig. 1", "gm5", 11, C["acento"]))
    svg.add(svg.text(98, 582, p["hero_caption"], "gm4", 11, C["texto2"]))
    svg.add(svg.text(W - 48, 582, p["hero_caption_right"], "gm4", 11, C["texto2"], anchor="end"))
    plate_end(svg)
    return svg.render()


def manifesto(p):
    H = 356
    svg = Svg(W, H, p["statement"][0] + " " + p["statement"][1])
    plate(svg)
    svg.add(svg.text(48, 104, p["statement"][0], "as6", 36, C["texto"], spacing=-0.6))
    svg.add(svg.text(48, 152, p["statement"][1], "as6", 36, C["texto2"], spacing=-0.6))
    svg.add(f'<line x1="48" y1="200" x2="{W - 48}" y2="200" stroke="{C["regla"]}"/>')
    col_w = (W - 96) / len(p["facts"])
    for i, (num, label) in enumerate(p["facts"]):
        x = 48 + i * col_w
        svg.add(svg.text(x, 262, num, "af8", 40, C["acento"] if i == 0 else C["texto"], spacing=-1))
        for j, line in enumerate(wrap(label, "gs4", 14, col_w - 28)):
            svg.add(svg.text(x, 292 + j * 21, line, "gs4", 14, C["texto2"]))
    plate_end(svg)
    return svg.render()


def featured(f):
    """Placa destacada: el resultado en grande, la semana animada y el diagrama de ruteo."""
    H = 664
    svg = Svg(W, H, f["name"])
    plate(svg)
    rojo = "#F85149"
    svg.add(
        '<defs><radialGradient id="halo2" cx="0.8" cy="0.35" r="0.6">'
        '<stop offset="0" stop-color="#18213A"/><stop offset="1" stop-color="#0C0F16" stop-opacity="0"/></radialGradient>'
        '<filter id="brillo" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>'
        f'<pattern id="rayas" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="3" height="8" fill="#F85149" fill-opacity="0.22"/></pattern></defs>',
        f'<rect width="{W}" height="{H}" fill="url(#halo2)" clip-path="url(#plate)"/>',
    )

    # etiqueta
    color = C["apoyo"]
    svg.add(
        f'<circle cx="52" cy="36" r="3.5" fill="{color}"/><circle cx="52" cy="36" r="3.5" fill="none" stroke="{color}">'
        '<animate attributeName="r" values="3.5;9" dur="2.2s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="0.8;0" dur="2.2s" repeatCount="indefinite"/></circle>'
    )
    svg.add(svg.text(64, 40, f["badge"], "gm5", 11, color))
    svg.add(svg.text(W - 48, 40, f"Fig. 2 · {f['name']}", "gm4", 11, C["texto2"], anchor="end"))

    # titular
    l1, pre, num, post = f["headline"]
    size, sp = 32, -0.6
    svg.add(svg.text(48, 102, l1, "as6", size, C["texto2"], spacing=sp))
    x = 48
    for part, col in ((pre, C["texto"]), (num, C["acento"]), (post, C["texto"])):
        lead = len(part) - len(part.lstrip(" "))
        x += text_width(" " * lead, "as6", size, sp)
        svg.add(svg.text(x, 146, part.strip(" "), "as6", size, col, spacing=sp))
        x += text_width(part.lstrip(" "), "as6", size, sp)
    for j, line in enumerate(wrap(f["desc"], "gs4", 15, 640)):
        svg.add(svg.text(48, 184 + j * 23, line, "gs4", 15, C["texto2"]))

    # ---- la semana: dos medidores que corren al mismo reloj
    T = 8.0            # duración del ciclo
    run = 6.3          # lo que tarda la semana en correr
    day = run / 7
    kt = lambda t: f"{t / T:.4f}"
    top = 238
    svg.add(f'<line x1="48" y1="{top}" x2="{W - 48}" y2="{top}" stroke="{C["regla"]}"/>')
    svg.add(svg.text(48, top + 34, f["week_title"], "gs5", 15, C["texto"]))
    svg.add(svg.text(48, top + 54, f["week_note"], "gm4", 11, C["texto2"]))

    tx0, tx1 = 236, W - 48
    cw = (tx1 - tx0) / 7
    # días
    for i, d in enumerate(f["days"]):
        cx = tx0 + cw * i + cw / 2
        svg.add(svg.text(cx, top + 40, d, "gm5", 12, C["texto2"], anchor="middle"))
    hl_vals = ";".join(f"{tx0 + cw * min(i, 6) + 6:.1f}" for i in range(8))
    hl_keys = ";".join(kt(min(i * day, run)) for i in range(7)) + ";1"
    svg.add(
        f'<rect y="{top + 22}" width="{cw - 12:.1f}" height="26" rx="7" fill="none" stroke="{C["acento"]}" stroke-opacity="0.8">'
        f'<animate attributeName="x" values="{hl_vals}" keyTimes="{hl_keys}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></rect>'
    )

    rows = [
        (f["rows"][0], top + 92, rojo, 1.0, 4.5),
        (f["rows"][1], top + 150, C["apoyo"], 0.6, 7.0),
    ]
    for (label, sub, end_text), ry, col, frac, days_to in rows:
        svg.add(svg.text(48, ry + 4, label, "gs5", 14, C["texto"]))
        svg.add(svg.text(48, ry + 22, sub, "gm4", 11, C["texto2"]))
        svg.add(f'<rect x="{tx0}" y="{ry - 8}" width="{tx1 - tx0}" height="16" rx="8" fill="{C["superficie"]}" stroke="{C["borde"]}"/>')
        full = (tx1 - tx0) * frac
        t_end = days_to * day
        svg.add(
            f'<rect x="{tx0}" y="{ry - 8}" height="16" rx="8" fill="{col}" width="0">'
            f'<animate attributeName="width" values="0;{full:.1f};{full:.1f};0" keyTimes="0;{kt(t_end)};{kt(T - 0.25)};1" '
            f'dur="{T}s" repeatCount="indefinite"/></rect>'
        )
        if frac >= 1:
            # el plan se acaba: el resto de la semana queda bloqueado
            lock_x = tx0 + cw * days_to
            svg.add(
                f'<rect x="{lock_x:.1f}" y="{top + 20}" width="{tx1 - lock_x:.1f}" height="30" rx="8" fill="url(#rayas)" '
                f'stroke="{rojo}" stroke-opacity="0.5" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{kt(t_end)};{kt(t_end + 0.15)};{kt(T - 0.25)};1" '
                f'dur="{T}s" repeatCount="indefinite"/></rect>'
            )
            svg.add(
                f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;0.35;1;0.35;1;1;0" '
                f'keyTimes="0;{kt(t_end)};{kt(t_end + 0.1)};{kt(t_end + 0.4)};{kt(t_end + 0.7)};{kt(t_end + 1.0)};{kt(t_end + 1.3)};{kt(T - 0.25)};1" '
                f'dur="{T}s" repeatCount="indefinite"/>'
                + svg.text(tx1, ry - 16, end_text, "gm5", 11, rojo, anchor="end")
                + "</g>"
            )
        else:
            svg.add(
                f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" '
                f'keyTimes="0;{kt(t_end - 0.1)};{kt(t_end + 0.2)};{kt(T - 0.25)};1" dur="{T}s" repeatCount="indefinite"/>'
                + svg.text(tx1, ry - 16, end_text, "gm5", 11, col, anchor="end")
                + "</g>"
            )

    # ---- el ruteo: cada pedido viaja a su carril
    dtop = top + 196
    svg.add(f'<line x1="48" y1="{dtop}" x2="{W - 48}" y2="{dtop}" stroke="{C["regla"]}"/>')
    lane_y = {"sonnet": dtop + 52, "opus": dtop + 128}
    lane_c = {"sonnet": C["apoyo"], "opus": C["acento"]}
    nx0, nx1, ny = 368, 516, dtop + 90
    lx = 640
    chip_h, gap, y0 = 28, 38, dtop + 20
    D = 3.6
    paths = []
    for i, (req, lane) in enumerate(f["requests"]):
        cy = y0 + i * gap + chip_h / 2
        tw = text_width(req, "gm4", 12)
        cwid = tw + 26
        col = lane_c[lane]
        b = i * D / 4
        svg.add(
            f'<rect x="48" y="{cy - chip_h / 2:.1f}" width="{cwid:.1f}" height="{chip_h}" rx="8" '
            f'fill="{C["superficie"]}" stroke="{C["borde"]}"/>',
            f'<rect x="48" y="{cy - chip_h / 2:.1f}" width="{cwid:.1f}" height="{chip_h}" rx="8" fill="none" stroke="{col}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;0;0" keyTimes="0;0.05;0.3;1" dur="{D}s" begin="{b:.2f}s" repeatCount="indefinite"/></rect>',
        )
        svg.add(svg.text(61, cy + 4.3, req, "gm4", 12, C["texto"]))
        x0 = 48 + cwid
        mid = (x0 + nx0) / 2
        svg.add(
            f'<path d="M{x0:.1f} {cy:.1f} C{mid:.1f} {cy:.1f} {mid:.1f} {ny} {nx0} {ny}" fill="none" stroke="{C["regla"]}" stroke-width="1.3"/>'
        )
        ty = lane_y[lane]
        m2 = (nx1 + lx) / 2
        path = f"M{x0:.1f} {cy:.1f} C{mid:.1f} {cy:.1f} {mid:.1f} {ny} {nx0} {ny} L{nx1} {ny} C{m2:.1f} {ny} {m2:.1f} {ty} {lx} {ty}"
        paths.append((path, col, b))

    for lane, ty in lane_y.items():
        m2 = (nx1 + lx) / 2
        svg.add(
            f'<path d="M{nx1} {ny} C{m2:.1f} {ny} {m2:.1f} {ty} {lx} {ty}" fill="none" stroke="{lane_c[lane]}" '
            'stroke-width="1.4" stroke-opacity="0.55"/>'
        )

    # clasificador
    name, sub = f["classifier"]
    svg.add(
        f'<rect x="{nx0}" y="{ny - 30}" width="{nx1 - nx0}" height="60" rx="12" fill="{C["superficie"]}" stroke="{C["regla"]}"/>'
    )
    cx = (nx0 + nx1) / 2
    svg.add(svg.text(cx, ny - 3, name, "gs5", 16, C["texto"], anchor="middle"))
    svg.add(svg.text(cx, ny + 17, sub, "gm4", 11, C["texto2"], anchor="middle"))

    # carriles, con un destello cuando llega cada pedido
    for lane, ty in lane_y.items():
        title, note, effort = f["lanes"][lane]
        col = lane_c[lane]
        llegadas = [b for (_, c, b) in paths if c == col]
        svg.add(
            f'<rect x="{lx}" y="{ty - 30}" width="{W - 48 - lx}" height="60" rx="12" fill="{C["superficie"]}" stroke="{C["borde"]}"/>'
        )
        for b in llegadas:
            svg.add(
                f'<rect x="{lx}" y="{ty - 30}" width="{W - 48 - lx}" height="60" rx="12" fill="{col}" fill-opacity="0.08" stroke="{col}" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;1;0" keyTimes="0;0.9;0.94;1" dur="{D}s" begin="{b:.2f}s" repeatCount="indefinite"/></rect>'
            )
        svg.add(f'<rect x="{lx}" y="{ty - 18}" width="3" height="36" rx="1.5" fill="{col}"/>')
        svg.add(svg.text(lx + 18, ty - 2, title, "as6", 18, C["texto"], spacing=-0.2))
        svg.add(svg.text(lx + 18, ty + 17, note, "gm4", 11, C["texto2"]))
        svg.add(svg.text(W - 64, ty - 2, effort, "gm4", 11, col, anchor="end"))

    # puntos que viajan (encima de todo)
    for path, col, b in paths:
        for r, op, extra in ((8, 0.35, ' filter="url(#brillo)"'), (3.6, 1, "")):
            svg.add(
                f'<circle r="{r}" fill="{col}" opacity="0"{extra}><animateMotion dur="{D}s" begin="{b:.2f}s" '
                f'repeatCount="indefinite" path="{path}"/>'
                f'<animate attributeName="opacity" values="0;{op};{op};0" keyTimes="0;0.06;0.92;1" dur="{D}s" '
                f'begin="{b:.2f}s" repeatCount="indefinite"/></circle>'
            )

    # pie: la línea de estado cambia con cada pedido
    svg.add(f'<line x1="48" y1="{H - 50}" x2="{W - 48}" y2="{H - 50}" stroke="{C["regla"]}"/>')
    svg.add(f'<rect x="48" y="{H - 30}" width="7" height="7" rx="1.5" fill="{C["acento"]}"/>')
    n = len(f["statuses"])
    for i, s in enumerate(f["statuses"]):
        on = ["0"] * n
        on[i] = "1"
        vals = ";".join(on + [on[0]])
        keys = ";".join(f"{k / n:.4f}" for k in range(n)) + ";1"
        svg.add(
            f'<g opacity="{on[0] if i == 0 else 0}"><animate attributeName="opacity" values="{vals}" keyTimes="{keys}" '
            f'calcMode="discrete" dur="{D}s" begin="{D:.2f}s" repeatCount="indefinite"/>'
            + svg.text(63, H - 23, s, "gm4", 11, C["texto2"])
            + "</g>"
        )
    cta = f["cta"]
    svg.add(svg.text(W - 72, H - 23, cta, "gm5", 12, C["texto"], anchor="end"))
    svg.add(arrow(W - 56, H - 27, C["acento"], 5))
    plate_end(svg)
    return svg.render()


def product(d, i):
    w, h = 432, 336
    svg = Svg(w, h, d["name"])
    plate(svg, rx=20, fill=C["superficie"])
    svg.add(
        '<defs><radialGradient id="spot" cx="0.5" cy="0.38" r="0.55">'
        f'<stop offset="0" stop-color="#202942"/><stop offset="1" stop-color="{C["superficie"]}" stop-opacity="0"/></radialGradient></defs>',
        f'<rect width="{w}" height="200" fill="url(#spot)"/>',
        product_object(svg, d["object"], w / 2, 120, 250, 128),
    )
    live = d["status"] in ("live", "open")
    color = C["verde"] if d["status"] == "live" else C["apoyo"] if d["status"] == "open" else C["acento"]
    label = {"live": "En producción", "open": "Código abierto"}.get(d["status"], "Próximamente")
    if live:
        svg.add(
            f'<circle cx="30" cy="34" r="3.5" fill="{color}"/><circle cx="30" cy="34" r="3.5" fill="none" stroke="{color}">'
            '<animate attributeName="r" values="3.5;9" dur="2.2s" repeatCount="indefinite"/>'
            '<animate attributeName="opacity" values="0.8;0" dur="2.2s" repeatCount="indefinite"/></circle>'
        )
    else:
        svg.add(f'<circle cx="30" cy="34" r="3.5" fill="none" stroke="{color}" stroke-width="1.5"/>')
    svg.add(svg.text(42, 38, label, "gm5", 11, color))
    svg.add(svg.text(w - 24, 38, f"0{i + 1}", "gm4", 11, C["texto2"], anchor="end"))
    svg.add(svg.text(24, 232, d["name"], "as6", 22, C["texto"], spacing=-0.3))
    for j, line in enumerate(wrap(d["desc"], "gs4", 14, w - 48)[:2]):
        svg.add(svg.text(24, 260 + j * 21, line, "gs4", 14, C["texto2"]))
    svg.add(f'<line x1="24" y1="298" x2="{w - 24}" y2="298" stroke="{C["regla"]}"/>')
    svg.add(svg.text(24, 320, d["label"], "gm4", 12, C["texto"]))
    svg.add(arrow(w - 32, 315, C["texto2"], 5))
    plate_end(svg, rx=20)
    return svg.render()


def stack(p):
    rows = p["stack"]
    H = 120 + 54 * len(rows) + 14
    svg = Svg(W, H, "Con qué construyo")
    plate(svg)
    svg.add(svg.text(48, 78, p["stack_title"], "as6", 26, C["texto"], spacing=-0.4))
    svg.add(svg.text(W - 48, 78, p["stack_note"], "gs4", 14, C["texto2"], anchor="end"))
    y = 120
    for label, items in rows:
        svg.add(f'<line x1="48" y1="{y}" x2="{W - 48}" y2="{y}" stroke="{C["regla"]}"/>')
        svg.add(svg.text(48, y + 33, label, "gm4", 12, C["texto2"]))
        svg.add(svg.text(200, y + 34, ", ".join(items), "gs5", 16, C["texto"]))
        y += 54
    plate_end(svg)
    return svg.render()


def log_header(p):
    H = 132
    svg = Svg(W, H, p["log_title"])
    plate(svg)
    svg.add(svg.text(48, 62, p["log_title"], "as6", 26, C["texto"], spacing=-0.4))
    svg.add(svg.text(48, 94, p["log_note"], "gs4", 14, C["texto2"]))
    svg.add(
        f'<circle cx="{W - 60}" cy="57" r="4" fill="{C["apoyo"]}"><animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/></circle>'
    )
    svg.add(svg.text(W - 74, 61, "automático, cada lunes", "gm4", 11, C["texto2"], anchor="end"))
    plate_end(svg)
    return svg.render()


def contact(c):
    w, h = 284, 92
    svg = Svg(w, h, f"{c['label']}: {c['value']}")
    plate(svg, rx=18, fill=C["superficie"])
    svg.add(svg.text(22, 36, c["label"], "gm4", 11, C["texto2"]))
    svg.add(svg.text(22, 64, c["value"], "gs5", 16, C["texto"]))
    svg.add(arrow(w - 30, 48, C["acento"], 6))
    plate_end(svg, rx=18)
    return svg.render()


# ---------------------------------------------------------------- README

CHANGELOG_DEFAULT = "_Todavía no hay corridas: el primer resumen llega el lunes después del primer commit público._"


def img(name, alt, width="100%"):
    return f'<img src="assets/{name}.svg" alt="{escape(alt)}" width="{width}">'


def readme(p):
    path = ROOT / "README.md"
    block = CHANGELOG_DEFAULT
    if path.exists():
        m = re.search(r"<!-- changelog:start -->\n(.*?)\n<!-- changelog:end -->", path.read_text(), re.S)
        if m and "Todavía no hay corridas" not in m.group(1) and "> " not in m.group(1)[:2]:
            block = m.group(1)

    prods = [
        f'<a href="{d["url"]}">{img(f"producto-{i + 1}", d["name"] + ": " + d["desc"], "49%")}</a>'
        for i, d in enumerate(p["deployments"])
    ]
    rows = "\n\n".join(f'<p align="center">\n{prods[i]}\n{prods[i + 1]}\n</p>' for i in range(0, len(prods), 2))
    links = "\n".join(
        f'<a href="{c["url"]}">{img(f"contacto-{i + 1}", c["label"] + ": " + c["value"], "32%")}</a>'
        for i, c in enumerate(p["contact"])
    )
    hero_alt = f"{p['name']}. {' '.join(p['hero_lines'])} Ilustración: oficina virtual en isométrico con un capataz y cuatro peones."
    facts = " ".join(f"{n}: {l}" for n, l in p["facts"])
    stack_alt = "; ".join(f"{g}: {', '.join(i)}" for g, i in p["stack"])
    feat = ""
    if "featured" in p:
        f = p["featured"]
        feat_alt = (
            f"{f['name']}: {f['headline'][0]} {''.join(f['headline'][1:])} {f['desc']} "
            "Diagrama: los pedidos pasan por el clasificador y llegan a Sonnet o a Opus."
        )
        feat = f'<a href="{f["url"]}">{img("destacado", feat_alt)}</a>\n\n'
    return f"""<a href="https://github.com/{p['user']}">{img('hero', hero_alt)}</a>

{feat}{img('manifiesto', ' '.join(p['statement']) + ' ' + facts)}

{rows}

{img('stack', stack_alt)}

{img('bitacora', p['log_title'] + '. ' + p['log_note'])}

<!-- changelog:start -->
{block}
<!-- changelog:end -->

<p align="center">
{links}
</p>

<p align="center"><sub>{p['footer']}</sub></p>
"""


def main():
    p = json.loads((ROOT / "profile.json").read_text())
    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob("*.svg"):
        old.unlink()
    out = {"hero": hero(p), "manifiesto": manifesto(p), "stack": stack(p), "bitacora": log_header(p)}
    if "featured" in p:
        out["destacado"] = featured(p["featured"])
    for i, d in enumerate(p["deployments"]):
        out[f"producto-{i + 1}"] = product(d, i)
    for i, c in enumerate(p["contact"]):
        out[f"contacto-{i + 1}"] = contact(c)
    for name, content in out.items():
        (ASSETS / f"{name}.svg").write_text(content)
    (ROOT / "README.md").write_text(readme(p))
    print("listo:", ", ".join(f"{n} {len(c) // 1024}KB" for n, c in out.items()))


if __name__ == "__main__":
    main()
