# OpenThreatGrid weekly report generator (runs as a CronJob).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generate_report.py .
COPY templates ./templates

RUN useradd --create-home --uid 10001 otg
USER otg

ENTRYPOINT ["python", "generate_report.py"]
