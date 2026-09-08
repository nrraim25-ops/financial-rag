# Multi-stage-friendly, minimal image. Stateless app container - the index
# and secrets are NOT baked into the image (see README Scaling section).
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

# ANTHROPIC_API_KEY etc. are injected at runtime via `docker run -e` or a
# secrets manager - never via COPY/ENV in this file.
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
