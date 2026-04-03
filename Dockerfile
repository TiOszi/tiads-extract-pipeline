FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipelines/ ./pipelines/

CMD ["python", "-c", "print('tiads-pipeline pronto.')"]
