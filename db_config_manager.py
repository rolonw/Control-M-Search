# db_config_manager.py - Gestión de configuración persistente de BD
import json
import os
from typing import Dict, Optional

CONFIG_FILE = "db_config.json"


def load_config() -> Dict:
    """Carga la configuración desde el archivo JSON."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Configuración por defecto (Oracle)
    return {
        "db_type": "oracle",
        "ems": {
            "host": "oradb",
            "port": 1521,
            "service_name": "orcl",
            "sid": "",
            "tns": "",
            "user": "CTMEMS919WIN",
            "password": "Passw0rd",
            "database": "",
            "driver": "",
        },
        "ctm": {
            "host": "oradb",
            "port": 1521,
            "service_name": "orcl",
            "sid": "",
            "tns": "",
            "user": "CTMSRV919WIN",
            "password": "Passw0rd",
            "database": "",
            "driver": "",
        },
    }


def save_config(config: Dict) -> tuple[bool, Optional[str]]:
    """Guarda la configuración en el archivo JSON. Retorna (éxito, mensaje_error)."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True, None
    except PermissionError as e:
        return False, "Sin permiso de escritura. En Docker, monte db_config.json sin :ro para poder guardar desde /admin."
    except OSError as e:
        if getattr(e, "errno", None) == 30:  # Read-only file system
            return False, "Archivo de solo lectura. En Docker, monte el volumen sin :ro."
        return False, str(e)
    except Exception as e:
        return False, str(e)


def get_config() -> Dict:
    """Obtiene la configuración actual."""
    return load_config()


def update_config(db_type: str, ems_config: Dict, ctm_config: Dict) -> tuple[bool, Optional[str]]:
    """Actualiza la configuración completa. Retorna (éxito, mensaje_error)."""
    config = {
        "db_type": db_type.lower(),
        "ems": ems_config,
        "ctm": ctm_config,
    }
    return save_config(config)
