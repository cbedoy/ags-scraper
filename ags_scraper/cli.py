"""Interfaz de línea de comandos para consultar el Periódico Oficial de Aguascalientes."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from .periodico import (
    EDICIONES,
    ORDENES_GOB,
    SECCIONES,
    TIPOS_PUBLICACION,
    PeriodicoOficialClient,
)


def _clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Elimina campos internos y rutas de Windows del servidor."""
    keep = {
        "IdPeriodico",
        "FechaPublicacion",
        "Numero",
        "Tomo",
        "Edicion",
        "Seccion",
        "Dependencias",
        "Total",
    }
    cleaned = {k: v for k, v in record.items() if k in keep}
    if "FechaPublicacion" in cleaned:
        cleaned["FechaPublicacion"] = str(cleaned["FechaPublicacion"])[:10]
    cleaned.setdefault("PdfUrl", None)
    if "IdPeriodico" in cleaned:
        cleaned["PdfUrl"] = PeriodicoOficialClient.url_pdf(cleaned["IdPeriodico"])
    return cleaned


def _print_results(results: List[Dict[str, Any]], limite: int) -> None:
    total = results[0].get("Total", len(results)) if results else 0
    print(f"Total de periódicos encontrados: {total}")
    shown = results[:limite]
    print(f"Mostrando {len(shown)}:\n")
    for i, record in enumerate(shown, 1):
        fecha = str(record.get("FechaPublicacion", ""))[:10]
        numero = record.get("Numero", "-")
        tomo = record.get("Tomo", "-")
        edicion = record.get("Edicion", "-")
        seccion = record.get("Seccion", "-")
        idp = record.get("IdPeriodico")
        print(f"[{i}] Periódico {idp} | {fecha} | Núm. {numero} | Tomo {tomo}")
        print(f"    Edición: {edicion} | Sección: {seccion}")
        print(f"    PDF: {PeriodicoOficialClient.url_pdf(idp)}")
        print()


def cmd_search(client: PeriodicoOficialClient, args: argparse.Namespace) -> int:
    try:
        results = client.buscar(
            titulo=args.titulo or "",
            contenido=args.contenido or "",
            fecha_ini=args.fecha_ini or "",
            fecha_fin=args.fecha_fin or "",
            edicion=args.edicion or "",
            seccion=args.seccion or "",
            orden_gobierno=args.orden or "",
            tipo_publicacion=args.tipo or "",
            numero=args.numero or "",
            pagina=args.pagina,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        payload = [_clean_record(r) for r in results[: args.limite]]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not results:
        print("Sin resultados.")
        return 0

    _print_results(results, args.limite)

    if args.descargar:
        for record in results[: args.limite]:
            idp = record["IdPeriodico"]
            try:
                path = client.descargar_pdf(idp, args.salida)
                print(f"Descargado: {path}")
            except (RuntimeError, OSError) as exc:
                print(f"No se pudo descargar {idp}: {exc}", file=sys.stderr)
    return 0


def cmd_detalle(client: PeriodicoOficialClient, args: argparse.Namespace) -> int:
    try:
        docs = client.detalle(args.id)
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(docs, ensure_ascii=False, indent=2, default=str))
        return 0

    if not docs:
        print("Sin documentos.")
        return 0

    print(f"Documentos en el periódico {args.id} ({len(docs)}):\n")
    for i, doc in enumerate(docs, 1):
        nombre = doc.get("NombreDocumento", "-").strip()
        pagina = doc.get("Pagina", "-")
        print(f"[{i}] p.{pagina}  {nombre}")
    return 0


def cmd_pdf(client: PeriodicoOficialClient, args: argparse.Namespace) -> int:
    print(PeriodicoOficialClient.url_visor(args.id, args.pagina))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="poe",
        description="Consulta el Periódico Oficial del Estado de Aguascalientes (uso no oficial).",
    )
    parser.add_argument("--timeout", type=float, default=60, help="Timeout HTTP en segundos.")
    parser.add_argument("--insecure", action="store_true", help="No verificar certificados TLS.")

    sub = parser.add_subparsers(dest="command")

    # Búsqueda -----------------------------------------------------------
    search = sub.add_parser("search", help="Buscar periódicos por palabras y filtros.")
    search.add_argument("-t", "--titulo", help="Búsqueda por título del documento.")
    search.add_argument("-c", "--contenido", help="Búsqueda dentro del contenido/índice.")
    search.add_argument("--fecha-ini", help="Fecha inicial (dd/mm/aaaa).")
    search.add_argument("--fecha-fin", help="Fecha final (dd/mm/aaaa).")
    search.add_argument("-e", "--edicion", help="Edición (id o nombre).")
    search.add_argument("-s", "--seccion", help="Sección (id o nombre).")
    search.add_argument("-o", "--orden", help="Orden de gobierno (id o nombre).")
    search.add_argument("-k", "--tipo", help="Tipo de publicación (id o nombre).")
    search.add_argument("--numero", help="Número del periódico.")
    search.add_argument("-p", "--pagina", type=int, default=1, help="Página de resultados.")
    search.add_argument("-n", "--limite", type=int, default=20, help="Resultados a mostrar.")
    search.add_argument("--json", action="store_true", help="Salida JSON.")
    search.add_argument("--descargar", action="store_true", help="Descargar los PDF mostrados.")
    search.add_argument("--salida", default=".", help="Directorio de descarga (con --descargar).")
    search.set_defaults(func=cmd_search)

    # Detalle ------------------------------------------------------------
    detalle = sub.add_parser("detalle", help="Listar documentos dentro de un periódico.")
    detalle.add_argument("id", type=int, help="IdPeriódico.")
    detalle.add_argument("--json", action="store_true", help="Salida JSON.")
    detalle.set_defaults(func=cmd_detalle)

    # Enlace PDF ---------------------------------------------------------
    pdf = sub.add_parser("pdf", help="Mostrar enlace del visor PDF de un periódico.")
    pdf.add_argument("id", type=int, help="IdPeriódico.")
    pdf.add_argument("-p", "--pagina", type=int, default=1, help="Página del PDF.")
    pdf.set_defaults(func=cmd_pdf)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    client = PeriodicoOficialClient(timeout=args.timeout, insecure=args.insecure)
    try:
        return args.func(client, args)
    except BrokenPipeError:
        import os

        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
