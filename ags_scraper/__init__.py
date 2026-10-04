"""ags-scraper: herramientas para consultar datos públicos del Gobierno del Estado de Aguascalientes."""

from .periodico import (
    BASE_URL,
    EDICIONES,
    ORDENES_GOB,
    SECCIONES,
    TIPOS_PUBLICACION,
    PeriodicoOficialClient,
)

__all__ = [
    "BASE_URL",
    "EDICIONES",
    "ORDENES_GOB",
    "SECCIONES",
    "TIPOS_PUBLICACION",
    "PeriodicoOficialClient",
]

__version__ = "0.1.0"
