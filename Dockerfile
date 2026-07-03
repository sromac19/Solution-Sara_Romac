# Multi-stage build: builder instalira dependency-je, runtime image ostaje malen.
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

FROM python:3.11-slim AS runtime

WORKDIR /app

# Ne pokrećemo aplikaciju kao root - dobra sigurnosna praksa za produkcijske image-e.
RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app/src
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Prije pokretanja servera primijenimo migracije - garantira da shema baze
# uvijek odgovara aktualnoj verziji koda pri svakom deployu/restartu.
CMD ["sh", "-c", "alembic upgrade head && uvicorn tickethub.main:app --host 0.0.0.0 --port 8000"]
