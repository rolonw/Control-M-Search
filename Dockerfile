# Dockerfile para Control-M Search Web
# Multi-stage build para optimizar el tamaño de la imagen

# Stage 1: Build stage
FROM python:3.10.13-slim AS builder

WORKDIR /build

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.10.13-slim

WORKDIR /app

# Instalar dependencias del sistema para runtime
# Para Oracle: no se necesita Oracle Client (usa modo thin)
# Para SQL Server: necesita unixodbc y drivers ODBC
# Para PostgreSQL: no necesita dependencias adicionales
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias Python instaladas desde el stage builder
COPY --from=builder /root/.local /root/.local

# Asegurar que los scripts en .local estén en el PATH
ENV PATH=/root/.local/bin:$PATH

# Copiar código de la aplicación
COPY . .

# Crear directorios para archivos de configuración y datos
RUN mkdir -p /app/data && \
    chmod 755 /app/data

# Variables de entorno por defecto
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Exponer el puerto de la aplicación
EXPOSE 5000

# Healthcheck para verificar que la aplicación está funcionando
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/about || exit 1

# Ejecutar la aplicación con el servidor de desarrollo de Flask (Python)
CMD ["python", "app.py"]
