FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipelines/ ./pipelines/

# Container fica idle — executado sob demanda pelo N8N via docker run
ENTRYPOINT ["python"]
CMD ["-c", "print('tiads-extract-pipeline pronto.')"]
