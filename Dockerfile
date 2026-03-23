FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src/engine:/app/src/backend:/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create storage directories
RUN mkdir -p /app/storage /app/artifacts /tmp/storage /tmp/artifacts

# Set permissions
RUN chmod +x /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Render defines $PORT automatically (no fallback needed)
EXPOSE 8000
CMD ["uvicorn", "src.backend.app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
