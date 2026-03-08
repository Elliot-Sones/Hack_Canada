# Stage 1: Build React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend-react/package*.json ./
RUN npm ci
COPY frontend-react/ ./
RUN npm run build

# Stage 2: Build Python backend + embed frontend
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source and install
COPY pyproject.toml .
COPY app/ ./app/
RUN pip install --no-cache-dir .

# Copy remaining files (alembic, scripts, etc.)
COPY . .

# Embed the built frontend
COPY --from=frontend-builder /frontend/dist /app/frontend-dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
