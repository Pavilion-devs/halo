# Build context is apps/api (Railway Root Directory = apps/api), so all COPY paths
# are relative to apps/api — not the repo root.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# Install deps from requirements.txt (no packaging/build backend needed — the app runs
# from source, with /app on sys.path). Copied first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

EXPOSE 8000

# Create tables, seed the two demo incidents, then launch. Re-runs on every boot so the
# demo is always clean — SQLite is ephemeral on Railway by design (don't attach a volume).
CMD ["sh", "-c", "python -c 'import app.db.models; from app.db.session import create_db_and_tables; create_db_and_tables()' && python scripts/seed_resilience_demo.py && python scripts/seed_live_approval_demo.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
