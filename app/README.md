# Capa de aplicación (`app/`)

Interfaz de escritorio en PySide6 para el monolito de certificación.

**Regla del proyecto:** esta carpeta NO toca `models/` ni `logic/`. Solo los
lee: importa `models.file_names.FileName` como contrato de nombres de archivo y
`models/reports/*` para verificar que las etiquetas de columnas sigan alineadas.

---

## Instalación

Descomprimir el ZIP de forma que `app/` quede junto a `logic/` y `models/`:

```
app_python/
├── app/          <-- esta carpeta
├── logic/        (intacta)
├── models/       (intacta)
├── .env
└── requirements.txt
```

Instalar dependencias (un solo archivo, en la raíz):

```bash
pip install -r requirements.txt
```

Sin internet (red corporativa), desde una máquina con salida:

```bash
pip download -r requirements.txt -d wheelhouse
# copiar la carpeta wheelhouse a la máquina destino y ahí:
pip install --no-index --find-links=wheelhouse -r requirements.txt
```

Crear el `.env` en la raíz (junto a `requirements.txt`):

```
DATA_PATH=C:\ruta\a\la\carpeta\de\datos
```

La app no usa caché en disco: los hallazgos se generan al pedirlos y el
resultado vive en memoria mientras la app está abierta. La verificación de
archivos cargados solo comprueba que existan en disco (no los lee).

## Ejecutar

```bash
python -m app.doctor    # verificar entorno y contratos (hacer esto primero)
python -m app.main      # abrir la aplicación
```

Importante: ambos comandos se ejecutan desde la RAÍZ del proyecto (la carpeta
que contiene `app/`, `logic/` y `models/`), no desde dentro de `app/`. Es lo que
permite que `models.file_names` sea importable.

---

## Qué hace hoy

**Navegación:** pantalla de inicio con una card por certificación; dentro de
cada una, sus hallazgos con accesos directos a "Cargar" y "Generar".

**Cargar Información** de los 8 hallazgos, con arrastrar y soltar, y un panel lateral que verifica contra el disco qué archivos están realmente guardados. Si un archivo no trae las columnas requeridas, la card muestra cuáles faltan. Cada hallazgo tiene su propia pantalla
con exactamente las fuentes que necesita.

El usuario **arrastra el archivo sobre la card** o lo elige con el botón; la app valida las cabeceras contra
el catálogo, consolida varios archivos si el slot lo admite, y escribe
`{DATA_PATH}/{file_name}.csv`.

Las fuentes transversales (DNI vs Usuarios, GDH, AD, Tickets) son **un solo
archivo en disco**. Cargarlas desde el hallazgo de Aplicaciones las deja
cargadas también en AD, Base de Datos y Perfiles. Para reemplazar una, se
elimina desde cualquier pantalla y se sube otra.

**Generar hallazgos**: los 8 están conectados a su reporte en `logic/`: se ejecuta el reporte de `logic/`, se muestra en
tabla con tarjetas de conteo por tipo de hallazgo, y se exporta a `.xlsx` con
las etiquetas visibles. El resultado vive en memoria mientras la app está
abierta: no se guarda en disco ni se precalienta nada. Cerrar la app descarta
los hallazgos generados (los archivos fuente y los Excel exportados quedan).

## Estructura

```
app/
├── main.py            punto de entrada
├── doctor.py          verificador de entorno y contratos
├── config.py          DATA_PATH y convenciones del CSV
│
├── catalog/           QUÉ se carga  (editar aquí, no en la UI)
│   ├── columns.py     cabeceras esperadas por fuente
│   ├── fuentes.py     definición única de cada fuente
│   ├── hallazgos.py   qué fuentes necesita cada hallazgo
│   ├── display.py     nombre técnico -> etiqueta visible
│   └── formatos.py    booleano -> X / SI-NO / Activo-Inactivo
│
├── ingest/            CÓMO se carga  (sin dependencias de Qt, testeable)
│   ├── normalize.py   normalización de cabeceras
│   ├── readers.py     lectura como texto, sin inferencia de tipos
│   ├── validate.py    columnas esperadas vs encontradas
│   ├── merge.py       consolidación de N archivos
│   └── writer.py      pipeline completo -> CSV
│
├── generation/        SALIDA hacia logic/
│   └── reports.py     adaptadores hallazgo -> reporte de logic/
│
├── storage/files.py   estado de carga (verificación por existencia en disco)
├── exports/excel.py   exportación .xlsx con las etiquetas visibles
├── tasks/runner.py    trabajo pesado fuera del hilo de la UI
└── ui/                PySide6
    └── responsive.py  grilla que reflowea + flow layout de acciones
```

`catalog/` e `ingest/` no importan PySide6. Se pueden probar con pytest sin
abrir una ventana, y sobreviven intactos si algún día cambia la tecnología de
interfaz.

---

## Cómo se hacen los cambios más frecuentes

| Necesito… | Editar |
|---|---|
| Cambiar las columnas que se validan de una fuente | `catalog/columns.py` |
| Agregar una fuente nueva | `catalog/fuentes.py` (una entrada) |
| Cambiar qué fuentes pide un hallazgo | `catalog/hallazgos.py` (lista de ids) |
| Renombrar una columna en pantalla y en el Excel | `catalog/display.py` (una línea) |
| Cambiar cómo se muestra un booleano (X, SI/NO, Activo) | `catalog/formatos.py` (una línea) |
| Cambiar el azul corporativo, tipografía o radios | `ui/theme.py` |
| Conectar un hallazgo nuevo a su reporte | `generation/reports.py` |

Renombrar una columna en `display.py` la cambia a la vez en la tabla y en el
Excel exportado. Salen del mismo diccionario, así que no se pueden desalinear.
Lo mismo vale para `formatos.py`: la tabla, el Excel del hallazgo y el Excel
del resumen leen el mismo diccionario.

### Agregar una fuente nueva (una card en «Cargar Información»)

Tres pasos, ninguno en la interfaz:

1. **`catalog/columns.py`** — las cabeceras que se validan del archivo:

   ```python
   MI_FUENTE = ["USUARIO", "DNI", "FECHA CREACION"]
   ```

2. **`catalog/fuentes.py`** — una línea, igual que las demás:

   ```python
   _reg(Fuente("mi-fuente", "Mi Fuente", OTROS_REPORTES,
               _one(FileName.MI_FUENTE, C.MI_FUENTE)))
   ```

   `FileName.MI_FUENTE` tiene que existir ya en `models/file_names.py`; ese
   archivo lo mantiene el backend, no esta capa.

   Si la fuente admite varios archivos que se consolidan, `multiple=True`. Si
   además hay que conservar de qué archivo vino cada fila, `origin_file=True`
   y un `subfolder=`.

3. **`catalog/hallazgos.py`** — agregar `"mi-fuente"` a la lista `fuente_ids`
   del hallazgo (o de varios: las fuentes transversales se comparten y quedan
   cargadas para todos a la vez).

Con eso ya está: la card, el arrastrar y soltar, la validación de cabeceras,
el panel lateral de estado, el contador de progreso y el borrado se generan
solos a partir del catálogo. `python -m app.doctor` avisa si el `FileName` no
existe o si un hallazgo apunta a una fuente que no está registrada.

---

## Decisiones de diseño

**Todo se lee como texto.** `dtype=str`, `keep_default_na=False`. La app de
carga no interpreta: transporta fielmente lo que el auditor descargó de cada
sistema. Quien convierte a fecha o booleano es `logic/`, que ya sabe el formato
de cada campo. Así un DNI `00123456` no pierde los ceros y una fecha
`01/02/2025` no se reinterpreta según el locale.

**El BOM se elimina a nivel de bytes**, antes de decodificar. Hacerlo sobre el
texto ya decodificado falla cuando el decoder cae a windows-1252 y el BOM
aparece como los tres caracteres `ï»¿` pegados al nombre de la primera columna.

**El formato de los booleanos es solo presentación.** `logic/` devuelve `bool`
nativos; `catalog/formatos.py` los traduce a `X` / `SI`-`NO` /
`Activo`-`Inactivo` al pintarlos y al exportarlos, pero el DataFrame en
memoria conserva el booleano. Así los conteos siguen operando sobre booleanos
y no sobre texto. El tercer estado (celda en blanco) es real: `logic/` escribe
`is_activo_gdh = (gdh_user and gdh_user.isActive)`, que vale `None` cuando el
DNI no aparece en GDH; eso es distinto de "No".

**La lectura del formato es idempotente.** `formatos.a_bool()` acepta tanto el
`bool` de `logic/` como el texto ya formateado. Hace falta porque el resumen
vuelve a leer el Excel que la propia app exportó: ahí la celda ya dice `X`, no
`True`.

**La interfaz se adapta al ancho.** La app se usa a media pantalla en monitores
Full HD (~960 px). Las grillas de cards recalculan sus columnas (1 a 3) en cada
cambio de tamaño y las barras de acciones bajan de línea en vez de recortarse.
El panel de estado ocupa su propia columna: empuja las cards a la izquierda,
nunca se superpone, y se oculta solo cuando no hay espacio para dos columnas.

**No hay estado de carga guardado.** La única verdad es el disco: si el
`.csv` existe, la fuente está cargada. La verificación solo comprueba la
existencia del archivo (no lo lee); las filas/columnas que se ven en las cards
provienen de la propia carga hecha en esta sesión. Esto elimina por
construcción los desfases entre lo que la interfaz cree y lo que hay
realmente.

**La escritura es atómica.** Se escribe a un temporal y recién al terminar se
reemplaza el definitivo. Si la aplicación muere a mitad de una carga grande, el
archivo anterior queda intacto en vez de quedar truncado.

**Sin caché.** No hay caché en disco ni precalentamiento de servicios: cada
«Generar Hallazgos» ejecuta el reporte de `logic/` desde cero con los archivos
actuales. Lo que ves en la tabla siempre corresponde a la última generación
que pediste en esta sesión.

---

## Pendientes

- **Bug en `logic/` (reportar al backend):** `ADService.sync_last_activity_entra()`
  no la llama nadie, y aunque se llamara asigna `user.last_activity`, mientras
  que `ad_report.py` lee `ad_user.ultima_actividad_entra`, que nunca se escribe.
  Por eso la columna "Último Login Entra" del hallazgo de AD sale vacía aunque
  el archivo de Entra ID esté cargado. No se arregla desde `app/` por la regla
  del proyecto.
- Confirmar el mapeo de fuentes de la Certificación de Generales y Especiales
  (hoy en `catalog/hallazgos.py` marcado con `TODO`).
- Empaquetado con PyInstaller.
- Fuente Inter: colocar los `.ttf` en `app/ui/fonts/` para que viaje con la
  aplicación. Sin ellos se usa Segoe UI, que existe en todo Windows.
