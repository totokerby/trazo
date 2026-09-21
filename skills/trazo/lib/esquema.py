"""Schema aliases: the public schema is English; Spanish keys are accepted too. Both normalize to the
internal names used by the rest of the package."""

DOC = {"repository": "repositorio", "footer": "pie", "title": "titulo", "sections": "secciones"}
SECTION = {"title": "titulo", "lead": "bajada", "views": "vistas", "cards": "tarjetas"}
VIEW = {"label": "rotulo", "diagram": "diagrama"}
CARD = {"title": "titulo", "accent": "acento"}
DIAGRAM = {"type": "tipo", "title": "titulo", "description": "descripcion", "size": "tamano",
           "zones": "zonas", "nodes": "nodos", "edges": "aristas"}
ZONE = {"label": "rotulo", "label_x": "rotulo_x"}
NODE = {"kind": "clase", "tag": "etiqueta", "name": "nombre", "detail": "detalle", "sources": "fuentes"}
EDGE = {"from": "de", "to": "a", "from_side": "lado_de", "to_side": "lado_a", "label": "texto",
        "style": "estilo", "mid": "medio", "segment": "tramo", "detail": "detalle", "order": "orden",
        "sources": "fuentes"}
SOURCE = {"path": "ruta", "line": "linea", "contains": "contiene"}

TYPES = {"architecture": "arquitectura", "flow": "flujo", "org": "organigrama", "layers": "capas"}
KINDS = {"focus": "foco", "process": "proceso", "state": "estado", "external": "externo",
         "person": "persona", "pending": "pendiente", "gate": "gate"}
STYLES = {"flow": "flujo", "main": "principal", "external": "externo", "pending": "pendiente",
          "main-pending": "principal-pendiente"}
SIDES = {"left": "izq", "right": "der", "top": "arriba", "bottom": "abajo"}
POS = {"above": "arriba", "below": "abajo", "left": "izq", "right": "der"}


def _keys(d, mapping):
    for en, es in mapping.items():
        if en in d and es not in d:
            d[es] = d.pop(en)
    return d


def _fuentes(obj):
    for f in obj.get("fuentes", []):
        _keys(f, SOURCE)


def normalize(doc):
    doc = _keys(doc, DOC)
    if "lang" not in doc:
        doc["lang"] = "en"
    for s in doc.get("secciones", []):
        _keys(s, SECTION)
        for c in s.get("tarjetas", []):
            _keys(c, CARD)
        for v in s.get("vistas", []):
            _keys(v, VIEW)
            d = _keys(v["diagrama"], DIAGRAM)
            d["tipo"] = TYPES.get(d.get("tipo"), d.get("tipo"))
            for z in d.get("zonas", []):
                _keys(z, ZONE)
            for n in d.get("nodos", []):
                _keys(n, NODE)
                if "clase" in n:
                    n["clase"] = KINDS.get(n["clase"], n["clase"])
                _fuentes(n)
            for e in d.get("aristas", []):
                _keys(e, EDGE)
                for k in ("lado_de", "lado_a"):
                    if k in e:
                        e[k] = SIDES.get(e[k], e[k])
                if "estilo" in e:
                    e["estilo"] = STYLES.get(e["estilo"], e["estilo"])
                if "pos" in e:
                    e["pos"] = POS.get(e["pos"], e["pos"])
                _fuentes(e)
    return doc
