"""Interfaz de línea de comandos del visor catastral VICEA (Aguascalientes)."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from .vicia import MUNICIPIOS, ViceaClient, resolve_municipio


def _print_direccion(resultados: List[Dict[str, Any]]) -> None:
    if not resultados:
        print("Sin resultados.")
        return
    print(f"Se encontraron {len(resultados)} domicilio(s):\n")
    for i, r in enumerate(resultados, 1):
        a = r["attributes"]
        c = r["centroide"]
        print(f"[{i}] {a.get('NOMBRE_COMPLETO_VIALIDAD')} {a.get('NUMERO_EXTERIOR')}"
              + (f" int. {a['NUMERO_INTERIOR']}" if a.get("NUMERO_INTERIOR") else ""))
        print(f"    Colonia: {a.get('NOMBRE_COMPLETO_ASENTAMIENTO')}")
        print(f"    Manzana: {a.get('MANZANA') or '-'} | Lote: {a.get('LOTE') or '-'}")
        if c:
            print(f"    Ubicación: {c['lat']:.6f}, {c['lon']:.6f}  {ViceaClient.url_maps(c['lat'], c['lon'])}")
        predios = r.get("predios", [])
        if predios:
            print(f"    Predios intersectados ({len(predios)}):")
            for p in predios:
                area = p.get("SHAPE_STArea__")
                area_txt = f"{area:,.1f} m²" if area is not None else "-"
                regimen = p.get("REGIMEN")
                print(f"      - Clave catastral: {p.get('CVE_CAT_EST') or '-'}")
                if p.get("CVE_CAT_ORI"):
                    print(f"        Clave original: {p.get('CVE_CAT_ORI')}")
                line = f"        Área: {area_txt}"
                if regimen:
                    line += f" | Régimen: {regimen}"
                if p.get("SC_CATASTRO") is not None:
                    line += f" | SC_CATASTRO: {p.get('SC_CATASTRO')}"
                print(line)
        else:
            print("    Predios: ninguno intersectado (posible capa de predios no cargada).")
        print()


def cmd_direccion(client: ViceaClient, args: argparse.Namespace) -> int:
    try:
        resultados = client.informacion_direccion(
            calle=args.calle, numero=args.numero, asentamiento=args.colonia
        )
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(resultados, ensure_ascii=False, indent=2, default=str))
        return 0
    _print_direccion(resultados)
    return 0


def cmd_asentamientos(client: ViceaClient, args: argparse.Namespace) -> int:
    try:
        features = client.buscar_asentamientos(args.query)
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([f["attributes"] for f in features], ensure_ascii=False, indent=2))
        return 0
    for f in features:
        a = f["attributes"]
        print(f"{a.get('CVE_ASENTAMIENTO')}  {a.get('NOMBRE_COMPLETO_ASENTAMIENTO')}  CP {a.get('CP')}")
    return 0


def cmd_vialidades(client: ViceaClient, args: argparse.Namespace) -> int:
    try:
        features = client.buscar_vialidades(args.query, args.asentamiento)
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([f["attributes"] for f in features], ensure_ascii=False, indent=2))
        return 0
    for f in features:
        a = f["attributes"]
        print(f"{a.get('CVE_VIALIDAD')}  {a.get('NOMBRE_COMPLETO_VIALIDAD')}  (asent. {a.get('CVE_ASENTAMIENTO')})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vicia",
        description="Consulta el catastro (visor VICEA) de Aguascalientes por dirección o clave. Uso no oficial.",
    )
    parser.add_argument("-m", "--municipio", default="1", help="Municipio (id o nombre).")
    parser.add_argument("--timeout", type=float, default=60, help="Timeout HTTP en segundos.")

    sub = parser.add_subparsers(dest="command")

    direccion = sub.add_parser("direccion", help="Buscar por calle y número.")
    direccion.add_argument("-c", "--calle", required=True, help="Nombre de la calle.")
    direccion.add_argument("-n", "--numero", required=True, help="Número exterior.")
    direccion.add_argument("-a", "--colonia", help="Colonia/asentamiento (opcional).")
    direccion.add_argument("--json", action="store_true", help="Salida JSON.")
    direccion.set_defaults(func=cmd_direccion)

    asentamientos = sub.add_parser("asentamientos", help="Buscar colonias por nombre.")
    asentamientos.add_argument("-q", "--query", required=True, help="Nombre o fragmento.")
    asentamientos.add_argument("--json", action="store_true", help="Salida JSON.")
    asentamientos.set_defaults(func=cmd_asentamientos)

    vialidades = sub.add_parser("vialidades", help="Buscar calles por nombre.")
    vialidades.add_argument("-q", "--query", required=True, help="Nombre o fragmento.")
    vialidades.add_argument("-a", "--asentamiento", help="CVE del asentamiento (opcional).")
    vialidades.add_argument("--json", action="store_true", help="Salida JSON.")
    vialidades.set_defaults(func=cmd_vialidades)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    client = ViceaClient(municipio=args.municipio, timeout=args.timeout)
    try:
        return args.func(client, args)
    except BrokenPipeError:
        import os

        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
