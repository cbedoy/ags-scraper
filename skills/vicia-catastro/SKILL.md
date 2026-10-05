---
name: vicia-catastro
description: Queries the Aguascalientes cadastral viewer (VICEA / Instituto Registral y Catastral) by street address or settlement name to retrieve official address matches, parcel number (manzana/lote), coordinates, and the cadastral key (clave catastral), area, and regime of intersecting parcels. Use to look up cadastral/parcel information for a specific address in Aguascalientes without the slow web map. Spanish deliverables.
---

# Catastro VICEA (Aguascalientes)

Look up cadastral/parcel information for a specific address using the bundled
`ags-scraper` CLI, bypassing the slow web map (which only works in Safari).

## When to Use

- Finding the **clave catastral** and parcel data (área, régimen) for an address.
- Geocoding a street + number (+ colonia) to coordinates.
- Discovering official settlement (colonia) and street names for exact matching.

## Prerequisites

- Python 3.9+.
- The `ags-scraper` repo available locally (CLI `vicia.py` at the repo root).
- Network access to `http://visorcartografico.aguascalientes.gob.mx:6080`.

## Commands

```bash
# Address lookup (street + number)
python vicia.py direccion -c "convencion de 1914 sur" -n 102

# Narrow by settlement and municipality
python vicia.py direccion -c "convencion" -n 102 -a "del trabajo" -m aguascalientes

# Discover settlement (colonia) names
python vicia.py asentamientos -q "centro"

# Discover street names within a settlement
python vicia.py vialidades -q "convencion" -a 00017

# Machine-readable output
python vicia.py direccion -c "convencion" -n 102 --json
```

## Output

Each match includes calle, número, colonia, manzana, lote, coordinates (lat/lon
with a Google Maps link), and intersecting **predios** with `CVE_CAT_EST`
(clave catastral), `CVE_CAT_ORI`, área (m²) and `REGIMEN`.

## Municipalities

`-m` accepts id or name: `1` aguascalientes, `2` asientos, `3` calvillo,
`4` cosio, `5` jesus maria, `6` pabellon de arteaga, `7` rincon de romos,
`8` san jose de gracia, `9` tepezala, `10` el llano, `11` san francisco de los
romo.

## Caveats

- The data is read-only and unofficial; confirm against the Instituto Registral
  y Catastral for legal/titling use.
- ArcGIS services are HTTP only (port 6080); HTTPS is misconfigured on their side.
- Searches are accent-insensitive; write street names without accents if unsure.
