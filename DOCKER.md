# Guía de Despliegue con Docker y Kubernetes

Esta guía explica cómo desplegar Control-M Search Web usando Docker y Kubernetes.

## 🐳 Docker

### Construcción de la imagen

```bash
# Construir la imagen
docker build -t controlm-search-web:latest .

# Verificar que la imagen se creó
docker images | grep controlm-search-web
```

### Ejecución con Docker

```bash
# Ejecutar el contenedor
docker run -d \
  --name controlm-search-web \
  -p 5000:5000 \
  -e FLASK_SECRET_KEY="tu-clave-secreta" \
  -e ADMIN_PASSWORD="tu-password-admin" \
  -v $(pwd)/db_config.json:/app/db_config.json:ro \
  -v $(pwd)/license.json:/app/license.json:ro \
  controlm-search-web:latest

# Ver logs
docker logs -f controlm-search-web

# Detener el contenedor
docker stop controlm-search-web
docker rm controlm-search-web
```

### Ejecución con Docker Compose

```bash
# Crear directorio para datos persistentes
mkdir -p data

# Configurar variables de entorno (opcional)
export FLASK_SECRET_KEY="tu-clave-secreta"
export ADMIN_PASSWORD="tu-password-admin"

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

### Acceso a la aplicación

Una vez iniciado el contenedor, accede a:
- **URL**: http://localhost:5000
- **Admin**: http://localhost:5000/admin

## ☸️ Kubernetes

### Requisitos previos

1. Cluster de Kubernetes funcionando
2. `kubectl` configurado
3. Acceso a un registry de imágenes Docker (Docker Hub, ACR, GCR, etc.)

### Pasos rápidos

#### 1. Construir y subir la imagen

```bash
# Construir
docker build -t tu-registry/controlm-search-web:latest .

# Subir al registry
docker push tu-registry/controlm-search-web:latest

# Actualizar deployment.yaml con la imagen correcta
sed -i 's|controlm-search-web:latest|tu-registry/controlm-search-web:latest|g' k8s/deployment.yaml
```

#### 2. Crear secretos

```bash
# Crear secretos (IMPORTANTE: usa valores seguros)
kubectl create secret generic controlm-search-secrets \
  --from-literal=flask-secret-key='tu-clave-secreta-muy-segura' \
  --from-literal=admin-password='tu-password-admin-seguro' \
  --from-file=license.json=./license.json
```

#### 3. Configurar ConfigMap

```bash
# Editar configmap.yaml con tu configuración de BD
nano k8s/configmap.yaml

# Aplicar ConfigMap
kubectl apply -f k8s/configmap.yaml
```

#### 4. Desplegar

```bash
# Aplicar todos los recursos
kubectl apply -f k8s/persistent-volume-claim.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# (Opcional) Si necesitas acceso externo
kubectl apply -f k8s/ingress.yaml
```

#### 5. Verificar

```bash
# Ver pods
kubectl get pods -l app=controlm-search-web

# Ver servicios
kubectl get svc

# Ver logs
kubectl logs -l app=controlm-search-web --tail=50

# Port-forward para acceso local
kubectl port-forward svc/controlm-search-web-service 8080:80
# Acceder a http://localhost:8080
```

## 🔧 Configuración

### Variables de entorno importantes

- `FLASK_SECRET_KEY`: Clave secreta para sesiones Flask (cambiar en producción)
- `ADMIN_PASSWORD`: Contraseña del panel de administración (cambiar en producción)
- `PORT`: Puerto donde escucha la aplicación (default: 5000)
- `DB_TYPE`: Tipo de base de datos (oracle, mssql, postgresql)

### Archivos de configuración

- `db_config.json`: Configuración de conexión a bases de datos
- `license.json`: Archivo de licencia de la aplicación

Estos archivos se pueden proporcionar de varias formas:
1. Montados como volúmenes (Docker)
2. ConfigMaps y Secrets (Kubernetes)
3. Variables de entorno (limitado)

## 🚀 Producción

### Recomendaciones para producción

1. **Seguridad**:
   - Cambiar `FLASK_SECRET_KEY` y `ADMIN_PASSWORD`
   - Usar HTTPS/TLS
   - Configurar Network Policies en Kubernetes
   - No exponer secretos en repositorios

2. **Rendimiento**:
   - Usar Gunicorn con múltiples workers
   - Configurar límites de recursos apropiados
   - Considerar usar Redis para sesiones compartidas si hay múltiples réplicas

3. **Monitoreo**:
   - Configurar health checks
   - Implementar logging centralizado
   - Configurar alertas

4. **Alta disponibilidad**:
   - Múltiples réplicas del deployment
   - Load balancer configurado
   - Persistent volumes para datos críticos

## 📝 Notas

- La aplicación usa sesiones Flask, por lo que es importante mantener la afinidad de sesión en producción
- Para SQL Server, asegúrate de tener drivers ODBC instalados en el contenedor
- Para Oracle, la aplicación usa modo "thin" y no requiere Oracle Client
- Los archivos `db_config.json` y `license.json` deben estar disponibles en runtime

## 🆘 Troubleshooting

### El contenedor no inicia

```bash
# Ver logs
docker logs controlm-search-web

# Verificar configuración
docker exec controlm-search-web cat /app/db_config.json
```

### Error de conexión a base de datos

- Verifica que el contenedor/pod pueda alcanzar las bases de datos
- Verifica la configuración en `db_config.json`
- Revisa los logs para mensajes de error específicos

### Problemas en Kubernetes

```bash
# Ver eventos del cluster
kubectl get events --sort-by=.metadata.creationTimestamp

# Describir recursos
kubectl describe pod <nombre-pod>
kubectl describe deployment controlm-search-web
```

Para más detalles, consulta `k8s/README.md`.
