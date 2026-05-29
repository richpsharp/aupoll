FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY config ./config

ENV PYTHONPATH=/app/src \
    AUPOLL_DB_PATH=/data/aupoll.sqlite3 \
    AUPOLL_CONFIG_PATH=/config/poll.yaml

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "gthread", "--threads", "4", "--keep-alive", "2", "aupoll.app:create_app()"]
