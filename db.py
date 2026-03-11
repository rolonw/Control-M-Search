# db.py - Acceso a base de datos con SQLAlchemy (Oracle, MSSQL, PostgreSQL)
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy import event

from config import get_db_type, get_ems_sqlalchemy_url, get_ctm_sqlalchemy_url


def _to_unicode(v):
    """Convierte un valor de BD a str UTF-8. Evita errores 'ascii codec can't decode' (p. ej. ó, ñ en PostgreSQL)."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, memoryview):
        return bytes(v).decode("utf-8", errors="replace")
    try:
        return str(v)
    except Exception:
        return ""

# Motores SQLAlchemy (se crean bajo demanda para usar la config actual)
_engine_ems: "Engine | None" = None
_engine_ctm: "Engine | None" = None


def reset_engines() -> None:
    """Invalida los motores para que se recreen con la config actual (p. ej. tras guardar en /admin)."""
    global _engine_ems, _engine_ctm
    if _engine_ems is not None:
        _engine_ems.dispose()
    if _engine_ctm is not None:
        _engine_ctm.dispose()
    _engine_ems = None
    _engine_ctm = None


def _pg_set_encoding(dbapi_connection, connection_record):
    """Fuerza UTF-8 en conexiones PostgreSQL para evitar 'ascii codec can't decode byte 0xf3'."""
    if hasattr(dbapi_connection, "set_client_encoding"):
        dbapi_connection.set_client_encoding("UTF8")


def _get_engine_ems() -> Engine:
    global _engine_ems
    if _engine_ems is None:
        url = get_ems_sqlalchemy_url()
        kwargs = {"pool_pre_ping": True, "pool_recycle": 300}
        # Oracle (oracledb) no acepta 'encoding' en connect(); PostgreSQL sí usa client_encoding
        if url.startswith("postgresql"):
            kwargs["connect_args"] = {"options": "-c client_encoding=UTF8"}
        _engine_ems = create_engine(url, **kwargs)
        if url.startswith("postgresql"):
            event.listen(_engine_ems, "connect", _pg_set_encoding)
    return _engine_ems


def _get_engine_ctm() -> Engine:
    global _engine_ctm
    if _engine_ctm is None:
        url = get_ctm_sqlalchemy_url()
        kwargs = {"pool_pre_ping": True, "pool_recycle": 300}
        # Oracle (oracledb) no acepta 'encoding' en connect(); PostgreSQL sí usa client_encoding
        if url.startswith("postgresql"):
            kwargs["connect_args"] = {"options": "-c client_encoding=UTF8"}
        _engine_ctm = create_engine(url, **kwargs)
        if url.startswith("postgresql"):
            event.listen(_engine_ctm, "connect", _pg_set_encoding)
    return _engine_ctm


def _run_query(engine: Engine, sql: str, params: dict | list | None = None) -> list[dict]:
    """Ejecuta una consulta SELECT y devuelve lista de dicts (columnas como keys). Valores en UTF-8 str."""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = result.keys()
        rows = result.fetchall()
        return [
            {c: _to_unicode(val) for c, val in zip(columns, row)}
            for row in rows
        ]


def _run_execute(engine: Engine, sql: str, params: dict | list | None = None) -> None:
    """Ejecuta UPDATE/INSERT/DELETE y hace commit."""
    with engine.connect() as conn:
        conn.execute(text(sql), params or {})
        conn.commit()


def get_data(sql: str, params: dict | list | None = None) -> list[dict]:
    return _run_query(_get_engine_ems(), sql, params)


def get_data_ctm(sql: str, params: dict | None = None) -> list[dict]:
    return _run_query(_get_engine_ctm(), sql, params)


def execute_ems(sql: str, params: dict | list | None = None) -> None:
    _run_execute(_get_engine_ems(), sql, params)


def get_combo_values(sql: str) -> list[str]:
    """Para llenar combos: APPLICATION, GROUP_NAME, NODE_ID. Valores ya en UTF-8."""
    rows = get_data(sql)
    return [_to_unicode(list(r.values())[0]) for r in rows]


# --- Consultas principales (DataJob)
def query_by_application(app: str) -> list[dict]:
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID WHERE J.APPLICATION = :app",
        {"app": app},
    )


def query_by_group(grp: str) -> list[dict]:
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID WHERE J.GROUP_NAME = :grp",
        {"grp": grp},
    )


def query_by_node_id(node_id: str, all_fields: bool = False) -> list[dict]:
    like = f"%{node_id}%"
    if all_fields:
        return get_data(
            "SELECT J.*, T.USER_DAILY FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
            "WHERE J.NODE_ID LIKE :lik",
            {"lik": like},
        )
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID WHERE J.NODE_ID LIKE :lik",
        {"lik": like},
    )


def query_by_jobname(jobname: str, all_fields: bool = False) -> list[dict]:
    like = f"%{jobname}%"
    if all_fields:
        return get_data(
            "SELECT J.*, T.* FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
            "WHERE J.JOB_NAME LIKE :lik",
            {"lik": like},
        )
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID WHERE J.JOB_NAME LIKE :lik",
        {"lik": like},
    )


def query_by_description(desc: str) -> list[dict]:
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "WHERE J.DESCRIPTION LIKE :lik ORDER BY J.MEMNAME",
        {"lik": f"%{desc}%"},
    )


def query_by_tables(tbl: str, all_fields: bool = False) -> list[dict]:
    like = f"%{tbl}%"
    if all_fields:
        return get_data(
            "SELECT J.*, T.* FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
            "WHERE T.SCHED_TABLE LIKE :lik",
            {"lik": like},
        )
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID WHERE J.PARENT_TABLE LIKE :lik",
        {"lik": like},
    )


def query_in_condition(cond: str) -> list[dict]:
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, J.MEMNAME AS SCRIPT, "
        "I.CONDITION AS IN_CONDITION, I.ODATE, I.AND_OR "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_LNKI_P I ON J.TABLE_ID = I.TABLE_ID AND J.JOB_ID = I.JOB_ID "
        "WHERE I.CONDITION LIKE :lik",
        {"lik": f"%{cond}%"},
    )


def query_in_condition_jobname(jobname: str) -> list[dict]:
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, J.MEMNAME AS SCRIPT, "
        "I.CONDITION AS IN_CONDITION, I.ODATE, I.AND_OR "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_LNKI_P I ON J.TABLE_ID = I.TABLE_ID AND J.JOB_ID = I.JOB_ID "
        "WHERE I.CONDITION LIKE :lik",
        {"lik": f"%{jobname}%"},
    )


def query_out_condition(cond: str) -> list[dict]:
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, J.MEMNAME AS SCRIPT, "
        "O.CONDITION AS OUT_CONDITION, O.ODATE, O.SIGN "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_LNKO_P O ON J.TABLE_ID = O.TABLE_ID AND J.JOB_ID = O.JOB_ID "
        "WHERE O.CONDITION LIKE :lik",
        {"lik": f"%{cond}%"},
    )


def query_out_condition_jobname(jobname: str) -> list[dict]:
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, J.MEMNAME AS SCRIPT, "
        "O.CONDITION AS OUT_CONDITION, O.ODATE, O.SIGN "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_LNKO_P O ON J.TABLE_ID = O.TABLE_ID AND J.JOB_ID = O.JOB_ID "
        "WHERE J.MEMNAME LIKE :lik",
        {"lik": f"%{jobname}%"},
    )


def query_estadisticas(job_mem: str) -> list[dict]:
    like = f"%{job_mem}%"
    db_type = get_db_type()
    if db_type == "oracle":
        return get_data(
            "SELECT JOB_MEM_NAME AS JOB, START_TIME AS INICIO, END_TIME AS FIN, "
            "TO_CHAR(TRUNC(RUN_TIME_SEC / 3600), 'FM00') || ':' || "
            "TO_CHAR(TRUNC(MOD(RUN_TIME_SEC, 3600) / 60), 'FM00') || ':' || "
            "TO_CHAR(MOD(RUN_TIME_SEC, 60), 'FM00') AS DURACION, "
            "GROUP_NAME AS APLICACION, NODE_ID AS SERVIDOR, "
            "CASE ENDED_STATUS WHEN 16 THEN 'Ended OK' WHEN 32 THEN 'Ended Not OK' ELSE 'Estado no conocido' END AS END_STATUS "
            "FROM RUNINFO_HISTORY WHERE JOB_MEM_NAME LIKE :lik ORDER BY START_TIME DESC",
            {"lik": like},
        )
    elif db_type == "mssql":
        return get_data(
            "SELECT JOB_MEM_NAME AS JOB, START_TIME AS INICIO, END_TIME AS FIN, "
            "CONVERT(varchar, DATEADD(SECOND, RUN_TIME_SEC, 0),108) AS DURACION, "
            "GROUP_NAME AS APLICACION, NODE_ID AS SERVIDOR, "
            "case ENDED_STATUS when 16 then 'Ended OK' when 32 then 'Ended Not OK' else 'Estado no conoicido' end as END_STATUS "
            "FROM RUNINFO_HISTORY WHERE JOB_MEM_NAME LIKE :lik ORDER BY START_TIME DESC",
            {"lik": like},
        )
    elif db_type == "postgresql":
        return get_data(
            "SELECT JOB_MEM_NAME AS JOB, START_TIME AS INICIO, END_TIME AS FIN, "
            "TO_CHAR((RUN_TIME_SEC || ' second')::interval, 'HH24:MI:SS') AS DURACION, "
            "GROUP_NAME AS APLICACION, NODE_ID AS SERVIDOR, "
            "CASE ENDED_STATUS WHEN 16 THEN 'Ended OK' WHEN 32 THEN 'Ended Not OK' ELSE 'Estado no conocido' END AS END_STATUS "
            "FROM RUNINFO_HISTORY WHERE JOB_MEM_NAME LIKE :lik ORDER BY START_TIME DESC",
            {"lik": like},
        )
    else:
        raise ValueError(f"Tipo de BD no soportado: {db_type}")


def query_script_cmdline(text_search: str) -> list[dict]:
    like = f"%{text_search}%"
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.CMD_LINE, J.DESCRIPTION, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME "
        "FROM DEF_JOB J JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "WHERE J.MEMNAME LIKE :lik OR J.CMD_LINE LIKE :lik2",
        {"lik": like, "lik2": like},
    )


def query_variables(var_text: str) -> list[dict]:
    like = f"%{var_text}%"
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, S.NAME AS VAR_NAME, S.VALUE "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.JOB_ID = S.JOB_ID AND J.TABLE_ID = S.TABLE_ID "
        "WHERE S.NAME LIKE :lik OR S.VALUE LIKE :lik2 ORDER BY S.NAME DESC",
        {"lik": like, "lik2": like},
    )


def query_node_groups() -> list[dict]:
    return get_data_ctm("SELECT GRPNAME, NODEID FROM CMS_NODGRP ORDER BY 1")


def query_variables_globales(var_name: str) -> list[dict]:
    if get_db_type() == "postgresql":
        return get_data_ctm(
            "SELECT var, varexpr FROM cmr_setvar WHERE var LIKE :lik ORDER BY var DESC",
            {"lik": f"%{var_name}%"},
        )
    return get_data_ctm(
        "SELECT VAR, VAREXPR FROM CMR_SETVAR WHERE VAR LIKE :lik ORDER BY VAR DESC",
        {"lik": f"%{var_name}%"},
    )


def unlock_tables(table_unlock: str) -> list[dict]:
    """Consulta relacionada con desbloqueo de tablas. Adaptar SQL según el motor de BD si es necesario."""
    # Placeholder: devolver resultado vacío o consulta genérica según tu esquema
    return get_data(
        "SELECT :tab AS table_name FROM DEF_JOB WHERE 1=0",
        {"tab": table_unlock},
    )


# --- Consultas avanzadas (AFT, SAP, BW, OS400)
def query_aft_jobname(text_search: str) -> list[dict]:
    return get_data(
        "SELECT J.PARENT_TABLE, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, S.NAME, S.VALUE "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "WHERE S.NAME LIKE '%FTP-%PATH%' AND J.JOB_NAME LIKE :lik",
        {"lik": f"%{text_search}%"},
    )


def query_aft_origendestino(text_search: str) -> list[dict]:
    return get_data(
        "SELECT J.PARENT_TABLE, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, S.NAME, S.VALUE "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "WHERE S.NAME LIKE '%FTP-%PATH%' AND S.VALUE LIKE :lik",
        {"lik": f"%{text_search}%"},
    )


def query_sap_jobname_cm(text_search: str) -> list[dict]:
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "J.NODE_ID, S.VALUE AS CMD_LINE, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "WHERE S.NAME LIKE '%SAPR3-JOBNAME%' AND J.JOB_NAME LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text_search}%"},
    )


def query_sap_jobname_r3(text_search: str) -> list[dict]:
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "J.NODE_ID, S.VALUE AS CMD_LINE, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "WHERE S.NAME LIKE '%SAPR3-JOBNAME%' AND S.VALUE LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text_search}%"},
    )


def query_bw_controlm(text_search: str) -> list[dict]:
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "S.VALUE AS CMD_LINE, J.NODE_ID, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "WHERE S.NAME LIKE '%SAPR3-ProcessChain_ID%' AND J.JOB_NAME LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text_search}%"},
    )


def query_bw_cadena_procesos(text_search: str) -> list[dict]:
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "S.VALUE AS CMD_LINE, J.NODE_ID, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "WHERE S.NAME LIKE '%SAPR3-ProcessChain_ID%' AND S.VALUE LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text_search}%"},
    )


def query_os400_cmdline(text_search: str) -> list[dict]:
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "J.NODE_ID, S.VALUE AS CMD_LINE, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "WHERE S.VALUE LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text_search}%"},
    )


def query_os400_jobname_cm(text_search: str) -> list[dict]:
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "J.NODE_ID, S.VALUE AS CMD_LINE, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J INNER JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "INNER JOIN DEF_SETVAR S ON J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "WHERE S.NAME LIKE '%OS400-CMDLINE1%' AND J.JOB_NAME LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text_search}%"},
    )
