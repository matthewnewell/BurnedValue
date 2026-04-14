FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Data directory — override with a volume mount to persist across restarts
ENV DATA_DIR=/app/data

# AI provider config — override at runtime (see docker-compose.yml)
ENV AI_PROVIDER=none
ENV AI_BASE_URL=
ENV AI_MODEL=
ENV AI_API_KEY=

EXPOSE 8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "app:app"]
