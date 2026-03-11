# Dockerfile para Control-M Search Web
# Python 3.10.13 | Flask | SQLAlchemy (Oracle, PostgreSQL, MSSQL)
# Multi-stage build para reducir tamaño de imagen

# ------------------------------------------------------------------------------
# Stage 1: Builder - instalar dependencias Python
# ------------------------------------------------------------------------------
FROM python:3.10.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
#    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Runtime
# ------------------------------------------------------------------------------
FROM python:3.10.13-slim

WORKDIR /app

# Runtime: unixodbc (MSSQL), curl (healthcheck). Oracle usa modo thin, PostgreSQL no requiere extras.
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

RUN mkdir -p /app/data && chmod 755 /app/data

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/about || exit 1

# Servidor de desarrollo Flask (python app.py). Para producción con más tráfico considerar Gunicorn.
CMD ["python", "app.py"]
