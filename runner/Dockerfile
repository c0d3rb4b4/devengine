FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client bash && rm -rf /var/lib/apt/lists/*

COPY runner/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY devengine /app/devengine
COPY runner /app/runner
COPY config /app/config

CMD ["python", "-m", "runner.service"]
