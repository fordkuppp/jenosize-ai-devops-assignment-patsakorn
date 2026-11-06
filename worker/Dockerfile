# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /src
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY pyproject.toml ./
COPY jenie ./jenie
RUN pip install --no-cache-dir .

FROM python:3.12-slim
RUN useradd --system --uid 10001 jenie
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY worker ./worker
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER 10001
ENTRYPOINT ["python", "-m", "worker.indexer.run"]
