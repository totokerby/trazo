"""Trazo geometry: anchors, orthogonal routing, rounded corners and collision detection."""

LADOS = ("izq", "der", "arriba", "abajo")
ANCHO_CHAR = 5.4  # upper bound for an 8px monospace label with .06em letter-spacing


def horizontal(lado):
    return lado in ("izq", "der")


def punto_lado(n, lado, k, total):
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]
    if horizontal(lado):
        py = round(y + h * k / (total + 1), 1)
        return (x if lado == "izq" else x + w, py)
    px = round(x + w * k / (total + 1), 1)
    return (px, y if lado == "arriba" else y + h)


def ruta(p1, l1, p2, l2, medio=None):
    """Orthogonal route: straight if both ends share an axis, L if orientation changes, Z otherwise."""
    (x1, y1), (x2, y2) = p1, p2
    h1, h2 = horizontal(l1), horizontal(l2)
    if h1 and h2:
        if abs(y1 - y2) < 0.5:
            return [p1, p2]
        mx = medio if medio is not None else (x1 + x2) / 2
        return [p1, (mx, y1), (mx, y2), p2]
    if not h1 and not h2:
        if abs(x1 - x2) < 0.5:
            return [p1, p2]
        my = medio if medio is not None else (y1 + y2) / 2
        return [p1, (x1, my), (x2, my), p2]
    if h1:
        return [p1, (x2, y1), p2]
    return [p1, (x1, y2), p2]


def trazo_d(pts, r=8):
    """SVG path with quarter-arc corners."""
    d = f"M {pts[0][0]} {pts[0][1]}"
    for i in range(1, len(pts) - 1):
        (ax, ay), (bx, by), (cx, cy) = pts[i - 1], pts[i], pts[i + 1]
        l1 = abs(bx - ax) + abs(by - ay)
        l2 = abs(cx - bx) + abs(cy - by)
        rr = min(r, l1 / 2, l2 / 2)
        ux1, uy1 = (bx - ax) / l1, (by - ay) / l1
        ux2, uy2 = (cx - bx) / l2, (cy - by) / l2
        sx, sy = bx - ux1 * rr, by - uy1 * rr
        ex, ey = bx + ux2 * rr, by + uy2 * rr
        giro = 1 if (ux1 * uy2 - uy1 * ux2) > 0 else 0
        d += f" L {sx:.1f} {sy:.1f} A {rr:.1f} {rr:.1f} 0 0 {giro} {ex:.1f} {ey:.1f}"
    return d + f" L {pts[-1][0]} {pts[-1][1]}"


def tramos(pts):
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]


def largo(t):
    return abs(t[1][0] - t[0][0]) + abs(t[1][1] - t[0][1])


def caja_rotulo(pts, texto, pos=None, t=0.5, tramo=None):
    """Label mask: 6-10px above (or beside) its segment, never on top of it."""
    ts = tramos(pts)
    if tramo is None:
        tramo = max(range(len(ts)), key=lambda i: largo(ts[i]))
    (ax, ay), (bx, by) = ts[tramo]
    mx, my = ax + (bx - ax) * t, ay + (by - ay) * t
    w = round(len(texto) * ANCHO_CHAR + 10)
    if ay == by:
        return (mx - w / 2, my + 7, w, 12) if pos == "abajo" else (mx - w / 2, my - 19, w, 12)
    return (mx - 7 - w, my - 6, w, 12) if pos == "izq" else (mx + 7, my - 6, w, 12)


def solapan(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def tramo_toca(s, r, pad=0.0):
    (ax, ay), (bx, by) = s
    x, y, w, h = r[0] - pad, r[1] - pad, r[2] + 2 * pad, r[3] + 2 * pad
    if ay == by:
        lo, hi = sorted((ax, bx))
        return y < ay < y + h and lo < x + w and hi > x
    lo, hi = sorted((ay, by))
    return x < ax < x + w and lo < y + h and hi > y


def cruzan(s, t):
    """X crossing, or parallel overlap closer than 12px."""
    (a1, a2), (b1, b2) = s, t
    sh, th = a1[1] == a2[1], b1[1] == b2[1]
    if sh == th:
        eje = 1 if sh else 0
        otro = 0 if sh else 1
        if abs(a1[eje] - b1[eje]) >= 12:
            return False
        lo1, hi1 = sorted((a1[otro], a2[otro]))
        lo2, hi2 = sorted((b1[otro], b2[otro]))
        return min(hi1, hi2) - max(lo1, lo2) > 1
    hs, vs = (s, t) if sh else (t, s)
    hy, vx = hs[0][1], vs[0][0]
    hlo, hhi = sorted((hs[0][0], hs[1][0]))
    vlo, vhi = sorted((vs[0][1], vs[1][1]))
    return hlo + 1 < vx < hhi - 1 and vlo + 1 < hy < vhi - 1


def resolver(diag):
    """Compute anchors, routes and labels of a normalized diagram."""
    nodos = {n["id"]: n for n in diag["nodos"]}
    aristas = diag.get("aristas", [])
    slots = {}
    for i, e in enumerate(aristas):
        for extremo, nid, lado in (("de", e["de"], e["lado_de"]), ("a", e["a"], e["lado_a"])):
            slots.setdefault((nid, lado), []).append((i, extremo))
    anclas = {}
    for (nid, lado), lista in slots.items():
        def clave(item):
            i, extremo = item
            o = nodos[aristas[i]["a" if extremo == "de" else "de"]]
            return (o["y"] + o["h"] / 2) if horizontal(lado) else (o["x"] + o["w"] / 2)
        lista.sort(key=lambda it: (aristas[it[0]].get("orden", 0), clave(it)))
        for k, it in enumerate(lista, 1):
            anclas[it] = punto_lado(nodos[nid], lado, k, len(lista))
    rutas, rotulos = [], []
    for i, e in enumerate(aristas):
        pts = ruta(anclas[(i, "de")], e["lado_de"], anclas[(i, "a")], e["lado_a"], e.get("medio"))
        rutas.append(pts)
        if e.get("texto"):
            caja = caja_rotulo(pts, e["texto"], e.get("pos"), e.get("t", 0.5), e.get("tramo"))
            rotulos.append((i, caja, e["texto"]))
    return rutas, rotulos
