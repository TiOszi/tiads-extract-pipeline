FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipelines/ ./pipelines/

# secrets.toml montado via volume em /root/.dlt/secrets.toml
CMD ["python", "-c", "print('tiads-pipeline pronto.')"]
