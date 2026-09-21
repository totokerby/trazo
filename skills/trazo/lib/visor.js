(function () {
  "use strict";
  var datos = JSON.parse(document.getElementById("trazo-datos").textContent);
  var T = JSON.parse(document.getElementById("trazo-textos").textContent);
  var raiz = document.documentElement;
  var TOKENS = ["--paper", "--node", "--ink", "--muted", "--soft", "--accent", "--accent-tint", "--link",
    "--ink-02", "--ink-03", "--ink-05", "--ink-10", "--ink-20", "--ink-22", "--ink-30", "--muted-10",
    "--accent-05", "--accent-50", "--zone"];

  function el(tag, attrs, hijos) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "texto") n.textContent = attrs[k]; else n.setAttribute(k, attrs[k]);
    });
    (hijos || []).forEach(function (h) { if (h) n.appendChild(h); });
    return n;
  }
  function leer(k, def) { try { return localStorage.getItem(k) || def; } catch (e) { return def; } }
  function guardar(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* no storage */ } }
  function plano(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }

  // hash parameters: theme=light|dark (or tema=claro|oscuro), solo=<diagram id> (isolated capture)
  var hash = {};
  location.hash.replace(/^#/, "").split("&").forEach(function (p) {
    var kv = p.split("="); if (kv[0]) hash[kv[0]] = decodeURIComponent(kv[1] || "");
  });

  // ---- theme
  var pedido = hash.theme || hash.tema;
  var tema = pedido ? ((pedido === "dark" || pedido === "oscuro") ? "dark" : "light") : leer("trazo-tema", "auto");
  var btnTema = el("button", { "class": "t-btn", type: "button" });
  function aplicarTema(t) {
    tema = t;
    if (t === "auto") raiz.removeAttribute("data-theme"); else raiz.setAttribute("data-theme", t);
    btnTema.textContent = T.tema + ": " + T[t];
  }
  btnTema.addEventListener("click", function () {
    var sig = { auto: "light", light: "dark", dark: "auto" }[tema];
    aplicarTema(sig); guardar("trazo-tema", sig);
  });
  aplicarTema(tema);

  // ---- search
  var buscar = el("input", { "class": "t-buscar", type: "search", placeholder: T.buscar,
    "aria-label": T.buscarAria });
  var cuenta = el("span", { "class": "t-cuenta", "aria-live": "polite" });
  var controles = document.querySelector(".t-controles");
  if (controles) { controles.appendChild(buscar); controles.appendChild(cuenta); controles.appendChild(btnTema); }

  var figuras = [];
  Array.prototype.forEach.call(document.querySelectorAll(".t-fig"), function (fig) {
    var slug = fig.getAttribute("data-diagrama");
    var d = datos[slug];
    if (!d) return;
    var svg = fig.querySelector("svg");
    var lienzo = fig.querySelector(".t-lienzo");
    var tip = fig.querySelector(".t-tip");
    var panel = fig.querySelector(".t-panel");
    var nodos = {};
    Array.prototype.forEach.call(svg.querySelectorAll(".t-nodo"), function (n) { nodos[n.getAttribute("data-id")] = n; });
    var aristas = svg.querySelectorAll(".t-arista, .t-rotulo");
    var sel = null;
    var fg = { fig: fig, slug: slug, nodos: nodos, d: d };
    figuras.push(fg);

    function vecinos(id) {
      var sale = [], entra = [];
      d.aristas.forEach(function (a) {
        if (a.de === id) sale.push(a);
        if (a.a === id) entra.push(a);
      });
      return { sale: sale, entra: entra };
    }
    function limpiar() {
      fig.classList.remove("t-foco");
      Array.prototype.forEach.call(svg.querySelectorAll(".t-on"), function (x) { x.classList.remove("t-on"); });
    }
    function iluminar(id) {
      limpiar();
      fig.classList.add("t-foco");
      nodos[id].classList.add("t-on");
      Array.prototype.forEach.call(aristas, function (g) {
        if (g.getAttribute("data-de") === id || g.getAttribute("data-a") === id) {
          g.classList.add("t-on");
          var otro = g.getAttribute("data-de") === id ? g.getAttribute("data-a") : g.getAttribute("data-de");
          if (nodos[otro]) nodos[otro].classList.add("t-on");
        }
      });
    }
    function iluminarArista(i) {
      limpiar();
      fig.classList.add("t-foco");
      var a = d.aristas[i];
      Array.prototype.forEach.call(svg.querySelectorAll('[data-i="' + i + '"]'), function (g) { g.classList.add("t-on"); });
      nodos[a.de].classList.add("t-on");
      nodos[a.a].classList.add("t-on");
    }
    function restaurar() { if (sel) iluminar(sel); else limpiar(); tip.hidden = true; }
    function ubicar(objetivo) {
      var r = objetivo.getBoundingClientRect(), f = fig.getBoundingClientRect();
      var x = r.left - f.left, y = r.bottom - f.top + 8;
      tip.hidden = false;
      var ancho = tip.offsetWidth;
      tip.style.left = Math.max(0, Math.min(x, f.width - ancho)) + "px";
      tip.style.top = y + "px";
    }
    function rel(a, id) {
      var otro = a.de === id ? a.a : a.de;
      return (a.de === id ? "-> " : "<- ") + d.nodos[otro].nombre + (a.texto ? " (" + a.texto.toLowerCase() + ")" : "");
    }
    function tipNodo(id) {
      var n = d.nodos[id], v = vecinos(id);
      tip.textContent = "";
      tip.appendChild(el("b", { texto: n.nombre }));
      var todas = v.sale.concat(v.entra);
      var lista = el("div", { "class": "t-lista" });
      if (!todas.length) lista.textContent = T.sinRel;
      todas.forEach(function (a) { lista.appendChild(el("div", { texto: rel(a, id) })); });
      tip.appendChild(lista);
      if (n.detalle || n.fuentes.length) tip.appendChild(el("div", { "class": "t-lista", texto: T.clic }));
      ubicar(nodos[id]);
    }
    function tipArista(i, g) {
      var a = d.aristas[i];
      tip.textContent = "";
      tip.appendChild(el("b", { texto: d.nodos[a.de].nombre + " -> " + d.nodos[a.a].nombre }));
      if (a.texto) tip.appendChild(el("div", { "class": "t-lista", texto: a.texto }));
      if (a.detalle) tip.appendChild(el("div", { texto: a.detalle }));
      ubicar(g);
    }
    function mostrar(id) {
      if (sel && nodos[sel]) nodos[sel].classList.remove("t-sel");
      sel = id;
      nodos[id].classList.add("t-sel");
      iluminar(id);
      var n = d.nodos[id], v = vecinos(id);
      panel.textContent = "";
      var izq = el("div", {}, [
        n.etiqueta ? el("p", { "class": "eyebrow", texto: n.etiqueta }) : null,
        el("h4", { texto: n.nombre }),
        n.sub.length ? el("div", { "class": "t-subs", texto: n.sub.join(" / ") }) : null,
        el("p", { texto: n.detalle || T.sinDetalle })
      ]);
      var der = el("div", {});
      function grupo(titulo, lista) {
        if (!lista.length) return;
        var ul = el("ul", {});
        lista.forEach(function (a) {
          var otro = a.de === id ? a.a : a.de;
          var b = el("button", { "class": "t-vecino", type: "button", texto: d.nodos[otro].nombre });
          b.addEventListener("click", function () { mostrar(otro); nodos[otro].focus(); });
          ul.appendChild(el("li", {}, [b, a.texto ? el("span", { "class": "t-rel", texto: "  " + a.texto }) : null]));
        });
        der.appendChild(el("div", { "class": "t-grupo" }, [el("p", { "class": "eyebrow", texto: titulo }), ul]));
      }
      grupo(T.envia, v.sale);
      grupo(T.recibe, v.entra);
      if (!v.sale.length && !v.entra.length) der.appendChild(el("p", { "class": "t-rel", texto: T.sinRel }));
      if (n.fuentes.length) {
        var ul = el("ul", {});
        n.fuentes.forEach(function (f) { ul.appendChild(el("li", { "class": "t-fuente", texto: f })); });
        der.appendChild(el("div", { "class": "t-grupo" }, [el("p", { "class": "eyebrow", texto: T.fuentes }), ul]));
      }
      var cerrar = el("button", { "class": "t-btn t-cerrar", type: "button", texto: T.cerrar, "aria-label": T.cerrarAria });
      cerrar.addEventListener("click", ocultar);
      panel.appendChild(izq); panel.appendChild(der);
      der.appendChild(cerrar);
      panel.hidden = false;
      tip.hidden = true;
    }
    function ocultar() {
      if (sel && nodos[sel]) nodos[sel].classList.remove("t-sel");
      sel = null; panel.hidden = true; limpiar();
    }
    fg.mostrar = mostrar;

    Object.keys(nodos).forEach(function (id) {
      var n = nodos[id];
      n.addEventListener("mouseenter", function () { iluminar(id); tipNodo(id); });
      n.addEventListener("mouseleave", restaurar);
      n.addEventListener("focus", function () { iluminar(id); tipNodo(id); });
      n.addEventListener("blur", restaurar);
      n.addEventListener("click", function () { mostrar(id); });
      n.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); mostrar(id); }
        if (ev.key === "Escape") ocultar();
      });
    });
    Array.prototype.forEach.call(svg.querySelectorAll(".t-arista"), function (g) {
      var i = +g.getAttribute("data-i");
      g.addEventListener("mouseenter", function () { iluminarArista(i); tipArista(i, g); });
      g.addEventListener("mouseleave", restaurar);
    });

    // ---- toolbar: zoom, export
    var escala = 1;
    function zoom(f) {
      escala = f === 0 ? 1 : Math.min(3, Math.max(1, escala * f));
      svg.style.width = (escala * 100) + "%";
      svg.style.minWidth = (900 * escala) + "px";
      lienzo.classList.toggle("t-zoom", escala > 1);
      bz.textContent = Math.round(escala * 100) + "%";
    }
    var menos = el("button", { "class": "t-btn", type: "button", texto: "-", "aria-label": T.alejar });
    var bz = el("button", { "class": "t-btn", type: "button", texto: "100%", "aria-label": T.original });
    var mas = el("button", { "class": "t-btn", type: "button", texto: "+", "aria-label": T.acercar });
    var exp = el("button", { "class": "t-btn", type: "button", texto: "SVG", "aria-label": T.svg });
    menos.addEventListener("click", function () { zoom(1 / 1.25); });
    bz.addEventListener("click", function () { zoom(0); });
    mas.addEventListener("click", function () { zoom(1.25); });
    exp.addEventListener("click", function () {
      var copia = svg.cloneNode(true);
      Array.prototype.forEach.call(copia.querySelectorAll(".t-on, .t-sel, .t-match"), function (x) {
        x.classList.remove("t-on", "t-sel", "t-match");
      });
      copia.removeAttribute("style");
      var cs = getComputedStyle(raiz);
      var vars = TOKENS.map(function (t) { return t + ":" + cs.getPropertyValue(t).trim(); }).join(";");
      var css = document.getElementById("trazo-caras").textContent + document.getElementById("trazo-css-svg").textContent;
      var st = document.createElementNS("http://www.w3.org/2000/svg", "style");
      st.textContent = "svg{" + vars + "}" + css;
      copia.insertBefore(st, copia.querySelector("defs"));
      var blob = new Blob([new XMLSerializer().serializeToString(copia)], { type: "image/svg+xml" });
      var a = el("a", { href: URL.createObjectURL(blob), download: slug + ".svg" });
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    });
    var barra = fig.querySelector(".t-barra");
    [menos, bz, mas, exp].forEach(function (b) { barra.appendChild(b); });

    // drag to pan while zoomed
    var ini = null;
    lienzo.addEventListener("pointerdown", function (ev) {
      if (escala === 1 || ev.target.closest(".t-nodo")) return;
      ini = { x: ev.clientX, y: ev.clientY, l: lienzo.scrollLeft, t: lienzo.scrollTop };
      lienzo.classList.add("t-arrastre");
    });
    window.addEventListener("pointermove", function (ev) {
      if (!ini) return;
      lienzo.scrollLeft = ini.l - (ev.clientX - ini.x);
      lienzo.scrollTop = ini.t - (ev.clientY - ini.y);
    });
    window.addEventListener("pointerup", function () { ini = null; lienzo.classList.remove("t-arrastre"); });
  });

  // ---- global search
  var primera = null;
  buscar.addEventListener("input", function () {
    var q = plano(buscar.value.trim()), total = 0;
    primera = null;
    figuras.forEach(function (fg) {
      Object.keys(fg.nodos).forEach(function (id) {
        var n = fg.d.nodos[id];
        var texto = plano([n.nombre, n.etiqueta, n.sub.join(" "), n.detalle, n.fuentes.join(" ")].join(" "));
        var ok = q.length > 1 && texto.indexOf(q) >= 0;
        fg.nodos[id].classList.toggle("t-match", ok);
        if (ok) { total++; if (!primera) primera = { fg: fg, id: id }; }
      });
    });
    cuenta.textContent = q.length > 1 ? (total + " " + (total === 1 ? T.nodo : T.nodos)) : "";
  });
  buscar.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" && primera) {
      primera.fg.nodos[primera.id].scrollIntoView({ block: "center" });
      primera.fg.mostrar(primera.id);
    }
  });

  if (hash.solo) {
    var fig = document.querySelector('.t-fig[data-diagrama="' + hash.solo + '"]');
    if (fig) {
      raiz.classList.add("t-solo");
      fig.closest("section").classList.add("t-visible");
      fig.closest(".t-vista").classList.add("t-visible");
    }
  }
})();
