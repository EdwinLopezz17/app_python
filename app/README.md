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

Opcionalmente, para mover la caché de hallazgos a otra ubicación:

```
CACHE_PATH=C:\ruta\a\la\cache
```

Si no se indica, la caché va a `%LOCALAPPDATA%\Pacifico\CertificacionPPS`.
**Nunca dentro de OneDrive.**

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

Cargar Información de los 6 hallazgos. Cada hallazgo tiene su propia pantalla
con exactamente las fuentes que necesita.

El usuario elige un `.csv`, `.xls` o `.xlsx`; la app valida las cabeceras contra
el catálogo, consolida varios archivos si el slot lo admite, y escribe
`{DATA_PATH}/{file_name}.parquet`.

Las fuentes transversales (DNI vs Usuarios, GDH, AD, Tickets) son **un solo
archivo en disco**. Cargarlas desde el hallazgo de Aplicaciones las deja
cargadas también en AD, Base de Datos y Perfiles. Para reemplazar una, se
elimina desde cualquier pantalla y se sube otra.

## Estructura

```
app/
├── main.py            punto de entrada
├── doctor.py          verificador de entorno y contratos
├── config.py          DATA_PATH y CACHE_PATH
│
├── catalog/           QUÉ se carga  (editar aquí, no en la UI)
│   ├── columns.py     cabeceras esperadas por fuente
│   ├── fuentes.py     definición única de cada fuente
│   ├── hallazgos.py   qué fuentes necesita cada hallazgo
│   └── display.py     nombre técnico -> etiqueta visible
│
├── ingest/            CÓMO se carga  (sin dependencias de Qt, testeable)
│   ├── normalize.py   normalización de cabeceras
│   ├── readers.py     lectura como texto, sin inferencia de tipos
│   ├── validate.py    columnas esperadas vs encontradas
│   ├── merge.py       consolidación de N archivos
│   └── writer.py      pipeline completo -> Parquet
│
├── storage/files.py   estado de carga (leído del disco, sin estado propio)
├── cache/             hallazgos generados en Parquet + invalidación por huella
├── exports/excel.py   exportación .xlsx con las etiquetas visibles
├── tasks/runner.py    trabajo pesado fuera del hilo de la UI
└── ui/                PySide6
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
| Cambiar el azul corporativo, tipografía o radios | `ui/theme.py` |

Renombrar una columna en `display.py` la cambia a la vez en la tabla y en el
Excel exportado. Salen del mismo diccionario, así que no se pueden desalinear.

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

**No hay estado de carga guardado.** La única verdad es el disco: si el
`.parquet` existe, la fuente está cargada. Esto elimina por construcción los
desfases entre lo que la interfaz cree y lo que hay realmente.

**La escritura es atómica.** Se escribe a un temporal y recién al terminar se
reemplaza el definitivo. Si la aplicación muere a mitad de una carga grande, el
archivo anterior queda intacto en vez de quedar truncado.

**La caché de hallazgos se invalida por huella.** Cada hallazgo guardado
recuerda el tamaño y la fecha de modificación de las fuentes que lo generaron.
Si alguna cambió, el hallazgo se marca como desactualizado automáticamente.

---

## Pendientes

- Generar hallazgos: conectar las pantallas con los reportes de
  `logic/*/reports/`. La caché ya está lista para recibirlos.
- Confirmar el mapeo de fuentes de la Certificación de Generales y Especiales
  (hoy en `catalog/hallazgos.py` marcado con `TODO`).
- Empaquetado con PyInstaller.
- Fuente Inter: colocar los `.ttf` en `app/ui/fonts/` para que viaje con la
  aplicación. Sin ellos se usa Segoe UI, que existe en todo Windows.
