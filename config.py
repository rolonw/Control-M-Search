# config.py - Configuración de la aplicación (SQLAlchemy)
import re
from urllib.parse import quote_plus

from db_config_manager import load_config


def _oracle_dsn_for_thin_mode(dsn: str) -> str:
    """
    python-oracledb en modo thin no soporta BEQUEATH (DPY-3001).
    Sustituir SERVER=BEQUEATH por SERVER=DEDICATED.
    """
    if not dsn or not dsn.strip():
        return dsn
    return re.sub(r"\(SERVER\s*=\s*BEQUEATH\)", "(SERVER=DEDICATED)", dsn.strip(), flags=re.IGNORECASE)


def _oracle_dsn_from_tns(tns: str, host: str, port: int, service_name: str, sid: str) -> str:
    """
    Construye el DSN para oracledb (modo thin) sin usar tnsnames.ora (evita DPY-4027).
    - Si tns está vacío: Easy Connect con host:port/service_name o host:port:sid.
    - Si tns contiene un descriptor (DESCRIPTION/ADDRESS): se extrae y se usa (sin alias).
    - Si tns es solo un alias (ej. "ORCL"): se ignora y se usa Easy Connect (no hay config_dir).
    """
    tns = (tns or "").strip()
    if not tns:
        if service_name:
            return f"{host}:{port}/{service_name}"
        if sid:
            return f"{host}:{port}:{sid}"
        return f"{host}:{port}/orcl"
    # Descriptor completo: extraer desde el primer '(' (quitar "ALIAS = ")
    if "(DESCRIPTION" in tns.upper() or "(ADDRESS" in tns.upper():
        idx = tns.find("(")
        if idx >= 0:
            descriptor = tns[idx:].strip()
            return _oracle_dsn_for_thin_mode(descriptor)
    # Es un alias simple: no usarlo (requeriría config_dir). Usar Easy Connect.
    if service_name:
        return f"{host}:{port}/{service_name}"
    if sid:
        return f"{host}:{port}:{sid}"
    return f"{host}:{port}/orcl"


def _get_sql_server_driver(driver_from_config: str):
    """Driver ODBC para SQL Server. Usa el config o detecta uno por defecto."""
    driver = (driver_from_config or "").strip()
    if not driver:
        from odbc_utils import get_default_sql_server_driver
        driver = get_default_sql_server_driver()
    if not driver:
        raise ValueError("No se encontró ningún driver ODBC para SQL Server instalado")
    return driver


def get_ems_sqlalchemy_url() -> str:
    """URL de conexión SQLAlchemy para la base de datos EMS (lee config actual)."""
    cfg = load_config()
    db_type = cfg.get("db_type", "oracle").lower()
    ems = cfg.get("ems", {})
    user = quote_plus(ems.get("user", "CTMEMS919WIN"))
    password = quote_plus(ems.get("password", "Passw0rd"))
    host = ems.get("host", "oradb")
    port = ems.get("port", 1521)
    if db_type == "oracle":
        service_name = ems.get("service_name", "orcl") or ""
        sid = ems.get("sid", "") or ""
        tns = ems.get("tns", "").strip()
        dsn = _oracle_dsn_from_tns(tns, host, port, service_name, sid)
        return f"oracle+oracledb://{user}:{password}@{dsn}"
    elif db_type == "mssql":
        driver = _get_sql_server_driver(ems.get("driver", ""))
        driver_encoded = quote_plus(driver)
        database = ems.get("database") or "master"
        return f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver={driver_encoded}"
    elif db_type == "postgresql":
        database = ems.get("database") or "postgres"
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Tipo de BD no soportado: {db_type}")


def get_ctm_sqlalchemy_url() -> str:
    """URL de conexión SQLAlchemy para la base de datos CTM (lee config actual)."""
    cfg = load_config()
    db_type = cfg.get("db_type", "oracle").lower()
    ctm = cfg.get("ctm", {})
    user = quote_plus(ctm.get("user", "CTMSRV919WIN"))
    password = quote_plus(ctm.get("password", "Passw0rd"))
    host = ctm.get("host", "oradb")
    port = ctm.get("port", 1521)
    if db_type == "oracle":
        service_name = ctm.get("service_name", "orcl") or ""
        sid = ctm.get("sid", "") or ""
        tns = ctm.get("tns", "").strip()
        dsn = _oracle_dsn_from_tns(tns, host, port, service_name, sid)
        return f"oracle+oracledb://{user}:{password}@{dsn}"
    elif db_type == "mssql":
        driver = _get_sql_server_driver(ctm.get("driver", ""))
        driver_encoded = quote_plus(driver)
        database = ctm.get("database") or "master"
        return f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver={driver_encoded}"
    elif db_type == "postgresql":
        database = ctm.get("database") or "postgres"
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"Tipo de BD no soportado: {db_type}")


# Para compatibilidad: DB_TYPE y variables usadas por app (about, etc.)
def _config() -> dict:
    return load_config()


def get_db_type() -> str:
    return _config().get("db_type", "oracle").lower()


# Exportar como DB_TYPE para que el resto del código no cambie
_db = _config()
DB_TYPE = _db.get("db_type", "oracle").lower()
