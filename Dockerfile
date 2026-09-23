FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip --default-timeout=1000 && \
    pip install --no-cache-dir -r requirements.txt --default-timeout=1000

COPY . .

CMD ["tail", "-f", "/dev/null"]
