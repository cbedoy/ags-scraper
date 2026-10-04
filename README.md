# ags-scraper

Herramientas de línea de comandos para consultar datos públicos del Gobierno del
Estado de Aguascalientes, México.

> **Autor:** Carlos Cervantes Bedoy
> **Licencia:** MIT
> **Estado:** en desarrollo temprano

## Motivo

La información pública del estado (Periódico Oficial, catastro, visores
cartográficos, normateca, etc.) existe, pero muchas veces es difícil de buscar:
interfaces web antiguas, formularios con paginación manual, resultados sin
exportación y endpoints que solo funcionan desde el navegador.

Este repositorio reúne **scripts pequeños y autocontenidos** que exponen esos
datos como una interfaz de línea de comandos y como librería de Python, para
automatizar búsquedas, descargas y análisis. La idea es ir agregando un script
por fuente de datos pública del estado.

### Scripts (actuales y planeados)

| Script | Fuente | Estado |
| ------ | ------ | ------ |
| `poe.py` | Periódico Oficial del Estado de Aguascalientes | ✅ funcional |
| *(visor catastral / VICEA)* | Instituto Registral y Catastral | 🔜 planeado |
| *(normateca)* | Normateca estatal | 🔜 planeado |

## `poe.py` — Periódico Oficial

Consulta el Periódico Oficial del Estado de Aguascalientes
(`https://eservicios2.aguascalientes.gob.mx/periodicooficial/`) desde la
terminal. Sin dependencias externas (solo librería estándar de Python).

> ⚠️ El contenido del portal es de **solo consulta** y **no tiene carácter
> oficial** (así lo declara el propio sitio). Para fines legales usa la fuente
> oficial.

### Requisitos

- Python 3.9+ (solo librería estándar).

### Uso

```bash
# Búsqueda por título del documento
python poe.py search -t reglamento

# Búsqueda dentro del contenido/índice (texto completo)
python poe.py search -c "desarrollo urbano"

# Combinar filtros: edición, tipo de publicación y rango de fechas
python poe.py search -e extraordinario -k decreto --fecha-ini 01/01/2024 --fecha-fin 31/12/2024

# Limitar resultados, paginar y exportar a JSON
python poe.py search -t reglamento -n 5 --json
python poe.py search -t reglamento -p 2 -n 10

# Ver los documentos (con página) dentro de un periódico
python poe.py detalle 568

# Enlace del visor PDF (o descargar los PDF mostrados)
python poe.py pdf 568 -p 2
python poe.py search -t reglamento -n 3 --descargar --salida ./pdfs
```

### Subcomandos

- `search` — busca periódicos por título (`-t`), contenido (`-c`), fechas,
  edición (`-e`), sección (`-s`), orden de gobierno (`-o`), tipo de publicación
  (`-k`) y número.
- `detalle <id>` — lista los documentos individuales dentro de un periódico.
- `pdf <id>` — imprime la URL del visor PDF.

### Filtros (id o nombre, sin acentos)

- **Edición:** `1` ordinario, `2` extraordinario, `3` vespertina.
- **Sección:** `1` primera … `10` décima, `52` vespertina, `58` extraordinario.
- **Orden de gobierno:** `1` poder legislativo, `2` poder ejecutivo,
  `3` poder judicial, `73` gobierno federal, entre otros.
- **Tipo de publicación:** `1` decreto, `2` reglamento, `3` acuerdo, `4`
  convenio, `163` edicto, etc.

Puedes ver los catálogos completos en `ags_scraper/periodico.py`.

### Uso como librería

```python
from ags_scraper import PeriodicoOficialClient

client = PeriodicoOficialClient()
resultados = client.buscar(titulo="reglamento", pagina=1)
for r in resultados:
    print(r["IdPeriodico"], r["FechaPublicacion"], PeriodicoOficialClient.url_pdf(r["IdPeriodico"]))
```

## Notas técnicas

- El buscador expone un endpoint JSON (`Default.aspx/obtenerInformacion`) que
  devuelve 500 resultados por página; `Total` indica el total de coincidencias.
- La búsqueda de **texto completo** (`--contenido`) depende del índice del
  servidor y en ocasiones es lenta o devuelve resultados intermitentes. Si una
  búsqueda por contenido falla, reintenta o usa `--titulo`.
- El servidor usa HSTS/TLS válido; el flag `--insecure` solo debe usarse para
  depuración.

## Uso con un agente / skill

Se incluye un skill en `skills/periodico-oficial/SKILL.md` que documenta cómo un
agente puede usar este script. Cópialo a tu directorio de skills para registrarlo.

## Contribuir

Cada script nuevo debe:

1. Usar solo librería estándar de Python (o documentar dependencias).
2. Exponer una librería (`ags_scraper/*.py`) y un CLI (`poe.py`, o similar).
3. Incluir ejemplos de uso y su catálogo de filtros.
4. Dejar claro que la fuente es pública y de solo consulta.
