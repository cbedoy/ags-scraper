"""Cliente no oficial para consultar el Periódico Oficial del Estado de Aguascalientes.

Este módulo implementa un cliente mínimo (solo librería estándar) sobre los
endpoints JSON que utiliza el visor público del Periódico Oficial:

    https://eservicios2.aguascalientes.gob.mx/periodicooficial/

No requiere credenciales. El contenido del portal es de *solo consulta* y no
tiene carácter oficial (así lo declara el propio sitio).
"""

from __future__ import annotations

import json
import ssl
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

BASE_URL = "https://eservicios2.aguascalientes.gob.mx/periodicooficial"
SEARCH_ENDPOINT = BASE_URL + "/Default.aspx/obtenerInformacion"
DETAIL_ENDPOINT = BASE_URL + "/Default.aspx/obtenerDetalle"

# --- Catálogos (valor enviado al servidor -> etiqueta legible) ---------------

EDICIONES: Dict[str, str] = {
    "0": "SIN ASIGNAR",
    "1": "ORDINARIO",
    "2": "EXTRAORDINARIO",
    "3": "VESPERTINA",
}

SECCIONES: Dict[str, str] = {
    "0": "SIN ASIGNAR",
    "1": "PRIMERA SECCION",
    "2": "SEGUNDA SECCION",
    "3": "TERCERA SECCION",
    "4": "CUARTA SECCION",
    "5": "QUINTA SECCION",
    "6": "SEXTA SECCION",
    "7": "SÉPTIMA SECCION",
    "8": "OCTAVA SECCION",
    "9": "NOVENA SECCION",
    "10": "DÉCIMA SECCION",
    "52": "VESPERTINA",
    "53": "DÉCIMA PRIMERA SECCIÓN",
    "54": "DÉCIMA SEGUNDA SECCIÓN",
    "55": "DÉCIMA TERCERA SECCIÓN",
    "56": "DÉCIMA CUARTA SECCIÓN",
    "57": "DÉCIMA QUINTA SECCIÓN",
    "58": "EXTRAORDINARIO",
    "103": "DÉCIMA SEXTA SECCIÓN",
    "104": "DÉCIMA SÉPTIMA SECCIÓN",
    "106": "DÉCIMA OCTAVA SECCIÓN",
    "107": "DÉCIMA NOVENA SECCIÓN",
}

ORDENES_GOB: Dict[str, str] = {
    "1": "PODER LEGISLATIVO",
    "2": "PODER EJECUTIVO",
    "3": "PODER JUDICIAL",
    "52": "FISCALÍA GENERAL DEL ESTADO",
    "53": "INSTITUTO ESTATAL ELECTORAL",
    "54": "INSTITUTO DE TRANSPARENCIA DEL ESTADO DE AGUASCALIENTES",
    "55": "SISTEMA ESTATAL ANTICORRUPCIÓN DEL ESTADO DE AGUASCALIENTES",
    "57": "COMISIÓN ESTATAL DE DERECHOS HUMANOS",
    "58": "INSTITUTO NACIONAL ELECTORAL",
    "59": "ÓRGANO SUPERIOR DE FISCALIZACIÓN",
    "60": "TRIBUNAL ELECTORAL DEL ESTADO DE AGUASCALIENTES",
    "61": "PODER JUDICIAL DE LA FEDERACIÓN",
    "62": "FISCALÍA GENERAL DEL ESTADO DE AGUASCALIENTES",
    "63": "INSTITUTO DE TRANSPARENCIA DEL ESTADO",
    "71": "ÓRGANOS AUTÓNOMOS",
    "73": "GOBIERNO FEDERAL",
    "74": "SECRETARÍA EJECUTIVA DEL SISTEMA ESTATAL ANTICORRUPCIÓN",
    "75": "OTRO",
}

TIPOS_PUBLICACION: Dict[str, str] = {
    "1": "DECRETO",
    "2": "REGLAMENTO",
    "3": "ACUERDO",
    "4": "CONVENIO",
    "6": "JUDICIALES Y GENERALES",
    "7": "AVISO NOTARIAL",
    "8": "CIRCULARES",
    "52": "FE DE ERRATAS",
    "53": "SECCION DE AVISOS",
    "54": "INFORME",
    "55": "ÍNDICE",
    "56": "CONVOCATORIA",
    "57": "RESOLUCIÓN",
    "58": "SENTENCIA",
    "59": "ACTA",
    "61": "LINEAMIENTOS",
    "62": "OTROS",
    "63": "REPORTES",
    "64": "AVISO",
    "65": "ANEXO",
    "66": "CÓDIGO MUNICIPAL",
    "67": "PRESUPUESTO DE EGRESOS",
    "68": "CÓDIGO",
    "69": "MANUAL",
    "70": "PROGRAMA",
    "71": "TABULADOR DE SUELDOS",
    "73": "POLÍTICAS DE OPERACIÓN",
    "74": "ESTATUTO",
    "75": "REGLAS DE OPERACIÓN",
    "76": "NORMAS",
    "77": "BASES",
    "78": "PROCEDIMIENTO",
    "79": "ESTATUTO ORGÁNICO",
    "80": "CUENTA PÚBLICA",
    "81": "GUÍA OPERATIVA",
    "82": "MARCO INTEGRAL",
    "83": "CÓDIGO DE ÉTICA",
    "84": "DEUDA PÚBLICA ESTATAL",
    "85": "DECLARATORIA DE INCORPORACIÓN",
    "86": "LICITACIÓN",
    "87": "CALENDARIO",
    "88": "CATÁLOGO",
    "89": "DEUDA PÚBLICA",
    "90": "REGLAS",
    "91": "POLÍTICAS DE DESCUENTO",
    "92": "LISTA DE PERITOS",
    "93": "DECLARATORIAS",
    "94": "FORTAMUN",
    "95": "CUOTAS Y TARIFAS",
    "145": "LEY ORGÁNICA",
    "146": "TARIFAS",
    "147": "ACCIÓN DE INCONSTITUCIONALIDAD",
    "148": "FIDEICOMISO",
    "149": "DICTAMEN",
    "150": "CERTIFICACIÓN DE PLAZO",
    "151": "DECLARATORIA CONSTITUCIONAL",
    "152": "PROTOCOLO",
    "153": "PUNTOS DE ACUERDO",
    "154": "PUNTOS RESOLUTIVOS",
    "155": "RELACIÓN DE INTEGRANTES",
    "156": "FICHAS TÉCNICAS",
    "157": "BANDO DE POLICÍA Y GOBIERNO",
    "158": "NOMBRAMIENTO",
    "159": "FAISMUN",
    "160": "DIRECTORIO DE NOTARIOS",
    "161": "LISTA DE DECRETOS",
    "162": "CONTRATO",
    "163": "EDICTO",
    "166": "ESQUEMA DE DESARROLLO URBANO",
    "167": "PLAN DE DESARROLLO",
    "168": "RELACIÓN DE ENTIDADES PARAESTATALES",
    "169": "PLAN ANUAL DE TRABAJO",
    "170": "DESCRIPCIONES GENERALES DE PUESTOS",
    "171": "PRESUPUESTO",
    "172": "FORMATOS",
    "173": "AUTORIZACIÓN",
    "174": "LISTADO DE OBRAS",
    "175": "FONDO",
    "177": "LISTADO DE FACILITADORES JUDICIALES",
    "178": "TABLA DE APORTACIONES",
}

RESULTS_PER_PAGE = 500


def _strip_accents(text: str) -> str:
    """Normaliza texto para comparaciones: sin acentos, mayúsculas."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return "".join(ch.upper() for ch in stripped)


def _resolve(value: str, catalog: Dict[str, str]) -> str:
    """Resuelve un filtro: acepta el ID numérico o el nombre (sin acentos)."""
    value = value.strip()
    if value in catalog:
        return value
    normalized = _strip_accents(value)
    for key, label in catalog.items():
        if _strip_accents(label) == normalized:
            return key
    raise ValueError(
        f"Valor no reconocido: {value!r}. Opciones: "
        + ", ".join(f"{k}={v}" for k, v in catalog.items())
    )


def _format_date(ddmmyyyy: str, end_of_day: bool) -> str:
    """Convierte 'dd/mm/yyyy' al formato que espera el servidor.

    El servidor recibe fechas en formato 'MM/DD/YYYY HH:MM:SS'.
    """
    if not ddmmyyyy:
        return ""
    try:
        day, month, year = ddmmyyyy.strip().split("/")
        day = int(day)
        month = int(month)
        year = int(year)
    except ValueError as exc:
        raise ValueError(f"Fecha inválida {ddmmyyyy!r}, use dd/mm/yyyy.") from exc
    time = "23:59:59" if end_of_day else "0:0:0"
    return f"{month:02d}/{day:02d}/{year} {time}"


class PeriodicoOficialClient:
    """Cliente de consulta del Periódico Oficial del Estado de Aguascalientes."""

    def __init__(self, timeout: float = 60, insecure: bool = False) -> None:
        self.timeout = timeout
        self.insecure = insecure

    # ------------------------------------------------------------------ HTTP

    def _post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        context = None
        if self.insecure:
            context = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout, context=context) as resp:
                body = resp.read()
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Error de conexión con {url}: {exc}") from exc
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Respuesta no JSON de {url}: {body[:200]!r}") from exc

    @staticmethod
    def _unwrap(outer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """El servidor responde {"d": "<cadena JSON>"}; devuelve la lista interna."""
        raw = outer.get("d") or ""
        if not raw:
            return []
        return json.loads(raw)

    # ------------------------------------------------------------- Búsquedas

    def buscar(
        self,
        titulo: str = "",
        contenido: str = "",
        fecha_ini: str = "",
        fecha_fin: str = "",
        edicion: str = "",
        seccion: str = "",
        orden_gobierno: str = "",
        tipo_publicacion: str = "",
        numero: str = "",
        pagina: int = 1,
    ) -> List[Dict[str, Any]]:
        """Busca periódicos por título, contenido y filtros.

        Devuelve la página solicitada de resultados (500 por página). Cada
        elemento incluye el campo ``Total`` con el número total de coincidencias.
        """
        payload: Dict[str, Any] = {
            "fipub": _format_date(fecha_ini, end_of_day=False),
            "ffpub": _format_date(fecha_fin, end_of_day=True),
            "actualIndice": None,
            "IdOrdenGobierno": _resolve(orden_gobierno, ORDENES_GOB) if orden_gobierno else "",
            "IdDependencia": "",
            "numero": numero,
            "IdEdicion": _resolve(edicion, EDICIONES) if edicion else "",
            "IdTipoPublicacion": (
                _resolve(tipo_publicacion, TIPOS_PUBLICACION) if tipo_publicacion else ""
            ),
            "NombreDocumento": titulo,
            "IdTomo": "",
            "IdSeccion": _resolve(seccion, SECCIONES) if seccion else "",
            "Contenido": contenido,
            "indiceActual": max(1, int(pagina)),
        }
        return self._unwrap(self._post(SEARCH_ENDPOINT, payload))

    def detalle(self, id_periodico: int) -> List[Dict[str, Any]]:
        """Lista los documentos individuales dentro de un periódico."""
        payload: Dict[str, Any] = {
            "id": id_periodico,
            "fipub": "",
            "ffpub": "",
            "actualIndice": None,
            "IdOrdenGobierno": "",
            "IdDependencia": "",
            "numero": "",
            "IdEdicion": "",
            "IdTipoPublicacion": "",
            "NombreDocumento": "",
            "IdTomo": "",
            "IdSeccion": "",
            "Contenido": "",
        }
        return self._unwrap(self._post(DETAIL_ENDPOINT, payload))

    # --------------------------------------------------------------- Enlaces

    @staticmethod
    def url_pdf(id_periodico: int) -> str:
        """URL directa del PDF de un periódico."""
        return f"{BASE_URL}/Archivos/{id_periodico}.pdf"

    @staticmethod
    def url_visor(id_periodico: int, pagina: int = 1) -> str:
        """URL del visor web que abre el PDF en una página concreta."""
        return (
            f"{BASE_URL}/web/viewer.html?file=../Archivos/{id_periodico}.pdf#page={pagina}"
        )

    def descargar_pdf(self, id_periodico: int, destino: str) -> str:
        """Descarga el PDF de un periódico y devuelve la ruta del archivo."""
        import pathlib

        url = self.url_pdf(id_periodico)
        path = pathlib.Path(destino) / f"{id_periodico}.pdf"
        request = urllib.request.Request(url, headers={"User-Agent": "ags-scraper/0.1"})
        context = ssl._create_unverified_context() if self.insecure else None
        with urllib.request.urlopen(request, timeout=self.timeout, context=context) as resp:
            content = resp.read()
        path.write_bytes(content)
        return str(path)
