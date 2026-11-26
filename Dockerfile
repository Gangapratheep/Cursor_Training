# Demo container image — prefer local `python app.py` for day-to-day use.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

ENV FLASK_ENV=production \
    BIND_HOST=0.0.0.0 \
    BIND_PORT=5000 \
    PYTHONUNBUFFERED=1

RUN mkdir -p /app/instance

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "1", "app:app"]
