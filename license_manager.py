# license_manager.py - Validación de licencia por fecha (no manipulable por el usuario)
# La clave solo la puede proveer el desarrollador; la duración viene en la propia clave.
# Este módulo es autónomo: la app valida sin depender de generate_license_key.py (script solo para el administrador).
import json
import os
import hmac
import hashlib
from datetime import date
from typing import Optional, Tuple

LICENSE_FILE = "license.json"
# Formato de clave: YYYY-MM-DD-<HMAC_SHA256(YYYY-MM-DD, secret) en hex>
KEY_DATE_LEN = 10  # "YYYY-MM-DD"

# Secreto para verificar claves. Sin LICENSE_SECRET en entorno se usa este valor.
# El script generate_license_key.py importa _get_secret desde aquí para firmar con el mismo secreto.
_DEFAULT_LICENSE_SECRET = "ControlM-Search-License-YPF"


def _path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), LICENSE_FILE)


def _get_secret() -> str:
    """Secreto para firmar/verificar claves. Por defecto el de código; opcionalmente LICENSE_SECRET en entorno."""
    return (os.getenv("LICENSE_SECRET") or _DEFAULT_LICENSE_SECRET).strip()


def _sign(expiry_iso: str) -> str:
    """Firma HMAC-SHA256 de la fecha (solo quien tiene el secreto puede generarla)."""
    secret = _get_secret()
    if not secret:
        return ""
    return hmac.new(secret.encode("utf-8"), expiry_iso.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_license_key(key: str) -> Optional[date]:
    """
    Verifica que la clave sea válida y devuelve la fecha de expiración que lleva embebida.
    La clave tiene formato YYYY-MM-DD-<firma>. Solo el desarrollador puede generar claves válidas.
    """
    key = (key or "").strip()
    secret = _get_secret()
    if not secret:
        return None
    parts = key.split("-")
    # YYYY-MM-DD = 3 partes; la firma HMAC hex son 64 caracteres (una sola parte sin guiones)
    if len(parts) != 4:
        return None
    date_part = "-".join(parts[:3])
    sig_part = parts[3]
    if len(date_part) != KEY_DATE_LEN or len(sig_part) != 64:
        return None
    expected_sig = _sign(date_part)
    if not hmac.compare_digest(expected_sig, sig_part):
        return None
    try:
        return date.fromisoformat(date_part)
    except ValueError:
        return None


def load_license() -> dict:
    """Carga la licencia desde el archivo. Solo existe en el servidor."""
    path = _path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_license(license_key: str) -> bool:
    """
    Guarda la clave de licencia (no la fecha suelta).
    Así, la fecha de expiración se deriva siempre de la clave verificada;
    modificar el archivo no permite ampliar la validez.
    """
    try:
        path = _path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"license_key": license_key.strip()}, f, indent=2)
        return True
    except Exception:
        return False


def get_valid_until() -> Optional[str]:
    """
    Devuelve la fecha de expiración solo si existe una clave guardada y válida.
    No se confía en ningún campo 'valid_until' del archivo (evita manipulación).
    """
    data = load_license()
    key = (data.get("license_key") or "").strip()
    if not key:
        return None
    expiry = verify_license_key(key)
    return expiry.isoformat() if expiry else None


def is_license_valid() -> bool:
    """
    Comprueba si la licencia es válida según la fecha del servidor.
    La fecha se obtiene siempre verificando la clave guardada; modificar
    license.json no permite ampliar la expiración.
    """
    valid_until = get_valid_until()
    if not valid_until:
        return False
    try:
        end = date.fromisoformat(valid_until)
        return date.today() <= end
    except (ValueError, TypeError):
        return False


def activate_license(key: str) -> Tuple[bool, str]:
    """
    Activa la licencia usando una clave proporcionada por el desarrollador.
    Se guarda la clave (no la fecha); la expiración se deriva siempre de la clave.
    Modificar license.json no permite ampliar la validez.
    """
    expiry = verify_license_key(key)
    if expiry is None:
        return False, "Clave de licencia inválida o corrupta. Solo el desarrollador puede proporcionar claves válidas."
    valid_until = expiry.isoformat()
    if save_license(key):
        return True, f"Licencia activada hasta el {valid_until}."
    return False, "No se pudo guardar la licencia."
