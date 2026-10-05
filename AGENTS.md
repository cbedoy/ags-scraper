# AGENTS.md

Guía para agentes y colaboradores que trabajen en este repositorio.

## Qué es este proyecto

`ags-scraper` reúne scripts para consultar datos públicos del Gobierno del
Estado de Aguascalientes. El objetivo es convertir fuentes web difíciles de
buscar (Periódico Oficial, catastro, normateca, visores) en interfaces CLI y
librerías Python reutilizables.

Autor: **Carlos Cervantes Bedoy**.

## Convenciones

- **Python 3.9+**, solo librería estándar salvo justificación explícita.
- Cada fuente de datos vive en su propio módulo dentro de `ags_scraper/`.
- Cada módulo expone una clase/cliente reutilizable y, cuando aplica, un CLI.
- El CLI principal es `poe.py` (entrada delgada a `ags_scraper/cli.py`).
- No añadir comentarios innecesarios; código en inglés, mensajes de usuario en
  español.
- No se usan secretos ni credenciales; todo es consulta pública.

## Cómo verificar cambios

```bash
python3 poe.py --help
python3 poe.py search -t reglamento -n 3
python3 poe.py detalle 568
```

No hay suite de tests formal aún. Para validar un cambio en el cliente, ejecuta
una búsqueda real contra el endpoint y compara con los resultados del portal.

## Endpoints clave (Periódico Oficial)

- Base: `https://eservicios2.aguascalientes.gob.mx/periodicooficial/`
- Búsqueda: `POST .../Default.aspx/obtenerInformacion`
  - Devuelve `{"d": "<JSON string>"}` con 500 resultados por página.
  - Parámetros: `fipub`, `ffpub` (formato `MM/DD/YYYY HH:MM:SS`), `NombreDocumento`,
    `Contenido`, `IdEdicion`, `IdSeccion`, `IdOrdenGobierno`, `IdTipoPublicacion`,
    `numero`, `indiceActual`.
- Detalle de un periódico: `POST .../Default.aspx/obtenerDetalle` con `{"id": ...}`.
- PDF: `.../Archivos/{IdPeriodico}.pdf`
- Visor: `.../web/viewer.html?file=../Archivos/{id}.pdf#page={pagina}`

## Catálogos de filtros

Están en `ags_scraper/periodico.py` (constantes `EDICIONES`, `SECCIONES`,
`ORDENES_GOB`, `TIPOS_PUBLICACION`). Si el portal agrega valores, actualízalas ahí.

## Notas de comportamiento

- La búsqueda por **texto completo** (`Contenido`) del Periódico Oficial es
  intermitente/lenta en el servidor. Preferir `NombreDocumento` cuando sea
  posible y documentar el aviso.
- El `Link` que devuelve el servidor es una ruta Windows local (inútil); usar
  `Archivos/{IdPeriodico}.pdf`.

## Endpoints clave (Catastro / visor VICEA)

- Host ArcGIS: `http://visorcartografico.aguascalientes.gob.mx:6080` (HTTP, no HTTPS).
- Servicio por municipio: `.../arcgis/rest/services/VICEA_AGS_<municipio>/MapServer`
  (municipio 1–11; ver `MUNICIPIOS` en `ags_scraper/vicia.py`).
- Capas relevantes (iguales en los 11 municipios):
  - `4` "P" — predios (terrenos): `CVE_CAT_EST`, `CVE_CAT_ORI`, `REGIMEN`, `STATUS`, `SHAPE_STArea__`.
  - `5` "C" — construcciones.
  - `6` "VIALIDADES" — calles: `NOMBRE_COMPLETO_VIALIDAD`, `CVE_VIALIDAD`, `CVE_ASENTAMIENTO`.
  - `7` "ASENTAMIENTOS" — colonias: `NOMBRE_COMPLETO_ASENTAMIENTO`, `CVE_ASENTAMIENTO`, `CP`.
  - `8` "NUMERO_OFICIAL" — domicilios: `NOMBRE_COMPLETO_VIALIDAD`, `NOMBRE_COMPLETO_ASENTAMIENTO`, `NUMERO_EXTERIOR`, `MANZANA`, `LOTE`.
- Consultas: `GET/POST .../MapServer/<capa>/query` con `where`, `outFields`,
  `geometry`, `geometryType`, `spatialRel`, `inSR`, `f=json`.
- La búsqueda espacial (predios que intersectan un domicilio) debe usar **POST**
  (`ags_scraper/vicia.py`), porque las geometrías grandes exceden el límite de
  longitud de una URL GET (error HTTP 400).
- SR nativo: `32613` (UTM 13N); las consultas devuelven geometría en `4326`
  usando `outSR=4326` / `inSR=4326`.

## Agregar un script nuevo

1. Crear `ags_scraper/<fuente>.py` con su cliente y catálogos.
2. Añadir un subcomando en `ags_scraper/cli.py` (o un CLI nuevo en
   `ags_scraper/<fuente>_cli.py` + entrada delgada en la raíz).
3. Documentar en `README.md` (tabla de scripts) y en `skills/` si aplica.
4. Probar contra la fuente real.

Los CLI siguen el patrón de `poe.py`/`vicia.py`: entrada delgada en la raíz que
importa `main()` desde `ags_scraper/<fuente>_cli.py`.
