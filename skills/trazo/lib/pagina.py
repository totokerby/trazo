"""Trazo self-contained HTML page: document, sections, views, cards and viewer."""
import base64
import html
import json
from pathlib import Path

from svg import svg

AQUI = Path(__file__).resolve().parent
CARAS = (("lmmono12-regular.otf", "normal", 400), ("lmmono10-italic.otf", "italic", 400),
         ("lmmonolt10-bold.otf", "normal", 700))


def fuentes():
    # Latin Modern Mono: LaTeX's typewriter face (\ttdefault with lmodern). GUST Font License.
    out = []
    for archivo, estilo, peso in CARAS:
        b64 = base64.b64encode((AQUI / "fonts" / archivo).read_bytes()).decode("ascii")
        out.append(f"@font-face{{font-family:'Latin Modern Mono';font-style:{estilo};font-weight:{peso};"
                   f"font-display:swap;src:url(data:font/otf;base64,{b64}) format('opentype')}}")
    return "".join(out)


TEXTOS = {
    "en": dict(tema="Theme", auto="auto", light="light", dark="dark", buscar="Search nodes, details or sources",
               buscarAria="Search the diagrams", sinRel="no relations drawn", clic="click for details",
               sinDetalle="No detail for this node.", envia="Sends to", recibe="Receives from",
               fuentes="Sources verified at build", cerrar="Close", cerrarAria="Close the detail panel",
               alejar="Zoom out", original="Original size", acercar="Zoom in", svg="Download the diagram as SVG",
               nodo="node", nodos="nodes", nav="Sections"),
    "es": dict(tema="Tema", auto="auto", light="claro", dark="oscuro", buscar="Buscar nodo, detalle o fuente",
               buscarAria="Buscar en los diagramas", sinRel="sin relaciones dibujadas", clic="clic para ver el detalle",
               sinDetalle="Sin detalle cargado para este nodo.", envia="Envia a", recibe="Recibe de",
               fuentes="Fuentes verificadas al construir", cerrar="Cerrar", cerrarAria="Cerrar el detalle",
               alejar="Alejar", original="Tamano original", acercar="Acercar", svg="Descargar el diagrama como SVG",
               nodo="nodo", nodos="nodos", nav="Secciones"),
}


def tokens(css, tema):
    """CSS custom properties of the light (:root) or dark ([data-theme="dark"]) block."""
    marca = ":root {" if tema == "light" else ':root[data-theme="dark"] {'
    bloque = css[css.index(marca) + len(marca):]
    bloque = bloque[:bloque.index("}")]
    return ";".join(d.strip() for d in bloque.split(";") if d.strip().startswith("--"))


def exportar_svg(diag, tema="light"):
    """Standalone SVG: same markup as the page, with theme tokens resolved and fonts embedded."""
    css = (AQUI / "visor.css").read_text(encoding="utf-8")
    css_svg = css[css.index("/* SVG"):css.index("/* interaction")]
    estilo = f"<style>svg{{{tokens(css, tema)}}}{fuentes()}{css_svg}</style>"
    marcado = svg(diag, diag["id"])
    return marcado.replace("<defs>", estilo + "<defs>", 1)


def e(s):
    return html.escape(str(s), quote=True)


def ref_fuente(f):
    return f["ruta"] + (f":{f['linea']}" if f.get("linea") else "") + (f"  ({f['contiene']})" if f.get("contiene") else "")


def datos_visor(diag):
    return dict(
        nodos={n["id"]: dict(nombre=n["nombre"], etiqueta=n["etiqueta"], sub=n["sub"], detalle=n.get("detalle", ""),
                             fuentes=[ref_fuente(f) for f in n.get("fuentes", [])]) for n in diag["nodos"]},
        aristas=[dict(de=a["de"], a=a["a"], texto=a.get("texto", ""), detalle=a.get("detalle", ""))
                 for a in diag["aristas"]])


def tarjetas(lista):
    if not lista:
        return ""
    out = []
    for t in lista:
        items = "".join(f"<li>{e(i)}</li>" for i in t.get("items", []))
        punto = "dot coral" if t.get("acento") else "dot"
        eb = f'<p class="eyebrow">{e(t["eyebrow"])}</p>' if t.get("eyebrow") else ""
        out.append(f'<div class="card">{eb}<div class="card-header"><span class="{punto}"></span>'
                   f'<h4>{e(t["titulo"])}</h4></div><ul>{items}</ul></div>')
    clase = "cards una" if len(lista) == 1 else "cards"
    return f'<div class="{clase}">' + "".join(out) + "</div>"


def construir(doc, sello):
    css = (AQUI / "visor.css").read_text(encoding="utf-8")
    caras = fuentes()
    css_svg = css[css.index("/* SVG"):css.index("/* interaction")]
    js = (AQUI / "visor.js").read_text(encoding="utf-8")
    datos, secciones, nav = {}, [], []
    for s in doc["secciones"]:
        vistas = []
        for v in s["vistas"]:
            d = v["diagrama"]
            datos[d["id"]] = datos_visor(d)
            rot = f'<h3>{e(v["rotulo"])}</h3>' if v.get("rotulo") else ""
            vistas.append(
                f'<div class="t-vista">{rot}<figure class="t-fig" data-diagrama="{e(d["id"])}">'
                f'<div class="t-barra"></div><div class="t-lienzo">{svg(d, d["id"])}</div>'
                f'<div class="t-tip" hidden></div><div class="t-panel" hidden aria-live="polite"></div></figure></div>')
        eb = f'<p class="eyebrow">{e(s["eyebrow"])}</p>' if s.get("eyebrow") else ""
        bajada = f'<p class="lead">{e(s["bajada"])}</p>' if s.get("bajada") else ""
        titulo = f'<h2>{e(s["titulo"])}</h2>' if s.get("titulo") else ""
        secciones.append(f'<section id="{e(s["id"])}">{eb}{titulo}{bajada}{"".join(vistas)}'
                         f'{tarjetas(s.get("tarjetas"))}</section>')
        if s.get("titulo") and len(doc["secciones"]) > 1:
            nav.append(f'<a href="#{e(s["id"])}">{e(s.get("nav", s["titulo"]))}</a>')
    lang = doc.get("lang", "en")
    textos = TEXTOS.get(lang, TEXTOS["en"])
    datos_json = json.dumps(datos, ensure_ascii=True).replace("</", "<\\/")
    textos_json = json.dumps(textos, ensure_ascii=True)
    eb = f'<p class="eyebrow">{e(doc["eyebrow"])}</p>' if doc.get("eyebrow") else ""
    intro = f'<p class="intro">{e(doc["intro"])}</p>' if doc.get("intro") else ""
    navh = f'<nav aria-label="{textos["nav"]}">{"".join(nav)}</nav>' if nav else ""
    pie = e(doc.get("pie", ""))
    return (
        '<!DOCTYPE html>\n<html lang="' + lang + '">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{e(doc["titulo"])}</title>\n<style id="trazo-caras">{caras}</style>\n<style>{css}</style>\n</head>\n<body>\n<div class="frame">\n'
        f'{eb}<h1>{e(doc["titulo"])}</h1>{intro}<div class="t-controles"></div>{navh}\n'
        + "\n".join(secciones) +
        f'\n<footer>{pie}<br>Trazo {sello}</footer>\n</div>\n'
        f'<script type="text/plain" id="trazo-css-svg">{css_svg}</script>\n'
        f'<script type="application/json" id="trazo-datos">{datos_json}</script>\n'
        f'<script type="application/json" id="trazo-textos">{textos_json}</script>\n'
        f'<script>{js}</script>\n</body>\n</html>\n')
