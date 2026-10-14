#!/usr/bin/env python3
"""Construye la sección de artículos de h-corpus.com a partir de los borradores en Markdown.

Uso, desde la raíz del repositorio:

    python3 herramientas/construir_articulos.py

Qué hace, en orden:
  1. Normaliza las URLs de todo site/: enlaces internos, canonical, og:url, JSON-LD y
     sitemap quedan absolutos y sin ".html" (/metodologia, /servicios/, /articulos/x),
     que es donde Cloudflare aterriza después de redirigir.
  2. Convierte cada articulo_*.md de la raíz en site/articulos/<slug>.html.
  3. Regenera site/articulos/index.html y las entradas de artículos del sitemap.

Los borradores .md no se suben a GitHub (están en .gitignore); el HTML generado sí.
Formato del borrador: ver plantillas/articulo.md. Sin dependencias externas.
"""
import html
import json
import pathlib
import posixpath
import re
import struct
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE = REPO / "site"
DOMINIO = "https://h-corpus.com"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


# ---------------------------------------------------------------------------
# 1. Normalización de URLs
# ---------------------------------------------------------------------------

def url_limpia(ruta):
    """/x.html -> /x ; /x/index.html -> /x/ ; /index.html -> /"""
    if ruta.endswith("/index.html"):
        return ruta[: -len("index.html")]
    if ruta.endswith(".html"):
        return ruta[: -len(".html")]
    return ruta


def normalizar_html(texto, url_pagina):
    base = posixpath.dirname(url_pagina).rstrip("/") + "/"

    def href(m):
        valor = m.group(1)
        if re.match(r"^(?:[a-z]+:|#|//)", valor):
            return m.group(0)
        ruta, sep, frag = valor.partition("#")
        if not ruta.endswith(".html"):
            return m.group(0)
        absoluta = posixpath.normpath(posixpath.join(base, ruta))
        absoluta = "/" + absoluta.lstrip("/")
        return f'href="{url_limpia(absoluta)}{sep}{frag}"'

    texto = re.sub(r'href="([^"]*)"', href, texto)
    texto = re.sub(re.escape(DOMINIO) + r'(/[^"\s<]*?\.html)\b',
                   lambda m: DOMINIO + url_limpia(m.group(1)), texto)
    return texto


def normalizar_sitio():
    cambiados = 0
    for f in sorted(SITE.rglob("*.html")):
        if f.name.startswith("google"):
            continue
        rel = "/" + f.relative_to(SITE).as_posix()
        antes = f.read_text(encoding="utf-8")
        despues = normalizar_html(antes, rel)
        if despues != antes:
            f.write_text(despues, encoding="utf-8")
            cambiados += 1
    sm = SITE / "sitemap.xml"
    s = sm.read_text(encoding="utf-8")
    s2 = re.sub(re.escape(DOMINIO) + r'(/[^<]*?\.html)<', lambda m: DOMINIO + url_limpia(m.group(1)) + "<", s)
    if s2 != s:
        sm.write_text(s2, encoding="utf-8")
        cambiados += 1
    print(f"URLs normalizadas en {cambiados} archivos")


# ---------------------------------------------------------------------------
# 2. Markdown -> HTML (el subconjunto que usan los artículos)
# ---------------------------------------------------------------------------

def leer_front_matter(texto):
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    if not m:
        raise ValueError("falta el bloque --- inicial con los metadatos")
    meta, lista = {}, None
    for linea in m.group(1).splitlines():
        if re.match(r"^\s+-\s+", linea) and lista is not None:
            meta[lista].append(linea.split("-", 1)[1].strip())
            continue
        k, _, v = linea.partition(":")
        k, v = k.strip(), v.strip()
        if not k:
            continue
        if v == "":
            meta[k], lista = [], k
        else:
            meta[k], lista = v.strip('"'), None
    return meta, texto[m.end():]


class Conversor:
    def __init__(self, slugs):
        self.slugs = slugs

    def enlace(self, url):
        m = re.match(r"^/articulos/([a-z0-9-]+)\.html$", url)
        if m:
            if m.group(1) not in self.slugs:
                raise ValueError(f"enlace a un artículo que no existe: {url}")
            return f"/articulos/{m.group(1)}"
        if url.startswith("/"):
            return url_limpia(url)
        return url

    def en_linea(self, texto):
        guardados = []

        def guardar(fragmento):
            guardados.append(fragmento)
            return f"\x00{len(guardados) - 1}\x00"

        texto = re.sub(r"`([^`]+)`", lambda m: guardar(f"<code>{html.escape(m.group(1), quote=False)}</code>"), texto)

        def link(m):
            url = self.enlace(m.group(2))
            externo = ' rel="noopener" target="_blank"' if url.startswith("http") else ""
            return guardar(f'<a href="{html.escape(url)}"{externo}>{self.en_linea(m.group(1))}</a>')

        texto = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, texto)
        texto = html.escape(texto, quote=False)
        texto = re.sub(r'"([^"\n]+)"', r"«\1»", texto)
        texto = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texto)
        texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", texto)
        return re.sub(r"\x00(\d+)\x00", lambda m: guardados[int(m.group(1))], texto)

    def tabla(self, filas):
        celdas = [[c.strip() for c in f.strip().strip("|").split("|")] for f in filas]
        cab, cuerpo = celdas[0], [c for c in celdas[1:] if not all(re.fullmatch(r":?-+:?", x) for x in c)]
        th = "".join(f'<th scope="col">{self.en_linea(c)}</th>' for c in cab)
        trs = "\n".join(
            "<tr>" + f'<th scope="row">{self.en_linea(f[0])}</th>' + "".join(f"<td>{self.en_linea(c)}</td>" for c in f[1:]) + "</tr>"
            for f in cuerpo)
        return ('<div class="service-table-wrap">\n<table class="service-table">\n'
                f"<thead><tr>{th}</tr></thead>\n<tbody>\n{trs}\n</tbody>\n</table>\n</div>")

    def bloques(self, texto):
        """Devuelve una lista de (tipo, html)."""
        lineas = texto.splitlines()
        out, parrafo, i = [], [], 0

        def cerrar_parrafo():
            if parrafo:
                out.append(("p", f"<p>{self.en_linea(' '.join(parrafo))}</p>"))
                parrafo.clear()

        while i < len(lineas):
            l = lineas[i]
            if not l.strip():
                cerrar_parrafo(); i += 1; continue
            if l.startswith("```"):
                cerrar_parrafo()
                lang = l[3:].strip() or "text"
                j = i + 1
                while not lineas[j].startswith("```"):
                    j += 1
                codigo = html.escape("\n".join(lineas[i + 1:j]), quote=False)
                out.append(("code", f'<div class="code-block"><pre tabindex="0"><code class="language-{lang}">{codigo}</code></pre></div>'))
                i = j + 1; continue
            if l.startswith("<figure"):
                cerrar_parrafo()
                j = i
                while lineas[j].strip() != "</figure>":
                    j += 1
                out.append(("figure", "\n".join(lineas[i:j + 1])))
                i = j + 1; continue
            m = re.match(r"^(#{2,3}) (.+)$", l)
            if m:
                cerrar_parrafo()
                n = len(m.group(1))
                out.append((f"h{n}", f"<h{n}>{self.en_linea(m.group(2).strip())}</h{n}>"))
                i += 1; continue
            if l.startswith("|"):
                cerrar_parrafo()
                j = i
                while j < len(lineas) and lineas[j].startswith("|"):
                    j += 1
                out.append(("table", self.tabla(lineas[i:j])))
                i = j; continue
            m = re.match(r"^(\d+\.|-) (.*)$", l)
            if m:
                cerrar_parrafo()
                ordenada = m.group(1) != "-"
                items = []
                while i < len(lineas):
                    m = re.match(r"^(\d+\.|-) (.*)$", lineas[i])
                    if m and (m.group(1) != "-") == ordenada:
                        items.append([m.group(2)]); i += 1
                    elif items and lineas[i].startswith("  ") and lineas[i].strip():
                        items[-1].append(lineas[i].strip()); i += 1
                    else:
                        break
                tag = "ol" if ordenada else "ul"
                lis = "\n".join(f"<li>{self.en_linea(' '.join(it))}</li>" for it in items)
                out.append((tag, f"<{tag}>\n{lis}\n</{tag}>"))
                continue
            parrafo.append(l.strip()); i += 1
        cerrar_parrafo()
        return out


# ---------------------------------------------------------------------------
# 3. Páginas
# ---------------------------------------------------------------------------

def fecha_larga(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} de {MESES[int(m) - 1]} de {y}"


def dimensiones_png(ruta):
    with open(ruta, "rb") as fh:
        cab = fh.read(24)
    return struct.unpack(">II", cab[16:24])


def cascaron():
    pagina = (SITE / "metodologia.html").read_text(encoding="utf-8")
    return pagina[:pagina.index('<main id="contenido">')], pagina[pagina.index("</main>"):]


def subir_un_nivel(s):
    """Rutas relativas de assets (css, img, favicon) para páginas dentro de /articulos/."""
    return re.sub(r'(href|src)="(?!https?:|mailto:|#|/|\.\./)([^"]+)"', r'\1="../\2"', s)


ORG = {"@type": "Organization", "name": "HCORPUS S.A.S.", "url": DOMINIO + "/",
       "logo": {"@type": "ImageObject", "url": DOMINIO + "/assets/img/logo-horizontal_transparente.png"}}


def encabezado(cab, titulo, descripcion, canonica, og_tipo, og_imagen, ld, extra_meta=""):
    h = cab
    h = re.sub(r"<title>.*?</title>", f"<title>{html.escape(titulo)}</title>", h)
    h = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{html.escape(descripcion)}">', h)
    h = re.sub(r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{html.escape(titulo)}">', h)
    h = re.sub(r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{html.escape(descripcion)}">', h)
    h = re.sub(r'<meta property="og:image" content=".*?">', f'<meta property="og:image" content="{og_imagen}">', h)
    h = h.replace('<meta property="og:type" content="website">',
                  f'<meta property="og:type" content="{og_tipo}">\n<meta property="og:url" content="{canonica}">{extra_meta}')
    h = re.sub(r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{canonica}">', h)
    h = h.replace('<link rel="stylesheet" href="css/styles.css">',
                  '<link rel="stylesheet" href="css/styles.css">\n\n<script type="application/ld+json">\n'
                  + json.dumps(ld, ensure_ascii=False, indent=2) + "\n</script>")
    h = h.replace(' aria-current="page"', "")
    h = h.replace('<a href="/articulos/">Artículos</a>', '<a href="/articulos/" aria-current="page">Artículos</a>', 2)
    return subir_un_nivel(h)


def tarjeta(a, con_meta=True):
    meta = (f"""
          <p class="article-card-meta">
            <span class="service-tags"><span>{a['etiqueta']}</span></span>
            <time datetime="{a['fecha']}">{fecha_larga(a['fecha'])}</time>
          </p>""" if con_meta else "")
    return f"""        <article class="service-card" data-reveal>{meta}
          <h3><a href="/articulos/{a['slug']}">{html.escape(a['title'])}</a></h3>
          <p>{html.escape(a['resumen'])}</p>
          <span class="service-link" aria-hidden="true">Leer artículo
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </span>
        </article>"""


def figura(a):
    img = a.get("imagen", "")
    if not img:
        return None
    png = SITE / img.lstrip("/").replace(".webp", ".png")
    w, h = dimensiones_png(png)
    return (f'<figure>\n<img src="{img}" alt="{html.escape(a.get("imagen_alt", ""))}" '
            f'width="{w}" height="{h}" loading="lazy" decoding="async">\n</figure>')


def construir_articulo(a, todos, conv, cab, pie):
    texto = re.sub(r"^# .*\n", "", a["cuerpo"].lstrip("\n"), count=1)
    partes = re.split(r"\n---\n", texto)
    cuerpo_md, cierre_md = ("\n---\n".join(partes[:-1]), partes[-1]) if len(partes) > 1 else (texto, "")

    bloques = conv.bloques(cuerpo_md)
    if bloques and bloques[0][0] == "p":
        bloques[0] = ("p", bloques[0][1].replace("<p>", '<p class="lead-answer">', 1))

    fig = figura(a)
    if fig and not any(t == "figure" for t, _ in bloques):
        destino = a.get("figura_despues_de")
        if destino:
            idx = next(k for k, (t, x) in enumerate(bloques) if t in ("h2", "h3") and destino in x)
            pos = next((k for k in range(idx + 1, len(bloques)) if bloques[k][0] in ("h2", "h3")), len(bloques))
        else:
            pos = next((k + 1 for k, (t, _) in enumerate(bloques) if t == "table"), None)
            if pos is None:
                h2s = [k for k, (t, _) in enumerate(bloques) if t == "h2"]
                pos = h2s[1] if len(h2s) > 1 else len(bloques)
        bloques.insert(pos, ("figure", fig))
    cuerpo_html = "\n\n".join(x for _, x in bloques)

    cierre_html = ""
    if cierre_md.strip():
        cb = conv.bloques(cierre_md)
        if cb and re.fullmatch(r"<p><strong>(.+)</strong></p>", cb[0][1]):
            cb[0] = ("h2", re.sub(r"<p><strong>(.+)</strong></p>", r"<h2>\1</h2>", cb[0][1]))
        cierre_html = ("\n    <!-- CIERRE: conecta el tema con el servicio -->\n"
                       '    <aside class="callout article-closing" aria-label="Servicio relacionado">\n'
                       + "\n".join("      " + x for _, x in cb) + "\n    </aside>")

    por_slug = {x["slug"]: x for x in todos}
    rel = [por_slug[s] for s in a.get("relacionados", []) if s in por_slug and s != a["slug"]]
    for x in todos:
        if len(rel) >= 3:
            break
        if x["slug"] != a["slug"] and x not in rel:
            rel.append(x)
    rel_html = ""
    if rel:
        rel_html = ('\n\n    <section class="article-related" aria-labelledby="relacionados">\n'
                    '      <h2 id="relacionados">Artículos relacionados</h2>\n'
                    '      <div class="services-grid">\n'
                    + "\n".join(tarjeta(x, con_meta=False) for x in rel[:3])
                    + "\n      </div>\n    </section>")

    palabras = len(re.sub(r"<[^>]+>", " ", cuerpo_html).split())
    minutos = max(1, round(palabras / 200))
    url = f"{DOMINIO}/articulos/{a['slug']}"
    og_img = DOMINIO + (a["imagen"].replace(".webp", ".png") if a.get("imagen") else "/assets/img/og-image.png")
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Article", "headline": a["title"], "description": a["meta_description"],
             "datePublished": a["fecha"], "dateModified": a.get("modificado", a["fecha"]),
             "inLanguage": "es-CO", "mainEntityOfPage": url, "image": og_img,
             "author": ORG, "publisher": ORG},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": DOMINIO + "/"},
                {"@type": "ListItem", "position": 2, "name": "Artículos", "item": DOMINIO + "/articulos/"},
                {"@type": "ListItem", "position": 3, "name": a["title"], "item": url}]},
        ],
    }
    h = encabezado(cab, a["meta_title"], a["meta_description"], url, "article", og_img, ld,
                   f'\n<meta property="article:published_time" content="{a["fecha"]}">')
    cuerpo = f"""<main id="contenido">
<article>

  <!-- ENCABEZADO DEL ARTÍCULO -->
  <header class="hero-dark">
    <div class="container">
      <nav class="breadcrumb" aria-label="Migas de pan">
        <a href="/">Inicio</a>
        <span aria-hidden="true">/</span>
        <a href="/articulos/">Artículos</a>
        <span aria-hidden="true">/</span>
        <span class="current">{html.escape(a['title'])}</span>
      </nav>
      <p class="eyebrow">{a['etiqueta']}</p>
      <h1>{html.escape(a['title'])}</h1>
      <p class="article-meta">
        <span>Publicado el <time datetime="{a['fecha']}">{fecha_larga(a['fecha'])}</time></span>
        <span>{minutos} min de lectura</span>
      </p>
    </div>
  </header>

  <!-- CUERPO (generado desde {a['archivo']}) -->
  <div class="container article-body">
    <div class="prose">
{cuerpo_html}
    </div>
{cierre_html}{rel_html}
  </div>

</article>
</main>
"""
    destino = SITE / "articulos" / f"{a['slug']}.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(h + cuerpo + pie.replace("</body>", '<script src="../js/highlight-r.js"></script>\n</body>'),
                       encoding="utf-8")
    print(f"  {destino.relative_to(REPO)}  ({palabras} palabras, {minutos} min)")


def construir_indice(arts, cab, pie):
    url = DOMINIO + "/articulos/"
    titulo = "Artículos de bioestadística y análisis de datos | hCorpus"
    desc = ("Artículos prácticos de bioestadística, epidemiología y análisis de datos en R: la Tabla 1, "
            "datos faltantes, supervivencia y tamaño de muestra, con código.")
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Artículos",
          "description": desc, "url": url, "publisher": ORG,
          "hasPart": [{"@type": "Article", "headline": a["title"], "url": f"{DOMINIO}/articulos/{a['slug']}",
                       "datePublished": a["fecha"]} for a in arts]}
    h = encabezado(cab, titulo, desc, url, "website", DOMINIO + "/assets/img/og-image.png", ld)
    tarjetas = "\n".join(tarjeta(a) for a in arts)
    cuerpo = f"""<main id="contenido">

  <!-- HERO -->
  <section class="hero-dark">
    <div class="container">
      <nav class="breadcrumb" aria-label="Migas de pan">
        <a href="/">Inicio</a>
        <span aria-hidden="true">/</span>
        <span class="current">Artículos</span>
      </nav>
      <p class="eyebrow">Artículos</p>
      <h1>Bioestadística y análisis de datos, en la práctica</h1>
      <p class="lede">Las preguntas que más nos hacen los grupos de investigación, respondidas con ejemplos y con el código en R para hacerlo usted mismo.</p>
    </div>
  </section>

  <!-- LISTADO (orden cronológico inverso) -->
  <section class="services">
    <div class="container">
      <div class="services-grid">
{tarjetas}
      </div>
    </div>
  </section>

  <!-- CTA -->
  <div class="container cta-wrap">
    <div class="cta-banner" data-reveal>
      <h2>¿Prefiere que lo hagamos nosotros?</h2>
      <p>Miramos su base o su protocolo durante una hora y le contamos por escrito qué encontramos. De ahí sale la cotización.</p>
      <a class="btn btn-on-dark" href="/#contacto">Escríbanos ahora</a>
    </div>
  </div>

</main>
"""
    (SITE / "articulos" / "index.html").write_text(h + cuerpo + pie, encoding="utf-8")
    print("  site/articulos/index.html")


def actualizar_sitemap(arts):
    sm = SITE / "sitemap.xml"
    s = sm.read_text(encoding="utf-8")
    s = re.sub(r"  <url>\n    <loc>" + re.escape(DOMINIO) + r"/articulos/.*?</url>\n", "", s, flags=re.S)
    nuevas = (f"  <url>\n    <loc>{DOMINIO}/articulos/</loc>\n    <changefreq>weekly</changefreq>\n"
              "    <priority>0.8</priority>\n  </url>\n")
    for a in arts:
        nuevas += (f"  <url>\n    <loc>{DOMINIO}/articulos/{a['slug']}</loc>\n"
                   f"    <lastmod>{a.get('modificado', a['fecha'])}</lastmod>\n"
                   "    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n")
    s = s.replace("</urlset>", nuevas + "</urlset>")
    sm.write_text(s, encoding="utf-8")
    print(f"  site/sitemap.xml ({len(arts)} artículos)")


def main():
    normalizar_sitio()

    arts, errores = [], []
    for f in sorted(REPO.glob("articulo_*.md")):
        meta, cuerpo = leer_front_matter(f.read_text(encoding="utf-8"))
        cuerpo = re.sub(r"\n?<!--.*?-->\n?", "\n", cuerpo, flags=re.S)  # los comentarios no se publican
        meta.update(cuerpo=cuerpo, archivo=f.name, orden=int(re.search(r"_(\d+)_", f.name).group(1)))
        meta.setdefault("resumen", meta["meta_description"])
        if len(meta["meta_title"]) > 60:
            errores.append(f"{f.name}: meta_title tiene {len(meta['meta_title'])} caracteres (máximo 60)")
        if not 140 <= len(meta["meta_description"]) <= 160:
            errores.append(f"{f.name}: meta_description tiene {len(meta['meta_description'])} caracteres (debe estar entre 140 y 160)")
        if meta.get("imagen") and not (SITE / meta["imagen"].lstrip("/")).exists():
            errores.append(f"{f.name}: no existe la imagen {meta['imagen']}")
        arts.append(meta)
    if errores:
        sys.exit("No se generó nada:\n  " + "\n  ".join(errores))

    arts.sort(key=lambda a: (a["fecha"], a["orden"]), reverse=True)
    conv = Conversor({a["slug"] for a in arts})
    cab, pie = cascaron()
    print(f"Artículos ({len(arts)}):")
    for a in arts:
        construir_articulo(a, arts, conv, cab, pie)
    construir_indice(arts, cab, pie)
    actualizar_sitemap(arts)


if __name__ == "__main__":
    main()
