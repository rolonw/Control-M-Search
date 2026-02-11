#!/usr/bin/env python3
"""
Generador de claves de licencia. Solo el desarrollador debe ejecutar este script.
Usa el mismo secreto que la app (por defecto en código; opcionalmente LICENSE_SECRET).
No es necesario configurar variables de entorno.

Uso:
  python generate_license_key.py 2027-02-08

  O con años desde hoy:
  python generate_license_key.py --years 2

La clave generada se entrega al cliente/administrador para activar la licencia en /admin.
"""
import os
import sys
import hmac
import hashlib
from datetime import date, timedelta

# Mismo secreto que license_manager (por defecto en código)
from license_manager import _DEFAULT_LICENSE_SECRET


def _get_secret():
    return (os.getenv("LICENSE_SECRET") or _DEFAULT_LICENSE_SECRET).strip()


def _sign(expiry_iso: str) -> str:
    secret = _get_secret()
    if not secret:
        return ""
    return hmac.new(secret.encode("utf-8"), expiry_iso.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_key(expiry: date) -> str:
    """Genera una clave de licencia válida para la fecha de expiración dada."""
    expiry_iso = expiry.isoformat()
    sig = _sign(expiry_iso)
    return f"{expiry_iso}-{sig}"


def main():
    if len(sys.argv) < 2:
        print("Uso: python generate_license_key.py YYYY-MM-DD   (ej: 2027-02-08)")
        print("     python generate_license_key.py --years N    (ej: --years 2)")
        sys.exit(1)

    if sys.argv[1] == "--years" and len(sys.argv) >= 3:
        try:
            years = int(sys.argv[2])
            expiry = date.today() + timedelta(days=365 * years)
        except ValueError:
            print("Error: --years debe ir seguido de un número.", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            expiry = date.fromisoformat(sys.argv[1])
        except ValueError:
            print("Error: Fecha debe ser YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)

    if expiry <= date.today():
        print("Advertencia: La fecha de expiración ya pasó o es hoy.", file=sys.stderr)

    key = generate_key(expiry)
    print(f"Licencia válida hasta: {expiry.isoformat()}")
    print(f"Clave (entregar al administrador del cliente):")
    print(key)


if __name__ == "__main__":
    main()
