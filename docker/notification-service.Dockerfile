FROM python:3.13-slim AS builder
WORKDIR /build
RUN pip install poetry
COPY services/notification-service/pyproject.toml services/notification-service/poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appgroup && adduser --system --ingroup appgroup appuser
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY services/notification-service/app/ ./app/
USER appuser
EXPOSE 8005
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
