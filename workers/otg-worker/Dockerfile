# OpenThreatGrid worker — runs as parser sidecar or enrichment consumer.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker ./worker

RUN useradd --create-home --uid 10001 otg
USER otg

# Default role is the consumer; override with: command: ["python","-m","worker","parser"]
ENTRYPOINT ["python", "-m", "worker"]
CMD ["consumer"]
