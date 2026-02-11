# db.py - Acceso a base de datos (Oracle, MSSQL, PostgreSQL)
from config import DB_TYPE, get_ems_connect_params, get_ctm_connect_params

# Importar drivers según el tipo de BD
if DB_TYPE == "oracle":
    import oracledb as db_driver
elif DB_TYPE == "mssql":
    import pyodbc as db_driver
elif DB_TYPE == "postgresql":
    import psycopg2 as db_driver
else:
    raise ValueError(f"Tipo de BD no soportado: {DB_TYPE}")


def _run_query(connect_params, sql, params=None):
    """Ejecuta una consulta y devuelve lista de dicts (columnas como keys)."""
    if DB_TYPE == "oracle":
        conn = db_driver.connect(**connect_params)
        try:
            cur = conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            columns = [c[0] for c in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()
    elif DB_TYPE == "mssql":
        # pyodbc usa connection string
        conn_str = (
            f"DRIVER={{{connect_params['driver']}}};"
            f"SERVER={connect_params['server']},{connect_params['port']};"
            f"DATABASE={connect_params['database']};"
            f"UID={connect_params['user']};"
            f"PWD={connect_params['password']}"
        )
        conn = db_driver.connect(conn_str)
        try:
            cur = conn.cursor()
            if params:
                # pyodbc usa ? como placeholder, convertir :nombre a ?
                import re
                sql_mssql = sql
                if isinstance(params, dict):
                    param_list = []
                    for key, value in params.items():
                        sql_mssql = sql_mssql.replace(f":{key}", "?", 1)
                        param_list.append(value)
                else:
                    sql_mssql = re.sub(r":\w+", "?", sql)
                    param_list = params
                cur.execute(sql_mssql, param_list)
            else:
                cur.execute(sql)
            columns = [col[0] for col in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()
    elif DB_TYPE == "postgresql":
        conn = db_driver.connect(**connect_params)
        try:
            cur = conn.cursor()
            if params:
                # psycopg2 usa %s como placeholder, convertir :nombre a %s
                sql_psql = sql
                if isinstance(params, dict):
                    # Reemplazar placeholders nombrados por %s y mantener orden
                    param_list = []
                    import re
                    for key, value in params.items():
                        sql_psql = sql_psql.replace(f":{key}", "%s", 1)
                        param_list.append(value)
                else:
                    # Ya es una lista, solo reemplazar : por %s
                    sql_psql = re.sub(r":\w+", "%s", sql)
                    param_list = params
                cur.execute(sql_psql, param_list)
            else:
                cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()


def _run_execute(connect_params, sql, params=None):
    """Ejecuta UPDATE/INSERT/DELETE y hace commit."""
    if DB_TYPE == "oracle":
        conn = db_driver.connect(**connect_params)
        try:
            cur = conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            conn.commit()
        finally:
            conn.close()
    elif DB_TYPE == "mssql":
        conn_str = (
            f"DRIVER={{{connect_params['driver']}}};"
            f"SERVER={connect_params['server']},{connect_params['port']};"
            f"DATABASE={connect_params['database']};"
            f"UID={connect_params['user']};"
            f"PWD={connect_params['password']}"
        )
        conn = db_driver.connect(conn_str)
        try:
            cur = conn.cursor()
            if params:
                import re
                sql_mssql = sql
                if isinstance(params, dict):
                    param_list = []
                    for key, value in params.items():
                        sql_mssql = sql_mssql.replace(f":{key}", "?", 1)
                        param_list.append(value)
                else:
                    sql_mssql = re.sub(r":\w+", "?", sql)
                    param_list = params
                cur.execute(sql_mssql, param_list)
            else:
                cur.execute(sql)
            conn.commit()
        finally:
            conn.close()
    elif DB_TYPE == "postgresql":
        conn = db_driver.connect(**connect_params)
        try:
            cur = conn.cursor()
            if params:
                sql_psql = sql
                if isinstance(params, dict):
                    import re
                    param_list = []
                    for key, value in params.items():
                        sql_psql = sql_psql.replace(f":{key}", "%s", 1)
                        param_list.append(value)
                else:
                    import re
                    sql_psql = re.sub(r":\w+", "%s", sql)
                    param_list = params
                cur.execute(sql_psql, param_list)
            else:
                cur.execute(sql)
            conn.commit()
        finally:
            conn.close()


def get_data(sql, params=None):
    return _run_query(get_ems_connect_params(), sql, params)


def get_data_ctm(sql, params=None):
    return _run_query(get_ctm_connect_params(), sql, params)


def execute_ems(sql, params=None):
    _run_execute(get_ems_connect_params(), sql, params)


def get_combo_values(sql):
    """Para llenar combos: APPLICATION, GROUP_NAME, NODE_ID."""
    rows = get_data(sql)
    return [str(list(r.values())[0]) for r in rows]


# --- Consultas principales (DataJob)
def query_by_application(app):
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T WHERE J.TABLE_ID = T.TABLE_ID AND J.APPLICATION=:app",
        {"app": app},
    )


def query_by_group(grp):
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T WHERE J.TABLE_ID = T.TABLE_ID AND J.GROUP_NAME=:grp",
        {"grp": grp},
    )


def query_by_node_id(node_id, all_fields=False):
    like = f"%{node_id}%"
    if all_fields:
        return get_data(
            "SELECT J.*, T.USER_DAILY FROM DEF_JOB J, DEF_TABLES T "
            "WHERE J.TABLE_ID = T.TABLE_ID AND J.NODE_ID LIKE :lik",
            {"lik": like},
        )
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T WHERE J.TABLE_ID = T.TABLE_ID AND J.NODE_ID LIKE :lik",
        {"lik": like},
    )


def query_by_jobname(jobname, all_fields=False):
    like = f"%{jobname}%"
    if all_fields:
        return get_data(
            "SELECT J.*, T.* FROM DEF_JOB J, DEF_TABLES T "
            "WHERE J.TABLE_ID = T.TABLE_ID AND J.JOB_NAME LIKE :lik",
            {"lik": like},
        )
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T WHERE J.TABLE_ID = T.TABLE_ID AND J.JOB_NAME LIKE :lik",
        {"lik": like},
    )


def query_by_description(desc):
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_TABLES T, DEF_JOB J WHERE J.TABLE_ID = T.TABLE_ID AND J.DESCRIPTION LIKE :lik ORDER BY J.MEMNAME",
        {"lik": f"%{desc}%"},
    )


def query_by_tables(tbl, all_fields=False):
    like = f"%{tbl}%"
    if all_fields:
        return get_data(
            "SELECT DEF_JOB.*, DEF_TABLES.* FROM DEF_JOB, DEF_TABLES "
            "WHERE DEF_JOB.TABLE_ID = DEF_TABLES.TABLE_ID AND DEF_TABLES.SCHED_TABLE LIKE :lik",
            {"lik": like},
        )
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.DESCRIPTION, J.CMD_LINE, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T WHERE J.TABLE_ID = T.TABLE_ID AND J.PARENT_TABLE LIKE :lik",
        {"lik": like},
    )


def query_in_condition(cond):
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, J.MEMNAME AS SCRIPT, "
        "I.CONDITION AS IN_CONDITION, I.ODATE, I.AND_OR "
        "FROM DEF_TABLES T, DEF_JOB J, DEF_LNKI_P I "
        "WHERE T.TABLE_ID = J.TABLE_ID AND T.TABLE_ID = I.TABLE_ID AND J.JOB_ID = I.JOB_ID AND I.CONDITION LIKE :lik",
        {"lik": f"%{cond}%"},
    )


def query_in_condition_jobname(jobname):
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, J.MEMNAME AS SCRIPT, "
        "I.CONDITION AS IN_CONDITION, I.ODATE, I.AND_OR "
        "FROM DEF_TABLES T, DEF_JOB J, DEF_LNKI_P I "
        "WHERE T.TABLE_ID = J.TABLE_ID AND T.TABLE_ID = I.TABLE_ID AND J.JOB_ID = I.JOB_ID AND I.CONDITION LIKE :lik",
        {"lik": f"%{jobname}%"},
    )


def query_out_condition(cond):
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, J.MEMNAME AS SCRIPT, "
        "O.CONDITION AS OUT_CONDITION, O.ODATE, O.SIGN "
        "FROM DEF_TABLES T, DEF_JOB J, DEF_LNKO_P O "
        "WHERE T.TABLE_ID = J.TABLE_ID AND T.TABLE_ID = O.TABLE_ID AND J.JOB_ID = O.JOB_ID AND O.CONDITION LIKE :lik",
        {"lik": f"%{cond}%"},
    )


def query_out_condition_jobname(jobname):
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, J.MEMNAME AS SCRIPT, "
        "O.CONDITION AS OUT_CONDITION, O.ODATE, O.SIGN "
        "FROM DEF_TABLES T, DEF_JOB J, DEF_LNKO_P O "
        "WHERE T.TABLE_ID = J.TABLE_ID AND T.TABLE_ID = O.TABLE_ID AND J.JOB_ID = O.JOB_ID AND J.MEMNAME LIKE :lik",
        {"lik": f"%{jobname}%"},
    )


def query_estadisticas(job_mem):
    if DB_TYPE == "oracle":
        return get_data(
        "SELECT JOB_MEM_NAME AS JOB, START_TIME AS INICIO, END_TIME AS FIN, "
        "TO_CHAR(TRUNC(RUN_TIME_SEC / 3600), 'FM00') || ':' || "
        "TO_CHAR(TRUNC(MOD(RUN_TIME_SEC, 3600) / 60), 'FM00') || ':' || "
        "TO_CHAR(MOD(RUN_TIME_SEC, 60), 'FM00') AS DURACION, "
        "GROUP_NAME AS APLICACION, NODE_ID AS SERVIDOR, "
        "CASE ENDED_STATUS WHEN 16 THEN 'Ended OK' WHEN 32 THEN 'Ended Not OK' ELSE 'Estado no conocido' END AS END_STATUS "
        "FROM RUNINFO_HISTORY WHERE JOB_MEM_NAME LIKE :lik ORDER BY START_TIME DESC",
        {"lik": f"%{job_mem}%"},
        )
    elif DB_TYPE == "mssql":
        return get_data(
        "SELECT JOB_MEM_NAME AS JOB, START_TIME AS INICIO, END_TIME AS FIN, "
        "CONVERT(varchar, DATEADD(SECOND, RUN_TIME_SEC, 0),108) AS DURACION, "
        "GROUP_NAME AS APLICACION, NODE_ID AS SERVIDOR, "
        "case ENDED_STATUS when 16 then 'Ended OK' when 32 then 'Ended Not OK' else 'Estado no conoicido' end as END_STATUS "
        "FROM RUNINFO_HISTORY WHERE JOB_MEM_NAME LIKE :lik ORDER BY START_TIME DESC",
        {"lik": f"%{job_mem}%"},
        )
    elif DB_TYPE == "postgresql":
        return get_data(
        "SELECT JOB_MEM_NAME AS JOB, START_TIME AS INICIO, END_TIME AS FIN, "
        "TO_CHAR((RUN_TIME_SEC || ' second')::interval, 'HH24:MI:SS') AS DURACION, "
        "GROUP_NAME AS APLICACION, NODE_ID AS SERVIDOR, "
        "CASE ENDED_STATUS WHEN 16 THEN 'Ended OK' WHEN 32 THEN 'Ended Not OK' ELSE 'Estado no conocido' END AS END_STATUS "
        "FROM RUNINFO_HISTORY WHERE JOB_MEM_NAME LIKE :lik ORDER BY START_TIME DESC",
        {"lik": f"%{job_mem}%"},
        )
    else:
        raise ValueError(f"Tipo de BD no soportado: {DB_TYPE}")



def query_script_cmdline(text):
    like = f"%{text}%"
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, "
        "J.MEMNAME AS SCRIPT, J.CMD_LINE, J.DESCRIPTION, J.NODE_ID, J.CONFIRM_FLAG, J.DAYS_CAL, "
        "J.WEEKS_CAL, J.CYCLIC, J.FROM_TIME, J.TO_TIME "
        "FROM DEF_JOB J JOIN DEF_TABLES T ON J.TABLE_ID = T.TABLE_ID "
        "WHERE J.MEMNAME LIKE :lik OR J.CMD_LINE LIKE :lik2",
        {"lik": like, "lik2": like},
    )


def query_variables(var_text):
    like = f"%{var_text}%"
    return get_data(
        "SELECT T.DATA_CENTER, J.PARENT_TABLE, J.TASK_TYPE, J.JOB_NAME, S.NAME AS VAR_NAME, S.VALUE "
        "FROM DEF_SETVAR S, DEF_JOB J, DEF_TABLES T "
        "WHERE (J.JOB_ID=S.JOB_ID AND J.TABLE_ID=S.TABLE_ID) "
        "AND (S.NAME LIKE :lik OR S.VALUE LIKE :lik2) ORDER BY S.NAME DESC",
        {"lik": like, "lik2": like},
    )


def query_node_groups():
    return get_data_ctm("SELECT GRPNAME, NODEID FROM CMS_NODGRP ORDER BY 1")


def query_variables_globales(var_name):
    return get_data_ctm(
        "SELECT VAR, VAREXPR FROM CMR_SETVAR WHERE VAR LIKE :lik ORDER BY VAR DESC",
        {"lik": f"%{var_name}%"},
    )


# --- Consultas avanzadas (AFT, SAP, BW, OS400)
def query_aft_jobname(text):
    return get_data(
        "SELECT J.PARENT_TABLE, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, S.NAME, S.VALUE "
        "FROM DEF_JOB J, DEF_TABLES T, DEF_SETVAR S "
        "WHERE J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID AND J.TABLE_ID = T.TABLE_ID "
        "AND S.NAME LIKE '%FTP-%PATH%' AND J.JOB_NAME LIKE :lik",
        {"lik": f"%{text}%"},
    )


def query_aft_origendestino(text):
    return get_data(
        "SELECT J.PARENT_TABLE, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, S.NAME, S.VALUE "
        "FROM DEF_JOB J, DEF_TABLES T, DEF_SETVAR S "
        "WHERE J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID AND J.TABLE_ID = T.TABLE_ID "
        "AND S.NAME LIKE '%FTP-%PATH%' AND S.VALUE LIKE :lik",
        {"lik": f"%{text}%"},
    )


def query_sap_jobname_cm(text):
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "J.NODE_ID, S.VALUE AS CMD_LINE, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T, DEF_SETVAR S "
        "WHERE J.TABLE_ID = T.TABLE_ID AND J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "AND S.NAME LIKE '%SAPR3-JOBNAME%' AND J.JOB_NAME LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text}%"},
    )


def query_sap_jobname_r3(text):
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "J.NODE_ID, S.VALUE AS CMD_LINE, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T, DEF_SETVAR S "
        "WHERE J.TABLE_ID = T.TABLE_ID AND J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "AND S.NAME LIKE '%SAPR3-JOBNAME%' AND S.VALUE LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text}%"},
    )


def query_bw_controlm(text):
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "S.VALUE AS CMD_LINE, J.NODE_ID, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T, DEF_SETVAR S "
        "WHERE J.TABLE_ID = T.TABLE_ID AND J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "AND S.NAME LIKE '%SAPR3-ProcessChain_ID%' AND J.JOB_NAME LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text}%"},
    )


def query_bw_cadena_procesos(text):
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "S.VALUE AS CMD_LINE, J.NODE_ID, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T, DEF_SETVAR S "
        "WHERE J.TABLE_ID = T.TABLE_ID AND J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "AND S.NAME LIKE '%SAPR3-ProcessChain_ID%' AND S.VALUE LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text}%"},
    )


def query_os400_cmdline(text):
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "J.NODE_ID, S.VALUE AS CMD_LINE, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T, DEF_SETVAR S "
        "WHERE J.TABLE_ID = T.TABLE_ID AND J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "AND S.VALUE LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text}%"},
    )


def query_os400_jobname_cm(text):
    return get_data(
        "SELECT J.PARENT_TABLE, J.APPLICATION, J.GROUP_NAME, J.JOB_NAME, J.MEMNAME AS SCRIPT, J.DESCRIPTION, "
        "J.NODE_ID, S.VALUE AS CMD_LINE, J.FROM_TIME, J.TO_TIME, T.USER_DAILY "
        "FROM DEF_JOB J, DEF_TABLES T, DEF_SETVAR S "
        "WHERE J.TABLE_ID = T.TABLE_ID AND J.TABLE_ID = S.TABLE_ID AND J.JOB_ID = S.JOB_ID "
        "AND S.NAME LIKE '%OS400-CMDLINE1%' AND J.JOB_NAME LIKE :lik ORDER BY J.JOB_NAME",
        {"lik": f"%{text}%"},
    )
