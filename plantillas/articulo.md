---
slug: palabras-clave-con-guiones
title: "Título H1: lo que la persona escribiría en Google"
meta_title: "Título para Google, máximo 60 caracteres | hCorpus"
meta_description: "Entre 140 y 160 caracteres. Responde la pregunta del buscador y dice qué va a encontrar en el artículo: el porqué, el cómo y el código."
fecha: AAAA-MM-DD
etiqueta: Bioestadística
imagen: /assets/img/articulos/nombre.webp
imagen_alt: "Qué muestra la figura, descrito para quien no la puede ver"
figura_despues_de: Texto de un subtítulo (opcional; por defecto va después de la primera tabla)
relacionados:
  - slug-de-otro-articulo
  - slug-de-otro-articulo
  - slug-de-otro-articulo
---

# Título H1 (se toma del campo title; esta línea se ignora)

Respuesta directa a la pregunta, en tres a cinco líneas. Quien llega de Google
tiene una pregunta: si no la ve respondida aquí, se va. Este párrafo sale
destacado.

## Un subtítulo cada 200 a 300 palabras

Texto normal. **Negrilla**, *cursiva*, `código en línea` y
[enlaces a otros artículos](/articulos/slug-de-otro-articulo.html). Si el enlace
apunta a un artículo que no existe, la herramienta se detiene y lo avisa.

```r
# Código R: se resalta solo y tiene botón Copiar
datos |> summary()
```

| Columna | Otra |
|---|---|
| La primera columna | sale como encabezado de fila |

1. Listas numeradas
2. y con viñetas (empiece la línea con "- ")

---

**Pregunta de cierre que conecta el tema con el servicio**

Dos o tres líneas, sin agresividad. La revisión inicial no tiene costo.

[Texto del enlace a la página comercial](/analisis-datos-articulo-cientifico.html)

<!--
CÓMO PUBLICAR
1. Copie este archivo a la raíz del repo como articulo_NN_tema.md (NN = número siguiente).
   Los .md no se suben a GitHub; el HTML generado sí.
2. Figura: deje el PNG y la versión WebP en site/assets/img/articulos/ con el mismo nombre
   (cwebp -q 85 nombre.png -o nombre.webp). La página usa el WebP; LinkedIn, el PNG.
3. Desde la raíz del repo:  python3 herramientas/construir_articulos.py
   Genera el artículo, el listado, los relacionados y el sitemap. No hace falta tocar CSS.
4. Revise, haga commit y push. Cloudflare publica solo.
-->
