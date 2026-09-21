#!/usr/bin/env python3
"""Trazo: diagrams as data. Python standard library only.

  trazo.py validate <doc.trazo.json> [--json]
  trazo.py build    <doc.trazo.json> <out.html> [--json]
  trazo.py capture  <out.html> <dir> [--theme light|dark|both]
  trazo.py test

Spanish aliases: validar, construir, captura, prueba.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from esquema import normalize  # noqa: E402
from validar import validar_documento  # noqa: E402
from pagina import construir  # noqa: E402

VERSION = "1.0.0"


def load(path):
    path = Path(path)
    raw = path.read_bytes()
    return normalize(json.loads(raw.decode("utf-8"))), raw, path.resolve().parent


def report(inf, as_json):
    if as_json:
        print(json.dumps(dict(errors=inf.errores, warnings=inf.advertencias), ensure_ascii=False, indent=2))
        return
    for x in inf.errores:
        print(f"ERROR  {x['where']}  [{x['code']}] {x['msg']}\n       -> {x['fix']}")
    for x in inf.advertencias:
        print(f"warn   {x['where']}  [{x['code']}] {x['msg']}\n       -> {x['fix']}")
    print(f"{len(inf.errores)} error(s), {len(inf.advertencias)} warning(s)")


def cmd_validate(args):
    doc, _, base = load(args[0])
    inf = validar_documento(doc, base)
    report(inf, "--json" in args)
    return 1 if inf.errores else 0


def cmd_build(args):
    doc, raw, base = load(args[0])
    out = Path(args[1])
    inf = validar_documento(doc, base)
    if inf.errores:
        report(inf, "--json" in args)
        print("not built: validation has errors (the previous output is left untouched)")
        return 1
    h_spec = hashlib.sha256(raw).hexdigest()
    stamp = f"{VERSION} - {date.today().isoformat()} - spec sha256 {h_spec[:12]}"
    html = construir(doc, stamp).encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=out.parent, prefix=".trazo-")
    with os.fdopen(fd, "wb") as f:
        f.write(html)
    os.replace(tmp, out)
    receipt = dict(output=str(out), spec_sha256=h_spec, spec_bytes=len(raw),
                   html_sha256=hashlib.sha256(html).hexdigest(), html_bytes=len(html),
                   diagrams=sum(len(s["vistas"]) for s in doc["secciones"]), warnings=len(inf.advertencias))
    print(json.dumps(receipt, indent=2) if "--json" in args else
          f"OK {out}  ({receipt['diagrams']} diagrams, {receipt['html_bytes']} bytes, "
          f"{receipt['warnings']} warnings)\n   spec {h_spec}\n   html {receipt['html_sha256']}")
    return 0


def browser():
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if shutil.which(name):
            return name
    return None


def cmd_capture(args):
    html, dest = Path(args[0]).resolve(), Path(args[1])
    themes = ["light", "dark"]
    flag = "--theme" if "--theme" in args else ("--tema" if "--tema" in args else None)
    if flag:
        t = {"claro": "light", "oscuro": "dark", "ambos": "both"}.get(args[args.index(flag) + 1], args[args.index(flag) + 1])
        themes = ["light", "dark"] if t == "both" else [t]
    nav = browser()
    if not nav:
        print("no Chrome or Chromium found: capture needs a machine with a browser")
        return 2
    dest.mkdir(parents=True, exist_ok=True)
    ids = [chunk.split('"', 1)[0] for chunk in
           html.read_text(encoding="utf-8").split('class="t-fig" data-diagrama="')[1:]]
    done = 0
    for slug in ids:
        for t in themes:
            png = dest / f"{slug}-{t}.png"
            subprocess.run([nav, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                            "--window-size=1440,900", f"--screenshot={png}",
                            f"file://{html}#solo={slug}&theme={t}"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
            done += png.exists()
    print(f"{done} capture(s) in {dest}  (1440x900; look at them: a capture does not approve the design)")
    return 0 if done == len(ids) * len(themes) else 1


def cmd_test(_):
    """Sources self-test: a diagram bound to a line stops validating when that line changes."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "code.py").write_text("def f():\n    return send_to_queue(msg)\n")
        spec = {"trazo": 1, "title": "test", "repository": ".", "sections": [{"id": "s", "views": [{
            "diagram": {"id": "p", "type": "flow", "title": "p", "description": "p", "size": [600, 260],
                        "nodes": [{"id": "a", "x": 40, "y": 40, "name": "Producer",
                                   "sources": [{"path": "code.py", "line": 2, "contains": "send_to_queue"}]},
                                  {"id": "b", "x": 360, "y": 40, "name": "Queue"}],
                        "edges": [{"from": "a", "from_side": "right", "to": "b", "to_side": "left", "label": "SENDS"}]}}]}]}

        def check():
            return validar_documento(normalize(json.loads(json.dumps(spec))), d)
        ok1 = not check().errores
        (d / "code.py").write_text("def f():\n    return publish(msg)\n")
        ok2 = any(x["code"] == "source-stale" for x in check().errores)
        (d / "code.py").unlink()
        ok3 = any(x["code"] == "source-missing" for x in check().errores)
    for name, ok in (("current source validates", ok1), ("changed line fails", ok2), ("deleted file fails", ok3)):
        print(("OK    " if ok else "FAIL  ") + name)
    return 0 if ok1 and ok2 and ok3 else 1


COMMANDS = {"validate": cmd_validate, "build": cmd_build, "capture": cmd_capture, "test": cmd_test,
            "validar": cmd_validate, "construir": cmd_build, "captura": cmd_capture, "prueba": cmd_test}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        return 2
    return COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
