# Observatorio Regional de Nariño

Plataforma académica de análisis económico para los 64 municipios de Nariño:
pobreza, valor agregado (PIB municipal) e inversión municipal.

**Autores:** Camila Guerrero · Geovanny Betancourt

## Contenido de la página

| Pestaña | Qué muestra |
|---|---|
| Presentación | Quiénes somos, qué hay en el sitio y fuentes |
| Indicadores | Resumen estadístico, ranking y tabla de los 64 municipios |
| Mapas | Mapas coropléticos: valor agregado municipal, participación en el valor agregado departamental, inversión municipal y pobreza |
| Econometría | Correlaciones de Pearson, dispersión y modelo OLS calculados en el navegador |
| Proyección | Escenarios ilustrativos a 2030 para el departamento o un municipio |
| Asistente | Chat que recupera fragmentos de los datos y responde por vía rápida y vía precisa, con fuentes |

## Estructura del repositorio

```
index.html              ← toda la página (HTML + estilos + lógica)
netlify.toml
README.md
data/
  municipios.csv        ← cifras de los 64 municipios (plantilla vacía hasta correr el script)
  narino.geojson        ← límites municipales (lo genera el script)
  departamento.csv      ← serie anual del valor agregado departamental (lo genera el script)
  meta.json, diagnostico.txt
herramientas/
  preparar_datos.py     ← se ejecuta en Google Colab; no hace parte del sitio
```

Ya no se usa la carpeta `assets/`; puedes borrarla del repositorio.

## 1. Generar la carpeta `data/` (una sola vez)

Las bases del Observatorio pesan más de 100 MB cada una, así que no van en el repositorio.
El script `herramientas/preparar_datos.py` las descarga de la carpeta pública de Drive,
deja solo los 64 municipios de Nariño y arma todo lo que la página necesita.

1. Abre [Google Colab](https://colab.research.google.com) y crea un cuaderno nuevo.
2. Pega el contenido completo de `herramientas/preparar_datos.py` en una celda y ejecútala.
3. Al terminar se descarga `data_observatorio.zip`. Descomprímelo en la raíz del repositorio:
   queda la carpeta `data/` con estos archivos.

| Archivo | Contenido |
|---|---|
| `municipios.csv` | Población, pobreza (IPM), valor agregado y demás indicadores por municipio |
| `departamento.csv` | Serie anual del valor agregado de Nariño (suma de municipios) |
| `narino.geojson` | Límites municipales para los mapas |
| `meta.json` | Año usado en cada indicador |
| `diagnostico.txt` | Qué hoja, columna y año se tomó de cada base |

Revisa `diagnostico.txt` antes de publicar. Si el script tomó una variable equivocada,
copia el nombre correcto desde ese archivo al diccionario `FORZAR` del script y vuelve a ejecutarlo.

### Llenar o corregir a mano

`data/municipios.csv` también se puede editar en Excel:

| Columna | Unidad esperada |
|---|---|
| `codigo` | DIVIPOLA de 5 dígitos (52001 = Pasto) |
| `municipio` | Nombre |
| `poblacion` | Habitantes |
| `ipm` | Pobreza multidimensional, en % |
| `valor_agregado` | Miles de millones de pesos |
| `inversion` | Millones de pesos |

- Se acepta separador `,` o `;` y decimales con punto o coma.
- Una celda vacía se muestra como "s.d." y el municipio sale sin color en el mapa.
- Cualquier columna numérica adicional aparece sola como un indicador más en tablas, mapas, correlaciones y asistente.
- La participación en el valor agregado departamental y los valores per cápita se calculan en la página.
- Si usas otras unidades, cambia `CONFIG.unidades` al inicio del `<script>` de `index.html`.

**Inversión municipal:** en la carpeta de Drive no hay una base con ese nombre. El script la busca
en las bases que descarga; si no aparece, agrega la columna `inversion` a mano y la página activa
sola el mapa y los indicadores de inversión.

## Despliegue en GitHub + Netlify

1. Sube `index.html`, `netlify.toml`, `README.md` y las carpetas `data/` y `herramientas/` a la raíz del repositorio.
2. En Netlify: *Add new site → Import an existing project* y elige el repositorio.
3. Build command: vacío. Publish directory: `.`
4. Deploy. Cada `git push` vuelve a publicar.

Para probar en tu computador, abre una terminal en la carpeta y ejecuta
`python -m http.server`; luego entra a `http://localhost:8000`. Abrir `index.html`
con doble clic no carga los datos.

## Sobre el asistente

Sigue el esquema del cuaderno de Colab del curso (trocear, recuperar los k fragmentos más
cercanos, responder por vía rápida y vía precisa, citar fuentes), pero sin modelo de lenguaje:
la recuperación es TF-IDF y corre en el navegador, así funciona en un sitio estático sin
servidor ni clave de API. Solo responde con lo que está en `data/municipios.csv` y en los
textos de la página.

## Fuentes

DANE · Consejo Privado de Competitividad – Universidad del Rosario
