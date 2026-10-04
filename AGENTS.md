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

- La búsqueda por **texto completo** (`Contenido`) es intermitente/lenta en el
  servidor. Preferir `NombreDocumento` cuando sea posible y documentar el aviso.
- El `Link` que devuelve el servidor es una ruta Windows local (inútil); usar
  `Archivos/{IdPeriodico}.pdf`.

## Agregar un script nuevo

1. Crear `ags_scraper/<fuente>.py` con su cliente y catálogos.
2. Añadir un subcomando en `ags_scraper/cli.py`.
3. Documentar en `README.md` (tabla de scripts) y en `skills/` si aplica.
4. Probar contra la fuente real.
