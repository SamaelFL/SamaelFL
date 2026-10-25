"""La oficina virtual en isométrico y los objetos de cada producto."""

import random

from iso import Box, Sprite, View, depth_sort, mix, render_scene, shade

P = {
    "night": "#0C0F16",
    "floor": "#1A2030",
    "floor_edge": "#0F131C",
    "wall_x": "#131926",
    "wall_y": "#182030",
    "wall_top": "#283043",
    "wood": "#3A3129",
    "desk": "#2A3142",
    "metal": "#3B4458",
    "dark": "#1C2230",
    "screen": "#0E2A2B",
    "glow": "#6FE3D0",
    "amber": "#FFB547",
    "hat": "#F2A93B",
    "white_hat": "#E9E4DA",
    "hoodie": "#2E3850",
    "shirt": "#D9D2C4",
    "pants": "#1E2333",
    "plant": "#2F5A4A",
    "pot": "#6B4A36",
    "text": "#EEEAE2",
    "muted": "#8D96A6",
}
SKINS = ["#B97A56", "#8D5A3B", "#C98E66", "#A86B45"]


def head_group(v, boxes, anim=""):
    inner = render_scene(v, boxes)
    xs = [b.bounds() for b in boxes]
    bounds = tuple(min(b[i] for b in xs) for i in range(3)) + tuple(max(b[i] for b in xs) for i in range(3, 6))
    return Sprite(bounds, f"<g>{anim}{inner}</g>")


def peon(v, px, py, skin, hat=P["hat"], react=True, uid="p"):
    """Peón sentado mirando hacia -x, con casco."""
    items = [
        Box(px - 0.45, py - 0.45, 1.0, 0.9, 0.9, 0.18, P["dark"]),            # asiento
        Box(px - 0.08, py - 0.08, 0.15, 0.16, 0.16, 0.85, P["metal"]),         # poste
        Box(px - 0.4, py - 0.4, 0.0, 0.8, 0.8, 0.15, P["metal"]),              # base
        Box(px - 0.95, py - 0.35, 1.18, 1.0, 0.7, 0.32, P["pants"]),           # muslos
        Box(px - 0.95, py - 0.32, 0.0, 0.28, 0.26, 1.18, P["pants"]),          # pierna
        Box(px - 0.95, py + 0.06, 0.0, 0.28, 0.26, 1.18, P["pants"]),          # pierna
        Box(px - 0.12, py - 0.42, 1.5, 0.58, 0.84, 1.2, P["hoodie"]),          # torso
        Box(px - 0.9, py - 0.62, 2.12, 0.78, 0.2, 0.2, P["hoodie"]),           # brazo
        Box(px - 0.9, py + 0.42, 2.12, 0.78, 0.2, 0.2, P["hoodie"]),           # brazo
        Box(px + 0.48, py - 0.45, 1.18, 0.16, 0.9, 0.95, shade(P["dark"], 1.15)),  # respaldo
    ]
    head = [
        Box(px - 0.12, py - 0.29, 2.72, 0.56, 0.58, 0.56, skin),
        Box(px - 0.18, py - 0.36, 3.2, 0.68, 0.72, 0.26, hat),
        Box(px - 0.42, py - 0.38, 3.18, 0.3, 0.76, 0.06, shade(hat, 0.92)),   # visera
    ]
    anim = ""
    if react:
        anim = (
            '<animateTransform attributeName="transform" type="translate" '
            'values="0 0;0 0;0 -4;0 1;0 0;0 0" keyTimes="0;0.6;0.64;0.7;0.76;1" dur="4s" repeatCount="indefinite"/>'
        )
    items.append(head_group(v, head, anim))
    return items


def desk(v, dx, dy, rng, uid):
    """Escritorio de peón con monitor (pantalla hacia +x), teclado y taza."""
    items = [Box(dx, dy, 1.9, 2.3, 2.6, 0.14, P["desk"])]
    for lx, ly in ((0.1, 0.1), (2.05, 0.1), (0.1, 2.35), (2.05, 2.35)):
        items.append(Box(dx + lx, dy + ly, 0.0, 0.14, 0.14, 1.9, P["metal"]))
    items.append(Box(dx + 0.32, dy + 1.18, 2.04, 0.18, 0.24, 0.42, P["metal"]))           # soporte
    items.append(Box(dx + 0.22, dy + 0.85, 2.04, 0.5, 0.9, 0.05, P["metal"]))             # base
    mon = Box(dx + 0.15, dy + 0.35, 2.4, 0.2, 1.9, 1.2, P["dark"], faces={"x": P["screen"]})
    u0, u1 = -(dy + 0.35 + 1.9) + 0.08, -(dy + 0.35) - 0.08
    v0, v1 = -(2.4 + 1.2) + 0.08, -2.4 - 0.08
    lines = []
    yy = v0 + 0.1
    for k in range(9):
        w = rng.uniform(0.3, 1.3)
        indent = rng.choice([0, 0, 0.15, 0.3])
        color = rng.choice([P["glow"], P["glow"], P["amber"], P["muted"]])
        lines.append(
            f'<rect x="{u0 + 0.1 + indent:.2f}" y="{yy:.2f}" width="{w:.2f}" height="0.055" rx="0.02" fill="{color}" opacity="0.85"/>'
        )
        yy += 0.12
    lines = lines + [f'<g transform="translate(0 1.08)">{"".join(lines)}</g>']
    scroll = (
        f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -1.08" '
        f'dur="{rng.uniform(5, 8):.1f}s" repeatCount="indefinite"/>'
    )
    flash = (
        f'<rect x="{u0}" y="{v0}" width="{u1 - u0:.2f}" height="{v1 - v0:.2f}" fill="{P["glow"]}" opacity="0">'
        '<animate attributeName="opacity" values="0;0;0.35;0;0" keyTimes="0;0.61;0.65;0.8;1" dur="4s" repeatCount="indefinite"/></rect>'
    )
    mon.after = (
        f'<g transform="{v.plane_x(dx + 0.35)}">'
        f'<clipPath id="scr{uid}"><rect x="{u0}" y="{v0}" width="{u1 - u0:.2f}" height="{v1 - v0:.2f}"/></clipPath>'
        f'<rect x="{u0}" y="{v0}" width="{u1 - u0:.2f}" height="{v1 - v0:.2f}" fill="{P["screen"]}"/>'
        f'<g clip-path="url(#scr{uid})"><g>{scroll}{"".join(lines)}</g></g>{flash}</g>'
    )
    items.append(mon)
    items.append(Box(dx + 1.15, dy + 0.75, 2.04, 0.45, 1.1, 0.06, shade(P["metal"], 0.8)))  # teclado
    items.append(Box(dx + 1.6, dy + 2.05, 2.04, 0.24, 0.24, 0.3, P["text"]))              # taza
    return items


def lead(v, x, y, z):
    """El capataz: de pie, casco blanco, mirando hacia +x. Devuelve partes y la posición de la mano."""
    skin = "#A9714C"
    items = [
        Box(x, y, z, 0.32, 0.28, 1.45, P["pants"]),
        Box(x, y + 0.45, z, 0.32, 0.28, 1.45, P["pants"]),
        Box(x - 0.1, y - 0.1, z + 1.45, 0.55, 0.95, 1.35, P["shirt"]),                 # torso
        Box(x - 0.05, y - 0.32, z + 1.75, 0.3, 0.22, 1.0, P["shirt"]),                  # brazo izq
        Box(x + 0.0, y + 0.85, z + 2.45, 1.0, 0.22, 0.22, P["shirt"]),                  # brazo del látigo
    ]
    head = [
        Box(x - 0.02, y + 0.06, z + 2.88, 0.58, 0.6, 0.58, skin),
        Box(x - 0.08, y - 0.01, z + 3.38, 0.7, 0.74, 0.27, P["white_hat"]),
        Box(x + 0.5, y - 0.03, z + 3.36, 0.3, 0.78, 0.06, shade(P["white_hat"], 0.9)),
    ]
    items.append(head_group(v, head))
    hand = v.p(x + 1.0, y + 0.96, z + 2.56)
    return items, hand


def whip(hand, svg):
    hx, hy = hand
    rest = "M0 0 C 6 14, -4 28, 4 42 S 14 58, 8 70"
    wind = "M0 0 C -6 -22, -30 -40, -56 -36 S -92 -12, -96 12"
    crack = "M0 0 C 30 -22, 70 -10, 88 26 S 100 96, 76 132"
    vals = ";".join([rest, rest, wind, crack, crack, rest, rest])
    kt = "0;0.42;0.55;0.62;0.68;0.88;1"
    spline = ";".join(["0.4 0 0.2 1"] * 6)
    spark = "".join(
        f'<line x1="0" y1="0" x2="{dx}" y2="{dy}" stroke="{P["amber"]}" stroke-width="2" stroke-linecap="round"/>'
        for dx, dy in ((10, -6), (12, 4), (4, 12), (-2, -11), (9, 10))
    )
    return (
        f'<g transform="translate({hx:.1f} {hy:.1f})">'
        f'<path fill="none" stroke="#C08552" stroke-width="2" stroke-linecap="round" d="{rest}">'
        f'<animate attributeName="d" values="{vals}" keyTimes="{kt}" calcMode="spline" keySplines="{spline}" dur="4s" repeatCount="indefinite"/></path>'
        f'<g transform="translate(76 132)" opacity="0">{spark}'
        + svg.text(12, -10, "¡CHAS!", "af8", 13, P["amber"]) +
        f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;0.61;0.63;0.72;1" dur="4s" repeatCount="indefinite"/></g>'
        f'</g>'
    )


def window_view(v, rng):
    u0, u1, v0, v1 = 9.0, 18.0, -9.0, -2.6
    w, h = u1 - u0, v1 - v0
    parts = [
        '<defs><linearGradient id="sky" x1="0" y1="-9" x2="0" y2="-2.6" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#070A14"/><stop offset="0.65" stop-color="#151A2E"/>'
        '<stop offset="1" stop-color="#3A2A35"/></linearGradient>'
        f'<clipPath id="win"><rect x="{u0}" y="{v0}" width="{w}" height="{h}"/></clipPath></defs>',
        f'<g clip-path="url(#win)"><rect x="{u0}" y="{v0}" width="{w}" height="{h}" fill="url(#sky)"/>',
    ]
    for _ in range(26):
        sx, sy, r = rng.uniform(u0, u1), rng.uniform(v0 + 0.1, v0 + 3.8), rng.uniform(0.025, 0.06)
        d = rng.uniform(2.5, 5)
        parts.append(
            f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="{r:.3f}" fill="#E9E4DA">'
            f'<animate attributeName="opacity" values="0.9;0.25;0.9" dur="{d:.1f}s" begin="{rng.uniform(0, 3):.1f}s" repeatCount="indefinite"/></circle>'
        )
    # Popocatépetl con fumarola
    parts.append('<polygon points="13.2,-2.6 15.6,-5.7 16.5,-5.8 19,-2.6" fill="#1F2436"/>')
    parts.append('<polygon points="15.3,-5.3 15.6,-5.7 16.5,-5.8 16.9,-5.25 16.45,-5.45 16.05,-5.15 15.75,-5.4" fill="#7E869A"/>')
    for k in range(4):
        b = f"{k * 1.5:.1f}s"
        parts.append(
            f'<circle cx="16.05" cy="-5.9" r="0.18" fill="#8D96A6" opacity="0">'
            f'<animate attributeName="cy" values="-5.9;-8.4" dur="6s" begin="{b}" repeatCount="indefinite"/>'
            f'<animate attributeName="cx" values="16.05;16.9" dur="6s" begin="{b}" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="0.15;0.7" dur="6s" begin="{b}" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.35;0" dur="6s" begin="{b}" repeatCount="indefinite"/></circle>'
        )
    # ciudad
    x = u0 - 0.2
    while x < u1:
        bw = rng.uniform(0.45, 1.0)
        bh = rng.uniform(0.6, 2.2)
        top = v1 - bh
        parts.append(f'<rect x="{x:.2f}" y="{top:.2f}" width="{bw:.2f}" height="{bh:.2f}" fill="#10141F"/>')
        for wy in range(int(bh / 0.22)):
            for wx in range(int(bw / 0.18)):
                if rng.random() < 0.22:
                    op = rng.uniform(0.35, 0.9)
                    parts.append(
                        f'<rect x="{x + 0.08 + wx * 0.18:.2f}" y="{top + 0.12 + wy * 0.22:.2f}" width="0.07" height="0.09" fill="{P["amber"]}" opacity="{op:.2f}"/>'
                    )
        x += bw + rng.uniform(0.02, 0.12)
    # torre con luz de obstrucción
    parts.append(f'<rect x="11.1" y="-6.4" width="0.7" height="3.8" fill="#121726"/>')
    parts.append(f'<rect x="11.4" y="-7.0" width="0.08" height="0.6" fill="#121726"/>')
    parts.append(
        '<circle cx="11.44" cy="-7.05" r="0.08" fill="#FF5A4F">'
        '<animate attributeName="opacity" values="1;0.1;1" dur="1.6s" repeatCount="indefinite"/></circle>'
    )
    for wy in range(14):
        if rng.random() < 0.5:
            parts.append(f'<rect x="11.2" y="{-6.25 + wy * 0.26:.2f}" width="0.5" height="0.05" fill="{P["amber"]}" opacity="0.4"/>')
    parts.append(f'<rect x="{u0}" y="{v0}" width="{w}" height="{h}" fill="#6FE3D0" opacity="0.03"/></g>')
    return f'<g transform="{v.plane_y(0)}">{"".join(parts)}</g>'


def office(svg, s=17, ox=556, oy=232):
    """Devuelve el SVG de la oficina completa (sin marco)."""
    v = View(s, ox, oy)
    rng = random.Random(7)
    W, D, H = 20, 16, 11
    back = []

    # muros y piso
    back.append(Box(-0.6, 0, -0.6, 0.6, D, H + 0.6, P["wall_x"], faces={"x": P["wall_x"], "top": P["wall_top"], "y": shade(P["wall_x"], 0.7)}).render(v))
    back.append(Box(-0.6, -0.6, -0.6, W + 0.6, 0.6, H + 0.6, P["wall_y"], faces={"y": P["wall_y"], "top": P["wall_top"], "x": shade(P["wall_y"], 0.7)}).render(v))
    back.append(Box(0, 0, -0.6, W, D, 0.6, P["floor"], faces={"top": P["floor"], "x": P["floor_edge"], "y": shade(P["floor_edge"], 1.2)}).render(v))

    # rejilla del piso y zócalos
    grid = "".join(
        f'<line x1="{i}" y1="0" x2="{i}" y2="{D}" stroke="#232B3D" stroke-width="0.03"/>' for i in range(2, W, 2)
    ) + "".join(f'<line x1="0" y1="{j}" x2="{W}" y2="{j}" stroke="#232B3D" stroke-width="0.03"/>' for j in range(2, D, 2))
    back.append(f'<g transform="{v.plane_z(0)}">{grid}</g>')
    back.append(f'<g transform="{v.plane_y(0)}"><rect x="0" y="-0.25" width="{W}" height="0.25" fill="#202839"/></g>')
    back.append(f'<g transform="{v.plane_x(0)}"><rect x="{-D}" y="-0.25" width="{D}" height="0.25" fill="#1A2130"/></g>')

    # ventana con vista a la ciudad
    back.append(window_view(v, rng))

    # letrero de neón
    neon = svg.text(0, 0, "SAID Co.", "af8", 1.2, P["amber"])
    back.append(
        f'<g transform="{v.plane_x(0)}"><g transform="translate(-15.2 -7.4)">'
        f'<g filter="url(#neonblur)" opacity="0.9">{neon}</g>{neon}'
        '<animate attributeName="opacity" values="1;1;0.35;1;0.6;1;1" keyTimes="0;0.86;0.87;0.88;0.89;0.9;1" dur="7s" repeatCount="indefinite"/>'
        '</g></g>'
    )

    # pizarrón detrás del capataz con el flujo de trabajo
    board = [f'<rect x="-5.4" y="-7.6" width="4.2" height="2.6" rx="0.08" fill="#D8D2C6"/>']
    labels = ["plan", "code", "eval", "ship"]
    for i, lab in enumerate(labels):
        bx = -5.15 + i * 1.0
        board.append(f'<rect x="{bx:.2f}" y="-6.6" width="0.72" height="0.42" rx="0.05" fill="none" stroke="#2A3142" stroke-width="0.04"/>')
        board.append(svg.text(bx + 0.36, -6.3, lab, "gm4", 0.2, "#2A3142", anchor="middle"))
        if i < 3:
            board.append(f'<path d="M{bx + 0.76:.2f} -6.39 h0.2" stroke="#C0392B" stroke-width="0.04"/>')
    board.append(svg.text(-5.15, -7.15, "pipeline v3", "gm4", 0.22, "#2A3142"))
    board.append('<path d="M-2.4 -5.55 q0.3 -0.25 0.6 0 t0.6 0" fill="none" stroke="#C0392B" stroke-width="0.04"/>')
    back.append(f'<g transform="{v.plane_x(0)}">{"".join(board)}</g>')

    # reloj
    clock = svg.text(6.0, -8.15, "02:47", "gm5", 0.62, P["glow"], anchor="middle")
    back.append(
        f'<g transform="{v.plane_y(0)}"><rect x="5.0" y="-8.85" width="2.0" height="0.95" rx="0.08" fill="#0A0D14" stroke="#2A3142" stroke-width="0.05"/>{clock}</g>'
    )

    # charcos de luz sobre el piso
    pools = []
    for cx, cy, r, color, op in ((3.2, 3.4, 3.2, P["amber"], 0.16), (9.0, 8.3, 2.6, P["amber"], 0.10), (14.0, 8.3, 2.6, P["amber"], 0.10),
                                 (9.0, 12.8, 2.6, P["amber"], 0.10), (14.0, 12.8, 2.6, P["amber"], 0.10)):
        pools.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#pool{"A" if color == P["amber"] else "G"})" opacity="{op / 0.16:.2f}"/>'
        )
    back.append(f'<g transform="{v.plane_z(0)}">{"".join(pools)}</g>')

    items = []
    # tarima del capataz
    items.append(Box(0.8, 0.8, 0, 4.5, 4.5, 0.55, "#2B3346", faces={"top": "#2E374B"}))
    stripe = "".join(
        f'<rect x="{0.8 + k * 0.5:.2f}" y="-0.5" width="0.25" height="0.5" fill="{P["amber"]}" opacity="0.85"/>' for k in range(9)
    )
    back_stage = (f'<g transform="{v.plane_y(5.3)}">{stripe}</g>', f'<g transform="{v.plane_x(5.3)}">'
                  + "".join(f'<rect x="{-(0.8 + k * 0.5) - 0.25:.2f}" y="-0.5" width="0.25" height="0.5" fill="{P["amber"]}" opacity="0.85"/>' for k in range(9))
                  + "</g>")
    items[-1].after = "".join(back_stage)
    lead_items, hand = lead(v, 2.7, 2.7, 0.55)
    items += lead_items

    # escritorios de los peones
    uid = 0
    for dy in (6.8, 11.3):
        for dx in (7.6, 12.6):
            items += desk(v, dx, dy, rng, uid)
            items += peon(v, dx + 2.75, dy + 1.3, SKINS[uid], uid=uid)
            uid += 1

    # racks de servidores
    for ry in (9.4, 11.7):
        rack = Box(0, ry, 0, 1.3, 2.0, 6.0, "#1D2332", faces={"x": "#171C29"})
        leds = []
        for row in range(14):
            for col in range(5):
                if rng.random() < 0.55:
                    color = rng.choice([P["glow"], P["glow"], P["amber"], "#3FB950"])
                    d = rng.uniform(0.6, 2.4)
                    leds.append(
                        f'<rect x="{-(ry + 2.0) + 0.25 + col * 0.3:.2f}" y="{-5.6 + row * 0.38:.2f}" width="0.12" height="0.07" fill="{color}">'
                        f'<animate attributeName="opacity" values="1;0.2;1" dur="{d:.1f}s" begin="{rng.uniform(0, 2):.1f}s" repeatCount="indefinite"/></rect>'
                    )
            leds.append(f'<rect x="{-(ry + 2.0) + 0.12:.2f}" y="{-5.68 + row * 0.38:.2f}" width="1.76" height="0.3" fill="none" stroke="#252D3F" stroke-width="0.03"/>')
        rack.after = f'<g transform="{v.plane_x(1.3)}">{"".join(leds)}</g>'
        items.append(rack)

    # marco de la ventana
    frame_c = "#2A3245"
    items.append(Box(8.8, 0, 2.3, 9.4, 0.45, 0.3, frame_c))
    items.append(Box(8.8, 0, 9.0, 9.4, 0.25, 0.25, frame_c))
    for fx in (8.8, 13.4, 18.0):
        items.append(Box(fx, 0, 2.6, 0.2, 0.25, 6.4, frame_c))

    # planta
    items.append(Box(18.6, 0.6, 0, 1.0, 1.0, 1.0, P["pot"]))
    for lx, ly, lz, sz in ((18.7, 0.7, 1.0, 0.8), (18.9, 0.5, 1.7, 0.7), (18.5, 0.9, 2.3, 0.6), (19.0, 0.8, 2.8, 0.5), (18.7, 0.6, 3.2, 0.45)):
        items.append(Box(lx, ly, lz, sz, sz, sz * 0.8, shade(P["plant"], 1.0 + (lz - 1) * 0.08)))

    # tapete y sillón del área de descanso
    items.append(Box(2.6, 8.6, 0, 3.4, 5.6, 0.04, "#242B3C", faces={"top": "#262E40"}))
    items.append(Box(2.9, 12.2, 0, 2.8, 1.2, 0.9, "#3A2F2A"))
    items.append(Box(2.9, 13.2, 0.9, 2.8, 0.25, 0.9, "#3A2F2A"))
    items.append(Box(3.4, 9.6, 0.04, 1.8, 1.2, 0.7, "#2E3648"))
    items.append(Box(3.6, 9.8, 0.74, 1.0, 0.7, 0.05, "#9AA3B3", faces={"top": "#B8C0CC"}))

    # mueble con cafetera
    items.append(Box(18.4, 7.0, 0, 1.5, 3.2, 2.2, "#2B3242"))
    items.append(Box(18.6, 7.3, 2.2, 1.0, 1.0, 1.3, "#151A26"))
    items.append(Box(18.7, 8.7, 2.2, 0.3, 0.3, 0.35, P["text"]))
    items.append(Box(18.7, 9.2, 2.2, 0.3, 0.3, 0.35, P["amber"]))

    scene = render_scene(v, items)

    # lámparas colgantes con cono de luz
    lights = []
    for cx, cy in ((9.0, 8.1), (14.0, 8.1), (9.0, 12.6), (14.0, 12.6), (3.2, 3.3)):
        top = v.p(cx, cy, H)
        lamp = v.p(cx, cy, 7.2)
        l0, l1 = v.p(cx - 1.2, cy + 1.2, 2.1), v.p(cx + 1.2, cy - 1.2, 2.1)
        lights.append(f'<line x1="{top[0]:.1f}" y1="{top[1]:.1f}" x2="{lamp[0]:.1f}" y2="{lamp[1]:.1f}" stroke="#2A3245" stroke-width="1"/>')
        lights.append(
            f'<polygon points="{lamp[0] - 4:.1f},{lamp[1] + 4:.1f} {lamp[0] + 4:.1f},{lamp[1] + 4:.1f} {l1[0]:.1f},{l1[1]:.1f} {l0[0]:.1f},{l0[1]:.1f}" fill="url(#cone)" opacity="0.5"/>'
        )
        lights.append(f'<path d="M{lamp[0] - 7:.1f} {lamp[1] + 4:.1f} L{lamp[0] - 3:.1f} {lamp[1] - 3:.1f} L{lamp[0] + 3:.1f} {lamp[1] - 3:.1f} L{lamp[0] + 7:.1f} {lamp[1] + 4:.1f} Z" fill="#2E3648"/>')
        lights.append(f'<ellipse cx="{lamp[0]:.1f}" cy="{lamp[1] + 4:.1f}" rx="6" ry="1.6" fill="{P["amber"]}"/>')

    # polvo flotando en la luz
    dust = []
    for _ in range(14):
        cx, cy = rng.choice(((9.0, 8.1), (14.0, 8.1), (9.0, 12.6), (14.0, 12.6), (3.2, 3.3)))
        px, py = v.p(cx + rng.uniform(-0.8, 0.8), cy + rng.uniform(-0.8, 0.8), rng.uniform(3, 6.5))
        d = rng.uniform(5, 9)
        dust.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{rng.uniform(0.6, 1.2):.1f}" fill="{P["amber"]}" opacity="0">'
            f'<animate attributeName="cy" values="{py:.1f};{py - 18:.1f}" dur="{d:.1f}s" begin="{rng.uniform(0, 4):.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.5;0" dur="{d:.1f}s" begin="{rng.uniform(0, 4):.1f}s" repeatCount="indefinite"/></circle>'
        )

    defs = (
        '<defs>'
        '<filter id="neonblur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="0.18"/></filter>'
        f'<radialGradient id="poolA"><stop offset="0" stop-color="{P["amber"]}" stop-opacity="0.16"/><stop offset="1" stop-color="{P["amber"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="cone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P["amber"]}" stop-opacity="0.35"/><stop offset="1" stop-color="{P["amber"]}" stop-opacity="0"/></linearGradient>'
        '</defs>'
    )
    return defs + "".join(back) + scene + "".join(lights) + "".join(dust) + whip(hand, svg)


# ---------------------------------------------------------------- objetos de producto

def plinth(items, cx, cy, size=3.6):
    h = size / 2
    items.append(Box(cx - h, cy - h, 0, size, size, 0.6, "#232A3B", faces={"top": "#2A3245"}))


def obj_dumbbell(v):
    items = []
    plinth(items, 0, 0)
    items.append(Box(-1.6, -0.12, 1.05, 3.2, 0.24, 0.24, "#9AA3B3"))
    for x0 in (-1.45, -1.05, 0.75, 1.15):
        items.append(Box(x0, -0.7, 0.6, 0.3, 1.4, 1.4, P["amber"] if x0 in (-1.45, 1.15) else "#2B3245"))
    return items


def obj_cv(v, svg):
    items = []
    plinth(items, 0, 0)
    for k in range(3):
        items.append(Box(-1.2 + k * 0.08, -1.5 + k * 0.08, 0.6 + k * 0.12, 2.4, 3.0, 0.12, "#E9E4DA"))
    top = items[-1]
    lines = [f'<rect x="-0.86" y="-1.12" width="0.9" height="0.16" fill="{P["amber"]}"/>']
    for k, w in enumerate((1.8, 1.4, 1.7, 1.1, 1.6, 1.3)):
        lines.append(f'<rect x="-0.86" y="{-0.7 + k * 0.32:.2f}" width="{w}" height="0.08" fill="#8D96A6"/>')
    top.after = f'<g transform="{v.plane_z(0.6 + 2 * 0.12 + 0.12)}">{"".join(lines)}</g>'
    items.append(Box(0.7, 0.9, 0.96, 0.6, 0.6, 0.08, "#3FB950", faces={"top": "#3FB950"}))
    return items


def obj_peon(v):
    items = [Box(-2.3, -1.6, -0.6, 5.6, 3.8, 0.6, "#232A3B", faces={"top": "#2A3245"})]
    rng = random.Random(3)
    return items + desk(v, -2.0, -1.0, rng, "solo") + peon(v, 0.75, 0.3, SKINS[2], uid="solo")


def obj_toolbox(v):
    items = []
    plinth(items, 0, 0)
    items.append(Box(-1.5, -0.8, 0.6, 3.0, 1.6, 1.3, "#2B3245"))
    items.append(Box(-1.55, -0.85, 1.9, 3.1, 1.7, 0.18, P["amber"]))
    items.append(Box(-0.7, -0.1, 2.08, 0.15, 0.2, 0.45, "#9AA3B3"))
    items.append(Box(0.55, -0.1, 2.08, 0.15, 0.2, 0.45, "#9AA3B3"))
    items.append(Box(-0.7, -0.1, 2.5, 1.4, 0.2, 0.14, "#9AA3B3"))
    items.append(Box(-0.25, 0.8, 1.15, 0.5, 0.06, 0.35, "#9AA3B3"))
    return items


ALTO_FICHA = 1.5


def obj_alcancia(v):
    """La caja del acreditador: una ranura arriba y un foco verde al frente."""
    items = []
    plinth(items, 0, 0)
    items.append(Box(-1.3, -1.0, 0.6, 2.6, 2.0, 1.8, "#2B3245", faces={"top": "#333C52"}))
    items.append(Box(-1.32, -1.02, 2.2, 2.64, 2.04, 0.2, P["amber"]))
    items.append(Box(-0.55, -0.09, 2.4, 1.1, 0.18, 0.02, "#0C0F16", faces={"top": "#0C0F16"}))
    items.append(Box(0.6, 1.0, 1.15, 0.45, 0.08, 0.45, "#24402F"))
    # Un punto invisible donde arranca la ficha, para que el encuadre la incluya.
    items.append(Box(0, 0, 2.45 + ALTO_FICHA + 0.6, 0.001, 0.001, 0.001, "#232A3B"))
    return items


def obj_prensa(v):
    """El enrutador: una pila de contexto que la prensa compacta."""
    items = []
    plinth(items, 0, 0)
    items.append(Box(-1.2, -1.2, 0.6, 2.4, 2.4, 0.2, "#2B3245"))
    for k in range(9):
        items.append(Box(-1.0, -1.0, 0.8 + k * 0.2, 2.0, 2.0, 0.16, "#E9E4DA" if k % 2 else "#D3CCC0"))
    tope = 0.8 + 9 * 0.2 + 0.02
    items.append(Box(-1.3, -1.3, tope, 2.6, 2.6, 0.22, P["amber"]))
    items.append(Box(-0.13, -0.13, tope + 0.22, 0.26, 0.26, 0.9, "#9AA3B3"))
    return items


# ---------------------------------------------------------------- animaciones de producto
# SMIL dentro del SVG: GitHub lo reproduce porque la imagen se sirve tal cual (sin JavaScript).

def _ease(n):
    return ";".join(["0.45 0 0.25 1"] * n)


def anim_dumbbell(v, items, svg):
    base = render_scene(v, items[:1])
    peso = render_scene(v, items[1:])
    sx, sy = v.p(0, 0, 0.6)
    rx, ry = 1.9 * v.s, 0.55 * v.s
    d = 1.15 * v.s
    sombra = (
        f'<ellipse cx="{sx:.1f}" cy="{sy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#000" opacity="0.32">'
        f'<animate attributeName="opacity" values="0.32;0.12;0.12;0.32;0.32" keyTimes="0;0.35;0.55;0.85;1" '
        f'calcMode="spline" keySplines="{_ease(4)}" dur="2.6s" repeatCount="indefinite"/>'
        f'<animate attributeName="rx" values="{rx:.1f};{rx * 0.7:.1f};{rx * 0.7:.1f};{rx:.1f};{rx:.1f}" keyTimes="0;0.35;0.55;0.85;1" '
        f'calcMode="spline" keySplines="{_ease(4)}" dur="2.6s" repeatCount="indefinite"/></ellipse>'
    )
    sube = (
        f'<g>{peso}<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;0 {-d:.1f};0 {-d:.1f};0 0;0 0" keyTimes="0;0.35;0.55;0.85;1" calcMode="spline" '
        f'keySplines="{_ease(4)}" dur="2.6s" repeatCount="indefinite"/></g>'
    )
    return base + sombra + sube


def anim_cv(v, items, svg):
    base = render_scene(v, items[:1])
    hojas = render_scene(v, items[1:4])
    sello = render_scene(v, items[4:])
    z = 0.6 + 2 * 0.12 + 0.12
    escaneo = (
        f'<g transform="{v.plane_z(z)}"><rect x="-1.0" y="-1.3" width="2.3" height="0.07" fill="{P["glow"]}" opacity="0">'
        '<animate attributeName="y" values="-1.3;1.55;1.55" keyTimes="0;0.55;1" dur="3.2s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values="0;0.9;0.9;0;0" keyTimes="0;0.05;0.5;0.56;1" dur="3.2s" repeatCount="indefinite"/>'
        '</rect></g>'
    )
    cae = 1.4 * v.s
    sello_anim = (
        f'<g opacity="0">{sello}'
        f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.55;0.62;0.92;1" dur="3.2s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="0 {-cae:.1f};0 {-cae:.1f};0 0;0 0" '
        f'keyTimes="0;0.55;0.64;1" calcMode="spline" keySplines="0 0 1 1;0.6 0 0.9 1;0 0 1 1" dur="3.2s" repeatCount="indefinite"/></g>'
    )
    flota = (
        f'<g>{hojas}{escaneo}{sello_anim}<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;0 {-0.12 * v.s:.1f};0 0" keyTimes="0;0.5;1" calcMode="spline" keySplines="{_ease(2)}" '
        f'dur="3.2s" repeatCount="indefinite"/></g>'
    )
    return base + flota


def anim_toolbox(v, items, svg):
    fijo = render_scene(v, items[:2] + items[6:])
    tapa = render_scene(v, items[2:6])
    d = 0.35 * v.s
    t = 3.0
    abre = (
        f'<g>{tapa}<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;0 {-d:.1f};0 {-d:.1f};0 0;0 0" keyTimes="0;0.15;0.6;0.75;1" calcMode="spline" '
        f'keySplines="{_ease(4)}" dur="{t}s" repeatCount="indefinite"/></g>'
    )
    colores = [P["amber"], P["glow"], "#3FB950", P["white_hat"]]
    cubos = []
    for i, (x, col) in enumerate(zip((-1.05, -0.4, 0.25, 0.9), colores)):
        cubo = render_scene(v, [Box(x - 0.03, -0.21, 1.95, 0.44, 0.44, 0.44, col)])
        ini = 0.12 + i * 0.07
        fin = min(ini + 0.45, 0.95)
        sube = 2.2 * v.s
        cubos.append(
            f'<g opacity="0">{cubo}'
            f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{ini:.2f};{ini + 0.08:.2f};{fin:.2f};1" dur="{t}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 {-sube:.1f};0 {-sube:.1f}" '
            f'keyTimes="0;{ini:.2f};{fin:.2f};1" calcMode="spline" keySplines="0 0 1 1;0.2 0.6 0.4 1;0 0 1 1" dur="{t}s" repeatCount="indefinite"/></g>'
        )
    return fijo + abre + "".join(cubos)


def anim_alcancia(v, items, svg):
    """Tres copias del mismo pago caen a la ranura: entra una, las otras rebotan."""
    fijo = render_scene(v, items[:4])
    foco_apagado = render_scene(v, items[4:5])
    foco = render_scene(v, [Box(0.6, 1.0, 1.15, 0.45, 0.08, 0.45, "#3FB950", faces={"top": "#7EE2A0"})])
    t = 3.4
    alto = ALTO_FICHA * v.s
    entra = 0.3 * v.s
    piezas = []
    for i, ini in enumerate((0.04, 0.38, 0.62)):
        ficha = render_scene(v, [Box(-0.3, -0.06, 2.45, 0.6, 0.12, 0.6, P["glow"], faces={"top": "#B4F2E8"})])
        llega = ini + 0.18
        if i == 0:
            # La primera entra: baja hasta la ranura y se mete.
            valores = f"0 {-alto:.1f};0 {-alto:.1f};0 0;0 {entra:.1f};0 {entra:.1f}"
            tiempos = f"0;{ini:.2f};{llega:.2f};{llega + 0.06:.2f};1"
            opacidad = f"0;0;1;1;0;0"
            t_op = f"0;{ini:.2f};{ini + 0.04:.2f};{llega:.2f};{llega + 0.06:.2f};1"
        else:
            # Las copias llegan, rebotan en la ranura y se desvanecen.
            rebote = -0.45 * v.s
            valores = f"0 {-alto:.1f};0 {-alto:.1f};0 0;0 {rebote:.1f};0 {rebote:.1f}"
            tiempos = f"0;{ini:.2f};{llega:.2f};{llega + 0.08:.2f};1"
            opacidad = "0;0;1;1;0;0"
            t_op = f"0;{ini:.2f};{ini + 0.04:.2f};{llega + 0.04:.2f};{llega + 0.12:.2f};1"
        piezas.append(
            f'<g opacity="0">{ficha}'
            f'<animate attributeName="opacity" values="{opacidad}" keyTimes="{t_op}" dur="{t}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="{valores}" keyTimes="{tiempos}" '
            f'calcMode="spline" keySplines="0 0 1 1;0.55 0 0.9 0.6;0.2 0.6 0.4 1;0 0 1 1" dur="{t}s" repeatCount="indefinite"/></g>'
        )
    prende = 0.04 + 0.18 + 0.05
    luz = (
        f'<g opacity="0">{foco}'
        f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{prende:.2f};{prende + 0.03:.2f};'
        f'{prende + 0.3:.2f};{prende + 0.4:.2f};1" dur="{t}s" repeatCount="indefinite"/></g>'
    )
    return fijo + foco_apagado + luz + "".join(piezas)


def anim_prensa(v, items, svg):
    """La pila crece paso a paso; al pasar el tope, la prensa la compacta."""
    t = 4.2
    base = render_scene(v, items[:2])
    capas = items[2:11]
    prensa = render_scene(v, items[11:])
    quedan = 3
    baja = (9 - quedan) * 0.2 * v.s
    salida = []
    for k, capa in enumerate(capas):
        dibujo = render_scene(v, [capa])
        if k < quedan:
            salida.append(dibujo)
            continue
        # De arriba hacia abajo se van al bajar la prensa; luego vuelven a crecer una por una.
        orden = (8 - k) / (8 - quedan)
        se_va = 0.12 + 0.3 * orden
        vuelve = 0.6 + 0.3 * (k - quedan) / (8 - quedan)
        salida.append(
            f'<g>{dibujo}<animate attributeName="opacity" values="1;1;0;0;1;1" '
            f'keyTimes="0;{se_va:.3f};{se_va + 0.03:.3f};{vuelve:.3f};{vuelve + 0.03:.3f};1" dur="{t}s" repeatCount="indefinite"/></g>'
        )
    golpe = (
        f'<g>{prensa}<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;0 0;0 {baja:.1f};0 {baja:.1f};0 0;0 0" keyTimes="0;0.1;0.44;0.52;0.62;1" calcMode="spline" '
        f'keySplines="0 0 1 1;0.5 0 0.8 0.6;0 0 1 1;{_ease(1)};0 0 1 1" dur="{t}s" repeatCount="indefinite"/></g>'
    )
    return base + "".join(salida) + golpe


ANIMADOS = {
    "dumbbell": anim_dumbbell,
    "cv": anim_cv,
    "toolbox": anim_toolbox,
    "alcancia": anim_alcancia,
    "prensa": anim_prensa,
}


def product_object(svg, kind, cx, cy, max_w, max_h, animar=False):
    from iso import _screen_box
    fn = {
        "dumbbell": obj_dumbbell,
        "peon": obj_peon,
        "toolbox": obj_toolbox,
        "alcancia": obj_alcancia,
        "prensa": obj_prensa,
    }

    def build(v):
        return obj_cv(v, svg) if kind == "cv" else fn[kind](v)

    probe = View(10, 0, 0)
    boxes = [_screen_box(probe, it.bounds()) for it in build(probe)]
    x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
    s = 10 * min(max_w / (x1 - x0), max_h / (y1 - y0))
    k = s / 10
    v = View(s, cx - (x0 + x1) / 2 * k, cy - (y0 + y1) / 2 * k)
    if animar and kind in ANIMADOS:
        return ANIMADOS[kind](v, build(v), svg)
    return render_scene(v, build(v))
