---
name: periodico-oficial-ags
description: Searches the Periódico Oficial del Estado de Aguascalientes (official state gazette) by title, full-text content, date range, edition, section, issuing authority, and document type, and retrieves documents or PDF links. Use to find laws, decrees, reglamentos, acuerdos, convenios, edictos and other official publications. Spanish deliverables.
---

# Periódico Oficial de Aguascalientes

Search and retrieve publications from the Periódico Oficial del Estado de
Aguascalientes using the bundled `ags-scraper` CLI.

## When to Use

- Finding a specific decree, law, reglamento, acuerdo, convenio, edicto, or
  budget publication.
- Checking when a norm was published (entry into force) and its PDF page.
- Pulling the list of documents inside a given edition (por índice).

## Prerequisites

- Python 3.9+.
- The `ags-scraper` repo available locally (the CLI is `poe.py` at the repo root).
- Network access to `https://eservicios2.aguascalientes.gob.mx/periodicooficial/`.

## Commands

```bash
# Search by title
python poe.py search -t "reglamento"

# Search by full-text content (may be slow/intermittent; retry if empty)
python poe.py search -c "desarrollo urbano"

# Search with filters: date range + edition + document type
python poe.py search --fecha-ini 01/01/2024 --fecha-fin 31/12/2024 -e extraordinario -k decreto

# Limit, paginate, JSON export
python poe.py search -t reglamento -n 10 --json
python poe.py search -t reglamento -p 2

# List documents (with page numbers) inside a periódico
python poe.py detalle <IdPeriodico>

# Viewer/PDF URL
python poe.py pdf <IdPeriodico> -p <pagina>
```

## Output

- Human-readable table with `IdPeriodico`, `FechaPublicacion`, `Numero`, `Tomo`,
  `Edicion`, `Seccion`, and the direct PDF URL.
- `--json` for machine-readable results (respects `--limite`).

## Caveats

- The portal is **solo consulta** and not legally official; always confirm
  against the official source for legal use.
- Full-text search (`--contenido`) depends on the server index and can be
  intermittent; prefer `--titulo` when possible and retry content searches.
- 500 results are returned per page; use `-p` to paginate and read `Total` for
  the full match count.
