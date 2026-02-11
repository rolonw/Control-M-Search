# app.py - Aplicación web Control-M Search
import csv
import io
import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, Response, session, url_for, abort, redirect
import db
from config import DB_TYPE
from db_config_manager import load_config, update_config
from odbc_utils import get_sql_server_drivers
from license_manager import is_license_valid, get_valid_until, activate_license

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "controlm-search-web-2024-change-in-production")
app.config["JSON_AS_ASCII"] = False

# Contraseña para /admin (cambiar en producción)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Rutas que no requieren licencia válida (solo admin puede entrar sin licencia)
_LICENSE_EXEMPT = frozenset(["admin", "admin_login", "admin_logout", "license_expired", "static"])


@app.before_request
def _check_license():
    """Validación por fecha en servidor: el usuario no puede manipularla."""
    if request.endpoint and request.endpoint in _LICENSE_EXEMPT:
        return None
    if request.path.startswith("/static"):
        return None
    if is_license_valid():
        return None
    return redirect(url_for("license_expired"))


def admin_required(f):
    """Decorador para proteger rutas de admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_authenticated"):
            if request.method == "POST":
                password = request.form.get("admin_password", "")
                if password == ADMIN_PASSWORD:
                    session["admin_authenticated"] = True
                else:
                    return render_template("admin_login.html", error="Contraseña incorrecta"), 401
            else:
                return render_template("admin_login.html"), 401
        return f(*args, **kwargs)
    return decorated_function


def _serialize_results(results):
    """Convierte resultados Oracle a listas/dicts serializables para sesión."""
    if not results:
        return []
    out = []
    for row in results:
        out.append({k: (str(v) if v is not None else "") for k, v in row.items()})
    return out


def _get_combos():
    """Retorna (apps, groups, nodes, error). Si hay excepción, error tiene el mensaje."""
    try:
        apps = db.get_combo_values("SELECT DISTINCT APPLICATION FROM DEF_JOB ORDER BY APPLICATION")
        groups = db.get_combo_values("SELECT DISTINCT GROUP_NAME FROM DEF_JOB ORDER BY GROUP_NAME")
        nodes = db.get_combo_values("SELECT DISTINCT NODE_ID FROM DEF_JOB ORDER BY NODE_ID")
        return apps, groups, nodes, None
    except Exception as e:
        return [], [], [], f"Error de conexión (combos): {e}"


@app.route("/")
def index():
    apps, groups, nodes, combo_error = _get_combos()
    return render_template(
        "index.html",
        apps=apps,
        groups=groups,
        nodes=nodes,
        results=None,
        count=None,
        error=combo_error,
    )


def _run_search():
    """Ejecuta la búsqueda según el tipo enviado en el formulario."""
    search_type = request.form.get("search_type") or request.args.get("search_type")
    all_fields = request.form.get("all_fields") == "1" or request.args.get("all_fields") == "1"
    results = []
    error = None
    try:
        if search_type == "application":
            v = request.form.get("application") or request.args.get("application", "").strip()
            if v:
                results = db.query_by_application(v)
        elif search_type == "group":
            v = request.form.get("group") or request.args.get("group", "").strip()
            if v:
                results = db.query_by_group(v)
        elif search_type == "node_id":
            v = request.form.get("node_id") or request.args.get("node_id", "").strip()
            if v:
                results = db.query_by_node_id(v, all_fields=all_fields)
        elif search_type == "jobname":
            v = request.form.get("jobname") or request.args.get("jobname", "").strip()
            if v:
                results = db.query_by_jobname(v.upper(), all_fields=all_fields)
        elif search_type == "description":
            v = request.form.get("description") or request.args.get("description", "").strip()
            if v:
                results = db.query_by_description(v)
        elif search_type == "tables":
            v = request.form.get("tables") or request.args.get("tables", "").strip()
            if v:
                results = db.query_by_tables(v, all_fields=all_fields)
        elif search_type == "script":
            v = request.form.get("script") or request.args.get("script", "").strip()
            if v:
                results = db.query_script_cmdline(v)
        elif search_type == "variables":
            v = request.form.get("variables") or request.args.get("variables", "").strip()
            if v:
                results = db.query_variables(v)
        elif search_type == "estadisticas":
            v = request.form.get("estadisticas") or request.args.get("estadisticas", "").strip()
            if v:
                results = db.query_estadisticas(v)
        elif search_type == "in_condition":
            v = request.form.get("in_condition") or request.args.get("in_condition", "").strip()
            if v:
                results = db.query_in_condition(v)
        elif search_type == "in_condition_job":
            v = request.form.get("in_condition_job") or request.args.get("in_condition_job", "").strip()
            if v:
                results = db.query_in_condition_jobname(v)
        elif search_type == "out_condition":
            v = request.form.get("out_condition") or request.args.get("out_condition", "").strip()
            if v:
                results = db.query_out_condition(v)
        elif search_type == "out_condition_job":
            v = request.form.get("out_condition_job") or request.args.get("out_condition_job", "").strip()
            if v:
                results = db.query_out_condition_jobname(v)
        elif search_type == "node_groups":
            results = db.query_node_groups()
        elif search_type == "variables_globales":
            v = request.form.get("var_global") or request.args.get("var_global", "").strip()
            if v:
                results = db.query_variables_globales(v)
        elif search_type == "unlock_tables":
            v = request.form.get("table_unlock") or request.args.get("table_unlock", "").strip()
            if v:
                results = db.unlock_tables(v)
        # Consultas avanzadas
        elif search_type == "aft_jobname":
            v = request.form.get("aft_jobname") or request.args.get("aft_jobname", "").strip()
            if v:
                results = db.query_aft_jobname(v)
        elif search_type == "aft_origendestino":
            v = request.form.get("aft_origendestino") or request.args.get("aft_origendestino", "").strip()
            if v:
                results = db.query_aft_origendestino(v)
        elif search_type == "sap_cm":
            v = request.form.get("sap_cm") or request.args.get("sap_cm", "").strip()
            if v:
                results = db.query_sap_jobname_cm(v)
        elif search_type == "sap_r3":
            v = request.form.get("sap_r3") or request.args.get("sap_r3", "").strip()
            if v:
                results = db.query_sap_jobname_r3(v)
        elif search_type == "bw_controlm":
            v = request.form.get("bw_controlm") or request.args.get("bw_controlm", "").strip()
            if v:
                results = db.query_bw_controlm(v)
        elif search_type == "bw_cadena":
            v = request.form.get("bw_cadena") or request.args.get("bw_cadena", "").strip()
            if v:
                results = db.query_bw_cadena_procesos(v)
        elif search_type == "os400_cmdline":
            v = request.form.get("os400_cmdline") or request.args.get("os400_cmdline", "").strip()
            if v:
                results = db.query_os400_cmdline(v)
        elif search_type == "os400_jobname":
            v = request.form.get("os400_jobname") or request.args.get("os400_jobname", "").strip()
            if v:
                results = db.query_os400_jobname_cm(v)
    except Exception as e:
        error = str(e)
    return results, error


@app.route("/search", methods=["GET", "POST"])
def search():
    apps, groups, nodes, combo_error = _get_combos()
    results = []
    error = combo_error
    if request.method == "POST" or request.args.get("search_type"):
        search_results, search_error = _run_search()
        results = search_results or []
        if search_error:
            error = search_error
        elif not error:
            error = combo_error
        session["last_results"] = _serialize_results(results) if results else []
    count = len(results) if results is not None else 0
    return render_template(
        "index.html",
        apps=apps,
        groups=groups,
        nodes=nodes,
        results=results if results else None,
        count=count,
        error=error,
    )


@app.route("/api/search", methods=["POST"])
def api_search():
    """API JSON para búsquedas (por si se quiere usar con AJAX)."""
    results, error = _run_search()
    if error:
        return jsonify({"ok": False, "error": error, "data": [], "count": 0})
    return jsonify({"ok": True, "data": results, "count": len(results), "error": None})


@app.route("/export.csv")
def export_csv():
    """Exporta la última consulta guardada en sesión a CSV."""
    results = session.get("last_results")
    if not results:
        return Response("No hay datos para exportar. Realice una búsqueda primero.", mimetype="text/plain", status=400)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(list(results[0].keys()))
    for row in results:
        writer.writerow([str(v) if v is not None else "" for v in row.values()])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=consulta.csv"},
    )


@app.route("/consultas-avanzadas")
def consultas_avanzadas():
    return render_template("consultas_avanzadas.html", results=None, count=None, error=None)


@app.route("/consultas-avanzadas/search", methods=["POST"])
def consultas_avanzadas_search():
    results, error = _run_search()
    session["last_results"] = _serialize_results(results) if results else []
    count = len(results) if results else 0
    return render_template(
        "consultas_avanzadas.html",
        results=results,
        count=count,
        error=error,
    )


@app.route("/informes")
def informes():
    """Informes con 4 grids: NODE_ID, APPLICATION, TASK_TYPE, OWNER (conteos por grupo)."""
    error = None
    report_node = []
    report_app = []
    report_task = []
    report_owner = []
    try:
        report_node = db.get_data(
            "SELECT NODE_ID, COUNT(*) AS TOTAL FROM DEF_JOB GROUP BY NODE_ID ORDER BY 2 DESC"
        )
        report_app = db.get_data(
            "SELECT APPLICATION, COUNT(*) AS TOTAL FROM DEF_JOB GROUP BY APPLICATION ORDER BY 2 DESC"
        )
        report_task = db.get_data(
            "SELECT TASK_TYPE, COUNT(*) AS TOTAL FROM DEF_JOB GROUP BY TASK_TYPE ORDER BY 2 DESC"
        )
        report_owner = db.get_data(
            "SELECT OWNER, COUNT(*) AS TOTAL FROM DEF_JOB GROUP BY OWNER ORDER BY 2 DESC"
        )
        # Serializar por si hay tipos no serializables (ej. Oracle)
        report_node = _serialize_results(report_node) if report_node else []
        report_app = _serialize_results(report_app) if report_app else []
        report_task = _serialize_results(report_task) if report_task else []
        report_owner = _serialize_results(report_owner) if report_owner else []
    except Exception as e:
        error = str(e)
    return render_template(
        "informes.html",
        report_node=report_node,
        report_app=report_app,
        report_task=report_task,
        report_owner=report_owner,
        error=error,
    )


@app.route("/node-groups")
def node_groups():
    try:
        results = db.query_node_groups()
    except Exception as e:
        results = []
        return render_template("util_result.html", results=[], count=0, error=str(e), title="Node Groups")
    return render_template("util_result.html", results=results, count=len(results), error=None, title="Node Groups")


@app.route("/variables-globales", methods=["GET", "POST"])
def variables_globales():
    if request.method == "POST":
        v = request.form.get("var_global", "").strip()
        if v:
            try:
                results = db.query_variables_globales(v)
                session["last_results"] = _serialize_results(results)
                return render_template("util_result.html", results=results, count=len(results), error=None, title="Variables Globales")
            except Exception as e:
                return render_template("util_result.html", results=[], count=0, error=str(e), title="Variables Globales")
    return render_template("util_form.html", action=url_for("variables_globales"), field_name="var_global", label="Nombre de la variable", title="Variables Globales", button_text="Buscar")


@app.route("/unlock-tables", methods=["GET", "POST"])
def unlock_tables():
    if request.method == "POST":
        v = request.form.get("table_unlock", "").strip()
        if v:
            try:
                results = db.unlock_tables(v)
                session["last_results"] = _serialize_results(results)
                return render_template("util_result.html", results=results, count=len(results), error=None, title="Unlock Tables")
            except Exception as e:
                return render_template("util_result.html", results=[], count=0, error=str(e), title="Unlock Tables")
    return render_template("util_form.html", action=url_for("unlock_tables"), field_name="table_unlock", label="Nombre de la tabla", title="Unlock Tables", button_text="Ejecutar")


@app.route("/about")
def about():
    config = load_config()
    ems_info = f"{config['ems']['host']}:{config['ems']['port']}"
    ctm_info = f"{config['ctm']['host']}:{config['ctm']['port']}"
    return render_template(
        "about.html",
        db_type=DB_TYPE.upper(),
        server_ems=ems_info,
        server_ctm=ctm_info,
    )


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    """Panel de administración para configurar la base de datos y la licencia."""
    config = load_config()
    error = None
    success = False
    license_success = None
    license_error = None
    odbc_drivers = get_sql_server_drivers()

    if request.method == "POST":
        # Activación de licencia (clave con duración, p. ej. 2 años)
        if request.form.get("action") == "activate_license":
            key = request.form.get("license_key", "").strip()
            ok, msg = activate_license(key)
            if ok:
                license_success = msg
            else:
                license_error = msg
        else:
            try:
                db_type = request.form.get("db_type", "oracle").lower()
                ems_config = {
                    "host": request.form.get("ems_host", "").strip(),
                    "port": int(request.form.get("ems_port", 1521)),
                    "service_name": request.form.get("ems_service_name", "").strip(),
                    "sid": request.form.get("ems_sid", "").strip(),
                    "tns": request.form.get("ems_tns", "").strip(),
                    "user": request.form.get("ems_user", "").strip(),
                    "password": request.form.get("ems_password", "").strip(),
                    "database": request.form.get("ems_database", "").strip(),
                    "driver": request.form.get("ems_driver", "").strip(),
                }
                ctm_config = {
                    "host": request.form.get("ctm_host", "").strip(),
                    "port": int(request.form.get("ctm_port", 1521)),
                    "service_name": request.form.get("ctm_service_name", "").strip(),
                    "sid": request.form.get("ctm_sid", "").strip(),
                    "tns": request.form.get("ctm_tns", "").strip(),
                    "user": request.form.get("ctm_user", "").strip(),
                    "password": request.form.get("ctm_password", "").strip(),
                    "database": request.form.get("ctm_database", "").strip(),
                    "driver": request.form.get("ctm_driver", "").strip(),
                }
                if update_config(db_type, ems_config, ctm_config):
                    success = True
                    config = load_config()
                else:
                    error = "Error al guardar la configuración."
            except Exception as e:
                error = f"Error: {str(e)}"

    valid_until = get_valid_until()
    return render_template(
        "admin.html",
        config=config,
        error=error,
        success=success,
        odbc_drivers=odbc_drivers,
        license_valid_until=valid_until,
        license_success=license_success,
        license_error=license_error,
    )


@app.route("/admin/logout")
def admin_logout():
    """Cerrar sesión de admin."""
    session.pop("admin_authenticated", None)
    return render_template("admin_login.html", message="Sesión cerrada correctamente")


@app.route("/licencia-expirada")
def license_expired():
    """Página mostrada cuando la licencia no está activa o ha expirado."""
    valid_until = get_valid_until()
    return render_template("license_expired.html", valid_until=valid_until)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
