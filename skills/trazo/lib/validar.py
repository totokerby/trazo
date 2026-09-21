"""Trazo validator. An error blocks the build; a warning does not."""
from geometria import LADOS, resolver, solapan, tramo_toca, cruzan, tramos
from svg import items_leyenda, alto_leyenda, lineas_nodo, escala, T_ETQ

CLASES = ("foco", "proceso", "estado", "externo", "persona", "pendiente", "gate")
ESTILOS = ("flujo", "principal", "externo", "pendiente", "principal-pendiente")
TOPES = {  # nodes, edges
    "arquitectura": (9, 12),
    "flujo": (9, 12),
    "organigrama": (12, 14),
    "capas": (6, 0),
}
MAX_ACENTO = 2
# public names, for messages
EN_TIPO = {"arquitectura": "architecture", "flujo": "flow", "organigrama": "org", "capas": "layers"}
EN_KINDS = "focus, process, state, external, person, pending, gate"
EN_STYLES = "flow, main, external, pending, main-pending"
EN_SIDES = "left, right, top, bottom"


class Informe:
    def __init__(self):
        self.errores, self.advertencias = [], []

    def error(self, donde, codigo, msg, arreglo):
        self.errores.append(dict(where=donde, code=codigo, msg=msg, fix=arreglo))

    def aviso(self, donde, codigo, msg, arreglo):
        self.advertencias.append(dict(where=donde, code=codigo, msg=msg, fix=arreglo))


def normalizar(diag):
    for n in diag.get("nodos", []):
        n.setdefault("w", 160)
        n.setdefault("h", 80)
        n.setdefault("sub", [])
        n.setdefault("etiqueta", "")
        n.setdefault("clase", "proceso")
    for e in diag.get("aristas", []):
        e.setdefault("estilo", "flujo")
    diag.setdefault("zonas", [])
    diag.setdefault("aristas", [])
    return diag


def verificar_fuente(f, raiz, donde, inf):
    ruta = (raiz / f.get("ruta", "")).resolve()
    ref = f.get("ruta", "?") + (f":{f['linea']}" if f.get("linea") else "")
    if not f.get("ruta") or not ruta.is_file():
        inf.error(donde, "source-missing", f"source {ref} does not exist",
                  "fix the path; it is relative to 'repository'")
        return
    lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
    linea, contiene = f.get("linea"), f.get("contiene")
    if linea and linea > len(lineas):
        inf.error(donde, "source-line", f"{ref}: the file has {len(lineas)} lines",
                  "the file changed: update the line or the diagram")
        return
    if contiene:
        if linea and contiene not in lineas[linea - 1]:
            inf.error(donde, "source-stale", f"{ref} no longer contains '{contiene}'",
                      "the code changed: check the diagram is still true, then update the line")
        elif not linea and not any(contiene in l for l in lineas):
            inf.error(donde, "source-stale", f"{ref} no longer contains '{contiene}'",
                      "the file changed: check the diagram is still true")


def validar_diagrama(diag, raiz, inf):
    did = diag.get("id", "?")
    tipo = diag.get("tipo")
    if tipo not in TOPES:
        inf.error(did, "type", f"unknown type '{tipo}'", "use architecture, flow, org or layers")
        return
    for campo, pub in (("titulo", "title"), ("descripcion", "description"), ("tamano", "size")):
        if not diag.get(campo):
            inf.error(did, "missing-field", f"missing '{pub}'",
                      "title and description feed <title>/<desc>; size is [width, height]")
    if not diag.get("tamano"):
        return
    W, H = diag["tamano"]
    esc = escala(diag)
    if not 0.5 <= esc <= 3:
        inf.error(did, "text-scale", f"text_scale {esc} is out of range", "use a value between 0.5 and 3")
        return
    imp = diag.get("_imp")
    if imp is not None:
        imp = imp if isinstance(imp, dict) else {}
        ancho, minimo = imp.get("ancho_pt"), imp.get("min_pt", 6)
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0 for x in (ancho, minimo)):
            inf.error(did, "print-profile", "'print' needs positive numbers: {\"width_pt\": N, \"min_pt\": N}",
                      "width_pt is the printed width of the diagram in points; min_pt defaults to 6")
            return
        real = T_ETQ * esc * ancho / W
        if real < minimo:
            inf.error(did, "print-size", f"the smallest text prints at {real:.1f} pt; the minimum is {minimo:g} pt "
                      f"(canvas {W} units at {ancho:g} pt wide)",
                      f"set 'text_scale' to {minimo * W / (T_ETQ * ancho):.2f} or more (then re-check the layout), "
                      f"or make the canvas {ancho * T_ETQ * esc / minimo:.0f} units wide or less")
    nodos = diag["nodos"]
    ids = [n.get("id") for n in nodos]
    if len(set(ids)) != len(ids):
        inf.error(did, "duplicate-id", "duplicate node ids", "give every node a unique id")
    idx = {n["id"]: n for n in nodos}
    maxn, maxa = TOPES[tipo]
    if len(nodos) > maxn:
        inf.error(did, "budget-nodes", f"{len(nodos)} nodes; the limit for '{EN_TIPO[tipo]}' is {maxn}",
                  "split into an overview + detail, or merge nodes that always travel together")
    if len(diag["aristas"]) > maxa:
        inf.error(did, "budget-edges", f"{len(diag['aristas'])} edges; the limit is {maxa}",
                  "delete the relations the layout already makes obvious")
    acento = sum(1 for n in nodos if n["clase"] == "foco") + \
        sum(1 for e in diag["aristas"] if e["estilo"].startswith("principal"))
    if acento > MAX_ACENTO:
        inf.error(did, "accent", f"{acento} accented elements; the limit is {MAX_ACENTO}",
                  "the accent is editorial: decide what the real focus is")
    for n in nodos:
        donde = f"{did}/{n['id']}"
        if n["clase"] not in CLASES:
            inf.error(donde, "kind", f"unknown kind '{n['clase']}'", f"use one of {EN_KINDS}")
        if not n.get("nombre"):
            inf.error(donde, "missing-name", "node without a name", "every node has a readable name")
        for k, pub in (("x", "x"), ("y", "y"), ("w", "w"), ("h", "h")):
            if n.get(k, 0) % 4:
                inf.aviso(donde, "grid", f"{pub}={n.get(k)} is off the 4px grid", "use a multiple of 4")
        if n["x"] < 0 or n["y"] < 0 or n["x"] + n["w"] > W or n["y"] + n["h"] > H - alto_leyenda(diag):
            inf.error(donde, "off-canvas", "the node leaves the canvas or covers the legend strip",
                      f"move it or enlarge 'size' (the legend takes the last {alto_leyenda(diag):.0f} units)")
        largo_sub = max([len(x) for x in n["sub"]] + [0]) * 5.6 * esc
        if largo_sub > n["w"] - 12 or len(n["nombre"]) * 7.2 * esc > n["w"] - 12:
            inf.aviso(donde, "text-width", "text runs close to the node border", "shorten it or widen the node")
        if lineas_nodo(n, esc)[2] > n["y"] + n["h"] - 4:
            inf.error(donde, "text-height", "the text runs past the bottom of the node",
                      "make the node taller ('h'), drop a sub line, or lower 'text_scale'")
        for f in n.get("fuentes", []):
            verificar_fuente(f, raiz, donde, inf)
    for i, a in enumerate(nodos):
        for b in nodos[i + 1:]:
            if solapan((a["x"], a["y"], a["w"], a["h"]), (b["x"], b["y"], b["w"], b["h"])):
                inf.error(did, "nodes-overlap", f"{a['id']} and {b['id']} overlap", "separate them")
    ok = True
    for e in diag["aristas"]:
        donde = f"{did}/{e.get('de')}->{e.get('a')}"
        if e.get("de") not in idx or e.get("a") not in idx:
            inf.error(donde, "orphan-edge", "the edge points to a missing node", "check 'from' and 'to'")
            ok = False
        if e.get("lado_de") not in LADOS or e.get("lado_a") not in LADOS:
            inf.error(donde, "side", "invalid side", f"use {EN_SIDES}")
            ok = False
        if e["estilo"] not in ESTILOS:
            inf.error(donde, "style", f"unknown style '{e['estilo']}'", f"use {EN_STYLES}")
        for f in e.get("fuentes", []):
            verificar_fuente(f, raiz, donde, inf)
    if not ok:
        return
    _, fin_leyenda = items_leyenda(diag)
    if fin_leyenda > W - 24:
        inf.error(did, "legend", f"the legend overflows ({fin_leyenda:.0f} > {W - 24})",
                  "widen the canvas or use fewer distinct kinds and styles")
    rutas, rotulos = resolver(diag)
    rects = {n["id"]: (n["x"], n["y"], n["w"], n["h"]) for n in nodos}
    ar = diag["aristas"]
    nombre = lambda i: f"{ar[i]['de']}->{ar[i]['a']}"
    for i, pts in enumerate(rutas):
        for s in tramos(pts):
            for nid, r in rects.items():
                if nid not in (ar[i]["de"], ar[i]["a"]) and tramo_toca(s, r):
                    inf.error(f"{did}/{nombre(i)}", "passes-behind-node", f"the line passes behind {nid}",
                              "change 'mid', the sides, or move the node")
        for j in range(i + 1, len(rutas)):
            if any(cruzan(s, t) for s in tramos(pts) for t in tramos(rutas[j])):
                inf.error(f"{did}/{nombre(i)}", "crossing", f"crosses or overlaps {nombre(j)}",
                          "keep 'mid' values at least 12px apart or reorder the sides")
    zonas = [(z["x"] + z.get("rotulo_x", 12), z["y"] - 6 * esc, round((len(z["rotulo"]) * 5.6 + 12) * esc), 12 * esc)
             for z in diag["zonas"]]
    for z in diag["zonas"]:
        if z["x"] < 0 or z["y"] < 8 or z["x"] + z["w"] > W or z["y"] + z["h"] > H - alto_leyenda(diag):
            inf.error(f"{did}/zone", "zone-off-canvas", f"zone '{z['rotulo']}' leaves the canvas or covers the legend strip",
                      "shrink the zone or enlarge 'size' (the legend takes the last 60px)")
    for z, zr in zip(diag["zonas"], zonas):
        for i, pts in enumerate(rutas):
            if any(tramo_toca(s, zr, 2) for s in tramos(pts)):
                inf.error(f"{did}/zone", "line-cuts-zone-label", f"{nombre(i)} cuts the zone label '{z['rotulo']}'",
                          "shift the label with 'label_x' or change the line's 'mid'")
    for i, caja, texto in rotulos:
        donde = f"{did}/{nombre(i)}"
        for nid, r in rects.items():
            if solapan(caja, r):
                inf.error(donde, "label-over-node", f"label '{texto}' covers {nid}",
                          "move it with 'pos', 't' or 'segment', or shorten it")
        for j, pts in enumerate(rutas):
            pad = 5.5 if j == i else -0.5
            if any(tramo_toca(s, caja, pad) for s in tramos(pts)):
                inf.error(donde, "label-over-line", f"label '{texto}' covers the line {nombre(j)}",
                          "move it with 'pos' (above/below/left/right), 't' or 'segment'")
        for i2, caja2, t2 in rotulos:
            if i2 > i and solapan(caja, caja2):
                inf.error(donde, "labels-overlap", f"'{texto}' covers '{t2}'", "move one of them")
        for z in zonas:
            if solapan(caja, z):
                inf.aviso(donde, "label-over-zone-label", f"'{texto}' covers a zone label", "move it")
    for z, zr in zip(diag["zonas"], zonas):
        for nid, r in rects.items():
            if solapan(zr, r):
                inf.error(f"{did}/zone", "zone-label-over-node", f"zone label '{z['rotulo']}' covers {nid}",
                          "move the node down or the zone up")


def validar_documento(doc, base):
    inf = Informe()
    if doc.get("trazo") != 1:
        inf.error("document", "version", "missing \"trazo\": 1", "declare the schema version")
    raiz = (base / doc.get("repositorio", ".")).resolve()
    vistos = set()
    for s in doc.get("secciones", []):
        for v in s.get("vistas", []):
            if not isinstance(v.get("diagrama"), dict):
                inf.error(s.get("id", "?"), "missing-diagram", "a view has no 'diagram' object",
                          "every entry in 'views' needs a 'diagram'")
                continue
            d = normalizar(v["diagrama"])
            d["_lang"] = doc.get("lang", "en")
            d["_escala"] = float(d.get("escala_texto", doc.get("escala_texto", 1.0)))
            d["_imp"] = d.get("impresion", doc.get("impresion"))
            if d.get("id") in vistos:
                inf.error(d.get("id", "?"), "duplicate-diagram-id", "duplicate diagram id", "ids are unique per document")
            vistos.add(d.get("id"))
            validar_diagrama(d, raiz, inf)
    return inf
