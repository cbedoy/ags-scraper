"""Cliente no oficial del visor catastral VICEA (Instituto Registral y Catastral).

Consulta por dirección y por clave catastral los servicios ArcGIS REST que
utiliza el visor:

    http://visorcartografico.aguascalientes.gob.mx:6080/arcgis/rest/services/VICEA_AGS_<municipio>/MapServer

Funciona sobre HTTP (no HTTPS) en el puerto 6080. Sin credenciales.
"""

from __future__ import annotations

import json
import unicodedata
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

ARC_HOST = "http://visorcartografico.aguascalientes.gob.mx:6080"
SERVICE_TMPL = ARC_HOST + "/arcgis/rest/services/VICEA_AGS_{municipio}/MapServer"

# Capas relevantes (iguales en los 11 municipios)
LAYER_PREDIOS = 4          # "P" — predios (terrenos)
LAYER_CONSTRUCCIONES = 5   # "C" — construcciones
LAYER_VIALIDADES = 6       # "VIALIDADES" — calles (polilíneas)
LAYER_ASENTAMIENTOS = 7    # "ASENTAMIENTOS" — colonias (polígonos)
LAYER_NUMERO_OFICIAL = 8   # "NUMERO_OFICIAL" — números de domicilio

MUNICIPIOS: Dict[str, str] = {
    "1": "AGUASCALIENTES",
    "2": "ASIENTOS",
    "3": "CALVILLO",
    "4": "COSIO",
    "5": "JESUS MARIA",
    "6": "PABELLON DE ARTEAGA",
    "7": "RINCON DE ROMOS",
    "8": "SAN JOSE DE GRACIA",
    "9": "TEPEZALA",
    "10": "EL LLANO",
    "11": "SAN FRANCISCO DE LOS ROMO",
}


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return "".join(ch.upper() for ch in stripped)


def resolve_municipio(value: str) -> str:
    """Resuelve id o nombre de municipio (ej. 'aguascalientes' -> '1')."""
    value = value.strip()
    if value in MUNICIPIOS:
        return value
    normalized = _strip_accents(value)
    for key, name in MUNICIPIOS.items():
        if _strip_accents(name) == normalized:
            return key
    raise ValueError(f"Municipio no reconocido: {value!r}. Opciones: {list(MUNICIPIOS.values())}")


class ViceaClient:
    """Consulta de direcciones y predios en el catastro de Aguascalientes."""

    def __init__(self, municipio: str = "1", timeout: float = 60) -> None:
        self.municipio = resolve_municipio(municipio)
        self.service = SERVICE_TMPL.format(municipio=self.municipio)
        self.timeout = timeout

    # ------------------------------------------------------------------ HTTP

    def _get_json(self, url: str) -> Dict[str, Any]:
        request = urllib.request.Request(url, headers={"User-Agent": "ags-scraper/0.2"})
        with urllib.request.urlopen(request, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def _post_json(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        body = urllib.parse.urlencode(params).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "User-Agent": "ags-scraper/0.2",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def _query_layer(self, layer: int, where: str, out_fields: str = "*",
                     return_geometry: bool = False, out_sr: int = 4326,
                     result_count: int = 50) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true" if return_geometry else "false",
            "f": "json",
            "resultRecordCount": result_count,
        }
        if return_geometry:
            params["outSR"] = out_sr
        url = f"{self.service}/{layer}/query?" + urllib.parse.urlencode(params)
        data = self._get_json(url)
        if "error" in data:
            raise RuntimeError(f"Error de ArcGIS: {data['error']}")
        return data.get("features", [])

    # ------------------------------------------------------------- Búsquedas

    @staticmethod
    def _like(term: str) -> str:
        """Normaliza un término para LIKE: sin acentos, mayúsculas, comillas escapadas."""
        term = _strip_accents(term).replace("'", "''")
        return term

    def buscar_asentamientos(self, nombre: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Colonias/asentamientos cuyo nombre contiene ``nombre``."""
        where = f"UPPER(NOMBRE_COMPLETO_ASENTAMIENTO) LIKE '%{self._like(nombre)}%'"
        return self._query_layer(
            LAYER_ASENTAMIENTOS, where,
            out_fields="CVE_ASENTAMIENTO,NOMBRE_COMPLETO_ASENTAMIENTO,CP,TIPO_ASENTAMIENTO",
            return_geometry=False, result_count=limit,
        )

    def buscar_vialidades(self, nombre: str, cve_asentamiento: Optional[str] = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Calles cuyo nombre contiene ``nombre`` (opcionalmente dentro de una colonia)."""
        where = f"UPPER(NOMBRE_COMPLETO_VIALIDAD) LIKE '%{self._like(nombre)}%'"
        if cve_asentamiento:
            where += f" AND CVE_ASENTAMIENTO = '{cve_asentamiento}'"
        return self._query_layer(
            LAYER_VIALIDADES, where,
            out_fields="CVE_VIALIDAD,CVE_ASENTAMIENTO,NOMBRE_COMPLETO_VIALIDAD,TIPO_VIALIDAD",
            return_geometry=False, result_count=limit,
        )

    def buscar_direccion(self, calle: str, numero: str,
                         asentamiento: Optional[str] = None,
                         limit: int = 50) -> List[Dict[str, Any]]:
        """Busca domicilios por calle y número exterior (y opcional colonia)."""
        where = f"UPPER(NOMBRE_COMPLETO_VIALIDAD) LIKE '%{self._like(calle)}%'"
        where += f" AND NUMERO_EXTERIOR = '{numero}'"
        if asentamiento:
            where += f" AND UPPER(NOMBRE_COMPLETO_ASENTAMIENTO) LIKE '%{self._like(asentamiento)}%'"
        return self._query_layer(
            LAYER_NUMERO_OFICIAL, where,
            out_fields=(
                "NOMBRE_COMPLETO_VIALIDAD,NOMBRE_COMPLETO_ASENTAMIENTO,NUMERO_EXTERIOR,"
                "NUMERO_INTERIOR,MANZANA,LOTE,CVE_ASENTAMIENTO,CVE_VIALIDAD,CVE_MUNICIPIO"
            ),
            return_geometry=True, result_count=limit,
        )

    def predios_en_geometria(self, geometry: Dict[str, Any],
                             limit: int = 20) -> List[Dict[str, Any]]:
        """Predios (terrenos) que intersectan una geometría ArcGIS.

        Usa POST para soportar geometrías grandes (evita el límite de longitud
        de URL de una petición GET).
        """
        params: Dict[str, Any] = {
            "where": "1=1",
            "outFields": (
                "CVE_CAT_EST,CVE_CAT_ORI,CVE_CAT_ORI_MUNICIPAL,REGIMEN,STATUS,"
                "ST_CATASTRO,SC_CATASTRO,SHAPE_STArea__"
            ),
            "returnGeometry": "false",
            "geometry": json.dumps(geometry),
            "geometryType": "esriGeometryPolygon",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": 4326,
            "f": "json",
            "resultRecordCount": limit,
        }
        url = f"{self.service}/{LAYER_PREDIOS}/query"
        data = self._post_json(url, params)
        if "error" in data:
            raise RuntimeError(f"Error de ArcGIS: {data['error']}")
        return data.get("features", [])

    # ------------------------------------------------------------ Resultados

    def informacion_direccion(self, calle: str, numero: str,
                              asentamiento: Optional[str] = None) -> List[Dict[str, Any]]:
        """Dirección -> domicilios encontrados y predios que los intersectan.

        Devuelve una lista con un elemento por domicilio; cada uno incluye sus
        atributos, el centroide (lat/lon) y los predios (clave catastral, área).
        """
        domicilios = self.buscar_direccion(calle, numero, asentamiento)
        resultados: List[Dict[str, Any]] = []
        for feature in domicilios:
            attrs = feature.get("attributes", {})
            geometry = feature.get("geometry")
            centroide = self._centroid(geometry)
            predios = self.predios_en_geometria(geometry) if geometry else []
            resultados.append({
                "attributes": attrs,
                "centroide": centroide,
                "predios": [p.get("attributes", {}) for p in predios],
            })
        return resultados

    @staticmethod
    def _centroid(geometry: Optional[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        if not geometry:
            return None
        rings = geometry.get("rings")
        if not rings:
            return None
        xs: List[float] = []
        ys: List[float] = []
        for ring in rings:
            for x, y in ring:
                xs.append(x)
                ys.append(y)
        if not xs:
            return None
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        return {"lat": cy, "lon": cx}

    @staticmethod
    def url_maps(lat: float, lon: float) -> str:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
