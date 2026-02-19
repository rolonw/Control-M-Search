# Despliegue en Kubernetes

Este directorio contiene los archivos YAML necesarios para desplegar Control-M Search Web en un cluster de Kubernetes.

## Archivos incluidos

- **deployment.yaml**: Define el Deployment con los pods de la aplicación
- **service.yaml**: Define el Service para acceso interno al cluster
- **configmap.yaml**: Configuración de la aplicación (db_config.json)
- **secrets.yaml**: Secretos sensibles (contraseñas, claves, licencias)
- **persistent-volume-claim.yaml**: Volumen persistente para datos
- **ingress.yaml**: Configuración de Ingress para acceso externo (opcional)

## Requisitos previos

1. Cluster de Kubernetes funcionando
2. `kubectl` configurado y conectado al cluster
3. Acceso a las bases de datos Control-M desde el cluster
4. (Opcional) Controlador de Ingress instalado (nginx, traefik, etc.)

## Pasos de despliegue

### 1. Preparar secretos

**IMPORTANTE**: No uses el archivo `secrets.yaml` directamente en producción. Crea los secretos manualmente:

```bash
# Crear secretos desde archivos locales
kubectl create secret generic controlm-search-secrets \
  --from-literal=flask-secret-key='tu-clave-secreta-segura' \
  --from-literal=admin-password='tu-password-admin-seguro' \
  --from-file=license.json=../license.json
```

### 2. Configurar ConfigMap

Edita `configmap.yaml` con tu configuración de base de datos real:

```bash
# Editar el archivo
nano configmap.yaml

# Aplicar el ConfigMap
kubectl apply -f configmap.yaml
```

### 3. Crear volumen persistente

```bash
kubectl apply -f persistent-volume-claim.yaml
```

### 4. Desplegar la aplicación

```bash
# Aplicar todos los recursos
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Verificar el despliegue
kubectl get pods -l app=controlm-search-web
kubectl get svc controlm-search-web-service
```

### 5. (Opcional) Configurar Ingress

Si necesitas acceso externo, configura el Ingress:

```bash
# Editar ingress.yaml con tu dominio
nano ingress.yaml

# Aplicar el Ingress
kubectl apply -f ingress.yaml
```

## Construir y subir la imagen Docker

Antes de desplegar, necesitas construir y subir la imagen Docker a un registry:

```bash
# Construir la imagen
docker build -t controlm-search-web:latest .

# Etiquetar para tu registry (ejemplo con Docker Hub)
docker tag controlm-search-web:latest tu-usuario/controlm-search-web:latest

# Subir la imagen
docker push tu-usuario/controlm-search-web:latest

# Actualizar deployment.yaml con la imagen correcta
```

O si usas un registry privado:

```bash
# Ejemplo con Azure Container Registry
az acr build --registry mi-registry --image controlm-search-web:latest .

# Ejemplo con Google Container Registry
gcloud builds submit --tag gcr.io/mi-proyecto/controlm-search-web:latest .
```

## Verificación

```bash
# Ver logs de los pods
kubectl logs -l app=controlm-search-web --tail=50

# Verificar estado del deployment
kubectl describe deployment controlm-search-web

# Verificar servicios
kubectl get svc

# Probar conectividad interna
kubectl port-forward svc/controlm-search-web-service 8080:80
# Luego acceder a http://localhost:8080
```

## Escalado

```bash
# Escalar a 3 réplicas
kubectl scale deployment controlm-search-web --replicas=3

# Escalado automático (requiere metrics-server)
kubectl autoscale deployment controlm-search-web --min=2 --max=5 --cpu-percent=70
```

## Actualización

```bash
# Actualizar la imagen
kubectl set image deployment/controlm-search-web \
  controlm-search-web=tu-usuario/controlm-search-web:v2.0

# Ver el progreso del rollout
kubectl rollout status deployment/controlm-search-web

# Rollback si es necesario
kubectl rollout undo deployment/controlm-search-web
```

## Troubleshooting

### Los pods no inician

```bash
# Ver eventos
kubectl get events --sort-by=.metadata.creationTimestamp

# Ver logs detallados
kubectl describe pod <nombre-del-pod>
kubectl logs <nombre-del-pod>
```

### Problemas de conexión a base de datos

- Verifica que el ConfigMap tenga la configuración correcta
- Verifica que el cluster pueda alcanzar las bases de datos (DNS, red, firewall)
- Revisa los logs de los pods para errores de conexión

### Problemas de sesión

- El Service tiene `sessionAffinity: ClientIP` configurado
- El Ingress tiene configuración de cookies para mantener sesiones
- Si usas múltiples réplicas, considera usar Redis para sesiones compartidas

## Notas de seguridad

1. **Nunca** commits secretos reales en el repositorio
2. Usa herramientas como Sealed Secrets o External Secrets Operator en producción
3. Configura Network Policies para limitar el tráfico de red
4. Usa TLS/HTTPS en producción (configura certificados en el Ingress)
5. Cambia las contraseñas por defecto antes de desplegar en producción

## Personalización

### Variables de entorno adicionales

Edita `deployment.yaml` para agregar más variables de entorno según necesites.

### Recursos (CPU/Memoria)

Ajusta los valores en `deployment.yaml` según tus necesidades:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Health checks

Los health checks están configurados en `deployment.yaml`. Puedes ajustar los tiempos según necesites.
