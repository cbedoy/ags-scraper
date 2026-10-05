"""ags-scraper: herramientas para consultar datos públicos del Gobierno del Estado de Aguascalientes."""

from .periodico import (
    BASE_URL,
    EDICIONES,
    ORDENES_GOB,
    SECCIONES,
    TIPOS_PUBLICACION,
    PeriodicoOficialClient,
)
from .vicia import MUNICIPIOS, ViceaClient

__all__ = [
    "BASE_URL",
    "EDICIONES",
    "ORDENES_GOB",
    "SECCIONES",
    "TIPOS_PUBLICACION",
    "MUNICIPIOS",
    "PeriodicoOficialClient",
    "ViceaClient",
]

__version__ = "0.2.0"
