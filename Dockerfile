# Dockerfile
FROM --platform=linux/amd64 python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    && pip install --no-cache-dir tensorflow==2.14

WORKDIR /app
COPY model/train.py .

CMD ["python", "train.py"]
