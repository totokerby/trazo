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


def e(s):
    return html.escape(str(s), quote=True)


def items_leyenda(diag):
    clases, estilos = [], []
    for n in diag["nodos"]:
        if n["clase"] not in clases:
            clases.append(n["clase"])
    for a in diag["aristas"]:
        if a["estilo"] not in estilos:
            estilos.append(a["estilo"])
    lang = diag.get("_lang", "en")
    x, items = 100, []
    for c in clases:
        items.append(("clase", c, x))
        x += 28 + len(NOMBRE_CLASE[lang][c]) * 5.2
    for s in estilos:
        items.append(("estilo", s, x))
        x += 36 + len(NOMBRE_ESTILO[lang][s]) * 5.2
    return items, x


def svg(diag, slug):
    W, H = diag["tamano"]
    rutas, rotulos = resolver(diag)
    ly = H - 34
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
        lw = round(len(z["rotulo"]) * 5.6 + 12)
        o.append(f'<rect class="t-zona" x="{z["x"]}" y="{z["y"]}" width="{z["w"]}" height="{z["h"]}" rx="8"/>')
        rx = z["x"] + z.get("rotulo_x", 12)
        o.append(f'<rect class="t-mascara" x="{rx}" y="{z["y"] - 6}" width="{lw}" height="12" rx="2"/>')
        o.append(f'<text class="t-rotulo-zona" x="{rx + 6}" y="{z["y"] + 3}" font-size="8" {MONO} '
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
                 f'<text x="{x + w / 2:.1f}" y="{y + 9:.1f}" font-size="8" {MONO} text-anchor="middle" '
                 f'letter-spacing="0.06em">{e(texto)}</text></g>')
    for n in diag["nodos"]:
        x, y, w, h, c = n["x"], n["y"], n["w"], n["h"], n["clase"]
        cx = x + w / 2
        etq = n["etiqueta"]
        corto = n["nombre"] + (": " + n["sub"][0] if n["sub"] else "")
        o.append(f'<g class="t-nodo k-{c}" data-id="{e(n["id"])}" tabindex="0" role="button" '
                 f'aria-label="{e(corto)}">')
        o.append(f'<rect class="t-base" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>')
        o.append(f'<rect class="t-caja" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>')
        if etq:
            tw = round(len(etq) * 5.2 + 10)
            o.append(f'<rect class="t-etq" x="{x + 8}" y="{y + 6}" width="{tw}" height="12" rx="2"/>')
            o.append(f'<text class="t-etq-txt" x="{x + 8 + tw / 2:.1f}" y="{y + 15}" font-size="7" {MONO} '
                     f'text-anchor="middle" letter-spacing="0.08em">{e(etq)}</text>')
        sub = n["sub"]
        if h <= 56:
            top = y + h / 2 + (-4 if sub else 4)
        else:
            top = y + (30 if etq else 22) + (0 if sub else 10)
        o.append(f'<text class="t-nombre" x="{cx}" y="{top}" font-size="12" font-weight="700" {SANS} '
                 f'text-anchor="middle">{e(n["nombre"])}</text>')
        for j, s in enumerate(sub):
            o.append(f'<text class="t-sub" x="{cx}" y="{top + 15 + j * 12}" font-size="9" {MONO} '
                     f'text-anchor="middle">{e(s)}</text>')
        if n.get("detalle") or n.get("fuentes"):
            o.append(f'<circle class="t-marca" cx="{x + w - 10}" cy="{y + 10}" r="2.5"/>')
        o.append('</g>')
    items, _ = items_leyenda(diag)
    lang = diag.get("_lang", "en")
    o.append(f'<g class="t-leyenda"><line class="t-regla" x1="24" y1="{ly - 8}" x2="{W - 24}" y2="{ly - 8}"/>'
             f'<text x="24" y="{ly + 10}" font-size="8" {MONO} letter-spacing="0.14em">{LEYENDA[lang]}</text>')
    for tipo, cual, x in items:
        if tipo == "clase":
            o.append(f'<rect class="t-caja k-{cual} t-muestra" x="{x}" y="{ly + 2}" width="14" height="10" rx="2"/>'
                     f'<text x="{x + 20}" y="{ly + 10}" font-size="8" {MONO}>{NOMBRE_CLASE[lang][cual]}</text>')
        else:
            o.append(f'<line class="t-linea s-{cual}" x1="{x}" y1="{ly + 7}" x2="{x + 22}" y2="{ly + 7}"/>'
                     f'<text x="{x + 28}" y="{ly + 10}" font-size="8" {MONO}>{NOMBRE_ESTILO[lang][cual]}</text>')
    o.append('</g></svg>')
    return "\n".join(o)
