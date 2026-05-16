# Silinosic-X Intelligence Framework — Docker Image
# Build: docker build -f docker/Dockerfile -t silinosic-x:latest .
# Run:   docker run -it --rm silinosic-x:latest

FROM python:3.12-slim

LABEL maintainer="voltsparx@gmail.com"
LABEL org.opencontainers.image.title="Silinosic-X"
LABEL org.opencontainers.image.description="Multi-engine OSINT orchestration framework"
LABEL org.opencontainers.image.source="https://github.com/voltsparx/Silinosic-X"

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tor \
    curl \
    wget \
    git \
    nmap \
    dnsutils \
    iputils-ping \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-dev.txt pyproject.toml ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir -e .

COPY docker/torrc.silinosic_x /etc/tor/torrc

RUN mkdir -p /app/output

ENTRYPOINT ["silinosic-x"]
CMD ["--help"]
