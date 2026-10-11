"""Genera los SVGs del perfil (claro y oscuro) y el README a partir de profile.json.

Uso:  python scripts/build.py
Requiere: fonttools y brotli (pip install fonttools brotli)
"""

import base64
import io
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT_DIR = ROOT / "scripts" / "fonts"

FONTS = {
    "mono": ("JBM", 400, "jetbrains-mono-latin-400-normal.woff2"),
    "monob": ("JBM", 700, "jetbrains-mono-latin-700-normal.woff2"),
    "sans": ("SG", 500, "space-grotesk-latin-500-normal.woff2"),
    "sansb": ("SG", 700, "space-grotesk-latin-700-normal.woff2"),
}

THEMES = {
    "dark": {
        "card": "#0f141a",
        "card2": "#151b23",
        "border": "#262d36",
        "faint": "#1c232c",
        "dots": "#2a323c",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "dim": "#4a535e",
        "accent": "#f2a541",
        "accent_soft": "#3a2a12",
        "teal": "#4fd1c0",
        "teal_soft": "#103532",
        "blue": "#6cb6ff",
        "gray": "#8b949e",
        "green": "#3fb950",
    },
    "light": {
        "card": "#ffffff",
        "card2": "#f6f8fa",
        "border": "#d8dee4",
        "faint": "#f0f3f6",
        "dots": "#d8dee4",
        "text": "#1f2328",
        "muted": "#59636e",
        "dim": "#a3acb6",
        "accent": "#b5650d",
        "accent_soft": "#fdf0dc",
        "teal": "#0f7b6c",
        "teal_soft": "#dcf3ef",
        "blue": "#0969da",
        "gray": "#6e7781",
        "green": "#1a7f37",
    },
}

_metrics = {}


def _font(key):
    if key not in _metrics:
        f = TTFont(FONT_DIR / FONTS[key][2])
        _metrics[key] = (f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm)
    return _metrics[key]


def text_width(s, key, size, spacing=0.0):
    cmap, hmtx, upm = _font(key)
    total = 0
    for ch in s:
        glyph = cmap.get(ord(ch))
        total += hmtx[glyph][0] if glyph else upm * 0.6
    return total / upm * size + spacing * len(s)


def wrap(s, key, size, max_w, max_lines):
    words, lines, cur = s.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if text_width(test, key, size) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while text_width(lines[-1] + "…", key, size) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + "…"
    return lines


def _subset_b64(key, chars):
    f = TTFont(FONT_DIR / FONTS[key][2])
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern"]
    opts.name_IDs = []
    s = subset.Subsetter(opts)
    s.populate(text=chars + " ")
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


class Svg:
    def __init__(self, w, h, title, theme):
        self.w, self.h, self.title, self.t = w, h, title, THEMES[theme]
        self.parts, self.defs, self.used = [], [], {}

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, font, size, fill, anchor="start", spacing=0, extra=""):
        self.used.setdefault(font, set()).update(s)
        family, weight, _ = FONTS[font]
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        an = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}"{an}{ls}{extra}>{escape(s)}</text>'
        )

    def render(self):
        faces = []
        for key, chars in self.used.items():
            family, weight, _ = FONTS[key]
            data = _subset_b64(key, "".join(sorted(chars)))
            faces.append(
                f"@font-face{{font-family:{family};font-weight:{weight};"
                f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
            )
        style = f"<style>{''.join(faces)}</style>"
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.title)}">'
            f"<title>{escape(self.title)}</title>{style}{defs}{''.join(self.parts)}</svg>"
        )


def frame(svg, rx=14):
    t = svg.t
    svg.add(
        f'<rect x="0.5" y="0.5" width="{svg.w - 1}" height="{svg.h - 1}" rx="{rx}" '
        f'fill="{t["card"]}" stroke="{t["border"]}"/>'
    )


def chip(svg, x, y, label, fg, bg, font="monob", size=11, pad=9, h=22):
    w = text_width(label, font, size) + pad * 2
    svg.add(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="6" fill="{bg}"/>')
    svg.text(x + pad, y + h / 2 + size * 0.36, label, font, size, fg)
    return w


def pulse_dot(svg, cx, cy, color, r=4):
    svg.add(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}">'
        f'<animate attributeName="opacity" values="1;0.35;1" dur="2s" repeatCount="indefinite"/></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="1.5">'
        f'<animate attributeName="r" values="{r};{r + 6}" dur="2s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0.7;0" dur="2s" repeatCount="indefinite"/></circle>'
    )


def trace_header(svg, kind, call, right, kind_fg, kind_bg, ok_color=None):
    t = svg.t
    w = chip(svg, 24, 20, kind, kind_fg, kind_bg)
    svg.text(24 + w + 12, 36, call, "monob", 14, t["text"])
    if ok_color:
        rw = text_width(right, "mono", 11)
        svg.add(f'<circle cx="{svg.w - 26 - rw - 10}" cy="32" r="3.5" fill="{ok_color}"/>')
    svg.text(svg.w - 24, 36, right, "mono", 11, t["muted"], anchor="end")
    svg.add(f'<line x1="0" y1="58" x2="{svg.w}" y2="58" stroke="{t["border"]}"/>')


# ---------------------------------------------------------------- banner

def banner(p, theme):
    W, H = 860, 300
    svg = Svg(W, H, f"{p['name']} · {p['role']}", theme)
    t = svg.t
    svg.defs.append(
        f'<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">'
        f'<circle cx="1.5" cy="1.5" r="1.2" fill="{t["dots"]}"/></pattern>'
        f'<linearGradient id="fade" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0.45" stop-color="{t["card"]}" stop-opacity="1"/>'
        f'<stop offset="0.8" stop-color="{t["card"]}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="cardclip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>'
    )
    frame(svg)
    svg.add(
        f'<g clip-path="url(#cardclip)"><rect x="0" y="45" width="{W}" height="{H - 45}" fill="url(#dots)"/>'
        f'<rect x="0" y="45" width="{W}" height="{H - 45}" fill="url(#fade)"/></g>'
    )

    # barra de sesión
    svg.text(24, 29, "session", "mono", 12, t["muted"])
    svg.text(24 + text_width("session ", "mono", 12), 29, "ismael@said-co", "mono", 12, t["text"])
    rw = text_width("running", "mono", 12)
    pulse_dot(svg, W - 24 - rw - 12, 25, t["green"], r=3.5)
    svg.text(W - 24, 29, "running", "mono", 12, t["green"], anchor="end")
    svg.add(f'<line x1="0" y1="45" x2="{W}" y2="45" stroke="{t["border"]}"/>')

    # identidad
    svg.text(32, 86, "SYSTEM PROMPT", "monob", 11, t["accent"], spacing=2)
    svg.text(29, 136, p["name"], "sansb", 50, t["text"], spacing=-1)
    svg.text(32, 166, f"{p['role']}  ·  {p['location']}  ·  {p['company']}", "mono", 14, t["muted"])
    for i, line in enumerate(wrap(p["tagline"], "sans", 18, 470, 2)):
        svg.text(32, 202 + i * 25, line, "sans", 18, t["text"])

    # línea de streaming con tecleo
    x0, y0, size = 50, 270, 13
    svg.add(f'<path d="M32 {y0 - 10} l6 5 l-6 5" fill="none" stroke="{t["accent"]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    items = p["stream"]
    slot, T = 4.0, 4.0 * len(items)
    cw = text_width("m", "mono", size)
    cursor_events = []
    for i, s in enumerate(items):
        start, end, typing = i * slot, (i + 1) * slot, min(1.6, 0.06 * len(s))
        keys, vals = [0.0], [0]
        for k in range(len(s) + 1):
            keys.append(start + typing * k / len(s))
            vals.append(k * cw)
        keys += [end - 0.35, end]
        vals += [len(s) * cw, 0]
        cursor_events += list(zip(keys[1:], vals[1:]))
        kt = ";".join(f"{k / T:.4f}" for k in keys + [T])
        vv = ";".join(f"{v:.1f}" for v in vals + [0])
        svg.defs.append(
            f'<clipPath id="type{i}"><rect x="{x0}" y="{y0 - 14}" width="0" height="20">'
            f'<animate attributeName="width" values="{vv}" keyTimes="{kt}" calcMode="discrete" '
            f'dur="{T}s" repeatCount="indefinite"/></rect></clipPath>'
        )
        svg.add(f'<g clip-path="url(#type{i})">')
        svg.text(x0, y0, s, "mono", size, t["muted"])
        svg.add("</g>")
    ck = [0.0] + [k for k, _ in cursor_events] + [T]
    cv = [0.0] + [v for _, v in cursor_events] + [0.0]
    svg.add(
        f'<rect x="{x0}" y="{y0 - 11}" width="7" height="14" fill="{t["accent"]}">'
        f'<animate attributeName="x" values="{";".join(f"{x0 + v + 2:.1f}" for v in cv)}" '
        f'keyTimes="{";".join(f"{k / T:.4f}" for k in ck)}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;0" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect>'
    )

    # grafo de agentes: lead + peones
    cx, cy = 708, 168
    nodes = [("plan", 616, 98), ("code", 800, 98), ("eval", 616, 238), ("ship", 800, 238)]
    for i, (label, nx, ny) in enumerate(nodes):
        path = f"M{cx} {cy} L{nx} {ny}"
        svg.add(f'<path d="{path}" stroke="{t["dim"]}" stroke-width="1.5" stroke-dasharray="2 5" stroke-linecap="round"/>')
    for i, (label, nx, ny) in enumerate(nodes):
        begin = f"{i * 0.7:.1f}s"
        path = f"M{cx} {cy} L{nx} {ny}"
        svg.add(
            f'<circle r="3.2" fill="{t["accent"]}" opacity="0">'
            f'<animateMotion path="{path}" dur="2.8s" begin="{begin}" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.75;1" dur="2.8s" begin="{begin}" repeatCount="indefinite"/></circle>'
        )
    for i, (label, nx, ny) in enumerate(nodes):
        begin = f"{i * 0.7:.1f}s"
        svg.add(f'<rect x="{nx - 38}" y="{ny - 15}" width="76" height="30" rx="8" fill="{t["card2"]}" stroke="{t["border"]}"/>')
        svg.add(
            f'<rect x="{nx - 38}" y="{ny - 15}" width="76" height="30" rx="8" fill="none" stroke="{t["accent"]}" stroke-width="1.5" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;0" keyTimes="0;0.6;0.78;1" dur="2.8s" begin="{begin}" repeatCount="indefinite"/></rect>'
        )
        svg.text(nx, ny + 4, label, "mono", 12, t["muted"], anchor="middle")
    svg.add(f'<rect x="{cx - 46}" y="{cy - 18}" width="92" height="36" rx="10" fill="{t["accent_soft"]}" stroke="{t["accent"]}" stroke-width="1.5"/>')
    svg.text(cx, cy + 5, "lead", "monob", 13, t["accent"], anchor="middle")
    svg.text(W - 24, H - 14, "1 lead · 4 peones", "mono", 10, t["dim"], anchor="end")
    return svg.render()


# ---------------------------------------------------------------- whoami

def whoami(p, theme):
    rows = p["whoami"]
    W, H = 860, 80 + 30 * len(rows) + 18
    svg = Svg(W, H, "whoami", theme)
    t = svg.t
    frame(svg)
    trace_header(svg, "tool_use", "whoami()", "200 OK · 0.42s", t["accent"], t["accent_soft"], t["green"])
    key_w = max(len(k) for k, _ in rows) + 2
    for i, (k, v) in enumerate(rows):
        y = 92 + i * 30
        svg.text(40, y, f"{i + 1:02d}", "mono", 12, t["dim"], anchor="end")
        svg.text(60, y, f"{k}:", "mono", 14, t["accent"])
        svg.text(60 + text_width("m" * key_w, "mono", 14), y, v, "mono", 14, t["text"])
    return svg.render()


# ---------------------------------------------------------------- deployments

def deploy_card(d, theme):
    W, H = 420, 180
    svg = Svg(W, H, d["name"], theme)
    t = svg.t
    frame(svg)
    svg.text(22, 34, d["kind"].upper(), "monob", 10, t["muted"], spacing=1.5)
    if d["status"] == "live":
        label, color = "live", t["green"]
        lw = text_width(label, "mono", 11)
        pulse_dot(svg, W - 22 - lw - 12, 30, color, r=3.5)
    else:
        label, color = "próximamente", t["accent"]
        lw = text_width(label, "mono", 11)
        svg.add(f'<circle cx="{W - 22 - lw - 12}" cy="30" r="3.5" fill="none" stroke="{color}" stroke-width="1.5"/>')
    svg.text(W - 22, 34, label, "mono", 11, color, anchor="end")
    svg.text(22, 72, d["name"], "sansb", 23, t["text"], spacing=-0.3)
    for i, line in enumerate(wrap(d["desc"], "sans", 14, W - 44, 2)):
        svg.text(22, 99 + i * 20, line, "sans", 14, t["muted"])
    x = 22
    for tag in d["tags"]:
        w = text_width(tag, "mono", 11) + 18
        svg.add(f'<rect x="{x}" y="138" width="{w:.1f}" height="22" rx="6" fill="{t["faint"]}" stroke="{t["border"]}"/>')
        svg.text(x + 9, 153, tag, "mono", 11, t["muted"])
        x += w + 6
    if d["status"] == "live":
        ax, ay = W - 30, 149
        svg.add(
            f'<path d="M{ax - 6} {ay + 6} L{ax + 6} {ay - 6} M{ax - 3} {ay - 6} L{ax + 6} {ay - 6} L{ax + 6} {ay + 3}" '
            f'fill="none" stroke="{t["muted"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    return svg.render()


# ---------------------------------------------------------------- stack

def stack(p, theme):
    W = 860
    t = THEMES[theme]
    colors = [t["accent"], t["teal"], t["blue"], t["gray"]]
    x_chips, max_x, row_gap, chip_h = 176, W - 24, 12, 28
    layout, y = [], 112
    for gi, (label, items) in enumerate(p["stack"]):
        x, row_y, chips = x_chips, y, []
        for it in items:
            w = text_width(it, "sans", 13) + 24
            if x + w > max_x:
                x, row_y = x_chips, row_y + chip_h + 8
            chips.append((it, x, row_y, w))
            x += w + 8
        layout.append((label, y, chips, colors[gi % len(colors)]))
        y = row_y + chip_h + row_gap + 8
    H = y + 6
    total = sum(len(items) for _, items in p["stack"])
    svg = Svg(W, H, "stack", theme)
    frame(svg)
    trace_header(svg, "tool_result", "context_window", f"{len(p['stack'])} capas · {total} herramientas", t["teal"], t["teal_soft"])

    # barra de contexto segmentada
    bx, bw, gap = 24, W - 48, 4
    usable = bw - gap * (len(layout) - 1)
    x = bx
    for (label, _, chips, color) in layout:
        w = usable * len(chips) / total
        svg.add(f'<rect x="{x:.1f}" y="76" width="{w:.1f}" height="8" rx="4" fill="{color}"/>')
        x += w + gap

    for label, gy, chips, color in layout:
        svg.add(f'<circle cx="30" cy="{gy + 14}" r="4" fill="{color}"/>')
        svg.text(42, gy + 18.5, label, "mono", 13, t["muted"])
        for it, cx, cy, w in chips:
            svg.add(f'<rect x="{cx:.1f}" y="{cy}" width="{w:.1f}" height="{chip_h}" rx="7" fill="{t["card2"]}" stroke="{t["border"]}"/>')
            svg.text(cx + 12, cy + 18.5, it, "sans", 13, t["text"])
    return svg.render()


# ---------------------------------------------------------------- cierre

def footer(p, theme):
    W, H = 860, 64
    svg = Svg(W, H, "end_turn", theme)
    t = svg.t
    frame(svg)
    w = chip(svg, 24, 21, "stop_reason", t["muted"], t["faint"])
    svg.text(24 + w + 12, 37, '"end_turn"', "mono", 14, t["text"])
    svg.text(W - 24, 37, f"hecho en {p['location']} · con agentes", "mono", 11, t["muted"], anchor="end")
    return svg.render()


# ---------------------------------------------------------------- README

def picture(name, alt, width="100%"):
    return (
        f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
        f'<img src="assets/{name}-light.svg" alt="{escape(alt)}" width="{width}"></picture>'
    )


CHANGELOG_DEFAULT = (
    "> Todavía no hay corridas. Cada lunes un modelo lee mis commits públicos de la semana "
    "y escribe aquí qué construí."
)


def readme(p):
    path = ROOT / "README.md"
    block = CHANGELOG_DEFAULT
    if path.exists():
        m = re.search(r"<!-- changelog:start -->\n(.*?)\n<!-- changelog:end -->", path.read_text(), re.S)
        if m:
            block = m.group(1)

    cards = []
    for i, d in enumerate(p["deployments"]):
        cards.append(f'<a href="{d["url"]}">{picture(f"deploy-{i + 1}", d["name"], "49%")}</a>')
    pairs = ["\n".join(cards[i:i + 2]) for i in range(0, len(cards), 2)]

    return f"""<a href="https://github.com/{p['user']}">{picture('banner', f"{p['name']} · {p['role']}")}</a>

### `01 tool_use` whoami()

{picture('whoami', 'whoami: ' + '; '.join(f'{k}: {v}' for k, v in p['whoami']))}

### `02 tool_use` list_deployments()

<p>
{(chr(10) + '</p><p>' + chr(10)).join(pairs)}
</p>

### `03 tool_result` context_window

{picture('stack', 'Stack: ' + '; '.join(f"{g}: {', '.join(i)}" for g, i in p['stack']))}

### `04 tool_result` weekly_changelog

<!-- changelog:start -->
{block}
<!-- changelog:end -->

{picture('footer', 'end_turn')}
"""


def main():
    p = json.loads((ROOT / "profile.json").read_text())
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        (ASSETS / f"banner-{theme}.svg").write_text(banner(p, theme))
        (ASSETS / f"whoami-{theme}.svg").write_text(whoami(p, theme))
        (ASSETS / f"stack-{theme}.svg").write_text(stack(p, theme))
        (ASSETS / f"footer-{theme}.svg").write_text(footer(p, theme))
        for i, d in enumerate(p["deployments"]):
            (ASSETS / f"deploy-{i + 1}-{theme}.svg").write_text(deploy_card(d, theme))
    (ROOT / "README.md").write_text(readme(p))
    print("listo:", ", ".join(sorted(f.name for f in ASSETS.glob("*.svg"))))


if __name__ == "__main__":
    main()
