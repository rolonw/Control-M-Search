# odbc_utils.py - Utilidades para detectar drivers ODBC
import pyodbc

def get_available_odbc_drivers():
    """Obtiene la lista de drivers ODBC disponibles."""
    try:
        return pyodbc.drivers()
    except Exception:
        return []


def get_sql_server_drivers():
    """Obtiene solo los drivers de SQL Server disponibles."""
    drivers = get_available_odbc_drivers()
    return [d for d in drivers if 'SQL Server' in d]


def get_default_sql_server_driver():
    """Obtiene el driver de SQL Server por defecto o el primero disponible."""
    sql_drivers = get_sql_server_drivers()
    if not sql_drivers:
        return None
    
    # Priorizar drivers más recientes
    preferred = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "SQL Server Native Client 11.0",
    ]
    
    for pref in preferred:
        if pref in sql_drivers:
            return pref
    
    # Si no hay preferido, devolver el primero
    return sql_drivers[0]
