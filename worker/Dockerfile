# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /src
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY pyproject.toml ./
COPY jenie ./jenie
RUN pip install --no-cache-dir .

ENV FASTEMBED_CACHE_PATH=/opt/models
RUN python -c "from fastembed import TextEmbedding; \
    TextEmbedding(model_name='BAAI/bge-small-en-v1.5')"

FROM python:3.12-slim
# Security updates for the base image. python:3.12-slim lags Debian's
# security archive, and Trivy blocked the build on two fixable HIGH CVEs in
# zlib1g — including a heap buffer overflow in gz_vacate() allowing
# arbitrary code execution. Pulling the patched package here is the cheapest
# correct fix; the alternative is waiting for the base image to be rebuilt.
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*
RUN useradd --system --uid 10001 jenie
COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/models /opt/models
WORKDIR /app
COPY worker ./worker
# The corpus ships with the indexer. Versioning them together means a given
# image always produces the same index, which is what makes the evaluation
# reproducible. In production the corpus would come from object storage or a
# docs repository and this would be a mount.
COPY data ./data
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FASTEMBED_CACHE_PATH=/opt/models \
    DATA_DIR=/app/data
USER 10001
ENTRYPOINT ["python", "-m", "worker.indexer.run"]
