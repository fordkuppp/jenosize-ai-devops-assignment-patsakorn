# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /src
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY pyproject.toml ./
COPY jenie ./jenie
RUN pip install --no-cache-dir .

# Bake the embedding model into the image rather than fetching it on first
# use. Downloading at startup makes the first request a multi-second outlier
# that pollutes the latency SLO, requires egress from every pod, and writes
# to a filesystem we mount read-only.
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
COPY api ./api
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FASTEMBED_CACHE_PATH=/opt/models
USER 10001
EXPOSE 8000
# --timeout-graceful-shutdown lets in-flight /ask calls finish on SIGTERM.
# Paired with the preStop hook in the Deployment: the hook stops new traffic
# arriving, this drains what is already in the process.
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--timeout-graceful-shutdown", "20"]
