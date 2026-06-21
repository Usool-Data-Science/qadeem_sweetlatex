# ── Stage 1: Python dependency builder ───────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System packages needed to compile some ML wheels (faiss, tokenizers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install PyTorch CPU-only first (much smaller than CUDA build — ~800 MB vs ~3 GB)
# Pin the index URL so Docker layer cache is stable
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
        torch==2.3.1 \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Lean runtime image ───────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system deps only (libpq for psycopg2, curl for healthcheck, pg_isready for Postgres checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder — keeps final image lean
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Pre-create ML artefact directories so volume mounts have the right paths
# even before the nightly Celery tasks have run for the first time
RUN mkdir -p /app/faiss_index /app/ml_models

# Collect static files at build time (avoids startup delay)
RUN python manage.py collectstatic --noinput --settings=sweetlatexBE.settings.prod 2>/dev/null || true

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]