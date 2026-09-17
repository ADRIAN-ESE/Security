FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# For HTTPS deployments behind a proxy, set COOKIE_SECURE=1 and provide
# SECRET_KEY / MASTER_KEY as environment variables.
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "2"]
