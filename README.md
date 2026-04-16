# Control-M Search®

Aplicación web Flask para búsqueda y consultas avanzadas en bases de datos de Control-M. Permite realizar búsquedas y exportar resultados a CSV desde las tablas de Control-M (por ejemplo `DEF_JOB`, `CMS_NODGRP` y consultas relacionadas). El módulo de **informes** no está incluido en esta versión; se prevé para una versión posterior.

## 🚀 Características

- **Búsquedas básicas**: Por aplicación, grupo, node_id, jobname, descripción, tablas, script, variables, estadísticas, condiciones IN/OUT
- **Consultas avanzadas**: Soporte para AFT, SAP, BW y OS400
- **Exportación a CSV**: Exporta la última búsqueda realizada (menú *Exportar a CSV*)
- **Sistema de licencias**: Validación por fecha en servidor (`license_manager.py`); activación en `/admin` con clave emitida por el proveedor
- **Panel de administración**: Gestión de licencias y configuración de base de datos
- **Multi-base de datos**: Soporte para Oracle, SQL Server y PostgreSQL

## 📋 Requisitos

- Python 3.8 o superior (entorno local). La imagen Docker usa **Python 3.11** sobre **AlmaLinux 9**; ver `DOCKER.md`.
- Acceso a base de datos Control-M (Oracle, SQL Server o PostgreSQL)
- Driver ODBC para SQL Server (si se usa SQL Server)

## 🔧 Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd Control-M_SearchWeb
   ```

2. **Crear entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar driver de base de datos según corresponda**
   
   **Para Oracle:**
   ```bash
   pip install oracledb>=1.4.0
   ```
   
   **Para SQL Server:**
   ```bash
   pip install pyodbc>=4.0.39
   ```
   
   **Para PostgreSQL:**
   ```bash
   pip install psycopg2-binary>=2.9.9
   ```

## ⚙️ Configuración

1. **Configurar base de datos**
   
   La aplicación utiliza el archivo `db_config.json` en la raíz del proyecto para la configuración de base de datos. Puedes configurarlo mediante:
   - El panel de administración en `/admin` (requiere contraseña)
   - Editando manualmente `db_config.json`

   En Docker, si montas `db_config.json` como solo lectura (`:ro`), no podrás guardar cambios desde `/admin`; monta el volumen sin `:ro` si necesitas editar la configuración desde la interfaz.


## 🏃 Ejecución

1. **Navegar al directorio webapp**
   ```bash
   cd Control-M_SearchWeb
   ```

2. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

3. **Acceder a la aplicación**
   
   Abrir navegador en: `http://localhost:5000`

## 📖 Uso

### Búsquedas Básicas

En la página principal puedes realizar búsquedas por:
- **Application**: Nombre de aplicación
- **Group**: Nombre de grupo
- **Node ID**: ID del nodo
- **Jobname**: Nombre del job
- **Description**: Descripción del job
- **Tables**: Tablas relacionadas
- **Script**: Contenido de script
- **Variables**: Variables del job
- **Estadísticas**: Estadísticas del job
- **Condiciones IN/OUT**: Condiciones de entrada/salida

### Consultas Avanzadas

En "Consultas Avanzadas" puedes realizar búsquedas específicas para:
- **AFT**: Búsqueda por job name o origen-destino
- **SAP**: Búsqueda por nombre en Control-M o SAP
- **BW**: Búsqueda por job name Control-M o cadena de procesos
- **OS400**: Búsqueda por CMD Line o job name

### Informes (próxima versión)

En esta versión **no** hay pantalla ni rutas de informes agregados. Las búsquedas por **Node Groups** y **Variables globales** siguen disponibles en la página principal y en consultas avanzadas según el formulario.

### Exportación

- Tras una búsqueda con resultados, usa el menú **Exportar a CSV** para descargar la última consulta ejecutada (`consulta.csv`).
- Si no hay resultados en caché, la exportación indicará que no hay datos; ejecuta una búsqueda primero.

### Administración

Accede a `/admin` para:
- Activar licencias con clave de licencia
- Configurar conexión a base de datos
- Ver información del sistema

**Nota**: En producción, define la contraseña de administración con la variable de entorno `ADMIN_PASSWORD` (por defecto en código solo para desarrollo). También conviene fijar `FLASK_SECRET_KEY`.

### Licencias (proveedor vs. cliente)

- **En runtime**, la aplicación solo usa `license_manager.py`: verifica la clave guardada en `license.json` y la fecha de expiración. **No hace falta** `generate_license_key.py` en el servidor del cliente para validar.
- **Generación de claves** (solo quien distribuye el software): ejecuta `python generate_license_key.py YYYY-MM-DD` o `python generate_license_key.py --years N`. Ese script importa la misma lógica de secreto que la app (`_get_secret` en `license_manager`) para firmar claves coherentes con la verificación.
- **Secreto compartido**: por defecto está en código (`license_manager`); en producción puedes fijar **`LICENSE_SECRET`** en el entorno (mismo valor al generar claves y al ejecutar la app). Cambia el valor por defecto si distribuyes binarios o imágenes a terceros.
- **Docker**: `.dockerignore` excluye `generate_license_key.py` de la imagen, de modo que el contenedor del cliente no incluye el generador.


## 📁 Estructura del Proyecto

```
├── app.py                    # Aplicación Flask principal
├── db.py                     # Acceso a datos (SQLAlchemy)
├── config.py                 # URLs de conexión según tipo de BD
├── db_config_manager.py      # Lectura/escritura de db_config.json
├── license_manager.py        # Validación y activación de licencia (autónomo en runtime)
├── generate_license_key.py   # Generador de claves (solo administrador; no requerido en el cliente)
├── odbc_utils.py             # Listado de drivers ODBC (SQL Server, admin)
├── templates/                # Plantillas HTML (Jinja2)
├── k8s/                      # Manifiestos Kubernetes (opcional)
├── Dockerfile                # Imagen Docker (AlmaLinux 9 + Python 3.11)
├── DOCKER.md                 # Guía Docker / Kubernetes
├── db_config.json            # Configuración de BD (editable o vía /admin)
├── license.json              # Licencia activa (generado vía /admin)
├── requirements.txt          # Dependencias Python
└── README.md                 # Este archivo
```

## 🗄️ Bases de Datos Soportadas

### Oracle
- Requiere: `oracledb` (modo thin; sin Oracle Client)
- Configuración: Host, puerto, service_name o SID, usuario, contraseña

### SQL Server
- Requiere: `pyodbc` y driver ODBC instalado
- Configuración: Servidor, puerto, base de datos, usuario, contraseña, driver ODBC
- Detecta automáticamente drivers disponibles

### PostgreSQL
- Requiere: `psycopg2-binary`
- Configuración: Host, puerto, base de datos, usuario, contraseña

## 🛠️ Desarrollo

### Tecnologías Utilizadas

- **Backend**: Flask (Python), **SQLAlchemy 2** para consultas
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Base de datos**: Oracle / SQL Server / PostgreSQL
- **Templates**: Jinja2

### Archivos Importantes

- `app.py`: Contiene todas las rutas y lógica de la aplicación
- `db.py`: Maneja todas las consultas a la base de datos
- `config.py`: URLs SQLAlchemy y tipo de BD (`oracle`, `mssql`, `postgresql`)
- `license_manager.py`: Comprueba y guarda la licencia; no depende del script generador en despliegue
- `generate_license_key.py`: Herramienta de línea de comandos para el proveedor (no necesaria en el entorno del usuario final)
- `templates/`: Plantillas HTML con Bootstrap

### Contenedor (Docker)

Ver **`DOCKER.md`**: construcción de imagen, variables de entorno, montaje de `db_config.json` / `license.json` y despliegue en Kubernetes.

## 📝 Notas

- La aplicación requiere acceso a las tablas `DEF_JOB` y `CMS_NODGRP` de Control-M
- Los archivos `db_config.json` y `license.json` se crean automáticamente
- En producción, cambiar la clave secreta de Flask y la contraseña de administración
- El sistema de licencias valida la fecha en el servidor, no puede ser manipulado por el cliente
- La clave de licencia se firma con HMAC; quien genera claves debe usar el mismo secreto que la app (`LICENSE_SECRET` o el valor por defecto en `license_manager`, según tu despliegue)

## 👤 Autor

**Walter Rolon**

- Contacto: soporte@cgconsultores.com.ar
- Versión: Web - 2026


## ⚠️ Troubleshooting

### Error de conexión a base de datos
- Verificar que `db_config.json` tenga la configuración correcta
- Verificar que las credenciales sean válidas
- Verificar que el servidor de BD sea accesible desde el servidor web

### Error "No hay datos para exportar"
- Realizar una búsqueda primero antes de exportar
- Verificar que la búsqueda haya devuelto resultados

### Error de licencia
- Verificar que la licencia esté activada en `/admin`
- Verificar que la fecha de expiración no haya pasado

## 📞 Soporte

Para soporte técnico, contactar a: soporte@cgconsultores.com.ar
