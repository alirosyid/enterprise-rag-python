# Gunakan image Python ringan untuk efisiensi
FROM python:3.11-slim

# Mencegah Python menulis file .pyc ke disk dan mem-bypass buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

# Instal dependensi sistem yang dibutuhkan untuk psycopg2 (PostgreSQL)
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean

# Instal dependensi Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode proyek
COPY . .

# Ekspos port API Gateway
EXPOSE 8001