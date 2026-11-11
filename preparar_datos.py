# ====================================================================
# Observatorio Regional de Nariño — preparar la carpeta data/
# --------------------------------------------------------------------
# Pega TODO este archivo en una celda de Google Colab y ejecútala.
# Descarga las bases de la carpeta pública de Drive, deja solo los
# 64 municipios de Nariño y genera:
#   data/municipios.csv     cifras por municipio
#   data/departamento.csv   serie anual del valor agregado de Nariño
#   data/narino.geojson     límites municipales para los mapas
#   data/meta.json          años y unidades usados
#   data/diagnostico.txt    qué columnas se tomaron de cada base
# Al final descarga data_observatorio.zip: descomprímelo en la raíz
# del repositorio (queda la carpeta data/) y haz push.
# ====================================================================
import subprocess, sys, os, re, json, csv, zipfile, unicodedata, urllib.request, urllib.parse
from collections import defaultdict

def _pip(*p):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *p], check=False)
try:
    import openpyxl
except ImportError:
    _pip("openpyxl"); import openpyxl

# ----------------------- CONFIGURACIÓN -----------------------
# clave: (id del archivo en Drive, nombre). Quita líneas para ir más rápido.
ARCHIVOS = {
    "ipm":        ("1GHmTH2oUAeHRaJ7pkvzbQvqcWAlTANig", "IPM_MUN_2018.xlsx"),
    "pib":        ("161oSE77fQOYg-7DI8dz5DJ35CreMxdyF", "BD_PIB_municipal_2011_2024p.xlsx"),
    "poblacion":  ("1RWwXMuXNEqAi3zk6P5YXdQFX1GIyHoyD", "BD_DEMOGRAFIA_MUNICIPAL_2011_2031.xlsx"),
    "nbi":        ("1l8MV0aXm1W02YfNGou14gZppIfpcupMB", "BD_NBI_MUN_2018.xlsx"),
    "laboral":    ("1wZVJwOq3l-ahsjDHAugsORcEcMYL2sQb", "MERCADO_LABORAL_MUN_2019-2025.xlsx"),
    "desempeno":  ("1AsEXXHWCsphaejzahdcFsIlk0ndWWv1p", "DESEMPENO_INSTITUCIONAL_MUNICIPAL.xlsx"),
}
# Qué variable buscar en cada base: (incluir, excluir) como expresiones regulares
# sobre el nombre de la columna/indicador sin tildes y en minúsculas.
REGLAS = {
    "ipm":            ("ipm",       r"ipm|pobreza multidimensional|multidimensional", r"cabecera|rural|centros|resto|urban"),
    "valor_agregado": ("pib",       r"valor agregado|pib|producto interno",            r"peso|particip|primari|secundari|terciari|per capita|percapita|crecim|variaci"),
    "poblacion":      ("poblacion", r"poblacion|total|habitantes|personas",            r"cabecera|rural|centros|resto|urban|hombre|mujer|porcen|tasa|indice|densidad"),
    "inversion":      (None,        r"inversion",                                      r"porcen|particip|per capita|percapita|indice|puntaje"),
    "NBI (%)":        ("nbi",       r"nbi|necesidades basicas",                        r"cabecera|rural|centros|resto|urban|miseria|componente|vivienda|servicios|hacinamiento|inasistencia|dependencia"),
    "Tasa de desempleo (%)": ("laboral", r"desempleo|desocupacion",                    r"hombre|mujer|joven|brecha"),
    "Desempeño municipal (puntaje)": ("desempeno", r"mdm|desempeno|puntaje|indice",    r"gestion|resultados|componente|ranking|puesto|grupo|categoria"),
}
# Si la detección automática falla, fuerza aquí el nombre exacto de la variable
# tal como aparece en data/diagnostico.txt, p. ej. {"ipm": "IPM Total"}.
FORZAR = {}
GEO_FUENTES = [
    "https://geoportal.superservicios.gov.co/server/rest/services/CARTO_BASE/Limites_Entidades_Territoriales/FeatureServer/1/query?"
    + urllib.parse.urlencode({"where": "DPTO_CCDGO='52'", "outFields": "DPTO_CCDGO,MPIO_CCDGO,MPIO_CNMBR", "outSR": "4326", "f": "geojson"}),
    "https://raw.githubusercontent.com/santiblanko/colombia.geojson/master/mpio.json",
]
CARPETA_BASES, SALIDA = "bases", "data"
# -------------------------------------------------------------

MUNICIPIOS = [("52001","Pasto"),("52019","Albán"),("52022","Aldana"),("52036","Ancuyá"),("52051","Arboleda"),("52079","Barbacoas"),("52083","Belén"),("52110","Buesaco"),("52203","Colón"),("52207","Consacá"),("52210","Contadero"),("52215","Córdoba"),("52224","Cuaspud"),("52227","Cumbal"),("52233","Cumbitara"),("52240","Chachagüí"),("52250","El Charco"),("52254","El Peñol"),("52256","El Rosario"),("52258","El Tablón de Gómez"),("52260","El Tambo"),("52287","Funes"),("52317","Guachucal"),("52320","Guaitarilla"),("52323","Gualmatán"),("52352","Iles"),("52354","Imués"),("52356","Ipiales"),("52378","La Cruz"),("52381","La Florida"),("52385","La Llanada"),("52390","La Tola"),("52399","La Unión"),("52405","Leiva"),("52411","Linares"),("52418","Los Andes"),("52427","Magüí"),("52435","Mallama"),("52473","Mosquera"),("52480","Nariño"),("52490","Olaya Herrera"),("52506","Ospina"),("52520","Francisco Pizarro"),("52540","Policarpa"),("52560","Potosí"),("52565","Providencia"),("52573","Puerres"),("52585","Pupiales"),("52612","Ricaurte"),("52621","Roberto Payán"),("52678","Samaniego"),("52683","Sandoná"),("52685","San Bernardo"),("52687","San Lorenzo"),("52693","San Pablo"),("52694","San Pedro de Cartago"),("52696","Santa Bárbara"),("52699","Santacruz"),("52720","Sapuyes"),("52786","Taminango"),("52788","Tangua"),("52835","San Andrés de Tumaco"),("52838","Túquerres"),("52885","Yacuanquer")]
ALIAS = {"san juan de pasto":"52001","san jose de alban":"52019","berruecos":"52051","genova":"52203","carlosama":"52224","el tablon":"52258","sotomayor":"52418","magui payan":"52427","piedrancha":"52435","bocas de satinga":"52490","salahonda":"52520","cartago":"52694","iscuande":"52696","santa cruz":"52699","guachaves":"52699","tumaco":"52835"}

def norm(s):
    s = unicodedata.normalize("NFD", str(s if s is not None else ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9% ]+", " ", s)).strip()

CODES = {c for c, _ in MUNICIPIOS}
MPIO3 = {c[2:] for c in CODES}
NOMBRES = {norm(n): c for c, n in MUNICIPIOS}; NOMBRES.update(ALIAS)
LOG = []
def log(*a):
    t = " ".join(str(x) for x in a); print(t); LOG.append(t)

def como_codigo(v):
    """52001, '52001', 52001.0, '52.001' -> '52001' si es un municipio de Nariño."""
    if v is None or isinstance(v, bool): return None
    if isinstance(v, float):
        if v != int(v): return None
        v = int(v)
    s = re.sub(r"\D", "", str(v)) if not isinstance(v, int) else str(v)
    return s if s in CODES else None

def num(v):
    if v is None or isinstance(v, bool): return None
    if isinstance(v, (int, float)): return float(v)
    s = re.sub(r"[\s$%]", "", str(v))
    if not s or not re.search(r"\d", s): return None
    d, c = s.count("."), s.count(",")
    if d and c: s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif c: s = s.replace(",", "") if c > 1 else s.replace(",", ".")
    elif d > 1: s = s.replace(".", "")
    try: return float(s)
    except ValueError: return None

def anio_de(v):
    if isinstance(v, float) and v == int(v): v = int(v)
    m = re.fullmatch(r"\s*(20[0-3]\d)\s*(p|pr|pre)?\s*", str(v), re.I)
    return int(m.group(1)) if m else None

# ---------------- lectura en flujo de un Excel pesado ----------------
def leer_hoja(ws, max_vacias=3000):
    """Devuelve (encabezado, filas de Nariño). Solo guarda filas que mencionan
    un código 52xxx o el departamento de Nariño, para no agotar la memoria."""
    cab, filas, vacias, primeras = None, [], 0, []
    for fila in ws.iter_rows(values_only=True):
        if fila is None or all(c is None or str(c).strip() == "" for c in fila):
            vacias += 1
            if vacias > max_vacias: break
            continue
        vacias = 0
        if cab is None:
            primeras.append(fila)
            textos = [c for c in fila if isinstance(c, str) and c.strip()]
            llenas = [c for c in fila if c is not None and str(c).strip() != ""]
            if len(llenas) >= 3 and len(textos) >= max(2, 0.6 * len(llenas)):
                cab = [str(c).strip() if c is not None else "" for c in fila]
            elif len(primeras) > 40: break
            continue
        es_narino = False
        for c in fila:
            if c is None: continue
            if como_codigo(c) or (isinstance(c, str) and norm(c) == "narino"): es_narino = True; break
        if es_narino: filas.append(fila)
    return cab, filas

def analizar_hoja(archivo, hoja, cab, filas):
    """Convierte la hoja en registros (codigo|'DEPTO', anio, variable, valor)."""
    n = len(cab); col = lambda j: [f[j] if j < len(f) else None for f in filas]
    cabn = [norm(h) for h in cab]
    # columna de código municipal
    cuenta = [sum(1 for v in col(j) if como_codigo(v)) for j in range(n)]
    jc = max(range(n), key=lambda j: cuenta[j]) if n else None
    codigos = None
    if jc is not None and cuenta[jc] >= 5:
        codigos = [como_codigo(v) for v in col(jc)]
    else:
        # código de 3 dígitos + departamento, o nombre del municipio
        jm = [j for j in range(n) if re.search(r"cod.*mun|mpio|municipio", cabn[j]) and sum(1 for v in col(j) if re.sub(r"\D", "", str(v)).zfill(3) in MPIO3 and len(re.sub(r"\D", "", str(v))) <= 3 and re.sub(r"\D", "", str(v))) >= 5]
        if jm:
            codigos = ["52" + re.sub(r"\D", "", str(v)).zfill(3) if v is not None and re.sub(r"\D", "", str(v)) and "52" + re.sub(r"\D", "", str(v)).zfill(3) in CODES else None for v in col(jm[0])]; jc = jm[0]
        else:
            cn = [0 if re.search(r"depart|dpto|dpnom", cabn[j]) else len({norm(v) for v in col(j) if isinstance(v, str) and norm(v) in NOMBRES}) for j in range(n)]
            jn = max(range(n), key=lambda j: cn[j]) if n else None
            if jn is None or cn[jn] < 5: return [], "sin columna de municipio"
            codigos = [NOMBRES.get(norm(v)) if isinstance(v, str) else None for v in col(jn)]; jc = jn
    # filas del total departamental (sin código municipal)
    jdep = [j for j in range(n) if sum(1 for v in col(j) if isinstance(v, str) and norm(v) == "narino") >= 1]
    # columna de año, o años como encabezados
    ja = next((j for j in range(n) if re.fullmatch(r"ano|anio|year|vigencia|periodo|ano de corte|a o", cabn[j])), None)
    if ja is None:
        cand = [j for j in range(n) if j != jc and sum(1 for v in col(j) if anio_de(v)) >= 0.9 * max(1, len(filas))]
        ja = cand[0] if cand else None
    anios_cab = {j: anio_de(cab[j]) for j in range(n) if anio_de(cab[j])}
    m = re.search(r"(20[0-3]\d)", str(hoja)) or re.search(r"(20[0-3]\d)", archivo)
    anio_def = int(m.group(1)) if m and not re.search(r"20[0-3]\d\D+20[0-3]\d", archivo if not re.search(r"20[0-3]\d", str(hoja)) else "") else None
    # columnas de texto y numéricas
    def frac_num(j):
        vals = [v for v in col(j) if v is not None and str(v).strip() != ""]
        return (sum(1 for v in vals if num(v) is not None) / len(vals)) if vals else 0
    es_id = lambda j: j == jc or j == ja or re.search(r"\bcod|codigo|divipola|dane|^id$|depart|dpto|municip|mpio|subregion|region|latitud|longitud|fuente|unidad", cabn[j])
    numericas = [j for j in range(n) if not es_id(j) and frac_num(j) >= 0.6]
    textos = [j for j in range(n) if not es_id(j) and j not in numericas and j not in jdep and any(isinstance(v, str) and v.strip() for v in col(j))]
    # formato largo: columna "indicador/variable" + columna "valor"
    jvar = next((j for j in textos if re.search(r"indicador|variable|concepto|actividad|sector|rama|cultivo|categoria|componente|dimension", cabn[j])), None)
    jval = next((j for j in numericas if re.fullmatch(r"valor|dato|cifra|resultado|total|cantidad|valor del indicador", cabn[j])), None)
    largo = jvar is not None and jval is not None and not anios_cab
    # dimensiones (sexo, área, edad…): quedarse con "total" si existe
    usar = [True] * len(filas); notas = []
    for j in textos:
        if j == jvar: continue
        vals = {norm(v) for v in col(j) if isinstance(v, str)}
        if 1 < len(vals) <= 40:
            tot = [v for v in vals if v.startswith("total") or v in ("ambos sexos", "todos", "todas", "nacional")]
            if tot:
                for i, v in enumerate(col(j)):
                    if not (isinstance(v, str) and norm(v) in tot): usar[i] = False
                notas.append(f"filtro {cab[j]}=total")
    reg = []
    for i, f in enumerate(filas):
        if not usar[i]: continue
        cod = codigos[i]
        if cod is None:
            if not any(j < len(f) and isinstance(f[j], str) and norm(f[j]) == "narino" for j in jdep): continue
            # fila departamental solo si no trae nombre de otro municipio
            cod = "DEPTO"
        a = anio_de(f[ja]) if ja is not None and ja < len(f) else anio_def
        if largo:
            v = num(f[jval]) if jval < len(f) else None
            if v is not None and jvar < len(f) and f[jvar]: reg.append((cod, a, str(f[jvar]).strip(), v))
        elif anios_cab:
            base = str(f[jvar]).strip() if jvar is not None and jvar < len(f) and f[jvar] else str(hoja)
            for j, an in anios_cab.items():
                v = num(f[j]) if j < len(f) else None
                if v is not None: reg.append((cod, an, base, v))
        else:
            for j in numericas:
                v = num(f[j]) if j < len(f) else None
                if v is not None: reg.append((cod, a, cab[j], v))
    forma = "largo" if largo else ("años en columnas" if anios_cab else "ancho")
    return reg, f"formato {forma}; código en «{cab[jc]}»; año: {('«'+cab[ja]+'»') if ja is not None else ('encabezados' if anios_cab else anio_def)}; {'; '.join(notas)}"

def leer_archivo(clave, ruta):
    nombre = os.path.basename(ruta); log(f"\n=== {clave}: {nombre} ===")
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    todos = []
    for ws in wb.worksheets:
        try:
            if hasattr(ws, "reset_dimensions"): ws.reset_dimensions()
            cab, filas = leer_hoja(ws)
        except Exception as e:
            log(f"  hoja «{ws.title}»: error al leer ({e})"); continue
        if not cab or not filas: log(f"  hoja «{ws.title}»: sin filas de Nariño"); continue
        reg, nota = analizar_hoja(nombre, ws.title, cab, filas)
        log(f"  hoja «{ws.title}»: {len(filas)} filas de Nariño → {len(reg)} datos. {nota}")
        log("    columnas: " + " | ".join(h for h in cab if h)[:600])
        vs = defaultdict(set)
        for c, a, v, _ in reg: vs[v].add(a)
        for v, an in list(vs.items())[:60]:
            an = sorted(x for x in an if x); log(f"    variable «{v}» años {an[0]}–{an[-1]}" if an else f"    variable «{v}»")
        todos += reg
    wb.close(); return todos

def elegir(registros, clave_salida, sumar=False):
    """Escoge la variable y el año más reciente con buena cobertura."""
    origen, inc, exc = REGLAS[clave_salida]
    fuentes = [origen] if origen else list(registros)
    mejor = None
    for src in fuentes:
        reg = registros.get(src) or []
        variables = sorted({r[2] for r in reg})
        if clave_salida in FORZAR: cand = [v for v in variables if v == FORZAR[clave_salida]]
        else:
            cand = [v for v in variables if re.search(inc, norm(v)) and not re.search(exc, norm(v))]
            if not cand and origen and len(variables) == 1: cand = variables
            cand.sort(key=lambda v: (0 if "total" in norm(v) else 1, len(v)))
        for v in cand:
            por_anio = defaultdict(lambda: defaultdict(list))
            for c, a, var, val in reg:
                if var == v: por_anio[a][c].append(val)
            buenos = [a for a, d in por_anio.items() if sum(1 for c in d if c in CODES) >= 40]
            if not buenos: continue
            cur = (src, v, por_anio, buenos); mejor = mejor or cur
            break
        if mejor: break
    return mejor

def serie(por_anio, anio, sumar):
    out = {}
    for c, vals in por_anio[anio].items():
        out[c] = sum(vals) if sumar else vals[0]
    return out

def descargar_bases():
    try: import gdown
    except ImportError: _pip("gdown"); import gdown
    os.makedirs(CARPETA_BASES, exist_ok=True); rutas = {}
    for k, (fid, nombre) in ARCHIVOS.items():
        ruta = os.path.join(CARPETA_BASES, nombre)
        if not os.path.exists(ruta) or os.path.getsize(ruta) < 10000:
            print("Descargando", nombre, "…")
            try: gdown.download(id=fid, output=ruta, quiet=True)
            except Exception as e: print("  no se pudo descargar:", e)
        if os.path.exists(ruta) and os.path.getsize(ruta) > 10000: rutas[k] = ruta
        else: log(f"FALTA {nombre}: revisa que el archivo sea público («Cualquier persona con el enlace»).")
    return rutas

def geometria():
    def cod(p):
        p = {k.lower(): v for k, v in p.items()}
        for k in ("mpio_cdpmp", "mpio_ccnct", "mpios", "cod_dane", "codigo", "divipola"):
            s = re.sub(r"\D", "", str(p.get(k, "")));
            if s in CODES: return s
        d, m = p.get("dpto_ccdgo", p.get("dpto")), p.get("mpio_ccdgo", p.get("mpio"))
        if m is not None:
            m = re.sub(r"\D", "", str(m))
            if m in CODES: return m
            if d is not None and str(d).zfill(2) == "52" and "52" + m.zfill(3) in CODES: return "52" + m.zfill(3)
        return None
    def redondear(x): return [redondear(y) for y in x] if isinstance(x, list) else round(x, 4)
    for url in GEO_FUENTES:
        try:
            print("Descargando límites municipales…")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            g = json.loads(urllib.request.urlopen(req, timeout=180).read().decode("utf-8", "ignore"))
            feats = []
            for f in g.get("features", []):
                c = cod(f.get("properties") or {})
                if c and f.get("geometry"):
                    f["geometry"]["coordinates"] = redondear(f["geometry"]["coordinates"])
                    feats.append({"type": "Feature", "properties": {"MPIO_CDPMP": c, "MPIO_CNMBR": dict(MUNICIPIOS)[c]}, "geometry": f["geometry"]})
            if len({f["properties"]["MPIO_CDPMP"] for f in feats}) >= 55:
                json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(SALIDA, "narino.geojson"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
                log(f"\nGeometría: {len(feats)} polígonos de {url.split('/')[2]}"); return True
            log(f"Geometría: {url.split('/')[2]} solo trae {len(feats)} municipios de Nariño; se prueba otra fuente.")
        except Exception as e:
            log(f"Geometría: falló {url.split('/')[2]} ({e})")
    log("Geometría: no se pudo generar data/narino.geojson; súbelo a mano (MGN del DANE)."); return False

def procesar(rutas):
    os.makedirs(SALIDA, exist_ok=True)
    registros = {k: leer_archivo(k, r) for k, r in rutas.items()}
    columnas, meta = {}, {"anios": {}, "variables": {}, "unidades": {}}
    log("\n=== Variables elegidas ===")
    pib = elegir(registros, "valor_agregado")
    for clave in REGLAS:
        sel = pib if clave == "valor_agregado" else elegir(registros, clave)
        if not sel: log(f"  {clave}: NO encontrada"); continue
        src, var, por_anio, buenos = sel
        anio = max(a for a in buenos if a is not None) if any(a is not None for a in buenos) else None
        if clave == "poblacion":   # mismo año que el valor agregado si existe; nunca una proyección futura
            ref = meta["anios"].get("valor_agregado")
            anio = ref if ref in buenos else max([a for a in buenos if a and a <= 2025] or [anio])
        columnas[clave] = serie(por_anio, anio, sumar=(clave == "poblacion"))
        meta["anios"][clave] = anio; meta["variables"][clave] = f"{var} ({ARCHIVOS[src][1]})"
        log(f"  {clave}: «{var}» de {ARCHIVOS[src][1]}, año {anio}, {sum(1 for c in columnas[clave] if c in CODES)} municipios")
        if clave == "valor_agregado":
            with open(os.path.join(SALIDA, "departamento.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["anio", "valor_agregado"])
                for a in sorted(x for x in por_anio if x):
                    d = por_anio[a]; mun = [d[c][0] for c in d if c in CODES]
                    if len(mun) >= 60: w.writerow([a, round(sum(mun), 3)])
    meta["anioBase"] = meta["anios"].get("valor_agregado") or 2024
    cols = [c for c in columnas]
    orden = [c for c in ("poblacion", "ipm", "valor_agregado", "inversion") if c in cols] + [c for c in cols if c not in ("poblacion", "ipm", "valor_agregado", "inversion")]
    with open(os.path.join(SALIDA, "municipios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["codigo", "municipio"] + orden)
        for c, n in MUNICIPIOS:
            w.writerow([c, n] + [("" if columnas[k].get(c) is None else (int(columnas[k][c]) if float(columnas[k][c]).is_integer() else round(columnas[k][c], 4))) for k in orden])
    json.dump(meta, open(os.path.join(SALIDA, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return columnas

def main():
    local = sys.argv[sys.argv.index("--local") + 1] if "--local" in sys.argv else None
    if local:
        rutas = {k: os.path.join(local, n) for k, (_, n) in ARCHIVOS.items() if os.path.exists(os.path.join(local, n))}
    else:
        rutas = descargar_bases()
    cols = procesar(rutas)
    if "--sin-geo" not in sys.argv: geometria()
    faltan = [k for k in ("ipm", "valor_agregado", "inversion") if k not in cols]
    if faltan: log("\nATENCIÓN, sin datos para: " + ", ".join(faltan) + ". Revisa data/diagnostico.txt y usa FORZAR si la variable existe con otro nombre.")
    open(os.path.join(SALIDA, "diagnostico.txt"), "w", encoding="utf-8").write("\n".join(LOG))
    with zipfile.ZipFile("data_observatorio.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(os.listdir(SALIDA)): z.write(os.path.join(SALIDA, n), "data/" + n)
    print("\nListo: data_observatorio.zip")
    try:
        from google.colab import files; files.download("data_observatorio.zip")
    except Exception: pass

main()
