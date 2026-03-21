FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY app/ ./app/
RUN pip install --no-cache-dir .

COPY fine-tuned-RAG/ ./fine-tuned-RAG/
COPY . .

EXPOSE 8000

ENV SERVICE_MODE=api
CMD sh -c 'if [ "$SERVICE_MODE" = "worker" ]; then celery -A app.celery_app worker --loglevel=info --concurrency=2; else uvicorn app.main:app --host 0.0.0.0 --port 8000; fi'
