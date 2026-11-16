# Multi-stage production container for Clipora
FROM node:20-alpine AS frontend-builder
WORKDIR /app/dashboard
COPY dashboard/package.json ./
RUN npm install
COPY dashboard/ ./
RUN npm run build

# Base Python runtime with FFmpeg
FROM python:3.12-slim AS runner

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    curl \
    ca-certificates \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and dashboard build
COPY src/ ./src/
COPY data/ ./data/
COPY fonts/ ./fonts/
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e .

COPY --from=frontend-builder /app/dashboard/dist /app/dashboard/dist

# Expose FastAPI HTTP Port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/config || exit 1

# Launch FastAPI Uvicorn Server
CMD ["uvicorn", "clipora.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
