# syntax=docker/dockerfile:1

FROM python:3.14-slim as base


FROM base as build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*


# Create a virtual environment to cleanly isolate dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

FROM python:3.14-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

COPY --from=build --chown=appuser:appuser /opt/venv /opt/venv

COPY --chown=appuser:appuser . .

CMD ["python", "main.py"]