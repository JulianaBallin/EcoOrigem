# syntax=docker/dockerfile:1
# Multi-stage image: "runtime" runs the node and the web app, "test" runs the checks.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ECOORIGEM_DATA_DIR=/data \
    ECOORIGEM_ASSETS_DIR=/app/assets

WORKDIR /app
RUN useradd --create-home --uid 1000 ecoorigem \
    && mkdir -p /data/node /data/wallet && chown -R ecoorigem:ecoorigem /data

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY ecoorigem ./ecoorigem
COPY assets ./assets

FROM base AS runtime
USER ecoorigem
VOLUME ["/data"]
EXPOSE 8545 5000
CMD ["python", "-m", "ecoorigem", "node", "--host", "0.0.0.0"]

FROM base AS test
COPY requirements-dev.txt pyproject.toml ./
RUN pip install -r requirements-dev.txt
COPY tests ./tests
ENV COVERAGE_FILE=/tmp/.coverage
USER ecoorigem
CMD ["pytest", "-q", "--cov", "-p", "no:cacheprovider"]
