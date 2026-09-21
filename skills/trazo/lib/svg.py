"""Trazo SVG rendering. Colors come from CSS classes (tokens on :root), never inline."""
import html

from geometria import resolver, trazo_d

NOMBRE_CLASE = {
    "es": {"foco": "Foco", "proceso": "Proceso", "estado": "Estado", "externo": "Externo",
           "persona": "Persona", "pendiente": "Pendiente", "gate": "Gate"},
    "en": {"foco": "Focus", "proceso": "Process", "estado": "State", "externo": "External",
           "persona": "Person", "pendiente": "Pending", "gate": "Gate"}}
NOMBRE_ESTILO = {
    "es": {"flujo": "flujo", "principal": "camino principal", "externo": "externo",
           "pendiente": "pendiente", "principal-pendiente": "principal, pendiente"},
    "en": {"flujo": "flow", "principal": "main path", "externo": "external",
           "pendiente": "pending", "principal-pendiente": "main, pending"}}
LEYENDA = {"es": "LEYENDA", "en": "LEGEND"}
FLECHA = {"flujo": "t-fl", "pendiente": "t-fl", "principal": "t-fl-acento",
          "principal-pendiente": "t-fl-acento", "externo": "t-fl-link"}
MONO = "font-family=\"'Latin Modern Mono', 'LM Mono 10', ui-monospace, monospace\""
SANS = MONO
# base sizes in canvas units; every one is multiplied by the diagram's text scale
T_NOMBRE, T_SUB, T_ROTULO, T_ETQ = 12, 9, 8, 7
LEYENDA_ALTO = 60


def e(s):
    return html.escape(str(s), quote=True)


def n(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def escala(diag):
    return diag.get("_escala", 1.0)


def alto_leyenda(diag):
    return LEYENDA_ALTO * escala(diag)


def items_leyenda(diag):
    s = escala(diag)
    clases, estilos = [], []
    for nodo in diag["nodos"]:
        if nodo["clase"] not in clases:
            clases.append(nodo["clase"])
    for a in diag["aristas"]:
        if a["estilo"] not in estilos:
            estilos.append(a["estilo"])
    lang = diag.get("_lang", "en")
    x, items = 100 * s, []
    for c in clases:
        items.append(("clase", c, x))
        x += (28 + len(NOMBRE_CLASE[lang][c]) * 5.2) * s
    for st in estilos:
        items.append(("estilo", st, x))
        x += (36 + len(NOMBRE_ESTILO[lang][st]) * 5.2) * s
    return items, x


def lineas_nodo(nodo, s):
    """Baselines of the name and sub lines, and the bottom of the last line."""
    y, h = nodo["y"], nodo["h"]
    sub, etq = nodo["sub"], nodo["etiqueta"]
    if h <= 56:
        top = y + h / 2 + (-4 if sub else 4) * s
    else:
        top = y + (6 + 24 * s if etq else 10 + 12 * s) + (0 if sub else 10 * s)
    subs = [top + (15 + j * 12) * s for j in range(len(sub))]
    fondo = (subs[-1] if subs else top) + 3 * s
    return top, subs, fondo


def svg(diag, slug):
    W, H = diag["tamano"]
    s = escala(diag)
    rutas, rotulos = resolver(diag)
    ly = H - 34 * s
    o = [f'<svg class="t-svg" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
         f'aria-labelledby="{slug}-title {slug}-desc" data-diagrama="{slug}">',
         f'<title id="{slug}-title">{e(diag["titulo"])}</title>',
         f'<desc id="{slug}-desc">{e(diag["descripcion"])}</desc>',
         '<defs>'
         f'<marker id="{slug}-fl" class="t-fl" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6"/></marker>'
         f'<marker id="{slug}-fl-acento" class="t-fl-acento" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6"/></marker>'
         f'<marker id="{slug}-fl-link" class="t-fl-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6"/></marker>'
         '</defs>',
         '<rect class="t-papel" width="100%" height="100%"/>']
    for z in diag["zonas"]:
        lw = round((len(z["rotulo"]) * 5.6 + 12) * s)
        rx = z["x"] + z.get("rotulo_x", 12)
        o.append(f'<rect class="t-zona" x="{z["x"]}" y="{z["y"]}" width="{z["w"]}" height="{z["h"]}" rx="8"/>')
        o.append(f'<rect class="t-mascara" x="{rx}" y="{n(z["y"] - 6 * s)}" width="{lw}" height="{n(12 * s)}" rx="2"/>')
        o.append(f'<text class="t-rotulo-zona" x="{n(rx + 6 * s)}" y="{n(z["y"] + 3 * s)}" font-size="{n(8 * s)}" {MONO} '
                 f'letter-spacing="0.14em">{e(z["rotulo"])}</text>')
    for i, pts in enumerate(rutas):
        a = diag["aristas"][i]
        o.append(f'<g class="t-arista s-{a["estilo"]}" data-i="{i}" data-de="{e(a["de"])}" data-a="{e(a["a"])}">'
                 f'<path class="t-toque" d="{trazo_d(pts)}"/>'
                 f'<path class="t-linea" d="{trazo_d(pts)}" marker-end="url(#{slug}-{FLECHA[a["estilo"]][2:]})"/></g>')
    for i, (x, y, w, h), texto in rotulos:
        a = diag["aristas"][i]
        o.append(f'<g class="t-rotulo" data-i="{i}" data-de="{e(a["de"])}" data-a="{e(a["a"])}">'
                 f'<rect class="t-mascara" x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="2"/>'
                 f'<text x="{x + w / 2:.1f}" y="{y + 9 * s:.1f}" font-size="{n(T_ROTULO * s)}" {MONO} text-anchor="middle" '
                 f'letter-spacing="0.06em">{e(texto)}</text></g>')
    for nodo in diag["nodos"]:
        x, y, w, h, c = nodo["x"], nodo["y"], nodo["w"], nodo["h"], nodo["clase"]
        cx = x + w / 2
        etq = nodo["etiqueta"]
        corto = nodo["nombre"] + (": " + nodo["sub"][0] if nodo["sub"] else "")
        o.append(f'<g class="t-nodo k-{c}" data-id="{e(nodo["id"])}" tabindex="0" role="button" '
                 f'aria-label="{e(corto)}">')
        o.append(f'<rect class="t-base" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>')
        o.append(f'<rect class="t-caja" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>')
        if etq:
            tw = round((len(etq) * 5.2 + 10) * s)
            o.append(f'<rect class="t-etq" x="{x + 8}" y="{y + 6}" width="{tw}" height="{n(12 * s)}" rx="2"/>')
            o.append(f'<text class="t-etq-txt" x="{x + 8 + tw / 2:.1f}" y="{n(y + 6 + 9 * s)}" font-size="{n(T_ETQ * s)}" {MONO} '
                     f'text-anchor="middle" letter-spacing="0.08em">{e(etq)}</text>')
        top, subs, _ = lineas_nodo(nodo, s)
        o.append(f'<text class="t-nombre" x="{cx}" y="{n(top)}" font-size="{n(T_NOMBRE * s)}" font-weight="700" {SANS} '
                 f'text-anchor="middle">{e(nodo["nombre"])}</text>')
        for linea, yy in zip(nodo["sub"], subs):
            o.append(f'<text class="t-sub" x="{cx}" y="{n(yy)}" font-size="{n(T_SUB * s)}" {MONO} '
                     f'text-anchor="middle">{e(linea)}</text>')
        if nodo.get("detalle") or nodo.get("fuentes"):
            o.append(f'<circle class="t-marca" cx="{x + w - 10}" cy="{y + 10}" r="2.5"/>')
        o.append('</g>')
    items, _ = items_leyenda(diag)
    lang = diag.get("_lang", "en")
    fs = n(8 * s)
    o.append(f'<g class="t-leyenda"><line class="t-regla" x1="24" y1="{n(ly - 8 * s)}" x2="{W - 24}" y2="{n(ly - 8 * s)}"/>'
             f'<text x="24" y="{n(ly + 10 * s)}" font-size="{fs}" {MONO} letter-spacing="0.14em">{LEYENDA[lang]}</text>')
    for tipo, cual, x in items:
        if tipo == "clase":
            o.append(f'<rect class="t-caja k-{cual} t-muestra" x="{n(x)}" y="{n(ly + 2 * s)}" width="{n(14 * s)}" height="{n(10 * s)}" rx="2"/>'
                     f'<text x="{n(x + 20 * s)}" y="{n(ly + 10 * s)}" font-size="{fs}" {MONO}>{NOMBRE_CLASE[lang][cual]}</text>')
        else:
            o.append(f'<line class="t-linea s-{cual}" x1="{n(x)}" y1="{n(ly + 7 * s)}" x2="{n(x + 22 * s)}" y2="{n(ly + 7 * s)}"/>'
                     f'<text x="{n(x + 28 * s)}" y="{n(ly + 10 * s)}" font-size="{fs}" {MONO}>{NOMBRE_ESTILO[lang][cual]}</text>')
    o.append('</g></svg>')
    return "\n".join(o)
