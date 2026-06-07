# OpenThreatGrid HTTP trap — deception web honeypot.
#
# Logs JSON events to /var/log/http-trap/http-trap.log, tailed by the OTG worker
# parser sidecar (SENSOR_TYPE=http-trap).
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HTTP_TRAP_LOG_PATH=/var/log/http-trap/http-trap.log

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home --uid 10003 trap \
    && mkdir -p /var/log/http-trap \
    && chown -R trap:trap /var/log/http-trap
USER trap

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
