FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/grow_intelligence/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/grow_intelligence/grow_intelligence /app/grow_intelligence
COPY config /app/config

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "grow_intelligence.main"]
