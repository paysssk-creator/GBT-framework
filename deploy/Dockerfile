# GBT小土豆 v5.0 Dockerfile
FROM python:3.12-slim

LABEL org.opencontainers.image.title="GBT小土豆"
LABEL org.opencontainers.image.description="智能大脑 v5.0 — 136个AI能力模块"
LABEL org.opencontainers.image.authors="自由的风"

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-chi-sim \
    git openssh-client curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /root/.gbt/memory /root/.gbt/data /root/.gbt/state

ENV PYTHONUNBUFFERED=1
ENV GBT_CONTEXT_BUDGET=128000

EXPOSE 9877

CMD ["python", "gbt.py", "daemon"]
