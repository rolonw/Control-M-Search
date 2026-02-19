# Control-M Search®

Aplicación web Flask para búsqueda y consultas avanzadas en bases de datos de Control-M. Permite realizar búsquedas, generar informes y exportar datos desde las tablas DEF_JOB y CMS_NODGRP de Control-M.

## 🚀 Características

- **Búsquedas básicas**: Por aplicación, grupo, node_id, jobname, descripción, tablas, script, variables, estadísticas, condiciones IN/OUT
- **Consultas avanzadas**: Soporte para AFT, SAP, BW y OS400
- **Informes interactivos**: Panel lateral con múltiples informes (NODE_ID, APPLICATION, TASK_TYPE, OWNER, Node Groups, Variables Globales)
- **Exportación a CSV**: Exporta resultados de búsquedas e informes
- **Sistema de licencias**: Validación por fecha con activación mediante clave
- **Panel de administración**: Gestión de licencias y configuración de base de datos
- **Multi-base de datos**: Soporte para Oracle, SQL Server y PostgreSQL

## 📋 Requisitos

- Python 3.8 o superior
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
   
   La aplicación utiliza el archivo `Control-M_SearchWeb/db_config.json` para la configuración de base de datos. Puedes configurarlo mediante:
   - El panel de administración en `/admin` (requiere contraseña)
   - Editando manualmente el archivo `Control-M_SearchWeb/db_config.json`


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

### Informes

En la página "Informes" encontrarás:
- **Por NODE_ID**: Conteo de jobs por NODE_ID
- **Por APPLICATION**: Conteo de jobs por APPLICATION
- **Por TASK_TYPE**: Conteo de jobs por TASK_TYPE
- **Por OWNER**: Conteo de jobs por OWNER
- **Node Groups**: Lista de grupos de nodos
- **Variables Globales**: Búsqueda de variables globales (requiere parámetro de búsqueda)

Cada informe incluye un botón para exportar a CSV.

### Exportación

- Los resultados de búsquedas se pueden exportar desde el menú "Exportar a CSV"
- Los informes tienen botones de exportación individuales
- Los archivos CSV se descargan con nombres descriptivos

### Administración

Accede a `/admin` para:
- Activar licencias con clave de licencia
- Configurar conexión a base de datos
- Ver información del sistema

**Nota**: Cambiar la contraseña de administración en producción modificando `ADMIN_PASSWORD` en `app.py`


## 📁 Estructura del Proyecto

```
├── Control-M_SearchWeb/
│   ├── app.py                 # Aplicación Flask principal
│   ├── db.py                  # Acceso a base de datos
│   ├── config.py              # Configuración de conexiones
│   ├── db_config_manager.py   # Gestión de configuración persistente
│   ├── license_manager.py     # Gestión de licencias
│   ├── odbc_utils.py          # Utilidades ODBC
│   ├── generate_license_key.py # Generador de claves de licencia
│   ├── templates/             # Plantillas HTML (Jinja2)
│   ├── db_config.json         # Configuración de BD (se crea automáticamente)
│   └── license.json           # Archivo de licencia (se crea automáticamente)
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

## 🗄️ Bases de Datos Soportadas

### Oracle
- Requiere: `oracledb` (anteriormente cx_Oracle)
- Configuración: Host, puerto, service_name o SID, usuario, contraseña
- Soporta modo thin (sin Oracle Client)

### SQL Server
- Requiere: `pyodbc` y driver ODBC instalado
- Configuración: Servidor, puerto, base de datos, usuario, contraseña, driver ODBC
- Detecta automáticamente drivers disponibles

### PostgreSQL
- Requiere: `psycopg2-binary`
- Configuración: Host, puerto, base de datos, usuario, contraseña

## 🛠️ Desarrollo

### Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Base de datos**: Oracle / SQL Server / PostgreSQL
- **Templates**: Jinja2

### Archivos Importantes

- `app.py`: Contiene todas las rutas y lógica de la aplicación
- `db.py`: Maneja todas las consultas a la base de datos
- `config.py`: Configuración de conexiones según tipo de BD
- `templates/`: Plantillas HTML con Bootstrap

## 📝 Notas

- La aplicación requiere acceso a las tablas `DEF_JOB` y `CMS_NODGRP` de Control-M
- Los archivos `db_config.json` y `license.json` se crean automáticamente
- En producción, cambiar la clave secreta de Flask y la contraseña de administración
- El sistema de licencias valida la fecha en el servidor, no puede ser manipulado por el cliente

## 👤 Autor

**Walter Rolon**

- Contacto: soporte@cgconsultores.com.ar
- Versión: Web - 2026

## 📄 Licencia

Este software es propiedad de CG Consultores. Todos los derechos reservados.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

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
