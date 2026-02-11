# config.py - Configuración de la aplicación
import os
import re
from dotenv import load_dotenv
from db_config_manager import load_config
from odbc_utils import get_default_sql_server_driver

load_dotenv()


def _oracle_dsn_for_thin_mode(dsn: str) -> str:
    """
    python-oracledb en modo thin no soporta BEQUEATH (DPY-3001).
    Sustituir SERVER=BEQUEATH por SERVER=DEDICATED para que la conexión funcione sin Oracle Client.
    """
    if not dsn or not dsn.strip():
        return dsn
    return re.sub(r"\(SERVER\s*=\s*BEQUEATH\)", "(SERVER=DEDICATED)", dsn.strip(), flags=re.IGNORECASE)

# Cargar configuración persistente
_db_config = load_config()
DB_TYPE = _db_config.get("db_type", "oracle").lower()

# Configuración EMS
_ems_config = _db_config.get("ems", {})
EMS_HOST = _ems_config.get("host", "oradb")
EMS_PORT = _ems_config.get("port", 1521)
EMS_SERVICE_NAME = _ems_config.get("service_name", "orcl")
EMS_SID = _ems_config.get("sid", "")
EMS_TNS = _ems_config.get("tns", "")
EMS_USER = _ems_config.get("user", "CTMEMS919WIN")
EMS_PASSWORD = _ems_config.get("password", "Passw0rd")
EMS_DATABASE = _ems_config.get("database", "")  # Para MSSQL/PostgreSQL
EMS_DRIVER = _ems_config.get("driver", "")  # Para MSSQL

# Configuración CTM
_ctm_config = _db_config.get("ctm", {})
CTM_HOST = _ctm_config.get("host", "oradb")
CTM_PORT = _ctm_config.get("port", 1521)
CTM_SERVICE_NAME = _ctm_config.get("service_name", "orcl")
CTM_SID = _ctm_config.get("sid", "")
CTM_TNS = _ctm_config.get("tns", "")
CTM_USER = _ctm_config.get("user", "CTMSRV919WIN")
CTM_PASSWORD = _ctm_config.get("password", "Passw0rd")
CTM_DATABASE = _ctm_config.get("database", "")  # Para MSSQL/PostgreSQL
CTM_DRIVER = _ctm_config.get("driver", "")  # Para MSSQL


def get_ems_connect_params():
    """Parámetros de conexión para EMS según el tipo de BD."""
    if DB_TYPE == "oracle":
        dsn = EMS_TNS.strip() if EMS_TNS else (
            f"{EMS_HOST}:{EMS_PORT}/{EMS_SERVICE_NAME}" if EMS_SERVICE_NAME
            else f"{EMS_HOST}:{EMS_PORT}:{EMS_SID}" if EMS_SID
            else f"{EMS_HOST}:{EMS_PORT}/orcl"
        )
        dsn = _oracle_dsn_for_thin_mode(dsn)
        return {
            "user": EMS_USER,
            "password": EMS_PASSWORD,
            "dsn": dsn,
        }
    elif DB_TYPE == "mssql":
        # Usar driver configurado o detectar uno automáticamente
        driver = EMS_DRIVER.strip() if EMS_DRIVER else get_default_sql_server_driver()
        if not driver:
            raise ValueError("No se encontró ningún driver ODBC para SQL Server instalado")
        return {
            "server": EMS_HOST,
            "port": EMS_PORT,
            "database": EMS_DATABASE or "master",
            "user": EMS_USER,
            "password": EMS_PASSWORD,
            "driver": driver,
        }
    elif DB_TYPE == "postgresql":
        return {
            "host": EMS_HOST,
            "port": EMS_PORT,
            "database": EMS_DATABASE or "postgres",
            "user": EMS_USER,
            "password": EMS_PASSWORD,
        }
    else:
        raise ValueError(f"Tipo de BD no soportado: {DB_TYPE}")


def get_ctm_connect_params():
    """Parámetros de conexión para CTM según el tipo de BD."""
    if DB_TYPE == "oracle":
        dsn = CTM_TNS.strip() if CTM_TNS else (
            f"{CTM_HOST}:{CTM_PORT}/{CTM_SERVICE_NAME}" if CTM_SERVICE_NAME
            else f"{CTM_HOST}:{CTM_PORT}:{CTM_SID}" if CTM_SID
            else f"{CTM_HOST}:{CTM_PORT}/orcl"
        )
        dsn = _oracle_dsn_for_thin_mode(dsn)
        return {
            "user": CTM_USER,
            "password": CTM_PASSWORD,
            "dsn": dsn,
        }
    elif DB_TYPE == "mssql":
        # Usar driver configurado o detectar uno automáticamente
        driver = CTM_DRIVER.strip() if CTM_DRIVER else get_default_sql_server_driver()
        if not driver:
            raise ValueError("No se encontró ningún driver ODBC para SQL Server instalado")
        return {
            "server": CTM_HOST,
            "port": CTM_PORT,
            "database": CTM_DATABASE or "master",
            "user": CTM_USER,
            "password": CTM_PASSWORD,
            "driver": driver,
        }
    elif DB_TYPE == "postgresql":
        return {
            "host": CTM_HOST,
            "port": CTM_PORT,
            "database": CTM_DATABASE or "postgres",
            "user": CTM_USER,
            "password": CTM_PASSWORD,
        }
    else:
        raise ValueError(f"Tipo de BD no soportado: {DB_TYPE}")


# Compatibilidad: cadena única (solo Oracle)
def get_ems_connect_string():
    if DB_TYPE != "oracle":
        raise ValueError("get_ems_connect_string() solo funciona con Oracle")
    p = get_ems_connect_params()
    return f"{p['user']}/{p['password']}@{p['dsn']}"


def get_ctm_connect_string():
    if DB_TYPE != "oracle":
        raise ValueError("get_ctm_connect_string() solo funciona con Oracle")
    p = get_ctm_connect_params()
    return f"{p['user']}/{p['password']}@{p['dsn']}"
